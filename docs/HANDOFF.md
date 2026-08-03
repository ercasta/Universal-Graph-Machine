# Handoff

Read this first when picking the project up cold. It says where things are, what state they are in,
what to do next, and which mistakes have already been made so they need not be made again.

**Verify:** `python -m ugm.selftest` — currently **252 checks, 0 failing**, in about 70 seconds.

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
| why a rule never calls `GET` | [mediated-access.md](mediated-access.md) — built; the note is the argument behind it |
| the instruction set | [reference/isa.md](reference/isa.md) |

## Current state

The system takes goals as text, plans by imagining on a workbench, acts through one guarded door,
notices when reality disagrees, and answers questions with the derivation that produced the answer.

A **capability audit** ([audit.md](audit.md)) found everything that could only be said in Python and
decided, case by case, whether that was a decision or an accident. All eight findings are closed, and it
produced `policy`, `procedure`, `tie_break`, five reflection opcodes, `ATTEMPT` and
`INVOKE … with <node>`.

Since then the work has been moving the **workbench** out of Python, and that has turned into the
current arc. `workbench.step` is now written in the surface but is not live: it costs ~25×, essentially
all of it the per-node frame copy. Two constraints then decide the architecture, and neither is about
performance:

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

What remains is what it was all for — **sparse frames**, where a frame maps only what changed in it and
resolution walks the chain. The reading half is built and the writing half is written but not switched
on; step 3 below says exactly what blocks it, and it is a correctness question rather than a cost one.

Mediation costs **4.5×** on Sussman's anomaly (241 ms bare, 1090 ms mediated, same plan) and about **14%**
on the whole self-test — which is the number that matters, since every stepped rule in the corpus now
goes through the eight names.

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
  chaining and a refusal. Two natives added: `find_function` and `minted`. **Not yet live** — see the
  measurements below.
* **Mediated access is built** — `access.py`, `rules/access.mf`, `rules/resolve.mf`, two natives
  (`resolver`, `context`), and the planning corpus rewritten to the eight names. Detail in
  [mediated-access.md](mediated-access.md), which now opens with what landed and what did not.
* **The corpus is mediated.** All 52 rules that are stepped on a workbench reach the graph through the
  eight names — measured by instrumenting `workbench.step` over the whole suite, not by reading, and the
  closed set covered every opcode they used. `asm.load_text` **links**: a body calling the vocabulary
  gets the vocabulary loaded, so no caller keeps that precondition by hand.
* **Resolution is indexed.** A frame carries a stored reference from identity to the version it holds
  (`workbench.index`), read by Python and by the surface alike. See the traps below for why.

Traps worth not re-learning:

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

`workbench.step` in the surface, against the Python it replaces:

| world | Python | surface | |
|---|---|---|---|
| 5 blocks | 17.9 ms | 753 ms | 42× |
| 20 blocks | 71.6 ms | 2248 ms | 31× |
| 60 blocks | 301 ms | 6634 ms | 22× |

~2000 interpreted instructions per step at twenty blocks, and **essentially all of it is `carry_frame`**
— the per-node frame copy. `step` is the innermost operation of `pursue`, called once per imagined
state. **Sparse frames delete that copy**, which is why the swap waits on them rather than on a faster
interpreter.

**The workbench cannot stay in Python**: planning that Python owns is planning the system cannot inspect
or change, which is the island the whole design exists to avoid. So the numbers say how much has to
change *before* the swap, not whether to make it. Avoiding the copy means a frame sharing versions with
its predecessor, which is only correct if reads are mediated — and mediation can live neither in the
kernel (it would have to know what a frame is) nor in Python. That leaves in-graph procedures.

## What to do next

Steps 1 and 2 of the previous plan are done and are described under *What landed* above; this is what
remains. [mediated-access.md](mediated-access.md) is the design, it opens with a table of what is built
and what is not, and it records two wrong turns in detail — both easy to make again.

### 1. Finish sparse frames: the identity model  ← start here

The reading half is built and the writing half is written and **dormant**. `rules/version.mf` mints a
version on write through a **`writer`** the context names beside its `resolver`; `workbench.step` has
been run sparse and reverted.

⚠⚠ **What blocks it is correctness, not cost.** With a sparse frame an edge written in frame N points at
the version its target had in frame N−1, while a goal constraint is checked against frame N's version of
that target — so `b on c` reads as false one step after it became true, and a one-step goal comes back
*not found*. That is how it was caught.

The fix is the model the design note actually states: **an edge names an identity, never a version, and
resolution happens on the target.** Five changes, and they have to land together because each one alone
breaks the others:

1. **`step` binds identities**, not images — `g.target(m, "original")` in place of `image_of(m)`.
2. **Frame 0's copies point at real nodes.** `_copy_set` currently rewrites edges into a parallel world;
   under this model there is no parallel world to rewrite into.
3. **A link constraint compares identities** — `original_of(target) == object`. This is the failure
   above, and it is *resolution on the target* in the one place that was still comparing raw ids.
4. **`function.invoke`'s type check resolves under the context.** It calls `types.violations` from Python
   with no activation, so once bindings are canonical a rule's *precondition* reads the real world while
   its *body* reads the frame. ⚠ Not in the design note — found on the way past.
5. **Then flip `step`**: drop the per-step copy, and delete the `dense` marker on frames (it exists only
   to stop `visible` walking a chain of full copies, which is O(depth × world) for nothing).

Then the four natives that must resolve (`is_a`, `check`, `plan`, `plan_step`) become testable, because
only now can ignoring the context be *wrong*; and the goal machinery and phase machine become boundaries
with something to read.

### 2. Swap `step.mf` live, and re-measure

Really the second half of the same job. The surface `step` measured 22–42× and **essentially all of it
was `carry_frame`** — the per-node frame copy. Sparse frames delete that copy, so `carry_frame` becomes
a handful of instructions and the comparison is finally about the interpreter rather than about copying.

### 3. `execution.step`, then the phase machine

`driver._phase_*` is reads, guards, one call, attribute writes and unlinks; its `_PHASES[phase]` dispatch
is what a dynamic `INVOKE` does.

### 4. The three predicates — independent, do whenever

`VKIND` and `compare.mf` land together with `goal.holds` (writing `compare.mf` earlier would duplicate
`types.compare`, which `goal.holds`, `criterion._holds` and every schema check share); `violations` as a
native; `predicted_changes` returning a node instead of a Python dict.

### 5. A benchmark in the repo

Twice in one arc the defect was found by a measurement and not by a check — the `called`-versus-`caller`
trap, and `Graph.labels` — and each time the harness was rebuilt in a scratch file and thrown away.
*Look at the clock, not only the report* should be something the project does, not something it
remembers.

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
a **world that cannot express the defect** — fix the scenario, not the assertion.

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
