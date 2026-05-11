---
name: plan-shape
title: Plan Shape
summary: The discipline a typed Plan carries — required fields, widened identity inputs, frozen-pin after dispatch, worker-SOP-bundle layering, validation gates, and top-level supersession.
applies_to: [plan, planspec, planunit, dagdefinition, dispatch, distributary, sop_set_hash, supersession, identity]
priority: must
version: 2
authored_by: Watermaster Riffle
inscribed: 2026-05-07
canon_anchor: Articles V, VI, IX, XII
---

## When

- compiling an Intent (or sequence of Intents) into a typed Plan for dispatch
- registering a new Plan in distributary's plan-registry
- proposing a revision to a previously dispatched Plan
- declaring or rotating the worker-SOP bundle that a Plan carries
- migrating dgov's existing in-flight Plans into watershed's plan-registry
- defining a Plan-derived contract (`Deposit`, `Validation`, `Merge`, `Baseline`) downstream of dispatch

## Do

- represent every Plan as a typed object carrying: `id` (content-derived, stable), `compiled_from: Intent | tuple[Intent, ...]`, `units: Mapping[slug, PlanUnit] | DagDefinition`, `sop_set_hash: str`, `project_root: Path`, `session_root: Path`, `default_agent: str`, `default_timeout_s: int`, `max_retries: int`, `compiled_by: WatermasterId`, `compiled_at: datetime` (UTC tz-aware), `source_mtime_max: datetime`, `state: Literal["draft", "dispatched", "superseded"]`, `supersedes: prior_plan_id | None`
- compute `id` from `(compiled_from, units, sop_set_hash, project_root, session_root, default_agent, default_timeout_s, max_retries, supersedes)`; these are the Plan inputs that change dispatch behavior or revision lineage
- preserve the verbatim `source_utterance` of every constituent Intent on the Plan, per `intent-compilation.md`
- treat a Plan as frozen-pinned once `state == "dispatched"`: `id`, `compiled_from`, `units`, `sop_set_hash`, `project_root`, `session_root`, `default_agent`, `default_timeout_s`, `max_retries`, `compiled_at`, and `supersedes` are immutable thereafter
- supersede a dispatched Plan via a new Plan whose top-level `supersedes: prior_plan_id` is set; the prior Plan's `state` transitions to `superseded` and is otherwise unchanged
- compute `sop_set_hash` from the worker-SOP bundle as it stands at compile time; the hash is part of the Plan's identity, not metadata
- validate every Plan before dispatch: slug format `^[a-z0-9-]+$`, no two units writing the same path, DAG acyclicity, unreachability detection from any root, prompt-text path validation
- record every dispatched Plan as the typed action of a `CompilationRecord` per `intent-compilation.md`; the Plan's `compiled_by` and `compiled_at` align with the CompilationRecord's
- distinguish the **worker-SOP bundle** (referenced by `sop_set_hash`, governs dispatched workers, distributary-internal) from the **lab SOPs** under `watershed/sops/` (govern the Watermaster, subject to `watermaster-preflight.md`); a Plan references the worker-SOP bundle by hash and does not import lab SOPs

## Do Not

- mutate a dispatched Plan in place; every revision is a new Plan with a new `id`
- include code in a Plan; Plans are pure data per CANON Article V
- conflate the worker-SOP bundle with watershed's lab SOPs; the two layers do not substitute for each other and cannot be unified by hash equivalence
- omit `sop_set_hash` from a Plan's identity; absence makes the Plan unrepresentable across worker-SOP changes
- omit `compiled_by`; anonymous Plans break the lineage of "who decided this" per `intent-compilation.md`
- dispatch a Plan whose pre-dispatch validation has not passed
- treat any change to a dispatched Plan as a "minor revision" — every change produces a new Plan with a new `id` and a `supersedes` link
- carry Plan supersession inside `compiled_from`; Intent provenance and Plan revision lineage are distinct contracts
- omit behavior-affecting dispatch fields from Plan identity
- bypass the plan-registry by dispatching directly through a worker subprocess; dispatch is mediated by distributary
- write or modify worker-SOP bundle contents from the Watermaster role; the bundle is a distributary-module artifact subject to its own conventions

## Verify

- every dispatched Plan has a stable content-derived `id`; re-compile of the same Intents, units, worker-SOP bundle, roots, defaults, retry budget, and supersession link yields a Plan with the same `id`
- every Plan carries a `sop_set_hash` matching the worker-SOP bundle as it stood at compile time; the hash is recoverable from the registered bundle
- a Plan's lifecycle is observable as `draft → dispatched → (optionally) superseded`; no other transitions occur
- a superseding Plan's top-level `supersedes` references a prior Plan id; the prior Plan's `state` is `superseded` and its other fields are unchanged
- a query for "all Plans referencing a given lab-SOP version" returns nothing (lab SOPs are not Plan-identity input); a query for "all Plans referencing a given worker-SOP-bundle hash" returns the expected set
- a Plan's `compiled_by` traces to a known Watermaster lineage entry per `intent-compilation.md`
- pre-dispatch validation rejects, with a typed error, any Plan that fails slug format, file overlap, DAG cycle, or unreachability checks

## Escalate

- if a Plan's units cannot be expressed as either `Mapping[slug, PlanUnit]` or a `DagDefinition` without distortion — a third Plan-units shape is needed, propose via preflight
- if `sop_set_hash` cannot be computed deterministically (machine-specific paths, mtime sensitivity, environment leakage) — fix the bundle's reproducibility, not the SOP
- if a Plan identity input proves machine-specific or unstable without changing dispatch behavior — remove it from identity by preflight rather than tolerating noisy ids
- if a class of Plan needs to dispatch without a `compiled_from` Intent (e.g., system-initiated cleanup) — argue first that an internal-Intent shape suffices rather than introducing untraceable Plans
- if dgov's existing in-flight Plans require migration to watershed's registry under invariants different from this SOP — frozen-pin them at their dgov state and mint new lab Plans for going-forward work
- if a worker subprocess needs to read a lab SOP at runtime — that is a layering violation; resolve by lifting the worker-relevant content into the worker-SOP bundle, not by allowing cross-layer reads
- if the Plan's `state` enum needs a fourth member (e.g., `aborted`, `expired`) — propose via preflight; the three-state lifecycle is canonical until then
