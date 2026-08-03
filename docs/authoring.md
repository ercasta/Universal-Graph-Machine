# Authoring

This is the one text surface a domain writes. Everything a domain contributes is data — goals,
types, guidelines, methods, criteria — and this is how it is written. Rules ship with the engine;
nobody authoring a domain should need to touch them.

The guide is written against the parser, and every ` ```cnl ` block below is **extracted from this
file and parsed by the self-test**. If this document and the parser disagree, the run turns red. The
previous reference was a module docstring nobody was obliged to update, and it had already gone stale
on a whole verb family; documentation that is merely checked by a human rots exactly like a comment
does.

## The shape of everything

One block per read. A header line, then an indented body:

```
<verb> <label>:
    <body line>
    <body line>          # everything after a # is a comment
```

```python
from ugm import intake
verb, node = intake.read(g, text)        # any family; returns what it built
goal       = intake.read_goal(g, text)   # a `goal` block specifically; refuses the other verbs
answer     = intake.respond(g, text, thread, subject)   # read it and DO the right thing with it
```

**Refusal is the feature, not an inconvenience.** Every vocabulary here is closed. A line that
matches no form is refused with its line number; a name that matches nothing is refused; a name
matching **more than one thing** is refused rather than guessed. That last is the standing rule of
this project — never identify by name alone — and guessing between two candidates would be inventing
a referent, which is exactly what a controlled language exists to prevent.

A refusal leaves nothing behind. Blocks are read inside a savepoint and rolled back on failure, so
there is no such thing as a half-built goal sitting in the graph looking as though it worked.

## The families

| verb(s) | builds | in one line |
|---|---|---|
| `goal` `ask` `why` `plan` | a **goal** | what must be true — same body, four things done with it |
| `type` | a **type** | a schema over a subgraph, of any depth |
| `prefer` `avoid` | a **guideline** | reorders what is tried; can never exclude |
| `method` `procedure` | a **method** | a decomposition into subgoals |
| `criterion` `directive` | a **criterion** | expert judgement: name the action to take |
| `what` `where` `when` | a **question** | locate a thing in an order the world already has |

Three of these pairs differ only in **force**, and in each case the surface makes you say the word,
because force is about *failure* and cannot be inferred from what is written:

* `method` falls back to searching; `procedure` refuses.
* `criterion` defers the alternatives; `directive` refuses.
* `prefer` and `avoid` can only ever reorder; neither can exclude anything.

## `goal` / `ask` / `why` / `plan`

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
| `plan` | pursued: this reaches the planner and comes back with a plan |

`plan` stops at a plan, and that safety is structural rather than intended. The whole search happens
on a workbench and the dispatcher refuses an imagined target, so a `plan` block cannot change the
world however wrong the text is. That is what makes it safe to put a driving verb on a surface a
language model may write. There is deliberately no verb that carries a plan out.

**`known` is a claim about an attribute slot, and it refuses anything else** — because the
alternative was a goal that closes itself. `repo.files known` used to be accepted, planned, and
reported done with an empty plan, having never looked: an absent slot reads as `None` rather than
*unknown*, and absence means *lacks it* by design, so the slot really was known. Two shapes now
refuse — a key naming an **edge**, and a key naming **nothing at all**. Neither is a bug in
ignorance-tracking; the mistake was letting a relation, or a typo, into an attribute-shaped claim.

So *"list all the files"* has no form here, and the refusal is the honest report of that: an absent
edge has nowhere to hang a marker, so there is nothing for a sensing action to close. Ask it with
`what` or `where` instead, or demand the structure with `has …` in a `type` block.

The plan constraints work in a question too. `never phone_the_registrar` inside an `ask` means *is
this derivable without asking anyone?*; `at most 2 steps` means *is it derivable in two steps?*
Constraining the route is constraining the route, whether the route is a plan or a derivation.

Depth is limited here to one hop, to an attribute. That is not an omission: the machinery reading
these constraints keys a slot as *(subject, key)* and would read two different wheels' pressures as
one contended slot. A `type` block takes references of any depth, because a type only ever checks.

## `type`

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

A bare `has wheel` is refused. Reading it as "at least one" is exactly what a controlled language
exists to resist: the author may have meant one, or four, or any. There is a word for each, so it
costs nothing to say which.

`has` counts one named edge and does not navigate. `has 1 ^contains` used to read `^contains` as a
label, count the targets of an edge nobody has — silently zero — and produce an unmeetable
requirement that looked fine. Depth belongs on a comparison line, which *is* navigated.

A type that demands nothing is refused: everything would be one, and that is a word, not a type.

## `prefer` / `avoid`

```cnl
prefer washing first:
    action wash             # the operator this is about
    touching c              # ...and/or an individual it must bind
    when clear_block        # a type the subject must satisfy
    because it is cheaper
```

`avoid` means **later**, not never. Only `never` in a goal means never, and it prunes because it is a
proof. A guideline is an author's opinion, so it can only reorder within what relevance already
decided — conflating the two is how advice quietly becomes a correctness rule and hides the only move
that worked.

Advice naming neither an action nor a thing is refused: it would match everything, and that is not
advice.

## `method` / `procedure`

```cnl
method service then wash:
    handles type washed_car             # which constraint sort and label this decomposes
    when car                            # a type the subject must satisfy
    because a car is washed after service
    some w in subject by wheel          # bind a FURTHER role, then speak of it below
    step subject is a serviced_car      # a subgoal
    step subject.clean = true
    step w.clean = true
    step subject on object
```

Also `within <method>` — applicable only inside that method's context. It must name exactly one
declared method.

**Steps speak of roles, never names** — `subject` and `object`, meaning the matched constraint's. A
method naming an individual would be about that individual and could not be reused.

**`some <name> in <ref> by <link>`** is how a step reaches a *third* individual the matched
constraint never names. Use `^link` to walk backwards. Declare before use; a name cannot be drawn
twice; an undrawn name in a step is refused.

It binds one thing — the nearest — and that is deliberate. A traversal reaches a set, and raising one
subgoal per member produces a plan valid only for the collection as it was when planned. For *do it
to each of them*, write the universal as a `type` and let the goal's witnesses drive it one member at
a time.

A draw whose traversal reaches nothing makes the method refuse rather than decompose: a step posed
about no individual reads downstream as a step that is simply done. A method with no steps is
likewise refused, because it would decompose into nothing, which reads downstream as an undecomposed
goal.

### Two kinds of rung: `step` and `do`

A block has one kind or the other, never both.

| rung | says | who chooses the action | decomposes into |
|---|---|---|---|
| `step <proposition>` | what must become **true** | the engine — search, with fallback | **subgoals** |
| `do <fn> <p> = <r>` | which action to **take** | you — the choice is closed | **subprocedures** |

A block of `do` rungs is a **procedure** in the strict sense: a sequence of actions, an act of faith
in whoever wrote it. It does not search and it does not fall back. The function a rung names may
itself be a procedure, so procedures decompose into procedures, and termination comes from authoring
rather than from a depth limit.

```cnl
procedure copy_the_subject:
    takes subject is a thing                        # parameters, in order; the type is optional
    do reachable start = subject as walk            # `as` names the result
    do copy_node original = walk as image           # ...so a later rung can use it
    because a procedure decomposes into subprocedures
```

**A parameter type is a precondition checked on every call**, not a hint. `takes subject is a thing`
compiles to `fn copy_the_subject(subject: thing)`, and passing anything that is not a `thing` is
refused at the call. Leaving the type off says nothing, and nothing is what it then constrains.

The check is **dynamic**, like all typing here: a type is a shape, `is_a` is computed from current
structure, and the schema is re-checked at the moment of the call. Nothing is stamped and believed —
an argument that satisfied the type an hour ago and has since lost a part is refused now. A type
nobody has declared is refused where it is written, since no argument could ever satisfy it.

**A procedure's references are its own variables**, not things in the world: each must be a parameter
(`takes x`) or a result an earlier rung named (`as x`). A rung naming an individual would make the
procedure about that individual — the same reason a `step` may only speak of roles.

**It is invoked by name, so its label must be a name.** `procedure copy_the_subject:` is accepted;
prose is not. Every other family takes a prose label because nothing calls those by name.

**It lowers to an ordinary function**, and you can read what it compiled to:

```
fn copy_the_subject(subject: thing):
    INVOKE R(walk) reachable start=F(subject)
    INVOKE R(image) copy_node original=R(walk)
    COPY R(result) R(image)
```

That is the whole executor. A sequence of calls *is* a function body, and an activation already
advances one instruction per tick on the agenda — so nothing new runs a procedure. The last
**top-level** rung's result is the procedure's result; a rung inside a block may not have run.

### Repetition and branching

Blocks nest by indentation. A line ending in `:` owns everything indented under it.

```cnl
procedure mark_the_blocks:
    takes subject
    do reachable start = subject as walk
    for each o in walk by found:
        when o is a block:
            do mark x = o
```

| line | means |
|---|---|
| `for each <n> in <ref> by <label>:` | once per target, nearest-first; `^label` walks backwards |
| `when <ref> is a <type>:` | only if it satisfies the type |
| `when <ref> is there:` | only if the reference denotes anything |
| `when <ref>.<key> = <value>:` | only if the attribute matches |
| `unless …:` | the same tests, negated |

**There is no `while`, and there will not be one.** `for each` counts the collection *once*, before the
block runs, so a body that appends to what it walks still terminates. A procedure cannot diverge —
which matters because [limits.md](limits.md) still says termination is unsolved, and a construct that
cannot loop forever needs no answer to that. It is the same restraint that stops `some … by …` in a
criterion from becoming a loop.

**Names are function-wide, not block-scoped**, because registers are. A name bound inside a block is
readable after it — but if the block did not run, reading it is refused at run time with the operand
named. This follows the target rather than pretending to a scope it does not have.

## `criterion` / `directive`

The list that decides what to do next. See [Deliberation](deliberation.md) for why it exists and what
it is worth.

```cnl
criterion clear the block that must move:
    wants link on                           # key on an UNMET goal constraint
    some top in subject by ^on              # bind a FURTHER role by walking a relation
    when top is a clear_block               # a condition
    unless wants link on from object        # a condition about the GOAL, not the world
    do unstack b = top, floor = the ground  # the action, WITH its arguments
    because nothing can be stacked while something sits on it
```

**`wants <sort> [<label>]`** is required. Sorts are `link`, `attr` and `type`. It matches an
**unmet** constraint of the goal and binds `subject` and `object` from it. A criterion may not name
individuals, so this is where its variables come from — and it is also exactly what an index would
key on.

**`some <name> in <ref> by <link>`** binds a further role. It is transitive and nearest-first, and
each candidate is tried in turn. Use `^link` to walk backwards. Declare before use; a name cannot be
drawn twice.

**Conditions**, each on its own line so a reader can be told *which one* ruled a candidate out:

| form | means |
|---|---|
| `<ref> <label> <ref>` | a link holds |
| `<ref>.<key> = <value>` | an attribute equals |
| `<ref> is a <type>` | satisfies a type |
| `<ref> is there` | the reference resolves to something |
| `wants <sort> [<label>] from <ref>` | the goal still requires something of it |

`when` requires the condition; `unless` requires its negation.

**`do <function> <param> = <ref>, <param> = <ref>`** is required. The action *with its arguments*,
which is the whole of what a criterion adds over a guideline.

### Strength

One line, and it carries two axes. `must` is the only one that touches failure; `should` and `could`
are both advisory and differ only in which is consulted first.

| line | suppresses enumeration | when it cannot act | competes |
|---|---|---|---|
| `must` | does **not** defer — the alternatives are never built | **refuses** | first |
| `should` (the default) | **defers** it — being wrong costs imagined states | falls silent | second |
| `could` | defers it | falls silent | last |

```cnl
criterion always clear the pile before stacking:
    must
    by operations                           # whose judgement this is; absent, it is `experience`
    wants link on
    when subject.^on is there               # THE GUARD - see below. Not optional.
    do unstack b = furthest subject by ^on, floor = the ground
    because a mandatory rule must say when it applies
```

**Guard your `must` rules.** *Recognising the situation* is exactly what the `when` and `unless` lines
say, so one with none recognises every matching unmet constraint — and refuses in all of
them, becoming a blanket veto over everything declared after it. Mandatory force obliges you to say
what to do in every case you claimed to govern; that is the price of removing the fallback.

Drop the `when` line above and it clears the pile, then meets a goal with nothing left on
the subject, recognises it, cannot act, and refuses, before anything declared after it is consulted.
That is not a bug; it is what you asked for by writing `must`.

A criterion with no `wants` has no variables; one with no `do` recognises a situation and then
declines to say what to do in it. Both are refused.

**A `do` line is checked against the function library where it is written**, so the function must
already be loaded, must exist, and the arguments must bind every parameter and no others:

```
do frobnicate f = subject      → refused: names no function in this library (known: unstack, …)
do unstack b = top             → refused: unstack takes (b, floor)
```

The reason is that the alternative is silence, and silence here is indistinguishable from advice that
lost. A criterion that cannot act in a situation is silent by design — *the first container happens
to be the one this goal forbids* is a situation, not a mistake. But a criterion naming a function that
does not exist is wrong in every world, for every subject, and folding that into the same silence made
a typo look exactly like judgement that did not apply.

The refusal is about what could never work, not about what does not apply here. A well-formed `do`
whose arguments happen to resolve to nothing, or to something the goal forbids, stays silent — that is
still a situation, and asking why not will tell you about it.

## `policy`

What is allowed, and on whose word. Three things that were previously sayable only from Python — a
norm about an operator, a standing prohibition on a thing, and an authority ordering between agents.

```cnl
policy house rules:
    by finance                      # whose judgement; absent, it is `experience`
    inviolable                      # or `defeasible`, the default
    forbid counterfeit              # a norm about an operator
    permit refund
    forbid touching vault           # a standing prohibition on a THING
    finance outranks operations     # an authority ordering, transitive
    because the auditor said so
```

**Line order does not matter.** `by` and `inviolable` may appear anywhere in the block and still
govern the norms above them. This is deliberately unlike `some` in a criterion, which must be
declared before use: a norm silently attributed to the wrong agent is the dangerous kind of wrong —
it parses, runs, and means something else.

**`forbid <action>` and `forbid touching <thing>` are different claims.** The first is a norm about an
operator, weighed against other norms and settled by authority. The second is a veto on a particular
node, checked at the moment of dispatch — so it blocks a call that was *planned before the
prohibition was written*, which is the order-independence the door exists to give.

**Neither is `never` in a goal block.** `never <action>` there is a **plan constraint**: it constrains
the route to *that* achievement and says nothing about anything else. A policy is standing. The two
look alike and are not, which is the near-miss this family exists to remove.

**A mistyped action name is refused here**, unlike in a goal's `never` line, which still accepts one
silently (see [limits.md](limits.md)). A norm about an operator that does not exist forbids nothing in
every world, for every agent — wrong the way a typo is wrong.

**Authority is what `tie_break`'s `authority` stage reads**, so this is where a criterion's precedence
ultimately comes from. It is transitive: if finance outranks operations and operations outranks
receiving, finance outranks receiving.

## `tie_break`

When two criteria both speak, something has to decide which one is heard. That decision is authored
here rather than built in, because *how this domain arbitrates* is domain knowledge — and a rule
living in Python is one nothing can read, quote or withdraw.

```cnl
tie_break house rules:
    authority
    force
    specificity
    random
    seed 7
    because a senior judgement outranks a narrow one here
```

One comparison per line, consulted top to bottom; the first that decides, decides.

| line | decides by | order |
|---|---|---|
| `authority` | who said it — transitively, over `authority_over` | partial |
| `force` | `must` > `should` > `could` | total |
| `specificity` | whose conditions are tighter, structurally | partial |
| `random` | a stable hash of the seed and the rule | total |
| `run <fn>` | a stored function, answering with the rule that comes first | unknown |

**The last line must decide every pair.** Two of the comparisons are partial orders — they answer
*undecided* for most pairs — so a rule ending in one leaves rules in an order nobody chose. That is
refused where it is written. `run <fn>` may never sit last, because nothing can show a function is
total.

**Nothing is ranked until you write one.** With no `tie_break` block, criteria are consulted in the
order they were declared, exactly as before.

**`run <fn>` is the escape from this table.** Ranking by seniority, by recency, by how often a rule
has been right before — none of those need a change to the engine. The function is called with the
two rules and answers with the one that comes first, or with nothing to pass.

## `what` / `where` / `when`

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

These have a **gap** in them, where every other verb states a whole proposition. They are answered by
locating a thing in an order the world already has, and the answer is returned and never recorded.

`by` keeps the vocabulary out of the machinery. `where` walks `contains` and `when` reads `at`
because those are conventions worth shipping as content, not because anything knows what a container
or a clock is. Keep parts in `part_of` and write `by part_of`.

The `when` here and the `when` inside an advice, method or criterion body are unrelated words.
Nothing can confuse them — only a first line is read as a verb — but do not try to unify them.

## One proposition grammar, in every position

A goal constraint, a method step and a `when` or `unless` condition are three renderings of the same
handful of claims. There is one recogniser, and each family decides only what to *do* with what it
recognises.

```
x l y          x l+ y          x.k = v          x.k known          x is a T          x is there
```

| | `goal` | `method step` | `when` / `unless` |
|---|---|---|---|
| `x l y` | yes | yes | yes |
| `x l+ y` — reach at any depth | yes | refused: no single edge achieves it | yes |
| `x.k = v` | yes | yes | yes |
| `x.k != v`, `< <= > >=` | yes | refused: a step is something to *achieve* | yes |
| `x is a T` | yes | yes | yes |
| `x is there` | refused: say `some T` | refused | yes |
| `x.k known` | yes | refused | refused |
| negation | via `never` (the route) | — | via `unless` |

A refusal names the form and the reason, rather than a position simply not matching.

On the right of a comparison a bare word is a **literal**, and a reference there is refused.
`a.size > b.size` would read `b.size` as the string `"b.size"`, which can never compare to a number,
so it is refused with a pointer to the `type` block, where relating two places is what the form is
for.

What is deliberately not unified is **depth**. A goal and a step take one hop; a condition takes any.
That is principled rather than accidental: the conflict checker keys a slot as *(subject, key)*, so
two navigated subjects would read as one contended slot, while a condition only ever checks. It is
asserted by a check, so a later tidy-up cannot quietly widen it.

## References

Everything that refers to something not at hand goes through one path grammar:

```
car.wheel[1].pressure     named edges, left to right; [i] indexes; [-1] counts from the end
wheel.^has                a BACKWARD hop, along an incoming edge
```

A backward hop resolves only when exactly one node points that way. Two candidates yield nothing
rather than a guess.

`+` is not part of a reference. `contains+` asks *is this reachable at any depth*, and belongs in a
link position — a goal line or a query. A reference must denote one node and reach denotes a set, so
`a.contains+.label` is refused, with a pointer to the form that does work.

In a criterion, a reference is one of:

| shape | example |
|---|---|
| a role | `subject`, `object`, or a name drawn by `some` |
| a path from a role | `subject.^on`, `object.wheel[0].rim` |
| a selector over a traversal | `furthest subject by ^on`, `nearest object by contains` |
| a named individual | `the ground` |

What the first segment names differs per block, which is how one language serves surfaces with
nothing else in common:

| block | the base is | depth |
|---|---|---|
| `type` | the node being checked | any |
| `goal` / `ask` / `why` / `plan` | a named individual | one hop, to an attribute |
| `method` / `procedure` | a role, or a name drawn by `some` | one hop, to an attribute |
| `criterion` / `directive` | a role, a drawn name, or `the <name>` | any |
| `prefer` / `avoid` | a named individual | none |

On the right of a comparison a bare word is a literal: `colour == red` compares against the string
`"red"`. To mean a reference, write one with a hop in it, such as `colour == body.colour`.

## Where the language model sits

A model may **write this text**. The parser then accepts or refuses it, deterministically, in one
place. What a model must never do is reach past the surface and write graph structure directly,
because then nothing could refuse it.

That is the whole border, and it is why every vocabulary here is closed and every refusal is loud.

`criterion` widens that border, and it is a knowing trade: a criterion body is closer to a small
program than a goal is. It is still a *pattern* — every condition is its own node, comparable,
refusable at parse time, and reportable when explaining why something did not happen.
