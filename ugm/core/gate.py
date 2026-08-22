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
        # ...and what an ERASURE is, gate vocabulary for the same reason
        # `refused` is: it is the record of a gate decision. `Graph.delete` sits
        # BELOW the gate -- no entry, no licence, no trail, no hooks -- so an
        # erasure was the one thing the agent could do that left nothing anyone
        # could read or argue with. This is where that stops.
        self.ERASED = g.atom("erased")
        self.erasures = 0

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

    def erase(
        self,
        node: NodeId,
        licence: NodeId,
        entity: Optional[NodeId] = None,
        source: Optional[NodeId] = None,
        consumed: Tuple[Entry, ...] = (),
    ) -> Entry:
        """Take `node` out of the graph, and say so on the log.

        Three things follow from putting this here rather than on `Graph`.

        **The licence is required.** An erasure with no reason is the case this
        exists to remove: `Graph.delete` could always be called, and afterwards
        nothing anywhere said that anything had gone, let alone why. `refused`
        is the precedent for the shape -- it carries `forbidding` as a member
        AND as the entry's licence -- so a reader can ask either way, and
        neither reading is the privileged one.

        **What is deleted and what is NAMED are two different nodes.** Only an
        anchor is ever a safe deletion target (`probes/erase.py`, check 4: a
        deleted individual hides nothing, because nothing removes a node from
        the buckets of the nodes that mention it). What the log names is the
        **entity** -- the desire, not its description -- because a term is a
        rigid designator and a premise is a description. `entity` defaults to
        `node` for the case where they coincide, and the caller that knows
        better says so.

        **A refused erasure does not happen.** The record goes through `write`,
        so it meets the vetoes first; if one refuses, the deletion is not
        performed and the refusal is what lands. An erasure that could not be
        recorded is an erasure that did not occur -- which is the whole content
        of *through the gate*, and is not a property `Graph.delete` could have
        had.
        """
        entity = node if entity is None else entity
        e = self.write(
            self.g.rel(self.ERASED, entity, licence), "+",
            licence=licence, source=source, consumed=consumed, mention=True,
        )
        if self.g.relation_of(e.proposition) is self.REFUSED:
            return e
        self.erasures += 1
        self.g.delete(node)
        return e
