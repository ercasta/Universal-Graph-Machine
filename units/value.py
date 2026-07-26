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
    """A subject-predicate-object triple in which **ALL THREE SLOTS ARE NODES** (§22.3, §22.5).

    The predicate is a ROLE NODE, not a string — the same kind of thing as its endpoints, which is what makes
    `?s ?p ?o` expressible with no new primitive.

    **⚠ BE PRECISE ABOUT WHAT THIS IS** (§32). A `Fact` is stored ATOMICALLY, not as two adjacency links
    through an intermediate node — so in LAYOUT it is a labelled edge, and an earlier version of this docstring
    claiming *"S-P-O as a directed path survives unchanged"* was too generous. What actually survives is
    everything [[spo-directed-path-no-labeled-edges]] was about:

    * roles are carried by POSITION, not by labels — `s` and `o` are told apart by where they sit;
    * the predicate is an ordinary node, so there is no separate label namespace and `?p` is a plain variable;
    * nothing hangs role-labelled edges on a fact about the world.

    **The atomic layout is a deliberate trade, made once, for DECIDABILITY:** a fact is a single set member, so
    `Absent` is a membership test — exact, immediate, no fuel (§6a). As a traversable 2-path, *"is P absent"*
    becomes *"is there no 2-path"*, which is a join, and the cheap exact negation the whole design rests on
    would be gone. Value equality and hashing are trivial for the same reason, and the fixpoint depends on it.

    **And the exception ships with its decomposition:** the inside of a fact is reachable as ordinary facts via
    `reify` (`<of_s>/<of_p>/<of_o>`) whenever something needs to compose with it. That escape hatch is what
    keeps this from being the unreachable island a superstructure otherwise creates (§32).

    A `str` is resolved through the default form set at construction (`vocab.role`), so call sites read
    the same; **where that resolution is allowed to happen is the whole discipline**, and `vocab` states
    it: a form may mint a role, an utterance may not."""
    s: Node
    p: Node
    o: Node

    def __post_init__(self) -> None:
        if not isinstance(self.p, Node):
            from .vocab import role
            object.__setattr__(self, "p", role(self.p))

    def __repr__(self) -> str:
        return f"{self.s} {self.p.name} {self.o}"


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

    def by_pred(self, p) -> tuple:
        """Facts with role `p` — a role node, or a name resolved through the form set. The bounded local
        index, and note it stays CRISP under §22.3: a role is an IDENTITY, so this is still a dict lookup
        and not a similarity search. §22.5 measured that the five predicate-keyed mechanisms go graded
        only when similarity matching arrives, which is a separate decision."""
        if not isinstance(p, Node) and p is not None:
            from .vocab import role
            p = role(p)
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
        """OMISSION — what a REWRITE does when its output does not carry an input fact forward (§21.1).
        It is required rather than incidental (§5): without it,
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
