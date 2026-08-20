"""Frames and the gate (§13).

A rule cannot name a locus -- it is generic, and a locus is anchored.

See docs/design/gate.md.
"""

from typing import Callable, List, Optional, Tuple

from .chain import PLUS, Chain, Entry, Moment
from .graph import Graph, NodeId


class Frame:
    """A reasoning in progress, as a node -- which is R7 discharged for the
    machinery itself. Frames form a forest, not a stack: two hypotheses under
    comparison are siblings, both alive, neither the caller of the other. What
    looks like a stack is the ancestor path of whichever frame is in focus.
    """

    def __init__(
        self,
        node: NodeId,
        seat: Moment,
        topic: Moment,
        parent: Optional["Frame"] = None,
        purpose: Optional[NodeId] = None,
        wrap: Optional[NodeId] = None,
    ) -> None:
        self.node = node
        self.seat = seat
        self.topic = topic
        self.parent = parent
        self.purpose = purpose
        # What a conclusion is re-wrapped in on the way out (§16). Held on the
        # frame rather than in a call stack, because there is no call: reasoning
        # inside a supposition is ordinary ticks of the ordinary loop, and the
        # frame has to survive between them.
        self.wrap = wrap
        # Where the frame BEGAN, which stops being the same as `seat` the moment
        # a `causes` rule applies inside it and the frame advances. Discharge
        # needs the beginning -- it collects every moment from here to now -- and
        # reading it off `seat` silently carried out only the last one.
        self.origin = seat
        self.children: List["Frame"] = []
        self.state: Optional[str] = None  # discharged | exhausted | abandoned
        self.carried: List["Entry"] = []  # what crossed out, wrapped (§17)
        if parent is not None:
            parent.children.append(self)

    def ancestry(self) -> List["Frame"]:
        """Derived, not maintained -- there is nothing to push (§4)."""
        out, f = [], self
        while f is not None:
            out.append(f)
            f = f.parent
        return out

    def __repr__(self) -> str:
        return f"Frame(seat={self.seat}, topic={self.topic})"


class Gate:
    """The one place a stamp is applied.

        Proposition and sign come from the rule.
        Locus, deposit, licence and source come from the frame and the channel.
        A rule may not name the second four.

    Two properties fall out rather than being enforced. Hypothetical containment
    is structural, because the locus was never the rule's to give. And forgery
    stops being a category: nothing is prohibited, everything is stamped.
    """

    def __init__(self, g: Graph, chain: Chain) -> None:
        self.g = g
        self.chain = chain
        self.FRAME = g.atom("frame")
        self.PROCESS = g.atom("process")
        # §17's *every seat move is a write*, which §21 listed as owed. See
        # `reseat`.
        self.MOVED = g.atom("moved")
        self.writes = 0
        # Effects leave the agent HERE, not in a phase of the loop.
        # → docs/design/gate.md#effects-leave-the-agent-here-not-in-a-phase-of
        self.on_write: List[Callable[["Frame", Entry], None]] = []

        # §19's carve-out, and the shape of it is the argument: Recall may be
        # incomplete about what to do. It may not be incomplete about what you
        # must not do.
        # → docs/design/gate.md#19-s-carve-out-and-the-shape-of-it-is-the-argu
        self.veto: List[Callable[["Frame", NodeId, str], Optional[NodeId]]] = []
        # What a refusal IS, and the reason it is gate vocabulary rather than a
        # machine's: it is the record of a gate decision, in the same family as
        # the stamp. A refusal that wrote nothing would be a fourth silent
        # decline -- the agent would not act, and would not know it had not.
        self.REFUSED = g.atom("refused")
        self.refusals = 0

    def frame(
        self,
        seat: Moment,
        topic: Optional[Moment] = None,
        parent: Optional[Frame] = None,
        purpose: Optional[NodeId] = None,
        wrap: Optional[NodeId] = None,
    ) -> Frame:
        """A frame is `frame(seat, topic)` -- two ordered members, structurally
        identical to a span. The engine learns no new relation name from it; what
        it needs is one register, which is the machine's `focus`.
        """
        topic = seat if topic is None else topic
        if not seat.at_or_after(topic):
            # A seat that is not at or after its topic is as meaningless as an
            # inverted span, so the check belongs here, where the mistake is
            # still attributable.
            raise ValueError(f"frame seat {seat} precedes its topic {topic}")
        # `instance`, not `rel`: two processes reasoning at the same seat about
        # the same topic are two frames, and §17 needs each to be a node other
        # facts can be about -- a purpose, a parent, a state.
        node = self.g.instance(self.FRAME, seat.node, topic.node)
        return Frame(node, seat, topic, parent, purpose, wrap)

    def reseat(self, frame: Frame, seat: Moment,
               licence: Optional[NodeId] = None,
               source: Optional[NodeId] = None) -> None:
        """Move a frame to a later seat, and SAY SO. What it is for: the agent's

        own frame must be able to advance while the register is pointing
        somewhere else, because the world does not stop talking while the agent
        is reasoning under a hypothesis. ⚠ And it is not derivable from the
        chain, which is why a fact about a moment is the only place it can
        live.

        See docs/design/gate.md#reseat.
        """
        follow_topic = frame.topic is frame.seat
        was = frame.seat
        frame.seat = seat
        if follow_topic:
            frame.topic = seat
        frame.node = self.g.instance(self.FRAME, frame.seat.node, frame.topic.node)
        self.write(frame, self.g.rel(self.MOVED, was.node, seat.node), PLUS,
                   licence=licence, source=source)

    def write(
        self,
        frame: Frame,
        proposition: NodeId,
        sign: str,
        licence: Optional[NodeId] = None,
        source: Optional[NodeId] = None,
        consumed: Tuple[Entry, ...] = (),
        locus: Optional[Moment] = None,
        mention: bool = False,
    ) -> Entry:
        """Mint one entry. `locus` is the consequent's bound locus when it has
        one (§8); otherwise the frame's topic supplies it.

        `mention` is the use/mention distinction, and it is needed the moment
        rules become data. `+ant(<R>, heat(?a, ?w))` is a **ground** claim about a
        rule, which happens to name a node that contains variables. It is not a
        generic claim, and refusing it would make rules unspeakable-about -- but
        structurally the two are the same shape, so nothing can tell them apart.
        What tells them apart is *who is writing*: the machinery reifying a rule
        is mentioning, a rule's consequent is using. That is §13's split again,
        and it is why this is a parameter the gate takes rather than a property
        of the proposition.
        """
        if not mention and self.g.has_var(proposition):
            raise ValueError(
                f"cannot deposit a generic proposition: {self.g.show(proposition)}"
            )
        # The veto runs before the deposit, so a forbidden entry never exists --
        # not even briefly, and not for `on_write` to see. That matters because
        # `_dispatch` is an `on_write` hook: refusing here is what keeps the act
        # inside the agent, rather than emitting it and regretting it.
        for vetoer in self.veto:
            forbidding = vetoer(frame, proposition, sign)
            if forbidding is None:
                continue
            self.refusals += 1
            return self.chain.deposit(
                seat=frame.seat,
                locus=frame.topic if locus is None else locus,
                proposition=self.g.rel(
                    self.REFUSED, proposition, self.chain.SIGN[sign], forbidding
                ),
                sign="+",
                licence=forbidding,
                source=source,
                consumed=tuple(x.node for x in consumed),
                mention=True,
            )

        self.writes += 1
        e = self.chain.deposit(
            seat=frame.seat,
            locus=frame.topic if locus is None else locus,
            proposition=proposition,
            sign=sign,
            licence=licence,
            source=source,
            consumed=tuple(e.node for e in consumed),
            mention=mention,
        )
        for hook in self.on_write:
            hook(frame, e)
        return e
