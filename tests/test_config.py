from pathlib import Path

from alert_dedupe.config import DEFAULT_ESCALATE_THRESHOLD, load_config


def test_defaults_when_env_empty():
    config = load_config(env={})
    assert config.escalate_threshold == DEFAULT_ESCALATE_THRESHOLD
    assert config.report_enabled is False
    assert config.input_dir.name == "sample_feeds"


def test_custom_input_dir_from_env():
    config = load_config(env={"ALERT_DEDUPE_INPUT_DIR": "/tmp/custom"})
    assert config.input_dir == Path("/tmp/custom")


def test_custom_escalate_threshold_from_env():
    config = load_config(env={"ALERT_DEDUPE_ESCALATE_THRESHOLD": "3"})
    assert config.escalate_threshold == 3


def test_reporting_enabled_only_when_both_creds_present():
    assert load_config(env={"ALERT_DEDUPE_AGENT_KEY_ID": "ak_x"}).report_enabled is False
    assert (
        load_config(
            env={"ALERT_DEDUPE_AGENT_KEY_ID": "ak_x", "ALERT_DEDUPE_AGENT_SECRET": "s"}
        ).report_enabled
        is True
    )
