# outcrop/

**Lit corpus.** The visible exposed face of accumulated literature.

## Provenance

New module. No existing repo to migrate from. Will replace ad-hoc Zotero browsing.

## What it owns

- **Zotero (writeable)** — pyzotero against the Zotero web API key, full CRUD: add, update, delete, batch tag, collection management
- **arXiv / preprint feeds** — daily / weekly ingestion against saved queries
- **Embeddings** — vector index over your library for semantic search
- **Citation API** — `cite(reference_id) → BibTeX` so `strata/` can pull citations by ID

## Public types it exposes (planned)

- `Reference` — a unique reference with citekey, abstract, embedding, source (Zotero / arXiv / inline)
- `ReadingList` — a project-tagged ordered collection of references
- `Query` — a saved search that can run on a schedule

## Why "outcrop"

An outcrop is the visible exposed face of underlying strata — bedrock or sedimentary layers, but laid bare. Literature is exactly that: the visible exposed face of accumulated thought, the part of the field's substrate that's been *exposed* and made readable. Papers outcrop; pre-print servers are fresh exposures.

The static-geology pair (`bedrock`, `outcrop`) brackets the dynamic infrastructure of the lab — substrate beneath, exposed knowledge above; everything in between flows.

## Status

Placeholder. The biggest piece of *new* code in the lab — most other modules are renames or carve-outs. Will probably be the second-priority build after distributary/tributary stabilize, since strata can wait on richer outcrop integration.

## Open questions

- **Vector store**: in-process (FAISS / chroma) vs Postgres + pgvector against your existing local Postgres? You already run Postgres for life-db; pgvector is probably the lowest-friction path.
- **arXiv ingestion frequency**: daily cron via the `schedule` skill, or on-demand?
- **Embedding model**: local (Apple MLX) or hosted? firepass-mcp's Kimi long-context could be useful for batch summaries even if not embeddings.
