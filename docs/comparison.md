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
