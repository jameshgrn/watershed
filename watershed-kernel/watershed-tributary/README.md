# watershed-tributary

This crate owns inbound lawful settlement.

It consumes `watershed_distributary::Deposit`; it does not create deposits.

Legal settlement transitions:

- `validate(Deposit, &[FileClaim], &VerificationSpec) -> Validation`
- `merge(AcceptedValidation) -> Merge`
- `baseline(Merge) -> Baseline`

Validation enforces three structural invariants on every Deposit-against-Plan pair: the verification spec declares at least one registered pressure-test name, the deposit's summary is non-empty, and every path in the deposit's `touched_files` is covered by a write-authorizing `FileClaim`. Directory claims cover descendants, sibling paths are outside authority, and `ReadOnly` claims do not authorize touched files. None of these checks is opt-in; they are properties of the `validate` transition itself.

`Validation` is either `Accepted(AcceptedValidation)` or `Rejected(RejectedValidation)`.

`AcceptedValidation`, `Merge`, and `Baseline` have crate-private constructors and content-derived ids: `validation:`, `merge:`, and `baseline:` respectively.

Outside crates can receive those states only through the legal settlement functions.

This crate cannot create deposits.

This crate cannot dispatch plans.

This crate cannot create Tasks.

Outbound motion is owned by `watershed-distributary`.
