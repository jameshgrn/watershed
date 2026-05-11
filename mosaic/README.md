# mosaic/

**Viz consumer.** Stitched output from many satellite passes. Spatial rendering of lab state.

## Provenance

`mosaic/` is `topos/` renamed onto the remote-sensing axis.

## What it owns

- **Globe / map renders** — interactive 3D globe, satellite overlays, basemaps
- **Mosaic stitching** — combine swaths / tiles / passes into single rendered views
- **Lineage-aware figures** — render a figure tied back to a `flume.Run` so provenance survives publication
- **Embeds** — output viz that strata manuscripts can reference by ID

## Public types it exposes (planned)

- `Figure` — a typed Artifact specialized for visual output, with run_id, code, parameters, rendered representation
- `Basemap` — a registered tile source
- `Pass` — a satellite pass / swath as a typed unit
- `Layer` — a renderable overlay on a basemap

## Why "mosaic"

What `topos/` does is stitch satellite output into renderable composites. "Mosaic" is the remote-sensing-native term for exactly that: many passes assembled into one image. Topos was Greek-place; mosaic is your actual technical vocabulary.

## Type discipline

Mosaic only consumes typed outputs from flume. Anything that lands here has already gone through quarry's transforms and flume's strict-typed operators. No raw data ever crosses into mosaic.

## Status

Placeholder. Awaiting migration from `~/projects/topos/`. `~/projects/tile-ripper/` may merge in — it produces the tiles mosaic stitches.
