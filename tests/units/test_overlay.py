"""`docs/units/revision-02-two-planes.md` §6 — output is an overlay, applied to the graph, read lazily.

Every test here was **mutation-checked**: the mechanism it claims to test was broken on purpose and the
test confirmed to fail. The kills are recorded in `revision-02` §6.
"""
from units.graph import EMPTY, Graph, Node, named
from units.overlay import (BASE, AddEdge, Identify, Mint, Overlays, Retract, SetAttr)


def test_all_four_effects_are_the_same_kind_of_thing():
    """The correction. `standing.py` carries `graph: Graph` **and** `merges: tuple`, because `Merge`
    could not be expressed as a fragment and got a side channel. Here one list holds all four."""
    g, paul = named(EMPTY, "Paul")
    g, mary = named(g, "Mary")
    extra = Node("extra")

    o = Overlays(g, [("u", Mint(extra, (("name", "Sue"),))),
                     ("u", AddEdge(paul, mary)),
                     ("u", SetAttr(paul, "age", 43)),
                     ("u", Identify(paul, mary))])

    assert len({type(e) for _, e in o.effects}) == 4
    assert not hasattr(o, "merges")          # no side channel for the one that does not fit
    assert o.resolve(mary) is paul
    assert extra in o.nodes()


H1, H2 = frozenset({"h1"}), frozenset({"h2"})


def test_alternatives_under_different_suppositions_never_meet_in_one_read():
    """§3 — scope is **support**. This is what makes the set unnecessary: two overlays resting on
    different suppositions are never both live, so *"a man under H1, a woman under H2"* is not a
    conflict and never presents as one. Reading the base world sees neither."""
    g, paul = named(EMPTY, "Paul")
    o = Overlays(g, [("u1", SetAttr(paul, "sex", "man")),
                     ("u2", SetAttr(paul, "sex", "woman"))],
                 support={"u1": H1, "u2": H2})

    assert o.read(paul, "sex", under=H1).value == "man"
    assert o.read(paul, "sex", under=H2).value == "woman"
    assert o.read(paul, "sex") is None                   # base world: neither is powered
    assert o.conflicts(under=H1) == [] and o.conflicts(under=H2) == []
    assert o.conflicts() == []


def test_two_values_in_one_configuration_is_a_conflict_not_a_set():
    """Invariant 16, rewritten. The engine does not pick and does not hand back a set: the value is
    **absent** and the disagreement is a **positive fact** for a rule to match (§8)."""
    g, paul = named(EMPTY, "Paul")
    o = Overlays(g, [("u1", SetAttr(paul, "sex", "man")),
                     ("u2", SetAttr(paul, "sex", "woman"))])

    assert o.read(paul, "sex") is None                   # not a winner, and not a set
    (c,) = o.conflicts()
    assert c.attr == "sex" and {r.value for r in c.readings} == {"man", "woman"}
    assert {r.source for r in c.readings} == {"u1", "u2"}    # names who disagreed


def test_a_rule_resolves_a_conflict_by_retracting_and_the_next_revive_reads_cleanly():
    """The loop the design actually needs: conflict → a rule concludes a `Retract` → clean read. The
    engine contributed the report and nothing else; which side goes is authored (§9)."""
    g, paul = named(EMPTY, "Paul", age=42)
    effects = [("birthday", SetAttr(paul, "age", 43))]
    o = Overlays(g, effects)
    assert o.read(paul, "age") is None and len(o.conflicts()) == 1

    o.effects.append(("stale-fact-rule", Retract(paul, "age", source=BASE)))  # that claim, not the slot
    o.reindex()
    assert o.read(paul, "age").value == 43
    assert o.conflicts() == []


def test_an_overlay_does_not_overwrite_what_it_overlays():
    """The reified-attribution constraint: applying is never writing. The base graph is untouched, so
    the disagreement is *visible* rather than silently resolved — which is what `Graph.union` could not
    do and what the conflict report depends on."""
    g, paul = named(EMPTY, "Paul", age=42)
    o = Overlays(g, [("birthday", SetAttr(paul, "age", 43))])

    (c,) = o.conflicts()
    assert {(r.value, r.source) for r in c.readings} == {(42, BASE), (43, "birthday")}
    assert g.attr(paul, "age") == 42                     # the base graph never changed


def test_an_attribute_overlay_is_not_an_attribute_write():
    """The `revision-01` spike finding this module preserves. `Graph.union` merges attrs by node, so two
    live derivations disagreeing about one `(node, attr)` collapse to whichever was unioned last, and
    the contradiction vanishes exactly when it matters. Shown here as the failure it would be."""
    g, paul = named(EMPTY, "Paul")
    collapsed = (g.with_node(paul, sex="man")).union(g.with_node(paul, sex="woman"))
    assert collapsed.attr(paul, "sex") == "woman"        # one reading survived. This is the bug.

    o = Overlays(g, [("h1", SetAttr(paul, "sex", "man")),
                     ("h2", SetAttr(paul, "sex", "woman"))])
    assert len(o.conflicts()) == 1                       # here it is detected instead


def test_an_overlay_is_gone_when_its_support_goes():
    """Revertability with no machinery: drop the effect and re-index. Nothing is retracted, and the base
    graph was never touched, so there is nothing to restore."""
    g, paul = named(EMPTY, "Paul", age=42)
    live = [("birthday", SetAttr(paul, "age", 43))]
    o = Overlays(g, live)
    assert o.read(paul, "age") is None                   # conflicted while powered

    o.effects = []                                       # the unit lost power
    o.reindex()
    assert o.read(paul, "age").value == 42


def test_a_computation_units_retraction_hides_while_powered_and_reverts():
    """A deletion is an overlay like any other: no data is lost, and it comes back on the revive that
    stops powering it. A *mutating* rule's deletion is the other disposition and is real at write-back
    (`revision-01` §2)."""
    g, paul = named(EMPTY, "Paul", age=42)
    effects = [("u", Retract(paul, "age"))]
    o = Overlays(g, effects)
    assert o.read(paul, "age") is None
    assert paul in o.nodes()                             # the node is still there; the slot is not

    o.effects = []
    o.reindex()
    assert o.read(paul, "age").value == 42               # no data was lost


def test_retracting_a_node_removes_it_from_the_overlaid_graph():
    """What System 1 recalls against next turn is the **overlaid** graph — derived structure present,
    retracted structure gone (`model.md` §7). An independent reason a read yields one value."""
    g, paul = named(EMPTY, "Paul")
    g, mary = named(g, "Mary")
    g = g.with_edge(paul, mary)
    o = Overlays(g, [("u", Retract(mary))])

    assert mary not in o.nodes()
    assert o.out(paul) == ()                             # and no dangling mention of it survives


def test_a_retraction_is_scoped_by_its_support_like_any_other_overlay():
    """Retraction under a supposition does not reach the base world — the seal, holding for a deletion,
    with no extra machinery because it is the same mechanism."""
    g, paul = named(EMPTY, "Paul", age=42)
    o = Overlays(g, [("u", Retract(paul, "age"))], support={"u": H1})

    assert o.read(paul, "age", under=H1) is None
    assert o.read(paul, "age").value == 42               # base world untouched


def test_identify_rewrites_every_mention_including_ones_it_never_saw():
    """`Identify` is what proves an overlay is a mutation of the one graph rather than a fragment. The
    edge from `car` was asserted before anyone decided the two nodes were the same, and it moves."""
    g, a = named(EMPTY, "the red car")
    g, b = named(g, "my car")
    g, garage = named(g, "garage")
    g = g.with_edge(garage, a)
    g, owner = named(g, "owner")
    g = g.with_edge(b, owner)

    o = Overlays(g, [("coref", Identify(a, b))])

    assert o.resolve(b) is a
    assert o.out(garage) == (a,)                         # mention it never touched, resolved
    assert o.out(a) == (owner,)                          # b's edge is now a's


def test_a_read_gathers_across_an_identification():
    """After an identification a read has to gather over the whole equivalence class — base attributes
    of the dropped node included, or half the thing quietly disappears."""
    g, a = named(EMPTY, "car", colour="red")
    g, b = named(g, "car", plate="AB123")
    o = Overlays(g, [("coref", Identify(a, b)), ("u", SetAttr(b, "floor", 3))])

    assert o.read(a, "plate").value == "AB123"           # reached through the merge
    assert o.read(a, "colour").value == "red"
    assert o.read(a, "floor").value == 3                 # overlay keyed on the dropped node


def test_identifications_chain():
    g, a = named(EMPTY, "a")
    g, b = named(g, "b")
    g, c = named(g, "c")
    o = Overlays(g, [("u", Identify(a, b)), ("u", Identify(b, c))])
    assert o.resolve(c) is a and o.resolve(b) is a


def test_eager_application_is_order_dependent_and_lazy_is_not():
    """A second argument for laziness, and this one is about correctness rather than cost.

    Applying eagerly, an `Identify` only rewrites the mentions that exist **when it is applied**. Any
    later effect naming the dropped node re-introduces it, and the graph ends up holding a node the
    system has already decided does not exist separately. Resolving at *read* time cannot have this bug,
    because there is no moment at which the rewrite happens.

    This matters here more than in an ordinary store: effect order within a revive is a scheduling
    artifact, and `model.md` §12 invariant 8 says a turn need not be reproducible. An order-sensitive
    application would make the *graph* depend on the scheduler."""
    g, paul = named(EMPTY, "Paul", age=42)
    g, other = named(g, "P.")
    effects = [("coref", Identify(paul, other)), ("u", AddEdge(paul, other))]
    o = Overlays(g, effects)

    eager = o.materialize()
    assert other in eager.nodes                          # stale: re-introduced after the merge
    assert eager.out(paul) == (other,)

    assert other not in o.nodes()                        # lazy: nothing to re-introduce
    assert o.out(paul) == (paul,)                        # the edge is a self-edge, as it must be

    flipped = Overlays(g, list(reversed(effects)))       # and the other order gives a third answer
    assert other not in flipped.materialize().nodes
    assert o.out(paul) == flipped.out(paul)              # …while lazy is invariant under the order


def test_the_index_holds_nothing_the_effects_do_not_describe():
    """Invariant 18 — everything persistent is plane 1. Rebuilding the index from the same effects gives
    the same reads, and rebuilding from none gives the base graph back."""
    g, paul = named(EMPTY, "Paul", age=42)
    effects = [("u", SetAttr(paul, "age", 43))]
    a = Overlays(g, effects)
    b = Overlays(g, list(effects))
    assert [(r.value, r.source) for c in a.conflicts() for r in c.readings] == \
           [(r.value, r.source) for c in b.conflicts() for r in c.readings]
    assert Overlays(g).read(paul, "age").value == 42
