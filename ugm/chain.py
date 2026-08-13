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

from typing import Dict, List, NamedTuple, Optional, Tuple

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
    locus: "Moment"
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
        licence: Optional[NodeId],
    ) -> None:
        self.node = node
        self.predecessor = predecessor
        self.licence = licence
        self.delta: List[Entry] = []
        self.depth = 0 if predecessor is None else predecessor.depth + 1

    def ancestors(self) -> List["Moment"]:
        """This moment and its predecessors, newest first."""
        out, m = [], self
        while m is not None:
            out.append(m)
            m = m.predecessor
        return out

    def at_or_after(self, other: "Moment") -> bool:
        """Is `other` this moment or one of its ancestors?

        A depth comparison is not enough once anything forks -- and supposing
        forks by construction. Two moments on different branches can share a
        depth while neither is on the other's walk, and a depth test would let a
        claim made inside one supposition answer a question asked inside its
        sibling. That is the containment property, so it has to be ancestry.
        """
        m: Optional["Moment"] = self
        while m is not None:
            if m is other:
                return True
            m = m.predecessor
        return False

    def __repr__(self) -> str:
        return f"M{self.depth}"


class Chain:
    """The history, and the reads over it."""

    def __init__(self, g: Graph) -> None:
        self.g = g
        self.ENTRY = g.atom("entry")
        self.MOMENT = g.atom("moment")
        # The structural mirror (§6). `pred` and `in_delta` are plain relation
        # instances, not entries: nobody asserted them, they cannot be denied,
        # dated or attributed. That is exactly §12's skeleton, and it is what
        # makes them matchable by a stratum-0 rule.
        self.PRED = g.atom("pred")
        self.IN_DELTA = g.atom("in_delta")
        self.IS_MOMENT = g.atom("moment_of")
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
        # Sign atoms live here rather than in the rule set, because an entry's
        # third member is a sign and the chain is what mints entries. Everything
        # else takes them from here: `atom` does not intern, so a second
        # `g.atom("+")` would be a different node that no rule could match --
        # the name-identity trap, which has cost this design four silent bugs.
        self.SIGN = {s: g.atom(s) for s in (PLUS, MINUS, UNSURE)}
        self.root = Moment(g.instance(self.MOMENT), None, None)
        g.rel(self.IS_MOMENT, self.root.node)
        self.moments: List[Moment] = [self.root]
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
        m = Moment(self.g.instance(self.MOMENT), predecessor, licence)
        self.g.rel(self.IS_MOMENT, m.node)
        self.g.rel(self.PRED, m.node, predecessor.node)
        self.moments.append(m)
        return m

    def deposit(
        self,
        seat: Moment,
        locus: Moment,
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
        self, proposition: NodeId, locus: Moment, seat: Optional[Moment] = None
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
        self, proposition: NodeId, locus: Moment, seat: Optional[Moment] = None
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
