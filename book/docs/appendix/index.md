# Appendix — concepts, in plain language

The book teaches each idea when you first need it. This appendix is for when you
want a little *more* on a concept, or you jumped straight here. Each entry is
short, plain, and points back into the book.

---

## What is a graph?

A **graph** is a collection of **dots** connected by **arrows**. The dots are
**nodes**; the connections are **edges**.

You already know dozens of graphs:

- A **subway map** — stations are nodes, tracks are edges.
- A **friend network** — people are nodes, "is friends with" is an edge.
- A **family tree** — people are nodes, "is a parent of" is an edge.

This machine lives in a graph where **every arrow has a name**, and arrows
sharing a name are kept **in order**. That second part sounds like a
technicality; it means a one-to-many relationship is also a list, so "the second
one" is a question you can ask.

→ [Chapter 1](../basic/01-the-substrate.md)

---

## Node, edge, attribute, reference

- **Node** — a thing. Everything is one: a crate, a rule, a goal, a memory.
- **Edge** — a named, ordered arrow between two nodes. An edge is a *claim*.
- **Attribute** — a value on a node that isn't a relationship: `height: 3`.
- **Reference** — a stored pointer to a node, held as an attribute value. Unlike
  an edge, it asserts nothing. A bookmark, not a claim.

→ [Chapter 1](../basic/01-the-substrate.md)

---

## Type — a shape, not a badge

A **type** describes a *shape*: which arrows a node must have, how many, and
what attribute values. Nothing is ever tagged. Asking "is this a car?" re-checks
the node's structure, every time.

Two things fall out for free: a thing can satisfy several shapes at once, and it
stops satisfying one the moment its structure changes — with nothing to
invalidate, because nothing was stored.

→ [Chapter 2](../basic/02-facts.md), [Chapter 21](../deep/21-types-as-shapes.md)

---

## Cast

Because a type is a shape, **changing a thing's type is just changing its
shape**. A rule promising `car → serviced_car` is a **cast**, and whatever it
alters along the way is merely how the cast is achieved.

Nothing records that a change happened. A node satisfies the stronger shape or
it doesn't — checkable now, rather than a claim about the past.

→ [Chapter 21](../deep/21-types-as-shapes.md)

---

## Pointing (and why nothing "fires")

In many reasoning systems a rule **fires** wherever the world matches it. Here a
rule is a function with parameters: it runs when something **points** it at
specific arguments, and never otherwise.

The trade: you lose automatic cascades, and you gain a rule that cannot surprise
you, cannot run twice by accident, and cannot interact with a rule written by
someone who never heard of it.

→ [Chapter 4](../basic/04-rules.md)

---

## Goal, and constraint

A **goal** is a set of **constraints** — things that must be true. Each is an
ordinary node, and keeping them separate is what makes planning possible: a goal
that can only say *yes/no* leaves a searcher nothing to aim at, while one that
names **which** constraints are still false lets it work backwards from what's
actually missing.

→ [Chapter 5](../intermediate/05-wanting-something.md)

---

## Safety and liveness

Two kinds of limit on *how* a goal may be reached, handled oppositely:

- **Safety** (`never unstack`, `at most 3 steps`) — once broken, no continuation
  repairs it. A breach is a **proof** the branch is dead, so it prunes, before
  the step is even imagined.
- **Liveness** (`must paint`) — a plan that hasn't done it yet is unfinished,
  not in violation. Checked only at the end; it must never prune.

Get these backwards and planning fails in both directions.

→ [Chapter 5](../intermediate/05-wanting-something.md),
[Chapter 12](../advanced/12-what-it-may-never-do.md)

---

## Workbench and frame

A **workbench** is a private copy of the world where the machine tries things
out. A **frame** is a snapshot after each imagined step — which is what lets it
answer "what was supposed to be true at step two?", the question that matters
when step two surprises it.

Nothing is committed by imagining.

→ [Chapter 6](../intermediate/06-imagining.md)

---

## Rank a guess; prune a proof

The rule that keeps hard problems solvable.

**Relevance** — how likely a move is to help — is a *guess*, so it only ever
changes the **order** moves are tried. Filtering on it would lose solutions:
some puzzles require taking something apart first, and that move scores badly by
any measure of relevance.

A **safety breach** is a *proof*, so pruning on it is sound.

→ [Chapter 7](../intermediate/07-finding-a-plan.md)

---

## The plan is found, not built

The machine searches by imagining, and every frame records the step that reached
it. So the path from the start to a frame satisfying the goal **already is** the
plan. There's no plan-assembly step.

Which is also why an answer arrives with its justification: the route *is* the
explanation.

→ [Chapter 7](../intermediate/07-finding-a-plan.md),
[Chapter 8](../intermediate/08-because.md)

---

## Yes, no, and unknown

Three answers, and the third isn't a failure:

- **yes** — a route was found;
- **no** — something incompatible holds *now*;
- **unknown** — nothing settles it either way.

A failed search has learned about the machine's own library, not about the
world. Treating "not found" as "false" is how a reasoner starts lying.

→ [Chapter 3](../basic/03-questions.md)

---

## Closed world vs. open world

**Open world** (the default): what isn't known isn't thereby false. **Closed
world**: assume the record is complete, so unproven means false.

Closing the world is a **stance** you choose per question, not something baked
into the machinery — and when the machine leans on it, it says so in the answer.

→ [Chapter 3](../basic/03-questions.md)

---

## Expectation

What a step *should* produce, **derived** from the two frames the machine already
imagined — never authored, never stored.

Expectations are **qualitative, never quantitative**: an assumption that produced
two files is offering a *witness, not a promise*. The expectation is that *some*
file appears. One is fine, five are fine; **zero** diverges.

→ [Chapter 10](../advanced/10-when-reality-disagrees.md)

---

## Divergence, contingency, replanning

**Divergence** — reality didn't match what a step promised. The machine stops
there and reports which step and how.

**Contingency** — if the plan forked earlier, a branch that assumed *what
actually happened* may already exist, imagined and checked. Continuing down it
isn't replanning at all.

**Replanning** — if nothing fits, pursue the goal again from the world as it now
stands. Note that it goes back to the **goal**, not to a shape-chaining planner,
which knows nothing about what you wanted.

→ [Chapter 11](../advanced/11-contingencies.md)

---

## The thread

The machine's short-term memory, as ordinary graph data: what it attended to and
what it applied, in order, each entry carrying *why* it followed the one before.

It records what was **considered** as well as what was **done**, and a reader has
to know which it wants — explaining why something is true uses only what was
really done, or it would answer with roads not taken.

→ [Chapter 13](../advanced/13-remembering.md)

---

## Episode, and learning

An **episode** is a sequence of applications. Compiling one produces a new rule
that replays it on a fresh subject — stored identically to an authored rule, and
indistinguishable from one.

There's no learning subsystem. Writing a rule is writing nodes and edges, which
every rule can already do.

→ [Chapter 14](../advanced/14-learning.md)

---

## Interference

Two independently authored rules, brought together by a library that grew,
writing the same thing for unrelated reasons. Both correct; the combination is
what nobody intended.

Distinguished from a **deliberate sequel** — two writes serving the *same* goal —
which is just what doing things in order looks like. Without that distinction
the detector reports everything and becomes noise.

→ [Chapter 15](../advanced/15-collisions.md)

---

## The five words

The search consults a decision once per imagined step, and the answer is one of
five: **expand** (imagine the best move — the default), **decompose** (raise
subgoals instead), **commit** (stop planning, act on what we have), **sense**
(stop planning and act in order to *find out*), **refuse** (there's no
sanctioned way, don't improvise).

Closed on purpose: it's the vocabulary everything authored has to speak, and a
vocabulary nobody can enumerate is one nobody can check.

→ [Chapter 16](../deliberation/16-choosing-what-to-do-next.md)

---

## Guideline

Authored preference — `prefer` and `avoid`. The weakest kind of knowledge here
and the only one that cannot cause harm: a guideline **reorders candidate moves
inside a relevance band** and does nothing else.

**`avoid` means later, never never.** The word that means never is `never`, and
it prunes because it's a proof. Advice is a guess.

→ [Chapter 17](../deliberation/17-advice-it-may-ignore.md)

---

## Method, procedure, and force

Both are authored decompositions: *for a goal of this shape, raise these
subgoals in this order.* They can be written identically, and what separates
them is **force** — what happens when a step doesn't work out.

- **method** (advisory) — fall back to searching.
- **procedure** (mandatory) — **refuse**, and don't look for another route.

Force is about failure, not strength, and it can't be inferred from the content,
so it has to be declared.

Both prune on **authority** rather than on evidence or proof, which is a third
kind of justification and the only one that can make a reachable goal
unreachable.

→ [Chapter 18](../deliberation/18-recipes-and-rules.md)

---

## Subgoal

A goal inside a goal. The child points at the parent, so *"am I inside a
procedure?"* is a short walk up a chain — the question a decision actually asks.

A cycle is impossible (a goal's parent is fixed when it's created), but **depth
isn't bounded**: a recipe that raises a goal matching the same recipe recurses
happily forever. That's open.

→ [Chapter 18](../deliberation/18-recipes-and-rules.md)

---

## Not there, versus not looked

An absent attribute means *hasn't got one*. A slot explicitly marked `UNKNOWN`
means *nobody has looked* — present, but not a value, and false to anything that
tests it.

So a condition can be unmet for two different reasons, and only the second is a
reason to go and look:

- **false** → find an action that makes it true;
- **unknown** → find an action that would reveal it.

The machine senses only when the plan **bottoms out** in ignorance, never when
it merely touches it.

→ [Chapter 19](../deliberation/19-not-knowing.md)

---

## Dispatch — the one door

Every effect on the world goes through a single place. That's what makes one
check cover every tool that will ever be registered.

Two rules: check when the action is about to happen (not when it's planned, so a
prohibition recorded afterwards still works), and commit the graph before going
through (because once an effect leaves, no rollback reaches it).

→ [Chapter 12](../advanced/12-what-it-may-never-do.md)

---

## Purity — what may be used to think

A rule may be used to answer a question only if it **provably never reaches
outside**, read off its stored instructions. If the machine can't tell, the
answer is no.

Deliberately conservative in the opposite direction from effect-reading, because
the costs differ: overstating what a rule *might do* wastes a step; understating
what it *could reach* sends an email you can't unsend.

→ [Chapter 23](../deep/23-concluding-vs-acting.md)

---

## The instruction set

A small, fixed vocabulary every rule body is made of: read, write, move, branch,
call another rule, and exactly one instruction that reaches outside.

Operands are literals, **registers** (local scratch), or **heads** — the things
the rule was pointed at. A rule gets fresh heads holding only its own arguments,
never its caller's.

→ [Chapter 20](../deep/20-instruction-set.md)

---

## Reading a rule's effects

What a rule could make true, read **off its stored instructions** — never
declared, so it can't drift from the body, because it *is* the body.

Effects carry **roles**, and a role can be a path: a rule that navigates to part
of its argument and writes there reports an effect on `c.right`, not on nothing.
The path is resolved late, against real arguments.

The result is an **over-approximation by contract** — safe for ordering
candidates, unsafe for concluding that a rule definitely does something.

→ [Chapter 22](../deep/22-reading-a-rule.md)

---

## Belief, and sighting

A **belief** is what the machine currently holds to be true — `count: 3` — and is
what everything reasons over. A **sighting** is what was actually *seen*, and
when.

Keeping them apart is what lets a belief be recognised as **stale** rather than
silently trusted. Something never looked at has no sighting at all — not a
cautious one.

→ [Chapter 24](../watching/24-what-it-saw.md)

---

## Attribution — "was it me?"

Given two sightings that differ, deciding whether the machine's own actions
account for the change or the world moved on its own.

It is **derived**, never logged: a journal of the machine's writes would miss
every external change (nothing happens in the graph when a file appears) and
would misreport the machine's own *look* as a change it made.

→ [Chapter 24](../watching/24-what-it-saw.md)

---

## Volatility

How often a slot changed in ways the machine could **not** attribute to itself.

It gives *go and look* a second trigger beside ignorance: not only *I don't
know*, but **I do know, and it's probably stale.**

→ [Chapter 24](../watching/24-what-it-saw.md)

---

## Agenda, tick, and task

An **agenda** is an ordered list of work. A **tick** advances the task at the
front by exactly **one primitive step** and moves it to the back.

A running program, a search, a plan being carried out, and a goal being pursued
are all tasks, all steppable the same way. Interleaving isn't a policy — it's
what falls out of rotating an ordered list.

→ [Chapter 25](../watching/25-one-loop.md)

---

## Look versus act

Whether the next step is reversible. `imagine` and `look` cost time; **`act`**
cannot be taken back.

A tool declares which it is, and anything that doesn't declare is assumed to
**act** — being wrong that way costs a pause, and being wrong the other way
spends an action somebody meant to withhold.

→ [Chapter 25](../watching/25-one-loop.md)

---

## Keep what you cannot re-derive

The forgetting rule. Two kinds of record are irreducible — **a crossing of the
world** (a tool call's result) and **a surprise** (a change nothing the machine
did explains). Everything else can be worked out again from the goal and the
library.

Implemented by naming what to **keep** rather than what to drop, so it can't
drift as new kinds of record appear.

→ [Chapter 27](../watching/27-forgetting.md)

---

## Superseded — compaction

Dropping a record that a **better** record already makes. Once a goal is closed
by something real, its pointer into the imagined version of events is a snapshot
of a world that no longer exists.

A goal that was planned and *not* carried out is the opposite case: its imagined
frame is the only account it has, and removing it would be forgetting the plan.

→ [Chapter 27](../watching/27-forgetting.md)

---

## Reach — `contains+`

*Is X reachable from Y by following this arrow, at any depth?* The one genuine
gap this project found in its own vocabulary — a parcel in a box in a warehouse
*is* in the warehouse, and nothing could previously say so.

Deliberately a **question only**: as a way of *naming* something it would denote
a set, and every name in this machine promises one node or nothing.

→ [Chapter 28](../watching/28-what-where-when.md)

---

## Reader — what, where, when

A question with a **gap** in it, answered by locating a thing in an order the
world already has, rather than by searching.

A reader **records nothing**, because its answer is one traversal away at any
moment and a stored one could only drift. What reaches memory is the *question*.

→ [Chapter 28](../watching/28-what-where-when.md)

---

## Moment

A point in time, held as a **node that points at what it dates** — never as a
stamp written onto the thing dated. One look dates many facts, dating disturbs
nothing, and a moment may carry no clock reading at all and be placed only by
what it comes after.

One action is one moment, and that covers what the action *produced*.

→ [Chapter 29](../world/29-when-things-happened.md)

---

## Utterance

The fact that somebody **said** something, as a thing in the world. Its speaker
is a node, not a name, and it points at whatever it authored — so it can be
attributed, withdrawn, or answered.

Withdrawing marks the authored block rather than deleting it: the outcome
changes, the history survives, and the retraction is itself on the record.

→ [Chapter 30](../world/30-who-said-it.md)

---

## Norm

A prohibition or permission about one action, attributed to a **source**, which
can be defeated by a source that outranks it — or declared *inviolable*, which
puts it outside the ranking rather than at the top of it.

Settled before planning starts, and written into the goal as ordinary `never`
constraints, so nothing downstream knows norms exist.

→ [Chapter 31](../world/31-overruled.md)

---

## Timer

A moment on a task, saying when it may first run. The agenda **waits and says
so** rather than rotating the task and retrying, because busy-looping looks
exactly like progress.

→ [Chapter 32](../world/32-waiting.md)

---

*This appendix grows with the book. The project lives on
[GitHub](https://github.com/ercasta/Universal-Graph-Machine).*
