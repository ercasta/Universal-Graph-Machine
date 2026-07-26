"""BANDED DEGREE AS DATA — `docs/design/substrate_inversion.md` §22.2, §22.2a, §22.7.

Promoted from `bench/spike_bands.py` (25/25). The user's requirement has two halves that pull apart:
likeliness must be **carried in data** so downstream units can reason over it, and it must be **banded**
— which turns out to be what makes the substrate terminate at all.

The first test is the termination check, written first on purpose (§22.4): §22.2a predicted a failure
that would present as a HANG rather than as a wrong answer, so it is measured both ways before anything
is built on top of it.
"""
from __future__ import annotations

from units import Budget, Fact, Net, Subgraph, Triple, Var, band as B, given, mint, role, rule
from units import trace as T
from units.match import Absent, solve

X, Y = Var("x"), Var("y")


# -- §22.2a: the reason bands are not a stylistic choice ------------------------------------------------

def test_a_continuous_degree_would_destroy_the_fixpoint():
    """§22.2a, and it is §20.1(a)'s minting trap in a second costume: a quantity that varies per run
    destroys the fixpoint it is meant to annotate. Two facts differing only in degree are different
    members of a frozenset, so *"output unchanged"* never holds."""
    seen, deg = set(), 1.0
    for _ in range(40):
        deg *= 0.9
        seen.add(round(deg, 12))
    assert len(seen) == 40, "every re-derivation is a new value — propagation could never quiesce"


def test_the_finite_lattice_reaches_a_fixpoint_in_bounded_steps():
    """min on a finite chain is monotone AND idempotent, which is the whole termination argument. The
    bound is the lattice HEIGHT, so it is knowable in advance rather than hoped for."""
    seen, cur = set(), B.CERTAIN
    for _ in range(40):
        cur = B.meet(cur, B.LIKELY)
        seen.add(cur)
    assert len(seen) == 1 and len(B.SCALE) == 5


def test_a_net_carrying_bands_still_settles():
    """The model can always be made to agree with itself, so the same claim through a real net."""
    a, b = mint("a"), mint("b")
    n = Net()
    g = n.spawn(given("g", [Fact(a, "p", b)]))
    g.adds = B.grade(g.adds, Fact(a, "p", b), B.LIKELY)
    n.declare("R", (Triple(X, "p", Y),), Triple(X, "r", Y))
    bud = n.run(Budget(400))
    assert not bud.exhausted
    before = {u.name: u.output for u in n.units.values()}
    n.run(Budget(400))
    assert all(before[u.name] == u.output for u in n.units.values())


# -- the lattice ----------------------------------------------------------------------------------------

def test_the_scale_and_the_join_are_inherited_from_ugm():
    """Not invented here: `ugm/possibility.py`'s five bands and its min-band join
    ([[possibilistic-layer]])."""
    assert B.SCALE == ("very unlikely", "unlikely", "likely", "very likely", "certain")
    assert B.meet(B.CERTAIN, B.UNLIKELY) is B.UNLIKELY


def test_meet_has_the_three_properties_termination_needs():
    """Commutative (premise order must not matter), associative (grouping must not matter), idempotent
    (re-derivation must produce an identical value, and therefore stop)."""
    assert B.meet(B.LIKELY, B.CERTAIN) is B.meet(B.CERTAIN, B.LIKELY)
    assert (B.meet(B.meet(B.CERTAIN, B.LIKELY), B.UNLIKELY)
            is B.meet(B.CERTAIN, B.meet(B.LIKELY, B.UNLIKELY)))
    assert B.meet(B.LIKELY, B.LIKELY) is B.LIKELY


def test_a_band_is_an_ordinary_role_node_not_a_python_parameter():
    """`composition_architecture.md`'s deferred arc: band and scope were threaded as Python parameters,
    so a new annotation axis meant editing the evaluator. Here a band is data."""
    assert B.LIKELY is role("likely")


# -- what a band grades ---------------------------------------------------------------------------------

def test_a_band_grades_a_fact_and_is_paid_for_only_where_used():
    """A fact, not an entity — two facts about one subject can differ in degree. That needs the fact
    reified, which §22.6 made ordinary; an ungraded fact costs nothing."""
    jack, mary, rich = mint("jack"), mint("mary"), mint("rich")
    f1, f2 = Fact(jack, "likes", mary), Fact(mary, "is_a", rich)
    view = B.grade(Subgraph([f1, f2]), f1, B.LIKELY)
    assert B.band_of(view, f1) is B.LIKELY
    assert B.band_of(view, f2) is None, "no band is NOT `certain` — absence of a degree is not a degree"
    assert f1 in view and f2 in view


def test_the_object_wire_may_describe_a_fact_but_never_a_firing():
    """⭐ CORRECTED BY §22.9. This test used to assert that the object wire needed its OWN reification
    vocabulary, because reusing the trace's tripped `Net.trace_leaks()`. That split was drawn one
    predicate too wide, and it was what made degree inheritance unexpressible as a rule: a premise's band
    hung off a REIFY handle while a firing's `<from>` pointed at a TRACE handle, denoting the same fact
    without being joinable.

    **Saying WHICH FACT a handle denotes is CONTENT. Only the firing vocabulary is provenance.** §16.6's
    constraint is unchanged in force — §6a's `Absent` must never see a derivation fact."""
    a, b = mint("a"), mint("b")
    view = B.grade(Subgraph([Fact(a, "p", b)]), Fact(a, "p", b), B.LIKELY)
    assert view.predicates() & {T.OF_S, T.OF_P, T.OF_O}, "description travels on the object wire"
    assert not (view.predicates() & T.FIRING_PREDICATES), "a derivation fact never does"


# -- inheritance ----------------------------------------------------------------------------------------

def _graded_net():
    danger, high = mint("danger"), mint("high")
    n = Net()
    src = n.spawn(given("src", []))
    src.adds = B.grade(Subgraph([Fact(danger, "is_a", high)]), Fact(danger, "is_a", high), B.LIKELY)
    r = n.spawn(rule("R", (Triple(X, "is_a", high),), Triple(X, "needs", high)))
    n.wire(src, r)
    n.propagate(Budget(200))
    return n, r, danger, high


def test_a_conclusion_inherits_its_premises_band_through_the_firing_record():
    """§16.5 built `last_firing` for exactly this and then only used it via a Python stand-in. **One
    generic computation that knows nothing about any template** — never a clause per template, which is
    `form_inventory.md` §9's combinatorial explosion."""
    n, r, danger, high = _graded_net()
    assert B.band_of(B.inherit(r), Fact(danger, "needs", high)) is B.LIKELY


def test_an_unbanded_premise_inherits_nothing_rather_than_becoming_certain():
    """§16.5's control, and the one that matters: silence must not be promoted to confidence."""
    danger, high = mint("danger"), mint("high")
    n = Net()
    src = n.spawn(given("src", [Fact(danger, "is_a", high)]))
    r = n.spawn(rule("R", (Triple(X, "is_a", high),), Triple(X, "needs", high)))
    n.wire(src, r)
    n.propagate(Budget(200))
    assert B.band_of(B.inherit(r), Fact(danger, "needs", high)) is None


def test_a_two_premise_conclusion_takes_the_weaker_band():
    """A chain is as strong as its weakest link — which is what min MEANS, and why it is the join."""
    danger, high, p1 = mint("danger"), mint("high"), mint("p1")
    n = Net()
    src = n.spawn(given("src", []))
    v = Subgraph([Fact(danger, "is_a", high), Fact(danger, "at", p1)])
    v = B.grade(v, Fact(danger, "is_a", high), B.CERTAIN)
    src.adds = B.grade(v, Fact(danger, "at", p1), B.UNLIKELY)
    r = n.spawn(rule("R2", (Triple(X, "is_a", high), Triple(X, "at", Y)), Triple(X, "needs", Y)))
    n.wire(src, r)
    n.propagate(Budget(200))
    assert B.band_of(B.inherit(r), Fact(danger, "needs", p1)) is B.UNLIKELY


# -- THE USER'S REQUIREMENT -----------------------------------------------------------------------------

def test_a_downstream_unit_can_reason_over_likeliness():
    """*"Likeliness has to be carried in data, otherwise downstream computation units can't reason over
    it."* A band is an ordinary fact, so a rule FIRES ON one with no new construct."""
    n, r, danger, high = _graded_net()
    graded = B.inherit(r)
    assert len(solve((Triple(Var("h"), B.OF_S, Var("s")), Triple(Var("h"), B.BAND, B.LIKELY)), graded)) == 1

    flag = mint("flag")
    review = rule("REVIEW", (Triple(Var("h"), B.BAND, B.LIKELY), Triple(Var("h"), B.OF_S, X)),
                  Triple(X, "needs_review", flag))
    review.inputs["in"] = graded
    review.run()
    assert review.last_derived, "a unit fires on a degree, not merely reports one"

    other = rule("OTHER", (Triple(Var("h"), B.BAND, B.UNLIKELY), Triple(Var("h"), B.OF_S, X)),
                 Triple(X, "needs_review", flag))
    other.inputs["in"] = graded
    other.run()
    assert not other.last_derived, "and not on a band it was not asked about"


# -- ⚠ THE GAP ------------------------------------------------------------------------------------------

def test_a_graded_absence_is_inexpressible():
    """⭐ §16.6's THIRD NEGATION, and the spike found it is worse than that section predicted.

    The prediction was that a degree *cannot ride* an absence — that `inherit` would grade a conclusion
    by its positive premises only and quietly ignore the absent atom's own confidence. What actually
    happens: **`grade` ASSERTS the fact it grades**, so attaching a band to P puts P in the value and the
    NAF flips — the rule stops firing entirely.

    So *"probably not P"* has nowhere to live: grade P and P becomes true; say nothing and P is certainly
    absent. **It is a REPRESENTATIONAL gap, not an inheritance one, and `inherit` was never the place to
    fix it.** Recorded as a live limitation rather than a bug to patch here."""
    danger, high, p1 = mint("danger"), mint("high"), mint("p1")
    base = B.grade(Subgraph([Fact(danger, "is_a", high)]), Fact(danger, "is_a", high), B.LIKELY)

    naf = rule("NAF", (Triple(X, "is_a", high), Absent(Triple(X, "at", p1))), Triple(X, "safe", high))
    naf.inputs["in"] = base
    naf.run()
    assert Fact(danger, "safe", high) in naf.output
    assert B.band_of(B.inherit(naf), Fact(danger, "safe", high)) is B.LIKELY

    with_graded_absence = B.grade(base, Fact(danger, "at", p1), B.UNLIKELY)
    naf2 = rule("NAF2", (Triple(X, "is_a", high), Absent(Triple(X, "at", p1))), Triple(X, "safe", high))
    naf2.inputs["in"] = with_graded_absence
    naf2.run()
    assert Fact(danger, "at", p1) in with_graded_absence, "grading asserted it"
    assert not naf2.last_derived, "so the NAF flipped and the rule stopped firing"


# -- ⭐ §25.3: the seam closes ---------------------------------------------------------------------------

def test_a_facts_handle_is_a_pure_function_of_the_fact():
    """§25.3, and it is the stronger of §23.3's two options: no lookup, no coordination, no registry —
    arithmetic on the three node IDENTITIES. Derived from identity, never from name, which is what keeps
    it inside §21.2."""
    from units import reify as R
    m1, m2, rich = mint("mary"), mint("mary"), mint("rich")
    assert R.handle_key(Fact(m1, "is_a", rich)) == R.handle_key(Fact(m1, "is_a", rich))
    assert R.handle_key(Fact(m1, "is_a", rich)) != R.handle_key(Fact(m2, "is_a", rich))


def test_reification_is_idempotent():
    """A whole class of §22.8 fixpoint bugs retired rather than guarded against."""
    from units import reify as R
    a, b = mint("a"), mint("b")
    v1, _ = R.reify(Subgraph(), Fact(a, "p", b))
    v2, _ = R.reify(v1, Fact(a, "p", b))
    assert v1 == v2


def test_the_object_and_trace_handles_now_coincide():
    """§23.3's blocker, gone. This is what makes inheritance expressible as a rule."""
    from units import reify as R
    danger, high = mint("danger"), mint("high")
    n = Net()
    src = n.spawn(given("src", []))
    src.adds = B.grade(Subgraph([Fact(danger, "is_a", high)]), Fact(danger, "is_a", high), B.LIKELY)
    r = n.spawn(rule("R", (Triple(X, "is_a", high),), Triple(X, "needs", high)))
    n.wire(src, r)
    n.propagate(Budget(300))
    assert (R.handle_for(r.view(), Fact(danger, "is_a", high))
            == R.handle_for(r.trace_output, Fact(danger, "is_a", high)))


def test_degree_inheritance_is_a_rule_not_python():
    """⭐ THE §23 SEAM, CLOSED. §16.5 designed this as *one generic rule over the firing record*; it stayed
    Python because it needed a predicate variable (§22.6) and a shared handle (§25.3). Both arrived.

    It reads the TRACE wire and writes the OBJECT wire — §16.6's *"where the two networks meet"*.

    ⚠ Still hand-wired: `Net.assemble` does not know about trace wires (§20.3). That is the remaining
    half, and it is much smaller than the half that just closed."""
    from units import reify as R
    danger, high = mint("danger"), mint("high")
    n = Net()
    src = n.spawn(given("src", []))
    src.adds = B.grade(Subgraph([Fact(danger, "is_a", high)]), Fact(danger, "is_a", high), B.LIKELY)
    r = n.spawn(rule("R", (Triple(X, "is_a", high),), Triple(X, "needs", high)))
    n.wire(src, r)
    n.propagate(Budget(300))

    lhs, rhs = B.inheritance_rule()
    u = rule("INHERIT", lhs, rhs)
    u.inputs["obj"], u.inputs["tr"] = r.view(), r.trace_output
    u.run()

    concl = R.handle_key(Fact(danger, "needs", high))
    assert Fact(concl, B.BAND, B.LIKELY) in u.output
    assert B.band_of(B.inherit(r), Fact(danger, "needs", high)) is B.LIKELY, "agrees with the Python one"
