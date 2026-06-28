# Design Debt

2026-05-22: WorkClass-in-Plan is deferred until policy consumes it. Promote when a transition uses `WorkClass` to gate or branch behavior.

2026-06-27: VerificationSpec-in-Plan was promoted. `Plan<ClaimsDeclared>` now must declare a `VerificationSpec` before compile, `Plan<Compiled>::validate` checks declared names and policy-required names, `Run` carries the spec, `collect` returns it, and tributary `validate` rejects empty or unknown verification specs.

2026-05-22: RollbackSpec-in-Plan is deferred. It likely belongs near settlement or dispatch safety. Promote when a real rollback path is added.

2026-06-06: Retired top-level Python `distributary/` and `tributary/`
scaffolds left no tracked source to port, but their ignored bytecode preserved
some design residue. The laws already promoted into Rust are claim path
normalization and conflict checks, typed plan/run/deposit motion, retry lineage,
DAG dependency and merge law, validation/merge/baseline construction boundaries,
and content-derived record identity. Do not recreate the Python packages.

Deferred residue from those scaffolds belongs above the kernel until a concrete
transition consumes it:

- `WorkerReturn`-style terminal telemetry: runner-reported dispatch-run id
  matching, terminal state, UTC termination time, exit code,
  prompt/completion token counts, and iteration counts. Promote only when an
  effect runner reports this envelope and a kernel transition consumes the
  telemetry rather than a narrow outcome enum.
- File-change records and content hashes: created/modified/deleted file change
  variants, path-hash-mode validation, canonical file-change-set identity, and
  no-op claims. Promote only when `Deposit` must carry content-addressed file
  changes instead of canonical touched paths.
- Validation evidence: schema pins, check verdicts, known-claim sets, and
  human-judgment verdicts. Promote only when tributary validation consumes
  concrete check evidence. `VerificationSpec` name declaration is already
  promoted; effectful check execution still belongs above the kernel.
- Merge evidence: merge mode, merged commit, validation id cross-checks against
  an external registry, and validated-deposit state checks. Promote only when a
  real settlement layer consumes merge evidence, not while `Merge` remains an
  in-memory accepted validation transition.
