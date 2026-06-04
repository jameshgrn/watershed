"""Internal helpers: path normalization, overlap detection, UTC validation, canonical JSON."""

from __future__ import annotations

import json
from datetime import datetime, timedelta


def _normalize_path(path: str) -> str:
    """Normalize a file path for comparison.

    Strips leading ``./`` prefix(es), trailing ``/``, and surrounding whitespace.
    Matches Rust ``trim_start_matches("./")`` behavior precisely.
    """
    result = path.strip()
    while result.startswith("./"):
        result = result[2:]
    return result.rstrip("/")


def _paths_overlap(a: str, b: str) -> bool:
    """Check if two paths overlap (identical or one is a parent of the other)."""
    norm_a = _normalize_path(a)
    norm_b = _normalize_path(b)
    if not norm_a or not norm_b:
        return False
    return norm_a == norm_b or norm_a.startswith(norm_b + "/") or norm_b.startswith(norm_a + "/")


def _require_utc(value: datetime, field_name: str) -> None:
    """Raise ValueError if *value* is not UTC tz-aware."""
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be UTC tz-aware")


def _canonical_json(value: object) -> str:
    """Return a compact, deterministic JSON representation."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
