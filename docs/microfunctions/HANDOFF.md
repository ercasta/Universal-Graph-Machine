# Handoff — 2026-07-30

**Read this first if you are picking this up cold.** One session, and it went further than a normal one:
the project's north star was repointed, a new engine was started, and it now runs a full plan-act-check
loop. `ugm/` and `units/` are untouched — nothing was deleted.

Verify the state in one command:

```
python -m microfunctions.selftest      # 105 checks, 0 errored
```

> **Update, 2026-07-31.** §5's item 1 (replanning on divergence) is **done** — see §5a. Items 2–5 stand,
> but they are no longer the top of the list: **`docs/microfunctions/thread_and_system1.md` supersedes §5
> for what to do next.** The engine had no outer loop at all — nothing invoked plan/workbench/execution —
> and that design is it. Its §1 (the thread) is **built** (§5b), and the loop itself now **runs end to
> end** on a blocks-world scenario (§5c). What remains from that design is System 1 and bottom-up type
> recognition.

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
| `execution.py` | **following a plan for real** — replay, deviation, contingencies, recovery |
| `thread.py` | **materialised short-term memory** — attention shifts + applications, navigable, cross-linkable |
| `goal.py` | a wanted state as **constraint nodes**; `unmet` is what drives planning |
| `driver.py` | **the outer loop** — pursue a goal by imagining; the plan is *found*, not built |

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

## 5a. Done since — replanning on divergence (2026-07-31)

`execution.py` gained `matching_alternative`, `resume`, `replan` and `recover`, plus `leaves_under`; the
replay loop was factored into `_replay`/`_carry`/`_settle` so it can start mid-path. Five checks (78 → 83).

**The shape.** Once a step diverges there are exactly two honest moves, and `recover` picks on structure,
not policy. **`resume`** asks each sibling the *same* question that detected the problem — `deviates`,
against that sibling's own promise. A sibling that survives it is a plan for the world we are now in,
already imagined and already checked, so continuing down it is not replanning at all but following the
contingency the fork was for. Tried first on evidence: it is verified against this world, a fresh proposal
is not. **`replan`** handles the rest — propose afresh with the diverged step's real result as the subject,
since that node *is* the actual state. It returns a lazy chain, so re-proposing still commits to nothing.

**⚠ Three things that were easy to get wrong, and are now test-enforced.**

- **The diverged call is not re-run.** It reached the world once; running it again doubles its effects.
  Its real outcome is instead *settled* onto the chosen branch's own mappings, carried from the shared
  parent frame — siblings do not share mapping nodes.
- **The sibling must be the same function.** Siblings are alternative *successors*, not necessarily
  alternative *outcomes*; a fork may try a different action. Resuming into one of those skips a call that
  never ran and then reports success.
- **A resumed branch may refer to a node that was only imagined,** and the follow-up step may operate on
  *that* rather than on the subject. Whatever the real call minted has to be bound onto the *other*
  branch's imagined mappings.

**Probed rather than believed**, per §7. Each of the three was planted as a bug and confirmed to turn the
relevant keys red — including the last, which was found only because a spy showed `_bind_minted` was
running with an empty list on the resume path, i.e. the first version of that check was passing without
testing anything.

**Deliberately not done: rehearsing a re-proposal.** `replan` returns a chain; nothing runs that chain on a
workbench, so a re-proposal is unverified where the original plan was verified. The blocker is a real
question, not a missing function: turning a chain into workbench steps needs a rule binding each pending
call's *output* to a mapping, and for a minting call that is the same open question as `compile_episode`'s
multi-argument replay. A guessed binding yields a plan that *looks* rehearsed. Also first-wins, not
arbitrated: among several matching branches, and among several leaves below one.

## 5b. Done since — the thread (2026-07-31)

`microfunctions/thread.py` — materialised, navigable short-term memory. 8 checks (83 → 91). Full reasoning
in `thread_and_system1.md` §1; the short version:

**The gap it closes is not "no memory", it is "attention is not data".** `Focus` is a Python object holding
no graph state, fresh per call, discarded. In a system whose claim is that a rule can reason about a rule,
the thing it looks *with* was the one thing it could not look *at*.

**A thread IS an episode, extended** — an application entry *is* the `application` node, and
`application.steps` now filters to applications so `compile_episode` is unaffected. One record, not two;
a parallel log would mean every reflective function consulting both.

**Decisions that survived building:** two entry kinds only (deliberate attention shift, application — ⚠ not
every ISA instruction, which would log pointer arithmetic); order in the ordered `step` edge with `prev`
carrying O(1) backward navigation *and* the reason as an edge property; `connect` mints a **node** because
`eprops` is index-keyed and reindexes, so an edge property has no stable address and cannot be pointed at;
the thread does **not** hang off `root`, which is load-bearing for the coming region rule.

**⚠ One design argument was wrong and is corrected in the doc.** Backward-linking was justified by the copy
boundary — it does not discriminate, since nothing in the world points at the thread either way. The real
reasons are O(1) back-stepping and the reason-on-the-transition.

**Walking needs no new ISA op**, and that is checked rather than asserted: a thread-walker loaded from
stored `.mf` text runs on the ordinary machine. The first version of that check passed `F(e)` where `MOVE`
wants a head *name* — it silently opened a head named after a node id and returned `None`. Caught by the
vacuity guard, not by the green.

Three planted-bug probes confirmed the new checks bite: dropping the `prev` chain, unfiltering `steps()`
(which crashes `compile_episode` loudly — the right failure), and hanging the thread off `root`.

**Next:** the outer loop (nothing appends to the thread automatically yet), then System 1. And while the
reasoning is fresh, `thread_and_system1.md` §5b records a **live defect**: `types.tag` stamps `is_a` and
`application.generalise` reads it as authoritative, so the type cache already drifts today.

## 5c. Done since — goals, the outer loop, and END TO END (2026-07-31)

`microfunctions/goal.py` + `microfunctions/driver.py`, and a blocks-world scenario that runs the whole
thing. 6 checks (91 → 97). **The engine now has a computation model**: a goal is materialised, a thread is
bootstrapped, and `driver.pursue` imagines its way to a state satisfying the goal.

The goal in the scenario is **to produce a plan**, not to act — a goal *about* planning, which is what
homoiconicity was for. Nothing dispatches; the search is entirely on a workbench, guaranteed rather than
intended because `dispatch.service` refuses an imagined target.

**⭐ The plan is FOUND, not built.** `execution.path_to(wb, winning_frame)` already *is* a plan, and
`execute` — written for `workbench.step` plans long before this existed — replays it against the real world
unchanged. Checked end to end: real blocks `[1,1,1]` before, `[1,2,3]` after.

**⚠ Backward chaining cannot express repetition.** A function has one declared return type, so "stack a
block, then stack another" is not a chain of distinct casts. Repetition comes from the **loop**. `plan.py`
and `driver.py` answer different questions and both are right; do not try to make one do the other's job.

**Two limits of the type system the scenario surfaced** — recorded, not worked around:

- schemas are **one level deep** (`schema_of` never recurses), so "on a block which is on a block" has no
  declared form; blocks carry `height` as an attribute instead;
- a schema constrains **one argument at one call site**, so `stack(b, onto)` cannot declare `b ≠ onto`.
  `driver.proposals` enforces it.

**`selection.py`'s boundary held.** It excludes multi-parameter functions because "inventing bindings is a
different problem (search) that should not hide inside candidate generation". That search went into the
driver, and `selection.py` needed no change — the module boundary was drawn correctly the first time.

**⚠ The bug worth remembering, because of how it failed.** The first driver deduped on the *action*
(`function` + arguments) rather than the *state*. The root frame enumerates every pair, so every action was
marked seen at depth 1 and every branch below had nothing left to try — three-block towers became
unreachable. It did not crash: it reported a plausible **"no plan found"**. A silent wrong answer, from a
visited-set that looked obviously correct. Dedupe on the state (`driver.state_of`).

## 5d. Goals are CONSTRAINTS, and planning is driven by the unmet ones (2026-07-31)

A goal is no longer a wanted type name — it is a set of **constraint nodes**, materialised like everything
else: `a on b`, `b on c`. Three sorts (link between named individuals / attribute value / type). ⚠ Link
constraints cannot be folded into `types.py`: a schema says `{label: (kind, count)}` and never a *particular*
target, because a schema is reusable and individuals are not.

**⭐ `goal.unmet` is the whole point.** A goal that can only answer yes/no forces blind search. One that
names *which constraints are still false* lets the driver ask what could close them — means-ends instead of
generate-and-test. Measured against the identical breadth-first search: **3 imagined states versus 55**,
same optimal plan.

**⭐ Relevance is read off the function body** (`driver.establishes`). Nothing declares effects — the
repoint deliberately moved away from operators carrying declarative effect descriptions — but a function
*is* graph data, so what it could make true is read from its instructions, and cannot drift from the body
because it *is* the body. Conservative: an unreadable label yields `unknown`, which orders but never rules
out. **Effects carry their roles** (`stack` links *param `b`* onto *param `onto`*), without which
`stack(b=b, onto=a)` scores identically to `stack(b=a, onto=b)` for "a on b".

**⚠ It RANKS, it never FILTERS — now proved, not asserted.** Sussman's anomaly (C on A; want A on B, B on
C) is checked: the plan must *begin* with `unstack`, which closes no constraint and scores low. Greedy
means-ends would be stuck; ranking keeps it reachable. Found in 3 steps.

**Three wrong search designs, in order, all with the same lesson — measure the guidance, don't assume it:**

1. **Depth-first over frames.** Adding *one* irrelevant rule (`paint`) to the library was enough to burn
   the whole budget down a branch that could never close the goal, while the sibling that solved it in one
   more move sat untouched on the stack.
2. **Best-first over frames.** Fixed that, and measured **no better than unguided** (15 against 14) —
   because every proposal in a frame was imagined before any frame was chosen. Ordering inside a frame
   cannot save work already done. The frontier must hold *proposals*.
3. **Best-first over proposals, keyed by the parent's open count.** Made the guided search *worse than
   breadth-first*: an unexplored root proposal that would obviously close a constraint carried its parent's
   score, while mediocre moves two levels down scored better, so the good move was abandoned permanently.
   **A proposal must be judged by the world it would produce, not the one it starts from** — hence
   `expected = open − 1 if the move exactly writes an open constraint`.

## 5e. Constraints on the PLAN, not just the world (2026-07-31)

A goal can now constrain the route as well as the destination: `forbid_action` (by operator, by node, or
both), `require_action`, `limit_steps`. This is what having the plan *in the graph* is for — it is not a
value a planner returned, it is frames and transformations, so "which actions may I use" is an ordinary
question about ordinary data.

**⚠ Safety versus liveness is the distinction that decides the whole design.**

- **Safety** ("never unstack", "never touch c", "at most 3 steps") — violated by a prefix ⇒ violated by
  every extension. A breach is a **proof** the branch is dead, so it prunes, and prunes *before* the step is
  imagined: a forbidden action costs nothing.
- **Liveness** ("must include a paint step") — a prefix without it is unfinished, not in violation. Checked
  only once the world constraints are met; must never prune.

Backwards in either direction fails: defer safety and the search burns out on branches that died at step
one; prune on liveness and nothing survives.

**⚠ This is where filtering is RIGHT, and it does not contradict §5d's "rank, never filter".** Relevance is
a *guess*, so filtering on it could lose a solution (Sussman needs a low-scoring move). A safety breach is a
*proof*. **Rank a guess; prune a proof.** Worth keeping both sentences together — they look contradictory
out of context and are not.

**⚠ Liveness changes search-node identity.** Two routes to the same world differ if one has already done a
required action and the other has not, so the visited key is `(state, still outstanding)`. Deduping on the
world alone would silently discard the finished route — the same class of bug as §5c's action-vs-state
dedup, caught this time by thinking about it rather than by a failing check.

**Distinct from `dispatch.forbid`**, which vetoes a *dispatch* at the world boundary at execution time and
cannot express "don't use this operator". Different layers; both wanted.

Checked: forbidding `unstack` turns Sussman's anomaly from solvable into honestly-unsolvable, and the banned
operator is *never once imagined*; forbidding a node keeps it untouched; a required action appears in a plan
that has no other reason to contain it; a step limit refuses at 2 and succeeds at 3.

## 5. What to do next

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
