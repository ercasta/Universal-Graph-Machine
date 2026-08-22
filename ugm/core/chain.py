"""Moments and entries, and the walk that reads them.

A moment is a signed delta, a predecessor and a licence. A proposition claims
nothing; the claim is a separate node, the entry, with exactly three members --
proposition and sign.

See docs/design/chain.md.
"""

import time as _wallclock
from typing import Dict, List, NamedTuple, Optional, Tuple

from .graph import Graph, NodeId

# -- the closed sets  -------------------------------------------------

PLUS = "+"
MINUS = "-"
UNSURE = "?"

# Signs are closed; GRADES are not, and never were replaced by anything closed.
# Modality is an ordinary proposition (`likely(p)`) a corpus wraps and unwraps.
# Why the ordinal scale went: docs/design/chain.md.


class Entry(NamedTuple):
    """The unit of assertion. Three members, and never a fourth: licence and
    source are ordinary facts about the entry"""

    node: NodeId  # the entry's own identity, so other facts can be about it
    proposition: NodeId
    sign: str
    licence: Optional[NodeId]  # what produced it: an application, an utterance
    source: Optional[NodeId]  # the channel it arrived through (§13)
    consumed: Tuple[NodeId, ...]  # the entries match consumed -- half the trail
    # Use or mention (§14). A ground claim ABOUT a rule names a node containing
    # variables, and is not a generic claim; structurally the two are identical,
    # so the difference has to be recorded rather than inferred.
    mention: bool = False


class Moment:
    """A state of affairs: the design's only such construct.

    `depth` exists so the two indices have a total order to compare on. In a
    linear chain it is the position; forking would need a real ancestry test,
    which slice one does not have.
    """

    def __init__(
        self,
        node: NodeId,
        predecessor: Optional["Moment"],
        chain: Optional["Chain"] = None,
    ) -> None:
        self.node = node
        self.predecessor = predecessor
        self.chain = chain
        self.delta: List[Entry] = []
        self.depth = 0 if predecessor is None else predecessor.depth + 1

    def ancestors(self) -> List["Moment"]:
        """This moment and its predecessors, newest first."""
        out, m = [], self
        while m is not None:
            out.append(m)
            m = m.predecessor
        return out

    def __repr__(self) -> str:
        return f"M{self.depth}"


class Chain:
    """The history, and the reads over it."""

    def __init__(self, g: Graph, clock: bool = False) -> None:
        self.g = g
        # Off by default: a source of nondeterminism is requested, not
        # inherited. Not a way to ORDER moments -- `pred`/`anc` do that
        # exactly. This answers *how long ago*. docs/design/chain.md.
        self.clock = clock
        self.ENTRY = g.atom("entry")
        self.MOMENT = g.atom("moment")
        # The structural mirror. `pred` and `in_delta` are plain relation
        # instances, not entries: nobody asserted them, they cannot be denied,
        # dated or attributed. That is exactly the skeleton, and it is what
        # makes them matchable by a stratum-0 rule.
        self.PRED = g.atom("pred")
        # Strict ancestry, as a name an ordinary rule may write. Not
        # materialised -- `structural_relations` walks it -- because the walk is
        # bounded and upward, and a stored transitive closure would be a cache
        # of something derived.
        self.SANC = g.atom("sanc")
        # ...and the reflexive one. `anc($m, $m)` holds, which is what lets a
        # read asked AT the seat find what the seat itself deposited -- the case
        # a strict walk silently drops. Both are walked rather than stored, for
        # `sanc`'s reason.
        self.ANC = g.atom("anc")
        self.IN_DELTA = g.atom("in_delta")
        # An entry's own three members, as a relation a rule may write:
        # `entry_of($e, $prop, $sign)`. Nothing is deposited for it --
        # the entry node already IS `entry(proposition, sign)`, so this
        # is `$t = entry(...)` prefix form arriving as a member instead of
        # as notation. The read could not be written without it: every rule
        # below `in_delta` needs an entry's locus and sign, and until now only a
        # second matcher's `capture` could reach them.
        self.ENTRY_OF = g.atom("entry_of")
        # `asking(<seat>)` -- what the read is anchored on, and what binds its
        # first member. Without it a seat can only be bound by enumerating
        # every moment. docs/design/chain.md.
        self.ASKING = g.atom("asking")
        # ...and WHAT is being asked about. A read answers about a proposition,
        # so a read that derives candidates for every proposition in the history
        # is answering questions nobody put. 
        # Seeded beside the seat, and by the same one caller.
        self.ASKED = g.atom("asked")
        self.IS_MOMENT = g.atom("moment_of")
        # `time(<moment>, <millis>)` -- structural, like `pred`, because nobody
        # asserted it and nothing can deny it. Deposited only when the clock is
        # on, so a corpus asking for it on a clockless run finds nothing, which
        # is the honest answer rather than a zero.
        self.TIME = g.atom("time")
        # Position within a delta. A moment's entries are ordered -- two claims
        # about the same locus are told apart by which was deposited later -- and
        # that order lived in a Python list, where no rule could reach it.
        self.DELTA_NEXT = g.atom("delta_next")
        # What an entry was derived FROM. Beside `pred` and `in_delta` rather
        # than as entries, and for their reason: nobody asserted it, it cannot be
        # denied, dated or attributed. Support is *how the entry was made*, not a
        # claim about the world -- so it is skeleton, and a rule may match it
        # without any of it being arguable.
        #
        # It was already recorded, as `Entry.consumed`: a Python tuple, so no
        # rule could ask what anything rested on and `why()` had to be a native
        # walk. §21's defect for the ninth time, and the fix is the one the other
        # eight got.
        self.RESTS_ON = g.atom("rests_on")
        # What LICENSED an entry --
        # `loaded(p)` for something the agent was told, `applied(<R>)` for
        # something it worked out. Beside `rests_on` and for its reason: nobody
        # asserted it, it cannot be denied, dated or attributed; it is *how the
        # entry was made*, not a claim about the world.
        #
        # It was already recorded as `Entry.licence`, a Python field, which is
        # finding 1 of the audit in Part 1: the discriminator between *told* and
        # *inferred* sat on every entry and no rule could read it.
        self.LICENSED_BY = g.atom("licensed_by")
        # ...and the other two fields called "ordinary facts about the entry"
        # while keeping them in Python. `arrived_on` is  channel;
        # `mentioned` is use/mention. Skeleton, for `rests_on`'s reason:
        # nobody asserted them, they are how the entry was made.
        self.ARRIVED_ON = g.atom("arrived_on")
        self.MENTIONED = g.atom("mentioned")
        # Sign atoms live here rather than in the rule set, because an entry's
        # third member is a sign and the chain is what mints entries. Everything
        # else takes them from here: `atom` does not intern, so a second
        # `g.atom("+")` would be a different node that no rule could match --
        # the name-identity trap, which has cost this design four silent bugs.
        self.SIGN = {s: g.atom(s) for s in (PLUS, MINUS, UNSURE)}
        self.root = Moment(g.instance(self.MOMENT), None, self)
        g.rel(self.IS_MOMENT, self.root.node)
        self._stamp(self.root)
        self.moments: List[Moment] = [self.root]
        self._moment_by_node: Dict[NodeId, Moment] = {self.root.node: self.root}
        # Entries by the proposition they are about: (seat, position, entry).
        # Deposit-side, so it indexes what was asserted and never what was
        # derived -- the condition §12 puts on any index in this design.
        self._claims: Dict[NodeId, List[Tuple[Moment, int, Entry]]] = {}
        self._by_node: Dict[NodeId, Entry] = {}

    def succeed(self, predecessor: Moment, licence: Optional[NodeId]) -> Moment:
        """Succession: the shared core of time and derivation (§4). Which of the
        two this is, is said by the licence and by nothing else."""
        # `instance`, not `rel`. A moment has no members, so interning would make
        # every moment in the history one node -- which it did, silently, until a
        # stratum-0 rule was written that needed to tell two of them apart. The
        # design says a moment is a node so that facts can be about it; that is
        # false the moment they are all the same node.
        # The moment's own
        # succession is `pred`; what a moment is FOR is a fact about it.
        m = Moment(self.g.instance(self.MOMENT), predecessor, self)
        self.g.rel(self.IS_MOMENT, m.node)
        self.g.rel(self.PRED, m.node, predecessor.node)
        self._stamp(m)
        self.moments.append(m)
        # ...and by node, because a rule can now name a moment and
        # something has to get from the name back to the thing. Maintained here,
        # where moments are made, rather than scanned for -- the rule that what
        # is read off a state is maintained where the state is.
        self._moment_by_node[m.node] = m
        return m

    @property
    def now(self) -> Moment:
        """The chain's end -- where the next entry lands.

        """
        return self.moments[-1]

    def moment_of(self, node: NodeId) -> Optional[Moment]:
        """The moment a node names, or None. Public because a structural walker
        needs it and reaching into `_moment_by_node` from another module would
        make the index's one maintainer two."""
        return self._moment_by_node.get(node)

    def _stamp(self, m: Moment) -> None:
        """When this moment was made, in milliseconds since the epoch.

        One place, because a moment is born in exactly two -- the root and
        `succeed` -- and a stamp applied in one of them would be a chain whose
        clock has a hole in it that nothing reports.

        Milliseconds as an ATOM whose name reads as a number, which is how
        every other numeral works here: nothing in the graph learns about
        arithmetic, and the one reader that wants it does the conversion.
        """
        if not self.clock:
            return
        self.g.rel(self.TIME, m.node,
                   self.g.atom(str(int(_wallclock.time() * 1000))))

    def deposit(
        self,
        proposition: NodeId,
        sign: str,
        licence: Optional[NodeId] = None,
        source: Optional[NodeId] = None,
        consumed: Tuple[NodeId, ...] = (),
        mention: bool = False,
    ) -> Entry:
        """Place an entry in the latest moment's delta.

        Callers should not reach this directly.

        Note: An entry was
        `entry(locus, proposition, sign)` here and `entry(pattern, sign)` in a
        rule's moment -- the same word for two shapes, which is the twin trap
        with a different name. With the locus gone they are one shape, and a
        rule's moment and a chain's moment are finally the same construct.

        **Where an entry lands is the latest moment, and that is not a
        register.** It is the chain's own end. Nothing chooses it, so nothing
        can choose it wrongly.
        """
        seat = self.moments[-1]
        node = self.g.instance(self.ENTRY, proposition, self.SIGN[sign])
        self.g.rel(self.IN_DELTA, seat.node, node)
        if seat.delta:
            self.g.rel(self.DELTA_NEXT, node, seat.delta[-1].node)
        for c in consumed:
            self.g.rel(self.RESTS_ON, node, c)
        if licence is not None:
            self.g.rel(self.LICENSED_BY, node, licence)
        if source is not None:
            self.g.rel(self.ARRIVED_ON, node, source)
        if mention:
            self.g.rel(self.MENTIONED, node)
        e = Entry(node, proposition, sign, licence, source, consumed, mention)
        seat.delta.append(e)
        # ...and an index by the entry's own node. `entry_by_node` was a scan of
        # every moment's delta, so the trail walk it serves was quadratic in the
        # history -- invisible because nothing in the loop calls it, and about to
        # stop being invisible now that support is a question the agent asks.
        self._by_node[node] = e
        # One index, over what was asserted rather than over what was derived --
        # the same licence gives the substrate, applied to the chain. `resolve`
        # is the design's most consequential cost and it was scanning every
        # entry ever deposited to answer a question about one proposition;
        # measured, that was 70% of the engine's runtime after the walk itself
        # had been fixed. The entries for one proposition are almost always one.
        self._claims.setdefault(proposition, []).append(e)
        return e

    # -- reading (§4) -----------------------------------------------------

    def resolve(self, proposition: NodeId) -> Optional[Entry]:
        """What the chain says about this proposition: the LAST claim made.

        What this cannot answer, said plainly: *did this hold THEN*. That is
        no longer a Python service and it is not lost -- `in_delta`, `pred`,
        `anc` and `entry_of` are ordinary structural relations, so a corpus that
        wants history writes the rule and gets a dated, attributable, deniable
        answer instead of a privileged one. 
        """
        got = self._claims.get(proposition)
        return got[-1] if got else None

    def holds(self, proposition: NodeId) -> Optional[str]:
        """The sign, or None if the chain says nothing. `?` is not None: it stops
        the walk and reports ignorance, which is the one thing writing nothing
        could never say"""
        e = self.resolve(proposition)
        return None if e is None else e.sign

    def trail(self, e: Entry) -> List[Entry]:
        """Every entry this one rests on, transitively. This is what makes *why
        do you believe that* answerable, and it is load-bearing for
        soundness rather than only for explanation."""
        seen: Dict[NodeId, Entry] = {}
        frontier = [e]
        while frontier:
            cur = frontier.pop()
            for c in cur.consumed:
                found = self.entry_by_node(c)
                if found is not None and found.node not in seen:
                    seen[found.node] = found
                    frontier.append(found)
        return list(seen.values())

    def entry_by_node(self, node: NodeId) -> Optional[Entry]:
        return self._by_node.get(node)

    def moment_by_node(self, node: NodeId) -> Optional[Moment]:
        return self._moment_by_node.get(node)

    def claims_about(self, proposition: NodeId) -> List[Entry]:
        """Every entry ever deposited about this proposition, in order. The
        deposit-side index, which permits precisely because it indexes what
        was asserted and never what was derived."""
        return list(self._claims.get(proposition, ()))

    def rests_on(self, e: Entry) -> List[Entry]:
        """What this entry was derived from, one hop, read from the graph rather
        than from the Python field. The two must agree -- the selftest's
        structural-mirror checks hold them to it (the retired `ugm.support`
        did before them) -- an index is a re-implementation of what it indexes,
        which is the lesson `state` paid for."""
        out = []
        for node in self.g.instances_of(self.RESTS_ON):
            if self.g.member(node, 0) != e.node:
                continue
            found = self._by_node.get(self.g.member(node, 1))
            if found is not None:
                out.append(found)
        return out
