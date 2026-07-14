# Demand-driven negation — design (Phase 6.2 / firmware v3)

> **Status: BUILT (2026-07-11); perf follow-on landed 2026-07-12.** All six migration steps landed;
> `ask_goal` is demand-driven; the forward `decide.solve` apparatus is deleted. The 2026-07-12
> endpoint-driven `_facts_matching` perf fix (plan item 0', lever (a)) is AS-BUILT §6. See the AS-BUILT
> section at the end for the deviations the implementation forced (they matter) — §§1–5 are firmware v3
> itself, §6 is the perf follow-on. The prose below is the original proposal, kept as rationale.

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

## AS-BUILT (2026-07-11) — what the implementation forced

The mechanism landed as designed (NAF in `chain_sip._nac_blocks`: nested negative demand → positive
closure → absence decides; fuel→UNKNOWN via a shared `_Exhaustion` flag → `check.py`'s 4-status). Five
deviations/additions that the design under-specified and that a future reader must know:

1. **Stratification lives at LOAD, not as a runtime raise.** The design said "port `_completing`/
   `NonStratifiable` into the chain, raise on a negative cycle." A runtime ground-goal cycle guard
   FIRES SPURIOUSLY on stratifiable banks: closing a negative's positive can transiently re-demand that
   same negative through a HIGHER-stratum, non-productive rule — e.g. the coref rule `?s is ?b when ?a
   same_as ?b and ?s is ?a` raises a wildcard `is(bo, ?)` demand that pulls in the `is`-producing
   `thief` rule, whose NAC re-demands `not cleared(bo)`. That is not a real cycle (object-aware analysis
   puts `thief` strictly above `cleared`). The correct arbiter is the EXISTING object-aware
   `authoring.lint_stratifiable` (run at `load_corpus`/`load_rules`): it accepts THIEF and rejects
   `p:-¬q, q:-¬p`. So the chain PRUNES-and-CONTINUES on re-entry (block the higher-stratum rule, don't
   recurse) — sound under the load-time guarantee. `NonStratifiable` is retained as a type but the chain
   does not raise it. This is a genuine improvement over the proposal, not a shortcut.

2. **NAC-closure MEMO (perf, load-bearing).** Without it a wildcard query is ~17× slower: the round loop
   re-services each demand every round, re-running each NAC's full nested closure per env per round. A
   shared `_closed` set (threaded `chain_sip`→`_solve_demand_rule`→`_nac_blocks`) closes each negative's
   positive ONCE per session (sound: facts are monotone + stratified, so the closure is stable). Also:
   `chain_sip` drives from a LOCAL agenda, never `bound_demands(rule_g)` (that scan-in-the-hot-path was
   itself quadratic); visible `<demand>` trace nodes are minted only at the top level.

3. **Graded α-cut is reified into the chain.** `write_rule` now reifies `GradedCondition`s
   (`<rule> -graded-> <graded>` with `gc_var`/`gc_dim`/`gc_threshold`); `chain._graded_ok` applies the
   α-cut DURING matching (the Phase-5.2 companion, forced because ICE_CREAM's `?c is urgent when … ?c is
   very urgent` otherwise fires for every customer — the graded filter was silently dropped). Inverted
   α-cut ('not at all') is still deferred, as in `lowering.lower_graded`.

4. **A NAC identical to a head atom is an IDEMPOTENCY memo, not negation.** `?a rel ?c when … and not
   ?a rel ?c` (the transitive check-before-derive guard) is dropped from the NAC set — the monotone
   chain already refuses to re-derive an existing fact, and treating it as NAF would flag a self-cycle.

5. **`why` provenance is order-sensitive (follow-on).** A fact derived by an earlier non-provenance
   query (e.g. `who is thief`) has no in-graph justification, so a later `why` on the SAME graph renders
   `(given)`. Workaround in use: ask `why` on a fresh `load_corpus` (the demand then re-derives WITH
   provenance). A robust fix (always-provenance, or re-derive-on-fresh-copy for `why`) is deferred —
   it trades perf for order-independence.

6. **ENDPOINT-DRIVEN `_facts_matching` (2026-07-12 perf follow-on — plan item 0', lever (a)).** The
   original `_facts_matching(pred, subj, obj)` scanned EVERY `pred` fact and recomputed each one's
   endpoint names to discard all but the one bound subject/object — a linear per-predicate scan on the
   hottest inner loop, and the top of the profile (`_endpoints`/`name` at ~850k/911k calls for a
   12-suspect wildcard `who is thief`). Because SIP means a demand almost always carries a bound
   endpoint, the fix reaches the matching facts THROUGH that endpoint's node: the bound name resolves to
   candidate nodes via the `name` value-accelerator (`nodes_named`, a candidate SET to test — never
   identity, so the label-less discipline of `attrgraph.py` holds), then local topology
   (`succ`/`pred` over the 2-hop reification) yields the `(pred,subj)` / `(pred,obj)` facts directly. A
   `_rel_matches_pred` helper carries the per-rel visibility half of `_fact_relnodes` (keyed, non-inert,
   control only as the active SUPPOSE-scope pencil) so the endpoint-driven paths are behaviour-identical
   to the scan; the whole-predicate scan remains the fallback ONLY for a fully-unbound demand. Result
   (identical answers, verified on the suite + the differential): under cProfile at 12 suspects/6
   aliases 6.18s→0.565s (call count 9.9M→0.98M); the full suite ~90s→~54s. The remaining levers named in
   item 0' — semi-naive worklist (re-service a demand only when a relevant fact appeared) and the coref
   demand fan-out — are un-started; at session scale the query is now sub-second, so they stay Phase 7.
