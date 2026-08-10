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

GRADES = ("unknown", "unlikely", "possible", "likely", "certain")


def weaker(a: str, b: str) -> str:
    """Ordinal composition by weakest link (§12). Sound down a chain; §12 records
    that it is silent about convergence, where belief ought to rise."""
    return a if GRADES.index(a) <= GRADES.index(b) else b


class Entry(NamedTuple):
    """The unit of assertion. Three members, and never a fourth: grade, licence
    and source are ordinary facts about the entry (§5)."""

    node: NodeId  # the entry's own identity, so other facts can be about it
    locus: "Moment"
    proposition: NodeId
    sign: str
    grade: str
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
        # Sign atoms live here rather than in the rule set, because an entry's
        # third member is a sign and the chain is what mints entries. Everything
        # else takes them from here: `atom` does not intern, so a second
        # `g.atom("+")` would be a different node that no rule could match --
        # the name-identity trap, which has cost this design four silent bugs.
        self.SIGN = {s: g.atom(s) for s in (PLUS, MINUS, UNSURE)}
        self.root = Moment(g.instance(self.MOMENT), None, None)
        g.rel(self.IS_MOMENT, self.root.node)
        self.moments: List[Moment] = [self.root]

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
        grade: str = "certain",
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
        e = Entry(node, locus, proposition, sign, grade, licence, source, consumed, mention)
        seat.delta.append(e)
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
        # Newest deposit first, and newest-within-a-moment first, so an
        # equal-locus tie is already settled by the order of the walk.
        for m in seat.ancestors():
            for e in reversed(m.delta):
                if e.proposition != proposition:
                    continue
                if not locus.at_or_after(e.locus):  # inheritance: locus or earlier
                    continue
                if best is None or e.locus.depth > best.locus.depth:
                    best = e
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
        for m in reversed(self.moments):
            for e in reversed(m.delta):
                if e.node == node:
                    return e
        return None
