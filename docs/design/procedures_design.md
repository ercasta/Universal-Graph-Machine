# Procedures + the tool-execution boundary — design notes (2026-07-16, ratified)

> **Status: RATIFIED decisions + a QUEUED arc** (design notes recorded from user discussion
> 2026-07-16; not yet an active build — slotted after Phase 9 Slice B in
> `implementation_plan.md`). Context: UGM supports agentic harnesses that drive execution —
> following procedures and defining action sequences toward a goal is in scope. Read with:
> `reference/processing_modes.md` (§1 ITERATE, §3 compositions, §4 acceptance test),
> `design/cnl_intake_design.md` §5 (the call/ask wait-set), `design/form_authoring_design.md`
> (the Slice-A form family the surface reuses).

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

## 2. The Procedures arc (QUEUED)

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
