"""Binding — NETL's failure mode does not recur (`docs/design/substrate_inversion.md` §14).

Promoted from `bench/spike_substrate_inversion_binding.py`, which answered the question; these keep it
answered. NETL propagated a MARKER — one bit at a node — which does inheritance perfectly and cannot
correlate two matches, so a two-place join becomes a cross-product. A unit whose state is a SUBGRAPH
carries the binding structurally: the value of `?y` is simply a node in the value.
"""
from __future__ import annotations

import pytest

from units import Absent, Fact, Net, Subgraph, Triple, Unit, UnsafePattern, Var, branch, given, mint

X, Y, Z = Var("x"), Var("y"), Var("z")
ADMIRES = ((Triple(X, "likes", Y), Triple(Y, "is", Z)), Triple(X, "admires", Z))


def _pairs(sub) -> set:
    return {(f.s.name, f.o.name) for f in sub}


# ── the NETL diagnosis ──────────────────────────────────────────────────────

def test_two_place_join_is_exact_where_marker_passing_cross_products():
    jack, bob, mary, sue, rich, poor = (mint(n) for n in
                                        ("jack", "bob", "mary", "sue", "rich", "poor"))
    view = Subgraph([Fact(jack, "likes", mary), Fact(bob, "likes", sue),
                     Fact(mary, "is", rich), Fact(sue, "is", poor)])

    # marker passing: mark, follow, conclude. No bindings anywhere, so no correlation.
    marked_x = {f.s for f in view if f.p == "likes"}
    marked_y = {f.o for f in view if f.p == "likes"}
    marked_z = {f.o for f in view.by_pred("is") if f.s in marked_y}
    markers = {(x.name, z.name) for x in marked_x for z in marked_z}

    u = Unit("admire", *ADMIRES)
    u.inputs["src"] = view
    u.run()

    truth = {("jack", "rich"), ("bob", "poor")}
    assert _pairs(u.derived("admires")) == truth
    assert markers == truth | {("jack", "poor"), ("bob", "rich")}      # 4 answers, 2 of them false


# ── identity, not name ──────────────────────────────────────────────────────

def test_cross_wire_join_is_by_identity_and_a_name_join_would_fabricate():
    """§5's correctness requirement. Two independently minted `mary`s are different things; only identity
    inheritance through the pipeline makes a cross-wire join mean anything."""
    jack, mary_a = mint("jack"), mint("mary")
    mary_b, rich = mint("mary"), mint("rich")            # same NAME, different NODE

    u = Unit("admire", *ADMIRES)
    u.inputs["A"] = Subgraph([Fact(jack, "likes", mary_a)])
    u.inputs["B"] = Subgraph([Fact(mary_b, "is", rich)])
    u.run()
    assert not u.derived("admires"), "two distinct marys must not join"
    assert mary_a.name == mary_b.name and mary_a != mary_b

    v = Unit("admire2", *ADMIRES)
    v.inputs["A"] = Subgraph([Fact(jack, "likes", mary_a)])
    v.inputs["B"] = Subgraph([Fact(mary_a, "is", rich)])  # the very same node object
    v.run()
    assert _pairs(v.derived("admires")) == {("jack", "rich")}


def test_identity_survives_union_and_fork():
    jack = mint("jack")
    a = Subgraph([Fact(jack, "is", mint("tall"))])
    b = Subgraph([Fact(jack, "is", mint("kind"))])
    merged = a | b
    assert all(f.s is jack for f in merged), "union must SHARE node objects, never rebuild them"
    assert (a | b) is not a and len(merged) == 2


# ── chains: a join along one, isolation across siblings ─────────────────────

def _two_hypotheses():
    jack, mary, rich, poor = mint("jack"), mint("mary"), mint("rich"), mint("poor")
    net = Net()
    base = net.spawn(given("base", [Fact(jack, "likes", mary)]))
    h1 = net.spawn(branch("H1", add=[Fact(mary, "is", rich)]))
    h2 = net.spawn(branch("H2", add=[Fact(mary, "is", poor)]))
    net.wire(base, h1)
    net.wire(base, h2)
    return net, base, h1, h2


def test_cross_chain_join_works_and_siblings_stay_isolated():
    net, base, h1, h2 = _two_hypotheses()
    e1 = net.spawn(Unit("E@H1", *ADMIRES))
    e2 = net.spawn(Unit("E@H2", *ADMIRES))
    net.wire(base, e1); net.wire(h1, e1)
    net.wire(base, e2); net.wire(h2, e2)
    net.propagate()

    a1, a2 = _pairs(e1.derived("admires")), _pairs(e2.derived("admires"))
    assert a1 == {("jack", "rich")}          # ?x/?y from base, ?z from the hypothesis
    assert a2 == {("jack", "poor")}
    assert not (a1 & a2)                     # and nothing bound across the two branches


def test_a_branch_carries_its_input_through():
    """Accretion (§5) — and it is half a mechanism, not a convenience: a spawned sibling instance sees
    base ONLY because its branch carries it."""
    _net, base, h1, _h2 = _two_hypotheses()
    _net.propagate()
    assert base.output.by_pred("likes")
    assert h1.output.by_pred("likes") and h1.output.by_pred("is")


def test_a_branch_can_remove_as_well_as_add():
    """§5: additive-only cannot express *"under H, not P"* against a base that holds P."""
    jack, tall = mint("jack"), mint("tall")
    net = Net()
    base = net.spawn(given("base", [Fact(jack, "is", tall)]))
    h = net.spawn(branch("H", remove=[Fact(jack, "is", tall)]))
    net.wire(base, h)
    net.propagate()
    assert base.output.by_pred("is") and not h.output.by_pred("is")


# ── the taxonomy is by degree ───────────────────────────────────────────────

def test_kind_is_read_off_the_wiring_not_declared():
    net, base, h1, _h2 = _two_hypotheses()
    e = net.spawn(Unit("E", *ADMIRES))
    net.wire(h1, e)
    net.propagate()
    assert base.kind == "given" and base.in_degree == 0     # an axiom is a nullary computation
    assert h1.kind == "carrier"
    assert e.kind == "rule"


# ── safety, checked at construction ─────────────────────────────────────────

def test_unsafe_negation_and_unsafe_head_are_refused_at_construction():
    with pytest.raises(UnsafePattern):
        Unit("bad", (Triple(X, "likes", Y), Absent(Triple(Z, "is", Y))), Triple(X, "ok", Y))
    with pytest.raises(UnsafePattern):
        Unit("bad2", (Triple(X, "likes", Y),), Triple(X, "ok", Z))
