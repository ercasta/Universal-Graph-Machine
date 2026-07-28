# 0029. A refusal is a fact: the assembler's decisions are recorded

**Status — current (2026-07-28): HISTORICAL.** predates the substrate inversion (2026-07-26). Not contradicted by name in `../../model.md`, and not carried forward as current either — read it as context, not as a decision in force.

**Status — as recorded:** Accepted
**Source:** substrate_inversion.md §27; `units/journal.py`

## Context

A dynamically-wired system cannot be statically checked, so introspection is all there is — and the
assembler, the part doing the dynamic wiring, was entirely outside it. The user's framing was a
*network-configuration network*: routing decisions should be first-class and inspectable.

## Decision

**Record every assembly decision as facts** — `<spawned>`, `<wire_from>`/`<wire_to>`/`<wire_kind>`,
`<declined>` with a reason, `<unused>` for a template accepted and never wired. **Observable, never writable**
(`0010`).

## Evidence

- **The failure mode it closes is the one that matters for intake:** a form can be accepted, become a
  well-formed template, and **never be wired — silently.** `wellformed()` stays clean, the budget is untouched,
  nothing says so. That is *"partial intake systematically drops exceptions"* one layer below the parser. Its
  mirror — a spurious instance that can never fire — was equally silent.
- Three things building it found:
  - **The journal must not be a unit.** It was one briefly and polluted every unit count, every `wellformed`
    walk and every upstream walk. The assembler's record is not part of the computation it records.
  - **A wire's identity must be a function of its endpoints**, and an already-wired producer must be skipped
    *silently* — logging it made the journal grow on every re-run of a quiescent net, and the journal rides a
    trace wire, so a growing journal destroys the fixpoint.
  - **`<unused>` is a state claim, not a firing, so it must be withdrawn.** The watcher flagged *itself*,
    because at the pass where orphans were computed it had no instance yet.
- Gating and rewiring are different acts: the biological framing that motivated this assumes *fixed* topology,
  which is a constraint we do not have and whose absence is the whole advantage. Only the inspectability was
  imported.

## Consequences

- The journal is the validation gate for the computed index (`0022`): what was proposed versus
  what actually fired.
- *"What did you not consider?"* has an answer, where before it had none.
