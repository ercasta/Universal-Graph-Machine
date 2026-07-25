"""The TWO negations, and what fuel is for (`docs/design/substrate_inversion.md` §6, §6b, §7).

§6's claim is that negation splits, and that only one half is hard:

  (a) NAF over the value ON A WIRE — exact and immediate. The value that arrived is FINISHED, so absence
      is decidable with no drain, no fixpoint, no fuel. This is the negation the substrate gets for free.
  (b) NAF over the OPEN DERIVATION — semi-decidable; the honest answer is a budget, and exhaustion yields
      UNKNOWN, never NO.

Also pinned here: §7's claim that revision is RE-RUNNING rather than retracting, and §6b's identified
hole — a late-wired producer can invalidate a unit that already concluded from absence.
"""
from __future__ import annotations

import pytest

from units import (Absent, Budget, Fact, Net, Subgraph, Triple, Unit, Var,
                   Verdict, branch, given, mint)

X, Y = Var("x"), Var("y")


# ── (a) NAF over the value on a wire: exact, immediate, no fuel ─────────────

def test_absence_on_a_wire_is_decided_immediately():
    jack, tall, flag = mint("jack"), mint("tall"), mint("odd")
    u = Unit("odd_one", (Triple(X, "is", tall), Absent(Triple(X, "is", flag))),
             Triple(X, "verdict", flag))
    u.inputs["src"] = Subgraph([Fact(jack, "is", tall)])
    assert u.run()
    assert {f.s.name for f in u.derived("verdict")} == {"jack"}


def test_the_same_absence_is_withdrawn_by_RE_RUNNING_not_by_retraction():
    """§7. Nothing is retracted because nothing was ever shared: the input changed, so the unit recomputes
    and the conclusion is simply not in the new output. No cascade, no copy-on-delete, no archive."""
    jack, tall, flag = mint("jack"), mint("tall"), mint("odd")
    u = Unit("odd_one", (Triple(X, "is", tall), Absent(Triple(X, "is", flag))),
             Triple(X, "verdict", flag))
    u.inputs["src"] = Subgraph([Fact(jack, "is", tall)])
    u.run()
    assert u.derived("verdict")

    u.inputs["src"] = Subgraph([Fact(jack, "is", tall), Fact(jack, "is", flag)])
    assert u.run(), "the output must change"
    assert not u.derived("verdict")


def test_absence_is_relative_to_the_wire_which_is_the_honest_reading():
    """A unit's reach is its IN-DEGREE (§2b). Two units with the same rule and different in-edges give
    different answers, and that is correct rather than a defect: each says only what it could see."""
    jack, tall, flag = mint("jack"), mint("tall"), mint("odd")
    lhs = (Triple(X, "is", tall), Absent(Triple(X, "is", flag)))
    net = Net()
    base = net.spawn(given("base", [Fact(jack, "is", tall)]))
    h = net.spawn(branch("H", add=[Fact(jack, "is", flag)]))
    net.wire(base, h)
    narrow = net.spawn(Unit("narrow", lhs, Triple(X, "verdict", flag)))
    wide = net.spawn(Unit("wide", lhs, Triple(X, "verdict", flag)))
    net.wire(base, narrow)
    net.wire(h, wide)
    net.propagate()
    assert narrow.derived("verdict") and not wide.derived("verdict")


# ── (b) NAF over the open derivation: fuel, and UNKNOWN is not NO ───────────

def test_exhausted_budget_yields_UNKNOWN_never_NO():
    b = Budget(limit=3)
    assert b.verdict(found=False) == Verdict.NO          # finished with fuel to spare
    b.spend(5)
    assert b.exhausted and b.verdict(found=False) == Verdict.UNKNOWN
    assert b.verdict(found=True) == Verdict.YES


def test_a_verdict_refuses_to_be_truthy():
    """UNKNOWN collapsing into NO is the silent failure this three-valued type exists to prevent."""
    with pytest.raises(TypeError):
        bool(Verdict.UNKNOWN)


def test_recursion_is_unrolled_by_assembly_and_bounded_by_fuel():
    """§0's central advantage over the biological analogy: depth is assembled, not grown. A transitive
    chain gets its depth from repeated instantiation, and the loop is bounded by FUEL rather than by the
    topology — which is why an exhausted budget must be reportable."""
    a, b, c, d = mint("a"), mint("b"), mint("c"), mint("d")
    net = Net()
    net.spawn(given("base", [Fact(a, "next", b), Fact(b, "next", c), Fact(c, "next", d)]))
    net.declare("T", (Triple(X, "next", Y),), Triple(X, "reaches", Y))
    net.declare("T2", (Triple(X, "reaches", Y), Triple(Y, "next", Var("z"))),
                Triple(X, "reaches", Var("z")))
    budget = net.run(Budget(limit=500))
    reached = {(f.s.name, f.o.name) for _u, f in net.derived_anywhere("reaches")}
    assert ("a", "d") in reached, "transitive depth must be reachable"
    assert not budget.exhausted


def test_a_tiny_budget_stops_rather_than_hangs():
    a, b = mint("a"), mint("b")
    net = Net()
    net.spawn(given("base", [Fact(a, "next", b)]))
    net.declare("T", (Triple(X, "next", Y),), Triple(X, "reaches", Y))
    budget = net.run(Budget(limit=2))
    assert budget.exhausted
    assert budget.verdict(found=False) == Verdict.UNKNOWN


# ── §6b: the identified hole ────────────────────────────────────────────────

def test_a_late_wired_producer_invalidates_a_conclusion_taken_from_absence():
    """§6b, the one hole the design names: lazy spawn can wire a NEW producer into a unit that has already
    fired, so 'I have all my inputs' is never final and an absence-decides is revocable.

    The fix is already the architecture's own: REFIRE. The conclusion is withdrawn by recomputation, not
    by retraction — but the test exists because the WINDOW in which the stale conclusion was visible is
    real, and any consumer that read it during that window read something the network later un-said."""
    jack, tall, flag = mint("jack"), mint("tall"), mint("odd")
    net = Net()
    base = net.spawn(given("base", [Fact(jack, "is", tall)]))
    late = net.spawn(given("late", [Fact(jack, "is", flag)]))
    u = net.spawn(Unit("odd_one", (Triple(X, "is", tall), Absent(Triple(X, "is", flag))),
                       Triple(X, "verdict", flag)))
    net.wire(base, u)
    net.propagate()
    assert u.derived("verdict"), "concluded from absence, with only `base` wired in"

    net.wire(late, u)                      # the hole: in-degree grows AFTER the unit concluded
    net.propagate()
    assert not u.derived("verdict"), "and refire withdraws it — no cascade, no retraction"
