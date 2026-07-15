"""The common Alert shape every adapter normalizes into (see adapters.py)."""

from __future__ import annotations

from dataclasses import dataclass

# Ordered worst-to-best so `max(severities, key=SEVERITY_RANK.get)` finds
# a group's highest severity deterministically, including for unknown
# values (rank 0, sorts below every recognized severity).
SEVERITY_RANK = {
    "unknown": 0,
    "info": 1,
    "warning": 2,
    "error": 3,
    "critical": 4,
}


@dataclass(frozen=True)
class Alert:
    id: str
    source: str
    title: str
    severity: str = "unknown"
    service: str | None = None
    description: str | None = None
    timestamp: str | None = None
    fingerprint: str | None = None
