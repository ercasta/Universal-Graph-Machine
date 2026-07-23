"""Help-flare (ugm/flare.py) — fuel exhaustion as a DURABLE, REACTABLE signal, on both committed-act paths.

The robustness audit's soft spot: a demand closure that exhausts its budget truncated SILENTLY. The flare
turns that event into a normal reactable fact `<goal-node> unresolved yes`, so the reactive core can respond
to its own resource limit. These tests drive the two committed-act paths (the reactive DERIVE gate `fire`,
and the ASK path `ask_goal`), plus the unit contract (idempotence, no false flares, reactability).
"""
from __future__ import annotations

import warnings

from ugm import AttrGraph
from ugm.cnl.machine_rules import load_machine_rules
from ugm.cnl.query import ask_goal
from ugm.reconsider import mark_dirty
from ugm.reactive import declare_reactive, fire
from ugm.flare import raise_flare, flares, FLARE_PRED, FLARE_MARK
from ugm.chain import _facts_matching


def _hard_cascade():
    # an 8-hop cascade x-a->..->h->y; starved at max_rounds=2 it cannot reach fixpoint -> exhausts.
    preds = ["a", "b", "c", "d", "e", "f", "g", "h"]
    rules = [r for lo, hi in zip(preds, preds[1:]) for r in load_machine_rules(f"?x {hi} ?y when ?x {lo} ?y")]
    kb = AttrGraph()
    x, y = kb.add_node("x"), kb.add_node("y")
    kb.add_relation(x, "a", y)
    return kb, rules


# --- unit contract ---------------------------------------------------------------------------------

def test_raise_flare_is_queryable_and_idempotent():
    kb = AttrGraph()
    raise_flare(kb, ("endangers", "wolf", "sheep"))
    assert ("endangers", "wolf", "sheep") in flares(kb)
    n_goal_nodes = len([g for g in kb.nodes() if (kb.name(g) or "").startswith("goal:")])
    raise_flare(kb, ("endangers", "wolf", "sheep"))                 # re-raise the SAME goal
    raise_flare(kb, ("endangers", "wolf", "sheep"))
    assert len([g for g in kb.nodes() if (kb.name(g) or "").startswith("goal:")]) == n_goal_nodes  # no storm
    assert flares(kb) == [("endangers", "wolf", "sheep")]           # still one flare


def test_flare_preserves_wildcard_endpoints():
    kb = AttrGraph()
    raise_flare(kb, ("h", None, "y"))
    assert ("h", None, "y") in flares(kb)                           # None round-trips (not the "*" spelling)


# --- the reactive DERIVE path ----------------------------------------------------------------------

def test_an_exhausted_reactive_derive_raises_a_flare():
    kb, rules = _hard_cascade()
    declare_reactive(kb, "h")
    mark_dirty(kb, [("a", "y")])
    fire(kb, rules, max_rounds=2)                                   # the reactive derive can't finish
    assert any(g[0] == "h" for g in flares(kb))                     # -> a flare, not a silent truncation


def test_a_settling_reactive_derive_raises_no_flare():
    kb = AttrGraph()
    w, s = kb.add_node("wolf"), kb.add_node("sheep")
    kb.add_relation(w, "hunts", s)
    rules = load_machine_rules("?x endangers ?y when ?x hunts ?y")
    declare_reactive(kb, "endangers")
    mark_dirty(kb, [("hunts", "sheep")])
    fire(kb, rules)                                                 # converges well under budget
    assert _facts_matching(kb, "endangers", "wolf", "sheep")        # derived
    assert flares(kb) == []                                         # and NO false flare


# --- the ASK path ----------------------------------------------------------------------------------

def test_an_exhausted_ask_raises_a_flare():
    kb, rules = _hard_cascade()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ans = ask_goal(kb, ("yesno", "x", "h", "y"), rules, max_rounds=2)
    assert ans == ["unknown"]                                       # honest "did not finish"
    assert ("h", "x", "y") in flares(kb)                            # AND a durable trace of it


def test_a_read_only_ask_raises_no_flare():
    kb, rules = _hard_cascade()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ask_goal(kb, ("yesno", "x", "h", "y"), rules, max_rounds=2, commit=False)
    assert flares(kb) == []                                         # commit=False keeps the no-mutation promise


# --- composition: the reactive core reacts to its own flare -----------------------------------------

def test_the_reactive_core_reacts_to_its_own_flare():
    # A flare is a plain reactable fact, so a DECLARED reactive rule fires on it — the system responds to its
    # own resource limit through the SAME gate, no special path. (`?g escalated yes when ?g unresolved yes`.)
    kb, rules = _hard_cascade()
    recovery = load_machine_rules(f"?g escalated {FLARE_MARK} when ?g {FLARE_PRED} {FLARE_MARK}")
    declare_reactive(kb, "h")
    declare_reactive(kb, "escalated")
    mark_dirty(kb, [("a", "y")])
    fire(kb, rules + recovery, max_rounds=2)                        # exhaust -> flare -> dirty grain
    fire(kb, rules + recovery, max_rounds=2)                        # next act: the recovery reaction fires
    assert _facts_matching(kb, "escalated", None, FLARE_MARK)       # the core reacted to its own flare
