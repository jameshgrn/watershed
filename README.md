# watershed/

Personal research lab. Fluvial geomorphology + hydrology + remote sensing + dynamics.

## Layout

```
watershed/
├── bedrock/        # canonical data + policy + schemas — source of truth
├── watershed-kernel/
│   ├── watershed-distributary/ # Rust lawful fan-out substrate
│   └── watershed-tributary/    # Rust lawful fan-in substrate
├── quarry/         # data orchestration: connectors, transforms, ETL boundary
├── rivulet/        # side-channel inference for Watermaster research/review
├── flume/          # strict-typed scientific workshop — only canonical types intake
├── outcrop/        # lit corpus — Zotero + arXiv + embeddings + cite
├── mosaic/         # viz consumer — globe, basemaps, satellite renders   (← topos)
├── strata/         # manuscript consumer — lint, bind, review            (← writing/scilint)
├── shared/         # cross-module typed contracts
└── tools/          # lab-wide CLI + scripts
```

## Two orthogonal axes

The lab runs on two orchestration axes that look the same shape but have different invariants:

**Code/agent axis (vertical):**

```
watershed-kernel/watershed-distributary  ──fan out──▶  lawful runs
                                                            │
                                                       typed deposits
                                                            │
watershed-kernel/watershed-tributary     ◀──fan in──────────┘
                                                            │
                                                     validation / merge
```

**Data axis (horizontal):**

```
bedrock  ──▶  quarry  ──▶  flume  ──▶  { mosaic, strata }
canonical    transforms   strict-typed   image, prose
data         + connectors  workshop      consumers
```

`outcrop/` feeds upstream into the data axis (citations into strata, references into flume). The static layers (`bedrock`, `outcrop`) bracket the dynamic work — substrate beneath, exposed knowledge above; everything in between flows.

## The narrative

The substrate doesn't move. **Bedrock** holds what's true. The Rust kernel's **watershed-distributary** crate fans out legal work; **watershed-tributary** brings typed deposits back through validation and merge. **Rivulet** is the Watermaster's small side-channel for cheap inference, research, and critique; it advises but does not author law or Deposits. **Quarry** transforms raw data from bedrock into the strict types **flume** consumes — flume is where the actual science runs with full type discipline. **Mosaic** and **strata** present flume's outputs as image and prose. **Outcrop** is the visible exposed face of accumulated literature — feeds into strata as citations, into flume as ground truth from prior work.

## Type discipline by module

| module | type stance |
|---|---|
| bedrock | schema-defined data, policy-aligned |
| quarry | accepts untyped inputs from outside, emits typed outputs |
| rivulet | advisory inference returns; read-only by default; no Deposits |
| flume | refuses non-canonical inputs; everything in is strict-typed |
| mosaic, strata | consume flume's typed outputs |
| outcrop | typed `Reference` records |
| watershed-kernel/watershed-distributary, watershed-kernel/watershed-tributary | typed `Plan`, `Run`, completed-run `Deposit`, `Validation`, `Merge`, `Baseline` |

## Status

**Scaffolding plus Rust kernel.** The authority-bearing fan-out/fan-in substrate lives in `watershed-kernel/` as Rust crates. The remaining module directories are placeholders until their migration begins.

Rust receives law when the law has a transition to live in: record identity, claim authority, sealed state movement, and crate-boundary construction rules. Runner orchestration, worktrees, persistence, CLI surfaces, prompts, event stores, and subprocess gates stay above the kernel until a typed rim layer needs them.

When ready: see `MIGRATION.md`.

## Why this exists

dgov + quarry-as-it-was + writing/scilint + topos were converging into one integrated control surface. Polyrepo integration tax was about to dominate the moonshot work in the cross-cutting layer. Monorepo with typed shared contracts collapses that tax. The names match what each module *does* — fluvial-system vocabulary because that's the shape of the science.

Manager-mode notes (Cowork-side context) live at `~/projects/CLAUDE.md`.
