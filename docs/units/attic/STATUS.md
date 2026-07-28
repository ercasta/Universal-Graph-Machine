# `units` — status

*One page. What is being worked on, what changed, what is open, and what needs a decision from you.*

**Last updated:** 2026-07-26 · **Suite:** 174 green (`pytest tests/units`)

> ⚠ **SUPERSEDED BY `docs/units/model.md` (2026-07-26).** The model this page reports progress against has been
> replaced: data is the substrate, computation is a transient circuit, matching is graded, scope is physical
> nesting, and there is no interpretation stage. Everything below describes the *previous* model and is accurate
> only as history. `model.md` §"What carries over from `ugm`" lists what survives and which decisions are
> contradicted.
>
> **Pending your call:** what happens to the existing `units/` code and its 174 tests, most of which test the
> superseded model. Until that is decided this page is not rewritten.

---

## Now

**Selector chains work** (`0035`–`0038`, 21/21 spike, `tests/units/test_selector.py`). The expression *does*
build the network, and the headline is that **the assembler wires the whole chain by itself** — because every
selector atom names its predicate, unlike a wildcard pattern. The expression contributes only ground step nodes
and `<narrows>` links, as data. Nothing gained the power to wire.

All three agreed probes came back clean: end to end resolves and names the right entity; the topology is a
**tree**, not a pipeline; and **belief is invariant under atom order** — only *re-attachment* changes meaning,
because the chain *is* the attachment structure.

**Just settled — the substrate's own ground rule, now written down** (`0039`–`0041`). You asked whether we use
labelled edges. Answer: a `Fact` is stored atomically, so in *layout* it is one — kept deliberately, because it
makes *"is P absent"* a membership test instead of a join, and it ships with its decomposition (`reify`) so it
stays composable. Roles are still positional and predicates are still ordinary nodes.

And the rejected shape had crept back in one place I had not noticed: the terminal **call** node carried
`<verb>`/`<target>` role edges. Now **positional** — a call is just another discourse node with a lexeme and
numbered arguments, measured n-ary on *"wash the car with the sponge"*.

The principle is recorded as **guards yes, kinds no**: when a distinction is needed it becomes a *fact* that
something asserts, never a new kind of thing. The counter-risk you raised is real — seven silent defects here were
exactly that — but it is the *recoverable* failure, and every one of those fixes was one predicate or one atom.

**Next, in order:**

1. **A grammar producing those steps.** It now has a concrete target: ground step nodes, `<narrows>` links, one
   template per syntactic position. This is what the *"a front-end must target a subgraph"* contract (`0020`)
   was pinned for.
2. **SUSPEND.** The terminal call is currently a *request as a fact* and nothing executes it. Building this
   reopens the deferred in-node ISA question (`0021`) on its own stated trigger.
3. The derived-removal decision below, whenever you want to take it.

---

## ⚠ Needs your decision

| # | question | why it is yours |
|---|---|---|
| 1 | **Can a rule remove?** (`decisions/0032`) | It is a paradigm choice, not a feature. A rule is currently a monotone accumulator. Making it a *rewrite* stays functional but gives up monotonicity — which three separate mechanisms rest on (the fixpoint argument, "revision = recompute forward", and the absence of retraction machinery). Nothing is blocked on it today; coreference is sound for matching and silent for counting without it. |

---

## Recently done

| what | outcome |
|---|---|
| **Selector chains** | The expression builds the network, and it **assembles itself**. Gating, failure-location and ambiguity all came free, reusing the reference machinery unchanged — strong evidence that reference and selection are one problem, not two. Found 2 more silent defects. |
| **Discourse reference** | Built as **data** — 7 declared rules, no engine support. A *lexeme* is the licensed bridge (the word is the form set's; the entity is nameless). Inequality dissolved into identity-as-data. Ambiguity and reference failure became detectable rather than silent. |
| **Assembler-completeness sweep** | Found and fixed 2 silent defects after the first one proved the bug class was live. |
| **The computed index** | Wire test moved from *"share a predicate"* to *"can this fact satisfy this atom"*. Quadratic → linear on the shape a minimal form set produces. Found 2 more silent defects, one of which produced a false conclusion. |

**Seven silent defects in the assembler have now been found and fixed, four of which changed an answer.**
Every one was a question asked at the wrong granularity — predicate where an atom was meant, positive where both
polarities were meant, "my chain derives it" where "my chain carries it" was meant, **reachability where *world*
was meant**. This is the standing hazard in this codebase: it does not crash, it degrades quietly.

The two newest are worth knowing because they will bite intake directly:

- **An utterance must enter as a carrier *below* the KB**, never as a second `given`. As a sibling it is a
  separate world, so nothing joins it to anything derived from the KB — and a negated premise over there reports
  **false**, not missing (`0037`).
- **Only a carrier forks a world** (`0038`, amending `0006`). Sibling *rules* over one carrier are the same
  world — which is the normal shape under subset output, and judging it by raw reachability made ordinary
  multi-premise rules unassemblable.

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
