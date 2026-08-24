# Stopping

```
mortal.ugm: 2 ticks, ended quiescent
```

**Quiescent** means: nothing left matches.

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

## Quiescence used to be made of rules, and no longer is

Earlier in this project, quiescence asked a semantic question: *would applying
this candidate change anything?* Answering it was six rules, and getting there
was the last thing standing between that design and a fully rule-level kernel,
because it looked like it needed something the language couldn't say — a claim
about a **set**, *no conclusion of this application would change anything*.
Measured on the gate that held the compiled verdict to those six rules: **145
candidates compared, 0 disagreeing.** And caching the verdict re-tested the same
answer 99.8% of the time, worth a factor of two on a quadratic that stayed a
quadratic — a result kept here as a reminder that *removes the cost per
candidate* and *removes the candidate* are different claims, easy to conflate
in the moment a number improves.

The table loop (Chapter 28) does not ask that question at all. There is no
per-candidate filter any more: a rule that matches and writes nothing new is
offered again, on the next tick, at the same score, because *this rule has
nothing further to give* became the corpus's judgement rather than the
engine's — the same move that turned `boost`/`damp`/`reset` into `attend`
(Chapter 28) turned *would this change anything* into a question a rule
answers about itself, with a guard: `no mortal($x)` on `<mortal>` above is what
stops it, not a compiled verdict watching from outside.

That is cheaper — nothing is compared against a cache, because nothing is
cached — and it moves a real cost onto the author: an unguarded rule that keeps
matching does not merely re-derive nothing, it **occupies every tick**, because
declaration order breaks every tie the same way. Chapter 28's penguin table
shows exactly this: `<flies>` without `no flies($x)` never gives `<flightless>`
a turn, for four hundred ticks, and the run never reaches quiescence at all.
*An occasion is consumed. A fact is not* (`docs/authoring.md` §0) is no longer
a style note — it's what keeps the loop moving.

## Quiescence is still a place the machinery can decline silently

Chapter 13 listed the silences. This is the one worth repeating here.

The design said the machinery has exactly two places it can be asked why it
returned part of a structure: **match**, and **write**. Both are observable —
match returning nothing, and a write refusing.

That was one short.

> **Quiescence is a third place the machinery can decline, and it declines
> silently.**

*Nothing matches* is a state a run reports (`ended quiescent`), but *this rule
keeps matching and keeps writing nothing* looks, from outside, exactly like
useful work — the loop has no way to say which one happened, because it no
longer asks. That's the price of dropping the six-rule check: a capability
(the machinery telling a rule apart from a rule that has gone stale) traded for
a cheaper loop and a guard the corpus now has to remember to write.

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
