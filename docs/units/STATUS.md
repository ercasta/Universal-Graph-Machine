# `units` — status

**One page, last updated 2026-07-29 (goal-experiment pass). What happened, what document to read for what, what's actually done vs.
designed, and what to pick up next.** This is the current, active thread. The index is `README.md`; the model
is `model.md`; the previous status page (pre-inversion, 174 tests, superseded 2026-07-26) is
`attic/STATUS.md`.

---

## The arc, in one paragraph

Started from a question about whether the closed class *composes* — pressure-tested `forms_discourse.md` and
`forms_llm.md` until "compositional fidelity vs. business correctness" became a clean split, which turned into a
concrete engineering goal (`cnl_engine_goal.md`), a phased plan (`cnl_engine_goal_plan.md`), a consolidated
inventory with live sieve numbers (`closed_class_inventory.md`), a completeness check anchored in real agentic
use cases (`agentic_scenario_catalog.md`), a symbolic proof tool (`units/smt_sieve.py`), a composition grammar
sketch (`composition_grammar.md`), an actual unbounded-depth safety proof (induction, not sampling), and — the
first time any of this landed in running code — a real, verified fix for the `conditional` detachment leak. One
big thread (SUPPOSE's discharge) was deliberately shelved along the way for lack of a real use case.

---

## Document map — what to read for what

| doc | read it for |
|---|---|
| `cnl_engine_goal.md` | the goal statement, the engine/ruleset responsibility split, the three ingredients |
| `cnl_engine_goal_plan.md` | the four-phase plan (A spec / B realizability / C composition proof / D termination); current status per phase |
| `closed_class_inventory.md` | the soundness-side check — every form's live-measured status, from `sieve.py` |
| `agentic_scenario_catalog.md` | the completeness-side check — ten real scenarios, what each needs, coverage verdicts |
| `composition_grammar.md` | the `BareClaim \| RelationalClaim` grammar sketch, the detachment fix's design, the nesting induction. ⚠ its `Conjunction`/`Disjunction`/`Negation`-as-siblings shape is superseded, update pending |
| `computation_units.md` | the `Trigger`-fan-in correction: and/or live at the antecedent position feeding one shared `then`, never as free-standing claims with independent consequents; the one discharge point; worked example; §5's `define`+`Identify` progressive-substitution experiment, tested against the real engine |
| `glossary.md` | plain-language definitions of every term actually agreed on this session — check before reusing jargon |
| `units/smt_sieve.py` | the runnable Z3 proofs (base case, inductive step) |
| `units/forms.py`, `units/sieve.py` | where the detachment fix actually landed in code |
| `units/goal_experiment.py` | goal lineage/interning, outcome-as-fact, abandon-and-decay, and additive rewriting — all checked against the real engine; findings in `cnl_engine_goal_plan.md` §7e |

Read `cnl_engine_goal.md` → `cnl_engine_goal_plan.md` first if picking this back up cold; the other docs hang
off those two.

---

## Status by phase

| phase | state |
|---|---|
| **A — spec the inventory** | in progress. `closed_class_inventory.md` has live numbers; open items: `past`/`evidential`/`mirative` are singleton slots (need a competing form to test independence); `quantification`/`causation`/`identity` not yet formalized at all |
| **B — realizability gate** | SUPPOSE's discharge **shelved** (no scenario needs it — see below). Nested-conditional evaluation needs a "gated" wiring discipline, proven abstractly, **not yet built in the real engine** |
| **C — composition proof** | `degree ∘ negation`, `ask`/`language` leaks: proven fixed via guarding (SMT, `unsat`). **`conditional` detachment: fixed in running code** (`Form.excludes_defaults`, `units/forms.py`/`sieve.py` — `still_leaking` empty, only the deliberately-requested `positive ∘ unmet` still leaks, correctly). n≥3 nesting: closed as a design requirement (induction proof), conditional on the gated wiring actually being built. **And/or: corrected to a `Trigger`-fan-in shape** (`computation_units.md`) — sound by construction, no discharge needed, provided `composition_grammar.md`'s old siblings shape is updated to match |
| **D — termination/honesty** | **untouched.** The surge detector still can't distinguish convergent recursion from a runaway cycle (`forms_discourse.md` §10.3) — this is the literal mechanism behind scenario 5 (honest exhaustion reporting), which is currently just broken |

---

## Shelved, on record

**SUPPOSE's discharge.** Diagnosed precisely (`powering()`'s wire-walk taints any unit downstream of a
supposition regardless of what it mints, because units have no ambient graph access — only their gates,
`engine.py` invariant 3). Shelved because none of the ten scenarios in `agentic_scenario_catalog.md` need the
agent to *derive* a new rule from a hypothesis — all ten only *apply* already-authored rules. Revives if a real
"agent learns its own rules from experience" scenario gets added to the catalog and earns its place the way the
other ten did.

---

## What's proven vs. what's actually built — don't conflate these

- **Proven, abstractly, in `units/smt_sieve.py`:** the base case (a bare claim alone is safe under guarding) and
  the inductive step (nested conditionals stay safe at unbounded depth, *if* wired "gated" not "naive").
- **Built and verified, in real code:** the detachment leak's fix (`Form.excludes_defaults`).
- **Not built:** an actual nested `Claim` structure in `units/` — there is currently no way to represent "if A,
  then: if B then C" as real graph data. The induction proof is real, but nothing has tested it against the
  running engine yet, because the structure it's a proof *about* doesn't exist in code.

---

## Recommended next step

**Updated 2026-07-29 — design doc written (`goal_machinery.md`), now moving to the first System 1 prototype.**
`units/goal_experiment.py` (four checks, all green) found the real shape, but the first write-up over-claimed
two findings as engine requirements when they were self-inflicted extra machinery — caught by re-reading the
explanation rather than the code, corrected same-session (`cnl_engine_goal_plan.md` §7e has the full
correction). The settled version: goal lineage/interning, outcome-as-fact, and decay all work with the five
existing effect kinds and no new gate concept, **provided** a turn is understood as *"same `Network`, same
standing units, axiom `.held` lifecycle managed between turns"* rather than anything rebuilt — a mechanism that
was already precedented three times in `test_engine.py` but never stated in one place until `goal_machinery.md`.
Additive rewriting re-hit `computation_units.md` §5's tunnel finding from the mint side, confirmed recurring
rather than one-off.

**Updated 2026-07-29 (later same day) — first System 1 prototype built, `units/system1_experiment.py`.** Three
checks, all green: RETRIEVE as a Python-level outer-loop function (attention = BFS from a seed, resemblance =
attribute-key overlap, wiring proposed by score) — no new engine mechanism, wiring is still `Network.wire()`.
Confirmed "allowed to be wrong" concretely (a candidate can be wired on crude resemblance and then simply fail
to fire, the wasted-step cost §7 names, never a wrong answer) and found a real asymmetry: the outer driver has
no tunnel of its own (unlike a `StandingUnit`, which only sees its gates), so avoiding a duplicate wire is a
plain Python check on `n.wires` — none of `goal_machinery.md` §3's axiom-lifecycle discipline was needed at
this layer. **Does not revise `goal_machinery.md`** — the two findings are consistent (the tunnel is a unit
property specifically, confirmed by finding a place it doesn't apply), so the accepted risk from choosing this
order didn't materialize this round. Full detail: `cnl_engine_goal_plan.md` §7f.

**Updated 2026-07-29 (later same day) — two follow-ups landed, `cnl_engine_goal_plan.md` §7g/§7h.**
`system1_experiment.py` gained fan-out (wire every candidate that clears `theta`, never unwire one for failing
to fire — settled as the answer to "how does retrieval avoid needing retraction") and one reused reflective
`Cell` (mutate `.held` in place across calls instead of minting a fresh axiom each time — the naive version
measurably grew `self.axioms`/wire-count by 1 every call, because `Network.axiom()` also writes its own node
into the graph; fixed, confirmed flat). Then `units/quantification_cursor_experiment.py` built and closed
`closed_class_inventory.md` §8 case (c) — the cursor across turns for member-by-member checking, using exactly
the axiom-lifecycle discipline plus a **new, sharper** finding: a reused reflective snapshot alone lags one
turn behind a sibling rule's *own* same-turn conclusion (refreshing `.held` happens *before* `revive()` runs,
so it can never contain what that same `revive()` is about to produce) — fixed with a second gate wired
directly to the sibling's `Cell`, not a bigger snapshot. `goal_machinery.md` §4 now has this as a precise
amendment. All three experiment scripts (`goal_experiment.py`, `system1_experiment.py`,
`quantification_cursor_experiment.py`) plus 114 tests are green.

**Not yet decided: next step after this.** Candidates, not yet chosen between: extend System 1 past a toy
resemblance metric (graded/banded scoring via `band.py`, attention decay); a subgoal with its own satisfaction
condition (`goal_machinery.md` §7's remaining open item); or address one of the lower-priority items below.

**Updated 2026-07-30 — `planning_meta_concepts_arc.md` + `closed_class_rechallenged.md`: force, level,
identity/merge, and transitivity all probed and confirmed.** `units/force_probe_experiment.py` (3 green),
`units/level_probe_experiment.py` (3 green), and `units/identity_merge_probe_experiment.py` (4 green) each
check that a relational form resolves to a declared-data slice plus one generic meta-rule, never a new
engine primitive — identity's version: `Merge` (already built) plus one rule quantifying over both concept
kind and key value via two `AttrVar`s, gated so an incidental shared attribute never triggers a merge.
`goal/procedure/question/prohibition` unification also confirmed
(`units/meta_concept_unification_experiment.py`, 3 green).

**⭐ Transitivity is the one exception to "pure sugar," and it's the reason probing beats pattern-matching.**
`units/transitivity_probe_experiment.py` (4 green) confirms predicate-variable *reading* transfers for free
via `AttrVar`, but predicate-variable *writing* genuinely needed a small engine extension: `Attribute.value`
and `Link.role` in `units/engine.py` now accept an already-bound `AttrVar`, symmetric to how node fillers
already read match bindings — pinned separately in `tests/units/test_engine.py`
(`test_attribute_value_can_read_a_bound_attrvar`, `test_link_role_can_read_a_bound_attrvar`).

**Updated 2026-07-30 (same day) — the definitional-coexistence risk is checked, closing out every item on
`closed_class_rechallenged.md` §9's probe list.** `units/definitional_coexistence_experiment.py` (3 green):
two independently-authored rules reacting to two coexisting forms of the same additively-rewritten fact
(`paul.age==42` directly, and the reified `age_claim.value==42` reached through `about`) and concluding the
identical value on the identical slot do NOT register as a conflict — `overlay.py`'s `Overlays.conflicts()`
dedupes by value, not by source, confirmed against running code rather than only inferred from reading it.
The converse holds too: a genuinely different conclusion on the same slot still surfaces as a real
`Conflict`. Standalone probe script, like the other four in this arc; the pytest suite stays at 116 green,
unaffected.

**Everything named in `planning_meta_concepts_arc.md` and `closed_class_rechallenged.md` is now checked.**
`closed_class_inventory.md`, `composition_grammar.md`, and `agentic_scenario_catalog.md` were revised to
match (2026-07-30 hygiene pass), and `docs/units/arc_recap.md` now carries the whole arc's narrative plus a
living "where we are now" section — read that first when picking this up cold.

**Updated 2026-07-30 (same day) — the CNL boundary's first real slice, built and growing.** Full detail:
`README.md`'s "The CNL boundary" section. `units/cnl.py` is the first actual CNL parser (everything before
this was 100% design); `units/goal_rules.py`, `author_rules.py`, `prohibition_rules.py`, `identity_rules.py`
are real, reusable modules, not throwaway probes — `force_probe_experiment.py` now imports its rules from
`goal_rules.py` rather than defining them twice. End to end, checked against the real engine: a natural-
language prompt, translated by hand into CNL text, parsed, and run — "is X known" and "do X" utterances
correctly mint and resolve goals; "the production database is dangerous" authored as a KB fact correctly
vetoes a later "delete the production database" command, regardless of authoring order, via two
independently-composing generic rules (`dangerous ⇒ forbidden`, `forbidden` vetoes `executed`) neither of
which knows the other exists. 144 tests green.

**Two real bugs found and fixed while building this — worth remembering, not just fixing quietly:** (1)
calling a rule-constructor function twice (once per `add`/`wire` loop) silently builds two disconnected
rule-object sets, failing with zero results and no exception; (2) matching a CNL-parsed relational role
(`target:`) as a crisp attribute passes against hand-built test graphs sharing the same wrong assumption,
while silently never matching real parsed text — the parser was right, the rules were wrong, and only
running *parsed* CNL rather than hand-built graphs surfaced it.

**Deliberately deferred, named rather than built ahead of a need:** compiling an authored `when:`/`then:`
shape into a genuinely new `StandingUnit` ("a rule writes a rule," `author_rules.py`'s docstring) — a real
compiler task, bigger than this slice; real coreference beyond lexically-identical bare words
(`identity_rules.py`'s docstring); a real action-dispatch/tool-call mechanism (`prohibition_rules.py`'s
`executed` is a stand-in, not a real `<call>`); CNL refusal and role-inventory validation.

**Also still open, from before, not blocking any of the above:** return to designing the causal-fact→plan
and norm→requirement→satisfies meta-rule chain — the piece of planning-support work that started the whole
closed-class-rechallenge detour, now buildable on top of a real CNL boundary instead of hand-built graphs.

**Updated 2026-07-30 (same day) — structural planning probed, and it forced a real architectural
resolution about the tunnel.** `units/structural_choice_experiment.py` (3 checks green): a genuine choice
among KB-declared candidates, resolved by committing to the real graph, honestly detecting a conflict
against already-declared data, retracting, and trying the next declared alternative — zero Python, zero
supposition. This led to a debate about whether tunnels/computation-units are needed at all, resolved (not
yet built) via: a meta-rule can mint a *second, supposition-wired instance* of a declared business rule
(reusing "a rule writes a rule," already proven possible) to explore hypothetically, fire-and-forget;
confirming a hypothesis needs no crossing at all, because confirming just means the antecedent becomes
really true, at which point a separate, always-real-wired instance of the same rule fires naturally.

**RESOLVED 2026-07-30 (same day) — the foundation question.** Neither revert wholesale nor stay on
`units/`'s substrate: `ugm/production_rule.py`'s `Rule` is already data and `ugm/machine.py` is already a
real register-based ISA over a genuine substrate (`attrgraph.py`) — `ugm/`'s actual weakness is
`ugm/lowering.run_bank`/`run_to_fixpoint` blindly forward-chaining every rule bank to fixpoint over the
whole graph, every pass. **Decision: keep `ugm/`'s substrate + ISA + rule-lowering; replace `run_bank`'s
blind driver with an outer-loop metaprocedure** (the "a rule writes a rule" mechanism from §2 of
`attic/handoff_ugm_reversion_evaluation.md`, now hosted on `ugm/`'s substrate instead of a new one).

**Next, concretely, in priority order:**
1. Read `ugm/suppose.py`, `scope_crossing.py`, `scope_kinds.py` against the §2 tunnel/metaprocedure
   resolution: does `ugm/`'s existing supposition machinery support "wire a minted rule-instance to a
   scope's cell," or does that need building fresh on `ugm/`'s substrate?
2. Probe a first outer-loop metaprocedure directly on `ugm/`: a meta-rule reading one declared
   `production_rule.Rule`'s own `lhs`/`rhs` and minting a second live instance of it, targeted rather than
   run via `run_bank` over everything.
3. Check `ugm/focus.py`'s demand-derived attention register as the seed for "which region" the
   metaprocedure applies to.
4. Decide whether `units/`'s `revision-01` argument ("circuits stand, no retraction needed") transfers to
   this metaprocedure-on-`ugm` model, or whether `ugm/retraction.py`/`reconsider.py` are still needed there.
5. ~~Triage `ugm/`'s 79 pre-existing test failures~~ **DONE 2026-07-30.** Also resolved: which branch to
   start from. `ugm`'s `main` is 706/706 green but PREDATES `scope_tree.py`/`scope_kinds.py`/
   `scope_crossing.py`/`reactive.py`/`flare.py` and the expanded CNL grammar entirely (they don't exist on
   `main`) — starting there means rebuilding all of it. The `grammar` branch (main + 111 commits) has these
   modules, with real dedicated test coverage, and its 79 failures (of 1127) are almost entirely
   concentrated in the possibilistic/band/hedge layer (`possibility.py`, `possibility_band/rules/cnl/guess`,
   hedge-related grammar intake, `test_world.py`/`test_epistemic_closure.py`'s band assertions) plus the
   *temporal* scope-variable engine (`test_scope_variable_rules/cnl.py` — a different mechanism from the
   focus/attention scope machinery). `test_isa_focus.py`, `test_scope_kinds.py`, `test_reactive.py`,
   `test_flare.py` are ALL GREEN; `test_scope_crossing.py` has one failure, a known pre-existing interning
   gap (a name resolving to multiple nodes), not a design flaw. **Decision: build forward on `grammar`'s
   tip as-is; treat the 79 failures as debt confined to the band/hedge layer, which `units/band.py` already
   superseded by finding — do not spend time fixing them before starting the metaprocedure work.**

**Still open, lower priority, not blocking the above:**
- **Give `COMMAND` real semantics** (`closed_class_inventory.md` §9) — small, concrete, quick: tests the
  `ask = command(report(P))` reduction hypothesis rather than leaving it argued-but-unverified.
- Closing out `past`/`evidential`/`mirative`'s open-hypothesis status (needs a competing form each before
  `slots()` can say anything); building the real nested-`Claim` structure to test the induction against running
  code rather than only against `smt_sieve.py`'s abstract model.

---

## How to read this project going forward

One status page, updated as things move, rather than re-deriving context from the full conversation each time.
Update this file's "Status by phase" and "Recommended next step" sections as work continues; add new rows to
the document map as new files get created. When a document is superseded, move it to `attic/` and add a row to
`attic/README.md` saying how it ended — do not leave a superseded document sitting beside a current one with
only a header to tell them apart.
