"""Kernel-shaped FileClaim mirror and PlanUnitFiles adapter.

Matches the Rust contract shape in watershed-contracts/src/lib.rs without
binding to Rust.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from distributary._compat import _normalize_path
from distributary.plan import PlanUnitFiles


class ClaimKind(StrEnum):
    """The kind of access a plan claims for a file."""

    ReadOnly = "ReadOnly"
    Exclusive = "Exclusive"
    Shared = "Shared"


@dataclass(frozen=True, slots=True)
class FileClaim:
    """A claimed file path and the authority requested over it."""

    path: str
    kind: ClaimKind

    def normalized_path(self) -> str:
        """Return the path form used when comparing claim authority."""
        return _normalize_path(self.path)

    def covers_path(self, path: str) -> bool:
        """Return whether this claim's path authority covers *path*."""
        claim = self.normalized_path()
        other = _normalize_path(path)
        if not claim or not other:
            return False
        return claim == other or other.startswith(f"{claim}/")

    def grants_write_to(self, path: str) -> bool:
        """Return whether this claim grants write authority for *path*."""
        return self.kind is not ClaimKind.ReadOnly and self.covers_path(path)

    def conflicts_with(self, other: FileClaim) -> bool:
        """Return whether this claim and *other* cannot legally run independently."""
        if self.kind is ClaimKind.ReadOnly or other.kind is ClaimKind.ReadOnly:
            return False
        if self.kind is ClaimKind.Shared and other.kind is ClaimKind.Shared:
            return False
        return self.covers_path(other.path) or other.covers_path(self.path)


def adapt_plan_unit_files_to_claims(files: PlanUnitFiles) -> tuple[FileClaim, ...]:
    """Adapt PlanUnitFiles to kernel-shaped FileClaim mirrors.

    Mapping:
    - ``read`` -> ``ReadOnly``
    - ``create`` / ``edit`` / ``delete`` / ``touch`` -> ``Exclusive``

    If the same path appears as both read and write-capable, write authority
    wins and only one ``Exclusive`` claim is emitted.

    Preserves stable first-seen order as much as possible after write-wins.
    Does not emit ``Shared`` until an actual source field consumes it.
    """
    seen: set[str] = set()
    claims: list[FileClaim] = []

    # Write-capable paths first — they win over reads.
    for path in (*files.create, *files.edit, *files.delete, *files.touch):
        norm = _normalize_path(path)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        claims.append(FileClaim(path=norm, kind=ClaimKind.Exclusive))

    # Read-only paths that were not already claimed as write.
    for path in files.read:
        norm = _normalize_path(path)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        claims.append(FileClaim(path=norm, kind=ClaimKind.ReadOnly))

    return tuple(claims)
