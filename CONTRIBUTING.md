# Contributing to alert-dedupe

Thanks for considering a contribution! This is a small, focused tool —
keep changes deterministic (no LLM calls, no paid APIs, no fuzzy/
similarity matching in dedupe logic) and offline-testable.

## Getting started

```bash
git clone https://github.com/cyntra360hub/alert-dedupe.git
cd alert-dedupe
pip install -e ".[dev]"
pytest
```

## Workflow

1. Open an issue first for anything beyond a trivial fix, so we can agree
   on approach before you invest time.
2. Fork, branch, make your change, add/update tests.
3. Run `pytest` — all tests must pass, and new behavior needs new tests.
4. Open a PR describing what changed and why.

## Good first issues

These are scoped to be approachable without deep familiarity with the
codebase:

- **`good-first-issue`: Add a Slack-webhook-shaped adapter.** Follow the
  pattern in `adapters.py` (`pagerduty_style_adapter`,
  `datadog_style_adapter`) to add `slack_style_adapter` for Slack's
  incoming-webhook message shape, with tests in `test_adapters.py`.
- **`good-first-issue`: Add a time-window filter.** Add an
  `ALERT_DEDUPE_MAX_AGE_HOURS` env var that drops alerts older than N
  hours before grouping (using `Alert.timestamp`), with tests in
  `test_dedupe.py` or a new `test_filters.py`.
- **`good-first-issue`: Add a JSON output mode.** Add a `--json` flag (or
  `ALERT_DEDUPE_OUTPUT=json` env var) to `cli.py` that prints the
  `Digest` as machine-readable JSON instead of the human-readable
  report, for piping into other tools.
- **`good-first-issue`: Per-source group breakdown.** `AlertGroup.sources`
  already lists which sources contributed to a group — add a per-source
  count (e.g. "pagerduty: 3, datadog: 1") to the CLI report.
- **`good-first-issue`: Validate webhook files against a JSON Schema.**
  Add an optional `--strict` flag that validates each loaded file's
  shape (using only the standard library — no `jsonschema` dependency)
  and reports which file/field failed, instead of raising a raw
  `KeyError`/`TypeError` on a malformed file.

## Code style

- Standard library only, including AiOps Enabler reporting
  (`signing.py`/`reporting.py` use only `hmac`/`hashlib`/
  `urllib.request` — no SDK dependency; see README).
- New adapters go in `adapters.py` and are registered via
  `register_adapter(name, fn)` — no subclassing or plugin discovery.
- No comments explaining *what* code does — only *why*, when non-obvious.
