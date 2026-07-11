# GoalSolver retirement — design (Phase 6.1)

> **Status: DONE / AS-BUILT (2026-07-11, 264 passed/1 skipped).** GoalSolver + the reference `Walker` are
> DELETED; `ask_goal` runs on the forward firmware (decided negation); `decide.solve` is a single firmware
> pass; `decided_negation=False` (the NAF path) is retired. See the CHANGELOG (Phase 6.1) for the as-built
> summary. NOTE — the design below assumed a demand-driven flip (`check`/`witnesses`); the actual build
> took the FORWARD path instead, because a hazard test proved the monotone demand-driven chain cannot do
> decided negation (its aggressive completion re-fires without the INTERPOSE defeat). Decided negation is
> inherently forward; `witnesses` was added then removed (unused by the final forward `ask_goal`). Crux #4
> (the NAC/negation gap) resolved as option (a): decided-negation-only + forward materialization. See
> [[delete-old-code-aggressively]].
> The active plan is `implementation_plan.md`; this is the design detail for its Phase 6.1 ("GoalSolver
> (or its remains) = ACCELERATOR only where profiling justifies; deleted where firmware subsumes it —
> coverage alone, NOT old-answer equivalence"). Companion of the Phase 6.0 rewriter retirement (the
> precedent this follows) and the `name_demotion_design.md` / `vocabulary_declaration_design.md` design
> docs. Written to be EXECUTABLE by a fresh session once §7 is answered.

## The problem — TWO reasoning engines in ugm, and the ask surface runs the OLD one

`ugm` ships two complete reasoning engines:

- **`GoalSolver` (`goal.py`)** — a Python tabled/demand-forward solver. The pre-firmware engine. Returns
  a SET OF BINDING TUPLES for a `Goal(pred, subj, obj)` (subj/obj may be free), handling transitivity
  (via the reference `Walker`, `goal.py:407`), coref (`same_as` following), NAC-as-completion negation,
  and graded degree — all in Python control flow.
- **The FIRMWARE** (Phases 4–5): `apply` (APPLY), `chain`/`chain_sip` (CHAIN), `check` (CHECK verdict),
  `choose` (CHOOSE), `suppose` (SUPPOSE), `cnl/walker.walk_on_demand` (in-graph fuelled walker). Reified
  rules, in-graph control, no Python driver.

**The defect:** the user-facing reasoning surface still runs the OLD engine. `cnl/query.ask_goal`
(`query.py:314,330`) calls `GoalSolver(graph, rules)`. The firmware entry points (`check`/`choose`/
`suppose`) are reached ONLY from `mode_calls.py` (the `<call>` procedures) and tests. So "is X a Y?" /
"who is a Y?" goes through GoalSolver, not the firmware. GoalSolver is thus a live parallel engine, not
a dead oracle — retiring it is a MIGRATION, not a delete.

## What the migration actually touches (audited 2026-07-11)

Three facts (verified in code) make this smaller than it looks:

1. **`check.collapse` ALREADY equals `ask_goal`'s verdict** — `{POSITIVE:"yes", ENTAILED_NEG:"no",
   ASSUMED_NO:"no", UNKNOWN:"unknown"}` (`check.py`). The yes/no path is a drop-in.
2. **No firmware module imports GoalSolver** — every `GoalSolver` mention in `check`/`choose`/`chain`/
   `apply` is a docstring reference. GoalSolver's ONLY production consumer is `query.ask_goal`
   (`solve_goal`/`solve_all` are export-/test-only; the `_recognize -> solve_all` note in `authoring.py`
   is a historical comment — recognition runs on `run_bank`).
3. **Transitivity is RULE-based, not `Walker`-based** — the firmware answers `is_a` transitivity by
   applying the ordinary `is_a.transitive` rule (`UNIVERSAL_RULES`) under demand (chain closes the
   demand set, `apply_to_fixpoint` runs it, `apply.py:403` notes the transitive rule terminates). So
   GoalSolver's `Walker` is a PERF-SELECTIVITY optimization, **NOT a correctness requirement**.
   `walk_on_demand` is therefore a later perf refinement, not a migration blocker.

### `ask_goal`'s three query shapes and their firmware cover

| `ask_goal` shape | today (GoalSolver) | firmware cover | gap? |
|---|---|---|---|
| **yes/no** (`is S C`) | `bool(solver.solve(Goal(p,s,o)))` → verdict | `check(...).collapse()` (== verdict, fact 1) | none — drop-in |
| **existential** (`is anyone happy`) | `solve(Goal(p, None, o))` non-empty | `check` with wildcard subj (`_present` does ∃) | none |
| **who** (`who is a Y`) | `solve(Goal(p, None, o))` → enumerate subjects | chain the demand → materialize → read witnesses | **G1: needs a thin firmware witness-gather** |
| **n-ary / why** | already falls back to forward `ask` (NOT GoalSolver) | unchanged | none — not on the goal path |

## The gaps to close (precise)

- **G1 — witness enumeration for "who".** `check` returns a VERDICT, not bindings. But chain materializes
  every goal-predicate fact into the graph, so the witnesses are readable off it afterward (like the
  probe's `has_is_a`). Needs a thin firmware entry — a `witnesses(fact_g, rule_g, goal)` / `gather` that
  runs the demand-driven chain and returns the binding set. Small (chain + read-off), NOT a new engine.
- **G2 — transitivity PERF (not correctness).** Rule-based transitivity is correct but runs `is_a.transitive`
  forward to fixpoint under demand — O(closure) firings, the "expensive all-ground-anchor rule" the
  walkers doc warns about. Fine at session scale; if a large bank makes it bite, point the transitive
  demand at `walk_on_demand` (the selective walker). PERF follow-on, gated on a profile, NOT this phase.
- **G3 — negation parity. ⚠ CONFIRMED BLOCKER (2026-07-11).** The step-1 `witnesses` differential is GREEN
  (500+ checks, positive banks). But an ATTEMPTED flip of `ask_goal` (step 3, since reverted) failed 3
  `test_isa_ask` negation tests: over a `decided_negation=False` closed-world bank the firmware wrongly
  answered `ada is thief: yes` (must be `no`). ROOT CAUSE: **APPLY/CHAIN are positive-only (`apply.py:21`)
  — they read the `nac` role but do NOT enforce it.** GoalSolver honors NAC via stratified NAC-AS-COMPLETION;
  the firmware's INTENDED replacement is DECIDED NEGATION (`decide.solve` materializes `is_not` as positive
  facts, so the NAC becomes a positive match the firmware handles). So the 3 tests pin the GoalSolver-specific
  NAC-completion path. This is the real fork (see §7 crux 4) — NOT closeable by a filter-at-EMIT (unsound
  under semi-naive fixpoint: the NAC fact may be derived a later round).
- **G4 — differential parity BEFORE deletion.** Extend the Phase 4.4 differential gate (`chain_sip` ==
  `GoalSolver` on ProofWriter-positive) to the FULL `ask_goal` surface: yes/no + existential + who +
  negation + transitive, over a randomized query set. GoalSolver stays as the differential ORACLE through
  the migration (the rewriter/Phase-6.0 pattern), deleted only when this is green.

## Migration steps (for the executing session)

1. **Firmware witness-gather (G1).** Add `witnesses(fact_g, rule_g, goal, *, open_preds=…)` (in `check.py`
   or a new `gather.py`): run the demand-driven chain for the (free-endpoint) goal, return the binding
   set. Unit-test it directly against `GoalSolver.solve` on who-queries. Suite green.
2. **Differential gate (G4).** A test that runs `ask_goal`-via-firmware vs `ask_goal`-via-GoalSolver over
   a randomized query set (yes/no, existential, who, negation, transitive) and asserts identical answers.
   Any divergence is a real gap → fix (likely G3) or record as an accepted firmware-semantics change per
   the no-equivalence ratification. This is the GATE for step 3.
3. **Flip `ask_goal` onto the firmware.** `yesno`/existential → `check(...).collapse()`; `who` → the
   witness-gather; n-ary/why unchanged (already forward `ask`). Keep `GoalSolver` importable as the
   differential oracle (behind the step-2 test only). Full suite green. **At this point GoalSolver has NO
   production consumer.**
4. **Confirm GoalSolver + reference `Walker` are unreferenced in production.** `goal.py:407`'s `Walker`
   use dies with GoalSolver; the reference `Walker`/`walk_to_goal` (`walker.py`) then has only test +
   bench consumers (the in-graph `walk_on_demand` is separate and STAYS).
5. **Delete.** Remove `GoalSolver`, `solve_goal`, `solve_all`, `Goal` (if unused elsewhere), the reference
   `Walker` + `walk_to_goal`, and their `__init__` exports. Migrate the 18 GoalSolver-referencing test
   files (~156 refs): tests pinning GoalSolver as the differential oracle convert to direct firmware-pinned
   assertions (per the no-equivalence ratification, exactly as Phase 6.0 did for the ~15 rewriter files);
   tests of GoalSolver INTERNALS with no firmware analog (staleness/cache/`_sa_union`, `test_isa_goal_walker_linear`,
   the adversarial goal-order tests) either re-target the firmware invariant they were really protecting,
   or delete if the invariant is GoalSolver-specific. Update `architecture.md` / `reference.md`.

## Test blast radius (2026-07-11)

18 test files reference `GoalSolver`/`solve_goal`/`solve_all`/`ask_goal` (~156 + 17 refs). Grouped:
- **Ask-surface tests** (`test_isa_ask`, `test_riddles`, `test_contract`) — re-point at firmware `ask_goal`;
  behavior should be identical (that is what step 2 gates).
- **GoalSolver-semantic tests** (`test_isa_goal*` — ~9 files: nac, predicate_nac, existential_nac, graded,
  seed, semi_naive, adversarial, walker, walker_linear) — these pin the OLD engine's behavior. Per the
  no-equivalence ratification, convert the ones protecting a REAL reasoning invariant (negation, coref,
  transitivity answers) into firmware assertions; delete the ones testing GoalSolver-internal mechanics
  (cache staleness, join order, the Python Walker's linear-recursion) that the firmware realizes differently.
- **Firmware/differential tests** (`test_isa_check`, `test_isa_firmware_gate`, `test_isa_trace`) — already
  firmware-side; drop the GoalSolver differential arm once step 2's gate subsumes it.

## Risks

- **A who-query answer the firmware can't reproduce** — surfaced by step 2's differential; the fix is G1/G3,
  not restoring GoalSolver. Expect one or two (the Phase-2.5 pattern).
- **Transitivity blow-up on a large bank** (G2) — a PERF risk, not correctness; mitigation is `walk_on_demand`,
  deferred to a profile. Does not gate deletion at session scale.
- **Over-deleting a test that protected a real invariant** — the mitigation is step 5's per-file triage
  (re-target vs delete), NOT a blanket delete. The differential (step 2) is the safety net: it must be
  green on the firmware path BEFORE any GoalSolver test is touched.
- **`Goal` dataclass reuse** — verify `Goal` isn't used by firmware/tests independently of GoalSolver before
  removing it (it may stay as a plain goal descriptor).

## §7 — Crux questions for the user to ratify BEFORE code

1. **Keep GoalSolver as a temporary differential ORACLE through steps 1–4, delete only in step 5
   (recommended — mirrors the rewriter/Phase-6.0 retirement), or cut over and delete in one move?**
   Recommendation: keep it as the oracle through the migration; the differential (step 2) is what earns
   the deletion. One-shot deletion loses the safety net for no real gain.
2. **Where does the "who"/binding surface live — a thin new firmware `witnesses`/`gather` entry
   (recommended), or extend `check` to optionally return bindings?** Recommendation: a separate
   `witnesses`/`gather` — keep `check` a verdict, add enumeration as its own mode (mirrors the
   CHECK/CHOOSE separation), so the verdict path stays simple.
3. **Is retiring the reference `Walker`/`walk_to_goal` in scope for THIS phase (delete with GoalSolver —
   recommended, its only non-test consumer is GoalSolver), or kept as a standalone utility?** Recommendation:
   delete with GoalSolver; the in-graph `walk_on_demand` is the real walker and STAYS. (This also retires
   the O(N)-per-call name-index wart found in `Walker.__init__` during the 2026-07-11 measurement pass.)

4. **NEW — how to handle the NAC/negation gap (G3), the confirmed blocker.** The ask-flip needs closed-world
   negation the firmware doesn't yet do. Three options:
   - **(a) Decided-negation-only (recommended).** The firmware's negation model IS decided negation
     (`decide.solve` → positive `is_not`). Make `ask_goal` reason over decided-negation rules (or run
     `decide.solve` in the ask path) so the firmware's positive chain handles it; RETIRE the
     `decided_negation=False` NAC-completion path with GoalSolver, re-targeting/deleting the 3
     GoalSolver-specific tests per the no-equivalence ratification + [[delete-old-code-aggressively]].
     Smaller, aligned with the ratified negation design; risk = verifying decided-negation gives correct
     closed-world answers on those banks before deleting the tests.
   - **(b) Firmware NAC support.** Add stratified NAC to APPLY/CHAIN (the general Phase-5 mode). Bigger,
     correctness-critical (NAF + stratification), but makes the firmware a true GoalSolver superset.
   - **(c) Defer the flip.** Land `witnesses` (done), leave `ask_goal` on GoalSolver until (a)/(b) lands.

### STATUS 2026-07-11 (as-built)
Step 1 (`check.witnesses` + differential) DONE, green (343 tests). Step 3 flip ATTEMPTED → reverted
(G3 blocker). Next decision = crux 4. `witnesses` stays regardless.

Answer the crux questions, and the executing session runs §Migration.
