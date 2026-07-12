# Implementation Plan — Universal Graph Machine (ACTIVE / remaining work)

> **Status: THE ACTIVE PLAN (2026-07-12, post done-split).** This is the UGM-only continuation of
> the original `harneskills` plan. Completed phases + landed milestones + settled rationale trails
> moved to `implementation_plan_done.md` (2026-07-12). This file is ONLY the remaining work.
> The harness (planning rule banks, SLM, session, TUI) has its own plan in `harneskills`.
>
> Module paths after split: `ugm.xxx` (was `harneskills.isa.xxx`); `ugm.cnl.xxx` (was
> `harneskills.xxx` for CNL-level modules). Tests: `ugm/tests/`. Source: `ugm/ugm/`.
>
> Read first: `reference.md` → `vision.md` → `logic_fragment.md` → `processing_modes.md`
> → `graph low level machine/isa-reference.md` → `architecture.md`. Log landed work in `CHANGELOG.md`.
>
> Standing rules: no commits by the assistant; domain logic ONLY in banks; strategies are
> DECLARED data, never engine sniffing; correctness before raw performance.
>
> **RATIFIED 2026-07-10 (user): EQUIVALENCE WITH THE PREVIOUS (rewriter / name-based) GENERATION IS NOT
> A CORRECTNESS TARGET.** The old generation was never used. The goal is a **WORKING, self-consistent
> firmware system**, judged on producing sensible answers on the benches, NOT on reproducing the old
> exhaustive engine's outputs. Impossible-blocker chance < 5%. Real long-pole for a *usable* system =
> **performance (Phase 7)**, not correctness.

## Current state

**Suite: 258 passed, 0 failed** (`python -m pytest -q`, ~54s post perf-lever-(a)). Production runtime is
100% the ISA engine, and so is every test — no second engine anywhere in the repo. `ask_goal` is
demand-driven; `rewriter.py`/`goal.py`/`walker.py`/`decide.py`/`solve.py` are all deleted.

Phases 0–2, 3.1-step1, 3.3, 4, 5, 6.0/6.1, firmware v3 (demand-driven negation), stance-as-data, and
perf lever (a) are **DONE** — see `implementation_plan_done.md` and `CHANGELOG.md`. **Do NOT re-do them;
do NOT resurrect `decide.solve`, `solve.py`, or the demand/coref/walk/asp leftovers.**

## Residuals carried out of done sections (don't lose these)

These were TODOs embedded in now-done phases; they live in the open work below:
- **`same_as propagates through X` CNL surface** (from Phase 3.1-step1) — needs coref rules reified;
  `coref_prop` is forward-compatible. Lands with Phase 3 rules-as-data. Also the mechanism half of the
  Phase 5.4 residual below.
- **APPLY-body graded α-cut + inverted ('not at all') cut** (from Phase 5.2 companion) — the CHAIN half
  is DONE (firmware v3 `chain._graded_ok`); the APPLY-body match-time cut remains. ⚠Opus.
- **`session.py:CONTENT_PREDS` + Python-generated coref rules** (from Phase 5.4 residual) — harness-side;
  resolves once coref rules reify (bank-authored `same_as propagates through X`).
- RETIRED / not carried: Phase 5.1's "aggressive `is_not` completion" (replaced by demand-driven NAF);
  Phase 2.2's "Phase-6 reader flip" (landed in Phase 6.0).

## Phase 8 — CLIENT: unified CNL intake + focus + streaming (ACTIVE — the current build)

> **This is now the primary track (2026-07-12, ratified with the user).** The first UGM *client* is an
> **agent loop with a TUI**, driven by CNL (the NL→CNL SLM is external; the system boundary is CNL). The
> load-bearing goal is **seamlessness** — a CNL utterance's own structure drives the loop with NO
> intent-recognition dispatcher. Full spec: **`docs/cnl_intake_design.md`**. This reroutes the plan onto
> the client build; the old NEXT STEP items become secondary/parallel tracks below. **Phase 3.2 (runtime
> rule edits) is ABSORBED here** (§8.6). The perf priority shifts from Phase 7a (total-KB size, wrong
> axis for this client) to **session accretion** (`docs/critique.md` §4.1a), answered by seed-from-focus.

Build slices, in dependency order (each with tests; the probe first to validate the premise):

- **8.0 — accretion + suspend/resume PROBE (first, diagnostic).** Measure per-utterance latency across a
  growing transcript; confirm (1) seed-from-focus keeps it flat (not tracking accumulated session), and
  (2) suspend/resume on `chain_sip` preserves the demand frontier. Run BEFORE building the spine on the
  premise. Design §7.
- **8.1 — unified intake entry + routing.** One entry: tokenize into the LIVE substrate (control-flagged)
  → `normalize_surface` → recognize → route fact / rule / `<query>` / `<goal>` / rejection by fired form.
  Eliminates the caller-side question-vs-assert fork. Design §1.
- **8.2 — `<query>` as a live control node.** Retire the throwaway-graph question path; a `<query>` lands
  control-flagged in the KB and raises its demand over the live graph. Monotonicity kept by the
  control/fact split. Design §2.
- **8.3 — `<focus>` stack + centers + seed-from-focus.** Pointer-at-center (extent DERIVED, not
  scope-as-subgraph); seed scope = top frame's centers; implicit widen-only + explicit `focus on`/`forget
  that`/`back to` (reuse SUPPOSE scope ops); scaffolding GC by reachability from focus roots. Design §3.
- **8.4 — anaphora as reasoning.** Descriptive → CHOOSE over centers; bare pronouns → CHOOSE over graded
  defeasible preferences (recency+role default, domain-overridable); metareasoning owns only the
  ask-vs-guess margin → near-tie escalates via the existing `ask_user`. Design §4. Habitability rejection
  outcome (§4a) lands with 8.1.
- **8.5 — event-emitting + resumable driver; suspend/resume `ask_user`.** Event sink at existing step
  boundaries (reuse RECORD/`<j:>` provenance as the substrate); generalize the blocking `ask_user` into
  suspend→return→resume with the pending question as a graph node. Wait-set v1 = `{ask_user}`. Design §5.
- **8.6 — runtime rule authoring (Phase 3.2, global KB concern).** `HEAD when …` lands via the same
  intake, reifies, reasons immediately; incremental head-index extend; RE-LINT stratification per add
  (`on_cycle` stance); conflict-lint AS CONVERSATION (a contradictory rule is rejected by ASKING, via the
  8.5 channel); disable = `<disabled>` marker (no deletion §5). Design §6.

**Model routing for Phase 8:** ⚠Opus for 8.1/8.2/8.3/8.5 (control/fact segregation, discourse model,
driver resumability — vision judgment); ✓S for 8.0 (probe/benchmark) and mechanical parts of 8.4/8.6
under the design spec.

## Secondary / parallel tracks (was NEXT STEP; run alongside or after Phase 8)

1. **Phase 5 exit gate — bench-sensibility half (harness-side).** Run card-trader + coref + full
   ProofWriter-coverage in `harneskills`. The engine half is MET in-repo (audited 2026-07-11); this half
   is not verifiable from this repo. NOTE: Phase 2.5 de-hardcoded the domain coref predicate list — coref
   now composes over `relation_predicates(graph)` + declared relations/prepositions, NOT a fixed engine
   list. A bench relying on a domain predicate composing across coref should Just Work if the predicate is
   present as a relation (default-grammar `in`/`has`/`before` included); if one regresses, DECLARE the
   relation in the harness KB — do NOT re-add an engine string.

2. **Phase 6.2 remaining (docs converge).** Two items left after the architecture-half landed:
   (a) refresh `reference.md`'s doc-map — it still lists `architecture.md` as pre-rehost / "must be
   rewritten at Phase 6.2", which is now stale (the rewrite landed 2026-07-12); also add the three engine
   docs (`architecture.md`, `engine_developer_guide.md`, `engine_user_guide.md`) to the LIVE map;
   (b) confirm finished phases are summarized in `CHANGELOG.md` (it is well-maintained; this is a
   verification pass, not new writing). ✓S.

3. **Phase 7(a) — the stated long-pole.** Now that 2.3 settled the name/key/value model, intern keys/
   values to ints + CSR adjacency + bitsets on a CLEAN representation (no bridge). ✓S for mechanical rungs
   with benchmarks; ⚠Opus for design.

4. **Demand-driven-negation PERF follow-on levers (b)(c)** (Phase 7-adjacent — the query is already
   sub-second at session scale, so this is optimization not correctness):
   - (b) semi-naive worklist so a demand re-services only when a relevant fact appeared (the round loop
     still re-services the whole local agenda each round; the profile's top is now `relations_from`/
     `_read_atoms` re-reading static reified-rule structure per service).
   - (c) the domain coref `same_as.*.is` demand fan-out.
   ALSO: `why` provenance is order-sensitive (a fact pre-derived without provenance renders `(given)`) —
   design AS-BUILT §5.

5. **Phase 3 remaining (rules-as-data / homoiconicity — off the critical path).**
   - **3.1 step 2:** demonstrate/prove pattern nodes stay fact-INVISIBLE when a rule fragment is folded
     into a live fact graph (control flag = segregation) — the one-graph fold. ⚠Opus (control/fact
     segregation). HAZARD: ephemeral APPLY frames add incoming edges to fact nodes; previewed and
     controlled by GC-after-pass, but the full fold needs care.
   - **3.2:** runtime rule edits by user CNL — **ABSORBED into Phase 8.6** (the client needs it as a live
     capability: add = same path as facts; disable = additive `<disabled>` marker; no deletion §5).
   - **3.4:** collections as first-class KB structure: member `next`-chains + list-authoring CNL forms
     (the ITERATE substrate — `processing_modes.md` §1). ⚠Opus.
   - Exit gate: every bank rule round-trips CNL → rule subgraph → rendered CNL.
   - NOTE: the meta-circular FORM-rule authoring (the quote/eval wall) is DEFERRED as a homoiconicity-
     purity milestone off the critical path (scoping decision 2026-07-09).

## Placeholders / optional follow-ons (not concrete tasks)

- **Broader FirmwarePolicy stance surface.** The stance-as-data work landed the two knobs the audit named
  (`negation_default`, `on_cycle`). A broader surface is a PLACEHOLDER — no third opinion is pending.
  Candidates ONLY if a workload needs one: CHOOSE tie-break / always-provenance `why` / default α-cut.
- **Prose `suppose … predict …` sugar** folding to slice 3c's reified encoding (new surface → SLM debt;
  deferred like `to NAME`, pick up if the SLM ledger is being retrained).
- **`tests/test_joern_corpus.py`** — legitimately slow, live-Joern; candidate for a `slow` marker.

## Phase 7 — PERFORMANCE track (after correctness — user standing rule)

In leverage order:
- **(a)** Intern keys/values to ints, CSR adjacency, bitset candidate sets — see NEXT STEP item 3.
- **(b)** Rust (PyO3) inner loop for Machine + store; Python stays the shell.
- **(c)** Per-rule AOT codegen = partial evaluation of APPLY (Soufflé-style), differentially gated.
- **(d)** Two-tier execution for runtime-edited rules — fresh rules interpret, stable-hot rules compile in
  background, version-stamp invalidation on edit. JIT (Cranelift/copy-and-patch before LLVM) only if
  profiling demands it.

## Model routing

⚠Opus = needs vision-judgment; ✓S = Sonnet-safe where a gate/spec catches deviation.
- Phase 5 exit gate (classify divergences / bench sensibility): **⚠Opus**
- Phase 6.2 remaining (doc-map refresh + CHANGELOG verification): **✓S**
- Phase 7(a) (intern/CSR/bitset): **✓S** with benchmarks for mechanical rungs; **⚠Opus** for design + AOT
  codegen
- Perf levers (b)(c) + `why` provenance ordering: **✓S** with benchmarks / differential gate
- APPLY-body α-cut + inverted ('not at all') cut: **⚠Opus**
- Phase 3.1 step 2 (one-graph fold): **⚠Opus** (control/fact segregation). 3.2/3.4: **⚠Opus**

## Risks

- **Session accretion is the client's real perf risk** (`docs/critique.md` §4.1a), NOT total-KB size —
  the monotone graph grows with the transcript. Answered by seed-from-focus (Phase 8.3) and validated by
  the 8.0 probe. Phase 7a interning is the WRONG axis for the agent-loop client; deprioritized.
- **Habitability at the CNL boundary** (`docs/critique.md` §4.4) — an unrecognized utterance must be an
  actionable rejection ("didn't understand X; nearest forms"), not a dead end. Falls out of the unified
  intake (Phase 8.1/§4a) as the empty-recognition case.
- **Performance (Phase 7) is the long-pole for the GENERAL engine** post the no-equivalence ratification;
  for the client it is reframed as session accretion above. Correctness risk is < 5% impossible-blocker.
- **SLM surface debt** accumulates from CNL form changes — batch retrains via the ledger in `harneskills`
  (`handoff_slm_surface_track.md`).
- **One-graph fold hazard (Phase 3.1 step 2)** — ephemeral APPLY frames add incoming edges to fact nodes;
  previewed and controlled by GC-after-pass, but the full fold needs care.
- **Meta-debugging** — the Phase 4 trace renderer is the mitigation; it is complete.
