"""Facts — a relation as a node, addressed by POSITION.

This is the wrapper the edges-as-nodes arc is built behind, and it is deliberately **behaviour
preserving**: the API is positional, the storage is still the `subject`/`object` edges that are there
today. Nothing about the graph changes when a caller moves onto it. What changes is that the caller
stops naming a role, so the storage can change later in one place instead of in every module.

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

⚠ **Coverage is partial by design, and that is the point of the increment.** `goal.py` is on this;
`conflict`, `criterion`, `driver` and `rules/holds.mf` still read the edges directly. That is safe only
because storage is unchanged, and it is what `raw_touches` below is for: the number that has to reach
zero before the storage may move.
"""
from __future__ import annotations

from .graph import Graph

#: Position → the edge label it is stored under today. Position 0 is the predicate and is not an edge:
#: it is the `label` attribute, which is where every existing reader looks for it.
#:
#: ⚠ This table is the whole of the transition. When storage moves to members, this module changes and
#: its callers do not — which is the only reason the wrapper is worth introducing before the change
#: rather than during it.
_STORED_AT = (None, "subject", "object")

#: How many participants a fact may have. Two, because every relation in the corpus is binary — see the
#: census. A third participant is a new position, not a new role name, and it costs one entry here.
ARITY = len(_STORED_AT) - 1


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
    return g.target(f, _STORED_AT[at])


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
    g.link(f, _STORED_AT[at], node)


def assert_fact(g: Graph, kind: str, pred: str | None, *members, **attrs) -> str:
    """Mint a fact node and fill its positions. `members` are positions 1..n, in order.

    `kind` stays a parameter because a `constraint` and a plain world relation are the same shape
    wearing different kinds, and collapsing them now would be the mistake this project keeps naming —
    one shape may be shared, one meaning may not."""
    f = g.mint(kind, **({"label": pred} if pred is not None else {}), **attrs)
    for i, m in enumerate(members, start=1):
        if m is not None:
            set_participant(g, f, i, m)
    return f


def raw_touches(g: Graph) -> int:
    """How many participant edges exist — the number that says how far the wrapper still has to reach.

    ⚠ It is a *population*, not an offender count, and the difference matters: while storage is
    unchanged a raw read is correct, so this cannot go red. It is the denominator for the conversion,
    in the shape `access.offenders` uses for the corpus it governs — and it exists so that *is the
    wrapper actually in the way* is answered by a number rather than by reading the imports."""
    return sum(len(g.targets(n, lbl))
               for n in g.nodes for lbl in _STORED_AT[1:])
