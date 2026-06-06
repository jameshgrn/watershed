# Pressure Tests

OnlyLawfulMotion is enforced by `tests/compile_fail/dispatch_unvalidated_plan.rs` and `tests/compile_fail/construct_validated_plan_directly.rs`. The rule is that dispatch only accepts `Plan<Validated>`, and no outside crate can fabricate that validated state without traversing the ceremony.

NoDoubleDispatch is enforced by `tests/compile_fail/dispatch_twice.rs`. The rule is that dispatch consumes the validated plan, so the same plan value cannot be dispatched twice.

SettlementSealed is enforced by `tests/compile_fail/construct_merge_from_distributary.rs`, `tests/compile_fail/construct_baseline_from_distributary.rs`, `tests/compile_fail/merge_rejected_validation.rs`, and `tests/compile_fail/baseline_without_merge.rs`. The rule is that `Merge` and `Baseline` are settlement states owned by `watershed-tributary`, rejected validation cannot be merged, and baseline anchoring requires a `Merge`.

CeremonyIsOrdered is enforced by `tests/compile_fail/skip_intent_recovery.rs`. The rule is that claims cannot be declared before intent recovery, so the outbound ceremony cannot skip or reorder the required states.

WorkerProducesDeposit is enforced by `tests/compile_fail/construct_completed_run_directly.rs`. The rule is that `Run<Completed>` cannot be constructed directly outside `watershed-distributary`, because completed runs represent worker-produced deposits.

DepositConstructorSealed is enforced by `tests/compile_fail/construct_deposit_directly.rs`. The rule is that authoritative `Deposit` records are owned by `watershed-distributary`, are created only by completed-run motion, and cannot be constructed directly by outside crates.

WorkerLifecycleSealed is enforced by `tests/compile_fail/complete_run_before_running.rs` and `tests/compile_fail/retry_completed_run.rs`. The rule is that the worker run lifecycle passes through `Pending → Running → Completed | Failed` in order: a Pending run cannot reach Completed without first becoming Running, and a Completed run cannot be retried. Only failed runs are retryable.

WorkerWaitOutcomeNarrowed is enforced by `tests/compile_fail/wait_done_rejects_kernel_task_state.rs`. The rule is that worker wait completion events accept only `TaskWaitOutcome`, not internal `TaskState`; an effect runner cannot report kernel states such as `Reviewing`, `Merging`, or `Merged` as worker wait results.

TaskStateRejectsDeadVariants is enforced by `tests/compile_fail/task_state_rejects_dead_variants.rs`. The rule is that the public DAG task state enum exposes only lifecycle states the kernel can actually enter; dead states like `Done`, `ReviewedFail`, and `Closed` are not constructible.

ReviewDoneRejectsBooleanVerdictBag is enforced by `tests/compile_fail/review_done_rejects_boolean_verdict_bag.rs`. The rule is that review completion events use a typed `TaskReviewOutcome`, not a boolean/string/count bag that can encode contradictory states.

MergeDoneRejectsOptionalError is enforced by `tests/compile_fail/merge_done_rejects_optional_error.rs`. The rule is that merge completion events use a typed `TaskMergeOutcome`, not an optional error field that encodes success by absence.

## Runtime invariants

Not all pressure tests are compile-fail. Some constitutional rules are about runtime behavior (validation logic, state-transition semantics only verifiable at runtime) and are enforced by deterministic integration tests rather than trybuild fixtures. These tests register their enforcement path in `pressure_tests()` in `watershed-contracts/src/lib.rs` alongside the compile-fail tests.

validation_rejects_unclaimed_files is enforced by `watershed-tributary/tests/claims_integrity.rs`. The rule is that validation rejects any deposit whose `touched_files` includes a path outside the plan's write-authorizing `FileClaim`s. Directory claims cover descendants, sibling paths are outside authority, and `ReadOnly` claims do not authorize touched files. This is a structural invariant — the kernel always enforces it on every Deposit-against-Plan pair, regardless of what the Plan listed in any required-checks field.

retry_lineage_from_failed is enforced by `watershed-distributary/tests/retry_lineage.rs`. The rule is that retrying a failed run preserves the original intent and claims, records `retried_from` pointing at the failed parent's id, increments `retry_index` by one, and derives a new lineage-aware run id. Equivalent retries from the same failed parent produce equal ids; retry lineage survives forward through `start`, `complete`, and `fail` transitions.

retry_respects_max_retries is enforced by `watershed-distributary/tests/retry_budget.rs`. The rule is that retrying a failed run whose current `retry_index` has reached the validating policy's `max_retries` budget returns `RetryError::BudgetExhausted`; an unbounded policy (`max_retries == None`) allows arbitrary retry depth. This is structural governance — the kernel enforces the bound under any policy that declares a finite budget, regardless of what any Plan listed in any required-checks field. The budget is governance, not identity: bounded and unbounded retries from equivalent failed parents produce equal run ids, so `derive_run_id`'s hash composition stays unchanged.

deposit_ids_are_derived is enforced by `watershed-distributary/tests/worker_lifecycle.rs`. The rule is that authoritative `Deposit` records receive content-derived `deposit:` ids from the producing run id, summary, and sorted touched files. Equivalent completed runs with the same touched files in a different input order produce equal deposit ids.

required_pressure_tests_are_registered is enforced by `watershed-distributary/tests/policy_pressure_tests.rs`. The rule is that `Plan<Compiled>::validate(...)` rejects any `Policy.required_pressure_tests` name absent from the `pressure_tests()` registry. This validates names only; it does not run tests, schedule tests, or add an effect layer.

pressure_test_registry_self_consistent is enforced by `watershed-contracts/src/lib.rs`. The rule is that the pressure-test registry is itself well-formed: trimmed names are non-empty and unique, trimmed claims are non-empty, and every `enforced_by` path is non-empty and resolves to a file inside the workspace.

file_claim_paths_reject_escape_forms is enforced by `watershed-contracts/src/lib.rs`, `watershed-distributary/tests/dag_plan.rs`, and `watershed-tributary/tests/claims_integrity.rs`. The rule is that file-claim authority paths reject empty paths, absolute paths, parent traversal, whitespace-only components, and current-directory-only forms before authorizing writes. Valid authority paths normalize to relative slash-separated paths for exact and descendant comparison.

dag_kernel_serial_merge_scan is enforced by `watershed-distributary/tests/dag_kernel.rs`. The rule is that the DAG kernel remains pure and deterministic: dispatch is dependency-gated, merge is serial and topological, terminal failed/skipped tasks do not block later mergeable tasks, non-terminal earlier tasks do block later merge, and failure cascades only to pending dependents. This is the Rust expression of dgov's kernel idea — effects stay outside; the kernel emits typed actions.

dag_kernel_binds_task_panes is enforced by `watershed-distributary/tests/dag_kernel.rs`. The rule is that the DAG kernel binds task pane identity when dispatch is acknowledged, rejects worker wait completion from any other pane, and carries the bound pane into review interrupts and merge actions.

dag_plan_claims_travel_to_merge is enforced by `watershed-distributary/tests/dag_plan.rs`. The rule is that `DagPlan` is the typed declaration layer before kernel state: it rejects claimless tasks, empty claim paths, duplicate task slugs, unknown dependencies, and dependency cycles; preserves deterministic topological order; and carries task `FileClaim`s into the `MergeTask` action used by settlement validation. This is the first bridge from DAG dispatch to the existing `Plan -> Run -> Deposit -> Validation -> Merge -> Baseline` ceremony without adding workers, worktrees, persistence, or a CLI.

dag_plan_rejects_conflicting_claims is enforced by `watershed-distributary/tests/dag_plan.rs`. The rule is that independent DAG tasks cannot both hold overlapping write authority over the same file or directory unless the overlapping claims are explicitly `Shared`. This is the Rust expression of dgov's file-claim conflict law: parallel motion is only legal when authority does not collide, while dependent overlap remains legal because the DAG serializes it.

dag_kernel_rejects_raw_claim_bypass is enforced by `watershed-distributary/tests/dag_kernel.rs`. The rule is that direct DAG kernel construction must carry file claims for every declared task and must reject independent overlapping write authority. Raw kernel construction cannot bypass the `DagPlan` claim law and later emit merge actions with empty or conflicting authority.
