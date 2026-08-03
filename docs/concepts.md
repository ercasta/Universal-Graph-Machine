# Concepts

Everything the machine knows, does, and is in the middle of doing lives in one graph, in one
vocabulary. This page describes that vocabulary from the bottom up: the substrate, how attention
works, what a type is, what a rule is, and how the pieces close over each other so that a rule can
read a rule.

## The substrate

A graph holds mutable nodes connected by **named edges**. A label maps to an ordered *list* of
targets, so a single-valued relation is a list of length one, a one-to-many relation is longer, and
addressing by index is a list index rather than a search.

```python
g.link(car, "wheel", w)        # append a target under a label
g.at(car, "wheel", 2)          # the third wheel — ordering is native
g.count(car, "wheel")          # 4
g.sources(w, "wheel")          # backwards, O(1) on a maintained reverse index
```

Three representational commitments follow.

**Named edges rather than role nodes.** An earlier design made edges nameless and roles into nodes,
so that a connection could be pointed at. That was correct about the rare case and charged a node
plus two edges for *every* connection to buy it. Named edges with optional **edge properties** are
what property graphs and RDF-star converged on: the common case is one entry, the rare case attaches
properties to the edge, and a genuinely n-ary relation mints a node for the relation itself.
Reification stays available and stops being mandatory.

**Ordered targets.** Order is a property of the substrate, not something reconstructed from
sequencing facts. This removed a real defect: compiling an episode into a rule had previously needed
a turn counter stamped by the driver purely to recover an order the substrate could not represent.

**Edges have identity.** An edge id is an ordinary string, minted and journalled like a node, so
edge properties are keyed by identity rather than by position: an insertion moves positions and
never properties, and there is no reindexing pass to get wrong. The payoff beyond that is that an
edge can be *pointed at* — a moment can date the arrival of a connection, which "when did this file
appear under this directory?" needs and no attribute on either end can express.

**References are not edges, and the distinction is load-bearing.** An edge is a relation — part of
what the graph asserts. A reference (`Ref`, held as an attribute value) is a stored pointer, the
graph's equivalent of a variable holding an address. A saved focus head, or one node naming another
as data, is a reference, not a claim that the two are related.

### Absence, and not knowing

`g.attr(node, key)` returns `None` when the node lacks that attribute. Absence means *lacks it*,
which is a claim, and it is deliberately different from *has not been established* — the
distinction that lets a goal say "go and look" rather than silently reading an unset slot as an
answer. See [`known` in the authoring guide](authoring.md#goal--ask--why--plan).

### The undo journal

Every mutation records how to reverse itself. `savepoint()` returns a marker and `rollback(sp)`
reverses back to it, at a cost proportional to the changes made rather than to the size of the
graph.

Its scope is deliberately small. The journal is **transactional, not hypothetical**: its one job is
that a program which raises halfway leaves no half-written graph, and `Machine.run` takes a
savepoint on entry and rewinds on exception. It is not the hypothesis mechanism, and it cannot undo
external effects. Once a tool call has been dispatched, atomicity is gone. Hence the standing rule:

> A rollback boundary must never span a dispatch. Commit before the call; past that point the
> journal is worthless and pretending otherwise is worse than not having it.

## Focus — attention as the control mechanism

With matching demoted to type validation, nothing decides what happens next, so focus does. A focus
is a set of named **heads**, each pointing at one node. Every graph starts with `root`, and every
head starts there or is derived from another head. A rule is invoked *on heads*, never on "whatever
matches", which is why wrong firing is structurally impossible rather than merely unlikely.

Navigation is the whole vocabulary. A head moves forward along a named edge (optionally by index),
backward through an incoming edge, or through a stored reference. Heads fork, so exploring two
candidates is two heads rather than a copied world; they spread to fan out over an ordered
one-to-many edge; they close when a line of inquiry is done. A move that fails **empties** the head
rather than raising — a failed navigation is an ordinary answer, in the same way an out-of-range
index is `None`.

Heads are named rather than positional so that one can be handed to a rule as an argument, stored in
the graph as a reference and picked up later, and — the reason that matters — *recorded*. "This
operation was applied to this head" is what an application node says.

## References — one language for reaching something

Anything not directly at hand is reached through one small path grammar:

```
path := seg ('.' seg)*
seg  := ['^'] label ('[' int ']')?
```

`car.wheel[1].pressure` walks named edges left to right, indexing into a label's ordered targets;
negative indices count from the end. `wheel.^has` is a backward hop along an incoming edge, and it
resolves only when exactly one node points that way — two candidates yield nothing rather than a
guess.

This grammar existed three times, undeclared, before it was written down: once in the planner's role
resolution, once in the goal parser, once in effect reading. Three copies of an unwritten grammar is
the shape a missing module makes, and the cost was that no other part of the surface could refer to
anything more than one hop away, which is why type schemas used to be one level deep.

Reach at any depth (`contains+`) is a separate thing and deliberately not part of a reference: a
reference must denote *one* node, and reach denotes a set. It belongs in a link position — a goal
line or a query.

## Types are subgraph schemas

A type is a schema over a subgraph, covering structure and attributes, declared as ordinary graph
data. A requirement reads directly off the graph: this label, this many targets, of this kind.
Checking a node against a schema *is* a graph pattern match — matching was not eliminated, it was
demoted. It validates one argument at one call site, bounded and terminating, instead of deciding
what fires across the whole graph.

```python
TY.declare_type(g, "car", requires={"wheel": TY.Req(4, "wheel"), "body": TY.Req(1, "body")})
TY.is_a(g, node, "car")            # True / False, by looking
TY.violations(g, node, "car")      # {'wheel': ('4 of kind wheel', '3')}
```

**Sub- and supertyping is structural.** A supertype relaxes constraints; a subtype tightens them.
Declaring a `base=` is a convenience for writing that, never what makes it true — two independently
declared types stand in the relation if their constraints do. Two consequences matter downstream: an
argument accepts any subtype for free, and a producer of a subtype satisfies a goal that wants the
supertype, with exact matches sorted first so a more specific producer is never preferred by
accident.

**Recognition is bottom-up.** `types.recognize(g, node)` reports which declared types a node
satisfies *now*. Multi-type membership falls out, and so does de-recognition: when a node stops
satisfying a shape there is nothing to invalidate, because nothing was ever stored.

Because a type is a shape rather than a tag, mutation needs no representation. `service(c: car) ->
serviced_car` is a cast; whatever it changes in the graph is merely how the cast is achieved.

## Rules are functions, and functions are graph data

A rule is a named program with typed parameters, stored in the graph and executed by the instruction
set. Every earlier version of the idea in this project stored rule-shaped data that a fixed compiler
turned into something *matched*; here the stored form is turned into something *run*.

A function node carries its parameters and instructions as ordered edges, and each instruction
carries its operands the same way. A label is stored as a `LABEL` instruction so the stored form
stays one flat ordered list.

The calling convention contains one real decision: **a callee gets a fresh focus** holding only its
bound parameters, never the caller's heads. Sharing would make every function silently sensitive to
where its caller happened to be looking, which is the ambient-context defect the whole design exists
to remove.

There is no seam, and that is the load-bearing claim. A stored function is not part of a rigid
end-to-end program. Nothing runs unless something calls it; composability comes from *which*
functions get called on *which* heads, and that is deliberation's job rather than a control-flow
graph fixed at authoring time. The library grows without any global program needing re-verification.

Python and stored programs coexist by one test: **Python for mechanism nothing reasons about; stored
instructions for anything that must be inspectable, generated, or learned.** See
[Execution model](execution-model.md) for the instruction set and where the line falls.

### The text surface

```
fn service_car(car):
    NATIVE "check" F(car) "car"
    SET F(car) "serviced" true
```

Assembly rather than a controlled language, deliberately and for now. A controlled language is the
eventual surface for functions, but starting there means designing a grammar before knowing what the
operations are. Assembly is unambiguous, so a translation is either right or loudly wrong with no
interpretation layer to hide a mistake in, and a higher-level surface compiles to exactly this later
without wasting any of it.

Parsing is lenient in, strict out. A bare word parses as a string, so a model writing `SET F(c)
colour red` means the obvious thing; `dump` always emits canonical quoted form, so the text is stable
and safe to show back to a model as "here is what you actually wrote". Unknown opcodes are refused
with the line number and the available set, because a plausible-looking wrong opcode accepted
silently produces a function that runs and does something else.

## Hypotheses are nodes, not a mechanism

A hypothesis is a node. If entertaining it needs a different version of something, it *builds* that
as an ordinary subgraph and hangs it off the hypothesis; if it needs to remember a prior value, it
writes an explicit backup node. There is no scope, no relativization, no pencil-and-ink layer.

This is smaller than what it replaces and strictly more capable in two ways.

**Rival hypotheses coexist.** The old supposition machinery entertained one assumption and discarded
it, so comparing candidate plans meant re-running. Two rivals are now two nodes, both live, both
readable, and choosing between them is an ordinary comparison.

**The verdict is a fact.** Previously a supposition's verdict came back as a Python value and its
scope was retired, so no rule could react to "that hypothesis was refuted". Here `status` is an
attribute on a node that persists.

Isolation is a consequence of addressing rather than a mechanism: a hypothesis's subgraph is
reachable only by navigating into it. The honest cost is that nothing is shared implicitly — a
hypothesis perturbing a large structure must build what differs. Build only the delta and reference
the rest.

## Applications and episodes

An application is a node: which function, bound to which arguments, in which episode. It is minted
by whoever applies the function, and thereafter it is ordinary data — navigable, comparable, and
capable of being pointed at by a hypothesis. A binding is itself a node, so "what if this had been
applied to *that*" is expressible.

An episode holds its applications on an ordered `step` edge. Four capabilities failed on the absence
of this record: choosing among candidates had nothing to point at, lookahead had nothing to
hypothesise about, nothing recorded what worked, and nothing could learn from it.

Learning falls out. `compile_episode` turns an episode into a reusable function that replays it on a
fresh subject — a definition plus a loop, no new machinery — and the result is indistinguishable
from an authored function: same storage, same catalogue, callable and recordable.

## The horizon — three layers, not two

Everything above is one representation, which raises the obvious question: if a rule is data and a
goal is data and the program counter is data, what is *not* data, and why not? The answer is a
line, and the mistake worth naming first is that there are **two** lines, easily conflated.

**Above the horizon is a web.** Types, criteria, methods, functions, norms, memories — authored
data, mutually supporting, none of it foundational. A concept here means what it means because of
where it sits in the network, and nothing in it is individually verifiable against the world. This
is where the outer loop works, and it is where almost everything should live.

**Below the horizon is the closed class.** A `goal` is not defined in terms of anything: it is a
handful of constraint nodes from a fixed vocabulary, natively supported by the surface, lowered to
functions and the instruction set by convention. The same is true of a consequent's two kinds, a
tie-break rule's comparisons, the eight proposition forms, and the opcodes. These are *primitive*
— not because they are simple, but because no arrangement of what is above them reconstructs them.

**The kernel boundary is a different, lower line.** Its test is *would a port re-make a decision
here?* — and a port re-makes decisions about the closed class all the time, because a `goal` is
something we decided. So:

| layer | example | ported by | can the layer above define it away? |
|---|---|---|---|
| substrate | the graph, the instruction set, dispatch | re-implementation | — |
| the closed class | `goal` sorts, consequent kinds, tie-break stages | re-implementation | **no** |
| the web | types, criteria, methods, functions, norms | carried over unchanged | n/a |

The horizon sits between the closed class and the web. The kernel boundary sits below the closed
class. Both are real and they are not the same.

### The decomposition error

The reason this matters in practice is that *"can the surface say this?"* has **three** answers,
and the tempting wrong one looks like progress.

Fodor's example is the standing warning: *kill* is not defined as *cause to die*. The relation is
real, but it is a relation **in the network** — an inference the web supports — and not a
decomposition into primitives. Treating it as a decomposition produces a definition that is subtly
and confidently wrong.

So when something turns out to be inexpressible:

1. **Expand the closed class.** Costs a new member, and each one must have something that runs it —
   a tag with no executor is worse than no form at all.
2. **Keep it opaque.** Named and declared, not decomposed. An honest answer.
3. **Relate it in the web.** Author ordinary rules connecting it to what already exists, *without
   claiming it reduces to them*.

Mistaking the third for the first is the error. The pressure runs the other way too: a closed class
grows one member at a time, each individually justified, and the way to keep it small is to make
option 3 the default and force option 1 to argue for itself.

**A closed class earns its place by being declared.** The shape to check for: a named set, reachable
as data, with a stated position on whether it has an escape into the web. A tie-break rule's stages
have one (`run <fn>`), so the closed set is the set that *ships*, never the set that is *possible*.
A consequent's kinds deliberately have none — a considered answer, not an oversight. What must never
happen is the third case: a closed class that is neither named nor reachable, existing only as a
Python function nobody can see.

## Why it closes

Every operation reads and mints structures from the same vocabulary, so nesting is the same case
repeated rather than a new one at each level. A goal about a plan, a hypothesis about an application,
a rule that writes a rule, a criterion that judges a search that is currently running — none of these
needed a mechanism, because there is only one kind of thing to make and one kind of thing to read.

The practical form of this rule is: **a hardcoded mechanism is an unreachable island.** Wherever the
engine keeps state in a Python structure, the system stops being able to compute about that state,
and every reflective capability fails exactly there. Most of the engine's recent work has been
moving such state — the planner's frontier, the interpreter's program counter, the outer loop's
agenda — into the graph, and the payoff each time was a capability rather than tidiness.
