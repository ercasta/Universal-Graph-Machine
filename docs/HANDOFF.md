# Handoff

Read this first when picking the project up cold. It says where things are, what state they are in,
what to do next, and which mistakes have already been made so they need not be made again.

**Verify:** `python -m ugm.selftest` — currently **265 checks, 0 failing**, in 90–120 seconds depending
on the machine. ⚠ The wall-clock numbers below drift with the host: measured twice in one session, the
same commit gave Sussman 1500 ms and 1920 ms. **Compare a change against the tree you changed, in the
same minutes** — never against a number written down earlier. ⚠ Take the baseline in a **worktree at
HEAD** (`git worktree add <tmp> HEAD --detach`), *not* `git stash -u`, whenever the working tree holds
work you have not committed: a stash/pop cycle around a long measurement is how hours get lost, and this
project has already recorded one such loss.
**Measure:** `python -m ugm.bench` — the numbers below, re-runnable. ⚠⚠ **A ratio hides a curve.**
**Audit:** `python -m ugm.reach` — *what of the engine's own machinery could a rule start?* **98 named
things cannot**, and the list is derived rather than written down. See P0 below.
**Weigh:** `python -m ugm.horizon` — *what would it cost to change a closed set?* **17 dispatchers down
to 0**: "closed" is a rate, not a kind. See [reflection.md](reflection.md).
`stepping` and `acting` report one number against a reference and cannot say whether the *shape* is
right; measure any new surface function at **three world sizes** before believing its ratio.

The engine is `ugm/`. An earlier iteration lived in `microfunctions/` and the package was renamed;
anything still pointing at `microfunctions/` or `docs/microfunctions/` is stale.

## Where to read

| you want | read |
|---|---|
| what the machine is | [overview.md](overview.md), then [concepts.md](concepts.md) |
| what a domain can write | [authoring.md](authoring.md) — the one text surface |
| how it runs | [execution-model.md](execution-model.md) |
| what it cannot do | [limits.md](limits.md) — kept deliberately honest |
| how it differs from its neighbours, and what is merely prior art | [comparison.md](comparison.md) — the claim is the **residue**, not the execution |
| whether the machine can be a description of itself, and what "innate" honestly means | [reflection.md](reflection.md) — one substrate, a floor, and a **measured** gradient |
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
| `execution.step` | ✅ **live** — `rules/execute.mf`, behind a wrapper; `_python_step` is the reference |
| `workbench.predicted_changes` | ✅ **live** — `rules/predict.mf`; it was never on the blocker list, and it was one |
| `driver._phase_*` | **not written** — the last of it, and unblocked; see item 3 |
| `workbench.deviates` | ✅ **live** — `rules/deviate.mf` + the `violations` native |
| `workbench.unmet_expectations` | ✅ **live** — `rules/unmet.mf`; `predicted_changes` returns a node and the prose moved to `explain_unmet` |
| `goal.holds` | ✅ **live** — `rules/holds.mf`, behind a wrapper; `_python_holds` is the reference |
| `rules/compare.mf` | ✅ **live on the goal path** — `holds.mf` calls it; `types.compare` still serves schema checks |
| the mediation layer (`access` / `resolve` / `version`) | ✅ live |

**Both swaps are done, and the doubling is gone.** What is left of each Python original is a *reference*
implementation — `_python_step`, `_python_open_workbench`, `_python_holds` — which exists to be compared
against in a check rather than to run. That is the answer to two implementations of one thing: a check
that compares them, not a deletion that leaves the surface unmeasured.

### The planner establishes a context, and `holds` went live on it

The last seam, and it turned out to be one line of the design rather than a mechanism. A Python caller
held a **view** — a function from a node to the node standing for it here — while a rule gets its world
from the ambient **context**. Those are the same information in two shapes, and the second shape is the
only one both sides can read, so `goal.holds` could be written and checked but never run.

`goal.py`'s predicates now take `ctx=` where they took `view=`, and `driver.context_in(g, frame)` is
where the planner says which world it means. It **reuses the context `workbench.step` already opened for
that frame** rather than minting a second one, found through the reverse index — two nodes that must
agree about a world are two nodes that can come not to. Whatever still wants a view derives one from the
context in `goal._world`, and that function is the honest statement of what is left: it survives for
`_python_holds` and for `witnesses` / `undetermined` / `witness`, which have not moved.

**The closure is gone, not replaced**, exactly as predicted: a rule in the closed vocabulary resolves
through the context, so `slot_of` inside a frame reads that frame's version without `holds.mf`
containing one word about frames.

⚠ **It cost ~2.3× on the flagship benchmark and was kept anyway.** Sussman goes 1600 ms → ~3740 ms at
*identical* 50 imagined states — same search, same plan, so the whole difference is interpretation.
`holds` is 444 calls and **54% of the run**, ~37 ms each, because one predicate evaluation makes a dozen
nested interpreted vocabulary calls. Two suspects were measured and cleared: the per-call `_ensure_holds`
lookup is noise, and the calls are not redundant (`_offer` genuinely needs `open_now`). This is the
`step` precedent rather than the `compare.mf` one — **the cost is a decision, not a veto** — and it is a
decision that stays reversible, because the wrapper is the thing that makes it flippable either way.

⚠ **`compare.mf` is no longer dormant**, and that is a side effect worth knowing. `holds.mf`'s `attr`
branch calls it, so every goal-constraint comparison now goes through the surface comparator, while
`types.compare` still sits under the schema checks. The note below saying it is deliberately not live is
true only of *that* path now.

## What landed since the audit

Detail and reasoning in [audit.md](audit.md) and [mediated-access.md](mediated-access.md); this is the
index, kept short on purpose so the plan below stays readable.

**The latest session, in one paragraph.** **The skeleton went up, and a rule can grow it** —
`ugm/construction.py` and `rules/teach.mf`: an utterance becomes a runnable goal by proposal and
selection, the world decides an attachment ambiguity no grammar can, and **a rule authors a construction
after which the system understands a sentence it has never seen**. Read *THE SKELETON IS UP* above. Before that,
in the same session, both pre-P0 probes ran and went opposite ways — *is `_covers` static?* **killed** the
precompute it was meant to de-risk (0.6 ms across the whole suite), and the **guard-address probe** turned
P1 from an optimisation into a requirement (no plan at all at two off-topic constraints, bindings 11 →
1153). Three checks added, all green under planted bugs; one vacuity found and fixed by planting.

**The session before that, in one paragraph.** **P0**, and it came out half the size it went in. The
**reachability pass** is built (`ugm/reach.py`, `python -m ugm.reach`): a rule enters Python through
exactly two doors, so *what can a rule start?* is a closure rather than an opinion, and the answer is
**87 named things it cannot**. It reproduces the hand audit, adds the replay's bookkeeping and the outer
loop to it, and **corrects §0 twice** — `loop.schedule` and `driver.open_planning` are both reachable,
which nobody had checked. The other half of P0, the `_covers` precompute, was **not built**: the probe
meant to de-risk it measured it at **0.6 ms across the whole suite** and cancelled it. One new check,
green with the inventory named and red under four planted bugs. Detail in §P0.

**Two sessions before that, in one paragraph.** `execution.step` — the loop that *acts* — is now
`rules/execute.mf` behind a wrapper, and with it `predicted_changes` (`rules/predict.mf`), which was
never on the list of what blocked it and was one; getting there needed no new capability and four
representation changes, of which only one looked like prose (item 3). ⚠ It was first written **O(world)**
and the *ratio* hid it for the whole session. Then the plan changed shape: a second arc —
**de-parserization**, dropping the parser for proposal + selection — turned out to be the *same* arc,
because both meet at **reachability**, and the two were merged into one dependency-ordered plan (P0–P5,
at the top of *What to do next*). That unification also settled the one open design question, the hooks.
Alongside it, three documents were written or reframed: [comparison.md](comparison.md) (what is actually
different here, and how much is prior art), the horizon's **second axis** and the primitive-admissibility
rule in [concepts.md](concepts.md), and the training formulation in
[harmonization.md](harmonization.md). **Read the P0–P5 table before anything else in that section.**

**The sessions before those, in one paragraph**, because the entries below are in the order things
were built rather than in the order they matter: `step` and `open_workbench` were **swapped live** behind thin
wrappers, so nothing in the workbench exists twice any more; **mediation is enforced** — `step` refuses
to imagine an unmediated operator, and the compliance pass runs over every corpus; all three decomposed
predicates were written; and **the planner now establishes a context instead of passing a view**, which
was the last seam and made `goal.holds` live — so all three are live, at a measured and deliberate 2.35×
on Sussman. Lessons that generalise past their occasions are in *How to work on this* at the bottom:
**moving to the surface deletes Python rather than porting it**, **a predicate that answers in prose
cannot move**, **a dormant twin rots**, **measure the blast radius before building the enforcement**,
and **carrying one fact in two shapes is what blocks a swap**.

* **The three predicates were decomposed**, got three *different* answers, and **all three are now
  written** — which is the last session's work and the reason the plan below starts at item 3.
  `goal.holds` needed `VKIND` and `rules/compare.mf`, and its Python view-closure turned out not to need
  replacing at all; `workbench.deviates` needed the **answering** form of `is_a` (the `violations`
  native, which hands the answer back as a node); `workbench.unmet_expectations` needed no capability and
  was blocked twice by *representation* — a Python dict going in and **prose** coming out. Two are live,
  All three are now live, `holds` last, once the planner established a context. Detail in item 4.
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
| Sussman's anomaly | **~3700–3760 ms**, 50 imagined states — 1600 ms with the Python `holds`, 1020 ms with the Python step too, 640 ms before sparse frames |
| a step, 5 / 60 / 300 blocks | **~125 / ~105 / ~135 ms** — against 53 / 56 / 59 for the Python step, and 47 / 68 / 198 dense |
| live `step` vs `_python_step` | **1.4–1.9×** — against 3.0× measured before the swap; the spread is noise, not a trend |
| live `execution.step` vs `_python_step` | **~2.5×** — paid per ACTION, where the planner pays per imagined state, and **flat in world size** |
| a mediated read vs a bare `GET` | **3.5–4.7×** |

The first row **more than doubled when `goal.holds` went live**, at an unchanged 50 imagined states. That
is the price of a predicate on the search's hottest path being interpreted, and it was taken deliberately
— see *The planner establishes a context* above for the measurement that decided it.

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

## ⭐⭐⭐ THE SKELETON IS UP — read this before the phase plan

**Words in, world changed, and it can say why it read them that way.** `ugm/construction.py` and
`check_AN_UTTERANCE_BECOMES_A_RUNNABLE_GOAL_BY_PROPOSAL_AND_SELECTION`. This was built **ahead of** the
P0–P5 order below, deliberately: the phases were being built as layers with no consumer, and a thin
complete path gives every one of them something to be measured against. The plan is still right about
*what* is missing; it was wrong to finish the layers first.

**What runs today.** An utterance is recorded as **tokens and nothing else** — no parse, no verb, no
`about`. Constructions **propose** readings; each is a candidate exactly as a proposed action is.
Knowledge **selects**. The winner's consequent authors a goal through the closed vocabulary, and the
engine plans it and acts.

⭐⭐⭐ **The load-bearing result is that the world decides the structure.** *"Put the block on the
table"* — is `on the table` where the block should **go**, or **which block** is meant? One utterance,
two constructions, two worlds, and the reading flips: with the block on the floor the phrase is a
destination and the engine moves it; with the block already on the table the phrase can only be
identifying, and a different goal is built. Nothing about the utterance changed. **That is the thing a
parser cannot do**, because the information settling the attachment lives in the reasoner and the parser
has already committed — the second wall in [comparison.md](comparison.md) §Language, which is why the
third one matters.

⭐⭐ **And it grows by data.** A third construction is authored with **no Python written and no module
edited**, and a sentence the system has never seen plans and runs. Compare the standing discipline:
*a new way of saying something is an interpretation rule in the web, never a new verb in `intake.py`.*
That sentence is now executable rather than aspirational.

**A construction is not a new kind of thing**, and that is most of why this was small. It has the three
parts a criterion has and **reuses the same nodes**: the address (`wants_sort` / `wants_label`), the
tests (`criterion.test`), and a consequent (`consequent.call`). So specificity ordering, the condition
reader and the *why-this-not-that* explanation all arrived already written — `function.guard`'s argument
(*"the condition language cannot tell a role from a parameter"*) carried one family further: it cannot
tell a token from a constraint either.

* **Word order is form, not grammar.** A construction reaches its other roles by walking the token chain
  (`some theme in head by ^next`), which offers every preceding token nearest-first, and ordinary `when`
  lines say which one is meant. Measured on the six-token sentence: the draws offer **six** candidate
  bindings and the tests keep one. Proposal and selection, at the level of a phrase.
* **Specificity is what decides between two valid readings**, not the random stage — a construction
  demanding everything another demands *and more* wins. Goldberg's ordering falling out of
  `precedence._covers`, which predates the language work entirely.
* ⚠ **Grounding is handed in and is not claimed.** That "block" denotes this node is reference
  resolution; it is the genuinely hard part and it is orthogonal to all of this.
* ⚠ **Silence is an outcome.** An utterance nothing addresses is *recorded*, not refused — the elsewhere
  case, per *Silent failure is acceptable; unrecorded failure is not* below.

⚠ **`python -m ugm.reach` went 87 → 98, and that is correct rather than a regression.** The front door is
Python, so adding it to the entry points honestly grows the inventory. **That is now the sharpest target
in the repo**: the skeleton's own segments are the next things to make reachable, and unlike the older
items they have a consumer that will notice.

**What this does not do**: it does not touch coverage (the tail of English was never the interesting
failure), it does not ground a reference, and it does not remove `intake.py` — the CNL still reads
criteria, methods and types, and the two front doors coexist until constructions cover what it does.

### ✅ And a rule can teach it — the growth claim is closed

`rules/teach.mf` + `check_A_RULE_CAN_TEACH_THE_SYSTEM_A_NEW_WAY_OF_SAYING_SOMETHING`. **A rule authors a
construction, and the system then understands a sentence it has never seen.** No Python helper called,
no module edited. It needed **no new capability**: a construction is nodes and edges, so `make`,
`set_slot` and `relate` are the whole of it — the same finding as `A_RULE_CAN_BUILD_A_RUNNABLE_GOAL`,
one level up.

⭐⭐⭐ **This is the bootstrap the learning story needs, and that is why it was worth doing before the
rest.** [harmonization.md](harmonization.md) proposes learning the rule ordering and
[comparison.md](comparison.md) proposes learning constructions — and **you cannot learn what you cannot
author**. Until now, authoring one meant calling Python, so every proposal about learning language was
secretly a proposal about *writing a Python function*. It is now a proposal about writing a rule, which
is a thing this system already does.

⭐⭐ **The claim that is not free is `EVERY_TEACHING_RULE_IS_MEDIATED`.** *A rule built it* would have
been true of a rule holding bare opcodes and would prove nothing about the layering. Every body in
`teach.mf` reaches the graph only through the eight closed names — checked with `access.bare_touches`,
the same pass that governs the planning corpus — so **teaching happens at the same layer everything else
does**.

⚠ **A vacuity found by planting, and it is a class worth naming: blinding the *measuring instrument*
left the check green.** With `bare_touches` stubbed to answer empty, *"none of the teaching rules are
bare"* passed — a sentence a broken pass produces just as readily as a mediated corpus does. The fix is a
**positive control** in the same graph and through the same call: a body that really is bare must be
reported. Generalising: when a check asserts *no offenders*, it must also assert that the pass can still
see one.

⚠ **One real difference between the two authoring routes, stated rather than normalised away**:
`consequent.call` **sorts** its parameters and a rule adding them one at a time cannot. Parameters are
named and become a dict at the call, so order is not meaning today — and the comparison check compares
them as a mapping, with the asymmetry asserted separately so it cannot quietly become meaning.

⚠ Still not done, and it is the interesting half: **nothing yet says *"when someone explains a new
phrasing, learn it"***. A rule can author a construction; no *utterance* causes one to be authored. That
is a construction whose consequent calls these functions, and it is the point at which the system starts
teaching itself.

### Where the skeleton is thin — the next work, in the order it hurts

1. ✅ **Done — a rule can now teach one.** `rules/teach.mf`, and
   `check_A_RULE_CAN_TEACH_THE_SYSTEM_A_NEW_WAY_OF_SAYING_SOMETHING`. See below.
2. ⭐⭐ **Nothing forks.** [comparison.md](comparison.md) argues a reading should be a **frame** on the
   workbench, so rival readings are branches carrying what each took on faith. Today `readings` returns a
   ranked list and the loser is kept only as a `rival` edge. The list is enough to choose; it is not
   enough to *evaluate a reading against evidence and abandon it*, which is what the abduction shape
   actually wants — and the workbench is the one layer already reachable, so this needs no new machinery.
3. **`_bindings_for` exists twice.** `criterion`'s addresses unmet goal constraints, `construction`'s
   addresses tokens, and the two differ by *one line* — what is being addressed. Making the source an
   argument collapses them. ⚠ Deliberately not done yet: *an island is created by the second caller*, and
   today there are exactly two. A third family addressing something is the moment.
4. **The address is a lemma.** `addresses token "on"` is exact string match. Croft's point is that
   categories are *derived* from the constructions a word occurs in, so the address should be able to
   name any discriminating attribute — which is what P1 is for, and what `_covers` already does
   structurally.
5. **Nothing is learned.** Harmonization's training formulation and *learning a construction is
   `compile_episode` for utterances* both now have something concrete to be about.

## ONE PLAN — de-Pythonization and de-parserization are the same arc

There are two open arcs and they were being planned separately. They should not be.

* **De-Pythonization** — the system's own machinery written in the surface, so it can be inspected and
  changed. Remaining: `driver._phase_*`.
* **De-parserization** — intake stops being a *parser*. Interpretation becomes **proposal + selection**
  over the web, because a parser decomposes an utterance before any knowledge is consulted, which is
  Fodor's error at the front door. See [comparison.md](comparison.md) §Language.

⭐⭐⭐ **They meet at REACHABILITY**, and that is the criterion that orders both. De-Pythonization has
been asking *"can the system inspect and change its planning?"*; de-parserization needs *"can a **rule**
reach it?"* — and every remaining item on the first arc is a prerequisite of the second. The plan below
is therefore in **dependency order**, not arc order, and the numbered sections after it are the detail.

⭐⭐⭐ **The unification settles the one open design question.** Item 3's blocker C1 — *are the hooks
(`rank`, `allow`, `trace`) named functions in the graph, or does Python keep a wrapper?* — was recorded as
a choice. **De-parserization decides it**: harmonization's whole proposal is to *learn the rule ordering*,
and **you cannot learn a Python callable**. Hooks must become data. That is no longer a judgement call.

| phase | what | why it is here, and what it unblocks |
|---|---|---|
| **P0** | ✅ **done, and half of it was deleted by its own probe.** The **reachability pass** is built (`ugm/reach.py`, `python -m ugm.reach`) and the check is green with the gap named. The `_covers` precompute is **not built**: measured at **0.00% of the suite** | see §P0 below. The probe that was meant to de-risk the precompute cancelled it instead |
| **P1** | the **addressing half of a guard** — `wants <sort> <label>` on function bodies, which `criterion.py` has and function guards lack | ⭐ **probed, and it is a requirement rather than an optimisation**: without an address the search finds a worse plan at one off-topic constraint and **no plan at all** at two, while bindings go 11 → 581. The index is the lesser half; the *"which tokens do I look at"* semantics is the point. Also predicate dispatch slice 3 |
| **P2** | **starting a pursuit** must be reachable — `open_pursuit` / `carry_out` / `loop.schedule`, `open_planning` (reading `max_steps` / `max_depth` / `guided` off the pursuit), `open_execution`. ⭐ **Not** the goal constructors: see below | de-Pythonization's cluster B **and** the language arc's precondition. Smaller than it looked |
| **P3** | **hooks become data** — `rank` / `allow` / `trace` as named functions and precedence stages; add the missing **`by experience`** comparator (`EXPERIENCE` is only an attributor today; `application.py` holds the record). ⚠⚠⚠ **Write the stratification argument first** — see below | decided by P2's needs rather than open. Unblocks `_phase_planning`, and *is* the learned-order artifact harmonization needs |
| **P4** | **`driver._phase_*` in the surface** — the seams (`driver.step`'s result dict, `T.attend`'s prose), then the machine | the last of arc one. After it a rule can drive plan-act-check end to end |
| **P5** | **interpretation as proposal + selection** — hand-seeded, forms fixed, improved by harmonization as **theory revision** | ⭐ **the skeleton is up** (see the section above `ONE PLAN`), built ahead of P1–P3 on purpose. What it did *not* need turned out to be most of them; what it now needs is listed under *Where the skeleton is thin* |

### ⚠⚠⚠ P3 has a regress in it, and the answer is already in the codebase — see [reflection.md](reflection.md)

**When `rank` becomes a rule, selecting which `rank` applies requires ranking.** That is the
self-application regress every reflective architecture meets, and it is not hypothetical here — P3 is
exactly the move that creates it. The field's answers are a *fixed floor*: Soar's architecture decides
when to go meta and productions do the rest; PRS puts meta-level KAs above a default that always
decides.

⭐ **This codebase already has that floor and has not noticed.** `precedence.seal_rule` refuses a
tie-break rule whose last stage is not total — *"the last stage must decide every pair … or two rules
sit in an order nobody chose"*. Read at P3 that stops being a nicety about ordering and becomes **the
stratification condition**: a base level that always decides, so the tower terminates. Write the
argument down before building P3, not after, and check that the hook stages inherit the same refusal —
a `rank` authored as a function stage may **not** sit last, which `add_stage` already says and which
will matter for a reason it was not written for.

✅ **Both are now written up in [reflection.md](reflection.md)**, together with the measured gradient that turns *innate vs learnable* from a question into a number. ⚠ The framing, in short, because it changes why the arc matters rather than what is in it:
**the planning machine should be an algorithmic description of itself that the engine executes.** That
is *computational reflection* — Maes' intercession rather than introspection, Smith's 3-Lisp, Bowen &
Kowalski's amalgamation, PRS's meta-KAs — and the **residue** thesis is the strongest argument for it,
stronger than the inspectability one used above: if the planner is rules, *"why did I plan it this
way?"* is answered by the machinery that already answers *"why is the block on the table?"*, so there is
one mechanism rather than two. Note also that the rules doing this are largely **non-verbal** — they
manipulate references rather than express actions — which is what the **closed class** already is, and
why it looks nothing like a verb family.

**What this plan deliberately does not contain**: a chart parser, more `intake.py` verb families (the
budget stands — a new way of saying something is an interpretation rule in the web), and predicate
dispatch **slice 4**, which advice-over-sequences still wants but which is not on the language critical
path.

✅ Both pre-P0 probes have now been run, and they went opposite ways: *is `_covers` static?* **killed**
the precompute, and the **guard-address probe** turned P1 from an optimisation into a requirement. Both
are written up below.

### ✅ The guard-address probe — the address is load-bearing, and it is indexed by the GOAL

*Blank the addressing half on utterances whose target structure is known; does search recover it, and
how does the space grow?* Interpretation-as-selection does not exist yet (P5), so the probe ran on the
machinery P1 is modelled on: a **criterion**'s `wants <sort> <label>` line, which says which unmet
constraint the advice is about and from which `subject` and `object` are bound. Three levels, the same
three criteria (`CRITERIA_TEXT`) and the same goals throughout:

| | addressing | |
|---|---|---|
| **L0** | `wants link on` | as authored |
| **L1** | `wants link` | the **label** blanked — any link constraint |
| **L2** | `wants` | the whole line blanked — every unmet constraint, whatever its sort |

⚠ **The first run of this probe was vacuous, and the reason generalises.** Sussman's goal is *two `on`
link constraints and nothing else*, so all three levels address the same two things and blanking is free
**by construction** — identical plan, identical 3 imagined states, identical 11 bindings, at 5 / 20 /
60 blocks. That is not a result about addressing; it is *a world that cannot express the defect*, this
project's standing diagnosis for a plant that stays green. ⭐ **It also settles one thing on its own: an
address has nothing to do with the size of the world.** Growing the world sixtyfold changed nothing.

The discriminating world adds constraints the criteria are **not** about — a second link label and a
second sort — and both have to be *achievable* or the probe measures an unsatisfiable goal instead of an
address (`paint` already sets `colour`; `place_beside` was added, because the block corpus has exactly
one link label and an address over one label cannot discriminate):

| off-topic pairs | | found | plan | imagined | bindings | ms |
|---|---|---|---|---|---|---|
| **1** | L0 | ✅ | 5 steps | 5 | **11** | 2150 |
| | L1 | ✅ | **6 steps** | 8 | 25 | 2960 |
| | L2 | ✅ | **6 steps** | 8 | 40 | 3290 |
| **2** | L0 | ✅ | 7 steps | 7 | **11** | 3810 |
| | L1 | ❌ **no plan** | — | 150 (budget) | **581** | 80200 |
| | L2 | ❌ **no plan** | — | 150 (budget) | **1153** | 76900 |

**The answers, in order.**

* ⭐⭐⭐ **Does search recover it? At one off-topic constraint yes, at two no.** With one, the plan is
  still found and is **worse** — six steps against five, because a criterion addressed at nothing in
  particular proposes an action it has nothing to say about and the plan carries it. With two, **both**
  blanked levels exhaust the budget and return no plan at all. So the addressing half is not an
  optimisation that buys an index; removing it changes what the system can find.
* ⭐⭐⭐ **How does the space grow? With the GOAL, not the world** — and combinatorially. Addressed, the
  binding count is **flat at 11** whether the goal has two constraints or six. Blanked, it goes
  **11 → 25 → 581** with the label alone gone, and **11 → 40 → 1153** with the sort gone too — a
  hundredfold on a goal of six constraints. The world sweep says the same thing from the other side:
  sixty blocks cost the addressed and the blanked run alike.
* ⚠ **The CNL already refuses a bare `wants`** — *"the criterion vocabulary is closed"* — so the address
  is mandatory in the **language** and optional only in the **mechanism** (`_bindings_for` matches
  nothing when `wants_sort` is absent, rather than everything). L2 had to strip the attribute off the
  node after reading. That the surface already insists is a small vote of confidence in P1.

**What this means for P1 and P5.** P1 was on the plan as *one change buys the index and the "which
tokens do I look at" semantics*; the index is the lesser half. A construction that does not say what it
addresses does not merely make selection slower — past a couple of constraints it stops finding readings
within any budget, which is the same wall `relevance` hits in
`check_EXPERT_JUDGEMENT_can_be_AUTHORED_AS_TEXT`. ⭐ And the good news is the shape: an utterance has
few constituents, so **the thing the cost scales in is small and bounded**, exactly as a goal's
constraint count is.

### ✅ P0 — the pass is built, and the probe deleted the other half

**The `_covers` precompute is not built, and should not be.** It was on the plan because dispatch is
quadratic in *applicable* bodies and the order looked static. Both halves of that were checked before
building anything, and the second one is beside the point:

* **Static: yes.** `_covers` was wrapped over the whole self-test — 107 calls, 70 distinct pairs, 37 of
  them repeats, and **zero disagreements**. So a cache would be sound.
* **Worth caching: no.** Those 107 calls cost **0.6 ms — 0.00% of a 258-second run.** There is nothing
  to precompute away.

The reason is the corpus rather than the algorithm: loaded with every rule file, it holds **61 names and
every single one has exactly one body**, so `select` never reaches the pairwise loop at all. The
quadratic is real and was re-measured — 0.03 / 0.85 / 14.5 / 57 ms at 1 / 10 / 50 / 100 applicable
bodies — it simply has no population yet. ⭐ **This is the *measure before optimizing* lesson arriving
with a named lever again**, and the plan's own text already said so two sections down: *"nothing in the
corpus dispatches yet"*. **The trigger to revisit is a second body under one name**, which is P1's
sequel and predicate dispatch slice 3; a cache installed now would be invalidation risk bought against a
0.6 ms saving.

**The reachability pass is built** — `ugm/reach.py`, and the argument for its shape is in its docstring.
A rule enters Python through exactly two doors, an **opcode** and a registered **native**, so what a rule
can reach is a transitive closure over the Python call graph from those doors; what the engine *does* is
the closure from its own entry points; and the inventory is the difference. Derived, not listed — which
is the property that keeps it from becoming the hand-written list it replaces.

    machinery: 307   reachable from a rule: 216   fronted by a surface name: 4   UNREACHABLE: 87

⭐ **A wrapper is not a gap, and missing that would have made the arc's successes read as its failures.**
`workbench.deviates` is Python no rule calls — but a rule calls `deviates`, the body it fronts. Read as a
bare Python call graph the number would *grow* every time something moved to the surface, which is
exactly backwards. `reach.fronted` reads the literal name out of the wrapper's own `fn.invoke`, and the
tell is that it is a **literal**: a wrapper names the body it stands for, while Python calling the
surface for its own reasons (`precedence._by_function`) passes a name it was given.

⚠⚠ **It found the prose wrong twice, which is the whole reason to measure rather than argue.** §0 below
listed `loop.schedule` among what a rule cannot reach. **It can** — `loop._after` is the native behind
`NATIVE … "after" …`, and it schedules. `driver.open_planning` is reachable too, through the `plan`
native. Both are now recorded as reachable, and the real gap in the second is a **different question the
pass does not claim to answer**: `plan` drops the pursuit's `max_steps` / `max_depth` / `guided`, so the
name is there and does not carry everything. ⭐ *Is there a name a rule can call* and *does that name
carry the whole capability* are two questions, and conflating them is how a list drifts.

⚠ **The check is green with the gap named, not red.** The plan said *"plus one check that goes red"*; a
standing red would cost the suite the property that makes it worth trusting, so
`check_THE_MACHINERY_A_RULE_CANNOT_START_IS_AN_INVENTORY_NOT_AN_ARGUMENT` follows
`check_A_RULE_CAN_BUILD_A_RUNNABLE_GOAL`'s precedent instead: it **asserts the inventory**, so closing an
item turns a line red and that line should be **deleted**, not fixed. It earns its green — four bugs were
planted in the pass (every function a door, none a door, fronting blinded, the `_PHASES` table unread)
and each went red on the lines meant to catch it.

⚠ The pass reads **Python bytecode**, and that is the point rather than a compromise: the boundary being
audited is Python's, so a pass written in the surface could only report what the surface already reaches,
which is the question begged. Its one approximation is stated in the module and chosen in
`precedence._covers`' direction — **a false *unreachable* costs somebody a look; a false *reachable*
silently retires work the arc still has to do** — so a call through a value computed at run time is
invisible and will be reported as a gap it may not be.

What the inventory says, grouped — and it reproduces the hand audit in §3 and adds to it:

| | |
|---|---|
| `driver._phase_*` (all five), `_attempt`, `_history`, `_record_execution`, `_plan_of`, `_looker_*` | **P4**, exactly as audited |
| `driver.carry_out` / `follow` / `open_pursuit` / `pursuit_step` | **P2** |
| `execution.open_execution` / `open_replay` / `bind` / `resume_replay` / `alternatives` / `matching_alternative` | **P2's B2**, and larger than B2 recorded — the replay's whole bookkeeping is Python |
| `loop.run` / `tick` / `advance` / `agenda` / `due` / `finished` | not previously on any list. Driving the outer loop is unreachable even though *scheduling onto* it is |
| `goal.open_goal` / `require_type` / `_constrain` / `sequence` / `close_goal` | §0's list. ⭐ Deliberately **not** P2 — a rule can already build a goal from the vocabulary |
| `workbench.as_violations` / `explain_unmet` / `phrase_unmet` / `drop_*` / `deviates` | the **renderers**, and they are correctly here: they are Python the surface does not have and does not want |
| `clock.at_of` / `arrived`, `application.applied_to`, `activation.describe`, `dispatch.observes`, `selection.candidates`, `forget.*` | readers nobody had asked about. Low value individually, and the first honest count of them |

### ⭐⭐⭐ What interpretation must PRODUCE — settled, and smaller than expected

Before designing how an utterance becomes something the engine runs, it is worth knowing what the
*output* must be, since everything downstream is specified by it. Answered by construction rather than by
design, in `check_A_RULE_CAN_BUILD_A_RUNNABLE_GOAL`:

```
goal        { label, verb }    -requires->  constraint
constraint  { sort, label }    -subject->   <a real node>
                               -object->    <a real node>
```

**Two nodes and four edges.** `sort` comes from the **closed class** (`link`, `attr`, `type`, `known`,
plus the three plan sorts), so the *shape* of the target is bounded — which is what makes
[harmonization.md](harmonization.md)'s training formulation plausible at all.

⚠⚠⚠ **But the target is not "lower it to the closed class", and reading it that way is Fodor's error one
level up.** The *shape* is closed; the **content is a web reference**, and interpretation should leave
meaning at the level the utterance expressed it. Three of the four sorts already point *into the web*
rather than into primitives:

* `sort: type` names an **authored type** — a schema defined elsewhere, with its own `base` chain. *"the
  room is tidy"* becomes a reference to `tidy_room`, and what tidy *means* stays where it was authored.
* a goal an authored **method** decomposes — `method.applicable` / `decompose` raise subgoals **at plan
  time**, not at interpretation time.
* `require_action(function=…)` names an authored **function**.

So **lowering is demand-driven and partial**: a method expands when planning needs it, a type is checked
when `holds` asks, and neither happens while interpreting. That is the horizon doc's third answer —
*relate it in the web*, never decompose — and mistaking it for a decomposition is exactly the error this
project names after Fodor. It is also the only way non-compositional constructions can work at all:
*kick the bucket* has no decomposition, only a reference.

Two consequences worth having in view before the language work:

* ⭐ **The learner's job shrinks and is better posed.** Learning *"tidy" → the type `tidy_room`* is a
  **reference**, not a decomposition — so it never has to rediscover what tidy means, because that is
  authored. This is the line between learning *language* and learning *the domain*, and only the first is
  in scope.
* ⚠ **The failure mode this invites has a name here already** — an interpretation naming a concept that
  nothing answers *parses, runs, and means nothing*, the island catalog's dangerous verdict, and the same
  rule `consequent.py` states as *a tag with nothing that runs it is worse than no form*.

  ⚠⚠ **But do not turn that into "every utterance must trigger something".** It must not: stating a fact
  triggers nothing and has *succeeded* — it added facts. Asking triggers an answer. Only a directive
  makes the engine run. A pass that warns whenever an utterance activates no machinery would fire on most
  of the language.

  The test that survives is narrower and uses an axis this project already has: **did the interpretation's
  claimed FORCE have a counterpart?** An assertion that records facts is fine. A *goal* that claims to be
  pursuable while naming a type nobody declared has failed on its own terms. Nothing else is checkable,
  and nothing else should be.

### Silent failure is acceptable; UNRECORDED failure is not

The system is heuristic and nobody should claim it is always correct — so an interpretation that quietly
gets it wrong is not a defect in the design, and refusing everything unrecognised is what makes a
controlled language brittle (`0/50` on raw prose is that failure, not a coverage failure).

⭐⭐ **The line to hold is therefore not correctness but accountability.** Do not warn, do not refuse, do
not block; **record what the reading could and could not account for**, and let whoever cares ask
afterwards. Warning at interpretation time would be the parser's error one more time — committing before
the consumer knows whether the gap matters — while recording is demand-driven like everything else here.
That is the residue thesis ([comparison.md](comparison.md)) doing exactly what it exists for: the honest
deliverable of a heuristic system is not *"always right"* but *"always able to say what it did and on
what basis"*.

⚠ **One boundary, and the machinery for it already exists.** A silent misreading is benign right up until
it becomes an **irreversible act**. `loop.IRREVERSIBLE = {ACT}` already distinguishes those steps, and
`loop.py` already states the property: *"the loop can decline to take the step; it cannot make the step
reversible."* So the rule is not *never fail silently* but **never act on an unaccounted-for reading
without the chance to decline** — a policy written against existing machinery rather than a guarantee
about interpretation.

⭐ And the *fallback* is an ordinary construction rather than an error path: an utterance matching nothing
specific falls to the **elsewhere case**, which records it as what `discourse.py` already makes it — a
world event with a speaker — losing nothing and claiming nothing.

⭐⭐ **A rule can already build it, with nothing but the eight closed vocabulary names** — no `goal.py`,
no `intake.py`, no native. The check authors a goal through `make` / `set_slot` / `relate`, and the
engine plans it, runs `stack` for real, and the world agrees. So **the representation half of
reachability is already closed**, and P2 shrinks accordingly: the goal constructors are *not* needed,
only the means of **starting a pursuit**.

⚠ And it isolates the genuinely hard part, which is not a graph-shape question at all. The rule above is
*handed* its two real nodes. Deciding that the token "a" denotes `block#1766` is **grounding** —
reference resolution — and it is orthogonal to both arcs. Everything in this plan makes the *machinery*
reachable; none of it grounds a reference. That is worth stating plainly before the language work starts,
so the remaining difficulty is not mistaken for an engineering gap.

### ⚠⚠⚠ 0. REACHABILITY — the criterion the arc has not been using, and it changes the order

**Everything moved so far is a *stepper*.** `workbench.step`, `goal.holds`, `deviates`,
`unmet_expectations`, `predicted_changes`, `execution.step` — all of them run *inside* machinery that
Python has already started. **Every entry point is still Python.** `goal.py` registers **no natives at
all**: `open_goal`, `require_link` / `require_attr` / `require_type` / `require_action` / `require_known`,
`open_pursuit`, `carry_out` are unreachable from a rule, and `driver` exposes only `plan` / `plan_step`,
which drops the pursuit's own parameters.

> **You can now watch the machine run. You still cannot start it from a rule.**

The arc's criterion has been *"can the system inspect and change its planning?"*. There is a second one —
*"can a **language rule** reach it?"* — and it selects different work. It matters because it is the
premise of everything in [comparison.md](comparison.md) about language: no amount of interpretation rules
can turn a sentence into something that drives the goal machinery if the machinery can only be entered
from Python. **The arc could complete without fixing this.**

⭐ **One large exception, and it is the encouraging one: the WORKBENCH is reachable.** `open_workbench`
and `step` are live surface functions, `fork` is literally `return step(…)`, and `deviates` /
`unmet_expectations` / `predicted_changes` / `holds` are live. So a rule can already build a
**hypothesis-evaluating machine** — several candidate readings as forked frames, each carrying what it
took on faith, evaluated against evidence, abandoned branches kept as data. That is exactly the bootstrap
language processing needs, and it needs no new machinery. Not a coincidence: the workbench is the one
layer this arc has finished. (`discard` and `matching_alternative` are still Python and wanted.)

What is and is not reachable today, which is less bad than it sounds:

* ✅ the goal **representation** — goals and constraints are ordinary web nodes, so the vocabulary
  (`make`, `relate`, `set_slot`) can build them. ⚠ But *only by reimplementing what `require_*` does*,
  which is the second-implementation-that-drifts defect this codebase keeps recording.
* ✅ reading a goal — `rules/holds.mf` is live.
* ✅ planning — `NATIVE "plan"` / `"plan_step"`.
* ❌ **starting a pursuit** (`open_pursuit` / `carry_out`), and `_ensure_*` loading, which is driven by
  the Python wrappers.

⚠⚠ **Two claims that used to be in the line above are wrong, and `python -m ugm.reach` is what found
it.** `loop.schedule` **is** reachable — `loop._after` is the native behind `NATIVE … "after" …` and it
schedules, so a rule really can put a follow-up on the agenda. `driver.open_planning` is reachable too,
through the `plan` native. What is true of the second is a *different* claim: `plan` takes only
`(goal, subject, thread)` and drops `max_steps` / `max_depth` / `guided`, so the name exists and does not
carry the whole capability (item B1). ⭐ **Those are two questions and this section had been asking them
as one.** What remains genuinely unreachable is *driving* the loop — `loop.run` / `tick` / `advance` —
which no list had recorded at all.

✅ **Half of this is already measured rather than argued.** `check_A_RULE_CAN_BUILD_A_RUNNABLE_GOAL` is
green: a rule authors a goal through the vocabulary alone, the engine plans it, and the world changes.
It also asserts the remaining gap explicitly — *starting a pursuit is still Python* — so that closing it
is a deliberate act, and the check tells you to **delete that line** rather than fix it when P2 lands.

**Do this before the rest of item 3**: only the *pursuit* half of cluster B is needed, and it is small.
✅ The other honest first move was a **pass** rather than a port — the analogue of `access.offenders`,
asking of each piece of machinery *is there a name a rule can call?* That is `ugm/reach.py`, it is built,
and it answers **87**. Read §P0 above for what it found, including the two claims in this section it
corrected.

**The arc is de-Pythonization, and one item of it is left.** Everything in this section before item 5 is
that arc; items 5 onward are correctness or capability. Nothing in the workbench exists twice any more,
and the loop *around* it now acts in the surface too — what remains is `driver._phase_*`, the state
machine that decides which of plan / act / recover / sense / check happens next.

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

### 3. ✅ `execution.step` is live · the phase machine is what is left

`rules/execute.mf`, behind a wrapper, with `_python_step` beside it as the reference and
`check_EXECUTION_STEP_IS_AN_ORDINARY_PROGRAM` comparing them over **five routes** — completing, a broken
prediction, an unbound argument, a stale precondition, and a chain — plus a vacuity guard that the five
routes reach *different* places, because two implementations that both diverge identically everywhere
would agree perfectly and mean nothing. Two bugs were planted against it and both went red.

Four things came out of doing it.

* ⭐⭐⭐ **A node a rule cannot ask for is still Python.** `predicted_changes` was **not** on the blocker
  list above — `deviates` and `unmet_expectations` were, because they are *predicates* — and it was a
  blocker. It already answered with a node, which is what made it look done; but `execution.step` in the
  surface has to *ask for* that node, and nothing in the surface could. It is `rules/predict.mf` now, and
  it needed no capability: `NKEYS`/`KEY_AT` and `NLABELS`/`LABEL_AT` already answer **sorted**, so the
  Python's `sorted(…)` had nothing to reproduce and the unions it takes are two-pointer merges. One
  native, `find_type`, on exactly `find_function`'s argument — a name to its node is a scan.
  *A recorded gap statement is a hypothesis, not an inventory*, and this is the second time that has
  cost a session.

* ⭐⭐⭐ **The prose split went further than expected, and `why` was the smallest part of it.** Four
  things were Python-shaped renderings rather than facts: the deviation's `why` (now a `cause` attribute
  plus a `_DEVIATION_PHRASE` table), the notes (now `unproduced` / `ambiguous` nodes), **what `ran`**
  (a tuple in an attribute — *a rule cannot build a tuple*, which is the same defect with no rendering in
  it at all), and the **violations** (`deviates` renders a dict; the deviation carries the node). The
  test for this is not "does it contain a sentence" but **"could a rule have produced this value?"**

* ⭐⭐⭐ **Ask before the fact; do not `ATTEMPT` after it.** The Python wrapped the real call in
  `try/except TypeViolation` and turned a stale precondition into a divergence. `ATTEMPT` is the obvious
  translation and is **wrong here**: it catches *every* refusal, so a `Vetoed` — a standing prohibition
  stopping a real action — would be quietly filed as a deviation instead of stopping the world, and it
  rolls its callee back, which is a promise this layer must never make (*fail fast on deviation, and do
  not roll back*). So the surface asks the **answering form** of the same question first, with the
  `violations` native. Same shape as `VKIND`: where Python recovers after the fact, the surface needs a
  predicate before it. ⚠ It reads the *first* body's parameter types where `fn.invoke` selects a body and
  then checks that one; nothing dispatches on a real operator yet, so they cannot disagree today.

* ⚠⚠ **A boundary check had to be re-aimed on the day the target moved** — the same lesson `holds`
  taught, arriving again and in the same week. `EVERY_BOUNDARY_ESTABLISHES_A_WORLD_TO_READ_IN` read
  `establishes` off the **operator's** activation, which was right only while Python opened the trivial
  context and passed it `under=` that one call. The surface establishes *above* the operator and the
  operator inherits, so the old question answered `None`: the check was measuring the shape of the
  Python. The fix is the one the imagining side already made — the context now hangs off the **replay**
  (`execution.world_of`), one per run rather than one per step, so the durable record of which world a
  run acted in survives the activation that established it.

Cost, on the new `acting` row of `python -m ugm.bench`: **~2.5×** against `_python_step` — the same order
as everything else interpreted here, and paid **per action** where the planner pays per imagined state (a
search imagines fifty to produce a plan of three). Sussman is unchanged, because planning does not act.

⚠⚠⚠ **It was first written O(world), and the constant factor hid it.** The ratio looked like an ordinary
interpreter tax; the *curve* did not. Measured at 6 / 30 / 120 blocks it went **618 / 1731 / 5206 ms**
while the Python it replaces stayed flat — a straight violation of the one claim the whole sparse-frame
arc exists to make, *cost follows change, not the size of the world*. Three fixes, and the classification
of each is the useful part:

* **`carry_bindings` asked the question forwards** — *for every mapping in force in `prev`, is there a
  successor in `frame`?* — which enumerates the world, because frame 0 maps every node there is. The same
  edge walked **backwards**, from the new frame's own (sparse) mappings, is O(change). *Semantic fix.*
* **`bind_minted` asked what was VISIBLE and filtered for imagined.** The workbench now records the
  identities it invented (`wb -imagined->`, written by `step.mf`) — `workbench.index`'s argument one level
  out, and a handful rather than a world. *Semantic fix.*
* **`binding_of` scanned the replay's `bound` edges**, of which `open_execution` seeds one per node in
  frame 0. It is one `DEREF` off an index `execution.bind` writes, which Python and the surface share.
  *Agnostic fix — the substrate map, whose key is an argument.*

**5206 → ~440 ms at 120 blocks, and the curve is flat.** The comparison check is what made this safe:
each fix is an *accelerated* walk held against the untouched Python on every route, so "faster" never had
to be taken on trust. ⭐ **A ratio hides a curve.** `stepping` and `acting` report one number against a
reference; `scaling` exists because that number cannot say whether the shape is right. Measure a new
surface function at three world sizes before believing its ratio.

⚠ And the swap that made it slower is the point rather than the cost: see
[comparison.md](comparison.md) — moving `execution.step` down bought **nothing** in execution terms and
bought a readable record of the one loop that touches the world. The residue is the product.

**What is left is `driver._phase_*`** — and it is **not one item**. Audited by enumerating what the five
phase bodies actually call, rather than from a list, because the list was wrong last time:

| | what | state |
|---|---|---|
| **A. seams — dicts, tuples and prose** | | |
| A1 | `driver.step`'s **result dict**. `found`/`how`/`length` are already on the search node; `why` is prose built at the end by `_exhausted` / `_stopped` | the `_diverge` / `_DEVIATION_PHRASE` fix again |
| A2 | `X.report_of` inside the phases | ✅ **done** — `_phase_acting` and `_phase_recovering` read the replay node |
| A3 | an attempt's `diverged` (a sentence), `ran` and `steps` (tuples) | ✅ **done** — edges to the replay and the plan frame; `_history` renders |
| A4 | `T.attend(why=…, note=…)` at ~6 sites; `_record_execution` | facts + renderer, not yet done |
| **B. constructors** | | |
| B1 | `open_planning` — the `plan` native takes only `(goal, subject, thread)` and drops `max_steps` / `max_depth` / `guided`, which are **attributes of the pursuit** | widen the native to read them |
| B2 | `X.open_execution` — `path_to` plus seeding frame 0 | portable |
| B3 | `_looker_for` / `_looker_on` scan a rule **body** for a `DISPATCH` whose tool only observes | ⚠ **a capability gap**: nothing in the surface reads a body's instructions |
| **C. one genuine blocker, and it is a design decision** | | |
| C1 | **the hooks.** `rank`, `allow` and `trace` are *Python callables* threaded from `carry_out` / `follow` through `open_planning` and `step` | **cannot cross at all** |

⚠⚠⚠ **C1 is the purest instance of the defect this whole arc keeps meeting** — a value a rule can
neither build nor read — and unlike the others it has no mechanical translation.

✅ **And it is now decided, by the other arc.** It was recorded as a choice between making hooks **named
functions in the graph** and letting Python keep a wrapper for the hook path. Harmonization's proposal is
to **learn the rule ordering** ([harmonization.md](harmonization.md) §Harmonization as training), and
**you cannot learn a Python callable** — so hooks become data, and `rank` in particular becomes the
learned-order artifact. That is phase **P3** above, and it also wants the missing `by experience`
comparator. `advice-over-sequences.md` wanted the same thing, and
`_warn_if_advice_is_inert(g, rank)` was already hinting that `rank` had an authored counterpart.

`_phase_acting` and `_phase_recovering` are the two that are nearly free now: what remains in them is
`_record_execution` and `_plan_of`. `_phase_checking` is next-easiest — `goal.holds` is already live
beneath `G.satisfied`.

The three swaps are the template: **write the wrapper first**, keep the Python beside it as `_python_*`,
and take the comparison check through *every* route the wrapper offers — that is what `workbench.mf`'s
dormant years cost.

### 4. ✅ The predicates that blocked the rest — all three done and live

Nothing is left in this item. It is kept because the *reasons* each of the three was stuck are the most
transferable thing in this document, and `execution.step` will meet at least two of them again.

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

* **`goal.holds` is live** — `rules/holds.mf`, all four sorts, checked against `_python_holds` **twice per
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

  ✅ **And it is now the live one.** The blocker was a seam rather than a cost, and the fix was to stop
  carrying the world in two shapes: `goal.py`'s predicates take `ctx=`, `driver.context_in` produces it,
  and the wrapper passes it `under=`. The tempting wrong fix — minting a context per call inside the
  wrapper — was avoided; `context_in` reuses the one `step` already opened for that frame.

  ⚠ **The comparison check had to be repointed, or it would have gone vacuous.** It compared `G.holds`
  against a hand-rolled `fn.invoke` of `holds`. The moment `G.holds` *became* that invoke, both sides
  were the surface and the check would have passed whatever the surface did — green, and meaningless.
  It now reads `_python_holds` against the live wrapper, and reaches the frame through
  `driver.context_in` rather than a context minted in the check, so it cannot pass against a route
  nothing in the system takes. **A comparison check aimed at a moving target has to be re-aimed on the
  day the target moves**, and the day it moves is exactly the day nobody is looking at it.

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

### 7. Predicate dispatch, slices 3–4 — now split by the unified plan

⚠ **Read the phase table first.** **Slice 3** (conditions speaking of the ambient goal) is on the
critical path as **P1**'s sequel; **slice 4** (`wants_that_unblock`, a failed condition becoming a
subgoal) is *not* on the language path and stays a capability to want. The rest of this section is the
original argument, which still holds.

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

**A predicate that answers in prose cannot move to the surface** — and *prose* was the narrow name for
it. `unmet_expectations` returned sentences containing `repr(got)`; rendering is a decision, and a
rendering decision inside a predicate is a second thing the predicate is for. But `execution.step` then
found the same defect three more times with no sentence in sight: a tuple in an attribute (`ran`), a
rendered dict (`violations`), a Python list (`unbound`). The general test is **"could a rule have
produced this value?"** — a tuple, a dict and a sentence all fail it equally, and only one of them looks
like prose. Facts on nodes, rendering at the edge, in a table beside the reader that prints them
(`_UNMET_PHRASE`, `_NOTE_PHRASE`, `_DEVIATION_PHRASE`). `driver._phase_*` is next and will want it again.

**A node the Python already answers with is not thereby reachable.** `predicted_changes` returned a
graph node, which is what unblocked `unmet_expectations` — and it was still the thing that blocked
`execution.step`, because a rule cannot *ask for* it. The blocker list named the two predicates and
missed the producer sitting between them. When auditing what stands in the way of a swap, enumerate what
the body **calls**, not what looks Python-shaped.

**Where Python recovers after the fact, the surface asks before it — and `ATTEMPT` is not the
translation of `try`.** `ATTEMPT` catches every refusal and rolls its callee back. In `execution.step`
that would turn a standing prohibition (`Vetoed`) into a routine deviation and would promise a rollback
in the one place in the system that must never promise one. The right move was the `VKIND` move: find
the **answering form** of the question the enforcing form was raising about (`violations` against
`fn.invoke`'s type check) and ask it first. Reach for `ATTEMPT` when the failure really is an ordinary
outcome, not when Python happened to spell a guard as a `try`.

**Carrying one fact in two shapes is what blocks a swap, and the shapes look like different things.**
`goal.holds` was written, checked and correct for a whole session without being able to run, and the
obstacle was never a capability: Python held a **view** and a rule needs a **context**, which are the
same world in the shape each side can read. Nothing named that as a defect, because both shapes were
doing real work. The tell is a call site holding *both* — and the wrong fix is the convenient one, a
wrapper minting the missing shape per call, which makes two things that must agree and lets them drift.
The right one is to keep the shape both sides can read and derive the other where it is still needed
(`goal._world`), with a stated expiry rather than a permanent bridge. **Expect this to be the shape of
the next blocker too**: `execution.step` reports in prose, which is the same defect in the answering
direction.

**A comparison check aimed at a moving target has to be re-aimed the day it moves.** The `holds` check
compared `G.holds` against an `fn.invoke` of `holds`; when `G.holds` *became* that invoke, both sides
were the surface. It would have stayed green forever and meant nothing. This is the twin of the dormant-
twin lesson below and arrives at the opposite moment — not when the surface sits still, but when it goes
live — so a swap's checklist has to include *what was this check comparing, and does it still compare
two different things?*

**A dormant twin rots against the thing it shadows.** `rules/workbench.mf` sat written-but-not-live long
enough to miss the frame index and three parameters, while its comparison check kept passing — because
the check only ever called the one-argument form. *A comparison check is only as strong as the routes it
takes through both sides.* Nothing is written-and-not-live today — `holds.mf` was the last, and
`compare.mf` now runs under it on the goal path — so the risk has moved from rot to the one above: a
check whose two sides quietly became one. The answer to both is routes, not vigilance.

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
A fourth: the `_covers` precompute was on the plan as *cheap and decisive*, and the probe written to
de-risk it **cancelled it** — 0.6 ms across the whole suite, because the corpus has 61 names and one
body each. ⭐ A probe that is only allowed to confirm the plan is not a probe.

**A capability with a name is not a gap, even when the Python around it is unreachable.** The
reachability pass, read as a bare Python call graph, reports every wrapper the arc has *created* as
something a rule cannot start — so the number would get worse each time something moved to the surface,
which is exactly backwards. A measurement whose direction of improvement is inverted is worse than none,
and the tell was that its worst offenders were the functions the last three sessions had just finished
swapping. Ask what the number does when the work succeeds.

**A reachability question splits into two, and reading them as one is how a list drifts.** *Is there a
name a rule can call?* and *does that name carry the whole capability?* have different answers for
`driver.open_planning`: the `plan` native reaches it, and drops three of the pursuit's parameters on the
way. The first is mechanically checkable and now is checked; the second is a judgement about what the
name is *for*, and belongs in prose beside the item rather than inside the pass.

**The enforcing form arrives before the answering one.** Wherever the engine can only *enforce*,
something above it that needs to *decide* will have to be Python. `types.check` raised where a guard
needed `is_a` to answer; `INVOKE` raised where a replay stepper needed `ATTEMPT`. This is the most
reliable predictor of where the next island is — and it runs both ways: `ATTEMPT` answered where
nothing could *raise*, which is what `REFUSE` is. Finding one half of a pair is a reason to look for the
other.

**A thin end-to-end path is worth more than a finished layer, and it costs less than it looks.** The
P0–P5 order built infrastructure with no consumer; the skeleton was built out of order and most of what
the plan said it needed turned out to be unnecessary, because **a construction is a criterion with a
different address** — same test nodes, same specificity comparator, same explanation shape. The lesson is
not *skip the plan*; it is that a plan ordered by dependency will always look like it must be walked in
order, and building the thinnest complete path is how you find out which dependencies were real. Two of
five phases were.

**Ask what it is for before building it.** An identity for imagined nodes was nearly built as a minted
placeholder before anyone asked what needed one. The answer turned out not to be the reason assumed
(chaining) but that a goal constraint can be existential — and once that was clear, the thing needed no
mechanism at all. Two of the largest near-misses in this arc were designs for a requirement nobody had
stated.

**A ratio hides a curve.** The surface `execution.step` was O(world) — 618 / 1731 / 5206 ms at 6 / 30 /
120 blocks — and its *ratio* against the Python looked like an ordinary interpreter tax the whole time.
`scaling` exists because a single number against a reference cannot say whether the shape is right.
Measure any new surface function at three world sizes before believing its ratio, and remember that in
Python an O(world) step is a dict comprehension costing nothing, while here it is five interpreted
instructions per node — **the same algorithm changes complexity class in effect when it crosses down.**

**Measurement finds what checks cannot.** The `called`-versus-`caller` defect was invisible to three
successive checks and obvious to a benchmark, because two activations made moments apart have ids that
sort the way they were made. When a planted bug stays green, the usual cause is not a weak assertion but
a **world that cannot express the defect** — fix the scenario, not the assertion. `python -m ugm.bench`
exists so this stops being rebuilt in a scratch file each time.

⭐ **The same failure has a second form, and a probe is far more exposed to it than a check: a
*homogeneous* fixture cannot measure a *discriminator*.** The guard-address probe blanked the addressing
half of three criteria on Sussman's anomaly and measured **no difference whatsoever** — same plan, same
imagined states, same eleven bindings, at 5, 20 *and* 60 blocks. It looked like a clean negative result
and it was an artefact: Sussman's goal is two constraints of one sort and one label, so there is nothing
for an address to tell apart. Adding constraints the criteria were *not* about took the same measurement
from "free" to "no plan at all". **Before believing a probe that reports no difference, ask whether the
fixture contains two of the thing being discriminated.**

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

**The CNL does not grow itself — and that is a stance, not a limit.** Adding a block verb is an edit to
`intake.py`, so the family count is a **budget**, which is why *relate it in the web* is usually the
cheaper answer as well as the principled one. **Keep the budget; drop the claim that it is a property of
the design.** The two were being stated as one sentence, and they are not the same:

* *"Adding a verb edits `intake.py`"* — true, and a consequence of intake being **a parser**.
* *"The CNL cannot grow itself"* — a position, and one the evidence does not support. The
  homoiconic-grammar spike ran **green**: a grammar declared in CNL generated chart rules with no engine
  change, and the semantic fold went with it the same day — 68 CNL lines → 206 rules, **no Python escape
  hatch**. ⚠ That was the *old* engine, whose control regime was *"every enabled rule fires, nothing
  selects"* — which is exactly what makes a chart work, and exactly what this agenda-driven, selective
  engine is not. The finding does not transfer for free; it does show the constraint was inherited rather
  than discovered.

Full reification was then cut on a stated benefit argument — *"the only capability it enables is
in-engine grammar metareasoning, which the user ruled out"*. ⭐ **That premise has changed**: language
processing and reasoning sharing one preference machinery is exactly the benefit judged absent then.
The replacement discipline, stated positively: **a new way of saying something is an interpretation rule
in the web, never a new verb in `intake.py`.** See [comparison.md](comparison.md) for why *parsing* is
the thing to drop and what replaces it — the short version is that a parser decomposes an utterance
before any knowledge is consulted, which is Fodor's error committed at the front door.

⚠⚠⚠ **An assertion built out of the function under test degrades exactly as the code does.** The check
guarding chain-walked resolution asserted `mapping_for(f2, x) == mapping_for(f1, x)` — two calls to the
thing being tested — and **passed with the defect planted**. Compute the expected answer structurally, by
a different route from the code under test. A second lesson from the same plant: the bug must be planted
where the answer actually comes *from*, or the trap stays unsprung and the green means nothing.

**Plant against one check, not the suite.** `python -c "from ugm import selftest as S; print(S.check_...())"`
takes a second. A plant that blinds the planner takes the whole suite from 70 seconds to over ten
minutes, which is a slow way to learn one boolean.

**A check that asserts *no offenders* must also assert that the pass can still see one.** Blinding
`access.bare_touches` to answer empty left `EVERY_TEACHING_RULE_IS_MEDIATED` **green**: the mediation
claim was certifying itself, because *"nothing was reported"* is what a working pass over a clean corpus
and a broken pass over any corpus both say. The fix is a **positive control** — a deliberately bare body
in the same graph, reported by the same call. This is the twin of *an assertion built out of the function
under test degrades as the code does*, one step out: here the instrument is not the code under test, and
blinding it is still invisible.

**Every check must earn its green.** Several checks in this suite were once vacuous — passing whatever
the code did — and were fixed by planting a deliberate bug and confirming they went red. Any new check
should earn its place the same way. That practice is the reason to trust the rest.
