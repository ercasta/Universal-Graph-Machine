"""Overlays, contradiction, refutation, and enumeration —
`docs/units/revision-01-standing-circuits.md` §9.

The claim under test: a hypothesis **materialises** its consequences into the graph, several hypotheses'
consequences coexist without that being a contradiction, and a contradiction refutes *the configuration
that powered it* — which the wiring already records, so no rule ever names a scope.
"""
from __future__ import annotations

from units.graph import EMPTY, Graph, named, occurrence, role_edge
from units.match import atom, role
from units.standing import Emit, Link, Merge, Network, Overlay, StandingUnit, Value, holds


def attribution(target, attr, value) -> Graph:
    """The same shape a derived claim has. Asserted and derived facts must **wear one shape** or a rule
    would have to match both — which is the finding in `revision-01` §9."""
    g, a = named(EMPTY, f"{attr}={value}")
    g = g.with_node(a, name="attribution", attr=attr, value=value)
    return role_edge(g, a, "of", target)


def paul_world():
    g = EMPTY
    g, paul = named(g, "Paul", age=42)
    return g, paul


# -- 1. overlays materialise without mutating what they overlay -----------------------------------

def test_an_overlay_does_not_touch_the_node_it_overlays():
    """*"Paul is 43"* stands beside the asserted *"Paul is 42"*. The axiom is never edited, so a
    digital twin can be revised without destroying what it was (§1)."""
    g, paul = paul_world()
    n = Network()
    ax = n.axiom(g)
    birthday = n.add(StandingUnit("had-a-birthday", (atom("p", name="Paul"),),
                                  Overlay("p", "age", 43)))
    n.wire(ax, birthday)
    n.revive()

    assert ax.held.graph.attr(paul, "age") == 42            # untouched
    assert {v for v, _ in n.readings(paul, "age")} == {42, 43}


def test_an_overlay_fades_with_its_support():
    g, paul = paul_world()
    n = Network()
    ax = n.axiom(g)
    u = n.add(StandingUnit("had-a-birthday", (atom("p", name="Paul"),), Overlay("p", "age", 43)))
    n.wire(ax, u)
    n.revive()
    assert {v for v, _ in n.readings(paul, "age")} == {42, 43}

    n.wires = []                                            # support removed
    n.revive()
    assert {v for v, _ in n.readings(paul, "age")} == {42}


def test_a_derived_edge_is_powered_the_same_way():
    """Not only nodes and attributes: a standing unit can power an **edge** between two nodes that both
    live elsewhere."""
    g, paul = paul_world()
    g, mary = named(g, "Mary")
    n = Network()
    ax = n.axiom(g)
    u = n.add(StandingUnit("colleagues",
                           (atom("a", name="Paul"), atom("b", name="Mary")),
                           Link("a", "b", role="colleague-of")))
    n.wire(ax, u)
    n.revive()

    assert u.cell.held.graph.out(paul)                      # the edge exists here
    assert not ax.held.graph.out(paul)                      # and not in the axiom
    n.wires = []
    n.revive()
    assert u.cell.held is None                              # and it fades


# -- 2. sibling hypotheses coexist; that is not a contradiction ------------------------------------

def gendered(n: Network, paul, label: str, gender: str, facial: str):
    """*"Assuming Paul is a {gender}, Paul has {facial}."* One supposition, one standing unit."""
    hg = EMPTY
    hg = hg.with_node(paul, gender=gender)
    cell = n.suppose(hg, name=label)
    u = n.add(StandingUnit(f"{gender}-grooming", (atom("p", gender=gender),),
                           Overlay("p", "facial-hair", facial), within=cell))
    n.wire(cell, u)
    return cell, u


# Two derived attributions about **the same target** (`atom("t")` in both) that disagree. This is only
# expressible because a derived claim is a NODE: as an attribute write the two would have collapsed.
CONTRADICTION = (
    atom("a1", name="attribution", attr="facial-hair", value="moustache",
         out=(role("of", atom("t")),)),
    atom("a2", name="attribution", attr="facial-hair", value="none",
         out=(role("of", atom("t")),)),
)


def test_two_hypotheses_materialise_coexisting_overlays_and_that_is_not_a_contradiction():
    """Both readings are physically in the graph at once. A detector wired to **one** hypothesis sees
    only that hypothesis's overlay, so nothing is reported — which is right: they are alternatives, not
    a conflict."""
    g, paul = paul_world()
    n = Network()
    n.axiom(g)
    h1, u1 = gendered(n, paul, "assuming-man", "man", "moustache")
    h2, u2 = gendered(n, paul, "assuming-woman", "woman", "none")

    d1 = n.add(StandingUnit("detect", CONTRADICTION, Emit("contradiction"), within=h1))
    n.wire(u1.cell, d1)
    n.revive()

    assert {v for v, _ in n.readings(paul, "facial-hair")} == {"moustache", "none"}
    assert d1.cell.held is None, "alternatives under distinct suppositions are not a contradiction"

    # Positive control, so the assertion above cannot pass merely because the pattern never matches:
    # the SAME detector, given both, does report. Which is correct — feeding one unit from two
    # suppositions is asserting their conjunction, and their conjunction really is inconsistent.
    d1.gates = ("in", "other")
    d1.latched = {"in": None, "other": None}
    n.wire(u2.cell, d1, "other")
    n.revive()
    assert holds(d1.cell.held.graph, "contradiction")
    assert n.powering(d1) == {h1, h2}


# -- 3. reductio: a contradiction inside one hypothesis refutes it ---------------------------------

def test_a_contradiction_refutes_the_configuration_that_powered_it():
    """Reductio, and the shape that matters. The detector is wired to **one** hypothesis, not to two.
    What the contradiction condemns is the configuration feeding it, and that configuration is read off
    the wiring by walking backwards — no rule asked which world it was in."""
    g, paul = paul_world()
    n = Network()
    base = n.axiom(g)

    # Asserted, and not up for discussion: Paul is clean-shaven.
    base_shaven = n.axiom(attribution(paul, "facial-hair", "none"), name="paul-is-clean-shaven")

    h, u = gendered(n, paul, "assuming-man", "man", "moustache")

    detect = n.add(StandingUnit("detect", CONTRADICTION, Emit("contradiction"), within=h))
    n.wire(u.cell, detect, "in")
    detect.gates = ("in", "base")
    detect.latched["base"] = None
    n.wire(base_shaven, detect, "base")
    n.revive()

    assert holds(detect.cell.held.graph, "contradiction")

    # Blame: the suppositions in the powering configuration. Base axioms are not discardable.
    blamed = n.powering(detect)
    assert blamed == {h}, blamed


def test_a_refutation_must_cross_to_an_axiom_to_survive_the_next_revive():
    """A refutation concluded *inside* a hypothesis dies with it, which would make the search amnesiac.
    Search state is asserted data advanced by a mutating rule — the same reason the enumerator's cursor
    is an axiom (§2, the two dispositions)."""
    g, paul = paul_world()
    n = Network()
    n.axiom(g)
    h, u = gendered(n, paul, "assuming-man", "man", "moustache")
    n.revive()
    assert u.cell.held is not None

    # Unpower the hypothesis, as the enumerator will when it moves on.
    h.held = Value(EMPTY)
    n.revive()
    assert u.cell.held is None, "everything materialised under it is gone — including any refutation"

    # Which is why the refutation is written back as an axiom instead.
    rg, _ = named(EMPTY, "refuted")
    n.axiom(rg, name="refuted:assuming-man")
    n.revive()
    assert holds(n.world(), "refuted")


# -- 4. the enumerator: round robin across turns, proof by elimination ------------------------------

def test_round_robin_enumeration_across_turns_eliminates_hypotheses():
    """The payoff. Three suppositions, one powered per turn by a **cursor held as an axiom**, each
    tested by the same standing detector. Two are refuted; one survives.

    Nothing here is engine support: the enumerator is data plus units, which is what `model.md` §11
    demands (the front end targets data, never an API)."""
    g, paul = paul_world()
    n = Network()
    n.axiom(g)
    shaven = n.axiom(attribution(paul, "facial-hair", "none"), name="paul-is-clean-shaven")

    # Three alternatives. Only "woman" is compatible with the asserted clean shave.
    alts = {"man": "moustache", "bearded-man": "moustache", "woman": "none"}
    cells, dets = {}, {}
    for gender, facial in alts.items():
        cell, u = gendered(n, paul, f"assuming-{gender}", gender, facial)
        cell.held = Value(EMPTY)                    # start unpowered
        d = n.add(StandingUnit(f"detect-{gender}", CONTRADICTION, Emit("contradiction"), within=cell))
        d.gates = ("in", "base")
        d.latched = {"in": None, "base": None}
        n.wire(u.cell, d, "in")
        n.wire(shaven, d, "base")
        cells[gender], dets[gender] = cell, d

    refuted = set()
    for turn, gender in enumerate(alts):             # one hypothesis per turn — the round robin
        for other, c in cells.items():               # the cursor: a mutating write to asserted data
            c.held = Value(EMPTY.with_node(paul, gender=other) if other == gender else EMPTY)
        n.revive()
        if dets[gender].cell.held is not None and holds(dets[gender].cell.held.graph, "contradiction"):
            refuted.add(gender)

    assert refuted == {"man", "bearded-man"}
    survivors = set(alts) - refuted
    assert survivors == {"woman"}


def test_elimination_proves_nothing_unless_the_enumeration_is_exhaustive():
    """The honest caveat, pinned as a test so it cannot be forgotten. The engine cannot know the
    alternatives were exhaustive — that is a knowledge claim (§11, garbage in garbage out). So the
    survivor of an elimination is **un-refuted**, never **proven**, which is the same weak, honest
    claim as `starved` ≠ underivable (§8)."""
    g, paul = paul_world()
    n = Network()
    n.axiom(g)
    shaven = n.axiom(attribution(paul, "facial-hair", "none"), name="paul-is-clean-shaven")

    cell, u = gendered(n, paul, "assuming-man", "man", "moustache")
    d = n.add(StandingUnit("detect", CONTRADICTION, Emit("contradiction"), within=cell))
    d.gates = ("in", "base")
    d.latched = {"in": None, "base": None}
    n.wire(u.cell, d, "in")
    n.wire(shaven, d, "base")
    n.revive()

    assert holds(d.cell.held.graph, "contradiction")        # this one is refuted
    # …and nothing anywhere asserts that some other hypothesis is therefore true.
    assert not holds(n.world(), "proven")
    assert not holds(n.world(), "woman")


# -- 5. a contribution is a revertable MUTATION, not a fragment in a box --------------------------

def test_merge_proves_a_contribution_is_not_confined_to_its_producer():
    """Minting a node, adding an edge and setting an attribute can all be *described* as a local
    fragment. **Merging cannot** — identifying two nodes rewrites every mention of them, anywhere. So a
    unit's output is a revertable mutation of the whole graph, and treating it as a box was a modelling
    error.

    It is revertable for the same reason everything else is: mutations are re-applied from the asserted
    layer on each revive, so a merge whose unit loses power simply does not happen again. Nothing is
    ever *un*-merged."""
    g = EMPTY
    g, morning = named(g, "the-morning-star")
    g, evening = named(g, "the-evening-star")
    g, _ = occurrence(g, "orbits", subject=morning, around=named(g, "Sun")[1])

    n = Network()
    ax = n.axiom(g)
    coref = n.add(StandingUnit("same-planet",
                               (atom("a", name="the-morning-star"),
                                atom("b", name="the-evening-star")),
                               Merge("a", "b")))
    n.wire(ax, coref)

    assert len({morning, evening} & n.graph().nodes) == 2      # two nodes before
    n.revive()
    live = n.graph()
    assert (morning in live.nodes) != (evening in live.nodes), "the merge collapsed them graph-wide"
    survivor = morning if morning in live.nodes else evening
    subject = next(r for r in live.nodes if live.attr(r, "name") == "subject")
    assert survivor in live.out(subject), "and the orbit was rewritten onto the survivor"

    # Unpower the unit: the identification is simply not made again.
    n.wires = []
    n.revive()
    reverted = n.graph()
    assert morning in reverted.nodes and evening in reverted.nodes


def test_a_hypothesis_needs_no_checkpoint_because_every_effect_is_revertable():
    """Checkpointing was only ever needed because units were assumed to write to the asserted layer.
    They do not: **every** effect is an overlay. So a supposition's consequences — including a merge —
    revert by the ordinary revive, with no copy, no merge-back and no nesting problem."""
    g = EMPTY
    g, a = named(g, "Hesperus")
    g, b = named(g, "Phosphorus")
    n = Network()
    base = n.axiom(g)
    supposing = n.suppose(EMPTY, name="assuming-they-are-one")
    u = n.add(StandingUnit("identify",
                           (atom("x", name="Hesperus"), atom("y", name="Phosphorus")),
                           Merge("x", "y"), within=supposing))
    n.wire(base, u)
    n.revive()
    assert len({a, b} & n.graph().nodes) == 1              # merged under the supposition

    supposing.held = Value(EMPTY)
    n.wires = []
    n.revive()
    assert {a, b} <= n.graph().nodes                       # and the asserted layer is intact
    assert base.held.graph is g                            # never touched at all


# -- 6. the two dispositions: an overlay is a thought, a mutation is an act ------------------------

def test_a_mutating_rule_persists_across_revives_and_a_computation_unit_does_not():
    """The split the whole design rests on, and the reason multi-turn search works.

    A **computation unit** produces overlays: a function of its inputs, recomputed every revive, gone
    the moment the input goes. A **regular rule** fires and applies — its effect is merged into the
    asserted layer at write-back and survives every subsequent revive.

    Here the same trigger drives both. The tick accumulates; the thought does not."""
    g, paul = paul_world()
    n = Network()
    ax = n.axiom(g)

    thought = n.add(StandingUnit("notices-paul", (atom("p", name="Paul"),),
                                 Emit("noticed", roles=(("of", "p"),))))
    act = n.add(StandingUnit("tick", (atom("p", name="Paul"),), Emit("tick"), mutating=True))
    n.wire(ax, thought)
    n.wire(ax, act)

    for expected_ticks in (1, 2, 3):
        n.revive()
        ticks = [x for x in n.record.held.graph.nodes
                 if n.record.held.graph.attr(x, "name") == "tick"]
        assert len(ticks) == expected_ticks, "a mutating rule's effect accumulates"
        noticed = [x for x in n.graph().nodes if n.graph().attr(x, "name") == "noticed"]
        assert len(noticed) == 1, "a computation unit's overlay is recomputed, never accumulated"

    # Remove the support. The thought vanishes; the acts already performed remain.
    n.wires = []
    n.revive()
    assert not holds(n.graph(), "noticed")
    assert holds(n.graph(), "tick")


def test_search_state_survives_because_a_regular_rule_wrote_it():
    """Why the enumerator works. Its cursor is not a conclusion recomputed each turn — it is written by
    a rule that fires and applies, so it is still there on the next revive. Counting ticks is a cursor
    that needs no arithmetic."""
    g, paul = paul_world()
    n = Network()
    ax = n.axiom(g)
    n.wire(ax, n.add(StandingUnit("advance", (atom("p", name="Paul"),),
                                  Emit("tick"), mutating=True)))

    alternatives = ["man", "bearded-man", "woman"]
    visited = []
    for _ in alternatives:
        n.revive()
        cursor = sum(1 for x in n.record.held.graph.nodes
                     if n.record.held.graph.attr(x, "name") == "tick")
        visited.append(alternatives[(cursor - 1) % len(alternatives)])

    assert visited == alternatives, "round robin advanced across turns without resetting"
