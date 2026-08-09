# Memory and time

The machine remembers what it did, what it saw, when it happened, and what was said to it — all as
ordinary graph data, so a rule can walk any of it. It also forgets, deliberately and by default,
because most of what a running system accumulates is scaffolding it can rebuild.

## The thread — short-term memory, materialised

A focus is a Python object holding no graph state, created fresh per call and discarded. So attention
was the one thing in this system that was not homoiconic, which is a strange hole in a project whose
claim is that a rule can reason about a rule. A system that cannot reason about where it has been
looking cannot explain itself, cannot notice that it is going in circles, and cannot learn from how
it moved. The thread is that record.

```
thread session (4 entries)
  0. attend root [start]
  1. attend chunk#20 [the car]  (user mentioned it)
  2. applied service  (it needed servicing)
  3. attend wheel#22  (checking the tyres)
```

**A thread is an episode, extended — not a second log.** An episode already mints a node per
application on an ordered `step` edge; a parallel record would mean two accounts of one event and
every reflective rule consulting both. So an application entry *is* the application node, and
`application.steps` filters back to applications, leaving episode compilation unaffected.

**Two entry kinds only** — a deliberate attention shift, and an application. Not every instruction:
head movement runs inside every rule body, and logging that would record pointer arithmetic rather
than reasoning. Nothing instruments the focus, on purpose.

**Order lives in the ordered `step` edge; `prev` carries navigation and the reason.** Stepping back
is a single hop rather than an index lookup, and *why* one step followed another is a property of the
transition, so it rides on the `prev` edge as an edge property. Walking forward is a reverse-index
query, so only one direction is stored, and the two views cannot disagree because exactly one
function appends.

An edge property cannot be pointed at, which sets a general rule: **ride on the edge what merely
describes it; mint a node for what must be pointed at.** That is why connecting two distant moments
mints a `connection` node — a hypothesis may dispute it.

**The thread does not hang off `root`.** Real things hang off root, which is what makes enumeration
by traversal safe and what separates the world from the scaffolding. Memory points *at* the world and
is never pointed at by it.

Walking the thread needs no new primitive. `prev` and `at` are ordinary edges, so a thread-walker is
an ordinary rule pointed at the thread — including one loaded from stored instruction text and run on
the ordinary machine.

The thread answers the questions that make an agent coherent over time: what did I just do, why did
this follow that, when did I last touch this node, and what did I see before I looked away.

## What was seen, and whether it was me

The graph holds the world as currently believed. That alone cannot answer "what was true before?".

The obvious place to look for the answer is the undo journal, and it is the wrong place. The journal
held the inverse of every mutation — hundreds after a single two-step plan — as Python closures the
system could not read, last-in-first-out only, and cleared outright when an effect was committed. So
the past was computed, unreadable, and then destroyed. Committing is right and stays: it answers *can
I reverse this?*, and once an email has left you cannot. What it should never have answered is *can I
remember what preceded it?*

More decisively, a journal delta records only the agent's **own** writes. The external world moves on
its own, so a log of what the agent did can never account for what it later finds. Observation has to
be recorded where the world is actually consulted.

So an **observation** — a sighting — is recorded at the dispatch boundary, before anything leaves: a
node, a slot, the value seen, and the moment. From that sequence three things are derivable rather
than stored:

* **what is believed** about a slot — the most recent sighting.
* **transitions** — that a slot changed between two sightings.
* **attribution** — whether the agent's own action falls between the two sightings, which is what
  distinguishes *I did that* from *that changed under me*.

**Volatility** is the summary: how often a slot was observed to change, and how much of that change
was unattributed. A world that moves under the agent scores high; a slot only the agent touches
scores zero. That gives sensing something to aim at.

Encoding and retention have opposite defaults, and keeping them apart is what makes this safe. A
sighting encodes only the slots of *the thing being looked at* — everything else the tool happened to
touch is the walk to school, and not encoding it is the correct outcome rather than a loss.

## Time

Time is a **node that points at what it dates**, never a label on the thing dated. Three consequences
follow, and they are why the direction is right rather than merely conventional.

**One look dates many facts.** An observation touches every slot of what was looked at, so the
natural cardinality is one moment pointing at many dated things.

**A business rule never calls the clock.** Dispatch mints the moment; a rule author does nothing.

**One action is one moment, covering what the action produced.** Listing a folder records sightings
*and* mints file nodes, and all of them share the single moment of that action. A product with its
own moment would be a second action, which is exactly the per-node timestamping this design rejects.

The obvious generalisation — date everything that gets minted — is wrong, and measurement says so. A
node minted by a rule body carries no moment and should not:

```
world arrival   (dispatch)  ->  temporal provenance:  a moment dates it
internal mint   (rule body) ->  causal   provenance:  the activation names what made it
```

Those are different answers to different questions at different points. The rule is *everything
observed or acted upon*, and a derived node is neither.

Given moments, ordering is ordinary: which followed which, what an interval spans, and where a thing
sits in the temporal order. That is what the `when` question reads.

### Time as a woven concern

Timestamping is not written by rule authors; it is woven at the boundary where actions happen.
Transaction management is woven the same way, at four hand-placed sites: one program run, one
authored block, the block seal, and the commit before an effect leaves.

There is deliberately no general aspect mechanism yet. The two concerns weave at different join
points — an *action* crossing the world boundary versus a *program or block* beginning and ending —
and a generic mechanism would have to invent a join-point vocabulary, which is a design rather than a
refactor. When it comes, its shape is already known: a table the kernel consults at a boundary and
does not populate. What must not happen is a kernel that knows what a timestamp is.

## Discourse — what was said, and what was taken back

Reading an authored block builds a goal, a criterion, a method — and, before this existed, recorded
nothing about the fact that somebody said it. So the system could hold what it had been told and
could not point at the *telling*.

**An utterance is in the world; the thread merely attends it.** It is a world object with a
**speaker who is a node**, not a string, and it points at what it authored. Identifying a speaker by
name alone is harmless with one actor and wrong the moment there are three.

From that, three capabilities follow with no further machinery:

* **Retraction.** Taking something back marks the authored node as withdrawn rather than deleting it.
  Enumerators skip withdrawn nodes, so the outcome really changes; history survives, because the
  utterance is still there; and the retraction is itself on the record. Retracting nothing, or
  retracting the same thing twice, is refused.
* **Authority.** Who may withdraw whose utterance is a question about nodes, so it has an answer.
* **Questions in conversation.** Something asked and not yet answered is a pending item that can be
  enumerated.

## Forgetting is the default

Remembering is the exception: the result of a tool call, something that surprises us, live work. Not
ordinary things.

This is not a reversal of the retention rule for observations. That rule was about **sightings**, and
it is untouched — an observation is the result of a tool call, and every one is kept. What it never
considered is the thing an interruptible engine creates: **its own computational scaffolding**.
Measured on a three-block world, three ordinary goals grow the graph from 80 nodes to 892, of which
about three quarters is scaffolding — searches, candidates, trace steps, frames, mappings, replays,
bindings, activations, registers.

So the rule generalises rather than reverses:

> **Keep what you cannot re-derive.** The world, the library, intent, the result of a tool call, a
> surprise, and live work.

Everything else is swept. Forgetting runs on a slower clock than the outer loop, one record per tick,
so it interleaves like any other task rather than stopping the world. On the measured case it took
the graph from 892 nodes to 238 with every answer unchanged.

Compaction is itself expressed as a rule rather than as a mechanism, which is what makes the policy
readable and arguable instead of compiled in.
