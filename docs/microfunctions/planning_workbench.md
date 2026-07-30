# The planning workbench — imagining effects, and the six things that make it tricky

**Status: design, 2026-07-30. Nothing built yet — deliberately.** This exists because the planner in
`microfunctions/plan.py` chains *declared types* symbolically, and that was correctly identified as
insufficient: to plan properly the system has to **imagine the actual effects** of running microfunctions,
which means running them somewhere that does not count.

The requirement, as stated: copy a subgraph under a planning workbench; run functions on it; each execution
produces a frame, frames connected by transformations, like a movie; keep that record so the plan can later
be *followed* and deviations detected; replace real tool calls with mocks that materialise the expected
effect; and bail out by scrapping the workbench and copying again.

All of that is right. This document is about the parts that do not fall out for free.

---

## 0. What is actually wrong with the current planner

Worth being precise, because it determines how much of `plan.py` survives.

`plan.py` reasons that if `service` is declared `car -> serviced_car`, then applying it to a car yields a
serviced car. That is a claim about the *type*, and it is all the planner knows. Two things it cannot know:

- **Whether the function will actually succeed** on this particular subgraph. The declaration is a promise,
  not a proof; a function can be given a well-typed argument and still fail, or achieve its cast in a way
  that matters for the next step.
- **What else changed.** A cast to `serviced_car` might also set a cost, consume a part, or link a record.
  The next function may depend on exactly those, and the type says nothing about them.

So backward type-chaining is a good way to **propose** a candidate chain and a bad way to **believe** one.
The natural division: keep `plan.py` as the proposer, and add the workbench as the verifier that actually
runs the proposal and reports what really happened. That also means the workbench does not replace
backward chaining — it grounds it.

---

## 1. The copy boundary — the genuinely hard one

*"Copy all the nodes and edges reachable from this node"* is not implementable as stated. In a connected
knowledge base, reachability from anything approaches everything: a car reaches its owner, who reaches
their employer, which reaches every other employee. Transitive closure is not a boundary.

Four candidate policies, and I think one is clearly right:

**(a) Depth limit.** Simple, and arbitrary in a way that will silently truncate exactly the structure some
function needed.

**(b) Follow edges, stop at references.** The substrate already distinguishes these: an **edge** is a
relation the graph asserts, a **`Ref`** is a stored pointer. Copying could follow edges and never follow
references. Appealing, and free — but it loads a boundary meaning onto a distinction that was drawn for a
different reason, and it breaks the moment someone models `car --owner--> person` as an edge, which is the
natural thing to do.

**(c) ⭐ The type schema is the boundary.** A `car` is declared as a body and four wheels. That declaration
is *already* a statement about what the thing is made of. So copy what the type says it consists of, and
stop. This is principled, reuses data that already exists, is authored rather than inferred, and — the part
that makes me confident — it puts the boundary in the same place the *type check* puts it, so a copy is
guaranteed to satisfy the same type as its original. If the schema says a car is body plus wheels, then a
copy of body plus wheels is a car.

**(d) Declared per edge label** (composition vs. association, the UML distinction). More precise than (c),
more to author, and mostly redundant with it.

**RESOLVED: everything reachable from the root.** None of the clever boundaries survive the honest
objection to them — **we genuinely cannot know in advance what a plan will need.** Every policy above is a
guess about which structure matters, and a guess that is wrong produces a plan that looks fine and fails on
contact with reality, which is the worst available failure mode. Schema-driven looked principled precisely
because it *hides* the guess inside something already authored for a different purpose.

The cost is accepted deliberately, and the reasoning is worth keeping:

- Planning is hard for humans too, and humans do not solve it by cleverly bounding what they consider.
- They explore **one option at a time**, so the working set at most doubles rather than branching
  combinatorially.
- Subgoal exploration during planning creates a **stack of workbenches** (§3a), which is the real
  multiplier — and it is unavoidable, not a design choice.
- Optimisation tricks come later, on measurement.

**And the performance worry turns out not to be a boundary question at all**, which is what makes accepting
this easy. Copy-on-write implements *exactly* these semantics more cheaply: everything reachable is
available in the workbench, a node is materialised on first write, and reads fall through to the original.
That is the same boundary, not a smaller one. So the decision here is closed, the cost question is a
separate and deferrable implementation matter, and nothing about correctness depends on when it is taken.

---

## 2. Identity across frames — mapping nodes, and why they are the crux

If a frame is a copy, every node in it has a new id, and three questions need answering: which real node
does this correspond to; which node in the previous frame; and, when the plan is finally executed for real,
which real node does this planned step apply to.

**An attribute is not enough, and the reason generalises.** The obvious cheap answer is `origin` — an
attribute on each copy pointing at the real node. That answers question one, and it is what an earlier
draft of this document proposed. It is not sufficient, because an attribute can only be *read*, and what is
actually needed is something a transformation can **point at**.

**The mechanism: a mapping node.** One node per tracked node per frame, with two outgoing edges — one to
the node in the original graph, one to that node's image in this frame's workbench copy — and a `next`
edge to the corresponding mapping in the following frame.

```
frame0                    frame1                    frame2
 mapping ──next──────────► mapping ──next──────────► mapping
   │ original                │ original                │ original
   ├──────────────► car#7 (the REAL node, shared)
   └─ image ► car#101        └─ image ► car#204        └─ image ► car#310
```

Three things follow, and each is the answer to a question the attribute version could not answer:

- **Replay is possible.** A transformation binds its arguments to **mappings, not to raw workbench nodes**.
  This is the crux of the whole design. At execution time, following `original` yields the real node the
  operation must actually be applied to. A plain log recording "`service` was applied" is unreplayable
  precisely because it does not identify the subject in a form that survives out of the workbench.
- **A node's history is a walk.** "What happened to this node, frame after frame" is following `next` —
  O(1) per hop, no scanning and no grouping. This is the *per-object* movie, as distinct from the
  per-frame one, and it is what deviation-checking will actually consult.
- **The correspondence is annotatable.** A mapping is a node, so a transformation, a deviation, or a note
  about *why* this node changed can hang off it.

### ⭐ The direction invariant: observations point at the observed, never the reverse

**A mapping points *to* the original node and *to* its workbench image. Nothing ever points from a node to
its mappings.** This is not a stylistic preference; it is what keeps copying from destroying itself.

Copying a subgraph means traversing outgoing edges from the subject. If a domain node had an edge to its
mapping, that traversal would reach the mapping, and from there the mapping's `original`, its `image`, and
its `next` — and thence every other frame, every other workbench, and every plan that ever touched that
node. One innocent copy would drag in the entire planning history, recursively. The failure would not be a
wrong answer; it would be an unbounded copy.

**And the constraint is free**, which is the part that makes it easy to keep. The reverse index already
answers the backward question: `sources(real, "original")` gives every mapping pointing at a node in O(1).
So "show me every plan that touches this car" is available *without* a forward edge — the lookup that would
have motivated the dangerous edge is already there.

Stated generally, because it applies to far more than mappings:

> **Structure points outward; metadata points inward.** Anything that is *about* a node — a mapping, an
> application, a hypothesis, a prohibition, a plan step — points at that node and is never pointed at by
> it. Structural traversal (copying, type-checking, subgraph operations) then sees only structure, by
> construction, and never needs a filter listing which kinds to avoid.

The rest of this engine already obeys this, so far by instinct rather than by rule: an `application` points
at its bindings which point at nodes; a `hypothesis` points at what it is `about`; a `forbidden` points
`on` its target; a `pending_call` points at what it `produced`. Nothing points back. That is worth locking
down with a test that scans every edge and fails if any non-metadata node points at a metadata one —
cheap to write, and it catches precisely the regression where someone adds a convenience edge and turns
every copy into a whole-graph copy.

**Two cases the simple picture misses**, both now settled:

**Nodes that exist only in imagination.** A function may mint something during planning. Its mapping has
**no `original`**, which is meaningful rather than broken: it says *this does not exist yet*. What ties it
to reality later is not a pointer but **the transformation that produced it** — which is recorded anyway.
When the plan runs for real and that same function executes, the newly minted real node can be connected to
its planned counterpart because we know which function just ran and which mapping that function's
transformation created. The correspondence is established **by provenance rather than by identity**, which
is the only thing available for something that did not exist when planning started.

**Nodes that disappear.** A function may drop something, and the chain **ends at the transformation that
dropped it** — `next` points to the call, not to another mapping. This is better than a boolean marker for
a reason worth stating: a terminator that names the cause is self-explaining. "This node stopped existing"
and "this node stopped existing *because `scrap` ran at step 4*" are different amounts of information, and
the second is what a deviation report needs. It also removes the ambiguity the marker was there to fix — a
chain that ends in a transformation is visibly finished, where a chain that merely stops could be one
nobody continued.

### 3a. Nested workbenches, and what the stack does to `original`

Subgoal exploration during planning opens a workbench inside a workbench. That is not an optional
refinement; it is what planning a subgoal *is*, and it has one consequence that must be handled rather
than discovered.

**A mapping's `original` points one level up, not necessarily at the real graph.** In a nested workbench,
the "original" of a copied node is the corresponding node in the *enclosing* workbench, which is itself a
copy. So resolving a mapping to the real node is a **walk** — follow `original` until you leave every
workbench — rather than a single hop.

Two things follow. Something must mark where the real graph is, so the walk has a terminator that is not
"the edge is missing" (which is also what an imagined node looks like — §2 — and conflating those would be
a genuine bug). And the depth of the stack is the real multiplier on planning cost, far more than the size
of any single copy: *k* levels of subgoal exploration means *k* nested copies of everything reachable.
That is the number worth measuring first when optimisation eventually comes.

---

## 3. Frames are necessary — the earlier draft was wrong, and precisely why

An earlier draft of this document argued that transformations alone would do, with one live workbench state
and frames materialised only at branch points. That was wrong, and the correction is worth recording
because the reasoning error is instructive.

The claim was not that transformations are unreplayable — with `origin` on each copy they very nearly are.
The claim that failed is subtler: **with only one live state there is exactly one workbench node per real
node, so there is nothing to chain.** "Follow this node frame after frame" has no frames to follow. The
per-object history in §2 — which is the thing deviation-checking actually needs — does not exist at all.
The cheap version answers "what was the plan" but not "what was this thing supposed to look like at step
three," and the second question is the one that matters when reality diverges.

So: **a frame per execution, with mapping nodes tying the frames together.** The movie is real.

**The cost is real too, and is deliberately not being optimised yet.** A copy per step is O(subgraph) per
step. The known lever, when it hurts, is copy-on-write: a frame copies only the nodes its transformation
actually touched, while mappings are still minted for every tracked node so the chains stay uniform. That
preserves everything above and removes the dominant cost — but it introduces aliasing (two frames sharing a
node means a later write must copy before mutating), which is a real correctness burden to take on
speculatively. This project's own standing lesson applies: the last time a named performance lever was
measured it turned out to be 6% of the cost. Build the correct version, measure, then decide.

---

## 4. Mocks are rules, outcomes are assumptions, and that is where hypotheses re-enter

A tool call cannot happen during planning, so a planning run substitutes a **mock**. The important
constraint: **a mock is an ordinary microfunction**, not a special kind of thing. A world rule says, in
effect, *"a `file_list` call produces file nodes"* — and it says it by being a stored function that
materialises them, subject to all the same machinery as any other: typed, inspectable, generated, callable.

**⭐ But a call can turn out several ways, so one mock is not enough.** `file_list` might find no files,
one file, or many, and those are not variations in degree — they lead to genuinely different plans. So a
function has **many** mocks, not one:

```
file_list --mock--> list_empty     -> empty_listing
file_list --mock--> list_one       -> singleton_listing
file_list --mock--> list_many      -> bulk_listing
```

Each mock's **return type is the outcome it assumes**, which is a pleasant consequence rather than a
convention: the type system already distinguishes the cases, and the planner already chains on return
types, so nothing new is needed to plan differently for each.

**Choosing a mock is making an assumption, and an assumption is a hypothesis.** This is the join, and it is
why §7's resolution (hypotheses are *run* via workbenches) turns out to be load-bearing rather than tidy.
A transformation that applied a mock records which hypothesis it assumed, so the plan carries its own
dependence on guesses, explicitly and inspectably. "Which parts of this plan are fragile" becomes a
question you can answer by looking, instead of a judgement someone has to remember to make.

**So the FRAME stack forks, and backtracking is ordinary.** Two axes, and they are deliberately different
mechanisms rather than one:

- **Subgoal exploration nests** — a workbench opened inside a workbench (§3a). A new copy, a new scope.
- **Assumption branching forks the frames** — *within* one workbench. Frame *N* gets several successor
  frames, one per assumed outcome, each reached by a different transformation. No new copy scope is
  needed, because all the branches are imagining the same world differently.

So a workbench's frames are a **tree**, not a list, and "the frame stack" is the current path down it.
Backtracking pops to a fork and descends a different child. The abandoned branch **stays as data**: a dead
end that was explored and rejected is precisely the thing worth not re-exploring, and erasing it throws
that away.

**⚠ One consequence for §2 that is easy to miss: a mapping's `next` also branches.** If frame *N* forks
three ways, a node's mapping in frame *N* has three successors, not one — the per-object history is a tree
too, mirroring the frame tree. This is not a problem (the substrate's `next` is an ordered 1:N edge like
any other, so it costs nothing), but code that walks a mapping chain must expect *targets*, not *a target*.
Written down because "follow `next`" reads as single-valued and would be implemented that way by default.

### ⚠ The thing that will kill this if left alone: do not enumerate

Every uncertain call multiplies branches. Three uncertain calls with three outcomes each is twenty-seven
plans, and that is a small plan. Eager enumeration is not a performance problem to optimise later; it is
the wrong shape, and this project already argued so at length under a different heading — nobody planning a
drive enumerates every possible red light, and no technique changes that, because the domain is open-ended.

The discipline that follows, and it should be the default rather than a mode:

> **Assume the likely outcome, plan forward, and keep the other mocks available *on deviation* rather than
> exploring them eagerly.** Branch only where the cost of being wrong is high enough to pay for it.

Two consequences worth having in view:

- **Which outcome to assume is a selection question**, and a language model at the boundary is well suited
  to it — "given this directory, is it likely empty?" is exactly the kind of judgement it is good at, and
  exactly the kind this engine should not be hard-coding.
- **Contingency plans come free when you do branch.** If reality returns a different outcome than assumed,
  and that branch was explored, the alternative plan already exists. Deviation handling and speculative
  branching are the same machinery, which is a reason to branch deliberately at the few points that
  warrant it.

This also reopens, honestly, a question this repoint had closed: the old engine's possibilistic layer
existed to rank uncertain outcomes. It was cut as machinery solving a problem an LLM already solves. The
weaker thing that does seem needed is a **declared preference order over a function's mocks** — ordinary
authored data, not a band algebra — so the default assumption is not simply whichever mock was declared
first. Worth building only when a case demands it, and worth *not* rebuilding the band layer for.

### The safety property, unchanged and still the most important part

**The substitution must be structural, not conventional.** "Remember to use mocks on the workbench" is the
same class of mistake as "remember to check the prohibition in each rule", which the trigger probe already
showed fails. The dispatcher must **refuse** to dispatch when the target is inside a workbench — one check
in the one choke point, making planning *incapable* of real effects rather than merely disciplined about
them.

One piece of bookkeeping now falls out for free rather than needing care: a mock's products are
automatically distinguishable from real ones, because they live in a workbench under a hypothesis. The
earlier draft required marking them explicitly; the structure marks them.

---

## 5. Deviation detection — reuse the type machinery

When the plan is finally executed for real, each step's outcome is compared against what the workbench
predicted. Comparing whole subgraphs is expensive and noisy — irrelevant differences will swamp real ones.

Cheaper and more meaningful: **a step deviates when its real result fails the cast the frame said it would
achieve.** The transformation already records the expected return type; checking it is `types.is_a`, which
is bounded and already written. Optionally record specific attributes the plan depended on and check those
too, but the type is the honest primary signal — it is exactly the promise the function made.

This also connects cleanly to the old engine's plan-act-check-replan loop: a deviation is an ordinary fact,
and replanning is running the proposer again from the actual state.

---

## 6. The leak that turned out not to exist — and the mistake worth keeping

The worry: `types.instances()` was a whole-graph scan, and workbench copies are nodes, so the moment a
workbench existed the planner would find its own imaginings and offer them as candidate arguments —
planning about the products of planning, with no error and no symptom beyond gradually stranger plans.

**The first fix was wrong, and instructively so.** It stamped every copy with an `in_workbench` attribute
and had scans filter on it, with a test guarding the filter. That is a *labelling* error: it asserts
something the structure already entails, so it can drift out of sync while the structure cannot. It also
added a mechanism, a parameter, and a test — three things to maintain — for a problem that was not real.

**The actual fix is to stop scanning.** Enumerate by traversal from a root, and the leak is structurally
impossible: nothing in the real graph points at a copy (only a mapping does, via `image`), and nothing
points at a workbench (a workbench points *at* its subject). So a copy is simply unreachable from `root`.
Passing a copy as the root enumerates inside that workbench, by the same mechanism, with no special case.

Two things this depends on, both already true and worth naming:

- **The direction invariant** (§2). It is what makes copies unreachable rather than merely unlabelled.
- **Real things hang off `root`.** That is what makes "the real world" a well-defined region rather than
  "whatever happens to be in the dict", and it is what the substrate's single starting node was always
  for.

### The general principle, because this will recur

> **A test that guards a mechanism I added because I did not see the structural answer is a smell. Delete
> the mechanism and the test goes with it. A test that guards a discipline a *human* must follow earns its
> place, because structure cannot enforce it.**

Both kinds are present here, and the difference is clean: the exclusion test guarded machinery (gone, along
with the machinery). The direction-invariant test guards authoring discipline — anyone can later add a
convenience edge from a node to its mapping, and nothing structural prevents it — so that one stays, and
is verified to catch a planted violation.

---

## 7. Hypotheses and workbenches compose — neither absorbs the other

**Resolved.** The question was whether a workbench *is* a hypothesis, given how much machinery they share:
provisional nodes, originals left intact, clean discard, verdict recorded as a fact. Both of the answers I
had framed were wrong, and the right one is a third:

> **A hypothesis is a premise. A workbench is the apparatus for finding out. Hypotheses are *run* via
> workbenches.**

They are different kinds of thing and they compose. "Suppose the door were locked" is an assumption; it
does not by itself say what follows. "Run these five steps and see" is a simulation; it needs a starting
state. Exploring a hypothesis is opening a workbench whose **frame 0 incorporates that hypothesis's
assumptions** — the copy is taken, the hypothesis's variants and assumed values are applied to it, and from
there it is an ordinary simulation.

This resolves the duplication worry without forcing a false identity. Nothing is built twice: the
hypothesis keeps its assumptions and its verdict; the workbench keeps frames, mappings and transformations;
and the join is one edge (`workbench --explores--> hypothesis`) plus the rule that frame 0 is seeded from
the hypothesis rather than from the bare original.

Two consequences worth noting now rather than discovering later:

- **`hypothesis.variant` and the workbench's frame-0 copy are the same operation** at different scales —
  build an altered version of something, leaving the original intact. The workbench's version is the
  general one (schema-bounded, mapping-tracked), so `variant` should eventually be expressed in terms of
  it rather than kept as a parallel implementation.
- **A hypothesis with no workbench is still meaningful** — it is an assumption nobody has explored yet,
  which is an ordinary and useful state. The verdict simply stays open.

---

## 8. What this means for what is already built

- `plan.py` **survives as the proposer** — backward chaining is a good way to generate a candidate chain.
  Its `run` becomes "run on a workbench" rather than "run for real."
- The lazy-chain property becomes *more* useful, not less: the chain is the thing the workbench executes.
- `dispatch.py` gains the workbench refusal (§4).
- `types.py` gains the scan-exclusion (§6) and is the copy boundary (§1).
- `hypothesis.py` is extended rather than paralleled (§7).

## 9. The data model, as it now stands

Settled (§2/§3):

| node | edges | meaning |
|---|---|---|
| `workbench` | `root_frame`, `subject`, `explores` → hypothesis, `parent` → enclosing workbench | one planning sandbox; nests for subgoals |
| `frame` | `mapping`, `next` → frame (**ordered, 1:N — forks**), `via` → transformation | one imagined state; frames form a tree |
| `mapping` | `original` → node one level up, `image` → this frame's copy, `next` → mapping (**1:N**) | one node's identity, followable; branches with the frames |
| `transformation` | `applies` → function, `arg` → **mapping** (never a raw node), `expects` → type, `assumes` → hypothesis | what turned one frame into the next, and what it took on faith |
| `function` | `mock` → function (**1:N**) | the possible outcomes of a call, each a real microfunction |

Three rules hold this together:

1. **A transformation's arguments are mappings**, never raw workbench nodes — a raw workbench node means
   nothing outside the workbench, so binding one makes the plan unreplayable.
2. **Metadata points inward** (§2) — nothing structural points at a mapping, or copying becomes unbounded.
3. **`next` is 1:N everywhere** — frames fork on assumptions, and mapping chains fork with them.

The one rule that makes replay work: **a transformation's arguments are mappings.** Nothing in a plan ever
binds a raw workbench node, because a raw workbench node means nothing outside the workbench.

## 10. Settled, and what is left

**Settled:** the copy boundary (§1 — everything reachable, cost accepted, copy-on-write is an
implementation of the same semantics rather than a smaller boundary); frames are necessary (§3); mapping
nodes with `next`, and transformations binding to mappings (§2); imagined nodes tied to reality by
provenance and dropped chains terminating at the dropping call (§2); the direction invariant (§2, now
test-enforced); hypotheses and workbenches compose rather than one absorbing the other (§7).

**Left to decide, and neither blocks starting:**

1. **How the real graph is marked**, so resolving `original` up a stack of nested workbenches terminates on
   something explicit rather than on a missing edge — which is also what an imagined node looks like
   (§3a). Small, but conflating those two would be a real bug.
2. **Where mocks are authored** — the `function --mock--> function` edge is clear, but nothing yet says
   whether a mock is hand-written per tool, generated from the tool's declared return type, or supplied by
   a language model at the boundary. The safety property (§4) does not depend on this; the quality of
   plans does.

**Build order**, given all of the above: the workbench-exclusion test for scans (§6) *before* the feature
that needs it, then copy + mappings, then frames + transformations, then the dispatch refusal (§4), then
mocks. Deviation detection (§5) comes last and is small, because it is `types.is_a` against a recorded
expectation.
