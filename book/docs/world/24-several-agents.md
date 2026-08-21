# Several agents

Everything so far has been one mind. Chapter 21 gave it channels — a way for the
world to speak to it, and a way for its intents to leave.

Point two of those at each other and you have a second thing entirely: **a table
of agents**, each with its own beliefs, talking.

```
dm ── +doing(tell(p1, locked(door1))) ──▶ actuator ──▶ [wire] ──▶ channel ──▶ says(dm, locked(door1), plus) ── p1
```

An agent's beliefs are **its own chain**. Nothing is shared: two machines hold
two graphs, and a node in one names nothing in the other. What crosses is an
**utterance** — rendered text, re-read in the receiver's own name scope — and
what the receiver does with it is a trust rule in its corpus.

## The wire is only a wire

That's the whole of the new machinery, and it must stay that way:

> The moment the wire decides which utterances are worth believing, hard-wired
> intake is back and no corpus can argue with it.

The wire renders what one machine emitted, hands the text to another machine's
channel, and decides whose turn it is. It does not decide what anyone believes.

That both ends already existed is the interesting part. `actuator` is the channel
that carries intents **out**; the loader's `say` is the scoped door for arrivals
**in**. Between them there was nothing left to design — Chapter 21, read end to
end.

## Two minds are two scopes

The first draft of this used **one machine and several frames**, and argued
*against* separate machines on the grounds that they share no node identity.

That was exactly backwards.

Identity is decided at intake, in a scope. So `sword` in the DM's head and
`sword` in a player's head **should** be different nodes. Separate machines give
belief separation **structurally**, rather than by a corpus being careful.

And frames couldn't have done it without a floor change: a frame branched off a
shared trunk cannot see the trunk advance, so the shared world stops being shared
at the moment it changes. With separate machines there is no trunk — the DM's
world is simply the DM's beliefs, and everything else learns of it by being told.

## Fog of war is structural

That's not a slogan; it's what the checks assert. Before anyone is told, the
players hold **nothing** about the door — not because the corpus was careful, but
because the fact is in a graph they cannot reach.

And two more, which together are the distinction `arrived` and `says` exist to
keep:

- Delete a player's **trust rule** and it is told, and still believes nothing.
- What it was told is **still on its record**. Heard, not believed.

An utterance is also **directed**. The DM spoke to one player, and the other has
no record of the DM speaking at all — broadcast would leak the world to an agent
no rule ever told.

## A round is a barrier

Every agent runs to quiescence; then everything said is delivered.

So an utterance made in round N is heard in round N+1, **never mid-thought**.
That's what makes the whole thing deterministic, and it's checked directly: it
takes two rounds for a word to travel two hops.

## What cannot cross

Probed rather than assumed — and all of these are refused **at the receiver's
parser**, none silently mangled:

| | |
|---|---|
| a proposition — `locked(door1)` | re-reads fine |
| a moment — `moment()` | **refused** |
| an entry — `entry(moment(), locked(door1), +)` | **refused** |
| a rule — `<narrate>` | **refused** |
| anything containing a variable | **refused** |

An utterance that does not **round-trip** is refused too: the wire re-renders
what was understood, and a truncation is caught at source.

And structure survives intact — `a(b)(c)` is heard as itself, and is a *different
node* from `a(b(c))` at the far end. Which is what stops *a composed with b* and
*a applied to b of c* being one thing between two agents.

## Two real ceilings

Both fall out of rules you already know, and both are worth knowing before you
design around them.

**Two agents can never refer to the same time.** Every moment renders as
`moment()`, so even a parser that accepted one would lose its identity. Chapter
23 made *the goblin acts after the hero* writable **within** one agent; between
agents, *you attacked before I did* has no route at all. If a table is ever to
agree on sequence, a moment needs a renderable, re-readable name.

**No agent can teach another a rule.** It falls out of *a fact may not contain a
variable* (Chapter 8). So a DM can say *the door is locked* and can never say
*locked doors need keys*.

Whether that second one is a position or an accident is an open question, and it
is recorded as one.

## What it costs

Startup is not a constraint: **about 5ms per machine**, 18 shipped rules each, and six
agents cost **37ms**.

And the transport is a swap rather than a redesign — one OS process per agent
over queues produces the **identical transcript and the identical beliefs**,
round for round, because crossing is already text.

!!! note "Deep dive: never compare node ids across machines"
    Two graphs built in the same order assign the same integers. Probed twice:
    equal in one case, unequal in another.

    So a cross-machine identity test is **accidentally right often enough to pass
    a check**. Compare rendered text.

!!! note "Deep dive: an A/B is blind to any bug both arms share"
    Two transports were built and checked against each other — nine checks, all
    green. **Two real bugs were invisible to every one of them**, because both
    live in the agent, which both transports use: shipping the whole cumulative
    emitted list (so everyone re-tells everything, every round, for ever — and
    it is quiescence-proof, because each arrival is a fresh entry), and
    delivering every utterance to every agent.

    The comparison could not see either, because the comparison *was* the
    instrument.

    The fix was checks that **pin the behaviour** rather than compare the arms —
    *nobody repeats themselves and the table goes quiet*, *an utterance is
    directed and the third agent has no record of the speaker*. Both were written
    by putting the bug in first.

    And one of them was worse than useless as first written: the transcript
    comparison catches out-of-order collection only when the scheduler *happens*
    to reorder replies — green on most runs with the bug present. The ordering is
    now a pure function handed a deliberately reversed input, so it fails every
    run.

    > **A check whose sensitivity depends on a race reports green while the bug
    > is there, which is worse than not having written it.**

## The other axis: experts

There's a second way to have more than one mind, and it is not a smaller version
of this one. It's the opposite axis, and confusing the two is the mistake worth
avoiding:

| | **agents** | **experts** |
|---|---|---|
| what differs | what they **believe** | what they **know how to do** |
| the graph | one each, disjoint | **one, shared** |
| what crosses | an **utterance**, re-read in the hearer's scope | nothing — a conclusion is simply there |
| fog of war | structural | none, by construction |

Two agents can disagree about whether the door is locked. **Two experts cannot**,
because there is one chain and one answer. What an expert has of its own is a
**rule set and a table** — which is exactly what Chapter 27 said expertise
consists of: *the right rules coming to mind at the right moment.*

An expert is a **subset of the rules, read off the graph**:

```
knows(geometry, <area>)          this expert has this rule
extends(geometry, arithmetic)    ...and everything that one has
```

And because those are ordinary facts, inheritance is **one ordinary rule** —
transitive for free, with no engine support at all:

```
rule <inherit> = implies( { +extends(?e, ?f), +knows(?f, ?r) },
                          { +knows(?e, ?r) } )
```

A corpus writes `expert geometry extends arithmetic` as a convenience over
exactly that. *Which rules does this expert have* stays an ordinary query, and a
rule can conclude `knows(...)` at run time — an expert that **learns** a rule is
adoption (Chapter 29) plus one fact.

### Consulting one

```
+consult(geometry, area(plot1))         the request
+question(area(plot1))                  what the consulted expert sees
+reply(area(plot1), 12)                 what it concludes
+answered(geometry, area(plot1), 12)    what the caller sees
```

That last line is deliberately **a tool's answer** (Chapter 22). From the
caller's side an expert and a tool are the same shape, so a corpus that consults
one can be pointed at the other without touching a rule. Which is the honest
definition of the difference:

> A **tool** is a request answered by a function rather than by a search.
> An **expert** is a request answered by a *search* rather than by a function.

And an expert may consult an expert, so it's a stack:

```
geometry <- area(plot1)
  geometry <- perim(plot1)
    arithmetic <- twice(3)
      -> 6
    -> 6
  -> 12
```

!!! note "Deep dive: the cycle test is on the pair, not the expert"
    Depth alone won't do. `A → B → A` asking something *new* is ordinary
    recursion and must be allowed; asking the same thing again is the loop. So
    what's refused is a repeated **(expert, question)** already on the stack.

    And the refusal goes **on the record** — `refused_consult(...)` — because a
    consultation that quietly returns nothing is indistinguishable from one that
    had nothing to say. Chapter 13's rule about silences, arriving in a new
    place.

    Two things this cost, both found by building. The first version ran a
    consulted expert and returned, leaving anything *it* asked for to the outer
    loop — so the stack was never deeper than one and the cycle test could never
    fire. Worse, the check asserting depth **passed anyway**, because it read the
    indentation off a log the code had written itself. A check built out of the
    thing under test degrades with it.

    The second: a refused consultation has to be marked *handled*, or the request
    is handed back for ever and the refusal is recorded once per look instead of
    once per request. Measured: 231 identical refusals.

**What it costs, stated rather than discovered.** An expert's conclusions are
**not contained**. One chain was the whole point, so a consulted expert that
concludes nonsense has concluded it for everybody. That's the price of sharing
beliefs, and it's precisely why the agents above exist for the other case.

## A third axis: walkers

There is a third way to have more than one of something, and it took an hour to
find only because a fourth thing looked like it. Laid out together:

| | differs in | mechanism |
|---|---|---|
| **agents** | what they **believe** | separate graphs |
| **experts** | what they **know how to do** | which rules they have |
| **frames** | what the agent is **attending to** | a queue, an expert, and that expert's table |
| **walkers** | **where in the structure** they are | `at(<w>, <node>)` |

A frame is not the missing one. A frame is a *line of work* — what was pushed,
which expert is in play (Chapter 25) — so it answers *what am I doing* and
never *where in the structure am I*. A walker needs no frame, no register and
no engine change, because its whole state is a fact:

!!! warning "This section's measurements are history"
    The walker **pattern** below still works — it is ordinary corpus writing,
    and nothing in the engine has to know about it. The probe that produced the
    numbers in this section was **deleted**, because its central claim (that
    contention shows up as a window of two) turned out to depend on where two
    rules happened to fall relative to a shortlist boundary rather than on
    anything about the design. Read the figures as a record of one run, not as
    something you can reproduce.

```
at(<walker>, <node>)        where it stands
child(<walker>, <node>)     one it spawned
```

`child(?w, ?y)` is a compound term over **bound** variables, and that is legal in
a consequent: a rule may introduce an individual as long as it is **denoted**.
What a rule may not do is conclude about a variable nothing binds. That is the
whole of spawning.

### A walker spawns rather than moves, and that is a measurement

The obvious design has a walker step and deny where it was:

```
<step> = causes( { +at(?w,?x), +door(?x,?y) }, { -at(?w,?x), +at(?w,?y) } )
<fork> = causes( { +at(?w,?x), +door(?x,?y) }, { +at(child(?w,?y), ?y) } )
```

Both want `at(w, r2)`. Whichever applies first **denies** it, and the other is
not refused — it is deferred (Chapter 17) until its premise no longer exists. On
a maze whose treasure is behind the second door out of one room:

```
spawn (no move)        ticks 7  max window 1  tried 146  walkers 5  found 1
move + fork            ticks 4  max window 2  tried  88  walkers 1  found 0
move + fork, ordered   ticks 7  max window 1  tried 152  walkers 5  found 1
```

> **The run that fails is the one that looks efficient.** Fewer ticks, less work,
> no error and no diagnostic.

Which is why the check asserts the **absence** of a find rather than the presence
of one. The third row is the repair that is not one: `overrides(<fork>, <step>)`
makes `<step>` undead — it never applies at all, and the extra six `tried` is
what it costs to carry a rule that cannot fire.

There is also a quieter payoff. Every window in the spawn run has **size 1**: a
walker never weighs two moves, because the branching lives in the walker
*population* rather than in any walker's choice. *Which move was good* is
answerable when there is one option and hopeless when there are forty, so this is
the property that makes a policy over walkers learnable at all.

### What goes in the identity term is the deduplication policy

Two routes into one room. Name a walker by the **path** it took and two arrivals
are two walkers, each re-exploring everything below. Chained diamonds, measured:

```
1 diamond,   4 rooms:   by-path   5   by-node   4
2 diamonds,  7 rooms:   by-path  13   by-node   7
3 diamonds, 10 rooms:   by-path  29   by-node  10
```

`2^(n+2) − 3` against `3n + 1`. Nothing errors and the treasure is still found;
the run simply does exponentially more of the same work.

`walker(?y)` fixes it in one word, and the fix is **interning** rather than a
guard: the same relation over the same members is the same node, so two arrivals
mint one walker and the second is not a new fact at all. No visited set and no
negation — which matters, because the negation a visited set wants is over
**entries**, where `−` means *denied* rather than *absent*, and the first draft
of this fixture matched nothing for exactly that reason.

> **The identity term is the deduplication policy.** `walker(<node>, <purpose>)`
> is the general form: drop the purpose and arrivals merge, make the purpose the
> path and they never do.

**And deduplicating is not forgetting.** Identity is *where* a walker is;
provenance is *how it got there*, and provenance is plural. One walker at the
join, both routes on the record:

```
came(walker(j0), via(walker(a0), a0))
came(walker(j0), via(walker(b0), b0))
```

### An expert can be a premise rather than a pool

Consulting an expert hands a whole request to one rule set, which is the right
grain for a question and the wrong one for a swarm: it cannot say *this rule
applies to the walkers running E*. Scoping expertise by **premise** can, and it
costs nothing beyond the `knows` and `extends` facts already above:

```
rule <extend> = implies( { +extends(?e,?f), +knows(?f,?c) }, { +knows(?e,?c) } )
rule <equip>  = implies( { +runs(?w,?e),    +knows(?e,?c) }, { +can(?w,?c)   } )
rule <grab>   = implies( { +at(?w,?x), +can(?w, grabbing), +treasure(?x) },
                         { +found(?w,?x) } )
```

Multiple inheritance falls out: a `raider` that extends a `scout` and a `looter`
has `moving` from one and `grabbing` from the other, through one ordinary rule
with no resolution order to declare. And the **spawning** rule chooses the
child's expert — pass `?e` down and the child loots, spawn it as a `scout` and
the treasure is never taken, because a scout cannot.

### Termination is a denial, and it is not retroactive

Every walker-relative rule needs `at(?w, ?x)`. So one denial removes the walker
from all of them at once:

```
rule <done> = implies( { +found(?w,?x) }, { -at(?w,?x) } )
```

No scheduler, no registry, no removal step — there is nothing holding a walker
except the fact that it is somewhere.

What it does not do is undo. The looted walker had already spread to the next
room, and which of the two happened first was decided by the table with nothing
saying so — visible as the **authored order of the rules** changing what is
concluded:

```
spread declared FIRST   live  at(w1, r1), at(walker(r3), r3)
spread declared LAST    live  at(w1, r1)
```

Same rules, same facts, no diagnostic. Which is the general rule this fixture
found from a fourth direction:

> **Precedence only bites when the loser's premise can be destroyed.**

With monotone rules the loop runs to quiescence and a merely-deferred rule
applies on some later tick, so the state is the same either way — measured on two
corridors, 21 ticks against 19 and both fully explored. *Ordering is not
defeasibility.* And spawning consumes nothing, so the per-position precedence the
moving design needed does not exist as a problem: **the missing mechanism was
missing because of the other design.**

### What this does not do

**Cycles are unbounded.** A maze with a loop grows `child(child(child(…)))`
without limit, and *do not go where you have been* is a negation over entries
again. The honest fix is the stratum-0 bridge that Chapter 26 uses to get a real
universal — and it is left undone deliberately, because this is about position
and that is about negation.

**Nothing is scheduled.** Walkers run under the ordinary loop, in whatever
order the table takes them — and since there is one chain and one state, there
is nothing for a scheduler to keep apart.

## Why this is the natural home for `blocked`

Chapter 13 introduced `blocked` — the agent's report that it has exhausted what
it can do alone — and noted that a corpus can key on it:

```
rule <ask-for-it> = implies( { +blocked(have(p1, ?k)) },
                             { +doing(tell(dm, want(p1, ?k))) } )
```

With one agent that's a little contrived. With several it is the whole point: a
player whose goal it cannot reach alone runs to quiescence, `<give-up>` writes
`blocked`, and **that** is the occasion where another mind is worth anything.

---

That's Part 5. The machine now handles stretches, indefinite patterns, other
people's words, numbers, clocks, and other minds.

The remaining parts are optional. They turn the machine around to look at
itself.

**Next:** the agent's own commitments, as ordinary facts.
[The agent's own state →](../watching/25-own-state.md)
