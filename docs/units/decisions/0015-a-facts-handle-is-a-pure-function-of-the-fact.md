# 0015. A fact's handle is a pure function of the fact

**Status:** Accepted
**Source:** substrate_inversion.md §25.3

## Context

Reification — talking *about* a fact — needs a node to hang annotations on. The obvious design is
one handle per fact per value, with the trace looking up whatever the object wire already minted. That requires
coordination between two wires that deliberately share no state.

## Decision

**The handle is arithmetic on the three node identities.** Any two reifications of the same fact,
anywhere, in any value, on any wire, produce the same node — no lookup, no registry, no coordination.

## Evidence

- It is a **function, not a table**, so `0005`'s one-global-structure rule is untouched.
- It is derived from **identity, never from name**: two entities both called `mary` yield different handles
  because their ids differ. Content-derived structural identity, not a label.
- Four consequences, and only the first was the goal: a degree hangs off the same node a firing points at;
  degree inheritance becomes a **rule**; reification is idempotent, retiring a class of fixpoint bugs rather
  than guarding them; and two derivations of one conclusion converge on one handle, so *"P has two
  justifications"* is represented natively.

## Consequences

- Two private key-derivation schemes became dead weight and were removed.
- Intake must not invent a third reification scheme.
