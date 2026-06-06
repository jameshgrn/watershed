# Engineer Return — Brief 3 (Artifact.id content-derivation)

**brief_id**: `brief-3-artifact-id-content-derivation` (refers to `/Users/jakegearon/projects/watershed/sketches/briefs/07-knickpoint/brief-3-artifact-id-content-derivation.md`)
**received_at**: 2026-05-11
**integrated_by**: Watermaster Knickpoint
**integration_action**: verified writes — all seven items (A–G) accepted; three derivation strategies + two canonicalization helpers landed in quarry-core; six Connectors updated for content-derivability (mixed eager/lazy paths); Zarr eager extended to hash directory stores; all 16 Operators already correct from Brief 1 (no further work needed); 22 new identity tests pass

## Files written

In-scope per Brief 3's write scope:

- `/Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/artifact.py` — `ArtifactIdentityError(ValueError)`, `canonical_params`, `canonical_uri`, `derive_id_from_source_bytes`, `derive_id_from_provenance`, `derive_id_from_source_ref`, `_derive_artifact_id` dispatch helper, and `__post_init__` extension that derives when `id is None`. `Artifact.id` field type changed to `str | None = None` (was `str = field(default_factory=lambda: str(uuid.uuid4()))`).
- Six Connectors with content-derivability fixes (eager content_hash population or lazy `lineage.params` discrimination):
  - `quarry-connectors/src/quarry_connectors/cog.py` (mixed eager/lazy)
  - `quarry-connectors/src/quarry_connectors/local_file.py` (mixed eager/lazy)
  - `quarry-connectors/src/quarry_connectors/fof_stack.py` (mixed)
  - `quarry-connectors/src/quarry_connectors/pixc.py` (mixed)
  - `quarry-connectors/src/quarry_connectors/postgis.py` (canonical backing URI lifted into the new `canonical_uri` helper; local `_backing_uri` now calls the shared helper)
  - `quarry-connectors/src/quarry_connectors/zarr.py` (eager — now content_hashes the directory store; net-new directory-hash logic to satisfy the discipline; smallest extension of the existing `content_hash(path)` helper)
- 23 other Connectors required no changes (CSVXY, DuckDB, ExcelXY, FlatGeobuf, GeoJSONSeq, GeoPackage, GeoParquet, GPX, HDF5, KMZ, LASPointCloud, MBTiles, NetCDF, ObjectStore, OGCServices, OpenTopography, Overture, Sentinel2, Shapefile, SLC, SpatiaLite, STAC, TopoJSON).
- No Operators required changes — Brief 1's work already set `lineage.operation = self.name`, `lineage.inputs`, and `lineage.params` correctly across all 16.
- New tests: `test_artifact_id_derivation.py`, `test_canonical_params.py`, `test_canonical_uri.py`, `test_artifact_id_post_init.py`, `test_connector_artifact_id_stability.py`.
- Updates to existing test fixtures that hardcoded uuid4 expectations — Codex passed explicit fixture ids where the tests were not testing derivation itself.

No file under `/Users/jakegearon/projects/watershed/` was modified.

## Test results

- Focused new identity tests: **22 passed**.
- Brief 1 + Brief 2 + Brief 3 focused surface tests: **98 passed**.
- Operator pressure subset: **426 passed**.
- Full pressure_test: **1949 passed, 54 skipped, 3 failed**. The 3 failures are the Source's pre-existing in-progress GeoJSON connector/router/docs work, unrelated to Brief 3 (consistent with Brief 1 and Brief 2 baselines).
- `ruff check`, `ruff format --check`, `git diff --check` on Brief 3 scope: pass.
- `ty check` on the modified `artifact.py`: pass. Connector-wide `ty` reports pre-existing SourceRef/optional-dependency diagnostics unrelated to Brief 3.

Test progression across Briefs (full pressure_test path): Brief 1 baseline 1896 → Brief 2 1927 (+31 new) → Brief 3 1949 (+22 new). 53 new tests across three Briefs.

## Deviations integrated

1. **`Lineage.inputs` not `input_ids`** (Item E wording correction). The Brief used `input_ids` based on a memory of `data-contracts.md` v2's wording; the actual field name on the Lineage record in quarry-core is `inputs`. Codex used the real field name. Integrated as wording fix; the discipline (provenance includes input artifact ids in canonical order) is unchanged.
2. **Zarr eager directory-hash** (Item D extension). Brief 3 named the constraint ("eager Connectors must populate content_hash") but didn't anticipate Zarr's directory-store layout where `content_hash(path)` fails on a directory. Codex extended the hashing logic to recursively hash directory contents, smallest change consistent with the discipline. This was useful adjacent work needed to satisfy the discipline rather than out-of-scope scope creep — the Brief's "no construction site blocked content derivation" requirement forced the question; Codex answered it without widening surface area. Integrated.

No other deviations.

## Connector survey (verbatim from return)

- Changed: COG (mixed), LocalFile (mixed), FOFStack (mixed), PIXC (mixed), PostGIS (mixed), Zarr (eager now source-byte derived).
- No change needed (23): CSVXY, DuckDB, ExcelXY, FlatGeobuf, GeoJSONSeq, GeoPackage, GeoParquet, GPX, HDF5, KMZ, LASPointCloud, MBTiles, NetCDF, ObjectStore, OGCServices, OpenTopography, Overture, Sentinel2, Shapefile, SLC, SpatiaLite, STAC, TopoJSON.

## Operator survey

All 16 Operators' Lineage construction in `execute()` already sets `operation = self.name`, `inputs = tuple(input.id for input in inputs)`, `params = <OperatorParams dict>`. No fixes needed: Aspect, BuildCOG, ClipRaster, D8FlowDirection, FillDepressions, FlowAccumulation, GeocodeSLC, Hillshade, RasterizeVector, Reproject, SampleRaster, SLCCalibration, Slope, SpatialJoin, WaterElevationMosaic, ZonalStats.

This is a positive externality of Brief 1 — operator-shape v1 alignment correctly set `lineage.operation`, and downstream consistency carries through to Brief 3's provenance derivation without further operator-side work.

## Flags

No new escalate-territory flags from Brief 3. All construction sites can now derive content-based ids. The 8 dual-residence flags from Brief 2 remain open (Thread B design question), and the Source's in-progress connector work continues to be the source of the 3 known pressure-test failures.

## Verbatim Engineer return (chat content)

```
Summary
   Brief 3 landed in /Users/jakegearon/projects/quarry: Artifact.id now derives from source bytes, operator provenance, or lazy source refs; URI/params canonicalization is centralized in quarry-core; lazy connector params were tightened where needed; Zarr eager now hashes directory stores; operator lineage needed no fixes. No watershed files were modified by me.

Item-by-item
   A-C: Implemented ArtifactIdentityError, canonical_params, canonical_uri, derive_id_from_source_bytes, derive_id_from_provenance, derive_id_from_source_ref, and Artifact.__post_init__ derivation in /Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/artifact.py.
   D: Connector pass-through changes: COG canonical source refs, PostGIS canonical backing URI, LocalFile/FOF/PIXC lazy source labels, Zarr eager content_hash.
   E: Surveyed all 16 operators. Existing lineage already sets operation=self.name, ordered inputs, and params. No operator business logic changed.
   F-G: Added identity/canonicalization/connector stability tests and updated legacy uuid-default test fixtures to pass explicit fixture ids where they are not testing identity derivation.

Connector survey
   Changed: COG mixed; LocalFile mixed; FOFStack mixed; PIXC mixed; PostGIS mixed; Zarr eager now source-byte derived.
   No change needed: CSVXY, DuckDB, ExcelXY, FlatGeobuf, GeoJSONSeq, GeoPackage, GeoParquet, GPX, HDF5, KMZ, LASPointCloud, MBTiles, NetCDF, ObjectStore, OGCServices, OpenTopography, Overture, Sentinel2, Shapefile, SLC, SpatiaLite, STAC, TopoJSON.
   Extra note: pre-existing untracked GeoJSON connector is still causing the known router/docs failures.

Operator survey
   All 16 passed the lineage read: Aspect, BuildCOG, ClipRaster, D8FlowDirection, FillDepressions, FlowAccumulation, GeocodeSLC, Hillshade, RasterizeVector, Reproject, SampleRaster, SLCCalibration, Slope, SpatialJoin, WaterElevationMosaic, ZonalStats. No fixes needed.

Flags
   No construction site blocked content derivation after the Zarr directory-hash fix. Lineage.inputs is the current field name, so provenance derivation uses that instead of the brief's input_ids wording. ty check passes for /Users/jakegearon/projects/quarry/packages/quarry-core/src/quarry_core/artifact.py; connector-wide ty still reports pre-existing SourceRef/optional dependency diagnostics.

Test results
   Focused new identity tests: 22 passed.
   Brief 1/2 + Brief 3 focused surface tests: 98 passed.
   Operator pressure subset: 426 passed.
   Full /Users/jakegearon/projects/quarry/tests/pressure_test: 1949 passed, 54 skipped, 3 failed. The 3 failures are the known GeoJSON/router/docs workspace issues, not Brief 3.
   Lint/format: targeted ruff check passed; targeted ruff format --check passed; git diff --check passed.
```
