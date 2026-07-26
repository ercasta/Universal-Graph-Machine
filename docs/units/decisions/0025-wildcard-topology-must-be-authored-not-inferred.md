# 0025. Wildcard topology must be authored, not inferred

**Status:** Accepted
**Source:** substrate_inversion.md §30.3; `bench/spike_discourse_reference.py`

## Context

Generic substitution — `?x ?p ?y ∧ ?x same_as ?z ⇒ ?z ?p ?y` — is the natural shape for a coreference
merge, and it is the first genuinely all-variable pattern in the system. The assembler wires it to whatever
produces `same_as` and nothing else, so it substitutes over its own control facts.

## Decision

**A pattern that declines to say what it reads must have its topology authored.** In practice: a
merge carrier over every producer whose facts the pattern needs.

## Evidence

- **This cannot be fixed by a better need computation.** The wildcard atom is satisfied by *any*
  fact, including the rule's own control facts, so *"is this atom unmet?"* is vacuously false. The atom is
  formally satisfied — by the wrong facts. No test at that granularity could notice.
- **The authored merge must hold every premise in one value.** A rule's output does not carry its input
  (`0008`), so a merge over the discourse and the decision but not the symmetry substitutes one way only. For the
  same reason the wildcard rule cannot self-unroll: hop *n+1* reads hop *n*'s conclusions, which contain no
  discourse. Measured.
- Two pre-existing defects in the bypass guard surfaced here, both from the same root — **subset output
  invalidates every "my chain has it" heuristic**:
  - `gated` treated a unit as a bypass of **itself**. An intermediate rule never carries an upstream unit's
    predicate, so a direct wire from that unit is the only route. A template whose negated premise was produced
    two units back was denied its own producer and **its negation went vacuously true.**
  - `restores_a_drop` counted facts a carrier **never received** as facts it dropped. A drop is what *arrived*
    and did not leave.

## Consequences

- This is not a defect but a price: it is what declining to say what you read costs. The same
  shape was already accepted for procedures, where intake manufactures the dependency.
- It is the first place where wiring is genuinely not inferable, which makes it the natural hook for
  *expression-derived topology*: if the syntax says how selectors nest, the syntax can author the wiring.
