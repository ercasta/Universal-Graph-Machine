# The table

Chapter 27 ended at the table: everything live gets a score, and the loop works
the table from the top. This chapter is what that loop is — and it is the loop
this design ships. It arrived as a challenger to a very different one, won on
measurement, and the story of the match is kept at the end of the chapter,
because the case for the winner *is* the comparison.

## The loop

> The system need not explain why it preferred a rule. That is not reasoning, it
> is System-1. You never proceed to match all possible rules: you work the
> current table from top to bottom and stop at the first rule that matches.
> Each applied rule then spends attention. **The rules stay fixed; the
> postconditions are what a learning process calibrates.**

Four things the engine knows here, and **none of them is semantic**:

```
a score per rule    ordered, tie broken by declaration order
apply the first     highest-scoring rule whose antecedent matches
then spend          run that rule's postconditions
...and stop         if one of them said so, the run is over
```

That's the whole loop. No goal, no completeness, no widening. Those are *corpus
rules* whose postconditions spend attention — **refocusing is a rule**
(`unattend`), **done is the output of a rule** that checks against the goal
(`stop`), and **suspend this line of work for another** is two more (`push`,
`pop` — Chapter 25's stack). Nothing in the loop knows what any of them is for.

A score is one of two numbers: rules the bundle marks `standing` sit at the
apparatus's height, and everything else sits at the floor. There is no third
place to be — and how that came to be the whole of it is the buff story, below.

## Stopping, and what it is worth

The fourth row is the one that makes the third mean anything, and it was
missing for a while. *Done is the output of a rule* was the design from the
start — and the loop had no way to **obey** one. A completion check concluded,
and the agent carried straight on to quiescence anyway.

```
rule <done> = implies( { +want(?w), +?w }, { +finished(?w) } )
after <done> => stop
```

| | moves |
|---|---|
| no postcondition — the agent notices and carries on | **64** |
| `after <done> => stop` | **9** |

`stop` is spent the way `attend` and `unattend` are spent, so it's a row in one
vocabulary rather than a branch. And the loop still knows nothing about goals:
it knows a rule said stop, exactly as it knows one said attend.

!!! note "Deep dive: the feature next door, which is worth nothing"
    The obvious next thought is: *let a goal raise the priority of the rule that
    checks it.* It was built and measured, and it moves **nothing**.

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
    The loop this one replaced refused to stop **quietly** on something it was
    asked for — an open goal *outranked* a satisfaction signal (Chapter 26).

    This loop cannot make that refusal, and the reason is exact: the veto is an
    **aggregate** — *nothing else is wanted and unmet* — and a rule cannot
    speak about the set of its own matches. Measured: give it two wants, make
    one reachable, and it stops with the other still wanted and still unmet —
    three moves, and an unmet want left behind.

    So the guarantee becomes a corpus's, which is the same trade the norms
    decision made — an engine guarantee becoming a corpus property **with an
    instrument watching it**. The measurement ships as a check rather than as a
    claim that this is fine.

## A postcondition is not an opcode

This is the line that has to be held, and this project has reason to be careful
about it: it deleted an instruction set once already.

A postcondition is a **query** — an ordinary antecedent, parsed by the ordinary
surface — and something to spend. There are exactly five, and every one of them
is a *deposit or a signal*, never a score:

```
attend(?x, n)   think about what this move just bound, and how much
unattend        stop thinking about whatever it was
stop            end the run
push(...)       suspend this line of work and open a frame
pop             return, carrying one node back
```

```
rule <spot> = implies( { +enemy(?x), +wounded(?x) }, { +opening(?x) } )
after <spot> => attend(?x, 3)
```

Rows, not branches. Adding a new kind of attention-spending is a new
postcondition, not a new engine case. And note what `attend` names: a **node**
the move itself bound — a thing in the world — never a rule.

## There used to be three more, and they moved a score

`boost(<R>, n)`, `damp(<R>, n)` and `reset` were postconditions too, and they
are retired — not because they didn't work, but because of what they *named*:

> **A rule id goes stale the moment a rule is adopted, composed or renamed. A
> corpus of experience written against rule names stops loading — rather than
> going quietly wrong.**

A lesson has to survive the agent changing its own rules, and a lesson about a
*thing* (`attend(?x)`) does, where a lesson about a *rule* (`boost(<R>)`)
cannot. Everything that existed to keep buffs healthy went with them: the decay
that stopped a self-lifting pair running away, the saturation that kept the
scale stable, the trace that rebuilt the table, the reranker. What is left
cannot decay, so there is nothing to tune.

The replacement is leaner than what it replaced. An `attention(x)` claim is
**recomputed at every move and kept nowhere** — *what is in front of me is
recomputed; what I was doing persists and fades* — so there is no lifetime knob
and no runaway to guard against. When the claim is denied, it is over.

And one thing became an error rather than a silence: a ranking-time `when`
trigger used to nudge scores inside a shortlist, and now the surface **refuses
it** with a message. Such a trigger ran on rules that had not applied and might
never apply — a deposit from there would be the agent claiming to think about
something because it considered thinking about it.

## Attention reaches both halves

`attention(x)` is an ordinary claim about a node, and it does two jobs at two
different prices:

| | what it decides | how exact | what it costs |
|---|---|---|---|
| the lift | which rules are matched at all | approximate | two dict reads |
| the pick | which of a rule's applications is taken | **exact** | nothing |

The lift is a **join**: the relations `goblin1` is currently spoken of under,
against the rules whose antecedents use one. It is approximate on purpose — a
rule reading `wounded(?x)` is lifted because *something* attended is wounded,
whether or not it would bind `?x` to it — and that is the right amount of
wrong, because the lift only decides who is *matched*. Exactness arrives one
layer up, for free: among a rule's found applications, the one about the
attended thing is taken, stably, so attention overrides the tie-break where it
has an opinion and defers to it everywhere else.

Measured, on a twelve-rule table of which three can match: a rule twelfth in
the table applies **first** when the thing it is about is attended, and the run
costs 195 matches against 238, because the window stopped widening past it.
Attending to *everything* discriminates nothing — it moves no rule ahead of any
other, and the first move is the untaught one.

## Why it can be fast: the window is a prefix

Scores only fall as you go down the table. So once a match is found at score
`s`, everything below `s − tolerance` is irrelevant **without being matched at
all**.

That's the whole performance claim, and it's testable: score *first*, then
match only the top of the table.

The cap on how many rules sit in one window is a guard against a pathological
table where forty rules share a score — not the mechanism.

And what keeps it honest is a rule you've already met:

> **A dry shortlist is not a finished search.**

If nothing in the window applies, the shortlist **widens**. Without that, a
miss in the top N would deposit `quiet` while work remained, the agent would
give up on goals it could have reached, and the trail would show a completed
search that never ran.

With it, the worst case is exactly the old cost and the best case is N.

## Four levers, and what each can actually do

There are four ways to make one rule win, they are not variants of each other,
and the difference that matters is the last column:

| lever | what it is | can it bring a rule *into consideration*? |
|---|---|---|
| declaration order | the tie-break at equal score | no — it orders equals |
| `standing(<R>)` | permanent height, marked by the bundle or the corpus | **yes** — it raises the floor |
| `dormant(<R>)` | not ranking at all; it takes a rule **out** | it removes a rule instead |
| `intercepts(<T>, after)` | not ranking either; it changes what a rule wrote | it does not choose, it rewrites |
| `attention(x)` / `after <R> => attend(?x)` | a lift keyed on a **thing** | **yes** — sized to clear the apparatus |

The last row is the learnable one, and it is the whole learnable path working
end to end: a move binds a node, a postcondition attends it, the lift decides
which rules are matched next and which application is taken, and the claim is
on the record for a rule to read, deny or reason about.

## Doubt is a move, not a pause

When two rules in the window score within the tolerance, that's a **doubt**.
The loop does not hold a tick waiting for it to resolve.

**Depositing the doubt is the move.** `close(<A>, <B>)` lands as a claim, and a
settling rule gets the next turn:

```
rule <settle-doubt> = implies( { +close(?a, ?b) }, { +settled(?a, ?b) } )
```

A corpus replaces it with something better — ask the user, apply a domain
criterion — by writing a rule that outscores it.

And the backstop needs no semantics: the doubt already stands on the next tick,
so restating it changes nothing, and quiescence lets the winner apply. A corpus
without a settling rule loses one tick rather than the loop.

!!! note "Deep dive: why concluding about `?a` is writable at all"
    `?a` is *the winner as the doubt named it* — two rules nobody knew when the
    settling rule was authored.

    That works only because **rules are subjects** here: `close(<A>, <B>)`
    names them, and a conclusion about `?a` is a **mention** (Chapter 10), so
    quiescence does not drop it as having nothing to deposit.

    Three separate features of the design have to be true at once for one
    default rule to be writable. That's usually the sign a design is coherent
    rather than merely large.

## The penguin, measured

Same corpus, same declaration order — *birds fly* written before *penguins are
flightless* — and the question is what actually makes the exception win:

| | pingu flies | grounded | tweety flies |
|---|---|---|---|
| declaration order alone | **True** | True | True |
| `standing(<flightless>)` | **True** | True | True |
| `dormant(<flies>)` | **False** | True | False |
| ...and the KB states `-penguin(tweety)` | False | True | **True** |

The first two rows are Chapter 26's point arriving in a table: **a loop that
runs to quiescence applies both rules whatever the order** — ordering is not
defeasibility, and neither is height. Only the third row stops Pingu flying, and
look at what it costs: taking `<flies>` out of the running grounds Tweety too,
because removal is per rule and an ordinary bird is not an exception to
anything. The fourth row is the one that works, and it is not a lever at all —
it is a fact. Say `-penguin(tweety)` and let `<flies>` read it: the general rule
keeps working for ordinary birds and declines for this one.

Tweety is the control here, and the whole reason the table is worth printing.
Without an ordinary bird in the fixture, rows three and four look identical and
the lever that breaks flight passes.

## The match that settled it

This loop arrived as a proposal beside a very different incumbent: recall
proposes, **everything** proposed is matched, defeat and quiescence filter,
arbitration ranks, one move is taken. That loop materialised an *option set* on
every tick — and the obvious objection, that most of it must be waste, was
measured and found wrong: **99.6% of those candidates genuinely applied**. The
option set was the price of being able to say *nothing else applied*, which is
what `blocked` and `<give-up>` are built on (Chapter 13).

So the two ran side by side, on the same corpora, with an instrument reporting
every conclusion either reached that the other did not — ticks first,
conclusions second:

| corpus | ticks (old / table) | conclusions | only the old loop | only the table |
|---|---|---|---|---|
| `delay.ugm` | 11 / 16 | 221 / 232 | `close` ×8 | `spent` ×7, `settled` ×7 |
| `worked.ugm` | 12 / 11 | 163 / 176 | — | `settled` ×4, `spent` ×4 |
| `quest-p1.ugm` | 18 / 21 | 186 / 206 | — | `settled` ×5, `spent` ×5, `close` ×5 |
| `dungeon` | 148 / 155 | 737 / 746 | `close` ×10, `defeated` ×1 | `spent` ×7, `settled` ×7 |

Read the third column as a **work list**: everything the table loop dropped was
a record the old tick kept *because* it materialised an option set. Most were
recovered as rules; the defeat record was recovered at the time, and has since
gone for good along with precedence itself (Chapter 17); and one is genuinely
gone — `close` over
the **whole** option set rather than over a window, a claim about a set the
table deliberately never builds. That loss is named, measured, and accepted.

The decision, taken after all of the above ran:

> **The table loop is the kernel** — not an optimisation beside the old one.

And the method is worth as much as the decision:

> **Subtract, do not rewrite.** Each definition that moves out of the host
> language gets a gate; when the gate is green, its Python goes.

For a while the old loop stayed on as the slow definition a gate held the
kernel to — Chapter 32's rule about optimisations, applied to the loop itself.
Then the comparison settled, and the old loop and the gate that compared them
were deleted together. What remains of them is this section, the checks that
keep the named losses honest, and `python -m ugm.core.attention` — which now
runs the worked examples above rather than a comparison, because there is no
second loop left to compare against.

---

**Next:** the postconditions are what a learning process calibrates. So where
does the learning come from?
[Learning →](29-learning.md)
