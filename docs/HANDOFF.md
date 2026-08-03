# Handoff

Read this first when picking the project up cold. It says where things are, what state they are in,
what to do next, and which mistakes have already been made so they need not be made again.

**Verify:** `python -m ugm.selftest` — currently **244 checks, 0 failing**.

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
| why rules will stop calling `GET` | [mediated-access.md](mediated-access.md) — a design note, nothing built |
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
procedures. That is [mediated-access.md](mediated-access.md) — **a design note, nothing built, and now
the main thread.**

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
* **`workbench.step` is written**, in `rules/step.mf`, checked against the Python on four routes plus
  chaining and a refusal. Two natives added: `find_function` and `minted`. **Not yet live** — see the
  measurements below.

Traps worth not re-learning:

* ⚠⚠ **`g.sources` returns its answer sorted by node id**, and an id is a string, so the reverse index
  cannot answer *the most recent*. An activation records its calls forwards as ordered `called` edges
  because of this. **A benchmark caught it, not a check**, and three successive guards passed with the
  defect planted — the surviving one drives the id counter across a power of ten on purpose.
* ⚠ **A recorded gap statement is a hypothesis, not an inventory.** The edge-property gap was documented
  as needing two reading opcodes; it needed a third to *write*.
* ⚠ Doc-comment blocks attach to the next `fn`, so inserting a function between a comment and its `fn`
  silently orphans the docs.

## Where the cost is

`workbench.step` in the surface, against the Python it replaces:

| world | Python | surface | |
|---|---|---|---|
| 5 blocks | 17.9 ms | 753 ms | 42× |
| 20 blocks | 71.6 ms | 2248 ms | 31× |
| 60 blocks | 301 ms | 6634 ms | 22× |

~2000 interpreted instructions per step at twenty blocks, and **essentially all of it is `carry_frame`**
— the per-node frame copy. `step` is the innermost operation of `pursue`, called once per imagined
state.

**The workbench cannot stay in Python**: planning that Python owns is planning the system cannot inspect
or change, which is the island the whole design exists to avoid. So the numbers say how much has to
change *before* the swap, not whether to make it. Avoiding the copy means a frame sharing versions with
its predecessor, which is only correct if reads are mediated — and mediation can live neither in the
kernel (it would have to know what a frame is) nor in Python. That leaves in-graph procedures.

## What to do next

[mediated-access.md](mediated-access.md) is the design, and it is decided enough to build from. Read it
first; it also records two wrong turns in some detail, and both are easy to make again.

1. **Two small fixes, right regardless of everything else.**
   * **Retention must become a call-site choice.** `function.invoke` runs with `retire=False` so a caller
     can ask what its call did, so every call leaves an activation, a focus, its heads and registers —
     ~5 nodes. Measured. Once reads are calls that is untenable, and it is a hygiene problem before it is
     a speed one: this system has already once mistaken interpreter scaffolding for world content.
   * **`INVOKE` should accept `F(x)` as its function operand.** It takes a literal or a register but not
     a focus head, so a procedure passed as a *parameter* needs a `COPY` first — friction sitting exactly
     on the pattern the design depends on.

2. **Build mediated access**, in the order the note argues for: the closed vocabulary as ordinary
   procedures; context on the activation, inherited through `caller`, established at the goal machinery,
   `step`, nested workbenches and `execution`; the four natives that need it (`is_a`, `check`, `plan`,
   `plan_step`); and the compliance check that a business rule contains no bare graph-touching opcode.
   `loop._after` is the precedent to read first — it already finds its agenda by walking from `act`.

3. **Make frames sparse** — a frame maps only what changed in it, reads walk up the chain, and an edge
   points at a canonical identity so resolution happens on the target. This is what all of it was for.

4. **Swap `step.mf` live**, and re-measure. Only now is the comparison meaningful.

5. **`execution.step`**, then **the phase machine** (`driver._phase_*`), which is reads, guards, one
   call, attribute writes and unlinks — its `_PHASES[phase]` dispatch is what a dynamic `INVOKE` does.

6. **The three predicates**, which are independent of the above and can be done whenever: `VKIND` and
   `compare.mf` land together with `goal.holds` (writing `compare.mf` earlier would duplicate
   `types.compare`, which `goal.holds`, `criterion._holds` and every schema check share); `violations`
   as a native; `predicted_changes` returning a node.

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

**Every check must earn its green.** Several checks in this suite were once vacuous — passing whatever
the code did — and were fixed by planting a deliberate bug and confirming they went red. Any new check
should earn its place the same way. That practice is the reason to trust the rest.
