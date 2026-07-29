# `units` — status

**One page, last updated 2026-07-28. What happened, what document to read for what, what's actually done vs.
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

**Revised 2026-07-29 — Phase D's surge-detector item is now partly closed** (see "Status by phase" above), and
quantification/aggregation, the prior "close second," **turned out not to be gaps at all** once actually worked
out (`closed_class_inventory.md` §8, `agentic_scenario_catalog.md` §11). Three independent findings from this
session now converge on one thing instead: **goal/subgoal machinery (`model.md` §8, designed, not built)** —
needed by scenario 10's quantification case (multi-turn enumeration), by "justification" dissolving into goal
lineage rather than a new form (`closed_class_inventory.md` §10, `agentic_scenario_catalog.md` §12), and by
System 1 absorbing the wiring cost the substitution experiment surfaced (`computation_units.md` §5).

**Candidates, not yet decided between:**
1. **Goal/subgoal machinery.** Highest-leverage by convergence (three findings depend on it), but the biggest
   lift — still design, not code, and a real undertaking.
2. **`identity`/equality.** Now the clearest remaining cross-cutting *content* gap (scenarios 3, 7, 8) — no
   longer tied with quantification, since quantification resolved. `identity` in the narrow "compare two values"
   sense looks buildable independent of Phase D; full reference/definite-description resolution is still blocked
   on the surge detector.
3. **Give `COMMAND` real semantics** (`closed_class_inventory.md` §9) — small, concrete, quick: tests the
   `ask = command(report(P))` reduction hypothesis rather than leaving it argued-but-unverified.

**Lower priority, worth remembering rather than acting on now:** closing out `past`/`evidential`/`mirative`'s
open-hypothesis status (needs a competing form each before `slots()` can say anything); building the real
nested-`Claim` structure to test the induction against running code
rather than only against `smt_sieve.py`'s abstract model.

---

## How to read this project going forward

One status page, updated as things move, rather than re-deriving context from the full conversation each time.
Update this file's "Status by phase" and "Recommended next step" sections as work continues; add new rows to
the document map as new files get created. When a document is superseded, move it to `attic/` and add a row to
`attic/README.md` saying how it ended — do not leave a superseded document sitting beside a current one with
only a header to tell them apart.
