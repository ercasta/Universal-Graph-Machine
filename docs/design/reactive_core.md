# The reactive core (STEP B/C of the arc) — a design sketch grounded in `reconsider`

> Status: DESIGN SKETCH, 2026-07-23. STEP B (soundness firing gate) + STEP C (standing reactive loop) of
> `implementation_plan.md` ▶ CURRENT ARC — LOCALITY BOUNDARY → REACTIVE CORE. Memory:
> `reactive-core-north-star`. STEP A (the identity boundary, `derivation_frame.md`) is the prerequisite and
> is DONE.

## The finding — the reactive skeleton already exists, and it is `reconsider`

The north star is "materializing a fact TRIGGERS reactions; the DATA decides what runs; push and pull
unify." The plan framed the build as "lift the semi-naive work-list from per-`run_bank` to a standing,
cross-call loop." Investigating the engine's existing event-pockets shows the standing loop is **already
built, for one reaction kind** — `reconsider` (docs/design/reconsider_design.md):

| Reactive-core primitive | Already in `reconsider` |
|---|---|
| **Event queue** (cross-call) | `kb.registers[DIRTY_REG]` — an insertion-ordered dict of `(pred, obj)` grains, written by `mark_dirty` at intake/evidence-acquisition. Accumulates ACROSS calls. |
| **Trigger dispatch** (what reacts to a change) | `_affected(dirty, rules)` — a fixpoint closure over the DECLARED rules' body→head edges: a changed grain propagates to every rule whose BODY reads it. Data-driven, computed from the bank, not hand-wired. |
| **Demand-gated firing** (lazy, not eager) | `ask_goal(commit=True)` runs `reconsider` BEFORE answering, gated on a non-empty dirty set (zero-cost when empty). Reactions fire when the agent next ACTS, never eagerly — the [[agent-not-theorem-prover]] laziness. |
| **Soundness / no self-reinforcement** (STEP B's core fear) | Detach-the-dirty-set-before-the-sweep (regress guard); materialized facts are monotone real knowledge and do NOT re-dirty; NAC atoms excluded from `_affected` (new facts only REDUCE an absence's derivability, so they cannot break it wrongly). This IS the [[recall-explicit-not-autofire]] invariant, implemented. |
| **Bounded** | The grain universe is finite (`dirty` ∪ the bank's head atoms). |

So the recall-autofire scar — the reason a reactive core is dangerous — was already navigated once, soundly,
for the NAF-recheck case. STEP B is therefore **not "invent a soundness gate"; it is "GENERALIZE the gate
`reconsider` already embodies"** and make its invariant a re-breakable, reusable contract.

## What `reconsider` does NOT yet do (the generalization = STEP C)

`reconsider` is specialized to ONE reaction: RE-CHECK an assumed-`no` NAF conclusion and RETRACT it if the
absence it leaned on is now filled. The reactive core generalizes on two axes:

1. **The reaction is fixed (retract stale NAF).** The general form: a DECLARED trigger fires a DECLARED
   reaction. A reaction may be (a) re-derive/propagate (forward cascade for a *reactive* predicate), (b)
   retract (what `reconsider` does), or (c) a side-effect / `<call>` (act on the world). All three are
   VISION-TRUE only if the trigger→reaction map is DECLARED DATA (a bank), dispatched by the engine's match
   loop — never a Python callback subscribed to writes.
2. **Firing is retract-only + demand-gated.** For proactive DERIVATION the gate must add the reactive/lazy
   dial: a predicate is `demand` (pull, the default — most predicates) or `reactive` (a materialization of
   its trigger enqueues its reaction, still fired at the next committed act, still fuel-bounded). This is the
   `open_preds`-shaped opt-in the plan named; it keeps eager exhaustive completion OUT while letting a few
   declared predicates push.

## STEP B — BUILT + LANDED 2026-07-23 (shipped 978 green)

`ugm/reactive.py`: `react(kb, rules)` — the DERIVE half of the FiringGate, wired into `ask_goal`'s commit
gate BEFORE `reconsider` (reads the shared dirty set without detaching; reconsider detaches). For every
affected grain (`reconsider._affected`) whose predicate is DECLARED reactive (`declare_reactive` /
`reactive_preds`, a `kb.registers[REACTIVE_REG]` set), it materializes the grain demand-driven
(`chain_sip`, monotone). Zero-cost and INERT when nothing is reactive/dirty — shipped 973→978 green (the +5
are `tests/test_reactive.py`), gate on every committed ask but early-returns. `tests/test_reactive.py`:
reactive materializes proactively at the committed ask (no query), non-reactive stays lazy-but-derivable,
demand-gated (nothing before an act), idempotent after the dirty set is consumed, and a mutually-reactive
`p<->q` CYCLE DRAINS rather than loops (the recall-autofire re-break, cycle form).

**DECLARATION-AS-DATA landed too (the vision-true surface, shipped 979 green):** `reactive_preds` reads
`P is reactive` FACTS off the KB (`_facts_matching(COPULA, ?, "reactive")`) unioned with the programmatic
register — so a corpus declares its own reactivity in its own text, no loader, no Python. Cost-free by
default (no node named `reactive` ⇒ an empty `nodes_named` lookup). `test_reactivity_declared_as_data`.

## STEP C.1 — the two reaction kinds unified under ONE gate (BUILT 2026-07-23, shipped 979 green)

`reactive.fire(kb, rules)` is the unified FiringGate: it reads + detaches the ONE dirty set once, computes
`active_rules` + `_affected` ONCE, and dispatches BOTH reaction kinds off that single closure — DERIVE
(`_derive`, materialize declared-reactive consequences) then RETRACT (`reconsider.sweep`, the stale-NAF
withdrawal). It replaces the previous commit-gate pair (`react` then `reconsider`, each independently
re-reading the dirty set and recomputing `_affected`); `ask_goal`'s commit block now calls `fire` alone.
Derive precedes retract (derive-then-recheck). Detach-once is the whole regress guard — neither half
re-populates `DIRTY_REG` (only intake/evidence do), verified against `chain`/`retraction`, so the captured
snapshot is the entire event batch.

The two standalone reactions survive as thin wrappers over the shared halves: `reconsider(kb, rules)`
= read+detach → `_affected` → `sweep`; `react(kb, rules)` = read → `_affected` → `_derive`. Both keep their
signatures/returns and their re-break tests (`test_reconsider` calls `reconsider` directly, `test_reactive`
calls `react` directly) — the direct-path guards. `sweep` and `_derive` take a PRE-COMPUTED `active`/
`affected` so the gate shares them; the wrappers compute their own. Shipped 979 green; `test_reactive` (6)
+ `test_reconsider` green.

## STEP C.2 — the reactions fire into the STEP-A frame (VERIFIED by construction, 2026-07-23, shipped 982 green)

The requirement: a reaction must reason over the canonical + guarded fact-view STEP A gave `_facts_matching`
(union a bound endpoint over its `denotes`-class; exclude control/inert scaffolding), so it cannot fire on a
token or on scaffolding. **This holds by construction — no new code — because every belief-read the two
halves do already routes through that one fetch:**

- **DERIVE** materializes via `chain.chain_sip`, which reads facts only through `_facts_matching`.
- **RETRACT**'s `_positive_now` recheck ("is the assumed absence now derivable?") runs `chain_sip` +
  `_facts_matching`; `reactive_preds` reads the `P is reactive` declaration through `_facts_matching`.
- The grains (`DIRTY_REG`, `_affected`) and the assumption goals (`_assumption_goal`) are **name-keyed**, and
  a name endpoint already unions same-named nodes (`nodes_named`) — so a TOKEN-resident trigger is seen and
  the reaction fires under the shared name (the entity's identity), the `ById`-only asymmetry STEP A closed
  never arising on this path.
- The raw graph reads left in `reconsider.sweep` (justification enumeration, `proves`/`assumes` edges) are
  **provenance-mechanics**, not belief-reads — they navigate the derivation DAG to decide WHAT to withdraw,
  and are correctly outside the fact-view.

Locked by three re-break tests in `tests/test_reactive.py` over a real token/entity `denotes` split:
`test_derive_fires_on_a_token_resident_trigger` (derive on a token-resident trigger materializes on the
entity), `test_retract_sees_a_token_resident_breaker` (the recheck sees a token-resident breaker across the
split and withdraws the stale NAF), `test_no_reaction_fires_on_control_scaffolding` (the guard keeps a
control node carrying a content edge from being reacted upon). Probe: `bench/spike_reactive_frame.py`.

## STEP C.3 — push/pull unification (the arc payoff, BUILT 2026-07-23, shipped 990 green)

The claim: forward (PUSH — a reactive cascade materializing eagerly at `reactive.fire`, no query) and demand
(PULL — an ask) are two ENTRIES INTO THE ONE DISPATCH, so they cannot diverge. **The mechanism that makes it
true was already in place: the DERIVE reaction (`reactive._derive`) materializes a grain by calling
`chain.chain_sip` — the DEMAND solver.** So PUSH is *event-triggered PULL*: there is no second evaluator on
the reactive path, both read the same canonical + guarded `_facts_matching` view (STEP A / §C.2), and the
forward/demand guard-divergence class ([[nac-grouping-engine-parity]], [[stratification-both-engines]])
cannot recur on it.

The non-trivial thing this had to survive: PUSH writes derived facts INTO the graph eagerly, and in the
stratification-sensitive shapes (`negation_over_derived`, feedback #18) a downstream NAC reads one — the exact
configuration where a NAIVE push (firing reactions in dirty order rather than stratified) would manufacture a
mis-stratified world. It holds because each reactive grain's `chain_sip` is a full stratified demand
derivation, so cross-grain firing order in `_derive` cannot mis-stratify: `chain_sip(ok)` pulls `reachable`
itself, regardless of whether `reachable`'s own reactive fire has run yet.

Demonstrated over the guard-divergence battery three-way — `PUSH(fire) == PULL(ask) == FORWARD(run_bank)` —
across every subset of a 7-fact pool × 6 shapes (768 worlds, all six discriminating). Probe:
`bench/spike_push_pull_unification.py` (GO, 768/768). Standing gate: `tests/test_push_pull_unification.py`
(6 parametrized shapes + `test_the_push_sweep_is_not_vacuous` + `test_the_push_column_rides_the_demand_engine`
— the last re-breaks feedback #16's NAC grouping and requires PUSH to then diverge from FORWARD, proving the
push column genuinely runs `chain_sip` rather than agreeing by sharing nothing).

**What this does and does not claim.** It does NOT merge `run_bank` and `chain_sip` into one engine (they stay
two, deliberately, guarded by `test_forward_demand_parity.py`). It claims that the REACTIVE path — the north
star's standing, cross-call, event-driven loop — has ONE evaluator (demand, reading the STEP-A view) entered
at two times: a materialization ENQUEUES (`mark_dirty`), an act DRAINS (`fire` → `chain_sip`). Push and pull
are that one dispatch seen from the write side and the read side. The forward engine `run_bank` remains the
legacy batch push; the reactive core supersedes it with event-triggered demand, and the three-way sweep shows
the supersession introduces no divergence.

## Robustness audit (2026-07-23, shipped 996 green)

Before moving to surface, the reactive core's *by-construction* soundness/termination claims were stress-
tested adversarially rather than left argued. **Finding: the reactive push (`fire`) inherits the demand
engine's guarantees because `_derive` delegates wholly to `chain_sip`, and C.1's unified gate preserves the
derive-then-recheck ordering.** Six adversarial banks pushed through `fire` all compute the world a demand
pull would (`bench/spike_reactive_robustness.py`, 6/6; locked as re-break tests in `tests/test_reactive.py`):

1. **Skolem-minting reactive head** — eager push mints ONE witness per binding (structural re-find
   convergence, [[skolem-minting-lhs-keyed]]), not a fuel-capped flood.
2. **Deep cascade** (a→b→c→d→e, all reactive) — one `fire` drains the whole chain (the `_affected` closure
   reaches every hop).
3. **Reactive rule WITH a NAC** — eager push respects the block exactly as demand (stratification per rule,
   because each grain's `chain_sip` is a full stratified derivation).
4. **Banded policy** — the possibilistic fold flows through the derive half (materializes as a banded fact).
5. **Derive-then-retract in one `fire`** — a reactive derive produces the breaker; the SAME gate materializes
   it and withdraws the stale NAF conclusion (the C.1 ordering, end-to-end).
6. **`focus_scope`** — a reactive derive fires into the scoped frame (materializes in-scope, bounded out).

**Termination.** The gate terminates: `_affected` draws from a finite grain universe (dirty ∪ the bank's head
atoms), and each grain's `chain_sip` is fuel-bounded (`max_rounds`, default 1000). A monotone reactive cycle
drains (§B); a skolem bank converges (check 1).

**~~Known soft spot~~ CLOSED 2026-07-23 by the HELP-FLARE (`ugm/flare.py`, shipped 1003 green).** Fuel
exhaustion no longer truncates silently: a demand closure that hits `max_rounds` on either committed-act path
raises a FLARE — a normal reactable fact `<goal-node> unresolved yes` (the reified goal carries
`f_pred`/`f_subj`/`f_obj`). Hooked at (1) the reactive DERIVE gate (`reactive._derive` threads `_Exhaustion`;
`fire`/`react` now thread `max_rounds` so the reactive derive honors the ask's budget) and (2) the ASK path
(`check` takes a caller-owned `fuel` flag; `ask_goal` raises a flare on an exhausted committed ask — the
durable trace the transient UNKNOWN lacked). SOUND: presence-triggered (fires on the exhaustion EVENT, never a
miss → no recall-autofire channel), deduped per goal (idempotent), inert/opt-in (no reaction unless a
predicate is declared reactive). `tests/test_flare.py` (7): both paths, idempotence, no-false-flare,
wildcard round-trip, and the reactive core reacting to its OWN flare. Probes: `bench/spike_help_flare.py`,
`bench/spike_governor.py`.

## The composability principle (the load-bearing constraint on everything above)

**These mechanisms cannot exist in isolation; they must combine in ARBITRARY ways — which is the whole reason
for a common substrate, and why hardcoding any of them in Python fails** (user, 2026-07-23). A Python function
that decides "this flare means abandon" is an island: a *rule* about authority, or reconsider, or another
policy can never reach into it. So the irreducible-Python line is drawn tightly:

- **Engine mechanism (Python, unavoidable):** detecting exhaustion (`_Exhaustion`), the reactive dispatch
  (`fire`), register storage. And the BRIDGES that turn an engine-internal event into a substrate fact —
  `flare.raise_flare` (exhaustion → `unresolved` fact) and `provenance.record_assumptions` (a NAF leap →
  `<assumed>` fact) are the same category: they MINT data, then step out of the way.
- **Everything downstream is DATA + RULES on the one graph, so it composes:** a flare is a fact a rule reads;
  an accumulator is substrate data a rule counts; a threshold is a declared fact; a recovery is a reactive
  rule; an authority order is a comparative fact. Because they are all in the same language, "goal G flared N
  times" and "Jack outranks John" can be combined in a SINGLE rule — e.g. the recovery STRATEGY is itself
  chosen by authority. That arbitrary cross-combination is impossible if any layer is a Python special case.

**Consequence for the governor (accumulator + threshold + recovery):** it is NOT built as a Python `govern()`
(the `bench/spike_governor.py` Python orchestration only VALIDATED the mechanism). It is authored as data +
rules. The build task is to expose the two substrate hooks a rule needs — an accumulator readable/writable by
the engine as data, and the flare fact (done) — then the threshold check and every recovery are ordinary
(reactive) rules. Heuristic termination (we do not decide halting — [[agent-not-theorem-prover]]) then falls
out of a declared threshold rule turning a repeatedly-flaring goal into a bounded, honest give-up.

## The reflexive governor (accumulator + threshold + recovery) — BUILT 2026-07-23 (shipped 1010 green)

Heuristic termination for a repeatedly-failing goal, as **100% data + rules** — no Python `govern()`, no
arithmetic tool (the composability principle enforced by `tests/test_substrate_purity.py`). The only Python is
the flare BRIDGE (`ugm/flare.py`), which now mints a DISTINCT `<event> flared <goal>` fact per exhaustion (the
ACCUMULATOR — a monotone set of event facts, never deduped) alongside the deduped `unresolved` signal.

Everything else is `corpus/governor.cnl`:
- **Count without arithmetic** — "reached level-k" = k DISTINCT failures = a k-fold SELF-JOIN with `!=` (the
  one native comparison). The severity LADDER (`mild`/`moderate`/`severe`) is one self-join per level.
- **Threshold as swappable DATA** — `?g abandoned yes when ?g reached ?level and ?c abandon_at ?level`; the
  `abandon_at ?level` FACT selects the active rung. Proven: same failures, `severe`→keep-going,
  `moderate`→abandon, by data alone (`test_the_threshold_moves_by_data_alone`).
- **Reactive** — `reached`/`abandoned` declared reactive (as data), so the gate escalates the ladder and
  materializes the verdict at each committed act with NO query: the system governs ITSELF.
- **Terminates** — the verdict is monotone; further failures neither un-abandon nor storm it.
- **Composes** — the recovery is ordinary rules, so authoritativeness can choose the recovery or the
  `abandon_at` level; reconsider can revise it; etc. No island.

`tests/test_governor.py` (3) drives the loop through `fire`. Ruled out: a GRADED-degree threshold — the
possibilistic combination is max-of-min (idempotent), so degrees can't accumulate/count
(`bench/spike_threshold_no_tool.py`). Trade-off: each level's join is structural, so the ladder is a bounded
declared set of ordinal levels (what governance wants); only an arbitrary unbounded-N threshold would need a
tool.

**Composition demonstrated in production (the thesis, end-to-end).** `corpus/recovery.cnl` selects the
recovery for an abandoned goal BY AUTHORITY (reified advice + a `more_important_than` fact + a NAF override).
Loaded ALONGSIDE `governor.cnl` in one KB, the two banks combine with nothing but shared facts: the governor
abandons a goal, and the most-authoritative advisor's recovery is applied. `test_governor.py`'s composition
tests prove it — `ops > policy` → `escalate`; reverse the ONE authority fact → `giveup`. Two independently-
authored mechanisms, steered by a single datum, no glue code — the composability principle at system scale.

**Silent-failure bug fixed en route:** the CNL corpus rule route (`cnl/authoring.load_rules` → `expand_rules`)
did NOT lift a `?a != ?b` body clause into a distinctness condition the way the machine surface
(`machine_rules._lift_distinct`) does — so a corpus rule with `!=` LOADED but never fired (it matched a
nonexistent `!=` fact). `load_rules` now runs `_lift_distinct`, so `!=` works in `.cnl` corpora.

## Side-effect reactions — the world-action boundary (the §C fork, BUILT 2026-07-23, shipped 1019 green)

The third reaction kind, and the LIVE-AGENT LOOP: a chosen recovery no longer sits as an inert fact — it
ACTS. Everything below the reactive core had been proven with hand-driven `fire()`; this is the stack meeting
a REAL `converse` session with a REAL `<call>`/`ask_user` boundary.

**Probe-first, and it paid.** `bench/spike_live_agent_loop.py` drove the whole reflexive stack (flare →
governor → authoritativeness → recovery) through the REAL committed-ask gate — repeated fuel exhaustion on a
never-settling question. Two findings a hand-driven test could not surface:
1. **The stack lights up through the real ask path** — the flare raised by `query.ask_goal` (not a probe's
   `raise_flare`) accumulates across turns, the governor escalates + abandons, and recovery is chosen by
   authority. Live-valid, not just unit-valid.
2. **A live-only pathology — governance can flare on ITSELF.** The reactive DERIVE threads the ask's
   `max_rounds`, so if the OBJECT goal's budget is so tight the GOVERNANCE derivation (the recovery/override
   ladder, a few hops) can't finish, it exhausts and raises flares the governor then counts — a reflexive
   feedback loop, and recovery never materializes. At an adequate governance budget it is clean (measured: a
   20-hop cascade starved at budget 2 self-flares; at 6+ it derives `recovery escalate` cleanly, 1 flare/turn,
   no self-flare). A robustness note, not a blocker (governance is a bounded ordinal ladder). The natural
   in-language fix is itself a recovery action: `raise_budget` (think harder), which the same mechanism below
   can now fire.

**The build (all data + rules + the tool boundary; no new graph-writing Python, guardrail unchanged):**
- **`recovery is actionable`** — a DATA declaration, sibling of `P is reactive` (`reactive.actionable_preds`
  reads `P is actionable` facts ∪ a programmatic register). A materialized fact of an actionable predicate is
  a chosen WORLD ACTION: its object names the tool, its subject the goal.
- **`reactive.emit_action_calls` — the fact→call BRIDGE.** A materialized `?g P ?a` (P actionable) becomes a
  `<call>` to tool `?a` with `arg=?g` (via `dispatch.emit_call` — the write stays in sanctioned `dispatch.py`,
  so `reactive.py` is not a substrate writer and the purity manifest is untouched). GENERIC — WHICH action
  was chosen is decided upstream by the recovery bank (by authority); the bridge only turns the chosen
  action-FACT into the `<call>` the tool boundary already understands, exactly as `flare.raise_flare` turns an
  exhaustion EVENT into a fact. Deduped against a pending call for the same (tool, arg).
- **`_derive` flags a fresh action.** When an actionable+reactive predicate NEWLY materializes at the gate,
  `_derive` sets `reactive.SIDE_EFFECT_REG` (a register — stepping state, not graph). Fresh-only, so the
  action fires on the turn the recovery first concludes and is monotone thereafter (no re-fire storm).
- **`intake._drain_side_effects` — the driver services it.** After a committed question, if the flag is set,
  the generator emits the action `<call>`s and services them via `dispatch.service_calls_cm`; an ASYNC tool
  SUSPENDs, yielded up as an `Event("call")` whose `.send()` is the world's response — the SAME suspend/resume
  a `goal` turn uses. Demand-gated: an ordinary question pays one register read. So a QUESTION whose failure
  the governor governed can escalate/give-up/raise-budget without the caller orchestrating it — the
  utterance's own reasoning drove the world action (the seamlessness goal).

**Demonstrated live (composability, end-to-end):** the never-settling question escalates FOR REAL — the
`escalate` `<call>` suspends to the host and is folded — and flipping the ONE `more_important_than` authority
fact makes `giveup` act instead, with no code change. Locked by `tests/test_side_effect_reaction.py` (7): the
action fires through a real `<call>`, authority chooses which action, it fires ONCE not per-turn (dedup), an
answerable question never acts (opt-in/zero-cost), a reactive-but-not-actionable pred never acts (the boundary
is a separate opt-in), the bridge dedups against a pending call, and the declaration reads as data.

## Arc status: STEP C COMPLETE

STEP A (identity frame) + B (reactive DERIVE gate + declaration-as-data) + C.1 (two reaction kinds unified
under `fire`) + C.2 (reactions fire into the STEP-A frame) + C.3 (push/pull unification) are all built and
shipped-green (990). The reactive core is a standing, cross-call, demand-gated, sound, event-driven loop with
one evaluator over one canonical fact-view. Deferred / future: side-effect (`<call>`) reactions (the
world-action boundary, §C fork), a CNL surface for the `reactive` declaration beyond the marker fact, and the
open question of whether `run_bank` is eventually retired in favour of the reactive push.

## STEP B — the firing gate, as a reusable contract (small, mostly formalization) [DESIGN, realized above]

- Lift `reconsider`'s safety properties into a named `FiringGate` contract: (i) reactions fire demand-gated
  (at a committed act), never eagerly; (ii) the event set is detached before firing (regress guard); (iii) a
  reaction that MATERIALIZES cannot re-enqueue its own trigger (no self-reinforcement — the monotone
  argument, generalized past NAF to any reaction); (iv) fuel-bounded (a reaction that never settles
  terminates honestly → the existing `max_rounds` budget).
- The re-breakable guard: a test that a reactive rule whose head fills its own trigger's absence does NOT
  loop (the recall-autofire scenario), reusing `reconsider`'s NAC-exclusion argument.

## STEP C — generalize triggers/reactions (the standing loop)

- A `<reactive>` declaration (a bank-level fact, like `R is a relation` / a schema trigger) marks a
  predicate/rule reactive. `mark_dirty` already records the event; `_affected` already computes the reach;
  the new work is dispatching the DECLARED reaction kind (derive / retract / call) through the gate, into a
  STEP-A bounded frame (a reaction reasons over the canonical, guarded fact-view `_facts_matching` now
  provides, so it cannot fire on tokens/scaffolding).
- Push/pull unify here: forward (a reactive cascade) and demand (a pull) become two entries into the SAME
  dispatch — a materialization enqueues, an ask drains; neither is a separate engine, so the forward/demand
  guard-divergence class cannot recur.

## Forks to settle (in the probe)

| Fork | Options / lean |
|---|---|
| Reactive opt-in granularity | per-PREDICATE (`open_preds`-shaped) vs per-RULE. Lean per-predicate (matches `_affected`'s grain, matches `open_preds`). |
| Reaction kinds in v1 | retract (have it) + derive (new). DEFER side-effect/`<call>` reactions to a later slice (they add the world-action boundary). |
| Where the reaction runs | into a STEP-A frame (canonical + guarded `_facts_matching`) — reuse, don't rebuild. |
| Trigger declaration surface | a `<reactive>` marker fact vs a new CNL form. Lean marker fact first (like `disjoint_from`), CNL surface later. |

## The minimal probe (proposed — NOT yet built)

Generalize `reconsider` to fire ONE declared DERIVE reaction, demand-gated, and show:
1. A predicate declared `reactive`: materializing its trigger fact makes its consequence available at the
   next committed ask WITHOUT an explicit query for the consequence (the data drove it) — while a
   NON-reactive predicate stays pull-only (unchanged laziness).
2. The recall-autofire re-break: a reactive rule whose head fills its own trigger's NAF absence does NOT
   self-reinforce (the gate holds).
3. Zero shipped regression (the generalization is additive; `reconsider`'s existing behavior is one
   configured instance of the general gate).

If it holds, STEP C is "wire the declared reaction kinds through the generalized gate"; if the
derive-reaction re-break fails, we learn the monotone argument does not extend past NAF and the gate needs
more than `reconsider` provides.

## Probe RESULT — GO (`bench/spike_reactive_derive.py`, 2026-07-23)

Generalized `reconsider`'s front half (`DIRTY_REG` → detach → `_affected`) with a DERIVE reaction
(`chain_sip` to materialize a reactive grain), orchestrating the existing primitives exactly as the build
would wire them. Confirmed: (1) a `reactive` predicate's consequence is MATERIALIZED at the next committed
act with NO query for it, while a non-reactive predicate stays not-materialized-but-demand-derivable
(laziness preserved); (2) firing is idempotent/terminating (first fire 1 grain, second 0 — the detach guard).

**A SHARPER SAFETY FINDING the probe made concrete: the reactive DERIVE gate avoids recall-autofire BY
CONSTRUCTION.** The recall-autofire scar was a MISS-triggered mechanism (auto-recall on a demand-MISS →
manufactures the very fact whose absence triggered it → self-reinforcing). The reactive gate is
PRESENCE-triggered (a POSITIVE materialization enqueues a reaction), so the trigger is never an absence the
reaction can fill — the self-reinforcement channel does not exist. Idempotence then follows from
monotonicity: a re-materialized fact is a no-op that enqueues no new grain, so a reactive CYCLE (`P⇒Q`,
`Q⇒P`, both reactive) drains rather than loops. (Left for the BUILD's re-break: the explicit P⇄Q cycle test,
and a NAF reaction under the gate — both expected to terminate by the same monotone argument.)

So STEP B's contract is even smaller than feared: presence-triggering + detach-before-fire + monotone
materialization already give soundness; the gate mostly FORMALIZES what the probe ran.
