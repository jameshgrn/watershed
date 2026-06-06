---
name: engineer-brief
title: Engineer Brief
summary: The discipline a typed Engineer Brief carries — verbatim utterance preservation, recipient-model identity, self-contained instructions, frozen-pin after transmission, explicit write scope, authoring identity, lineage protection, and the audit-trail for external-agent consultations.
applies_to: [engineer, brief, consultation, watermaster, external, audit, compilation, three_party_loop, return_integration, write_scope]
priority: must
version: 2
authored_by: Watermaster Riffle
inscribed: 2026-05-07
canon_anchor: Articles VI, IX, XII, XIII, XVI
---

## When

- compiling a Source utterance or Watermaster thinking into an Engineer Brief for an external-agent consultation
- selecting an Engineer model (which external intelligence) to receive a Brief
- transmitting a Brief to an Engineer through the current Source-as-carrier loop
- receiving and integrating an Engineer's return into the lab
- proposing a revision Brief after a faulty return, a wrong recipient, or missing context
- recording an Engineer consultation in the audit trail

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

## Escalate

- if a Source utterance compiles to both an Intent (typed module action) and an Engineer Brief (outside consultation) — decompose into two separate compilations of distinct types
- if an Engineer return contradicts a CANON article or a live SOP — name the contradiction openly per Article XII; the Engineer's outside view is most valuable when it surfaces contradictions the chain missed
- if an Engineer return contains freelance vocabulary outside the lab's metaphor — reject or revise via a follow-up Brief
- if a Brief class recurs structurally — propose a Brief-template via preflight
- if Cowork or another harness gains direct cross-model Engineer invocation — revise this SOP via preflight; the Source-as-carrier three-party loop is a current affordance, not a discipline principle
- if the persistence home for Briefs and EngineerReturns is needed before dgov's ledger has migrated — record both at a per-session interim store under `sketches/briefs/{NN-watermaster}/`, with Brief files named `brief-{N}-{kebab-slug}.md` and EngineerReturn files named `return-{N}.md`, until the ledger is canonical (interim home, not permanent)
- if an Engineer model's identity changes mid-consultation — frozen-pin the existing records and supersede with a new Brief
- if a Brief needs to grant write access to `sketches/lineage/*` — escalate; lineage is the Watermaster's domain, not the Engineer's; no preflight overrides this
- if Engineer-written files repeatedly land out of `write_scope` — the Brief's scope is underspecified or the Engineer is misreading; tighten the Brief, do not normalize scope creep
