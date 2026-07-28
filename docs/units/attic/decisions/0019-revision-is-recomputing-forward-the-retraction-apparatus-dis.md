# 0019. Revision is recomputing forward; the retraction apparatus dissolves

**Status — current (2026-07-28): SURVIVES, vindicated and strengthened.** `../../model.md` §1 — revive-from-axioms is what makes it literally true. Invariant 11.

**Status — as recorded:** Accepted
**Source:** substrate_inversion.md §7, §24.2

## Context

`ugm/` has a retraction cascade, copy-on-delete, and broken-assumption stamps — a substantial
apparatus for un-concluding things.

## Decision

**Nothing is retracted. A unit re-runs and downstream recomputes.** Retracting a *fact* is not a
data operation at all: it is deleting the `given` unit that supplied it, i.e. an operation on **topology**.

## Evidence

- The apparatus in `ugm/` is an artifact of mutable shared state and has no work to do here.
- It falls out rather than being designed, which is the main argument that the inversion is doing something.

## Consequences

- **This rests on rules being monotone accumulators** (`0004`), which is why `0032` is a
  paradigm question.
- A *state claim* — as opposed to a firing — must still be actively withdrawn when it stops holding, or it is a
  false report. Firings accrete; state claims do not.
