# Implementation Plan — Universal Graph Machine (ACTIVE / remaining work)

> **Status: THE ACTIVE PLAN (re-pointed 2026-07-16 — see "Current focus").** This file holds ONLY remaining
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

## Current focus (re-pointed 2026-07-16 — Phase 8's engine side is COMPLETE)

Every substrate-side arc that was in flight is now closed (see CHANGELOG 2026-07-16 entries and the
per-arc docs): mechanism/policy BOTH AXES (incl. the discriminator audit), the possibilistic layer
(incl. the polish batch: kind-wearing verdicts, env-rendering, stance CNL, fork-leak fix), the whole
explanation arc (linked subgoal chain + certain-NAF assumed-records), Phase 8's engine side
(goal/act route with async-tool suspend, nearest-forms rejection, focus-reachability GC), and the
parked-item cleanup (demand-coref CLOSED-as-settled; INTERPOSE/RESTORE deleted). The book is synced.

**Also closed (2026-07-16, the compliance/revision session):**
- **ISA-compliance pass** — every driver write is an ISA program (`provenance.record_firing` =
  the ONE justification-minting path; retraction RECORD = MINT+`REDIRECT`; suppose/possibility/
  choose writes lowered); new gated opcodes `REDIRECT` (privileged, retraction-only) and `SWEEP`
  (control-node deletion, refuses facts/provenance); BORN-CONTROL token skolems
  (`lower_rhs.resolve`), so every scaffolding deletion flows through `SWEEP`/`DROP_CTRL`; the
  superseded APPLY frame-matcher DELETED (`apply.py` = shared readers + head index).
- **Determinism + demand subsumption** — substrate adjacency/indices are insertion-ordered
  dict-as-set (the 30× PYTHONHASHSEED work-variance fix; runs are bit-for-bit reproducible on the
  fast topology); `_round` skips demands whose strict generalization stands (halves adversarial
  topologies, +0.45% on the fast path).
- **RECONSIDER (`design/reconsider_design.md`, BUILT)** — demand-driven revision of materialized
  NAF conclusions: intake marks `(pred, obj)` grains in registers; the next committed ask re-checks
  affected `<assumed>` records and withdraws broken support (cascade + copy-on-delete, history
  stamped `broken_assumption`); forward `run_bank` journals its survived NACs too (provenance=True);
  committed intake asks run provenance ALWAYS-ON (user-ratified; +15% heavy whole-graph ask).
- **Hard-vs-assumed surfacing capstone** — `ask_goal` verdicts wear their kind in every stance
  (`no` / `no (assumed)` / `unknown`); book synced (chs. 0/3/4/5/8/9/10/19 + appendix; ch. 8 tells
  the self-revision story).
- **Habitability hardening** — inverted why-question forms; the keyword-in-name-slot lint
  (`query._kw_in_name_slot`): a mis-parse is UNRECOGNIZED (loud wall + nearest-forms), never a
  silent wrong answer.

**The queue, in order:**

1. **The CLIENT — rebuild `harneskills_new` against the `converse`/Event/Outcome contract**
   (external repo; UGM owns the contract — user decision 2026-07-16, recorded in
   `design/cnl_intake_design.md`). The harness's own session/driver/interaction scaffolding predates
   the intake spine and duplicates it; the end-state is a `Session` that only drives `converse` and
   renders events (TUI), with the SLM at the NL→CNL boundary (anaphora via `focus.top_centers`).
   The **Phase 5 exit-gate bench half** (card-trader + coref + ProofWriter coverage) rides along —
   it runs in the harness. Nothing in this repo blocks it; engine gaps found there come back here as
   feedback items.
2. **CNL FORM AUTHORING (Phase 9 — RE-SCOPED + RATIFIED 2026-07-16).** ⭐ DESIGN:
   **`design/form_authoring_design.md`** — build by its §5 slices. The original
   "forms-as-KB-data" scope (migrate every bank to KB-resident reified rules, self-hosting
   kernel, zero-`Rule`-literals gate) was CUT after benefit decomposition (design §6): the
   shipped banks are frozen in practice, `Rule` lists are already DATA to the lowering (so the
   Rust boundary was already final), habitability already derives from `Rule` structure, and
   in-engine grammar metareasoning — the only capability reification enables — is ruled out
   (user, 2026-07-16). What remains is the capability that was genuinely missing: **the grammar
   is extensible from the outside, in CNL** — `form KEY : HEAD when BODY` (machine grammar +
   new `rl_key` naming form), recognized at intake and in loaded KB files (multi-KB model,
   strict declare-before-use), routed to its bank by its own RHS structure, disable/nearest-
   forms covered, persisted as the CNL line itself. Enabling finding kept: rule-source CNL
   already spans the form language (bound-literal tokens `is?`/`<query>?`; NAC-group
   independence) — full reification stays a proven, parked path. Exit gate
   (capability-shaped): a domain KB file declares a new sentence shape in CNL; facts and
   questions in that shape parse; nearest-forms and disable cover it; no Python edited.
   **Slices A+B DONE 2026-07-16 (567 green)** — `cnl/form_authoring.py` (`form KEY :` grammar,
   `rl_key`, safety lint, key-merge) + intake FORM route + D3 bank placement + `load_kb`
   (multi-KB-file, declare-before-use); nearest-forms/disable cover authored forms. Exit gate
   MET (a KB file declares new shapes; parse/answer/suggest/disable all work; no Python edited).
   Remaining: optional Slice C (exemplar sugar) + the book authoring-chapter section.
3. **PROCEDURES (queued arc — design notes RATIFIED 2026-07-16: `design/procedures_design.md`).**
   Sequences of actions toward a goal — the agentic-harness "drive the execution" capability,
   after Phase 9 Slice B. Decomposition (all KB data + declared banks, NO engine change —
   composition ITERATE × CALL × CHECK, passes `processing_modes.md` §4): **collections 3.4**
   (step lists as member `next`-chains — 3.4's driving workload, absorbed here) + a universal
   **STEPPING BANK** (invoke/step/advance/discrepancy + the resurrected planner gap-fill
   bridge; procedure = pre-made plan, planner = synthesized plan, same execution gate) + a
   **`to NAME :` authoring form** (Slice-A family). TOOL BOUNDARY RATIFIED same day (design
   notes §1): UGM owns the call token + the fold, executes CALCULATORS inline, SUSPENDS world
   actions to the harness (`Event("call")` / `.send()`); failure is data rules react to.
4. **Phase 7b — the Rust interpreter port** (full plan `design/rust_engine_plan.md`). Fully
   unblocked: procedures became ISA firmware first (Phase A done 2026-07-14; the 2026-07-16
   compliance pass closed the driver-write gaps), so Phase B ports ONLY the interpreter and the
   instruction set is the frozen contract. Measured prize: 381× on the match loop. The former
   "after Phase 9" ordering constraint DISSOLVED with the 9 re-scope (the data/interpreter
   boundary was already final — `Rule` lists are data to the lowering); start whenever a real
   target-scale workload is too slow and 7(a) is exhausted.

Small in-repo residuals live in their homes, none blocking: the 8.5b tail + perf levers below
("until they bite"), the possibilistic feature threads (`possibilistic.md`: abduction SUPPOSE,
propagation-strength knob, S7.7 band scale), and the Phase 3 leftovers (below).

## Current state (2026-07-16)

**Suite: 538 passed, 0 failed.** Production runtime is
100% the ISA engine — no second engine anywhere in the repo. The big arcs are COMPLETE (see CHANGELOG
for each):

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

## Phase 8 — CLIENT: unified CNL intake + focus + streaming (ENGINE SIDE COMPLETE 2026-07-16 — residuals only)

> The first UGM *client* is an **agent loop with a TUI**, driven by CNL (the NL→CNL SLM is external;
> the system boundary is CNL). Load-bearing goal: **seamlessness** — the utterance's own structure
> drives the loop, NO intent-recognition dispatcher. Full spec: **`design/cnl_intake_design.md`** —
> its §8 build map shows every substrate row BUILT; what remains of Phase 8 is the CLIENT itself
> (queue item 1 above, in `harneskills_new`). The slices below are non-blocking residuals.
> Anaphora (8.4) is OFF the roadmap (boundary concern, SLM-side).

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
     (the ITERATE substrate — `reference/processing_modes.md` §1). ⚠Opus. ABSORBED into the
     PROCEDURES arc (Current-focus queue item 3, `design/procedures_design.md`) — step lists
     are its driving workload.
   - Exit gate: every bank rule round-trips CNL → rule subgraph → rendered CNL.
   - NOTE: meta-circular FORM-rule authoring (the quote/eval wall) — RESOLVED 2026-07-16: the
     wall needs no new machinery (rule-source CNL already expresses forms; finding recorded in
     `design/form_authoring_design.md` §1). The authoring surface is **Phase 9 (CNL form
     authoring)**, item 2 of the Current-focus queue; FULL bank reification was cut (design §6)
     and stays a parked, proven path.

3. **Program-as-data homoiconicity** — the wider frontier the firmware arc opened: programs the
   machine runs, represented in the graph it runs on (seed-from-focus is already in-machine as
   `MEMBER` over `registers["<focus>"]`; value operands generalize by "just change the lowering
   program" — `attic/isa_value_operands_design.md` §6). Phase 9 is its first concrete slice
   (rules-as-data was the zeroth); the rest stays design-track (⚠Opus).

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
