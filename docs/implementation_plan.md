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

**Suite: 341 passed, 1 skipped, 0 failed** (post Phase 5.5 slices 4 + 3c, 2026-07-11, `python -m pytest -q`).
The 460-passed figure logged at the repo split was inflated by ~123 tests that exercised harness-only
content (`SOLVE_RULES`/`PLANNING_RULES`/`Session`/CPG-mechanism banks) mistakenly carried over by the
carveout instead of staying in `harneskills`; those were trimmed/deleted (2 whole files, 99 functions
across 7 mixed files) before Phase 6.0 started. See CHANGELOG for both cleanups.

**Phase 5.5 slices 1–4 DONE (CHECK+CHOOSE as `<call>` calculators; rules-emit; SUPPOSE-call scope
authoring; plan→act→check→replan). Phase 6.0 DONE (rewriter retirement + reader flips — narrow scope,
see correction below).** See CHANGELOG.

**Phase 5.5 slice 3c DONE (2026-07-11) — SUPPOSE authored as a `<call>` mode.** A hypothesis carries
VARIABLE-LENGTH assumptions/predictions (why it couldn't be a fixed-slot call like CHECK/CHOOSE), so
`mode_calls.suppose_tool` takes N `assume`/`predict` REIFIED TRIPLES (`<t> -[k_subj/k_pred/k_obj]-> …`),
runs the firmware `suppose`, and folds a `<suppose>` verdict back — the 3a/3b shape extended to
list-valued args. Authored via the EXISTING machine-rule grammar (zero new prose forms, zero SLM debt);
prose `suppose … predict …` sugar is a tracked follow-on (like `to NAME`). `tests/test_isa_suppose_calls.py`
(6 tests). See CHANGELOG.

**Phase 5.5 slice 4 DONE (2026-07-11) — `solve.py` retired.** The plan→act→check→replan CONTROL FLOW is
now a KB-declared composition of ITERATE×CHECK over `<check>` verdicts, serviced by the EXISTING `<call>`
loop (`run_bank(..., tools=mode_registry(rule_g))`) — no new driver, no Python control flow, no predicate
name in engine code (`tests/test_isa_plan_act_check.py`, 4 tests). `solve.py` DELETED (it was export-only
inside `ugm`); its harness-side consumers migrate onto the declared composition cross-repo. KEY RESULT:
the monotone substrate needs NO driver-state reset — each op's CHECK is fired-suppressed per (op, want),
so an alternative op's positive verdict is independent of the diverged op's stale assumed-no, the same
teardown-subsumption Phase 2/3 found for `DROP_CTRL`. See CHANGELOG.

**PHASE 6.0 CORRECTION (2026-07-11) — the `TEMPORARY BRIDGE` dual-write is NOT rewriter-only.**
Before executing 6.0, tracing actual readers found the three "TEMPORARY BRIDGE" comments
(`attrgraph.py`'s `add_relation`, `lowering.py`'s `to_attrgraph` and `lower_rhs`) are wrong about
what blocks their removal: `machine.py`'s own `MINT` intern/dedup logic reads `attrs[NAME]`/
`g.name(rel)` directly, and dozens of production call sites (`apply.py`, `walker.py`, `choose.py`,
...) read a relation's predicate back via `g.name(rel)`. Dropping the legacy `name` write now would
break the live ISA engine, not just retire oracle support. **So the bridges were deliberately left
in place** — they're entangled with **Phase 2.3** ("name demoted to ordinary VALUED attr... KB-
declared discriminating-key indexes"), which is real design work (a new indexing-declaration
concept), not a mechanical sweep, despite its "✓S mechanical" routing below. What Phase 6.0 actually
did: deleted `rewriter.py` + its `isa=False` branch/re-exports (migrating ~15 dependent test files
onto `run_bank`/`run_rules`, converting differential-vs-rewriter assertions to direct ISA-pinned
ones per the no-equivalence ratification), and did the `nodes_named`→`nodes_with_key` /
`startswith("<")`→`is_control` reader flips. Also fixed a real pre-existing bug found along the way:
`run_bank` ignored `Rule.meta` (every firing minted provenance regardless of the flag, unlike the
oracle's `emit_prov = provenance and not rule.meta` guard) — now fixed in `lowering.py`.

**SLICE 4 SCOPE CLARIFICATION (2026-07-11, user-confirmed diagnosis) — RESOLVED, slice 4 now DONE (see
NEXT STEP). The diagnosis below stands as the rationale trail; the fix landed exactly as scoped here.**
Before starting slice 4, we
checked whether `solve.py` (the goal-directed planning driver) is genuinely `ugm`-scope firmware or
harness-only planning-application content that leaked into this repo's plan during the carveout — the
same class of bug Phase 6.0's own test-suite cleanup found for `PLANNING_RULES`/`SOLVE_RULES`. First
pass (vocabulary + test-coverage evidence: `solve.py` hardcodes `pre`/`add`/`del`/`cost`/`want`/
`chosen`/`before`/`ready`/`done`, duplicates `harneskills/planning.py`+`harneskills/isa/solve.py`
which ARE tested there, and has ZERO tests in `ugm/tests/`) argued for moving it to `harneskills`
wholesale. **That read was incomplete.** Reading `solve.py` directly: its actual solving MECHANISM is
`GoalSolver(ag, plan_rules, tools=tools).solve(Goal(...))` — the same ISA-native demand-forward
backward reasoner every legitimate `ugm` capability uses (`check.py`, `choose.py`), not a from-scratch
engine like the retired `rewriter.py`. So it is NOT pre-ISA legacy code, and NOT simply
misplaced-repo content.

**The real defect: `solve.py` violates the plan's own standing rule** ("domain logic ONLY in banks;
strategies are DECLARED data, never engine sniffing," line 13) — its driver hardcodes fixed predicate
NAMES straight into Python control flow (`graph.name(r) == "want"`/`"add"`/`"del"`/`"chosen"`/`"cost"`/
`"ready"`/`"done"`), exactly the shape-sniffing anti-pattern Phase 5.4 already eliminated for the
walker/coref strategies (`_is_transitive_closure_rule`, `_is_same_as_prop` → declared `rel_property`/
`coref_prop` flags). `solve.py` never got that treatment. This also matches the ALREADY-TRACKED
**Phase 2.5** item ("`solve.py`'s predicate list → KB declarations," line 150) and 5.5's own exit gate
("engine grep-clean — no strategy selection in Python," line 244) — slice 4 isn't a new direction,
it's the mechanism half of a fix Phase 2.5 already named the vocabulary half of.

**So slice 4 IS genuinely `ugm`-scope firmware work, reframed:** not "extend `solve.py` as-is with
mode-calls" (the original phrasing's ambiguity), but "retire `solve.py`'s Python-hardcoded
plan→act→check→replan CONTROL FLOW by expressing it as a KB-declared composition of ITERATE×CHECK
over `<check>` verdicts (`mode_calls.py`'s existing `<call>` loop — reuse, don't rebuild), the same
way Phase 5.4 retired the walker/coref sniffers." The planning-specific predicate VOCABULARY
(`pre`/`add`/`del`/`cost`/`want`) stays whatever a bank declares it to be — those banks (and any
STRIPS-flavored demo content) can legitimately live in `harneskills` as an APPLICATION of the generic
mechanism, same as `harneskills/planning_kb.py` already is for the forward planner. `solve.py`'s
Python driver becomes dead weight once the declared composition subsumes it, at which point it
retires like `rewriter.py` did — not before.

**PICK UP NEXT — recommended order:**
1. **Phase 5 exit gate** — benches produce sensible, self-consistent answers on firmware semantics.
2. **Phase 2.5** — `COPULA`/`NEG_SUFFIX` and the (now-retired) `solve.py`'s predicate VOCABULARY → KB
   declarations. Slice 4 did the control-flow half; this is the vocabulary half (`want`/`add`/`chosen`/
   `done`/… as declared KB, not literal strings in banks). ⚠Opus for "what's KB vs engine."
3. **Phase 2.3** (name demotion) — now correctly scoped as its OWN phase, not a 6.0 sub-item. Needs
   an Opus-level design call on the KB-declared discriminating-key-index mechanism before any code
   moves; blocks nothing else on the firmware path, so it's not urgent.
4. **Optional follow-on** — prose `suppose … predict …` sugar folding to slice 3c's reified encoding
   (new surface → SLM debt; deferred like `to NAME`, pick up if the SLM ledger is being retrained).

**Slices 4 and 3c are DONE — do NOT re-do them.** (Both were in this list; see the DONE notes above.)

**Model routing** — ⚠Opus = needs vision-judgment; ✓S = Sonnet-safe where a gate/spec catches deviation.
- Slice 4 (plan→act→check→replan): **DONE** (was ⚠Opus)
- Slice 3c (SUPPOSE CNL scope authoring): **DONE** (was ⚠Opus)
- 5.5 exit gate (classify divergences): **⚠Opus**
- Companion: graded α-cut DURING matching **⚠Opus**; aggressive `is_not` completion **⚠Opus**;
  wire `chosen` as declared CHOOSE **~✓S** (gated)
- Phase 2.3 (name→valued attr, KB-declared discriminating-key indexes): **⚠Opus** — real design work,
  NOT mechanical (see correction above); 2.4 (name-free identity tokens) still **✓S** once 2.3 lands
- Phase 2.5 (COPULA/NEG_SUFFIX / `solve.py` preds → KB declarations): **⚠Opus** for "what's KB vs engine"
- Phase 3.1 step 2 (one-graph fold): **⚠Opus** — control/fact segregation. 3.2/3.4: **⚠Opus**
- Phase 6.1 demotion decisions **⚠Opus**; `architecture.md` rewrite **✓S**
- Phase 7 perf: **✓S** with benchmarks for mechanical rungs; **⚠Opus** for design + AOT codegen

**EQUIVALENCE NOT REQUIRED (2026-07-10 ratification) — consequences in force:**
- `rewriter` oracle + its `isa=False` branch retired (Phase 6.0, done) — `TEMPORARY BRIDGE` dual-write
  stays (see correction above; it's load-bearing for the ISA engine itself, not just the oracle)
- 5.5 exit gate COLLAPSES: "classify every divergence" → "firmware sensible + self-consistent on benches"
- Keep GoalSolver as DEVELOPMENT oracle only; demote/delete on firmware coverage alone
- Real long-pole for a *usable* system = **performance (Phase 7)**, not correctness
- Impossible-blocker chance < 5%

## Where the system is (2026-07-11, post repo-split)

**341 tests green, 1 skipped.** All ISA engine files are in `ugm/ugm/`; CNL surface in `ugm/ugm/cnl/`.
The planning rule banks (`PLANNING_RULES`, `SOLVE_RULES`, etc.) and harness benches live in `harneskills`.
`solve.py` is DELETED (Phase 5.5 slice 4) — the plan→act→check→replan control flow is now a KB-declared
composition over the existing `<call>` loop (`tests/test_isa_plan_act_check.py`). SUPPOSE is now a
`<call>` mode too (slice 3c, `tests/test_isa_suppose_calls.py`) — CHECK/CHOOSE/SUPPOSE all serviced by
the one loop.

**PRODUCTION RUNTIME IS 100% THE ISA ENGINE, AND SO IS EVERY TEST.** `rewriter.py` is DELETED
(Phase 6.0) — there is no second engine anywhere in this repo anymore. `run_rules` no longer has an
`isa` parameter; it always runs `run_bank`. The `TEMPORARY BRIDGE` dual-write (legacy `name` VALUED
attr on relation nodes) is RETAINED — it is load-bearing for `machine.py`'s own MINT intern/dedup and
for the many `g.name(rel)` predicate reads across the engine, not rewriter-only as its comments once
claimed (see the Phase 6.0 correction note above); it retires only once Phase 2.3 lands.

Phases 0–5.5 slices 1–3b, slice 4, Phase 6.0 are DONE. See CHANGELOG.md for the full trail.

Companion slices still open: graded α-cut DURING matching in APPLY/CHAIN; aggressive `is_not`
completion (`decide.solve`'s write-side elimination). (The "wire the planner's `chosen` pick as a
declared CHOOSE" companion is subsumed by slice 4 — `solve._mint_chosen` is gone with `solve.py`; the
declared composition commits `chosen` as a rule.)

Also still open (NOT on firmware path): Phase 3.1 step 2 (one-graph fold); Phase 2.3 name demotion
(now correctly an Opus-level design task, not oracle-blocked — the oracle is gone); `tests/test_joern_corpus.py`
(legitimately slow, live-Joern, candidate for `slow` marker).

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

- **2.5** `COPULA`/`NEG_SUFFIX` and the (now-retired) planner's predicate VOCABULARY (`want`/`add`/
  `chosen`/`done`/`best`/… — formerly hardcoded in `solve.py`, now in the harness banks) → KB
  declarations. Slice 4 did the control-flow half; this is the vocabulary half.
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
  axis). (The "wire `solve._mint_chosen` as a declared CHOOSE" companion is closed by slice 4 — `solve.py`
  is retired; the declared plan→act→check→replan composition commits `chosen` as a rule.)

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

  - **Slice 3c DONE (2026-07-11).** SUPPOSE authored as a `<call>` mode with VARIABLE-LENGTH
    assumptions/predictions (the reason it couldn't be a fixed-slot call): `mode_calls.suppose_tool`
    reads N `assume`/`predict` reified triples (`<t> -[k_subj/k_pred/k_obj]-> …`), runs the firmware
    `suppose`, folds a `<suppose>` verdict back (CONFIRMED/REFUTED/INCONCLUSIVE) — the 3a/3b shape
    (rules emit calls, the existing loop services them, effect feeds back) extended to list args.
    Authored via the EXISTING machine-rule grammar; zero new prose forms, zero SLM debt. Prose
    `suppose … predict …` sugar (folds to this) deferred like `to NAME`. `tests/test_isa_suppose_calls.py`
    (6 tests): all 3 verdicts vs. direct `suppose`, control-token verdict, multi-assumption/prediction
    call, and a CNL-authored rule emitting the call whose verdict drives a downstream rule.

  - **Slice 4 DONE (2026-07-11).** Retired `solve.py`'s Python-hardcoded plan→act→check→replan CONTROL
    FLOW (the `graph.name(r) == "want"/"add"/"chosen"/"done"` shape-sniffing) by expressing it as a
    KB-DECLARED composition of ITERATE×CHECK over `<check>` verdicts, serviced by the EXISTING `<call>`
    loop (`run_bank(..., tools=mode_registry(rule_g))`) — no new driver. `tests/test_isa_plan_act_check.py`
    (4 tests): ACT → an `act` CALL, CHECK → a CHECK CALL per want (verdict feeds back as matchable
    control relations), REPLAN → a rule committing an alternative op on a divergence; plus the
    derived-effect bridge (CHECK resolving a want observed only via a rule-bank derivation). `solve.py`
    DELETED (export-only inside `ugm`; harness consumers migrate cross-repo). KEY RESULT: the monotone
    substrate needs NO driver-state reset — per-(op,want) CHECK suppression makes an alternative op's
    positive verdict independent of the diverged op's stale assumed-no, the `DROP_CTRL` teardown-
    subsumption again. Pairs with **Phase 2.5** (the vocabulary half: `want`/`add`/… → KB declarations).

  **Exit gate (DOWNGRADED per 2026-07-10 ratification):** engine grep-clean (no strategy selection
  in Python); benches (card-trader + coref + riddles, now in `harneskills`) produce SENSIBLE,
  SELF-CONSISTENT answers on firmware semantics. No longer requires divergence-from-old-exhaustive
  classification.

---

## Phase 6 — DEMOTE the Python solver; docs converge

- **6.0 DONE (2026-07-11, 331 passed/1 skipped).** Retired `rewriter.py` entirely (deleted; `run_rules`'s
  `isa`/`seeds` params removed, always runs `run_bank`); did the `nodes_named("<tok>")`→`nodes_with_key`
  and `startswith("<")`→`is_control` reader flips in `ugm/cnl/forms.py`/`ugm/cnl/universal.py`. **NOT
  done, and correctly rescoped out of 6.0** (see the correction note under NEXT STEP): the
  `TEMPORARY BRIDGE` dual-write (load-bearing for MINT intern/dedup + `g.name(rel)` reads, not
  oracle-only) and Phase 2.3 name demotion — these are now their own item, gated on an Opus design
  call, not a mechanical sweep. `_INERT_NAMES`/`_is_inert` mostly stays by design (pattern/literal-side
  guards over string tokens, not node instances); the one ambiguous site (`lowering.py`'s `to_attrgraph`
  bridge) is tied to that bridge's own eventual fate, left untouched.

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

- **Slice 4 judgment** — RESOLVED (DONE 2026-07-11): reused the `<call>` loop, declared the strategy
  as forward rules, did NOT rebuild the driver; `solve.py` deleted. The remaining grep-clean of hardcoded
  predicate STRINGS in the (harness-side) banks is Phase 2.5's vocabulary half.
- **Performance (Phase 7) is the real long-pole** for a usable system post the no-equivalence
  ratification. Correctness risk is < 5% impossible-blocker; performance is the open question.
- **Meta-debugging** — the Phase 4 trace renderer is the mitigation; it is complete.
- **SLM surface debt** accumulates from CNL form changes in Phases 2/3/5 — batch retrains via
  the ledger in `harneskills` (`handoff_slm_surface_track.md`).
- **One-graph fold hazard (Phase 3.1 step 2)** — ephemeral APPLY frames add incoming edges to
  fact nodes; previewed and controlled by GC-after-pass, but the full fold needs care.
