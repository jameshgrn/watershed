"""Tributary - fan-in deposit records for Watershed."""

from __future__ import annotations

from tributary.deposit import (
    CreatedFileChange,
    DeletedFileChange,
    Deposit,
    DepositState,
    DispatchRunRecord,
    FileChange,
    FileChangeSet,
    ModifiedFileChange,
    derive_deposit_id,
    submit_deposit_from_dispatch_run,
)
from tributary.merge import Merge, apply_merge_to_deposit, derive_merge_id, record_merge
from tributary.validation import (
    SchemaPin,
    Validation,
    ValidationCheck,
    ValidationVerdict,
    apply_validation_to_deposit,
    authorized_deposit_state,
    derive_validation_id,
    validate_deposit_integrity,
)

__all__ = [
    "apply_merge_to_deposit",
    "apply_validation_to_deposit",
    "authorized_deposit_state",
    "CreatedFileChange",
    "DeletedFileChange",
    "Deposit",
    "DepositState",
    "derive_deposit_id",
    "derive_merge_id",
    "DispatchRunRecord",
    "FileChange",
    "FileChangeSet",
    "Merge",
    "ModifiedFileChange",
    "record_merge",
    "SchemaPin",
    "submit_deposit_from_dispatch_run",
    "validate_deposit_integrity",
    "Validation",
    "ValidationCheck",
    "ValidationVerdict",
    "derive_validation_id",
]
