# Demand-driven negation — design (Phase 6.2 / firmware v3)

> **Status: PROPOSAL (2026-07-11) — written to be EXECUTED by a fresh session.** Motivation ratified by
> the user: **we are building a bounded reasoning AGENT, not a theorem prover.** A human decides a
> negation by ASKING the positive when the question comes up and taking absence-of-evidence as the
> answer — demand-driven CWA — NOT by eagerly completing every `is_not` fact and retracting the wrong
> ones (the theorem-prover's closed-world completion). This note replaces the forward
> completion+defeat+retract apparatus for negation with **stratified negation-as-failure evaluated on
> demand inside `chain_sip`**. Companion of `goalsolver_retirement_design.md` (Phase 6.1). See
> [[delete-old-code-aggressively]].

## The insight

Negation is a QUESTION you ask, lazily, at the point a rule needs it:

- `?x is thief when ?x is a suspect and ?x is not cleared` — to decide `thief(ada)`, bind `ada` from
  `suspect(ada)`, then **demand `cleared(ada)`**; its demand-closure comes back empty → `not cleared`
  holds → `thief(ada)`. No `is_not` fact is ever materialized; nothing is completed or retracted.

The current firmware instead runs FORWARD decided negation (`decide.solve`): AGGRESSIVELY materialize
`?c is_not cleared` for every suspect (`completion_rule`), then INTERPOSE-retract the ones a positive
`cleared` defeats (`DEFEAT_SEED` + `RETRACT_RULES`). That whole apparatus exists ONLY to make eager
forward evaluation sound. Demand-driven NAF needs **none** of it — it is answer-equivalent AND strictly
simpler.

This is also why the model is right for THIS system: bounded, on-demand, ask-when-needed (vision §6a/§11/
§14, `walkers_and_locality.md`) — the cognition model, not the exhaustive-solver model.

## What it RETIRES (net simplification, not new machinery)

- `decide.completion_rule` + the `_completion_rules` generation in `authoring.expand_rules`.
- `decide.DEFEAT_SEED` and the negation use of `retraction.RETRACT_RULES` (retraction the MECHANISM
  stays — it is still used for real belief revision / `RESTORE`; only its role as negation-defeat goes).
- `decide.solve` as the answering path (it may reduce to nothing, or stay only as an optional bulk
  forward-materialize helper — see §Crux).
- The `is not P` → positive `is_not P` UPGRADE in `_expand_rule_node` (`_is_cw_negation`): a closed-world
  `not P` clause stays a NAC and is decided on demand, NOT upgraded + completed.

## The mechanism — stratified NAF in `chain_sip`

Today `chain_sip` is positive-only (`apply.py:21`): it services `<demand>`s by applying positive rules.
Add ONE capability: a rule body NAC clause `not L(binding)` is serviced by a **nested negative demand**.

1. **Sub-goal the positive.** When the demand-driven evaluation of a rule reaches a NAC clause `not L`
   with its variables bound (by the positive body matched so far), spawn a NESTED demand for `L`
   (bound-tuple, via the existing `chain_sip` machinery / `<demand>` magic set).
2. **Run it to CLOSURE.** The nested positive demand runs to genuine fixpoint within its stratum.
3. **Absence decides.** No `L`-fact in the closure ⇒ `not L` holds ⇒ the rule fires. Any `L`-fact ⇒
   the NAC fails for that binding.
4. **Monotone, no `is_not`.** Nothing is materialized for the negative; the verdict is computed from the
   (empty) demand-closure — exactly how `check.py` already computes a top-level `ASSUMED_NO` (§ this is
   the SAME move, pushed inside rule bodies).

### Stratification (the hard, correctness-critical part)

NAF is only sound if the positive it negates is fully resolved FIRST. So:

- **Stratum ordering.** A NAC on predicate `L` may only be decided once `L`'s positive demand-closure is
  complete. The demand scheduler must resolve the `L` sub-demand to closure before committing the
  negation — a negation frontier below the current goal's stratum.
- **Cycle detection.** `not P` transitively depending on `not P` is non-stratifiable — must raise (the
  deleted `GoalSolver._completing` frozenset + `NonStratifiable` are the reference implementation;
  reconstruct that logic in the chain's negative-demand path). NEVER silently return a wrong answer.
- **Reference:** git history of `ugm/goal.py` — `_complete_negative`, `_completing`, `_neg_of`,
  `NonStratifiable`. That was the correct demand-driven-NAF model; it lived in a duplicate ENGINE (rightly
  deleted, Phase 6.1) but belongs in `chain_sip` as firmware.

### Fuel makes "unknown" honest (a bonus the forward model can't give)

NAF soundness needs the positive sub-demand EXHAUSTED. Under §14 fuel-bounding, if the positive
sub-demand runs out of fuel BEFORE closure, the honest answer is **UNKNOWN** ("I didn't finish looking"),
NOT a decided `no`. This falls straight out of `check.py`'s existing 4-status model (POSITIVE /
ENTAILED_NEG / ASSUMED_NO / UNKNOWN): a fuel-exhausted negative sub-demand is UNKNOWN; a fully-closed
empty one is ASSUMED_NO. The forward exhaustive model cannot express this distinction — it always claims
completeness. This is the agent-not-theorem-prover payoff made concrete.

## What STAYS forward (unchanged)

- **Recognition** — `_recognize` → `run_bank` (whole-batch CNL parsing; not reasoning).
- **Load-time structural materialization** — coref propagation (`_coref_propagation`), graded embeddings
  (`graded_rules` + `propagate_embeddings`), universal expansion (`every X is a Y` laws). These are
  eager by NATURE ("for all") and run once at load; they are not query-time answering.
- `run_bank`/`run_rules` — the substrate forward driver, retained for all of the above (and as the
  re-add path for optional bulk materialization).

## What we LOSE by dropping forward answering, and re-addability

- **Fully-derived snapshot.** After a forward pass, a RAW graph read is complete ("absent ⇒ not
  derivable"). Demand-driven, a fact is absent until demanded, so raw reads are unsound — all querying
  must go through the demand-driven `ask`. (Inspection/debug/export tools that read the graph directly
  must run a materialize pass first — which `run_rules` still provides.)
- **Eager bulk amortization** — one forward pass answers everything; demand-driven pays per query. BUT
  monotone persistence means demanded derivations STAY in the graph, so it is lazy/incremental
  amortization, not lost work — often better (first query cheap, later queries reuse).
- **Nothing for negation correctness** — demand-driven NAF is answer-equivalent to decided negation on
  every stratifiable bank (the differential gate, below).
- **Re-addability: HIGH.** `run_rules` never leaves (recognition needs it). The retired negation rules
  are declarative + a thin driver, reconstructable from git + this note. Dropping them is not a one-way
  door; keeping a dead parallel forward-negation path IS the two-engine debt we just killed, so DELETE
  and reconstruct-if-needed, do not keep-just-in-case.

## Migration steps (for the executing session)

1. **Teach `chain_sip` to service a NAC clause via a nested negative demand** (positive-closure +
   absence-decides), single stratum first (no nesting). Unit-test on THIEF_CW-shaped banks.
2. **Add stratification + cycle detection** to the negative-demand path (port `GoalSolver._completing`/
   `NonStratifiable` from git into the chain). Test nested + cyclic negation banks.
3. **Fuel → UNKNOWN** on an unexhausted negative sub-demand; wire into `check.py`'s 4-status verdict.
4. **Differential gate:** for every stratifiable bank in the suite, demand-driven-NAF answers ==
   current forward `decide.solve` answers (yes/no/who). This EARNS the retirement. (Keep `decide.solve`
   importable as the throwaway differential oracle through steps 1–4, exactly the Phase-6.1 pattern.)
5. **Flip `ask_goal`** to the demand-driven chain (drop the `decide.solve` + read path); it is
   demand-driven again — locality restored, for the RIGHT reason (the model), not as an optimization.
6. **Retire the forward negation apparatus:** delete `completion_rule`/`_completion_rules`/`DEFEAT_SEED`,
   the `_is_cw_negation` upgrade, and (per §Crux) reduce/retire `decide.solve`. Migrate/delete the
   completion/defeat tests onto the demand-driven answers.

## Risks

- **Stratification is where wrong answers hide.** This is the one genuinely hard part; do NOT ship step 5
  before step 4's differential is green on nested + cyclic banks. Non-stratifiable ⇒ raise, never guess.
- **Performance of repeated negative sub-demands** — a NAC re-demanded per binding can be costly; monotone
  persistence + the fired/demand set mitigate, but profile on the coverage_audit bank.
- **Graded × NAF interaction** — a graded NAC (α-cut inside a negated clause) is out of first scope;
  keep the graded-α-cut companion (Phase 5.2) separate.

## §Crux — RATIFIED 2026-07-11 (user chose BOTH the aggressive option)

1. **Drop forward answering ENTIRELY** — `decide.solve` is retired as an answering path with NO
   `materialize()` helper kept. Inspection/export tools that need a fully-derived snapshot run
   `run_rules` themselves. (Reconstruct-from-git if ever needed; keeping a dead parallel forward path
   is exactly the two-engine debt Phase 6.1 killed.)
2. **Fold `ask` into `ask_goal`** — one demand-driven answering entry; `ask` stops being a distinct
   raw-materialized-graph reader.

Rationale: no second negation model, no two-engine debt — consistent with [[agent-not-theorem-prover]]
and [[delete-old-code-aggressively]]. So step 6 is a full DELETION, not a demotion.
