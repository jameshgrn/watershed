---
name: validation-shape
title: Validation Shape
summary: The discipline a typed Validation carries — Deposit identity, frozen input pins, pressure-test and schema evidence, trichotomy verdicts, and the state transition it authorizes.
applies_to: [validation, deposit, tributary, gate, pressure_test, schema, verdict, merge, frozen_pin]
priority: must
version: 1
authored_by: Watermaster Riffle
inscribed: 2026-05-07
canon_anchor: Articles II, IV, V, IX, XII, XIV
---

## When

- validating a Deposit at tributary's boundary
- running pressure tests, schema checks, or semantic settlement against a Deposit
- recording the verdict that authorizes or blocks downstream Merge
- re-validating a frozen Deposit after the validation harness, schema pins, or canonical state changed
- defining a Merge contract that depends on Validation

## Do

- represent every Validation as a typed object carrying: `id` (content-derived, stable), `deposit_id: str`, `validator_set_hash: str`, `schema_pins: Mapping[str, int]`, `pressure_test_results: tuple[CheckResult, ...]`, `schema_checks: tuple[SchemaCheckResult, ...]`, `semantic_settlement_verdict: IntegrationCandidateVerdict`, `verdict: Literal["pass", "fail", "needs_human"]`, `reason: str`, `validated_at: datetime` (UTC tz-aware), `signed_by: WatermasterId`
- compute `id` from `(deposit_id, validator_set_hash, schema_pins, pressure_test_results, schema_checks, semantic_settlement_verdict, verdict, reason)`; the same Deposit checked by the same validators against the same pins with the same evidence yields the same Validation id
- resolve `deposit_id` through tributary's deposit-registry before validation; downstream records reference the Deposit by `deposit_id`, not by worktree path, branch, or commit ref
- treat a Validation as frozen-pinned at record time: `id`, `deposit_id`, `validator_set_hash`, `schema_pins`, evidence fields, `verdict`, and `reason` are immutable thereafter
- recover the worker-SOP bundle from `deposit_id → Deposit.from_dispatch_run_id → DispatchRun.from_plan_id → Plan.sop_set_hash`; do not duplicate the Plan's SOP hash on the Validation
- validate every entry in `Deposit.claims` against the typed-contract registry in `shared/`; every claim receives evidence, failure, or a named reason for `needs_human`
- apply the verdict trichotomy exactly: `pass` authorizes `Deposit.state` transition `submitted → validated`; `fail` authorizes `submitted → rejected`; `needs_human` authorizes no Deposit state transition
- leave a Deposit in `submitted` when the Validation verdict is `needs_human`; unblock only by explicit Watermaster action that records a later `pass` or `fail` Validation, or by a superseding Deposit
- when multiple Validations exist for one Deposit, treat the latest Validation by `validated_at` and append order as the only candidate Merge authorizer; Merge must cite that Validation's `id`, and its verdict must be `pass`
- include truth-source labels on every comparable pressure-test output per `truth-source-labeling.md`
- pin every Dataset schema consulted during validation by integer schema version per `schema-versioning.md`
- preserve the full provenance chain from Source utterance to verdict: `Intent → CompilationRecord → Plan → DispatchRun → Deposit → Validation`

## Do Not

- validate a Deposit by surface forms such as worktree path, branch name, or commit ref
- create `needs_human` as a Deposit state; it is a Validation verdict and a hold
- merge a Deposit whose latest Validation verdict is `fail` or `needs_human`
- treat an earlier `pass` Validation as authorizing Merge after a later Validation exists for the same Deposit
- treat `pass` as an automatic merge; Validation authorizes Merge but does not perform it
- mutate a Validation after human intervention; record a new Validation that references the same `deposit_id`
- drop failed pressure-test, schema, or settlement evidence from the record
- accept a Validation with unpinned schema versions or an unhashable validator set
- copy Plan or Intent fields onto the Validation when they are recoverable through `deposit_id`

## Verify

- every Validation references an existing Deposit by `deposit_id`
- every Validation id is stable under repeat validation with the same Deposit, validators, pins, evidence, verdict, and reason
- every `pass` Validation has complete passing evidence for all required Deposit claims
- every `fail` Validation carries at least one failing check, rejected schema check, or failing settlement verdict
- every `needs_human` Validation leaves the Deposit in `submitted` and records a reason actionable by the Watermaster
- the latest Validation for a Deposit is the only record that can authorize Merge
- every comparable pressure-test output carries a truth-source label
- every schema check records the Dataset schema version it checked against
- a second Validation for the same Deposit appears as a new append-only record; the prior Validation is unchanged

## Escalate

- if the evidence cannot be classified as `pass`, `fail`, or `needs_human` without distortion
- if `needs_human` recurs for the same Deposit after Watermaster intervention; the claim, validator, or Deposit shape is underspecified
- if a validation harness defect is discovered after a `pass` or `fail`; freeze the prior Validation and mint a new one naming the contradiction
- if required schema pins are unavailable; fix the bedrock or quarry lineage gap before validating
- if Validation needs to authorize a state outside `validated` or `rejected`; propose a Deposit lifecycle revision by preflight
