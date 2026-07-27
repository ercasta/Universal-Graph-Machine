"""Overlays, contradiction, refutation, and enumeration —
`docs/units/revision-01-standing-circuits.md` §9.

The claim under test: a hypothesis **materialises** its consequences into the graph, several hypotheses'
consequences coexist without that being a contradiction, and a contradiction refutes *the configuration
that powered it* — which the wiring already records, so no rule ever names a scope.
"""
from __future__ import annotations

from units.graph import EMPTY, Graph, named, occurrence, role_edge
from units.match import atom, role
from units.standing import Link, Network, Overlay, StandingUnit, Value, holds
from units.unit import Emit


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
    n.axiom(attribution(paul, "facial-hair", "none"), name="paul-is-clean-shaven")

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
        n.wire(n.axioms[1], d, "base")
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
    n.axiom(attribution(paul, "facial-hair", "none"), name="paul-is-clean-shaven")

    cell, u = gendered(n, paul, "assuming-man", "man", "moustache")
    d = n.add(StandingUnit("detect", CONTRADICTION, Emit("contradiction"), within=cell))
    d.gates = ("in", "base")
    d.latched = {"in": None, "base": None}
    n.wire(u.cell, d, "in")
    n.wire(n.axioms[1], d, "base")
    n.revive()

    assert holds(d.cell.held.graph, "contradiction")        # this one is refuted
    # …and nothing anywhere asserts that some other hypothesis is therefore true.
    assert not holds(n.world(), "proven")
    assert not holds(n.world(), "woman")


# -- 5. checkpointing: scoping what is MUTATED, not only what is derived ---------------------------

def balance(target, amount):
    return attribution(target, "balance", amount)


def test_a_mutation_under_a_hypothesis_does_not_reach_the_base_layer():
    """The hole positioning does not cover. Materialized facts are recomputed every revive, so a
    hypothesis's *conclusions* are free — but a mutating rule writes to the asserted layer, permanently.
    A checkpoint is what makes the write local."""
    g, paul = paul_world()
    n = Network()
    base = n.axiom(balance(paul, 100), name="ledger")
    h = n.suppose(EMPTY, name="assuming-he-pays")
    made = n.checkpoint(h)
    assert made, "the base layer was copied into the hypothesis"
    (_, copy), = [(o, c) for o, c in made if o is base]

    # A mutating rule fires under the hypothesis, across two turns.
    for turn in (1, 2):
        copy.held = Value(balance(paul, 100 - 40 * turn))
        n.revive()

    assert {v for v, _ in n.readings(paul, "balance")} == {100, 20}
    assert base.held.graph is not None
    inside = [v for v, c in n.readings(paul, "balance") if c.inside(h)]
    outside = [v for v, c in n.readings(paul, "balance") if not c.inside(h)]
    assert inside == [20] and outside == [100]


def test_commit_merges_the_checkpoint_and_discard_does_not():
    """The two exits, and they are the only two — one explicit act each, same shape as §6's crossing."""
    g, paul = paul_world()

    for exit_, expected in (("commit", 20), ("discard", 100)):
        n = Network()
        base = n.axiom(balance(paul, 100), name="ledger")
        h = n.suppose(EMPTY, name="assuming-he-pays")
        (_, copy), = n.checkpoint(h)
        copy.held = Value(balance(paul, 20))
        n.revive()

        getattr(n, exit_)(h)
        n.revive()
        assert [v for v, _ in n.readings(paul, "balance")] == [expected], exit_
        assert not any(c.inside(h) and c is not h for c in n.cells()), "checkpoint reclaimed either way"


def test_search_state_must_live_outside_the_checkpoints_it_controls():
    """The enumerator's cursor and its refutations are precisely what must survive a branch being
    abandoned. Checkpointed, they would be rolled back by the discard that abandons the branch — and
    the search would loop on the hypothesis it just refuted, forever."""
    g, paul = paul_world()
    n = Network()
    n.axiom(balance(paul, 100), name="ledger")
    cursor = n.axiom(named(EMPTY, "refuted:assuming-he-pays")[0], name="search-state")

    h = n.suppose(EMPTY, name="assuming-he-pays")
    n.checkpoint(h)
    n.discard(h)
    n.revive()

    assert holds(n.world(), "refuted:assuming-he-pays")
    assert cursor in n.axioms


def test_a_checkpoint_shares_rather_than_copies():
    """Found by mutation testing: deep-copying the asserted layer makes **no semantic difference**,
    because `Graph` is immutable and a mutating rule replaces a cell's value rather than editing it.
    So a checkpoint is copy-on-write by construction and costs one `Cell` per asserted cell, not one
    graph per hypothesis — which is what makes multi-turn hypothesis exploration affordable at all."""
    g, paul = paul_world()
    n = Network()
    base = n.axiom(balance(paul, 100), name="ledger")
    h = n.suppose(EMPTY, name="assuming-he-pays")
    (_, copy), = n.checkpoint(h)

    assert copy.held.graph is base.held.graph, "no copy was made"

    copy.held = Value(balance(paul, 20))            # a mutating write diverges only this cell
    n.revive()
    assert base.held.graph is not copy.held.graph
    assert [v for v, c in n.readings(paul, "balance") if not c.inside(h)] == [100]
