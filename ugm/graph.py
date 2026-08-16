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
        # ⭐⭐⭐ Whether a node is generic, decided at MINT rather than on every
        # ask. It cannot change: a node's relation and members are fixed when it
        # is built, so *contains a variable somewhere* is fixed with them.
        #
        # Profiled, and it was not a small share: `has_var` was **91% of the
        # rule-level read** -- 7.6M calls recursing the whole structure each
        # time, because the structural generators ask it of every instance in a
        # bucket on every enumeration. Computing it here is O(arity) once
        # instead of O(size) per question.
        self._has_var: Dict[NodeId, bool] = {}
        self._next = 0
        # One index, over what was asserted rather than over what was derived
        # (§12): relation instances keyed by (rel, members) so the same
        # proposition is one node however often it is spoken of.
        self._interned: Dict[Tuple[Optional[NodeId], Tuple[NodeId, ...]], NodeId] = {}
        # A second index over what was asserted, not over what was derived (§16):
        # instances by relation. A rule whose antecedent names a relation has to
        # start somewhere, and scanning every node is the alternative.
        self._by_rel: Dict[NodeId, List[NodeId]] = {}
        # ...and a third, over the same instances by WHAT SITS IN EACH ARGUMENT
        # POSITION. `_by_rel` answers *every `delta_next`*; this answers *every
        # `delta_next` whose first argument is this entry*, which is what a
        # matcher with one argument already bound actually wants.
        #
        # The entry side took this index once already -- an option set weighed
        # by scanning was 2,006,004 unifications and 3,003 after -- and the
        # structural side never did, because until §7 stopped hiding two thirds
        # of the chain from the matcher there was nothing here big enough to
        # notice. Profiled the hour it became visible: `cand` went 193 -> 2,062
        # in one fixture, and `<beaten-locus>` joining `cand` against `cand` by
        # scanning was 4.4M unifications in 60 seconds, which is 2,062 squared.
        #
        # Insertion-ordered like the others, so nothing downstream inherits a
        # tie-break from a hash.
        self._by_arg: Dict[Tuple[NodeId, int, NodeId], List[NodeId]] = {}
        # Which variables are in a node, memoised. Immutable for `_has_var`'s
        # reason -- a node's relation and members are fixed when it is built.
        # ⚠ It lives HERE and not beside its one reader, because a node id means
        # nothing outside the graph that minted it: a module-level cache keyed
        # on the id answered a second machine's question with the first
        # machine's node, and the suite reported a corpus rule as concluding
        # about a variable nothing binds.
        self._vars_in: Dict[NodeId, set] = {}

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
        # ⚠ Both, and this is the one place they can disagree: `_mint` decides
        # genericity from the relation and members, which a bare variable has
        # none of, so it would record False. A variable IS the generic thing.
        self._has_var[n] = True
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

    def find_rel(self, relation: NodeId, *members: NodeId) -> Optional[NodeId]:
        """The interned instance if it exists, without creating one.

        ⚠ `rel` cannot answer this: asking would build the thing asked about.
        That is harmless for a proposition and not harmless for the skeleton,
        where existing IS the fact -- so §6's quiescence needs a question it can
        put without answering it. See `rules.already_there`.
        """
        return self._interned.get((relation, tuple(members)))

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
        # Every constituent is already minted, so its answer is already here.
        self._has_var[n] = (
            (relation is not None and self._has_var.get(relation, False))
            or any(self._has_var.get(mm, False) for mm in members)
        )
        if name is not None:
            self._name[n] = name
        if relation is not None:
            self._by_rel.setdefault(relation, []).append(n)
            for i, mm in enumerate(members):
                self._by_arg.setdefault((relation, i, mm), []).append(n)
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
        """Whether a structure is generic -- contains a variable anywhere (§4).

        Decided at mint (see `_has_var`); this is the lookup. The recursive
        definition it replaces is kept as `_has_var_slow`, and `ugm.selftest`
        holds the two to each other over every node the suite builds -- an index
        is a re-implementation of what it indexes, which is the lesson `state`
        paid for once already.
        """
        return self._has_var[n]

    def _has_var_slow(self, n: NodeId) -> bool:
        """The definition, walked. Not used by the engine; kept so the cached
        answer has something to be wrong against."""
        if self.is_var(n):
            return True
        r = self._rel[n]
        if r is not None and self._has_var_slow(r):
            return True
        return any(self._has_var_slow(m) for m in self._members[n])

    def instances_of(self, relation: NodeId) -> List[NodeId]:
        """Every instance of a relation, in mint order. Insertion-ordered, so a
        derivation that ends in a tie breaks it the same way on every run."""
        return list(self._by_rel.get(relation, ()))

    def instances_with(self, relation: NodeId, pos: int, member: NodeId) -> List[NodeId]:
        """Every instance of a relation with this node in this argument position.
        The narrow form of `instances_of`, and the same guarantee: mint order."""
        return self._by_arg.get((relation, pos, member), [])

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
