# watershed-contracts

This crate owns canonical data shared across the workspace.

- `RecoveredIntent`: structured goal, scope, constraints, and non-goals.
- `WorkClass`: discrete category for planned work.
- `FileClaim`: path plus requested claim kind, with shared path coverage, write-authority, conflict semantics, and canonical authority form. Authority paths normalize to relative slash-separated paths and reject empty paths, absolute paths, parent traversal, and whitespace-only components.
- `ClaimKind`: read-only, exclusive, or shared file authority.
- `VerificationSpec`: declared pressure-test checks for task success; plans must declare one before compile, and validation consumes it by name.
- `RollbackSpec`: declared steps for reverting task work.
- `Policy`: governance rules used to validate compiled plans, including required pressure-test registry names.
- `PressureTest`: named rule and deterministic test path that enforces it, whether the rule is compile-fail or runtime-enforced.
- `ContractError`: shared error type for invalid contract data.

The pressure-test registry is self-checked for trimmed non-empty unique names,
trimmed non-empty claims, and enforcement paths that resolve to files inside the
workspace.

All public contract data derives `Serialize`, `Deserialize`, `JsonSchema`, `Debug`, and `Clone` where applicable.

The schema emitter in `xtask` writes JSON Schema files for public kernel record types across the workspace into `schemas/`.

Top-level Python copies of these contracts are not authoritative; the Rust types in this crate are the source of truth.
