"""Validation v0 tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from typing import Any, cast

import pytest

from tributary import (
    CreatedFileChange,
    Deposit,
    FileChangeSet,
    SchemaPin,
    Validation,
    ValidationCheck,
    ValidationVerdict,
    apply_validation_to_deposit,
    authorized_deposit_state,
    derive_validation_id,
    submit_deposit_from_dispatch_run,
    validate_deposit_integrity,
)

HASH_A = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


class DispatchRunStub:
    id = "disprun:abc123"
    state = "done"
    worktree_id = "/tmp/wt-a"


def _dt(offset: int = 0) -> datetime:
    return datetime(2026, 5, 17, 12, 0, offset, tzinfo=UTC)


def _deposit(*, state: str = "submitted", claims: tuple[str, ...] = ("claim:code",)) -> Deposit:
    deposit = submit_deposit_from_dispatch_run(
        DispatchRunStub(),
        commit_ref=None,
        claims=claims,
        file_changes=FileChangeSet((CreatedFileChange("src/a.py", HASH_A),)),
        submitted_at=_dt(),
    )
    if state == "submitted":
        return deposit
    return Deposit(
        from_dispatch_run_id=deposit.from_dispatch_run_id,
        worktree_id=deposit.worktree_id,
        commit_ref=deposit.commit_ref,
        claims=deposit.claims,
        file_changes=deposit.file_changes,
        submitted_at=deposit.submitted_at,
        state=cast(Any, state),
        _id=deposit.id,
    )


def test_validate_deposit_integrity_passes_known_claims() -> None:
    validation = validate_deposit_integrity(
        _deposit(),
        known_claims=("claim:code",),
        validator_set_hash="validators:v0",
        schema_pins=(SchemaPin("dataset-a", 1),),
        validated_at=_dt(),
        signed_by="watermaster:avulsion",
    )

    assert validation.id.startswith("validation:")
    assert validation.deposit_id.startswith("deposit:")
    assert validation.verdict == "pass"
    assert authorized_deposit_state(validation) == "validated"
    assert validation.checks == (
        ValidationCheck(
            name="claim_integrity:claim:code",
            verdict="pass",
            reason="claim is known to this validation run",
        ),
        ValidationCheck(
            name="file_changes:content_identity",
            verdict="pass",
            reason="file changes carry canonical content identity",
        ),
    )


def test_validate_deposit_integrity_fails_unknown_claims() -> None:
    validation = validate_deposit_integrity(
        _deposit(),
        known_claims=("claim:tests",),
        validator_set_hash="validators:v0",
        validated_at=_dt(),
        signed_by="watermaster:avulsion",
    )

    assert validation.verdict == "fail"
    assert authorized_deposit_state(validation) == "rejected"
    assert validation.checks[0] == ValidationCheck(
        name="claim_integrity:claim:code",
        verdict="fail",
        reason="claim is not in supplied known_claims",
    )


def test_validate_deposit_integrity_rejects_non_submitted_deposit() -> None:
    with pytest.raises(ValueError, match="submitted"):
        validate_deposit_integrity(
            _deposit(state="validated"),
            known_claims=("claim:code",),
            validator_set_hash="validators:v0",
            validated_at=_dt(),
            signed_by="watermaster:avulsion",
        )


def test_validation_id_is_stable_and_excludes_time_and_signer() -> None:
    first = validate_deposit_integrity(
        _deposit(),
        known_claims=("claim:code",),
        validator_set_hash="validators:v0",
        validated_at=_dt(),
        signed_by="watermaster:avulsion",
    )
    second = validate_deposit_integrity(
        _deposit(),
        known_claims=("claim:code",),
        validator_set_hash="validators:v0",
        validated_at=_dt(1),
        signed_by="watermaster:other",
    )

    assert first.id == second.id


def test_validation_id_changes_with_evidence() -> None:
    deposit = _deposit()
    passed = derive_validation_id(
        deposit_id=deposit.id,
        validator_set_hash="validators:v0",
        schema_pins=(),
        checks=(
            ValidationCheck(
                "claim_integrity:claim:code",
                "pass",
                "claim is known to this validation run",
            ),
        ),
        verdict="pass",
        reason="all integrity checks passed",
    )
    failed = derive_validation_id(
        deposit_id=deposit.id,
        validator_set_hash="validators:v0",
        schema_pins=(),
        checks=(
            ValidationCheck(
                "claim_integrity:claim:code",
                "fail",
                "claim is not in supplied known_claims",
            ),
        ),
        verdict="fail",
        reason="one or more integrity checks failed",
    )

    assert passed != failed


def test_validation_canonicalizes_schema_pins_and_checks() -> None:
    deposit = _deposit()
    validation = Validation(
        deposit_id=deposit.id,
        validator_set_hash="validators:v0",
        schema_pins=(SchemaPin("z", 2), SchemaPin("a", 1)),
        checks=(
            ValidationCheck("z-check", "pass", "z passed"),
            ValidationCheck("a-check", "pass", "a passed"),
        ),
        verdict="pass",
        reason="all integrity checks passed",
        validated_at=_dt(),
        signed_by="watermaster:avulsion",
    )

    assert validation.schema_pins == (SchemaPin("a", 1), SchemaPin("z", 2))
    assert validation.checks == (
        ValidationCheck("a-check", "pass", "a passed"),
        ValidationCheck("z-check", "pass", "z passed"),
    )


def test_needs_human_validation_authorizes_no_deposit_state() -> None:
    validation = Validation(
        deposit_id=_deposit().id,
        validator_set_hash="validators:v0",
        schema_pins=(),
        checks=(
            ValidationCheck("claim_integrity:claim:code", "needs_human", "registry unavailable"),
        ),
        verdict="needs_human",
        reason="one or more integrity checks need human judgment",
        validated_at=_dt(),
        signed_by="watermaster:avulsion",
    )

    assert authorized_deposit_state(validation) is None


def test_apply_pass_validation_returns_validated_deposit_without_mutating_original() -> None:
    deposit = _deposit()
    validation = validate_deposit_integrity(
        deposit,
        known_claims=("claim:code",),
        validator_set_hash="validators:v0",
        validated_at=_dt(),
        signed_by="watermaster:avulsion",
    )

    applied = apply_validation_to_deposit(deposit, validation)

    assert deposit.state == "submitted"
    assert applied.state == "validated"
    assert applied.id == deposit.id
    assert applied.from_dispatch_run_id == deposit.from_dispatch_run_id
    assert applied.file_changes == deposit.file_changes


def test_apply_fail_validation_returns_rejected_deposit() -> None:
    deposit = _deposit()
    validation = validate_deposit_integrity(
        deposit,
        known_claims=("claim:tests",),
        validator_set_hash="validators:v0",
        validated_at=_dt(),
        signed_by="watermaster:avulsion",
    )

    applied = apply_validation_to_deposit(deposit, validation)

    assert applied.state == "rejected"
    assert applied.id == deposit.id


def test_apply_needs_human_validation_returns_submitted_deposit_unchanged() -> None:
    deposit = _deposit()
    validation = Validation(
        deposit_id=deposit.id,
        validator_set_hash="validators:v0",
        schema_pins=(),
        checks=(
            ValidationCheck("claim_integrity:claim:code", "needs_human", "registry unavailable"),
        ),
        verdict="needs_human",
        reason="one or more integrity checks need human judgment",
        validated_at=_dt(),
        signed_by="watermaster:avulsion",
    )

    assert apply_validation_to_deposit(deposit, validation) is deposit


def test_apply_validation_rejects_mismatched_deposit_id() -> None:
    deposit = _deposit()
    other = _deposit(claims=("claim:tests",))
    validation = validate_deposit_integrity(
        other,
        known_claims=("claim:tests",),
        validator_set_hash="validators:v0",
        validated_at=_dt(),
        signed_by="watermaster:avulsion",
    )

    with pytest.raises(ValueError, match="does not match"):
        apply_validation_to_deposit(deposit, validation)


def test_apply_validation_rejects_non_submitted_deposit() -> None:
    deposit = _deposit()
    validation = validate_deposit_integrity(
        deposit,
        known_claims=("claim:code",),
        validator_set_hash="validators:v0",
        validated_at=_dt(),
        signed_by="watermaster:avulsion",
    )
    validated = apply_validation_to_deposit(deposit, validation)

    with pytest.raises(ValueError, match="submitted"):
        apply_validation_to_deposit(validated, validation)


@pytest.mark.parametrize(
    "schema_pin",
    [
        lambda: SchemaPin("", 1),
        lambda: SchemaPin("dataset-a", 0),
    ],
)
def test_schema_pin_rejects_invalid_values(schema_pin) -> None:
    with pytest.raises(ValueError):
        schema_pin()


@pytest.mark.parametrize(
    "check",
    [
        lambda: ValidationCheck("", "pass", "ok"),
        lambda: ValidationCheck("claim:code", cast(ValidationVerdict, "unknown"), "ok"),
        lambda: ValidationCheck("claim:code", "pass", ""),
    ],
)
def test_validation_check_rejects_invalid_values(check) -> None:
    with pytest.raises(ValueError):
        check()


def test_validation_rejects_invalid_deposit_id() -> None:
    with pytest.raises(ValueError, match="deposit"):
        Validation(
            deposit_id="disprun:abc123",
            validator_set_hash="validators:v0",
            schema_pins=(),
            checks=(ValidationCheck("claim:code", "pass", "ok"),),
            verdict="pass",
            reason="all integrity checks passed",
            validated_at=_dt(),
            signed_by="watermaster:avulsion",
        )


def test_validation_rejects_naive_validated_at() -> None:
    with pytest.raises(ValueError, match="validated_at"):
        Validation(
            deposit_id=_deposit().id,
            validator_set_hash="validators:v0",
            schema_pins=(),
            checks=(ValidationCheck("claim:code", "pass", "ok"),),
            verdict="pass",
            reason="all integrity checks passed",
            validated_at=datetime(2026, 5, 17, 12, 0, 0),
            signed_by="watermaster:avulsion",
        )


def test_validation_rejects_non_utc_validated_at() -> None:
    with pytest.raises(ValueError, match="UTC"):
        Validation(
            deposit_id=_deposit().id,
            validator_set_hash="validators:v0",
            schema_pins=(),
            checks=(ValidationCheck("claim:code", "pass", "ok"),),
            verdict="pass",
            reason="all integrity checks passed",
            validated_at=datetime(2026, 5, 17, 12, 0, 0, tzinfo=timezone(timedelta(hours=1))),
            signed_by="watermaster:avulsion",
        )


def test_validation_rejects_duplicate_schema_pins() -> None:
    with pytest.raises(ValueError, match="duplicate schema"):
        Validation(
            deposit_id=_deposit().id,
            validator_set_hash="validators:v0",
            schema_pins=(SchemaPin("dataset-a", 1), SchemaPin("dataset-a", 2)),
            checks=(ValidationCheck("claim:code", "pass", "ok"),),
            verdict="pass",
            reason="all integrity checks passed",
            validated_at=_dt(),
            signed_by="watermaster:avulsion",
        )


def test_validation_rejects_duplicate_checks() -> None:
    with pytest.raises(ValueError, match="duplicate validation"):
        Validation(
            deposit_id=_deposit().id,
            validator_set_hash="validators:v0",
            schema_pins=(),
            checks=(
                ValidationCheck("claim:code", "pass", "ok"),
                ValidationCheck("claim:code", "pass", "still ok"),
            ),
            verdict="pass",
            reason="all integrity checks passed",
            validated_at=_dt(),
            signed_by="watermaster:avulsion",
        )


def test_validation_rejects_verdict_that_does_not_match_checks() -> None:
    with pytest.raises(ValueError, match="does not match"):
        Validation(
            deposit_id=_deposit().id,
            validator_set_hash="validators:v0",
            schema_pins=(),
            checks=(ValidationCheck("claim:code", "fail", "bad"),),
            verdict="pass",
            reason="all integrity checks passed",
            validated_at=_dt(),
            signed_by="watermaster:avulsion",
        )


def test_validate_deposit_integrity_rejects_empty_known_claims() -> None:
    with pytest.raises(ValueError, match="known_claims"):
        validate_deposit_integrity(
            _deposit(),
            known_claims=(),
            validator_set_hash="validators:v0",
            validated_at=_dt(),
            signed_by="watermaster:avulsion",
        )


def test_validation_is_frozen() -> None:
    validation = validate_deposit_integrity(
        _deposit(),
        known_claims=("claim:code",),
        validator_set_hash="validators:v0",
        validated_at=_dt(),
        signed_by="watermaster:avulsion",
    )

    with pytest.raises(FrozenInstanceError):
        _assign_reason(validation)


def _assign_reason(validation: Any) -> None:
    validation.reason = "changed"
