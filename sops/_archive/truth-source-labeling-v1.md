---
name: truth-source-labeling
title: Truth Source Labeling
summary: Every comparable output is tagged by truth source. Backend-native, reference-synthesized, and diagnostic-only are the classes. Evaluation requires the tags.
applies_to: [evaluation, comparison, eval, benchmark, backend, reference, truth, label, claim]
priority: must
version: 1
authored_by: Watermaster Reach
inscribed: 2026-05-06
canon_anchor: Article XIV
---

## When

- producing an output that will be compared against a reference
- writing or modifying an evaluation harness
- writing or modifying a backend that participates in a comparison
- registering a new comparable quantity in a benchmark
- producing diagnostic output that may be misread as authoritative

## Do

- tag every comparable output with one of three truth sources: `backend_native`, `reference_synthesized`, `diagnostic_only`
- attach the tag to the typed output as a structured field, not a comment or sidecar string
- use `backend_native` when the value comes from the backend's own computation
- use `reference_synthesized` when the value was produced by a reference oracle for comparison
- use `diagnostic_only` when the value supports debugging or auxiliary inspection but does not bear evaluation weight
- include the tag in any persisted record (registry, lineage, run output)
- include the tag in any prose claim of "passes eval" or equivalent
- when comparing two backends, verify their tag distributions match before declaring parity

## Do Not

- accept untagged comparable outputs at the evaluation boundary
- use `backend_native` as a default when truth source is unknown; use `diagnostic_only` and escalate
- silently promote a `diagnostic_only` value to evaluation weight
- compare a `backend_native` value to a `reference_synthesized` value as if both bore the same evidentiary status
- shim a value from one truth class to another via a translation layer; the original tag travels with the value
- write evaluation reports that do not surface the tags

## Verify

- every output participating in a comparison carries one of the three tags
- the evaluation harness fails closed when an untagged comparable output reaches the comparison boundary
- evaluation reports surface the tag for every claim
- a backend's `truth_source_by_field` mapping covers every comparable output it produces

## Escalate

- if a comparable output legitimately fits none of the three classes
- if a reference oracle's `reference_synthesized` outputs need to be promoted to `backend_native` after a backend ships
- if two backends produce comparable outputs with incompatible tag distributions and parity claims persist
- if the evaluation harness lacks a place to attach the tag without restructuring
