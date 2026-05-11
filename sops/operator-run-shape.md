---
name: operator-run-shape
title: Operator Run Shape
summary: The discipline a typed OperatorRun carries — required fields, content-derived identity, two-phase frozen-pin, pinned operator spec hash and determinism class, seed-value surfacing, retry lineage, and the Intent-traceable provenance chain.
applies_to: [operatorrun, operator, flume, executor, determinism_class, seed, retry, registry, lifecycle, frozen_pin]
priority: must
version: 1
authored_by: Watermaster Glide
inscribed: 2026-05-10
canon_anchor: Articles II, IV, V, IX, X, XV
---

## When

- constructing an OperatorRun at an executor's submit boundary
- recording an operator execution's terminal telemetry
- proposing a retry from a prior failed or cancelled OperatorRun
- registering an OperatorRun in flume's run-registry (today quarry-registry)
- defining or revising a record that references an OperatorRun by id
- migrating quarry-core's existing `RunRecord` instances into operator-run-shape

## Do

- represent every OperatorRun as a typed object carrying: `id` (content-derived, stable), `operator_name: str`, `operator_spec_hash: str`, `determinism_class: Literal["deterministic", "stable", "stochastic"]`, `input_ids: tuple[str, ...]`, `params_hash: str`, `params: Mapping[str, Any]`, `executor_name: str`, `seed_value: str | int | None`, `retried_from: prior_operator_run_id | None`, `retry_index: int`, `dispatched_by: WatermasterId`, `from_intent_id: str | None`, `submitted_at: datetime` (UTC tz-aware), `state: Literal["pending", "running", "completed", "failed", "cancelled"]`, `started_at: datetime | None` (UTC tz-aware), `completed_at: datetime | None` (UTC tz-aware), `timing_seconds: float | None`, `output: OperatorResult | None`, `error: str`
- compute `id` from `(operator_name, operator_spec_hash, input_ids, params_hash, executor_name, seed_value, retried_from, retry_index, submitted_at)`; these are the inputs that uniquely identify an execution attempt
- compute `operator_spec_hash` as a content hash over the Operator's `OperatorSpec` fields per `sops/operator-shape.md` at the moment the OperatorRun is constructed; the hash pins the operator invariants the run executed under, per CANON Article X
- compute `params_hash` as a content hash over the key-sorted serialized `params` at construction; identity is stable across re-serialization
- pin `determinism_class` at construction from the Operator's `OperatorSpec` per `sops/determinism-class.md`; a later change to the Operator's class does not retroactively rewrite history
- when `determinism_class == "stochastic"`, populate `seed_value` with the value of `params[OperatorSpec.seed_param]`; when `deterministic` or `stable`, leave `seed_value = None`
- preserve the optional Intent provenance chain: when the OperatorRun is the typed action of a CompilationRecord per `sops/intent-compilation.md`, set `from_intent_id` to the originating Intent's id; otherwise leave `None`
- treat input fields as frozen-pinned at dispatch (state transition `pending → running`): `id`, `operator_name`, `operator_spec_hash`, `determinism_class`, `input_ids`, `params_hash`, `params`, `executor_name`, `seed_value`, `retried_from`, `retry_index`, `dispatched_by`, `from_intent_id`, and `submitted_at` are immutable thereafter
- treat output fields as frozen-pinned at terminal (state transition `running → completed | failed | cancelled`): `state`, `output`, `started_at`, `completed_at`, `timing_seconds`, and `error` are immutable thereafter
- inherit OperatorResult's frozen-pin per CANON Article XV: the `output` pointer freezes at terminal, the OperatorResult contents are frozen at construction per `sops/operator-shape.md`
- inherit truth-source labeling on the OperatorResult per `sops/truth-source-labeling.md`; do not duplicate `truth_source_by_field` on the OperatorRun
- represent operator failure as `state == "failed"` with `error` non-empty; never as a fabricated side channel, per `sops/data-contracts.md`
- distinguish validation failure (caught by `validate_inputs` before execution) from execution failure: both end in `state == "failed"`; `error` text discriminates the cause
- increment `retry_index` when `retried_from` is set (`retry_index = retried_from.retry_index + 1`); zero otherwise
- emit downstream records (Artifact registration via `output.artifact.id`, CheckResults via the output's checks, Lineage edges over the input/output artifacts) that reference the OperatorRun by `operator_run_id`, not by surface forms such as executor handle or process id

## Do Not

- mutate an OperatorRun's input fields after `state` transitions out of `pending`; retries are new OperatorRuns with a `retried_from` lineage link
- mutate an OperatorRun's output fields after `state` reaches a terminal value
- assign a non-content-derived id (e.g., `uuid4`); identity is content-derived
- omit `operator_spec_hash`; the Operator's invariants are part of the typed record, not metadata
- omit `determinism_class`; pinning at construction is required regardless of class
- set `seed_value` non-`None` when `determinism_class != "stochastic"`
- set `seed_value` to `None` when `determinism_class == "stochastic"`
- treat an OperatorRun's `state` as observable beyond the five declared values
- include downstream record states (artifact registered, check evaluated, lineage edge written) on the OperatorRun; those belong to Artifact, CheckResult, and Lineage records
- carry executor backend internals (worker pool handle, subprocess pid, SLURM job id) on the OperatorRun as typed fields; they are operational, not lab-canonical — extension via the existing `executor_meta` (quarry-core) or an analogous untyped escape hatch is acceptable; promoting them to typed fields requires preflight
- carry retry lineage as a fork field; OperatorRun has no fork, only retry
- pin `operator_spec_hash` from a copy made before the Operator was registered; hash the registered spec
- pin `determinism_class` from `params` or runtime detection; the source of truth is `OperatorSpec`
- bypass the executor's submit boundary; OperatorRun construction is mediated by the Executor protocol per quarry-core's `executor.py`

## Verify

- every OperatorRun has a stable content-derived `id`; re-construction with the same operator, spec hash, inputs, params hash, executor, seed value, retry lineage, and submission timestamp yields the same id
- every OperatorRun's `operator_spec_hash` is recoverable as the hash of the registered Operator's `OperatorSpec` at `submitted_at`
- every OperatorRun's `determinism_class` matches the Operator's `OperatorSpec.determinism_class` at `submitted_at`
- every OperatorRun with `determinism_class == "stochastic"` has a non-`None` `seed_value`; the value equals `params[OperatorSpec.seed_param]`
- every OperatorRun with `determinism_class != "stochastic"` has `seed_value is None`
- every OperatorRun's lifecycle observed across the registry follows only legal transitions (`pending → running`, `pending → failed` for validation failure, `running → completed | failed | cancelled`); invalid transitions raise typed errors
- an OperatorRun in `state == "completed"` has `output` non-`None` and `error == ""`
- an OperatorRun in `state == "failed"` has `error` non-empty; `output` may be `None` (validation or pre-output execution failure) or non-`None` (post-output failure)
- an OperatorRun's `from_intent_id`, when set, resolves to a known Intent per `sops/intent-compilation.md`
- a query for "all OperatorRuns under an operator name" returns the set; a query for "the retry chain from id X" returns the chain in submission order
- a downstream Artifact's lineage `executor_id` and `operation` reconcile against the OperatorRun by id; the Artifact's content-derived identity per `sops/data-contracts.md` is unaffected by OperatorRun fields
- the OperatorRun's provenance trace `from_intent_id → CompilationRecord → Source utterance` is reconstructible when `from_intent_id` is set

## Escalate

- if a class of OperatorRun originates inside a Worker subprocess (initiated by a DispatchRun rather than a Watermaster intent) — propose a typed `dispatched_by` extension (e.g., a union `WatermasterId | DispatchRunId`) via preflight; do not freelance the field
- if the executor backend requires typed handles (Dask future, SLURM job id) that today's `executor_meta` cannot carry without distortion — propose typed extension via preflight rather than weakening the SOP's typed-field rule
- if `operator_spec_hash` proves unstable across machines (path leakage, environment sensitivity in OperatorSpec construction) — fix the OperatorSpec's reproducibility per `sops/operator-shape.md`, not this SOP
- if `params` cannot be serialized to a stable form (callable params, non-deterministic ordering) — fix the OperatorParams subclass; key-sorted serialization is the canonical form
- if a retry chain becomes deep enough that re-execution semantics diverge from the original (e.g., retried inputs differ subtly from original inputs because of intervening Artifact migrations) — that is a sign the inputs should be re-pinned by content hash, not that retry lineage is wrong
- if today's quarry-core `RunRecord` uuid4 identity must coexist with content-derived identity during migration — frozen-pin existing uuid4 RunRecords at their quarry-core state and mint new OperatorRuns under this SOP for going-forward executions
- if an OperatorRun's `state` enum needs a sixth member (e.g., `timed_out`) — propose via preflight; the five-state lifecycle is canonical until then
- if the bundler-hash-composition gap that `dispatch-run-shape` v1 escalates has an analogue on the operator side (e.g., `OperatorSpec` hash composition misses behavior-affecting fields) — that is an operator-shape revision, not this SOP
