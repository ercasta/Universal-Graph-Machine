"""GUIDELINE — authored preference that may be wrong without being unsound.

`deliberation.md` §3. The weakest of the four forces, and the only one that can never change *what* is
reachable — a guideline **reorders and nothing else**. That is not timidity, it is the standing rule:

> **Rank a guess; prune a proof.**

`goal.forbid_action` prunes because a safety breach is a proof that every extension is dead. A guideline is
an author's opinion about what will help, so excluding on it could lose a solution — `driver`'s Sussman
check exists precisely because the winning move scored *low*. Everything here therefore adjusts order
within what `relevance` already decided, and can never make a reachable goal unreachable.

**⭐ A guideline is DATA, not a microfunction**, per the standing principle that microfunctions ship with
the engine and everything a domain contributes is data. The *ranker* that reads them ships here; the
guidelines themselves are nodes an author writes, a reader can inspect, and `conflict.py` can one day say
disagree.

**⚠ It orders WITHIN a `relevance` band and never across bands.** Band 4 means "this call, with these
bindings, writes exactly an open constraint" — derived from the function's own body, which is stronger
evidence than an author's heuristic. Letting the weaker evidence beat the stronger is how authored advice
makes a system dumber than it was. The composed score is `band + offset` with `offset` in `[0, 1)`, so
`rank >= 4` keeps meaning exactly what `driver` requires of it.

**⚠ The fraction is an ENCODING OF AN ORDER, not a weight.** There is no number here to tune, and that is
deliberate — `deliberation.md` §5 rejects weights because weights are the thing that needs tuning.
Precedence among guidelines is **declaration order**, the same free ordering `mock` already uses.

**Not recorded on the thread.** A guideline is consulted once per proposal — thousands of times in a
search — so logging it would swamp the record it would be trying to inform. What *is* auditable is the
guideline itself, standing in the graph, plus the plan that resulted.
"""
from __future__ import annotations

from . import function as fn
from .graph import Graph
from .types import is_a

PREFER = "prefer"
AVOID = "avoid"


def _advise(g: Graph, stance: str, *, function: str | None = None, on: str | None = None,
            when: str | None = None, because: str | None = None) -> str:
    if function is None and on is None:
        raise ValueError("a guideline must name a function, a node, or both — one that matches "
                         "everything is not advice")
    gl = g.mint("guideline", stance=stance, **{k: v for k, v in
                (("function", function), ("when", when), ("because", because)) if v is not None})
    if on is not None:
        g.link(gl, "on", on)                 # points OUT at the world — never pointed at, per the invariant
    return gl


def prefer(g: Graph, *, function=None, on=None, when=None, because=None) -> str:
    """Try this sooner, all else being equal. `when` is a type the subject must satisfy."""
    return _advise(g, PREFER, function=function, on=on, when=when, because=because)


def avoid(g: Graph, *, function=None, on=None, when=None, because=None) -> str:
    """Try this later — ⚠ **later, not never.** `goal.forbid_action` is the one that means never, and it
    prunes because it is a proof. Conflating the two is how advice quietly becomes a correctness rule."""
    return _advise(g, AVOID, function=function, on=on, when=when, because=because)


def advice(g: Graph) -> tuple:
    """Every guideline, in **declaration order** — which is precedence order, free, because `of_kind`
    returns mint order. Library-region data: guidelines describe the library, so like functions and types
    they do not hang off `root` and are never copied into a workbench."""
    return g.of_kind("guideline")


def applies(g: Graph, gl: str, name: str, bound: dict) -> bool:
    """Does this guideline speak to applying `name` with these already-resolved bindings?

    ⚠ `when` is checked against the **subject** — `function.subject_param`'s guarantee that the first
    parameter is the subject, used rather than re-derived. A condition richer than a type (the three
    constraint sorts, goal ancestry) arrives with decision rules; a type is what `types.py` already
    provides and it is the honest floor to start from."""
    want = g.attr(gl, "function")
    if want is not None and want != name:
        return False
    node = g.target(gl, "on")
    if node is not None and node not in bound.values():
        return False
    when = g.attr(gl, "when")
    if when is not None:
        subject = fn.subject_param(g, name)
        if subject is None or not is_a(g, bound.get(subject), when):
            return False
    return True


def ranker(g: Graph, base=None):
    """The engine-shipped ranker that reads authored guidelines. Drops into `driver.pursue(rank=...)`.

    Returns `base(...) + offset`, `offset` in `[0, 1)`, so band semantics survive untouched. Three tiers,
    and within `prefer` an earlier declaration outranks a later one:

        avoided  <  no guideline  <  preferred (earlier declared first)

    ⚠ `avoid` maps to the *bottom of its band*, never below it. Pushing it into a lower band would let a
    guideline overturn `relevance`, which §3 forbids — and would be indistinguishable from a prune the
    first time it hid the only move that worked."""
    from .driver import relevance
    base = base or relevance

    def rank(gr: Graph, name: str, bindings: dict, unmet: tuple) -> float:
        from . import workbench as W
        band = base(gr, name, bindings, unmet)
        rules = advice(gr)
        if not rules:
            return band
        bound = {p: (W.resolve(gr, m) or W.image_of(gr, m)) for p, m in bindings.items()}
        tier = 1                                          # nothing to say about this one
        for i, gl in enumerate(rules):
            if applies(gr, gl, name, bound):
                tier = 0 if gr.attr(gl, "stance") == AVOID else 2 + (len(rules) - i)
                break                                     # declaration order decides; first match wins
        return band + tier / (len(rules) + 3)             # strictly < 1, so the band is never crossed

    return rank


def governing(g: Graph, name: str, bound: dict) -> tuple:
    """Which guidelines spoke to this call, in precedence order — the reader's "why was this preferred?".

    Advice that cannot be interrogated afterwards is indistinguishable from a magic number, which is the
    objection to a learned weight and would be no less true of an authored one."""
    return tuple(gl for gl in advice(g) if applies(g, gl, name, bound))


__all__ = ["PREFER", "AVOID", "prefer", "avoid", "advice", "applies", "ranker", "governing"]
