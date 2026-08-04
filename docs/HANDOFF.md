# Handoff

Read this first when picking the project up cold. It says where things are, what state they are in,
what to do next, and which mistakes have already been made so they need not be made again.

**Verify:** `python -m ugm.selftest` — currently **255 checks, 0 failing**, in about 60 seconds.
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

`workbench.step` written in the surface is now **3.0×** the Python one, against 22–42× before — because
`carry_frame` was essentially all of that, and sparse frames deleted it. The self-test runs in 60 s
against 70 s before.

The planner pays for it: Sussman's anomaly is **1020 ms against 640 ms**, at the identical 50 imagined
states. That is not the search getting worse, it is copying moving into the interpreter on a world small
enough for dense to have been the right answer. It is the honest number and it is where a
faster interpreter would show up.

## What landed since the audit

Detail and reasoning in [audit.md](audit.md) and [mediated-access.md](mediated-access.md); this is the
index, kept short on purpose so the plan below stays readable.

* **The three predicates were decomposed** and got three *different* answers. `goal.satisfied` is a loop
  whose only blocker was a Python closure standing in for a frame node; it needs one substrate opcode,
  **`VKIND`** (a value's category), which closes both remaining gaps at once — naming `UNKNOWN`, and
  `compare`'s totality. `workbench.deviates` wants **`types.violations` as a native** beside `is_a`.
  `workbench.unmet_expectations` needs no capability: it is blocked upstream because
  `predicted_changes` returns a Python dict, and should return a transient node. **None of this is
  built.**
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
  the activation `SELF` names, so a boundary needs no Python. Still not the live one; the Python `step`
  is, and the two are checked against each other.
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

* ⚠⚠⚠ **Binding a rule to an identity makes an unmediated rule loudly wrong instead of accidentally
  right.** While `step` handed over the frame's copies, a bare `LINK F(d) …` landed in the frame by
  luck. Bound to the thing itself, the same instruction **writes to the real world while planning**.
  Roughly a dozen test fixtures were unmediated and every one of them turned a check red until it was
  rewritten to the vocabulary. `access.offenders` is the pass that says so, and it is currently run over
  one graph rather than over every corpus — the obvious next guard is `step` refusing an unmediated
  operator outright.
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
| Sussman's anomaly | **1020 ms**, 50 imagined states — 640 ms before sparse frames |
| a step, 5 / 60 / 300 blocks | **53 / 56 / 59 ms** — against 47 / 68 / 198 dense |
| surface `step` vs Python | **3.0×** — against 22–42× before |
| a mediated read vs a bare `GET` | **3.8×** |

The second row is the one the design was for: **cost follows change, not the size of the world.** The
first row is the price paid for it on a five-node world, where copying four nodes in Python was cheaper
than minting two versions through an interpreted `copy_with_edges`. Both are true, and quoting either
alone misrepresents the change.

**The workbench cannot stay in Python**: planning that Python owns is planning the system cannot inspect
or change, which is the island the whole design exists to avoid. Sharing versions between frames is only
correct if reads are mediated — and mediation can live neither in the kernel (it would have to know what
a frame is) nor in Python. That is why the mediation layer exists, and it is now load-bearing rather than
anticipatory: a native that ignores the context can finally be *caught*.

## What to do next

Sparse frames and the identity model are done and are described under *What landed* above; this is what
remains. [mediated-access.md](mediated-access.md) is the design, it opens with a table of what is built
and what is not, and it records the wrong turns in detail — all easy to make again.

### 1. Enforce mediation at `step`  ← start here

**This is now a correctness hole, not a tidiness one, and it is the thing most likely to bite whoever
picks this up.** A rule bound to identities that touches the graph bare **writes to the real world while
planning**. `access.offenders` already answers the question and `check_A_PLANNING_OPERATOR_MAY_NOT_TOUCH_THE_GRAPH_BARE`
already asks it — over one graph. Two things to decide:

* run the compliance pass over *every* corpus the self-test builds, not one; and
* have `step` refuse an unmediated operator outright, which needs `fn.load` per step and therefore wants
  the answer cached on the function node.

The evidence that this matters: roughly a dozen fixtures in `selftest.py` were unmediated, every one of
them went red, and each was a rule quietly writing to reality from inside an imagination.

### 2. The remaining two natives, and `predicted_changes`

`types.is_a` and `types.check` resolve now, through `workbench.view_of`. `driver.plan` and
`driver.plan_step` do not, and the natives inventory in [mediated-access.md](mediated-access.md) says
they must. Then `predicted_changes` should return a transient node rather than a Python dict, which is
what blocks `workbench.unmet_expectations`.

⚠ A gap found on the way and left open deliberately: `types.fails` resolves the *neighbours* it walks
through `path.adjacent`, but `function.invoke` type-checks its argument through the resolver and then
walks from there with **no view**, because at that point it holds a context rather than a frame. The
schemas in the corpus are attribute-shaped so nothing catches it. It wants a world where a parameter
type's *schema* depends on a neighbour the frame changed.

### 3. Predicate dispatch, slices 3–4

[predicate-dispatch.md](predicate-dispatch.md). **Slice 3** — conditions that speak of the ambient goal,
reached by walking the chain, which is what makes *go to the bank* work when the world alone cannot
decide it. **Slice 4** is the prize: `wants_that_unblock` reads guards, so a failed condition becomes a
subgoal rather than a refusal.

⚠ Nothing in the corpus dispatches yet — `stack`'s guard is a *constraint*, not a choice between bodies,
so the union in `driver.establishes` and the specificity ordering are exercised only by their checks. The
first real multi-body operator is where ranking can quietly degrade; measure the search when it lands.

### 4. `execution.step`, then the phase machine

`driver._phase_*` is reads, guards, one call, attribute writes and unlinks; its `_PHASES[phase]` dispatch
is what a dynamic `INVOKE` does.

### 5. Swap `step.mf` live

`rules/step.mf` is sparse, establishes its own context, and agrees with the Python on four routes plus
chaining and a refusal — at **3.0×**, against 22–42× when it had to copy. The remaining question is
whether the planner can afford it, and the answer is a measurement rather than an argument.

### 6. The three predicates — independent, do whenever

`VKIND` and `compare.mf` land together with `goal.holds` (writing `compare.mf` earlier would duplicate
`types.compare`, which `goal.holds`, `criterion._holds` and every schema check share); `violations` as a
native.

**Expressible is not the same as rewritten**, and the difference should not be allowed to blur.

## How to work on this

**Decompose before believing something is primitive.** The single most useful test found here. It
turned six proposed natives into five substrate opcodes and two edge reads; it caught a third executor
that was not needed; it shrank every expansion in the audit below its first estimate.

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
