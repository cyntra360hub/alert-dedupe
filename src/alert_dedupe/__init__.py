"""alert-dedupe: deduplicates and groups alerts from pluggable sources
into a compact digest."""

from alert_dedupe.dedupe import Digest, build_digest

__all__ = ["Digest", "build_digest"]
__version__ = "0.1.0"
