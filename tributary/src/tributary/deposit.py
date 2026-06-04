"""Deposit records at tributary's fan-in boundary."""

from __future__ import annotations

import hashlib
import re
from dataclasses import InitVar, dataclass, field
from datetime import datetime
from typing import Literal, Protocol, TypeAlias

from tributary._compat import _canonical_json, _normalize_repo_path, _require_utc

DepositState: TypeAlias = Literal["submitted", "validated", "merged", "rejected", "superseded"]
FileChangeKind: TypeAlias = Literal["create", "modify", "delete"]

_DEPOSIT_STATES = frozenset({"submitted", "validated", "merged", "rejected", "superseded"})
_CLAIM_RE = re.compile(r"^[a-z][a-z0-9_.:-]*$")


class _TransitionToken:
    pass


_TRANSITION_TOKEN = _TransitionToken()


class DispatchRunRecord(Protocol):
    """Protocol shape tributary needs from a dispatch record."""

    @property
    def id(self) -> str: ...

    @property
    def state(self) -> str: ...

    @property
    def worktree_id(self) -> str: ...


@dataclass(frozen=True, slots=True)
class CreatedFileChange:
    """A file created by a worker."""

    path: str
    after_content_hash: str
    mode: str | None = None
    kind: Literal["create"] = field(init=False, default="create")

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_repo_path(self.path))
        _require_content_hash(self.after_content_hash, "after_content_hash")
        _validate_mode(self.mode)


@dataclass(frozen=True, slots=True)
class ModifiedFileChange:
    """A file modified by a worker."""

    path: str
    before_content_hash: str
    after_content_hash: str
    mode: str | None = None
    kind: Literal["modify"] = field(init=False, default="modify")

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_repo_path(self.path))
        _require_content_hash(self.before_content_hash, "before_content_hash")
        _require_content_hash(self.after_content_hash, "after_content_hash")
        _validate_mode(self.mode)


@dataclass(frozen=True, slots=True)
class DeletedFileChange:
    """A file deleted by a worker."""

    path: str
    before_content_hash: str
    mode: str | None = None
    kind: Literal["delete"] = field(init=False, default="delete")

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_repo_path(self.path))
        _require_content_hash(self.before_content_hash, "before_content_hash")
        _validate_mode(self.mode)


FileChange: TypeAlias = CreatedFileChange | ModifiedFileChange | DeletedFileChange


@dataclass(frozen=True, slots=True)
class FileChangeSet:
    """Canonical content-addressed set of file changes."""

    changes: tuple[FileChange, ...] = ()

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for change in self.changes:
            if change.path in seen:
                raise ValueError(f"duplicate file change path: {change.path!r}")
            seen.add(change.path)
        object.__setattr__(self, "changes", tuple(sorted(self.changes, key=lambda c: c.path)))

    def identity(self) -> tuple[dict[str, str | None], ...]:
        """Return the canonical identity payload for this file-change set."""
        return tuple(_file_change_identity(change) for change in self.changes)


@dataclass(frozen=True, slots=True)
class Deposit:
    """A typed proposed change emitted at tributary's ingest boundary."""

    id: str = field(init=False)
    from_dispatch_run_id: str
    worktree_id: str
    commit_ref: str | None
    claims: tuple[str, ...]
    file_changes: FileChangeSet
    submitted_at: datetime
    state: DepositState = "submitted"
    supersedes: str | None = None
    _transition_token: InitVar[_TransitionToken | None] = None

    def __post_init__(self, _transition_token: _TransitionToken | None) -> None:
        _validate_dispatch_run_id(self.from_dispatch_run_id)
        _validate_worktree_id(self.worktree_id)
        _validate_commit_ref(self.commit_ref)
        _validate_deposit_state(self.state)
        if _transition_token is not _TRANSITION_TOKEN and self.state != "submitted":
            raise ValueError("Deposit state transitions must use tributary transition functions")
        _require_utc(self.submitted_at, "submitted_at")
        if self.supersedes is not None:
            _validate_deposit_id(self.supersedes, "supersedes")
        object.__setattr__(self, "claims", _normalize_claims(self.claims))
        object.__setattr__(self, "id", _deposit_id_from_instance(self))


def submit_deposit_from_dispatch_run(
    dispatch_run: DispatchRunRecord,
    *,
    commit_ref: str | None,
    claims: tuple[str, ...],
    file_changes: FileChangeSet,
    submitted_at: datetime,
    supersedes: str | None = None,
) -> Deposit:
    """Create a submitted Deposit from a terminal done dispatch record."""
    _validate_dispatch_run_id(dispatch_run.id)
    if dispatch_run.state != "done":
        raise ValueError(
            f"Deposit submission requires a DispatchRun in state 'done', got {dispatch_run.state!r}"
        )
    return Deposit(
        from_dispatch_run_id=dispatch_run.id,
        worktree_id=dispatch_run.worktree_id,
        commit_ref=commit_ref,
        claims=claims,
        file_changes=file_changes,
        submitted_at=submitted_at,
        state="submitted",
        supersedes=supersedes,
    )


def derive_deposit_id(
    *,
    from_dispatch_run_id: str,
    claims: tuple[str, ...],
    file_changes: FileChangeSet,
    commit_ref: str | None,
) -> str:
    """Content-derive a stable Deposit id with strategy tag ``deposit:``."""
    _validate_dispatch_run_id(from_dispatch_run_id)
    payload = {
        "from_dispatch_run_id": from_dispatch_run_id,
        "claims": _normalize_claims(claims),
        "file_changes": file_changes.identity(),
        "commit_ref": _normalized_commit_ref(commit_ref),
    }
    digest = hashlib.sha256(f"deposit:{_canonical_json(payload)}".encode()).hexdigest()
    return f"deposit:{digest}"


def _deposit_id_from_instance(deposit: Deposit) -> str:
    return derive_deposit_id(
        from_dispatch_run_id=deposit.from_dispatch_run_id,
        claims=deposit.claims,
        file_changes=deposit.file_changes,
        commit_ref=deposit.commit_ref,
    )


def _file_change_identity(change: FileChange) -> dict[str, str | None]:
    before_hash = None
    after_hash = None
    if isinstance(change, CreatedFileChange):
        after_hash = change.after_content_hash
    elif isinstance(change, ModifiedFileChange):
        before_hash = change.before_content_hash
        after_hash = change.after_content_hash
    else:
        before_hash = change.before_content_hash
    return {
        "kind": change.kind,
        "path": change.path,
        "before_content_hash": before_hash,
        "after_content_hash": after_hash,
        "mode": change.mode,
    }


def _require_content_hash(value: str, field_name: str) -> None:
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty content hash")


def _validate_mode(value: str | None) -> None:
    if value is not None and (not value or value.strip() != value):
        raise ValueError("mode must be None or a non-empty string")


def _validate_dispatch_run_id(value: str) -> None:
    if not value.startswith("disprun:"):
        raise ValueError(
            "from_dispatch_run_id must reference a DispatchRun id with 'disprun:' prefix"
        )


def _validate_deposit_id(value: str, field_name: str) -> None:
    if not value.startswith("deposit:"):
        raise ValueError(f"{field_name} must reference a Deposit id with 'deposit:' prefix")


def _validate_worktree_id(value: str) -> None:
    if not value or value.strip() != value:
        raise ValueError("worktree_id must be non-empty")


def _validate_commit_ref(value: str | None) -> None:
    if value is not None and (not value or value.strip() != value):
        raise ValueError("commit_ref must be None or a non-empty string")


def _normalized_commit_ref(value: str | None) -> str | None:
    _validate_commit_ref(value)
    return value


def _validate_deposit_state(value: DepositState) -> None:
    if value not in _DEPOSIT_STATES:
        raise ValueError(f"Invalid Deposit state: {value!r}")


def _normalize_claims(claims: tuple[str, ...]) -> tuple[str, ...]:
    if not claims:
        raise ValueError("claims must be non-empty")
    normalized: list[str] = []
    seen: set[str] = set()
    for claim in claims:
        value = claim.strip()
        if value != claim or not _CLAIM_RE.match(value):
            raise ValueError("claims must be typed-contract names matching ^[a-z][a-z0-9_.:-]*$")
        if value in seen:
            raise ValueError(f"duplicate claim: {value!r}")
        seen.add(value)
        normalized.append(value)
    return tuple(sorted(normalized))
