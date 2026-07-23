"""ROBUSTNESS BATTERY against the reactive `fire` gate — stress the by-construction claims.

Each check pushes an adversarial reactive bank through `fire` (eager materialization) and compares to what
DEMAND would compute, or to the known-correct convergence. A gap here = a place the reactive push does not
inherit the demand engine's guarantees.
"""
from __future__ import annotations

import warnings

import ugm as h
from ugm import AttrGraph
from ugm.production_rule import Rule, Pat
from ugm.cnl.machine_rules import load_machine_rules
from ugm.reconsider import mark_dirty
from ugm.reactive import declare_reactive, fire
from ugm.chain import _facts_matching, chain_sip
from ugm.cnl.query import _reify_rules
from ugm.policy import FirmwarePolicy

warnings.simplefilter("ignore")
BANDED = FirmwarePolicy(uncertainty="banded")


def _mat(g, p, s, o):
    return bool(_facts_matching(g, p, s, o))


def check_1_skolem_minting_reactive_converges():
    # A skolem-minting rule's HEAD declared reactive: eager push must mint ONE witness per binding (converge
    # by structural re-find), NOT a fuel-capped flood and NOT zero.
    R = Rule(key="mk", lhs=[Pat("?p", "is_a", "state")],
             rhs=[Pat("?p", "has_succ", "s2?"), Pat("s2?", "succ_of", "?p")])
    g = h.Graph()
    for nm in ("p1", "p2"):
        n = g.add_node(nm); g.add_relation(n, "is_a", g.add_node("state"))
    declare_reactive(g, "has_succ")
    mark_dirty(g, [("is_a", "state")])
    fire(g, [R])
    succ = [x for x in g.nodes() if g.name(x) == "s2"]
    ok = len(succ) == 2
    print(f"  1 skolem-reactive converges     -> {ok} (minted {len(succ)}, want 2)")
    return ok


def check_2_deep_cascade_drains_in_one_fire():
    # a->b->c->d->e, ALL reactive. Materialize a, fire ONCE: the whole cascade must materialize (the
    # standing work-list closes the chain), not stop after one hop.
    rules = []
    chain_preds = ["a", "b", "c", "d", "e"]
    for lo, hi in zip(chain_preds, chain_preds[1:]):
        rules += load_machine_rules(f"?x {hi} ?y when ?x {lo} ?y")
    g = AttrGraph()
    x, y = g.add_node("x"), g.add_node("y")
    g.add_relation(x, "a", y)
    for p in chain_preds[1:]:
        declare_reactive(g, p)
    mark_dirty(g, [("a", "y")])
    fire(g, rules)
    ok = _mat(g, "e", "x", "y")
    print(f"  2 deep cascade drains (a..e)     -> {ok}")
    return ok


def check_3_nac_reactive_respects_block():
    # A reactive rule WITH a NAC: `ok when has and not blocked`. Eager push must respect the NAC exactly as
    # demand would — push `ok` iff not blocked. Two worlds.
    rules = load_machine_rules("?c ok yes when ?l has ?c and not ?c blocked yes")

    def push_world(blocked: bool):
        g = AttrGraph()
        l, c, yes = g.add_node("l"), g.add_node("c"), g.add_node("yes")
        g.add_relation(l, "has", c)
        grains = [("has", "c")]
        if blocked:
            g.add_relation(c, "blocked", yes); grains.append(("blocked", "yes"))
        declare_reactive(g, "ok")
        mark_dirty(g, grains)
        fire(g, rules)
        return _mat(g, "ok", "c", "yes")

    def demand_world(blocked: bool):
        g = AttrGraph()
        l, c, yes = g.add_node("l"), g.add_node("c"), g.add_node("yes")
        g.add_relation(l, "has", c)
        if blocked:
            g.add_relation(c, "blocked", yes)
        chain_sip(g, ("ok", "c", "yes"), rules=_reify_rules(rules))
        return _mat(g, "ok", "c", "yes")

    ok = (push_world(False) == demand_world(False) == True
          and push_world(True) == demand_world(True) == False)
    print(f"  3 NAC-reactive respects block    -> {ok} "
          f"(push F/T = {push_world(False)}/{push_world(True)})")
    return ok


def check_4_banded_reactive_materializes():
    # Under a BANDED policy, a reactive consequence of a graded trigger must materialize (the possibilistic
    # fold flows through the derive half). Compare push-materialized to a demand under the same policy.
    rules = load_machine_rules("?x endangers ?y when ?x hunts ?y")
    g = AttrGraph()
    w, s = g.add_node("wolf"), g.add_node("sheep")
    g.add_relation(w, "hunts", s, confidence=0.6)         # a graded/hedged trigger
    declare_reactive(g, "endangers")
    mark_dirty(g, [("hunts", "sheep")])
    fire(g, rules, policy=BANDED)
    push = bool(_facts_matching(g, "endangers", "wolf", "sheep", bands=True))

    g2 = AttrGraph()
    w2, s2 = g2.add_node("wolf"), g2.add_node("sheep")
    g2.add_relation(w2, "hunts", s2, confidence=0.6)
    chain_sip(g2, ("endangers", "wolf", "sheep"), rules=_reify_rules(rules), policy=BANDED)
    demand = bool(_facts_matching(g2, "endangers", "wolf", "sheep", bands=True))
    ok = push == demand == True
    print(f"  4 banded reactive materializes   -> {ok} (push={push} demand={demand})")
    return ok


def check_5_derive_then_retract_in_one_fire():
    # THE C.1 crux: a REACTIVE derive produces the very breaker that makes a NAF conclusion stale, and the
    # SAME `fire` call must BOTH materialize it (derive) AND withdraw the stale conclusion (retract) — the
    # derive-then-recheck ordering, end-to-end through the unified gate.
    from ugm.cnl.authoring import run_rules
    from ugm.lowering import load_fact_triples
    R_end = Rule(key="endangers.hunts", lhs=[Pat("?x", "hunts", "?y")], rhs=[Pat("?x", "endangers", "?y")])
    R_safe = Rule(key="safe.near", lhs=[Pat("?x", "near", "?y")],
                  nac=[Pat("?x", "endangers", "?y")], rhs=[Pat("?x", "safe", "?y")])
    g = h.Graph()
    load_fact_triples(g, [("wolf", "near", "sheep")])
    run_rules(g, [R_end, R_safe], provenance=True)
    assert _mat(g, "safe", "wolf", "sheep")                  # NAF conclusion stands (assumed)

    # now the reactive trigger lands; endangers is REACTIVE, so fire's DERIVE materializes it, then RETRACT
    # rechecks the `safe` assumption against the just-derived breaker — one gate, one dirty set.
    load_fact_triples(g, [("wolf", "hunts", "sheep")])
    declare_reactive(g, "endangers")
    mark_dirty(g, [("hunts", "sheep")])
    fired, withdrawn = fire(g, [R_end, R_safe])
    ok = _mat(g, "endangers", "wolf", "sheep") and not _mat(g, "safe", "wolf", "sheep") and withdrawn == 1
    print(f"  5 derive-then-retract one fire   -> {ok} (fired={fired} withdrawn={withdrawn})")
    return ok


def check_6_focus_scope_bounds_the_derive():
    # A reactive derive under a focus_scope must respect it: materialize when the nodes are in the live set,
    # NOT when they are excluded — the reaction fires into the SCOPED frame, like a scoped demand.
    rules = load_machine_rules("?x endangers ?y when ?x hunts ?y")

    def fire_with_scope(scope):
        g = AttrGraph()
        w, s = g.add_node("wolf"), g.add_node("sheep")
        g.add_relation(w, "hunts", s)
        declare_reactive(g, "endangers")
        mark_dirty(g, [("hunts", "sheep")])
        fire(g, rules, focus_scope=scope)
        return _mat(g, "endangers", "wolf", "sheep")

    in_scope = fire_with_scope(frozenset({"wolf", "sheep"}))
    out_scope = fire_with_scope(frozenset({"unrelated"}))
    ok = in_scope and not out_scope
    print(f"  6 focus_scope bounds the derive  -> {ok} (in={in_scope} out={out_scope})")
    return ok


if __name__ == "__main__":
    results = [
        check_1_skolem_minting_reactive_converges(),
        check_2_deep_cascade_drains_in_one_fire(),
        check_3_nac_reactive_respects_block(),
        check_4_banded_reactive_materializes(),
        check_5_derive_then_retract_in_one_fire(),
        check_6_focus_scope_bounds_the_derive(),
    ]
    print("=" * 60)
    print(f"ROBUSTNESS: {sum(results)}/{len(results)} invariants hold"
          + ("" if all(results) else "  <-- GAP(S) FOUND"))
