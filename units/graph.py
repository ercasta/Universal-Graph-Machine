"""The graph — `docs/units/model.md` §3.

The whole inventory: nameless nodes, directed nameless edges, and two sorts of attribute (crisp valued,
and gradable carrying a degree). There are **no node kinds**, and nothing here knows what a relation, a
role, an occurrence or a statement is — those are encodings *in* the graph, not types *of* it.

**`name` has no privileged status** (§12 invariant 7). It is stored in `attrs` beside `age` and `colour`,
there is no `by_name` index, and nothing in this module compares two nodes' names. A rule that wants
name-equality asks for it (§4).

**A `Graph` is a value, not a store.** Units are handed one and produce another (§5). This is what makes
the tunnel work at all: *scope is the provenance of the value at your gate*, so a supposition is an
ordinary graph-to-graph transformation and no rule ever has to ask which world it is in (§6).
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Iterable, Mapping

_NID = itertools.count(1)


def _freeze(m: Mapping) -> Mapping:
    """Make the attribute maps genuinely read-only.

    **Immutability is load-bearing, not hygiene** (§5, §12 invariant 3): a unit sees only what its gates
    deliver, and if it can mutate the value it was handed then isolation is a convention rather than a
    fact — and the tunnel's whole guarantee is that a supposition cannot reach the base world. A frozen
    dataclass around plain dicts does *not* give this: the dicts stay writable through the field. So the
    maps are proxied, inner and outer.

    The cost is a copy per construction. Accepted for now, and it is the obvious first thing to measure
    if graph-building shows up hot."""
    return MappingProxyType({k: MappingProxyType(dict(v)) for k, v in m.items()})


class Node:
    """An identity. `hint` is a debugging label with **no semantics** — it is not an attribute, it is not
    matched against, and two nodes with the same hint are two nodes ([[node-identity-is-not-a-semantic-proxy]]).

    Minting is the only way to get one, and two calls always give two distinct nodes. That is
    `cnl.md` §1's *create, never merge* holding at the bottom of the stack: there is no operation here
    that identifies two nodes, so no amount of boundary code can accidentally perform one."""

    __slots__ = ("nid", "hint")

    def __init__(self, hint: str = "") -> None:
        self.nid = next(_NID)
        self.hint = hint

    def __repr__(self) -> str:
        return f"#{self.nid}{':' + self.hint if self.hint else ''}"


@dataclass(frozen=True)
class Graph:
    """An immutable graph value.

    `attrs` are crisp (`name = "Paul"`, `age = 42`); `degrees` are gradable (`good`, `beautiful`,
    `likely`) and carry a band. Keeping them in separate maps is §3's two-sorts distinction made
    structural, so the matcher cannot silently treat one as the other."""

    nodes: frozenset = frozenset()
    edges: frozenset = frozenset()                 # (src, dst) — directed, and that is all it says
    attrs: Mapping[Node, Mapping[str, Any]] = field(default_factory=dict)
    degrees: Mapping[Node, Mapping[str, str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "attrs", _freeze(self.attrs))
        object.__setattr__(self, "degrees", _freeze(self.degrees))

    # -- construction: every one returns a new value and shares node identities ----------------

    def with_node(self, n: Node, **crisp: Any) -> "Graph":
        attrs = dict(self.attrs)
        if crisp:
            attrs[n] = {**attrs.get(n, {}), **crisp}
        return Graph(self.nodes | {n}, self.edges, attrs, self.degrees)

    def with_edge(self, src: Node, dst: Node) -> "Graph":
        return Graph(self.nodes | {src, dst}, self.edges | {(src, dst)}, self.attrs, self.degrees)

    def with_degree(self, n: Node, attr: str, band: str) -> "Graph":
        degrees = dict(self.degrees)
        degrees[n] = {**degrees.get(n, {}), attr: band}
        return Graph(self.nodes | {n}, self.edges, self.attrs, degrees)

    def merge(self, keep: Node, drop: Node) -> "Graph":
        """Replace `drop` with `keep` everywhere. **The application of a coreference decision, never the
        decision itself.**

        `cnl.md` §1 forbids the *boundary* from merging two nodes, because merging is where judgement
        lives. It does not forbid merging: it says a **rule** must be the one to decide, gradedly and
        revisably. So this is the mechanism a concluded `same-as` is applied through at write-back
        (§9), exactly as a concluded deletion is — and nothing calls it except that application.

        Degrees are combined with `meet`: two views of one thing are as strong as the weaker. Crisp
        attributes are unioned, `keep` winning a genuine conflict."""
        from .band import meet as _meet
        if keep is drop:
            return self
        m = lambda n: keep if n is drop else n              # noqa: E731

        attrs: dict = {}
        for n, a in self.attrs.items():
            t = m(n)
            base = attrs.get(t, {})
            # `keep`'s own attributes win a conflict, whatever order we met them in.
            attrs[t] = {**dict(a), **base} if n is drop else {**base, **dict(a)}
        degrees: dict = {}
        for n, dmap in self.degrees.items():
            t = m(n)
            cur = dict(degrees.get(t, {}))
            for k, v in dmap.items():
                cur[k] = _meet(cur.get(k), v)
            degrees[t] = cur

        return Graph(frozenset(m(n) for n in self.nodes),
                     frozenset((m(a), m(b)) for a, b in self.edges),
                     attrs, degrees)

    def without(self, n: Node, attr: str | None = None) -> "Graph":
        """Remove an attribute, or the node itself. **Write-back only.**

        Nothing inside a turn calls this: a computation unit's deletion is an *overlay* and hides while
        powered (`revision-02` §6). This is the other disposition — a mutating rule's deletion, applied
        to the asserted layer once stabilization is over, exactly as `model.md` §9 requires deletions to
        be proposals applied at the boundary rather than mutations the circuit performs."""
        if attr is not None:
            attrs = {k: dict(v) for k, v in self.attrs.items()}
            attrs.get(n, {}).pop(attr, None)
            return Graph(self.nodes, self.edges, attrs, self.degrees)
        return Graph(self.nodes - {n},
                     frozenset((a, b) for a, b in self.edges if a is not n and b is not n),
                     {k: v for k, v in self.attrs.items() if k is not n},
                     {k: v for k, v in self.degrees.items() if k is not n})

    def union(self, other: "Graph") -> "Graph":
        attrs = {**self.attrs}
        for n, a in other.attrs.items():
            attrs[n] = {**attrs.get(n, {}), **a}
        degrees = {**self.degrees}
        for n, d in other.degrees.items():
            degrees[n] = {**degrees.get(n, {}), **d}
        return Graph(self.nodes | other.nodes, self.edges | other.edges, attrs, degrees)

    # -- reads ---------------------------------------------------------------------------------

    def out(self, src: Node) -> tuple:
        return tuple(d for (s, d) in self.edges if s is src)

    def attr(self, n: Node, key: str) -> Any:
        return self.attrs.get(n, {}).get(key)

    def degree(self, n: Node, key: str) -> str | None:
        return self.degrees.get(n, {}).get(key)

    def __or__(self, other: "Graph") -> "Graph":
        return self.union(other)

    def __len__(self) -> int:
        return len(self.nodes)


EMPTY = Graph()


def occurrence(g: Graph, name: str, **roles: Node) -> tuple[Graph, Node]:
    """Build one relation the way §3 requires: an **occurrence node**, and each participant reached
    through a **fresh intermediate role node**.

    Role nodes are per-occurrence — *"exactly as two integer variables holding 7 are still two
    variables"* — so nothing is shared between two occurrences that happen to use the same role name.
    Arity is unbounded: another keyword is another node and two edges.

    This is a *convenience for building test data*, not a primitive. Note it cannot express *"Paul and
    Mary went"* (two `agent` roles) through keywords; `role_edge` is the general form."""
    occ = Node(name)
    g = g.with_node(occ, name=name)
    for role_name, filler in roles.items():
        g = role_edge(g, occ, role_name.replace("_", " "), filler)
    return g, occ


def role_edge(g: Graph, occ: Node, role_name: str, filler: Node) -> Graph:
    """One participant, through its own fresh role node. Call twice with the same `role_name` to get
    two distinct role nodes — which is how plurality is represented without a set node (§3)."""
    r = Node(role_name)
    g = g.with_node(r, name=role_name)
    return g.with_edge(occ, r).with_edge(r, filler)


def named(g: Graph, name: str, **crisp: Any) -> tuple[Graph, Node]:
    n = Node(name)
    return g.with_node(n, name=name, **crisp), n


__all__ = ["Node", "Graph", "EMPTY", "occurrence", "role_edge", "named"]
