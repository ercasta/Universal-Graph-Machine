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

## STEP B — the firing gate, as a reusable contract (small, mostly formalization)

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
