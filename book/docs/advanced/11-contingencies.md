# Contingencies and replanning

A step diverged. Now what?

The machine has exactly two honest moves, and — this is the nice part — it
chooses between them on **structure**, not on a policy someone tuned.

## First: was this already thought about?

The plan forked back in Chapter 6 because someone thought the scan could turn
out more than one way. One branch assumed files; the other assumed empty.
Reality says empty.

So the machine asks each sibling branch **the same question that detected the
problem** — does reality deviate from *this* branch's promise? The branch that
assumed *empty* survives that test.

```
recovery kind: contingency
ran after    : ('scan_dir', 'archive')
completed    : True
```

And notice what that is. It isn't replanning. It's a plan for the world we're
actually in, **already imagined and already checked**, sitting there waiting.
Continuing down it is just following the contingency the fork existed for.

The machine tries this first on evidence rather than taste: a matching branch
has been verified against this world; a freshly-invented plan has not.

## Three ways this goes wrong, all avoided on purpose

This is the part of the system where mistakes are expensive, so each of these is
guarded explicitly.

**The diverged step must not run again.** It reached the world once. Running it
a second time doubles whatever it did — sends the message twice, moves the crate
twice. So its *real* outcome is carried across onto the branch being resumed,
rather than the branch being replayed from the top. This is the single most
likely bug in this whole area.

**The sibling must be the same action.** A fork isn't necessarily about
alternative *outcomes* — it might be a different move entirely. Resuming into
one of those would silently skip a call that never happened, and then cheerfully
report success.

**The resumed branch may refer to things that were only imagined.** Its next
step might operate on a file the *other* branch had dreamed up. So whatever
reality actually produced has to be bound onto this branch's imagined stand-ins
before it continues.

None of these are hypothetical. Each was planted as a deliberate bug to confirm
the guard catches it — and the third was only found because a probe showed the
binding step running with an empty list, quietly testing nothing.

## Second: nothing explored fits

If no sibling survives, the branch tree has nothing useful to say. Then the only
sound move is to plan afresh **from the world as it actually is**, taking the
diverged step's real result as the starting point — because that is, literally,
the current state.

Here's the trap the machine fell into first, and it's instructive.

Recovery originally went to the *backward-chaining* planner from Chapter 7 — the
one that chains through what each action produces. Asked to recover a diverged
"some file must exist", it answered:

```
    listing: already satisfied
```

True. And completely useless. Backward chaining knows about **shapes**, and it
had one; it knows nothing about the *goal* you were pursuing.

The fix is the obvious one once you see it: **replanning is going round the loop
again.** Come back to the goal, open a fresh workbench on the world as it now
stands, and pursue it. No new machinery — the outer loop already does this.

## The loop, closed

Put it together and you get the machine's actual life:

```
plan by imagining  →  act for real  →  reality disagrees
       ↑                                      │
       └──────────  replan from here  ←───────┘
```

A real run: the first scan finds nothing, the prediction breaks, the machine
replans from the real state, a file has appeared by then, the second attempt
completes, and only *then* is the goal recorded as met.

## The world moving while the plan was waiting

There's a third way a plan fails, and it isn't a step going wrong. It's a step
that was fine when the plan was made and **isn't fine any more**.

A plan gets verified against a world, and then it waits its turn. Meanwhile
something else moves: a subgoal runs, another goal on the same loop gets a tick
(Chapter 25), or the world simply changes on its own. By the time step three
comes up, its requirement — *I must be at home to catch the train* — is no
longer true.

The machine already caught this. Every call re-checks its requirements at the
moment it's made, which is precisely the check that stops a plan acting on a
world it was never verified against. That part was right.

What was wrong was how it reported. It **raised** — and nothing caught it. The
failure went straight up through the executing step, past the pursuit, and out
of the outer loop itself. Two things died:

- the pursuit was stranded mid-action, believing it was still going;
- **every other task on the loop died with it**, including one that had nothing
  whatever to do with it.

That second one is the real damage, and it's invisible to any test that runs one
thing at a time.

So a broken requirement is now reported the same way any other surprise is: as a
**divergence**.

```
attempt 0: ran ('fly_home',), completed=False
  DIVERGED at go_to_school
    expected at_home, but: {'@where': ("== 'home'", "'abroad'")}
    go_to_school could not be applied: its p no longer satisfies what it
    requires. The world moved after this plan was verified.
attempt 1: ran ('fly_home', 'go_to_school'), completed=True
```

Three things about that report are deliberate:

**It's a divergence, not an error.** The plan met the world and the world had
moved. That's what divergence *is*.

**No contingency is offered.** Chapter 11 opened by trying siblings first — but
a sibling is resumed by carrying the diverged call's *real outcome* across, and
here the call **never ran**. There is no outcome. Offering a contingency would
mean resuming a branch on the strength of a result that doesn't exist, so the
machine declines and replans instead.

**The neighbours survive.** The unrelated goal sharing the loop keeps ticking
and finishes for real. That's the property the whole change was for, and the
machine's own check enforces it by running a second, entirely unconnected plan
alongside — one that shares no node, no shape and no action with the first — and
confirming it was still going *at the moment* the other one failed.

## "I know how to do this" is not "this is now true"

That last clause is a distinction the machine got wrong once, and it's worth
your attention because it's easy to reproduce in any planning system.

Two different facts:

- **a plan was found** — the goal is met *in imagination*;
- **the goal is closed** — it's met *in reality*.

These were originally one record. The result was that a goal read as
**accomplished** the moment an imagined frame satisfied it — while execution had
diverged and nothing whatsoever had happened in the world.

They're separate now, and every downstream reader inherits the distinction
rather than the confusion.

## What isn't here

Honesty about the edges, because they're real:

- **A re-proposal isn't rehearsed.** When the machine replans, it commits to
  nothing — but the new plan also hasn't been run on a workbench the way the
  original was. Fixing that needs a real decision about how a pending step's
  output binds to an imagined stand-in, which is the same open question as
  Chapter 14's. A guessed binding would produce a plan that merely *looks*
  rehearsed, which is worse than one that's honestly unverified.
- **Ties are taken first-come.** Among several matching branches, the machine
  takes the first rather than pretending to choose well.
- **Nothing stops you forking everything.** Three uncertain steps with three
  outcomes each is twenty-seven plans, and that's a small plan. The discipline —
  *branch only where being wrong is expensive; keep the rest for when reality
  actually disagrees* — is currently a discipline, not something enforced.

---

**Next:** the machine can recover from surprises. Now: the things it must never
do, whatever happens. [What it may never do →](12-what-it-may-never-do.md)
