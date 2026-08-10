"""Frames and the gate (§13).

A rule cannot name a locus -- it is generic, and a locus is anchored. The frame
is what the machinery supplies one from:

    seat    the moment its writes are deposited in     -- where I am standing
    topic   the locus its writes are stamped with      -- what I am about

Normally they coincide. They come apart exactly twice: reasoning about the past,
where the topic is earlier than the seat, and reasoning under a supposition,
where the seat is inside it.

The requirement is narrower than a prohibition on rules writing:

    No write bypasses the stamp.

What must be impossible is an entry whose provenance is absent or false. An entry
a rule caused to exist is not forgery -- it arrives through the gate and leaves it
stamped with the rule that caused it, which is the ordinary record. That is what
lets `the user says it is raining` become `it is raining` by a rule the agent can
be asked about, rather than by a hard-wired intake nobody can argue with.
"""

from typing import Callable, List, Optional, Tuple

from .chain import Chain, Entry, Moment
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
        self.writes = 0
        # Effects leave the agent HERE, not in a phase of the loop. §16 already
        # places action dispatch at the write -- *the one place effects leave the
        # agent, where the set is small and known* -- and §19 puts the
        # prohibition check in the same place for the same reason. An
        # implementation that polls for intents once a tick has moved that
        # decision into control flow, where nothing can override it.
        #
        # These are Python callables, which is honest debt: §21 records that the
        # bundle should be rules, and a hook is not one.
        self.on_write: List[Callable[["Frame", Entry], None]] = []

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
        it needs is one register, which is the machine's `focus`."""
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

    def reseat(self, frame: Frame, seat: Moment) -> None:
        """Move a frame to a later seat.

        §17 says every seat move is a write, and this one is not yet recorded as
        an entry -- noted in §21 rather than hidden. What it is for: the agent's
        own frame must be able to advance while the register is pointing
        somewhere else, because the world does not stop talking while the agent
        is reasoning under a hypothesis.

        The frame node is re-minted, so `frame(seat, topic)` keeps saying where
        the frame is rather than where it began.
        """
        follow_topic = frame.topic is frame.seat
        frame.seat = seat
        if follow_topic:
            frame.topic = seat
        frame.node = self.g.instance(self.FRAME, frame.seat.node, frame.topic.node)

    def write(
        self,
        frame: Frame,
        proposition: NodeId,
        sign: str,
        grade: str = "certain",
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
        self.writes += 1
        e = self.chain.deposit(
            seat=frame.seat,
            locus=frame.topic if locus is None else locus,
            proposition=proposition,
            sign=sign,
            grade=grade,
            licence=licence,
            source=source,
            consumed=tuple(e.node for e in consumed),
            mention=mention,
        )
        for hook in self.on_write:
            hook(frame, e)
        return e
