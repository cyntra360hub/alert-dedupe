from alert_dedupe.dedupe import build_digest, compute_fingerprint, normalize_title
from alert_dedupe.models import Alert


def test_normalize_title_collapses_whitespace_and_lowercases():
    assert normalize_title("  High   Memory  Usage  ") == "high memory usage"


def test_explicit_fingerprint_is_used_as_is():
    alert = Alert(id="1", source="x", title="t", fingerprint="explicit-fp")
    assert compute_fingerprint(alert) == "explicit-fp"


def test_computed_fingerprint_is_stable_across_cosmetic_title_differences():
    a = Alert(id="1", source="x", title="High memory usage", severity="warning", service="api")
    b = Alert(id="2", source="x", title="  High   memory usage  ", severity="warning", service="api")
    assert compute_fingerprint(a) == compute_fingerprint(b)


def test_computed_fingerprint_differs_by_severity():
    a = Alert(id="1", source="x", title="t", severity="warning")
    b = Alert(id="2", source="x", title="t", severity="critical")
    assert compute_fingerprint(a) != compute_fingerprint(b)


def test_build_digest_groups_duplicates():
    alerts = [
        Alert(id="1", source="x", title="Same issue", severity="warning", service="api"),
        Alert(id="2", source="x", title="Same issue", severity="warning", service="api"),
        Alert(id="3", source="x", title="Different issue", severity="critical", service="db"),
    ]
    digest = build_digest(alerts)
    assert digest.total_alerts == 3
    assert digest.total_groups == 2
    assert digest.groups[0].count == 2  # biggest group first
    assert digest.groups[0].title == "Same issue"


def test_digest_noise_reduction_pct():
    alerts = [Alert(id=str(i), source="x", title="Same", severity="warning") for i in range(4)]
    digest = build_digest(alerts)
    assert digest.total_alerts == 4
    assert digest.total_groups == 1
    assert digest.noise_reduction_pct == 75.0


def test_empty_alerts_produces_empty_digest():
    digest = build_digest([])
    assert digest.total_alerts == 0
    assert digest.total_groups == 0
    assert digest.noise_reduction_pct == 0.0
    assert digest.max_group_size == 0


def test_group_severity_is_highest_among_its_alerts():
    alerts = [
        Alert(id="1", source="x", title="t", severity="warning", fingerprint="fp1"),
        Alert(id="2", source="x", title="t", severity="critical", fingerprint="fp1"),
    ]
    digest = build_digest(alerts)
    assert digest.groups[0].severity == "critical"


def test_group_sources_is_sorted_unique():
    alerts = [
        Alert(id="1", source="b", title="t", fingerprint="fp1"),
        Alert(id="2", source="a", title="t", fingerprint="fp1"),
        Alert(id="3", source="a", title="t", fingerprint="fp1"),
    ]
    digest = build_digest(alerts)
    assert digest.groups[0].sources == ("a", "b")
