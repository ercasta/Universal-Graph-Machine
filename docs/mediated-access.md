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
| domain vocabulary | `support_of`, `wheels_of`, … | open, incomplete by design |

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

**Two risks this buys, both wanting artifacts rather than assumptions.**

A native receiving `act` does not mean it *uses* it. A native that ignores context is a silent hole of
exactly the same class as a bare `GET` in a rule. So natives need their own compliance question, and
*every native was audited for whether it needs context* has to be a recorded artifact.

And establishing a context becomes a thing that can be forgotten. If `step` fails to establish,
everything beneath it silently inherits the caller's frame and plans in the wrong world. That is the
failure mode dynamic scope buys, and it wants a check that goes red when a boundary does not establish —
not a convention that a boundary should remember to.

## Ruled out, with reasons

**Sharing versions without mediating reads.** Not merely awkward — incorrect. A node id conflates *which
node* with *which version*, so a new version of `Y` makes every `X -on-> Y` stale, and re-pointing
cascades to every transitive predecessor. Measured on a real planning run: with 43 blocks, 2 images
change content and **43 of 45 must be re-pointed**. Persistent data structures escape this by being
trees with one root; a graph with a hub node and cycles has no such bound.

**Copy-on-write inside `SET` / `LINK`.** Puts frame-awareness into the kernel; a port would have to
re-make the decision.

**Two lowered forms, one per context.** Loses composability by making the *pair* the unit: anything
reasoning about a rule would have to know which form it had. One artifact whose linking varies is
strictly better than two artifacts that must be kept in step.

**Keeping the workbench in Python.** Planning that Python owns is planning the system cannot inspect or
change. Not available at any price.

## Open questions

**1. Which natives need context.** The *mechanism* is settled by the binder above — `native.call`
already hands every primitive its activation, so a native can find the context and resolve as it walks.
What is not settled is the inventory. `types.is_a` walks a node's edges and its neighbours' to check a
schema, so it plainly needs it; `find_function` resolves a name against the function index and plainly
does not. Every native in between has to be decided one at a time, and the decision recorded, because a
native that quietly ignores context is indistinguishable from one that correctly does not need it. This
is work with a known shape rather than an open design problem, but it is the work most likely to leave a
silent hole.

**2. Does the domain layer participate in mediation, or only consume it?** If `support_of` is an
ordinary procedure over `related`, mediation is automatic and there is nothing to decide. If a domain
name may be implemented natively, it opens a second hole of exactly the shape of question 1 — and unlike
the native inventory, the domain vocabulary is *open*, so the hole cannot be closed by enumeration. The
cheap answer is probably to forbid it: a domain name is a procedure, and anything wanting to be a native
belongs in the closed set where it can be audited.

**3. What establishes a context besides `step`.** `step` is the obvious boundary. Whether `execution`,
the phase machine, or a nested workbench are others has not been examined, and each one that is a
boundary is another place the establish-or-silently-inherit failure can occur.

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
