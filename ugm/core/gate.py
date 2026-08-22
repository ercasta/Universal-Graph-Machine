"""The gate (§13).

See docs/design/gate.md.
"""

from typing import Callable, List, Optional, Tuple

from .chain import Chain, Entry
from .graph import Graph, NodeId


class Gate:
    """The one place a stamp is applied.

        Proposition and sign come from the rule.
        Licence and source come from the caller and the channel.
        Where it lands comes from the chain's own end.
        A rule may not name any of the last three.

    One property falls out rather than being enforced: forgery is not a
    category, because nothing is prohibited and everything is stamped. The other
    one -- hypothetical containment is structural, because the locus was never
    the rule's to give -- went with the locus, and `learning/practice.py` is
    where containment is now an ordinary premise instead.
    """

    def __init__(self, g: Graph, chain: Chain) -> None:
        self.g = g
        self.chain = chain
        self.writes = 0
        # Effects leave the agent HERE, not in a phase of the loop.
        # → docs/design/gate.md#effects-leave-the-agent-here-not-in-a-phase-of
        self.on_write: List[Callable[[Entry], None]] = []

        # §19's carve-out, and the shape of it is the argument: Recall may be
        # incomplete about what to do. It may not be incomplete about what you
        # must not do.
        # → docs/design/gate.md#19-s-carve-out-and-the-shape-of-it-is-the-argu
        self.veto: List[Callable[[NodeId, str], Optional[NodeId]]] = []
        # What a refusal IS, and the reason it is gate vocabulary rather than a
        # machine's: it is the record of a gate decision, in the same family as
        # the stamp. A refusal that wrote nothing would be a fourth silent
        # decline -- the agent would not act, and would not know it had not.
        self.REFUSED = g.atom("refused")
        self.refusals = 0

    def write(
        self,
        proposition: NodeId,
        sign: str,
        licence: Optional[NodeId] = None,
        source: Optional[NodeId] = None,
        consumed: Tuple[Entry, ...] = (),
        mention: bool = False,
    ) -> Entry:
        """Mint one entry.

        `mention` is the use/mention distinction, and it is needed the moment
        rules become data. `+ant(<R>, heat($a, $w))` is a **ground** claim about a
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
        # The veto runs before the deposit, so a refused entry never exists --
        # not even briefly, and not for `on_write` to see. That matters because
        # `_dispatch` is an `on_write` hook: refusing here is what keeps the act
        # inside the agent, rather than emitting it and regretting it.
        for vetoer in self.veto:
            forbidding = vetoer(proposition, sign)
            if forbidding is None:
                continue
            self.refusals += 1
            return self.chain.deposit(
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
            proposition=proposition,
            sign=sign,
            licence=licence,
            source=source,
            consumed=tuple(e.node for e in consumed),
            mention=mention,
        )
        for hook in self.on_write:
            hook(e)
        return e
