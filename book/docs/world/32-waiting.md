# Waiting

*Take the pasta off after ten minutes.*

Every chapter so far has been about the machine doing something. This one is
about it doing nothing — on purpose, for a known length of time, without
becoming useless in the meantime. It's a surprisingly good test of everything
that came before.

## Nothing new is represented

That's the striking part. A timer needs two things, and the machine already had
both:

- **a moment** to wait for — Chapter 29's, with an actual clock reading on it;
- **a task** to run when it arrives — Chapter 25's, since every unit of work in
  this machine is an ordinary task on one agenda.

All that was missing was the edge connecting them. And it hangs off the **task**,
not off the queue:

```
this task ──not_before──▶ (moment t=1000.0, "pasta is done")
```

So *"when may this run?"* is a property of the work itself, answerable by anyone
looking at it — rather than a fact locked inside whatever queue it happens to be
sitting in.

## It waits; it does not spin

Two tasks on the agenda: taking the pasta off, gated on ten minutes' time, and
laying the table, gated on nothing.

Run it before the ten minutes are up:

```
ran   : lay_the_table
why   : waiting on a timer
waiting on : (the pasta task)
```

Then move the clock forward and run it again:

```
ran   : take_the_pasta_off
why   : the agenda is empty
pasta cooking : False
```

Four things in those two runs, and each was a way of getting it wrong:

**The gate really gates.** The pasta task did not run early. Otherwise it's
decoration.

**The gate is not a block.** It ran the moment the clock reached it.

**One timer doesn't freeze the machine.** Laying the table happened while the
other task waited. A gate on one piece of work must not stop unrelated work.

**Waiting is reported, never spun on.** This is the one worth dwelling on. The
easy implementation rotates the gated task to the back of the queue and tries
again — and then the machine burns through its entire tick budget doing nothing
while *looking exactly like progress*. That's the shape of every silent failure
in this book. Instead the tick returns a record naming what it's waiting for and
stops, because *sleep, or go and do something else* is a decision only the thing
driving the machine can make.

!!! note "The agenda just made its first choice"
    Until this existed, taking the next task was `whatever's at the front` —
    round-robin, no content, no decision. This is the **first selection the
    agenda has ever made**, which makes it the same seam where any future
    triage — urgency, priority, deadlines — would go.

    Worth knowing before a second reason to open it turns up.

## The procedure installs its own timer

Now the version that matters. Whoever called `cook_pasta` doesn't know about the
ten minutes. **The recipe** knows about the ten minutes.

```
fn cook_pasta(p: pot) -> pot:
    SET F(p) "cooking" true
    NATIVE R(t) "after" 600 "take_the_pasta_off" F(p)
```

One line. *In ten minutes, run this, on this pot.* And it's an ordinary line in
an ordinary rule body — the recipe schedules its own follow-up, which is what
recipes in the real world do.

```
cooking now       : True
pending task      : take_the_pasta_off
gate is           : 600 seconds out
why               : waiting on a timer

...ten minutes later:
cooking           : False
```

Note `NATIVE` — Chapter 20's escape hatch for primitives the instruction set
doesn't itself contain. Reaching the agenda is machinery, not business, so it
belongs on the far side of that table.

## The bug worth ending the book on

Building this uncovered something small and perfect, and it's a fitting last
example because it's the same species as half the others.

A running rule body needs to answer *"which loop am I on?"* — otherwise it has
nowhere to schedule its follow-up. The obvious answer: follow the agenda's edge
backwards. Every task on the agenda has one.

Every task except the one that's currently running.

Because that edge was doing two jobs at once. It was the **turn order** — and a
tick takes the task off the front *before* advancing it, precisely so it can put
it back at the tail afterwards. So a running task is not on the agenda at all,
which is exactly when it asks.

The first version refused every single call with *"you are not on an agenda"* —
which was, at least, the honest failure the guard was written for.

The fix is to notice that these are two different facts:

| fact | how stable |
|---|---|
| whose turn is next | changes every tick, by design |
| which loop this task belongs to | doesn't change at all |

They now ride on two edges. And a body that genuinely isn't on any agenda is
still refused, because a timer installed nowhere can never fire — and would look
exactly like one that's merely early.

That's the whole book in miniature: two facts sharing one arrow, working
perfectly until the day something asked one of them at the wrong moment.

---

## That's the book

Where you've been:

- **Part 1** — a world of nodes and named arrows, both of which you can point
  at; shapes rather than badges; and a rule that runs only when you point it at
  something.
- **Part 2** — wanting things, imagining them, finding routes, and explaining
  what happened without inventing what didn't.
- **Part 3** — reality disagreeing, models that anticipate rather than assume,
  contingencies, hard limits, memory, learning, and noticing its own intentions
  colliding.
- **Part 4** — telling it how to work: advice it may ignore, recipes that replace
  the search, procedures it may not work around, and breaking off mid-plan to go
  and find something out.
- **Part 5** — the instructions underneath, the line between machinery and
  decisions, and the two readings of a rule's body that make planning and safety
  possible.
- **Part 6** — what it saw and who changed it, every loop as an ordinary task, a
  rule that judges a computation while it runs, forgetting as the default, and
  questions with a gap in them.
- **Part 7** — moments that point at what they date, a conversation with more
  than one person in it, prohibitions that can be overruled by someone with
  standing, and waiting without spinning.

The thread running through all of it is one property. **Everything is made of the
same stuff.** Rules, goals, plans, memories, explanations, conflicts, half-run
programs, moments, utterances, prohibitions — all ordinary data in one graph.
Every capability in Parts 2 to 7 is a consequence: the machine can plan because
it can read its rules, explain because its reasoning is an object, learn because
it can write a rule, refuse to reason with a dangerous rule because it can
inspect one before running it, stop itself thinking too long because a running
computation is a thing in its world like any other — and arbitrate between two
people's instructions because *who said so* is a node, the same as everything
else.

None of those needed a subsystem. They needed the same substrate, asked a
different question.

[Back to the start :octicons-arrow-left-24:](../index.md){ .md-button }
