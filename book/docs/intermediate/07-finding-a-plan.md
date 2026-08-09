# Finding a plan — not building one

The machine can want things (Chapter 5) and try things out where they don't
count (Chapter 6). Put those together and you get planning.

The surprise is how little there is to it, and it starts with the chapter title.

## There is no plan-construction step

Here's what actually happens. The machine imagines a move, getting a new frame.
From there it imagines another. It keeps going until it reaches a frame where
the goal is satisfied.

And then — it's done. Not "then it assembles a plan". The **path through the
frames is already the plan**: every frame records the step that reached it, so
the route from the start to the winning frame is a replayable sequence of
actions. There was never any plan to build.

That's why the machine's own report reads the way it does:

```
found: True | imagined: 2 | plan length: 2
    stack(b=b, onto=c)
    stack(b=a, onto=b)
```

Two steps, found by imagining two situations.

## Why two and not sixty-seven

Turn off the machine's judgement and run the identical search — same world, same
actions, same goal:

```
  guided=True  found=True imagined=  2 plan=2 steps
  guided=False found=True imagined= 67 plan=2 steps
```

Both find the same two-step plan. One looks at two possibilities; the other at
sixty-seven. Around **thirty times** fewer situations considered, for the same
answer.

Run either of them again and you get the same numbers. That's worth a moment,
because it wasn't always true.

!!! note "Deep dive: the search used to give a different answer each time"
    For a while these figures wobbled — the same puzzle measured 12 situations,
    then 306, then 400-and-give-up, in a single session. The plan was never
    *wrong*, just arbitrary, and arbitrary at wildly varying cost.

    The cause was one line. A helper that collects what's reachable in the
    world handed back an unordered collection, so when the machine copied the
    world onto the workbench, the order it copied things in came down to
    where each node happened to land in memory. Two moves that scored the same
    were then separated by nothing at all.

    The lesson generalises past this machine: **a computation that's supposed
    to be repeatable and ends in an unordered collection has a hidden
    tie-break in it.** Over a hundred checks passed straight over this one,
    because every one of them asked whether the plan was right — and it always
    was.

The difference is that the guided search asks, of every move it might make:
**would this close something that's still missing?** Which it can only ask
because Chapter 5's goal names its unfinished business.

## How it knows what an action would do

Now the good part. To ask "would `stack` help?", the machine needs to know what
`stack` does. Where does that knowledge live?

Not in a declaration. **It reads the rule's own instructions.** As we saw in
Chapter 4:

```
effects read off the body: [('attr', 'sealed', 'j', None)]
```

Nobody writes an effects section. There's nothing that could fall out of step
with the body, because it *is* the body. That's Part 1's "a rule is data"
delivering something concrete rather than remaining a slogan.

And it reads **roles**, not just names. `stack` doesn't merely "write an `on`
arrow" — it puts *its argument `b`* onto *its argument `onto`*. Without that
distinction, `stack(b=b, onto=a)` looks exactly as promising for the goal
"a on b" as `stack(b=a, onto=b)` does, since both involve the same two crates.
With it, the machine can tell the right way round from the wrong way round, and
the guidance stops being nearly worthless.

## The rule that keeps hard problems solvable

Here's the trap, and the machine's answer is the most instructive thing in this
chapter.

If relevance tells you which moves help, why not simply *ignore* moves that
don't? It would be faster still.

Because it breaks. Try this famous little puzzle — `c` is sitting on `a`, and we
want `a` on `b` and `b` on `c`:

```
found: True | imagined: 50 | plan length: 3
    unstack(b=c, floor=ground)
    stack(b=b, onto=c)
    stack(b=a, onto=b)
```

Look at the first move. **`unstack` closes nothing.** It doesn't make `a on b`
true, or `b on c`. By any measure of relevance it's a bad move — and the puzzle
cannot be solved without it. You have to take something apart before you can
build.

So the machine's rule is:

> **Rank a guess; prune a proof.**

Relevance is a *guess* about what will help, so it only ever changes the **order**
things are tried. It never removes anything, because a guess that removed the
`unstack` would make this puzzle unsolvable while reporting an honest-looking
"no plan found".

A safety constraint from Chapter 5 — `never paint` — is a *proof*: no
continuation of a plan that painted something makes it unpainted. That prunes,
soundly.

The two sentences look contradictory out of context. They're the same principle:
match your confidence to what you actually know.

It also settles a question you might not have thought to ask yet: what happens
when *you* want to steer the search. Chapter 17 is that chapter, and this rule
is why the answer is "you may reorder it, and you may not prune it."

!!! note "Deep dive: three search designs that failed first"
    Depth-first burned an entire budget down one branch that could never work,
    while the sibling that solved it sat untouched. Best-first over *frames*
    measured no better than no guidance at all, because every move in a frame
    got imagined before any frame was chosen — ordering inside a frame can't
    save work you've already done. And a version that scored a move by the world
    it *started* from was worse than doing nothing, because a promising move at
    the top carried its parent's mediocre score and got abandoned. **A move must
    be judged by the world it would produce.** Each of these was measured, not
    guessed.

## What backward chaining can't do

The machine has a second, cheaper way to plan: chain backwards through what each
action *produces*. To get a sealed jar, find something that produces one.

It's useful and it has a hard limit worth knowing. An action declares **one**
outcome shape, so "stack a crate, then stack another crate" isn't a chain of
different stages — it's the same stage twice. Backward chaining literally cannot
express repetition.

Repetition comes from the search in this chapter. The two approaches answer
different questions and neither is a defect in the other:

- *What sequence of stages reaches this kind of thing?* — chain backwards.
- *What do I get if I try this, then this?* — imagine forward, a frame per step.

## When it fails

If the search runs out, the machine doesn't merely say no. It hands back the
workbench — **every situation it explored is still there**, along with what
remained unmet and which moves got refused.

That leads to an authoring rule that isn't obvious: **an action that wants to
explain itself must leave its reason where the frames are.** An action that
quietly does nothing when its preconditions fail is untraceable afterwards. One
that writes down *why* it did nothing can be found in the frame that tried it.
Silence costs nothing while planning and everything afterwards.

---

**Next:** the machine found a route. Now let's ask it the question it's uniquely
good at. [Because… →](08-because.md)
