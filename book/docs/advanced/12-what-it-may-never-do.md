# What it may never do

A machine that plans is a machine that will occasionally propose something you
didn't want. This chapter is about the limits — and specifically about the fact
that there are **three** of them, at three different places, doing three
different jobs.

Getting them muddled is how a system ends up with a limit that looks solid and
isn't.

## Limit one: shaping what's ever considered

You met this in Chapter 0:

```
never paint
never touch c
at most 3 steps
```

These live in the **goal**, and they work by pruning: the machine checks a move
against them *before* imagining it. A forbidden action is never explored at all.

The reason this is sound is worth restating from Chapter 7. A safety breach is a
**proof** — no continuation of a plan that painted something makes it unpainted.
So removing the branch can't lose a solution. Contrast relevance, which is a
*guess* and therefore only ever reorders.

What this limit is good at: shaping the space of plans. What it cannot do:
protect you from anything outside the planner.

There's a softer thing that looks like this and isn't — `avoid unstack`, which
means *later* rather than *never*. Keeping those two apart is Chapter 17's whole
subject, because a preference that quietly hardened into a prohibition would
lose you solutions while still producing plans.

## Limit two: the one door to the outside

Every action that touches the world — every message, every file write, every
call to anything real — goes through **one** place. Not one per tool. One, total.

That's what makes a check meaningful. A veto is ordinary data: a node saying
*this target is off limits*. And because there's a single door, one check covers
every tool that will ever be registered, including ones written by people who
never heard of vetoes.

Two rules govern that door, and both were established by experiment before
anything was built on them:

**Check when the action is about to happen, not when it's planned.** A planned
step is inert data until the door is reached — so a prohibition recorded *after*
the plan was made still blocks it. Checking at plan time would mean the answer
depended on the order you happened to do things in.

**Commit the graph before going through.** Once an effect leaves, atomicity is
over. So the machine's own state is settled first, and the undo journal is never
allowed to span the door. Chapter 10 said this about rollback; it's the same
rule from the other side.

This limit catches what the first one can't — anything reaching the world, no
matter which plan or which code path proposed it. What it cannot do is express
"don't use that action", because by the time you're at the door, the choice of
action is long past.

## Limit three: what may never be used to *think*

This one is subtler, and it's the one people don't anticipate.

In this machine, concluding something and doing something are both "running a
rule". `seal` changes a jar; `scan_dir` reaches a filesystem. Both are rules,
both run the same way. So when you ask a **question** — Chapter 3 — what stops
the machine from answering it by going and doing something?

Nothing, unless you say so. So:

> A rule may be used to answer a question only if it **provably never reaches
> the outside** — read off its stored instructions, following every rule it
> calls.

That's a proof, not a preference, so it prunes rather than ranks. And it's
deliberately conservative in the opposite direction from Chapter 7's effect
reading: if the machine *can't tell* whether a rule reaches outside, the answer
is no. An unreadable rule is barred. The cost of being wrong is a question that
goes unanswered, rather than a question that sends an email.

### Where the danger actually is

It's tempting to say this stops a question from deleting your files. Measured,
that's not quite true, and the precise version is more interesting.

Remove the bar and ask a question, and the search *doesn't* delete anything —
because searching happens on a workbench, and limit two refuses any target that
only exists in imagination. What you get instead is a **crash**: the question
becomes unanswerable.

The real exposure is one step later. When you decide to **keep** what the
machine worked out, the derivation is replayed against the real world — and
there, the outside call is genuine. A proof containing an impure step sends the
mail at the moment you accept the answer.

So the bar does two jobs: it keeps the search from crashing on a candidate it
was never entitled to try, and it makes *keeping an answer* safe by construction
rather than by you inspecting the proof first.

## Three limits, three jobs

| limit | where | stops |
|---|---|---|
| goal constraints | while planning | actions being *considered* |
| the one door | at the moment of acting | effects reaching the world |
| the purity bar | while answering | thinking that would *act* |

They're layers, not duplicates. Each catches something the others structurally
cannot, and none of them is a substitute for another.

!!! warning "The general lesson, which outlives this machine"
    A guarantee belongs where it cannot be forgotten. When the machine plans, an
    outward-reaching action gets substituted for a harmless assumed version —
    and that substitution is what makes planning *useful*. It is deliberately
    **not** what makes it safe. Safety is the separate refusal at the door, so
    that if substitution were ever bypassed or forgotten, the action still could
    not reach anything. Putting the guarantee inside the convenience would have
    made it a habit rather than a wall.

---

**Next:** the machine has been keeping notes this whole time. Let's read them.
[Remembering →](13-remembering.md)
