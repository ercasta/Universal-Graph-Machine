"""Clock — time as a node that points at what it dates.

A moment is a node, and it points at everything it dates. Nothing already in the graph is
modified to acquire a time.

Three things follow from that direction, and they are why it is right rather than merely a
convention. One look dates many facts, so the natural cardinality is one moment to many dated
things, which the edge direction gives for free. Dating is non-invasive, so a fact can be dated
after the event, by something that does not own it. And it matches the direction invariant the
rest of the engine enforces: the record points at the world and the world never points back.

`dated()` is therefore a reverse lookup and costs no scan, because the reverse index is
maintained.

Absolute and relative moments are both first class. `now()` stamps from the real clock — the
agent is assumed to have one — but a moment may carry no scalar at all and be placed only by
`before` edges: "after the meeting", "a minute after the pan is hot". Order here is a partial
order over moment nodes, read with `path.reaches`, with the scalar used where both moments have
one. That makes this the third ranking in the engine read by the same traversal, alongside
authority for discourse and norms, and containment for reach.

Edges cannot be dated, and that is a substrate fact rather than a decision: edge properties are
keyed by position and reindex on insertion, so there is nothing stable for a moment to point at.
The available answer costs no substrate change — an edge's history is the record of the changes
that made and unmade it, and dating that record dates the edge. This module only has to be right
about moments.

See `docs/memory.md`.
"""
from __future__ import annotations

import time as _wallclock

from .graph import Graph

MOMENT = "moment"
DATES, BEFORE = "dates", "before"


def moment(g: Graph, *, at=None, label: str | None = None) -> str:
    """A point in time. `at` is an absolute stamp; omit it for a relative, undefined moment.

    An undefined moment is not a defect and must not be filled in with a guess — *"a minute after the
    pan is hot"* is a real thing to say before any clock reading exists, and `before` is what places it."""
    return g.mint(MOMENT, **{k: v for k, v in (("at", at), ("label", label)) if v is not None})


def now(g: Graph, *, label: str | None = None) -> str:
    """A moment stamped from the real clock. The one place wall-clock time enters the engine.

    Deliberately one place, for the same reason `dispatch.service` is the one place an effect leaves:
    a reading taken wherever it is convenient cannot be substituted in a check, and a test that cannot
    control the clock is a test that is slow or flaky. Callers wanting a fixed clock pass `at=`."""
    return moment(g, at=_wallclock.time(), label=label)


def stamp(g: Graph, when: str, *nodes: str) -> str:
    """Date these nodes with this moment. The moment points at them, never the reverse."""
    for n in nodes:
        if n not in g.targets(when, DATES):
            g.link(when, DATES, n)
    return when


def dated(g: Graph, node: str) -> tuple:
    """Every moment that dates this node — O(1) on the reverse index, oldest-minted first."""
    return tuple(m for m in g.sources(node, DATES) if g.kind(m) == MOMENT)


def at_of(g: Graph, when: str):
    """The absolute stamp, or `None` for a relative moment."""
    return g.attr(when, "at")


def arrived(g: Graph, when: str, *, at=None) -> bool:
    """Has this moment come? `at` overrides the wall clock, so a check need not sleep.

    A relative moment can never `arrive`, and this refuses rather than guessing. *"A minute after
    the pan is hot"* is a real thing to say and carries no scalar, so there is nothing to compare a clock
    reading against. Answering `False` would make a timer that silently never fires — indistinguishable
    from one that is merely early — and answering `True` would fire it immediately. Both are the
    silent-acceptance failure this project keeps catching, so the caller is told instead."""
    stamp_at = at_of(g, when)
    if stamp_at is None:
        raise ValueError(
            f"{when} is a relative moment with no absolute stamp, so nothing can say whether it has "
            f"arrived. Place it with `before`, or give it an `at=` when it is minted.")
    return (at if at is not None else _wallclock.time()) >= stamp_at


def follows(g: Graph, later: str, earlier: str) -> str:
    """Place `later` after `earlier` in the partial order. Returns the edge's source, for chaining."""
    if later == earlier:
        raise ValueError("a moment cannot follow itself")
    g.link(earlier, BEFORE, later)
    return later


def precedes(g: Graph, a: str, b: str) -> bool:
    """Is `a` before `b`? Scalars when both have one, otherwise the `before` partial order.

    Scalars first, and they are decisive. Two absolutely-stamped moments are ordered by their
    stamps whatever the graph says; disagreeing with the clock would make a recorded reading unusable.
    Returns `False` for *unordered*, which is not the same as *after* — ask both ways to tell them
    apart, exactly as `locate.relate` returns `None` rather than inventing an order."""
    if a == b:
        return False
    x, y = at_of(g, a), at_of(g, b)
    if x is not None and y is not None:
        return x < y
    from .path import reaches
    return reaches(g, a, BEFORE, b)


def ordered(g: Graph, moments) -> tuple:
    """The moments that carry a stamp, in time order. Undated ones are dropped, not appended — a
    relative moment has no position on this line and putting it at either end would be an invention."""
    return tuple(sorted((m for m in moments if at_of(g, m) is not None), key=lambda m: at_of(g, m)))


def moments(g: Graph) -> tuple:
    return g.of_kind(MOMENT)


def describe(g: Graph, when: str) -> str:
    stamped = at_of(g, when)
    head = g.attr(when, "label") or ("t=%.3f" % stamped if stamped is not None else "sometime")
    what = len(g.targets(when, DATES))
    return f"{head} ({what} thing{'' if what == 1 else 's'} dated)"


__all__ = ["arrived", "MOMENT", "DATES", "BEFORE", "moment", "now", "stamp", "dated", "at_of",
           "follows", "precedes", "ordered", "moments", "describe"]
