# Mediated access

**A design note, not a spec. None of this is built.** It records an argument, the measurements that
constrain it, the alternatives already ruled out, and the questions still open — so the next pass argues
with a document rather than reconstructing a conversation.

## Two demands, one mechanism

Two unrelated-looking needs turn out to want the same thing, and conflating them has already caused one
wrong turn in the reasoning, so they are separated here first.

**Meaning.** A rule that says `GET F(b) "on"` has flattened *the support of b* into an edge traversal.
The relation is gone as a relation: nothing can ask what the rule was about, only what it stepped
through. The open class of language is a net, and much of what a sentence says is expressible only as
something else — so the intermediate names are not decoration, they *are* where meaning lives. Lower
past them and the web is lost.

**Transparency.** Planning wants to read over a partially modified graph — to see a frame's version of
the world without every rule knowing what a frame is. That requires every access a rule makes to be
interposable. Not most of them: **every** one, or the answer is silently wrong.

The same abstraction serves both, which is why they were conflated. They pull in opposite directions,
which is why they must not be.

## Lowering stops above the instruction set

The decisive move is that a rule is lowered to a **named call**, never to an opcode.

A call survives compilation: `INVOKE` stores the function's *name*, so `driver.establishes` and
`driver.reads` can walk a stored body and see what it calls. An opcode does not survive in the same
sense — `GET` is a traversal, and the thing it was a traversal *of* is gone. So the call graph is the
semantic net, and lowering past a name is exactly where a thing stops being in the web.

Lowering to a name also separates **compilation from linking**. Which implementation a name resolves to
is decided at run time, not baked in when the rule was written. That is what lets the machinery change
what a read *means* — resolving a version, recording provenance, checking a permission — without
touching a single rule. The mechanism is already proven here rather than speculative: `INVOKE` resolves
a name through a register, `find_function` exists, and mock substitution already replaces a function at
invocation with neither caller nor callee knowing.

## Three layers, and why it cannot be two

| layer | membership | totality |
|---|---|---|
| kernel | the instruction set | closed |
| **mediated access** | ~9 names, below | **closed, and must be total** |
| domain vocabulary | `support_of`, `wheels_of`, … | open, incomplete by design, **and may contain no natives** |

**Totality is unobtainable from an open class**, and that single fact forces the middle layer. The
domain vocabulary is open and will never cover everything — that is the islands finding, and it is the
same point as *some things are only expressible as something else*. Transparency needs the opposite: one
unmediated access and planning over a partially modified graph gives wrong answers. So mediation must
bottom out in a closed set, with domain names implemented *in terms of* it rather than instead of it.

This is [the horizon's three layers](concepts.md) arriving from a new direction, which is some evidence
it is the right cut.

## What rules actually touch

Measured, not imagined. Every authored rule in the self-test corpus — `stack`, `unstack`, `paint`,
`service`, `wash`, `list_dir` and its mocks — reaches the graph through six operations, plus two for
many-valued relations and one to mint:

| name | replaces | note |
|---|---|---|
| `slot_of(node, key)` | `ATTR` | |
| `set_slot(node, key, value)` | `SET` | |
| `related(node, label)` | `GET` | single-valued |
| `relations(node, label)`, `relation_at(node, label, i)` | `COUNT`, `GET_AT` | count-plus-index, as everywhere |
| `relate(node, label, other)` | `LINK` | |
| `unrelate(node, label, index)` | `UNLINK` | |
| `make(kind)` | `NEW` | a minted node needs a version identity too |

Everything else in those bodies is `ADD` / `LT` / `JMP` — arithmetic and control, which touch nothing
and need no mediation. `DISPATCH` is already mediated by construction: it is the one door out, and it
refuses an imagined target.

The reflection opcodes (`KIND`, `NLABELS`, `LABEL_AT`, `DEREF`, `SETREF`, `NEPROPS`, …) appear **only**
in substrate programs — `reachable`, `copy_set`, `open_workbench`, `step`. So the layer line is not a
new rule to impose; it is where the code already sits.

## What stays bare, and why it is a layer rather than a list

Programs below the workbench abstraction keep the bare instruction set: `reachable`, `copy_set`,
`carry_frame`, the reflection walks. Two reasons, and the first is the principled one.

They operate on **structure**, not on world content. `copy_set` copying a node's edges is not a claim
about the world that could be true in one frame and false in another; it is machinery moving structure
around, and there is nothing for a version to mean.

And routing them through mediation would tax the machinery being made affordable — an injected read
measures at 2.9× a bare one, and `copy_set` performs thousands.

Stated as a *layer* this is a rule anybody can apply. Stated as a list of exceptions it is a judgement
call somebody must remember, which is the defect shape this codebase keeps recording.

## Governance: the two demands are enforced differently

The consequence of totality-versus-coverage, and the practical half of the whole note:

* **The closed set must be enforced.** A bare graph-touching opcode in a business rule is a defect, and
  a compliance pass over stored bodies can say so — the bodies are data, and `driver.reads` already
  walks them. Missing mediation produces wrong answers.
* **The domain vocabulary just grows.** A missing name costs expressiveness and nothing else.

Two demands, one mechanism, two governance regimes. Expecting one policy to serve both is the error this
note exists to prevent.

## Recording comes free

A worry that turned out to be unfounded, recorded so it is not re-raised. Substitution in this codebase
is supposed to be a *claim*: choosing a mock outcome becomes a hypothesis on the transformation. Late
binding looked like substitution with no record. It is not — an activation already carries `of`, naming
the function that actually ran, so *what did this rule really do* is answerable by walking the
activation, exactly as it is for a mock.

## Measurements that constrain the design

| | |
|---|---|
| injected read vs bare `GET` | **2.9×** — cheaper than assumed; time is not the obstacle |
| nodes minted per injected read | **~5** — an activation, a focus, its heads and registers |
| interpreter cost per instruction | **~50–90 µs** — activation state is graph-resident and journaled |

The middle row is the one that bites, and it is not about speed. `function.invoke` runs with
`retire=False` so a caller can ask what its call did. If reads become calls, that default litters the
graph with interpreter scaffolding — and this system has already once mistaken its own scaffolding for
world content and type-checked it as a domain object. **Retention must become a call-site choice**
before reads become calls.

## What the mediation is for: frames as markers

The representation this serves, because the vocabulary above is only worth its cost if this works.

**A frame points only at what changed in it.** Structurally that is what exists today —
`frame -mapping-> mapping(original, image)` — and *nothing about the shape changes*. What changes is the
density: today every node in the world gets a mapping in every frame; here only the changed ones do.
Reading becomes: look for a mapping in this frame, and failing that walk up the frame chain.

So a frame stops being a **container** holding a copy of everything and becomes a **marker** — the point
in a branch's history that versions are stamped against, and the thing resolution walks up. That is the
linear thread of changes without which per-node before-and-afters have local order and no global one:
`mapping -next-> mapping` orders one node's versions, `frame -next-> frame` orders the world's.

**Edges are not separately versioned.** An edge belongs to a node-version, so changing `b -on-> c` into
`b -on-> a` mints a new version of `b` carrying its whole edge set, and edge properties ride along on the
copy exactly as `copy_set` already carries them.

**And the rule the whole scheme rests on: an edge points at a canonical identity, never at a version.**
Resolution happens at read time, on the *target*. This is what makes the sparse frame correct, and it is
what the *Ruled out* entry below gets its correction from — with identity-pointing edges there is no
cascade, because a hub's edges name identities that never change however often their members do.

Three consequences, one of them unfinished:

* **Resolution walks the frame chain, not the graph.** Cycles in the world are irrelevant to it and
  termination is trivial — unlike `path.reaches`, which needs a seen-set. Measured depth on Sussman's
  anomaly: **5**.
* **A high-degree node that changes copies all its edges.** Fine in evidence — what changes is blocks,
  not hubs — but it is the shape to watch. If it ever bites, that is when edges would need their own
  identity, and since edges gained one they could have it.
* **A node minted while imagining is its own identity**, and needs no mechanism. It is a first version
  with no earlier one: minted in frame N, inherited by every later frame by the same walk that resolves
  anything else. That is uniform with a real node, whose identity is the real node and whose first
  version appears in frame 0.

  This was nearly over-built into a minted placeholder — a plan variable, a skolem — before the question
  *what is it for* was asked. What it is for is not chaining: **a goal constraint can be existential**,
  and `goal.holds` for a subject-less type constraint enumerates `instances(type, under)` over the
  frame's world. So invented nodes must persist across frames or *there is a file* stops reading as
  satisfied one step after it became true. Persistence is the whole requirement, and identity-as-first-
  version delivers it for nothing.

  One consequence: `is_imagined` currently asks *does this mapping lack an `original`*, and would ask
  *is this its own original* — an absence becoming a positive fact, which is the direction this codebase
  prefers anyway.

## What the branching measurement rules out

The alternative worth taking seriously was to mediate **writes** instead of reads: keep the node id
always holding the latest value and push the old one into a *before* record. Reads would stay bare —
which dissolves the totality burden, the natives question and the per-read cost at a stroke — and it
would match the runtime, where the world is the present and history is the thread.

It does not survive the measurement. An undo log assumes one live present; the search does not have one.
On Sussman's anomaly:

| | |
|---|---|
| imagined steps | 50 |
| stepped frames that fork | **16 of 17**, branching factor mostly 4 |
| max chain depth | 5 |
| copies still needed if copying on fork | 33, against 50 today |

The driver enumerates a frame's whole product of applicable actions eagerly, so alternatives are
materialised rather than explored one at a time. Trail-and-undo pays off only if the search is
serialised, and serialising it is a far larger change than anything here. The saving would be a third,
and it would not scale, because every fork copy is still O(world).

Versions scale with *change* instead: ~2 changed nodes per step, so 50 steps costs ~100 node copies
against today's 50 × world — 100 versus 250 in a five-node world, 100 versus 2250 in a forty-five-node
one. **Branching is the argument for mediating reads and against mediating only writes.**

## The binder: dynamic scope over the activation chain

Something has to decide which implementation a name resolves to. This is the design's main question and
it now has a recommended answer, recorded here with the argument rather than as a verdict.

**A registry is a catalogue, not a binder.** `native.py` answers *what implementations exist*, and it is
a fixed table. It cannot answer *which one now*, because a search holds many branches alive at once and
there is no single "now". So a registry is necessary and insufficient, and the real choice is between
threading the context through every signature and finding it dynamically.

**Recommended: dynamic scope, with the context on the activation and inherited through the `caller`
chain.** The argument that decides it is specific to this engine. Dynamic scope is normally a bad trade
because you cannot see what a function will do without tracing the stack, and the stack is not data.
Here it is: every activation points at its caller, `activation.chain` walks it, and *what context was
this running under* is an ordinary query. The usual opacity is precisely the thing this engine does not
have.

Three consequences follow, and each is a cost that would otherwise have to be paid:

* **Learning is untouched.** With threading, `application.generalise` must know that one parameter is
  special, or every learned rule is welded to whatever context was in scope when it was recorded. Under
  dynamic scope a learned rule never names a context, so it is context-neutral automatically. The
  problem does not get solved; it stops existing.
* **Natives get it for free.** `native.call` already passes `act` to every primitive whether it wants it
  or not — deliberately, because a registry recording which primitives take context would be a second
  thing to keep in step. So `types.is_a` can resolve as it walks. Under threading, every native call
  site would have to pass the context explicitly.
* **The cost is per call, not per read.** An activation inherits its caller's context pointer once, at
  `open_activation`. Nothing walks the chain per access.

**The objection, and why it survives.** `INVOKE` deliberately gives a callee a fresh focus with none of
the caller's heads, so *a function is never silently sensitive to where its caller happened to be
looking*. Inheriting context looks like the same mistake in another dimension, and the answer is not
that attention and linking are merely different things. It is that **the call chain and the frame nest
identically — a callee always runs in its caller's frame — whereas attention does not nest**, because a
callee looks at its own arguments and not at its caller's. Frame is a property of the dynamic extent;
attention is a property of the call. Inheriting the first is the correct semantics; inheriting the
second would be the accident `INVOKE` guards against. Whoever builds this should state that where a
reader will meet it, because it will otherwise read as a contradiction.

**The design rule that falls out: inherit by default, establish explicitly at the boundary.** `step`
does not inherit — it *establishes* the new frame's context for the call it makes. Which is a good sign
about the cut: `step` is already the mediation point today, doing it by materialising at bind time. The
seam does not move; only the mechanism at it changes.

**Boundaries nest, and there are more than two.** The goal machinery establishes the coarse fact — *we
are planning, in this workbench* — at the point where it selects a rule and hands it over; `step`
refines that to a particular frame; a nested workbench nests its context exactly as it already nests its
`original` pointers, where `resolve` is already a walk. Dynamic scope handles all of it natively:
establish, inherit, re-establish deeper. This is the original argument for the whole approach arriving
at its conclusion — the subsystems that already manipulate rules are the ones that configure them, and
a rule is never edited to say which world it is reading.

**And `execution` is a boundary too, which removes the last mode from the design.** The real world is
not the *absence* of a context; it is the **trivial** context, the one whose resolution is the identity
function. `execution` establishes it, and the same rule runs there unchanged.

That is what makes *one rule set* true rather than aspirational. There is never mediated-versus-
unmediated execution to branch on, no rule that has two behaviours, and the failure mode is uniform:
forgetting to establish is the same bug in the same place whether the system is planning or acting.

**Two risks this buys, both wanting artifacts rather than assumptions.**

A native receiving `act` does not mean it *uses* it. A native that ignores context is a silent hole of
exactly the same class as a bare `GET` in a rule. So natives need their own compliance question, and
*every native was audited for whether it needs context* has to be a recorded artifact.

And establishing a context becomes a thing that can be forgotten. If `step` fails to establish,
everything beneath it silently inherits the caller's frame and plans in the wrong world. That is the
failure mode dynamic scope buys, and it wants a check that goes red when a boundary does not establish —
not a convention that a boundary should remember to.

## Ruled out, with reasons

**Edges that point at versions.** Not merely awkward — incorrect, and this is the trap that cost the
most reasoning. If an edge names a version, a new version of `Y` makes every `X -on-> Y` stale, and
re-pointing cascades to every transitive predecessor. Measured on a real planning run: with 43 blocks, 2
images change content and **43 of 45 would have to be re-pointed**. Persistent data structures escape
this by being trees with one root; a graph with a hub node and cycles has no such bound.

⚠ **This rules out version-pointing edges, and nothing else.** It was first read as ruling out sharing
altogether — which closed the whole thread for a while — and that was wrong. With edges naming
canonical identities and resolution at read time, the cascade does not arise at all: a hub's edges name
identities that never change however often their members do. The measurement is real and the inference
drawn from it was not.

**Copy-on-write inside `SET` / `LINK`.** Puts frame-awareness into the kernel; a port would have to
re-make the decision.

**Two lowered forms, one per context.** Loses composability by making the *pair* the unit: anything
reasoning about a rule would have to know which form it had. One artifact whose linking varies is
strictly better than two artifacts that must be kept in step.

**Keeping the workbench in Python.** Planning that Python owns is planning the system cannot inspect or
change. Not available at any price.

## Decided: no member of the open vocabulary may be native

A domain name is normally an ordinary procedure — `support_of(b)` is a body containing
`related(b, "on")` — and is mediated automatically, because everything it does goes through the closed
set. The alternative is to register it in Python, so `INVOKE support_of` reaches a function that walks
the graph directly. The reasons anyone would are real: speed, or a concept needing something procedures
cannot do — a numeric routine, a lookup against data held outside.

**It is forbidden anyway, and the argument is the totality one.** A native reads raw structure and
bypasses mediation. The seven natives can be audited because there are seven; the domain vocabulary is
*open*, so its members could never be enumerated and the audit could never be finished. One escape
hatch and the guarantee is gone.

The escape that remains costs nothing: if a domain concept genuinely needs a primitive, that primitive
joins the **closed** set and is audited like the others. Reaching outside the system is already
`DISPATCH`'s job, and is mediated by construction.

Stated as an invariant: **natives are a closed class; the domain vocabulary is an open class; an open
class may not contain natives.**

## Open questions

**1. May a plan act on something it invented?** *"List the directory, then read the first file"* is
obviously wanted eventually, and the machinery half-exists: `enumerate_frame` draws candidates from
`W.mappings(g, frame)`, which includes imagined ones, and `_bind_minted` exists to tie them to real
nodes at execution. But **nothing in the corpus does it** — the one minting mock is used only for
expectation checking. So this is latent capability, and it should be decided as a planning question on
its own terms rather than settled as a side effect of the versioning work.

⚠ It carries a known defect with it. `_bind_minted` matches planned nodes to real ones **by kind and
order**, and says so — *"ambiguous: N real X nodes for a planned one — paired by order"* — while
`activation.minted` notes that changing its sort *"would silently change which imagined node binds to
which real one"*. A positional pairing over a string sort decides which real file the plan meant. That
is recorded here as a defect to fix **when the capability is taken up**, not to fix under cover of this
work.

**2. Whether the phase machine establishes anything.** `execution`, `step`, the goal machinery and
nested workbenches are settled above. The phase machine appears to orchestrate and inherit, but that has
not been looked at, and every boundary is a place the establish-or-silently-inherit failure can occur.

## The natives inventory

Every registered native, and whether it must find the context. The mechanism is settled — `native.call`
hands every primitive its activation — so this is the list, not the design. It is recorded because **a
native that quietly ignores context is indistinguishable from one that correctly does not need it**, and
that is the likeliest place for this whole scheme to be silently wrong.

The test is not "does it touch the graph" but **does it traverse world content whose value depends on
which frame you are in**.

| native | owner | context? | why |
|---|---|---|---|
| `is_a` | `types` | **yes** | walks the node's edges *and its neighbours'* to check a schema; every hop needs resolving |
| `check` | `types` | **yes** | `violations` then raise — the same traversal as `is_a` |
| `plan` | `driver` | **yes** | opens a workbench on a subject, so it reads world structure to copy it |
| `plan_step` | `driver` | **yes** | steps a search; frames are its whole subject matter |
| `find_function` | `function` | no | resolves a name against the function index; functions are not world content and are not versioned |
| `minted` | `activation` | no | reads `minted` edges off an activation — interpreter state, not world content. It *returns* world nodes, but as identities, which is what the caller wants |
| `after` | `loop` | no | reads the agenda off its own activation and mints a moment; touches no world content |

Four of seven. The two `types` entries are the load-bearing ones, because `is_a` is on the hot path of
every proposal and every guard.

**`after` is also the precedent for the binder**, and worth reading before building it: it already finds
the agenda it is on by walking from `act`, and its docstring gives the reason natives are handed one at
all — *"a body that had to be told which loop it was running on would be a body that could not be
moved."* That is the dynamic-scope argument, already made, already built, for a different context.

## Where this came from

Recorded because the reasoning is worth more than the conclusion, and because two of the numbers above
were got wrong first.

The thread began as a performance question — the surface `workbench.step` measured 25× the Python one,
with essentially all of it in the per-node frame copy. That framing produced a wrong recommendation
twice: first that sharing versions would save ~96% of the copying (it would not; unmediated sharing is
incorrect, and the cascade measurement is in *Ruled out* above), then that the copy was therefore
load-bearing and the thread should be closed (it is not; that argument only defeats *unmediated*
sharing).

What actually settled the shape was two constraints that are not about performance at all: **the
workbench cannot stay in Python**, because planning Python owns is planning the system cannot inspect;
and **lowering must stop above the instruction set**, because a name is where meaning lives and where
linking can still happen. Given those, mediation cannot be in the kernel and cannot be in Python, and
in-graph procedures are not one option among several — they are the only place left.
