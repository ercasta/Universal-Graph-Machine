"""The acceptance harness for `docs/units/revision-01-standing-circuits.md` §7.

Six rows carried over from `attachment.md` §4, two retired (the cooldown rows), three new. Plus the
claim the whole revision rests on: **a derived fact is positioned, never pooled.**
"""
from __future__ import annotations

from units.graph import EMPTY, Graph, Node, named, occurrence, role_edge
from units.match import atom, role
from units.standing import SURGE_AT, Cell, Network, StandingUnit, holds
from units.unit import Emit


# -- fixtures ------------------------------------------------------------------------------------

def socrates_world():
    """*Socrates is a man.* Encoded as §3 requires: an occurrence node with role nodes."""
    g = EMPTY
    g, socrates = named(g, "Socrates")
    g, man = named(g, "man")
    g, _ = occurrence(g, "is-a", subject=socrates, kind=man)
    return g, socrates, man


MORTAL_RULE = (
    atom("occ", name="is-a", out=(
        role("subject", atom("s")),
        role("kind", atom(name="man")),
    )),
)


def mortal_unit(**kw) -> StandingUnit:
    return StandingUnit("all-men-are-mortal", MORTAL_RULE,
                        Emit("mortal", roles=(("of", "s"),)), **kw)


# -- 1. the claim --------------------------------------------------------------------------------

def test_a_standing_unit_holds_its_conclusion():
    g, socrates, _ = socrates_world()
    n = Network()
    ax = n.axiom(g)
    u = n.add(mortal_unit())
    n.wire(ax, u)
    n.revive()

    assert holds(u.cell.held.graph, "mortal")
    assert holds(n.world(), "mortal")


def test_the_conclusion_is_positioned_not_pooled():
    """The headline, and the version that actually discriminates.

    The first draft of this test asserted only that `mortal` lives at its producer and nowhere else —
    which **carry-forward also satisfies**, because carry-forward pollutes the conclusion cell with the
    premises rather than the other way round. Mutation testing caught it. The claim that separates
    positioning from a pool-on-a-wire is `0008` **subset output**: a cell holds what its unit derived
    and *nothing else*."""
    g, _, _ = socrates_world()
    n = Network()
    ax = n.axiom(g)
    u = n.add(mortal_unit())
    n.wire(ax, u)
    n.revive()

    assert holds(u.cell.held.graph, "mortal")
    # Subset output: the premise did NOT travel down the wire into the conclusion's cell.
    assert not holds(u.cell.held.graph, "is-a")
    assert not holds(u.cell.held.graph, "man")
    # …and the conclusion exists in exactly one place, which is its producer.
    assert not holds(ax.held.graph, "mortal")
    producers = [c for c in n.cells() if c.held and holds(c.held.graph, "mortal")]
    assert producers == [u.cell]


def test_provenance_is_the_wiring():
    """*Why do you believe this?* is a walk from the cell to what feeds its unit — no derivation was
    written back, and no provenance channel exists."""
    g, _, _ = socrates_world()
    n = Network()
    ax = n.axiom(g)
    u = n.add(mortal_unit())
    n.wire(ax, u)
    n.revive()

    supports = [src for (src, dst, _) in n.wires if dst is u]
    assert supports == [ax]


# -- 2. revive from axioms (the new harness row) -------------------------------------------------

def test_changing_an_axiom_makes_the_conclusion_absent_with_nothing_retracted():
    """The central claim of the revision. Rebuild the axiom without the premise, revive, and the
    conclusion is simply not produced. No retraction, no cascade, no invalidation."""
    g, socrates, man = socrates_world()
    n = Network()
    ax = n.axiom(g)
    u = n.add(mortal_unit())
    n.wire(ax, u)
    n.revive()
    assert holds(n.world(), "mortal")

    # A mutating rule edits asserted data: Socrates is no longer a man.
    from units.standing import Value
    stripped = EMPTY
    stripped, s2 = named(stripped, "Socrates")
    ax.held = Value(stripped)

    n.revive()
    assert not holds(n.world(), "mortal")
    assert u.cell.held is None


def test_graph_state_is_a_pure_function_of_axioms_and_wiring():
    """Invariant 15. Two revives with nothing changed produce the same content — no accretion, and no
    cooldown table needed to prevent it."""
    g, _, _ = socrates_world()
    n = Network()
    ax = n.axiom(g)
    u = n.add(mortal_unit())
    n.wire(ax, u)

    n.revive()
    first = len(u.cell.held.graph.nodes)
    for _ in range(5):
        n.revive()
    assert len(u.cell.held.graph.nodes) == first


# -- 3. cycles ------------------------------------------------------------------------------------

def ping_pong(n: Network, seed: Graph):
    """Two units feeding each other: A sees `ping` and emits `pong`; B sees `pong` and emits `ping`."""
    a = n.add(StandingUnit("A", (atom("x", name="ping"),), Emit("pong", roles=(("of", "x"),))))
    b = n.add(StandingUnit("B", (atom("x", name="pong"),), Emit("ping", roles=(("of", "x"),))))
    n.wire(a.cell, b)
    n.wire(b.cell, a)
    return a, b


def test_an_unpowered_cycle_is_structurally_silent():
    """§3. A cycle unreachable from any axiom is never fired, so it needs no detection at all. This is
    why no well-founded support check is required."""
    n = Network()
    n.axiom(EMPTY)                       # nothing to say
    a, b = ping_pong(n, EMPTY)
    n.revive()

    assert a.cell.held is None and b.cell.held is None
    assert n.surges == []
    assert a.firings == 0


def test_a_powered_cycle_surges_and_names_its_loop():
    """§4. Growth on revisit, a burn, and a positive fact — never an absence to be noticed."""
    g = EMPTY
    g, seed = named(g, "ping")
    n = Network()
    ax = n.axiom(g)
    a, b = ping_pong(n, g)
    n.wire(ax, a)
    n.revive()

    assert n.surges, "a powered cycle must surge"
    s = n.surges[0]
    assert set(s.loop) == {"A", "B"}, s.loop
    assert s.burned is not None


def test_a_long_acyclic_chain_neither_surges_nor_weakens():
    """§4, and the test that separates revisit-counting from hop-counting. A hop counter passes every
    other test in this file and fails this one."""
    depth = 30
    g = EMPTY
    g, _ = named(g, "step0")
    n = Network()
    prev = n.axiom(g)
    for i in range(depth):
        u = n.add(StandingUnit(f"u{i}", (atom("x", name=f"step{i}"),),
                               Emit(f"step{i + 1}", roles=(("of", "x"),))))
        n.wire(prev, u)
        prev = u.cell
    n.revive()

    assert n.surges == [], "a chain deeper than the surge threshold must not trip it"
    assert prev.held is not None
    assert holds(prev.held.graph, f"step{depth}")
    # The discrimination, made explicit: the chain is ten times deeper than the surge threshold, so a
    # hop counter would have burned it at step 3. Nothing was revisited, so revisit-counting sees zero.
    assert len(prev.held.path) == depth > SURGE_AT
    assert max(prev.held.path.count(u) for u in set(prev.held.path)) == 1


def test_fuel_bounds_the_revive_independently_of_surge():
    """Found by mutation testing: with surge detection removed the revive **does not terminate**, so
    surge is the only termination guarantee the design supplies. That is the fail-dangerous side of
    choosing growth over decay, and it makes `model.md` §8's inner budget load-bearing rather than
    belt-and-braces. Exhaustion is a fact, never a silent truncation."""
    g = EMPTY
    g, _ = named(g, "ping")
    n = Network()
    ax = n.axiom(g)
    a, b = ping_pong(n, g)
    n.wire(ax, a)

    n.revive(fuel=2)
    assert n.out_of_fuel is True

    n.revive()                      # default fuel: surge handles it long before the backstop
    assert n.out_of_fuel is False
    assert n.surges


# -- 4. partial wiring ----------------------------------------------------------------------------

def test_a_partially_wired_unit_is_stable():
    """§5, and the dissolution of `attachment.md`'s multi-premise anchoring crux. The unit holds, fires
    nothing, raises nothing, and reports what it is missing."""
    g, _, _ = socrates_world()
    n = Network()
    ax = n.axiom(g)
    u = n.add(StandingUnit("two-premise", MORTAL_RULE,
                           Emit("mortal", roles=(("of", "s"),)), gates=("a", "b")))
    n.wire(ax, u, "a")                      # gate "b" is deliberately left unwired
    n.revive()

    assert u.dangling() == ("b",)
    assert n.dangling() == [("two-premise", "b")]
    assert u.cell.held is not None          # it still derived what it could from gate "a"


def test_a_dangling_gate_is_a_standing_trigger():
    """The same structure read from the other end: a condition that has not occurred is a gate that has
    not been filled. Fill it and the watch fires — no monitor, no subscription, no polling.

    This is also how a **prohibition** is expressed without an absence test: *"do not do X"* waits for X
    to be **present**, which matters because §4 removed cheap exact negation."""
    n = Network()
    watch = n.add(StandingUnit("watch-for-breach", (atom("x", name="breach"),),
                               Emit("alarm", roles=(("of", "x"),)), gates=("trigger",)))
    n.revive()
    assert watch.dangling() == ("trigger",)     # genuinely unfed: the watch is standing
    assert watch.cell.held is None
    assert watch.firings == 0                   # and it costs nothing while it waits

    # The condition occurs. Wiring it in is the only act required.
    g = EMPTY
    g, _ = named(g, "breach")
    breach = n.axiom(g, name="breach-detected")
    n.wire(breach, watch, "trigger")
    n.revive()

    assert watch.dangling() == ()
    assert holds(watch.cell.held.graph, "alarm")


# -- 5. the tunnel, for free ----------------------------------------------------------------------

def test_the_base_world_cannot_see_into_a_hypothesis():
    """§5 of the revision, and the six surviving harness rows. No `visible_at`, no `ScopePointer`, no
    projection: the base unit is not wired to the hypothesis's cell, and that is the entire seal."""
    g, socrates, man = socrates_world()
    n = Network()
    ax = n.axiom(g)

    hg = EMPTY
    hg, god = named(hg, "god")
    hg, _ = occurrence(hg, "is-a", subject=socrates, kind=god)
    supposing = n.suppose(hg, name="supposing-socrates-is-a-god")

    inside = n.add(StandingUnit("gods-are-immortal",
                                (atom("occ", name="is-a", out=(
                                    role("subject", atom("s")),
                                    role("kind", atom(name="god")),
                                )),),
                                Emit("immortal", roles=(("of", "s"),)),
                                within=supposing))
    n.wire(supposing, inside)
    n.revive()

    assert holds(inside.cell.held.graph, "immortal")     # true inside the supposition
    assert not holds(n.world(), "immortal")              # and not in the base world
    assert holds(n.at(supposing), "immortal")            # visible from inside it


def test_two_sibling_hypotheses_do_not_contaminate_each_other():
    g, socrates, _ = socrates_world()
    n = Network()
    from units.standing import Value

    def hypothesis(label, kind_name, concl):
        hg = EMPTY
        hg, k = named(hg, kind_name)
        hg, _ = occurrence(hg, "is-a", subject=socrates, kind=k)
        cell = n.suppose(hg, name=label)
        u = n.add(StandingUnit(f"{kind_name}-rule",
                               (atom("occ", name="is-a", out=(
                                   role("subject", atom("s")),
                                   role("kind", atom(name=kind_name)),
                               )),),
                               Emit(concl, roles=(("of", "s"),)), within=cell))
        n.wire(cell, u)
        return cell, u

    h1, u1 = hypothesis("supposing-god", "god", "immortal")
    h2, u2 = hypothesis("supposing-stone", "stone", "insentient")
    n.revive()

    assert holds(n.at(h1), "immortal") and not holds(n.at(h1), "insentient")
    assert holds(n.at(h2), "insentient") and not holds(n.at(h2), "immortal")
    assert not holds(n.world(), "immortal") and not holds(n.world(), "insentient")


def test_crossing_is_one_wire_into_the_hypothesis_cell():
    """*"Suppose it rains — then I'd need the umbrella — so take the umbrella."* Nothing was permitted
    and no crossing predicate was consulted; someone attached, or they didn't."""
    g, socrates, _ = socrates_world()
    n = Network()
    from units.standing import Value

    hg = EMPTY
    hg, god = named(hg, "god")
    hg, _ = occurrence(hg, "is-a", subject=socrates, kind=god)
    supposing = n.suppose(hg, name="supposing-god")

    inside = n.add(StandingUnit("gods-are-immortal",
                                (atom("occ", name="is-a", out=(
                                    role("subject", atom("s")),
                                    role("kind", atom(name="god")),
                                )),),
                                Emit("immortal", roles=(("of", "s"),)),
                                within=supposing))
    n.wire(supposing, inside)

    # The crossing: a base-level unit wired to the tunnel's output cell.
    crossed = n.add(StandingUnit("if-immortal-then-noted",
                                 (atom("occ", name="immortal"),),
                                 Emit("conditionally-immortal", roles=()),
                                 within=None))
    n.wire(inside.cell, crossed)
    n.revive()

    assert holds(n.world(), "conditionally-immortal")
    assert not holds(n.world(), "immortal")         # the premise itself did not escape


# -- 6. create, never merge ------------------------------------------------------------------------

def test_two_derivations_of_the_same_content_are_distinct_and_independent():
    """§3. This is why no justification set, in-list or multiple-support bookkeeping is needed: killing
    one producer leaves the other standing, because they were never one fact."""
    g, socrates, man = socrates_world()
    g, greek = named(g, "greek")
    g, _ = occurrence(g, "is-a", subject=socrates, kind=greek)

    n = Network()
    ax = n.axiom(g)
    by_man = n.add(mortal_unit())
    by_greek = n.add(StandingUnit("all-greeks-are-mortal",
                                  (atom("occ", name="is-a", out=(
                                      role("subject", atom("s")),
                                      role("kind", atom(name="greek")),
                                  )),),
                                  Emit("mortal", roles=(("of", "s"),))))
    n.wire(ax, by_man)
    n.wire(ax, by_greek)
    n.revive()

    assert holds(by_man.cell.held.graph, "mortal")
    assert holds(by_greek.cell.held.graph, "mortal")

    # Kill one support by cutting its wire. The other is untouched — no bookkeeping consulted.
    n.wires = [w for w in n.wires if w[1] is not by_man]
    n.revive()
    assert by_man.cell.held is None
    assert holds(by_greek.cell.held.graph, "mortal")
    assert holds(n.world(), "mortal")


# -- 7. no rule pattern names a scope --------------------------------------------------------------

def test_no_rule_pattern_names_a_scope():
    """Invariant 1, checked structurally: the same unit definition is used inside and outside a
    hypothesis in these tests, and nothing in a pattern can refer to a cell."""
    from units.match import atoms
    for pattern in (MORTAL_RULE,):
        for a in atoms(pattern):
            keys = {k for k, _ in a.attrs}
            assert "scope" not in keys and "within" not in keys and "cell" not in keys
