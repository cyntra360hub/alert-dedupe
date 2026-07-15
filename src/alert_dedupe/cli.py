"""alert-dedupe command-line entry point."""

from __future__ import annotations

import sys

from alert_dedupe.config import load_config
from alert_dedupe.dedupe import Digest, build_digest
from alert_dedupe.loader import load_directory
from alert_dedupe.reporting import digest_outcome, report_run


def _print_report(digest: Digest, escalate_threshold: int) -> None:
    print(f"{digest.total_alerts} alert(s) -> {digest.total_groups} group(s) "
          f"({digest.noise_reduction_pct}% noise reduction)")
    for group in digest.groups:
        flag = " [ESCALATE]" if group.count >= escalate_threshold else ""
        print(f"  [{group.severity:8}] x{group.count:<3} {group.title!r} "
              f"(sources: {', '.join(group.sources)}){flag}")
    print()
    outcome = digest_outcome(digest, escalate_threshold)
    print(f"Overall: outcome={outcome}")


def main() -> int:
    config = load_config()
    alerts = load_directory(config.input_dir)
    digest = build_digest(alerts)
    _print_report(digest, config.escalate_threshold)

    if config.report_enabled:
        try:
            report_run(config, digest)
            print("Reported run to AiOps Enabler.")
        except Exception as exc:  # noqa: BLE001
            print(f"AiOps Enabler reporting failed (non-fatal): {exc}", file=sys.stderr)
    else:
        print("AiOps Enabler reporting disabled (no credentials configured).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
