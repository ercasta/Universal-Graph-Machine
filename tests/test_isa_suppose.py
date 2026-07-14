"""
Phase 5.3 — SUPPOSE firmware (`harneskills/isa/suppose.py`): `<hypothesis>` scopes done as the
PENCIL/INK split (`processing_modes.md` mode 6). Obligations:

  1. scope-aware matching is BEHAVIOR-NEUTRAL when no scope is active (the positive core is protected):
     a pencil fact is invisible to ordinary `chain_sip`;
  2. inside a scope, CHAIN sees the pencil and reasons over it, EMITting derivations in pencil only;
  3. CONFIRM commits the assumptions to INK and the ink survives the scope teardown;
  4. REFUTE (a contradiction) and INCONCLUSIVE leave INK untouched (monotone — no retraction) and sweep
     every pencil node;
  5. same-graph, not possible-worlds: the reasoning never forks a `graph.copy()`.
"""
import ugm as h
from ugm import Pat, Rule
from ugm import (
    AttrGraph, chain_sip,
    suppose, explain_suppose, scope_members,
    CONFIRMED, REFUTED, INCONCLUSIVE, HYPOTHESIS,
)
from ugm.suppose import _pencil


def _facts(triples) -> AttrGraph:
    g = AttrGraph()
    ids: dict[str, str] = {}

    def node(name: str) -> str:
        if name not in ids:
            ids[name] = g.add_node(name)
        return ids[name]

    for s, p, o in triples:
        g.add_relation(node(s), p, node(o))
    return g


def _reify(rules) -> AttrGraph:
    rg = AttrGraph()
    for r in rules:
        h.write_rule(rg, r)
    return rg


BIRD_FLIES = Rule(key="bird_flies", lhs=[Pat("?x", "is", "bird")], rhs=[Pat("?x", "is", "flyer")])
PENGUIN_NOFLY = Rule(key="peng_nofly", lhs=[Pat("?x", "is", "penguin")], rhs=[Pat("?x", "is_not", "flyer")])


def _ink(g) -> set:
    """The INK layer only: `(s, pred, o)` for every NON-control, non-inert rel node with real endpoints.
    (`derived_triples` deliberately includes control rel nodes; a pencil fact must be read out of ink.)"""
    out: set = set()
    for r in g.nodes():
        if g.is_control(r) or g.is_inert(r):
            continue
        rn = g.predicate(r)
        if not rn:
            continue
        preds = [s for s in g.pred(r) if not (g.is_control(s) or g.is_inert(s))]
        succs = [o for o in g.succ(r) if not (g.is_control(o) or g.is_inert(o))]
        for s in preds:
            for o in succs:
                if g.name(s) and g.name(o):
                    out.add((g.name(s), rn, g.name(o)))
    return out


# --- 1. behavior-neutral: a pencil fact is invisible to ordinary (scopeless) matching ---------------

def test_pencil_fact_is_invisible_to_scopeless_chain():
    g = _facts([])
    rg = _reify([BIRD_FLIES])
    scope = g.add_node(HYPOTHESIS, control=True)
    tweety = g.add_node("tweety")
    _pencil(g, scope, tweety, "is", g.add_node("bird"))
    # ordinary CHAIN (no scope) must NOT see the pencil `tweety is bird`, so it derives nothing
    before = _ink(g)
    chain_sip(g, ("is", "tweety", "flyer"), rules=rg)
    assert _ink(g) == before                                  # positive core untouched


def test_in_scope_chain_sees_the_pencil_and_derives_in_pencil():
    g = _facts([])
    rg = _reify([BIRD_FLIES])
    scope = g.add_node(HYPOTHESIS, control=True)
    tweety = g.add_node("tweety")
    _pencil(g, scope, tweety, "is", g.add_node("bird"))
    # WITHIN the scope, the pencil `tweety is bird` is visible -> `tweety is flyer` is derived...
    chain_sip(g, ("is", "tweety", "flyer"), scope=scope, rules=rg)
    # ...but only in PENCIL: it is NOT an ink fact (derived_triples reads ink only)
    assert ("tweety", "is", "flyer") not in _ink(g)
    # and it is a member of the scope (a scope-tagged control rel node)
    assert len(scope_members(g, scope)) == 2                      # the assumption + the derived consequence


# --- 3. CONFIRM: assumptions enter ink and survive teardown ----------------------------------------

def test_confirm_commits_the_assumption_to_ink():
    # observed: tweety flies. Hypothesis `tweety is bird` predicts it -> confirmed, inked.
    g = _facts([("tweety", "is", "flyer")])
    rg = _reify([BIRD_FLIES])
    r = suppose(g, assumptions=[("tweety", "is", "bird")], predictions=[("is", "tweety", "flyer")], rules=rg)
    assert r.status == CONFIRMED
    assert r.committed == [("tweety", "is", "bird")]
    # the assumption is now INK and survives the scope sweep...
    assert ("tweety", "is", "bird") in _ink(g)
    # ...and no <hypothesis>/pencil scaffolding lingers
    assert g.nodes_named(HYPOTHESIS) == []


def test_confirmed_ink_lets_ordinary_reasoning_rederive_the_consequence():
    g = _facts([("tweety", "is", "flyer")])
    rg = _reify([BIRD_FLIES])
    suppose(g, [("tweety", "is", "bird")], [("is", "tweety", "flyer")], rules=rg)
    # after confirmation the inked assumption drives ordinary (scopeless) CHAIN to the consequence
    chain_sip(g, ("is", "tweety", "flyer"), rules=rg)
    assert ("tweety", "is", "flyer") in _ink(g)               # already ink; still holds — monotone


# --- 4. REFUTE: contradiction leaves ink untouched -------------------------------------------------

def test_refute_on_contradiction_leaves_ink_untouched():
    # tweety is a penguin (real) => `tweety is_not flyer` is entailed. Supposing `tweety is bird`
    # predicts `tweety is flyer` — the supposition entails the OPPOSITE -> refuted, nothing inked.
    g = _facts([("tweety", "is", "penguin")])
    rg = _reify([BIRD_FLIES, PENGUIN_NOFLY])
    ink_before = _ink(g)
    r = suppose(g, [("tweety", "is", "bird")], [("is", "tweety", "flyer")], rules=rg)
    assert r.status == REFUTED
    assert r.contradiction == ("is", "tweety", "flyer")
    assert r.committed == []
    # MONOTONE: ink is exactly what it was; the pencil (assumption + derivations) is gone
    assert _ink(g) == ink_before
    assert g.nodes_named(HYPOTHESIS) == []
    assert scope_members(g, "anything") == []                    # no lingering scope-tagged nodes


def test_inconclusive_when_prediction_underivable_leaves_ink_untouched():
    # nothing derives `tweety is swimmer`; no contradiction either -> inconclusive, ink untouched.
    g = _facts([])
    rg = _reify([BIRD_FLIES])
    before = _ink(g)
    r = suppose(g, [("tweety", "is", "bird")], [("is", "tweety", "swimmer")], rules=rg)
    assert r.status == INCONCLUSIVE
    assert r.committed == []
    assert _ink(g) == before
    assert g.nodes_named(HYPOTHESIS) == []


# --- 5. same-graph, and the explanation renders ---------------------------------------------------

def test_two_supposes_on_the_same_graph_do_not_interfere():
    g = _facts([("tweety", "is", "flyer")])
    rg = _reify([BIRD_FLIES])
    r1 = suppose(g, [("tweety", "is", "bird")], [("is", "tweety", "flyer")], rules=rg)
    # a second, unrelated, underivable hypothesis on the SAME graph must not disturb the first's ink
    r2 = suppose(g, [("robin", "is", "rock")], [("is", "robin", "swimmer")], rules=rg)
    assert r1.status == CONFIRMED and r2.status == INCONCLUSIVE
    assert ("tweety", "is", "bird") in _ink(g)               # r1's commit stands
    assert ("robin", "is", "rock") not in _ink(g)           # r2 touched no ink
    assert g.nodes_named(HYPOTHESIS) == []                       # both scopes swept


def test_explain_suppose_renders_the_verdict_and_the_commit():
    g = _facts([("tweety", "is", "flyer")])
    rg = _reify([BIRD_FLIES])
    r = suppose(g, [("tweety", "is", "bird")], [("is", "tweety", "flyer")], rules=rg)
    lines = explain_suppose(r)
    assert lines[0].startswith("confirmed")
    assert any("tweety is bird" in ln for ln in lines)          # what entered ink
    assert "  reasoned about:" in lines
