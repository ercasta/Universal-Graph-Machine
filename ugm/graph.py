"""The substrate of §3: nodes, directed edges, ordered members. Nothing else.

Edges carry no information beyond connecting, so anything you want to say about a
connection has to be a node. A relation instance -- what would elsewhere be a
labelled edge -- is therefore a node with a relation and ordered members:

    on(a, b)        a node whose relation is `on` and whose members are a, b

Ordering is the one thing that is not itself structure (§3), which is why the
substrate provides it natively and provides nothing else.

Determinism: no derived result is ever read out of a set. Membership, minting
order and every iteration below are insertion-ordered, so a computation that ends
in a tie breaks it the same way on every run.
"""

from typing import Dict, List, Optional, Tuple

NodeId = int


class Graph:
    """Nodes with ordered members. Names are for printing and never for identity."""

    def __init__(self) -> None:
        self._rel: Dict[NodeId, Optional[NodeId]] = {}
        self._members: Dict[NodeId, Tuple[NodeId, ...]] = {}
        self._name: Dict[NodeId, str] = {}
        self._is_var: Dict[NodeId, bool] = {}
        self._next = 0
        # One index, over what was asserted rather than over what was derived
        # (§12): relation instances keyed by (rel, members) so the same
        # proposition is one node however often it is spoken of.
        self._interned: Dict[Tuple[Optional[NodeId], Tuple[NodeId, ...]], NodeId] = {}
        # A second index over what was asserted, not over what was derived (§16):
        # instances by relation. A rule whose antecedent names a relation has to
        # start somewhere, and scanning every node is the alternative.
        self._by_rel: Dict[NodeId, List[NodeId]] = {}

    # -- minting ----------------------------------------------------------

    def atom(self, name: str) -> NodeId:
        """A node with no relation and no members: an individual, or a relation
        to be used by others. Nothing structural tells the two apart, which is
        correct -- the difference is how they are used."""
        n = self._mint(None, (), name)
        return n

    def var(self, name: str) -> NodeId:
        """A variable, for the generic moments of a rule (§4)."""
        n = self._mint(None, (), name)
        self._is_var[n] = True
        return n

    def rel(self, relation: NodeId, *members: NodeId) -> NodeId:
        """A relation instance. Interned: `on(a, b)` names one node however many
        times it is built, so a proposition has one identity to be claimed about."""
        key = (relation, tuple(members))
        if key in self._interned:
            return self._interned[key]
        n = self._mint(relation, tuple(members), None)
        self._interned[key] = n
        return n

    def instance(self, relation: NodeId, *members: NodeId) -> NodeId:
        """A relation instance that is *not* interned: a distinct node every time.

        Propositions intern, because `on(a, b)` is one idea however often it is
        spoken. Entries must not, because an entry is an act of claiming -- two
        claims about the same proposition at the same locus are two events, and
        §5 needs each to be a node other facts can be about. Interning them would
        make `mistaken(<e>)` land on both at once.
        """
        return self._mint(relation, tuple(members), None)

    def _mint(
        self, relation: Optional[NodeId], members: Tuple[NodeId, ...], name: Optional[str]
    ) -> NodeId:
        n = self._next
        self._next += 1
        self._rel[n] = relation
        self._members[n] = members
        self._is_var[n] = False
        if name is not None:
            self._name[n] = name
        if relation is not None:
            self._by_rel.setdefault(relation, []).append(n)
        return n

    # -- reading ----------------------------------------------------------

    def relation_of(self, n: NodeId) -> Optional[NodeId]:
        return self._rel[n]

    def members(self, n: NodeId) -> Tuple[NodeId, ...]:
        return self._members[n]

    def member(self, n: NodeId, i: int) -> NodeId:
        return self._members[n][i]

    def is_var(self, n: NodeId) -> bool:
        return self._is_var.get(n, False)

    def has_var(self, n: NodeId) -> bool:
        """Whether a structure is generic -- contains a variable anywhere (§4)."""
        if self.is_var(n):
            return True
        r = self._rel[n]
        if r is not None and self.has_var(r):
            return True
        return any(self.has_var(m) for m in self._members[n])

    def instances_of(self, relation: NodeId) -> List[NodeId]:
        """Every instance of a relation, in mint order. Insertion-ordered, so a
        derivation that ends in a tie breaks it the same way on every run."""
        return list(self._by_rel.get(relation, ()))

    def count(self) -> int:
        return self._next

    # -- printing ---------------------------------------------------------

    def call_it(self, n: NodeId, text: str) -> NodeId:
        """Give an existing node a name, for printing only.

        Names are never identity here (that is the whole of §3's second
        paragraph), so this cannot make two nodes one or tell two apart. What it
        is for is that a rule is minted as `implies(moment(...), moment(...))`
        and prints as ninety characters of its own structure -- in every plan
        node, every licence, every `unmet`. The author called it `<boil>`; there
        was simply nowhere to put that.
        """
        self._name[n] = text
        return n

    def show(self, n: NodeId) -> str:
        if n in self._name:
            return self._name[n]
        r = self._rel[n]
        if r is None:
            return f"#{n}"
        inner = ", ".join(self.show(m) for m in self._members[n])
        return f"{self.show(r)}({inner})"
