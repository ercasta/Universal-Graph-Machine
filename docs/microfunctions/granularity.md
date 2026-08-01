# Granularity — plans at more than one grain, and monitoring that survives refinement

**Status: DESIGN, nothing measured.** Written against the state at HANDOFF §6j. Companion to
`deliberation.md` (which introduced methods and force) and to §5q/§5r/§5s of `HANDOFF.md`.

The prompting example: *plan a vacation — book hotel, book flight.* In execution, "book hotel" turns out to
be several smaller steps, which may themselves need planning. The demand is that **expanding a step into its
detail must not read as a divergence from the plan and must not trigger replanning.**

**§§12–17 extend this**, and they generalise it: plans are also interrupted by other actions and by events,
detours are *legitimate*, several unrelated plans are kept at once, and so **checking for divergence must
itself be a decision** rather than something that happens on every step. §1–§11 turn out to be the special
case where the interrupting plan is your own child.

---

## 1. What already exists, so that nobody rebuilds it

Most of the hierarchy is here. The gap is narrower than the question sounds.

| already built | where |
|---|---|
| a goal has a **parent**, ancestry, depth, and children | `goal.py` §5q |
| ordered subgoals (`then`/`sequence`), `BY_STEPS`, `ADVISORY`/`MANDATORY` | `goal.py` §5r |
| **authored decompositions that select themselves** — the kb saying what "book hotel" is made of | `method.py` §5s |
| decompose-or-search, once per goal | `driver.attempt` |
| walk the subgoals in order | `driver.follow` |
| plan / act / check / replan over graph-resident state | `driver` pursuit phases §6d |
| deviation, contingency, replan **within one plan** | `execution.py` §5a |
| constraints on the plan itself — `forbid_action`, `require_action`, `limit_steps` | `goal.py` §5e |

So "a hierarchy of plans" is **not** a new tree to build. The goal hierarchy *is* the hierarchy, and
`method.decompose` is how the kb populates it. Three things are actually missing, and only one of them is
mechanism.

## 2. The rungs, and which of them can say what they are doing

The arc from §6b was: *no Python control loop; every level's state is a node; one tick is one primitive
step.* Applied to granularity, the ladder from a wish down to a real action is:

| rung | state node | steppable |
|---|---|---|
| pursue a goal | `pursuit` | ✅ `pursuit_step` |
| **follow a decomposition** | **— none —** | ❌ `follow` is a Python `for` |
| search for a plan | `search` | ✅ `search.step` |
| replay a plan for real | `replay` | ✅ `execution.step` |
| run one function | `activation` | ✅ `Machine.tick` |
| reach the world | `dispatch` | — the irreversible edge |

**⭐ The decomposition rung is the one rung with no node**, and it is the outermost one. `loop.py` knows
`pursuit` as a task kind and `_subtask` resolves a pursuit's `search` or `replay`; nothing there knows a
goal can be *followed*. So `driver.follow` blocks the outer loop for the whole of a nested plan, and the
system cannot answer *"which step of the vacation are we on"* — it is doing something it cannot say it is
doing. **This is the same defect in its fourth incarnation**, after attention (`thread.py`), the goal
(`goal.py`) and deliberation (`search.py`). By now the shape of the fix should be assumed rather than
argued.

## 3. ⭐⭐ The principle: a level is judged by its own promise, at its own grain

Everything below is a corollary of one sentence, and the sentence is what makes the user's demand a
*property* rather than a *feature*:

> **A level's promise is exactly its goal's constraints. A level is monitored by asking that level's own
> promise, never by comparing what happened against what a different level planned.**

This is the same move `execution.step` already makes one rung down. A cast is checked against *its own*
declared return type, and `predicted_changes` is derived from *the two adjacent frames* — never from
anything a caller expected. Extending it upward costs no new idea.

### 3a. ⭐ The corollary the question was asking for

**Refinement cannot register as divergence, because the parent never sees the child's actions at all.** The
parent's step "book hotel" is not a function call and has no trace to compare; its promise is *the
subgoal's constraints hold when the step finishes*. Whether the child kept that promise in one dispatch or
in twelve steps with two internal replans is invisible above the boundary.

**⭐ The stronger form, and the thing to check:** *the parent's plan is invariant under refinement of its
steps.* The identical parent goal, run once where `book hotel` is a single dispatched call and once where a
method expands it into four steps, must produce the identical parent plan, the identical monitoring outcome,
and the identical replan count.

### 3b. ⚠ The way to get this wrong is to monitor the action trace

If the parent's monitor were *"did the observed `done` entries match my expected step names"*, then
`search_hotels, pay, confirm` against an expected `book_hotel` is a divergence at step one, and the system
replans a plan that is working. It would also be a labelling error in the §4-of-HANDOFF sense: the level of
an action is already entailed by its goal's ancestry, so stamping a level on the record would be asserting
what the structure entails, and could drift.

**Do not build a plan differ. Do not align two traces. There is no "right level" to find** — you never
compare two levels, so the question of which to compare at does not arise. The level that owns a failure is
the level whose own promise broke, and it is reached by walking up from the failure, not by choosing in
advance.

## 4. What a parent DOES monitor — two questions, and only two

Insulating the parent from refinement must not insulate it from consequences. There are exactly two things
a parent has to ask, and it asks them **after a step completes**, not during it:

**(a) Did this step keep its promise?** — `G.satisfied(child, under=subject)`. Already available. Not "did
it run the actions I imagined".

**(b) Is the rest of my plan still viable?** — the child may have kept its promise *and* wrecked the
remainder: book-hotel succeeds and spends the budget, so book-flight is now impossible. This is not the
child diverging. It is the parent diverging, and it needs a check the parent owns.

⚠ **(b) is where the honest limit sits.** The parent has no rehearsed intermediate states to compare
against, because `follow` never planned — it holds an ordered list of subgoals, not a frame path. Rehearsing
a decomposition is the same open question `execution.replan` declines (§5a) and `compile_episode` runs into.
So the cheap, sound version of (b), built from parts that already exist:

* the parent's **safety** constraints, re-asked over the trace so far — a breach is a proof (`G.breached`);
* `conflict.unsatisfiable` on each **remaining** step's goal — a decidable contradiction, so no false
  positives.

That detects *proved* invalidation and stays silent on *probable* invalidation. Say so out loud rather than
faking the second with a heuristic.

### 4a. The table that is the deliverable

| at the child | what the parent sees |
|---|---|
| internal deviation, recovered by a contingency, promise kept | **nothing** |
| internal replanning, promise kept | **nothing** |
| more or fewer real actions than anything predicted | **nothing** |
| a method chose a different route than last time, promise kept | **nothing** |
| promise not kept after its attempts are exhausted | step failed → the ladder, §5 |
| promise kept, but a parent safety constraint is breached | **parent** diverged → parent repairs the remainder |
| promise kept, but a later sibling is now unsatisfiable | **parent** diverged → parent repairs the remainder |

The four "nothing" rows are the answer to the question. The last two are why the answer is not simply
"don't monitor".

## 5. The escalation ladder — replan at the lowest level that broke

Replanning is not one thing, and the demand *"a detail expansion must not trigger replanning"* is really
*"replanning must happen at the level that failed"*. Ranked, innermost first:

1. **within a plan** — contingency then replan against the world as it is. `execution.resume` / pursuit
   phases. ✅ exists.
2. **at the step's own goal** — re-pursue it, up to `attempts`. ✅ exists.
3. **⭐ at the parent, keeping the decomposition — try a different METHOD for that step.** ❌ missing, and
   nearly free: `method.applicable` already returns *every* matching `(method, constraint)` pair in
   declaration order, and `driver.attempt` takes `hits[0]` and discards the rest. **The remaining applicable
   methods are to a goal exactly what `execution.alternatives`' sibling frames are to a plan** — a second
   route, authored in advance, already inspectable. Same shape one rung up.
4. **at the parent, dropping the decomposition** — `ADVISORY` fallback to searching the parent flat. ✅
   exists, but is all-or-nothing and skips rung 3 entirely today.
5. **above the parent** — the same ladder, recursively.

⚠ `MANDATORY` still cuts the ladder off at its own level: a procedure that cannot be followed **refuses**,
and *"could not do it"* beats *"did it another way"* (§5r). Rung 3 is legitimate under `MANDATORY` only if
the alternative method is itself sanctioned — an alternative *method* is still an authored route, so this
is arguably fine, but it is a policy decision and should be **declared, not inferred**, exactly as `force`
and `met_by` are.

## 6. ⭐⭐ Plan constraints across a boundary: prohibitions inherit, budgets divide, obligations discharge anywhere

`goal.breached` reads `constraints(g, goal)` — the goal's **own** constraints, with no ancestry walk. So
today a plan constraint on the vacation does not reach the search that plans the hotel. That is a real
defect and it is precisely a granularity defect: the parent constrains the plan, the child does the
planning, and the constraint does not cross the boundary. `goal.ancestry` makes the fix structural.

But the three sorts do **not** inherit alike, and §5e's safety/liveness distinction is what decides it:

| sort | across the boundary | why |
|---|---|---|
| `never` (prohibition) | **inherits unchanged** to every descendant | a ban that a child could sidestep is not a ban; and a breach is a proof at any depth |
| `at_most` (budget) | **divides — it is consumed, not copied** | inherited unchanged, three children each spend the whole budget and the parent's limit means nothing |
| `eventually` (obligation) | **must NOT inherit** | inherited, every child is separately required to paint; it is discharged by *some* step *somewhere* in the subtree |

⚠ **A budget counts at the grain of the level that declared it.** "At most 4 steps" on the vacation counts
*the vacation's own steps*, where a subgoal is one step — otherwise the meaning of a limit changes the day
somebody authors a method, which is the same failure as monitoring the action trace. A budget that is meant
to bound *real actions* is a different constraint and should be written as one rather than being inferred
from depth.

⚠ **Liveness is checked at the level that declared it, over the whole subtree beneath it** — `G.witness`'s
shape, not a per-child filter.

## 7. The mechanism: a pursuit whose sub-task is another pursuit

One structural change, and everything above becomes reachable.

`pursuit_step` already dispatches on a `phase` and advances a **current sub-task**: a `search` while
`PLANNING`, a `replay` while `ACTING`. Add a phase for a goal that is decomposed:

* **`FOLLOWING`** — sub-task is the **child pursuit** for the current step. One tick of the parent is one
  tick of the child. Position lives on the parent node (`at`, and a link to the current step), so
  `follow`'s Python `for` disappears the way `carry_out`'s `while` did in §6d.
* `loop.py` needs `_subtask` to resolve the child pursuit, and nothing else: a nested pursuit is already a
  `pursuit`, so `finished` / `describe` / `advance` all work unchanged.
* `driver.attempt` becomes the transition *into* `FOLLOWING` rather than a Python entry point.

**⭐ Two properties fall out, and they are the reason this is the right carrier:**

1. **Depth costs nothing in ticks.** One primitive step is still one primitive step, taken at the leaf. A
   refinement does not make the outer loop coarser, and a nested plan is exactly as interruptible as a flat
   one. ⚠ This is the invariant a check must pin: *the tick count for a goal is the same whether the work is
   nested or flat*, because nesting adds no work of its own.
2. **`describe_pursuit` recurses, and that is the whole of "track at the right level":**
   `pursuing 'vacation', step 1 of 2 ('book hotel'): pursuing 'book hotel', attempt 1: acting (step 2 of 4)`.
   Free.

**⭐ Why a pursuit and not a new `plan` node.** The hierarchy alternates: goal → *(method)* → subgoals →
*(search)* → a frame path → transformations → calls. A method yields **subgoals**; a search yields
**frames**. There is no single object that is "the plan" at both grains — but a pursuit is *goal in, plan
out, real actions at the leaves* at every grain, so it is the one thing that composes with itself. Minting a
`plan` node spanning levels would be inventing a second record of something the pursuit chain already is.

**⭐ And the multi-level execution record needs no new record either.** `_record_execution` already marks
what really ran with `for_goal`. *"What did the vacation actually do"* is then thread entries whose goal is
at-or-under the vacation goal — `G.ancestry`, already there. *"At which level"* is `G.depth_of`. Nothing is
stamped; the level is **recovered**, per §4 of HANDOFF.

## 8. Termination

§5q's warning becomes live here: parentage is set at mint so a **cycle is structurally impossible**, but
**depth is not bounded** — recursive decomposition mints a fresh goal each time and the chain grows without
looping. With nested pursuits that is an unbounded nest of tasks rather than a Python recursion, so it will
exhaust the loop's `max_ticks` rather than the stack, which is better but not an answer.

A decomposition bound read from `G.depth_of`, refusing **loudly** — the honest stand-in the ISA's
`MAX_STEPS` already is. ⚠ Note the common case is detectable more precisely: a method matching a goal that
`method.under_method` says it itself raised is self-recursion, and can be refused with a reason rather than
by running out of budget.

## 9. Slices

**A. The nested pursuit, behaviour-neutral.** `FOLLOWING` phase + `loop._subtask`, `follow` reimplemented
over it. Nothing new is decided; the same decompositions run to the same outcomes. ⚠ **The vacuity guard is
the whole slice** (§5o's lesson): "unchanged behaviour" passes for a seam that does nothing, so the check
must *also* require the outer loop to stop mid-child and `describe` the position at both levels.

**B. The two parent questions** (§4) — (a) is a call to `G.satisfied`; (b) is `G.breached` plus
`conflict.unsatisfiable` over the remaining steps. Plus the §3a invariance check.

**C. Constraint inheritance** (§6) — the ancestry walk, and the three sorts behaving differently.
Independent of A and B; could go first, and is the slice most likely to be *found* wrong by a check.

**D. Rung 3** (§5) — the next applicable method as a goal-level contingency. Small, given `applicable`
already returns the list.

**E. Termination** (§8).

## 10. Checks that would earn their place, with their vacuity guards

* **⭐ Invariance under refinement.** The same parent goal twice — once with `book hotel` as a single
  dispatch, once with a method expanding it into four steps. Same parent plan, same monitoring outcome,
  **zero** parent replans in both. ⚠ *Vacuity guard: assert the second run really executed more real
  actions.* Otherwise the two runs may have been the same run and the check proves nothing.
* **A consequence still escalates.** Same setup, but the child's expansion breaches a parent `never` or
  makes a later sibling unsatisfiable — the parent **must** notice. Without this, §3a's insulation is
  indistinguishable from not monitoring at all, and a check for the first property alone would pass a
  parent that is simply blind.
* **Prohibition inherits, obligation does not.** Two goals **structurally identical apart from the
  constraint sort** — the §5r discipline — required to behave oppositely across the boundary.
* **A budget is not spent twice.** A parent `at_most` with two children; inheriting it unchanged lets each
  child spend the whole thing. ⚠ *Vacuity guard: the flat version of the same plan must breach the same
  limit*, or the check is measuring the decomposition rather than the budget.
* **Depth costs no ticks** (§7). ⚠ *Vacuity guard: the nested run must really have been nested* —
  assert a child pursuit existed — or a run that silently flattened would pass.
* **Rung 3 before rung 4.** A goal with two applicable methods, the first non-covering: the second must be
  tried **before** the flat fallback, and the flat fallback must still be reachable when both fail.
  Precedent: §5s's completeness guard, *a goal solvable by search stays solvable*.

## 11. Open, and deliberately not answered here

* **Rehearsing a decomposition** — §4(b)'s honest limit. The parent detects proved invalidation only. The
  blocker is unchanged from §5a and is a real question about binding a pending call's output, not a missing
  function.
* **Whether a parent counts as met when its children are** stays `subgoals_met`'s answer: a **reader**, not
  a definition (§5q). Nesting does not change that, and deciding it here would settle it for every future
  method at the moment it is least clear which is wanted.
* **Thread volume.** Every level attends, every attempt attends, and nesting multiplies both. ⭐ A
  **completed subtree is the ideal `COMPACT` candidate** — keep the promise and the outcome, drop the
  internal search — which is exactly the case §9-of-HANDOFF item 2 says is missing to make `PIN` and
  thread compaction matter. Build them together, or neither.
* **Interference across levels.** `conflict.interference_between` takes two plans and reports a collision
  before either runs. Two *sibling subgoals* are two plans, so it should apply directly — unprobed, and
  probing it is cheap.

---

# Part II — detours, several plans at once, and checking as a decision

## 12. A detour is not a divergence, and the engine already knows the difference

Two things that look alike from outside and arrive by completely different routes:

* **a divergence** — *the world contradicted a prediction I made.* Recorded by `execution.step` when a real
  result fails its cast or an expectation, as a `deviation` node.
* **a detour** — *I chose to do something else for a while.* Nothing was predicted and nothing failed.

**⭐ Interleaving is already free and already non-divergent, and §6d is why.** A suspended replay is a node
holding its own position (`at`, `bound`, `notes`); a suspended pursuit is a node holding its phase. The
outer loop's round-robin advances one task and leaves the others *untouched* — and untouched is exactly the
state a plan should be in while something else happens. Nothing needs saving, because nothing was ever in a
Python local. **A task switch cannot register as a deviation**, because the deviating path is only reachable
by advancing the replay.

So the mechanism for detours is built. What is *not* built is the consequence.

## 13. ⭐⭐ The real problem: the world moves while you are not looking

A plan was verified against a world. While it is suspended — because a child is running, because another
pursuit got the tick, because an event arrived — that world changes, and **nothing re-verifies the plan on
the way back in.** `execution.step` checks the cast of the step it *just ran*; it never asks *"is what
remains still a plan for the world I am now in."*

This is the honest form of the question. It is not "should we check for divergence" in the abstract — it is:

> **How much has changed since this plan was last verified, and who changed it?**

And it makes checking a *decision* for a real reason rather than a preference: **checking costs**
(re-asking constraints, re-running `unsatisfiable` over remaining steps), the cost is paid per resumption,
and with several plans resumptions are frequent. A check that runs unconditionally is a check that will be
turned off.

## 14. ⭐⭐ Don't check on a clock — check when your FOOTPRINT was touched, by someone who is not you

Both halves of §13's question are answerable from records that already exist. No new mechanism.

**The footprint** — what this plan depends on and will touch — is derivable, never authored:

* what it already stands on: the replay's `bound` nodes name the real nodes it is holding;
* what it will touch: each remaining step's role nodes, via `driver.establishes` + `driver.role_node`, which
  §5k built to answer exactly *"which individual does this operation concern"*;
* for a *parent*, the remaining subgoals' constraint subjects and objects.

**Who touched it** is on the thread already. `_record_execution` marks what really ran with `for_goal` and
`done`, so *"what has happened since I was suspended"* is a walk from a remembered position, and
`G.ancestry` says whose doing it was.

> **A plan is stale when something outside its own subtree wrote inside its footprint. Otherwise it is
> still verified, and re-checking it is waste.**

Two unrelated plans have disjoint footprints, so the intersection is empty and resumption costs nothing —
which is the whole point, since unrelated concurrent plans are the common case.

**⭐ Attribution is the discriminator, and `memory.attribute` already is it.** §6a built *"was it me?"* as a
**derived** answer with no new record. A child touching its parent's footprint is the child doing its job —
expected, and handled by §4's two questions. An unrelated pursuit, or an observation that came from the
world, making the *identical write* is a different fact entirely. ⚠ These two cases must differ **only** in
attribution when they are checked, or the check is being decided by something else (§5s's vacuous negative).

**⭐⭐ And this collapses Part I into Part II.** A parent following a decomposition *is a suspended plan*.
§4's "is the rest of my plan still viable" and "is this resumed plan stale" are **the same check with a
different toucher** — one mechanism, two uses. That is the argument for building §14 rather than §4(b):
§4(b) is what you get for free once this exists.

## 15. ⚠⚠ Where checking may be deferred, and where it may never be

The decision to check needs a boundary, and the engine already draws exactly one hard line — `dispatch.py`'s
asymmetry, which §4 of `HANDOFF.md` calls the single most important safety property in the design.

> **Checking may be deferred indefinitely while thinking. It may never be deferred across the irreversible
> edge.** Re-validation is due **before the next dispatch**, not before the next tick.

That gives the decision a shape instead of a knob:

| a plan is | meaning | what may proceed |
|---|---|---|
| **verified** | nothing outside my subtree has touched my footprint since I was last verified | anything, including a dispatch |
| **stale** | something has | imagining, planning, ticking — but **re-validate before acting** |
| **diverged** | re-validation failed | the §5 ladder |

⚠ A stale plan is **not** a diverged one, and conflating them is the failure the whole document is about: a
detour makes plans stale by the dozen and almost none of them are wrong. Staleness says *"my evidence has
expired"*, divergence says *"my evidence was contradicted"*. Only the second is a reason to replan.

## 16. Several plans at once — what exists, and the one seam to add

**Multiple concurrent plans already work.** `loop.py` holds **one agenda**, `schedule` puts a task on it,
and a `pursuit` is a task kind. Two unrelated goals, one hierarchical and one flat, interleave today. Also
already present, and load-bearing the moment plans run concurrently: `conflict.unsatisfiable` (decidable
contradiction), `conflict.interference` (two goals that really did write one slot), and
`interference_between` (two plans, *before* either runs).

What is missing is **which task gets the next tick**. Round-robin is a fine default and should stay the
default. The precedent for the rest is §5o's: **add a seam that is inert by default and steer it with
data.**

⚠ **Frequency decides its shape** (`deliberation.md` §4, the rule §5m records paying to learn). An agenda
choice happens *every tick* — the highest frequency in the system, higher than the per-proposal ranker. So
it must be a **pure ranker over tasks**, structural and cheap, exactly as `guideline.py` is for proposals
and for the same reason. Method-matching-style work there would invert the cost of everything it saves.

⚠ **And it must only ever order, never exclude.** §5p's finding — that "advice cannot exclude" is a
guarantee of the *frontier's architecture*, not of the advisor — has to be re-established here rather than
assumed, because an agenda is not a frontier: a ranker that can starve a task forever *has* excluded it. The
guarantee wanted is that every scheduled task eventually ticks.

### 16a. Events do not interrupt anything

⭐ The deflationary framing, and it keeps the architecture whole: **an event is an observation; what
interrupts is a goal raised in response, competing on the one agenda.** No preemption, no interrupt
mechanism, no privileged path. §6b's *nothing is uninterruptible* gains its mirror — *nothing is
un-interrupting either*, because nothing can seize the loop.

The chain is then entirely made of parts that exist: an observation is recorded (`loop.look`, `memory`) → it
may be a **surprise**, which §6g already treats as the exception to forgetting → a surprise is precisely
"the world was not as recorded", so it is the strongest possible staleness signal under §14 → and it may
raise a goal, which is scheduled like any other.

⚠ **A scheduled task must be a retention root.** §6g made forgetting the default; a suspended pursuit that
gets forgotten cannot be resumed, and the failure would be silent and late. This is the natural first
consumer of `PIN` (§9-of-HANDOFF item 2, currently unexercised).

## 17. Slices, do-nots, and checks for Part II

**Slices.** F: the footprint, derived and unstored. G: staleness — the since-I-was-suspended walk, attributed
via `memory.attribute`. H: the dispatch gate of §15. I: the agenda ranker seam, inert. J: `PIN` for scheduled
tasks. ⚠ F+G+H subsume §9's slice B — build them in this order, not that one.

**Do not:**

* **do not preempt** — one agenda, everything is a task;
* **do not check on a clock or on every tick** — the cost is what makes it a decision at all;
* **do not treat a task switch as a deviation**, and do not let staleness reuse the `deviation` node;
* **do not store the footprint** — it is derivable, and a stored one would drift the moment a plan replans
  (the labelling error §4-of-HANDOFF records);
* **do not build a priority scheduler** — a ranker, inert by default;
* **do not let a plan be forgotten while it is on the agenda.**

**Checks that would earn their place:**

* **Two unrelated plans interleave and neither goes stale**, neither replans, and both complete. ⚠ *Two
  vacuity guards, and both are needed:* assert they really interleaved (tick order), **and** that a third
  plan sharing one node with one of them **does** go stale — a detector that never fires passes the first
  half on its own.
* **Attribution, and nothing else.** My own child's write does not mark me stale; an unrelated pursuit
  performing the **identical** write does. The two cases must differ only in who did it.
* **The gate holds.** A stale plan may keep planning and must not dispatch before re-validating. ⚠ *Guard:*
  plant the touch so that dispatching without re-validation does the visibly wrong thing in the world —
  otherwise the check passes against a gate that is never reached.
* **Detour and return.** Interrupt A with B, come back: A completes with the same plan, zero replans.
  ⚠ *Guard:* assert B really performed real actions, or A was never actually interrupted.
* **A suspended pursuit survives a `forget` pass**, and is resumable afterwards.
* **Starvation.** Every scheduled task eventually ticks under an adversarial ranker (§16's guarantee, which
  §5p's cannot be borrowed for).

---

# Part III — preconditions, and why the guidance is one-sided

The prompting example: *I have to get to school. At home, the plan is just "go to school". Abroad, I must
first fly home.* The plan's shape depends on the state, which is what preconditions are for.

## 18. Preconditions and effects already exist, and re-declaring them would be a regression

**A precondition is the parameter type; an effect is the return type.** `plan.py`'s docstring and §4 of
`HANDOFF.md` state it: `service(c: car) -> serviced_car` is a **cast**, and what it changes is merely how
the cast is achieved. `driver.proposals` will not even offer a function whose parameter type the candidate
fails, so a precondition is enforced before anything is imagined.

**⚠ The one thing not to do here is re-introduce declared effects.** §5d records the reason and it is not a
matter of taste: nothing declares effects, so `driver.establishes` reads what a function could make true
**off its stored body**, and *it cannot drift from the body because it is the body*. A declared effect is a
second statement of the same thing, and the two can disagree — which is `types.tag`'s `is_a` stamp all over
again (§5i: a cache of a claim must be re-validated on read; better still not to keep one). STRIPS-style
operator descriptions would undo a deliberate repoint.

**So the school example largely works today**, and the scope should be honest about that. From home, the
goal *at school* finds the one-step plan. From abroad, `go_to_school`'s parameter type is not satisfied so
it is never proposed, `fly_home`'s is, and the two-step plan exists and is found. Nothing is missing
structurally. **Two things are genuinely missing, and only the second is the interesting one.**

## 19. ⚠ Gap 1 — a precondition cannot name an individual, or relate two parameters

Goals may name individuals: `require_link(goal, me, "at", school)` is an ordinary link constraint between
named nodes. **Preconditions may not**, and it is a deliberate refusal with a good reason: a schema says
`{label: (kind, count)}` and never a *particular* target, because a schema is reusable and individuals are
not (§5d). So *"p is at home"* — a link to one particular place — has no form as a parameter type. That
asymmetry is exactly what the school example presses on.

The multi-parameter form is the same gap and is already documented as a known limit. `driver.proposals`
says so in its own docstring — *"`types.py` validates ONE argument at ONE call site by design, so a relation
between parameters has no declared form and has to be enforced here or in the body"* — and enforces only the
degenerate case, `len(set(combo)) != len(combo)`, in Python. `go(p, from, to)` needs *"p is at `from`"*,
which that cannot express, so today it is either a Python hack or a body that quietly does nothing (which
§5k's authoring rule already calls unexplainable).

**⭐ The fix has a place to live, and §6 of `HANDOFF.md` states the blocker in a way that names it.** The
recorded reason is *"two parameters are two subgraphs with no node above them to hang the demand on"* —
but there **is** a node above them: **the call**. A precondition over several parameters is a constraint on
the **binding**, not on any one argument, and that is a different thing from a type rather than a bigger
one. §5v already built the vocabulary: `path.py` is one reference language and `Rel` relates two places
inside one subgraph; this is the same idea across two.

Narrow and defensible: **only preconditions gain a form, and only for what a type provably cannot reach.**
Effects stay derived. And it deletes a hardcoded island (the composability principle's own test: a
mechanism hardcoded in Python is unreachable from the graph).

## 20. ⭐⭐ Gap 2 — the guidance reads EFFECTS and ignores PRECONDITIONS

This is the real content of *"we need cause and effect for planning"*, and it is not that preconditions are
absent — it is that **half the information in them is never used.**

`driver.relevance` scores a proposal by what it **establishes** against the goal's `unmet` constraints
(§5d). From abroad, the goal is *at school*. `fly_home` establishes *at home*, which is **not an unmet goal
constraint** — so it scores **band 0**, indistinguishable from painting a wall. The two-step plan is found
by *blind search*, not by reasoning. It works only because ranking never excludes (§5e), which is the
standing Sussman property doing the load-bearing work again.

> **⭐ An unsatisfied precondition of a relevant action is itself worth establishing.** That is the missing
> half: guidance runs forward from effects and never regresses through preconditions.

**How to do it without paying for it.** ⚠ `relevance` runs thousands of times per search (the frequency
rule, `deliberation.md` §4, and the mistake §5m records paying for once). So do **not** compute this per
proposal. Once per search node:

1. the **near-miss** actions — those whose effects reach an unmet goal constraint but whose parameter types
   are not satisfied here. ⭐ This is probably free: `types.violations` already reports **which**
   requirements failed, so *"one requirement away"* is a reading of an answer the enumerator computes
   anyway. Verify that before designing around it.
2. those failed requirements become a **derived secondary constraint set** — the things that would unlock
   a band-4 action;
3. a proposal that writes one of them scores in a band **below** real goal constraints and **above** zero.
   That fits the existing `band + offset` encoding (§5p) with nothing to tune.

⚠ **It must RANK, never filter.** A regressed precondition is a *guess about the route*; a safety breach is
a *proof*. §5e's sentence applies unchanged — **rank a guess, prune a proof** — and Sussman's anomaly is the
standing counterexample to any temptation to prune here.

⚠ **Bound the regression.** One level first. Unbounded means-ends regression is the same unbounded-depth
risk as §8's decomposition, and a cyclic library must refuse loudly rather than spin — `plan.py` already
carries a recursion guard on the set of types being satisfied, and the same discipline applies.

⚠ **The finding to assert is the BAND, not the step count** (§5k's correction, sharpened by §5l). Without
regression, *no proposal reaching `fly_home` can reach a non-zero band at all*, so the guided and blind
searches are the same search. That is the thing to check.

## 21. ⭐ And this closes back onto Part I

An unmet precondition raises a subgoal, ordered **before** the action that needed it. That is *the same
structure* `method.decompose` produces — an ordered subgoal under the parent, `then`-linked. So:

| a prerequisite step comes from | |
|---|---|
| **authored** — the kb says *book hotel* is four steps | `method.py` |
| **found** — the planner regresses through an unmet precondition | §20 |

Same shape, two sources. And per §3a a regressed prerequisite is a **refinement**: *fly home* appears
beneath *get to school* rather than beside it, so it is not a divergence from the plan and triggers no
replanning — which is the original demand arriving from a third direction. ⚠ It also means the depth bound
of §8 and the regression bound of §20 are **the same bound**, and should be one thing rather than two.

## 22. Not answered here

* **Deleted preconditions.** An action can *break* another's precondition — go to school, then fly abroad.
  §5l records that a redesign of `relevance` around this was nearly bought once, on evidence that turned out
  to be the irreproducibility artifact. At the plan level this is `conflict.interference`'s territory and
  the detector already exists; do not build a second one inside the ranker without measuring first.
* **Cost.** *Fly home* and *walk to school* are not comparable moves, and nothing here has a cost model —
  `plan.py` says so plainly ("no cost model, first solution wins"). Preference between rival routes is
  `guideline.py`'s job today, and that is an ordering, not a metric.

**Checks that would earn their place:**

* **The same goal from two states.** Subject at home → one step; subject abroad → two, with `fly_home`
  reaching a **non-zero band**. ⚠ *Vacuity guard: assert that without regression it is band 0*, or the check
  is measuring the search rather than the guidance.
* **A precondition relating two parameters is enforced.** `go(p, from, to)` refuses a binding where `p` is
  not at `from`. ⚠ *Guard: the parameter types alone must admit that binding*, or the check is passing on
  the type system and the new form is untested.
* **Regression ranks and does not filter.** A Sussman-shaped case where the regressed prerequisite scores
  low and must still be reachable.
* **A cyclic library refuses loudly** rather than spinning.

---

# Part IV — the recommendation, and one build order

## 23. ⭐⭐ This is NOT a redesign, and the evidence is that every gap came out additive

Three parts, three prompting questions, and **not one of them turned out to contradict the substrate.**
What was found instead, every time, was a structure already present with one thing missing beside it:

| the question | what was actually missing |
|---|---|
| a hierarchy of plans | one **node** on one rung — `follow` is a Python `for` (§2) |
| monitoring across levels | a **derived footprint** and a walk; no new record (§14) |
| several plans, detours | almost nothing — the loop already interleaves (§12, §16) |
| cause, effect, preconditions | **half a ranker** — guidance never regresses (§20) |

Nothing here proposes changing `graph.py`, `types.py`, `workbench.py`, `execution.py` or the pursuit
phases. Two mechanisms get *deleted* (`follow`'s loop, `proposals`' `b ≠ onto` hack) and one form is added
where a type provably cannot reach (§19). That is the signature of a design holding, not one due for
replacement — and this project's own history is the argument for taking it seriously: §5j, §5k, §5l and §5m
are all records of a plausible redesign that measurement did not support.

**⚠ Everything above is DESIGN and nothing in it is measured.** §5n flagged the same about
`deliberation.md`, and every claim in this project that has since been probed came out weaker. So the first
move is not a slice.

## 24. Probe first — three cheap measurements, each of which could kill a slice

Read-only, hours not days, and each has a decisive outcome:

1. **Does `types.violations` report which requirements failed, per candidate?** If yes, §20's near-miss set
   is a reading of something the enumerator already computes and the slice is small. If no, it needs the
   enumerator to carry more, and the cost argument has to be redone.
2. **Run the school scenario as it stands** — subject at home, then abroad. Confirm the two-step plan is
   found and that `fly_home` reaches **band 0**. ⚠ Assert the *band*, not the step count (§5k, sharpened by
   §5l). If it is already non-zero, §20 is wrong about the defect.
3. **Schedule two unrelated pursuits on one loop today** and see what actually breaks. Part II assumes the
   interleaving works and only the *consequences* are missing. That assumption is untested, and it is the
   one carrying the most weight.

## 25. The order, once the probes land

1. **§20 — regression through preconditions.** Best payoff per line, isolated to `driver.relevance`, and the
   school example is a ready-made check. It is the difference between planning that reasons and planning
   that searches.
2. **C — plan constraints inherit down the ancestry** (§6). Small, independent of everything else, and the
   slice most likely to be *found wrong* by its own check — which is why it goes early.
3. **A — the nested pursuit** (§7). Structural, behaviour-neutral, kills the last Python control loop, and
   is the enabler for the rest.
4. **F + G + H — footprint, staleness, the dispatch gate** (§14, §15). ⚠ These **subsume slice B**: once
   staleness exists, a parent's "is my remainder viable" is the same check with a different toucher. Build
   in this order, not B's.
5. **D — the next applicable method as a goal-level contingency** (§5). Nearly free.
6. **§19 — preconditions over a binding.** Deliberately last of the substantive slices: the largest surface
   change (a form, a surface, a refusal), and §20 may turn out to cover the cases that motivated it.
7. **I / J / E — the agenda ranker, `PIN` for scheduled tasks, the depth bound.** ⚠ §8's decomposition bound
   and §20's regression bound are **one bound**, and should be built once.

## 26. What would turn this into a real redesign

Stated in advance, so the answer is not decided by whoever is tired:

* **§4(b) cannot be done with proofs alone.** If detecting "my remainder is no longer viable" genuinely
  needs the parent to hold a *rehearsed* plan, then the workbench and plan representation are implicated,
  and that is the same open question `execution.replan` and `compile_episode` both decline. That is a
  redesign question, and it is the most likely one.
* **Concurrency cannot hold suspended plans safely.** If bindings can go stale in a way §14's footprint
  cannot detect, the one-agenda model is implicated rather than the monitoring.
* **Regression cannot be banded without exploding cost.** §5l nearly bought a `relevance` redesign once on
  evidence that turned out to be an artifact. If it happens again on real evidence, it is real.

---

# Part V — THE PROBES RAN (2026-08-01). Two claims weakened, two findings that were not predicted

Baseline before and after: **184 checks, 0 FAILED**. Nothing in the engine was changed; all three probes
are read-only. Per §7-of-HANDOFF the weakened versions are the ones worth keeping.

## 27. Probe 1 — ✅ and better than hoped

`types.fails` returns **`{label: (expected, actual)}`** — precisely which requirements failed — and
`violations` is `requirements` + `fails` composed. **`driver.proposals:121` already calls `fails` on every
candidate and discards the dict**, keeping only its truthiness.

> ⭐ The near-miss information §20 needs is *already computed on every candidate test in every enumeration*
> and thrown away. The slice is reading a return value, not adding a pass.

## 28. Probe 2 — ⚠ §20 WAS WRONG AS STATED, and the real defect is worse

**The prediction was that `fly_home` would score band 0.** It scores **band 4**:

```
subject at home    plan ('go_to_school',)                bands {go_to_school: 4, nap: 0}
subject abroad     plan ('fly_home', 'go_to_school')     bands {fly_home: 4, buy_ticket: 0, nap: 0}
```

**⭐⭐ Because `relevance` matches the SLOT, not the VALUE.** The goal wants `where == school`; `fly_home`
writes `where = home`; that is band 4. It reaches the right answer for a reason that does not generalise —
and the design took the right answer as evidence the mechanism worked.

**The discriminating case is a prerequisite that writes a DIFFERENT slot.** Add `buy_ticket(p: at_abroad)
-> ready_to_fly` writing `ticket`, and from abroad-without-a-ticket it scores **band 0, tied with `nap`,
`read`, and every idle operator in the library.**

> **⭐⭐ Band 4 is reachable only for the LAST step of a chain.** The guidance is one-step slot-matching
> lookahead. It has never once guided *toward a prerequisite* — the corrected form of §20's claim.

**⚠⚠ AND WHAT SAVES IT TODAY IS AN UNDECLARED ALPHABETICAL TIE-BREAK.** `fn.names` is sorted, so among
band-0 ties the alphabetically-first proposal is expanded first, and `buy_ticket` happens to sort before
`idle*`, `nap` and `read`. Rename it and the guidance is measurably gone:

| the prerequisite is named | +2 idle ops | +6 | +12 |
|---|---|---|---|
| `buy_ticket` | 3 | 3 | 3 |
| `zz_buy_ticket` | 7 | 11 | 17 |
| *(blind control)* | 32 | 92 | 1831 |

**The planner's cost depends on the name of a function.** Guided still beats blind — because once the
prerequisite is done, the *next* step is band 4 — but at the step that matters the search is unguided and
degrades with library size.

> ⭐ **§5l's sentence, landing in a new place:** *anywhere order reaches a ranking, a frontier or a "first
> match", that tie-break is load-bearing and nobody declared it.* §5l fixed order that was **unstable**.
> This order is **stable and arbitrary**, which is exactly why 184 checks pass over it and why a single
> scenario looks fine.

⚠ Method note: the first run of this probe wrote `SET F(p) "ticket" True` and the plan was unreachable.
`True` is not a `.mf` literal — the surface takes `true` — and `_operand` fell through to *bare word*,
silently yielding the string `"True"`. A silent acceptance at the boundary `asm.py` exists to police,
the same shape as §5k's `INVOKE`. Worth a refusal; not this arc's job.

## 29. Probe 3 — the premise holds, and TWO assumptions were wrong in opposite directions

**✅ Two unrelated pursuits interleave today, unchanged.** Both scheduled on one loop: 12 ticks, 8 task
switches, both goals satisfied **in reality**, both pursuits report done. §12 and §16 were right that the
mechanism is built.

**⭐ A stale precondition IS re-checked at execution time, and §15 underestimated the engine.** `fn.invoke`
re-validates the parameter type at the call, so a plan cannot act on a precondition that has gone false.
Planted directly — plan while abroad-with-ticket, run `fly_home` for real, let an event put the subject
back abroad, then step — and it is caught:

```
go_to_school(p=…): person#28 is not a at_home: {'@where': ("== 'home'", "'abroad'")}
```

**The dispatch gate §15 proposes already exists for TYPE preconditions.** That is a real strengthening.

**⚠⚠ BUT IT REPORTS BY RAISING, AND THE EXCEPTION ESCAPES THE OUTER LOOP.**

```
TypeViolation ESCAPED THE OUTER LOOP
pursuit phase: acting | done: False
describe: pursuing 'be at school', attempt 1: acting (step 2 of 2)
```

`execution.step` does not catch it, `pursuit_step` does not, `loop.tick` does not. The pursuit is stranded
mid-`acting`, and **every other task on the agenda dies with it** — which is precisely the failure mode
concurrency makes likely and single-plan testing cannot see.

> **⭐⭐ So staleness is DETECTED and NOT RECOVERABLE. It is an exception where it should be a `deviation`.**

This reshapes the whole of Part II. `_diverge` already records `frame`, `transformation`, `result` and
`minted`; `recover` already tries a contingency and then replans; `_phase_acting` already routes a failed
report. **Turning that `TypeViolation` into a deviation makes the entire existing recovery ladder apply to
staleness for free** — and it is a `try` around one call plus a `_diverge`, not the footprint machinery.

⚠ **The footprint (§14) therefore demotes from mechanism to OPTIMISATION.** Correctness comes from the
re-check that already happens at every call; the footprint's job is only to let a plan *know it is stale
before it gets there*, and to avoid re-validating when nobody touched it. That is worth having and it is no
longer load-bearing. ⚠ It also does not cover everything: the call-site re-check tests **parameter types**,
so a plan invalidated in a way no parameter type expresses (§19's gap — an individual, a relation between
two parameters) is still undetected. §19 and §29 are the same gap seen twice.

## 30. ⭐ The revised order

§25 was written before the probes and is superseded.

1. **✅ DONE — see §33.** Catch `TypeViolation` at the call site and record a `deviation` (§29).
2. **§20 regression, in its corrected form** (§28) — guide toward a prerequisite that writes a *different
   slot*, using the `fails` dict probe 1 found is already computed. ⚠ The check must **rename the
   prerequisite to something alphabetically late**, or the alphabetical tie-break passes it for free. That
   guard is now mandatory on any guidance check in this repo.
3. **Declare the tie-break** (§28). Independent of everything, and the finding most likely to be quietly
   distorting other measurements in this repo.
4. **C — plan constraints inherit** (§6), unchanged.
5. **A — the nested pursuit** (§7), unchanged.
6. **F/G/H — footprint and staleness**, now as an optimisation over 1, not a mechanism.
7. **D**, then **§19**, then **I / J / E**.

## 31. The tie-break audit — it distorts the CONTROLS, not the treatments

`function.names` is `tuple(sorted(...))`. Every recorded scenario re-measured under three orderings
(alphabetical as shipped / reverse alphabetical / declaration order):

| scenario | recorded | alphabetical | reverse | declaration |
|---|---|---|---|---|
| tower, **guided** (§5d, §5l) | 2 | 2 | **2** | **2** |
| tower, **blind control** (§5d) | 67 | 67 | **30** | **28** |
| Sussman, guided (§5e, §5p) | 50 | 52 | **52** | **52** |
| threshold, paths (§5k) | 3 | 3 | **6** | 3 |
| threshold, without paths (§5k) | 10 | 10 | **20** | 10 |
| threshold, blind (§5k) | 10 | 10 | **20** | 10 |

*(Sussman at 52 rather than 50 is this probe's reconstruction of the world, not a discrepancy.)*

**⭐ The pattern is exact and it is reassuring in the direction that matters.** Where **band 4 is reachable
the number does not move at all** — the band dominates the key and the tie-break only breaks genuine ties.
Where there is **no guidance**, the key is `(0, 0, depth)` or all-band-0 and **the alphabet is the entire
ordering**.

**⚠ So the one materially affected figure is §5d's headline ratio.** Guided-vs-blind on the tower is
recorded as 2 vs 67, a 33× win. Under declaration order the *control* is 28, so the honest claim is **2 vs
28, ~14×**. The finding survives — guidance genuinely wins, and by a wide margin — but the magnitude was
inflated ~2.4× by an arbitrary sort inside the control. §5k's ratios are preserved under scaling (3/10/10 →
6/20/20), and §5k already says its finding is the *band*, not the count.

**⭐ And this is the SAME phenomenon as §28, not a second one:** *the tie-break decides exactly where the
guidance is absent.* Probe 2's prerequisite is band 0 among band-0 ties, so it is all tie-break; a blind
control is all tie-break by definition.

**⚠ The repo has two conventions for precedence among authored things, and they disagree.**
`guideline.py`, `method.py` and `mock` all use **declaration order**, documented as deliberate and free via
`of_kind`'s mint order. `function.names` sorts. And `driver.py`'s own module docstring already claims
*"candidate ordering is declaration order"* — **which is not true of the code**. Making `names` return
`of_kind` order fixes the docstring, adopts the convention the rest of the engine states, and replaces an
undeclared tie-break with a declared one. ⚠ It will move recorded blind-control figures; per the table
above it moves no guided one.

## 32. ⭐⭐ Do we need bands? — one predicate earns its place, the scale does not, and the SHAPE is wrong

`relevance` returns 0–4 (4 exact, 3 both individuals wrong roles, 2 one individual, 1 right label, 0
nothing). Two facts decide the question:

1. **Only `rank >= 4` affects the frontier's first key component.** `expected = len(open_now) − (1 if
   rank_here >= 4 else 0)`. Bands 1/2/3 differ from 0 **only** as the second component — a tie-break, which
   §31 shows is then re-broken by the alphabet anyway.
2. **§5p requires the band to dominate** `band + offset`, so the scale is *an ordinal encoding of an order,
   not a weight* — nothing is tunable, by design.

> **So the honest description is: one PREDICATE ("does this close an open constraint?") plus a five-value
> tie-break.** It is a classifier, not a heuristic — and it was never claimed otherwise, but calling it
> "four bands" makes it sound like a graded estimate that it is not.

**Keep the predicate.** §31 measures it as the one thing that is order-robust, and §5d's 2-vs-28 is real.
**Bands 1–3 are doing far less than the name suggests** and should be justified on their own evidence or
collapsed; §5k's own note that "band 4 versus band 3 is the one that earns its place" already hints at it.

**⚠⚠ But the real answer is that the band is the wrong SHAPE for what §28 needs.** A band classifies *this
move against the goal*. A prerequisite is not a worse match — it is a **different distance**, and no
refinement of a match-quality scale can express *"closes nothing, but puts a band-4 move within reach"*.
That is why `buy_ticket` and `nap` are indistinguishable: they are equally *unrelated*, and correctly so.

**⭐ The proposal, and it is additive rather than a redesign.** Add a component to the frontier key derived
from the near-miss dict probe 1 found is already computed:

```
key = (expected, -band, -unlocks, depth)
      #                  ^ how many currently-unproposable band-4 actions this move would make proposable
```

* it **cannot demote a band-4 move** — it sits after the band, so §5p's dominance invariant is untouched;
* it **ranks, never filters** — Sussman is unaffected, since it only ever orders;
* it is **derived, not authored, and not a weight** — `fails` already returns which requirements failed on
  every candidate in every enumeration;
* it makes `buy_ticket` beat `nap` **for a stated reason**, which is exactly what §31 says the ordering
  currently lacks.

**⚠ One defect found on the way, and it is small and separate.** `_effects` records a `SET` as
`("attr", key, subject_role, None)` — **the value is hardcoded `None`** even when it is a static literal in
the instruction. So an attribute effect carries its slot and its subject but never what it writes, which is
why `fly_home` scores band 4 for writing `where = home` against a goal wanting `where = school`: *right
label, right subject, value never consulted.* Link effects **do** carry both roles, so link constraints are
checked exactly and attribute constraints are not. ⚠ Fixing it would make band 4 truthful and, on its own,
make the school scenario *slower* — the guidance that is currently accidental would have to be replaced by
the `unlocks` component above. **Build the two together, or neither.**

## 33. ✅ BUILT — a stale precondition is a deviation (2026-08-01). 185 checks, 0 FAILED

Two lines of mechanism, one check, three planted-bug probes.

* `function.invoke` attaches `function` / `param` / `want` / `violations` to the `TypeViolation` it raises,
  **so the reactor does not re-derive the check** — a second implementation of "which parameter failed and
  how" is precisely the drift this codebase keeps recording.
* `execution.step` catches it and calls `_diverge`. Nothing else changed: `recover`, `_phase_acting`,
  `pursuit_report` and `loop.tick` all already knew what to do with a deviation.

**⭐ `result=None` is load-bearing, not a placeholder.** The call *never ran*, so there is no real outcome
to settle onto a sibling's mappings — and `matching_alternative` already declines when `result` is `None`.
So a contingency is correctly not offered and recovery goes to replanning, which is the honest move when
the world has *moved* rather than merely surprised us. That fell out; it was not arranged.

Measured end to end: the world moves under a two-step plan mid-flight, the plan diverges instead of
crashing, the pursuit replans from the real state and succeeds on attempt 2, and the unrelated plan
sharing nothing with it completes for real.

### ⚠⚠ And the check's own headline guard was VACUOUS on its first version

The guard that matters is *"the other task on the agenda survived"*, since a wrecked agenda is invisible to
any test that schedules one thing. The planted-bug probe — restore the pre-fix behaviour, let the exception
escape — turned **eight** keys red and **left that one green.**

**Because the control finished too early.** The box plan was one cast, so it completed before the school
plan reached the act that diverged; "it survived" was true of a task that had nothing left to survive. The
fix is that the control must still be **running** at the moment of the failure: the box is now a three-cast
chain, and the check records `not finished(box)` **at the tick the deviation appears**, not afterwards.
Re-probed: that key and `and_it_really_acted` now go red with the rest.

> ⚠ **A control that has already finished is not a control.** `THE_OTHER_TASK_SURVIVED` and
> `THE_OTHER_TASK_WAS_STILL_RUNNING` look like the same assertion and only one of them tests anything —
> the §7 lesson in a form it had not taken before: *the vacuity was in the control's timing, not in the
> assertion*.

⚠ Not closed by this: the re-check is on **parameter types**, so a plan invalidated in a way no parameter
type can express is still undetected — §19 and §29 remain the same gap seen twice.

## 34. ✅ BUILT — the ordering, the value, and `unlocks` (2026-08-01). 187 checks, 0 FAILED

The three changes §32 said to build together, built together. The school scenario, guided:

| library | before | after |
|---|---|---|
| prerequisite + 0 irrelevant operators | 4 | **3** |
| + 2 | 6 | **3** |
| + 6 | 10 | **3** |
| + 12 | 16 | **3** |
| *(blind control)* | 12 → 1512 | unchanged |

**Flat, optimal, and name-independent.** Enumeration cost is back within noise of §5m's figures.

**1. `function.names` returns declaration order.** `driver.py` had documented this the whole time and the
code sorted. Recorded numbers moved exactly as §31 predicted: the blocks blind control 67 → **28**, guided
unchanged at 2, Sussman unchanged. ⚠ One check broke, and it was right to: §6f pinned the blind control at
a literal `67`, three times. **A pin on an arbitrary tie-break is the bug**, so the check now measures the
full cost *from its own control run* and asserts a relation between two runs — stable under any ordering,
because both runs share it.

**2. An `attr` effect carries the value it writes.** Fourth slot tagged by the first: object role for a
`link`, value for an `attr`, `UNREADABLE` when computed. Four checks pinned the old `None` and now assert
the value, which is strictly more than they said before.

**3. `unlocks`.** ⭐ Its input was already being computed: `types.fails` returns *which* requirement failed,
and enumeration discarded the dict.

### ⚠⚠ Three things the building found that the design did not

**(a) The cheap-looking version was 3.4× slower.** Collecting misses during enumeration reuses a value
already computed — and puts a set insertion on the path taken by *most* candidate tests, which is what
enumeration mostly does. §5m's benchmark went 2.08 → 6.98 ms, and **gating it by relevance only got to
6.30**. The fix inverts it: record only *which functions were blocked*, and recompute their requirements
afterwards. **A blocked function contributed no proposal, so blocked functions are few by definition** —
on the blocks world with 200 irrelevant nodes that is *zero* recomputation, because nothing relevant is
blocked there. The expensive case is exactly the case that needs the answer.

> ⭐ **Doing the work eagerly for everything cost more than doing it lazily for the few that need it, even
> though the eager version was reusing a value already in hand.** Reuse is not automatically the cheap side.

**(b) It scored zero on every proposal, silently, because two paths disagreed about which node they meant.**
Wants were keyed by the workbench **image**; `unlocks` resolved to the **original**. A no-op that looks
exactly like "the idea does not help". The expression was written out seven times in `driver.py`; it is
`stands_for` once now — *the difference between a convention and a guarantee*.

**(c) ⚠⚠ The dominance invariant is OVER-DETERMINED, and the docstring claiming otherwise was wrong.**
`unlocks` said it cannot outrank a closing move *because `-unlocks` sits after `-band`*. It does — and that
is a redundant second guard, because `expected` is the key's first component and already folds in
`rank >= 4`. Probed three ways against a detour unlocking **two** requirements where the closing move
unlocks one: neutering `expected` alone changes nothing, swapping the components alone changes nothing,
**only both together** degrade the plan.

> ⚠ **A property enforced twice cannot be guarded by a check, and every single-line probe of it comes back
> green.** Worth knowing before someone simplifies one of the two and finds everything still passing.

⚠ And it left a question **named rather than settled**: below band 4, "mentions the goal's label" currently
beats "would unblock something relevant" — weak evidence beating derived evidence. Never argued, so it was
left as found and written down.

### ⚠ Two checks whose first version proved nothing

Both were caught by probing, neither by the green — §7 again, twice in one slice.

* the detour written to test dominance first wrote only `where`, scoring the **same** unlock count as the
  closing move, so no inversion of the key could separate them;
* `WRITING_THE_WRONG_VALUE_IS_NO_LONGER_BAND_4` compared two `dict.get` defaults, because `fly_home` is not
  offered at all in the world it was asked about. Ranking two proposals needs a frame where **both are
  offered**.

## 35. ✅ BUILT — a prohibition crosses a boundary, and the other two sorts do not (2026-08-01). 188 checks

Slice C. `goal.prohibitions` walks the ancestry; `goal.budget_of` does not, and says why.

**⭐ The three sorts behaving differently is the whole content**, and §6 predicted it correctly:

| sort | crosses? | |
|---|---|---|
| `never` | **yes**, at any depth | a breach is a proof wherever it happens |
| `eventually` | **no** | discharged by *some* step *somewhere* below — inherited, every child would separately have to paint |
| `at_most` | **no, and refused rather than omitted** | a budget counts at the grain of the level that declared it |

**⚠ The budget is the interesting refusal.** Applying a parent's count to a child's *actions* would break a
limit the moment somebody authored a method — the limit's meaning would depend on how finely the plan
happened to be decomposed, which is the same error as monitoring the action trace (§3b). Copying it to each
child is worse: three children each spend the whole budget. Consuming it properly needs a level that knows
how many of *its own* steps have been taken — the decomposition rung that still has no state node (§2).
**So it stays a gap, written down.** A gap that is written down beats a wrong answer.

**⚠ The control is a ban on an UNRELATED goal, not the absence of a ban.** Two worlds differing only in
whether the goal holding the prohibition is an *ancestor* is the only pair that tests ancestry — comparing
"banned" to "not banned" passes for an implementation that reads every goal in the graph. Probed: that
implementation turns exactly those three keys red.

⚠ **And a probe found the check reporting an ERROR where it should report a red key.** The over-broad
version left the plan empty and `plan_other[0]` raised `IndexError` — counted by the harness, but as a
blow-up rather than as *which property failed*. §5g's lesson has a mirror: **a red key beats an exception
just as it beats a quiet `False`.** Indexed as `plan_other[:1]` now.
