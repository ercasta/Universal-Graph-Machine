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

import inspect
import heapq
import os
from typing import Iterable, List, NamedTuple, Optional, Tuple

from .chain import MINUS, PLUS, UNSURE, Chain, Entry, Locus, Moment, scope_of
from .channels import Arrival, Channels
from .gate import Frame, Gate
from .graph import Graph, NodeId
from .rules import (
    _defeaters,
    already_there,
    GENERIC,
    CAUSES,
    IMPLIES,
    Application,
    Member,
    Rule,
    RuleSet,
    _defeated,
    arbitrate,
    defeat,
    match,
    occurs,
    unify,
    Situation,
    current_state,
    substitute,
    _left_open,
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
    def __init__(self, clock: bool = False) -> None:
        self.g = Graph()
        # Off by default: a stamp per moment makes two runs differ, and
        # §3's determinism is measured byte for byte. See `Chain.__init__`.
        self.chain = Chain(self.g, clock=clock)
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
        # ⭐⭐⭐ **The aggregate over bindings, and it is the GENERAL case of
        # `rooted`, `unsupported` and `blocked` rather than a fourth of them.**
        # A rule's antecedent is existential -- each member matches *an entry*,
        # so a rule says *there is an entry such that*, and a `-` member says
        # *an entry denies this*, never *for no `?x`*. A rule therefore sees one
        # binding at a time, and *there are two matches* exists only inside
        # `match`, which is the floor.
        #
        # `docs/observations.md` §4 reaches this from four directions and they
        # collapse to one question -- *how many ground matches does this pattern
        # have here?* -- with the comparison left to a corpus:
        #
        #     nothing was told about it        0
        #     it held throughout        counterexamples 0
        #     ***the*** goblin                 1
        #     nothing has handled this yet     0
        #
        # One request, four uses, and the meaning is the corpus's own rule
        # rather than four bundled ones. That is *rows, not branches* at the
        # level of the feature itself.
        # ⭐ The marker a consequent writes to introduce a thing: `new(person)`.
        # See `_apply`. Reserved, so a corpus cannot mean something else by it
        # without knowing -- and so the loader resolves it to THIS node.
        self.NEW = self.g.atom("new")
        self.COUNT = self.g.atom("count")      # ask
        self.COUNTED = self.g.atom("counted")  # ...and the answer, always

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
        # The third negative existential, asked and answered like the other two.
        self.SUPPORT = self.g.atom("support")          # the request
        self.UNSUPPORTED = self.g.atom("unsupported")  # the answer, only ever yes
        # *Not that one* -- what a plan has tried and ruled out for a variable.
        #
        # A separate relation rather than a denied `binds`, deliberately. Reading
        # `-binds(<plan>, ?v, sink)` as an exclusion would give `-` a second
        # meaning it has nowhere else: everywhere in this design a denial says
        # *an entry denies this*, and it steers nothing. Here it would also have
        # to steer a search, and a sign that means one thing in general and
        # something extra in one place is the kind of quiet asymmetry §5 is for
        # refusing. One more piece of vocabulary is the cheaper price.
        self.EXCLUDED = self.g.atom("excluded")
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
        self.DEFEATED = self.g.atom("defeated")
        # ⚠ Owned by the machine, not minted beside the loader's. Precedence is
        # read from the graph now, so the node a corpus writes and the node the
        # arbitrator looks for have to be one -- `atom` does not intern, and
        # that twin has cost this repo seven findings.
        self.OVERRIDES = self.g.atom("overrides")
        self.SUPERSEDES = self.g.atom("supersedes")
        # ⭐ The rule set reads precedence off the graph, at wherever the agent
        # is standing. It owns neither the nodes nor the position, so both are
        # handed to it -- one place, so the node a corpus writes and the node
        # the arbitrator looks for cannot come apart.
        self.rules.OVERRIDES = self.OVERRIDES
        self.rules.SUPERSEDES = self.SUPERSEDES
        self.rules.claims = self._claims
        self.ADOPT = self.g.atom("adopt")
        # §4's larger optimisation, as a request. ⭐ `composed` closes the same
        # defect `defeated` and `rests_on` did: `RuleSet.composed_from` is a
        # Python dict, so *which rules is this a shortcut for* was a question
        # about the agent's own rule set that no rule could ask -- and §22 needs
        # exactly that to decompose on surprise.
        # Where a rule's member says its entry must sit (§12's locus).
        self.AT = self.g.atom("at")
        # ...and asking how two of them are ordered (§10, §22).
        # ...and the name a member gives what it matched (§12's `as`).
        # ⚠ NOT `self.BINDS`, which is the PLAN-bindings relation twelve lines
        # of this file already use. Reusing the attribute made every plan print
        # its bindings as `names(...)` and broke `ugm.backward` -- one node with
        # two meanings, committed by the author of the note warning about it.
        self.NAMES = self.g.atom("names")
        self.COMPUTES = self.g.atom("computes")
        # The skeleton, as members an ordinary rule may write (§6, §12).
        from .rules import structural_relations
        self.rules.structural = structural_relations(self.chain)
        # How the chain asks about containment. Set here because this is the
        # only object that has both a chain and a rule set.
        self.chain.consult = self._reaching
        self.COMPOSE = self.g.atom("compose")
        self.COMPOSED = self.g.atom("composed")
        self.WIDENED = self.g.atom("widened")
        # Refraction's vocabulary (§14). `spent` is the record of an
        # instantiation having run; `premises` names the entries it ran on;
        # `contested` is the occasion refraction would otherwise have hidden.
        self.SPENT = self.g.atom("spent")
        self.PREMISES = self.g.atom("premises")
        self.CONTESTED = self.g.atom("contested")
        self.REACHED = self.g.atom("reached")
        self.BOUNDED = self.g.atom("bounded")
        # ...and the third bound, which was the only one not on the record.
        # A corpus asked for this first, ahead of every feature in its list.
        self.TICKS = self.g.atom("ticks")
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
        #
        # ⭐⭐⭐ **And it now moves TWO registers, which is the whole of stage
        # three** (`docs/situations.md`). The graph has a situation register for
        # the same reason the machine has a frame one -- minting requires
        # somewhere to stand -- and the two must never disagree, because a rule
        # matching inside a supposition reads the indices and the indices are
        # keyed by situation. Making this a property is what stops them: there
        # are five assignments to `focus` in the repository, and an engine that
        # kept them in step by remembering to would be one line from a leak.
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
            "count": self.COUNT, "counted": self.COUNTED, "new": self.NEW,
            "answers": self.ANSWERS, "answered": self.ANSWERED,
            "scoped": self.SCOPED, "loaded": self.LOADED,
            "again": self.AGAIN,
            "dormant": self.DORMANT, "due": self.DUE, "prefer": self.PREFER,
            "forbidden": self.FORBIDDEN, "refused": self.REFUSED,
            "standing": self.STANDING,
            "recall": self.RECALL, "recalled": self.RECALLED,
            "close": self.CLOSE, "tolerance": self.TOLERANCE,
            "defeated": self.DEFEATED, "adopt": self.ADOPT,
            "spent": self.SPENT, "premises": self.PREMISES,
            "contested": self.CONTESTED,
            "compose": self.COMPOSE, "composed": self.COMPOSED,
            "at": self.AT, "moved": self.gate.MOVED,
            # The skeleton, as names a corpus may write (§6, §12). `pred` is the
            # stored immediate predecessor; `anc`/`sanc` are the reflexive and
            # strict walks; the rest are what the chain deposits as it builds.
            "pred": self.chain.PRED, "sanc": self.chain.SANC,
            "anc": self.chain.ANC,
            "in_delta": self.chain.IN_DELTA,
            "delta_next": self.chain.DELTA_NEXT,
            "rests_on": self.chain.RESTS_ON,
            "licensed_by": self.chain.LICENSED_BY,
            "arrived_on": self.chain.ARRIVED_ON,
            "mentioned": self.chain.MENTIONED,
            "entry_of": self.chain.ENTRY_OF,
            # ...and a stretch of it. `span_of(?s, ?start, ?end)` mints when the
            # endpoints are bound and decomposes when the span is (§11).
            "span_of": self.chain.SPAN_OF, "span": self.chain.SPAN,
            "asking": self.chain.ASKING, "asked": self.chain.ASKED,
            # ⚠ Without this line `time(?m, ?t)` in a corpus is a FRESH
            # atom -- `g.atom` does not intern -- so the rule is well
            # formed, `is_stratum0` says no, the member matches nothing,
            # and nothing raises. The name-identity trap, caught here on
            # its fifth outing.
            "time": self.chain.TIME,
            "holds_at": self.chain.HOLDS_AT,
            "reaches": self.chain.REACHES,
            "names": self.NAMES, "computes": self.COMPUTES,
            "overrides": self.OVERRIDES, "supersedes": self.SUPERSEDES,
            "widened": self.WIDENED, "reached": self.REACHED,
            "bounded": self.BOUNDED, "ticks": self.TICKS,
            "budget": self.BUDGET, "depth": self.DEPTH,
            "hypotheses": self.HYPOTHESES,
            **{str(i): n for i, n in self.NUMERAL.items()},
            "check": self.CHECK, "unmet": self.UNMET,
            "verdict": self.VERDICT, "pursued": self.PURSUED,
            "support": self.SUPPORT, "unsupported": self.UNSUPPORTED,
            "excluded": self.EXCLUDED,
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
        # The live cache for this seat, set by `_applications` and read by
        # `_would_change`. None until the first tick, so a verdict asked for
        # outside the loop is simply computed.
        self._verdicts: Optional[dict] = None
        # Which rules matched here, carried beside the candidate list because
        # `defeat` reads it and the candidate list no longer contains it.
        self._matched_rules: dict = {}
        # What matching actually produced, against what the loop then weighed.
        # Two numbers rather than one, because the whole claim is the gap: the
        # loop used to make them equal by rediscovering its options every tick.
        self.matched = 0
        self.considered = 0
        # The resolved state, kept rather than rebuilt. See `_state`.
        self._state_cache: dict = {}
        # `new(...)` terms per rule -- see `_markers`.
        self._marker_cache: dict = {}
        # ...and what the seat has mentioned, accumulated over the same delta.
        self._play_cache: dict = {}
        self._stopped: set = set()
        self._noticed: set = set()
        self._vetoed: set = set()
        self._reified: set = set()
        self._exercised: set = set()
        # Structural relations that have grown since the matcher last looked.
        # See `_mint_structure`: structure sits in no delta, so this is the only
        # thing that can tell the incremental path a skeleton fact appeared.
        self._structure_touched: set = set()
        # Answers to *can this locus see that one*, which are stable once
        # given: ancestry is append-only and a span's endpoints never move.
        self._reaches: Dict[Tuple[NodeId, NodeId], bool] = {}
        # Refraction (§14). An instantiation -- a rule and the entries it
        # consumed -- fires once. See `_instantiation`, `_spend`, `_contest`.
        self._spent: dict = {}
        self._spent_by_prop: dict = {}
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
                             self.COUNT, self.COUNTED, self.NEW,
                             self.DUE, self.VERDICT, self.PURSUED, self.PREFER,
                             self.SUPPORT, self.UNSUPPORTED, self.EXCLUDED,
                             self.FORBIDDEN, self.STANDING,
                             self.RECALL, self.RECALLED, self.CLOSE,
                             self.TOLERANCE, self.BUDGET, self.DEPTH,
                             self.HYPOTHESES, self.WIDENED, self.REACHED,
                             self.BOUNDED, self.DEFEATED, self.ADOPT,
                             self.SPENT, self.PREMISES, self.CONTESTED,
                             # A seat move is the machinery's record of its own
                             # advance, not a claim about the supposed world, so
                             # a wrapper has nothing to qualify: without this a
                             # `causes` rule applied under a hypothesis carried
                             # `likely(moved(...))` out of it -- the agent
                             # hedging about where it had been standing. Caught
                             # by `a_cause_moves_the_register`, which is the
                             # fixture that asked for the seat move in the first
                             # place.
                             self.gate.MOVED}

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
        self.gate.on_write.append(self._adopt)
        # Refraction's cost, checked at the write: see `_contest`.
        self.gate.on_write.append(self._contest)
        self.gate.on_write.append(self._dispatch)
        self.gate.on_write.append(self._enter)
        self.gate.on_write.append(self._answer)
        for name, request, fn, standing in (
            ("fit", "fit", self._fit, True),
            ("settle", "check", self._settle, True),
            ("verdict", "verdict", self._verdict, True),
            ("root", "root", self._root, False),
            # NOT `standing`: unlike `<fit>` and `<verdict>`, nothing in the
            # apparatus asks it, so a corpus that retires it loses only what it
            # chose to ask. The status quo ante is its absence, which is §20's
            # own test for a capability that is safe to retire.
            ("supported", "support", self._supported, False),
            # NOT `standing`, by the same test the two above use:
            # nothing in the apparatus counts, so a corpus that
            # retires it loses only what it chose to ask, and the
            # status quo ante is its absence.
            ("counter", "count", self._count, False),
            # NOT `standing`, by the same test: deny it and the agent is exactly
            # what it was before composition had a trigger, which is sound.
            ("composer", "compose", self._compose, False),
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
        # ⚠⚠ **The POSITION.** It was missing and it is part of the rule
        # missing and both are part of the rule: an antecedent is a sequence --
        # §18's tiebreak reads the consumed entries and `consumed` is filled by
        # member position -- and a consequent member states how strongly it
        # would conclude. Without them a rule read back out of the graph is a
        # different rule, silently, and `g.rel` interns, so a rule with two
        # identical members would have lost one of them as well.
        #
        # The antecedent carries no grade, and that is not an omission: `Member`
        # says so -- what a premise was worth is read off the entry that matched
        # it, not asserted by the rule.
        for i, m in enumerate(rule.antecedent):
            w(self.g.rel(self.ANT, rule.node, m.pattern,
                         self.rules.SIGN[m.sign], self._numeral(i)))
            self._reify_locus(w, self.ANT, rule.node, i, m)
            self._reify_binds(w, self.ANT, rule.node, i, m)
        for i, m in enumerate(rule.consequent):
            w(self.g.rel(self.CON, rule.node, m.pattern,
                         self.rules.SIGN[m.sign], self._numeral(i)))
            self._reify_locus(w, self.CON, rule.node, i, m)
            self._reify_binds(w, self.CON, rule.node, i, m)

    def _reify_locus(self, w, side, node, i, m) -> None:
        """...and WHERE the member's entry must sit, when it says (§12).

        ⚠⚠⚠ **Not optional, and the least visible part of the feature.**
        `adopt` reads a rule back out of the graph and `compose` builds one from
        two others; a locus that reify does not record is a locus those two
        silently drop, and the rule that comes back is a DIFFERENT rule. That is
        the twin-trap family, which has bitten four times, and a corpus that
        retracts in 57% of its rules -- which a foreign one measured -- would hit
        it immediately rather than eventually.

        A separate relation rather than a sixth member of `ant`/`con`, because
        most members have no locus and §5 refuses a shape whose arity varies
        with how much happens to be known about it.
        """
        if m.locus is None:
            return
        w(self.g.rel(self.AT, side, node, self._numeral(i), m.locus))

    def _reify_binds(self, w, side, node, i, m) -> None:
        """...and the name the member gives what it matched (§12's `as`).

        Same argument as `_reify_locus`, and it is the fifth time this argument
        has had to be made: a slot the graph does not record is a slot `adopt`
        and `compose` silently drop, and the rule that comes back is a different
        rule. The twin-trap family.
        """
        if m.binds is None:
            return
        w(self.g.rel(self.NAMES, side, node, self._numeral(i), m.binds))

    def _numeral(self, i: int):
        """A node for a small whole number. `NUMERAL` stops at nine because
        nothing needed ten; a rule with eleven members is not an error."""
        if i not in self.NUMERAL:
            self.NUMERAL[i] = self.g.atom(str(i))
        return self.NUMERAL[i]

    def reify_all(self) -> None:
        """Kept because instruments call it; it should now find nothing to do.
        Rules are reified when they are authored (`RuleSet.on_rule`)."""
        for r in self.rules.rules:
            self.reify(r)

    # -- the register -----------------------------------------------------

    @property
    def focus(self) -> Frame:
        return self._focus

    @focus.setter
    def focus(self, frame: Frame) -> None:
        """Move the register -- and the graph's, which is the same move.

        §4 item 3: finding where to write requires a read, and a read requires
        somewhere to stand. That was always true of the chain; situations make
        it true of the graph as well, because *what structure exists* is now a
        question with a standpoint. One assignment, two registers, and no caller
        that has to know.
        """
        self._focus = frame
        self.g.situation = frame.situation

    # -- supposing --------------------------------------------------------

    def suppose(
        self, assumption: NodeId, wrap: Optional[NodeId] = None
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

        ⭐⭐⭐ **And that was true of entries and false of structure, which is
        what the situation fixes** (`docs/situations.md`). Probed before it
        existed, on a supposition concluding an ordinary stratum-0 fact inside
        itself:

            is secret(a) BELIEVED at the root?     None      contained
            is said(secret(a)) in the graph?       True      not contained

        The seat could not close that, and no amount of ancestry could: the leak
        was never in the read. `at_or_after` is consulted when an ENTRY is
        resolved, and a structural fact is never resolved -- it is enumerated
        out of the argument index, which spanned everything. So a supposition
        cuts a **branch of the graph** as well as a successor of the chain, and
        the index keyed by that branch is what makes `said(secret(a))` die with
        the hypothesis that built it.
        """
        licence = self.g.rel(self.SUPPOSING, assumption)
        seat = self.chain.succeed(self.focus.seat, licence)
        # Cut before the frame is built and after the licence and the seat are,
        # so both of those are the caller's nodes: the caller has to be able to
        # name what it supposed and where it stood to suppose it.
        situation = self.g.branch(self.focus.situation)
        child = self.gate.frame(seat, parent=self.focus, purpose=licence, wrap=wrap,
                                situation=situation)
        # Moving the register. This is the irreducible part, and it is the ONLY
        # irreducible part -- §4 item 3: finding where to write requires a read,
        # and a read requires somewhere to stand. Everything else about supposing
        # is convention.
        self.focus = child
        self.gate.write(child, assumption, PLUS, licence=licence, source=self.KB)
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
        self.suppose(assumption, wrap=wrap)

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
        # ⚠⚠⚠ **The entries, not only the map.** This built `env` by READING the
        # plan's bindings and then wrote its answer with `consumed=(e, s)` -- so a
        # conclusion that relied on *which tap* did not rest on the entry that
        # said which tap. Three things followed, and all three are R5's
        # guarantee failing quietly at the one place a plan commits to something:
        #
        #   * `unsupported` could not see a withdrawn binding, so the two halves
        #     of this arc did not compose;
        #   * §12's weakest link could not weaken a conclusion by the grade of
        #     the binding it assumed -- a `@possible` tap laundered into a
        #     `@certain` achievement;
        #   * `why()` never mentioned which tap it had assumed.
        env: dict = {}
        env_from: dict = {}
        for s in state:
            if (
                s.sign == PLUS
                and self.g.relation_of(s.proposition) is self.BINDS
                and self.g.member(s.proposition, 0) == plan
            ):
                var = self.g.member(s.proposition, 1)
                env[var] = self.g.member(s.proposition, 2)
                env_from[var] = s
        licence = self.g.rel(self.ACHIEVED, goal)
        for s in state:
            if s.sign != PLUS or self.g.relation_of(s.proposition) in self._bookkeeping:
                continue
            b = unify(self.g, goal, s.proposition, dict(env))
            if b is None:
                continue
            # ⭐ *Not that one.* Reconsidering a binding was the last of the four
            # hats, and the reason it was stuck is smaller than it looked: a
            # `binds` fact has always been deniable, and denying it achieves
            # nothing, because this loop then re-unifies and picks the SAME first
            # candidate. What was missing was never a way to withdraw a choice;
            # it was a way to say what has already been tried.
            #
            # So the binding stays a construction (§18: deciding identity where
            # the name is read), and reconsidering one is an ordinary claim a
            # corpus makes and can itself deny.
            if any(
                self._claims(self.g.rel(self.EXCLUDED, plan, var, val))
                for var, val in b.items()
            ):
                continue
            # Only the bindings this goal actually USED. An env entry for a
            # variable the goal never mentions is not something the answer rests
            # on, and consuming it would make every sibling's conclusion depend
            # on every other sibling's choice -- which is the opposite of what
            # §18 wants from plan bindings.
            used = tuple(
                s2 for var, s2 in env_from.items() if occurs(self.g, var, goal, {})
            )
            self.gate.write(
                frame, self.g.rel(self.ACHIEVED, goal), PLUS,
                licence=licence, source=self.KB, consumed=(e, s) + used, mention=True,
            )
            for var, val in b.items():
                if var not in env:
                    self.gate.write(
                        frame, self.g.rel(self.BINDS, plan, var, val), PLUS,
                        licence=licence, source=self.KB,
                        consumed=(e, s) + used, mention=True,
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

    def _count(self, frame: Frame, e: Entry) -> None:
        """Answer *how many ground matches does this pattern have here?*

            count(goblin(?x))         a REQUEST, asked by a corpus rule
            counted(goblin(?x), 2)    the answer, and it always answers

        ⭐⭐⭐ **The general case of the three asks above it**, and the reason it
        is worth having is that they are three special cases of one question.
        `rooted`, `unsupported` and `blocked` each enumerate something the rules
        produced and each answers only *yes*, because each is a negative
        existential and §17 says deposit the smallest unarguable record. A count
        is not a negative existential -- it is the measurement all three are
        thresholds on -- so it answers with a number and lets a corpus write the
        comparison:

            { +counted(?p, 0) }  =>  nothing was told about it
            { +counted(?p, 1) }  =>  ***the*** one that satisfies it
            { +counted(?p, 2) }  =>  ambiguous, and what to do about it is mine

        ⚠⚠⚠ **The matcher does the counting, and that is the whole of why this
        is admissible.** `deposit-dont-decide.md`: the engine may compute
        anything whose result is a fact the rules can read, deny and argue with;
        what it may not do is decide. So the count is not a second enumeration
        written beside `match` -- it builds a one-member probe rule and runs the
        ordinary matcher, which means the number is *the same enumeration a rule
        would have got*, and a corpus can never be told a count that disagrees
        with what it could match for itself.

        ⚠⚠ **Answered at the ask, not at quiescence.** It is on the write path
        with the other answerers, so `count(...)` is answered the moment it is
        written. That is the opposite of `unsupported` -- which is a claim about
        a FINISHED search and a lie before `quiet` -- and it is right here for
        the reason the whole aggregate exists: a reading with two candidates is
        ambiguous *now*, and a corpus that had to wait for quiescence to find
        out would have acted on one of them already.

        ⚠ **A count is not monotone, and nothing pretends otherwise.** It is
        true of a moment and the next entry can falsify it. The answer is an
        ordinary dated fact, so the ordinary read supersedes it when the count
        changes -- but only if it is ASKED again, because the machinery does not
        volunteer. A corpus holding a stale count is holding a fact about the
        moment it asked, which is what it is.
        """
        if self.g.relation_of(e.proposition) is not self.COUNT or e.sign != PLUS:
            return
        (pattern,) = self.g.members(e.proposition)
        # A one-member probe, matched by the ordinary matcher at this frame --
        # `_spend_posts` builds one the same way for a postcondition's query.
        probe = Rule(e.proposition, IMPLIES,
                     [Member(PLUS, pattern)], [], "<count>")
        # ⚠ Distinct PROPOSITIONS, not applications, and this is a GUARD rather
        # than a repair -- said plainly because the difference matters. The
        # question is *how many things*, and an application is per surviving
        # entry; those coincide today, and probed on a proposition denied and
        # re-asserted they still coincide (2 applications, 2 propositions). So
        # nothing here has been seen to need it. It is kept because the two are
        # different questions and only one of them is the one being asked, and
        # the day `resolve` keeps two live entries for one proposition the count
        # should not quietly start answering the other.
        seen = set()
        for hit in match(
            self.g, self.chain, probe, frame.topic, frame.seat,
            self._situation(), computes=self.rules.computes,
            structural=self.rules.skeleton(),
        ):
            seen.add(substitute(self.g, pattern, hit.bindings))
        # ⚠⚠⚠ **Keyed on the ASK, not on the pattern, and that is what makes the
        # answer readable at all.** A statement's variables are scoped to it
        # (§8), so the `?x` in one rule's `goblin(?x)` is not the `?x` in
        # another's -- two rules writing the same description build two nodes,
        # and a corpus had no way to name the thing it had just asked about.
        # Keyed on `count(goblin(?x))` it does, by the route the surface already
        # gives a description: name the statement.
        #
        #     fact <goblins> = count(goblin(?x))
        #     rule <ambiguous> = implies( { +counted(<goblins>, 2) }, { ... } )
        #
        # Read back the pattern with an ordinary structural member if you want
        # it; the count is about the question that was asked.
        answer = self.g.rel(self.COUNTED, e.proposition, self._numeral(len(seen)))
        # ⚠⚠⚠ **A COUNT IS A FUNCTIONAL ATTRIBUTE, so the old one is denied in
        # the same breath.** `counted(p, 2)` and `counted(p, 3)` are different
        # propositions, so asserting the second leaves the first standing and
        # the corpus has two answers to one question -- which is the dungeon's
        # `hp(g1, 5)` and `hp(g1, 2)` defect exactly, one layer down, and the
        # design's own second constraint on this feature: *not monotone, by
        # construction; a count is true of a moment and can be falsified by the
        # next entry.*
        #
        # Authored corpora pay this by writing the denial and the assertion as a
        # pair. Nobody can write it here, because nobody but the machinery knows
        # what the previous count was -- so the machinery owes it, and the
        # alternative is an agent that believes there are two goblins and three.
        for old in self.g.instances_of(self.COUNTED):
            if old == answer or self.g.member(old, 0) != e.proposition:
                continue
            if self.chain.resolve(old, frame.topic, frame.seat) is None:
                continue
            self.gate.write(
                frame, old, MINUS, licence=e.proposition, source=self.KB,
                mention=True,
            )
        self.gate.write(
            frame, answer, PLUS,
            licence=e.proposition, source=self.KB, mention=True,
        )

    def _supported(self, frame: Frame, e: Entry) -> None:
        """Answer *does anything still hold this up?* -- the third negative
        existential, and it gets the treatment the other two got.

            support(p)        a REQUEST, asked by a corpus rule
            unsupported(p)    the answer, deposited only when nothing does

        §12's argument against making it a rule is the same one that settled
        `blocked` and `rooted`: *no remaining support* is a claim about every
        entry that ever claimed `p`, and a `-` member says *an entry denies
        this*, never *for no entry*. So it is machinery, and it **answers only
        yes** -- a machinery that answered *no* would be asserting a negative
        existential of its own (§17: deposit the smallest unarguable record).

        ⭐⭐⭐ **And what it does NOT do is retract.** Losing your reason is not
        acquiring a counter-reason. If a source is discredited, what it told you
        does not thereby become false; you have stopped having a reason, which is
        a different state and the one you can act on. An engine that deposited
        `-p` here would be making a claim about the world that nothing justified,
        and §12's weakest link would have a link with nothing behind it.

        It is also not the machinery's call. *Undo what the plan asserted* and
        *keep believing it until something contradicts it* are both correct, for
        different deployments, so the reaction is a corpus's:

            {+unsupported(?p)} => {-?p}                tear down
            {+unsupported(?p)} => {+goal(?p)}          go and re-derive it
            {+unsupported(?p)} => {+doing(ask(?p))}    ask
                                                      ...or nothing

        ⚠ **Asked, never volunteered**, and for `blocked`'s reason exactly: a
        proposition may rest on several things, so withdrawing one says nothing
        until the rest have been looked at. That makes this an aggregate over a
        finished search, legitimate at `quiet` and a lie before it.

        A fact nobody derived rests on nothing and is supported by its own
        assertion -- that is what makes this bottom out rather than regress.
        """
        if self.g.relation_of(e.proposition) is not self.SUPPORT or e.sign != PLUS:
            return
        (about,) = self.g.members(e.proposition)
        for claim in self.chain.claims_about(about):
            if claim.sign != PLUS:
                continue
            if not self._seat_holds(claim):
                continue
            if all(self._current(c) for c in self.chain.rests_on(claim)):
                return  # something still holds it up
        self.gate.write(
            frame, self.g.rel(self.UNSUPPORTED, about), PLUS,
            licence=self.g.rel(self.SUPPORT, about), source=self.KB,
            consumed=(e,), mention=True,
        )

    def _seat_holds(self, claim: Entry) -> bool:
        """Is this entry on the branch the register is standing on? Containment
        again: an entry made inside a supposition is not support out here."""
        return self.focus.seat.at_or_after(claim.locus) or claim.locus is self.focus.seat

    def _current(self, c: Entry) -> bool:
        """Is this consumed entry still what `resolve` returns for its own
        proposition? The chain is append-only, but `resolve` is not monotone --
        a later denial makes what an entry rested on no longer the claim."""
        return self.chain.resolve(
            c.proposition, self.focus.topic, self.focus.seat
        ) is c

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
        for settled in self._as_settled(wanted, state):
            self.gate.write(
                frame,
                self.g.rel(self.PURSUED if fits else self.BLOCKED, settled),
                PLUS,
                licence=self.g.rel(self.VERDICT, wanted),
                source=self.KB,
                consumed=(e,),
                mention=True,
            )

    def _as_settled(self, wanted: NodeId, state) -> NodeId:
        """A goal, with whatever its own plan has since bound filled in.

        ⭐⭐⭐ **A verdict was reported AS THE RULE WROTE IT, and by the time it is
        reported that is no longer the most informed thing available.** A foreign
        corpus found it (`docs/quest-feedback.md` §1): fitting `open(door1)`
        against `{ +have(?w, ?k), +opens(?k, ?d) }` subgoals `opens(?k, door1)`,
        the world satisfies it with `opens(key1, door1)`, **and the machinery
        records `binds(plan, ?k, key1)`** -- and then said `blocked(have(?w, ?k))`
        anyway. The binding was not missing. It was known, written down, and not
        read back.

        ⚠ **The consequence is exactly the one they named, and it is not
        cosmetic**: a generic term cannot be uttered (§14 -- `_dispatch` refuses a
        generic intent, because a description cannot be acted on), so an agent
        could not say what it was stuck on unless the rule's member happened to
        be ground already. They shaped a corpus around it, carrying
        `have(p1, key1)` ground for that reason alone. *Ask for help* was a
        special case when it should have been the general one.

        ⚠ Instantiated HERE rather than at the subgoal, and the moment is the
        argument: when `<expand>` writes the subgoals nothing has checked them
        yet, so the sibling's binding does not exist. A verdict is asked at
        quiescence, which is the latest moment there is -- so it is the one that
        knows the most.

        ⚠⚠⚠ **One answer PER PLAN, and the first version of this returned one
        answer and was silently wrong.** A rule fitted to two goals shares its
        variable nodes, so `plan(<unlock>, open(door1))` and
        `plan(<unlock>, open(door2))` both carry a `?k` -- the *same node* --
        bound to `key1` and `key2`, and they subgoal the *same* `have(?w, ?k)`
        node. Collecting every relevant binding into one environment then let the
        last one win: the agent was stuck on two keys and said one. Arbitrary and
        silent, which is the worst pair this design knows.

        ⚠ Only bindings from a plan this goal is actually a **subgoal of**. Every
        `binds` fact in the state would drag in an unrelated plan's choices, which
        is what `_check` already refuses one level down.

        ⚠⚠ **And that last restriction is UNFALSIFIABLE, recorded rather than
        left looking measured.** Removing it breaks nothing, and the reason is
        structural: §8 scopes variables to a statement, so a plan binding a
        variable that occurs in this goal must be built from the same rule -- and
        this goal is that rule's member, so every such plan is already in the set.
        The guard cannot currently be wrong. It is kept for `_check`'s reason,
        and because a second way of building plans would make it load-bearing
        immediately, but no check here can see it and none pretends to.
        """
        plans = {self.g.member(s.proposition, 0) for s in state
                 if s.sign == PLUS
                 and self.g.relation_of(s.proposition) is self.SUBGOAL
                 and self.g.member(s.proposition, 1) == wanted}
        if not plans:
            return [wanted]
        env: dict = {}
        for s in state:
            if (s.sign == PLUS
                    and self.g.relation_of(s.proposition) is self.BINDS
                    and self.g.member(s.proposition, 0) in plans):
                env.setdefault(self.g.member(s.proposition, 0), {})[
                    self.g.member(s.proposition, 1)] = self.g.member(s.proposition, 2)
        out = []
        for plan in sorted(plans):
            got = substitute(self.g, wanted, env.get(plan, {}))
            if got not in out:
                out.append(got)
        return out or [wanted]

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

    def _note_defeat(self) -> None:
        """Say which rule beat which, here.

            defeated(<loser>, <winner>)

        §21's defect for the **tenth** time, and this one is the pattern's
        purest case: `defeat` computes exactly this on every tick, uses it, and
        throws it away. Twenty-two defeats happened across the whole suite and
        no rule could ask about one of them -- so *which of my rules actually
        fight* was a question about a run that no run recorded.

        ⭐ It is the occasion, and §19 says that is all that ships. What to do
        about a rule that keeps losing -- ask its author, raise a precedence,
        mark it dormant, delete it -- is a corpus's, and there are at least four
        sensible answers:

            {+defeated(?l, ?w)} => {+doing(ask(?l))}  /  {+dormant(?l)}  /  nothing

        ⚠ **A defeat is not recorded when arbitration ignored it.** If every
        matched rule is defeated, §14's cycle fallback lets them all through so
        that arbitration stays total -- and nobody was defeated, so writing that
        somebody was would be recording an event that did not happen.

        ⚠ Costs nothing when nothing is ordered, which is most corpora: the
        authored precedence table is empty and this returns at the first line.
        """
        if not self.rules.precedence(self.OVERRIDES):
            return
        matched = list(self._matched_rules.values())
        pairs = [
            (loser, winner)
            for loser in matched
            for winner in _defeaters(self.rules, loser, matched)
        ]
        if not pairs or len({l.node for l, _ in pairs}) == len(matched):
            return  # nothing matched, or the cycle fallback let everyone through
        for loser, winner in pairs:
            self._note(
                self.g.rel(self.DEFEATED, loser.node, winner.node),
                licence=self.g.rel(self.APPLIED, winner.node),
            )

    def _close(self, a: Tuple[int, int], b: Tuple[int, int]) -> bool:
        """Are these two scores close enough to be doubt?

        The knob, read as data: `tolerance(2)` says a gap of two or less is not
        a difference the agent will rely on. Zero by default, so doubt is an
        exact tie until something claims otherwise -- and `standing` never ties
        with an ordinary rule, because a deliberate precedence is an answer.
        """
        return a[0] == b[0] and abs(a[1] - b[1]) <= self._tolerance()

    def _reaching(self, a: NodeId, b: NodeId) -> bool:
        """Does any rule say that `a` reaches `b`? (§11's containment, moved.)

        The machinery consulting a corpus's rules, on demand, with both
        arguments already bound -- the door `_forbid`, `precedence()` and
        `_recall` already use, given a general name. It is ONE backward step and
        not a fixpoint: the consequent is unified with the question, those
        bindings are substituted into the antecedent, and the antecedent is
        matched. Nothing has to be selected, which is the whole point -- a rule
        that had to win a move before the read could answer would make a span
        claim invisible until it did.

        ⚠ The author's line is about logic BURIED in Python, not about the
        direction of a call. A lookup that argues for nothing is not logic; the
        three span decisions it looks up are, and they are in `bundle.ugm` where
        a corpus can argue with them.
        """
        key = (a, b)
        hit = self._reaches.get(key)
        if hit is not None:
            return hit
        want = self.g.rel(self.chain.REACHES, a, b)
        answer = False
        for r in self.rules.rules:
            for m in r.consequent:
                if self.g.relation_of(m.pattern) is not self.chain.REACHES:
                    continue
                bound = unify(self.g, m.pattern, want, {})
                if bound is None:
                    continue
                probe = Rule(
                    r.node, r.connective,
                    [Member(x.sign, substitute(self.g, x.pattern, bound),
                            x.locus, x.binds)
                     for x in r.antecedent],
                    [], (r.name or "?") + "-reaches",
                )
                if match(self.g, self.chain, probe, self.focus.topic,
                         self.focus.seat, Situation(self.g, []),
                         computes=self.rules.computes,
                         structural=self.rules.skeleton()):
                    answer = True
                    break
            if answer:
                break
        self._reaches[key] = answer
        return answer

    def _note(self, proposition: NodeId, licence: Optional[NodeId] = None) -> None:
        """Record that the machinery did something a rule may care about.

        The user's reason, and it is the right one: these should be **reasonable
        over**. An agent that has reached past its shortlist twice, or been
        stopped by a bound, knows something about its own effort -- and until
        now that lived in a Python counter, which is §21's defect for the
        seventh time.

        Deduped by reading the graph: restating is not revising (§8), and the
        claim is *this happened here*, not how often.

        The licence defaults to *the loop ran out of work here*, which is what
        the effort records are about. A caller with a better answer to **why
        this is on the record** passes it -- `defeated` names the rule that won,
        the way `forgone` and `close` name the rule that was chosen.
        """
        if self._claims(proposition):
            return
        self.gate.write(
            self.focus, proposition, PLUS,
            licence=licence or self.g.rel(self.QUIET, self.focus.seat.node),
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

    def computator(self, name, fn) -> NodeId:
        """Register a function that is COMPUTED during a match (§12, §22).

            { +purse(?a, ?x), +cost(?i, ?c), minus(?x, ?c) as ?new }

        ⭐⭐⭐ **Purity is structural here, not declared.** An answerer is given
        `(machine, frame, entry)` and can do anything; a computator is given
        **values** and returns a value, so it cannot reach the graph, the
        register or the world -- there is nothing to reach them with. The
        deleted engine proved purity with 45 lines of transitive static
        analysis; not handing the function anything is cheaper and stronger.

        ⭐ And it is what makes an application ATOMIC. A tool answers through
        the write, so its answer lands a tick later and a transfer can be caught
        half-done -- measured, an agent emitted an act on a total that never
        existed (§22). Computed during the match, the result reaches the same
        consequent, in one moment.

        ⚠ It is registered in the CORPUS's scope, for `Loader.answerer`'s reason:
        a relation is a name, and a name minted beside the corpus's table is a
        relation nobody can write.
        """
        rel = self.g.atom(name) if isinstance(name, str) else name
        self.rules.computes[rel] = fn
        # ...and it is on the record, so *which of these exist* is a query
        # rather than a fact about the source (§17).
        self.gate.write(self.focus, self.g.rel(self.COMPUTES, rel), PLUS,
                        licence=self.g.rel(self.REIFIED, rel), source=self.KB,
                        mention=True)
        return rel

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
        # ⚠⚠ **And the protocol is checked HERE, at the one place both doors go
        # through.** Reported by `pystrider`, who registered a two-argument
        # function through the scoped door and got
        # `TypeError: <lambda>() takes 2 positional arguments but 3 were given`
        # out of `gate.write`, at the first write, with nothing saying the
        # registration was the problem -- one cycle to find. The mistake is easy
        # to make because the apparatus's own reifier registers `(frame, entry)`
        # and wraps it, so both arities are visible in this file.
        #
        # A registration is a declaration, and §5 says a silence is the defect:
        # this refuses it at the moment the claim is made, which is the only
        # moment the caller is looking at it.
        try:
            inspect.signature(fn).bind(None, None, None)
        except TypeError:
            raise TypeError(
                f"answerer {name!r} does not take (machine, frame, entry) -- an "
                f"answerer is called with three arguments and returns the answer "
                f"node, or None for *I have nothing to say*"
            ) from None
        except (ValueError, AttributeError):
            pass  # a builtin or C callable has no signature to read; let it run
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
        into a belief is an authored rule, which may wrap it as weakly as it likes, so a
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

    # `_precede` and `_precedence_for` were here: a write hook that kept a
    # Python precedence table equal to the graph, and a re-scan that caught the
    # precedences written before their rule was live. Both are gone, because
    # `RuleSet.precedence` reads the graph instead of mirroring it -- so there
    # is nothing to keep equal and nothing to catch up. Measured before
    # deleting: the suite runs in 6.42s against 6.38s, so the table was buying
    # nothing but the two ways it could be wrong.

    def _adopt(self, frame: Frame, e: Entry) -> None:
        """Make a rule the graph describes into a rule the loop reads.

            adopt(<R>)

        ⭐⭐⭐ **`reify` went one way.** A rule has been data since §14's worked
        example -- `rule(<R>)`, `conn`, `ant`, `con`, all deposited at authoring
        -- and `RuleSet.rule` was called only by the parser and by tests. So the
        agent could be asked *which rules do I have* and could never answer
        *and now I have this one*. Every amendment was a file edit, which is
        why nothing in the harmonization family was buildable.

        This is a **door, not a question**, and belongs with `_dispatch` and
        `_enter` rather than with the six answerers: `_dispatch` is where an
        intent leaves the agent and this is where a rule enters it. What decides
        that a rule is worth having is a corpus concluding `adopt(?r)`; what
        happens then is not a judgement.

        ⚠⚠⚠ **Refused inside a supposition, and this is containment rather than
        caution.** §4 makes a frame's conclusions unreadable from outside by
        construction -- the seat is a successor, so the caller's walk never
        reaches it -- but `RuleSet.rules` is one list shared by every frame. A
        rule adopted while supposing would apply *after* the frame is discharged
        and to everything, so supposing would change what the agent believes,
        which is the one thing supposing must not do. `_dispatch`'s argument
        exactly: **supposing must not bring it about.** Refused on the record,
        naming the supposition, because a silent decline is what §5 spent the
        vocabulary avoiding.

        ⚠ A generic `adopt` is not acted on, for `_dispatch`'s reason: a
        description of a rule is not a rule.
        """
        if e.sign != PLUS or self.g.relation_of(e.proposition) is not self.ADOPT:
            return
        if self.g.has_var(e.proposition):
            return  # a description cannot be adopted; §15's condition again
        (node,) = self.g.members(e.proposition)
        if any(r.node == node for r in self.rules.rules):
            return  # already live -- restating is not revising (§8)
        if self._hypothetical(frame):
            refusal = self.g.rel(
                self.REFUSED, e.proposition, self.chain.SIGN[PLUS],
                frame.purpose or self.g.rel(self.SUPPOSING, node),
            )
            if self.chain.resolve(refusal, frame.topic, frame.seat) is None:
                self.gate.write(frame, refusal, PLUS, licence=e.node,
                                source=self.KB, mention=True)
            return
        built = self._read_rule(frame, node)
        if built is None:
            return
        connective, ant, con = built
        # Through `RuleSet.rule`, so an adopted rule is a rule in every respect:
        # reified, indexed by what it concludes, and visible to `_recall` on the
        # next tick. ⚠ Its name is the node's, so `why()` and the report print
        # something a reader can look up rather than ninety characters of its
        # own structure.
        # ⚠ The node the graph described, never a fresh one. See `RuleSet.rule`.
        self.rules.rule(connective, ant, con, self.g.show(node), node)

    def _compose(self, frame: Frame, e: Entry) -> None:
        """Collapse two rules into one, because a corpus asked.

            compose(<a>, <b>)     ⟹     composed(<c>, <a>, <b>)

        §4 calls composition the design's larger optimisation -- it removes
        steps rather than making them cheaper -- and it had no trigger: the
        function existed and only Python called it, which is where `adopt` was
        before it was a door.

        ⭐⭐⭐ **The corpus decides; the function executes.** Which rules are
        worth collapsing is a judgement, and §21's judgement census says a
        judgement the machinery makes alone is a seam: the agent could not
        notice it was composing the wrong things, because a bad shortcut makes
        worse work and never a wrong conclusion, so no fixture fails. So this
        answers a request and never proposes one. `{+exercised(?a), +exercised(?b)}
        ⟹ {+compose(?a, ?b)}` is a corpus's line, and *compose what has run
        often and never surprised* stays §22's open trigger rather than becoming
        a constant in here.

        ⚠⚠⚠ **Refused inside a supposition, and it is `_adopt`'s argument
        exactly.** `RuleSet.rules` is one list shared by every frame, and
        `compose` appends through `RuleSet.rule` -- so a shortcut built while
        supposing would apply after the frame is discharged and to everything.
        Supposing would change what the agent believes, which is the one thing
        supposing must not do. This guard is the reason composition could not
        simply be wired to the existing function.

        ⚠ **What it deposits closes a defect rather than adding vocabulary.**
        `composed_from` was a Python dict, so *which rules is this a shortcut
        for* was unanswerable by any rule -- §1's pattern, and the one §22 needs
        for *decompose on surprise*, since the licence has to name the
        constituents for the agent to know which sub-steps to re-run.

        ⚠ Inherited precedence is deposited here, not appended to a list: since
        precedence is READ from the graph (§18), a defeat that binds a
        constituent has to bind the composition as a **claim** or it does not
        bind at all.
        """
        members = self.g.members(e.proposition)
        if len(members) != 2:
            return None
        # ⚠⚠⚠ **`has_var` is not a usable guard here, and copying `_adopt`'s was
        # the bug.** A LIVE rule node is `causes(moment(...), moment(...))` and
        # therefore holds the variables of its own patterns, so
        # `compose(<s1>, <s2>)` reports generic however ground the claim is.
        # That is §5's use/mention distinction: a ground claim ABOUT a rule names
        # a node containing variables, and structurally the two are identical.
        # `_adopt` gets away with the test only because the rule it names has
        # been described and not yet built.
        #
        # What tells them apart is membership of the live set: `by_node` answers
        # *is this a rule* without asking what it looks like. A genuinely generic
        # `compose(?x, ?y)` has variables as members, and a variable is in no
        # rule set, so the same line refuses it.
        first = self.rules.by_node.get(members[0])
        second = self.rules.by_node.get(members[1])
        if first is None or second is None:
            # Not live rules. `None` is a real answer (§17) -- a tool that must
            # answer everything is one nothing can decline.
            return None
        if self._hypothetical(frame):
            refusal = self.g.rel(
                self.REFUSED, e.proposition, self.chain.SIGN[PLUS],
                frame.purpose or self.g.rel(self.SUPPOSING, e.proposition),
            )
            if self.chain.resolve(refusal, frame.topic, frame.seat) is None:
                self.gate.write(frame, refusal, PLUS, licence=e.node,
                                source=self.KB, mention=True)
            return None
        self.rules.inherit = []
        composed = self.rules.compose(first, second)
        if composed is None:
            return None  # nothing of the first's consequent meets the second
        self.gate.write(
            frame,
            self.g.rel(self.COMPOSED, composed.node, first.node, second.node),
            PLUS, licence=e.node, source=self.KB, mention=True,
        )
        for higher, lower in self.rules.inherit:
            self.gate.write(
                frame, self.g.rel(self.OVERRIDES, higher.node, lower.node),
                PLUS, licence=e.node, source=self.KB, mention=True,
            )
        self.rules.inherit = []
        return None

    def _read_rule(self, frame: Frame, node: NodeId):
        """What the graph says this rule is, or `None` if it does not say.

        Read at the frame's own position through `resolve`, so a retracted part
        is not read -- amending a rule is denying one of its members, and that
        has to be what the reader sees.

        ⚠ **Position is what orders the members**, not the order the facts were
        deposited in. Minting order would reproduce authored order by accident
        for anything `reify` wrote, and a check over it could never fail.
        """
        conn = None
        for p in self.g.instances_of(self.CONN):
            if self.g.member(p, 0) is node and self._claims(p):
                conn = self.g.member(p, 1)
        if conn is None:
            return None
        connective = CAUSES if conn is self.rules.CAUSES else IMPLIES
        sign_of = {v: k for k, v in self.chain.SIGN.items()}

        def slot(rel_kind, relation, i):
            """A member's extra slot -- its locus, or the name it gives what it
            matched -- read at the frame's position like everything else here."""
            for q in self.g.instances_of(rel_kind):
                mm = self.g.members(q)
                if (len(mm) == 4 and mm[0] is relation and mm[1] is node
                        and self.g.show(mm[2]) == str(i) and self._claims(q)):
                    return mm[3]
            return None

        def locus_at(relation, i):
            """...and the member's locus, if the graph says it has one (§12).

            Read the same way as everything else here -- through `_claims`, at
            the frame's position -- so amending a rule's locus is denying a
            fact, exactly as amending its members is.
            """
            for q in self.g.instances_of(self.AT):
                mm = self.g.members(q)
                if (len(mm) == 4 and mm[0] is relation and mm[1] is node
                        and self.g.show(mm[2]) == str(i) and self._claims(q)):
                    return mm[3]
            return None

        def side(relation):
            out = []
            for p in self.g.instances_of(relation):
                if self.g.member(p, 0) is not node or not self._claims(p):
                    continue
                members = self.g.members(p)
                i = self.g.show(members[3])
                out.append((i, Member(sign_of.get(members[2], PLUS), members[1],
                                      locus_at(relation, int(i)),
                                      slot(self.NAMES, relation, int(i)))))
            return [m for _, m in sorted(out, key=lambda pair: int(pair[0]))]

        con = side(self.CON)
        if not con:
            return None  # a rule that concludes nothing is not a rule
        return connective, side(self.ANT), con

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
                # ⭐⭐⭐ **Carried across the situation boundary, by atom.**
                # This is the one place a node built inside a hypothesis becomes
                # something the caller says, and before situations there was
                # nothing to do here because there was no boundary -- which is
                # exactly the defect. `e.proposition` is a node of the
                # hypothesis's branch; re-stating it at the caller's seat has to
                # re-state it in the caller's branch, or the caller's own
                # indices would end up holding a reference to structure it
                # cannot see, and the leak would come back through the door
                # marked *conclusions*.
                #
                # `carry` re-interns in the target and records where the thing
                # landed, so the caller's `likely(q)` is about the caller's `q`
                # -- the one it already had, if it had one.
                inner = self.g.carry(e.proposition, parent.situation)
                sign = e.sign
                if sign == MINUS:
                    inner, sign = self.g.rel(self.NOT, inner), PLUS
                crossed = self.g.rel(wrap, inner)
                out.append(
                    self.gate.write(
                        parent,
                        crossed,
                        sign,
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
        self._forget_spent(frame)
        frame.carried = out
        return out

    # -- the loop ---------------------------------------------------------

    def tick(self) -> Step:
        # ⭐ **The register's own seat is askable**, so a rule that reads the raw
        # chain has an anchor without anything handing it one. Skeleton, so it is
        # minted rather than deposited, and interned, so this is a dict lookup
        # after the first tick at a seat.
        #
        # ⚠ Without it a corpus's chain-reading rules are DEAD: every structural
        # member is anchored, and `anc(?s, ?d)` with nothing binding `?s` finds
        # nothing. `ask_read` seeded it by hand for the gate, and a corpus has no
        # such hand -- so the capability existed and no corpus could reach it.
        # That is §21's defect in its usual shape, caught one commit after the
        # thing it is about.
        #
        # ⚠ Anchored at the SEAT rather than at every moment, which is the
        # containment story as well as the cheap one: what the agent may read the
        # chain about is where the agent is standing.
        self.g.rel(self.chain.ASKING, self.focus.seat.node)

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
        state = self._situation()
        self._applications(proposed, state)
        # What the situation recommends, computed once for this tick.
        keys = self._in_play()
        rank = lambda r: self._rank(r, keys)
        # Defeat, quiescence, passing-up and arbitration, all of them lazily and
        # none of them over the whole candidate set. `_choose` is the same four
        # steps in the same order -- see its docstring for why each may be done
        # at the top of a heap instead of over a list, and `ugm.arbitration` for
        # the instrument that holds it to the list version's answer.
        chosen, rivals, sharing = self._choose(proposed, keys)
        # Before the move, for §16's reason and for `_note_doubt`'s: what lost
        # is visible now. ⚠ And OUTSIDE `_choose`, because `ugm.arbitration`
        # re-runs that path against the same state and its whole legitimacy is
        # that neither side writes -- an instrument that deposits has stopped
        # observing and started being a second agent.
        self._note_defeat()
        if chosen is not None:
            self._note_doubt(rivals, chosen, rank)
            # Before applying, not after: the rivals are visible now, and this is
            # §16's ordering trap for the fourth time.
            self._forgo(sharing, chosen)
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
        # Refraction: this instantiation has now run. Recorded AFTER the write,
        # because `_spend` indexes what the application concluded and that is
        # what `_contest` watches for a later denial.
        self._spend(chosen, wrote)
        self.useful_writes += len(wrote)
        # `matched` in a Step is now *how many candidates were weighed to make
        # this move*, which is what the field always meant and no longer the
        # same as how many exist. The chooser stops at the first that survives.
        return Step(arrivals, len(proposed), 1 + len(rivals), chosen, wrote, "applied")

    def run(self, limit: int = 100) -> List[Step]:
        """Bounded, and it returns a result *and* a state -- because a search that
        stopped is not a search that found nothing (§9, §15).

        ⭐⭐⭐ **And the bound says so, which is §21's defect for the eleventh
        time and the one a foreign corpus asked for first.** `docs/quest-feedback.md`
        §0: they wrote three corpora, made six rule bugs, and **not one produced an
        error** -- four ran to the tick limit and two were silent. What the engine
        said about a corpus that never terminates:

            settles      steps=  3/60   last=quiescent
            runs away    steps= 60/60   last=applied

        A corpus that is finished and one that never will be differed only in
        whether `len(steps)` happened to equal the limit **the caller chose**, and
        `exhausted` stayed 0 either way. **No rule could ask *did I run out of
        time?*** -- while the depth and hypothesis budgets both deposit
        `bounded(...)` when they bite. The tick limit was the one bound not on the
        record, and that was inconsistent with this engine's own practice rather
        than a considered position.

        ⚠ Deposited only when the loop is still WORKING at the limit. A run that
        stops because there is nothing left to do has not been bounded by
        anything, and saying it had would make the record useless in the other
        direction.
        """
        # ⚠⚠⚠ **THE MIGRATION TO THE TABLE LOOP IS STAGED, AND THIS IS THE
        # SWITCH.** Replacing the body with `attention.run(self, limit).steps`
        # is one line and it works -- the table loop now returns `Step`s for
        # exactly that reason. What it costs today is **58 of 549 checks**, and
        # the list is not noise: `enough` and its open-goal veto, dormancy and
        # callbacks, proposing a supposition, and the match cache. Each is a
        # piece of the tick this loop does not do yet.
        #
        # Left on the option-set loop until those land, so the repository never
        # stops running -- *subtract, do not rewrite*, which is the discipline
        # that made every other Python deletion here safe.
        # ⭐⭐⭐ **THE TABLE LOOP IS THE LOOP.** What stood here -- materialise every
        # live application, defeat, filter, arbitrate, apply -- is gone. The
        # option set was the price of being able to say *nothing else applied*,
        # and the author's judgement is that it is not worth paying on every
        # tick: the table is a prefix scan, so a rule below the window costs
        # nothing at all.
        #
        # **Held to the loop it replaces before that loop stopped being the
        # one that runs**, and the numbers are the argument rather than the
        # decision: 58 of 545 checks failed at the first flip, and the suite is
        # now green under BOTH -- every check that remains is loop-agnostic,
        # every check that was not is either ported or deleted with the
        # machinery it described. `ugm.attention` still gates conclusions on
        # four corpora, one-sided: the table loop may conclude more, never less,
        # except `close` and `forgone`.
        #
        # ⚠ The import is local because `attention` imports this module. The
        # cycle is real, and the alternative -- moving the loop in here -- would
        # put the table back inside the engine, which is the thing this undoes.
        from .attention import run as _table_run

        return _table_run(self, limit=limit).steps

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

        ⚠ Both halves are accumulated rather than scanned, and they accumulate
        for different reasons -- which is the same asymmetry `named` measured
        when it asked whether either could be a fact. The delta half is
        **monotone by construction**: a moment's delta only ever grows, so what
        it has mentioned is a running union over a cursor. The goal half is not
        monotone -- a goal can be denied, and then it is no longer in play -- so
        it is a count maintained where the state is, not a union.
        """
        seat = self.focus.seat
        play = self._play_cache.get(seat.node)
        if play is None:
            play = {"pos": 0, "rels": set()}
            self._play_cache = {seat.node: play}  # one seat at a time
        for i in range(play["pos"], len(seat.delta)):
            rel = self.g.relation_of(seat.delta[i].proposition)
            if rel is not None:
                play["rels"].add(rel)
        play["pos"] = len(seat.delta)
        # ...and what the agent is TRYING TO DO, which is not the same question
        # and turned out to be the one that matters. Keyed only on what changed,
        # a table cannot discriminate on goal-directed work: every domain the
        # agent knows about is in play all the time, and being in play says
        # nothing about being useful. A live goal does.
        return play["rels"] | self._kept()["goals"].keys()

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

        This adds nothing ordinal, and there is no longer anything ordinal for
        it to be confused with: §10's grades are gone, and *how sure the agent
        is* is a wrapper around a claim rather than a number beside one. How
        strong a recommendation is and how sure the agent is of it were always
        two quantities; now only one of them is a number.
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
        uncertainty now reaches the `says` claim as a wrapper a rule can read instead of
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
        # ⭐⭐⭐ **And the same argument one layer down, which situations made
        # visible.** The comment below says the report belongs to the agent
        # rather than to what the agent happens to be supposing, and that was
        # true of the SEAT and false of everything else on this path: the
        # register is inside the hypothesis, so the successor moment, the
        # utterance and `arrived(...)` itself were all being minted into the
        # hypothesis's branch and then deposited into the agent's own delta.
        # The entry was the agent's and its proposition was not, so a rule at
        # the root asking what a channel said would have found nothing
        # structurally -- the world's own testimony, contained inside a guess
        # about it. `reseat` is not enough on its own for the same reason a
        # successor seat was never enough on its own.
        with self.g.standing_in(own.situation):
            self._report(own, a)

    def _report(self, own: Frame, a: Arrival) -> None:
        """The body of `_deliver`, standing in the agent's own situation."""
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
            self.gate.reseat(own, self.chain.succeed(own.seat, self.KB),
                             licence=self.KB, source=a.channel)
        utterance = self.g.instance(self.UTTERANCE, a.channel, a.proposition)
        report = self.g.rel(
            self.ARRIVED, a.channel, a.proposition, self.rules.SIGN[a.sign]
        )
        self.gate.write(
            own, report, PLUS, licence=utterance, source=a.channel,
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
            self.gate.reseat(self.focus, self.chain.succeed(self.focus.seat, licence),
                             licence=licence, source=self.KB)
        frame = self.focus
        mention = self._is_mention(app)

        # ⭐⭐⭐ **§6's price, charged by §6's own test.** A rule whose antecedent
        # is entirely structural is applied without a read, so it must conclude
        # without one: *stratum 0 must produce structure, not entries. If the
        # walk deposited its intermediate results as claims, it would be reading
        # entries and the circle would return.* So the conclusion is an ordinary
        # interned relation instance -- undated, unattributed, deniable by
        # nothing -- which is exactly what the skeleton is everywhere else.
        #
        # ⚠ That is the whole of the difference between the two matchers. Same
        # recall, same match, same arbitration, same rule type, same surface;
        # one more row deciding where the consequent lands, and the row is read
        # off the antecedent rather than authored. §5's *one interpreter* and
        # §6's *one more row, not one more branch* are both true of the code now.
        #
        # ⚠ Interning is what makes the fixpoint detectable: a fact already
        # derived mints no node, so a stratum-0 rule re-applying is a no-op and
        # quiescence sees it as one.
        if self.rules.is_stratum0(app.rule):
            self._mint_structure(app)
            return ()

        wrote: List[Entry] = []
        # ⭐⭐⭐ **A rule may introduce a thing that did not exist.** Everything a
        # consequent could name until now came from a binding or was written
        # literally, so *there is some new person here* was unsayable -- the
        # binding check refuses `+named(?p, ?x)` with `?p` unbound, correctly,
        # because the gate cannot deposit a variable. `new(person)` says it
        # instead: a marker term the application replaces with a node it mints.
        #
        # ⚠ **One node per distinct marker per APPLICATION**, so `+a(new(p))`
        # and `+b(new(p))` in one consequent are about the same new thing, and
        # two firings are about two things. That is what keeps two people called
        # Paul apart: the mint is per occasion, not per name.
        #
        # ⚠⚠ **Refraction is what stops this running away**, and it already
        # exists: an instantiation fires once for a given set of premises
        # (`_survives` -> `_spent`), so a minting rule cannot re-fire on the
        # bindings it already used. What refraction does NOT stop is a
        # generative CHAIN -- mint, conclude about the new node, mint again --
        # because those are different bindings every time. Quiescence cannot see
        # it either: a fresh node always changes something. `bounded(ticks)` is
        # the backstop, and it reports after the fact.
        marks = self._markers(app.rule)
        if marks:
            app = app._replace(bindings={
                **app.bindings,
                **{mk: self.g._mint(None, (), None) for mk in marks},
            })
        for m in app.rule.consequent:
            grounded = substitute(self.g, m.pattern, app.bindings)
            if app.rule.connective == "causes":
                self._expect(frame, grounded, m.sign, licence)
            wrote.append(
                self.gate.write(
                    frame,
                    grounded,
                    m.sign,
                    licence=licence,
                    source=self.KB,  # the rule is the licence; the KB is the channel
                    consumed=app.consumed,
                    mention=mention,
                    locus=self._conclude_at(m, app.bindings),
                )
            )
        return tuple(wrote)

    def _conclude_at(self, member, bindings, strict: bool = True) -> Optional[Locus]:
        """A consequent member's own locus (§8), or None for the frame's topic.

        ⚠⚠⚠ **This was parsed, boundness-checked, reified -- and ignored.**
        `text.py` refuses a consequent whose locus variable no antecedent binds,
        `_reify_locus` records it so the round trip through the graph keeps it,
        and `_apply` then wrote every conclusion at the frame's topic anyway. So
        `{ +noted(?p) at ?mp }` matching entries at M1 and M2 deposited BOTH at
        M2, and nothing could see it: the two differ only in a field no outcome
        check reads. §21's defect for the eleventh time, and this face of it --
        *a knob read and not obeyed* -- is the one `adopt` recorded about a
        rule's grade, arriving at the locus.
        ⚠ It is also what spans needed: a span can only be a locus if a rule can
        SAY which locus it concludes at, and until this line the only locus a
        rule could ever produce was the one the frame supplied.

        The locus a rule may name is one the antecedent bound, so it is a moment
        or span already on the frame's walk. The seat check is kept anyway,
        because `reify`/`adopt` can hand this a rule nobody parsed.

        ⚠ `strict=False` is for quiescence, which asks this about applications
        that may never be chosen. It answers `None` where the strict form
        refuses, so a malformed locus is reported once at the write -- where the
        rule is actually being applied and the mistake is attributable -- rather
        than from inside a verdict about a move nobody made.
        """
        if member.locus is None:
            return None
        node = substitute(self.g, member.locus, bindings)
        if self.g.is_var(node):
            return None  # unbound: the frame's topic, as before
        locus = self.chain.locus_by_node(node)
        if locus is None:
            if not strict:
                return None
            raise ValueError(
                f"a consequent's locus must be a moment or a span, and "
                f"{self.g.show(node)} is neither"
            )
        if not self.focus.seat.at_or_after(locus):
            if not strict:
                return None
            # The gate's own rule for a frame, one level down: a claim about a
            # locus the seat does not reach is a claim about the future, and §8
            # gives it nowhere to sit.
            raise ValueError(
                f"cannot conclude at {locus}: the seat {self.focus.seat} does "
                f"not reach it"
            )
        return locus

    # -- stratum 0 (§6) ----------------------------------------------------

    def _mint_structure(self, app: Application) -> int:
        """A stratum-0 rule's conclusion: an ordinary interned relation
        instance, undated and unattributed. Returns how many were NEW, which is
        what makes the fixpoint detectable -- interning means a fact already
        derived mints no node.
        """
        added = 0
        for m in app.rule.consequent:
            # ⚠⚠⚠ **The count is taken BEFORE substitution, and that is the
            # whole of the fixpoint.** `substitute` builds the grounded node with
            # `g.rel`, which interns -- so the fact is created there, and a
            # novelty test made afterwards always finds it already present. The
            # loop then derived everything correctly and believed it had derived
            # nothing: one pass per layer, no fixpoint, and a read that answered
            # from a third of the candidates. It failed as a wrong ANSWER rather
            # than as a crash, which is the only reason the gate caught it.
            before = self.g.count()
            grounded = substitute(self.g, m.pattern, app.bindings)
            if _left_open(self.g, m.pattern, app.bindings):
                continue
            if m.sign != PLUS:
                # There is nothing to deny. A skeleton fact is how the graph was
                # built; a rule concluding `-pred(...)` is not saying something
                # false, it is saying something with no meaning, and silence
                # would hide the author's mistake rather than tolerate it.
                raise ValueError(
                    f"{app.rule}: a stratum-0 rule concludes structure, and "
                    f"structure has no sign -- '{m.sign}' on "
                    f"{self.g.show(m.pattern)} cannot be deposited"
                )
            self.g.rel(self.g.relation_of(grounded), *self.g.members(grounded))
            if self.g.count() != before:
                added += 1
            # ⚠⚠⚠ **A structural fact enters no delta, so nothing re-triggers a
            # rule that reads it.** Incremental matching is driven by the seat's
            # delta -- a `Situation` of ENTRIES -- and structure is not an entry,
            # by §6's whole design. So a rule mentioning a structural relation
            # was matched in full exactly once, on its first pass, and anything
            # derived after that stayed invisible to it for ever. Measured: the
            # stratum-0 half concluded correctly and the ordinary rule reading
            # its conclusion never fired at all.
            #
            # ⚠⚠⚠ Recorded UNCONDITIONALLY, not on novelty, and that is the
            # interning trap for the third time in one commit. Quiescence has
            # already run `substitute` on this conclusion to decide whether it
            # would change anything -- which INTERNS it -- so by the time the
            # mint happens the novelty is gone and a novelty-gated record
            # captures nothing. Over-invalidating by relation costs one extra
            # full match; under-invalidating loses the conclusion permanently.
            self._structure_touched.add(self.g.relation_of(grounded))
        return added

    def ask_read(self, *seats, about=()) -> None:
        """Seed `asking(<seat>)` -- what the rule-level read is anchored on --
        and `asked(<prop>)` for each proposition the question is about.

        Skeleton, so it is minted rather than deposited: the question is not a
        claim about the world, and §6's price applies to it as to every other
        structural fact the read produces.

        `about` may be empty, and then the read is asked about everything the
        chain mentions, which is what it always did. That is the honest default
        and a costly one: the read is a fixpoint, so an unasked proposition
        still gets its candidates, its beatings and its winner.
        """
        for s in seats:
            self.g.rel(self.chain.ASKING, s.node)
        for p in about:
            self.g.rel(self.chain.ASKED, p)

    def settle_structure(self) -> int:
        """Run the stratum-0 rules to fixpoint, layer by layer.

        ⭐ §6's recall policy, and it is the whole of what makes stratum 0
        different: *recall for stratum 0 is all of them, every time -- the set
        is small and fixed, so the policy is a different table, not a different
        mechanism.* Match is the shared one, the rules are ordinary rules, and
        the conclusion is minted by the shared `_mint_structure`.

        ⚠ Each LAYER to fixpoint before the next begins, because a negated
        member reads a lower layer and must read a finished one (`RuleSet.strata`).

        ⭐⭐⭐ **Semi-naive: a rule is re-run only when something it READS has
        grown.** A rule's matches depend on exactly the relations in its
        antecedent, plus the chain, which does not move while this runs. So if
        none of them gained a fact since the rule last ran, it can produce
        nothing new and running it is pure waste -- which is what the naive
        version did, re-running every rule in the layer on every pass.

        It pays where the layer is uneven, and the read's is: `cand` is the
        expensive rule and depends on **nothing derived**, so it runs once
        instead of once per pass, while `dep_after` recurses and keeps its turn.
        **14.4s -> 5.6s** on the same 553 facts.

        ⚠ And then profiling said the rest was not here at all: `has_var` was
        **91%** of what remained, asked of every instance in a bucket on every
        enumeration and re-walking the whole structure each time. Deciding it at
        mint took the same run to **0.42s**. *Measure before optimising* --
        semi-naive was the right change and the third of the total.

        ⚠ This is the coarse form -- by RELATION, not by fact. True semi-naive
        would hand each rule only the facts that appeared, the way `match`'s
        `fresh` delta does for the ordinary loop; that cannot be reused here
        because `fresh` is a `Situation` of entries and these are not entries.
        The refinement is available and unmeasured.
        """
        derived = 0
        rel_of = self.g.relation_of
        for layer in self.rules.strata():
            # Everything runs once; after that, only what reads something new.
            pending = list(layer)
            while pending:
                grew: set = set()
                for r in pending:
                    added = 0
                    for app in match(
                        self.g, self.chain, r, self.focus.topic, self.focus.seat,
                        Situation(self.g, []),
                        computes=self.rules.computes,
                        structural=self.rules.skeleton(),
                    ):
                        added += self._mint_structure(app)
                    if added:
                        derived += added
                        for m in r.consequent:
                            grew.add(rel_of(m.pattern))
                if not grew:
                    break
                pending = [
                    r for r in layer
                    if any(rel_of(m.pattern) in grew for m in r.antecedent)
                ]
        return derived

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

    def _kept(self) -> dict:
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

        ⭐⭐⭐ **What is kept is the SITUATION, not a list.** Keeping the state and
        then materialising it -- and indexing it, and scanning it for goals --
        once per tick left the tick O(everything known) anyway, which is the
        whole of what `heap` measured and could not fix. The three consumers are
        maintained through the same one-claim-at-a-time walk that maintains the
        state: `Situation.add`/`drop` for the matcher's index, and a count per
        key for `_in_play`. A tick is then O(what changed).

        ⚠ The keys are a COUNT and not a set, because two goals can put the same
        relation in play and one of them going away must not take the other's key
        with it. The same reason `emitted` had to be read off the graph: a
        derived set that forgets who contributed to it cannot be maintained.
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
        # ⚠ `_merges` is part of the key: a merge changes which entries answer
        # which member, and the kept state is MAINTAINED rather than rebuilt --
        # so without this the state keeps answering with the index it had
        # before two things became one.
        key = (topic.node, seat.node, hidden, self.g._merges)
        cache = self._state_cache.get(key)
        if cache is None:
            props: dict = {}
            sit = Situation(self.g)
            goals: dict = {}
            # Oldest first, so the dict's insertion order is claim order and
            # reading it back reversed gives the walk's newest-first order.
            for e in reversed(current_state(self.chain, topic, seat)):
                if e.source in hidden:
                    continue
                # ⚠ (proposition, span) rather than proposition -- see
                # `chain.scope_of`. Two recognitions over different stretches
                # supersede nothing of each other, and keyed by proposition the
                # state kept exactly one of them.
                props[(e.proposition, scope_of(e.locus))] = (
                    (e.locus.depth, seat.depth, 0), e
                )
                sit.add(e)
                self._count_goal(goals, e, +1)
            cache = {"pos": len(seat.delta), "props": props,
                     "sit": sit, "goals": goals}
            self._state_cache = {key: cache}
            return cache

        props, sit, goals = cache["props"], cache["sit"], cache["goals"]
        for i in range(cache["pos"], len(seat.delta)):
            e = seat.delta[i]
            if not topic.at_or_after(e.locus):
                continue  # a claim about a moment later than what we are about
            if e.source in hidden:
                continue  # a domain that is not in mind
            k = (e.locus.depth, seat.depth, i)
            scope = (e.proposition, scope_of(e.locus))
            prev = props.get(scope)
            if prev is not None:
                if k <= prev[0]:
                    continue
                del props[scope]          # re-inserted below, so it moves to
                sit.drop(prev[1])         # the newest end of the order, and
                self._count_goal(goals, prev[1], -1)  # stops being in play
            props[scope] = (k, e)
            sit.add(e)
            self._count_goal(goals, e, +1)
        cache["pos"] = len(seat.delta)
        return cache

    def _count_goal(self, goals: dict, e: Entry, by: int) -> None:
        """What an entry puts in play by being a live goal, counted.

        Two keys and not one: the goal itself, and its RELATION, which is the
        half that transfers. A key that is the goal itself is true of one
        episode -- what an agent learned about `boiling(kettle)` says nothing
        when it is next asked for `boiling(pot)`, and a table that cannot
        generalise is a cache. The relation is the coarsest thing two episodes
        can share, so it is where experience can accumulate at all.
        """
        if e.sign != PLUS or self.g.relation_of(e.proposition) is not self.GOAL:
            return
        wanted = self.g.member(e.proposition, 0)
        rel = self.g.relation_of(wanted)
        for k in ((wanted,) if rel is None else (wanted, rel)):
            n = goals.get(k, 0) + by
            if n:
                goals[k] = n
            else:
                goals.pop(k, None)

    def _situation(self) -> Situation:
        """The kept state, indexed for matching. See `_kept`. This is what the
        loop wants: it never needed the list, and building one for it was the
        last O(everything known) work in a tick."""
        return self._kept()["sit"]

    def _state(self) -> List[Entry]:
        """The kept state as a list, newest-first. See `_kept`.

        ⚠ The list is the Situation's own and is rebuilt only when the state
        changes, so a caller that sorted it in place would be sorting the
        state. Every caller iterates.
        """
        return self._kept()["sit"].entries

    def _retire(self, cache: dict, k) -> None:
        """Drop a cached application and every index that points at it.

        Two callers, and they retire for different reasons: a later entry made
        what the application consumed no longer current, or a structural
        relation it negates has grown. One removal either way -- the indexes do
        not care why, and having two copies of this list is how one of them ends
        up missing an index.
        """
        app = cache["apps"].pop(k, None)
        if app is None:
            return
        cache["live"].discard(k)
        cache["quiet"].pop(k, None)
        cache["by_rule"].get(k[0], set()).discard(k)
        # The heap keeps its entry: removing from the middle of one is what a
        # lazy check at the top is for, and `apps` is the authority on whether a
        # candidate still exists.
        for w in self._wants(app):
            cache["by_want"].get(w, set()).discard(k)
        for c in app.consumed:
            cache["by_prop"].get(c.proposition, set()).discard(k)

    def _applications(
        self, proposed: List[Rule], state: Situation, materialise: bool = False
    ) -> List[Application]:
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
            cache = {"pos": 0, "apps": {}, "rule_pos": {}, "by_prop": {},
                     "quiet": {}, "quiet_by_prop": {},
                     # The candidate set, maintained incrementally. `live` is
                     # every application not KNOWN to be a no-op; `by_rule` is
                     # what `defeat` needs and `live` cannot give it.
                     "live": set(), "by_rule": {},
                     # ...and the two indexes the chooser needs so that a tick
                     # is not linear in the candidate set. `bucket` is a heap
                     # per rule, ordered by the STABLE stamp measured equivalent
                     # to the recomputed state position; `by_want` is what
                     # `_forgo` reads instead of scanning every candidate.
                     "bucket": {}, "by_want": {}, "seq": 0}
            self._match_cache = {fk: cache}  # one seat at a time; forking is a miss
        # `_would_change` reads the same cache, and gets there by this reference
        # rather than by recomputing `fk`: the two must agree about which seat
        # they are talking about, and one of them owning the key is how.
        self._verdicts = cache

        here = len(self.focus.seat.delta)
        delta = self.focus.seat.delta[cache["pos"]:]
        cache["pos"] = here

        # 0. Structure derived since the last look. It sits in no delta, so the
        # incremental path cannot see it: a rule reading a structural relation
        # that has grown must be matched in FULL again, which is what dropping
        # its cursor asks for.
        if self._structure_touched:
            grown = self._structure_touched
            self._structure_touched = set()
            for r in self.rules.rules:
                if any(self.g.relation_of(mm.pattern) in grown
                       for mm in r.antecedent):
                    cache["rule_pos"].pop(r.node, None)
                    # ⚠⚠⚠ **...and its cached applications with it, because a
                    # full re-match can only ADD.** Dropping the cursor asks for
                    # the rule to be matched again, and step 2's merge skips any
                    # key already present -- so a re-match that NO LONGER yields
                    # an application cannot remove it. That is invisible for a
                    # positive member, whose application would merely be
                    # rediscovered, and wrong for a NEGATED structural one:
                    # negation as failure is evaluated at match time, so when the
                    # relation it negates grows, the stale application survives
                    # and applies.
                    #
                    # Step 1 retires an application when a later ENTRY unsettles
                    # what it consumed. A structural fact has no entry and sits
                    # in no delta, so that path never sees it -- which is why the
                    # invalidation was present, correct, and unable to help.
                    # Measured: docs/observations.md §3.1.
                    for k in [k for k in cache["apps"] if k[0] == r.node]:
                        self._retire(cache, k)

        # 1. Retire what a later claim unsettled.
        if delta:
            suspect: set = set()
            for e in delta:
                suspect |= cache["by_prop"].get(e.proposition, set())
                # ...and the same move for the QUIESCENCE verdict, which is a
                # read of exactly the propositions the application would write.
                # A verdict can only change if one of those does, so a fresh
                # entry about one retires it and nothing else has to.
                for k in cache["quiet_by_prop"].pop(e.proposition, ()):
                    if cache["quiet"].pop(k, None) is not None and k in cache["apps"]:
                        self._revive(cache, k)  # back in the running, and on the heap
                rel = self.g.relation_of(e.proposition)
                if rel is self.FORBIDDEN or rel is self.REFUSED:
                    # A norm is not indexed by what it forbids -- `_forbid`
                    # consults every prohibition whose pattern shares a relation
                    # with what is about to be written, so a new one can change
                    # the answer for a proposition no cached verdict mentions.
                    # Blunt on purpose: norms are authored and refusals are rare,
                    # and a precise index here would have to reproduce `_forbid`'s
                    # matching, which is the re-implementation trap `state`
                    # already paid for once.
                    cache["quiet"].clear()
                    cache["quiet_by_prop"].clear()
                    cache["live"] = set()
                    cache["bucket"] = {}
                    for k in cache["apps"]:
                        self._revive(cache, k)
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
                    self._retire(cache, k)

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
                    self.g, self.chain, r, self.focus.topic, self.focus.seat, state,
                    computes=self.rules.computes,
                    structural=self.rules.skeleton(),
                )
            elif start < here:
                if start not in deltas:
                    deltas[start] = Situation(self.g, [
                        e for e in self.focus.seat.delta[start:here]
                        if e.source not in hidden
                    ])
                found = match(
                    self.g, self.chain, r, self.focus.topic, self.focus.seat, state,
                    fresh=deltas[start], computes=self.rules.computes,
                    structural=self.rules.skeleton(),
                )
            else:
                continue
            self.matched += len(found)
            for a in found:
                k = (r.node, frozenset(a.bindings.items()))
                if k in cache["apps"]:
                    continue
                cache["apps"][k] = a
                cache["live"].add(k)
                cache["by_rule"].setdefault(r.node, set()).add(k)
                # The stamp, assigned once and never recomputed: an entry's node
                # is minted from a monotonic counter at deposit, so descending
                # node order IS most-recently-claimed-first. Measured equivalent
                # to the recomputed state position over 2,452 ticks, against an
                # inverted control that disagreed about 686 moves.
                #
                # `seq` only breaks ties the stamp cannot have -- two candidates
                # of one rule with the same consumed entries are the same
                # candidate -- and exists so the heap never compares a `key`,
                # which holds a frozenset and is not orderable.
                cache["seq"] += 1
                heapq.heappush(
                    cache["bucket"].setdefault(r.node, []),
                    (tuple(-c.node for c in a.consumed), _stamp(a), cache["seq"], k),
                )
                for w in self._wants(a):
                    cache["by_want"].setdefault(w, set()).add(k)
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
        rank = {r.node: i for i, r in enumerate(proposed)}
        live = set(rank)
        # ⚠ Which `defeat` reads, and which is O(rules) rather than O(candidates)
        # -- so it is built whether or not the list is.
        self._matched_rules = {
            node: proposed[rank[node]]
            for node, ks in cache["by_rule"].items()
            if ks and node in live
        }
        if not materialise:
            # The list, its `order` index and its sort were the last O(state)
            # work left in a tick that no longer reads any of them: `_choose`
            # walks the heaps. Building it anyway was pure ceremony, and pure
            # ceremony repeated once per tick is another factor of n.
            return []
        order = {e.node: i for i, e in enumerate(state.entries)}
        last = len(order)
        # ⭐⭐⭐ **Only what could still have something to do.** This used to walk
        # every application ever found, on every tick, and hand them all to five
        # O(candidates) passes -- which is where the quadratic was, and why
        # remembering each application's VERDICT bought a constant factor and
        # left the exponent alone: caching a verdict removes the cost per
        # candidate, not the candidate.
        #
        # `live` is maintained where the facts change rather than recomputed:
        # an application joins it when it is found, leaves when `_would_change`
        # records that it is a no-op, and rejoins when the entry that made it one
        # is superseded. So a tick costs O(new + revived), not O(everything).
        # ⚠ ...except when the rule set uses `supersedes`, which compares
        # CONSUMED ENTRIES between two applications and therefore cannot be
        # answered from a list one of them may be missing from. Then the whole
        # set goes through, at the old cost. Stated rather than hidden, and
        # measured by a check either way.
        keys = (cache["apps"] if self.rules.precedence(self.SUPERSEDES)
                else cache["live"])
        out = [cache["apps"][k] for k in keys if k[0] in live]
        out.sort(key=lambda a: (rank[a.rule.node],
                                tuple(order.get(c.node, last) for c in a.consumed)))
        # ⚠⚠⚠ **What `defeat` must NOT be given is this list**, and that is the
        # whole difficulty of the change. `rules.defeat` runs before quiescence
        # on purpose -- *defeat is about whose antecedent holds, not about who
        # still has work to do* -- so a rule whose conclusion is already written
        # must go on defeating its rival, or the boss's rule is obeyed once and
        # the vice's quietly overwrites it on the next tick. Withholding the
        # quiet applications from the candidate list is right; withholding them
        # from defeat is that bug.
        #
        # So the rules that MATCHED are carried separately, which is all
        # `_defeated` reads, and maintaining it costs a set per rule.
        return out

    def _materialise(self, proposed: List[Rule], state: Situation) -> List[Application]:
        """The candidate list as `tick` used to build it: every live application,
        defeated and filtered, in the order arbitration read them.

        Nothing in the loop calls this. It exists because `_choose` is an
        optimisation of a semantics, and §20's floor gate is the standing answer
        to that: the slow definition has to stay, so the fast one can be held to
        it rather than trusted. `ugm.arbitration` runs both on every tick of
        every fixture and compares the move.
        """
        out = self._applications(proposed, state, materialise=True)
        out = defeat(self.rules, out, self._matched_rules.values())
        out = [a for a in out if not self._passed_up(a)]
        out = [a for a in out if self._would_change(a)]
        # ⚠⚠⚠ **Sorted, because `arbitrate` picks the FIRST among applications of
        # one rule and until now nothing said which that was.** The heap orders
        # by consumed entries and then by insertion; this list was in match
        # order; and the two agreed only because two applications of one rule
        # could not previously share their consumed entries. A structural member
        # binds without consuming (§12), so they can -- and `ugm.arbitration`
        # reported the divergence the hour it became possible.
        #
        # §10's rule, one level up: *a deterministic computation whose result
        # depends on an undeclared enumeration order has a tie-break nobody
        # authored*. Node identity is the stamp everywhere else here, so it is
        # the stamp here.
        return sorted(out, key=_order_key)

    @staticmethod
    def _binding_stamp(app) -> tuple:
        """A path-independent order for applications that CONSUMED THE SAME ENTRIES.

        ⚠⚠⚠ Until structural members existed this could not arise: every
        antecedent member was an entry, so two applications of one rule that
        consumed the same entries were the same application. A structural member
        binds without consuming (§12 -- it claims nothing, so there is nothing
        to have read), so `sanc(?m, ?up)` yields one application per ancestor,
        all with identical `consumed`.

        The heap then fell through to insertion order, which the fast and slow
        paths discover differently -- and `ugm.arbitration` reported 20
        disagreements about the move, all of one rule, all `fast=reach
        slow=reach`. That is §10's recorded trap exactly: *a deterministic
        computation whose result depends on an undeclared enumeration order has
        a tie-break nobody authored.*

        Node identity is the stamp everywhere else here, so it is the stamp
        here: sorted, so it cannot depend on which order the walk found them.
        """
        return tuple(sorted(v for v in app.bindings.values() if isinstance(v, int)))

    def _revive(self, cache: dict, k) -> None:
        """Put a candidate back in the running, and back on its rule's heap.

        The two have to happen together. `live` says whether a candidate counts;
        the heap is how the chooser reaches it. Adding to the first without the
        second is a candidate the agent believes it has and never looks at --
        which is a silent unsoundness rather than a slow path, because a rule
        would stop being applied with nothing anywhere saying so.
        """
        if k in cache["live"]:
            return
        app = cache["apps"][k]
        cache["live"].add(k)
        cache["seq"] += 1
        heapq.heappush(
            cache["bucket"].setdefault(k[0], []),
            (tuple(-c.node for c in app.consumed), _stamp(app), cache["seq"], k),
        )

    def _instantiation(self, app: Application) -> tuple:
        """What a rule application IS, for the purpose of firing once.

        The rule and **the entries it consumed** -- not its bindings. That
        distinction is the whole difference between this and the dedup `_enter`
        deleted, which keyed on the assumption alone and made a hypothesis
        unfinishable: *explore `broken(pipe)` […] then be told `wet(pipe)`, and
        the hypothesis is never revisited*.

        Being told something new deposits a new ENTRY, so an application that
        consumes it is a different instantiation and runs on its own. An
        application whose premises have not moved is the same one, and repeating
        it derives nothing the first did not.

        The bindings are in the key as well, and leaving them out cost 12 checks
        before it cost anything else. A structural or computed member **consumes
        no entry** -- `match` drops its slot -- so a stratum-0 rule's consumed
        tuple is empty for *every* binding, and keying on premises alone made
        such a rule fire once in its life. That took out the recursion over
        spans, hypothesis explanation and norm retirement together. Premises say
        *what the world showed*; bindings say *which case this is*, and firing
        once means once per case.
        """
        return (app.rule.node,
                tuple(sorted(e.node for e in app.consumed)),
                frozenset(app.bindings.items()))

    def _spend(self, app: Application, wrote: Tuple[Entry, ...]) -> None:
        """Mark an instantiation spent, and put it on the record.

        Refraction, in the sense OPS5 gave the word: an instantiation fires once
        for a given set of premises. What is new here is not the mechanism but
        that it is **sayable** -- `spent(<R>, premises(...))` is deposited, so
        the agent can be asked which of its rules have already run on what, and
        a corpus can reason about it. Chemistry that leaves a note.

        Measured need: `<grant>` applied 4 times in 8 ticks on one unchanging
        premise, and a foreign corpus, the dungeon and this document's own
        interpreter each hand-built a different substitute (`may(x, r)`, a round
        counter, a grant placed at an earlier locus).
        """
        key = self._instantiation(app)
        if key in self._spent:
            return
        # A refused write never happened -- §19 runs the veto *before* the
        # deposit, so "a forbidden entry never exists, not even briefly". An
        # instantiation fires once when it fires; being turned away at the gate
        # is not firing, and marking it spent would make refusal permanent.
        # That is the property measured earlier in this session and nearly lost
        # here: withdraw the prohibition and the rule applies on its own, which
        # is `arbitration-is-scheduling`'s *a loser is deferred, not rejected*
        # holding at the gate as well as in the chooser.
        if wrote and all(
            self.g.relation_of(e.proposition) is self.gate.REFUSED for e in wrote
        ):
            return
        concluded = tuple(e.proposition for e in wrote if e.sign == PLUS)
        self._spent[key] = (app.rule.node, app.consumed, concluded, self.focus)
        # ...and RETIRE it, rather than leaving it in the candidate set to be
        # skipped. Measured: filtering it in `_survives` instead cost the two
        # optimisations this loop was built around -- `live` and `apps` came out
        # the same size, which that check's own comment calls the sign that
        # withholding "has silently stopped working", and weighing went back to
        # quadratic (60 facts: 1,950 candidates weighed; 120: 7,500). Returning
        # early from `_survives` skips `_would_change`, so no no-op verdict is
        # ever cached and every spent candidate is re-walked for ever. A spent
        # instantiation cannot fire again while its frame lives, so it does not
        # belong in the candidate set at all.
        # WITHHELD, not retired. Retiring it outright also removes it from
        # `by_rule`, which is what `defeat` reads to know which rules matched
        # here -- and `overrides` is per tick, so an overriding rule that had
        # fired once stopped counting as having matched and the defeat silently
        # lapsed. That cost 11 checks across `overrides`, `supersedes` and
        # `defeated`. The application stays on the record; it only leaves the
        # live set, which is the same treatment a no-op verdict gets.
        for cache in self._match_cache.values():
            cache["live"].discard((app.rule.node, frozenset(app.bindings.items())))
        for p in concluded:
            self._spent_by_prop.setdefault(p, set()).add(key)
        if app.consumed:
            self._note(self.g.rel(
                self.SPENT, app.rule.node,
                self.g.rel(self.PREMISES, *sorted(e.node for e in app.consumed))))

    def _contest(self, frame: Frame, e: Entry) -> None:
        """The price of refraction, paid rather than accepted.

        Firing once turns a loud contradiction into a silent one. `<grant>`'s
        runaway was not a rule misbehaving: `implies` says *whenever A, B*, and
        the corpus asserted `-B` while `A` still held. The 194 acts were the
        engine believing both. Refraction stops the symptom and leaves the
        contradiction in place -- which is the one failure mode this design is
        least willing to buy, and §8 already names it as unowned: *is this moment
        consistent? is a query somebody must run, and the design does not say
        who.*

        So this is who, for exactly the case refraction creates: a spent
        instantiation's conclusion is denied **while its premises still stand**.
        That is the loop, caught at the moment it would have started, and
        deposited as `contested(<R>, <what>)` for a corpus to answer.

        Cheap because it is indexed by the proposition being written, like
        `_forbid`: a denial about something no spent rule concluded costs one
        dict lookup.
        """
        if e.sign != MINUS:
            return
        for key in list(self._spent_by_prop.get(e.proposition, ())):
            rule_node, consumed, _, _f = self._spent[key]
            if not all(
                self.chain.resolve(c.proposition, frame.topic, frame.seat) is c
                for c in consumed
            ):
                continue  # the premises moved: the rule may run again on its own
            self._note(self.g.rel(self.CONTESTED, rule_node, e.proposition),
                       licence=self.g.rel(self.APPLIED, rule_node))

    def _forget_spent(self, frame: Frame) -> None:
        """A frame's refraction ends with the frame.

        `_match_cache` is already per-seat, and says why: *the cache belongs to
        a seat, because a `Situation` does. Supposing forks.* Refraction is the
        same kind of state and needs the same scope -- an instantiation spent
        inside a hypothesis must not stay spent outside it, or **supposing
        changes what the agent believes**, which is the one thing supposing may
        not do (`_adopt`'s argument, and `_dispatch`'s).

        Found by measurement rather than foresight: leaving it global broke the
        modality pipeline, hypothesis explanation and structural containment on
        a forking chain -- every one of them a check about supposing.
        """
        gone = [k for k, v in self._spent.items() if v[3] is frame]
        for k in gone:
            _, _, concluded, _ = self._spent.pop(k)
            for p in concluded:
                bucket = self._spent_by_prop.get(p)
                if bucket is not None:
                    bucket.discard(k)

    def _markers(self, rule) -> Tuple[NodeId, ...]:
        """The `new(...)` terms in a rule's consequent, cached on the rule node.

        Scanned rather than declared, so a corpus writes `new(person)` where it
        wants one and nothing else changes. Cached because the answer depends
        only on the rule, and `_apply` asks on every firing.
        """
        got = self._marker_cache.get(rule.node)
        if got is None:
            found: List[NodeId] = []

            def walk(n: NodeId) -> None:
                if self.g.relation_of(n) is self.NEW:
                    if n not in found:
                        found.append(n)
                    return
                for mm in self.g.members(n):
                    walk(mm)

            for m in rule.consequent:
                walk(m.pattern)
            got = tuple(found)
            self._marker_cache[rule.node] = got
        return got

    def _survives(self, app: Application) -> bool:
        """The three per-candidate filters, in `tick`'s order. Defeat is not
        here: it is per RULE, and the chooser applies it once per rule rather
        than once per candidate."""
        # Spent is checked LAST, and the order is the whole of it. Checked first,
        # it returns before `_would_change` runs -- so no no-op verdict is ever
        # cached, the candidate is revived on every change it reads, and weighing
        # goes back to quadratic (measured: 60 facts weighed 1,950 candidates,
        # 120 weighed 7,500). Running the verdict first keeps the withholding
        # machinery intact and lets refraction filter what survives it.
        if self._passed_up(app) or not self._would_change(app):
            return False
        return self._instantiation(app) not in self._spent

    def _choose(self, proposed: List[Rule], keys: set):
        """Pick the move without materialising the option set.

        ⭐⭐⭐ **The quadratic was never the cost of a candidate; it was the cost of
        looking at all of them.** With n independent applicable rules and §18's
        one move per tick, the loop weighed n, then n−1, then n−2 -- and
        `weigh` measured that 99.6% of those candidates genuinely applied, so
        there was nothing left to withhold. What is left is to stop *looking*.

        Three facts make that possible, and each was measured before it was used:

        * **The arbitration key is per RULE.** `rules.arbitrate`'s key is
          `(score(rule), rules.index(rule))` and contains nothing about the
          application, so there are |rules| priorities and not n.
        * **The within-rule order is a stable stamp.** An entry's node is minted
          from a monotonic counter, so descending node order reproduces
          most-recently-claimed-first exactly -- 0 disagreements over 2,452
          ticks, against a control that disagreed about 686 moves.
        * **Nothing needs the whole list.** `_note_doubt` reads the rivals'
          RULES, which the rule order gives in rank order; `_forgo` reads the
          candidates that share a want, which is an index.

        So: rules in rank order, each rule's candidates in stamp order, validate
        at the top and step to the next on rejection. Returns the chosen
        application and the two collections `tick` still owes the record.

        ⚠ Laziness is only sound because rejection is *sticky*. A candidate that
        fails `_would_change` is withheld until something it reads changes, so
        walking past it is paid once and not once per tick. A candidate that
        fails `_passed_up` is not withheld -- `forgone` can be denied -- so that
        one is re-walked, which is a cost this does not hide.
        """
        cache = self._verdicts
        if self.rules.precedence(self.SUPERSEDES):
            # ⚠ `supersedes` is defeat **for this case**, decided by whether two
            # applications share a consumed entry -- a question about a PAIR of
            # candidates, which nothing at the top of a heap can answer. So a
            # rule set that uses it gets the list, and the old cost. Stated
            # rather than hidden, and gated by a check either way: the fast path
            # is for corpora that do not order two rules for the same case.
            state = Situation(self.g, self._state())
            everything = self._materialise(proposed, state)
            rank = lambda r: self._rank(r, keys)
            self.considered += len(everything)
            picked = arbitrate(self.rules, everything, rank)
            if picked is None:
                return None, [], []
            return picked, everything, everything
        rank_of = {r.node: i for i, r in enumerate(self.rules.rules)}
        live_rules = {r.node: r for r in proposed}
        # `defeat` reads the rules that MATCHED, which is every rule holding a
        # candidate -- including ones whose candidates are all no-ops. That is
        # the split `weigh` made, and it is the reason this can be lazy at all.
        matched = [
            live_rules[n] for n, ks in cache["by_rule"].items()
            if ks and n in live_rules
        ]
        undefeated = [r for r in matched if not _defeated(self.rules, r, matched)]
        if not undefeated:
            # The cycle fallback (§14): arbitration stays total, so nobody is
            # defeated rather than everybody.
            undefeated = matched
        order = sorted(undefeated, key=lambda r: (self._rank(r, keys), rank_of[r.node]))

        def candidates(rule: Rule) -> Iterable[Application]:
            """This rule's live candidates, newest-claimed first, lazily."""
            heap = cache["bucket"].get(rule.node)
            if not heap:
                return
            # ⚠⚠⚠ **A heap that keeps its dead is walked past them every tick.**
            # The first version re-pushed the withheld candidates so they would
            # keep their place -- and measured 721,800 heappops over 1,202
            # ticks, because every tick popped the whole accumulated no-op
            # prefix and put it straight back. That is the quadratic the heap
            # was built to remove, wearing a heap's clothes.
            #
            # So the heap holds only what is LIVE, and revival pushes back
            # (`_revive`). Popping a withheld candidate drops it for good, which
            # is safe precisely because being withheld is not permanent and the
            # invalidation pass is what says so.
            kept = []
            try:
                while heap:
                    item = heapq.heappop(heap)
                    # ⚠ The LAST field, not a counted one. This read `item[2]`
                    # and a field was inserted before it -- silently, since the
                    # heap still popped, just the wrong element of the tuple.
                    k = item[-1]
                    if k not in cache["apps"] or k not in cache["live"]:
                        continue
                    # ⚠⚠⚠ **Kept BEFORE the yield, not after.** The consumer
                    # breaks out of this loop the moment it has its move, which
                    # closes the generator and raises `GeneratorExit` *at* the
                    # yield -- so anything after it never runs, and the chosen
                    # candidate was silently dropped from its heap. It then
                    # stopped existing for every later tick: 29 checks failed,
                    # none of them about heaps.
                    kept.append(item)
                    yield cache["apps"][k]
                    if k not in cache["live"]:
                        # `_would_change` withheld it while we were looking at
                        # it. Then it does not go back, and `_revive` is what
                        # returns it if the entry it read is superseded.
                        kept.pop()
            finally:
                for item in kept:
                    heapq.heappush(heap, item)

        chosen = None
        best = None
        rivals: List[Application] = []
        for rule in order:
            here = self._rank(rule, keys)
            if chosen is not None and not self._close(here, best):
                break  # past the point where anything could still be doubt
            for app in candidates(rule):
                self.considered += 1
                if not self._survives(app):
                    continue
                if chosen is None:
                    chosen, best = app, here
                    if here[0] == 0:
                        # A tie among `standing` rules is not doubt, so nothing
                        # after this is worth walking for.
                        return chosen, [], self._sharing(chosen)
                else:
                    rivals.append(app)
                break
        if chosen is None:
            return None, [], []
        return chosen, rivals, self._sharing(chosen)

    def _sharing(self, chosen: Application) -> List[Application]:
        """The candidates `_forgo` has to consider: those serving a goal the
        chosen application also serves. Read off `by_want` rather than by
        scanning, which is what keeps a tick off the whole candidate set.

        Empty when the chosen application serves no goal at all, which is
        `_forgo`'s own first line and the common case."""
        cache = self._verdicts
        wants = self._wants(chosen)
        if not wants:
            return []
        out, seen = [], set()
        for w in wants:
            for k in cache["by_want"].get(w, ()):
                if k in seen or k not in cache["apps"] or k not in cache["live"]:
                    continue
                seen.add(k)
                app = cache["apps"][k]
                if app.rule is not chosen.rule and self._survives(app):
                    out.append(app)
        return out

    def _would_change(self, app: Application) -> bool:
        """Quiescence: an application that restates what the chain already says is
        not a step. Without this the loop would reapply every rule forever, and
        *nothing left to do* would be unsayable.

        ⭐⭐⭐ **And it was the agent recomputing its entire option set on every
        move.** Profiled at 38% of runtime, ~800 calls a tick; measured before
        this was built, on a chain of `edge` facts:

        | facts | ticks | calls | re-tests returning the SAME answer |
        |---|---|---|---|
        | 200 | 202 | 40,400 | 99.0% |
        | 500 | 502 | 251,000 | 99.6% |
        | 1,000 | 1,002 | 1,002,000 | **99.8%** |

        Third instance of one observation -- `delta` found 98.7% of matching was
        re-derivation, `state` found the walk was rebuilding what a delta could
        extend, and this is *nothing remembers that this question was already
        answered*. The answer is kept beside the applications, in the same cache
        and retired by the same discipline, because it is the same kind of claim.

        ⚠ **What the measurement corrected.** The cost was assumed to be the
        chain walk; it is the smallest of the three parts. At 1,000 facts:
        `_forbid` 5.31s, `substitute` 3.94s, `resolve` 1.10s. A cache is the
        right fix anyway -- it skips all three -- but *optimise the walk* would
        have bought the least of them.

        **What the verdict depends on**, which is what makes it cacheable: the
        resolves of the propositions this application would write, plus the
        prohibitions consulted about them. Nothing else. So a fresh entry about
        one of those retires it (`quiet_by_prop`), a fresh `forbidden` or
        `refused` flushes the lot, and a fork misses because the cache belongs to
        a seat. ⚠ This is not a *seen it* set for the same reason `_applications`
        is not: `resolve` is non-monotone, so quiescence has to keep being able
        to change its mind.
        """
        # ⚠⚠⚠ **A stratum-0 verdict is never cached, and finding out why took a
        # runaway.** The cache retires a verdict when a proposition it READ
        # changes (`quiet_by_prop`); a stratum-0 rule reads no proposition, so
        # `touched` is empty and a `True` cached on the first tick is never
        # retired by anything. The same application then applies for ever --
        # measured at 60 ticks of `applied`, identical bindings, on a rule that
        # had already drawn its conclusion.
        #
        # ⭐ It costs nothing to skip the cache here: the verdict is a
        # substitution and a count, where the ordinary one is a resolve per
        # conclusion plus the prohibitions consulted about it.
        if self.rules.is_stratum0(app.rule):
            return self._decide_change(app, [])

        cache = self._verdicts
        key = None
        if cache is not None:
            key = (app.rule.node, frozenset(app.bindings.items()))
            hit = cache["quiet"].get(key)
            if hit is not None:
                return hit
        # Every proposition this verdict was READ from, so the index can retire
        # it. Collected as the answer is computed rather than derived afterwards,
        # because the second would be a re-implementation of this method and
        # `state` records what that costs.
        touched: List[NodeId] = []
        answer = self._decide_change(app, touched)
        if key is not None:
            cache["quiet"][key] = answer
            if not answer:
                # Out of the running until something it reads changes. This is
                # the line that moves the exponent; the caching above only made
                # each re-test cheap.
                cache["live"].discard(key)
            for p in touched:
                cache["quiet_by_prop"].setdefault(p, set()).add(key)
        return answer

    def _decide_change(self, app: Application, touched: List[NodeId]) -> bool:
        # ⚠⚠⚠ **A stratum-0 rule is asked about the GRAPH, not the state.** Its
        # conclusion is structure, so it never enters the chain, so `resolve`
        # below answers `None` for it forever and quiescence says *yes, this
        # changes something* on every tick. Measured before fixing: a corpus rule
        # reading the raw chain ran 40 ticks of `applied` and never once went
        # quiet. The rule was right, the conclusion was right, and the loop could
        # not tell it had already drawn it.
        #
        # ⭐ Monotone, which is why this is sound to cache with no index: a
        # skeleton fact cannot be denied, so once minting it adds nothing, that
        # stays true. `resolve` is non-monotone and needs `quiet_by_prop`; this
        # does not.
        # ⚠⚠⚠ And it asks WITHOUT BUILDING, which is the interning trap's fourth
        # appearance and the only one that was a semantic defect rather than
        # bookkeeping. `substitute` interns, so a verdict computed with it makes
        # the conclusion exist -- and the next caller is told there is nothing to
        # do. `ugm.arbitration` runs the fast path and the slow one over the same
        # state, and reported the fast path choosing a move the slow path found
        # nothing for: **one path's question consumed the other's answer.**
        # `already_there` is the same walk with no minting in it.
        if self.rules.is_stratum0(app.rule):
            for m in app.rule.consequent:
                got = already_there(self.g, m.pattern, app.bindings)
                if got is GENERIC:
                    continue  # mints nothing, so changes nothing
                if got is None:
                    return True  # ground and not yet derived
            return False

        for m in app.rule.consequent:
            grounded = substitute(self.g, m.pattern, app.bindings)
            if self.g.has_var(grounded) and not self._is_mention(app):
                # Genuinely generic: the rule's consequent names something its
                # antecedent never bound, and there is nothing to deposit. A
                # conclusion that contains variables because it is ABOUT a rule
                # is a different case entirely, and dropping it here is how a
                # rule reasoning about rules used to look exactly like a rule
                # with nothing to do -- silently, and only at this line.
                #
                # `touched` stays empty, deliberately: this verdict is a property
                # of the rule and its bindings, so nothing can ever change it and
                # it is cached with no index at all.
                return False
            touched.append(grounded)
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
                touched.append(record)
                if self.chain.resolve(record, self.focus.topic, self.focus.seat) is None:
                    return True
                continue
            # ⚠⚠⚠ **At the consequent's OWN locus, and this is the same defect
            # as the write's twice over.** Quiescence asked whether the
            # proposition already holds at the frame's TOPIC -- so a rule
            # concluding `+taking_turns(?a, ?b) at ?s` was told *nothing to do*
            # the moment any span had it, and §13's recursion produced its first
            # recognition and stopped. Fixing the write alone was not enough:
            # the loop never reached the write, because the verdict was computed
            # about a different locus than the one the conclusion would land at.
            at = self._conclude_at(m, app.bindings, strict=False)
            cur = self.chain.resolve(
                grounded, self.focus.topic if at is None else at, self.focus.seat
            )
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

    def web(self, rules=None) -> Tuple[dict, dict]:
        """For each relation name: how often it is READ (an antecedent member)
        and WRITTEN (a consequent member, or a fact deposited).

        ⭐⭐⭐ **Meaning in an open class is given by the web.** A name nothing
        ever draws a conclusion from, or nothing ever establishes, means nothing
        -- so a corpus containing one is silently smaller than it looks. This is
        the price of §2's open class paying for its own detection: nothing else
        in the engine could tell a proposition awaiting its meaning from a typo.

        Here rather than in an instrument because the loader warns with it and
        `ugm.vocabulary` maps with it, and a second implementation of a thing
        that indexes what it re-implements is what `state` paid for once.

        ⚠⚠⚠ **A VARIABLE in relation position is not a name, and reporting one
        was this instrument's own bug.** `+?kind(?item)` applies a class held in
        a variable (§4's *a class as data*), and `relation_of` answers with the
        variable node, which `show` prints as `?kind`. So a corpus using the
        feature was told nothing writes a relation it never named -- the rule
        derives correctly and the checker called it a defect. Found by sweeping
        the 239 machines the suite builds, which is the only way it could have
        been: the corpus that uses it is inline in a Python fixture, where none
        of this tooling reaches. **The bare variable, distorting a measurement
        for the fourth time.**
        """
        read: dict = {}
        written: dict = {}

        def name(node):
            rel = self.g.relation_of(node)
            if rel is None or self.g.is_var(rel):
                return None
            return self.g.show(rel)

        for r in (self.rules.rules if rules is None else rules):
            for x in r.antecedent:
                got = name(x.pattern)
                if got is not None:
                    read[got] = read.get(got, 0) + 1
            for x in r.consequent:
                got = name(x.pattern)
                if got is not None:
                    written[got] = written.get(got, 0) + 1
        for mo in self.chain.moments:
            for e in mo.delta:
                got = name(e.proposition)
                if got is not None:
                    written[got] = written.get(got, 0) + 1
        return read, written

    def unwebbed(self, rules=None) -> List[str]:
        """Names some rule READS that nothing anywhere writes.

        ⚠ **The engine's own names are excluded, because the MACHINERY supplies
        them**: the bundle reads `arrived`, `emitted`, `taken` and `quiet` and
        writes none of them, correctly. Without this the bundle reports 11.

        ⚠⚠ **Only this direction is a signal, and it was measured rather than
        assumed.** *Written and never read* reports 11 to 17 names on healthy
        corpora -- the machinery's bookkeeping, plus a corpus's own OUTPUTS,
        since nobody reads an answer. That is `ugm.harmony`'s false-positive
        shape arriving again. This direction reports **zero** on every corpus
        here, and one on a corpus with a typo in it.
        """
        read, written = self.web(rules)
        return sorted(n for n in read
                      if not written.get(n) and n not in self.reserved)

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
                                "sign": self.g.show(sign)})
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
                        item["sign"],
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
        if e.source is not None:
            bits.append(f"via {self.g.show(e.source)}")
        if e.licence is not None:
            bits.append(f"licensed by {self.g.show(e.licence)}")
        return ", ".join(bits)


# -- inducing a tree from several episodes ---------------------------------


def _order_key(app) -> tuple:
    """The one total order over an application, used by both paths (§21)."""
    return (tuple(-c.node for c in app.consumed),
            tuple(sorted(v for v in app.bindings.values() if isinstance(v, int))))


def _stamp(app) -> tuple:
    return _order_key(app)[1]


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

        ⭐⭐⭐ **How sure is a WRAPPER, not a field**, and this was the argument
        that eventually deleted grades outright. §21's item 5 was that a grade
        is a Python field on the entry, so no rule can read one -- a confidence
        unreadable by the very rules that would act on it. A wrapper is an ordinary node: `_priority` does not count it
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
