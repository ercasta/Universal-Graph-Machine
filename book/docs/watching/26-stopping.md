# Stopping

```
mortal.ugm: 3 ticks, ended quiescent
```

**Quiescent** means: applying anything further would change nothing.

That's *exhaustion*, and it is not the same as being finished. This chapter is
about the difference, which turns out to be one of the more consequential
distinctions in the design.

## Two ways to be over

| | what it is | what it says |
|---|---|---|
| **quiescence** | nothing left to apply | I have run out of work |
| **`enough(x)`** | satisfaction | I have got what I came for |

An agent that only has the first will keep going until there's nothing left to
derive, whether or not it achieved anything. An agent that only has the second
can't tell you it's stuck.

And they interact in one direction only:

> **The loop may end. It may not end quietly on something it was asked for.**

An open goal is a **veto** that outranks satisfaction. If you asked for
something and the loop is stopping without it, that has to be reported, not
silently accepted.

## Why stopping is what makes preference mean anything

Here's the result that surprised the people who built it.

The machine runs to quiescence. So a preference between two rules — *try this
one first* — changes only the **order**, never the outcome: a low-scoring rule
is deferred, not removed, and if its situation still holds it will get its turn
eventually.

Which means **ordering alone is not defeasibility**. Both rules apply, whatever
the order.

> **What turns an order into a default is stopping.** Ask, take the first rule
> that matches, act.

So *completion is the output of a rule* isn't a detail of the design. It's what
makes a score mean anything at all.

Run the classic case — penguins, and whether they fly — with two rules declared
in the order *birds fly*, *penguins are flightless*:

| | pingu flies | grounded |
|---|---|---|
| declaration order alone | **True** | True |
| `dormant(<flies>)` | **False** | True |

The first row is the demonstration: run to quiescence, *both* rules apply, and
the order decided nothing. Only taking a rule out of the running changes the
answer — and that is not an ordering either, which is the point. What makes any
order meaningful at all is a stop. Chapter 28 measures the whole ladder, and
Chapter 17 shows why taking the rule out is the wrong tool for an exception.

And the same fact from the other direction:

> **Recall cannot save work in a machine that runs to quiescence.** Narrowing
> what comes to mind changes the *order* in which conclusions are reached, and
> nothing else, until something stops.

Which is why Chapter 27 comes after this one, and why the order **stopping →
recall → learning** is the order the pieces had to be built in.

## Quiescence is itself made of rules

The check *would this application change anything?* is six rules.

And it was the last thing standing between this design and a fully rule-level
kernel, because it looked like it needed something the language couldn't say: a
claim about a **set** — *no conclusion of this application would change
anything*.

It turned out not to. The universal ranges over **structure**, where a `−`
member can only mean *not derived* — and that's the universal wanted, for free.
A claim about a set of *entries* would have been the hard case, because there a
`−` member can only say *an entry denies this*.

Measured on the gate that holds the compiled verdict to those six rules: **145
candidates compared, 0 disagreeing.**

!!! note "Deep dive: caching a verdict is not the exponent"
    Quiescence re-tested the same verdict **99.8%** of the time, and caching it
    bought a factor of two — and left the quadratic completely unchanged.

    > **Caching a verdict removes the cost per candidate, not the candidate.**

    1,000 applications across 1,002 ticks is still 1,000 × 1,002. The walk being
    re-done was the *smallest* of the three costs, not the largest, and the
    measurement said so only after the optimisation had been written.

    A related finding from the same week, and it's the more useful one: the
    benchmark that had defined "the wall is scale" was the **worst case** — 99.6%
    of candidates genuinely applied on that fixture, against **10.6%** across the
    real suite.

    > **A benchmark that cannot fail is worse than none, because it reads as
    > evidence.**

## Quiescence is a place the machinery can decline silently

Chapter 13 listed the silences. This is the one worth repeating here, because
it's the reason quiescence needed its own gate.

The design said the machinery has exactly two places it can be asked why it
returned part of a structure: **match**, and **write**. Both are observable —
match returning nothing, and a write refusing.

That was one short.

> **Quiescence is a third place the machinery can decline, and it declines
> silently.**

*This application would change nothing* is indistinguishable from *there was
nothing to apply*. A whole capability — rules reasoning about rules — was
dropped there for a long time, with no error, no trace, and nothing to
distinguish it from correct behaviour.

## Doubt, and settling it

When two candidate moves score within a tolerance of each other, that's a
**doubt** — and the interesting design question is what to do about it.

The answer here is: nothing special. Depositing the doubt **is** the move. A
settling rule gets the next turn — an ordinary rule, replaceable rather than a
branch. A corpus replaces it by writing a rule that outscores it: ask the
user, apply a domain criterion, whatever fits.

And the backstop needs no semantics at all: if nothing settles, restating the
doubt changes nothing, so quiescence lets the winner apply. A corpus without a
settling rule loses one tick rather than the loop.

The price is visible in ticks — a doubt costs a move and settling costs another
— and it is worth it, because *the agent was unsure here* becomes a fact with a
trail rather than a coin flip nobody recorded.

---

**Next:** which rules even get considered.
[What comes to mind →](27-recall.md)
