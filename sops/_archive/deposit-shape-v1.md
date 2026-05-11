---
name: deposit-shape
title: Deposit Shape
summary: The discipline a typed Deposit carries — required fields, frozen-pin at submission, the five-state lifecycle, the typed-claims contract, and the Plan-Intent provenance chain.
applies_to: [deposit, tributary, distributary, worker, claims, validation, merge, supersession]
priority: must
version: 1
authored_by: Watermaster Riffle
inscribed: 2026-05-07
canon_anchor: Articles II, III, IV, IX, XII
---

## When

- emitting a Deposit from a worker subprocess at the typed seam between distributary and tributary
- ingesting a Deposit at tributary's boundary
- registering a Deposit in tributary's deposit-registry
- validating a Deposit (calling `tributary.validate(deposit)`)
- merging a Deposit (calling `tributary.merge(deposit, validation)`)
- proposing a revision Deposit after rejection or to supersede a non-terminal prior
- defining a `Validation`, `Merge`, or `Baseline` contract that references a Deposit

## Do

- represent every Deposit as a typed object carrying: `id` (content-derived, stable), `from_dispatch_run_id: str`, `worktree_id: str`, `commit_ref: str | None`, `claims: tuple[str, ...]`, `file_changes: FileChangeSet`, `submitted_at: datetime` (UTC tz-aware), `state: Literal["submitted", "validated", "merged", "rejected", "superseded"]`, `supersedes: prior_deposit_id | None`
- compute `id` from `(from_dispatch_run_id, claims, file_changes, commit_ref)`; the same dispatch + same claims + same file changes + same commit yields the same Deposit id
- treat a Deposit as frozen-pinned at submission: `id`, `from_dispatch_run_id`, `worktree_id`, `commit_ref`, `claims`, `file_changes`, and `submitted_at` are immutable thereafter
- enumerate every contract the agent claims to satisfy in `claims: tuple[str, ...]`; each entry is a registered typed-contract name in `shared/`, not free-text; an empty tuple is forbidden — a Deposit always claims something, even if just `"no-op"`
- include `commit_ref: str | None` — `None` when the worker submitted without committing (metadata-only work); otherwise the git SHA inside the worktree
- represent the Deposit's lifecycle as `submitted → validated | rejected`; a `validated` Deposit may transition to `merged`; any non-terminal Deposit may transition to `superseded`; `merged` and `superseded` are terminal
- supersede a non-terminal Deposit via a new Deposit whose `supersedes: prior_deposit_id` is set; the prior Deposit's `state` transitions to `superseded` and its other fields are unchanged
- emit `Validation`, `Merge`, and `Baseline` records that reference Deposits by `deposit_id` (not by surface forms like worktree path or commit ref)
- preserve the Plan-Intent provenance chain: a Deposit's `from_dispatch_run_id` resolves to a DispatchRun whose `from_plan_id` resolves to a Plan whose `compiled_from` resolves to one or more Intents per `intent-compilation.md`; the audit trail from Source utterance to Deposit is unbroken

## Do Not

- mutate a Deposit after submission; every revision is a new Deposit with a new `id` and a `supersedes` link
- accept a Deposit at the tributary boundary that lacks `from_dispatch_run_id` or `claims`; both are required identity components
- accept claims that are not registered in `shared/`'s typed-contract registry; freelance claim strings are rejected at the boundary
- reference a Deposit by its worktree path or commit ref outside of the Deposit type itself; downstream code references by `deposit_id`
- silently merge a Deposit whose Validation verdict is `needs_human` without explicit Watermaster intervention
- collapse the Deposit lifecycle by treating `validated → merged` as automatic; a Validation pass does not authorize merge
- conflate `claims` with `file_changes`; claims are typed contracts (semantic), file_changes are paths (operational)
- treat a `merged` or `superseded` Deposit as revisable; both are terminal
- carry `from_plan_id` directly on the Deposit; the Plan id is derivable via `from_dispatch_run_id → DispatchRun.from_plan_id` and duplicating it invites drift

## Verify

- every Deposit at the tributary boundary has a stable content-derived `id`; resubmission of identical work from the same dispatch yields the same id
- every claim in `Deposit.claims` resolves to a registered typed-contract name in `shared/`
- a Deposit's `from_dispatch_run_id` traces to a known DispatchRun, which traces to a known Plan, which traces to known Intent(s) per `intent-compilation.md`
- a Deposit's lifecycle observed across the registry follows only legal transitions (`submitted → validated`, `submitted → rejected`, `validated → merged`, any-non-terminal `→ superseded`); invalid transitions raise typed errors
- a superseding Deposit's `supersedes: prior_deposit_id` references an actual prior Deposit; the prior's state is `superseded` and its other fields are unchanged
- `Validation` records reference Deposits by `deposit_id` and the registry returns the typed Deposit object for each
- a Deposit's compliance posture (which worker-SOP-bundle the agent operated under) is recoverable via `from_dispatch_run_id → Plan.sop_set_hash` per `plan-shape.md`
- a query for "all Deposits in state `submitted`" returns a finite walkable set; a query for "the supersedes-chain from id X" returns the chain in temporal order

## Escalate

- if a Deposit legitimately needs to be re-validated (e.g., the validation harness was wrong) — frozen-pin the original Deposit and Validation, mint a new Validation referencing the same Deposit, name the contradiction in the new Validation's notes
- if `claims: tuple[str, ...]` cannot represent a class of contracts (e.g., parameterized `"satisfies-X-with-tolerance-N"`) — propose a typed `Claim` shape via preflight; do not overload the string format
- if a worker legitimately needs to submit multiple Deposits from one DispatchRun (e.g., partial work + planned continuation) — argue first that two DispatchRuns is the right shape rather than introducing a one-to-many relationship
- if the merge-without-validation case is real (e.g., trivially mechanical changes that bypass typed claims) — propose a `mechanical_merge` flow via preflight; do not freelance
- if the lifecycle needs a sixth state (e.g., `partially_merged`, `pending_review`) — propose via preflight; the five-state lifecycle is canonical until then
- if dgov's existing `IntegrationCandidate` records require migration into Deposits under invariants different from this SOP — frozen-pin them at their dgov state and mint Deposits for going-forward work
- if `from_dispatch_run_id` cannot be resolved (e.g., the DispatchRun was archived before the Deposit was ingested) — that is a layering violation; resolve by extending the lifetime of DispatchRun records, not by allowing orphan Deposits
