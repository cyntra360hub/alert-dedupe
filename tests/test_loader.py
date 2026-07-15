import json
from pathlib import Path

from alert_dedupe.loader import load_directory, load_file


def test_load_file_generic_format(tmp_path: Path):
    path = tmp_path / "a.json"
    path.write_text(json.dumps({"format": "generic", "alerts": [{"id": "1", "title": "x"}]}))
    alerts = load_file(path)
    assert len(alerts) == 1
    assert alerts[0].id == "1"


def test_load_file_defaults_to_generic_when_format_missing(tmp_path: Path):
    path = tmp_path / "a.json"
    path.write_text(json.dumps({"alerts": [{"id": "1", "title": "x"}]}))
    alerts = load_file(path)
    assert len(alerts) == 1


def test_load_file_bare_list_is_generic(tmp_path: Path):
    path = tmp_path / "a.json"
    path.write_text(json.dumps([{"id": "1", "title": "x"}, {"id": "2", "title": "y"}]))
    alerts = load_file(path)
    assert len(alerts) == 2


def test_load_directory_missing_returns_empty(tmp_path: Path):
    assert load_directory(tmp_path / "nope") == []


def test_load_directory_combines_all_json_files(tmp_path: Path):
    (tmp_path / "a.json").write_text(json.dumps({"alerts": [{"id": "1", "title": "x"}]}))
    (tmp_path / "b.json").write_text(json.dumps({"alerts": [{"id": "2", "title": "y"}]}))
    (tmp_path / "not-json.txt").write_text("ignore me")
    alerts = load_directory(tmp_path)
    assert {a.id for a in alerts} == {"1", "2"}


def test_load_directory_bundled_sample_feeds():
    # Exercises the real bundled src/alert_dedupe/data/sample_feeds/ shipped
    # with the package.
    repo_root = Path(__file__).resolve().parent.parent
    alerts = load_directory(repo_root / "src" / "alert_dedupe" / "data" / "sample_feeds")
    assert len(alerts) >= 8
    assert {a.source for a in alerts} >= {"in-house-monitor", "pagerduty", "datadog"}
