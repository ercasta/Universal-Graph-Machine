# Mechanism / Policy Separation — Axis B: control state → machine registers

> **Status (2026-07-16): ARC COMPLETE.** Everything below stands, plus: the dynamic ITERATE trip
> count (§4b), the linked subgoal chain + certain-NAF assumed-records + kind-wearing banded verdicts
> (§5.4), and the closing DISCRIMINATOR AUDIT over the remaining `<…>` state (§8) — which found
> every remaining item already on the right side of the line and RESOLVED the `is_control`
> retirement question by reversal (the marker is load-bearing visibility mechanism for
> graph-resident explanation/pencil/pattern, not a vestige). Suite: **531 passed**.
>
> Original probe record follows.
>
> ✅ **Mechanism + Probe 1 built; Probe 2 attempted and REVERTED (2026-07-14).** The
> control-register file (`AttrGraph.registers`) landed, and the discourse **focus stack** moved into it.
> A second lift (the demand **search trace**) was tried and REVERTED: the demand/subgoal chain turned out
> to be *explanation* (the negative's provenance), not mechanical stepping, so it stays a matchable graph
> node — see §4/§5. That reversal is the sharpest finding of this probe: it draws the register/graph line
> exactly. **`ITERATE`** (§8's exemplar — a loop whose counter is a register value, not a minted node)
> also landed (§4b). Suite: **355 passed**. Second half of the thesis in
> `docs/attic/mechanism_policy_separation.md` (Axis A = copy-on-delete retraction, done). Prerequisite reading:
> that doc's §1 (two homes) and §8.
>
> **Timing (session scale, 2026-07-14):** per-utterance `ingest` median **~12 ms** (8–16 ms across
> icecream/barista/cards/planning/risk) — healthy interactive latency, the scale that matters (perf is
> judged per-utterance, not data-scale). Corpus load 2–49 ms/line; `planning.cnl` is the outlier (~49
> ms/line — heavy rule reasoning). `ITERATE` is linear at ~13–17 µs/iteration (the register-counter loop
> adds no graph-node overhead). Suite ~13 s / 355 tests (slowest single 2.76 s).

---

## 1. The thesis

`docs/attic/mechanism_policy_separation.md` §1/§8: **execution/control state belongs in machine
registers/pointers, not in data-graph nodes.** The ISA baked control-vs-fact into nodes (`is_control`
flag + the `<…>` naming convention), so machine state — a focus cursor, a demand agenda, a search
trace — lived in the data graph as `<focus>`/`<demand>` nodes, indistinguishable in *kind* from facts.

**Two HOMES (ratified):**
- **the graph** holds everything *reasoned-over* — facts AND their explanation/provenance/history.
  Explanation MUST be matchable data in the SAME graph or the system can't reason about its own
  reasoning (meta-rules, TMS, the retraction cascade, `why`).
- **registers** hold execution state that explains nothing — the focus cursor, a demand search trace,
  loop/iteration counters. This is the ONLY thing that physically leaves the graph.

**The discriminating test:** does *anything reason about it* — including reasoning about the reasoning?
If yes → **graph** (data or explanation, visibility-scoped). If it only answers *"how did the machine
step?"* → **register**. Ratified corollary (2026-07-14): **"explanation is not how the machine
stepped."** This cuts BOTH ways, and the demand chain is where it bites (§4/§5):
- the AGENDA / worklist / iteration order / loop counter = mechanical stepping → **register**;
- the SUBGOAL CHAIN ("to answer X I needed Y, which needed Z") is **explanation** — the negative's
  provenance (an assumed-no is justified by the searched closure) — so it → **graph**, matchable, exactly
  like a positive's `<j:>` proof tree. "No rule branches on it" is NOT the test (no ordinary rule branches
  on `<j:>` provenance either — only meta-rules do, and it still lives in the graph so it CAN be reasoned
  about). "Is it explanation?" is the test.

---

## 2. The mechanism: `AttrGraph.registers`

A single new field on the substrate (`ugm/attrgraph.py`): `self.registers: dict[str, object] = {}`.

- A **control-register file** — named slots (string key → arbitrary Python value). It is PHYSICALLY
  separate from the node/edge store (`_nodes`/`_out`/`_in`), so `match`/`seed`/`nodes()`/
  `derived_triples` never see it. Control state is thereby *not a fact* by construction — no `<…>`
  node, no `is_control` flag, no chance of leaking into fact matching.
- A slot holds **an arbitrary heap object** — a list, a set, a linked stack. So a register is not a
  fixed hardware slot; it is a *pointer to machine memory*. This matters for §5.
- `copy()` deep-copies `registers`, so the register file travels with the graph (a suppose trial copy,
  a serialized KB) — persistence without graph nodes. Deterministic (plain Python containers), so the
  reproducibility constraint holds.

This is the vision's "`State.regs` is already a register file of pointers-to-nodes, used ephemerally and
invisibly to rules" — made **persistent** and **graph-scoped** (survives across programs/passes),
instead of the ephemeral per-program `State.regs`.

---

## 3. Probe 1 — the discourse focus stack (`ugm/focus.py`)

**Was:** a `<focus>` STACK in the data graph — `<focus>` frame nodes, `newer -[below]-> older` links,
`frame -[center]-> entity` pointers; drop = "cut the pointer nodes, keep the entity" + `gc_disconnected`.

**Now:** `kb.registers["focus"]` — a plain list of frames, each frame an ordered list of center **names**.
Frame `[-1]` is TOP.

- **Why names, not node-ids:** focus is *name-grained attention* — the discourse handle the SLM resolves
  anaphora to, and exactly what `top_centers` already feeds `fscope` (a set of names). Storing names makes
  focus a PURE register with **zero** graph coupling.
- **Payoff:** a `drop` is now **graph-neutral by construction** — focus never linked the entities, so
  there is nothing to cut and no §5 fact-deletion risk (the old "keep the entity" guarantee is now
  trivially true). No focus node can leak into fact matching, ever.
- **API preserved** (`push_focus`/`widen`/`drop_focus`/`reenter_focus`/`top_centers`/`top_frame`), so the
  sole consumer (`intake.py`) and all 15 `test_isa_focus.py` tests are unchanged and green. Recognition of
  the explicit control-CNL (`FOCUS_FORMS`, `recognize_focus_op`) stays graph/rules — that is *parsing an
  utterance* in a scratch graph, legitimately data; only the persistent focus STATE moved to the register.

Retired: `FOCUS`/`CENTER`/`BELOW` node vocabulary, `_frames`/`_covered`/`_entity_node`/`_center_*`/
`_drop_top` (and their `add_node`/`add_relation`/`remove_node`/`gc_disconnected` pokes).

---

## 4. Probe 2 — the demand search trace: ATTEMPTED, then REVERTED

**The attempt.** The demand chain minted a VISIBLE `<demand>` control node per top-level magic-set element
(`for=/subj=/obj=`), read by `bound_demands`/`demanded_preds`/`render_demands` for the "what I looked for"
trace. Since the **agenda** (the worklist that drives evaluation) was ALREADY a Python-local set
(`chain_sip`'s `agenda`) and `rule_g` is per-query, it *looked* like the `<demand>` nodes were pure trace,
so they were lifted to `rule_g.registers["demand_trace"]`. Tests stayed green (the outputs are identical).

**Why it was WRONG (reverted).** The "what I looked for" trace is what makes an assumed-no / UNKNOWN
answer explainable (`check.py`): under negation-as-failure, the negative is justified by "I searched the
closure of P and found nothing." That searched structure — the SUBGOAL CHAIN — **is the negative's
provenance**, the mirror of a positive's `<j:>` proof tree. It is EXPLANATION, reasoned-over, so it must
stay a matchable graph node (the Axis A HARD CONSTRAINT: never lift explanation out of the graph). Lifting
it to a register was the exact mistake that doc warns against. So `<demand>` stays a graph node; the
register lift is reverted.

**What genuinely IS a register here** (and always was): the AGENDA / worklist / fired-set / fuel counter —
the "what to try next, in what order" — a Python-local set, mechanical stepping. That part is correct as-is.

This reversal is the probe's key finding: it separates the demand chain's TWO parts cleanly — mechanical
agenda (register) vs. subgoal chain / negative-provenance (graph).

## 4b. Probe 3 — `ITERATE`: control-flow with a register counter (`ugm/machine.py`)

The clean §8 exemplar the demand trace turned out NOT to be. `ITERATE(counter, count)` is a MATCHING
opcode that FORKS the state stream over `range(count)`, binding `counter` in `State.regs` — a LOOP whose
counter is a **register value**, never a MINT-ed `<iter>`/`<round>` graph node (a loop counter explains
nothing → register). It fits the machine's model exactly: the match phase is already a nondeterministic
fork (SEED forks over candidates), so a bounded loop is a fork over a range, and the effect phase runs the
body once per index. This is PARALLEL/MAP iteration (each index independent); a stateful ACCUMULATING loop
is the driver's fixpoint (`run_bank`/`run_to_fixpoint`), whose round counter is likewise a Python-local
register. `count` is a literal int OR — the **dynamic trip count** (built 2026-07-16) — a register NAME:
the bound is read from the state's own binding, so it can come from graph DATA matched earlier in the
program. Resolution lives inside the instruction (isa_value_operands §3): an int literal counts directly,
a node-pointer counts by its value-node's carried value (numeric strings — the CNL-authored shape —
included). Each incoming state resolves its OWN bound (a per-state trip count, the fork semantic
extended). A bound with no whole-number reading raises `ProgramError` — loud, never a silent empty loop,
and a fractional value is refused rather than truncated.

Tests (`tests/test_isa_iterate.py`): the fork binds a register counter and touches NO graph node; the body
runs once per index; an empty loop is a no-op; it composes after a prior fork; the dynamic bound reads an
int-literal register, a value-node pointer, resolves per-state, and is loud on non-numbers. Greenfield (no
existing iteration node to retire) — mode_calls.py §19 envisions it as the plan→act→check→replan loop
primitive.

---

## 5. The register/graph boundary under RECURSION (the arbitrary-depth question)

A live design question (raised 2026-07-14): *arbitrary-depth nested subgoals seem to need a pointer
materialized in the graph — unless we have infinite registers.*

Resolution, and the sharpened boundary:

1. **Registers are not finite hardware slots.** A slot holds an arbitrary heap object, so ONE slot holds a
   growable stack — the register is the stack *pointer*, the stack grows in machine memory (Python heap).
   No infinite registers; no graph nodes.
2. **Nesting already works with zero graph nodes.** `chain_sip` recurses (`_nac_blocks` →
   `chain_sip(_neg_stack=neg_stack | {neg_goal}, …)`, `chain.py`): each recursive call is a Python stack
   frame with its OWN local `agenda`; `_neg_stack` is a `frozenset` threaded down the recursion (the
   stratification stack). Both are heap/stack memory, invisible to rules, unbounded. The lifted `<demand>`
   nodes were only the top-level trace — never the recursion.
3. **What decides graph-materialization is the discriminator, not depth** — and the subgoal chain lands
   on the GRAPH side (this is the §4 finding, and it VINDICATES the original "pointer in the graph"
   intuition):
   - the pure *agenda* (order/counters) → register-referenced heap structure (unbounded is fine);
   - the subgoal CHAIN **is explanation** — "proving X *because* it is a subgoal of Y, which is *why* the
     answer is Z" — reasoned-over like provenance, so it → **graph nodes with inter-frame pointers** (same
     home as the proof tree). Arbitrary depth is a non-issue here: the graph is unbounded storage (nodes),
     the inter-frame links are edges. So the "pointer materialized in the graph" the depth question worried
     about is exactly right — not because of depth, but because the chain is explanation.
4. **Refinement owed — BUILT 2026-07-16 (the linked subgoal chain):** the flat `<demand>` magic set stays
   (rule-graph, top-level, unconditional — its consumers `bound_demands`/`render_demands`/the gather loop
   are untouched). Under `provenance=True` the chain STRUCTURE is additionally recorded: interned
   `<subgoal>` nodes **in the FACT graph** (explanation's home — the rule graph is discarded per
   `ask_goal` call) with provenance-inert parent -[`raised`]-> child edges, at EVERY negation depth
   (in-frame sub-demands link under the demand being served; a NAC child frame's goal rides the suspend
   request's new 4th element to link under the demand whose rule raised it). `subgoal_decomposition`
   walks one step; `surface.explain` renders an `assumed not:` line's decomposition as indented
   `looked for:` lines at DOMAIN GRAIN (fully-bound, non-`same_as` children — the coref congruence's
   probes stay matchable in the chain but narrate the machinery, so the renderer skips them; the same
   cut `on_subgoal`'s frame grain makes). A memoized NAC re-encounter adds no new link (no new search
   happened). Tests: `tests/test_subgoal_chain.py`.

   **Certain-NAF assumed-records (same day — the record half of the hard-vs-assumed capstone):** a CRISP
   surviving NAC now journals its leaned-on absence at Π = 0 (`_nac_blocks` appends in silent mode; the
   ink/pencil EMIT path attaches `_record_assumptions`), so a crisp `why` shows `assumed not: … (no
   evidence for it was found)` with the decomposition hanging off it — identical shape to the banded
   story. Verdicts untouched (provenance-only). The capstone's SURFACING half landed the same day:
   under the BANDED stance, `ask_goal`'s verdict wears its kind — ASSUMED_NO answers `no (assumed)`
   (bound goals and the banded ∃), ENTAILED_NEG stays a plain hard `no`; the crisp default keeps the
   yes/no/unknown collapse (deliberate — a crisp caller wanting the kind uses `check` directly).

So: the AGENDA is a register; the SUBGOAL CHAIN is graph (explanation). Depth never forces graph
materialization — being explanation does.

---

## 6. Acceptance

- Focus (Probe 1): 15/15 `test_isa_focus.py` green via the unchanged public API; no `<focus>`/`center`/
  `below` node is ever created (a `drop` mutates no graph node).
- Demand chain (Probe 2 reverted): `<demand>` subgoal nodes stay in the graph;
  `test_isa_chain.py`/`test_isa_trace.py` green (unchanged from before the probe).
- Substrate: `AttrGraph.registers` is invisible to matching/seeding/`derived_triples`, and `copy()`
  carries it — the mechanism stands on Probe 1 (focus) alone.
- Full suite: **350 passed**.

---

## 7. Out of scope / next

- ~~**Other `<…>` control state.**~~ AUDITED 2026-07-16 — see §8. Every remaining item is already on
  the right side of the register/graph line; nothing to lift.
- ~~**`ITERATE` over a loop register.**~~ BUILT (§4b), including the dynamic register-read trip count
  (2026-07-16).
- ~~**The linked subgoal chain** (§5.4)~~ BUILT 2026-07-16 — see §5.4.
- ~~**Retiring the `is_control` flag / `<…>` convention**~~ RESOLVED BY REVERSAL 2026-07-16 — see §8.5.

---

## 8. The closing discriminator audit (2026-07-16)

The arc's final pass: apply the §4 discriminator — *"does ANYTHING reason about it (incl.
reasoning-about-reasoning)? → graph; only 'how did the machine step?' → register"* — to every `<…>`
state the probes deferred. Verdicts, with the load-bearing reason each:

**8.1 `<call>` / dispatch (`dispatch.py`) — ALREADY SPLIT CORRECTLY.** The `<call>` record, its
argument slots, and tool results are GRAPH: rules *materialize* calls and *read* results — the
record is the reasoned-over coupling surface (the §8 hard rule: rules and tools couple only through
nodes). The servicing MECHANICS are already control-machine registers (`ctrl["call_id"]`,
`ctrl["tool"]`, `ctrl["req"]`, `ctrl["touched"]`, the `kind` scalar) since the §9.4 port
(`service_calls_cm`). Exactly the §6 sentence already in the module: "the `<call>` RECORD stays a
graph node; only the return/resume mechanics moved." Nothing to do.

**8.2 `<hypothesis>` / suppose scope (`suppose.py`) — GRAPH, deliberately.** Pencil rels are
matched in-scope (OVERLAY) — reasoned-over by construction. The scope NODE itself carries semantic
content: a possibilistic fork scope wears `LIKELINESS` (read by `_band_suffix`, `_env_ok` — the
band and world-exclusivity ARE reasoning inputs), so the scope node is a fact about the hypothesis,
not a stepping cursor. The ACTIVE-scope pointer is a threaded Python parameter (`scope=`) — per-query
and re-entrant (nested queries carry different scopes); the Python call frame IS its register file,
and a persistent `kb.registers` slot would *break* re-entrancy. The in-scope working set OVERLAY
reads is already a driver-parked register (`registers[live]`). Nothing to do.

**8.3 Recognition token-chain (`<sentence>`/`first`/`next`) — GRAPH.** The chain is DATA while the
forms run: `QUESTION_FORMS`/surface strata match it. Reasoned-over, ephemeral by lifecycle (throwaway
parse graphs), not by home. Nothing to do.

**8.4 `<head-index>` (`apply.build_head_index`) — GRAPH, considered and kept.** It is derived/
mechanical (an index), which *sounds* register-shaped — but it is derived data ABOUT RULES, queryable
through the substrate (`rules_producing`, "no Python dict" by explicit earlier decision), and "which
rules could produce X" is exactly what means-ends / program-as-data reasoning asks. The register home
is for stepping state, not for materialized views of graph data.

**8.5 `is_control` / the `<…>` convention — RETIREMENT RESOLVED BY REVERSAL.** The premise of the
retirement item was that once control STATE moved to registers, control-marked NODES would become
rare and the flag vestigial. The Probe 2 reversal (and everything it seeded: the subgoal chain,
assumed-records) established the opposite: explanation, pencil, pattern-space, and trace are
*permanent graph residents*, and the marker attribute is the visibility MECHANISM that keeps them
out of fact reads (firmware §3: marker attrs are the truth; the boolean field is already gone —
`is_control` reads `CONTROL_MARK in attrs`). The convention is load-bearing mechanism, not a
vestige. CLOSED, not deferred.

**Arc verdict:** the two homes hold — GRAPH: facts + everything reasoned-over (explanation,
provenance, subgoal chain, pencil, pattern, call records, rule wiring); REGISTERS: stepping
(agenda/fuel/loop counters/PC/control stack/focus working-set/dispatch mechanics). Every deferred
item audited; no further lifts owed. Axis B is COMPLETE.
