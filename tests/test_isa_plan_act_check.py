"""
Phase 5.5 slice 4 — plan -> act -> check -> replan as a KB-DECLARED control-token program.

This is the demonstration that RETIRES `solve.py`'s Python-hardcoded driver. `run_to_goal` held the
plan-execution control flow in a Python `for _ in range(max_cycles)` loop with hardcoded predicate
NAMES straight in the control flow (`graph.name(r) == "want"/"add"/"chosen"/"ready"/"done"`) — the
standing-rule violation ("domain logic ONLY in banks; strategies are DECLARED data, never engine
sniffing"), the same shape-sniffing anti-pattern Phase 5.4 eliminated for the walker/coref strategies.

Here the ENTIRE loop is DATA: a handful of forward rules serviced by the EXISTING `<call>` loop
(`run_bank(..., tools=mode_registry(rule_g))`, `mode_calls.py`) — no new driver, no Python control
flow, no predicate NAME baked into engine code. The planning vocabulary (`want`/`add`/`chosen`/`done`/
`observed`/`achieved`/`diverged`/`reached`) is whatever THESE rules and the `act` tool declare it to
be, exactly as `processing_modes.md` §3 prescribes: "try-per-plan -> check -> replan = ITERATE over the
expected-effect list x CHECK each against observed facts."

The three control-flow elements `run_to_goal` hardcoded, now each a rule (or a §8 CALL):
  - ACT  (`_perform_op`/`simulate_effects`)  -> an `act` CALL: the world boundary materializes an op's
    OBSERVED effects (or withholds them — a divergence). Acting is a CALL (§8), not Python control flow.
  - CHECK (`goal_satisfied`/`_diverged`)      -> a CHECK CALL per wanted effect; the `<check>` verdict
    feeds back as matchable control relations (`<check> -[of]-> effect`, `-[status]-> STATUS`).
  - REPLAN (`_replan` driver-state reset)     -> a rule that COMMITS an alternative op on a divergence.

KEY RESULT (the teardown-subsumed story, again): the composition is MONOTONE and needs NO reset. Each
op's CHECK is fired-suppressed per (op, effect), so an alternative op contributes its OWN positive
verdict independently of the diverged op's stale assumed-no verdict — nothing to tear down, exactly as
Phase 2/3 found `DROP_CTRL`/`planning_teardown.cnl` subsumed. `run_to_goal`'s "reset driver state and
re-derive" is Python machinery the monotone substrate makes unnecessary.
"""
import ugm as h
from ugm import Pat, Rule
from ugm import AttrGraph, run_bank, derived_triples, mode_registry
from ugm.dispatch import call_arg


# The plan-state marker object: a control token (reserved `<...>`), so a rule producing `?op chosen
# <plan>` mints a CONTROL relation — plan bookkeeping stays out of the monotone fact layer.
PLAN = "<plan>"


def _has(g: AttrGraph, s: str, p: str, o: str) -> bool:
    return (s, p, o) in derived_triples(g)


def _ensure(g: AttrGraph, name: str) -> str:
    found = g.nodes_named(name)
    return found[0] if found else g.add_node(name)


# --- the loop, authored as forward rules (the control flow `run_to_goal` hardcoded, now DATA) -----

# ACT: for each chosen, not-yet-acted op, emit an `act` CALL — the §8 world boundary. WHICH op acts
# and WHEN is decided by this rule (data); the dispatcher stays content-blind.
EMIT_ACT = Rule(key="emit.act",
                lhs=[Pat("?op", "chosen", PLAN)], nac=[Pat("?op", "done", PLAN)],
                rhs=[Pat("<call>?", "tool", "act"), Pat("<call>?", "op", "?op")])

# CHECK: once an op has acted, CHECK each goal-want against the OBSERVED facts (copula goal `?e is
# observed`; `pred` defaults to `is`) — every want, not just the acted op's base adds, so a DERIVED
# effect (test 4's bridge) is caught, the faithful analog of `goal_satisfied` scanning all wants after
# acting. Fired-suppression keys this per (op, want), so each op contributes at most one verdict per
# want — the reason no reset is needed between plans (a later op re-checks with a fresh binding-sig).
EMIT_CHECK = Rule(key="emit.check",
                  lhs=[Pat("<goal>", "want", "?e"), Pat("?op", "chosen", PLAN),
                       Pat("?op", "done", PLAN)],
                  rhs=[Pat("<call>?", "tool", "check"), Pat("<call>?", "subj", "?e"),
                       Pat("<call>?", "obj", "observed")])

# REACT (positive): a positive verdict for a wanted effect marks it achieved.
ACHIEVE = Rule(key="react.achieve",
               lhs=[Pat("?v", "of", "?e"), Pat("?v", "status", "positive")],
               rhs=[Pat("?e", "achieved", PLAN)])

# REACT (assumed-no): an assumed-no verdict is the plan-check MISMATCH — a divergence.
DIVERGE = Rule(key="react.diverge",
               lhs=[Pat("?v", "of", "?e"), Pat("?v", "status", "assumed-no")],
               rhs=[Pat("?e", "diverged", PLAN)])

# REPLAN: on a divergence, COMMIT an alternative op that adds the diverged effect and has not already
# run. The selection-as-data; the loop then acts + checks the alternative. (`run_to_goal`'s `_replan`.)
REPLAN = Rule(key="replan.commit",
              lhs=[Pat("?e", "diverged", PLAN), Pat("?alt", "add", "?e")],
              nac=[Pat("?alt", "done", PLAN)],
              rhs=[Pat("?alt", "chosen", PLAN)])

# GOAL: reached when a wanted effect is achieved (single-want demo; multi-want forall is the ITERATE
# domino over a reified want-list — Phase 3.4's collection substrate, not this slice).
REACHED = Rule(key="goal.reached",
               lhs=[Pat("<goal>", "want", "?e"), Pat("?e", "achieved", PLAN)],
               rhs=[Pat("<goal>", "reached", PLAN)])

LOOP = [EMIT_ACT, EMIT_CHECK, ACHIEVE, DIVERGE, REPLAN, REACHED]


def act_tool(withheld: frozenset[str]):
    """The §8 act/observe boundary (the declared-data analog of `solve._perform_op`). Reads the `op`
    slot, materializes the op's declared `add` effects as OBSERVED facts (`?e is observed`), and marks
    the op `done`. A `withheld` op acts but its effect is NOT observed — the divergence a real action
    tool (or `run_to_goal`'s `failures`) would produce. The world decides the outcome; the rules that
    emitted the call decide only WHICH op and WHEN."""
    def handler(g: AttrGraph, call_id: str) -> set[str]:
        op_id = call_arg(g, call_id, "op")
        if op_id is None:
            return set()
        touched: set[str] = set()
        if g.name(op_id) not in withheld:
            for r, e in g.relations_from(op_id):
                if g.name(r) == "add":                          # the op's declared effect (a fact)
                    touched.add(g.add_relation(e, "is", _ensure(g, "observed")))
        touched.add(g.add_relation(op_id, "done", _ensure(g, PLAN)))   # the op acted
        return touched
    return handler


def _world(withheld: frozenset[str]):
    """Two routes to `at_goal`; `route_A` is the seeded plan. Returns (graph, registry)."""
    g = AttrGraph()
    goal = g.add_node("<goal>")
    at_goal = g.add_node("at_goal")
    route_a = g.add_node("route_A")
    route_b = g.add_node("route_B")
    g.add_relation(goal, "want", at_goal)          # the goal (fact)
    g.add_relation(route_a, "add", at_goal)        # operator effects (facts)
    g.add_relation(route_b, "add", at_goal)
    g.add_relation(route_a, "chosen", g.add_node(PLAN))   # the initial plan (seeded; selection is CHOOSE)
    # CHECK's backward bank is empty here — the observation is a base fact, so `check` resolves it by
    # presence alone (the derived-effect bridge is exercised separately below). `act` is a domain CALL
    # composed into the SAME registry as the firmware modes.
    registry = {**mode_registry(AttrGraph()), "act": act_tool(withheld)}
    return g, registry


# --- 1: the happy path — plan -> act -> check -> reached, entirely as data, no Python driver -------

def test_plan_act_check_reaches_the_goal_with_no_driver():
    g, registry = _world(withheld=frozenset())          # route_A acts reliably
    run_bank(g, LOOP, tools=registry)

    assert _has(g, "at_goal", "is", "observed")          # the act materialized the observation
    assert _has(g, "at_goal", "achieved", PLAN)          # the CHECK verdict fed back positive
    assert _has(g, "<goal>", "reached", PLAN)            # the goal is reached
    assert not _has(g, "at_goal", "diverged", PLAN)      # no mismatch on the happy path
    assert not _has(g, "route_B", "chosen", PLAN)        # no replan needed
    assert g.nodes_named("<call>") == []                 # every act/check call was consumed


# --- 2: divergence -> replan -> reached, still entirely as data --------------------------------------

def test_divergence_drives_a_replan_onto_the_alternative():
    g, registry = _world(withheld=frozenset({"route_A"}))   # route_A acts but its effect is withheld
    run_bank(g, LOOP, tools=registry)

    assert _has(g, "at_goal", "diverged", PLAN)          # the assumed-no verdict fed back as a mismatch
    assert _has(g, "route_B", "chosen", PLAN)            # the replan rule committed the alternative
    assert _has(g, "at_goal", "is", "observed")          # route_B's act produced the observation
    assert _has(g, "at_goal", "achieved", PLAN)          # its independent CHECK fed back positive
    assert _has(g, "<goal>", "reached", PLAN)            # the goal is reached after the replan
    assert g.nodes_named("<call>") == []


# --- 3: no reset needed — the monotone substrate subsumes `run_to_goal`'s driver-state teardown -----

def test_replan_needs_no_teardown_the_stale_verdict_is_inert_control():
    g, registry = _world(withheld=frozenset({"route_A"}))
    run_bank(g, LOOP, tools=registry)

    # Both verdicts coexist harmlessly: route_A's stale assumed-no AND route_B's positive. The
    # positive one drives achievement; the stale one is never torn down (it is control, fact-invisible).
    from ugm.mode_calls import check_results
    statuses = sorted(r["status"] for r in check_results(g) if r.get("subj") == "at_goal")
    assert statuses == ["assumed-no", "positive"]        # no reset — both survive, monotone
    assert _has(g, "<goal>", "reached", PLAN)


# --- 4: the derived-effect bridge — CHECK resolves an observation DERIVED by the rule bank ----------
#        (`run_to_goal`'s ONE integration point: `_observe_simulated` reads base + DERIVED adds). Here
#        the wanted effect `won` is not observed directly; a bridge rule derives it from `trophy is
#        observed`, and CHECK (chain over rule_g) finds it — the same CHAIN the whole firmware uses.

def test_check_resolves_a_derived_observation_via_the_rule_bank():
    rule_g = AttrGraph()
    h.write_rule(rule_g, Rule(key="bridge",
                              lhs=[Pat("trophy", "is", "observed")],
                              rhs=[Pat("won", "is", "observed")]))
    g = AttrGraph()
    goal = g.add_node("<goal>")
    won = g.add_node("won")
    celebrate = g.add_node("celebrate")
    g.add_relation(goal, "want", won)
    g.add_relation(celebrate, "add", g.add_node("trophy"))   # op adds `trophy`, not `won` directly
    g.add_relation(celebrate, "chosen", g.add_node(PLAN))
    registry = {**mode_registry(rule_g), "act": act_tool(frozenset())}

    run_bank(g, LOOP, tools=registry)

    assert _has(g, "trophy", "is", "observed")           # the base effect the act materialized
    assert _has(g, "won", "is", "observed")              # DERIVED by the bridge during CHECK's chain
    assert _has(g, "won", "achieved", PLAN)              # the derived observation fed back positive
    assert _has(g, "<goal>", "reached", PLAN)
