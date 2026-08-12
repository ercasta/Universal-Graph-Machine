"""Channels (§13).

Every entry names where it arrived from, and that has two layers which must not
be fused:

    channel     the intake path -- this socket, this sensor, the knowledge base.
                Mechanically observed, so it cannot be wrong, in the way a sensor
                cannot misreport its own reading.

    authority   who is taken to have spoken, and what their word is worth.
                An ordinary claim, gradeable and defeasible.

Fusing them would make authority unforgeable by fiat, so that anyone reaching the
right socket would thereby be the boss. The knowledge base is a channel like any
other: reading it faithfully is guaranteed, and what it *says* stays contestable,
which is what `by(R, boss)` and `overrides(R1, R2)` depend on.
"""

from typing import Callable, List, NamedTuple, Optional

from .graph import Graph, NodeId


class Arrival(NamedTuple):
    channel: NodeId
    proposition: NodeId
    sign: str
    grade: str


class Channels:
    """The world enters here, and it does not wait for a tick.

    Intake used to be the first line of the loop: each tick drained a queue and
    stamped what had arrived. Nothing needed it to be a phase. An arrival is an
    external event, and an external event is not something the agent *does* --
    so delivery writes immediately, through the gate, and the loop has one fewer
    branch.

    The queue survives only for arrivals delivered before anything is listening,
    which is the ordinary case in a constructor.
    """

    def __init__(self, g: Graph) -> None:
        self.g = g
        self.CHANNEL = g.atom("channel")
        self._pending: List[Arrival] = []
        self._known: List[NodeId] = []
        # Set by the machine. Not a second register and not a phase: it is the
        # same shape as the gate's write hooks -- the boundary calling in, rather
        # than the loop reaching out.
        self.sink: Optional[Callable[[Arrival], None]] = None
        self.arrived = 0  # since the last tick, so a silence can still be named

    def open(self, name: str) -> NodeId:
        c = self.g.atom(name)
        self._known.append(c)
        return c

    def known(self) -> List[NodeId]:
        """Every channel opened or used. Insertion-ordered like everything else
        here (§3), so anything that iterates them breaks ties the same way twice."""
        return self._known

    def use(self, node: NodeId) -> NodeId:
        """Treat an existing node as a channel.

        A channel is an ordinary node, so a surface that has already coined
        `user` while writing `says(user, ...)` must end up with the *same* node
        when it opens the channel -- otherwise the rule that reads utterances and
        the intake that writes them would be talking about two different sockets
        with one name.
        """
        if node not in self._known:
            self._known.append(node)
        return node

    def deliver(
        self, channel: NodeId, proposition: NodeId, sign: str = "+", grade: str = "certain"
    ) -> None:
        """Deliver an arrival. Nothing is believed yet: what arrives is that the
        channel said so, and turning that into a claim about the world is a rule
        the agent can be asked about."""
        a = Arrival(channel, proposition, sign, grade)
        self.arrived += 1
        if self.sink is None:
            self._pending.append(a)
            return
        self.sink(a)

    def drain(self) -> List[Arrival]:
        """Whatever was delivered before anyone was listening."""
        out = list(self._pending)
        self._pending.clear()
        return out

    def since_last_tick(self) -> int:
        n, self.arrived = self.arrived, 0
        return n

    def pending(self) -> int:
        return len(self._pending)
