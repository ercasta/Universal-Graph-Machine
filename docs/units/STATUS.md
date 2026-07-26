# `units` — status

*One page. What is being worked on, what changed, what is open, and what needs a decision from you.*

**Last updated:** 2026-07-26 · **Suite:** 158 green (`pytest tests/units`)

---

## Now

Documentation restructure, then the **selector-chain spike**: does the *expression* build the network?

> *"wash the car that is parked at the third floor of the garage near the movie theater"*
> → a tree of selector units, each narrowing the previous one's result, terminating in a call to `wash`.

Agreed scope for that spike — three things, written to break:

1. **the full sentence end to end** — does it resolve, does each selector gate, do ambiguity and reference
   failure surface at each hop;
2. **branching, not just chains** — *"the car and the truck that are parked there"*, to confirm the topology
   is a tree/DAG before any linear assumption gets baked in;
3. **surface-sensitivity of belief** — deliberately try to make two differently-nested expressions with the
   same meaning produce *different beliefs*. The expression may determine the selector topology; it must not
   determine what is believed.

---

## ⚠ Needs your decision

| # | question | why it is yours |
|---|---|---|
| 1 | **Can a rule remove?** (`decisions/0032`) | It is a paradigm choice, not a feature. A rule is currently a monotone accumulator. Making it a *rewrite* stays functional but gives up monotonicity — which three separate mechanisms rest on (the fixpoint argument, "revision = recompute forward", and the absence of retraction machinery). Nothing is blocked on it today; coreference is sound for matching and silent for counting without it. |

---

## Recently done

| what | outcome |
|---|---|
| **Discourse reference** | Built as **data** — 7 declared rules, no engine support. A *lexeme* is the licensed bridge (the word is the form set's; the entity is nameless). Inequality dissolved into identity-as-data. Ambiguity and reference failure became detectable rather than silent. |
| **Assembler-completeness sweep** | Found and fixed 2 silent defects after the first one proved the bug class was live. |
| **The computed index** | Wire test moved from *"share a predicate"* to *"can this fact satisfy this atom"*. Quadratic → linear on the shape a minimal form set produces. Found 2 more silent defects, one of which produced a false conclusion. |

**Five silent defects in the assembler have now been found and fixed, three of which changed an answer.**
Every one was a question asked at the wrong granularity — predicate where an atom was meant, positive where
both polarities were meant, "my chain derives it" where "my chain carries it" was meant. This is the standing
hazard in this codebase: it does not crash, it degrades quietly.

---

## Open, not blocking

- **Wildcard cost.** A pattern that declines to say what it reads (`?x ?p ?y`) spawns redundant instances and
  cannot be restricted by any static analysis. Diagnosed in advance by `ComputedIndex.wildcards()`.
- **Trace-wire fan-out.** Every unit emits every firing predicate, so a trace consumer is wired broadly. A
  content-level restriction is available and unbuilt; deferred because stratification caps trace consumers at
  one level, making the cost linear rather than compounding.
- **Fan-out scale unmeasured.** Chains and wide nets are linear; sibling-hypothesis fan-out has never been
  measured, and it is the shape that could still blow up.
- **Not built:** force, a sink, suspend/procedures, a grammar. Each has a decided shape.

---

## How to read this project

| you want | read |
|---|---|
| what the system is and how to use it | `docs/units/reference.md` |
| why a decision was taken, and the evidence | `docs/units/decisions/` (see its `README.md`) |
| what I am doing right now | this file |
| the original reasoning trail | `docs/design/substrate_inversion.md` — history, no longer maintained |
