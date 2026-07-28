# 0003. The store is bounded, not abolished

**Status — current (2026-07-28): SURVIVES.** in force. `../../model.md` §16 carries it as the revive-cost question.

**Status — as recorded:** Accepted
**Source:** substrate_inversion.md §2b (a correction the original design did not state)

## Context

"No blackboard" was stated as though units had no store at all. They do: a unit joins over the
union of its inputs, which is a store.

## Decision

**A unit's in-degree is what bounds its epistemic reach.** What is abolished is an unbounded
*shared* store, not a store. Every wire added is a deliberate widening of what that unit may conclude.

## Evidence

- `Unit.view()` is the union of inputs plus `adds` minus `removes` — demonstrably a store, and
  demonstrably bounded.
- This is what makes negation-as-failure cheap (`0011`): the value is finished, so absence is decidable now.

## Consequences

- In-degree is the analogue of a scope, which is why the wiring policy (`0006`) carries the
  weight that a scope object would carry elsewhere.
- Adding a wire "to make a rule work" is a semantic act, not a plumbing fix.
