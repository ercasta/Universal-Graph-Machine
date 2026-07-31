# `microfunctions/` — the new engine

**Started 2026-07-30. Supersedes `ugm/`.** Picking this up cold? Read `docs/microfunctions/HANDOFF.md` first, then `docs/microfunctions/north_star.md`; this package is that
document in code. `ugm/` and `units/` stay as the findings they are — nothing deleted, and deletion is
earned per item by the audit in `north_star.md` §6.

`python -m microfunctions.selftest` — **78 checks, 0 errored.**

| module | what it is |
|---|---|
| `graph.py` | the substrate — mutable nodes, **named edges**, **ordered targets** (index addressing), **edge properties**, **references**, a maintained reverse index, and an undo journal |
| `focus.py` | **the control mechanism** — named heads pointing into the graph; move forward, backward, through references, fork, spread, close |
| `types.py` | a type is a subgraph schema, declared as ordinary graph data; validation, never dispatch |
| `hypothesis.py` | a hypothesis is an ordinary **node**, with ordinary subgraphs under it. No scopes, no relativization, no supposition primitive |
| `isa.py` | imperative ISA over named/indexed edges, focus heads, and references; programs are data |
| `function.py` | a rule IS a function — a named ISA program with parameters, stored in the graph and executed |
| `asm.py` | the text surface and LLM border — one instruction per line, natural-language comments kept as data, `.mf` files |
| `application.py` | applications and episodes — the record of what the system did, as ordinary nodes |
| `thread.py` | **materialised short-term memory** — what we just did, navigable; an episode extended with attention shifts |
| `plan.py` | **backward chaining over return types into a LAZY chain** — plans are data, nothing runs until the action |
| `dispatch.py` | the one place an effect leaves the graph, and the checkpoint guarding it |
| `workbench.py` | **imagining effects on a copy** — frames, mappings, forking, backtracking |
| `execution.py` | **following a plan for real** — replay, deviation detection, contingencies |
| `selection.py` | candidates, ranking, applying one function at a time |
| `rules/*.mf` | the KB on disk |

## The substrate

**Named edges replace role nodes.** `rev-02` §5 made edges nameless and roles nodes so a connection could
be pointed at — correct, but it charged a node plus two edges for *every* connection to keep the rare case
expressible. Named edges plus optional **edge properties** are what property graphs and RDF-star converged
on: the common case is one entry, the rare case attaches properties, a genuine n-ary relation mints a node
for the relation itself. Reification stays available and stops being mandatory.

**Targets are ordered, so index addressing is free.** A label maps to an ordered list: single-valued is
length 1, 1:N (`list --item--> a, b, c`) is longer, `g.at(lst, "item", 2)` is a list index. This removed a
real defect — compiling an episode into a procedure had needed a driver-stamped turn counter purely to
recover an order the old substrate could not represent. ⚠ Insert and remove **shift edge properties along
with their edges**; checked explicitly, because getting it wrong silently misattributes a property.

**References are not edges, and the distinction is load-bearing.** An *edge* is a relation — part of what
the graph asserts. A *reference* (`Ref`, held as an attribute value) is a stored pointer, the graph's
equivalent of a variable holding an address. A saved focus head, or one node naming another as data, is a
reference, not a claim that the two are related.

**Mutable, with a maintained reverse index.** `g.sources(node, label)` is O(1), which is what `BACK` needs.
The reverse index is keyed without the position, deliberately: keeping indices in it would make every
insert rewrite unrelated entries.

## Focus is the control mechanism

With matching demoted to type validation, nothing decides what happens next — so focus does. A focus is a
set of named **heads**, each pointing at one node, starting from `root`. A microfunction is invoked *on
heads*, never on "whatever matches", which is why wrong firing is structurally impossible rather than
merely unlikely. Heads move forward along a named edge (by index), backward through an incoming edge,
or through a stored reference; they fork to explore rivals without copying the world, spread to fan out
over an ordered 1:N edge, and close when done. A move that fails **empties** the head rather than raising —
a failed navigation is an ordinary answer, like an out-of-range index being `None`.

Heads are named rather than positional so one can be handed to a microfunction as an argument, stored in
the graph as a `Ref`, and — the reason that matters — *recorded*: "this operation was applied to this head"
is `docs/microfunctions/graph_data_model.md` §6.3's application node, and the episode machinery built on it works unchanged.

## Hypotheses are nodes, not a mechanism

A hypothesis is a node. If entertaining it needs a different version of something it *builds* that as an
ordinary subgraph and hangs it off the hypothesis (`variant`); if it needs to remember a prior value it
writes an **explicit backup** node. No scope, no relativization, no pencil/ink layer.

This is smaller than what it replaces and also strictly more capable in two ways worth naming:

- **Rival hypotheses coexist.** The old supposition machinery entertained one assumption and discarded it;
  comparing candidate plans meant re-running. Two rivals are now two nodes, both live, both readable, and
  choosing between them is an ordinary comparison — exactly what selection needs.
- **⭐ The verdict is a fact.** `docs/microfunctions/graph_data_model.md` §6.1 recorded a real gap: a supposition's verdict came
  back as a Python value and its scope was retired, so no rule could react to "that hypothesis was
  refuted." Here `status` is an attribute on a node that persists. That gap closes *by not being
  reintroduced*.

Isolation is a consequence of addressing, not a mechanism: a hypothesis's subgraph is reachable only by
navigating into it, so leaking would require deliberately walking there and copying something out.

**The honest cost:** nothing is shared implicitly. A hypothesis that perturbs a large structure must build
what differs — there is no free relativized view. Build only the delta and reference the rest.

## The undo journal — deliberately small scope

⚠ **The journal is transactional, not hypothetical.** Its one real job: *a program that raises halfway
leaves no half-written graph.* `Machine.run` takes a savepoint on entry and rewinds on exception. That is
all it claims.

It is **not** the hypothesis mechanism (that is nodes), and it **cannot** undo external effects. The moment
a tool call is dispatched, atomicity is gone — the effect escaped and no journal reaches it. So the rule to
hold to:

> **A rollback boundary must never span a dispatch.** Commit before the call; past that point the journal
> is worthless and pretending otherwise is worse than not having it.

Kept because it is ~15 lines and one integer per savepoint, and because it makes a raising program safe by
default. If nothing outside `selftest.py` turns out to use it, delete it — that is cheap, and preferable
to building anything on top of it. Do not design around it.

## Why an ISA, if microfunctions are Python

Because a program that is *data* can be inspected, generated, stored, and learned; a Python function is
fast and readable but opaque, and an episode cannot be compiled into one. Both coexist by the test
`mechanism_policy_separation.md` already uses: **Python for mechanism nothing reasons about; ISA for
anything that must be inspectable, generated, or learned.** `selftest.py` builds a program at runtime from
a parameter and runs it.

Operands: a bare value is a literal, `R("x")` reads a register, **`F("h")` reads a focus head** — that last
is what makes a program *pointed*. A runaway program raises at `MAX_STEPS` rather than truncating silently;
termination is still unsolved (`STATUS.md` phase D), so failing loudly is the honest stand-in.

## Rules are functions, and functions are graph data

`function.py` + `asm.py` are where "rules as data" stops being a slogan. Every earlier version of the idea
in this project stored rule-shaped data that a fixed compiler turned into something *matched*; here the
stored form is turned into something **run**. A rule is a named ISA program with parameters.

**Stored as ordered edges** — a `function` node carries `param` and `instr` as ordered 1:N edges, each
instruction carries `arg` the same way. Before named/indexed edges this would have needed a position
attribute on every instruction and a sort on every load. A label is stored as a `LABEL` instruction so the
stored form stays one flat ordered list.

**The calling convention has one real decision in it: a callee gets a fresh focus** holding only its bound
parameters, never the caller's heads. Sharing would make every function silently sensitive to where its
caller happened to be looking — the ambient-context defect the whole repoint exists to remove. Isolation
here is the same discipline as pointing: a function sees what it was handed.

**`asm.py` is the LLM border.**

```
fn service_car(car):
    CHECK F(car) "car"
    SET F(car) "serviced" true
```

Assembly rather than a CNL *for now*, deliberately: a controlled natural language is the eventual surface,
but starting there means designing a grammar before knowing what the operations are. Assembly is
unambiguous, so a translation is either right or loudly wrong with no interpretation layer to hide a
mistake in. A higher-level surface compiles to exactly this later, wasting none of it.

Parsing is **lenient in, strict out**: a bare word parses as a string (a model writing `SET F(c) colour red`
means the obvious thing), but `dump` always emits canonical quoted form, so it is textually stable and safe
to show a model as "here is what you actually wrote." Unknown opcodes are refused with the line number and
the available set — a plausible-looking wrong opcode accepted silently is the dangerous failure, because it
produces a function that runs and does something else.

**No seam, and this is the load-bearing claim.** A stored function is not part of a rigid end-to-end
program. Nothing runs unless something calls it; composability comes from *which* functions get called on
*which* heads, and that is selection's job, not a control-flow graph fixed at authoring time. The library
grows without any global program needing re-verification — the property the telecom feature-interaction
literature took decades to arrive at.

**⭐ The reflexive edge finally has somewhere to land.** `closure_probe_experiment.py` found that
rule-writes-a-rule was proven only in a test and used by no shipped library. `selftest.py` now has a
microfunction that generates a function from a parameter, stores it, runs it, and dumps it back.

## Types are schemas; mutation is a cast

A type is a schema over a subgraph — **structure and attributes** — the way a Pydantic schema constrains a
frame. That removes any need to represent mutation: `service(c: car) -> serviced_car` is a **cast**, and
whatever it changes in the graph is merely how the cast is achieved. Nothing records that a mutation
happened, because nothing needs to — a node either satisfies the stronger schema or it does not, checkable
at any moment rather than being a historical claim. Precondition and effect reduce to parameter type and
return type.

**Sub/supertypes are structural.** A supertype relaxes constraints; a subtype tightens them. `base=` is a
convenience for writing that, never what makes it true — two independently declared types stand in the
relation if their constraints do. This shows up in two places: an argument accepts any subtype (free, since
`is_a` checks constraints not names), and a producer of a subtype satisfies a goal wanting the supertype
(`fn.producers` asks `subsumes`, with exact matches sorted first so a more specific producer is never
preferred by accident).

## Planning: backward chaining into a lazy chain

To obtain a `T`, find the functions returning `T`, make their parameter types the subgoals, recurse. The
result is a chain of **pending calls that nothing has executed**. Transformations compose; an action
materialises — the Spark separation, taken seriously, and it buys three things that previously needed
separate machinery:

- **A plan is data** — inspectable, comparable against a rival, hypothesisable, or handed to a model to
  critique, all before anything happens.
- **Nothing is committed by thinking.** Exploring a plan is just not calling `run`. There is no mode to be
  in and no supposition mechanism required.
- **Two rival plans are two chains**, side by side — what non-greedy selection will need.

**A cast returns its subject**, which is why `run` falls back to the first bound argument when a function
sets no `result`. That is not a convention papering over ambiguity; creating something genuinely new is the
case that has to say so.

⚠ **Honest scope:** depth-limited depth-first search, first solution wins. No cost model, no preference
between rival producers beyond exact-match-first, no backtracking across a committed subgoal. Adequate for
chains of a handful of steps — which is the size this system needs — and it should not be mistaken for a
general-purpose planner.

## Dispatch: one checkpoint

Both rules here were established by probe before any of it was built:

1. **Check at APPLY time, not MINT time.** A pending call is inert data until the dispatcher reaches it, so
   a prohibition recorded *after* the call was planned still blocks it. This recovers the order-independence
   ambient matching used to give free.
2. **A rollback boundary must never span a dispatch.** The graph is committed *before* the handler runs.
   Nothing reaches an effect that has already left.

One choke point, so one check covers every tool ever registered — including ones written by code that never
heard of prohibitions. A veto is ordinary data (a `forbidden` node pointing at a target); the dispatcher
knows one reserved name and never interprets a value.

## Selection

Under rule matching, dispatch was automatic: everything applicable fired. Under microfunctions nothing
happens unless something chooses — so selection is not an optimisation, it *is* the control flow, and the
system's effectiveness is now literally the quality of this module. Three stages, kept separate because
conflating them is what made matching hard to reason about:

1. **Candidates** (`selection.candidates`) — which functions *could* apply, from declared parameter types
   (`fn service(c: car)`). This is matching in its demoted role: bounded, one node, no fixpoint. Restricted
   to single-parameter functions on purpose — a multi-parameter function needs a *binding* proposed, which
   is search, and hiding search inside candidate generation would be a mistake.
2. **Ranking** — a declared `priority` (ordinary authored data), plus one structural rule, plus an optional
   external `scorer`, which is where a language model plugs in reading `function.catalogue`'s docs.
3. **Applying** (`selection.step`) — invoke, and **record the application**, so the next round sees it.

**The structural rule that earned its place: a function is never applied twice to the same node.** Under
rules this needed a hand-authored consumption marker per rule, and forgetting one produced an unbounded
stream of repeated effects — the single most persistent defect of the old design. Here it is one check in
one place, possible only because applications are recorded.

A refused application is **data, not a crash**: the outcome is stored and the loop continues.

⚠ **Selection is greedy, deliberately and temporarily.** Non-greedy choice informed by which subsequences
work well is the actual goal, and it needs the episode corpus this module produces — so it comes after,
not with. The hooks are explicit rather than implied: `scorer`, and recorded episodes.

## Applications and episodes

`application.py` closes what `docs/microfunctions/graph_data_model.md` §6.3 called the most load-bearing
gap: the system kept no record of its own reasoning steps. An application is a node — which function, which
bindings, which episode — and a binding is itself a node so that "what if this had been applied to *that*"
is expressible.

**⭐ Ordering is native**, which is the substrate change paying its way. The earlier version of this
experiment found applications had no inherent order and needed a turn counter stamped by the driver. An
episode now holds its applications on an ordered `step` edge. The turn counter is gone.

**Learning falls out.** `compile_episode` turns an episode into a reusable function that replays it on a
fresh subject — `function.define` plus a loop, no new machinery, and the result is indistinguishable from
an authored function (same storage, same catalogue, callable and recordable). ⚠ Honest scope: it handles a
sequence of single-argument operations on one subject. Generalising means deciding how a replay maps old
bindings to new — a real question about *analogy*, not a missing mechanism.

## The workbench — imagining what functions would do

`plan.py` chains declared *types*, which is a promise rather than a proof and says nothing about what else
changed. So backward chaining is a good way to **propose** a chain and a bad way to **believe** one. The
workbench runs the proposal somewhere that does not count. Design: `docs/microfunctions/planning_workbench.md`.

**The copy boundary is everything reachable from the subject.** Every cleverer boundary is a guess about
which structure will matter, and a wrong guess yields a plan that looks fine and fails on contact with
reality. Copy-on-write, if ever needed, implements exactly these semantics more cheaply — it is not a
smaller boundary.

**Mappings are the crux.** A mapping points at the original and at this frame's image, and chains via
`next`. **A transformation binds its arguments to mappings, never raw workbench nodes** — that is what makes
a plan replayable, since following `original` yields the node the operation must really be applied to. A log
saying "`service` was applied" is unreplayable: it does not identify the subject in a form that survives out
of the workbench.

**⚠ The direction invariant.** A mapping points *to* the original and image; nothing points from a node to
its mappings. Copying traverses outgoing edges, so one edge the other way would drag in that mapping's
original, image and `next` — and thence every frame, every workbench, every plan touching that node. Not a
wrong answer: an **unbounded copy**. Enforced by `check_metadata_is_never_pointed_at_by_structure`, which
scans every edge and is verified to catch a planted violation.

**Frames form a tree.** Steps extend a path; assumptions fork it. `next` is 1:N on frames *and* on
mappings, so a node's own history branches with the frames it lives in — code assuming a single successor
would silently follow one branch.

**Nesting vs forking are different axes.** Subgoal exploration **nests** (a workbench inside a workbench,
new copy scope, `original` pointing one level up so resolution is a walk); assumption branching **forks the
frames** inside one workbench, since all branches imagine the same world differently.

**⚠ Scans exclude workbench copies by default.** Not a convenience — copies are ordinary nodes, so an
unfiltered scan would find the system's own imaginings and offer them as candidate arguments, planning
about the products of planning with no error and no symptom beyond gradually stranger plans. The test for
this was written before the feature that causes it.

## Mocks, assumptions, and deviation

**A call can turn out several ways, so a function has many mocks** — each an ordinary microfunction whose
**return type is the outcome it assumes**, so the existing type-chaining planner plans each case
differently with nothing added:

```
fn list_dir(d: dir) -> listing:                              # reaches the world
fn list_empty(d: dir) -> empty_listing mocks list_dir:       # assume nothing there
fn list_full(d: dir)  -> full_listing  mocks list_dir:       # assume plenty
```

**Declaration order is preference order**, free, because `mock` is an ordered edge. That is deliberately
the weakest thing that works: the old possibilistic band layer existed to rank uncertain outcomes and was
cut as machinery solving a problem a language model already solves. An ordered list is the residue actually
needed — something has to decide the default, or it is whichever mock was declared first *by accident*
rather than *by intent*.

**Choosing an outcome is making an assumption**, so the transformation records a hypothesis, and
`fragile_steps` answers "which parts of this plan are guesses" as a lookup rather than a judgement someone
has to remember to make. Forking on a different outcome gives two worlds side by side — and contingency
plans come free from having explored both.

**⚠ Two mechanisms, and they must not be conflated.** On a workbench a function with declared outcomes is
*substituted* by one — that makes planning **useful**. What makes it **safe** is separate:
`dispatch.service` **refuses an imagined target** (one a mapping points at as an `image`). If substitution
were ever forgotten or bypassed, a dispatching function still could not reach the world. Putting the
guarantee in the substitution would be putting it in the wrong place. The refusal is checked *before* the
veto, since an imagined target's prohibitions are imagined too.

**Deviation is a failed cast** — `types.is_a` against the type the transformation recorded. Cheap,
meaningful, and it reports *how* it deviated, not merely that it did. Comparing whole subgraphs would let
irrelevant differences swamp real ones; the expected type is the honest signal because it is exactly the
promise the function made.

## Following a plan for real

Everything execution needs was already recorded, which is what mappings and transformations were *for*
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

**Fail fast, and do not roll back.** Execution stops at the first step whose real result fails the cast it
promised, because everything after it was planned *on the assumption that it held*. Nothing is undone:
real effects have already left the graph, and pretending a journal could reach them would be worse than
not having one. The honest output is "these ran, this diverged, here is how."

**Imagined nodes are bound by provenance.** A step may mint something that did not exist at planning time;
its mapping has no `original`, and the real counterpart is matched by *which transformation produced it* —
the only correspondence available for something that did not exist when planning started. ⚠ Matching within
a transformation is by kind and order, so if one transformation mints two nodes of the same kind the
pairing is a guess — and `execute` says so in its notes rather than choosing silently.

**Contingencies come free.** `alternatives` returns the sibling branches explored for a step that
diverged. That is the payoff for branching deliberately at the few points that warrant it, and the reason
an abandoned fork is kept as data rather than erased.

## The thread — short-term memory as data

Design: `docs/microfunctions/thread_and_system1.md` §1. This is the first piece of the **outer loop**, which
this engine had been missing since it started: `plan.py` chains, `workbench.py` imagines, `execution.py`
replays, `selection.py` ranks — and nothing invoked any of them.

**Why it exists.** `Focus` is a Python object holding no graph state, created fresh per call and discarded.
So attention was the one thing here that was *not* homoiconic — a strange hole in a system whose claim is
that a rule can reason about a rule. A thread is that record, as ordinary graph data.

**A thread IS an episode, extended — not a second log.** `application.py` already mints a node per
application on an ordered `step` edge; a parallel record would mean two accounts of one event and every
reflective function consulting both. So an application entry **is** the `application` node, and
`application.steps` filters back to applications so `compile_episode` is unaffected.

**Two entry kinds only** — a deliberate attention shift, and an application. ⚠ Not every instruction:
`Focus.move` runs inside every microfunction body, and logging those would record pointer arithmetic rather
than reasoning. Nothing instruments `Focus`, on purpose.

**Order lives in the ordered `step` edge; `prev` carries navigation and the reason.** Stepping back is O(1)
rather than an index lookup, and *why* a step followed another is a property of the transition, so it rides
on the `prev` edge as an edge property. Walking forward is a reverse-index query, so only one direction is
stored. The two views agree because exactly one function appends — a discipline a human must follow, hence
a test.

**⚠ A `prev` edge property cannot be pointed at.** `eprops` is keyed `(src, label, index)` and reindexes on
insertion. So: *ride on the edge what merely describes it; mint a node for what must be pointed at.* That
is why `connect` — tying two distant moments — mints a `connection` node: a hypothesis may dispute it.

**⚠ The thread does not hang off `root`.** "Real things hang off root" is what makes `types.instances` safe
by traversal and what will separate the world from the scaffolding when System 1 explores. Memory points
*at* the world and is never pointed at by it.

**Walking needs no new primitive.** `prev` and `at` are ordinary edges, so `MOVE` navigates them: a
thread-walker is an ordinary microfunction *pointed at* the thread. `selftest.py` proves this by loading one
from stored ISA text and running it on the ordinary machine.

```
thread session (4 entries)
  0. attend root [start]
  1. attend chunk#20 [the car]  (user mentioned it)  ~1 tie(s)
  2. applied service  (it needed servicing)  ~1 tie(s)
  3. attend wheel#22  (checking the tyres)
```

**Not here yet:** nothing appends to the thread automatically — the outer loop that does is the next piece,
and System 1 (bounded association from the thread head) after it.

## Recovering from a divergence

Once a step has diverged there are exactly two honest moves, and `recover` picks between them on the
structure rather than on a policy.

**`resume` — was this outcome already explored?** A fork exists precisely because someone thought a call
could turn out more than one way. `matching_alternative` asks each sibling the same question that detected
the problem — `deviates`, against the sibling's own promise — and a sibling that survives it is a plan for
the world we are now in, *already imagined and already checked*. Continuing down it is not replanning; it
is following the contingency the fork was for. This is tried first on evidence, not taste: a matching
branch is verified against this world and a fresh proposal is not.

**⚠ The diverged call is not re-run.** It reached the world once, and running it again would double its
effects — the single most likely bug here. Its real outcome is instead *settled* onto the chosen branch's
own mappings, carried from the shared parent frame, since siblings do not share mapping nodes. That
includes anything the call **minted**: a branch may refer to a node that did not exist at planning time,
and the follow-up step may operate on *that* rather than on the original subject.

**⚠ Resuming requires the sibling to be the same function.** Siblings are alternative *successors*, which
need not be alternative *outcomes* — a fork may try a different action entirely. Resuming into one of those
would silently skip a call that never ran and then report success.

**`replan` — nothing explored fits.** Then the branch tree has nothing to say, and the only sound move is
to propose afresh **from the world as it actually is**, taking the diverged step's real result as the
subject, because that node *is* the actual state. What comes back is a lazy chain, so re-proposing still
commits to nothing. With no goal to aim at, `recover` says `stuck` rather than inventing one.

```
ran: list_dir, archive
  (resumed on the branch assuming full_listing)
completed as planned
```

## Not here yet

- **Rehearsing a re-proposal.** `replan` returns a chain; nothing runs that chain on a workbench first, so
  a re-proposal is unverified where the original plan was verified. The blocker is real rather than
  missing code: turning a chain into workbench steps needs a rule binding each pending call's *output* to a
  mapping, and for a call that mints something that is the same open question as `compile_episode`'s. A
  guessed binding would produce a plan that *looks* rehearsed.
- **Arbitrating between several matching branches, or several leaves below one.** Both take the first,
  matching the planner's first-solution-wins discipline rather than pretending to choose.
- **⚠ A policy against enumerating mocks eagerly.** Nothing currently stops a caller forking every outcome
  of every uncertain call — three calls with three outcomes each is twenty-seven plans, and that is a small
  plan. `step` assumes the preferred outcome, which is the right default, but the discipline (branch only
  where being wrong is expensive; keep the others for *on deviation*) is not enforced anywhere.
- **Non-greedy selection**, and learned preference over subsequences — see the warning above.
- **Conflict detection.** ⚠ A regression, not a deferral: the old rule engine surfaced two conclusions
  disagreeing rather than letting one silently overwrite, and the composition-safety argument rested on it.
  Mutable last-write-wins has nothing. The intended answer is reflective microfunctions — functions that
  read applications and the graph and detect conflicts — which needs no new mechanism, only writing them.
- **A goal as a node** driving planning, rather than a caller passing a wanted type.
- **Conflict arbitration and termination.** Both still open, unchanged by any of this.
- **Performance.** No indexing beyond the reverse index; `types.instances()` is a whole-graph scan and
  exists only to seed a candidate index.
