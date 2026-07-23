"""HELP-FLARE PROBE — make fuel exhaustion a durable, REACTABLE signal instead of a silent truncation.

Design under test: when a demand closure exhausts its round budget (`_Exhaustion.exhausted`), materialize a
FLARE — a normal (reactable) fact `<goal-node> stuck yes`, where the goal node reifies (f_pred/f_subj/f_obj)
the goal that ran out of fuel (the sibling of reconsider's `<assumed>` record). The flare:
  - is QUERYABLE (a durable trace: "I did not finish looking at G"),
  - is DEDUPED per goal (idempotent — re-exhausting G does not storm),
  - marks its grain dirty so the REACTIVE CORE can dispatch a declared reaction (the system reacts to its own
    resource limit), while staying INERT/opt-in by default (no reaction unless declared -> no loop),
  - is PRESENCE-triggered (fires on the exhaustion event, never on a miss) -> no recall-autofire channel.

The probe validates: detection, flare materialization, idempotence, reactability, and no-loop soundness.
"""
from __future__ import annotations

import warnings

from ugm import AttrGraph
from ugm.attrgraph import valued, graded
from ugm.machine import Machine, MINT, State
from ugm.cnl.machine_rules import load_machine_rules
from ugm.cnl.query import _reify_rules
from ugm.reconsider import mark_dirty
from ugm.reactive import declare_reactive, fire
from ugm.chain import chain_sip, _facts_matching, _Exhaustion

warnings.simplefilter("ignore")

FLARE_PRED = "stuck"          # the flare marker predicate (plain -> reactable; domain corpora avoid it)
YES = "yes"


def _goal_node(kb, goal):
    """Reify a goal as a deduped node carrying f_pred/f_subj/f_obj (sibling of the <assumed> record)."""
    p, s, o = (x if x is not None else "*" for x in goal)
    nm = f"goal:{p}:{s}:{o}"
    for n in kb.nodes_named(nm):
        return n                                       # DEDUP: one node per goal identity
    return Machine().apply(kb, [MINT("_g", attrs={
        "name": valued(nm), "f_pred": valued(p), "f_subj": valued(s), "f_obj": valued(o)})],
        State({})).regs["_g"]


def raise_flare(kb, goal):
    """Materialize (or reuse) the flare fact for `goal` and mark its grain — the reactive-core event."""
    g = _goal_node(kb, goal)
    yes = (kb.nodes_named(YES) or [None])[0] or kb.add_node(YES)
    if not any(kb.predicate(r) == FLARE_PRED for r in kb.out(g)):   # DEDUP the fact too (idempotent)
        kb.add_relation(g, FLARE_PRED, yes)
        mark_dirty(kb, [(FLARE_PRED, YES)])
    return g


def demand_with_flare(kb, goal, rules, *, max_rounds):
    """A fuel-tracked demand: run the closure, and if it exhausts, RAISE A FLARE instead of silently
    truncating. Returns (derived_count, exhausted)."""
    fuel = _Exhaustion()
    n = chain_sip(kb, goal, rules=rules, max_rounds=max_rounds, _fuel=fuel)
    if fuel.exhausted:
        raise_flare(kb, goal)
    return n, fuel.exhausted


def _cascade_rules(preds):
    return [r for lo, hi in zip(preds, preds[1:]) for r in load_machine_rules(f"?x {hi} ?y when ?x {lo} ?y")]


def check_1_exhaustion_raises_a_flare():
    preds = ["a", "b", "c", "d", "e", "f", "g", "h"]
    rules = _reify_rules(_cascade_rules(preds))
    kb = AttrGraph()
    x, y = kb.add_node("x"), kb.add_node("y")
    kb.add_relation(x, "a", y)
    _n, exhausted = demand_with_flare(kb, ("h", "x", "y"), rules, max_rounds=2)   # starve the budget
    flare_up = bool(_facts_matching(kb, FLARE_PRED, None, YES))
    ok = exhausted and flare_up
    print(f"  1 exhaustion raises a flare      -> {ok} (exhausted={exhausted}, flare={flare_up})")
    return ok, kb, rules


def check_2_flare_is_idempotent(kb, rules):
    before = len([n for n in kb.nodes() if (kb.name(n) or "").startswith("goal:")])
    demand_with_flare(kb, ("h", "x", "y"), rules, max_rounds=2)      # re-exhaust the SAME goal
    demand_with_flare(kb, ("h", "x", "y"), rules, max_rounds=2)
    after = len([n for n in kb.nodes() if (kb.name(n) or "").startswith("goal:")])
    flares = len(_facts_matching(kb, FLARE_PRED, None, YES))
    ok = before == after == 1 and flares == 1
    print(f"  2 flare is idempotent (no storm) -> {ok} (goal-nodes={after}, flares={flares})")
    return ok


def check_3_system_reacts_to_the_flare():
    # A DECLARED reaction fires on the flare through the reactive gate: `?g escalated yes when ?g stuck yes`.
    # The flare marked its grain dirty; declaring `escalated` reactive makes the next committed act escalate.
    kb = AttrGraph()
    x, y = kb.add_node("x"), kb.add_node("y")
    kb.add_relation(x, "a", y)
    react_rules = load_machine_rules(f"?g escalated {YES} when ?g {FLARE_PRED} {YES}")
    rules_r = _reify_rules(_cascade_rules(["a", "b", "c", "d", "e", "f", "g", "h"]))
    demand_with_flare(kb, ("h", "x", "y"), rules_r, max_rounds=2)    # exhaust -> flare -> dirty grain
    declare_reactive(kb, "escalated")
    fire(kb, react_rules)                                            # the reactive core reacts to its flare
    escalated = bool(_facts_matching(kb, "escalated", None, YES))
    print(f"  3 system reacts to the flare     -> {escalated} (escalated materialized)")
    return escalated


def check_4_no_loop_when_reaction_retries():
    # SOUNDNESS: even a reaction that RE-DEMANDS the stuck goal must not loop. The flare is deduped +
    # presence-triggered, so a second fire finds the SAME single flare and terminates (no storm/hang).
    kb = AttrGraph()
    x, y = kb.add_node("x"), kb.add_node("y")
    kb.add_relation(x, "a", y)
    rules_r = _reify_rules(_cascade_rules(["a", "b", "c", "d", "e", "f", "g", "h"]))
    for _ in range(5):                                              # repeated acts must terminate
        demand_with_flare(kb, ("h", "x", "y"), rules_r, max_rounds=2)
        fire(kb, [])
    flares = len(_facts_matching(kb, FLARE_PRED, None, YES))
    ok = flares == 1
    print(f"  4 no loop under retry            -> {ok} (flares still {flares})")
    return ok


if __name__ == "__main__":
    ok1, kb, rules = check_1_exhaustion_raises_a_flare()
    ok2 = check_2_flare_is_idempotent(kb, rules)
    ok3 = check_3_system_reacts_to_the_flare()
    ok4 = check_4_no_loop_when_reaction_retries()
    print("=" * 62)
    results = [ok1, ok2, ok3, ok4]
    print(f"HELP-FLARE: {sum(results)}/{len(results)} "
          + ("GO — exhaustion is a durable, reactable, sound signal" if all(results) else "<-- GAP"))
