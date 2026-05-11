---
name: baseline-shape
title: Baseline Shape
summary: The discipline a typed Baseline carries — Merge anchoring, sentrux subprocess wrapping, content hash of .sentrux/baseline.json, and frozen next-run reference.
applies_to: [baseline, sentrux, tributary, merge, gate, subprocess, pointer, content_hash, reproducibility]
priority: must
version: 1
authored_by: Watermaster Riffle
inscribed: 2026-05-07
canon_anchor: Articles II, IV, VIII, IX, XII
---

## When

- saving a known-good state after a Merge
- running sentrux baseline capture or gate from tributary
- giving distributary a next-run baseline reference
- recording a drift reference for future validation
- diagnosing mismatch between typed Baseline history and `.sentrux/baseline.json`

## Do

- represent every Baseline as a typed object carrying: `id` (content-derived, stable), `merge_id: str`, `branch: str`, `name: str`, `sentrux_ref: Pointer`, `sentrux_content_hash: str`, `sentrux_version: str`, `gate_result: GateResult`, `captured_at: datetime` (UTC tz-aware), `captured_by: WatermasterId`
- create a Baseline only through `tributary.baseline.save(merge_id, branch, name)` after a Merge exists
- require `merge_id` to resolve to a Merge whose `merged_commit` is the branch head at capture time
- run sentrux only as a subprocess; capture the command, version, exit status, and gate result through tributary's typed boundary
- canonicalize the `.sentrux/baseline.json` location into `sentrux_ref: Pointer` before writing the Baseline record
- compute `sentrux_content_hash` from the exact bytes of `.sentrux/baseline.json` after sentrux writes it
- compute `id` from `(merge_id, sentrux_ref, sentrux_content_hash, sentrux_version)`; the same Merge and same sentrux baseline bytes under the same sentrux version yield the same Baseline id
- treat Baseline as a wrapper and pointer to sentrux's native baseline file; sentrux owns `.sentrux/baseline.json`
- treat a Baseline as frozen-pinned at record time: `id`, `merge_id`, `sentrux_ref`, `sentrux_content_hash`, `sentrux_version`, and `gate_result` are immutable thereafter
- expose Baseline to distributary by `baseline_id`, never by branch name or file path

## Do Not

- import sentrux as a Python library
- mirror the full `.sentrux/baseline.json` payload into watershed-owned schema fields
- create a Baseline from branch name alone
- create a Baseline before the Merge it anchors to exists
- mutate a Baseline when sentrux rewrites `.sentrux/baseline.json`; mint a new Baseline record
- treat Merge as automatically baseline-producing
- use a raw filesystem path as Baseline identity
- accept a sentrux subprocess failure as a Baseline with warning notes

## Verify

- `merge_id` resolves to an existing Merge before sentrux runs
- the branch head at capture time equals `Merge.merged_commit`
- the sentrux subprocess exits successfully and produces `.sentrux/baseline.json`
- `sentrux_ref` is canonicalized per `pointer-canonicalization.md`
- `sentrux_content_hash` matches the bytes at `sentrux_ref`
- the Baseline id is stable under repeat construction from the same Merge, sentrux pointer, content hash, and sentrux version
- distributary can retrieve the Baseline by `baseline_id` and recover the anchoring Merge

## Escalate

- if sentrux changes `.sentrux/baseline.json` format or omits a recoverable version
- if the branch head no longer matches `Merge.merged_commit` at capture time
- if sentrux must be imported to obtain required state; preserve the subprocess boundary and propose a typed adapter instead
- if multiple Baselines for one Merge become routine; define the policy before the registry accumulates ambiguous anchors
- if Baseline needs to carry more than pointer, content hash, version, and gate summary; argue why the field belongs in watershed rather than in sentrux's native file
