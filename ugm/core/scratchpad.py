"""The scratchpad (§4, §5).

There is one graph and it is the state. Nothing is computed from a history,
because there is no history: what the agent believes now is what is in the
graph now, and a retraction is a deletion rather than a later claim that wins.

A proposition on its own claims nothing. `boiling($w)` is in the graph as a
rule's stored pattern, and `heat(k)` may be in it as something a rule merely
mentions, so presence of a proposition cannot mean belief. What means belief is
an ANCHOR -- `believed(p)` -- a node of its own:

    boiling($w)              structure. Never believed.
    believed(boiling(k))     present = believed. Absent = not.

That is §14's use/mention distinction made structural instead of recorded: USE
is anchored, MENTION is not, and no flag on the writer has to be got right.

Three consequences, and they are the whole of why the chain went:

    assert     mint the anchor
    retract    DELETE the anchor. `p` survives as structure, which is correct --
               rules mention it -- and the state is back where it started, with
               no scar and no un-claim primitive.
    ignorance  absence. *Never considered* and *considered and dropped* are the
               same state, and that is honest: nothing here remembers.

A proposition has at most one anchor -- `note` looks before it mints, which is
where that invariant lives now that the graph interns nothing. Asserting
something already believed is not a second act; there is nowhere for a second
act to go -- though it MAY move the number below.

`p(a)` said twice is two propositions and so two anchors, which is the point:
two occasions. What cannot happen is two anchors on ONE proposition.

Intensity (docs/design/intensity-gates.md). Belief used to be a bare
presence/absence flag; every anchor now carries a NUMBER as well, and "on" --
what an antecedent member and `no` both ask about -- is "above zero". Nothing
about the anchor/occasion picture above changes: intensity rides beside it,
one float per anchor, and it is what makes `keep` (read without spending) and
"combine by max" (docs/design/intensity-gates.md's "First-cut defaults")
possible at the layer above this one (`Machine`/`attention.run`). The zero
end needs no separate state at all -- an anchor AT zero and no anchor read
the same to every rule, so "set to zero" is erasure, unchanged from today,
and nothing here has to represent "anchored but off".

See docs/design/scratchpad.md.
"""

from typing import Dict, List, Optional

from .graph import Graph, NodeId

#: What a plain `+p(x)` writes when nothing says otherwise -- "fully on",
#: and the number every occasion had, implicitly, before intensity existed.
#: Kept here rather than in `Gate` because it is the one number this file's
#: own callers (`note`, defaulted) need without an import.
ON = 1.0


class Scratchpad:
    """What is believed, which is what is anchored -- now at a strength."""

    def __init__(self, g: Graph) -> None:
        self.g = g
        # The anchor relation. One atom, taken from here by everything that
        # needs it: `atom` does not intern, so a second `g.atom("believed")`
        # would be a different node that no rule could match -- the
        # name-identity trap, which has cost this design four silent bugs.
        self.BELIEVED = g.atom("believed")
        self.writes = 0
        self.erasures = 0
        # anchor -> its intensity. Keyed on the ANCHOR (the `believed(p)`
        # instance), not on `p` itself, because occasions survive: `p(a)`
        # believed twice is two anchors, and each carries its own number
        # (docs/design/intensity-gates.md, "Occasions survive"). An anchor
        # not in this dict was minted before intensity existed anywhere but
        # this file's own tests, or is a stale key after an erase this dict
        # forgot to drop -- `erase` below is what keeps that from happening.
        self._intensity: Dict[NodeId, float] = {}
        # Which relations a node is currently spoken of under, counted.
        #
        # *What is believed about `goblin1` right now* -- and it has to be the
        # scratchpad's answer rather than the graph's, because the graph holds
        # every proposition anything ever mentioned. A node the agent knew
        # about last week and holds nothing about now is not a node any rule is
        # going to be about, and that is the half attention needs.
        #
        # Maintained here, where belief is made, rather than scanned for: the
        # rule that what is read off a state is maintained where the state is.
        # Counted rather than a set, because an erasure has to be exact.
        self._rels: Dict[NodeId, Dict[NodeId, int]] = {}

    # -- writing ----------------------------------------------------------

    def note(self, proposition: NodeId, intensity: float = ON) -> NodeId:
        """Believe `proposition`, AT `intensity`. Returns its anchor.

        Callers should not reach this directly: `Gate.write` is the one place a
        belief enters, because that is where the hooks are.

        Minting is unchanged: an already-anchored proposition gets the
        existing anchor back rather than a second one, because `rel` mints
        now and a second anchor on one belief is not a thing `erase` could
        ever take back one-for-one. What IS new is that the existing anchor's
        NUMBER moves to `intensity` regardless -- a second `write` on one
        occasion is a recharge, and a caller that meant merely to check
        whether something is believed was never calling `note` to do it
        (`holds`/`anchor` below do not write).
        """
        got = self.anchor(proposition)
        if got is not None:
            self._intensity[got] = intensity
            return got
        self.writes += 1
        self._mention(proposition, +1)
        anchor = self.g.rel(self.BELIEVED, proposition)
        self._intensity[anchor] = intensity
        return anchor

    def erase(self, proposition: NodeId) -> bool:
        """Stop believing `proposition`. True if there was anything to stop.

        Only the ANCHOR is deleted. Deleting the proposition would take a node
        other things still mention out of the graph, and `probes/erase.py`
        measured what that costs: deleting an individual hides nothing, because
        nothing removes a node from the buckets of the nodes that name it. The
        anchor is the one safe deletion target and this is the only deleter.
        """
        anchor = self.anchor(proposition)
        if anchor is None:
            return False
        self.erasures += 1
        self._mention(proposition, -1)
        self.g.delete(anchor)
        # Dropped rather than left to rot: `anchor` cannot be minted again --
        # `g.rel` never reuses a deleted node's id -- so a stale entry here
        # would sit forever, and `_intensity` growing without bound the way
        # an unbounded cache does is the one failure mode a dict this small
        # can still have.
        self._intensity.pop(anchor, None)
        return True

    def intensity(self, anchor: NodeId) -> float:
        """This ANCHOR's number. `ON` for one this dict never heard of --
        which is only ever a caller's own bug (an anchor this scratchpad
        did not mint) rather than a live case, since every path that mints
        one records a number in the same breath `note` does."""
        return self._intensity.get(anchor, ON)

    def occasion_intensity(self, proposition: NodeId) -> float:
        """`intensity`, but resolved through `occasion` first -- the number
        of whatever occasion of this SHAPE is believed, for a caller (a rule
        reading `intensity($x) as $n`) that has a proposition rather than an
        anchor in hand. `0.0` when nothing of the shape is believed at all,
        which is the honest reading of *how on is this* for a thing that is
        not on."""
        occ = self.occasion(proposition)
        anchor = self.anchor(occ)
        return self.intensity(anchor) if anchor is not None else 0.0

    def _mention(self, proposition: NodeId, d: int) -> None:
        """Move the `relations_of` counts for one proposition's arguments.

        The arguments only, one deep: `on(a, b)` says something about `a` and
        about `b`, and `on` itself is what it says rather than a thing spoken
        about.
        """
        rel = self.g.relation_of(proposition)
        if rel is None:
            return
        if self.g._identity:
            rel = self.g.identity_of(rel)
        for m in self.g.members(proposition):
            held = self._rels.setdefault(m, {})
            n = held.get(rel, 0) + d
            if n > 0:
                held[rel] = n
            else:
                # Dropped rather than left at zero, so `relations_of` is a
                # plain read and the dict does not grow a tail of relations
                # nothing is spoken of under any more.
                held.pop(rel, None)
                if not held:
                    self._rels.pop(m, None)

    def relations_of(self, node: NodeId) -> List[NodeId]:
        """The relations this node is currently believed to stand in, in the
        order they were first claimed."""
        return list(self._rels.get(node, ()))

    # -- reading ----------------------------------------------------------

    def anchor(self, proposition: NodeId) -> Optional[NodeId]:
        """This proposition's anchor if it has one, without making it.

        `note` cannot answer this: asking would answer itself.

        The ARGUMENT index, not `find_rel`. `find_rel` asks about a shape, and
        `believed(p)` and `believed(q)` have one shape whenever `p` and `q` do
        -- so asking it here reports one occasion believed because another one
        is. Belief is per node, which is the whole of *two loves between the
        same pair are two things*, and the argument index is the one keyed on
        the node rather than on what it is made of.
        """
        got = self.g.instances_with(self.BELIEVED, 0, proposition)
        return got[0] if got else None

    def holds(self, proposition: NodeId) -> bool:
        """Is this believed? One dict lookup, and it is the whole of belief."""
        return self.anchor(proposition) is not None

    def holds_any(self, proposition: NodeId) -> bool:
        """Is ANY instance of this proposition believed?

        `holds` asks about one node, which is right when the node is the
        subject -- an entity, a relationship someone is making claims about.
        Absence is not that question. `no p($x)` asks whether anything says
        `p(x)`, and a second instance of `p(x)` sitting anchored beside the
        canonical one makes it say so.
        """
        return any(self.anchor(p) is not None for p in self.g.like(proposition))

    def occasion(self, proposition: NodeId) -> NodeId:
        """The believed node of this shape, given one that may only describe it.

        `proposition` itself when it is believed, which is every caller that
        matched its node. Otherwise the oldest occasion saying the same thing,
        and `proposition` unchanged when nothing does.

        This is where a caller holding a SHAPE meets the engine holding
        OCCASIONS. `m._attend(kb.term("intake(e2, mary)"))` names a term from
        outside and gets a node minted on the spot, which is attention on a
        thing nobody believes and no rule can match -- so the claim lands
        nowhere. It was the same node while `rel` interned, which is why
        nothing had to say this before.
        """
        if self.holds(proposition):
            return proposition
        for other in self.g.like(proposition):
            if self.holds(other):
                return other
        return proposition

    def believed(self) -> List[NodeId]:
        """Every believed proposition, newest first.

        Mint order reversed. An erased anchor leaves `_by_rel` when it is
        deleted, so this never reports something erased; and re-asserting an
        erased belief mints a fresh anchor, which puts it back at the newest
        end where a re-assertion belongs.
        """
        return [self.g.member(a, 0)
                for a in reversed(self.g.instances_of(self.BELIEVED))]

    def anchors(self) -> List[NodeId]:
        """The anchors themselves, newest first. For a reader that wants the
        node rather than what it is about."""
        return list(reversed(self.g.instances_of(self.BELIEVED)))
