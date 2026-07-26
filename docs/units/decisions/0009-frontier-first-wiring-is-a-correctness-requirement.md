# 0009. Frontier-first wiring is a correctness requirement

**Status:** Accepted
**Source:** substrate_inversion.md §16.4

## Context

When several producers could feed a template, the assembler has to pick. Taking the first one found
is the obvious choice and it is wrong.

## Decision

**Candidates are tried deepest-upstream first.**

## Evidence

Two producers in one lineage can project *identically* while the deeper one carries strictly more
context — a hypothesis marker, a time index, an attribution. Taking the shallower one silently drops that
context, which is precisely a bypass of the unit that added it.

## Consequences

- It is not a performance heuristic and must not be relaxed as one.
- It costs an upstream walk per candidate per template per pass; memoised, and measured linear.
