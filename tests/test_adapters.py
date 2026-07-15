import pytest

from alert_dedupe.adapters import (
    datadog_style_adapter,
    generic_adapter,
    get_adapter,
    pagerduty_style_adapter,
    register_adapter,
)
from alert_dedupe.models import Alert


def test_generic_adapter_with_alerts_key():
    raw = {"alerts": [{"id": "1", "source": "x", "title": "Boom", "severity": "critical"}]}
    result = generic_adapter(raw)
    assert result == [Alert(id="1", source="x", title="Boom", severity="critical")]


def test_generic_adapter_bare_object_is_single_alert():
    raw = {"id": "1", "title": "Boom", "source": "x"}
    result = generic_adapter(raw)
    assert len(result) == 1
    assert result[0].id == "1"


def test_generic_adapter_defaults():
    raw = {"alerts": [{"id": "1", "title": "Boom"}]}
    result = generic_adapter(raw)
    assert result[0].source == "generic"
    assert result[0].severity == "unknown"
    assert result[0].service is None


def test_pagerduty_style_adapter_maps_urgency_to_severity():
    raw = {
        "messages": [
            {
                "incident": {
                    "id": "pd-1",
                    "title": "Down",
                    "urgency": "high",
                    "service": {"summary": "checkout"},
                    "created_at": "2026-01-01T00:00:00Z",
                }
            }
        ]
    }
    result = pagerduty_style_adapter(raw)
    assert result[0].severity == "critical"
    assert result[0].service == "checkout"
    assert result[0].source == "pagerduty"


def test_datadog_style_adapter_extracts_service_from_tags():
    raw = {
        "events": [
            {
                "id": "dd-1",
                "title": "CPU high",
                "alert_type": "error",
                "tags": ["service:worker", "env:prod"],
            }
        ]
    }
    result = datadog_style_adapter(raw)
    assert result[0].service == "worker"
    assert result[0].severity == "error"
    assert result[0].source == "datadog"


def test_get_adapter_unknown_format_raises():
    with pytest.raises(ValueError, match="no adapter registered"):
        get_adapter("carrier-pigeon")


def test_register_adapter_makes_it_retrievable():
    def custom(raw):
        return []

    register_adapter("custom-test-format", custom)
    assert get_adapter("custom-test-format") is custom
