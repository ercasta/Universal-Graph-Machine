"""A table-driven loop, beside the one that exists. (the author's design)

    python -m ugm.core.attention

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
postconditions spend attention -- *refocusing* is a rule (`unattend`), *done* is
the output of a rule that checks against the goal (`stop`). Nothing in this file
knows what either is.

⭐⭐⭐ **`stop` is what made *done is the output of a rule* mean anything.**
It was written here from the start and the loop had no way to obey one: a
completion check concluded and the agent carried straight on to quiescence.
`stop` is a postcondition beside `attend` and `unattend`, so it is a row rather
than a branch, and the loop still knows nothing about
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

## Attention: the same table, keyed on a THING

Everything above scores rules. `prefer(<R>, key, n)` names a rule, a buff names
a rule, a reranker nudges a rule -- and the loop takes the first surviving
application and breaks. So with two goblins in the room and one `<attack>` rule,
**which goblin is struck was never chosen**: it is the walk's answer, which is
authoring order wearing a preference. Nothing in this file could say otherwise,
because the thing to be preferred is not a rule.

`attention(x)` is an ordinary claim about a NODE, and it reaches both halves:

| | what it decides | how exact | what it costs |
|---|---|---|---|
| `_attended_first` | which of a rule's applications is taken | **exact** | nothing -- `found` is already materialised |
| `_pull` | which rules are matched at all | approximate | two dict reads |

⭐⭐⭐ **The second is a join, and that is the only reason it is affordable.**
*Which rules are about `goblin1`* has no syntactic answer -- every rule is
generic, so no rule's text mentions `goblin1` -- and its exact answer is *those
with an application binding it*, which is the option set this loop exists not to
build. Asked from the other end it is two lookups: the relations `goblin1` is
currently spoken of under (`Situation.relations_of`, the state's third index),
and the rules whose antecedent uses one (`Table.by_relation`). The same
join-not-scan that recovered `overrides`, `supersedes` and `forgone`, for the
fourth time.

⚠ **Approximate on purpose.** A rule reading `wounded(?x)` is lifted because
`goblin1` is wounded, whether or not it would bind `?x` to goblin1. That is the
right amount of wrong: the lift decides who is MATCHED, and being roughly right
about a shortlist costs a slot. Exactness arrives one layer up, for free.

⚠ **Ranking-time and kept nowhere**, unlike a buff.
This file's own line between the two kinds of attention is *what I was doing
persists and fades, what is in front of me is recomputed* -- and a claim the
agent is currently making about what it is thinking about is plainly the second.
Making it a buff would give it a life and a ceiling on top of a claim that has
both already: the claim is denied, and it is over.

⚠ And `_attended_first` is STABLE, so attention overrides §18's tie-break where
it has an opinion and defers to it everywhere else. Measured on two goblins: the
walk strikes the last-declared first, attention on the other flips it, and
attention on the one already chosen changes nothing.

Measured, on a twelve-rule table of which three rules can match: a rule twelfth
in the table applies FIRST when the thing it is about is attended, and the run
costs **195 matches against 238** because the shortlist stopped widening past it.

⚠ Attending to all three costs 193 -- indistinguishable. An earlier version of
this paragraph read a 157-against-143 gap as *attention that names everything
narrows nothing*, and growing the bundle by three rules turned it into 193
against 195, pointing the other way. The cost was the wrong column: what
attention that names everything loses is DISCRIMINATION, and that is checkable
-- it moves no rule ahead of any other, so the first move is the untaught one.

## ⚠⚠⚠ Attending the last move's RIGHT-HAND SIDE by default: built, and BACKED OUT

The obvious next step, and it does not survive contact. *What I was just doing
is part of my representation of the world* — so after a move, attend to every
node it wrote, decomposed (`on(d1, z)` gives `on(d1,z)`, `on`, `d1`, `z`),
replacing rather than accumulating, with learned lessons adding to it.

Three variants, measured on the whole suite:

| how the lift was computed | suite |
|---|---|
| flat, every rule attention touches | **10 checks failed** |
| counted, by how many attended nodes a rule is about | **13 failed** |
| counted, capped below `STANDING` so the apparatus keeps its place | **13 failed** |

...against one measured gain: Hanoi 100 ticks to 99.

⭐ **The diagnosis is why the note is worth more than the code.** A flat lift
moved **34% of the pool by the same amount every tick**, which reorders nothing
inside that third — *attention that names everything discriminates nothing*,
arriving as a default. Counting fixed the flatness and exposed the next
problem: `<move>` has 15 ground nodes against `<ask>`'s 2, so a big rule matches
more of anything. Wired on its own, counting cost the `focus` arm of
`ugm.teaching` **44 domain conclusions against 3** on the dungeon — the one
corpus with a real learned attention policy.

⚠ And the thing it was built to fix got WORSE. `ugm.hanoi` records a decline
arriving at tick ~101; a pending `attempt` that no rule wrote is not in the last
write set, so under the default it stopped being declined at all.

**So the default wants doing WITH the scoring work, not before it** — length
normalisation is what stops a big rule winning on size, and an inverse-frequency
weight is what stops `stage` and `on` lifting everything. Neither exists yet, and
this is what it looks like without them.

## ...and where a lesson about it lives: a postcondition, never a rule

A postcondition can spend three things, and `attend` is the one that DEPOSITS:

    attend(?x, n)   think about what this move just bound, and how much
    unattend        stop thinking about whatever it was
    stop            end the run

⚠⚠⚠ **There were three more and they moved a SCORE**: `boost`, `damp` and
`reset`. They named a RULE, which is what retired them -- a rule id goes stale
the moment a rule is adopted, composed or renamed, so a corpus of experience
written in them stops LOADING rather than going quietly wrong. Everything that
kept them alive went too: `LIFE`, the saturation ceiling, the trace that rebuilt
the table, `_rerank`, and the `reflex` calibration. What is left cannot decay,
so there is nothing to tune.

⭐⭐⭐ **It has to be a postcondition, and that was measured before it was
built.** `docs/HANDOFF.md` 2026-08-15 wrote a learned recogniser as a RULE and it
fired **twice out of sixteen installed** -- *in a one-move-per-tick loop,
spending a move on recognition competes with doing the work*, and the rule that
recognises a situation loses to the rule that acts in it, every time. A
postcondition is evaluated for free after whatever applied. The same sentence
decided where the bigram lives; this is it applying to attention.

⚠ **The table does not run these.** A deposit writes a claim the corpus can
read, deny and reason about, and a table that could write claims would be an
interpreter with a memory. So `_spend_one` splits them: attention to the machine,
and only the stop recorded on the table.

⚠⚠⚠ **And a ranking-time `when` trigger is REFUSED**, which used to be the
stronger case and is now simply an error. Such a trigger ran on rules that had
not applied and may never apply, so a deposit from there would be the agent
claiming to think about something because it considered thinking about it.
`_rerank` was the only thing that ran one and is retired, so the surface rejects
it rather than accepting a lesson that silently does nothing.

⚠ `unattend` is what bounds the mechanism. A buff had `LIFE` and a ceiling; a
claim has neither, so a lesson that only ever attends accumulates until
everything is attended -- which is measurably the same as attending to nothing.
Spent as a pair, attention becomes a FOCUS: one thing at a time, and the
replacement is on the record as a denial rather than as a forgetting.

## The trace

Every buff is recorded as (tick, by whom, target, delta), so the table at step
k is the defaults plus the deltas up to k. That is what makes a frozen
postcondition's effect showable after the fact -- *authority was in fact
considered* -- without the loop having to justify an ordering it does not
reason about.
"""

import time
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

from .graph import NodeId
from .machine import Machine, Step
from .rules import (STOP, UNATTEND, Application, Attend, Member, Rule,
                    Situation, _superseded, match, substitute)
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
# How far attention lifts a rule that could be about what is attended.
#
# Recomputed every move and kept nowhere, unlike a buff -- so there is no decay
# to tune and no runaway to guard against. That is
# this file's own line between the two kinds of attention, and a claim the agent
# is currently making about what it is thinking about is plainly the second
# kind: *what is in front of me is recomputed*.
#
# Sized against `STANDING - FLOOR` (9), so a rule attention reaches can clear
# the apparatus rather than merely climb past its neighbours at the floor. A
# lift that could not do that would find the top of the table already full and
# change nothing, which is the failure mode `_rerank` measured for shortlist-only
# nudges: a mechanism that cannot bring a rule INTO consideration is not one
# that can direct anything.
PULL = 6

# The default doubt-settling rule, and the author's correction to an earlier
# sketch of mine: the loop does not need to HOLD a tick waiting for doubt to be
# resolved, because a settling rule fires. Depositing the doubt IS the move and
# this rule gets the next turn. A corpus replaces it with something better (ask
# the user, apply a domain criterion) by writing a rule that outscores it.
#
# ⚠ It used to carry `frozen after <settle-doubt> => boost(?a, 1)` -- the
# settlement was a buff, so it was calibratable. With the buffs retired it
# concludes and nothing more, and the loop's own backstop is what makes
# progress: the doubt already stands on the next tick, so `fresh` is false and
# the winner applies. The boost was never what unblocked the run; it reinforced
# a winner the loop had already chosen.
#
# `?a` is the winner as the doubt named it. That is only writable because rules
# are subjects here -- `close(<A>, <B>)` names them -- and because `_note`
# deposits it as a MENTION, so a rule concluding about `?a` is not dropped by
# quiescence as having nothing to deposit.
SETTLE = """
rule <settle-doubt> = implies( { +close(?a, ?b) }, { +settled(?a, ?b) } )
"""
SETTLING = ("settle-doubt",)


class Post(NamedTuple):
    """A postcondition: a query, and what it SPENDS if the query holds.
    `query` is the name of a rule authored in the corpus whose ANTECEDENT is the
    query -- so the surface parses it, and this file adds no notation. Such
    rules never enter the table.

    ⚠ `spends` used to be `buffs`, and the rename is the retirement in one word:
    what a postcondition may now say is `attend`, `unattend` and `stop`. None of
    them moves a score, so there is no table to keep an account of and no trace
    to keep it in.

    `frozen` marks what a calibration process may not touch. It changes nothing
    about how the postcondition runs.
    """

    of: str  # the rule this hangs off
    query: Optional[str]
    spends: Tuple[object, ...]
    frozen: bool = False


class Table:
    """Scores over rules, ordered. `STANDING` or `FLOOR`, and nothing moves
    them after `absorb` -- the only thing that ever did was a buff."""

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
        # Attention's rule-side lookup, built once because a rule's antecedent
        # does not change. `absorb` is the only thing that can invalidate it.
        self.by_relation = _by_relation(self.rules, self.g)
        # Why the run ended, if a postcondition ended it. A name rather than a
        # flag, because *why did you stop?* has to be answerable -- the same
        # reason the shipped loop's `_enough` returns what was named.
        self.stopped: Optional[str] = None
        # ⚠ The score is now FIXED once built: `STANDING` or `FLOOR`, moved only
        # by `absorb`. There is nothing to age, expire or rebuild, because the
        # only thing that used to move it was a buff. What varies move to move is
        # the attention lift, and `order` takes that as an argument and keeps it
        # nowhere -- which is the whole of this file's line between the two kinds
        # of attention.
        self.now = 0
        # How many ticks this table has been run through. A table handed back for
        # a second run continues the count, and `now == 0` cannot tell *never
        # ran* from *ran tick 0* -- the exact case a host stepping one tick at a
        # time produces.
        self.ticked = 0

    def absorb(self, rules: Sequence[Rule], standing: set) -> int:
        """Take in rules the agent did not start with.

        ⭐⭐⭐ **`adopt` means the rule set moves at run time**, and a table built
        once cannot see it: the rule was live, it was the node the graph
        described, and it never applied because nothing had a score for it. The
        round trip was open at the last step.

        A new rule enters at the floor like any other -- `standing` if the bundle
        says so. Nothing already in the table is touched.
        """
        added = 0
        for r in rules:
            if r.node in self.score:
                continue
            self.score[r.node] = (
                STANDING if (r.node in standing or r.name in SETTLING) else FLOOR
            )
            # Ranked after everything present, which IS authored order: a rule
            # adopted on tick 40 was authored on tick 40.
            self.rank[r.node] = len(self.rules)
            self.rules.append(r)
            if r.name:
                self.by_name[r.name] = r
                self.name_of[r.node] = r.name
            added += 1
        if added:
            # ⚠ Rebuilt rather than appended to, because a rule adopted at run
            # time is the case `absorb` exists for and a stale lookup here fails
            # in the quietest way there is: the rule is in the table, at the
            # floor, and attention can never reach it. That is `adopt`'s own
            # round-trip defect one index along.
            self.by_relation = _by_relation(self.rules, self.g)
        return added

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

    def _target(self, target: NodeId, bindings) -> Optional[NodeId]:
        """A rule node, or a variable the query bound to one."""
        if self.g.is_var(target):
            return None if not bindings else bindings.get(target)
        return target

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
    # Members that could not be indexed and were answered by a scan, over this
    # run -- the totals beside `widenings`, and the per-member breakdown that
    # says which one to go and change. `scans` counts the fallbacks and
    # `scanned_nodes` the instances they walked, which is the one that ranks
    # them. `scanned` is `member as written -> [times, nodes]`.
    # See `rules._narrowed`.
    scans: int = 0
    scanned: Dict[str, List[int]] = {}
    scanned_nodes: int = 0


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
    # ⚠⚠⚠ **EVERY overrider that matched, not the first.** This returned on the
    # first one, so a rule beaten by two recorded only whichever `precedence()`
    # happened to list first -- and the dungeon has both `<halt>` and
    # `<hero-acts>` over `<hero-holds>`. `<halt>` won the race and
    # `defeated(<hero-holds>, <hero-acts>)` was never written, which
    # `ugm.attention`'s own gate caught as a conclusion the shipped loop reaches
    # and this one does not.
    #
    # ⭐ The DECISION is unaffected -- defeated is defeated, and the first match
    # settles it. What was incomplete is the RECORD, and *which of my rules
    # actually fight* is the question the deposit exists to answer.
    beaten = False
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
            beaten = True
    return beaten


def _rivals(m: Machine, chosen: Application, state) -> List[Application]:
    """The other ways of getting what this move is getting.

    ⭐⭐⭐ **Complete forgoing looked like it needed the option set, and it does
    not.** *What else could have served this want* ranges over every rule only if
    you ask it that way round. `_wants` reads what an application CONSUMED -- an
    application that consumed `goal(w)` is a response to wanting `w` -- so a
    rival is a rule that could consume `goal(w)` too, and **only a rule whose
    antecedent reads `goal` can.** That is a lookup over the rule set, and it is
    usually a handful.

    So the prefix scan keeps its window for CHOOSING and asks a second, narrow
    question for passing up: the same join-not-scan that recovered `overrides`
    and `supersedes`, and the third time it has turned an apparent aggregate into
    an index.

    ⚠ Only when the move serves a want at all, which is the common case being
    cheap rather than an optimisation: most moves consume no goal and pay
    nothing.
    """
    if not m._wants(chosen):
        return []
    out: List[Application] = []
    for r in m.rules.rules:
        if r is chosen.rule:
            continue
        if not any(m.g.relation_of(mm.pattern) is m.GOAL for mm in r.antecedent):
            continue
        out.extend(match(
            m.g, m.chain, r, m.focus.topic, m.focus.seat, state,
            computes=m.rules.computes, structural=m.rules.skeleton(),
        ))
    return out


def _dormant(m: Machine, r: Rule) -> bool:
    """Claimed `dormant` and not yet claimed `due`.

    ⚠ Deliberately NOT a mark on the rule that the engine reads. A mark authored
    once is relative to nothing -- not to the situation, not to the goal, not to
    who is asking -- which is §12's *achievability is not a mark*, the earliest
    instance of the error this design generalises. As a pair of ordinary claims
    it is dated, attributable, deniable, and readable by rules, and `due` can be
    concluded by anything at all.
    """
    return (m._claims(m.g.rel(m.DORMANT, r.node))
            and not m._claims(m.g.rel(m.DUE, r.node)))


def _is_superseded(m: Machine, app: Application, state) -> bool:
    """Defeated **for this case** rather than for this step.

    ⭐ The property `supersedes` exists for is *substitute where an outcome is
    declared, otherwise assume* -- and it is not expressible any other way. Three
    routes were measured and all three fail:
    **a buff** cannot, because ordering is not defeasibility -- boosting the
    winner gets it applied first and the loser applies second and overwrites it,
    which measured WORSE than doing nothing; **consumption** cannot, because the
    trigger `did` is re-derived from `emitted`, the boundary record a corpus must
    never consume; and **a negated member** cannot, because *this act has no
    declared outcome* is negation over an open domain.

    So it is ported rather than dropped, and the shape is `_is_defeated`'s one
    construct along: the question is about a PAIR of applications, so match only
    the rules that supersede this one and ask whether any of their applications
    shares a consumed entry with this one. A join, not a scan -- where the old
    loop answered it by materialising every application it had.
    """
    higher = [h for h, lower in m.rules.precedence(m.rules.SUPERSEDES)
              if lower is app.rule]
    if not higher:
        return False
    others: List[Application] = []
    for h in higher:
        others.extend(match(
            m.g, m.chain, h, m.focus.topic, m.focus.seat, state,
            computes=m.rules.computes, structural=m.rules.skeleton(),
        ))
    return _superseded(m.rules, app, others)


def _standing(m: Machine) -> set:
    """The rules the bundle deposits `standing(<R>)` about -- the default table,
    which already exists in all but name."""
    out = set()
    for node in m.g.instances_of(m.STANDING):
        members = m.g.members(node)
        if len(members) == 1 and m._claims(node):
            out.add(members[0])
    return out


def _by_relation(rules: Sequence[Rule], g) -> Dict[NodeId, List[NodeId]]:
    """Which rules could be about a relation: antecedent relation -> rule nodes.

    The rule-side half of attention's join, and it is built once per table
    rather than per move because a rule's antecedent does not change. `absorb`
    is what keeps it current when the rule set does.

    ⚠ A member whose pattern is a bare variable or whose relation is a variable
    is filed under nothing. `+?p` is a rule about anything, and lifting it
    whenever anything is attended would lift it always -- which is the same
    thing as never, and costs a slot in every shortlist to say so.
    """
    out: Dict[NodeId, List[NodeId]] = {}
    for r in rules:
        seen = set()
        for mm in r.antecedent:
            if g.is_var(mm.pattern):
                continue
            rel = g.relation_of(mm.pattern)
            if rel is None or g.is_var(rel) or rel in seen:
                continue
            seen.add(rel)
            out.setdefault(rel, []).append(r.node)
    return out


def _pull(m: Machine, table: "Table", state: Situation,
          attended: Sequence[NodeId]) -> Dict[NodeId, int]:
    """Attention's rule-level lift: two dict reads and no matching.

    ⭐⭐⭐ **The join, and the reason attention is affordable where a query is
    not.** *Which rules are about `goblin1`* looks like it needs matching --
    every rule is generic, so no rule's text mentions `goblin1` at all, and the
    only exact answer is *those with an application binding it*, which is the
    option set this loop exists not to build. Asked the other way round it is
    two lookups:

        goblin1 -> the relations it is spoken of under   (`relations_of`)
                -> the rules whose antecedent uses one   (`_by_relation`)

    ⚠ **Approximate, and deliberately so.** A rule reading `wounded(?x)` is
    lifted because `goblin1` is wounded, whether or not it would bind `?x` to
    goblin1 rather than to someone else. That is the right amount of wrong: this
    decides who is MATCHED, not who wins, and being roughly right about a
    shortlist costs a slot. The exact answer arrives one layer up, in
    `_attended_first`, where the bindings are already in hand and free.

    ⚠ Not summed over attended nodes. A rule reachable from two attended nodes
    is not twice as relevant, and letting it be would make the lift a popularity
    count over whatever the corpus happened to attend to.
    """
    lift: Dict[NodeId, int] = {}
    # ⭐⭐⭐ **POSITION is the strength.** `attended` arrives newest-first, so
    # what the agent turned to last lifts hardest and what is about to fall off
    # the bottom barely lifts at all. That gradient is the whole reason the
    # queue exists: a FLAT lift moved 34% of the pool by the same amount every
    # tick (20d), which reorders nothing inside that third -- and counting, then
    # inverse frequency, were both attempts to buy back a differentiation the
    # ordering gives away for nothing.
    #
    # ⚠ A rule reachable from two attended nodes takes the STRONGER, not the
    # sum. Being about two things the agent is thinking of does not make a rule
    # twice as relevant, and summing would make the lift a popularity count over
    # whatever the corpus happened to attend to.
    weights = m._attention_weights()
    for i, node in enumerate(attended):
        # ⭐⭐⭐ **Position times the learned multiplier.** Depth says how
        # recently the agent turned to a thing; the multiplier says how much a
        # lesson thinks it is worth. Neither alone is enough -- everything one
        # move wrote arrives at the same depth, so without a weight the queue
        # cannot separate them, which is exactly what sank attending the
        # right-hand side twice (20d, 20h).
        weight = max(1, PULL - i) * weights.get(node, 1)
        for rel in state.relations_of(node):
            for r in table.by_relation.get(rel, ()):
                if weight > lift.get(r, 0):
                    lift[r] = weight
    return lift


def _attended_first(found: List[Application], attended: Sequence[NodeId],
                    weights: Optional[dict] = None) -> List[Application]:
    """Order a rule's own applications by what the agent is thinking about.

    ⭐⭐⭐ **This is the half no rule-keyed buff can express, and it costs
    nothing.** The loop takes the first surviving application and breaks, so
    which BINDING wins has always been walk order -- authoring order, wearing a
    preference. `table.score` is keyed by `r.node`; `prefer(<R>, key, n)`,
    `_rerank` and every taught reranker key on CONTEXT. None of them can say
    *this rule, on that one*, because the thing being preferred is not a rule.

    A claim about a node can. And `found` is already materialised -- the loop
    paid for it and threw everything past the first survivor away -- so ordering
    it is a sort over a list that is usually one or two long.

    ⚠ **Stable, and that is what keeps the existing tie-break intact.** Among
    applications attention says nothing about, the order is exactly the order
    the matcher produced, which is §18's most-recent-first. So attention
    OVERRIDES the walk where it has an opinion and defers to it everywhere else
    -- rather than replacing an ordering the whole design rests on.

    ⚠⚠ **And it counts, rather than testing.** An application binding two
    attended nodes goes before one binding one, which is what makes attending to
    a pair mean *the move involving both* instead of *either, and the walk
    decides*.
    """
    if len(found) < 2:
        return found
    at = set(attended)
    weights = weights or {}

    rank = {node: (len(attended) - i) * weights.get(node, 1)
            for i, node in enumerate(attended)}

    def weight(a: Application) -> int:
        # ⚠ Weighted by POSITION here too, so an application binding what the
        # agent just turned to beats one binding what it is about to forget.
        # Summed, unlike the rule lift: binding two attended things really is
        # more about them than binding one, because a binding is the whole
        # move rather than a reason to look.
        return sum(rank.get(v, 0) for v in a.bindings.values() if v in at)

    scored = [(weight(a), i, a) for i, a in enumerate(found)]
    if not any(w for w, _i, _a in scored):
        return found  # nothing attended is in play here; do not touch the order
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [a for _w, _i, a in scored]


def _queries(m: Machine, posts: Sequence[Post]) -> set:
    return {p.query for p in posts if p.query}


def run(m: Machine, posts: Sequence[Post] = (), limit: int = 400,
        chooser=None, watch=None,
        pool: Optional[Sequence[Rule]] = None,
        table: Optional["Table"] = None) -> Report:
    """The loop, in full. Everything else in this file is bookkeeping.

    ⚠ `reflex` used to be a parameter here -- damp a rule that was tried and
    missed, boost the one that applied, the cheapest calibration imaginable. It
    went with the buffs, and with it the only thing in this file that wrote a
    score from the loop's own experience. What survives is attention, which is
    written by a rule rather than by the loop.
    """
    queries = _queries(m, posts)
    # ⭐ `pool` is what makes an EXPERT possible: one shared graph, one shared
    # chain, and a table over a SUBSET of the rules. The loop does not know what
    # an expert is -- it is handed the rules it may consider, exactly as it is
    # handed the corpus. `ugm.experts` reads the subset off the graph.
    # ⚠ Whether the pool was HANDED to us decides whether it may grow. An
    # expert's pool is what `knows` says it is, and a rule the agent adopts is
    # not that expert's until something says so. The default pool is *every
    # rule*, and that is a set the agent can add to at run time.
    fixed = pool is not None
    if pool is None:
        pool = m.rules.rules
    pool = [r for r in pool if r.name not in queries]
    # ⭐⭐⭐ **A caller may bring its own table, and `docs/interpretation-feedback.md`
    # §4 is right that the day it matters is the day something else changes.**
    # A host driving the agent one tick at a time calls this per `/step`, and a
    # table built here is free EXACTLY while no postcondition has moved it: with
    # no posts supplied a table is its defaults plus an ATTENTION lift
    # recomputed from the graph every tick, so a rebuilt table is the same
    # table. Supply
    # real postconditions and the rebuild silently discards every spend -- what
    # the agent learned *within* a run -- and nothing says so, because from
    # here nothing went wrong.
    #
    # ⚠ **The ticks continue from `table.now` rather than restarting at 0.**
    # Nothing in the table decays any more, so this no longer guards a lift's
    # age; it is what lets a caller stepping one tick at a time see a monotone
    # tick count rather than a saw-tooth.
    if table is None:
        table = Table(m.g, pool, _standing(m))
    base = table.now + 1 if table.ticked else 0
    by_rule: Dict[str, List[Post]] = {}
    for p in posts:
        by_rule.setdefault(p.of, []).append(p)

    applied: List[str] = []
    steps: List[Step] = []
    arrivals = 0
    tried = 0
    doubts = 0
    widenings = 0
    windows: List[int] = []
    # Sampled rather than reset: the graph is shared -- an expert, a table of
    # agents and a supposition all run over one -- so a run reports the scans
    # IT caused and clears nothing another caller is still counting.
    scans0 = {k: list(v) for k, v in m.g.scans.items()}
    t0 = time.time()
    for tick in range(base, base + limit):
        # Not a phase: the world may have spoken since the last move, and the
        # shipped loop asks the same question in the same place.
        # ⭐⭐⭐ **The anchor a corpus reads the raw chain from.** Minting it is the
        # whole of this line -- `asking(<seat>)` has to EXIST for a stratum-0
        # rule to bind it, and a corpus has no hand to seed it with. Without it
        # *it was on, then it was not* cannot be written at all: the rule is well
        # formed, every other member matches, and it silently never applies.
        #
        # ⚠ Anchored at the SEAT rather than at every moment, which is the
        # containment story as well as the cheap one: what the agent may read the
        # chain about is where the agent is standing.
        m.g.rel(m.chain.ASKING, m.focus.seat.node)

        # A rule the agent authored since the last tick enters the table now.
        if not fixed:
            table.absorb([r for r in m.rules.rules if r.name not in queries],
                         _standing(m))

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
        table.now = tick
        table.ticked += 1

        window: List[Application] = []
        top = None
        # ⭐⭐⭐ **Dormancy, and it is the right form of *disable a rule*.** A rule
        # claimed `dormant` is not considered until something claims it `due` --
        # which is all a callback is. Both are ordinary FACTS rather than a mark
        # the engine reads, so both are askable, defeasible and attributable, and
        # *which rules is this hypothesis carrying* is a query rather than a
        # field.
        #
        # ⚠ Read every tick and at the register's own position, never once when
        # the pool is built: `due` can be concluded mid-run, and a callback
        # attached inside a hypothesis must wake only there.
        # ⭐⭐⭐ **THE `prefer` LIFT IS GONE, and what is left is the same lift
        # by a better key.** The table used to read `prefer(<R>, key, score)`
        # as a buff, which it is -- *when this is in play, think of R*. What is
        # wrong with it is not the arithmetic, it is the subject: it can only
        # ever name a RULE, so it cannot tell two goblins apart, and a lesson
        # keyed on `<R>` is stale the moment that rule is adopted, composed or
        # renamed. Measured on the dungeon, every rule-naming arm lost to the
        # node-naming one, and `occasion` was worse than doing nothing.
        #
        # Attention keys on a NODE, is read at the same point in the move, and
        # is what `learned` now writes. Nothing else about the lift changed.
        #
        # ⚠ Ranking-time and kept nowhere: an attention claim is a fact the
        # corpus is currently making, so the lift
        # is a function of the state and re-deriving it is the whole of keeping
        # it current. Making it a buff would give it a life and a saturation
        # ceiling on top of a claim that already has both -- the claim is
        # denied, and it is over.
        attended = m._attended()
        # ⚠⚠⚠ **The queue has two uses and only one of them can starve.**
        # Ordering a rule's own BINDINGS costs nothing -- the applications are
        # already in hand. LIFTING rules changes which are matched at all, so a
        # queue full of whatever the last move wrote can push the shortlist onto
        # recently-touched rules and leave work unreached: measured, the dungeon
        # quiesced 32 moves early and lost 48 conclusions.
        #
        # So the lift is driven by what a LESSON asked for -- a weighted
        # `attend(?x, n)` -- and the whole queue orders bindings.
        lift = None
        asked = m._attention_asked()
        if asked:
            lift = _pull(m, table, state, asked) or None
        ordered = [r for r in table.order(lift) if not _dormant(m, r)]
        cut = 0
        while cut < len(ordered) and not window:
            # One shortlist at a time. Score decides WHO is matched, which is
            # the whole proposal: a rule below the cut costs nothing at all.
            chunk = ordered[cut:cut + SHORTLIST]
            if cut:
                widenings += 1
            cut += SHORTLIST
            for r in chunk:
                if top is not None and table.score[r.node] < top - TOLERANCE:
                    break  # the prefix ends here, and the rest is not matched
                tried += 1
                found = match(
                    m.g, m.chain, r, m.focus.topic, m.focus.seat, state,
                    computes=m.rules.computes,
                    structural=m.rules.skeleton(),
                )
                # ...and WHICH of them, which the loop has never chosen. It
                # takes the first survivor and breaks, so the binding was
                # decided by the walk. Free: `found` is already here.
                if attended:
                    found = _attended_first(found, attended,
                                            m._attention_weights())
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
                    continue
                for a in found:
                    if m._survives(a) and not _is_superseded(m, a, state):
                        window.append(a)
                        if top is None:
                            top = table.score[r.node]
                        break
                if len(window) >= WINDOW:
                    break
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
        # ⭐⭐⭐ **Taking one way of getting something passes up the others**, and
        # this loop was not saying so -- which cost `ugm.learning` and
        # `ugm.practice` entire, because rehearsing safely IS choosing and then
        # naming what you did not do.
        #
        # ⭐ And it names the rivals the agent ACTUALLY WEIGHED -- the window --
        # where the option-set loop named every application it had materialised.
        # That is the more honest record of the two: *what did you pass up* ought
        # to mean *what did you consider and not take*, not *what existed*.
        #
        # ⚠ `forgone` stays out of `ACCEPTED_LOSSES` for the corpus gate all the
        # same: the two loops weigh different sets, so they legitimately pass up
        # different things.
        m._forgo(window + _rivals(m, chosen, state), chosen)
        m._widened = False
        wrote = m._apply(chosen)
        m._attend_written(wrote)
        m._spend(chosen, wrote)
        applied.append(chosen.rule.name or "?")
        steps.append(Step(arrivals, len(window), tried, chosen,
                          tuple(wrote or ()), "applied"))
        if watch is not None:
            # AFTER the move, not at the choice: a tick that deposits a doubt
            # chooses and then does not apply, so watching at the choice
            # recorded a rule that never ran -- and a lesson built from that
            # sequence teaches a move that never happened.
            #
            # ⭐ **...and the `Step` goes with it, which is the whole of
            # `docs/interpretation-feedback.md` §4.** Watching after the move
            # means `_spend` has already appended its refraction bookkeeping, so
            # a watcher asking the CHAIN *what did that move write* over-reports
            # by a `spent(...)` term -- and the harness was wrapping
            # `Machine._apply` on the instance to get the honest answer. It is
            # the one place it reached inside the engine. The step already
            # carries `wrote`, the entries the application itself deposited, so
            # the answer was here all along and nothing was handing it over.
            watch(m, table, window, chosen, tick, steps[-1])
        _spend_posts(m, table, chosen, tick, state)
        if table.stopped is not None:
            steps.append(Step(arrivals, 0, tried, None, (), "stopped"))
            # *Completion is the output of a rule*, and this is the loop obeying
            # one. It knows a rule spent `stop`; it does not know what a goal is,
            # which is the line this file has held from the start.
            break
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
    scanned = {}
    for k, v in m.g.scans.items():
        was = scans0.get(k, [0, 0])
        if v[0] > was[0]:
            scanned[k] = [v[0] - was[0], v[1] - was[1]]
    return Report(
        len(applied), applied, time.time() - t0, tried, _state(m), table,
        doubts, windows, widenings, steps,
        sum(v[0] for v in scanned.values()), scanned,
        sum(v[1] for v in scanned.values()),
    )


def _spend_one(m: Machine, table: Table, tick: int, by: str, spends, frozen,
               bindings, rule_node) -> None:
    """Spend one postcondition: attention to the machine, a stop to the table.

    ⭐⭐⭐ **The split is the design, not plumbing.** A deposit writes a claim the
    corpus can read, deny and reason about, and a table that could write claims
    would be an interpreter with a memory. A stop writes nothing and only says
    the run is over, so it is the one thing recorded on the table.

    ⚠ The licence is the rule that spent it, so *why am I thinking about this*
    answers with a rule and a moment.
    """
    licence = m.g.rel(m.APPLIED, rule_node)
    for target, _delta in spends:
        if isinstance(target, Attend):
            node = table._target(target.term, bindings)
            if node is None:
                node = target.term
            # ⚠ Ground only, and silently so. A postcondition naming a variable
            # the move did not bind has nothing to attend TO, and depositing
            # `attention(?x)` would be a claim about no one -- which `_attended`
            # would then refuse to read, one layer further from the mistake.
            if node is not None and not m.g.has_var(node):
                # ⭐ The learned WEIGHT rides along: `attend(?x, 3)` says this
                # node matters more than whatever else is in the queue at the
                # same depth -- a calibration that names a node instead of a
                # rule.
                m._attend(node, licence, target.weight)
            continue
        if target is UNATTEND:
            m._unattend(licence)
            continue
        if target is STOP:
            # Recorded here, obeyed by the loop. Keeping the decision out of the
            # spend is what lets *why did you stop?* answer with a rule's name
            # rather than a flag.
            table.stopped = by


def _spend_posts(m: Machine, table: Table, chosen: Application, tick: int,
                 state: Situation) -> None:
    """Run the applied rule's postconditions and move the table.

    The query is matched with the application's own bindings already
    substituted in, which is what makes it a POSTcondition rather than a second
    rule: `after { +penguin(?x) }` asks about the `?x` this rule just bound. A
    bare `after` has no query and holds always.
    """
    name = chosen.rule.name or "?"
    for query, spends, frozen, _learned in m.rules.triggers.get(
            chosen.rule.node, ()):
        if not query:
            _spend_one(m, table, tick, name, spends, frozen, chosen.bindings,
                       chosen.rule.node)
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
            _spend_one(m, table, tick, name, spends, frozen, bound,
                       chosen.rule.node)


def _state(m: Machine) -> set:
    """What the agent ends up holding, as (proposition, sign). The comparison
    has to be over conclusions rather than over moves: two loops that reach the
    same beliefs by different routes agree about the world, and that is the
    question."""
    return {(m.g.show(e.proposition), e.sign) for e in m._state()}


# -- the comparison ---------------------------------------------------------

PENGUIN = """
fact bird(tweety)
fact bird(pingu)
fact penguin(pingu)
fact asked(pingu)
fact asked(tweety)

rule <flies>      = implies( {{ +bird(?x), +considered(?x) }},    {{ +can_fly(?x) }} )
rule <flightless> = implies( {{ +penguin(?x), +considered(?x) }}, {{ +grounded(?x) }} )
rule <classify>   = implies( {{ +asked(?x) }},                    {{ +considered(?x) }} )
{post}
"""


def penguin() -> int:
    """The author's example, and it found the mechanism's real boundary.

    `<flies>` is declared first, so under declaration order it wins for every
    bird, penguin included. The general rule IS the more foundational one, which
    is what declaration order says.

    **But ordering alone is not defeasibility, and running it is how that
    showed.** A loop that continues to quiescence applies BOTH rules whatever
    the order: a low score delays a rule, it never removes one, and removal is
    the thing this design refuses on purpose. So the penguin comes out flying
    AND grounded whichever rule went first.

    ⚠⚠⚠ **THE BUFF NEVER FIXED THE PENGUIN, AND RETIRING IT COSTS NOTHING
    HERE.** This file used to say *the specificity has to come from a buff*, and
    that was wrong in the way that matters: `boost(<flightless>, 20)` reordered
    the two rules and `can_fly(pingu)` stayed true in both arms. Measured on the
    way out. What a buff bought was the ORDER, and the order is not the answer to
    the penguin -- the answer is that the specific rule DEFEATS the general one,
    which §12 has said all along and which no score can say.

    The four levers on one fixture, and **only the last one answers the
    question** -- which the control is what shows:

        lever              pingu flies   tweety flies
        declaration order      yes           yes        an ordering, so both apply
        standing               yes           yes        likewise -- and that is correct
        overrides              no            NO         defeat, and TOO COARSE
        representation         no            yes        the only one that works

    ⚠⚠⚠ **`overrides` grounds tweety as well, and that was not expected.**
    `overrides(<flightless>, <flies>)` is defeat per RULE: once `<flightless>`
    matches anywhere, `<flies>` is out for everybody, so the ordinary bird stops
    flying too. It solves the penguin by breaking flight, which is not solving
    it. §12's defeat is the right KIND of answer and the wrong GRAIN -- the
    claim needs to be about this binding, and `overrides` cannot say that.

    ⭐ What does work is representation: state `-penguin(tweety)` and let
    `<flies>` read it. The general rule keeps working for ordinary birds and
    declines for this one, because the corpus said something it knew rather than
    leaving it to a score. §9's positive tests, with the negative WRITTEN rather
    than inferred from silence.

    ⭐ `tweety` is the control and is the whole reason this table is worth
    printing. Without it `overrides` and representation look identical, and the
    lever that breaks flight passes.
    """
    print()
    print("  the penguin -- ordering is not defeasibility")
    wrong = 0
    DENIED = PENGUIN.replace(
        "fact penguin(pingu)",
        "fact penguin(pingu)" + chr(10) + "fact -penguin(tweety)").replace(
        "+bird(?x), +considered(?x) }}",
        "+bird(?x), +considered(?x), -penguin(?x) }}")
    cases = (
        ("declaration order alone", PENGUIN.format(post="")),
        ("standing(<flightless>)",
         PENGUIN.format(post="fact standing(<flightless>)")),
        ("overrides(<flightless>, <flies>)",
         PENGUIN.format(post="fact overrides(<flightless>, <flies>)")),
        ("the KB states -penguin(tweety)", DENIED.format(post="")),
    )
    for label, src in cases:
        m = Machine()
        kb = load(m, src)
        load(m, SETTLE)
        run(m, limit=12)
        held = lambda t: m.holds(kb.term(t)) == "+"
        pingu_flies, tweety_flies = held("can_fly(pingu)"), held("can_fly(tweety)")
        print(f"    {label:32} pingu flies: {str(pingu_flies):5}  "
              f"grounded: {str(held('grounded(pingu)')):5}  "
              f"tweety flies: {tweety_flies}")
        if label.startswith(("overrides", "the KB")):
            # The two that claim to answer it: the penguin must not fly, and an
            # ordinary bird must still be able to.
            if pingu_flies:
                print(f"    FAIL  {label} left the penguin flying")
                wrong += 1
            if label.startswith("the KB") and not tweety_flies:
                print(f"    FAIL  {label} grounded tweety as well, which is not "
                      f"solving the penguin but breaking flight")
                wrong += 1
        elif not pingu_flies:
            print(f"    FAIL  {label} is an ORDERING and must not remove a "
                  f"conclusion -- if it does, ordering has become defeat")
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
    concluded and the agent carried straight on to quiescence. `stop` is one of
    the three things a postcondition can spend, beside `attend` and `unattend`.
    A row, not a branch, and the loop still knows nothing about goals: it knows
    a rule said stop.

    ⭐⭐⭐ **And the trigger everyone reaches for first is worth nothing.** The
    obvious proposal -- let a goal raise the priority of the rule that checks it
    -- was built and measured before this, and it moves NOTHING. A completion
    check is **self-gating**: it cannot match until the thing is done, and the
    instant it can, widening reaches it in the same move. Score decides which of
    several MATCHING rules wins; a check that can only match at the finish line
    has nobody to go before. Measured with the check at the floor, reranked,
    buffed persistently in two places, and standing. The rows below keep that
    null result where the next person to propose it will find it.

    ⚠⚠⚠ **TWO OF THE FIVE ROWS ARE GONE WITH THE BUFFS.** Both spent
    `boost(<done>, 20)` from a `when` trigger, and a `when` trigger is now
    refused outright -- nothing runs one. What remains of *raise the check's
    priority* is the `standing` row, which is the strongest lever of the four
    that were tried and still moves the run no earlier: a completion check that
    cannot match until the thing is done has nobody to go before, whatever its
    score. The null result is therefore still gated, by the arm that had the
    best chance of breaking it.

    ⚠ The check asserts the SHAPE of the null result rather than an equality:
    at most a move either way, against the tens of moves `stop` itself is worth.
    Written with the numbers in it so a drift shows. Equality was the sharper
    test and stopped being available when retiring `<relevant>` shifted the
    declaration RANK of every rule in every corpus -- rank breaks the tie when
    scores are equal at the floor.
    """
    print()
    print("  stopping -- a cart to build, and a check that says when it is done")
    bad = 0
    seen = {}
    cases = (
        ("", "no postcondition"),
        ("after <done> => stop", "stop, <done> at the floor"),
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
    # ⚠ A BOUND, not an equality -- see the docstring. It has to stay far
    # tighter than what `stop` buys, or it would stop being able to fail.
    drift = abs(seen["stop, and <done> standing"]
                - seen["stop, <done> at the floor"])
    worth = seen["no postcondition"] - seen["stop, <done> at the floor"]
    if drift > 1 or drift * 10 >= worth:
        print(f"    FAIL  raising the check's priority changed the run by "
              f"{drift} moves against {worth} for `stop` -- the null result "
              f"moved")
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
    return penguin() + stopping()


if __name__ == "__main__":
    raise SystemExit(main())
