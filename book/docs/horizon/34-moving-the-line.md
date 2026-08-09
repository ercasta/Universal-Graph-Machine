# Moving the line

*The machine is currently taking its own planning away from Python, one piece at
a time. This is what that looks like from the inside.*

Chapter 33 said the horizon is a decision. This chapter is about the machine
acting on it — and it is the most honest chapter in the book, because the work
is unfinished and the numbers are not all flattering.

## Why the workbench, of all things

[Chapter 6](../intermediate/06-imagining.md) introduced the workbench: the place
the machine imagines a change before making it. It was written in Python.

Nobody minded for a long time, and then somebody asked the question this book
keeps asking: *can the machine inspect it?* No. *Can the machine change how it
plans?* No. Planning was the one activity the machine could not reason about,
which is precisely backwards for a machine whose whole claim is that it reasons
about its own work.

> **Planning that Python owns is planning the system cannot inspect or change.**

So the workbench had to come up above the horizon. Everything that follows is
consequences of that one sentence.

## Decompose before believing something is primitive

The first move was a list of things that "obviously" had to stay primitive, to
be exposed as named hooks the way [Chapter 20](../deep/20-instruction-set.md)'s
`NATIVE` exposes the planner. Six of them.

Then somebody tried to decompose them anyway. **Four of the six turned out to be
plain arrow-reads.** Not "roughly equivalent to" — actually just reading arrows,
in a language that already read arrows perfectly well.

Opening a workbench, the one that looked most obviously primitive, turned out to
be three loops and a copy. What had genuinely been blocking it was a single
missing question. Every way of reading the graph took a name you had **already
decided on**: *give me the `height` of this*, *give me what it `supports`*. There
was no way to ask *what names does this thing even have?*

That asymmetry — you can read any slot you can name, and you cannot ask which
slots are there — is why the copy could not be written. Five small additions to
the substrate closed it (*what kind is this? how many names? give me the nth
one?*), and opening a workbench became an ordinary authored program.

The lesson generalised into a rule the project now applies before anything else:

> **A thing is primitive only after you have tried to decompose it and named
> what was missing.**

Applied to the audit in Chapter 33, it shrank every single estimate. Applied
here, it converted six proposed primitives into five substrate additions and two
arrow-reads.

!!! note "Test the claim before building the fix for it"
    Three times during this work, something was "missing" and already worked.
    The sharpest: calling a function whose *name is decided at run time* was
    assumed impossible and was written down as needing a new instruction. It had
    always worked. Trying it took a minute; the instruction nobody needed would
    have been permanent.

## Where a rule is allowed to stop

The second constraint is subtler, and it is about how far down authored work is
allowed to be translated.

When an authored rule is turned into something runnable, the translation could
bottom out at an **instruction** — fast, direct, final. It doesn't. It stops one
level higher, at a **named call**.

Two reasons, and both are about meaning rather than speed:

- **A name is where meaning lives.** What calls what *is* the machine's semantic
  network. Translate a read straight into an instruction and that read vanishes
  from the network; it is no longer a thing anything can reason about.
- **A name is resolved when it runs.** So the machine can change what a read
  *means* — what world it reads from, whether it is being imagined or done for
  real — without editing a single rule.

Put the two constraints together. The workbench can't be in Python. Reads can't
be raw instructions. What is left is that reads go through **rules in the graph**,
which is where this arc ended up.

## Eight names

A rule never touches the graph directly. It reaches it through **eight** names —
read a slot, set a slot, ask about a relation, list relations, take the nth one,
relate, unrelate, make something new — and every richer vocabulary a domain
writes (*the supports of this*, *the wheels of that*) is written in terms of
those eight.

Why exactly eight, and why closed? Because of **totality**. The whole scheme only
works if *every* access can be intercepted: one unmediated read while the machine
is imagining, and it is planning against a half-modified world and doesn't know
it. And you cannot get "every one" out of an open-ended set — there is always one
more.

So mediation has to bottom out in a closed set. Which is Chapter 33's three-layer
shape all over again, arrived at from a completely different direction: not *what
can't be defined away?* but *what may not be Python?* Two different questions,
same cut. That is about as much evidence as you get that a line is in the right
place.

## What it bought: cost that follows change

The payoff arrived with a change to how imagined worlds are stored, and it rests
on one sentence:

> **An arrow names an identity, never a version.**

Before, imagining a step **copied the world** so the copy could be scribbled on.
That is fine for five things and hopeless for three hundred. Now a step copies
nothing: it records only what it *changed*, and reading walks back through the
chain of changes until it finds an answer.

| world size | copying the world | recording only changes |
|---|---|---|
| 5 things | 47 ms | 53 ms |
| 60 things | 68 ms | 56 ms |
| 300 things | 198 ms | **59 ms** |

**The curve is the result, not any single row.** Cost now follows how much
changed, not how big the world is. And note the top row honestly: on a tiny
world the new way is *slower*, because copying four things in Python was cheaper
than the more careful machinery. Quoting either row on its own misrepresents the
change.

## The bill, stated plainly

Moving work above the horizon costs speed. There is no version of this where it
doesn't, and the project's own notes keep the numbers rather than the adjectives:

| | |
|---|---|
| a mediated read vs a raw instruction | **3.8×** |
| the workbench step, authored vs Python | **3.0×** — it was 22–42× before sparse frames |
| a full plan for the puzzle in Chapter 7 | **1020 ms**, against 640 ms before |

The last row is the uncomfortable one, and it is uncomfortable in an instructive
way: it is a small world, where copying was the right answer, now paying for
machinery that wins on large ones. The right response is not to explain it away.
It is to write it down, notice that it is where a faster interpreter would show
up, and carry on.

There is also a distinction the project keeps insisting on:

> **Expressible is not the same as rewritten.**

And a sharper version of the same discipline. Three pieces of the workbench now
exist **twice** — once in Python, once written above the horizon, checked
against each other and agreeing. The Python ones are still the ones that run.
That is not a failure; it is the measurement not having been made yet, and the
gap is recorded as a gap rather than quietly rounded up to *done*. Letting the
two blur is how a plan turns into a claim.

## The guard that stopped firing

One last story, because it is the same species as every other failure in this
book and it happened *during* this work.

[Chapter 12](../advanced/12-what-it-may-never-do.md) established that imagining
must never reach the world. That was enforced by checking the target: *is this
thing a workbench copy? then refuse.* It worked, and every test agreed it worked.

Then imagined rules stopped being handed copies, and started being bound to the
real things instead — the identity rule above. Which means the target of an
action inside a plan is now **the real node**. The guard asked its question, got
*no, that's a real node*, and allowed it. Silently. A plan **actually listed a
directory** on somebody's disk.

Nothing was wrong with the guard's logic. It had never been asking the right
question. *Can this reach the world?* was never a fact about the **thing being
touched** — it is a fact about **what the machine is doing right now**. Am I
imagining? The new guard asks that, and nothing about the target could ever have
told it.

Worth generalising, because it is the most expensive shape in this book:

> A check that tests a **value** for a fact about the **context** is right by
> coincidence — until the day it isn't. And it fails silently, because a check
> that has stopped firing looks exactly like a check with nothing to complain
> about.

Both tests are kept. They catch different mistakes.

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
- **Part 8** — the second line: what is *not* data and why, the three answers to
  "it can't say that", and the machine currently hauling its own planning up
  across that line.

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

And Part 8 is that property being taken seriously about the one place it had
been quietly excused: the machine's own thinking.

[Back to the start :octicons-arrow-left-24:](../index.md){ .md-button }
