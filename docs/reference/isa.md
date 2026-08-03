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
| `SOURCES dst node [label]` | the nodes pointing at this one |

A `GET` that finds no edge assigns nothing rather than assigning `None`. Writing that would mint an
edge to `None`, and the graph would stop being able to tell *no part* from *a part that is nothing*.

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

**Not yet reflectable: edge properties.** `EPROP` reads one named property and nothing enumerates
them, so a copy written in the surface does not carry them across. That needs `NEPROPS` / `EPROP_AT`
and is a real gap rather than a simplification — the Python copy had exactly this bug once, and
nothing failed, because no check copied an edge with properties.

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
