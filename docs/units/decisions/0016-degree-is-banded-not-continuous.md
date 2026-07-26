# 0016. Degree is banded, not continuous

**Status:** Accepted
**Source:** substrate_inversion.md §22

## Context

Uncertainty could be a number in [0,1] or a small ordered set of bands.

## Decision

**A finite band lattice**, with `meet` = min.

## Evidence

**Finiteness is load-bearing for termination, not style.** A continuous degree can be revised by
ever-smaller amounts forever, so "output unchanged" never holds. A finite lattice reaches a fixed point.

## Consequences

- Degree inheritance is one generic rule over the firing record — three atoms — rather than a
  clause per template. It reads the trace wire and writes the object wire, which is where the two networks meet.
- **A graded absence is inexpressible** via `grade`, because grading asserts. Explicit negation is the fix
  (`0018`).
- Inheritance grades by *positive* premises only: a conclusion drawn partly from an absence is graded as though
  the absence were free.
