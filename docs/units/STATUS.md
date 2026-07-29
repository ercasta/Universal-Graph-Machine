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

**Still open, lower priority, not blocking the above:**
- **`identity`/equality.** The clearest remaining cross-cutting *content* gap (scenarios 3, 7, 8), independent of
  the joint arc above. `identity` in the narrow "compare two values" sense looks buildable independent of Phase
  D; full reference/definite-description resolution is still blocked on the surge detector.
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
