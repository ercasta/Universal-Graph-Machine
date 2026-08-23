"""The substrate of §3: nodes, directed edges, ordered members. Nothing else.

Edges carry no information beyond connecting, so anything you want to say about
a connection has to be a node.

See docs/design/graph.md.
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
        #  Whether a node is generic, decided at MINT rather than on every
        # ask.
        # → docs/design/graph.md#whether-a-node-is-generic-decided-at-mint-r
        self._has_var: Dict[NodeId, bool] = {}
        self._next = 0

        #  Members that fell off the index, counted by the member as written
        # -- docs/interpretation-feedback.md §3.
        # → docs/design/graph.md#members-that-fell-off-the-index-counted-b
        self.scans: Dict[str, List[int]] = {}

        # -- identity (coreference) ----------------------------------
        # The third identity, and it is the one that can be decided LATE. 
        # Leaves only, and the default is the node itself.
        # → docs/design/graph.md#identity-coreference
        self._identity: Dict[NodeId, NodeId] = {}
        # The key each node is INDEXED under, so a merge knows what to move and
        # does not have to recompute the world to find out.
        self._keyed: Dict[NodeId, Tuple] = {}
        # `identity -> nodes whose key mentions it`. This is what
        # makes a merge cost the upward CLOSURE of the merged things rather than
        # a scan of the graph -- and the closure is the number that decides
        # whether this is affordable.
        self._mentions: Dict[NodeId, List[NodeId]] = {}
        # Whether ANY merge has happened in this graph. The fast path is a
        # single boolean test rather than a dict get per member per `rel`, and
        # `rel` is the hottest call in the engine.
        self._merges = 0

        # One index, over what was asserted rather than over what was derived
        # (§12): relation instances keyed by (rel, members) so the same
        # proposition is one node however often it is spoken of.
        self._interned: Dict[
            Tuple[Optional[NodeId], Tuple[NodeId, ...]], NodeId
        ] = {}
        # A second index over what was asserted, not over what was derived (§16):
        # instances by relation. A rule whose antecedent names a relation has to
        # start somewhere, and scanning every node is the alternative.
        self._by_rel: Dict[NodeId, List[NodeId]] = {}
        # ...and a third, over the same instances by WHAT SITS IN EACH ARGUMENT
        # POSITION.
        # → docs/design/graph.md#and-a-third-over-the-same-instances-by-what
        self._by_arg: Dict[Tuple[NodeId, int, NodeId], List[NodeId]] = {}
        # Which variables are in a node, memoised. Immutable for `_has_var`'s
        # reason -- a node's relation and members are fixed when it is built.
        #  It lives HERE and not beside its one reader, because a node id means
        # nothing outside the graph that minted it: a module-level cache keyed
        # on the id answered a second machine's question with the first
        # machine's node, and the suite reported a corpus rule as concluding
        # about a variable nothing binds.
        self._vars_in: Dict[NodeId, set] = {}

    def identity_of(self, n: NodeId) -> NodeId:
        """What `n` counts as -- itself, unless something merged it.

        Follows chains: merging `b` into `a` and then `a` into `c` leaves `b`
        pointing at `a`, so this walks to the representative. No path
        compression, because a merge is a claim and the chain is the record of
        the order the claims were made in.
        """
        if not self._merges:
            return n
        seen = 0
        while True:
            got = self._identity.get(n)
            if got is None or got == n:
                return n
            n = got
            seen += 1
            if seen > len(self._identity):  # a cycle nothing should be able to build
                return n

    def _key(self, relation: Optional[NodeId], members: Tuple[NodeId, ...]):
        """The interning key, in identities rather than in nodes.

        With no merge anywhere this is the members tuple itself, so the key is
        the one the engine used before identity existed and the dict lookup is
        unchanged. That equality is what makes this free for every corpus that
        never corefers, and it is checked rather than asserted.
        """
        if not self._merges:
            return relation, members
        return (
            None if relation is None else self.identity_of(relation),
            tuple(self.identity_of(m) for m in members),
        )


    def merge(self, keep: NodeId, drop: NodeId) -> int:
        """`drop` counts as `keep` from here on. Returns nodes repointed.

        Congruence, and it is why this cannot be two dict writes. Without
        the repoint, everything said before the merge is LOST.

        See docs/design/graph.md#merge.
        """
        self._index_for_merge()
        moved = 0
        work = [(keep, drop)]
        while work:
            x, y = work.pop()
            if x == y:
                continue
            self._identity[y] = x
            self._merges += 1
            # Everything whose key mentioned `y` now keys on `x` instead.
            for n in list(self._mentions.get(y, ())):
                old = self._keyed.get(n)
                if old is None:
                    continue
                kr, km = self._key(self._rel[n], self._members[n])
                if (kr, km) == old:
                    continue
                okr, okm = old
                self._drop_from_index(n, okr, okm)
                already = self._interned.get((kr, km))
                if already is not None and already != n:
                    # Two nodes have collapsed onto one key. The older one wins,
                    # for the reason mint order always wins here: it is the one
                    # anything else already points at.
                    lo, hi = (already, n) if already < n else (n, already)
                    work.append((lo, hi))
                else:
                    self._interned[(kr, km)] = n
                    self._by_rel.setdefault(kr, []).append(n)
                    for i, mm in enumerate(km):
                        self._by_arg.setdefault((kr, i, mm), []).append(n)
                    self._keyed[n] = (kr, km)
                    for c in (kr,) + tuple(km):
                        self._mentions.setdefault(c, []).append(n)
                moved += 1
        return moved

    def _index_for_merge(self) -> None:
        """Build `_keyed` and `_mentions`, once, at the first merge.

        Everything a merge needs to find is derivable from what is already
        stored, so the choice is *maintain it always* or *build it when it is
        first wanted*. Maintaining it always taxed every corpus that never
        corefers; this pays O(nodes) once, for the corpus that does.
        """
        if self._keyed:
            return
        for n, r in self._rel.items():
            if r is None:
                continue
            kr, km = self._key(r, self._members[n])
            self._keyed[n] = (kr, km)
            for x in (kr,) + tuple(km):
                self._mentions.setdefault(x, []).append(n)

    def delete(self, n: NodeId) -> None:
        """Take `n` out of the graph. The scratchpad's erase.

        Note: this does no repoint and no cascade.
        `merge` had to repoint -- *without it, everything said before the merge
        is LOST* -- because a merged node still means something. A deleted one
        does not. Anything still naming `n` is left dangling on the argument
        that **no rule matches an incomplete subgraph**: a premise that needs
        `n` fails to bind, so the dangling half is unreachable rather than
        wrong. `probes/erase.py` is that argument, measured.

        Structure only. What makes a proposition BELIEVED is an anchor node --
        `believed(p)` -- so retracting a belief is deleting the anchor and never
        the proposition, which rules mention and must keep.
        """
        rel, members = self._rel.get(n), self._members.get(n, ())
        if rel is not None:
            kr, km = ((rel, members) if not self._merges
                      else self._key(rel, members))
            self._drop_from_index(n, kr, km)
            self._keyed.pop(n, None)
        for d in (self._rel, self._members, self._name, self._is_var,
                  self._has_var, self._vars_in):
            d.pop(n, None)

    def _drop_from_index(self, n: NodeId, kr, km) -> None:
        """Take `n` out of every index it is in under `(kr, km)`."""
        if self._interned.get((kr, km)) == n:
            del self._interned[(kr, km)]
        b = self._by_rel.get(kr)
        if b and n in b:
            b.remove(n)
        for i, mm in enumerate(km):
            b = self._by_arg.get((kr, i, mm))
            if b and n in b:
                b.remove(n)

    # -- minting ----------------------------------------------------------

    def atom(self, name: str) -> NodeId:
        """A node with no relation and no members: an individual, or a relation
        to be used by others. Nothing structural tells the two apart, which is
        correct -- the difference is how they are used."""
        n = self._mint(None, (), name)
        return n

    def entity(self) -> NodeId:
        """A labelless node: nothing but an id.

        An entity is characterized by its id alone -- any name it answers to
        is a claim about it (`named(e, paul)`), never part of it, so there is
        nothing to pass here. The same mint a consequent's `+kind` marker
        performs, made public so anything coming into the world from Python
        comes in the same way a rule brings it in."""
        return self._mint(None, (), None)

    def var(self, name: str) -> NodeId:
        """A variable, for the generic moments of a rule (§4)."""
        n = self._mint(None, (), name)
        self._is_var[n] = True
        #  Both, and this is the one place they can disagree: `_mint` decides
        # genericity from the relation and members, which a bare variable has
        # none of, so it would record False. A variable IS the generic thing.
        self._has_var[n] = True
        return n

    def rel(self, relation: NodeId, *members: NodeId) -> NodeId:
        """A relation instance, interned: `on(a, b)` names one node however many
        times it is built."""
        members = tuple(members)
        found = self._interned_lookup(relation, members)
        if found is not None:
            return found
        n = self._mint(relation, members, None)
        if self._merges:
            relation, members = self._key(relation, members)
        self._interned[(relation, members)] = n
        return n

    def find_rel(self, relation: NodeId, *members: NodeId) -> Optional[NodeId]:
        """The interned instance if it exists, without creating one.

         `rel` cannot answer this: asking would build the thing asked about.
        That is harmless for a proposition and not harmless for the skeleton,
        where existing IS the fact -- so §6's quiescence needs a question it can
        put without answering it. See `rules.already_there`.
        """
        return self._interned_lookup(relation, tuple(members))

    def _interned_lookup(
        self, relation: Optional[NodeId], members: Tuple[NodeId, ...]
    ) -> Optional[NodeId]:
        """The interned node for this key, or None. One dict get."""
        if self._merges:
            relation, members = self._key(relation, members)
        return self._interned.get((relation, members))

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
        self, relation: Optional[NodeId], members: Tuple[NodeId, ...],
        name: Optional[str],
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
            kr, km = ((relation, members) if not self._merges
                      else self._key(relation, members))
            self._by_rel.setdefault(kr, []).append(n)
            for i, mm in enumerate(km):
                self._by_arg.setdefault((kr, i, mm), []).append(n)
            #  **Only once something has merged.** Maintaining these at
            # every mint cost the suite 9% -- 8.25s to 9.01s -- for corpora that
            # never corefer and never will, which is the one thing this layer
            # promised not to do. They are built by a single scan at the first
            # merge instead (`_index_for_merge`), and maintained from then on.
            # Measured rather than reasoned about: the fast path in `_key` was
            # already free, and this was the half that was not.
            if self._merges:
                self._keyed[n] = (kr, km)
                for x in (kr,) + tuple(km):
                    self._mentions.setdefault(x, []).append(n)
        return n

    # -- reading ----------------------------------------------------------

    def relation_of(self, n: NodeId) -> Optional[NodeId]:
        """ Tolerant of a DELETED node, and it has to be. `probes/erase`
        measured the alternative: erasing a proposition still named by an entry
        raised `KeyError` out of `Situation._keys`, because the state walk reads
        the relation of every entry it indexes. *Dangling references can stay*
        is only true if reading one answers rather than raises."""
        return self._rel.get(n)

    def members(self, n: NodeId) -> Tuple[NodeId, ...]:
        return self._members.get(n, ())

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
        The narrow form of `instances_of`, and the same guarantee: mint order.

         The list is the index's OWN and must not be mutated -- a caller that
        edited it would edit every later read.
        """
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
        if n not in self._rel:
            return f"#{n}(erased)"   # a dangling reference, printed as one
        r = self._rel[n]
        if r is None:
            return f"#{n}"
        inner = ", ".join(self.show(m) for m in self._members[n])
        return f"{self.show(r)}({inner})"
