---
name: merge-shape
title: Merge Shape
summary: The discipline a typed Merge carries — Deposit and authorizing Validation identity, frozen merge evidence, successful integration only, and separation from Baseline capture.
applies_to: [merge, deposit, validation, tributary, integration, branch, commit, baseline, provenance]
priority: must
version: 1
authored_by: Watermaster Riffle
inscribed: 2026-05-07
canon_anchor: Articles II, IV, V, IX, XII
---

## When

- merging a validated Deposit into a target branch
- recording a successful integration in tributary history
- transitioning a Deposit from `validated` to `merged`
- preparing a branch for an explicit Baseline capture
- reconstructing the dispatch chain from Source utterance to merged code

## Do

- represent every Merge as a typed object carrying: `id` (content-derived, stable), `deposit_id: str`, `validation_id: str`, `target_branch: str`, `base_commit: str`, `merged_commit: str`, `merge_strategy: str`, `merged_at: datetime` (UTC tz-aware), `merged_by: WatermasterId`
- compute `id` from `(deposit_id, validation_id, target_branch, base_commit, merged_commit, merge_strategy)`; the same authorized Deposit merged to the same target with the same resulting commit yields the same Merge id
- require `validation_id` to resolve to a Validation whose `deposit_id` equals the Merge's `deposit_id`
- require the authorizing Validation verdict to be `pass`
- require the Deposit state to be `validated` before merge begins
- perform the repository merge first; emit a Merge record only after `merged_commit` exists and is reachable from `target_branch`
- transition the Deposit state to `merged` only after the Merge record is written
- treat a Merge as frozen-pinned at record time: `id`, `deposit_id`, `validation_id`, branch fields, commit fields, strategy, and timestamp are immutable thereafter
- preserve the full chain by identity: `Intent → CompilationRecord → Plan → DispatchRun → Deposit → Validation → Merge`
- keep Baseline downstream: create Baseline only through an explicit `tributary.baseline.save(merge_id, branch, name)` call after Merge exists

## Do Not

- emit a Merge for a failed repository merge
- merge a Deposit authorized by a Validation with verdict `fail` or `needs_human`
- merge a Deposit whose `validation_id` points at a different `deposit_id`
- treat Validation `pass` as automatic merge
- reference the Deposit by worktree path, branch, or commit ref outside the Deposit record
- mutate a Merge to attach a later Baseline id; Baseline records point to Merge, not the reverse
- run sentrux or write `.sentrux/baseline.json` as part of Merge
- merge a Deposit whose file changes exceed the PlanUnit file claims without returning to Validation or supersession

## Verify

- the authorizing Validation exists, has verdict `pass`, and references the same `deposit_id`
- the Deposit exists and is in state `validated` before Merge
- the resulting `merged_commit` exists, is reachable from `target_branch`, and includes the Deposit's declared file changes
- the Merge id is stable under repeat construction from the same Deposit, Validation, target branch, base commit, merged commit, and strategy
- the Deposit lifecycle shows `submitted → validated → merged` and no skipped transition
- no Baseline id is stored on the Merge record
- tributary history can walk from Merge to Validation to Deposit to DispatchRun to Plan to Intent

## Escalate

- if the target branch moves between Validation and Merge; re-run merge preparation and consider a new Validation before proceeding
- if conflict resolution requires edits outside the Deposit's file claims; reject or supersede the Deposit rather than widening Merge silently
- if a later Validation contradicts the authorizing `pass` before Merge occurs; freeze both records and require Watermaster decision before merging
- if a class of work must merge without Validation; propose a separate preflighted flow rather than bypassing this SOP
- if policy requires every Merge to produce a Baseline atomically; revise Merge and Baseline together by preflight
