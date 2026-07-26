"""MATCHING — topology and attributes, graded (`docs/units/model.md` §4).

A pattern is a conjunction of `Pat` atoms (a tree each) and `Absent` guards. Each atom constrains one
node: crisp attributes it must carry, gradable attributes it must carry (which **contribute their band
to the match**), and outgoing edges to sub-atoms. A match therefore has a **strength**, not a boolean
verdict, and the strength is the `meet` of everything that went into it.

**Nothing is matched implicitly, including names.** There is no name-equality rule in here. An atom that
wants a node called `"destination"` says so, and that is *also* how role nodes are identified — §4's
third consequence, in the flesh. It is intolerable to write by hand, which is exactly why `cnl.md` §2
makes `destination:` a **surface** convention that expands to this. The privilege lives in the front
end; the matcher grants none.

**There is no global similarity metric.** Similarity is authored per atom. An `AttrVar` lets a rule say
*"these two nodes carry the same name"* — but it is the **rule** saying name-equality counts here, which
is precisely §4's worked example. The engine still has no opinion.

**Absence is not free** (§4). `Absent` is *"nothing matched this above θ"*, not a membership test. It can
be wrong, and it is a threshold you chose.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator

from .band import at_least, meet
from .graph import Graph, Node


@dataclass(frozen=True)
class AttrVar:
    """A variable over an attribute **value** rather than a node.

    `atom("a", name=AttrVar("n"))` with `atom("b", name=AttrVar("n"))` means *"two nodes carrying the
    same name"* without the rule knowing which name. This is the one construct that makes authored
    similarity expressible; without it a rule could only ever ask for a name it already knew."""

    name: str


@dataclass(frozen=True)
class Pat:
    """One atom. Every field is a constraint the author wrote down."""

    var: str | None = None
    attrs: tuple = ()          # ((key, value | AttrVar), …)
    graded: tuple = ()         # (key, …) — must be present; its band enters the match strength
    out: tuple = ()            # sub-atoms reached by one outgoing edge

    def __post_init__(self) -> None:
        if isinstance(self.attrs, dict):
            object.__setattr__(self, "attrs", tuple(sorted(self.attrs.items(), key=lambda kv: kv[0])))
        if isinstance(self.graded, str):
            object.__setattr__(self, "graded", (self.graded,))


@dataclass(frozen=True)
class Absent:
    """A negative conjunct: this must **not** match, above θ.

    ⚠ §4 is explicit that the cheap exact negation is gone and that this is a correction rather than a
    loss. What is here is *"nothing I could find matched"*, evaluated against the value on the gate —
    bounded, and therefore honest — never *"this is not derivable anywhere"*."""

    atoms: tuple

    def __post_init__(self) -> None:
        if isinstance(self.atoms, Pat):
            object.__setattr__(self, "atoms", (self.atoms,))


def atom(var: str | None = None, /, out: tuple = (), graded=(), **attrs) -> Pat:
    """`atom("c", name="Paul")` — the readable constructor."""
    return Pat(var=var, attrs=tuple(sorted(attrs.items(), key=lambda kv: kv[0])),
               graded=graded, out=tuple(out))


def role(name: str, target: Pat) -> Pat:
    """A role node, identified the only way the engine allows: by matching its `name` attribute
    explicitly. `cnl.md`'s `destination:` compiles to exactly this."""
    return Pat(attrs=(("name", name),), out=(target,))


def absent(*atoms: Pat) -> Absent:
    return Absent(tuple(atoms))


@dataclass(frozen=True)
class Match:
    bindings: dict             # var -> Node
    values: dict               # AttrVar name -> attribute value
    band: str | None           # None = crisp; the match involved no gradable attribute

    def __getitem__(self, k: str) -> Node:
        return self.bindings[k]


def _match_atom(g: Graph, pat: Pat, n: Node, binds: dict, vals: dict,
                used: frozenset) -> Iterator[tuple]:
    """Yield `(bindings, values, band)` for every way `pat` matches at node `n`."""
    if pat.var is not None:
        prior = binds.get(pat.var)
        if prior is not None and prior is not n:
            return                                   # identity join — never a name join
        binds = {**binds, pat.var: n}

    for k, v in pat.attrs:
        got = g.attr(n, k)
        if isinstance(v, AttrVar):
            if got is None:
                return
            seen = vals.get(v.name, _MISSING)
            if seen is not _MISSING and seen != got:
                return                               # the same AttrVar must see the same value
            vals = {**vals, v.name: got}
        elif got != v:
            return

    band = None
    for k in pat.graded:
        d = g.degree(n, k)
        if d is None:
            return                                   # the attribute is required; its degree grades it
        band = meet(band, d)

    yield from _match_out(g, pat.out, 0, n, binds, vals, band, used | {n})


_MISSING = object()


def _match_out(g: Graph, subs: tuple, i: int, n: Node, binds: dict, vals: dict,
               band, used) -> Iterator[tuple]:
    if i == len(subs):
        yield binds, vals, band
        return
    for nxt in g.out(n):
        if nxt in used:
            continue                                 # two sub-atoms may not collapse onto one neighbour
        for b2, v2, band2 in _match_atom(g, subs[i], nxt, binds, vals, used):
            yield from _match_out(g, subs, i + 1, n, b2, v2, meet(band, band2), used | {nxt})


def solve(g: Graph, pattern: tuple, theta: str | None = None) -> list:
    """Every way the conjunction `pattern` matches `g`, above θ."""
    results: list = []
    _solve(g, tuple(pattern), 0, {}, {}, None, theta, results)
    out = [Match(b, v, band) for b, v, band in results
           if theta is None or at_least(band, theta)]
    return _dedupe(out)


def _solve(g: Graph, pattern: tuple, i: int, binds: dict, vals: dict, band,
           theta, acc: list) -> None:
    if i == len(pattern):
        acc.append((binds, vals, band))
        return
    item = pattern[i]

    if isinstance(item, Absent):
        # Evaluated with the bindings established so far, so a guard can talk about them.
        blocked: list = []
        _solve(g, item.atoms, 0, binds, vals, None, theta, blocked)
        if any(theta is None or at_least(b, theta) for _, _, b in blocked):
            return
        _solve(g, pattern, i + 1, binds, vals, band, theta, acc)
        return

    for n in g.nodes:
        for b2, v2, band2 in _match_atom(g, item, n, binds, vals, frozenset()):
            _solve(g, pattern, i + 1, b2, v2, meet(band, band2), theta, acc)


def _dedupe(matches: list) -> list:
    seen, out = set(), []
    for m in matches:
        key = (tuple(sorted((k, v.nid) for k, v in m.bindings.items())),
               tuple(sorted(m.values.items())), m.band)
        if key not in seen:
            seen.add(key)
            out.append(m)
    return out


def atoms(pattern) -> Iterator[Pat]:
    """Every atom in a pattern, for inspection. `model.md` §12 invariant 1 — *no rule pattern names a
    scope* — is tested by walking this and looking at what the author wrote."""
    stack = []
    for p in (pattern if isinstance(pattern, (tuple, list)) else [pattern]):
        stack.extend(p.atoms if isinstance(p, Absent) else [p])
    while stack:
        p = stack.pop()
        yield p
        stack.extend(p.out)


__all__ = ["Pat", "Match", "Absent", "AttrVar", "atom", "role", "absent", "solve", "atoms"]
