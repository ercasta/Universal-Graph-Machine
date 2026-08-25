# Shapes

Some things are known by their **shape** rather than by their extent.

*Anna and Bo are taking turns* can be said having watched a sequence, and it
can be said having watched nothing — *imagine they are taking turns* — and
it is the same claim either way.

The second reading is the demanding one. There's no sequence to point at, and
materialising one would state a number of turns nobody claimed.

## Two kinds of indefiniteness

They look alike and they are not one construct:

| | *taking turns* | *some files* |
|---|---|---|
| indefinite in | **extent along a stretch** | **multiplicity within one moment** |
| composes by | succession — ordered, elements are events | membership — unordered, elements are individuals |
| leaks if materialised | invents a number of turns | invents a number of files |

They share one principle, which Chapter 19's stretches already applied and
which this generalises:

> **Describe the extent. Never enumerate it.**

## A shape is a definition, not a term

Given Chapter 6's antecedent, a shape needs no new construct. It's a
**recursive definition over stretches**, written as ordinary rules in
ordinary vocabulary. Chapter 19 described what a stretch is: two node names,
carried as arguments of a proposition the corpus asserts — nothing minted,
nothing derived.

*Taking turns* needs at least two turns, so that's the base case; the step
case consumes one turn and defers the rest:

```
<TT-base>   two consecutive turns by different actors — a stretch of one step
<TT-step>   one turn, followed by a stretch over which the others took turns
```

## Succession is the corpus's to assert

Nothing derives an ordering between two moments. The recursion has to be
handed its own succession as ordinary facts — nobody infers *turn 2 comes
right after turn 1* on the corpus's behalf:

```
rule <TT-base>
  +turn($n, $a)
  +next($n, $m)
  +turn($m, $b)
  +different($a, $b)
  no turns($n, $m, $a, $b)
->
  +turns($n, $m, $a, $b)

rule <TT-step>
  +turn($n, $a)
  +next($n, $m)
  +turns($m, $k, $b, $c)
  +different($a, $b)
  no turns($n, $k, $a, $b)
->
  +turns($n, $k, $a, $b)

fact +turn(1, anna)  fact +turn(2, bo)    fact +turn(3, anna)
fact +turn(4, bo)    fact +turn(5, anna)
fact +next(1, 2)  fact +next(2, 3)  fact +next(3, 4)  fact +next(4, 5)
fact +different(anna, bo)  fact +different(bo, anna)
```

```
$ python -m ugm turns.ugm
turns.ugm: 12 ticks, ended quiescent

what it believes, newest first:
  turns(1, 5, anna, bo)
  turns(2, 5, bo, anna)
  turns(3, 5, anna, bo)
  turns(1, 4, anna, bo)
  turns(2, 4, bo, anna)
  turns(1, 3, anna, bo)
  turns(1, 2, anna, bo)
  turns(2, 3, bo, anna)
  turns(3, 4, anna, bo)
  turns(4, 5, bo, anna)
  ...
```

Ten stretches, every one of them from a five-turn alternation, with the
argument order correct in each — the recursion working over facts the corpus
states outright, each turn its own distinct proposition (see below).

## Every distinct claim survives

`turn(1, anna)` and `turn(3, anna)` are **different propositions** —
different arguments, different nodes — so neither supersedes the other. Both
are simply believed, simultaneously, for as long as nobody erases either.
That is what lets `<TT-step>` see the earlier turn it needs even after later
turns by the same actor are also believed.

What *is* necessary: the `no turns($n, $m, $a, $b)` guard on both rules.
Without it each rule keeps matching the same already-true conclusion, and
the run never reaches quiescence — it burns through the tick limit finding
nothing new:

> **An application that changes nothing is offered again.** A shape's own
> recursion has to stop itself; nothing else will.

!!! note "Deep dive: what the `no` guard is actually asking"
    Building `turns($n, $m, $a, $b)` twice gives two nodes. They are the same
    **shape**, and that is what `no` asks about: *does anything believed say
    this*, not *is this particular node believed*. So the guard still works —
    it just is not resting on the substrate handing back one fixed node.

    It used to. Relation instances were interned, and asking *is this already
    concluded* meant asking about one node. That was the project's single most
    expensive recurring bug, failing in four ways worth naming:

    - **never fires** — the node already existed, so nothing looked new;
    - **always fires** — a fresh node every time, so no fixed point;
    - **records nothing** — the conclusion was interned before novelty was
      counted, so the facts were right and the fixpoint never came;
    - **not pure** — asking the question changed some other answer.

    Three of the four came from *building* a node in order to ask about one.
    Nothing builds to ask any more: a question about a shape is looked up, and
    what a rule matched is carried forward rather than reconstructed.

## Bounds are facts about the shape

*At least three*, *no more than seven*, *exactly two* — these are ordinary
facts about the shape node, not extra members and not a new construct.

Two different bounds must not share a slot, and the distinction matters:

- how many **elements** the shape has;
- how far the **search** is willing to go looking.

The second is the searcher's budget, not a property of the world. Which is
Chapter 13's rule again:

> **Bounded expansion returns a result and a state, never a result.**

## Plurality is a group

*Some files* takes the other move, and it's the same principle applied to
multiplicity rather than extent: **mint one node for the group**, and its
size is a fact about that node.

```
fact +files(g1)          there is a group
fact +size(g1, 3)        ...and it has three members, if you happen to know
```

Membership is not stored, for the same reason a stretch's contents aren't.
What you know about the group is said about the group.

The same move works for a **scalar you don't know**. There is no grade to
say *unknown* with — a proposition is asserted or it isn't, nothing in
between. So don't name the value; name the **relationship**, and say what's
known of it:

```
rule <pour> = implies( { +poured($g), no rises($g) },
                       { +rises($g) } )
rule <spill> = implies( { +rises($g), +brim($g, low), no overflows($g) },
                        { +overflows($g) } )

fact +poured(g1)
fact +brim(g1, low)
```

```
$ python -m ugm pour.ugm --ask "overflows(g1)"
pour.ugm: 3 ticks, ended quiescent
overflows(g1): believed
```

`rises($g)` never names a level; it names a direction, reasoned with exactly
like any other belief. The real limit, stated honestly: once you stop naming
values, a second change has nothing to compare against, so a genuinely
tracked quantity has to be **chained** — `level1`, `level2`,
`above(level2, level1)`, each step its own node. That works, and it's
*ordinal* tracking: the agent can come to know the level is above the brim
and can never again know that it was, say, 5.

Where the number is actually known, use a computator instead. Chapter 22.

---

**Next:** everything so far has been the machine's own knowledge. What about
somebody telling it something?
[Who said it →](21-channels.md)
