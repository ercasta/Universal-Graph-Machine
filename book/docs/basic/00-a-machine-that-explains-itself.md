# A machine that shows its work

Most computers are oracles. You ask, they answer, and you just have to trust
them. Type a question into a box and you get back "42" with no way to see how it
got there.

This machine is different. It works things out — and it can always show you the
working. Let's watch it do something small and completely honest: build a tower.

## A very small world

Three crates on the ground, labelled `a`, `b` and `c`. That's the entire world.

```
        [a]   [b]   [c]
    ────────────────────────
            the ground
```

The machine also knows two things it can *do*. Not facts — **actions**:

- **stack** — put a crate on top of another crate, if both have clear tops.
- **unstack** — take a crate off whatever it's on and set it on the ground.

And, because we'll want it in a minute, a third action with nothing to do with
towers at all: **paint** a crate red.

## Tell it what you want, not what to do

Here's the whole instruction. Read it out loud — it's a wish list:

```
goal build a tower:
    a on b
    b on c
    never paint
```

Three lines. The first two say what must be **true when it's finished**: `a` on
top of `b`, `b` on top of `c`. The third says something about **how it's allowed
to get there**: don't paint anything, ever.

Notice what we did *not* write. We never said "first stack b onto c, then stack
a onto b". We never mentioned the order, or which crate to move first, or that
`b` has to move before `a` does. We described the destination and left the route
to the machine.

## Watch it work

```
found: True | imagined: 2 | plan length: 2
    stack(b=b, onto=c)
    stack(b=a, onto=b)
```

There's the plan: put `b` on `c`, then put `a` on `b`. Which is right — and it's
also the *shortest* right answer.

But look at the middle number. **It imagined 2.**

Two hypothetical situations considered, in total, to find a two-step plan. The
machine wasn't grinding through every combination of crates and actions. It was
working out which moves could possibly help, trying those first, and leaving the
rest alone. Chapter 7 is about how — and about the honest measurement that the
same search, run *without* that judgement, takes 67.

!!! note "Every number in this book is a real measurement"
    Nothing here is illustrative. Run this yourself and you get 2, and you get
    2 again — the search is repeatable, and Chapter 7's deep dive is about the
    period when it wasn't and nobody noticed.

!!! note "The word 'imagined' is literal"
    The machine did not stack anything to find this plan. It made a private copy
    of the world and moved crates around **in the copy**. Nothing real moved
    until it had a plan it believed in. That copy is an actual object with an
    actual name — the *workbench* — and Chapter 6 is entirely about it.

## The line you didn't need

Remember `never paint`? Here's what the machine says about it afterwards:

```
blocked: ('never paint',)
```

It's telling us the rule *did something* — a move it would otherwise have
considered got refused. And here's the part worth pausing on: a forbidden action
costs **nothing**. The machine doesn't imagine painting a crate and then throw
the result away. It never imagines it at all.

That sounds like an optimisation. It isn't. It's the difference between a
machine that *might* do the thing you forbade and then think better of it, and
one for which the forbidden thing was never on the table. Chapter 12 is about
that difference, and about where each kind of limit belongs.

## Then it actually does it

Planning is not doing. So far every crate is exactly where it started. When we
tell it to go ahead:

```
carried out: True | ran: ('stack', 'stack')

  a is on b
  b is on c
  c is on the ground
```

The tower is real now. Two actions ran, and they were the ones it had rehearsed.

The rehearsal matters more than it looks. Because the machine had already
imagined each step, it knows what each one is *supposed* to produce. So when
reality doesn't match the rehearsal — the crate slips, the shelf is full, the
file isn't there — it notices immediately, and it knows exactly which step
surprised it. That's Chapter 10, and it's where this machine earns its keep.

## And it remembers doing it

One more thing. The machine kept notes:

```
thread session (5 entries)
  0. attend root [start]
  1. attend goal#80 [goal: build a tower [a on b, b on c, never paint]]  (taking on the goal)
  2. applied stack  (depth 1, 2 constraint(s) open)
  3. applied stack  (depth 2, 1 constraint(s) open)
  4. attend goal#80 [plan is 2 step(s)]  (goal met (found))
```

You can read the whole episode: it took on a goal, applied `stack` twice, and
finished. Look at entry 2 — *"2 constraint(s) open"*. It's recording not just
what it did but **how much of the goal was still unfinished when it did it**.
Entry 3 says one. It was closing in.

This isn't a log file. It's ordinary data in the same graph as everything else,
which means the machine can *read its own notes* and reason about them. That's
how it answers "why did you do that?" in Chapter 8, and how it notices two of
its own intentions colliding in Chapter 15.

## What you just saw

Four ideas. The rest of the book is these four getting sharper:

1. **You describe the destination; it finds the route.** Goals are things that
   must be true, not scripts to run.
2. **It imagines before it acts.** Plans are rehearsed in a copy of the world,
   so nothing is committed by thinking.
3. **Limits are part of the goal.** "Never do this" shapes the search instead of
   being checked afterwards.
4. **It keeps its working.** Not a summary written after the fact — the actual
   steps, still readable.

---

**Next:** what this world is actually made of. It's simpler than you'd expect —
one kind of thing, joined by named arrows. [The substrate →](01-the-substrate.md)
