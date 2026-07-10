# ISA coverage map — the card-trader banks against the opcode set

> **The ISA arc, Phase 0 (coverage map) + Phase 1 (predicate-NAC) + Phase 2 (existential NACs /
> `DROP_CTRL` subsumed), 2026-07-06.**
> The plan (handoff "Next step"): migrate the shipped reasoning onto the label-less / goal-directed
> machine (`harneskills/isa/`), using the card-trader banks + scenario harness as a DIFFERENTIAL-TEST
> ORACLE, so domain reasoning has *nowhere to hardcode* (a domain-blind machine + a dumb lowering).
> This doc is the Phase-0 map: every card-trader bank's rules against the opcode set
> (`SEED`/`FOLLOW`/`JOIN`/`GRADE`/`FUZZY`/`MINT`/`EMIT`/`DROP_CTRL`) and the NAC shapes, with each
> row marked COVERED (pre-arc), PHASE 1 (done this session), or PHASE 2/3 (remaining).
>
> Read `isa-reference.md` (the opcode semantics + the honest verdict) and `rule-isa-design.md`
> first. The ISA is the "make hardcoding STRUCTURALLY IMPOSSIBLE" move: with CNL → a dumb lowering
> → a fixed generic machine, all domain content MUST be CNL rules — the guard becomes structure.

## The opcode set (recap)

| Opcode | Role | Kind |
|---|---|---|
| `SEED` | enumerate nodes by key (rarest-anchor) | match |
| `FOLLOW` / `JOIN` | pointer-register edge cursor / follow-then-test | match |
| `TEST` / `SAME` | crisp filter / register unification (repeated var) | match |
| `GRADE` / `FUZZY` | graded α-cut on a bound reg / graded seed | match |
| `MINT` / `EMIT` | reify a relation-or-node / monotone fact write | effect |
| `DROP_CTRL` | delete a CONTROL edge (refuses a fact edge) | effect |

Negation is **not** an opcode (no `CHECK-ABSENT`): a NAC is materialized as a positive `R_not` fact
and matched with `SEED`/`TEST` — the decide line. Aggregation is **not** an opcode (it folds across
the state stream) — a `<call>` calculator, by design. Neither is exercised the way that matters here:
the card trader has no aggregation, and ranking is discrete/structural.

## Bank-by-bank coverage

Legend: **✅ covered** (positive/graded fragment already reproduced, `test_isa_lowering.py` /
`test_isa_goal*`), **🟩 Phase 1/2** (predicate-NAC completion + existential-NAC emptiness checks + `DROP_CTRL` subsumed,
done), **🟧 Phase 3** (goal-directed planner + the `chosen` selection), **⬛ tool** (`<call>`, outside
the machine).

### `corpus/policy.cnl` — deontic prohibition + defeasible override

| Rule (abbrev.) | Shape | Opcodes / status |
|---|---|---|
| `?act overridden <yes> when forbidden ?lo and encouraged ?hi and ?hi outranks ?lo` | positive 3-clause join | ✅ SEED/FOLLOW/JOIN/MINT |
| `?o excluded <yes> when ?o is_a ?act and ?act forbidden ?src and **not ?act overridden <yes>**` | +ground-object NAC, subj bound | 🟩 `overridden_not` completion |
| object-scoped `?n overridden <yes> when ?n polarity forbidden … ?hi outranks ?lo` | positive multi-clause join over reified `<norm>` nodes | ✅ (norm nodes MINTed at load; rule is positive) |
| object-scoped `?o excluded <yes> when … and **not ?n overridden <yes>**` | +ground-object NAC, subj bound | 🟩 `overridden_not` completion |

### `corpus/preference.cnl` — discrete deontic ranking

| Rule (abbrev.) | Shape | Opcodes / status |
|---|---|---|
| `encouraged outranks neutral` (×3 tier facts) | bodiless facts (data) | ✅ base facts |
| `?o stance encouraged when ?o is_a ?act and ?act encouraged ?src` (+`discouraged`) | positive 2-clause join | ✅ |
| `?o stance neutral when ?o add ?c and **not ?o stance encouraged and not ?o stance discouraged**` | +TWO ground-object NACs, subj bound (the DEFAULT) | 🟩 `stance_not` completion ×2 |
| `?o dominated <yes> when ?o viable … ?x viable … ?s2 outranks ?s1` | positive 6-clause self-join (`?o`/`?x`) | ✅ SAME (repeated var) |

### `corpus/risk.cnl` — graded risk-appetite α-cut

| Rule (abbrev.) | Shape | Opcodes / status |
|---|---|---|
| `?o excluded <yes> when caution is high and ?o add ?c and ?o is slightly risky` (×3 levels) | positive + GRADED condition, no NAC | ✅ GRADE (α-cut = `graded_degree`, `test_isa_goal_graded`) |

### `corpus/cards_reasoning.cnl` — deductive business semantics

| Rule (abbrev.) | Shape | Opcodes / status |
|---|---|---|
| `?c is valuable when ?c is rare and ?c is in_demand` | positive copula conjunction | ✅ |
| `?c is premium when ?c is valuable and ?c is mint`; `?c is worth_holding when ?c is premium` | positive multi-step | ✅ |
| `market is hot when demand is high and supply is low` | positive conjunction | ✅ |
| `sell encouraged today when market is hot` | positive; HEAD is a deontic fact (just a MINT) | ✅ |

### `corpus/planning.cnl` — the planner (15 rules): the heavy bank

| Rule (abbrev.) | Shape | Opcodes / status |
|---|---|---|
| `<need> for ?c when <goal> want ?c`; `<need> for ?p when candidate … pre` | positive | ✅ |
| `?o candidate ?c when <need> for ?c and ?o add ?c and **not ?o excluded <yes>**` | +ground-object NAC | 🟩 `excluded_not` completion |
| `?c reachable <yes> when <now> true ?c`; `reachable when viable+add` | positive | ✅ |
| `?o blocked_by ?p when candidate … pre ?p and **not ?p reachable <yes>**` | +ground-object NAC | 🟩 `reachable_not` completion |
| `?o viable <yes> when candidate ?g and **not ?o blocked_by ?anyp**` | +**variable-object NAC** (¬∃p) | 🟩 Phase 2: ¬∃p emptiness check |
| `drop ?o blocked_by ?p when blocked_by ?p and ?p reachable <yes>` | **control retraction** | 🟩 Phase 2: DROP_CTRL **SUBSUMED** (inert on the goal path — no stale block asserted) |
| `?o cost_settled <yes> when viable and **not ?o needs_price <yes>**` | +ground-object NAC | 🟩 |
| `<call>? tool rank … when cost_settled and **not ?o ranked <yes>**` | +ground NAC + `<call>` tool | 🟩 NAC / ⬛ tool (rank calculator) |
| `?o dominated <yes> when viable … ?x cheaper_than ?o` | positive self-join | ✅ (needs `cheaper_than` from the rank ⬛ tool) |
| `?o best <yes> when viable and cost_settled and **not ?o dominated <yes>**` | +ground-object NAC | 🟩 |
| `?o chosen <yes> when <need> for ?c and best and add ?c and **not ?x chosen <yes> and not ?x add ?c**` | +**grouped NAC on OWN head** (¬∃x SELECTION) | 🟩 Phase 3: driver resolution chain (preferences → KB `tie_break` `<call>` → deterministic-arbitrary) |
| `?o1 before ?o2 when chosen … chosen … add ?c … pre ?c` | positive self-join | ✅ |

## The frontier, precisely

**Phase 1 (DONE this session) — ground-object, body-bound-subject predicate NACs.** `isa/goal.py`
`_lower_nac` + `_complete_negative` generalized from the copula (`is`/`is_not`) to an ARBITRARY
relation: `not ?s R o` → positive body clause `?s R_not o`, completed by a nested-complete-solve of
`R(s, o)` (the copula being just `R = is`). This covers the BULK of the card-trader NACs —
`overridden`, `stance`, `excluded`, `reachable`, `needs_price`, `ranked`, `dominated`, `best`.
Differential-tested against the STRATIFIED forward driver (`authoring.run_rules`) on the real
`preference.cnl` stance bank and the full `policy.cnl` override bank (`test_isa_goal_predicate_nac.py`,
6 tests): the goal-directed completion reproduces the stratified answer exactly — including the
demo's keystone, `today outranks standing` → `sell overridden` → the exclusion lifted. (Note: the
oracle is `run_rules`, the stratified driver, NOT `rewriter.run`; the naive single-fixpoint driver
evaluates a NAC against a partial graph and derives the unsound `op stance neutral` alongside
`op stance encouraged` — the completion's nested-complete-solve is the goal-directed analog of
stratifying the producer below the consumer, which is what makes it sound.)

**Phase 2 (DONE 2026-07-06) — the two EXISTENTIAL NAC shapes, and `DROP_CTRL` SUBSUMED.**
`tests/test_isa_goal_existential_nac.py`. `_lower_nac` now PARTITIONS a rule's NACs: a clause with a
NAC-LOCAL free var is EXISTENTIAL (grouped by shared free var, applied per env as a demand-driven
emptiness check — `_exist_nac_blocks`/`_group_satisfiable`); a fully-bound clause stays the ground
`R_not` path. This lifts both shapes the Phase-1 slice rejected:
- **¬∃p (variable object)** — `not ?o blocked_by ?anyp`: the head fires iff `blocked_by(o, ?)` has no
  witness, the subgoal solved to completion in a nested solve.
- **grouped ¬∃x (shared free subject)** — `not ?x A and not ?x B`: grouped into ONE conjunctive
  existential (the forward engine's `not (A and B)` reading), blocked iff a joint witness exists;
  two DISTINCT free vars stay independent groups (`¬A ∧ ¬B`, either blocks).

- **`DROP_CTRL` is SUBSUMED, not needed** — the load-bearing finding. The block/unblock idiom's
  `drop ?o blocked_by ?p …` exists only to RETRACT a block the forward engine asserts prematurely;
  on the demand path `blocked_by` is computed against COMPLETE reachability, so no stale block is ever
  asserted and the `drop` rule (empty rhs) is INERT. DIFFERENTIAL-TESTED against the ACTUAL planner
  driver — the repeat-`run_rules`-until-stable loop of `planning.plan`, where `drop` IS load-bearing —
  the goal solver reproduces the loop's final `viable`/`reachable` exactly, `blocked_by` empty in both.
  (A single stratified `run_rules` sweep under-derives; the mutual viable↔reachable recursion needs the
  loop, which is why the loop is the oracle, not a lone sweep.)
- **The one Phase-3 residual, isolated** — the `chosen` commit rule's grouped NAC references its OWN
  head (`not ?x chosen …`): a non-stratified SELECTION the forward engine resolves by commit-ORDER,
  not completion. `_lower_nac` REJECTS it (a grouped existential NAC whose predicate == a head
  predicate). Loading the WHOLE `corpus/planning.cnl` bank raises on exactly this one rule — every
  other rule lowers — so Phase 3's remaining scope is precisely operational choice for `chosen`.

**Phase 3 CORE (DONE 2026-07-07) — the goal-directed planner.** `harneskills/isa/solve.py`
(`derive_plan` + `run_to_goal`; `tests/test_isa_solve.py`). The forward-fixpoint loop is replaced by
`GoalSolver` demand-forward: a goal PULLS only its AND-OR chain (measured — goal-directed `reachable` is
a STRICT SUBSET of forward's; it never saturates the goal fact). The `chosen` SELECTION is the ratified
resolution CHAIN — preferences (the `dominated`/`best` CNL) resolve a unique best DETERMINISTICALLY (the
selection mostly SUBSUMED); a genuine tie → a KB-prescribed `tie_break` `<call>`; else a deterministic-
arbitrary pick (stable order, not RNG). The whole control-TEARDOWN bank (`planning_teardown.cnl`, 15
gated drops) is SUBSUMED: control (`chosen`/`done`/viable/ready/…) is DRIVER-held and injected into a
fresh per-cycle `AttrGraph`, so the persistent graph stays purely monotone and a replan is a driver-state
reset (the `DROP_CTRL` subsumption of Phase 2, now for the entire replan machinery). Differential-tested
vs `planning.solve` — happy → `done`, withheld-effect divergence → replan → `done`, dead goal → `stuck`.

**Phase 3 REMAINDER (DONE 2026-07-07) — the tool boundary + the non-toy stress case.** (1) The rank
`<call>` tool serviced GOAL-DIRECTED: `GoalSolver` gained a `tools` registry (a TOOL-BACKED relation → a
calculator run ONCE on first demand); `cheaper_than` is backed by `rank_cheaper_than`, so a `dominated`
subgoal demands the ordering → the tool mints it → `dominated`/`best` complete. A COST preference (chain
step 1) breaks a tie by cost, and `examples/coffee.py` reproduces `plan()` exactly (`test_isa_solve.py`).
(2) The card-trader stress case (`test_isa_solve_cards.py`): `run_to_goal` drives the real
`cards_frontier_kb.cnl` + value→plan bridge + full `POLICY_RULES` — the bridge's DERIVED operator effect
is observed via demand-forward add-resolution (`_observe_simulated`), object-scoped deontic exclusion (a
predicate-NAC) + override work on the demand path. **The ISA arc is now SEMANTICALLY COMPLETE on the
planner**; what remains is the HONEST GATE (production parity to retire `rewriter.run`).

**Non-issues.** No aggregation in the card trader (ranking is discrete/structural), so the one thing
the ISA can't express isn't exercised. `<call>` tools (rank/price/act) stay Python calculators
OUTSIDE the machine (⬛ rows) — the `rank` tool derives `cheaper_than`, which the positive `dominated`
rule then joins on, so the tool boundary composes cleanly with the covered fragment.

## The honest gate (unchanged)

The reference machine proves SEMANTICS, not SPEED. `rewriter.run` carries the profiled
matching-bound wins (df-indexed rarest-anchor SEED, hub-flooding avoidance, semi-naïve delta
matching); dropping it from the shipped engine is gated on PRODUCTION PARITY, not on this coverage
map. Phases 2–3 are where the name-based engine does things the positive-core ISA has only shown on
smaller fragments — expect those to drive the remaining work.
