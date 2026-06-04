"""Merge v0 tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from typing import Any, cast

import pytest

from tributary import (
    CreatedFileChange,
    Deposit,
    FileChangeSet,
    Merge,
    Validation,
    ValidationCheck,
    apply_merge_to_deposit,
    apply_validation_to_deposit,
    derive_merge_id,
    record_merge,
    submit_deposit_from_dispatch_run,
    validate_deposit_integrity,
)

HASH_A = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


class DispatchRunStub:
    id = "disprun:abc123"
    state = "done"
    worktree_id = "/tmp/wt-a"


def _dt(offset: int = 0) -> datetime:
    return datetime(2026, 5, 18, 12, 0, offset, tzinfo=UTC)


def _submitted_deposit(*, claims: tuple[str, ...] = ("claim:code",)) -> Deposit:
    return submit_deposit_from_dispatch_run(
        DispatchRunStub(),
        commit_ref="abc123",
        claims=claims,
        file_changes=FileChangeSet((CreatedFileChange("src/a.py", HASH_A),)),
        submitted_at=_dt(),
    )


def _pass_validation(deposit: Deposit) -> Validation:
    return validate_deposit_integrity(
        deposit,
        known_claims=deposit.claims,
        validator_set_hash="validators:v0",
        validated_at=_dt(1),
        signed_by="watermaster:avulsion",
    )


def _validated_deposit() -> tuple[Deposit, Validation]:
    submitted = _submitted_deposit()
    validation = _pass_validation(submitted)
    return apply_validation_to_deposit(submitted, validation), validation


def _merge(deposit: Deposit, validation: Validation, *, offset: int = 2) -> Merge:
    return record_merge(
        deposit,
        validation,
        target_branch="main",
        base_commit="abc123",
        merged_commit="def456",
        merge_strategy="fast-forward",
        merged_at=_dt(offset),
        merged_by="watermaster:avulsion",
    )


def test_record_merge_from_validated_deposit_and_pass_validation() -> None:
    deposit, validation = _validated_deposit()

    merge = _merge(deposit, validation)

    assert merge.id.startswith("merge:")
    assert merge.deposit_id == deposit.id
    assert merge.validation_id == validation.id
    assert merge.target_branch == "main"
    assert merge.base_commit == "abc123"
    assert merge.merged_commit == "def456"
    assert merge.merge_strategy == "fast-forward"


def test_merge_id_is_stable_and_excludes_time_and_signer() -> None:
    deposit, validation = _validated_deposit()

    first = _merge(deposit, validation, offset=2)
    second = record_merge(
        deposit,
        validation,
        target_branch="main",
        base_commit="abc123",
        merged_commit="def456",
        merge_strategy="fast-forward",
        merged_at=_dt(3),
        merged_by="watermaster:other",
    )

    assert first.id == second.id


def test_merge_id_changes_with_merged_commit() -> None:
    deposit, validation = _validated_deposit()

    first = derive_merge_id(
        deposit_id=deposit.id,
        validation_id=validation.id,
        target_branch="main",
        base_commit="abc123",
        merged_commit="def456",
        merge_strategy="fast-forward",
    )
    second = derive_merge_id(
        deposit_id=deposit.id,
        validation_id=validation.id,
        target_branch="main",
        base_commit="abc123",
        merged_commit="fed654",
        merge_strategy="fast-forward",
    )

    assert first != second


def test_record_merge_rejects_submitted_deposit() -> None:
    deposit = _submitted_deposit()
    validation = _pass_validation(deposit)

    with pytest.raises(ValueError, match="validated Deposit"):
        _merge(deposit, validation)


def test_record_merge_rejects_validation_for_different_deposit() -> None:
    deposit, _ = _validated_deposit()
    other_submitted = _submitted_deposit(claims=("claim:tests",))
    other_validation = _pass_validation(other_submitted)

    with pytest.raises(ValueError, match="does not match"):
        _merge(deposit, other_validation)


def test_record_merge_rejects_non_pass_validation() -> None:
    submitted = _submitted_deposit()
    failed_validation = validate_deposit_integrity(
        submitted,
        known_claims=("claim:tests",),
        validator_set_hash="validators:v0",
        validated_at=_dt(1),
        signed_by="watermaster:avulsion",
    )
    rejected = apply_validation_to_deposit(submitted, failed_validation)

    with pytest.raises(ValueError, match="validated Deposit"):
        _merge(rejected, failed_validation)


def test_record_merge_rejects_validated_deposit_with_fail_validation() -> None:
    deposit, validation = _validated_deposit()
    failed_validation = Validation(
        deposit_id=deposit.id,
        validator_set_hash="validators:v0",
        schema_pins=(),
        checks=(ValidationCheck("claim_integrity:claim:code", "fail", "bad"),),
        verdict="fail",
        reason="one or more integrity checks failed",
        validated_at=_dt(2),
        signed_by="watermaster:avulsion",
    )

    with pytest.raises(ValueError, match="pass Validation"):
        _merge(deposit, failed_validation)


def test_merge_rejects_direct_construction() -> None:
    deposit, validation = _validated_deposit()

    with pytest.raises(ValueError, match="record_merge"):
        Merge(
            deposit_id=deposit.id,
            validation_id=validation.id,
            target_branch="main",
            base_commit="abc123",
            merged_commit="def456",
            merge_strategy="fast-forward",
            merged_at=_dt(2),
            merged_by="watermaster:avulsion",
        )


def test_merge_rejects_explicit_id_override() -> None:
    deposit, validation = _validated_deposit()
    kwargs: dict[str, Any] = {
        "deposit_id": deposit.id,
        "validation_id": validation.id,
        "target_branch": "main",
        "base_commit": "abc123",
        "merged_commit": "def456",
        "merge_strategy": "fast-forward",
        "merged_at": _dt(2),
        "merged_by": "watermaster:avulsion",
        "_id": "merge:forged",
    }

    with pytest.raises(TypeError, match="_id"):
        Merge(**kwargs)


def test_apply_merge_returns_merged_deposit_without_mutating_original() -> None:
    deposit, validation = _validated_deposit()
    merge = _merge(deposit, validation)

    merged = apply_merge_to_deposit(deposit, merge)

    assert deposit.state == "validated"
    assert merged.state == "merged"
    assert merged.id == deposit.id
    assert merged.from_dispatch_run_id == deposit.from_dispatch_run_id
    assert merged.file_changes == deposit.file_changes


def test_apply_merge_rejects_mismatched_deposit_id() -> None:
    deposit, _ = _validated_deposit()
    other_submitted = _submitted_deposit(claims=("claim:tests",))
    other_validation = _pass_validation(other_submitted)
    other_deposit = apply_validation_to_deposit(other_submitted, other_validation)
    other_merge = _merge(other_deposit, other_validation)

    with pytest.raises(ValueError, match="does not match"):
        apply_merge_to_deposit(deposit, other_merge)


def test_apply_merge_rejects_non_validated_deposit() -> None:
    deposit, validation = _validated_deposit()
    merge = _merge(deposit, validation)
    merged = apply_merge_to_deposit(deposit, merge)

    with pytest.raises(ValueError, match="validated"):
        apply_merge_to_deposit(merged, merge)


@pytest.mark.parametrize(
    ("field_name", "overrides"),
    [
        ("target_branch", {"target_branch": ""}),
        ("base_commit", {"base_commit": " abc123"}),
        ("merged_commit", {"merged_commit": ""}),
        ("merge_strategy", {"merge_strategy": " fast-forward"}),
        ("merged_by", {"merged_by": ""}),
    ],
)
def test_merge_rejects_invalid_fields(field_name: str, overrides: dict[str, str]) -> None:
    deposit, validation = _validated_deposit()
    kwargs: dict[str, object] = {
        "target_branch": "main",
        "base_commit": "abc123",
        "merged_commit": "def456",
        "merge_strategy": "fast-forward",
        "merged_at": _dt(2),
        "merged_by": "watermaster:avulsion",
    }
    kwargs.update(overrides)

    with pytest.raises(ValueError, match=field_name):
        record_merge(deposit, validation, **cast(Any, kwargs))


def test_merge_rejects_naive_merged_at() -> None:
    deposit, validation = _validated_deposit()

    with pytest.raises(ValueError, match="merged_at"):
        record_merge(
            deposit,
            validation,
            target_branch="main",
            base_commit="abc123",
            merged_commit="def456",
            merge_strategy="fast-forward",
            merged_at=datetime(2026, 5, 18, 12, 0, 0),
            merged_by="watermaster:avulsion",
        )


def test_merge_rejects_non_utc_merged_at() -> None:
    deposit, validation = _validated_deposit()

    with pytest.raises(ValueError, match="UTC"):
        record_merge(
            deposit,
            validation,
            target_branch="main",
            base_commit="abc123",
            merged_commit="def456",
            merge_strategy="fast-forward",
            merged_at=datetime(2026, 5, 18, 12, 0, 0, tzinfo=timezone(timedelta(hours=1))),
            merged_by="watermaster:avulsion",
        )


def test_merge_is_frozen() -> None:
    deposit, validation = _validated_deposit()
    merge = _merge(deposit, validation)

    with pytest.raises(FrozenInstanceError):
        _assign_strategy(merge)


def _assign_strategy(merge: Any) -> None:
    merge.merge_strategy = "changed"
