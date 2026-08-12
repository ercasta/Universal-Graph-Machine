"""The interpreter (§14, §16).

    Recall proposes. Match filters. Arbitrate commits. Only the last is total.

The step is *select a rule, apply it*, and object-rules and meta-rules must be
indistinguishable to it -- a flat tower, not a stacked one. There are no phases:
every convention the loop used to enact is a bundled rule or a request answered
at the write, so adding one adds rows rather than branches.

Recall is narrowable but not yet learned. `prefer(<R>, k)` is a table of ordinary
facts, and §15 is emphatic that this is the step where experience belongs and
where being wrong is recoverable -- so the seam is here, the table is data, and
the learning is not.
"""

import os
from typing import List, NamedTuple, Optional, Tuple

from .chain import GRADES, MINUS, PLUS, UNSURE, Chain, Entry, Moment
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
    Situation,
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
    state: str  # applied | supposed | widened | quiet | quiescent | nothing-matched


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
        # The same record, for an act that was decided on but not taken --
        # because the register was inside a hypothesis. Planning has to be able
        # to reason PAST an action, and what it reasons past is the action's
        # assumed outcome, not its occurrence.
        self.TAKEN = self.g.atom("taken")
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
        # The second match a backward reader needs, and the one §18 warns about:
        # *is this goal already satisfied* must run inside the bindings that
        # satisfied its siblings, or `tap(?t)` and `under(kettle, ?t)` are met by
        # different taps and the plan is wrong -- silently.
        self.CHECK = self.g.atom("check")  # the request
        self.UNMET = self.g.atom("unmet")  # nothing in the state answers it
        # The third request, and the one that retires the last phase. `blocked`
        # claims that NO rule fits -- an aggregate over a finished search, which
        # no positive rule can say and `-` cannot say either (§9's `-` is *an
        # entry denies this*, not *for no ?r*). So a rule asks, at a moment it
        # chooses, and the machinery answers by counting what the corpus already
        # produced. It runs no search of its own: `fits` entries are the rules'
        # own work, and this only reads them.
        self.VERDICT = self.g.atom("verdict")  # the request
        self.PURSUED = self.g.atom("pursued")  # something fits it
        # Denial as a TERM, beside the sign rather than instead of it (§9).
        # A sign is a member of an entry, so it cannot sit inside another term --
        # and §16 nests terms by construction. Concluding `-b` under a `likely`
        # supposition means *likely, not-b*; with only a sign to carry it, what
        # crosses out is `-likely(b)`, which says *not likely that b*. Different
        # claim, and the wrong one.
        self.NOT = self.g.atom("not")

        # Returning from a hypothesis, as an occasion other rules can key on
        # (§13, §15). Leaving a frame is a register event -- anchored, so
        # machinery -- and what the machinery deposits is the smallest
        # unarguable record of it, exactly as `arrived` and `emitted` are for the
        # boundary. What it MEANS is rules.
        self.LEFT = self.g.atom("left")
        # The other silent decline (§5). The loop running out of work is the
        # third place the machinery declines and the only one that used to say
        # nothing at all -- so reasoning could stop with goals still open and
        # nothing in the graph recorded that it had. `quiet(<m>)` is that record,
        # and a watchdog is then an ORDINARY rule with `+quiet(?m)` in its
        # antecedent: inert until the loop stops, which is precisely when the
        # aggregate it wants to compute -- *is anything still open?* -- becomes
        # legitimate, because the search it is an aggregate over has finished.
        self.QUIET = self.g.atom("quiet")
        # The other way to be over, and the design had only one (§19). Running out
        # of work is EXHAUSTION; this is SATISFACTION -- *there is nothing more
        # worth doing about x*. It has to be a claim rather than a condition in the
        # loop, because *worth* is a judgement and §4 puts judgements in data; and
        # it has to exist at all because an agent that stops only when exhausted
        # does an amount of work its corpus fixes, so nothing it learns can make it
        # cheaper. Measured: an ideal recall table reached a goal in 8 ticks
        # instead of 734 and saved nothing, because the loop went to quiescence
        # anyway.
        #
        # The argument is *what makes here over* -- a goal, a plan, a woken rule.
        # The loop never reads it; it is there so that *why did you stop?* has an
        # answer, which is the criterion §2 calls not-lossy.
        self.ENOUGH = self.g.atom("enough")
        # ...and the record that it happened. Same treatment as `left`, `quiet`,
        # `arrived` and `emitted` (§17): the machinery deposits the smallest
        # unarguable thing and says nothing about what it means.
        #
        # It is deliberately NOT `quiet`. `quiet` is what `<give-up>` asks its
        # verdict at, and `blocked` claims that no rule fits -- an aggregate over a
        # FINISHED search. A search that stopped because it was satisfied has not
        # finished, and reporting the goals it never reached as blocked is the
        # same unsoundness `_widen` exists to prevent, arriving from a second side.
        self.STOPPED = self.g.atom("stopped")
        # ...and what the machinery says instead, when it will not let a stop
        # stand. `open(<w>)` is a goal that was still outstanding at the moment
        # the agent tried to be done with everything.
        #
        # This is §19's carve-out for the third time, and the argument transfers
        # verbatim. Recall may be incomplete about what to do; it may not be
        # incomplete about what you must not do -- or about whether to go on --
        # or about a goal it is dropping. A corpus can be wrong about what is
        # worth doing next; it may not silently abandon what it was asked for.
        # So this is a VETO and not a rule: consulted before the stop is made,
        # never proposed, never arbitrated, and it cannot be forgotten by a
        # corpus that did not think of it.
        self.OPEN = self.g.atom("open")
        # What a finished episode has to say about the rules that ran in it:
        # `helped(<R>, <key>)`, deposited by the offline review. The smallest
        # unarguable record again -- *this rule was on the support of something
        # achieved* is a fact about the trail, where *so prefer it next time* is a
        # claim, and stays a rule.
        self.HELPED = self.g.atom("helped")
        # ...and its opposite, which only becomes sayable once a task is split.
        # `harmed(<R>, <key>)`: something the agent wanted was made FALSE, and
        # this rule is on the support of the entry that made it so.
        #
        # Episode-level failure has no author -- many rules, one bad outcome, and
        # nothing to attribute it to. A lost SUBGOAL has one: the negating entry
        # carries a licence, so the walk that finds credit finds blame by running
        # over a `-` instead of a `+`.
        self.HARMED = self.g.atom("harmed")
        # Forgoing: the thing arbitration was assumed to do and never did.
        # `forgone(<R>, <w>)` says *R was a live way of getting w and I took
        # another one*, and it is a fourth way for a rule not to run, distinct
        # from all three that existed:
        #
        #   defeated   (`overrides`, `supersedes`)  a rival answer is better
        #   forbidden  (the gate's veto)            it may never happen
        #   not recalled                            it did not come to mind
        #   FORGONE                                 it was reasonable and I chose otherwise
        #
        # Only the last is a decision, and only the last needs to be **deniable**:
        # the alternative was good, so passing it up has to be revisable when the
        # goal it served turns out still open. That is why this is a deposit ABOUT
        # the alternative rather than a retraction of the goal -- retract the goal
        # and credit cannot find what it achieved, and a failed act loses the want
        # with nothing left to notice.
        self.FORGONE = self.g.atom("forgone")
        # A callback: a pointer to a rule, hung on a node. `+resume(h, <R>)` says
        # *when h returns, R's turn has come* -- and `turn` is the strongest thing
        # it can say, because §5's wall stands: no rule may apply a rule.
        self.RESUME = self.g.atom("resume")
        # A rule that ordinary recall does not propose. Dormancy is what makes a
        # pointer do any work -- with recall exhaustive, a callback rule would
        # apply whenever it happened to match and the pointer would be decoration.
        self.DORMANT = self.g.atom("dormant")
        # ...and the fact that wakes one. This is directed RECALL, not invocation:
        # a proposed rule still has to match, can still be defeated, and still
        # competes in arbitration. Nothing owns the loop (§18).
        self.DUE = self.g.atom("due")
        # §19's table, as facts. `prefer(<R>, k)` says *when k is in play, bring
        # R to mind* -- authored now, learnable later from the trail the
        # machinery already deposits, and readable either way because it is an
        # ordinary claim rather than a weight in an interpreter.
        #
        # The key is NOT the register. The register is where attention is, and it
        # is a fresh moment every tick, so a table keyed on it would never see the
        # same key twice. What recurs is what the situation is ABOUT, so the key
        # is a relation in play.
        # §19's table, as facts: `prefer(<R>, key, 3)`.
        #
        #     key      what the recommendation is keyed on -- a node
        #     score    HOW MUCH it recommends, and this is a CARDINAL
        #
        # The score is the table's own quantity and has nothing to do with §10's
        # grades. Grades are ordinal and stay ordinal -- an entry's grade still
        # composes by §12's weakest link, and nothing here adds one. What adds is
        # the score, which was always a magnitude: *how much experience
        # recommends this*, summed over the recommendations that apply.
        #
        # Keeping them apart is what lets the entry's grade go on meaning
        # something separate: `+prefer(<R>, k, 3) @possible` is a strong
        # recommendation the agent is not sure of.
        self.PREFER = self.g.atom("prefer")
        # Numerals as shared nodes for the small ones, so a score written in a
        # corpus and a score written by a rule are the same node. Everything
        # that READS a numeral reads its name, so an unshared one still works --
        # but two nodes with one name is the trap this design has paid for four
        # times, and there is no reason to invite it.
        self.NUMERAL = {i: self.g.atom(str(i)) for i in range(10)}
        # The second carve-out, and it is the mirror of §19's first. Norms may
        # not be forgotten because forgetting one is a forbidden act nobody
        # notices; the BUNDLE may not be forgotten because it is how the agent
        # reads at all. `intake` not coming to mind is not a worse plan -- it is
        # a report that never became a belief. Being overridable and being
        # forgettable are different properties, and only the first was ever
        # claimed for the bundle.
        #
        # A fact, not a Python flag, so a corpus can make its own rules standing
        # and can retire one of ours.
        self.STANDING = self.g.atom("standing")
        # §19's carve-out. `forbidden(<pattern>)` is a norm, and its argument is a
        # DESCRIPTION rather than a proposition -- `forbidden(doing(harm(?x)))`
        # names a class of acts, the way `ant(<R>, heat(?a, ?w))` names a class of
        # premises. It is never matched by the loop; it is consulted at the gate.
        # Recall, as a request -- the fourth. `_recall` narrows which rules are
        # PROPOSED, and that cannot reach a cross product written inside an
        # antecedent: `<ask-fit>` used to say `+goal(?w), +rule(?r)` and matched
        # |goals| x |rules| ways however few rules were proposed. Measured, it
        # was 711 of 816 applications on a workload -- an agent asking every rule
        # it has about every goal it holds, before doing anything.
        #
        # So *what comes to mind about this?* becomes a question a rule can ask.
        # Two moves the agent cannot tell apart. Ordinal scoring makes this
        # exact and constant-free: they are *close* when they tie, and the top
        # score being unique is what confidence would mean.
        #
        # Deposited rather than acted on, because what to DO when unsure is a
        # claim and not machinery -- think longer, ask, suppose one and look,
        # take the reversible one. §14 keeps arbitration total, so a choice is
        # still made this tick; the record is what lets the agent know it was
        # not a confident one.
        self.CLOSE = self.g.atom("close")
        # ...and HOW CLOSE IS CLOSE is a knob, so it is a fact: `tolerance(2)`.
        #
        # This is the design's first **cardinal** quantity, and it is a departure
        # rather than an oversight. §12 says the grade scale is ordinal and that
        # ordinals do not add; a preference score adds them. What that buys is a
        # knob that can say *within 2* instead of enumerating which pairs of
        # grades count as indistinguishable. What it costs is stated in §12's own
        # terms: two weak preferences can now outweigh one strong one, which an
        # ordinal scale existed to prevent. §21 carries it.
        #
        # Zero by default, so the default is an exact tie and no behaviour
        # depends on a constant nobody chose. A rule can raise it -- which is the
        # reason it is a fact and not a field: an agent harder to convince when
        # the next step cannot be taken back writes `+tolerance(3)` while
        # `doing(...)` is in play, and *how careful am I being* becomes a claim
        # with a trail.
        self.TOLERANCE = self.g.atom("tolerance")
        self.RECALL = self.g.atom("recall")
        self.RECALLED = self.g.atom("recalled")
        self.FORBIDDEN = self.g.atom("forbidden")
        self.REFUSED = self.gate.REFUSED

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
            "says": self.SAYS, "arrived": self.ARRIVED, "kb": self.KB,
            # §9's denial-as-a-term. Missing until the bundle moved into the
            # surface, which is how it was found: <denial> is written against
            # `not(?p)`, so a corpus could not state, argue with or override the
            # one rule that reconciles the two ways of saying no.
            "not": self.NOT,
            "rule": self.RULE, "conn": self.CONN, "ant": self.ANT, "con": self.CON,
            "suppose": self.SUPPOSE, "goal": self.GOAL,
            "achieved": self.ACHIEVED, "blocked": self.BLOCKED,
            "plan": self.PLAN, "subgoal": self.SUBGOAL,
            "binds": self.BINDS, "expands": self.EXPANDS,
            "doing": self.DOING, "did": self.DID,
            "expects": self.EXPECTS, "deviates": self.DEVIATES,
            "taken": self.TAKEN, "emitted": self.EMITTED,
            "left": self.LEFT, "quiet": self.QUIET, "resume": self.RESUME,
            "enough": self.ENOUGH, "stopped": self.STOPPED, "open": self.OPEN,
            "helped": self.HELPED, "harmed": self.HARMED,
            "forgone": self.FORGONE,
            "dormant": self.DORMANT, "due": self.DUE, "prefer": self.PREFER,
            "forbidden": self.FORBIDDEN, "refused": self.REFUSED,
            "standing": self.STANDING,
            "recall": self.RECALL, "recalled": self.RECALLED,
            "close": self.CLOSE, "tolerance": self.TOLERANCE,
            **{str(i): n for i, n in self.NUMERAL.items()},
            "check": self.CHECK, "unmet": self.UNMET,
            "verdict": self.VERDICT, "pursued": self.PURSUED,
            "fit": self.FIT, "fits": self.FITS, "unfit": self.UNFIT,
            "need": self.NEED,
            "causes": self.rules.CAUSES, "implies": self.rules.IMPLIES,
            # The signs as ARGUMENTS -- `expects(p, plus)` mentions a sign where
            # `+p` uses one.
            #
            # ⚠ `unsure` is NOT load-bearing for the bundle, and the first
            # version of this comment said it was. Measured by deleting it: the
            # machine still builds, because the deviation rules carry §9's `?`
            # as a member SIGN (`? ?p`), which the parser always accepted --
            # not as an argument. What is real is the ASYMMETRY it was noticed
            # through: two of three signs could be spoken about and the third
            # could only be used. `expects(p, plus)` was writable and
            # `expects(p, unsure)` was not, so a corpus could say *I expected it
            # to hold* but not *I expected to be unable to say* -- which §9
            # insists is a claim and not the absence of one. Exercised by
            # `the_surface_can_say_what_the_apparatus_is_made_of`, because a
            # vocabulary entry with no user is the thing `ugm.bundle` exists to
            # catch.
            "plus": self.rules.SIGN["+"], "minus": self.rules.SIGN["-"],
            "unsure": self.rules.SIGN["?"],
        }

        self.selections = 0
        self.useful_writes = 0
        self.exhausted = 0
        self.max_depth = 8
        self._enacted: set = set()
        self._supposed: set = set()
        self.supposition_budget = 32
        # Backward reading is rules now, so its budget is the ordinary one: the
        # loop's `limit`, and `_would_change` for termination. The phase carried
        # its own counter because it ran outside arbitration and nothing else
        # could stop it.
        self.expansions = 0
        self._acted: set = set()
        self._quieted: set = set()
        self._stopped: set = set()
        self._noticed: set = set()
        self._vetoed: set = set()
        self._reified: set = set()
        # §19. `None` is the deliberate-reasoning setting -- recall with the
        # budget removed -- and it is the default, because narrowing is a claim
        # about what an agent has learned and a fresh agent has learned nothing.
        self.recall_budget: Optional[int] = None
        self._widened = False
        self.widenings = 0
        self._actuators: List[NodeId] = []
        self.emitted: List[NodeId] = []
        # Machinery vocabulary: requests, not claims. Nothing carries these out of
        # a frame.
        #
        # `doing` is deliberately NOT here. It is a request, but it is a request
        # about the world rather than about the machinery, and *what I would do
        # under this hypothesis* is the one thing a hypothesis about a course of
        # action is FOR. Kept as bookkeeping, an agent that supposed a premise
        # and found it would fire a missile came back knowing nothing at all.
        # What crosses is `likely(doing(...))`, which no dispatch matches --
        # the boundary keys on `doing`, and a wrapped intent is a claim, not an
        # intent. This is the closed set of §10 growing by one, and it is a real
        # cost -- worth listing rather than letting it accumulate (§5).
        self._bookkeeping = {self.SUPPOSE, self.GOAL, self.ACHIEVED, self.BLOCKED,
                             self.PLAN, self.SUBGOAL, self.BINDS, self.EXPANDS,
                             self.EXPECTS, self.DID, self.DEVIATES,
                             self.EMITTED, self.FIT, self.FITS, self.UNFIT,
                             self.NEED, self.CHECK, self.UNMET,
                             self.LEFT, self.QUIET, self.RESUME, self.DORMANT,
                             self.ENOUGH, self.STOPPED, self.OPEN, self.HELPED, self.HARMED,
                             self.FORGONE,
                             self.DUE, self.VERDICT, self.PURSUED, self.PREFER,
                             self.FORBIDDEN, self.STANDING,
                             self.RECALL, self.RECALLED, self.CLOSE,
                             self.TOLERANCE}

        # A rule becomes data when it is authored, not when someone remembers to
        # ask. Backward reading is rules now, and it enumerates `+rule(?r)` --
        # so a rule loaded after a call to `reify_all` would have been invisible
        # to the reader, with nothing anywhere saying so.
        self.rules.on_rule.append(self.reify)

        self.bundle: List[Rule] = []
        self._install_bundle()
        # Every bundled rule is standing, deposited rather than assumed -- so
        # *which rules always come to mind?* is a query, and a corpus can add to
        # the list or take something off it.
        for r in self.bundle:
            self.gate.write(
                self.focus, self.g.rel(self.STANDING, r.node), PLUS,
                licence=self.g.rel(self.REIFIED, r.node), source=self.KB, mention=True,
            )
        self.gate.on_write.append(self._dispatch)
        self.gate.on_write.append(self._enter)
        self.gate.on_write.append(self._fit)
        self.gate.on_write.append(self._settle)
        self.gate.on_write.append(self._verdict)
        self.gate.on_write.append(self._remember)
        self.gate.veto.append(self._forbid)
        # The boundary calls in. Anything delivered before now was queued because
        # nobody was listening yet, so it is drained once, here.
        self.channels.sink = self._deliver
        for pending in self.channels.drain():
            self._deliver(pending)

    # -- the bundle -------------------------------------------------------

    #: The bundle, in the surface, in authored order. §18's tiebreak reads this
    #: file top to bottom, so its order is a precedence claim a reader can see.
    BUNDLE = os.path.join(os.path.dirname(__file__), "rules", "bundle.ugm")

    def _install_bundle(self) -> None:
        """Load the conventions that ship as rules rather than as branches (§4).

        This used to build them here, with `self.rules.rule(IMPLIES, [Member(...
        g.rel(...))], ...)`. It does not any more, and the move was a TEST rather
        than a tidy: the design's claim is that the HOW is data, and authoring
        the apparatus in Python meant nobody had ever checked that the surface
        can say what the apparatus is made of.

        It could not. `arrived` and `not` were absent from `reserved`, so
        <intake> and <denial> were unwritable by anyone but the engine -- and,
        worse than unwritable, a corpus naming those relations got a *twin* node
        that matched nothing, silently. That is the trap this codebase has paid
        for four times, arriving from the vocabulary side. Both are load-bearing:
        deleting either name now fails construction, which is the probe.

        So `_vocabulary_is_surface_nameable` runs on every load. A bundled rule
        reaching for a relation a corpus cannot name is now a construction
        error, not a silent divergence.
        """
        from .text import load_file  # deferred: `text` imports `Machine`

        first = len(self.rules.rules)
        self._bundle_loader = load_file(self, self.BUNDLE)
        self.bundle = list(self.rules.rules[first:])
        self._vocabulary_is_surface_nameable()

    def _vocabulary_is_surface_nameable(self) -> None:
        """Every relation the bundle uses must be a name a corpus can write.

        Not a style rule. `Graph.atom` mints a fresh node per call -- names are
        not identity -- so a relation the bundle uses and `reserved` does not
        carry is a node the surface cannot reach. A corpus rule written against
        it would build a second node with the same name and never match, with
        nothing anywhere saying so.
        """
        known = set(self.reserved.values())
        missing = []

        def visit(n: NodeId) -> None:
            rel = self.g.relation_of(n)
            if rel is None:
                return
            if rel not in known and self.g.show(rel) not in missing:
                missing.append(self.g.show(rel))
            for m in self.g.members(n):
                visit(m)

        for r in self.bundle:
            for m in list(r.antecedent) + list(r.consequent):
                visit(m.pattern)
        if missing:
            raise RuntimeError(
                f"the bundle uses relations no corpus can name: {missing}. "
                f"Add them to `Machine.reserved` -- a name minted beside that table "
                f"is a second node with one name, and a corpus rule about it would "
                f"silently match nothing."
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
        if rule.node in self._reified:
            return
        self._reified.add(rule.node)
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
        """Kept because instruments call it; it should now find nothing to do.
        Rules are reified when they are authored (`RuleSet.on_rule`)."""
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
            # The bindings, as facts about the plan. A rule cannot hold a binding
            # (that is why `need` arrives instantiated), but it can hold a NODE
            # that other requests read -- which is how the sibling-agreement
            # problem is solved without a rule ever touching a substitution.
            plan = self.g.rel(self.PLAN, rule_node, goal)
            for var, val in b.items():
                self.gate.write(
                    frame, self.g.rel(self.BINDS, plan, var, val), PLUS,
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

    def _settle(self, frame: Frame, e: Entry) -> None:
        """Answer *is this goal already satisfied?* -- the second match.

        `+check(<plan>, goal)` asks it, and the answer must be computed **inside
        the plan's bindings**, which is what makes it a different service from
        `fit` rather than the same one pointed elsewhere. §18 states the failure
        it prevents: satisfy `tap(?t)` with `tap(sink)` and the sibling goal
        `under(kettle, ?t)` must be about *that* tap. Checked independently,
        `tap(sink)` and `under(kettle, drain)` both report achieved and the plan
        is wrong without anything saying so.

        A goal may be generic, which is why this cannot be a chain lookup: the
        rule that proposed `tap(?t)` left `?t` unbound, and resolving by
        proposition identity would report a satisfiable goal as blocked.
        """
        if self.g.relation_of(e.proposition) is not self.CHECK or e.sign != PLUS:
            return
        plan, goal = self.g.members(e.proposition)
        state = current_state(self.chain, self.focus.topic, self.focus.seat)
        env = {
            self.g.member(s.proposition, 1): self.g.member(s.proposition, 2)
            for s in state
            if s.sign == PLUS
            and self.g.relation_of(s.proposition) is self.BINDS
            and self.g.member(s.proposition, 0) == plan
        }
        licence = self.g.rel(self.ACHIEVED, goal)
        for s in state:
            if s.sign != PLUS or self.g.relation_of(s.proposition) in self._bookkeeping:
                continue
            b = unify(self.g, goal, s.proposition, dict(env))
            if b is None:
                continue
            self.gate.write(
                frame, self.g.rel(self.ACHIEVED, goal), PLUS,
                licence=licence, source=self.KB, consumed=(e, s), mention=True,
            )
            for var, val in b.items():
                if var not in env:
                    self.gate.write(
                        frame, self.g.rel(self.BINDS, plan, var, val), PLUS,
                        licence=licence, source=self.KB, consumed=(e, s), mention=True,
                    )
            return
        self.gate.write(
            frame, self.g.rel(self.UNMET, plan, goal), PLUS,
            licence=licence, source=self.KB, consumed=(e,), mention=True,
        )

    def _verdict(self, frame: Frame, e: Entry) -> None:
        """Answer *did anything fit this goal?* -- the aggregate, and the last
        thing the goal phase was doing that no rule could do.

        `blocked` is a claim that **no** rule fits. §12's argument that it cannot
        be a rule stands: a positive rule fires when *some* rule does not fit,
        which is a different claim, and a `-` member says *an entry denies this*,
        never *for no `?r`*. It is an aggregate over a finished search.

        Three things make answering it here different from running it in a phase,
        and together they are the reason the phase could go.

        **It runs no search.** Every `fits` entry it counts was produced by the
        rules, through `fit`. This reads the state and nothing else -- so *which
        rules were considered* stays the corpus's business, and recall can still
        narrow it (§19). A phase that searched for itself made recall unreachable.

        **It is asked, not assumed.** A rule decides when a goal is settled --
        `+quiet(?m), +goal(?w) => +verdict(?w)` is the shipped policy, and it is
        overridable like any other. The phase asserted the same policy in control
        flow, where §18 says a convention is invisible and expensive.

        **It is timed by the corpus, not by the loop.** The phase ran ahead of
        recall and returned early, so while any goal was unexpanded no ordinary
        rule could apply -- backward search monopolised the loop and reported a
        goal as blocked that forward reasoning would have satisfied. `ugm.backward`
        measured exactly that. Asking at quiescence cannot starve anything,
        because there is nothing left to starve.

        Two-valued, because a request that answers only when the news is bad is a
        third silent decline (§5).
        """
        if self.g.relation_of(e.proposition) is not self.VERDICT or e.sign != PLUS:
            return
        (wanted,) = self.g.members(e.proposition)
        state = current_state(self.chain, self.focus.topic, self.focus.seat)
        # Two ways a goal is answered, and the vocabulary for both was already
        # settled by the other two requests: `fits` (a rule could produce it) and
        # `achieved` (the world already does). Counting both is what keeps
        # `blocked` meaning what it meant when a phase computed it -- *nothing
        # answers this* -- rather than the narrower *no rule derives this*, which
        # would report a goal satisfied by a plain fact as blocked.
        answered = False
        for s in state:
            if s.sign != PLUS:
                continue
            rel = self.g.relation_of(s.proposition)
            if rel is self.FITS and self.g.member(s.proposition, 1) == wanted:
                answered = True
                break
            if rel is self.ACHIEVED and self.g.member(s.proposition, 0) == wanted:
                answered = True
                break
        fits = answered
        self.gate.write(
            frame,
            self.g.rel(self.PURSUED if fits else self.BLOCKED, wanted),
            PLUS,
            licence=self.g.rel(self.VERDICT, wanted),
            source=self.KB,
            consumed=(e,),
            mention=True,
        )

    def _remember(self, frame: Frame, e: Entry) -> None:
        """Answer *what comes to mind about this?* (§19).

        The first version of this answered *every rule*, which made it a slower
        way of writing the cross product it replaced. What makes it an answer
        rather than a scan is `RuleSet.by_conclusion`: rules indexed by the
        relation they conclude, so *what could produce `w0_s8(item)`* is a lookup
        and not a search over the rule set.

        That is not experience -- it is an index, and it is exact. §19's learning
        goes on top: among the candidates an index returns, which to try first,
        and when to stop trying. An agent that has to enumerate before it can
        prefer has not remembered anything.
        """
        if self.g.relation_of(e.proposition) is not self.RECALL or e.sign != PLUS:
            return
        self._answer_recall(frame, self.g.member(e.proposition, 0), e)

    def _answer_recall(
        self, frame: Frame, about: NodeId, because: Optional[Entry] = None
    ) -> None:
        candidates = self.rules.by_conclusion.get(self.g.relation_of(about), ())
        licence = self.g.rel(self.RECALL, about)
        for r in candidates:
            if self._claims(self.g.rel(self.DORMANT, r.node)) and not self._claims(
                self.g.rel(self.DUE, r.node)
            ):
                continue
            self.gate.write(
                frame, self.g.rel(self.RECALLED, r.node, about), PLUS,
                licence=licence, source=self.KB,
                consumed=(because,) if because is not None else (), mention=True,
            )

    # -- norms ------------------------------------------------------------

    def _forbid(self, frame: Frame, proposition: NodeId, sign: str) -> Optional[NodeId]:
        """§19's carve-out, and the whole of it.

        > **Recall may be incomplete about what to do. It may not be incomplete
        > about what you must not do.**

        A norm expressed as a rule is a competitor in recall, and a prohibition
        that fails to come to mind is a forbidden act that nothing notices. The
        repair is not to make recall complete for norms -- that reintroduces the
        exhaustive search §19 exists to avoid. It is to take them off the recall
        path entirely, which is what this is: not proposed, not matched, not
        arbitrated, not defeasible by precedence. Consulted on every write.

        **Cheap because it is indexed by what is about to be written.** §3's
        second index is instances-by-relation, so only prohibitions whose pattern
        has the same relation as this proposition are looked at, and only those
        are resolved. A corpus with a hundred norms about acting costs nothing on
        a write about the weather.

        **Asserting only.** `forbidden(p)` forbids bringing `p` about, and
        bringing about is `+`. Denying you are doing harm is not the forbidden
        act. Extending this to signs is rows rather than branches, and there is
        no case for it yet.

        **A norm is still a belief.** It is resolved at the writer's own position
        like anything else, so it can be denied, dated, or held only under a
        supposition. What it cannot do is fail to be consulted.

        One gap, pinned by a check rather than left to be discovered: a norm
        cannot be revised **from the surface**, because its argument is a
        description, a description is an authored statement, and §8 scopes a
        statement's variables to it -- so writing `-forbidden(doing(harm(?x)))` a
        second time denies a *different node* that says a similar thing. Revising
        one needs a way to name it, as `<...>` names a rule. §21.

        The one thing not checked is a refusal itself: forbidding the *record* of
        a refusal would make the veto silent, which is the failure mode the whole
        carve-out is against.
        """
        if sign != PLUS:
            return None
        rel = self.g.relation_of(proposition)
        if rel is None or rel is self.REFUSED:
            return None
        for node in self.g.instances_of(self.FORBIDDEN):
            (pattern,) = self.g.members(node)
            if self.g.relation_of(pattern) != rel:
                continue
            if unify(self.g, pattern, proposition, {}) is None:
                continue
            e = self.chain.resolve(node, frame.topic, frame.seat)
            if e is not None and e.sign == PLUS:
                return node
        return None

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
        # Returning is an OCCASION, and the smallest unarguable record of it is
        # that this frame, assuming this, is over. Nothing here says what follows
        # -- `<resuming>` and whatever a corpus hangs on the hypothesis do that.
        # This is the same split as `arrived` and `emitted`: crossing is
        # machinery because a frame is anchored and a rule is generic; what the
        # crossing MEANS was never the machinery's to say.
        (assumption,) = self.g.members(frame.purpose) if frame.purpose is not None else (frame.node,)
        self.gate.write(
            self.focus, self.g.rel(self.LEFT, frame.node, assumption), PLUS,
            licence=self.g.rel(self.CONCLUDED, frame.node), source=self.KB,
        )
        return True

    def _wants(self, app) -> set:
        """Which goals this application is a way of serving.

        Read off the evidence, which is where the answer already is: an
        application that consumed `goal(w)` is a response to wanting `w`. That is
        the same comparison `supersedes` makes, and for the same reason -- the
        trail records what each application matched, so nothing new is measured.

        Note what this does NOT use. `fits` says *this rule's consequent could BE
        the goal*, which is backward reading's question and the wrong one here:
        `<use-tap>` concludes `doing(fill(kettle))` and fits nothing, yet it is
        plainly a way of getting water. What makes two rules alternatives is that
        they answer the same want, not that they conclude the same thing.
        """
        out = set()
        for e in app.consumed:
            if self.g.relation_of(e.proposition) is self.GOAL:
                out.add(self.g.member(e.proposition, 0))
        return out

    def _forgo(self, applications, chosen) -> None:
        """Taking one way of getting something is passing up the others.

        This is what arbitration was assumed to do and did not: a rule that lost
        was **deferred**, so quiescence ran it anyway and an agent with two ways
        to do something did both -- including the destructive one. Measured, with
        acts: `emitted: ['fill(kettle)', 'smash(jug1)']`.

        **Passing up is the default, and complementary work is the exception a
        corpus declares.** That is the one judgement here, and it is made on which
        way the error is recoverable rather than on which is more often right:

        | forgo by default | an agent that should have done both under-does. The
        |                  | goal stays open, the veto deposits `open(w)`, and the
        |                  | rule below hands the alternative back. Recoverable.
        | defer by default | an agent that should have done one does both. The jug
        |                  | is smashed. **Not** recoverable.

        So the deposit is deniable, and retrying is one ordinary corpus rule:

            {+open(?w), +forgone(?r, ?w)} => {-forgone(?r, ?w)}

        *When what I wanted is still outstanding, reconsider what I passed up.*
        That is §21's backtracking item, arriving as a consequence rather than as
        machinery, and it is why this had to be a fact about the alternative
        rather than a retraction of the goal.

        ⚠ The apparatus is exempt on both sides -- §13's carve-out again. Nearly
        every bundled rule consumes `goal(?w)`, so without this, applying one
        would forgo backward reading entire.
        """
        wants = self._wants(chosen)
        if not wants or self._claims(self.g.rel(self.STANDING, chosen.rule.node)):
            return
        for a in applications:
            if a.rule is chosen.rule:
                continue
            if self._claims(self.g.rel(self.STANDING, a.rule.node)):
                continue
            for w in wants & self._wants(a):
                self.gate.write(
                    self.focus, self.g.rel(self.FORGONE, a.rule.node, w), PLUS,
                    licence=self.g.rel(self.APPLIED, chosen.rule.node),
                    source=self.KB, mention=True,
                )

    def _passed_up(self, app) -> bool:
        """Has this way of getting what it serves already been passed up?"""
        if self._claims(self.g.rel(self.STANDING, app.rule.node)):
            return False
        return any(
            self._claims(self.g.rel(self.FORGONE, app.rule.node, w))
            for w in self._wants(app)
        )

    def _note_doubt(self, applications, chosen, rank) -> None:
        """Say when the choice was not forced.

        A tie at the top means two rules the agent has no reason to separate,
        and it was previously resolved in silence by whichever was authored
        first. The choice still happens -- arbitration is total (§14) -- but it
        is now on the record that it was arbitrary, which is the difference
        between an agent that is confident and one that merely proceeds.

        Pairwise, so the arity is fixed. §5 refuses a node whose members mean
        different things depending on how many there are, and *the candidates I
        could not separate* is exactly the shape that tempts one.
        """
        best = rank(chosen.rule)
        if best[0] == 0:
            # A tie among `standing` rules is not doubt. The apparatus's order
            # is authored on purpose -- reading before acting, noticing before
            # continuing -- and a deliberate precedence is an answer, not an
            # absence of one. Recording it would bury the real cases in noise,
            # which is what it did.
            return
        rivals = [
            a.rule for a in applications
            if a.rule is not chosen.rule and self._close(rank(a.rule), best)
        ]
        for rival in rivals:
            self.gate.write(
                self.focus, self.g.rel(self.CLOSE, chosen.rule.node, rival.node), PLUS,
                licence=self.g.rel(self.APPLIED, chosen.rule.node),
                source=self.KB, mention=True,
            )

    def _close(self, a: Tuple[int, int], b: Tuple[int, int]) -> bool:
        """Are these two scores close enough to be doubt?

        The knob, read as data: `tolerance(2)` says a gap of two or less is not
        a difference the agent will rely on. Zero by default, so doubt is an
        exact tie until something claims otherwise -- and `standing` never ties
        with an ordinary rule, because a deliberate precedence is an answer.
        """
        return a[0] == b[0] and abs(a[1] - b[1]) <= self._tolerance()

    def _tolerance(self) -> int:
        """How far apart two scores may be and still count as close -- read from
        the graph, so the agent can raise it and can be asked why.

        Zero unless something says otherwise, which is what keeps the default
        free of a constant nobody chose. A numeral is an ordinary atom whose
        *name* reads as a number: nothing in the graph learns arithmetic, and
        this is the only reader that wants any.
        """
        best = 0
        for node in self.g.instances_of(self.TOLERANCE):
            e = self.chain.resolve(node, self.focus.topic, self.focus.seat)
            if e is None or e.sign != PLUS:
                continue
            name = self.g.show(self.g.member(node, 0))
            if name.isdigit():
                best = max(best, int(name))
        return best

    def _widen(self) -> bool:
        """A shortlist that ran dry is not a search that finished (§15, §19).

        The exhaustive pass is **not a fallback** -- §19 is explicit that it is
        the only thing injecting candidates a narrowed recall would never produce,
        and that training recall on its own accepted outputs narrows it
        monotonically otherwise. Here it is also a soundness condition, which is
        the part that was not obvious until the phase went: `quiet` is what
        `<give-up>` asks its verdict at, and `blocked` is an aggregate over a
        finished search. Reaching `quiet` on a shortlist would report *no rule
        fits* about rules nobody asked.
        """
        if self.recall_budget is None or self._widened:
            return False
        self._widened = True
        self.widenings += 1
        return True

    def _enough(self) -> Optional[NodeId]:
        """Is anything claiming that here is over?

        The whole of the loop's part in stopping, and it is a read rather than a
        decision: what counts as enough is a rule's to say, and this only asks
        whether one has said it. Returns what was named, because the record has
        to be able to answer *why did you stop?*.

        Resolved at the current focus, which is what makes it work inside a
        hypothesis for free: an `enough` concluded under a supposition is in force
        there and nowhere else, so the branch ends and the run does not. And what
        crosses out is `likely(enough(g))`, which is a claim about the branch --
        no relation matches it, so a satisfied branch cannot stop its parent by
        accident.
        """
        reason = None
        for node in self.g.instances_of(self.ENOUGH):
            if self.g.has_var(node):
                continue  # a description is not a claim; §15's condition again
            e = self.chain.resolve(node, self.focus.topic, self.focus.seat)
            if e is not None and e.sign == PLUS:
                reason = node
                break
        if reason is None:
            return None
        if self.focus.seat.node in self._vetoed:
            # The veto has already been exercised here, and it did not merely
            # cost a tick: it handed the loop back. Reacting to an open goal --
            # diagnosing it, asking about it, going after it -- is ordinary
            # reasoning that takes as many steps as it takes, and an `enough`
            # consulted again on the next tick would cut it off after one.
            #
            # So an outstanding goal does not delay a stop, it OUTRANKS one, and
            # the agent finishes the ordinary way: at quiescence, which is the
            # only claim that nothing is left that was ever true. Note what that
            # costs and where: nothing, when the goals are achieved or genuinely
            # unreachable (a blocked goal yields no new work, so the loop quiesces
            # at once) -- and the whole of the saving when one is reachable, which
            # is the case where saying *enough* was wrong.
            return None
        if self._notice_open():
            self._vetoed.add(self.focus.seat.node)
            return None
        return reason

    def _notice_open(self) -> bool:
        """The veto: a stop with a goal still outstanding is not a stop.

        Why this is machinery and not the rule a well-written corpus would have.
        *If I still have a question to ask, there is more worth doing* is true,
        and a corpus that states it needs nothing here. But the guarantee wanted
        is that an agent cannot walk away from what it was asked for **because
        nobody thought of the case**, and a convention every corpus must remember
        is exactly the kind this design keeps finding it has lost. §19 already
        made this argument once, about norms, and the shape is the same one:
        unconditionally consulted, entirely contestable.

        What it is not: a phase. It runs at one machinery decision, the way
        `_forbid` runs at the write and `_widen` runs at quiescence, and all three
        are the same move -- **escalate before believing a decline.**

        | `_widen`  | a shortlist that ran dry is not a search that finished |
        | `_forbid` | a write a norm covers never happens |
        | this      | a stop with a goal still open is not a stop |

        **And the refusal writes**, for the reason §19 gives and for a second one.
        A veto depositing nothing would be a silent decline, which is the failure
        being designed against; and it is what makes this terminate, exactly as a
        norm's refusal is what stops a forbidden rule re-applying. Each goal
        vetoes **once**, so what is guaranteed is that nothing is dropped without
        the agent being given the occasion to react -- not that it always finds an
        answer, which no mechanism can promise.
        """
        seat = self.focus.seat.node
        stopped = False
        for node in self.g.instances_of(self.GOAL):
            if self.g.has_var(node):
                continue
            e = self.chain.resolve(node, self.focus.topic, self.focus.seat)
            if e is None or e.sign != PLUS:
                continue
            (wanted,) = self.g.members(node)
            if (seat, wanted) in self._noticed:
                continue
            got = self.chain.resolve(wanted, self.focus.topic, self.focus.seat)
            if got is not None and got.sign == PLUS:
                continue
            self._noticed.add((seat, wanted))
            self.gate.write(
                self.focus, self.g.rel(self.OPEN, wanted), PLUS,
                licence=self.g.rel(self.GOAL, wanted), source=self.KB, mention=True,
            )
            stopped = True
        return stopped

    def _halt(self, reason: NodeId) -> bool:
        """Record that the loop stopped because it was satisfied, not because it
        was exhausted. Once per seat, for the same reason `quiet` is.

        Why this is the register's discipline and not a rule: no rule can stop
        the loop -- nothing owns it (§18) -- and a rule that concluded *stop* and
        then went on being one of many applicable rules would have concluded a
        wish. The claim is the corpus's, the stopping is the register's, and the
        split is the same one `left` and `quiet` already make.

        Why it is checked BEFORE the tick's work rather than after: arbitration is
        total, so by the time an application has been chosen the move is made.
        This is §16's ordering trap -- being careful has to come before the step
        it is about -- and it is the second time it has decided a design.
        """
        seat = self.focus.seat
        if seat.node in self._stopped:
            return False
        self._stopped.add(seat.node)
        self.gate.write(
            self.focus, self.g.rel(self.STOPPED, seat.node, reason), PLUS,
            licence=self.g.rel(self.ENOUGH, reason), source=self.KB,
        )
        return True

    def _wake(self) -> bool:
        """The loop found nothing to do. Say so, in the graph, once per seat.

        §5 named two places the machinery declines -- match and write -- and
        quiescence is the third. It was the only one that declined *silently*,
        and silence is what lets reasoning stop with goals still open and nothing
        anywhere recording that it stopped rather than finished.

        What is deposited is one fact and no interpretation. A watchdog is then
        an ordinary rule with `+quiet(?m)` in its antecedent: inert until the
        loop stops, because nothing else ever writes that. No registry of
        watchdogs, no trigger table, no second loop -- the trigger IS the fact,
        and the rule that wants it says so in its antecedent like any other rule.

        Two things fall out that are worth having. Quiescence is the moment an
        **aggregate over a finished search** becomes legitimate, which is where
        §21's homeless `blocked` belongs -- *no rule fits* is only true of a
        search that is over, and now there is a fact that says one is. And
        because waking is an ordinary write, whatever a watchdog concludes is
        ordinary reasoning: preemptable, defeasible, and in the same trace.

        Once per seat, tracked rather than resolved, because the point of the
        entry is to be *new* -- writing it a second time at the same seat would
        make it re-match forever.
        """
        seat = self.focus.seat
        if seat.node in self._quieted:
            return False
        self._quieted.add(seat.node)
        self.gate.write(
            self.focus, self.g.rel(self.QUIET, seat.node), PLUS,
            licence=self.g.rel(self.QUIET, seat.node), source=self.KB,
        )
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
        if self._hypothetical(frame):
            # **Supposing something must not bring it about.** §13 says nothing
            # leaves a frame and §17 makes containment structural -- but effects
            # were leaving immediately, because dispatch is at the write and the
            # write did not ask where it was standing. Measured: supposing a
            # premise whose rule concludes `+doing(fire(missile))` fired the
            # missile.
            #
            # That is not a leak in the chain -- the conclusion stayed inside and
            # crossed out wrapped, exactly as designed. It is the boundary
            # ignoring the register, which no amount of correct wrapping can fix
            # afterwards, because the act has already happened.
            #
            # It also has to hold before a hypothesis can be used to ASK whether
            # a course of action is acceptable, which is the whole reason to open
            # one about an act. An agent that finds out by doing it has not
            # considered anything.
            #
            # But the REASONING must not stop here, and stopping it was this
            # repair's first mistake -- a plan died at its first action instead
            # of continuing past it. Deciding to act is a **conclusion**; what
            # planning needs from that conclusion is the action's **assumed
            # outcome**. So the same record is deposited under a different name:
            # nothing left the agent, and everything downstream still follows.
            self.gate.write(
                frame, self.g.rel(self.TAKEN, what), "+",
                licence=self.g.instance(self.UTTERANCE, self.KB, what),
                source=self.KB, consumed=(e,),
            )
            return
        self.emitted.append(what)
        # The smallest unarguable record that something left the agent. What it
        # MEANS is `<did>`, and what follows from it is `<assert-act>`.
        self.gate.write(
            frame, self.g.rel(self.EMITTED, what), "+",
            licence=self.g.instance(self.UTTERANCE, self.KB, what),
            source=self.KB, consumed=(e,),
        )

    def _hypothetical(self, frame: Frame) -> bool:
        """Is this frame inside a supposition? Derived from the forest, not held.

        §4 allows one privileged pointer and this is not a second one: the
        purpose of every frame on the path to the root already says whether it
        was entered by supposing.
        """
        f: Optional[Frame] = frame
        while f is not None:
            if f.purpose is not None and self.g.relation_of(f.purpose) is self.SUPPOSING:
                return True
            f = f.parent
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

    # Noticing a deviation used to be a phase here. It is now four bundled rules
    # (`_install_bundle`), and it had no boundary component at all -- §18 already
    # said *surprise is a match*, and the phase was that sentence being false of
    # the implementation.

    # -- backward reading -------------------------------------------------
    #
    # It used to be here: `_expand_goal`, the last interpreter phase, deleted in
    # `nophases`. It is now six bundled rules over three requests -- `<ask-fit>`,
    # `<plan>`, `<expand>`, `<ask-check>`, `<give-up>` -- and `ugm.backward`
    # measured them against it, one rule deleted at a time, before it went.
    #
    # What it was NOT doing is the finding. §14's wall (a rule cannot decide that
    # a ground goal corresponds to a stored generic pattern) was real, and the
    # phase was never the answer to it -- `fit` is. What the phase added on top
    # was a precedence claim written in control flow: it ran ahead of recall and
    # returned early, so while any goal was unexpanded no ordinary rule could
    # apply. That starved forward reasoning badly enough that a goal the corpus
    # could satisfy reported as blocked, which `ugm.backward` found by comparing
    # the two readers rather than by anybody suspecting it.

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
        while m is not None and m is not frame.origin.predecessor:
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
                # The sign has to go INSIDE the wrapper, and only a term can be
                # inside a wrapper. `-b` concluded here means *likely, not-b* --
                # so it crosses as `+likely(not(b))`, never as `-likely(b)`.
                inner = e.proposition
                sign = e.sign
                if sign == MINUS:
                    inner, sign = self.g.rel(self.NOT, e.proposition), PLUS
                out.append(
                    self.gate.write(
                        parent,
                        self.g.rel(wrap, inner),
                        sign,
                        grade=e.grade,
                        licence=self.g.rel(self.CONCLUDED, frame.node),
                        source=self.KB,
                        consumed=(e,),
                        # A mention carried out of a frame is still a mention.
                        # Dropping it here made the gate refuse a conclusion
                        # ABOUT a rule the moment one was drawn under a
                        # hypothesis -- §14's propagation, with a hole in it at
                        # the one place conclusions change hands.
                        mention=e.mention,
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

        # The second way to be over (§19). Asked here, ahead of everything, for
        # the reason §16 found the hard way: arbitration is total, so a check made
        # after one has run is a check made after the move.
        #
        # What it routes to is the `chosen is None` path below, minus the
        # widening -- because widening exists to turn *my shortlist ran dry* into
        # *the search finished*, and satisfaction is not a claim about the search
        # at all. Inside a hypothesis it is `_leave`: enough HERE ends the branch,
        # which is how *is this plan settled* and *is this woken rule done* get
        # their local answer through the door that already existed.
        reason = self._enough()
        if reason is not None:
            if self._leave():
                return Step(arrivals, 0, 0, None, (), "supposed")
            # Terminal, and that is the point rather than an omission: `quiet`
            # continues the loop so a watchdog can key on it, because *the search
            # finished* leaves work worth doing. *Nothing more is worth doing*
            # does not. A corpus wanting a wind-down concludes it before it
            # concludes `enough`; §21 records the case where that is not enough.
            self._halt(reason)
            return Step(arrivals, 0, 0, None, (), "stopped")

        # There is no second line. Every phase is gone: recall, match, defeat,
        # quiescence, arbitrate, apply -- and the two things a register owes,
        # `_leave` when a hypothesis runs out of work and `_wake` when the loop
        # does. Nothing here decides anything a rule could have decided.
        proposed = self._recall()
        # One walk, for every rule proposed. §4 calls the walk the design's most
        # consequential cost and it is: measured, it was 86% of runtime, and 16
        # of every 17 of those walks were the same walk repeated.
        state = Situation(
            self.g, current_state(self.chain, self.focus.topic, self.focus.seat)
        )
        applications: List[Application] = []
        for r in proposed:
            applications.extend(
                match(self.g, self.chain, r, self.focus.topic, self.focus.seat, state)
            )
        # Defeat before quiescence -- see `rules.defeat` for why the order is not
        # interchangeable.
        applications = defeat(self.rules, applications)
        # ...and the fourth way not to run, which is the only one that is a
        # decision: this was a live way of getting what I wanted and I took
        # another. Checked here rather than in `defeat` because it is not a claim
        # that the rule is worse -- it is a claim that the question it answered
        # has been answered.
        applications = [a for a in applications if not self._passed_up(a)]
        applications = [a for a in applications if self._would_change(a)]

        # What the situation recommends, computed once for this tick.
        keys = self._in_play()
        rank = lambda r: self._rank(r, keys)
        chosen = arbitrate(self.rules, applications, rank)
        if chosen is not None:
            self._note_doubt(applications, chosen, rank)
            # Before applying, not after: the rivals are visible now, and this is
            # §16's ordering trap for the fourth time.
            self._forgo(applications, chosen)
        if chosen is None:
            # Nothing came to mind that had anything to do -- which is not the
            # same as nothing being left to do, and §15 says only the second
            # should be believed. So the first escalation is to recall harder.
            #
            # This is not politeness. `quiet` is what `<give-up>` asks a verdict
            # at, and `blocked` claims that NO rule fits: an aggregate over a
            # finished search. A narrowed recall that stopped has not finished a
            # search, it has finished a shortlist. Without this line, turning the
            # budget on would make the agent give up on goals it could have
            # reached, and the trail would show a completed search that never ran.
            if self._widen():
                return Step(arrivals, len(proposed), 0, None, (), "widened")
            # Nothing more to do *here*. If `here` is inside a supposition, that
            # is not the end of the run -- it is the end of the supposition, so
            # carry its conclusions out and restore the register. The frame is
            # left because the loop ran out of work in it, never because a
            # subroutine returned.
            if self._leave():
                return Step(arrivals, len(proposed), 0, None, (), "supposed")
            # ...and if there is nothing to leave either, the loop has stopped.
            # Say so before reporting it, so that anything waiting on the loop
            # stopping gets its turn (`_wake`). This is not a phase: it writes
            # one fact and decides nothing.
            if self._wake():
                return Step(arrivals, len(proposed), 0, None, (), "quiet")
            return Step(
                arrivals,
                len(proposed),
                0,
                None,
                (),
                "quiescent" if arrivals == 0 else "nothing-matched",
            )

        self.selections += 1
        # Something applied, so the shortlist is trusted again. Widening is a
        # state the agent is in, not a mode it is switched into.
        self._widened = False
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
            if s.state not in ("applied", "supposed", "expanded", "quiet", "widened"):
                break
        return out

    # -- the four primitives ----------------------------------------------

    def _recall(self) -> List[Rule]:
        """Never complete, by design (§15). Exhaustive here, which is the
        deliberate-reasoning setting: recall with the budget removed -- with one
        exception, and the exception is the first thing a corpus has ever been
        able to say to this step.

        A rule claimed `dormant` is not proposed until something claims it `due`.
        That is all a callback is. §15 argues recall is where experience belongs
        and where being wrong is recoverable; a pointer hung on a hypothesis is
        experience the corpus supplies instead of learns, arriving at exactly the
        seam that was reserved for it.

        Both are ordinary facts, so both are askable, defeasible and attributable
        -- *which rules is this hypothesis carrying?* is a query, not a field. And
        both are read at the register's own position, so a callback attached
        inside a hypothesis wakes only there.

        Cost, stated rather than discovered: two resolves per rule per tick.
        Cheap now because the rule set is small and `resolve` is a walk; the
        moment it is not, this is an index over two relations, not a redesign.
        """
        live: List[Rule] = []
        for r in self.rules.rules:
            if self._claims(self.g.rel(self.DORMANT, r.node)) and not self._claims(
                self.g.rel(self.DUE, r.node)
            ):
                continue
            live.append(r)
        if self._widened:
            return live

        # Preference does NOT narrow this step, and finding out why was the
        # session's clearest negative result. Filtering recall by *what fits the
        # current goal* starved a rule that reacted to a **blocked** goal --
        # `{+blocked(heat(?a, ?w))} => {+doing(heat(anna, ?w))}` is the most
        # useful rule in that corpus and it does not fit the goal at all.
        #
        # > **Relevance to a goal is one signal, and as a filter it is silent
        # > about everything it is not about.**
        #
        # So preference orders (`arbitrate`) rather than excludes, where being
        # wrong costs a worse choice this tick instead of a plan that stalls.
        # What narrows here stays what a corpus *claimed*: `dormant` unless
        # `due`. An optional cap is kept for measuring, and defaults to off.
        if self.recall_budget is None:
            return live
        keys = self._in_play()
        # By preference alone, not by `_rank`: `standing` is a claim about
        # PRECEDENCE once a rule has matched, not about being brought to mind,
        # and letting it order this step filled every shortlist with apparatus.
        ranked = sorted(
            enumerate(live),
            key=lambda pair: (-self._priority(pair[1], keys), pair[0]),
        )
        out = [r for _, r in ranked[: self.recall_budget]]
        for r in live:
            # Two things a cap may not starve, and they are §19's carve-out
            # arriving for the third and fourth time.
            #
            # A woken callback, because a pointer that recall can drop is not a
            # pointer.
            #
            # And the **apparatus**. §16 kept `standing` out of this step's
            # ORDERING -- it is a claim about precedence once a rule has matched,
            # and letting it sort filled every shortlist with machinery. Inclusion
            # is a different claim, and the measurement forced it: with an ideal
            # table and a budget the run to quiescence got *slower* (239 ticks
            # against 124 exhaustive), because the better the table was at the
            # task the further down it pushed the rules that read, notice and
            # stop. Once stopping is a rule, being late to recall it is being
            # late to stop.
            #
            # > Recall may be incomplete about what to do. It may not be
            # > incomplete about what you must not do -- or about whether to go on.
            #
            # The cost is stated rather than hidden: a corpus that marks fifty
            # rules `standing` has no budget left, and that is its own claim about
            # what must always come to mind.
            if r not in out and (
                self._claims(self.g.rel(self.DUE, r.node))
                or self._claims(self.g.rel(self.STANDING, r.node))
            ):
                out.append(r)
        return out

    def _in_play(self) -> set:
        """What the situation is about, as a set of relation nodes.

        The current moment's delta -- *what just changed* -- rather than the whole
        state, because a key that matches everything ranks nothing. This is the
        cheapest thing that recurs across situations, and the point of putting it
        here is that it is one method: a better answer replaces it without
        touching the loop, the table, or any rule.
        """
        out = set()
        for e in self.focus.seat.delta:
            rel = self.g.relation_of(e.proposition)
            if rel is not None:
                out.add(rel)
        # ...and what the agent is TRYING TO DO, which is not the same question
        # and turned out to be the one that matters. Keyed only on what changed,
        # a table cannot discriminate on goal-directed work: every domain the
        # agent knows about is in play all the time, and being in play says
        # nothing about being useful. A live goal does.
        for s in current_state(self.chain, self.focus.topic, self.focus.seat):
            if s.sign == PLUS and self.g.relation_of(s.proposition) is self.GOAL:
                wanted = self.g.member(s.proposition, 0)
                out.add(wanted)
                # ...and its RELATION, which is the half that transfers. A key
                # that is the goal itself is true of one episode: what an agent
                # learned about `boiling(kettle)` says nothing when it is next
                # asked for `boiling(pot)`, and a table that cannot generalise is
                # a cache. The relation is the coarsest thing two episodes can
                # share, so it is where experience can accumulate at all.
                rel = self.g.relation_of(wanted)
                if rel is not None:
                    out.add(rel)
        return out

    def _rank(self, rule: Rule, keys: set) -> Tuple[int, int]:
        """The sort key arbitration uses after defeat. Lower is better.

        `standing` first, so the reading apparatus keeps the authored precedence
        it already had -- preference is about which of the agent's OWN moves is
        the better one, never about whether to keep reading. Then preference,
        then (in `arbitrate`) authored order."""
        if self._claims(self.g.rel(self.STANDING, rule.node)):
            return (0, 0)
        return (1, -self._priority(rule, keys))

    def _priority(self, rule: Rule, keys: set) -> int:
        """**How much** this situation recommends this rule: the sum of the
        scores of the `prefer` claims whose key is in play.

        An order alone cannot distinguish *one clear best* from *two I cannot
        separate*, and only a magnitude can say how far apart two candidates are.
        So the table carries a score, and scores are compared as **cardinals**.

        This adds nothing ordinal. §10's grades are a different quantity on a
        different scale and keep their own composition rule (§12's weakest link);
        an entry's grade here says how confident the agent is *in the
        recommendation*, which is not how strong the recommendation is.
        """
        score = 0
        for node in self.g.instances_of(self.PREFER):
            members = self.g.members(node)
            if len(members) != 3 or members[0] != rule.node or members[1] not in keys:
                continue
            e = self.chain.resolve(node, self.focus.topic, self.focus.seat)
            if e is None or e.sign != PLUS:
                continue
            name = self.g.show(members[2])
            if name.isdigit():
                score += int(name)
        return score

    def _claims(self, proposition: NodeId) -> bool:
        e = self.chain.resolve(proposition, self.focus.topic, self.focus.seat)
        return e is not None and e.sign == PLUS

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
            # The register MOVES; it is not replaced. Minting a fresh frame here
            # dropped the parent, the purpose and the wrap -- so a `causes` rule
            # applied under a hypothesis orphaned the register, `_leave` could
            # never fire, and everything concluded under that hypothesis stayed
            # inside it with nothing saying so. §4 allows one register; advancing
            # it is a seat move, and §17 says a seat move is what `reseat` is for.
            self.gate.reseat(self.focus, self.chain.succeed(self.focus.seat, licence))
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
            forbidding = self._forbid(self.focus, grounded, m.sign)
            if forbidding is not None:
                # A forbidden conclusion never lands, so the chain never says it
                # and the rule would match again on every tick, forever. What
                # settles it is the refusal: once THAT is recorded, applying
                # again would change nothing. So the rule applies exactly once,
                # the record exists, and the loop can go quiet -- which is the
                # difference between a norm and a livelock.
                record = self.g.rel(
                    self.REFUSED, grounded, self.rules.SIGN[m.sign], forbidding
                )
                if self.chain.resolve(record, self.focus.topic, self.focus.seat) is None:
                    return True
                continue
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

        Inheritance has to start somewhere, and `app.rule.mentions` is the
        source: a rule AUTHORED naming a rule -- `+resume(?h, <cb>)`, the `<...>`
        marker the surface already reads for facts -- is mentioning. Without it a
        rule that attaches a rule to something concludes a structurally generic
        proposition from entries that are not mentions, and quiescence drops it
        as *nothing to do*.
        """
        return app.rule.mentions or any(e.mention for e in app.consumed)

    # -- asking -----------------------------------------------------------

    def holds(self, proposition: NodeId, locus: Optional[Moment] = None) -> Optional[str]:
        locus = self.focus.topic if locus is None else locus
        return self.chain.holds(proposition, locus, self.focus.seat)

    # -- experience -------------------------------------------------------

    def review(self) -> List[Tuple[Rule, NodeId]]:
        """*Which rules earned the outcome?* -- asked of a finished episode.

        **Offline, and that is a position rather than an implementation detail.**
        Credit needs the outcome and the outcome is not known until the episode
        ends, so nothing here runs in the loop and nothing about the loop changes.
        It is also why this is a method and not a request answered at `quiet`: a
        run that ends satisfied ends at `stopped`, which is terminal, and the
        episodes most worth learning from are exactly the ones that went well.

        **It needs no new bookkeeping**, which is the finding that made it
        buildable. R5 already licenses every derived entry with `applied(<R>)`
        because the trail is load-bearing for §12's weakest link -- so walking
        back from what was achieved reaches the rules that produced it, and only
        those. Measured on a corpus with two ways to get water: the walk returns
        the rule that was used and not the rule that was available.

        What it deposits is `helped(<R>, <key>)` and no interpretation, the same
        split as every other occasion (§17). Turning that into a preference is a
        rule, because *how much a rule having helped once should count* is a
        claim and §4 puts claims in data.

        The key is the goal's **relation**, not the goal. That is the only choice
        here that could have gone otherwise, and it is forced by wanting anything
        to transfer: a row keyed on `boiling(kettle)` is true of one episode.
        """
        rule_at = {r.node: r for r in self.rules.rules}
        earned: List[Tuple[Rule, NodeId]] = []
        seen_pairs = set()
        for s in current_state(self.chain, self.focus.topic, self.focus.seat):
            if s.sign != PLUS or self.g.relation_of(s.proposition) is not self.GOAL:
                continue
            wanted = self.g.member(s.proposition, 0)
            key = self.g.relation_of(wanted)
            if key is None:
                continue
            got = self.chain.resolve(wanted, self.focus.topic, self.focus.seat)
            if got is None or got.sign != PLUS:
                # Nothing was achieved, so there is nothing to credit. Note what
                # this does NOT do: blame. A rule that was applied on a failed
                # episode was not thereby wrong -- the episode may have been
                # impossible -- and §19's whole argument against training recall
                # on its own outputs applies twice as hard to training it on its
                # own failures.
                continue
            for node in self._support(wanted):
                e = self.chain.resolve(node, self.focus.topic, self.focus.seat)
                if e is None or e.licence is None:
                    continue
                if self.g.relation_of(e.licence) is not self.APPLIED:
                    continue
                rule = rule_at.get(self.g.member(e.licence, 0))
                if rule is None or (rule.node, key) in seen_pairs:
                    continue
                seen_pairs.add((rule.node, key))
                earned.append((rule, key))
                self.gate.write(
                    self.focus, self.g.rel(self.HELPED, rule.node, key), PLUS,
                    licence=self.g.rel(self.ACHIEVED, wanted), source=self.KB,
                    mention=True,
                )
        return earned

    def blame(self) -> List[Tuple[Rule, NodeId]]:
        """*Which rules cost the agent something it wanted?* -- the other half,
        and the one that only exists because a task is split into subgoals.

        **Failure at episode level has no author.** Many rules ran, one outcome
        was bad, and nothing attributes it -- which is why `review` deliberately
        refuses to blame: a failed episode may have been an impossible one.

        A lost *subgoal* is different, and the difference is §9's. Two ways a goal
        can fail to hold, and only one of them is somebody's doing:

        | no entry at all | it was never reached. Many causes, no author. |
        | an entry says `-` | something MADE it false, and that entry has a licence. |

        So blame runs the same walk as credit over a denial instead of an
        assertion, and it reaches the decision rather than the physics: measured,
        from a lost `intact(jug1)` back through the rule that broke it, the act
        that was taken, and the rule that chose the act.

        Ground goals only. Backward reading expands into generic subgoals like
        `heat(?a, kettle)` which were never meant to hold as stated, and counting
        those as failures would blame every rule for every search.
        """
        rule_at = {r.node: r for r in self.rules.rules}
        out: List[Tuple[Rule, NodeId]] = []
        seen = set()
        for s in current_state(self.chain, self.focus.topic, self.focus.seat):
            if s.sign != PLUS or self.g.relation_of(s.proposition) is not self.GOAL:
                continue
            wanted = self.g.member(s.proposition, 0)
            if self.g.has_var(wanted):
                continue
            key = self.g.relation_of(wanted)
            got = self.chain.resolve(wanted, self.focus.topic, self.focus.seat)
            if key is None or got is None or got.sign != MINUS:
                continue
            for node in self._support(wanted) | {wanted}:
                e = self.chain.resolve(node, self.focus.topic, self.focus.seat)
                if e is None or e.licence is None:
                    continue
                if self.g.relation_of(e.licence) is not self.APPLIED:
                    continue
                rule = rule_at.get(self.g.member(e.licence, 0))
                if rule is None or (rule.node, key) in seen:
                    continue
                seen.add((rule.node, key))
                out.append((rule, key))
                self.gate.write(
                    self.focus, self.g.rel(self.HARMED, rule.node, key), PLUS,
                    licence=self.g.rel(self.GOAL, wanted), source=self.KB,
                    mention=True,
                )
        return out

    def _support(self, proposition: NodeId) -> set:
        """Everything that held this up, transitively. The trail, walked."""
        seen, frontier = set(), [proposition]
        while frontier:
            p = frontier.pop()
            if p in seen:
                continue
            seen.add(p)
            e = self.chain.resolve(p, self.focus.topic, self.focus.seat)
            if e is None:
                continue
            for s in self.chain.trail(e):
                frontier.append(s.proposition)
        return seen

    def learned(self, score: int = 3) -> List[str]:
        """What this episode has to say to the next one, as surface text.

        Offline learning crossing an episode boundary is a corpus being written,
        and a corpus is text -- so what an agent learned is **readable, editable
        and arguable** rather than a weight somewhere. That is not decoration:
        §19 puts experience in recall precisely because being wrong there is
        recoverable, and it is only recoverable if it can be found and denied.
        """
        # The one policy in this method, stated rather than buried: a rule that
        # cost the agent something is not recommended, however well it served the
        # goal it was serving. Without this the signal actively misleads --
        # measured, before subgoals were used: the rule that smashed a jug to get
        # water was ON the support of the water, so credit recommended it.
        #
        # Suppression rather than a negative score, because the table's numerals
        # are non-negative (a numeral is an atom whose name reads as a number, and
        # `-3` does not). §21 records that; *how badly* is not sayable yet, only
        # *at all*.
        harmed = {rule.node for rule, _ in self.blame()}
        rows: List[str] = []
        seen = set()

        def row(rule: Rule, key: NodeId) -> None:
            if rule.name is None or rule.node in harmed or (rule.node, key) in seen:
                return
            seen.add((rule.node, key))
            rows.append(f"fact prefer(<{rule.name}>, {self.g.show(key)}, {score})")

        for rule, key in self.review():
            row(rule, key)
        # ...and the half that suppression cannot supply. Measured: an episode
        # that smashed a jug for water blamed the smasher, dropped it from these
        # rows, and **smashed the jug again**, because omitting a rule leaves it
        # exactly where it was -- first in authored order.
        #
        # > **Suppression is not a decision.** It can say *do not recommend this*.
        # > It cannot say *do that instead*, and only the second changes a run.
        for rule, key in self._instead_of(harmed):
            row(rule, key)
        return rows

    def _instead_of(self, harmed: set) -> List[Tuple[Rule, NodeId]]:
        """The live alternatives to what cost the agent something.

        Blame names the rule that did the damage; it is silent about what else
        was available, because the rule that was passed up never ran and so is on
        no trail. **Forgoing already recorded it.** `forgone(A, w)` is deposited
        when `A` was a live way of getting `w` and something else was taken, and
        it is licensed by `applied(<winner>)` -- so *what did I do instead of A*
        is a question the deposit already answers.

        Joining them needs no new bookkeeping, which is the same result credit
        assignment had: a blamed winner names its own forgone alternatives, and
        those are exactly the rules worth promoting. Neither half is a signal
        alone -- blame without forgoing suppresses into the same choice, and
        forgoing without blame recommends whatever was passed up for any reason.

        ⚠ An alternative that is itself blamed earns nothing; `learned` filters
        both halves through the same suppression, so a world whose every route
        does damage recommends none of them rather than the least-examined one.
        """
        rule_at = {r.node: r for r in self.rules.rules}
        out: List[Tuple[Rule, NodeId]] = []
        for node in self.g.instances_of(self.FORGONE):
            # ⚠ The WANT must be ground, not the whole node. A `forgone` node
            # names a rule, and a rule node is generic by construction -- so
            # `has_var(node)` is true of every real deposit, and guarding on it
            # silently returned nothing. Same shape as `blame`'s guard, which is
            # about generic subgoals like `heat(?a, kettle)` that were never
            # meant to hold as stated, and belongs on the same member.
            if self.g.has_var(self.g.member(node, 1)):
                continue
            e = self.chain.resolve(node, self.focus.topic, self.focus.seat)
            if e is None or e.sign != PLUS or e.licence is None:
                continue
            if self.g.relation_of(e.licence) is not self.APPLIED:
                continue
            if self.g.member(e.licence, 0) not in harmed:
                continue
            alt = rule_at.get(self.g.member(node, 0))
            key = self.g.relation_of(self.g.member(node, 1))
            if alt is not None and key is not None:
                out.append((alt, key))
        return out

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
