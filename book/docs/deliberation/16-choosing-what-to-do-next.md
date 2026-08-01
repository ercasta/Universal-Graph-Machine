# Choosing what to do next

Everything up to here has been the machine deciding for itself. It ranks moves
by relevance, it replans when reality disagrees, it reaches for a contingency
when one fits. Nowhere in any of that did *you* get a say.

Part 4 is about giving you one. And it starts with a defect that took three
tries to notice, because each time it wore different clothes.

## The thing it could do but never think about

Chapter 7's search is a loop: pick the best-ranked move, imagine it, repeat
until the goal is satisfied or the budget runs out. Simple, and it works.

But look at where the decisions are. *Which move next?* is a comparison inside
the loop. *Should I stop and act?* isn't asked at all. *Is this the sanctioned
way to do this?* has nowhere to be asked from. The loop runs start to finish
with no gap in it, so nothing can get between two imagined steps.

Which means deliberation was the one thing the machine **computed with and
could not compute about**.

That sentence should sound familiar, because this book has told the same story
twice already:

| what was stuck in code | so you couldn't | fixed by |
|---|---|---|
| attention — a plain object holding nothing | look at what it was attending to | the thread (Chapter 13) |
| the goal — a plain string | point at what it wanted | goal constraints (Chapter 5) |
| the decision — a `while` loop | say anything about how it should choose | this chapter |

Each time the fix was the same shape: **take the thing that was hiding in the
machinery and make it data.** And each time it looked, beforehand, like an
implementation detail rather than a missing capability.

## A gap in the loop, and five words to put in it

The change itself is small. The search now consults a decision once per
imagined step, *before* it imagines anything, and the decision may answer with
one of five words.

| word | means |
|---|---|
| **expand** | imagine the best-ranked move — the whole of the old behaviour |
| **decompose** | don't enumerate moves; raise subgoals instead (Chapter 18) |
| **commit** | stop planning; what we have is what we'll do |
| **sense** | stop planning and act **in order to find out** (Chapter 19) |
| **refuse** | there's no sanctioned way to proceed; don't improvise |

A closed set of five, on purpose. This is the vocabulary that everything you
ever author has to speak, and a vocabulary you can't enumerate is one nobody
can check.

Two of them look like duplicates and aren't:

**`sense` versus `commit`.** Both stop planning and act. What differs is *why*,
and the why is what a reader needs later. "I stopped because I had a good
enough plan" and "I stopped because I need to go and look" are different
events, and a record that collapses them has thrown away the useful part.

**`refuse` versus "no plan found".** One is an absence — I searched and there
wasn't a route. The other is a prohibition — there may well be a route, and I
was not permitted to take it. Chapter 18 is entirely about why that distinction
earns its own word.

## What it looks like when something speaks up

Nothing has to. Say nothing and you get exactly the old search:

```
plan found in 2 step(s) after imagining 2, goal: tower [a on b, b on c]
  stack(b=b, onto=c)
  stack(b=a, onto=b)
```

Now have the decision say *stop* after the first imagined step:

```
no plan: that's enough planning
```

```
{'found': False, 'steps': 1, 'stopped': 'commit', 'why': "that's enough planning"}
```

Three things to notice. It stopped after one imagined step rather than two. It
says **which word stopped it** and **the reason it was given**. And it hands
back the prefix it had — the workbench and the frame are still there, so the
partial plan is available rather than discarded.

The reason also lands on the thread, next to everything else that happened:

```
taking on the goal
decided to commit
```

That matters more than it looks. Chapter 13's thread already recorded what the
machine *considered*, not just what it did. Now it records what **governed** the
considering. A run you can't reconstruct the governance of is a run you can't
defend afterwards, and Chapter 18 is where that stops being abstract.

## Not knowing a word is an error, not a shrug

Hand the decision a word the machine can't act on and it stops loudly:

```
'dance' is not one of ('expand', 'decompose', 'commit', 'sense', 'refuse')
```

And even for a real word used at the wrong moment:

```
'decompose' needs per-STEP decomposition; a method applies per GOAL,
via driver.attempt — methods are consulted once per goal, not per step
```

That second message is really about the next section.

## How often each kind of decision gets asked

This is the part most likely to be got wrong, and getting it wrong makes the
cure cost more than the disease.

A search reaching sixty-something imagined states scores a dozen candidate moves
at each one — many hundreds of scorings for a two-step plan, and far more on
anything harder. So a decision that runs at that rate has to be cheap, and a
decision that's expensive has to run at a rate where that's affordable.

| what decides | asked | how often | so it must be |
|---|---|---|---|
| a recipe or a procedure | when a goal is taken on | a handful of times | may be expensive |
| a stop-rule (`commit` / `sense` / `refuse`) | once per imagined step | hundreds | cheap and structural |
| a guideline | once per *candidate move* | thousands | pure ordering, nothing else |

That's why `decompose` refuses to be answered per step. Not because the
machinery is missing — Chapter 18's recipes exist and work — but because
matching a recipe against a goal is a per-goal-sized job, and doing it per step
would invert the cost of the thing it exists to save.

The three chapters that follow are one row of that table each.

## When several things apply at once

Fixed order, declared once, no weights and nothing to tune:

1. a safety constraint is breached → prune the branch *(a proof — Chapter 12)*
2. a **procedure** applies → decompose, or refuse if it can't be followed
3. a **recipe** applies → decompose
4. a **stop-rule** applies → commit or sense
5. otherwise → expand, ordered by relevance, ties broken by **guidelines**

Where several of one kind apply, the one declared first wins. That's free —
declaration order is already recorded — and it's deliberately not a number.

!!! warning "Why there are no weights anywhere in this"
    A numeric combiner would let you blend a safety constraint, a recipe and a
    heuristic into a single score, and it would work beautifully on the example
    in front of you. Then it needs tuning, and the tuning is per domain, and the
    numbers end up meaning nothing to anyone who didn't set them.

    Fixed precedence has a real cost — you can't express "usually this, but
    slightly more that" — and it buys something worth more: every decision has
    exactly one reason, and the reason is a sentence rather than a magnitude.

!!! note "Deep dive: how do you test a gap that does nothing?"
    The first version of this changed no behaviour at all: the search consulted
    the new decision point, got told nothing, and carried on. Which raises an
    awkward question — how do you check you've built anything?

    Not by checking the old behaviour is unchanged. A gap nothing can steer is
    indistinguishable from no gap, and it would pass that check perfectly. So
    the check requires **both halves**: the default path identical, *and* a
    decision genuinely diverting the search. A version that consults the
    decision and throws the answer away fails the second half.

    That habit — asking what a passing check would still pass if the feature
    were absent — is the one this project trusts most.

---

**Next:** the cheapest kind of authored knowledge, and the only kind that can be
wrong without ever being dangerous. [Advice it may ignore →](17-advice-it-may-ignore.md)
