# Procedures + the tool-execution boundary — design notes (2026-07-16, ratified)

> **Status: RATIFIED decisions + a COMPLETE arc** (design notes from user discussion 2026-07-16;
> BUILT 2026-07-16/17, Slices 1–3, suite green). Context: UGM supports agentic harnesses that drive
> execution — following procedures and defining action sequences toward a goal is in scope. Read with:
> `reference/processing_modes.md` (§1 ITERATE, §3 compositions, §4 acceptance test),
> `design/cnl_intake_design.md` §5 (the call/ask wait-set), `design/form_authoring_design.md`
> (the Slice-A form family the surface reuses).
>
> **Arc summary (as built):** the stepping bank is `corpus/procedure.cnl` (content-blind machine
> rules riding the existing planner). Slice 1 = INVOKE/ORDER/GAP-FILL on a pre-made plan. Slice 2 =
> the intake surface — `to NAME : A then B then C` authors + `run NAME` invokes (both HEADER/COMMAND
> ROUTES in `ugm/cnl/procedure_surface.py`, siblings of `form KEY :`, NOT fact-forms), driven by the
> now-stratified `intake._act_loop` (§Slice-2 finding below, realized). Slice 3 = DISCREPANCY/replan
> (a step finished but its effect never showed → mismatch fact → an untried alternative producer runs
> through the same gate). Tests: `tests/test_procedures.py` (author + invoke through real `ingest`).

## 1. The tool-execution boundary (RATIFIED)

**Decision: UGM owns the CALL TOKEN and the FOLD; it EXECUTES calculators; it SUSPENDS world
actions to the harness.**

- **The decision is always UGM's; the transport never is.** A rule materializes a `<call>`
  node — tool name + argument slots as graph data. That token IS "the next action is calling
  X with args Y": inspectable, provenance-carrying, matchable by other rules. UGM knows
  exactly three things about a tool: its **name**, its **argument slots**, and its **fold**
  (how the response lands back as facts). It never knows transport, auth, SDKs, retries —
  that is the harness's identity.
- **Execution splits by the nature of the tool** (the split the machinery already embodies):
  - **Calculators** — arithmetic, the fuel `dec`, the CHECK/CHOOSE/SUPPOSE mode-calls: pure,
    deterministic, engine-adjacent. Serviced INLINE (`run_bank(tools=…)` at quiescence).
    They are part of *reasoning*, not action.
  - **World actions** — HTTP, files, `ask_user`, anything with side effects / latency /
    failure: SUSPEND through `service_calls_cm` → `Event("call", {tool, call, request})` →
    the harness's `.send()` is the world's answer, folded back by the tool's fold half.
    `ask_user` is just a world call in the wait-set `{ask, call}` — one mechanism, no
    special human case.
- **Rationale:** (a) UGM stays deterministic and testable — the bit-for-bit determinism
  survives; a simulated `AsyncTool` exercises the whole loop with no network; (b) **failure
  is data, not control flow** — a tool error folds into facts and RULES react (replan,
  declared retry policy, escalate to ask); UGM needs no exception semantics for the world;
  (c) boundary symmetry — the SLM sits at NL↔CNL, the harness at decision↔world; UGM's
  surface is CNL in, `<call>`/`ask` events out; (d) many harnesses (TUI, server, batch)
  drive one KB through the same `converse` contract with zero UGM changes.
- The sync tool registry is NOT a counterexample: a caller passing Python callables is
  *choosing to be the harness in-process* — the caller's identity, not UGM growing arms.

## 2. The Procedures arc (BUILT — Slices 1–3, see §3–§5)

**The capability:** a named, remembered sequence of steps toward a goal — a PRE-MADE plan the
KB carries as content, invoked like any goal, executed through the one call loop, gap-filled
by the planner where a step's precondition is unmet.

**History:** the previous generation had this (`procedure.py`: `to brew get_water then
add_beans then heat` desugared to planner operators; invocation marked steps `chosen`;
gap-filling connected them to the planner — building its before-gate exposed the NAC-groups
engine fix). Never re-hosted in the rebuild: old-generation equivalence is not a target, no
workload demanded it, and its natural substrate (collections 3.4) stayed queued. The orphaned
`corpus/procedure.cnl` (the one gap-fill bridge rule, referencing deleted consumers) was
removed 2026-07-16; that rule returns as part of the stepping bank below.

**Decomposition — all KB data + declared banks, no engine change.** Passes the
`processing_modes.md` §4 acceptance test: procedure execution is a COMPOSITION
(ITERATE × CALL × CHECK), never a new mode (§3 already sketches exactly this loop).

1. **The step list = collections 3.4** (its driving workload — 3.4 finally has a consumer):
   a `<proc>` node (named, e.g. `brew`) with a member `next`-chain of step nodes; each step
   a call/subgoal TEMPLATE (tool or operator name + argument slots). Same shape as token
   chains, so the substrate is proven.
2. **A universal STEPPING BANK** (domain-blind machine rules, a handful):
   - *invoke* — a `<goal>` naming a procedure seeds the `<current>` cursor on step 1;
   - *step* — `<current>` on a step materializes its `<call>`/subgoal (execution then follows
     §1: calculator inline, world action suspends);
   - *advance* — the step's expected effects CHECK-confirmed → cursor moves to the next
     member (the ITERATE domino);
   - *discrepancy* — a mismatch is a FACT; replan/gap-fill rules match it;
   - *gap-fill* (the resurrected bridge rule) — a chosen step's unmet precondition becomes a
     `<need>`, and the planner banks synthesize the missing sub-plan, ordered `before` the
     step by the existing producer/consumer rule. **Procedure = pre-made plan; planner =
     synthesized plan; same execution gate — they compose.**
3. **The authoring surface** — `to NAME : step then step then step`: a header form in the
   `form KEY :` family (Phase 9 Slice A machinery); the `then`-chain is 3.4's list-authoring
   half (`form.then`'s `X then Y → X before Y` normalization already ships).

**Exit gate sketch:** author a procedure in CNL; `goal`-invoke it; steps execute in order
through the call loop (world steps suspending to the driver); an injected discrepancy
triggers gap-fill/replan; every domain-shaped thing is declared — the stepping bank is
content-blind (§D litmus applies).

**Sequencing:** after Phase 9 Slice B; directly serves the harness client (queue item 1 —
this is the "drive the execution" capability an agentic harness consumes).

**Model routing:** the 3.4 collection encoding + stepping bank ⚠Opus (cursor/collection
vision judgment); the `to NAME :` form ✓S under the Slice-A pattern.

## 3. Slice 1 — the stepping bank (DONE 2026-07-16, 569 green)

`corpus/procedure.cnl` — THREE content-blind machine rules, riding entirely on the existing
planner banks (no engine change, no new substrate):

- **INVOKE** `?s chosen <yes> when <run> proc ?p and ?p step ?s` — a run procedure's steps are
  marked chosen directly (the pre-made plan; planner goal-spray never sees them).
- **ORDER** `?a before ?b when <run> proc ?p and ?a step_before ?b` — the step order is lifted
  into the planner's `before`, honoured at execution by `planning_execution.cnl`'s `waits_for`
  gate (which, its own comment notes, exists for exactly this pure-sequencing case).
- **GAP-FILL** `<need> for ?p when ?o chosen <yes> and ?o pre ?p and not <now> true ?p` — the
  resurrected bridge; an unmet precondition re-enters the planner, which synthesizes + commits
  a filler and orders it before the consuming step (producer/consumer). Procedure = pre-made
  plan; planner = synthesized plan; ONE gate — proven to compose.

Procedure representation (the shape Slice 2's `to NAME :` surface will generate): `NAME step S`
(membership) + `A step_before B` (order) + the invocation request `<run> proc NAME`. This is
the ordered-collection encoding — flat ordered facts, which compose directly with the planner's
`before`, chosen over a literal `next`-chain (the `next`/`first` predicates are the tokenizer's
swept control scaffolding; distinct fact predicates are cleaner and the "collection" is the
`step_before` order).

`tests/test_procedures.py` (2 tests) — also the FIRST in-repo end-to-end run of
`planning.cnl` + `planning_execution.cnl` (the `needs`/`produces` problem surface and the solve
driver are harness-side, so operators are authored in the core `pre`/`add` vocabulary):
(1) ordered execution via the waits_for gate; (2) a missing precondition gap-filled by the
planner and ordered before its consumer.

### FINDINGS (carry to Slice 2 / the act-arm wiring)

- **The planner execution gate needs a STRATIFIED, ITERATIVE solve driver** — `run_rules`
  (stratified) looped to graph-quiescence. Raw `run_bank` (unstratified) RACES: `ready` fires
  before `unmet` is derived (the NAC-over-derived-fact ordering), so a step acts before its
  precondition holds. The test carries a `_solve` loop standing in for the harness driver.
- **⚠ The in-repo `intake._act_loop` uses unstratified `run_bank`** — sufficient for the
  monotone mini-act-bank it was built against, but NOT for the NAC-heavy planner execution
  gate. **Wiring procedures through the `goal …` act arm requires `_act_loop` to stratify**
  (run_rules per cycle, or the harness owns the solve loop). This is a Slice-2 wiring item, not
  a Slice-1 blocker — the bank is proven with the correct driver.
- **A `ready` op acts once** — the `<exec> ready ?o` token persists across solve cycles
  (monotone) and fired-suppression is per-cycle, so the act boundary must guard on `done` (or
  consume the ready token). A world action isn't repeated for a completed step — the guard is
  realistic, not a workaround.

### Slice 2 — the intake surface + act-arm stratification (DONE 2026-07-17)

- **Act-arm stratification (the ⚠ finding above, realized).** `intake._act_loop` now forward-runs
  STRATIFIED (`run_rules` per pass) and loops to GRAPH quiescence (`derived_triples` snapshot equality),
  keeping its async `<call>` suspension. It is now a strict superset of the test's old `_solve` — the ONE
  act driver, UGM-side of the tool boundary (the solve-to-quiescence loop is pure reasoning; only the
  `<call>` suspends to the harness). The `_solve` crutch is deleted.
- **Authoring surface `to NAME : A then B then C`** and **invocation surface `run NAME`** — both are
  intake ROUTES (`ugm/cnl/procedure_surface.py`), siblings of the `form KEY :` header route, NOT
  `FACT_FORM`s. Why not fact-forms: the fact bank is one non-stratified `run_bank` where a procedure
  span-tag would RACE `form.then` (`X then Y -> before`) to the `then` tokens, and `form.then` emits the
  planner's GLOBAL `before`, whereas a procedure needs PROCEDURE-SCOPED `step_before` (lifted to `before`
  only on `<run>`, so a step name shared by two procedures is not ordered globally by one). The routes
  emit `step`/`step_before`/`is_a procedure` directly; `run NAME` seeds `<run> proc NAME` and drives the
  same `_act_loop` a `goal` does. New Outcome/Event kind `"procedure"`.

### Slice 3 — discrepancy / replan (DONE 2026-07-17)

Post-hoc effect-mismatch recovery — §1(b) "failure is data" made concrete. Four rules in
`corpus/procedure.cnl`: DISCREPANCY (`?o done and ?o add ?e and not <now> true ?e` — a step finished but
its effect never showed; `done`+`<now>` are both tool-set together on success, so no false positive and
no strat cycle), EXCLUDE (a durable failed-means record + guard), REPLAN (`?alt chosen when ?o
discrepancy ?e and ?alt add ?e and not ?alt done and not ?alt excluded` — an untried alternative producer
runs through the existing gate + gap-fill), CLEAR (drop the discrepancy once the effect is achieved).

**Stratification finding (load-bearing):** INVOKE's `chosen` MUST stay in the base stratum. The first
design gated INVOKE with `not ?s excluded` (+ drop `chosen`, + route recovery through the planner's
`<need>`/commit) and BROKE gap-fill: any NAC on `excluded` in a `chosen`-producing rule pushes `chosen`
to a stratum after `excluded`(str0), but its consumers `unmet`/`waits_for`/`before` sit in str0 and the
stratifier does not lift a positive consumer to its producer's stratum — so `unmet` under-derives and
`ready` fires before it (the Slice-2 race, re-opened). Fix: don't gate INVOKE, don't drop `chosen`, don't
route recovery through the planner's commit (which pushes `chosen` past `ready`); the stepping bank picks
the alternative DIRECTLY (`done` alone already prevents retrying the failed step). MVP limitation: the
direct rule chooses ALL untried producers of `?e` at once (no cost-ranking); fine for the single-
alternative case, and the planner-routed minimal-recovery path stays blocked by the strat hazard above.
