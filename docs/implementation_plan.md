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

**Suite: 283 passed, 1 skipped, 0 failed** (`python -m pytest -q`, ~66s). 274 (firmware v3 + the
2026-07-12 endpoint-driven `_facts_matching` perf fix, was ~90s→~54s) + 9 new `test_isa_policy.py`
(firmware STANCE as data). Prior baseline 264 (Phase 6.1).

**FIRMWARE STANCE AS DATA + PLUGGABLE TOOLS + ENGINE DOCS DONE (2026-07-12, user-directed).** The
firmware's opinions are now selectable data (`ugm/policy.py` `FirmwarePolicy`: `negation_default`
closed/open + `open_preds`/`closed_preds`; `on_cycle` raise/degrade), wired through
`check`/`ask_goal`/`mode_calls`/loaders, `DEFAULT_POLICY` behaviour-neutral. `dispatch.merge_tools`
= collision-safe tool composition (the mechanism was already pluggable). Three docs written:
`docs/architecture.md` (the generic→opinionated layering — Phase 6.2 architecture half),
`docs/engine_developer_guide.md`, `docs/engine_user_guide.md`; README de-staled + Architecture section.
See CHANGELOG (2026-07-12). **Still OPEN (user is driving):** (1) the FirmwarePolicy landed the two
knobs the audit named; a broader stance surface is future. (2) Pre-Phase-7 LEFTOVER-LIVENESS sweep —
`ugm/demand.py`, `ugm/coref_walk.py`, `ugm/cnl/walker.py`, `ugm/asp.py` are pre-firmware-v3
demand/coref/walk subsystems; the user is adapting harneskills (the only consumer) to make them safe to
DELETE. Do NOT delete blind — they are exported public API; delete only once harneskills is migrated.

**FIRMWARE v3 (demand-driven negation) DONE (2026-07-11).** Negation is decided ON DEMAND by NAF in
`chain_sip._nac_blocks` (nested negative demand → positive closure → absence decides); fuel→UNKNOWN;
stratification enforced at LOAD by the object-aware `lint_stratifiable`, chain prune-and-continues on
re-entry (a runtime raise fired spuriously on coref banks — see design AS-BUILT §1). `ask_goal` is
demand-driven (`ask` is now pure rendering). `expand_rules` no longer upgrades closed-world NACs / emits
completion rules. `ugm/decide.py` + `test_decide.py` DELETED (the step-4 differential earned it). Graded
α-cut reified into the chain (`write_rule`/`chain._graded_ok`). Perf: NAC-closure memo + local-agenda
drive took a wildcard query 129s→7.5s, the suite 26min→90s. As-built + deviations:
`docs/demand_driven_negation_design.md` AS-BUILT §§1–5; CHANGELOG. **Do NOT re-do; do NOT resurrect
`decide.solve`.**

**PICK UP NEXT — recommended order:**
0'. **Demand-driven-negation PERF follow-on (Phase 7-adjacent, the honest weak spot). LEVER (a) DONE
   (2026-07-12).** The linear per-predicate fact scan is gone: `chain._facts_matching` is now
   ENDPOINT-DRIVEN — a bound endpoint (SIP makes one almost always available) reaches its facts through
   the endpoint's node via the `name` value-accelerator + local topology, not a whole-predicate scan
   (`_endpoints`/`name` left the top of the profile). Behaviour-identical (whole suite + NAF differential
   green); under cProfile at 12 suspects/6 aliases 6.18s→0.565s (call count 9.9M→0.98M), full suite
   ~90s→~54s. As-built: `docs/demand_driven_negation_design.md` AS-BUILT §6; CHANGELOG (2026-07-12).
   **REMAINING levers (un-started, now Phase 7 — the query is sub-second at session scale):** (b) semi-
   naive worklist so a demand re-services only when a relevant fact appeared (the round loop still
   re-services the whole local agenda each round; the profile's new top is `relations_from`/`_read_atoms`
   re-reading static reified-rule structure per service); (c) the domain coref `same_as.*.is` demand
   fan-out. ALSO still open: `why` provenance is order-sensitive (a fact pre-derived without provenance
   renders `(given)`) — design AS-BUILT §5.

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
[RESOLVED: the bridge was retired in Phase 2.3, 2026-07-11 — see that entry. This correction stands as
the rationale trail for WHY 6.0 correctly left it in place at the time.]
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
0. **DEMAND-DRIVEN NEGATION (firmware v3) — DONE 2026-07-11.** See the NEXT STEP block at the top and
   `docs/demand_driven_negation_design.md` AS-BUILT. The perf follow-on is item 0' up top.
1. **Phase 5 exit gate — bench-sensibility half (harness-side)** — run card-trader + coref + full
   ProofWriter-coverage in `harneskills`. The engine-half is MET in-repo (audited 2026-07-11); this half
   is not verifiable from this repo. NOTE for that run: Phase 2.5 (2026-07-11) de-hardcoded the domain
   coref predicate list — coref now composes over `relation_predicates(graph)` (relations in play) +
   declared relations/prepositions, NOT a fixed engine list. A harness bench relying on a domain predicate
   composing across coref should Just Work if the predicate is present as a relation (default-grammar
   `in`/`has`/`before` included); if one regresses, DECLARE the relation in the harness KB, do NOT re-add
   an engine string.
2. **Phase 7(a)** — now that 2.3 settled the name/key/value model, intern keys/values to ints + CSR
   adjacency + bitsets on a CLEAN representation (no bridge). The plan's stated long-pole.
3. **Optional follow-on** — prose `suppose … predict …` sugar folding to slice 3c's reified encoding
   (new surface → SLM debt; deferred like `to NAME`, pick up if the SLM ledger is being retrained).

**Slices 4/3c and Phase 2.3/2.4/2.5 are DONE, and the 5.5 exit-gate ENGINE half is MET — do NOT re-do them.**

**Model routing** — ⚠Opus = needs vision-judgment; ✓S = Sonnet-safe where a gate/spec catches deviation.
- Slice 4 (plan→act→check→replan): **DONE** (was ⚠Opus)
- Slice 3c (SUPPOSE CNL scope authoring): **DONE** (was ⚠Opus)
- 5.5 exit gate (classify divergences): **⚠Opus**
- Companion: graded α-cut DURING matching — **DONE for CHAIN** (firmware v3, `chain._graded_ok`); the
  APPLY-body α-cut + inverted ('not at all') cut remain **⚠Opus**. Aggressive `is_not` completion is
  **RETIRED** (demand-driven NAF replaced it; `decide.solve` deleted). `chosen` as declared CHOOSE **~✓S**
- Phase 2.3 (name→valued attr, KB-declared discriminating-key indexes): **⚠Opus** — real design work,
  NOT mechanical (see correction above); 2.4 (name-free identity tokens) still **✓S** once 2.3 lands
- Phase 2.5 (COPULA/NEG_SUFFIX / coref predicate VOCABULARY → consolidate/de-hardcode): **DONE** (was ⚠Opus)
- Phase 3.1 step 2 (one-graph fold): **⚠Opus** — control/fact segregation. 3.2/3.4: **⚠Opus**
- Phase 6.1 demotion decisions **⚠Opus**; `architecture.md` rewrite **✓S**
- Phase 7 perf: **✓S** with benchmarks for mechanical rungs; **⚠Opus** for design + AOT codegen

**EQUIVALENCE NOT REQUIRED (2026-07-10 ratification) — consequences in force:**
- `rewriter` oracle + its `isa=False` branch retired (Phase 6.0, done); the `TEMPORARY BRIDGE` dual-write
  (which outlived the oracle as load-bearing for the ISA engine itself) is now also RETIRED (Phase 2.3, done)
- 5.5 exit gate COLLAPSES: "classify every divergence" → "firmware sensible + self-consistent on benches"
- Keep GoalSolver as DEVELOPMENT oracle only; demote/delete on firmware coverage alone
- Real long-pole for a *usable* system = **performance (Phase 7)**, not correctness
- Impossible-blocker chance < 5%

## Where the system is (2026-07-11, post repo-split)

**274 tests green, 1 skipped** (firmware v3 demand-driven negation, 2026-07-11). All ISA engine files are in `ugm/ugm/`; CNL surface in `ugm/ugm/cnl/`.
The planning rule banks (`PLANNING_RULES`, `SOLVE_RULES`, etc.) and harness benches live in `harneskills`.
`solve.py` is DELETED (Phase 5.5 slice 4) — the plan→act→check→replan control flow is now a KB-declared
composition over the existing `<call>` loop (`tests/test_isa_plan_act_check.py`). SUPPOSE is now a
`<call>` mode too (slice 3c, `tests/test_isa_suppose_calls.py`) — CHECK/CHOOSE/SUPPOSE all serviced by
the one loop.

**PRODUCTION RUNTIME IS 100% THE ISA ENGINE, AND SO IS EVERY TEST.** `rewriter.py` is DELETED
(Phase 6.0) — there is no second engine anywhere in this repo anymore. `run_rules` no longer has an
`isa` parameter; it always runs `run_bank`. The `TEMPORARY BRIDGE` dual-write (legacy `name` VALUED
attr on relation nodes) is now RETIRED (Phase 2.3, 2026-07-11): a relation's predicate is SOLELY its
graded key, read via `AttrGraph.predicate(rid)`/`has_key`; the ~85 `g.name(rel)` predicate readers (plus
the `nodes_named(PREDICATE)` / `walker.get_attr(r,"name")` classes the plain grep missed) were migrated.
See `docs/name_demotion_design.md` + CHANGELOG.

Phases 0–5.5 slices 1–3b, slice 4, Phase 6.0/6.1, and firmware v3 (demand-driven negation) are DONE.
See CHANGELOG.md for the full trail. `ask_goal` is demand-driven; `decide.py` is deleted.

Companion slices still open: graded α-cut DURING matching in APPLY (the CHAIN half is DONE — firmware
v3 `chain._graded_ok`) + the inverted ('not at all') cut. Aggressive `is_not` completion is RETIRED
(demand-driven NAF replaced it). (The "wire the planner's `chosen` pick as a declared CHOOSE" companion
is subsumed by slice 4 — `solve._mint_chosen` is gone with `solve.py`; the declared composition commits
`chosen` as a rule.)

Also still open (NOT on firmware path): Phase 3.1 step 2 (one-graph fold); `tests/test_joern_corpus.py`
(legitimately slow, live-Joern, candidate for `slow` marker). (Phase 2.3 name demotion + bridge
retirement is DONE — 2026-07-11.)

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
  in a new leaf module `ugm/vocabulary.py` (single source of truth; the 4× `COPULA` dup + both `_neg_pred`
  bodies now import from it). Tier-2 domain coref leak removed: `authoring._COREF_PREDS`'s hardcoded
  `wants`/`in`/`has`/`before`/… gone; `_coref_propagation` derives the set content-blind via
  `SUBSTRATE_COREF_PREDS | relation_predicates(graph) | declared_relations | declared_prepositions` (the
  faithful additive-coref analog, handles default-grammar `in`/`has`/`before` that a declared-only set
  would drop). Tier-3 CNL surface English lexicon stays literal by design. Reasoning modules
  (`goal`/`decide`/`check`/`demand`/`coref_walk`) grep-clean of vocab literals; no substrate constant
  defined outside `vocabulary.py`. Design as-built: `docs/vocabulary_declaration_design.md`, CHANGELOG.
  (The planner's `want`/`add`/`chosen`/… vocabulary is harness-side now — Slice 4 retired `solve.py`, so
  those live in the harness banks as APPLICATION vocabulary, not engine constants.)

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

  **ENGINE-HALF MET — audited 2026-07-11 (in-repo).** Systematic sweep of `ugm/` for strategy-selection-
  in-Python: (1) the three shape-sniffers are gone (Phase 5.4); (2) `solve.py`'s hardcoded plan control
  flow is gone (slice 4); (3) NO rule-key sniffing (`r.key`/`rule.key` uses are all provenance journaling,
  `Unlowerable` error text, fired-suppression keying, exist-NAC bookkeeping, or determinism sorting —
  never strategy selection); (4) every remaining `g.name(...) == "literal"` is either firmware CONTROL
  SUBSTRATE (`next`/`at` cursor, `<qevent>`) or CNL SURFACE RECOGNITION grammar (`body`/`first`/`same_as`/
  `relation`/`about`/`violates`/`yes`) — recognition, not reasoning-strategy; (5) `goal.py:127 == "transitive"`
  READS the declared `R is transitive` → `rel_property` map (content-blind, Phase 5.4's `_closure_declarations`),
  not sniffing. The Python-hardcoded predicate STRINGS that remained at the audit — the copula/negation/coref
  VOCABULARY convention (`check`/`decide`/`goal`'s `COPULA="is"`/`NEG_SUFFIX="_not"`; `authoring._COREF_PREDS`;
  `universal.SAME_AS_RULES`) — were **Phase 2.5's explicit scope** (+ the 5.4b tracked residual B), NOT
  strategy selection, so they did not gate 5.5; **Phase 2.5 has since consolidated them into
  `ugm/vocabulary.py` and de-hardcoded the domain coref list (2026-07-11, DONE).** The firmware-semantics gate (`chain_sip == GoalSolver`,
  Phase 4.4) and the riddles bench are GREEN in the in-repo suite.
  **BENCH-SENSIBILITY HALF is harness-side:** card-trader + coref + full ProofWriter-coverage benches
  live in `harneskills` (ProofWriter-coverage also needs external data), so that half must be run there —
  it is not verifiable from this repo.

---

## Phase 6 — DEMOTE the Python solver; docs converge

- **6.0 DONE (2026-07-11, 331 passed/1 skipped).** Retired `rewriter.py` entirely (deleted; `run_rules`'s
  `isa`/`seeds` params removed, always runs `run_bank`); did the `nodes_named("<tok>")`→`nodes_with_key`
  and `startswith("<")`→`is_control` reader flips in `ugm/cnl/forms.py`/`ugm/cnl/universal.py`. The
  `TEMPORARY BRIDGE` dual-write + Phase 2.3 name demotion were correctly rescoped OUT of 6.0 (their own
  item, gated on a design call, not a mechanical sweep) — and have since LANDED as Phase 2.3 (2026-07-11,
  the bridge is retired; `lowering.to_attrgraph`'s name-write is gone). `_INERT_NAMES`/`_is_inert` mostly
  stays by design (pattern/literal-side guards over string tokens, not node instances).

- **6.1 DONE (2026-07-11, 264 passed/1 skipped) — THE TWO-ENGINE RETIREMENT.** `ugm/goal.py` (GoalSolver,
  Goal, solve_goal, solve_all, NonStratifiable) and `ugm/walker.py` (the Python reference `Walker`/
  `walk_to_goal`) are DELETED. `ask_goal` — GoalSolver's last production consumer — now runs the FORWARD
  firmware (`decide.solve` decided-negation + read via `match_pats`). `decide.solve` de-Python-ed to a
  single stratified `run_rules` pass (the two-phase `if` dissolved). `decided_negation=False` (the NAF
  path) retired — decided negation is unconditional. ~79 GoalSolver/Walker/solve_all tests removed (12
  files); survivors re-targeted onto the firmware. KEY REALIZATION: the monotone demand-driven chain
  (`chain`/`check`) CANNOT do decided negation (aggressive completion re-fires without the INTERPOSE
  defeat) — decided negation is inherently FORWARD, and `run_bank` already stratifies + services INTERPOSE.
  The in-graph `cnl/walker.walk_on_demand` is the real walker and STAYS. As-built:
  `docs/goalsolver_retirement_design.md`, CHANGELOG. Ratified [[delete-old-code-aggressively]].

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
