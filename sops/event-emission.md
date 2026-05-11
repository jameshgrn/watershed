---
name: event-emission
title: Event Emission
summary: The typed-record-and-emission-act discipline for lab events — frozen-dataclass shape, content-derived identity, one canonical emitter per event type, typed references to chain records, append-only inscription, frozen-pin at emission, and the boundary against subscription (deferred).
applies_to: [event, emission, frozen_dataclass, append_only, lifecycle, observability, telemetry, registry, chain]
priority: must
version: 1
authored_by: Watermaster Glide
inscribed: 2026-05-10
canon_anchor: Articles II, III, IV, V, IX, XV
---

## When

- defining a new event type for any lab module's lifecycle, telemetry, or observation surface
- proposing a revision to an existing event type's shape, fields, or discriminator
- emitting an event at a canonical emission site (kernel transition, runner exit, settlement phase, integration verdict, operator submit, etc.)
- registering an event type in the typed-event registry (today dgov's `VALID_EVENTS` / `_EVENT_TYPE_MAP`; eventually `shared/`)
- lifting dgov's existing event types into `shared/` under typed-reference discipline
- proposing an administrative reset (today's dgov `reset_plan_state` / `reset_task_state`) that touches the events store

## Do

- represent every event as a frozen dataclass (`@dataclass(frozen=True)`) carrying: `event_type: Literal["<discriminator>"]` (the type-name string discriminator, hardcoded as the default value), `id: str` (content-derived, stable, computed at emission), `emitted_at: datetime` (UTC tz-aware, recorded at emission), `emitter: str` (the canonical emission site, named in code), `payload_hash: str` (content hash over the event's typed payload fields), plus the event's typed payload fields
- compute `id` from `(event_type, emitter, emitted_at, payload_hash)`; the same event_type at the same emitter at the same instant with the same payload yields the same id
- compute `payload_hash` from a content hash over the event's typed payload fields (every field other than `event_type`, `id`, `emitted_at`, `emitter`, `payload_hash`), with keys sorted; identity is stable across re-serialization
- reference chain records by typed id pointer: `from_plan_id: str | None`, `from_dispatch_run_id: str | None`, `from_operator_run_id: str | None`, `from_deposit_id: str | None`, `from_validation_id: str | None`, `from_merge_id: str | None`, `from_baseline_id: str | None`, `from_artifact_id: str | None`, `from_intent_id: str | None`, `from_plan_unit_slug: str | None` — populate the fields that apply, leave the rest `None`
- distinguish "field unset" (`None`) from "field has typed empty value" (typed default) — every reference field is `str | None = None`; every payload field with a meaningful empty form is the typed empty (`tuple[str, ...] = ()`, `Mapping[str, str] = {}`); no empty-string sentinels for fields that should be `None`
- enforce one canonical emitter per event type: each event class is emitted from exactly one named code site, recorded in the event's `emitter` field as a stable identifier (e.g., `"kernel.run_start"`, `"runner.task_done"`, `"settlement_flow.phase_started"`); multi-site emission for the same event type is forbidden except for the explicitly escalate-named `worker_log` case
- gate emission with a typed registry: every emitted event type is present in the typed-event registry (`shared/` table; today dgov's `_EVENT_TYPE_MAP`); emission of an unregistered event type raises `UnknownEventTypeError`
- validate emission at the boundary: emitting an event raises `EmissionError` when (a) the event type is not registered, (b) a required typed-reference field cannot resolve to a known chain record, or (c) the event's payload fails its own dataclass field-type discipline
- inscribe every emitted event into the append-only event store; reads return the same bytes for the same `id` indefinitely
- treat an event as frozen-pinned at emission: every field is immutable after `emitted_at`; revisions are forbidden (any need to "correct" an event is escalate territory)
- emit a typed `EmissionFailure` event when emission itself fails (database lock, store full, schema mismatch); emissions are never silently dropped
- name the emitter site in code by a stable string (`emitter = "kernel.run_start"`) rather than by an inline lambda or anonymous call site; the string is the identifier readers query against
- preserve verbatim payload reference fields: when an event references chain records, the typed id is recorded as the bytes the chain record uses for identity, never paraphrased or normalized
- distinguish telemetry events (observation-only, no state-machine consequence) from lifecycle events (cause downstream state transitions) — both are typed and registered; the registry indicates which class the event belongs to (`event_class: Literal["lifecycle", "telemetry"]` per registry entry, not per event instance)

## Do Not

- mutate an event after emission; the event store is append-only at the discipline level
- emit an event with autoincrement-only identity; identity is content-derived from `payload_hash` and emission context
- emit the same event type from multiple canonical sites; one event type, one canonical emitter (`worker_log` escalate-named exception)
- reference chain records by surface form (`pane`, `plan_name`, `task_slug` strings) when the typed id is recoverable; today's dgov string references are frozen-pinned debt, not aspirational pattern
- use empty-string defaults on reference fields (`pane: str = ""`, `plan_name: str = ""`); `None` is the absence sentinel
- silently drop an emission (database lock, store full, transient failure); failures emit `EmissionFailure` and surface as typed errors to the emitter
- store untyped `dict[str, Any]` payloads outside the escalate-named legacy cases (today's settlement `evidence`); new events use typed payload fields
- delete or mutate events to satisfy an administrative reset; reset is a separate typed `EventStoreReset` record naming the deleted range, not an in-place DELETE
- emit an event whose required typed-reference field is `None` when the surrounding context has a resolvable record; `None` is for genuinely absent references, not for "I didn't pass it in"
- mix lifecycle and telemetry within a single event type; the typed-event registry classifies each type, and downstream consumers (eventually) bind on the class
- skip preflight when adding a new event type; the typed-event registry is part of the lab's typed-contract surface
- emit events from non-watershed code paths (Workers in subprocess, external services) without crossing the rim discipline per CANON Article III; events that originate outside watershed are materialized through a Connector-shaped emission rim, not freelanced
- carry runtime UI state (pane slug, tmux pane id, terminal window state) on an event as a primary identity field; runtime UI state is operational, recorded in `metadata` if at all, and never part of identity
- duplicate a chain record's fields on the event when the chain record is referenceable by id; downstream readers resolve by id

## Verify

- every emitted event has a stable content-derived `id`; re-construction with the same event_type, emitter, emitted_at, and payload yields the same id
- every emitted event's `payload_hash` matches a re-hash of the typed payload fields in canonical key-sorted form
- every event's `event_type` matches the discriminator literal of the dataclass that constructed it
- every event type in the typed-event registry is implemented by exactly one frozen dataclass and emitted from exactly one canonical site (excepting `worker_log`)
- every typed-reference field on an event, when non-`None`, resolves to a known chain record in the appropriate registry
- a query for "all events for `from_plan_id == X`" returns the set in emission-time order; the same for `from_dispatch_run_id`, `from_operator_run_id`, etc.
- emission of an unregistered event type raises `UnknownEventTypeError`; emission of an event with an unresolvable required reference raises `EmissionError`
- the event store contains no rows that bypass `id` content-derivation or `payload_hash` pinning (post-lift; today's dgov rows are frozen-pinned at their state and escape the post-lift discipline)
- an event read from the store equals (by content hash) the event emitted, indefinitely
- an `EmissionFailure` event is present in the store for every observed silent-drop case; no transient failures lose telemetry without typed acknowledgement (post-lift)
- the typed-event registry is the single authoritative source of "what events the lab can emit"; the dataclass module and the registry stay in lockstep — adding a class without registering it, or registering an entry without a class, fails verification
- adding a new event type leaves a preflight record per `watermaster-preflight.md`

## Escalate

- if a new event type cannot be expressed as a frozen dataclass without distortion (deeply variable payload, recursive structure) — propose typed extension or a parameterized event family via preflight, not a `dict[str, Any]` carrier
- if an emission site legitimately needs to emit two event types from one code path (e.g., a transition that observes both lifecycle and telemetry) — emit them as two separate events; the one-event-one-emitter rule does not block two events from one site
- if `worker_log` (or another legitimate multi-emitter case) recurs — propose making the case canonical with an explicit "multi-emitter" registry flag rather than treating each new case as one-off
- if a chain record's reference shape cannot be reduced to a typed id (e.g., a reference to a record-not-yet-materialized) — record the reference fields as `None` and emit a follow-up event when the record materializes; never freelance an intermediate untyped reference
- if dgov's existing event types must be migrated under invariants different from this SOP — frozen-pin them at their dgov state per Article XV and mint new event types under the SOP for going-forward emissions; the lift discipline matches the pattern `plan-shape` and `dispatch-run-shape` adopt for dgov-in-flight records
- if an administrative reset of the event store (today's `reset_plan_state` / `reset_task_state`) is legitimately required — propose a typed `EventStoreReset` record that names the deleted range, the cause, and the authorizing Watermaster; mint via preflight; do not normalize DELETE-on-events
- if a `dict[str, Any]` payload on legacy events (today's settlement `evidence`) becomes intolerable for downstream consumers — propose typed extraction via preflight; do not retrofit the legacy event without naming the contradiction
- if the typed-event registry's home (today dgov's `_EVENT_TYPE_MAP` and `VALID_EVENTS`) must move into `shared/` before distributary lifts — the lift discipline is its own preflight; this SOP does not prescribe the lift timing
- if subscribers begin to bind on events before a parallel `event-subscription` SOP exists — escalate via preflight; binding is a typed contract that requires its own discipline, not a side door from emission
- if the bundler-hash-composition gap that `dispatch-run-shape` v1 escalates has an analogue at the emission boundary (e.g., events that should drift-flag worker-SOP bundle changes but don't) — that is a chain-SOP revision touching events, not this SOP
- if an event must be emitted from non-watershed code (a Worker subprocess, a sentrux subprocess, a connector) — propose an emission-rim Connector-shaped contract via preflight; do not freelance cross-rim emission
- if the typed-event registry needs to support multiple versions of one event type — propose `schema-versioning.md`-style integer versions on the registry entry, or distinct event_type strings per version; do not collapse them under one identifier
