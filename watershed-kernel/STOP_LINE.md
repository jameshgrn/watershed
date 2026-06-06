# Kernel Stop Line

The kernel is finished enough when it makes illegal motion impossible and legal
motion obvious for the dispatcher ceremony. It is not finished by becoming a
runner, service, CLI, database, pane manager, or policy engine.

## End State

The kernel owns:

- shared contracts for recovered intent, file claims, policy, pressure tests,
  and generated schemas;
- typed outbound motion from `Plan<Drafted>` through `Plan<Validated>`;
- typed worker run motion from `Run<Pending>` through `Run<Completed>` or
  `Run<Failed>`, including completed-run deposits and lawful retry;
- a pure DAG event kernel for dependency-gated dispatch, pane-bound task motion,
  typed wait/review/merge outcomes, serial merge, and failure cascade;
- inbound settlement states for validation, merge, and baseline anchoring; and
- compile-fail and runtime tests for the laws above.

## Outside The Kernel

These belong above the kernel:

- real worker execution;
- subprocess management;
- git worktree creation or cleanup;
- pane lifecycle management;
- persistent registries or queues;
- CLI or UI surfaces;
- policy language design;
- scheduler services;
- network APIs; and
- project-specific workflow decisions.

The kernel may emit typed actions that an outer layer performs. It should not
perform those effects itself.

## Future Change Gate

Do not add a type, field, transition, constructor, dependency, or public surface
unless all of these are true:

1. A concrete illegal motion is currently expressible, or a concrete legal motion
   required by an outer layer is impossible.
2. The new model object is created or proved by a legal motion.
3. A later legal motion consumes or depends on it.
4. A compile-fail or focused integration test demonstrates the law.

If a proposed change only makes orchestration more convenient, it belongs above
the kernel. If it only records information that no kernel transition consumes,
it belongs above the kernel. If it adds a second way to express the same state,
it should be rejected or the older state should be replaced.

## Maintenance Bias

Prefer tightening existing boundaries over adding new concepts. Prefer deleting
dead states and ambiguous field bags over extending them. Prefer docs and tests
when the law already exists in code.
