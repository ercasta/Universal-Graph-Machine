"""`units/engine.py` — the consolidated machine.

Ports the claims from the three superseded spikes (`standing.py`, `overlay.py`-driven-directly, and
`turn.py`) onto one engine, and adds the ones only a consolidated machine can state: **scope is
support**, computed by walking the wiring, joining `revision-02` §3's two halves.
"""
import pytest

from units.engine import (SILENCED, SURGE_AT, SURGED, Attribute, Drop, Emit, Link, Merge,
                          Network, StandingUnit, bundled_silence_rule)
from units.graph import EMPTY, Node, named
from units.match import atom, atoms, role


def kb(**attrs):
    g, paul = named(EMPTY, "Paul", **attrs)
    return g, paul


# -- 1. the standing circuit -----------------------------------------------------------------------

def test_a_standing_unit_holds_its_conclusion():
    g, soc = named(EMPTY, "Socrates", kind="man")
    n = Network()
    n.wire(n.given(g), n.add(StandingUnit(
        "mortality", (atom("x", kind="man"),), Attribute("x", "mortal", True))))
    n.revive()
    assert n.world().attr(soc, "mortal") is True


def test_changing_an_axiom_makes_the_conclusion_absent_with_nothing_retracted():
    """Invariant 11, and the central claim of `revision-01`. No retraction runs; the conclusion is
    simply not produced next time."""
    g, soc = named(EMPTY, "Socrates", kind="man")
    n = Network()
    ax = n.given(g)
    n.wire(ax, n.add(StandingUnit("m", (atom("x", kind="man"),), Attribute("x", "mortal", True))))
    assert n.revive().world().attr(soc, "mortal") is True

    ax.held = None                                   # the premise is gone
    n.asserted = n.asserted.without(soc, "kind")
    assert n.revive().world().attr(soc, "mortal") is None


def test_graph_state_is_a_pure_function_of_axioms_and_wiring():
    """Invariant 15. Two revives of the same network agree; no hidden accumulation survives."""
    g, soc = named(EMPTY, "Socrates", kind="man")
    n = Network()
    n.wire(n.given(g), n.add(StandingUnit(
        "m", (atom("x", kind="man"),), Attribute("x", "mortal", True))))
    first = n.revive().world().attr(soc, "mortal")
    second = n.revive().world().attr(soc, "mortal")
    assert first == second is True


def test_a_partially_wired_unit_is_stable():
    """Invariant 14. An unconnected gate is not an error and not an unfinished assembly step: the unit
    holds, produces nothing, and that empty gate is what asks (§9) and holds attention (§7)."""
    g, _ = kb(age=42)
    n = Network()
    u = n.add(StandingUnit("two", (atom("x", name="Paul"),), Attribute("x", "seen", True),
                           gates=("in", "other")))
    n.wire(n.given(g), u, "in")
    n.revive()
    assert u.dangling() == ("other",)
    assert n.surges == [] and not n.out_of_fuel


# -- 2. energy at the gate -------------------------------------------------------------------------

def chain(n: Network, depth: int):
    g, _ = named(EMPTY, "step0")
    prev = n.given(g)
    for i in range(depth):
        u = n.add(StandingUnit(f"u{i}", (atom("x", name=f"step{i}"),),
                               Emit(f"step{i + 1}", roles=(("of", "x"),))))
        n.wire(prev, u)
        prev = u.cell
    return prev


def test_a_long_acyclic_chain_neither_surges_nor_weakens():
    """Invariant 13, and the discrimination that separates gate energy from hop counting: a chain ten
    times deeper than the threshold delivers **once per gate**, so no input ever changes."""
    n = Network()
    depth = 30
    chain(n, depth)
    n.revive()
    assert depth > SURGE_AT
    assert n.surges == []
    assert max(u.changes[g] for u in n.units for g in u.gates) == 0


def ping_pong(n: Network):
    a = n.add(StandingUnit("A", (atom("x", name="ping"),), Emit("pong", roles=(("of", "x"),))))
    b = n.add(StandingUnit("B", (atom("x", name="pong"),), Emit("ping", roles=(("of", "x"),))))
    n.wire(a.cell, b)
    n.wire(b.cell, a)
    return a, b


def test_an_unpowered_cycle_is_structurally_silent():
    """`revision-01` §3. A cycle unreachable from any axiom is never fired, so it needs no detection —
    which is why no well-founded support check is required."""
    n = Network()
    a, b = ping_pong(n)
    n.revive()
    assert a.firings == 0 and b.firings == 0 and n.surges == []


def test_a_powered_cycle_surges_and_names_its_loop_from_the_wiring():
    """The loop is read off the **topology**, not off the value — there is no AS-path any more."""
    g, _ = named(EMPTY, "ping")
    n = Network()
    a, b = ping_pong(n)
    n.wire(n.given(g), a)
    n.revive()
    assert n.surges, "a powered cycle must surge"
    assert set(n.surges[0].loop) == {"A", "B"}


def test_repeat_arrivals_of_the_same_value_are_not_energy():
    """`model.md` §5 — *a repeat arrival is a firing*. Four wires from one source fire the unit four
    times and that is legitimate; only a *change* is energy."""
    g, _ = named(EMPTY, "seed")
    n = Network()
    ax = n.given(g)
    u = n.add(StandingUnit("u", (atom("x", name="seed"),), Emit("out", roles=(("of", "x"),))))
    for _ in range(4):
        n.wire(ax, u)
    n.revive()
    assert n.surges == [] and u.firings == 4 and u.changes["in"] == 0


# -- 3. scope is SUPPORT — the join this consolidation exists for ------------------------------------

def eligibility(n: Network, cell, name: str):
    u = n.add(StandingUnit(name, (atom("x", standing="clean"),),
                           Attribute("x", "eligible", True)))
    n.wire(cell, u)
    return u


def test_scope_is_support_and_the_base_world_cannot_see_into_a_hypothesis():
    """`revision-02` §3, and the two halves finally meeting: `overlay.py` took a configuration as
    declared, `standing.py` computed one by walking wiring. Here `powering()` computes it and the read
    uses it.

    Note what is *not* here: no `Cell.within`, no `Cell.scope`, no containment, and no projection."""
    g, paul = named(EMPTY, "Paul")
    n = Network()
    n.given(g)
    h = n.supposing(named(EMPTY, "Paul")[0].with_node(paul, standing="clean"), name="H")
    u = eligibility(n, h, "elig")
    n.revive()

    assert n.powering(u) == frozenset({"H"})         # scope, read off the wiring
    assert n.world().attr(paul, "eligible") is None  # not a place — a filter
    assert n.graph(frozenset({"H"})).attr(paul, "eligible") is True


def test_two_sibling_hypotheses_do_not_contaminate_each_other():
    g, paul = named(EMPTY, "Paul")
    n = Network()
    n.given(g)
    h1 = n.supposing(EMPTY.with_node(paul, sex="man"), name="H1")
    h2 = n.supposing(EMPTY.with_node(paul, sex="woman"), name="H2")
    u1 = n.add(StandingUnit("r1", (atom("x", sex="man"),), Attribute("x", "verdict", "m")))
    u2 = n.add(StandingUnit("r2", (atom("x", sex="woman"),), Attribute("x", "verdict", "w")))
    n.wire(h1, u1)
    n.wire(h2, u2)
    n.revive()

    assert n.graph(frozenset({"H1"})).attr(paul, "verdict") == "m"
    assert n.graph(frozenset({"H2"})).attr(paul, "verdict") == "w"
    assert n.world().attr(paul, "verdict") is None
    # …and read together they are ALTERNATIVES, reported as a conflict rather than silently collapsed.
    assert len(n.graph().conflicts()) == 1


def test_crossing_is_one_wire_out_of_the_supposition():
    """`model.md` §6's only survivor of the tunnel: getting out is one explicit act. Nothing was
    permitted and no crossing predicate was consulted — someone attached, or they didn't."""
    g, paul = named(EMPTY, "Paul")
    n = Network()
    n.given(g)
    h = n.supposing(EMPTY.with_node(paul, standing="clean"), name="H")
    inner = eligibility(n, h, "inner")
    outer = n.add(StandingUnit("outer", (atom("x", eligible=True),),
                               Attribute("x", "noted", True)))
    n.wire(inner.cell, outer)
    n.revive()

    assert n.powering(outer) == frozenset({"H"})     # crossing does not escape the support
    assert n.graph(frozenset({"H"})).attr(paul, "noted") is True
    assert n.world().attr(paul, "noted") is None


def test_no_rule_pattern_names_a_scope():
    """Invariant 1, the strongest signal of regression — and now free: there is no scope object for a
    pattern to name."""
    g, paul = named(EMPTY, "Paul")
    n = Network()
    h = n.supposing(EMPTY.with_node(paul, standing="clean"), name="H")
    u = eligibility(n, h, "elig")
    for p in atoms(u.pattern):
        assert "H" not in dict(p.attrs).values()
        assert "scope" not in dict(p.attrs) and "world" not in dict(p.attrs)


# -- 4. conflict, merge, deletion --------------------------------------------------------------------

def test_two_live_derivations_disagreeing_is_a_conflict_not_a_collapse():
    g, paul = kb(age=42)
    n = Network()
    ax = n.given(g)
    n.wire(ax, n.add(StandingUnit("bday", (atom("x", name="Paul"),), Attribute("x", "age", 43))))
    n.revive()

    assert n.world().attr(paul, "age") is None       # conflicted reads as absent
    (c,) = n.world().conflicts()
    assert {r.value for r in c.readings} == {42, 43}


def test_merge_rewrites_every_mention_including_ones_the_unit_never_saw():
    g, a = named(EMPTY, "the car", colour="red")
    g, b = named(g, "my car", plate="AB123")
    g = g.with_edge(a, b)
    n = Network()
    n.wire(n.given(g), n.add(StandingUnit(
        "coref", (atom("p", name="the car"), atom("q", name="my car")), Merge("p", "q"))))
    n.revive()

    w = n.world()
    assert w.attr(a, "plate") == "AB123"             # reached through the identification
    assert w.attr(a, "colour") == "red"


def test_a_computation_units_deletion_hides_while_powered_and_never_reaches_the_store():
    g, paul = kb(age=42)
    n = Network()
    n.wire(n.given(g), n.add(StandingUnit("hide", (atom("x", name="Paul"),), Drop("x", "age"))))
    n.revive()

    assert n.world().attr(paul, "age") is None       # hidden
    assert n.asserted.attr(paul, "age") == 42        # …and nothing was removed


def test_deletion_cannot_undermine_its_own_support_in_a_propagating_engine():
    """⚠ **A finding of the consolidation, and it reverses a `turn.py` result.**

    `turn.py` recomputed every unit's premise from the current view each round, so a unit deleting its
    own premise unpowered itself and oscillated. Here it does not, and the reason is the distinction
    `revision-02` §1 draws: **power is plane 2, readability is plane 1.** A value that arrived on a wire
    cannot be un-delivered by an overlay that changes what is *readable*.

    So the self-undermining oscillation was a property of that evaluation strategy, not of deletion —
    and the propagating engine `model.md` §5 actually specifies does not have it."""
    g, paul = kb(age=42)
    n = Network()
    n.wire(n.given(g), n.add(StandingUnit("selfeater", (atom("x", age=42),), Drop("x", "age"))))
    n.revive()

    assert n.surges == []                            # no oscillation to detect
    assert not n.out_of_fuel
    assert n.world().attr(paul, "age") is None


# -- 5. the unit as data ------------------------------------------------------------------------------

def test_units_share_the_graph_and_ordinary_rules_do_not_see_them():
    """Invariant 19 and `revision-02` §5's *no machinery partition*. Unit nodes live in the same graph;
    an ordinary rule does not match them because nothing matches implicitly."""
    g, paul = kb(age=42)
    n = Network()
    u = n.add(StandingUnit("watcher", (atom("x", name="Paul"),), Attribute("x", "noted", True)))
    n.wire(n.given(g), u)
    n.revive()
    assert u.node in n.asserted.nodes
    assert n.world().attr(u.node, "noted") is None
    assert n.world().attr(paul, "noted") is True


def test_the_bundled_rule_silences_a_surged_unit():
    """The engine reports `surged` as a fact on the unit's own node; a rule matches it and concludes the
    correction. The engine never silences — which needs a unit to be plane-1 data."""
    g, _ = named(EMPTY, "ping")
    n = Network()
    a, b = ping_pong(n)
    n.wire(n.given(g), a)
    rule = bundled_silence_rule(n)
    n.wire(a.cell, rule)
    n.revive()

    assert n.surges
    surged = n._unit_named(n.surges[0].unit)
    assert n.graph().attr(surged.node, SURGED) is not None    # reported, on the unit's node


# -- 6. the two dispositions ---------------------------------------------------------------------

def test_a_mutating_rule_persists_and_a_computation_unit_does_not():
    """`revision-01` §2, the split the whole design rests on. A computation unit *holds* something true
    while its input holds; a mutating rule *acts* and is finished."""
    g, paul = kb(age=42)
    n = Network()
    ax = n.given(g)
    n.wire(ax, n.add(StandingUnit("thought", (atom("x", name="Paul"),),
                                  Attribute("x", "thought", True))))
    n.wire(ax, n.add(StandingUnit("act", (atom("x", name="Paul"),),
                                  Attribute("x", "acted", True), mutating=True)))
    n.revive()
    assert n.asserted.attr(paul, "acted") is True    # the act landed in the store…
    assert n.asserted.attr(paul, "thought") is None  # …the thought did not

    ax.held = None                                   # unpower everything
    n.revive()
    assert n.asserted.attr(paul, "acted") is True    # the act survives with no support
    assert n.world().attr(paul, "thought") is None


def test_search_state_survives_because_a_regular_rule_wrote_it():
    """The canonical case for the two dispositions: an enumerator's cursor held as a *derived* fact
    resets to the first hypothesis every revive, and the search becomes amnesiac."""
    g, cur = named(EMPTY, "cursor", at=0)
    n = Network()
    n.wire(n.given(g), n.add(StandingUnit("advance", (atom("c", at=0),),
                                          Attribute("c", "at", 1), mutating=True)))
    n.revive()
    assert n.asserted.attr(cur, "at") == 1           # advanced, and it stays advanced
    n.revive()
    assert n.asserted.attr(cur, "at") == 1


def test_a_surged_turn_writes_nothing_back():
    """No answer was reached, so none is applied — or an unstable configuration would edit the world a
    little on every attempt."""
    g, _ = named(EMPTY, "ping")
    g2, paul = kb()
    n = Network()
    a, b = ping_pong(n)
    n.wire(n.given(g), a)
    w = n.add(StandingUnit("writer", (atom("x", name="Paul"),),
                           Attribute("x", "written", True), mutating=True))
    n.wire(n.given(g2), w)
    n.revive()
    assert n.surges
    assert n.applied == ()
    assert n.asserted.attr(paul, "written") is None


# -- 7. order independence: the nearest thing to a semantics ----------------------------------------

def diamond(order, wire_order):
    """One axiom feeding two units, both feeding a two-gate join. The shape where latching could bite:
    the join's output depends on which gate arrived first, if anything is order-dependent."""
    g, paul = named(EMPTY, "Paul", a=1, b=2)
    n = Network()
    ax = n.given(g)
    left = StandingUnit("left", (atom("x", a=1),), Attribute("x", "L", True))
    right = StandingUnit("right", (atom("x", b=2),), Attribute("x", "R", True))
    join = StandingUnit("join", (atom("x", L=True), atom("y", R=True)),
                        Attribute("x", "both", True), gates=("p", "q"))
    for u in [[left, right, join][i] for i in order]:
        n.add(u)
    wires = [(ax, left, "in"), (ax, right, "in"),
             (left.cell, join, "p"), (right.cell, join, "q")]
    for i in wire_order:
        n.wire(*wires[i])
    n.revive()
    return n, paul


def test_the_result_does_not_depend_on_unit_or_wire_order():
    """**Invariant 15, meant literally** — and `review-01` §4's one structural gap: *"if invariant 15 is
    meant literally, it needs an argument that latching cannot make a stabilization result
    order-dependent, and the docs do not have one."*

    This is that argument in testable form. `model.md` §5 says gates latch and a unit fires on whatever
    arrives, using the latched values of the others — so a two-gate join fires *twice*, once per
    arrival, and the order decides which firing is partial. What must not vary is where it **settles**.

    It does not, and the reason is structural rather than lucky: a unit's output is a function of its
    gate contents, the gate contents are a function of the wiring, and effects **compose** by lazy
    overlay rather than by an order-sensitive application (`revision-02` §6 finding 4)."""
    from itertools import permutations

    from units.engine import readable
    results = set()
    for order in permutations(range(3)):
        for wire_order in permutations(range(4)):
            n, paul = diamond(order, wire_order)
            assert n.surges == [] and not n.out_of_fuel
            # …keyed by attribute, not by node identity: every construction mints a fresh Paul, so
            # comparing `nid` would report a difference that is not one.
            content = {k: v for (_nid, k), v in readable(n.world(), [paul]).items()}
            results.add(tuple(sorted(content.items())))

    assert len(results) == 1, f"{len(results)} distinct outcomes across 144 orderings"
    (only,) = results
    assert dict(only)["both"] is True                 # …and it is the *right* one, not uniformly empty
    assert dict(only)["L"] is True and dict(only)["R"] is True


def test_a_join_fires_once_per_arrival_which_is_why_the_test_above_is_not_trivial():
    """The control. If the join fired only once, order-independence would be uninteresting — the point
    is that latching makes it fire repeatedly with *different* partial inputs, and it still settles in
    the same place."""
    n, _ = diamond((0, 1, 2), (0, 1, 2, 3))
    join = n._unit_named("join")
    assert join.firings > 1
    assert join.dangling() == ()
