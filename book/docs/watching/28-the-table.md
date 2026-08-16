# The table

Chapter 27 said the machine needs something to hand it a set of rules to choose
from. This chapter is about what that something should be, and it is the biggest
open argument in the design.

## What the shipped loop does

Recall proposes. Everything proposed is matched. Defeat and quiescence filter.
Arbitration ranks what survives. One move is taken.

That materialises an **option set** on every tick, and the obvious objection is
that most of it must be waste. Measured, it isn't: **99.6% of those candidates
genuinely applied**.

So the option set is not waste. It is the *price of being able to say nothing
else applied* — which is exactly what `blocked` and `<give-up>` are built on
(Chapter 13).

The question is whether that price is worth paying on every tick.

## The other loop

> The system need not explain why it preferred a rule. That is not reasoning, it
> is System-1. You never proceed to match all possible rules: you work the
> current table from top to bottom and stop at the first rule that matches. Each
> applied rule then spends attention — a list of query → buff — which moves the
> scores of other rules. **The rules stay fixed; the postconditions are what a
> learning process calibrates.**

Four things the engine knows here, and **none of them is semantic**:

```
a score per rule    ordered, tie broken by declaration order
apply the first     highest-scoring rule whose antecedent matches
then spend          run that rule's postconditions to move the table
...and stop         if one of them said so, the run is over
```

That's the whole loop. No goal, no completeness, no widening. Those are *corpus
rules* whose postconditions reset buffs — **refocusing is a rule**, and **done is
the output of a rule** that checks against the goal. Nothing in the loop knows
what either is.

## Stopping, and what it is worth

The fourth row is the one that makes the third mean anything, and it was missing
for a while. *Done is the output of a rule* was the design from the start — and
the loop had no way to **obey** one. A completion check concluded, and the agent
carried straight on to quiescence anyway.

```
rule <done> = implies( { +want(?w), +?w }, { +finished(?w) } )
after <done> => stop
```

| | moves |
|---|---|
| no postcondition — the agent notices and carries on | **62** |
| `after <done> => stop` | **5** |

`stop` is spent the way `boost`, `damp` and `reset` are spent, so it's a row in
one vocabulary rather than a branch. And the loop still knows nothing about
goals: it knows a rule said stop, exactly as it knows one said reset.

!!! note "Deep dive: the feature next door, which is worth nothing"
    The obvious next thought is: *let a goal raise the priority of the rule that
    checks it.* It was built and measured, and it moves **nothing** — with the
    check at the floor, reranked, buffed persistently in two places, and
    standing. Identical every time, before `stop` existed and after.

    A completion check is **self-gating**. It cannot match until the thing is
    already done, so while the goal is unfinished it isn't losing to anything —
    it isn't a candidate at all. The instant it becomes matchable, widening
    reaches it in the same move.

    > **Score decides which of several *matching* rules wins. It never decides
    > whether a matching rule is reachable** — widening does that, and widening
    > doesn't stop at the top of the table.

    So a check that can only match at the finish line has nobody to go before.
    That null result is kept as a check, where the next person to propose the
    feature will find it.

!!! note "Deep dive: what stopping costs"
    The shipped loop refuses to stop **quietly** on something it was asked for —
    an open goal *outranks* a satisfaction signal (Chapter 26).

    The table loop cannot make that refusal, and the reason is exact: the veto is
    an **aggregate** — *nothing else is wanted and unmet* — and a rule cannot
    speak about the set of its own matches. Measured: give it two wants, make one
    reachable, and it stops with the other still wanted and still unmet.

    So the guarantee becomes a corpus's, which is the same trade the norms
    decision made — an engine guarantee becoming a corpus property **with an
    instrument watching it**. The measurement ships as a check rather than as a
    claim that this is fine.

## A postcondition is not an opcode

This is the line that has to be held, and this project has reason to be careful
about it: it deleted an instruction set once already.

A postcondition is a **query** — an ordinary antecedent, parsed by the ordinary
surface — and a **buff** naming a rule.

```
rule <flightless> = ...
after { +penguin(?x) } => boost(<flightless>, 20)
```

Rows, not branches. Adding a new kind of attention-spending is a new
postcondition, not a new engine case.

## Why it can be fast: the window is a prefix

Scores only fall as you go down the table. So once a match is found at score
`s`, everything below `s − tolerance` is irrelevant **without being matched at
all**.

That's the whole performance claim, and it's testable: score *first*, then match
only the top of the table.

The cap on how many rules sit in one window is a guard against a pathological
table where forty rules share a score — not the mechanism.

And what keeps it honest is a rule you've already met:

> **A dry shortlist is not a finished search.**

If nothing in the window applies, the shortlist **widens**. Without that, a miss
in the top N would deposit `quiet` while work remained, the agent would give up
on goals it could have reached, and the trail would show a completed search that
never ran.

With it, the worst case is exactly today's cost and the best case is N.

## Buffs fade, and that had to be learned the hard way

A buff that never expires is what made the first taught table run away: `A` lifts
`R`, `R` lifts `A`, every lift permanent, and the loop finds work for ever.

A lift is about **what is going on now** — *what I was doing is part of my
representation of the world* — so it fades. What survives is the
**postcondition**, which re-applies whenever its query holds again.

There's a second bound, and the reasoning behind where it's applied is worth
following:

**A boost shrinks as the rule is already lifted** — the useful half of a
sigmoid. Applied when the table is *read*, a monotone transform cannot change
any ordering, and ordering is all the table is for. Applied at the **update**, it
bounds the scale — and the scale has to be stable or `tolerance` stops meaning
anything.

Measured: the runaway table fired **0 doubts against 13** for the untaught one,
because nothing was ever *close* to anything again. A table with no ties has
stopped being able to notice it is unsure.

## Doubt is a move, not a pause

When two rules in the window score within the tolerance, that's a **doubt**. The
loop does not hold a tick waiting for it to resolve.

**Depositing the doubt is the move.** A settling rule gets the next turn, and
what it does is spend attention — so the settlement is a buff like every other,
calibratable rather than a branch:

```
rule <settle-doubt> = implies( { +close(?a, ?b) }, { +settled(?a, ?b) } )
frozen after <settle-doubt> => boost(?a, 1)
```

A corpus replaces it with something better — ask the user, apply a domain
criterion — by writing a rule that outscores it.

And the backstop needs no semantics: if nothing settles, restating the doubt
changes nothing, so quiescence lets the winner apply. A corpus without a settling
rule loses one tick rather than the loop.

!!! note "Deep dive: why `boost(?a, 1)` is writable at all"
    `?a` is *the winner as the doubt named it* — two rules nobody knew when the
    postcondition was authored.

    That works only because **rules are subjects** here: `close(<A>, <B>)` names
    them, and a conclusion about `?a` is a **mention** (Chapter 10), so
    quiescence does not drop it as having nothing to deposit.

    Three separate features of the design have to be true at once for one line of
    a default postcondition to be writable. That's usually the sign a design is
    coherent rather than merely large.

## The penguin, measured

Same corpus, same declaration order — *birds fly* written before *penguins are
flightless*:

| | doubts | applied | first answer |
|---|---|---|---|
| declaration order alone | 1 | `classify`, `settle-doubt`, `flies`, `flightless` | `can_fly(pingu)` |
| with one postcondition | 0 | `classify`, `flightless`, `flies` | `grounded(pingu)` |

No defeat relation, no `unless`, no precedence claim. Just a score and a stop.

And Chapter 26's point arriving from the other side: **a loop that runs to
quiescence applies both rules whatever the order.** What turns an order into a
default is *asking, taking the first rule that matches, and acting*.

## The two loops, side by side

Run against the shipped loop on four corpora — ticks, then conclusions:

| corpus | ticks (shipped / table) | conclusions | only shipped | only table |
|---|---|---|---|---|
| `delay.ugm` | 11 / 16 | 221 / 232 | `close` ×8 | `spent` ×7, `settled` ×7 |
| `worked.ugm` | 12 / 11 | 163 / 176 | — | `settled` ×4, `spent` ×4 |
| `quest-p1.ugm` | 18 / 21 | 186 / 206 | — | `settled` ×5, `spent` ×5, `close` ×5 |
| `dungeon` | 148 / 155 | 737 / 746 | `close` ×10, `defeated` ×1 | `spent` ×7, `settled` ×7 |

Read it as a **work list, not a failure**. Everything the table loop drops is a
record the shipped tick keeps *because* it materialises an option set:

- `close` is doubt over the **whole** option set rather than over a window;
- `defeated` is one rule beating another, which needs both to have been matched;
- `quiet` is the loop saying it stopped; `left` is a supposition being exited.

Each of those is a rule to write. And two of them the table loop **cannot**
recover, because they are claims about a set it deliberately never built.

## The decision

The author's, taken after all of the above ran:

> **The table loop is the kernel** — not an optimisation beside the shipped one.

With the losses accepted and named: `close` over the whole option set, and
`defeated`. The shipped loop stays on as **the slow definition a gate holds the
kernel to** — which is Chapter 32's rule about optimisations, applied to the
loop itself.

And the method is worth as much as the decision:

> **Subtract, do not rewrite.** Each definition that moves out of the host
> language gets a gate; when the gate is green, its Python goes.

The kernel *emerges* rather than being written, and the repository never stops
running. That's the alternative to a rewrite, and it's available here only
because every fast path already has a slow definition sitting beside it.

!!! note "Deep dive: the honest size of the thing"
    `machine.py` is **55% prose** — 5,507 lines, of which 1,979 are code. So the
    "1,000-line kernel" is roughly what is *left* after the logic moves out, not
    a target somebody has to hit by rewriting.

    Measuring that before starting is what turned a rewrite into a subtraction.

---

**Next:** the postconditions are what a learning process calibrates. So where
does the learning come from?
[Learning →](29-learning.md)
