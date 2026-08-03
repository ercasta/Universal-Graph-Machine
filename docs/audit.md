# The horizon audit

What can only be said in Python, and for each case whether that is a decision or an accident.

The organising claim is [concepts.md](concepts.md)'s: there is a **closed class** of primitive forms
below the horizon and a **web** of authored data above it, and the way to keep the closed class small
is to make relating-in-the-web the default and force expansion to argue for itself.

## Method

Two tests, applied in order.

**1. Decompose before believing it is primitive.** The lesson from `open_workbench`: it was on a list
of primitives to expose as natives, and it turned out to be three loops and a copy. What actually
blocked writing it in the surface was one asymmetry — every graph read took a slot you had already
named, and nothing could ask *which slots are there*. Five substrate opcodes later it is an ordinary
program in `ugm/rules/workbench.mf`, and four of the six proposed natives turned out to be plain edge
reads. **A thing is primitive only after you have tried to decompose it and named what was missing.**

**2. Then choose one of three answers**, never two:

1. **Expand the closed class** — costs a member, and each must have something that runs it.
2. **Keep it opaque** — named and declared, not decomposed. An honest answer.
3. **Relate it in the web** — author rules connecting it to what exists, *without claiming it reduces
   to them*.

Mistaking (3) for (1) is Fodor's error: *kill* is not *cause to die*, and treating a network relation
as a decomposition produces a definition that is confidently wrong.

**A closed class is well formed when it is named, has an executor per member, and takes a stated
position on whether it has an escape into the web.** The failure case is a fourth thing: a closed
class that is neither named nor reachable, existing only as a Python function nobody can see.

## Register of closed classes

| class | members | executor per member? | escape | verdict |
|---|---|---|---|---|
| `consequent.KINDS` | achieve, call | yes — `method.decompose`, `criterion.speaks` | **none, stated** | ✅ well formed |
| `precedence.STAGES` | authority, force, specificity, random | yes — four comparators | **`run <fn>`** | ✅ well formed |
| `isa` opcodes | 30-odd | yes — the interpreter | none, by design | ✅ substrate |
| `loop` verbs / `IRREVERSIBLE` | imagine, look, act, run, forget | yes | none — deliberate, safety | ✅ stated |
| `intake.FORMS` | 9 families of body lines | yes — the parsers | readable via `forms_for()` | ✅ reachable |
| `types.VALUE_OPS`, `IDENTITY_OPS` | 6 + 2 | yes — `compare` | none stated | ⚠ silent |
| `goal.FORCES` | advisory, mandatory | yes | none stated | ⚠ silent |
| `norm.STANCES`, `norm.FORCES` | forbid/permit, defeasible/inviolable | yes | none stated | ⚠ silent |
| `driver.VERBS` | expand, decompose, commit, sense, refuse | **no — two are unimplemented** | **none, stated** | ✅ recorded, see F6 |
| ~~`forget.ROOT_KINDS`~~ | — | — | — | ✅ gone — now a `policy`, see F7 |
| `intake.VERBS` | 15 block verbs | yes | **none — adding one is Python, on purpose** | ✅ stated, see F5 |

The two marked ✅ *well formed* are the model: one has an escape and one deliberately refuses one,
and both say so. "Silent" means the class may be right but nobody wrote down whether it is closed on
purpose — cheap to fix, and worth fixing before the next member is added by reflex.

## Findings, ranked

### F1, F2, F3 — CLOSED: the `policy` family

All three were the same shape — *what is allowed, and on whose word* — so they cost one family rather
than three, which is what the budget beside `intake.VERBS` asks for. See
[authoring.md](authoring.md#policy).

```cnl
policy house rules:
    by finance
    inviolable
    forbid counterfeit              # F2 — a norm about an operator
    forbid touching vault           # F3 — a standing prohibition on a thing
    finance outranks operations     # F1 — an authority ordering
```

Two things fell out that were not in the plan.

**Line order had to stop mattering.** `by` and `inviolable` govern norms written above them. The
idiom elsewhere is declaration-before-use — `some` in a criterion — and it is wrong here: it would
silently attribute a norm to `experience` when the author said otherwise, and a misattributed norm
parses, runs and means something else. So the block re-attributes at seal.

**A mistyped action is now refused**, which closes half of a limit `limits.md` had recorded as open.
Only half: a goal's `never` line still accepts one silently, and that entry stands.

### F8 — CLOSED: `do` rungs, and no third executor

A `method`/`procedure` block takes one kind of rung or the other, never both:

| rung | says | who chooses | decomposes into |
|---|---|---|---|
| `step <proposition>` | what must become **true** | the engine — search, with fallback | subgoals |
| `do <fn> <p> = <r>` | which action to **take** | the author — choice closed | **subprocedures** |

**The finding is what it did not cost.** A procedure of calls looked like it needed a third executor —
`consequent.py` records that `method.decompose` and `criterion.speaks` are the two and that unifying
them was not attempted — which meant a task kind and four new branches in `loop.py`. It needed none.
A sequence of calls, each result nameable by the next, **is** a function body of `INVOKE`
instructions, and an activation already advances one instruction per tick on the agenda with its verb
reported before each step. So this is a **lowering**, and the outer loop has never heard of a
procedure — pinned by a check.

It also cost nothing from the family budget: a rung inside an existing family, not a new verb. That
was predicted by F5's economics and is the first time that prediction was tested.

The lowering emits **assembly text** and reads it back through `asm`, so it passes through the border
that validates opcodes and `INVOKE`'s operand shape rather than around it — and *"what did my
procedure compile to?"* has a readable answer stored on the authored node. A lowering nobody can see
is the island pattern with an extra step.

### F4 — CLOSED: control flow, and it cannot diverge

F8 had already changed this one's shape. *"A controlled language for functions"* sounded like a
grammar for programs; once a procedure lowered to one, what remained was two constructs.

```cnl
for each o in walk by found:
    when o is a block:
        do mark x = o
```

They arrive as two new **consequent kinds** — `iterate` and `guard` — which is the sanctioned way that
closed set grows: each member is a decision about an executor, and the executor is `method.lower`,
which emits the jumps. They are consequents rather than a separate node kind because a loop sitting
between two calls has to be *in* the rung sequence, and two edge labels would lose the ordering
between them, which is the whole content of a program.

**There is no `while`.** `for each` counts its collection once, before the block runs, so a body that
appends to what it walks still terminates — a procedure cannot diverge. That is deliberate rather than
unfinished: termination is unsolved (above), and a construct that cannot loop forever needs no answer
to it. Same restraint that keeps `criterion.draw` from being a loop.

Two bugs the build produced, both of the compile-cleanly-then-fail kind:

* **`bound` was seeded with the parameters**, inverting the one distinction it exists to make — a
  parameter is a focus head, a rung result is a register — so every program read an unset register
  where its argument was.
* **A rung inside a block became the procedure's result.** Compiled fine, then died on the final
  `COPY` when the guard did not run, turning *"the condition was false"* into a crash. Only a
  top-level rung can be the result.

### F7 — CLOSED: the keeping policy is authored text

`forget.ROOT_KINDS` was eight node kinds in a Python tuple. It is now `ugm/rules/keeping.cnl`, a
`policy` of `keep <kind>` lines, and the reasons that used to sit in a comment beside the tuple are in
it — where someone deciding whether to keep a kind will actually read them.

The comment had already started to rot, which is the argument in miniature: it carried a dead entry
naming a kind that did not exist, beside a note wondering aloud whether another was redundant. That is
what a judgement does when it is kept where nothing can argue with it.

**Cost: one line in an existing family.** No new verb, no new closed-class member — F5's economics,
tested a second time.

**An empty policy refuses rather than defaulting.** This is the one place where *nothing authored* and
*a safe default* come apart. `precedence` can answer "declaration order" and mean it; there is no
harmless reading of *keep nothing*, because it hands a sweep the whole graph. So `roots` raises and
says how to fix it.

The check earns its place by authoring a **different** policy and watching the answer change — a
policy nobody consults would keep answering the same way.

### F6 — CLOSED: recorded, not changed

`driver.VERBS` stays closed with no escape, and now says so. A search move is what the engine does
*while* deciding, one level below the criteria and methods a domain writes; a new one changes how
deliberation works, not what this domain knows. That is the exact opposite of `precedence.STAGES`,
which has `run <fn>` because ranking by seniority or recency *is* a domain's business.

The honest half is recorded too: two members have no machinery, so the set is aspirational at the
edges and membership is not proof that something works.

*Original findings, kept for the reasoning:*

### F1 — Authority has no surface, and ranking now depends on it

`precedence` ranks criteria by `authority` first. Authority is an `authority_over` edge between
agents, and there is **no CNL block that writes one**: `discourse.authority(…)` is a Python call, or a
stored function does it with a `LINK`. So the highest-precedence input to the newest decision
procedure can only be authored by the two routes the surface exists to replace.

This is the sharpest finding because it was shipped this session. It is also the cheapest to fix.

**Verdict: expand (1).** *"Finance outranks operations"* is a thing a domain says, and there is
nowhere to say it.

### F2 — The entire normative layer has no surface

`intake.py` contains **zero** references to `norm`. Norms — `forbid`/`permit`, a source, defeasible
versus inviolable, an authority ordering among them — are Python-only.

The near-miss makes this worse rather than better: a `goal` block has `never <action>`, which looks
like a prohibition and is a **plan constraint** — it constrains the route to *this* achievement. A
norm is standing, sourced, and applies to everything. Two different claims, one of which is sayable,
which is exactly the shape `limits.md` warns must not pass as a paraphrase.

**Verdict: expand (1).** This is domain knowledge by definition — a norm without a speaker is not a
norm, and speakers are already representable.

### F3 — A standing prohibition has no surface

`dispatch.forbid` mints the veto that blocks any dispatch naming a target. Python-only. Same
argument as F2 and probably the same block.

**Verdict: expand (1).**

### F4 — Function bodies are assembly-only

`asm.py`'s own docstring concedes it: *"Assembly rather than a controlled language, for now… A
controlled language is the eventual surface for functions."* Every action the system can take is
authored in ISA text. This is the friend's observation #8 and it is correct.

**Verdict: expand (1)** — and it is the largest single piece of work on this page.

### F5 — The surface's own vocabulary is closed in Python

`intake.VERBS` is a Python tuple. Adding a family — which F1–F4 all require — means editing
`intake.py`. So every finding above is structurally the same finding: **the CNL cannot grow itself.**

This is the one place where I would *not* reflexively expand. A grammar that is data is a real
research commitment, and `FORMS` already exposes the body-line vocabulary through `forms_for()`, so
the surface is inspectable even though it is not extensible.

**Verdict: opaque (2), stated.** Record that block verbs are closed in Python on purpose, and that
the cost is one edit per family. Revisit only if families start arriving faster than this.

### F6 — The planner's move vocabulary is closed, and two members do not exist

`driver.VERBS` is `expand, decompose, commit, sense, refuse`, with a companion set for *"verbs whose
machinery does not exist yet"* that raises rather than being ignored. So this closed class fails the
executor-per-member test by its own admission — honestly, and in the right direction.

**Verdict: opaque (2) for now**, but it should say so. A search move is not something a domain
authors; it is something the engine does. The gap is documentation, not capability.

### F7 — "What is irreplaceable" is a policy in a Python tuple

`forget.ROOT_KINDS` lists eight node kinds that are never forgotten. That is not a vocabulary — it is
a **judgement about value**, and it is exactly the kind of thing the web is for. The module's own
comment shows the maintenance cost: it records a dead entry (`"thread"` names no kind) and reasons
about whether `observation` is redundant.

**Verdict: relate in the web (3)** — and this is the one case on the page where option 3 is right.
*What must never be forgotten* is a claim about the domain, expressible as a type or a criterion, not
a member of a closed class. Turning it into a Python tuple was the accident.

### F8 — A procedure cannot be a sequence of actions

`method.step(sort=…)` takes a constraint sort, so a `procedure` block decomposes into **subgoals**
only. There is no way to write an ordered sequence of calls — the acts of faith that the goal
machinery itself would have to be written as.

The representation already exists: `consequent.CALL`, with a `do <fn> a = r` surface in criteria. The
missing piece is a **third executor** — `consequent.py` records that `method.decompose` and
`criterion.speaks` are the two, and that unifying them was deliberately not attempted.

**Verdict: expand (1)**, and it is the prerequisite for moving the pursuit loop above the horizon.

## Correctly opaque

Not everything needs a surface, and the test is *would a domain ever need to say this?* These are
engine services, and their being Python is a decision rather than an escape:

`graph`, `isa`, `focus`, `native`, `dispatch` (the door itself), `activation`, `thread`, `search`,
`selection`, `application`, `memory`, `clock`, `forget` (the mechanism — see F7 for the policy),
`conflict`, `query`, `plan`, `path`.

`workbench` moved out of this list this session: `reachable`, `copy_node` and `open_workbench` are
now `.mf`. `workbench.step` has not been decomposed and should not be assumed primitive — its core
looks like `INVOKE` plus minting a transformation, but it wraps a speculative run in
savepoint/rollback, and whether *that* is substrate is the next open question.

## Status

| finding | verdict | state |
|---|---|---|
| F1 authority has no surface | expand | ✅ closed — `policy` |
| F2 norms have no surface | expand | ✅ closed — `policy` |
| F3 standing prohibition has no surface | expand | ✅ closed — `policy` |
| F5 the CNL cannot grow itself | opaque, **stated** | ✅ recorded beside `intake.VERBS` |
| F8 no procedure-as-call-sequence | expand | ✅ closed — `do` rungs, **no new family, no new executor** |
| F4 function bodies are assembly-only | expand | ✅ closed — `for each` / `when`, two consequent kinds |
| F6 planner move vocabulary | opaque, **stated** | ✅ recorded beside `driver.VERBS` |
| F7 `forget.ROOT_KINDS` | **relate in the web** | ✅ closed — `keep <kind>`, `rules/keeping.cnl` |

F5 turned out to be the load-bearing one, and settling it changed the economics of everything else:
if a family costs a permanent edit to `intake.py`, then *relate in the web* is not merely the
philosophically preferred answer but the cheaper one. That is the argument for F7 without needing to
appeal to Fodor at all — and the argument for F8 being a new **rung type inside `procedure`** rather
than a new family, which costs nothing from this budget.

F8 tested that prediction and it held: a rung inside an existing family, no new verb, and — the part
that was not predicted — **no new executor either**, because the decompose-first test caught a task
kind that was not needed.

F4 then confirmed it twice over: predicted to be *"the large one"*, it cost two consequent kinds and
no new family, because F8's lowering had already done the structural work. **Every expansion on this
page turned out smaller than its first estimate, and in each case the decompose-first test is what
shrank it.**

**Every finding on this page is now closed.** Three by expansion into one new family, two by a rung or
a line inside a family that already existed, one by moving a judgement into the web, and two by
writing down a position that was already being held silently.

The pattern that held throughout: **every expansion came in under its first estimate, and
decompose-first is what shrank each one.** F8 was predicted to need a third executor and needed none.
F4 was predicted to be "the large one" and cost two consequent kinds. F7 and F6 cost no capability at
all. The one thing that did *not* shrink was `intake.VERBS` (F5) — and settling that as deliberately
closed is what made the others cheap, because it turned *relate it in the web* from the principled
answer into the economical one.

## The second pass: `workbench.step` and `execution.step`

Both were flagged *not assumed primitive, not yet decomposed*. Decomposed, they came apart almost
entirely, and what was left was **two narrow gaps, shared by both** — now closed.

`workbench.step` is a frame copy (expressible since the reflection opcodes), an outcome choice
(`mocks_of` is edge reads; `applicable` is a per-parameter type test, and `is_a` became a native for
the procedure guards), a call, and a record of it. `execution.step` is the same shape with the real
function instead of the mock, plus the deviation ladder — all comparisons over frames.

**One prediction was wrong and worth recording.** Calling a function chosen at run time was assumed
missing. It already worked: `INVOKE`'s name operand resolves through a register, at both the
instruction-set and assembly levels. Tested rather than reasoned about, which is the only reason it did
not become a third opcode nobody needed.

What was actually missing:

* **A binding set could not be built.** `INVOKE`'s bindings had parameter names fixed at assembly
  time. Now `INVOKE dst fn with node` takes them as graph data — `arg` edges carrying `param` and
  `value`. Not "a register may hold a dict": that is a Python value the system cannot read.
* **A refusal could not be a value.** `ATTEMPT dst err fn …` hands one back as a node. Separate opcode,
  not a flag — the two capabilities are independent and bundling them would be the `CLONE` mistake.

`ATTEMPT` also forced a substrate-level `graph.Refusal`, because the kernel-boundary check caught the
first version importing `types` and `dispatch` from inside the instruction set. The kernel now knows
the *category* and never the members, which is `native.py`'s shape a second time — a better design that
the existing check extracted rather than allowed.

The generalisation is in [limits.md](limits.md): **the enforcing form arrives before the answering
one**, and wherever the engine can only enforce, something above it that needs to *decide* will be
Python. That is now the most reliable predictor on either page.

`driver.py`'s phase machine sits on these two, so it is unblocked rather than separately blocked.

What is no longer measured, and should be before the next pass:

**`driver.py`'s phase machine** decomposes to almost nothing of its own. Each phase reads attributes off
the pursuit node, branches, calls one sub-stepper, writes attributes, and unlinks released sub-tasks —
reads, guards, calls, `SET`, `UNLINK`. Even the `_PHASES[phase]` dispatch is a string-to-executor lookup,
which is what a dynamic `INVOKE` now does directly.

What it is waiting on is not itself but **three predicates nobody had decomposed**. They have now been,
and the useful result is that **the three get three different answers.** The question was posed as a
choice between two — a loop over constraint nodes, or a native registered by its owner — and only one
of them is either.

| predicate | verdict |
|---|---|
| `goal.satisfied` | a loop over constraint nodes. Needs **one** substrate primitive, not a native |
| `workbench.deviates` | three instructions. Genuinely wants a native, for the reason `is_a` did |
| `workbench.unmet_expectations` | neither. Blocked upstream on a **representation**, not a capability |

### `goal.satisfied` — a loop, and the blocker was a closure

It comes apart into `met_by` (one `ATTR`), `subgoals_met` (a loop and a recursive `INVOKE`),
`world_constraints` (a loop over `requires`), `unmet` (a loop over `holds`), and `holds` — which is
where all the difficulty is. `holds` branches on four sorts, and each branch was examined separately:

* **`view` is a Python closure, and that was the real blocker.** It reads as an arbitrary callable, so
  it looks like something the surface can never hold. It is not: *every* `view` in the codebase is
  either the identity `_same` or `driver.view_in(g, frame)` — checked, not assumed. So the parameter is
  a **frame node, or nothing**, wearing a closure's clothes, and `view(subject)` is `mapping_for` then
  `image_of` — two edge reads `workbench.mf` already does. This costs no new capability at all. It is
  the same lesson as `_PHASES[phase]`: what looked like Python-only control was Python-only
  *representation*.
* **`type`** needs `is_a` (already a native) and `instances`, which is `reachable` (already
  `reachable.mf`) filtered by `is_a`. Expressible today.
* **transitive `link`** needs `path.reaches` — a cycle-safe worklist walk, which is exactly
  `reachable.mf`'s shape, seen-map and all. Expressible today.
* **`known`** asks whether a slot holds `UNKNOWN`, and **the surface cannot name `UNKNOWN`.** `null`
  parses to `None`, which means the opposite — *lacks it*, not *has not been looked at* — so writing
  the test with `null` would silently answer the wrong question about the wrong distinction.
* **`attr`** needs `types.compare`: seven operators, and *total*, answering `False` where Python
  raises. Dispatching on the operator is an ordinary `EQ`/`JMPIF` chain. Totality is not: `LT` raises
  on a string against a number, and nothing in the surface can ask whether two values are comparable
  before trying. `ADD` raises the same way; `ATTEMPT` catches `Refusal` and deliberately not
  `TypeError`, and stretching it to would turn program bugs into a quiet `err` nobody reads — the one
  thing that comment exists to forbid.

The last two look like two gaps and are one. Both are questions about **what category a value is**, and
the surface has no way to ask — the same asymmetry the reflection opcodes closed for nodes, one level
down: every comparison takes an ordering you have already assumed, exactly as every graph read used to
take a slot you had already named. One opcode — call it `VKIND`, reporting `text` / `number` /
`boolean` / `null` / `unknown` / `list` — closes both, and `compare` becomes an ordinary `.mf`.

**`VKIND` reports the category and must not decide the ordering.** Python orders `bool` with `int` and
`float`, so `compare('<', False, 1)` is `True` today. It would be tempting to fold `boolean` into
`number` and make the order class fall out of one `EQ` — and that is the `CLONE` mistake again: *which
categories order together* is a decision, and a primitive that bakes it in is a composite wearing
substrate's clothes. The opcode says `boolean`; `compare.mf` maps categories to order classes itself.

**Not built yet, deliberately.** `types.compare` is the one comparator shared by `goal.holds`,
`criterion._holds` and every schema check, and its own docstring records that a second implementation
was the drift this codebase keeps finding. Writing `compare.mf` before `holds` moves into the surface
would *create* that second implementation and leave it doubled for the length of the rewrite. `VKIND`
and `compare.mf` land together with `holds`, replacing the Python rather than shadowing it.

### `workbench.deviates` — the answering form again

One `ATTR` for `expects`, one null guard, one call to `types.violations`. There is nothing to
decompose; it is already three instructions. What it cannot do is *call* `violations`, and this is the
predictor from [limits.md](limits.md) landing on the nose: `types.check` raises and `types.is_a`
answers, and `is_a` is a native for that reason — but `is_a` answers only yes or no, and `deviates`
has to say *how*, which is what `violations` is. **`violations` is `is_a`'s answering form, and it
should be a native beside it, registered by `types.py`, which already owns both.**

This is the one place where reaching for a native is right rather than lazy, and it is worth being
explicit about why, given that reaching for one was wrong three times during the audit. Decomposing
`violations` does not reach a loop over nodes: it reaches `requirements`, which compiles a declared
type into `Req` / `AttrReq` / `Rel` dataclasses — a Python-side representation of a type that nothing
in the graph mirrors. Lifting *that* is a real arc and a much larger one than the phase machine. The
native is a boundary drawn where the layer actually ends, not a shortcut around a loop.

The work in it is the return value: `violations` hands back `{label: (expected, actual)}`, and a
native must hand back a node.

### `workbench.unmet_expectations` — blocked on a representation

All three of its arguments are Python values — `prediction` is a dict of tuples, `bound` is a dict,
`minted` is a list — and it returns English strings. So it cannot be lifted on its own, and its own
shape is not what is stopping it: the loops are ordinary, and `ADD` concatenates strings, so even the
messages are expressible (checked).

The blocker is upstream, in `predicted_changes`, which produces that dict. Its docstring argues at
length that expectations are derived from two frames and **never recorded**, because recording
expectation nodes would assert what the structure already entails — a labelling error, and a node per
imagined step of which the driver makes hundreds. That argument is right, and it is about *storage*.
It does not reach the *interchange*: the dict is already a materialised expectation, minted every time
this runs, and the only thing the choice of a Python dict buys is that nothing but Python can read it.

So the fix is that `predicted_changes` yields a **transient node, dropped by its caller** — which is
what `reachable.mf`'s scratch `walk` node already is, and is not the same thing as storing an
expectation on the plan. Until that lands, `unmet_expectations` is not blocked on a missing capability
and adding one for it would be building against the wrong wall.

### What this changes

The phase machine's three dependencies cost, in total: **one substrate opcode** (`VKIND`), **one
native** (`types.violations`), and **one representation change** (`predicted_changes` returning a
node). None of the three predicates needs the "richer guard tests" the open question assumed, and two
of the three needed nothing that could be called a capability at all.

The other dependency is `execution.step` itself, which the phase machine calls and which is expressible
but not rewritten.

**Neither `workbench.step` nor `execution.step` has been rewritten in the surface.** They are now
*expressible*, which is a different claim from *done*, and the difference should not be allowed to
blur: the gaps were found by decomposing on paper and closed by adding the primitives. The rewrite —
and the measurement of what it costs in speed — is outstanding.
