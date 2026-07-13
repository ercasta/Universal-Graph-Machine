# Implementation plan — make coreference fully DEMAND-DRIVEN (perf + vision)

Status: **the demand-driven change is CORRECT but REGRESSES performance (per-query coref blowup); it
now lives UNCOMMITTED in the `main` working tree as the base for the real fix.** The forward plan is
value-INDEXING (cheap value-match seeding) + defeasible NODE-COALESCING (eliminate propagation) +
mention over-marking cleanup — see §0.3. Read §0 FIRST.

## 0. RESULT (read first) — demand-driven coref works but is 3–6× SLOWER

The full change was built and works: `same_as` made visible to the demand matcher
(`chain._rel_matches_pred`), the graded rule made to FOLLOW `same_as` (`_graded_rule`), and the eager
`prop` pass removed from `load_corpus`/`load_facts`. Correctness is essentially there: of the 13
originally-affected tests, 11 pass; only 2 trace tests needed expectation updates (done); the full
suite is 337 pass / 1 fail (`test_new_core.py::test_ask_relation_questions`).

BUT performance regressed severely:
- `load_corpus` got **10× faster** (6.2s → 0.64s — the eager blowup is gone). GOOD.
- Per-query cost **exploded**: ~**26 s/query** (was ~0.2s). Demo 04: 39s → **220s**. Demo 05: 62s →
  **151s**. Full suite: 64s → **286s**.

Profile of ONE query (`is alice served express`, demo 04) — **~897,000 fact EMITs**, 123s under
cProfile:
- `resolve_write_node → _one_identity → _same_as_neighbors` = **77%** (write-target disambiguation
  runs an undirected `same_as` BFS per EMIT; `_same_as_neighbors` called 1.35M times). This part is a
  fixable constant-factor (memoize the coref class / make the diagnostic warning lazy) — but fixing it
  only takes 123s → ~28s, still far too slow.
- The DEEPER cost is the **~897K EMITs themselves**: the demand path re-runs the coref PROPAGATION per
  query. Rules-based propagation over the dense same-name `same_as` graph (the `same_name` rule makes an
  M² CLIQUE per name group, and `same_as.subj/obj.same_as` transitivity re-walks it) is super-linear —
  the SAME blowup as the eager pass, but now paid PER QUERY instead of once per load, with no
  amortization (and the demos reload per question, so no session reuse either).

**Root tension:** coref propagation-as-rules is inherently expensive on a dense `same_as` graph.
Eager pays it once/load; demand pays it once/query (worse for query-heavy use). The cheap alternative
is union-find equivalence-class resolution at lookup — which the user REJECTED for the engine
(`coref-stays-cnl-not-engine`). So the vision (coref = rules) and the perf goal are in direct tension
on this axis. **This needs a user decision — see §0.1.**

### 0.1 Options for the user (recommendation first)
1. **(Recommended) Bounded attention.** Run demand coref under `attention="focus"` (already exists,
   `intake.ingest`, `docs/cnl_intake_design.md §3`): a query reasons only within the focus working set,
   so coref composition is bounded to in-play entities, not the whole `same_as` graph. Vision-pure
   (it's the agent-not-theorem-prover reading) AND likely fast. The demos use `attention="global"`;
   this is a semantic choice (off-focus facts are outside attention). Try this FIRST on the wip branch.
2. **Cut same_as density.** The `same_name` rule makes an M² clique; a STAR per name group (each mention
   `same_as` one representative) is O(M) and makes traversal/composition cheap — but producing a star
   from a declared value-match rule needs a mechanism (the deleted `wire_same_as` did exactly this in
   the engine; doing it as a rule is the open question).
3. **Reconsider union-find** for coref RESOLUTION (not the deprecated engine merge; an equivalence-class
   lookup the rules consult). The perf data is strong evidence for it; it conflicts with
   `coref-stays-cnl-not-engine`. User's call whether the perf cost changes that stance.
4. **Keep eager, optimize its computation.** Stay eager (fast queries) and attack the eager cost: the
   `same_name` M² Cartesian → name-index seed (matcher already has `nodes_named`). Doesn't remove the
   propagation blowup, but avoids the per-query regression entirely.

Cheap constant-factor win regardless of direction: memoize `_same_as_neighbors` / make the
`resolve_write_node` `_one_identity` warning lazy (it's a diagnostic; 77% of a query's time).

### 0.2 What is in the `main` working tree (uncommitted)
The full working change set (correct, slow): `chain._rel_matches_pred` same_as-visibility fix,
`_graded_rule` follows `same_as`, `load_corpus`/`load_facts` defer `prop`, and the 2 trace-test
updates. Committed `main` is still `550e11f` (no foreign commits — the wip branch was deleted at the
user's request; changes brought over as working-tree edits for the user to commit under their own
authorship).

### 0.3 FORWARD PLAN (the real fix — decided in conversation)
Attack both coref costs at the root, staying vision-close:
1. **Value-indexing for value-match seeding (START HERE).** The substrate ALREADY has the machinery:
   `attrgraph._by_value` (per-key,per-value index), `declare_index(key)` (builds from existing nodes,
   incrementally maintained in `set_attr`), and the matcher's name-index SEED fast path
   (`machine.py:376`). Do: (a) `declare_index(dim)` for every value-match key when a rule is loaded
   (dynamically, so conversation-created rules index too); (b) a TRANSPARENT matcher optimization —
   a value-EQUALITY `VMATCH(a,b,key)` where `b` is seeded after `a` is bound becomes an index SEED of
   `b` over `_by_value[key][value_of(a)]` (sideways info passing), collapsing the M² Cartesian to
   Σ bucket². General (helps ALL value-match rules + "system-1" associative recall), not coref-specific.
2. **Defeasible node-coalescing to eliminate propagation.** A reversible `COALESCE`/`SPLIT` ISA op pair
   (modeled on the reserved `INTERPOSE`/`RESTORE` reversible-rewrite opcodes, `lowering.py:386`),
   fired by the `same_as` rule as its EFFECT: physically fold coreferent ENTITY mentions to one node
   (facts unified → nothing to propagate; the `ByById`/unbound `who` bug also vanishes). Must be
   reversible (keep a coalescence record: original ids + per-edge provenance, to SPLIT on defeat),
   rule-triggered (judgment stays CNL), and must protect relation/marker nodes (the old
   `canonicalize` merge bug). This is `canonicalize` done RIGHT (reversible) — confirm the user accepts
   a reversible merge given the destructive one was deleted.
3. **Mention over-marking cleanup (cheap, complementary).** The cliques are big mostly from
   NON-entities: `_corpus_lines` (`authoring.py:1251`) strips only full-line `#` comments, NOT inline
   ones, so `alice is very urgent  # degree 0.8` tokenizes "degree"/"0.8"/etc. into mention nodes;
   plus grammar/connective words (`and`×15, `a`×11, `when`, `not`) get marked. Demo 04: 116 mention
   nodes / Σbucket²=678, but real entity coref (alice×5, bob×5, …) is a small fraction. Fix inline-
   comment stripping and tighten `mark_mentions` to real fact arguments → smaller cliques for free.

---

Below: the original staged plan + the Blocker A/B/C investigation (still valid as reference).

## 1. Goal

Demos are slow (super-linear in corpus size). The cause is NOT reasoning and NOT the deprecated
coref tools (already deleted, commit `550e11f`). It is the **eager coreference pass** in
`load_corpus`/`load_facts` that materializes the full `same_as` fact-propagation closure at load
time. Make coreference **fully demand-driven** — compose facts across `same_as` only for the goal a
query actually asks — with **no eager coref pass**, honoring the vision (coref is CNL rules, never
hardcoded in the engine — see memory `coref-stays-cnl-not-engine`). End state: no eager
`run_bank(kb, coref+prop)`, all tests green, demos fast.

## 2. Performance findings (baseline, post-nuke, on this machine — high run-to-run variance)

Per-demo wall time (fresh `load_corpus` per question, as `demos/run.py` does):

| demo | content lines | time |
|---|---|---|
| 01 | 11 | ~2.4s |
| 02 | 15 | ~3.2s |
| 03 | 22 | ~13s |
| 04 | 23 | ~39s |
| 05 | 34 | ~62s (was 253s under load) |
| 06 (session, load-once) | — | ~1.3s |

Where the time goes (demo 04, one `load_corpus` = ~6.2s unprofiled):

| load pass | forms | nodes in→out | firings | time |
|---|---|---|---|---|
| recognize | 57 | 399→686 | 108 | 0.36s |
| **coref (`same_name` + `prop`)** | 56 | 802→**1834** | **17,215** | **6.57s** |
| graded | 3 | 1834→1834 | 3 | 0.04s |

Reasoning itself is cheap (`ingest`/`ask_goal` ≈ 0.2s/question). **94% of load = the coref pass.**
Breakdown of the coref pass (demo 04): 116 mention nodes, 39 distinct names.
- `same_name` rule: 678 firings (= Σ group_size²; matcher pays the full 116² Cartesian — its LHS
  `[?x is_a mention, ?y is_a mention]` shares no variable so the whole cross-product is enumerated
  before the value-match-on-name prunes it). Nodes 802→1480.
- `prop` (55 `same_as_rules`, one per content predicate): **16,537 firings**, nodes 1480→1834
  (tripling the graph by copying every content fact across every `same_as` edge). **This is the blowup.**

The demo runner ALSO reloads the whole corpus per question (`demos/run.py:95`), multiplying the
above by #questions. Load-once (the `Session`/`ingest` pattern, demo 06) removes that multiplier
(demo 04: 37s→8s) but does NOT fix the single-load cost. A separate, optional cleanup.

## 3. What is already done (committed `550e11f` "Removed deprecated computations")

Deleted the deprecated coreference-as-a-tool family (engine/loader-level, name-reading — the thing
the vision superseded):
- `ugm/cnl/forms.py`: `canonicalize` (destructive merge), `wire_same_as` (additive same-name link,
  O(M)), `coref_in_context` (context-scoped), and the `_contexts_of` helper.
- Removed their exports from `ugm/__init__.py`; added `mark_mentions` to exports.
- Deleted the tests OF those functions; rewrote 3 tests that merely USED one as a coref step
  (`test_new_core.py::test_ask_is_a_questions_and_unrecognized`,
  `::test_universal_rules_via_graph_match_python`,
  `test_isa_reasoning_parity.py::test_graded_pass_writes_the_expected_embedding_end_to_end`).
- **KEPT** (these belong to the vision): `mark_mentions` (marking), `same_name_coref_rules` +
  `same_as_rules` (the declared CNL coref rules), `propagate_embeddings` (graded-layer union tool).
- Full suite: 338 passed.

## 4. Vision constraints — DO NOT VIOLATE

- Coreference resolution stays expressed as **CNL rules**. Do NOT put union-find / `same_as`-class
  resolution into `_facts_matching` or the matcher (that resurrects `wire_same_as`). See memory
  `coref-stays-cnl-not-engine`, `coref-as-rules-mention-marker`.
- Identity (deciding coref) = the declared `same_name` value-match rule. Propagation (composing
  facts across `same_as`) = the declared `same_as_rules`. Both already appended to the demand rule
  set in `load_corpus` (`authoring.py:1286`).
- Agent, not theorem prover: demand-driven, absence decides, fuel→UNKNOWN (memory
  `agent-not-theorem-prover`). "Don't compute what we might not need" — the user's explicit driver
  for this change.

## 5. Core finding: demand-driven coref WORKS for bound goals; three things block full removal

Proven: `ask_goal` composes a content fact across `same_as` with **zero** eager passes
(`is alice happy` derived across a `same_as` link, only `same_name` edges materialized). So the
demand solver's core capability is present. Deferring `prop` (changing `run_bank(kb, coref+prop)` →
`run_bank(kb, coref)` in `load_corpus`, keeping `coref+prop` in the demand set) broke **11 tests**.
Root causes, in priority order:

### BLOCKER A — SOLVED. Root cause: `same_as` invisible to the demand matcher.
(The "stratified NAF" hypothesis below was WRONG — kept for the record; the real cause is simpler.)

**Real root cause:** the same-name coref rule reads the `<mention>` control marker, so
`_rule_touches_control` flags it and `run_bank` mints its `same_as` head as a CONTROL relation.
The FORWARD matcher sees control rels (so eager `prop` composes across them), but the DEMAND matcher
`_facts_matching` SKIPS control rels (`_rel_matches_pred`, `chain.py:368`). So the declared coref
propagation rules can NEVER see `same_as` on demand — they can't traverse the link — and on-demand
coref composition silently fires 0. Eager `prop` masked this by composing everything up front.

Evidence: converting `same_as` to non-control made `ask_goal` compose a fact onto a `ById`-pinned
sibling on demand (`fired 1`), and the thief riddle came out fully correct under deferred `prop`
(including `who is thief` → `[cy is thief]`). Direct tests showed demand `prop` composition fires 0
for `in` (by name AND by id) and `is` (by id) while `same_as` was control.

**Fix (applied, `chain.py` `_rel_matches_pred`):** let the coref substrate `same_as` through the
control filter in the demand matcher — aligning it with the forward matcher — while `focus`/
enumeration still hide `same_as` by PREDICATE (not by control), so it stays infrastructure at
user-facing surfaces. One-line semantic change; verified to green the whole Blocker-A set under
deferred load. (Alternative considered: make `same_as` never-control at the source in `lower_rhs` —
uniform but leaks `same_as` into enumeration/export; the matcher-only fix is more contained.)

NOTE: my earlier claim "demand-driven content coref works" was WRONG — that only worked because a
name-bound query finds a fact on ANY same-named mention via `_candidate_nodes`, needing no `prop`.
Actual `prop` composition never fired until this fix.

<details><summary>Superseded hypothesis (stratified NAF) — ignore</summary>

Eager coref-materialization masks a latent bug in the demand solver's negation handling for
**unbound** (`who …`) goals.

Evidence (thief riddle `THIEF_CW`, `tests/test_isa_ask.py:80`, deferred load):
- Bound queries all correct: `is cy thief`→yes, `is ada thief`→no, `is bo thief`→no.
- Unbound wrong: `who is thief` → `[ada, bo, cy]` (should be `[cy]`). ada/bo are cleared (alibi /
  library→innocent→cleared) so their `not cleared` NAC should block them.
- The failure persists **even with coref/prop removed from the demand set** and **even after
  warming `who is cleared` into the graph first**. So it is NOT missing facts and NOT the prop
  rules producing spurious facts — it is the NAC not blocking in the unbound solve.
- Sub-goals are identical eager vs deferred: `who is cleared`→[ada,bo], `who is a suspect`→[ada,bo,cy],
  `is bo cleared`→yes. So the pieces work; only the NAC-inside-unbound-rule-solve differs.

Hypothesis: in `chain.py`, `_solve_demand_rule` evaluates a rule's NAC (`_nac_blocks`) per bound
env during the outer round-based fixpoint (`chain_sip`). For an unbound outer goal the body binder
(`?x is a suspect`) and the NAC's nested positive closure (`cleared(?x)`) interleave across rounds
in a way that violates stratification timing — the NAC is decided before its positive is fully
closed for that env. Under eager load the extra materialized ground facts make the timing work out.
This is the real prerequisite: **the demand solver must fully close a NAC's positive before
deciding the NAC, independent of the outer goal's binding.**

Fix location: `chain.py` — `_solve_demand_rule` (~606), `_nac_blocks` (~576), `chain_sip` (~686).
Verify against: `test_riddles.py::test_thief_riddle_answers_the_question`,
`::test_vase_riddle_yesno_and_why_not`,
`test_isa_ask.py::test_closed_world_elimination_via_demand_driven_naf`,
`::test_cwa_default_no_vs_owa_optin_unknown`,
`test_contract.py::test_contract_closed_world_elimination`. These should pass under DEFERRED load
BEFORE touching load_corpus (reproduce with the harness in §7).
</details>

### BLOCKER B — the graded/embedding layer needs the eager `prop`
Graded degrees are computed eagerly at load (`graded_rules` then `propagate_embeddings`,
`authoring.py:1282-1283`). For `morningstar is very bright` to get a degree, the graded rule must
know the **use-site** `bright` token is gradable — but `gradable` is declared on a DIFFERENT
`bright` mention (`bright is gradable`) and only reaches the use-site via `prop` across the
same-name `same_as`. Defer `prop` → no degree → value-matches like `close bright` have nothing to
compare → coref rule never fires.

Evidence: `test_isa_value_match.py::test_coref_as_a_declared_rule_composes_close_entities` returns
`no` instead of `yes` under deferred; passes when eager restored.

The general pattern: **declaration/marker predicates on a concept** (`gradable`, `closed world`,
`disjoint`) are stated on one mention and must apply to all same-named mentions. These are the
propagations we DO need; arbitrary content propagation is what we don't.

Design options (pick with the user):
1. Make degree computation demand-driven: compute a mention's degree when a value-match/graded
   condition demands it, resolving `gradable` (following coref) at that point. Vision-pure, most work.
2. Resolve concept declarations (`gradable`/`closed world`/`disjoint`) by NAME at the check point
   (a concept is gradable if ANY same-named mention is declared gradable). Cheap, but is a form of
   name-resolution in the engine — check against the vision (arguably OK: it reads a DECLARATION,
   not general coref-following; still, get user sign-off).
3. Keep a MINIMAL eager pass that propagates ONLY declaration/marker predicates (a small fixed set),
   with all content propagation demand-driven. Pragmatic; violates "no eager pass" in the letter but
   not the spirit (bounded, tiny). Fastest to green.

Affected tests: `test_contract.py::test_contract_graded_defeasible_routing`,
`test_isa_ask.py::test_ask_goal_matches_forward_ask_on_the_defeasible_graded_bank`,
`test_isa_value_match.py::test_coref_as_a_declared_rule_composes_close_entities`,
`test_new_core.py::test_one_graph_context_isolation` (uses `urgent is gradable`).

### BLOCKER C — forward-path consumers expect materialization
Tests/paths using the forward snapshot (`run_rules` / `ask`, not `ask_goal`) legitimately read
pre-materialized coref facts. Under demand-driven coref they must either move to `ask_goal` or run
`prop` explicitly for a forward snapshot (`run_rules(kb, rules)` still re-derives it — that's why
`prop` stays in the returned rule set). Candidates:
`test_isa_runbank.py::test_load_corpus_reasons_correctly_on_run_bank_recognition`,
`test_new_core.py::test_load_corpus_emergent_recognition`. Triage each: is it demand-path (should
pass once A/B fixed) or forward-path (update the test to the demand entry point)?

## 6. Staged implementation plan

Do the stages IN ORDER; each ends green. Keep `load_corpus` eager until Stage 3 so the suite stays
green while you fix the solver underneath it.

- **Stage 0 — regression harness.** Add a tiny bench/repro (see §7) that loads a corpus with `prop`
  deferred and runs the failing queries, so you can iterate on the solver WITHOUT editing
  `load_corpus`. Not a committed test necessarily; a scratch driver is fine.
- **Stage 1 — fix Blocker A** (stratified NAF for unbound goals) in `chain.py`. This is the crux and
  is independent of coref: it makes `who`-style CWA correct demand-driven. Verify the riddle/CWA
  tests pass under the deferred harness. Commit (solver fix stands on its own merit).
- **Stage 2 — decide + implement Blocker B** (graded declarations). Pick option 1/2/3 with the user.
  Verify graded/defeasible tests under the deferred harness.
- **Stage 3 — flip `load_corpus` + `load_facts`** to defer `prop`
  (`run_bank(kb, coref+prop)` → `run_bank(kb, coref)`; keep `coref+prop` in the returned rules).
  Run full suite. Triage Blocker-C stragglers.
- **Stage 4 — measure.** Re-time the demos; expect the coref pass to collapse from ~6.5s to well
  under 1s per load. Update this doc's numbers.
- **Stage 5 (optional) — same_name Cartesian + eager same_as.** The `same_name` rule still pays the
  M² Cartesian (seed it from the name index instead — `machine.py:376` `nodes_named` fast path,
  keeping it a declared value-match rule). And consider whether `same_as` EDGE derivation can also
  be demand-driven (needs `focus.py` + `propagate_embeddings` to not require eager edges;
  `focus.py:251` only SKIPS same_as if present, so it's already safe).
- **Stage 6 (optional, separate) — demo runner.** Make `demos/run.py` load-once (or reload only for
  `why`) to kill the per-question reload multiplier.

## 7. Repro harness (deferred load without touching `load_corpus`)

```python
import ugm as h
from ugm.cnl.authoring import (_recognize, _corpus_lines, _ALL_FORMS, _coref_propagation,
                               expand_rules, expand_loose_from_graph, graded_rules)
from ugm.cnl.forms import mark_mentions, propagate_embeddings
from ugm.cnl.universal import same_name_coref_rules
from ugm.lowering import run_bank
from ugm.cnl.query import ask_goal

def load_deferred(text):
    kb = h.Graph()
    _recognize(kb, _corpus_lines(text), _ALL_FORMS)
    mark_mentions(kb, _ALL_FORMS)
    coref = same_name_coref_rules(); prop = _coref_propagation(kb)
    run_bank(kb, coref)                       # same_as EDGES only; prop DEFERRED
    run_bank(kb, graded_rules(kb)); propagate_embeddings(kb)
    rules = expand_rules(kb) + expand_loose_from_graph(kb) + coref + prop
    return kb, rules
# thief riddle: `who is thief` should be ['cy is thief'] once Blocker A is fixed.
```

## 8. The 11 tests that broke under naive deferral (categorized)

- Blocker A (NAF/CWA/unbound): `test_riddles.py::test_thief_riddle_answers_the_question`,
  `::test_vase_riddle_yesno_and_why_not`,
  `test_isa_ask.py::test_closed_world_elimination_via_demand_driven_naf`,
  `::test_cwa_default_no_vs_owa_optin_unknown`,
  `test_contract.py::test_contract_closed_world_elimination`.
- Blocker B (graded): `test_contract.py::test_contract_graded_defeasible_routing`,
  `test_isa_ask.py::test_ask_goal_matches_forward_ask_on_the_defeasible_graded_bank`,
  `test_isa_value_match.py::test_coref_as_a_declared_rule_composes_close_entities`,
  `test_new_core.py::test_one_graph_context_isolation` (graded + served).
- Blocker C / triage: `test_isa_runbank.py::test_load_corpus_reasons_correctly_on_run_bank_recognition`,
  `test_new_core.py::test_load_corpus_emergent_recognition`.

## 9. Open questions for the user

1. Blocker B: which option (1 demand-computed degrees / 2 concept-declaration-by-name / 3 minimal
   eager marker pass)? Trades vision-purity vs effort.
2. Should `same_as` EDGE derivation also become demand-driven (Stage 5), or is an eager
   `run_bank(kb, coref)` for the edges acceptable (cheap, and `propagate_embeddings`/`focus` want
   the edges present)? The user said "everything demand-driven" — confirm scope.
3. Is a minimal eager marker pass (option B3) acceptable as a stepping stone, or must the first
   landed version have zero eager coref?
