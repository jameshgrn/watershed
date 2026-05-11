---
name: pointer-canonicalization
title: Pointer Canonicalization
summary: Bedrock's Pointer identifies a resource by canonical form, not surface form. Connectors canonicalize at the rim; the registry indexes by canonical Pointer; equality is canonical-form equality.
applies_to: [pointer, uri, identity, equivalence, connector, registry, bedrock, canonicalize]
priority: must
version: 1
authored_by: Watermaster Thalweg
inscribed: 2026-05-07
canon_anchor: Articles II, III
---

## When

- producing a `Pointer` (any code that constructs one)
- writing a Connector or modifying its materialize path
- registering an Artifact with a Pointer reference
- adding support for a new URI scheme to the lab
- diagnosing duplicate registrations or missing lineage connections that may stem from non-canonical Pointer surface forms

## Do

- canonicalize every URI through `bedrock.pointer.canonicalize(uri) → Pointer` before constructing a Pointer or registering against one
- treat Pointer equality as equality of canonical form, not surface URI string
- index every registry by canonical Pointer; canonicalize lookup queries before search
- register a per-scheme canonicalization rule before any Connector materializes from that scheme; rules live in bedrock's per-scheme registry
- write canonicalization rules that are idempotent (`canonicalize(canonicalize(uri)) == canonicalize(uri)`), equivalence-preserving (two URIs for the same resource map to one canonical form), and distinct-preserving (two URIs for different resources never collide)
- represent composite resources (STAC item with assets, multi-file datasets, etc.) as a parent Pointer plus separate Pointers for each accessible part; never collapse the parts into the parent
- treat `Pointer` as identity-of-location only; for identity-of-content, use the Artifact's content-addressed `id`; the two are distinct

## Do Not

- compare Pointers by surface URI string
- bypass `canonicalize` in any code path that produces a Pointer
- register an Artifact under a non-canonicalized Pointer
- silently drop unknown URI schemes; raise a typed error and require registration of a rule
- collapse query parameters wholesale; some change content (`?version=42`) and some do not (`?utm_source=...`); the per-scheme rule must distinguish them explicitly
- canonicalize to a cache or local access path; the canonical form is the upstream resource, not the access copy
- mutate a Pointer's canonical form after construction

## Verify

- `canonicalize(canonicalize(uri)) == canonicalize(uri)` for every supported scheme
- two known-equivalent URIs (e.g., `s3://bucket/key` and `https://bucket.s3.amazonaws.com/key`) produce equal canonical Pointers
- two known-distinct URIs never produce equal canonical Pointers
- registry queries return the same result regardless of which equivalent surface form was passed
- a Connector cannot produce a Pointer that bypasses `canonicalize` (path-coverage check)
- an unsupported scheme produces a typed error at the boundary, not a fall-back to identity

## Escalate

- if a URI scheme's equivalence rules cannot be expressed without a content-fetching probe (HTTP HEAD or similar) — prefer structural canonicalization unless the case is genuinely necessary
- if two schemes have an equivalence relation across them that needs canonical convergence (e.g., a `data:` URI and a content-addressed Pointer pointing at the same bytes) — that is a cross-scheme rule, not a per-scheme one
- if a Connector requires non-canonical Pointer access for a legitimate reason (rare; usually a sign the scheme rule is wrong)
- if Pointer canonical form must change because the per-scheme rule was wrong — every existing registration depending on the old canonical form is affected; treat as a frozen-pin migration per `schema-versioning.md`
