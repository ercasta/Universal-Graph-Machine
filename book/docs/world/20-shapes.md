# Shapes

Some things are known by their **shape** rather than by their extent.

*Anna and Bo are taking turns* can be said having watched a sequence, and it can
be said having watched nothing — *imagine they are taking turns* — and it is the
same claim either way.

The second reading is the demanding one. There's no sequence to point at, and
materialising one would state a number of turns nobody claimed.

## Two kinds of indefiniteness

They look alike and they are not one construct:

| | *taking turns* | *some files* |
|---|---|---|
| indefinite in | **extent along the chain** | **multiplicity within a moment** |
| composes by | succession — ordered, elements are moments | membership — unordered, elements are individuals |
| leaks if materialised | invents a number of turns | invents a number of files |

They share one principle, which spans already applied and which this generalises:

> **Describe the extent. Never enumerate it.**

## A shape is a definition, not a term

Given Chapter 6's antecedent, a shape needs no new construct. It's a **recursive
definition over spans**, written as ordinary rules in ordinary vocabulary.

*Taking turns* needs at least two turns, so that's the base case; the step case
consumes one turn and defers the rest:

```
<TT-base>   two consecutive acts by different actors, over the span between them
<TT-step>   one act, followed by a span over which the others took turns
```

Written out and run over a five-moment alternation, those recognise *taking
turns* over **every stretch it holds over** — ten of them, from M0..M2 out to
M0..M5, with the argument order correct in each.

## Why a shape is three rules, not two

Here's the part that's genuinely interesting, and it was predicted by the design
before it was built.

An alternation **repeats its actors by definition**. So `acts(anna)` at M1 is
superseded by `acts(anna)` at M3 — and a matcher sees the **resolved** state,
one entry per proposition. The earlier turn is not in the state.

The step case needs precisely that earlier turn.

So the two recognisers have to match over the **raw chain** rather than the
resolved state. And that turns out to be allowed, for a reason that connects
straight back to Chapter 31:

> **A rule whose antecedent is entirely structural concludes structure rather
> than a claim.**

The recognisers mention only `anc`, `in_delta`, `entry_of`, `span_of` — no
entries. So what they conclude is *structure*: a `turns(?s, ?a, ?b)` that is
undated, unattributed, and deniable by nothing. Exactly what a walk's
intermediate result has to be, or the bootstrap circle returns.

Then **one ordinary rule says it**:

```
rule <say> = implies( { turns(?s, ?a, ?b), +watching(x) },
                      { +taking_turns(?a, ?b) at ?s } )
```

Two rules to see it, one to say it. The chain-reading rules are allowed to read
the raw chain precisely **because they cannot assert anything about what they
find**.

!!! note "Deep dive: the interning trap has four faces"
    Recursion over spans hangs without interning — the same stretch gets a fresh
    node every time and nothing ever reaches a fixed point.

    But interning is also this project's single most expensive recurring bug,
    and it fails in four distinct ways, which is why it's worth naming them:

    - **never fires** — the node already existed, so nothing looked new;
    - **always fires** — a fresh node every time, so no fixed point;
    - **records nothing** — the conclusion was interned before novelty was
      counted, so the facts were right, the fixpoint never came, and the answer
      was *wrong rather than crashed*;
    - **not pure** — asking the question changed some other answer.

    A span node survives the test because **nothing reads its existence**:
    `span` is in no structural relation, so no rule enumerates spans and no walk
    visits them. Asking twice gives the same answer, and asking changes no other
    answer.

## Bounds are facts about the shape

*At least three*, *no more than seven*, *exactly two* — these are ordinary facts
about the shape node, not extra members and not a new construct.

Two different bounds must not share a slot, and the distinction matters:

- how many **elements** the shape has;
- how far the **search** is willing to go looking.

The second is the searcher's budget, not a property of the world. Which is
Chapter 13's rule again:

> **Bounded expansion returns a result and a state, never a result.**

## Plurality is a group

*Some files* takes the other move, and it's the same principle applied to
multiplicity rather than extent: **mint one node for the group**, and its size is
a fact about that node.

```
+files(<g>)          there is a group
+size(<g>, 3)        ...and it has three members, if you happen to know
```

Membership is not stored, for the same reason a span's contents aren't. What you
know about the group is said about the group.

The same move works for a **scalar you don't know**:

```
rule <pour> = causes( { +level(?g, ?v), +poured(?g) },
                      { ? level(?g, ?v), +greater(after(?g), ?v), +rises(level(?g)) } )
```

Don't name the value; name the **quantity**, and say what's known of it. And it
is genuinely reasoned with, not merely recorded — a downstream rule reads it:

```
rule <spill> = implies( { +greater(after(?g), ?v), +brim(?g, ?v) }, { +overflows(?g) } )
```

The real limit, stated honestly: once the level reads `?`, a second change has
nothing to compare against, so the quantity has to be **chained** —
`after1`, `after2`, `above(after2, after1)` — each step its own node. That works,
and it's *ordinal* tracking: the agent can come to know the level is above the
brim and can never again know that it's 5.

Where the number is actually known, use arithmetic instead. Chapter 22.

---

**Next:** everything so far has been the machine's own knowledge. What about
somebody telling it something?
[Who said it →](21-channels.md)
