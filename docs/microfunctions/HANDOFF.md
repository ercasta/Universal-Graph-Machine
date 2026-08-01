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
python -m microfunctions.selftest      # 141 checks, 0 FAILED
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
| `goal.py` | a wanted state as **constraint nodes**; `unmet` drives planning; **hierarchy** gives context |
| `driver.py` | **the outer loop** — pursue a goal by imagining; the plan is *found*, not built |
| `intake.py` | **the border** — one closed CNL for goals, guidelines and methods; refuses |
| `conflict.py` | contradictory goals, and **interference** between goals over one slot |
| `guideline.py` | **authored preference as data** — reorders within a band, can never exclude |
| `method.py` | **authored decompositions as data** that select themselves; prune on *authority* |

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

**148 checks, 0 FAILED.** New module `path.py`; `types.py` widened; `type` is the eighth CNL verb.

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
worth keeping:** `conflict.py` keys a contended slot by `(subject, key)` and would read two wheels'
pressures as one slot; `query.settle` writes with `g.put(subject, …)` and would land the answer on the base
rather than on the node the reference reaches. A type schema has neither problem **because it only ever
checks**. Depth is available where it is correct, refused loudly where the machinery behind it has not
caught up, and the boundary is a table in `intake.py`'s docstring rather than folklore.

**Next, if this is picked up:** teach `conflict.py` and `query.settle` a navigated subject, then the goal
and method rows of that table open up. `driver.relevance` would also rank a navigated goal constraint at
band 4 instead of 3, since `establishes` already speaks in the same paths — that is the interesting half.

## 5. What to do next

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
- **Termination and conflict arbitration** are both open. The ISA fails loudly at `MAX_STEPS` as an honest
  stand-in for the first; nothing addresses the second.
- **The undo journal is transactional only.** A rollback boundary must never span a dispatch. Do not design
  around it; if nothing outside `selftest.py` uses it, delete it.
- **A reference reaches any depth in a `type` block, one hop in a `goal` or `method` one** — see §5v for
  why that is a refusal rather than an omission, and what has to change to lift it.
- **A type constrains ONE subgraph**, so `stack(b, onto)` still cannot declare `b ≠ onto`: two parameters
  are two subgraphs with no node above them to hang the demand on. `driver.proposals` enforces it.
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
