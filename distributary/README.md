# distributary/

**Agent dispatch.** Where work fans out into branches.

## Provenance

Half of `dgov/` — the fan-out half. Dispatch, plan trees, worktrees, governor.

## What it owns

- **Plan trees** — directed task graphs the governor compiles and runs
- **Dispatch** — assigning tasks to agents, creating worktrees, kicking off runs
- **Governor** — planning policy, retry policy, done-criteria
- **SOPs** — standard operating procedures bound to plan tasks

## Public types it exposes (planned)

- `Plan` — a directed task tree
- `Task` — a unit of work bound to an SOP
- `Run` — an execution of a task in a worktree
- `Governor` — the policy attached to a Plan

## Why "distributary"

In a river system, a distributary is where a single channel splits into many branches that fan out toward the sea — the canonical example is a delta. In agentic terms, that's exactly what dispatch does: takes one task and fans it out into many parallel branches (worktrees, PRs, agent invocations).

The metaphor goes the right way: distributary is *outflow*. Work leaves here.

## Pair

`tributary/` is the matched fan-in. Distributary fans work out; tributary brings typed outputs back and merges. Together they replace dgov.

## Status

Placeholder. Awaiting migration from `~/projects/dgov/` (fan-out half of the split).
