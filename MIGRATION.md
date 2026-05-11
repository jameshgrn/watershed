# MIGRATION

How `watershed/` gets populated from existing repos.

## Rename and split map

| old | new | notes |
|---|---|---|
| `dgov/` | **`distributary/`** + **`tributary/`** | split: distributary owns plan trees + dispatch + worktrees + governor; tributary owns ingest + validate + merge + baseline (sentrux) |
| `quarry/` (existing) | **`quarry/`** (orchestration) + **`flume/`** (workshop) | split: connectors / transforms / ETL stay in quarry; strict-typed scientific operators (D8, Priority-Flood, flow accumulation) move to flume |
| `topos/` | **`mosaic/`** | rename only, role unchanged |
| `writing/` (scilint) | **`strata/`** | rename only, role unchanged |
| *(new)* | **`bedrock/`** | new canonical data + policy layer; emerges from existing data layouts (Postgres, life-db, on-disk artifacts) consolidated under schema-defined contracts |
| *(new)* | **`outcrop/`** | new lit corpus; Zotero + arXiv + embeddings |

## Migration strategy

**Big-bang preferred.** You're mid-flight in dgov + quarry simultaneously, so incremental migration creates N painful weeks instead of one painful weekend. Pick a window, do it cleanly.

## Order of operations

1. **distributary first.** Split dgov: dispatch + plan + worktree code → distributary. Keep CLI alias `dgov` → `distributary` during transition.
2. **tributary second.** Move dgov's ingest + validate + baseline + sentrux integration into tributary. Wire up the contract between distributary and tributary explicitly (typed `Deposit`, `Merge` records).
3. **flume.** Pull strict-typed scientific operators from existing `quarry/` — D8, Priority-Flood, flow accumulation, registry, pressure-tests. These become the workshop floor.
4. **quarry.** What's left in original `quarry/` becomes the orchestration / connector / transform layer. Owns the untyped→typed boundary.
5. **strata.** Move scilint from `writing/`. Brand copy ("Your manuscript is not ready") survives the rename.
6. **mosaic.** Move topos. `tile-ripper` likely merges in here.
7. **bedrock.** Consolidate canonical data + policy. May involve schema work to make the existing Postgres / life-db / on-disk artifacts policy-compliant under one substrate.
8. **outcrop.** New build. Heaviest *new* code in the migration. Wire writeable Zotero (pyzotero against web API) + arXiv ingest + vector index. Vector store: probably pgvector against your existing local Postgres.

## Commit history strategy

| module | strategy | reason |
|---|---|---|
| distributary, tributary | preserve via `git filter-repo` from dgov | active development; blame matters |
| quarry, flume | preserve from existing quarry; need to split history along directory boundaries | active; the split itself is interesting historically |
| mosaic | squash from topos | less active, cleaner |
| strata | preserve from writing/ | scilint has a story worth keeping |
| bedrock | new commits only | nothing to preserve |
| outcrop | new commits only | nothing to preserve |

## Downstream references to update

- `sentrux` integration — does it import `dgov` by name? If so, alias to `tributary` since that's where baselines live now.
- `.mcp.json` — `qgis_mcp` and `firepass-mcp` paths point into `~/projects/`; check that none reference dgov or quarry by absolute path.
- `sandfrom.space/dgov/` → `/distributary/` and `/tributary/` redirects.
- Bluefield / Hermes agent configs — any hardcoded `dgov` references.
- `~/projects/CLAUDE.md` — update shorthand section once committed.
- Any external docs / install instructions referencing `dgov`, `scilint`, or `topos` by name.

## Transition window

14–30 day deprecation window where old CLI names alias to new ones with deprecation warnings. Then drop.

## Status

This is a scaffold. No code has been moved. Module subdirectories contain only placeholder READMEs. Review the structure; when satisfied, the actual migration is a Maker-mode operation in your terminal — distributary can govern its own birth if we're feeling poetic.
