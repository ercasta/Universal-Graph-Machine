"""`docs/units/revision-02-two-planes.md` §6 — output is an overlay, applied to the graph, read lazily.

Every test here was **mutation-checked**: the mechanism it claims to test was broken on purpose and the
test confirmed to fail. The kills are recorded in `revision-02` §6.
"""
from units.graph import EMPTY, Graph, Node, named
from units.overlay import (BASE, AddEdge, Identify, Mint, Overlays, SetAttr)


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


def test_a_read_returns_a_set_never_a_winner():
    """Invariant 16. Two live overlays disagreeing about one attribute are two **readings**, and
    collapsing them is CSS's cascade — a precedence policy hardcoded in the engine."""
    g, paul = named(EMPTY, "Paul", age=42)
    o = Overlays(g, [("h1", SetAttr(paul, "sex", "man")),
                     ("h2", SetAttr(paul, "sex", "woman"))])

    sexes = o.read(paul, "sex")
    assert len(sexes) == 2
    assert {r.value for r in sexes} == {"man", "woman"}
    assert {r.source for r in sexes} == {"h1", "h2"}     # provenance is the overlay set


def test_an_overlay_does_not_overwrite_what_it_overlays():
    """A derived value stands *beside* the asserted one, and the asserted one is still readable. This is
    the reified-attribution constraint: applying is never writing."""
    g, paul = named(EMPTY, "Paul", age=42)
    o = Overlays(g, [("birthday", SetAttr(paul, "age", 43))])

    ages = o.read(paul, "age")
    assert {(r.value, r.source) for r in ages} == {(42, BASE), (43, "birthday")}
    assert g.attr(paul, "age") == 42                     # the base graph never changed


def test_an_attribute_overlay_is_not_an_attribute_write():
    """The spike finding this module is built to preserve. `Graph.union` merges attrs by node, so two
    live derivations disagreeing about one `(node, attr)` collapse to whichever was unioned last — and
    the contradiction vanishes exactly when it matters. Shown here as the failure it would be."""
    g, paul = named(EMPTY, "Paul")
    collapsed = (g.with_node(paul, sex="man")).union(g.with_node(paul, sex="woman"))
    assert collapsed.attr(paul, "sex") == "woman"        # one reading survived. This is the bug.

    o = Overlays(g, [("h1", SetAttr(paul, "sex", "man")),
                     ("h2", SetAttr(paul, "sex", "woman"))])
    assert len(o.read(paul, "sex")) == 2                 # both survive


def test_an_overlay_is_gone_when_its_support_goes():
    """Revertability with no machinery: drop the effect and re-index. Nothing is retracted, and the base
    graph was never touched, so there is nothing to restore."""
    g, paul = named(EMPTY, "Paul", age=42)
    live = [("birthday", SetAttr(paul, "age", 43))]
    o = Overlays(g, live)
    assert len(o.read(paul, "age")) == 2

    o.effects = []                                       # the unit lost power
    o.reindex()
    assert [r.value for r in o.read(paul, "age")] == [42]


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

    assert [r.value for r in o.read(a, "plate")] == ["AB123"]     # reached through the merge
    assert [r.value for r in o.read(a, "colour")] == ["red"]
    assert [r.value for r in o.read(a, "floor")] == [3]           # overlay keyed on the dropped node


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
    assert [(r.value, r.source) for r in a.read(paul, "age")] == \
           [(r.value, r.source) for r in b.read(paul, "age")]
    assert [r.value for r in Overlays(g).read(paul, "age")] == [42]
