# watershed-tributary

This crate owns inbound lawful settlement.

Legal settlement transitions:

- `validate(Deposit, &[FileClaim]) -> Validation`
- `merge(AcceptedValidation) -> Merge`
- `baseline(Merge) -> Baseline`

Validation enforces two structural invariants on every Deposit-against-Plan pair: the deposit's summary is non-empty, and every path in the deposit's `touched_files` appears in the plan's `FileClaim`s. Neither check is opt-in; both are properties of the `validate` transition itself.

`Validation` is either `Accepted(AcceptedValidation)` or `Rejected(RejectedValidation)`.

`AcceptedValidation`, `Merge`, and `Baseline` have crate-private constructors.

Outside crates can receive those states only through the legal settlement functions.

This crate cannot dispatch plans.

This crate cannot create Tasks.

Outbound motion is owned by `watershed-distributary`.
