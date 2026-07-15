import json

from alert_dedupe.config import Config
from alert_dedupe.dedupe import build_digest
from alert_dedupe.models import Alert
from alert_dedupe.reporting import ReportingError, digest_outcome, report_run


class _FakePoster:
    def __init__(self):
        self.calls = []

    def __call__(self, url, body, headers):
        self.calls.append((url, body, headers))
        return {"id": "evt_123"}


def _digest(count: int):
    alerts = [Alert(id=str(i), source="x", title="Same", fingerprint="fp1") for i in range(count)]
    return build_digest(alerts)


def test_digest_outcome_success_below_threshold():
    assert digest_outcome(_digest(2), escalate_threshold=5) == "success"


def test_digest_outcome_escalated_at_threshold():
    assert digest_outcome(_digest(5), escalate_threshold=5) == "escalated"


def test_report_disabled_returns_none():
    poster = _FakePoster()
    config = Config(report_enabled=False)
    assert report_run(config, _digest(1), poster=poster) is None
    assert poster.calls == []


def test_report_enabled_sends_started_then_completed():
    poster = _FakePoster()
    config = Config(report_enabled=True, agent_key_id="ak_test", agent_secret="s3cret")
    response = report_run(config, _digest(1), poster=poster)
    assert response == {"id": "evt_123"}
    kinds = [json.loads(c[1])["event_type"] for c in poster.calls]
    assert kinds == ["task_started", "task_completed"]


def test_reported_outcome_matches_digest_outcome():
    poster = _FakePoster()
    config = Config(
        report_enabled=True, agent_key_id="ak_test", agent_secret="s3cret", escalate_threshold=3
    )
    report_run(config, _digest(3), poster=poster)
    second_body = json.loads(poster.calls[1][1])
    assert second_body["outcome"] == "escalated"


def test_reporting_error_carries_status_and_detail():
    err = ReportingError(422, '{"detail": "bad request"}')
    assert err.status_code == 422
    assert "bad request" in err.detail
