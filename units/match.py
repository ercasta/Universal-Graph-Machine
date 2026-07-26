"""MATCHING — topology and attributes, graded (`docs/units/model.md` §4).

A pattern is a tree of `Pat` atoms. Each atom constrains one node: crisp attributes it must carry,
gradable attributes it must carry (which **contribute their band to the match**), and outgoing edges to
sub-atoms. A match therefore has a **strength**, not a boolean verdict, and the strength is the `meet` of
everything that went into it.

**Nothing is matched implicitly, including names.** There is no name-equality rule in here. An atom that
wants a node called `"destination"` says `attrs={"name": "destination"}`, and that is *also* how role
nodes are identified — §4's third consequence, in the flesh. It is intolerable to write by hand, which is
exactly why `cnl.md` §2 makes `destination:` a **surface** convention that expands to this. The privilege
lives in the front end; the matcher grants none.

**There is no global similarity metric.** Similarity is authored per atom: an atom asking for a gradable
attribute is *choosing* to accept it at whatever degree the data carries. Nothing here compares two
arbitrary nodes for resemblance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator

from .band import at_least, meet
from .graph import Graph, Node


@dataclass(frozen=True)
class Pat:
    """One atom. Every field is a constraint the author wrote down."""

    var: str | None = None
    attrs: tuple = ()          # ((key, value), …) — crisp equality
    graded: tuple = ()         # (key, …) — must be present; its band enters the match strength
    out: tuple = ()            # sub-atoms reached by one outgoing edge

    def __post_init__(self) -> None:
        if isinstance(self.attrs, dict):
            object.__setattr__(self, "attrs", tuple(sorted(self.attrs.items())))
        if isinstance(self.graded, str):
            object.__setattr__(self, "graded", (self.graded,))


def atom(var: str | None = None, /, out: tuple = (), graded=(), **attrs) -> Pat:
    """`atom("c", name="Paul")` — the readable constructor."""
    return Pat(var=var, attrs=tuple(sorted(attrs.items())), graded=graded, out=tuple(out))


def role(name: str, target: Pat) -> Pat:
    """A role node, identified the only way the engine allows: by matching its `name` attribute
    explicitly. `cnl.md`'s `destination:` compiles to exactly this."""
    return Pat(attrs=(("name", name),), out=(target,))


@dataclass(frozen=True)
class Match:
    bindings: dict
    band: str | None           # None = crisp; the match involved no gradable attribute

    def __getitem__(self, k: str) -> Node:
        return self.bindings[k]


def _match_atom(g: Graph, pat: Pat, n: Node, binds: dict, used: frozenset) -> Iterator[tuple]:
    """Yield `(bindings, band)` for every way `pat` matches at node `n`."""
    if pat.var is not None:
        prior = binds.get(pat.var)
        if prior is not None and prior is not n:
            return                                   # identity join — never a name join
        binds = {**binds, pat.var: n}

    for k, v in pat.attrs:
        if g.attr(n, k) != v:
            return

    band = None
    for k in pat.graded:
        d = g.degree(n, k)
        if d is None:
            return                                   # the attribute is required; its degree grades it
        band = meet(band, d)

    yield from _match_out(g, pat.out, 0, n, binds, band, used | {n})


def _match_out(g: Graph, subs: tuple, i: int, n: Node, binds: dict, band, used) -> Iterator[tuple]:
    if i == len(subs):
        yield binds, band
        return
    for nxt in g.out(n):
        if nxt in used:
            continue                                 # two sub-atoms may not collapse onto one neighbour
        for b2, band2 in _match_atom(g, subs[i], nxt, binds, used):
            yield from _match_out(g, subs, i + 1, n, b2, meet(band, band2), used | {nxt})


def solve(g: Graph, pattern: tuple, theta: str | None = None) -> list:
    """Every way the conjunction `pattern` matches `g`, above θ.

    ⚠ **This is where cheap exact negation went** (§4). There is no membership test: *"P is absent"* is
    now *"nothing matched P above θ"*, and θ is a number you can be wrong about. Stated as a correction
    rather than a loss — the *"a little bird is not really a bird"* case needs it."""
    results: list = []
    _solve(g, pattern, 0, {}, None, results)
    out = [Match(b, band) for b, band in results
           if theta is None or at_least(band, theta)]
    return _dedupe(out)


def _solve(g: Graph, pattern: tuple, i: int, binds: dict, band, acc: list) -> None:
    if i == len(pattern):
        acc.append((binds, band))
        return
    for n in g.nodes:
        for b2, band2 in _match_atom(g, pattern[i], n, binds, frozenset()):
            _solve(g, pattern, i + 1, b2, meet(band, band2), acc)


def _dedupe(matches: list) -> list:
    seen, out = set(), []
    for m in matches:
        key = (tuple(sorted((k, v.nid) for k, v in m.bindings.items())), m.band)
        if key not in seen:
            seen.add(key)
            out.append(m)
    return out


def atoms(pattern) -> Iterator[Pat]:
    """Every atom in a pattern, for inspection. `model.md` §12 invariant 1 — *no rule pattern names a
    scope* — is tested by walking this and looking at what the author wrote."""
    stack = list(pattern) if isinstance(pattern, (tuple, list)) else [pattern]
    while stack:
        p = stack.pop()
        yield p
        stack.extend(p.out)


__all__ = ["Pat", "Match", "atom", "role", "solve", "atoms"]
