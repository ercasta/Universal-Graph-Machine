"""The copy boundary under hubs — `reachable` inverts, and the probe says what that costs.

[facts-as-nodes.md](../docs/facts-as-nodes.md) names this as one of the two things that **change shape
rather than move**:

> *`reachable` inverts.* "Everything reachable from `start` by outgoing edges" is the workbench's copy
> boundary — and if entities have no outgoing edges it returns **just `start`**. The boundary must become
> a **reverse closure**: the facts mentioning these entities, then the entities those mention,
> transitively. Different termination properties, and it needs an explicit bound where the forward walk
> needed none.

That paragraph is a design note. This is the measurement of it, run **before** the conversion rather
than after, for the reason `ugm.leak` states in its own docstring: during a change that moves every
relation from an edge to a node, a suite going red says a hundred things at once and none of them says
which one this was.

⭐ **Both of the probe's findings are about what the forward walk was getting for free**, and neither is
in the design note. The note treats the inversion as a rewrite with a bound to be chosen. It is two
losses, and the bound is only the first of them:

1. **The direction invariant stops protecting the copy boundary.** `workbench.reachable`'s docstring
   says *"metadata is not reached, by the direction invariant — mappings, applications, hypotheses and
   plans all point at domain nodes and are never pointed at by them"*, and `facts-as-nodes.md` reasons
   from the same invariant that *"a forward traversal from `a` cannot reach the version in a
   hypothesis"*. Both are true **of a forward walk**. The copy boundary is the one walk that cannot stay
   forward, so it is precisely the walk that loses the guarantee: a reverse closure from `a` arrives at
   every hub pointing at `a`, and metadata is exactly what points at domain nodes. Measured below —
   unbounded, the boundary swallows the hypotheses.
2. ⚠⚠⚠ **The boundary loses its ORDER, and the order is load-bearing.** The forward walk's order is a
   fact about the graph: `g.labels` is sorted and `g.targets` is an insertion-ordered tuple. The reverse
   index is a **`set`** (`Graph.inc: dict[str, set]`), so `g.sources` has nothing to preserve and sorts
   by node id — and a node id comes from a process-global counter. That is the defect
   `workbench.reachable` records at length and paid a session for: copy order decides mint order decides
   `proposals` order, which is the search's last tie-break, and the identical five-block goal was
   measured at 12 imagined states, then 306, then budget-exhausted failure, on consecutive runs of one
   process.

So the inversion is not a rewrite of one loop. **It needs the reverse index to become ordered**, which
is a substrate change, and it needs an authored bound where the shape used to supply one.

`python -m ugm.boundary`.
"""
from __future__ import annotations

from . import fact as F, workbench as W
from .graph import Graph, new_graph

#: What a reverse closure is allowed to walk into. This is the *authored bound* finding 1 says the
#: inversion needs: under hubs, "metadata does not point at the world" is false — a mapping, a claim and
#: a constraint all point at domain nodes, and a reverse walk arrives at all three. Naming the kinds the
#: boundary means is the smallest honest replacement, and it is discipline where the forward walk had
#: structure.
WORLD = ("fact",)


def forward(g: Graph, start: str) -> dict:
    """Today's boundary, unchanged — `workbench.reachable`, so the comparison is against the live one."""
    return W.reachable(g, start)


def reverse(g: Graph, start: str, *, kinds=WORLD, member: str = F.MEMBERS) -> dict:
    """The inverted boundary: facts mentioning these entities, then the entities those mention.

    One walk rather than two alternating ones, because a hub is reached *backwards* from a participant
    and its participants are reached *forwards* from it, and nested reification means either may be
    either. So each node is expanded in both directions along the one member label, and the closure is
    over that.

    `kinds=None` removes the bound, which is what the unbounded measurement below runs.

    ⚠ The visit order is whatever `g.sources` hands back, which is sorted by node id. That is not an
    oversight in this function — there is nothing better available, and saying so is finding 2."""
    seen, stack = {}, [start]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen[n] = None
        for hub in g.sources(n, member):                      # ⚠ sorted by node id: see the docstring
            if kinds is None or g.kind(hub) in kinds:
                if hub not in seen:
                    stack.append(hub)
        for m in g.targets(n, member):
            if m not in seen:
                stack.append(m)
    return seen


# --- the two worlds, built to be the same world -----------------------------------------------------
def edge_world(g: Graph, n: int = 3) -> tuple:
    """`a on b on c on table`, in today's shape — a labelled edge per relation.

    Returned as `(entities, start)` so the two builders answer alike and the comparison is structural
    rather than by name."""
    table = g.mint("floor", label="table")
    blocks = [g.mint("block", label=f"b{i}") for i in range(n)]
    below = blocks[1:] + [table]
    for b, under in zip(blocks, below):
        g.link(b, "on", under)
    return tuple(blocks) + (table,), blocks[0]


def hub_world(g: Graph, n: int = 3) -> tuple:
    """The same world under the arc's shape: entities with **no outgoing edges**, one hub per relation."""
    table = g.mint("floor", label="table")
    blocks = [g.mint("block", label=f"b{i}") for i in range(n)]
    below = blocks[1:] + [table]
    for b, under in zip(blocks, below):
        F.assert_fact(g, "fact", "on", b, under)
    return tuple(blocks) + (table,), blocks[0]


def _hypothesis_on(g: Graph, entity: str) -> str:
    """Metadata pointing at a domain node — the shape the direction invariant is about.

    A `same_as` bridge is the arc's own example (*the identity bridge is the same construct*), and it is
    what `workbench`'s mapping becomes: it points at the identity and at the imagined version, and is
    pointed at by neither. Under a forward walk that makes the version unreachable from the real node.
    Under a reverse one it makes it one hop away."""
    version = g.mint("block", label="imagined")
    F.assert_fact(g, "same_as", "same_as", entity, version)
    return version


# --- the measurements -------------------------------------------------------------------------------
def collapse() -> dict:
    """Finding 0, the premise: does the forward boundary really collapse under hubs?"""
    g = new_graph()
    _, e_start = edge_world(g)
    _, h_start = hub_world(g)
    return {"forward_on_edges": len(forward(g, e_start)),
            "forward_on_hubs": len(forward(g, h_start)),
            "reverse_on_hubs": len(reverse(g, h_start))}


def isolation() -> dict:
    """Finding 1: unbounded, the inverted boundary walks into metadata.

    The control is the pair — the *forward* walk on the *edge* world with the same bridge planted must
    not reach the version, or the probe is measuring its own construction rather than the inversion."""
    g = new_graph()
    _, e_start = edge_world(g)
    e_version = _hypothesis_on(g, e_start)

    g2 = new_graph()
    _, h_start = hub_world(g2)
    h_version = _hypothesis_on(g2, h_start)

    return {"forward_reaches_the_version": e_version in forward(g, e_start),
            "reverse_unbounded_reaches_it": h_version in reverse(g2, h_start, kinds=None),
            "reverse_bounded_reaches_it": h_version in reverse(g2, h_start),
            "unbounded_size": len(reverse(g2, h_start, kinds=None)),
            "bounded_size": len(reverse(g2, h_start))}


def _shape(g: Graph, order) -> tuple:
    """A visit order as the world sees it, not as the ids do — so two builds can be compared at all."""
    return tuple(g.attr(n, "label") or g.kind(n) for n in order)


def fan_edge_world(g: Graph, n: int = 3) -> tuple:
    """A hand holding several blocks, in today's shape — one node, several edges under one label.

    ⚠ **A chain cannot measure this and the first version used one.** `a on b on c on table` is a path:
    every node has one unvisited neighbour, so the visit order is forced whatever the walk sorts by, and
    the probe reported STABLE against a defect that was really there. *A homogeneous fixture cannot
    measure a discriminator*, and a path is homogeneous for an ordering question. The branch is the
    fixture."""
    hand = g.mint("hand", label="hand")
    held = [g.mint("block", label=f"b{i}") for i in range(n)]
    for b in held:
        g.link(hand, "holds", b)
    return (hand,) + tuple(held), hand


def fan_hub_world(g: Graph, n: int = 3) -> tuple:
    """The same fan under hubs — `holds(hand, b0)`, `holds(hand, b1)`, … , one hub each."""
    hand = g.mint("hand", label="hand")
    held = [g.mint("block", label=f"b{i}") for i in range(n)]
    for b in held:
        F.assert_fact(g, "fact", "holds", hand, b)
    return (hand,) + tuple(held), hand


#: How many nodes `fan_hub_world` mints before the first hub — the hand and the blocks. Named because
#: the straddle below has to be placed relative to it, and a builder that grew by one would silently
#: stop straddling and the probe would report stable again for the wrong reason.
_LEAD = 1 + 3


def _straddle(g: Graph, lead: int = _LEAD) -> int:
    """Mint filler until the *next* world's hubs will span a power of ten.

    ⚠ **The first version of this burned a round 200 ids and reported the order STABLE** — which is this
    project's standing diagnosis for a plant that stays green: *a homogeneous fixture cannot measure a
    discriminator*. Ids are compared as strings, so a reordering needs the ids at one node to straddle a
    power of ten (`#1000` sorts before `#999`), and hoping a fixed burn lands there is hoping. The
    recorded near-miss said the same thing in the same words — *three successive guards passed with the
    defect planted; the surviving one drives the id counter across a power of ten on purpose* — and this
    is that, constructed rather than wished for."""
    nxt = int(g.mint("probe").split("#")[1]) + 1
    power = 10 ** len(str(nxt + lead))                 # the next power of ten above where we would land
    while nxt + lead < power - 1:
        nxt = int(g.mint("filler").split("#")[1]) + 1
    # The first hub now takes `power - 1` and the rest go over the boundary, so mint order and string
    # order disagree. ⚠ `lead` has to match what the caller mints between here and the first hub, and
    # getting it wrong is silent — the probe reported STABLE twice for exactly that reason. `ordering`
    # therefore checks that the straddle actually happened rather than trusting this arithmetic.
    return power


def ordering() -> dict:
    """Finding 2: the inverted boundary's order is a fact about the id counter, not about the graph.

    Two isomorphic worlds in one process, the second built with its hubs straddling a power of ten. The
    forward walk on the edge world is run beside it as the control: if *both* orders moved the probe
    would be measuring the builder, and if neither did it would be measuring nothing."""
    g = new_graph()
    _, e1 = fan_edge_world(g)
    _, h1 = fan_hub_world(g)
    _, e2 = fan_edge_world(g)          # the control's second world, built before the straddle: its order
    _straddle(g)                       # is structural, so where in the id range it sits cannot matter
    _, h2 = fan_hub_world(g)

    # ⚠ The condition this probe rests on, verified rather than computed. Mint order is what the hubs
    # were created in; `g.sources` is what the walk sees. If they agree, the straddle did not happen and
    # a STABLE reading below would mean nothing — which is what it meant the first two times.
    minted = [n for n in g.nodes if g.kind(n) == "fact" and h2 in g.targets(n, F.MEMBERS)]
    straddled = tuple(g.sources(h2, F.MEMBERS)) != tuple(minted)

    fwd1, fwd2 = _shape(g, forward(g, e1)), _shape(g, forward(g, e2))
    rev1, rev2 = _shape(g, reverse(g, h1)), _shape(g, reverse(g, h2))
    return {"straddled": straddled,
            "forward_order_1": fwd1, "forward_order_2": fwd2, "forward_stable": fwd1 == fwd2,
            "reverse_order_1": rev1, "reverse_order_2": rev2, "reverse_stable": rev1 == rev2}


def equivalence() -> dict:
    """Does the inverted boundary answer the same world the forward one does?

    The entities must match exactly. The hubs are extra by construction — they are the relations, which
    had no node to be copied before — so they are reported rather than compared, since *how much bigger
    is the boundary* is the question a conversion actually has to answer."""
    g = new_graph()
    e_all, e_start = edge_world(g, 8)
    h_all, h_start = hub_world(g, 8)

    got_e = forward(g, e_start)
    got_h = reverse(g, h_start)
    entities = {n for n in got_h if g.kind(n) != "fact"}
    return {"forward_entities": len(got_e),
            "reverse_entities": len(entities),
            "same_world": len(entities) == len(got_e) == len(e_all) == len(h_all),
            "reverse_total": len(got_h),
            "growth": round(len(got_h) / len(got_e), 2)}


def report() -> str:
    c, i, o, e = collapse(), isolation(), ordering(), equivalence()
    lines = [
        "0. the premise — a forward walk collapses under hubs",
        f"   forward, edges: {c['forward_on_edges']} nodes   forward, hubs: {c['forward_on_hubs']} "
        f"({'just the start, as predicted' if c['forward_on_hubs'] == 1 else 'NOT the predicted collapse'})",
        f"   reverse, hubs:  {c['reverse_on_hubs']} nodes",
        "",
        "1. the direction invariant does not survive the inversion",
        f"   forward walk reaches an imagined version: "
        f"{'YES — the control is broken' if i['forward_reaches_the_version'] else 'no (control)'}",
        f"   reverse walk, unbounded, reaches it:     "
        f"{'YES — metadata is inside the copy boundary' if i['reverse_unbounded_reaches_it'] else 'no'}",
        f"   reverse walk, bounded by kind, reaches:  "
        f"{'YES' if i['reverse_bounded_reaches_it'] else 'no — but the bound is AUTHORED, not structural'}",
        f"   boundary size: {i['unbounded_size']} unbounded vs {i['bounded_size']} bounded",
        "",
        "2. the inverted boundary has no order of its own",
        f"   control — the second world's hubs really do straddle a power of ten: "
        f"{'yes' if o['straddled'] else 'NO, so nothing below means anything'}",
        f"   forward, two isomorphic worlds in one process: "
        f"{'stable' if o['forward_stable'] else 'UNSTABLE'}",
        f"   reverse, the same two:                        "
        f"{'stable' if o['reverse_stable'] else 'UNSTABLE — sorted by node id, which is a fact about nothing'}",
        f"     {o['reverse_order_1']}",
        f"     {o['reverse_order_2']}",
        "",
        "3. what the boundary costs, at 8 blocks",
        f"   entities: {e['forward_entities']} forward, {e['reverse_entities']} reverse "
        f"({'the same world' if e['same_world'] else 'DIFFERENT WORLDS'})",
        f"   total copied: {e['reverse_total']} against {e['forward_entities']} — {e['growth']}×, "
        f"the relations now being nodes",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
