import alert_dedupe.cli as cli_mod


def test_main_reports_failure_and_exits_nonzero_on_crash(monkeypatch, capsys):
    # No AiOps credentials configured -> reporting is disabled, so this
    # only exercises the crash-handling/exit-code path, not the network.
    monkeypatch.delenv("ALERT_DEDUPE_AGENT_KEY_ID", raising=False)
    monkeypatch.delenv("ALERT_DEDUPE_AGENT_SECRET", raising=False)

    def boom(path):
        raise ValueError("malformed webhook file: missing 'id'")

    monkeypatch.setattr(cli_mod, "load_directory", boom)

    exit_code = cli_mod.main()

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "[ERROR] failed to load/process alerts" in captured.err
    assert "Overall: outcome=failure" in captured.out


def test_main_reports_success_on_clean_run(monkeypatch, capsys, tmp_path):
    monkeypatch.delenv("ALERT_DEDUPE_AGENT_KEY_ID", raising=False)
    monkeypatch.delenv("ALERT_DEDUPE_AGENT_SECRET", raising=False)
    monkeypatch.setenv("ALERT_DEDUPE_INPUT_DIR", str(tmp_path))

    exit_code = cli_mod.main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Overall: outcome=success" in captured.out
