# 0012. Provenance travels on its own wire, and a unit sees it only if it asked

**Status:** Accepted
**Source:** substrate_inversion.md §16.6, §20, §26

## Context

A conclusion's annotations — degree, attribution — are inherited from the facts that produced it,
and under subset output (`0008`) there is no "afterwards" in which to work out which those were. So provenance
has to be recorded as it happens. The question is where it lives.

## Decision

**Two wires, accreting in opposite directions.** The object wire uses subset output, so silence
gates. The trace wire is append-only: a firing cites the firings that produced its premises. A unit receives
the trace **only if its pattern names a firing predicate** — and subset output is what contains that.

## Evidence

- If provenance accretes onto the object wire, `Absent` stops asking *"is P absent from the world I
  was handed?"* and starts asking *"was P mentioned in the derivation?"* — two different questions with the
  same syntax, which is the worst kind of leak. Asserted by `Net.trace_leaks()`.
- Refusing a unit's request for the trace would make metareasoning unsayable, so the constraint is
  *conditional*, not absolute. Measured three ways: an ordinary unit's view holds no firing predicate, a
  consumer's does, and the consumer's *output* does not.
- `why` is a forward walk over what **fired**, never backward over wires: wires say only what *could* have fed
  a unit, refire keeps only the last output, and late wiring changes the topology.

## Consequences

- Degree inheritance becomes one generic rule that reads the trace wire and writes the object
  wire, rather than a clause per template (`0016`).
- Trace consumers need stratification or they feed each other forever (`0013`).
- Trace wiring is maximally unselective and no static analysis can fix it (`0022`).
