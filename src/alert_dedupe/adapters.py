"""Pluggable adapters: each turns one raw webhook-payload shape into a
list of `Alert` objects. See README "Webhook-file format" for the full
spec of what a file on disk looks like and how `format` selects an
adapter.

Adding your own source: write a function `(raw: dict) -> list[Alert]`
and call `register_adapter("your-format-name", your_function)` -- no
subclassing, no plugin discovery magic, just a dict registry so it's
easy to read, test, and override in a fork.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from alert_dedupe.models import Alert

Adapter = Callable[[dict[str, Any]], list[Alert]]

_ADAPTERS: dict[str, Adapter] = {}


def register_adapter(name: str, adapter: Adapter) -> None:
    _ADAPTERS[name] = adapter


def get_adapter(name: str) -> Adapter:
    try:
        return _ADAPTERS[name]
    except KeyError:
        raise ValueError(
            f"no adapter registered for format {name!r}; known formats: "
            f"{sorted(_ADAPTERS)}"
        ) from None


def generic_adapter(raw: dict[str, Any]) -> list[Alert]:
    """The default format: `{"alerts": [{"id", "source", "title", ...}]}`
    or a bare list of such objects (see `loader.load_file`), each object
    mapping ~1:1 onto `Alert`'s fields."""
    items = raw.get("alerts", [raw]) if "alerts" in raw else [raw]
    alerts = []
    for item in items:
        alerts.append(
            Alert(
                id=str(item["id"]),
                source=item.get("source", "generic"),
                title=item["title"],
                severity=item.get("severity", "unknown"),
                service=item.get("service"),
                description=item.get("description"),
                timestamp=item.get("timestamp"),
                fingerprint=item.get("fingerprint"),
            )
        )
    return alerts


def pagerduty_style_adapter(raw: dict[str, Any]) -> list[Alert]:
    """Illustrative PagerDuty-webhook-shaped adapter (not the exact real
    PagerDuty schema -- simplified for demonstration of pluggability
    across genuinely different wire shapes). Expects
    `{"messages": [{"event": {...}, "incident": {"id", "title",
    "urgency", "service": {"summary"}, "created_at"}}]}`."""
    alerts = []
    for message in raw.get("messages", []):
        incident = message.get("incident", {})
        urgency = incident.get("urgency", "unknown")
        severity = {"high": "critical", "low": "warning"}.get(urgency, urgency)
        alerts.append(
            Alert(
                id=str(incident["id"]),
                source="pagerduty",
                title=incident.get("title", "(untitled incident)"),
                severity=severity,
                service=(incident.get("service") or {}).get("summary"),
                timestamp=incident.get("created_at"),
            )
        )
    return alerts


def datadog_style_adapter(raw: dict[str, Any]) -> list[Alert]:
    """Illustrative Datadog-monitor-webhook-shaped adapter (simplified,
    not the exact real Datadog schema). Expects a list of
    `{"id", "title", "alert_type", "text", "date_epoch_ms", "tags"}`."""
    alerts = []
    for item in raw.get("events", []):
        tags = item.get("tags", [])
        service = next((t.split(":", 1)[1] for t in tags if t.startswith("service:")), None)
        severity = {"error": "error", "warning": "warning", "success": "info"}.get(
            item.get("alert_type", "unknown"), "unknown"
        )
        alerts.append(
            Alert(
                id=str(item["id"]),
                source="datadog",
                title=item.get("title", "(untitled alert)"),
                severity=severity,
                service=service,
                description=item.get("text"),
                timestamp=str(item.get("date_epoch_ms")) if item.get("date_epoch_ms") else None,
            )
        )
    return alerts


register_adapter("generic", generic_adapter)
register_adapter("pagerduty", pagerduty_style_adapter)
register_adapter("datadog", datadog_style_adapter)
