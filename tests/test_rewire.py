"""
Edge-rewiring — the `rewire` control-layer primitive (`cut`/`link` on raw edges), and
retraction-by-INTERPOSITION built on it (docs/depythonization_design.md §4).

A fact is the 2-hop path `S -> rel -> O`. To hide it we SPLICE a fresh `<retracted>` node into
the path (`rel -> <retracted> -> O`), breaking the 2-hop the matcher walks — the fact stops
matching through ordinary graph rewriting, the matcher untouched. To resurrect, a rule matches the
interposed shape and splices it back out. This is the identity/provenance-preserving structural
edit `drop`+re-add cannot express (re-adding would mint a new relation node with new provenance).

Production never runs `rewire` through the oracle — it lowers a `rewire=[("cut",...), ("link",...)]`
triple to the ISA's INTERPOSE opcode (lowering.lower_rewire), executed by run_bank/run_rules. These
tests exercise that lowering + execution path end to end, on the ISA engine.
"""
import ugm as h
from ugm.cnl.authoring import run_rules
from ugm.attrgraph import _is_inert


def _visible(g, s, p, o):
    """Does the raw 2-hop path  s -[p]-> o  exist directly on the graph? A '?'-prefixed s/o is a
    wildcard (matches any node) — plain structural inspection, no matcher involved, except a
    wildcard never lands on an INERT node (a `<retracted>` marker etc.): an ordinary pattern
    refuses to bind those (`_try_bind`'s `match_inert` refusal), so this mirrors that for a wildcard
    endpoint. The interposed shape also breaks the 2-hop itself (it becomes 3-hop through the
    marker), so a hidden fact reads as not-visible here for that reason too."""
    s_free, o_free = s.startswith("?"), o.startswith("?")
    s_ids = g.nodes() if s_free else g.nodes_named(s)
    o_ids = None if o_free else set(g.nodes_named(o))
    for s_id in s_ids:
        if s_free and _is_inert(g.name(s_id)):
            continue
        for rel in g.out(s_id):
            if g.name(rel) != p:
                continue
            for o_id in g.out(rel):
                if o_free and _is_inert(g.name(o_id)):
                    continue
                if o_free or o_id in o_ids:
                    return True
    return False


def test_rewire_cut_and_link_raw_edges():
    # the primitive in isolation. NOTE: `lower_rewire` only recognizes the one sanctioned
    # 3-op interposition shape (cut/link/link forming a reversible splice) — a bare cut (or any
    # other rewire shape) is deliberately `Unlowerable` (lowering.py: "raw-edge surgery outside the
    # reversible interposition is not a sanctioned ISA fact op"), so a bare-cut RULE cannot run
    # through run_rules/run_bank. The primitive itself is the INTERPOSE opcode, exercised here
    # directly on the Machine (as test_isa_interpose.py's opcode-identity test does) rather than
    # through a Rule — cut+link, just not via the rule/matcher surface.
    from ugm.machine import Machine, INTERPOSE, State
    g = h.Graph()
    a, r, b = g.add_node("a"), g.add_node("r"), g.add_node("b")
    g.add_edge(a, r); g.add_edge(r, b)
    assert _visible(g, "?x", "r", "b")
    Machine().apply(g, [INTERPOSE(rel="r", obj="b", marker_name="<retracted>", out="mk")],
                     State({"r": r, "b": b}))
    assert not _visible(g, "?x", "r", "b")          # the 2-hop path is broken


def test_interpose_hides_fact_from_matching():
    g = h.Graph()
    g.add_relation(g.add_node("alice"), "is_not", g.add_node("urgent"))
    assert _visible(g, "?x", "is_not", "urgent")

    # HIDE: splice a fresh <retracted> into the object edge: is_not -> <retracted> -> urgent
    interpose = h.Rule(
        key="interpose",
        # both endpoints must be LHS-BOUND for `lower_rewire` to recognize this as the sanctioned
        # interposition shape (implementation_plan.md Phase 0.5) — a plain-literal object does not
        # lower, so `?o` (not `urgent`) is the bound object here.
        lhs=[h.Pat("?x", "is_not?", "?o")], rhs=[],     # bind the is_not RELATION node via `is_not?`
        rewire=[("cut", "is_not?", "?o"),
                ("link", "is_not?", "<retracted>?"),
                ("link", "<retracted>?", "?o")])
    run_rules(g, [interpose], provenance=False)

    assert not _visible(g, "?x", "is_not", "urgent")   # hidden
    # and it does NOT leak as a spurious `alice is_not <retracted>`: <retracted> is inert, so an
    # ordinary (non-provenance-aware) pattern refuses to bind it.
    assert not _visible(g, "?x", "is_not", "?o")


def test_interpose_preserves_the_relation_node_identity():
    # the is_not relation node (and any provenance hanging off it) SURVIVES the hide — only its
    # object edge is rerouted. drop+re-add could not do this (it would delete the node).
    g = h.Graph()
    rel = g.add_relation(g.add_node("alice"), "is_not", g.add_node("urgent"))
    run_rules(g, [h.Rule(key="interpose", lhs=[h.Pat("?x", "is_not?", "?o")], rhs=[],
                         rewire=[("cut", "is_not?", "?o"),
                                 ("link", "is_not?", "<retracted>?"),
                                 ("link", "<retracted>?", "?o")])], provenance=False)
    assert g.has(rel) and g.name(rel) == "is_not"      # same node, same identity


def test_interpose_then_resurrect_restores_the_fact():
    g = h.Graph()
    g.add_relation(g.add_node("alice"), "is_not", g.add_node("urgent"))
    run_rules(g, [h.Rule(key="interpose", lhs=[h.Pat("?x", "is_not?", "?o")], rhs=[],
                         rewire=[("cut", "is_not?", "?o"),
                                 ("link", "is_not?", "<retracted>?"),
                                 ("link", "<retracted>?", "?o")])], provenance=False)
    assert not _visible(g, "?x", "is_not", "urgent")

    # RESURRECT: the exact INVERSE of INTERPOSE — splice the marker back out. `lower_rewire` has
    # no rule-level shape for this (only the one-directional hide lowers; see the note in
    # test_rewire_cut_and_link_raw_edges), but RESTORE is a real, sanctioned opcode
    # (isa-reference.md "Reserved: INTERPOSE / RESTORE") — today only reachable directly on the
    # Machine (as test_isa_interpose.py's opcode-identity test does), not via a Rule/CNL surface.
    # Invoke it directly to prove the identity/provenance-preserving reversal the ISA supports.
    from ugm.machine import Machine, RESTORE, State
    rel = next(r for r in g.out(g.nodes_named("alice")[0]) if g.name(r) == "is_not")
    marker = next(m for m in g.out(rel) if g.name(m) == "<retracted>")
    urgent = g.nodes_named("urgent")[0]
    Machine().apply(g, [RESTORE(rel="rel", marker="mk", obj="obj")],
                     State({"rel": rel, "mk": marker, "obj": urgent}))
    assert _visible(g, "?x", "is_not", "urgent")       # restored


def test_interpose_stops_a_consumer_rederiving():
    # end-to-end meaning: hiding the fact stops a domain rule that consumes it from firing.
    consumer = h.Rule(key="serve", lhs=[h.Pat("?x", "is_not", "urgent")],
                      rhs=[h.Pat("?x", "served", "regular")])
    g = h.Graph()
    g.add_relation(g.add_node("alice"), "is_not", g.add_node("urgent"))
    run_rules(g, [consumer], provenance=False)
    assert _visible(g, "?x", "served", "regular")      # consumer fired

    g2 = h.Graph()
    g2.add_relation(g2.add_node("alice"), "is_not", g2.add_node("urgent"))
    run_rules(g2, [h.Rule(key="interpose", lhs=[h.Pat("?x", "is_not?", "?o")], rhs=[],
                         rewire=[("cut", "is_not?", "?o"),
                                 ("link", "is_not?", "<retracted>?"),
                                 ("link", "<retracted>?", "?o")])], provenance=False)
    run_rules(g2, [consumer], provenance=False)
    assert not _visible(g2, "?x", "served", "regular")  # hidden premise -> no derivation
