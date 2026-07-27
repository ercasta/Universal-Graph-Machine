"""`units/engine.py` — the consolidated machine.

Ports the claims from the three superseded spikes (`standing.py`, `overlay.py`-driven-directly, and
`turn.py`) onto one engine, and adds the ones only a consolidated machine can state: **scope is
support**, computed by walking the wiring, joining `revision-02` §3's two halves.
"""
import pytest

from units.engine import (FROM, GATE, OUT, SILENCED, SURGE_AT, SURGED, TO, WIRE, Attribute, Drop,
                          Emit, Link, Merge, Network, StandingUnit, bundled_silence_rule,
                          effects_of)
from units.graph import EMPTY, Node, named, role_edge
from units.match import AttrVar, atom, atoms, role


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
    correction. The engine never silences — which needs a unit to be plane-1 data.

    ⚠ **This test used to stop at the first assertion, and the two lines below it were both false.**
    The rule's pattern was `surged=None`, which `attr` answers for every node that *lacks* the
    attribute, so it matched everything except its target; and `surged` was written only into the read
    layer, where no unit can see it (invariant 3). Checking the engine's half of a two-half mechanism
    is what let both survive."""
    g, _ = named(EMPTY, "ping")
    n = Network()
    a, b = ping_pong(n)
    n.wire(n.given(g), a)
    rule = bundled_silence_rule(n)
    n.revive()

    assert n.surges
    surged = n._unit_named(n.surges[0].unit)
    assert n.graph().attr(surged.node, SURGED) is not None    # reported, on the unit's node
    assert rule.firings, "the rule never saw the report"
    assert n.graph().attr(surged.node, SILENCED) is True      # …and a RULE concluded the correction


def test_without_the_bundled_rule_nothing_is_silenced():
    """The negative control. The engine reports and does nothing else — if it silenced on its own the
    rule would be decoration (`rev-02` §6)."""
    g, _ = named(EMPTY, "ping")
    n = Network()
    a, b = ping_pong(n)
    n.wire(n.given(g), a)
    n.revive()

    assert n.surges
    assert all(n.graph().attr(u.node, SILENCED) is None for u in n.units)


def test_the_corrector_does_not_burn_itself_when_several_loops_surge():
    """⚠ **A defect the working rule exposed immediately.** The report accumulates on one cell, so every
    surge after the first is a *change* on the corrector's single gate — and at `SURGE_AT` the detector
    burned the corrector itself, leaving the last loop uncorrected.

    That is counting **growth** as cycling. `rev-02` §6's own theorem says growth is not evidence of a
    cycle, and applying it to the value on the wire is the fix: a strictly larger input is not energy.
    The price is that monotone-but-infinite is squarely fuel's job, which `rev-02` §9 already says."""
    g, _ = named(EMPTY, "ping")
    n = Network()
    ax = n.given(g)
    loops = []
    for i in range(SURGE_AT + 1):                             # one more loop than the threshold
        a = n.add(StandingUnit(f"A{i}", (atom("x", name="ping"),), Emit("pong", roles=(("of", "x"),))))
        b = n.add(StandingUnit(f"B{i}", (atom("x", name="pong"),), Emit("ping", roles=(("of", "x"),))))
        n.wire(a.cell, b)
        n.wire(b.cell, a)
        n.wire(ax, a)
        loops.append(a)
    rule = bundled_silence_rule(n)
    n.revive()

    assert rule.name not in {s.unit for s in n.surges}, "the corrector burned itself"
    assert all(n.graph().attr(a.node, SILENCED) is True for a in loops)


def test_a_rule_not_wired_to_the_report_cannot_see_it():
    """Why the report had to become a **cell**. A unit sees only its gates, so a fact the engine merely
    writes into the read layer is unreachable however good the pattern is."""
    g, _ = named(EMPTY, "ping")
    n = Network()
    a, b = ping_pong(n)
    ax = n.given(g)
    n.wire(ax, a)
    watcher = n.add(StandingUnit("watcher", (atom("s", **{SURGED: AttrVar("g")}),),
                                 Attribute("s", SILENCED, True)))
    n.wire(ax, watcher)                                       # wired to the WRONG thing
    n.revive()

    assert n.surges
    assert watcher.firings and n.graph().attr(a.node, SILENCED) is None


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


# -- 8. the wiring register — tier 0 ----------------------------------------------------------------
#
# `forms_cnl.md` §9 step 1. Topology was a Python list of tuples, which made invariant 18 false and made
# the front end's target an **engine API** rather than data (`model.md` §11). These are the tests that
# say it is data now: written by hand, concluded by a rule, and removable by removing the fact.

def wire_nodes(n: Network) -> list:
    return [w for w in n.asserted.nodes if n.asserted.attr(w, "name") == WIRE]


def test_a_circuit_can_be_wired_by_writing_graph_data_alone():
    """**The contract `model.md` §11 asks for, cashed.** Not one call to `wire()`: a `<wire>` occurrence
    with three role nodes, written the way any other fact is written, and the circuit runs."""
    g, soc = named(EMPTY, "Socrates", kind="man")
    n = Network()
    ax = n.given(g)
    u = n.add(StandingUnit("m", (atom("x", kind="man"),), Attribute("x", "mortal", True)))

    w, gate = Node(WIRE), Node("in")
    a = n.asserted.with_node(w, name=WIRE).with_node(gate, name="in")
    a = role_edge(a, w, FROM, ax.node)
    a = role_edge(a, w, TO, u.node)
    n.asserted = role_edge(a, w, GATE, gate)

    n.revive()
    assert n.world().attr(soc, "mortal") is True


def test_removing_the_fact_unwires_the_circuit():
    """Derived, not owned. If topology were still a field, deleting the description would change
    nothing — which is exactly the failure this step exists to remove."""
    g, soc = named(EMPTY, "Socrates", kind="man")
    n = Network()
    n.wire(n.given(g), n.add(StandingUnit(
        "m", (atom("x", kind="man"),), Attribute("x", "mortal", True))))
    assert n.revive().world().attr(soc, "mortal") is True

    (w,) = wire_nodes(n)
    n.asserted = n.asserted.without(w)
    assert n.wires == ()
    assert n.revive().world().attr(soc, "mortal") is None


def test_a_mutating_rule_can_conclude_a_wire():
    """**Invariant 4 cashed** — *"if routing is ever learned, units propose wirings as facts."* The rule
    is ordinary and its effect is an ordinary `Emit`; what makes it a wiring is only that it names the
    tier-0 vocabulary. Nothing in the engine knows this rule is special, and the wire it concludes is
    applied at write-back like any other act."""
    g, soc = named(EMPTY, "Socrates", kind="man")
    g, feed = named(g, "feed")                      # the gate to wire to, as a node in the world
    n = Network()
    src = n.given(g, name="src")
    target = n.add(StandingUnit("m", (atom("x", kind="man"),), Attribute("x", "mortal", True),
                                gates=("feed",)))
    assert n.revive().world().attr(soc, "mortal") is None       # unwired: nothing happens

    planner = n.add(StandingUnit(
        "planner", (atom("c", name="src"), atom("t", name="m"), atom("g", name="feed")),
        Emit(WIRE, roles=((FROM, "c"), (TO, "t"), (GATE, "g"))), mutating=True))
    # The planner has to *see* the machinery to talk about it, and it does so the ordinary way: an axiom
    # delivering the graph it lives in. Homoiconicity costing nothing until someone looks (`rev-02` §5).
    n.wire(n.axiom(*effects_of(n.asserted), name="reflect"), planner)

    n.revive()
    assert (src, target, "feed") in n.wires                     # the wire exists because a rule said so
    assert n.revive().world().attr(soc, "mortal") is True


def test_a_wire_naming_something_that_was_never_built_is_skipped():
    """A description is not an assembly. The assembler wires what it can resolve and passes over what it
    cannot — the same stance as a dangling gate (invariant 14), not an error."""
    g, _ = named(EMPTY, "Socrates", kind="man")
    n = Network()
    ax = n.given(g)
    ghost = Node("nobody")
    w, gate = Node(WIRE), Node("in")
    a = n.asserted.with_node(w, name=WIRE).with_node(gate, name="in").with_node(ghost, name="nobody")
    a = role_edge(a, w, FROM, ax.node)
    a = role_edge(a, w, TO, ghost)
    n.asserted = role_edge(a, w, GATE, gate)

    assert n.wires == ()
    n.revive()
    assert n.surges == [] and not n.out_of_fuel


def test_a_units_output_cell_is_reachable_from_its_node():
    """`out:`, tier 0. A wire may be written naming only the unit, so the cell it feeds from has to be
    findable in the graph rather than through a Python attribute."""
    n = Network()
    u = n.add(StandingUnit("u", (atom("x"),), Attribute("x", "seen", True)))
    (cell_node,) = [d for r in n.asserted.out(u.node)
                    if n.asserted.attr(r, "name") == OUT for d in n.asserted.out(r)]
    assert cell_node is u.cell.node


def leaky(reflective: bool):
    """A rule with a **generic structural** pattern — *anything with an outgoing edge* — which is the
    shape that leaked the last time the metalanguage went into the graph (`?y is meta when ?y is a
    relation` deriving `produces is meta`). Wired either to world data or to a reflective axiom."""
    g, _ = named(EMPTY, "Paul", age=42)
    n = Network()
    ax = n.given(g)
    n.wire(ax, n.add(StandingUnit("u", (atom("x", name="Paul"),), Attribute("x", "seen", True))))
    leak = n.add(StandingUnit("leak", (atom("r", out=(atom("t"),)),), Attribute("r", "meta", True)))
    n.wire(n.axiom(*effects_of(n.asserted), name="reflect") if reflective else ax, leak)
    n.revive()
    return n, [w for w in n.asserted.nodes if n.asserted.attr(w, "name") == WIRE]


def test_machinery_is_unreachable_unless_something_wires_it():
    """`T9`, the half that holds — and it is the half that matters. The wiring register put the
    metalanguage in the graph, which is what leaked last time; here a rule that would happily mark a
    wire never gets the chance, because nothing delivered one to its gate."""
    n, wires = leaky(reflective=False)
    assert wires
    assert all(n.graph().attr(w, "meta") is None for w in wires)


def test_invariant_19_is_false_as_written_and_the_barrier_is_the_wiring():
    """⚠ **`T9` against the known leak, and it leaks.** Invariant 19 says *a pattern that does not name
    machinery never matches machinery*. It does not hold: a wire occurrence has an outgoing edge like
    everything else, so a **generic structural** pattern matches it without naming anything. What is
    true is the weaker and more useful statement above — machinery has to be **delivered** before any
    pattern can see it, and delivering it is a deliberate act.

    So the protection is `model.md` §5 (a unit sees only its gates), not invariant 7. Recorded rather
    than patched: a partition is what `rev-02` §5 rejected, and the mechanism `rev-02` §9 nominates for
    this is attention."""
    n, wires = leaky(reflective=True)
    assert any(n.graph().attr(w, "meta") is True for w in wires), \
        "if this stops leaking, invariant 19 can be restated — check why before celebrating"


def test_the_engine_holds_no_topology_of_its_own():
    """Invariant 18, read off the source, because this is the kind of thing that grows back: there is no
    assignment to a wire list anywhere, and `wires` is derived."""
    import inspect

    import units.engine as engine
    src = inspect.getsource(engine)
    assert "self.wires.append" not in src and "self.wires =" not in src
    assert isinstance(engine.Network.wires, property)


def test_a_second_network_assembles_the_same_circuit_from_the_graph_alone():
    """**The point of the whole step.** A fresh `Network` handed only the asserted graph — never told
    how anything is wired — assembles the identical circuit and reaches the identical conclusion. The
    circuit persisted because its *description* did (`rev-02` §5).

    ⚠ It still has to be handed the unit **objects**, because a unit's pattern and effects are Python.
    That is `pattern:`, tier 0's remaining role, and it is the next thing this register has to swallow."""
    g, soc = named(EMPTY, "Socrates", kind="man")
    n = Network()
    ax = n.given(g)
    u = n.add(StandingUnit("m", (atom("x", kind="man"),), Attribute("x", "mortal", True)))
    n.wire(ax, u)
    assert n.revive().world().attr(soc, "mortal") is True

    again = Network(n.asserted)
    again.axioms.append(ax)
    again._built[ax.node] = ax
    again.add(u)
    assert [(s.name, d.name, gate) for s, d, gate in again.wires] == [("given", "m", "in")]
    assert again.revive().world().attr(soc, "mortal") is True


def test_a_join_fires_once_per_arrival_which_is_why_the_test_above_is_not_trivial():
    """The control. If the join fired only once, order-independence would be uninteresting — the point
    is that latching makes it fire repeatedly with *different* partial inputs, and it still settles in
    the same place."""
    n, _ = diamond((0, 1, 2), (0, 1, 2, 3))
    join = n._unit_named("join")
    assert join.firings > 1
    assert join.dangling() == ()


# -- 9. suppositions and acts ------------------------------------------------------------------------

def test_a_mutating_rule_inside_a_supposition_does_not_act_on_the_world():
    """⚠ **A leak, found 2026-07-27 while probing discharge.** `rev-02` §6 claims scoping comes free —
    *"a deletion inside a supposition does not reach the base world, with no extra machinery."* That
    holds for **overlays**, which are read under a configuration. Write-back has no configuration at
    all, so it applied regardless: *"suppose it rains"* wired to a mutating rule really took the
    umbrella.

    Support is the filter on write-back exactly as it is on the read path."""
    g, lion = named(EMPTY, "lion")
    n = Network()
    n.given(g)
    h = n.supposing(EMPTY.with_node(lion, provoked=True), name="H")
    act = n.add(StandingUnit("act", (atom("x", provoked=True),),
                             Attribute("x", "umbrella_taken", True), mutating=True))
    n.wire(h, act)
    n.revive()

    assert n.powering(act) == frozenset({"H"})
    assert n.asserted.attr(lion, "umbrella_taken") is None      # the act did NOT happen
    assert n.world().attr(lion, "umbrella_taken") is None


def test_an_act_outside_every_supposition_still_lands():
    """The control. The filter is support, not mutation — an unhypothesised act is unaffected."""
    g, lion = named(EMPTY, "lion", provoked=True)
    n = Network()
    n.wire(n.given(g), n.add(StandingUnit("act", (atom("x", provoked=True),),
                                          Attribute("x", "umbrella_taken", True), mutating=True)))
    n.revive()
    assert n.asserted.attr(lion, "umbrella_taken") is True


def test_nothing_downstream_of_a_supposition_can_conclude_in_the_base_world():
    """⭐ **Discharge is structurally impossible, and this is the measurement behind that claim.**

    Natural deduction introduces `→` by *assume P, derive Q, **discharge** to P → Q* — and discharge is
    exactly the step that must leave the hypothesis behind. `powering()` walks backwards over the
    wiring, so support propagates forward through **every** wire: anything reachable from a supposition
    is inside it, by construction. There is no wiring that gets a conclusion out.

    So `forms_discourse` §4.4's *"SUPPOSE is the introduction rule for the conditional"* is not
    buildable on this engine as it stands — the first two steps work and the third has no mechanism."""
    g, lion = named(EMPTY, "lion")
    n = Network()
    n.given(g)
    h = n.supposing(EMPTY.with_node(lion, provoked=True), name="H")
    inner = n.add(StandingUnit("inner", (atom("x", provoked=True),),
                               Attribute("x", "dangerous", True)))
    n.wire(h, inner)
    discharge = n.add(StandingUnit("discharge", (atom("x", dangerous=True),),
                                   Attribute("x", "conditional_holds", True)))
    n.wire(inner.cell, discharge)
    n.revive()

    assert n.powering(discharge) == frozenset({"H"})             # inherited, unavoidably
    assert n.world().attr(lion, "conditional_holds") is None     # …so it cannot reach the base world
    assert n.graph(frozenset({"H"})).attr(lion, "conditional_holds") is True
