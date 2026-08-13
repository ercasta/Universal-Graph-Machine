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


class Answerer(NamedTuple):
    """A tool: something that answers a request without searching for it.

    It is deliberately the same shape as a rule where anything looks at it --
    a `name` in the `<...>` namespace and a `node` other statements can be about
    -- because `review` and `blame` walk licences and must not care which kind of
    statement produced an entry. A tool that credit could not reach would be a
    tool nothing could learn about.
    """

    name: str
    node: NodeId
    request: NodeId
    fn: object  # fn(machine, frame, entry) -> NodeId | None


class Machine:
    def __init__(self) -> None:
        self.g = Graph()
        self.chain = Chain(self.g)
        self.gate = Gate(self.g, self.chain)
        self.rules = RuleSet(self.g, self.chain)
        self.channels = Channels(self.g)

        self.SAYS = self.g.atom("says")
        self.APPLIED = self.g.atom("applied")
        # The same claim as `applied(<R>)`, but as a proposition a rule can
        # match rather than a licence only Python can read.
        self.EXERCISED = self.g.atom("exercised")
        # §6's *a root goal is never checked*, and §12's reason it could not be:
        # a root goal is a `goal(?w)` with **no** `subgoal(?p, ?w)`, which is a
        # negative existential, and a `-` member says *an entry denies this*,
        # never *for no ?p*. So it gets the treatment `blocked` got -- a REQUEST
        # the machinery answers by looking, because an aggregate over what the
        # rules produced is the machinery's business and not a rule's.
        self.ROOT = self.g.atom("root")        # ask
        self.ROOTED = self.g.atom("rooted")    # ...and the answer, when it is one
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
        # Tools. §21's honest debt, taken: a request answered by *a function
        # rather than a search* is how `fit` and `verdict` escape §5's wall, and
        # it is the only shape in this design that a thing outside the agent can
        # legitimately take. What was wrong with it was never the shape -- it was
        # that the BINDING of answerer to request lived in Python, so a corpus
        # could not see which tools existed, could not retire one, and could not
        # reason about one. Two ordinary relations fix all three:
        #
        #   answers(<M>, ask)          M answers `ask` requests. A FACT, so a
        #                              corpus can query it (R4) and deny it.
        #   answered(<M>, ask(x), y)   what M said. A record, not a claim --
        #                              exactly `arrived` to `says`, and the
        #                              corpus supplies the trust rule.
        #
        # ⭐ **A tool may propose; it may never conclude.** The answer is a
        # deposit ABOUT what the tool said, so believing it is an authored rule
        # with a grade. Let a tool write a belief directly and §12's weakest link
        # has a link with nothing behind it and `why()` stops answering -- the
        # not-lossy criterion failing at the one place nothing else guards.
        # Which name table a domain's documents were written in. Provenance
        # already records WHERE a fact came from (its channel); this records the
        # scope its names were resolved in, which is the other half and the half
        # a session needs to be rebuilt into the same nodes rather than twins.
        # ⚠ THE one `loaded` node. `Loader` minted its own with `g.atom`, which
        # does not intern -- so the licence the loader stamped and the licence
        # the machine looked for were two nodes with one name, and rendering a
        # session found no told facts at all. The twin trap, in the code that
        # exists to describe provenance.
        self.LOADED = self.g.atom("loaded")
        self.SCOPED = self.g.atom("scoped")
        self.ANSWERS = self.g.atom("answers")
        self.ANSWERED = self.g.atom("answered")
        # ⭐⭐⭐ Re-asking. §6 recorded *a request can only be made once* and §21
        # carried it as one of the two original four hats still open.
        #
        #     again(<request>, <occasion>)   ask this again, because of this
        #
        # What was blocked was never the chain. §10's two indices already make
        # *the same claim, later* expressible, and `deposit` mints a fresh entry
        # for a proposition it has seen before without complaint. What forbids a
        # re-ask is `_would_change` -- quiescence, at the RULE level: an
        # application that restates what the chain already says is not a step, so
        # `<ask-check>` concluding `+check(p, w)` a second time is dropped.
        #
        # So the missing thing is a fresh NODE, which is exactly what the design
        # said, and a wrapper is one. `again(req, occ)` is an ordinary node that
        # differs per occasion, so concluding it IS a step; and re-delivering the
        # wrapped request through the gate reaches whatever answers it, because
        # answering is an `on_write` hook and a write is a write. A tool becomes
        # re-askable by the same line that makes `check` re-askable, and neither
        # answerer learns a thing about re-asking.
        self.AGAIN = self.g.atom("again")
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
        # ⭐⭐ The other three knobs, by the SAME argument `tolerance` was made a
        # fact for: *how careful am I being is a claim with a trail, and a rule
        # can raise it before an irreversible step.* They were Python fields,
        # which made them the one kind of decision this design does not allow --
        # one nobody can ask about or argue with.
        #
        #     budget(3)       how many rules recall may propose
        #     depth(4)        how deep a hypothesis may nest
        #     hypotheses(5)   how many may be open at once
        #
        # The DEFAULT stays in Python, exactly as `tolerance`'s zero does: a
        # default nobody has to choose is not a hidden decision, it is the
        # absence of one.
        # ...and what the machinery does when it reaches one, as EVENTS rather
        # than counts. A count cannot be a fact here: `widened(2)` and
        # `widened(3)` are different propositions and both would hold. §17's
        # pattern is the right one and was always the right one -- deposit the
        # smallest unarguable record and let rules say what it means, exactly as
        # `quiet`, `left`, `stopped` and `emitted` do.
        #
        #     widened(<seat>)        recall reached past its shortlist
        #     reached(<seat>)        a domain was brought back out of dormancy
        #     bounded(<which>)       a bound stopped a supposition
        #
        # ⚠ `_enter`'s comment has said *each reports that it was hit rather
        # than stopping silently (§13)* since it was written, and the report was
        # `self.exhausted += 1` -- a Python counter no rule can read. The code
        # claimed a property it did not have.
        self.WIDENED = self.g.atom("widened")
        self.REACHED = self.g.atom("reached")
        self.BOUNDED = self.g.atom("bounded")
        self.BUDGET = self.g.atom("budget")
        self.DEPTH = self.g.atom("depth")
        self.HYPOTHESES = self.g.atom("hypotheses")
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
            "forgone": self.FORGONE, "exercised": self.EXERCISED,
            "concluded": self.CONCLUDED,
            "root": self.ROOT, "rooted": self.ROOTED,
            "answers": self.ANSWERS, "answered": self.ANSWERED,
            "scoped": self.SCOPED, "loaded": self.LOADED,
            "again": self.AGAIN,
            "dormant": self.DORMANT, "due": self.DUE, "prefer": self.PREFER,
            "forbidden": self.FORBIDDEN, "refused": self.REFUSED,
            "standing": self.STANDING,
            "recall": self.RECALL, "recalled": self.RECALLED,
            "close": self.CLOSE, "tolerance": self.TOLERANCE,
            "widened": self.WIDENED, "reached": self.REACHED,
            "bounded": self.BOUNDED,
            "budget": self.BUDGET, "depth": self.DEPTH,
            "hypotheses": self.HYPOTHESES,
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
        # ⭐⭐⭐ **A session is what it was TOLD.** Everything that entered from
        # outside, in order: corpora loaded, arrivals delivered, runs asked for.
        # Saving that rather than the object graph is what §3's determinism is
        # worth -- measured across four hash seeds, the same inputs reproduce
        # the same 619 entries byte for byte -- and it keeps the save file
        # READABLE and arguable where a pickle would be neither.
        # Which document is being read right now, so a rule's reification is
        # stamped with it. A rule had no provenance at all: `RuleSet.rules` is a
        # Python list, and nothing said which corpus authored which rule.
        self._authoring_source: Optional[NodeId] = None
        # The bundle is not something the agent was TOLD -- it is what it reads
        # with. Journalling it would replay it into a machine that already has
        # it: `<intake> is already declared`, which is how this was found.
        self._booting = True
        # Which corpus scope an arrival's term was written in, so replay
        # rebuilds the same node and not a twin. Set by `Loader.say`.
        self._saying_scope: Optional[str] = None
        # ...and whether we are re-living it. See `_dispatch`.
        self.replaying = False
        # Named name-scopes, so two documents can be about the same kettle. A
        # corpus is a bound and that is what makes reference a construction
        # rather than an inference; naming the bound lets it span documents
        # without weakening it. See `text.Loader`.
        self.scopes: dict = {}
        # Applications carried across ticks, per seat. See `_applications`.
        self._match_cache: dict = {}
        # What matching actually produced, against what the loop then weighed.
        # Two numbers rather than one, because the whole claim is the gap: the
        # loop used to make them equal by rediscovering its options every tick.
        self.matched = 0
        self.considered = 0
        # The resolved state, kept rather than rebuilt. See `_state`.
        self._state_cache: dict = {}
        self._stopped: set = set()
        self._noticed: set = set()
        self._vetoed: set = set()
        self._reified: set = set()
        self._exercised: set = set()
        # §19. `None` is the deliberate-reasoning setting -- recall with the
        # budget removed -- and it is the default, because narrowing is a claim
        # about what an agent has learned and a fresh agent has learned nothing.
        self.recall_budget: Optional[int] = None
        self._widened = False
        self.recoveries = 0
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
                             self.FORGONE, self.EXERCISED, self.CONCLUDED,
                             self.ROOT, self.ROOTED,
                             self.DUE, self.VERDICT, self.PURSUED, self.PREFER,
                             self.FORBIDDEN, self.STANDING,
                             self.RECALL, self.RECALLED, self.CLOSE,
                             self.TOLERANCE, self.BUDGET, self.DEPTH,
                             self.HYPOTHESES, self.WIDENED, self.REACHED,
                             self.BOUNDED}

        # A rule becomes data when it is authored, not when someone remembers to
        # ask. Backward reading is rules now, and it enumerates `+rule(?r)` --
        # so a rule loaded after a call to `reify_all` would have been invisible
        # to the reader, with nothing anywhere saying so.
        self.rules.on_rule.append(self.reify)

        self.answerers: List["Answerer"] = []
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
        # ⭐⭐⭐ **The apparatus eats its own cooking.** `answers(<M>, ask)` was
        # built so that a TOOL's binding could be data -- visible, queryable,
        # deniable -- and it shipped with exactly zero apparatus users: every
        # request the machinery answered, it answered because a Python line in
        # this constructor said so. That is §21's most frequent defect in this
        # codebase, stated as *something the machinery knows and no rule can ask
        # about*, and it is the same one `exercised`, the entry's grade and a
        # tool's binding each closed. The fix is always the same: put it in the
        # graph.
        #
        # Six requests, six bindings, all of them facts:
        #
        #   <fit>       fit      could this rule produce this goal?
        #   <settle>    check    is this goal already satisfied, in these bindings?
        #   <verdict>   verdict  did ANYTHING fit it?  -- the aggregate
        #   <root>      root     is this what I was asked for?
        #   <remember>  recall   what comes to mind about this?
        #   <re-ask>    again    ask that again, because of this
        #
        # ⚠⚠⚠ **Deniable is not the same as forgettable, and only two of them
        # are both.** The criterion is not preference:
        #
        # > **A capability whose absence is the status quo ante is safe to
        # > retire.** Deny `<re-ask>` and each question is asked once; deny
        # > `<root>` and the general stop rule never fires and the agent runs to
        # > quiescence. Both are what it did before the commit that added them,
        # > and both were sound.
        #
        # The other four are §19's carve-out arriving a fifth time -- deny
        # `<fit>` or `<settle>` and backward reading stops; deny `<verdict>` and
        # a goal nothing can reach is never reported blocked. So they are marked
        # `standing`, which is the fact the bundle already uses for exactly this
        # claim: **overridable but not forgettable**, and `_answer` records a
        # refusal rather than obeying. A corpus can still argue with any of
        # them; it cannot make the agent stop reading.
        #
        # ⚠⚠⚠ **`<remember>` is the fourth, and I put it in the safe column
        # first.** The reasoning was *narrowing off means exhaustive recall,
        # which is the default* -- and it is wrong about which thing this
        # answers. `_remember` is not the narrowing; it is the ANSWER to the
        # recall request, and `<ask-fit>` keys on `recalled(?r, ?w)`, so nothing
        # asks `fit` about anything without it. Measured on a goal reachable
        # only backwards: 15 ticks and two subgoals becomes 4 ticks and none.
        # The narrowing lives in the `prefer` table and the budget, which are
        # separately deniable and were what the criterion was actually about.
        self.gate.on_write.append(self._dispatch)
        self.gate.on_write.append(self._enter)
        self.gate.on_write.append(self._answer)
        for name, request, fn, standing in (
            ("fit", "fit", self._fit, True),
            ("settle", "check", self._settle, True),
            ("verdict", "verdict", self._verdict, True),
            ("root", "root", self._root, False),
            ("remember", "recall", self._remember, True),
            ("re-ask", "again", self._again, False),
        ):
            # `fn` is `(frame, entry)`; the answerer protocol is `(machine,
            # frame, entry)`, and the answer is None because the apparatus
            # CONCLUDES where a tool PROPOSES. That is the one asymmetry left in
            # the door, and it is the right one: a tool is outside the agent, so
            # what it says lands as `answered(<M>, req, y)` for a corpus to
            # believe or not; `<settle>` is the agent, so what it finds lands as
            # `achieved`. Same binding, same trail, different standing to speak.
            a = self.answerer(name, request, lambda _m, f, e, fn=fn: fn(f, e))
            if standing:
                self.gate.write(
                    self.focus, self.g.rel(self.STANDING, a.node), PLUS,
                    licence=self.g.rel(self.REIFIED, a.node), source=self.KB,
                    mention=True,
                )
        self.gate.veto.append(self._forbid)
        self._booting = False
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
        src = self._authoring_source or self.KB
        w = lambda p: self.gate.write(
            f, p, "+", licence=self.g.rel(self.REIFIED, rule.node), source=src, mention=True
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
        if len(self.focus.ancestry()) > self._knob(self.DEPTH, self.max_depth):
            self.exhausted += 1
            self._note(self.g.rel(self.BOUNDED, self.DEPTH))
            return
        if len(self._supposed) >= self._knob(
                self.HYPOTHESES, self.supposition_budget):
            self.exhausted += 1
            self._note(self.g.rel(self.BOUNDED, self.HYPOTHESES))
            return
        assumption, wrap = self.g.members(e.proposition)
        self._enacted.add(e.node)
        # ⭐⭐⭐ **Whether to suppose again is REASONING, and it was Python.**
        # This line used to drop a second supposition of the same assumption --
        # *supposing the same thing twice derives nothing new* -- which is true
        # only while nothing has changed, and it made a hypothesis
        # unfinishable: explore `broken(pipe)`, find the reasoning wants
        # `wet(pipe)`, conclude nothing and discharge; then be told `wet(pipe)`,
        # and the hypothesis is never revisited.
        #
        # ⚠⚠ The first repair was worse: a Python test for *was this licensed by
        # `again`*, which put the decision back in the machinery one layer down.
        # Measured instead -- **the dedup was redundant.** Quiescence already
        # stops a RULE re-concluding `suppose(p, w)`, because the proposition
        # already holds; the runaway the old comment feared (a rule inside the
        # frame re-supposing its own assumption) runs 4 ticks to quiescence with
        # the dedup and 4 without, identically.
        #
        # So both are gone. What decides that a hypothesis is worth entering
        # again is a corpus writing `again(suppose(p, w), <occasion>)` -- the
        # same argument re-asking is built on, and now the only one.
        #
        # `_supposed` stays as a COUNT, for `hypotheses(n)`: how many distinct
        # assumptions have been entered.
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
        state = self._state()
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

    def _root(self, frame: Frame, e: Entry) -> None:
        """Answer *is this what I was asked for, or something I asked myself?*

        §6 recorded the gap and §12 recorded why it could not be a rule: a root
        goal is a `goal(?w)` with **no** `subgoal(?p, ?w)`, and a `-` member says
        *an entry denies this*, never *for no `?p`*. That is the same shape as
        `blocked` -- a negative existential over what the rules produced -- so it
        gets the same treatment, which is the point of having settled it once.

        It answers only when the answer is YES. `rooted(w)` is deposited if
        nothing claims `w` is anybody's subgoal; nothing is written otherwise,
        exactly as `_verdict` writes `blocked` only when nothing fits. A
        machinery that answered *no* would be asserting a negative existential of
        its own, and §17's rule is to deposit the smallest unarguable record.

        What it unblocks is one line a corpus could not write before:

            rule <done> = implies( { +goal(?w), +rooted(?w), +?w },
                                   { +enough(?w) } )

        *What I was asked for holds, so I am done.* The version without `rooted`
        is unsound and running it is how the gap was found -- `<expand>` writes
        `+goal(sub)` for every subgoal backward reading derives, so the agent
        stopped at the first satisfied SUBGOAL: measured, tick 51 of a run whose
        goal arrived at 57.

        ⚠ It is asked, not volunteered, for the reason §19 gives about recall:
        this is a question about a search that has got somewhere, and asking it of
        every goal the moment it appears would answer before `<expand>` had
        written the `subgoal` entry that makes the answer false. The corpus asks
        when it is ready to stop.
        """
        if e.sign != PLUS or self.g.relation_of(e.proposition) is not self.ROOT:
            return
        wanted = self.g.member(e.proposition, 0)
        for node in self.g.instances_of(self.SUBGOAL):
            if self.g.member(node, 1) != wanted:
                continue
            s = self.chain.resolve(node, frame.topic, frame.seat)
            if s is not None and s.sign == PLUS:
                return
        self.gate.write(
            frame, self.g.rel(self.ROOTED, wanted), PLUS,
            licence=self.g.rel(self.GOAL, wanted), source=self.KB, mention=True,
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
        state = self._state()
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

    def _note(self, proposition: NodeId) -> None:
        """Record that the machinery did something a rule may care about.

        The user's reason, and it is the right one: these should be **reasonable
        over**. An agent that has reached past its shortlist twice, or been
        stopped by a bound, knows something about its own effort -- and until
        now that lived in a Python counter, which is §21's defect for the
        seventh time.

        Deduped by reading the graph: restating is not revising (§8), and the
        claim is *this happened here*, not how often.
        """
        if self._claims(proposition):
            return
        self.gate.write(
            self.focus, proposition, PLUS,
            licence=self.g.rel(self.QUIET, self.focus.seat.node),
            source=self.KB, mention=True,
        )

    def _knob(self, relation: NodeId, default):
        """A knob a corpus can turn, read from the graph.

        Generalised out of `_tolerance`, which had this shape and this argument
        first: a numeral is an ordinary atom whose *name* reads as a number, so
        nothing in the graph learns arithmetic and only the reader that wants one
        does. Highest wins, so raising a bound is a claim and lowering it is a
        different claim about the same thing, settled by §12's ordinary defeat.
        """
        best = None
        for node in self.g.instances_of(relation):
            e = self.chain.resolve(node, self.focus.topic, self.focus.seat)
            if e is None or e.sign != PLUS:
                continue
            name = self.g.show(self.g.member(node, 0))
            if name.isdigit() and (best is None or int(name) > best):
                best = int(name)
        return default if best is None else best

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
        if self._knob(self.BUDGET, self.recall_budget) is None or self._widened:
            return False
        self._widened = True
        self.widenings += 1
        self._note(self.g.rel(self.WIDENED, self.focus.seat.node))
        return True

    def _outstanding(self) -> bool:
        """Is anything the agent was asked for still unmet? Read the same way
        `_notice_open` reads it, because it is the same question."""
        for node in self.g.instances_of(self.GOAL):
            if self.g.has_var(node):
                continue
            e = self.chain.resolve(node, self.focus.topic, self.focus.seat)
            if e is None or e.sign != PLUS:
                continue
            got = self.chain.resolve(
                self.g.member(node, 0), self.focus.topic, self.focus.seat
            )
            if got is None or got.sign != PLUS:
                return True
        return False

    def _recover(self) -> bool:
        """Nothing applies -- but is that because a domain is out of mind? (§19)

        §19's carve-out for the fourth time, and the argument transfers whole.
        Unloading a domain is **safe to be wrong about**: worst case it comes
        back, which is why *when to unload* may be an ordinary defeasible rule
        and is exactly the seam experience belongs at. Reaching for it again may
        **not** be, and the asymmetry is the same one every time:

            Recall may be incomplete about what to do.
            It may not be incomplete about what it has NOT looked at.

        Because `quiet` is what `<give-up>` asks its verdict at, and `blocked`
        claims that **nothing** answers a goal -- an aggregate over a *finished*
        search. A goal whose evidence is merely dormant would be reported
        unreachable, and the trail would show a completed search that never ran.

        ⚠⚠⚠ **Only when something is outstanding**, and running it without that
        is how the shape became clear. The unsoundness is precise: `blocked` is
        about a GOAL. A run with nothing outstanding declines nothing -- and
        escalating anyway wakes every domain at the end of every run, which threw
        away the whole 14.5x saving and failed two dormancy checks that were
        right to fail. So this carve-out is narrower than `_widen`'s and says so:
        *escalate before believing a decline about something I was asked for.*

        Everything comes back, not one domain chosen by some order: which to try
        first is a judgement, and §15 refuses orders nobody can justify.

        ⚠ **It terminates on its own, and a `_widened`-style once-only flag was
        wrong here.** Escalating writes `due` for everything hidden, so nothing
        is out of mind and the next call returns False -- no guard needed. Worse,
        a guard would BLOCK a legitimate second escalation, since the only way
        something becomes hidden again is a corpus claiming it, which is a new
        decline about a new dormancy and deserves a fresh reach. The flag was
        written first, gated by nothing, and removing it is what the kill-probe
        asked for.
        """
        if not self._out_of_mind() or not self._outstanding():
            return False
        self.recoveries += 1
        self._note(self.g.rel(self.REACHED, self.focus.seat.node))
        # A claim, deposited rather than a flag, so *why is billing back?* has an
        # answer and a corpus can argue with the escalation as it can with
        # anything else. `due` is the same fact that wakes a dormant rule.
        for c in self._out_of_mind():
            self.gate.write(
                self.focus, self.g.rel(self.DUE, c), PLUS,
                licence=self.g.rel(self.QUIET, self.focus.seat.node),
                source=self.KB, mention=True,
            )
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

    # -- tools ------------------------------------------------------------

    def answerer(self, name: str, request: str, fn) -> "Answerer":
        """Register something that answers a request. §21's debt, as data.

        A tool is not a new kind of thing. It is the shape `_fit` and `_verdict`
        already have -- **a request answered by a function rather than a search**
        -- which is how stratum 0 escapes §5's wall, and it is the only shape
        something outside the agent can honestly take: a search the agent cannot
        inspect is not reasoning it can be held to.

        What changes here is where the BINDING lives. `_fit` answers `fit` because
        a Python line says so, and the consequences are the ones this design keeps
        finding: a corpus cannot ask which tools exist, cannot retire one on
        evidence, and cannot reason about one. So the binding is a fact:

            answers(<M>, ask)

        deposited like any other, queryable by R4, and **deniable**. Retiring a
        tool is `fact -answers(<oracle>, guess)` and the machinery stops calling
        it -- the same move §9 gave norms, which were also unconditionally
        consulted and still entirely contestable.

        `fn(machine, frame, entry)` returns the answer node, or `None` for *I have
        nothing to say* -- which is a real answer and not a failure, because a
        tool that must answer everything is a tool nothing can decline.

        ⚠ The name goes in the `<...>` namespace, which is the namespace of
        STATEMENTS, because a tool is something other statements are about.
        One table with rules and named facts, so a tool cannot share a name with
        a rule -- two things with one name is the mistake the marker prevents.
        """
        # ⚠ `request` may be a NodeId, and for a corpus relation it must be.
        # Registering a tool in Python and naming its request as a STRING mints a
        # relation beside whatever table the corpus resolves against, so the tool
        # answers a request nobody can write -- measured, and it is the twin trap
        # for the third time this session. `Loader.answerer` is the scoped door;
        # a bare string is right only for a relation `reserved` already carries.
        rel = request if isinstance(request, int) else (
            self.reserved.get(request) or self.g.atom(request))
        node = self.g.atom(name)
        a = Answerer(name, node, rel, fn)
        self.answerers.append(a)
        self.gate.write(
            self.focus, self.g.rel(self.ANSWERS, node, a.request), PLUS,
            licence=self.g.rel(self.REIFIED, node), source=self.KB, mention=True,
        )
        return a

    def _answer(self, frame: Frame, e: Entry) -> None:
        """Call whatever answers this request, and record what it said.

        Three things it deliberately is not.

        **Not a conclusion.** What lands is `answered(<M>, req, y)` -- a record
        that M said so, the same treatment §17 gives every arrival. Turning it
        into a belief is an authored rule carrying an authored grade, so a
        confident tool cannot launder a weak answer into a strong claim, and
        §12's weakest link keeps working with nothing added.

        **Not unconditional.** The binding is read from the graph on every write,
        so denying `answers(<M>, ask)` silences the tool immediately and on the
        record. A tool wired in Python could only be silenced by editing Python.

        **Not invisible.** The deposit is licensed by `applied(<M>)` -- the same
        licence a rule's conclusion carries -- so `review` and `blame` walk
        through a tool without knowing it is one. That is the whole of what
        *jointly trained* can honestly mean here: one credit walk, reaching
        rules and tools alike, producing labels for both.
        """
        if e.sign != PLUS or not self.answerers:
            return
        rel = self.g.relation_of(e.proposition)
        if rel is None:
            return
        for a in self.answerers:
            if a.request is not rel:
                continue
            if not self._claims(self.g.rel(self.ANSWERS, a.node, a.request)):
                # ⚠⚠⚠ §19's carve-out, a fifth time, and the argument transfers
                # verbatim: recall may be incomplete about what to DO, never
                # about how to READ. Retiring a tool is an ordinary revision --
                # it was somebody's claim that the tool was worth consulting.
                # Retiring `<fit>` is not an opinion about a tool; it is the
                # agent losing backward reading, silently, on one corpus line.
                #
                # So a `standing` binding is **overridable but not
                # forgettable** -- the same distinction the bundle makes, and
                # the same fact. The denial is not ignored: it is REFUSED, on
                # the record, so *I tried to turn this off and was not allowed*
                # is answerable. A fourth silent decline is what §5 spent the
                # design's whole vocabulary avoiding.
                if not self._claims(self.g.rel(self.STANDING, a.node)):
                    continue
                refusal = self.g.rel(
                    self.REFUSED,
                    self.g.rel(self.ANSWERS, a.node, a.request),
                    self.chain.SIGN[MINUS],
                    self.g.rel(self.STANDING, a.node),
                )
                if self.chain.resolve(refusal, frame.topic, frame.seat) is None:
                    self.gate.write(
                        frame, refusal, PLUS,
                        licence=self.g.rel(self.STANDING, a.node),
                        source=self.KB, mention=True,
                    )
            said = a.fn(self, frame, e)
            if said is None:
                continue
            self.gate.write(
                frame, self.g.rel(self.ANSWERED, a.node, e.proposition, said), PLUS,
                licence=self.g.rel(self.APPLIED, a.node), source=self.KB,
                mention=True,
            )

    def _again(self, frame: Frame, e: Entry) -> None:
        """Re-deliver a request, because a corpus said an occasion warrants it.

        §6: *a request can only be made once.* `<ask-check>` asks whether a
        subgoal is already satisfied at the moment the subgoal appears; if
        forward reasoning satisfies it three ticks later, nothing asks again,
        because re-concluding `+check(p, w)` restates what the chain says and
        quiescence drops it. Requests are facts, and a fact is not an event.

        ⭐⭐⭐ **The request never needed to be fresh. The ENTRY did.** The chain
        has always taken a second entry for a proposition it has seen -- that is
        §10's two indices, and *the same claim, later* is what they exist for.
        What forbids the re-ask is `_would_change`, and it forbids it of a RULE.
        The machinery re-delivering is not a rule restating, so the prohibition
        was never about this act at all.

        So the whole of it is a wrapper and one write:

            again(<request>, <occasion>)

        an ordinary node, differing per occasion, so concluding it is a step;
        and what this does with it is write the wrapped request through the
        gate, where every answerer already listens. `_settle`, `_fit`,
        `_verdict`, `_root` and `_answer` are `on_write` hooks, so a re-asked
        request reaches all five, and a **tool** becomes re-askable by the same
        line -- which is the property `answers(<M>, ask)` was for. Not one
        answerer knows this exists.

        ⭐⭐ **Its own binding is a fact**, which no other piece of the apparatus
        can say: this is registered through `answerer`, so `answers(<re-ask>,
        again)` is on the record and `fact -answers(<re-ask>, again)` turns
        re-asking off. §21's *the apparatus does not eat its own cooking* is now
        true of eight hooks rather than nine.

        ⚠⚠⚠ **What an occasion may be is the whole question, and it is not free
        choice.** An occasion the asking can itself create warrants the next
        re-ask, which creates the occasion after that: `ugm.reask` measures both
        sides of it. The criterion the measurement gives:

        > **An occasion warrants a re-ask only if re-asking cannot produce one.**

        The wrapper is deliberately generic -- it re-delivers whatever it wraps.
        Wrapping something that is not a request re-asserts it, which is honest
        rather than an error: the entry is new, and §10 says what a second entry
        about the same proposition means.
        """
        if e.sign != PLUS or self.g.relation_of(e.proposition) is not self.AGAIN:
            return
        members = self.g.members(e.proposition)
        if len(members) != 2:
            return
        request, occasion = members
        self.gate.write(
            frame, request, PLUS,
            licence=self.g.rel(self.AGAIN, request, occasion),
            source=self.KB,
            consumed=(e,),
            # Inherited, not asserted: the re-ask is the same act as the ask, so
            # whether it uses or mentions is settled by what is being re-asked
            # and not by the fact of repeating it. `has_var` catches the case
            # `_would_change` catches -- a request holding a pattern, which is a
            # ground claim that happens to contain variables (§14).
            mention=e.mention or self.g.has_var(request),
        )

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
        if self.replaying:
            # ⚠⚠⚠ **Replaying a session must not re-do it.** The boundary is the
            # one place effects leave, and it does not know a repeat from a
            # first time -- resume a session that opened a door and it opens the
            # door again. This is `_hypothetical`'s argument in a second place:
            # supposing must not bring it about, and neither must remembering.
            #
            # What it writes instead is `taken`, which the bundle already turns
            # into `did`. So the agent believes it acted -- it did, in the
            # session being resumed -- and nothing leaves. No new vocabulary:
            # `taken` has always meant *decided on and not emitted*.
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
        # Which hypothesis produced which conclusion. It was already recorded --
        # as the crossed entry's LICENCE, `concluded(<frame>)` -- and a licence
        # is a Python field on the entry, so no rule could ask. §21's defect for
        # the eighth time, and it closes the way the other seven did: deposit the
        # record. `applied(<R>)` became `exercised`, the entry's grade became a
        # wrapper, a tool's binding became `answers`, the effort counters became
        # `widened`/`reached`/`bounded`.
        #
        # What it buys is the one thing `hypothesis.py`'s `rivals(about)` had and
        # this floor did not: two suppositions about the same thing both cross
        # their conclusions to the same parent as `likely(q)`, and until now
        # nothing said which came from where -- so a corpus could open rivals and
        # not compare them. `+left(?f, ?a), +concluded(?f, ?c)` is now a join.
        #
        # Deduped per discharge, and it is a claim about the frame rather than a
        # count: a proposition concluded twice inside crossed once, and says so
        # once. Bookkeeping, so a nested frame does not carry
        # `likely(concluded(...))` out -- the same treatment `left` gets.
        recorded: set = set()
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
                crossed = self.g.rel(wrap, inner)
                out.append(
                    self.gate.write(
                        parent,
                        crossed,
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
                # PLUS whatever the conclusion's own sign was: this is not the
                # claim, it is the record that this frame reached it. A frame
                # that concluded `?q` still concluded something.
                if crossed not in recorded:
                    recorded.add(crossed)
                    self.gate.write(
                        parent, self.g.rel(self.CONCLUDED, frame.node, crossed), PLUS,
                        licence=self.g.rel(self.CONCLUDED, frame.node),
                        source=self.KB, mention=True,
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
            self.g, self._state()
        )
        applications = self._applications(proposed, state)
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
            # ...and the same move for FACTS. A shortlist that ran dry is not a
            # search that finished, and neither is a search that never looked at
            # what it had put out of mind.
            if self._recover():
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
        budget = self._knob(self.BUDGET, self.recall_budget)
        if budget is None:
            return live
        keys = self._in_play()
        # By preference alone, not by `_rank`: `standing` is a claim about
        # PRECEDENCE once a rule has matched, not about being brought to mind,
        # and letting it order this step filled every shortlist with apparatus.
        ranked = sorted(
            enumerate(live),
            key=lambda pair: (-self._priority(pair[1], keys), pair[0]),
        )
        out = [r for _, r in ranked[:budget]]
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
        for s in self._state():
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
        # ⭐⭐⭐ THAT THIS RULE HAS RUN, as a PROPOSITION and not only as a licence.
        #
        # `applied(<R>)` is already on every derived entry, because R5 needs it
        # for §12's weakest link -- but a licence is an entry FIELD, so no rule
        # can read one. That is the same shape as an entry's grade (§21 item 5)
        # and as a tool's binding before `answers`: something the machinery knows
        # and no rule can ask about. Both were closed by putting the thing in the
        # graph, and this is the third.
        #
        # What it buys is that **deadness becomes a blocked goal**. A corpus that
        # wants to be sure a rule is load-bearing asserts `+goal(exercised(<R>))`;
        # if nothing ever runs it, backward reading finds nothing that could
        # conclude that, `<give-up>` writes `blocked` at `quiet`, and §19's veto
        # refuses to end quietly on it. No census, no watchdog registry, no
        # pairing of each rule with a guard -- **dying is already intercepted, so
        # the whole of the addition is being able to die on this.**
        #
        # Once per rule, deduped like `reify`: it is a claim about the rule, not
        # a count of its applications, and re-concluding it every tick would be
        # noise quiescence has to chew through.
        if app.rule.node not in self._exercised:
            self._exercised.add(app.rule.node)
            self.gate.write(
                self.focus, self.g.rel(self.EXERCISED, app.rule.node), PLUS,
                licence=licence, source=self.KB, mention=True,
            )
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

    def _out_of_mind(self) -> frozenset:
        """Which domains are not in mind. `dormant` until something claims
        `due` -- the same pair that governs a rule, and for the same reason.

        ⚠⚠⚠ Read by BOTH the kept state and the delta that feeds incremental
        matching, which is why it is a method rather than a local. Filtering
        only the state left the delta unfiltered, so a fact in a dormant domain
        was invisible to the state and still matched once on the tick it
        arrived -- found by the one check that loaded a fact mid-run, and by
        nothing else.
        """
        return frozenset(
            c for c in self.channels.known()
            if self._claims(self.g.rel(self.DORMANT, c))
            and not self._claims(self.g.rel(self.DUE, c))
        )

    def _state(self) -> List[Entry]:
        """The resolved state here, kept across ticks instead of rebuilt.

        `current_state` is §4's walk and the design calls it the single most
        consequential cost: it collects every proposition the chain has ever
        claimed on this branch and `resolve`s each one. That is O(everything
        known) and it ran **twice a tick**, so it was the binding constraint the
        moment `delta` took matching out of the way.

        The same observation fixes it: a moment is a delta, so the state after
        depositing an entry is the state before, plus that one claim. What is
        kept is `proposition -> (key, entry)` where the key is `resolve`'s own
        ordering -- (locus depth, deposit depth, position) -- so a later claim
        replaces an earlier one exactly when `resolve` would have preferred it,
        and an entry about an EARLIER locus correctly loses to one about a later
        one. Nothing here re-derives the ordering; it reuses it.

        ⚠⚠⚠ **Order is part of the answer here too, and more sharply than in
        matching.** `current_state` returns propositions **most-recently-claimed
        first**, and §18's *a description with two candidates resolves to the
        most recent* is a semantic claim that rests on it -- not a detail of the
        walk. So an updated proposition is re-inserted at the end of the dict
        and the result is read back reversed, which reproduces the walk's order
        exactly. Getting this wrong in `delta` cost four checks; it is the same
        trap, one layer down.

        ⚠ A different topic or seat is a different state, so it is a cache miss
        and a full rebuild -- which is the safe direction, and what supposing,
        leaving and re-seating each want.
        """
        # ⭐⭐⭐ **What is in mind, for FACTS.** The agent has always narrowed
        # which rules come to mind -- `dormant` until something claims `due` --
        # and never which facts do. Same relation, second kind of thing: rows,
        # not branches. `fact dormant(billing)` takes a domain out of mind, and
        # because a domain is a channel and every loaded fact carries its
        # channel as its source, there is nothing to look up but what provenance
        # already recorded.
        #
        # Measured before building it: three domains loaded and a goal in one,
        # 23.5s over 600 ticks; with only its own domain in mind, 1.6s over 198,
        # and **the identical 196 conclusions**. It is the strongest lever
        # measured all session, because it cuts both factors -- fewer facts make
        # each tick cheaper AND leave fewer conclusions to draw.
        #
        # ⚠ Unloading is safe to be wrong about: worst case the domain comes
        # back. That is exactly why it may be an ordinary defeasible rule, where
        # §19 insists the ESCALATION -- reaching for more when a search comes up
        # dry -- may not be, since a goal whose evidence is merely out of mind
        # would otherwise read as `blocked`.
        hidden = self._out_of_mind()
        topic, seat = self.focus.topic, self.focus.seat
        key = (topic.node, seat.node, hidden)
        cache = self._state_cache.get(key)
        if cache is None:
            props: dict = {}
            # Oldest first, so the dict's insertion order is claim order and
            # reading it back reversed gives the walk's newest-first order.
            for e in reversed(current_state(self.chain, topic, seat)):
                if e.source in hidden:
                    continue
                props[e.proposition] = (
                    (e.locus.depth, seat.depth, 0), e
                )
            cache = {"pos": len(seat.delta), "props": props}
            self._state_cache = {key: cache}
            return [e for _, e in reversed(list(cache["props"].values()))]

        props = cache["props"]
        for i in range(cache["pos"], len(seat.delta)):
            e = seat.delta[i]
            if not topic.at_or_after(e.locus):
                continue  # a claim about a moment later than what we are about
            if e.source in hidden:
                continue  # a domain that is not in mind
            k = (e.locus.depth, seat.depth, i)
            prev = props.get(e.proposition)
            if prev is not None:
                if k <= prev[0]:
                    continue
                del props[e.proposition]  # re-inserted below, so it moves to
            props[e.proposition] = (k, e)  # the newest end of the order
        cache["pos"] = len(seat.delta)
        return [e for _, e in reversed(list(props.values()))]

    def _applications(self, proposed: List[Rule], state: Situation) -> List[Application]:
        """What could apply here -- carried across ticks instead of rediscovered.

        ⭐⭐⭐ **The loop was stateless between ticks.** Every tick it re-ran every
        rule's join over the whole state, filtered the result, applied one, and
        threw the rest away; next tick it did all of it again. Measured before
        building this: 5,775 applications matched over a 600-fact corpus, of
        which **75 were new** -- 98.7% waste -- and **92.9% on the kettle
        fixture**, so this was never a big-corpus concern. It has been true since
        the first tick ever ran.

        What makes it fixable without a new representation is that §4 already
        made a moment **a signed delta**, and `Chain.deposit` already records each
        entry's position in it. *What is new since I last looked* is
        `seat.delta[pos:]` -- available all along, and not read.

        So: keep the applications, and each tick match only the delta (`match`'s
        `fresh` argument, one pass per antecedent member). Three things have to
        be right, and each is a way this could be wrong rather than merely slow.

        **A newly proposed rule has no history**, so it gets a full match. Recall
        is not fixed -- `dormant`/`due` and `_widen` change what comes to mind --
        and a rule proposed for the first time on tick 40 was never matched on
        tick 39.

        **The cache belongs to a seat**, because a `Situation` does. Supposing
        forks, `_leave` returns, `_deliver` reseats; each is a different state and
        a cache miss, which is the safe direction.

        ⚠⚠⚠ **And an application can stop being applicable, which is the part
        that is not merely bookkeeping.** The chain is append-only but `resolve`
        is not monotone: a denial deposited later makes what an application
        consumed no longer the current claim. So each cached application is
        indexed by the propositions it consumed, and a fresh entry about one of
        those re-checks exactly those applications -- an application survives iff
        every entry it consumed is still what `resolve` returns. That is why this
        cannot be a *seen it* set: quiescence has to keep being able to change
        its mind.
        """
        hidden = self._out_of_mind()
        # ⚠⚠⚠ **What is in mind is part of the cache key**, and leaving it out is
        # a silent bug rather than a slow one: while a domain is dormant its
        # entries are filtered out of the delta and the cursors move past them
        # anyway. Wake the domain and those facts are behind every rule's cursor
        # forever -- so the escalation brings a domain back and the agent still
        # cannot see it. Measured exactly that way before this line existed.
        fk = (self.focus.topic.node, self.focus.seat.node, hidden)
        cache = self._match_cache.get(fk)
        if cache is None:
            cache = {"pos": 0, "apps": {}, "rule_pos": {}, "by_prop": {}}
            self._match_cache = {fk: cache}  # one seat at a time; forking is a miss

        here = len(self.focus.seat.delta)
        delta = self.focus.seat.delta[cache["pos"]:]
        cache["pos"] = here

        # 1. Retire what a later claim unsettled.
        if delta:
            suspect: set = set()
            for e in delta:
                suspect |= cache["by_prop"].get(e.proposition, set())
            for k in suspect:
                app = cache["apps"].get(k)
                if app is None:
                    continue
                alive = all(
                    self.chain.resolve(c.proposition, self.focus.topic, self.focus.seat)
                    is c
                    for c in app.consumed
                )
                if not alive:
                    del cache["apps"][k]
                    for c in app.consumed:
                        cache["by_prop"].get(c.proposition, set()).discard(k)

        # 2. Full match for rules newly come to mind; delta match for the rest.
        #
        # ⚠⚠⚠ **The position is PER RULE, and a global one is wrong.** Recall is
        # not fixed: a rule drops out of mind under a budget and comes back when
        # `_widen` fires. With one shared cursor, everything deposited while it
        # was away has already been consumed, so it comes back and is told
        # nothing is new -- and the chain a->b->c stops at b. That is one
        # selftest check, and it is the difference between a cache and a leak of
        # attention: *new* means new **to this rule**, not new to the loop.
        # Rules mostly share a cursor, so the delta they are shown is mostly the
        # same one: built per distinct start rather than per rule.
        deltas: dict = {}
        for r in proposed:
            start = cache["rule_pos"].get(r.node)
            cache["rule_pos"][r.node] = here
            if start is None:
                found = match(
                    self.g, self.chain, r, self.focus.topic, self.focus.seat, state
                )
            elif start < here:
                if start not in deltas:
                    deltas[start] = Situation(self.g, [
                        e for e in self.focus.seat.delta[start:here]
                        if e.source not in hidden
                    ])
                found = match(
                    self.g, self.chain, r, self.focus.topic, self.focus.seat, state,
                    fresh=deltas[start],
                )
            else:
                continue
            self.matched += len(found)
            for a in found:
                k = (r.node, frozenset(a.bindings.items()))
                if k in cache["apps"]:
                    continue
                cache["apps"][k] = a
                for c in a.consumed:
                    cache["by_prop"].setdefault(c.proposition, set()).add(k)

        # ⚠⚠⚠ **Order is part of the answer, not a detail of how it was found.**
        # §18's last tiebreak is authored order and §14 keeps arbitration total,
        # so *which application is chosen* can turn on where it sat in the list.
        # A full match yields them in state order, nested-loop over each
        # antecedent member; a cache yields them in the order they were
        # discovered, which is tick order. Those differ the moment anything is
        # deposited, and five checks failed on exactly that -- a description
        # resolving to the wrong candidate, a plan binding to the wrong sibling.
        #
        # So the order is reconstructed rather than inherited: rules in the order
        # recall proposed them, and within a rule, lexicographically by where
        # each consumed entry sits in the current state -- which is precisely
        # what the nested loop would have produced.
        order = {e.node: i for i, e in enumerate(state.entries)}
        last = len(order)
        rank = {r.node: i for i, r in enumerate(proposed)}
        live = set(rank)
        out = [a for k, a in cache["apps"].items() if k[0] in live]
        out.sort(key=lambda a: (rank[a.rule.node],
                                tuple(order.get(c.node, last) for c in a.consumed)))
        self.considered += len(out)
        return out

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
        rule_at = self._statements()
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
        rule_at = self._statements()
        out: List[Tuple[Rule, NodeId]] = []
        # ⭐⭐⭐ HOW BADLY, and it needs no negative numeral. §21 carried *a small
        # cost cannot be weighed against a large benefit* as blocked on the
        # table's non-negative numerals -- and the blocker dissolves once the
        # quantity is named correctly. Harm is **how many wanted things were
        # lost**, which is a count, and a count is non-negative by construction.
        # Nothing has to say `-3`; the comparison that matters is *this route
        # cost two and that one cost one*.
        tally: dict = {}
        licence_for: dict = {}
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
                if rule is None:
                    continue
                pair = (rule.node, key)
                if pair not in tally:
                    tally[pair] = set()
                    licence_for[pair] = wanted
                    out.append((rule, key))
                tally[pair].add(wanted)
        # Deposited after the walk, not during it: the magnitude is an aggregate
        # over everything lost, so writing it inside the loop would report the
        # first count as the answer -- §16's ordering trap, in a smaller place.
        self._harm = {}
        for (node, key), lost in tally.items():
            self._harm[node] = self._harm.get(node, 0) + len(lost)
            self.gate.write(
                self.focus,
                self.g.rel(self.HARMED, node, key, self.NUMERAL[min(len(lost), 9)]),
                PLUS, licence=self.g.rel(self.GOAL, licence_for[(node, key)]),
                source=self.KB, mention=True,
            )
        return out

    def harm_of(self, rule) -> int:
        """How many wanted things this statement cost, over the episode just run.

        Zero for anything `blame` did not reach, which is the honest reading:
        *nothing observed*, not *nothing done*. An agent that has never taken a
        route knows nothing about its cost, and that ignorance is what makes
        exploration necessary rather than optional."""
        if not hasattr(self, "_harm"):
            self.blame()
        return self._harm.get(getattr(rule, "node", rule), 0)

    def _statements(self) -> dict:
        """Everything an `applied(...)` licence can name, by node.

        Rules **and tools**, in one table, because the credit walk follows a
        licence and a licence says *this produced that*. Which kind of statement
        it was is a question for the reader, not for the walk -- and keeping them
        apart here would mean a tool could give a bad answer, cost the agent a
        goal, and be the one thing `blame` could not see.

        ⚠ Rules first, so a tool cannot shadow a rule if a name is ever reused.
        The loader already refuses that at authoring; this is the second door.
        """
        out = {r.node: r for r in self.rules.rules}
        for a in self.answerers:
            out.setdefault(a.node, a)
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

    def learned(self, score: int = 3, conditional: bool = False) -> List[str]:
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

        tools = {a.node for a in self.answerers}

        def row(rule, key: NodeId) -> None:
            if rule.name is None or rule.node in harmed or (rule.node, key) in seen:
                return
            # ⚠ Tools are credited and blamed -- `_statements` puts them on the
            # walk deliberately -- but not RECOMMENDED, because a `prefer` row is
            # read by recall and recall proposes rules. A row naming a tool would
            # be inert: it would cost nothing, break nothing, and look exactly
            # like a row that works, which is the failure mode `ugm.bundle`
            # exists to catch. *Which tool to consult when* is a real question
            # and a different mechanism; §21.
            if rule.node in tools:
                return
            seen.add((rule.node, key))
            rows.append(f"fact prefer(<{rule.name}>, {self.g.show(key)}, {score})")

        for rule, key in self.review():
            row(rule, key)
        # ⭐ The conditional form: a learned rule instead of a learned fact, which
        # is the whole of what "generalisation" turns out to mean here.
        #
        # A `prefer` FACT is a decision tree of depth ZERO -- it says *always*,
        # given its key. A `prefer`-concluding RULE says *when*. That is not an
        # analogy: a tree's root-to-leaf path IS a rule, its internal nodes are
        # antecedent members, and `<relevant>` has shipped in exactly this shape
        # since §13. What is more, `_priority` SUMS applicable rows, so a set of
        # such rules is already an **additive ensemble** -- nobody designed that
        # as one; it falls out of *applicable rows sum*.
        #
        # ⚠ `standing` is not decoration and the fixture found it: unmarked, a
        # preference rule mentions `goal(?w)`, so forgoing reads it as a rival way
        # of getting the same want and passes it up before it can advise
        # (measured: `forgone(<t1>)` deposited, priority 0). Marked, it advises
        # (priority 7). §16's *being careful has to come before the move it is
        # about*, arriving from a third side.
        if conditional:
            tests = self._circumstances(self._choosers(harmed))
            if tests:
                return self._advice_rows(tests, harmed, score, rows)
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

    def _circumstances(self, choosers: List[Rule]) -> List[NodeId]:
        """*What about this situation made that the wrong move?*

        The tests of a learned decision tree, and they are read off the trail
        rather than engineered: the ground propositions on the support of what
        was **lost**, less four kinds that cannot discriminate.

        | the lost goals themselves | the conclusion, not a circumstance |
        | machinery bookkeeping     | `goal`, `did`, `doing`, `emitted` are true of every episode |
        | what the CHOOSING rule's antecedent already requires | constant wherever the choice arises at all |
        | anything generic          | §12: a pattern is not an observation |

        What survives is what was true **here** and need not be true next time --
        which is exactly the question a tree's internal node asks. Note it needs
        no new bookkeeping either: R5 keeps the support for the weakest link, and
        this reads it. That is the fifth time.

        ⚠ **All of them, as a conjunction**, and the choice is made on which error
        is recoverable -- the same judgement forgoing made. An over-specific
        condition simply does not fire, and the agent falls back to what it did
        before; an over-general one advises confidently in situations it has
        never seen. Under-advising is recoverable.
        """
        skip = set(self._bookkeeping) | {self.DOING, self.GOAL, self.DID, self.EMITTED}
        # ⚠ The CHOOSING rule's antecedent only, not every blamed rule's. The
        # blame walk reaches the physics too (`<cost>`, `<extra>`), and the
        # physics rules are precisely the ones whose antecedents name the
        # damaging circumstance -- so excluding theirs deletes the signal. Found
        # by measurement: the first version learned nothing and looked like it
        # had merely declined to.
        required = set()
        lost = set()
        for rule in choosers:
            for m in rule.antecedent:
                r = self.g.relation_of(m.pattern)
                if r is not None:
                    required.add(r)
        out: List[NodeId] = []
        for s in current_state(self.chain, self.focus.topic, self.focus.seat):
            if s.sign != PLUS or self.g.relation_of(s.proposition) is not self.GOAL:
                continue
            w = self.g.member(s.proposition, 0)
            if self.g.has_var(w):
                continue
            e = self.chain.resolve(w, self.focus.topic, self.focus.seat)
            if e is not None and e.sign == MINUS:
                lost.add(w)
        for w in lost:
            for p in self._support(w):
                rel = self.g.relation_of(p)
                if rel is None or rel in skip or rel in required:
                    continue
                if p in lost or self.g.has_var(p) or p in out:
                    continue
                e = self.chain.resolve(p, self.focus.topic, self.focus.seat)
                if e is not None and e.sign == PLUS:
                    out.append(p)
        return out

    def _generalise(self, propositions: List[NodeId]) -> List[str]:
        """Render ground propositions as one generic antecedent.

        Every constant becomes a variable, **shared across the conjunction** so
        that `completes(jug1, heirlooms), precious(jug1)` becomes
        `completes(?v0, ?v1), precious(?v0)` -- the join is what makes it a claim
        about a *kind* of situation rather than a longer way of naming this one.

        ⭐ Generalising is unconstrained here, and that is a property of the
        shape rather than luck: a preference consequent (`prefer(<R>, key, n)`)
        contains **no variables at all**, so the loader's rule that a consequent
        variable must be bound by the antecedent is satisfied by everything. A
        learned rule that concluded about the world would not have that freedom.
        """
        names: dict = {}

        def render(n: NodeId) -> str:
            rel = self.g.relation_of(n)
            if rel is None:
                if n not in names:
                    names[n] = f"?v{len(names)}"
                return names[n]
            return f"{self.g.show(rel)}(" + ", ".join(
                render(m) for m in self.g.members(n)) + ")"

        return ["+" + render(n) for n in propositions]

    def _advice_rows(self, tests: List[NodeId], harmed: set, score: int,
                     rows: List[str]) -> List[str]:
        """One learned rule per promoted alternative, plus its `standing` line."""
        antecedent = ", ".join(self._generalise(tests)) if tests else ""
        out = list(rows)
        tools = {a.node for a in self.answerers}
        for rule, key in self._instead_of(harmed):
            if rule.name is None or rule.node in tools:
                continue
            name = f"learned-{rule.name}-{self.g.show(key)}"
            consequent = f"+prefer(<{rule.name}>, {self.g.show(key)}, {score})"
            if antecedent:
                out.append(f"rule <{name}> = implies( {{ {antecedent} }},"
                           f" {{ {consequent} }} )")
                out.append(f"fact standing(<{name}>)")
            else:
                # No tests left: the tree has been pruned to depth zero, which is
                # an unconditional row again -- and saying so in the same
                # vocabulary is what makes *how deep should this be* a measurable
                # question rather than a choice made once at the top.
                out.append(f"fact prefer(<{rule.name}>, {self.g.show(key)}, {score})")
        return out

    def refine(self, cost, score: int = 3) -> List[str]:
        """Drop the tests that do not pay. §4's *compose what never surprised*,
        from the other end: **decompose what turns out not to matter.**

        `learned(conditional=True)` takes every circumstance it can see, because
        an over-specific rule fails safe -- it does not fire and the agent falls
        back. But failing safe repeatedly is still failing, and nothing in one
        episode can say which of its circumstances was the operative one. Only
        more episodes can, so this is reduced-error pruning over corpus text:
        greedy backward elimination against a `cost` the caller supplies.

        ⭐ **Ties go to the MORE GENERAL rule** (`<=`, not `<`). That is the only
        judgement in here, and it is the standard one: between two hypotheses that
        explain the evidence equally, the one with fewer conditions transfers
        further. The opposite bias would keep every accident of the episode it
        learned from.

        `cost(rows) -> number` is the caller's, and it must be, because what an
        episode cost is a question about a world and this object is not one. It
        is also why this is offline and outside the loop, like everything else
        experience does.

        ⚠ What this is NOT is mutation. It only ever *removes* a test it already
        had; it cannot add one it never saw, merge two rules, or revisit a tree
        that has stopped paying. Those are §21.
        """
        harmed = {rule.node for rule, _ in self.blame()}
        tests = self._circumstances(self._choosers(harmed))
        base = [r for r, k in self.review()]

        def rows_for(keep: List[NodeId]) -> List[str]:
            plain: List[str] = []
            seen = set()
            tools = {a.node for a in self.answerers}
            for rule, key in self.review():
                if (rule.name is None or rule.node in harmed
                        or rule.node in tools or (rule.node, key) in seen):
                    continue
                seen.add((rule.node, key))
                plain.append(f"fact prefer(<{rule.name}>, {self.g.show(key)}, {score})")
            return self._advice_rows(keep, harmed, score, plain)

        # ⚠⚠⚠ STEEPEST descent, not first-improvement, and the difference is not
        # a refinement of a refinement -- it decides whether this works at all.
        # Taking the first drop that ties prunes the tree to NOTHING: measured,
        # `{precious, completes}` dropped `precious` for an equal score, then
        # dropped `completes` for an equal score, and arrived at the
        # unconditional row it was supposed to improve on -- while dropping
        # `completes` FIRST scores strictly better and is the answer. A tie is
        # not evidence that a test is worthless; it is evidence that THIS drop
        # is neutral, and another may not be.
        keep = list(tests)
        best = cost(rows_for(keep))
        while keep:
            trials = [([x for x in keep if x is not t], t) for t in keep]
            scored = [(cost(rows_for(trial)), i, trial)
                      for i, (trial, _) in enumerate(trials)]
            # Insertion order breaks the tie (§3: no derived result out of a set).
            low, _, trial = min(scored, key=lambda s: (s[0], s[1]))
            if low > best:
                break
            keep, best = trial, low
        return rows_for(keep)

    def _choosers(self, harmed: set) -> List[Rule]:
        """Of the rules blamed, the ones that made a CHOICE rather than took part.

        A blame walk reaches everything on the support of what was lost -- the
        rule that decided, the act, and the physics that carried it out. Only the
        first had an alternative, and forgoing is what says so: a rule that
        licensed a `forgone` deposit is one that was picked over something else.
        """
        at = self._statements()
        out: List[Rule] = []
        for node in self.g.instances_of(self.FORGONE):
            if self.g.has_var(self.g.member(node, 1)):
                continue
            e = self.chain.resolve(node, self.focus.topic, self.focus.seat)
            if e is None or e.sign != PLUS or e.licence is None:
                continue
            if self.g.relation_of(e.licence) is not self.APPLIED:
                continue
            n = self.g.member(e.licence, 0)
            r = at.get(n)
            if n in harmed and isinstance(r, Rule) and r not in out:
                out.append(r)
        return out

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
        rule_at = self._statements()
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

    def _rendered(self) -> List[dict]:
        """The session, RENDERED out of the graph -- corpora, in the order they
        were read.

        ⭐⭐⭐ **There is no journal.** The first version kept one: a Python list
        of everything that came in. It was a side-channel duplicating the chain,
        in a design whose whole thesis is that nothing the machinery knows may
        be unaskable by a rule -- and a kept list can drift from the graph,
        where a rendering cannot. Everything it held was already here:

            the corpus text        rules are nodes; connective, antecedent and
                                   consequent all reprint
            which facts were told  `licence = loaded(p)`, `source = <domain>`
            what the world said    `arrived(c, p, sign)` entries
            the scope of each      `scoped(<domain>, <scope>)`, deposited by the
                                   loader as an ordinary claim about itself

        ⚠ What is rendered is a **corpus**, never entries. §13 scores *authors
        write entries natively* as a leak -- supply a deposit and you can date a
        claim to when it was not held -- so a saved session replays through the
        ordinary loading path and earns its stamps again.
        """
        scope_of: dict = {}
        for n in self.g.instances_of(self.SCOPED):
            if self.holds(n) == PLUS:
                who, where = self.g.members(n)
                scope_of.setdefault(who, self.g.show(where))
        bundled = {r.node for r in self.bundle}
        rule_by_node = {r.node: r for r in self.rules.rules}

        # ⚠ `show` prints a sign atom as `+`, and the surface reads a sign in
        # ARGUMENT position as `plus`. So a rendered `says(user, ?p, +)` does
        # not reparse -- rendering has to speak the surface's language, not the
        # graph's printing convention. Found by reading the first save file.
        signs = {v: k for k, v in self.reserved.items()
                 if k in ("plus", "minus", "unsure")}

        def surface(n: NodeId) -> str:
            if n in signs:
                return signs[n]
            if n in self.g._name:
                return self.g._name[n]
            rel = self.g.relation_of(n)
            if rel is None:
                return self.g.show(n)
            return f"{surface(rel)}({', '.join(surface(x) for x in self.g.members(n))})"

        def as_text(r) -> str:
            side = lambda ms: ", ".join(
                f"{m.sign}{surface(m.pattern)}" for m in ms
            )
            return (f"rule <{r.name}> = {r.connective}( {{ {side(r.antecedent)} }}, "
                    f"{{ {side(r.consequent)} }} )")

        # Walked in deposit order, so interleaving is preserved and a new block
        # opens whenever the document changes.
        out: List[dict] = []
        seen_rule: set = set()

        def emit(source, line):
            where = self.g.show(source) if source is not None else None
            scope = scope_of.get(source)
            domain = None if where in (None, "kb") else where
            if out and out[-1]["scope"] == scope and out[-1]["domain"] == domain:
                out[-1]["src"] += line + chr(10)
            else:
                out.append({"kind": "load", "scope": scope, "domain": domain,
                            "src": line + chr(10)})

        for mo in self.chain.moments:
            for e in mo.delta:
                rel = self.g.relation_of(e.proposition)
                if rel is self.RULE and e.mention:
                    node = self.g.member(e.proposition, 0)
                    r = rule_by_node.get(node)
                    if r is None or node in bundled or node in seen_rule:
                        continue
                    seen_rule.add(node)
                    emit(e.source, as_text(r))
                    continue
                if rel is self.ARRIVED:
                    c, prop, sign = self.g.members(e.proposition)
                    out.append({"kind": "say", "channel": self.g.show(c),
                                "scope": scope_of.get(c),
                                "proposition": surface(prop),
                                "sign": self.g.show(sign), "grade": e.grade})
                    continue
                lic = e.licence
                if lic is None or self.g.relation_of(lic) is not self.LOADED:
                    continue
                if rel is self.SCOPED:
                    continue  # the loader's claim about itself; re-made on load
                emit(e.source, f"fact {e.sign}{surface(e.proposition)}")
        return out

    def save(self, path: str) -> None:
        """Write the session as what it was told -- rendered from the graph.

        §3's determinism is what makes this enough: measured, the same corpus
        reproduces the same 619 entries byte for byte across four hash seeds, so
        *what it was told* is a complete description of *what it knows*. And it
        is a file a person can read, diff and argue with, which a pickle is not.

        ⚠ What it cannot carry: a tool's answers. An answerer is a Python
        function, so a resumed session must re-register its tools, and a SAMPLED
        answer would not reproduce at all -- §21 already records that a real
        model needs its seed on the record before it is reproducible reasoning.
        """
        import json

        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"ugm": 1, "session": self._rendered()}, fh, indent=1)

    def replay(self, session: List[dict], limit: int = 400) -> None:
        """Re-live a session without re-doing it.

        The boundary is muted for the whole of it (`replaying`), so acts land as
        `taken` and become `did` through the bundle -- the agent remembers
        acting, and nothing leaves. Resume a session that opened a door and the
        door is not opened twice.
        """
        from .text import load

        self.replaying = True
        try:
            for item in session:
                if item["kind"] == "load":
                    load(self, item["src"], item.get("scope"), item.get("domain"))
                elif item["kind"] == "say":
                    scope = item.get("scope")
                    ldr = load(self, "", scope, None)
                    self.channels.deliver(
                        ldr.channel(item["channel"]),
                        ldr.term(item["proposition"]),
                        item["sign"], item.get("grade", "certain"),
                    )
                # ⭐ Think after each block, to quiescence. `run` is not state
                # and is not rendered -- *think until there is nothing left* is
                # what the agent does, not something it was told -- and running
                # twice over is idempotent, because `quiet` is once per seat.
                self.run(limit=limit)

        finally:
            self.replaying = False

    def report(self) -> List[str]:
        """What happened, for a person -- §2's not-lossy criterion at the one
        boundary nobody had crossed.

        Everything here was already in the graph. A corpus with a typo ends
        `quiescent` with `blocked(water(kettle))` deposited -- the agent has
        diagnosed itself exactly -- and there was no way to be told. `why()`
        answers about a proposition you already suspect; this answers *what
        became of what I asked for*, which is the question someone actually has.

        Depth first, left to right, because backward reading already built the
        tree: a goal, the plans that fit it, and each plan's subgoals in the
        order they were needed. Printed that way it reads as an argument rather
        than as a dump, and the indentation is the search's own shape.
        """
        out: List[str] = []
        holds = lambda p: self.holds(p)
        # ⚠ `has_var` is NOT a filter here. A subgoal backward reading has not
        # bound yet -- `heat(?a, kettle)` -- is exactly what a reader needs to
        # see, and filtering it emptied the tree and left the subgoals looking
        # like roots. The guard belongs on `goal`, where a description is not a
        # claim (§15), and nowhere else.
        live = lambda rel: [n for n in self.g.instances_of(rel)
                            if self.holds(n) == PLUS]

        def status(w: NodeId) -> str:
            if holds(w) == PLUS:
                return "held"
            if any(self.g.member(n, 0) == w for n in live(self.BLOCKED)):
                return "BLOCKED"
            return "open"

        # goal -> plans -> subgoals, which is exactly what `<plan>` and
        # `<expand>` deposited; nothing is recomputed here.
        plans: dict = {}
        for n in live(self.EXPANDS):
            plan, wanted, _rule = self.g.members(n)
            plans.setdefault(wanted, []).append(plan)
        # ⚠ Not the apparatus's own goals. Backward reading makes `need(...)`
        # and `fits(...)` goals like any other, and shown here they read as
        # things the user asked for -- several of them permanently `BLOCKED`,
        # which is both true and meaningless. A report is about the world the
        # corpus is about; the machinery's own search is what `why` is for.
        subs: dict = {}
        for n in live(self.SUBGOAL):
            plan, sub = self.g.members(n)
            if self.g.relation_of(sub) in self._bookkeeping:
                continue
            subs.setdefault(plan, []).append(sub)

        def walk(w: NodeId, depth: int, seen: frozenset) -> None:
            if w in seen or depth > 12:
                out.append("  " * depth + f"{self.g.show(w)} ...")
                return
            here = plans.get(w, [])
            head = f"{self.g.show(w)}  [{status(w)}]"
            # ⭐ **Indent where there is a CHOICE; chain where there is not.**
            # One way of getting something is not a branch, and indenting it
            # says there was a decision where there was none -- the same reason
            # `likely(not(p))` reads as one line and not as three. So a single
            # plan joins its goal's line, and several are laid out as the
            # alternatives they are.
            if len(here) == 1:
                out.append("  " * depth + head + f"  via {self.g.show(self.g.member(here[0], 0))}")
                for sub in subs.get(here[0], []):
                    walk(sub, depth + 1, seen | {w})
                return
            out.append("  " * depth + head)
            for plan in here:
                out.append("  " * (depth + 1) + f"via {self.g.show(self.g.member(plan, 0))}")
                for sub in subs.get(plan, []):
                    walk(sub, depth + 2, seen | {w})

        wanted = [self.g.member(n, 0) for n in live(self.GOAL)
                  if not self.g.has_var(n)
                  and self.g.relation_of(self.g.member(n, 0)) not in self._bookkeeping]
        subgoal_of = {s for ss in subs.values() for s in ss}
        roots = [w for w in wanted if w not in subgoal_of] or wanted
        if roots:
            out.append("asked for:")
            for w in roots:
                walk(w, 1, frozenset())
        # ⚠ From the GRAPH, not from `self.emitted`. That list is a Python
        # field holding this process's emissions, so a RESUMED session -- which
        # remembers acting and correctly did not act again -- reported having
        # done nothing. `did(...)` is the claim, and it is what a reader wants:
        # *what did you do*, not *what left the socket during this process*.
        did = live(self.DID)
        if did:
            out.append("did:")
            out.extend(f"  {self.g.show(self.g.member(n, 0))}" for n in did)
        refused = live(self.REFUSED)
        if refused:
            out.append("refused:")
            out.extend(f"  {self.g.show(n)}" for n in refused)
        opened = live(self.OPEN)
        if opened:
            out.append("still open when it tried to stop:")
            out.extend(f"  {self.g.show(self.g.member(n, 0))}" for n in opened)
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


# -- inducing a tree from several episodes ---------------------------------


def leaves(episode) -> List[Tuple[str, str, Tuple[str, ...]]]:
    """What one finished episode proposes: `(alternative, key, tests)` per leaf.

    Rendered as TEXT rather than as nodes, because episodes are separate agents
    with separate graphs and a node from one means nothing in another. That is
    §3's *names are not identity* deciding an interface: what crosses an episode
    boundary is corpus text, exactly as `learned` already had it.
    """
    harmed = {r.node for r, _ in episode.blame()}
    tests = tuple(episode._generalise(episode._circumstances(episode._choosers(harmed))))
    out = []
    for rule, key in episode._instead_of(harmed):
        if rule.name is not None:
            out.append((rule.name, episode.g.show(key), tests))
    return out


def induce(episodes, cost, score: int = 3, hedge: bool = False) -> List[str]:
    """Grow a decision tree with MORE THAN ONE LEAF, from more than one episode.

    `refine` prunes a single path. A tree is several: *in situations like this
    prefer X; in situations like that prefer Y.* Each episode proposes one leaf --
    the alternative it wishes it had taken, conditioned on what was true when it
    went wrong -- and the leaves are then pruned **jointly** against a cost the
    caller measures.

    ⭐⭐⭐ **Wrong leaves are expected, and pruning is what makes that safe.** An
    episode only ever knows the cost of the route it ACTUALLY took, so an episode
    that broke a jug proposes *prefer the tap* whether or not the tap is worse --
    which is the oscillation `lesser_of_two_evils` measures, arriving as an
    ordinary over-general hypothesis. Reduced-error pruning is exactly the
    instrument for that: a leaf that does not pay is dropped, and the oscillation
    stops being a special case needing its own mechanism.

    Two edits, one search (steepest descent, as `refine` had to learn): drop a
    whole leaf, or drop one test from a leaf. Ties go to the smaller tree -- fewer
    leaves and fewer conditions both transfer further.

    ⚠ It still cannot ADD a test no episode saw, nor merge two leaves into one.
    Those are mutation proper, and they are affordable for the same reason the
    rest is: every leaf concludes `prefer`, so a bad candidate costs ticks.
    """
    # ⭐⭐⭐ WHAT EACH ROUTE COST, accumulated across episodes -- the second of the
    # two things `lesser_of_two_evils` showed were needed and neither of which
    # works alone. An episode knows only what the route it took cost; several
    # episodes know several, and the comparison *this one cost two and that one
    # cost one* is then sayable without a negative numeral anywhere.
    observed: dict = {}
    for ep in episodes:
        for rule in ep.rules.rules:
            if rule.name is not None:
                h = ep.harm_of(rule)
                if h:
                    observed[rule.name] = max(observed.get(rule.name, 0), h)
    worst = max(observed.values()) if observed else 0

    def weight(name: str) -> int:
        """A route's score: how much better than the worst thing known.

        Non-negative by construction, so it lives on the table's own cardinal
        scale untouched (§12's ordinals are a different quantity and stay one).
        A route never tried scores the full `score` -- ignorance reads as
        optimism, which is what makes the agent try something it has not tried
        rather than settling on the first thing that merely worked."""
        return score if name not in observed else max(
            0, score + worst - observed[name])

    seen, cand = set(), []
    for ep in episodes:
        for name, key, tests in leaves(ep):
            k = (name, key, tests)
            if k not in seen:
                seen.add(k)
                cand.append([name, key, list(tests)])

    def advice(name: str, key: str) -> str:
        """`prefer(...)`, or `possible(prefer(...))` when nothing was observed.

        ⭐⭐⭐ **How sure is a WRAPPER, not a field.** §21's item 5 is that grades
        are Python fields on the entry, so no rule can read one -- which makes a
        confidence expressed as a grade unreadable by the very rules that would
        act on it. A wrapper is an ordinary node: `_priority` does not count it
        (an unsure preference must not silently steer), and a corpus rule decides
        whether to take it up:

            rule <venture> = implies( { +possible(prefer(?r, ?k, ?n)), +exploring },
                                      { +prefer(?r, ?k, ?n) } )

        So **explore/exploit stops being machinery and becomes a claim** --
        defeasible, deniable, on the trail, and switched by an ordinary fact. The
        default with no such rule is to exploit, which is the conservative one.

        ⚠ And the test is constant-free, which §15 went to some trouble for:
        `observed` versus `never tried` is a distinction the trail makes, not a
        threshold anybody chose. A route the agent has taken is asserted; one it
        has only reasoned about is hedged.
        """
        bare = f"prefer(<{name}>, {key}, {weight(name)})"
        return bare if (name in observed or not hedge) else f"possible({bare})"

    def rows_for(tree) -> List[str]:
        out = []
        for i, (name, key, tests) in enumerate(tree):
            if tests:
                rn = f"learned-{i}-{name}-{key}"
                out.append(f"rule <{rn}> = implies( {{ {', '.join(tests)} }},"
                           f" {{ +{advice(name, key)} }} )")
                out.append(f"fact standing(<{rn}>)")
            else:
                out.append(f"fact +{advice(name, key)}")
        return out

    # Every route observed to harm gets a row too, not only the ones some episode
    # proposed -- otherwise the LESSER of two evils is unsayable, because the
    # route that merely cost less was never anybody's regretted alternative.
    for name in observed:
        for _, key, _ in cand:
            if not any(c[0] == name and c[1] == key for c in cand):
                cand.append([name, key, []])
            break

    tree = cand
    best = cost(rows_for(tree))
    while True:
        # ⚠⚠⚠ ORDER MATTERS ON A PLATEAU, and this is where the search failed.
        # Reaching the good tree needs TWO edits -- drop the unconditional leaf
        # AND drop a test -- each individually neutral. A greedy walk that
        # accepts ties therefore gets wherever the trial order sends it, and the
        # first version dropped the GOOD leaf and collapsed to the very
        # unconditional row it was meant to beat.
        #
        # So ties are broken by doubting the LEAST SPECIFIC leaf first. That is
        # not a tuning knob: a leaf with no tests fires in every situation, which
        # makes it the strongest claim in the tree and the first that should have
        # to earn its place. Leaf-drops before test-drops, fewest tests first.
        trials = []
        for i in sorted(range(len(tree)), key=lambda j: len(tree[j][2])):
            trials.append([l for j, l in enumerate(tree) if j != i])
        for i in range(len(tree)):
            for t in range(len(tree[i][2])):
                alt = [list(l) for l in tree]
                alt[i][2] = [x for k, x in enumerate(tree[i][2]) if k != t]
                trials.append(alt)
        if not trials:
            break
        scored = [(cost(rows_for(tr)), i, tr) for i, tr in enumerate(trials)]
        low, _, tr = min(scored, key=lambda s: (s[0], s[1]))
        if low > best:
            break
        tree, best = tr, low
    return rows_for(tree)


def forest(episodes, cost, trees: int = 3, score: int = 3) -> List[str]:
    """Many trees over different episodes, and their DISAGREEMENT is the hedge.

    `induce` grows one tree from everything the agent has been through, which
    means one unlucky episode is in every leaf it produces. Bagging is the usual
    answer -- grow several trees from overlapping subsets and combine them -- and
    two things make it fit here rather than merely be importable.

    ⚠⚠⚠ **MEASURED, AND IT DOES NOT PAY YET -- one tree beats the bag.** On the
    situation-dependent fixture: one tree 1, forest 2, nothing 4. The reason
    falsifies the claim this function was built on, so it is recorded here rather
    than quietly fixed:

    > **`_priority` SUMS, and summation is not VOTING.** In a classifier forest a
    > minority tree is outvoted. Here every tree's rows are ADDED, so a single
    > over-general row -- one bag that pruned to an unconditional `prefer` --
    > fires in every situation and cannot be outvoted by the two trees that
    > learned the condition. The ensemble has a way for advice to accumulate and
    > no way for it to be overruled.

    ⚠ And the unanimity test is too coarse to catch it: the trees all advise the
    same RULE and disagree about *when*, so nothing is hedged. Agreement has to be
    about the condition, not the conclusion -- which is the same lesson `refine`
    and `induce` each learned in their own way, that the interesting structure is
    in the antecedent.

    What a forest here would need is a combination rule that can DEFEAT rather
    than only add -- §12's `overrides` is the obvious candidate and is untried.
    Left as a measured negative result with a gate, not deleted: the day
    summation stops dominating, the gate fails and sends someone here.

    ⭐⭐⭐ **And the spread is already sayable.** §15 settled that *two candidates
    are close exactly when they tie*, needing no threshold; the same argument
    gives confidence here for free. A route the trees **agree** about is asserted
    (`prefer(...)`); one they **disagree** about is wrapped
    (`possible(prefer(...))`), which `_priority` does not count until a corpus
    rule ventures on it. So the forest does not need a confidence scale -- it
    needs the wrapper it already has, and unanimity is the constant-free test.

    ⚠ The subsets are contiguous slices, not random draws: §3 forbids reading a
    derived result out of an unseeded source, and a bagged forest whose bags are
    unseeded is that bug wearing a hat. Deterministic bags, reproducible trees.
    """
    eps = list(episodes)
    if not eps:
        return []
    n = max(1, min(trees, len(eps)))
    bags = [[eps[j] for j in range(len(eps)) if j % n != i] or eps for i in range(n)]
    grown = [induce(bag, cost, score=score) for bag in bags]

    def advised(rows):
        out = {}
        for r in rows:
            if "prefer(<" not in r:
                continue
            name = r.split("prefer(<", 1)[1].split(">", 1)[0]
            out[name] = out.get(name, 0) + 1
        return out

    votes = [advised(rows) for rows in grown]
    named = [n for v in votes for n in v]
    unanimous = {x for x in named if all(x in v for v in votes)}

    out: List[str] = []
    for i, rows in enumerate(grown):
        for r in rows:
            # ⚠ Rename EVERY row of the tree, not the rule alone. The first
            # version prefixed the rule and left `standing(<learned-...>)`
            # pointing at the old name, and the loader refused the corpus --
            # which is `<...>` doing its job: a name that does not resolve is an
            # error, where a silently-wrong reference would have been a bug.
            r = r.replace("learned-", f"t{i}-learned-")
            if "prefer(<" in r:
                name = r.split("prefer(<", 1)[1].split(">", 1)[0]
                if name not in unanimous:
                    # The one edit: what the trees could not agree on is offered,
                    # not asserted, so the disagreement stays visible in the
                    # corpus instead of being averaged away.
                    head, _, tail = r.partition("+prefer(")
                    r = head + "+possible(prefer(" + tail.rstrip()
                    r = (r[:-2] + "))" + r[-2:]) if r.endswith(") )") else r + ")"
            if r not in out:
                out.append(r)
    return out
