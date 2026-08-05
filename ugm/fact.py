"""Facts — a relation as a node, addressed by POSITION.

This is the wrapper the edges-as-nodes arc is built behind, and **the first swap has been through it**:
participants were `subject` / `object` edges and are now ordered members of one label. Every caller —
`goal`, `conflict`, `criterion`, `driver` and `rules/holds.mf` — was written against positions and none
of them changed when the storage did. That is the whole claim of the wrapper, and it is the evidence
for it rather than an argument.

**Why positional, and not `subject` / `object`.** Roles are carried by position and direction here, and
role-*labelled* participation edges are a rejected shape. A label is also a name, and a name is where
meaning lives — so `subject` and `object` in the graph are two more entries in a vocabulary that
already carries one relation under four names and one name over three relations. Position commits to
nothing and is what a fact is: an ordered tuple.

**Position 0 is the predicate.** A fact is `[predicate, subject, object]`, which is S-P-O with position
carrying everything — the shape this project settled on long before this module, and the one a
`constraint` node has been an instance of all along without saying so. Today the predicate lives in the
`label` attribute rather than as a member, because that is where `holds` and `driver._relevance` read
it; `predicate` below is the seam that hides it.

⚠ **What is NOT here, on purpose.** There is no `retract`. A frame needs to record an *absence* rather
than delete an edge — an additive delta inherits its parent's connections and re-leaks the very thing
this arc exists to stop — but nothing consumes that yet, and machinery built for no consumer is the
trade this codebase declines. It arrives with the frame work, not before it.

⚠ **A constraint is a HUB, and world facts are not.** The chosen encoding for `a on b` is the per-fact
2-hop path `a --> on#7 --> b` ([harmony.md](../docs/harmony.md)). A constraint does not take that shape,
and the reason is the direction invariant rather than convenience: a constraint *requires* a relation
rather than asserting it, and putting it on the path would make `a` point at metadata — while *a goal
points at the world and is never pointed at by it*. So metadata hangs its participants off itself, and
only the role names became positions here.
"""
from __future__ import annotations

from .graph import Graph

#: The one label a fact's participants hang from. Position IS the ordinal along this label, which is
#: why there is a single name here where there were two role names before: `subject` and `object` were
#: two more entries in a vocabulary that already carries one relation under four names.
#:
#: Ordered adjacency is a substrate primitive here — `(src, label) -> [dst, …]`, ordered and journaled —
#: so position costs nothing to store and nothing to maintain.
MEMBERS = "at"

#: How many participants a fact may have. Two, because every relation in the corpus is binary — see the
#: census. This is a *validation* bound rather than a storage one: the members are a list, so raising it
#: is this line and nothing else. It is kept low on purpose, because an off-by-one that lands inside the
#: arity is a wrong answer while one that lands outside it is an exception.
ARITY = 2


def predicate(g: Graph, f: str):
    """Position 0 — what relation this fact asserts, or `None` if it asserts none.

    Stored as an attribute rather than as a member, which is a fact about today's storage and not about
    the shape: `holds` dispatches on it and `driver._relevance` ranks on it, both by reading `label`."""
    return g.attr(f, "label")


def participant(g: Graph, f: str, at: int):
    """The node at this position, or `None` if the fact does not fill it.

    A missing participant is ordinary rather than exceptional — a `type` constraint with no subject is
    *existential* (`is there any t under here?`), and an `attr` constraint has a subject and no object.
    So this answers `None` and lets the caller decide, which is what every existing reader already does
    with `g.target`."""
    if not 1 <= at <= ARITY:
        raise ValueError(f"position {at} is not one of 1..{ARITY}")
    # ⚠ The bound above is not decoration. `Graph.at` accepts a negative index the way Python does, so
    # position 0 would arrive as index -1 and answer with the LAST participant — a wrong node rather
    # than an error, which is the failure mode this codebase least wants.
    return g.at(f, MEMBERS, at - 1)


def participants(g: Graph, f: str) -> tuple:
    """Every position, in order, with `None` for the ones this fact does not fill.

    Fixed width rather than compacted, so position survives a gap: an `attr` constraint's subject is
    position 1 whether or not anything sits at 2, and a caller that indexes into a compacted tuple would
    read the object out of the subject's place the moment a fact left a hole."""
    return tuple(participant(g, f, i) for i in range(1, ARITY + 1))


def set_participant(g: Graph, f: str, at: int, node: str) -> None:
    """Put a node at this position. Writes once; a position is not a list."""
    if participant(g, f, at) is not None:
        raise ValueError(f"position {at} of {f} is already filled")
    # Positions are an ordinal along one label, so a gap is not representable: filling 2 while 1 is
    # empty would store the object where the subject is read from. Refused rather than padded, because
    # every fact in the corpus fills a prefix — an `attr` constraint has a subject and no object, a
    # subjectless `type` constraint has neither, and nothing has an object without a subject.
    if g.count(f, MEMBERS) != at - 1:
        raise ValueError(f"position {at} of {f} would leave a gap: only {g.count(f, MEMBERS)} filled")
    g.link(f, MEMBERS, node)


def assert_fact(g: Graph, kind: str, pred: str | None, *members, **attrs) -> str:
    """Mint a fact node and fill its positions. `members` are positions 1..n, in order.

    `kind` stays a parameter because a `constraint` and a plain world relation are the same shape
    wearing different kinds, and collapsing them now would be the mistake this project keeps naming —
    one shape may be shared, one meaning may not."""
    f = g.mint(kind, **({"label": pred} if pred is not None else {}), **attrs)
    for i, m in enumerate(members, start=1):
        if m is None:
            break              # a prefix, and the rest is absent rather than empty — see above
        set_participant(g, f, i, m)
    return f


def raw_touches(g: Graph) -> int:
    """How many participant edges exist — the number that says how far the wrapper still has to reach.

    ⚠ It is a *population*, not an offender count, and the difference matters: while storage is
    unchanged a raw read is correct, so this cannot go red. It is the denominator for the conversion,
    in the shape `access.offenders` uses for the corpus it governs — and it exists so that *is the
    wrapper actually in the way* is answered by a number rather than by reading the imports."""
    return sum(len(g.targets(n, MEMBERS)) for n in g.nodes)
