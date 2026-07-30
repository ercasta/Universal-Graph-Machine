# `units` — the current system

> **Foundation decision, 2026-07-30 (see `arc_recap.md`'s current Act and
> `attic/handoff_ugm_reversion_evaluation.md`): going forward, new work builds on `ugm/`'s substrate
> (`ugm/attrgraph.py`), ISA (`ugm/machine.py`), and rule-lowering — NOT a third from-scratch substrate.**
> `units/`'s own substrate (`units/engine.py`) and every mechanism validated on it (scope-as-support, the
> tunnel resolution, "a rule writes a rule," the closed-class algebra) remain the **findings this project
> stands on** — they are what gets ported onto `ugm/`'s substrate as an outer-loop metaprocedure replacing
> `ugm/lowering.run_bank`'s blind whole-graph fixpoint driver, not a rival implementation. This directory's
> documents (`model.md`, the CNL boundary, the probes) stay the authoritative record of *what was found*;
> where the code that embodies it lives is what changed.

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
| **`arc_recap.md`** | the whole arc, narrated — where this came from and where it's going, including the 2026-07-30 foundation decision. Read this **first** if you're picking this up cold |
| **`attic/handoff_ugm_reversion_evaluation.md`** | RESOLVED — the audit and reasoning behind the foundation decision above. Read if you need the "why," not just the "what" |
| **`metaprocedure_model.md`** | the computation model's goal-driven/metaprocedure/central-gate shape, precisely mapped onto `ugm/`'s existing mechanisms (`dispatch.py`, `mode_calls.py`, `corpus/procedure.cnl`, `reactive.py`, `machine.py`'s `ControlMachine`) — with two concrete gaps named and two probes proposed. Read after the foundation decision, before picking up outer-loop-metaprocedure work |
| **`the_data_model.md`** | ⭐ **plain-language prose**: what a goal, a plan, and a hypothesis actually *are* as graph structure, what the ~15 generic operations on them do, why they nest without limit, and the one missing node kind (a metarule *application*) that blocks metarule selection and learned metaprocedures. Read this to understand the data model; read its companion below to verify it |
| **`graph_data_model.md`** | the same content as signature tables — the concept/operation vocabulary, a mechanical closure check for unbounded-depth composition, three named gaps, four probes, and the graph-database thought experiment as a falsification bar. Read after `metaprocedure_model.md` |
| **`handoff_overlay_band_composition.md`** | ⚠ **open handoff, 2026-07-30**: does likeliness/band composition (`machine.py`'s `OVERLAY_BAND`) need privileged ISA support, or is it ordinary declared rules like everything else this arc found? Read this if picking up the possibilistic/band layer |
| **`STATUS.md`** | what is being worked on right now, and what to pick up next, in more granular detail than the recap's own §5 |
| **`model.md`** | the computation model — the single design document |
| **`glossary.md`** | plain-language definitions of terms actually agreed on. Check before reusing jargon |

---

## The model and surface

| doc | what it is | status |
|---|---|---|
| **`model.md`** | The computation model: data, matching, units, the two planes, scope as support, overlays, energy and the burn, the two loops, goals, the boundary | current |
| **`cnl.md`** | the CNL surface itself — brackets, roles, nesting, transcription | current; `forms_cnl.md` constrains it |
| `goal_machinery.md` | The goal/subgoal lineage design `model.md` §8 points to — interning, outcome, decay, additive rewriting, the turn/axiom-lifecycle mechanism | design, settled |
| `computation_units.md` | Worked example (gates/wires/overlays): the tunnel, precisely (a computation unit's output doesn't persist; a unit sees only its own gates); the `Trigger`-fan-in shape for and/or | design note |
| `review-01-prior-art.md` | The model located in the literature (proof theory, dynamic/update semantics, linear logic, LF/Twelf), graded rediscovery / recombination / novel. Changes no decision, still accurate | reference, evergreen |

## Forms and the closed class — the original inventory (07-27/28)

The engine's target: a controlled language whose **closed-class composition machinery is sound to unlimited
nesting depth**, carrying opaque domain content through it without ever composing over the content. This is
where the Leibniz/harmony reasoning trail lives — full narrative in `arc_recap.md` §2.

| doc | read it for | status |
|---|---|---|
| **`cnl_engine_goal.md`** | the goal stated as one checkable claim; the engine/ruleset responsibility split | north star |
| **`forms_cnl.md`** | **build from this** — principles `P1`–`P10`, the two decision procedures, the entry format, the test suite, the build order | specification |
| `forms_discourse.md` | ⚠ the **argument**, not the specification — how every position above was reached, including the wrong turns (the Leibniz/350-years question, harmony, CONTENT×FORCE×LEVEL). Supersedes `docs/design/form_inventory.md` (§12 lists what survived) | design + reasoning trail |
| `forms_llm.md` | what may be asked of the translator and what may not; how a depth-bound LLM fails *silently* | design |

## Verification

The soundness/completeness checks for the closed-class inventory. All three were revised 2026-07-30 against
`closed_class_rechallenged.md` (below) — the rows affected by the rechallenge (causation, identity/merge,
quantification's cursor case) are updated in place, not merely flagged; everything else (the sieve
measurements, the ask/command finding, the scenario coverage verdicts unrelated to the rechallenge) was
already accurate and is unchanged.

| doc | read it for |
|---|---|
| `closed_class_inventory.md` | the soundness check — every form's live-measured status from `units/sieve.py` |
| `agentic_scenario_catalog.md` | the completeness check — ten agentic scenarios, what each needs, coverage verdicts. ⚠ synthetic, not real usage |
| `composition_grammar.md` | the `BareClaim \| RelationalClaim` grammar sketch for `conditional` specifically — the one genuinely relational, closed-class form this grammar was ever for; the detachment fix; the nesting induction |

## Planning, the middle tier, and the closed class rechallenged (07-30 — the current frontier)

The most recent, most active thread. Full narrative and how it connects to everything above:
**`arc_recap.md` §3–§4.**

| doc | read it for | status |
|---|---|---|
| **`closed_class_rechallenged.md`** | the sharp version: is the closed class itself smaller than thought? 5 relational forms probed against the real engine — 4 confirmed pure sugar (zero engine change), transitivity confirmed but needed a real, small engine extension. The definitional-coexistence conflict-detection risk, also checked | design note, probing complete |
| `planning_meta_concepts_arc.md` | the full prose story this was extracted from — exploration vs. execution, the middle tier, Zave's telecom precedent, the goal/procedure/question/prohibition unification | design note, prose |
| `cnl_engine_goal_plan.md` | the original four-phase plan (A spec / B realizability / C composition proof / D termination) and the day-by-day goal/subgoal build log (§7a–§7h) that `goal_machinery.md` and the probe scripts above were extracted from. Heavily cross-referenced from code (`units/engine.py`, `units/goal_experiment.py`, others) — still the canonical pointer for those citations even though its content is now mostly digested elsewhere | historical log; per-phase status lives in `STATUS.md` now |

## The CNL boundary — first real slice (07-30, current work)

Where `cnl.md`/`forms_cnl.md` stopped being 100% design. `units/cnl.py` is the first parser turning actual
CNL text into graph data; everything downstream of it reuses meta-rules already checked in isolation
(`force_probe_experiment.py`, `identity_merge_probe_experiment.py`) rather than inventing new ones.

| module | what it does | grew out of |
|---|---|---|
| `units/cnl.py` | the parser: `[head \| role: filler ...]`, nesting = containment, `force:`/`level:` marked as crisp attributes (a real contradiction between `cnl.md` and `forms_cnl.md`/the checked probes, found and fixed 2026-07-30 — `cnl.md` §2/§4/§5), everything else as relational role nodes |
| `units/goal_rules.py` | `ask_to_goal`/`command_to_goal`/`goal_achieved`/`goal_diverged`, promoted out of `force_probe_experiment.py` into a shared, importable module once something real got built on top of the finding |
| `units/author_rules.py` | routes `force="author"` — scoped to fact-authoring only; compiling an authored `when:`/`then:` shape into a genuinely new `StandingUnit` ("a rule writes a rule") is deferred, named explicitly rather than built ahead of a need |
| `units/prohibition_rules.py` | "don't do anything dangerous," for real: a declared `dangerous` fact propagates into `forbidden` via one generic rule; a separate, independent watcher vetoes a command's goal from ever executing if its target is forbidden |
| `units/identity_rules.py` | cross-statement identity, first cut: two bare-word fillers with the same name merge. Found necessary, not hypothetical — the danger-detection scenario's two utterances mention "production_database" separately, and `cnl.py` mints a fresh node per mention unless something merges them |

**Two real bugs surfaced building this, both instructive, both fixed:** calling a rule-constructor function
twice (once to `add`, once to `wire`) silently builds two disconnected rule-object sets — no exception, just
zero results; and matching a CNL-parsed relational role (`target:`) as if it were a crisp attribute passes
against hand-built test graphs that share the same wrong assumption, while silently never matching real
parsed text at all. Both are recorded in the relevant module's own docstring, not smoothed over.

## Code

| | |
|---|---|
| `units/graph.py` | the graph — nameless nodes, nameless edges, crisp and gradable attributes. Immutable, and that is load-bearing |
| `units/match.py` | matching over topology and attributes, graded; `AttrVar` for value-equality without knowing the value in advance |
| `units/band.py` | degree, finite and ordered |
| `units/engine.py` | the one machine — standing units, gates, wires, revive, surge, write-back, the three registers |
| `units/overlay.py` | overlays applied lazily, indexed once per revive; configuration-relative reads; conflicts (deduped by **value**, not source) |
| `units/forms.py`, `units/sieve.py` | the closed-class inventory and the runnable leak probe |
| `units/smt_sieve.py` | the Z3 proofs — base case and inductive step |
| `units/substitution_experiment.py` | `define` + `Identify` as progressive substitution |
| `units/goal_experiment.py`, `system1_experiment.py`, `quantification_cursor_experiment.py`, `goal_decomposition_experiment.py`, `nac_verification_experiment.py` | the goal-machinery arc's worked examples |
| `units/force_probe_experiment.py`, `level_probe_experiment.py`, `identity_merge_probe_experiment.py`, `transitivity_probe_experiment.py`, `definitional_coexistence_experiment.py` | the closed-class-rechallenged arc's five probes |
| `units/cnl.py`, `goal_rules.py`, `author_rules.py`, `prohibition_rules.py`, `identity_rules.py` | the CNL boundary's first real slice — see the section above |
| `units/structural_choice_experiment.py` | structural planning as live, real commit/detect/retract/retry — no supposition, no Python. Led directly to the tunnel/metaprocedure resolution in `handoff_ugm_reversion_evaluation.md` §2 |
| `tests/units/` | 144 green (the structural-choice probe has its own `report()`-style checks, not yet ported to pytest) |

## Conventions

- **A document states its own status in its header**, and when it is superseded it **moves to `attic/`** with a
  row in `attic/README.md` saying how it ended. A superseded document does not sit beside a current one with
  only a banner to tell them apart.
- **A document that's still the right document, but wrong in specific places, gets those places fixed in
  place — not a blanket "stale" banner at the top.** A banner that just says "don't trust this, revision
  queued" is worse than either fixing it or filing it: it's confusing to read against with no idea which
  parts are actually wrong, and it invites the fix to be deferred indefinitely. Find the exact rows/claims
  a new finding overturns, correct them precisely, and move on. This directory carries no blanket staleness
  markers as of 2026-07-30 for exactly this reason.
- **`model.md`'s section numbers are stable.** They are cited from module docstrings; renumber only with a
  sweep of `units/*.py` and this directory.
- **Terms go in `glossary.md` before they are reused**, in plain language, and only once actually discussed.
- **Measured numbers carry their source.** A performance or coverage claim without a runnable bench or test
  behind it does not belong in a current document.
- **`arc_recap.md`'s §5 ("Where we are now") is the living pointer to what's next** — update it, not this
  file's structure, as work continues. This file's job is the map; that one's is the current position.

## `attic/`

The reasoning trail: the original `model.md` and its two revisions, the substrate-inversion lab notebook, the
pre-inversion status page and annotated reference, 41 decision records of which seven survive, and two
working documents (`forms_extra_considerations.md`, `planning_example.md`) whose ideas are now fully
absorbed into current documents. Nothing in there is authoritative — `attic/README.md` is the final word on
each.
