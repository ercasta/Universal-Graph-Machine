# The agent in its own graph

A design for the execution model: how the system represents itself, how its processes are represented,
what causes a process to start, and how it answers questions about what it is doing.

This is a design document. [execution-model.md](execution-model.md) describes what runs today; nothing
here is built. It is written throughout in the representation the
[facts-as-nodes.md](facts-as-nodes.md) arc is converting to, because the argument does not survive
translation into the current one.

## Contents

1. [The requirement](#1-the-requirement)
2. [The representation](#2-the-representation)
3. [The self](#3-the-self)
4. [Indexicals](#4-indexicals)
5. [Processes and doings](#5-processes-and-doings)
6. [When a doing holds](#6-when-a-doing-holds)
7. [Phases become derived readings](#7-phases-become-derived-readings)
8. [What triggers what](#8-what-triggers-what)
9. [Turn order on the agenda](#9-turn-order-on-the-agenda)
10. [Reading the scheduler without driving it](#10-reading-the-scheduler-without-driving-it)
11. [Answers](#11-answers)
12. [Worked example: "what are you doing?"](#12-worked-example-what-are-you-doing)
13. [What must be built](#13-what-must-be-built)
14. [Open questions and risks](#14-open-questions-and-risks)
15. [Relation to the rest of the plan](#15-relation-to-the-rest-of-the-plan)

---

## 1. The requirement

The requirement, as stated:

> The agent needs a representation of itself within the graph, otherwise "I" and "you" are meaningless.

The capability it has to buy is small enough to test: the user asks *"what are you doing?"* and the
system answers *"I am planning"* — by reading the graph, not by calling a Python function that knows
about itself.

The design commits to a stronger form than that capability strictly needs, because the weaker form is
not worth building:

> There is no self-inspection mechanism.

*"What are you doing?"* is a question about the world, where the world happens to contain the asker's
interlocutor. It goes through the machinery that answers *"why is the block on the table?"*. If it needs
a path of its own, the design has failed. This is the reflection thesis's own claim
([reflection.md](reflection.md)): if the planner is rules, *"why did I plan it this way?"* is answered by
the machinery that already answers *"why is the block on the table?"*, so there is one mechanism rather
than two.

Two things the design does not claim. It does not ground references — that *"the block"* denotes a
particular node remains the hard problem, and it is untouched here. And it does not make the system
correct about itself; it makes the system able to say what it is doing and on what basis.

---

## 2. The representation

Everything below obeys one shape, and every example is checkable against it.

### 2.1 The shape

`a on b` is three nodes: `on`, pointing at `a` and `b`. The relation node is the thing; its ordered
edges are its members.

```
on(a, b)                  the `on` node points at a, then b
doing(self, search_1)     the `doing` node points at self, then search_1
agent(self)               the `agent` node points at self — one member, and still the shape
```

There is no property bag anywhere, and no separate node holding the relation.

### 2.2 A concept is not an assertion

`on(a, b)` by itself is a **concept** — the notion of `a` being on `b`. Whether it holds, who says so,
when, and whether they are reliable are separate facts to be reasoned over. So asserting it is a further
node:

```
on(a, b)                  the concept — three nodes, and minting it claims nothing
claimed(on_1, anna)       the assertion — Anna says so
```

This is [facts-as-nodes.md](facts-as-nodes.md)'s *a proposition is not an assertion*, and it is what
makes the rest of this document possible. A doing that has a beginning and an end needs the concept and
the claims about it to be different nodes, or *"I was planning"* and *"I am planning"* cannot both be
representable.

### 2.3 Attributes do not exist

If relations are nodes, the attribute mechanism has no remaining job, and the substrate keeps none.

| what was an attribute | what it is now |
|---|---|
| the kind, set at mint | an ordinary classification fact — `block(a)`, `agent(self)` |
| a scalar's payload (`2`, `1.0`, `"planning"`) | identity by content — a scalar node does not carry `1.0`, it is `1.0` |
| edge properties | gone; they existed only because an edge could not carry a fact |
| everything else — a phase, a stop flag, a step index, a tick count, a label | an ordinary fact |

This matters here rather than being housekeeping. A phase held as an attribute cannot be dated, caused,
questioned or retracted. As a fact it can. *"Since when have you been planning?"*, *"why are you
planning?"* and *"what would make you stop?"* are the same questions asked of the agent that *"when did
this become true?"* asks of a block, and they are unanswerable while the agent's state is a property bag.

A name is a claim for the same reason. `named(self, system)` is a fact rather than a label, because two
independently authored knowledge bases will name one thing differently, and the bridge between them is
an authored fact with a speaker ([harmonization.md](harmonization.md)). A label has nowhere to put the
speaker.

### 2.4 Entities have no outgoing edges, with no exception

Because classification is an ordinary fact rather than a marking on the node, the invariant holds
without a carve-out:

```
agent(self)          the `agent` node points at self
agent(user)          a different `agent` node points at user
```

`self` has no outgoing edges. Nothing composes through it, and *what else is an agent* is a reverse
lookup. The leak this rules out is the shared middle: `a --> on --> b` and `c --> on --> d` sharing one
`on` node really do put `a --> on --> d` in the graph. Here each fact is its own node, so there is no
shared middle to walk through.

### 2.5 What this section does not settle

Two questions are left to [facts-as-nodes.md](facts-as-nodes.md) §*The floor*. How an instance relates
to the relation it instances — §9 and §12 write `ordered(next_form)`, which presumes that can be said.
And what at the floor is not itself a node, since a node's edges to its members cannot each be nodes or
the storage never bottoms out. Nothing below depends on either answer.

---

## 3. The self

```
agent(self)
agent(user)

named(self, system)
named(user, anna)
```

The system is an agent exactly as the user is. Not a new kind, and that is the design decision rather
than an economy. Three things follow, none of which needs machinery:

- **Indexicals become resolvable.** §4.
- **The system's own claims are ranked by the same authority machinery as everyone else's.** The
  discourse layer already ranks speakers. Today the system is a label used only when it asks the user a
  question, so its own assertions sit outside the ordering that governs everyone else's.
- **The system can be the subject of a fact**, which is the thing it cannot be today. Without that,
  nothing it does can be dated, caused, attributed or retracted — the existence / holding / attribution
  split has no attribution for the agent itself.

One self per graph, minted at bootstrap. The scope is session-sized, and an agent that is not one thing
across a session cannot be the referent of "you" twice in a conversation.

---

## 4. Indexicals

An indexical's referent is a function of who is speaking to whom, and the graph records that as soon as
an utterance is a world event with participants:

```
utterance(u1)
said(user, u1)
to(u1, self)
```

Then the whole of it is two sentences:

> `I` denotes the one who said the utterance the word occurs in.
> `you` denotes the one it is `to`.

These are two constructions in the proposal-and-selection sense
([expressiveness-and-uniformity.md](expressiveness-and-uniformity.md)), and the construction skeleton is
already built. No new capability is required: a construction is nodes and edges, and a rule can already
author one.

The symmetry is the test. The same two constructions, applied to an utterance the system said, resolve
`I` to `self` and `you` to `user`, with nothing reversed and no special case. If either direction needs
its own rule, the self is not really an agent among agents and §3 is decoration.

---

## 5. Processes and doings

Two nodes, because they answer two questions.

```
search(s1)                  the process — a thing with a step, on an agenda
doing(self, s1)             the doing — that this agent is engaged in that process
```

The process is what is being run: it has state, it can be advanced, it can finish. The doing is that
this agent is engaged in it, and it is what carries the time, the cause and the ending.

This is the existence / holding / attribution split applied to the agent:

| layer | here |
|---|---|
| existence | `s1` exists, and `doing(self, s1)` is a concept; minting it asserts nothing |
| holding | when the doing began, and whether it has ended — §6 |
| attribution | who says the system is doing it, and why — `caused(u1, doing_1)` |

### 5.1 Why a doing is a fact rather than a property

Scored against the four criteria before deciding, with the cost recorded even though the answer is not
close:

| candidate | not leaking | not lossy | readable | composable |
|---|---|---|---|---|
| a property on the process (`phase = planning`) | yes | no — no time, no cause, no speaker | partly | no — nothing to point at |
| an edge from the self to the process | no — gives the self outgoing edges; `self → s1 → goal_3` composes | no — same | yes | no |
| **a fact, `doing(self, s1)`** | **yes — no entity-to-entity path** | **yes — datable, causable, retractable** | **yes** | **yes — the doing can be a member: `caused(u1, doing_1)`** |

The fact wins on all four. The cost, recorded anyway: one node per process start, and the doing has to
be ended, which §6 shows is the expensive part.

---

## 6. When a doing holds

*"I was planning and now I am not"* must be representable, or the system claims to be doing everything it
has ever done. Two candidates, genuinely different rather than notational.

**Option A — the real world gets a frame chain, and the doing goes absent in a later frame.**

```
frame_k     doing_1 present
frame_k+1   doing_1 absent
```

**Option B — moments bound the doing, and holding is computed.**

```
doing(self, s1)
began(doing_1, m3)
ended(doing_1, m7)
caused(judgement_2, ended_1)      why it stopped
```

| candidate | not leaking | not lossy | readable | composable |
|---|---|---|---|---|
| A — frames over the real world | yes | yes | *what is true now* means walking the chain | yes |
| **B — moments bounding the doing** | **yes** | **yes** | **yes** | **yes — `ended` is a node, so it can be caused and questioned** |

**Option B is recommended**, and the reason is about layering rather than convenience.
[facts-as-nodes.md](facts-as-nodes.md) is explicit that *absent* is the frame mechanism and nothing else
— it is how you delete something a previous frame held, and it is not a claim that something is false. A
doing that has stopped is not a frame-mechanical deletion; it is a fact about the world having a
beginning and an end. Collapsing the two would put a technical device where a temporal claim belongs.

The cost is real and must not be bought back with a cache. *"Are you planning now?"* stops being a
lookup and becomes a computation — has begun, has not ended, at this moment. An index over what was
asserted is storage; a cache of what was derived is a truth-maintenance system, and the arc has declined
that commitment twice.

This lands the design on the matrix's weakest row. Time and aspect is partial in every column and has no
CNL form, and the self-model cannot be honest without it. That is a finding rather than a blocker: it
means the time work has a consumer, which is the condition this project puts on building anything.

---

## 7. Phases become derived readings

Today a pursuit carries a phase — planning, acting, recovering, sensing, checking. Under this design
there is nothing to carry it, and the label is not missed.

```
pursuit(p1)          pursues(p1, goal_3)          doing(self, p1)
search(s1)           serves(s1, p1)               doing(self, s1)
```

A pursuit is *planning* because a search serving it is live. It is *acting* because a replay serving it
is live. The phase is a reading derived from which sub-process is being done, not a stored label.

This also distinguishes two phases the labels could not. Acting and recovering both have a live replay,
so as labels they are two names for one situation plus a flag. As structure they differ in why:

```
replay(r1)     serves(r1, p1)     doing(self, r1)     caused(deviation_1, doing_4)
```

Recovering is acting whose doing was caused by a deviation. So *"why are you doing this?"* answers
itself, where a label had to be asked about separately.

The cost: five attribute comparisons become five derived readings, on a path the loop takes every tick.
Whether that is affordable is a measurement this document does not have, and the precedent cuts both
ways — the goal predicate going interpreted cost 2.35× on the flagship benchmark and was kept
deliberately.

---

## 8. What triggers what

Today the order of work is the agenda, plus timers, plus a Python state machine inside a pursuit. The
state machine is the part that decides what follows what, and it is the part that is not data.

> A trigger is a rule whose condition is over the graph — including over process facts — and whose
> consequent starts a process.

The phase machine then stops being the mechanism and becomes three instances of it:

```
when   a pursuit pursues a goal that does not hold, and no live search serves it
then   start a search serving that pursuit

when   a search serving a pursuit has produced a plan, and no live replay serves it
then   start a replay serving that pursuit, carrying that plan

when   a replay serving a pursuit deviated
then   start a search serving that pursuit, caused by that deviation
```

Three consequences, and the third is what pays for the work:

- **Triggering becomes authorable.** A domain can add *"when the kettle boils, stop waiting"* without a
  module, in the same way a rule can already author a construction.
- **Triggering becomes readable.** A Python `if phase == PLANNING` is an opaque blob; a condition over
  facts is a structure something can ask questions of. This is the content of the reflection arc's B3.
- **Triggering becomes explicable.** *"Why are you planning?"* is answered by the trigger's own
  condition — because this goal does not hold and nothing was planning it. That is the residue applied
  to the agent's own control flow, and it is exactly the sentence the current phase machine cannot
  produce.

---

## 9. Turn order on the agenda

The outer loop is round-robin: take the head, advance it one step, put it back at the tail. That order
is a relation between tasks.

```
next_turn(s1, r2)
ordered(next_turn)
```

It is not any of the orders the arc has already catalogued — `before` on moments, `then` on a goal's
required order, `after` on a plan's actual order, `next` on frames, `next` on tokens, and method steps'
positional order. It is a sixth, and it must not become temporal, exactly as form order must not: *what
runs next* and *what happened before* are different relations.

This matters more than a catalogue entry. The matrix's one wholly blank row is protocol and order over a
sequence, whose worked example is taking turns — and the outer loop is a set of processes taking turns.
The engine contains an instance of the semantics it cannot state, so making the agenda's order sayable
is the same work as making *taking turns* sayable. That is the strongest argument yet that the blank row
belongs on the critical path rather than parked.

---

## 10. Reading the scheduler without driving it

This is a safety boundary rather than an unfinished migration, and the distinction matters because the
reachability pass reports it as a gap. That pass answers *can a rule reach this*; it never asks *should
it*.

| capability | verdict |
|---|---|
| start a process | yes — a running body already reaches its own agenda and schedules onto it |
| read status | yes, and this is the real gap |
| drive, reorder, or force a tick | no, deliberately |

The reason for the third is the most important safety property in the design. A tick reports the verb it
would perform before taking it, so a caller can stop before the first irreversible one: the loop can
decline to take a step, but it cannot make a step reversible. A rule that could force a tick would route
around the only veto point in the system.

Reading means these facts, not a Python interface:

```
doing(self, P)                    what am I doing
began(D, M)   ended(D, M)         since when, and until when
serves(sub, parent)               what is this in service of
caused(X, D)                      why am I doing it
next_turn(T1, T2)                 what runs next
not_before(T, M)                  what is waiting, and on what
would_be(T, act)                  would the next step touch the world
```

`would_be` must stay derived rather than stored, because its whole value is that it is asked before the
step is taken. A stored answer is a cache of a derived value.

---

## 11. Answers

An answer is a node the engine builds; emitting it is a tool call. Not a string returned by a renderer —
a predicate that answers in prose cannot move, and this project has paid for that twice.

```
answer(a1)
about(a1, u1)                     which utterance it answers
reports(a1, doing_2)              each thing it says is a fact, pointed at
reports(a1, doing_1)
```

Each report is a separate fact rather than a member of one, so each can be questioned on its own —
*"why that one?"* picks out a single doing without disturbing the others. A single answer node with a
list of members would make the answer atomic, and an answer nobody can ask a follow-up about is a string
with extra steps.

Emitting it is a dispatch to an `answer` tool, and three consequences follow rather than being added:

- **Answering is an act, not a look.** It reaches outward, and you cannot unsay something. So it lands
  on the irreversible list and the loop can decline to take it, which is correct and did not have to be
  legislated.
- **The system's answers become world events with a speaker**, symmetric with the existing mechanism by
  which it asks the user a question. So *"what did you tell me?"* and *"why did you say that?"* become
  ordinary questions.
- **Rendering is translation at the edge**, which is already the sanctioned practice. The content is
  graph structure; only the last hop is words.

The trap to avoid is building the answer node in Python and immediately stringifying it, which is the
same defect wearing a node. The test is the one used everywhere in this arc: could a rule have produced
this value?

---

## 12. Worked example: "what are you doing?"

The system is already planning. Every line is a node; nothing is a property.

### 12.1 Before the question

```
agent(self)          agent(user)
named(self, system)  named(user, anna)

pursuit(p1)          pursues(p1, goal_3)
search(s1)           serves(s1, p1)

doing(self, p1)      began(doing_1, m2)
doing(self, s1)      began(doing_2, m2)     caused(trigger_1, doing_2)
```

Neither doing has ended, so both hold at any moment after `m2`.

### 12.2 The utterance arrives

Recorded as tokens and nothing else — no parse, no verb — per the skeleton already built.

```
utterance(u1)
said(user, u1)     to(u1, self)     when(said_1, m9)

token_at(u1, 0, w_what)      next_form(w_what, w_are)
token_at(u1, 1, w_are)       next_form(w_are, w_you)
token_at(u1, 2, w_you)       next_form(w_you, w_doing)
token_at(u1, 3, w_doing)

ordered(next_form)
```

`next_form` is form order and must not be `before`. Word order is not time, and one name over two
relations is the defect the label census already caught the engine committing with `next`.

### 12.3 Interpretation

A construction addressed at `w_doing` proposes a question about what its subject is doing. The indexical
construction of §4 resolves `w_you`: the utterance is `to` `self`, so `you` is `self`.

```
reading(r1)          about(r1, u1)      proposes(r1, q1)
question(q1)         asks(q1, doing(self, ?))      subject_of(q1, self)
```

The world disambiguates nothing here, and that is worth saying rather than hiding: this sentence has one
reading. The attachment-ambiguity result belongs to *"put the block on the table"*.

### 12.4 The question starts a process

Asking triggers an answer — a trigger in the §8 sense, whose consequent starts a process:

```
answering(ans1)      answers(ans1, u1)
doing(self, ans1)    began(doing_3, m10)     caused(q1, doing_3)
next_turn(s1, ans1)
```

There is no interrupt, no special path and no privileged status. Answering is a process among processes
and takes one step per tick like the search does, so the system stays interruptible while answering.

### 12.5 The answering process reads the graph

It asks the ordinary question — which doings of `self` hold at `m10`? — and gets three:

```
doing(self, p1)      began m2,  not ended      pursuing goal_3
doing(self, s1)      began m2,  not ended      searching, in service of p1
doing(self, ans1)    began m10, not ended      answering u1
```

The third is the answering process reporting itself. That is not a defect to filter out: *"and answering
your question"* is a true and useful thing to say, and a system that hid it would misrepresent what it
is doing.

It terminates for a structural reason rather than a guard. The agenda advances each task by one step per
tick, so a process that observes processes cannot outrun what it observes, and observing a process mints
nothing — the doing is one node, not a chain. The failure mode to design against is therefore not
infinite regress but infinite reporting, and the single node is what rules that out.

### 12.6 The answer is built and emitted

```
answer(a1)           about(a1, u1)
reports(a1, doing_2)          I am searching for a plan for goal_3
reports(a1, doing_1)          in service of pursuing goal_3
reports(a1, doing_3)          and answering you
```

The answer is a set of pointers into what is already true, not a new description of it. Nothing is
copied, so the answer cannot drift from the state it reports, and every follow-up lands on the same
nodes the answer pointed at.

```
dispatch the answer tool with a1

utterance(u2)
said(self, u2)     to(u2, user)     when(said_2, m11)
renders(u2, a1)
```

The tool renders — *"I'm planning how to achieve goal_3, and answering you."* — and that rendering is
the only place words appear.

### 12.7 What the follow-ups cost

Each of these is the existing question machinery pointed at the nodes above. No new mechanism:

| question | answered by |
|---|---|
| since when? | `began(doing_2, m2)` |
| why are you planning? | `caused(trigger_1, doing_2)`, and the trigger's condition: this goal does not hold and nothing was planning it |
| what for? | `serves(s1, p1)`, `pursues(p1, goal_3)` |
| why did you say that? | `renders(u2, a1)` → `about(a1, u1)` — because you asked |
| are you still doing it? | no `ended` for `doing_2`, so yes |
| stop | assert `ended(doing_2, m12)` and `caused(u3, ended_1)`; the loop declines the next tick |

The last one shows the design working. Today stopping is a flag the loop checks. Here it is an ordinary
assertion by an agent with authority, dated and attributed, so *who stopped me, when, and were they
entitled to?* is answerable — and the discourse layer's existing authority ranking governs it without
being told anything about processes.

---

## 13. What must be built

| item | notes |
|---|---|
| ending a doing | §6. Needs the time and aspect semantics that are partial in every column of the matrix and have no CNL form. The largest item, and the self-model cannot be honest without it |
| the self node | §3. Small, and blocks everything else |
| the addressee of an utterance | §4. The discourse layer records the speaker and not the hearer, so `you` has nothing to resolve against |
| the indexical constructions | §4. No new capability — a rule can author a construction today |
| the answer node and the `answer` tool | §11. The tool must be registered as not observing, so it classifies as an act |
| triggers as data | §8. This is P4's content, re-motivated: not *the phase machine should be in the surface* but *what triggers what must be explicable* |
| the agenda's order, declared | §9, and it is the matrix's blank row wearing engine clothes |
| reading status | §10. Nothing new — the facts are the reading. The gap is that they are properties today, which the conversion closes |

---

## 14. Open questions and risks

1. **The phase machine dissolving into derived readings is unmeasured**, and it sits on the loop's
   hottest path. §7 states the cost and does not price it. The precedent says an interpreted predicate on
   a hot path can cost 2.35× and be worth it; it does not say this one is.
2. **"No self-inspection mechanism" is a claim, not yet a result.** It holds in the §12 trace, which is
   one sentence with one reading. Earning it needs a discrimination pair: two situations in which the
   agent should answer differently about itself, where the difference comes from the world rather than
   from a special case.
3. **The self may need to be more than one node.** Asked of a system running two independent
   conversations, *"what are you doing?"* wants one answer per addressee, and one self with one agenda
   may be the wrong shape. Not solved here; recorded so it is not later discovered as a bug.
4. **Reporting and doing may not stay separable.** §12.5 cuts the regress by observing that a process is
   a node and observing it mints nothing. If any observation ever mints a doing — a *noticing* process,
   say — the cut fails and the floor has to become explicit rather than structural.
5. **None of the shape is novel, and that bounds the claim rather than defeating it.** An agent with a
   self-model in its own knowledge base is BDI, PRS's meta-level knowledge areas, and Soar's state
   stack. What would be new is what the rest of the arc claims — the residue: that *why are you
   planning?* is answered by the machinery that answers *why is the block on the table?*, rather than by
   an introspection interface bolted beside it. Per [comparison.md](comparison.md) that remains a
   hypothesis until the system reasons differently through ordinary reasoning.

---

## 15. Relation to the rest of the plan

- It gives retraction a consumer. Signed frame membership and `retract` were on the critical path with
  nothing waiting on them; ending a doing is what waits on them.
- It re-motivates P4. The phase machine is not owed to the surface because Python is untidy — it is owed
  because what triggers what must be explicable, and a Python conditional cannot be asked why.
- It re-files the reachability inventory's loop entries. Driving the outer loop is reported as
  unreachable and should be recorded as deliberately so (§10). The pass says *cannot*; only a design can
  say *should not*.
- It puts the matrix's blank row on the critical path (§9) by finding an instance of it inside the
  engine.
- It does not advance grounding, and should not be read as doing so (§1).
