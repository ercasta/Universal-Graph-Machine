# Wanting something

Part 1 left the machine in an odd position. It has a world, it has rules, and
rules only run when something points them at something — but nothing points.
Nothing happens.

This is where that gets fixed. The machine acts because it **wants** something,
and this chapter is about what wanting is made of.

## A goal is a list of things that must be true

Back to the crates from Chapter 0:

```
goal build a tower:
    a on b
    b on c
```

The machine reads that as two separate **constraints**, and it keeps them
separate — that turns out to matter enormously:

```
goal: build a tower [a on b, b on c]
```

Each constraint is an ordinary node in the graph, like everything else. A goal
isn't a string you handed to a planner and a planner swallowed. It's data,
sitting there, inspectable.

## The question that makes planning possible

Ask whether the goal is met:

```
satisfied now?   False
```

Not much use. Now ask the *good* question:

```
what's missing?  ['a on b', 'b on c']
```

This is the difference between a machine that can plan and one that can only
flail. A goal that answers **yes/no** leaves a searcher nothing to aim at — all
it can do is try things and check afterwards. A goal that names **which
constraints are still false** lets the machine ask a much better question:

> *What could make `a on b` true?*

That's the shift from **generate-and-test** to **means–ends**: instead of
guessing and checking, work backwards from what's actually missing. In Chapter 7
we'll see it cost three imagined situations instead of eighty-seven.

And it only works because the goal was kept as separate constraints. Squash
those two lines into one indivisible wish and there's nothing to work backwards
from.

!!! note "Satisfied is always recomputed"
    The machine never stores "this goal is met". It re-checks the structure
    every time, exactly as Chapter 2's types are re-checked. It *does*
    separately record "I found a plan for this" and "this was actually done" —
    but those are claims about the machine's own history, and it keeps them
    firmly apart from the question of whether the thing is true right now. A
    plan that was found and then diverged must never read as an accomplished
    goal.

## Three kinds of thing you can want

The vocabulary is small and closed on purpose:

| form | means |
|---|---|
| `a on b` | a **relationship** between two particular things |
| `b.clear = true` | an **attribute** having a particular value |
| `some file` | **something** of that shape must exist |
| `a is a sealed_jar` | that particular thing must satisfy that shape |

The third one is worth noticing. `some file` doesn't name anything — it says
*bring a thing of this kind into existence*. That's a goal no signature could
express, and Chapter 7 shows the machine satisfying it by finding an action that
**creates** files rather than one that changes something that already exists.

!!! note "Deep dive: why relationships can't just be shapes"
    Chapter 2's shapes say things like *3 jars* — a kind and a count. They can
    never say *this particular jar*, because a shape is reusable and an
    individual isn't. So "a on b" genuinely needs its own form. The two kinds of
    constraint stay separate on purpose, and one goal can hold both.

## Wanting things about the journey, not just the destination

Everything so far describes the world *afterwards*. But you can also constrain
**how the machine is allowed to get there**:

```
never unstack           don't use that action at all
never touch c           leave that crate alone, by any means
must paint              the plan has to include this somewhere
at most 3 steps         a budget
```

You saw `never paint` in Chapter 0. What's worth understanding is *why the
machine can offer this at all*, and the answer is Chapter 6's: a plan here isn't
a value some planner handed back. It's frames and steps sitting in the graph. So
"which actions did you use, and how many" is an ordinary question about ordinary
data — the same kind of question as "is `a` on `b`".

These four split into two families, and getting the split wrong breaks planning
in both directions:

**Safety** — `never`, `at most`. If a plan has already broken one, no amount of
continuing can repair it. So a breach is a **proof** the branch is dead, and the
machine prunes it — *before* imagining the step. A forbidden action costs
nothing at all.

**Liveness** — `must`. A plan that hasn't painted anything yet isn't in
violation; it's unfinished. So this is checked only at the end, and it must
never prune, or every branch dies at step one.

Same syntax, opposite handling, and the machine decides which is which from the
constraint itself rather than asking you to remember.

## Goals that contradict themselves

Some wishes can't be met, and sometimes that's provable without searching at
all — wanting a jar both sealed and unsealed, or `never seal` alongside
`must seal`, or a budget of zero steps. The machine checks for those first and
refuses at zero cost.

Deliberately, it only reports contradictions it can *prove*. "You can't build a
tower with two crates" is a fact about the world that would need domain
knowledge, so it's left to the search to discover honestly. A conflict detector
that cries wolf is worse than none, because you stop reading it.

---

**Next:** the machine has something to want. Now watch it try things out
somewhere that doesn't count. [Imagining →](06-imagining.md)
