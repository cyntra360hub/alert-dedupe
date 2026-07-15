"""Deterministic deduplication and grouping of alerts.

Two alerts are considered the same underlying issue if they share a
fingerprint: either an explicit `Alert.fingerprint` (if the source
provides one -- most real alerting systems do, e.g. PagerDuty's
`dedup_key`), or a fingerprint computed here from
`(source, service, severity, normalized title)`. Title normalization
(lowercase, whitespace-collapsed) absorbs cosmetic differences between
otherwise-identical repeat alerts without doing any fuzzy/similarity
matching -- deterministic in, deterministic out.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from alert_dedupe.models import SEVERITY_RANK, Alert

_WHITESPACE = re.compile(r"\s+")


def normalize_title(title: str) -> str:
    return _WHITESPACE.sub(" ", title.strip().lower())


def compute_fingerprint(alert: Alert) -> str:
    if alert.fingerprint:
        return alert.fingerprint
    key = "|".join(
        [alert.source, alert.service or "", alert.severity, normalize_title(alert.title)]
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class AlertGroup:
    fingerprint: str
    alerts: tuple[Alert, ...]

    @property
    def count(self) -> int:
        return len(self.alerts)

    @property
    def title(self) -> str:
        return self.alerts[0].title

    @property
    def sources(self) -> tuple[str, ...]:
        return tuple(sorted({a.source for a in self.alerts}))

    @property
    def severity(self) -> str:
        return max((a.severity for a in self.alerts), key=lambda s: SEVERITY_RANK.get(s, 0))


@dataclass(frozen=True)
class Digest:
    total_alerts: int
    groups: tuple[AlertGroup, ...]

    @property
    def total_groups(self) -> int:
        return len(self.groups)

    @property
    def noise_reduction_pct(self) -> float:
        if self.total_alerts == 0:
            return 0.0
        return round(100 * (1 - self.total_groups / self.total_alerts), 1)

    @property
    def max_group_size(self) -> int:
        return max((g.count for g in self.groups), default=0)


def build_digest(alerts: list[Alert]) -> Digest:
    grouped: dict[str, list[Alert]] = {}
    for alert in alerts:
        fp = compute_fingerprint(alert)
        grouped.setdefault(fp, []).append(alert)

    groups = tuple(
        AlertGroup(fingerprint=fp, alerts=tuple(items)) for fp, items in grouped.items()
    )
    # Deterministic order: biggest groups (most duplicated / noisiest)
    # first, ties broken by fingerprint so ordering never depends on
    # dict/insertion order across Python versions or runs.
    groups = tuple(sorted(groups, key=lambda g: (-g.count, g.fingerprint)))

    return Digest(total_alerts=len(alerts), groups=groups)
