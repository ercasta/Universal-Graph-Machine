"""
Edge-rewiring — the `rewire` control-layer primitive (`cut`/`link` on raw edges), and
retraction-by-INTERPOSITION built on it (docs/depythonization_design.md §4).

A fact is the 2-hop path `S -> rel -> O`. To hide it we SPLICE a fresh `<retracted>` node into
the path (`rel -> <retracted> -> O`), breaking the 2-hop the matcher walks — the fact stops
matching through ordinary graph rewriting, the matcher untouched. To resurrect, a rule matches the
interposed shape and splices it back out. This is the identity/provenance-preserving structural
edit `drop`+re-add cannot express (re-adding would mint a new relation node with new provenance).
"""
import ugm as h
from ugm.cnl.rewriter import match, run


def _visible(g, s, p, o):
    return bool(match(g, [h.Pat(s, p, o)]))


def test_rewire_cut_and_link_raw_edges():
    # the primitive in isolation: cut an edge, link another, between bound nodes.
    g = h.Graph()
    g.add_relation(g.add_node("a"), "r", g.add_node("b"))
    assert _visible(g, "?x", "r", "b")
    # cut the r->b edge (the relation node `r?` bound via a bound-literal predicate)
    run(g, [h.Rule(key="cut.rb", lhs=[h.Pat("?x", "r?", "b")], rhs=[],
                   rewire=[("cut", "r?", "b")])])
    assert not _visible(g, "?x", "r", "b")          # the 2-hop path is broken


def test_interpose_hides_fact_from_matching():
    g = h.Graph()
    g.add_relation(g.add_node("alice"), "is_not", g.add_node("urgent"))
    assert _visible(g, "?x", "is_not", "urgent")

    # HIDE: splice a fresh <retracted> into the object edge: is_not -> <retracted> -> urgent
    interpose = h.Rule(
        key="interpose",
        lhs=[h.Pat("?x", "is_not?", "urgent")], rhs=[],     # bind the is_not RELATION node via `is_not?`
        rewire=[("cut", "is_not?", "urgent"),
                ("link", "is_not?", "<retracted>?"),
                ("link", "<retracted>?", "urgent")])
    run(g, [interpose])

    assert not _visible(g, "?x", "is_not", "urgent")   # hidden
    # and it does NOT leak as a spurious `alice is_not <retracted>`: <retracted> is inert, so an
    # ordinary (non-provenance-aware) pattern refuses to bind it.
    assert not _visible(g, "?x", "is_not", "?o")


def test_interpose_preserves_the_relation_node_identity():
    # the is_not relation node (and any provenance hanging off it) SURVIVES the hide — only its
    # object edge is rerouted. drop+re-add could not do this (it would delete the node).
    g = h.Graph()
    rel = g.add_relation(g.add_node("alice"), "is_not", g.add_node("urgent"))
    run(g, [h.Rule(key="interpose", lhs=[h.Pat("?x", "is_not?", "urgent")], rhs=[],
                   rewire=[("cut", "is_not?", "urgent"),
                           ("link", "is_not?", "<retracted>?"),
                           ("link", "<retracted>?", "urgent")])])
    assert g.has(rel) and g.name(rel) == "is_not"      # same node, same identity


def test_interpose_then_resurrect_restores_the_fact():
    g = h.Graph()
    g.add_relation(g.add_node("alice"), "is_not", g.add_node("urgent"))
    run(g, [h.Rule(key="interpose", lhs=[h.Pat("?x", "is_not?", "urgent")], rhs=[],
                   rewire=[("cut", "is_not?", "urgent"),
                           ("link", "is_not?", "<retracted>?"),
                           ("link", "<retracted>?", "urgent")])])
    assert not _visible(g, "?x", "is_not", "urgent")

    # RESURRECT: match the interposed shape `?x -> is_not -> <retracted> -> urgent` (naming
    # <retracted> makes the rule provenance-aware, so it may traverse the inert interposer) and
    # splice it back out.
    resurrect = h.Rule(
        key="resurrect",
        lhs=[h.Pat("?x", "is_not?", "<retracted>"),
             h.Pat("is_not?", "<retracted>?", "urgent")], rhs=[],
        rewire=[("cut", "is_not?", "<retracted>?"),
                ("cut", "<retracted>?", "urgent"),
                ("link", "is_not?", "urgent")])
    run(g, [resurrect])
    assert _visible(g, "?x", "is_not", "urgent")       # restored


def test_interpose_stops_a_consumer_rederiving():
    # end-to-end meaning: hiding the fact stops a domain rule that consumes it from firing.
    consumer = h.Rule(key="serve", lhs=[h.Pat("?x", "is_not", "urgent")],
                      rhs=[h.Pat("?x", "served", "regular")])
    g = h.Graph()
    g.add_relation(g.add_node("alice"), "is_not", g.add_node("urgent"))
    run(g, [consumer])
    assert _visible(g, "?x", "served", "regular")      # consumer fired

    g2 = h.Graph()
    g2.add_relation(g2.add_node("alice"), "is_not", g2.add_node("urgent"))
    run(g2, [h.Rule(key="interpose", lhs=[h.Pat("?x", "is_not?", "urgent")], rhs=[],
                    rewire=[("cut", "is_not?", "urgent"),
                            ("link", "is_not?", "<retracted>?"),
                            ("link", "<retracted>?", "urgent")])])
    run(g2, [consumer])
    assert not _visible(g2, "?x", "served", "regular")  # hidden premise -> no derivation
