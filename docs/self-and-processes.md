# The agent in its own graph — self, processes, and what triggers what

**A design document, not a description of what runs.** [execution-model.md](execution-model.md) says how
the machine works today. This says what it should be, and why — and it is written entirely in the
representation the [facts-as-nodes.md](facts-as-nodes.md) arc is converting to, because the point does
not survive translation into the current one.

The requirement, stated by the user and load-bearing for everything below:

> **The agent needs a representation of itself within the graph, otherwise "I" and "you" are
> meaningless.**

And the capability it has to buy: the user asks *"what are you doing?"*, and the system answers *"I am
planning"* — **by reading the graph**, not by a Python function that knows about itself.

⭐⭐⭐ **The strongest form of this design, and the one it commits to: there is NO self-inspection
mechanism.** *"What are you doing?"* is a question about the world, where the world happens to contain
the asker's interlocutor. It goes through the machinery that answers *"why is the block on the table?"*
If it needs its own path, the design has failed — and this is the reflection thesis's own claim
([reflection.md](reflection.md)): *if the planner is rules, "why did I plan it this way?" is answered by
the machinery that already answers "why is the block on the table?", so there is one mechanism rather
than two.*

---

## 0. The reading discipline — the universal shape, and attributes do not exist

Everything in this document obeys one shape, and every example is checkable against it. If a line below
carries a property bag, the design is wrong at that line.

### The shape

**`a on b` is three nodes: `on`, pointing at `a` and `b`.** Nothing else — no fact node beside the
relation, no edge to a concept, no property bag. The relation node *is* the fact, and its ordered edges
*are* its members.

```
on(a, b)                  the `on` node points at a, then b
doing(self, search_1)     the `doing` node points at self, then search_1
agent(self)               the `agent` node points at self — one member, and still the shape
```

⚠ **This is written form and storage at once, which is why no second form appears below.** An earlier
draft of this page showed a separate node for the fact, an edge to a relation concept, and a member
label — four nodes and two labels where there are three nodes and no choice to make. Recorded rather
than deleted because the error is instructive: inventing a node to *hold* the relation is the reflex the
shape exists to remove, and it reintroduces exactly the shared-middle it is designed to prevent.

⭐ **Classification is a relation like any other**, which is why `agent(self)` above is a fact rather
than a type marking. *Who says this is an agent, and since when* is a real question — the cross-domain
case is two KBs classifying one thing differently, settled by an **authored bridge with a speaker**
([harmonization.md](harmonization.md)) — and a marking has nowhere to put the speaker.

⚠⚠ **Two things the shape does not settle, and this page does not need them settled.** How an instance
relates to the relation it instances (`ordered(next_form)` in §4.1 and §7.2 presume that can be said),
and what at the floor is not itself a node, since a node's edges to its members cannot each be nodes or
the storage never bottoms out. Both belong to [facts-as-nodes.md](facts-as-nodes.md) §*The floor*.
**Nothing below depends on either**, which is what lets this page proceed.

### ⭐⭐⭐ Attributes do not exist

This is not a simplification for the document's sake. It is the settled consequence of the shape
(facts-as-nodes §*Attributes are the same shape*): **if attributes are nodes, the attribute mechanism
has no remaining job**, and the substrate keeps none.

| what was an attribute | what it is now |
|---|---|
| `kind`, set at mint | an ordinary **classification fact** — `block(a)`, `agent(self)` |
| a scalar's payload (`2`, `1.0`, `"planning"`) | **identity by content** — a scalar node does not *carry* `1.0`, it **is** it |
| edge properties | gone — they existed only because an edge could not carry a fact |
| everything else — `phase`, `stop`, `done`, a replay's step index, `ticks`, `label` | an ordinary **fact**, with all that implies |

⚠ **"All that implies" is the whole reason this matters here.** `phase("planning")` as an attribute
cannot be dated, caused, questioned or retracted. As a fact it can. *"Since when have you been
planning?"*, *"why are you planning?"*, *"what would make you stop?"* are the same question asked of the
agent that *"when did this become true?"* asks of a block — and they are unanswerable while the agent's
state is a property bag.

⚠ **Even a name is a claim.** `named(self, system)` is a fact, not a label, because two independently
authored KBs will name one thing differently and the bridge between them is an authored fact with a
speaker ([harmonization.md](harmonization.md)). A label attribute has nowhere to put the speaker.

### ⭐ And classification being a fact is what makes *entities have no outgoing edges* true without an exception

An earlier draft marked the type on the node and then argued that this was an admissible exception to
the load-bearing invariant. **There is no exception once classification is an ordinary fact**, and the
argument was a symptom of the wrong shape rather than a subtlety:

```
agent(self)          the `agent` node points AT self
agent(user)          a different `agent` node points AT user
```

`self` has no outgoing edges at all — the `agent` node points at it, and nothing points out of it. So
nothing composes through `self`, and *what else is an agent* is the reverse lookup it should be.
⚠ Contrast the canonical leak, which this rules out structurally: `a --> on --> b` and `c --> on --> d`
sharing one `on` really do put `a --> on --> d` in the graph. Here each fact is its own node, so there
is no shared middle to walk through.

---

## 1. The self is an agent among agents

```
agent(self)
agent(user)

named(self, system)
named(user, anna)
```

⭐ **Not a new kind, and that is the design decision.** The system is an `agent` exactly as the user is.
Three things follow, and none of them needs machinery:

* **Indexicals become resolvable**, §2.
* **The system's own claims are ranked by the same authority machinery as anyone else's.**
  `discourse.py` already ranks speakers; today the system is a *label* (`SYSTEM`) used only when it asks
  the user a question, so its own assertions sit outside the ordering that governs everyone else's.
* **The system can be the subject of a fact**, which is the thing it cannot be today. Without it,
  nothing the system does can be dated, caused, attributed or retracted — the three-layer split
  (existence / holding / attribution) simply has no attribution for the agent itself.

⚠ **One self per graph, minted at bootstrap.** The scope is session-sized, and an agent that is not
one thing across a session cannot be the referent of "you" twice in a conversation.

---

## 2. "I" and "you" — an indexical is a construction, not a module

An indexical's referent is a function of **who is speaking to whom**, and the graph already records
that as soon as an utterance is a world event with participants:

```
u1 = utterance()
said(user, u1)
to(u1, self)
```

Then, and this is the whole of it:

> **`I` denotes the one who `said` the utterance the word occurs in. `you` denotes the one it is `to`.**

Two constructions, in the P5 proposal-and-selection sense
([expressiveness-and-uniformity.md](expressiveness-and-uniformity.md), and the skeleton already built in
`ugm/construction.py`). **No new capability**, because a construction is nodes and edges and a rule can
already author one (`rules/teach.mf`).

⭐ **And the symmetry is the test.** The same two constructions, applied to an utterance the *system*
said, resolve `I` to `self` and `you` to `user` — with nothing reversed and no special case. If either
direction needs its own rule, the self is not really an agent among agents and §1 is decoration.

⚠ **Grounding is still not claimed.** That *"the block"* denotes `block#1766` is reference resolution
and remains the hard part. Indexicals are the easy corner of it precisely because the graph already
records the two participants — which is worth saying so that closing this is not mistaken for closing
grounding.

---

## 3. A process is a thing; DOING it is a fact

This is the central distinction and everything downstream depends on it.

```
search(search_1)                the PROCESS — a thing, with a step, on an agenda
d1 = doing(self, search_1)             the DOING   — a fact about an agent and a process
```

Two nodes because they answer two questions. The process is *what is being run* — it has state, it can
be advanced, it can be finished. The doing is *that this agent is engaged in it* — and that is what
carries the time, the cause and the ending.

It is the three-layer split from facts-as-nodes, applied to the agent:

| | |
|---|---|
| **existence** | `search_1` exists, and `d1 = doing(self, search_1)` is a proposition; minting it asserts nothing |
| **holding** | when the doing began and whether it has ended — §3.2 |
| **attribution** | who says the system is doing it, and why — `caused(u1, d1)` |

### 3.1 Scoring the alternative — how the self relates to what it is doing

Per the standing process, before deciding, and the cost written down even where the answer is obvious:

| | not leaking | not lossy | readable | composable |
|---|---|---|---|---|
| an attribute on the process (`phase = planning`) | ✅ | ❌ no time, no cause, no speaker | ⚠ | ❌ nothing to point at |
| an edge `self --doing--> search_1` | ❌ gives the self outgoing edges; `self → search_1 → goal_3` composes | ❌ same | ✅ | ❌ |
| ⭐ **a hub `doing(self, search_1)`** | ✅ no entity→entity path | ✅ datable, causable, retractable | ✅ | ✅ the doing can be a member: `caused(u1, d1)` |

**The hub, on all four.** The cost, recorded anyway: one node per process-start, and the doing has to be
**ended**, which §3.2 shows is the expensive part.

### 3.2 ⚠⚠⚠ The open question: how a doing ENDS

*"I was planning and now I am not"* must be representable, or the system claims to be doing everything
it has ever done — the arc's own leak, landing on the agent. Two candidates, and they are genuinely
different rather than notational:

**(a) The real world gets a frame chain, and the doing goes `absent` in a later frame.**

```
frame_k   : d1 present
frame_k+1 : d1 absent
```

**(b) The doing is bounded by moments, and holding is computed.**

```
d1 = doing(self, search_1)
began(d1, m3)
ended(d1, m7)
caused(judgement_2, ended_1)          why it stopped — the residue, free
```

| | not leaking | not lossy | readable | composable |
|---|---|---|---|---|
| (a) frames over the real world | ✅ | ✅ | ⚠ *what is true now* means *walk the chain* | ✅ |
| ⭐ (b) moments bounding the doing | ✅ | ✅ | ✅ | ✅ `ended` is a node, so it can be caused and questioned |

⭐ **(b) is recommended**, for a reason that is about layering rather than convenience: facts-as-nodes is
explicit that **`absent` is the frame mechanism and nothing else** — it is how you delete something a
previous frame held, and it is *not* a claim that something is false. A doing that has stopped is not a
frame-mechanical deletion; it is a fact about the world having a beginning and an end. Collapsing them
would put a technical device where a temporal claim belongs, which is the frame-vs-hypothesis confusion
one level down.

⚠ **The cost, stated plainly: *are you planning now?* stops being a lookup and becomes a computation** —
*has begun, has not ended, at this moment*. That is the same trade §*A proposition is not an assertion*
already accepted for world facts, and it must not be bought back with a cache: **an index over what was
asserted is storage; a cache of what was derived is a TMS.**

⚠⚠ **And this lands the design squarely on the matrix's weakest row.** *Time / aspect* is `⚠` in every
column and has **no CNL family** ([HANDOFF.md](HANDOFF.md), the matrix). The self-model cannot be honest
without it. That is a finding, not a blocker: it says the time work has a consumer, which is the
condition this project puts on building anything.

### 3.3 The phase machine dissolves

Today a pursuit carries `phase = planning | acting | recovering | sensing | checking`. Under this design
there is nothing to carry it, and that turns out to be an improvement rather than a loss:

```
p1 = pursuit()
pursues(p1, goal_3)
doing(self, p1)

search(search_1)
serves(search_1, p1)
doing(self, search_1)
```

> **The pursuit is *planning* because a `search` that serves it is live. It is *acting* because a
> `replay` that serves it is live.** The phase is a **derived reading** of which sub-process is being
> done, not a stored label.

⭐ **And the two phases the labels could not distinguish become distinguishable.** `acting` and
`recovering` both have a live replay, so as labels they are two names for one situation plus a flag.
As structure they differ in **why**:

```
replay(r1)        serves(r1, p1)      doing(self, r1)
                                             caused(deviation_1, doing_of_r1)
```

*Recovering* is *acting whose doing was caused by a deviation*. So *"why are you doing this?"* answers
itself, where a label had to be asked about separately.

⚠ **The cost, written down:** five attribute comparisons become five derived readings, on a path the
loop takes every tick. Whether that is affordable is a measurement this document does not have, and the
precedent cuts both ways — `holds` going interpreted cost 2.35× on Sussman and was kept deliberately.

---

## 4. What triggers what

Today: agenda order, plus timers, plus a Python state machine inside a pursuit. The state machine is the
part that decides what follows what, and it is the part that is not data.

> **A trigger is a rule whose condition is over the graph — including over process facts — and whose
> consequent spawns a process.**

The phase machine then stops being *the* mechanism and becomes three instances of it:

```
when   pursues(P, G) and not holds(G) and no live search serves P
then   open a search serving P

when   a search serving P has produced a plan and no live replay serves P
then   open a replay serving P, carrying that plan

when   a replay serving P deviated
then   open a search serving P, caused by that deviation
```

Three consequences, and the third is the one that pays:

* **Triggering becomes authorable.** A domain can add *"when the kettle boils, stop waiting"* without a
  module, in the same way `rules/teach.mf` adds a construction without one.
* **Triggering becomes readable**, which is B3 — *the surface can read what an operation is about*. A
  Python `if phase == PLANNING` is an opaque blob; a condition over facts is a structure something can
  ask questions of.
* ⭐⭐⭐ **Triggering becomes explicable.** *"Why are you planning?"* is answered by the trigger's own
  condition: *because this goal does not hold and nothing was planning it.* That is the residue thesis
  applied to the agent's own control flow, and it is exactly the sentence the current phase machine
  cannot produce.

### 4.1 ⭐ The agenda's turn order is a SIXTH order, and it is the example the matrix is missing

The outer loop is round-robin: take the head, advance one step, put it back at the tail. That order is
a relation between tasks, and it is not any of the five the arc already catalogued (`before` on moments,
`then` on a goal, `after` on a plan, `next` on frames, `next` on tokens, plus method steps' positional
order).

```
next_turn(search_1, replay_2)          agenda order
ordered(next_turn)                     declared, per facts-as-nodes §Ordered and unordered
```

⚠ **It must not become temporal**, exactly as form order must not: *what runs next* and *what happened
before* are different relations, and collapsing them is Fodor's error at scale, one more time.

⭐⭐⭐ **And notice what this is.** The matrix's one wholly blank row is *protocol / order over a
sequence*, whose worked example is **taking turns** — and the outer loop is literally a set of processes
taking turns. So the engine contains an instance of the semantics it cannot state, and making the
agenda's order sayable is *the same work* as making *taking turns* sayable. That is the strongest
argument yet that the blank row is on the critical path rather than parked.

---

## 5. Reading the scheduler, and not driving it

⭐⭐⭐ **This is a safety boundary, not an unfinished migration**, and the distinction matters because
`python -m ugm.reach` reports it as a gap. That pass answers *can a rule reach this*; it never asks
*should it*. Three-way split:

| | |
|---|---|
| **spawn** a process | ✅ **yes** — a running body reaches its own agenda and schedules onto it. Already true |
| **read** status | ✅ **yes — and this is the real gap** |
| **drive / reorder / force a tick** | ❌ **no, deliberately** |

The reason for the third is the single most important safety property in the design: *a tick reports the
verb it would perform before taking it, and a caller can stop before the first irreversible one — the
loop can decline to take the step; it cannot make the step reversible.* A rule that could force a tick
would route around the one veto point in the system.

What *reading* means, as facts rather than as a Python API:

```
doing(self, P)                          what am I doing
began(D, M) / ended(D, M)               since when, and until when
serves(sub, parent)                     what is this in service of
caused(X, D)                            why am I doing it
next_turn(T1, T2)                       what runs next
not_before(T, M)                        what is waiting, and on what
would_be(T, act)                        would the next step touch the world
```

⚠ **`would_be` is the one that must stay derived rather than stored**, because its whole value is that
it is asked *before* the step is taken. A stored answer is a cache of a derived value, which is the TMS
commitment declined twice already.

---

## 6. The answer node and the answer tool

⭐⭐⭐ **An answer is a node the engine builds, and emitting it is a tool call.** Not a string returned
by a Python renderer — *a predicate that answers in prose cannot move*, and this project has already
paid for that twice (`unmet_expectations`, blocked by a dict going in and prose coming out).

```
answer(a1)
about(a1, u1)                   which utterance it answers
reports(a1, d1)                 each thing it says is a FACT, pointed at
reports(a1, d2)
```

⭐ **Each report is a separate fact rather than members of one**, so each can be questioned on its own —
*"why that one?"* picks out `d1` without disturbing `d2`. A single answer node with a list of members
would make the answer atomic, and an answer nobody can ask a follow-up about is a string with extra
steps.

Emitting it is a `DISPATCH` to an `answer` tool, and **three consequences fall out rather than being
added**:

* ⭐⭐⭐ **Answering is an `act`, not a `look`.** It reaches outward, and **you cannot unsay something**.
  So it lands on the irreversible list and the loop can decline to take it — which is the correct
  behaviour and nobody had to legislate it.
* **The system's answers become world events with a speaker**, symmetric with `discourse`'s existing
  `ask_user` (an utterance `by=SYSTEM`). So *"what did you tell me?"* and *"why did you say that?"*
  become ordinary questions.
* **Rendering is translation at the EDGE**, which is already the sanctioned practice (`_UNMET_PHRASE`).
  The *content* is graph structure; only the last hop is words.

⚠ **The trap this must not fall into**: building the answer node in Python and immediately stringifying
it is the same defect wearing a node. The test is the one the arc uses everywhere — **could a rule have
produced this value?**

---

## 7. Worked trace — *"what are you doing?"*, end to end

The system is already planning. Every line below is a fact node; nothing is an attribute.

### 7.1 The state before the question

```
agent(self)            agent(user)
named(self, system)           named(user, anna)

pursuit(p1)                   pursues(p1, goal_3)
search(s1)                    serves(s1, p1)

d1 = doing(self, p1)          began(d1, m2)
d2 = doing(self, s1)          began(d2, m2)
caused(trigger_1, d2)         the planning trigger of §4 fired
```

*Nothing has ended, so both doings hold at any moment after `m2`.*

### 7.2 The utterance arrives

Recorded as tokens and nothing else — no parse, no verb, per the skeleton that is already built.

```
utterance(u1)
said(user, u1)   to(u1, self)   when(said_1, m9)

token_at(u1, 0, w_what)      next_form(w_what, w_are)
token_at(u1, 1, w_are)       next_form(w_are, w_you)
token_at(u1, 2, w_you)       next_form(w_you, w_doing)
token_at(u1, 3, w_doing)

ordered(next_form)                     word order is a relation, and it is DECLARED ordered
```

⚠ **`next_form` is form order and must not be `before`.** This is the five-orders discipline showing up
in the smallest possible example: word order is not time, and one label over two relations is the defect
the census already caught the engine committing with `next`.

### 7.3 Interpretation — proposal and selection

A construction addressed at `w_doing` proposes: *a question about what its subject is doing*. The
indexical construction of §2 resolves `w_you` — the utterance is `to` `self`, so `you` is `self`.

```
reading(r1)                 about(r1, u1)
proposes(r1, question_1)
question(q1)                asks(q1, doing(self, ?))
subject_of(q1, self)
```

**The world does not disambiguate anything here**, and that is worth noting rather than hiding: this
sentence has one reading. The attachment-ambiguity result belongs to *"put the block on the table"*, and
claiming it everywhere would be the kind of overreach this project's docs are written against.

### 7.4 The question spawns a process

*Asking triggers an answer* — a trigger in the §4 sense, whose consequent spawns:

```
answering(ans1)             answers(ans1, u1)
d3 = doing(self, ans1)             began(d3, m10)
caused(q1, d3)                     WHY it is answering: because that was asked
next_turn(s1, ans1)                it takes its turn on the same agenda
```

⭐ **Note what is not here: no interrupt, no special path, no privileged status.** Answering is a
process among processes and takes one step per tick like the search does. The system stays interruptible
while answering, which is the property the whole loop exists to preserve.

### 7.5 The answering process reads the graph

It asks the ordinary question — *which `doing(self, ?)` hold at `m10`?* — and gets **three**:

```
d1 = doing(self, p1)         began m2,  not ended     pursuing goal_3
d2 = doing(self, s1)         began m2,  not ended     searching, serving p1
d3 = doing(self, ans1)       began m10, not ended     answering u1
```

### 7.6 ⭐⭐⭐ The regress appears, and the honest answer includes it

`d3` is the answering process reporting **itself**. That is not a defect to be filtered — *"and
answering your question"* is a true and useful thing to say, and a system that hid it would be
misrepresenting what it is doing.

**It terminates**, and the reason is structural rather than a guard: the agenda advances each task by
**one step per tick**, so a process that observes processes cannot outrun the thing it observes. The
floor is the one already in the codebase — `precedence.seal_rule`'s *the last stage must be total* —
and the tower is finite per tick rather than excluded by prohibition.

⚠ **The failure mode to design against is not infinite regress but infinite REPORTING**: an answering
process that reports its own reporting of its own reporting. The cut is that `d3` is *one* doing, not a
chain — the process is a node, and observing it does not mint a new one.

### 7.7 The answer is built

```
answer(a1)            about(a1, u1)
reports(a1, d2)              I am searching for a plan for goal_3
reports(a1, d1)              …in service of pursuing goal_3
reports(a1, d3)              …and answering you
```

⭐ **The answer is a set of pointers into what is already true**, not a new description of it. Nothing
is copied, so the answer cannot drift from the state it reports — and every follow-up question lands on
the same nodes the answer pointed at.

### 7.8 The answer is emitted

```
DISPATCH answer a1

utterance(u2)
said(self, u2)    to(u2, user)    when(said_2, m11)
renders(u2, a1)
```

The tool renders — *"I'm planning how to achieve goal_3, and answering you."* — and the rendering is the
only place words appear.

### 7.9 ⭐⭐⭐ What the follow-ups now cost, which is the whole point

Every one of these is the **existing** question machinery pointed at the nodes above. No new mechanism:

| question | answered by |
|---|---|
| *"since when?"* | `began(d2, m2)` |
| *"why are you planning?"* | `caused(trigger_1, d2)` → the trigger's own condition: *goal_3 does not hold and nothing was planning it* |
| *"what for?"* | `serves(s1, p1)`, `pursues(p1, goal_3)` |
| *"why did you say that?"* | `renders(u2, a1)` → `about(a1, u1)` → because you asked |
| *"are you still doing it?"* | `ended(d2, ?)` — absent, so yes |
| *"stop"* | assert `ended(d2, m12)`, `caused(u3, ended_2)` — and the loop declines the next tick |

⚠ **`"stop"` is the one that shows the design working.** Today stopping is a `stop` attribute the loop
checks. Here it is an ordinary assertion by an agent with authority, dated and attributed — so *who
stopped me, when, and were they entitled to?* is answerable, and the discourse layer's existing
authority ranking governs it without being told about processes at all.

---

## 8. What this requires that does not exist

Listed so the design can be costed rather than admired.

| | |
|---|---|
| ⚠⚠⚠ **ending a doing** | §3.2. Needs the **time/aspect** semantics that are `⚠` in every column of the matrix and have no CNL family. The largest item, and the self-model cannot be honest without it |
| **the self node** | §1. Small, and blocks everything |
| **`to(utterance, agent)`** | the addressee. `discourse` records the speaker and not the hearer, so `you` has nothing to resolve against |
| **the indexical constructions** | §2. No new capability — a rule can author a construction today |
| **the `answer` tool** and the answer node | §6. Needs `answer` registered as a dispatch target that does *not* observe, so it classifies as `act` |
| **triggers as data** | §4. This is P4's content, re-motivated: not *"the phase machine should be in the surface"* but *"what triggers what must be explicable"* |
| **agenda order declared** | §4.1, and it is the matrix's blank row wearing engine clothes |
| ⭐ **nothing new for reading status** | §5 — the facts are the reading. The gap is that they are attributes today, which the conversion closes |

---

## 9. ⚠ Where this could be wrong

*"Too good to be true"* is the right reflex, and five places this is not yet earned:

1. ⚠⚠ **The phase machine dissolving into derived readings is unmeasured**, and it is on the loop's
   hottest path. §3.3 states the cost and does not price it. The `holds` precedent says an interpreted
   predicate on a hot path can cost 2.35× and be worth it; it does not say this one is.
2. ⚠⚠ **"No self-inspection mechanism" is a claim, not yet a result.** It holds in the §7 trace, which
   is one sentence with one reading. The test that would earn it is a **discrimination pair**: two
   situations in which the agent should *answer differently about itself*, where the difference comes
   from the world rather than from a special case. Per the standing lesson, *a distinction nothing acts
   on is bought and never spent.*
3. ⚠⚠ **The self may need to be more than one node.** *"What are you doing?"* asked of a system running
   two independent conversations wants one answer per addressee, and one `self` with one agenda may be
   the wrong shape. Deliberately not solved here; recorded so it is not discovered as a bug.
4. ⚠ **Reporting versus doing may not stay separable.** §7.6 cuts the regress by observing that a
   process is a node and observing it mints nothing. If any observation ever mints a doing — a
   *"noticing"* process, say — the cut fails and the floor has to be explicit rather than structural.
5. ⚠ **None of the shape is novel, and that bounds the claim rather than defeating it.** An agent with a
   self-model in its own knowledge base is BDI (`belief`, `desire`, `intention` as data), PRS's
   meta-level KAs, and Soar's state stack. What would be new is the same thing the rest of the arc
   claims — the **residue**: that *why are you planning?* is answered by the machinery that answers *why
   is the block on the table?*, rather than by an introspection API bolted beside it. Per
   [comparison.md](comparison.md), that stays a hypothesis until the system reasons differently
   *through ordinary reasoning*.

---

## 10. Where this sits against the rest of the plan

* It **gives `retract` a consumer.** Signed membership and `retract` were on the critical path (*B
  requires C*) with nothing waiting on them. Ending a doing is what waits on them.
* It **re-motivates P4.** The phase machine is not owed to the surface because Python is untidy; it is
  owed because *what triggers what* must be explicable, and a Python `if` cannot be asked why.
* It **re-files the reach inventory's loop entries.** `loop.run` / `tick` / `advance` are reported as
  unreachable and should be recorded as **deliberately** so — §5. The pass says *cannot*; only a design
  can say *should not*.
* It **puts the matrix's blank row on the critical path**, §4.1, by finding an instance of it inside the
  engine.
* ⚠ It **does not** advance grounding, and should not be read as doing so — §2.
