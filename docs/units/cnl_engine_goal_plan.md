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
guard.

⚠ **First pass at this section overstated two of the four findings, and the correction is worth keeping on
record rather than smoothing over.** The first version reached for two pieces of unnecessary machinery — a
*second* `Network` object, rebuilt each "turn"; a *second gate*, to keep goal-facts and wire-facts from
colliding — and reported both as if the engine required them. Neither does. The actual mechanism was already
sitting in `tests/units/test_engine.py` (`test_a_rule_writes_a_whole_rule_with_nothing_authored_in_python`,
`test_a_mutating_rule_can_conclude_a_wire`): **one persisting `Network`, one persisting `StandingUnit`**, and
between turns you manage the axiom's `.held` lifecycle — null the stale one, wire a fresh reflective axiom
capturing the *current* `self.asserted`, onto the *same* gate. Re-verified directly against the engine before
rewriting `goal_experiment.py` to match. Corrected findings below; what stood is marked as such.

**Lineage interning: the guard works, and the "naive" failure isn't a finding — it's documented behavior.**
`_raise_subgoal_rule`'s NAC guard (`absent(atom("g", out=(role("raised", atom()),)))`) is the interning
mechanism §7c called for. Calling `revive()` again with the axiom left untouched **correctly** mints a second
subgoal (1 → 2, `check_lineage_interning_naive`) — not because of a defect, but because `model.md` §5 says
exactly this will happen (*"a repeat arrival is a firing... there is no value-comparison test suppressing
it"*): the guard's view is built only from what's latched on its own gate, and redelivering the identical,
unmanaged snapshot is misuse of the axiom, not a property of goal machinery. **The corrected fix stays on one
`Network`:** null the stale axiom (`ax.held = None`), wire a fresh `n.axiom(*effects_of(n.asserted), ...)` —
capturing what write-back just added — onto the *same* gate the unit already had (`check_lineage_interning_managed`,
1 → 1). No second `Network`, no rebuild. The earlier framing ("needs the outer loop to be real... rebuild
`Network` from the accumulated graph") described a working but gratuitously heavier mechanism, invented instead
of reaching for the one already precedented in the test suite.

**Outcome-as-a-positive-fact needed nothing beyond an ordinary mutating rule** — `achieved`/`diverged` landed
exactly as designed, no surprises, and nothing about this finding changed on re-check.

**Decay's wire-retraction needs delivery, but not a second gate.** `model.md` §6 (invariant 19 — *"machinery
must be delivered to a gate before any pattern can see it"*) is the real requirement, and it's satisfied by
**one** reflective axiom (`n.axiom(*effects_of(n.asserted), name="reflect")`) on the unit's **one** ordinary
gate: taken after `given()`/`wire()` have both already written into `self.asserted`, that snapshot is a strict
superset of what the plain axiom alone would deliver, so nothing needs splitting across two gates. The earlier
"needs a second gate" claim was an artifact of the first draft wiring `ax` and `reflect` to *separate* gates
instead of reaching for one reflective axiom that already contains everything — a problem manufactured by that
choice, then patched with more machinery, not a fact about the engine. Confirmed by reading `n.wires`
before/after (the `("given", "watch", "in")` wire is gone; the redundant `("given", "decay", "in")` wire the
first draft added isn't even present in the corrected version), and `abandoned` is `True`.

**Additive rewriting hit the tunnel again, the same shape `computation_units.md` §5 already found for
`Identify`/substitution, and this one held up on re-check.** `reify_age`'s output (`Emit` + `Attribute`)
carries only the *new* facts it minted — not a copy of the base fact it read (`age=42` on Paul, `StandingUnit`'s
`view()` is built from an `EMPTY` base, never `self.asserted`) — so a consumer pattern requiring `name="paul"`
on the linked node fails: that attribute was never re-emitted, only referenced by identity. Fixed by dropping
the redundant constraint (the "about" edge already carries the right node by identity; nothing needs to
re-check its name) rather than by wiring the consumer to both the axiom and the producer as
`computation_units.md` §5 did — a narrower fix here because the consumer didn't actually need the base fact's
*attributes*, only the node it pointed at. **The general lesson holds regardless of which fix applies:** a
unit's output is only ever what it minted or concluded, never a passthrough of what it read, so any rule
consuming a derived fact must be wired (or its pattern scoped) to match what that fact's producer actually
re-asserts. `old_form_seen` and `new_form_seen` both landed and `age` stayed `42` — additive coexistence
confirmed.

**What this changes about §7c, going in to the design doc — corrected:** the table's shape survives unchanged,
and so does its claim that no new effect kind or gate concept is needed. What moves from "detail" to
"requirement, stated" is narrower than the first draft claimed: (1) a goal-lineage consumer across turns must
have its axiom's lifecycle *managed* (nulled when stale, refreshed with a reflective snapshot when something
new needs seeing) — this is a **discipline on how `Network`/`Cell` get used**, not a requirement to rebuild
anything; (2) a rule matching machinery (a wire) needs it *delivered*, via a reflective axiom, same gate as
everything else — not a dedicated one. Both are already implied by `model.md` §§6–7 and by precedent already
in the test suite; the corrected version of this section is closer to "confirmed the existing idiom transfers"
than "found a new requirement."

**Not yet touched:** a subgoal with its *own* satisfaction condition distinct from its parent's (this
experiment's subgoal is a bare lineage marker, no `wants` of its own); a check that spans more than one revive
(the cursor case, `closed_class_inventory.md` §8 case (c)); and System 1 in any form — every wire above is
still hand-authored, per §7c's explicit deferral. §7f (below) is that deferral being spent.

### 7f. Built and run, 2026-07-29 — `units/system1_experiment.py`, a first RETRIEVE prototype

The goal design doc (`goal_machinery.md`) is written; this is the deliberate next step taken with the explicit
possibility that it revises that doc, not after it. Three checks
(`python -m units.system1_experiment`), all green:

**RETRIEVE, minimally.** `attention()` is a BFS outward from a seed set, `resemblance()` scores a candidate
unit's *required attribute keys* (read off its authored `Pat`s via `match.atoms()`) against what's attended, by
Jaccard overlap; `retrieve()` wires in any candidate clearing a stated `theta`. Nothing here is a new engine
mechanism — wiring is still `Network.wire()`, decided by a score instead of by hand. This is deliberately
Python-level, not a rule: `model.md` §7 says the **outer driver** does retrieval, wiring, running, and writing,
and that "no semantics" means it never judges *content* — content judgement stays inside units, exactly as
before. Retrieval choosing *which* units get a chance to judge is not a content judgement itself.

**"Allowed to be wrong" is not a hand-wave — it showed up as an actual result, not a caveat.** Two candidate
rules (`mortal_rule` needs `kind`, `flight_rule` needs `kind`) both get wired against an attended `kind="man"`
node, because the resemblance scorer looks at attribute *keys*, not values — a crude, honestly-stated
similarity, not a claim of correctness. `flight_rule` gets wired and then **simply fails to fire**, because
firing still goes through `units/match.py`'s exact solver once wired — System 2 stays exact, exactly as §7
requires. This is the "wasted step" cost stated in the design, now demonstrated rather than asserted: a wrong
suggestion costs a dangling wire, never a wrong conclusion.

**A candidate needing an attended key that's genuinely absent stays unwired** (`weather_rule` needing
`humidity`, nothing attended has it, score 0.0) — the honest incompleteness §7 names: *"a rule that would have
applied may simply never come to mind."*

**The outer driver has no tunnel of its own, and that's a real, useful asymmetry — not the same finding as
`goal_machinery.md` §3, its mirror image.** A `StandingUnit` only ever sees its own gates, which is why a
rule-level interning guard needed the axiom-lifecycle discipline (null a stale axiom, wire a fresh reflective
snapshot) to see its own prior conclusion. The retrieval code calling `n.wire()` is not a unit — it is ordinary
Python holding a reference to `n` — so checking "is this candidate already wired" is a direct read of
`n.wires`, no reflective axiom needed. Two calls to `retrieve()` with the same candidate wire it exactly once
(verified). Worth stating plainly: **the tunnel is a property of units, specifically, not of every reader of
the graph** — §6/§7 never claimed otherwise, but it wasn't obvious until something outside a unit needed to
check its own past action.

**What this does not yet touch, honestly:** attention decay/leak (`model.md` §13), think-harder/random-refocus
(§7's PageRank-damping mitigation), asynchronous retrieval, and any similarity metric beyond crude key-overlap
(subgraph embedding, graded/banded resemblance using `band.py` rather than a bare float). None of these were
needed to get RETRIEVE to run once; they're the next layer if retrieval needs to scale past a toy pool.

**Does this revise `goal_machinery.md`?** Not yet, and the asymmetry above is why: retrieval turned out to
need *less* machinery than rule-level interning, not more, because it isn't bound by the tunnel. Nothing here
contradicts §3's mechanism for units — it confirms the tunnel is specifically a unit property by finding a
place (the outer driver) where it doesn't apply.

### 7g. Two follow-up additions to `system1_experiment.py`, 2026-07-29 (same day) — fan-out, and one reused cell

Raised in conversation, checked against the engine before being added: if retrieval can wire more than one
candidate at once, does that let it avoid ever needing to *un*wire a candidate later (pick one "best" rule,
swap it for a better one as data changes)? And does refreshing what an already-wired candidate can see require
minting a fresh reflective axiom every time, or can the same one be reused?

**Fan-out is unrestricted, verified directly.** `Network.wires` is just a set of `(src, dst, gate)` triples —
nothing anywhere limits how many consumers one source cell feeds. `retrieve()` already wires every candidate
clearing `theta` from the *same* reflective snapshot in one call (`check_fan_out_multiple_candidates_share_one_source`
confirms both `mortal_rule` and `flight_rule` are fed by exactly one shared source). Combined with `model.md`
§7's *"a dangling gate is a standing trigger"*, this settles the original question: **wire every plausible
candidate, never unwire one for failing to fire.** An unfired, wired candidate costs nothing and stays ready —
if the graph later changes so its pattern matches, it fires without retrieval ever having to reconsider it.
This also means "multiple candidates producing multiple overlays" was never actually a problem needing new
design: each unit's output is already its own independent `Cell.held` (`model.md` §1 — *"create never merge...
two units producing the same content are two live outputs"*), and disagreement between them is exactly what the
existing conflict-detection/retraction loop (§5/§9) is for, not something fan-out introduces.

**⭐ A real, measured cost was found and fixed while building this: minting a fresh reflective axiom every
`retrieve()` call causes unbounded, linear-per-call growth — not hypothetical, counted.** `Network.axiom()`
doesn't just set `.held`, it also writes the axiom cell's own node into the graph (`_describe`), so a *later*
reflective snapshot (`effects_of(n.asserted)`) includes descriptions of every *earlier* reflective axiom —
literally a mirror capturing all the previous mirrors. Measured over three simulated turns, minting fresh each
time: `self.axioms` and the wire count into the candidate both grew 2 → 3 → 4. **Fix, verified:** `retrieve()`
now accepts an existing reflective `Cell` and — on every call after the first — just reassigns its `.held` in
place (`reflect.held = Value(effects_of(n.asserted))`) rather than calling `n.axiom()` again. Since a plain
attribute assignment never calls `_describe()`, no new node or wire is ever added.
`check_reusing_one_reflective_cell_stays_flat_across_turns` confirms flat counts (2, 2, 2) across three turns
where the naive version would have grown to (2, 3, 4). **General lesson, stated once so it isn't re-derived per
worked example:** *"refresh what a unit can see"* means updating an existing `Cell.held`, not minting a new
`Cell` — minting is for genuinely new content, refreshing is for the same content restated.

### 7h. Built and run, 2026-07-29 (same day) — `units/quantification_cursor_experiment.py`, case (c) closed

`closed_class_inventory.md` §8 case (c) — *"checking every member of a bounded set needs more than one revive,
e.g. a tool call per member"* — was the one quantification case left open, and the concrete scenario that
originally motivated needing goal machinery at all (`STATUS.md`'s "recommended next step" history). Built now
that both mechanisms it needs exist: the axiom-lifecycle discipline (§7e/`goal_machinery.md` §3) and fan-out
from a reused reflective cell (§7g). Three checks, all green.

**The cursor is exactly what `model.md` §8 says it must be, and it was checked, not assumed.** `checked` is a
mutating rule's conclusion (asserted data), never a computation unit's overlay — verified directly
(`check_cursor_survives_because_it_is_asserted_not_derived`): a member checked on turn 1 is *still* checked on
turn 2, even though turn 2 delivers no new input for that member at all. Had `checked` been concluded by a
computation unit instead, it would vanish every revive and the same member would be re-asked forever.

**The universal outcome behaves exactly as `goal_machinery.md` §2 already required, now over a real multi-turn
case:** `achieved`/`diverged` are positive facts, and — checked explicitly, not just assumed — **stay `None`
through every middle turn**, never concluding completeness before the last member's result has actually
arrived. Both directions verified: all-eligible reaches `achieved`; one ineligible member reaches `diverged`,
never `achieved`.

**⭐ One new finding, sharper than anything in §4/§7g: fan-out from a single reused reflective snapshot is not
always enough, and the gap has a precise shape.** `achieved`/`diverged`, wired only to the reused reflective
axiom, computed one turn late — `achieved` only turned `True` on an *extra*, otherwise pointless settle turn
after the last member was actually checked. Reason: `reflect.held` is refreshed *before* `revive()` runs, i.e.
*before* this same turn's `check_member` has fired — so the reflective snapshot necessarily reflects the graph
as it stood at the *start* of the turn, one step behind a sibling rule's *own* output from later in that same
turn. **Fixed with a second gate wired directly to the sibling's `Cell`** (`check_member.cell`, its output from
this firing, available before write-back applies it to the store) — not a bigger snapshot, which cannot help
here since no snapshot taken before `revive()` runs can ever contain what that same `revive()` is about to
produce. `goal_machinery.md` §4 is amended with this as a precise addendum: reach for a bigger reflective
snapshot when the gap is *what's already in the store*; reach for a sibling's own cell when the gap is *what a
rule concludes this same turn*. These are different gaps with different fixes, and conflating them is an easy
mistake — the first attempt at this experiment made exactly that mistake before the fix was found.

**What this closes:** `closed_class_inventory.md` §8 case (c) moves from "designed, not built" to built and
green. Case (d) (open, unbounded domain) is unaffected — it was flagged as "possibly not a form question at
all," and nothing here bears on that.
