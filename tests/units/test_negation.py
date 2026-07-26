"""EXPLICIT NEGATION — `docs/design/substrate_inversion.md` §22.7a, §22.8.

Promoted from `bench/spike_explicit_negation.py` (22/22). The user's fix for §22.7a, and it is a change
to what the DATA SUBGRAPH can say rather than to the computation units: *"probably not P"* is two nodes —
a `not` node carrying a grade, pointing at P.

The tests are grouped as fix / inertness / **cost** / win / limits, because the cost is the part that
decides whether this was cheap.
"""
from __future__ import annotations

from units import Fact, Subgraph, Triple, Var, band as B, mint, negation as N, reify as R, rule

X, Y = Var("x"), Var("y")


def _world():
    jack, mary, rich = mint("jack"), mint("mary"), mint("rich")
    P = Fact(jack, "likes", mary)
    return jack, mary, rich, P


# -- the fix --------------------------------------------------------------------------------------------

def test_probably_not_p_no_longer_asserts_p():
    """§22.7a's defect, gone. `band.grade` asserts what it grades — talking ABOUT a fact and CLAIMING it
    finally come apart, which is all the fix ever was."""
    jack, mary, rich, P = _world()
    v = N.deny(Subgraph([Fact(mary, "is_a", rich)]), P, B.LIKELY)
    assert P not in v
    assert N.denied(v, P)
    assert N.denial_band(v, P) is B.LIKELY


def test_it_needed_no_new_construct():
    """§22.6 made a fact able to occupy a node slot, and `reify.py` already held the vocabulary because
    §22.7's band needed the same thing from an unrelated direction. §17.E predicted exactly this."""
    jack, mary, rich, P = _world()
    v, h = R.reify(Subgraph(), P)
    assert P not in v, "reify describes a fact without claiming it"
    assert R.fact_of(v, h) == P


def test_an_ungraded_denial_is_not_a_certain_one():
    """The same control as `band.band_of`: absence of a degree is not a degree."""
    jack, mary, rich, P = _world()
    v = N.deny(Subgraph(), P)
    assert N.denied(v, P) and N.denial_band(v, P) is None


# -- inertness ------------------------------------------------------------------------------------------

def test_a_denial_is_inert_to_ordinary_matching():
    """The failure that would have sunk it: asserting *not P* must not make P matchable."""
    jack, mary, rich, P = _world()
    v = N.deny(Subgraph([Fact(mary, "is_a", rich)]), P, B.LIKELY)
    r = rule("R", (Triple(X, "likes", Y),), Triple(X, "seen", Y))
    r.inputs["w"] = v
    r.run()
    assert not r.last_derived, "a denial is not P wearing a hat"


# -- ⚠ THE COST -----------------------------------------------------------------------------------------

def test_absent_conflates_nothing_known_with_denied():
    """⚠ THE PRICE, and it is the classical NAF-vs-strong-negation split: the proposal RELOCATES the
    ambiguity rather than removing it. There are now three states and `Absent` distinguishes two."""
    from units.match import Absent
    jack, mary, rich, P = _world()

    def fires(view):
        u = rule("N", (Triple(Y, "is_a", rich), Absent(Triple(jack, "likes", mary))),
                 Triple(Y, "safe", rich))
        u.inputs["w"] = view
        u.run()
        return bool(u.last_derived)

    nothing_known = Subgraph([Fact(mary, "is_a", rich)])
    denied = N.deny(Subgraph([Fact(mary, "is_a", rich)]), P, B.LIKELY)
    asserted = Subgraph([P, Fact(mary, "is_a", rich)])

    assert fires(nothing_known)
    assert fires(denied), "`Absent` cannot tell 'denied' from 'unknown'"
    assert not fires(asserted)


def test_the_other_negation_is_an_ordinary_pattern():
    """And the cost is bounded: a rule that means *actively denied* asks for the denial. No new atom
    kind, no second matcher — the rule author simply has to choose which negation is meant."""
    jack, mary, rich, P = _world()
    denied = N.deny(Subgraph([Fact(mary, "is_a", rich)]), P, B.LIKELY)

    def fires(view):
        u = rule("D", (Triple(Var("n"), N.DENIES, Var("h")), Triple(Var("h"), R.OF_S, X)),
                 Triple(X, "was_denied", mary))
        u.inputs["w"] = view
        u.run()
        return bool(u.last_derived)

    assert fires(denied)
    assert not fires(Subgraph([Fact(mary, "is_a", rich)]))


# -- the win --------------------------------------------------------------------------------------------

def test_a_unit_can_reason_over_a_denial_and_its_degree():
    """Why it belongs in the data at all. §22.7 did this for degree; this does it for negation."""
    jack, mary, rich, P = _world()
    flag = mint("flag")

    def fires(view):
        u = rule("DOUBT", (Triple(Var("n"), N.DENIES, Var("h")), Triple(Var("n"), B.BAND, B.LIKELY),
                           Triple(Var("h"), R.OF_S, X)),
                 Triple(X, "worth_checking", flag))
        u.inputs["w"] = view
        u.run()
        return bool(u.last_derived)

    assert fires(N.deny(Subgraph(), P, B.LIKELY)), "fires on a denial we are only probably sure of"
    assert not fires(N.deny(Subgraph(), P, B.CERTAIN)), "and not on one we are certain of"


def test_p_and_not_p_are_a_distribution_not_a_contradiction():
    """⭐ A set could never represent this before. With bands it is not an inconsistency to be resolved
    but competing degrees — [[possibilistic-layer]]'s ranked hypotheses, arriving for free.

    The honest half: **nothing reconciles them.** A rule asking for P fires and ignores the denial
    entirely. A RECONCILIATION unit is what is missing, and it does not exist."""
    jack, mary, rich, P = _world()
    both = N.deny(Subgraph([P]), P, B.UNLIKELY)
    assert P in both and N.denied(both, P)

    r = rule("R", (Triple(X, "likes", Y),), Triple(X, "seen", Y))
    r.inputs["w"] = both
    r.run()
    assert r.last_derived, "the denial is ignored — reconciliation is unbuilt"


def test_a_unit_can_emit_a_denial_instead_of_falling_silent():
    """§16.2's gate, sharpened: *"I have nothing"* and *"I deny"* stop being the same act."""
    jack, mary, rich, P = _world()
    silent = rule("S", (Triple(X, "likes", Y),), Triple(X, "seen", Y))
    silent.inputs["w"] = Subgraph([Fact(mary, "is_a", rich)])
    silent.run()
    assert not silent.output

    denial = N.deny(Subgraph([Fact(mary, "is_a", rich)]), P, B.LIKELY)
    assert N.denied(denial, P) and P not in denial


# -- ⚠ the limit ----------------------------------------------------------------------------------------

def test_a_derived_denial_needs_a_key_or_the_fixpoint_never_closes():
    """⚠ §20.1(a)'s trap for the THIRD time — after the trace's firing nodes and the band's handles.
    `deny` mints a `not` node, so two denials of one fact are different values and a re-derived denial
    never converges. Asserted denials are safe; a DERIVED one must pass `key=`.

    The pattern is now firm enough to state as a rule: **anything minted per run must be keyed, or it
    destroys the fixpoint it is annotating.**"""
    jack, mary, rich, P = _world()
    base = Subgraph([Fact(mary, "is_a", rich)])
    assert N.deny(base, P, B.LIKELY) != N.deny(base, P, B.LIKELY), "unkeyed diverges"

    k = mint("denier")
    assert N.deny(base, P, B.LIKELY, key=k) == N.deny(base, P, B.LIKELY, key=k), "keyed converges"
