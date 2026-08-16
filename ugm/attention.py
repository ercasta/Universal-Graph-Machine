"""A table-driven loop, beside the one that exists. (the author's design)

    python -m ugm.attention

The loop this repo ships weighs an option set: recall proposes, everything
matches, defeat and quiescence filter, arbitration ranks, one move is taken.
Measured, 99.6% of those candidates genuinely applied -- the option set is not
waste, it is the price of being able to say *nothing else applied*, which is
what `blocked` and `<give-up>` are built on.

The author's proposal is a different loop, and its claim is that the price is
not worth paying most of the time:

> The system need not explain why it preferred a rule. That is not reasoning,
> it is System-1. You never proceed to match all possible rules: you work the
> current table from top to bottom and stop at the first rule that matches.
> Each applied rule then spends attention -- a list of query -> buff -- which
> moves the scores of other rules. The rules stay fixed; the postconditions are
> what a learning process calibrates.

Four things the engine knows here, and none of them is semantic:

    a score per rule    ordered, tie broken by declaration order
    apply the first     highest-scoring rule whose antecedent matches
    then spend          run that rule's postconditions to move the table
    ...and STOP         if one of them said so, the run is over

No goal, no completeness, no widening. Those are corpus rules whose
postconditions reset buffs -- *refocusing* is a rule, *done* is the output of a
rule that checks against the goal. Nothing in this file knows what either is.

⭐⭐⭐ **The fourth row is `stop`, and it is what made the third mean anything.**
*Done is the output of a rule* was written here from the start and the loop had
no way to obey one: a completion check concluded and the agent carried straight
on to quiescence. `stop` is a postcondition beside `boost`, `damp` and `reset`,
so it is a row rather than a branch, and the loop still knows nothing about
goals -- only that a rule spent one. Measured on `stopping()` below: **62 moves
to 5.**

⚠⚠⚠ **And the obvious feature next door is worth nothing, which is why it is
checked rather than argued.** *Let a goal raise the priority of the rule that
checks it* moves NOTHING -- a completion check is self-gating, so it cannot
match until the thing is done, and the instant it can, widening reaches it in
the same move. Score decides which of several MATCHING rules wins; a check that
can only match at the finish line has nobody to go before.

⚠⚠ **What `stop` costs**: the shipped loop refuses to stop quietly on something
it was asked for, and this loop cannot make that refusal, because the veto is an
aggregate a rule cannot state. `stopping()` measures the loss rather than
asserting it is acceptable.

## What is deliberately NOT here

**An instruction set.** This project deleted an ISA once already; the floor is
four primitives and the standing test is that a feature adds rows rather than
branches. A postcondition is not an opcode: it is a query -- an ordinary
antecedent, parsed by the ordinary surface -- and a buff naming a rule. Buffs
are supplied from Python for now so the surface stays open until the loop has
been watched running.

**A replacement.** This is an instrument. It runs beside the shipped loop on the
same corpora and reports where they differ, which is the only way to find out
what first-match costs in conclusions rather than in theory.

## The trace

Every buff is recorded as (tick, by whom, target, delta), so the table at step
k is the defaults plus the deltas up to k. That is what makes a frozen
postcondition's effect showable after the fact -- *authority was in fact
considered* -- without the loop having to justify an ordering it does not
reason about.
"""

import os
import time
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

from .graph import NodeId
from .machine import Machine, Step
from .rules import STOP, Application, Member, Rule, Situation, match, substitute
from .text import load, load_file

# A rule the bundle marks `standing` is in the table at the default; everything
# else is in it at the floor. The author's own correction to an earlier sketch:
# do not mark a subset as *in* the table, because a rule nothing ever boosts
# would be dead, and deadness should be a thing the agent can be asked about
# rather than a thing the table quietly enforces.
STANDING = 10
FLOOR = 1

# How close is close, and how many rules may be in one window. Both are knobs,
# so in a corpus both are facts -- `tolerance(2)` already is one. The window is
# a PREFIX of the table: scores only fall as you go down it, so once a match is
# found at `s`, everything below `s - TOLERANCE` is irrelevant without being
# matched. The cap is a guard against a pathological table where forty rules
# sit on one score, not the mechanism.
TOLERANCE = 2
WINDOW = 3

# How many rules are matched before the loop admits its table was wrong. The
# author's proposal, and it is what makes the design's performance claim
# testable: score FIRST, then match only the top of the table. Everything below
# is never matched at all -- unless nothing up here applies, and then the
# shortlist widens.
#
# Widening is the guarantee that keeps this honest, and it is the shipped rule:
# *a dry shortlist is not a finished search*. Without it a miss in the top N
# would deposit `quiet` while work remained, the agent would give up on goals it
# could have reached, and the trail would show a completed search that never
# ran. With it, the worst case is exactly today's cost and the best case is N.
SHORTLIST = 5

# The range a shortlist's own scores are mapped onto before a reranker's nudge
# is added to them. Small enough that a nudge can move something, wide enough
# that a strong preference is not thrown away.
NORM = 6

# How long a buff lives, and how far a rule may be lifted.
#
# **Life.** A buff that never expires is what made the taught table run away:
# `A` lifts `R`, `R` lifts `A`, and every lift is permanent, so the loop finds
# work for ever. A lift is about what is going on NOW -- the author's *what I
# was doing is part of my representation of the world* -- so it fades. What
# survives is the postcondition, which re-applies whenever its query holds
# again.
#
# **Saturation.** A boost shrinks as the rule is already lifted, which is the
# useful half of a sigmoid: a monotone transform applied when the table is READ
# cannot change any ordering, and ordering is all the table is for. Applied at
# the UPDATE it bounds the scale -- and the scale has to be stable or
# `tolerance` stops meaning anything. Measured: the runaway fired **0 doubts**
# against 13 untaught, because nothing was ever close to anything again.
LIFE = 12
MAX_LIFT = 12

# The default doubt-settling rule, and the author's correction to an earlier
# sketch of mine: the loop does not need to HOLD a tick waiting for doubt to be
# resolved, because a settling rule fires. Depositing the doubt IS the move;
# this rule gets the next turn, and what it does is spend attention -- so the
# settlement is a buff like every other, calibratable and learnable rather than
# a branch. A corpus replaces it with something better (ask the user, apply a
# domain criterion) by writing a rule that outscores it.
#
# `?a` in the buff is the winner as the doubt named it. That is only writable
# because rules are subjects here -- `close(<A>, <B>)` names them -- and because
# `_note` deposits it as a MENTION, so a rule concluding about `?a` is not
# dropped by quiescence as having nothing to deposit.
SETTLE = """
rule <settle-doubt> = implies( { +close(?a, ?b) }, { +settled(?a, ?b) } )
frozen after <settle-doubt> => boost(?a, 1)
"""
SETTLING = ("settle-doubt",)


class Buff(NamedTuple):
    """What a postcondition does: move one rule's score.

    `target` is a rule's name as `<...>` writes it -- or a VARIABLE the query
    bound, which is what makes a doubt-settling rule writable at all: the doubt
    is about two rules nobody knew when the postcondition was authored, so
    `boost(?a, 1)` has to mean *the rule this query found*. That works because
    rules are already subjects here: `close(<A>, <B>)` names them, and a
    conclusion naming a rule is a mention -- the case that was invisible to the
    matcher until this session.
    """

    target: str  # `<name>`, or `?var` bound by the postcondition's query
    delta: int


class Post(NamedTuple):
    """A postcondition: a query, and what it does to the table if the query
    holds. `query` is the name of a rule authored in the corpus whose
    ANTECEDENT is the query -- so the surface parses it, and this file adds no
    notation. Such rules never enter the table.

    `frozen` marks what a calibration process may not touch. It changes nothing
    about how the postcondition runs, and it is recorded on the trace.
    """

    of: str  # the rule this hangs off
    query: Optional[str]
    buffs: Tuple[Buff, ...]
    frozen: bool = False


class Spend(NamedTuple):
    tick: int
    by: str
    target: str
    delta: int
    frozen: bool


class Table:
    """Scores over rules, ordered, with the trace that rebuilds them."""

    def __init__(self, g, rules: Sequence[Rule], standing: set) -> None:
        self.g = g
        self.name_of: Dict[NodeId, str] = {}
        self.score: Dict[NodeId, int] = {}
        self.rank: Dict[NodeId, int] = {}
        self.by_name: Dict[str, Rule] = {}
        for i, r in enumerate(rules):
            self.score[r.node] = (
                STANDING if (r.node in standing or r.name in SETTLING) else FLOOR
            )
            # Declaration order, first declared winning. This is §18's tiebreak
            # already -- authored order -- and it is not decorative: two thirds
            # of this agent's arbitrations are settled by the order of the
            # bundle file. ⚠ It can only BE the tiebreak because buffs do the
            # specificity work: `bird -> flies` declared before
            # `penguin -> flightless` wins for ever unless something lifts the
            # specific rule.
            self.rank[r.node] = i
            if r.name:
                self.by_name[r.name] = r
                self.name_of[r.node] = r.name
        self.rules = list(rules)
        self._defaults = dict(self.score)
        self.trace: List[Spend] = []
        # Why the run ended, if a postcondition ended it. A name rather than a
        # flag, because *why did you stop?* has to be answerable -- the same
        # reason the shipped loop's `_enough` returns what was named.
        self.stopped: Optional[str] = None
        # (born, rule, delta) -- the score is DERIVED from these and the
        # defaults, so nothing has to be undone when one expires.
        self.live: List[Tuple[int, NodeId, int]] = []
        self.now = 0

    def age(self, tick: int) -> None:
        """Drop what has expired and recompute. Cheap: the live list is short
        by construction, because that is what a lift being about NOW means."""
        self.now = tick
        self.live = [b for b in self.live if tick - b[0] < LIFE]
        self.score = dict(self._defaults)
        for _born, node, delta in self.live:
            self.score[node] = self.score[node] + delta

    def clear(self, tick: int, by: str) -> int:
        """Refocusing: back to the default table. The author's own mechanism --
        a rule whose postcondition resets the buffs -- and it needs no notion of
        a goal here, because deciding when to refocus is the rule's business."""
        dropped = len(self.live)
        for _born, node, delta in self.live:
            self.trace.append(Spend(tick, by, self.name_of.get(node, "?"),
                                    -delta, False))
        self.live = []
        self.age(tick)
        return dropped

    def order(self, extra=None) -> List[Rule]:
        """Highest score first, ties by declaration order. `extra` is the
        ranking-time nudge, added but never kept: a reranker reorders what is
        in front of the agent now, and next move it is recomputed."""
        lift = extra or {}
        return sorted(
            self.rules,
            key=lambda r: (-(self.score[r.node] + lift.get(r.node, 0)),
                           self.rank[r.node]),
        )

    @staticmethod
    def _bare(name: str) -> str:
        """`<flightless>` and `flightless` name the same rule. The surface
        writes the marker, `Rule.name` does not carry it, and a buff that
        silently hits nothing is the twin-node trap in its cheapest form -- the
        run stayed green and the penguin kept flying."""
        return name[1:-1] if name.startswith("<") and name.endswith(">") else name

    def spend(self, tick: int, by: str, buffs, frozen: bool, bindings) -> None:
        for target, delta in buffs:
            if target is STOP:
                # Recorded here, obeyed by the loop. Keeping the decision out of
                # `spend` is what lets the trace stay a pure account of scores --
                # and a stop moves no score, so it must not pretend to.
                self.stopped = by
                self.trace.append(Spend(tick, by, "stop", 0, frozen))
                continue
            if target is None:  # a reset, not a buff
                self.clear(tick, by)
                continue
            node = self._target(target, bindings)
            if node is None or node not in self._defaults:
                continue
            # Saturating: how much of the intended lift is left to give. A rule
            # already at the ceiling gains nothing from being taught again,
            # which is what keeps the scale -- and therefore `tolerance` --
            # meaningful.
            lift = self.score[node] - self._defaults[node]
            room = max(0, MAX_LIFT - abs(lift))
            actual = max(-room, min(room, delta))
            if not actual:
                continue
            self.live.append((tick, node, actual))
            self.score[node] = self.score[node] + actual
            self.trace.append(
                Spend(tick, by, self.name_of.get(node, "?"), actual, frozen))

    def _target(self, target: NodeId, bindings) -> Optional[NodeId]:
        """A rule node, or a variable the query bound to one."""
        if self.g.is_var(target):
            return None if not bindings else bindings.get(target)
        return target

    def rebuilt(self, upto: int) -> Dict[NodeId, int]:
        """The table as it stood after `upto` ticks, from the defaults and the
        trace alone.

        This is what the author asked for in place of explaining a preference:
        not a justification of the ordering, which is chemistry and owes none,
        but a record from which any step's table can be reconstructed -- so that
        *authority was in fact considered* is showable after the fact. Checked
        against the live table on every run below, because a trace that has
        quietly stopped being complete is a log, not a record.
        """
        out = dict(self._defaults)
        for s in self.trace:
            if s.tick > upto:
                break
            if s.tick < self.now - LIFE + 1 and s.delta > 0:
                continue  # expired, and the trace records the life as well
            t = self.by_name.get(self._bare(s.target))
            if t is not None:
                out[t.node] = out[t.node] + s.delta
        return out


class Report(NamedTuple):
    ticks: int
    applied: List[str]
    seconds: float
    tried: int  # rules whose antecedent was matched, over the whole run
    state: set
    table: "Table"
    doubts: int = 0
    windows: List[int] = []
    widenings: int = 0
    # One `Step` per move, in the shape the option-set loop returned, so this
    # loop can BE `Machine.run` rather than sit beside it. `applied` above is
    # the same sequence as names; this carries the `Application` itself, which
    # is what a caller reading `s.applied.rule.name` needs.
    steps: List["Step"] = []


def _is_defeated(m: Machine, rule: Rule, state) -> bool:
    """Does anything that overrides this rule match here?

    ⭐ The option-set loop answered this by having matched everything already.
    A prefix scan has not, so it asks the question the other way round: read the
    rules that override this one -- precedence is read from the graph, and there
    are usually one or two -- and match only those.

    ⚠ `supersedes` is NOT here. It defeats per CASE rather than per rule: only
    the applications sharing a consumed entry with the winner are out, so it
    cannot be settled by asking whether a rule matched. It is applied where the
    applications are, below.
    """
    higher = [h for h, lower in m.rules.precedence(m.rules.OVERRIDES)
              if lower is rule]
    for h in higher:
        found = match(
            m.g, m.chain, h, m.focus.topic, m.focus.seat, state,
            computes=m.rules.computes, structural=m.rules.skeleton(),
        )
        # ⚠⚠⚠ **Matched, NOT survived**, and the difference is the whole of it.
        # `_survives` asks whether the winner still has work to do -- and once it
        # has applied, its conclusion holds, so it stops surviving and the loser
        # is suddenly undefeated. Measured: A2 applied, then A1 applied straight
        # after and overwrote it, which is exactly the failure the option-set
        # loop records as *defeat is about whose antecedent holds, not about who
        # still has work*.
        if found:
            # On the record, because *which of my rules actually fight* is a
            # question about a run that no run recorded until it was deposited.
            m._note(m.g.rel(m.DEFEATED, rule.node, h.node))
            return True
    return False


def _standing(m: Machine) -> set:
    """The rules the bundle deposits `standing(<R>)` about -- the default table,
    which already exists in all but name."""
    out = set()
    for node in m.g.instances_of(m.STANDING):
        members = m.g.members(node)
        if len(members) == 1 and m._claims(node):
            out.add(members[0])
    return out


def _queries(m: Machine, posts: Sequence[Post]) -> set:
    return {p.query for p in posts if p.query}


def run(m: Machine, posts: Sequence[Post] = (), limit: int = 400,
        reflex: bool = False, chooser=None, watch=None,
        pool: Optional[Sequence[Rule]] = None) -> Report:
    """The loop, in full. Everything else in this file is bookkeeping.

    `reflex` is the cheapest calibration imaginable and it is here to answer one
    question: can *rules matched per move* be moved at all? A rule that was
    tried and did not match is damped by one; the rule that applied is boosted
    by one. No model, no gold, no human -- just the fact that the table was
    wrong about who was worth trying, which the loop already knows for free at
    the moment it finds out. If this does not move the number, no learning will.
    """
    queries = _queries(m, posts)
    # ⭐ `pool` is what makes an EXPERT possible: one shared graph, one shared
    # chain, and a table over a SUBSET of the rules. The loop does not know what
    # an expert is -- it is handed the rules it may consider, exactly as it is
    # handed the corpus. `ugm.experts` reads the subset off the graph.
    if pool is None:
        pool = m.rules.rules
    pool = [r for r in pool if r.name not in queries]
    table = Table(m.g, pool, _standing(m))
    by_rule: Dict[str, List[Post]] = {}
    for p in posts:
        by_rule.setdefault(p.of, []).append(p)

    index = _by_target(m)
    applied: List[str] = []
    steps: List[Step] = []
    arrivals = 0
    tried = 0
    doubts = 0
    widenings = 0
    windows: List[int] = []
    t0 = time.time()
    for tick in range(limit):
        # Not a phase: the world may have spoken since the last move, and the
        # shipped loop asks the same question in the same place.
        arrivals = m.channels.since_last_tick() or 0

        # ⭐⭐⭐ **Satisfaction, ported from the tick this loop replaces.** `stop`
        # is the rule-level route and it stays the recommended one -- a rule
        # concludes that here is over and its postcondition ends the run. This
        # is the other half, and it is here rather than as a rule because the
        # **open-goal veto is an aggregate**: *nothing else is wanted and unmet*
        # is a claim about a set, and a rule cannot speak about the set of its
        # own matches. `Machine._enough` already reads `enough(...)` at the
        # focus and exercises the veto once per seat, so this calls it rather
        # than growing a second copy.
        #
        # ⚠ Inside a hypothesis, enough ends the BRANCH and not the run -- which
        # is `_leave`, the door that already existed, and is how *is this plan
        # settled* gets a local answer.
        #
        # ⚠ And it deliberately writes no `quiet`. `quiet` continues the loop so
        # a watchdog can key on it, because *the search finished* leaves work
        # worth doing and *nothing more is worth doing* does not.
        reason = m._enough()
        if reason is not None:
            if m._leave():
                steps.append(Step(arrivals, 0, tried, None, (), "supposed"))
                continue
            m._halt(reason)
            steps.append(Step(arrivals, 0, tried, None, (), "stopped"))
            break

        state = m._situation()
        table.age(tick)

        window: List[Application] = []
        top = None
        ordered = table.order()
        cut = 0
        while cut < len(ordered) and not window:
            # One shortlist at a time. Score decides WHO is matched, which is
            # the whole proposal: a rule below the cut costs nothing at all.
            chunk = ordered[cut:cut + SHORTLIST]
            # ...and the shortlist is reordered by what is in front of the
            # agent now. Ephemeral: recomputed for each shortlist and kept
            # nowhere, so there is no decay to tune and no runaway to guard
            # against -- the difference between the two kinds of attention.
            chunk, tried = _rerank(m, table, state, chunk, index, tried)
            if cut:
                widenings += 1
            cut += SHORTLIST
            missed: List[Rule] = []
            for r in chunk:
                if top is not None and table.score[r.node] < top - TOLERANCE:
                    break  # the prefix ends here, and the rest is not matched
                tried += 1
                found = match(
                    m.g, m.chain, r, m.focus.topic, m.focus.seat, state,
                    computes=m.rules.computes,
                    structural=m.rules.skeleton(),
                )
                # `_survives` is the shipped per-candidate filter: passed up,
                # quiescent, or already spent on these premises. Refraction
                # stays, because *this instantiation has run* is not the same
                # claim as *this rule's score is low*, and keying firing-once to
                # the rule would stop it ever applying to new data.
                # ⭐⭐⭐ **Defeat, and it was MISSING -- which the corpus-level gate
                # could not see.** `_survives` is the per-candidate filter and
                # says so in its own docstring: defeat is per RULE, applied once
                # per rule by the chooser this loop replaced. So a prefix scan
                # dropped `overrides` entirely, and 65 checks said so the moment
                # this loop became the loop.
                #
                # ⚠⚠ The gate agreeing was not wrong, it was WEAK: it compares
                # final conclusions, and a loop that runs to quiescence applies
                # the loser eventually anyway -- *ordering is not defeasibility*,
                # this design's own line, arriving as an instrument defect. Two
                # loops can agree about every conclusion and disagree about
                # whether a rule was defeated.
                #
                # The repair keeps the prefix scan: `overrides(A, B)` needs to
                # know whether A matched, and A's defeaters are a SMALL set read
                # off the graph -- so match those rather than the pool. A join,
                # not a scan, which is this repository's standing answer.
                if _is_defeated(m, r, state):
                    missed.append(r)
                    continue
                hit = False
                for a in found:
                    if m._survives(a):
                        window.append(a)
                        hit = True
                        if top is None:
                            top = table.score[r.node]
                        break
                if not hit:
                    missed.append(r)
                if len(window) >= WINDOW:
                    break
            if reflex:
                for r in missed:
                    # The DELTA ACTUALLY APPLIED goes on the trace, not the one
                    # intended: the floor clamps it, and recording the intent
                    # made the trace unable to rebuild the table. Caught by the
                    # assertion below the first time it ran, which is what that
                    # assertion is for.
                    was = table.score[r.node]
                    table.score[r.node] = max(0, was - 1)
                    table.trace.append(
                        Spend(tick, "reflex", r.name, table.score[r.node] - was,
                              False))
        if not window:
            # Nothing in the table matched. The engine says so and nothing
            # more: `quiet(<seat>)` is a fact about the machinery, like the
            # doubt, and it is what every rule that reacts to the loop having
            # stopped is waiting for -- `<give-up>`, the watchdogs, `blocked`.
            # Without it the bundle never gets its turn, which is why the first
            # version of this loop never acted at all on `quest-p1`.
            # ⭐⭐⭐ **Effort, and the order is the old tick's exactly.** A
            # shortlist that ran dry is not a search that finished, and neither
            # is a search that never looked at what it had put out of mind. Both
            # deposit -- `widened(<seat>)`, `reached(<seat>)` -- so *I had to go
            # and get that* is a sentence a corpus can write.
            #
            # ⚠ These are NOT ported logic. They are the loop reporting its own
            # event, which is the same shape as `quiet` and `arrived`: the
            # smallest unarguable record of something only the loop can know.
            # `Machine._widen` already reads the budget knob off the graph and
            # guards once per seat, so this calls it rather than growing a
            # second copy that would drift.
            if m._widen():
                steps.append(Step(arrivals, 0, tried, None, (), "widened"))
                continue
            if m._recover():
                steps.append(Step(arrivals, 0, tried, None, (), "widened"))
                continue
            if m._wake():
                steps.append(Step(arrivals, 0, tried, None, (), "quiet"))
                continue
            # ...and the register: nothing more applies HERE, and here may be
            # inside a supposition. Moving the register is chemistry -- the
            # same move `causes` makes -- and the decision to make it is the
            # empty window, so no notion of a goal is involved.
            if m._leave():
                steps.append(Step(arrivals, 0, tried, None, (), "supposed"))
                continue
            # The run is over, and WHICH silence it was goes on the record: the
            # option-set loop's callers read `steps[-1].state` in 33 places to
            # tell a finished search from one that hit the limit.
            steps.append(Step(arrivals, 0, tried, None, (), "quiescent"))
            break
        windows.append(len(window))
        # Who picks. The table picks by default -- that is System 1 -- but a
        # human stepping the corpus by hand, or the shipped arbitration acting
        # as a gold teacher, is the same signature and the same loop. The first
        # user of a KB is a person choosing moves; the table is what that use
        # leaves behind.
        chosen = window[0] if chooser is None else chooser(m, table, window, state)
        if chosen is None:
            break
        if len(window) > 1:
            # The doubt is DEPOSITED, not recorded: an entry a rule can match,
            # so a corpus reacts to it -- tiebreaking, or asking. The machinery
            # noticing something it must not decide and depositing a fact is
            # this repo's standing answer (`unsupported`, `contested`,
            # `defeated`, `blocked`), and `close` was the one occasion that was
            # written and never reacted to.
            fresh = False
            for rival in window[1:]:
                node = m.g.rel(m.CLOSE, chosen.rule.node, rival.rule.node)
                if m.chain.resolve(node, m.focus.topic, m.focus.seat) is None:
                    m._note(node)
                    fresh = True
            if fresh:
                # Depositing IS the move. A settling rule -- the default one, or
                # a corpus's own -- is in the table and gets the next turn.
                doubts += 1
                steps.append(Step(arrivals, len(window), tried, None, (),
                                  "applied"))
                continue
            # ...and the backstop: the doubt already stands and nothing settled
            # it, so restating it changes nothing and the winner applies. A
            # corpus with no settling rule loses a tick, not the loop.
        # ⚠⚠⚠ **Something applied, so the shortlist is trusted again.** The old
        # tick resets this on every application -- *widening is a state the
        # agent is in, not a mode it is switched into* -- and this loop did not,
        # so after the first dry shortlist it never reached past one again for
        # the whole run. One line, and it is a real behavioural difference
        # rather than a record: measured, 3 widenings became 1.
        m._widened = False
        wrote = m._apply(chosen)
        m._spend(chosen, wrote)
        applied.append(chosen.rule.name or "?")
        steps.append(Step(arrivals, len(window), tried, chosen,
                          tuple(wrote or ()), "applied"))
        if watch is not None:
            # AFTER the move, not at the choice: a tick that deposits a doubt
            # chooses and then does not apply, so watching at the choice
            # recorded a rule that never ran -- and a lesson built from that
            # sequence teaches a move that never happened.
            watch(m, table, window, chosen, tick)
        if reflex:
            table.score[chosen.rule.node] = table.score[chosen.rule.node] + 1
            table.trace.append(Spend(tick, "reflex", chosen.rule.name, 1, False))
        _spend_posts(m, table, chosen, tick, state)
        if table.stopped is not None:
            steps.append(Step(arrivals, 0, tried, None, (), "stopped"))
            # *Completion is the output of a rule*, and this is the loop obeying
            # one. It knows a rule spent `stop`; it does not know what a goal is,
            # which is the line this file has held from the start.
            break
    # The trace is held to the table on every run: same scores, rebuilt from
    # the defaults and the spends alone.
    assert table.rebuilt(limit) == table.score, "the trace cannot rebuild the table"
    # ⚠ **The loop ran out of ITERATIONS, not out of work.** The first version of
    # this asked whether the last `Step` was `applied`, and the last step is
    # never `applied` -- the loop appends a `quiescent` or `stopped` step when it
    # finishes and appends nothing when the `for` simply runs out. So the test is
    # the absence of an ending: a run that finished wrote one, and a run the
    # budget cut off did not.
    #
    # A run that stops because there is nothing left to do has not been bounded
    # by anything, and saying it had would make the record useless in the other
    # direction.
    if steps and steps[-1].state == "applied":
        m.exhausted += 1
        m._note(m.g.rel(m.BOUNDED, m.TICKS))
    return Report(
        len(applied), applied, time.time() - t0, tried, _state(m), table,
        doubts, windows, widenings, steps
    )


def _by_target(m: Machine) -> Tuple[Dict[NodeId, List], List]:
    """Ranking-time triggers, indexed by the rule they lift.

    §19's own trick for norms, one level up: `_forbid` is cheap because it looks
    only at prohibitions whose relation matches what is about to be written, and
    a reranker is cheap for the same reason -- a trigger about wounds costs
    nothing on a move about doors. A trigger whose target is a VARIABLE cannot
    be indexed, because which rule it lifts is what its query decides; those are
    consulted whenever anything is.
    """
    by_target: Dict[NodeId, List] = {}
    floating: List = []
    for trig in m.rules.triggers.get(None, ()):
        targets = [t for t, _d in trig[1]]
        if any(t is None or m.g.is_var(t) for t in targets):
            floating.append(trig)
            continue
        for t in targets:
            by_target.setdefault(t, []).append(trig)
    return by_target, floating


def _rerank(m, table, state, chunk, index, tried: int):
    """Reorder THE SHORTLIST, and pay only for it.

    The author's restriction, and it is what makes reranking affordable: a
    reranker looks at the options in front of the agent and nudges them. It
    cannot pull a rule in from the bottom of the table -- widening is what
    reaches those, and a reranker applies to each shortlist as it is reached.

    Measured before the restriction: every trigger evaluated on every move cost
    fifteen extra matches a move on a scan that did not shrink, and the cost
    column read 42.7 against a 29.6 baseline.
    """
    by_target, floating = index
    wanted = []
    for r in chunk:
        wanted.extend(by_target.get(r.node, ()))
    lift: Dict[NodeId, int] = {}
    for query, buffs, _frozen in wanted + floating:
        tried += 1
        hits = match(
            m.g, m.chain, Rule(0, "implies", list(query), [], "when"),
            m.focus.topic, m.focus.seat, state,
            computes=m.rules.computes, structural=m.rules.skeleton(),
        ) if query else [None]
        for hit in hits:
            bindings = {} if hit is None else hit.bindings
            for target, delta in buffs:
                if target is None or target is STOP:
                    # A reset means nothing to a nudge that is not kept, and a
                    # stop is not a nudge at all: a reranker reorders what is in
                    # front of the agent, and ending the run is not an ordering.
                    # A corpus that wants to stop hangs it off a rule that RAN.
                    continue
                node = table._target(target, bindings)
                if node is not None and node in table.score:
                    lift[node] = lift.get(node, 0) + delta
    if not lift:
        return chunk, tried
    # ...and the shortlist is RENORMALISED before the nudge is added.
    #
    # A persistent lift runs to the saturation ceiling, so adding a nudge to it
    # changes nothing: measured, teaching both kinds together scored exactly
    # what the persistent half scored on its own while paying the reranker's
    # cost. The alternative I proposed -- let the reranker set the order -- was
    # wrong, and the author's objection is the right one: a trigger that names
    # a POSITION has to know what it is competing against, and then triggers
    # stop being independent and stop being separately learnable.
    #
    # So the scale is fixed where the comparison happens instead. Within a
    # shortlist the base scores are mapped onto [0, NORM], which is not
    # flattening -- a rule the table strongly prefers keeps its lead over one it
    # barely prefers -- but it makes habit and situation commensurable, so a
    # nudge can move something without a trigger knowing anything but its own
    # query.
    lo = min(table.score[r.node] for r in chunk)
    hi = max(table.score[r.node] for r in chunk)
    span = (hi - lo) or 1
    based = {r.node: NORM * (table.score[r.node] - lo) / span for r in chunk}
    return sorted(chunk, key=lambda r: (-(based[r.node] + lift.get(r.node, 0)),
                                        table.rank[r.node])), tried


def _spend_posts(m: Machine, table: Table, chosen: Application, tick: int,
                 state: Situation) -> None:
    """Run the applied rule's postconditions and move the table.

    The query is matched with the application's own bindings already
    substituted in, which is what makes it a POSTcondition rather than a second
    rule: `after { +penguin(?x) }` asks about the `?x` this rule just bound. A
    bare `after` has no query and holds always.
    """
    name = chosen.rule.name or "?"
    for query, buffs, frozen in m.rules.triggers.get(chosen.rule.node, ()):
        if not query:
            table.spend(tick, name, buffs, frozen, chosen.bindings)
            continue
        probe = Rule(
            chosen.rule.node, chosen.rule.connective,
            [Member(mm.sign, substitute(m.g, mm.pattern, chosen.bindings),
                    mm.locus, mm.binds) for mm in query],
            [], f"{name}-after",
        )
        for hit in match(
            m.g, m.chain, probe, m.focus.topic, m.focus.seat, state,
            computes=m.rules.computes, structural=m.rules.skeleton(),
        ):
            bound = dict(chosen.bindings)
            bound.update(hit.bindings)
            table.spend(tick, name, buffs, frozen, bound)


def _holds(m: Machine, table: Table, query: str, state: Situation):
    """Does the postcondition's query hold here? It is an ordinary antecedent,
    matched by the ordinary matcher -- the query rule is loaded with the corpus
    and kept out of the table."""
    r = table.by_name.get(query)
    if r is None:
        for x in m.rules.rules:
            if x.name == query:
                r = x
                break
    if r is None:
        return []
    return match(
        m.g, m.chain, r, m.focus.topic, m.focus.seat, state,
        computes=m.rules.computes, structural=m.rules.skeleton(),
    )


def _state(m: Machine) -> set:
    """What the agent ends up holding, as (proposition, sign). The comparison
    has to be over conclusions rather than over moves: two loops that reach the
    same beliefs by different routes agree about the world, and that is the
    question."""
    return {(m.g.show(e.proposition), e.sign) for e in m._state()}


# -- the comparison ---------------------------------------------------------

CORPORA = ("delay.ugm", "worked.ugm", "quest-p1.ugm", "dungeon")

# What the table loop is allowed not to reach.
#
# Both are claims about an option set this loop deliberately never builds.
# `close` is a doubt -- these two candidates scored within the tolerance -- and
# `forgone` is *this way of getting it was passed up*, which needs the ways not
# taken to have been materialised.
#
# ⚠ `forgone` was the harder call and the author took it. Its own check argues
# it is **a safety property before it is a learning one** -- *an act cannot be
# taken back* -- so dropping it means the agent no longer records which act it
# passed up. Written down here rather than in a commit message, because the next
# person to want it will look at this list first.
#
# ⭐⭐ **`defeated` WAS on this list and has come off it**, which is the useful
# half of the story. It was accepted as unreachable on the same grounds: one
# rule beating another needs both to have been matched. That was wrong -- the
# question can be asked the other way round. `overrides(A, B)` needs to know
# whether A matched, A's overriders are read off the graph and there are usually
# one or two, so `_is_defeated` matches THOSE rather than the pool. A join, not
# a scan, and the prefix survives.
#
# ⚠ The list is short on purpose and every addition is a decision, not a
# convenience. Anything else the table loop fails to conclude is a rule that has
# not been written yet, and the gate below says so.
ACCEPTED_LOSSES = frozenset({"close", "forgone"})


DEFAULT_POSTS = (Post("settle-doubt", None, (Buff("?a", 1),), frozen=True),)


def _load(name: str, settling: bool = False) -> Machine:
    m = Machine()
    load_file(m, os.path.join(os.path.dirname(__file__), "rules", name))
    if settling:
        load(m, SETTLE)
    return m


def _fight(run_it: bool):
    """The dungeon, which is the largest corpus here -- 21 rules of its own, a
    fight that takes tens of moves, and three tools. It cannot be loaded from
    the file alone: `<dice>`, `<arith>` and `<beats>` are answerers registered
    in Python, so the machine is built the way `ugm.dungeon` builds it and only
    the loop differs."""
    from . import dungeon

    m, _kb, _asked = dungeon.fight(seed=7, limit=400 if run_it else 0)
    return m


def compare(name: str) -> dict:
    """Both loops on one corpus, from the same text."""
    if name == "dungeon":
        t0 = time.time()
        a = _fight(True)
        shipped = {"ticks": a.selections, "seconds": time.time() - t0,
                   "state": _state(a), "applied": []}
        b = _fight(False)
        load(b, SETTLE)
        r = run(b, limit=400)
        return {"corpus": name, "shipped": shipped, "table": {
            "ticks": r.ticks, "seconds": r.seconds, "state": r.state,
            "tried": r.tried, "applied": r.applied,
            "doubts": r.doubts, "windows": r.windows,
            "widenings": r.widenings}}
    a = _load(name)
    t0 = time.time()
    steps = a.run(limit=400)
    shipped = {
        "ticks": len(steps),
        "seconds": time.time() - t0,
        "state": _state(a),
        "applied": [s.applied.rule.name for s in steps if s.applied is not None],
    }
    b = _load(name, settling=True)
    r = run(b)
    return {
        "corpus": name,
        "shipped": shipped,
        "table": {
            "ticks": r.ticks, "seconds": r.seconds, "state": r.state,
            "tried": r.tried, "applied": r.applied,
            "doubts": r.doubts, "windows": r.windows,
            "widenings": r.widenings,
        },
    }


PENGUIN = """
fact bird(tweety)
fact bird(pingu)
fact penguin(pingu)
fact asked(pingu)

rule <flies>      = implies( {{ +bird(?x), +considered(?x) }},    {{ +can_fly(?x) }} )
rule <flightless> = implies( {{ +penguin(?x), +considered(?x) }}, {{ +grounded(?x) }} )
rule <classify>   = implies( {{ +asked(?x) }},                    {{ +considered(?x) }} )
{post}
"""

CALIBRATED = "after <classify> { +penguin(?x) } => boost(<flightless>, 20)"


def penguin() -> int:
    """The author's example, and it found the mechanism's real boundary.

    `<flies>` is declared first, so under declaration order it wins for every
    bird, penguin included. Nothing about the tiebreak can fix that -- the
    general rule IS the more foundational one, which is what declaration order
    says. The specificity has to come from a buff.

    **But ordering alone is not defeasibility, and running it is how that
    showed.** A loop that continues to quiescence applies BOTH rules whatever
    the order: a low score delays a rule, it never removes one, and removal is
    the thing this design refuses on purpose (preference orders, it does not
    exclude). So the penguin comes out flying and grounded, twice, and the buff
    changes nothing you can see.

    What makes the order into a default is **stopping**: ask, take the first
    rule that matches, act on it. That is the System-1 reading taken seriously,
    and it is why *completion is the output of a rule* is not a detail of the
    author's design -- it is what turns a score into a default. Below, one move
    per question.
    """
    print()
    print("  the penguin -- ask, and take the first rule that matches")
    wrong = 0
    for post in ("", CALIBRATED):
        m = Machine()
        load(m, PENGUIN.format(post=post))
        load(m, SETTLE)
        r = run(m, limit=6)
        first = next((x for x in r.applied if x in ("flies", "flightless")), "-")
        answer = {"flies": "can_fly(pingu)", "flightless": "grounded(pingu)"}
        label = "with the postcondition" if post else "declaration order alone"
        print(f"    {label:24} {r.doubts} doubt(s), applied {r.applied}")
        print(f"    {'':24} first answer -> {answer.get(first, '-')}")
        if post and first != "flightless":
            wrong += 1
    return wrong


# -- stopping, which is what makes a score mean anything --------------------

_IDLE = "\n".join(
    "rule <f%d> = implies( { +wood(?x) }, { +step%d(?x) } )" % (i, i)
    for i in range(1, 13))
_DEEP = "\n".join(
    "rule <g%d> = implies( { +step%d(?x) }, { +after%d(?x) } )" % (i, i, i)
    for i in range(1, 13))

# ⚠ `want`, not `goal`. `goal` is the apparatus's own relation and the backward
# reader deposits its own, so a completion check written over `goal(?w)` fires
# on the machinery's subgoals -- measured, and it reported the check firing
# BEFORE the thing was built. A corpus's vocabulary is not the apparatus's.
STOPPING = """
fact +want(assembled(cart))
fact +wood(cart)
rule <wheel> = implies( { +wood(?x) },       { +have(wheel) } )
rule <axle>  = implies( { +have(wheel) },    { +have(axle) } )
rule <bed>   = implies( { +have(axle) },     { +have(bed) } )
rule <build> = implies( { +have(bed) },      { +assembled(cart) } )
rule <done>  = implies( { +want(?w), +?w },  { +finished(?w) } )
""" + _IDLE + "\n" + _DEEP + "\n"

# Two things wanted, one reachable: the stop fires on the one that was built
# while the other is still wanted and still unmet.
OPEN_WANT = """
fact +want(assembled(cart))
fact +want(painted(cart))
fact +wood(cart)
rule <wheel> = implies( { +wood(?x) },       { +have(wheel) } )
rule <build> = implies( { +have(wheel) },    { +assembled(cart) } )
rule <done>  = implies( { +want(?w), +?w },  { +finished(?w) } )
after <done> => stop
"""


def _stopping_run(src, limit=400):
    m = Machine()
    load(m, src)
    load(m, SETTLE)
    return m, run(m, limit=limit)


def stopping() -> int:
    """`stop`, and the two things measuring it settled.

    This file's own design says *done is the output of a rule that checks
    against the goal* -- and the loop had no way to obey one: the check
    concluded and the agent carried straight on to quiescence. `stop` is the
    fourth thing a postcondition can spend, beside `boost`, `damp` and `reset`.
    A row, not a branch, and the loop still knows nothing about goals: it knows
    a rule said stop.

    ⭐⭐⭐ **And the trigger everyone reaches for first is worth nothing.** The
    obvious proposal -- let a goal raise the priority of the rule that checks it
    -- was built and measured before this, and it moves NOTHING. A completion
    check is **self-gating**: it cannot match until the thing is done, and the
    instant it can, widening reaches it in the same move. Score decides which of
    several MATCHING rules wins; a check that can only match at the finish line
    has nobody to go before. Measured with the check at the floor, reranked,
    buffed persistently in two places, and standing -- identical every time,
    before `stop` existed and after. The rows below keep that null result where
    the next person to propose it will find it.
    """
    print()
    print("  stopping -- a cart to build, and a check that says when it is done")
    bad = 0
    seen = {}
    cases = (
        ("", "no postcondition"),
        ("when { +want(?w) } => boost(<done>, 20)", "a trigger, and no stop"),
        ("after <done> => stop", "stop, <done> at the floor"),
        ("after <done> => stop\nwhen { +want(?w) } => boost(<done>, 20)",
         "stop, and the trigger as well"),
        ("after <done> => stop\nfact standing(<done>)",
         "stop, and <done> standing"),
    )
    for post, label in cases:
        _m, r = _stopping_run(STOPPING + "\n" + post)
        done = any(p == "finished(assembled(cart))" and sg == "+"
                   for p, sg in r.state)
        seen[label] = r.ticks
        print(f"    {label:32} {r.ticks:>4} moves   finished: {done}   "
              f"stopped by {r.table.stopped}")
        if not done:
            bad += 1
    # The claim, as a number: obeying the rule is what shortens the run.
    if seen["stop, <done> at the floor"] >= seen["no postcondition"]:
        print("    FAIL  `stop` did not shorten the run")
        bad += 1
    # ...and the null result, kept as a check so it cannot quietly come back.
    if seen["stop, and the trigger as well"] != seen["stop, <done> at the floor"]:
        print("    FAIL  the trigger changed the run -- the null result moved")
        bad += 1

    # ⚠⚠⚠ THE COST, measured rather than asserted. The shipped loop refuses to
    # stop QUIETLY on something it was asked for: an open goal outranks an
    # `enough`. This loop cannot, because that veto is an aggregate -- *nothing
    # else is wanted and unmet* -- and a rule cannot speak about the set of its
    # matches. So the guarantee becomes a corpus's, exactly as it did for norms,
    # and this is the instrument that watches it rather than a claim that it is
    # fine.
    _m, r = _stopping_run(OPEN_WANT, limit=200)
    held = {p for p, sg in r.state if sg == "+"}
    quiet_on_open = ("want(painted(cart))" in held
                     and "painted(cart)" not in held
                     and r.table.stopped is not None)
    print(f"    {'stopped with a want still open':32} {r.ticks:>4} moves   "
          f"unmet want left behind: {quiet_on_open}")
    if not quiet_on_open:
        print("    FAIL  the open-want probe has nothing to measure")
        bad += 1
    return bad


def main() -> int:
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(__doc__.split("## What is deliberately NOT here")[0].strip())
    print()
    print(f"  {'corpus':16} {'ticks':>12} {'seconds':>14} {'conclusions':>22}")
    bad = 0
    for name in CORPORA:
        c = compare(name)
        s, t = c["shipped"], c["table"]
        missing = s["state"] - t["state"]
        extra = t["state"] - s["state"]
        w = t["windows"] or [0]
        print(f"  {name:16} {s['ticks']:>5} {t['ticks']:>6} "
              f"{s['seconds']:>7.2f} {t['seconds']:>6.2f} "
              f"{len(s['state']):>10} {len(t['state']):>6}"
              f"   -{len(missing)} +{len(extra)}"
              f"   doubt {t['doubts']}/{len(w)}, "
              f"{t['tried'] / max(1, len(w)):.1f} matched/move, "
              f"{t['widenings']} widenings")
        if missing or extra:
            # By RELATION, because the interesting question is not which
            # proposition is absent but which piece of the shipped tick was
            # responsible for it. Everything this loop drops -- doubt, forgone,
            # leaving a supposition, saying `quiet` -- is machinery the author's
            # design moves into rules, so the diff is the work list.
            for label, diff in (("only shipped", missing), ("only table", extra)):
                by_rel: Dict[str, int] = {}
                for p, sign in diff:
                    by_rel[p.split("(")[0]] = by_rel.get(p.split("(")[0], 0) + 1
                if by_rel:
                    worst = sorted(by_rel.items(), key=lambda kv: -kv[1])[:6]
                    print(f"      {label:12} " +
                          ", ".join(f"{k} x{v}" for k, v in worst))
        # ⭐⭐⭐ **And now it is a GATE, which it was not.** This block printed the
        # diff and `bad` was never touched -- so *the table loop reaches the same
        # conclusions* was asserted nowhere, by anything, while being the whole
        # premise of replacing the other loop with it. A comparison that cannot
        # fail is this repository's most-recorded instrument defect, and it was
        # sitting in the one place that has to be trustworthy before any Python
        # is deleted.
        #
        # The claim, stated so it can be wrong: **the table loop may conclude
        # MORE than the option-set loop. It may not conclude LESS**, except for
        # the two records that exist only because the other loop materialises an
        # option set, and which the author accepted losing.
        unexplained = sorted(p for p, _sign in missing
                             if p.split("(")[0] not in ACCEPTED_LOSSES)
        if unexplained:
            print(f"      FAIL  {len(unexplained)} conclusion(s) lost that are "
                  f"not an accepted loss: {unexplained[:4]}")
            bad += 1
    print()
    print("  option-set | table, per column. The gate is one-sided on purpose:")
    print("  the table loop may conclude MORE, and may not conclude LESS except")
    print(f"  for {', '.join(sorted(ACCEPTED_LOSSES))} -- records that exist only because the")
    print("  other loop materialises an option set. Everything else it drops is")
    print("  a rule still to write, and that list is a failure rather than a note.")
    return bad + penguin() + stopping()


if __name__ == "__main__":
    raise SystemExit(main())
