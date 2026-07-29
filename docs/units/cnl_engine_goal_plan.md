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
| Surge detector cannot distinguish convergent recursion from a runaway cycle | **D — reframed and partly closed 2026-07-29**: the distinguishing check is structurally impossible (verified, not just unsolved), but the dangerous half — a truncated answer read as if complete — is fixed by excluding burned units from reads |

---

## 6. What this plan does not cover

Same exclusions as `cnl_engine_goal.md` §5 — nothing here touches business-rule correctness or open-class
predicate interaction. This plan is scoped entirely to the closed class and the engine that composes it.
