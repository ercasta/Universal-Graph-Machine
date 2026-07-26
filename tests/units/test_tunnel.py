"""THE TUNNEL SPIKE — falsifying the one claim the paradigm flip is justified by.

`model.md`'s carry-over table lists four differences from `ugm` and marks three of them retrofittable.
The fourth is not:

> **The inner loop is a circuit, so no rule ever matches a scope.**

That is what was blocking, and it is what drove the flip — so it is the thing to try to break first,
before anything is built on top of it. This module runs the *same rule object* over the base world and
inside a hypothesis, and checks that nothing about the rule changed, that the rule never mentions the
hypothesis, that the conclusion cannot leave the tunnel unless someone attached a wire to the end
marker, and that the conclusion's degree came from the match.

**What is stubbed, so the result is not over-read.** Retrieval is hardcoded (System 1 is not built), the
wiring is hand-assembled rather than described in data (`cnl.md` §4), the "good standing" judgement is a
gradable attribute rather than a second rule, and there is no boundary, no CNL, and no outer loop. The
spike tests the *circuit*, not the model.
"""
from __future__ import annotations

import pytest

from units import (EMPTY, Circuit, Emit, Graph, SealBreach, atom, atoms, named, occurrence,
                   role, rule, transform, weaker)

# --------------------------------------------------------------------------------------------
# The knowledge. ONE module-level pattern, used unchanged by every test below — the identity of
# this object is what invariant 1 is tested against.
# --------------------------------------------------------------------------------------------

ELIGIBILITY = (
    atom("m", name="member-for", out=(
        role("agent", atom("c")),
        role("duration", atom(name="over a year")),
    )),
    atom("st", name="standing", graded=("good",), out=(
        role("agent", atom("c")),          # same var -> an IDENTITY join, never a name join
    )),
    atom("d", name="loyalty discount"),
)

GETS_DISCOUNT = Emit("gets", roles=(("agent", "c"), ("patient", "d")), graded="eligible")


def eligibility_rule():
    """A fresh unit over the shared pattern. Fresh because gates latch — a unit is stateful (§5) — but
    the *pattern* is the same object every time, which is the point."""
    return rule("eligibility", ELIGIBILITY, GETS_DISCOUNT)


def base_world():
    """Paul: a member since 2019, with two payments late.

    The late payments show up as a *gradable* `good` attribute at a marginal band. In the real design
    that band would be concluded by a second rule (`model.md` §10 step 4); here it is data, which is the
    spike's biggest simplification."""
    g = EMPTY
    g, paul = named(g, "Paul")
    g, discount = named(g, "loyalty discount")
    g, over_a_year = named(g, "over a year")
    g, _member = occurrence(g, "member-for", agent=paul, duration=over_a_year)
    g, standing = occurrence(g, "standing", agent=paul)
    g = g.with_degree(standing, "good", "unlikely")        # marginal
    return g, paul, discount


def payments_settled(g: Graph) -> Graph:
    """The supposition: *"what if he pays them off?"* — an ordinary graph-to-graph transformation.

    Note what it does NOT do: it stamps no hypothesis marker, mints no world node, and sets no flag.
    There is nothing here for a downstream rule to notice."""
    for n in g.nodes:
        if g.degree(n, "good") is not None:
            g = g.with_degree(n, "good", "certain")
    return g


def conclusions(g: Graph):
    return [n for n in g.nodes if g.attr(n, "name") == "gets"]


# --------------------------------------------------------------------------------------------
# 1. The base world
# --------------------------------------------------------------------------------------------

def test_fires_in_the_base_world_at_the_matched_band():
    base, paul, discount = base_world()
    c = Circuit()
    elig = c.statement("eligibility", eligibility_rule())
    c.write_back(elig.end)

    out = c.feed(elig, base).written_back(elig.end)

    got = conclusions(out)
    assert len(got) == 1
    # §4: the firing INHERITS its match strength. Eligibility fires, but marginally, not flatly.
    assert out.degree(got[0], "eligible") == "unlikely"


# --------------------------------------------------------------------------------------------
# 2. The same rule, inside a hypothesis  — THE CLAIM
# --------------------------------------------------------------------------------------------

def test_the_same_rule_fires_inside_the_tunnel_and_concludes_more_strongly():
    """`model.md` §10 steps 4 vs 5: *the same rules ran inside and outside the hypothesis.*"""
    base, paul, discount = base_world()
    c = Circuit()
    inner = c.statement("eligibility", eligibility_rule())
    tunnel = c.statement("suppose-settled", transform("settle", payments_settled), inner)
    c.write_back(tunnel.end)

    out = c.feed(tunnel, base).written_back(tunnel.end)

    got = conclusions(out)
    assert len(got) == 1
    assert out.degree(got[0], "eligible") == "certain"      # unqualified, inside the supposition


def test_the_rule_is_byte_identical_in_both_positions():
    """Not *equivalent* — the same object. The unit differs because gates latch; the knowledge does
    not."""
    outside = eligibility_rule()
    inside = eligibility_rule()
    assert outside.pattern is ELIGIBILITY
    assert inside.pattern is ELIGIBILITY
    assert outside.pattern is inside.pattern


def test_no_rule_pattern_names_a_scope():
    """§12 invariant 1 — *the single strongest signal of regression.*

    Walk every atom the author wrote and check that none of it mentions the hypothesis, a world, a
    scope, or a marker. If this ever fails, the design has regressed."""
    forbidden = {"suppose", "settled", "hypothesis", "scope", "world", "context", "tunnel", "marker"}
    written = {str(v).lower() for p in atoms(ELIGIBILITY) for _, v in p.attrs}
    written |= {k.lower() for p in atoms(ELIGIBILITY) for k, _ in p.attrs}
    written |= {g.lower() for p in atoms(ELIGIBILITY) for g in p.graded}
    assert not (written & forbidden), f"the rule mentions a scope: {written & forbidden}"


def test_the_hypothesis_leaves_no_trace_for_a_rule_to_match():
    """The other half of the same invariant, from the data side: the supposed graph carries no marker
    distinguishing it from the base one. Isolation is the wiring, not a flag."""
    base, _, _ = base_world()
    supposed = payments_settled(base)
    assert supposed.nodes == base.nodes                       # nothing minted to mark a world
    assert supposed.edges == base.edges
    changed = {n for n in base.nodes if base.degrees.get(n) != supposed.degrees.get(n)}
    assert {base.attr(n, "name") for n in changed} == {"standing"}


def test_the_conclusion_is_stronger_inside_than_outside():
    base, _, _ = base_world()

    c1 = Circuit()
    s1 = c1.statement("eligibility", eligibility_rule())
    c1.write_back(s1.end)
    out1 = c1.feed(s1, base).written_back(s1.end)

    c2 = Circuit()
    inner = c2.statement("eligibility", eligibility_rule())
    t2 = c2.statement("suppose-settled", transform("settle", payments_settled), inner)
    c2.write_back(t2.end)
    out2 = c2.feed(t2, base).written_back(t2.end)

    b1 = out1.degree(conclusions(out1)[0], "eligible")
    b2 = out2.degree(conclusions(out2)[0], "eligible")
    assert weaker(b1, b2)


# --------------------------------------------------------------------------------------------
# 3. The seal, and crossing
# --------------------------------------------------------------------------------------------

def test_a_conclusion_cannot_leave_the_tunnel_unless_someone_attached():
    """§6: *getting out is one explicit act.* Same circuit as the passing case, minus the one wire."""
    base, _, _ = base_world()
    c = Circuit()
    inner = c.statement("eligibility", eligibility_rule())
    tunnel = c.statement("suppose-settled", transform("settle", payments_settled), inner)
    # deliberately NO write_back

    run = c.feed(tunnel, base)

    assert run.written_back(tunnel.end) is EMPTY
    # …and it is not that nothing happened: the rule did fire, inside.
    assert inner._last.firings == 1


def test_the_base_world_is_untouched_by_the_hypothesis():
    """The circuit never mutates the store (§9): a value went in, a different value came out."""
    base, _, _ = base_world()
    c = Circuit()
    inner = c.statement("eligibility", eligibility_rule())
    tunnel = c.statement("suppose-settled", transform("settle", payments_settled), inner)
    c.write_back(tunnel.end)

    c.feed(tunnel, base)

    assert conclusions(base) == []
    assert base.degree([n for n in base.nodes if base.attr(n, "name") == "standing"][0],
                       "good") == "unlikely"


def test_a_unit_cannot_mutate_the_value_it_was_handed():
    """§5/§12 invariant 3. The tunnel's guarantee is that a supposition cannot reach the base world, and
    that is worth nothing if the graph handed to a unit is writable through its own fields — isolation
    would be a convention rather than a fact. Caught once already: a frozen dataclass around plain dicts
    does not give this."""
    base, _, _ = base_world()
    standing = [n for n in base.nodes if base.attr(n, "name") == "standing"][0]

    with pytest.raises(TypeError):
        base.degrees[standing]["good"] = "certain"
    with pytest.raises(TypeError):
        base.attrs[standing]["name"] = "something else"
    with pytest.raises(TypeError):
        base.degrees[standing] = {}

    assert base.degree(standing, "good") == "unlikely"


def test_wiring_into_a_sealed_interior_is_refused():
    """§12 invariant 9 — *no wire terminates inside a sealed span.* Mechanically, the only handle on a
    statement is its end marker; this is the check for anyone who reaches past the API."""
    c = Circuit()
    interior = eligibility_rule()
    stmt = c.statement("eligibility", interior)
    sink = transform("sink", lambda g: g)

    with pytest.raises(SealBreach):
        c.wire(interior, sink)

    c.wire(stmt.end, sink)          # the end marker, however, is attachable — that is the one exit


def test_a_statement_may_be_attached_to_but_only_from_its_end():
    """The asymmetry stated in `Circuit.wire`: attaching TO a statement (at its begin marker) is how
    anything is fed at all; attaching FROM one is only ever at the end."""
    c = Circuit()
    a = c.statement("a", eligibility_rule())
    b = c.statement("b", transform("b", lambda g: g))
    c.wire(a.end, b)                                        # to a statement: fine
    with pytest.raises(SealBreach):
        c.wire(b.steps[0], a)                               # from a unit: never


# --------------------------------------------------------------------------------------------
# 4. Outcomes are positive facts
# --------------------------------------------------------------------------------------------

def test_an_unfed_gate_reports_a_miss_rather_than_silence():
    """§8/§9: a starved gate emits a **miss** carrying what it wanted — the natural signal for reaching
    outside, and the same shape as the out-of-fuel handler."""
    c = Circuit()
    stmt = c.statement("eligibility", eligibility_rule())

    misses = c.feed(stmt, EMPTY).misses()

    assert misses == []                     # the gate WAS fed — with nothing, which is not the same
    empty_out = stmt._last.output
    assert conclusions(empty_out) == []     # nothing matched: starved, NOT "Paul is ineligible"


def test_a_never_fed_gate_is_a_miss_and_names_what_it_wanted():
    c = Circuit()
    stmt = c.statement("eligibility", eligibility_rule())
    downstream = eligibility_rule()
    c.wire(stmt.end, downstream)

    misses = downstream.misses()

    assert len(misses) == 1
    assert "member-for" in misses[0].wanted


# --------------------------------------------------------------------------------------------
# 5. Sibling hypotheses — the case that actually killed `ugm`
# --------------------------------------------------------------------------------------------

def test_two_sibling_hypotheses_do_not_contaminate_each_other():
    """**The strongest form of the claim.**

    `ugm` needed a whole apparatus for this — `0006` (a producer joins an instance only if comparable
    with every other), later amended by `0038` (only a carrier can fork a world) — because two
    hypotheses over one base live in the same store and every rule had to know which world it was
    matching. That is the machinery `model.md` §6 says becomes unnecessary.

    Here: two suppositions off the same base, in **one circuit**, each with its own copy of the same
    rule. Nothing declares a world, nothing compares two, and no rule mentions either."""
    base, _, _ = base_world()

    def payments_lapse(g: Graph) -> Graph:
        for n in g.nodes:
            if g.degree(n, "good") is not None:
                g = g.with_degree(n, "good", "very unlikely")
        return g

    c = Circuit()
    settled_inner = c.statement("eligibility", eligibility_rule())
    settled = c.statement("suppose-settled", transform("settle", payments_settled), settled_inner)
    lapsed_inner = c.statement("eligibility", eligibility_rule())
    lapsed = c.statement("suppose-lapsed", transform("lapse", payments_lapse), lapsed_inner)
    c.write_back(settled.end)
    c.write_back(lapsed.end)

    run_a = c.feed(settled, base)
    run_b = c.feed(lapsed, base)

    out_a = run_a.written_back(settled.end)
    out_b = run_b.written_back(lapsed.end)

    assert out_a.degree(conclusions(out_a)[0], "eligible") == "certain"
    assert out_b.degree(conclusions(out_b)[0], "eligible") == "very unlikely"

    # …and neither world's conclusion is anywhere in the other.
    assert len(conclusions(out_a)) == 1
    assert len(conclusions(out_b)) == 1
    assert not (set(conclusions(out_a)) & set(conclusions(out_b)))


def test_a_sibling_hypothesis_does_not_reach_the_base_world():
    """The containment half: neither supposition's conclusion is in the persistent data unless it
    crossed. Two tunnels, one wire out."""
    base, _, _ = base_world()

    c = Circuit()
    inner_a = c.statement("eligibility", eligibility_rule())
    a = c.statement("suppose-a", transform("settle", payments_settled), inner_a)
    inner_b = c.statement("eligibility", eligibility_rule())
    b = c.statement("suppose-b", transform("settle2", payments_settled), inner_b)
    c.write_back(a.end)                     # only A crosses

    run_a, run_b = c.feed(a, base), c.feed(b, base)

    assert conclusions(run_a.written_back(a.end)) != []
    assert run_b.written_back(b.end) is EMPTY
    assert conclusions(base) == []          # the store never moved
