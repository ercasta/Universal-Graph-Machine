# `core/attention.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

The loop: a table over rules, take the first that matches, then spend.

⭐⭐⭐ **This is the loop this repo ships, and it is the only one.** `Machine.run`
is three lines that call it; `Machine.tick` is five. What follows is the
argument that put it there, and it is written against a loop that no longer
exists -- kept in that tense on purpose, because the case for this one is the
comparison, and the comparison is what was deleted once it was settled.

The loop this repo shipped THEN weighed an option set: recall proposes,
everything matches, defeat and quiescence filter, arbitration ranks, one move is
taken.
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
join-not-scan that recovered `forgone`, for the
fourth time.

⚠ **Approximate on purpose.** A rule reading `wounded($x)` is lifted because
`goblin1` is wounded, whether or not it would bind `$x` to goblin1. That is the
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

    attend($x, n)   think about what this move just bound, and how much
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

## How many rules are matched before the loop admit

How many rules are matched before the loop admits its table was wrong. The
author's proposal, and it is what makes the design's performance claim
testable: score FIRST, then match only the top of the table. Everything below
is never matched at all -- unless nothing up here applies, and then the
shortlist widens.

Widening is the guarantee that keeps this honest, and it is the shipped rule:
*a dry shortlist is not a finished search*. Without it a miss in the top N
would deposit `quiet` while work remained, the agent would give up on goals it
could have reached, and the trail would show a completed search that never
ran. With it, the worst case is exactly today's cost and the best case is N.

## How long a buff lives, and how far a rule may be

How long a buff lives, and how far a rule may be lifted.

**Life.** A buff that never expires is what made the taught table run away:
`A` lifts `R`, `R` lifts `A`, and every lift is permanent, so the loop finds
How far attention lifts a rule that could be about what is attended.

Recomputed every move and kept nowhere, unlike a buff -- so there is no decay
to tune and no runaway to guard against. That is
this file's own line between the two kinds of attention, and a claim the agent
is currently making about what it is thinking about is plainly the second
kind: *what is in front of me is recomputed*.

Sized against `STANDING - FLOOR` (9), so a rule attention reaches can clear
the apparatus rather than merely climb past its neighbours at the floor. A
lift that could not do that would find the top of the table already full and
change nothing, which is the failure mode `_rerank` measured for shortlist-only
nudges: a mechanism that cannot bring a rule INTO consideration is not one
that can direct anything.

## The default doubt-settling rule, and the author'

The default doubt-settling rule, and the author's correction to an earlier
sketch of mine: the loop does not need to HOLD a tick waiting for doubt to be
resolved, because a settling rule fires. Depositing the doubt IS the move and
this rule gets the next turn. A corpus replaces it with something better (ask
the user, apply a domain criterion) by writing a rule that outscores it.

⚠ It used to carry `frozen after <settle-doubt> => boost($a, 1)` -- the
settlement was a buff, so it was calibratable. With the buffs retired it
concludes and nothing more, and the loop's own backstop is what makes
progress: the doubt already stands on the next tick, so `fresh` is false and
the winner applies. The boost was never what unblocked the run; it reinforced
a winner the loop had already chosen.

`$a` is the winner as the doubt named it. That is only writable because rules
are subjects here -- `close(<A>, <B>)` names them -- and because `_note`
deposits it as a MENTION, so a rule concluding about `$a` is not dropped by
quiescence as having nothing to deposit.

## There is no defeat

One thing decides what is in front of the agent, and it is the table: a score,
authored order, and `dormant` -- a claim, read every tick, that a rule is not in
the running until something claims `due`. Precedence is gone. There is no
relation that removes a rule the table put in front of the agent, and no step in
the loop that asks whether one applies.

`overrides` and `supersedes` were both subtracted rather than replaced, and what
each of them was actually saying turned out to be sayable already:

    `overrides(<gob-flees>, <gob-acts>)`     `no hp($x, 1)` -- a premise about
                                             the state, not about a rule
    `overrides(<hero-acts>, <hero-holds>)`   nothing: acting spends `may(hero)`,
                                             so the loser has no right left to
                                             act on and authored order settles it
    `overrides(<halt>, ...)`                 nothing: each actor needs its
                                             combatants present
    `supersedes(<outcome>, <assert-act>)`    `no substituted($what)` in the
                                             bundled rule, per ACT
    a rule settling a conflict between two   `dormant(<loser>)`, concluded by an
    of the agent's own rules                 ordinary rule and withdrawn by `due`

The last row is the one that carried the weight. Harmonization, acquisition and
the learned-rule policy were all written as *conclude a precedence*, and all
three say the same thing better as *take that rule out*: it is per rule either
way, it is a claim rather than a pair, it is revocable, and the corpus that
concluded it IS the record -- the engine used to deposit `defeated(<loser>,
<winner>)` to answer *which of my rules actually fight*, and the corpus was
already saying it.

What is genuinely lost is the case where a rule should be out only WHILE
another one applies. `overrides` never expressed that either -- it was per rule
and per tick, and the dungeon's `<hero-holds>` shows what per tick bought: an
accident that read like a mechanism. A corpus that wants it writes the premise.

## `_rivals`

The other ways of getting what this move is getting.

    ⭐⭐⭐ **Complete forgoing looked like it needed the option set, and it does
    not.** *What else could have served this want* ranges over every rule only if
    you ask it that way round. `_wants` reads what an application CONSUMED -- an
    application that consumed `goal(w)` is a response to wanting `w` -- so a
    rival is a rule that could consume `goal(w)` too, and **only a rule whose
    antecedent reads `goal` can.** That is a lookup over the rule set, and it is
    usually a handful.

    So the prefix scan keeps its window for CHOOSING and asks a second, narrow
    question for passing up: the same join-not-scan that recovered `forgone`,
    and the second time it has turned an apparent aggregate into an index.

    ⚠ Only when the move serves a want at all, which is the common case being
    cheap rather than an optimisation: most moves consume no goal and pay
    nothing.

## `_pull`

Attention's rule-level lift: two dict reads and no matching.

    ⭐⭐⭐ **The join, and the reason attention is affordable where a query is
    not.** *Which rules are about `goblin1`* looks like it needs matching --
    every rule is generic, so no rule's text mentions `goblin1` at all, and the
    only exact answer is *those with an application binding it*, which is the
    option set this loop exists not to build. Asked the other way round it is
    two lookups:

        goblin1 -> the relations it is spoken of under   (`relations_of`)
                -> the rules whose antecedent uses one   (`_by_relation`)

    ⚠ **Approximate, and deliberately so.** A rule reading `wounded($x)` is
    lifted because `goblin1` is wounded, whether or not it would bind `$x` to
    goblin1 rather than to someone else. That is the right amount of wrong: this
    decides who is MATCHED, not who wins, and being roughly right about a
    shortlist costs a slot. The exact answer arrives one layer up, in
    `_attended_first`, where the bindings are already in hand and free.

    ⚠ Not summed over attended nodes. A rule reachable from two attended nodes
    is not twice as relevant, and letting it be would make the lift a popularity
    count over whatever the corpus happened to attend to.

## POSITION is the strength. attended arr

⭐⭐⭐ **POSITION is the strength.** `attended` arrives newest-first, so
what the agent turned to last lifts hardest and what is about to fall off
the bottom barely lifts at all. That gradient is the whole reason the
queue exists: a FLAT lift moved 34% of the pool by the same amount every
tick (20d), which reorders nothing inside that third -- and counting, then
inverse frequency, were both attempts to buy back a differentiation the
ordering gives away for nothing.

⚠ A rule reachable from two attended nodes takes the STRONGER, not the
sum. Being about two things the agent is thinking of does not make a rule
twice as relevant, and summing would make the lift a popularity count over
whatever the corpus happened to attend to.

## `_attended_first`

Order a rule's own applications by what the agent is thinking about.

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

## pool is what makes an EXPERT possible: one s

⭐ `pool` is what makes an EXPERT possible: one shared graph, one shared
chain, and a table over a SUBSET of the rules. The loop does not know what
an expert is -- it is handed the rules it may consider, exactly as it is
handed the corpus. `ugm.experts` reads the subset off the graph.
⚠ Whether the pool was HANDED to us decides whether it may grow. An
expert's pool is what `knows` says it is, and a rule the agent adopts is
not that expert's until something says so. The default pool is *every
rule*, and that is a set the agent can add to at run time.

## A caller may bring its own table, and doc

⭐⭐⭐ **A caller may bring its own table, and `docs/interpretation-feedback.md`
§4 is right that the day it matters is the day something else changes.**
A host driving the agent one tick at a time calls this per `/step`, and a
table built here is free EXACTLY while no postcondition has moved it: with
no posts supplied a table is its defaults plus an ATTENTION lift
recomputed from the graph every tick, so a rebuilt table is the same
table. Supply
real postconditions and the rebuild silently discards every spend -- what
the agent learned *within* a run -- and nothing says so, because from
here nothing went wrong.

⚠ **The ticks continue from `table.now` rather than restarting at 0.**
Nothing in the table decays any more, so this no longer guards a lift's
age; it is what lets a caller stepping one tick at a time see a monotone
tick count rather than a saw-tooth.

## Not a phase: the world may have spoken since the

Not a phase: the world may have spoken since the last move, and the
loop asks the same question in the same place.

**The anchor a corpus reads the raw chain from.** Minting it is the
whole of this line -- `asking(<m>)` has to EXIST for a stratum-0 rule
to bind it, and a corpus has no hand to seed it with. Without it *it
was on, then it was not* cannot be written at all: the rule is well
formed, every other member matches, and it silently never applies.

One anchor rather than one per moment, and what that buys is cost.
The rule-level read is a fixpoint, so an unanchored read gives every
proposition its candidates and its winner -- `ask_read`'s own docstring
calls that the honest default and a costly one.

It used to buy a second thing, and no longer does. The line read
*anchored at the seat*, and the seat was where the agent was standing:
what it could read the chain about depended on where it stood, which
was containment as well as economy. There is no seat and no register
now, and one chain with one standpoint, so there is nothing to contain.
A caller can still anchor a read at a moment it names -- `ask_read`
takes them -- but that is a caller's choice, not a boundary.

## Satisfaction, ported from the tick this lo

⭐⭐⭐ **Satisfaction, ported from the tick this loop replaces.** `stop`
is the rule-level route and it stays the recommended one -- a rule
concludes that here is over and its postcondition ends the run. This
is the other half, and it is here rather than as a rule because the
**open-goal veto is an aggregate**: *nothing else is wanted and unmet*
is a claim about a set, and a rule cannot speak about the set of its
own matches. `Machine._enough` already reads `enough(...)` at the
focus and exercises the veto once per seat, so this calls it rather
than growing a second copy.

⚠ Inside a hypothesis, enough ends the BRANCH and not the run -- which
is `_leave`, the door that already existed, and is how *is this plan
settled* gets a local answer.

⚠ And it deliberately writes no `quiet`. `quiet` continues the loop so
a watchdog can key on it, because *the search finished* leaves work
worth doing and *nothing more is worth doing* does not.

## Dormancy, and it is the right form of dis

⭐⭐⭐ **Dormancy, and it is the right form of *disable a rule*.** A rule
claimed `dormant` is not considered until something claims it `due` --
which is all a callback is. Both are ordinary FACTS rather than a mark
the engine reads, so both are askable, defeasible and attributable, and
*which rules is this hypothesis carrying* is a query rather than a
field.

⚠ Read every tick and at the register's own position, never once when
the pool is built: `due` can be concluded mid-run, and a callback
attached inside a hypothesis must wake only there.
⭐⭐⭐ **THE `prefer` LIFT IS GONE, and what is left is the same lift
by a better key.** The table used to read `prefer(<R>, key, score)`
as a buff, which it is -- *when this is in play, think of R*. What is
wrong with it is not the arithmetic, it is the subject: it can only
ever name a RULE, so it cannot tell two goblins apart, and a lesson
keyed on `<R>` is stale the moment that rule is adopted, composed or
renamed. Measured on the dungeon, every rule-naming arm lost to the
node-naming one, and `occasion` was worse than doing nothing.

Attention keys on a NODE, is read at the same point in the move, and
is what `learned` now writes. Nothing else about the lift changed.

⚠ Ranking-time and kept nowhere: an attention claim is a fact the
corpus is currently making, so the lift
is a function of the state and re-deriving it is the whole of keeping
it current. Making it a buff would give it a life and a saturation
ceiling on top of a claim that already has both -- the claim is
denied, and it is over.

## The queue has two uses and only one of the

⚠⚠⚠ **The queue has two uses and only one of them can starve.**
Ordering a rule's own BINDINGS costs nothing -- the applications are
already in hand. LIFTING rules changes which are matched at all, so a
queue full of whatever the last move wrote can push the shortlist onto
recently-touched rules and leave work unreached: measured, the dungeon
quiesced 32 moves early and lost 48 conclusions.

So the lift is driven by what a LESSON asked for -- a weighted
`attend($x, n)` -- and the whole queue orders bindings.

## `_survives` is the per-candidate filter

`_survives` is the per-candidate filter: passed up, quiescent, or already spent
on these premises. Refraction stays, because *this instantiation has run* is not
the same claim as *this rule's score is low*, and keying firing-once to the rule
would stop it ever applying to new data.

Nothing else filters here. Taking a rule out of the running is decided where the
ordering is built, from `dormant`, and it is per rule -- so a filter that reads
one application at a time is the wrong place to ask it, and there is no longer a
question to ask.

## Nothing in the table matched. The engine says so

Nothing in the table matched. The engine says so and nothing
more: `quiet(<seat>)` is a fact about the machinery, like the
doubt, and it is what every rule that reacts to the loop having
stopped is waiting for -- `<give-up>`, the watchdogs, `blocked`.
Without it the bundle never gets its turn, which is why the first
version of this loop never acted at all on `quest-p1`.
⭐⭐⭐ **Effort, and the order is the old tick's exactly.** A
shortlist that ran dry is not a search that finished, and neither
is a search that never looked at what it had put out of mind. Both
deposit -- `widened(<seat>)`, `reached(<seat>)` -- so *I had to go
and get that* is a sentence a corpus can write.

⚠ These are NOT ported logic. They are the loop reporting its own
event, which is the same shape as `quiet` and `arrived`: the
smallest unarguable record of something only the loop can know.
`Machine._widen` already reads the budget knob off the graph and
guards once per seat, so this calls it rather than growing a
second copy that would drift.

## ...and the backstop: the doubt already stands an

...and the backstop: the doubt already stands and nothing settled
it, so restating it changes nothing and the winner applies. A
corpus with no settling rule loses a tick, not the loop.
⚠⚠⚠ **Something applied, so the shortlist is trusted again.** The old
tick resets this on every application -- *widening is a state the
agent is in, not a mode it is switched into* -- and this loop did not,
so after the first dry shortlist it never reached past one again for
the whole run. One line, and it is a real behavioural difference
rather than a record: measured, 3 widenings became 1.
⭐⭐⭐ **Taking one way of getting something passes up the others**, and
this loop was not saying so -- which cost `ugm.learning` and
`ugm.practice` entire, because rehearsing safely IS choosing and then
naming what you did not do.

⭐ And it names the rivals the agent ACTUALLY WEIGHED -- the window --
where the option-set loop named every application it had materialised.
That is the more honest record of the two: *what did you pass up* ought
to mean *what did you consider and not take*, not *what existed*.

⚠ `forgone` stays out of `ACCEPTED_LOSSES` for the corpus gate all the
same: the two loops weigh different sets, so they legitimately pass up
different things.

## AFTER the move, not at the choice: a tick that d

AFTER the move, not at the choice: a tick that deposits a doubt
chooses and then does not apply, so watching at the choice
recorded a rule that never ran -- and a lesson built from that
sequence teaches a move that never happened.

⭐ **...and the `Step` goes with it, which is the whole of
`docs/interpretation-feedback.md` §4.** Watching after the move
means `_spend` has already appended its refraction bookkeeping, so
a watcher asking the CHAIN *what did that move write* over-reports
by a `spent(...)` term -- and the harness was wrapping
`Machine._apply` on the instance to get the honest answer. It is
the one place it reached inside the engine. The step already
carries `wrote`, the entries the application itself deposited, so
the answer was here all along and nothing was handing it over.

## The loop ran out of ITERATIONS, not out of w

⚠ **The loop ran out of ITERATIONS, not out of work.** The first version of
this asked whether the last `Step` was `applied`, and the last step is
never `applied` -- the loop appends a `quiescent` or `stopped` step when it
finishes and appends nothing when the `for` simply runs out. So the test is
the absence of an ending: a run that finished wrote one, and a run the
budget cut off did not.

A run that stops because there is nothing left to do has not been bounded
by anything, and saying it had would make the record useless in the other
direction.

## `penguin`

The author's example, and it found the mechanism's real boundary.

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
        dormant(<flies>)       no            NO         removal, and TOO COARSE
        representation         no            yes        the only one that works

    ⚠⚠⚠ **Taking the general rule out grounds tweety as well, and that was not
    expected.** `dormant(<flies>)` is removal per RULE: `<flies>` is out for
    everybody, so the ordinary bird stops flying too. It solves the penguin by
    breaking flight, which is not solving it. Removal is the right KIND of
    answer and the wrong GRAIN -- the claim needs to be about this binding, and
    a claim about a rule cannot say that. `overrides` was measured here first
    and behaved identically, which is part of why it is gone.

    ⭐ What does work is representation: state `-penguin(tweety)` and let
    `<flies>` read it. The general rule keeps working for ordinary birds and
    declines for this one, because the corpus said something it knew rather than
    leaving it to a score. §9's positive tests, with the negative WRITTEN rather
    than inferred from silence.

    ⭐ `tweety` is the control and is the whole reason this table is worth
    printing. Without it removal and representation look identical, and the
    lever that breaks flight passes.

## `stopping`

`stop`, and the two things measuring it settled.

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
