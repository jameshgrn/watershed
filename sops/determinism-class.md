---
name: determinism-class
title: Determinism Class
summary: Every flume Operator declares its determinism class as deterministic, stable, or stochastic. The class governs reproducibility expectations, pressure-test comparison, baseline drift detection, and registry deduplication.
applies_to: [operator, flume, determinism, reproducibility, pressure_test, baseline, drift, semantic_equality, seed]
priority: must
version: 1
authored_by: Watermaster Thalweg
inscribed: 2026-05-07
canon_anchor: Articles II, IV, XIV
---

## When

- writing a new Operator in flume
- evolving an existing Operator's behavior in a way that may change its determinism characteristics
- writing or modifying a pressure test for an Operator
- declaring a baseline against which drift will be measured
- writing or modifying a `MigrateOperator` per `schema-versioning.md`
- adding registry-level deduplication for OperatorRun outputs

## Do

- declare every Operator's `determinism_class: Literal["deterministic", "stable", "stochastic"]` as a typed first-class attribute on the Operator class
- use `deterministic` when same inputs + same params + same Operator code produce byte-identical output across every executor, every run
- use `stable` when same inputs + same params produce semantically equivalent output (per a declared `semantic_equality` predicate) but bytes may differ across executors or runs (parallel float-ordering, embedded timestamps in output headers, non-deterministic intermediate data structures)
- use `stochastic` when output depends on a seed; declare `seed_param: str` naming which param carries the seed; with the seed pinned, output is reproducible
- for `stable` Operators, declare `semantic_equality(a: Artifact, b: Artifact) -> bool`; without it, the Operator cannot be classed stable
- for `stochastic` Operators, the seed must be a param of the OperatorRun, not an environment read or a global default
- record the determinism class in every `OperatorRun` record alongside operator_name, inputs, params; the class travels with the run
- compose determinism class with truth-source per `truth-source-labeling.md`: `(determinism_class, truth_source)` is the full reproducibility tag for a comparable output

## Do Not

- omit the `determinism_class` declaration on a new Operator; absence is not a default
- class an Operator `deterministic` when it relies on parallel non-associative reductions, system time, environment variables, file-system iteration order, or unseeded randomness
- class an Operator `stable` without declaring `semantic_equality`
- class an Operator `stochastic` and read its seed from anywhere other than its params
- declare the same Operator under multiple classes; the classes are mutually exclusive
- compare two OperatorRun outputs for parity without consulting both runs' determinism classes — a deterministic-vs-stable comparison requires `semantic_equality`, not byte equality
- promote a `stable` Operator to `deterministic` by post-hoc canonicalization of bytes; if the Operator's natural output is stable, its class is stable

## Verify

- every Operator in flume's registry has a non-empty `determinism_class`
- a `deterministic` Operator passes a byte-identity pressure test across two runs with same inputs + same params on different executors
- a `stable` Operator passes its declared `semantic_equality` pressure test across the same conditions
- a `stochastic` Operator with the same seed passes byte-identity (or semantic equality, depending on the underlying determinism it inherits when seeded) across executors
- a `stochastic` Operator without seed pinning produces different output across runs — a positive failure check that the class is honest about its non-determinism
- baseline drift comparison consults the determinism class and uses the appropriate equality predicate
- `OperatorRun` records preserve the determinism class of the Operator that produced them

## Escalate

- if an Operator legitimately straddles classes (e.g., float-deterministic on one architecture but float-stable across architectures) — declare the weaker class and document the architecture-specific stronger guarantee in operator notes
- if an Operator's stochastic seed needs to come from a non-param source (rare; usually fixable by elevating the source to a param)
- if a fourth class is needed (e.g., bounded-error / approximate) — argue first that `stable` with an ε-tolerant `semantic_equality` doesn't suffice
- if the determinism class must change between Operator versions — treat as a breaking change to the Operator's contract; pressure-tests pinned to the prior class need re-baselining
