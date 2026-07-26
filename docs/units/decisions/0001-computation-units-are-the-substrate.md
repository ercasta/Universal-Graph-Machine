# 0001. Computation units are the substrate

**Status:** Accepted
**Source:** substrate_inversion.md §§0–1, `bench/spike_substrate_inversion_binding.py`

## Context

`ugm/` is a graph that is only data, with computation bolted on: an interpreter steps over a
mutable store. Every mechanism added to it — scope, attribution, hypotheses, degree — has had to be *policed*
against that shared store (visibility checks, write discipline, crossing rules), because any unit of
computation can address anything.

The alternative is to invert it: make the computation units the substrate, and let a graph be the value that
flows between them.

## Decision

**A unit holds a whole subgraph as its state, fires when its input matches its pattern, and emits a
new subgraph. A graph is not a store; it is the value on a wire.** Connections are created at run time, so
depth is assembled on demand rather than pre-wired.

The falsifiable form: **nothing may enumerate globally over data.** Bounded enumeration within one value on
one wire is permitted; a second global structure over facts means something has leaked back into being a
store.

## Evidence

- The immediate payoff is that isolation stops being policed and becomes a **calling convention**:
  a unit cannot see what was not piped into it, because no address for it exists.
- Marker propagation (NETL) was the obvious cheaper design and it fails on the canonical two-place join:
  markers cannot record *which* `?y` a given `?x` went with, so a join becomes a cross-product. Measured —
  markers answer 4, of which 2 are false; subgraph-valued units answer exactly 2.
- `units/` may not import from `ugm/`, asserted by a test rather than intended. What has to be copied is then
  evidence about what was genuinely shared versus what was a store-shaped assumption riding along.

## Consequences

- Depth is not bounded by the topology, so it must be bounded by fuel (`0030`).
- Scope, hypotheses and provenance all have to be re-derived from wiring rather than declared (`0007`).
- `ugm/` stays working and untouched; nothing is retired until this substrate answers a real question end to
  end.
