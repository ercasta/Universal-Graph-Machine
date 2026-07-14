"""Phase 8 NEXT STEP C — id-addressed goal path (name-vs-id addressing).

From the pystrider offline feedback: the tuple-goal APIs (`chain_sip`/`check`/`suppose`) address
entities by NAME, and on a DUPLICATE name the WRITE/seed side silently took `nodes_named(...)[0]` — so
a consumer with legitimately DISTINCT same-named nodes (created directly, not via CNL) was forced into
global name-uniqueness and could not hand the firmware a specific node.

C makes the endpoints accept a `ById(node_id)` pin (additive; the name path is untouched):
  - the demand SEEDS from exactly that node and matches walk out of it (`_facts_matching`);
  - EMIT / SUPPOSE pencil land derived/assumed facts on exactly that node (`resolve_write_node`);
  - a stale pin RAISES at the boundary (`validate_ids`) instead of seeding empty / writing a phantom.

And the same silent->loud theme at the three write points: a NAME resolving to >1 GENUINELY DISTINCT
same-named entity (not coref mentions of one, not reified clause scaffolding) WARNS before the [0]-pick.
"""
import warnings

import pytest

from ugm import (AttrGraph, ById, Pat, Rule, write_rule, chain_sip, check, suppose,
                 POSITIVE, ASSUMED_NO, CONFIRMED)


def _thief_rules() -> AttrGraph:
    rg = AttrGraph()
    write_rule(rg, Rule(key="thief", lhs=[Pat("?x", "stole", "?y")], rhs=[Pat("?x", "is", "thief")]))
    return rg


def _two_distinct_ada() -> tuple[AttrGraph, str, str]:
    """Two DISTINCT nodes both named 'ada' (the pystrider case), created directly, NOT coref-linked.
    Only the FIRST stole the book."""
    g = AttrGraph()
    a1, a2 = g.add_node("ada"), g.add_node("ada")
    g.add_relation(a1, "stole", g.add_node("book"))
    return g, a1, a2


def _is_thief_subjects(g: AttrGraph) -> list[str]:
    return [s for r in g.nodes() if g.predicate(r) == "is"
            for s in g.pred(r) if not g.is_control(s)
            for o in g.succ(r) if g.name(o) == "thief"]


# --- id-addressed query disambiguates distinct same-named nodes --------------------------------------

def test_check_by_id_seeds_from_the_pinned_node():
    g, a1, a2 = _two_distinct_ada()
    rg = _thief_rules()
    # a1 stole -> a thief; a2 did not. The NAME 'ada' cannot tell them apart, the ID can.
    assert check(g, ("is", ById(a1), "thief"), rules=rg) == POSITIVE
    assert check(g, ("is", ById(a2), "thief"), rules=rg) == ASSUMED_NO


def test_by_id_emit_lands_the_derived_fact_on_the_pinned_node():
    g, a1, a2 = _two_distinct_ada()
    rg = _thief_rules()
    chain_sip(g, ("is", ById(a1), "thief"), rules=rg)
    subjects = _is_thief_subjects(g)
    assert a1 in subjects and a2 not in subjects        # derived onto a1 exactly, never a2


def test_by_id_object_endpoint_is_pinned():
    # walk INTO a pinned object: two 'book' nodes, only book1 was stolen. The FREE subject slot binds
    # to a `ById` now (the id-addressed core, Stage 3 — a discovered node is returned by id, not name);
    # the pinned object endpoint returns verbatim.
    from ugm.chain import _facts_matching
    g = AttrGraph()
    ada = g.add_node("ada"); b1, b2 = g.add_node("book"), g.add_node("book")
    g.add_relation(ada, "stole", b1)
    assert _facts_matching(g, "stole", None, ById(b1)) == [(ById(ada), ById(b1))]
    assert _facts_matching(g, "stole", None, ById(b2)) == []          # b2 was never stolen


# --- suppose pins assumptions / predictions to a specific node ---------------------------------------

def test_suppose_by_id_commits_to_the_pinned_node():
    g = AttrGraph()
    a1, a2 = g.add_node("ada"), g.add_node("ada"); g.add_node("book")
    rg = _thief_rules()
    # The prediction `is thief` pinned to a2 CONFIRMS only if a2 (not a1) is reasoned as the thief:
    # a2's pencil `stole book` derives it. Pinning to a1 (who never stole) would be inconclusive.
    res = suppose(g, [(ById(a2), "stole", "book")], [("is", ById(a2), "thief")], rules=rg)
    assert res.status == CONFIRMED
    # the committed assumption landed on a2 exactly (ink survives; the pencil prediction is swept, §5).
    stole_subjects = [s for r in g.nodes() if g.predicate(r) == "stole"
                      for s in g.pred(r) if not g.is_control(s)]
    assert a2 in stole_subjects and a1 not in stole_subjects


def test_suppose_by_id_is_inconclusive_when_the_wrong_node_is_pinned():
    # pin the assumption to a2 but PREDICT about a1 -> a1 never stole, so the thief prediction fails.
    g = AttrGraph()
    a1, a2 = g.add_node("ada"), g.add_node("ada"); g.add_node("book")
    rg = _thief_rules()
    res = suppose(g, [(ById(a2), "stole", "book")], [("is", ById(a1), "thief")], rules=rg)
    assert res.status != CONFIRMED


# --- silent->loud: a stale pin raises at the boundary ------------------------------------------------

def test_by_id_missing_node_raises():
    g, a1, _ = _two_distinct_ada()
    rg = _thief_rules()
    with pytest.raises(ValueError, match="not in the graph"):
        check(g, ("is", ById("no-such-node"), "thief"), rules=rg)


def test_suppose_by_id_missing_node_raises():
    g, _, _ = _two_distinct_ada()
    rg = _thief_rules()
    with pytest.raises(ValueError, match="not in the graph"):
        suppose(g, [(ById("ghost"), "stole", "book")], [], rules=rg)


# --- silent->loud: the write points WARN on a genuinely-ambiguous name -------------------------------

def _warns_distinct(fn) -> bool:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        fn()
        return any("distinct" in str(x.message) for x in w)


def test_name_write_warns_over_distinct_entities():
    # both 'ada' now have their own facts -> two DISTINCT entities; a name-addressed EMIT must warn.
    g, a1, a2 = _two_distinct_ada()
    g.add_relation(a2, "stole", g.add_node("pen"))
    rg = _thief_rules()
    assert _warns_distinct(lambda: chain_sip(g, ("is", "ada", "thief"), rules=rg))


def test_name_write_does_not_warn_for_a_single_node():
    g = AttrGraph(); a = g.add_node("ada"); g.add_relation(a, "stole", g.add_node("book"))
    rg = _thief_rules()
    assert not _warns_distinct(lambda: chain_sip(g, ("is", "ada", "thief"), rules=rg))


def test_name_write_does_not_warn_for_coref_linked_mentions():
    # two 'ada' mentions of ONE identity (same_as-linked) -> the [0]-pick composes; no warn.
    g = AttrGraph()
    a1, a2 = g.add_node("ada"), g.add_node("ada")
    g.add_relation(a1, "stole", g.add_node("book"))
    g.add_relation(a2, "is", g.add_node("detective"))
    g.add_relation(a1, "same_as", a2)
    rg = _thief_rules()
    assert not _warns_distinct(lambda: chain_sip(g, ("is", "ada", "thief"), rules=rg))


def test_by_id_write_never_warns():
    # pinning is the fix the warning points to -> the id path itself is silent.
    g, a1, a2 = _two_distinct_ada()
    g.add_relation(a2, "stole", g.add_node("pen"))
    rg = _thief_rules()
    assert not _warns_distinct(lambda: chain_sip(g, ("is", ById(a1), "thief"), rules=rg))
