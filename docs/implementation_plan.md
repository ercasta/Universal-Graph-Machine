# Implementation Plan — Universal Graph Machine (ACTIVE / remaining work)

> **Status: THE ACTIVE PLAN (2026-07-14, post doc-reorganization).** This file holds ONLY remaining
> work. Everything landed lives in `CHANGELOG.md` (dated entries + the phase appendix at its end);
> the as-built system is described by `architecture.md` and the reference docs. The harness (planning
> rule banks, SLM, session, TUI) has its own plan in `harneskills`.
>
> Module paths: `ugm.xxx` (engine), `ugm.cnl.xxx` (CNL surface). Tests: `tests/`. Source: `ugm/`.
>
> Read first: `README.md` (index + decisions in force) → `vision.md` → `reference/logic_fragment.md`
> → `reference/processing_modes.md` → `reference/isa_reference.md` → `architecture.md`. Log landed
> work in `CHANGELOG.md`.
>
> Standing rules: no commits by the assistant; domain logic ONLY in banks; strategies are
> DECLARED data, never engine sniffing; correctness before raw performance.
>
> **RATIFIED 2026-07-10 (user): EQUIVALENCE WITH THE PREVIOUS (rewriter / name-based) GENERATION IS NOT
> A CORRECTNESS TARGET.** The old generation was never used. The goal is a **WORKING, self-consistent
> firmware system**, judged on producing sensible answers on the benches, NOT on reproducing the old
> exhaustive engine's outputs. Real long-pole for a *usable* system = **performance (Phase 7)**, not
> correctness.

## Current state (2026-07-14)

**Suite: 442 passed, 0 failed** (`.venv/Scripts/python.exe -m pytest -q`, ~14s). Production runtime is
100% the ISA engine — no second engine anywhere in the repo. The big arcs are COMPLETE (see CHANGELOG
2026-07-14 for each):

- **Firmware over ISA** — the demand solver's work runs as ISA programs (one matcher, `State.regs`
  bindings, ephemeral `GRADE`/`VMATCH`, compiler-emitted visibility guards, `MEMBER`/`OVERLAY`
  live-sets); `skip_inert` retired — the machine has NO privileged category and NO mode; ONE-GRAPH FOLD
  landed including the API (`chain_sip(g, goal)` / `check(g, goal)` / `suppose(g, asms, preds)`, with
  `rules=` as an optional separate bank).
- **The ISA control machine** — `ControlMachine` (PC, `BRANCH`/`BRANCH_IF`/`CALL`/`RET`/`SUSPEND`/
  `HALT`, `SETI`/`DEC`, control stack, `PRIM`); every Python control driver ported; forward-only plane.
- **Mechanism/policy separation** — Axis A copy-on-delete retraction (privileged `RETIRE` + `<history>`
  records); Axis B `AttrGraph.registers` (focus stack is a register; the demand trace stays a graph
  node because it is EXPLANATION).
- **Phase 8 client spine** — unified intake, focus stack + seed-from-focus bounded attention (probe-
  validated flat curve), streaming `ingest`/`converse` with suspend/resume ask, trace events, runtime
  rule authoring (conflict-as-conversation, disable). 8.5b/8.6 functionally complete.

## Open follow-ons from the completed arcs (small, concrete)

- **Wire real async tools / `ask_user` through `service_calls_cm`** (control machine follow-on, lands
  with Phase 8.5 streaming): the `SUSPEND`/`RESUME` mechanism exists end-to-end with a simulated
  `AsyncTool`; it is a candidate replacement for the generator `_NeedVerdict` unwind.
- **Retire the control-mechanics `<…>` tokens** now that control moved into the machine
  (`attic/isa_control_machine.md` §6/§11 triage: explanation stays graph, mechanics become
  registers/instructions).
- **SUPPOSE scope overlay maintained incrementally by the writers** — today the `OVERLAY` set is
  derived per lookup from the `SCOPE` tags (`chain._scope_pencils`); end-state: `suppose`/`chain`
  writers maintain the register-pointed set, the tag stays the pencil's persistent explanation.
- **Forward-path readers onto the same visibility program** — `apply._fact_relnodes` etc. still read
  scope tags directly; migrate onto the `MEMBER`/`OVERLAY`/guard vocabulary the demand read uses.
- **`<call>` / dispatch state audit** — confirm none of it is a persisted fact-graph node; move
  mechanics to registers/ephemeral.
- **A5 — name the irreducible primitive set** (partially done): TEST-absent, `MEMBER`, `OVERLAY` are
  named ops; still Python: skolem re-finding (`_find_skolem_witness`) and sub-demand raising (a driver
  step in `_round`). Write the closed list down in `reference/isa_reference.md` when it stabilizes.
- **Axis A side item (user's call):** `DROP_CTRL` goes raw; fact/control deletion policy moves above
  the mechanism.
- **Linked subgoal chain** (Axis B "later"): parent→child in-graph pointers so `explain` walks the
  negative's decomposition.
- **pystrider #8c — id-addressed RETRIEVE surface:** "who realizes X" as a **RETRIEVE `<call>` mode**
  (like CHECK/CHOOSE/SUPPOSE in `mode_calls.py`), NOT a `who()` Python helper. Not started.
- **VISION-CLEANUP: get-or-create plumbing should EMIT `MINT`, not poke the substrate** (tagged
  `TODO(vision-cleanup)` in-source): `dispatch._ensure`, `mode_calls._ensure`, `focus._entity_node`.
  Principle ratified: every *semantic* (interning, dedup) is an ISA instruction/program; `add_node`/
  `add_relation` are the dumb loader. ✓S per site (mechanical); ⚠Opus for the "does ALL firmware
  minting become emitted `MINT`" scope call.

## Residuals carried out of done phases (don't lose these)

- **`same_as propagates through X` CNL surface** (from Phase 3.1-step1) — needs coref rules reified;
  `coref_prop` is forward-compatible. Lands with Phase 3 rules-as-data. Also the mechanism half of the
  Phase 5.4 residual below.
- **APPLY-body graded α-cut + inverted ('not at all') cut** (from Phase 5.2 companion) — the CHAIN half
  is DONE (`chain._graded_ok` → now the ephemeral `GRADE` program); the APPLY-body match-time cut
  remains. ⚠Opus.
- **`session.py:CONTENT_PREDS` + Python-generated coref rules** (from Phase 5.4 residual) —
  harness-side; resolves once coref rules reify (bank-authored `same_as propagates through X`).
- RETIRED / not carried: Phase 5.1's "aggressive `is_not` completion" (replaced by demand-driven NAF);
  Phase 2.2's "Phase-6 reader flip" (landed in Phase 6.0); the coref `canonicalize` deletion follow-up
  (already deleted along with `wire_same_as` — interning at the CNL reader replaced them, see
  `attic/indexing_and_coalescing_design.md`).

## Phase 8 — CLIENT: unified CNL intake + focus + streaming (ACTIVE — remaining tail)

> The primary track (ratified 2026-07-12): the first UGM *client* is an **agent loop with a TUI**,
> driven by CNL (the NL→CNL SLM is external; the system boundary is CNL). Load-bearing goal:
> **seamlessness** — the utterance's own structure drives the loop, NO intent-recognition dispatcher.
> Full spec: **`design/cnl_intake_design.md`**. 8.1/8.3/8.5a/8.5b/8.6 are functionally COMPLETE
> (CHANGELOG 2026-07-12); anaphora (8.4) is OFF the roadmap (boundary concern, SLM-side).

**INTAKE-SPINE DISCIPLINE (anti-hardcoding — any session on Phase 8 MUST obey; reviewers reject diffs
that break one).** Full list: `design/cnl_intake_design.md` §D. In brief: (1) route by which FORMS
fired, never by sniffing the utterance string; (2) focus moves are CNL forms; (3) pronoun ranking is
DECLARED defeasible-priority data; (4) rejection/"nearest forms" computed from recognition structure;
(5) `<focus>`/`<query>`/`<goal>` are control tokens via the `<…>`→control chokepoint; (6) no predicate/
English-word STRINGS as control signals in intake code; (7) metareasoning owns only effort/margins.
Litmus: grep intake code for a domain or function word used as a control signal — if one is
load-bearing, it belongs in a bank.

Remaining slices:

- **8.5b tail:** TRUE wall-clock trace interleaving (a live `_record` callback needs coroutine
  reasoning — the generator can't yield from inside the synchronous chain; the control machine's
  `SUSPEND` may now be the mechanism); extend mid-chain gather to who/∃/n-ary questions (v1 covers the
  yes/no-bound path); lazy (relevance-ordered) instead of eager frontier asking.
- ~~**8.5 async wiring**~~ **DONE 2026-07-16:** the GOAL/COMMAND route landed (`form.goal`-minted
  `<goal>` triggers `intake._act_loop`); async tools suspend through `service_calls_cm` as `"call"`
  events (wait-set = `{ask, call}`); §4a nearest-forms rejection computed from the banks; persistent
  `<goal>`/`<call>` scaffolding gets focus-reachability GC (`focus.gc_cold_scaffolding` on narrowing
  moves). ENGINE SIDE OF PHASE 8 COMPLETE — see `design/cnl_intake_design.md` status + §8 build map.
  Remaining Phase 8 work is CLIENT-side (TUI+SLM in `harneskills_new`, consuming the
  `converse`/Event/Outcome contract — UGM owns the contract, user decision 2026-07-16).
- **8.6 perf follow-on:** INCREMENTAL head-index extend (today `_reify_rules` rebuilds per `ask_goal`;
  correctness already right — a new/disabled rule takes effect immediately).
- **Wildcard-closure re-entry (perf lever (b), wire when it bites):** `chain_sip` re-entry redoes the
  closure for a WILDCARD/whole-session goal (bound queries are cheap and focus subsumes the common
  interactive turn — measured 2026-07-14). Fix when wildcard-streaming latency matters: persistent
  tabled frontier / semi-naive delta ACROSS calls via the memo-table-in-`AttrGraph.registers`; the
  control machine's `Continuation` is the mechanism. Differentially gated.

**Model routing for Phase 8:** ⚠Opus for the async/streaming driver work (vision judgment); ✓S for
mechanical parts under the design spec.

## Secondary / parallel tracks

1. **Phase 5 exit gate — bench-sensibility half (harness-side).** Run card-trader + coref + full
   ProofWriter-coverage in `harneskills`. The engine half is MET in-repo (audited 2026-07-11). If a
   bench relying on a domain predicate composing across coref regresses, DECLARE the relation in the
   harness KB — do NOT re-add an engine string.

2. **Phase 3 remaining (rules-as-data / homoiconicity — off the critical path).**
   - ~~3.1 step 2 (one-graph fold)~~ **DONE 2026-07-14** (firmware-over-ISA arc, `PATTERN_MARK`).
   - **3.4:** collections as first-class KB structure: member `next`-chains + list-authoring CNL forms
     (the ITERATE substrate — `reference/processing_modes.md` §1). ⚠Opus.
   - Exit gate: every bank rule round-trips CNL → rule subgraph → rendered CNL.
   - NOTE: meta-circular FORM-rule authoring (the quote/eval wall) stays DEFERRED (scoping 2026-07-09).

3. **Program-as-data homoiconicity** — the next frontier the firmware arc opened: programs the machine
   runs, represented in the graph it runs on (seed-from-focus is already in-machine as `MEMBER` over
   `registers["<focus>"]`; value operands generalize by "just change the lowering program" —
   `attic/isa_value_operands_design.md` §6). ⚠Opus (design work, not yet a concrete slice).

## Phase 7 — PERFORMANCE track (after correctness — user standing rule)

In leverage order:
- **(a)** Intern keys/values to ints, CSR adjacency, bitset candidate sets. **The LOW-RISK first rung,
  in PURE PYTHON** (dispatch-table `_match_step`, int-interned keys, array/`__slots__` register states).
  Likely 2–3× at near-zero risk. Do this BEFORE (b) if perf bites. ✓S for mechanical rungs with
  benchmarks; ⚠Opus for design. NOTE: for the agent-loop client the axis that matters is session
  accretion (answered by seed-from-focus), not total-KB size — don't start 7a for the client's sake.
- **(b) → Phase 7b: Rust core, Python surface.** ⭐ FULL PLAN: **`design/rust_engine_plan.md`**.
  STRATEGY (user-ratified): procedures became ISA FIRMWARE first (Phase A — now DONE, 2026-07-14), so
  Phase B ports ONLY the interpreter — the procedures come along as DATA both interpreters run.
  MEASURED CONSTANT: match inner loop ~381× (`bench/rust_pilot/`). GUARDRAILS: perf NOT the current
  bottleneck; Rust = CONSTANT, focus = CURVE; Amdahl-bounded; the Python engine STAYS the reference
  oracle, differential-tested; FREEZE the ISA first. Start only when a real target-scale workload is
  too slow AND (a) is exhausted. ✓S for the mechanical slices under the differential gate.
- **(c)** Per-rule AOT codegen = partial evaluation of APPLY (Soufflé-style), differentially gated.
- **(d)** Two-tier execution for runtime-edited rules — fresh rules interpret, stable-hot rules compile
  in background, version-stamp invalidation on edit. JIT only if profiling demands it.
- **Perf levers (b')(c') from the demand-negation work** (query already sub-second at session scale):
  semi-naive worklist so a demand re-services only when a relevant fact appeared; the domain coref
  `same_as.*.is` demand fan-out (bounded by focus in practice). ALSO: `why` provenance is
  order-sensitive (a fact pre-derived without provenance renders `(given)`).

## Placeholders / optional follow-ons (not concrete tasks)

- **Broader FirmwarePolicy stance surface** — no third opinion is pending. Candidates ONLY if a
  workload needs one: CHOOSE tie-break / always-provenance `why` / default α-cut.
- **Prose `suppose … predict …` sugar** folding to the reified encoding (new surface → SLM debt).
- **`tests/test_joern_corpus.py`** — legitimately slow, live-Joern; candidate for a `slow` marker.

## Model routing

⚠Opus = needs vision-judgment; ✓S = Sonnet-safe where a gate/spec catches deviation.
- Phase 8 async/streaming driver work: **⚠Opus**; mechanical slices under spec: **✓S**
- Phase 7(a): **✓S** with benchmarks for mechanical rungs; **⚠Opus** for design + AOT codegen
- Phase 3.4 collections; program-as-data design: **⚠Opus**
- APPLY-body α-cut + inverted cut: **⚠Opus**
- Vision-cleanup MINT-emission sites: **✓S** per site; **⚠Opus** for the scope call

## Risks

- **Session accretion is the client's real perf risk** (`critique.md` §4.1a), NOT total-KB size.
  Answered by seed-from-focus (8.3b) and validated by the probes; re-validate if the client workload
  changes shape.
- **Habitability at the CNL boundary** (`critique.md` §4.4) — an unrecognized utterance must be an
  actionable rejection, not a dead end. Handled by unified intake; keep it true as forms grow.
- **Performance (Phase 7) is the long-pole for the GENERAL engine**; for the client it is reframed as
  session accretion. Correctness risk is < 5% impossible-blocker.
- **SLM surface debt** accumulates from CNL form changes — batch retrains via the ledger in
  `harneskills` (`handoff_slm_surface_track.md`).
- **Meta-debugging** — the Phase 4 trace renderer is the mitigation; it is complete.
