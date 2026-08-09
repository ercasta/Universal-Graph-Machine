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

from typing import List, NamedTuple, Optional

from .graph import Graph, NodeId


class Arrival(NamedTuple):
    channel: NodeId
    proposition: NodeId
    sign: str
    grade: str


class Channels:
    """Intake is part of the loop: each tick drains what has arrived, stamps it,
    then reasons. That makes arrival ordering explicit, and gives surprise a
    single place where the world enters."""

    def __init__(self, g: Graph) -> None:
        self.g = g
        self.CHANNEL = g.atom("channel")
        self._pending: List[Arrival] = []
        self._known: List[NodeId] = []

    def open(self, name: str) -> NodeId:
        c = self.g.atom(name)
        self._known.append(c)
        return c

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
        """Queue an arrival. Nothing is believed yet: what arrives is that the
        channel said so, and turning that into a claim about the world is a rule
        the agent can be asked about."""
        self._pending.append(Arrival(channel, proposition, sign, grade))

    def drain(self) -> List[Arrival]:
        out = list(self._pending)
        self._pending.clear()
        return out

    def pending(self) -> int:
        return len(self._pending)
