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
        # -- labels ---------------------------------------------------------
        # A label is a NAME THAT PICKS OUT A NODE, and a node may have several.
        # Several labels on one node means those labels are aliases: `loves` and
        # `adores` name one relation, so `adores(x, z)` is `loves(x, z)` -- not
        # because the two build one node, but because every lookup widens to
        # the class the label merged them into (`counts_as`).
        #
        # This is what `_name` is NOT. `_name` is display -- a rule minted as
        # ninety characters of its own structure prints as `<boil>` -- and the
        # docstring on `name` says so: it cannot make two nodes one. A label
        # can, and that is the difference.
        #
        # Ordered, first attached first, because printing needs one canonical
        # answer and mint order is the tiebreak everywhere else in the engine.
        self._labels: Dict[NodeId, List[str]] = {}
        self._by_label: Dict[str, NodeId] = {}
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
        # The inverse: a representative, and everything that counts as it,
        # representative first.
        #
        # This is what replaced re-keying. While `rel` interned, a merge had to
        # MOVE every node whose key mentioned the merged one, because the key
        # was identity and two nodes could collapse onto one. Nothing interns
        # now, so a key is just the members as written and a merge moves
        # nothing: the indexes stay where they were and a LOOKUP widens to the
        # class instead. A merge is a dict write again.
        self._class: Dict[NodeId, List[NodeId]] = {}
        # One entry per `merge()` call, in order -- *a merge is a claim and the
        # chain is the record of the order the claims were made in*
        # (`identity_of`'s own docstring). This is what lets `unmerge` ask
        # *is this the top of the record* instead of guessing.
        self._merge_log: List[dict] = []

        # An index over what was asserted, not over what was derived (§16):
        # instances by relation. A rule whose antecedent names a relation has to
        # start somewhere, and scanning every node is the alternative.
        self._by_rel: Dict[NodeId, List[NodeId]] = {}
        # ...and a second, over the same instances by WHAT SITS IN EACH ARGUMENT
        # POSITION.
        # → docs/design/graph.md#and-a-third-over-the-same-instances-by-what
        self._by_arg: Dict[Tuple[NodeId, int, NodeId], List[NodeId]] = {}
        # ...and a third: every instance sharing one shape, mint order.
        #
        # Nothing interns the same proposition into one node any more, so
        # `p(a)` said twice is two nodes and this is the index that still calls
        # them the same proposition. Absence is the question that needs it:
        # `no p($x)` asks whether ANYTHING says `p(x)`, which is a question
        # about the shape and not about one of the nodes that has it.
        #
        # Keyed on the shape ALL THE WAY DOWN, not on the members as ids. One
        # level was enough while `rel` interned, because then a member id WAS
        # its shape: `raining(here)` was one node, so `arrived(user,
        # raining(here))` had one key. Rebuilt now, the inner node is a new id
        # and the outer key no longer matches -- which is `m.holds(kb.term(
        # "arrived(user, raining(here))"))` answering *no* about something
        # believed.
        self._by_key: Dict[Tuple, List[NodeId]] = {}
        # A node's shape, memoised: its own id if it is a leaf, and
        # `(shape of relation, shapes of members)` if it is not. Immutable for
        # `_has_var`'s reason -- what a node is made of is fixed when it is
        # built. Sub-shapes are shared tuples, so this is a pointer per node
        # rather than a copy of the structure.
        self._shape: Dict[NodeId, Tuple] = {}
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
        if not self._identity:
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

    def counts_as(self, n: NodeId) -> Tuple[NodeId, ...]:
        """Every node that counts as `n` does, `n`'s own representative first.

        The half of identity a LOOKUP needs. `identity_of` narrows -- many
        nodes to the one they stand for -- and every index here is keyed on the
        node as written, so narrowing alone would ask `_by_arg` about `paul`
        and miss the instance built off `paul-b`. This widens instead.

        A single-element tuple for anything nothing merged, which is every node
        in a corpus that never corefers, so the widening costs one dict get.
        """
        if not self._identity:
            return (n,)
        return tuple(self._class.get(self.identity_of(n), (n,)))

    def merge(self, keep: NodeId, drop: NodeId) -> int:
        """`drop` counts as `keep` from here on. Returns nodes repointed.

        One dict write, plus the labels. It used to be a cascade: while `rel`
        interned, the interning key was in IDENTITIES, so a merge could make
        two nodes collide onto one key and the engine had to decide which
        survived -- a decision it makes nowhere else. Nothing interns now, two
        nodes of one shape are two occasions, and there is nothing to collide.
        Congruence moved to the read side, where `counts_as` widens a lookup to
        the class and `unify` compares through `identity_of`.

        Returns 0: nothing moves any more. Kept as a return rather than dropped
        so a caller that measured the cascade sees it go to zero instead of
        seeing the call change shape.

        See docs/design/graph.md#merge.
        """
        keep, drop = self.identity_of(keep), self.identity_of(drop)
        if keep == drop:
            return 0
        self._identity[drop] = keep
        kin = self._class.setdefault(keep, [keep])
        for x in self._class.pop(drop, [drop]):
            if x not in kin:
                kin.append(x)
        # Labels follow identity: everything `drop` answered to, `keep` answers
        # to now. That is what makes two labels on one node aliases.
        moved_labels: List[str] = []
        for text in self._labels.pop(drop, ()):
            if text not in self._labels.setdefault(keep, []):
                self._labels[keep].append(text)
            self._by_label[text] = keep
            moved_labels.append(text)
        self._merge_log.append({"keep": keep, "drop": drop,
                                "labels": moved_labels})
        return 0

    def unmerge(self, keep: NodeId, drop: NodeId) -> int:
        """Undo `merge(keep, drop)`, if it is the record's own top.

        Reversible only when it is the MOST RECENT merge -- *a merge is a claim
        and the chain is the record of the order the claims were made in*
        (`identity_of`), so undoing anything but the top rests a later claim on
        a premise this call would remove.

        There is no longer a cascade to refuse: a merge collapses no other pair
        of nodes together, so the only thing to put back is the identity and
        the labels that travelled with it.

        Refuses loudly -- `ValueError`, naming which condition failed -- on
        the same argument as the loader's refusals: doing nothing silently
        and doing the wrong thing silently are both worse than stopping.
        """
        if not self._merge_log or (self._merge_log[-1]["keep"], self._merge_log[-1]["drop"]) != (keep, drop):
            top = self._merge_log[-1] if self._merge_log else None
            if top is None:
                raise ValueError("nothing has been merged")
            raise ValueError(
                f"can only unmerge the most recent merge, "
                f"merge({self.show(top['keep'])}, {self.show(top['drop'])}); "
                f"a later merge may rest on this one"
            )
        entry = self._merge_log.pop()
        for text in entry["labels"]:
            if text in self._labels.get(keep, ()):
                self._labels[keep].remove(text)
            self._labels.setdefault(drop, []).append(text)
            self._by_label[text] = drop
        del self._identity[drop]
        kin = self._class.get(keep)
        if kin is not None:
            back = [x for x in kin
                    if x == drop or self.identity_of(x) == drop]
            for x in back:
                kin.remove(x)
            if len(kin) <= 1:
                self._class.pop(keep, None)
            if len(back) > 1:
                self._class[drop] = back
        return 0

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
            self._drop_from_index(n, rel, members)
        self._shape.pop(n, None)
        for text in self._labels.pop(n, ()):
            if self._by_label.get(text) == n:
                del self._by_label[text]
        for d in (self._rel, self._members, self._name, self._is_var,
                  self._has_var, self._vars_in):
            d.pop(n, None)

    def _drop_from_index(self, n: NodeId, kr, km) -> None:
        """Take `n` out of every index it is in."""
        b = self._by_rel.get(kr)
        if b and n in b:
            b.remove(n)
        b = self._by_key.get(self._shape.get(n))
        if b and n in b:
            b.remove(n)
        for i, mm in enumerate(km):
            b = self._by_arg.get((kr, i, mm))
            if b and n in b:
                b.remove(n)

    # -- minting ----------------------------------------------------------

    # -- labels ---------------------------------------------------------------

    def label(self, n: NodeId, text: str) -> NodeId:
        """Give `n` the label `text`, and return what `text` now names.

        If nothing carried the label, `n` carries it. If another node did, the
        two are ALIASES and this merges them -- which is the whole content of
        *several labels on one node*, read from the other side.

        Irreversible without an unmerge, because it is a merge.
        """
        n = self.identity_of(n)
        if n not in self._labels and n in self._name and not self._is_var.get(n):
            #  The first label makes the node's existing name a label too, or
            # `labels_of` would report that a node called `loves` answers only
            # to `adores`. Seeded HERE and not at mint, so a corpus atom never
            # enters the table by being written -- only by being labelled.
            self._labels[n] = [self._name[n]]
            self._by_label.setdefault(self._name[n], n)
        held = self._by_label.get(text)
        if held is not None:
            held = self.identity_of(held)
            if held != n:
                #  The older node is kept, which is `merge`'s own rule for a
                # key collision: it is the one anything else already points at.
                lo, hi = (held, n) if held < n else (n, held)
                self.merge(lo, hi)
                return lo
            return n
        self._labels.setdefault(n, []).append(text)
        self._by_label[text] = n
        return n

    def unlabel(self, n: NodeId, text: str) -> bool:
        """Take a label off. Does NOT undo a merge the label caused: the nodes
        are already one, and only an unmerge could separate them."""
        n = self.identity_of(n)
        got = self._labels.get(n)
        if not got or text not in got:
            return False
        got.remove(text)
        if self._by_label.get(text) == n:
            del self._by_label[text]
        return True

    def labels_of(self, n: NodeId) -> Tuple[str, ...]:
        """Every label `n` answers to, first attached first."""
        return tuple(self._labels.get(self.identity_of(n), ()))

    def labelled(self, text: str) -> Optional[NodeId]:
        """What this label names, or None. The inverse of `label`."""
        got = self._by_label.get(text)
        return None if got is None else self.identity_of(got)

    def atom(self, name: str) -> NodeId:
        """A node with no relation and no members: an individual, or a relation
        to be used by others. Nothing structural tells the two apart, which is
        correct -- the difference is how they are used.

        **Deliberately NOT resolved through the label table.** Making this
        return the node that already carries the name was tried and reverted:
        it globally interns every atom by spelling, and the loader's per-corpus
        table exists on an argued position -- *two corpora may be about
        different kettles and are never about different 2s* (`text.py:823`).
        A name a corpus writes is local. A LABEL is a claim of identity, and it
        is made by calling `label`.

        Measured before reverting: on `delay.ugm` the change removed zero twins,
        because the loader's table was already doing the work.
        """
        return self._mint(None, (), name)

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
        """A relation instance: a distinct node every time it is built.

        This used to intern -- `on(a, b)` named one node however often it was
        written -- and interning was the substrate deciding that saying a thing
        twice is saying it once. That is a claim about occasions, and it is not
        the substrate's to make: an occasion is what attention is spent on, and
        two occasions cannot be told apart while structure is identity.

        So the write policy moved up. Whoever wants the node that is already
        there asks for it, with `find_rel`, and mints only when there is none
        -- which is what `Scratchpad.note` does to keep one anchor per belief,
        and what `Machine._note_that` does for the machinery's own record.
        """
        return self._mint(relation, tuple(members), None)

    def find_rel(self, relation: NodeId, *members: NodeId) -> Optional[NodeId]:
        """An instance with this shape if one exists, without creating one.

         `rel` cannot answer this: asking would build the thing asked about.
        That is harmless for a proposition and not harmless for the skeleton,
        where existing IS the fact.

        Answered from `_by_key` -- the index over EVERY instance sharing a key
        -- rather than from the intern table, which names one node per key and
        so answers *nothing has that shape* while a twin sits beside it. The
        two agree for anything only ever built through `rel`; they part where
        `instance` has minted.
        """
        got = self._same_shape(relation, tuple(members))
        return got[0] if got else None

    def like(self, n: NodeId) -> Tuple[NodeId, ...]:
        """Every instance sharing `n`'s key -- itself included, canonical first.

        `rel(on, a, b)` returns one node; `instance(on, a, b)` mints another.
        Both are `on(a, b)`. Anything asking a question about the PROPOSITION
        rather than about one entity has to ask it of all of them, and absence
        is that question.
        """
        rel = self._rel.get(n)
        if rel is None:
            return (n,)
        got = self._same_shape(rel, self._members[n])
        return got if got else (n,)

    def _same_shape(
        self, relation: Optional[NodeId], members: Tuple[NodeId, ...]
    ) -> Tuple[NodeId, ...]:
        """Every live node of this shape, mint order. One dict get, normally.

        With nothing merged the shape is the key and this is `_by_key` read
        straight. With something merged, one shape can have been written under
        any node of each leaf's class -- `loves(paul-b, mary)` IS `loves(paul,
        mary)` once the two names are one -- so the buckets to read are the
        product of the classes, `_shapes_of` below. That product is one entry
        wide until a merge touches a leaf the term uses, which is what makes
        the widening affordable: it is paid by the corpus that corefers.
        """
        key = (self.shape_of(relation), tuple(self.shape_of(m) for m in members))
        if not self._identity:
            return tuple(self._by_key.get(key, ()))
        out: List[NodeId] = []
        for k in self._shapes_of(relation, members):
            out.extend(self._by_key.get(k, ()))
        return tuple(sorted(set(out)))

    def _shapes_of(
        self, relation: Optional[NodeId], members: Tuple[NodeId, ...]
    ) -> List[Tuple]:
        """Every shape this term could have been written under, once identity
        is allowed to stand in at any leaf."""
        out: List[Tuple] = [()]
        for part in (relation,) + tuple(members):
            here = self._leaf_shapes(part)
            out = [k + (x,) for k in out for x in here]
        return [(k[0], k[1:]) for k in out]

    def _leaf_shapes(self, n: Optional[NodeId]) -> List:
        if n is None:
            return [None]
        rel = self._rel.get(n)
        if rel is None:
            return list(self.counts_as(n))
        return self._shapes_of(rel, self._members[n])

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
            self._shape[n] = shape = (self.shape_of(relation),
                                      tuple(self.shape_of(m) for m in members))
            self._by_rel.setdefault(relation, []).append(n)
            self._by_key.setdefault(shape, []).append(n)
            for i, mm in enumerate(members):
                self._by_arg.setdefault((relation, i, mm), []).append(n)
        return n

    def shape_of(self, n: NodeId) -> Tuple:
        """What `n` is made of, all the way down. Its own id if it is a leaf.

        Two nodes are the same PROPOSITION when their shapes are equal, which
        is the question `like`, `find_rel` and absence all ask. It was node
        identity while `rel` interned; it is this now.
        """
        got = self._shape.get(n)
        return n if got is None else got

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

        `.get(n, False)`, not `self._has_var[n]` -- `delete` clears this
        entry along with the rest, and `relation_of`'s own docstring is the
        rule every reader here has to keep: *dangling references can stay is
        only true if reading one answers rather than raises.* `destroy` in
        the RHS (`new_substrate.md`) is what found this raising: a rule that
        re-applies after destroying what it bound (nothing stops it, the
        same standing an unguarded MINTING rule has) grounds a binding to a
        now-deleted node and asked whether it still had a variable in it.
        """
        return self._has_var.get(n, False)

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
        derivation that ends in a tie breaks it the same way on every run.

        Widened to the relation's class, so a merge that made `adores` and
        `loves` one name reaches what was written under either. Mint order is
        node order, which is what makes the widened read still deterministic.
        """
        if not self._identity:
            return list(self._by_rel.get(relation, ()))
        kin = self.counts_as(relation)
        if len(kin) == 1:
            return list(self._by_rel.get(kin[0], ()))
        out: List[NodeId] = []
        for r in kin:
            out.extend(self._by_rel.get(r, ()))
        return sorted(set(out))

    def instances_with(self, relation: NodeId, pos: int, member: NodeId) -> List[NodeId]:
        """Every instance of a relation with this node in this argument position.
        The narrow form of `instances_of`, and the same guarantee: mint order.

        Widened for `instances_of`'s reason, over both the relation's class and
        the member's: `loves($a, mary)` has to reach the instance written as
        `loves(paul-b, mary)` once `paul-b` counts as `paul`.

         With nothing merged the list is the index's OWN and must not be
        mutated -- a caller that edited it would edit every later read.
        """
        if not self._identity:
            return self._by_arg.get((relation, pos, member), [])
        rk, mk = self.counts_as(relation), self.counts_as(member)
        if len(rk) == 1 and len(mk) == 1:
            return self._by_arg.get((rk[0], pos, mk[0]), [])
        out: List[NodeId] = []
        for r in rk:
            for x in mk:
                out.extend(self._by_arg.get((r, pos, x), ()))
        return sorted(set(out))

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
