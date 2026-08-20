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

        # ⭐ **Members that fell off the index**, counted by the member as
        # written -- `docs/interpretation-feedback.md` §3. `_narrowed` cannot
        # index a structure that still carries a variable, so it falls back to
        # every instance of the relation: correct, sanctioned, and until now
        # invisible. An instrument, not a fact -- nothing reads this but a
        # `Report`, and no rule can match on it.
        #
        # `member as written -> [times it fell back, nodes those scans visited]`.
        self.scans: Dict[str, List[int]] = {}

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
        # `atom -> (relation atom, member atoms)`: the structural layer written
        # in the portable identity rather than the local one, so a thing can be
        # rebuilt in a situation that has never seen it. See `_mint` for why
        # this is not a duplicate of `_members`, and `rebuild` for what reads it.
        self._atom_members: Dict[
            AtomId, Tuple[Optional[AtomId], Tuple[AtomId, ...]]
        ] = {}
        # ...and the leaf half of the same record: `atom -> (name, is a
        # variable)`. Neither is derivable from the structure -- an atom and a
        # variable are both *no relation, no members*, and a name is not
        # structural at all -- so a replay that read only `_atom_members` would
        # rebuild every leaf as an anonymous ground node. Measured the hard way:
        # a replayed rule's `?x` came back as an atom named nothing and matched
        # nothing.
        self._atom_leaf: Dict[AtomId, Tuple[Optional[str], bool]] = {}

        # -- identity (coreference within a situation) --------------------
        #
        # ⭐⭐⭐ **The third identity, and it is the one that can be decided
        # LATE.** A node is the realisation, an atom is the portable name, and
        # neither can express *these two turned out to be the same thing*.
        # Today identity is settled by construction and never inferred -- the
        # loader's name table decides it at intake, interning decides it for
        # compounds -- so two nodes are one node or they are unrelated, and
        # there is no third state. This is the third state.
        #
        # ⚠ **Leaves only, and the default is the node itself.** A compound's
        # identity is not stored because it is DERIVED: interning keys on the
        # identities of the relation and members, so the canonical node *is* the
        # derived identity. That is the exact opposite of the atom rule one
        # block up, and the asymmetry is load-bearing:
        #
        #     atom      minted, never derived -- correspondence is an ACT, so a
        #               rule can deny that two situations mean one relationship
        #     identity  derived for compounds -- congruence IS the feature: if
        #               `a` and `b` are one thing then so are `f(a)` and `f(b)`
        #
        # One id cannot be both minted and derived, which is why this is a third
        # id rather than a reading of the second.
        #
        # ⚠⚠ **An unmerged corpus pays nothing.** With no entry here every
        # lookup returns the node it was given, so the interning key is
        # byte-identical to what it was before identity existed. That is the
        # same discipline `count` is held to: nothing that never corefers pays.
        # ⚠⚠⚠ **AND IT SUPERSEDES THE ATOM LAYER ABOVE -- next commit.** The
        # author's argument, and it is right: branching is a COPY, so two nodes
        # with one identity in two branches are one thing, which is the whole of
        # what an atom does. The objection this file records one block up --
        # *two situations that happened to build the same shape would be forced
        # to agree* -- assumes COINCIDENCE, and under branching there is none:
        # anything two branches share they share by DESCENT, so deriving the
        # same compound identity means they were built from the same parts and
        # genuinely are the same relationship. Independently minted things have
        # different identities and are not forced together.
        #
        # And the clincher is structural rather than philosophical: a derived
        # compound identity IS `(identity of relation, identities of members)`,
        # so it describes its own structure -- which is exactly what
        # `_atom_members` was added for, and makes that table redundant.
        # `rebuild` can recurse on the identity term itself.
        #
        # Landed beside the atom layer rather than instead of it so this commit
        # stays green and bisectable; the collapse is its own change.
        self._identity: Dict[Tuple[SituationId, NodeId], NodeId] = {}
        # The key each node is INDEXED under, so a merge knows what to move and
        # does not have to recompute the world to find out.
        self._keyed: Dict[NodeId, Tuple] = {}
        # `(situation, identity) -> nodes whose key mentions it`. This is what
        # makes a merge cost the upward CLOSURE of the merged things rather than
        # a scan of the graph -- and the closure is the number that decides
        # whether this is affordable.
        self._mentions: Dict[Tuple[SituationId, NodeId], List[NodeId]] = {}
        # Whether ANY merge has happened in this graph. The fast path is a
        # single boolean test rather than a dict get per member per `rel`, and
        # `rel` is the hottest call in the engine.
        self._merges = 0

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

    def identity_of(self, n: NodeId, s: Optional[SituationId] = None) -> NodeId:
        """What `n` counts as HERE -- itself, unless something merged it.

        Resolved through the visibility walk rather than read off the node, for
        the reason every other situation-relative thing is: a merge concluded
        inside a hypothesis must die with the hypothesis, and a field on a node
        would rewrite what the parent sees. `docs/situations.md`'s own line --
        *the indices are where this is enforced, and not the nodes.*

        ⚠ Follows chains: merging `b` into `a` and then `a` into `c` leaves `b`
        pointing at `a`, so this walks to the representative. No path
        compression, because the path is per-situation and compressing it in a
        child would write a claim the parent never made.
        """
        if not self._merges:
            return n
        s = self.situation if s is None else s
        seen = 0
        while True:
            got = None
            for sit, cap in reversed(self._visible(s)):
                hit = self._identity.get((sit, n))
                if hit is not None and hit < cap:
                    got = hit
                    break
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


    def merge(self, keep: NodeId, drop: NodeId,
              s: Optional[SituationId] = None) -> int:
        """`drop` counts as `keep` from here on, in `s`. Returns nodes repointed.

        ⭐⭐⭐ **Congruence, and it is why this cannot be two dict writes.** Once
        two things are one thing, every relationship either of them stands in is
        a relationship of the one thing -- so `bright(morning)` and
        `bright(evening)` have to become one node too, and so does anything
        built on THOSE. Merging two leaves therefore induces merges all the way
        up, and the worklist below is that cascade.

        ⚠⚠⚠ **Without the repoint, everything said before the merge is LOST.**
        `bright(morning)` was interned under a key naming morning's identity;
        after the merge `rel(bright, morning)` computes a key naming the new
        one, finds nothing, and mints a third node while the original sits
        unreachable in the index. Not a leak of containment -- a silent loss of
        what the agent already believed, which is worse, because nothing reports
        it. This is the whole of what makes identity a change to the INDICES
        rather than a field on a node.

        ⚠ **Per situation, so a merge inside a hypothesis dies with it.**
        Deciding two things are the same is a decision, and a decision made
        while supposing is not a decision about the world.

        ⚠ It does NOT decide anything: the caller supplies the pair, and the
        caller is a rule concluding `same(a, b)`. `deposit-dont-decide.md` --
        the engine may compute the consequence, never make the choice.
        """
        s = self.situation if s is None else s
        self._index_for_merge()
        moved = 0
        work = [(keep, drop)]
        while work:
            x, y = work.pop()
            if x == y:
                continue
            self._identity[(s, y)] = x
            self._merges += 1
            # Everything whose key mentioned `y` now keys on `x` instead.
            for n in list(self._mentions.get((s, y), ())):
                old = self._keyed.get(n)
                if old is None:
                    continue
                kr, km = self._key(self._rel[n], self._members[n])
                if (kr, km) == old:
                    continue
                okr, okm = old
                self._drop_from_index(n, s, okr, okm)
                already = self._interned.get((s, kr, km))
                if already is not None and already != n:
                    # Two nodes have collapsed onto one key. The older one wins,
                    # for the reason mint order always wins here: it is the one
                    # anything else already points at.
                    lo, hi = (already, n) if already < n else (n, already)
                    work.append((lo, hi))
                else:
                    self._interned[(s, kr, km)] = n
                    self._by_rel.setdefault((s, kr), []).append(n)
                    for i, mm in enumerate(km):
                        self._by_arg.setdefault((s, kr, i, mm), []).append(n)
                    self._keyed[n] = (kr, km)
                    for c in (kr,) + tuple(km):
                        self._mentions.setdefault((s, c), []).append(n)
                moved += 1
            self._merged.clear()  # bucket merges are cached against a stale key
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
            sit = self._sit_of[n]
            kr, km = self._key(r, self._members[n])
            self._keyed[n] = (kr, km)
            for x in (kr,) + tuple(km):
                self._mentions.setdefault((sit, x), []).append(n)

    def _drop_from_index(self, n: NodeId, s: SituationId, kr, km) -> None:
        """Take `n` out of every index it is in under `(kr, km)`."""
        if self._interned.get((s, kr, km)) == n:
            del self._interned[(s, kr, km)]
        b = self._by_rel.get((s, kr))
        if b and n in b:
            b.remove(n)
        for i, mm in enumerate(km):
            b = self._by_arg.get((s, kr, i, mm))
            if b and n in b:
                b.remove(n)

    def rebuild(self, a: AtomId, target: SituationId) -> NodeId:
        """Materialise the thing `a` names, in `target`, **from atoms alone**.

        This is what `docs/situations.md` means by *a situation is materialised*
        and it is the half stage 4 exists to build. `carry` transports a node
        that still exists; this reconstructs one from the portable record, so it
        works for a situation whose nodes were never minted or were discarded.

        ⭐ **It reads `_atom_members` and never `_members`**, which is the whole
        test of whether the atom layer is real. If this function needed a node
        to consult, atoms would be labels on a structure rather than a structure
        of their own, and nothing could ever be thrown away.

        ⚠ **Already-there wins, by the visibility walk.** If `target` can
        already see a realisation of `a`, that one is the answer -- rebuilding
        beside it would put two nodes for one thing in one situation, which is
        the twin trap wearing a replay. That is also what makes this idempotent,
        and what lets it be checked against capped visibility: rebuilding
        something a situation can already reach must be a no-op.

        ⚠ A variable rebuilds as a variable. `_is_var` is not derivable from the
        structure -- a bare variable has no relation and no members, exactly like
        an atom -- so it is carried across explicitly. Without this a replayed
        rule's members turn into ground atoms named `?x` and match nothing.
        """
        got = self.node_of(a, target)
        if got is not None:
            return got
        rel_a, mem_a = self._atom_members[a]
        # Depth first, because `_mint` reads its constituents' atoms.
        rel = None if rel_a is None else self.rebuild(rel_a, target)
        members = tuple(self.rebuild(x, target) for x in mem_a)
        name, generic = self._atom_leaf.get(a, (None, False))
        with self.standing_in(target):
            n = self._mint(rel, members, name, atom=a)
            if generic:
                self._is_var[n] = True
                self._has_var[n] = True
            if rel is not None:
                self._interned[(target, rel, members)] = n
        return n

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
        self._atom_leaf[self._atom[n]] = (name, True)
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
        if self._merges:
            relation, members = self._key(relation, members)
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
        if self._merges:
            relation, members = self._key(relation, members)
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
        self, relation: Optional[NodeId], members: Tuple[NodeId, ...],
        name: Optional[str], atom: Optional[AtomId] = None,
    ) -> NodeId:
        n = self._next
        self._next += 1
        s = self.situation
        self._rel[n] = relation
        self._members[n] = members
        self._is_var[n] = False
        self._sit_of[n] = s
        # ⭐ `atom` is supplied only by `rebuild`, and it is what makes a replay
        # a REPLAY rather than a second world that resembles the first. A node
        # minted fresh gets a fresh portable name; a node materialised from a
        # delta already has one, and minting a new one would break the
        # correspondence the delta was written in.
        if atom is None:
            a = self._next_atom
            self._next_atom += 1
        else:
            a = atom
        self._atom[n] = a
        self._node_by_atom[(a, s)] = n
        # ⭐⭐⭐ **The same structure again, one level up, in atoms** -- and it is
        # the floor stage 4 stands on. A delta referencing atoms can name
        # `healthy(paul)`, and naming it is not enough to REBUILD it: a
        # compound's atom is minted and deliberately not derived from its
        # members', so the atom alone says nothing about what it is made of.
        # Without this table an atom is a name for a node that has to still
        # exist, which is the thing replay is for getting rid of.
        #
        # ⚠ Kept beside `_members` rather than replacing it. `_members` is per
        # NODE and is what every reader walks; this is per ATOM and is what
        # survives the node being discarded. They are the same shape and they
        # answer different questions -- which is the whole of why there are two
        # identities in the first place.
        self._atom_members[a] = (
            None if relation is None else self._atom[relation],
            tuple(self._atom[mm] for mm in members),
        )
        self._atom_leaf.setdefault(a, (name, False))
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
            self._by_rel.setdefault((s, kr), []).append(n)
            for i, mm in enumerate(km):
                self._by_arg.setdefault((s, kr, i, mm), []).append(n)
            # ⚠⚠⚠ **Only once something has merged.** Maintaining these at
            # every mint cost the suite 9% -- 8.25s to 9.01s -- for corpora that
            # never corefer and never will, which is the one thing this layer
            # promised not to do. They are built by a single scan at the first
            # merge instead (`_index_for_merge`), and maintained from then on.
            # Measured rather than reasoned about: the fast path in `_key` was
            # already free, and this was the half that was not.
            if self._merges:
                self._keyed[n] = (kr, km)
                for x in (kr,) + tuple(km):
                    self._mentions.setdefault((s, x), []).append(n)
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
        # ⚠⚠⚠ **The atom learns the name too, or a replay prints as its own
        # structure.** A rule is minted as a compound and named afterwards, so
        # `_mint` never saw `<intake>` -- and a materialised rule came back
        # rendering as ninety characters of `implies(moment(entry(...)))`, which
        # is the exact defect this method exists to fix, arriving one layer down.
        # Caught by replaying the bundle: 110 of 160 propositions round-tripped
        # with identical structure and a different rendering.
        self._atom_leaf[self._atom[n]] = (text, self._is_var.get(n, False))
        return n

    def show(self, n: NodeId) -> str:
        if n in self._name:
            return self._name[n]
        r = self._rel[n]
        if r is None:
            return f"#{n}"
        inner = ", ".join(self.show(m) for m in self._members[n])
        return f"{self.show(r)}({inner})"
