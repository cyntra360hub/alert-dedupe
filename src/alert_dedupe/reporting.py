"""Optional AiOps Enabler reporting via raw HMAC-signed REST calls to
POST /api/v1/events -- no SDK dependency (see signing.py's module
docstring for why).

Reporting only happens when the caller explicitly enables it (see
`config.load_config`). This module never phones home by default.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
import uuid
from collections.abc import Callable
from typing import Any

from alert_dedupe.config import Config
from alert_dedupe.dedupe import Digest
from alert_dedupe.signing import sign_request

Poster = Callable[[str, bytes, dict[str, str]], dict[str, Any]]


class ReportingError(Exception):
    """Raised when the AiOps Enabler API rejects a signed request."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"AiOps Enabler API error {status_code}: {detail}")


def post_signed(url: str, body: bytes, headers: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=10.0) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raise ReportingError(exc.code, exc.read().decode("utf-8", "replace")) from exc


def _send_event(config: Config, payload: dict[str, Any], poster: Poster) -> dict[str, Any]:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = sign_request(
        key_id=config.agent_key_id, secret=config.agent_secret, body=body  # type: ignore[arg-type]
    )
    url = f"{config.base_url.rstrip('/')}/api/v1/events"
    return poster(url, body, headers)


def findings_summary(digest: Digest, escalate_threshold: int) -> str | None:
    """A compact, human-readable summary of a completed dedupe run, for
    the AiOps Enabler event's `external_ref` field (the only freeform
    field the events API offers). None when there were no alerts at all
    to report on."""
    if digest.total_alerts == 0:
        return None
    large = [g for g in digest.groups if g.count >= escalate_threshold]
    parts = [f"swept {digest.total_alerts} alert(s) -- {digest.total_groups} group(s)"]
    if large:
        parts.append(f"{len(large)} large group(s) (>={escalate_threshold})")
    return "; ".join(parts)[:255]


def report_run(
    config: Config,
    digest: Digest | None,
    error: str | None = None,
    poster: Poster = post_signed,
    run_started: float | None = None,
) -> dict[str, Any] | None:
    """Report one alert-dedupe run as a signed task_started/task_completed
    event pair. Returns the platform's task_completed response, or None
    if reporting is disabled.

    `outcome` is `success` whenever the run actually completed --
    **including** when it groups a large, noisy burst of alerts, since
    detecting that is this agent doing its job, not a failure. `outcome`
    is `failure` only when `error` is given, meaning the run itself
    crashed (e.g. a malformed webhook file) before it could produce a
    digest at all -- see `cli.py`, which is the only caller that ever
    passes `error`. Findings (or the error) go in `external_ref`, the
    events API's only freeform field.

    `run_started` should be a `time.monotonic()` reading taken before the
    load+dedupe ran (see cli.py), so the reported `duration_ms` reflects
    the real work done rather than just the round trip of this function's
    own task_started call. Falls back to timing only this call when
    omitted (e.g. in tests).
    """
    if not config.report_enabled:
        return None

    task_id = str(uuid.uuid4())
    if run_started is None:
        run_started = time.monotonic()

    _send_event(config, {"event_type": "task_started", "task_id": task_id}, poster)
    # Never report a duration of 0 -- a sub-millisecond run still took a
    # real, non-zero amount of time as far as the platform's pulse is
    # concerned.
    duration_ms = max(1, round((time.monotonic() - run_started) * 1000))
    payload: dict[str, Any] = {
        "event_type": "task_completed",
        "task_id": task_id,
        "outcome": "failure" if error else "success",
        "duration_ms": duration_ms,
        "category": "alert-triage",
    }
    if error:
        payload["external_ref"] = error[:255]
    elif digest is not None:
        summary = findings_summary(digest, config.escalate_threshold)
        if summary:
            payload["external_ref"] = summary
    return _send_event(config, payload, poster)
