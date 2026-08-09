# Forgetting is the default

Three ordinary goals on a world of three blocks. Start with 80 nodes; finish with
**892**.

None of that is a leak. Every one of those nodes is something that made the
machine able to say what it was doing: imagined states, candidate moves, trace
steps, frames, mappings, replays, half-run programs, registers. Parts 2 through 6
were spent building them on purpose.

But roughly three quarters of it is **scaffolding**, and scaffolding is
re-derivable. Given the goal and the library, the machine can think it again.

## The rule

> **Keep what you cannot re-derive.** There are two irreducible kinds: **a
> crossing of the world**, and **a surprise**. Everything else is ordinary.

Stated the other way round, which is how it's meant: *forgetting is the default;
remembering is the exception.*

A **crossing of the world** is the result of a tool call. You cannot re-do it —
the world has moved on, and re-doing it may not even be safe. What the machine
saw when it looked in that folder is gone the moment it stops being written down.

A **surprise** is a change nothing the machine did can account for: Chapter 24's
`external` verdict, a prediction that didn't materialise, an expectation that
came out wrong. It's information precisely *because* the machine's own model
failed to predict it. Re-deriving it is exactly what re-deriving cannot do.

Everything else — every state it imagined on the way to a plan it has already
found — is a note about a road it can walk again.

!!! note "This is not the opposite of Chapter 24"
    Chapter 24 argued that sightings default to being **kept**, because dropping
    what you reasoned from can contradict conclusions you've already drawn. That
    argument was about sightings, and every sighting survives here.

    What Chapter 24 didn't have was the category Chapter 25 then created: **the
    machine's own scaffolding**. So the rule generalises rather than reverses.

## Name the roots, not the rubbish

The obvious implementation is a list of droppable kinds. It's also the wrong one:
it drifts out of date the moment somebody adds a kind, and the drift is silent.

So the machine names what to **keep** instead — the world, what it was asked for,
what it did, what it saw, what surprised it, the library — and drops whatever
none of those can reach.

That works because of a rule the graph has enforced since Chapter 13: **metadata
points inward**. Memory points at the world and the world never points back. So a
root that is a piece of world drags no scaffolding in with it, while a surprise
drags in exactly what it was a surprise *about*.

**And live work needs no special case.** A task on the agenda is a root. Being
scheduled *is* the statement "this is what I am doing", and because a pursuit
points at its search which points at its workbench, the closure protects all of
it. A sweep can run *while* the machine is mid-plan, and the plan still finishes
and still changes the world.

!!! warning "Forgetting is a task, not a pass"
    It goes on the agenda from Chapter 25 and drops **one record per tick** —
    interleaved with real work, and stoppable partway through.

    A sweep that ran to completion inside a single call would be exactly the
    uninterruptible thing the last two chapters existed to remove, and of all the
    candidates it is the worst one: it is the operation you most want to be able
    to interrupt.

    And it isn't exempt from its own rule. A finished sweep is ordinary
    scaffolding, so the next one forgets it.

## The number is not the point

Measured: **892 nodes to 175**.

Which proves nothing on its own, and this is the trap worth naming. A sweep that
deleted everything would score beautifully on size.

So the test isn't the count. It's that **nothing became unanswerable**. Every
question the machine can ask of its past is asked before the sweep and after it,
and the answers must come back *identical*:

- what is true now;
- **why** it's true — Chapter 8's history, still complete;
- what I did, in order;
- whether two intentions collided (Chapter 15);
- which goals are met;
- whether the library can still plan.

Six questions, same answers, one fifth of the nodes.

There's one more key, and it's the one that catches a *partial* sweep:
**everything still there must be there for a reason.** Ask any survivor:

```
goal          what was wanted, and what was done
observation   the result of a tool call
deviation     a surprise: reality contradicted the plan
function      the library: authored, not derived
candidate     nothing keeps it          ← so it goes
```

If something survives that nothing keeps, the sweep didn't finish — even though
every answer above would still have been perfect.

## The bug that key was written for

It's worth telling, because the shape recurs.

The sweep marked records to drop, then walked its list of them. The list was a
set of **edges**, and dropping a node removes every edge into it — *including the
sweep's own edge to it*.

So the cursor walked a list shrinking underneath it and **silently forgot every
other record**. 892 down to 564, with 798 marked.

Everything looked fine. Every answer that had to be preserved was preserved. The
count really did fall. The only symptom was that it fell less than it should
have, which is not a symptom anybody notices.

This is the same family as a bug from earlier in the project, where a search
returned a set and its tie-break silently became hash order. Neither produced a
wrong answer. Both produced a **quietly partial** one, because a container behaved
in a way the walk over it didn't account for.

!!! note "Three of the four defects here were found by planting bugs, not by tests passing"
    One root, `thread`, turned out to name nothing at all — the protection was
    coming from somewhere else. Found by removing it and watching nothing change.

    Worse: the two exceptions the whole rule is *about* were **untested**. The
    blocks world never calls a tool, so it produces zero observations — a sweep
    over it could have dropped every observation there is and stayed green. Found
    by removing `observation` from the roots and watching nothing change.

    Green tests said the rule worked. Deliberately breaking it said which parts
    of it were being tested at all.

## Superseded, not forgotten

There's a gentler operation beside dropping, and it turned out to be a **rule**
rather than machinery.

Chapter 5's goals keep two kinds of evidence rigorously apart, because conflating
them was once a real bug — the machine closed a goal on imagined evidence and
reported it met while nothing had happened:

| record | means |
|---|---|
| `planned` + `seen_in` | *I know how to do this* — pointing at an imagined frame |
| `closed` + `met_by` | *this is now true* — pointing at something real |

Once the second exists, the first is a snapshot of a world that no longer does.
And one edge into one imagined frame keeps every frame, mapping and
transformation reachable from it alive.

So the whole of compaction is *knowing when a record is superseded*: two
unlinks, and a condition.

!!! warning "The condition is the correctness argument"
    A goal that was planned and **not** carried out has no other evidence. Its
    imagined frame is the only account of how it would be met, and recovering
    from a failure needs it.

    So the two goals must be treated **oppositely**, and a compaction that
    ignored `closed` would be forgetting the plan rather than tidying up. Break
    it deliberately and the tidying still *looks* like it works — while the
    merely-planned goal quietly loses its evidence and its plan becomes
    unreadable.

## Why this matters beyond housekeeping

A machine that keeps everything is not being careful. It's deferring a judgement
it should be making — about which of its records are claims on the world and
which are notes about how it got there.

Making that judgement explicit is what lets a machine run for a long time. And it
puts the burden where it belongs: not *what may I delete*, but **what could I not
reconstruct if I dropped it?**

---

**Next:** and the same question, asked of answers.
[What, where, and when →](28-what-where-when.md)
