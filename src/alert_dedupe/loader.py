"""Loads alerts from a directory of webhook-shaped JSON files.

Webhook-file format (see README for the full spec): each `*.json` file
in the directory is one JSON object. An optional top-level `"format"`
key selects which adapter (adapters.py) interprets the rest of the file
-- `"generic"` if omitted. This lets a directory mix files from several
real alerting sources (PagerDuty, Datadog, a custom in-house webhook,
...) as long as each file names its own format.
"""

from __future__ import annotations

import json
from pathlib import Path

from alert_dedupe.adapters import get_adapter
from alert_dedupe.models import Alert


def load_file(path: Path) -> list[Alert]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    format_name = raw.get("format", "generic") if isinstance(raw, dict) else "generic"
    adapter = get_adapter(format_name)
    if isinstance(raw, list):
        return adapter({"alerts": raw})
    return adapter(raw)


def load_directory(path: Path) -> list[Alert]:
    if not path.exists():
        return []
    alerts: list[Alert] = []
    for file_path in sorted(path.glob("*.json")):
        alerts.extend(load_file(file_path))
    return alerts
