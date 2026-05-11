---
name: intent-compilation
title: Intent Compilation
summary: How the Watermaster translates the Source's natural-language request into typed lab actions. Defines the typed Intent, the per-module intents catalog, the compilation discipline, and the audit record that ties an utterance to the action(s) taken.
applies_to: [intent, compilation, dispatch, watermaster, source, utterance, audit, catalog, mediation]
priority: must
version: 1
authored_by: Watermaster Thalweg
inscribed: 2026-05-07
canon_anchor: Articles IV, VI, IX, XIII
---

## When

- compiling a Source utterance into one or more typed actions
- dispatching an action against a module's intents catalog
- adding a new intent to a module
- recording the compilation that produced an action
- escalating an utterance that does not map cleanly to a registered intent
- revising an action whose original compilation was wrong

## Do

- represent every compiled request as a typed `Intent` carrying: `domain` (the module), `verb` (the module-registered intent name), `payload` (a typed handle or URI; `None` for status queries), `params` (a typed mapping per the intent's signature), `source_utterance` (the original natural-language request, verbatim), `compiled_at` (UTC tz-aware), `compiled_by` (Watermaster id from the lineage chain)
- require every module to register its intents in a typed catalog: `module.intents -> Mapping[verb, IntentSpec]`, where `IntentSpec` declares the expected payload type and param schema
- restrict dispatch to (domain, verb) pairs present in the catalog; an utterance that maps to no registered intent is not an Intent — escalate or ask the Source
- when an utterance is ambiguous between two or more plausible Intents, ask the Source for disambiguation before dispatching
- when an utterance is missing a required param, ask the Source for the missing param before dispatching
- decompose a multi-step utterance into a sequence of Intents, executed and recorded individually; do not collapse multi-module work into a single catalog call
- record every dispatched Intent as a typed `CompilationRecord` carrying the Intent, the typed action dispatched, the typed result, and the Watermaster's compilation notes
- when revising an earlier Intent (e.g., the Watermaster's initial compilation was wrong), produce a new Intent whose record carries a `supersedes: intent_id` link to the prior; the prior record is frozen-pinned and not mutated
- preserve the verbatim `source_utterance` exactly as the Source wrote it; never substitute a paraphrase

## Do Not

- dispatch an action that does not correspond to a registered intent
- silently fill in missing params with defaults; ask the Source
- silently disambiguate between competing plausible interpretations; ask the Source
- mutate a CompilationRecord after dispatch — superseding records reference, they do not overwrite
- omit the verbatim `source_utterance` from the Intent — even if redundant, it is the only ground truth for the request
- compose an Intent that crosses module domains; a single Intent has exactly one `domain`
- bypass the catalog by calling a module's surface directly without producing an Intent; the catalog is the authoritative interface for Watermaster-mediated calls
- omit `compiled_by` — anonymous compilations break the lineage of "who decided this"

## Verify

- every dispatched action has a corresponding CompilationRecord
- every CompilationRecord references an Intent whose (domain, verb) is present in that module's intents catalog
- every Intent's `source_utterance` is non-empty and verbatim from the Source
- a future Watermaster reading the audit log can reconstruct what the Source asked, how it was compiled, and what was done
- `compiled_by` traces to a known Watermaster lineage entry
- multi-step utterances appear in the log as a sequence of Intents with consistent ordering
- a superseding revision references its prior via `supersedes`; both records are present in the log

## Escalate

- if an utterance has no plausible match in any module's intents catalog — the lab may need new intent registration or a new module surface; do not freelance an action
- if disambiguation between intents requires inspecting state across multiple modules to decide — defer to the Source rather than introducing cross-module heuristics
- if a class of utterance recurs and the catalog cannot represent it without distortion — propose a new intent shape via preflight rather than stretching an existing one
- if the persistence home for CompilationRecords is needed before dgov's ledger has migrated — record records to a per-session interim store under `sketches/intents/{NN-watermaster}/` until the ledger is canonical (interim home, not permanent)
- if a revision pattern emerges where the Watermaster's first compilation is consistently wrong for a class of utterance — that is a signal the catalog or this SOP needs revision, not that the Watermaster needs more discipline
