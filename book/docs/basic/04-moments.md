# Moments

A **moment** is the machine's only construct for a state of affairs.

A state in time is a moment. A hypothetical is a moment. A supposition is a
moment. A rule's antecedent is a moment. There is no separate "frame", "world",
"context" or "scope" object anywhere in the design.

A moment has three parts and nothing else:

```
<M> = a signed delta     +  a predecessor        +  a licence
      (entries, §8)         (an edge to a moment)   (an edge to a node)
```

- The **delta** is what changed — a list of entries.
- The **predecessor** says what it changed *from*.
- The **licence** says what authorised the difference.

Only the licence varies with what kind of moment it is:

| the moment is | its predecessor is | its licence says |
|---|---|---|
| a state in **time** | the previous state | *an event happened* |
| an **imagined** state | the imagined state before it | *I applied this rule in supposition* |
| an **assumption** | where I was standing when I made it | *I decided to suppose this* |
| a rule's antecedent | none, or another generic moment | — |

One construct, four jobs. That is not thrift for its own sake: it means every
question you can ask about history you can also ask about a hypothetical,
without anything being written twice.

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

## Nesting needs no mechanism

A supposition inside a supposition is just a path in the predecessor tree. There
is no depth limit and nothing to push onto a stack, because *scope nesting is
ancestry*, and ancestry is derived rather than stored.

This is a good example of what a well-chosen construct buys. "Nested contexts"
is usually a feature with a data structure behind it. Here it's a consequence of
moments having predecessors.

!!! note "Deep dive: scope is not control"
    Ancestry answers *what can I see from here*. It says nothing about *which
    reasoning invoked which, and where an answer is owed* — that's a separate
    structure (Chapter 25), and the absence of a scope stack doesn't imply the
    absence of the other one.

## A moment is already a belief state

Here's the part that surprises people.

A moment's delta is entries, and an entry names the moment it is *about*. Those
need not be the same moment. So a single moment carries two things at once:

| | |
|---|---|
| **the world at a point** | the entries in the delta whose locus is the moment itself |
| **what the agent believes here, about any time** | the delta entire |

Which means:

> **There is no belief-set object.** A moment already is one.

What would elsewhere be "the current belief set" is the chain read at the moment
you're standing in. And belief revision is ordinary succession — the same
relation, with a licence saying *I came to think otherwise*.

Introducing a second membership structure for beliefs would create a second
ordering alongside succession, and two orderings that agree by convention drift
apart without anything noticing.

## Time and derivation share a core

Two orderings could easily have become unrelated things: succession in time, and
succession in a derivation. Here they are **one relation with two licences**.
Succession is the shared core; time adds a clock stamp above it, derivation adds
a licensing rule above it.

One invariant has to survive that sharing:

> **Supposing takes no time.**

A derivation step is succession without duration. If the shared core carried a
clock, the two would have been collapsed rather than related, and every
hypothetical would falsely advance the world.

## What it costs

Let's score it honestly, the way this design scores everything, against the four
criteria it uses:

| | a mutable world state | a set of currently-believed facts | **moment = delta + predecessor + licence** |
|---|---|---|---|
| not leaking | overwriting loses what it replaced, so *it changed* and *I was wrong* become one operation | says what is believed and nothing about when or why | every difference is licensed and dated |
| not lossy | history is gone | the previous set is gone unless separately kept | nothing is overwritten |
| readable | a lookup | a lookup | **a read is a walk** — the largest single cost in the design |
| composable | two writers contend for one cell | union of sets is not merge of beliefs | forks are free; two successors need no coordination |

That "a read is a walk" is the price of the whole thing, and it is paid on every
single read. What it buys: supposition at no extra cost, immutable history, and
a date on every claim.

Chapter 5 is that walk.

---

**Next:** if a moment only stores what changed, then *is this true here?* isn't
a lookup. Here's what it is instead.
[Reading is a walk →](05-the-read.md)
