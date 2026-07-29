# Plan: reaching the goal in `cnl_engine_goal.md`

**Status: plan, 2026-07-28; updated 2026-07-29 for the and/or `Trigger` finding; §7 added 2026-07-29 as the next
arc's entry point.** References `cnl_engine_goal.md`
— read that first for the goal statement, the engine/ruleset responsibility split, and the three ingredients.
This document is the phase plan for closing the gap between "realistic goal" and "shipped guarantee," plus one
worked example (SUPPOSE's discharge) that turned out to be the concrete case for phase 2 below.

---

## 1. Why a phased plan, not a single pass

Two of the three ingredients (`cnl_engine_goal.md` §3) are calculus-level and largely engine-independent;
one is not. Sequencing that ignores this either wastes proof effort on forms that can't be realized in this
engine's execution model, or defers the one ingredient (honest depth/exhaustion reporting) that was never going
to fall out of CNL design at all. The phases below are ordered to catch the cheap failures first.

---

## 2. The four phases

### Phase A — Spec: finalize the closed-class inventory, abstractly

Nail down every closed-class form's intro/elim rule as a calculus-level statement — largely independent of
engine plumbing, and largely **not novel**: borrow proven calculi per family rather than inventing them
(`forms_discourse.md` §4.3, §4.5 — natural deduction for the connectives, Montague/type theory for composition,
DRT for reference, linear logic if action/consumption enters scope). Output: the entry format (`forms_discourse.md`
§5.2) filled in for every form, with `commits`/`forbids` split per the sieve's finding.

**In progress: `closed_class_inventory.md`.** Consolidates every form named across the docs plus what's already
runnable in `units/forms.py`, with a live-measured status per entry (confirmed / resolved hypothesis / open
hypothesis / structurally blocked / not yet formalized). Read it for current Phase A state before starting new
inventory work — it also names which items are actually Phase B or Phase D blocked rather than Phase A gaps.

### Phase B — Realizability gate: can this engine's execution model realize each rule at all?

**Cheap, per-form, before deep composition-proof investment.** For each entry from Phase A, check — not
implement, just check — whether the engine's already-chosen execution primitives (wires, cycles, support-as-a-
wire-value) can realize it. This is the phase that would have caught the SUPPOSE finding early; §3 below is the
worked example, now verified against the actual code rather than only against the memory record.

Anything that fails this gate forces a real choice: revise the execution model, or revise the form. Nothing
downstream should be built on a form that hasn't cleared this gate.

**And/or (`Trigger`'s `All`/`Any`, `composition_grammar.md` §8) clears this gate almost for free**, and it's
worth stating why next to a form that failed it: `All` is an ordinary two-gate unit (fires once both deliver —
already how any two-input unit works), `Any` is the same shape with either-delivers instead of both. Nothing new
is asked of the execution model — contrast with SUPPOSE's discharge (§3), which needed a primitive
(`powering()`'s backward wire-walk) that doesn't exist. That's the actual distinction Phase B is for: `Trigger`
passes because it reuses gates as they already work; discharge fails because escaping a supposition needs a
boundary the engine has no gate kind for.

### Phase C — Composition proof: do the forms that passed Phase B compose with each other?

The harder, `sieve.py`-style pairwise-and-beyond work (`forms_discourse.md` §4.2) — but now scoped to forms
already known realizable, so the effort isn't spent proving composition for something that turns out unbuildable.

### Phase D — Termination/honesty, in parallel, independent of which forms end up in the inventory

Fix or replace the surge detector (`forms_discourse.md` §10.3) so depth exhaustion is *reported*, not silently
truncated. This is foundational computational-model work — a real termination argument or energy measure that
distinguishes convergent recursion from a runaway cycle — and does not depend on the CNL's contents, so it can
proceed independently of phases A–C.

**⭐ Done, 2026-07-29 — reframed and partly closed.** The "distinguish convergent recursion from a runaway
cycle" framing above was checked against the running code and found **structurally impossible, not merely
unsolved**: every self-loop this engine can express mints a fresh node each pass, so no two passes' values are
ever equal or in a subset relation, and there is no content-blind signal left to build a smarter detector out
of (`forms_discourse.md` §10.3's 2026-07-29 update has the trace). What was fixable and is fixed: the detector
was conflating two different failures under one veto — a wasted-but-honest false positive (depth 4, correct,
discarded) and a genuinely dangerous false negative (depth ≥ 5, truncated, returned as if complete). Fixed by
excluding a burned unit's value from every read (`Network._unit_burned`, `units/engine.py`) so it reads as
*absent* rather than as a stale partial answer, paired with widening `SURGE_AT` (3 → 6) so the common shallow
case doesn't trip the veto at all. Neither part proves termination; together they close the actual ingredient-3
ask — the engine no longer reports a wrong answer as if it were right.

---

## 3. ⚠ SHELVED, 2026-07-28: SUPPOSE's discharge

**Not being worked on, and here's why, so it isn't quietly re-picked-up without the reason attached.**
Checked against `agentic_scenario_catalog.md`'s ten scenarios directly: every one of them assumes rules are
already authored by a human and the agent's job is to *apply* them (modus ponens — already works, no problem).
**None of the ten need the agent to derive a brand-new rule from exploring a hypothetical**, which is the only
thing discharge is actually for. That makes this the same shape of mistake `mirative` turned out to be — a
real, well-motivated capability (there, from linguistic typology; here, from natural deduction) that got
significant attention without ever being checked against a demonstrated need.

Where it would earn its place back: an agent that learns or refines its own rules from experience (simulates
cases, notices a pattern, wants to encode it as a new standing rule rather than re-deriving it each time) — a
real capability, but a materially more advanced one than anything in the current ten scenarios. If that becomes
an actual need, add it to the catalog as its own scenario and let it justify the work the way the other ten did,
rather than resuming this because it's a known gap in natural deduction.

**What stays valid despite shelving this:** the *diagnosis* below (why discharge doesn't work on this engine as
built) is a correct, permanent finding about the architecture, worth keeping on record even unstarted. What does
**not** carry over is any claim that fixing it is on the critical path — it no longer is.

The original worked example, kept for the record:

## 3a. Worked example: SUPPOSE's discharge, checked against the code — the canonical Phase B case

`forms_discourse.md` §4.4 claims *"SUPPOSE is the introduction rule for the conditional"* — assume P, derive Q,
discharge to conclude P → Q. This is exactly a Phase A form (borrowed straight from natural deduction, nothing
novel about the abstract rule). Whether **this engine** can realize discharge is a Phase B question, and it has
already been asked and answered in the code:

**The test.** `tests/units/test_engine.py:682-706`,
`test_nothing_downstream_of_a_supposition_can_conclude_in_the_base_world`. It builds precisely the fix this
conversation proposed — a `discharge` unit that mints a **new, different** attribute (`conditional_holds`)
rather than re-asserting the raw hypothetical conclusion (`dangerous`) — wired downstream of a
supposition-powered unit. Result:

```python
assert n.powering(discharge) == frozenset({"H"})             # inherited, unavoidably
assert n.world().attr(lion, "conditional_holds") is None     # …so it cannot reach the base world
assert n.graph(frozenset({"H"})).attr(lion, "conditional_holds") is True
```

**Why minting a different fact doesn't help.** `powering()` (`units/engine.py:980-1000`) decides whether a unit
is "inside" a supposition purely from **wiring topology** — a backward walk over every wire, collecting any
ancestor's `.supposes`. It has no notion of *what* a downstream unit chooses to write; it only asks whether a
wire path leads back to a supposition. `discharge` minting `conditional_holds` instead of `dangerous` doesn't
change that it is wired downstream of `inner`, so `write_back()`'s filter (`engine.py:919`,
`not self.powering(u)`) excludes it exactly as it would exclude the raw conclusion. **The taint propagates
through the wire, not through the content of what gets written.**

**What this means for the fix.** The engine currently has one kind of connection, and it always propagates
support — correctly, because that's what stops the *other*, adjacent leak
(`test_a_mutating_rule_inside_a_supposition_does_not_act_on_the_world`, `engine.py:915`: *"suppose it rains"*
wired to a mutating rule must not really take the umbrella). Discharge needs a **structurally different**
operation: not *"read through the supposition to act on its content"* (must stay scoped) but *"read about the
supposition to state a conditional"* (must escape it — that is what discharge *is*). These are different
questions answered through the same mechanism today, and that conflation is the actual finding, not a missing
mint.

**What an actual fix requires:** a second kind of gate — a hypothetical-test / discharge gate — that queries
`self.graph(under=frozenset({"H"})).attr(...)` as a snapshot read rather than an ordinary wire, and which
`powering()` treats as a boundary: the backward walk stops there instead of passing through. This is a genuine
new primitive, not a parameter on the existing one, and it carries a real design risk that must be resolved, not
assumed away: the boundary has to be narrow enough that only a unit minting the *conditional relation itself*
can use it — nothing should be able to use the same escape hatch to let a mutating effect act on the world
unconditionally, which would silently reopen the umbrella leak the adjacent test exists to prevent.

**Status:** open. This is Phase B's first concrete item — solving it (new gate kind + the boundary condition on
its use) is a prerequisite for `forms_discourse.md` §4.4 being buildable on this engine, and for the conditional
entering Phase C's composition-proof work at all.

---

## 4. `units/smt_sieve.py` — a second, decidable check feeding Phase C

`sieve.py` finds a leak by building a concrete cell, running the actual engine, and reading the result —
sound, but only over the cells `cells()` happens to construct. Telecom's feature-interaction-detection
literature (Zave, from 1993) takes the other route: encode each feature as a declarative constraint and ask a
decision procedure whether *any* assignment violates it — a proof over the whole symbolic domain in one query,
the same move as lifting a hard-to-separate boundary into a space where it becomes linear (z = x² + y² for a
circle).

**Built and run.** `units/smt_sieve.py` re-expresses `SEED`'s `fires`/`conclusions`/`forbids` as Z3 formulas over
free variables (`polarity`, `force`, `level`, `has_degree` — no concrete claim is ever constructed) and asks,
per form, whether its `forbids` is satisfiable. Result, reproducing three known findings **as proofs rather than
samples**:

| form | naive | guarded | witness (naive) |
|---|---|---|---|
| `negation` | `sat` (leaks) | `unsat` (proven safe, not just untested) | `polarity=NEG, has_degree=True` — exactly the measured `degree ∘ negation` leak |
| `ask` | `sat` | `unsat` | `polarity=POS, force=ASK` — `forms_discourse.md` §8's "map the question, then assert it" |
| `language` | `sat` | `unsat` | `level=LANGUAGE, polarity=POS` |

**What this is not yet:** for a domain this small, exhaustive enumeration could already reach the same
conclusion — the payoff is the infrastructure (forms as pure formulas over free variables), not a new result
today. Two directions this opens, one of which has already paid off:

1. **`conditional`, extended — done, and it found a second, real defect.** Adding `has_conditional`/
   `antecedent_satisfied` to the encoding and checking a `conditional_detachment` formula came back `sat` in
   **both** naive and guarded modes. This predicted, and `guard_density(CANDIDATES)`/`probe((UNMET, POSITIVE),
   guarded=True)` then confirmed empirically, that **guarding does not fix `conditional`'s detachment leak** —
   distinct from the discharge blocker in §3, and living in Phase C rather than Phase B. Recorded in
   `closed_class_inventory.md` §5. This is the first case in this project where the SMT encoding found something
   the empirical sieve hadn't been run to check yet, rather than only reproducing an already-known result.
2. **Corrected framing, 2026-07-28: "prove it for n forms at once" doesn't need induction here — it's already
   what a free (unfixed) variable gives you.** Every attribute in the encoding (polarity, force, level,
   has_degree, has_conditional, antecedent_satisfied) was already left unfixed, which means each `check()` call
   was already asking about every combination of every form that can affect it, of any size, in one query —
   there was never a separate "now do triples" step to do. What was actually still missing was a form with no
   variable yet: added `command` as a third `Force` value (it shares `ask`'s forbids shape). Re-running the full
   check with every current form that has real teeth (negation, degree, ask, command, language, conditional)
   included at once: **negation/ask/command/language all come back `unsat` under guarding** (proven safe across
   the whole current inventory, not sampled); **`conditional_detachment` stays `sat` even guarded** — confirming
   item 1's finding holds up against the fuller check, not just the smaller one. What this still cannot cover:
   a form nobody has designed yet has no variable in this file, and no solver query can protect against that —
   that's a design-discipline question for how future guards get authored, not something provable today.
3. **⭐ The nesting-depth induction — done, and NOT related to discharge (correcting a conflation of mine).**
   `composition_grammar.md` §5a: with the base case already proven (item 2, above), the inductive step — does
   nesting one conditional inside another stay safe, *assuming* the inner one already is — was checked two ways
   in `check_inductive_step()`. Naive wiring (outer concludes the answer directly) is `sat`, leaking even under
   the induction hypothesis. Gated wiring (outer only unlocks whatever the inner already concludes) is `unsat`,
   safe at every depth. ⚠ **This is about evaluating an already-authored nested rule** — modus ponens applied
   twice ("if A, then: if B then C," given A and B) — **not about SUPPOSE's discharge.** I originally worded
   this as depending on "the discharge mechanism," which was wrong: nested rule *evaluation* is purely
   elimination-side and needs no hypothesis-introduction at all. It is squarely still needed (scenarios 1 and 6
   both evaluate authored conditional rules) and is **not blocked by shelving discharge (§3)** — a concrete
   requirement on how nested-conditional evaluation must be wired, standing on its own.
4. **And/or, worked out the same way and landing in the same place.** `composition_grammar.md` §8 (via
   `computation_units.md`'s worked example): `and`/`or` are a fan-in shape at a conditional's antecedent
   position (`Trigger`'s `All`/`Any`), always feeding one shared `then`, never a free-standing claim with its
   own consequent. Sound by construction, same reasoning as item 3 — and, same correction as item 3 needed
   twice now, **not about discharge either**: a bare "A or B" with nothing derived from it is inert content;
   it only becomes a discharge problem if something tries to derive a *new* shared conclusion independently
   under each disjunct, which is out of scope for the same reason §3 is shelved.

---

## 5. Open items carried from `cnl_engine_goal.md`, restated as phase assignments

| item | phase |
|---|---|
| Full closed-class inventory with intro/elim stated per entry | A |
| SUPPOSE's discharge gate (§3) | **shelved** — no scenario in `agentic_scenario_catalog.md` needs it; diagnosis kept on record, not on the critical path |
| Nested-conditional evaluation must use "gated" wiring, not "naive" (§4 item 3) | C — independent of discharge; needed for scenarios 1 and 6 |
| ⭐ **Conditional's detachment leak — DONE, fixed in code 2026-07-28** | C — `Form.excludes_defaults` (`units/forms.py`, `units/sieve.py`); `still_leaking` now empty, guarded leak rate 0.008 with only the explicitly-requested `positive ∘ unmet` remaining, correctly. First item in this plan to go from design/proof to verified running code |
| Guards found to silence rather than compose (0 leaks, 0 passes) | B/C — a guard that only blocks is a Phase B form that hasn't been given a real Phase C composition path yet |
| Pairwise leaks (65% of naive cells) | C — now also provable rather than only samplable, per §4 |
| n ≥ 3 nesting | **C — closed as a design requirement.** §4 item 3's induction proves safety at unbounded depth *conditional on* the gated wiring discipline; no longer an open measurement question, and not blocked by shelving discharge |
| And/or (`Trigger`'s `All`/`Any`, `composition_grammar.md` §8) | **B — cleared** (ordinary multi-gate wiring, nothing new asked of the execution model); **C — closed as a design requirement**, sound by construction, same shape as n ≥ 3 nesting above; **not built** in `units/` yet |
| Surge detector cannot distinguish convergent recursion from a runaway cycle | **D — reframed and partly closed 2026-07-29**: the distinguishing check is structurally impossible (verified, not just unsolved), but the dangerous half — a truncated answer read as if complete — is fixed by excluding burned units from reads |

---

## 6. What this plan does not cover

Same exclusions as `cnl_engine_goal.md` §5 — nothing here touches business-rule correctness or open-class
predicate interaction. This plan is scoped entirely to the closed class and the engine that composes it.

---

## 7. Next arc, 2026-07-29 — goal/subgoal lineage, a first System 1, and additive rewriting

**Start here if resuming cold.** Three threads, tackled **jointly**, not as separate tickets — they turned out to
be intertwined enough that solving one without the others would likely mean redoing it. `computation_units.md`
and `closed_class_inventory.md` §8/§10 have the reasoning that led here; this section is the one place that
states the combined arc and what to actually build first.

### 7a. Why these three, together

- **Goal/subgoal lineage** (`model.md` §8, design not code) is now a confirmed dependency of three separate
  findings: quantification's case (c) — checking a set member-by-member across turns needs a cursor that
  survives a revive (`closed_class_inventory.md` §8); "justification" dissolving into goal lineage rather than a
  new CONTENT form (`closed_class_inventory.md` §10, `agentic_scenario_catalog.md` §12); and the substitution
  experiment's wiring-cost finding, which is exactly System 1's job to absorb (`computation_units.md` §5).
- **A first System 1 prototype** (`model.md` §7, associative retrieval — design not code) is the connective
  tissue: "which standing rule is relevant right now" is the same question whether the consumer is a goal
  deciding which rule decomposes it into subgoals, or a term deciding which definition-rule rewrites it. Building
  retrieval once and letting both ride it beats each hand-wiring its own chain.
- **In-KB rewriting** came up as a natural extension of the `define`+`Identify` substitution experiment
  (`computation_units.md` §5) — and forced a real decision, resolved in conversation: rewriting a fact into a
  different form means **minting the new-form fact alongside the old**, not replacing it. Both coexist; rules
  using either form fire independently; convergence happens by accumulation, not destruction. (A destructive
  rewrite was considered and rejected — it would reopen exactly the collapse `model.md` §3 already paid to
  prevent: two live derivations silently clobbering one shared value.)

### 7b. Prior art actually checked, not assumed — from the OLD `ugm` engine

A full research pass (not guessed) found real, usable prior art for **half** of this, and confirmed the other
half is genuinely new territory in both generations:

- **What's validated and portable (the shape, not the code):** the old engine's plan→act→check→replan loop
  (`docs/design/procedures_design.md`, `ugm/mode_calls.py`, worked example in `tests/test_isa_plan_act_check.py`)
  — a `<call>` token is data (tool name + args), "checking" is an ordinary rule reacting to a verdict fact,
  discrepancy/achieved/diverged are **positive facts attached to the goal**, never absence-tests, and the whole
  loop composes monotonically with **no teardown** (a stale verdict from an abandoned path just sits there,
  inert, harmless — five rules, no Python driver, `test_isa_plan_act_check.py`'s docstring). This matches
  `model.md` §8's own framing closely and can be ported as a rule bank.
- **What was never built, in either generation:** a persisted **goal → subgoal lineage relation** that a rule
  could walk afterward for explanation. The old procedures arc has goals, steps, checks, replanning — but no
  parent→child edge between goal-nodes. `ugm/chain.py`'s `<subgoal>` looked like a candidate but is confirmed (by
  the code's own comments) to be a different concept — negation-as-failure explanation ("I searched X and found
  nothing"), not agentic goal decomposition. Its **shape** is reusable (an interned goal-shaped node, a
  parent-child edge, control-marked) even though its semantics aren't.
- **Why a `GoalSolver` was retired** (`docs/attic/goalsolver_retirement_design.md`): consolidating two competing
  engines into one, not a flaw in goal/subgoal machinery itself — mostly doesn't transfer. One real lesson that
  does: backward/demand-driven search and closed-world negation don't compose cleanly (a hazard test proved it).
  `units/` is already on the correct side of this (forward, revive-from-axioms, never backward demand), so this
  is a reassurance, not a warning to act on.
- **Two scars worth not re-earning a third time:** (1) the procedure's own step order and the planner's global
  order had to be kept as two distinct relations — conflating them broke things; expect subgoal lineage similarly
  needs to stay **scoped** to its own goal, never a global relation. (2) **Stratification races around
  NAC-shaped guards that gate a subsequent action were the single most recurring bug** in the old procedures arc,
  rediscovered three separate times across its slices. Any rule that spawns or completes a subgoal on a
  `not X`-shaped guard needs to be tested explicitly for this race, not just reasoned about.

### 7c. The design so far, pending a worked example

| fact/relation | shape | who writes it |
|---|---|---|
| a goal | an ordinary node + a `wants:` role pointing at its satisfaction-condition claim | a mutating rule (must survive a suspend) |
| subgoal lineage | `goal -[raised]-> subgoal`, interned (get-or-create per parent + satisfaction-condition, borrowing `ugm/chain.py`'s interning pattern, not its NAF semantics) | a mutating rule |
| outcome | a positive marker attribute on the goal node — `achieved` / `diverged` / `abandoned` — never an absence-test | a mutating rule, reacting to whatever "checks" the condition |
| decay | a mutating rule concluding `abandoned=True` **plus** retracting the goal's own gate-wiring (closing `model.md` §13's attention-leak) — the `raised` lineage edge itself stays, permanently, same reasoning as provenance-is-free | a mutating rule, deliberately using the one non-monotone effect |

**Deliberately deferred:** `model.md` §7's full associative retrieval is not a prerequisite — build the goal bank
with explicit wiring first (same as every worked example this session), and treat System 1 as what removes that
authoring cost later, not a blocker now. A *first* prototype of it (scope still to be decided) is part of this
arc, but need not be the associative-recall machinery in full.

### 7d. Next action

Build a small worked example the way `Trigger` and the substitution experiment got one before any of this was
written up as settled: one parent goal, one subgoal it raises, a check that fires an outcome, and an
abandon-and-decay case — run against the real engine, see what breaks, *then* write the design doc. Do the same
for a minimal rewrite-via-addition case (two coexisting forms of one fact, a rule that fires off either) before
committing to the shape in §7c.

### 7e. Built and run, 2026-07-29 — `units/goal_experiment.py`

Four checks, all against the real engine (`python -m units.goal_experiment`), all green, none needing new engine
code — everything in §7c's table is buildable with the five existing effect kinds plus the existing `absent()`
guard. What running it actually found, which is more than "it works":

**Lineage interning needs the outer loop to be real, not a detail to defer.** `_raise_subgoal_rule`'s NAC guard
(`absent(atom("g", out=(role("raised", atom()),)))`) is the interning mechanism §7c called for, and it works —
*but only across the per-turn "rebuild `Network` from the accumulated graph"* shape, not across two `revive()`
calls on one `Network`. Measured both ways: two revives on the same `Network` mint a **second** subgoal (1 → 2,
`check_lineage_interning_naive`); a fresh `Network` per turn, axiom rebuilt from the prior turn's
`n.asserted`, mints exactly one (1 → 1, `check_lineage_interning_per_turn`). The reason is mechanical and worth
recording as a general lesson, not just a goal-machinery footnote: **an axiom's held value is a fixed snapshot
taken at construction** (`given()` calls `effects_of(g)` once), so calling `revive()` again on the same
`Network` redelivers the *original* graph, blind to anything write-back added since — the guard reads only what
is delivered to the unit's own gate, and nothing re-derives that delivery. This matches `model.md` §7's outer
loop exactly (*"the next step retrieves against the data step 3 produced"*) — the loop already prescribed
rebuilding per step, this just confirms goal lineage has no exemption from that discipline.

**Outcome-as-a-positive-fact needed nothing beyond an ordinary mutating rule** — `achieved`/`diverged` landed
exactly as designed, no surprises. The clean case in this arc.

**Decay's wire-retraction needed one thing §7c's table didn't say out loud: machinery has to be *delivered*
before a rule can drop it.** `model.md` §6 already states this (invariant 19 — *"machinery must be delivered to
a gate before any pattern can see it"*) but §7c's table reads as if `Drop` on a `<wire>` node were a one-gate
affair like everything else in the table. It is not: the decay rule needed a **second gate**, fed by
`n.axiom(*effects_of(n.asserted), name="reflect")` (the same reflective-axiom idiom `test_engine.py`'s
`leaky()` uses), because the goal facts and the wire facts are never both on one gate's latched value at once —
wiring both sources to the same default gate would just have the later delivery silently overwrite the earlier
one (single-gate latch, not accumulation). Confirmed by reading `n.wires` before/after: the `("given", "watch",
"in")` wire is gone after revive, `abandoned` is `True`, and — not exercised here since this scenario's goal has
no lineage, but consistent with the design — nothing else needed touching.

**Additive rewriting hit the tunnel again, the same shape `computation_units.md` §5 already found for
`Identify`/substitution, and the fix generalizes.** `reify_age`'s output (`Emit` + `Attribute`) carries only the
*new* facts it minted — not a copy of the base fact it read (`age=42` on Paul) — so a naive consumer pattern
requiring `name="paul"` on the linked node fails: that attribute was never re-emitted, only referenced by
identity. Fixed by dropping the redundant constraint (the "about" edge already carries the right node by
identity; nothing needs to re-check its name) rather than by wiring the consumer to both the axiom and the
producer as `computation_units.md` §5 did — a narrower fix here because the consumer didn't actually need the
base fact's *attributes*, only the node it pointed at. **The general lesson holds regardless of which fix
applies:** a unit's output is only ever what it minted or concluded, never a passthrough of what it read, so any
rule consuming a derived fact must be wired to see everything its pattern actually needs — the wiring cost
`computation_units.md` §5 flagged as System 1's job to absorb is confirmed here as a *recurring* cost, not a
one-off found once and fixed once. With that, `old_form_seen` and `new_form_seen` both landed **and** `age`
stayed `42` — additive coexistence confirmed, not merge-and-hope.

**What this changes about §7c, going in to the design doc:** the table's shape survives unchanged — no new
effect kind, no new gate concept beyond what already exists — but two things move from "detail" to
"requirement, stated": (1) any goal-lineage consumer (a check rule, a decay rule, anything reading `raised`)
must be re-derived from the accumulated graph each turn, never revived twice against a stale snapshot; (2) any
rule matching machinery (a wire, in this case) needs a dedicated gate fed by a reflective axiom, not folded onto
the same gate as its ordinary premises. Neither is a change to the model — both are already implied by
`model.md` §§6–7 — but neither was visible until something broke against the running code, which is exactly why
§7d asked for this before the design doc rather than after.

**Not yet touched:** a subgoal with its *own* satisfaction condition distinct from its parent's (this
experiment's subgoal is a bare lineage marker, no `wants` of its own); a check that spans more than one revive
(the cursor case, `closed_class_inventory.md` §8 case (c)); and System 1 in any form — every wire above is
still hand-authored, per §7c's explicit deferral.
