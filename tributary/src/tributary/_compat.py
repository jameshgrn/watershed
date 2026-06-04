"""Internal helpers for canonical JSON, UTC validation, and repo paths."""

from __future__ import annotations

import json
from datetime import datetime, timedelta


def _canonical_json(value: object) -> str:
    """Return a compact deterministic JSON representation."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _require_utc(value: datetime, field_name: str) -> None:
    """Raise ValueError if *value* is not UTC tz-aware."""
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be UTC tz-aware")


def _normalize_repo_path(path: str) -> str:
    """Normalize and validate a repo-relative path."""
    result = path.strip()
    while result.startswith("./"):
        result = result[2:]
    result = result.rstrip("/")
    if not result:
        raise ValueError("path must be non-empty")
    if result.startswith("/"):
        raise ValueError(f"path must be repo-relative, got {path!r}")
    parts = result.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"path must not contain empty, '.', or '..' segments: {path!r}")
    return result
