# Handoff — 2026-07-30

**Read this first if you are picking this up cold.** One session, and it went further than a normal one:
the project's north star was repointed, a new engine was started, and it now runs a full plan-act-check
loop.

> ⚠ **Corrected 2026-07-31:** this paragraph used to end "`ugm/` and `units/` are untouched — nothing was
> deleted." **Both directories are gone from the repo now**, so the scenario audit in §5 item 3 ("before
> deleting anything from `ugm/`") is moot as written, and `../pystrider`'s `test_conformance_strider.py`
> and `test_rulestrider.py` fail collection on `import ugm` — two dead test files over there, unrelated to
> any engine change.

Verify the state in one command:

```
python -m microfunctions.selftest      # 196 checks, 0 FAILED
```

> **⭐⭐⭐ Update, 2026-08-01 — READ §6c–§6i BEFORE §5.** The whole of §6b's arc landed in one day and
> **§5 below is largely historical**: §6c made the ISA tick, §6d built the single outer loop (`loop.py`),
> §6e probed the strong version (b) and recommends **not** doing it, §6f showed the system can judge its
> own computation, §6g made **forgetting the default**, §6h built **transitive reach**, §6i added the
> **wh-questions** (`locate.py`), and §6j made a universal constraint **rankable**. §5's items 3–5 still stand and are listed there; **§9 is the current
> list.**

> **⭐⭐⭐ Update, 2026-08-02 — GRANULARITY. Read `docs/microfunctions/granularity.md` and then §6k–§6n.**
> A design pass on *plans at more than one grain* (nested plans, detours, several plans at once,
> preconditions) turned into **three probes and four slices**, and the probes are the important part:
> **two of the design's own claims were measured wrong**, and two defects nobody was looking for turned up.
> §6k is the probe results, §6l–§6n the slices. ⚠ **§6l changes an ordering that every recorded cost figure
> in this document was taken under** — see it before trusting a number here.
>
> ⚠ **Two arcs landed concurrently on 2026-08-02 and the check counts interleave.** §6k–§6n took the
> suite 184 → 188; a separate arc (`criterion.py`, `docs/microfunctions/cnl.md`,
> `docs/microfunctions/expert_judgement.md`) took it to **196**, and is documented in its own files
> rather than here. So the per-section counts below are the state *at that section*, not a running
> total — only the verify line at the top is current.

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
| 4b | `granularity.md` | ⭐ plans at more than one grain — nested plans, detours, several at once, preconditions. Parts I–III are design, IV the build order, **V the probe results that weakened two of its own claims** |
| — | `docs/microfunctions/README.md` | index, plus a **staleness review** of #2 and #5 |

⚠ #2 and #5 were written before the substrate changed twice. Three passages were **corrected in place**
(the hypothesis section described a scope; §4 proposed a scratch graph; "operations are metarules"). The
staleness review records what changed. Everything else in them survived, which is itself the evidence that
the data model was genuinely independent of the execution model.

## 3. What exists and works

| module | role |
|---|---|
| `graph.py` | substrate — mutable, **named edges**, **ordered targets** (index addressing), edge properties, **references** (`Ref` ≠ edge), maintained reverse index, undo journal |
| `focus.py` | addressing — named heads **as graph data**; move forward/backward/through refs, fork, spread, close |
| `activation.py` | **the interpreter's own state** — `pc`, stack, registers, what a call minted; the yield point |
| `loop.py` | **THE OUTER LOOP** — one agenda, one tick, one primitive step; `imagine` / `look` / `act` / `forget` |
| `forget.py` | **the slower clock** — forgetting is the DEFAULT; a tool call and a surprise are the exceptions |
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
| `goal.py` | a wanted state as **constraint nodes**; `unmet` drives planning; **hierarchy** gives context |
| `driver.py` | **the outer loop** — pursue a goal by imagining; the plan is *found*, not built |
| `intake.py` | **the border** — one closed CNL for goals, guidelines, methods, types and questions; refuses |
| `locate.py` | **the wh-questions** — `what` / `where` / `when`: locate a thing in an order that already exists, and record nothing |
| `conflict.py` | contradictory goals, and **interference** between goals over one slot |
| `guideline.py` | **authored preference as data** — reorders within a band, can never exclude |
| `method.py` | **authored decompositions as data** that select themselves; prune on *authority* |
| `criterion.py` | a concurrent arc, not covered here — see `expert_judgement.md` and `cnl.md` |

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

- ~~schemas are **one level deep** (`schema_of` never recurses), so "on a block which is on a block" has no
  declared form; blocks carry `height` as an attribute instead;~~ **RETIRED 2026-08-01 — see §5v.**
  `Req(type=…)` recurses to any depth and `Rel` relates two places inside one subgraph.
- a schema constrains **one argument at one call site**, so `stack(b, onto)` cannot declare `b ≠ onto`.
  `driver.proposals` enforces it. **Still true** — a type is about one subgraph, and two parameters are
  two subgraphs with no node above them to hang the demand on.

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

## 5f. Expectations — divergence the declared type cannot catch (2026-07-31)

`workbench.predicted_changes` / `unmet_expectations`, checked by `execution._replay`. 6 checks (105 → 111).

**⭐ Derived from the two frames, never authored and never stored.** The workbench already imagined the
outcome, so frame N−1 and frame N *are* the before and after: the expectation is their difference. Storing
expectation nodes was the obvious alternative and would have been a labelling error, plus a node per
imagined step, of which the driver makes hundreds.

**⭐⭐ QUALITATIVE, NEVER QUANTITATIVE — the correction that matters most.** The first version compared
magnitudes: the mock minted two file nodes, so it expected two. That is useless in practice, because a
listing produces a *variable* number and a plan diverging on three-instead-of-two is diverging on noise.
**The number in a mock is a witness, not a promise.** The expectation is existential — *some* file exists.
Checked: one file and five both complete; zero still diverges.

The division of labour, now explicit:

- **the declared return type carries the discriminating claim** (empty vs non-empty) — checked by the cast,
  and deliberately *not* re-checked as an expectation, so a failure is reported once where it belongs;
- **the derived expectation carries the qualitative shape** (files appeared, the directory got marked).

**⭐⭐ The same knowledge drives PLANNING, and it comes from the mocks.** `establishes` now unions in each
declared outcome's effects, and records `NEW` as a `mint` effect. `scan_dir(d: dir) -> listing` mentions no
file and its body is a `DISPATCH`; the fact that listing produces files lives in the **mock**, which is the
declared assumption. So a goal of "some file must exist" finds the call — something no parameter or return
signature could express. Recovery through the ordinary contingency machinery works on these too, and
`matching_alternative` now judges a sibling by *its own* expectations, not merely its type.

**⚠ A LIVE BUG this surfaced: mocks were being proposed as actions.** A mock is an assumption about how a
real call turns out, not something to do — the first run planned `found_two` instead of `scan_dir`, i.e. a
plan naming a function that must never be executed for real. Invisible in a library without mocks, which is
why blocks-world never showed it. Fixed in `driver.proposals`; `workbench.step` substitutes the mock when
the real operator is stepped, which is where that belongs.

## 5g. END TO END — plan, act, diverge, replan, succeed (2026-07-31)

`driver.carry_out`. Asked "do we have an end to end?", the honest answer was **no** — every piece was
checked in isolation and running the whole chain broke in three places. All three are now fixed.

**⚠ Replanning was going to the wrong planner.** `execution.recover` chains backwards over return types via
`plan.py`, which knows nothing about a goal's constraints. Asked to recover a diverged "some file must
exist", it answered *"listing: already satisfied"* — true, and useless. Recovery for a driver-made plan has
to come back to `carry_out` and re-pursue the **goal**; replanning is just going round the loop again, and
it needs no new state because `pursue` opens a fresh workbench on the current real subject.

**⚠ The driver closed a world goal on IMAGINED evidence.** After a diverged execution the goal read as met
while nothing had happened. Split into `record_plan` (a plan was found — met in imagination) and
`close_goal` (met in reality). "I know how to do this" and "this is now true" are different claims.

**⚠ The driver never forks on mock outcomes**, so a plan it produced has no sibling branches and `resume`
can never apply to one. Stated rather than hidden; it is why the loop leans on replanning. Closing it is
`§5` item 4's question from the other side.

**⚠ AND THE HARNESS WAS NOT FAILING ON `False`.** It tallied only exceptions, so a check that ran fine and
answered "no" printed among a hundred lines and a skim missed it — the mistake §7 already records having
made once, made again with `goal_recorded_as_met`. `report()` now counts any key that is exactly `False`;
the tally reads **FAILED**, not "errored". Non-boolean values (counts, reasons) are left alone. No other
latent `False` was hiding.

The run: first listing finds nothing, the prediction breaks, it replans from the real state, a file has
appeared, the second attempt completes, and the goal is closed *only then*. Ten thread entries hold the
whole story.

## 5h. Intake — something said becomes a goal (2026-07-31)

`microfunctions/intake.py`. The loop is driven entirely by a goal, and the only way to get one was to call
`goal.py` from Python — so the one thing that *starts* the system was the one thing it could not receive.

**⭐ Why this is a small module now, when it was a research programme before.** The `ugm/`-era attempts
translated prose into *arbitrary graph structure* and scored 0/50 on raw prose, with the gap recorded as
"100% constructional" — unsurprising, since the target was unbounded. A goal is no longer arbitrary
structure: it is a handful of **constraint nodes from a closed vocabulary**. Eight forms is a different
problem from anything. The intake problem changed shape because §5d changed what a goal is.

**The border is unchanged from the standing position:** a model may *write this text*; the parser then
accepts or refuses it deterministically. What a model must never do is reach past the surface and write
graph structure, because then nothing could refuse it. `asm.py` is this for functions; `intake.py` is its
sibling for goals.

**⚠ Refusal is the feature**, three ways, all loud: a line outside the vocabulary; a name matching nothing;
and a name matching **more than one thing**. That last is the recorded lesson — nodes are nameless and a
`label` is a convenience, so *never identify by name alone*; guessing between candidates would invent a
referent. A refusal leaves **nothing behind**, because a half-built goal would be pursued and would look
like it was working.

```
goal stack a on b on c:      ->  carried out: True in 1 attempt
    a on b                       plan: ('stack', 'stack')
    b on c                       reality: a on b? True
    never unstack
    at most 4 steps
```

## 5i. The type-cache drift defect — FIXED, and recognition gained (2026-07-31)

`thread_and_system1.md` §5b recorded this as a **live defect**, measured rather than hypothesised:
`types.tag` stamps `is_a`, and `application.generalise` read that raw attribute as authoritative. A stamp
is a claim about the *past*; `is_a` is computed from current structure. Remove a wheel from a tagged car and
the stamp still said `car` — so a learned function took its parameter name *and its declared type* from a
class the node no longer belonged to, producing a function that would refuse its own training example.

**The rule, as designed: cache the candidate, re-validate on read.** `types.tagged_as` returns the hint only
if it still holds. The cost that justifies a cache is the *search over all types* (linear in how many are
declared); one check against a *named* type is ~25µs, so re-validating is nearly free and drift becomes
structurally impossible rather than merely unlikely. The raw attribute is now documented as a hint about
what to check, never an answer, and `tagged_as` is the only sanctioned reader.

**⭐ And `types.recognize` — the bottom-up direction the module never had.** Every entry point was top-down:
`is_a` asks about a *named* type, `instances` enumerates for a *named* type, nothing asked what a node turns
out to be. Three lines, because typing was already structural and dynamic — only the direction was absent.
**Multi-type and de-recognition fall out** rather than needing mechanism, which is the evidence the shape is
right: independent structural predicates, so of course a washed car is also a serviced car, and of course
removing a wheel de-recognises it with nothing to invalidate.

That closes §5 of `thread_and_system1.md`. What remains from that design is System 1 itself, which the
end-to-end work showed to be an **optimisation** at this scale rather than a capability — it becomes
load-bearing only when the world is too large for `driver.proposals` to enumerate.

## 5j. Conflict detection — the regression, addressed (2026-07-31)

`microfunctions/conflict.py`. §5 item 2 called this a **regression, not a deferral**.

**⚠ The old notion does not transfer, and copying it would have been wrong.** That engine *derived facts*,
so two rules concluding contradictory things was a contradiction outright. This one *performs actions in
sequence*, where a later write legitimately overrides an earlier one — `stack` sets `clear` false on one
block and true on another every time it runs. Reporting that would bury the real cases.

What survives is **interference**: two independently authored functions, composed by a library that grew,
writing one slot for unrelated reasons — the telecom feature-interaction problem `function.py` already
cites as prior art. Two detectors, for two different questions:

- **`unsatisfiable(goal)`** — decidable contradictions only, so no false positives: two attribute
  constraints on one slot demanding different values, `never f` with `must f`, a budget of zero. `pursue`
  now refuses such a goal at zero cost instead of searching for it.
- **`interference(thread)`** — two goals that really did write one slot differently.

**⭐ A conflict needs no new node kind:** it is a `connection` with relation `conflicts`, the cross-link
`thread.py` already had. "No new mechanism, only writing them" turned out to be true.

**Three wrong versions, each caught by a vacuity guard rather than by a green.**

1. **Latest-value scanning.** Comparing each write against a running latest value silently lost the pairs
   it was looking for: the second goal re-imagined the *same* action before its differing one, so a
   same-goal entry overwrote the running value and the cross-goal disagreement never met. Interference is
   a property of two *intents*, so claims must be grouped per intent and compared afterwards.
2. **⚠ Analysing the search instead of the actions.** The driver records every proposal it considers,
   most from branches it abandons — so a goal that *considered* `paint` before choosing `varnish` looked
   like it claimed both. The thread held planning and nothing about what actually happened.
   `driver._record_execution` now puts what really ran on the thread marked `done`, and `interference`
   looks only at those. **This closed a gap listed as missing since §5b: execution never reached the
   thread.**
3. **Recording workbench copies as the subject.** Two goals open two workbenches, so their entries could
   never refer to the same node and no reflective reader could line them up. The driver now records the
   real node a copy stands for — more truthful anyway, since an application says which function was
   applied to which *subject*.

**And the harness gained a fix of its own:** the `FALSE` marker added in §5g used a non-ASCII glyph, which
made the report unpipeable on a cp1252 console. ASCII now.

## 5k. The first consumer's feedback, worked through (2026-07-31)

`../pystrider/docs/feedback_microfunctions.md` — written against `d7110c4` by the team building `strider/`
on this engine, 5 modules and 79 pins doing Python source → graph → neutral descriptions → recognition.
Every item arrived as *measured repro* plus *hypothesis about the cause*, with the hypotheses flagged as
things to check rather than findings. **Every one of their diagnoses was right**, which is worth recording
because the same document explains that several of their confident diagnoses against the *old* engine were
inverted. Reading effects off a stored body turns out to be a thing an outsider can reason about correctly.

**⭐⭐ The big one: a role is a PATH, not a parameter name (`driver.establishes`).** A function whose
operands are parameters read beautifully; one that had to **navigate** went dark.

```
fn lower_threshold(c: comparison) -> comparison:
    GET R(rhs) F(c) "right"        # ← the subject is now in a register
    ATTR R(v) R(rhs) "value"
    ADD R(v2) R(v) -1
    SET R(rhs) "value" R(v2)       # ← writes to a register: reported as an effect on NOTHING
```

An operation whose entire purpose is to change the comparison statically appeared to change nothing. Their
framing is the one that generalises: *read a part, write to that part* is what most operations on
structured data look like, so the functions that were invisible were exactly the ones doing real work on a
structure — and a bridge between two vocabularies is nothing **but** navigation.

The fix is provenance, and it is static and free: `R(rhs)` was assigned by `GET R(rhs) F(c) "right"`, so it
denotes *`c`'s `right`*. Three role forms now, distinguishable by inspection — `c` (a parameter), `c.right`
(navigated, `c.child[2]` for an indexed hop), `$it` (minted locally).

**⭐ The half that was not obvious: the path is resolved DYNAMICALLY, in `driver.role_node`.**
`establishes` can say *`c`'s `right`* without knowing which node that is; only a caller holding bindings
can turn that into an individual and ask whether it is the one a constraint is about. Static provenance
plus dynamic resolution is what restores band 4 for a navigating operator, and splitting it that way is the
whole trick — neither half alone does anything.

Measured on two comparisons with a goal to lower one literal (`check_ranking_sees_through_a_navigating_operator`):

| | imagined states |
|---|---|
| guided, with paths | **3** |
| guided, without them (the previous behaviour) | 5–10 |
| blind | 5–10 |

⚠ **The step counts are not the finding; the band is.** Without paths, *no proposal could reach band 4 at
all* — so the guided search and the blind one were the same search, tie-broken by frontier insertion order,
which is why the two controls straddle each other run to run. That is `../pystrider`'s "found essentially
unguided" in this engine's own numbers, and it is why the check asserts band reachability rather than a
timing.

**⭐ `unknown` says WHAT it could not read.** It was whole-function, so an unreadable write to `y` darkened
a description that was provably complete for `x`. It is now a **frozenset of the roles** the unreadable
instructions concern, `None` meaning "somewhere we cannot name at all". Empty is falsy, so every existing
`if unknown:` reads unchanged. Their deeper point is now in the docstring: **`establishes` is an
over-approximation by contract** — conservative for ranking, a false-positive generator for recognition —
and the same return value carries opposite safety for its two consumers. That should have been said out
loud the first time.

**⭐ `INVOKE` had no operand-shape check, and it is the only opcode with a shape** (`asm.py`). Every opcode
*name* was validated; `INVOKE`'s third operand is a *mapping*, there was no way to write one in `.mf`, so
the natural positional form parsed, defined, and failed at run time inside the interpreter with
`AttributeError: 'str' object has no attribute 'items'` — no line, no opcode, nothing naming the operand.
Exactly the silent acceptance `asm.py`'s own docstring says it exists to prevent. There is now a surface
(`INVOKE R(out) as_iteration it=F(f) seq=R(s)`) and anything else is refused with a line number.

That was filed as a bug and the feature request behind it mattered more: **a microfunction was not
composable from another in the authored surface**, so `strider/` duplicated a vocabulary across two `.mf`
files and checked for drift itself. It is now. ⚠ Fixing the surface exposed a second silent break: `unparse`
rendered the raw Python dict, so a **learned** function (`application.compile_episode` builds `INVOKE`
operands in Python) could not be read back in. The only guard was that the word `INVOKE` appeared in the
dump — a vacuous green of exactly the kind §7 keeps catching.

**⭐ Compose-time interference (`conflict.interference_between`).** Their hypothesis — "`interference` over
a frame chain, the same function with a different source of claims" — was right, with one correction: it
takes **two** chains, never one. A single chain is one committed plan, and steps within one plan are a
deliberate sequence; reading one would report the ordinary sequels the `done` filter and the different-goal
requirement exist to suppress. With two plans it is nearly free, `claims_of` reused unchanged, and it
reports a collision **before either plan runs**. ⚠ It is the only detector here that reports something that
has not happened, so it is the only one that can be wrong about the future, and it records nothing on the
thread for that reason.

**Papercuts, both load-bearing.** `function.param_names` exists (they were reduced to `load(g, name)[0][1]`),
and — the question worth answering — **"the first parameter is the subject" is a GUARANTEE, not a
convention**, now said out loud in `function.subject_param`, which `execution.py`'s two dependent sites call
instead of re-deriving it.

**Documented rather than changed, because the gap was in the docs:** `pursue` now says that the failure
report hands back the `workbench` **so the explored frames can be interrogated** — a refusal's reason lives
there and nowhere else — with the authoring rule that follows and had never been written down: *an
operation that wants to explain itself must record its reason where the frames are.* A microfunction that
quietly does nothing when a precondition fails is unexplainable after a failed search; one that writes
`unsupported_confirmation_step` is diagnosable. Silence costs nothing at planning time and everything
afterwards.

**Left alone, deliberately.** ⚠ **Reversed 2026-08-01 — see §5v.** `types.schema_of` being flat was argued
here to be not a defect: a schema constrains each label independently and so can never say "the `body` and
the `element` are related this way", which is why their patterns are read off function bodies via
`establishes`. That argument was right about the *limit* and wrong about it being the right one to keep —
`Rel` says exactly that, in the same graph data, checked by the same code that checks a count.
`types.recognize` classifies structure, theirs carries joins, and the two are still complementary rather
than one subsuming the other. And **quantifiers**: an
open question ("who is admitted") becomes one search per candidate here, which they measured at 2 searches
and 22 imagined states against one saturation, called affordable, and explicitly did not ask for. Noted as
a shape consumers will keep bringing rather than as a thing to build.

**Verification:** 126 checks 0 FAILED here, and `../pystrider`'s 110 `strider` pins pass unchanged against
the modified engine — including the `unknown` bool → frozenset change, which they consume as `if unknown:`.

## 5l. ⚠⚠ THE SEARCH WAS IRREPRODUCIBLE — root cause found and fixed (2026-07-31)

Found while asking a different question: *has the world got big enough for System 1 to be worth
building?* The scaling measurement disagreed with itself, and that turned out to matter far more than the
question that prompted it. 133 checks, 0 FAILED.

**The defect.** `workbench.reachable` traverses deterministically — `g.labels` is sorted, `g.targets` is an
insertion-ordered tuple — and then returned a **`set`**, discarding that order. Set iteration order of node
ids then decided the copy order. Ids come from a **process-global** counter (`kind#N`), so the same world
built twice in one process gets different ids, hashes in a different order, and is copied in a different
order. `mappings` order is `proposals` order, and `pursue`'s frontier breaks ties by insertion order. Same
defect a second time at `workbench.step`, which rebuilt `set(prev_images.values())` per frame.

Measured on one identical five-block goal, consecutive runs of one process:

```
found=False imagined=400 (budget exhausted)
found=False imagined=400
found=True  imagined= 12
```

**⭐ Nothing was ever lost, and that is the whole reason it survived.** The *set* of proposals is identical
every time — checked — so this never produced a wrong plan, only an **arbitrary plan at an arbitrary cost**.
A single run of anything is self-consistent, so all 132 checks passed over it, every scenario worked, and
only a measurement *repeated inside one process* could see it. It also survives `PYTHONHASHSEED=0`, because
the varying thing is the id strings, not the hash function.

**⚠ Every performance number in these docs was taken under it.** They are now stable and were re-measured;
the claims all survive, the figures moved:

| claim | recorded | now (identical across 3 runs) |
|---|---|---|
| §5d guided vs blind | 3 vs 55 | **2 vs 67** |
| §5k paths / without / blind | 3 / 5–10 / 5–10 | **3 / 10 / 10** |

**⚠ And it corrects §5k's explanation of its own controls.** That section attributed the two controls
"straddling each other run to run" to band-4 being unreachable, leaving the search "tie-broken by frontier
insertion order". The first half is right and is the finding; the second half named the mechanism without
noticing that *insertion order was not stable*. The controls now sit still at 10 and 10, which is the
stronger version of the same claim.

**⭐ The apparent capability wall was an artifact.** Before the fix, towers of 5+ blocks looked unsolvable
(budget-exhausted at 400 imagined states) and 4 blocks cost 11 — which read as a plateau in greedy
best-first and nearly bought a redesign of `driver.relevance` around deleted preconditions. With the order
stable, the guidance is **optimal**: n blocks costs n−1 imagined states, with no search at all.

```
3 blocks -> 2 imagined   5 blocks -> 4 imagined
4 blocks -> 3 imagined   6 blocks -> 5 imagined
```

**The fix** is to return the traversal order rather than to sort — the order is a *fact about the graph*
and was already deterministic; only the container threw it away. `reachable` returns a dict used as an
ordered set (membership stays O(1) for the callers that only ask `in`), and `step` dedupes with
`dict.fromkeys`. `types.instances` and `intake` also consume `reachable` and were silently order-unstable
too; both are now stable for free.

`check_the_copy_order_is_a_fact_about_the_graph_not_about_node_ids` builds one world twice in a process and
compares. **Vacuity guard: it asserts the two builds really do get different ids**, or stable order would
prove nothing. Planted-bug probe run per §7 — restoring the `set` turns `COPY_ORDER_IS_STABLE` and
`AND_SO_IS_THE_SEARCH` red while `the_search_still_succeeds` stays green, which is the defect's signature
in one line.

> **A deterministic computation that ends in a `set` has an undeclared tie-break in it.** Anywhere order
> reaches a ranking, a frontier, or a "first match", that tie-break is load-bearing and nobody declared it.

### What the System 1 question actually measured

The prompting question is answered, and the answer is **not yet, and the first lever is not System 1**:

| | proposals at root | ms/enumeration | imagined |
|---|---|---|---|
| 3 blocks | 12 | 0.65 | 2 |
| 3 blocks + 200 inert nodes | 12 | **37.2** | 2 |
| 3 blocks + 100 extra operators | 312 | 37.4 | 2 |

`proposals` runs `is_a` over every mapping × every parameter, so **world content that can bind to nothing
still costs**: 200 inert nodes bought a 57× enumeration cost and *zero* extra proposals. That is the
System-1-shaped problem (bounded neighbourhood instead of whole-frame scan) — but `thread_and_system1.md`
§5b already names a cheaper lever for exactly it: **index declared types by their required labels**, so a
node with no `wheel` edge is never tested against `car`. Do that first and re-measure; System 1 is still
waiting on a threshold that has not arrived.

## 5m. The enumeration cost — and the named lever was aimed at the wrong thing (2026-07-31)

§5l ended by recommending `thread_and_system1.md` §5b's lever (index declared types by required labels).
**Profiling first showed that lever would not have touched the measured cost**, which is worth recording
because the reasoning was plausible and wrong for a reason that generalises. 134 checks, 0 FAILED.

**Where the cost actually was.** `types.find_type` and `function.find` scanned `g.nodes` — materialising a
tuple of *every node in the graph* — on every lookup, and `violations` reached `find_type` **four times per
call** (itself, `schema_of`, `attrs_of`, plus a hop per `base`). One `driver.proposals` enumeration over a
world with 200 nodes that can bind to nothing:

```
21,525 find_type calls        0.321s cumulative   \  out of ~0.47s in violations
21,575 g.nodes tuple builds   0.112s tottime      /
```

**⭐ So the cost was never in *testing candidates* — it was in *looking the type up by name*, once per
test.** The named lever skips hopeless tests, and would have left four whole-graph scans inside each
surviving one. ⚠ And it would not have applied here at all: it keys on required *labels*, and
`clear_block` is `{kind_of: block, clear: True}` — **no required labels whatsoever**. The lever was written
from `car`-needs-`wheel` and silently assumed schemas are structural.

**Two fixes, both structural, neither a heuristic.**

1. **`Graph.of_kind`** — a kind index maintained by `mint` and `drop`. **⭐ This is the same shape as `inc`
   and legitimate for the same reason: the SUBSTRATE maintains it on the only operation that can create a
   kind, so it cannot drift.** Contrast `types.tag`, whose `is_a` stamp is a *claim a rule made* and so must
   be re-validated on read (§5i). Same word, opposite status — worth keeping the two straight. `put` now
   **refuses** to change `kind` rather than maintaining machinery for a case that should not exist
   (`_copy_set` already excluded `kind` as "positional").
2. **`violations` resolves the name once** — `_schema_at`/`_attrs_at` take the type *node*, so a caller
   that has already resolved a name does not resolve it three more times.

| | before | after |
|---|---|---|
| 3 blocks, enumeration | 0.65 ms | **0.37 ms** |
| + 200 inert nodes | 37.2 ms | **7.95 ms** |
| + 100 extra operators | 37.4 ms | **7.86 ms** |
| `../pystrider`'s 143 pins | 91.5 s | **32.1 s** |

`check_the_kind_index_cannot_disagree_with_a_scan` guards it — a hand-maintained index is exactly the kind
of discipline a test earns its place on. **Vacuity guard: it exercises `drop` and `rollback`**, since a
write-only index passes any test that never removes anything. Planted-bug probes per §7: a `drop` that
leaves a stale entry, and a permissive `put`, each turn distinct keys red.

**Then the residue turned out to be loop-invariant work, not candidate testing either.** With `of_kind` in,
profiling again put the cost in the 5,125 `violations` calls — but the waste *inside* them was that
`_schema_at`/`_attrs_at` rebuild the same type's requirement dicts **once per candidate**. Resolving a name
and walking its `base` chain depends only on the type. So `types.requirements` gathers `(schema, attrs)`
once and `types.fails` tests against them; `violations` is now those two composed, so there is **one
implementation and nothing that can disagree** — no test needed, which is the structural answer rather than
a guarded one. `driver.proposals` hoists it per parameter.

⚠ **`requirements` is deliberately NOT a cache.** Nothing is stored, so nothing can drift; it is the same
answer `schema_of`/`attrs_of` give, computed where it is still valid to hoist. A caller that mutates a type
mid-loop must re-ask — the honest contract, where a cache would have to guess.

| enumeration | at §5l | after `of_kind` | after hoisting | total |
|---|---|---|---|---|
| 3 blocks | 0.65 ms | 0.37 ms | **0.26 ms** | 2.5× |
| + 200 inert nodes | 37.2 ms | 7.95 ms | **2.08 ms** | **17.9×** |
| + 100 extra operators | 37.4 ms | 7.86 ms | **6.2 ms** | 6× |
| `../pystrider`'s 143 pins | 91.5 s | 32.1 s | **27.3 s** | 3.4× |

⚠ One reading was **noise**: the 100-operator row first measured 9.15 ms and looked like a regression from
hoisting. Repeated, it is 6.1–6.5. Single timings are not measurements — the §5l lesson applies to its own
follow-up. What remains in that row is library size (100 functions × `load` + `param_types`), which is a
different axis from world size and untouched by any of this.

**Still not System 1, and the case is now much weaker.** Inert world content costs ~8× baseline enumeration,
down from ~57×. `proposals` does still test every mapping against every parameter type, which is the
System-1-shaped residue — but it is 2 ms. Re-measure before building §§2–4; the threshold has moved further
away, not closer.

> **Profile before choosing a lever, even one you wrote down yourself after measuring.** §5l's measurement
> was right that enumeration was the cost; the *inference* about which part was a guess, and it named a fix
> that did not apply to its own benchmark.

## 5n. Deliberation — DESIGNED, not built (2026-07-31)

`docs/microfunctions/deliberation.md`. Out of a design conversation, not a probe — **nothing in it is
measured**, which is worth flagging given how consistently measurement has weakened claims here.

**The one architectural change it turns on:** `pursue` is a closed loop with no yield point, and
`pursue`/`carry_out` are Python, never reachable from the ISA — checked. So deliberation is the thing the
system computes *with* and cannot compute *about*. ⭐ **The same defect in its third incarnation**, after
attention (fixed by `thread.py`) and the goal (fixed by `goal.py`, whose docstring names the pattern).

Everything else follows: five verbs (`EXPAND`/`DECOMPOSE`/`COMMIT`/`SENSE`/`REFUSE`), and guidelines,
methods, procedures and stop-and-act become four *kinds of decision* rather than four features.

**⭐⭐ The distinction the doc exists for: force is about FAILURE, not strength.** A **method** that does not
fit falls back to search; a **procedure** that does not fit must `REFUSE`, because for compliance "no plan
found" beats "found a plan another way". That inverts every existing reflex — `carry_out` replans,
`recover` tries contingencies. It cannot be inferred from content and must be declared.

**⚠ Frequency is the thing most likely to be got wrong.** Methods per goal (few, may be expensive);
stop-rules per search step (hundreds, must be structural); guidelines per proposal (thousands, must be a
pure ranker — and that is the existing `rank=` hook, so guidelines need *no new mechanism* and are the
cheapest slice).

**Prior art survives the code deletion, and should be read before re-deriving:**
`docs/design/procedures_design.md` §3 is a *stepping bank* — the yield point, built and green in the old
engine — and `docs/units/goal_machinery.md` §8 is "a subgoal with its own condition", also built. Expect
§5j's outcome: the findings transfer, the mechanism probably does not.

**First slice, deliberately inert:** steppable search plus a `decide()` that always returns `EXPAND` —
zero behaviour change, verified by the existing 134 checks and by the search staying deterministic.

## 5o. Deliberation slice 1 — the seam, inert (2026-07-31)

`driver.pursue(..., decide=...)` plus the five verbs. 135 checks, 0 FAILED, default path identical, search
still deterministic. `deliberation.md` §11 has the detail.

**⚠ The vacuity guard is the whole test, and it is the point of the slice.** A seam nothing can steer is
indistinguishable from no seam, and would pass any check asserting only "default behaviour unchanged" —
precisely the false green §7 keeps catching. So `check_the_deliberation_seam_is_inert_by_default_and_live_when_used`
requires **both**: identical by default, *and* a decision really diverting the search. Planted-bug probe: a
`pursue` that consults `decide` and discards the answer fails it.

⚠ **And the check caught a mistake in its own author.** `AND_IT_REACHES_THE_THREAD` was silently `False`
because it read `g.attr(entry, "why")` — but `why` is an edge property of the *transition* and must be read
through `thread.why`. Exactly the §5g failure mode, landing on the person who wrote §5g's fix.

**`decide` is a participant, so it gets the real thing** — the opposite of `trace`, which gets labels
because a watcher must not be able to steer. Same reasoning, opposite conclusion; the two must not be made
to look alike. Built only from what the frontier item already carries, per `deliberation.md` §4.

**Unbuilt verbs raise and name what is missing** (`DECOMPOSE` → goal hierarchy, `SENSE` → ignorance) rather
than being ignored. ⚠ Not done: the search is not *externally* steppable — no resumable generator — and
nothing yet executes the prefix `COMMIT` hands back.

**⭐⭐ And a standing principle was stated: MICROFUNCTIONS SHIP WITH THE ENGINE.** They are *how the engine
works*, not user-definable; everything a domain contributes is **data**. That collapses the four-surfaces
worry (`asm.py` becomes internal) and narrows the LLM border in the safe direction. ⚠ **It is in tension
with `north_star.md` ("rules become microfunctions"), `function.py` ("a rule is a function"), `asm.py`
being documented as the LLM border, `../pystrider` authoring `.mf`, and §5k's `INVOKE` surface added
expressly to help them.** The unsettled question is where *domain actions* sit; `deliberation.md` §12 works
it through and proposes the line at **knowledge versus capability**.

## 5p. Deliberation slice 2 — guidelines, as data (2026-08-01)

`microfunctions/guideline.py`. 136 checks, 0 FAILED. `prefer`/`avoid` are **nodes an author writes**; the
*ranker* that reads them ships with the engine and drops into the existing `pursue(rank=...)` hook, so the
driver needed no change at all.

**⭐⭐ The property that makes advice safe to accept: `avoid` means LATER, never NEVER.** The decisive case
is Sussman's anomaly reused as a contrast — §5e already shows that *forbidding* `unstack` turns it honestly
unsolvable, so **avoiding** `unstack` must leave it solved. It does, by the very move that was avoided.

**⭐⭐ AND THE PLANTED-BUG PROBE TAUGHT MORE THAN THE CHECK.** A ranker rigged to return `-999` for every
avoided call — advice behaving as an outright *filter* — **still solved the anomaly.** So *"advice cannot
exclude" is a guarantee of `pursue`'s architecture, not of `guideline.py`*: the frontier only ever
**orders**, so no score however low puts a move out of reach. That is precisely why authored advice is safe
to accept at all, and it means the check *demonstrates* the property rather than enforcing it. What
`guideline.py` must get right on its own is the **band**.

**⚠ Bands are the real invariant.** The composed score is `band + offset`, `offset` in `[0, 1)`, so
`rank >= 4` keeps meaning exactly what the driver requires. Band 4 is derived from the function's own body;
a guideline is an author's opinion. Letting the weaker evidence beat the stronger is how authored advice
makes a system dumber than it was. ⚠ The fraction is **an encoding of an order, not a weight** — nothing
here is tunable, and precedence among guidelines is *declaration order*, free via `of_kind`'s mint order.

**⚠ Two versions of this check were vacuous before it bit.** First, advising per *function* put every
proposal in a band on the same side, so within-band reordering could not be observed at all — advising on a
**node** (`prefer(on=c)`, "settle the base first") is what puts two differently-advised proposals in one
band. Second, the band test used only `prefer`, so the avoided tier was never exercised and a planted
band-crossing bug passed. Both found by probing, neither by the green.

**⭐⭐ And the two-level architecture was settled** (`deliberation.md` §12): *"rules become microfunctions"*
means an action like `stack` is **data**, executed by an **interpreter microfunction that ships with the
engine** — not the full ISA as data, only business-model operations (mint, get/set attr, link/unlink over
paths), never privileged ISA. ⭐ **This makes `establishes` EXACT**: every one of its six `unknown` cases is
an artefact of reading a general-purpose ISA, and a closed branch-free vocabulary has none of them, so band
4 becomes reliably reachable. §5k's role-**paths** become the native form rather than something recovered
from register provenance. ⚠ The risk is vocabulary creep — `stack` already needs `height + 1` — so the
stopping rule is stated: **action data says what changes and has no control flow; branching lives in
decision rules; repetition lives in the loop.**

## 5q. Deliberation slice 3 — goals gain a hierarchy (2026-08-01)

137 checks, 0 FAILED. `open_goal(..., under=, because=)` plus `parent_of`, `subgoals`, `ancestry`,
`within`, `depth_of`, `decomposed`, `subgoals_met`. This is what `DECOMPOSE` had nothing to post into and
what a decision rule had no context to key on.

**⭐ The child points at the PARENT.** Ancestry — *"am I inside a `y`?"*, the question a rule asks — is then
a walk up a path, while children stay O(1) through the reverse index. Same decision as `thread.py`'s `prev`,
for the same reasons, and it keeps the metadata direction invariant.

**⭐ A cycle is structurally impossible**, because parentage is set at mint and never changed — a fresh node
cannot already be its own ancestor. Same shape as `Graph.of_kind` being an index rather than a cache. ⚠ That
bounds cycles, **not depth**: recursive decomposition mints a fresh goal each time, so the chain grows
without looping and `depth_of` is what a termination bound must read.

**⭐⭐ And the prior art paid for itself immediately.** `docs/units/goal_machinery.md` §8 records that a
parent's "all my children are done" guard was written as an **absence** — no subgoal that is unmet — and was
therefore **vacuously true before any subgoal had been minted**: an undecomposed goal read as trivially
achieved. Generalised there as *don't trust an open-ended absence without an explicit closure fact*. That
trap is now guarded (`decomposed`, and `subgoals_met` returning False when undecomposed) and planted-bug
probed. ⚠ Note `satisfied` already applied the identical rule one level down via `bool(cs)` — **the same
mistake was available in two places and had only been fixed in one.**

**⚠ `subgoals_met` is a READER, not the definition of a parent's satisfaction.** Whether a parent counts as
met when its children are is a *policy* belonging to whatever raised them — a method may decompose into
steps that jointly achieve it, or into checks that merely support it. Deciding that here would settle it for
every future method at the moment it is least clear which is wanted.

**⭐ Also recovered from §8, and it shapes what comes next:** *"goal/subgoal turned out to be the shape
everything else in this arc reduces to — a procedure is this shape plus one sequencing edge, a question is
this shape wanting a knowledge-claim instead of a world-state claim."* If that transfers, **procedures are
much closer than the design assumed**, and `SENSE` (§8 of `deliberation.md`) is a goal wanting a knowledge
claim rather than a new mechanism.

## 5r. Deliberation slice 4 — methods and procedures (2026-08-01)

138 checks, 0 FAILED. `goal.then`/`sequence`, `BY_STEPS`, `ADVISORY`/`MANDATORY`, and `driver.follow`.

**⭐ Probed §8's claim before building on it, and it substantially held** — the first claim in this project
lately that survived contact roughly intact. *"A procedure is this shape plus one sequencing edge"*: two
ordered subgoals ran through the existing `carry_out` **unchanged**, in order, and reality came out right.
Structure was not the gap.

**Two things the probe found that the claim did not mention:**

1. **Nothing walked the order** — the gap was *drive*, not structure. `driver.follow` is that walk, and it
   is deliberately thin because everything underneath already worked.
2. **⭐ A procedure's parent has no world constraints of its own.** *"Do these steps, in this order"* is the
   whole of it — so `satisfied`, which only ever read constraints, called a perfectly completed procedure
   **unsatisfied**. Hence `BY_STEPS`: for a procedure, having followed the steps *is* being met. §8's third
   variant (a goal wanting a *knowledge* claim) is the same move a third time, and is `SENSE`'s shape.

**⭐⭐ FORCE decides what happens on failure, and that is the whole method/procedure distinction.**
`ADVISORY` falls back to searching for the parent goal; `MANDATORY` **refuses**. ⚠ For a procedure *"could
not do it"* is a better answer than *"did it another way"* — which inverts every other reflex in `driver`,
where `carry_out` replans and `recover` reaches for contingencies. The check builds the two
**structurally identically apart from the declared force** and requires them to behave oppositely; three
planted-bug probes (all-advisory, all-mandatory, `satisfied` ignoring `BY_STEPS`) each turn distinct keys
red.

⚠ **A refusal is not a failed search** and they are reported differently: one says the world would not
permit it, the other that we were not permitted to try. ⚠ **Advisory fallback cannot resurrect a MANDATORY
parent** — force is read from the parent whose decomposition it is, never from the step that failed, or a
mandatory procedure containing an advisory sub-method would become improvisable one level down.

⚠ **`met_by` and `force` are DECLARED, not inferred.** Structure *almost* entails `met_by` (no constraints
plus ordered children looks like a procedure) but a goal may legitimately have both, and both are
statements of authorial intent rather than facts about the graph.

**Still to come:** methods as *data* that select themselves (today a decomposition is built by hand, so
nothing yet matches a method to a goal), and `SENSE`.

## 5s. Methods as data that select themselves (2026-08-01)

`microfunctions/method.py` + `driver.attempt`. 139 checks, 0 FAILED. Closes slice 4: an author no longer
assembles subgoals by hand.

**⭐ Context is STRUCTURAL, which was the open question.** A method is generic and cannot name an individual
ancestor goal — and letting authors unroll context into position-specific methods is the labelling error
`goal.ancestry` exists to prevent. The answer: a subgoal **points at the method that raised it**, so
*"within a goal raised by M"* is an ordinary walk up the ancestry asking a structural question. No strings,
no goal taxonomy, and it works under recursion.

**⭐ `attempt` is the GOAL-level decision point, deliberately not inside the search loop** — `deliberation.md`
§4's frequency rule. Methods are consulted once per goal (few, may be expensive); the per-step `decide` hook
runs hundreds of times and must stay structural. Method matching in the inner loop would invert the cost of
the thing it saves, which is the mistake §5m records paying for once already.

**⚠⚠ THE BUG WORTH REMEMBERING: a method is a ROUTE, not a REDEFINITION.** The first `decompose` stamped
`met_by=BY_STEPS` on every goal it decomposed. So a goal with real world constraints stopped being judged by
them — and when the advisory method then failed and `follow` fell back to searching for that same goal, the
goal could no longer be satisfied *by any route*, because its criterion had been rewritten to "my steps are
done" and its steps were the ones that had just failed. **The decomposition silently destroyed the escape
hatch that makes authority safe.** Fixed by rewriting the grounding only when there is nothing to rewrite:
a goal with its own constraints keeps them; a goal with none is a procedure.

**⚠ The completeness guard is the key that matters.** A method prunes by *replacing* enumeration — the
exponential win, and why it cannot be a ranker — so a wrong or non-covering one could make a reachable goal
**unreachable**, a failure mode nothing else here has (`guideline.py` can only reorder; `forbid_action`
prunes on a proof). Checked directly: a goal solvable by search **stays solvable** when a method that
mishandles it is declared.

**⚠ And a second vacuous check caught by probing, not by the green.** The context test's negative case used
a goal whose constraint was a *different sort*, so the mismatch was decided by sort and the context
condition was never exercised — a `under_method` rigged to return `True` always still passed. The two cases
must differ **only** in context.

## 5t. The border, extended to everything a domain contributes (2026-08-01)

`intake.py` restructured. 140 checks, 0 FAILED. One block grammar, three families:

| verb | produces |
|---|---|
| `goal` / `ask` / `why` | a goal — same body, different thing done with it |
| `prefer` / `avoid` | a **guideline** |
| `method` / `procedure` | a **method**, advisory or mandatory |

**⭐⭐ Why this and not `SENSE` first: the standing principle was STATED AND UNENFORCED.** Microfunctions
ship with the engine and everything a domain contributes is data — but the border existed for **goals
alone**, so a guideline or a method could only be authored by calling Python. That is exactly the "reach
past the surface and write graph structure" this module's own docstring says must never happen, because
then nothing can refuse it. A gap between what the docs say and what is true.

**⭐ It was one parser, not a fourth.** The four-surfaces worry collapsed when `asm.py` became internal, so
this extends the existing `<verb> <label>:` block rather than adding a grammar.

**⭐ A step's grammar is the GOAL grammar with roles instead of names.** `step subject on object`,
`step object.clear = true`. The only legal subjects are `subject` and `object` — the matched constraint's —
and a step naming an individual is **refused**, because a method that named one could not be reused. Same
reason `types.py` refuses to let a schema name a target.

**⚠ `method` and `procedure` have identical bodies and differ only in force**, so the surface makes the
author say which word they mean rather than inferring what cannot be inferred.

**⭐ Refusal now leaves nothing behind via the JOURNAL.** The old path dropped constraints by hand, which
had to be kept in step with everything a body could mint. `savepoint`/`rollback` is what the journal was
built for, and this is **its first consumer outside `selftest.py`** — which answers §6's standing note that
it should be deleted if nothing used it. ⚠ Transactional only: nothing between savepoint and rollback may
`commit`.

**⚠ `describe` now refuses what it cannot render.** Handed a guideline it used to emit `goal <label>:` with
an empty body — well-formed, wrong, and exactly the "best effort" this module exists to prevent. A round
trip a model checks itself against must not be able to lie.

**The key that carries the check is END TO END**: a method *authored as text* decomposes a goal authored as
text and changes the real world. A parser producing nodes nobody uses would satisfy every structural
assertion. Planted-bug probes: disabling `rollback`, and dropping the closure checks, each turn keys red.
⚠ The first probe attempt **failed to plant anything** — it wrapped `read`, whose own rollback still ran —
which is the fifth time this session a probe caught a check or a probe being vacuous.

## 5u. Ignorance, and SENSE — the last capability gap (2026-08-01)

`graph.UNKNOWN`, `goal.require_known` / `undetermined` / `blocked_on_ignorance`, the `a.k known` surface
form. 141 checks, 0 FAILED.

**⭐⭐ NOT LOOKED, as distinct from NOT THERE.** The engine already performed information-gathering actions
but could only model them as world-*changing* ones — `scan_dir`'s mock mints file nodes, as though scanning
**created** files rather than revealing them. Underneath was a substrate limit: an attribute was present or
absent and absence meant *lacks it*. So the system could not tell *"make p true"* from *"find out whether
p"*, an information-gathering subgoal had nothing to close, and `pursue` reported failure identically
whether **no plan exists** or **no plan exists given what I know** — though only the second warrants going
and finding out.

**⭐ The fix rode on §5d rather than adding a planner.** A goal naming *which* constraints are false lets
the driver ask what could close them; one separating **false** from **unknown** lets it reach for a sensing
action. `undetermined` is that separation, and `require_known` is §8's third variant of the goal shape — *a
question is this shape wanting a knowledge claim* — after `BY_CONSTRAINTS` and `BY_STEPS`.

**⚠ Explicit ignorance only.** Absence still means *lacks it*; a slot is unknown only when something says
so. Treating every absence as ignorance would make the whole graph unknown and every constraint
undecidable — and would be untrue, since most absences really are knowledge.

**⚠ Attribute slots only, recorded rather than worked around.** An absent *edge* has nowhere to hang a
marker — no slot to write on — the same substrate limit that makes an edge property unaddressable.

**⚠ `blocked_on_ignorance` requires BOTTOMING OUT in ignorance, not touching it.** A goal with one unknown
slot and three false constraints still has world work to do; sensing on a mere touch makes the system look
in every box.

**Two bugs, both caught by something other than the green.**

1. `require_known` passed `subject` as a keyword to `_constrain`, making it a stored *string* rather than
   an edge — so `g.target(c, "subject")` was `None`, `holds` looked at nothing, and **a knowledge goal
   closed itself before anyone had looked**. Caught by `describe` rendering it as "something.colour", which
   is the round trip earning its keep.
2. The check's ignorance *contrasts* were evaluated in the return dict, **after** `carry_out` had already
   made the slot known — so they passed regardless. A planted bug proved they tested nothing. Sixth vacuity
   caught by probing this session.

**`SENSE` is no longer unbuilt**, and `DECOMPOSE`'s refusal message was corrected: it does not raise for
want of a goal hierarchy (that exists) but because a method applies **per goal** via `driver.attempt`, never
per search step. Frequency, not absence.

## 5v. ⭐⭐ One reference language, and types that use it (2026-08-01)

**150 checks, 0 FAILED.** New module `path.py`; `types.py` widened; `type` is the eighth CNL verb;
two consumer-reported defects fixed (§9, §10 of `../pystrider/docs/feedback_microfunctions.md`); `CHANGELOG.md`.

**⭐⭐ The reference language already existed, three times, and that is why schemas were flat.**
`driver.role_node` had a private regex resolving `c.right` and `c.child[2]`; `intake._constrain` split
`b.clear` by hand on the first dot; `establishes` emitted dotted roles and nothing said what one *was*.
Three copies of an unwritten grammar is the shape a missing module makes, and the cost was not duplication
— it was that **no other part of the surface could refer to anything more than one hop away**. The
one-level schema limit was downstream of a missing module, not a decision about types.

`path.py` is that grammar, once: `seg ('.' seg)*`, `seg := ['^'] label ('[' int ']')?`. Nothing counts
hops, so depth was never the hard part.

**⭐⭐ The last segment is an attribute or a node according to what the POSITION demands** — `==` compares
values, `is` compares identities, so `value_at` reads the last segment as an attribute and `node_at` walks
it as an edge. ⚠ The tempting alternative — *follow the edge if there is one, else read the attribute* —
would make a written path mean whatever the world happens to contain when it is read, so adding an edge
could silently change what an old declaration said. That is this codebase's standing drift class
(`types.tag`, the kind index). **Nothing in `path.py` consults the graph to decide what a path MEANS**,
only to find what it denotes.

**Types gained three things, all ordinary graph data:** `Req(type=…)` recurses into the target's own
schema (⚠ coinductively, so `person.friend: person` terminates on two mutual friends); counts became
ranges; `AttrReq` carries a comparison. And **`Rel` relates two places inside one subgraph** —
`wheel[0].pressure == wheel[1].pressure` — which is the demand a per-label requirement structurally cannot
express, and which §5k's "left alone, deliberately" argued was correctly out of scope. That argument was
right about the limit and wrong about keeping it.

**⚠ `subsumes` stopped being dict equality and had to.** Once a demand is a range, a subtype narrowing its
base's range must still subsume, or every widened type would stop subsuming itself and `function.producers`
would quietly lose candidates. Undecidable cases (`!=`, unordered values) answer **False** on purpose: a
lost candidate is recoverable, an unsound one is not.

**⭐⭐ The composition review found a live silent defect, which is the argument for doing it.**
`a.wheel[1].pressure = 3` in a goal split on the first dot and built a constraint about an attribute
literally named `wheel[1].pressure` — unmeetable, and `describe_constraint` rendered it back looking
correct, so the round trip *lied*. It is refused now. ⚠ **And refused rather than supported, for a reason
worth keeping:** `conflict.unsatisfiable` keys a contended slot by `(subject, key)` and would read two
wheels' pressures as one slot (a contradiction reported where there is none — the unsound direction);
`goal.holds`, `goal.undetermined` and `query.refutes` all read the attribute off the base node. A type schema has neither problem **because it only ever
checks**. Depth is available where it is correct, refused loudly where the machinery behind it has not
caught up, and the boundary is a table in `intake.py`'s docstring rather than folklore.

**Next, if this is picked up:** teach `conflict.unsatisfiable`, `goal.holds`/`undetermined` and
`query.refutes` a navigated subject, then the goal and method rows of that table open up.
`driver.relevance` would also rank a navigated goal constraint at band 4 instead of 3, since `establishes`
already speaks in the same paths — that is the interesting half.

## 5w. The second consumer round — two real defects, and a CHANGELOG we owed (2026-08-01)

`../pystrider/docs/feedback_microfunctions.md`, re-read after §5v landed. §1–§4, §6–§8 were already worked
through in §5k. Three items were live.

**⭐⭐ §10 — a write through an unset register minted an edge whose target was `None`.** `regs.get` answers
`None` for a register a `GET` never filled, which is an *ordinary* case the moment a part of the input can
be missing, and `g.link` appended it. `targets` then came back non-empty, so every "is this part present?"
test answered **yes**, and the `None` was handed on as though it were a node — surfacing arbitrarily far
from the instruction that caused it. **It converts a MISSING part into a PRESENT-BUT-NULL one**, which
destroys a distinction sitting one underneath `graph.UNKNOWN`'s: *no part* versus *a part that is nothing*.
Now refused at the write ops in `isa._step`, naming opcode and operand — their suggestion, and right:
this layer knows the operand, the substrate would only know something passed it a `None`. `run` already
rolls back on any exception, so a refusal leaves nothing behind.

**⭐ §9 — a declared parameter type was enforced only by `driver.proposals`.** They carried a safety
property entirely in a signature and had documented it as *"the unsafe app is unbuildable"* when it was
only ever *"no plan builds it"*. `function.invoke` now checks, with `check_types=False` as the opt-out.
⚠ An **undeclared** parameter type refuses too, because `proposals` already treats one as satisfiable by
nothing — allowing it here would recreate exactly the divergence being closed. Their `CHECK`-as-first-
instruction workaround can go; it was the "declared type and enforced type kept in step by hand" shape.

**⭐ §11 — and this one was our fault, made this session.** `types.attrs_of` changed return shape
mid-session (a bare value became `AttrReq`) while they were working against it, and from outside there is
no way to tell *"upstream grew a capability"* from *"we broke something"* without bisecting. `CHANGELOG.md`
now exists, with the rule stated in it: **every change to what a public function returns or accepts gets a
line on the day it happens**, release or not.

**⭐ §5 is answered rather than fixed, and worth telling them.** They recorded — *as a non-defect* — that
they could not build recognition on `types.py` because a schema constrains each label independently and so
can never say "the `body` and the `element` are related this way". §5v's `Rel` says exactly that. Their
`recognizes` still carries joins we do not (theirs are read off function bodies, ours off declared data),
so the two stay complementary; but the specific thing they said a schema structurally could not express,
it now can.

## 5x. WHERE / WHEN / WHAT — probed against the closed class, not argued (2026-08-01)

**The question, from the user:** the CNL must not only *describe* but *drive*, and `why`/`where`/`when`/
`what` are fundamental — **about the world**, so a built-in KB is legitimate; what has to be justified is
the **machinery** underneath it, in the sense of language's ~50-element **closed class**
(`docs/units/closed_class_inventory.md`).

⚠ **The framing matters and I had it wrong twice.** First I mapped these to engine *introspection*
("when did **we** touch this" → `thread.last_touching`); they are about the world ("when did it
**happen**"). Then I treated a built-in KB as a violation of *everything a domain contributes is data*; it
is not. **Content shipping with the engine is fine. Machinery shipping with the engine has to earn it.**
The test is the standing one — `baroque-vs-fundamental`, and `causation-core-was-sugar`'s lesson: probe
first, because a whole conceptual core once turned out to be sugar.

**So it was probed, not argued** (scratchpad, blocks below are the measured output).

**`what` — already machinery, no surface.** `types.recognize` is the world question *what kind of thing is
this*, structural and bottom-up. The split is already clean: classification is machinery, the kinds are
data. Needs a verb, nothing else.

**`when` — sugar, and it became sugar THIS MORNING.** Ordering and interval containment over a comparable
value is the closed-class residue, and §5v built exactly that: `arrived between 0 and 6` and
`arrived < next.arrived` (a `Rel` between two paths) both hold, measured. Allen's interval relations
(before / during / overlaps / meets) reduce to comparisons on two endpoints, so they are sugar too. What is
left is *vocabulary* — a conventional `time` attribute — which is content, and content may ship.

**⭐⭐ `where` — NOT sugar. The residue is TRANSITIVE CLOSURE, and it is genuinely absent.** Measured three
ways on a parcel nested inside a box inside a warehouse:

* a fixed-depth type cannot reach it (a path is a fixed sequence of hops — nothing counts them, but nothing
  repeats them either);
* a goal link constraint `wh contains parcel` is **false**, because the parcel is not a direct target;
* the path grammar has no repetition operator at all.

⭐ **And this corroborates `closed_class_rechallenged.md` from a completely different direction.** That
document probed five relational forms and found four pure sugar — causation, quantification's open case,
force/level, identity/merge — with **transitivity the one that needed a real engine extension**. Arriving
at the same single item by walking backwards from "what does *where* need" is the strongest evidence
available here that it is a genuine closed-class member rather than a convenience.

**⭐ So the item to build is not `where`; it is transitive closure over a named edge.** Domain-neutral, and
one primitive serves containment, ancestry, part-of, dependency and reachability at once. `where` then
becomes a **built-in KB** — a `contains` edge plus a small type library, authored in the ordinary surface —
which is the legitimate kind of shipping-with-the-engine.

**⚠ The real design problem, which is not the parser.** Closure makes a path **multi-valued**, and
`path.py` is built on single-node resolution (`node_at` returns one node or `None`, and `_step` already
refuses to guess between two backward sources). Two positions, very different costs:

* **predicate position** — *is X reachable from Y via `contains`?* Stays boolean, stays single-valued,
  breaks no contract, and answers "where is it" completely. Needs cycle protection, for which the
  coinductive discipline in `types._target_ok` is the precedent.
* **reference position** — `a.contains+.label` denotes a *set*, which breaks `node_at`'s contract and
  every caller that assumes one node.

**Recommendation: predicate position first.** Small, closed, checkable, and it does not force a decision
about multi-valued references that nothing yet needs.

**⚠ Two silent acceptances the probe caught in §5v's own work**, both fixed and pinned
(`check_the_reference_language_refuses_what_it_cannot_express`): `path.parse("contains*")` *succeeded*,
yielding a label literally named `contains*` that would match nothing forever — the person writing it is
reaching for closure, and a never-matching label is the worst possible answer; and `has 1 ^contains`
accepted `^contains` as a plain edge label, counting the targets of an edge nobody has. Same class as the
mis-parse §5v records. **A probe of "is this sugar?" found two defects in the thing being probed**, which
is the argument for probing rather than reasoning.

**Not yet surfaced, and deliberately:** `plan` / `replan` / `do`. Verified — `pursue` and `carry_out`
appear nowhere in `isa.py`, `dispatch.py`, `function.py` or `asm.py`, so planning is not reachable from a
microfunction at all. A control verb today would be a surface saying what the machinery cannot honour,
which is precisely §5v's defect. `deliberation.md` records why it is not mere plumbing: `pursue` is a
closed loop with no yield point, so deliberation is the third thing the system computes *with* and cannot
compute *about*. **Steppable search is the prerequisite**, and it was already the listed one.

## 5y. DECISION — builtins are not policed, and the risk is accepted (2026-08-01)

**Decided by the user, after the objection below was raised and answered.** Recorded here rather than left
implicit, because "we chose not to guard this" is exactly the kind of thing that becomes an invisible
assumption and then reads later as an oversight.

**The finding that reframed it: there is no boundary to relax.** `microfunctions/` has **no privilege
mechanism at all** — no privileged/trusted/builtin distinction anywhere in the package, and `asm` accepts
every opcode in `isa.__all__` from any `.mf` file it loads. The "two levels" of `deliberation.md` §12 are
entirely **de facto**: `pursue` happens to be Python and happens not to be exposed. So exposing deliberation
is **additive work**, not the lifting of a restriction.

**The objection, for the record.** Because there is no privilege mechanism, making deliberation callable
from the ISA makes it callable *by domain data too*. `metaprocedure-model-defined` identified **load-time
rule-authoring privilege** as one of two independent gaps in the *old* engine; it was never carried over,
and this is that gap arriving again with more at stake.

**The decision: do not police it. Accept that an author can reach privileged machinery. For now.**

**Why that is defensible, not merely expedient.** `composability-principle` is the standing foundation:
*reflexive mechanisms must combine on ONE substrate; hardcoding = an unreachable island.* A Python-only
`pursue` **is** that island, and the homoiconicity claim — the thing argued to be the real edge over a
language model — is that a rule can write a rule. If deliberation is Python, the system cannot reason about
its own deliberating, which is the capability the architecture exists to buy. Policing first would mean
building the guard before the thing being guarded, and this project's standing advice runs the other way:
probe first, and delete aggressively.

**⚠ What to revisit it on, so "for now" has a trigger rather than being forever:**

* the moment a `.mf` file that the engine did not ship is loaded from an untrusted source;
* the moment a domain author's mistake (not malice) reaches deliberation and produces a failure that is
  hard to attribute — that is the cheap early warning, and it will arrive before any adversarial case;
* if `establishes` stops being exact because machinery entered the **action** population. That payoff is
  the measured reason the two-level split existed, and it survives only while builtins are never
  *proposed*. Keep that structural — an action is something `proposals` can bind arguments to — rather
  than a flag. `labelling-error-and-when-tests-earn-their-place`: the workbench fix was **not scanning**,
  not a filter, and no marker was needed once isolation was structural.

**⚠ And one cost that stops being theoretical.** §6 lists termination as open with `MAX_STEPS` an "honest
stand-in". Deliberation that can deliberate about deliberation makes that load-bearing rather than
academic.

## 5z. Steppable search — state as data, a yield point, the ISA, and a CNL verb (2026-08-01)

**157 checks, 0 FAILED.** New module `search.py`; `driver.pursue` rewired onto it, split around
`driver.step`, reached from the ISA via `PLAN`/`STEP`, and finally reachable from the CNL as `plan`.
**No semantics changed by any of it.**

**What moved.** `pursue` held its whole working state in Python locals — a `frontier` list, a `seen` set,
a step counter, a list of refusals. Everything else it touches was already graph data, so the search was
the one part of the planner the planner could not read. That is `composability-principle`'s **unreachable
island** exactly, and it is where the homoiconicity claim was failing quietly. Now: `search`, `candidate`,
`candidate_arg`, `trace_step`, `signature`, `refusal`.

**⚠ This slice deliberately changes nothing else.** Swapping four containers *and* altering behaviour at
once would leave nothing to check the swap against. The 153 checks are the oracle; `pursue`'s report gained
`search` and lost nothing.

**⭐ The plan-so-far became a linked list and should always have been one.** The old `trace + ((name, …),)`
copied the whole prefix per candidate. `trace_step ──after──▶ trace_step` shares prefixes for free — the
expression was already describing a linked list.

**⭐⭐ The check this needed, which did not exist and would have caught the worst bug this project has had.**
`search-was-irreproducible-set-tiebreak`: a `set` made the frontier tie-break hash-ordered, and **132
checks passed over it** because every one asserted the *answer* and none asserted the *price*. So there is
now a check that asserts the price — same goal, six runs, one process, identical imagined-state counts.

⚠ **Run BLIND and with headroom, because that is the only discriminating case.** Guided search on the
tower imagines 2 states, far too few for a tie-break to matter; a guided-only check would sail past the very
bug it exists for. Unguided, every frontier key is `(0, 0, depth)` so essentially *everything* ties and the
order is purely insertion — 67 states. And it must not sit at the default `max_steps`, where blind search
merely exhausts at 60 every run and looks deterministic by hitting the ceiling.

**⭐ Verified by re-injecting the defect rather than by assuming.** Patching `take_best` to sort
`set(frontier)` gives `THE_COST_IS_IDENTICAL_ACROSS_RUNS: False` at 81 varying states while
`and_so_is_the_plan` stays `True` — **the defect's exact signature: the answer stays right and only the
price wanders.**

**Two rules `search.py` is built to keep, stated in it:** the frontier is an *ordered* edge list and the
sort over it is *stable*, so ties break exactly as they did when it was a Python list; and a signature is
*canonicalised by sorting* before comparison, never iterated, because `state_of` really does return a
`frozenset`.

⚠ `already_seen` is a linear scan bounded by `max_steps`, so a search costs O(steps²) attribute reads — a
few thousand. Not indexed on purpose: an index is a second structure that can disagree with the first.
Revisit only with a measurement (`measure-before-optimizing-ugm`).

**⭐⭐ Slice 2 — THE YIELD POINT — landed the same day. `driver.step` is it.** One iteration; returns
`None` to continue, the report when finished (found / stopped / exhausted). `pursue` is now a loop *over*
it and is unchanged in behaviour. What made this a mechanical change rather than a rewrite is slice 1:
because every piece of a step's state hangs off one `search` node, an iteration can be a module-level
function instead of a closure inside a `while`.

⚠ **The context splits in two, and the split is the honest one.** `search.context` returns the
graph-resident half (goal, workbench, thread, subject, bounds, the thread entry the goal was opened at);
`rank`, `allow`, `trace` and `decide` stay Python callables passed per call, because a callable cannot
live in a graph. Hooks are substitutable *behaviour*; everything else is *state*.

⚠ **Stepping is a yield point, not isolation.** The graph is mutable and the frontier refers to frames, so
driving one search while something else edits its workbench is undefined. Said in `step`'s docstring so
nobody assumes otherwise.

**Verified by driving it by hand**: the 67-state blind search, 67 turns, reaching the **same plan at the
same cost** as `pursue`. That equivalence is the whole check — a yield point that changed the search would
be a fork, not a seam — plus a guard that the frontier is non-empty at some pause, or `step` could have
quietly run the whole thing and returned once.

**⭐⭐⭐ Slice 3 — DELIBERATION IS REACHABLE AS DATA.** Two new opcodes, and a microfunction *authored as
text* now drives the planner and reads its answer:

```
fn think(goal, subject, thread) -> plan:
    PLAN R(s) F(goal) F(subject) F(thread)
    .again:
    STEP R(more) R(s)
    JMPIF R(more) ".again"
    ATTR R(result) R(s) "found"
```

Measured: same plan as `pursue`, same cost (2 imagined states), and the answer read back through an
ordinary `ATTR` because **the outcome is graph data** (`done`, `found`, `how`, `length`, and a `reached`
edge on the search node) rather than only a Python return value.

⚠ **Why `PLAN`/`STEP` are primitives and not sugar**, by this project's own closed-class test: searching
cannot be composed from GET/SET/LINK — there is no sequence of them that imagines a state, and frontier
ordering is not expressible as data manipulation. They earn a place in the opcode set the way `DISPATCH`
does. ⚠ And `STEP` is deliberately **one iteration**: an opcode that ran a search to completion would be
one opaque instruction and would buy nothing, because the whole point is stopping between two imagined
states.

⭐ **`open_planning` exists so there is ONE setup.** `pursue` and `PLAN` share it. Two setups that could
drift is the defect shape this codebase keeps recording, and the drift would have been silent — a second
path that forgot to seed the visited set with the root would re-imagine the starting world forever.
⚠ The already-satisfied case moved onto the search node (`already=True`) rather than being an early
`return` in `pursue`, so both drivers give the same answer; an ISA program calling `PLAN` previously had
no way to learn that the goal needed nothing done.

**⚠ A latent `asm` bug found on the way, same family as `../pystrider` §6.** `_OPCODES` filtered
`isa.__all__` on `isupper()` alone, so **`WRITES_REGISTER` — a frozenset — was accepted as an
instruction** at load time and would have failed opaquely inside the interpreter. Exactly the silent
acceptance `asm.py`'s docstring says it exists to prevent. Now filtered on `callable`.

**⭐⭐ And the CNL gained `plan` — the surface stops only DESCRIBING and starts DRIVING.** It is a
**fourth force on the same body**, not a new family: `goal` / `ask` / `why` / `plan` take identical
bodies and differ only in what is done with them, which is `intake.py`'s own thesis paying rent.

```
goal make it so:   ask is it so?:   why is it so?:   plan make it so:
    a on b             a on b           a on b           a on b
```

⚠⚠ **Why a DRIVING verb is safe on a surface a language model may write, and the property is structural
rather than intended:** the whole search happens on a workbench and `dispatch.service` refuses an imagined
target, so a `plan` block **cannot change the world however wrong the text is**. Measured — the block runs,
returns the two-step plan, and `a`'s edges are unchanged. **A verb that CARRIED OUT the plan would cross
into real effects and is deliberately absent** until that is discussed on its own terms rather than
arriving as a fifth item in a tuple.

⚠ **`replan` is not here, and that is a real gap rather than an omission.** Re-pursuing means naming a goal
that already exists, and `resolve` finds individuals by `label` **under `root`** — goals do not hang off
root, so the CNL has no form for referring to one. Inventing one would be the guess this module exists to
refuse.

**What is still open.** §6's termination limit is now load-bearing rather than academic, per §5y — a
program can `PLAN` inside a plan, and `MAX_STEPS` is still only an honest stand-in. Also unbuilt: the
`what` / `when` readers (§5x — `types.recognize` and the ordering comparisons already exist, they have no
verb), and **transitive closure in predicate position**, which §5x found is the one genuine closed-class
gap behind `where`.

## 6a. MEMORY — what was seen, and whether the agent did it (2026-08-01)

**161 checks, 0 FAILED.** New module `memory.py`; one hook in `dispatch.service`.

**⭐⭐ The past was computed, unreadable, then destroyed.** `graph.py`'s undo journal held the inverse of
**every** mutation — measured at **650 entries** after one two-step plan — as a Python list of closures:
unreadable by the system, LIFO-only, and cleared outright by `dispatch.service`'s `commit()`. The thread
recorded *that* `stack` ran and never *what it changed*. Third island of the session, after the search
frontier and deliberation, and the same signature: **not a missing mechanism, but a mechanism whose output
nothing keeps.**

⚠ **`commit()` is right and stays.** It answers *"can I reverse this?"* and once an effect has left the
answer is no. What it must never also answer is *"can I remember what preceded it?"*. The snapshot is
taken **before** the commit; the journal's semantics are untouched.

**⭐⭐ The external world breaks a delta log, and that reshaped the design.** A journal delta records only
the agent's own writes — when a file changes on disk *nothing happens in the graph at all*. Worse, the
second look is itself a write, so a naive delta log would say *"the agent changed `count` from 3 to 5"*
when the truth is *"the agent looked, and found 5 where it had recorded 3."*

So: **observations** (what was seen, at the dispatch boundary — already the one place anything crosses)
plus **the thread** (what was done, already ordered, already flagging `done`), and **attribution is
DERIVED from the two**. ⭐ It needed no new record: `driver.establishes` already reads a stored body to say
which slots a function writes and with which roles, and `role_node` resolves a role against bindings. The
engine could already answer *"could this application have touched that slot?"* and had never been asked.

Measured — the folder scenario, with an external world the agent does not control:

```
3 -> 5: external — nothing I did could have
5 -> 0: mine (empty_it)          <- read off the body; nothing declared it
```

⚠ **Evidence, not proof.** `establishes` over-approximates by contract, so `MINE` means *could have been
mine*. And the everyday case stays undecidable: observe A, act expecting B, observe A — either the action
did not take or the world reverted it, same evidence, window closed.

**⭐⭐ The user corrected me on change-and-back, and the correction improved the design.** I claimed it was
invisible; it is visible whenever an observation falls **inside** the excursion, and three sightings
showing A, B, A are exactly that. So it is a **sampling-rate** question, not an impossibility — and
sampling rate is something the agent controls, given volatility. It also settled a storage fork: a
difference-only record would store A, B, A as *no change*, so the agent would have watched a round trip
and recorded that nothing happened. What survives is narrower: sightings bound change **from below** and
never count it.

**⭐⭐ Encoding and retention are different moments with OPPOSITE defaults** — the user's point, and it
reversed my recommendation. *You do not remember how many steps it took to get to school*: not forgotten,
never encoded.

| moment | default | why |
|---|---|---|
| **encoding** | **do not** | never-encoded is honest ignorance, *recoverable by looking* |
| **retention** | **do** | dropping what was reasoned from can contradict conclusions already drawn |

⭐ **The encoding gate already exists and it is attention**: `dispatch.service` is called *on a target*,
which is what is being attended to. So the structural default is the slots of the thing looked at —
neither everything nor nothing. ⚠ Every slot of it, not only the ones the tool rewrote, because a
difference-only record cannot tell *unchanged* from *unobserved* (the `UNKNOWN` conflation one level up)
and would leave "when did I last check?" unanswerable for stable slots.

**⭐ Volatility gives `SENSE` something to aim at.** `driver.py` records that `SENSE` "needs ignorance",
and ignorance was the only available trigger — *I do not know, so look*. Unattributed-change rate supplies
the one that actually arises: **I knew, and it is probably stale.** Measured 1.0 for a slot the world moves
and 0.0 for one only the agent touches.

**Still open:** the retention seam (`keep` is wired and inert; the KEEP/COMPACT/DROP/PIN vocabulary is
designed, not built), and edges — sightings cover attributes only, and a folder's *contents* are edges.
`workbench.expectations` already faced that and answered qualitatively ("files appeared", never how many);
the same granularity should apply.

## 6b. ⭐⭐⭐ NEXT ARC — ONE OUTER LOOP, NOTHING UNINTERRUPTIBLE (handoff, 2026-08-01)

**Not started. This section is the brief.** Everything below was settled in discussion; none of it is built.

### The principle (the user's, and it is sharper than what this session built toward)

> There is a **single outer-outer control loop**. Planning is **not** a real execution control loop — its
> control loop is *represented as data*, and the outer loop always interleaves and ticks. No seams, no
> fixpoint procedures that cannot be interrupted.

⚠ **This is not a new direction — it COMPLETES one already taken.** `run_bank`'s blind fixpoint was
retired for exactly this reason (a fixpoint is a computation you cannot be inside of), and
`agent-not-theorem-prover` rejects eager exhaustive completion on the same grounds. The principle is that
decision applied without exception, at every level.

### The test, which makes "no seams" checkable rather than a slogan

> **Can the executor be stopped between any two primitive operations, and can the system say what it was
> doing?**

### ⚠⚠ Applying the test today: we removed one seam and left an identical one BELOW it, inverted

§5z made planning steppable. But `isa.Machine._loop` is an ordinary Python `while` holding `pc`, `stack`
and `regs` as Python locals, so the `think` microfunction §5z is proud of —

```
fn think(goal, subject, thread) -> plan:
    PLAN R(s) F(goal) F(subject) F(thread)
    .again:
    STEP R(more) R(s)
    JMPIF R(more) ".again"
```

— drives an **interruptible** search from inside an **atomic** invocation. Steppability at the wrong
level. The principle predicts exactly this, which is the argument for adopting it.

### The inventory — every remaining control loop, and where its state lives

| loop | budget | state in |
|---|---|---|
| **`isa.Machine._loop`** | **`MAX_STEPS = 100_000`** | Python: `pc`, `stack`, `regs` — **and `Focus` is a Python object too** |
| `execution._replay` | plan length | Python |
| `driver.carry_out` | attempts | Python |
| `driver.pursue` | — | already `while True: step(...)`; now trivially a pure driver |

⚠ **Four things must materialise, not three.** `focus.py`'s named heads are as much interpreter state as
the registers, and it is easy to miss because `Focus` looks like a helper rather than a loop variable.

### Two versions. The second is better and the blast radius is MEASURED

**(a) Materialise and tick.** `pc`/`stack`/`regs`/focus become graph data; `_loop` becomes `tick`. Same
move as §5z slice 1, one level down. ~40 register-write sites in `_step`.

**(b) ⭐⭐ STRONG — remove the looping instructions, so a microfunction CANNOT cheat.** With no backward
jumps a program is straight-line plus forward branches: **termination becomes structural**, `MAX_STEPS`
becomes unnecessary rather than an "honest stand-in", and repetition must come from the outer loop — which
is the principle, enforced rather than trusted.

**⭐ Two independent routes reach (b), which is the strongest evidence available here:**

* `deliberation.md` §12 already concluded that a **closed, branch-free vocabulary makes `establishes`
  EXACT** — every one of its `unknown` cases is an artefact of reading a general-purpose ISA. Confirmed in
  code: `driver._effects` does `unknown.add(None)` on `CALL` — *"a local jump: the body runs out of
  order"* — which darkens the whole description. Removing local control flow removes that blindness.
* The user reached the same conclusion from **termination**. Two directions, one answer.

**⭐ Blast radius, measured — only THREE sites use backward jumps, all in `selftest.py`:**

* `check_isa_writes_graph_and_loops_over_indexed_edges` (`JMPNOT`/`JMP`) — exists to test looping;
* `check_runaway_program_halts_loudly` (`JMP("loop")` at itself) — exists to test that runaway halts, and
  becomes **unconstructible** under (b), which is the point rather than a loss;
* the `think` function above (twice) — which is the inverted case, and under (b) the outer loop drives the
  stepping instead.

No shipped `.mf` uses one. `../pystrider` should be asked before (b) lands.

### Order, oracle, and the trap

1. `pursue` becomes a pure driver (nearly free now).
2. `Machine`: state to graph data, `tick` replaces `_loop`. **The 161 checks are the oracle** — same
   discipline that worked three times today: move state, change nothing else, verify, then proceed.
3. Only then (b), retiring the loop opcodes.

⚠ **The trap: keeping the fast Python loop "just for the hot path."** Two executors that are supposed to
agree is the drift class this codebase keeps re-finding, and it would drift **silently**. Either the ticked
interpreter is *the* interpreter or this is not worth doing. Slow and singular beats fast and forked.

⚠ **What must NOT change: `dispatch` is not a seam to remove.** Once a handler is called the world is
executing, not us. That boundary is what the design is organised around, and `commit()` is the honest
admission of it.

### What it buys beyond tidiness

**Termination becomes ONE problem.** Today `Machine.MAX_STEPS`, `pursue(max_steps)` and `carry_out`'s
attempts are three independent stand-ins in three corners, and §6 lists termination as open. One executor
means one budget, one place to reason about it, and one place a *decision* about "have I spent enough on
this?" can live. Under (b) it stops being a budget at all for the ISA half.

It also dissolves the deliberation regress rather than guarding it: deliberating about deliberating is more
data on the same tick.

### The verb set, for when the loop exists

Settled in discussion, and deliberately the small part — what kind of step a tick may be:
**imagine** (free, reversible) · **look** (crosses `dispatch`, reversible consequences) · **act**
(**gated**, `commit()` fires, nothing after is undoable) · **remember / forget** (a slower clock) ·
**commit / refuse** (terminal, already exist).

⚠ **One thing must not become uniform: irreversibility.** Acting is not a peer of remembering, and a
uniform cycle must keep the asymmetry `dispatch.py` calls "the single most important safety property in
the design". Rank a guess, prune a proof — "this cannot be undone" is nearer a proof.

⚠ **And one concrete gap this exposes:** `dispatch.register(name, handler)` takes any callable and nothing
says whether a tool **observes** or **changes**. The veto and commit machinery treat a directory scan and a
sent email identically. `look` versus `act` needs that distinction to exist.

⚠ **Do not flatten the goal.** A game loop *simulates*; this *pursues*. `unmet` is the gradient and it is
the entire reason guidance works (3 imagined states against 55). Adopt the loop's shape for *what may
happen at a step*, keep the goal for *how the step is chosen*.

## 6c. ⭐⭐⭐ THE EXECUTOR TICKS — the interpreter's state is graph data (2026-08-01)

**165 checks, 0 FAILED.** New module `activation.py`; `focus.py` rewritten onto the graph; `isa.Machine`
split into `start` / `tick` / `run`. This is §6b's step 2, and **the 161 checks were the oracle** — the
discipline that worked three times before: move state, change nothing else, verify.

**The test is now answerable, and it is checked rather than asserted.** *Can the executor be stopped
between any two primitive operations, and can the system say what it was doing?* A paused activation
carries `pc`, the stack, every register, and the focus it is running on; `describe` names the function and
the opcode; and a **stored `.mf` microfunction reads a suspended one with ordinary `ATTR`/`GET`** — no new
opcode, the same evidence `thread.py` used for the same claim.

**⚠ Four things had to materialise, and the fourth is the one that hides.** `pc`, the stack, the registers
— and the **focus**. `focus.py`'s docstring used to say, approvingly, that a focus "holds no graph state
itself". That was the defect stated as a feature: `thread.py` exists because *attention was not data*, and
it materialised the **shifts** while leaving **the pointers** in a Python object that was fresh per call and
discarded.

**⭐⭐ The bug this uncovered was in something else, and it had been latent since the workbench was built.**
`workbench.step` and `execution._replay` both wrapped an invocation in `before = set(g.nodes)` and took the
difference. That answers *what nodes appeared anywhere*, when the question is *what did this call add to the
world* — an over-approximation from the start (a callee minting a hypothesis would have counted). Putting
the interpreter's state in the graph turned it live and loud: a `focus` node was bound as an imagined result
and then type-checked, giving `escalate(r=…): focus#96108 is not a report`. **The fix is a record, not a
filter over kinds**: `NEW` is the only instruction that mints, `DISPATCH` is the only other way the world
grows, a callee is reached through its `caller` edge — so `activation.minted` is exact, and it removes two
whole-graph scans (`labelling-error-and-when-tests-earn-their-place`: *the fix was not to scan*).

**⚠ Retirement is not the same as being uninterruptible, and the two must not be conflated.** A finished
activation is not state anybody can be inside of, so `run` drops it; `retire` **refuses** a live one. Same
shape as `dispatch.commit()` — the honest admission that a boundary has been crossed, never a licence to
discard what has not. `workbench.discard` scraps the activations its imagined steps ran on (via a new `ran`
edge on the transformation), which is what keeps *back to the original size* true.

**⭐ `INVOKE` links callee to caller, so the ISA has a stack trace.** A nested invocation used to be a
nested Python frame — invisible to the system running it — so "what was it doing?" could only ever answer
about the outermost program.

**Measured: the cost is nothing.** The full self-test runs in **7.4 s against 7.2 s** before, with every
register read and write now going through the graph. The reason is that registers per activation are few
and the reads are short scans; it was worth measuring rather than assuming, and it removes the only
argument for the "keep the fast Python loop" trap §6b warns about.

**Four planted-bug probes, each biting a distinct key** (§7):

* a `tick` that quietly runs the program to completion — the *fast path* trap, planted — turns
  `IT_REALLY_PAUSED_MID_FLIGHT` red **while the answer stays right**, which is the defect's exact signature;
* a `describe` that gives only an index turns `and_it_says_what_it_was_doing` red;
* an `INVOKE` that forgets `caller=` turns `AND_IT_NAMES_ITS_CALLER` red while the effect still happens;
* a `retire` without its guard turns `a_live_activation_cannot_be_retired` red.

**⚠ One existing check had to be rewritten, and the old form had stopped meaning what it said.**
`check_fork_explores_two_candidates_without_copying_the_world` asserted `len(g.nodes) == 3` to mean *the
world was not copied*. Once heads are nodes that is simply false, and the honest assertion is the one it
always intended: the two candidates are **the same two nodes**, not images of them.

**⚠ And verifying against the consumer turned up a RED PIN THAT WAS ALREADY RED.** `../pystrider`'s strider
suite is **155 passed, 1 failed** against this work — and the same test fails identically with this session's
changes stashed, so it is not from the tick. It is **§5w's own change**: `test_strider_unknown.py`'s
`..._CALLS_and_that_is_a_fact_about_our_DESCRIPTIONS` hits `LINK: operand F(arg) is not a node`, which is
exactly the consumer impact that change's `CHANGELOG` line predicted in writing. ⚠ §5k verified the pins
after touching the engine; §5w did not, and the prediction sat in the changelog while the breakage sat
unnoticed in their suite. **Predicting a consumer impact is not the same as telling the consumer.** Worth
raising with them as an intended refusal rather than leaving them to bisect. (The rest of their collection
errors are the pre-existing `import ugm` ones this file already records.)

### ⚠ What is NOT done, and the measurement for the next step

**(b) — removing backward jumps — is deliberately not landed.** §6b's blast radius was **re-measured**, and
it is now smaller than recorded: `../pystrider` uses **no loop opcode at all** (`JMP`/`JMPIF`/`JMPNOT`/
`CALL`/`RET` appear nowhere in `strider/` or its experiments), so the three sites in `selftest.py` are the
whole of it. That is the fact the "ask the consumer first" note existed to establish.

⚠ **But (b) cannot land before the outer loop exists.** Under (b) repetition must come from the outer
loop — and today the only thing that expresses repetition over `STEP` is `think`, whose backward jump (b)
removes. Landing it now would delete the one way to write the thing with nothing to replace it. **(b) is
the third step for a reason, and the outer loop is the second half of it.**

**Two Python loops remain, exactly as §6b's inventory says:** `execution._replay` (state: which frame,
`bound`, `notes`, `ran`) and `driver.carry_out` (attempts). ⭐ They were deliberately left, and the argument
is the same one that made the ISA the mandatory case: **the ISA loop *is* the executor**, so it had to
tick. Those two are candidates to become **ticks of the single outer loop** rather than two more bespoke
steppers — materialising them separately first would build the very thing §6b calls the trap, in slow
motion. ⚠ `_replay` also crosses `dispatch`, so its yield points are where the `look` / `act` asymmetry has
to be honoured rather than merely tidied.

## 6d. ⭐⭐⭐ ONE OUTER LOOP — every control loop is now data (2026-08-01)

**170 checks, 0 FAILED**, and the self-test is *faster* than before the arc started (6.4 s against 7.2 s —
`activation.minted` removed two whole-graph scans). New module `loop.py`; `execution._replay` and
`driver.carry_out` materialised. **§6b's inventory is empty.**

**⭐ Almost nothing in `loop.py` is mechanism, and that is the evidence the earlier slices were the right
ones.** Every control loop had already become *a node plus a `step`*, so the outer loop is an **ordered
agenda and a dispatch on `kind`**:

| task | one primitive step is | state lives in |
|---|---|---|
| `activation` | one ISA instruction | `activation.py` (§6c) |
| `search` | one imagined state | `search.py` (§5z) |
| `replay` | one real action | `execution.py` (here) |
| `pursuit` | one step of plan/act/check/replan | `driver.py` (here) |

Adding a kind of work means writing its `step`, not touching `loop.py`.

**⭐ Round-robin, and the rotation IS the data.** `tick` takes the head of the agenda, advances it one
step, and re-links it at the tail — so interleaving is not a policy the module implements but the ordinary
consequence of the agenda being an ordered edge, and *which task is next* is a question anyone can ask of
the graph. Checked with a stored microfunction and a whole goal-pursuit on one agenda, alternating.

**⚠ A tick of a pursuit is NOT "one attempt", and getting that wrong would have been the easy version.**
An attempt contains a whole search and a whole replay. So a pursuit holds a **current sub-task** and
advancing it advances *that* by one primitive step, changing phase only when it finishes — and a phase
transition costs a tick of its own, because *"the plan is in hand and nothing has been done yet"* is a
state the system may legitimately be stopped in. It is the last moment before anything becomes
irreversible. The check requires `ticks > 2 × attempts`, and the planted-bug probe (a tick that runs a
whole attempt) turns exactly that key red while the verdict stays right.

**⭐⭐ The one thing that must NOT become uniform is irreversibility, and it is now expressible.**
`loop.verb_of` answers **before** a step is taken: `imagine` costs time, `act` cannot be taken back. §6b
named the missing piece and it is closed — `dispatch.register(name, handler, observes=True)` distinguishes
a directory scan from a sent email, ⚠ **declared rather than inferred, defaulting to the unsafe-to-assume
answer** (unmarked means *acts*). ⚠ Declining is something a *caller* does, not something `run` does on
its behalf: `run(until=)` stops after a tick, and stopping *before* an act means reading `verb_of` off the
head of the agenda and simply not calling `tick`. That asymmetry is deliberate.

**⭐ `open_execution` and the contradiction check both became ONE setup.** Extracting the replay's seeding
had the same motive as §5z's `open_planning`, and the second one was found by writing the bug: the first
draft of `pursuit_step` re-implemented `conflict.unsatisfiable` because `pursue` did it as an early
`return`. Now it is recorded **on the search node** (`contradictory=`) and reported by `step`, exactly as
`already=` was — so every driver gives the same answer and there is nothing to keep in step by hand.

**Five planted-bug probes, each biting a distinct key, all with the right signature** — the answer stays
right and only the property is lost:

* a greedy `execution.step` → `IT_PAUSED_BETWEEN_TWO_REAL_ACTIONS` red;
* a pursuit tick that runs a whole attempt → `A_TICK_IS_A_PRIMITIVE_STEP_NOT_AN_ATTEMPT` red;
* a `tick` that re-links at the **front** (the "just finish this one" trap) → `and_really_alternated` red;
* a `verb_of` that always answers `run` → the loop takes the irreversible step, and
  `AND_THE_WORLD_WAS_STILL_UNTOUCHED_THEN` goes red, which is the proof the stop was load-bearing;
* a `dispatch.observes` that always says yes → `a_changing_one_is_an_ACT` red.

**⚠ And the third probe justified a key I nearly did not write.** `THEY_INTERLEAVED` (the *set* of kinds
advanced) stayed **green** under the no-rotation bug, because both tasks still ran eventually. Only
`and_really_alternated` (the *order*) caught it. A set answers "did both happen"; interleaving is a claim
about order, and the obvious assertion was the wrong shape.

**⚠ A refusal that is the honest boundary of the whole arc.** `loop.advance` **refuses** an activation
with no `of` — a program that exists only as a Python tuple cannot be reconstructed, so it can be resumed
by nothing but the caller holding it, which is `composability-principle`'s unreachable island exactly.
Saying so beats skipping it. The vacuity guard is that the same program *stored* is driven without
complaint, so the refusal is about reconstructability, not about activations.

### ⚠ (b) is STILL not ready, and now for a sharper reason

> **Superseded by §6e the same day: (b) was probed and the recommendation is NOT to do it.**
> The continuation question below is real, but it turned out not to need answering — see §6e.3.

§6c said (b) — removing backward jumps — waits on the outer loop. The loop exists, and the real blocker is
now visible and is **not** the opcodes:

```
fn think(goal, subject, thread) -> plan:
    PLAN R(s) …
    .again:  STEP R(more) R(s) ;  JMPIF R(more) ".again"
```

Under the principle, `think` should `PLAN`, put the search **on the agenda**, and return — the outer loop
advances it. But then `think` cannot *use* the plan: its invocation is over before the search finishes.
**So (b) needs an answer to "how does a program wait for a task it scheduled", and that is a question
about continuations as data, not about jumps.** Removing the loop opcodes first would delete the only way
to express the thing while the replacement is still undesigned. ⭐ The three-site blast radius stands
(`../pystrider` uses no loop opcode), so this is a design gap, not a compatibility one.

**Also still open:** `remember` / `forget` are in §6b's verb set and are not scheduled by the loop — they
are the "slower clock", and `memory.py`'s retention seam (§6a) is the thing they would drive.

## 6e. ⚠⚠ (b) PROBED, AND THE RECOMMENDATION IS: DO NOT DO IT (2026-08-01)

**171 checks, 0 FAILED.** §6b's strong version — remove the looping instructions so a microfunction
*cannot* cheat — was carried through three sections as the arc's destination. It was probed rather than
built, per §7, and **all three of its payoffs are weaker than recorded**. Nothing was removed; one check
and one measurement were added.

**⭐⭐ 1. The `establishes` payoff is ZERO on this library, and the reasoning behind it was wrong about the
code.** §6b said: *"`deliberation.md` §12 already concluded that a closed, branch-free vocabulary makes
`establishes` EXACT — every one of its `unknown` cases is an artefact of reading a general-purpose ISA.
Confirmed in code: `driver._effects` does `unknown.add(None)` on `CALL`."* Measured over every function the
engine's own scenarios define:

| | functions |
|---|---|
| already **exact** | **8** |
| darkened by `DISPATCH` | 2 |
| darkened by control flow | **0** |

And the reason is worse than the count. **`_effects` never reads jumps at all** — the walk is linear, so
`JMP`/`JMPIF`/`JMPNOT` are skipped entirely: a write in a loop body is reported once, a conditional write
is reported as unconditional. Removing backward jumps would therefore change `establishes` **only** by
deleting the unexercised `CALL` case. The two real `unknown`s are `DISPATCH` — the world — which no
branch-free vocabulary touches. Now stated in `_effects` itself, because it was a silent property of an
over-approximation whose contract says *that* it over-approximates but never *which constructs* do it.

**⭐⭐ 2. The termination payoff is RELOCATED, not delivered.** (b) promised *termination becomes
structural, `MAX_STEPS` becomes unnecessary*. But §6b in the same breath says **repetition must come from
the outer loop** — so an agenda that can re-schedule is exactly where unbounded repetition moves to, and
`loop.run(max_ticks=…)` is the same honest stand-in one level up. What (b) would actually buy is *"one ISA
program terminates"*, which is true and much smaller than *"termination becomes one problem"*. ⚠ The
budgets that remain are `Machine.MAX_STEPS` (a runaway guard), `search.max_steps`/`max_depth` and
`pursuit.attempts` (**policy** — how much is this goal worth?), and `loop.run`'s `max_ticks` (the one that
bounds everything the loop drives). Collapsing them would be wrong: they are not four stand-ins for one
question any more, which is itself progress, but it is not the promised single budget.

**⭐⭐⭐ 3. And the practical motive is GONE, because every level ticks.** The argument that made (b) feel
urgent was §6b's own diagram: `think` spins on `STEP`, so *"an interruptible search driven from inside an
atomic invocation"*. **The invocation is not atomic any more.** The loop advances the activation one
instruction at a time, that instruction advances the search one imagined state at a time, and unrelated
work runs in between — checked, with the discriminating guard that the other task must advance **while
`think`'s search is still open**, not merely before or after it. Three levels of stepping compose, and a
blocking program no longer holds the loop.

That was the whole reason to force repetition out of the ISA. **So a microfunction does not need to be
rewritten in continuation-passing style, and `AFTER`/`SCHEDULE` opcodes are not needed either** — which is
just as well, since CPS-ing the authoring surface would have been paid by every author forever.

**⚠ What (b) would still buy, stated fairly so the decision can be revisited:** a program whose termination
is decidable by inspection, which matters if untrusted `.mf` is ever loaded (§5y names that as the trigger
to revisit builtin policing, and it is the same trigger). If that day comes, the blast radius is still
three sites in `selftest.py` and `../pystrider` still uses no loop opcode. **Until then the cost is
certain and the benefit is measured at zero.**

> **Every claim in this arc that was checked got weaker, and the weakened version is the one worth
> keeping** — §7, holding for the fourth time in two days. The strong version survived three sections of
> being written down as the destination, and eleven lines of measurement.

## 6f. ⭐⭐⭐ WHAT THE ARC WAS FOR: the system can judge its own computation (2026-08-01)

**172 checks, 0 FAILED.** **The user's observation, and it is the payoff no single slice delivered:** this
architecture allows heuristics about the *status of the computations themselves* — *"I have been planning
for too long"* — which is monitoring and control of the system's own process.

**⭐⭐ It was probed rather than agreed with, and it came out true with one line missing.** A watcher
authored as **text** reads a live `search` node, judges it mid-flight, and stops it:

```
# Am I taking too long over this? If so, stop planning.
fn watch_planning(s, budget):
    .again:
    ATTR R(over) F(s) "done"  ;  JMPIF R(over) ".end"
    ATTR R(n) F(s) "steps"    ;  ATTR R(b) F(budget) "value"
    LT R(ok) R(n) R(b)        ;  JMPIF R(ok) ".again"
    SET F(s) "stop" "REFUSE"
    SET F(s) "stop_why" "planning has gone on too long"
    .end:
```

Measured: the verdict lands **while the search is still open** (15 states in, phase `planning`), the
pursuit gives up honestly, and the world is untouched. The control — the identical search with a generous
budget — imagines all 67 and **succeeds**, so the stop is what ended it and not exhaustion.

**⚠ Three things had to already be true, and each came from a different slice:**

* **the state of a running computation is data** — `search.steps`, the frontier, the phase, the program
  counter (§5z, §6c, §6d). Nothing to add;
* **the watcher runs *while* the watched thing runs** — because it is a task on the same agenda and the
  loop rotates (§6d). Without that it could only ever deliver a post-mortem;
* **the judgement can have an effect** — and *this* was the missing line. `stop` as ordinary data, honoured
  by `driver.step` beside the other termination conditions, and by `loop.finished` for every kind of task.

**⭐ Monitoring and control are separable, and the planted-bug probe separated them.** With `stop` ignored,
the watcher still judges correctly — and the world gets built anyway. With interleaving removed, it cannot
even judge. Two probes, two distinct halves, both red in the right places.

**⭐ `decide` is not made redundant by this and the distinction is worth keeping.** `decide` is a Python
callable consulted **per proposal** — the right frequency for a ranker-shaped decision (`deliberation.md`
§4) and the wrong thing for something a domain author writes. `stop`-as-data is the same decision expressed
as **data**, which the standing principle requires. They produce the *same verbs and the same report*,
through one `_stopped` builder, deliberately: a caller cannot tell which route fired, so two report
builders would drift invisibly.

**⚠ Stopping a `replay` is the valuable case and the dangerous one.** It means *do not take the next
irreversible action* — exactly what a monitor should be able to say — and it leaves a plan half
carried-out. That is honest rather than new: a divergence already leaves one, and nothing is ever undone
because real effects have left the graph.

**⭐⭐ And it is a third, independent argument against (b).** A watcher must poll, so it **needs**
repetition; under (b) it could not be written as a single microfunction at all. §6e reached the same
conclusion from exactness and from termination — three directions, one answer.

⚠ **On the word.** This is metacognitive monitoring in the plain functional sense: the system's own process
is an object it can inspect and steer, the way it already inspects a goal or a plan. That is a specific,
checkable capability and it is what the checks assert. It is not a claim about anything else the word
"self" gets used for, and the docs should not start making one.

## 6g. ⭐⭐⭐ FORGETTING IS THE DEFAULT (2026-08-01)

**176 checks, 0 FAILED.** New module `forget.py`. **The user's rule:** *forgetting is the default;
remembering is the exception — the result of a tool call, something that surprises us. Not ordinary
things.*

**⚠ It looks like a reversal of §6a and is not, which is the first thing to get straight.** §6a's table
has **retention defaulting to KEEP**, argued from *dropping what you reasoned from can contradict
conclusions already drawn*. That argument was about **sightings**, and every one of them is kept here. What
§6a never had is the category the outer-loop arc then created — **the engine's own scaffolding** — so the
rule generalises rather than reverses:

> **Keep what you cannot re-derive.** The two irreducible kinds are **a crossing of the world** and **a
> surprise**. Everything else is re-derivable from the goal and the library, by thinking again.

**⭐ Surprise needed no invention.** The engine already computes it three ways — `memory.attribute`
answering `EXTERNAL`, a `deviation` node, `workbench.unmet_expectations`. Retention had never been asked to
consult them.

**⭐⭐ Name the ROOTS, not the rubbish.** A list of droppable *kinds* would drift the moment a module added
one. A root set states the belief directly, and the **direction invariant does the rest for free**:
metadata points at what it describes, so the world drags nothing in while a surprise drags in exactly what
it was a surprise *about*. ⭐ `loop` is a root, which makes **live work safe with no special case at all**
— being scheduled *is* the statement "this is what I am doing", and the closure protects the pursuit, its
search and its workbench. (The first version took a hand-passed pin and promptly swept the loop node out
from under the sweep running on it.)

**⚠ Forgetting is a TASK, not a pass** — one record per tick, on the same agenda, interleaved and
stoppable. A sweep that ran to completion inside one call would be exactly the uninterruptible fixpoint
this arc exists to remove, and it is the *worst* candidate for one. ⭐ It is also not exempt from its own
rule: a finished sweep is ordinary scaffolding, and the next one forgets it — asserted.

**Measured, on three ordinary goals over the three-block world: 892 nodes to 238.**

**⚠⚠ THE CHECK IS NOT THE NODE COUNT.** A sweep that dropped everything would score beautifully on size,
so every question the engine can ask of its past is asked before and after and must come back
**identical**: what is true, why (`query.history_for`), what I did, whether two intentions collided, which
goals are met, and whether the library still thinks.

### ⚠ Four defects, and three were found by probing rather than by the green

1. **⭐⭐ THE WORKLIST WAS AN EDGE LIST BEING CONSUMED BY SOMETHING THAT DELETES EDGES.** `Graph.drop`
   removes every edge into the node it drops — *including the sweep's own `doomed` edge to it* — so a
   cursor walked a list shrinking underneath it and **silently forgot every other record**: 892 to 564
   where 798 were marked. It looked like a working sweep: every answer it had to preserve was preserved and
   the count really did fall. Same family as `search-was-irreproducible-set-tiebreak` — not a wrong
   answer, a *quietly partial* one, from a container whose behaviour the walk did not account for. Now
   consumed from the front, and `EVERY_SURVIVOR_IS_KEPT_FOR_A_REASON` is the key that catches it.
2. **⚠ `"thread"` was a DEAD root** — it names no kind, because §5b made a thread *an episode extended*.
   The protection was coming from `episode` all along. Found by a planted-bug probe that removed it and
   changed nothing.
3. **⚠⚠ The two exceptions the rule is actually about were UNTESTED.** The blocks world never dispatches,
   so it has **zero** observations — a sweep over it could have dropped every observation there is and
   every key would have stayed green. Found by a probe removing `observation` from the roots that changed
   nothing. There is now a check on a world the agent really looks at, where a directory moves under it.
4. **⚠ And my own scenario was wrong twice** in ways the code was right about: the third `look()` re-scans
   and overwrites what `empty_it` did, and an action invoked directly never reaches the thread, so
   `attribute` called both changes external. Both fixed in the check, neither in the engine.

**⚠ Which roots actually protect anything — MEASURED, because assuming was wrong twice.** `function`,
`type` and `episode` are load-bearing (`episode` carries the most, 83 nodes); `deviation` once its replay
is swept; `loop` only while work is live, which this table cannot see and a probe proved. `root`, `goal`
and `observation` are **currently redundant** — all reached via the thread — and are kept deliberately
**as statements of the rule**, because the first compaction of old thread entries would otherwise turn *we
keep what we saw* into *until the thread is tidied*. That is the difference between a redundant root and a
dead one.

### ⭐⭐ COMPACT — and it is a RULE, not a mechanism

Added the same day. §6a's vocabulary is now `KEEP` / `COMPACT` / `DROP`, with `PIN` as `also=`.

`goal.py` already keeps two kinds of evidence rigorously apart, because conflating them was a real defect
(§5g: the driver closed a world goal on imagined evidence, so a goal read as *met* while nothing had
happened):

| record | means |
|---|---|
| `planned` + `seen_in` + `planned_witness` | *I know how to do this* — pointing at an imagined frame |
| `closed` + `met_by` | *this is now true* — pointing at a real node |

**Once the second exists the first is a snapshot of a world that no longer does**, and one edge into one
frame keeps every frame, mapping and transformation reachable from it alive. So the whole of `COMPACT`
turned out to be *knowing when a record is superseded* — two unlinks and a condition. **Measured: 51
further nodes, 22% of what survives an ordinary sweep.**

⚠⚠ **The condition IS the correctness argument.** A goal that was planned and *not* carried out has no
other evidence: its imagined frame is the only account of how it would be met, and `execution.recover`
needs the frame tree it belongs to. The check requires the two goals to be treated **oppositely**, and the
planted-bug probe — a compaction that ignores `closed` — turns three keys red while the tidying still
appears to work: the merely-planned goal loses its evidence, its frame is swept, and its plan becomes
unreadable. ⚠ `planned` survives on both; what goes is only the pointer into the imagination.

⚠ Compaction runs **eagerly**, before the doomed set is computed, and is not queued a-record-per-tick like
the sweep. An unlink here is not a loss — it removes a claim a *better* record already makes — so there is
nothing to be stopped in the middle of.

**Still open:** ⚠ `PIN` (`also=`) is unexercised, and compaction of **old thread entries** is the case
that would make `observation` a load-bearing root rather than a redundant one.

## 6h. ⭐⭐⭐ TRANSITIVE REACH — the one genuine closed-class gap, built (2026-08-01)

**179 checks, 0 FAILED.** `path.reaches` / `via` / `parse_link`; `goal.require_link(..., transitive=True)`;
the CNL form `wh contains+ parcel`.

**⭐⭐ Two independent routes reached this single item, which is the strongest evidence available here.**
`closed_class_rechallenged.md` probed five relational forms and found four **pure sugar** — causation,
quantification's open case, force/level, identity/merge — with **transitivity** the one needing a real
engine extension. §5x arrived at the same item by walking backwards from *what does the word `where`
need*: a parcel in a box in a warehouse is not reachable by a fixed-depth type, a goal's link constraint
reads **false** because the parcel is not a direct target, and the path grammar has no repetition operator.

**⚠⚠ PREDICATE POSITION ONLY, and that restriction is the design rather than a first slice.** *Is X
reachable from Y?* stays boolean and single-valued, so it breaks no contract. A **reference** —
`a.contains+.label` — would denote a *set*, breaking `node_at`'s promise of one node or `None` and every
caller that assumes it. `parse` still refuses `+` in a path and now **says where to go instead**, which is
the difference between a refusal and a dead end.

**⭐ It stayed the `link` sort rather than becoming a new one.** It *is* the same subject, label and object
asked as reach instead of adjacency, so one line in `goal.holds` covers it; a new sort would have had to be
taught to `query.refutes`, `conflict`, `driver.relevance` and `describe` for a difference none of them care
about.

**⭐⭐ And the planning half is the part a predicate alone does not give you.** `driver.relevance` scores a
proposal by what a body *establishes*, and `put_in` links `box contains parcel` — which is **not** the
constraint being asked (`wh contains+ parcel`). So the closing move cannot reach the top band, and the plan
is found by **ranking**. This is *rank a guess, prune a proof* (§5e) earning its keep in a case that did not
exist when it was written: had relevance been a filter, a reach goal would be unreachable. Checked end to
end — authored as text, planned, carried out, and the parcel really ends up in the box.

**⚠ Two authored forms compose to make the check mean something.** `never touch wh` is what forces the
transitive route; without it the planner puts the parcel straight into the warehouse and a plain link
constraint would have done. A plan constraint and a transitive world constraint, in one block.

### ⚠ Two vacuous checks caught by probing, both mine

1. **⚠⚠ THE CYCLE GUARD WAS TESTED BY A QUESTION THAT HAS AN ANSWER.** Containment is only *supposed* to be
   acyclic and a graph does not enforce it, so `reaches` carries `types._target_ok`'s discipline. But asking
   whether something that **is** there is reachable returns before the loop is ever re-entered — a version
   with **no cycle protection at all** passed. Measured, by planting exactly that. Only a **miss** walks the
   whole cycle, so the check now asks for a node that is not there, and the naive version raises
   `RecursionError`. *A termination guard is tested by a query that fails, never by one that succeeds.*
2. **⚠ A contrast evaluated after the mutation it was contrasting with.** `reach_is_NOT_reflexive` sat in
   the return dict, so it ran *after* the cycle was added — at which point `wh` genuinely is reachable from
   `wh`. It read `False` for the right reason and the wrong question. §5u records this exact trap; this is
   the second time in this file.

Four planted-bug probes bite: reach implemented as adjacency (the transitive goal reads false and the plan
is never found), reach made reflexive, no cycle protection (`RecursionError`), and a surface that silently
drops the `+` (the goal is never carried out).

**What this unlocks, and what it deliberately does not.** `where` is now a **built-in KB** rather than
machinery — a `contains` edge and a small type library, authored in the ordinary surface, which is the
legitimate kind of shipping-with-the-engine (§5x). ⚠ Still unbuilt: the `what` and `when` readers, which
need no machinery at all (`types.recognize` and the ordering comparisons already exist) and only want a
verb. ⚠ And `via` returns a set-shaped answer for a caller that has somewhere to put one; it is
deliberately **not** wired into any path.

## 6i. ⭐⭐ THE WH-QUESTIONS — what / where / when, and they needed a verb (2026-08-01)

**182 checks, 0 FAILED.** New module `locate.py`; three more CNL verbs. §9 item 1, and the claim it rested
on — *no machinery needed* — held up under probing, which is not what usually happens here.

**⭐⭐ They are a different FORM, not a fifth force, and getting that wrong would have been the easy
version.** `goal` / `ask` / `why` / `plan` share one body because a goal, a question and an instruction are
the same set of constraints differing only in **force** (§5h). The obvious move was to add `what` as a
fifth verb on that body. It is not one: these have a **gap** in them, and answering one is not searching —
it is **locating a thing in an order the world already has**. So they take a different body (one bare name
per line) and they **answer** instead of recording. In the project's own vocabulary that is the *content*
axis moving where `ask`-versus-`goal` was the *force* axis.

| verb | the order it reads | the machinery, which already existed |
|---|---|---|
| `what` | subsumption | `types.recognize` (§5i) |
| `where` | containment | §6h's reach, walked backwards |
| `when` | temporal | comparisons on two endpoints |

⚠ **The three are not one operation and saying so would be too neat:** `what` compares a node against a
population of *types*, the other two against a population of *nodes*. What they really share is the part
that matters — each reads an order that is already there, so none of them searches.

**⭐⭐ `when` is SUGAR, and it is now CHECKED rather than argued.** §5x *measured* it as sugar and that was
still an argument. The check authors the same judgement twice — once as `locate.relate`, once as an
ordinary `type` block whose `Rel` says `first.end < second.start` — and requires them to agree. ⚠ **The
first version of that check was wrong and the type block was right**: `<` is strict, so it says `before`
and **not** `meets`, and I had lumped the two relations together. Three pairs now straddle the boundary in
both directions, which is a much better test than the one I meant to write. Allen's thirteen relations are
eleven comparisons on four endpoints and add no expressive power to what a schema could already demand.

**⭐ `where` is the caller `path.via` was written for and did not have.** §6h shipped `via` set-shaped and
deliberately unwired, because a *reference* denoting a set breaks `node_at`. A question is exactly the
position with somewhere to put one: *where is it* has no single answer — the parcel is in the box **and**
in the warehouse — so reach stays a predicate everywhere a single node is demanded, and the set surfaces
only here.

**⚠ The vocabulary is content; only the traversal had to be earned.** `by` names one hop **as walked from
the thing**, reusing `path.py`'s `^` for direction — so `by ^contains` climbs out of a container and
`by part_of` climbs the opposite convention, with the same traversal. Checked on a world written each way.
Without that, `where` would be about containment rather than about reach, and a domain word would have
leaked into the engine.

**⭐⭐ A READER RECORDS NOTHING, and that is §6g's rule applied to answers.** *Keep what you cannot
re-derive.* A reader's answer is a traversal away at any moment, so storing one could only ever let it
drift from the world it describes — precisely `types.tag`'s stamp still saying `car` after the wheel came
off (§5i). ⚠ **The contrast with `ask` settling by default is not an inconsistency**: a derivation *ran*,
and repeating it costs a search. Recomputing beats remembering exactly when recomputing is cheap. What
*does* reach the thread is the **question** — that it was asked is history — and never the answer.

**Five planted-bug probes, each biting a distinct key**, and the second has the ideal signature:

* `where` as one hop rather than reach → `AND_IT_REACHES_PAST_THE_IMMEDIATE_ONE` red;
* ⭐ a reader that **caches off-graph** → `THE_WORLD_IS_UNCHANGED_BY_ASKING` stays green, the answer still
  looks right, and only `AND_THE_ANSWER_FOLLOWS_THE_WORLD_WHEN_IT_MOVES` goes red. *That* key is the whole
  property, and a check asserting only "asking changes nothing" would have passed the bug;
* `relate` folding `meets` into `before` → the type-block agreement goes red;
* `where` returning a `set` → `nearest_first_because_it_is_not_a_set` red;
* a `_seal` that accepts an empty question → its refusal key red.

**⚠ And the §5u/§6h trap caught me for the third time in this file:** a count read *in the return dict*,
after an incomparable event had been minted, measured the omission rather than the placement. It read
`False` for the right reason and the wrong question. Both readings are now keys, taken in the right order.

**⭐ Verified against the consumer, which §9 said was owed.** `../pystrider` is **157 passed, 0 failed** —
and its previously-red pin (§6c, §5w's unset-register refusal) is **green**, fixed on their side. That debt
is closed; `Focus(g)` evidently reached them too.

## 6j. ⭐⭐ WITNESSES — a universal constraint stops being a yes/no (2026-08-01)

**184 checks, 0 FAILED.** `plural_step.md` slice A. Full reasoning there; the short version:

**The finding, measured before anything was built.** A universal is expressible today
(`has no file each a ungone_file`, measured as sugar in `not_supported.md`) and was **invisible to
planning**: against `d is a tidied_dir`, even a *singular* action that would certainly close it scored
**band 1**, where the same action against the equivalent singular constraint scored **4**. That is §5d's
founding defect one level up — *a goal that can only answer yes/no forces blind search* — and it is the
same *predicate-expressible, planning-half-missing* split §6h found for transitive reach.

`goal.witnesses` names the members that make a constraint false; `types.offenders` computes them.
Measured acceptance: **1 → 4**, with no plural machinery at all.

**⚠⚠ Getting the measurement right took two tries and the first proved nothing.** `relevance` binds
**mappings**, not raw nodes, so passing raw nodes collapsed *every* score to band 1 — including the
control. A measurement whose control does not light up is not a measurement.

**⭐ Only the too-many direction has witnesses, and the asymmetry is the open world.** A missing wheel does
not exist, so there is nothing to blame; that direction was already served from the other side by
`relevance`'s existential `mint` branch. Between them the two are covered, and conflating them would mean
inventing a node to blame — planted as a probe, and it turns exactly that key red.

**⭐ `relevance` kept its four-argument signature** by recovering the frame from its bindings rather than
accepting a `view` — a `view=` parameter would have to cross the `rank=` hook and `guideline.compose`, and
a module-level stash would be the hidden Python channel §6b exists to remove.

**⚠ Witnesses are derived, never stored**, over-ruling *keep it in the graph* on two precedents: §5f
refused to materialise expectations (hundreds of frames), and §5i's drift defect is exactly what a stored
witness list would be. What *did* come into the open is the **question**, previously buried in a local
`sum()` inside `types.fails`.

**Every measured search cost is unchanged** — guided vs blind still 2 vs 67, role paths still 3/10/10 —
which is what makes this additive rather than a re-tuning of §5d's hard-won bands.

## 6k. ⭐⭐⭐ GRANULARITY — the design was probed first, and two of its claims were wrong (2026-08-02)

`docs/microfunctions/granularity.md` is the design; this is what measuring it changed. The prompting
questions were ordinary product ones — *my plan is "book hotel, book flight" but booking a hotel is itself
several steps; plans get interrupted and detours are legitimate; to get to school from abroad I must fly
home first* — and the notable thing is that **every gap came out additive.** Nothing in three parts
contradicted the substrate: no change to `graph.py`, `types.py`, `workbench.py`, `execution.py` or the
pursuit phases, and two mechanisms *deleted*.

**⭐⭐ The principle the whole design reduces to, and it makes the demand a property rather than a feature:**

> **A level is judged by its own promise, at its own grain.** A level's promise is exactly its goal's
> constraints, and it is monitored by asking *that* promise — never by comparing what happened against what
> a different level planned.

**Refinement therefore cannot register as divergence**, because the parent never sees the child's actions
at all: "book hotel" is not a function call and has no trace to compare. ⚠ The way to get this wrong is to
monitor the **action trace**, which would make `search_hotels, pay, confirm` a divergence from an expected
`book_hotel` at step one. **Do not build a plan differ; there is no "right level" to find**, because you
never compare two levels.

### The three probes, and what they cost the design

**1. ✅ Better than hoped.** `types.fails` returns `{label: (expected, actual)}` — *which* requirement
failed — and `driver.proposals` already called it on every candidate and **discarded the dict**.

**2. ⚠ WRONG AS STATED, and the real defect is worse.** The design predicted a prerequisite would score
band 0. In the school scenario `fly_home` scored **band 4** — because `relevance` matched the **slot** and
never the **value**: the goal wants `where = school`, `fly_home` writes `where = home`, band 4. *The right
answer for a reason that does not generalise*, and the design had taken the right answer as evidence the
mechanism worked. The discriminating case is a prerequisite writing a **different slot** (`buy_ticket` sets
`ticket`), which scores 0 and ties with every idle operator.

> **⭐⭐ Band 4 is reachable only for the LAST step of a chain.** The guidance is one-step slot-matching
> lookahead; it had never once guided *toward a prerequisite*.

**⚠⚠ And what rescued it was an undeclared alphabetical tie-break** — `function.names` was `sorted()`, and
`buy_ticket` happens to sort before `idle*`/`nap`. Renamed `zz_buy_ticket`, cost went 3/3/3 → 7/11/17.
**The planner's cost depended on the name of a function.**

**3. The concurrency premise held, and two assumptions were wrong in opposite directions.** Two unrelated
pursuits interleave on one loop today, unchanged: 12 ticks, 8 switches, both goals satisfied in reality.
⭐ A stale precondition **is** re-checked at execution time (`fn.invoke` re-validates parameter types), so a
plan cannot act on a world it was not verified against — stronger than the design assumed. ⚠⚠ **But it
reported by raising, and the exception escaped `execution.step`, `pursuit_step` AND `loop.tick`**, stranding
the pursuit mid-`acting` and killing every other task on the agenda. Detection existed; recovery did not.

### The tie-break audit — it distorted the CONTROLS, not the treatments

Every recorded scenario re-measured under three orderings:

| | recorded | alphabetical | reverse | declaration |
|---|---|---|---|---|
| tower, **guided** | 2 | 2 | **2** | **2** |
| tower, **blind control** | 67 | 67 | **30** | **28** |
| Sussman, guided | 50 | 52 | **52** | **52** |
| threshold, paths/without/blind | 3/10/10 | 3/10/10 | **6/20/20** | 3/10/10 |

**⭐ Where band 4 is reachable the number does not move at all** — the band dominates the key and the
tie-break only breaks genuine ties. Where there is no guidance, the tie-break is the *entire* ordering.
**⚠ So §5d's headline is the one affected figure: 2-vs-67 is honestly 2-vs-28**, ~14x rather than 33x. The
finding survives; the magnitude was inflated ~2.4x by an arbitrary sort **inside the control**.

> ⭐ This is the same phenomenon as probe 2, not a second one: **the tie-break decides exactly where the
> guidance is absent.**

## 6l. ⭐⭐⭐ BUILT — a stale precondition is a deviation; ordering, values, and `unlocks` (2026-08-02)

**184 → 187 checks, 0 FAILED.** Four changes, all probed.

**1. `TypeViolation` → `deviation`** (`execution.step`, and `function.invoke` now attaches `param` / `want`
/ `violations` so the reactor does not re-derive the check). Nothing else changed — `recover`,
`_phase_acting` and `loop.tick` already knew what to do with a deviation. ⭐ **`result=None` turned out to
be load-bearing rather than a placeholder:** the call never ran, so there is no outcome to settle onto a
sibling's mappings, and `matching_alternative` *already* declines when `result` is `None`. A contingency is
correctly not offered and recovery goes to replanning — the honest move when the world has **moved** rather
than merely surprised us. That fell out; it was not arranged.

**2. `function.names` returns DECLARATION order.** ⚠ `driver.py` had documented this the whole time and the
code sorted. `guideline`, `mock` and `method` precedence are all declaration order and say so; functions
were the odd one out. ⚠ One check broke and **was right to**: §6f pinned the blind control at a literal
`67`, three times. *A pin on an arbitrary tie-break is the bug* — it now measures the full cost from its own
control run and asserts a **relation between two runs**, which is stable under any ordering.

**3. An `attr` effect carries the VALUE it writes.** `_effects` hardcoded `None`. The fourth slot is now
tagged by the first — object role for a `link`, value for an `attr`, `driver.UNREADABLE` when computed.
⚠ A sentinel and not `None`, because `None` is an ordinary attribute value.

**4. `unlocks` — the frontier key is `(expected, -band, -unlocks, depth)`.** A band classifies *this move
against the goal*; a prerequisite closes nothing, so it is band 0 **correctly**, and no refinement of a
match-quality scale can fix that — a prerequisite is not a worse match, it is a **different distance**.
Measured, school scenario, guided:

| library | before | after |
|---|---|---|
| prerequisite + 0 irrelevant operators | 4 | **3** |
| + 2 / + 6 / + 12 | 6 / 10 / 16 | **3 / 3 / 3** |

Flat, optimal, name-independent. Enumeration cost back within noise of §5m's figures.

### ⚠⚠ Three things the building found that the design did not

**(a) The cheap-looking version was 3.4x SLOWER.** Collecting misses during enumeration *reuses a value
already computed* — and puts a set insertion on the path taken by **most** candidate tests, which is what
enumeration mostly does. §5m's benchmark went 2.08 → 6.98 ms, and gating it by relevance only reached 6.30.
The fix inverts it: record only **which functions were blocked**, and recompute their requirements
afterwards. A blocked function contributed no proposal, so **blocked functions are few by definition** — on
the blocks world with 200 irrelevant nodes that is *zero* recomputation, because nothing relevant is
blocked there. The expensive case is exactly the case that needs the answer.

> ⭐ **Doing the work eagerly for everything cost more than doing it lazily for the few that need it, even
> though the eager version was reusing a value already in hand.** Reuse is not automatically the cheap side.

**(b) It scored zero on every proposal, silently, because two paths disagreed about which node they meant.**
Wants were keyed by the workbench **image**; `unlocks` resolved to the **original**. A no-op that looks
exactly like *"the idea does not help"*. The expression was written out **seven times** in `driver.py`; it
is `driver.stands_for` once now — the difference between a convention and a guarantee.

**(c) ⚠⚠ THE DOMINANCE INVARIANT IS OVER-DETERMINED, and the docstring claiming otherwise was wrong.**
`unlocks` said it cannot outrank a closing move *because `-unlocks` sits after `-band`*. It does — and that
is a **redundant second guard**, because `expected` is the key's first component and already folds in
`rank >= 4`. Probed three ways against a detour unlocking two requirements where the closing move unlocks
one: neutering `expected` alone changes nothing, swapping the components alone changes nothing, **only both
together** degrade the plan.

> ⚠ **A property enforced twice cannot be guarded by a check, and every single-line probe of it comes back
> green.** Worth knowing before someone simplifies one of the two and finds everything still passing.

⚠ And it left a question **named rather than settled**: below band 4, *"mentions the goal's label"* beats
*"would unblock something relevant"* — weak evidence beating derived evidence. Never argued, so left as
found and written down. Relatedly, **§32 of `granularity.md` argues bands 1–3 do far less than the name
suggests**: only `rank >= 4` reaches the key's first component, so the honest description is *one predicate
plus a five-value tie-break*, not a graded estimate.

## 6m. ⭐⭐ BUILT — a prohibition crosses a goal boundary; the other two sorts do not (2026-08-02)

**188 checks, 0 FAILED.** `goal.prohibitions` walks the ancestry; `goal.budget_of` does not, and says why.
`breached` read the goal's **own** constraints, so a ban on "arrange the trip" said nothing to the search
planning "get to school" underneath it. **A ban a child can sidestep is not a ban.**

| sort | crosses? | |
|---|---|---|
| `never` | **yes**, at any depth | a breach is a proof wherever it happens |
| `eventually` | **no** | discharged by *some* step *somewhere* below — inherited, every child would separately have to paint |
| `at_most` | **no, and REFUSED rather than omitted** | a budget counts at the grain of the level that declared it |

**⚠ The budget refusal is the interesting one.** Applying a parent's count to a child's *actions* would
break a limit the moment somebody authored a method — the limit's meaning would depend on how finely the
plan happened to be decomposed, which is the same error as monitoring the action trace. Copying it to each
child is worse: three children each spend the whole budget. Consuming it needs a level that knows how many
of **its own** steps have been taken — the decomposition rung that still has no state node (§6n).
**So it stays a gap, written down. A gap that is written down beats a wrong answer.**

⚠ **The control is a ban on an UNRELATED goal, not the absence of a ban.** Two worlds differing only in
whether the goal holding the prohibition is an *ancestor* is the only pair that tests ancestry; "banned"
versus "not banned" passes for an implementation that reads every goal in the graph. Probed: it does.

## 6n. ⭐⭐⭐ THE NEXT SLICE — the decomposition rung has no node (design done, not built)

`granularity.md` §2 and §7. **`driver.follow` is a Python `for` loop**, and it is now the outermost one.

| rung | state node | steppable |
|---|---|---|
| pursue a goal | `pursuit` | ✅ |
| **follow a decomposition** | **— none —** | ❌ a Python `for` |
| search for a plan | `search` | ✅ |
| replay a plan for real | `replay` | ✅ |
| run one function | `activation` | ✅ |

`loop.py` knows `pursuit` as a task kind and `_subtask` resolves its `search` or `replay`; nothing there
knows a goal can be **followed**. So a nested plan blocks the outer loop, and the system cannot answer
*"which step of the vacation are we on"* — **the same defect in its fourth incarnation**, after attention
(`thread.py`), the goal (`goal.py`) and deliberation (`search.py`). By now the shape of the fix should be
assumed rather than argued: a **`FOLLOWING` phase whose sub-task is the child pursuit**.

**⭐ Two properties fall out, and they are why a pursuit is the right carrier rather than a new `plan` node:**
depth costs **nothing in ticks** (one primitive step is still taken at the leaf, so a nested plan is exactly
as interruptible as a flat one), and `describe_pursuit` **recurses**, which is the whole of "track at the
right level" for free. A method yields *subgoals* and a search yields *frames*, so there is no single object
that is "the plan" at both grains — but a pursuit is *goal in, plan out, actions at the leaves* at every
grain, so it is the one thing that composes with itself.

⚠ It is also what **§6m's budget gap** and **`granularity.md` §4(b)** are both blocked on.

## 6o. ⭐⭐⭐ THE SURFACE ARC — a probe, two self-closing goals, one grammar, and the discourse (2026-08-02)

**How this started, and it is the reason the findings are worth trusting.** Not from a design doc: from
*"what would a user actually say to an agentic coding assistant?"*. Fourteen utterances, each pushed all
the way to execution rather than to the parser — `docs/microfunctions/probe_agentic_coding.py`, which
records four verdicts (`RUNS` / `PARSES` / `REFUSED` / `NO FORM`) and keeps the ones that were wrong.

⚠⚠ **`PARSES` was the dangerous verdict, and that is the headline.** Two utterances were accepted, planned,
and reported **done with an empty plan, having never looked**.

### (a) A knowledge goal that closes itself — FIXED

`repo.files known` — and the shape recurred **twice**, by two routes, in a function whose docstring already
records being caught once:

* the key names an **edge** (`repo.file known`): `holds` asks `g.attr(here, key) is not UNKNOWN`, and an
  edge label has no attribute slot at all;
* the key names **nothing** (`repo.files known`, a plain mistyped plural) — the half that actually bit,
  because *every typo behaves this way*.

⚠ Neither is a bug in `UNKNOWN`. Absence-means-*lacks-it* is deliberate, so the slot really was known; the
mistake was admitting a **relation, or a typo, into an attribute-shaped claim**. Both now refuse in
`goal.require_known`. ⚠ The refusal does **not** grant the capability: *"which files are in the repo"* still
has no form (G0/G1), and now says so instead of answering it wrongly.

### (b) A method step could not name a third individual — FIXED

`some <name> in <ref> by <link>` existed in `criterion` and not in `method`, so a decomposition whose steps
concern a third individual had no form — the gap `expert_judgement.md` §8f closed for criteria and never
carried across. Lifted. ⚠⚠ **Singular on purpose**: raising one subgoal per member is the first thing
`plural_step.md` §4 forbids, and slice A's witnesses already make *"do it to each"* plannable one member at
a time — measured again here.

⭐ **And the probe corrected itself twice, which is the part to imitate.** *"For each file, lint it"* was
first reported as a capability gap; it was the probe's own `max_depth` of 8 against a nine-cast plan, and
it plans fine at 12 — at **1124 imagined states**, so plurality is a **cost** problem, not a capability
one. The plural constraint was then measured at band 1 and is band **4**: raw nodes had been passed where
`relevance` wants mappings, the exact trap `plural_step.md` §1 records.

### (c) ⭐⭐⭐ ONE PROPOSITION GRAMMAR — `intake._shape`

A goal constraint, a method step and a `when`/`unless` condition were **three hand-written parsers** for
the same handful of claims, and they had drifted in four ways nobody chose: transitive `l+` in a goal only,
the five comparison operators in a `type` block only, `x is there` in a criterion only, negation in a
criterion only. One recogniser now; each family only decides what to *do* with what it recognised. Same
move `path.py` made one level down — *"It is one grammar because it used to be three."*

⚠⚠ **The transitive case nearly went silently wrong.** The parser change alone would have made
`when x contains+ y` parse while `criterion._holds` still compared **one direct edge** — accepted, meaning
something narrower. So the evaluator moved with the surface, using the same `path.reaches` `goal.holds`
uses, and `describe_test` renders the `+` back. Its check asserts it **evaluates**, with the same condition
minus the `+` as the control.

⚠ **Depth is deliberately NOT unified** — one hop in a goal and a step (`conflict.unsatisfiable` keys a
slot as `(subject, key)`), any depth in a condition (it only ever checks). Asserted by a check so a later
tidy-up cannot quietly widen it.

### (d) ⭐⭐⭐ DISCOURSE — `discourse.py`, and the correction that shaped it

`intake.read` built a goal, a criterion, a method, and recorded **nothing about the fact that somebody said
it** — measured: two blocks against a fresh thread left it holding only its opening entry. That is this
project's founding defect in a **fourth** place, after attention, the goal and deliberation.

**⭐⭐ An utterance is a WORLD event; the thread merely attends it.** The first version made it a thread
entry with the speaker as a **string attribute** (`by="user"`) — the standing rule broken in one line,
*never identify by name alone*. Harmless with one actor, wrong with three, and unable to represent an
external system or another agent at all. Now: utterances hang off a `conversation` under `root`, speakers
are **nodes**, and the thread holds ordinary `attend` entries pointing at them. ⭐ **The third `ENTRY_KINDS`
member the first version added was given back** — `thread.py`'s *"deliberately only two"* was right, and
the one-order property retraction needs survives, because an attention entry is in the same `step` edge.

**⭐⭐ Retract the utterance, NOT the world.** A withdrawn block stops being consulted, through one `live()`
filter in the three enumerators. It is **marked, never deleted**; nothing it concluded is unwound
(`REVISION 01` deleted TMS on purpose); nothing dispatched is reversed. `forget.py` already settled why —
retention defaults to KEEP because `why` and `conflict.interference` read history.

**⭐⭐ Authority is WORLD DATA.** *"Ignore that"* is not a global fact with three speakers; it is an act by
somebody, and whether it lands is a question of standing. Default: a speaker withdraws their own, and
anything else must be **said** — `authority(holder, over)`, transitive via `path.reaches`. ⚠ Before this,
anybody could withdraw anything: a policy nobody chose. ⭐ This is the **caller `not_supported.md` G7 was
missing**, whose deferral is on the stated grounds that *"neither has a caller"* — conditional, and the
condition is now met.

**⭐ Asking needed no new machinery: it is a DISPATCH**, `observes=True`. `answered` is separate from `ask`
because a person is not a function. ⚠ A docstring here claimed *"the planner structurally cannot ask"* and
that is **false** — the target is a question node minted fresh in the real graph, so `_in_workbench` never
fires. Latent rather than live (no ISA opcode reaches `ask`), and recorded as such.

### What this arc says about the surface

⭐⭐⭐ **The CNL is a programming language missing bind, branch and loop** — the three things the probe's
utterances failed on were exactly variable binding, conditional, and iteration. Bind is now done. ⚠ The
argument that the CNL should therefore *not* be a programming language was wrong and was withdrawn: recipes
and legal procedure are programs written in language. The real question is *which* — `.mf`/ISA is a program
the planner cannot see inside (`establishes` returns `unknown`), a method is one it can.

⚠ **SQL is the cautionary case, and it is precise**: its *expression* grammar composes across every clause,
its *clause* grammar is forty years of islands, and its answer to a limited execution model was a **second
language** (PL/SQL). One shape with several executors is the thing to aim at; one grammar per executor is
the failure.

**Verify:** `python -m microfunctions.selftest` → **202 checks, 0 FAILED**.

## 9. ⭐ WHAT TO DO NEXT (current as of 2026-08-02)

Ranked. Everything above §5 is history; this is the list.

**⭐⭐⭐ 0a. THE SURFACE ARC (§6o) IS A THIRD DONE.** In order, because each makes the next cheap:

1. **`type` and `prefer`/`avoid` onto `_shape`.** `type` is the interesting one — it holds the full
   operator set and the `relates` forms, so it is the position that could *supply* the widened comparisons
   to the others rather than merely being where they are legal.
2. **The typed consequent** — collapse `step` / `do` / a memory write into **conditions → consequent**.
   ⭐ This is the user's framing and it is what makes `remember` and `learn` cheap rather than two more
   islands: `learn` writes a **criterion**, so it needs no new family at all. ⚠ Open: whether a consequent
   is a fourth tagged shape or its own small grammar.
3. **The sidecar executor.** ⚠⚠ `loop.py` claims *"the Python-control-loop inventory is empty"* and **it is
   not true**: `criterion.decide` returns a closure that loops `for c in criteria(g)` to completion, once
   per imagined step, invisible to the agenda because it is a `propose=` **hook parameter** — the same
   hidden Python channel `plural_step.md` invoked to reject a `view=` argument. Deleting it is the vacuity
   test for the whole architecture: the claim becomes true for the first time.
   ⭐ The design (the user's): decision rules have the **same shape** as everything else and differ only in
   **execution** — a sidecar that runs to completion beside the loop that ticks. That resolves a standing
   contradiction between `loop.py` (*nothing uninterruptible*) and `expert_judgement.md` (*scheduler, not
   work, uninterruptible on purpose*): an unnamed exception is a leak, a named one is an architecture. ⚠ It
   is sound only because the sidecar **cannot dispatch** — atomicity is then structural rather than
   trusted, which is the same reason `while` is forbidden there.
   ⚠ Open: one agenda with a task whose `step` runs to completion, or a genuinely separate executor.

⚠ **Also open from §6o:** the discourse moves have **no CNL surface** — `retract` is a Python call, and
*"ignore that"* does not fit `<verb> <label>:` + body. That is a **shape** question, not a vocabulary one,
and `remember` may want the same bare-line shape. Decide it once, for all three.

**0. ⭐⭐⭐ THE NESTED PURSUIT — §6n, and it is the top of the list.** `driver.follow` is a Python `for`
loop and the last one; the decomposition rung is the only rung with no state node. Design is done in
`granularity.md` §7, and the shape should be assumed rather than re-argued — it is the same move §6c and
§6d already made twice. ⚠ **Two other items are blocked on it**: §6m's budget-across-levels gap, and
`granularity.md` §4(b) (a parent noticing its remaining plan is no longer viable). ⚠ Its check's vacuity
guard is that the outer loop must be able to **stop mid-child and describe the position at both levels** —
"behaviour unchanged" passes for a seam that does nothing (§5o).

**0b. Then the FOOTPRINT** (`granularity.md` §14–§15), which §6l **demoted from mechanism to
optimisation**: correctness already comes from the per-call re-check, so the footprint's only job is to let
a plan know it is stale *before* it gets there. ⚠ The re-check tests **parameter types**, so a plan
invalidated in a way no parameter type can express is still undetected — the same gap as
`granularity.md` §19 (a precondition cannot name an individual or relate two parameters), seen twice.

**1. ✅ DONE — see §6i.** `what` / `where` / `when` are CNL verbs (`locate.py`), and the *no machinery
needed* claim survived probing: `when`'s sugar status is now checked against an authored `type` block
rather than argued.

**1b. ⭐ THE PLURAL STEP — `plural_step.md` is the current arc.** Slice A is **done** (§6j). Next is
slice B (a distributive role, so a *plural* action becomes rankable too), then C (imagine/replay over N
members, which the loop arc makes nearly free), then D (surface). ⚠ The doc's four *do nots* are the
valuable part: do not expand at plan time, do not teach `_effects` to read loops, do not make the plural
step atomic, and measure `proposals` cost before and after.

**2. `PIN` is unexercised, and compacting old thread entries is the case that would make it matter.**
`forget.also=` exists and no check drives it. ⚠ Compacting the thread is also what would turn `observation`
from a *redundant* root into a load-bearing one (§6g) — so build the two together or neither.

**3. Sightings cover attributes only.** §6a's own gap: an absent *edge* has nowhere to hang a marker, so a
folder's **contents** cannot be observed the way its `count` can. `workbench.expectations` already faced
this and answered **qualitatively** ("files appeared", never how many); the same granularity should apply.

**4. `pursue` does not fork on mock outcomes**, so a plan the driver produced has no sibling branches and
`resume` can essentially never apply to one (§5g). The loop leans on replanning instead. Closing it is §5
item 4's question from the other side — *branch only where being wrong is expensive*.

**4b. ⚠ THE SUB-BAND-4 ORDERING WAS NEVER ARGUED (§6l).** Below band 4, *"mentions the goal's label"*
currently beats *"would unblock something relevant"* — weak evidence beating derived evidence. And
§32 of `granularity.md` argues bands 1–3 do much less than the name suggests, since only `rank >= 4`
reaches the key's first component. Decide it on a measurement or collapse them; do not leave it looking
settled.

**5. Copy-on-write, but MEASURE FIRST.** §6's known limit. The multiplier is workbench **stack depth**, not
the size of one copy, and copy-on-write implements exactly the same semantics rather than a smaller
boundary. `measure-before-optimizing-ugm`, and §5m's stronger version: *profile before choosing a lever,
even one you wrote down yourself after measuring.*

**Deliberately NOT on this list:** §6b's **(b)** — removing the loop opcodes. §6e probed all three of its
payoffs and they came out at zero, relocated, and moot respectively. Revisit only if untrusted `.mf` is
ever loaded, which is the same trigger §5y names for policing builtins.

⚠⚠ **`../pystrider` HAS NOT BEEN RE-RUN SINCE §6l, AND §6l CHANGED TWO THINGS THEY CONSUME.**
`driver.establishes` changed the shape of an `attr` effect (fourth element is now the value, not `None`)
and `function.names` changed enumeration order. Both are in the CHANGELOG; per the lesson below, that is
**not the same as telling them**, and the pins should be run. This is the first thing to do before any new
slice.

✅ The debt to `../pystrider` was CLOSED as of §6i. It was **157 passed / 0 failed** against this engine as of
§6i — the pin that was red (§5w's unset-register refusal, §6c) has been fixed on their side, and `Focus(g)`
evidently reached them. ⚠ The lesson it was recorded for stands: *predicting a consumer impact in a
CHANGELOG is not the same as telling the consumer*, and the pins should be run after every engine change,
as §5k did and §5w did not.

## 5. What to do next (HISTORICAL — see §9)

**2. ✅ DONE — see §5j and §5k.** Conflict detection landed (`unsatisfiable`, `interference`, and
`interference_between` for the compose-time case). Left here for the reasoning: The old rule engine surfaced two conclusions
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
- **⚠⚠ NOTHING FORGETS, and the loop arc made that measurable rather than theoretical.** Every computation
  is now a record — searches, candidates, trace steps, replays, bindings, pursuits, attempts, and the
  interpreter's own activations and registers — and none of it is ever dropped. Measured 2026-08-01 on the
  three-block world (80 nodes), carrying out three ordinary goals in one session:

  | after | nodes | grew by |
  |---|---|---|
  | the world alone | 80 | — |
  | "build a tower" | 259 | +179 |
  | "stack the other way" | 467 | +208 |
  | "put a on c" | 892 | +425 |

  **96 world nodes against 796 records — 8×, and the per-goal cost is rising.** ⚠ It is not a leak and
  `workbench.discard` is not the answer: these are the records that make the system able to say what it
  did and why, which is the whole point of materialising them. What is missing is the *other* half — §6a's
  retention vocabulary (KEEP / COMPACT / DROP / PIN) is **designed and inert**, and §6b's verb set lists
  `remember` / `forget` as "a slower clock" that the loop does not schedule. ⚠ And §6a already settled the
  hard part: **retention defaults to KEEP**, because dropping what was reasoned from can contradict
  conclusions already drawn — so this is not garbage collection, and anything that forgets has to justify
  itself against `why`, `memory.attribute` and `conflict.interference`, all of which read history.
- **Termination and conflict arbitration** are both open. The ISA fails loudly at `MAX_STEPS` as an honest
  stand-in for the first; nothing addresses the second.
- **The undo journal is transactional only.** A rollback boundary must never span a dispatch. Do not design
  around it; if nothing outside `selftest.py` uses it, delete it.
- **A reference reaches any depth in a `type` block, one hop in a `goal` or `method` one** — see §5v for
  why that is a refusal rather than an omission, and what has to change to lift it.
- **A type constrains ONE subgraph**, so `stack(b, onto)` still cannot declare `b ≠ onto`: two parameters
  are two subgraphs with no node above them to hang the demand on. `driver.proposals` enforces it.
  ⚠ **This is the same gap as the one §6l's precondition re-check cannot cover**, seen from the other
  side: a plan invalidated in a way no *parameter type* can express is invisible to the call-site check.
  `granularity.md` §19 proposes the fix and names where it lives — **the call**, which is the node above
  two parameters that §6 kept saying did not exist.
- **⚠ Enumeration order is now DECLARATION order, and it is load-bearing** (§6l). It decides which world is
  imagined first wherever two proposals tie. That is a *declared* default rather than a good one — an
  author who has not thought about order gets whatever order they wrote. ⚠ **Cost figures recorded before
  2026-08-02 were taken under the alphabet**; guided ones did not move, blind/unguided controls moved by up
  to 2.4x, and §5d's headline is honestly 2-vs-28 rather than 2-vs-67.
- **⚠ `driver.relevance` is one predicate plus a tie-break, not a graded estimate.** Only `rank >= 4`
  reaches the frontier key's first component; bands 1–3 differ from 0 only as an ordering. §32 of
  `granularity.md` argues they earn much less than the name suggests, and §9 item 4b carries it.
- **⚠ A budget (`at_most`) does not cross a goal boundary** (§6m). Prohibitions inherit; budgets and
  obligations do not. The budget case is a **refusal with a reason**, not an omission — consuming one needs
  the decomposition rung that has no state node yet (§6n).
- **A quoted literal cannot contain a space** anywhere in the CNL — every block splits its lines on
  whitespace. Pre-existing, now shared by one more surface.

## 7. Process notes that earned their place

**For every green, ask what would make it vacuous.** Five false or wrong greens were caught in one day: a
mis-credited wildcard made a closure check pass without checking anything; two sources wired to one gate
silently overwrote each other; a `None`-vs-`False` parameter tested the wrong world; a module-level check
list omitted every test defined below it; and one assertion reported `False` as a *value* rather than an
error, which a skim would have missed.

**Probe before believing the pattern.** Every claim in this session that was checked got weaker, and the
weakened version is the one worth keeping.
