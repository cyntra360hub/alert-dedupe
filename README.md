[![AiOps Enabler rating](https://api.aiopsenabler.com/badge/alert-dedupe.svg)](https://aiopsenabler.com/agents/alert-dedupe)

# alert-dedupe

A small, deterministic Python agent that reads alert streams from
pluggable sources and outputs a **deduplicated, grouped digest** — no
LLM calls, no paid APIs, no server to run.

## What it does

1. Loads alerts from a directory of webhook-shaped JSON files (see
   "Webhook-file format" below) — by default, the bundled sample feeds
   in `src/alert_dedupe/data/sample_feeds/`.
2. Computes a deterministic fingerprint per alert: the alert's own
   `fingerprint` field if the source provides one (most real alerting
   systems do — e.g. PagerDuty's `dedup_key`), otherwise one derived
   from `(source, service, severity, normalized title)`.
3. Groups alerts sharing a fingerprint, ranks groups by size (noisiest
   first), and reports each group's highest severity and contributing
   sources.

## Install

Requires Python 3.12+.

```bash
pip install .
```

## Usage

```bash
alert-dedupe
```

Or as a module:

```bash
python -m alert_dedupe.cli
```

### Webhook-file format

Point `ALERT_DEDUPE_INPUT_DIR` at a directory of `*.json` files — each
file is one JSON object (or a bare array, treated as `generic`). An
optional top-level `"format"` key selects which adapter interprets the
rest of the file (`"generic"` if omitted), so a directory can mix files
from several real alerting sources:

```jsonc
// generic (default) — a flat list matching Alert's own fields
{
  "format": "generic",
  "alerts": [
    {"id": "1", "source": "datadog", "title": "CPU high", "severity": "warning", "service": "api"}
  ]
}
```

Two illustrative source-shaped adapters ship out of the box
(`src/alert_dedupe/adapters.py`) — `"pagerduty"` and `"datadog"`,
simplified stand-ins for those systems' real webhook shapes, demonstrating
the pattern rather than being exact schema matches. **Adding your own is
one function call:**

```python
from alert_dedupe.adapters import register_adapter

def my_source_adapter(raw: dict) -> list[Alert]:
    ...

register_adapter("my-source", my_source_adapter)
```

then set `"format": "my-source"` in that source's files.

### Configuration (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| `ALERT_DEDUPE_INPUT_DIR` | bundled sample feeds | directory of webhook-format JSON files |
| `ALERT_DEDUPE_ESCALATE_THRESHOLD` | `5` | a group at/above this size is flagged `[ESCALATE]` and reported as `escalated` |

Copy `.env.example` to `.env` to set these locally; `.env` is gitignored
and never committed.

## Optional: AiOps Enabler integration

alert-dedupe can optionally report each run as a signed task event to
[AiOps Enabler](https://aiopsenabler.com), a public-interest registry of
verified AI agent performance. **This is opt-in and off by default** —
the agent never phones home unless you explicitly configure credentials.

Reporting is implemented as **raw HMAC-signed REST**
(`src/alert_dedupe/signing.py` + `reporting.py`), built directly from the
platform's own published spec ([skill.md](https://aiopsenabler.com/skill.md) §3,
[api-guide.md](https://aiopsenabler.com/api-guide.md) §2) using only the
standard library. This is a deliberate substitution for the
officially-documented Python SDK (`aiops-enabler`): its install command
points at `github.com/cyntra360hub/aiops-enabler`, which is currently a
**private** repository and not installable by the public despite being
the documented path for external integrators. Raw signed REST sidesteps
that and is functionally equivalent (same headers, same signing scheme,
same published test vector — see `tests/test_signing.py`).

To enable it, set two environment variables (in `.env` locally, or as
GitHub Actions secrets in CI — see `.github/workflows/scheduled.yml`):

```
ALERT_DEDUPE_AGENT_KEY_ID=ak_...
ALERT_DEDUPE_AGENT_SECRET=...
```

With both set, each run sends a signed `task_started` / `task_completed`
event pair to `POST /api/v1/events`, with `outcome` set to `escalated`
when any group reaches `ALERT_DEDUPE_ESCALATE_THRESHOLD`, otherwise
`success`.

### README badge

The badge at the top of this file is AiOps Enabler's public, CDN-cached,
unauthenticated badge endpoint — `GET /badge/{slug}.svg` — safe to embed
in any third-party README with no API key. It shows this agent's live
rating once published; **it 404s until the operator publishes this
agent's profile** (see [skill.md](https://aiopsenabler.com/skill.md)
section 2 — a signed request still succeeds and is recorded before
publishing, only the *public* badge/profile needs that extra step). Swap
`alert-dedupe` in the badge URL for your own agent's slug if you fork
this.

### Rating widget

Beyond the static badge, AiOps Enabler also offers an embeddable
"Rate me 👍👎" widget for an agent's own UI, so end users can rate an
interaction directly:

- **Script embed:** `GET https://api.aiopsenabler.com/widget/{slug}.js`
- **Iframe embed:** `GET https://api.aiopsenabler.com/widget/{slug}`
- Submissions go to `POST /api/v1/agents/{slug}/widget-rating` — public
  and **unsigned** (rate-limited by IP + slug instead), since it's meant
  to be called directly from a browser where a secret can't be kept
  safe. This is distinct from this repo's own signed `POST /api/v1/ratings`
  path (used by an agent's *backend*, not applicable here since
  alert-dedupe is a CLI tool with no end-user-facing UI to embed a widget
  into) — documented here for completeness, for forks that do have one.

## Development

```bash
pip install -e ".[dev]"
pytest
```

All tests run fully offline — no network calls; the bundled sample feeds
are read from disk directly.

## License

MIT — see [LICENSE](LICENSE).
