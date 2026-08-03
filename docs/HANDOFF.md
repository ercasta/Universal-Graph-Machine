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

1. **Decompose three predicates** — `goal.satisfied`, `workbench.deviates`,
   `workbench.unmet_expectations`. Each is plausibly either a loop over constraint nodes (wanting
   richer guard tests than `attr = value` / `is a T` / `is there`) or a native registered by its owner,
   as `types.is_a` already is. **Decide by decomposing, not by reaching for a native** — reaching for
   the native was the wrong call three times during the audit.
2. **Rewrite `workbench.step`** as a procedure. Its pieces are all expressible now.
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
