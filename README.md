# watershed/

Personal research lab. Fluvial geomorphology + hydrology + remote sensing + dynamics.

## Layout

```
watershed/
├── bedrock/        # canonical data + policy + schemas — source of truth
├── distributary/   # agent dispatch, plan trees, worktrees   (← dgov, fan-out half)
├── tributary/      # ingest, validate, merge to main          (← dgov, fan-in half)
├── quarry/         # data orchestration: connectors, transforms, ETL boundary
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
distributary  ──fan out──▶  agents work in worktrees
                                       │
                                  typed outputs
                                       │
tributary     ◀──fan in────────────────┘
                                       │
                                merge to main
```

**Data axis (horizontal):**

```
bedrock  ──▶  quarry  ──▶  flume  ──▶  { mosaic, strata }
canonical    transforms   strict-typed   image, prose
data         + connectors  workshop      consumers
```

`outcrop/` feeds upstream into the data axis (citations into strata, references into flume). The static layers (`bedrock`, `outcrop`) bracket the dynamic work — substrate beneath, exposed knowledge above; everything in between flows.

## The narrative

The substrate doesn't move. **Bedrock** holds what's true. **Distributary** fans out agents to do work; **tributary** brings their typed outputs back and merges them. **Quarry** transforms raw data from bedrock into the strict types **flume** consumes — flume is where the actual science runs with full type discipline. **Mosaic** and **strata** present flume's outputs as image and prose. **Outcrop** is the visible exposed face of accumulated literature — feeds into strata as citations, into flume as ground truth from prior work.

## Type discipline by module

| module | type stance |
|---|---|
| bedrock | schema-defined data, policy-aligned |
| quarry | accepts untyped inputs from outside, emits typed outputs |
| flume | refuses non-canonical inputs; everything in is strict-typed |
| mosaic, strata | consume flume's typed outputs |
| outcrop | typed `Reference` records |
| distributary, tributary | typed `Run`, `Plan`, `Deposit`, `Merge` |

## Status

**Scaffolding under review.** Each module directory holds a placeholder `README.md` describing its role, provenance (which existing repo absorbs into it), public types it will own, and current status. No code migrated yet.

When ready: see `MIGRATION.md`.

## Why this exists

dgov + quarry-as-it-was + writing/scilint + topos were converging into one integrated control surface. Polyrepo integration tax was about to dominate the moonshot work in the cross-cutting layer. Monorepo with typed shared contracts collapses that tax. The names match what each module *does* — fluvial-system vocabulary because that's the shape of the science.

Manager-mode notes (Cowork-side context) live at `~/projects/CLAUDE.md`.