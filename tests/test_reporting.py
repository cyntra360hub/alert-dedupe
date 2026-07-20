import json

from alert_dedupe.config import Config
from alert_dedupe.dedupe import build_digest
from alert_dedupe.models import Alert
from alert_dedupe.reporting import ReportingError, findings_summary, report_run, technical_summary


class _FakePoster:
    def __init__(self):
        self.calls = []

    def __call__(self, url, body, headers):
        self.calls.append((url, body, headers))
        return {"id": "evt_123"}


def _digest(count: int):
    alerts = [Alert(id=str(i), source="x", title="Same", fingerprint="fp1") for i in range(count)]
    return build_digest(alerts)


def test_findings_summary_none_for_empty_digest():
    assert findings_summary(_digest(0), escalate_threshold=5) is None


def test_findings_summary_names_the_largest_group():
    summary = findings_summary(_digest(2), escalate_threshold=5)
    assert summary == "grouped 2 alerts into 1 group -- e.g. Same (2x)"


def test_technical_summary_below_threshold_has_no_large_group_mention():
    summary = technical_summary(_digest(2), escalate_threshold=5)
    assert summary == "1 group(s) from 2 alert(s)"


def test_technical_summary_at_threshold_mentions_large_group():
    summary = technical_summary(_digest(5), escalate_threshold=5)
    assert summary == "1 group(s) from 5 alert(s); 1 large group(s) (>=5)"


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


def test_large_noisy_group_is_still_success_with_details_and_external_ref():
    # A burst of duplicate alerts is a successful detection, not a
    # failure -- the finding goes in `details`/`external_ref`, not outcome.
    poster = _FakePoster()
    config = Config(
        report_enabled=True, agent_key_id="ak_test", agent_secret="s3cret", escalate_threshold=3
    )
    report_run(config, _digest(3), poster=poster)
    second_body = json.loads(poster.calls[1][1])
    assert second_body["outcome"] == "success"
    assert second_body["details"] == "grouped 3 alerts into 1 group -- e.g. Same (3x)"
    assert second_body["external_ref"] == "1 group(s) from 3 alert(s); 1 large group(s) (>=3)"


def test_empty_digest_is_success_without_details_or_external_ref():
    poster = _FakePoster()
    config = Config(report_enabled=True, agent_key_id="ak_test", agent_secret="s3cret")
    report_run(config, _digest(0), poster=poster)
    second_body = json.loads(poster.calls[1][1])
    assert second_body["outcome"] == "success"
    assert "external_ref" not in second_body
    assert "details" not in second_body


def test_error_reports_failure_with_error_in_external_ref():
    poster = _FakePoster()
    config = Config(report_enabled=True, agent_key_id="ak_test", agent_secret="s3cret")
    report_run(config, None, error="malformed webhook file: missing 'id'", poster=poster)
    second_body = json.loads(poster.calls[1][1])
    assert second_body["outcome"] == "failure"
    assert second_body["external_ref"] == "malformed webhook file: missing 'id'"


def test_reporting_error_carries_status_and_detail():
    err = ReportingError(422, '{"detail": "bad request"}')
    assert err.status_code == 422
    assert "bad request" in err.detail


def test_duration_ms_is_never_zero():
    poster = _FakePoster()
    config = Config(report_enabled=True, agent_key_id="ak_test", agent_secret="s3cret")
    report_run(config, _digest(1), poster=poster)
    second_body = json.loads(poster.calls[1][1])
    assert isinstance(second_body["duration_ms"], int)
    assert second_body["duration_ms"] >= 1


def test_duration_ms_reflects_real_elapsed_run_time():
    import time

    poster = _FakePoster()
    config = Config(report_enabled=True, agent_key_id="ak_test", agent_secret="s3cret")
    run_started = time.monotonic() - 2.5
    report_run(config, _digest(1), poster=poster, run_started=run_started)
    second_body = json.loads(poster.calls[1][1])
    assert second_body["duration_ms"] >= 2500
