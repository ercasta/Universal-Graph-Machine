# Handoff

Read this first when picking the project up cold. It says where things are, what state they are in,
what to do next, and which mistakes have already been made so they need not be made again.

**Verify:** `python -m ugm.selftest` — currently **240 checks, 0 failing**.

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
| the instruction set | [reference/isa.md](reference/isa.md) |

## Current state

The system takes goals as text, plans by imagining on a workbench, acts through one guarded door,
notices when reality disagrees, and answers questions with the derivation that produced the answer.

The most recent arc was a **capability audit** ([audit.md](audit.md)): finding everything that could
only be said in Python, and for each case deciding whether that was a decision or an accident. All
eight findings are closed. What came out of it:

* **`policy`** — norms, standing prohibitions, authority orderings, and what survives forgetting.
* **`procedure`** — `do` rungs, `for each`, `when`, lowering to an ordinary stored function.
* **`tie_break`** — how criteria are ranked, authored rather than compiled in.
* **Five reflection opcodes** (`KIND`, `NLABELS`, `LABEL_AT`, `NKEYS`, `KEY_AT`) that moved
  `open_workbench` out of Python and into `ugm/rules/workbench.mf`.
* **`ATTEMPT`**, and `INVOKE … with <node>` — a refusal as a value, and a binding set built at run time.

## What to do next

In this order. Steps 2–4 are the last large Python island: the plan-act-check-replan loop.

1. ~~Decompose three predicates.~~ **Done — see [audit.md](audit.md).** They got three *different*
   answers, and the total cost is smaller than the open question assumed:
   * `goal.satisfied` is a loop over constraint nodes. Its blocker was not a capability but a
     **closure standing in for a node** — `view` is only ever identity or `view_in(g, frame)`, so it
     becomes a frame node and two edge reads. What it does need is **one substrate opcode, `VKIND`**
     (a value's category: `text` / `number` / `boolean` / `null` / `unknown` / `list`), which closes
     both remaining gaps at once — naming `UNKNOWN`, and `compare`'s totality. `VKIND` must report
     the category and **not** decide which categories order together; that is `compare.mf`'s job.
   * `workbench.deviates` is three instructions and wants **`types.violations` as a native**, beside
     `is_a`. The answering form again: `is_a` says yes/no, `deviates` must say *how*. Decomposing
     `violations` reaches the `Req`/`AttrReq`/`Rel` dataclasses, not a loop — a real layer boundary,
     not a shortcut. The work is returning a node instead of a dict.
   * `workbench.unmet_expectations` needs **no capability at all**. It is blocked upstream: its inputs
     are Python dicts because `predicted_changes` returns one. That should return a transient node,
     dropped by its caller, as `reachable.mf`'s scratch node already is.

   **Nothing was built.** `VKIND` and `compare.mf` land *with* step 2, not before it — writing
   `compare.mf` early would duplicate `types.compare`, which is shared by `goal.holds`,
   `criterion._holds` and every schema check, and its own docstring records that a second
   implementation is the drift this codebase keeps finding.
2. **Rewrite `workbench.step`** as a procedure. **Started — the first prerequisite has landed.**
   Decomposed, it is: copy the carried-forward images, mint the new frame and its mappings, choose an
   outcome (`mocks_of` / `applicable` — edge reads plus `is_a`, which is already a native), call it,
   map what it minted, and record a transformation. `INVOKE … with <node>` covers building the argument
   set at run time, exactly as the audit predicted.

   **Done:** `copy_set` now lives in `rules/reachable.mf` and **carries edge properties**, which is what
   `workbench.mf` declared as a real gap on itself. It cost three opcodes — `NEPROPS`, `EPROP_AT` and
   `SETEPROP` — plus `graph.put_edge_props`. ⚠ **The recorded gap statement named only the two readers.**
   None of the three reads *writes*, and Python never noticed because `g.link(**props)` takes the whole
   dict at creation and the surface cannot hold a dict. `open_workbench` now shares `copy_set` instead of
   inlining it.

   **Also done — the other two gaps are closed:**
   * **`SELF`** gives a program its own activation, so it can ask what its own `INVOKE` did (`ACT.minted`,
     and `tr -ran-> act`). The callee needed nothing: the call just made is the newest source of the
     caller's `caller` edge. Not bundled onto `INVOKE` as a second destination register — that would be
     the `CLONE` mistake.
   * **`REFUSE kind why`** lets the surface decline. Both operands required, because an exception type is
     a claim about whose fault it is and a surface refusal has no Python class to be named by; the name
     travels as data and `ATTEMPT` reports it over the Python class.
   * ⚠ **`SOURCES` was replaced by `NSOURCES` / `SOURCE_AT`.** Reaching the callee needs to walk `caller`
     *backwards*, and `SOURCES` returned the whole tuple into a register — the only opcode that did, and
     unusable for it, since nothing indexes a register holding a collection. No program used it. This is
     the ISA's own count-plus-index convention applied to the one opcode that broke it.

   **`workbench.step` is now written**, in `rules/step.mf`, as five functions: `binding_value`,
   `outcome_fits`, `choose_outcome`, `outcome_named`, `carry_frame`, and `step`. It is checked against
   the Python it replaces on four routes — a plain cast, a chosen outcome, a named outcome, and a mock
   that mints — plus chaining, and an undeclared outcome.

   Two natives were added, both boundaries rather than shortcuts. `find_function` (owned by
   `function.py`) resolves a name to its node: decomposing it reaches `g.of_kind`, and giving the surface
   a way to enumerate every node of a kind is the whole-graph scan `types.instances` refuses at length.
   `minted` (owned by `activation.py`) gathers what a call created: decomposing it reaches a set union
   and a sort, and that sort decides which imagined node `execution._bind_minted` pairs with which real
   one.

   ⚠⚠ **An activation now records its calls forwards, as ordered `called` edges.** The first version read
   them backwards off `caller`, and that is wrong in a way nothing small shows: `g.sources` returns its
   answer **sorted by node id**, and an id is a string, so past four digits `activation#993` sorts after
   `activation#9905`. `step` was reading `carry_frame`'s activation as though the called function had
   minted the frame. **A benchmark caught it, not a check** — and the check that guards it now has to
   drive the id counter across a power of ten on purpose, because two activations made moments apart
   have ids that sort the way they were made. Three successive versions of that guard passed with the
   defect planted.

   **It is NOT the live implementation, and that is a measurement rather than a hesitation.**

   | world | Python | surface | |
   |---|---|---|---|
   | 5 blocks | 17.9 ms | 753 ms | 42× |
   | 20 blocks | 71.6 ms | 2248 ms | 31× |
   | 60 blocks | 301 ms | 6634 ms | 22× |

   ~2000 interpreted instructions per step at twenty blocks, and **essentially all of it is
   `carry_frame`** — the per-node frame copy. `step` is the innermost operation of `pursue`, called once
   per imagined state, so 25× lands directly on the measured hot path. The standing stance is *slow and
   singular beats fast and forked*, but 25× on the innermost loop is a different proposition from a
   phase machine that runs once per tick.

   The useful thing the measurement says is **where** the cost is: not interpreter overhead spread thin,
   but one O(world size) copy per step. So the question it raises is not "make the interpreter faster"
   but **"must a step copy the whole frame?"** — a question about the workbench's design, not about the
   surface. That is the honest next thread, and it was invisible until `step` was expressible.
3. **Rewrite `execution.step`.** Needs `ATTEMPT` and dynamic bindings; both exist.
4. **The phase machine** (`driver._phase_*`) falls out once 1–3 land. It is reads, guards, one call,
   attribute writes and unlinks — even its `_PHASES[phase]` dispatch is what a dynamic `INVOKE` does.
5. **Measure.** `pursue` is the measured hot path — asking criteria before enumeration was 6.6× at
   sixty blocks. Interpreted phases will be slower. The standing stance is *slow and singular beats
   fast and forked*, but that should be a measurement rather than an assumption.

`workbench.step` and `execution.step` are **expressible but not rewritten**. Those are different
claims and the difference should not be allowed to blur.

## How to work on this

**Decompose before believing something is primitive.** The single most useful test found here. It
turned six proposed natives into five substrate opcodes and two edge reads; it caught a third executor
that was not needed; it shrank every expansion in the audit below its first estimate.

**Test the claim before building the fix for it.** Three times during the audit something was
"missing" and already worked — dynamic function names most sharply. The cheapest guard is to try it.

**The enforcing form arrives before the answering one.** Wherever the engine can only *enforce*,
something above it that needs to *decide* will have to be Python. `types.check` raised where a guard
needed `is_a` to answer; `INVOKE` raised where a replay stepper needed `ATTEMPT`. This is the most
reliable predictor of where the next island is.

**A closed class earns its place by being declared** — named, reachable as data, with a stated
position on whether it has an escape into the web. See [concepts.md](concepts.md) on the horizon.

**The CNL cannot grow itself, on purpose.** Adding a block verb is an edit to `intake.py` forever, so
the family count is a budget — which is why *relate it in the web* is usually the cheaper answer as
well as the principled one.

**Every check must earn its green.** Several checks in this suite were once vacuous — passing whatever
the code did — and were fixed by planting a deliberate bug and confirming they went red. Any new check
should earn its place the same way. That practice is the reason to trust the rest.
