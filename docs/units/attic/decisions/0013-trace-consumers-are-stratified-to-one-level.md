# 0013. Trace consumers are stratified to one level

**Status — current (2026-07-28): SUPERSEDED.** `../../model.md` §1 — stratification is dropped with the provenance wire.

**Status — as recorded:** Accepted
**Source:** substrate_inversion.md §26.1 — discovered, not designed

## Context

A unit that reads only firing predicates (an explanation hop, a stability watcher) has nothing to
spawn on the object wire, so it spawns on its trace half. And then: every unit has a trace; a trace consumer is
itself a unit; so consumers feed consumers.

## Decision

**A unit that reads the trace is never wired to the trace of a unit that reads the trace.** Level 0
is the world, level 1 is about level 0, and level 2 would need a deliberate act — there is not one.

## Evidence

- Measured before the guard existed: **57 instances, fuel exhausted.** Because firing nodes are
  minted, the projection never repeats, so the ordinary dedup never fires either.
- The guard is a single local test over a unit's own pattern (`Net.reads_trace`).
- **This wall was predicted in writing and walked into anyway** — the note said stratification "must be designed
  in, not discovered", and it was discovered. Worth remembering about this document's other predictions.

## Consequences

- Journal predicates count as firing predicates, so the same guard covers them for free.
- Genuine multi-level metareasoning would need an explicit act, which is the right shape for it.
