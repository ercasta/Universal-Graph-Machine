"""The VALUE — what flows on a wire (`docs/design/substrate_inversion.md` §1, §5).

The inversion in one line: **the graph is not the store, it is the datum.** A `Subgraph` is an immutable
value produced by a unit and consumed by whoever the topology connects. There is no global graph, and
nothing in this package holds a registry of nodes or facts — see §1's falsifiable test.

TWO PROPERTIES ARE LOAD-BEARING, and only one of them is obvious.

**Immutability** is the obvious one: a unit may not mutate what it was handed, or the isolation that makes
this substrate work becomes a convention rather than a fact.

**IDENTITY INHERITANCE is the non-obvious one, and it is a CORRECTNESS requirement, not a cost trade-off**
(§5, spike case 2 in `bench/spike_substrate_inversion_binding.py`). A variable bound on one input wire must
join with the same variable on another, and what makes two occurrences THE SAME is node identity — never
the name. Two independently minted nodes both called `mary` are different things, and a join by name
fabricates a conclusion from them. So every operation here SHARES node objects rather than reconstructing
them: `union` shares, `without` shares, a fork shares. **A copy that re-mints nodes is not slow, it is
wrong**, which is why there is deliberately no `Node.copy`, no re-interning, and no lookup by name.

(The frozenset spine IS copied on each union — O(n) in the value's size. That is the known and accepted
perf shape for now: correctness first, per the project's standing rule. A HAMT would share the spine too,
and is the one optimization that would change nothing semantically. Recorded, not done.)
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Iterable, Iterator

_NID = itertools.count(1)


@dataclass(frozen=True)
class Node:
    """An entity. `nid` is IDENTITY; `name` is a LABEL and is never identity
    ([[node-identity-is-not-a-semantic-proxy]] — "the substrate is nameless").

    Minted once, at the unit that introduces it, and inherited unchanged through every downstream value.
    There is no `nodes_named` here and there will not be one: fusing two same-named nodes is exactly the
    name-luck failure this substrate is built to make unrepresentable."""
    nid: int
    name: str

    def __repr__(self) -> str:                      # `mary#7` — the id is visible on purpose
        return f"{self.name}#{self.nid}"


def mint(name: str = "") -> Node:
    """A FRESH node. Two calls with the same name give two DISTINCT nodes, deliberately."""
    return Node(next(_NID), name)


@dataclass(frozen=True)
class Fact:
    """A subject-predicate-object triple. The predicate is a string; subject and object are nodes — the
    S-P-O-as-a-directed-path commitment survives the inversion unchanged
    ([[spo-directed-path-no-labeled-edges]])."""
    s: Node
    p: str
    o: Node

    def __repr__(self) -> str:
        return f"{self.s} {self.p} {self.o}"


class Subgraph:
    """An immutable set of facts, with a per-predicate index built lazily.

    **The index is legitimate and is not a store.** §1's test forbids GLOBAL enumeration over data; this
    enumerates only within one bounded value that a unit was explicitly handed. That distinction is the
    whole architecture: a unit's reach is bounded by its in-degree (§2b), and `by_pred` cannot see past it.
    """
    __slots__ = ("_facts", "_index")

    def __init__(self, facts: Iterable[Fact] = ()) -> None:
        self._facts: frozenset = facts if isinstance(facts, frozenset) else frozenset(facts)
        self._index: dict | None = None

    # -- reads ---------------------------------------------------------------

    @property
    def facts(self) -> frozenset:
        return self._facts

    def by_pred(self, p: str) -> tuple:
        """Facts with predicate `p`. The bounded local index — the reason matching here is not a scan."""
        if self._index is None:
            idx: dict = {}
            for f in self._facts:
                idx.setdefault(f.p, []).append(f)
            self._index = {k: tuple(v) for k, v in idx.items()}
        return self._index.get(p, ())

    def predicates(self) -> frozenset:
        if self._index is None:
            self.by_pred("")                        # force the build
        return frozenset(self._index or ())

    # -- persistent updates: every one of these SHARES node and fact objects --

    def union(self, other: "Subgraph") -> "Subgraph":
        if not other._facts:
            return self
        if not self._facts:
            return other
        return Subgraph(self._facts | other._facts)

    def with_facts(self, facts: Iterable[Fact]) -> "Subgraph":
        add = frozenset(facts)
        return self if add <= self._facts else Subgraph(self._facts | add)

    def without(self, facts: Iterable[Fact]) -> "Subgraph":
        """REMOVAL, and it is required rather than incidental (§5): a delta must be able to override, or
        *"under H, not P"* against a base that holds P — most of what a hypothesis is for — cannot be
        expressed. Note this makes the value on a wire NON-MONOTONE while each unit stays a pure function,
        which is safe here only because nothing is shared: downstream recomputes, nothing is retracted."""
        drop = frozenset(facts)
        return self if not (drop & self._facts) else Subgraph(self._facts - drop)

    # -- protocol ------------------------------------------------------------

    def __or__(self, other: "Subgraph") -> "Subgraph":
        return self.union(other)

    def __iter__(self) -> Iterator[Fact]:
        return iter(self._facts)

    def __contains__(self, f: Fact) -> bool:
        return f in self._facts

    def __len__(self) -> int:
        return len(self._facts)

    def __bool__(self) -> bool:
        return bool(self._facts)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Subgraph) and self._facts == other._facts

    def __hash__(self) -> int:
        return hash(self._facts)

    def __repr__(self) -> str:
        return "{" + ", ".join(sorted(repr(f) for f in self._facts)) + "}"


EMPTY = Subgraph()
