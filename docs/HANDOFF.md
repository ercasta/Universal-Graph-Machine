# Handoff

Read this first when picking the project up cold. It says where things are, what state they are in,
what to do next, and which mistakes have already been made so they need not be made again.

**Verify:** `python -m ugm.selftest` — currently **259 checks, 0 failing**, in 90–120 seconds depending
on the machine. ⚠ The wall-clock numbers below drift with the host: measured twice in one session, the
same commit gave Sussman 1500 ms and 1920 ms. **Compare a change against the tree you changed, in the
same minutes** — `git stash -u`, measure, pop — never against a number written down earlier.
**Measure:** `python -m ugm.bench` — the numbers below, re-runnable.

The engine is `ugm/`. An earlier iteration lived in `microfunctions/` and the package was renamed;
anything still pointing at `microfunctions/` or `docs/microfunctions/` is stale.

## Where to read

| you want | read |
|---|---|
| what the machine is | [overview.md](overview.md), then [concepts.md](concepts.md) |
| what a domain can write | [authoring.md](authoring.md) — the one text surface |
| how it runs | [execution-model.md](execution-model.md) |
| what it cannot do | [limits.md](limits.md) — kept deliberately honest |
| what is only sayable in Python, and why | [audit.md](audit.md) |
| dispatching on a condition rather than a type | [predicate-dispatch.md](predicate-dispatch.md) — slices 1-2 built |
| advice about the *order* of a plan's actions | [advice-over-sequences.md](advice-over-sequences.md) — a design thread, nothing built |
| making the open class converge on one terminology | [harmonization.md](harmonization.md) — a design thread, nothing built; probes first |
| why a rule never calls `GET` | [mediated-access.md](mediated-access.md) — built; the note is the argument behind it |
| the instruction set | [reference/isa.md](reference/isa.md) |

## Current state

The system takes goals as text, plans by imagining on a workbench, acts through one guarded door,
notices when reality disagrees, and answers questions with the derivation that produced the answer.

A **capability audit** ([audit.md](audit.md)) found everything that could only be said in Python and
decided, case by case, whether that was a decision or an accident. All eight findings are closed, and it
produced `policy`, `procedure`, `tie_break`, five reflection opcodes, `ATTEMPT` and
`INVOKE … with <node>`.

Since then the work has been moving the **workbench** out of Python, and that arc has now landed:
**frames are sparse**, and a frame maps only what changed in it. Two constraints decided the
architecture, and neither is about performance:

* **The workbench cannot stay in Python.** Planning that Python owns is planning the system cannot
  inspect or change.
* **Lowering stops above the instruction set** — at a *named call*, never an opcode. A name is where
  meaning lives (the call graph is the semantic net) and it is what lets linking happen at run time, so
  the machinery can change what a read *means* without editing a single rule.

Together those say mediation can live neither in the kernel nor in Python, which leaves in-graph
procedures. That is [mediated-access.md](mediated-access.md), and **the mechanism is now built**: a rule
reaches the graph through eight closed names, each of which asks the ambient context how to resolve a
node and calls the resolver *by name*. `workbench.step` and `execution` establish; everything beneath
inherits by walking `caller`. The planning corpus is written that way and the planner reads it exactly as
it read the opcode version.

And what it was all for is now built. **A frame maps only what changed in it**; `step` copies nothing;
a version is minted by the writer the first time a frame writes to a node; and reading walks the chain.
The rule the whole scheme rests on is one sentence:

> **An edge names an identity, never a version, and resolution happens on the target.**

That sentence is the model. Nothing rewrites edges any more — not `_copy_set`, not the writer, not
`relate` — and a rule is bound to *the thing itself* in both worlds, so one rule really does have one
behaviour and only what a read means differs.

**Stepping now costs O(change) rather than O(world)**, which is the shape the whole design was for:

| world | dense (before) | sparse (now) |
|---|---|---|
| 5 blocks | 47 ms | 53 ms |
| 60 blocks | 68 ms | 56 ms |
| 300 blocks | 198 ms | 59 ms |

Ten chained steps, best of three. Dense wins the small row and that is expected rather than
disappointing: the copying moved from Python into an interpreted `copy_with_edges`, so a five-node copy
got dearer and a three-hundred-node one stopped happening. The curve is the result, not any row.

`workbench.step` written in the surface was **3.0×** the Python one, against 22–42× before — because
`carry_frame` was essentially all of that, and sparse frames deleted it. **And it is now the live one.**

### The swap landed

`workbench.step` is a **thin Python wrapper around `rules/step.mf`**. It describes the bindings as a node
— a Python dict is not something a rule can be handed — invokes `step`, and hands back the
`(frame, transformation)` pair every caller already read. `_python_step` is kept immediately below it as
the reference the surface is checked against, which is the answer to two implementations of one thing:
compare them in a check rather than delete the one nothing measures.

Three things came out of doing it, and only the first was expected:

* **The cost is a decision, not a veto.** The suite goes 60 s → 90 s and Sussman's anomaly 1020 ms →
  ~1450 ms at the identical 50 imagined states. `stepping` now reads **1.3–1.6×** rather than 3.0×,
  because the live path passes `retain=False` and the reference it is measured against is
  `_python_step`.
* **A piece of Python was deleted rather than moved.** The Python `step` had to unlink its half-written
  frame by hand when the call raised — the chain must be linked *before* the call, since resolution walks
  it. A microfunction's writes are journaled, so a `step` that *is* a microfunction rolls back whole and
  the frame was never minted. The unwinding was written into the wrapper first and *then* found to be
  dead code. `check_a_step_that_RAISED_is_not_in_the_history` now guards that the step is inside the
  transaction.
* **A boundary's establishing activation is now scaffolding.** The Python established the context and
  passed it `under=`, so the callee's activation answered `establishes`. The surface establishes on its
  *own* activation with `SELF`, and the call discards that — so *which world was this step imagined in*
  is answered through the frame the context points at, which is where `discard` already looked for it.

⚠ **Where the Python still is.** The arc is not finished, and the shape of what remains is easy to lose:

| | state |
|---|---|
| `workbench.step` | ✅ **live** — `rules/step.mf`, behind a wrapper; `_python_step` is the reference |
| `workbench.open_workbench` | ✅ **live** — `rules/workbench.mf`, same shape; `_python_open_workbench` is the reference |
| `copy_set` / `reachable` | ✅ **live** via `open_workbench`; the Python `reachable` stays for `view=` callers |
| `execution.step`, `driver._phase_*` | **not written** — and blocked by the row below |
| `workbench.deviates` | ✅ **live** — `rules/deviate.mf` + the `violations` native |
| `workbench.unmet_expectations` | ✅ **live** — `rules/unmet.mf`; `predicted_changes` returns a node and the prose moved to `explain_unmet` |
| `goal.holds` | **written** (`rules/holds.mf`) and checked, **not live** — the planner holds a view, not a context; see step 4 |
| the mediation layer (`access` / `resolve` / `version`) | ✅ live |

**Both swaps are done, and the doubling is gone.** What is left of each Python original is a *reference*
implementation — `_python_step`, `_python_open_workbench` — which exists to be compared against in a
check rather than to run. That is the answer to two implementations of one thing: a check that compares
them, not a deletion that leaves the surface unmeasured.

## What landed since the audit

Detail and reasoning in [audit.md](audit.md) and [mediated-access.md](mediated-access.md); this is the
index, kept short on purpose so the plan below stays readable.

**The last session, in one paragraph**, because the entries below are in the order things were built
rather than in the order they matter: `step` and `open_workbench` were **swapped live** behind thin
wrappers, so nothing in the workbench exists twice any more; **mediation is enforced** — `step` refuses
to imagine an unmediated operator, and the compliance pass runs over every corpus; and all three
decomposed predicates were written, two of them live. Four lessons came out of it that generalise past
their occasions, and they are in *How to work on this* at the bottom: **moving to the surface deletes
Python rather than porting it**, **a predicate that answers in prose cannot move**, **a dormant twin
rots**, and **measure the blast radius before building the enforcement**.

* **The three predicates were decomposed**, got three *different* answers, and **all three are now
  written** — which is the last session's work and the reason the plan below starts at item 3.
  `goal.holds` needed `VKIND` and `rules/compare.mf`, and its Python view-closure turned out not to need
  replacing at all; `workbench.deviates` needed the **answering** form of `is_a` (the `violations`
  native, which hands the answer back as a node); `workbench.unmet_expectations` needed no capability and
  was blocked twice by *representation* — a Python dict going in and **prose** coming out. Two are live,
  `holds` is written and checked but waiting on the planner to establish a context. Detail in item 4.
* **`copy_set` moved to the surface** carrying edge properties, and `open_workbench` shares it. Cost:
  `NEPROPS`, `EPROP_AT`, `SETEPROP`, `graph.put_edge_props`.
* **`SELF`** (a program's own activation) and **`REFUSE kind why`** (the surface can decline).
  `SOURCES` was replaced by **`NSOURCES` / `SOURCE_AT`**.
* **A call now discards its own scaffolding** unless the call site says `keep`, and `INVOKE`'s function
  operand takes a focus head. The first of the two mattered enough to be listed as a prerequisite for
  everything below; both are in [reference/isa.md](reference/isa.md).
* **`workbench.step` is written**, in `rules/step.mf`, checked against the Python on four routes plus
  chaining and a refusal. Two natives added: `find_function` and `minted`. It is sparse too, and it
  **establishes its own context in the surface** — a context is a node and `establish` is an edge onto
  the activation `SELF` names, so a boundary needs no Python. **And it is now the live one**, behind a
  wrapper, with `_python_step` kept beside it as the reference the checks compare against.
* **Mediated access is built** — `access.py`, `rules/access.mf`, `rules/resolve.mf`, two natives
  (`resolver`, `context`), and the planning corpus rewritten to the eight names. Detail in
  [mediated-access.md](mediated-access.md), which now opens with what landed and what did not.
* **The corpus is mediated.** All 52 rules that are stepped on a workbench reach the graph through the
  eight names — measured by instrumenting `workbench.step` over the whole suite, not by reading, and the
  closed set covered every opcode they used. `asm.load_text` **links**: a body calling the vocabulary
  gets the vocabulary loaded, so no caller keeps that precondition by hand.
* **Resolution is indexed.** A frame carries a stored reference from identity to the version it holds
  (`workbench.index`), read by Python and by the surface alike. See the traps below for why.
* **Sparse frames landed, and with them the identity model.** `step` copies nothing and binds
  identities; `_copy_set` and `copy_set` no longer rewrite edges; frame 0's copies point at real nodes;
  an imagined node is **its own original**, stated positively, so later versions of it have an identity
  to share. `dense` is gone. `path.adjacent` is the one hop everything traverses through, and it takes a
  view; `workbench.View` answers both directions (identity → version, and back).
* **Two of the four natives now resolve.** `types.is_a` and `types.check` find their world through
  `workbench.view_of`, which reads the ambient context. `plan` and `plan_step` still do not.
* **`function.invoke` checks a parameter type in the world the body will run in**, resolving the
  argument through the context's resolver *by name* (`access.resolved`). A precondition read from reality
  while the body it guards reads a frame is a rule refusing a state it is being run in.
* **`dispatch` refuses on the context, not on the argument.** *Am I imagining?* is a property of the
  dynamic extent. See the traps.
* **There is a benchmark in the repo** — `python -m ugm.bench`.
* **Predicate dispatch — a name may mean several bodies, and the world picks.** A function states
  `when` / `unless` conditions in its own `.mf` source; `fn.select` takes the most specific applicable
  body, `precedence._covers` orders them, and declaration order breaks every tie the partial order
  cannot. `invoke` selects before it loads; `driver.establishes` unions over the bodies.
  `driver.enumerate_frame`'s hardcoded *no node in two roles* is gone and `stack` says it itself.
  Cost: nothing measurable. [predicate-dispatch.md](predicate-dispatch.md) has the argument — the short
  version is that the alternative is **name mangling**, and a mangled name buries the distinguishing
  condition in an identifier where nothing can read it, which is an island per sense.
* **`x is y` used to parse as a link labelled `is`** — silently matching nothing, in every family using
  the shared proposition grammar. Recognised now, as the `same` sort; a condition builds it, a goal and a
  method step refuse it with a reason.

Traps worth not re-learning:

* ⚠⚠ **Moving something into the surface can make Python bookkeeping around it obsolete, not portable.**
  Two pieces of the Python `step` had no counterpart to write: the failed-call unwinding (the journal
  does it) and passing the context `under=` a call (the surface establishes on `SELF` and the callee
  inherits). Both were reproduced first and then removed. Ask what the Python was compensating for
  before translating it — the answer is sometimes *for being Python*.
* ⚠ **Lazy linking moves a cost across a node-count baseline.** `step` loads `rules/step.mf` into a graph
  the first time it is called there, which is right — a name is only meaning if something answers it —
  but a check that snapshots `len(g.nodes)` before the first step now counts ~680 nodes of library as
  workbench residue.
* ⚠⚠⚠ **Binding a rule to an identity makes an unmediated rule loudly wrong instead of accidentally
  right.** While `step` handed over the frame's copies, a bare `LINK F(d) …` landed in the frame by
  luck. Bound to the thing itself, the same instruction **writes to the real world while planning**.
  Roughly a dozen test fixtures were unmediated and every one of them turned a check red until it was
  rewritten to the vocabulary. `access.offenders` is the pass that says so, it now runs over **every**
  corpus, and `step` **refuses** an unmediated operator outright — see item 5.
* ⚠⚠⚠ **`dispatch.service` refused an *imagined target*, and there is no longer such a thing.** The
  safety property — planning cannot reach the world — was implemented by asking whether the target was a
  workbench copy. Under identity binding the target of a dispatch inside a plan is the *real* node, so
  the guard silently stopped firing and a plan **actually listed a directory**. The property was always
  about the dynamic extent: `dispatch.imagining` asks the context instead. Both tests are kept, because
  they catch different mistakes.
* ⚠⚠ **`relate` resolved its target as well as its subject**, so an edge stored a *version*. Two routes
  to the same world then looked different, `state_of` stopped deduping, and Sussman's anomaly went from
  50 imagined states to over 100 — with every individual answer still correct. **Cost was the only
  symptom**, and it took a version-by-version diff of two states that should have been equal to find.
* ⚠⚠ **`visible` must answer in the order the world was first laid out, not the order it changed.**
  Walking nearest-first and keeping the first answer puts whatever the step touched at the front, so the
  world's order differed in every frame — and that order is `proposals` order, which is the search's last
  tie-break. Deterministic, and worse. Walk oldest-first and let later versions replace earlier ones in
  place.
* ⚠ **The chain must be linked before the call, and unlinked if the call raises.** Resolution walks
  `frame -next-> frame`, so an unattached frame is one in which nothing is visible. But an imagined step
  that raises — arithmetic meeting `UNKNOWN` is routine — would then leave a half-written frame wired
  into the history.

* ⚠⚠ **`g.sources` returns its answer sorted by node id**, and an id is a string, so the reverse index
  cannot answer *the most recent*. An activation records its calls forwards as ordered `called` edges
  because of this. **A benchmark caught it, not a check**, and three successive guards passed with the
  defect planted — the surviving one drives the id counter across a power of ten on purpose.
* ⚠ **A recorded gap statement is a hypothesis, not an inventory.** The edge-property gap was documented
  as needing two reading opcodes; it needed a third to *write*.
* ⚠ Doc-comment blocks attach to the next `fn`, so inserting a function between a comment and its `fn`
  silently orphans the docs.
* ⚠⚠⚠ **A helper that scans the whole graph hides until something calls it a lot.** `Graph.labels`
  derived a node's labels by scanning every edge key in the graph, and `drop` calls it once per node —
  invisible for years, then **70% of a planning run** the moment calls began discarding their own
  scaffolding. It is a maintained index now. The lesson generalises past this instance: the profile named
  a function nobody had touched in the change that made it hot.
* ⚠⚠ **An index belongs above the horizon, and the mechanism below it.** Locating a version by asking the
  reverse index which mappings name a node, then asking each which frame it was in, is O(versions) with
  an allocation per hop — and it made the search-heavy checks 30× slower. The fix was not a cleverer
  walk: the frame carries a **stored reference** from identity to version (`workbench.index`), which is
  the substrate's ordinary key-to-node map knowing nothing about frames, while the decision to key it by
  identity is the workbench's. One check went 155 s → 5.1 s. Python and the surface read the *same*
  index, so the two walks cannot drift.
* ⚠⚠ **A static reader that loses information gets slower before it gets wrong.** Disabling
  `access.as_opcode` — which lets `driver._effects` see through a mediated call — reddens seven checks
  and takes the suite from 59 seconds to minutes, because a planner that cannot see what a rule
  establishes ranks everything alike and the search explodes. Look at the clock, not only the report.
* ⚠ **`unparse` dropped the `with` keyword**, so a function using the graph-data binding form dumped to
  text that would not parse back. The round-trip check covered only the form that worked. Fixed.

## Where the cost is

Run `python -m ugm.bench`. The current numbers, and what each one is for:

| | |
|---|---|
| Sussman's anomaly | **~1450 ms**, 50 imagined states — 1020 ms with the Python step, 640 ms before sparse frames |
| a step, 5 / 60 / 300 blocks | **~105 / ~115 / ~105 ms** — against 53 / 56 / 59 for the Python step, and 47 / 68 / 198 dense |
| live `step` vs `_python_step` | **1.3–1.6×** — against 3.0× measured before the swap |
| a mediated read vs a bare `GET` | **3.5–4.7×** |

The second row is the one the design was for: **cost follows change, not the size of the world** — flat
across a sixtyfold range, where dense was linear. The whole row moved up when the surface `step` went
live, and the shape did not. The first row is what a five-node world costs for it, where copying four
nodes in Python was cheaper than minting two versions through an interpreted `copy_with_edges`. All of
these are true together, and quoting any one alone misrepresents the change.

⚠ These are noisy — ±10% run to run on the same machine, and `scaling`'s three columns are within noise
of each other, which is the point rather than a defect in the measurement. Compare shapes and factors,
never single milliseconds.

**The workbench cannot stay in Python**: planning that Python owns is planning the system cannot inspect
or change, which is the island the whole design exists to avoid. Sharing versions between frames is only
correct if reads are mediated — and mediation can live neither in the kernel (it would have to know what
a frame is) nor in Python. That is why the mediation layer exists, and it is now load-bearing rather than
anticipatory: a native that ignores the context can finally be *caught*.

## What to do next

**The arc is de-Pythonization, and it is unfinished.** Everything in this section before item 5 is that
arc; items 5 onward are correctness or capability. Nothing in the workbench exists twice any more — the
next Python is in the *loop around* it.

### 1. ✅ `step.mf` is live · 2. ✅ `open_workbench` and `copy_set` with it

Both done, both as thin wrappers. See *The swap landed* above for what `step` cost and what it taught.
The wrapper was the whole trick — rewriting every caller first would have made the measurement expensive
to take and expensive to undo, which is how a swap turns into a commitment before it is a result.

`open_workbench` cost nothing measurable (suite ~88 s, Sussman ~1520 ms, both unchanged): it runs once
per workbench where `step` runs once per imagined state. Three things it needed that the dormant version
did not have, all of which had arrived beneath it since it was written: `label` / `parent` / `explores`
as parameters, and — the load-bearing one — `SETREF frame identity mapping`, the frame index. Its absence
does not degrade gently; the next step raises on an unset register.

⚠ The lesson that generalises to `execution.step` below: **a dormant implementation rots against the
thing it shadows.** `rules/workbench.mf` was written, checked, and left dormant, and in that time the
index landed, the mapping loop grew a line, and three parameters appeared. The check that compared them
kept passing, because it only ever called the one-argument form. *A comparison check is only as strong
as the routes it takes through both sides.*

### 3. `execution.step`, then the phase machine

The last big Python island in the plan-act-check loop. `driver._phase_*` is reads, guards, one call,
attribute writes and unlinks; its `_PHASES[phase]` dispatch is what a dynamic `INVOKE` does.

⚠ **It is blocked by item 4, not merely adjacent to it** — `execution.step` calls `W.deviates` and
`W.unmet_expectations`, both of which are now live. That is the one place the ordering in this list was
wrong.

⚠⚠ **And item 4 now points back at this one.** `goal.holds` is written and checked but not live, because
a Python caller holds a **view** while the surface gets its world from the ambient **context**. The
planner establishing a context is this item's work, and it is what makes `holds.mf` swappable — so the
two are one piece of work, taken from either end.

⚠ And it reports in **prose** in several places (`_diverge(why=…)`, `_note`). See item 4 on
`unmet_expectations`: prose is a rendering decision, and a predicate carrying one cannot move to the
surface. Expect to split each of them the same way — facts on the node, sentences at the edge.

The two swaps above are the template: **write the wrapper first**, keep the Python beside it as
`_python_*`, and point the comparison check at the reference rather than deleting it. And take the
comparison check through *every* route the wrapper offers — that is what `workbench.mf`'s dormant years
cost.

### 4. The predicates that block the rest — two of three done, and the third's prerequisites are in

⚠ **Item 3 depends on this one**, which the ordering above did not say: `execution.step` calls
`W.deviates` and `W.unmet_expectations`, so it cannot be written above them.

* ✅ **`workbench.deviates` is `rules/deviate.mf`.** What kept it in Python was never its control flow —
  it is one branch and one cast — but that nothing could say *how* a cast failed. `check` insists,
  `is_a` answers yes-or-no, and the new **`violations` native** (`types.gather_violations`) completes the
  trio by handing the answer back as a **node**. Enforcing form before answering form, again: finding one
  half of a pair is the standing reason to look for the other. The wrapper renders the node back to the
  `{label: (expected, actual)}` dict its callers read, and that translation dies when `execution.step`
  moves and reads the node directly.

  ⚠ It found one thing Python had been hiding: **a null result.** `deviates(tr, None)` is ordinary — a
  call can return nothing — and Python answered it by accident, because `violations(None, …)` has a case
  for it. The instruction set *refuses* an operand that holds nothing, on purpose, so the surface had to
  state the case. The refusal is right and the fix is one branch; the general shape is that moving to the
  surface turns a permissive Python default into a decision somebody has to write down.

* ✅ **`workbench.unmet_expectations` is `rules/unmet.mf`.** The audit said it needed *no capability at
  all*, which was true and not the whole story: it was blocked twice, both times by **representation**.

  Its **input** was a Python dict. `predicted_changes` now returns a **transient node** — one ordered
  `expect` edge per expectation, each carrying its own `sort` (`attr` / `link` / `kind`), so a reader is
  one loop rather than three, and `sort` is exactly the kind of condition a dispatching predicate would
  select a body on. The caller drops it (`drop_prediction`), like `reachable`'s walk.

  Its **output** was **prose** — `f"expected {key}={want!r} but found {got!r}"` — and that is the half
  worth remembering, because it looks like a weakness of the surface and is not. ⭐⭐ **A predicate that
  answers in prose cannot move.** `repr` is a *rendering* decision, and a rendering decision inside a
  predicate is a second thing the predicate is for. Split — the predicate answers with facts, one table
  (`_UNMET_PHRASE`) renders them, `explain_unmet` is what `execution.step` calls — the rest was a
  transcription. **Carry this into `execution.step`**, which reports in prose in several places.

  ⚠ Two things the graph made you say out loud that the dict got for free. A tuple slot could hold
  `None` to mean *expected to be cleared*; an attribute holding `None` is simply **absent**, so the node
  says it with `mode` (`exact` / `set`) — clearer than the `"<set>"` magic string it replaces. And the
  Python reference stored the named target of a `missing_edge` as an **attribute** while the surface
  `LINK`ed it; `explain_unmet` reads it with `g.target`, so only one of those spellings works. The
  comparison check caught it — the two answers differed by exactly that field.
* **`goal.holds`** — ✅ its two prerequisites landed together, as predicted. **`VKIND`** (a value's
  category: `nothing` / `unknown` / `truth` / `number` / `text` / `other`) and **`rules/compare.mf`**,
  which is `types.compare` written in the surface. Totality was the whole difficulty: `LT` is Python's
  `<`, so a string against a number raises, and a program cannot catch — it has to ask first.

  Checked exhaustively rather than by example — every operator against every pair drawn from numbers,
  truths, texts, `nothing`, `UNKNOWN` and a value of no named category, about a thousand cases. Two
  disagreements, both `()` against itself under `<=` / `>=`, and they are **named in the check** rather
  than excluded from it so the difference cannot widen unnoticed.

  ⚠ `compare.mf` is **not** the live comparator for Python callers, and that is a decision:
  `types.compare` sits under every schema check, which is the hottest path in the system, and an
  interpreted call there is paid on every `is_a` in every search. The surface calls `compare.mf`, Python
  calls `types.compare`, and the check holds them together. When `types.fails` itself moves, this
  becomes one implementation again.

  ⚠ It reproduces one of Python's rules rather than improving on it: a truth orders against a number,
  because `True < 2` is True there. Being stricter would be defensible in isolation and wrong in
  context — there is *one* comparison, and two spellings disagreeing about a single pair is exactly what
  a shared comparator exists to prevent.

* **`goal.holds` is written** — `rules/holds.mf`, all four sorts, checked against the Python **twice per
  constraint**: once in reality and once inside a frame where the answers differ. That second reading is
  the point; agreeing only in the real world is what a predicate that quietly ignores the context looks
  like. Two natives were added, both the *must resolve* kind: **`reaches`** (one-or-more hops with the
  cycle protection a surface rewrite may not approximate) and **`instances`** (enumeration by traversal —
  handing the surface a whole-graph scan is what `types.instances` refuses at length).

  **The closure was not replaced, it is gone.** A rule in the closed vocabulary resolves through the
  ambient context, so every `view=` in the Python is machinery for a problem the surface does not have.

  ⚠⚠ **A gap in the vocabulary, found by writing this.** `related` resolves the node it reads *from* and
  returns the target **unresolved** — right, because an edge names an identity. That is invisible while
  the answer is fed to another vocabulary call, since `slot_of` resolves its own subject; it appears the
  moment the answer goes to something that does not, and `is_a` is exactly that — it resolves the
  neighbours it walks but takes the node it is asked about as given. Handing it an identity asks about
  *reality* while the rule around it reads a frame. `holds` spells the resolution out (`here_now`, three
  instructions, the resolver called by name, as `access.resolved` does from Python) rather than adding a
  ninth vocabulary member: **an island is created by the second caller**, and today there is one. A
  second rule needing *this node, here* is the moment to make it a member.

  ⚠⚠ **It is not swapped live, and the blocker is a seam rather than a cost.** A Python caller holds a
  **view**; the surface gets its world from the ambient **context**. `driver` calls `unmet(…, view=…)`
  with no context established, so a wrapper would have to mint a context per call — which is the wrong
  fix. The right one is for the planner to establish a context, and that is item 3's work. Until then
  `holds.mf` is checked against the Python rather than running, and the check is what stops it rotting —
  see what `workbench.mf` cost by sitting dormant with a comparison that only took one route.

### 5. ✅ Mediation is enforced at `step`

Done, both halves. `step` **refuses to imagine an unmediated operator** — `REFUSE "UnmediatedOperator"`
— and the compliance pass runs over **every corpus the self-test builds**, enumerated by reflection
rather than from a list.

The verdict is decided once, in `function.define`, and stored as `mediated` on the function node: it
cannot change after the body arrives, and asking `access.bare_touches` per step would mean loading the
body back out of the graph on the hot path. The vocabulary is exempt by name, from `access.VOCABULARY`,
which is the same set `offenders` reads — so the two exemptions cannot drift.

What the work actually found, in the order it found it:

* **The blast radius was one.** Before building anything, `workbench.step` was instrumented over the
  whole suite to ask which operators are ever *stepped* while unmediated. The answer was a single
  `git_status` in one inline fixture — so enforcement could go in without a migration.
* **The whole-corpus sweep found nine more, in five fixtures**, none of which failed anything, because
  none of them was ever stepped. All rewritten to the vocabulary.
* **The danger is demonstrable, not theoretical.** With the refusal disabled, the check's own
  `leaving_the_REAL_WORLD_untouched` goes red: a step *imagining* `tamper` writes `tampered` onto the
  real car.
* Cost: nothing measurable. It is one attribute read per step.

### 6. The two natives that still do not resolve

`types.is_a` and `types.check` find their world through `workbench.view_of`. `driver.plan` and
`driver.plan_step` do not, and the natives inventory in [mediated-access.md](mediated-access.md) says
they must.

⚠ A gap found on the way and left open deliberately: `types.fails` resolves the *neighbours* it walks
through `path.adjacent`, but `function.invoke` type-checks its argument through the resolver and then
walks from there with **no view**, because at that point it holds a context rather than a frame. The
schemas in the corpus are attribute-shaped so nothing catches it. It wants a world where a parameter
type's *schema* depends on a neighbour the frame changed.

### 7. Predicate dispatch, slices 3–4 — a capability, not part of the arc, and now the one to want

[predicate-dispatch.md](predicate-dispatch.md). **Slice 3** — conditions that speak of the ambient goal,
reached by walking the chain, which is what makes *go to the bank* work when the world alone cannot
decide it. **Slice 4** is the prize: `wants_that_unblock` reads guards, so a failed condition becomes a
subgoal rather than a refusal.

**These two moved up.** [advice-over-sequences.md](advice-over-sequences.md) — advice that constrains
the *order* of a plan's actions rather than any one of them — asks for exactly them and for nothing
else new: *at each step, check I am not violating anything and that I am respecting the advice* is
slice 3 plus slice 4. That thread is also the strongest argument for finishing items 3 and 4 first,
since a Python phase machine cannot consult a prescription written in the web.

⚠ Nothing in the corpus dispatches yet — `stack`'s guard is a *constraint*, not a choice between bodies,
so the union in `driver.establishes` and the specificity ordering are exercised only by their checks. The
first real multi-body operator is where ranking can quietly degrade; measure the search when it lands.

⚠⚠ **And a question that was raised and not settled:** *do coinductive rules resolve ambiguity?* The
answer reached was **no** — coinduction is a stance on whether circular support *counts*, and it is the
permissive one, so it admits more readings rather than choosing between them. Ambiguity needs consistency
**and** preference, and coinduction speaks only to the first. The split worth keeping: **the recursion in
a schema is coinductive; the support from the world must be grounded.** `types._target_ok` and
`types.fails` already do exactly that, by accident of good taste rather than by statement. What is
genuinely missing is *propagation between rival readings* — today the only way to compare two
interpretations is to run both. That is a probe, not a build.

## How to work on this

**Moving something to the surface deletes Python rather than porting it.** Twice in one arc a piece of
the Python had no counterpart to write, and both times it was reproduced first and then found to be dead
code: the failed-step unwinding (a microfunction's writes are journaled, so a call that raises rolls
back whole) and passing a context `under=` a call (the surface establishes on `SELF` and the callee
inherits). Ask what the Python was compensating for before translating it — the answer is sometimes *for
being Python*.

**A predicate that answers in prose cannot move to the surface.** `unmet_expectations` returned
sentences containing `repr(got)`. That looks like a weakness of the surface and is not: rendering is a
decision, and a rendering decision inside a predicate is a second thing the predicate is for. Split it —
facts on the node, sentences at the edge — and the rest was a transcription. `execution.step` reports in
prose in several places and will want the same split.

**A dormant twin rots against the thing it shadows.** `rules/workbench.mf` sat written-but-not-live long
enough to miss the frame index and three parameters, while its comparison check kept passing — because
the check only ever called the one-argument form. *A comparison check is only as strong as the routes it
takes through both sides.* Anything left written-and-not-live (today: `holds.mf`, `compare.mf`) is under
that risk, and the answer is routes, not vigilance.

**Measure the blast radius before building an enforcement.** Before `step` was made to refuse unmediated
operators, `workbench.step` was instrumented over the whole suite to ask how many operators are ever
*stepped* while unmediated. The answer was one, so the guard could go in with no migration and no
judgement call about acceptable breakage. Measuring by running, not by reading, is also how the corpus's
mediation was established in the first place.

**Decompose before believing something is primitive.** The single most useful test found here. It
turned six proposed natives into five substrate opcodes and two edge reads; it caught a third executor
that was not needed; it shrank every expansion in the audit below its first estimate. Its converse is
worth stating too: when something *must* be a native, say why in the docstring, or the next reader will
assume it was primitive. `types.gather_instances` is a native because the traversal it would need
(`reachable`) is in the surface but **unmediated** — not because enumeration is a primitive.

**Test the claim before building the fix for it.** Three times during the audit something was
"missing" and already worked — dynamic function names most sharply. The cheapest guard is to try it.

**The enforcing form arrives before the answering one.** Wherever the engine can only *enforce*,
something above it that needs to *decide* will have to be Python. `types.check` raised where a guard
needed `is_a` to answer; `INVOKE` raised where a replay stepper needed `ATTEMPT`. This is the most
reliable predictor of where the next island is — and it runs both ways: `ATTEMPT` answered where
nothing could *raise*, which is what `REFUSE` is. Finding one half of a pair is a reason to look for the
other.

**Ask what it is for before building it.** An identity for imagined nodes was nearly built as a minted
placeholder before anyone asked what needed one. The answer turned out not to be the reason assumed
(chaining) but that a goal constraint can be existential — and once that was clear, the thing needed no
mechanism at all. Two of the largest near-misses in this arc were designs for a requirement nobody had
stated.

**Measurement finds what checks cannot.** The `called`-versus-`caller` defect was invisible to three
successive checks and obvious to a benchmark, because two activations made moments apart have ids that
sort the way they were made. When a planted bug stays green, the usual cause is not a weak assertion but
a **world that cannot express the defect** — fix the scenario, not the assertion. `python -m ugm.bench`
exists so this stops being rebuilt in a scratch file each time.

**When a safety property is implemented by looking at the argument, ask what it is really about.**
*Planning cannot reach the world* was checked by asking whether the dispatch target was a workbench
copy. That was the same question only while planning handed rules copies; the moment a rule was bound to
the real thing, the guard went quiet and stayed quiet. The property was always about the **dynamic
extent** — *am I imagining?* — and nothing about the argument could have said so. Worth generalising: a
guard that tests a *value* for a fact about the *context* is right by coincidence until the day it is
not, and it fails silently, because a guard that stops firing looks exactly like a guard that has
nothing to complain about.

**A recorded gap statement is a hypothesis, not an inventory.** The edge-property gap was written down
as needing two reading opcodes. It needed a third, to write.

**A closed class earns its place by being declared** — named, reachable as data, with a stated
position on whether it has an escape into the web. See [concepts.md](concepts.md) on the horizon.

**The CNL cannot grow itself, on purpose.** Adding a block verb is an edit to `intake.py` forever, so
the family count is a budget — which is why *relate it in the web* is usually the cheaper answer as
well as the principled one.

⚠⚠⚠ **An assertion built out of the function under test degrades exactly as the code does.** The check
guarding chain-walked resolution asserted `mapping_for(f2, x) == mapping_for(f1, x)` — two calls to the
thing being tested — and **passed with the defect planted**. Compute the expected answer structurally, by
a different route from the code under test. A second lesson from the same plant: the bug must be planted
where the answer actually comes *from*, or the trap stays unsprung and the green means nothing.

**Plant against one check, not the suite.** `python -c "from ugm import selftest as S; print(S.check_...())"`
takes a second. A plant that blinds the planner takes the whole suite from 70 seconds to over ten
minutes, which is a slow way to learn one boolean.

**Every check must earn its green.** Several checks in this suite were once vacuous — passing whatever
the code did — and were fixed by planting a deliberate bug and confirming they went red. Any new check
should earn its place the same way. That practice is the reason to trust the rest.
