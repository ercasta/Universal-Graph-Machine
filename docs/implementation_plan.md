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

## ▶ CURRENT ARC (RE-POINTED 2026-07-23) — LOCALITY BOUNDARY → REACTIVE CORE

> **This re-orientation supersedes the flip-default grind as the top goal** (that grind is now a
> DOWNSTREAM BENEFICIARY + a measurement, not the driver). It came out of a design conversation
> (2026-07-23); the dated handoff blocks below remain valid context/history. Standing rules unchanged
> (no assistant commits; domain logic ONLY in banks; strategies are DECLARED data; correctness before
> perf). Memory: [[derivation-frame-consolidation]], [[reactive-core-north-star]].

### ═══ FRESH-SESSION START HERE (2026-07-23 end — suite 1022 green, flip 32/1022) ═══

**⭐⭐ `X prep Y` GRAMMAR SURFACE — BOTH HALVES LANDED 2026-07-23 (shipped 1022 green; flip 43→32).** Two
predicating-preposition surfaces added to `corpus/loudon_grammar.cnl`, each reusing an existing fold, each
locked in `test_grammar_shipped_agreement.py`:
1. **DECLARATIVE (the metric mover, flip 43→32, −11).** `clause expands to np plus pp` + 3 subj/prep/pobj slot
   lines → a bare `bo in library` (no verb — English drops the copula in a locative) parses as a CLAUSE and
   asserts `(bo, in, library)`, so `?x is innocent when ?x in library` fires. Before, it covered the whole
   utterance only as a NOUN PHRASE (`np plus pp`), never a `clause` root (`grammar.ROOT="clause"`), committing
   NO fact ⇒ bo an unclered crisp thief, polluting who/∃/why. No ambiguity (an np full-span is not a clause
   root). Gate: `…[predicating-x-prep-y]`.
2. **INTERROGATIVE (a habitability bug fix, +0 flip — no flip test asks it).** `qclause asks subj prep pobj
   when pobj` + copula-plus-np subj/prep/pobj slots → `is bo in library` now ASKS `(bo, in, library)` (→ yes).
   Before, the copula-plus-np qclause carried no subj/prep slot, so no `asks` fold fired and the question was
   silently DROPPED (routed as a fact that committed nothing, answer None) — the "question silently mis-routes"
   habitability failure. Gate: `…[interrogative-x-prep-y]` + its negative control.

ZERO shipped regression across both (1022 green). Remaining 32 flip failures are OTHER clusters, NOT clean
grammar-coverage: deferred-handler duality (causal_propagation 4, counterfactual 2, prop-cause 1 — the
intern_denoted family, superseded-in-principle by the STEP-A read boundary but still failing under flip),
integration (intake_forms 5, intake_act 3, intake_surface_facts 3, isa_* singles), the existential/relation
semantics (`is anyone happy` — `happy` declared a RELATION vs used as a copula property, entangled, NOT a
surface gap), and banded why-rendering (test_world 1: a fork premise renders "standing on the unlikely world
where…" not "cy is alibied (unlikely) (given)"). Memory: [[flip-default-blocked-by-greedy-grammar]].

**ONE-LINE STATE.** The arc (LOCALITY BOUNDARY → REACTIVE CORE) is **COMPLETE + a GOVERNANCE layer + the
LIVE-AGENT LOOP (side-effect reactions), shipped-green (1019)**. Reactive core: STEP A (identity boundary) + B
(reactive DERIVE gate) + C.1 (two reaction kinds unified under one `fire` gate) + C.2 (reactions fire into the
STEP-A frame) + C.3 (push/pull unification — PUSH is event-triggered PULL; `PUSH==PULL==FORWARD`). Then
robustness audit + a REFLEXIVE GOVERNANCE layer: HELP-FLARE (`ugm/flare.py`), the GOVERNOR
(`corpus/governor.cnl` — self-join `!=` severity ladder + swappable `abandon_at` threshold), AUTHORITY-chosen
RECOVERY (`corpus/recovery.cnl`) COMPOSING with the governor, all guarded by the COMPOSABILITY-PRINCIPLE
fitness function (`tests/test_substrate_purity.py`). **Then (2026-07-23 end) the LIVE-AGENT LOOP: the chosen
recovery now ACTS** — `recovery is actionable` (data) → the fact→call bridge (`reactive.emit_action_calls`) →
the driver services it as an `Event("call")` suspension, all through the REAL `converse` session. See
`docs/design/reactive_core.md` (§Robustness, §reflexive governor, §Side-effect reactions) + memory
`composability-principle`, `reactive-core-north-star`.

**⭐⭐ LIVE-AGENT LOOP BUILT 2026-07-23 (shipped 1019 green) — side-effect reactions, the §C fork.** The whole
reflexive stack met a REAL `converse` session with a REAL `<call>`/`ask_user` boundary for the first time
(`bench/spike_live_agent_loop.py`). PROBE-FIRST paid: it surfaced (1) the stack lights up through the real
committed-ask gate — the flare raised by `query.ask_goal` accumulates across turns, governor abandons,
recovery chosen by authority; and (2) a LIVE-ONLY pathology — because the reactive DERIVE threads the ask's
`max_rounds`, an object goal with a too-tight budget starves the GOVERNANCE derivation, which then flares on
ITSELF (clean at budget ≥ ~6; self-flares at 2 — a robustness note, natural fix = a `raise_budget` recovery
action). THE BUILD (all data+rules+tool boundary, no new graph-writing Python, purity manifest untouched):
`recovery is actionable` (declaration-as-data, sibling of `P is reactive`) → `reactive.emit_action_calls`
(fact→call BRIDGE via `dispatch.emit_call`, deduped) → `_derive` flags a FRESH actionable materialization
(`SIDE_EFFECT_REG`, fire-once) → `intake._drain_side_effects` services the `<call>` after a committed question
(async suspends as `Event("call")`, the SAME boundary a `goal` turn uses). Demonstrated: the never-settling
question ESCALATES for real, and flipping the ONE authority fact makes `giveup` act instead — composability,
live. `tests/test_side_effect_reaction.py` (7). Design: reactive_core.md §Side-effect reactions.

**NEXT = STEER again (the live loop closed; core well-hardened + reflexive + now ACTING).** Candidate moves,
none forced — my recommendation is the SURFACE `X prep Y` flip lever (the biggest measurable correctness lever
now that the core arc is done), or a `raise_budget` recovery action (the in-language fix for the self-flare
pathology, a small satisfying capstone of the live loop). Full candidate list below (unchanged).

**~~my recommendation: the LIVE-AGENT LOOP~~ DONE (see above).** The whole
reflexive stack (flare → governor → authoritativeness → recovery) had been proven in TESTS but never met a
real reasoning session with a real `<call>`/`ask_user` boundary — that is where the genuine unknowns were
(timing, cross-turn escalation, whether the chosen recovery actually ACTS). All three unknowns resolved:
cross-turn escalation works, timing is at the committed-ask gate, and the chosen recovery ACTS. The SURFACE
`X prep Y` flip lever (below) is higher METRIC movement (flip 43→lower) but a known grammar grind — lower
architectural information; keep it as the parallel product track.

**WHAT'S DONE (read the dated ⭐ blocks below + the two design docs for detail):**
- **STEP A — identity boundary. BUILT + COMMITTED (user).** `chain._canon_class` reads a bound endpoint as
  its `denotes`-class (both directions, nameless structure) in `_facts_matching` (`_candidate_nodes` +
  `_bound_class_pins`); the token/entity dual-store dissolves as a read-time VIRTUAL union (no copy, no
  merge-back). `intern_denoted` DELETED. Shipped green; flip 43 unchanged (a consolidation, not a
  flip-mover). Design: `docs/design/derivation_frame.md`. Probe: `bench/spike_derivation_frame_vision.py`.
- **STEP B — reactive DERIVE gate. BUILT (shipped 979 green).** `ugm/reactive.py::react(kb,rules)` wired
  into `ask_goal`'s commit gate BEFORE `reconsider` (shares the ONE dirty set; reconsider detaches). A
  predicate declared reactive has its consequence MATERIALIZED demand-driven at the next committed act when
  its trigger landed — data-driven, demand-gated, INERT by default. SOUND BY CONSTRUCTION (presence-
  triggered, not miss-triggered → no recall-autofire channel; monotone → cycles drain). The reactive
  skeleton IS `reconsider` generalized (DIRTY_REG queue + `_affected` dispatch + demand-gated firing +
  regress guard, all pre-existing). Design: `docs/design/reactive_core.md`. Probe:
  `bench/spike_reactive_derive.py`.
- **STEP C surface — declaration-as-DATA. BUILT.** `reactive_preds` reads `P is reactive` FACTS off the KB
  (unioned with the programmatic register), cost-free by default. `tests/test_reactive.py` (6).

**NEXT (the rest of STEP C, in order):**
1. **~~Unify retract + derive under ONE gate.~~ ⭐ DONE 2026-07-23 (shipped 979 green).** `reactive.fire(kb,
   rules)` reads + detaches the ONE dirty set once, computes `active_rules` + `_affected` ONCE, and dispatches
   BOTH reaction kinds off that single closure — DERIVE (`reactive._derive`) then RETRACT
   (`reconsider.sweep`). `ask_goal`'s commit block calls `fire` alone (was `react` then `reconsider`, each
   re-reading the dirty set + recomputing `_affected`). The two standalone reactions survive as thin wrappers
   over the shared halves (`sweep`/`_derive` take pre-computed `active`/`affected`), keeping their direct-path
   re-break tests (`test_reconsider` calls `reconsider`, `test_reactive` calls `react`). Detach-once is the
   whole regress guard — verified neither half re-populates `DIRTY_REG` (only intake/evidence do). Design:
   `docs/design/reactive_core.md` §C.1.
2. **~~Fire reactions into a STEP-A frame.~~ ⭐ DONE 2026-07-23 (shipped 982 green) — HOLDS BY CONSTRUCTION,
   no new code.** Both halves' belief-reads route through the canonical + guarded `_facts_matching`/`chain_sip`
   (derive via `chain_sip`; retract's `_positive_now` recheck + `reactive_preds` via `_facts_matching`), and
   grains/assumption-goals are NAME-keyed → name-union sees a token-resident trigger and fires under the
   entity's identity (the `ById`-only asymmetry STEP A closed never arises here). The raw reads left in
   `sweep` (justification/`proves`/`assumes` enumeration) are provenance-MECHANICS, correctly outside the
   fact-view. Locked by 3 re-break tests over a real token/entity `denotes` split
   (`tests/test_reactive.py::test_{derive_fires_on_a_token_resident_trigger,retract_sees_a_token_resident_
   breaker,no_reaction_fires_on_control_scaffolding}`). Probe: `bench/spike_reactive_frame.py`. Design:
   `docs/design/reactive_core.md` §C.2.
3. **~~The push/pull-unification claim.~~ ⭐⭐ DONE 2026-07-23 (shipped 990 green) — THE ARC PAYOFF.** PUSH
   (reactive cascade materializing eagerly at `fire`) and PULL (demand ask) are two entries into the ONE
   dispatch, non-divergent BY CONSTRUCTION: the DERIVE reaction (`reactive._derive`) materializes via
   `chain_sip`, so PUSH is *event-triggered PULL* — one evaluator, one STEP-A fact-view, no second engine on
   the reactive path. Survives the load-bearing eager-materialization case (`negation_over_derived`, #18)
   because each grain's `chain_sip` is a full stratified demand derivation, so cross-grain firing order cannot
   mis-stratify. Demonstrated `PUSH==PULL==FORWARD` three-way over the guard-divergence battery (768 worlds ×
   6 shapes, all discriminating). Probe: `bench/spike_push_pull_unification.py`. Standing gate:
   `tests/test_push_pull_unification.py` (6 shapes + not-vacuous + a re-break proving the push column rides
   `chain_sip`). Does NOT merge `run_bank`/`chain_sip` (they stay two, guarded by `test_forward_demand_
   parity.py`); it supersedes the forward batch-push with event-triggered demand at zero divergence cost.
   Design: `docs/design/reactive_core.md` §C.3. **STEP C — and the whole re-pointed arc's build — COMPLETE.**

**⭐ ROBUSTNESS AUDIT DONE 2026-07-23 (shipped 996 green) — user steer: harden the CORE before surface.** The
by-construction soundness/termination claims were stress-tested adversarially, not left argued. Finding: the
reactive push (`fire`) inherits the demand engine's guarantees (`_derive` delegates wholly to `chain_sip`) and
C.1's gate preserves derive-then-recheck — 6/6 adversarial banks compute the world a demand pull would
(skolem-minting convergence, deep cascade drain, NAC-under-eager-push, banded policy, derive-then-retract in
one `fire`, focus_scope bounding). Locked as re-break tests (`tests/test_reactive.py` robustness cluster) +
`bench/spike_reactive_robustness.py`. Termination holds (finite `_affected` grain universe + fuel-bounded
`chain_sip`). **ONE documented soft spot, not yet hardened:** fuel exhaustion is SILENT (a `chain_sip` hitting
`max_rounds` truncates with no signal) — latent for well-formed banks (monotone finite closure keeps the
reactive path under the cap), a deliberate future item since surfacing it touches `chain_sip` broadly. Design:
`docs/design/reactive_core.md` §Robustness audit.

**⭐ HELP-FLARE (governor Slice 1) BUILT 2026-07-23 (shipped 1003 green) — the audit soft spot CLOSED.**
Fuel exhaustion is no longer silent: a demand closure that hits `max_rounds` on either committed-act path
raises a FLARE — a durable, reactable fact `<goal-node> unresolved yes` (`ugm/flare.py`). Hooked at the
reactive DERIVE gate (`_derive` threads `_Exhaustion`; `fire`/`react` now thread `max_rounds` so the reactive
derive honors the ask's budget) and the ASK path (`check` takes a caller-owned `fuel`; `ask_goal` flares on an
exhausted committed ask). Sound: presence-triggered, deduped, inert/opt-in. `tests/test_flare.py` (7) incl.
the reactive core reacting to its OWN flare. Exported (`ugm.raise_flare`/`flares`). Design:
`docs/design/reactive_core.md` §Robustness (soft spot now CLOSED).

**⭐⭐ THE COMPOSABILITY PRINCIPLE (user, 2026-07-23) — the load-bearing constraint.** These mechanisms
(flare / accumulator / threshold / recovery / authoritativeness / reconsider / reactivity) CANNOT exist in
isolation; they must combine in ARBITRARY ways — the whole reason for a common substrate, and why hardcoding
any of them in Python fails (it makes an island no rule can reach). Irreducible Python = engine mechanism +
the BRIDGES that mint an engine-event into a fact (`flare.raise_flare`, `provenance.record_assumptions`).
EVERYTHING downstream is DATA + RULES so it composes. **Consequence: the governor is NOT a Python `govern()`**
— accumulators are substrate data, thresholds are declared facts, recovery + threshold-checks are (reactive)
rules. See `docs/design/reactive_core.md` §Composability principle.

**⭐ AUTHORITATIVENESS PROBE GO 2026-07-23 (`bench/spike_authoritativeness.py`) — native, and it composes.**
Reified attributed advice ("John says when alarm do evacuate") + a `more_important_than` comparative fact +
a NAF override rule ("chosen unless a more-important applicable advice beats it") resolve to the
higher-authority action (shelter, not evacuate) — ALL data+rules, no Python policy. Flipping the authority
FACT flips the outcome with zero code change. And the SAME mechanism composes with the flare (authority
chooses a RECOVERY: Jack says abandon → the recovery is abandon), proving two mechanisms combine on the shared
substrate with no new machinery — the composability principle demonstrated.

**⭐ SUBSTRATE-PURITY GUARDRAIL BUILT 2026-07-23 (shipped 1007 green) — the composability principle ENFORCED.**
`tests/test_substrate_purity.py`: an AST fitness function (user: "can we TECHNICALLY prevent" the Python
drift). Scans `ugm/` for the domain-content mutators (`add_relation`/`set_attr`); every writer must be a
CATEGORIZED MANIFEST entry (substrate/engine/surface/bridge/tool). A NEW module authoring graph content FAILS
until consciously added → drift becomes a reviewed decision. Self-verifying (`test_the_guardrail_has_teeth`).
Caught a real thing: `lowering.py` authors via MINT/EMIT through the machine (vision-clean), correctly NOT in
the manifest. Limits (honest): catches new AUTHORING, not policy-through-a-bridge or pure-Python branching.

**⭐ ACCUMULATOR SHAPE PROBED GO 2026-07-23 (`bench/spike_accumulator.py`).** No native rule-level numeric
comparison (only `!=`), so threshold ARITHMETIC goes through the §8 calculator/TOOL boundary (the `rank`
precedent). Vision-true layering: accumulator = a VALUED `flare_count` attr (non-monotone SET, mechanism);
threshold = a declared FACT (swappable — proven 3→5 by data alone); tally = a tool deriving `reached_limit yes`
(arithmetic only); recovery = a RULE (composes w/ authoritativeness). Only the tally is Python, only arithmetic.

**⭐ THRESHOLD-WITHOUT-A-TOOL PROBED GO 2026-07-23 (`bench/spike_threshold_no_tool.py`) — the governor can be
100% DATA+RULES, no tally tool.** Gradable degrees RULED OUT (max-of-min is idempotent → degrees don't
accumulate, can't count). WINNER: "reached level-k" = k DISTINCT `flared` events = an N-fold SELF-JOIN with
`!=` (the one native comparison) — no arithmetic. Threshold = a SWAPPABLE FACT via a bounded LADDER of named
levels + an `abandon_at ?level` fact (proven: same 2 events, severe→keep-going, moderate→abandon). Accumulator
= the monotone SET of distinct event facts (no non-monotone attribute-set needed). Trade-off: each level's
join is structural, so the ladder is bounded/declared (fine — governance = a few ordinal levels).

**⭐⭐ GOVERNOR SLICE 2 BUILT 2026-07-23 (shipped 1010 green) — 100% DATA+RULES, no Python govern(), no tool.**
Flare bridge (`ugm/flare.py`) now mints a DISTINCT `<event> flared <goal>` fact per exhaustion (accumulator =
monotone event set). `corpus/governor.cnl`: severity ladder (k-fold self-join with `!=`), swappable
`abandon_at ?level` threshold FACT, `reached`/`abandoned` reactive → self-governing at each committed act.
`tests/test_governor.py` (3). Silent-failure bug fixed en route: `authoring.load_rules` now runs
`_lift_distinct` so `!=` works in `.cnl` corpora (was: loaded-but-never-fired). Design: reactive_core.md
§reflexive governor. **THE REACTIVE-CORE + GOVERNANCE ARC IS BUILT.**

**NEXT = STEER. Candidate moves, none forced:**
- **~~The dominant flip debt is the SURFACE `X prep Y` gap~~ DECLARATIVE + INTERROGATIVE DONE 2026-07-23 (flip
  43→32, shipped 1022).** Both `bo in library` (asserts) and `is bo in library` (asks) now parse (predicating
  `clause`/`qclause` prep folds in loudon_grammar.cnl). REMAINING flip surface work is thinner: `who is in
  library` (wh-prep enumeration → no answer) + the VERBED-prep misparse (`the lion lives in africa`); the rest
  of the 32 are non-surface clusters (deferred-handler duality, existential/relation semantics, banded
  why-rendering). See the ⭐⭐ block at the top + [[flip-default-blocked-by-greedy-grammar]].
- **~~Wire the flare/governor into the live agent loop~~ DONE 2026-07-23 (shipped 1019).** A recovery reaction
  that actually escalates (a real `<call>`/`ask_user` suspension), authoritativeness choosing the recovery in a
  real `converse` session. See the ⭐⭐ LIVE-AGENT LOOP block above + reactive_core.md §Side-effect reactions.
  Follow-on surfaced: a `raise_budget` recovery action (the in-language fix for the governance self-flare
  pathology the live loop found — the reactive DERIVE inheriting the object goal's tight `max_rounds`).
- **Broader `!=`-in-corpus / custom-relation-in-fact ergonomics** — the two intake gaps this slice surfaced
  (the `!=` lift is fixed; declare-before-use for a fact relation remains a papercut).
- **The dominant flip debt is the SURFACE `X prep Y` gap (43/973, orthogonal `.cnl` lever).** `bo in library`
  doesn't parse ⇒ crisp-thief false positive. Biggest measurable correctness lever, independent of the core.
  (User deferred: harden the core first.)
- **Side-effect (`<call>`) reactions** — the third reaction kind (§C fork), which adds the world-action
  boundary to the FiringGate: a declared trigger fires a suspended `<call>` (the tool contract already
  exists, [[procedures-tool-boundary]]). Extends the reactive core into acting, not just deriving.
- **A CNL surface for the `reactive` declaration** beyond the `P is reactive` marker fact (a dedicated form),
  if a corpus needs richer trigger→reaction authoring.
- **Retire `run_bank`?** — the open question §C.3 raises: whether the legacy forward batch-push is eventually
  replaced by the reactive push. A real simplification, but a large one; scope as its own arc with the
  differential (`test_forward_demand_parity.py`) as the re-break floor.

**COMMITTED — clean tree.** The whole reactive-core + governance arc was committed by the user (branch
`grammar`, commit `7780df8 "wip grammar"`, on top of the STEP-A/STEP-B work committed in prior sessions). A
fresh session starts clean — the only thing `git status` may show is this plan doc's handoff update itself. The commit contents (for
orientation): production — `ugm/flare.py` (help-flare + counting events), `ugm/reactive.py`
(`_derive`/`react`/`fire` + `max_rounds`/flare threading), `ugm/reconsider.py` (`sweep`/`reconsider` split),
`ugm/cnl/query.py` (commit gate → `fire` + ask-path flare), `ugm/check.py` (caller-owned `fuel`),
`ugm/cnl/authoring.py` (`_lift_distinct` in `load_rules` — the `!=`-in-corpus fix), `ugm/__init__.py`
(reactive/flare exports). Corpora — `corpus/governor.cnl`, `corpus/recovery.cnl`. Tests — `test_reactive.py`
(+3 C.2 frame +6 robustness), `test_push_pull_unification.py` (8), `test_flare.py` (7), `test_governor.py` (5),
`test_substrate_purity.py` (4, the guardrail). Bench — `bench/spike_{reactive_frame,push_pull_unification,
reactive_robustness,help_flare,governor,authoritativeness,accumulator,threshold_no_tool}.py`. Suite **1012
green**.

**ORTHOGONAL, OFF THE CRITICAL PATH:** flip debt 43/930 is dominated by the SURFACE `X prep Y` gap (a
separate `.cnl` lever); STEP A/B/C do not move it and are not measured by it. The committed grammar-route
gates (`test_grammar_route_reasoning.py`, `test_grammar_shipped_agreement.py`) remain the regression floor.

### ═══ (north-star rationale + full narrative below) ═══

**THE NORTH STAR: a REACTIVE / EVENT-DRIVEN core — materializing a fact or rule TRIGGERS reactions, the
DATA decides what runs (not a driver script), and this UNIFIES push (forward) and pull (demand) so they
can no longer diverge.** This is the agent endgame and a genuine candidate UNIFICATION of the two engines
whose drift is the whole forward/demand guard-divergence class. The mechanism is NOT new-from-scratch:
forward chaining is already data-driven, and `run_bank`'s semi-naive loop is already a WORK-LIST ("a write
is an event; re-run only the rules that read what changed") — but scoped inside one call and terminating at
fixpoint. The goal reframed: LIFT that internal work-list to a STANDING, cross-call, system-wide reactive
loop, VISION-TRUE (triggers are DECLARED banks dispatched by the engine's match loop, never Python
callbacks — a generalization of a mechanism already in the machine).

**WHY IT IS STRICTLY DOWNSTREAM OF TWO PREREQUISITES (do NOT build the reactive core first — empirically
unsafe):**
1. **A LOCALITY / FRAME BOUNDARY (build first).** Events without scoping are the locality bug class at
   scale, now WITH side-effects — "rules firing on parts of the graph we don't want" (tokens, scaffolding,
   other utterances) but reacting. Reactions must fire INTO A BOUNDED FRAME. This is the derivation-frame
   work (below), and it is the SAME architecture as the reactive core seen from the data side — the first
   bounded reactive primitive.
2. **A SOUNDNESS GATE ON FIRING (reactive ≠ eager ≠ unsound).** Demand-driven laziness is a chosen
   commitment ([[agent-not-theorem-prover]]); a naive push/trigger re-introduces the rejected eager
   completion. And this scar is EMPIRICAL: [[recall-explicit-not-autofire]] — auto-firing recall
   on a demand-miss was PROVEN self-reinforcing and NAF-flipping. So firing stays DEMAND-GATED / fuel-
   bounded; "reactive" predicates are an opt-in dial (like `open_preds`), most predicates still pull.

**THE PATH (ordered, internals-first, fundamentals-not-quick-fixes — user steer 2026-07-23):**

- **STEP A — THE DERIVATION FRAME, VISION-TRUE (copy-on-lazy).** The recurring flip corner-case class is
  LOCALITY OF PROCESSING (token/entity dual-store, scaffolding enumeration leak, schema control-mirror),
  paid so far in N per-site denotation patches. The fix (user, 2026-07-23; spike **GO 3/3**,
  `bench/spike_derivation_frame.py`): reason over a materialized COPY with value semantics (one node per
  name ⇒ token/entity/scaffolding collapse or are never copied in), MERGE conclusions back to source at ONE
  identity boundary — subsumes BOTH `intern_denoted` and the who-guard at once; the node-bound
  predicate-variable reify bridge survives the copy round-trip. A projection was REJECTED: it isolates
  READS but not WRITES, and a derived fact LANDING on a node is where the aliasing bites (message-passing
  vs shared state). **VISION CONSTRAINT (user 2026-07-23): the spike's Python `project()`/`merge_back()`
  are substrate-poking and must NOT ship.** The build is COPY-ON-LAZY IN THE ENGINE: materialization +
  identity-resolution live INSIDE `_facts_matching` (an ISA fact-fetch instruction) at first-touch, the
  frame→source boundary is a SUBSTRATE RELATION read by instructions (sibling of `denotes`), and merge-back
  is a BANK using existing provenance (`proves`/`uses`), not `set_attr`. Measured by "the per-site patches
  can be DELETED and forward==demand never diverges," NOT by the flip count.
  - **DESIGN + VISION-TRUE PROBE DONE 2026-07-23** (`docs/design/derivation_frame.md`,
    `bench/spike_derivation_frame_vision.py`, GO). The forks resolved: the frame is VIRTUAL — a read-time
    UNION over a bound endpoint's CANONICAL EQUIVALENCE CLASS (node + `denotes`-co-referents, both
    directions), NOT a copy/projection and NOT a single denotes-PICK (the reverted slice-1c, which dropped
    the token-resident fact). No second graph, no merge-back, and `intern_denoted` becomes DELETABLE (reads
    union, so where a write lands stops mattering). Both consolidations live in the ONE fetch
    `_facts_matching`: the guard (fact-view, already there) + canonicalization (identity, to add in
    `_candidate_nodes` + `_bound_endpoint_ops`).
  - **⭐⭐ STEP A BUILT + LANDED 2026-07-23 (shipped 973 green, flip 43/930 UNCHANGED, `intern_denoted`
    DELETED).** `chain._canon_class` (denotes-class both directions) + `_candidate_nodes` canonicalization +
    the both-bound object-filter loop (`_bound_class_pins`, entity-pin only, report-under-original-identity,
    dedup). Chose a node-id class loop over an ISA MEMBER test (MEMBER is name-based → would over-match
    distinct same-named nodes + break skolem disambiguation; the class must be nameless denotes-structure —
    the user's "nodes are nameless in the subgraph"). `intern_denoted` machinery removed from
    `machine.py`/`lowering.py`/`intake.py`; prop-cause derives via canonicalization (gate green). Flip
    UNCHANGED = a CONSOLIDATION, not a flip-mover (identity cases were already patch-green); comparative
    INTACT on shipped (union kept what slice-1c's PICK dropped). Details+results:
    `docs/design/derivation_frame.md` §Build. NEXT = STEP B.
- **⭐ STEP B/C DESIGN SKETCH DONE 2026-07-23 (`docs/design/reactive_core.md`) — KEY FINDING: the reactive
  skeleton ALREADY EXISTS and it is `reconsider`.** The standing, cross-call, demand-gated work-list is built
  for ONE reaction (NAF-recheck): event queue = `DIRTY_REG`, trigger dispatch = `_affected` (body→head
  fixpoint over declared rules), demand-gated firing = `ask_goal(commit)` runs it before answering, soundness
  = detach-before-sweep + NAC-exclusion + monotone (= the recall-autofire invariant, ALREADY implemented).
- **STEP B — THE SOUNDNESS/FIRING GATE = GENERALIZE reconsider's gate** into a reusable `FiringGate` contract
  (demand-gated, detach-before-fire regress guard, no reaction re-enqueues its own trigger, fuel-bounded).
  Not invent — lift what reconsider proved. Re-breakable guard = the recall-autofire loop test.
- **STEP C — GENERALIZE THE REACTION.** reconsider's fixed reaction (retract-stale-NAF) → a DECLARED
  trigger→reaction (derive / retract / call), a per-predicate `reactive` opt-in (open_preds-shaped, so
  derivation pushes only where declared — laziness preserved), reactions fired into a STEP-A frame (canonical
  + guarded `_facts_matching`). Push/pull unify at the ONE dispatch (retiring the guard-divergence class).
- **⭐ REACTIVE-DERIVE PROBE GO 2026-07-23 (`bench/spike_reactive_derive.py`).** Generalized reconsider's
  front half (DIRTY_REG→detach→_affected) with a DERIVE reaction (chain_sip): a `reactive` predicate's
  consequence materialized proactively at the next committed act with NO query (data drove it), non-reactive
  stayed lazy-but-demand-derivable, firing idempotent. SHARPER SAFETY FINDING: the reactive gate avoids
  recall-autofire BY CONSTRUCTION — it is PRESENCE-triggered (fires on a positive materialization), not
  MISS-triggered (recall-autofire fired on an absence and filled it → self-reinforced), so the
  self-reinforcement channel does not exist; termination follows from monotonicity. STEP B's contract is
  smaller than feared.
- **⭐⭐ STEP B BUILT + LANDED 2026-07-23 (shipped 978 green — 973+5).** `ugm/reactive.py`: `react(kb,rules)`
  (the DERIVE half of the FiringGate) wired into `ask_goal`'s commit gate BEFORE `reconsider` (shares the
  dirty set; reconsider detaches). A predicate declared reactive (`declare_reactive`/`reactive_preds`, a
  `kb.registers` set) has its consequence materialized demand-driven (`chain_sip`) at the next committed act
  when its trigger landed. INERT by default (early-returns with no reactive preds → shipped unaffected).
  `tests/test_reactive.py` (6): proactive-materialize-without-query, non-reactive-stays-lazy, demand-gated,
  idempotent-after-consume, mutually-reactive p↔q CYCLE DRAINS (recall-autofire re-break), AND declaration-
  as-DATA. **DECLARATION-AS-DATA surface landed too (shipped 979 green):** `reactive_preds` reads `P is
  reactive` FACTS off the KB (unioned with the register), so a corpus declares its own reactivity in its own
  text — no loader, no Python, cost-free by default. NEXT = the REST of STEP C (unify retract+derive under
  ONE gate consuming the dirty set once; fire into a STEP-A frame; the push/pull unification claim), or steer.

**HOW THE FLIP + SURFACE FIT NOW (downstream, orthogonal):** the flip debt is **43/973** (measured
2026-07-23). STEP A retires the IDENTITY subset. The DOMINANT remaining cluster is SURFACE-gated (`X prep
Y` predicating clause — `bo in library` doesn't parse ⇒ bo is a crisp thief ⇒ `is anyone thief` = `yes`
not `likely`, VERIFIED), which the frame does NOT touch — that stays a SEPARATE, independently-scheduled
`.cnl` grammar lever, not on the reactive-core critical path. The committed grammar-route validation gates
(`test_grammar_route_reasoning.py`, `test_grammar_shipped_agreement.py`) remain the regression floor.

---

## ▶ PRIOR ARC (2026-07-22, context/history) — COMPOSITION CLOSURE → SCOPE GENERALIZATION (suite **873 green**)

**⭐ CAUSATION CORE — BACKWARD DIAGNOSIS LANDED 2026-07-22 (suite 909 green), the first slice of the
next arc (§9.2 sequences causation FIRST).** A PROBE re-scoped it: C1 entity-level causation is native
THROUGH REAL INTAKE (`causes` = a declared relation + an ordinary propagation rule derives the effect —
`does X have Y` answers `yes`), so the forward/plan direction needs no build. The genuinely-missing
capability is BACKWARD DIAGNOSIS ("why does this hold?"), and it turned out to be a SURFACE-WIRING slice,
not new reasoning: provenance (`proves`/`uses`) + `surface.explain` already walk a fact's derivation
(the rule, its premises, the `causes` link, and the NAF leaps) — the legacy `query.py` even had `why`
forms, but off the unified `ingest` route. The slice: `ugm/cnl/why_surface.parse_why` (a pure keyword-led
recognizer, `why S P O` / `why is S O` / `why is S a O`, PREDICATE-FAITHFUL so it dodges the orthogonal
`has`/`have` gap) + a `why` route in `intake.py` above the yes/no recognizer that answers via the
STRUCTURED tuple goal `ask_goal(kb, ("why", s, p, o), …)` (bypasses the question STRING; runs the closure
with provenance always-on, then `explain`). New `Outcome("why", explanation=…)` kind + `Event("why")` /
`Event("explanation")`. `tests/test_why_diagnosis.py` (9). One test re-homed: `why is ada thief` now
routes `why` with the trace in `.explanation`, not overloaded into `.answer` (`test_habitability`).
- **⭐ THE `has`/`have` CONFLUENCE GAP — FIXED 2026-07-22 (suite 913 green), and it IS sugar.** `does X
  have Y` asked predicate `have` while `X has Y` stored `has`, so even a stored fact answered `no
  (assumed)`. Classified via `baroque-vs-fundamental`: `has`/`have` are surface inflections of ONE
  relation (paraphrasable, belief-invariant) ⇒ SUGAR — the exact category as the existing `are`->`is`
  fold (`forms.normalize_lexical`, "mechanical, meaning-free, not reasoning"). Root cause was STRUCTURAL:
  the assertion tokenize applied `normalize_lexical`, the QUESTION tokenize (`query._recognize_question`)
  did NOT — so the two paths normalized differently. Fix: generalized the fold to a `{synonym:canonical}`
  map with `have`->`has` (`had` LEFT ALONE — past tense is the temporal arc's, not sugar) and applied it
  on the question path too. What it PROTECTS is fundamental: both surfaces of a relation must
  canonicalize to one predicate (same failure family as the determiner kind/property mismatch). General
  open-class verb inflection stays the prose->CNL translator's job. `tests/test_verb_morphology.py` (4).
- **⭐ `what causes X` LANDED 2026-07-22 (suite 918 green) — variable-binding backward diagnosis.** The
  ENUMERATE counterpart to `why` (which explains ONE known fact): `what causes X` lists the causes.
  PROBE finding: `who causes X` already worked (it is a `who P O` wh-query, qtype `who`); the only gap was
  that `what` was not a recognized wh-word, so `what causes X` mis-routed to the FACT path and silently
  asserted a bogus `what causes X` fact. Fix = two additive `what` subject-wh forms in `query.py`
  mirroring the `who` pair, both mapping to qtype `who` — SUGAR again (`what`/`who` = a person/thing
  surface split with NO query difference in a label-less substrate). Held the boundary: the n-ary OBJECT
  `what` (`SUBJ V what P ARG`, non-leading) is a different construction, untouched. `tests/
  test_what_causes.py` (5, incl. the no-bogus-fact regression + who/what agreement).
- **⭐ FORWARD-SUGAR LANDED 2026-07-22 (suite 923 green) — and the finding is that it needs NO ENGINE
  CODE.** "Declaring `X causes Y` should propagate the effect without hand-writing `?x has ?e when ?x has
  ?c and ?c causes ?e`" is DECLARED DATA via the EXISTING `define schema` meta-pattern: a TWO-parameter
  schema `define schema ?r propagates ?base : ?x ?base ?e when ?x ?base ?c and ?c ?r ?e` captures the
  causal-propagation MEANING once, then `causes propagates has` (a plain fact) materialises the concrete
  rule — exactly as `ancestor is transitive` materialises transitivity. So causation is NOT privileged:
  its propagation is declared like any relation property, honouring "domain logic ONLY in banks". One
  schema serves many causal relations (`causes`, `enables`, …), and `why` sees the materialised firing's
  provenance. This also VALIDATED multi-parameter schemas (the shipped `transitive` schema is
  single-param). DELIBERATELY NOT shipped as a built-in `propagates` schema — that would privilege
  causation against the same principle that keeps `transitive` declared; a default causal vocabulary is a
  separate opt-in if wanted. `tests/test_causal_propagation.py` (5, incl. the re-break: no schema ⇒ no
  propagation).
- **⭐ COUNTERFACTUAL LANDED 2026-07-22 (suite 928 green) — causation's THIRD §9.2 direction; core now
  COMPLETE.** `suppose A : P` / `what if A : P` entertains `A` and reads whether `P` would hold, INKING
  NOTHING — the ADDITIVE counterfactual ("if A *were* so, would P hold?"), which is NATIVE via
  `suppose(commit=False)` (probe: baseline `no (assumed)`, `suppose lion has hunger` ⇒ CONFIRMED, derives
  `lion has aggression` in pencil, ink unchanged). Slice = surface only: `ugm/cnl/suppose_surface.py`
  (pure keyword parser, `suppose`/`what if`, `:` splits assumption from prediction, predicate-faithful +
  `have`->`has`) + an intake route → `_reify_rules` + `suppose(commit=False)`, verdict→answer
  (CONFIRMED=yes, INCONCLUSIVE=no (assumed), REFUTED=no). New `Outcome("suppose")` + `Event("suppose")`.
  The SUBTRACTIVE counterfactual ("if A were NOT so") needs retract-under-hypothesis (non-monotone) = the
  out-of-core completion, not surfaced. `tests/test_counterfactual.py` (5, incl. the non-inking guarantee).
- **⭐⭐ CAUSATION CORE COMPLETE (§9.2):** forward (`causes propagates has` schema) + backward-explain
  (`why X`) + backward-enumerate (`what causes X`) + counterfactual (`suppose A : P`). THE ARC'S
  THROUGH-LINE: almost everything was SUGAR / declared-data / surface-wiring — the only genuinely new
  intake surfaces were `why`/`suppose` routes, both thin wrappers over existing machinery (`explain`,
  `suppose`). Probing first turned each "missing capability" into a declaration or a surface, never engine.
- **⭐ EXISTENTIAL CORE (§9.2 #2) — CONFIRMED NATIVE THROUGH INTAKE 2026-07-22 (suite 934 green). No
  build; a probe + a guard test.** "A witness exists without a name, resolved on demand" works end-to-end
  via the EXISTING rule + question forms: the LHS-keyed skolem head (`k? opens ?d when ?d is a locked`)
  parses and mints an unnamed witness per match; the existential yes/no (`does anything opens door1` →
  yes, `is anyone happy` → yes) resolves it on the demand path; enumeration (`who opens door1` → `k opens
  door1`) finds it; and it COMPOSES DOWNSTREAM (E2: `is door1 accessible` → yes via the unnamed opener,
  control plain door → no). `tests/test_existential.py` (6, incl. the no-rule-no-witness + keyed-to-match
  controls). **§9.2's THREE agentic cores are now all reached** (causation, existential, ordered-ranging).
  - **Two gaps, both correctly OUT:** (a) general verb inflection `open`/`opens` — the open-class
    lemmatization deferred as the translator's job (only the closed-class `have` was folded); (b) a DIRECT
    existential ASSERTION `some key opens door1` mints a node literally named `key` (conflates witnesses)
    — the out-of-core COMPLETION, because a bare assertion has no LHS to key the witness on, colliding
    with [[skolem-minting-lhs-keyed]] (agent asserts a rule/specific fact, not a bare ∃).
  - **⚠ ORTHOGONAL BUG FOUND (not existential): a rule head `?d is a KIND when …` mis-routed to the FACT
    path (the `when` dropped, landing as a fact), while `?d is PROP when …` routed `rule`. — FIXED
    2026-07-22 (suite 945 green).** ROOT CAUSE: the prose `rule.head` form is rigid 3-token (`?hs ?hp ?ho`
    then `when`), so a 4-token KIND head (`?d is a predator`, the determiner `a` between `is` and the kind)
    could not match and fell through to the fact path. Fix = a `rule.head.is_a` variant (`authoring.py`
    RULE_FORMS) that folds `S is a KIND when …` to the SAME `is_a` predicate a `X is a Y` FACT produces
    (`_SUGAR_IS_A`) — so the derived head and a `is X a Y` query agree, the determiner carrying kind-vs-
    property exactly as on the fact side. The plain form self-excludes (`a` never abuts `when`), so the two
    are unambiguous. `tests/test_new_core.py` (2: fold + end-to-end firing with a negative control). NOT
    covered (documented first-slice limits, same as the plain head): the `if … then S is a KIND` and
    plural-noun universal surfaces keep their 3-token heads; a KIND head there is a separate small slice.
- **⭐⭐ ② FACTS-AS-TRUTH-BEARERS BUILT 2026-07-22 (suite 943 green) — the genuinely-fundamental primitive,
  and it is PREDICATE-VARIABLE MATCHING, not causation-specific.** The user picked the full engine build
  over the surface ceiling. A probe first RE-SHAPED the finding (the arc's method, and this is the arc's
  ONE non-sugar item): the binder spike recorded C3 as "clauses must be S-P-O so `?b holds` is unwritable,
  and no dereify" — **both wrong-as-stated.** A 3-token variable-predicate clause `?s ?p ?o` authors fine
  (only the 2-token `?b holds` is rejected — ARITY, not predicate-vars); the DEREIFY (variable-predicate
  HEAD, `?p` LHS-bound) ALREADY fired forward (the `MINT.key_reg` write side); and propositional MP is
  pure S-P-O over handle entities. **The one true wall was READING a fact through a bound predicate
  variable** (the REIFY direction — the lowerer's "no ground anchor") plus DEMAND-REACHABILITY of
  variable-predicate rules. So propositional causation is DECLARED DATA — a three-rule reification bridge
  (`bench/spike_facts_as_truth_bearers.py`): `?h truth yes when … ?h pred ?p … and ?s ?p ?o` (reify) /
  `?b truth yes when ?a truth yes and ?a causes ?b` (MP, S-P-O) / `?s ?p ?o when … ?h truth yes`
  (dereify) — honouring "domain logic ONLY in banks", causation UNprivileged.
  - **THE PRIMITIVE, on BOTH engines (forward + demand parity):**
    - **`machine.py`:** `TEST`/`SEED` gained a `key_reg` (dynamic key = `name(regs[key_reg])`), symmetric
      with the existing `MINT`/`EMIT.key_reg` write side — the read half of predicates-are-keys.
    - **`lowering.py` `lower_conj`:** split the "bound predicate var" case with a new `rel_vars` set — a
      var bound in PREDICATE position stays a rel-node reuse (unchanged); a var bound in an ENDPOINT
      position (`?h pred ?p`) is a VALUE node, matched via the dynamic-key `TEST(rel, key_reg=?p)`. This
      also FIXED a pre-existing endpoint-bound-predicate bug (it used to reuse the value node as a rel reg).
    - **`chain.py` (demand):** `_unify_head_with_demand` binds a variable head predicate to the demanded
      predicate's value-node; the body loop resolves a bound `?p` to its predicate string (`_pred_name_of`
      = operand-value-or-name, the value-node/entity denotation bridge) before `_facts_matching`; the head
      EMIT resolves `hp` likewise; `_sideways_order` defers a var-pred atom until `?p` is bound.
    - **`apply.py` (head index):** a variable-predicate head is catalogued under a `HEAD_VAR_PRED`
      wildcard bucket; `rules_producing` returns it for every concrete demand.
  - **THE PRIMITIVE IS GENERAL — the promised bonus landed:** generic relation-property transitivity
    written ONCE over `?r` (`?x ?r ?z when ?x ?r ?y and ?y ?r ?z`) now works on demand (the query supplies
    the anchor). Re-break-guarded that it does NOT over-reach (`a rel b` + `b other c` ⇏ `a rel c`).
  - **`tests/test_facts_as_truth_bearers.py` (9):** reify/dereify each direction, the full bridge forward
    AND demand with negative controls (soundness: antecedent absent ⇒ no consequent), generic transitivity
    + its non-over-reach guard, and the 2-token arity boundary still rejected. ZERO regressions across the
    whole suite despite touching all four hot-path modules; re-break confirmed the wildcard-head-index
    guard is load-bearing (both demand tests fail without it).
  - **THE SURFACE LANDED 2026-07-22 (suite 953 green): `that A causes that B`.** The Option-B follow-on,
    now riding the primitive above (not the no-engine ceiling). `ugm/cnl/cause_surface.py` (a pure
    keyword/structure recognizer like suppose/why, grammar refuses it) + a `cause` intake route above the
    fact route. The `that` NOMINALIZER is the whole discriminator — `that door1 is open causes that cat is
    scared` marks TWO propositions, while a bare `hunger causes aggression` is ENTITY-level (C1, native)
    and left to the fact route (re-break-guarded: bare `A causes B` never routes `cause`). Emits
    content-keyed HANDLES (`prop:s:p:o`, plain names so their facts are visible) carrying subj/pred/obj +
    a `causes` edge via `assemble_facts` (interns by name ⇒ coref with the proposition's entities), and
    installs the three bridge rules ONCE into the `rules` list (idempotent by key). KEY: because rules
    live in the LIST (reified at query time), the surface is ORDER-INDEPENDENT — a link stated before its
    antecedent still fires when the antecedent lands (a raw one-graph `write_rule` before facts does NOT,
    a pre-existing interning collision, but the intake model dodges it). CHAINS (A→B→C via the derived
    middle fact), handles KIND propositions (`is_a` agrees both sides), reconsider-dirties the consequent.
    `Outcome("cause")` + `Event("cause"/"cause-done")`; `tests/test_propositional_cause.py` (8, incl.
    order-independence, chaining, negative control, the `that`-nominalizer boundary). Clause menu mirrors
    `suppose_surface` (`S P O` / `S is O` / `S is a O`) + a 2-token intransitive `S P` → `S P yes`.
## ▶ SESSION DETAIL 2026-07-23 (suite **973 green**, flip **43/973**) — STEP A groundwork

> The arc was RE-POINTED above (LOCALITY BOUNDARY → REACTIVE CORE) after this block was written; the
> frame spike here IS "STEP A". Pick up at the new arc's **NEXT CONCRETE STEP** (design doc + vision-true
> probe). Detail below.

**⭐⭐ THE CONSOLIDATION DIRECTION IS DECIDED (user, 2026-07-23): a DERIVATION FRAME (materialized COPY
+ merge-back), NOT a read-projection, NOT more per-site patches. Spike GO 3/3 —
`bench/spike_derivation_frame.py`.** The user reframed the whole recurring corner-case class as
LOCALITY-OF-PROCESSING (rules/reads touching graph they shouldn't — the token/entity dual-store, the
scaffolding enumeration leak, the schema control-mirror) and argued the fix is message-passing over
shared-state: reason over a COPY with value semantics (one node per name ⇒ token/entity/scaffolding
collapse or are never copied in), then MERGE conclusions back to source at ONE identity boundary —
discardable/re-derivable like an ETL job or a stack frame. Rationale that settled projection-vs-copy: a
projection isolates READS but not WRITES, and writes (a derived fact landing on a node) are exactly where
the aliasing bites, so a view leaves the shared-state bug in place; a copy gives write-isolation.
- **SPIKE VERDICT (3/3, `python -m bench.spike_derivation_frame`):** a one-node-per-name copy dissolves
  the identity class at one boundary, SUBSUMING BOTH per-site patches at once — the `intern_denoted`
  WRITE-patch (CASE 1: prop-cause authored `intern_denoted=False` answers `no (assumed)` on the shared
  graph, `yes` in the frame) AND the who-branch READ-guard (CASE 2: enumeration is structurally clean —
  no empty-named scaffolding row — with no guard). The node-bound predicate-variable reify bridge SURVIVES
  the project→reassemble round-trip (the "does the copy preserve enough?" risk — answered yes). CASE 3:
  merge-back lands the conclusion on the source entity (`no (assumed)`→`yes`), frame discarded.
- **COPY-ON-LAZY is the production shape (user's follow-up + agreed):** don't eager-project the whole KB
  (the spike did, to prove the hypothesis) — start an EMPTY frame that materialises a source node at
  FIRST-TOUCH by the demand path (`_facts_matching`), resolving identity once per node and memoising the
  frame→source back-pointer. The frame IS the memo table; reconciles value-semantics isolation with the
  lazy/demand engine, and collapses the N denotation call-sites into the ONE fact-fetch primitive. NOT
  built — the next probe.
- **KNOWN LIMITS the spike made concrete (cost, not correctness):** (a) the merge boundary must carry an
  explicit frame→source back-pointer (ById discipline), not re-resolve by NAME as the spike's `merge_back`
  does, or a genuine same-name/different-entity case mis-merges — but it is ONE place to get right; (b) the
  frame fixes the IDENTITY/locality class ONLY — a fact that never PARSED (`bo in library`, the `X prep Y`
  surface gap) is not in the projection to copy, so surface-coverage gaps are untouched (consistent with
  the flip categorization: test_world banded failures are SURFACE-gated — `bo in library` doesn't parse ⇒
  bo is a crisp thief ⇒ `is anyone thief` = `yes` not `likely`, VERIFIED this session); (c) `commit=False`
  already scopes crisp WRITES into a suppose pencil scope but IN THE SHARED GRAPH, so reads still alias —
  the COPY is the missing half, complementary to write-scoping.
- **HEDGE STOPGAP REVERTED (was the anti-pattern).** Mid-session I built a `possibility._entity(denoted=)`
  / `add_fork(denoted=True)` hedge dual-store patch (item 2) — but it is the N+1th per-site denotation
  patch the frame arc retires, its gate test did NOT discriminate (passed with AND without the fix, because
  chain joins by NAME so the hedge-on-token split is tolerated for name-level joins — only NODE-bound joins
  break), and it fixed no shipped failing test (the test_world banded misses are surface-gated). Reverted
  cleanly; working tree = only `?? bench/spike_derivation_frame.py`. Lesson recorded: the hedge dual-store
  is real (hedge pencil lands on the token without the patch — verified) but does NOT bite name-level joins.
- **NEXT (recommended):** probe COPY-ON-LAZY — put the denotation-resolution + frame-memo inside
  `_facts_matching` (the one fact-fetch), start empty, materialise at first-touch, carry a frame→source
  back-pointer for merge. Validate it subsumes intern_denoted + the who-guard (re-run the spike's cases
  through the lazy path) with zero shipped regression. THEN the surface bucket (`X prep Y`) is still the
  separate, orthogonal lever for the surface-gated flip failures.
- **Flip re-measured 43/973 this session** (harness recreated: scratchpad `flipplugin.py` patches
  `grammar_intake.session_banks` to declare-on-first-use `open_class="noun"`; `-p flipplugin` with the
  scratchpad on PYTHONPATH; ~4.75 min). Clusters unchanged in KIND from the 2026-07-22 handoff below
  (surface `X prep Y`, integration, schema/causal/counterfactual, banded-surface-gated).

---

## ▶▶ SESSION-END HANDOFF 2026-07-22 (suite **973 green**)

**═══ START-HERE (fresh-session summary; details in the dated blocks below) ═══**

**ONE-LINE STATE.** The flip-default arc is proceeding **validation-first, internals-first**: three
committed fixes landed this session (all shipped-green), the flip debt is down to **45 fails / 973**, and a
spike settled HOW the deep consolidation must be done. The remaining internal work is understood and bounded.

**⚠ UNCOMMITTED WORKING TREE (verified `git status`, NOT from memory — re-verify at session start). KEEP ALL:**
- `M ugm/machine.py` — step-2 `MINT.intern_denoted` (write-side token→entity for deferred recognizers).
- `M ugm/intake.py` — step-2 propositional-cause emit uses `intern_denoted=True`.
- `M ugm/lowering.py` — schema fix: `guard_fact` + `fact_only` plumbing through `run_bank`/`_lower_bank_rule`.
- `M ugm/cnl/define_surface.py` — `apply_schemas` calls `run_bank(..., fact_only=True)`.
- `M tests/test_grammar_route_reasoning.py` — grammar-route reasoning gate (+propositional-cause, +schema tests).
- `?? tests/test_grammar_shipped_agreement.py` — NEW shipped-vs-grammar agreement harness (9 scenarios).
- `M docs/implementation_plan.md` — this handoff.
- Nothing committed by the assistant (standing rule). Run the EOL check before any commit (all LF now).

**WHAT LANDED THIS SESSION (all shipped 973-green, flip 51→45):**
1. **Validation infra** — `test_grammar_route_reasoning.py` (grammar-route REASONING gate) + NEW
   `test_grammar_shipped_agreement.py` (parametrized: both routes must reason IDENTICALLY + hit the answer).
   These gate the exact regression class the shipped suite structurally can't catch.
2. **Step 2 — propositional-cause WRITE-SIDE duality fix** (the proper re-derivation of reverted slice-1c):
   opt-in `MINT.intern_denoted` (deferred recognizers intern handle endpoints THROUGH `denotes` to the
   ENTITY, not the token). Strictly better than slice-1c — no read-path change, comparative order untouched.
3. **Schema forward-match control guard** (Option A, scoped): `guard_fact`/`fact_only` — the meta-bank matches
   FACTS only (control+inert guarded), closing the forward-vs-demand guard divergence for that one bank.

**THE CONSOLIDATION SPIKE VERDICT (the strategic result — read the two ◆ blocks below).** The recurring
corner cases are NOT the ISA/firmware or the S-P-O rule shape (every fix was small+local, all cases are
GRAMMAR-ROUTE-ONLY; shipped is 973-green throughout). Two real causes: (1) a layered identity model (one
referent → token+entity+copies+control-mirror) with no single enforced invariant; (2) forward vs demand
disagree on "what is a fact." The spike PROVED the fix for (2) must be a **PER-CALL contract**, not per-rule
(per-rule breaks recognition — the forward path is dual-purpose). Mechanism = tag REASONING `run_bank` calls
with `fact_only=True`; `guard_fact`/`fact_only` is already its first instance.

**NEXT, IN ORDER (internals-first):**
1. **The consolidation (real fix for divergence class):** audit `run_bank` call sites; tag the REASONING ones
   (`run_rules` forward snapshots, comparison-rule runs, any reasoning bank) `fact_only=True`; measure each.
   Low-risk, one site at a time. Retires the schema/enumeration divergence class at the reasoning boundary.
2. **Hedge dual-store** — extend `intern_denoted` (proven pattern) to the hedge/uncertainty emit path; the
   test_world banded misses are this (validate on a morphology-clean scenario, NOT test_world — it's
   entangled with the `X prep Y` surface gap).
3. **THEN surface + integration** (deliberately last): `X prep Y` predicating clause (riddles/new_core),
   existentials, intake_forms/act/surface_facts rewrites, the `SWEEP refused` caller.

**RE-MEASURE THE FLIP:** scratchpad `flipplugin.py` (a pytest plugin patching `grammar_intake.session_banks`
to declare-on-first-use, `open_class="noun"`) — run `-p flipplugin` with the scratchpad dir on `PYTHONPATH`.
Current: **45 fails / 973**. ~4.5 min; run in background.

**═══ (dated detail blocks follow) ═══**

**⭐⭐ SCHEMA FORWARD-MATCH CONTROL GUARD — LANDED 2026-07-22 (suite 973 green). Option A, scoped, the
principled fix.** The `test_schema_surface` flip crash (5 tests) was `define schema ?r is transitive` +
`ancestor is transitive` → `expand_rules` CRASH (`k_pred resolves to no token`). ROOT CAUSE: `apply_schemas`
runs the schema meta-bank FORWARD via `run_bank`, and the forward path keeps CONTROL nodes matchable BY
DESIGN (`AttrGraph.set_inert` docstring: a control relation like the planner's `chosen` must be read by
forward control rules) — only the DEMAND path's `_guard` excludes them. On the grammar route a folded fact
leaves its `is_a` content on BOTH the entity AND an interpretation control node, so the trigger `?r is_a
transitive` bound the unnamed control node too and reflected a malformed rule. Same forward-vs-demand guard
divergence as the slice-1a enumeration leak. FIX (chosen with the user, Option A over the surgical Option B):
an OPT-IN full fact-guard for the meta-bank only — `lowering.guard_fact` (control + inert absent, the same
pair `chain._guard` emits) threaded through `run_bank(..., fact_only=True)` → `_lower_bank_rule` (cache key
extended) → used ONLY by `apply_schemas`. NOT a blanket forward guard (Option C) — that would break forward
control rules; scoping keeps the default forward path (control stays matchable) untouched. Inert on the
shipped route (no interpretation control nodes). Validated: shipped 973 green (hot-path `run_bank`/lowering
touched, suite time flat ~94s), `test_schema_surface` 8/8 under the flip (was 5 failing), + committed gate
`test_grammar_route_reasoning::test_a_define_schema_materialises_over_the_grammar_route` (reproducible with a
plain `declare_grammar`, no harness). Files: `lowering.py` (guard_fact + fact_only plumbing),
`define_surface.py` (the one call site). **FLIP RE-MEASURED: 50 → 45 fails** (the schema cluster cleared,
zero new failures).

**◆ THE DEEPER DIAGNOSIS (user's question 2026-07-22 — why we keep hitting corner cases).** Every flip
corner case this session (propositional-cause token/entity, comparative regression, schema control-mirror,
enumeration leak, order-independence) is GRAMMAR-ROUTE-ONLY — the shipped route (one referent = one node) is
973 green throughout. So the mechanism (ISA/firmware, S-P-O rule shape) is NOT the culprit: every fix was
small + local, nothing cascaded (the firmware bet paying off), and no case was a rule-expressiveness or
join-semantics failure. The real cause is TWO unreconciled things: (1) the grammar route runs a LAYERED
identity model (one referent → token + entity + copies + control-mirror) over a substrate that assumes "a
node IS a thing," with NO single enforced invariant — we resolve identity CASE BY CASE (`_through_denotation`
at N sites, a guard here) instead of at one boundary; (2) TWO fact-matchers (forward `run_bank` vs demand
`chain`) that must agree but DRIFT (the control-guard divergence was today's schema + earlier enumeration
bug). "Doing it right" = two CONSOLIDATIONS, not a new formalism: (a) one identity boundary (canonical `ById`
by construction, denotation as a substrate primitive); (b) one guarded fact-view shared by forward+demand so
they cannot diverge. Both are the deferred UNIFICATION ARC (retiring the duality fights the deliberately-kept
surface/interpretation split) — we are paying it in installments, one corner case each. HIGHEST-LEVERAGE
next: spike consolidation (b) — smaller than full identity-unification, retires the whole forward/demand
guard-divergence CLASS (schema + enumeration were both it).

**◆ CONSOLIDATION SPIKE (b) — DONE 2026-07-22. VERDICT: the shared fact-view is real, but PER-CALL, NOT
per-rule.** Hypothesis tested: derive the fact-guard PER RULE (from what it READS, split from the producer-
side `_rule_touches_control` which includes the head) and apply it on the forward path so a fact rule matches
identically to the demand engine. RESULT: **per-rule auto-derivation is a hard NO-GO.**
- Attempt 1 (LHS/NAC has a `<…>` control token ⇒ reads control, else fact-rule ⇒ full guard): **401 fails,
  grammar DECLARATION itself errors** ("no lexicon"). `compile_grammar` parses via `run_bank`, and
  recognition/parse rules read control scaffolding (spans, `next`-chains) WITHOUT a `<…>` gate token, so they
  were misclassified as fact rules and guarded → parsing produced nothing.
- Attempt 2 (also treat a LHS predicate in the caller's `control_preds` as a control read): **still empty
  grammar** — `compile_grammar`'s vocabulary parse (`run_bank(tmp, VOCABULARY_FORMS)`) passes NO
  `control_preds`, so those parse rules' control reads are undeclarable at that granularity.
- ROOT: the forward path is DUAL-PURPOSE (recognition READS control scaffolding + reasoning reads facts), and
  "control visible by default" is LOAD-BEARING for recognition. There is NO per-rule SYNTACTIC signal that
  reliably separates the two — the layer is a property of the CALLER/bank, not the rule.
- **VERDICT: GO on the consolidation, expressed as a PER-CALL contract.** The reliable signal is the caller:
  REASONING `run_bank` calls opt into the fact-guard (`fact_only=True` — `apply_schemas` already does, and the
  schema fix's `guard_fact`/`fact_only` machinery IS the first instance of this contract); RECOGNITION calls
  keep the default (control visible). This gives "forward reasoning == demand" (the meaningful half; recognition
  has no demand counterpart, so no divergence there to close). Fully reverted, suite back to **973 green**.
- **THE REAL FIX (post-spike, incremental, low-risk):** audit the `run_bank` call sites, tag the REASONING
  ones (`run_rules` forward snapshots, comparison-rule runs, any reasoning bank) with `fact_only=True`, measure
  each. That retires the forward/demand guard-divergence class at the reasoning boundary WITHOUT touching
  recognition. Each call site is one small, independently-measurable step.

**⭐⭐ STEP 2 (re-derive slice-1c PROPERLY) — DONE 2026-07-22 (suite 972 green), and the re-derivation is
STRICTLY BETTER than the reverted slice-1c.** The reverted slice-1c resolved node identity THROUGH `denotes`
on the READ path (`_candidate_nodes`/`_bound_endpoint_ops`/`resolve_write_node`), which fixed
propositional-cause but REGRESSED comparative partial-order under the flip (`is cy more suspicious than bo`
→ `unknown`, because the transitive rule's bound middle-variable got resolved to the entity while the
comparison fact — authored by the DEFERRED comparison recognizer, which interns by name to the TOKEN — sat
on the token). REPRODUCED both directions this session (scratchpad `repro_slice1c.py` under a rebuilt flip
harness). **THE ROOT CAUSE is a DUAL FACT STORE, and the fix is on the WRITE side, opt-in, not the read
path:** the grammar route folds a proposition's content onto the interpretation ENTITY, but a deferred
recognizer's `assemble_facts` interns its handle endpoints by name to the TOKEN (inserted first ⇒
`nodes_named[0]`), so a node-bound bridge join reads the content-free token → `no (assumed)`. FIX = an
opt-in `intern_denoted` mode: `MINT.intern_denoted` (machine intern branch follows `denotes` on the chosen
canonical node), threaded through `assemble_facts(..., intern_denoted=True)`, set ONLY at the
propositional-cause emit site (`intake.py` ~797). Inert on the shipped route (no `denotes`) and GATED, so
the grammar route's own duality-preserving interning is untouched.
- **WHY NOT the global machine intern branch:** tried it un-gated first — broke 10 grammar-route tests
  (contradiction / discardable-interpretation / reconsider / negation folding), because the grammar route's
  OWN folding interns through that branch and DELIBERATELY keeps token≠entity ([[surface-interpretation-split]]).
  The gate is load-bearing: the fix must reach only the deferred recognizers, never the fold.
- **VALIDATED against BOTH gates + a new committed test.** `test_grammar_route_reasoning.py` gained
  `test_a_propositional_cause_link_derives_over_grammar_folded_propositions` (+ its no-antecedent re-break),
  reproducible with a plain `declare_grammar(open_class="noun")` — NO scratchpad harness. Full suite 972
  green (was 970), shipped time flat (~84s ⇒ no hot-path regression), comparative partial-order UNTOUCHED.
- **KNOWN LIMIT (deliberately not chased): order-independence under the flip.** `that A causes that B`
  stated BEFORE its antecedent `A` still answers `no (assumed)` under the flip, because at intern time the
  entity `A` denotes does not exist yet, so the handle interns to an orphan node. The SHIPPED route is
  order-independent (rules live in the LIST, reified at query time); the flip's break is the same
  entity-doesn't-exist-yet family as the link-first riddle. Small follow-up, not this slice.
- **UNCOMMITTED at this handoff:** `M ugm/machine.py ugm/lowering.py ugm/intake.py`,
  `M tests/test_grammar_route_reasoning.py`, `?? tests/test_grammar_shipped_agreement.py`, `M docs/…`. KEEP.

**⭐ FRESH FULL FLIP MEASUREMENT 2026-07-22 (with the write-side fix in place): 50 fail / 922 pass** (was
51 at revert, pre-fix). Rebuilt harness = a pytest plugin patching `grammar_intake.session_banks` to
declare-on-first-use (`open_class="noun"`) — catches EVERY ingest path incl. name-imported `ingest` and
`load_corpus("")`, no per-module patching (scratchpad `flipplugin.py`/`conftest.py`; run `-p flipplugin`
with the scratchpad on `PYTHONPATH`). Fail clusters, MECHANISM-VERIFIED by reading each (not sampled):
- **test_schema_surface (5) — PURE INTERNAL, a CRASH, the cleanest next target. DIAGNOSED.** `define schema
  ?r is transitive` + `ancestor is transitive` CRASHES in `expand_rules` (`k_pred resolves to no token`).
  ROOT CAUSE: the schema meta-rule runs FORWARD via `run_bank` (in `apply_schemas`), and forward matching
  does NOT apply the demand path's control/inert `_guard` — so `?r` binds to BOTH the genuine entity
  (n-named "ancestor") AND a grammar-route interpretation CONTROL node (unnamed, ctrl=True) that also
  carries the `is_a transitive` edge. The control-bound fragment reflects to a malformed rule (unnamed
  predicate) → crash. SAME CLASS as the slice-1a enumeration leak (forward vs demand guard divergence). FIX
  = guard control/inert nodes in the schema meta-rule's forward run — SCOPE IT to `apply_schemas`'s
  `run_bank` (a run-bank control-skip option, or a meta-rule trigger guard), NOT a blanket forward-matcher
  change (the grammar route's own forward passes legitimately touch control nodes — the risk the unification
  probe flagged). This is a deliberate 1-slice fix, deferred to start fresh (long session).
- **test_world (4) — HETEROGENEOUS (surface + internal), do NOT treat as one.** `is bo thief → yes` (should
  be `no (assumed)`) is the `X prep Y` GRAMMAR GAP: `bo in library` doesn't parse → bo never innocent/cleared
  → thief. That is SURFACE (`.cnl`). The cy/banded misses (`is anyone thief → yes` not `likely`; `why cy is
  cleared` missing the `cy is alibied (unlikely)` premise) are HEDGE DUAL-STORE — the hedge (`cy is unlikely
  alibied`, a deferred recognizer) interning to the token, the same family `intern_denoted` fixed for
  propositional-cause. The hedge dual-store is the natural EXTENSION of the write-side fix (apply the pattern
  to the hedge/uncertainty emit path) — but it is entangled with the `in library` surface gap in these tests,
  so validate on a morphology-clean scenario, not test_world directly.
- **Grammar coverage / surface (riddles 3, new_core 3, isa_value_match 2, some world/isa_ask): the `X prep Y`
  predicating clause + existentials.** `.cnl`-file work, deliberately LAST.
- **Integration (intake_forms 5, intake_act 3, intake_surface_facts 3, + singles): authored-forms routing,
  the `SWEEP refused` caller, accretion/harness test rewrites.** The plan's originals.

**NEXT (recommended order, internals-first per the user's steer):** (1) the **schema forward-match control
guard** — pure internal, a crash, fully diagnosed, ~1 slice; (2) the **hedge dual-store** `intern_denoted`
extension (write-side, proven pattern) validated on a clean banded scenario; (3) THEN the surface bucket
(`X prep Y` grammar coverage) + integration. The engine/reasoning core of the flip is sound (enumeration
guard + coref + banded/`why` + propositional-cause write-side fix); the remaining internal work is the
forward-match guard divergence (schema) and the hedge dual-store, both understood.

---



**⭐ STEP 1 (broaden the validation gate) — DONE 2026-07-22 (suite 970 green). The AGREEMENT HARNESS
`tests/test_grammar_shipped_agreement.py` (9 parametrized scenarios).** The complement to the fixed-answer
gate: each morphology-clean reasoning scenario runs through BOTH routes — shipped (plain KB) and grammar
(`open_class="noun"`) — and asserts (a) the two routes reason IDENTICALLY and (b) both land on the intended
answer (so agreement on a WRONG answer is caught too). Shapes: stored copula fact→yesno, copula-rule
derivation, multi-hop chain, two-premise join across mentions, NAF defeasible + clearance re-break, negative
control, wh-enumeration, banded-over-hedge. This is the gate step 2 validates slice-1c against — assert both
routes still agree AFTER the `denotes` change, not a scratchpad harness.
- **A REAL FINDING while building it (settled, do not re-litigate):** the shipped route recognizes ONLY
  copula (`is`) facts — arbitrary S-V-O (`lion has mane`, `eats`, `likes`, `owns`) is `unrecognized` on the
  shipped `load_facts` path. So S-V-O intake is a grammar-route CAPABILITY, not a shared reasoning shape;
  agreement scenarios use copula facts (an S-V-O yes/no would compare against a route that never stored the
  fact). S-V-O agreement, if wanted, belongs in the grammar-ONLY gate (`test_grammar_route_reasoning.py`),
  not the cross-route harness. (This is why the first draft's `has`-scenario diverged `yes` vs `no
  (assumed)` — not an engine bug.)
- **UNCOMMITTED at this sub-handoff:** `?? tests/test_grammar_shipped_agreement.py` (NEW, 9 green). KEEP.

**NEXT (unchanged order):** step 2 = re-derive slice-1c PROPERLY (the `chain.py` `denotes`-resolution that
fixes propositional-cause node-bound joins) and validate against BOTH grammar gates — it must keep the
agreement harness green (that is where the original slice-1c regression, banded partial-order, would show).
Then step 3 grammar coverage. Full pre-step-1 story below.

---



**ONE-LINE STATE.** The grammar flip-default was re-investigated end-to-end this session; the reasoning
side is essentially SOUND, the remaining work is grammar-coverage + surface-specific integration, and the
STRATEGY PIVOTED to **validation infrastructure FIRST, surface fixes LAST** — the first committed
grammar-route reasoning gate now exists. Full story + every finding: memory
[[flip-default-blocked-by-greedy-grammar]] (read it first) and the RE-MEASURE block just below.

**⚠ WORKING TREE — COMMIT THESE FIRST (staged, `git status`):**
- `?? tests/test_grammar_route_reasoning.py` — NEW, the validation gate (8 tests, all green). KEEP.
- `M ugm/chain.py` — a REVERT (slice-1c backed out to its `0e0e231` state). KEEP the revert.
- `D _flip_plugin.py` — removing a scratchpad harness the prior `e90178c` commit accidentally added at the
  repo root. KEEP the deletion.
- Already committed & KEPT: slice-1a (`ugm/cnl/query.py` enumeration guard, in `e90178c`) and the
  recognizer-hoist (`intake._defers_to_keyword_surface`, in `0e0e231`).

**WHAT LANDED (all 961-green):**
1. **VALIDATION GATE `tests/test_grammar_route_reasoning.py` (8 tests).** Runs core REASONING through the
   grammar route (`open_class="noun"`, the default-grammar config): fact→yesno, copula-rule derivation,
   two-premise join across coreferent mentions, NAF defeasible + clearance re-break, wh-enumeration
   without a surface leak, banded-question-wears-its-band, `why` trace. Gates the exact class of
   regression the 953 shipped suite CANNOT catch (it under-exercises the grammar route).
2. **slice-1a — the wh-enumeration control-node guard** (`query.py`): the crisp no-scope `who` branch
   used raw `match_pats` (no `_guard`); switched to the guarded `_facts_matching` like the scoped/banded
   branches. Killed the empty-named `' P O'` scaffolding leak; `test_what_causes` passes under the flip.
3. **recognizer-hoist** (`intake._defers_to_keyword_surface`): defers keyword-led surfaces + wh-queries to
   their precise recognizers before the greedy `open_class="noun"` grammar can steal them as S-V-O facts.

**WHAT WAS REVERTED & WHY (the key lesson).** slice-1c (a `denotes`-resolution in `chain.py` — the
read-side mirror of `resolve_write_node`, for node-bound joins across the token/entity duality) correctly
fixed propositional-cause but **passed 953-green while REGRESSING grammar-route reasoning** (banded
partial-order), caught only by the scratchpad flip harness. Reverted: bad trade under "surface last", and
unvalidated. THE LESSON drove the pivot: **do not tune hot-path engine code against a scratchpad harness —
build committed grammar-route coverage first.**

**THE REMAINING FLIP WORK (verified categorisation, 51 fails at revert; NOT one clean fix):**
- **Grammar coverage (~9)** — `X prep Y` predicating clause (riddles need it: `rex in yard` doesn't
  assert, so nothing clears), existentials. `.cnl` work. SURFACE = LAST.
- **Surface-specific handler integration (~25, HETEROGENEOUS)** — schema/causal-propagation/counterfactual
  each fail for their OWN grammar-route reason; propositional-cause was the node-bound-join duality
  (slice-1c, reverted). Banded/world/isa_ask are banded-through-grammar. SURFACE-ADJACENT = LAST.
- **Integration (~17)** — intake_forms, intake_act (`SWEEP refused: not a control node` caller fix),
  accretion + harness test rewrites, reconsider. The plan's originals.

**NEXT, IN ORDER (validation-first):**
1. **Broaden the validation gate** — more reasoning shapes, and/or a parametrized shipped-vs-grammar
   *agreement* harness (same corpus, assert both routes reason identically). ONLY THEN touch engine code.
2. With the gate in place, re-derive slice-1c PROPERLY (it fixes a real bug) and validate it against the
   gate, not a harness.
3. Grammar coverage (predicating `X prep Y`) + the integration items — LAST, surface.

**SETTLED THIS SESSION (do not re-litigate):** GC gate → do NOT sweep on the grammar route (traced +
empirical). Corpus-load is NOT broken by the flip (batch path bypasses the grammar). Coref WORKS on the
grammar route (mentions intern to one entity; rule joins compose). Retiring the duality at the source is
REJECTED (violates [[surface-interpretation-split]]). Both fundamental primitives (① scope generalization,
② facts-as-truth-bearers) remain BUILT; the `is a KIND` rule-head bug and propositional-causation surface
are DONE.

---
_Earlier handoff (still valid context) below:_

**⭐⭐ FLIP-DEFAULT RE-MEASURED 2026-07-22 (suite 953 green) — 59 fails not 18, and the real blocker is the
INTERPRETATION/REASONING DUALITY, not integration bookkeeping.** Fresh deterministic harness (loudon
`Grammar` loaded once, `copy.deepcopy` per grammar-less KB — sharing one lets `sync_vocabulary` cross-
pollinate lexicons — auto-`declare_grammar(open_class="noun")`, register-marked to dodge the `id(kb)`-reuse
bug). Memory: [[flip-default-blocked-by-greedy-grammar]].
- **THREE things SETTLED this session:**
  - **GC GATE (gate #1) → do NOT sweep on the grammar route.** Traced + empirically confirmed: the
    revision path `reconsider`→`rebuild`→`mark_all_spans` re-reads the WHOLE standing surface across ALL
    past utterances; `gc_utterance_scaffolding` destroys the `first`/`next` token chain the fold needs, so a
    post-sweep `rebuild` returns `[]` (vs correct facts un-swept). Accretion is the deliberately-accepted
    cost of a permanent revisable surface. The 2 `test_isa_focus` accretion fails get TEST-REWRITTEN.
  - **CORPUS-LOAD FEAR RULED OUT.** `load_world`/`load_corpus` load facts via the batch `_recognize` path
    (bypasses `ingest`/`session_banks`), so only interactive queries hit the grammar — a domain corpus's
    `is cy thief` still answers correctly under the flip.
  - **RECOGNIZER-HOIST BUILT (UNCOMMITTED, shipped stays 953 green): `intake._defers_to_keyword_surface`.**
    A guard before the grammar dispatch that defers keyword-led surfaces (suppose/why/cause/comparison/hedge
    via PURE recognizers) AND wh-queries (`recognize(text).qtype=="who"` — the grammar route hardcodes the
    `("yesno",…)` goal so it CANNOT enumerate `who`/`what`) to the precise recognizers below. Root cause it
    fixes: under `open_class="noun"` (which a default grammar NEEDS) the grammar reads `what causes X` /
    `suppose A : P` / `that A causes that B` / comparatives as plain S-V-O facts, stealing them before their
    recognizers run; the intake comments' "grammar refuses these, reached by fall-through" was MEASURED only
    WITHOUT open_class. Principled (most-specific-wins, as the authoring cluster already is), shipped-safe
    (guard only runs when a grammar is declared). **But it moved the flip only 59→54** — proving the theft
    was NOT the dominant cost.
- **⭐ THE REAL BLOCKER (found once the hoist unblocked wh-enumeration): reasoning over a grammar-route KB
  is POLLUTED because reasoning reads the RAW graph while the grammar KB permanently carries the
  interpretation/surface layer.** Two manifestations: (1) SURFACE control nodes carry CONTENT edges — `what
  causes aggression` enumerated a spurious `' causes aggression'` from two empty-named `ctrl=True`
  interpretation/span artifacts holding a real `causes`→aggression edge (the shipped route never hits this
  because it SWEEPS — forbidden here by the GC gate); (2) interpretation COPIES split a name across 2+ nodes
  (`'dangerous' resolves to 2 distinct nodes; a rule join may silently derive nothing`) — breaks RULE
  reasoning. This is [[interpretation-nodes-are-the-target]] / the token-entity duality, UNSOLVED for the
  query path.
- **⭐ CHEAPEST VIABLE FIX PROBED — REASON OVER A CLEAN PROJECTION of the interpretation.** `gi.facts(kb)`
  (= `scope_facts`) is CLEAN (no surface, one node per name). PROVEN: load `scope_facts` into a scratch
  `AttrGraph` + run `ask_goal` there ⇒ enumeration `what causes aggression` returns exactly
  `[fear…, hunger…]` (no pollution), yesno + rule-join (`is lion dangerous` off `lion is strong` + a rule)
  both correct, `who is dangerous` clean. Solves BOTH manifestations at once (clean single-node-per-name
  graph). **ARC COMPLICATION (the risk):** the recognizer-hoist created a DUAL FACT STORE — crisp grammar
  facts live in the interpretation scope (`gi.facts`), but DEFERRED special surfaces (hedge FORKS,
  comparisons, propositional-cause handles) write to the REAL KB (confirmed: `cy is likely alibied` routes
  `hedge`, absent from `gi.facts`). A clean reasoning view must UNION both, and banded/fork reasoning
  (test_world/isa_ask/contract) needs the fork scopes projected too — that union is the arc's unknown.
- **ARC ESTIMATE (multi-slice, its "own session" as the plan always said):** (a) a `reasoning_projection(kb)`
  helper + route grammar-route yesno/wh/why/suppose/goals through it [moderate, ~1 slice]; (b) UNION the
  deferred/banded facts + fork scopes into the projection [the risky slice — needs its own probe]; (c)
  provenance/`why`, the goal act-loop, and perf (cache + invalidate on ingest) over the projection
  [moderate]; (d) the original ~18 integration items (GC-gate + accretion test rewrites, the
  `SWEEP refused: not a control node` caller fix in `test_intake_act`, authored-forms routing, expectation
  rewrites) [small-moderate]. Current flip debt with the hoist in place: **54 of 953**.

**⭐ SCOPE-KIND UNIFICATION LANDED 2026-07-22 (suite 900 green) — the §4 table is now TRUE IN CODE.**
With the arc's Slices 0–2 complete, the two ontological kind modules (`attribution.py` holder +
`temporal.py` temporal) were near-identical — the same helpers modulo a `(kind, key_attr)` pair and two
policy flags. They are DELETED and consolidated into `ugm/scope_kinds.py`: a kind-parameterized core
(`scope_of` / `pen_scoped` / `holds_in` / `scopes_holding`) plus thin kind-bound verbs. Timely, not
premature: building both as near-copies FIRST is what validated "kind dispatch generalizes with zero
read-engine change," so this extracts a MEASURED axis, not a guessed one. Deferred, deliberately: (a)
the `epistemic` fork is NOT folded in (it carries a band, is discounted, isn't entity-keyed —
`suppose.py`/`possibility.py`); (b) `chain.py`'s `@?t` rule path stays hardcoded `temporal` (ranging
`@?t` over other kinds = the "family-B" arc). Public API deleted, not aliased (engine is experimental,
single owner) — 5 test files re-pointed to `ugm.scope_kinds`, the 40 existing scope tests pass
UNCHANGED (the equivalence proof), + `tests/test_scope_kinds.py` (6) drives the core through a synthetic
third kind with negative controls on kind-dispatch + non-veridicality + materialize.


**⭐ META-PATTERN SURFACE LANDED 2026-07-22 (suite 873 green) — the payoff of the quote token.**
`define schema <trigger> : <template>` lets a user define what a relation-PROPERTY means AS A RULE
TEMPLATE, in the language: `define schema ?r is transitive : ?a ?r ?c when ?a ?r ?b and ?b ?r ?c`, then
`ancestor is transitive` (a plain fact) materialises the transitivity rule for `ancestor` (and the same
schema serves `before`, `symmetric`, …). `cnl/define_surface.compile_schema`/`apply_schemas`, wired on
the intake FACT route (run the meta-bank forward + harvest when a triggering declaration lands —
order-independent, idempotent, `Event("schema")`). Quote-vs-bind principle: a template var in the
TRIGGER is BOUND (the parameter `?r`), one that is not is QUOTED (a var of the written rule). `tests/
test_schema_surface.py` (8). **The in-language replacement for the Python relation-property expanders.**
⚠ Perf: `apply_schemas` runs the meta-bank on every fact when any schema exists (free when none) —
gate on trigger-predicate if it ever bends.


**⭐⭐ SIDE-ARC 2026-07-22: THE QUOTE TOKEN + THE `define` SURFACE (suite 865 green).** From the user's
"define meaning and use it? drastically simplify?" — audit in `design/meaning_surfaces_audit.md`. Two
findings + two builds:
- **"Define meaning and use it" was NOT a missing primitive** (rules = sufficient defs, skolems =
  necessary; both NATIVE). The sprawl is TWO axes: ~13 LOADERS (collapsible — the real simplification,
  NOT yet done) vs per-relation rule GENERATORS (thought quote-wall-bound).
- **⭐ THE QUOTE-WALL WAS ALREADY CLIMBED, and is now removed IN-LANGUAGE.** `learner.py` already writes
  variable-bearing rules; the only thing still walled was the *ergonomic* form (writing `?a` as a
  literal). **Built the QUOTE token `'?a`** (`production_rule` §QUOTE — a leading `'` escapes the
  variable reading; `literal_name`/`Pat.__post_init__` strip it, everything else additive): a meta-rule
  now writes relation-property transitivity in-language, no Python expander (proven,
  `tests/test_quote_token.py`, incl. re-break: bare `?a` → malformed, loud). Delicacy is authoring
  POLICY, not an engine limit (user's framing).
- **Built the `define` surface** (`cnl/define_surface.py`) — `define H as B` (sufficient rule) /
  `define H iff B` (+ the NECESSARY direction: `H ⇒ B` with non-head vars as a SHARED bound-literal
  skolem witness — both directions of meaning from ONE statement). Reuses `load_machine_rules` (no
  second grammar); wired into the MAIN intake as `Outcome("define")` (NOT a new loader — respecting the
  audit). `tests/test_define_surface.py` (10).
- **NEXT for this side-arc (audit §6):** ~~the meta-pattern CNL surface~~ **DONE — see the META-PATTERN
  block above.** REMAINING: **loader convergence** (route comparative/uncertainty through intake, retire
  `load_corpus` — user's "start 2 in a fresh session" item); leave hedges/forks to scope generalization
  (family B). ~~Also still owed from Slice 2: the `@?t` CNL surface.~~ **`@?t` DONE 2026-07-22 (suite 880
  green) — see the Slice 2 block below.**
  - **⭐ LOADER CONVERGENCE DONE 2026-07-22 (suite 886 green) — comparison converged, hedge deferred,
    batch loader reimplemented.**
    - **STEP 1 (comparison):** `x is more/less D than y` routes through `intake.ingest` as an additive
      FALLBACK `Outcome("comparison")` (reusing `parse_comparative`), keyword-gated, above the crisp fact
      route. MEASURED: the canonical grammar refuses it, so nothing is stolen (grammar KB via
      fall-through). An ink relation (transitivity on demand, no `rules` mutation) — SURVIVES later
      fact-path normalization.
    - **⚠ HEDGE tried on intake and REVERTED — a real finding, now ROOT-CAUSED AND FIXED.** A hedge
      authors a banded FORK that read back `assumed-no` after any later fact ingest. FIRST diagnosis
      ("normalize_surface breaks it, family B, wait for scope generalization") was SHALLOW. **Root cause
      (traced 2026-07-22): the fork's `<hypothesis>` scope node is EDGELESS BY DESIGN** — its pencils
      reference it by a `scope` VALUED ATTR, not a graph edge — so the incidental edge-based GC
      (`lowering.final_gc`, which runs whenever a bank carries drops; `AttrGraph.gc_disconnected`) swept
      it as "orphaned scaffolding," a FALSE POSITIVE. **This was NOT hedge-specific: holder AND temporal
      scopes were silently destroyed the same way** (their tests never interleaved a fact after
      authoring). **THE GC FIX LANDED 2026-07-22 (suite 886 green):** exempt `<hypothesis>` nodes from
      both GC passes (`HYPOTHESIS` moved to `vocabulary.py` as the shared low-level constant; scope
      deletion stays owned by `suppose._drop_scope`). Verified across all 3 kinds + `_drop_scope` intact +
      re-break-confirmed; `tests/test_scope_survives_gc.py` (5). This UNBLOCKED hedge-through-intake (see
      below). The DEEPER family-B authoring unification (one kinded primitive; `@?t` ranging over
      epistemic/holder scopes) is separate and unforced.
    - **STEP 2 (batch loader): `load_corpus` is now ingest-in-a-loop** (kept its `(kb, rules)` signature —
      the "reimplement, keep signature" decision — so ~132 call sites untouched). ONE recognition/routing
      path, declare-before-use. Fallout: 2 `test_new_core` tests (inspected rule-source GRAPH internals →
      now the `rules` LIST; one used the Stage-3 loose sugar the ingest path has no route for).
    - **⭐ HEDGE CONVERGED + `load_world` FOLDED 2026-07-22 (suite 894 green):** after the GC fix, the
      hedge intake route (`Outcome("hedge")`) was re-added and `load_world` collapsed to a thin
      `load_corpus` alias — every layer (facts, rules, hedges, either/or, comparisons) now goes through
      the ONE ingest path. The 7 earlier `test_world` failures were purely the GC bug.
    - **⭐ STAGE-3 LOOSE SUBSYSTEM RETIRED 2026-07-22 (suite 894 green):** `load_loose_rules`,
      `parse_lexicon`, `expand_loose`/`expand_loose_from_graph`, `frames_in_graph`, `TRANSLATION_FORMS`,
      `LEXICON_FORMS` deleted + removed from `RULE_SOURCE_FORMS` + 7 `__init__` exports + 2 `test_new_core`
      tests + the `test_isa_runbank` fixture. Dead on the live path once `load_corpus` became
      ingest-in-a-loop; superseded by the prose->CNL layer.
    - `intake.py` §"LOADER CONVERGENCE"; `tests/test_intake_loader_convergence.py` + guard
      (+comparison/hedge surfaces). **THE LOADER-CONVERGENCE SIDE-ARC IS COMPLETE.**


**THE ARC IN ONE PARAGRAPH.** The grammar arc's real question — "are the fundamental epistemic blocks
enough?" — became: are they REASONED-OVER (not just mapped), and CLOSED under composition, at arbitrary
DEPTH? Two probes answered it. `bench/spike_epistemic_closure.py` (clause-3 = reasoned-over, + closure)
found blocks compose closed EXCEPT a verified negative-side leak. `bench/spike_binder.py` decomposed the
shared cross-fact primitive and found: **ranging is NATIVE** (existential = LHS-keyed skolem + demand;
ordered = recursion over relational order), and the ONE critical-path fundamental gap is
**RELATIVIZING a fact to a context** — i.e. **SCOPE GENERALIZATION**, which converges the negative-band
leak, attribution, and tense into ONE extension of the existing scope mechanism. Full reasoning +
inventory: `design/form_inventory.md` §9.1–9.3; engine design: `design/scope_generalization.md`.

**KEY SETTLED CONCLUSIONS (so they are not re-litigated; all in form_inventory §9):**
- **Understanding needs CLAUSE 3 — reasoned-over, not just mapped** (the conditionality "right by luck
  on the token" bug). Closure = every composition lands in {reasoned ∪ explicitly-refused}, never
  {silently mis-mapped}; goal = smallest CLOSED set covering the corpus (closure can force it LARGER).
- **Closure-at-depth ⟺ ONE uniform evaluation mechanism** (cond∘degree PASSES under banded chain_sip;
  degree∘negation LEAKED = two mechanisms).
- **In-scope is a CORE/COMPLETION line INSIDE each block** (agentic, not theorem-proving): tense-core =
  state-transition (not full temporal logic); causation-core = entity-level + SUPPOSE; quantification-
  core = existential-under-uncertainty + universal. Completions are declared ceilings.
- **TWO distinct missing primitives, only ① on the critical path:** ① SCOPE GENERALIZATION
  (relativization; shared by tense-core + attribution + negative-band; an EXTENSION of the scope
  mechanism); ② FACTS-AS-TRUTH-BEARERS — its productive half (propositional-causation C3) is a
  deferrable ceiling, but its RELATING half already exists as PROVENANCE (`proves`/`uses`) and
  explainability rides it, so scoped derivations must go through `record_firing` with scope intact.

**⭐ SLICE 0 LANDED 2026-07-22 (suite 818 green): the negative READ is banded SYMMETRICALLY.**
`check.check` under a banded policy now reads the hard-negative's band (`_band_present`, + runs the
negative closure banded) and returns a banded-negative verdict (`band_word(n) + " not"`, e.g. `likely
not`) instead of collapsing a fork/pencil ¬L to `assumed-no`. This closes the verified band∘negation
leak and establishes the invariant every later scope kind needs ("a scope's relativizer is read on
BOTH polarities"). Guards: `tests/test_possibility_band.py::test_banded_negation_wears_its_degree...`
(+ crisp-path-unchanged), re-breakable. `collapse`/`explain_check` pass the new verdict through as a
band word (verified: `.get(status, status)` + banded fallback).

**⭐ SLICE 1 LANDED 2026-07-22 (suite 831 green): the `holder` scope KIND (attribution).**
The kind-representation fork is DECIDED — a **`kind` valued attr on the scope node**
(`suppose.SCOPE_KIND`, default-absent ⇒ `epistemic`), NOT distinct marker names. Reasons: additive
(joins the `<likeliness>`/`<choice>`/`<derived-env>` attr family on `<hypothesis>`); uniform dispatch
(`suppose.scope_kind` = one attr read); and all the scope machinery (`scope_members`, `all_fork_bands`,
`_drop_scope`) keys on the `SCOPE` tag + `<hypothesis>`-ness, never the marker name, so a holder scope
is penned/swept identically and ONLY the read dispatches on kind.
- **⭐ THE READ IS ALREADY ONTOLOGICAL AND NON-VERIDICAL — probe-confirmed BEFORE building.** A crisp
  `check(scope=holder)` sees the pencil via `_scope_pencils` ⇒ POSITIVE; a global `check` never sees a
  control pencil ⇒ ASSUMED_NO; under banded policy the holder scope carries NO `<likeliness>` so it is
  never discounted (and merges at CERTAIN when active). So Slice 1 was NOT a read-engine change — it is
  the KIND + KEYING + AUTHORING layer (`ugm/attribution.py`): `SCOPE_KIND=holder`, a `<holder>` key
  (one reused scope per party), `consider(g, N, triple)`, `holds_for(g, N, goal)`, `holders_considering`.
- **Acceptance MET:** *N considers the lion a cat* ⇒ `is the lion a cat` → **no globally / yes relative
  to N**. Guards in `tests/test_attribution.py` (11), re-broken on both load-bearing axes: `holds_for`
  not relativizing → the yes vanishes; a holder scope carrying a band → it leaks into the global banded
  read (non-veridicality broken).
- **ADDITIVITY VERIFIED:** existing forks carry no kind attr and dispatch as `epistemic` — no scope was
  retroactively kinded. `KIND_EPISTEMIC` is the read-time default, not a stored value.

**⭐ SLICE 2 PART (a) LANDED 2026-07-22 (suite 840 green): the `temporal` ordered ontological scope.**
`ugm/temporal.py` — the SECOND ontological kind, mirroring attribution exactly (`KIND_TEMPORAL`, keyed
to an index entity by `<temporal-index>`; `at_time` / `holds_at` / `temporal_scope_of` / `order` /
`indices_holding`). Ontological at its index, non-veridical globally, same as holder. The ORDER is
ordinary INK relational content between the index entities (`order` writes `t1 before t2`), traversed by
an ordinary recursive rule (spike O1 — NATIVE, tested). `tests/test_temporal.py` (9), incl. the O2a
unary-state frame axiom ranging natively. **This validated that kind dispatch generalizes past holder
with zero read-engine change** — the same conclusion as Slice 1, now confirmed on a second kind.

**⭐⭐ PART (b) SEMANTICS PROVEN NATIVE — the wall is ONLY the rule language (probe, 2026-07-22).**
Hand-simulated the BINARY-fact frame axiom (`has(x,y)@t1 ∧ t1 before t2 ⇒ has(x,y)@t2` — the O2b wall)
with a Python driver over the scope helpers (`indices_holding` binds the index; the ink `before` read;
`at_time` pens into the later index's scope). It WORKS: `holds_at(t2)` flips assumed-no → positive,
stays non-veridical globally. So the O2b "binary fact is 4-place" wall is DISSOLVED by the scope
encoding — no reification, no 4th S-P-O slot. **The entire remaining gap is expressing this AS A RULE**
(binding the relativizing index/scope as a variable), i.e. the §6 open fork, now the only work left in
Slice 2.

**◆ THE OPEN FORK IS NOW LIVE — scope-variable rule SYNTAX + MATCHING (`scope_generalization.md` §6).**
The probe reframed it: because the scope is KEYED to an ordinary index entity (Slice 1's pattern), the
frame axiom is cleanest RANGED OVER THE INDEX ENTITY, not the scope node — `has(x,y)@?t1 ∧ ?t1 before
?t2 ⇒ has(x,y)@?t2` where `?t` is an ordinary variable and `@?t` says "relativized to the scope keyed
to ?t". So the new mechanism = a per-atom RELATIVIZER (`@?t`): match binds/uses the index like any var
(free ⇒ bind from the matched fact's scope; bound ⇒ resolve to its scope), head pens into the keyed
scope (what `Band` already nearly does). The remaining engine change is per-atom scope resolution in the
body-atom loop (today `scope=` is run-level, `chain.py:~1195`). The fork is which SURFACE + matcher
integration — pending a user decision before build.

**⭐⭐ SLICE 2 PART (b) — SCOPE-VARIABLE RULE ENGINE LANDED 2026-07-22 (suite 848 green): the one
genuinely new mechanism of the whole arc.** User picked the per-atom `@?t` relativizer (general
scope-variable rules) over a built-in closure. A rule ATOM now carries an optional RELATIVIZER
(`Pat.rel`, `@?t`): matched / written RELATIVIZED to the temporal scope KEYED to `?t`. The frame axiom
`has(?x,?y)@?t1 ∧ ?t1 before ?t2 ⇒ has(?x,?y)@?t2` PERSISTS A BINARY FACT across time — the O2b "4-place"
wall, dissolved. `tests/test_scope_variable_rules.py` (8).
- **DEMAND-PATH, additive.** `Pat` gained a `rel` slot (default ""); `write_rule` stores it on the
  atom's pred node (`apply.ATOM_REL`); `apply._read_atoms_rel` reads 4-tuples for the demand chain. In
  `chain._apply_rule_demand`: a relativized BODY atom ranges temporal-scope pencils binding the index
  (`_relativized_matching`, echoing bound endpoints exactly as `_facts_matching` does — the identity bug
  that cost the first debug), a relativized HEAD pens into the scope keyed to its bound index
  (`_scope_for_index`, mint-on-demand), and the head's `?t` binds at seed time to the RUN-LEVEL scope's
  index (a timed fact is non-veridical globally, so it is only derivable relative to a keyed scope).
  `holds_at` now MATERIALIZES the queried index's scope (you must have a context to reason in).
- **KEY DESIGN POINTS (settled):** ranged over the INDEX ENTITY, not the scope node (the probe's
  reframing); un-relativized atoms are wholly unaffected (**848 green, zero hot-path regressions**);
  multi-hop persistence uses a transitive `precedes` (spike O1) — a relativized body atom READS pencils,
  it does not recursively demand them (a direct-`before` axiom persists one hop unless intermediates are
  materialized). Kind fixed at `temporal` for now (head-mint needs a kind); holder-inheritance can reuse
  the machinery with a kind tag later.

**⭐ THE CNL `@?t` SURFACE LANDED 2026-07-22 (suite 880 green) — SLICE 2 IS COMPLETE.** The frame axiom
is now expressible in the language: `?x has ?y @?t2 when ?x has ?y @?t1 and ?t1 before ?t2` folds through
`load_machine_rules` to the exact `Rule` the engine test built by hand (`Pat.rel` on the relativized
atoms), and persists a binary fact across time end-to-end (non-veridical globally). Three edits, all
additive:
- **Tokenize tags the relativizer** (`forms.tokenize`): an `@?t` token gets `is_rel yes` — done at the
  one chokepoint every fold path shares, because the grammar forms match token NAMES and cannot express a
  "starts with `@`" pattern. Ephemeral NAC-guard scaffolding (like `is_kw`/`kw_not`), stripped with the
  `yes` node; inert on every non-rule path (`@` is not CNL content).
- **A relativized clause form on BOTH the shared body and the machine head** (`authoring.
  _GENERIC_BODY_CLAUSE_REL`, `machine_rules._rel_clause`): `S P O @?t` captures the trailing token as
  `k_rel` and carries `body_end`/`head_end` on the RELATIVIZER (not the object), so the `and`/switch
  domino continues past all four tokens. `_cond_pat` strips the leading `@` and reflects it into
  `Pat.rel`.
- **A defer NAC on the plain clauses** (`?co next ?relx ∧ ?relx is_rel yes`) — a separate independent NAC
  group (grouped by the free `?relx`; `_nac_groups` excludes LHS-bound `?co`), so the plain clause yields
  to the relativized one when a relativizer follows. **RE-BREAK CONFIRMED load-bearing:** stripping it
  makes the plain clause ALSO fire, injecting a spurious un-relativized `?x has ?y` copy (rel="") that
  would break non-veridicality. `tests/test_scope_variable_cnl.py` (7).
- **DEFERRED limits (not needed for the acceptance):** a relativized `not` clause (`not S P O @?t`) and a
  relativized PROSE head (`S P O @?t when …` — prose head is single-triple, so it uses `_rel_clause`'s
  machine path). The shared body spine gives prose bodies the relativizer for free.
3. **Independent, off the critical path:** causation's entity-level core is NATIVE now (build on it);
   propositional causation (② C3) is a declared ceiling.

**BENCHES/PROBES ADDED (re-runnable, `PYTHONIOENCODING=utf-8`, deterministic ×2):**
`bench/spike_epistemic_closure.py` (clause-3 + closure; 8 PASS / 3 REFUSED / 1 LEAK — the LEAK is the
INTAKE-side hedge∘negation, not the machine), `bench/spike_binder.py` (E/O/C map: 3 NATIVE capabilities,
2 GAPs = relativization + propositional-causation). Memory: `binding-is-the-missing-axis.md`,
`epistemic-closure-under-composition.md`.

**RELATION TO THE GRAMMAR ARC BELOW:** this arc emerged FROM the grammar/flip-default work (below) and
supersedes it as the current focus, but the flip-default integration work is still valid REMAINING work
— it was not done. Pick this arc up first; the grammar handoff is preserved verbatim below.

## ▶ PICK UP HERE (handoff 2026-07-20 END OF SESSION — suite **818 green**, pystrider **388 green**)

**STATE IN ONE PARAGRAPH.** The grammar route now carries every FORCE as a declared verb
(assert/deny/hedge/ask/goal/command), routes DECLARATIVELY on the force its parse recovered, keeps
its metalanguage (L0) in a register, parses under an ISA control program rather than a Python driver,
and discriminates kind-from-property by the determiner. Step 2 (flip the default) is **measured at 18
failing tests of 818** and is an INTEGRATION slice, not a rewrite — see the triage below.

**⚠ UNCOMMITTED AT HANDOFF — verified against `git status`, not from memory:**
`ugm/cnl/grammar_intake.py`, `ugm/intake.py`, `docs/implementation_plan.md`. That is the
entity-side reconsider wiring plus this handoff. Everything earlier in the session was committed as
it went. `docs/design/inference_inventory.md` (from the `/btw` fork) may still be UNTRACKED — check.
**Re-verify with `git status` rather than trusting this line**: the previous handoff's tree note was
stale and cost a re-check at the start of this session.

**⚠ RUN THE EOL NORMALIZER BEFORE COMMITTING** (`scratchpad/fix_eol.py`, driven off
`git diff --name-only`). Windows editing silently rewrites LF files as CRLF and turns a 400-line diff
into a whole-file rewrite; it bit five files this session.

**NEXT, IN ORDER (all four are step 2's integration work; see the full triage lower down):**
1. **Decide the GC contract** — does the grammar route want `gc_utterance_scaffolding`? Its surface
   is DELIBERATELY permanent (the re-interpretation loop re-reads it), so "sweep the spent token
   chain" may be exactly wrong here. **A decision, not a patch.** Gates ~5 of the 18.
2. **Fix `SWEEP refused: not a control node`** (2 in `test_intake_act`) — the `forget that` GC
   (`gc_cold_scaffolding`) reaches interpretation entities and the guard correctly refuses. Guard
   working, caller wrong.
3. **Decide whether authored forms (`form K : …`) should reach the grammar route** — they extend the
   SHIPPED recognizer only (1 real failure).
4. **Then** rewrite the ~5 expectation tests (they pin the shipped route's LIMITS) and flip.

**THREE STANDING RULES THIS SESSION EARNED — read before measuring anything:**
- **Run a measurement harness TWICE and compare before quoting its number.** Five harness bugs this
  arc; the flip harness was nondeterministic (`id(kb)` reuse) and every number it produced before the
  fix (44/20/19/17) was junk. Only 18 is confirmed.
- **Read ONE failure to its mechanism rather than summarising N.** Sampling misclassified the step-2
  failures three separate times; the full read found ~11 real gaps where the sample said "test
  expectations".
- **A trace that CONFIRMS your current hypothesis is the one to distrust.** Both wrong diagnoses this
  session stopped at the first observation consistent with what was already believed.

**⭐⭐ STEP 1 IS DONE: DECLARATIVE ROUTING + THE `command` FORCE LANDED 2026-07-20.** The router
dispatches on WHICH FORCE THE PARSE RECOVERED, not on position in an ordered if-ladder. Built as one
slice with the COMMAND force, because router-only would have left focus/stance/run in a positional
ladder and made "routing is no longer order-dependent" only half-true.

- **`commands` is the sixth force verb**, one tuple in `_assert_forms`' `(verb, mode)` table plus
  declarations — the fourth time that prediction has held. `iclause` productions in
  `loudon_grammar.cnl` cover `focus on X` / `be cautious` / `run build`; `COMMAND_ACTS`
  (`intake.py`) resolves the imperative WORD to the act, as declared data beside `policy.STANCES`.
  **The grammar says only what it can see** — this is a command, this is its verb — while what each
  verb DOES stays in the module that owns it. No focus/stance/running logic moved into the grammar.
- **`iclause` needs no `suppresses`**, unlike `qclause`/`gclause`: it embeds an np/pp/adj, not a
  whole `clause`, so nothing inside it predicates. Declaring it anyway would put a premise on every
  assert rule for nothing.
- **THE AUTHORING CLUSTER STAYS ABOVE THE DISPATCH — and it is not a compromise.** disable / form /
  procedure / rule must yield a `Rule`, which the fold structurally cannot produce (§4b class (b)).
  MEASURED: the grammar refuses all four surfaces under both `open_class` settings, so this order
  and the reverse agree — which is exactly what makes their position not a routing decision. Pinned
  by `test_the_authoring_cluster_is_refused_by_the_grammar`, which fails loudly if a future grammar
  starts parsing one. This is also what keeps conditionals on the rule route.
- **A REFUSED PARSE FALLS THROUGH** to the remaining recognizers, so a grammar need not declare
  every surface (`forget that` still reaches the shipped focus form). **What it must never reach is
  `load_facts`** — that would write content onto TOKENS and silently reintroduce the duality while
  routing as `fact`. Explicit guard, pinned.
- **MEASURED:** suite 781 → **793 green** (12 new), **pystrider 388 green**, Loudon corpus still
  **19/19, 0 ambiguous, 0 refused** at 107 ms/line. The plan's "expect red" did not materialize, and
  the probe said in advance that it would not.

**⭐ THE PROBE CHANGED THE PLAN TWICE, BEFORE ANY CODE WAS WRITTEN** (method: PROBE BEFORE SCOPING).
1. **The ladder was NOT actually order-dependent** — exactly one recognizer fires on every surface
   tried, with ONE exception (`forget that rule` fires both `disable` and `focus`). So this was an
   architecture fix, not a bug fix; the urgency was lower and the risk lower than the plan assumed.
2. **Hoisting would steal nothing.** I predicted it would break conditionals, since `?x is dangerous
   when ?x is strong` looked parseable under `open_class="noun"`. It is not — `when` is undeclared,
   so the grammar refuses it. **That prediction was wrong and the probe cost two minutes.**

**⭐⭐ TWO LESSON-4 NEAR-MISSES, BOTH CAUGHT BY RE-BREAKING, AND THE SECOND IS THE INSTRUCTIVE ONE.**
Re-break verified on all three axes; two tests passed under the defect they were written for.
1. **The force-routing table could not see its own property.** `focus on lion` yields
   `Outcome("focus")` whether the GRAMMAR or the shipped string recognizer decided, so the obvious
   test was blind to the entire slice. Fixed with a STRUCTURAL discriminator:
   `recognize_focus_op` runs in a SCRATCH graph, so an `iclause` span standing in the KB proves the
   parse decided. Fails the moment the dispatch moves back below the focus recognizer.
2. **⭐ THE INPUT WAS THE TEST.** `test_a_grammar_kb_never_reaches_the_token_fact_route` passed with
   its guard DELETED, because `glorp the flarn quux` is refused by the shipped fact forms too — the
   input could not tell the two paths apart. The discriminating shape is `zork is a cat`: the
   grammar refuses it (undeclared word) while `load_facts` recognizes it perfectly. **A fall-through
   test is only as good as an input the two paths disagree about** — pick the input from the
   DISAGREEMENT, not from what looks unparseable.

**⚠ A TOOLING TRAP THAT COST A REVIEWABLE DIFF, worth knowing about:** editing rewrote
`intake.py`, `grammar.py` and `grammar_intake.py` from LF to CRLF, turning a 414-line diff into a
4,500-line whole-file rewrite. Caught because the stat showed `implementation_plan.md` at 3,589
changed lines when it had not been touched. Normalized back per file against HEAD (never a blanket
conversion). **Check `git diff --stat` against `--ignore-cr-at-eol` before committing on this
repo** — the working tree is LF and Windows editing drifts it.

**⭐⭐ STEP 2's COST MEASURED 2026-07-20 — 44 of 818, and the prerequisite list was WRONG.**
Simulated the flip instead of working through a list written several slices earlier
(`scratchpad/flipdefault.py`, a pytest plugin lazily giving every grammar-less KB the canonical
grammar). **95% of the suite passes with the grammar as the default route.** The failures decompose
into exactly TWO causes, neither of which is on the plan's prerequisite list:

1. **THE `question` EVENT WAS MISSING on the grammar route — a real defect, now FIXED (suite 818).**
   A grammar question streamed `['answer']` where the shipped route streams
   `['question', 'answer']`, so a TUI could not render the question it was answering. Accounted for
   3 failures. Pinned by `test_a_grammar_question_emits_the_question_event_before_the_answer`.
   **Found by simulating the flip, not by reading the code** — the grammar route is exercised by so
   few tests today that an event-level gap sat unnoticed through three slices.
2. **⭐ THE REMAINING 44 WERE A KIND-vs-PROPERTY PREDICATE MISMATCH, and the DETERMINER fixes it:
   44 → 19.** `open_class="noun"` makes a bare post-copula word an np, so the grammar commits and
   asks `is_a` (a KIND) where the shipped route uses `is` (a PROPERTY). English already marks the
   distinction with the DETERMINER (*is a cat* vs *is clean*) and the surface carries it — the
   grammar was discarding it, because `copula plus np` fires whether or not a determiner is present.
   * **THE FIX NEEDS NO NEW CATEGORY:** capture `det` as a slot, percolate it, and guard the
     assertions on its presence — `clause asserts subj is_a kind when det` /
     `clause asserts subj is kind unless det`. The subject's own determiner cannot interfere,
     because a clause takes `det` from its RIGHT child.
   * **⚠ AND IT MUST BE DONE ON THE QUESTION SIDE TOO — that half is 25 of the 44.** The first
     version patched only `clause` and **fixed 0**. `is ada watched` was ASKING
     `('ada','is_a','watched')` while the rule derived `('ada','is','watched')`: the question and the
     assertion must agree on the predicate, or every derived property answers `no (assumed)`. Same
     two lines on `qclause` (+ `det` slots through `qbody`).
   * **⭐ APPLIED to `corpus/loudon_grammar.cnl` 2026-07-20 (suite 818 green, pystrider 388 green).**
     MEASURED on the shipped grammar: **5/5 discrimination, corpus still 19/19 with zero ambiguity,
     flip 44 → 20**, and the question side now AGREES with the assertion side (`bo is cleared` then
     `is bo cleared` → `yes`; `bo is a suspect` then `is bo a suspect` → `yes`).
   * **ONE LINE CORRECTED vs the probe, deliberately.** The probe had
     `slot det in qclause from copula plus np is right head`, which takes the np's HEAD as the
     determiner — always present, so that production would always read KIND. Shipped as
     `is right det`, which is what the guard actually means. **Cost: flip 19 → 20**, with the
     failure mix redistributed (`intake_forms` 4→3, `reconsider` 4→5, `surface_facts` 2→3) rather
     than one clean regression. Taking the semantically-correct line over the one-test-better one;
     the +1 was not chased further, which is recorded rather than hidden.
   * **~~THE REMAINING 19 ARE NOT ARCHITECTURE~~ — WRONG, AND THE FULL TRIAGE PROVED IT.** That
     conclusion came from sampling FIVE of them. **Reading all 20 found ~11 REAL integration gaps.**
     Third time in one day that a sample beat me; see the triage below.

**⚠⚠ THREE DIAGNOSES, TWO WRONG — RECORDED IN FULL BECAUSE THE METHOD LESSON IS THE DELIVERABLE.**
1. "It's adjectives" — from two sampled error strings. **Right about the CONCEPT, incomplete as a
   FIX** (assertions only): 0 of 44.
2. "It's the token/entity name-resolution duality, i.e. `_through_denotation`" — from tracing ONE
   failure. **Wrong**, and it looked authoritative: the rule fires on the entity, the token is
   empty, so a name read "obviously" hits the empty token. **It does not** — `_candidate_nodes`
   returns BOTH nodes and both are fact entities. I stopped the trace one step early, at the fact
   that fit the story.
3. Tracing the QUESTION path — the actual cause, and it was never on the assertion side at all.

**THE RULE THIS YIELDS: a trace that CONFIRMS the current hypothesis is the one to distrust.** Both
wrong diagnoses ended at the first observation consistent with what I already believed. The third
only appeared by asking what the QUESTION resolved to, which no summary of the failures suggested.

**⚠ THE "MIGRATION COST IS ~ZERO ON VOCABULARY" CLAIM: still false as written, but the burden is
NOT per-KB.** It holds for RELATIONS (`sync_vocabulary` derives them). Adjectives were never
declarable on the shipped route — but the determiner discriminator removes that burden entirely
rather than shifting it onto each KB, which is what makes it the right fix rather than a workaround.

**⭐⭐ `parse` IS NOW AN ISA CONTROL PROGRAM 2026-07-20 (suite 818 green, corpus 19/19, 109 ms/line).**
User question: "are we wrestling with homoiconicity / would an ISA program be easier?" The
investigation it triggered is worth more than the change.

- **THE DIAGNOSIS: `parse` was a PYTHON CONTROL DRIVER — a regression against a COMPLETED arc.** It
  sequenced three banks with `if`/`return`/`try-finally`, which is exactly what the ISA control-machine
  arc retired everywhere else (`run_bank`'s fixpoint, `_act_loop`, `dispatch` all became
  `ControlMachine` programs). The grammar arc then reintroduced one. **The banks always ran on the
  machine; only the SEQUENCING did not** — so "2300 lines of Python in the parser" was really ~20
  lines of driver plus a compile-time rule generator.
- **THE THREE-WAY OUTCOME IS NOW A BRANCH, not a `return`**, and **the `finally` became a JOIN BLOCK**
  — every outcome branches to one `RETIRE` block, which is the only thing making `UNPARSED` retire on
  all paths. **RE-BREAK VERIFIED on exactly that axis**: routing the REFUSED exit around the join
  fails `test_unparsed_marks_do_not_survive_a_parse` with the marks still standing. The guard written
  for the Python `finally` transfers to the branch program unchanged — evidence the conversion
  preserved the invariant rather than the syntax.
- **STILL PYTHON: `parse_batch`** — same three banks plus a `try/finally`, but STRAIGHT-LINE (no
  conditionals), so it is sequencing rather than control flow. Low value; listed for completeness.

**⚠⚠ THE INVESTIGATION CORRECTED TWO THINGS IN THIS FILE, AND ONE HAD ALREADY MISLED A DESIGN
DISCUSSION.**
1. **SEMI-NAIVE ROUNDS WERE ALREADY BUILT** (same day, second-lever block) — but `run_bank`'s
   docstring still said *"Naive — no semi-naive delta / df-seeding"*, this file quoted that stale
   sentence as a LIVE root cause, and it was then offered as the argument for building it again.
   Docstring corrected at source. **The day's third instance of trusting a summary over the source.**
2. **SEMI-NAIVE COULD NEVER HAVE RETIRED THE DELTA MARKS** — a CATEGORY ERROR between two kinds of
   incrementality. Semi-naive scopes rounds 2..n WITHIN one `run_bank` call; round 1 still matches the
   whole graph. The marks exist for CROSS-CALL scoping, since `parse` re-runs the banks per utterance
   over a graph holding every earlier sentence and nothing remembers the previous fixpoint.
   **Retiring them needs PERSISTENT cross-call deltas** — real, unbuilt, and the honest target if the
   delta machinery is ever attacked. Value is lower than it looks: the three marks are built, tested
   and guarded; the hazard is mainly a FOURTH one.

**THE ARCHITECTURAL QUESTION, ANSWERED WITH ITS REASONS (so it is not re-litigated).** "Would a
hand-written / ISA parser be easier than grammar-as-rules?"
- **The declared grammar is earning its keep and is NOT the cost.** Hedging landed declarations-only;
  COMMAND was declarations plus one table entry; the determiner discriminator is pure declarations.
  The 2300 lines of bank generation are a FIXED cost, already paid and generic over the grammar — new
  grammar features do not touch them.
- **The real tax was fixpoint semantics** — ~10 silent defects (6 bound-literal/idempotency, 3 delta
  lifecycles, 1 join order) — and its root is the ENGINE, not the formulation. Parsing-as-deduction is
  a known-good technique.
- **The chart does NOT have to be DERIVED by rules to LIVE in the graph.** If a rewrite is ever
  wanted, a purpose-built parser can WRITE the chart and everything downstream (slots, fold,
  re-minting, interpretation) survives untouched — which keeps the option open at low cost.
- **TRIGGERS that would justify it:** parse perf becoming a blocker again, a fourth delta mark, or the
  Rust port (where the plan already says firmware-as-ISA first, then port the interpreter).

**⭐⭐ THE FULL STEP-2 TRIAGE (all 20 read, 2026-07-20) — THE FLIP IS NOT A TEST REWRITE.**
I twice reported these as "test expectations plus vocabulary" from a sample of five. Reading every
one classifies them as:

**⭐ REAL, AND MOSTLY ONE CAUSE (~8): the grammar route's fact branch omits the shipped route's
POST-FACT BOOKKEEPING.** Verified structurally — the whole grammar branch is:
`focus_mod.widen(...)` / `yield Event("fact")` / `return`. The shipped tail additionally does
  * `mark_dirty([fact_grain(kb, n) for n in <nodes minted by this utterance>])` — so a user-asserted
    fact makes a stale NAF conclusion revisable. **Missing ⇒ 5 `test_reconsider` failures**
    (`['yes'] == ['no (assumed)']`, "the fact should have marked its grain"), plus
    `test_isa_intake::test_question_negative` and `test_think_harder`'s crash, which depend on the
    same revision path.
  * `focus_mod.gc_utterance_scaffolding(kb, anchor)` — accretion control. **Missing ⇒ 2
    `test_isa_focus` failures.** ⚠ BUT THIS ONE IS A DESIGN QUESTION, NOT A PATCH: the grammar
    route keeps its surface DELIBERATELY (it is the permanent record the re-interpretation loop
    re-reads), so "sweep the spent token chain" is not obviously wanted here. Decide the contract
    before copying the call.
  * ⚠ AND `mark_dirty` CANNOT BE COPIED VERBATIM: the shipped version selects "nodes not in
    `nodes_before`", the SNAPSHOT PROXY already measured defective on this route (it is what
    `asserts_content` replaced). The entity-side grain needs deriving, not porting.
**REAL, separate (2): `SWEEP refused: nNNN is not a control node`** in `test_intake_act` — the focus
GC (`gc_cold_scaffolding`, the `forget that` path) reaches interpretation entities and the SWEEP
guard correctly refuses. The guard is working; the caller is wrong.
**REAL, separate (1): authored forms do not reach the grammar route** —
`test_intake_forms::test_authored_declarative_form_lands_facts` goes `'unrecognized'` where the
shipped route lands a fact. `form K : …` extends the SHIPPED recognizer only.
**TEST EXPECTATIONS to rewrite (5):** `test_habitability`, `test_intake_act::…nearest_forms`,
`test_intake_forms::{unknown_shape_unrecognized_before_declaration, key_conflict_accepted_replaces}`,
`test_intake_surface_facts::test_undeclared_verb_with_preposition_MIS_PARSES`. All assert
`unrecognized`/a known MIS-PARSE for shapes the grammar legitimately handles — they pin the SHIPPED
route's limits, and the flip makes them false by making the system better.
**VOCABULARY, expected (2):** `alice likes bob` (no `likes`), `this lion is a cat` (no `this`).
**HARNESS ARTIFACT (1):** `test_no_grammar_declared_means_no_banks` — the flip plugin gives every KB
a grammar, so it defeats this test by construction. Not a signal.

**CONSEQUENCE: step 2 is an INTEGRATION slice, not a rewrite slice.** The honest order is: wire
reconsider grains to the entity side → decide the GC contract → decide whether authored forms should
reach the grammar route → then rewrite the 5 expectation tests and flip.

**⭐ STEP ONE OF THAT ORDER IS DONE 2026-07-20 (suite 818 green): RECONSIDER IS WIRED TO THE ENTITY
SIDE — `test_reconsider` 5 → 1, flip 20 → 18.** Corpus still 19/19 at 108 ms/line (was 109).

- **A CONTENT DIFF, NOT A NODE SNAPSHOT, and that is the whole design.** A grain is
  `(predicate, object-NAME)` — content, never identity — so `route` diffs `facts(kb)` around
  `extend` and hands the result to intake as `data["committed"]`. Copying the shipped selector
  ("relations not in `nodes_before`") would have re-imported the proxy this route already measured
  DEFECTIVE, since a re-derived relation is a new node id and any rebuild makes everything look new.
  **The same repair as `asserts_content`, applied to the second reader that leaned on identity.**
- ⚠ COST NOTED, NOT YET A PROBLEM: the diff walks the scope twice per utterance, i.e. O(session) —
  the shape this arc has fought five times. Measured flat so far (108 ms/line on 19 lines); if a long
  session ever bends, derive the grains from the PARSE instead (the declared assertion slots, as
  `force_triple` does) rather than from the fold's output.
- **1 `test_reconsider` failure REMAINS** and has not been diagnosed.

**⚠⚠ AND EVERY EARLIER FLIP NUMBER IN THIS FILE WAS UNRELIABLE — THE HARNESS AGAIN, FIFTH TIME.**
`scratchpad/flipdefault.py` recorded "already tried" in a dict keyed by `id(kb)`, and **CPython
REUSES ids after GC**, so a fresh KB could inherit a dead one's flag and silently never get a
grammar. Symptom: the same file reported 3, 4 and 5 failures across runs, and the totals 44 / 20 /
19 / 17 were all taken with it. Fixed by marking on the KB itself (`kb.registers`); **18 is the first
number confirmed by two identical consecutive runs**, and it is the one to trust.
**THE LESSON HAS NOW EARNED ITS OWN RULE: a measurement harness needs a DETERMINISM CHECK — run it
twice and compare — before any number it produces is quoted.** Every instance this arc
(`clear_fresh`, `mark_tokens`, the relation regex, the L0 parse order, this) was a harness that
silently disagreed with the pipeline it duplicated.

**NEXT, in order:**
1. **Flip the default** (step 2 — cost MEASURED: 44/818, and **19/818 once the determiner
   discriminator is applied to BOTH the assert and the ask side**. The remaining 19 are test
   expectations and lion-grammar vocabulary, not architecture. Apply `scratchpad/probe_det.py`'s
   patch to `corpus/loudon_grammar.cnl` first — it is validated and orthogonal to the flip.) — a KB with no declared grammar gets the canonical one.
   Still owed first: `focus.utterance_subjects`, `authoring.anchor_has_content_fact` (both walk the
   token chain), the book/playground surface, and the 54 `nodes_named` read sites.
   **And the grammar files should converge to ONE canonical file now** — `loudon_grammar.cnl` has
   quietly become it (facts + hedging + questions + goals + commands) while still being named after
   a bench corpus.
2. ~~**The deferred slice: make `disable` vs `focus` structural.**~~ **DONE 2026-07-20 — see below.**
3. **The long tail**: degree adverbs (`very risky`), `every person is a mortal`, PP attachment.

**⭐ THE DEFERRED SLICE LANDED 2026-07-20 (suite 806 green): NO CHECK IN THE ROUTER DEPENDS ON ITS
ORDER ANY MORE.** Split out of the declarative-routing slice deliberately, and the split was the
right call for a reason worth keeping: **the two slices had different blast radii.** Declarative
routing touched only the grammar route, which nothing shipped reaches (`declare_grammar` appears in
6 files, all grammar modules/tests/docs). This one touches `focus.FOCUS_FORMS`, which every KB and
pystrider run through on every utterance. Bundling them would have put the one change that could
break pystrider in the same commit as two that structurally could not.

- **ONE NAC IS THE WHOLE FIX.** `focus.drop` matched `forget ? that ?` with no constraint on what
  FOLLOWS, so it fired on `forget that rule` alongside `rule_control`'s more specific form, and only
  intake's check order picked the winner. Adding `nac=[Pat("that?", "next", "?more")]` — "nothing
  follows `that`" — states exactly what the more specific form's extra token contradicts. The same
  `next`-absence NAC `grammar.SUPPRESS_FORMS` already uses; verified first that `cnl.forms.tokenize`
  appends no end marker, so a final token genuinely has no `next`.
- **THE EXISTING TEST WAS BLIND, which is why a comment was not enough.**
  `test_forget_that_rule_is_not_focus_drop` goes through `ingest`, so it passes whether the forms
  are exclusive or whether LADDER POSITION is silently deciding — re-break confirmed it stays green
  with the NAC removed. The property is only visible at the RECOGNIZER level
  (`test_the_disable_and_focus_forms_are_mutually_exclusive`). **Third lesson-4 near-miss of the
  day; all three were "the test observes an outcome both paths produce".**
- **GENERALIZED INTO A STANDING GUARD:** `test_at_most_one_router_recognizer_claims_a_surface`
  sweeps all 8 router recognizers over one representative surface per route (12 surfaces). That is
  the §D.1 property stated for the whole router rather than for one pair, and it is the thing that
  will catch the next route quietly reintroducing an ordered ladder. It held for every surface
  except `forget that rule` before this fix — i.e. the sweep would have found this defect.

**⭐⭐ FORCE COVERAGE RE-DERIVED 2026-07-20 (`bench/spike_force_coverage.py`) — 80%, AND IT FOUND A
REAL DEFECT.** The §4b claim ("68 utterances, 54%, 25 of 31 failures are force") came from a scratch
probe that no longer existed, so it could not be checked after the force work. Now extracted from
`tests/` rather than hand-listed, because a hand-kept list drifts toward what we know works.

- **61 unique utterances, 40 parsed (66% raw).** By force: **ask 16, assert 13, command 8, goal 3**
  — i.e. **27 of 40 covered utterances are a force that did not exist as a form this morning.**
- **THE RAW NUMBER OVERSTATES THE GAP AND THE HEADLINE UNDERSTATES IT**, so the bench separates
  three things the first run conflated: 7 refusals are BANK AUTHORING (deliberately not in the
  grammar), 4 are DELIBERATE NEGATIVE FIXTURES (gibberish whose refusal is the behaviour under
  test — scoring those as failures penalises the grammar for working). **Against what the language
  is actually meant to say: 40/50 = 80%.**
- **THE NEGATIVE-FIXTURE LIST IS HAND-JUSTIFIED ON PURPOSE.** Nothing in the string separates
  "gibberish by design" from "a construction we cannot yet say", and automating that judgement is
  precisely how a coverage number becomes self-congratulatory.
- **THE HARNESS WAS THE BUG ONCE MORE — THIRD TIME IN THIS ARC** (after `clear_fresh` and
  `mark_tokens`). The relation-vocabulary extractor anchored `$` to end-of-line, but the
  declarations sit INSIDE string literals so a quote follows; it silently matched nothing and the
  vocabulary fix looked ineffective. **Re-check any harness that duplicates a pipeline.**

**⭐⭐⭐ THE DEFECT THE BENCH FOUND — USE vs MENTION, and it BLOCKS STEP 2 (verify before flipping
the default).** Declaring a word as a relation makes the DECLARATION SENTENCE ITSELF unparseable.

- `produces is a relation` **parses while `produces` is unknown and REFUSES once it is a
  `transitive`** — a verb-category word can no longer head an np, so it cannot be a subject.
  `roars is a relation` already refuses today (`roars` is declared intransitive in the grammar
  file); `lion is a relation` parses. **The grammar cannot talk ABOUT its own vocabulary.**
- **MEASURED THROUGH REAL `ingest`, and this is the live consequence: the SAME declaration ingested
  TWICE routes `fact` then `unrecognized`.** `sync_vocabulary` is correct only because it syncs
  AFTER the fold, so the declaration is read while the word is still unknown — the mechanism is
  load-bearing on ORDERING, which nothing states or tests.
- **WHY IT BLOCKS THE FLIP:** `form_authoring` already records that re-declaration is the NORMAL
  case under the multi-KB-file model ("a key re-declared IDENTICALLY is idempotent"). Making the
  grammar the default route makes every corpus's relation declarations subject to this. It is the
  intake-layer twin of the idempotency family this plan has hit five times.
- **NOT FIXED — it is a DESIGN question, not a patch** (a use-mention/quoting form is a new
  fundamental entry, now recorded in `form_inventory.md` §4a). Options not yet weighed: a quoting
  surface, letting a declared word keep its noun reading in subject position, or exempting the
  declaration forms from the grammar route the way the authoring cluster already is.

**⭐⭐⭐ LEVEL IS A THIRD AXIS — HYPOTHESIS CONFIRMED BY PROBE 2026-07-20 (user proposal).** The
question: should parsing/understanding be explicitly LAYERED, from the layer that declares rules and
vocabulary up to the interpretation that uses them — since a language able to express rules has a
META level. Probed before scoping, and it held.

- **THE AXIS.** `form_inventory.md` has CONTENT (*what is claimed*) and FORCE (*what is being done
  with the claim*). LEVEL is a third: **what the claim is ABOUT — the world (L2), the theory (L1),
  or the language itself (L0).** Orthogonal to both, and MEASURED so: `is produces a relation`
  routes as a question (force) about the language (level), i.e. the axes compose.
- **THE FALSIFIABLE TEST, and it passed cleanly:** if the use-mention defect is a LAYER VIOLATION
  rather than a missing form, the non-idempotent surfaces should be exactly the L0 ones. Round-
  tripped 12 surfaces (ingest the same line twice into one KB): **every L1 and L2 surface routes
  identically twice; the ONLY failure is L0 (`produces is a relation` → `fact`, then
  `unrecognized`).** The axis predicts the defect exactly.
- **THE ASSIGNMENT NEVER FAILED** on the 15 surfaces tried. ⚠ Weak evidence — I chose them; an
  adversarial attempt to find an unclassifiable surface has NOT been made and should be.
- **⭐ THE FINDING I DID NOT PREDICT, and it is worse than the use-mention bug because it is
  SILENT: L0 BARELY EXISTS AT INTAKE.** Of four L0 surfaces:
  * `R is a relation` — the only one that WORKS (and the one that breaks on re-declaration).
  * `np expands to noun`, `rarely means 0.15` — **NOT INGESTIBLE.** Loader-only, so a session
    cannot declare a production or a hedge band at all.
  * **`wolf is a noun` — routes `fact` and EXTENDS NOTHING. Measured: `wolf` is absent from the
    lexicon before and after.** A user declaring a word gets a success verdict and an inert fact.
    This is §8's "understanding ≠ parsing" at the META level.
- **⚠ THE SMUGGLING IS BY DESIGN AND LOAD-BEARING, which is what makes the fix a refactor rather
  than a routing tweak.** `forms.declared_relations` reads `R is_a relation` OUT OF THE GRAPH, so
  L0 is deliberately implemented AS L2 and `sync_vocabulary` depends on it. Relocating L0 means
  relocating that read. Also: **the token/entity duality reaches the meta level** — after the
  declaration, `produces` resolves to 2 nodes.
- **CONSEQUENCE FOR `form_inventory.md`:** the `use vs mention` entry added earlier today should be
  RE-DIAGNOSED as a layer violation, not a missing quoting form. Kept for now with this note,
  because the entry's OBSERVATION is right even though its diagnosis was wrong.
- **⚠ THIS BLOCKS STEP 2 MORE FIRMLY THAN THE USE-MENTION NOTE DID.** Flipping the default sends
  every corpus's declarations through the grammar route, where re-declaration is the normal case
  under the multi-KB-file model.
**⭐⭐ OPTION C BUILT 2026-07-20 (user decision; suite 811 green). L0 IS NOW A REGISTER.**
`grammar_intake.VOCABULARY_FORMS` / `recognize_vocabulary` / `VOCABULARY_REGISTER`, routed as the
first thing `route` does, plus a `vocabulary` Outcome kind.

- **TWO INDEPENDENT DESIGN RULES, and re-breaking proved they are separable** (each fixes a
  different defect, which is why the comparison of options B and C turned on the second):
  * **(1) recognized by a FIXED form, never the object grammar** → re-declaration is idempotent.
    Re-break: routing L0 through the parse restores `fact` → `unrecognized`.
  * **(2) stored in a REGISTER, never as graph facts** → no leak, no duality. Re-break: writing the
    fact as well (i.e. option B without scope-filtering) restores BOTH `?y is meta when ?y is a
    relation` firing AND `produces` resolving to two nodes, while idempotency stays fixed.
- **MEASURED:** `produces is a relation` twice → `vocabulary`/`vocabulary` (was `fact`/
  `unrecognized`); 0 nodes named `produces` (was 2); 0 L0 facts in the graph; and the word is usable
  by the very next utterance (`get_beans produces beans` → `fact`). Corpus still **19/19**.
  Force coverage **80% → 86%** (44/51), real gaps 10 → 7.
- **THE FORK IS DELIBERATE AND SCOPED:** only the GRAMMAR route uses the register. The shipped route
  is untouched, because `load_corpus` bypasses intake entirely (`_recognize` over `_ALL_FORMS`) and
  `forms.relation_forms` rebuilds from the graph per batch — so its `R is_a relation` facts must
  stay. `sync_vocabulary` therefore reads the UNION, and the two readers are kept separate so the
  graph half can be retired without touching the register half.
- **⚠ HARNESS TRAP, FOURTH TIME IN THIS ARC** (after `clear_fresh`, `mark_tokens`, the relation
  regex): `spike_force_coverage.py` calls `parse` directly, so it did not know L0 is now recognized
  BEFORE the parse and reported a 4-point coverage DROP that was purely the harness. Fixed by
  mirroring `route`'s L0 check. **A harness that duplicates a pipeline must be re-checked every time
  the pipeline gains a step — this is now a standing rule, not an observation.**
- **PYSTRIDER 388 GREEN on this slice** — no fix needed. The prediction (it touches `grammar_intake`
  and one `intake` branch, neither of which pystrider reaches) held, and is now a measurement rather
  than an argument.
- **⭐ THE LEXICON NO-OP FIXED 2026-07-20 (suite 817 green), immediately after** — `wolf is a noun`
  routed `fact` and extended NOTHING, i.e. a success verdict plus an inert fact. The worst of the
  L0 defects because it was SILENT rather than refused, and it became visibly inconsistent the
  moment `produces is a relation` started returning `vocabulary`.
  * ONE form covers the family: `W is a K` with the kind BOUND, not literal. `resolve_vocabulary`
    then asks the LIVE GRAMMAR (`vocabulary_categories` = production categories ∪ lexicon values)
    whether `K` names a category — data, never a keyword list.
  * **⚠ THE RISK IT INTRODUCED, and why the grammar check is load-bearing:** a bound kind makes the
    form fire on EVERY bare `W is a K`, including ordinary facts. **Re-break verified — drop the
    category check and `ada is a suspect` silently becomes a lexicon declaration committing no
    fact.** The SHAPE match is not the decision; the grammar is.
  * MEASURED: `wolf is a noun` / `snarls is a intransitive` → `vocabulary` + lexicon entry, and
    `the wolf snarls` then lands `('wolf','snarls','true')`. `lion is a cat` / `ada is a suspect`
    still route `fact`. Corpus 19/19; force coverage 46/54 (85%), `vocabulary` now 10 utterances.
- **⭐ SETTLED (user, 2026-07-20): A SESSION MUST NOT EXTEND THE GRAMMAR STRUCTURE AT RUNTIME.**
  So L0 has THREE tiers, not two, and the runtime line is **structure vs vocabulary** — NOT
  schema vs instances, which is how this plan and `form_inventory.md` first drew it and is wrong
  (a production is an instance of the schema and still must not grow).
  * **schema** (what kinds of declaration exist) — Python, never grows.
  * **structure** (which productions/slots/force verbs the language has) — grammar file, load-time
    only. **Frozen at runtime by decision.**
  * **vocabulary** (which words are in which category) — grammar file OR live session. Grows.
  * **THE REASONS, recorded because the behaviour previously had none:** (1) TRANSLATOR STABILITY —
    new vocabulary does not change the language's SHAPE, so an SLM needs no re-briefing; a new
    production does. (2) AMBIGUITY BLAST RADIUS — a new word can only create ambiguity in sentences
    containing THAT word, while a new production can make sentences ambiguous that contain no new
    token at all, and ambiguity here is detected but deliberately never auto-resolved.
  * **ZERO WORK — verified, not assumed.** `np expands to noun`, `slot … is only head`,
    `clause asserts …`, `qclause asks …` all route `unrecognized`, and `load_kb` RAISES naming the
    line. The decision ratifies the status quo; what changed is that it now has a stated reason.
    "It happens not to work" is not the same as "it must not work."
- **⚠ THE ONE INCONSISTENCY THE DECISION EXPOSES: hedge bands.** `rarely means 0.15` is VOCABULARY
  by the tiering above (a word and the degree it denotes — no production, no shape change), so it
  SHOULD be runtime-declarable; it currently routes `unrecognized`, i.e. is treated as structure.
  Cheap to move if wanted (`sync_vocabulary` already recompiles, which is what a new band needs
  since the fold takes the band as a compile-time constant). Flagged, not decided.
- **⭐ OPTION D IS DROPPED, and that is a RESULT rather than a deferral** (user challenge: "why do we
  have option D as next? I thought we chose C"). Both of its justifications died under checking:
  * **"It makes `sync_vocabulary`'s ordering explicit"** — killed by C itself. L0 is now recognized
    by a fixed form BEFORE the parse, so the declaration cannot be affected by what it declares, in
    any order. The ordering it was meant to expose no longer exists.
  * **"The grammar route is order-dependent where the shipped route is not"** — measured TRUE
    (declaration-after-use: `load_corpus` derives the fact, the grammar route loses it) but
    MIS-FRAMED as a regression. **`load_kb`'s docstring makes declare-before-use the DELIBERATE
    contract** — "a line using a form that arrives later is unrecognized … there is no whole-file
    re-offer fixpoint" — with a LOUD WALL behind it (`load_kb` raises, naming the line and the
    nearest forms). D would have contradicted a settled decision, not fixed a defect.
  * **The real residue is an inconsistency worth NAMING, not fixing here:** two batch loaders with
    different contracts — `load_corpus` (legacy, whole-batch, 2-pass `_recognize`) vs `load_kb`
    (intake, declare-before-use). That is a convergence question for the step-2 flip, not a bug.
  * **LESSON: "complementary, do it anyway" is where unjustified work hides.** D survived two
    review passes as a parenthetical because nobody asked it to justify itself; one direct challenge
    killed it in two checks.

- **~~THE OPEN DECISION~~ (settled — C):** where do L0 declarations LIVE? (a) graph facts in a
  control/meta scope — smallest change, fixes the duality, keeps `declared_relations`' read shape;
  (b) a register beside `forms`/`policy`/`grammar` — cleanest separation, `sync_vocabulary` must
  change; (c) an L0 recognizer in the authoring cluster writing to a register — matches the cluster
  precedent exactly and is the recommendation, since that cluster is already "utterances that do
  not describe the world".
- Probe: `scratchpad/probe_levels.py`.

**⚠ THE EOL TRAP BIT AGAIN, TWICE MORE** (`focus.py`, `rule_control.py`). The normalizer now reads
`git diff --name-only` instead of a hand-kept path list, so it covers whatever was touched:
`scratchpad/fix_eol.py`. **Run it before every commit on this repo.**

**⚠ TWO MEASUREMENT-INFRASTRUCTURE GAPS, both found by trying to re-measure and worth fixing before
step 2 — a claim you cannot re-run is a claim you cannot defend.**

1. **`bench/coverage_audit.py` is BROKEN (pre-existing):** it calls `h.lint_rules`, which does not
   exist in `ugm` (the name appears only in `consistency_design.md` and the bench itself);
   `h.stratify` beside it does exist. ⚠ **AND IT IS NOT THE CNL BENCH** — I first recorded it here
   as blocking the §4b coverage figure, which was WRONG and is corrected rather than deleted: it
   audits CODE bug-detection rule coverage for the ugm-for-code arc (resource/collection hazards,
   miss taxonomy). Unrelated to forms. Fixing it belongs to that project, not this one.
2. ~~**⭐ THE 54% FORCE-COVERAGE FIGURE IS NOT REPRODUCIBLE.**~~ **FIXED — `bench/spike_force_coverage.py`
   now re-derives it, and it found a REAL DEFECT on its first honest run (see below).** `form_inventory.md` §4b states "over
   the 68 unique CNL utterances the repo's own tests actually ingest, a canonical grammar covers 37
   (54%), and 25 of the 31 failures are force" — and **no checked-in bench produces it.** It came
   from a scratch probe that is gone. That number is the whole justification for the force arc, so
   it is exactly the one that should be re-runnable now that ASK/GOAL/COMMAND have all landed. **A
   small `bench/spike_force_coverage.py` re-deriving it is the natural first task of step 2**, and
   would say concretely how much of the 31 the three force slices actually closed.

## ▶ PREVIOUS HANDOFF (2026-07-20 evening, suite 781 green)

**THE ARC IS NOW "THE GRAMMAR SUBSUMES CNL".** Read `design/form_inventory.md` §4 FIRST — it gained a
second AXIS today (CONTENT vs FORCE) and is the spec the remaining work follows.

**WHERE IT STANDS.**
- **FORCE is a form, not a route, for the whole fact tail.** ASSERT/DENY/HEDGE/ASK/GOAL are declared
  verbs; COMMAND/RETRACT/NORM already work ABOVE the fork and are not gaps.
  **SUPERSEDED 2026-07-20 (see the current handoff): COMMAND became a declared verb too.** The
  "not a gap" call was right about RETRACT/NORM and wrong about COMMAND — moving it onto the
  grammar is what let routing stop being positional for focus/stance/run.
- **Migration cost of making the grammar the default is ~ZERO on vocabulary** — `sync_vocabulary`
  DERIVES the grammar lexicon from a KB's existing `R is a relation` declarations.
- **Performance is no longer the blocker**: 237 → **135 ms/utt**, suite 156 s → **51 s**,
  `load_grammar` 1402 → **13 ms warm**. pystrider (the only client) **388 green** throughout.

**~~⚠ WORKING TREE: UNCOMMITTED~~ — STALE, and it was stale when read.** Everything listed here had
in fact landed in `3e387e6 wip grammar`; only `docs/implementation_plan.md` was actually modified.
**Verify with `git status` rather than trusting a handoff's tree note** — a warning that outlives
its commit costs a re-check every session.

**NEXT, in order (staging settled with the user):**
1. ~~**DECLARATIVE ROUTING — the payoff, and the riskiest thing left.**~~ **DONE 2026-07-20 — see
   the current handoff.** Landed together with the COMMAND force. The two predictions in this item
   were both wrong in the safe direction: it did NOT go red (781 → 793, pystrider 388 throughout),
   because nothing shipped declares a grammar, and the ordered ladder turned out not to be
   order-dependent in practice except for one pair.
2. **Flip the default** — a KB with no declared grammar gets the canonical one. Still owed first:
   `focus.utterance_subjects`, `authoring.anchor_has_content_fact` (both walk the token chain), the
   book/playground surface, and the 54 `nodes_named` read sites (currently harmless by ABSENCE, not
   by redirect).
3. **The long tail**: degree adverbs (`very risky` — the hedging family again, 5 of 7 corpus
   refusals), `every person is a mortal`, PP attachment.

**METHOD THAT PAID ALL DAY, and the reason to keep it:** PROBE BEFORE SCOPING. Gap sizing from
intuition was wrong ~6 times today and right once; the probe is cheap and changed the plan every
time. Twice the MEASUREMENT HARNESS was itself the bug (a predicate extractor that declared `ada` a
verb; a core grammar that stripped the verbs) — re-check a harness that duplicates a pipeline.
And **RE-BREAK EVERY TEST on its intended axis**: the DENY collapse's behavioural tests both passed
under the defect, and only the rule-COUNT test caught it.

**WHAT THIS SESSION DID, newest first** (each has its own dated block below, with measurements):

1. **Incremental interpretation** — `extend`/`rebuild` split on a second delta mark (`unfolded`).
   interpret 0.93 → 0.52 s and FLAT (0.014 s/utterance late in a session).
2. **Order-independence measured, and a REAL defect found** — facts were order-independent all
   along, but `route`'s fact/unrecognized VERDICT disagreed in 22 of 24 orders and was wrong in both
   directions. Fixed by asking the PARSE (`asserts_content`), not a node-id snapshot.
3. **`extend ≡ rebuild` proven** — the gate on all of the above. Blocked by two LATENT idempotency
   defects that discard-first had been silently paying for.
4. **RHS variable predicates** (`MINT.key_reg`) — `assert_bank` 133 → 33 rules. First slice of the
   learning arc's `predicates-are-keys`.
5. **Parse tree materialized** (`decomposition_bank`) — slot stage 17×.
6. **The monotonicity claim DROPPED** (user decision) — docs now say "no fact-relation deletion
   WITHIN a pass"; `EMIT` VALUED documented as a destructive overwrite; versioning is opt-in KB data.

**NEXT, in order:**

- ~~**Commit**, then the token delta on `chart`/`ambiguity`~~ **BOTH DONE 2026-07-20 — see the
  fifth-lever block below.** And re-measuring paid AGAIN (fourth time): the stated lever was wrong
  in two ways at once. `span_bank` was NOT delta-seeded as claimed and had the steepest curve of
  all; and the biggest remaining stage afterwards turned out to be a JOIN-ORDER defect, not a
  seeding one.
- **⚠ FIRST, READ THE RAW-PROSE RESULT BELOW (2026-07-20) — it re-points the arc.** The grammar
  scores **0/50 on verbatim book prose** and the gap is 100% constructional, not clerical. Two
  roadmap items are measured as not-viable-as-stated. Decide the scope question there before
  spending anything on step 5 or on more coverage.
- **Step 5** — retire what the fork subsumes (`ugm/intake.py:461` still forks; `has_content_fact` is
  kept only for snapshot-passing callers and is marked as defective).
- **The DENY collapse** — 26 of `assert_bank`'s remaining 33 rules; needs the positive/negative
  pairing as graph data (`w -[neg_of]-> w_not`) so the rule BINDS the negative instead of computing
  a string. Vocabulary change, not a lowering one; would take the bank to ~8.

**FOUR SILENT-FAILURE LESSONS FROM THIS SESSION — read before touching the fold:**

1. **A `<…>`-named premise turns a fact-writing rule into a control-writing one** (vision §5,
   working as designed). Cost: the whole fold produced ZERO facts while every rule fired correctly.
   A delta mark consumed by fact-writing rules needs a PLAIN name + `SURFACE_PREDS` membership.
2. **Discard-first HIDES non-idempotency.** A bank only ever run over freshly-discarded state can be
   non-idempotent for years without a symptom; the discard is paying the bill. Two surfaced the
   instant the scope was kept.
3. **A delta mark's CLEARING is load-bearing and its absence is silent** — everything stays correct,
   the seed set just grows until the optimization undoes itself. Every delta needs a test asserting
   the marks do not outlive their phase.
4. **Re-break every parity test.** The first `extend ≡ rebuild` test passed for the WRONG REASON —
   its corpus derived no contradiction, so the defect it existed to catch was never exercised.

**Where the new code is:** `ugm/cnl/grammar_intake.py` (the forked route, `extend`/`rebuild`,
`reconsider`, `asserts_content`/`asserting_categories`, loud `declare_grammar`), `ugm/cnl/grammar.py`
(`decomposition_bank` + `_prod_key`, `FRESH`/`UNINTERPRETED` marks + `clear_fresh`/
`clear_uninterpreted`/`mark_all_spans`, `mintable_slots` / `remint_mark_bank` /
`reinterpretation_slots`, the span rule's idempotency NAC), `ugm/interpretation.py` (idempotent
`interpret_mentions` + `contradiction_bank`, delta-led `HEAD_BRIDGE`, `discard_scope` re-marking),
`ugm/machine.py` + `ugm/lowering.py` (`MINT.key_reg` + LHS-bound RHS predicate variables), the fork
block at `ugm/intake.py:461`.

**Tests worth knowing about:** `tests/test_grammar_intake.py` (21 — incl. the order-permutation
sweep over both readings, `extend ≡ rebuild`, the minted-subkind verdict, and the two
`declare_grammar` loudness tests), `tests/test_grammar.py` (27 — incl.
`test_parse_banks_are_idempotent`, `test_decompositions_tile_their_parent`,
`test_fresh_marks_do_not_survive_a_parse`, `test_the_fresh_delta_skips_no_work`),
`tests/test_isa_lowering.py` (the dynamic-key MINT trio).

**STEP 2 LANDED 2026-07-19 AS OPTION (b), VIA A DELIBERATE FORK.** User decision: option (a)'s
direct fold was rejected as a target because it entrenches the token/entity duality —
**the target is interpretation nodes**, and "going red for a while" plus duplicated intake paths is
acceptable to get there. Built:

- `ugm/cnl/grammar_intake.py` — the grammar route. `declare_grammar` parks compiled banks in
  `kb.registers["grammar"]` (mechanism state, beside `forms`/`policy`); `route()` runs
  parse → `live_scope` → `interpretation.interpret`, so **facts land on ENTITY nodes reached by
  `denotes`, never on the tokens**. ONE live scope per session (`registers["interpretation"]`) —
  enforcing a single live interpretation is what keeps branch selection out.
- **Entity-aware counterparts of the three duality-dependent readers**, written beside the
  originals rather than as edits to them: `denotata` (the `denotes` hop), `has_content_fact`
  (counterpart of `authoring.anchor_has_content_fact`), `utterance_centers` (counterpart of
  `focus.utterance_subjects`, rendering centers via `describe` so a minted subkind enters focus by
  its DESCRIPTION — it has no name).
- **The fork point** is one block at `ugm/intake.py:461`, routed by the declared register (§D.1, no
  string sniff). Questions, rules, focus moves, forms and procedures are UNTOUCHED and shared by
  both paths. Declare-before-use means the suite stayed green by construction — **the fork cost 0
  failures**, since no KB in the repo declares a grammar yet.
- **`Outcome("ambiguous")` is a new kind** (not a flavour of `unrecognized`): "I cannot parse this"
  and "I parsed it two ways" want different responses, and only the second becomes a discriminating
  question. An ambiguous utterance commits NOTHING (pinned by test) where today's bank writes three
  wrong facts.
- `tests/test_grammar_intake.py` (15) pins the contract: fact-on-entity-not-token, surface survives
  `discard_scope`, the exception sentence lands as `has_not`, refused ≠ ambiguous, and a KB with no
  grammar is unaffected.

**SLICE 3 (THE REVISION LOOP) DONE 2026-07-19 (suite 721 green).** `grammar_intake.reconsider`.
The design question below DISSOLVED: the answer is not "declare alternative readings" but
**evidence-driven re-minting** — the contradiction itself says where to re-read.

- **THE DISCRIMINATOR** (user's framing, and the key architectural point): one derived contradiction
  is the same signal for two faults in different layers — "you merged two entities" (a JUDGEMENT:
  defeasible, session-scoped, discardable) vs "your rule needs an exception" (KNOWLEDGE: structural,
  persists across sessions). The support tells them apart: if the contradicted entity was
  interpreted from >1 surface mention, a coreference judgement is load-bearing → re-interpret. If
  not, `reconsider` returns `RULE` and touches NOTHING — that case belongs to the learning arc's
  defeasible-exception model (§7.3), not here. **Try the revisable thing first, because being wrong
  about it is free.**
- **Mechanism, all in rules:** `remint_mark_bank` marks the spans a contradiction implicates (it
  re-derives the contradiction condition inline, like `contradiction_bank`, since the
  `<contradiction>` node has no stable identity to match on); `reinterpretation_slots` percolates
  everywhere EXCEPT a marked span and mints there instead (NAC / premise on the same marker, so a
  re-interpretation is still ONE reading, never a branch). `mintable_slots` derives WHERE minting is
  meaningful from the grammar's own declarations — a `head`-slot whose category asserts a
  description built from another slot of the same production — never from category names.
- **Result on the real case** (`bengal`/`guzerat`/bare `lion`): 1 contradiction → `REVISED`, 0
  remaining, and the facts are `<is bengal & is_a lion> has mane`, `<is guzerat & is_a lion> has_not
  mane`, **`lion has mane`**. The bare mention stays unsplit because it heads no mintable production
  — which is exactly what makes minting evidence-driven rather than the unconditional (and for a
  non-restrictive modifier, wrong) move a declared `mint` grammar makes. This closes the plan's open
  item "restrictive vs non-restrictive modification" by a route it did not anticipate.
- Marks live on SPANS (surface), so they survive the discard that clears the entities: a re-minting
  judgement is DURABLE and every later utterance is read under it.

**BUGS FOUND BUILDING IT.**
1. **`discard_scope` leaked one orphan `member` rel per member** — `remove_node` does not clean up a
   node's INCOMING relations. The operation the whole architecture rests on being free was quietly
   not discarding. (Then I broke it worse: reading `scope_members` AFTER unlinking them discarded
   NOTHING — snapshot membership first. That regression, not any name collision, is what made a
   3-sentence session stop terminating.)
2. **`route` accumulated interpretations instead of replacing one** — 3 sentences produced 5
   duplicate contradiction markers. One live interpretation means exactly one, rebuilt.
3. **A bound-literal marker mints a fresh node per firing**, so the mint rule matched once per mark
   and minted an entity for each (35 marks, 5× node blowup). The mark is a flag: it must be a PLAIN
   literal, which the lowering interns graph-wide.
4. **⭐ `span_bank` WAS NOT IDEMPOTENT — a pre-existing shipped defect (integration step 1) that made
   session-long surface accretion QUADRATIC.** `<span>?` is a BOUND literal: named, but minted FRESH
   per firing. `parse` runs every bank over the WHOLE graph, so each utterance re-minted all of the
   session's earlier spans — re-running the banks on an UNCHANGED graph added 52 nodes every time,
   and parsing one sentence five times grew the graph by 104, 149, 201, 253, 305. Fixed with a
   self-guarding NAC ("unless a span with this cat/begin/end already stands"); accretion is now FLAT
   at 97/sentence. This is the structural counterpart of `intern_described`, which fixes exactly
   this re-minting for minted ENTITIES — same defect, other layer. Pinned by
   `test_parse_banks_are_idempotent`. **GENERAL LESSON, alongside the `load_facts` one: a bank that
   runs over the whole graph must be IDEMPOTENT, or repetition is quadratic by construction.**

**MEASURED AFTER THE FIXES** (3-sentence session): route `0.23 / 0.60 / 1.07 s` (was 0.21 / 1.14 /
4.41 — 4.1× on the third), `reconsider` **0.91 s** (was 6.65 — 7.3×), graph 508 nodes (was 1497),
suite 97 s → 63 s. Interpretation now shows ZERO leak across repeated interpret/discard cycles.

**A CORRECTION, RECORDED BECAUSE THE WRONG VERSION WAS BRIEFLY WRITTEN DOWN HERE.** This plan
claimed a second bug: "a standing interpretation makes the next `parse` explode, because the chart
keys on NAMES and `interpret_mentions` mints entities carrying their token's name". **That is
FALSE.** Measured: parsing with a live interpretation costs 0.06 s and the chart does not grow — the
lexicon rules require `?t next ?u` and entity nodes have no `next`, so they cannot match. The
apparent explosion was bug 1 (nothing was being discarded, so interpretations piled up). The
`route`-discards-before-parsing layering built on that false premise has been REMOVED; results and
timings are identical without it.

**Consequence for the token/entity partition question (user, 2026-07-19):** distinguishing discourse
tokens from interpretation nodes would NOT have helped performance, because the bug motivating it
does not exist. The epistemic split may still be right on other grounds (`surface_interpretation.md`
argues observation-vs-inference decides membership unambiguously, unlike the engineering strata a
`<stratum>` tag was rejected for) — but it should be decided on those grounds, NOT sold as a perf
fix. The real perf lever was idempotency.

**Still owed:** `route` calls `parse` (not `parse_batch`) and `interpret` re-reads the WHOLE standing
surface per utterance, so cost is still linear-per-utterance = quadratic per session. Now that
discarding before parsing is gone, the incremental path is open: keep the scope and interpret only
the new spans, re-interpreting wholesale only when a contradiction demands it.

**STEP 4, FIRST LEVER LANDED 2026-07-19 (suite 723 green): THE PARSE TREE IS MATERIALIZED.**
Measured first, and the measurement redirected the work twice — record this, because the plan's
stated priorities were wrong in a specific, repeatable way.

- **What the 8-sentence session actually cost:** `parse` 0.66 s / `interpret` 10.75 s. So
  **`parse_batch` — the lever this section owed — is 6% of the problem**, and `interpret` is 94%.
  One level down, `interpret`'s five whole-graph banks split **88.5% slots**, 11% asserts, and
  ~0% for the other three.
- **The fix** (the "materialize the parse tree" lever below, confirmed still dominant): a new
  `decomposition_bank` reifies ONE `<dec>` node per (parent, children) decomposition, and every
  slot rule now seeds on a `dprod` literal and does two pointer hops instead of redoing the same
  9-premise `cat`/`begin`/`end` join. `_production_lhs` is the single chokepoint, so `slot_bank`,
  `remint_mark_bank` and `reinterpretation_slots` all got it at once.
- **A REIFIED decomposition node, not flat `kidl`/`kidr` edges** — the chart is PACKED, so one span
  can carry several decompositions, and two flat edge sets would let the left child of one reading
  pair with the right child of another and feed a slot from a tree that was never parsed. Pinned by
  `test_decompositions_tile_their_parent`.
- The bank runs in `parse` (it is SURFACE — spans and their tree, no denotation) and is
  **idempotent by NAC**, the `span_bank` lesson applied one layer up.
- **MEASURED:** slot stage 9.39 → 0.54 s (**17×**), interpret 10.75 → 1.67 s (**6.4×**), session
  11.41 → 3.11 s (**3.7×**), suite 66.7 → 53.1 s. Work moved INTO parse (0.66 → 1.44 s), which is
  the right trade: derived once per decomposition instead of 32 times per interpretation.

**WHERE THE COST SITS NOW** (re-measure again before the next lever — that is twice this section's
stated priority has been wrong):
- `parse` **1.44 s (46%)**, now the steeper curve: `decomposition_bank` still runs its 9-premise
  join over the WHOLE standing surface every utterance. Idempotent, so it accretes nothing — but it
  still pays the match. This is the natural landing site for the incremental fix, and the cost is
  now concentrated in ONE bank instead of smeared across 32 slot rules.
- `interpret` **1.67 s (54%)**, now dominated by **`asserts` (1.02 s, 63% of interpretation)** —
  which is lever (2) below (86 rules only because a slot-valued predicate expands per lexicon word;
  RHS variable predicates take it to ~6, and the LEARNING ARC WANTS THE SAME PRIMITIVE).
- So the ordering from here is: **(a) RHS variable predicates** (biggest single stage, and shared
  with the learning arc), then **(b) incremental surface** (the remaining curve, both banks).

**STEP 4, SECOND LEVER LANDED 2026-07-19 (suite 728 green): RHS VARIABLE PREDICATES.** The
`predicates-are-keys` primitive the learning arc also wants, built as its first slice.

- **`MINT` gained `key_reg`** — a DYNAMIC PREDICATE for a reified relation, the same mechanism
  `EMIT` already had. The mechanism existing on `EMIT` but not `MINT` is the whole reason this was
  blocked: a fact head is a MINTED rel node, so `EMIT`'s dynamic key could not reach it.
  **`dedup` resolves the dynamic key too** — without that, a variable-predicate rule mints a fresh
  rel node per firing and never reaches a fixpoint (the accretion `dedup` exists to prevent, back
  through the door). Pinned by `test_a_dynamic_key_head_still_dedups`.
- **`lower_rhs` now accepts an LHS-BOUND predicate variable** and still rejects an RHS-ONLY one:
  with no LHS binding there is no node to take a name from, and inventing one is predicate
  INVENTION — the rest of `predicates-are-keys`, deliberately NOT smuggled in through the lowering.
- **`assert_bank` 133 rules → 33.** A slot-valued predicate no longer expands per lexicon word.
- **DENY still expands** (26 of the remaining 33 rules): its head is `neg_pred(?w)`, a STRING
  derivation from the matched word, and the ISA has no string ops. Collapsing it needs the
  positive/negative pairing to exist as GRAPH DATA (`w -[neg_of]-> w_not`) so the rule can BIND the
  negative instead of computing it — a vocabulary change, not a lowering one. Cheap and worth doing;
  it would take the bank to ~8.
- **MEASURED:** asserts stage 1.02 → 0.28 s (**3.6×**), interpret 1.67 → 1.03 s, session
  3.11 → 2.50 s. **Cumulative across both levers: 11.41 → 2.50 s (4.6×)**, suite 97 → 52 s.

**STEP 4, THIRD LEVER LANDED 2026-07-19 (suite 730 green): THE INCREMENTAL SURFACE DELTA.**
Re-measured first, as promised, and this time the inference held: within `parse`, `spans+decs` was
71.5%, `ambiguity` 19.2%, `chart` 9.3%.

- **⚠ THE QUOTE BELOW WENT STALE AND THEN MISLED A DESIGN DISCUSSION (2026-07-20).** Semi-naive
  rounds LANDED later the same day (see the second-lever block), but `run_bank`'s docstring still
  carried the old "Naive" sentence, so this file kept quoting it as a LIVE root cause — and it was
  duly repeated as the argument for building something already built. Docstring now corrected at
  source. **AND THE DEEPER POINT, which survives: semi-naive is WITHIN-CALL only.** It scopes rounds
  2..n; round 1 still matches the whole graph. The delta marks exist for CROSS-CALL scoping, which no
  engine feature provides — so semi-naive never could have retired them, and any claim that it would
  is a category error between the two kinds of incrementality.
- **The root cause is one documented sentence in `run_bank`: "Naive — no semi-naive delta /
  df-seeding (correctness-first)."** Every bank re-matches every rule against the whole graph on
  every call. And `lower_conj` seeds each rule from its FIRST pattern, so leading a decomposition
  rule with `?p cat np` seeded EVERY span in the session and then joined. The NAC stopped the
  re-MINT but not the re-JOIN — which is why the idempotency fix made accretion flat without making
  the cost flat.
- **The fix is a DELTA carried as declared rule structure, not an engine change.** `span_bank` now
  also marks each span it mints with `<fresh>` (its NAC means that is exactly the new sentence's
  spans), and every `decomposition_bank` rule LEADS with `?p <fresh> ?fr` so the seed set is the new
  sentence rather than the session. This is the semi-naive delta `run_bank` does not have, obtained
  without touching `run_bank`.
- **SOUND because a span never crosses a sentence** — spans are bounded by `begin`/`end` within one
  token chain, so a new span's decomposition can only involve spans of the same sentence, which are
  fresh too. Pinned by `test_the_fresh_delta_skips_no_work` (a sentence must materialize the same
  tree parsed alone or as the third utterance of a session).
- **`clear_fresh` is LOAD-BEARING and its absence is SILENT** — leave the marks standing and every
  answer is still correct, the seed set just grows with the session and the optimization undoes
  itself. Observed accidentally while measuring (stage went 0.51 s back to 1.55 s in a profiling
  harness that omitted the call). Guarded by `test_fresh_marks_do_not_survive_a_parse`. It is
  O(marked) via the key index, never a graph sweep — a sweep would reintroduce exactly the
  per-utterance whole-graph cost it exists to remove.
- **MEASURED:** spans+decs 1.38 → 0.51 s (**2.7×**), parse 1.48 → 0.87 s, session 2.50 → 1.80 s.

**CUMULATIVE ACROSS THE THREE LEVERS: session 11.41 → 1.80 s (6.3×), suite 97 → 54 s.**

**WHERE IT SITS NOW — roughly balanced, no single dominant stage:**
- `parse` **0.87 s (48%)**: spans+decs 0.51, **`ambiguity` 0.36 (now comparable, and NOT delta-
  scoped)**, chart 0.18. The obvious next lever is extending the same delta to chart + ambiguity —
  their rules are per-sentence local by the same argument, but they write onto TOKENS, so the mark
  goes on the new sentence's tokens (available in `parse` before the banks run) rather than on
  spans. Should be quick and would take ~30% off the session.
- `interpret` **0.93 s (52%)**: slots 0.52, asserts 0.26. Needs the real incremental-interpretation
  design — keep the scope, interpret only new spans, re-interpret wholesale only when a
  contradiction demands it. NOTE the "this is cross-sentence so the delta cannot apply" claim was
  WRONG (see below): the expensive stages are anchored on a single span and the genuinely
  cross-sentence pieces (`interpret_mentions`, `intern_described`, `contradiction_bank`) measured at
  7% of the stage. The blocker is not cross-sentence-ness, it is that `reinterpret` unconditionally
  DISCARDS, so nothing is ever "already done".

**ORDER INDEPENDENCE MEASURED 2026-07-19 — and it found a REAL defect, not the predicted one
(suite 733 green).** User challenge: "if two sentences speak about the same thing, their order
should not matter." Swept all 24 orders of a 4-sentence corpus, under BOTH readings (percolate and
mint).

- **The FACTS are order-independent — 0 disagreements in all 48 runs.** Every design argument in the
  thread about description-key drift breaking `intern_described` was WRONG: the two `african lion`
  mentions intern cleanly even when one has already acquired `is strong`, because `interpret` stages
  all defining assertions before interning and `route` always rebuilds. Recorded because the wrong
  version was argued at length.
- **The ROUTING VERDICT was order-dependent in 22 of 24 orders**, and wrong in both directions —
  the quietly-does-something-wrong class. `route` asked `has_content_fact(since=<pre-utterance node
  ids>)`:
  * **False negative:** `denotata` reaches entities by the `denotes` hop from tokens, so a MINTED
    subkind — which hangs off the span's `head` slot and is reachable from NO token — is invisible.
    `the african lion has a mane` wrote three facts and returned `unrecognized`.
  * **False positive / the order dependence:** `lion` IS in that sentence's denotata, so once any
    earlier utterance gave `lion` a fact, the same sentence reports `fact` for someone else's
    content. The `since` snapshot does not filter it because **`reinterpret` re-mints the whole
    interpretation every utterance — a re-derived relation is a NEW NODE ID, so rebuild makes
    everything look new.**
- **FIXED by asking a structural question instead of an identity one** (`grammar_intake.
  asserts_content`): does this utterance's parse contain a span in a category that DECLARES a
  predication (`asserting_categories` = exactly `assert_bank(defining=False)`'s selection, read off
  the same declarations)? That reads the SURFACE and the GRAMMAR only, never enters the
  interpretation layer, and so cannot be perturbed by rebuilding or by what other sentences said.
  Order-independent by construction, and it routes by WHICH FORMS FIRED rather than by inspecting
  results (§D.1). 48/48 agree after the fix, and the mint reading now reports `fact` correctly.
- **KEY LESSON, and the reason this belongs in the plan:** node-identity stability was doing
  load-bearing semantic work it should never have carried (user's question: "is node identity really
  important, or only something we need to make the system testable?" — the answer was neither; it
  was a proxy for a question that has a direct structural answer). **Grep intake for other
  `since=`/snapshot-diff verdicts — the same proxy is likely used elsewhere.**
- Guard: `test_interpretation_does_not_depend_on_utterance_order` (parametrized over both readings,
  trimmed to 3 sentences / 6 orders for suite time) + `test_a_minted_subkind_is_reported_as_a_fact`.
  RE-BREAK VERIFIED: restoring the old verdict fails both; reverting passes.
- **Consequence for extend mode:** the earlier framing here — that extend RISKS introducing order
  dependence — was backwards. Rebuild caused the order dependence that existed. After the fix the
  verdict no longer depends on identity at all, which is the better outcome: the semantics stopped
  caring about the optimization.
- **`authoring.anchor_has_content_fact` (the shipped-path original of the same snapshot proxy) is
  CLEAN — checked, not assumed.** 0 disagreements over its permutations, and the trap its docstring
  names (`whether bo is a suspect` after `bo is a suspect`) correctly returns `unrecognized`. The
  defect really was specific to discard-and-rebuild: with nothing deleted, `MINT(dedup=True)` reuses
  the existing rel node on re-derivation, so identity stays stable and `since` means what it says.

**EXTEND ≡ REBUILD: THE SEMANTIC GATE IS GREEN AND PINNED (2026-07-19, suite 734).** Before building
any delta machinery, the semantic question was isolated from the performance one: what happens if we
simply STOP DISCARDING? Answer: the FACTS were identical immediately — but three utterances gave
**5 contradiction markers instead of 1 and 872 nodes instead of 612**. That is the plan's own
"bug 2", and it was NOT a reason extend is unsound. Both causes were **latent idempotency defects
that discard-first was silently paying for**:

- **`contradiction_bank`'s `<contradiction>?` is a BOUND literal** — minted fresh per firing, so
  re-running the bank duplicated the marker. THE FOURTH MEMBER OF THIS FAMILY (`<span>?`, the remint
  mark, `intern_described`, this). Fixed with a self-guarding NAC.
- **`interpret_mentions` called `add_node(name)` unconditionally**, minting a parallel entity per
  name on every pass, and re-wiring every `denotes`/`interprets` edge. Now find-or-create against
  the scope's existing members.

Both fixed AT THE SOURCE, so the equivalence is a property of the banks rather than of a test
harness. After the fixes: same facts, same 1 contradiction, same 612 nodes. Pinned by
`test_extending_the_scope_equals_rebuilding_it`, **re-break verified on BOTH halves** (removing
either fix fails it) and pointed at `CONTRA` rather than `ORDER_CORPUS` — the first version passed
for the wrong reason because its corpus derives no contradiction at all.

**GENERAL LESSON, and the reason this took four instances to see: discard-first HIDES
non-idempotency.** A bank that is re-run over surviving state must be idempotent; a bank that is
only ever run over freshly-discarded state can be non-idempotent for years without a symptom. Every
such defect is a bill the discard was paying. Expect more of them the moment any other scope stops
being torn down.

**INCREMENTAL INTERPRETATION LANDED 2026-07-19 (suite 734 green).** The fold is seeded on a second
delta mark, `UNINTERPRETED` (`unfolded`), written by `span_bank` beside `FRESH`.

- **TWO marks, not one, because the LIFECYCLES differ:** `FRESH` dies at the end of `parse` (its
  consumer, `decomposition_bank`, is done); `unfolded` must survive into `interpret` and dies there.
  Sharing one would couple the phases and make `parse` unusable standalone. Both are written by the
  same rule at the same instant, so nothing is derived twice — only retired twice.
- **`extend` / `rebuild` split** in `grammar_intake`: `route` extends (fold what is marked),
  `reconsider` rebuilds (discard, `mark_all_spans`, fold). **Expressed in the SAME vocabulary** — the
  two paths run identical banks and differ only in how much they mark, so they cannot drift apart.
  `reinterpret` stays as an alias for `rebuild`.
- **`discard_scope` re-marks every span**, so the invariant is self-maintaining: discarding
  invalidates the whole fold, and a caller that forgot to re-mark would make the next `interpret` a
  SILENT no-op.
- **MEASURED:** interpret **0.93 → 0.52 s**, and the CURVE IS FLAT — later sentences cost
  0.014-0.016 s against 0.109 s for sentence 4, i.e. proportional to the new sentence rather than to
  the session. Session **1.80 → 1.39 s**. Validated on the full 8-sentence session: extend and
  rebuild give identical facts and identical contradiction counts (extend has 15 FEWER nodes —
  rebuild's repeated discard leaves orphans; extend is the cleaner path, not the lossy one).

**CUMULATIVE ACROSS ALL FOUR LEVERS: session 11.41 → 1.39 s (8.2×).** (Fifth lever 2026-07-20 below;
its numbers are on a different 8-sentence corpus, so compare within that block, not against these.)

**TWO DEFECTS FOUND BUILDING IT, both silent, both worth remembering:**

1. **⭐ A `<…>`-NAMED PREMISE TURNS A FACT-WRITING RULE INTO A CONTROL-WRITING ONE.** The mark was
   first called `<uninterpreted>`; `_rule_touches_control` then flagged every fold rule, so
   `lower_rhs` minted every head with `control=True` and `scope_facts` filtered them all out —
   **the fold produced ZERO facts while every rule fired correctly.** This is vision §5 working as
   designed (a rule gated by a control token produces control-layer output); the lesson is that the
   `<…>` convention is LOAD-BEARING and a delta mark consumed by fact-writing rules must have a
   PLAIN name. Renamed to `unfolded` and added to `SURFACE_PREDS` beside `cat`/`begin`/`end`, which
   is exactly the precedent (surface scaffolding with plain names, skipped by readers).
2. **`remint_mark_bank` must NOT be delta-seeded.** It shares `_production_lhs` with the fold, but it
   runs AFTER `interpret` has retired the marks and has to find contradiction sites anywhere in the
   session. Delta-seeding made it match nothing — silently, with `reconsider` reporting ASK forever
   instead of REVISED. `_production_lhs(delta=False)` is the whole-graph variant.

**WHERE IT SITS NOW:** `parse` **0.87 s (63%)** is the remaining curve — `chart` and `ambiguity` are
still whole-graph per utterance (`spans+decs` is already delta-seeded). Same treatment applies: their
rules are per-sentence local, but they write onto TOKENS, so the mark goes on the new sentence's
tokens. `interpret` **0.52 s (37%)** and flat.

**STEP 4, FIFTH LEVER LANDED 2026-07-20 (suite 736 green): THE TOKEN DELTA + A JOIN-ORDER FIX.**
Re-measured first, and the measurement corrected the plan's own prescription TWICE. Session on an
8-sentence corpus **2.68 → 1.42 s**, `parse` **1.89 → 0.72 s (2.6×)**, and EVERY parse stage is now
flat in session length (it was the only remaining curve).

- **`UNPARSED` (`unparsed`), the THIRD delta mark**, on the new sentence's TOKENS. `FRESH` and
  `UNINTERPRETED` hang on span nodes, so they can only seed banks that run once spans exist; the
  three banks that BUILD spans (`chart_bank`, `ambiguity_bank`, `span_bank`) had no span to seed
  from. Written by `mark_tokens` right after `tokenize`, retired by `clear_unparsed`.
- **THE PLAN'S STATED LEVER WAS WRONG AGAIN, in a new way: `span_bank` was never delta-seeded.**
  This file asserted "`spans+decs` is already delta-seeded" — only `decomposition_bank` was.
  `span_bank` had the STEEPEST curve of all four stages (4.3 → 179 ms over 7 sentences, 42×). Its
  idempotency NAC (integration step 1's fix) stopped the re-MINT but never the re-JOIN, so it
  accreted nothing while paying session-wide match cost every utterance. **Idempotency makes
  ACCRETION flat; only a delta makes COST flat** — they are different fixes and the first one
  reads like the second.
- **⭐ AND THE SECOND HALF WAS NOT A DELTA PROBLEM AT ALL — IT WAS JOIN ORDER.** After the token
  delta, `decomposition_bank` was still growing (27.7 → 86 ms) and had become the LARGEST stage,
  despite having been delta-seeded since the third lever. Cause: `lower_conj` drives a join from a
  BOUND endpoint and, with neither endpoint bound, SEEDs the whole predicate class — so a child
  premise led by `?l cat np` seeded EVERY `cat` node in the session and filtered afterwards.
  Reaching the child from the boundary token instead (`?l begin ?a`, a FOLLOW from the already-bound
  `?a`) starts from the handful of spans at that position. Same fix in `span_bank`'s NAC.
  **The conjunction is IDENTICAL either way — this is join order, not semantics**, which is exactly
  what makes it invisible in review and easy to regress. Stage 0.37 → 0.17 s and flat.
- **A THIRD LESSON ABOUT THE SEED, ALONGSIDE THE OTHER TWO:** a bank can be idempotent AND
  delta-seeded and still be quadratic, if its premise order throws the seed away on the next join.
  Worth grepping the other generated banks for a premise led by a category/predicate literal with
  no bound endpoint.
- **`_retire_mark` now deletes via the gated `SWEEP` opcode** instead of raw `remove_node` — the
  lowering-compliance path every other scaffolding-retiring driver (`focus`, `dispatch`,
  `possibility`) already uses. Not box-ticking: `SWEEP` REFUSES a fact or provenance node, so a
  delta mark landing where it should not now fails LOUDLY. Covers all three marks at one chokepoint.
- **Guards, per this section's own lessons 3 and 4:**
  `test_unparsed_marks_do_not_survive_a_parse` (the NEW trap this mark has and the other two do not:
  `UNPARSED` is written BEFORE the banks run and `parse` can return REFUSED/AMBIGUOUS from the
  middle, so it must clear on EVERY exit path — hence the `finally`) and
  `test_the_token_delta_skips_no_work`. **RE-BREAK VERIFIED ON THE INTENDED AXIS FOR BOTH** — and
  the second one's first re-break was a lesson-4 near-miss: under-marking made it fail at the
  STANDALONE baseline, i.e. for a reason every other test already catches. Re-broken instead as
  "seed only the session's first sentence", which leaves the baseline passing and fails on the
  session-vs-alone property the test actually exists for.
- **A measurement-harness trap, the same one this section recorded for `clear_fresh`:** the
  profiling harness reimplements `parse`'s body, so it did not call `mark_tokens` and reported every
  sentence REFUSED at 0.012 s — i.e. "a 100× speedup". A harness that duplicates a pipeline must be
  re-checked against it whenever the pipeline gains a step.

**⭐ RAW-PROSE MEASUREMENT 2026-07-20 — THE GRAMMAR SCORES 0/50 ON THE ACTUAL BOOK, AND THE GAP IS
100% CONSTRUCTIONAL** (`bench/spike_loudon_prose.py`). The arc's headline number ("19/19, 100%
parsed, first pass") was always measured on **the 19 CNL lines an LLM produced from the 50
sentences** — the caveat was recorded but kept getting dropped. This runs the same grammar on the
VERBATIM text, which the arc had deferred since 2026-07-18.

- **0/50 as printed. 0/50 de-punctuated. 0/50 with the vocabulary wall lifted entirely**
  (`open_class="noun"`). So the decomposition this bench was built to produce came back DEGENERATE:
  the tokenizer contributes NOTHING (whitespace-only splitting was the suspected culprit and is
  not), the lexicon contributes NOTHING, and **the entire gap is construction**.
- **It is not a near miss, and that is the decision-changing part.** The chart is built even when
  the parse fails, so the longest constituent it derives is a distance metric: **mean 13% of the
  sentence, best case 31% (4 tokens of 13), and ZERO sentences within 80% of a full span.** The
  grammar builds 3-4 token fragments inside 13-22 token sentences. 80% of prose tokens are outside
  the 26-word declared lexicon; median sentence is 29 tokens against a CNL median of 5.
- **CONSEQUENCE 1 — growing `loudon_grammar.cnl` toward prose is not an incremental path.** Real
  prose here is subordination, coordination, quoted speech, passives, relatives and possessives, all
  at once, in nearly every sentence.
- **⭐ CONSEQUENCE 2 — FORM LEARNING BY ALIGNMENT (§7.1 / slice S2b) IS NOT THE ROUTE TO PROSE.**
  Alignment mints a form by matching an unrecognized utterance against the structure its rephrasing
  produced. At 13% coverage **there is no structure to align against**. S2b may still be right for
  CNL-adjacent input; it cannot get from here to books. This matters because S2b was queued as
  exactly that bridge — building it first and discovering this would have been expensive.
- **WHAT THE ARCHITECTURE ALREADY SAYS, and the scope question to settle.** The NL→CNL boundary is
  ALREADY assigned to an SLM in the Phase 8 client design, and `loudon_lion_corpus.py` is that step
  done by hand. Read that way the run is not a failure — it says the LLM translation is
  **LOAD-BEARING, not scaffolding to be removed**, and the grammar's real value is what it does ON
  the CNL: refusing cleanly instead of writing three wrong facts, detecting ambiguity instead of
  guessing, landing the linguistically-marked EXCEPTION (`has no mane`) a form bank drops, and
  supporting contradiction-driven re-interpretation. **Those were the things biasing the learner
  (§10a), and they are fixed.** OPEN, AND A USER DECISION: does "learn by reading books" mean raw
  prose in, or CNL-from-an-LLM in? Everything downstream (S2b's value, whether coverage work is
  worth anything, what the exit gate for the learning arc even is) hangs on it. **Do not answer it
  by building.**

**⭐⭐⭐ FOUNDATIONAL, AND IT NOW HAS ITS OWN DOC: `design/form_inventory.md` (user, 2026-07-20).**
A construction is either **BAROQUE** (ornamental variation on a commitment the substrate can already
hold — unbounded) or **EPISTEMICALLY FUNDAMENTAL** (a KIND of commitment it cannot hold — small and
roughly enumerable). Test: can it be paraphrased into existing forms WITHOUT CHANGING WHAT THE
SYSTEM BELIEVES? This is why "minimum form set + LLM translator" is viable rather than wishful (the
translator absorbs the unbounded half); it is the SAME line as "learning surface is verifiable,
learning semantics is not", reached independently from epistemology; and it predicts cost (a
fundamental form is cheap iff a substrate mechanism already exists — hedging landed in a day because
the possibilistic layer existed; tense would not). The doc carries the TYPED INVENTORY and the
four-outcome translation contract that generates it. **Read it before adding to any grammar file.**

**⭐⭐ THE RE-POINT THIS PRODUCED (user decision, 2026-07-20): THE TARGET IS A MINIMUM FORM SET, NOT
FORM LEARNING.** Settled in conversation after the 0/50 result. `"learn by reading books"` means
**CNL-from-an-LLM in** — raw prose is NOT the intake target and never needs to parse.

- **THE GOAL: a minimum set of forms adequate to represent the concepts, plus a CNL-encoded grammar
  saying how they COMPOSE.** An LLM/SLM translates prose into that set. Parsing coverage of English
  is not a target and never was the useful measurement.
- **WHY THIS IS FORCED, not merely convenient: a learnable form set is in tension with a stable
  translation target.** If forms can be invented at runtime the SLM does not know them; if it does
  not know them it cannot translate into them; so a runtime-invented form is useless for reading
  books. The target language must be FIXED AND KNOWN for a translator to aim at it.
- **COMPOSITION IS WHY A MINIMUM SET IS VIABLE AT ALL** — and it is why the CNL grammar beats a flat
  form bank, for a reason better than elegance: a form bank scales LINEARLY in sentence shapes (one
  form per shape), a grammar scales COMBINATORIALLY (productions compose). Bounded form set,
  unbounded sentences. The homoiconic grammar arc already built this; its value is here, not in
  prose coverage.
- **"CAVEMAN CNL" IS THE FORM SET ITSELF** (user, correcting this plan's first draft of the
  re-point): the caveman SPEAKS these forms. `learning_design.md` §7.1's tiers survive, but their
  STATUS inverts — read them against the new architecture, not as a learning ladder:
  * **T1 (alias — new surface, EXISTING semantics) = THE SYNTACTIC SUGAR LAYER. Survives and is
    PROMOTED.** §7.1 records "adds no expressive power" as a limitation the design must not overstate.
    **Under this architecture that is precisely the SAFETY PROPERTY**: sugar desugars to core, so it
    is meaning-preserving BY CONSTRUCTION and a learned sugar form is CHECKABLE (does it produce the
    same graph structure as the core form it aliases?). **This is where "learning variations of
    forms" legitimately survives** — learning SURFACE is verifiable, learning SEMANTICS is not.
  * **T2 (authored — new semantics, no learning) = HOW THE CORE SET GROWS.** Deliberate, human,
    already shipped (`form KEY : HEAD when BODY`). This is the mechanism for adding the three
    missing constructions below.
  * **T3 (induced semantics from a rephrasing) = THE DISPLACED ONE.** It mints semantics at runtime
    that no translator knows and nothing can check — exactly the tension above. Already ruled out as
    the route to prose by the 13%-coverage result (nothing to align against). Not deleted; parked
    with its reason.
- **SUGAR HELPS THE SLM, BUT MUST EARN ITS PLACE EMPIRICALLY.** It shortens the distance between
  prose and target (fewer translation errors, fewer spurious refusals) while adding no
  expressiveness — so it cannot enable silent approximation. But every sugar form is surface the SLM
  must know. Criterion: a sugar form is justified when it MEASURABLY reduces translation error or
  refusal rate, never speculatively.
- **⚠ THE FAILURE MODE MOVES TO THE TRANSLATOR, AND IT IS THE ORIGINAL ONE.** §10a's finding was
  that partial intake systematically drops EXCEPTIONS because exceptions are linguistically marked.
  A parser lacking a form REFUSES — loudly, countably. **An LLM lacking a form does not refuse; it
  paraphrases into the nearest available form.** The output parses cleanly, the bias is identical,
  and it is now INVISIBLE ("...without any mane" → `the guzerat lion is a lion`, exception gone, no
  trace). **CONTRACT: the translator must be able to say "I cannot say this in this language."**
  `bench/loudon_lion_corpus.py`'s protocol — every sentence yields CNL OR a recorded reason, never
  silence — is a human doing exactly this, and should become the boundary contract. This makes
  minimality a SAFETY property: every missing form is a place the translator quietly approximates.
- **THE STOPPING CRITERION (or "minimal" degenerates into bikeshedding):** the form set is adequate
  when a corpus audit yields ZERO "we had no form for it" reasons. Falsifiable, not a taste call.
- **AND IT MUST BE CORPUS-DERIVED, NOT DESIGNED A PRIORI.** The audit below found 3 real gaps and
  DISPROVED 2 suspected ones. Designing from intuition would have gotten both wrong.

**THE AUDIT — THE FIRST ENTRIES IN THE CONCEPT INVENTORY (2026-07-20).** Classified the 37
untranslated Loudon sentences by their recorded `reason-if-empty`, then probed each candidate gap
with vocabulary added, to separate FORM gaps from LEXICON/convention gaps:

- **~31 of 37 are "the source asserts nothing extractable"** — anecdote, quoted narrative,
  bibliographic, about hunters rather than lions. A property of the SOURCE (§10a's 26% finding), not
  of the form set. Nothing to fix.
- **NOT gaps, though they looked like them** (both parse once the words are declared):
  `the mane is thick` (a property of a PART — a translation CONVENTION that facts are about animals,
  not an expressiveness limit) and `the captive lion has a mane` (`captive lion` is modifier+np,
  identical to `african lion`, and the existing minting handles it as a subkind).
  `the mane is a part of the lion` comes back AMBIGUOUS — the form exists, the PP attachment is
  flagged rather than guessed, which is the grammar working as designed.
- **~6 sentences are real expressiveness failures, needing THREE constructions:**
  1. **HEDGING / FREQUENCY** (`the lion sometimes has a mane`) — sentences 8, 12, 13, 18, 24, 37.
     **The most frequent gap, and the cheapest: UGM ALREADY HAS THE SEMANTICS** (the possibilistic
     banded layer, θ dial, defeasible-guess — arc complete 2026-07-16). The gap is PURELY the CNL
     surface. Note the naive fix is wrong: declaring `generally` a modifier parses but asserts
     `lion is generally` — it needs a real adverbial slot.
  2. **ATTRIBUTION / clausal complement** (`some naturalists consider the lion a cat`) — 8, 23.
  3. **CONDITIONAL / subordination** (`the lion is dangerous when the lion is hungry`) — 18.
- **CONSEQUENCE FOR THE LEARNING ARC: §7.3 IS UNBLOCKED.** Rule learning (S5/S6 built; §7.3 rule
  revision, the defeasible-exception model, promotion by survival) was blocked on intake for DATA,
  not for mechanism. The intake fix landed. That half is the actual goal and is now the live work.
  **S2c (the discriminating question) survives and is promoted** — it serves the rule half plus
  ambiguity resolution, independent of form learning.
- **CONSEQUENCE FOR THE GRAMMAR FILES:** `corpus/lion_grammar.cnl` and `corpus/loudon_grammar.cnl`
  are per-corpus BENCH artifacts today. Under this framing they should converge to ONE canonical
  grammar that IS the specification of the target language — versioned, normative, and the thing the
  SLM prompt is written against. Nothing in the repo treats either as normative yet.
- Evidence: `bench/spike_loudon_prose.py` (the 0/50 run + the audit probes).

**HEDGING SLICE 1 (THE GRAMMAR HALF) DONE 2026-07-20 (suite 738 green).** First entry of the concept
inventory built. `corpus/loudon_grammar.cnl` gains a `hedge` closed class (`generally`/`usually`/
`sometimes`/`occasionally`) and three productions: `hvp expands to hedge plus vp`, `hclause expands
to np plus hvp`, `clause expands to hclause`.

- **A hedged clause is its OWN CATEGORY, and that is the load-bearing choice.** `clause asserts subj
  pred obj` structurally cannot fire on an `hclause`, so a hedged sentence **commits no ink**
  — correct, because ink means CERTAIN and `generally` is a claim about a band. `clause expands to
  hclause` only makes it root-reachable and percolates NO slots. **Declarations only, no Python.**
- **19/19 CNL corpus baseline preserved, no ambiguity introduced** (the new productions need a hedge
  token, which no existing corpus line has). Hedged sentences parse and expose
  `subj`/`pred`/`obj`/`hedge` on the span; pinned by `test_a_hedged_clause_parses_and_commits_no_ink`
  (which also checks the unhedged counterpart still writes its fact — the new category stole nothing)
  and `test_the_hedge_word_is_recoverable_from_the_parse`.
- **Parsed-with-no-fact is the HONEST intermediate state, not a silent drop** — `route` still reports
  the utterance. Refusing it would be §10a's exception-dropping failure in another costume.

**SLICE 2a LANDED 2026-07-20 — OPTION B CHOSEN (user): RULES CAN NOW AUTHOR A BANDED FORK
(suite 742 green).** "Expanding what rules can do" rather than adding a Python driver. Two
primitives, both in the established shape (rule expressiveness grows by a DECLARED structure the
lowering executes — never by sniffing a Pat):

- **`production_rule.Band`** — a declared RHS EFFECT beside `GradedCondition`/`ValueMatch`/
  `Distinct`: write a GRADED attribute at a fixed degree on an RHS node, and optionally PEN named
  RHS relations behind it as a scope. A triple-only RHS could not write a graded attribute at all,
  which is why the whole possibilistic representation was unreachable from rules.
- **`EMIT.value_reg`** — dynamic VALUE (the node id in a register), symmetric with the existing
  `key_reg`, because a scope tag points at a node minted by the SAME firing and so has no
  compile-time id. VALUED-only, guarded: a node id is data, never a degree.
- **THE ACCEPTANCE CRITERION WAS PARITY, NOT "a band appears"** — the rule must land the SAME
  representation `possibility.add_fork` does, so the banded readers cannot tell them apart. Verified
  identical (bands, `possibility`, reader output) against the Python path; a parallel-but-different
  encoding would have been worse than no feature. Pinned by `test_a_rule_can_author_a_banded_fork`
  and `test_a_penned_head_is_control_and_scope_tagged`.
- **⚠ THE FAMILY'S FIFTH INSTANCE, FOUND AND FIXED IN THE SAME SESSION.** `Band`'s scope skolem is a
  bound literal, so the first version minted FRESH PER FIRING: re-running the bank over an unchanged
  graph went 5 → 6 → 7 → 8 nodes, orphaning a `<hypothesis>` per pass. **Silent** — the penned head
  dedups, so the fork count stayed right and every band reader still answered correctly. It would
  have reintroduced precisely the session-long accretion the step-4 arc removed, because the grammar
  fold re-runs its banks over the whole graph every utterance.
- **THE FIX NEEDED A NEW MECHANISM, WHICH IS THE INTERESTING PART: a scope has NEITHER existing
  identity.** `intern` canonicalizes by NAME; `dedup` reuses by relation TOPOLOGY. A scope has no
  name and no subject/object edges, so neither applies — which is *why* it re-minted. So `MINT`
  gained a THIRD find-or-create mode, **`reuse_attr_of` + `reuse_key`**: reuse the node an existing
  BACK-REFERENCE points at. The scope's identity is the `<scope>` tag its own penned fact already
  carries, so a found (deduped) head yields a found scope. Node count now FLAT across runs, parity
  with `add_fork` preserved. Pinned by `test_a_band_is_idempotent_across_runs`, **re-break verified**
  (removing the reuse reproduces 5 → 6 → 7 → 8 exactly).
- **GENERAL LESSON, now on its fifth recurrence — worth a LINT rather than a sixth discovery:** a
  bound-literal skolem in a bank that re-runs is non-idempotent BY CONSTRUCTION. The three
  find-or-create modes now cover the three identities a minted node can have (name / topology /
  back-reference), so the lint has something to prescribe.

**SLICE 2b LANDED 2026-07-20 — HEDGING WORKS END TO END (suite 747 green, Loudon CNL still 19/19).**
`the lion generally has a mane` now lands as a fork at band 0.75 and commits NO ink.

- **`hedges`, a third assertion verb beside `asserts`/`denies`.** `_assert_forms` already generated
  over `(verb, mode)` pairs, so the declaration surface cost one tuple entry; the grammar file says
  `hclause hedges subj pred obj when hedge`. It is a VERB, not a flavour of `asserts`, for the same
  reason `denies` is one: the three differ in WHAT THEY COMMIT, which is what a declaration should
  say.
- **`HEDGE means NUMBER` as a grammar declaration** (`generally means 0.75`, `sometimes means 0.4`),
  read into `Grammar.hedge_bands`. Declared in the GRAMMAR because the band must be a COMPILE-TIME
  constant: `_hedge_rules` emits ONE RULE PER HEDGE WORD with the degree as a literal in its `Band`,
  since reading a degree at apply time would need a numeric lookup the ISA has no operation for.
  Same per-word expansion `deny` uses, and bounded by the DECLARED hedge vocabulary (4 words), not
  by the lexicon. Deliberately the SAME SURFACE as `uncertainty.parse_hedge_decl` so there is one
  syntax for "what degree does this word mean". An undeclared band is SKIPPED, never defaulted —
  a silent 0.5 would be inventing a degree.
- **⭐ A SILENT, ORDER-DEPENDENT FACT LOSS FOUND AND FIXED: `MINT(dedup=True)` WAS NOT LAYER-AWARE.**
  It matched on (subject, predicate, object) and ignored whether the candidate was a PENCIL, so a
  hedged `lion has mane` (control, scope-tagged, 0.75) made a LATER certain `lion has mane` reuse
  the pencil and write no ink — **the certain fact vanished**. Only in that order: assert-then-hedge
  was fine, hedge-then-assert lost it. A hedged claim and a certain claim are DIFFERENT assertions
  about the same triple and both must stand. Fixed by requiring the dedup candidate's control-ness
  to match. Pinned by `test_hedging_and_asserting_the_same_triple_is_order_independent`
  (parametrized over both orders), **re-break verified with the right asymmetry** — removing the
  guard fails `order1` and passes `order0`.
- **This is the same class the `asserts_content` fix removed once already** (order-dependent, silent,
  wrong in one direction only). Worth noting it appeared here from an INTERACTION between two
  correct-in-isolation mechanisms — pencil-vs-ink and dedup — rather than from either being wrong.

**⭐ THE REFUSAL EXPERIMENT 2026-07-20 — THE CONTRACT HOLDS, AND IT FOUND TWO SILENT DEFECTS IN THE
HEDGING SHIPPED THE SAME DAY (suite 755 green).** A cold-context subagent got ONLY the
comment-stripped form set (the shipped file's comments name the audit and list the gap sentence
numbers — that would have handed over the answer) and the 50 VERBATIM sentences, with the corpus
protocol: every sentence yields CNL, NOTHING-TO-ASSERT, or CANNOT-EXPRESS, never silence.

- **THE LOAD-BEARING ASSUMPTION HELD.** Zero manufactured facts; every produced CNL line parses;
  and **all 10 disagreements with the hand translation run the same way — hand=CNL, agent=refused.**
  Not one case of extracting where the human declined. The failure mode the whole re-point worried
  about (silent paraphrase into the nearest available form) **did not occur at all**.
- **BUT COVERAGE COLLAPSED: 3/50 vs the hand translation's 13/50**, refusing 26. The principle
  underneath is consistent and is the REAL finding: **the agent treats "weaker than the source" as
  grounds for refusal; the human treated it as acceptable partial capture.** Sentence 1's
  `the lion is strong` is a presupposition inside a causal explanation, not the assertion; sentence
  3's `lives in africa` drops "CONFINED to" — true but weaker. **OPEN CONTRACT QUESTION, and it
  sets the coverage ceiling for everything downstream: is weakening allowed, forbidden, or
  allowed-but-flagged?** Forbidden gives 6% translatability; allowed stops the KB faithfully
  reflecting the source. NOT a question to answer by building.
- **⚠ TWO SILENT DEFECTS IN SLICE 2b, FOUND BY READING THE DECLARATIONS:** `the lion generally
  hunts at night` and `the lion generally roars` PARSED, routed as `fact`, and committed
  **NOTHING** — no ink, no fork. `clause` declares several assertion shapes and slice 2b mirrored
  only the three it had tests for; the INTRANSITIVE (`unless obj`) and PREPOSITIONAL (`when pobj`)
  shapes were missing. **The tests covered exactly the shapes that had been built** — testing what
  was written rather than what the grammar can say. Also inflated the experiment's own numbers:
  2 of the 26 refusals were these defects, not the language's limits.
- **ROOT CAUSE AND FIX: the band was taken from the assertion's own `when` guard**, and the
  declaration surface allows ONE — so any hedged shape needing its own guard was UNWRITABLE. Fixed
  by `<cat> hedges under <slot>`, declaring the band slot ONCE PER CATEGORY so each line's guard
  stays free. All seven `clause` shapes now have hedged counterparts, pinned by
  `test_every_plain_shape_has_a_hedged_counterpart` (parametrized over SHAPES, deliberately, since
  the defect was shape-coverage); **re-break verified with the right asymmetry** — removing the two
  declarations fails the intransitive and prepositional cases and passes the two that always worked.
- **METHOD NOTE: a cold context was the POINT, not a convenience.** The subagent found by
  inspection what the author's tests missed, because it did not know which shapes had been built.
  This is the one task in the session where spawning an agent was right; the FIX was done inline,
  because there cold context is a liability (the `<…>` control-flag trap, delta seeding, join order,
  bound-literal skolems are all silent and specific).
- **CAVEAT, RECORDED SO THE RESULT IS NOT OVERSOLD:** the subagent is the SAME MODEL, so this
  controls for the session's context, not for model-level bias. A real SLM at the NL→CNL boundary
  may behave very differently — likely worse, since the discipline shown here is not cheap.
- Artifacts: scratch `refusal/` (leak-free inputs, `score.py`, `translation.json`).

**HEDGING IS COMPLETE** (concept-inventory gap 1 of 3). The other two were PROBED 2026-07-20, and the
guess written here first — "neither has an engine-side representation waiting, so both are likely
larger" — **was wrong for both**, in the same direction as every other mis-sizing this session:

- **ATTRIBUTION (`some naturalists consider the lion a cat`) IS MOSTLY DECLARATION WORK.** The
  pencil mechanism hedging uses already gives NON-VERIDICALITY FOR FREE: pen the proposition behind
  a scope keyed by its HOLDER (`<attribution>` node + `held_by` relation) and `check` returns
  **`assumed-no`** for it while an ordinary ink fact returns `positive`. So "recorded but not
  asserted" — the thing that looked like the hard part — already works. What is needed is
  declarations (a clause-as-complement production) plus a penning verb.
  * **DESIGN NOTE THIS SURFACED: the right primitive is `Scope`, not `Band`.** `Band` mints a scope,
    sets a GRADED attr, and pens heads. Attribution needs the same minus the degree, plus an
    ordinary `held_by` triple the RHS can already write. So the band is one optional DECORATION on a
    more general "pen these heads behind this node". Generalize when the second user arrives — but
    know that it is coming, and do not entrench `Band`'s graded key as mandatory.
- **CONDITIONAL (`the lion is dangerous when the lion is hungry`) IS A REAL DESIGN QUESTION — BUT
  NOT A GRAMMAR ONE.** Both halves already exist: `load_machine_rules` accepts `HEAD when BODY`, and
  the shipped intake ALREADY routes `?x is dangerous when ?x is hungry` to **`rule`** (the grammar
  fork left the rule route untouched). The gap is exactly one step: the natural sentence names `the
  lion` twice where the rule needs `?x`. **The question is WHO DECIDES WHAT VARIES** — (i) treat it
  as a GROUND conditional about the kind node (safe, invents nothing, but does not reach individual
  lions without an `is_a`-inheritance rule); (ii) variabilize the repeated subject (the system
  inventing a generalization); (iii) ask, via the discriminating question. **That is the LEARNING
  ARC's licensing question (§6.3, promotion by survival), not the grammar's** — a grammar cannot
  safely decide that `the lion` becomes `?x`. Route it there rather than answering it in
  `assert_bank`.
- **THE META-PATTERN, now three-for-three: gap sizing from intuition has been wrong every time this
  session, always by assuming depth where there was declaration work** (part-properties and
  captive-vs-wild in the audit; both of these). The probe is cheap — parse the sentence, check what
  the readers say — and it has changed the plan every time. Probe before scoping.

**⭐⭐ PROBED 2026-07-20, AND IT RELOCATED THE DESIGN QUESTION ONE LEVEL DOWN.** Two results, the
second more important than the question that prompted it:

1. **GENERICITY IS ONE DECLARATION LINE.** `slot det in np from determiner plus np is left head`
   keeps the determiner the grammar currently discards, and `a lion` / `the lion` become
   distinguishable (`det=a` vs `det=the`) with the corpus baseline unmoved at 19/19 and no ambiguity
   introduced. So the "who decides what varies" question does NOT need the discriminating question
   as its default answer: **English already marks the distinction, and the form set can carry it** —
   the same pattern as the marked exception (`no`) and the marked hedge (`generally`). User's
   instinct was `ask`; the probe says ask should be the ESCALATION (absent determiner, contested
   reading, or a `reconsider` contradiction implicating the choice), never the default, because
   batch corpus reading cannot afford a question per conditional and the answer is predictable
   almost always. **Silent variabilization stays rejected.**
2. **⚠ THE CONDITIONAL PARSES COMPLETELY AND WRITES TWO FALSE FACTS.**
   `a lion is dangerous when a lion is hungry` yields the full structure
   (`hsubj/hadjc/hdet` + `bsubj/badjc/bdet`, both readings distinguished) — and
   `facts = [(lion,is,dangerous), (lion,is,hungry)]`. **The sentence asserts NEITHER.** It parsed,
   reported `fact`, and committed two falsehoods: the quietly-does-something-wrong class.
   Cause: the two halves ARE `clause` spans, so `clause asserts subj is adjc when adjc` fires on
   each independently.

**THE REAL DESIGN QUESTION, and it is shared by all three remaining constructions: ASSERTION MUST BE
GATED BY CONTEXT, NOT BY CATEGORY.** Hedging avoided this by making `hclause` its own category, so
`clause asserts …` structurally cannot fire on it — **but that trick does not COMPOSE.** A
conditional's halves genuinely are clauses; giving them a non-asserting category means duplicating
every clause production, and attribution's complement needs the same again. Each non-asserting
context multiplies the grammar.

**BUILT 2026-07-20 (suite 751 green).** `<cat> suppresses` is a declaration; `suppression_bank`
marks every span the category dominates; `assert_bank` NACs on the mark. NO engine change — the
closure runs over the tree `decomposition_bank` already reifies: two rule families per child edge
(`dleft`/`dright`/`donly`), a base case (direct child of a suppressing span) and a transitive case.

- Conditional **2 false facts → 0**; plain sentences untouched in BOTH utterance orders; Loudon
  corpus still **19/19**; accretion FLAT (292 nodes per utterance, constant across repeats).
- **Delta-seeded on `FRESH` and idempotent by NAC**, following `decomposition_bank` exactly — sound
  on the same argument (a span's dominators are spans of the same sentence). Premise order is the
  join plan: `?p` is bound by the mark first, so `cat`/`dparent`/the child edge are all FOLLOWs.
- **DECLARE-BEFORE-USE: a grammar that declares no suppression pays nothing** — not even the extra
  NAC premise, which is only added when `gram.suppressing` is non-empty. Pinned.
- **⚠ THE PLAIN NAME WAS LOAD-BEARING, AND THIS WAS NEARLY THE SIXTH INSTANCE.**
  `_rule_touches_control` inspects the **NAC** as well as the LHS, so naming the mark
  `<suppressed>` would have flagged every assert rule as control-writing and the fold would have
  produced ZERO facts while every rule fired correctly. Checked before writing it rather than after
  — the one time this session the trap was avoided rather than survived.
- Pinned by four tests including `test_without_gating_a_conditional_asserts_both_halves`, which
  pins the DEFECT so the gate cannot be quietly removed.

**⚠ CORRECTION TO THIS SECTION'S FIRST DRAFT: it does NOT retire `hclause`.** The claim was that one
mechanism covers all three. The probe says there are TWO gates, because the two shapes differ:
- **DOMINATION gating** (a descendant of a suppressing span does not assert) — what conditionals and
  attribution need, since their content is a NESTED clause. This is what was just probed.
- **SELF gating** (this span asserts hedged rather than plainly) — what hedging needs. `hclause`
  contains no inner `clause` span, so nothing dominates anything; the hedged clause must suppress
  its OWN plain assertion. That is `clause asserts subj pred obj unless hedge` — which the
  declaration surface CANNOT express today, because it allows only ONE guard and
  `unless neg` already occupies it. So retiring `hclause` needs MULTI-GUARD `unless`, a different
  (also small) change — not this one.

**⭐⭐ THE DUALITY BIT, AND IT WAS SILENT AND RIGHT-BY-LUCK (2026-07-20, suite 757 green).** Set out to
build `implies` (sequence item 1 below). Probed first, per this file's own three-for-three lesson —
and the probe killed the feature and found a defect underneath it instead.

- **`implies` IS NOT NEEDED, AND WOULD HAVE BEEN BUILT ON SAND.** The explicit core surface for
  conditionality ALREADY SHIPS: `?x is dangerous when ?x is hungry` is unambiguous by construction
  and intake routes it to the rule layer **ahead of the grammar fork**. Measured working on the
  grammar route in all four shapes (universal, ground, rule-before-fact, fact-before-rule).
  `a lion is dangerous when a lion is hungry` is therefore **T1 SUGAR**, and this plan's own
  criterion says sugar is justified from the residue log, never speculatively. Not built.
- **⭐ BUT THE RULE LAYER AND THE GRAMMAR ROUTE DID NOT MEET.** A rule MATCHED its premise on the
  interpretation ENTITY (where the fold writes content) and EMITted its conclusion onto the discourse
  TOKEN, because `nodes_named` returns the token first and `resolve_write_node` takes `[0]`.
  Measured: `is hungry` on the entity, `is dangerous` on the token. **The derived fact fell OUTSIDE
  the interpretation scope** — invisible to `scope_facts`, uncleared by `discard_scope`, unrevisable
  by `reconsider`, and surviving a re-reading that invalidates its own premise. **The question still
  answered `yes`**, because name resolution also happened to pick the token first. The
  quietly-does-something-wrong class, with a `UserWarning` as its only trace.
- **THE FIX IS STRUCTURAL AND AT ONE CHOKEPOINT:** `chain._through_denotation` — **a node that
  `denotes` something is SURFACE, so content addressed by its name belongs to its denotation.** This
  is the discipline `resolve_write_node` already stated ("a write must land on a real entity node");
  a token that denotes something is precisely not one. `DENOTES` moved to `vocabulary.py` (the leaf)
  so `chain` can see it without a cycle. **All three write paths go through `resolve_write_node`**
  (`chain EMIT`, `ask_goal materialize`, `suppose assumption`), so one fix covers every place a name
  becomes a write target — the chokepoint its docstring claimed, and it held.
- **INERT ON THE SHIPPED ROUTE BY CONSTRUCTION** — nothing there writes `denotes`, so nothing maps
  and it is the identity function. Declare-before-use, the same discipline the fork uses. Confirmed:
  the suite was 755 green before and after, with the change in.
- The read-side `_warn_name_split_join` now collapses through denotation too: a token and its
  denotation were never two identities, they were **one identity split across the layer boundary**,
  so warning about them was crying wolf.
- Pinned by `test_a_derived_fact_lands_in_the_interpretation_not_on_the_token` and
  `test_a_derived_fact_is_discardable_like_any_other_judgement` (the second is the POINT, not a
  tidier address: a conclusion derived from an interpretation is itself a judgement and must be
  takeable-back). **RE-BREAK VERIFIED on both** — removing the one line fails both on the intended
  axis. Note the assertion is on `gi.facts` and NOT on the answer: the answer was already `yes` while
  the belief lived in the wrong layer, which is exactly why a test on the answer would have passed.
- **⚠ READS ARE NOT YET PRINCIPLED, only harmless.** 54 `nodes_named` sites across 23 modules still
  resolve by name. They work because reading a TOKEN now finds no content — an absence, not a
  redirect. That is fine while the fold is the only writer, and it is the next thing to make
  structural if any reader starts caring which node it got.
- **THE LESSON, and it generalizes past this bug: "the mechanism exists" ≠ "the mechanism is
  REACHABLE from the surface".** `form_inventory.md` §2(c) prices a fundamental form as cheap iff a
  substrate mechanism already exists; that is necessary, not sufficient — mechanism and surface must
  land in the SAME LAYER. **Probe every "mechanism exists" entry end to end (assert through the real
  route, then ASK) before calling it cheap.** Attribution is next and has exactly this shape.
- **METHOD NOTE: the surface/epistemic split is what found it.** The user's question — "can we
  distinguish what is surface and what is epistemic, since surface may be managed by SLM/LLM
  conversion later?" — moved attention off the declaration syntax (all baroque) and onto the real
  commitment: *when the system derives through a conditional, what does it believe and in which layer
  does that belief live?* The answer was "an ink fact on a discourse token", which no surface choice
  could have fixed. **Classify the decision list before building it.**
- Probes: scratch `probe_cond.py` / `probe_explicit.py` / `probe_duality.py` (the last reads the
  NODES, which is what separated "works" from "right by luck").

**ATTRIBUTION'S SUBSTRATE PROBED END TO END — SOUND, AND `Band` GENERALIZED (2026-07-20, suite 758
green).** Held to the rule the duality bug just produced: probe a "mechanism exists" entry through
the REAL route before calling it cheap. Hedging is the cheap proxy, since it already drives the same
pencil scope THROUGH THE FOLD.

- **The pencil mechanism is reachable end to end, and for the right reason.** Under the default crisp
  stance a hedged premise answers `no (assumed)` and a rule does NOT reason through it — correct,
  that IS the non-veridicality attribution wants. Under a banded stance (`be decisive`) the hedged
  fact answers `likely` AND a rule reasons through it, with the band PROPAGATING to the conclusion
  at 0.75.
- **Verified at NODE level, not from the reader's number** — the lesson from the duality bug, where
  the reader was right by luck. Both the hedged premise and the derived conclusion are pencil
  relations **on the ENTITY** (`n168`); the surface token carries nothing. So the possibilistic
  layer, the rule layer and the grammar route all meet on the entity side. **Attribution inherits a
  working substrate**, and the plan's "mostly declaration work" now has evidence behind it.
- **`Band` GENERALIZED, per its own design note ("generalize when the second user arrives — do not
  entrench the graded key as mandatory"). The second user has arrived.** `key`/`degree` are now
  OPTIONAL: the primitive is "pen these heads behind this node", and the graded attribute is one
  optional thing you may say about that node. Attribution needs the scope MINUS the degree — and had
  they stayed mandatory it would have had to **fabricate a degree**, which is exactly the silent
  default the hedge path refuses to make (an undeclared band is SKIPPED there, never defaulted).
- **THE NAME STAYS `Band`, deliberately, and that is this session's principle applied to itself.**
  The design note said "the right primitive is `Scope`, not `Band`". Renaming is SURFACE — churn
  across the lowering, the grammar and the tests for no change in what any rule can express. The
  mandatory graded key was the real entrenchment; that is what came off. Spend on the epistemic
  column, not the baroque one.
- Pinned by `test_a_band_can_pen_without_a_degree`, which asserts BOTH halves (the head is penned and
  `<scope>`-tagged; no degree is fabricated on the scope node). **Re-break verified** — forcing the
  graded write back on fails it.
- Probe: scratch `probe_attribution.py`.

**⭐⭐ WHAT BREAKS IF THE GRAMMAR ROUTE BECOMES THE DEFAULT — MEASURED 2026-07-20 (user question).**
Answer: **not the client. The CNL surface.** And the blocker is not coverage, it is a scaling hazard
that only appears when you fix coverage.

- **`../pystrider` IS ESSENTIALLY UNAFFECTED, measured: 388 passed / 0 failed against this tree**
  (which also clears my `_through_denotation` change — inert on a client that never writes `denotes`,
  as designed). The SHIPPED packages (`pystrider/`, `grammapy/`) call `ingest` **zero times**; the
  only 6 calls are in `experiments/` and are ALL `to NAME :` / `run NAME` — **procedure routes, which
  sit ABOVE the fork** along with questions, rules, focus, stance and forms. pystrider is a
  graph+rules+reasoning client (`AttrGraph`, `load_machine_rules`, `ask_goal`, `suppose`,
  `set_candidate`), not a natural-language one. NOTE the stale memory: the "14 pre-existing failures"
  baseline is gone, it is now fully green.
- **The exposure is the FACT tail, and it is large in the REPO: 79 of 152 non-comment lines across
  the shipped `corpus/*.cnl` are fact-route lines** that would hit the fork.
- **THREE BREAKING CLASSES, measured on real corpus lines** (`get_beans produces beans`,
  `we want have_coffee`, `charizard is rare`, `buy_charizard is a buy`, `ada visits dog`,
  `don't sell rare cards`):
  * **Closed vocabulary: 0/6.** Every word must be in a declared lexicon with a declared category.
  * **+ open vocabulary for ENTITIES: 2/6.** Fixes nouns, not predicates.
  * **+ predicates declared `transitive`: 5/6.** So arbitrary binary relations DO work — but each
    predicate needs a lexicon line, the grammar-route counterpart of the shipped `relation_forms`
    "declare the relation and a form is generated". Comparable burden, NOT a blocker.
  * **1/6 never parses: `don't sell rare cards`** — an imperative/policy line. A genuinely absent
    construction, not a vocabulary gap.
- **⭐ THE REAL BLOCKER, AND IT IS THE OPPOSITE OF WHAT COVERAGE WORK ASSUMES: OPENING THE VOCABULARY
  MANUFACTURES AMBIGUITY IN SENTENCES THAT ALREADY WORKED.** `charizard is rare` parses cleanly with
  open nouns, and goes AMBIGUOUS once `rare` is declared an `adj` — because `chart_bank`'s
  open-class NAC excludes only `CLOSED_CLASSES` (`determiner`/`negator`/`comparator`/`preposition`/
  `copula`), so a declared CONTENT word is still ALSO eligible as an open noun. Two categories, two
  readings. **Reproduced on the shipped corpus: `the lion is strong` is `parsed` closed-vocabulary
  and `ambiguous` with `open_class="noun"`.** The Loudon 19/19 baseline never saw this because it
  runs closed.
- **WHY THAT IS THE DECISION-RELEVANT PART.** An ambiguous utterance commits NOTHING (by design). So
  the grammar does not degrade GRACEFULLY as vocabulary grows — it degrades into silence, and the two
  fixes for coverage (declare more words / open the vocabulary) pull against each other. Any
  "make it the default" plan must resolve this FIRST, or every KB gets quieter as it gets bigger.
- **⭐ FIXED 2026-07-20 (suite 761 green) — AND THE INTUITION WAS RIGHT THIS TIME, WHICH IS ITSELF
  WORTH RECORDING** after four consecutive mis-scopings. The probe confirmed it rather than
  overturning it: **the open-class default now applies to words the grammar declares NOTHING about**,
  not to every word outside a closed class. `chart_bank`'s marker renamed `closed_class` ->
  `DECLARED` (the rename IS the fix — the old name marked only function words).
  * **MEASURED:** Loudon corpus with `open_class="noun"` goes **21 parsed + 2 ambiguous -> 23/23**;
    gibberish still REFUSED; closed-vocabulary behaviour bit-identical. The corpus sample goes 5/6
    with no ambiguity (`don't sell rare cards` still refuses — a genuinely absent construction).
  * **THE TRADE, MEASURED IN BOTH DIRECTIONS RATHER THAN ASSERTED.** A nominalized adjective
    (`the strong is smaller than the lion`) parsed under the old rule and now REFUSES — **but the
    capability MOVED to an explicit declaration rather than being lost**: add `strong is a noun` and
    it parses again, at which point `the lion is strong` is ambiguous HONESTLY, because the grammar
    really has said the word is two things. **Declaring is how a grammar says what a word can be; the
    default only fills in for words it has not spoken about.** And the loss case is a REFUSAL — loud
    and countable — where the old behaviour's cost was silence. That is the direction this project
    trades in.
  * `CLOSED_CLASSES` no longer gates anything and `chart_bank`/`compile_grammar` lost their dead
    `closed=` parameter. **`bench/spike_homoiconic_grammar.py`'s `lexical_spans` REIMPLEMENTED the
    old rule** and was updated in the same change — the "harness that duplicates a pipeline" trap
    this file has now recorded three times.
  * Pinned by `test_opening_the_vocabulary_does_not_make_declared_words_ambiguous`,
    `test_the_open_default_still_refuses_gibberish` and
    `test_a_word_needing_two_categories_must_DECLARE_both` (which pins the LOSS case too, so the
    trade cannot be quietly reversed). **RE-BREAK VERIFIED WITH THE RIGHT ASYMMETRY:** restoring the
    old gating fails the two behaviour tests and leaves the gibberish one passing — correct, since
    that one guards a property the fix PRESERVES rather than one it introduces.
- **⭐⭐ THE DECLARATION BURDEN IS ~ZERO, AND IT IS NOW DERIVED (2026-07-20, suite 765 green).** User's
  challenge ("the burden should be easily fixable, we don't have thousands of lines of KB") — correct,
  and the measurement found something stronger than "small":
  * **THE BURDEN ALREADY EXISTS AND IS ALREADY PAID.** The SHIPPED route refuses `get_beans produces
    beans` outright until the KB says `produces is a relation` (measured). So the grammar route's
    `produces is a transitive` was NEVER a new burden — **same line count, same `X is a Y` shape,
    only the category word differs.** There is no migration cost here, only a rename.
  * **SIZE: 9 distinct predicates across EVERY shipped corpus** (`acts_on`/`costs`/`have`/`needs`/
    `outranks`/`produces`/`want`/`wants`/`is`), 1-5 per KB; the 54 entity words are free under open
    vocabulary.
  * **SO IT IS DERIVED, NOT WRITTEN: `grammar_intake.sync_vocabulary`** reads `declared_relations`
    and adds each as `RELATION_CATEGORY = "transitive"`. **An existing KB migrates without editing
    its corpus.** My worry that `relation` -> `transitive` might be silently wrong for some predicate
    was UNFOUNDED, and measured so: a purely derived grammar (domain-neutral core + open nouns +
    derived relations) parses **69 of 76 corpus fact lines with ZERO mis-mappings**.
  * **RUNTIME GROWTH WAS THE REAL REQUIREMENT**, not a read at declaration time: a corpus declares
    its relations in its own text, so on this route `produces is a relation` is itself parsed by the
    grammar and the vocabulary arrives DURING ingestion. `route` syncs first and re-reads the banks
    (the sync recompiles, so a caller holding pre-sync banks would parse with a stale lexicon).
  * **CHEAP ONLY BECAUSE IT RECOMPILES RATHER THAN RE-READS — and the measurement is a surprise
    worth its own line: `load_grammar` is 1678 ms against `compile_grammar`'s 13 ms (126×).** The
    text->`Grammar` parse is the expensive half, and it is LONGER THAN AN ENTIRE 8-SENTENCE SESSION
    (1.39 s). Syncing by re-reading source text would have cost 1.7 s per utterance. **`load_grammar`
    is now the single largest cost in a grammar session and nothing has ever profiled it.**
  * **`declare_grammar` GAINED `open_class=`** — the route shipped with CLOSED vocabulary, so the
    open-class fix above was not even reachable from intake. `GrammarBanks` remembers `open_class` so
    a recompile cannot silently drop it.
  * **THE SAFETY PROPERTY IS PRESERVED AND PINNED**: an undeclared predicate is still REFUSED, not
    guessed. Deriving must not degrade into "accept any three words". Four tests incl.
    `test_an_undeclared_predicate_is_still_refused` and
    `test_an_explicit_grammar_declaration_beats_the_derived_default` (the derivation fills a gap, it
    never re-categorises hand-written vocabulary).
- **THE REMAINING GAP IS TWO CONSTRUCTIONS, NOT A LONG TAIL.** The 7 refusals out of 76 are:
  1. **DEGREE ADVERBS — 5 of 7** (`buy_online is somewhat risky`, `trade_at_club is very risky`,
     `alice is very urgent`). **This is the hedging family again** — an adverbial slot on an
     ADJECTIVE where `generally` was one on a VP, and **UGM already has the semantics** (bands, θ).
     Cheapest remaining inventory entry by some distance, and it is a FORM_INVENTORY entry
     (`degree`) already listed as REPRESENTED — the surface just does not cover the adjectival case.
  2. **IMPERATIVES — 2 of 7** (`don't sell rare cards`, `serve urgent customers first`). Genuinely
     absent; these are policy/preference lines, arguably not fact-route content at all.
- **NOT CHECKED, and owed before any migration:** `focus.utterance_subjects` and
  `authoring.anchor_has_content_fact` are the two token-chain readers `grammar_intake` wrote
  counterparts for rather than edits; the book/playground surface; and whether `load_kb` corpora would
  each need a grammar file. The 54 `nodes_named` read sites (above) are in the same bucket.

**⭐⭐ `load_grammar` PROFILED AND CACHED 2026-07-20 (suite 767 green) — SUITE 156 s → 77 s (2×).**
Nothing had ever profiled it; it was the largest single cost in a grammar session.

- **`read_grammar` WAS QUADRATIC IN A PLAIN PYTHON SWEEP** — not in any bank. It made **3,278,010
  `has_key` calls** on the 124-line Loudon grammar (30 candidate declaration keys probed against
  every relation in the graph), and grew **122× for 8.3× more input** (3.9 ms at 15 lines → 476 ms at
  124). Fixed by taking candidates from the O(1) KEY INDEX (`nodes_with_key`) instead:
  **476 → 33 ms (14×)**. Iteration ORDER deliberately unchanged — `slot_bank`/`assert_bank` derive
  rule keys from list POSITION, so reordering `gram.slots` would silently rename every generated
  rule. **Verified IDENTICAL output (order included) against the old implementation on both shipped
  grammars**, not merely faster.
- **THE REST IS `load_facts` (1424 ms), THE NAIVE `run_bank` SHAPE** — 863k matcher steps running 17
  declaration forms over the whole graph. NOT fixed; cached around instead.
- **CACHED, because grammar text → `Grammar` is PURE.** Measured before: **47 calls totalling 59.2 s
  across the two grammar test modules alone** — 63% of their runtime re-parsing two unchanging files.
  Now **1402 ms cold / 13 ms warm (108×)**; bounded `lru_cache` rather than unbounded, since benches
  and probes generate grammars programmatically.
- **⚠ THE CACHE HAD TO RETURN COPIES, AND THAT IS LOAD-BEARING.** `Grammar` is MUTABLE and is mutated
  in normal operation — `sync_vocabulary` writes derived relations into `lexicon`. Sharing the cached
  instance would leak one KB's vocabulary into every other KB built from the same file: **"a word
  parses in a test only when some earlier test ran"** — order-dependent and silent, this session's
  signature failure mode. Pinned by `test_loading_the_same_grammar_twice_does_not_share_mutable_state`
  and the end-to-end `test_two_kbs_from_one_grammar_file_do_not_share_derived_vocabulary`;
  **re-break verified** (both fail without the `deepcopy`).
- **SEQUENCING CORRECTED WHILE PINNING IT:** `route` now reads the banks from the REGISTER (live
  source of truth, so a caller's stale reference is harmless) and syncs vocabulary AFTER the fold, so
  the register reflects everything declared the instant the call returns. Syncing only before it left
  the register lying about what the KB knew until some later utterance happened to run — found by a
  test failing for the right reason.
- **`declared_relations` de-sweeped** (same key-index fix): `sync_vocabulary` calls it per utterance,
  so a whole-graph sweep would make a session quadratic in its own length. Only 0.22 ms at 1445 nodes
  today — fixed before it was not.
- **⭐ THE VIABILITY NUMBER THE PROFILING WAS FOR, and it is the honest blocker for subsumption:
  ~240 ms/utterance on the grammar route** (route closed 237, open vocabulary 261, full `ingest` 266
  — so open vocabulary costs ~10% and `ingest`'s other routes ~7%; the cost is the grammar route
  itself). **Against the ~12 ms/utterance the shipped path budgets, that is ~20×.** Grammar LOADING is
  now a solved cost (13 ms warm); PER-UTTERANCE is not. **Subsumption would apply that 240 ms to
  every question and every stance line too**, which is the trade to decide before moving surfaces
  onto it. The remaining lever is the one this file already names: `load_facts`/`run_bank` is naive,
  and `parse`+`interpret` were last optimized to a LINEAR-but-constant-heavy shape.

**⭐⭐ WHERE THE 240 ms/UTTERANCE ACTUALLY SITS — PROFILED 2026-07-20 (user: "could it be optimized
further?"). YES, AND THE LEVER IS SEMI-NAIVE `run_bank`, NOT ANY BANK.**

- **STAGE SPLIT (8-sentence session, 256 ms/utt):** `interpret` **56.4%**, `ambiguity` 21.5%,
  `spans+decs+supp` 15.3%, `chart` 6.8%, tokenize 0.1%. Inside `interpret`: **`slots` 59.9%**,
  `asserts` 29.5%, `contradiction` 8.1%, mentions 2.0%, defining_asserts 0.3%, intern 0.2%.
  **So `slots` alone is ~33% of the whole session** and is the single biggest stage.
- **⭐ IT IS FLAT, NOT GROWING — so this is a CONSTANT-FACTOR problem and every delta/seeding lever is
  ALREADY SPENT.** Measured over 8 utterances while the graph went 192 → 1406 nodes: slots stayed
  45-103 ms and asserts 25-49 ms, varying with SENTENCE COMPLEXITY rather than session length. The
  step-4 arc's work holds; there is no seeding defect left to find here.
- **⭐⭐ THE REAL FINDING: ~300 MATCH CALLS TO PRODUCE ~20 FIRINGS.** The slot bank runs **5.1 fixpoint
  rounds × 59 rules = ~301 match calls** and fires 16/19/22 times. `cProfile` confirms the cost is
  purely the matcher (593k `_match_step`, 2.3M `isinstance` = 17% on its own) — **not** re-lowering
  (already cached per-rule on `rule.__dict__["_lowered_bank"]`) and not stratification.
- **THE CAUSE IS THE ONE THIS FILE ALREADY DOCUMENTS IN `run_bank`'s OWN DOCSTRING: "Naive — no
  semi-naive delta / df-seeding (correctness-first)."** Every round re-matches EVERY rule, including
  rules whose premises nothing has touched since the last round. Rounds are legitimate (slot
  percolation genuinely cascades: np inside np inside clause) — re-matching *all* 59 rules per round
  is not.
- **⭐⭐ DONE 2026-07-20 (suite 772 green): PREDICATE-LEVEL SEMI-NAIVE ROUNDS. Grammar session
  218 → 135 ms/utt (1.62×); THE WHOLE SUITE 78 s → 51 s (1.5×); pystrider 388 green.** The
  `"Naive — no semi-naive delta"` note in `run_bank`'s own docstring, finally addressed — and the
  win is system-wide, not grammar-only, because EVERY bank pays this.
  * **THE MECHANISM:** after a round, collect the predicates actually written; next round, match only
    rules whose LHS mentions one of them. Per-rule LHS/RHS predicate sets computed once.
  * **SOUNDNESS RESTS ON MONOTONICITY, and the NAC case is the EASY direction:** adding facts can
    only make a NAC's witness MORE likely, so a NAC can never ENABLE a rule it previously blocked.
    (A blocked match is deliberately not added to `fired`, so it retries each round — and that retry
    is only useful if a premise predicate changed.) **`drop` breaks monotonicity, so a bank
    containing any drop opts out entirely.**
  * **CONSERVATIVE ON WRITES:** a variable head predicate, `bands`, or `propagate` writes things no
    `Pat` names, so those rules set `dirty = None` (match everything next round). Tool servicing does
    the same, since it mutates outside rule firing. Being wrong in that direction only costs speed.
  * **GATED ON A DIFFERENTIAL, not on the argument above:** identical triples/nodes/scope-facts on a
    full grammar session, then the whole 772-test suite (planning, procedures, possibility, coref,
    deontic, learning), then the pystrider client. `semi_naive=False` remains as the escape hatch and
    as the differential's other arm.
  * **PINNED BY A CASCADE, deliberately** — `test_semi_naive_reaches_the_same_fixpoint_as_the_naive_loop`
    (4-deep chain, so several rounds are REQUIRED) and
    `test_semi_naive_still_fires_a_rule_whose_premise_appears_later` (a consumer listed BEFORE its
    producer, which is what a dirty set that does not survive rounds gets wrong). **Re-break verified:
    making the dirty set not carry what was written fails both.**
- **~~THE PROPOSED LEVER~~, ranked first: PREDICATE-LEVEL SEMI-NAIVE ROUNDS.** After each round, collect
  the predicates actually written; in the next round only match rules whose LHS mentions one of them
  (plus rules not yet matched). **Sound on a monotone bank, and the NAC case is the easy direction**:
  adding facts can only make a NAC *more* restrictive, so a NAC can never ENABLE a rule that was
  previously blocked. Estimated ~3× on the two dominant stages, i.e. session ~256 → ~150 ms/utt.
  **⚠ ENGINE CHANGE to the core forward driver used by every bank — gate it on the existing
  forward/demand differential sweep, and expect the standing rule ("correctness before raw
  performance") to apply.**
- **SECOND LEVER — ⭐ DONE 2026-07-20 (suite 770 green): THE DENY COLLAPSE. `assert_bank` 61 → 32
  rules; session 237 → 221 ms/utt (7%, as estimated).** The pairing predicted by this file
  (`w -[neg_of]-> w_not`) now exists as GRAPH DATA, authored once per graph by
  `author_negative_pairing` through the ISA (`load_fact_triples`, so interned + deduped), and the
  rule BINDS the negative as an ordinary LHS-bound predicate variable. **The vocabulary became DATA
  (looked up) instead of RULES (re-matched every round) — that is the whole saving.**
  * **⚠ THE TOKEN/ENTITY DUALITY BIT AGAIN, ONE LAYER ALONG, and the first version silently DROPPED
    THE EXCEPTION** (`the guzerat lion has no mane` parsed, routed `fact`, and wrote no `has_not`).
    `author_negative_pairing` interns by NAME and the TOKEN is created first, so the `neg_of` edge
    landed on the token — while the `pred` slot binds the ENTITY (`HEAD_BRIDGE` resolves a one-token
    span's head to what its token denotes). Same name, different node, no match. **Fixed by having
    the rule hop back across the layer explicitly via `interprets`** (the entity's own provenance to
    its mention), which also keeps the vocabulary on the PERMANENT SURFACE rather than inside the
    discardable interpretation. `INTERPRETS` joined `DENOTES` in `vocabulary.py` (the leaf) for it.
  * `NEG_OF` is a PLAIN name and is in `SURFACE_PREDS`: a `<...>` name would have made
    `_rule_touches_control` classify every deny rule as control-writing and the fold would have
    produced zero facts while firing correctly (lesson 1, checked before writing rather than after).
  * **THE TEST THAT MATTERS IS ON RULE COUNT vs LEXICON SIZE, NOT ON BEHAVIOUR** — and the re-break
    proved why: restoring the per-word expansion leaves BOTH behavioural tests passing (the exception
    still lands) and fails only `test_the_deny_bank_does_not_grow_with_the_lexicon` (61 → 86 with 25
    extra words). A behavioural test structurally cannot see this regression.
  * Also pinned: `test_the_negative_pairing_is_authored_once` (the fold re-runs over the whole graph
    every utterance, so non-idempotent authoring would accrete — the bound-literal family's sixth
    would-be instance, guarded by the key index).
- **THIRD: `ambiguity` at 21.5%** is now the largest stage OUTSIDE interpret and has never been
  attacked. Measure it before assuming — this file's stated lever has been wrong four times.
- **NOT a lever: `load_grammar`.** Solved by the cache above (13 ms warm).

**⭐⭐ FORCE, SLICE 1: QUESTIONS LAND 2026-07-20 (suite 778 green).** The first non-assert force to
become a FORM rather than an intake route. `design/form_inventory.md` §4b is the spec; it was written
BEFORE the build, deliberately (user: "we need the inventory of epistemic forms to be a valid
reference"), so this was a spec-follow rather than an invention.

- **`asks` IS THE FOURTH FORCE VERB, and the one that COMMITS NOTHING** — `<cat> asks subj pred obj`
  generates **no fold rule at all**. `_assert_forms`' `(verb, mode)` table gained one tuple; the
  declaration records only WHICH SLOTS carry the asked triple, and `grammar_intake.question_of`
  reads them. That is the whole point of force as a declaration axis: `asserts`/`denies`/`hedges`/
  `asks` differ in WHAT THEY COMMIT, and asks commits nothing.
- **ROUTED BY THE PARSE, NOT BY POSITION IN THE LADDER.** `route` returns `question` because the
  root span is in a category declaring `asks` — no string sniffing (§D.1). This is the first
  concrete piece of DECLARATIVE ROUTING replacing `_ingest_gen`'s ordered if-ladder.
- **ANSWERING IS UNCHANGED, deliberately:** the same `_answer_with_ask` the shipped route uses,
  handed the STRUCTURED goal `("yesno", s, p, o)` (`_tuple_query` already accepted tuples) instead of
  a question string. Moving force onto the grammar must not fork the answering machinery.
- **⚠ A QUESTION ASSERTED ITS OWN CONTENT — found while building, and it is §8's failure exactly.**
  `whether P` embeds a genuine `clause` span, so `clause asserts …` fired on it: measured,
  `whether lion is huge` wrote `lion is_a huge`. **Perfect content mapping, zero force.** Fixed with
  `qclause suppresses` — the domination gate built for CONDITIONALS, reused rather than duplicated,
  which is evidence that gate generalises beyond the case it was built for.
- **A READER, NOT A REIFIED `<question>` NODE — and the discriminator is worth recording:** an
  answer is a VALUE returned to the caller, not graph state, and reading the parse is what
  `asserts_content` already does for the assert force. Reified intent (`run NAME` → `<run> proc NAME`)
  is the right shape for forces that LEAVE SOMETHING BEHIND; ASK leaves nothing.
- **SEQUENCING CORRECTED MID-BUILD:** the first version read slots BEFORE `extend` and found nothing,
  because slot percolation runs in `interpret`, not `parse`. Folding the question first turns out to
  be RIGHT rather than a compromise — `interpret_mentions` resolves the question's words to the SAME
  entities the facts were written on, which is what makes the question REFER.
- **MEASURED:** all six question shapes route correctly (`is X adj`, `is X a Y`, `is X P Y`,
  `whether …` ×3) and the answers come back `yes` / `no (assumed)` through real `ingest`, with facts
  UNCHANGED. Loudon fact corpus still 23/23, no ambiguity introduced.
- Pinned by `test_a_question_routes_by_its_parse_and_commits_nothing` (parametrized over shapes),
  `test_a_whether_question_does_not_assert_its_own_complement` (pins the DEFECT), and
  `test_a_question_is_answered_through_the_shipped_machinery`. **RE-BROKEN ON BOTH HALVES
  INDEPENDENTLY:** removing `qclause suppresses` fails the complement test; making `asks` generate a
  fact rule like `asserts` fails it AND the commits-nothing case.
- **ONE SHIPPED TEST NEEDED FIXING FOR THE RIGHT REASON.**
  `test_a_grammar_declaring_no_suppression_is_unaffected` used `loudon_grammar.cnl` as its example of
  a suppression-free grammar; questions made that false. It now BUILDS its own un-declaring grammar —
  a declare-before-use test must supply the un-declaring case itself rather than assume the shipped
  file stays that way.
- **REMAINING FORCE GAP: 7 of the original 31** (4 goals, 3 speech acts) once questions are counted.

**⭐⭐⭐ CAN THE GRAMMAR SUBSUME CNL? PROBED 2026-07-20 (user question) — YES FOR TWO OF THE THREE
CLASSES, AND THE MAIN RISK DID NOT MATERIALIZE.**

- **THE DIAGNOSIS FIRST, because it is a MODELLING gap and not an implementation one. The grammar
  models propositional CONTENT; ILLOCUTIONARY FORCE lives in the router.** Every `form_inventory.md`
  entry (degree, negation, attribution, conditionality, genericity, tense, quantification, causation,
  resemblance) is about WHAT IS CLAIMED. **There is no entry for FORCE** — assert / ask / command /
  author — yet UGM has always had it, implemented as the ordered if-ladder of intake ROUTES in
  `_ingest_gen`. Apply the doc's own test: `is lion dangerous` cannot be paraphrased into an
  assertion without changing what the system DOES. **So force is epistemically FUNDAMENTAL and is the
  one fundamental thing missing from the inventory.** That is why the grammar does not subsume CNL.
- **THE AXIS IS ALREADY HALF-BUILT.** `asserts`/`denies`/`hedges` ARE force markers — they differ
  precisely in WHAT THEY COMMIT. `asks`/`authors`/`commands` extend the same declaration axis
  (`_assert_forms`' `(verb, mode)` table), not a new mechanism.
- **SYNTAX IS NOT THE BLOCKER — MEASURED.** Given productions, the grammar parses every surface
  tried, **declarations only, no Python**: question (`is lion dangerous`), stance (`be cautious`),
  focus (`focus on lion`), run (`run build`), norm (`don't sell rare cards`). The gap is entirely in
  what the FOLD CAN PRODUCE.
- **THREE OUTPUT CLASSES, and only one is hard:**
  * **(a) GRAPH WRITES — reachable today.** A norm reifies as a `<norm>` node plus relations, which
    is what `Band` already does.
  * **(b) BANK AUTHORING — rules / forms / procedures** must yield a `Rule`, not a triple. This is
    the `implies` problem generalized. **USER DECISION: handled by HAND-AUTHORING one "universal"
    grammar** (T2-authored, the normative spec of the target language — the convergence this file
    already called for). Not learned.
  * **(c) SPEECH ACTS — question / stance / focus / run / disable.** They do not add knowledge, they
    DO something.
- **THE BRIDGE HAS A PRECEDENT IN-CODEBASE: REIFIED INTENT.** `run NAME` already works by seeding a
  `<run> proc NAME` node a driver then acts on. So the fold writes a reified intent (graph data,
  which it can already do) and the ROUTE dispatches on it. That covers (a) and (c) with NO new fold
  capability.
- **MEASURED: ONE grammar carrying facts + all five force surfaces gives ZERO ambiguity, and the
  Loudon fact corpus stays 23/23.** The risk this probe existed to find did not appear.
- **⚠ AND MY STATED REASON WHY WAS WRONG — CHECKED, AND DISPROVED.** I predicted the open-class fix
  was a PREREQUISITE (that force words doubling as nouns would collapse it). Simulated the old
  behaviour by declaring `be`/`focus`/`run` as nouns TOO: **everything still parses unambiguously.**
  The real reason is better and more robust: **English marks force POSITIONALLY at the LEFT EDGE** —
  an imperative/prohibitive/copula in initial position is structurally unambiguous against a fact
  that starts with an np, and there is no `np plus np` production for the noun reading to use. Force
  composes cleanly because of where it sits, not because of the lexicon.
- **FORCE IS RECOVERABLE FROM THE PARSE**, so routing can become DECLARATIVE: the root category
  distinguishes `clause` / `qclause` / `iclause` / `pclause`. That is a WIN over today's ordered
  if-ladder (try question, then rule, then fact), which is order-dependent by construction, and it is
  exactly §D.1 ("route by which forms fired, not by sniffing the utterance"). NOTE `iclause`
  currently conflates stance/focus/run — they need a SLOT (the imperative word) to separate, which is
  ordinary declaration work.
- **THE ARGUMENT FOR, in this project's own terms:** forms FAIL SILENTLY by not matching; the grammar
  REFUSES loudly and detects ambiguity. Nine surfaces on forms is nine places a near-miss quietly
  does nothing — §10a's exception-dropping bias in another costume.
- **STILL TO WEIGH: COST.** Forms are cheap; the grammar costs a `load_grammar` (see the profiling
  block) plus ms/utterance. Every surface moved onto it pays that.
- Probe: scratch (surface sweep + combined-grammar ambiguity run).

**SEQUENCE: domination gating FIRST — DONE. Conditionality — DONE, by deletion plus the fix above.
Attribution's substrate — PROBED AND GENERALIZED.** Next, in order:
1. ~~**Conditionals** — an `implies` verb~~ **DROPPED 2026-07-20, and that is the RESULT, not a
   deferral.** The explicit core form already ships and routes correctly; `implies` would be sugar
   over it. Revisit only if the residue log shows a translator wanting it.
2. **Attribution** — a clause-as-complement production plus a holder-keyed scope. **SUBSTRATE PROBED
   END TO END AND VERIFIED SOUND 2026-07-20** (see the block below), so what remains really is
   declarations. `Band` generalized ahead of it (also below).
3. **Multi-guard `unless`** — INDEPENDENT cleanup that would retire `hclause`. `hclause` is not
   wrong, just duplicative, so this can wait.
4. **Make READS structural, if any reader starts caring.** 54 `nodes_named` sites resolve by name and
   currently work by ABSENCE (a token carries no content) rather than by redirect. Harmless while
   the fold is the only writer; the same `_through_denotation` collapse is the fix if that changes.

STILL NOT SHIPPED IN `corpus/loudon_grammar.cnl`, and now permanently: the conditional productions
live only in the tests, and with `implies` dropped there is no reason to move them. A conditional is
said in the CORE rule surface (`?x is dangerous when ?x is hungry`), which never enters the grammar
route at all. **The suppression gate stays** — it is built, tested, and attribution needs it, since
attribution's complement genuinely is a nested clause.

**Follow-up CLOSED by the drop:** the note here said a gated conditional reports `fact` while writing
nothing, and that `implies` would fix the verdict. With conditionals handled on the rule route ahead
of the fork, the grammar never sees one, so the mismatch cannot arise. It WOULD return if the
conditional productions were ever shipped into the grammar file without a verb — which is the reason
not to.

**Superseded — the decision this replaced (kept for the argument):** The
possibilistic layer already has the target representation (a `<hypothesis>` scope carrying a graded
`<likeliness>`, holding pencil facts) and the scale is already KB data (`uncertainty.hedge_bands`,
`X means N`). The open question is WHO turns the hedged span into a fork:

- **A rule cannot do it today.** A fork scope is `MINT` with GRADED ATTRIBUTES
  (`LIKELINESS: graded(0.7)`); a rule RHS is `Pat(s, p, o)` triples and has no way to write a graded
  attribute with a numeric value. So a `hedges` verb in the assert-declaration surface would need a
  lowering extension first.
- **Option A — a driver in the interpretation layer** calling the existing `possibility.fork_fact`.
  COMPLIANT (that helper is already an ISA program, not raw substrate poking) and small. COST: the
  slots→triple mapping (`subj pred obj` / `subj is adjc` / `subj is_a kind`) would be re-derived in
  Python, duplicating what the `clause asserts …` declarations already say — the one real smell.
- **Option B — extend the declaration surface with a `hedges` verb** (`hclause hedges subj pred obj
  when hedge`), symmetric with `asserts`/`denies`, generating one rule per hedge word (band known at
  COMPILE time from the declarations, so no runtime numeric lookup — the same per-word expansion
  `deny` already uses). Keeps ALL the fact-shaping in declarations. COST: needs the lowering to mint
  a scope with a graded attr from a rule RHS.
- **Option C — fold the hedge into the existing `either…or`/fork authoring path** in `world.py`, and
  treat the grammar route as producing input to it rather than authoring directly.
- RECOMMENDATION: **B if the lowering extension is small, else A with the mapping read off
  `gram.assertions` rather than hardcoded.** B is the only one that keeps the "domain logic ONLY in
  banks" rule intact, and a graded-attr RHS is plausibly wanted by other banded work anyway.

**WHERE THE COST SITS AFTER IT** — `parse` **0.72 s (51%)**: `ambiguity` 0.35 (48% of parse, and now
the largest single stage), `decs` 0.17, `chart` 0.12, `spans` 0.07. `interpret` **0.70 s (49%)**.
Both halves are flat per utterance now, so the session is LINEAR rather than quadratic and the next
gain is a constant-factor one — measure before assuming `ambiguity` is the target.

**Also fixed 2026-07-19: `declare_grammar` failed SILENTLY on a bad path.** A non-existent path fell
through to `load_grammar(str(...))` and was parsed AS GRAMMAR TEXT, giving an empty grammar that
refused every sentence — the failure looked like "the grammar is fast", and it cost one bogus
benchmark run before being noticed. Now raises on an unresolvable path, plus a backstop `ValueError`
for any grammar with no lexicon and no productions whatever it was built from.

**Superseded design question (kept — the argument is why the answer is better):** The loop
contradiction → ask → `discard_scope` → re-interpret is what interpretation nodes are FOR, and three
of its four pieces already exist (`contradiction_bank` runs inside `interpret`; `discard_scope`;
`culprits`). The missing piece is **how a KB declares ALTERNATIVE READINGS**. The Loudon bench gets
its two readings by string-substituting one declaration line
(`slot head in np from modifier plus np is right head` → `mint head in np from modifier plus np
under right head`), which is a bench trick, not a surface. Options to decide between: a declared
ranked list of readings in the grammar file; a reading as a named variant bank the re-interpretation
selects; or the discriminating question choosing the slot declaration directly. Do NOT invent this
silently — it decides what "re-interpret" even means.

**Then step 4 (optimize) and step 5 (retire what the fork subsumes).** Note the grammar route
inherits the "run_bank over the whole graph, once per utterance" quadratic shape — `route()` calls
`parse` (not `parse_batch`) and `interpret` re-runs over the standing surface. Fine at session
scale; MEASURE before step 4, and re-measure the step-4 levers below since the 29× `load_facts` fix
already changed the cost picture.

**Superseded resume block (2026-07-18) follows** — its option (a)/(b) question is CLOSED by the
above.

**Where the code is:** `ugm/cnl/grammar.py` (declarations → `Grammar` → `GrammarBanks` → `parse` /
`parse_batch`), `ugm/interpretation.py` (scope, `denotes`/`interprets`, `discard_scope`,
`<contradiction>`, `describe`/`intern_described`), grammars as KB files
(`corpus/lion_grammar.cnl`, `corpus/loudon_grammar.cnl`), tests `tests/test_grammar.py` (24),
benches `bench/spike_homoiconic_grammar.py`, `bench/spike_interpretation_scope.py`,
`bench/spike_loudon_grammar.py`. Designs: `design/homoiconic_grammar.md` (READ ITS §0 FIRST — §§8-12
are spike evidence), `design/surface_interpretation.md`.

**⚠ THE NEXT ACTION NEEDS A DECISION FROM THE USER — ask before building.** Integration step 2
(wire the grammar as an opt-in intake route) hits the **token/entity duality**: today the token node
IS the entity (`focus.utterance_subjects`, `anchor_has_content_fact`, `gc_utterance_scaffolding`,
every `nodes_named` lookup depend on it, and `intern_mentions` maintains it by destructively folding
same-named mentions). But `interpretation.interpret_mentions` mints a SEPARATE entity node named
`lion` beside the token also named `lion` — two nodes, one name, ambiguous lookups. Two options:

- **(a) grammar route, DIRECT fold — ~1 hour.** Lexical head is the token itself, no interpretation
  scope; facts land exactly where they do today so nothing downstream changes. Ships the coverage
  win (intransitive / negation / comparative / prepositional + REFUSE + ambiguity detection) into
  production intake. Drops the defeasible-denotation layer. **Recommended** — the hook is one block
  at `intake.py:462-468` (`_ingest_gen`'s FACT/GOAL/UNRECOGNIZED route), and exercising the grammar
  from real intake paths should surface more of what step 3 surfaced.
- **(b) grammar route WITH the interpretation scope — a session or more.** Requires resolving the
  duality across intake/focus/query, in code with no grammar tests protecting it. NOTE: a middle
  path (make the representative TOKEN be the entity, so no duplicate names) was explored and
  collapses back into (b) — it needs a consistent representative across mentions, which is exactly
  what destructive `intern_mentions` provides today and what the scope is meant to make revisable.

If (a): also decide what an AMBIGUOUS utterance returns — a new `Outcome` kind, or `unrecognized`
with distinct guidance. It should ultimately become a discriminating question via `can_ask`.

**Alternative if the user prefers not to split the layer:** skip to step 4 (optimization) and return
to integration once the duality has a plan. Step 4's measured levers: materialize the parse tree
(slot stage 81.7 → 21.7 ms, 3.8×, MEASURED) and RHS variable predicates (assert bank 86 → ~6 rules;
**the learning arc wants the same primitive**, `predicates-are-keys`). Note the 29× `load_facts` fix
below already changed the cost picture — RE-MEASURE before optimizing further.

**Not blocking but owed:** `<contradiction>` derivation is still a local stand-in
(`interpretation.contradiction_bank`); `consistency_design.md` designs the real one and remains a
SKETCH. The interpretation loop depends on it. Also `authoring.load_facts` does not strip `#`
comments though every other CNL loader does (worked around in `grammar.load_grammar`) — fix at
source.

## Current focus (re-pointed 2026-07-18 — INTAKE GRAMMAR, ahead of more learning)

**SPIKE DONE 2026-07-18, GREEN — the arc is buildable** (`bench/spike_homoiconic_grammar.py`,
results in `design/homoiconic_grammar.md` §8). **NEXT TASK: slice 1, THE FOLD** (parse → facts,
production-attached semantics), gated on subsuming `FACT_FORMS`.

What the spike settled, in one paragraph. A grammar declared in CNL (lexicon `lion is a noun`,
unchanged shipped surface + ONE new production form pair `np expands to determiner plus np`)
generates chart rules that run on `run_bank` with NO engine change. **Token-passing IS chart
parsing** — a chart is exactly "every enabled rule fires, nothing selects" — so the §3 crux was a
false alarm at the level of the control regime. All five residual Loudon failures now parse
(intransitive, negation+modifier, prepositional, comparative), including `the guzerat lion has no
mane` — the exception-bearing sentence the whole re-point was about — and `glorp the flarn` is
REFUSED. **Ambiguity is detectable in-engine with no branch selection**: not by counting root
spans (that silently reports "unambiguous" — packing erases derivation identity), and not by an
unpacked forest (correct but 5.2 s at 11 tokens), but by a generated top-down USEFULNESS pass plus
a `Distinct` on the split point — exact on the PP-attachment case, zero false positives, 41 rules.
Open vocabulary works and refusal survives it (one NAC rule over declared closed classes; also
cheaper). Cost 15-41 ms/utterance against a ~12 ms budget, on an unmemoized bank.

**SLICE 1 (THE FOLD) DONE 2026-07-18** — `bench/spike_grammar_fold.py`, design §9. Semantics is
CNL too (`slot head in np from determiner plus np is right head`; `clause denies subj pred obj
when neg`) — 68 CNL lines, 206 generated rules, no Python escape hatch, so **§5.4 answers "no
second system"** on the evidence available. The architectural move: the chart stays PACKED while
parsing and identity is minted only for the spans the usefulness pass says survive — O(n), so
slots get nodes to hang on without paying for the unpacked forest. `the guzerat lion has no mane`
now writes **`(lion has_not mane)`** — the exception the learner needed and never got. The
ambiguous sentence writes NOTHING and asks, where today's bank writes three wrong facts.

**§7 RESOLVED 2026-07-18** — `bench/spike_grammar_subkind.py`, design §10. The dichotomy was
FALSE: the choice was never "decompose onto the head" vs "an opaque `african_lion` string". A
modified NP mints a distinct NAMELESS node whose identity is its DESCRIPTION — `<e> is_a lion`,
`<e> is guzerat` — so decomposition stays completely intact (both questions still answer) and only
the node carrying it changes. Nameless is the precedent, not an exception: feedback #15's
`ByDesc`/`_find_skolem_witness` identity law already says a minted node has no name, only its
defining relations. **One declaration line** carries it (`mint head in np from modifier plus np
under right head`). Payoff beyond tidiness: `lion has mane` and `<e> has_not mane` now stand on
different nodes linked by `is_a`, so the exception is a REACHABLE counterexample to
`?x has mane when ?x is_a lion` — the structure the defeasible-exception arc has been missing was
a grammar problem all along. Cost: interning must become description-keyed (`intern_described`,
the counterpart to the name-keyed `intern_mentions`, which is structurally blind to nameless
nodes) — and that is REQUIRED for correctness, not tidiness, because RHS-only value invention
re-mints on every bank run (10 nodes → 1 on a 3-sentence corpus).

**INTEGRATION STEP 1 DONE 2026-07-18 (suite 705 green).** The machinery moved out of `bench/` into
`ugm/cnl/grammar.py` (declaration forms, `Grammar`/`GrammarBanks`, chart/ambiguity/span/slot/assert
generation, `parse`) and `ugm/interpretation.py` (scope, `denotes`/`interprets`, `discard_scope`,
contradiction marker, `describe`/`intern_described`); the grammar itself is now a real KB file,
`corpus/lion_grammar.cnl`; behaviours pinned by `tests/test_grammar.py` (22 tests). The two spikes
whose content had entirely moved were DELETED; the two that remain keep only the measurements that
decided design questions and import the modules (output verified byte-identical). **No existing
path changed** — nothing calls the grammar yet, which is why the suite stayed green.

**INTEGRATION STEP 3 DONE 2026-07-18 (suite 706 green)** — the grammar met the Loudon corpus
(`bench/spike_loudon_grammar.py`, `corpus/loudon_grammar.cnl`, design §12). **19/19 (100%) parsed
on the FIRST pass**, 0 refused, 0 ambiguous, 28.5 ms/line; the grammar needed three new
constructions (predicative adjective, copula+NP subsumption, a second preposition), all
declarations, no Python. The KB now holds the generalization AND its counterexample on distinct
`is_a`-linked entities; the same corpus derives **1 contradiction under the percolating reading and
0 under minting**. Caveat: these are the 19 CNL lines an LLM produced from the 50 sentences, not
the sentences.

**⚠ SHIPPED-CODE DEFECT FOUND AND FIXED: `load_facts` was QUADRATIC in batch size.**
`authoring._recognize` ran `normalize_surface` once per sentence, but that ignores its `anchor` and
runs each stratum over the WHOLE graph to fixpoint — N sentences = N global fixpoints over a graph
growing with N. 26 ms/line at 10 lines, 161 ms/line at 80; an 85-line KB file took 24 s. Hoisted to
ONE batch pass: per-line cost FLAT ~5 ms, 80 lines **12.9 s → 0.44 s (29×)**, and the whole test
suite 78 s → 42 s. This bites `load_facts`/`load_corpus`/`load_kb` equally — the grammar arc only
exposed it. GENERAL LESSON (it recurred immediately in the new code, fixed with `parse_batch`):
**"run_bank over the whole graph, once per utterance" is quadratic by construction.**

Also fixed: **identity must be settled before predication** — an acquired fact (`the african lion
is strong`) leaked into a minted entity's DESCRIPTION and stopped it interning with the same
subkind elsewhere, because NP-level attribution and clause-level predication both write `is`.
Assertions in a MINTING category are now DEFINING, run first, then interning, then everything else.

**Integration steps 2, 4, 5:** (2) wire as an OPT-IN intake route — a KB that declares a grammar gets
the grammar path, everything else keeps the shipped forms (declare-before-use, so the suite stays
green by construction); (3) **run the real corpora** — Loudon's 50 sentences first: all coverage so
far is on 7 hand-picked sentences chosen to exercise known gaps, so expect this to be sobering, and
it will force the question of WHO WRITES THE GRAMMAR for open prose (loops back to the learning
arc's T3 form learning); (4) optimize; (5) retire what it subsumes. Step 3 needs `<contradiction>`
derivation, which `consistency_design.md` sketches but does not build.

**Optimizations, when step 4 arrives:** (1) ~~**materialize the parse tree**~~ **DONE 2026-07-19 —
see the step-4 block above.** Diagnosis confirmed (all 32 slot rules redid the same 6-way
parent/child join; the stage was 88.5% of interpretation), but the prescription needed one change:
NOT flat `?p kidL/kidR` edges, which mispair children of a packed span, but a REIFIED decomposition
node. Result 17× on the stage, better than the 3.8× predicted here. ~~Second lever: the assert stage
is 86 rules only because a slot-valued predicate expands per lexicon word~~ **ALSO DONE 2026-07-19
(133 → 33 on the Loudon grammar; see the second-lever block above)** — `MINT.key_reg` plus
`lower_rhs` accepting an LHS-BOUND predicate variable. Landed the LEARNING ARC's shared primitive
(`predicates-are-keys`) in its first slice; predicate INVENTION (an RHS-only predicate variable)
stays rejected. The DENY case still expands per word and needs the negative-predicate pairing as
graph data to finish; (2) ambiguity → discriminating question
via `can_ask`; (3) restrictive vs non-restrictive modification — minting is currently unconditional,
which is weaker rather than wrong but loses the merge's free coreference; route on the existing
`declared_definites`/`is_unique` machinery (UNTESTED); (4) declaration loudness (a malformed `slot`
line still fails silently); (5) compare against `comparative.py` before claiming full subsumption.

**SURFACE / INTERPRETATION SPLIT — spiked 2026-07-18** (`bench/spike_interpretation_scope.py`,
design §11; user proposal). The sentence's nodes are the permanent monotone record; every
JUDGEMENT about what it MEANS (denotation, coreference, subkind-vs-same-entity) lives in a SCOPE of
COPIES with provenance back to the surface. **Inside the scope the merge stays destructive** — one
node per entity, no `same_as` clique, no representative hop — because reversal is never needed:
discard and re-derive. Demonstrated end to end: 2 sentences parsed ONCE (231 surface nodes) →
interpretation A percolates → `lion has mane` + `lion has_not mane` → `<contradiction>` derived →
provenance shows the entity came from 2 surface mentions, so a JUDGEMENT is in the support → ASK →
discard scope (90 nodes, 231/231 surface intact) → interpretation B mints a subkind → 0
contradictions, no re-parse. **The system discovers the reading was wrong instead of being told** —
which removes §10's requirement that the domain author know the right reading in advance.

**This is also the answer to the substrate-layering question.** A `<stratum>` node attribute was
the wrong shape because the strata on offer were ENGINEERING distinctions (control vs fact) while
the failures were reading rules over legitimately shared nodes. Observation vs inference is
EPISTEMIC, is exactly two layers, and decides membership unambiguously. Key finding: the line is
not "which node it hangs on" but "structure vs denotation" — the surface is tokens, chains and
`cat`/`begin`/`end`, and every slot/`denotes` edge is interpretation even when written onto a
surface span. Open before this is production: copy-on-WRITE scope (materialized today — at session
scale it must be a delta over `OVERLAY` or it shadows the whole KB); PROMOTION of uncontested
interpretations (same mechanism as promotion-by-survival for rules); enforcing ONE live
interpretation (else branch selection returns); culprit selection when the support holds several
judgements; and reusing `suppose`/`SCOPE` (noting this is a STANDING scope, not a hypothesis fork).

**Substrate layering (user question, 2026-07-18):** the fold slice hit TWO accidental cross-layer
reads — `is_a <mention>` polluting the lexicon (152 rules instead of 30, ~80% of runtime) and a
CNL `yes` token being deleted by `authoring._recognize`'s scaffolding strip. Both are name-keyed
GLOBAL partitions leaking into user data (a shared PREDICATE; a reserved NAME). Neither would have
been caught by a node-level `<stratum>` tag — in both cases the node was legitimately shared and
the *reading rule* had no business seeing it. Design note in §9.5; decide after the memoization
pass, against this incident list rather than speculatively.

Original framing of the task, kept because the argument is what selected it:

Why this and not the next learning slice — a real-corpus test redirected the plan. The learning arc
landed (S1, S1b, S3a, S5, S6; `design/learning_design.md`), and was then run against 50 verbatim
sentences of a real natural-history book (`bench/spike_loudon.py`, `bench/loudon_lion_corpus.py`).
Three results, in ascending order of importance:

1. **Real prose is 26% facts.** 13/50 sentences assert anything extractable; the rest is anecdote,
   quoted narrative, hedged attribution. That is the SOURCE's property, not a defect.
2. **Intake was 0%, and it was a WIRING gap.** `surface_forms` (determiner stripping + noun-phrase
   decomposition) ran on the question path and the loose-rule path but never on the FACT path.
   Wiring it into `authoring._recognize` took routed coverage 0% → 79%; 7.1 → 11.2 ms/utterance
   after memoizing the strata. `tests/test_intake_surface_facts.py`.
3. **PARTIAL INTAKE COVERAGE IS NOT NEUTRAL — this is what re-points the plan.** Exceptions are
   LINGUISTICALLY MARKED ("without any mane", "no", "unlike", "except"), and those are exactly the
   constructions a bare S-P-O form bank drops. The corpus states a real generalization (lions have
   manes) AND its real exception (the Lion of Guzerat has none); the learner proposed the
   generalization and the exception never reached the KB, because that sentence is the one that
   would not parse. A partially-covering parser does not lose sentences at random: it loses the
   EXCEPTIONS and keeps the GENERALIZATIONS, biasing everything downstream toward confident
   over-generalization.

So more learning machinery on top of partial intake produces optimistically-biased results, and the
defeasible-exception work has no data to run on. **Intake first.**

And 79% is ROUTING, not correctness — two silent defects are pinned as tests:
`the lion lives in africa` ROUTES as a fact and folds to `('lives','is','lion')` (an undeclared verb
absorbed by NP-decomposition — worse than the unrecognized case it replaced), and
`the guzerat lion has no mane` is unrecognized yet still writes `lion is guzerat` (an unrecognized
line is not inert, and the dropped part is the negation). Both are the "quietly does something
wrong" class that S1/S1b spent the session eliminating — which is the argument for the grammar.

### Then (unblocked, in the learning arc)
- **§7.3 rule revision** + the **defeasible-exception model** (user-agreed: refutation should record
  an exception, not delete a good rule). Blocked on intake for DATA, not for mechanism.
- **Promotion by survival** — counting survived/failed discriminating questions as rule attributes
  (user's idea; auditable, unlike frequency). Decide defeasible-vs-fatal refutation FIRST, or the
  fatal model gets baked in.
- **S2/S2b/S2c** — the dialogue surfaces (Caveman CNL T1, the T3 alignment spike, and the
  discriminating question, which is the bootstrapping engine and serves both halves of the arc).

## Current focus (SUPERSEDED — re-pointed 2026-07-16, Phase 8's engine side is COMPLETE)

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
   Book DONE (ch. 7 "You can teach it new shapes"). Remaining: optional Slice C (exemplar sugar).
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
   **Slice 1 DONE 2026-07-16 (569 green)** — `corpus/procedure.cnl` (3 content-blind rules:
   invoke/order/gap-fill) rides the existing planner gate unchanged; first in-repo end-to-end
   planner run (`tests/test_procedures.py`). FINDING: `intake._act_loop` uses unstratified
   `run_bank` and must stratify to run the NAC-heavy planner gate — a Slice-2 wiring item.
   Remaining: Slice 2 (`to NAME :` surface + `<run> proc` request + act-arm stratification).
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
