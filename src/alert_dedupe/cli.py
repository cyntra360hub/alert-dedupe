"""alert-dedupe command-line entry point."""

from __future__ import annotations

import sys

from alert_dedupe.config import load_config
from alert_dedupe.dedupe import Digest, build_digest
from alert_dedupe.loader import load_directory
from alert_dedupe.reporting import report_run


def _print_report(digest: Digest, escalate_threshold: int) -> None:
    print(f"{digest.total_alerts} alert(s) -> {digest.total_groups} group(s) "
          f"({digest.noise_reduction_pct}% noise reduction)")
    for group in digest.groups:
        flag = " [ESCALATE]" if group.count >= escalate_threshold else ""
        print(f"  [{group.severity:8}] x{group.count:<3} {group.title!r} "
              f"(sources: {', '.join(group.sources)}){flag}")
    print()
    print("Overall: outcome=success")


def main() -> int:
    config = load_config()

    # Load+process is the only step that can genuinely "error out" (a
    # malformed webhook file, an unreadable input dir, ...) -- caught
    # here so a crash still gets reported as outcome=failure instead of
    # silently sending no event at all. A large/noisy digest is NOT an
    # error: that's this agent doing its job, reported as outcome=success
    # with the finding in external_ref (see reporting.py).
    digest: Digest | None = None
    error: str | None = None
    try:
        alerts = load_directory(config.input_dir)
        digest = build_digest(alerts)
    except Exception as exc:  # noqa: BLE001
        error = str(exc)
        print(f"[ERROR] failed to load/process alerts: {exc}", file=sys.stderr)
    else:
        _print_report(digest, config.escalate_threshold)

    if error:
        print("Overall: outcome=failure")

    if config.report_enabled:
        try:
            report_run(config, digest, error)
            print("Reported run to AiOps Enabler.")
        except Exception as exc:  # noqa: BLE001
            print(f"AiOps Enabler reporting failed (non-fatal): {exc}", file=sys.stderr)
    else:
        print("AiOps Enabler reporting disabled (no credentials configured).")

    return 1 if error else 0


if __name__ == "__main__":
    raise SystemExit(main())
