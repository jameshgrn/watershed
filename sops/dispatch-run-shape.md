---
name: dispatch-run-shape
title: Dispatch Run Shape
summary: The discipline a typed DispatchRun carries — required fields, effective worker-SOP bundle and drift, frozen-pin in two phases, retry vs fork lineage, and the Plan-Intent-Deposit provenance chain.
applies_to: [dispatchrun, distributary, worker, dispatch, sop_set_hash, drift, retry, fork, worktree, telemetry, lifecycle]
priority: must
version: 1
authored_by: Watermaster Pool
inscribed: 2026-05-10
canon_anchor: Articles IV, V, IX, XII
---

## When

- compiling a Plan unit's dispatch into a typed DispatchRun at distributary's dispatch boundary
- launching a worker subprocess in a worktree under a Plan
- recording the worker's exit telemetry into the DispatchRun
- proposing a retry or iteration fork from a prior DispatchRun
- registering a DispatchRun in distributary's run-registry
- defining a Deposit, Validation, or Merge contract that references a DispatchRun
- migrating dgov's existing in-flight execution state into watershed's DispatchRun registry

## Do

- represent every DispatchRun as a typed object carrying: `id` (content-derived, stable), `from_plan_id: str`, `unit_slug: str`, `worktree_id: str`, `branch: str`, `base_commit: str`, `agent_model: str`, `effective_sop_set_hash: str`, `drift_against_plan: bool`, `drift_evidence: tuple[str, ...]`, `retried_from: prior_dispatch_run_id | None`, `forked_from: prior_dispatch_run_id | None`, `retry_index: int`, `fork_depth: int`, `dispatched_by: WatermasterId`, `dispatched_at: datetime` (UTC tz-aware), `state: Literal["pending", "active", "done", "failed", "timed_out", "abandoned"]`, `exit_code: int | None`, `last_error: str`, `output_dir: str`, `prompt_tokens: int`, `completion_tokens: int`, `iteration_count: int`, `terminated_at: datetime | None` (UTC tz-aware)
- compute `id` from `(from_plan_id, unit_slug, worktree_id, branch, base_commit, agent_model, effective_sop_set_hash, retried_from, forked_from, retry_index, fork_depth, dispatched_at)`; these are the dispatch inputs that uniquely identify an execution attempt
- compute `effective_sop_set_hash` at dispatch time using the same method the Plan used to compute its `sop_set_hash` per `plan-shape.md`; record the hash of the bundle the worker actually loaded, not the bundle the Plan declared
- compute `drift_against_plan = (effective_sop_set_hash != Plan.sop_set_hash)` and resolve the Plan via `from_plan_id`; record the boolean even when `False`
- when `drift_against_plan == True`, populate `drift_evidence` with one or more typed descriptors of the form `"set:added=<sop>"`, `"set:removed=<sop>"`, or `"metadata:modified=<sop>:<field>"`; when `drift_against_plan == False`, `drift_evidence` is empty
- preserve the Plan-Intent provenance chain: a DispatchRun's `from_plan_id` resolves to a Plan whose `compiled_from` resolves to one or more Intents per `intent-compilation.md`; the audit trail from Source utterance to DispatchRun is unbroken
- restrict the lineage links to mutually exclusive shapes: at most one of `retried_from` and `forked_from` is non-`None`; original executions have both `None`
- distinguish retry from fork: a retry produces a fresh worktree and a new worker subprocess after a prior DispatchRun terminated in `failed | timed_out | abandoned`; a fork continues the same logical work in the same worktree after the prior DispatchRun reached the iteration budget at `timed_out` and the governor authorized continuation
- increment `retry_index` when `retried_from` is set (`retry_index = retried_from.retry_index + 1`); increment `fork_depth` when `forked_from` is set (`fork_depth = forked_from.fork_depth + 1`); zero otherwise
- treat a DispatchRun's input fields as frozen-pinned at dispatch (state transitions `pending → active`): `id`, `from_plan_id`, `unit_slug`, `worktree_id`, `branch`, `base_commit`, `agent_model`, `effective_sop_set_hash`, `drift_against_plan`, `drift_evidence`, `retried_from`, `forked_from`, `retry_index`, `fork_depth`, `dispatched_by`, and `dispatched_at` are immutable thereafter
- treat a DispatchRun's output fields as frozen-pinned at terminal (state transitions `active → done | failed | timed_out | abandoned`): `state`, `exit_code`, `last_error`, `output_dir`, `prompt_tokens`, `completion_tokens`, `iteration_count`, and `terminated_at` are immutable thereafter
- emit Deposit records and kernel events that reference a DispatchRun by `dispatch_run_id`, not by surface forms such as worktree path, pane slug, or branch

## Do Not

- mutate a DispatchRun's input fields after `state` transitions out of `pending`; revisions are new DispatchRuns with retry or fork lineage
- mutate a DispatchRun's output fields after `state` reaches a terminal value
- record both `retried_from` and `forked_from` as non-`None` on the same DispatchRun
- record `retry_index > 0` without a matching non-`None` `retried_from`; record `fork_depth > 0` without a matching non-`None` `forked_from`
- omit `effective_sop_set_hash`; the worker-SOP bundle loaded at dispatch is part of the typed record, not metadata
- omit `drift_against_plan`; the comparison is recorded for every DispatchRun, not only when drift is detected
- treat a DispatchRun's `state` as observable beyond the six declared values
- include kernel TaskState values such as `reviewing`, `reviewed_pass`, `merging`, or `merged` on a DispatchRun; those states belong to subsequent Deposit, Validation, and Merge records per their respective SOPs
- carry `from_intent_id` directly on a DispatchRun; Intent provenance is recoverable via `from_plan_id → Plan.compiled_from`
- carry a downstream Deposit's id on the DispatchRun itself; the Deposit references the DispatchRun by `from_dispatch_run_id` per `deposit-shape.md`
- carry runtime UI state (pane slugs, tmux session ids, terminal window state) on a DispatchRun; runtime UI state is operational, not lab-canonical
- write a DispatchRun whose `from_plan_id` resolves to a Plan that was not in state `dispatched` at `dispatched_at`; subsequent supersession of the Plan does not retroactively invalidate the DispatchRun

## Verify

- every DispatchRun has a stable content-derived `id`; re-construction from the same Plan, unit, worktree, branch, base commit, agent model, effective bundle hash, lineage links, retry/fork counters, and dispatch timestamp yields the same id
- every DispatchRun's `from_plan_id` resolves to a Plan in distributary's plan-registry, and that Plan was in state `dispatched` at `dispatched_at` (it may now be `superseded`)
- every DispatchRun's `effective_sop_set_hash` is recoverable as the hash of the worker-SOP bundle as it stood at `dispatched_at`
- every DispatchRun records `drift_against_plan` as a boolean derived from `effective_sop_set_hash == Plan.sop_set_hash`; when `True`, `drift_evidence` is non-empty and every entry matches a typed descriptor shape
- every DispatchRun's `retried_from` and `forked_from` are not both non-`None`; an originating DispatchRun has both `None`
- every DispatchRun's lifecycle observed across the registry follows only legal transitions (`pending → active`, `active → done | failed | timed_out | abandoned`); invalid transitions raise typed errors
- a DispatchRun in `state == "done"` has `exit_code == 0`; a DispatchRun in `state == "failed"` has `exit_code != 0` and `last_error` non-empty
- a downstream Deposit's `from_dispatch_run_id` resolves to a DispatchRun in state `done`; Deposits cannot reference non-terminal or non-`done` DispatchRuns
- a query for "all DispatchRuns under a Plan" returns the set; a query for "the retry chain from id X" or "the fork chain from id X" returns the chain in dispatch order
- a DispatchRun's provenance trace `from_plan_id → Plan.compiled_from → Intent(s) → CompilationRecord(s) → Source utterance` is reconstructible end-to-end

## Escalate

- if the worker-SOP-bundle hash discipline used by the bundler is structurally insufficient to detect a class of drift (e.g., SOP body changes not reflected in metadata-only hash composition) — propose a bundler-level revision via preflight; do not weaken DispatchRun's typed `drift_against_plan` to compensate
- if a DispatchRun legitimately needs both a retry and a fork lineage (e.g., a forked continuation that itself was retried) — the cleanest model is a chain of DispatchRuns where each carries exactly one lineage link to its immediate predecessor; argue first that this suffices before relaxing the mutual-exclusion rule
- if the DispatchRun `state` enum needs a seventh member (e.g., `cancelled` distinct from `abandoned`) — propose via preflight; the six-state lifecycle is canonical until then
- if a DispatchRun must record runtime UI state (pane slugs, tmux state) for operator inspection — that belongs in operational telemetry, not the lab-canonical record; argue first that a separate operational-state surface suffices
- if dgov's TaskState values beyond the worker-execution span (`reviewing`, `reviewed_pass`, `merging`, `merged`, etc.) need to be mirrored on DispatchRun — that is a layering violation; resolve by lifting those states onto Deposit/Validation/Merge per their respective SOPs
- if a worker subprocess legitimately needs to dispatch without a `from_plan_id` (e.g., system-initiated diagnostic run) — argue first that an internal-Plan shape per `plan-shape.md` suffices rather than introducing untraceable DispatchRuns
- if `drift_evidence` cannot describe a class of drift (e.g., the bundler version itself changed, not the bundle contents) — propose typed extension of the descriptor format via preflight
- if dgov's existing in-flight execution records cannot be lifted into DispatchRuns under these invariants — frozen-pin them at their dgov state and mint DispatchRuns for going-forward work, per the same pattern `plan-shape.md` adopts
