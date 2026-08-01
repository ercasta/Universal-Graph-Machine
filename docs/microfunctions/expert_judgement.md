# Expert judgement — an ordered list of criteria

> **Status, 2026-08-01: §1's seam is BUILT (`driver.Call`, `189 checks, 0 FAILED`); §§2–7 are still
> proposals.** Three measured results overturn things argued earlier in this same document:
>
> 1. **Two criteria** take Sussman from **52 imagined states to 4** and a four-block problem from **378 to
>    8 with a shorter plan**. Expert judgement works, and cheaply.
> 2. **The loop is not needed.** `path.via` plus a selector reproduces a hand-rolled `while` *exactly*, so
>    **§4 is over-stated** and §8.4 corrects it: a *set position with a selector*, not iteration.
> 3. **⭐⭐ Real pruning is measurably worse than ranking the same knowledge** (134 imagined against 8 on
>    four blocks) — because a rank informs every choice on the frontier and a prune informs only the next.
>    §8b. This is a measurement; §2's objection and its withdrawal were both arguments.
> 4. **⭐⭐⭐ At scale, criteria make the search SIZE-INDEPENDENT** — 5 imagined states for every world from
>    5 to 20 blocks, while the engine's own guidance falls off a cliff between 6 and 7 and stops finding a
>    plan at all. ⚠ But **all the residual cost is enumeration, and `Call` does not touch it**: `_offer`
>    builds the O(N²) product before `decide` is ever consulted, so the seam is in the wrong place. §8c.
> 5. **⭐⭐⭐ `propose` puts it in the right place — BUILT.** Same knowledge asked before the product:
>    **6.6× faster at sixty blocks**, and *zero* proposals built on Sussman. The suppressed enumeration is
>    **deferred, not skipped**, so a wrong criterion cannot make the goal unreachable — ⚠ though it does
>    cost **plan quality**, which §2 claimed was free. §8d.
>
> 6. **⭐⭐⭐ IT IS AUTHORABLE — `criterion.py` + one verb on the one CNL.** Three criteria in text drive
>    the search to **4 imagined states and ZERO proposals built at sixty blocks** (0.04s against `rank`'s
>    8.59s). A criterion's variables come from an **unmet goal constraint**, which is also §7's index key.
>    §8e.
>
> The ⚠ marks are the load-bearing content.

Written out of a design conversation on 2026-08-01. It answers the question `deliberation.md` §10 left
open — *"what is a condition written in?"* — and in doing so **knowingly reverts** that section's
pattern-not-program decision. §5 records what that costs.

---

## 1. The shape

An ordered list of **criteria**. Each takes two parameters:

| parameter | what it is |
|---|---|
| `goal` | the goal being pursued, or nothing |
| `context` | a node, navigated freely |

and returns either **a bound call** — `stack(a, b)`, a function with its arguments denoted — or **one of
the five existing verbs** (`EXPAND` / `DECOMPOSE` / `COMMIT` / `SENSE` / `REFUSE`), or nothing.

*"Think more"* is `EXPAND`, which is already the default. So both sides of the return are closed sets and
nothing new is needed there.

**The first criterion that speaks wins.** Precedence is declaration order — the same free ordering
`guideline.advice()` already uses, and the same reason `deliberation.md` §5 gives for rejecting weights:
weights are the thing that needs tuning.

It sits on `driver.pursue(decide=...)`, the seam built inert in slice 1 (`deliberation.md` §11).

**✅ BUILT 2026-08-01 — `driver.Call`.** `decide` may now return `Call(function, bindings, why)` and the
loop substitutes it for the ranked choice. Denoting the arguments was already solved (`path.py`, the one
reference language). See **§8b** for what it validates, the livelock it exposed, and the measurement that
says pruning is *worse* than ranking the same knowledge.

## 2. It prunes where it speaks, and `relevance` ranks where it is silent

The standing rule is *rank a guess; prune a proof*, and the first version of this design was rejected on
it: a first-match list is a prune, and `driver`'s Sussman check exists precisely because the winning move
scored low.

**⭐ That objection was mis-aimed and is withdrawn.** `relevance` must rank because it is **domain-blind**
— it scores a proposal by whether the function's effects write an open constraint, so an unstack-to-clear
move provably scores 0 and pruning on it loses the solution. A criterion is **authored knowledge** that
can name the winning move directly. *"When the goal is X on Y and something is on X, unstack it first"* is
correct, and Sussman is only hard for a planner that lacks it.

So the two tiers:

> **Criteria prune where they speak. `relevance` ranks where they are silent.**

**⚠ The dangerous case is not a criterion that fires — it is one that fires on partial knowledge.**
Silence falls back to search and is safe. A criterion speaking with 80% of the picture prunes the other
20% away on the strength of an incomplete opinion, which is strictly worse than saying nothing. What
entitles a criterion to prune is therefore a distinction the *author* makes: is the claim about the
**action** ("this move looks good here") or about the **situation** ("in this situation, this is the
move")? Only the second is entitled, and that is a declared force, per `deliberation.md` §3's finding that
force is about failure — a method falls back to search, a procedure must refuse.

**⭐ And pruning is cheap to be wrong about here**, which is what makes the whole thing affordable.
`deliberation.md` §8: *"the cost of a wrong assumption is bounded by what you will have done before you
discover it. If everything downstream is imagining, being wrong costs nothing."* A criterion prunes while
**imagining**. So:

> A criterion may prune freely, provided **the prune is recorded** and **the fallback is reachable**.

## 3. It is scheduler, not work — so it is uninterruptible on purpose

`loop.py`'s claim is that nothing is uninterruptible. This is an exception, and it is a principled one:

> **Every interruptible system has an uninterruptible scheduler.** `loop.tick` is already one — it is
> Python, it runs to completion, it is not on the agenda.

If deciding-what-to-tick were itself a task, you would need to tick in order to decide and decide in order
to tick. `loop.py`'s "nothing uninterruptible" was always a claim about the **work** verbs — and those are
exactly the five it enumerates (`imagine`, `look`, `act`, `run`, `forget`). The criteria list is not work.
It decides what work happens next, on the spot, and returns.

## 4. ⭐⭐ And *that* is what forbids `while`

This is the sharpest constraint in the design, and it is a consequence of §3 rather than a taste.

Nothing can stop the criteria list while it runs. The self-monitoring machinery — a watcher that judges a
running computation and writes `stop` on it — works by being **another task on the agenda**, and the
agenda is not ticking. So an unbounded loop in a criterion is a scheduler that can hang with nothing above
it to notice.

> **Loops yes. `while` no.** The form must be structurally terminating: bounded iteration over a finite
> collection already materialised in the graph — for-each, fold, *"the smallest X where…"*. Termination is
> not argued, it is a property of the form.

> **⚠⚠ MEASURED, AND WEAKER THAN THIS — see §8.4.** The one case that demanded iteration is served by a
> **set-valued reader plus a selector** (`path.via` + *"the last one"*), which reproduces a hand-rolled
> `while` exactly. Bounded iteration may still be needed for something else, but nothing has demanded it
> yet, so the vocabulary should start at the selector and grow only against a measured residue. The
> argument below stands as the *bound* on what may ever be added; it is not a licence to add it now.

**⭐ This converges with the indexability constraint from the opposite direction.** Bounded iteration over
a materialised collection is exactly what indexes; a `while` is exactly what does not. Two independent
requirements landing on one vocabulary is the best evidence available that it is the right one.

It also keeps `deliberation.md`'s stopping rule intact rather than reverting it. *"Action data contains no
control flow; branching lives in decision rules; repetition lives in the loop"* becomes: repetition lives
in the loop **for work**, and in a bounded form **for the scheduler**. One relaxation, one reason.

## 5. ⭐⭐ The axis was misnamed: inspectable vs only-runnable

`deliberation.md` §10 decided *"a decision rule is DATA, not a microfunction"*. That reads as a
contradiction, because **a microfunction is already data** — a stored ISA program held in the graph, which
is the homoiconicity the whole project is built on.

The axis §10 actually cared about was never data-versus-code. It was:

> **inspectable, or only runnable.**

A **general**-ISA program is only runnable: you cannot compare two of them (`conflict.py`), a parser
cannot refuse a bad one, a reader cannot dispute its condition. That is what killed it, and "program" was
a poor proxy for it. A criterion authored in CNL, materialised in the graph, compiled to a **restricted**
instruction set — bounded iteration, no unbounded control flow — is **both**: it runs fast and straight
through, and it retains enough structure to compare, to refuse at parse time, and to answer §6.

### What the revert actually costs

§10 gave three reasons for patterns over programs. They do not fare equally:

| reason | verdict |
|---|---|
| `conflict.py` cannot compare two programs | **degrades, does not die.** The *return* is a named function — trivially comparable. Only the overlap of two conditions is hard. And `conflict.claims_of` already reads stored programs narrowly and deliberately under-reports; there is precedent. |
| a CNL can refuse a pattern; it can only emit a program it cannot check | **⚠ real cost.** The standing principle says the LLM border narrows *in the safe direction* — "a model writes data a parser can refuse, never a program nobody can check". This reverses that direction. Not fatal (`asm.py` is a program surface with a refusal story) but it must be a knowing trade, recorded here rather than discovered later. |
| a program's condition is not disputable by a reader | **answered by `activation.py`.** Interpreter state is data and the executor ticks, so a criterion that ran leaves a readable record of which instructions it executed. The contrastive query becomes a **trace**, not a failed conjunct — weaker than a structural claim, but implementable, and most engines could not offer it at all. |

## 6. ⭐ "Why not X?" is promoted from a bonus to a requirement

Under ranking, the alternatives are still on the frontier and can be inspected. **Under pruning they do
not exist anywhere** — the search never saw them. So the contrastive query is the only window onto what
the criteria discarded, and it must ship in the same slice, or the first wrong criterion yields *"no plan
found"* with nothing behind it.

It has three answers, and they should not be conflated:

1. **no criterion pointed at X** — cheap, honest, probably the common case
2. **a criterion pointed at X, but an earlier one won** — the interesting one
3. **a criterion would have pointed at X but one part of its condition failed** — needs the trace of §5

The `why` half already exists: `guideline.governing` returns which guidelines spoke to a call, in
precedence order.

## 7. Indexing

**⚠ DO NOT BUILD YET.** With twenty criteria a linear scan behind a cheap type guard beats any index, and
the project's precedent is that the named lever was 6% of the cost. What matters *now* is that the
vocabulary stays indexable; the data structure is a later afternoon once there is a corpus to measure.

**Goals have no schema — but their constraints have a closed sort vocabulary**, and that is the key that
is free. `driver.relevance` already iterates unmet constraints per proposal reading exactly
`(sort, label-or-key)`, where `sort ∈ {link, attr, type, never, eventually, at_most}`. A criterion keying
on *"when the goal wants `on(x,y)`"* indexes on that, as a byproduct of work already happening in the hot
path. Second goal-side key: `goal.ancestry` labels — *"am I inside a `deliver_order`?"*.

**Context type** is the third key.

> **⚠ The subtyping trap.** Expanding a criterion into subtype buckets *at registration* **breaks
> silently**: types are minted as data at runtime, so a subtype declared after the criterion never gets
> the entry, and every test written before that subtype exists still passes. Walk the context type's
> ancestry **at lookup** instead.

**⭐ The return indexes better than the condition.** A condition is a program, so any index over it is
approximate; a return is a named function, a literal, exact. The **reverse index** — action → criteria
that could return it — is what makes §6's contrastive query cheap instead of a full scan with every
condition evaluated. Design it in the same pass.

**The index is candidate generation** — `selection.py`'s stage 1, *"matching in its demoted role: bounded,
one node at a time, no fixpoint"*. So it must be **sound, never exact**: it may never drop a criterion that
would have fired. Which gives the vocabulary rule:

> **Every condition form contributes an index key, or nothing.** An unkeyable form is allowed — it simply
> does not narrow, and runs on whatever survives the keyed filter. Expressiveness costs speed rather than
> being forbidden.

## 8. The probe — RUN 2026-08-01

`probe_criteria.py`, next to this file. Two criteria, wired as a dominating `rank` over the blocks world
`selftest.py` already has. **The engine is untouched — `188 checks, 0 FAILED` before and after.**

**⚠ Measuring the prune without pruning.** `allow` filters on the function name only, so the prune arm
cannot be wired without an engine change. Instead the criteria are a dominating `rank`, and the cost a
pruning version would have paid is read off **imagined steps versus plan length**: when they are equal the
search never deviated, so a prune would have committed to exactly this — for better or worse.

### Results

| scenario | imagined (relevance / criteria) | plan (rel / crit) | |
|---|---|---|---|
| Sussman | 52 / **4** | 3 / 3 | same plan |
| plain tower | 2 / 3 | 2 / 2 | same plan |
| Sussman, goal constraints declared in reverse | 52 / **4** | 3 / 3 | same plan |
| 4 blocks, 3 constraints | 378 / **8** | 6 / **4** | **better plan** |
| two-deep blocker, **loop-free** criterion | 91 / 4 | 3 / **4** | ⚠ **worse plan, and a prune would have locked it in** |
| two-deep blocker, **bounded-loop** criterion | 91 / **3** | 3 / 3 | same plan |
| two-deep blocker, **`path.via` + a selector, no control flow** | 91 / **3** | 3 / 3 | **same as the loop, exactly** |

**1. Does it solve Sussman? Yes — 52 imagined states down to 4**, same three-step plan. The user's claim
holds and holds easily.

**2. How many criteria? TWO.** *"If the goal wants X on Y and something is above X or Y, take it off"* and
*"if the goal wants X on Y, both are clear, and Y is already in its final place, stack X on Y."* That is
knowledge, not the answer written out — the same two criteria carry every scenario, including ones the
baseline handles badly.

**3. Coverage under perturbation — two findings, opposite signs.**

- ⭐ **Reordering the goal's constraints changes nothing** (4 imagined either way), so the criteria are not
  reading declaration order by accident.
- ⭐ **On four blocks the criteria produced a *better plan*, not just a cheaper search** — 4 steps against
  the baseline's 6, and 378 imagined states down to 8. Plan quality was not one of the questions and it
  improved anyway.
- ⚠ **And the predicted failure landed exactly where predicted.** With the loop-free criterion, the
  two-deep blocker (two blocks stacked on the one that must move) yields a **4-step plan where 3 suffice**
  — and `imagined == plan length`, meaning the search never deviated, so **a pruning version would have
  committed to the worse plan with nothing to fall back to.** This is the entire residue of the withdrawn
  objection, and it is real: partial knowledge prunes the better answer away.

**⚠ So the metric cuts both ways, which was not anticipated.** *"A prune would have been free"* is not a
success signal — on the two-deep blocker it is precisely the warning that a prune would have been
**locked in**. It measures *decisiveness*, and decisiveness is only good when the criteria are right.

**4. ⭐⭐⭐ THE CAPABILITY IS LOAD-BEARING. THE LOOP IS NOT.** Replacing *"the block directly on X"* with
*"the **topmost** block above X"* turns the failure into a clean win — **91 → 3 imagined, plan back to 3
steps**, every other scenario unchanged. So reaching the top of the pile is genuinely required.

But it needs **no control flow**, and the first version of this section said it did. `path.via(x, "on",
back=True)` already walks the pile breadth-first, **nearest first**, so *the topmost is simply the last
one*. Written that way — a **set-valued reader plus a selector**, no `while`, no recursion — the criterion
reproduces the hand-rolled loop **exactly**, on every scenario.

> ⚠⚠ **Corrected claim: what the vocabulary needs is a SET POSITION WITH A SELECTOR, not iteration.**
> That is strictly weaker than §4's bounded loop — still total, still indexable, still decomposable for
> §6 — and the traversal it stands on already ships.

### Condition-language residue — ⚠ **both of the first version's items were wrong**

This is the project's own pattern landing on this document: it looked fundamental, and it was already
there. `probe first` (`causation-core-was-sugar`, `closed-class-rechallenged`), applied to a residue log
that had not itself been probed.

1. ~~**INVERSE RELATION — "the block that is ON x"**~~ — **NOT A GAP. It has existed all along**, as `^on`.
   `path.py`'s grammar is `seg := ['^'] label ('[' int ']')?` and `_step` implements the backward hop
   through `Graph.sources`. ⚠ With one real restriction, which is a feature: it resolves only when
   **exactly one** node points that way — true of a block, false of the ground — *never identify by
   ambiguity*.
2. ~~**Needs iteration to a fixed point**~~ — **NO. `path.via` already does the traversal**, and is
   documented as being "offered for a caller that has somewhere to put a set". The genuine residue is
   narrower: `via` is deliberately **not reachable from the path grammar**, because a reference that
   denoted a set would break `node_at`'s promise to return one node. So the one real gap is a **surface
   form that may denote a set and select from it** — and it is a surface gap, not an engine gap.

---

## 8b. The seam, BUILT 2026-08-01 — and pruning measured for real

`driver.Call(function, bindings, why)` — a decision that names **what to do**, not only whether to keep
going. `decide` may now return one, and `driver._honour` substitutes it for the ranked choice.
`189 checks, 0 FAILED` (`check_a_decision_can_NAME_THE_ACTION_and_the_displaced_one_stays_reachable`).

**What it validates, and the line it will not cross.** A `Call` may name a binding the enumeration never
proposed — that is the point, and it is `selection.candidates`' *"inventing bindings is search"* wall
coming down deliberately. It may **not** name an ill-typed binding, one node in two roles, an unknown
function, the wrong arity, or **an action the goal forbids**. Each raises `Undecidable` naming the fault.
Rank a guess, prune a proof: a decision arriving from outside must not be able to launder a guess into an
overrule of `goal.forbid_action`.

**⚠⚠ THE LIVELOCK, and it is the thing this slice actually taught.** §2's two rules — *first match wins*
and *the fallback stays reachable* — are in direct tension. The displaced candidate goes back on the
frontier, the search re-takes it, a deterministic criterion names the same action, that action reaches an
already-imagined state, and the candidate goes back again. Measured before the fix: **12 steps, 9 of them
the same substitution from one frame, goal never reached.**

> **A decision applies once per frame per call.** Recorded on the frame, compared on
> `(function, individuals)`. Not a new principle — it is `deliberation.md` §4's frequency rule and exactly
> the answer `DECOMPOSE` already gives: *frequency, not absence*. And it is honest rather than silent: the
> decision was not ignored, it has **already been carried out here**, and the trace emits `spent`.

### ⭐⭐ Real pruning is measurably WORSE than ranking the same knowledge

Same two criteria, three wirings (imagined states / plan length):

| scenario | prune only (`Call`) | rank only | both |
|---|---|---|---|
| Sussman | 5 / 3 | **4 / 3** | 6 / 3 |
| plain tower | 3 / 2 | **3 / 2** | 4 / 2 |
| Sussman, reordered | 5 / 3 | **4 / 3** | 6 / 3 |
| 4 blocks, 3 constraints | 134 / 4 | **8 / 4** | 12 / 4 |
| two-deep blocker | 6 / 3 | **3 / 3** | 5 / 3 |

**Ranking wins every scenario, and combining the two is worse than ranking alone.** The reason is
structural, and it is the sharpest thing measured in this document:

> **A rank informs every choice on the frontier. A prune informs only the next one.** Once a decision is
> spent for a frame, the search falls back to plain `relevance` — so pruning buys decisiveness at one step
> and forfeits guidance everywhere else. On four blocks that is 134 imagined states against 8.

⚠ **This partly vindicates §2's withdrawn objection, but for a completely different reason than the one
originally given.** The claim was *"pruning loses the solution"* — it did not, anywhere; every wiring found
a plan. The real cost is efficiency, not completeness, and no amount of Sussman-style reasoning would have
predicted it. Both the objection and its withdrawal were arguments; this is a measurement.

**So what is `Call` for?** Not speed. Two things, and they are worth the seam:

1. **Naming a binding enumeration would not produce.** Untested here — blocks world enumerates everything,
   so the feature has no room to pay. A domain with a large or unbounded binding space is where it earns
   its place, and that is the next probe.
2. **Saying "this and nothing else" with a recorded reason** — the audit and compliance case §6 needs.

**⭐ The build order this implies: rank by default, prune only where an author declares a claim about the
situation rather than about the action** (§2's advisory-versus-mandatory distinction). That was argued from
force; it now has a number behind it.

---

## 8c. A LARGE BINDING SPACE — measured 2026-08-01

`probe_binding_space.py`. `stack(b, onto)` is two-parameter, so a world of N clear blocks offers O(N²)
proposals per frame, while the criteria read only the blocks the **goal** names — O(goal), independent of
N. Goal is always `a on b on c`, with `c` buried under two others so the topmost-of-the-pile knowledge is
actually needed. Budget 400 steps.

| N | wiring | found | imagined | plan | frames | **proposals** | secs |
|---|---|---|---|---|---|---|---|
| 5 | relevance | yes | 139 | 6 | 55 | 644 | 0.97 |
| 6 | relevance | yes | 357 | 6 | 144 | 2 128 | 11.15 |
| 7 | relevance | **NO** | 400 | — | 178 | 3 327 | 21.82 |
| 8 | relevance | **NO** | 400 | — | 196 | 4 759 | 29.96 |
| 5 | rank | yes | **5** | 4 | 4 | 86 | 0.02 |
| 8 | rank | yes | **5** | 4 | 4 | 230 | 0.05 |
| 12 | rank | yes | **5** | 4 | 4 | 534 | 0.12 |
| 16 | rank | yes | **5** | 4 | 4 | 966 | 0.20 |
| 20 | rank | yes | **5** | 4 | 4 | 1 526 | 0.43 |
| 20 | `Call` | yes | 7 | 4 | 6 | 2 179 | 0.63 |

**⭐⭐⭐ 1. Expert judgement makes the search size-independent.** Imagined states stay at **5** for every N
from 5 to 20, while the engine's own guidance goes 139 → 357 → **falls off a cliff between 6 and 7 blocks**
and stops finding a plan at all. That is not a constant-factor speed-up; the number of states explored
stops depending on the size of the world. It is much the strongest result in this document, and it is the
user's original claim — *"the best move according to our knowledge"* — holding at scale.

**⚠ 2. But the residual cost is entirely ENUMERATION, and criteria do not touch it.** With criteria the
search visits four frames at every N — yet proposals grow **86 → 1 526** and time **0.02s → 0.43s**, purely
because each of those four frames still builds the full O(N²) product. All of the remaining cost is
building proposals that a decision then ignores.

**⭐⭐⭐ 3. And `Call` — built precisely for this — does not help. It makes it worse.** At every size it
enumerates *more* than ranking (2 179 against 1 526 at N=20), because it visits six frames instead of four.

> **The seam is in the wrong place, and the reason is architectural rather than incidental.** `_offer`
> enumerates a frame at the end of the step that creates it; `decide` is consulted later, when a candidate
> *from* that frame is taken. **Enumeration is already paid before a `Call` is ever consulted.** So naming
> a binding can change *which* proposal is imagined and can never avoid *building* the proposal set — which
> is the entire cost this feature was built to remove.

**The headroom, and it is large.** At N=20 ranking spends 1 526 proposals across 4 frames (~380 each). A
criterion that spoke at *frame-expansion* time would offer one call for the frames it speaks to — order
**4 proposals instead of 1 526**, better than 99% avoided. That is the next slice: consult criteria inside
`_offer`, before the cartesian product, and fall back to full enumeration only where they are silent.

⚠ **It does not change §8b's ranking-beats-pruning result, and must not be read as reversing it.** Deciding
early is about *not building* proposals; ranking versus pruning is about *which* of the built ones to take.
The two are orthogonal, and the measured order is still: rank by default, and now — enumerate lazily.

---

## 8d. `propose` — deciding BEFORE enumerating. BUILT 2026-08-01

`driver.pursue(propose=...)`, consulted inside `_offer` **before the cartesian product**. Same `Call`, same
`check_call` validation, one step earlier. `190 checks, 0 FAILED`
(`check_deciding_BEFORE_enumerating_suppresses_the_product_but_never_LOSES_it`).

**⭐⭐ The suppressed enumeration is DEFERRED, not skipped.** That is the whole design. A frame a criterion
spoke for records a `deferred` node; when the frontier empties, `_backfill` builds one and the search
carries on. Only a search with nothing left deferred is exhausted. So authored knowledge may be wrong
without a solution becoming unreachable — the property `relevance` gets by ranking rather than filtering,
obtained here by a different means, because at this point in the loop there is nothing yet to rank.

| N | wiring | imagined | plan | frames enumerated | **proposals** | secs |
|---|---|---|---|---|---|---|
| 20 | rank | 5 | 4 | 4 | 1 526 | 0.36 |
| 20 | `Call` | 7 | 4 | 6 | 2 179 | 0.66 |
| 20 | **`propose`** | 5 | 4 | **1** | **381** | **0.07** |
| 30 | rank | 5 | 4 | 4 | 3 486 | 1.20 |
| 30 | **`propose`** | 5 | 4 | **1** | **871** | **0.27** |
| 60 | rank | 5 | 4 | 4 | 14 166 | 8.58 |
| 60 | **`propose`** | 5 | 4 | **1** | **3 541** | **1.30** |

4× fewer proposals and **6.6× faster at sixty blocks**, with the identical plan. And on Sussman, where the
criteria cover every frame, a good proposer builds **zero** proposals against the default's 135 — the
enumeration disappears entirely rather than shrinking.

### ⚠⚠ What it costs, measured rather than argued

**Completeness holds. Plan quality does not.** A deliberately useless proposer (always `paint`) still
reaches the goal — but with `(paint, paint, unstack, stack, stack)` against the default's
`(unstack, stack, stack)`. Backtracking to the newest deferral extends the bad prefix before the root's
alternatives are ever built.

> **The honest statement: deferral preserves the GOAL, not the plan.** That is strictly milder than losing
> the solution, and strictly worse than `relevance`, which pays neither cost because it never suppresses
> anything. A wrong criterion is now cheap-but-not-free, where §2 claimed it was free.

**⚠ And the backtracking order is not a taste.** Oldest-first floods the frontier with one frame's whole
product while the proposer keeps deferring new frames behind it: the same useless-proposer run then **fails
outright** — 200 steps, no plan — where newest-first succeeds. Chronological backtracking, measured.

### Where that leaves the three seams

| | asked | changes | measured verdict |
|---|---|---|---|
| `rank` | per proposal | the order | **the default.** Size-independent search, no completeness cost |
| `decide` → `Call` | per candidate taken | which one is imagined | for *audit* and for naming a binding; never for speed |
| `propose` → `Call` | per frame, before the product | whether the product is built | **the large win**, and the only one that touches enumeration |

`rank` and `propose` compose and should be used together; `Call` at `decide` time is the one whose value is
expressiveness rather than cost.

---

## 8e. THE CNL — BUILT 2026-08-01. `criterion.py` + one block in `intake.py`

`191 checks, 0 FAILED`. Not a fifth surface: one more verb on the one CNL, per HANDOFF §5t.

```
criterion clear the block that must move:
    wants link on
    do unstack b = furthest subject by ^on, floor = the ground
    because nothing can be stacked while something sits on it

criterion build from the bottom up:
    wants link on
    when subject is a clear_block
    when object is a clear_block
    unless wants link on from object
    do stack b = subject, onto = object
```

**⭐⭐ Where the variables come from is the whole design.** A criterion may not name individuals — one
saying *"unstack c"* would be about `c` and could not be reused. `wants link on` matches an **unmet**
constraint of the goal and binds `subject` and `object` from it. That is `method.py`'s trick in a second
place, **and it is exactly §7's index key**: goals have no schema, but their constraints have a closed sort
vocabulary, and `driver.relevance` already computes it per proposal. What a criterion keys on and what an
index would key on turned out to be the same thing, so indexability needed no arranging.

**⭐⭐ `furthest subject by ^on` — the set position with a selector, replacing the loop.** `path.via` walks
nearest-first, so the topmost of a pile is the last one. Vacuity guard in the check: swap `furthest` for
`nearest` and the criterion names a buried block, which `unstack` refuses.

### The numbers, from authored text

| N | found | imagined | plan | frames enumerated | proposals | secs |
|---|---|---|---|---|---|---|
| 5 | yes | 4 | 4 | 0 | **0** | 0.01 |
| 20 | yes | 4 | 4 | 0 | **0** | 0.01 |
| 60 | yes | 4 | 4 | 0 | **0** | **0.04** |

**Zero proposals built, at every size**, against `rank`'s 14 166 and 8.59s at sixty blocks — and against
`relevance`, which stops finding a plan at all between six and seven. On Sussman: **3 imagined states
against 52**, and every scenario returns an optimal plan. ⭐ The authored criteria are *better* than the
hand-written Python ones of §8 (3 against 4–5 on Sussman, 4 against 8 on four blocks), because the CNL made
the two "clear the way" cases separate criteria and each says one thing.

### ⚠ The bug this slice produced, which is the one worth remembering

`governing` and `speaks` **disagreed**. `governing` checked only the `when` lines; `speaks` also required
the action's references to resolve — so on Sussman's root frame it reported all three criteria as having
spoken when only one could. Two paths computing *"the same"* thing differently, landing in the one feature
whose entire job is to explain truthfully. Fixed by one `_try` both call, and guarded.

That also settles a design question by force: **an action's arguments are part of its condition.** *"Take
the topmost block off the pile above x"* does not apply when there is no pile, and making the author write
a separate guard would mean a forgotten guard becomes a crash mid-search rather than silence.

### What is still not settled

- Blocks world only, throughout.
- **The index is still not built** — and now there is finally a corpus shape to build it against. §7's rule
  stands: every condition form contributes an index key or nothing.
- `decide`-time `Call` remains the seam with no measured payoff; its case is audit, not cost.
- Nothing has tested criteria that *disagree* — `conflict.py` can compare what two criteria return, and
  nothing does. Whether two criteria stay two on a domain with more operators is untested, and that
  is the number question 2 actually cares about.
- Nothing here was authored in CNL; the criteria are Python. The condition **vocabulary** — the real
  design — is still unwritten.

## 9. Open

- **Binding-invention moves out of search, deliberately.** `selection.candidates` refuses multi-parameter
  functions because *"inventing bindings is a different problem (search) that should not hide inside
  candidate generation"*. A criterion returning `stack(a,b)` does exactly that job. Right, and the point of
  the feature — but the wall should come down on purpose.
- **The seam has to change to accept a bound call.** Today `decide` runs after `take_best` and can only
  stop. §1.
- **What declares force?** §2 needs advisory-versus-mandatory to be a declared property of each criterion,
  and nothing says how it is written yet.
- **The condition vocabulary itself.** The whole design, and unwritten. It has three constraints that
  agree: total and bounded (§4), indexable (§7), decomposable enough for §6.
