# `probes/alternation.py` — the argument

The agent takes one move; the world runs to quiescence; then it is asked again.

## Two pools, and neither corpus mentions the other's vocabulary

`probes.experts` built a table over a SUBSET of the rules so one expert could
consult another. The same mechanism separates deliberation from physics: the
world's rules say what follows from an act (`did`, `achieves`, `intact`), the
agent's rules say what to do about an open gap (`missing`, `doing`), and
neither names the other's relations. One graph, one chain, two tables.

That separation is not decoration. It is what makes *run the world to
quiescence* a sentence at all: quiescence is a property of a rule set, and
without a pool there is only one rule set to be quiet.

## What alternating buys, and what it does not

**It fixes the timing.** The world has settled before the agent is asked again,
so there is no window in which the agent commits to a second route while the
first is still in flight. Every guard invented for that window -- a `pending`
fact, a spent occasion, a `forgone` deposit -- is unnecessary here, and the
probe carries none of them.

**It does not fix the wanting.** The control is the same alternation with the
agent keyed on `goal(...)` instead of on the gap:

    cycle 1  use-jug   (world settled in 4)
    cycle 2  use-tap   (world settled in 2)
    emitted ['smash(jug1)', 'fill(kettle)']

Two acts for one want. The world settled in between and it changed nothing,
because `goal(water(kettle))` is still asserted after the water arrives. **A
goal outlives its own satisfaction**; settling cannot retract what nobody
denied.

Keyed on the gap, recomputed at a settled world, the same corpus emits one act
and then has nothing to do. A want computed from the state cannot outlive what
closes it. That is the whole difference, and it is the reason the gap is worth
having beyond planning.

## Where competence goes

With the architecture guaranteeing one act per want, a lesson decides WHICH of
the open routes is taken and nothing else. Untaught the probe smashes the jug;
`attention(sink, 3)` and it fills the kettle. Competence orders; it never has
to remove, which is the standing answer to why a lift was never going to be
enough on its own.

## Which way is style

Where a want has more than one way to it, the choice is not a defect to be
managed. Two agents, one corpus, one weight apart:

    careful   (attention(sink,  3))   ['fill(kettle)']
    barbarian (attention(sink, -3))   ['smash(jug1)']

The barbarian is not broken. It reaches the want by the way it prefers, and the
jug is what that costs. A negative weight is what lets a corpus say *this way is
against my character* without saying it is unavailable -- which is the whole
difference between a weight and `dormant`, and the reason both exist.

## Revising, and not re-attempting

A route that did not deliver leaves the gap open, so the alternative is taken on
the next cycle:

    cycle 1  use-tap   (the tap delivers nothing)
    cycle 2  use-jug
    emitted ['fill(kettle)', 'smash(jug1)']

Passing up is revisable by construction, and nothing had to be un-said to revise
it -- where a `forgone` deposit had to be denied by a corpus rule, and a spent
goal had to be re-asserted.

⚠ And the failing route is not re-attempted: with one route and no delivery the
agent tries it once and stops. Refraction already says *not again on these
grounds*, so nothing has to weigh a re-attempt down. A weight is the wrong tool
for it anyway -- `attention(sink, -3)` says *this way is against my character*,
which is a claim about style and holds whether or not the way has been tried.

## What is not answered here

**What "settled" means for a world with standing rules.** This world goes quiet
in two to four moves. A world with a clock, a watchdog, or any rule that
re-derives from its own output has no quiescence to wait for, and the agent
would never be asked again. A bound is the obvious answer and it is not the
same thing.

**Who drives the alternation.** The probe drives it from Python, which is the
honest way to measure it and the wrong way to ship it: *whose turn is it* is a
claim, and a claim belongs in the graph.

**And there is deliberately no general answer to failure.** Nothing here tracks
attempts, counts them, or hands an alternative back on the agent's behalf. What
to do when a way does not deliver is a corpus's, and different characters answer
it differently -- the barbarian tries the other door, the careful one asks. A
generic attempt-manager would make that decision once, in the machinery, for
every corpus that ever runs; the measurements above say it is not needed to
avoid doing two things at once, which was the only reason to want one.
