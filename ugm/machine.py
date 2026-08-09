"""The interpreter (§14, §16).

    Recall proposes. Match filters. Arbitrate commits. Only the last is total.

The step is *select a rule, apply it*, and object-rules and meta-rules must be
indistinguishable to it -- a flat tower, not a stacked one. Slice one has no
meta-rules yet, but the loop is written so that adding them adds rules rather
than branches.

Recall is not yet learned: it proposes everything. §15 is emphatic that this is
the step where experience belongs and where being wrong is recoverable, so the
seam is here and the learning is not.
"""

from typing import List, NamedTuple, Optional, Tuple

from .chain import Chain, Entry, Moment
from .channels import Arrival, Channels
from .gate import Frame, Gate
from .graph import Graph, NodeId
from .rules import (
    Application,
    Member,
    Rule,
    RuleSet,
    arbitrate,
    effective_grade,
    match,
    substitute,
)


class Step(NamedTuple):
    """What one tick did, and -- when it did nothing -- which silence it was.

    *Nothing applied* and *nothing came to mind* are different events (§15), and
    only the second should escalate. Slice one cannot yet tell them apart, since
    recall is exhaustive; the field exists so that the day it can, no caller has
    to change.
    """

    arrivals: int
    proposed: int
    matched: int
    applied: Optional[Application]
    wrote: Tuple[Entry, ...]
    state: str  # applied | quiescent | nothing-matched


class Machine:
    def __init__(self) -> None:
        self.g = Graph()
        self.chain = Chain(self.g)
        self.gate = Gate(self.g, self.chain)
        self.rules = RuleSet(self.g)
        self.channels = Channels(self.g)

        self.SAYS = self.g.atom("says")
        self.APPLIED = self.g.atom("applied")
        self.ARRIVED = self.g.atom("arrived")

        # The knowledge base is a channel like any other (§13). Reading it
        # faithfully is guaranteed; what it *says* -- the rules -- stays as
        # contestable as anything else, which is what `by(R, boss)` depends on.
        self.KB = self.channels.open("kb")

        # The one register (§10): which node the machinery is currently reasoning
        # in. The frame itself is an ordinary node; only the pointer is
        # privileged.
        self.focus: Frame = self.gate.frame(self.chain.root)

        self.selections = 0
        self.useful_writes = 0

    # -- the loop ---------------------------------------------------------

    def tick(self) -> Step:
        arrivals = self._intake()

        proposed = self._recall()
        applications: List[Application] = []
        for r in proposed:
            applications.extend(
                match(self.g, self.chain, r, self.focus.topic, self.focus.seat)
            )
        applications = [a for a in applications if self._would_change(a)]

        chosen = arbitrate(self.rules, applications)
        if chosen is None:
            return Step(
                arrivals,
                len(proposed),
                0,
                None,
                (),
                "quiescent" if arrivals == 0 else "nothing-matched",
            )

        self.selections += 1
        wrote = self._apply(chosen)
        self.useful_writes += len(wrote)
        return Step(arrivals, len(proposed), len(applications), chosen, wrote, "applied")

    def run(self, limit: int = 100) -> List[Step]:
        """Bounded, and it returns a result *and* a state -- because a search that
        stopped is not a search that found nothing (§9, §15)."""
        out: List[Step] = []
        for _ in range(limit):
            s = self.tick()
            out.append(s)
            if s.state != "applied":
                break
        return out

    # -- the four primitives ----------------------------------------------

    def _recall(self) -> List[Rule]:
        """Never complete, by design (§15). Exhaustive here, which is the
        deliberate-reasoning setting: recall with the budget removed."""
        return list(self.rules.rules)

    def _intake(self) -> int:
        """Drain the channels and stamp what arrived.

        What is written is that the channel said so -- never the content as a
        claim about the world. Believing it is a rule's job, and that rule can be
        argued with.
        """
        arrivals = self.channels.drain()
        for a in arrivals:
            utterance = self.g.rel(self.ARRIVED, a.channel, a.proposition)
            said = self.g.rel(self.SAYS, a.channel, a.proposition)
            self.gate.write(
                self.focus,
                said,
                a.sign,
                grade=a.grade,
                licence=utterance,
                source=a.channel,
            )
        return len(arrivals)

    def _apply(self, app: Application) -> Tuple[Entry, ...]:
        """Forward reading: apply the consequent's signs into the right moment.

        `implies` lands in the *same* moment -- the entry is derived, and retract
        the antecedent and it goes with it. `causes` lands in a *later* one -- the
        entry is asserted, and it persists. Water you have stopped heating stays
        boiled, which is why a zero-delay cause is still not an implication.
        """
        licence = self.g.rel(self.APPLIED, app.rule.node)
        if app.rule.connective == "causes":
            seat = self.chain.succeed(self.focus.seat, licence)
            self.focus = self.gate.frame(seat, purpose=self.focus.purpose)
        frame = self.focus

        wrote: List[Entry] = []
        for m in app.rule.consequent:
            grounded = substitute(self.g, m.pattern, app.bindings)
            wrote.append(
                self.gate.write(
                    frame,
                    grounded,
                    m.sign,
                    grade=effective_grade(m.grade, app.consumed),
                    licence=licence,
                    source=self.KB,  # the rule is the licence; the KB is the channel
                    consumed=app.consumed,
                )
            )
        return tuple(wrote)

    # -- helpers ----------------------------------------------------------

    def _would_change(self, app: Application) -> bool:
        """Quiescence: an application that restates what the chain already says is
        not a step. Without this the loop would reapply every rule forever, and
        *nothing left to do* would be unsayable."""
        for m in app.rule.consequent:
            grounded = substitute(self.g, m.pattern, app.bindings)
            if self.g.has_var(grounded):
                return False
            cur = self.chain.resolve(grounded, self.focus.topic, self.focus.seat)
            if cur is None or cur.sign != m.sign:
                return True
        return False

    # -- asking -----------------------------------------------------------

    def holds(self, proposition: NodeId, locus: Optional[Moment] = None) -> Optional[str]:
        locus = self.focus.topic if locus is None else locus
        return self.chain.holds(proposition, locus, self.focus.seat)

    def why(self, proposition: NodeId, locus: Optional[Moment] = None) -> List[str]:
        """*Why do you believe that, and on whose word?* -- R5.

        The trail is not a debugging aid: §12 makes it load-bearing for
        correctness, because a missing support link removes a weak link from the
        minimum and the conclusion becomes falsely confident.
        """
        locus = self.focus.topic if locus is None else locus
        e = self.chain.resolve(proposition, locus, self.focus.seat)
        if e is None:
            return []
        lines = [self._line(e)]
        for s in self.chain.trail(e):
            lines.append("  because " + self._line(s))
        return lines

    def _line(self, e: Entry) -> str:
        bits = [f"{e.sign}{self.g.show(e.proposition)} @{e.locus}"]
        bits.append(f"grade={e.grade}")
        if e.source is not None:
            bits.append(f"via {self.g.show(e.source)}")
        if e.licence is not None:
            bits.append(f"licensed by {self.g.show(e.licence)}")
        return ", ".join(bits)
