# rivulet/

**Side-channel inference for Watermaster thinking.** Small, bounded model calls
for research, critique, summarization, and review of plans or reasoning.

## What It Is

A rivulet is a temporary side flow. It helps the Watermaster think without
becoming the source of authority.

Use it for:

- governor-level research before compiling an Intent, Plan, or Brief
- critique of Watermaster reasoning, plan shape, or tradeoffs
- read-only review of a draft Brief, Plan, SOP proposal, or architecture sketch
- literature or codebase summarization where the output is advisory evidence
- cheap provider experiments that should not leak into canonical module law

## What It Is Not

- not the Rust kernel
- not a Worker
- not an Engineer Brief by default
- not a DispatchRun
- not a Deposit
- not a path for direct file edits
- not a way around Watermaster mediation

If a rivulet finds work to do, the Watermaster compiles that into the proper
surface: an Intent, Engineer Brief, Plan, or no action.

## Future Surface

Keep the first implementation narrow:

```text
rivulet.submit(request) -> RivuletJob
rivulet.status(job_id) -> RivuletJob
rivulet.result(job_id) -> RivuletReturn
rivulet.cancel(job_id) -> RivuletJob
```

Convenience commands can sit in `tools/`:

```text
lab rivulet research
lab rivulet review-plan
lab rivulet review-thinking
lab rivulet critique-brief
lab rivulet summarize
```

## Record Sketch

Do not promote this into `shared/` until another module consumes it.

```text
RivuletJob
  id
  role: research | review | critique | summarize
  provider_ref
  model
  state: queued | running | completed | failed | cancelled
  prompt_ref
  context_refs
  result_ref
  created_by: WatermasterId
  created_at
  started_at
  finished_at
  prompt_tokens
  completion_tokens
  cost
```

```text
RivuletReturn
  job_id
  summary
  findings
  citations_or_file_refs
  uncertainty
  recommended_next_surface: intent | brief | plan | none
```

## Boundary Rules

- Rivulets are read-only unless a future preflight explicitly changes this.
- Results are advisory until the Watermaster converts them into a typed action.
- Provider selection, model routing, API keys, retries, queues, and cost tracking
  belong here or in the rim tooling, never in `watershed-kernel/`.
- If output becomes canonical lab data, materialize it through the appropriate
  typed boundary instead of treating raw model text as truth.
- A write-capable coding run belongs under distributary dispatch, not rivulet.

## Status

Scaffold only. This directory exists so the cheap-inference successor to the
FirePass researcher/reviewer pattern has a watershed-native home when the rim
layer is ready.
