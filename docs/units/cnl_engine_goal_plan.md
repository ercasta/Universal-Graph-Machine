# Plan: reaching the goal in `cnl_engine_goal.md`

**Status: plan, 2026-07-28.** References `cnl_engine_goal.md` — read that first for the goal statement, the
engine/ruleset responsibility split, and the three ingredients. This document is the phase plan for closing the
gap between "realistic goal" and "shipped guarantee," plus one worked example (SUPPOSE's discharge) that turned
out to be the concrete case for phase 2 below.

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

### Phase C — Composition proof: do the forms that passed Phase B compose with each other?

The harder, `sieve.py`-style pairwise-and-beyond work (`forms_discourse.md` §4.2) — but now scoped to forms
already known realizable, so the effort isn't spent proving composition for something that turns out unbuildable.

### Phase D — Termination/honesty, in parallel, independent of which forms end up in the inventory

Fix or replace the surge detector (`forms_discourse.md` §10.3) so depth exhaustion is *reported*, not silently
truncated. This is foundational computational-model work — a real termination argument or energy measure that
distinguishes convergent recursion from a runaway cycle — and does not depend on the CNL's contents, so it can
proceed independently of phases A–C.

---

## 3. Worked example: SUPPOSE's discharge, checked against the code — the canonical Phase B case

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

## 4. Open items carried from `cnl_engine_goal.md`, restated as phase assignments

| item | phase |
|---|---|
| Full closed-class inventory with intro/elim stated per entry | A |
| SUPPOSE's discharge gate (§3 above) | B |
| Guards found to silence rather than compose (0 leaks, 0 passes) | B/C — a guard that only blocks is a Phase B form that hasn't been given a real Phase C composition path yet |
| Pairwise leaks (65% of naive cells) | C |
| n ≥ 3 nesting, unmeasured | C |
| Surge detector cannot distinguish convergent recursion from a runaway cycle | D |

---

## 5. What this plan does not cover

Same exclusions as `cnl_engine_goal.md` §5 — nothing here touches business-rule correctness or open-class
predicate interaction. This plan is scoped entirely to the closed class and the engine that composes it.
