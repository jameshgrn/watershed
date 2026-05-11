# strata/

**Manuscript consumer.** Layered argument; deposits of thought.

## Provenance

`strata/` is `scilint/` (in `writing/`) renamed.

## What it owns

- **Linting** — three-tier manuscript review: deterministic regex (T1), LLM sentence analysis (T2), section-level argument structure (T3). Reads LaTeX / Markdown / PDF.
- **Binding** — manuscript sections reference `mosaic.Figure` IDs; if a figure regenerates, strata flags the section as stale
- **Citations** — pulls from `outcrop.Reference` by ID so citekeys + abstracts stay current
- **Terminal UI** — read, review, edit with live linting, accept/reject fixes, commit

## Public types it exposes (planned)

- `Manuscript` — a typed reference to a LaTeX document with sections, figure refs, citation refs
- `Section` — a unit of prose with attached references
- `LintFix` — a deterministic fix strata can apply
- `LintFlag` — a non-fixable issue requiring human attention

## Why "strata"

A paper is layered argument: introduction sediments down on results, methods underpin the discussion, the abstract caps the column. Sections are deposits with unconformities between them — exactly where reviewers attack. Plural form ("strata") because the surface holds many manuscripts and many revision-layers within each one.

## Type discipline

Strata only consumes typed outputs:
- `Figure` from mosaic (binds by ID, flags staleness on lineage change)
- `Reference` from outcrop (binds by ID, refreshes on update)
- nothing else crosses into the manuscript surface

## What survives the rename

The brand copy. The README opens with *"Your manuscript is not ready"* — that line works regardless of what the tool is called. Plus the three-tier architecture, the terminal UI, the existing rules engine.

## Status

Placeholder. Awaiting migration from `~/projects/writing/` (where scilint currently lives).
