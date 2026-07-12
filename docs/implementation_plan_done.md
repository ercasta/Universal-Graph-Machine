# Implementation Plan — COMPLETED WORK (Universal Graph Machine)

> **Archive of DONE items split out of `implementation_plan.md` (2026-07-12).** This holds the
> finished phases, landed milestones, and the rationale trails for decisions that are now settled.
> The ACTIVE plan (remaining work + next step) lives in `implementation_plan.md`. Nothing here is a
> TODO. Residual TODOs that were embedded in these done sections were lifted into the active plan;
> see its "Residuals carried out of done sections" note.
>
> Standing rules (still in force, repeated in the active plan): no commits by the assistant; domain
> logic ONLY in banks; strategies are DECLARED data, never engine sniffing; correctness before raw
> performance. **RATIFIED 2026-07-10 (user): EQUIVALENCE WITH THE PREVIOUS (rewriter / name-based)
> GENERATION IS NOT A CORRECTNESS TARGET** — the old generation was never used; the goal is a WORKING,
> self-consistent firmware system judged on sensible bench answers, not old-output reproduction.

---

## Landed milestones (the NEXT-STEP achievements, newest first)

### Firmware stance as DATA + pluggable tools + engine docs — DONE 2026-07-12 (user-directed)
The firmware's opinions are now selectable data (`ugm/policy.py` `FirmwarePolicy`: `negation_default`
closed/open + `open_preds`/`closed_preds`; `on_cycle` raise/degrade), wired through
`check`/`ask_goal`/`mode_calls`/loaders, `DEFAULT_POLICY` behaviour-neutral. `dispatch.merge_tools`
= collision-safe tool composition (the mechanism was already pluggable). Three docs written:
`docs/architecture.md` (the generic→opinionated layering — Phase 6.2 architecture half),
`docs/engine_developer_guide.md`, `docs/engine_user_guide.md`; README de-staled + Architecture section.
See CHANGELOG (2026-07-12). Note: the FirmwarePolicy landed the two knobs the audit named; a broader
stance surface is tracked as a PLACEHOLDER in the active plan (no third opinion is pending).

### Pre-Phase-7 LEFTOVER RETIREMENT — DONE 2026-07-12
`ugm/demand.py` / `ugm/coref_walk.py` / `ugm/cnl/walker.py` / `ugm/asp.py` DELETED (superseded by the
firmware-v3 chain; no live path depended on them), plus `corpus/walker.cnl`, three dedicated test files,
the walker/demand benches, and the walker/demand/coref test functions in `test_machine_rules`/
`test_new_core`. `ugm/__init__.py` unwired (incl. a stale `"decide"` entry). Suite 283→258 (−25 tests,
all for deleted code), 0 failed. harneskills (the only cross-repo consumer) is being adapted onto the
engine docs — any reference to a deleted export migrates to `chain_sip`/`ask_goal`/`same_as_rules` per
`docs/engine_user_guide.md`. See CHANGELOG.

### Demand-driven-negation PERF lever (a) — DONE 2026-07-12
The linear per-predicate fact scan is gone: `chain._facts_matching` is now ENDPOINT-DRIVEN — a bound
endpoint (SIP makes one almost always available) reaches its facts through the endpoint's node via the
`name` value-accelerator + local topology, not a whole-predicate scan. Behaviour-identical (whole suite
+ NAF differential green); under cProfile at 12 suspects/6 aliases 6.18s→0.565s (call count 9.9M→0.98M),
full suite ~90s→~54s. As-built: `docs/demand_driven_negation_design.md` AS-BUILT §6; CHANGELOG.

### FIRMWARE v3 (demand-driven negation) — DONE 2026-07-11
Negation is decided ON DEMAND by NAF in `chain_sip._nac_blocks` (nested negative demand → positive
closure → absence decides); fuel→UNKNOWN; stratification enforced at LOAD by the object-aware
`lint_stratifiable`, chain prune-and-continues on re-entry. `ask_goal` is demand-driven (`ask` is now
pure rendering). `expand_rules` no longer upgrades closed-world NACs / emits completion rules.
`ugm/decide.py` + `test_decide.py` DELETED (the step-4 differential earned it). Graded α-cut reified into
the chain (`write_rule`/`chain._graded_ok`). Perf: NAC-closure memo + local-agenda drive took a wildcard
query 129s→7.5s, the suite 26min→90s. As-built + deviations: `docs/demand_driven_negation_design.md`
AS-BUILT §§1–5; CHANGELOG. **Do NOT re-do; do NOT resurrect `decide.solve`.**

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

## Phase 2 — ATTRIBUTE-NATIVE conventions (namelessness for real) ✅ COMPLETE

- **2.1 DONE (2026-07-08, 470 green).** Predicates as graded KEYS (`{chase: 1.0}` on rel node);
  `add_relation` mints the predicate key; `nodes_with_key`/`has_key` replace name-equality tests
  in `lowering`, `goal`, `solve`. TEMPORARY BRIDGE dual-write (also writes legacy VALUED `name`)
  kept until Phase 6 oracle retirement. Reserved-key collision (`name` predicate) guarded.

- **2.2 DONE (2026-07-09, 478 green) — both halves.** [Residual now RESOLVED: the "Phase-6 reader
  flip" it named landed in Phase 6.0.]
  - HALF 1: control-token dual-write — `add_node("<goal>")` also writes `{<goal>: 1.0}` key
  - HALF 2: `add_node` control-flag at mint chokepoint — reserved `<…>` syntax ⟹ `control=True`
  - `_is_inert`→`.inert` flag migration COMPLETE for all non-oracle, non-bridge sites

- **2.3 DONE (2026-07-11, 341 green).** `name` demoted to an ordinary VALUED attr; the value-accelerator
  generalized to KB-declared discriminating-key indexes (`_by_value`/`declare_index`/`nodes_with_value`,
  default `{"name"}`); the `TEMPORARY BRIDGE` dual-write RETIRED (a relation's predicate is solely its
  graded key; new `AttrGraph.predicate(rid)`; `name()` requires VALUED so a `name`-predicate relation is
  sound). ~85 predicate readers swept + the `nodes_named(PREDICATE)`/`walker.get_attr(r,"name")` classes
  the plain grep missed. Bonus: `derived_triples` no longer emits garbage triples (entity-as-relation).
  Design + as-built: `docs/name_demotion_design.md`, CHANGELOG.

- **2.4 DONE (2026-07-11, 342 green).** Identity tokens name-free: a coref-class token is now
  `SEP + class-rep-nid` (was `name + SEP + rep`) — the redundant name prefix is dropped, the name is
  recovered from the rep node via `ag.name(rep)` in `_render` (the output boundary). The Skolem token
  likewise references its fresh node id. Contained entirely to `goal.py` (SEP never escaped it); gated
  by the coref/adversarial suite + a new name-free pin (`test_duplicated_name_identity_token_is_name_free`).

- **2.5 DONE (2026-07-11, 342 green).** Crux §7 ratified "**consolidate**". Tier-1 substrate vocabulary
  (`COPULA`/`NEG_COPULA`/`NEG_SUFFIX`/`IS_A`/`SAME_AS`/`DISJOINT`/`CLOSES`/`CWA`/… + `neg_pred`) centralized
  in a new leaf module `ugm/vocabulary.py` (single source of truth). Tier-2 domain coref leak removed:
  `authoring._COREF_PREDS`'s hardcoded `wants`/`in`/`has`/`before`/… gone; `_coref_propagation` derives the
  set content-blind via `SUBSTRATE_COREF_PREDS | relation_predicates(graph) | declared_relations |
  declared_prepositions`. Tier-3 CNL surface English lexicon stays literal by design. Reasoning modules
  grep-clean of vocab literals; no substrate constant defined outside `vocabulary.py`. Design as-built:
  `docs/vocabulary_declaration_design.md`, CHANGELOG. (The planner's `want`/`add`/`chosen`/… vocabulary is
  harness-side now — Slice 4 retired `solve.py`.)

---

## Phase 3 — RULES AS DATA (homoiconicity) — PARTIALLY DONE

> SCOPING DECISION (2026-07-09): Phase 3 is done AS PREREQUISITE FOR Phase 4's firmware — the
> firmware needs the reified rule SHAPE, NOT the "built by FORM rules" authoring. The meta-circular
> FORM-rule authoring (the quote/eval wall) is DEFERRED as a homoiconicity-purity milestone off the
> critical path.
>
> Steps 3.1-step2, 3.2, 3.4 remain OPEN — see the active plan. Done steps below.

- **3.1 STEP 1 DONE (2026-07-09, 478 green).** `rule_graph.write_rule` modernized: rule/var/pattern
  nodes are `control`-flagged; each pattern atom built in FACT SHAPE via `add_relation` (predicate
  as graded key), so APPLY can seed through `nodes_with_key` exactly as for facts.
  [RESIDUAL lifted to active plan: `same_as propagates through X` CNL surface lands here — needs coref
  rules reified; `coref_prop` is forward-compatible.]

- **3.3 DONE (2026-07-09, 487 green).** Head index as graph structure: `<head-index>` hub with
  `hub -[headPred]-> rule_node` per head predicate. Built by `apply.build_head_index` / `rules_producing`.

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

## Phase 5 — FIRMWARE v2: the psychology leaves Python ✅ COMPLETE (engine half)

- **5.1 DONE (2026-07-10).** CHECK: `check(fact_g, rule_g, goal, open_preds=…)` → 4-status verdict
  (POSITIVE / ENTAILED_NEG / ASSUMED_NO / UNKNOWN) over `chain_sip`. `collapse()` == `ask_goal`
  verdict. `explain_check` renders "where I looked." `ugm/check.py`, `tests/test_isa_check.py`.
  [COMPANION now RETIRED: AGGRESSIVE `is_not` completion (`decide.solve`'s write-side elimination) was
  replaced by demand-driven NAF in firmware v3; `decide.solve` is deleted. Do NOT resurrect.]

- **5.2 DONE (2026-07-10).** CHOOSE: `choose(g, goal, alpha=…)` = graded α-cut argmax (nothing-beats-it,
  MONOTONE, ties→all win). `ugm/choose.py`, `tests/test_isa_choose.py`. Gated on design fixtures +
  200-seed randomized argmax differential.
  [COMPANION half-open, lifted to active plan: graded α-cut DURING matching in the APPLY body + the
  inverted ('not at all') cut. The CHAIN half is DONE (firmware v3 `chain._graded_ok`).]

- **5.3 DONE (2026-07-10).** SUPPOSE: `<hypothesis>` scopes — pencil writes, `chain_sip` in-scope,
  CONFIRM→ink / REFUTE→drop_scope, ink monotone. `ugm/suppose.py`, `tests/test_isa_suppose.py`.
  Scope-aware matching as `scope=` param on `apply`/`chain` fact readers, gated behavior-NEUTRAL.

- **5.4 DONE (2026-07-10).** Declared strategies replace shape-sniffing: walker/transitive (`R is
  transitive` → `_closure_declarations`), coref-follow (`coref_prop` flag on `Rule` read by
  `GoalSolver`, not key-sniffing). All three sniffers deleted. `ugm/cnl/machine_rules.py`, `ugm/goal.py`.
  [TRACKED RESIDUAL lifted to active plan: `session.py:CONTENT_PREDS` + Python-generated coref rules →
  Phase 3 (bank-authored `same_as propagates through X`) once coref rules reify — harness-side.]

- **5.5 KB procedures — DONE.** Named compositions of modes, authored in CNL, run as control-token
  programs.
  - **Slices 1–2 DONE (2026-07-10).** CHECK + CHOOSE as `<call>` calculators. `ugm/mode_calls.py`,
    `tests/test_isa_mode_calls.py`. Reuses the existing `<call>` loop; NOT a new driver.
  - **Slices 3a–3b DONE (2026-07-10).** Rules emit mode-calls, existing loop services them, verdict
    feeds back. Key-aware INTERN fix (MINT skips reified domain-relation candidates). Zero new CNL
    surface, zero SLM debt.
  - **Slice 3c DONE (2026-07-11).** SUPPOSE authored as a `<call>` mode with VARIABLE-LENGTH
    assumptions/predictions: `mode_calls.suppose_tool` reads N `assume`/`predict` reified triples
    (`<t> -[k_subj/k_pred/k_obj]-> …`), runs the firmware `suppose`, folds a `<suppose>` verdict back
    (CONFIRMED/REFUTED/INCONCLUSIVE). Authored via the EXISTING machine-rule grammar; zero new prose
    forms, zero SLM debt. `tests/test_isa_suppose_calls.py` (6 tests). [Prose `suppose … predict …`
    sugar deferred like `to NAME` — tracked as an optional follow-on in the active plan.]
  - **Slice 4 DONE (2026-07-11).** Retired `solve.py`'s Python-hardcoded plan→act→check→replan CONTROL
    FLOW (the `graph.name(r) == "want"/"add"/"chosen"/"done"` shape-sniffing) by expressing it as a
    KB-DECLARED composition of ITERATE×CHECK over `<check>` verdicts, serviced by the EXISTING `<call>`
    loop (`run_bank(..., tools=mode_registry(rule_g))`) — no new driver. `tests/test_isa_plan_act_check.py`
    (4 tests). `solve.py` DELETED (export-only inside `ugm`; harness consumers migrate cross-repo).
    KEY RESULT: the monotone substrate needs NO driver-state reset — per-(op,want) CHECK suppression makes
    an alternative op's positive verdict independent of the diverged op's stale assumed-no (the `DROP_CTRL`
    teardown-subsumption again). Pairs with Phase 2.5 (the vocabulary half).

  **Exit gate (DOWNGRADED per 2026-07-10 ratification):** engine grep-clean (no strategy selection in
  Python); benches produce SENSIBLE, SELF-CONSISTENT answers on firmware semantics. No longer requires
  divergence-from-old-exhaustive classification.

  **ENGINE-HALF MET — audited 2026-07-11 (in-repo).** Systematic sweep of `ugm/` for strategy-selection-
  in-Python: (1) the three shape-sniffers are gone (5.4); (2) `solve.py`'s hardcoded plan control flow is
  gone (slice 4); (3) NO rule-key sniffing; (4) every remaining `g.name(...) == "literal"` is firmware
  CONTROL SUBSTRATE or CNL SURFACE RECOGNITION grammar — never reasoning-strategy; (5) `goal.py:127 ==
  "transitive"` READS the declared `rel_property` map. Phase 2.5 has since consolidated the copula/
  negation/coref VOCABULARY into `ugm/vocabulary.py` and de-hardcoded the domain coref list.
  [The BENCH-SENSIBILITY HALF is harness-side and remains OPEN — see the active plan.]

---

## Phase 6 — DEMOTE the Python solver; docs converge — PARTIALLY DONE

- **6.0 DONE (2026-07-11, 331 passed/1 skipped).** Retired `rewriter.py` entirely (deleted; `run_rules`'s
  `isa`/`seeds` params removed, always runs `run_bank`); did the `nodes_named("<tok>")`→`nodes_with_key`
  and `startswith("<")`→`is_control` reader flips in `ugm/cnl/forms.py`/`ugm/cnl/universal.py`. The
  `TEMPORARY BRIDGE` dual-write + Phase 2.3 name demotion were correctly rescoped OUT of 6.0 (their own
  item) — and have since LANDED as Phase 2.3 (2026-07-11). `_INERT_NAMES`/`_is_inert` mostly stays by
  design (pattern/literal-side guards over string tokens).

- **6.1 DONE (2026-07-11, 264 passed/1 skipped) — THE TWO-ENGINE RETIREMENT.** `ugm/goal.py` (GoalSolver,
  Goal, solve_goal, solve_all, NonStratifiable) and `ugm/walker.py` (the Python reference `Walker`/
  `walk_to_goal`) are DELETED. `ask_goal` — GoalSolver's last production consumer — now runs the FORWARD
  firmware. ~79 GoalSolver/Walker/solve_all tests removed (12 files); survivors re-targeted onto the
  firmware. KEY REALIZATION: the monotone demand-driven chain CANNOT do decided negation — decided negation
  is inherently FORWARD, and `run_bank` already stratifies + services INTERPOSE. [Superseded in part by
  firmware v3, which made negation demand-driven and deleted `decide.py`.] As-built:
  `docs/goalsolver_retirement_design.md`, CHANGELOG. Ratified [[delete-old-code-aggressively]].

- **6.2 architecture half DONE (2026-07-12).** `docs/architecture.md` rewritten as the as-built
  generic→opinionated layering (substrate → engine/ISA → tools → reified rules → firmware → stance → CNL).
  [Two 6.2 items REMAIN OPEN — see active plan: refresh `reference.md`'s doc-map (it still lists
  architecture.md as pre-rehost / to-be-rewritten), and summarize finished phases into CHANGELOG.]

---

## Settled rationale trails (historical — the reasoning behind done decisions)

### PHASE 6.0 CORRECTION (2026-07-11) — the `TEMPORARY BRIDGE` dual-write was NOT rewriter-only
[RESOLVED: the bridge was retired in Phase 2.3, 2026-07-11. This correction stands as the rationale for
WHY 6.0 correctly left it in place at the time.] Tracing actual readers found the three "TEMPORARY BRIDGE"
comments (`attrgraph.py`'s `add_relation`, `lowering.py`'s `to_attrgraph`/`lower_rhs`) were wrong about
what blocked their removal: `machine.py`'s MINT intern/dedup read `attrs[NAME]`/`g.name(rel)` directly, and
dozens of production call sites read a relation's predicate back via `g.name(rel)`. Dropping the legacy
`name` write then would break the live ISA engine. So the bridges were deliberately left in place —
entangled with Phase 2.3 (real indexing-declaration design work). What 6.0 actually did: deleted
`rewriter.py` + its `isa=False` branch/re-exports (migrating ~15 dependent test files onto `run_bank`/
`run_rules`, converting differential-vs-rewriter assertions to direct ISA-pinned ones), and the
`nodes_named`→`nodes_with_key` / `startswith("<")`→`is_control` reader flips. Also fixed a real
pre-existing bug: `run_bank` ignored `Rule.meta` (every firing minted provenance regardless of the flag)
— now fixed in `lowering.py`.

### SLICE 4 SCOPE CLARIFICATION (2026-07-11, user-confirmed) — RESOLVED, slice 4 is DONE
Before starting slice 4, we checked whether `solve.py` was genuinely `ugm`-scope firmware or harness-only
planning content that leaked in. First pass (vocabulary + zero `ugm/tests/` coverage) argued for moving it
to `harneskills` wholesale. **That read was incomplete.** Reading `solve.py` directly: its solving MECHANISM
is `GoalSolver(...).solve(Goal(...))` — the same ISA-native demand-forward backward reasoner every
legitimate `ugm` capability uses, not a from-scratch engine like `rewriter.py`. So it was NOT pre-ISA legacy
and NOT simply misplaced-repo content. **The real defect: `solve.py` violated the plan's own standing rule**
— its driver hardcoded fixed predicate NAMES into Python control flow (`graph.name(r) == "want"/"add"/…`),
exactly the shape-sniffing Phase 5.4 eliminated for the walker/coref strategies. So slice 4 was genuinely
`ugm`-scope firmware work, reframed: not "extend `solve.py` as-is" but "retire its Python-hardcoded
plan→act→check→replan CONTROL FLOW by expressing it as a KB-declared composition of ITERATE×CHECK over
`<check>` verdicts (reuse `mode_calls.py`'s existing `<call>` loop, don't rebuild)." The planning-specific
predicate VOCABULARY (`pre`/`add`/`del`/`cost`/`want`) stays whatever a bank declares — those banks live in
`harneskills` as an APPLICATION of the generic mechanism.
