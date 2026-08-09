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

## A stand-in can be a *model*, not just an assumption

Everything above treats the imagined outcome as a guess: *suppose the folder has
files in it*. That's how the stand-ins in Chapter 6 were written, and it made
them look like the only thing they could be.

They aren't. A stand-in is an ordinary rule, so it can **read the world and work
the answer out**.

Take a machine that can run `git status` on a repository. Here's the same
unedited stand-in, consulted twice:

```
in a repository nobody has touched   →  predicts: dirty = False
in a repository I have just edited   →  predicts: dirty = True
```

One stand-in. Two worlds. Two different predictions, *because the worlds
differ*. That's not an assumption — it's an **anticipation**, and it's the
difference between *suppose it comes back clean* and *I know I changed three
files, so it had better come back dirty*.

Nothing was added to the machine to make this possible. It had simply never been
written down that a stand-in could do it.

And notice what it buys. Run `git status` for real in the edited repository and
have it report *clean*, and:

```
completed : False
diverged at: git_status
  assumed: git_status turns out report
  expected: report                        ← the declared shape: passes
  unmet_expectations: ('expected dirty=True but found False',)
```

The shape check passes because `report` says nothing about `dirty` — the answer
is a perfectly well-formed status report either way. Only the anticipation
catches it. That's a genuine surprise about the world, detected because the
machine had a model of what it was about to see rather than a hope.

## Where the relation between acting and looking comes from

There's something slightly odd about the example above, worth pulling out.

*Editing files* and *running `git status`* are two completely different
operations. Nothing in either one mentions the other. So how does the machine
know they're connected — that having done the first is a reason to expect
something of the second?

The obvious answer is to write the connection down: an arrow saying `git_status`
*reflects* `edit`. And it's the wrong answer, for a reason this book keeps
returning to — an authored connection can drift away from what the rules
actually do, and then it's a confident lie.

The machine derives it instead, from two things it already has:

| | comes from | says |
|---|---|---|
| what the **act** does | `edit`'s own body | it writes `changed_file` |
| what the **look** watches | `git_status`'s **stand-in** | it reports on `changed_file` |

Overlap them and the relation falls out. And the asymmetry is the interesting
part: for the *act* you read the body, but for the *look* you must read the
**stand-in** — because a look's body is just "reach outside and ask", which
establishes nothing at all. Read the look's body and every look in the world
relates to nothing.

The payoff is drift. Refactor `edit` to write a differently-named slot and leave
the stand-in untouched, and the relation **disappears** — correctly, because the
model is now watching the wrong thing. An authored arrow would still be sitting
there, still saying the two are connected, still true-looking.

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
