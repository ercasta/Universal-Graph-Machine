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

from .chain import PLUS, Chain, Entry, Moment
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
        self._deviations: set = set()
        self.emitted: List[NodeId] = []
        # Machinery vocabulary: requests, not claims. Nothing carries these out of
        # a frame. This is the closed set of §10 growing by one, and it is a real
        # cost -- worth listing rather than letting it accumulate (§5).
        self._bookkeeping = {self.SUPPOSE, self.GOAL, self.ACHIEVED, self.BLOCKED,
                             self.PLAN, self.SUBGOAL, self.BINDS, self.EXPANDS,
                             self.EXPECTS, self.DOING, self.DID, self.DEVIATES}

        self.bundle: List[Rule] = []
        self._install_bundle()

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

    def suppose(self, assumption: NodeId, grade: str = "certain") -> Frame:
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
        child = self.gate.frame(seat, parent=self.focus, purpose=licence)
        self.focus = child
        self.gate.write(child, assumption, "+", grade=grade, licence=licence, source=self.KB)
        return child

    def _enact_supposition(self) -> bool:
        """Rules propose a supposition; the machinery enacts it.

        A rule concludes `+suppose(p, likely)` -- an ordinary entry, matched and
        deposited like any other. The loop then does what a rule cannot: open the
        frame, reason inside, and carry the conclusions out wrapped. That is the
        same division as the gate (§13) -- the rule says *what*, the machinery
        supplies the *where*, because a frame is anchored and a rule is generic.

        It recurses by construction: a conclusion drawn inside the frame that is
        itself wrapped proposes another supposition, one level down. The depth
        bound is a budget, and like every bound here it must report that it was
        hit rather than silently stopping (§9).
        """
        if len(self.focus.ancestry()) > self.max_depth:
            self.exhausted += 1
            return False
        if len(self._supposed) >= self.supposition_budget:
            self.exhausted += 1
            return False
        for e in current_state(self.chain, self.focus.topic, self.focus.seat):
            if e.sign != "+" or e.node in self._enacted:
                continue
            if self.g.relation_of(e.proposition) != self.SUPPOSE:
                continue
            assumption, wrap = self.g.members(e.proposition)
            self._enacted.add(e.node)
            # Supposing the same thing twice derives nothing new: everything
            # downstream of it was already drawn the first time. Without this the
            # loop crosses guards it created a moment ago, forever.
            if assumption in self._supposed:
                return True
            self._supposed.add(assumption)
            frame = self.suppose(assumption, grade=e.grade)
            self.discharge(frame, wrap)
            return True
        return False

    # -- acting, and being wrong about it ---------------------------------

    def actuator(self, name: str) -> NodeId:
        """A channel that carries intents OUT. Channels already carry the world
        in (§13); acting is the same relation read the other way, and needs no
        new construct for the same reason an action needs none (§11)."""
        node = self.channels.open(name)
        self._actuators.append(node)
        return node

    def _act(self) -> bool:
        """Emit what the agent has decided to do.

        §11: an action is an event, an event is a moment, and *to execute* means
        make this event-fact true. So nothing here is an action construct -- a
        rule concludes `+doing(p)` like any other fact, and this carries it past
        the boundary. What comes back comes back as an ordinary arrival, on an
        ordinary channel, and may disagree.
        """
        for e in current_state(self.chain, self.focus.topic, self.focus.seat):
            if e.sign != "+" or e.node in self._acted:
                continue
            if self.g.relation_of(e.proposition) is not self.DOING:
                continue
            if self.g.has_var(e.proposition):
                continue  # cannot act on a description; §8's achievability, met
            self._acted.add(e.node)
            (what,) = self.g.members(e.proposition)
            self.emitted.append(what)
            did = self.g.rel(self.DID, what)
            self.gate.write(
                self.focus, did, "+", licence=did, source=self.KB, consumed=(e,),
            )
            # §11: *to execute* means make this event-fact true. The agent knows
            # it acted -- that is not a claim about the world's response, which
            # arrives on a channel and may disagree. Asserting the act is what
            # gives the rules something to fire on, and gives the expectation
            # something to be disappointed by.
            self.gate.write(
                self.focus, what, "+", licence=did, source=self.KB, consumed=(e,),
            )
            return True
        return False

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

    def _notice_deviation(self) -> int:
        """Surprise is a match: an expected entry and an observed entry that
        disagree (§16). The machinery only *notices*; what to do about it is a
        rule, so it can be overridden like any other strategy."""
        found = 0
        state = current_state(self.chain, self.focus.topic, self.focus.seat)
        expectations = [
            s for s in state
            if s.sign == "+" and self.g.relation_of(s.proposition) is self.EXPECTS
        ]
        for exp in expectations:
            prop, sign_node = self.g.members(exp.proposition)
            if (exp.node, prop) in self._deviations:
                continue
            observed = self.chain.resolve(prop, self.focus.topic, self.focus.seat)
            if observed is None:
                continue
            expected_sign = "+" if sign_node == self.rules.SIGN["+"] else "-"
            if observed.sign == expected_sign:
                continue
            self._deviations.add((exp.node, prop))
            self.gate.write(
                self.focus, self.g.rel(self.DEVIATES, prop), "+",
                licence=self.g.rel(self.DEVIATES, prop), source=self.KB,
                consumed=(exp, observed),
            )
            found += 1
        return found

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
        """
        self.run(limit=limit)
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
        return out

    # -- the loop ---------------------------------------------------------

    def tick(self) -> Step:
        arrivals = self._deliver()

        if self._enact_supposition():
            return Step(arrivals, 0, 0, None, (), "supposed")

        if self._act():
            return Step(arrivals, 0, 0, None, (), "acted")

        # Not gated on arrivals: a deviation usually appears a tick or two AFTER
        # the report lands, once a trust rule has turned what a channel said into
        # a belief. Checking only on the arriving tick misses every one of them.
        if self._notice_deviation():
            return Step(arrivals, 0, 0, None, (), "surprised")

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
            if s.state not in ("applied", "supposed", "expanded", "acted", "surprised"):
                break
        return out

    # -- the four primitives ----------------------------------------------

    def _recall(self) -> List[Rule]:
        """Never complete, by design (§15). Exhaustive here, which is the
        deliberate-reasoning setting: recall with the budget removed."""
        return list(self.rules.rules)

    def _deliver(self) -> int:
        """Cross the boundary, and nothing else.

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
        arrivals = self.channels.drain()
        for a in arrivals:
            utterance = self.g.instance(self.UTTERANCE, a.channel, a.proposition)
            report = self.g.rel(
                self.ARRIVED, a.channel, a.proposition, self.rules.SIGN[a.sign]
            )
            self.gate.write(
                self.focus, report, "+",
                grade=a.grade, licence=utterance, source=a.channel,
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
