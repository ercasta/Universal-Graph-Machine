# When reality disagrees

Everything so far has assumed the world cooperates. It doesn't.

The machine planned by imagining. Imagining is guessing — careful, structured
guessing, but guessing. This chapter is about what happens when the guess turns
out wrong, and it's where the design starts paying for itself.

## A plan that assumed something

New scenario. The machine can **scan** a directory — an action that genuinely
reaches outside, into a real filesystem. It can't know in advance what's there,
so it has two assumed outcomes: the directory holds a couple of files, or it's
empty.

It plans on the first assumption, intending to archive what it finds.

Then we run it for real, against a directory that is, in fact, empty:

```
ran      : ('scan_dir',)
completed: False
diverged at: scan_dir
  assumed: scan_dir turns out listing
  expected: listing
  unmet_expectations: ("expected some 'file' edge, found none",
                       'expected some new file node, found none')
```

It noticed. Immediately, at the exact step, and it can say **what** it expected
that didn't happen.

## Where the expectation came from

Here's the part worth slowing down for, because the obvious design is wrong.

The obvious design: have each action declare what it expects. That's an
authoring burden, and worse, it's a second description of the action that can
drift away from what the action does.

The machine does something better. It **already imagined** the outcome — that's
what Chapter 6's frames are. So the frame before the step and the frame after it
*are* the before and after. The expectation is simply their difference,
computed when needed and never stored anywhere.

Nothing is authored. Nothing can drift. And the machine doesn't pay for a stored
expectation on every one of the hundreds of steps it imagines while searching.

## Expectations are qualitative, never quantitative

This one was got wrong first, and the correction is the most useful idea in the
chapter.

The assumed outcome created **two** file nodes. So the first version of this
expected two files, and reported a divergence when reality produced three.

That's useless. A directory listing produces a *variable* number of files;
diverging on three-instead-of-two is diverging on noise. The number in an
assumption is a **witness, not a promise** — it's there to make the imagined
world concrete, not to be checked.

So the expectation is existential: *some* file appeared. One file completes the
plan. Five complete it. **Zero** diverges — and zero is the case that actually
matters, because it's the one that breaks everything downstream.

## Two kinds of check, doing two different jobs

The machine checks a completed step twice, and the division is deliberate:

| check | catches |
|---|---|
| **the declared outcome shape** | the discriminating claim — empty versus non-empty |
| **the derived expectation** | the qualitative change — files appeared at all |

An expectation never re-checks what the shape already checks, so a failure gets
reported once, in the place that owns it.

That matters here because in this scenario **both assumed outcomes declare the
same shape** — `listing`. Reality satisfies it either way. So the shape check
passes, and only the derived expectation can catch the disagreement. Had the
machine relied on types alone, it would have sailed on to archive a listing that
contained nothing.

## Fail fast, and don't pretend to undo

When a step diverges, the machine **stops**. It doesn't attempt the rest of the
plan, because every later step was chosen on the assumption that this one held.

And it does not roll back. This is worth stating plainly:

> Real effects have already left. A file was written, a message was sent, a
> crate was moved. No amount of internal bookkeeping reaches them.

The machine has an undo journal for its own graph, and it is scrupulous about
its limits: **a rollback boundary must never span a step that reached outside.**
Pretending otherwise would be worse than not having one, because you'd trust it.

So the honest report is the one you got above: *these ran, this one diverged,
here's how.*

!!! note "Deep dive: matching up things that didn't exist yet"
    A step can create something — a file that had no counterpart at planning
    time. Its imagined version has nothing to map back to, so the machine
    matches real to imagined by *which step produced it*. That's the only
    correspondence available. And when one step creates two things of the same
    kind, the pairing is genuinely a guess — so the machine **says so in its
    notes** rather than choosing silently and looking confident.

## The point of having assumed anything

Notice what the machine has, at the moment of failure, that a simpler system
wouldn't: it knows the assumption it made, it knows the assumption was wrong,
and — because it explored the alternative back in Chapter 6 — **it already has a
plan for the world it's actually in.**

That's the next chapter.

---

**Next:** what to do about it. [Contingencies and replanning →](11-contingencies.md)
