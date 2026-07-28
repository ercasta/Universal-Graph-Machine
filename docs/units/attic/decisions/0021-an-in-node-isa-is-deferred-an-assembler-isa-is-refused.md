# 0021. An in-node ISA is deferred; an assembler ISA is refused

**Status — current (2026-07-28): HISTORICAL.** predates the substrate inversion (2026-07-26). Not contradicted by name in `../../model.md`, and not carried forward as current either — read it as context, not as a decision in force.

**Status — as recorded:** Deferred
**Source:** substrate_inversion.md §20.4

## Context

`ugm/` puts capabilities in an instruction set rather than in Python helpers, on the principle that
anything hardcoded in Python is an unreachable island. The same question applies to a unit's pattern and to the
assembler's policy.

## Decision

**In-node ISA: deferred.** No unreachable island exists there today — a pattern is authored data
and matching is a pure function of it. **Assembler ISA: refused**, on `0010`'s line rather than on cost.

## Evidence

- The discriminator used: *does deferring risk correctness, or only cost?* Here only cost, and a
  previous lowering pass in `ugm/` proves the retrofit is possible.
- **Named triggers to build it:** the first unit that must observe or emit another unit's *program*, or the
  first `SUSPEND` — which means procedures reopen this question on schedule rather than as drift.

## Consequences

- Procedures cannot be built without revisiting this.
- Nothing currently prevents a unit from reasoning about a *pattern*, because patterns are already data.
