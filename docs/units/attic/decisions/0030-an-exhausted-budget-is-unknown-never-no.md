# 0030. An exhausted budget is UNKNOWN, never NO

**Status — current (2026-07-28): REPLACED.** `../../model.md` §11 — fuel is a positive fact (`out_of_fuel`) among five outcomes, not a value `UNKNOWN`.

**Status — as recorded:** Accepted
**Source:** substrate_inversion.md §7; `units/fuel.py`

## Context

Depth here comes from assembling new instances, not from traversing a fixed topology, so the loop
cannot be bounded structurally. It is bounded by fuel — and a fuel limit is a fact about resources, not about the
world.

## Decision

**`Verdict` is three-valued and refuses to be truthy**, so `UNKNOWN` cannot collapse into `NO` at a
call site that forgot to check.

## Evidence

- The whole point of separating the two negations (`0011`) is undone if a resource limit can silently
  become a claim, so the type enforces it rather than the caller remembering.

## Consequences

- Callers must ask explicitly. That is the intended friction.
- Reasoning is demand-driven and *incomplete on purpose*; an honest "I ran out" beats a confident wrong answer.
