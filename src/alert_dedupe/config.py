"""Configuration for alert-dedupe, sourced from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Bundled sample feeds, shipped *inside* the package (not a sibling repo
# directory) so they're present whether alert-dedupe is installed
# editable or as a built wheel -- demonstrates the tool end-to-end with
# zero setup either way.
DEFAULT_INPUT_DIR = Path(__file__).resolve().parent / "data" / "sample_feeds"
DEFAULT_ESCALATE_THRESHOLD = 5


@dataclass(frozen=True)
class Config:
    input_dir: Path = DEFAULT_INPUT_DIR
    escalate_threshold: int = DEFAULT_ESCALATE_THRESHOLD
    report_enabled: bool = False
    agent_key_id: str | None = None
    agent_secret: str | None = None
    base_url: str = "https://api.aiopsenabler.com"


def load_config(env: dict[str, str] | None = None) -> Config:
    """Build a Config from environment variables (or an injected mapping,
    for tests). Reporting is opt-in: it only turns on when both
    ALERT_DEDUPE_AGENT_KEY_ID and ALERT_DEDUPE_AGENT_SECRET are set."""
    source = env if env is not None else os.environ

    # `.get(key, default)` only falls back when the key is *absent* -- an
    # explicitly empty env var (as in .env.example's unset-but-present
    # placeholders) would otherwise silently win over the default, so an
    # empty/unset value is treated the same via `or`.
    input_dir = Path(source.get("ALERT_DEDUPE_INPUT_DIR") or DEFAULT_INPUT_DIR)
    escalate_threshold = int(
        source.get("ALERT_DEDUPE_ESCALATE_THRESHOLD") or DEFAULT_ESCALATE_THRESHOLD
    )

    key_id = source.get("ALERT_DEDUPE_AGENT_KEY_ID") or None
    secret = source.get("ALERT_DEDUPE_AGENT_SECRET") or None
    base_url = source.get("ALERT_DEDUPE_BASE_URL", "https://api.aiopsenabler.com")

    return Config(
        input_dir=input_dir,
        escalate_threshold=escalate_threshold,
        report_enabled=bool(key_id and secret),
        agent_key_id=key_id,
        agent_secret=secret,
        base_url=base_url,
    )
