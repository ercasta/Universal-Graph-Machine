"""The interpreter (§14, §16).

Recall proposes. Match filters. Arbitrate commits. Only the last is total. The
step is *select a rule, apply it*, and object-rules and meta-rules must be
indistinguishable to it -- a flat tower, not a stacked one.

See docs/design/machine.md.
"""

from .. import corpora as _corpora
import inspect
import heapq
from typing import Dict, List, NamedTuple, Optional, Tuple

from .chain import MINUS, PLUS, Chain, Entry
from .channels import Arrival, Channels
from .gate import Gate
from .graph import Graph, NodeId
from .rules import (
    _defeaters,
    already_there,
    ABSENT,
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
    fn: object  # fn(machine, entry) -> NodeId | None


#: How many things may be attended at once. A knob, so `attention_span(3)` in a
#: corpus narrows it -- and a narrower span is a STEEPER gradient over fewer
#: things, which is what *concentrating* would mean here.
ATTENTION_SPAN = 7

#: How deep the attention stack may go. A backstop against a corpus that pushes
#: its way down for ever on ever-changing nodes, which the cycle test cannot see
#: -- the nodes are different every time. ⚠ Copied from `probes/experts.py`'s
#: `DEPTH`, and so is its caution: an earlier draft of that file returned to the
#: outer loop instead of servicing nested consultations in place, so the stack
#: was never deeper than one, the cycle test could never fire, and a check
#: asserting depth passed while the stack was flat.
FRAME_DEPTH = 8


class Frame:
    """One turn of attention: a queue, the EXPERT whose rules are in play, and
    that expert's table.

    ⭐⭐⭐ **The attention stack and the consultation stack are one construct,
    not two.** `push` is how one expert calls another and `pop` is how it gets
    the result back. A frame is not only a queue of nodes: it is everything a
    sub-line of work has that the line above it must not lose, and the table is
    in that list because `tick`'s own docstring says what losing it costs --
    *a caller stepping by hand would lose every buff between one tick and the
    next and be measuring a different agent each time*.

    ⚠⚠⚠ **The graph is untouched by push and pop.** This is not a transaction,
    there is no rollback, and nothing derived inside a frame stops existing when
    it is popped. Attention management is the whole of this. The one thing a pop
    does take back is the frame's own `attention` claims, and it DENIES them
    rather than dropping them -- `_unattend` scoped to a frame, for the reason
    `_unattend` gives.

    ⚠ The expert is held by NAME -- a node -- never as a frozen rule list, and
    `_expert_pool` is read on demand: `knows(?e, ?r)` can be CONCLUDED mid-run,
    `<inherit>` derives more of them, and a pool frozen at push time could not
    see one. The same finding as `pool_of` is *read, never kept*.
    """

    __slots__ = ("queue", "expert", "table", "on", "claimed")

    def __init__(self, expert: Optional[NodeId] = None, on=()) -> None:
        self.queue: List[Tuple[NodeId, int]] = []
        # None means *the rules of the frame below*: a push that discriminates
        # nothing suspends attention without changing whose rules are in play,
        # which is the pure attention-stack case and is worth having alone.
        self.expert = expert
        self.table = None
        self.on: Tuple[NodeId, ...] = tuple(on)
        # What this frame deposited `attention(...)` for, so a pop can deny
        # exactly what it claimed and nothing the frame below claimed.
        self.claimed: List[NodeId] = []


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
        # ⭐⭐⭐ The aggregate over bindings, and it is the GENERAL case of
        # rooted, unsupported and blocked rather than a fourth of them. ⚠ NOT
        # in reserved, deliberately.
        # → docs/design/machine.md#the-aggregate-over-bindings-and-it-is-the
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
        # A separate relation rather than a denied binds, deliberately.
        # → docs/design/machine.md#not-that-one-what-a-plan-has-tried-and-rule
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
        # The other silent decline (§5).
        # → docs/design/machine.md#the-other-silent-decline-5-the-loop-running
        self.QUIET = self.g.atom("quiet")
        # The other way to be over, and the design had only one (§19). Running
        # out of work is EXHAUSTION; this is SATISFACTION -- *there is nothing
        # more worth doing about x*.
        # →
        # docs/design/machine.md#the-other-way-to-be-over-and-the-design-had-onl
        self.ENOUGH = self.g.atom("enough")
        # ...and the record that it happened. Same treatment as left, quiet,
        # arrived and emitted (§17): the machinery deposits the smallest
        # unarguable thing and says nothing about what it means.
        # → docs/design/machine.md#and-the-record-that-it-happened-same-treatme
        self.STOPPED = self.g.atom("stopped")
        # ...and what the machinery says instead, when it will not let a stop
        # stand. open(<w>) is a goal that was still outstanding at the moment
        # the agent tried to be done with everything.
        # → docs/design/machine.md#and-what-the-machinery-says-instead-when-it
        self.OPEN = self.g.atom("open")
        # What a finished episode has to say about the rules that ran in it:
        # `helped(<R>, <key>)`, deposited by the offline review. The smallest
        # unarguable record again -- *this rule was on the support of something
        # achieved* is a fact about the trail, where *so prefer it next time* is a
        # claim, and stays a rule.
        self.HELPED = self.g.atom("helped")
        # ...and its opposite, which only becomes sayable once a task is split.
        # → docs/design/machine.md#and-its-opposite-which-only-becomes-sayable
        self.HARMED = self.g.atom("harmed")
        # Forgoing: the thing arbitration was assumed to do and never did.
        # →
        # docs/design/machine.md#forgoing-the-thing-arbitration-was-assumed-to-d
        self.FORGONE = self.g.atom("forgone")
        # Tools. ⚠ THE one loaded node.
        # → docs/design/machine.md#tools-21-s-honest-debt-taken-a-request-answe
        self.LOADED = self.g.atom("loaded")
        self.SCOPED = self.g.atom("scoped")
        self.ANSWERS = self.g.atom("answers")
        self.ANSWERED = self.g.atom("answered")
        # ⭐⭐⭐ Re-asking. §6 recorded *a request can only be made once* and §21
        # carried it as one of the two original four hats still open.
        # → docs/design/machine.md#re-asking-6-recorded-a-request-can-only-b
        self.AGAIN = self.g.atom("again")
        # A callback: a pointer to a rule, hung on a node. `+resume(h, <R>)` says
        # *when h returns, R's turn has come* -- and `turn` is the strongest thing
        # it can say, because §5's wall stands: no rule may apply a rule.
        # A rule that ordinary recall does not propose. Dormancy is what makes a
        # pointer do any work -- with recall exhaustive, a callback rule would
        # apply whenever it happened to match and the pointer would be decoration.
        self.DORMANT = self.g.atom("dormant")
        # ...and the fact that wakes one. This is directed RECALL, not invocation:
        # a proposed rule still has to match, can still be defeated, and still
        # competes in arbitration. Nothing owns the loop (§18).
        self.DUE = self.g.atom("due")
        # Attention: what the agent is thinking about, said about a NODE. ⚠ And
        # it is safe by construction under the action palette: attention is a
        # FACT, so a learned rule that sets it can redirect what the agent
        # considers and can...
        # →
        # docs/design/machine.md#attention-what-the-agent-is-thinking-about-sai
        self.ATTENTION = self.g.atom("attention")
        # How many things may be attended at once -- a knob, so a corpus can say
        # it, the way `budget(3)` already is one. Shrinking it is forgetting
        # sooner; growing it is holding more in mind at a weaker gradient.
        self.SPAN = self.g.atom("attention_span")
        # How deep the attention stack may go, as a knob beside the span. The
        # two bound the same thing from opposite ends: the span says how much
        # one frame holds, the depth says how many frames there may be.
        self.DEPTH = self.g.atom("frame_depth")
        # ⭐⭐⭐ Which expert holds which rule, and which expert inherits which.
        # These are the SURFACE's names -- `expert geometry extends arithmetic`
        # writes them -- and they are reserved here because the engine now reads
        # them too: `push` picks an expert, and a name minted beside the loader's
        # table would be a second `knows` that never meets the corpus's. The
        # twin trap, and `reserved` is the standing answer to it.
        self.KNOWS = self.g.atom("knows")
        self.EXTENDS = self.g.atom("extends")
        # A frame was opened, and on what. `pushed(<expert>, <node>)` -- or
        # `pushed(<node>)` where nothing discriminated an expert.
        self.PUSHED = self.g.atom("pushed")
        # ...and closed, carrying one node back: `popped(<expert>, <node>)`.
        self.POPPED = self.g.atom("popped")
        # ⭐⭐⭐ **The pick AND the scores it beat**, in hundredths, as numerals a
        # rule can compare. An unarguable step cannot buy back vetoability; what
        # it must not lose is LEGIBILITY, and every other engine decision nobody
        # can override is deposited here -- `refused`, `unafforded`, `declined`.
        # On a life-or-death step the pick will be wrong eventually, and `why()`
        # should answer rather than shrug.
        self.SUITS = self.g.atom("suits")
        # §18's call stack, as facts -- the plumbing under a recursive plan,
        # and deliberately NOT a strategy for making one. ⚠ advances/closes are
        # DATA, not rules.
        # → docs/design/machine.md#18-s-call-stack-as-facts-the-plumbing-under
        self.AFFORDED = self.g.atom("afforded")
        # ...and asking for one. attempt(move(d1, z)) is the agent proposing to
        # act; the world model's own rules resolve it, or decline it. ⚠
        # Deposited, not VETOED.
        # → docs/design/machine.md#and-asking-for-one-attempt-move-d1-z-is
        self.ATTEMPT = self.g.atom("attempt")
        # ⚠ Distinct from `refused`, which is the GATE's: a write a norm
        # covered, arity 3, carrying the norm that forbade it. *You may not* and
        # *there is no such move* are different claims and conflating them would
        # lose both.
        self.DECLINED = self.g.atom("declined")
        # Why the machinery declined one. A corpus declining for its own reasons
        # says its own word here; this is the only one the engine ever uses.
        self.UNAFFORDED = self.g.atom("unafforded")
        # ...and the other one the apparatus gives: nothing resolved it, and the
        # loop ended. `<unattended>` in the bundle concludes it, so it has to be
        # RESERVED -- a bundle rule's argument atom is a twin waiting to happen
        # exactly as its relation is, and this one was: the rule fired, and a
        # corpus asking about `declined(?a, unattended)` built a second node
        # with the same name and saw nothing.
        self.UNATTENDED = self.g.atom("unattended")
        self.CALL = self.g.atom("call")
        self.STAGE = self.g.atom("stage")
        self.SPAWN = self.g.atom("spawn")
        self.AWAITS = self.g.atom("awaits")
        self.RETURNED = self.g.atom("returned")
        self.ADVANCES = self.g.atom("advances")
        self.CLOSES = self.g.atom("closes")
        # Numerals as shared nodes for the small ones, so a score written in a
        # corpus and a score written by a rule are the same node. Everything
        # that READS a numeral reads its name, so an unshared one still works --
        # but two nodes with one name is the trap this design has paid for four
        # times, and there is no reason to invite it.
        self.NUMERAL = {i: self.g.atom(str(i)) for i in range(10)}
        # The second carve-out, and it is the mirror of §19's first.
        # →
        # docs/design/machine.md#the-second-carve-out-and-it-is-the-mirror-of-1
        self.STANDING = self.g.atom("standing")
        # §19's carve-out.
        # → docs/design/machine.md#19-s-carve-out-forbidden-pattern-is-a-nor
        self.CLOSE = self.g.atom("close")
        # ⭐⭐ Three knobs, each a FACT rather than a Python field, because
        # *how careful am I being* is a claim with a trail and a rule can raise
        # it before an irreversible step: *how careful am I being is a claim with a trail, and a rule
        # can raise it before an irreversible step.* They were Python fields,
        # which made them the one kind of decision this design does not allow
        # -- one nobody can ask about or argue with.
        # → docs/design/machine.md#the-other-three-knobs-by-the-same-argument
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
        self.RECALL = self.g.atom("recall")
        self.RECALLED = self.g.atom("recalled")
        self.FORBIDDEN = self.g.atom("forbidden")
        # The world model's split (docs/world-model.md): a relation declared
        # `relationship(<rel>)` holds among things that have ids -- entities and
        # other relationships -- and never among denotations. A declaration,
        # like `forbidden`, so adding a relation adds a row.
        self.RELATIONSHIP = self.g.atom("relationship")
        self.REFUSED = self.gate.REFUSED

        # The knowledge base is a channel like any other (§13). Reading it
        # faithfully is guaranteed; what it *says* -- the rules -- stays as
        # contestable as anything else, which is what `by(R, boss)` depends on.
        self.KB = self.channels.open("kb")

        # The one register (§10): which node the machinery is currently
        # reasoning in. The frame itself is an ordinary node; only the pointer
        # is privileged.
        # → docs/design/machine.md#the-one-register-10-which-node-the-machinery

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
            "goal": self.GOAL,
            "achieved": self.ACHIEVED, "blocked": self.BLOCKED,
            "plan": self.PLAN, "subgoal": self.SUBGOAL,
            "binds": self.BINDS, "expands": self.EXPANDS,
            "doing": self.DOING, "did": self.DID,
            "expects": self.EXPECTS, "deviates": self.DEVIATES,
            "taken": self.TAKEN, "emitted": self.EMITTED,
            "quiet": self.QUIET,
            "enough": self.ENOUGH, "stopped": self.STOPPED, "open": self.OPEN,
            "helped": self.HELPED, "harmed": self.HARMED,
            "forgone": self.FORGONE, "exercised": self.EXERCISED,
            "root": self.ROOT, "rooted": self.ROOTED,
            "count": self.COUNT, "counted": self.COUNTED,
            "answers": self.ANSWERS, "answered": self.ANSWERED,
            "scoped": self.SCOPED, "loaded": self.LOADED,
            "again": self.AGAIN,
            "dormant": self.DORMANT, "due": self.DUE,
            "attention": self.ATTENTION,
            "attention_span": self.SPAN,
            "frame_depth": self.DEPTH,
            "knows": self.KNOWS, "extends": self.EXTENDS,
            "pushed": self.PUSHED, "popped": self.POPPED,
            "suits": self.SUITS,
            "afforded": self.AFFORDED, "attempt": self.ATTEMPT,
            "declined": self.DECLINED, "unafforded": self.UNAFFORDED,
            "unattended": self.UNATTENDED,
            "call": self.CALL, "stage": self.STAGE, "spawn": self.SPAWN,
            "awaits": self.AWAITS, "returned": self.RETURNED,
            "advances": self.ADVANCES, "closes": self.CLOSES,
            "forbidden": self.FORBIDDEN, "refused": self.REFUSED,
            "relationship": self.RELATIONSHIP,
            "standing": self.STANDING,
            "recall": self.RECALL, "recalled": self.RECALLED,
            "close": self.CLOSE,
            "defeated": self.DEFEATED, "adopt": self.ADOPT,
            "spent": self.SPENT, "premises": self.PREMISES,
            "contested": self.CONTESTED,
            "compose": self.COMPOSE, "composed": self.COMPOSED,
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
            # ⚠ `span_of(?s, ?start, ?end)` was described here and is GONE with
            # the locus -- a stretch was a kind of locus, and an entry has none.
            # The comment outlived the row it documented; `ugm.gates.vocabulary`
            # is what proved the name was gone rather than merely unused.
            "asking": self.chain.ASKING, "asked": self.chain.ASKED,
            # ⚠ Without this line `time(?m, ?t)` in a corpus is a FRESH
            # atom -- `g.atom` does not intern -- so the rule is well
            # formed, `is_stratum0` says no, the member matches nothing,
            # and nothing raises. The name-identity trap, caught here on
            # its fifth outing.
            "time": self.chain.TIME,
            "names": self.NAMES, "computes": self.COMPUTES,
            "overrides": self.OVERRIDES, "supersedes": self.SUPERSEDES,
            "widened": self.WIDENED, "reached": self.REACHED,
            "bounded": self.BOUNDED, "ticks": self.TICKS,
            "budget": self.BUDGET,
            **{str(i): n for i, n in self.NUMERAL.items()},
            "check": self.CHECK, "unmet": self.UNMET,
            "verdict": self.VERDICT, "pursued": self.PURSUED,
            "support": self.SUPPORT, "unsupported": self.UNSUPPORTED,
            "excluded": self.EXCLUDED,
            "fit": self.FIT, "fits": self.FITS, "unfit": self.UNFIT,
            "need": self.NEED,
            "causes": self.rules.CAUSES, "implies": self.rules.IMPLIES,
            # The signs as ARGUMENTS -- expects(p, plus) mentions a sign where
            # +p uses one. ⚠ unsure is NOT load-bearing for the bundle, and the
            # first version of this comment said it was.
            # →
            # docs/design/machine.md#the-signs-as-arguments-expects-p-plus-men
            "plus": self.rules.SIGN["+"], "minus": self.rules.SIGN["-"],
            "unsure": self.rules.SIGN["?"],
            # ...and the absence mode's node, so a reified `no` member --
            # `ant(?r, ?p, absent, ?i)` -- is a row a corpus can ask about.
            "absent": self.rules.SIGN[ABSENT],
        }

        self.selections = 0
        self.useful_writes = 0
        self.exhausted = 0
        # Backward reading is rules now, so its budget is the ordinary one: the
        # loop's `limit`, and `_would_change` for termination. The phase carried
        # its own counter because it ran outside arbitration and nothing else
        # could stop it.
        self.expansions = 0
        self._acted: set = set()
        self._quieted: set = set()
        # ⭐⭐⭐ A session is what it was TOLD. Everything that entered from
        # outside, in order: corpora loaded, arrivals delivered, runs asked
        # for.
        # → docs/design/machine.md#a-session-is-what-it-was-told-everythin
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
        # `+kind` marks per rule -- see `_markers`.
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
        # Machinery vocabulary: requests, not claims. Nothing carries these out
        # of a frame. doing is deliberately NOT here.
        # →
        # docs/design/machine.md#machinery-vocabulary-requests-not-claims-noth
        self._bookkeeping = {self.GOAL, self.ACHIEVED, self.BLOCKED,
                             self.PLAN, self.SUBGOAL, self.BINDS, self.EXPANDS,
                             self.EXPECTS, self.DID, self.DEVIATES,
                             self.EMITTED, self.FIT, self.FITS, self.UNFIT,
                             self.NEED, self.CHECK, self.UNMET,
                             self.QUIET, self.DORMANT,
                             self.ENOUGH, self.STOPPED, self.OPEN, self.HELPED, self.HARMED,
                             self.FORGONE, self.EXERCISED,
                             self.ROOT, self.ROOTED,
                             self.COUNT, self.COUNTED, self.NEW,
                             self.DUE, self.VERDICT, self.PURSUED,
                             self.ATTENTION, self.SPAN, self.DEPTH,
                             self.PUSHED, self.POPPED, self.SUITS,
                             self.AFFORDED, self.ATTEMPT, self.DECLINED,
                             self.UNAFFORDED, self.UNATTENDED, self.CALL, self.STAGE, self.SPAWN,
                             self.AWAITS, self.RETURNED,
                             self.ADVANCES, self.CLOSES,
                             self.SUPPORT, self.UNSUPPORTED, self.EXCLUDED,
                             self.FORBIDDEN, self.RELATIONSHIP, self.STANDING,
                             self.RECALL, self.RECALLED, self.CLOSE,
                             self.BUDGET,
                             self.WIDENED, self.REACHED,
                             self.BOUNDED, self.DEFEATED, self.ADOPT,
                             # ⚠ `self.gate.MOVED` was the last name here, and
                             # it was bookkeeping for a reason that is gone
                             # twice over: a seat move was the machinery's
                             # record of its own advance, and there is neither
                             # a seat to move nor a hypothesis to carry it out
                             # of. `Gate.reseat` minted it; nothing does now.
                             self.SPENT, self.PREMISES, self.CONTESTED}

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
                self.g.rel(self.STANDING, r.node), PLUS,
                licence=self.g.rel(self.REIFIED, r.node), source=self.KB, mention=True,
            )
        # ⭐⭐⭐ The apparatus eats its own cooking. ⚠ <remember> is the fourth,
        # and I put it in the safe column first.
        # → docs/design/machine.md#the-apparatus-eats-its-own-cooking-ans
        self.gate.on_write.append(self._adopt)
        # Refraction's cost, checked at the write: see `_contest`.
        self.gate.on_write.append(self._contest)
        self.gate.on_write.append(self._dispatch)
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
            # `fn` is `(entry)`; the answerer protocol is `(machine, entry)`,
            # and the answer is None because the apparatus
            # CONCLUDES where a tool PROPOSES. That is the one asymmetry left in
            # the door, and it is the right one: a tool is outside the agent, so
            # what it says lands as `answered(<M>, req, y)` for a corpus to
            # believe or not; `<settle>` is the agent, so what it finds lands as
            # `achieved`. Same binding, same trail, different standing to speak.
            a = self.answerer(name, request, lambda _m, e, fn=fn: fn(e))
            if standing:
                self.gate.write(
                    self.g.rel(self.STANDING, a.node), PLUS,
                    licence=self.g.rel(self.REIFIED, a.node), source=self.KB,
                    mention=True,
                )
        self.gate.veto.append(self._forbid)
        self.gate.veto.append(self._only_among_ids)
        self.gate.on_write.append(self._unafforded)
        # ⭐⭐⭐ Attention is a bounded QUEUE, newest first -- what replaces
        # unattend, LIFE and the accumulation problem at once. ⚠ And it decays
        # by DISPLACEMENT rather than by a timer, which is the better notion:
        # ten quiet ticks should not forget what you were doing, and ten busy
        # ones...
        # → docs/design/machine.md#attention-is-a-bounded-queue-newest-first
        # ⭐⭐⭐ ...and a STACK of those queues, because the queue forgets two
        # ways and a filter cannot help with either: at span 7 a long enough
        # sub-line evicts anything, however well chosen. A stack does not
        # filter, it SUSPENDS -- the outer frame is off the queue entirely, so
        # it cannot be evicted however long the inner line runs.
        self._frames: List[Frame] = [Frame()]
        # ⚠ Set once, at startup, and kept: `(document frequency, term counts)`
        # over experts. Adding an expert re-scores every other one and changes
        # which expert is picked for unrelated frames -- a FEATURE, not a bug,
        # written down so nobody debugs it as nondeterminism. See `_idf`.
        self._idf_cache = None
        # What the queue has forgotten, and how often it wanted it back. The
        # measurement `docs/todo.md` asks for before the stack is believed.
        self._evicted: set = set()
        self._readmitted = 0
        # ⚠ The lowest frame the RUNNING loop may pop back to. A nested `run()`
        # -- a consultation, a supposition, a table of agents -- serves the frame
        # it started on and must not pop the caller's out from under it, so the
        # floor moves with the run rather than being fixed at the root.
        self._floor = 0
        # The table a hand-stepping caller keeps between `tick` calls.
        self._step_table = None
        self._booting = False
        # The boundary calls in. Anything delivered before now was queued because
        # nobody was listening yet, so it is drained once, here.
        self.channels.sink = self._deliver
        for pending in self.channels.drain():
            self._deliver(pending)

    # -- the bundle -------------------------------------------------------

    #: The bundle, in the surface, in authored order. §18's tiebreak reads this
    #: file top to bottom, so its order is a precedence claim a reader can see.
    BUNDLE = _corpora.path("bundle.ugm")

    def _install_bundle(self) -> None:
        """Load the conventions that ship as rules rather than as branches (§4).

        This used to build them here, with self.rules.rule(IMPLIES, [Member(...
        g.rel(...))], ...).

        See docs/design/machine.md#install-bundle.
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
        # ⚠⚠⚠ The mint marker is the one relation that is surface-reachable
        # WITHOUT being a reserved name, and it has to be, or bundling a rule
        # that introduces something is impossible.
        # → docs/design/machine.md#the-mint-marker-is-the-one-relation-that-i
        known.add(self.NEW)
        missing = []

        def visit(n: NodeId) -> None:
            rel = self.g.relation_of(n)
            if rel is None:
                # ⚠⚠⚠ An ARGUMENT atom is a twin waiting to happen exactly as a
                # relation is, and this returned early on every one of them.
                # →
                # docs/design/machine.md#an-argument-atom-is-a-twin-waiting-to-happ
                if (not self.g.is_var(n) and not self.g.members(n)
                        and n not in known and self.g.show(n) not in missing):
                    missing.append(self.g.show(n))
                return
            if rel not in known and self.g.show(rel) not in missing:
                missing.append(self.g.show(rel))
            if rel is self.NEW:
                # ⚠ A mint MARKER is internal. `+k` says *one new thing per
                # application* and `k` is how the author told two markers apart
                # inside one consequent -- it names nothing a corpus could ask
                # about, so requiring it to be reserved would reserve a letter.
                return
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
        src = self._authoring_source or self.KB
        w = lambda p: self.gate.write(
            p, "+", licence=self.g.rel(self.REIFIED, rule.node), source=src, mention=True
        )
        w(self.g.rel(self.RULE, rule.node))
        conn = self.rules.CAUSES if rule.connective == "causes" else self.rules.IMPLIES
        w(self.g.rel(self.CONN, rule.node, conn))
        # ⚠⚠ The POSITION.
        # → docs/design/machine.md#the-position-it-was-missing-and-it-is-pa
        for i, m in enumerate(rule.antecedent):
            w(self.g.rel(self.ANT, rule.node, m.pattern,
                         self.rules.SIGN[m.sign], self._numeral(i)))
            self._reify_binds(w, self.ANT, rule.node, i, m)
        for i, m in enumerate(rule.consequent):
            w(self.g.rel(self.CON, rule.node, m.pattern,
                         self.rules.SIGN[m.sign], self._numeral(i)))
            self._reify_binds(w, self.CON, rule.node, i, m)

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

    def _fit(self, e: Entry) -> None:
        """Answer a match request (§5's wall, from the side that can be crossed).

        A rule concludes +fit(<R>, goal) -- *could this rule produce this?* --
        and the machinery answers, because deciding that a ground goal
        corresponds to a stored generic pattern is match, and match is floor.

        See docs/design/machine.md#fit.
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
                self.g.rel(self.FITS, rule_node, goal), PLUS,
                licence=licence, source=self.KB, consumed=(e,), mention=True,
            )
            # The bindings, as facts about the plan. A rule cannot hold a binding
            # (that is why `need` arrives instantiated), but it can hold a NODE
            # that other requests read -- which is how the sibling-agreement
            # problem is solved without a rule ever touching a substitution.
            plan = self.g.rel(self.PLAN, rule_node, goal)
            for var, val in b.items():
                self.gate.write(
                    self.g.rel(self.BINDS, plan, var, val), PLUS,
                    licence=licence, source=self.KB, consumed=(e,), mention=True,
                )
            for want in rule.antecedent:
                self.gate.write(
                    self.g.rel(self.NEED, rule_node, goal, substitute(self.g, want.pattern, b)),
                    PLUS,
                    licence=licence, source=self.KB, consumed=(e,), mention=True,
                )
            return
        self.gate.write(
            self.g.rel(self.UNFIT, rule_node, goal), PLUS,
            licence=licence, source=self.KB, consumed=(e,), mention=True,
        )

    def _settle(self, e: Entry) -> None:
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
        # ⚠⚠⚠ The entries, not only the map.
        # → docs/design/machine.md#the-entries-not-only-the-map-this-buil
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
            # ⭐ *Not that one.* Reconsidering a binding was the last of the
            # four hats, and the reason it was stuck is smaller than it looked:
            # a binds fact has always been deniable, and denying it achieves
            # nothing, because this loop then re-unifies and picks the SAME
            # first candidate.
            # →
            # docs/design/machine.md#not-that-one-reconsidering-a-binding-was-th
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
                self.g.rel(self.ACHIEVED, goal), PLUS,
                licence=licence, source=self.KB, consumed=(e, s) + used, mention=True,
            )
            for var, val in b.items():
                if var not in env:
                    self.gate.write(
                        self.g.rel(self.BINDS, plan, var, val), PLUS,
                        licence=licence, source=self.KB,
                        consumed=(e, s) + used, mention=True,
                    )
            return
        self.gate.write(
            self.g.rel(self.UNMET, plan, goal), PLUS,
            licence=licence, source=self.KB, consumed=(e,), mention=True,
        )

    def _root(self, e: Entry) -> None:
        """Answer *is this what I was asked for, or something I asked myself?*

        §6 recorded the gap and §12 recorded why it could not be a rule: a root
        goal is a goal(?w) with no subgoal(?p, ?w), and a - member says *an
        entry denies this*, never *for no ?p*. ⚠ It is asked, not volunteered,
        for the reason §19 gives about recall: this is a question about a
        search that has got somewhere, and asking it of every goal...

        See docs/design/machine.md#root.
        """
        if e.sign != PLUS or self.g.relation_of(e.proposition) is not self.ROOT:
            return
        wanted = self.g.member(e.proposition, 0)
        for node in self.g.instances_of(self.SUBGOAL):
            if self.g.member(node, 1) != wanted:
                continue
            s = self.chain.resolve(node)
            if s is not None and s.sign == PLUS:
                return
        self.gate.write(
            self.g.rel(self.ROOTED, wanted), PLUS,
            licence=self.g.rel(self.GOAL, wanted), source=self.KB, mention=True,
        )

    def _count(self, e: Entry) -> None:
        """Answer *how many ground matches does this pattern have here?*

        count(goblin(?x)) a REQUEST, asked by a corpus rule counted(goblin(?x),
        2) the answer, and it always answers ⭐⭐⭐ The general case of the three
        asks above it, and the reason it is worth having is that they are three
        special cases of one question. ⚠ Answered at the ask, not at
        quiescence.

        See docs/design/machine.md#count.
        """
        if self.g.relation_of(e.proposition) is not self.COUNT or e.sign != PLUS:
            return
        (pattern,) = self.g.members(e.proposition)
        # A one-member probe, matched by the ordinary matcher at this frame --
        # `_spend_posts` builds one the same way for a postcondition's query.
        probe = Rule(e.proposition, IMPLIES,
                     [Member(PLUS, pattern)], [], "<count>")
        # ⚠ Distinct PROPOSITIONS, not applications, and this is a GUARD rather
        # than a repair -- said plainly because the difference matters.
        # → docs/design/machine.md#distinct-propositions-not-applications-and-t
        seen = set()
        for hit in match(
            self.g, self.chain, probe, 
            self._situation(), computes=self.rules.computes,
            structural=self.rules.skeleton(),
        ):
            seen.add(substitute(self.g, pattern, hit.bindings))
        # ⚠⚠⚠ Keyed on the ASK, not on the pattern, and that is what makes the
        # answer readable at all.
        # → docs/design/machine.md#keyed-on-the-ask-not-on-the-pattern-and
        answer = self.g.rel(self.COUNTED, e.proposition, self._numeral(len(seen)))
        # ⚠⚠⚠ A COUNT IS A FUNCTIONAL ATTRIBUTE, so the old one is denied in
        # the same breath.
        # → docs/design/machine.md#a-count-is-a-functional-attribute-so-the
        for old in self.g.instances_of(self.COUNTED):
            if old == answer or self.g.member(old, 0) != e.proposition:
                continue
            if self.chain.resolve(old) is None:
                continue
            self.gate.write(
                old, MINUS, licence=e.proposition, source=self.KB,
                mention=True,
            )
        self.gate.write(
            answer, PLUS,
            licence=e.proposition, source=self.KB, mention=True,
        )

    def _supported(self, e: Entry) -> None:
        """Answer *does anything still hold this up?* -- the third negative

        existential, and it gets the treatment the other two got.

        See docs/design/machine.md#supported.
        """
        if self.g.relation_of(e.proposition) is not self.SUPPORT or e.sign != PLUS:
            return
        (about,) = self.g.members(e.proposition)
        for claim in self.chain.claims_about(about):
            if claim.sign != PLUS:
                continue
            if all(self._current(c) for c in self.chain.rests_on(claim)):
                return  # something still holds it up
        self.gate.write(
            self.g.rel(self.UNSUPPORTED, about), PLUS,
            licence=self.g.rel(self.SUPPORT, about), source=self.KB,
            consumed=(e,), mention=True,
        )

    def _current(self, c: Entry) -> bool:
        """Is this consumed entry still what `resolve` returns for its own
        proposition? The chain is append-only, but `resolve` is not monotone --
        a later denial makes what an entry rested on no longer the claim."""
        return self.chain.resolve(c.proposition) is c

    def _verdict(self, e: Entry) -> None:
        """Answer *did anything fit this goal?* -- the aggregate, and the last

        thing the goal phase was doing that no rule could do. blocked is a
        claim that no rule fits.

        See docs/design/machine.md#verdict.
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
                self.g.rel(self.PURSUED if fits else self.BLOCKED, settled),
                PLUS,
                licence=self.g.rel(self.VERDICT, wanted),
                source=self.KB,
                consumed=(e,),
                mention=True,
            )

    def _as_settled(self, wanted: NodeId, state) -> NodeId:
        """A goal, with whatever its own plan has since bound filled in.

        ⭐⭐⭐ A verdict was reported AS THE RULE WROTE IT, and by the time it is
        reported that is no longer the most informed thing available. ⚠ The
        consequence is exactly the one they named, and it is not cosmetic: a
        generic term cannot be uttered (§14 -- _dispatch refuses a generic
        intent, because...

        See docs/design/machine.md#as-settled.
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

    def _remember(self, e: Entry) -> None:
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
        self._answer_recall(self.g.member(e.proposition, 0), e)

    def _answer_recall(
        self, about: NodeId, because: Optional[Entry] = None
    ) -> None:
        candidates = self.rules.by_conclusion.get(self.g.relation_of(about), ())
        licence = self.g.rel(self.RECALL, about)
        for r in candidates:
            if self._claims(self.g.rel(self.DORMANT, r.node)) and not self._claims(
                self.g.rel(self.DUE, r.node)
            ):
                continue
            self.gate.write(
                self.g.rel(self.RECALLED, r.node, about), PLUS,
                licence=licence, source=self.KB,
                consumed=(because,) if because is not None else (), mention=True,
            )

    # -- norms ------------------------------------------------------------

    def _forbid(self, proposition: NodeId, sign: str) -> Optional[NodeId]:
        """§19's carve-out, and the whole of it.

        > Recall may be incomplete about what to do. It may not be incomplete >
        about what you must not do.

        See docs/design/machine.md#forbid.
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
            e = self.chain.resolve(node)
            if e is not None and e.sign == PLUS:
                return node
        return None

    def _only_among_ids(self, proposition: NodeId, sign: str) -> Optional[NodeId]:
        """The world model's split, enforced where facts enter.

        A relation declared `relationship(<rel>)` holds among things that have
        ids -- entities, atoms, other reified relationships -- and never among
        denotations. A compound member is an expression: a criterion for
        picking a thing out, not a thing, and depositing it would put a query
        into the world as if it were one. Any sign, because denying the
        malformed claim treats the query as a thing exactly as asserting it
        does. The refusal goes on the record like any other (`refused(...)`).
        """
        rel = self.g.relation_of(proposition)
        if rel is None or rel is self.REFUSED:
            return None
        # ⚠ A `+kind` marker is exempt: `new(kind)` is an id COMING TO BE, not
        # an expression -- which is what lets `_decide_change` consult this
        # veto on a minting rule's conclusion before anything is minted.
        if all(self.g.relation_of(mm) is None
               or self.g.relation_of(mm) is self.NEW
               for mm in self.g.members(proposition)):
            return None
        for node in self.g.instances_of(self.RELATIONSHIP):
            (declared,) = self.g.members(node)
            if declared != rel:
                continue
            e = self.chain.resolve(node)
            if e is not None and e.sign == PLUS:
                return node
        return None

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

        This is what arbitration was assumed to do and did not: a rule that
        lost was deferred, so quiescence ran it anyway and an agent with two
        ways to do something did both -- including the destructive one. ⚠ The
        apparatus is exempt on both sides -- §13's carve-out again.

        See docs/design/machine.md#forgo.
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
                    self.g.rel(self.FORGONE, a.rule.node, w), PLUS,
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

    def _reaching(self, a: NodeId, b: NodeId) -> bool:
        """Does any rule say that `a` reaches `b`? (§11's containment, moved.)

        The machinery consulting a corpus's rules, on demand, with both
        arguments already bound -- the door _forbid, precedence() and _recall
        already use, given a general name. ⚠ The author's line is about logic
        BURIED in Python, not about the direction of a call.

        See docs/design/machine.md#reaching.
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
                            x.binds)
                     for x in r.antecedent],
                    [], (r.name or "?") + "-reaches",
                )
                if match(self.g, self.chain, probe, Situation(self.g, []),
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

        The user's reason, and it is the right one: these should be reasonable
        over.

        See docs/design/machine.md#note.
        """
        if self._claims(proposition):
            return
        self.gate.write(
            proposition, PLUS,
            licence=licence or self.g.rel(self.QUIET, self.chain.now.node),
            source=self.KB, mention=True,
        )

    # -- the attention stack ----------------------------------------------

    @property
    def _attention(self) -> List[Tuple[NodeId, int]]:
        """The TOP frame's queue, which is what every reader of it wants.

        ⭐ A property rather than a rename, because *what the agent is thinking
        about* has one answer at any moment and it is the innermost line of
        work's. Everything the flat queue did it still does; what changed is
        that there can be more than one, and only one of them is live.
        """
        return self._frames[-1].queue

    @_attention.setter
    def _attention(self, queue) -> None:
        self._frames[-1].queue = list(queue)

    def _push_frame(self, nodes, licence: Optional[NodeId] = None):
        """Suspend what the agent was doing and open a frame on `nodes`.

        ⭐⭐⭐ **This is a call.** The nodes are what the new line of work is
        about; the expert is computed FROM them, so `push` names nodes and never
        an expert -- a rule that had to name one would be choosing the callee,
        which is the thing selection exists to do.

        ⚠ Returns None if the push was refused, and a refusal is DEPOSITED: a
        consultation that returned nothing and one that was never opened are two
        different things, and the second is the agent's own business to react to.
        """
        nodes = [n for n in nodes
                 if n is not None and not self.g.has_var(n)]
        if not nodes:
            # ⚠ Ground only, and silently so -- the same judgement `_spend_one`
            # makes about `attend(?x)` naming a variable the move did not bind.
            # A frame about no one is not a frame.
            return None
        expert, scores = self._pick_expert(nodes)
        for cand, score in scores:
            # The pick and the scores it beat, before the frame is opened, so
            # they stand even when the push is then refused.
            self._note(self.g.rel(self.SUITS, cand, self._numeral(score)),
                       licence)
        key = (expert, frozenset(nodes))
        if any((f.expert, frozenset(f.on)) == key for f in self._frames):
            # ⚠ The cycle test is on the PAIR -- the expert AND what it is being
            # asked about -- never on the expert alone. `A -> B -> A` about
            # something NEW is ordinary recursion and must stay allowed; the same
            # expert on the same nodes is the loop. `probes/experts.py` keys on
            # `(expert, question)` for exactly this reason, and with frames the
            # stack is the natural place to keep it.
            self._declined_frame(self.PUSHED, expert, nodes[0],
                                 "already_open", licence)
            return None
        if len(self._frames) >= (self._knob(self.DEPTH, FRAME_DEPTH)
                                 or FRAME_DEPTH):
            self._declined_frame(self.PUSHED, expert, nodes[0],
                                 "too_deep", licence)
            return None
        frame = Frame(expert, nodes)
        self._frames.append(frame)
        # Reversed, so the FIRST node named ends up at the front of the new
        # queue: `push(?a, ?b)` reads left to right and position is the
        # gradient, so the leftmost has to lift hardest.
        for node in reversed(nodes):
            self._attend(node, licence)
        for node in nodes:
            self._note(self.g.rel(self.PUSHED, expert, node)
                       if expert is not None
                       else self.g.rel(self.PUSHED, node), licence)
        return frame

    def _pop_frame(self, node: Optional[NodeId] = None,
                   licence: Optional[NodeId] = None) -> bool:
        """Return to the frame below, attending `node` on it.

        ⭐ `pop(?x)` carries one node back: the attention-level analogue of a
        return value. Without it the agent returns from a sub-line with no idea
        it concluded anything and has to rediscover it by ordinary matching --
        which is what `probes/experts.py` does today, re-running the caller from
        the top because there is nothing to resume into.

        ⚠⚠ The frame's own `attention` claims are DENIED, and nothing else is
        touched. Everything the frame concluded stands: popping a set of graph
        changes is a different feature, it does not exist, and it is not wanted.
        """
        if len(self._frames) - 1 <= self._floor:
            # ⚠ The root is not popped. Whether `stop` should BE *pop the root*
            # is elegant and not required; until it is, a pop with nothing to
            # return to is declined on the record rather than raised, because a
            # corpus that pops too often is arguing with itself and that is its
            # business.
            self._declined_frame(self.POPPED, None, node, "at_root", licence)
            return False
        frame = self._frames.pop()
        for n in frame.claimed:
            # Denied, not forgotten -- `_unattend`'s finding, scoped to a frame.
            # Left standing they would go on lifting rules from the bottom of
            # `_attended()` for the rest of the run, and the suspension would
            # leak the very thing it exists to put away.
            self.gate.write(
                self.g.rel(self.ATTENTION, n), MINUS,
                licence=licence or self.g.rel(self.QUIET, self.chain.now.node),
                source=self.KB, mention=True,
            )
        if node is not None and not self.g.has_var(node):
            self._attend(node, licence)
        self._note(self.g.rel(self.POPPED, frame.expert, node)
                   if frame.expert is not None and node is not None
                   else self.g.rel(self.POPPED,
                                   node if node is not None
                                   else self.chain.now.node),
                   licence)
        return True

    def _declined_frame(self, what: NodeId, expert, node, why: str,
                        licence: Optional[NodeId] = None) -> None:
        """A push or a pop that did not happen, on the record.

        On the record, never silent: `declined` is already what this machinery
        writes when an attempt is well formed and refused anyway, and a stack
        that quietly did nothing would be indistinguishable from one that had
        nothing to do."""
        self._note(self.g.rel(
            self.DECLINED, what,
            node if node is not None else self.chain.now.node,
            self.g.atom(why)), licence)

    # -- picking the expert -------------------------------------------------

    def _expert_pool(self, expert: Optional[NodeId]) -> List["Rule"]:
        """The rules this expert may consider, read off the graph.

        ⚠ Read, never kept: a registry built at load could not see a `knows` a
        rule concluded, and `<inherit>` concludes them.
        """
        if expert is None:
            return list(self.rules.rules)
        by_node = {r.node: r for r in self.rules.rules}
        out: List["Rule"] = []
        for inst in self.g.instances_of(self.KNOWS):
            members = self.g.members(inst)
            if len(members) != 2 or members[0] is not expert:
                continue
            if not self._claims(inst):
                continue
            r = by_node.get(members[1])
            if r is not None and r not in out:
                out.append(r)
        # Declaration order, so the table's tiebreak means what it means
        # everywhere else: the order the author wrote them in.
        order = {r.node: i for i, r in enumerate(self.rules.rules)}
        out.sort(key=lambda r: order.get(r.node, 0))
        return out

    def _experts(self) -> List[NodeId]:
        """Everyone who knows anything, in the order the graph met them."""
        out: List[NodeId] = []
        for inst in self.g.instances_of(self.KNOWS):
            members = self.g.members(inst)
            if len(members) != 2 or self.g.has_var(members[0]):
                continue
            if not self._claims(inst):
                continue
            if members[0] not in out:
                out.append(members[0])
        return out

    def _terms_of(self, expert: NodeId) -> Dict[NodeId, int]:
        """What an expert's rules are ABOUT: ground terms, counted.

        ⭐ Decomposed with `_nodes_of`, which is attention's own scoring: a
        proposition is every node it is made of, and each part counts. The
        discussion was had once for rules; this is it for experts.
        """
        counts: Dict[NodeId, int] = {}
        for r in self._expert_pool(expert):
            for mm in list(r.antecedent) + list(r.consequent):
                for node in self._nodes_of(mm.pattern, []):
                    if self.g.is_var(node) or self.g.has_var(node):
                        continue
                    counts[node] = counts.get(node, 0) + 1
        return counts

    def _idf(self):
        """`(terms per expert, inverse document frequency)` -- computed ONCE.

        ⭐⭐⭐ **IDF is the principled repair of a collapse this repository
        measured**, not a generic scoring choice. `_salient` compared raw
        relation sets and `_relations_required` collapsed to `{goal, in}` for
        every route, so it could not tell two routes apart, `leaves()` returned
        nothing, and the agent rehearsed, was harmed, blamed correctly and
        learned nothing with no error anywhere. A term in every expert's pool
        gets weight ZERO here and stops drowning the signal; the discriminating
        terms carry the score.

        ⭐ It also supersedes a hand-rolled guard. `_pull` takes the STRONGER,
        not the sum, because *adding them would make the weight a popularity
        count* -- a crude defence against ubiquity. IDF is the well-founded
        version of the same defence, which is what makes a weighted SUM safe
        here where a raw one was not.

        ⚠ Computed once, at the first pick, over the whole KB as loaded. Pools
        are read and never kept, and `knows(?e, ?r)` can be concluded mid-run,
        so an expert's actual pool can GROW after its scores were computed. The
        two facts are in tension by design rather than by oversight.
        """
        if self._idf_cache is not None:
            return self._idf_cache
        import math

        docs = {e: self._terms_of(e) for e in self._experts()}
        total = len(docs)
        df: Dict[NodeId, int] = {}
        for terms in docs.values():
            for t in terms:
                df[t] = df.get(t, 0) + 1
        idf = {t: math.log(total / d) for t, d in df.items()} if total else {}
        self._idf_cache = (docs, idf)
        return self._idf_cache

    def _pick_expert(self, nodes):
        """Which expert a frame about `nodes` belongs to, by TF-IDF.

        ⚠⚠⚠ **Unarguable, and knowingly so.** Like attention it is life or
        death -- an expert that is never picked cannot object that it was not --
        and §19 already answered this shape of problem. The answer was never a
        veto over the choice: *recall may be incomplete about what to do; it may
        not be incomplete about what you must not do.* `_forbid` runs outside
        recall entirely, so the mitigation for an unarguable selection is not
        making it arguable, it is knowing what must not ride on it.

        Returns `(expert or None, [(expert, hundredths) ...])`. ⚠ **None when
        nothing discriminates.** A score of zero everywhere means the terms are
        in every pool or in none, and picking the first expert declared would be
        a coin flip wearing a mechanism's clothes -- so the frame keeps the
        rules of the frame below and says so.
        """
        docs, idf = self._idf()
        if not docs:
            return None, []
        # ⭐ The query, decomposed exactly as an expert's pool is, with a BONUS
        # for compounds: matching a whole proposition is a stronger signal than
        # matching the relation it is made of, because the parts are what
        # everything shares.
        query: Dict[NodeId, int] = {}
        for node in nodes:
            for term in self._nodes_of(node, []):
                if self.g.is_var(term) or self.g.has_var(term):
                    continue
                bonus = 2 if self.g.members(term) else 1
                query[term] = query.get(term, 0) + bonus
        scores = []
        for expert, terms in docs.items():
            score = 0.0
            for term, weight in query.items():
                if term in terms:
                    score += weight * terms[term] * idf.get(term, 0.0)
            # Hundredths, so the deposit is a numeral a rule can compare and
            # `why()` can read back.
            scores.append((expert, int(round(score * 100))))
        best = max(s for _e, s in scores)
        if best <= 0:
            return None, scores
        # Ties by the order the graph met the expert, which is authored order --
        # the same tiebreak the table uses, one construct along.
        for expert, score in scores:
            if score == best:
                return expert, scores
        return None, scores

    def _attend(self, node: NodeId, licence: Optional[NodeId] = None,
                weight: int = 1) -> bool:
        """*Think about this one.* -- what a postcondition spends when it
        attends, and an ordinary claim when it lands.

        ⭐ Licensed by the rule that spent it, the way `close` and `defeated`
        name the rule that produced them. So *why am I thinking about this*
        answers with a rule and a moment, which is the whole reason attention is
        a claim rather than a field on the loop.
        """
        self._push_attention(node, weight)
        prop = self.g.rel(self.ATTENTION, node)
        if self._claims(prop):
            return False
        self._note(prop, licence)
        # ⚠ Recorded against the frame that made it, so a pop denies exactly
        # what its own line of work claimed and nothing the line below did.
        self._frames[-1].claimed.append(node)
        return True

    def _attend_written(self, wrote) -> None:
        """What a move just wrote goes on the queue, at weight 1.

        ⚠⚠⚠ Backed out TWICE before (20d, 20h) and back only because the piece
        it was missing now exists. Everything one move writes arrives at the
        same depth, so the queue alone cannot tell those nodes apart -- and a
        queue permanently full of undifferentiated nodes made the agent chase
        its own tail and quiesce 30 moves early.

        ⭐ A learned `attend(?x, 3)` outweighs them. Weight 1 is *this is what
        just happened*; a multiplier is *and a lesson says this part mattered*.
        """
        for e in reversed(tuple(wrote or ())):
            # ⚠ NOT the agent's own record-keeping. `spent`, `did`, `goal` and
            # the rest are how the machinery remembers what it did, not things
            # the world is about -- and a queue full of them is a queue that
            # says nothing about the situation.
            if self.g.relation_of(e.proposition) in self._bookkeeping:
                continue
            for node in self._nodes_of(e.proposition, []):
                if self.g.relation_of(node) in self._bookkeeping:
                    continue
                self._push_attention(node)

    def _nodes_of(self, node: NodeId, out: List[NodeId]) -> List[NodeId]:
        """A proposition, decomposed into every node it is made of."""
        if node in out:
            return out
        out.append(node)
        rel = self.g.relation_of(node)
        if rel is not None:
            self._nodes_of(rel, out)
        for m in self.g.members(node):
            self._nodes_of(m, out)
        return out

    def _push_attention(self, node: NodeId, weight: int = 1) -> None:
        """To the top, and whatever falls off the bottom is forgotten.

        ⚠ Re-attending something already in the queue MOVES it up rather than
        adding it twice: a thing thought about twice is one thing thought about
        recently, and a queue that held duplicates would let one node crowd out
        everything else the agent knows it is doing.
        """
        queue = self._frames[-1].queue
        if node in self._evicted:
            # ⚠⚠⚠ **The number the stack has to justify itself against.** A node
            # that fell off the bottom and is wanted AGAIN is an outer focus a
            # sub-line evicted while it was still live -- the agent rediscovering
            # by ordinary matching what it already knew it was doing. Counted
            # rather than argued: *a frame that fixes nothing measurable is a
            # mechanism this design would refuse on its own terms.*
            self._readmitted += 1
            self._evicted.discard(node)
        queue[:] = [(n, w) for n, w in queue if n != node]
        queue.insert(0, (node, max(1, weight)))
        span = self._knob(self.SPAN, ATTENTION_SPAN)
        if span is not None and span > 0:
            for n, _w in queue[span:]:
                self._evicted.add(n)
            del queue[span:]

    def _unattend(self, licence: Optional[NodeId] = None) -> int:
        """Stop thinking about whatever it was -- `reset`, for attention.

        ⚠ **Denied, not forgotten.** *The agent stopped attending to this here*
        is dated and attributable; dropping a Python set is not readable by any
        rule and cannot be argued with. That is `docs/deposit-dont-decide.md`
        applied to the one piece of state a postcondition can now write.

        ⚠⚠ And something must say it. Attention accumulates otherwise, and
        attention that names everything narrows nothing -- measured in
        `ugm.selftest`. A buff had `LIFE` for this reason; a claim has a denial,
        and a corpus decides when.
        """
        dropped = 0
        self._attention = []
        for node in self._attended():
            self.gate.write(
                self.g.rel(self.ATTENTION, node), MINUS,
                licence=licence or self.g.rel(self.QUIET, self.chain.now.node),
                source=self.KB, mention=True,
            )
            dropped += 1
        return dropped

    def _unafforded(self, e) -> None:
        """An attempt at something the palette does not afford, on the record.

        ⭐ The engine's whole share of an action. What is LEGAL is the world
        model's business and a rule says it; what EXISTS is the palette's, and
        only the machinery can check it, because subsumption runs the pattern
        against the entry and here the entry is the generic one.

        ⚠ Cheap for `_forbid`'s reason: indexed by what is being written, so it
        costs nothing on a write that is not an attempt, and the palette is
        walked only for one that is.
        """
        if self._booting or e.sign != PLUS:
            return
        if self.g.relation_of(e.proposition) is not self.ATTEMPT:
            return
        members = self.g.members(e.proposition)
        if len(members) != 1 or self.g.has_var(members[0]):
            return
        wanted = members[0]
        for node in self.g.instances_of(self.AFFORDED):
            sig = self.g.members(node)
            if len(sig) != 1 or not self._claims(node):
                continue
            # ⭐⭐⭐ The palette is the AUTHOR's, and this is what makes that true
            # rather than conventional. ⚠ The affordance is not refused — a
            # corpus may say what it likes, and a claim ABOUT the palette is
            # not a claim ON it.
            # →
            # docs/design/machine.md#the-palette-is-the-author-s-and-this-is-w
            e = self.chain.resolve(node)
            if e is not None and e.licence is not None and (
                    self.g.relation_of(e.licence) is self.APPLIED):
                continue
            if unify(self.g, sig[0], wanted, {}) is not None:
                return
        self._note(self.g.rel(self.DECLINED, wanted, self.UNAFFORDED),
                   licence=e.node)

    def _knob(self, relation: NodeId, default):
        """A knob a corpus can turn, read from the graph.

        A numeral is an ordinary atom whose *name* reads as a number, so
        nothing in the graph learns arithmetic and only the reader that wants one
        does. Highest wins, so raising a bound is a claim and lowering it is a
        different claim about the same thing, settled by §12's ordinary defeat.
        """
        best = None
        for node in self.g.instances_of(relation):
            e = self.chain.resolve(node)
            if e is None or e.sign != PLUS:
                continue
            name = self.g.show(self.g.member(node, 0))
            if name.isdigit() and (best is None or int(name) > best):
                best = int(name)
        return default if best is None else best

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
        self._note(self.g.rel(self.WIDENED, self.chain.now.node))
        return True

    def _outstanding(self) -> bool:
        """Is anything the agent was asked for still unmet? Read the same way
        `_notice_open` reads it, because it is the same question."""
        for node in self.g.instances_of(self.GOAL):
            if self.g.has_var(node):
                continue
            e = self.chain.resolve(node)
            if e is None or e.sign != PLUS:
                continue
            got = self.chain.resolve(self.g.member(node, 0))
            if got is None or got.sign != PLUS:
                return True
        return False

    def _recover(self) -> bool:
        """Nothing applies -- but is that because a domain is out of mind? (§19)

        §19's carve-out for the fourth time, and the argument transfers whole.
        ⚠ Only when something is outstanding, and running it without that is
        how the shape became clear.

        See docs/design/machine.md#recover.
        """
        if not self._out_of_mind() or not self._outstanding():
            return False
        self.recoveries += 1
        self._note(self.g.rel(self.REACHED, self.chain.now.node))
        # A claim, deposited rather than a flag, so *why is billing back?* has an
        # answer and a corpus can argue with the escalation as it can with
        # anything else. `due` is the same fact that wakes a dormant rule.
        for c in self._out_of_mind():
            self.gate.write(
                self.g.rel(self.DUE, c), PLUS,
                licence=self.g.rel(self.QUIET, self.chain.now.node),
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
            e = self.chain.resolve(node)
            if e is not None and e.sign == PLUS:
                reason = node
                break
        if reason is None:
            return None
        if self.chain.now.node in self._vetoed:
            # The veto has already been exercised here, and it did not merely
            # cost a tick: it handed the loop back.
            # →
            # docs/design/machine.md#the-veto-has-already-been-exercised-here-and-it
            return None
        if self._notice_open():
            self._vetoed.add(self.chain.now.node)
            return None
        return reason

    def _notice_open(self) -> bool:
        """The veto: a stop with a goal still outstanding is not a stop.

        Why this is machinery and not the rule a well-written corpus would
        have.

        See docs/design/machine.md#notice-open.
        """
        seat = self.chain.now.node
        stopped = False
        for node in self.g.instances_of(self.GOAL):
            if self.g.has_var(node):
                continue
            e = self.chain.resolve(node)
            if e is None or e.sign != PLUS:
                continue
            (wanted,) = self.g.members(node)
            if (seat, wanted) in self._noticed:
                continue
            got = self.chain.resolve(wanted)
            if got is not None and got.sign == PLUS:
                continue
            self._noticed.add((seat, wanted))
            self.gate.write(
                self.g.rel(self.OPEN, wanted), PLUS,
                licence=self.g.rel(self.GOAL, wanted), source=self.KB, mention=True,
            )
            stopped = True
        # ⭐⭐⭐ And an ATTEMPT nobody resolved, which is the same claim. ⚠ It has
        # to be HERE and not in a watchdog keyed on quiet, and that is the
        # whole finding.
        # → docs/design/machine.md#and-an-attempt-nobody-resolved-which-is-t
        return self._notice_attempts() or stopped

    def _notice_attempts(self) -> bool:
        """An attempt nobody resolved, on the record before the loop ends.

        ⭐⭐⭐ A goal still open and a request still outstanding are the same
        claim -- *the agent was asked for something and it did not happen* --
        so both go on the record as open and both veto a stop once. ⚠ Called
        from BOTH endings, and that is the whole of it.

        See docs/design/machine.md#notice-attempts.
        """
        seat = self.chain.now.node
        noticed = False
        for node in self.g.instances_of(self.ATTEMPT):
            if self.g.has_var(node):
                continue
            e = self.chain.resolve(node)
            if e is None or e.sign != PLUS:
                continue
            (asked,) = self.g.members(node)
            if (seat, asked) in self._noticed:
                continue
            self._noticed.add((seat, asked))
            # ⚠⚠⚠ The machinery says this, not a bundled watchdog, and the
            # reason is measured rather than aesthetic.
            # →
            # docs/design/machine.md#the-machinery-says-this-not-a-bundled-wat
            self._note(self.g.rel(self.DECLINED, asked, self.UNATTENDED),
                       licence=self.g.rel(self.ATTEMPT, asked))
            noticed = True
        return noticed

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
        seat = self.chain.now
        if seat.node in self._stopped:
            return False
        self._stopped.add(seat.node)
        self.gate.write(
            self.g.rel(self.STOPPED, seat.node, reason), PLUS,
            licence=self.g.rel(self.ENOUGH, reason), source=self.KB,
        )
        return True

    def _wake(self) -> bool:
        """The loop found nothing to do. Say so, in the graph, once per seat.

        ⚠ And notice what is still outstanding while there is still a tick to
        react in -- the same call _enough makes before stopping satisfied.

        See docs/design/machine.md#wake.
        """
        seat = self.chain.now
        if seat.node in self._quieted:
            return False
        self._quieted.add(seat.node)
        self._notice_attempts()
        self.gate.write(
            self.g.rel(self.QUIET, seat.node), PLUS,
            licence=self.g.rel(self.QUIET, seat.node), source=self.KB,
        )
        return True

    # -- acting, and being wrong about it ---------------------------------

    # -- tools ------------------------------------------------------------

    def computator(self, name, fn) -> NodeId:
        """Register a function that is COMPUTED during a match (§12, §22).

        { +purse(?a, ?x), +cost(?i, ?c), minus(?x, ?c) as ?new } ⭐⭐⭐ Purity is
        structural here, not declared. ⚠ It is registered in the CORPUS's
        scope, for Loader.answerer's reason: a relation is a name, and a name
        minted beside the corpus's table is a relation nobody...

        See docs/design/machine.md#computator.
        """
        rel = self.g.atom(name) if isinstance(name, str) else name
        self.rules.computes[rel] = fn
        # ...and it is on the record, so *which of these exist* is a query
        # rather than a fact about the source (§17).
        self.gate.write(self.g.rel(self.COMPUTES, rel), PLUS,
                        licence=self.g.rel(self.REIFIED, rel), source=self.KB,
                        mention=True)
        return rel

    def answerer(self, name: str, request: str, fn) -> "Answerer":
        """Register something that answers a request. §21's debt, as data.

        A tool is not a new kind of thing. ⚠ The name goes in the <...>
        namespace, which is the namespace of STATEMENTS, because a tool is
        something other statements are about.

        See docs/design/machine.md#answerer.
        """
        # ⚠ request may be a NodeId, and for a corpus relation it must be.
        # → docs/design/machine.md#request-may-be-a-nodeid-and-for-a-corpus-re
        try:
            inspect.signature(fn).bind(None, None)
        except TypeError:
            raise TypeError(
                f"answerer {name!r} does not take (machine, entry) -- an "
                f"answerer is called with two arguments and returns the answer "
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
            self.g.rel(self.ANSWERS, node, a.request), PLUS,
            licence=self.g.rel(self.REIFIED, node), source=self.KB, mention=True,
        )
        return a

    def _answer(self, e: Entry) -> None:
        """Call whatever answers this request, and record what it said.

        Three things it deliberately is not. Not a conclusion. What lands is
        answered(<M>, req, y) -- a record that M said so, the same treatment
        §17 gives every arrival.

        See docs/design/machine.md#answer.
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
                # about how to READ.
                # →
                # docs/design/machine.md#19-s-carve-out-a-fifth-time-and-the-argum
                if not self._claims(self.g.rel(self.STANDING, a.node)):
                    continue
                refusal = self.g.rel(
                    self.REFUSED,
                    self.g.rel(self.ANSWERS, a.node, a.request),
                    self.chain.SIGN[MINUS],
                    self.g.rel(self.STANDING, a.node),
                )
                if self.chain.resolve(refusal) is None:
                    self.gate.write(
                        refusal, PLUS,
                        licence=self.g.rel(self.STANDING, a.node),
                        source=self.KB, mention=True,
                    )
            said = a.fn(self, e)
            if said is None:
                continue
            self.gate.write(
                self.g.rel(self.ANSWERED, a.node, e.proposition, said), PLUS,
                licence=self.g.rel(self.APPLIED, a.node), source=self.KB,
                mention=True,
            )

    def _again(self, e: Entry) -> None:
        """Re-deliver a request, because a corpus said an occasion warrants it.

        §6: *a request can only be made once.* <ask-check> asks whether a
        subgoal is already satisfied at the moment the subgoal appears; if
        forward reasoning satisfies it three ticks later, nothing asks again,
        because re-concluding +check(p, w) restates what the chain says and
        quiescence drops it. ⚠ What an occasion may be is the whole question,
        and it is not free choice.

        See docs/design/machine.md#again.
        """
        if e.sign != PLUS or self.g.relation_of(e.proposition) is not self.AGAIN:
            return
        members = self.g.members(e.proposition)
        if len(members) != 2:
            return
        request, occasion = members
        self.gate.write(
            request, PLUS,
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

    def _dispatch(self, e: Entry) -> None:
        """The outbound boundary, at the write rather than in the loop.

        A rule concludes +doing(p) like any other fact; this carries it past
        the agent's edge, because a boundary is anchored and a rule is generic.

        See docs/design/machine.md#dispatch.
        """
        if e.sign != PLUS or self.g.relation_of(e.proposition) is not self.DOING:
            return
        if self.g.has_var(e.proposition):
            return  # a description cannot be acted on; §15's condition, at the edge
        if e.node in self._acted:
            return
        self._acted.add(e.node)
        (what,) = self.g.members(e.proposition)
        if self.replaying:
            # ⚠⚠⚠ Replaying a session must not re-do it.
            # → docs/design/machine.md#replaying-a-session-must-not-re-do-it-t
            self.gate.write(
                self.g.rel(self.TAKEN, what), "+",
                licence=self.g.instance(self.UTTERANCE, self.KB, what),
                source=self.KB, consumed=(e,),
            )
            return
        self.emitted.append(what)
        # The smallest unarguable record that something left the agent. What it
        # MEANS is `<did>`, and what follows from it is `<assert-act>`.
        self.gate.write(
            self.g.rel(self.EMITTED, what), "+",
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

    def _adopt(self, e: Entry) -> None:
        """Make a rule the graph describes into a rule the loop reads.

        adopt(<R>) ⭐⭐⭐ reify went one way. ⚠ Refused inside a supposition, and
        this is containment rather than caution.

        See docs/design/machine.md#adopt.
        """
        if e.sign != PLUS or self.g.relation_of(e.proposition) is not self.ADOPT:
            return
        if self.g.has_var(e.proposition):
            return  # a description cannot be adopted; §15's condition again
        (node,) = self.g.members(e.proposition)
        if any(r.node == node for r in self.rules.rules):
            return  # already live -- restating is not revising (§8)
        built = self._read_rule(node)
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

    def _compose(self, e: Entry) -> None:
        """Collapse two rules into one, because a corpus asked.

        compose(<a>, <b>) ⟹ composed(<c>, <a>, <b>) §4 calls composition the
        design's larger optimisation -- it removes steps rather than making
        them cheaper -- and it had no trigger: the function existed and only
        Python called it, which is where adopt was before it was a door. ⚠
        Refused inside a supposition, and it is _adopt's argument exactly.

        See docs/design/machine.md#compose.
        """
        members = self.g.members(e.proposition)
        if len(members) != 2:
            return None
        # ⚠⚠⚠ has_var is not a usable guard here, and copying _adopt's was the
        # bug.
        # → docs/design/machine.md#has-var-is-not-a-usable-guard-here-and
        first = self.rules.by_node.get(members[0])
        second = self.rules.by_node.get(members[1])
        if first is None or second is None:
            # Not live rules. `None` is a real answer (§17) -- a tool that must
            # answer everything is one nothing can decline.
            return None
        self.rules.inherit = []
        composed = self.rules.compose(first, second)
        if composed is None:
            return None  # nothing of the first's consequent meets the second
        self.gate.write(
            self.g.rel(self.COMPOSED, composed.node, first.node, second.node),
            PLUS, licence=e.node, source=self.KB, mention=True,
        )
        for higher, lower in self.rules.inherit:
            self.gate.write(
                self.g.rel(self.OVERRIDES, higher.node, lower.node),
                PLUS, licence=e.node, source=self.KB, mention=True,
            )
        self.rules.inherit = []
        return None

    def _read_rule(self, node: NodeId):
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

        def side(relation):
            out = []
            for p in self.g.instances_of(relation):
                if self.g.member(p, 0) is not node or not self._claims(p):
                    continue
                members = self.g.members(p)
                i = self.g.show(members[3])
                out.append((i, Member(sign_of.get(members[2], PLUS), members[1],
                                      slot(self.NAMES, relation, int(i)))))
            return [m for _, m in sorted(out, key=lambda pair: int(pair[0]))]

        con = side(self.CON)
        if not con:
            return None  # a rule that concludes nothing is not a rule
        return connective, side(self.ANT), con

    def _expect(self, proposition: NodeId, sign: str, licence: NodeId) -> None:
        """Forward application deposits what it predicts (§16).

        Without the deposit there is nothing to be surprised against -- an
        expectation that lives in an interpreter variable is unmatched not
        because the rule was weak but because there is nothing there to match.
        """
        self.gate.write(
            self.g.rel(self.EXPECTS, proposition, self.rules.SIGN[sign]), "+",
            licence=licence, source=self.KB, mention=True,
        )

    # Noticing a deviation used to be a phase here. It is now four bundled rules
    # (`_install_bundle`), and it had no boundary component at all -- §18 already
    # said *surprise is a match*, and the phase was that sentence being false of
    # the implementation.

    # -- backward reading ------------------------------------------------- It
    # used to be here: _expand_goal, the last interpreter phase, deleted in
    # nophases.
    # → docs/design/machine.md#backward-reading

    # -- the loop ---------------------------------------------------------

    def tick(self) -> Step:
        """One move of the loop, for a caller that wants to step and look.

        ⭐⭐⭐ This was 129 lines of the option-set loop -- materialise every live
        application, defeat, filter, arbitrate, apply -- kept alive so that
        `ugm.attention`'s comparison had something to compare against. Both are
        deleted (20k, 20l). What a caller of `tick` wants is *step once and
        look*, and this is that: the same loop `run` is, bounded to one move.

        ⚠ The table PERSISTS across calls, or a caller stepping by hand would
        lose every buff between one tick and the next and be measuring a
        different agent each time.

        ⚠⚠ **Measured 2026-08-21, and that warning is currently INERT.** With
        the buffs retired a score is `STANDING` or `FLOOR` and only `absorb`
        moves it, so a rebuilt table and a kept one agree in both fields that
        decide a move -- `probes/experts.py` runs a consultation chain both ways
        and gets the same moves in the same order. Kept because it costs nothing
        and is load-bearing again the day anything moves a score.

        See docs/design/machine.md#tick.
        """
        from .attention import Table, _standing, run as _table_run

        if self._step_table is None:
            self._step_table = Table(self.g, self.rules.rules, _standing(self))
        steps = _table_run(self, limit=1, table=self._step_table).steps
        return steps[0] if steps else Step(0, 0, 0, None, (), "quiescent")

    def run(self, limit: int = 100) -> List[Step]:
        """Bounded, and it returns a result *and* a state -- because a search that

        stopped is not a search that found nothing (§9, §15). ⭐⭐⭐ And the bound
        says so, which is §21's defect for the eleventh time and the one a
        foreign corpus asked for first. ⚠ Deposited only when the loop is still
        WORKING at the limit.

        See docs/design/machine.md#run.
        """
        # ⭐⭐⭐ THE TABLE LOOP IS THE LOOP. This was the switch in a staged
        # migration; the migration is finished and this is the entry point. It
        # stays a delegation rather than moving the callers, because 193 call
        # sites in this tree say `m.run(limit=...)` and none of them wants to
        # know that a table exists.
        # → docs/design/machine.md#the-table-loop-is-the-loop
        from .attention import run as _table_run

        return _table_run(self, limit=limit).steps

    # -- the four primitives ----------------------------------------------

    def _recall(self) -> List[Rule]:
        """Never complete, by design (§15). Exhaustive here, which is the

        deliberate-reasoning setting: recall with the budget removed -- with
        one exception, and the exception is the first thing a corpus has ever
        been able to say to this step.

        See docs/design/machine.md#recall.
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

        # Nothing DERIVED narrows this step, and finding out why was a
        # session's clearest negative result. ⚠ The cap used to order by
        # prefer(<R>, key, n) before cutting.
        # →
        # docs/design/machine.md#nothing-derived-narrows-this-step-and-finding-o
        budget = self._knob(self.BUDGET, self.recall_budget)
        if budget is None:
            return live
        out = list(live[:budget])
        for r in live:
            # Two things a cap may not starve, and they are §19's carve-out
            # arriving for the third and fourth time. A woken callback, because
            # a pointer that recall can drop is not a pointer.
            # →
            # docs/design/machine.md#two-things-a-cap-may-not-starve-and-they-are-1
            if r not in out and (
                self._claims(self.g.rel(self.DUE, r.node))
                or self._claims(self.g.rel(self.STANDING, r.node))
            ):
                out.append(r)
        return out

    def _attended(self) -> List[NodeId]:
        """What the agent is thinking ABOUT: the nodes it claims `attention` of.

        The counterpart to _in_play, and the difference is the point. ⚠ Ground
        only.

        See docs/design/machine.md#attended.
        """
        # ⭐ The QUEUE first, newest at the front, because position is the
        # gradient: what the agent turned to last is what it is most about.
        out: List[NodeId] = [n for n, _w in self._attention]
        # ...and a standing claim not in the queue goes at the BOTTOM. A corpus
        # writing `fact +attention(goblin1)` has said something lasting rather
        # than something recent, so it ranks below whatever the agent was just
        # doing -- and it is not lost.
        for node, _weight in self._claimed_attention():
            if node not in out:
                out.append(node)
        return out

    def _attention_asked(self) -> List[NodeId]:
        """Only what something CLAIMED attention of — authored or learned.

        ⭐⭐⭐ The line is claimed vs derived, not weighted vs plain. Someone
        saying *attend to this* is a reason to bring rules to mind; the
        machinery noticing *this just happened* is not, and conflating them is
        what starved the shortlist — the dungeon quiesced 32 moves early and
        lost 48 conclusions because a queue full of the last move's nodes
        decided which rules were matched at all.

        ⚠ Ordered by the QUEUE where a claim is in it, so a claim just made
        outranks one standing since the corpus loaded.
        """
        # ⚠⚠⚠ **GRAPH order for the tail, and it was a SET.** `for n in {...}`
        # iterated by node id, so which standing claim lifted hardest was decided
        # by how many atoms the machinery happened to mint before the corpus was
        # loaded -- and adding one reserved name reordered a shortlist in a check
        # that had been green for weeks. Nothing raised, because a set is a
        # perfectly good answer to *which*; it is only no answer at all to
        # *which first*, and position is the strength here.
        claimed = [n for n, _w in self._claimed_attention()]
        want = set(claimed)
        out = [n for n, _w in self._attention if n in want]
        for n in claimed:
            if n not in out:
                out.append(n)
        return out

    def _claimed_attention(self) -> List[Tuple[NodeId, int]]:
        """Every standing `attention` claim, as `(node, weight)`, in graph order.

        ⭐⭐⭐ A claimed attention may carry its evidence count, exactly as a
        spent one does. ⚠ A weight that is not a numeral is ignored rather than
        refused: a numeral is an atom whose name reads as a number, and
        attention(x, soon) is a claim about...

        See docs/design/machine.md#claimed-attention.
        """
        out: List[Tuple[NodeId, int]] = []
        for node in self.g.instances_of(self.ATTENTION):
            members = self.g.members(node)
            if not 1 <= len(members) <= 2 or self.g.has_var(members[0]):
                continue
            if not self._claims(node):
                continue
            weight = 1
            if len(members) == 2:
                name = self.g.show(members[1])
                if name.isdigit():
                    weight = max(1, int(name))
            out.append((members[0], weight))
        return out

    def _attention_weights(self) -> dict:
        """Node -> the multiplier a lesson put on it, for the lift.

        ⚠ The STRONGER of the two, never the sum. A node both spent and
        claimed is not twice as salient, and adding them would make the weight a
        popularity count -- the same judgement `_pull` makes about a rule
        reachable from two attended nodes.
        """
        out = {n: w for n, w in self._attention}
        for node, weight in self._claimed_attention():
            if weight > out.get(node, 0):
                out[node] = weight
        return out

    def _claims(self, proposition: NodeId) -> bool:
        e = self.chain.resolve(proposition)
        return e is not None and e.sign == PLUS

    def _deliver(self, a: Arrival) -> None:
        """Cross the boundary, and nothing else — when the world speaks, not when

        the loop next gets round to asking.

        See docs/design/machine.md#deliver.
        """
        self._report(a)

    def _report(self, a: Arrival) -> None:
        """The body of `_deliver`."""
        utterance = self.g.instance(self.UTTERANCE, a.channel, a.proposition)
        report = self.g.rel(
            self.ARRIVED, a.channel, a.proposition, self.rules.SIGN[a.sign]
        )
        self.gate.write(
            report, PLUS, licence=utterance, source=a.channel,
        )

    def _apply(self, app: Application) -> Tuple[Entry, ...]:
        """Forward reading: apply the consequent's signs into the right moment.

        `implies` lands in the *same* moment -- the entry is derived, and retract
        the antecedent and it goes with it. `causes` lands in a *later* one -- the
        entry is asserted, and it persists. Water you have stopped heating stays
        boiled, which is why a zero-delay cause is still not an implication.
        """
        licence = self.g.rel(self.APPLIED, app.rule.node)
        # ⭐⭐⭐ THAT THIS RULE HAS RUN, as a PROPOSITION and not only as a
        # licence.
        # → docs/design/machine.md#that-this-rule-has-run-as-a-proposition-and
        if app.rule.node not in self._exercised:
            self._exercised.add(app.rule.node)
            self.gate.write(
                self.g.rel(self.EXERCISED, app.rule.node), PLUS,
                licence=licence, source=self.KB, mention=True,
            )
        if app.rule.connective == "causes":
            # ⭐ A `causes` rule lands in a LATER moment, so applying one advances
            # the chain. There is no register to move and nothing to say about
            # having moved it: the chain's end is where the next entry lands, and
            # `succeed` is the whole of the move. `reseat` and its `moved(?a, ?b)`
            # record went with the frame that had a seat to move.
            self.chain.succeed(self.chain.now, licence)
        mention = self._is_mention(app)

        # ⭐⭐⭐ §6's price, charged by §6's own test. ⚠ That is the whole of the
        # difference between the two matchers.
        # → docs/design/machine.md#6-s-price-charged-by-6-s-own-test-a
        if self.rules.is_stratum0(app.rule):
            self._mint_structure(app)
            return ()

        wrote: List[Entry] = []
        # ⭐⭐⭐ A rule may introduce a thing that did not exist. ⚠ One node per
        # distinct marker per APPLICATION, so +a(+p) and +b(+p) in one
        # consequent are about the same new thing, and two firings are about
        # two things.
        # → docs/design/machine.md#a-rule-may-introduce-a-thing-that-did-not
        marks = self._markers(app.rule)
        if marks:
            # ⚠⚠⚠ The veto runs before the MINT, not only before the deposit.
            # An application whose EVERY conclusion the gate would turn away
            # brings nothing into being: the marker-form conclusions are
            # written instead -- and refused, so the record is the one
            # `_decide_change` can resolve and the rule is refused ONCE.
            # Without this, each retry minted a fresh orphan only to have
            # every claim about it refused, forever: 297 refusals to the run
            # limit, measured, where one is the point.
            pre = [(substitute(self.g, m.pattern, app.bindings), m.sign)
                   for m in app.rule.consequent]
            if all(any(v(p, s) is not None for v in self.gate.veto)
                   for p, s in pre):
                return tuple(
                    self.gate.write(p, s, licence=licence, source=self.KB,
                                    consumed=app.consumed, mention=mention)
                    for p, s in pre)
            app = app._replace(bindings={
                **app.bindings,
                **{mk: self.g.entity() for mk in marks},
            })
        for m in app.rule.consequent:
            grounded = substitute(self.g, m.pattern, app.bindings)
            if app.rule.connective == "causes":
                self._expect(grounded, m.sign, licence)
            wrote.append(
                self.gate.write(
                    grounded,
                    m.sign,
                    licence=licence,
                    source=self.KB,  # the rule is the licence; the KB is the channel
                    consumed=app.consumed,
                    mention=mention,
                )
            )
        return tuple(wrote)

    def _mint_structure(self, app: Application) -> int:
        """A stratum-0 rule's conclusion: an ordinary interned relation
        instance, undated and unattributed. Returns how many were NEW, which is
        what makes the fixpoint detectable -- interning means a fact already
        derived mints no node.
        """
        added = 0
        for m in app.rule.consequent:
            # ⚠⚠⚠ The count is taken BEFORE substitution, and that is the whole
            # of the fixpoint.
            # →
            # docs/design/machine.md#the-count-is-taken-before-substitution-an
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
            # ⚠⚠⚠ A structural fact enters no delta, so nothing re-triggers a
            # rule that reads it.
            # →
            # docs/design/machine.md#a-structural-fact-enters-no-delta-so-noth
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
        the conclusion is minted by the shared _mint_structure. ⚠ Each LAYER to
        fixpoint before the next begins, because a negated member reads a lower
        layer and must read a finished one (RuleSet.strata).

        See docs/design/machine.md#settle-structure.
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
                        self.g, self.chain, r,
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

        current_state is §4's walk and the design calls it the single most
        consequential cost: it collects every proposition the chain has ever
        claimed on this branch and resolves each one. ⚠ Order is part of the
        answer here too, and more sharply than in matching.

        See docs/design/machine.md#kept.
        """
        # ⭐⭐⭐ What is in mind, for FACTS. The agent has always narrowed which
        # rules come to mind -- dormant until something claims due -- and never
        # which facts do. ⚠ Unloading is safe to be wrong about: worst case the
        # domain comes back.
        # → docs/design/machine.md#what-is-in-mind-for-facts-the-agent-ha
        hidden = self._out_of_mind()
        seat = self.chain.now
        # ⚠ `_merges` is part of the key: a merge changes which entries answer
        # which member, and the kept state is MAINTAINED rather than rebuilt --
        # so without this the state keeps answering with the index it had
        # before two things became one.
        key = (seat.node, hidden, self.g._merges)
        cache = self._state_cache.get(key)
        if cache is None:
            props: dict = {}
            sit = Situation(self.g)
            goals: dict = {}
            # Oldest first, so the dict's insertion order is claim order and
            # reading it back reversed gives the walk's newest-first order.
            for e in reversed(current_state(self.chain)):
                if e.source in hidden:
                    continue
                # ⚠ Keyed by the proposition alone. It used to be
                # `(proposition, span)`, because two recognitions over different
                # stretches superseded nothing of each other -- and a span was a
                # LOCUS. With no locus there is one order and the later claim
                # governs, which is what §10's read always said.
                props[e.proposition] = (0, e)
                sit.add(e)
                self._count_goal(goals, e, +1)
            cache = {"pos": len(seat.delta), "props": props,
                     "sit": sit, "goals": goals}
            self._state_cache = {key: cache}
            return cache

        props, sit, goals = cache["props"], cache["sit"], cache["goals"]
        for i in range(cache["pos"], len(seat.delta)):
            e = seat.delta[i]
            if e.source in hidden:
                continue  # a domain that is not in mind
            prev = props.get(e.proposition)
            if prev is not None:
                del props[e.proposition]  # re-inserted below, so it moves to
                sit.drop(prev[1])         # the newest end of the order, and
                self._count_goal(goals, prev[1], -1)  # stops being in play
            props[e.proposition] = (i, e)
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

        ⭐⭐⭐ The loop was stateless between ticks. ⚠ And an application can stop
        being applicable, which is the part that is not merely bookkeeping.

        See docs/design/machine.md#applications.
        """
        hidden = self._out_of_mind()
        # ⚠⚠⚠ **What is in mind is part of the cache key**, and leaving it out is
        # a silent bug rather than a slow one: while a domain is dormant its
        # entries are filtered out of the delta and the cursors move past them
        # anyway. Wake the domain and those facts are behind every rule's cursor
        # forever -- so the escalation brings a domain back and the agent still
        # cannot see it. Measured exactly that way before this line existed.
        fk = (self.chain.now.node, self.chain.now.node, hidden)
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

        here = len(self.chain.now.delta)
        delta = self.chain.now.delta[cache["pos"]:]
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
                    # ⚠⚠⚠ ...and its cached applications with it, because a
                    # full re-match can only ADD.
                    # →
                    # docs/design/machine.md#and-its-cached-applications-with-it-be
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
                if (rel is self.FORBIDDEN or rel is self.REFUSED
                        or rel is self.RELATIONSHIP):
                    # A norm is not indexed by what it forbids -- _forbid
                    # consults every prohibition whose pattern shares a
                    # relation with what is about to be written, so a new one
                    # can change the answer for a proposition no cached verdict
                    # mentions.
                    # →
                    # docs/design/machine.md#a-norm-is-not-indexed-by-what-it-forbids-fo
                    cache["quiet"].clear()
                    cache["quiet_by_prop"].clear()
                    cache["live"] = set()
                    cache["bucket"] = {}
                    for k in cache["apps"]:
                        self._revive(cache, k)
            # An absence has no entry to pivot on, so the incremental pass
            # cannot see it flip: a claim about its relation -- either sign,
            # because an assertion ends an absence and a denial can begin one
            # -- re-matches the whole rule, the same move structure growing
            # makes above.
            flipped = {self.g.relation_of(e.proposition) for e in delta}
            for r in self.rules.rules:
                if any(mm.sign == ABSENT
                       and self.g.relation_of(mm.pattern) in flipped
                       for mm in r.antecedent):
                    cache["rule_pos"].pop(r.node, None)
            for k in suspect:
                app = cache["apps"].get(k)
                if app is None:
                    continue
                alive = all(
                    self.chain.resolve(c.proposition)
                    is c
                    for c in app.consumed
                )
                if not alive:
                    self._retire(cache, k)

        # 2. Full match for rules newly come to mind; delta match for the rest.
        # ⚠⚠⚠ The position is PER RULE, and a global one is wrong.
        # →
        # docs/design/machine.md#2-full-match-for-rules-newly-come-to-mind-delt
        deltas: dict = {}
        for r in proposed:
            start = cache["rule_pos"].get(r.node)
            cache["rule_pos"][r.node] = here
            if start is None:
                found = match(
                    self.g, self.chain, r, state,
                    computes=self.rules.computes,
                    structural=self.rules.skeleton(),
                )
            elif start < here:
                if start not in deltas:
                    deltas[start] = Situation(self.g, [
                        e for e in self.chain.now.delta[start:here]
                        if e.source not in hidden
                    ])
                found = match(
                    self.g, self.chain, r, state,
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
                # The stamp, assigned once and never recomputed: an entry's
                # node is minted from a monotonic counter at deposit, so
                # descending node order IS most-recently-claimed-first.
                # →
                # docs/design/machine.md#the-stamp-assigned-once-and-never-recomputed-a
                cache["seq"] += 1
                heapq.heappush(
                    cache["bucket"].setdefault(r.node, []),
                    (tuple(-c.node for c in a.consumed), _stamp(a), cache["seq"], k),
                )
                for w in self._wants(a):
                    cache["by_want"].setdefault(w, set()).add(k)
                for c in a.consumed:
                    cache["by_prop"].setdefault(c.proposition, set()).add(k)

        # ⚠⚠⚠ Order is part of the answer, not a detail of how it was found.
        # → docs/design/machine.md#order-is-part-of-the-answer-not-a-detail
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
        # ⭐⭐⭐ Only what could still have something to do. ⚠ ...except when the
        # rule set uses supersedes, which compares CONSUMED ENTRIES between two
        # applications and therefore cannot be answered from a list one of...
        # → docs/design/machine.md#only-what-could-still-have-something-to-do
        keys = (cache["apps"] if self.rules.precedence(self.SUPERSEDES)
                else cache["live"])
        out = [cache["apps"][k] for k in keys if k[0] in live]
        out.sort(key=lambda a: (rank[a.rule.node],
                                tuple(order.get(c.node, last) for c in a.consumed)))
        # ⚠⚠⚠ What defeat must NOT be given is this list, and that is the whole
        # difficulty of the change.
        # → docs/design/machine.md#what-defeat-must-not-be-given-is-this-li
        return out

    def _materialise(self, proposed: List[Rule], state: Situation) -> List[Application]:
        """The candidate list as `tick` used to build it: every live application,
        defeated and filtered, in the order arbitration read them.

        Nothing in the loop calls this. It exists because `_choose` is an
        optimisation of a semantics, and §20's floor gate is the standing answer
        to that: the slow definition has to stay, so the fast one can be held to
        it rather than trusted. the retired `ugm.arbitration` ran both on every tick of
        every fixture and compares the move.
        """
        out = self._applications(proposed, state, materialise=True)
        out = defeat(self.rules, out, self._matched_rules.values())
        out = [a for a in out if not self._passed_up(a)]
        out = [a for a in out if self._would_change(a)]
        # ⚠⚠⚠ Sorted, because arbitrate picks the FIRST among applications of
        # one rule and until now nothing said which that was.
        # → docs/design/machine.md#sorted-because-arbitrate-picks-the-firs
        return sorted(out, key=_order_key)

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

        The rule and the entries it consumed -- not its bindings.

        See docs/design/machine.md#instantiation.
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
        # deposit, so "a forbidden entry never exists, not even briefly".
        # → docs/design/machine.md#a-refused-write-never-happened-19-runs-the-v
        if wrote and all(
            self.g.relation_of(e.proposition) is self.gate.REFUSED for e in wrote
        ):
            return
        concluded = tuple(e.proposition for e in wrote if e.sign == PLUS)
        self._spent[key] = (app.rule.node, app.consumed, concluded)
        # ...and RETIRE it, rather than leaving it in the candidate set to be
        # skipped.
        # → docs/design/machine.md#and-retire-it-rather-than-leaving-it-in-the
        for cache in self._match_cache.values():
            cache["live"].discard((app.rule.node, frozenset(app.bindings.items())))
        for p in concluded:
            self._spent_by_prop.setdefault(p, set()).add(key)
        if app.consumed:
            self._note(self.g.rel(
                self.SPENT, app.rule.node,
                self.g.rel(self.PREMISES, *sorted(e.node for e in app.consumed))))

    def _contest(self, e: Entry) -> None:
        """The price of refraction, paid rather than accepted.

        Firing once turns a loud contradiction into a silent one. <grant>'s
        runaway was not a rule misbehaving: implies says *whenever A, B*, and
        the corpus asserted -B while A still held.

        See docs/design/machine.md#contest.
        """
        if e.sign != MINUS:
            return
        for key in list(self._spent_by_prop.get(e.proposition, ())):
            rule_node, consumed, _ = self._spent[key]
            if not all(
                self.chain.resolve(c.proposition) is c
                for c in consumed
            ):
                continue  # the premises moved: the rule may run again on its own
            self._note(self.g.rel(self.CONTESTED, rule_node, e.proposition),
                       licence=self.g.rel(self.APPLIED, rule_node))

    def _markers(self, rule) -> Tuple[NodeId, ...]:
        """The `+kind` marks in a rule's consequent, cached on the rule node.

        Scanned rather than declared, so a corpus writes `+person` where it
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
        # ⚠⚠⚠ An absence is re-asked at the door. A candidate matched while
        # `no p` held may be applied ticks later, and nothing consumed records
        # the absence -- there is no entry to go stale, so the premises-still-
        # current check cannot catch it. Skeleton relations are exempt: their
        # absence was evaluated by a walker, and BUILDING the proposition to
        # re-ask would derive the very structure asked about.
        absent = [m for m in app.rule.antecedent if m.sign == ABSENT]
        if absent:
            skel = self.rules.skeleton()
            for m in absent:
                if self.g.relation_of(m.pattern) in skel:
                    continue
                e = self.chain.resolve(
                    substitute(self.g, m.pattern, app.bindings))
                if e is not None and e.sign == PLUS:
                    return False
        return self._instantiation(app) not in self._spent

    def _would_change(self, app: Application) -> bool:
        """Quiescence: an application that restates what the chain already says is

        not a step. Without this the loop would reapply every rule forever, and
        *nothing left to do* would be unsayable. ⭐⭐⭐ And it was the agent
        recomputing its entire option set on every move. ⚠ What the measurement
        corrected.

        See docs/design/machine.md#would-change.
        """
        # ⚠⚠⚠ A stratum-0 verdict is never cached, and finding out why took a
        # runaway.
        # → docs/design/machine.md#a-stratum-0-verdict-is-never-cached-and-f
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
        # ⚠⚠⚠ A stratum-0 rule is asked about the GRAPH, not the state.
        # → docs/design/machine.md#a-stratum-0-rule-is-asked-about-the-graph
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
                # antecedent never bound, and there is nothing to deposit.
                # →
                # docs/design/machine.md#genuinely-generic-the-rule-s-consequent-names-s
                return False
            touched.append(grounded)
            # The verdict predicts what the GATE will do, so it asks the gate's
            # own vetoes -- `_forbid`, and the world model's
            # `_only_among_ids` -- rather than one of them.
            forbidding = next(
                (f for v in self.gate.veto for f in (v(grounded, m.sign),)
                 if f is not None), None)
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
                if self.chain.resolve(record) is None:
                    return True
                continue
            cur = self.chain.resolve(grounded)
            if cur is None or cur.sign != m.sign:
                return True
        return False

    def _is_mention(self, app: Application) -> bool:
        """Is this application talking ABOUT rules rather than in them?

        §14 says the use/mention distinction is settled by *who is writing* --
        the machinery reifying a rule mentions, a rule's consequent uses.

        See docs/design/machine.md#is-mention.
        """
        return app.rule.mentions or any(e.mention for e in app.consumed)

    # -- asking -----------------------------------------------------------

    def web(self, rules=None) -> Tuple[dict, dict]:
        """For each relation name: how often it is READ (an antecedent member)

        and WRITTEN (a consequent member, or a fact deposited). ⭐⭐⭐ Meaning in
        an open class is given by the web. ⚠ A VARIABLE in relation position is
        not a name, and reporting one was this instrument's own bug.

        See docs/design/machine.md#web.
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
        since nobody reads an answer. That was `ugm.harmony`'s false-positive
        shape arriving again. This direction reports **zero** on every corpus
        here, and one on a corpus with a typo in it.
        """
        read, written = self.web(rules)
        return sorted(n for n in read
                      if not written.get(n) and n not in self.reserved)

    def holds(self, proposition: NodeId) -> Optional[str]:
        """What the agent believes about this proposition, or None.

        ⚠ It used to take a `locus` -- *what did you believe THEN* -- and that
        went with the locus itself. History is not lost: `in_delta`, `pred`,
        `anc` and `entry_of` are ordinary structural relations, so asking about
        the past is a rule a corpus writes rather than a second Python read.
        """
        return self.chain.holds(proposition)

    # -- experience -------------------------------------------------------

    def review(self) -> List[Tuple[Rule, NodeId]]:
        """*Which rules earned the outcome?* -- asked of a finished episode.

        Offline, and that is a position rather than an implementation detail.

        See docs/design/machine.md#review.
        """
        rule_at = self._statements()
        earned: List[Tuple[Rule, NodeId]] = []
        seen_pairs = set()
        for s in current_state(self.chain):
            if s.sign != PLUS or self.g.relation_of(s.proposition) is not self.GOAL:
                continue
            wanted = self.g.member(s.proposition, 0)
            key = self.g.relation_of(wanted)
            if key is None:
                continue
            got = self.chain.resolve(wanted)
            if got is None or got.sign != PLUS:
                # Nothing was achieved, so there is nothing to credit. Note what
                # this does NOT do: blame. A rule that was applied on a failed
                # episode was not thereby wrong -- the episode may have been
                # impossible -- and §19's whole argument against training recall
                # on its own outputs applies twice as hard to training it on its
                # own failures.
                continue
            for node in self._support(wanted):
                e = self.chain.resolve(node)
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
                    self.g.rel(self.HELPED, rule.node, key), PLUS,
                    licence=self.g.rel(self.ACHIEVED, wanted), source=self.KB,
                    mention=True,
                )
        return earned

    def blame(self) -> List[Tuple[Rule, NodeId]]:
        """*Which rules cost the agent something it wanted?* -- the other half,

        and the one that only exists because a task is split into subgoals.
        Failure at episode level has no author.

        See docs/design/machine.md#blame.
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
        for s in current_state(self.chain):
            if s.sign != PLUS or self.g.relation_of(s.proposition) is not self.GOAL:
                continue
            wanted = self.g.member(s.proposition, 0)
            if self.g.has_var(wanted):
                continue
            key = self.g.relation_of(wanted)
            got = self.chain.resolve(wanted)
            if key is None or got is None or got.sign != MINUS:
                continue
            for node in self._support(wanted) | {wanted}:
                e = self.chain.resolve(node)
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
            e = self.chain.resolve(p)
            if e is None:
                continue
            for s in self.chain.trail(e):
                frontier.append(s.proposition)
        return seen

    def learned(self, score: int = 3, conditional: bool = False) -> List[str]:
        """What this episode has to say to the next one, as surface text.

        Offline learning crossing an episode boundary is a corpus being
        written, and a corpus is text -- so what an agent learned is readable,
        editable and arguable rather than a weight somewhere. ⚠ Credit is not
        written any more, and that is a loss, stated.

        See docs/design/machine.md#learned.
        """
        rows: List[str] = []
        harmed = {rule.node for rule, _ in self.blame()}
        if conditional:
            # ⭐ The conditional form: a learned RULE instead of a learned fact,
            # which is the whole of what "generalisation" turns out to mean here.
            # A tree's root-to-leaf path IS a rule and its internal nodes are
            # antecedent members; what the leaf concludes is now attention.
            return self._advice_rows(
                self._circumstances(self._choosers(harmed)), harmed, score)
        # ...and the half that suppression cannot supply. Measured: an episode
        # that smashed a jug for water blamed the smasher, dropped it from these
        # rows, and **smashed the jug again**, because omitting a rule leaves it
        # exactly where it was -- first in authored order.
        #
        # > **Suppression is not a decision.** It can say *do not recommend this*.
        # > It cannot say *do that instead*, and only the second changes a run.
        seen = set()
        for _rule, _binder, node, _key in self._regretted(harmed):
            if node in seen:
                continue
            seen.add(node)
            # ⚠⚠⚠ A lesson may only name something that OUTLIVES the episode.
            # A labelless entity is minted while the run goes and is a
            # different node next time, so `attention(#1501, 3)` would name
            # nothing in the episode that loads it -- and `#` opens a comment,
            # so the row would take the rest of the document with it. What is
            # dropped is said, in a line the surface can carry, because a
            # lesson that quietly lost half its rows is the failure this whole
            # file is written against.
            if node not in self.g._name:
                rows.append(f"# an unnameable node was attended and could not "
                            f"be carried: {self.g.show(node)}")
                continue
            rows.append(f"fact +attention({self.g.show(node)}, {score})")
        return rows

    def _regretted(self, harmed: set) -> List[Tuple[Rule, NodeId, NodeId, NodeId]]:
        """The passed-up alternatives, each with the node its lesson names.

        `(rule, binder, node, key)` -- the forgone rule, a held proposition that
        speaks of the salient node, that node, and the want it served. The rule
        is carried for identity and measurement only; **nothing written from
        this mentions it**, which is the point of the rewrite.

        ⚠ Tools are blamed and credited -- `_statements` puts them on the walk
        deliberately -- but never promoted. A lesson naming a tool would cost
        nothing, break nothing, and look exactly like one that works, which is
        the failure mode `ugm.bundle` exists to catch.
        """
        tools = {a.node for a in self.answerers}
        choosers = self._choosers(harmed)
        out: List[Tuple[Rule, NodeId, NodeId, NodeId]] = []
        for rule, key in self._instead_of(harmed):
            if rule.name is None or rule.node in tools:
                continue
            found = self._salient(rule, choosers)
            if found is None:
                continue
            out.append((rule, found[0], found[1], key))
        return out

    def _circumstances(self, choosers: List[Rule]) -> List[NodeId]:
        """*What about this situation made that the wrong move?*

        The tests of a learned decision tree, and they are read off the trail
        rather than engineered: the ground propositions on the support of what
        was lost, less four kinds that cannot discriminate. ⚠ All of them, as a
        conjunction, and the choice is made on which error is recoverable --
        the same judgement forgoing made.

        See docs/design/machine.md#circumstances.
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
        for s in current_state(self.chain):
            if s.sign != PLUS or self.g.relation_of(s.proposition) is not self.GOAL:
                continue
            w = self.g.member(s.proposition, 0)
            if self.g.has_var(w):
                continue
            e = self.chain.resolve(w)
            if e is not None and e.sign == MINUS:
                lost.add(w)
        for w in lost:
            for p in self._support(w):
                rel = self.g.relation_of(p)
                if rel is None or rel in skip or rel in required:
                    continue
                if p in lost or self.g.has_var(p) or p in out:
                    continue
                e = self.chain.resolve(p)
                if e is not None and e.sign == PLUS:
                    out.append(p)
        return out

    def _relations_required(self, rule: "Rule") -> set:
        """The relations a rule's antecedent names, ignoring the generic ones.

        The same read `attention._by_relation` does on the rule side of the
        lift, and for the same reason: a member that is a bare variable, or
        whose relation is a variable, is about anything, so it distinguishes
        nothing.
        """
        out = set()
        for m in rule.antecedent:
            if self.g.is_var(m.pattern):
                continue
            rel = self.g.relation_of(m.pattern)
            if rel is not None and not self.g.is_var(rel):
                out.add(rel)
        return out

    def _salient(self, alt: "Rule", choosers: List["Rule"]
                 ) -> Optional[Tuple[NodeId, NodeId]]:
        """What the passed-up route is ABOUT and the route that harmed is not.

        ⭐⭐⭐ This is the whole of what it takes to key a lesson on a NODE
        instead of on a rule, and it needs no new bookkeeping. ⚠ The test is
        the LIFT ITSELF, and it has to be, because a proxy for it wrote a
        lesson that could not work.

        See docs/design/machine.md#salient.
        """
        mine = self._relations_required(alt)
        theirs = [self._relations_required(c) for c in choosers]
        if not mine:
            return None
        held: List[NodeId] = []
        spoken: Dict[NodeId, set] = {}
        for s in current_state(self.chain):
            p = s.proposition
            rel = self.g.relation_of(p)
            if s.sign != PLUS or rel is None or self.g.has_var(p):
                continue
            held.append(p)
            for x in self.g.members(p):
                spoken.setdefault(x, set()).add(rel)
        best = None
        for i, p in enumerate(held):
            for x in self.g.members(p):
                # A node spoken OF, not a structure spoken of it: `sink`, never
                # `water(kettle)`. Attention ranks bindings, and a binding is a
                # node.
                if self.g.relation_of(x) is not None:
                    continue
                under = spoken.get(x, set())
                if not (under & mine) or any(under & t for t in theirs):
                    continue
                key = (len(self.g.members(p)), i)
                if best is None or key < best[0]:
                    best = (key, p, x)
        return None if best is None else (best[1], best[2])

    def _generalise(self, propositions: List[NodeId],
                    names: Optional[dict] = None) -> List[str]:
        """Render ground propositions as one generic antecedent.

        Every constant becomes a variable, shared across the conjunction so
        that completes(jug1, heirlooms), precious(jug1) becomes completes(?v0,
        ?v1), precious(?v0) -- the join is what makes it a claim about a *kind*
        of situation rather than a longer way of naming this one. ⚠ names is an
        OUT parameter, and it is not a convenience.

        See docs/design/machine.md#generalise.
        """
        names = {} if names is None else names

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
                     rows: Optional[List[str]] = None) -> List[str]:
        """One learned rule per promoted alternative, plus its `standing` line.

        ⭐⭐⭐ The BINDER is always in the antecedent, and it is what makes an
        attention lesson generalise at all. ⚠ The name carries no rule id:
        <learned-water-tap> is the want and the binder's relation.

        See docs/design/machine.md#advice-rows.
        """
        out = list(rows or [])
        seen = set()
        for _rule, binder, node, key in self._regretted(harmed):
            names: dict = {}
            members = self._generalise(list(tests) + [binder], names)
            var = names.get(node)
            if var is None:
                continue
            rel = self.g.relation_of(binder)
            name = f"learned-{self.g.show(key)}-{self.g.show(rel)}"
            if name in seen:
                continue
            seen.add(name)
            out.append(f"rule <{name}> = implies( {{ {', '.join(members)} }},"
                       f" {{ +attention({var}, {score}) }} )")
            out.append(f"fact standing(<{name}>)")
        return out

    def refine(self, cost, score: int = 3) -> List[str]:
        """Drop the tests that do not pay. §4's *compose what never surprised*,

        from the other end: decompose what turns out not to matter. ⚠ What this
        is NOT is mutation.

        See docs/design/machine.md#refine.
        """
        harmed = {rule.node for rule, _ in self.blame()}
        tests = self._circumstances(self._choosers(harmed))

        def rows_for(keep: List[NodeId]) -> List[str]:
            return self._advice_rows(keep, harmed, score)

        # ⚠⚠⚠ STEEPEST descent, not first-improvement, and the difference is
        # not a refinement of a refinement -- it decides whether this works at
        # all.
        # → docs/design/machine.md#steepest-descent-not-first-improvement-and
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
            e = self.chain.resolve(node)
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
        was available, because the rule that was passed up never ran and so is
        on no trail. Forgoing already recorded it. ⚠ An alternative that is
        itself blamed earns nothing; learned filters both halves through the
        same suppression, so a world whose every route does damage...

        See docs/design/machine.md#instead-of.
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
            e = self.chain.resolve(node)
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

        were read. ⭐⭐⭐ There is no journal. The first version kept one: a
        Python list of everything that came in.

        See docs/design/machine.md#rendered.
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

        # ⚠⚠⚠ A LABELLESS ENTITY HAS NO NAME TO RENDER, and `show` prints one
        # as `#1501` -- which the tokeniser reads as a COMMENT, so a session
        # containing one saved a file that could not be loaded back at all.
        # Found by writing the guide, which is the second time the save file
        # has been read by a person and the second defect it turned up.
        #
        # A surrogate name is the honest repair rather than a workaround: an
        # entity IS its id (docs/world-model.md), the surface has only names
        # for identity, and what has to survive the round trip is that every
        # fact about one entity lands back on ONE node. The name is a handle
        # this document mints, not a claim -- anything the corpus wanted to
        # SAY about the entity is in the facts beside it.
        taken = set(self.g._name.values())
        surrogate: Dict[NodeId, str] = {}

        def handle(n: NodeId) -> str:
            got = surrogate.get(n)
            if got is None:
                got = f"entity-{n}"
                while got in taken:  # never shadow a name the corpus wrote
                    got += "_"
                taken.add(got)
                surrogate[n] = got
            return got

        def surface(n: NodeId) -> str:
            if n in signs:
                return signs[n]
            if n in self.g._name:
                return self.g._name[n]
            rel = self.g.relation_of(n)
            if rel is None:
                # ...and an ERASED node reaches here too, printed `#7(erased)`.
                # A dangling reference is already a defect; rendering it as
                # something that reloads keeps it a defect the file can carry.
                return handle(n)
            return f"{surface(rel)}({', '.join(surface(x) for x in self.g.members(n))})"

        def member_text(m) -> str:
            # ⚠ `no p(?x)` is a WORD in sign position, so it needs the space
            # that `+p(?x)` must not have. Without it the file said
            # `noserved(?p)` -- one atom, a different rule, and no error.
            sep = " " if m.sign == ABSENT else ""
            return f"{m.sign}{sep}{surface(m.pattern)}"

        def as_text(r) -> str:
            side = lambda ms: ", ".join(member_text(m) for m in ms)
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

    def why(self, proposition: NodeId) -> List[str]:
        """*Why do you believe that, and on whose word?* -- R5.

        The trail is not a debugging aid: §12 makes it load-bearing for
        correctness, because a missing support link removes a weak link from the
        minimum and the conclusion becomes falsely confident.

        ⚠ It took a `locus` -- *why did you believe that THEN* -- and answering
        it needed the second index. What it answers now is about the chain's
        end, which is the only standpoint there is.
        """
        e = self.chain.resolve(proposition)
        if e is None:
            return []
        lines = [self._line(e)]
        for s in self.chain.trail(e):
            lines.append("  because " + self._line(s))
        return lines

    def _line(self, e: Entry) -> str:
        bits = [f"{e.sign}{self.g.show(e.proposition)}"]
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
    tests = episode._circumstances(episode._choosers(harmed))
    out = []
    for rule, binder, node, key in episode._regretted(harmed):
        # ⚠ Rendered TOGETHER, never separately. The tests and the binder share
        # variables wherever they share a constant, and that join is what makes
        # a leaf a claim about a kind of situation rather than a longer way of
        # naming this one -- `precious(?v0), completes(?v0, ?v1), tap(?v2)`.
        names: dict = {}
        members = episode._generalise(list(tests) + [binder], names)
        var = names.get(node)
        if var is None:
            continue
        out.append((rule.name, episode.g.show(key), tuple(members[:-1]),
                    members[-1], var))
    return out


def induce(episodes, cost, score: int = 3, hedge: bool = False) -> List[str]:
    """Grow a decision tree with MORE THAN ONE LEAF, from more than one episode.

    refine prunes a single path. ⚠ It still cannot ADD a test no episode saw,
    nor merge two leaves into one.

    See docs/design/machine.md#induce.
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
        for name, key, tests, binder, var in leaves(ep):
            k = (name, key, tests, binder, var)
            if k not in seen:
                seen.add(k)
                cand.append([name, key, list(tests), binder, var])

    def advice(name: str, var: str) -> str:
        """`attention(?v, n)`, or `possible(...)` when nothing was observed.

        ⭐⭐⭐ How sure is a WRAPPER, not a field, and this was the argument that
        eventually deleted grades outright. ⚠ And the test is constant-free,
        which §15 went to some trouble for: observed versus never tried is a
        distinction the trail makes, not a threshold anybody chose.

        See docs/design/machine.md#advice.
        """
        bare = f"attention({var}, {weight(name)})"
        return bare if (name in observed or not hedge) else f"possible({bare})"

    def rows_for(tree) -> List[str]:
        out = []
        for i, (name, key, tests, binder, var) in enumerate(tree):
            # ⚠ The BINDER survives every prune. A leaf may lose every test and
            # still be a rule, because the node it advises attending has to be
            # bound by something -- and a leaf pruned to its binder alone is the
            # generic depth-0 lesson, *whatever plays that part, think about it*.
            rn = f"learned-{i}-{key}-{binder.split('(')[0].lstrip('+')}"
            out.append(f"rule <{rn}> = implies( {{ {', '.join(list(tests) + [binder])} }},"
                       f" {{ +{advice(name, var)} }} )")
            out.append(f"fact standing(<{rn}>)")
        return out

    # ⭐ The synthetic row for an unproposed route is GONE, and nothing replaced
    # it.
    # → docs/design/machine.md#the-synthetic-row-for-an-unproposed-route-is

    tree = cand
    best = cost(rows_for(tree))
    while True:
        # ⚠⚠⚠ ORDER MATTERS ON A PLATEAU, and this is where the search failed.
        # Reaching the good tree needs TWO edits -- drop the unconditional leaf
        # AND drop a test -- each individually neutral.
        # → docs/design/machine.md#order-matters-on-a-plateau-and-this-is-wher
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
    """Many trees over different episodes, combined by union.

    induce grows one tree from everything the agent has been through, which
    means one unlucky episode is in every leaf it produces. ⚠ MEASURED, AND IT
    DOES NOT PAY -- one tree beats the bag.

    See docs/design/machine.md#forest.
    """
    eps = list(episodes)
    if not eps:
        return []
    n = max(1, min(trees, len(eps)))
    bags = [[eps[j] for j in range(len(eps)) if j % n != i] or eps for i in range(n)]
    grown = [induce(bag, cost, score=score) for bag in bags]

    out: List[str] = []
    for i, rows in enumerate(grown):
        for r in rows:
            # ⚠ Rename EVERY row of the tree, not the rule alone. The first
            # version prefixed the rule and left `standing(<learned-...>)`
            # pointing at the old name, and the loader refused the corpus --
            # which is `<...>` doing its job: a name that does not resolve is an
            # error, where a silently-wrong reference would have been a bug.
            r = r.replace("learned-", f"t{i}-learned-")
            if r not in out:
                out.append(r)
    return out
