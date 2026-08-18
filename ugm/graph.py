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

⭐⭐⭐ **And a node has two identities (`docs/situations.md`).**

    node id     the realisation of a thing INSIDE one situation
    atom id     the portable name of that thing, ACROSS situations

The defect this exists to fix is that containment held for entries and failed for
structure. An entry carries a locus, so it is situation-relative by construction;
a stratum-0 conclusion was an interned relation instance -- undated, unattributed,
deniable by nothing -- so it belonged to no situation and was visible from every
one. Probed, on a supposition concluding an ordinary fact inside itself:

    is secret(a) BELIEVED at the root?     None      the entry is contained
    is said(secret(a)) in the graph?       True      the structure was not

Ancestry could not fix it, because the leak was not in the read: `at_or_after` is
checked when resolving an entry, and a structural fact is never resolved -- it is
enumerated straight out of the argument index. **So the indices are where this is
enforced, and not the nodes.** `_interned`, `_by_rel` and `_by_arg` are keyed by
situation below, and that is the concrete place the design lives or dies.
"""

from bisect import bisect_left
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple

NodeId = int
AtomId = int
SituationId = int

# The cap on an UNCAPPED step of a visibility walk. Node ids are minted from one
# monotonic counter, so "every node" is "every node id below infinity" and a
# single comparison decides both cases.
_UNCAPPED = 1 << 62

# The situation everything starts in. A machine that never supposes never leaves
# it, and every fast path below is written for exactly that case.
ROOT_SITUATION: SituationId = 0


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

        # -- situations (`docs/situations.md`) ----------------------------
        #
        # **A situation is a branch. A moment is a commit.** Deltas and
        # inheritance stay *within* a situation -- silence still means inherit,
        # so the frame problem stays solved where the agent spends its time.
        # What changes here is the STRUCTURAL layer: a node is minted into a
        # situation, and a situation sees its own nodes plus its ancestors' --
        # never a sibling's, and never a descendant's.
        #
        # ⚠ **Ancestor visibility is CAPPED, and the cap is what makes this a
        # branch rather than a window onto a moving parent.** A situation
        # records the node counter as it stood when it was cut; an ancestor node
        # minted after that is a later commit on another branch and is not in
        # this one. Without the cap a supposition would see the world change
        # under it while it reasoned, which is precisely the containment this
        # file exists to give.
        #
        # The cap composes down a chain by `min`, and because a child is always
        # cut after its parent the `min` is just the nearest branch point on the
        # path -- see `_visible`.
        self._sit_parent: Dict[SituationId, Optional[SituationId]] = {ROOT_SITUATION: None}
        self._sit_born: Dict[SituationId, int] = {ROOT_SITUATION: 0}
        self._next_sit: SituationId = ROOT_SITUATION + 1
        # The register. One, like the machine's `focus`, and moved by whatever
        # moves that -- a situation nobody is standing in cannot mint anything.
        self.situation: SituationId = ROOT_SITUATION
        self._sit_of: Dict[NodeId, SituationId] = {}
        # The visibility walk, memoised. Never invalidated: a situation's parent
        # and birth counter are fixed when it is cut.
        self._vis: Dict[SituationId, Tuple[Tuple[SituationId, int], ...]] = {}

        # -- atoms --------------------------------------------------------
        #
        # Every node, not only leaves. The reason is replay: a delta must
        # reference atoms rather than node ids, or replaying it into another
        # situation would reference nodes belonging to the situation it came
        # from -- and a delta names the relationship `healthy(paul)` as much as
        # it names `paul`.
        #
        # ⚠ **An atom is minted, never derived from the members' atoms.**
        # Deriving it would make identity structural rather than asserted, so
        # two situations that happened to build the same shape would be forced
        # to agree that it is the same relationship, with nothing holding the
        # correspondence that a rule could ask about or deny. Correspondence is
        # established by an ACT -- `carry` -- and by nothing else.
        self._atom: Dict[NodeId, AtomId] = {}
        self._next_atom: AtomId = 0
        # `(atom id, situation) -> node id`: the index that makes reading across
        # situations a lookup rather than a search. It is filled at mint for a
        # node's own situation and by `carry` for every situation a thing has
        # been transported into.
        self._node_by_atom: Dict[Tuple[AtomId, SituationId], NodeId] = {}

        # One index, over what was asserted rather than over what was derived
        # (§12): relation instances keyed by (rel, members) so the same
        # proposition is one node however often it is spoken of -- **within a
        # situation**. Across situations it is two nodes, and the atom index is
        # what says they are the same thing.
        self._interned: Dict[
            Tuple[SituationId, Optional[NodeId], Tuple[NodeId, ...]], NodeId
        ] = {}
        # A second index over what was asserted, not over what was derived (§16):
        # instances by relation. A rule whose antecedent names a relation has to
        # start somewhere, and scanning every node is the alternative.
        self._by_rel: Dict[Tuple[SituationId, NodeId], List[NodeId]] = {}
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
        self._by_arg: Dict[Tuple[SituationId, NodeId, int, NodeId], List[NodeId]] = {}
        # The merge of a bucket across a visibility walk, memoised. Only the
        # OWN-situation half of a merge can change -- every ancestor's visible
        # half is frozen by the cap -- so the bucket's own length is a complete
        # validity stamp, and a situation that mints nothing pays one dict get.
        self._merged: Dict[Tuple[SituationId, object], Tuple[List[NodeId], int]] = {}
        # Which variables are in a node, memoised. Immutable for `_has_var`'s
        # reason -- a node's relation and members are fixed when it is built.
        # ⚠ It lives HERE and not beside its one reader, because a node id means
        # nothing outside the graph that minted it: a module-level cache keyed
        # on the id answered a second machine's question with the first
        # machine's node, and the suite reported a corpus rule as concluding
        # about a variable nothing binds.
        self._vars_in: Dict[NodeId, set] = {}

    # -- situations -------------------------------------------------------

    def branch(
        self, parent: Optional[SituationId] = None, born: Optional[int] = None
    ) -> SituationId:
        """Cut a new situation off `parent` (the register, by default).

        Cheap by construction: **no copy-on-write and no eager copy**. A
        situation that nobody asks about costs one parent pointer and one
        integer, and what it sees of its ancestors is computed on the way past
        rather than materialised on the way in.

        ⭐ `born` is where the cut is, and passing one is **branching from an
        arbitrary past commit** -- which the design lists among the things this
        buys and which was simply absent before. `Moment.watermark` is what a
        caller passes: the node counter as it stood when that moment was made,
        so the new situation sees the structural world as of then. Default is
        now, which is the ordinary case and the only one `suppose` uses.
        """
        p = self.situation if parent is None else parent
        s = self._next_sit
        self._next_sit += 1
        self._sit_parent[s] = p
        self._sit_born[s] = self._next if born is None else born
        return s

    def situation_parent(self, s: SituationId) -> Optional[SituationId]:
        return self._sit_parent[s]

    @contextmanager
    def standing_in(self, s: SituationId):
        """Mint into `s` for the duration, then put the register back.

        For the callers that are building something on someone else's behalf.
        The machine's own register follows its focus, which is right for the
        agent reasoning; it is wrong exactly when the agent is doing something
        for a frame it is not standing in -- the gate depositing into a frame it
        was handed, and delivery, where the world speaks while the register is
        inside a hypothesis and the report belongs to the agent rather than to
        what the agent happens to be supposing.
        """
        was = self.situation
        self.situation = s
        try:
            yield
        finally:
            self.situation = was

    def _visible(self, s: SituationId) -> Tuple[Tuple[SituationId, int], ...]:
        """The situations `s` can see, ROOT FIRST, each with the node id it can
        see that situation up to.

        Root first because node ids ascend and an ancestor's visible half is
        entirely below the branch point: concatenating in this order yields mint
        order overall, which every reader below depends on for its tie-break.
        """
        got = self._vis.get(s)
        if got is not None:
            return got
        walk: List[Tuple[SituationId, int]] = []
        cap = _UNCAPPED
        cur: Optional[SituationId] = s
        while cur is not None:
            walk.append((cur, cap))
            # Stepping to the parent, the cap becomes the branch point -- and
            # `min` with what we already carried, which is always the branch
            # point itself since a child is cut after its parent.
            born = self._sit_born[cur]
            cap = born if born < cap else cap
            cur = self._sit_parent[cur]
        walk.reverse()
        got = tuple(walk)
        self._vis[s] = got
        return got

    def visible(self, n: NodeId, s: Optional[SituationId] = None) -> bool:
        """Can `s` see `n`? Its own nodes, and its ancestors' up to the cut."""
        s = self.situation if s is None else s
        home = self._sit_of[n]
        for sit, cap in self._visible(s):
            if sit == home:
                return n < cap
        return False

    def situation_of(self, n: NodeId) -> SituationId:
        return self._sit_of[n]

    # -- atoms ------------------------------------------------------------

    def atom_of(self, n: NodeId) -> AtomId:
        """The portable name of the thing this node realises."""
        return self._atom[n]

    def node_of(self, a: AtomId, s: Optional[SituationId] = None) -> Optional[NodeId]:
        """`?x@S`: take the atom of a thing, find its node in `S`.

        A lookup and not a search, which is the whole reason the index exists.
        The visibility walk is consulted nearest-first, so a situation that has
        its own realisation of a thing answers with that one rather than with
        the ancestor's it was carried from.
        """
        s = self.situation if s is None else s
        vis = self._visible(s)
        for sit, cap in reversed(vis):
            n = self._node_by_atom.get((a, sit))
            if n is not None and n < cap:
                return n
        return None

    def carry(self, n: NodeId, target: SituationId) -> NodeId:
        """Transport a node into `target`, and RECORD that it landed there.

        This is what a delta referencing atoms buys, arriving one construct at a
        time instead of as a replay: a conclusion drawn inside a supposition is
        built out of that situation's nodes, and re-stating it at the caller's
        seat has to re-state it in the caller's situation or the caller's own
        indices would carry a reference to something it cannot see.

        ⚠ **Structure decides identity WITHIN the target, and the atom index
        records where the carried thing landed.** Those are two different
        claims and both are needed. The first is `docs/situations.md`'s own
        rule -- *within a situation, the same relationship is one node* -- so a
        carry that minted unconditionally would split the target's identity for
        anything it already had. The second is what keeps the design's rejection
        of structural identity honest: the correspondence exists only where a
        carry created it, so two situations that never exchanged anything are
        still never forced to agree about a shape they both happen to build.

        The consequence, stated rather than discovered: the map from atoms to
        nodes in a situation is many-to-one at a landing site. `node_of` answers
        *where did this thing go*, not *what is this node's only name*.
        """
        if self.visible(n, target):
            return n
        a = self._atom[n]
        landed = self.node_of(a, target)
        if landed is not None:
            return landed
        rel = self._rel[n]
        members = tuple(self.carry(m, target) for m in self._members[n])
        crel = None if rel is None else self.carry(rel, target)
        was, self.situation = self.situation, target
        try:
            if crel is None:
                # A leaf: an individual, or a relation used by others. Minted
                # rather than interned, exactly as `atom`/`var` mint it.
                new = self._mint(None, (), self._name.get(n))
                if self._is_var.get(n, False):
                    self._is_var[new] = True
                    self._has_var[new] = True
            else:
                new = self.rel(crel, *members)
                # ⚠ The name too, and only if the target had nothing there
                # already. Names are for printing and never for identity, so
                # this cannot make two nodes one -- but a rule carried out of a
                # supposition that lost its `<boil>` would print as ninety
                # characters of its own structure in every `unmet` downstream,
                # which is the exact complaint `call_it` exists to answer.
                if n in self._name and new not in self._name:
                    self._name[new] = self._name[n]
        finally:
            self.situation = was
        # The correspondence, held rather than derived. `_atom[new]` is left
        # alone -- a node keeps the name it was minted under, and this says only
        # that asking for `a` in `target` reaches it.
        self._node_by_atom.setdefault((a, target), new)
        return new

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
        """A relation instance. Interned **within the register's situation**, so
        `on(a, b)` names one node there however many times it is built -- and a
        different node in a situation that built its own."""
        members = tuple(members)
        found = self._interned_lookup(relation, members)
        if found is not None:
            return found
        n = self._mint(relation, members, None)
        self._interned[(self.situation, relation, members)] = n
        return n

    def find_rel(self, relation: NodeId, *members: NodeId) -> Optional[NodeId]:
        """The interned instance if it exists, without creating one.

        ⚠ `rel` cannot answer this: asking would build the thing asked about.
        That is harmless for a proposition and not harmless for the skeleton,
        where existing IS the fact -- so §6's quiescence needs a question it can
        put without answering it. See `rules.already_there`.
        """
        return self._interned_lookup(relation, tuple(members))

    def _interned_lookup(
        self, relation: Optional[NodeId], members: Tuple[NodeId, ...]
    ) -> Optional[NodeId]:
        """The interned node this situation reaches, NEAREST FIRST.

        Nearest first because a situation that re-stated something for itself
        means that one: a carried conclusion is the caller's node, not the
        hypothesis's, and reaching past it would put the contained thing back in
        circulation.
        """
        vis = self._visible(self.situation)
        if len(vis) == 1:
            # Never branched from here -- one dict get, which is what the whole
            # engine did before situations existed and still does at the root.
            return self._interned.get((self.situation, relation, members))
        for sit, cap in reversed(vis):
            n = self._interned.get((sit, relation, members))
            if n is not None and n < cap:
                return n
        return None

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
        s = self.situation
        self._rel[n] = relation
        self._members[n] = members
        self._is_var[n] = False
        self._sit_of[n] = s
        a = self._next_atom
        self._next_atom += 1
        self._atom[n] = a
        self._node_by_atom[(a, s)] = n
        # Every constituent is already minted, so its answer is already here.
        self._has_var[n] = (
            (relation is not None and self._has_var.get(relation, False))
            or any(self._has_var.get(mm, False) for mm in members)
        )
        if name is not None:
            self._name[n] = name
        if relation is not None:
            self._by_rel.setdefault((s, relation), []).append(n)
            for i, mm in enumerate(members):
                self._by_arg.setdefault((s, relation, i, mm), []).append(n)
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

    def _bucket(self, index: Dict, key: object, sub: object) -> List[NodeId]:
        """One bucket, merged across the visibility walk and memoised.

        ⚠ **This is where the leak was, so this is where it is closed.** Distinct
        nodes alone would not have closed it: the structural walkers enumerate
        straight out of these indices, so an index that still spanned situations
        would hand a supposition's conclusion to the caller whatever identity it
        had.

        The merge is cached against the OWN bucket's length, and that is a
        complete stamp rather than a cheap one: every ancestor's contribution is
        `lst[:cap]`, the cap is the branch point, and nothing minted after the
        branch point can land below it.
        """
        vis = self._visible(self.situation)
        if len(vis) == 1:
            return index.get((self.situation,) + key, ())  # type: ignore[return-value]
        own = index.get((self.situation,) + key, ())
        ck = (self.situation, sub)
        hit = self._merged.get(ck)
        if hit is not None and hit[1] == len(own):
            return hit[0]
        out: List[NodeId] = []
        for sit, cap in vis:
            lst = index.get((sit,) + key)
            if not lst:
                continue
            # Ascending by construction, so the visible half is a prefix and
            # finding it is a bisect rather than a filter.
            out.extend(lst if cap == _UNCAPPED else lst[:bisect_left(lst, cap)])
        self._merged[ck] = (out, len(own))
        return out

    def instances_of(self, relation: NodeId) -> List[NodeId]:
        """Every instance of a relation VISIBLE FROM HERE, in mint order.
        Insertion-ordered, so a derivation that ends in a tie breaks it the same
        way on every run."""
        return list(self._bucket(self._by_rel, (relation,), relation))

    def instances_with(self, relation: NodeId, pos: int, member: NodeId) -> List[NodeId]:
        """Every instance of a relation with this node in this argument position.
        The narrow form of `instances_of`, and the same guarantee: mint order.

        ⚠ The list is the index's own and must not be mutated, which was true
        before situations and is still true: the merged form is cached, so a
        caller that edited it would edit every later read.
        """
        return self._bucket(self._by_arg, (relation, pos, member), (relation, pos, member))

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
