# Reference: the instruction set

Stored rules are programs over this instruction set. The set is deliberately small: it covers the
substrate (nodes, named edges, references), the focus, a little arithmetic, control flow, and three
ways of reaching outside a program. Anything above that — what a plan is, what a moment means — is
never an opcode. See [the kernel boundary](../execution-model.md#the-kernel-boundary).

## Operands

| form | means |
|---|---|
| `"text"`, `42`, `-1.5`, `true`, `false`, `null` | a literal |
| a bare word | a literal string (`SET F(c) colour red` means the obvious thing) |
| `R(x)` | read or write register `x` |
| `F(h)` | the node that focus head `h` points at |
| `&x` | a reference to node `x` |
| `.label` | a jump target |

`F(h)` is what makes a program *pointed*: an instruction names the head it acts on, never "whatever
matches".

## Opcodes

### Writing the graph

| opcode | effect |
|---|---|
| `NEW dst kind` | mint a node of `kind`; the activation records that this program minted it |
| `SET node key value` | write an attribute |
| `SETREF node key target` | store a reference as an attribute value |
| `LINK src label dst` | append `dst` under `label` |
| `LINK_AT src label index dst` | insert at a position, shifting edge properties with their edges |
| `UNLINK src label index` | remove one target |
| `DROP node` | remove a node |

### Reading the graph

| opcode | effect |
|---|---|
| `GET dst src label` | the single target under `label` |
| `GET_AT dst src label index` | the target at a position |
| `COUNT dst src label` | how many targets under `label` |
| `ATTR dst node key` | an attribute value |
| `EPROP dst src label index key` | a property of one edge |
| `DEREF dst node key` | follow a stored reference |
| `NSOURCES dst node [label]` | how many nodes point at this one |
| `SOURCE_AT dst node [label] i` | the node at a position among those pointing at this one |

A `GET` that finds no edge assigns nothing rather than assigning `None`. Writing that would mint an
edge to `None`, and the graph would stop being able to tell *no part* from *a part that is nothing*.

`NSOURCES` / `SOURCE_AT` replace `SOURCES`, which returned the whole tuple into a register. It was the
only opcode that did, and it was unusable for exactly that reason: nothing indexes a register holding a
collection, so a program could learn *that* something pointed at a node and never *which* thing. No
program used it. Count-plus-index is the convention everything else here already follows.

### Reflecting on a node's shape

Every read above takes a slot you have already named. These ask what the slots *are*.

| opcode | effect |
|---|---|
| `KIND dst node` | what it was minted as |
| `NLABELS dst node` | how many distinct edge labels |
| `LABEL_AT dst node index` | the label at a position, in sorted order |
| `NKEYS dst node` | how many attributes, excluding `kind` |
| `KEY_AT dst node index` | the attribute key at a position, in sorted order |

That single asymmetry — *what is at this label* versus *which labels are there* — is why copying a
subgraph used to look like a primitive. It is not: `reachable` is a walk over outgoing edges and
copying a node is minting one with the same kind and attributes, and both are ordinary loops over
structure the instruction set could not see. They are now written in the surface, in
`ugm/rules/reachable.mf` and `ugm/rules/workbench.mf`, and `open_workbench` with them.

**These are substrate.** None encodes a decision about goals, plans, time or criteria, so they sit
below the kernel boundary, and adding them *shrinks* what has to live above it. A single `CLONE`
opcode was the obvious alternative and was refused: *"the same kind and the same attributes"* is a
decision, and an opcode that bakes one in is a composite wearing substrate's clothing.

`kind` is read by `KIND` and is not one of the attribute keys. It is positional, it cannot change
after minting, and letting it out of `KEY_AT` would make a copy written in the surface try to set it
twice.

**Order is inherited, not invented.** `LABEL_AT` follows `g.labels`' sorted order and `KEY_AT` sorts
too, because a program that walks a node twice must walk it alike. `workbench.reachable` records
what the alternative cost: returning a `set` there substituted the iteration order of node-id
strings, and one five-block search measured 12 imagined states, then 306, then budget-exhausted
failure, on consecutive runs of a single process.

### Reflecting on an edge's properties

The same asymmetry, one level further out, and it stayed open when the five above were added.

| opcode | effect |
|---|---|
| `NEPROPS dst src label index` | how many properties this edge carries |
| `EPROP_AT dst src label index i` | the property key at a position, in sorted order |
| `SETEPROP src label index key value` | set one property on an edge that already exists |

Addressed as `EPROP` addresses them — `src`, `label`, `index` — never by edge id, so a program keeps
holding exactly one kind of pointer.

**The gap statement that stood here named half of it**, and that is worth recording because reading it
as complete would have produced a `copy_set` that enumerated an edge's properties correctly and still
dropped every one. `EPROP` reads a property whose name you know and the two new readers say which names
there are; **none of the three writes**. Python never noticed, because `g.link(**props)` takes the whole
dict at edge creation and Python can build a dict first. The surface cannot, so it must make the edge
and then set the properties one at a time — which is `SET`'s shape, and is what `SETEPROP` is.

`put_edge_props` is the substrate half, and it is new for the same reason: until now properties could
only be given at `link` time, because nothing but Python ever needed to give them.

With these, `copy_set` carries edge properties, and `ugm/rules/reachable.mf` owns the copying half that
`open_workbench` used to inline and that `workbench.step` needs too. The Python `_copy_set` dropped edge
properties silently once, and nothing failed **because no check copied an edge that carried any** — so
the check matters more than the opcodes, and planting two deliberate bugs (drop the carry; address the
new edge by the wrong position) is what established that it fires.

### Calling, and being refused

| opcode | effect |
|---|---|
| `INVOKE dst <fn> p=x q=y` | call a stored function; a refusal **raises** |
| `INVOKE dst <fn> with node` | the same, with the bindings described by a node |
| `INVOKE dst <fn> … keep` | the same, leaving the callee's activation to be read |
| `ATTEMPT dst err <fn> …` | the same call, with a refusal handed back in `err` as a node |
| `REFUSE kind why` | decline, as the callee — raises a refusal `ATTEMPT` can catch |
| `SELF dst` | the activation running this instruction |

`<fn>` may be a literal name, **a register, or a focus head** — calling a function chosen at run time
already worked before either of these existed, and a procedure passed as a *parameter* arrives as
`F(how)`, which is the form late binding depends on. The name is what travels in every case; only the
operand form differs.

**`keep` decides what happens to the call's own record, and it is the call site's decision.** A call
leaves an activation, its registers, the focus minted for it and that focus's heads — about five nodes.
By default they go when the call finishes. `keep` retains them, for a caller that means to ask what the
call did (`SELF`, then the last `called`).

The default used to be the other way, on the grounds that somebody might ask. That is fine while calls
are rare and untenable once a graph *read* is one — see `docs/mediated-access.md`, where ~9 mediating
procedures sit under every `ATTR`, `GET` and `SET` a rule performs. It is a hygiene question before it
is a speed one: the residue is interpreter state sitting in the same graph as the world, and this system
has already once mistaken its own scaffolding for world content and type-checked a `focus` as a domain
object. Measured on 200 mediated reads: **1008 nodes left behind, against 8**, for about 5% more time.

What the call *did* survives being discarded. Its `minted` record moves to the caller first, so
`activation.minted` answers exactly as before — that walk already unioned a callee's mints into its
caller's. Only the per-call breakdown is given up, which is what the call site said it did not want.

**`REFUSE` is the enforcing form of `ATTEMPT`**, and for once it was the missing one. Everywhere else
here the engine had the enforcing form and lacked the answering one — `types.check` raised where a guard
needed `is_a`; `INVOKE` raised where a replay stepper needed `ATTEMPT`. This was the inverse: a program
in the surface could decline a request only by being wrong in a way the interpreter noticed, which is a
bug with a convenient side effect rather than a refusal.

Both operands are required. An exception type is a claim about *whose fault it is*, and a surface
refusal has no Python class of its own to be named by, so without a name every one of them would report
as the bare category and leave callers reading prose out of `why`. The name travels as data —
`graph.Refusal` carries it, and `ATTEMPT` reports it in preference to the Python class. That keeps the
kernel's rule intact rather than bending it: it raises the *category* carrying a name it was handed, and
a name it was handed is not a name it knows.

`REFUSE` does not roll anything back. A savepoint here would be one this instruction never took, and a
program that wants its refusal to be clean is already somebody's `ATTEMPT` callee, which takes one.

**`SELF`** is how a program asks what its own call did — `workbench.step` calls a function and then has
to know what that call minted, and to record the activation on the transformation. An activation records
the calls it makes as ordered `called` edges, so the most recent one is the last of them.

```
SELF   R(me)
INVOKE R(out) some_function x=F(x) keep
COUNT  R(n) R(me) "called"
ADD    R(last) R(n) -1
GET_AT R(callee) R(me) "called" R(last)
```

**Read `called` forwards; never read `caller` backwards.** A callee also points at its caller, and the
reverse index looks like it would answer the same question one edge cheaper. It does not: `g.sources`
returns its answer **sorted by node id**, and a node id is a string, so once ids reach four digits
`activation#993` sorts after `activation#9905` and "the most recent" quietly means "the
lexicographically largest". The reverse index cannot carry insertion order, and here the order *is* the
information. This is `search-was-irreproducible-set-tiebreak` in a new place — a deterministic
computation ending in a sort over ids has an undeclared tie-break in it — and it was a benchmark rather
than any check that caught it, because two activations made moments apart have ids that sort the way
they were created.

A second destination register on `INVOKE` was the obvious alternative and was refused for the reason
`CLONE` was: calling, and asking what a call did, are independent capabilities that merely happen to be
wanted together.

**`with node`** is how a program assembles a call it worked out. The node carries ordered `arg` edges
to nodes with a `param` attribute and a `value` edge:

```
NEW  R(b) "binding"
SET  R(b) "param" R(name)      ← the parameter name, computed
LINK R(b) "value" R(node)
LINK R(args) "arg" R(b)
INVOKE R(out) R(fn) with R(args)
```

Graph data rather than "a register may hold a dict", deliberately: a dict in a register is a Python
value the system cannot read, which is the island pattern with a shorter name. A node with `arg` edges
is something a rule can build, inspect, store and hand on — and it is the shape `transformation`
already uses to record a step's arguments.

**`ATTEMPT` catches a closed set, and the line is whose fault it is.** A **refusal** is a claim about
the world or the request — a precondition that no longer holds, a standing prohibition, an imagined
target. Those subclass `graph.Refusal` and come back as a `refusal` node carrying what refused and
why. An **error** is a claim about the program — an unset register, an unknown function, a bad opcode
— and those still abort, because handing one back as data turns a bug into an `err` nobody reads.

A refused attempt **leaves nothing behind**: the savepoint is rolled back, so a caller that carries on
is not carrying on over a half-applied call. Nothing real can have escaped, since every refusal fires
before `dispatch.service` commits.

`Refusal` lives in the substrate so the instruction set can catch the *category* without importing the
layers that raise it — the `native.py` shape again. The kernel-boundary check caught the first version
of `ATTEMPT` importing `types` and `dispatch` directly.

`ATTEMPT` is a separate opcode rather than a flag on `INVOKE`, because failing-as-a-value and
calling-dynamically are independent capabilities that merely happened to be needed together.

### The focus

| opcode | effect |
|---|---|
| `FOCUS head [start]` | open a named head, at `root` by default |
| `FORK new existing` | a second head at the same place |
| `CLOSE head` | close a head |
| `MOVE head label [index]` | forward along a named edge |
| `BACK head [label] [index]` | backward through an incoming edge |
| `FOLLOW head key` | through a stored reference |
| `SPREAD dst head label` | fan out over an ordered one-to-many edge |
| `HEAD dst head` | the node a head points at |
| `HASFOCUS dst head` | whether the head is open and non-empty |

A move that fails empties the head rather than raising.

### Values and control flow

| opcode | effect |
|---|---|
| `CONST dst value` / `COPY dst src` | assign |
| `ADD dst a b` | sum |
| `LT dst a b`, `EQ dst a b`, `NOT dst a` | comparison and negation |
| `JMP .label` | jump |
| `JMPIF cond .label` / `JMPNOT cond .label` | conditional jump |
| `CALL .label` | push a return address and jump |
| `RET` | return |
| `HALT` | stop this program |

Control flow is by label: a bare string in the program is a jump target, not an instruction.

### Leaving the program

| opcode | effect |
|---|---|
| `INVOKE R(dst) name param=operand …` | call another stored function |
| `DISPATCH dst tool target` | reach the world, through the one door |
| `NATIVE dst name args…` | call a registered primitive by name |

`INVOKE` gives the callee a **fresh focus** holding only its bound parameters. `DISPATCH` is the only
route to an effect, and it is where prohibitions are checked, imagined targets are refused, an
observation is recorded, and the moment of the action is minted. `NATIVE` looks a name up in a table
the kernel does not populate; a native is only callable once its owner module has been imported, and
an unknown one refuses by listing what is registered.

Registered natives today are `check` (validate a node against a type), `plan` (open a planning
search) and `plan_step` (advance one).

## The assembly surface

```
# Mark a car as serviced, once we are sure it really is a car.
fn service_car(car):
    # refuse anything that is not a well-formed car
    NATIVE "check" F(car) "car"
    SET F(car) "serviced" true
```

A header is `fn <name>(<params>)` with an optional return type and an optional mock target:

```
fn list_dir(d: dir) -> listing:
fn list_empty(d: dir) -> empty_listing mocks list_dir:
```

A parameter may carry a type annotation, and that annotation is what makes candidate generation
possible: without it, nothing can ask which functions could apply to a node.

**Comments are natural language and are kept as data.** A comment block immediately above `fn`
documents the function; one immediately above an instruction annotates it; a trailing comment is a
note on that instruction. A blank line breaks a comment block from what follows. Those documents are
what an external scorer — a language model reading the function catalogue — actually reads.

**Parsing is lenient in, strict out.** A bare word parses as a string, but `dump` always emits
canonical quoted form, so the text is stable and safe to show back to a model as "here is what you
actually wrote". An unknown opcode is refused with the line number and the available set, because a
plausible-looking wrong opcode accepted silently produces a function that runs and does something
else. An instruction outside any function is refused, and so is a file with no functions in it.

```python
from ugm import asm
asm.load_text(g, text)        # parse and define
asm.load_file(g, path)        # one .mf file
asm.load_dir(g, path)         # a directory of them
asm.dump(g, "service_car")    # canonical text, round-tripped from the graph
```

## Execution

A machine carries the graph (mutated in place), registers and a focus. `run` takes a savepoint on
entry and rewinds on exception, so a program that raises halfway leaves no half-written graph — but a
rollback boundary must never span a dispatch, because nothing reaches an effect that has already
left.

`run` is a loop over `tick`, and one tick is one instruction. The program counter, call stack and
registers live in an [activation record](../execution-model.md#the-interpreters-state-is-graph-data)
in the graph, which is what lets the executor be stopped between any two instructions and say what it
was doing.

A runaway program raises at a step limit rather than truncating silently. Termination is unsolved;
failing loudly is the honest stand-in.
