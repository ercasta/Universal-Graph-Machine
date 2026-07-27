"""OVERLAYS — `docs/units/revision-02-two-planes.md` §6.

A spike, deliberately separate from `standing.py`, which implements revision 01 and carries the design
error this module exists to correct.

## The claim

A unit's output is **not a graph**. It is an **overlay**: a revertable mutation applied to the one graph
— mint a node, add an edge, set an attribute, identify two nodes. Nothing is materialized; a read
consults the live overlays and composes the answer.

## What went wrong in `standing.py`, and why it is the type's fault

`Value` carries `graph: Graph` **and** `merges: tuple` beside it. `Merge` could not be expressed as a
fragment — it rewrites every mention of a node, anywhere — so it was carried out of band and re-applied
at read time in `Network._assemble`. **One effect type not fitting the container is the container being
wrong.** Here all four effects are the same kind of thing and there is no side channel.

## Two constraints this module is built to keep

**A read returns a set, never a winner** (invariant 16). Two live overlays disagreeing about one
attribute are two *readings*. Collapsing them is CSS's cascade — a precedence policy hardcoded in the
engine, which `model.md` §11 says must stay authored. `read()` returns a list and never sorts it.

**Applying an attribute overlay must never write the attribute** (`revision-01` §9's design-changing
finding). `Graph.union` merges attrs by node, so two live derivations disagreeing about one
`(node, attr)` collapsed silently, and the contradiction vanished exactly when it mattered. A `SetAttr`
applies as a **reified attribution node**. Keeping that here is what lets one graph hold *"a man under
H1, a woman under H2"*.

## The number this module exists to produce

`Identify` is the case that decides whether lazy application is affordable. Mint, edge and attribute
overlays are local, so a read consults a small set; an identification rewrites every mention, so *every*
read — including every read the matcher does, which is most of the inner loop — must resolve identity as
it goes. See `bench_overlay.py`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from .graph import EMPTY, Graph, Node

ATTRIBUTION = "attribution"
BASE = "<base>"


# -- the four effects. All of them mutate the one graph; none of them is a fragment. -------------

@dataclass(frozen=True)
class Mint:
    """Bring a node into being, with crisp attributes. The only effect that creates identity."""

    node: Node
    attrs: tuple = ()                       # ((key, value), …)


@dataclass(frozen=True)
class AddEdge:
    src: Node
    dst: Node


@dataclass(frozen=True)
class SetAttr:
    """Derive an attribute onto a node that lives elsewhere.

    ⚠ Applies as a **reified attribution**, never as a write — see the module docstring. The target is
    untouched wherever it actually lives, so *"Paul is 43"* from a birthday rule stands beside the
    asserted *"Paul is 42"* rather than overwriting it."""

    target: Node
    attr: str
    value: Any


@dataclass(frozen=True)
class Identify:
    """Two nodes are one thing — the **applied** coreference decision.

    This is the effect that proves an overlay is a mutation rather than a fragment: minting, edges and
    attributes can all be described locally, and this cannot. It is still revertable for the ordinary
    reason: it is re-applied from the axioms on every revive, so an identification whose unit loses
    power simply is not made again. Nothing is ever un-merged.

    ⚠ The *decision* is a rule's (`cnl.md` §1, create-never-merge). This is only its application."""

    keep: Node
    drop: Node


EFFECTS = (Mint, AddEdge, SetAttr, Identify)


@dataclass(frozen=True)
class Reading:
    """One live answer, and what is keeping it alive.

    There is never a single answer to collapse to. `source` is the unit whose overlay produced it, or
    `BASE` for asserted data — which is provenance arriving free, since the overlay set *is* the
    derivation."""

    value: Any
    source: str

    def __repr__(self) -> str:
        return f"{self.value!r}@{self.source}"


class Overlays:
    """A base graph plus the live overlays, read lazily.

    The index is built once per revive and thrown away with the values — it holds nothing across a
    revive that the effects do not describe (invariant 18). Reads are then O(1) lookups plus identity
    resolution, which is the whole cost question.
    """

    __slots__ = ("base", "effects", "_parent", "_members", "_edges", "_attribs", "_minted")

    def __init__(self, base: Graph = EMPTY, effects: Sequence[tuple] = ()) -> None:
        self.base = base
        self.effects = list(effects)            # (source, effect)
        self.reindex()

    # -- indexing: once per revive ---------------------------------------------------------------

    def reindex(self) -> None:
        """Two passes, and the order matters.

        Identity first, because everything else is indexed **by resolved node** — that is what keeps a
        read from having to walk the equivalence class. Doing it the other way round means every read
        pays for the merge; doing it this way means only the index does.
        """
        self._parent: dict = {}
        touched: list = []
        for _, e in self.effects:
            if isinstance(e, Identify):
                self._union(e.keep, e.drop)
                touched.extend((e.keep, e.drop))

        # ⚠ The root belongs to its own class. Building this from `_parent`'s keys alone omits it, and
        # a read then silently loses the surviving node's *own* asserted attributes — found by
        # `test_a_read_gathers_across_an_identification`, and exactly the quiet-degradation class
        # `STATUS.md` records seven of.
        self._members: dict = {}
        for n in touched:
            members = self._members.setdefault(self._find(n), [])
            if n not in members:
                members.append(n)

        self._edges: dict = {}
        self._attribs: dict = {}
        self._minted: list = []
        for src, e in self.effects:
            if isinstance(e, AddEdge):
                self._edges.setdefault(self._find(e.src), []).append((self._find(e.dst), src))
            elif isinstance(e, SetAttr):
                self._attribs.setdefault(self._find(e.target), []).append((e.attr, e.value, src))
            elif isinstance(e, Mint):
                self._minted.append((e, src))
            elif not isinstance(e, Identify):
                raise TypeError(f"unknown effect {e!r}")

    def _union(self, keep: Node, drop: Node) -> None:
        a, b = self._find(keep), self._find(drop)
        if a is not b:
            self._parent[b] = a                 # `keep` wins, so resolution is stable and authored

    def _find(self, n: Node) -> Node:
        p = self._parent.get(n)
        if p is None:
            return n
        root = self._find(p)
        self._parent[n] = root                  # path compression
        return root

    # -- the read path ---------------------------------------------------------------------------

    def resolve(self, n: Node) -> Node:
        """Which node this one turned out to be. Identity is plumbing (`model.md` §11) and this is where
        it is paid for."""
        return self._find(n)

    def _raw(self, n: Node) -> Iterable[Node]:
        """Every node that resolves to `n` — what a read has to gather over."""
        return self._members.get(n, (n,))

    def read(self, n: Node, key: str) -> list:
        """**Every** live value for `n.key`, with what keeps each alive.

        Returns a list and never picks. Two live overlays disagreeing about one attribute are two
        readings — *"a man under H1, a woman under H2"* — and telling that from *"a man and a woman"* is
        a rule's judgement, never the engine's (invariant 16)."""
        n = self._find(n)
        out: list = []
        for raw in self._raw(n):
            v = self.base.attr(raw, key)
            if v is not None:
                out.append(Reading(v, BASE))
        for attr, value, src in self._attribs.get(n, ()):
            if attr == key:
                out.append(Reading(value, src))
        for minted, src in self._minted:
            if self._find(minted.node) is n:
                for k, v in minted.attrs:
                    if k == key:
                        out.append(Reading(v, src))
        return out

    def out(self, n: Node) -> tuple:
        """Outgoing neighbours, resolved. Base edges and overlay edges are the same thing here."""
        n = self._find(n)
        seen: list = []
        for raw in self._raw(n):
            for d in self.base.out(raw):
                d = self._find(d)
                if d not in seen:
                    seen.append(d)
        for d, _ in self._edges.get(n, ()):
            if d not in seen:
                seen.append(d)
        return tuple(seen)

    def nodes(self) -> tuple:
        seen: list = []
        for n in list(self.base.nodes) + [m.node for m, _ in self._minted]:
            r = self._find(n)
            if r not in seen:
                seen.append(r)
        return tuple(seen)

    # -- comparison only: the eager path ---------------------------------------------------------

    def materialize(self) -> Graph:
        """Apply everything and hand back a `Graph`.

        Here **for the benchmark and for nothing else.** It is what lazy application is being compared
        against, and its cost is the argument: materializing rebuilds the whole graph including the
        untouched base, so it scales with the *twin* where a lazy read scales with the *overlays*. Under
        `revision-01` a revive is already O(circuit); making it O(twin) as well is the thing to avoid."""
        g = self.base
        for _, e in self.effects:
            if isinstance(e, Mint):
                g = g.with_node(e.node, **dict(e.attrs))
            elif isinstance(e, AddEdge):
                g = g.with_edge(e.src, e.dst)
            elif isinstance(e, SetAttr):
                a = Node(f"{e.attr}={e.value}")
                g = g.with_node(a, name=ATTRIBUTION, attr=e.attr, value=e.value)
                r = Node("of")
                g = g.with_node(r, name="of").with_edge(a, r).with_edge(r, e.target)
            elif isinstance(e, Identify):
                g = g.merge(e.keep, e.drop)
        return g


__all__ = ["Mint", "AddEdge", "SetAttr", "Identify", "Overlays", "Reading",
           "EFFECTS", "ATTRIBUTION", "BASE"]
