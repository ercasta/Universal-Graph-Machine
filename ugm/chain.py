"""Moments (§4) and entries (§5), and the walk that reads them.

A moment is a signed delta, a predecessor and a licence. A proposition claims
nothing; the claim is a separate node, the entry, with exactly three members --
locus, proposition, sign.

An entry carries two times, and keeping them apart is the whole of §4's second
half:

    locus       what the claim is about
    deposit     the moment whose delta it sits in -- when the claim was made

In the common case they coincide. They come apart when the agent learns
something about a time that has already passed, which is what makes belief
revision ordinary rather than a second mechanism.
"""

import time as _wallclock
from typing import Dict, List, NamedTuple, Optional, Tuple, Union

from .graph import Graph, NodeId

# -- the closed sets of §10 -------------------------------------------------

PLUS = "+"
MINUS = "-"
UNSURE = "?"

# ⭐⭐⭐ **There is no closed set of grades, and that is the point of removing
# them.** `GRADES` was five names in Python -- unknown, unlikely, possible,
# likely, certain -- with an ordinal `weaker` composing them by weakest link on
# every write. It has been deleted, and what replaces it is `likely(p)`: an
# ordinary proposition, crossed into a supposition by an ordinary rule, coming
# back out wrapped. So a corpus may now have whatever modalities it likes, with
# whatever ordering it authors, and §10's *closed is a rate, not a kind* holds
# one place further.
#
# Measured before deleting, three ways. `ugm.modality` already ranked the grade
# last of the three treatments -- **not a term, so no rule can ask about it; no
# guard to cross; does not nest**. The suite authored one in **4 of 3,740
# rules** and carried one on **6 of 32,289 entries**. And `weaker` was called
# from exactly one place: the grade was carried, composed and printed, and
# **nothing ever decided on it**, which is this repo's own *read and not obeyed*
# defect arriving at the floor.
#
# ⚠ What is lost is that weakest link was AUTOMATIC and TOTAL. A conclusion
# drawn from an uncertain premise is now derived only if a corpus crossed, and
# what comes out is nested -- `likely(possible(x))` -- where `min` gave one
# ordinal. Collapsing that is a corpus's table and its ordering is a corpus's
# claim, which is the trade: the ordinal stops being free and starts being
# arguable.


class Entry(NamedTuple):
    """The unit of assertion. Three members, and never a fourth: licence and
    source are ordinary facts about the entry (§5)."""

    node: NodeId  # the entry's own identity, so other facts can be about it
    locus: "Locus"
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
    """A state of affairs: the design's only such construct (§4).

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

    def at_or_after(self, other: "Locus") -> bool:
        """Is `other` this moment or one of its ancestors?

        A depth comparison is not enough once anything forks -- and supposing
        forks by construction. Two moments on different branches can share a
        depth while neither is on the other's walk, and a depth test would let a
        claim made inside one supposition answer a question asked inside its
        sibling. That is the containment property, so it has to be ancestry.

        ⚠ **The span case is no longer decided here.** *A span is at or before
        this moment once the stretch is complete* is a decision, not a walk, and
        it lives in `bundle.ugm` now as `<span-complete>` -- a rule a corpus can
        argue with, override or delete. What is left in Python is the walk,
        which the author's line permits, and a lookup that argues for nothing.
        """
        if isinstance(other, Span):
            return bool(self.chain and self.chain.consult(self.node, other.node))
        m: Optional["Moment"] = self
        while m is not None:
            if m is other:
                return True
            m = m.predecessor
        return False

    def __repr__(self) -> str:
        return f"M{self.depth}"


class Span:
    """A stretch of the chain: a node with exactly two members, a start moment
    and an end moment (§11).

    Some claims are not about a moment at all. *They are taking turns* is not
    true of any instant; its subject is a stretch. So a locus is a moment **or a
    span**, which §8 has said since it was written and the engine did not build.

    **The contents are not stored**, and the reason is structural rather than
    frugal: the predecessor relation is single-valued, so the walk back from the
    end is unique and the chain already settles what lies between. Storing them
    would be a second answer to *what is in this span* that could disagree with
    the first.

    ⭐⭐⭐ **Inheritance is within a kind of locus, and that is the whole of the
    read's growth.** Three of the four directions are decided here:

        moment .at_or_after(span)    -- ✅ the stretch is over; the recognition
                                        stands, and ordinary rules can use it
        span   .at_or_after(moment)  -- ❌ a claim about an INSTANT is not a
                                        claim about a stretch
        span   .at_or_after(span)    -- the same span, and no other

    The ❌ is the load-bearing one. Letting a moment's claim inherit into a span
    would answer *did it hold throughout* from an entry that says only *it held
    then* -- and a denial in the middle of the stretch is exactly what the read
    cannot see, because `resolve` returns one winner rather than scanning an
    interval. That would be a leak of the worst kind: free, unarguable, and
    wrong only sometimes. A corpus that wants *it held at the start, so it held
    throughout* writes the rule, and then it is dated, attributed and deniable
    like every other claim. §12's grade deletion made the same trade: the free
    ordinal becomes the arguable one.

    ⚠ Containment between two spans -- a claim over M7..M12 answering about
    M9..M11 -- is NOT read here either, for the same reason and with the same
    remedy. Interval relations are ordinary facts about endpoints (§11), so
    `during(?s2, ?s1)` is a corpus's to conclude and to reason from.
    """

    def __init__(self, node: NodeId, start: "Moment", end: "Moment",
                 chain: Optional["Chain"] = None) -> None:
        self.node = node
        self.start = start
        self.end = end
        self.chain = chain
        # ⚠ The end, because that is when the stretch is over and the claim is
        # available. Recency in `resolve`'s key is *how recent is the thing this
        # is about*, and for a stretch that is where it finishes.
        self.depth = end.depth

    def at_or_after(self, other: "Locus") -> bool:
        """Both remaining cases are policy and neither is decided here.

        `<span-itself>` in `bundle.ugm` says a span reaches itself; **nothing
        says a span reaches a moment**, and that is the honest way to write no
        -- a rule that does not exist rather than a branch that returns False.
        """
        return bool(self.chain and self.chain.consult(self.node, other.node))

    def __repr__(self) -> str:
        return f"S{self.start.depth}..{self.end.depth}"


# A locus is a moment or a span (§8), and after this line that is true of the
# engine and not only of the document.
Locus = Union[Moment, Span]


def scope_of(locus: Locus) -> Optional[NodeId]:
    """What a claim at this locus can be SUPERSEDED WITHIN.

    ⭐⭐⭐ **The resolved state is one entry per proposition, and that was an
    assumption about loci rather than about propositions.** It is right exactly
    while every two loci are comparable -- on a chain of moments one is always at
    or before the other, so the later claim governs and keeping one answer is the
    whole of §10's read. Spans are not comparable: *they took turns over M1..M4*
    and *over M2..M4* are two claims, neither superseding the other, and a state
    keyed on the proposition alone silently kept one.

    So a claim is superseded only by a claim it is comparable with, and the key
    says which: `None` for a moment, since all moments share one order, and the
    span's own node for a span, since each is its own.

    ⚠⚠ **What this is NOT load-bearing for, because the probe corrected the
    claim.** I wrote first that §13's recursion cannot see its own output without
    it, and that is false of the shape actually built: *taking turns* recurses in
    the STRUCTURAL layer, which never consults the resolved state, so removing
    this breaks exactly one check -- the one that asserts it directly -- and the
    ten recognitions still land. It would be load-bearing for a recursion written
    over ENTRIES, and that route is blocked one step earlier anyway (§12: a single
    fact's own history is not in the resolved state). So what this buys is
    **reading** two recognitions over different stretches, which is what any rule
    downstream of a shape does, and it is asserted directly because nothing else
    can see it.
    """
    return locus.node if isinstance(locus, Span) else None


class Chain:
    """The history, and the reads over it."""

    def __init__(self, g: Graph, clock: bool = False) -> None:
        self.g = g
        # ⭐ **The wall clock, off by default, and the reason is measured
        # rather than assumed.** A stamp is STRUCTURAL, like `pred` -- not an
        # entry -- so switching the clock on leaves the entries of two runs
        # byte-identical and only the stamps differ. `ugm.dungeon`'s *the same
        # seed replays the same fight, entry for entry* is untouched.
        #
        # What does diverge is a corpus that READS the clock: its conclusions
        # are entries, and they carry a number that was different last time. So
        # the clock is inert until asked for, and off by default because a
        # source of nondeterminism should be requested rather than inherited.
        #
        # ⚠ What it is NOT: a way to order moments. `pred` and `anc` already do
        # that, and they are exact where a clock is only monotone-ish. The stamp
        # answers *how long ago*, which the chain could not answer at all --
        # moments are ORDERED, not MEASURED, and `depth` is a position rather
        # than a duration.
        self.clock = clock
        self.ENTRY = g.atom("entry")
        self.MOMENT = g.atom("moment")
        # The structural mirror (§6). `pred` and `in_delta` are plain relation
        # instances, not entries: nobody asserted them, they cannot be denied,
        # dated or attributed. That is exactly §12's skeleton, and it is what
        # makes them matchable by a stratum-0 rule.
        self.PRED = g.atom("pred")
        # Strict ancestry, as a name an ordinary rule may write (§12). Not
        # materialised -- `structural_relations` walks it -- because the walk is
        # bounded and upward, and a stored transitive closure would be a cache
        # of something derived (§3).
        self.SANC = g.atom("sanc")
        # ...and the reflexive one. `anc(?m, ?m)` holds, which is what lets a
        # read asked AT the seat find what the seat itself deposited -- the case
        # a strict walk silently drops. Both are walked rather than stored, for
        # `sanc`'s reason.
        self.ANC = g.atom("anc")
        self.IN_DELTA = g.atom("in_delta")
        # An entry's own three members, as a relation a rule may write:
        # `entry_of(?e, ?locus, ?prop, ?sign)`. Nothing is deposited for it --
        # the entry node already IS `entry(locus, proposition, sign)`, so this
        # is §12's `?t = entry(...)` prefix form arriving as a member instead of
        # as notation. The read could not be written without it: every rule
        # below `in_delta` needs an entry's locus and sign, and until now only a
        # second matcher's `capture` could reach them.
        self.ENTRY_OF = g.atom("entry_of")
        # ⭐⭐⭐ **The question, as a skeleton fact.** `asking(<seat>)` is what the
        # read is anchored ON, and it is the difference between a read and an
        # enumeration of the history. Every other member of the read's rules
        # walks or looks up from something already bound; this is what binds the
        # first one.
        #
        # It is skeleton by the same test as the rest -- nobody asserted it, it
        # cannot be denied, dated or attributed, and it says how the graph is
        # being read rather than anything about the world. The machinery seeds
        # it; §6's price applies to it exactly as to `cand` and `best`.
        #
        # ⚠ Without it the read's first member is unanchored, and the only way
        # to bind a seat is to enumerate every moment -- which is what the second
        # matcher did, and why it was *deliberately slow*: it derived the read
        # for every seat in the history whether or not anything asked.
        self.ASKING = g.atom("asking")
        # ...and WHAT is being asked about. A read answers about a proposition,
        # so a read that derives candidates for every proposition in the history
        # is answering questions nobody put. It went unnoticed while §7 hid two
        # thirds of the chain from the matcher: with the reified entries visible
        # the same five-moment fixture derived 10,638 facts to answer 28
        # questions. Seeded beside the seat, and by the same one caller.
        self.ASKED = g.atom("asked")
        # Whether one locus can see a claim made at another, WHERE THAT IS A
        # DECISION rather than a walk. Moment-to-moment is ancestry and stays a
        # walk; the three span cases are policy, they live in `bundle.ugm`, and
        # this is the relation they conclude.
        self.REACHES = g.atom("reaches")
        # ...and how the machinery asks. Set by the Machine, which is the only
        # thing that has both a chain and a rule set. `None` means nothing has
        # been told the policy, and then no span reaches anything -- the honest
        # default, since the answer comes from rules and there are none.
        #
        # Python consulting rules is not the boundary this design polices: the
        # author's line is about logic BURIED in Python, and a lookup that
        # argues for nothing is not that. `_forbid` reads `forbidden`,
        # `precedence()` reads what the graph claims, `_recall` reads `dormant`
        # -- this is the same door with a general name.
        self.consult = lambda a, b: False
        self.IS_MOMENT = g.atom("moment_of")
        # `time(<moment>, <millis>)` -- structural, like `pred`, because nobody
        # asserted it and nothing can deny it. Deposited only when the clock is
        # on, so a corpus asking for it on a clockless run finds nothing, which
        # is the honest answer rather than a zero.
        self.TIME = g.atom("time")
        # A stretch of the chain, as a member a rule may write (§11):
        # `span_of(?s, ?start, ?end)`. Nothing is deposited for it -- the span
        # node already IS `span(start, end)` -- so this is `entry_of`'s shape
        # one construct along, and for `entry_of`'s reason: the read cannot be
        # written without a way to get at a node's own members.
        self.SPAN = g.atom("span")
        self.SPAN_OF = g.atom("span_of")
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
        # ⭐ EXPERIMENT (docs/observations.md §2.8). What LICENSED an entry --
        # `loaded(p)` for something the agent was told, `applied(<R>)` for
        # something it worked out. Beside `rests_on` and for its reason: nobody
        # asserted it, it cannot be denied, dated or attributed; it is *how the
        # entry was made*, not a claim about the world.
        #
        # It was already recorded as `Entry.licence`, a Python field, which is
        # finding 1 of the audit in Part 1: the discriminator between *told* and
        # *inferred* sat on every entry and no rule could read it.
        self.LICENSED_BY = g.atom("licensed_by")
        # ...and the other two fields §5 called "ordinary facts about the entry"
        # while keeping them in Python. `arrived_on` is §13's channel;
        # `mentioned` is §14's use/mention. Skeleton, for `rests_on`'s reason:
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
        self._span_by_node: Dict[NodeId, Span] = {}
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
        # The licence is no longer carried: it was assigned here and read
        # nowhere in the repository, while §4 claimed *which of the two this is
        # is said by the licence and by nothing else*. The moment's own
        # succession is `pred`; what a moment is FOR is a fact about it.
        m = Moment(self.g.instance(self.MOMENT), predecessor, self)
        self.g.rel(self.IS_MOMENT, m.node)
        self.g.rel(self.PRED, m.node, predecessor.node)
        self._stamp(m)
        self.moments.append(m)
        # ...and by node, because a rule can now name a moment (§12's `at`) and
        # something has to get from the name back to the thing. Maintained here,
        # where moments are made, rather than scanned for -- §7's rule that what
        # is read off a state is maintained where the state is.
        self._moment_by_node[m.node] = m
        return m

    def _stamp(self, m: Moment) -> None:
        """When this moment was made, in milliseconds since the epoch.

        One place, because a moment is born in exactly two -- the root and
        `succeed` -- and a stamp applied in one of them would be a chain whose
        clock has a hole in it that nothing reports.

        ⚠ Milliseconds as an ATOM whose name reads as a number, which is how
        every other numeral works here: nothing in the graph learns about
        arithmetic, and the one reader that wants it does the conversion.
        """
        if not self.clock:
            return
        self.g.rel(self.TIME, m.node,
                   self.g.atom(str(int(_wallclock.time() * 1000))))

    def deposit(
        self,
        seat: Moment,
        locus: Locus,
        proposition: NodeId,
        sign: str,
        licence: Optional[NodeId] = None,
        source: Optional[NodeId] = None,
        consumed: Tuple[NodeId, ...] = (),
        mention: bool = False,
    ) -> Entry:
        """Place an entry in `seat`'s delta, about `locus`.

        Callers should not reach this directly -- it is what the gate of §13
        wraps, and the gate is the only thing that knows where the stamps come
        from.
        """
        # Three members, and never a fourth (§8): locus, proposition, sign. The
        # sign was previously kept beside the node in Python, which made the
        # implementation disagree with the design in the one place a rule would
        # have had to look.
        node = self.g.instance(self.ENTRY, locus.node, proposition, self.SIGN[sign])
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
        e = Entry(node, locus, proposition, sign, licence, source, consumed, mention)
        seat.delta.append(e)
        # ...and an index by the entry's own node. `entry_by_node` was a scan of
        # every moment's delta, so the trail walk it serves was quadratic in the
        # history -- invisible because nothing in the loop calls it, and about to
        # stop being invisible now that support is a question the agent asks.
        self._by_node[node] = e
        # One index, over what was asserted rather than over what was derived --
        # the same licence §3 gives the substrate, applied to the chain. `resolve`
        # is the design's most consequential cost (§4) and it was scanning every
        # entry ever deposited to answer a question about one proposition;
        # measured, that was 70% of the engine's runtime after the walk itself
        # had been fixed. The entries for one proposition are almost always one.
        self._claims.setdefault(proposition, []).append((seat, len(seat.delta) - 1, e))
        return e

    # -- reading (§4) -----------------------------------------------------

    def resolve(
        self, proposition: NodeId, locus: Locus, seat: Optional[Moment] = None
    ) -> Optional[Entry]:
        """Does this proposition hold at `locus`, as believed at `seat`?

        Two orderings decide it, and they are not interchangeable:

            latest locus first   -- the most recent claim about the world wins,
                                    which is what makes silence mean *inherit*
            latest deposit next  -- among claims about the same time, the agent's
                                    current view wins over what it used to think

        Both are needed. Locus alone cannot tell a revision from the original;
        deposit alone would let an old belief about a late moment be overruled by
        a new belief about an early one.
        """
        if seat is None:
            seat = self.moments[-1]
        best: Optional[Entry] = None
        best_key = ()
        # The two orderings, as one comparison instead of as a walk order. The
        # old loop went newest-moment-first and newest-within-a-moment-first and
        # replaced `best` only on a strictly later locus -- so the winner was the
        # entry with the greatest (locus depth, seat depth, position), and that
        # is what is computed here. Containment still costs an ancestry test:
        # a depth comparison cannot replace it once anything forks, and supposing
        # forks by construction.
        for m, pos, e in self._claims.get(proposition, ()):
            if not locus.at_or_after(e.locus):  # inheritance: locus or earlier
                continue
            if not seat.at_or_after(m):  # ...and it must be on this branch
                continue
            key = (e.locus.depth, m.depth, pos)
            if best is None or key > best_key:
                best, best_key = e, key
        return best

    def holds(
        self, proposition: NodeId, locus: Locus, seat: Optional[Moment] = None
    ) -> Optional[str]:
        """The sign, or None if the chain says nothing. `?` is not None: it stops
        the walk and reports ignorance, which is the one thing writing nothing
        could never say (§6)."""
        e = self.resolve(proposition, locus, seat)
        return None if e is None else e.sign

    def trail(self, e: Entry) -> List[Entry]:
        """Every entry this one rests on, transitively. This is what makes *why
        do you believe that* answerable, and per §12 it is load-bearing for
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

    def span(self, start: Moment, end: Moment) -> Span:
        """Mint the stretch from `start` to `end` (§11).

        ⭐ **Interned, so a span has one identity however often it is built.**
        Two recognisers reaching the same stretch must reach the same node or
        everything said about it splits in two -- the twin trap, which this
        design has paid for often enough to reach for `rel` first.

        ⚠ **The ancestry check is HERE, and §11 says why**: nothing prevents
        constructing a span whose start is not an ancestor of its end, such a
        span is meaningless, and this is the site where the mistake is still
        attributable. A degenerate span is refused too -- `span(M7, M7)` is a
        second name for a moment, and two ways to say one locus is exactly the
        ambiguity the read cannot afford.

        ⚠ Spans are minted by recognisers and never enumerated: any two moments
        form one, so the population is quadratic in the history.
        """
        if not end.at_or_after(start):
            raise ValueError(f"span start {start} is not an ancestor of {end}")
        if end is start:
            raise ValueError(f"a span needs a stretch: {start} to {end} is one moment")
        node = self.g.rel(self.SPAN, start.node, end.node)
        got = self._span_by_node.get(node)
        if got is None:
            got = Span(node, start, end, self)
            self._span_by_node[node] = got
        return got

    def span_by_node(self, node: NodeId) -> Optional[Span]:
        return self._span_by_node.get(node)

    def locus_by_node(self, node: NodeId) -> Optional[Locus]:
        """A locus is a moment or a span (§8), and a bound locus arrives as a
        node -- so getting from the name back to the thing has to ask both."""
        return self._moment_by_node.get(node) or self._span_by_node.get(node)

    def claims_about(self, proposition: NodeId) -> List[Entry]:
        """Every entry ever deposited about this proposition, in order. The
        deposit-side index, which §12 permits precisely because it indexes what
        was asserted and never what was derived."""
        return [e for _, _, e in self._claims.get(proposition, ())]

    def rests_on(self, e: Entry) -> List[Entry]:
        """What this entry was derived from, one hop, read from the graph rather
        than from the Python field. The two must agree, and `ugm.support` is what
        holds them to it -- an index is a re-implementation of what it indexes,
        which is the lesson `state` paid for."""
        out = []
        for node in self.g.instances_of(self.RESTS_ON):
            if self.g.member(node, 0) != e.node:
                continue
            found = self._by_node.get(self.g.member(node, 1))
            if found is not None:
                out.append(found)
        return out
