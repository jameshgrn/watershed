"""Validation records over submitted Deposits."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, TypeAlias

from tributary._compat import _canonical_json, _require_utc
from tributary.deposit import _TRANSITION_TOKEN, Deposit, DepositState

ValidationVerdict: TypeAlias = Literal["pass", "fail", "needs_human"]

_VALIDATION_VERDICTS = frozenset({"pass", "fail", "needs_human"})


@dataclass(frozen=True, slots=True)
class SchemaPin:
    """Dataset schema version consulted during validation."""

    name: str
    version: int

    def __post_init__(self) -> None:
        _require_clean_string(self.name, "schema pin name")
        if self.version < 1:
            raise ValueError("schema pin version must be >= 1")

    def identity(self) -> dict[str, int | str]:
        """Return canonical identity data for this schema pin."""
        return {"name": self.name, "version": self.version}


@dataclass(frozen=True, slots=True)
class ValidationCheck:
    """Evidence for one validation check."""

    name: str
    verdict: ValidationVerdict
    reason: str

    def __post_init__(self) -> None:
        _require_clean_string(self.name, "validation check name")
        _validate_verdict(self.verdict)
        _require_clean_string(self.reason, "validation check reason")

    def identity(self) -> dict[str, str]:
        """Return canonical identity data for this check."""
        return {
            "name": self.name,
            "verdict": self.verdict,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class Validation:
    """Frozen validation verdict over a Deposit."""

    id: str = field(init=False)
    deposit_id: str
    validator_set_hash: str
    schema_pins: tuple[SchemaPin, ...]
    checks: tuple[ValidationCheck, ...]
    verdict: ValidationVerdict
    reason: str
    validated_at: datetime
    signed_by: str

    def __post_init__(self) -> None:
        _validate_deposit_id(self.deposit_id)
        _require_clean_string(self.validator_set_hash, "validator_set_hash")
        _require_clean_string(self.reason, "reason")
        _require_clean_string(self.signed_by, "signed_by")
        _require_utc(self.validated_at, "validated_at")
        _validate_verdict(self.verdict)
        schema_pins = _normalize_schema_pins(self.schema_pins)
        checks = _normalize_checks(self.checks)
        _validate_verdict_matches_checks(self.verdict, checks)
        object.__setattr__(self, "schema_pins", schema_pins)
        object.__setattr__(self, "checks", checks)
        object.__setattr__(self, "id", _validation_id_from_instance(self))


def validate_deposit_integrity(
    deposit: Deposit,
    *,
    known_claims: tuple[str, ...],
    validator_set_hash: str,
    validated_at: datetime,
    signed_by: str,
    schema_pins: tuple[SchemaPin, ...] = (),
) -> Validation:
    """Validate supplied-data integrity for a submitted Deposit."""
    if deposit.state != "submitted":
        raise ValueError(f"Validation requires a submitted Deposit, got {deposit.state!r}")
    known = _normalize_known_claims(known_claims)
    checks = [_claim_check(claim, known) for claim in deposit.claims]
    checks.append(_file_change_identity_check(deposit))
    verdict = _derive_verdict(tuple(checks))
    return Validation(
        deposit_id=deposit.id,
        validator_set_hash=validator_set_hash,
        schema_pins=schema_pins,
        checks=tuple(checks),
        verdict=verdict,
        reason=_validation_reason(verdict),
        validated_at=validated_at,
        signed_by=signed_by,
    )


def authorized_deposit_state(validation: Validation) -> DepositState | None:
    """Return the Deposit state this Validation authorizes, if any."""
    if validation.verdict == "pass":
        return "validated"
    if validation.verdict == "fail":
        return "rejected"
    return None


def apply_validation_to_deposit(deposit: Deposit, validation: Validation) -> Deposit:
    """Return the Deposit state authorized by a Validation without mutating input."""
    if validation.deposit_id != deposit.id:
        raise ValueError(
            f"Validation deposit_id does not match Deposit.id: {validation.deposit_id!r} "
            f"!= {deposit.id!r}"
        )
    if deposit.state != "submitted":
        raise ValueError(f"Validation can only apply to submitted Deposits, got {deposit.state!r}")
    target_state = authorized_deposit_state(validation)
    if target_state is None:
        return deposit
    return Deposit(
        from_dispatch_run_id=deposit.from_dispatch_run_id,
        worktree_id=deposit.worktree_id,
        commit_ref=deposit.commit_ref,
        claims=deposit.claims,
        file_changes=deposit.file_changes,
        submitted_at=deposit.submitted_at,
        state=target_state,
        supersedes=deposit.supersedes,
        _transition_token=_TRANSITION_TOKEN,
    )


def derive_validation_id(
    *,
    deposit_id: str,
    validator_set_hash: str,
    schema_pins: tuple[SchemaPin, ...],
    checks: tuple[ValidationCheck, ...],
    verdict: ValidationVerdict,
    reason: str,
) -> str:
    """Content-derive a stable Validation id with strategy tag ``validation:``."""
    _validate_deposit_id(deposit_id)
    _require_clean_string(validator_set_hash, "validator_set_hash")
    _validate_verdict(verdict)
    _require_clean_string(reason, "reason")
    normalized_schema_pins = _normalize_schema_pins(schema_pins)
    normalized_checks = _normalize_checks(checks)
    _validate_verdict_matches_checks(verdict, normalized_checks)
    payload = {
        "deposit_id": deposit_id,
        "validator_set_hash": validator_set_hash,
        "schema_pins": tuple(pin.identity() for pin in normalized_schema_pins),
        "checks": tuple(check.identity() for check in normalized_checks),
        "verdict": verdict,
        "reason": reason,
    }
    digest = hashlib.sha256(f"validation:{_canonical_json(payload)}".encode()).hexdigest()
    return f"validation:{digest}"


def _validation_id_from_instance(validation: Validation) -> str:
    return derive_validation_id(
        deposit_id=validation.deposit_id,
        validator_set_hash=validation.validator_set_hash,
        schema_pins=validation.schema_pins,
        checks=validation.checks,
        verdict=validation.verdict,
        reason=validation.reason,
    )


def _claim_check(claim: str, known_claims: frozenset[str]) -> ValidationCheck:
    if claim in known_claims:
        return ValidationCheck(
            name=f"claim_integrity:{claim}",
            verdict="pass",
            reason="claim is known to this validation run",
        )
    return ValidationCheck(
        name=f"claim_integrity:{claim}",
        verdict="fail",
        reason="claim is not in supplied known_claims",
    )


def _file_change_identity_check(deposit: Deposit) -> ValidationCheck:
    deposit.file_changes.identity()
    return ValidationCheck(
        name="file_changes:content_identity",
        verdict="pass",
        reason="file changes carry canonical content identity",
    )


def _derive_verdict(checks: tuple[ValidationCheck, ...]) -> ValidationVerdict:
    if any(check.verdict == "needs_human" for check in checks):
        return "needs_human"
    if any(check.verdict == "fail" for check in checks):
        return "fail"
    return "pass"


def _validation_reason(verdict: ValidationVerdict) -> str:
    if verdict == "pass":
        return "all integrity checks passed"
    if verdict == "fail":
        return "one or more integrity checks failed"
    return "one or more integrity checks need human judgment"


def _normalize_schema_pins(schema_pins: tuple[SchemaPin, ...]) -> tuple[SchemaPin, ...]:
    seen: set[str] = set()
    normalized = tuple(sorted(schema_pins, key=lambda pin: pin.name))
    for pin in normalized:
        if pin.name in seen:
            raise ValueError(f"duplicate schema pin: {pin.name!r}")
        seen.add(pin.name)
    return normalized


def _normalize_checks(checks: tuple[ValidationCheck, ...]) -> tuple[ValidationCheck, ...]:
    if not checks:
        raise ValueError("checks must be non-empty")
    seen: set[str] = set()
    normalized = tuple(sorted(checks, key=lambda check: check.name))
    for check in normalized:
        if check.name in seen:
            raise ValueError(f"duplicate validation check: {check.name!r}")
        seen.add(check.name)
    return normalized


def _normalize_known_claims(claims: tuple[str, ...]) -> frozenset[str]:
    if not claims:
        raise ValueError("known_claims must be non-empty")
    normalized: set[str] = set()
    for claim in claims:
        _require_clean_string(claim, "known claim")
        if claim in normalized:
            raise ValueError(f"duplicate known claim: {claim!r}")
        normalized.add(claim)
    return frozenset(normalized)


def _validate_verdict_matches_checks(
    verdict: ValidationVerdict,
    checks: tuple[ValidationCheck, ...],
) -> None:
    derived = _derive_verdict(checks)
    if verdict != derived:
        raise ValueError(
            f"Validation verdict {verdict!r} does not match check verdicts {derived!r}"
        )


def _validate_verdict(value: ValidationVerdict) -> None:
    if value not in _VALIDATION_VERDICTS:
        raise ValueError(f"Invalid Validation verdict: {value!r}")


def _validate_deposit_id(value: str) -> None:
    if not value.startswith("deposit:"):
        raise ValueError("deposit_id must reference a Deposit id with 'deposit:' prefix")


def _require_clean_string(value: str, field_name: str) -> None:
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty string without surrounding whitespace")
