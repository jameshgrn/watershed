# watershed-contracts

This crate owns canonical data shared across the workspace.

- `RecoveredIntent`: structured goal, scope, constraints, and non-goals.
- `WorkClass`: discrete category for planned work.
- `FileClaim`: path plus requested claim kind, with shared path coverage, write-authority, and conflict semantics.
- `ClaimKind`: read-only, exclusive, or shared file authority.
- `VerificationSpec`: declared checks for task success.
- `RollbackSpec`: declared steps for reverting task work.
- `Policy`: governance rules used to validate compiled plans.
- `PressureTest`: named rule and deterministic test path that enforces it.
- `Deposit`: typed worker output collected from completed runs.
- `ContractError`: shared error type for invalid contract data.

All public contract data derives `Serialize`, `Deserialize`, `JsonSchema`, `Debug`, and `Clone` where applicable.

The schema emitter in `xtask` writes JSON Schema files for the public contract types into `schemas/`.
