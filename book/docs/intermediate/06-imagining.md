# Imagining

The machine wants a tower. It has actions that could build one. So why doesn't
it just start stacking?

Because it might be wrong — and because it can find out for free.

## Somewhere that doesn't count

The machine opens a **workbench**: a private copy of the world, with every
consequence of an action landing in the copy rather than in reality.

Watch it stack `b` onto `c` there:

```
frames so far        : 2
in the copy, b is on : c
in reality,  b is on : the ground
```

Both statements are true at once, and neither is a fudge. There genuinely is a
situation in which `b` sits on `c` — it just isn't this one.

That's the whole idea. **Nothing is committed by thinking.**

## Why a copy, and not a list of intended moves

The obvious cheaper design is to keep a list — *"I intend to stack b on c, then
a on b"* — and never copy anything. It's smaller, and it's not enough, for a
reason that only shows up when things go wrong.

A list tells you what you *meant* to do. It can't tell you what the world would
have *looked like* at step two. And "what was supposed to be true at step two"
is precisely the question you need answered when step two surprises you. With
one live state there's nothing to compare against.

So the machine keeps a **frame** per step: a snapshot of how things stood after
each imagined move. Frame 0 is where we started, frame 1 is after stacking. Two
frames, as reported above.

## Frames form a tree

Steps extend a path. But an action that could turn out more than one way
**forks** it:

```
                   ┌── (it's empty)  ──> …
   (before) ──scan─┤
                   └── (it's full)   ──> …
```

Both branches are imagined, both are kept. Which gives the machine something
valuable and slightly unusual: when reality later announces the directory was
empty, the plan for that case **already exists**, already checked. Chapter 11
is about cashing that in.

An abandoned branch is kept as data too. A dead end that was explored and
rejected is exactly the thing worth not re-exploring.

## Following the thread back to reality

Here's the subtle part, and the one the design would fail without.

Inside the copy, `b` isn't the real `b` — it's a stand-in. So if the machine
plans a step against the stand-in and then tries to carry it out, which crate
does it actually lift?

The answer is that each imagined thing keeps a **mapping** back to what it
stands for, and every planned step binds to the *mapping*, never to the raw
stand-in. Follow the mapping and you get the real crate. That indirection is
what makes a plan replayable at all.

A log saying "`stack` was applied" can't do this. It doesn't identify the
subject in a form that survives outside the copy.

!!! note "Deep dive: the direction rule"
    Anything *about* a node — a mapping, a plan step, a note — points **at** it,
    and the node never points back. That sounds fussy. It's load-bearing:
    copying follows arrows outward, so a single arrow pointing the wrong way
    would drag a node's mappings into the copy, and from there every frame,
    every workbench, and every plan that ever touched it. Not a wrong answer —
    an unbounded one. The machine checks this rule against itself.

## Guessing, on the record

Some actions genuinely can turn out several ways, and the machine can't know
which in advance. Listing a directory finds files, or finds nothing.

So an action is allowed to have several **assumed outcomes**, and imagining one
of them is *making an assumption*. The machine records that assumption on the
step — which means "which parts of this plan are guesses?" is a lookup, not a
judgement someone has to remember to make.

The order you declare those outcomes in is the order it prefers them. That's
deliberately the weakest thing that works: something has to pick a default, and
it should be by *intent* rather than by whichever one happened to be written
first.

## The guarantee that isn't in the plan

One thing sits underneath all of this, and it's worth saying plainly because it
would be easy to get wrong.

When the machine imagines an action that would reach outside — send a message,
delete a file, phone someone — **the outside call is refused**. Not skipped, not
faked: refused, because its target exists only inside a workbench.

That refusal is deliberately kept separate from the mechanism that substitutes
an assumed outcome. Substitution is what makes planning *useful*. The refusal is
what makes it *safe*. If substitution were ever forgotten or bypassed, an
outward-reaching action still could not touch the world. Putting the guarantee
inside the substitution would be putting it in the wrong place — it would be
a habit rather than a wall.

## What it costs

Honestly: a full copy per frame. The machine doesn't try to be clever about
which parts of the world might matter, because every cleverer boundary is a
*guess*, and a wrong guess produces a plan that looks fine and falls over on
contact with reality.

There's a well-known cheaper technique that gives exactly these semantics, and
it's available if the cost ever bites. It hasn't been taken yet, deliberately —
measure first.

---

**Next:** the machine can imagine one step. Now watch it search — and find a plan
it never actually built. [Finding a plan →](07-finding-a-plan.md)
