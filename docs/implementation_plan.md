# Implementation Plan — Universal Graph Machine

> **Status: THE ACTIVE PLAN (2026-07-11, post repo-split).** This is the UGM-only continuation of
> the original `harneskills` plan. All ISA engine, firmware, CNL surface, and substrate work lives
> here. The harness (planning rule banks, SLM, session, TUI) has its own plan in `harneskills`.
>
> Module paths after split: `ugm.xxx` (was `harneskills.isa.xxx`); `ugm.cnl.xxx` (was
> `harneskills.xxx` for CNL-level modules). Tests: `ugm/tests/`. Source: `ugm/ugm/`.
>
> Read first: `reference.md` → `vision.md` → `logic_fragment.md` → `processing_modes.md`
> → `graph low level machine/isa-reference.md`. Log landed work in `CHANGELOG.md`.
>
> Standing rules: no commits by the assistant; domain logic ONLY in banks; strategies are
> DECLARED data, never engine sniffing; correctness before raw performance.
>
> **RATIFIED 2026-07-10 (user): EQUIVALENCE WITH THE PREVIOUS (rewriter / name-based) GENERATION IS NOT
> A CORRECTNESS TARGET.** The old generation was never used. `rewriter.py` + the `TEMPORARY BRIDGE`
> dual-write are a DEV CONVENIENCE (a handy oracle while building), NOT an equivalence contract — retire
> them freely when they get in the way. The goal is a **WORKING, self-consistent firmware system**, judged
> on producing sensible answers on the benches, NOT on reproducing the old exhaustive engine's outputs.
> GoalSolver stays only as a *development* oracle for the firmware (no old-answer-preservation constraint).

## NEXT STEP (pick this up FIRST)

**Suite: 460 passed, 0 failed** (post repo-split, 2026-07-11, `python -m pytest -q`).

**Phase 5.5 slices 1–2 (CHECK+CHOOSE as `<call>` calculators), 3a, 3b DONE.** See Phase 5.5 details.

**PICK UP NEXT — recommended order:**
1. **Phase 6.0** — retire `rewriter.py` + `TEMPORARY BRIDGE` dual-write + reader flips. ✓Sonnet,
   mechanical, unblocked by the no-equivalence ratification. Do this FIRST — it shrinks the codebase
   and clears the oracle debt before the judgment-heavy firmware work.
2. **Phase 5.5 slice 4** — plan→act→check→replan as ITERATE×CHECK over `<check>` verdicts. ⚠Opus —
   "reuse the existing execution loop in `solve.py`, don't rebuild" is exactly the judgment Sonnet
   tends to violate.
3. **Phase 5.5 slice 3c** — SUPPOSE scope authoring in CNL (deferred from 3b). ⚠Opus.
4. **Phase 5 exit gate** — benches produce sensible, self-consistent answers on firmware semantics.

**Model routing** — ⚠Opus = needs vision-judgment; ✓S = Sonnet-safe where a gate/spec catches deviation.
- Slice 4 (plan→act→check→replan): **⚠Opus**
- Slice 3c (SUPPOSE CNL scope authoring): **⚠Opus**
- 5.5 exit gate (classify divergences): **⚠Opus**
- Companion: graded α-cut DURING matching **⚠Opus**; aggressive `is_not` completion **⚠Opus**;
  wire `chosen` as declared CHOOSE **~✓S** (gated)
- Phase 2.3 / 2.4 (name→valued attr; name-free identity tokens): **✓S** — mechanical, differentially gated
- Phase 2.5 (COPULA/NEG_SUFFIX / `solve.py` preds → KB declarations): **⚠Opus** for "what's KB vs engine"
- Dual-write bridge removal + rewriter retirement: **✓S** sweep (decision to retire is Opus/user)
- Phase 3.1 step 2 (one-graph fold): **⚠Opus** — control/fact segregation. 3.2/3.4: **⚠Opus**
- Phase 6 demotion decisions **⚠Opus**; `architecture.md` rewrite **✓S**
- Phase 7 perf: **✓S** with benchmarks for mechanical rungs; **⚠Opus** for design + AOT codegen

**EQUIVALENCE NOT REQUIRED (2026-07-10 ratification) — consequences in force:**
- Retire `rewriter` oracle + `TEMPORARY BRIDGE` dual-write NOW (unblocks 2.2/2.3 reader flips)
- 5.5 exit gate COLLAPSES: "classify every divergence" → "firmware sensible + self-consistent on benches"
- Keep GoalSolver as DEVELOPMENT oracle only; demote/delete on firmware coverage alone
- Real long-pole for a *usable* system = **performance (Phase 7)**, not correctness
- Impossible-blocker chance < 5%

## Where the system is (2026-07-11, post repo-split)

**460 tests green.** All ISA engine files are in `ugm/ugm/`; CNL surface in `ugm/ugm/cnl/`.
The planning rule banks (`PLANNING_RULES`, `SOLVE_RULES`, etc.) and harness benches live in `harneskills`.

**PRODUCTION RUNTIME IS 100% THE ISA ENGINE.** No production path calls the reference `rewriter` at
runtime. `rewriter.py` is RETAINED as a differential-test oracle only. Every `run_rules` caller in
production passes `isa=True`; the `isa=False` branch is dead in production.

Phases 0–5.5 slices 1–3b are DONE. See CHANGELOG.md for the full trail.

Companion slices still open (not blocking 5.5 slice 4): graded α-cut DURING matching in APPLY/CHAIN;
aggressive `is_not` completion (`decide.solve`'s write-side elimination); wire the planner's `chosen`
pick (`solve._mint_chosen`) as a declared CHOOSE.

Also still open (NOT on firmware path): Phase 3.1 step 2 (one-graph fold); Phase 2.3 name demotion
(oracle-blocked); `tests/test_joern_corpus.py` (legitimately slow, live-Joern, candidate for `slow` marker).

---

## Phase 0 — ONE ENGINE: finish the peel, delete `rewriter` ✅ COMPLETE

All items DONE (2026-07-07/08, 465 tests). Key landmarks:

- **0.1** `run_bank` optimized (name-index SEED + bound-endpoint join driving; 89×→2.6× on planning.cnl)
- **0.2** All recognizers onto `run_bank` (rule loaders, `load_facts`, `load_corpus`)
- **0.3** Planner control onto ISA: `DROP_CTRL` lowering + control-stamp-at-MINT
- **0.4** Graded/coref reasoning passes onto ISA (`_coref_propagation`, `graded_rules`)
- **0.5** All production callers on `isa=True`; `rewriter.py` retained as TEST ORACLE only

---

## Phase 1 — STABILIZE the oracle ✅ COMPLETE

All items DONE (2026-07-08, 470 tests).

- **1.1** `GoalSolver` staleness fixed (`_sa_union`, `_token_class`, nested-solver identity caches)
- **1.2** `_group_satisfiable` cached safely (epoch-validated, monotonic invalidation)
- **1.3** Stratification LINT at bank load (`authoring.lint_stratifiable` wired into loaders)
- **1.4** Adversarial tests (`tests/test_isa_goal_adversarial.py`): goal-order independence,
  derived-`same_as`, cache staleness, `NonStratifiable` regardless of asking order

---

## Phase 2 — ATTRIBUTE-NATIVE conventions (namelessness for real)

- **2.1 DONE (2026-07-08, 470 green).** Predicates as graded KEYS (`{chase: 1.0}` on rel node);
  `add_relation` mints the predicate key; `nodes_with_key`/`has_key` replace name-equality tests
  in `lowering`, `goal`, `solve`. TEMPORARY BRIDGE dual-write (also writes legacy VALUED `name`)
  kept until Phase 6 oracle retirement. Reserved-key collision (`name` predicate) guarded.

- **2.2 DONE (2026-07-09, 478 green) — both halves.**
  - HALF 1: control-token dual-write — `add_node("<goal>")` also writes `{<goal>: 1.0}` key
  - HALF 2: `add_node` control-flag at mint chokepoint — reserved `<…>` syntax ⟹ `control=True`
  - `_is_inert`→`.inert` flag migration COMPLETE for all non-oracle, non-bridge sites
  - **REMAINING = Phase-6 reader flip only** (blocked on oracle): `nodes_named("<tok>")`→
    `nodes_with_key`, `startswith("<")`→`is_control` in `forms.py:473/507/548`, `universal.py:90`

- **2.3** `name` demoted to ordinary VALUED attr; value-accelerator indexes for KB-declared
  discriminating keys only. BLOCKED on oracle retirement (Phase 6.0).

- **2.4** Identity tokens name-free (coref-class representative nid, not `name\x00rep`);
  rendering to surface at the output boundary only.

- **2.5** `COPULA`/`NEG_SUFFIX` and `solve.py`'s predicate list → KB declarations.
  Exit gate: engine code grep-clean for predicate/key strings; benches green.

---

## Phase 3 — RULES AS DATA (homoiconicity)

> SCOPING DECISION (2026-07-09): Phase 3 is done AS PREREQUISITE FOR Phase 4's firmware — the
> firmware needs the reified rule SHAPE, NOT the "built by FORM rules" authoring. The meta-circular
> FORM-rule authoring (the quote/eval wall) is DEFERRED as a homoiconicity-purity milestone off the
> critical path.

- **3.1 STEP 1 DONE (2026-07-09, 478 green).** `rule_graph.write_rule` modernized: rule/var/pattern
  nodes are `control`-flagged; each pattern atom built in FACT SHAPE via `add_relation` (predicate
  as graded key), so APPLY can seed through `nodes_with_key` exactly as for facts.
  TRACKED: `same_as propagates through X` CNL surface lands here (needs coref rules reified;
  `coref_prop` is forward-compatible — will become a graph attribute at the same read site).

- **3.1 STEP 2 NEXT:** demonstrate/prove pattern nodes stay fact-INVISIBLE when rule fragment is
  folded into a live fact graph (control flag = segregation) — the one-graph fold.

- **3.2** Runtime rule edits by user CNL: add = same path as facts; disable = additive `<disabled>`
  marker; re-enable = control-layer op. No rule deletion (§5 monotonicity).

- **3.3 DONE (2026-07-09, 487 green).** Head index as graph structure: `<head-index>` hub with
  `hub -[headPred]-> rule_node` per head predicate. Built by `apply.build_head_index` / `rules_producing`.

- **3.4** Collections as first-class KB structure: member `next`-chains + list-authoring CNL forms
  (the ITERATE substrate — `processing_modes.md` §1).

  Exit gate: every bank rule round-trips CNL → rule subgraph → rendered CNL.

---

## Phase 4 — FIRMWARE v1: APPLY + CHAIN (the positive core) ✅ COMPLETE

All items DONE (2026-07-09/10). Gate met.

- **4.1 DONE** — all four gadgets: `<frame>` (bindings), `<current-atom>` cursor over `next`-chain
  itinerary, `<fresh>` semi-naive delta, bound-tuple SIP `<demand>` at CHAIN-side.

- **4.2 DONE** — `apply_rule` / `apply_to_fixpoint` (`ugm/apply.py`): reified-rule match with
  VISIBLE `<frame>` bindings, df-seeded, semi-naive, fuel-bounded. Differentially gated vs `run_bank`.

- **4.3 DONE** — `chain` / `chain_sip` / `demand_closure` (`ugm/chain.py`): demand-driven sub-goaling
  through `<head-index>`, bound-tuple SIP (SUBJECT/OBJECT pruning). Gated: derives exactly the
  goal-predicate facts `run_bank` derives, never applies irrelevant rules.

- **4.4 DONE** — trace renderer: `RECORD` (mode 9) mints `<j:rulekey>` justifications at every
  APPLY/CHAIN EMIT, byte-identical to `run_bank(provenance=True)`; renders via existing `surface.explain`;
  `render_demands` shows the bound magic set as CNL.
  **Exit gate met**: `chain_sip` == `GoalSolver` on a randomized ProofWriter-positive slice (1000+ checks).

---

## Phase 5 — FIRMWARE v2: the psychology leaves Python

- **5.1 DONE (2026-07-10).** CHECK: `check(fact_g, rule_g, goal, open_preds=…)` → 4-status verdict
  (POSITIVE / ENTAILED_NEG / ASSUMED_NO / UNKNOWN) over `chain_sip`. `collapse()` == `ask_goal`
  verdict. `explain_check` renders "where I looked." `ugm/check.py`, `tests/test_isa_check.py`.
  COMPANION (open): AGGRESSIVE `is_not` completion (`decide.solve`'s write-side elimination).

- **5.2 DONE (2026-07-10).** CHOOSE: `choose(g, goal, alpha=…)` = graded α-cut argmax (nothing-beats-it,
  MONOTONE, ties→all win). `ugm/choose.py`, `tests/test_isa_choose.py`. Gated on design fixtures +
  200-seed randomized argmax differential.
  COMPANION (open): graded α-cut DURING matching (APPLY/CHAIN body — lifts off positive-only on graded
  axis); wire `solve._mint_chosen` as a declared CHOOSE.

- **5.3 DONE (2026-07-10).** SUPPOSE: `<hypothesis>` scopes — pencil writes, `chain_sip` in-scope,
  CONFIRM→ink / REFUTE→drop_scope, ink monotone. `ugm/suppose.py`, `tests/test_isa_suppose.py`.
  Scope-aware matching as `scope=` param on `apply`/`chain` fact readers, gated behavior-NEUTRAL.

- **5.4 DONE (2026-07-10).** Declared strategies replace shape-sniffing: walker/transitive (`R is
  transitive` → `_closure_declarations`), coref-follow (`coref_prop` flag on `Rule` read by
  `GoalSolver`, not key-sniffing). All three sniffers deleted. `ugm/cnl/machine_rules.py`, `ugm/goal.py`.
  TRACKED RESIDUAL: `session.py:CONTENT_PREDS` + Python-generated coref rules → Phase 3 (bank-authored
  `same_as propagates through X`) once coref rules reify.

- **5.5 KB procedures** — named compositions of modes, authored in CNL, run as control-token programs.

  - **Slices 1–2 DONE (2026-07-10).** CHECK + CHOOSE as `<call>` calculators. `ugm/mode_calls.py`,
    `tests/test_isa_mode_calls.py`. Reuses the existing `<call>` loop; NOT a new driver.

  - **Slices 3a–3b DONE (2026-07-10).** Rules emit mode-calls, existing loop services them, verdict
    feeds back. Key-aware INTERN fix (MINT skips reified domain-relation candidates, retires the
    predicate-literal aliasing sharp edge). Zero new CNL surface, zero SLM debt.

  - **Slice 3c (OPEN)** — SUPPOSE scope authoring in CNL (deferred from 3b; variable-length
    assumptions/predictions). ⚠Opus.

  - **Slice 4 (OPEN — NEXT FIRMWARE TASK)** — plan→act→check→replan expressed as ITERATE×CHECK
    over `<check>` verdicts. Compose the EXISTING execution loop in `solve.py` with mode-calls.
    Do NOT rebuild the driver. ⚠Opus.

  **Exit gate (DOWNGRADED per 2026-07-10 ratification):** engine grep-clean (no strategy selection
  in Python); benches (card-trader + coref + riddles, now in `harneskills`) produce SENSIBLE,
  SELF-CONSISTENT answers on firmware semantics. No longer requires divergence-from-old-exhaustive
  classification.

---

## Phase 6 — DEMOTE the Python solver; docs converge

- **6.0 NOW-UNBLOCKED — pull FORWARD (✓Sonnet).** Retire `rewriter.py` + `TEMPORARY BRIDGE`
  dual-write. Then sweep the reader flips they blocked: `nodes_named("<tok>")`→`nodes_with_key`;
  `startswith("<")`→`is_control` (`ugm/cnl/forms.py:473/507/548`, `ugm/cnl/universal.py:90`);
  2.3 name demotion; delete `_INERT_NAMES`/`_is_inert`. All differentially gate-able against a
  KEPT GoalSolver (dev oracle). Do this BEFORE judgment-heavy firmware work.

- **6.1** GoalSolver (or its remains) = ACCELERATOR only where profiling justifies; deleted where
  firmware subsumes it (coverage alone — NOT old-answer equivalence).

- **6.2** Rewrite `architecture.md` as the as-built description of THIS system; `reference.md`
  doc-map refreshed; finished phases summarized into `CHANGELOG.md`.

---

## Phase 7 — PERFORMANCE track (after correctness — user standing rule)

In leverage order:
- **(a)** Intern keys/values to ints, CSR adjacency, bitset candidate sets
- **(b)** Rust (PyO3) inner loop for Machine + store; Python stays the shell
- **(c)** Per-rule AOT codegen = partial evaluation of APPLY (Soufflé-style), differentially gated
- **(d)** Two-tier execution for runtime-edited rules — fresh rules interpret, stable-hot rules
  compile in background, version-stamp invalidation on edit. JIT (Cranelift/copy-and-patch before
  LLVM) only if profiling demands it.

---

## Risks

- **Slice 4 judgment** — "reuse the loop, don't rebuild" is a vision call, not a mechanical task.
  Use Opus; gate the result on sensible plan→act→check→replan behavior on the benches.
- **Performance (Phase 7) is the real long-pole** for a usable system post the no-equivalence
  ratification. Correctness risk is < 5% impossible-blocker; performance is the open question.
- **Meta-debugging** — the Phase 4 trace renderer is the mitigation; it is complete.
- **SLM surface debt** accumulates from CNL form changes in Phases 2/3/5 — batch retrains via
  the ledger in `harneskills` (`handoff_slm_surface_track.md`).
- **One-graph fold hazard (Phase 3.1 step 2)** — ephemeral APPLY frames add incoming edges to
  fact nodes; previewed and controlled by GC-after-pass, but the full fold needs care.
