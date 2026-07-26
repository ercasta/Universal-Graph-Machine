"""THE WIRING REGISTER — the assembler works from data alone (`model.md` §11, `cnl.md` §4).

`test_tunnel.py` hand-assembled its circuit through the `Circuit` API, which is exactly what §11
forbids: *"the front end targets data, never an engine API — otherwise the system can say things it
cannot learn."* This module rebuilds the identical scenario as a **described graph** and checks it
behaves the same, that the assembler adds nothing the description did not ask for, and that the seal
survives the trip through data.

**What this does NOT show.** `cnl.md` §4's actual claim is that *rules* write this register during
comprehension. The descriptions here are hand-written. So this tests the **assembler** half — that a
dull, semantics-free reader is sufficient — and leaves the rule-writes-it half untested.
"""
from __future__ import annotations

import pytest

from units import Description, SealBreach, Statement, assemble
from tests.units.test_tunnel import base_world, conclusions, payments_settled


def eligibility_description(*, suppose: bool = False) -> tuple:
    """The `model.md` §10 scenario, as data. Note there is no Python callable anywhere in here — the
    supposition is a `stamp` effect, so *"what if he pays them off?"* is describable."""
    d = Description()

    member = d.atom("m", name="member-for", out=(
        d.role("agent", d.atom("c")),
        d.role("duration", d.atom(name="over a year")),
    ))
    standing = d.atom("st", name="standing", graded="good", out=(
        d.role("agent", d.atom("c")),           # same var -> identity join, described as data
    ))
    discount = d.atom("d", name="loyalty discount")

    elig_unit = d.unit("eligibility-rule", (member, standing, discount),
                       (d.mint("gets", args=(("agent", "c"), ("patient", "d")), graded="eligible"),))
    elig = d.statement("eligibility", elig_unit)

    if not suppose:
        d.write_back(elig)
        d.feeds(elig)
        return d, "eligibility"

    settle_unit = d.unit("settle", (d.atom("s", name="standing", graded="good"),),
                         (d.stamp("s", "good", "certain"),))
    settle = d.statement("settle", settle_unit)
    tunnel = d.statement("suppose-settled", settle, elig)
    d.write_back(tunnel)
    d.feeds(tunnel)
    return d, "suppose-settled"


# --------------------------------------------------------------------------------------------
# 1. Parity with the hand-assembled circuit
# --------------------------------------------------------------------------------------------

def test_described_assembly_reproduces_the_base_world_result():
    base, _, _ = base_world()
    d, root = eligibility_description()

    a = assemble(d.g)
    out = a.feed(root, base).written_back(a.port(root))

    got = conclusions(out)
    assert len(got) == 1
    assert out.degree(got[0], "eligible") == "unlikely"


def test_described_assembly_reproduces_the_tunnel_result():
    base, _, _ = base_world()
    d, root = eligibility_description(suppose=True)

    a = assemble(d.g)
    out = a.feed(root, base).written_back(a.port(root))

    got = conclusions(out)
    assert len(got) == 1
    assert out.degree(got[0], "eligible") == "certain"


def test_the_supposition_needs_no_python():
    """The escape hatch is closed. `payments_settled` was a Python callable doing what no rule could
    describe; the described version is a pattern and a `stamp`, and it produces the same graph."""
    base, _, _ = base_world()
    d = Description()
    unit = d.unit("settle", (d.atom("s", name="standing", graded="good"),),
                  (d.stamp("s", "good", "certain"),))
    stmt = d.statement("settle", unit)
    d.write_back(stmt)

    a = assemble(d.g)
    described = a.feed("settle", base).written_back(a.port("settle"))
    by_hand = payments_settled(base)

    standing = [n for n in base.nodes if base.attr(n, "name") == "standing"][0]
    assert described.degree(standing, "good") == by_hand.degree(standing, "good") == "certain"


def test_the_described_pattern_decodes_to_the_hand_written_one():
    """The strongest available parity statement: the data does not merely *behave* like the Python
    pattern, it **decodes to an equal object**. Which is what makes decoding transcription rather than
    interpretation (`assemble.py`'s docstring) — total, mechanical, and with no room for a choice."""
    from units.assemble import _pat, _roles
    from tests.units.test_tunnel import ELIGIBILITY

    d, _ = eligibility_description()
    unit = [n for n in d.g.nodes
            if d.g.attr(n, "name") == "unit" and d.g.attr(n, "label") == "eligibility-rule"][0]

    decoded = tuple(_pat(d.g, p) for p in _roles(d.g, unit, "pattern"))

    assert decoded == ELIGIBILITY


def test_the_description_is_verbose_and_that_is_the_cost():
    """`cnl.md` §5 flags verbosity as a real cost rather than a wart. Measured here so the number is
    visible when it starts to hurt: one rule, one statement, and a write-back."""
    d, _ = eligibility_description()

    assert len(d.g.nodes) > 40           # ~47 nodes for ONE rule
    assert len(d.g.edges) == len(d.g.nodes) - 1


# --------------------------------------------------------------------------------------------
# 2. The assembler adds nothing
# --------------------------------------------------------------------------------------------

def test_two_undescribed_statements_are_not_connected():
    """§12 invariant 4 and §11 together: the assembler wires only what is described. Two statements in
    one description with no wire between them must stay unconnected — feeding one may not run the
    other."""
    base, _, _ = base_world()
    d = Description()
    a_unit = d.unit("a", (d.atom("x", name="standing", graded="good"),),
                    (d.stamp("x", "good", "certain"),))
    b_unit = d.unit("b", (d.atom("y", name="standing", graded="good"),),
                    (d.stamp("y", "good", "very unlikely"),))
    d.statement("A", a_unit)
    d.statement("B", b_unit)

    asm = assemble(d.g)
    asm.feed("A", base)

    assert asm.by_label["B"]._last.firings == 0


def test_a_described_wire_connects_them_and_nothing_else_does():
    base, _, _ = base_world()
    d = Description()
    a_unit = d.unit("a", (d.atom("x", name="standing", graded="good"),),
                    (d.stamp("x", "good", "certain"),))
    b_unit = d.unit("b", (d.atom("y", name="standing", graded="good"),), ())
    stmt_a = d.statement("A", a_unit)
    stmt_b = d.statement("B", b_unit)
    d.wire(stmt_a, stmt_b)

    asm = assemble(d.g)
    asm.feed("A", base)

    assert asm.by_label["B"]._last.firings == 1


def test_the_assembler_mints_no_units_of_its_own():
    d, root = eligibility_description(suppose=True)
    described_units = sum(1 for n in d.g.nodes if d.g.attr(n, "name") == "unit")

    asm = assemble(d.g)

    assert described_units == 2                      # settle + eligibility
    assert len(asm.circuit.units) == described_units


# --------------------------------------------------------------------------------------------
# 3. The seal survives the trip through data
# --------------------------------------------------------------------------------------------

def test_a_wire_out_of_a_units_interior_is_refused_even_when_described():
    """The description language has no name for a statement's interior (`cnl.md` §3 — only statements
    carry labels, and a label denotes the end marker). Reaching past that anyway, by naming the unit
    node directly, must still be refused."""
    d = Description()
    interior = d.unit("interior", (d.atom("x", name="standing"),), ())
    d.statement("sealed", interior)
    sink_unit = d.unit("sink", (d.atom("y", name="standing"),), ())
    sink = d.statement("sink", sink_unit)
    d.wire(interior, sink)                           # naming the UNIT, not the statement

    with pytest.raises(SealBreach):
        assemble(d.g)


def test_write_back_may_only_name_a_statement():
    d = Description()
    u = d.unit("u", (d.atom("x", name="standing"),), ())
    d.statement("s", u)
    d.write_back(u)                                  # a unit, not the statement

    with pytest.raises(ValueError, match="end marker"):
        assemble(d.g)


# --------------------------------------------------------------------------------------------
# 4. Nesting round-trips  (§12 invariant 2 — the one flagged as most likely to drift)
# --------------------------------------------------------------------------------------------

def test_described_nesting_becomes_the_same_nesting():
    d, root = eligibility_description(suppose=True)

    asm = assemble(d.g)
    tunnel = asm.by_label[root]

    assert isinstance(tunnel, Statement)
    assert [s.label for s in tunnel.steps] == ["settle", "eligibility"]
    assert all(isinstance(s, Statement) for s in tunnel.steps)


def test_step_order_comes_from_the_description_not_from_iteration_order():
    """Steps are ordered by an `index` attribute on the **role node**, not by graph iteration. If that
    degrades, the tunnel runs the eligibility rule *before* the supposition and the answer is silently
    wrong rather than an error.

    ⚠ **Repeated deliberately.** The first version of this test asserted once and passed even with
    ordering removed: each `Description` mints fresh nodes, so frozenset iteration order varies per
    instance and a single assertion is a coin flip. Order bugs here are *flaky*, which is precisely what
    makes them dangerous — so this samples enough fresh descriptions to make luck implausible."""
    base, _, _ = base_world()

    for _ in range(25):
        d, root = eligibility_description(suppose=True)
        asm = assemble(d.g)

        tunnel = asm.by_label[root]
        assert [s.label for s in tunnel.steps] == ["settle", "eligibility"]

        out = asm.feed(root, base).written_back(asm.port(root))
        assert out.degree(conclusions(out)[0], "eligible") == "certain"


def test_step_order_is_taken_from_the_index_not_the_creation_order():
    """The sharper form: create the steps in one order and describe them in another. Anything reading
    creation order, insertion order or node id gets this backwards.

    Repeated for the same reason as the test above — a single sample is a coin flip."""
    base, _, _ = base_world()

    for _ in range(25):
        d = Description()

        # created FIRST, but must run SECOND
        elig = d.statement("eligibility", d.unit(
            "eligibility-rule",
            (d.atom("st", name="standing", graded="good"),),
            (d.mint("verdict", args=(("about", "st"),), graded="eligible"),)))

        # created SECOND, but must run FIRST
        settle = d.statement("settle", d.unit(
            "settle",
            (d.atom("s", name="standing", graded="good"),),
            (d.stamp("s", "good", "certain"),)))

        d.write_back(d.statement("tunnel", settle, elig))

        asm = assemble(d.g)
        out = asm.feed("tunnel", base).written_back(asm.port("tunnel"))

        verdict = [n for n in out.nodes if out.attr(n, "name") == "verdict"]
        assert len(verdict) == 1
        # "certain", not "unlikely" — the supposition ran first, as described
        assert out.degree(verdict[0], "eligible") == "certain"
