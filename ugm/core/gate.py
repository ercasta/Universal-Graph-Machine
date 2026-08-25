"""The gate (§13).

The one place a belief enters or leaves. Two acts, and they are exact
opposites: `write` mints an anchor, `erase` deletes one.

What the gate used to be is worth saying, because most of it is gone. It
stamped every deposit with a licence, a source and a landing place, and it held
a list of vetoes any of which could refuse a write. The licence and the source
were the derivation record, and the derivation record went with the chain; the
vetoes were the engine deciding what a corpus may not say, which is the
corpus's business and not the engine's. What is left is the seam: one function
in, one function out, and the hooks that let something happen when a belief
changes.

See docs/design/gate.md.
"""

from typing import Callable, List

from .graph import Graph, NodeId
from .scratchpad import ON, Scratchpad


class Gate:
    """The one door in and out of belief."""

    def __init__(self, g: Graph, pad: Scratchpad) -> None:
        self.g = g
        self.pad = pad
        self.writes = 0
        self.erasures = 0
        # Effects leave the agent HERE, not in a phase of the loop. An
        # actuator, an answerer, a delta record: each is a function called when
        # a belief lands, so there is no phase in which acting happens and no
        # rule can act without going through this.
        self.on_write: List[Callable[[NodeId], None]] = []
        # ...and the same for a belief that goes. Erasure was once the one
        # thing the agent could do that left nothing anyone could read: it went
        # straight to `Graph.delete`, below every hook. This is where that
        # stops.
        self.on_erase: List[Callable[[NodeId], None]] = []

    def write(self, proposition: NodeId, generic: bool = False,
              intensity: float = ON) -> NodeId:
        """Believe `proposition` AT `intensity`, and return its anchor.

        `generic` is the one escape, and it is needed the moment rules become
        data. `ant(<R>, heat($a, $w))` is a **ground** claim about a rule, which
        happens to name a node that contains variables. It is not a generic
        claim, and refusing it would make rules unspeakable-about -- but
        structurally the two are the same shape, so nothing can tell them
        apart. What tells them apart is *who is writing*: the machinery
        reifying a rule knows it is naming one, and a rule's consequent does
        not.

        `intensity` (docs/design/intensity-gates.md) is the general write the
        design retires `-p` in favour of: every ordinary `+p(x)` still calls
        this at the default (`ON`, "fully on"), and a rule that wants to say
        HOW on -- the runaway guard reading its own count and writing it back
        up by one -- calls it with a number instead. There is no separate
        "set to zero" here: zero is what `erase` already means (below), and a
        caller computing a write of zero is expected to call that instead,
        the same way `-p(x)` reads as erasure rather than as this method
        handed a zero.
        """
        if not generic and self.g.has_var(proposition):
            raise ValueError(
                f"cannot believe a generic proposition: {self.g.show(proposition)}"
            )
        self.writes += 1
        anchor = self.pad.note(proposition, intensity)
        for hook in self.on_write:
            hook(proposition)
        return anchor

    def erase(self, proposition: NodeId) -> bool:
        """Stop believing `proposition`. True if it was believed.

        The proposition itself is never deleted -- only its anchor. It survives
        as structure, which is correct, because rules mention it and a rule
        that lost the node it names would stop matching for a reason nothing
        could state.

        Handed a node nothing anchors, this erases the OLDEST occasion of the
        same shape. A caller that matched its node -- `-$hit`, `-p($x)` -- hands
        the occasion it means and this never fires. A caller that WROTE one to
        say which proposition -- a ground `-p(a)`, where there is no binding to
        carry an occasion -- means *stop believing p(a)*, and the shape is all
        it said. Oldest first because it is the one thing here that is not a
        choice: it is the occasion everything else already saw.

        One occasion, not all of them, because `write` writes one. `p(a)`
        believed twice is two occasions and a single `-p(a)` spends a single
        one.
        """
        proposition = self.pad.occasion(proposition)
        if not self.pad.erase(proposition):
            return False
        self.erasures += 1
        for hook in self.on_erase:
            hook(proposition)
        return True
