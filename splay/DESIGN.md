# Splay — Parallel Inference with Coherence

**Splay** is a watershed rim surface for parallel thinking. It splays one
problem across N inference angles, then coheres the raw findings into a single
synthetic report that the Watermaster consumes directly.

Splay is an homage to the distributary, not a part of it. It borrows the
parallelism of the construction layer but lives in the rim, produces no
construction artifact, and requires no kernel lifecycle.

## Design assumptions

- Tokens cost nothing and are bought at a flat rate.
- Parallelism is cheap; the cost is in the Watermaster's attention.
- The coherence step is the boundary between inference and mediation.

## What Splay is

A single-channel surface:

```
Source or Watermaster → SplayJob
                         ↓
              ┌─────────┴─────────┐
              │   N parallel        │
              │   RivuletJobs       │
              │   (one per angle)    │
              └─────────┬─────────┘
                        ↓
              ┌─────────┴─────────┐
              │  Coherence Job      │
              │  (single rivulet)  │
              └─────────┬─────────┘
                        ↓
                   SplayReturn
```

The Watermaster sees one `SplayReturn`, not N raw returns.

## What Splay is not

- Not a chain — no sequential dependency between angles
- Not the distributary — no DispatchRun, no Deposit, no Validation
- Not a Worker — no tool loop, no write capability
- Not an Engineer Brief — does not produce code or construction artifacts
- Not the kernel — rim-only, no Rust identity or lifecycle

## Records

### SplayJob

```
SplayJob
  id                    // SplayJobId
  context_refs          // files, docs, schema, lineage entries
  angles: Angle[]       // each has a name, prompt, model hint
  coherence_prompt      // optional; default is system-defined
  coherence_model       // optional; defaults to same provider as rivulet
  state: queued | splatting | cohering | completed | failed | cancelled
  created_by            // WatermasterId
  created_at
  splatted_at           // when all angle jobs finished
  cohered_at            // when coherence job finished
```

### Angle

```
Angle
  name                  // e.g. "security", "performance", "readability"
  prompt                // the specific instruction for this angle
  model_hint            // optional; overrides default for this angle
  context_overrides     // optional; additional files only for this angle
```

### AngleSummary

```
AngleSummary
  angle_name
  key_findings: string[]
  certainty: high | medium | low
  recommendation: string | null
  raw_job_id            // backreference to the underlying RivuletJob
```

### SplayReturn

```
SplayReturn
  job_id
  synthesis             // coherent summary written by the coherence job
  conflicts: CrossAngleConflict[]
  certainty: high | medium | low
  recommended_next_surface: intent | brief | plan | none
  raw_summaries: map[angle_name] -> AngleSummary  // available for inspection
```

### CrossAngleConflict

```
CrossAngleConflict
  angles: [angle_name, angle_name]
  conflict_type: contradiction | tension | omission | priority
  description
  suggested_resolution: string | null
```

## Surface operations

```
splay.submit(request) -> SplayJob
splay.status(job_id) -> SplayJob
splay.return(job_id) -> SplayReturn
splay.cancel(job_id) -> SplayJob
```

Convenience commands:

```
lab splay review --file src/dag.rs --angles "security,performance,readability"
lab splay decide --prompt "Should we merge the distributary-tributary port?"
lab splay research --topic "DuckDB spatial indexing" --angles "technical,ecosystem,comparative"
lab splay audit --sop intent-compilation --angles "completeness,clarity,authority"
```

## Coherence step

The coherence job is a single `RivuletJob` that receives:

- `AngleSummary[]` (not full raw returns — compression is the rim's job)
- The original `context_refs`
- The `coherence_prompt` (or a default)

It produces the `synthesis`, the `conflicts`, and the `certainty` assessment.

The Watermaster does not synthesize. The Watermaster reads the `SplayReturn`
and compiles it into the proper watershed surface: Intent, Engineer Brief,
Plan, or no action.

## Boundary rules

- Splay is read-only. No angle may write to the filesystem.
- If an angle needs a file edit, that finding is compiled into an Engineer
  Brief by the Watermaster, not executed by the angle.
- Provider selection, model routing, retries, and cost tracking live in the
  rim tooling, never in `watershed-kernel/`.
- A `SplayReturn` is advisory until the Watermaster acts on it.
- Raw summaries are available for inspection but are not the primary view.
  The primary view is the coherent synthesis.

## Canonical angles

A system-defined set of angles for common splay roles. Each angle is a
read-only reviewer with a specialized prompt. The `review` angle is modeled on
the FirePass reviewer system prompt (adapted for the splay surface).

| Angle | Purpose | Modeled on |
|---|---|---|
| `review` | Full code review — correctness, security, architecture, performance, style | FirePass reviewer |
| `completeness` | Audit for missing surfaces, boundaries, edge cases | watershed-native |
| `clarity` | Audit for ambiguous terms, missing examples, contradictions | watershed-native |
| `authority` | Audit for rim/kernel boundary violations | watershed-native |
| `security` | Security audit — injection, validation, secrets, race conditions | watershed-native |
| `performance` | Performance audit — complexity, memory, blocking, leaks | watershed-native |
| `readability` | Readability audit — names, docs, nesting, types | watershed-native |
| `test-coverage` | Test coverage audit — missing paths, brittle tests | watershed-native |
| `correctness` | Correctness audit — off-by-one, state machines, logic | watershed-native |
| `design` | Design audit — coupling, abstraction, patterns, APIs | watershed-native |

All angles are read-only. No angle may write to the filesystem. The Watermaster
compiles findings into action.

The Watermaster may override or extend these. Custom angles are first-class.

## Status

Implemented. The `splay/` directory contains:
- `src/models.py` — record types (`SplayJob`, `SplayReturn`, `Angle`, etc.)
- `src/orchestrator.py` — parallel dispatch, coherence, parsing
- `src/providers.py` — provider abstraction (`FireworksProvider`)
- `src/angles.py` — canonical angle definitions
- `tests/test_splay.py` — mock tests (passing)
- `tests/test_splay_live.py` — live API tests (requires `FIREWORKS_API_KEY`)

The implementation is watershed-native. It uses the Fireworks backend (same as
FirePass) but owns the orchestration, record types, and coherence step.

The splay surface is ready for use. The `lab splay` CLI is not yet built.

## Relation to other surfaces

| Surface | Layer | Produces | Parallel |
|---|---|---|---|
| **rivulet** | rim | `RivuletReturn` (advisory) | single |
| **splay** | rim | `SplayReturn` (synthesized) | parallel |
| **distributary** | kernel | `DispatchRun`, `Deposit` | parallel |
| **Engineer Brief** | kernel | construction artifacts | single (with lifecycle) |

Splay uses rivulet internally. Distributary uses workers internally. The
Watermaster is the consumer of both.
