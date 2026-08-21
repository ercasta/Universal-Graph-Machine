# Moments

A **moment** is the machine's only construct for a state of affairs.

A state in time is a moment. A hypothetical is a moment. A supposition is a
moment. A rule's antecedent is a moment. There is no separate "frame", "world",
"context" or "scope" object anywhere in the design.

A moment has three parts and nothing else:

```
<M> = a signed delta     +  a predecessor
      (entries, §8)         (an edge to a moment)
```

- The **delta** is what changed — a list of entries.
- The **predecessor** says what it changed *from*.

Two parts, and the same construct does two jobs:

| the moment is | its predecessor is |
|---|---|
| a state in **time** | the previous state |
| a rule's antecedent | none, or another generic moment |

That is not thrift for its own sake: a rule is a fact relating two generic
moments (Chapter 6), so the thing a rule is *made of* is the thing history is
made of, and nothing is written twice.

!!! note "There used to be a third part, and two more jobs"
    A moment also carried a **licence** — what authorised the difference — and
    the four-row version of the table above included an *imagined* state and an
    *assumption*, because supposing forked the chain.

    Both are gone. The licence was assigned and then read nowhere, so it went;
    what authorised a claim is recorded on the **entry** instead, which is
    where `why` reads it from. Supposing went with the locus and the fork —
    nothing branches the chain now, and a `causes` application is the only
    thing that advances it.

## Anchored and generic

The distinction that carries weight isn't between *kinds* of moment. It's this:

- an **anchored** moment — actual individuals, and a predecessor in the real
  history;
- a **generic** moment — variables, and no anchored predecessor.

A rule's two halves are generic. Everything else is anchored.

A generic moment may have a *generic* predecessor, and that's what lets a
pattern say *and then* — a pattern is a chain, not a point. What a generic
moment may **not** do is point into the actual history, because a pattern naming
a particular past would be about that one occasion and could never be reused.

Because the distinction is structural, it's checkable rather than maintained by
etiquette. It is the one place in Part 1 where that's true, and it's true
because *generic* is one of the five floor items showing through (Chapter 30).

The machine's central operation is then one line:

> **To match a moment is to unify a generic chain against an anchored one.**

## Ancestry is derived, not stored

A moment has one predecessor, so *what came before what* is a walk rather than
a stored ordering — and a rule can ask it, with `anc` and `sanc` (Chapter 23).
There is no depth field to keep consistent and no ordering to drift.

!!! note "Deep dive: scope is not control"
    Ancestry answers *what came before here*. It says nothing about *which
    reasoning invoked which, and where an answer is owed* — that's a separate
    structure, the attention stack of Chapter 25, and the absence of one does
    not imply the absence of the other.

## A moment is already a belief state

Here's the part that surprises people.

A moment's delta is the entries deposited in it — everything the agent came to
think at that point, and nothing else. So the chain needs no second structure:

> **There is no belief-set object.** The chain already is one.

What would elsewhere be "the current belief set" is what the chain says now:
for each proposition, the last entry about it. And belief revision is an
ordinary deposit — a later claim, which supersedes the earlier one without
touching it.

Introducing a second membership structure for beliefs would create a second
ordering alongside succession, and two orderings that agree by convention drift
apart without anything noticing.

## Time and derivation share a core

Two orderings could easily have become unrelated things: succession in time, and
succession in a derivation. Here they are **one relation**, with the licence
recorded on each entry rather than on the moment. Succession is the shared
core; time adds a clock stamp above it (Chapter 23), derivation adds a
licensing rule above it.

One invariant has to survive that sharing:

> **Deriving takes no time.**

A derivation step is succession without duration. If the shared core carried a
clock, the two would have been collapsed rather than related, and every
hypothetical would falsely advance the world.

## What it costs

Let's score it honestly, the way this design scores everything, against the four
criteria it uses:

| | a mutable world state | a set of currently-believed facts | **moment = delta + predecessor** |
|---|---|---|---|
| not leaking | overwriting loses what it replaced, so *it changed* and *I was wrong* become one operation | says what is believed and nothing about when or why | every difference is deposited, licensed and ordered |
| not lossy | history is gone | the previous set is gone unless separately kept | nothing is overwritten |
| readable | a lookup | a lookup | a lookup — *later supersedes earlier* |
| composable | two writers contend for one cell | union of sets is not merge of beliefs | appending is the only write |

The readable row used to say **a read is a walk — the largest single cost in
the design**, and it was true: the read was measured at 86% of runtime. It is
now one index lookup, because the second time coordinate that made it a walk
was removed (Chapter 5). What the construct still buys is immutable history and
a licence on every claim.

Chapter 5 is that read, and the story of how it stopped being a walk.

---

**Next:** if a moment only stores what changed, what does *is this true?*
actually do?
[The read →](05-the-read.md)
