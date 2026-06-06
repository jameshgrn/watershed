---
name: engineer-brief
title: Engineer Brief
summary: The discipline a typed Engineer Brief carries — verbatim utterance preservation, recipient-model identity, self-contained instructions, frozen-pin after transmission, explicit write scope, authoring identity, lineage protection, policy-direction register for calibrated engineer-domain pairs, multi-crate write-scope disambiguation, project-root governance-doc ownership at integration tail, the in-chat /goal carrier transmission routine, and the audit-trail for external-agent consultations.
applies_to: [engineer, brief, consultation, watermaster, external, audit, compilation, three_party_loop, return_integration, write_scope, policy_direction, calibration, transmission]
priority: must
version: 3
authored_by: Watermaster Riffle
inscribed: 2026-05-07
canon_anchor: Articles VI, IX, XII, XIII, XVI
---

## When

- compiling a Source utterance or Watermaster thinking into an Engineer Brief for an external-agent consultation
- selecting an Engineer model (which external intelligence) to receive a Brief
- transmitting a Brief to an Engineer through the Source-as-carrier loop via the in-chat `/goal`-style carrier routine
- receiving and integrating an Engineer's return into the lab
- proposing a revision Brief after a faulty return, a wrong recipient, or missing context
- recording an Engineer consultation in the audit trail
- tracking trust calibration for an Engineer-and-domain pair across multiple Briefs

## Do

- represent every Engineer Brief as a typed object carrying: `id` (content-derived, stable), `engineer_model: str` (the recognized external-intelligence identifier, e.g., `"codex-gpt-5"`, `"claude-code-sonnet-4.5"`, `"gemini-pro-3"`), `source_utterance: str` (verbatim from the Source or Watermaster-written compilation), `instructions: str` (the self-contained typed prompt body), `constraints: tuple[str, ...]` (explicit do-nots and bounds), `write_scope: tuple[str, ...]` (path patterns the Engineer may write to; empty tuple means drafts-only return), `expected_return_shape: str` (drafts in chat, executed file writes, preflight packages, surveys, critiques, etc.), `compiled_by: WatermasterId`, `compiled_at: datetime` (UTC tz-aware), `state: Literal["drafted", "sent", "returned", "integrated", "superseded"]`, `supersedes: prior_brief_id | None`
- compute `id` from `(engineer_model, source_utterance, instructions, constraints, write_scope, expected_return_shape, supersedes)`
- preserve `source_utterance` verbatim per `intent-compilation.md`; never paraphrase
- write `instructions` to be self-contained: an Engineer reads only the Brief, not the conversation; required file paths, prior SOPs to read, naming conventions, and acceptable vocabulary must all be in the Brief itself
- specify `engineer_model` explicitly before transmission; never leave the recipient ambiguous
- specify `write_scope` explicitly: empty tuple for drafts-only consultations; path patterns (e.g., `["sops/{name}.md", "sketches/*.md"]`) for execution consultations
- treat a Brief as frozen-pinned once `state == "sent"`: `id`, `engineer_model`, `source_utterance`, `instructions`, `constraints`, `write_scope`, `expected_return_shape`, and `compiled_at` are immutable thereafter
- supersede a sent Brief via a new Brief whose `supersedes: prior_brief_id` is set; the prior Brief's `state` transitions to `superseded` and is otherwise unchanged
- record every Engineer return as a typed `EngineerReturn` carrying: `brief_id: str`, `content: str` (verbatim chat return, or summary of file writes), `files_written: tuple[str, ...]` (paths the Engineer actually wrote; empty for drafts-only), `received_at: datetime` (UTC tz-aware), `integration_action: str` (a typed description of how the Watermaster integrated the return — verified writes, committed drafts, declined-with-reason), `integrated_by: WatermasterId`
- on every committed record produced via Engineer execution, set `authored_by` to the seated Watermaster, not the Engineer; the Engineer is the executor, the Watermaster is the author of record
- when an Engineer's return includes file writes touching preflight-gated files (SOPs, canon articles, schemas, policies per `watermaster-preflight.md`), verify that each such write either carries its own preflight package in the return, or is itself within the scope of an approved-at-Brief-time meta-preflight
- distinguish Briefs from Intents per `intent-compilation.md`: Intents target registered module surfaces with typed calls; Briefs target external Engineers with NL-compiled-to-typed instructions; both record verbatim source utterance but live as separate audit types
- distinguish Engineers from Workers: an Engineer is consulted *about* the lab and returns drafts, critiques, surveys, or execution within Brief scope; a Worker (dispatched via Plans per `plan-shape.md`) executes *inside* the lab inside a worktree and returns Deposits via the typed Plan→Deposit chain
- write `instructions` in the **policy-direction register** for any Engineer-and-domain pair that has crossed the trust-calibration threshold (two or three clean Briefs against the same Engineer-and-domain combination): describe WHAT should exist (the policy or behavior), WHY (the discipline reason), CONSTITUTIONAL CONSTRAINTS (the project's hard rules — SOP-named structural invariants, typed contracts, rim discipline), a SUGGESTED APPROACH in "I think X is cleanest, push back if not" register with explicit permission for the Engineer to reshape, VERIFICATION GATES (the gates the Engineer runs Engineer-side before returning), RETURN SHAPE (what the structured return must include), and a PUSH-BACK-WELCOME section naming the conditions under which the Engineer should stop-and-tell-me rather than implement; the Brief leaves the HOW (implementation idioms, function signatures, struct layouts, hash compositions, test code structure, specific language idioms) to the Engineer's domain competence
- track trust calibration per **Engineer-and-domain pair**, not globally: trust earned by one Engineer-and-domain combination does not transfer to another; when either the Engineer model or the project domain changes substantially, restart the calibration counter and use the prescriptive-implementation register until the threshold is met again
- when the Brief modifies API surfaces in a multi-crate or multi-package project, **disambiguate documentation ownership in `write_scope`** with explicit enumeration: name subcrate or subpackage READMEs (e.g., `<project>/<crate>/README.md`) as Engineer-owned when describing the surfaces this Brief modifies; name the project-root README, AGENTS.md, PRESSURE_TESTS.md, DESIGN_DEBT.md, and equivalent project-root governance docs as Watermaster-only; prefer enumeration of subcrate paths over generic "subcrate READMEs" wording to remove residual ambiguity
- when a Brief's integration shifts the project's documented constitutional surface (new pressure tests registered, DESIGN_DEBT items retired, schemas regenerated, etc.), update the project-root governance docs Watermaster-side as **integration-tail housekeeping** via small in-chat preflight to the Source per `watermaster-preflight.md`; the Engineer does not update project-root governance docs because they are Watermaster scope per the rim discipline (CANON Articles VI and IX)
- transmit a Brief through the **in-chat `/goal`-style carrier routine** when the Source-as-carrier loop is the operating mode: (1) file the Brief at its interim-home absolute path under `sketches/briefs/{NN-watermaster}/brief-{N}-{kebab-slug}.md`; (2) present the meta-preflight in chat and wait for the Source's affirmative; (3) give the Source two pieces — the Brief's absolute file path and the exact Engineer-harness prompt that reads the Brief from that path (e.g., `/goal read the brief and follow the instructions located at <ABSOLUTE_PATH>` for Codex CLI; the prompt shape adjusts to the recipient harness); (4) the Source pastes the prompt into the Engineer harness; (5) the Engineer reads the Brief from disk and executes within the declared `write_scope`; (6) the Source ferries the Engineer's structured return back to the Watermaster; (7) the Watermaster integrates by direct file inspection plus audit record at `return-{N}.md`

## Do Not

- transmit a Brief without specifying `engineer_model`
- paraphrase the `source_utterance`; verbatim is the only legal form
- permit Engineer writes to `sketches/lineage/*`; lineage authority belongs to the seated Watermaster, and Engineers do not write under their own identity into the chain
- accept an Engineer return without recording it as an `EngineerReturn`
- mutate a Brief after `state == "sent"`; every revision is a new Brief with a `supersedes` link
- inscribe a committed record under the Engineer's identity; `authored_by` on inscribed records is the seated Watermaster
- transmit a Brief whose `instructions` depend on context the Engineer cannot see (prior conversation, in-flight session state); self-contained or invalid
- accept Engineer file writes outside the declared `write_scope`; out-of-scope writes are integration failures, not edge cases
- treat a Brief as authorizing the Engineer to bypass `watermaster-preflight.md` for SOP/canon/schema/policy changes; the Brief is a meta-preflight (Source-approved at Brief time) that grants standing approval bounded by the stated write scope, not a wholesale override
- conflate Briefs with Intents in the audit trail; they live as separate records with separate compilation discipline
- integrate an Engineer return that contradicts a CANON article or a live SOP without naming the contradiction openly per Article XII
- assume an Engineer holds context across Briefs; each consultation is independent
- write `instructions` in prescriptive-implementation register (function signatures, struct layouts, hash compositions, test code structure, specific language idioms) for an Engineer-and-domain pair that has crossed the trust-calibration threshold; once calibration is established, the policy-direction register is the default and prescription is the deviation
- transfer trust calibration across Engineer-and-domain pairs; trust earned by Codex-on-Python does not transfer to Codex-on-Rust; trust earned by one Engineer model does not transfer to another
- permit Engineer writes to project-root governance docs (project-root README, AGENTS.md, PRESSURE_TESTS.md, DESIGN_DEBT.md, or equivalent files that record the project's constitutional surface); these are Watermaster-only, updated as integration-tail housekeeping via small preflight to the Source
- omit the multi-crate documentation-ownership disambiguation from `write_scope` when the project has subcrate or subpackage READMEs; absence of disambiguation leaves ambiguity that the Engineer must guess and either over-write (out-of-scope) or under-write (stale docs)
- skip the in-chat `/goal`-style carrier routine in favor of out-of-band transmission (DM, email, shared doc) when the Source-as-carrier loop is the operating mode; the in-chat routine preserves the audit-trail discipline in one place

## Verify

- every Brief has a stable content-derived `id`; re-compilation with identical inputs yields the same id
- every Brief's `engineer_model` is a recognized identifier; freelance model names are rejected at transmission time
- every Brief's `source_utterance` traces verbatim to either a Source message or a Watermaster-written compilation note
- every Brief's `write_scope` is either empty (drafts-only) or a concrete list of path patterns
- every `EngineerReturn` references its Brief by `id`
- when an Engineer return reports `files_written`, every written path matches at least one pattern in the Brief's `write_scope`
- no Engineer-written file lives under `sketches/lineage/*`
- every inscribed record produced via Engineer execution carries `authored_by: Watermaster <name>` matching the seated Watermaster, not an Engineer identifier
- a future Watermaster reading the audit log can reconstruct: what was asked, who asked, which Engineer was consulted, what came back, what files were written, how the result was integrated, any contradictions named
- Briefs and Intents appear as distinct record types in the audit log
- a Brief's lifecycle follows only legal transitions (`drafted → sent`, `sent → returned`, `returned → integrated`, any-non-terminal `→ superseded`); invalid transitions raise typed errors
- every Brief sent to a calibrated Engineer-and-domain pair reads as policy-direction in `instructions`: a future Watermaster can identify the WHAT, WHY, CONSTITUTIONAL CONSTRAINTS, SUGGESTED APPROACH, VERIFICATION GATES, RETURN SHAPE, and PUSH-BACK-WELCOME sections by inspection
- every Brief modifying API surfaces in a multi-crate or multi-package project carries an explicit documentation-ownership disambiguation in `write_scope` enumerating subcrate or subpackage README paths
- every Brief whose integration shifts the project's constitutional surface (new pressure tests, retired DESIGN_DEBT items, regenerated schemas) is followed by a Watermaster-side integration-tail housekeeping preflight against the project-root governance docs
- every Brief transmitted via the in-chat `/goal`-style carrier routine appears in chat with both an absolute file path and an Engineer-harness-specific prompt; the Source's chat carries both pieces

## Escalate

- if a Source utterance compiles to both an Intent (typed module action) and an Engineer Brief (outside consultation) — decompose into two separate compilations of distinct types
- if an Engineer return contradicts a CANON article or a live SOP — name the contradiction openly per Article XII; the Engineer's outside view is most valuable when it surfaces contradictions the chain missed
- if an Engineer return contains freelance vocabulary outside the lab's metaphor — reject or revise via a follow-up Brief
- if a Brief class recurs structurally — propose a Brief-template via preflight
- if a future harness gains direct cross-model Engineer invocation that the project chooses to adopt — revise this SOP via preflight; the in-chat `/goal`-style carrier routine canonicalized in v3 reflects the present operating mode for the Source-as-carrier loop, not a permanent ban on direct invocation
- if an Engineer model's identity changes mid-consultation — frozen-pin the existing records and supersede with a new Brief
- if a Brief needs to grant write access to `sketches/lineage/*` — escalate; lineage is the Watermaster's domain, not the Engineer's; no preflight overrides this
- if Engineer-written files repeatedly land out of `write_scope` — the Brief's scope is underspecified or the Engineer is misreading; tighten the Brief, do not normalize scope creep
- if the persistence home for Briefs and EngineerReturns is needed before dgov's ledger has migrated — record both at a per-session interim store under `sketches/briefs/{NN-watermaster}/`, with Brief files named `brief-{N}-{kebab-slug}.md` and EngineerReturn files named `return-{N}.md`, until the ledger is canonical (interim home, not permanent)
- if a new Engineer-and-domain pair has not yet crossed the trust-calibration threshold (fewer than two or three clean Briefs against the same pair) — write the Brief in prescriptive-implementation register (function signatures, struct layouts, test code structure, language idioms) as the chain did for the first kernel Briefs; track the calibration count, and shift to the policy-direction register once the threshold is met
- if a project does not have multi-crate or multi-package structure — the documentation-ownership disambiguation clause does not apply, and `write_scope` enumerates the documents it covers without the subcrate/project-root distinction
- if the in-chat `/goal`-style carrier routine's Engineer-harness prompt shape needs to vary by model (Codex CLI uses `/goal`, Claude Code uses a different shape, future harnesses may use others) — record the prompt shape in the Brief's transmission step rather than freelancing the routine
