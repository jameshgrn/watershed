# MIGRATION

How `watershed/` gets populated from existing repos.

## Rename and split map

| old | new | notes |
|---|---|---|
| `dgov/` | **`watershed-kernel/watershed-distributary/`** + **`watershed-kernel/watershed-tributary/`** for authority-bearing motion | split: Rust distributary owns legal fan-out; Rust tributary owns ingest validation, merge, and baseline authority. Any future Python/TS orchestration should wrap the kernel rather than duplicate the state machine. Do not force runner/worktree/persistence/prompt code into Rust. |
| `quarry/` (existing) | **`quarry/`** (orchestration) + **`flume/`** (workshop) | split: connectors / transforms / ETL stay in quarry; strict-typed scientific operators (D8, Priority-Flood, flow accumulation) move to flume |
| `topos/` | **`mosaic/`** | rename only, role unchanged |
| `writing/` (scilint) | **`strata/`** | rename only, role unchanged |
| *(new)* | **`bedrock/`** | new canonical data + policy layer; emerges from existing data layouts (Postgres, life-db, on-disk artifacts) consolidated under schema-defined contracts |
| *(new)* | **`outcrop/`** | new lit corpus; Zotero + arXiv + embeddings |

## Migration strategy

**Big-bang preferred.** You're mid-flight in dgov + quarry simultaneously, so incremental migration creates N painful weeks instead of one painful weekend. Pick a window, do it cleanly.

## Order of operations

1. **kernel distributary first.** Move dispatch/plan/run authority into `watershed-kernel/watershed-distributary/` when a Rust transition consumes it. Keep any Python/TS layer as orchestration only.
2. **kernel tributary second.** Move ingest/validate/merge/baseline authority into `watershed-kernel/watershed-tributary/` when the law is consumed by the tributary ceremony. Wire up the handoff from distributary explicitly: completed runs emit typed `Deposit`; tributary validates it into `Validation`, `Merge`, and `Baseline` records.
3. **flume.** Pull strict-typed scientific operators from existing `quarry/` — D8, Priority-Flood, flow accumulation, registry, pressure-tests. These become the workshop floor.
4. **quarry.** What's left in original `quarry/` becomes the orchestration / connector / transform layer. Owns the untyped→typed boundary.
5. **strata.** Move scilint from `writing/`. Brand copy ("Your manuscript is not ready") survives the rename.
6. **mosaic.** Move topos. `tile-ripper` likely merges in here.
7. **bedrock.** Consolidate canonical data + policy. May involve schema work to make the existing Postgres / life-db / on-disk artifacts policy-compliant under one substrate.
8. **outcrop.** New build. Heaviest *new* code in the migration. Wire writeable Zotero (pyzotero against web API) + arXiv ingest + vector index. Vector store: probably pgvector against your existing local Postgres.

## Commit history strategy

| module | strategy | reason |
|---|---|---|
| watershed-kernel distributary/tributary crates | preserve in watershed-kernel history | authority-bearing state machines live in Rust; Python package history should not become a second law |
| quarry, flume | preserve from existing quarry; need to split history along directory boundaries | active; the split itself is interesting historically |
| mosaic | squash from topos | less active, cleaner |
| strata | preserve from writing/ | scilint has a story worth keeping |
| bedrock | new commits only | nothing to preserve |
| outcrop | new commits only | nothing to preserve |

## Downstream references to update

- `sentrux` integration — does it import `dgov` by name? If so, alias to `tributary` since that's where baselines live now.
- `.mcp.json` — `qgis_mcp` and `firepass-mcp` paths point into `~/projects/`; check that none reference dgov or quarry by absolute path.
- `sandfrom.space/dgov/` → kernel-backed distributary/tributary documentation redirects once a public surface exists.
- Bluefield / Hermes agent configs — any hardcoded `dgov` references.
- `~/projects/CLAUDE.md` — update shorthand section once committed.
- Any external docs / install instructions referencing `dgov`, `scilint`, or `topos` by name.

## Transition window

14–30 day deprecation window where old CLI names alias to new ones with deprecation warnings. Then drop.

## Status

The top-level Python `distributary/` and `tributary/` package attempt was removed. Authority-bearing fan-out/fan-in work now lives in Rust under `watershed-kernel/`; future rim code should consume that substrate instead of reimplementing it. The migration rule is specific: move state-machine authority into Rust when the current kernel needs it, and leave orchestration above the kernel.
