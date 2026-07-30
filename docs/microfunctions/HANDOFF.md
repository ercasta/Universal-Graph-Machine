# Handoff — 2026-07-30

**Read this first if you are picking this up cold.** One session, and it went further than a normal one:
the project's north star was repointed, a new engine was started, and it now runs a full plan-act-check
loop. `ugm/` and `units/` are untouched — nothing was deleted.

Verify the state in one command:

```
python -m microfunctions.selftest      # 78 checks, 0 errored
```

---

## 1. What changed, in one paragraph

The bet was always **content as data** — business rules, goals, plans, hypotheses, explanations, all in one
graph so that anything can be reasoned about, including another rule. It was never **pattern matching as
the execution model**. Those two had been welded together since the beginning, and essentially all of this
project's accidental complexity came from the weld. Separating them changes almost nothing about what the
system represents and almost everything about how it computes: rules become **microfunctions** — ordinary
imperative programs over the graph, *pointed at* their arguments rather than firing wherever the world
happens to match.

`microfunctions/` is that, in ~3,600 lines. It supersedes `ugm/`.

## 2. Reading order

| # | document | why |
|---|---|---|
| 1 | `north_star.md` | the repoint, the evidence for it, triggers, microfunctions, what gets cut |
| 2 | `the_data_model.md` | plain prose: what a goal, plan, hypothesis *are*; the operations; why they nest |
| 3 | `microfunctions/README.md` | the code's own entry point — every module, and the reasoning per layer |
| 4 | `planning_workbench.md` | the workbench design: mappings, frames, mocks, the direction invariant |
| 5 | `graph_data_model.md` | the analytical companion to #2 — tables, closure check, probe results |
| — | `docs/microfunctions/README.md` | index, plus a **staleness review** of #2 and #5 |

⚠ #2 and #5 were written before the substrate changed twice. Three passages were **corrected in place**
(the hypothesis section described a scope; §4 proposed a scratch graph; "operations are metarules"). The
staleness review records what changed. Everything else in them survived, which is itself the evidence that
the data model was genuinely independent of the execution model.

## 3. What exists and works

| module | role |
|---|---|
| `graph.py` | substrate — mutable, **named edges**, **ordered targets** (index addressing), edge properties, **references** (`Ref` ≠ edge), maintained reverse index, undo journal |
| `focus.py` | addressing — named heads; move forward/backward/through refs, fork, spread, close |
| `types.py` | a type is a **subgraph schema** (structure *and* attributes); structural sub/supertyping |
| `function.py` | **a rule is a function** — a named ISA program with typed params, stored in the graph |
| `asm.py` | the text surface and LLM border; `.mf` files; comments kept as data |
| `isa.py` | imperative ISA; `F(head)` operands make a program *pointed*; `INVOKE`, `DISPATCH` |
| `hypothesis.py` | a hypothesis is an ordinary **node** — no scopes, no relativization |
| `application.py` | applications and episodes — the record of what the system did |
| `selection.py` | candidates → rank → apply → record |
| `plan.py` | backward chaining over return types into a **lazy** chain |
| `dispatch.py` | the one place an effect leaves the graph, and its checkpoint |
| `workbench.py` | **imagining** effects on a copy — frames, mappings, mocks, forking |
| `execution.py` | **following a plan for real** — replay, deviation, contingencies |

## 4. The decisions that took the longest to reach

Each of these was got wrong at least once first, and the wrong version is recorded in the docs so nobody
re-derives it.

**Mutation is a cast.** A type is a schema over a subgraph — structure *and* attributes — the way a
Pydantic schema constrains a frame. So `service(c: car) -> serviced_car` is a **cast**, and whatever it
changes is merely how the cast is achieved. Nothing records that a mutation happened, because a node either
satisfies the stronger schema or it does not, checkable now rather than as a historical claim. Precondition
and effect reduce to parameter type and return type. **A cast returns its subject** — which is why `run`
falls back to the first argument when a function sets no `result`; creating something new is the case that
must say so.

**Planning is backward chaining into a lazy chain.** Nothing is committed by thinking: exploring a plan is
just not calling `run`. This removed the need for a supposition mechanism entirely.

**Frames are necessary; a log is not enough.** With one live state there is exactly one workbench node per
real node, so there is nothing to chain, and "what did this look like at step 3" is unanswerable. That is
the question that matters when reality diverges.

**Transformations bind *mappings*, never raw nodes.** A mapping points at the original and at this frame's
image. Following `original` yields the node an operation must really be applied to. A log saying
"`service` was applied" is unreplayable because it does not identify the subject in a form that survives
out of the workbench.

**⚠ The direction invariant: structure points outward, metadata points inward.** Anything *about* a node —
mapping, application, hypothesis, prohibition, plan step — points at it and is never pointed at by it.
Copying traverses outgoing edges, so one edge the other way drags in that mapping's original, image and
`next`, and thence every frame, every workbench, every plan touching that node. **Not a wrong answer: an
unbounded copy.** Enforced by `check_metadata_is_never_pointed_at_by_structure`, verified against a planted
violation. **This is the invariant most likely to be broken by a well-meaning convenience edge.**

**Do not label what the structure entails.** Workbench copies were briefly stamped with an `in_workbench`
attribute, with scans filtering on it and a test guarding the filter. That was a labelling error — it
asserts what the structure already entails, so it can drift. The real fix was **not to scan**: enumerate by
traversal from `root`, and copies are structurally unreachable. Marker, filter, parameter and test all
evaporated together. This relies on the discipline that **real things hang off `root`**.

> **A test guarding a mechanism added for lack of the structural answer is a smell — delete the mechanism
> and the test goes too. A test guarding a discipline a *human* must follow earns its place.**

**Mocks are rules, and outcomes are assumptions.** A call can turn out several ways, so a function has
*many* mocks, each an ordinary microfunction whose **return type is the outcome it assumes**. Declaration
order is preference order, free, because `mock` is an ordered edge. Choosing one is an assumption, recorded
as a hypothesis on the transformation — so `fragile_steps` answers "which parts of this plan are guesses"
as a lookup.

**⚠ Substitution and safety are two mechanisms and must stay apart.** Mock substitution on a workbench makes
planning *useful*; `dispatch.service` refusing an imagined target makes it *safe*. If substitution were
forgotten or bypassed, a dispatching function still could not reach the world. Putting the guarantee in the
substitution would put it in the wrong place.

## 5. What to do next

**1. Replanning on divergence** — the obvious next piece, and small now. `execute` reports a deviation and
`alternatives` returns the sibling branches already explored; nothing yet chooses one and continues, or
re-proposes from the actual state. Everything it needs exists.

**2. ⚠ Conflict detection — a regression, not a deferral.** The old rule engine surfaced two conclusions
disagreeing rather than letting one silently overwrite, and the composition-safety argument for the open
middle tier *rested on it*. The new engine has nothing; mutable last-write-wins. The intended answer is
reflective microfunctions — functions that read applications and the graph and detect conflicts — which
needs no new mechanism, only writing them. Do this before it becomes load-bearing.

**3. The scenario audit, before deleting anything from `ugm/`.** `north_star.md` §6: take the ten scenarios
in `docs/units/agentic_scenario_catalog.md` and ask, per scenario, which actually *requires* skolem
constants, ATMS environment-consistency, possibilistic bands, stratified negation, or demand-driven
selection propagation. Prediction: few to none, and where one seems required the real requirement will turn
out to be a language-model judgement. Cheap, decisive, and deletion should wait on it.

**4. A policy against enumerating mocks eagerly.** Three uncertain calls with three outcomes each is
twenty-seven plans, and that is a small plan. `step` defaults to the preferred outcome, which is right, but
nothing enforces "branch only where being wrong is expensive; keep the others for *on deviation*".

**5. Non-greedy selection.** `selection.py` ranks by a declared `priority` and is now the vestigial piece —
planning became the control flow. Learned preference over subsequences needs the episode corpus
`application.py` produces.

## 6. Known limits, stated so nobody rediscovers them

- **Planner:** depth-limited DFS, first solution wins. No cost model, no backtracking across a committed
  subgoal. Adequate for a handful of steps; not a general-purpose planner.
- **Copy cost:** a full copy per frame, and the real multiplier is the *stack depth* of nested workbenches
  (subgoal exploration), not the size of a single copy. Copy-on-write is the known lever and implements
  *exactly* the same semantics — it is not a smaller boundary. Deliberately not taken: measure first.
- **`compile_episode`** generalises single-argument operations on one subject. Multi-argument replay needs
  a decision about how old bindings map to new — a real question about *analogy*, not a missing mechanism.
- **Imagined-node matching** within one transformation is by kind and order. Two minted nodes of the same
  kind make the pairing a guess; `execute` says so in `notes` rather than choosing silently.
- **Termination and conflict arbitration** are both open. The ISA fails loudly at `MAX_STEPS` as an honest
  stand-in for the first; nothing addresses the second.
- **The undo journal is transactional only.** A rollback boundary must never span a dispatch. Do not design
  around it; if nothing outside `selftest.py` uses it, delete it.

## 7. Process notes that earned their place

**For every green, ask what would make it vacuous.** Five false or wrong greens were caught in one day: a
mis-credited wildcard made a closure check pass without checking anything; two sources wired to one gate
silently overwrote each other; a `None`-vs-`False` parameter tested the wrong world; a module-level check
list omitted every test defined below it; and one assertion reported `False` as a *value* rather than an
error, which a skim would have missed.

**Probe before believing the pattern.** Every claim in this session that was checked got weaker, and the
weakened version is the one worth keeping.
