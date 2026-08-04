# What is actually different — an honest comparison

This document exists to stop a claim from being made loosely. UGM has a graph world, dynamic attributes,
predicate dispatch, hypothetical worlds, rules as data and computation as data. It is tempting to read
that list and conclude the combination must be new. **Not one item on it is.** Every feature here has
decades of prior art, usually done better and always done faster.

So the question worth asking is narrower: *is there a property this system has that its neighbours do
not, and would that property buy anything?* There is a candidate. It is **not** what the machinery does
when it runs, and stating it as though it were is the mistake this document is written to prevent.

## First, the prior art

| feature here | where it already exists, often since the 1970s |
|---|---|
| a graph world with dynamic attributes | frame systems (Minsky; KRL), semantic nets, RDF/OWL, Cyc, Datomic |
| rules as data | Prolog, Datalog, CLIPS, Soar, ACT-R, production systems generally |
| dispatch on conditions of the world | predicate dispatch (Chambers' Cecil; Ernst et al., ECOOP'98), CLOS, Clojure multimethods |
| computation reachable as data | 3-Lisp and reflective towers (B. C. Smith), Smalltalk, the CLOS MOP |
| hypothetical worlds | ATMS environments (de Kleer), Datomic's `d/with`, STRIPS/PDDL, ASP |
| what a derivation rests on | TMS / ATMS justifications — which this project **deleted**, deliberately |
| reinterpreting what a read means | dynamic scope; and much more precisely, **algebraic effect handlers** (Eff, Koka, OCaml 5) |

Anyone claiming novelty for *"predicate dispatch plus dynamic attributes"* should be pointed at CLOS,
which has had both for forty years. The claim has to be somewhere else or it is not a claim.

## The candidate, stated correctly

> The advantage, if there is one, is not that the machinery **executes** in the surface.
> It is that the machinery's **by-products carry semantics** — the supporting data structures a
> reasoning process leaves behind are addressable, domain-level objects rather than interpreter state.

The distinction matters because the two come apart, and here they come apart in the direction that makes
the point sharply: moving `execution.step` into the surface made it **3–5× slower** and bought nothing at
all in execution terms. What it bought was that a plan being carried out for real now leaves a record
anyone can ask about mid-flight — where it has got to, which real node stands for which imagined one,
what it has already done, what it could not pair and why. Before, that was four Python local variables.

The residue is the product. Execution is the price.

## What the residue actually is

Not an aspiration — these are the kinds the modules declare, and every one of them is an ordinary node
you can point at, query, store, or hand to a rule:

* **imagining** — `workbench`, `frame`, `mapping`, `transformation`, `hypothesis`
* **searching** — `search`, `candidate`, `trace_step`, `refusal`, `signature`
* **acting** — `replay`, `bound`, `deviation`, `unproduced`, `ambiguous`
* **computing** — `activation`, `register`, `focus`, `head`, `context`
* **deciding** — `tie_break`, `stage`, `criterion`, `norm`
* **remembering** — `attention`, `application`, `forgetting`, `loop`

So questions that are ordinarily *engine instrumentation* are ordinary graph reads here:

| question | answered by |
|---|---|
| which assumption is this plan resting on? | `transformation -assumes-> hypothesis`; `workbench.fragile_steps` |
| what did I imagine would happen, and what actually did? | two frames' difference, against the replay's bindings |
| which real thing is this imagined thing? | `mapping`, and `execution.bound_to` |
| how far through the irreversible part am I? | `replay.at`, mid-flight |
| why did it stop? | a `deviation` node naming the frame, the transformation, and what was minted |
| what did this rule consider and rule out? | `refusal`, kept rather than erased |
| what was this call doing when I paused it? | `activation`, with its program counter |

## Where each neighbour stops

The useful comparisons are the ones that get closest, not the ones that are furthest away.

**Production systems (Soar, ACT-R, CLIPS).** Rules are data; the *engine* — match, conflict resolution,
firing — is host code. Soar and ACT-R record a great deal about their own operation, and that is exactly
the right instinct; but what they record is a designed instrumentation channel, not the engine's own
working representation. Nothing in the rule language can be handed the engine's state as an ordinary
value and reason over it.

**Prolog / Datalog / ASP.** The search tree lives in the WAM's stacks. *Which of my assumptions does this
answer rest on* has no answer without instrumenting the engine or reifying the proof by hand. Where a
proof term is available it is a proof of a query, not a record of a process that acted on a world.

**PDDL planners.** The plan comes out; the search that produced it does not. The road not taken is gone,
which is why a contingency has to be replanned rather than looked up. Here an abandoned fork is kept as
data, and `execution.matching_alternative` reads it — a contingency for free, because the branch was
already imagined and already checked.

**ATMS / TMS.** The closest relative for *what does this rest on*, and better at it. A label really does
say which environments support a fact. But an ATMS is one mechanism recording one kind of dependency; it
does not also hold the plan, the actions, the refusals and the interpreter. This project deleted its TMS
and recomputes on demand ([advice-over-sequences.md](advice-over-sequences.md)) — a decision that only
makes sense if what supports what is derivable from the residue you already keep.

**Datomic.** `d/with` gives a speculative database *as a value*, which is genuinely the workbench's idea,
and `as-of` is genuinely time-travel over one representation. What is not there is the *reasoning*: the
hypothetical world is a value your code produces, and nothing records why you produced it, what you
expected of it, or which of its differences you were counting on.

**Algebraic effect handlers.** Precisely mediated access: a read becomes an operation, and a handler
decides what it means — which is exactly *one rule, one behaviour, only what a read means differs*. This
is the strongest analogue and the one to compare against seriously. The difference is where the handler
lives: it is installed by host code, chosen lexically or dynamically, and is not something the running
program can inspect, name, or rewrite. Here the resolver is **named in the graph** (`in_frame`), found
through the ambient context, and is an ordinary function the system could in principle reason about.

**The CLOS MOP.** The strongest precedent for *change your own mechanism from within the language*, and
it is a real precedent. But the MOP is reflective about **evaluation**. This is reflective about
**planning, acting, and checking against a world**, which is a different object — and the residue that
falls out is about an agent's engagement with a world rather than about method lookup.

## The outer loop — the same thesis, applied to control

A second candidate, and it turns out to be the residue argument again rather than an independent one.
There is **one** outer loop, every long-running activity is a node plus a `step`, and nothing is
uninterruptible: an activation advances by one instruction, a search by one imagined state, a replay by
one real action, a pursuit by one step of plan-act-check-replan. Adding a kind of work means writing its
`step`, not touching the loop.

**Interruptibility itself is thoroughly prior art**, and it is worth being blunt about how thoroughly:

| what | where |
|---|---|
| resumable procedures | coroutines and generators (Lua, Python, Go), CPS, `call/cc` |
| preemption a program cannot escape | the BEAM — reduction-counted, fair, and far stronger than this |
| a reified, inspectable stack | Smalltalk's `thisContext`; reflective towers |
| durable, resumable long-running procedures | Temporal, Azure Durable Functions, Step Functions |
| one decision cycle driving everything | **Soar**, **ACT-R** — this architecture, in the 1980s |
| the agent's own intentions as first-class droppable data | **BDI: PRS, AgentSpeak/Jason** — the closest relative |

AgentSpeak is the one to measure against. It has an interpreter cycle, intentions are first-class, and an
agent can suspend, drop or resume them. If the claim were *"procedures are interruptible and the
continuation is data"*, AgentSpeak got there first.

So the claim is again not the mechanism but what the paused state **says**:

* **The continuation is domain-readable at every level, in one representation.** A paused BEAM process
  says nothing; a paused Temporal workflow says where it is but not what it is *for*. Here a stopped
  pursuit answers *which goal, which attempt, which phase, how many states imagined, step 2 of 4* —
  `driver.describe_pursuit` is a read, not an instrumentation channel — and one level down the stopped
  activation names the function and the instruction, and one level up the agenda says who is next.
* ⭐ **The system knows which of its own steps are irreversible, and that is a semantic fact rather than
  a scheduling one.** A tick reports its verb — `imagine`, `look`, `act`, `run`, `forget` — and `ACT` is
  the one that reaches the world, so a caller can stop *before* the first irreversible step. Temporal
  knows about retries, not about moral irreversibility; Soar does not classify its operators this way.
  `loop.py` states the property directly: *"the loop can decline to take the step; it cannot make the
  step reversible"*. That is the residue thesis applied to control — the *kind* of a step carries
  meaning, so a policy about what may happen next can be written against it.
* **The criterion for interrupting can itself be authored.** A watcher written as ordinary text can stop
  a live search on a judgement about how the search is going, because the search's own progress is data
  the watcher can read. That is interruption whose *reason* is domain knowledge rather than a timer.

⚠ And the honest weaknesses, which are the mirror image: this is **cooperative, not preemptive** — a
native or a Python loop beneath the horizon still blocks, and natives are uninterruptible by design;
there are no fairness guarantees of the kind the BEAM makes; and nothing is persisted, so "durable
execution" is a property the graph could support and does not currently claim.

## What is genuinely composite

None of the above is unique on its own. What is unusual is that **all of it is in one graph, and the
by-products point at each other**: a deviation names a transformation, which names the hypothesis it
assumed, which sits on a frame, whose mappings say which real node each imagined one stands for, which
a replay bound while acting, under a context whose resolver is a named function you can read — and the
whole chain is reachable *from a task the outer loop has paused mid-step*, because the pause is at the
same level of description as everything else.

That is the composability principle the project already states — *reflexive mechanisms must combine on
one substrate* — and it is the only place a claim of novelty could survive contact with the list above.
A system with a TMS **and** a planner **and** a MOP, each excellent, still has three representations and
no way to ask a question that crosses them.

## Language — where parsing stops, and what could be on the other side

The boldest available claim about this project is that **language processing and reasoning coexist with
no seam**: utterances compile to expressions the engine runs, ambiguity is resolved by the same authored
preference machinery that chooses actions, and the engine knows nothing special about *why*, *what* or
*how* — they are simply different procedures the language compiles to.

**As stated, that claim is false twice over**, and both are worth knowing before it is repeated.

*The prior art is directly on point, not adjacent.* **SHRDLU** (Winograd, 1971) and **procedural
semantics** are almost verbatim this thesis: English compiled into PLANNER procedures, reasoning and
acting on a blocks world in one system — and SHRDLU learned *"a steeple is a stack which contains two
green cubes and a pyramid"* and understood the word afterwards. **DCGs in Prolog**: parsing *is*
inference, one engine, one representation, ambiguity as ordinary nondeterminism, and a wh-question is a
query with a variable. Add **Montague**, **Cyc**, **ACE**, **GF**, and **Inform 7**, whose *"does the
player mean…"* rules resolve ambiguity in the same rulebook machinery as everything else.

*And it is false of this repository today.* `intake.py` has `GOAL_VERBS = ("goal", "ask", "why", "plan")`
and, further down, `if verb == "why": …`. The machinery knows about *why* by name, in Python. What exists
is a controlled language with a Python front end.

### The wall, in three layers — only the third is one

1. **Coverage.** Grammars trail the tail of language forever: `0/50` on raw prose, `26%` on the book
   corpus. Painful, but engineering.
2. **The ordering.** A parser must commit to a structure *before* the reasoner is consulted, while the
   information needed to choose the structure lives *in* the reasoner. An architectural inversion; no
   grammar fixes it.
3. ⭐⭐⭐ **Parsing is a decomposition operation, and this project's own epistemology forbids it.** A
   parser rewrites an utterance into constituents by a fixed grammar, before any knowledge is consulted.
   But meaning is held here to live *above* the horizon — *"kill = cause to die fails as a decomposition
   because that relation lives above the horizon; it is a network relation, not a definition."* That is
   Fodor's error, named in [concepts.md](concepts.md) and refused everywhere else in the design.
   **A parser at the front is the one place the project does the thing it forbids.**

That third one is not passed with a better grammar. It says the operation is wrong.

### What is on the other side, and its name

**Hobbs, *Interpretation as Abduction* (1993)** — syntax, semantics, pragmatics, coreference and
ambiguity all fall out of finding the lowest-cost abductive proof of an utterance. No separate parser;
interpretation *is* inference. Which is to say **proposal + selection**, and that is already the shape of
`proposals` → `relevance` → `tie_break`.

In this system's terms: an utterance is **evidence** rather than a string to rewrite; a reading is a
**candidate**, exactly like a proposed action; selection is *authored, inspectable* preference where a
parser's is grammar accident; and the survivor is an **interpretation node**. The payoff is the residue
thesis reaching language — **an interpretation you can ask *why* of.** Hobbs gives the shape; nothing in
that tradition keeps the proof afterwards.

The rule form that goes with it is **Construction Grammar**, and here too the tradition is ahead:
**Radical Construction Grammar** (Croft) denies that parts of speech are primitives at all — categories
are *derived* from the constructions a word occurs in; **Goldberg** and **Fillmore** give form-meaning
pairs from specific idioms to schematic argument structures, ordered by specificity; and **Fluid
Construction Grammar** (Steels) is the computational one, bidirectional, with agents inventing and
learning constructions at run time.

⭐ **What would be this system's own is narrower and real.** In FCG the constructions are data but the
unification engine and the learning operators are Lisp. Here, if a rule writes a rule, the **learner is
itself a rule** — same representation, selected by the same dispatch, revisable, attributable to whoever
said it, retractable — and *which construction fired and why it beat the others* is residue. Note also
that **learning a construction is `compile_episode` for utterances**, and harmonization is already
described as that function's missing sibling: three threads with one shape.

⚠ And the honest costs. Abductive interpretation is a research problem — search over proofs, famously
expensive, which is why the field went statistical and then neural. At 3–5× per interpreted layer a naive
version is unaffordable here. Which lands where this project's own note already put it: an LLM is *"one
possible tool a rule dispatches to at the boundary (construction, ambiguity resolution, prose→CNL)"*.
**The proposer need not be symbolic; the disposer is the whole point.** Coverage stops being this
project's problem, and what remains is the part that was always its own: the interpretation is durable,
chosen by authored knowledge, and records why.

### What it would cost, measured rather than argued

Construction grammar is a *massively* multi-body dispatch, and the note in
[predicate-dispatch.md](predicate-dispatch.md) predicted where that bites: *"the first real multi-body
operator is where ranking can quietly degrade."* Measured on `fn.select`, bodies under one name:

| bodies | only one applies | **all applicable** |
|---|---|---|
| 10 | 0.28 ms | 0.82 ms |
| 50 | 1.18 ms | **18 ms** |
| 100 | — | **63 ms** |
| 200 | 4.86 ms | — |

Linear when few apply (~24 µs of guard evaluation per body) and **quadratic in the number of *applicable*
bodies** — and many-applicable is construction grammar's normal case, not its worst one.

Two things follow, and neither is a wall.

* ⭐ **The quadratic is recomputation, not cost.** `precedence._covers(g, a, b)` compares two *guards*:
  no arguments, no frame, no call data. **The specificity order is static**, and `select` rebuilds it on
  every call. `function.define` already sets the precedent by deciding `mediated` once when the body
  arrives, *"because asking per step would mean loading the body back out of the graph on the hot path"*.
* ⭐ **You can drop parsing; you cannot drop indexing.** A chart was never a commitment to *grammar* — it
  was a commitment to not evaluating every rule against every span. ⚠ And note what this does **not**
  require: a part of speech. Filtering on any discriminating attribute works, which is what `_covers`
  already does — *"is every demand `b` makes also made, at least as tightly, by `a`?"*, subsumption over
  tests, no category consulted. Discriminating is simply not the same as **cheap**: asking each rule
  *"does your constraint match?"* is O(rules) whichever kind of constraint it is, so cheapness means
  going the other way, from the attributes *present* to the rules that want them. The key for that
  already exists and is used as a pairwise early-out rather than as an index — `_covers` opens with
  *"keying differs first: two rules that watch different constraints never compete"*.

Both are probes, and both are affordable before any language design is written.

## Is this "self-awareness"? — scoping the claim before someone else does

The residue list invites a bigger word than it has earned, so: **no, not yet**, and the gap has a precise
shape. Nothing here is about experience or feeling; the question is the ordinary one about *data*, and
even on those terms the honest answer is *a precondition, not the thing*.

Maes' distinction (*Computational Reflection*, 1987) does most of the work. **Reflection** is reading
your own structure; **intercession** is acting on what you read. A **self-model** is a third thing again,
and it is the one that would justify the word.

| ingredient | here |
|---|---|
| **reification** — internal state as first-class values | yes, thoroughly: `activation`, `frame`, `replay`, `search`, `context` |
| **introspection** — the system reads it, in its own language | yes: `SELF` hands a program its own activation |
| **intercession** — it acts on what it reads | in places: `REFUSE`, a watcher stopping a live search, mediation enforced at `step` |
| **self-model** — a representation of itself *as a subject* | **no** |
| **monitoring** — watching its own performance and adapting | fragments: criteria, expert judgement |

Two places where self-reference genuinely does work rather than merely being available:

* **`dispatch.imagining`** — *am I inside an imagined world right now?* The system asks about its own
  dynamic extent in order to constrain what it may do. Its history is the instructive part: the same
  safety property used to be checked by looking at the *argument* (is this node a workbench copy), and
  that guard silently stopped firing the day rules were bound to real nodes. **The property was always
  about the system's own state, never about the object** — which is what makes this an instance of
  self-knowledge rather than a type test wearing its clothes.
* **`memory.attribute`** — *was it me?* Separating changes the system caused from changes the world made,
  which is why a slot only it touches scores zero volatility.

**What is missing is the difference between a record of experience and a model of a subject.** The
residue says what happened, in the same vocabulary the world is described in. A trace of my actions is
not a model of me. Self-awareness in the sense worth claiming would need something like *"I tend to
over-plan in worlds of this shape"* or *"I am unreliable about that"* — a representation **about** the
system, used to decide. Nothing here holds one.

⚠ And there is a tension worth stating against this project's own instinct: **uniformity is in some ways
the opposite of self-awareness.** Representing the system's own activity exactly as the world is
represented means no self/other line is drawn anywhere. Awareness of a self requires a *distinction*, not
merely transparency — which is why it is telling that the one place UGM comes closest is `attribute`,
whose entire job is to draw that line.

The fair sentence is therefore **self-transparency, with a few working instances of self-reference, and
no self-model**. That is a real precondition — metacognition cannot be built on a system whose reasoning
leaves no readable trace — and a precondition is not the thing. The test is the same one this document
applies everywhere: *availability is not awareness; the representation has to be used in the loop.*

## The price, and it is not small

Every layer that moves into the surface costs 3–5× against the Python it replaces, and it **compounds**
as more machinery moves down. `goal.holds` alone more than doubled the flagship benchmark. That is the
honest shape of the trade: readable residue is bought with interpretation, and the project has taken that
trade deliberately every time, recorded each price, and kept every swap reversible behind a wrapper.

It is also the right way round, which is the one defence worth making: an unreadable-but-fast mechanism
cannot be made readable later, whereas a readable-but-slow one can be made fast — by a better
interpreter, a compiler, or a native whose every decision is an argument (see the horizon section in
[concepts.md](concepts.md)).

## How to falsify this

⚠ **As of today this is a hypothesis, not a demonstrated advantage.** Nothing in the repository shows a
task UGM performs that a good Prolog program plus a planner could not. Uniformity is a *property*; an
advantage is a *result*, and the two must not be conflated.

The claim becomes real the first time the system **changes how it reasons through ordinary reasoning**,
with no metalanguage and no host code:

* advice that constrains the **order** of a plan's actions by reading the guards of the very rules that
  plan — [advice-over-sequences.md](advice-over-sequences.md), which needs predicate dispatch slices 3–4;
* **harmonization** rewriting a term that `rules/resolve.mf` itself is written in
  — [harmonization.md](harmonization.md), designed and not built;
* a question that crosses the residue and cannot be asked of any single neighbour above: *which of my
  standing assumptions did the action I took last Tuesday depend on, and is it still true?*
* a decision to **stop** taken on the residue rather than on a budget: a watcher that halts a pursuit
  because of what the pursuit's own record says about it — and, the sharper version, one that declines
  the next step *because it is an `ACT`* on grounds the system authored itself.

Until one of those runs, the correct description of this project is **"an unusually uniform substrate,
whose reasoning leaves readable residue"** — which is a real and unusual property, and not yet a proven
advantage. Anything stronger should be written here only with a demonstration beside it.
