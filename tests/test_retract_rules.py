"""
Retraction AS RULES — the cascade over now-matchable provenance, hiding by interposition
(docs/depythonization_design.md §4; retraction.RETRACT_RULES). The Python `cascade_retract` driver
expressed as meta-rules: seed `<retract> targets ?rel`, the CASCADE rule propagates the marker
along `proves`/`uses`, the INTERPOSE rule splices `<retracted>` into each targeted fact to hide it.

Aggressive/single-support form (stratified): correct for a derivation chain; a multi-support fact
would be over-retracted and is recovered by re-derivation (deferred — not exercised here).
"""
import ugm as h
from ugm import provenance as prov, retraction as ret
from ugm.cnl.authoring import run_rules

R1 = h.Rule(key="r0.r1", lhs=[h.Pat("?a", "r0", "?b")], rhs=[h.Pat("?a", "r1", "?b")])
R2 = h.Rule(key="r1.r2", lhs=[h.Pat("?a", "r1", "?b")], rhs=[h.Pat("?a", "r2", "?b")])


def _vis(g, s, p, o):
    """Does the raw 2-hop path  s -[p]-> o  exist? (s/p/o are all ground names here — interposed
    hiding breaks this 2-hop into a 3-hop through the `<retracted>` marker, so a hidden fact reads
    as not-visible directly, no matcher needed.)"""
    return any(g.has_key(r, p) and o_id in g.out(r)
               for s_id in g.nodes_named(s) for r in g.out(s_id) for o_id in g.nodes_named(o))


def _n_justifications(g):
    return len([n for n in g.nodes() if prov.is_justification(g.name(n))])


def _build():
    """Two independent chains r0 -> r1 -> r2, over bases `x r0 y` and `p r0 q` (axiomatized)."""
    g = h.Graph()
    r0_xy = g.add_relation(g.add_node("x"), "r0", g.add_node("y"))
    g.add_relation(g.add_node("p"), "r0", g.add_node("q"))
    prov.axiomatize(g, ["r0"])            # base facts get an <axiom> proof (never cascade candidates)
    run_rules(g, [R1, R2])                # derive r1, r2 for both, WITH provenance
    return g, r0_xy


def test_cascade_hides_the_whole_chain_below_a_retracted_base():
    g, r0_xy = _build()
    assert _vis(g, "x", "r1", "y") and _vis(g, "x", "r2", "y")

    ret.retract(g, r0_xy)                 # seed + cascade + interpose (provenance=False)

    # x's chain is hidden (the retracted base + everything derived from it)
    assert not _vis(g, "x", "r0", "y")
    assert not _vis(g, "x", "r1", "y")
    assert not _vis(g, "x", "r2", "y")
    # the independent p chain is untouched
    assert _vis(g, "p", "r0", "q") and _vis(g, "p", "r1", "q") and _vis(g, "p", "r2", "q")


def test_cascade_mints_no_new_justifications():
    # meta-rules run with provenance=False (the regress guard): retraction adds no <j:> nodes.
    g, r0_xy = _build()
    before = _n_justifications(g)
    ret.retract(g, r0_xy)
    assert _n_justifications(g) == before


def test_interposition_preserves_relation_identity():
    # hiding is by interposition, so the derived relation nodes SURVIVE (only their object edge is
    # rerouted) — the reversibility a sever-based cascade cannot offer.
    g, r0_xy = _build()
    r1_xy = next(r for r in g.nodes() if g.predicate(r) == "r1")   # the derived x r1 y relation node
    ret.retract(g, r0_xy)
    assert g.has(r1_xy) and g.predicate(r1_xy) == "r1"             # same node, still present, just hidden


def test_no_retract_no_effect():
    # the rules are inert without a seed: RETRACT_RULES over an untouched graph change nothing.
    g, _ = _build()
    vis_before = [_vis(g, "x", p, o) for p, o in (("r0", "y"), ("r1", "y"), ("r2", "y"))]
    run_rules(g, ret.RETRACT_RULES, provenance=False)
    assert [_vis(g, "x", p, o) for p, o in (("r0", "y"), ("r1", "y"), ("r2", "y"))] == vis_before
    assert all(vis_before)
