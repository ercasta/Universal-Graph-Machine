# 0033. Force is unit shape, not a router

**Status — current (2026-07-28): HISTORICAL.** predates the substrate inversion (2026-07-26). Not contradicted by name in `../../model.md`, and not carried forward as current either — read it as context, not as a decision in force.

**Status — as recorded:** Designed, not built
**Source:** substrate_inversion.md §16.6, §24.2

## Context

Assert / ask / command / author / suppose / retract were previously *intake routes* — a dispatch
decision made before anything reached the substrate. Nothing in `Unit` or `Net` distinguishes an asserted output
from a supposed one.

## Decision

**Each force is a different act on the network:**

| force | the act |
|---|---|
| assert | spawn a `given` (in-degree 0) |
| author a rule | `declare` a template — the library, not a unit |
| ask | spawn a **sink** on the object wire; `why` is a sink on the trace wire |
| suppose | spawn a `branch` |
| command / act | a unit that **suspends** |
| **retract** | **delete the `given` unit** — an operation on topology, not on facts |

## Evidence

- The retract row was not designed; it falls out of `0019`, and it is the cleanest thing in the
  mapping.
- Nothing here needs a router: the force *is* which construct gets built.

## Consequences

- Atomic chains are unimplementable until this exists, because nothing currently marks an
  intermediate as carrying no assertoric force (`0034`).
- Intake has nothing to map onto until this exists.
- The **sink** is the cheapest piece and exercises force, wiring and `Verdict` at once.
