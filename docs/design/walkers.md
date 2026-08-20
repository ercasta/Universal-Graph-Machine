# `walkers.py` — the argument

> ⚠⚠⚠ **The module is DELETED (2026-08-20).** This file is kept because five
> other documents cite what it measured, and because the prose *is* the record
> of it — but nothing here describes live code.
>
> Why it went: `<step>` and `<fork>` have identical antecedents and contend for
> one walker position, and the probe's claim was that the contention *is visible
> as a window of two*. It is not, reliably. The recall table is matched in
> chunks of `SHORTLIST = 5` and the loop stops widening the moment its window is
> non-empty, so whether a rival is seen depends on where the two rules fall
> relative to a chunk boundary. The situations deletion took two rules out of
> the bundle (23 → 21), which moved `<step>` to index 19 — the last slot of the
> chunk 15–19 — and `<fork>` to 20. `<step>` matched, the window filled, and
> `<fork>` was never matched at all. Changing `SHORTLIST` to 6 and nothing else
> restored the old numbers exactly.
>
> ⭐ That is a finding about the ENGINE and not only about the fixture: whether
> the agent notices it is choosing under doubt — `close(<R1>, <R2>)` — depends
> on table position. `docs/todo.md` carries it as an open question.
>
> ⚠ What is no longer measured anywhere: *moving loses a branch silently*, and
> the by-path/by-node growth rates.

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

A walker is a position on a NODE, and it is an ordinary fact.

    python -m ugm.probes.walkers

The design has three positions already and none of them is this one:

| | differs in | mechanism |
|---|---|---|
| agents (`ugm.table`) | what they **believe** | separate graphs |
| experts (`ugm.experts`) | what they **know how to do** | a rule pool |
| frames (`gate.Frame`) | **when**, and under what supposition | seat and topic, both moments |
| **walkers** | **where in the structure** | `at(<w>, <node>)` -- this file |

A frame is not the missing one, and the confusion is worth naming because it
cost an hour: `frame(seat, topic)` is a position in the CHAIN. Both members are
moments. It answers *as of when*, never *about what*. So a walker needs no
frame, no register and no engine change: its whole state is a fact.

    at(<walker>, <node>)        where it stands
    child(<walker>, <node>)     a walker it spawned, minted from bound variables

Both are ordinary. `child(?w, ?y)` is a compound term over BOUND variables, so
the gate accepts it -- what a rule may not do is conclude about a variable
nothing binds, and this binds both. That is the whole of spawning.

## A walker SPAWNS rather than MOVES, and the reason is a measurement

The obvious design has a walker step from node to node, denying its old
position. It loses branches, silently:

    <step> = causes( { +at(?w,?x), +door(?x,?y) }, { -at(?w,?x), +at(?w,?y) } )
    <fork> = causes( { +at(?w,?x), +door(?x,?y) }, { +at(child(?w,?y), ?y) } )

Both want `at(w, r2)`. Whichever applies first denies it, and the other is not
refused -- it is DEFERRED until its premise no longer exists. Arbitration
decided the shape of the search, and nothing said so. On the maze below that run
finds nothing at all, and it is the cheapest-looking of the three:

    spawn (no move)        ticks   8   per walker 1   tried 192   found 1
    move + fork            ticks   4   per walker 2   tried 100   found 0
    move + fork, ordered   ticks   8   per walker 1   tried 200   found 1

**The run that fails is the one that looks efficient.** Fewer ticks, less work,
no error, no diagnostic. That is this repository's standing failure mode
arriving in a new place, and it is why the check below asserts the absence of a
find rather than the presence of one.

The third row is the repair that is not one. `overrides(<fork>, <step>)` was
meant to order the two; what it actually does is make `<step>` undead -- its
positions are IDENTICAL to spawn-only, so it never applied once, and the extra
six `tried` is the price of carrying a rule that cannot fire. `overrides` is per
RULE, and what a walker wants is *fork before stepping AT THIS NODE* -- narrower
than a rule, wider than one instantiation. `overrides` is too broad and
`supersedes` too narrow; both were measured before, and this is a third case
where neither grain fits.

So: spawning has no premise to contend over, and the design question disappears
rather than being solved.

## What the spawn design buys, stated as numbers

**The option set per WALKER is ONE.** No walker in the spawn run ever has two
applications weighed about it -- the branching lives in the walker POPULATION
rather than in any walker's choice. That is the whole argument for a walker
having a small action space: *which move was good* is answerable when there is
one option and hopeless when there are forty, so credit assignment becomes
possible at all. Nothing here learns yet; this is the property that makes
learning worth attempting.

⚠⚠⚠ **Per walker, and it used to be measured per WINDOW, which is not the same
claim and broke the day something unrelated moved.** A window holds every
application the agent weighed across ALL walkers, so two walkers with one option
each make a window of two while nothing about any walker's choice has changed.
It read 1 by luck: scores are equal at the floor, so which rules reach a
shortlist is decided by declaration rank, and adding three rules to the bundle --
rules that never match in this file at all -- shifted every corpus rule by three
and made it 2. The measurement was of the table's layout, not of this design.
The distinction it now draws is sharper as well as sounder: `move + fork` weighs
two options ABOUT ONE WALKER, which is exactly the contention this file is
about.

**A walker's identity is its path.** `child(child(w1, r2), r4)` is not a label,
it is the route: r1, then r2, then r4. Provenance falls out of minting identity
from bound variables, and nothing records it.

## What goes in the identity term is the deduplication policy

Two routes into one room. `child(?w, ?y)` names a walker by the PATH it took, so
two arrivals at the same node are two walkers -- and each explores the subtree
below it again. Chained diamonds, measured:

    1 diamond(s),  4 rooms:  by-path    5   by-node    4
    2 diamond(s),  7 rooms:  by-path   13   by-node    7
    3 diamond(s), 10 rooms:  by-path   29   by-node   10

`2^(n+2) - 3` against `3n + 1`. Nothing errors, the treasure is still found, and
the run simply does exponentially more of the same work: the third case for
running out of everything before anything says so.

`walker(?y)` fixes it in one word, and the fix is INTERNING rather than a guard:
`g.rel` returns the same node for the same relation and members, so two arrivals
at `r4` mint one walker and the second is not a new fact at all. No visited set,
no negation -- which matters, because the negation a visited set wants is over
entries, where `-` means DENIED rather than absent, and the first draft of this
file matched nothing for exactly that reason.

The general term is `walker(<node>, <purpose>)`, and both designs are its special
cases: drop the purpose and arrivals merge, make the purpose the path and they
never do. So the identity term IS the policy, stated where a reader can see it.

**And deduplicating is not forgetting.** Identity is WHERE a walker is;
provenance is HOW it got there, and provenance is plural. One walker at `r4`,
both routes recorded:

    at(walker(r4), r4)
    came(walker(r4), via(walker(r2), r2))
    came(walker(r4), via(walker(r3), r3))

## An expert is a PREMISE, not a pool

`ugm.experts` gives a rule set read off the graph -- `knows(<e>, <r>)`,
`extends(<e>, <f>)`, inheritance as one ordinary rule -- and hands it to a run as
`pool`. That is one rule set for a whole run, so it cannot say *this rule applies
to walkers running E*, which is what a swarm needs.

Scoping by PREMISE can, and costs nothing:

    fact +knows(scout, moving)         fact +extends(raider, scout)
    fact +knows(looter, grabbing)      fact +extends(raider, looter)

    rule <extend> = implies( { +extends(?e,?f), +knows(?f,?c) }, { +knows(?e,?c) } )
    rule <equip>  = implies( { +runs(?w,?e),    +knows(?e,?c) }, { +can(?w,?c)   } )

    rule <grab>   = implies( { +at(?w,?x), +can(?w, grabbing), +treasure(?x) },
                             { +found(?w,?x) } )

Multiple inheritance falls out: two `extends` facts both match, so `raider` has
`moving` from one parent and `grabbing` from the other, through one rule and no
resolution order. And a SPAWNING rule chooses the child's expert, which is what
*spawn an expert at a node* means here -- pass `?e` down and the child inherits
the role, name another and it does not. Measured: with children spawned as
`scout`, the treasure is never taken, because a scout cannot loot.

## Termination is a DENIAL, and it is not retroactive

Every walker-relative rule needs `at(?w, ?x)`, so denying that one fact removes
the walker from all of them at once:

    rule <done> = implies( { +found(?w,?x) }, { -at(?w,?x) } )

No scheduler, no registry, no removal step -- there is nothing holding the walker
except the fact that it is somewhere.

What it does NOT do is undo. The looted walker spread to the next room BEFORE it
was terminated, and which of the two happened first was decided by arbitration
with nothing saying so.

## Precedence only bites when the loser's PREMISE CAN BE DESTROYED

Four attempts to order rules in this file behaved four different ways, and the
rule behind all of them is one sentence.

    <fork> vs <step>        the loser's premise is DENIED by the winner
                            -> ordering decides the outcome, silently
    <spread> vs <done>      same, and the ordering that decides it is the
                            order the rules were DECLARED IN: spread first and
                            the walker reaches the next room, spread last and
                            it never does
    overrides(fork, step)   the winner matches wherever the loser does
                            -> the loser never gets a tick at all
    overrides(grab, spread) the winner matches only where treasure is
                            -> the loser is suppressed there and nowhere else
    two corridors           monotone rules, nothing destroyed
                            -> B is fully explored either way, 17 ticks vs 21

`overrides` suppresses per TICK and per RULE, whenever the defeater matches
anywhere. Because the loop runs to quiescence, a merely-deferred rule applies on
some later tick and the final state is the same -- *ordering is not
defeasibility*, this design's own line, arriving from a fourth direction. The
only time order changes what is CONCLUDED is when the winner destroys what the
loser needed.

So the spawn design does more than keep branches: **nothing is consumed, so
ordering is irrelevant, so the per-position precedence a moving walker wanted is
not needed at all.** The missing mechanism was missing because of the other
design.

## What this does not do

**Cycles are unbounded.** `child(child(child(...)))` grows without limit on a
maze with a loop, and the guard a corpus would reach for -- *do not go where you
have been* -- is a negation over entries, where `-` means DENIED rather than
absent. The first version of this file was written with `-seen(?w, ?y)` and
matched nothing at all. The honest fix is the stratum-0 bridge `ugm.interpret`
uses, and it is deliberately not done here: this file is about position, and
that is about negation.

**Nothing is scheduled.** The walkers run under the ordinary loop, in whatever
order arbitration picks. A declared-order scheduler is `ugm.table`'s problem
already solved, and only speculative walkers -- ones at different SEATS -- would
need it, because only those have separate materialised states.

**Nothing waits.** A walker that parks until a subgoal completes is `dormant`
until something claims `due`, which is shipped and untouched here.

## Per WALKER, not per window, and the differ

⚠⚠⚠ **Per WALKER, not per window, and the difference is the whole claim.**
This read `max(rep.windows)` and called it *one option is weighed per
move*. It is not the same measurement: a window holds every application
the agent weighed, across ALL walkers, so two walkers with one option each
make a window of two and nothing about any walker's choice has changed.

It read 1 for a long time by luck. Scores are equal at the floor, so which
rules reach a shortlist is decided by declaration RANK -- and adding three
rules to the bundle, which never match here at all, shifted every corpus
rule by three and made it 2. A check that an unrelated change can break
was measuring the table's layout, not this file's design.

The claim is *the branching lives in the walker POPULATION rather than in
any walker's choice*, so the measurement is: group each window by the
walker its applications are about, and take the largest group.

## THE TICK COUNT IS NOT ASSERTED, and that i

⚠⚠⚠ **THE TICK COUNT IS NOT ASSERTED, and that is the third time this
fixture has been moved by an edit somewhere else.** It read
`ordered["ticks"] != plain["ticks"]` -- *ordering changed WHEN* -- and the
two counts now coincide at 18, because retiring `<relevant>` made the
bundle one rule shorter and declaration RANK is what breaks the tie when
scores are equal at the floor. The call-stack rules did the same in 20e,
and a bundled `<unattended>` did it again.

> **A check on a tick count in this fixture is measuring the size of the
> bundle, not the thing it names.**

What the claim is actually about survives untouched and is what is gated:
nothing was destroyed, so the unrelated corridor is fully explored either
way. The counts are printed above, where a drift is visible without being
load-bearing.
