# Remembering

The machine has been keeping notes since Chapter 0. Time to read them properly —
and to understand why they exist at all, because the reason is stranger than
"logging is useful".

## The hole this fills

Think back over the book. Rules are data. Goals are data. Plans are frames in
the graph. Explanations are the routes themselves. Everything the machine works
with is something it can point at and reason about.

Everything except one thing: **what it was paying attention to.**

Attention was a passing Python object, created for a call and thrown away. In a
machine whose whole claim is that a rule can reason about a rule, the thing it
looked *with* was the one thing it couldn't look *at*. That's the hole the
thread fills.

## What it looks like

```
thread session (6 entries)
  0. attend root [start]
  1. attend goal#80 [goal: tower [a on b, b on c]]  (taking on the goal)
  2. applied stack  (depth 1, 2 constraint(s) open)
  3. applied stack  (depth 1, 2 constraint(s) open)
  4. applied stack  (depth 2, 1 constraint(s) open)
  5. attend goal#80 [plan is 2 step(s)]  (goal met (found))
```

Two kinds of entry, and only two: a deliberate **shift of attention**, and an
**application** of a rule. Each carries *why* it followed the one before.

!!! note "Why not record everything?"
    Rules move a cursor around the graph constantly while running. Logging those
    would record pointer arithmetic, not reasoning — a perfect account of the
    machine's fidgeting, useless for understanding what it was doing. So nothing
    instruments that layer, on purpose. Two entry kinds is a judgement about
    what counts as a thought.

## Read entry 3 again

Here's the detail that teaches you the most about what this thread *is*.

The final plan was two steps. But there are **three** applications on the
thread, and entries 2 and 3 are both at "depth 1".

That's because the thread records what the machine **considered**, not just what
it settled on. Entry 2 was a move down a branch it later abandoned.

Which sets up a distinction that turns out to be load-bearing: the notes hold
both the search and the deed, and a reader has to know which it wants. When the
machine answers *why* something is true (Chapter 8), it looks only at what was
genuinely **done** — otherwise it would explain the world using roads not taken.
When it asks what it *thought about*, it wants all of it.

Marking that difference was a real fix, not a nicety. An early version of
conflict detection (next chapter but one) analysed the whole thread and
concluded that a goal which merely *considered* painting had claimed to paint.
It was analysing the search and reporting it as behaviour.

## Questions you can ask notes

Because the thread is ordinary graph data, ordinary questions work on it.

```
when did I last touch b? -> stack
its bindings: {'b': 'a', 'onto': 'b'}
```

*Which was the most recent thing I did involving that crate?* — answered by
stepping backwards through the entries. Every entry knows the one before it, so
going back is a single hop rather than a search, and the reason for each
transition rides along on the link itself.

You can also tie two distant moments together — *this is why that happened* —
and that link is a **node**, deliberately, so that something else can point at
it and dispute it. A note about a connection needs to be argued with; a mere
annotation can't be.

## The thread doesn't hang off the world

One structural detail with real consequences. Chapter 2 said real things hang
off the root. The thread **doesn't**.

Memory points *at* the world and is never pointed at by it. So when the machine
makes a copy of the world to think in, it doesn't drag its own memories along —
and when it enumerates what exists, it doesn't find its own notes and offer them
as things to reason about. The separation between the world and the scaffolding
is structural rather than something a filter has to maintain.

## And it's walkable by ordinary means

The thread is nodes and named arrows, so a rule can walk it — pointed at the
thread the way any rule is pointed at anything. No new instruction was needed,
and that's checked rather than asserted: there's a thread-walking rule, loaded
from stored text, running on the ordinary machinery.

That's what makes the next two chapters possible. A machine that can read its
own history can learn from it, and can notice when it's working against itself.

!!! note "Two things this chapter deliberately leaves for Part 6"
    The thread records what the machine **thought**. It says nothing about what
    the machine **looked at** — and *I believe the folder holds three files* and
    *I saw three files, at 4pm* are very different claims.
    [Chapter 24](../watching/24-what-it-saw.md) separates them, and uses the
    separation to answer *did I change this, or did somebody else?*

    And nothing here ever gets thrown away, which cannot be right for a machine
    meant to run for a long time.
    [Chapter 27](../watching/27-forgetting.md) makes forgetting the default —
    without any of the questions above becoming unanswerable.

---

**Next:** turning what it did into something it can do again.
[Learning from what it did →](14-learning.md)
