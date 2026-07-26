# 0023. What may start a computation and what distinguishes two of them are different questions

**Status:** Accepted
**Source:** substrate_inversion.md §28.1, §29.1; `bench/spike_assembler_completeness.py`

## Context

The assembler decides two things about a producer's offer: whether it may *instantiate* a template,
and what that offer is *identified by* for deduplication. These were computed from the same set, and the results
were wrong in both directions.

## Decision

**The trigger is the positive body only. The projection spans both polarities.**

- **Trigger** — a template must never be instantiated on *"there is no P"*: such an instance has no positive
  premise and nothing to conclude from.
- **Projection** — it is an *identity*, so two offers differing only in a negation-relevant fact are
  **different offers**.

## Evidence

Two silent defects, both answer-changing:

- **A negated premise's producer was never wired.** Its predicate was in no need set, so under subset output the
  negation was evaluated against a value the fact never reached: a rule concluded `walker` with `dead` derived
  and sitting one wire away. **A false conclusion, on a three-atom rule.**
- **Two sibling worlds collapsed into one.** Branches differing only in a negation-relevant fact project
  identically on the positive half, so the second was declined as *nothing new* — and **the world where the
  answer was YES had no instance at all.**

A related granularity error had to be fixed alongside: **the join is over atoms, not predicates.** A
predicate-level need cannot say *"another producer of `is_a`, for a different atom of it"*, and reported the need
as already satisfied.

## Consequences

- Collapsing the two **loses worlds** rather than raising an error, which is the general hazard:
  `_offer` now returns `None` for *nothing to trigger on* and the both-polarity projection otherwise, so they
  cannot be confused again.
- Coreference is unbuildable without this fix: its inequality guard depends on a negated premise's producer
  actually being wired.
