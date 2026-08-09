# Planning and acting

The machine pursues a goal by imagining what its rules would do, keeping every imagined state, and
taking the path that reaches a state the goal accepts. That path already is a plan, so it can be run
against the real world unchanged. When reality disagrees, the machine stops, says how, and either
resumes onto a branch it already explored or replans from where it actually is.

## A goal is a set of constraints

A goal is a node, and each thing it requires is a node under it. Three sorts, because three
questions genuinely differ:

* **link** — *`a` must be `on` `b`*: a specific edge between specific individuals.
* **attr** — *`b` must be clear*: a specific value on a specific node.
* **type** — *something must be a `three_high`*: a reusable schema, optionally about a named
  subject; without one it asks whether anything in the region qualifies.

A link constraint cannot simply be a type. A schema says *this label, this kind, this many*, never a
*particular* target — and that is not an oversight. A schema is reusable and individuals are not.

There is a fourth, different kind of requirement: **knowledge**. `d.contents known` says *go and
look*, rather than *make it so*. It is what lets a plan contain a sensing step. Because absence of an
attribute means *lacks it*, a knowledge claim is restricted to attribute slots and refuses anything
else — otherwise a goal that asked about an absent edge would read as satisfied without ever having
looked.

Goals nest. A goal can raise subgoals, know why it raised them, and order them; and a goal is closed
only by reality. Finding a plan records that a plan was found; nothing but a completed execution
closes the goal. Those were once one operation, and conflating them meant a goal read as met while
execution had diverged and nothing had happened.

### What drives the search

`goal.unmet` — *which constraints are still false* — is what makes this means–ends rather than blind
search. A goal that only answers yes or no forces generate-and-test; a goal that names what is still
open lets the driver ask what could close it.

## Constraints on the plan itself

A goal can constrain not just the world but the route taken to it, which is what having the plan *in
the graph* is for. The plan is not a value a planner returned; it is frames and transformations, so
"which actions may I use, and how many" is an ordinary question about ordinary data.

```
goal: [a on b, never anything on c, must paint]
plan found in 2 step(s) after imagining 2
  stack(b=a, onto=b)
  paint(b=b)
```

The distinction that decides how these are handled is safety versus liveness.

**Safety** — *never `unstack`*, *never touch block c*, *at most 3 steps*. Violated by a prefix means
violated by every extension, so a breach is a proof that the branch is dead. It prunes, and prunes
*before* the step is imagined, so a forbidden action costs nothing at all.

**Liveness** — *the plan must include a `paint` step*. A prefix without it is not in violation,
merely unfinished. It is checked only when the world constraints are met, and it must never prune.

Getting this backwards fails in both directions: defer a safety constraint and the search burns out
on branches that died at step one; prune on a liveness constraint and nothing survives.

Liveness also changes what counts as the same search node. Two routes to the same world differ if
one has already done a required action and the other has not, so the visited-set key is the state
*plus* what is still outstanding. Deduping on the world alone silently discards the finished route.

## Relevance is read off the rule's body

Nothing declares effects. A function *is* graph data, so what it could make true is read from its
stored instructions, and it cannot fall out of date with the body because it *is* the body.

Effects carry their roles: `stack` links *its parameter `b`* onto *its parameter `onto`*. Without
that, `stack(b=b, onto=a)` would look as good as `stack(b=a, onto=b)` for the constraint "a on b".

The same reading unions in each declared outcome's effects, which is how the planner learns things
the signature cannot express. `scan_dir(d: dir) -> listing` mentions no file and its body is a single
dispatch; the fact that listing a directory produces files lives in the **mock**. So a goal of "some
file must exist" finds the call.

When a body cannot be read — because it calls out to something opaque — the reader says so, naming
the role it could not resolve, rather than reporting a confident empty answer.

### Rank a guess; prune a proof

Relevance only ever *orders* candidates. On Sussman's anomaly (C on A; want A on B and B on C) the
plan must *start* with `unstack`, a move that closes no constraint and therefore scores low. A greedy
means–ends planner that only tried constraint-closing moves would be stuck. Because relevance only
orders, the move stays reachable and the plan is found in three steps.

A safety breach is different in kind: no continuation of a plan that used a forbidden action makes it
unused. That is a proof, so it prunes. The rule generalises across the whole engine — relevance,
guidelines and criteria are guesses and may only reorder; prohibitions and budgets are proofs and may
exclude.

Measured against the identical breadth-first search on a three-crate tower: two to three imagined
states guided, against fifty-three to eighty-seven blind, with the same optimal plan. Both figures
are ranges because tie-breaking varies between runs; the plan is invariant.

## Imagining on a workbench

Backward chaining over declared types concludes that applying `service` to a car yields a serviced
car. That is a promise, not a proof, and it says nothing about what *else* changed — which the next
step may depend on. So type chaining is a good way to **propose** a chain and a bad way to
**believe** one. The workbench runs the proposal somewhere that does not count.

**The copy boundary is everything reachable from the subject.** Every cleverer boundary is a guess
about which structure will matter, and a wrong guess yields a plan that looks fine and fails on
contact with reality. Copy-on-write, if it is ever needed, implements exactly these semantics more
cheaply; it is not a smaller boundary.

**Mappings are the crux.** A mapping points at the original and at this frame's image, and chains to
the next frame. A transformation binds its arguments to *mappings*, never to raw workbench nodes,
which is what makes a plan replayable: following `original` yields the node the operation must really
be applied to. A log saying "`service` was applied" is unreplayable, because it does not identify the
subject in a form that survives out of the workbench.

Two invariants keep this from going wrong.

*Metadata points inward.* A mapping points to the original and the image; nothing points from a node
to its mappings. Copying traverses outgoing edges, so one edge the other way would drag in that
mapping's original, image and successor — and thence every frame, every workbench, every plan
touching that node. The failure is not a wrong answer but an unbounded copy. A check scans every edge
for it and is itself verified against a planted violation.

*Scans exclude workbench copies by default.* Copies are ordinary nodes, so an unfiltered scan would
find the system's own imaginings and offer them as candidate arguments — planning about the products
of planning, with no error and no symptom beyond gradually stranger plans.

**Frames form a tree.** Steps extend a path; assumptions fork it. Successor edges are one-to-many on
frames *and* on mappings, so a node's own history branches with the frames it lives in.

Nesting and forking are different axes. Subgoal exploration **nests** — a workbench inside a
workbench, a new copy scope, with resolution walking one level up. Assumption branching **forks the
frames** inside one workbench, because all branches imagine the same world differently.

## Mocks: a call can turn out several ways

A function has many mocks, each an ordinary rule whose **return type is the outcome it assumes**, so
the existing type-chaining planner plans each case differently with nothing added:

```
fn list_dir(d: dir) -> listing:                              # reaches the world
fn list_empty(d: dir) -> empty_listing mocks list_dir:       # assume nothing there
fn list_full(d: dir)  -> full_listing  mocks list_dir:       # assume plenty
```

Declaration order is preference order, free, because mocks hang on an ordered edge. That is
deliberately the weakest thing that works. Something has to decide the default, or it is whichever
mock happened to be declared first by accident rather than by intent.

Choosing an outcome is making an assumption, so the transformation records a hypothesis, and
`fragile_steps` answers "which parts of this plan are guesses" as a lookup rather than a judgement
someone has to remember to make. Forking on a different outcome gives two worlds side by side, and
contingency plans come free from having explored both.

Two mechanisms are at work here and must not be conflated. On a workbench, a function with declared
outcomes is *substituted* by one of them — that is what makes planning **useful**. What makes it
**safe** is separate: the dispatcher refuses an imagined target outright. If substitution were ever
forgotten or bypassed, a dispatching function still could not reach the world. The refusal is checked
before any veto, since an imagined target's prohibitions are imagined too.

A mock is never proposed as an action. It is an assumption about how a real call turns out, so
planning one would be planning to *assume*, and would name a function that must never really run.

## Expectations — what the type cannot catch

A plan step predicts more than a type. `workbench.predicted_changes` **derives** that prediction from
the two frames the workbench already holds — frame N−1 and frame N *are* the before and after — so
nothing is authored and nothing is stored.

```
DIVERGED at scan_dir
  it had assumed: scan_dir turns out listing
  expected some 'file' edge, found none
  expected some new file node, found none
```

Expectations are **qualitative, never quantitative**. A mock that mints two file nodes is giving a
witness, not a promise: a listing produces a variable number, and diverging on three-instead-of-two
is diverging on noise. The expectation is existential — *some* file exists. One file and five both
complete; zero diverges.

The division of labour: the declared return type carries the discriminating claim (empty versus
non-empty) and is checked by the cast; the derived expectation carries the qualitative shape of the
change. An expectation never re-checks what the type checks, so a failure is reported once.

Expectations are also **conditioned**. What a call is expected to do can depend on the state it is
made in, so the same unedited mock can predict two different things in two different worlds.

## Two planners, two questions

Both exist, and neither is a defect in the other.

**Backward chaining over return types** asks *what sequence of casts reaches this type?* It does no
imagining, is cheap, and is right when operators form a pipeline of distinct stages. The result is a
chain of **pending calls that nothing has executed** — a plan that is data, comparable against a
rival, hypothesisable, or handed to a model to critique, all before anything happens. Exploring it is
simply not calling `run`; there is no mode to be in.

**Forward search on the workbench** asks *what do I get if I try this, then this?* It keeps a frame
per step and is right when the same operator applies repeatedly and the interesting thing is the
resulting state. Backward chaining structurally cannot express repetition — a function has one
declared return type, so "stack a block, then stack another" is not a chain of distinct casts.
Repetition comes from the loop.

**The plan is found, not built.** The path from the workbench root to the frame that satisfies the
goal records every state imagined and every transformation that reached it, so it is already
replayable. There was never a plan-construction step to write.

```
plan found in 3 step(s) after imagining 50, goal: A on B on C [a on b, b on c] — MET
  unstack(b=c, floor=ground)
  stack(b=b, onto=c)
  stack(b=a, onto=b)
```

Binding search — proposing *which arguments* to try — lives with the forward search rather than in
candidate generation. Deciding what could apply to one node is bounded matching; inventing bindings
is search, and hiding search inside candidate generation would misplace it.

## Following a plan for real

Everything execution needs was already recorded, which is what mappings and transformations are for
rather than a log: the **real** function (stored separately from the mock that was imagined), the
**mappings** (which resolve to real nodes), and the **expected type**.

```
--- executing the branch that assumed 'empty' ---
ran: list_dir
DIVERGED at list_dir
  it had assumed: list_dir turns out empty_listing
  expected empty_listing, but: {'@count': ('0', 'None')}

contingency already explored: ['full_listing']
```

**Fail fast, and do not roll back.** Execution stops at the first step whose real result fails the
cast it promised, because everything after it was planned on the assumption that it held. Nothing is
undone: real effects have already left the graph, and pretending a journal could reach them would be
worse than not having one. The honest output is "these ran, this diverged, here is how".

Deviation is a failed cast, checked against the type the transformation recorded. That is cheap and
meaningful, and it reports *how* it deviated rather than merely that it did. Comparing whole
subgraphs would let irrelevant differences swamp real ones; the expected type is the honest signal
because it is exactly the promise the function made.

**Imagined nodes are bound by provenance.** A step may mint something that did not exist at planning
time; its mapping has no original, and the real counterpart is matched by *which transformation
produced it* — the only correspondence available. Matching within a transformation is by kind and
order, so if one transformation mints two nodes of the same kind the pairing is a guess, and the
report says so rather than choosing silently.

## Recovering from a divergence

Once a step has diverged there are exactly two honest moves, and the choice between them is made on
the structure rather than on a policy.

**Resume — was this outcome already explored?** A fork exists precisely because someone thought a
call could turn out more than one way. Each sibling is asked the same question that detected the
problem — does the real result deviate from *that sibling's* own promise? — and a sibling that
survives is a plan for the world we are now in, already imagined and already checked. Continuing down
it is not replanning; it is following the contingency the fork was for. This is tried first on
evidence rather than taste: a matching branch is verified against this world and a fresh proposal is
not.

Two things make resuming safe. The diverged call is **not re-run** — it reached the world once, and
running it again would double its effects. Its real outcome is instead settled onto the chosen
branch's own mappings, carried from the shared parent frame, including anything the call minted,
since a branch may refer to a node that did not exist at planning time. And the sibling must be the
**same function**: siblings are alternative *successors*, which need not be alternative *outcomes*,
and resuming into a fork that tried a different action entirely would silently skip a call that never
ran and then report success.

**Replan — nothing explored fits.** Then the branch tree has nothing to say, and the only sound move
is to propose afresh from the world as it actually is, taking the diverged step's real result as the
subject because that node *is* the actual state. What comes back is a lazy chain, so re-proposing
still commits to nothing. With no goal to aim at, recovery reports `stuck` rather than inventing one.

Replanning against a goal comes back to the driver rather than to backward chaining. Backward
chaining knows nothing about a goal's constraints; asked to recover a diverged "some file must exist"
it answered *"listing: already satisfied"* — true, and useless. Re-pursuing the goal is the only
recovery that means anything, and it needs no new state.

## The loop closed

```
attempt 0: planned ('scan_dir',) -> ran ('scan_dir',), completed=False
   DIVERGED at scan_dir | expected some 'file' edge, found none
attempt 1: planned ('scan_dir',) -> ran ('scan_dir',), completed=True
goal: find a file [something is a file] - MET
```

Plan by imagining, act for real, notice that reality disagrees, replan from where we actually are,
succeed. `driver.carry_out` is that loop.

## Questions are goals

"Is Paul mortal?" is the goal *find out whether Paul is mortal*, and answering it is pursuing it.
There is no second control loop, no query evaluator, and no separate ask/tell duality: a question
hands the search the same constraint nodes any other goal is made of.

**The plan is the proof.** Because the driver finds a plan rather than building one, for a question
that plan is the derivation — the frame path from what is known to the claim being true. An answer
therefore arrives with its justification already in hand, as ordinary graph data, and nothing has to
reconstruct why afterwards.

Three verdicts, and the third is not a failure:

* **yes** — derived, or already known.
* **no** — something incompatible holds *now*. This is a stronger claim than failing to derive.
* **unknown** — nothing derived it. A failed search has learned about its own library, not about the
  world. Closing the world is a **stance** passed per question, never a property of the machinery.

**A derivation may never act.** Concluding and doing are both "running a rule" here, so a rule may be
used to answer a question only if it provably never dispatches, read off its stored body and
transitively through its calls. That is a proof, so it prunes, and it is deliberately conservative in
the refusing direction: a body that cannot be read is barred.

**Asking changes nothing.** The derivation runs on a workbench, so asking whether the salt is sealed
does not seal it. Answering then *settles* the verdict so the next question need not re-derive it,
and that settling is what later makes an explanation possible.

The route constraints work in a question too. `never phone_the_registrar` asks *can you establish
this without reaching outside?*; `at most 2 steps` asks *is it derivable in two steps?* Constraining
the route is constraining the route, whether the route is a plan or a derivation.

## Explanations that refuse to be invented

```python
I.respond(g, "why is the salt sealed?:\n    salt.sealed = true", th)
# salt.sealed = True: because seal(j=salt) ran
```

Three honest answers — *derived here*, *true but given*, *not true at all* — and a deliberately
absent fourth. For a fact that already holds with no recorded history, a fresh search would happily
produce "here is a way this could follow". That is a fine answer to a different question and a lie as
an account of history, so the machine says it does not know, and redirects to the question that does
apply. An engine that manufactures plausible history makes every explanation untrustworthy.
