"""Merge records over validated Deposits."""

from __future__ import annotations

import hashlib
from dataclasses import InitVar, dataclass, field
from datetime import datetime

from tributary._compat import _canonical_json, _require_utc
from tributary.deposit import Deposit
from tributary.validation import Validation


@dataclass(frozen=True, slots=True)
class Merge:
    """Frozen record of a successful supplied merge result."""

    id: str = field(init=False)
    deposit_id: str
    validation_id: str
    target_branch: str
    base_commit: str
    merged_commit: str
    merge_strategy: str
    merged_at: datetime
    merged_by: str
    _id: InitVar[str | None] = None

    def __post_init__(self, _id: str | None) -> None:
        _validate_deposit_id(self.deposit_id)
        _validate_validation_id(self.validation_id)
        _require_clean_string(self.target_branch, "target_branch")
        _require_clean_string(self.base_commit, "base_commit")
        _require_clean_string(self.merged_commit, "merged_commit")
        _require_clean_string(self.merge_strategy, "merge_strategy")
        _require_clean_string(self.merged_by, "merged_by")
        _require_utc(self.merged_at, "merged_at")
        object.__setattr__(self, "id", _merge_id_from_instance(self, _id))


def record_merge(
    deposit: Deposit,
    validation: Validation,
    *,
    target_branch: str,
    base_commit: str,
    merged_commit: str,
    merge_strategy: str,
    merged_at: datetime,
    merged_by: str,
) -> Merge:
    """Record a Merge from supplied evidence after validation has authorized it."""
    if deposit.state != "validated":
        raise ValueError(f"Merge requires a validated Deposit, got {deposit.state!r}")
    if validation.deposit_id != deposit.id:
        raise ValueError(
            f"Validation deposit_id does not match Deposit.id: {validation.deposit_id!r} "
            f"!= {deposit.id!r}"
        )
    if validation.verdict != "pass":
        raise ValueError(f"Merge requires a pass Validation, got {validation.verdict!r}")
    return Merge(
        deposit_id=deposit.id,
        validation_id=validation.id,
        target_branch=target_branch,
        base_commit=base_commit,
        merged_commit=merged_commit,
        merge_strategy=merge_strategy,
        merged_at=merged_at,
        merged_by=merged_by,
    )


def apply_merge_to_deposit(deposit: Deposit, merge: Merge) -> Deposit:
    """Return the Deposit state authorized by a Merge without mutating input."""
    if merge.deposit_id != deposit.id:
        raise ValueError(
            f"Merge deposit_id does not match Deposit.id: {merge.deposit_id!r} != {deposit.id!r}"
        )
    if deposit.state != "validated":
        raise ValueError(f"Merge can only apply to validated Deposits, got {deposit.state!r}")
    return Deposit(
        from_dispatch_run_id=deposit.from_dispatch_run_id,
        worktree_id=deposit.worktree_id,
        commit_ref=deposit.commit_ref,
        claims=deposit.claims,
        file_changes=deposit.file_changes,
        submitted_at=deposit.submitted_at,
        state="merged",
        supersedes=deposit.supersedes,
        _id=deposit.id,
    )


def derive_merge_id(
    *,
    deposit_id: str,
    validation_id: str,
    target_branch: str,
    base_commit: str,
    merged_commit: str,
    merge_strategy: str,
) -> str:
    """Content-derive a stable Merge id with strategy tag ``merge:``."""
    _validate_deposit_id(deposit_id)
    _validate_validation_id(validation_id)
    _require_clean_string(target_branch, "target_branch")
    _require_clean_string(base_commit, "base_commit")
    _require_clean_string(merged_commit, "merged_commit")
    _require_clean_string(merge_strategy, "merge_strategy")
    payload = {
        "deposit_id": deposit_id,
        "validation_id": validation_id,
        "target_branch": target_branch,
        "base_commit": base_commit,
        "merged_commit": merged_commit,
        "merge_strategy": merge_strategy,
    }
    digest = hashlib.sha256(f"merge:{_canonical_json(payload)}".encode()).hexdigest()
    return f"merge:{digest}"


def _merge_id_from_instance(merge: Merge, explicit_id: str | None) -> str:
    if explicit_id is not None:
        _validate_merge_id(explicit_id, "_id")
        return explicit_id
    return derive_merge_id(
        deposit_id=merge.deposit_id,
        validation_id=merge.validation_id,
        target_branch=merge.target_branch,
        base_commit=merge.base_commit,
        merged_commit=merge.merged_commit,
        merge_strategy=merge.merge_strategy,
    )


def _validate_deposit_id(value: str) -> None:
    if not value.startswith("deposit:"):
        raise ValueError("deposit_id must reference a Deposit id with 'deposit:' prefix")


def _validate_validation_id(value: str) -> None:
    if not value.startswith("validation:"):
        raise ValueError("validation_id must reference a Validation id with 'validation:' prefix")


def _validate_merge_id(value: str, field_name: str) -> None:
    if not value.startswith("merge:"):
        raise ValueError(f"{field_name} must reference a Merge id with 'merge:' prefix")


def _require_clean_string(value: str, field_name: str) -> None:
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty string without surrounding whitespace")
