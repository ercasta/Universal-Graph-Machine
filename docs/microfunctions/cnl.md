# The CNL — an authoring guide

> **What this is.** The one text surface a domain writes. Everything a domain contributes is **data** —
> goals, types, guidelines, methods, criteria — and this is how it is written. Microfunctions ship with
> the engine; nobody authoring a domain should need to touch them.
>
> **Written against the parser** (`microfunctions/intake.py`), 2026-08-01. If this document and the parser
> disagree, the parser is right and this is a bug.
>
> **⭐ Every ` ```cnl ` block below is EXTRACTED FROM THIS FILE AND PARSED by the self-test**
> (`check_the_CNL_GUIDE_parses`). That is deliberate: the previous reference was a module docstring
> nobody was obliged to update, and it had already gone stale on a whole verb family. Documentation that
> is merely *checked by a human* rots exactly like a comment does.

---

## 0. The shape of everything

One block per `read`. A header line, then an indented body:

```
<verb> <label>:
    <body line>
    <body line>          # everything after a # is a comment
```

```python
from microfunctions import intake
verb, node = intake.read(g, text)        # any family; returns what it built
goal       = intake.read_goal(g, text)   # a `goal` block specifically; refuses the other verbs
answer     = intake.respond(g, text, thread, subject)   # read it and DO the right thing with it
```

**⚠ Refusal is the feature, not an inconvenience.** Every vocabulary here is **closed**. A line that
matches no form is refused with its line number; a name that matches nothing is refused; a name matching
**more than one thing** is refused rather than guessed. That last one is the standing rule of this
project — *never identify by name alone* — and guessing between two candidates would be inventing a
referent, which is exactly what a controlled language exists to prevent.

**⚠ A refusal leaves nothing behind.** Blocks are read inside a savepoint and rolled back on failure, so
there is no such thing as a half-built goal sitting in the graph looking as though it worked.

## 1. The families

| verb(s) | builds | in one line |
|---|---|---|
| `goal` `ask` `why` `plan` | a **goal** | what must be true — same body, four things done with it |
| `type` | a **type** | a schema over a subgraph, of any depth |
| `prefer` `avoid` | a **guideline** | reorders what is tried; can never exclude |
| `method` `procedure` | a **method** | a decomposition into subgoals |
| `criterion` `directive` | a **criterion** | expert judgement: name the action to take |
| `what` `where` `when` | a **question** | locate a thing in an order the world already has |

**⭐ Three of these pairs differ ONLY in force**, and in each case the surface makes you say the word,
because force is about *failure* and cannot be inferred from what is written:

* `method` falls back to searching; `procedure` **refuses**.
* `criterion` defers the alternatives; `directive` **refuses**.
* `prefer`/`avoid` can only ever reorder — neither can exclude anything.

---

## 2. `goal` / `ask` / `why` / `plan`

The same body throughout. A goal is a set of constraints; what differs is what you then do with them.

```cnl
goal stack them:
    a on b                  # a link between two named individuals
    wh contains+ parcel     # ...at ANY depth - the `+` qualifies the relation
    b.clear = true          # an attribute value
    d.contents known        # a KNOWLEDGE claim: go and LOOK, rather than make it so
    some file               # SOMETHING of this type must exist
    a is a serviced_car     # this individual must satisfy this type

    never unstack           # a forbidden operator
    never touch c           # an individual the plan may not bind
    must paint              # the plan has to include this
    at most 3 steps         # a budget
```

| verb | what happens |
|---|---|
| `goal` | recorded, to be pursued later |
| `ask` | answered — a verdict on something that may not be true |
| `why` | explained — the history behind something that already holds |
| `plan` | **pursued**: this reaches the planner and comes back with a plan |

**⚠ `plan` stops at a plan, and that safety is structural rather than intended.** The whole search happens
on a workbench and `dispatch.service` refuses an imagined target, so a `plan` block **cannot change the
world however wrong the text is**. That is what makes it safe to put a driving verb on a surface a
language model may write. There is deliberately no verb that carries a plan out.

**⭐ The plan constraints work in a question too.** `never phone_the_registrar` inside an `ask` means *"is
this derivable without asking anyone?"*; `at most 2 steps` means *"is it derivable in two steps?"*.
Constraining the route is constraining the route, whether the route is a plan or a derivation.

⚠ **Depth is limited here to one hop**, to an attribute (`b.clear`). Not an omission — the machinery that
reads these constraints (`goal.holds`, `conflict.unsatisfiable`, `query.refutes`) keys a slot as
`(subject, key)` and would read two different wheels' pressures as one contended slot. A `type` block
takes references of any depth, because a type only ever *checks*.

---

## 3. `type`

```cnl
type car:
    is a vehicle                            # inherit another type's demands
    has 4 wheel each a wheel                # a count, a label, and what each target must BE
    has 1 body each of kind body            # ...or merely what it was minted as
    has at most 1 trailer                   # a count is a RANGE
    weight between 800 and 2000             # an attribute, bounded
    colour = "red"                          # an attribute, exact
    pressure >= 2.0                         # == != < <= > >=
    wheel[0].pressure == wheel[1].pressure  # two places inside the subgraph agreeing
    wheel[0].rim is not wheel[1].rim        # ...and not being the same node
    because a car is a car
```

Counts: `n` · `n to m` · `at least n` · `at most n` · `some` · `no` · `a`/`an`/`one` · `any`.

**⚠ A bare `has wheel` is refused.** Reading it as "at least one" is exactly what a controlled language
exists to resist: the author may have meant one, or four, or any. There is a word for each, so it costs
nothing to say which.

**⚠ `has` counts ONE named edge and does not navigate.** `has 1 ^contains` used to read `^contains` as a
label, count the targets of an edge nobody has — silently zero — and produce an unmeetable requirement
that looked fine. Depth belongs on a comparison line, which *is* navigated.

⚠ A type that demands nothing is refused: everything would be one, and that is a word, not a type.

---

## 4. `prefer` / `avoid`

```cnl
prefer washing first:
    action wash             # the operator this is about
    touching c              # ...and/or an individual it must bind
    when clear_block        # a type the subject must satisfy
    because it is cheaper
```

**⚠ `avoid` means LATER, not never.** Only `never` in a goal means never, and it prunes because it is a
proof. A guideline is an author's opinion, so it can only reorder *within* what relevance already decided —
conflating the two is how advice quietly becomes a correctness rule and hides the only move that worked.

⚠ Advice naming neither an action nor a thing is refused: it would match everything, and that is not advice.

---

## 5. `method` / `procedure`

```cnl
method service then wash:
    handles type washed_car             # which constraint sort and label this decomposes
    when car                            # a type the subject must satisfy
    because a car is washed after service
    step subject is a serviced_car      # a subgoal
    step subject.clean = true
    step subject on object
```

Also `within <method>` — only inside that method's context. It must name **exactly one** declared method.

**⚠ Steps speak of ROLES, never names** — `subject` and `object`, meaning the matched constraint's. A
method naming an individual would be *about* that individual and could not be reused.

⚠ A method with no steps is refused: it would decompose into nothing, which reads downstream as an
undecomposed goal.

---

## 6. `criterion` / `directive` — expert judgement

The list that decides what to do next. See `expert_judgement.md` for why it exists and what it measures.

```cnl
criterion clear the block that must move:
    wants link on                           # key on an UNMET goal constraint
    some top in subject by ^on              # bind a FURTHER role by walking a relation
    when top is a clear_block               # a condition
    unless wants link on from object        # a condition about the GOAL, not the world
    do unstack b = top, floor = the ground  # the action, WITH its arguments
    because nothing can be stacked while something sits on it
```

**`wants <sort> [<label>]`** — required. Sorts: `link` · `attr` · `type`. It matches an **unmet**
constraint of the goal and **binds `subject` and `object`** from it. A criterion may not name individuals,
so this is where its variables come from — and it is also exactly what an index would key on.

**`some <name> in <ref> by <link>`** — bind a further role. Transitive and nearest-first; each candidate is
tried in turn. Use `^link` to walk backwards. Declare before use; a name cannot be drawn twice.

**Conditions**, each on its own line so a reader can be told *which one* ruled a candidate out:

| form | means |
|---|---|
| `<ref> <label> <ref>` | a link holds |
| `<ref>.<key> = <value>` | an attribute equals |
| `<ref> is a <type>` | satisfies a type |
| `<ref> is there` | the reference resolves to something |
| `wants <sort> [<label>] from <ref>` | the goal still requires something of it |

`when` requires it; `unless` requires its negation.

**`do <function> <param> = <ref>, <param> = <ref>`** — required. The action *with its arguments*, which is
the whole of what a criterion adds over a guideline.

### Force

| | suppresses enumeration | when it cannot act |
|---|---|---|
| `criterion` | **defers** it — being wrong costs imagined states | falls silent; the search carries on |
| `directive` | does **not** defer — the alternatives are never built | **refuses** |

```cnl
directive always clear the pile before stacking:
    wants link on
    when subject.^on is there               # ⚠ THE GUARD — see below. Not optional.
    do unstack b = furthest subject by ^on, floor = the ground
    because a mandatory rule must say when it applies
```

**⚠⚠ Guard your directives.** *"Recognises the situation"* is exactly what the `when`/`unless` lines say,
so a directive with none recognises **every** matching unmet constraint — and refuses in all of them,
becoming a blanket veto over everything declared after it. Mandatory force obliges you to say what to do in
every case you claimed to govern. That is the price of removing the fallback.

Drop the `when` line above and the directive clears the pile, then meets a goal with nothing left on the
subject, recognises it, cannot act, and refuses — before anything declared after it is consulted. That is
not a bug; it is what you asked for by writing `directive`.

⚠ A criterion with no `wants` has no variables; one with no `do` recognises a situation and then declines
to say what to do in it. Both are refused.

---

## 7. `what` / `where` / `when`

```cnl
what it is:
    parcel
```
```cnl
where it is:
    parcel
    by contains
```
```cnl
when it was:
    by start
    parcel
```

One bare name per line — the thing asked about — optionally `by <link>` for the relation to walk.

**⭐ These have a GAP in them**, where every other verb states a whole proposition. They are answered by
locating a thing in an order the world already has, and the answer is **returned and never recorded**.

**⚠ `by` keeps the vocabulary out of the machinery.** `where` walks `contains` and `when` reads `at`
because those are conventions worth shipping as content, not because anything knows what a container or a
clock is. Keep parts in `part_of` and write `by part_of`.

⚠ The `when` here and the `when` inside an advice, method or criterion body are unrelated words. Nothing
can confuse them — only a first line is read as a verb — but do not try to unify them.

---

## 8. References — one language, four shapes

Everything that refers to something not at hand goes through `path.py`.

```
car.wheel[1].pressure     named edges, left to right; [i] indexes; [-1] counts from the end
wheel.^has                a BACKWARD hop, along an incoming edge
```

**⚠ A backward hop resolves only when EXACTLY one node points that way.** Two candidates yield nothing
rather than a guess.

**⚠ `+` is not part of a reference.** `contains+` asks *is this reachable at any depth*, and belongs in a
link position — a goal line or a query. A reference must denote **one** node and reach denotes a set, so
`a.contains+.label` is refused, with a pointer to the form that does work.

In a criterion, a reference is one of:

| shape | example |
|---|---|
| a role | `subject`, `object`, or a name drawn by `some` |
| a path from a role | `subject.^on`, `object.wheel[0].rim` |
| a selector over a traversal | `furthest subject by ^on`, `nearest object by contains` |
| a named individual | `the ground` |

**What the first segment names differs per block**, which is how one language serves surfaces with nothing
else in common:

| block | the base is | depth |
|---|---|---|
| `type` | the node being checked | **any** |
| `goal` / `ask` / `why` / `plan` | a named individual | one hop, to an attribute |
| `method` / `procedure` | a role | one hop, to an attribute |
| `criterion` / `directive` | a role, a drawn name, or `the <name>` | **any** |
| `prefer` / `avoid` | a named individual | none |

⚠ On the **right** of a comparison a bare word is a **literal**: `colour == red` compares against the
string `"red"`. To mean a reference, write one with a hop in it (`colour == body.colour`).

---

## 9. Where the language model sits

A model may **write this text**. The parser then accepts or refuses it, deterministically, in one place.
What a model must never do is reach past the surface and write graph structure directly, because then
nothing could refuse it.

That is the whole border, and it is why every vocabulary here is closed and every refusal is loud.

⚠ **`criterion` widens that border and it is a knowing trade** — a criterion body is closer to a small
program than a goal is. It is still a *pattern*: every condition is its own node, comparable, refusable at
parse time, and reportable by `criterion.governing` when it explains why something did **not** happen.
`expert_judgement.md` §5 records the argument and what it costs.
