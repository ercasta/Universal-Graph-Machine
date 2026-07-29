# `units` — the current system

> **This is the live generation.** `units/` is what is being built. The `ugm` engine (`docs/*.md`,
> `docs/design/`, `docs/reference/`, `docs/attic/`, and the `book/`) is the **previous** generation — still
> running, still documented, still the thing the book teaches, but not what is being designed here. Nothing in
> this directory supersedes anything in those, and the two have separate attics.

**One paragraph.** The system holds a graph of data that persists, and computes over it by assembling a circuit
that **stands**. Values are re-established from the axioms each turn, so conclusions are recomputed rather than
maintained and no retraction machinery is needed. Matching is **graded**; scope is **support** — which
configuration powers a conclusion — rather than a place a fact sits; and everything about a unit (its pattern,
its effects, its wiring) is ordinary graph data, so a rule can write a rule. The front end is a controlled
natural language an LLM translates prose into, and the boundary **transcribes without interpreting** — every
interpretive judgement is a rule inside the loop.

---

## Start here

| | |
|---|---|
| **`STATUS.md`** | what is being worked on right now, phase by phase, and what to pick up next |
| **`model.md`** | the computation model — the single design document. Consolidated 2026-07-28 |
| **`glossary.md`** | plain-language definitions of terms actually agreed on. Check before reusing jargon |

## The model

| doc | what it is | status |
|---|---|---|
| **`model.md`** | The computation model: data, matching, units, the two planes, scope as support, overlays, energy and the burn, the two loops, goals, the boundary. Section numbers are stable and cited from `units/*.py` | **current** — §§1–6, §8's energy/burn and §9's write-back are BUILT (113 tests); §7 and the goal machinery are design |
| `review-01-prior-art.md` | The model located in the literature, graded rediscovery / recombination / novel. Changes no decision | review, 2026-07-27 |

## The CNL and the closed class

The engine's target is a controlled language whose **closed-class composition machinery is sound to unlimited
nesting depth**, carrying opaque domain content through it without ever composing over the content.

| doc | read it for | status |
|---|---|---|
| **`cnl_engine_goal.md`** | the goal stated as one checkable claim; the engine/ruleset responsibility split | north star, 2026-07-28 |
| **`cnl_engine_goal_plan.md`** | the four-phase plan (A spec / B realizability / C composition proof / D termination) | plan; per-phase status in `STATUS.md` |
| **`cnl.md`** | the surface itself — brackets, roles, nesting, transcription. Still current; `forms_cnl.md` constrains it | design, 2026-07-26 |
| **`forms_cnl.md`** | **build from this** — principles `P1`–`P10`, the two decision procedures, the entry format, the test suite, the build order | specification, 2026-07-27 |
| `forms_discourse.md` | ⚠ the **argument**, not the specification — how every position above was reached, including the wrong turns. Supersedes `docs/design/form_inventory.md` (§12 lists what survived) | design + reasoning trail |
| `forms_llm.md` | what may be asked of the translator and what may not; how a depth-bound LLM fails *silently* | design, 2026-07-27 |
| `forms_extra_considerations.md` | a Q&A trail pressure-testing the two above. Not a specification | reasoning trail |
| **`closed_class_inventory.md`** | the **soundness** check — every form's live-measured status from `units/sieve.py` | Phase A, in progress |
| **`agentic_scenario_catalog.md`** | the **completeness** check — ten agentic scenarios, what each needs, coverage verdicts. ⚠ synthetic, not real usage | Phase A working document |
| `composition_grammar.md` | the `BareClaim \| RelationalClaim` sketch, the detachment fix, the nesting induction | design sketch, not implemented, ⚠ predates the `Trigger`-fan-in correction in `computation_units.md`, update pending |
| `computation_units.md` | worked example (gates/wires/overlays), the `Trigger`-fan-in shape for and/or, the one discharge point, two corrections made along the way | design note, 2026-07-29 |

Read `cnl_engine_goal.md` → `cnl_engine_goal_plan.md` first if picking this up cold; the rest hangs off those
two. `closed_class_inventory.md` and `agentic_scenario_catalog.md` are complementary and neither substitutes
for the other.

## Code

| | |
|---|---|
| `units/graph.py` | the graph — nameless nodes, nameless edges, crisp and gradable attributes. Immutable, and that is load-bearing |
| `units/match.py` | matching over topology and attributes, graded |
| `units/band.py` | degree, finite and ordered |
| `units/engine.py` | the one machine — standing units, gates, wires, revive, surge, write-back, the three registers |
| `units/overlay.py` | overlays applied lazily, indexed once per revive; configuration-relative reads; conflicts |
| `units/forms.py`, `units/sieve.py` | the closed-class inventory and the runnable leak probe |
| `units/smt_sieve.py` | the Z3 proofs — base case and inductive step |
| `units/substitution_experiment.py` | `define` + `Identify` as progressive substitution — order-independence, circular-definition safety, the tunnel's wiring cost. `computation_units.md` §5 |
| `tests/units/` | 113 green. `bench_overlay.py` carries the lazy-vs-eager measurements |

## Conventions

- **A document states its own status in its header**, and when it is superseded it **moves to `attic/`** with a
  row in `attic/README.md` saying how it ended. A superseded document does not sit beside a current one with
  only a banner to tell them apart.
- **`model.md`'s section numbers are stable.** They are cited from module docstrings; renumber only with a
  sweep of `units/*.py` and this directory.
- **Terms go in `glossary.md` before they are reused**, in plain language, and only once actually discussed.
- **Measured numbers carry their source.** A performance or coverage claim without a runnable bench or test
  behind it does not belong in a current document.

## `attic/`

The reasoning trail: the original `model.md` and its two revisions, the substrate-inversion lab notebook, the
pre-inversion status page and annotated reference, and 41 decision records of which seven survive. Nothing in
there is authoritative — `attic/README.md` is the final word on each.
