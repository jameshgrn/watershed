# tributary/

**Agent ingest.** Where completed work first flows back in.

## Provenance

Half of `dgov/` - the fan-in half. v0 keeps typed fan-in records in memory.

## What v0 Owns

- **Deposit records** - typed proposed changes from terminal dispatch runs
- **File changes** - content-addressed file-change sets supplied as data
- **Claim names** - non-empty typed-contract strings, pending a shared registry
- **Validation records** - integrity verdicts over submitted Deposits
- **Merge records** - successful supplied integration evidence over validated Deposits

## Public Types (v0)

| Type | Module | Purpose |
|---|---|---|
| `Deposit` | `deposit` | Submitted proposed change keyed by `from_dispatch_run_id` |
| `DepositState` | `deposit` | `submitted` / `validated` / `merged` / `rejected` / `superseded` |
| `CreatedFileChange` | `deposit` | Created file with after-content hash |
| `ModifiedFileChange` | `deposit` | Modified file with before/after content hashes |
| `DeletedFileChange` | `deposit` | Deleted file with before-content hash |
| `FileChangeSet` | `deposit` | Canonical content-addressed set of file changes |
| `derive_deposit_id` | `deposit` | Content-derived stable id with `deposit:` tag |
| `submit_deposit_from_dispatch_run` | `deposit` | Builds a submitted Deposit from a done dispatch record |
| `Validation` | `validation` | Frozen verdict over a submitted Deposit |
| `ValidationVerdict` | `validation` | `pass` / `fail` / `needs_human` |
| `ValidationCheck` | `validation` | Evidence for one validation check |
| `SchemaPin` | `validation` | Dataset schema version pin consulted by validation |
| `derive_validation_id` | `validation` | Content-derived stable id with `validation:` tag |
| `validate_deposit_integrity` | `validation` | Supplied-data integrity validator for submitted Deposits |
| `authorized_deposit_state` | `validation` | Pure mapping from verdict to authorized Deposit state |
| `apply_validation_to_deposit` | `validation` | Pure in-memory Validation application |
| `Merge` | `merge` | Successful integration record citing Deposit and Validation |
| `derive_merge_id` | `merge` | Content-derived stable id with `merge:` tag |
| `record_merge` | `merge` | Builds a Merge from a validated Deposit and pass Validation |
| `apply_merge_to_deposit` | `merge` | Pure in-memory Merge application |

## Design Constraints

- **No dgov imports** - clean watershed package; no dependency on `dgov`.
- **No distributary runtime import** - submit from a protocol-shaped dispatch record.
- **No worktree discovery** - file changes are supplied data, not git diff output.
- **No real merge execution** - merge records consume supplied commit evidence; no git operations.
- **Transition-only deposits** - submitted Deposits advance through validation and merge functions.
- **Factory-only merge records** - Merge records are built by `record_merge`, not direct construction.
- **Derived IDs only** - record constructors do not accept explicit id overrides.
- **No baseline** - Merge does not run sentrux or capture Baseline records.
- **No registry or persistence** - validation consumes supplied data and emits records only.

## Why "tributary"

In a river system, tributaries are smaller channels flowing *into* a larger one — the inverse of a distributary. In agentic terms: many parallel agent outputs flowing back into the main trunk after validation.

The metaphor goes the right way: tributary is *inflow*. Work returns here, gets vetted, joins the main channel.

## Pair

`distributary/` is the matched fan-out. Together they replace dgov, with the dispatch/ingest split made explicit by separate modules.

## Why split dgov in two

Different invariants on each side. Distributary is concerned with *creating valid work* (planning, dispatch, governance of in-flight runs). Tributary is concerned with *certifying completed work* (typed validation, merge integrity, baseline anchoring). Combining them in one module hid that asymmetry; splitting them makes each phase auditable on its own terms.

## Status

v0 Deposit, Validation, and Merge records implemented.
