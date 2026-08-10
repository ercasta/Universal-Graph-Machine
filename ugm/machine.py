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

from .chain import MINUS, PLUS, UNSURE, Chain, Entry, Moment
from .channels import Arrival, Channels
from .gate import Frame, Gate
from .graph import Graph, NodeId
from .rules import (
    IMPLIES,
    Application,
    Member,
    Rule,
    RuleSet,
    arbitrate,
    defeat,
    effective_grade,
    match,
    unify,
    current_state,
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
        self.rules = RuleSet(self.g, self.chain)
        self.channels = Channels(self.g)

        self.SAYS = self.g.atom("says")
        self.APPLIED = self.g.atom("applied")
        self.ARRIVED = self.g.atom("arrived")
        self.EMITTED = self.g.atom("emitted")
        self.UTTERANCE = self.g.atom("utterance")
        # §14: the vocabulary a rule uses to speak about a rule.
        self.RULE = self.g.atom("rule")
        self.CONN = self.g.atom("conn")
        self.ANT = self.g.atom("ant")
        self.CON = self.g.atom("con")
        self.REIFIED = self.g.atom("reified")
        self.SUPPOSING = self.g.atom("supposing")
        self.CONCLUDED = self.g.atom("concluded")
        self.SUPPOSE = self.g.atom("suppose")
        self.GOAL = self.g.atom("goal")
        self.WANTED = self.g.atom("wanted")
        self.ACHIEVED = self.g.atom("achieved")
        self.BLOCKED = self.g.atom("blocked")
        self.PLAN = self.g.atom("plan")
        self.SUBGOAL = self.g.atom("subgoal")
        self.BINDS = self.g.atom("binds")
        self.EXPANDS = self.g.atom("expands")
        self.DOING = self.g.atom("doing")
        self.DID = self.g.atom("did")
        self.EXPECTS = self.g.atom("expects")
        self.DEVIATES = self.g.atom("deviates")
        # Match, as a request (§21). A rule can HOLD a pattern -- `+con(?r, ?pat,
        # +)` binds one -- and cannot APPLY one, because applying is substitution
        # and substitution is floor. So the missing thing is a service, not a
        # capability: ask whether a rule could produce a goal, and be told what
        # its antecedent becomes if so.
        self.FIT = self.g.atom("fit")  # the request
        self.FITS = self.g.atom("fits")  # it could, and here is the instantiation
        self.UNFIT = self.g.atom("unfit")  # it could not
        self.NEED = self.g.atom("need")  # one instantiated antecedent member

        # The knowledge base is a channel like any other (§13). Reading it
        # faithfully is guaranteed; what it *says* -- the rules -- stays as
        # contestable as anything else, which is what `by(R, boss)` depends on.
        self.KB = self.channels.open("kb")

        # The one register (§10): which node the machinery is currently reasoning
        # in. The frame itself is an ordinary node; only the pointer is
        # privileged.
        self.focus: Frame = self.gate.frame(self.chain.root)

        # Every name the machinery coins, in one place. The surface seeds its
        # table from this, so a name written in a rule is the SAME node the
        # machinery writes. Four separate bugs came from minting a reserved atom
        # beside this table -- `says`, `overrides`, `suppose`, `goal` -- each
        # silent, each looking like a rule that simply did not fire.
        self.reserved = {
            "says": self.SAYS, "kb": self.KB,
            "rule": self.RULE, "conn": self.CONN, "ant": self.ANT, "con": self.CON,
            "suppose": self.SUPPOSE, "goal": self.GOAL,
            "achieved": self.ACHIEVED, "blocked": self.BLOCKED,
            "plan": self.PLAN, "subgoal": self.SUBGOAL,
            "binds": self.BINDS, "expands": self.EXPANDS,
            "doing": self.DOING, "did": self.DID,
            "expects": self.EXPECTS, "deviates": self.DEVIATES,
            "causes": self.rules.CAUSES, "implies": self.rules.IMPLIES,
            "plus": self.rules.SIGN["+"], "minus": self.rules.SIGN["-"],
        }

        self.selections = 0
        self.useful_writes = 0
        self.exhausted = 0
        self.max_depth = 8
        self._enacted: set = set()
        self._supposed: set = set()
        self.supposition_budget = 32
        self.expansions = 0
        self.expansion_budget = 64
        self._expanded: set = set()
        self._acted: set = set()
        self._actuators: List[NodeId] = []
        self.emitted: List[NodeId] = []
        # Machinery vocabulary: requests, not claims. Nothing carries these out of
        # a frame. This is the closed set of §10 growing by one, and it is a real
        # cost -- worth listing rather than letting it accumulate (§5).
        self._bookkeeping = {self.SUPPOSE, self.GOAL, self.ACHIEVED, self.BLOCKED,
                             self.PLAN, self.SUBGOAL, self.BINDS, self.EXPANDS,
                             self.EXPECTS, self.DOING, self.DID, self.DEVIATES,
                             self.EMITTED, self.FIT, self.FITS, self.UNFIT,
                             self.NEED}

        self.bundle: List[Rule] = []
        self._install_bundle()
        self.gate.on_write.append(self._dispatch)
        self.gate.on_write.append(self._enter)
        self.gate.on_write.append(self._fit)
        # The boundary calls in. Anything delivered before now was queued because
        # nobody was listening yet, so it is drained once, here.
        self.channels.sink = self._deliver
        for pending in self.channels.drain():
            self._deliver(pending)

    # -- the bundle -------------------------------------------------------

    def _install_bundle(self) -> None:
        """The conventions that ship as rules rather than as branches (§4).

        Each one here is a name that used to be in Appendix C's census with an
        interpreter phase behind it, and is now data: readable by R4's queries,
        defeasible by `overrides`, and preemptable because it is selected like
        anything else.

        They are installed first, so the authored-order tiebreak of §18 prefers
        them -- which reproduces the old behaviour, where the phase ran before
        any rule was considered. That is a precedence claim, and being a claim
        rather than a control-flow fact is the whole point: a corpus can now
        override it.
        """
        g = self.g
        c, p, s = g.var("?channel"), g.var("?said"), g.var("?sign")

        # What a report MEANS. Crossing the boundary stays machinery, because a
        # channel is anchored and a rule is generic; deciding that an arrival is
        # a saying does not, and never did.
        self.bundle.append(
            self.rules.rule(
                IMPLIES,
                [Member(PLUS, g.rel(self.ARRIVED, c, p, s))],
                [Member(PLUS, g.rel(self.SAYS, c, p, s))],
                "intake",
            )
        )

        # What an emission MEANS: the agent acted.
        w = g.var("?what")
        self.bundle.append(
            self.rules.rule(
                IMPLIES,
                [Member(PLUS, g.rel(self.EMITTED, w))],
                [Member(PLUS, g.rel(self.DID, w))],
                "did",
            )
        )
        # And §15's *the agent asserts the act*, which was an unarguable line of
        # the interpreter and is now a defeasible claim. The consequent is a bare
        # variable, which §12 calls vacuous BACKWARDS and exact forwards -- the
        # same shape as a trust rule, and for the same reason: it says *believe
        # what this channel reported*, where the channel is the agent's own
        # hands.
        self.bundle.append(
            self.rules.rule(
                IMPLIES,
                [Member(PLUS, g.rel(self.DID, w))],
                [Member(PLUS, w)],
                "assert-act",
            )
        )

        # Surprise. §18 says it in one line -- *an expected entry and an observed
        # entry that disagree* -- and as a phase that line was false of the
        # implementation: the comparison was Python, so no rule could see it,
        # reorder it, or refuse it.
        #
        # Four rows, not four branches. Two expected signs times the two ways an
        # observation can contradict one: the opposite sign, and `?`. The last is
        # the case a phase gets right by accident and a rule has to state --
        # §9's `?` invalidates without replacing, so *I can no longer say* is a
        # disappointed expectation exactly as much as *the opposite happened*.
        q = g.var("?p")
        for expected, observed, why in (
            (PLUS, MINUS, "contradicted"),
            (PLUS, UNSURE, "invalidated"),
            (MINUS, PLUS, "contradicted"),
            (MINUS, UNSURE, "invalidated"),
        ):
            self.bundle.append(
                self.rules.rule(
                    IMPLIES,
                    [
                        Member(PLUS, g.rel(self.EXPECTS, q, self.rules.SIGN[expected])),
                        # A bare variable, already bound by the member above, so
                        # this matches the observation of that very proposition
                        # under the sign that disappoints it.
                        Member(observed, q),
                    ],
                    [Member(PLUS, g.rel(self.DEVIATES, q))],
                    f"deviation-{expected}-{why}",
                )
            )

    # -- rules as data ----------------------------------------------------

    def reify(self, rule: Rule) -> None:
        """Deposit what a rule IS, so rules can be matched by rules.

        This is §14's worked example made real -- `+rule(?r)`, `+conn(?r, causes)`
        and the members of each side. Without it a rule is a node nobody asserted,
        so `match` (which walks entries) cannot see it, and R4's questions are
        answerable only by the engine.

        The patterns are **mentioned**, not used: `+ant(<R>, heat(?a, ?w))` claims
        something about a rule and binds nothing.
        """
        f = self.focus
        w = lambda p: self.gate.write(
            f, p, "+", licence=self.g.rel(self.REIFIED, rule.node), source=self.KB, mention=True
        )
        w(self.g.rel(self.RULE, rule.node))
        conn = self.rules.CAUSES if rule.connective == "causes" else self.rules.IMPLIES
        w(self.g.rel(self.CONN, rule.node, conn))
        for m in rule.antecedent:
            w(self.g.rel(self.ANT, rule.node, m.pattern, self.rules.SIGN[m.sign]))
        for m in rule.consequent:
            w(self.g.rel(self.CON, rule.node, m.pattern, self.rules.SIGN[m.sign]))

    def reify_all(self) -> None:
        for r in self.rules.rules:
            self.reify(r)

    # -- supposing --------------------------------------------------------

    def suppose(
        self, assumption: NodeId, grade: str = "certain", wrap: Optional[NodeId] = None
    ) -> Frame:
        """Enter a supposition: assume `assumption` bare, and reason inside.

        This is the alternative to lifting. Where a lifting rule rewrites
        `likely(X)` into `likely(Y)` and therefore has to name the pattern of
        every rule it crosses, supposing **unwraps** -- inside the frame the
        assumption is an ordinary fact, and the ordinary rules apply to it by
        ordinary matching. Nothing is mentioned, so nothing hits use/mention, and
        rules carrying variables work unchanged.

        Containment is structural rather than promised: the frame's seat is a
        *successor* of the caller's, so the caller's walk never reaches it. What
        was concluded under the supposition is unreadable from outside until
        something deliberately carries a claim out.
        """
        licence = self.g.rel(self.SUPPOSING, assumption)
        seat = self.chain.succeed(self.focus.seat, licence)
        child = self.gate.frame(seat, parent=self.focus, purpose=licence, wrap=wrap)
        # Moving the register. This is the irreducible part, and it is the ONLY
        # irreducible part -- §4 item 3: finding where to write requires a read,
        # and a read requires somewhere to stand. Everything else about supposing
        # is convention.
        self.focus = child
        self.gate.write(child, assumption, PLUS, grade=grade, licence=licence, source=self.KB)
        return child

    def _enter(self, frame: Frame, e: Entry) -> None:
        """Open a supposition when one is requested -- at the write, not in a
        phase, and *without* running the reasoning inside it.

        A rule concludes `+suppose(p, likely)` like any other fact. What the
        machinery does that a rule cannot is move the register, because a frame
        is anchored and a rule is generic. It does nothing else.

        The old phase did much more: it opened the frame and then called `run()`
        inside it, to quiescence, before returning. That is a subroutine call,
        and §18 spends its length arguing that nothing may own the loop --
        `if to find an answer, look for causes is control flow, step three owns
        the agent until it returns`. Supposition was exactly that, in the
        machinery rather than in a corpus, and it meant a surprise could not
        preempt reasoning carried out under a hypothesis.

        Reasoning inside a supposition is now ordinary ticks of the ordinary
        loop, with the register pointing inside. The frame is left when the loop
        finds nothing more to do there (`_leave`).
        """
        if self.g.relation_of(e.proposition) is not self.SUPPOSE or e.sign != PLUS:
            return
        if e.node in self._enacted or self.g.has_var(e.proposition):
            return
        # Bounds, and each reports that it was hit rather than stopping silently
        # (§13). Depth recurses by construction: a wrapped conclusion carried out
        # of one frame proposes the next.
        if len(self.focus.ancestry()) > self.max_depth:
            self.exhausted += 1
            return
        if len(self._supposed) >= self.supposition_budget:
            self.exhausted += 1
            return
        assumption, wrap = self.g.members(e.proposition)
        self._enacted.add(e.node)
        # Supposing the same thing twice derives nothing new: everything
        # downstream of it was already drawn the first time. Without this the
        # loop crosses guards it created a moment ago, forever.
        if assumption in self._supposed:
            return
        self._supposed.add(assumption)
        self.suppose(assumption, grade=e.grade, wrap=wrap)

    def _fit(self, frame: Frame, e: Entry) -> None:
        """Answer a match request (§5's wall, from the side that can be crossed).

        A rule concludes `+fit(<R>, goal)` -- *could this rule produce this?* --
        and the machinery answers, because deciding that a ground goal
        corresponds to a stored generic pattern is `match`, and match is floor.

        What comes back is not a yes and a binding. A binding is a map from
        variables to nodes, and a rule cannot hold one, let alone apply it. So
        the answer is already **instantiated**:

            +fits(<R>, goal)                one, if the rule could
            +need(<R>, goal, <subgoal>)     one per antecedent member, substituted
            +unfit(<R>, goal)               otherwise

        That is the whole service, and its shape is the finding: the missing
        piece was never *match* on its own. Match and substitute travel together,
        because the caller cannot do the second half.

        Everything else stays a rule -- whether to ask, which rule to prefer,
        whether to check satisfaction first, what to write when nothing fits.
        Those are the conventions §18 froze into a phase.
        """
        if self.g.relation_of(e.proposition) is not self.FIT or e.sign != PLUS:
            return
        rule_node, goal = self.g.members(e.proposition)
        if self.g.has_var(goal):
            return  # a description is not a goal; §15's condition, again
        rule = next((r for r in self.rules.rules if r.node == rule_node), None)
        if rule is None:
            return
        licence = self.g.rel(self.WANTED, rule_node, goal)

        for m in rule.consequent:
            if m.sign != PLUS or self.g.is_var(m.pattern):
                # A bare-variable consequent claims it can conclude anything, so
                # backwards it proposes itself for every goal without end. §12
                # calls it vacuous rather than wrong, and parks the real answer
                # in recall.
                continue
            b = unify(self.g, m.pattern, goal, {})
            if b is None:
                continue
            self.gate.write(
                frame, self.g.rel(self.FITS, rule_node, goal), PLUS,
                licence=licence, source=self.KB, consumed=(e,), mention=True,
            )
            for want in rule.antecedent:
                self.gate.write(
                    frame,
                    self.g.rel(self.NEED, rule_node, goal, substitute(self.g, want.pattern, b)),
                    PLUS,
                    licence=licence, source=self.KB, consumed=(e,), mention=True,
                )
            return
        self.gate.write(
            frame, self.g.rel(self.UNFIT, rule_node, goal), PLUS,
            licence=licence, source=self.KB, consumed=(e,), mention=True,
        )

    def _own_frame(self) -> Frame:
        """Where the agent itself is standing, as opposed to where its reasoning
        currently is.

        Climb out of every supposition in the register's ancestry. What is left
        is the outermost frame that is not a hypothesis -- the agent's own seat,
        and the only place a report from the world may land.

        This is derived, not a second register. §4 allows exactly one privileged
        pointer, and a second one for *the agent's own position* would have been
        the easy wrong answer: the position is recoverable from the forest, so it
        does not need to be held.
        """
        f = self.focus
        while (
            f.parent is not None
            and f.purpose is not None
            and self.g.relation_of(f.purpose) is self.SUPPOSING
        ):
            f = f.parent
        return f

    def _leave(self) -> bool:
        """The loop has nothing more to do inside the current supposition, so
        carry its conclusions out and restore the register.

        This is not a phase over a convention -- it is the register's own
        discipline. Something entered; something must restore. What it does while
        restoring *is* convention (§16's re-wrap), and it cannot be a rule for
        §17's reason: reading another frame's conclusions is match with an
        explicit anchor, and an anchor is exactly what a generic rule cannot name.
        """
        frame = self.focus
        if frame.parent is None or frame.wrap is None:
            return False
        self.discharge(frame, frame.wrap)
        return True

    # -- acting, and being wrong about it ---------------------------------

    def actuator(self, name: str) -> NodeId:
        """A channel that carries intents OUT. Channels already carry the world
        in (§13); acting is the same relation read the other way, and needs no
        new construct for the same reason an action needs none (§11)."""
        node = self.channels.open(name)
        self._actuators.append(node)
        return node

    def _dispatch(self, frame: Frame, e: Entry) -> None:
        """The outbound boundary, at the write rather than in the loop.

        A rule concludes `+doing(p)` like any other fact; this carries it past
        the agent's edge, because a boundary is anchored and a rule is generic.
        It is the mirror of `_deliver`, and between them the boundary has exactly
        two names -- one per direction.

        Everything the old `_act` phase did *besides* crossing is now a rule:
        `<did>` records that the agent acted, and `<assert-act>` asserts the act
        itself. The second is the interesting one. §15 argues that the agent must
        assert what it did -- otherwise it emits an intent into silence and
        nothing downstream ever happens -- and as a phase that argument was
        unarguable. As a rule it is a claim, and an agent that should *not*
        assume its acts succeed is now expressible by overriding it.
        """
        if e.sign != PLUS or self.g.relation_of(e.proposition) is not self.DOING:
            return
        if self.g.has_var(e.proposition):
            return  # a description cannot be acted on; §15's condition, at the edge
        if e.node in self._acted:
            return
        self._acted.add(e.node)
        (what,) = self.g.members(e.proposition)
        self.emitted.append(what)
        # The smallest unarguable record that something left the agent. What it
        # MEANS is `<did>`, and what follows from it is `<assert-act>`.
        self.gate.write(
            frame, self.g.rel(self.EMITTED, what), "+",
            licence=self.g.instance(self.UTTERANCE, self.KB, what),
            source=self.KB, consumed=(e,),
        )

    def _expect(self, frame: Frame, proposition: NodeId, sign: str, licence: NodeId) -> None:
        """Forward application deposits what it predicts (§16).

        Without the deposit there is nothing to be surprised against -- an
        expectation that lives in an interpreter variable is unmatched not
        because the rule was weak but because there is nothing there to match.
        """
        self.gate.write(
            frame, self.g.rel(self.EXPECTS, proposition, self.rules.SIGN[sign]), "+",
            licence=licence, source=self.KB, mention=True,
        )

    # Noticing a deviation used to be a phase here. It is now four bundled rules
    # (`_install_bundle`), and it had no boundary component at all -- §18 already
    # said *surprise is a match*, and the phase was that sentence being false of
    # the implementation.

    # -- backward reading -------------------------------------------------

    def _expand_goal(self) -> bool:
        """Read a rule backwards: what would make this goal true?

        §14 says backward reading is not a fifth primitive but rules over the
        four, and prints a rule to do it -- `+want(?f), +member(+?f, con(?r))`.
        That rule cannot work, and the reason is worth stating: `con(?r, ...)`
        stores the rule's PATTERN, which is generic, while a goal is ground. One
        variable cannot bind to both. Deciding they correspond is `match`, and
        `match` is a primitive no rule can call.

        So this sits in the machinery until a rule can invoke matching -- the
        same wall the lifting rule hit, arrived at from the other side.

        R2 is the other obligation: reading a rule backwards is reading its
        converse, which is a hypothesis and not an entailment. Every subgoal is
        licensed as `wanted`, never `applied`, so a conclusion drawn forwards is
        permanently distinguishable from a goal proposed backwards.
        """
        if self.expansions >= self.expansion_budget:
            self.exhausted += 1
            return False
        state = current_state(self.chain, self.focus.topic, self.focus.seat)
        for e in state:
            if e.sign != "+" or self.g.relation_of(e.proposition) != self.GOAL:
                continue
            if e.node in self._expanded:
                continue
            (wanted,) = self.g.members(e.proposition)
            self._expanded.add(e.node)

            # *Is this goal already satisfied?* is a MATCH, not a lookup. A
            # subgoal is often generic -- `tap(?t)`, because the rule that
            # proposed it left `?t` unbound -- and `resolve` compares proposition
            # identity, so it would report a satisfied goal as blocked.
            #
            # And the match must run inside the PLAN's bindings. Satisfying
            # `tap(?t)` with `tap(sink)` binds `?t` for the sibling goal
            # `under(kettle, ?t)`. Checked independently, `tap(sink)` and
            # `under(kettle, drain)` would both report achieved and the plan
            # would be wrong -- silently, which is the worst kind.
            plan = self._plan_of(wanted, state)
            env = self._bindings_of(plan, state) if plan is not None else {}
            held, extended = None, None
            for s in state:
                if s.sign != "+":
                    continue
                b = unify(self.g, wanted, s.proposition, dict(env))
                if b is not None:
                    held, extended = s, b
                    break
            if held is not None:
                if plan is not None:
                    for var, val in extended.items():
                        if var not in env:
                            self.gate.write(
                                self.focus, self.g.rel(self.BINDS, plan, var, val), "+",
                                licence=self.g.rel(self.ACHIEVED, wanted), source=self.KB,
                                consumed=(held,), mention=True,
                            )
                self._note(self.ACHIEVED, wanted, e)
                return True

            candidates = []
            for r in self.rules.rules:
                for m in r.consequent:
                    if m.sign != "+":
                        continue
                    if self.g.is_var(m.pattern):
                        # A consequent that is a bare variable says *this rule can
                        # conclude anything*. Forwards that is exact and useful --
                        # it is how `+says(user, ?p)` becomes `+?p`. Backwards it
                        # is vacuous: it proposes itself for every goal, and its
                        # subgoal is another goal of the same shape, without end.
                        #
                        # So the two readings of one statement are not equally
                        # informative, which R1 never promised. Recall is where
                        # this belongs once it is learned (§15); until then the
                        # backward reader declines what it cannot use.
                        continue
                    b = unify(self.g, m.pattern, wanted, {})
                    if b is not None:
                        candidates.append((r, b))
                        break
            if not candidates:
                # *I found no way* is not *there is no way* (§9, §15). This says
                # only the first, and says it explicitly rather than by silence.
                self._note(self.BLOCKED, wanted, e)
                return True

            self.expansions += 1
            rule, binding = candidates[0]
            licence = self.g.rel(self.WANTED, rule.node, wanted)
            # One plan per expansion, and it is the thing bindings belong to.
            # Not interned: expanding the same goal twice by different rules is
            # two plans, which is what having alternatives means.
            plan = self.g.instance(self.PLAN, rule.node, wanted)
            self.gate.write(
                self.focus, self.g.rel(self.EXPANDS, plan, wanted, rule.node), "+",
                licence=licence, source=self.KB, consumed=(e,), mention=True,
            )
            for var, val in binding.items():
                self.gate.write(
                    self.focus, self.g.rel(self.BINDS, plan, var, val), "+",
                    licence=licence, source=self.KB, mention=True,
                )
            for m in rule.antecedent:
                sub = substitute(self.g, m.pattern, binding)
                self.gate.write(
                    self.focus, self.g.rel(self.GOAL, sub), "+",
                    licence=licence, source=self.KB, consumed=(e,), mention=True,
                )
                self.gate.write(
                    self.focus, self.g.rel(self.SUBGOAL, plan, sub), "+",
                    licence=licence, source=self.KB, mention=True,
                )
            return True
        return False

    def _plan_of(self, wanted: NodeId, state: List[Entry]) -> Optional[NodeId]:
        """Which plan proposed this goal. A goal with no plan is a root want."""
        for s in state:
            if s.sign == "+" and self.g.relation_of(s.proposition) is self.SUBGOAL:
                plan, sub = self.g.members(s.proposition)
                if sub == wanted:
                    return plan
        return None

    def _bindings_of(self, plan: NodeId, state: List[Entry]) -> dict:
        """A plan's environment, read back out of the graph -- which is R7: the
        agent's own working state is a fact, not an interpreter variable."""
        env = {}
        for s in state:
            if s.sign == "+" and self.g.relation_of(s.proposition) is self.BINDS:
                p, var, val = self.g.members(s.proposition)
                if p == plan:
                    env[var] = val
        return env

    def _note(self, relation: NodeId, wanted: NodeId, because: Entry) -> None:
        self.gate.write(
            self.focus, self.g.rel(relation, wanted), "+",
            licence=self.g.rel(relation, wanted), source=self.KB,
            consumed=(because,), mention=True,
        )

    def discharge(self, frame: Frame, wrap: NodeId, limit: int = 100) -> List[Entry]:
        """Run to quiescence inside, then carry conclusions out **wrapped**.

        Nothing leaves a frame (§13). What crosses is a claim *about* what was
        concluded under the supposition -- `likely(q)` at the caller's seat, never
        `q`. The caller knows it was working under a guard; the rules inside never
        had to.

        This used to begin with `self.run(limit)` -- a nested loop that owned the
        agent until the supposition was exhausted. It does not any more: the
        caller is `_leave`, which runs when the ordinary loop has already found
        nothing more to do inside.
        """
        inside = []
        m: Optional[Moment] = self.focus.seat
        while m is not None and m is not frame.seat.predecessor:
            inside.append(m)
            m = m.predecessor
        assumption_licence = frame.purpose

        out: List[Entry] = []
        parent = frame.parent or frame
        self.focus = parent
        for moment in reversed(inside):
            for e in moment.delta:
                if e.licence == assumption_licence:
                    continue  # the assumption itself is not a conclusion
                if self.g.relation_of(e.proposition) in self._bookkeeping:
                    # A request to suppose is not a claim about the world, so
                    # there is nothing for the wrapper to qualify. Carrying it
                    # out produces `likely(suppose(...))`, which the rule that
                    # crosses guards then crosses -- the machinery supposing its
                    # own bookkeeping, forever.
                    continue
                out.append(
                    self.gate.write(
                        parent,
                        self.g.rel(wrap, e.proposition),
                        e.sign,
                        grade=e.grade,
                        licence=self.g.rel(self.CONCLUDED, frame.node),
                        source=self.KB,
                        consumed=(e,),
                    )
                )
        frame.state = "discharged"
        frame.carried = out
        return out

    # -- the loop ---------------------------------------------------------

    def tick(self) -> Step:
        # Not a phase. Delivery happened when the world spoke; this only asks how
        # much of it happened since the last step, so that *nothing applied* and
        # *nothing arrived and nothing applied* stay different silences (§19).
        arrivals = self.channels.since_last_tick()

        if self._expand_goal():
            return Step(arrivals, 0, 0, None, (), "expanded")

        proposed = self._recall()
        applications: List[Application] = []
        for r in proposed:
            applications.extend(
                match(self.g, self.chain, r, self.focus.topic, self.focus.seat)
            )
        # Defeat before quiescence -- see `rules.defeat` for why the order is not
        # interchangeable.
        applications = defeat(self.rules, applications)
        applications = [a for a in applications if self._would_change(a)]

        chosen = arbitrate(self.rules, applications)
        if chosen is None:
            # Nothing more to do *here*. If `here` is inside a supposition, that
            # is not the end of the run -- it is the end of the supposition, so
            # carry its conclusions out and restore the register. The frame is
            # left because the loop ran out of work in it, never because a
            # subroutine returned.
            if self._leave():
                return Step(arrivals, len(proposed), 0, None, (), "supposed")
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
            if s.state not in ("applied", "supposed", "expanded"):
                break
        return out

    # -- the four primitives ----------------------------------------------

    def _recall(self) -> List[Rule]:
        """Never complete, by design (§15). Exhaustive here, which is the
        deliberate-reasoning setting: recall with the budget removed."""
        return list(self.rules.rules)

    def _deliver(self, a: Arrival) -> None:
        """Cross the boundary, and nothing else — when the world speaks, not when
        the loop next gets round to asking.

        This is what stays machinery under §5's test, and the reason is §18's:
        a channel is **anchored** and a rule is generic, so no rule can name the
        socket a report came in on. But *being machinery* never made it a phase.
        An arrival is an external event, and an external event is not something
        the agent does; nothing about it belongs in the agent's step.

        So delivery is now the boundary calling in, the same shape as the gate's
        write hooks, and the tick lost its first line.

        This is what stays machinery under §5's test, and the reason is §18's:
        a channel is **anchored** and a rule is generic, so no rule can name the
        socket a report came in on. What the machinery deposits is therefore the
        smallest unarguable record of a boundary event --

            arrived(channel, proposition, sign)      sourced to the channel

        -- and *what that means* is a rule (`<intake>` below). Previously this
        method wrote `says(...)` directly, which made `says` a name the engine
        knew: Appendix C's census, one line of it.

        Two things improve by the split rather than merely moving. The arrival's
        grade now reaches the `says` claim through §16's weakest link instead of
        through a keyword argument, so nothing special-cases it. And provenance
        lands where §17 says it should: the raw arrival is the **channel** record,
        unforgeable and sourced to the socket; the `says` claim above it is
        derived, licensed by a rule, and therefore arguable.

        `says` still carries the reported sign as a member, and the entry is
        always positive -- the channel did speak. Writing `-says(c, p)` would
        claim the channel stayed silent, which is a different fact and not the
        one observed. §21 records the better answer: an arrival should be a
        moment, so a report is a signed delta.
        """
        own = self._own_frame()
        if own is not self.focus:
            # The register is inside a hypothesis and the world has spoken. The
            # report belongs to the AGENT, not to what the agent happens to be
            # supposing -- so it lands on a successor of the agent's own seat,
            # which forks the chain away from the supposition's branch.
            #
            # Both halves matter. Without the re-seating the entry would be
            # appended to a moment that already has descendants, and deposit
            # order is position along the walk, so a report arriving now would
            # read as older than everything concluded since. Without the fork it
            # would land inside the supposition and leave it wrapped, which is
            # what it did: the agent's only record of what a channel said became
            # `likely(says(...))` -- the world's own testimony, hedged.
            self.gate.reseat(own, self.chain.succeed(own.seat, self.KB))
        utterance = self.g.instance(self.UTTERANCE, a.channel, a.proposition)
        report = self.g.rel(
            self.ARRIVED, a.channel, a.proposition, self.rules.SIGN[a.sign]
        )
        self.gate.write(
            own, report, PLUS,
            grade=a.grade, licence=utterance, source=a.channel,
        )

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
        mention = self._is_mention(app)

        wrote: List[Entry] = []
        for m in app.rule.consequent:
            grounded = substitute(self.g, m.pattern, app.bindings)
            if app.rule.connective == "causes":
                self._expect(frame, grounded, m.sign, licence)
            wrote.append(
                self.gate.write(
                    frame,
                    grounded,
                    m.sign,
                    grade=effective_grade(m.grade, app.consumed),
                    licence=licence,
                    source=self.KB,  # the rule is the licence; the KB is the channel
                    consumed=app.consumed,
                    mention=mention,
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
            if self.g.has_var(grounded) and not self._is_mention(app):
                # Genuinely generic: the rule's consequent names something its
                # antecedent never bound, and there is nothing to deposit. A
                # conclusion that contains variables because it is ABOUT a rule
                # is a different case entirely, and dropping it here is how a
                # rule reasoning about rules used to look exactly like a rule
                # with nothing to do -- silently, and only at this line.
                return False
            cur = self.chain.resolve(grounded, self.focus.topic, self.focus.seat)
            if cur is None or cur.sign != m.sign:
                return True
        return False

    def _is_mention(self, app: Application) -> bool:
        """Is this application talking ABOUT rules rather than in them?

        §14 says the use/mention distinction is settled by *who is writing* --
        the machinery reifying a rule mentions, a rule's consequent uses. That is
        too strong, and running it is how the gap showed: a rule whose antecedent
        matched `con(?r, ?pat, +)` binds `?pat` to a stored pattern, and anything
        it concludes about `?pat` is a **ground claim that happens to contain
        variables**. A rule's consequent can mention.

        What tells them apart is inheritance rather than authorship:

        > **Mention propagates through bindings. A conclusion drawn from a
        > mentioned entry is itself a mention.**

        That is checkable rather than declared -- the entries match consumed are
        already recorded, because R5 needs them for the trail. This is the trail
        being load-bearing for something other than explanation, which §16 argues
        is the pattern to expect.
        """
        return any(e.mention for e in app.consumed)

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
