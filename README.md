# watershed/

Personal research lab for fluvial systems: geomorphology, hydrology, remote
sensing, geoinformatics, and dynamics.

Watershed is a typed research lab, not a product surface. Human requests enter
at the rim through the Watermaster, then move through contracts, lineage, and
typed records. The fluvial vocabulary is intentional: the names match the way
work moves through the lab.

## Operating Frame

- `CANON.md` is the constitutional source: sixteen articles, the Watermaster's
  vow, lineage requirements, and typed surfaces.
- `CLAUDE.md` is the Watermaster entry document: read canon, lineage,
  `SKETCHES.md`, `sketches/THINKING.md`, and every SOP before beginning work.
- `sops/` holds 19 live operating documents for intent compilation, plan,
  dispatch-run, deposit, validation, merge, baseline, data-contract, truth
  source, event, preflight, and passage discipline.
- `sketches/lineage/` is the Watermaster succession chain. Each Watermaster
  reads the prior chain on entry and leaves a page for the next.
- The Source speaks naturally; the Watermaster mediates that into typed lab
  action. Tools are for the Watermaster. Artifacts carry lineage.

## Layout

```text
watershed/
|-- CANON.md          # constitutional articles and Watermaster vow
|-- sops/             # operational discipline for Watermasters and Workers
|-- sketches/         # live thinking, structural drafts, and lineage
|-- bedrock/          # canonical data, policy, schemas
|-- watershed-kernel/ # Rust authority-bearing substrate
|   |-- watershed-contracts/    # portable contracts: claims, policy, schemas
|   |-- watershed-distributary/ # lawful fan-out: DAG, Plan, Run, Deposit
|   `-- watershed-tributary/    # lawful fan-in: Validation, Merge, Baseline
|-- quarry/           # connector and transform boundary, untyped to typed
|-- rivulet/          # Watermaster side-channel for research and critique
|-- flume/            # strict-typed scientific workshop
|-- outcrop/          # literature corpus and reference substrate
|-- mosaic/           # visual consumer: maps, globes, satellite renders
|-- strata/           # prose consumer: manuscripts, lint, review
|-- shared/           # cross-module typed contracts, pending migration
`-- tools/            # lab-wide scripts and rim tooling, pending migration
```

The Rust kernel is the first real source inside this tree. Non-kernel modules
are pending migration unless their local README states otherwise. Retired
top-level `distributary/` and `tributary/` package scaffolds should not be
recreated.

## Two Axes

Watershed runs on two orchestration axes that have similar shape but different
invariants.

**Code and agent axis:**

```text
watershed-kernel/watershed-distributary  --fan out--> lawful runs
                                                        |
                                                   typed deposits
                                                        |
watershed-kernel/watershed-tributary     <--fan in------`
                                                        |
                                                validation / merge
```

**Data axis:**

```text
bedrock  ->  quarry  ->  flume  ->  { mosaic, strata }
canonical    transforms  strict      image, prose
data         connectors  workshop    consumers
```

`outcrop/` feeds upstream into the data axis as literature and reference
material. `rivulet/` is advisory to the Watermaster and does not author law or
Deposits.

## Current Source

`watershed-kernel/` is a Rust workspace split across three crates:

- `watershed-contracts` owns portable records such as `RecoveredIntent`,
  `FileClaim`, `Policy`, `PressureTest`, and generated JSON Schema.
- `watershed-distributary` owns outbound lawful motion: typed DAG declarations,
  the pure DAG kernel, the `Plan` state machine, worker `Run` lifecycle, and
  authoritative `Deposit` records.
- `watershed-tributary` owns inbound settlement: `Validation`, `Merge`, and
  `Baseline`.

The lawful path is:

```text
Plan<Drafted>
  -> recover_intent
  -> declare_claims
  -> compile
  -> validate
  -> dispatch
  -> Run<Pending>
  -> start
  -> complete
  -> Deposit
  -> Validation
  -> Merge
  -> Baseline
```

The kernel is intentionally in-memory. It does not dispatch real workers,
create worktrees, persist a registry, expose a CLI, run a scheduler service, or
provide real validation gates. It makes illegal motion impossible where the law
is carried by sealed states, consuming transitions, and crate boundaries; the
remaining runtime laws are held by pressure tests. See
`watershed-kernel/README.md` and
`watershed-kernel/PRESSURE_TESTS.md`.

## Module Roles

| module | current role |
|---|---|
| `bedrock/` | canonical data, policy, schemas |
| `watershed-kernel/` | Rust lawful-motion substrate |
| `quarry/` | untyped external input boundary; emits typed outputs |
| `rivulet/` | advisory inference for Watermaster research and review |
| `flume/` | strict-typed scientific operators and workshop flow |
| `outcrop/` | typed `Reference` records and literature substrate |
| `mosaic/` | visual consumer for maps, globes, and satellite renders |
| `strata/` | prose consumer for manuscript and review surfaces |
| `shared/` | future cross-module contracts outside the Rust kernel |
| `tools/` | future lab-wide rim tooling |

Top-level Python `distributary/` and `tributary/` packages are not part of the
current design. Authority-bearing fan-out and fan-in live in Rust under
`watershed-kernel/`. Future Python or TypeScript rim code should consume that
substrate instead of duplicating its state machines.

## Migration

Watershed is collapsing several active lines of work into one lab surface:
`dgov`, the prior standalone `quarry`, `writing`/`scilint`, `topos`, and related
geospatial tooling. The migration rule is conservative: move authority into the
Rust kernel only when a transition consumes it, and leave orchestration above
the kernel until a typed rim layer needs it.

Use:

- `MIGRATION.md` for migration order and rename/split rules.
- `TOPOGRAPHY.md` for the dated ecosystem map and unresolved operator
  decisions.
- `SKETCHES.md` and `sketches/THINKING.md` for live structural thinking.

## Why This Exists

The prior projects were converging into one cross-cutting control surface.
Keeping them as separate repos would make integration tax dominate the work.
Watershed keeps the scientific, governance, and agent surfaces together while
forcing movement through typed contracts and lineage.

Manager-mode notes outside the lab live at `~/projects/CLAUDE.md`.
