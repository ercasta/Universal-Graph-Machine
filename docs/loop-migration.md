# Deleting the option-set loop — the work list

The author's decision: **the table loop is the loop, and the option-set loop
goes.** The engine is experimental and owes nobody stability, so a check that
only makes sense for the loop being deleted may be deleted with it.

This file is the measured work list rather than a plan. Every line below comes
from running the suite with `Machine.run` pointed at `attention.run`, which is
now a one-line change because the table loop returns `Step`s.

    58 of 545 -> **39 of 535**, and nothing raises.

Progress is at the bottom. The count of checks falls as well as the count of
failures, because a check about machinery that is going is deleted with it.

Reproduce with `scratchpad/fallout.py`: it wraps every selftest function so one
exception does not hide the rest, which is how the whole list came out in one
pass instead of 58 iterations.

---

## What has already landed

**The comparison became a gate.** `ugm.attention` printed a diff and never
touched `bad`, so *the table loop reaches the same conclusions* — the premise of
this entire migration — was asserted nowhere. It is now one-sided: the table
loop may conclude **more**, never **less**, except `ACCEPTED_LOSSES`.

**Defeat came back, and it was not on the list.** `_survives` is per-candidate
and excludes defeat by design (*defeat is per RULE*), so a prefix scan dropped
`overrides` entirely.

>⚠⚠⚠ **The gate agreed anyway, and that is the finding.** It compares final
>conclusions, and a loop that runs to quiescence applies the loser eventually —
>*ordering is not defeasibility*, this design's own line, arriving as an
>instrument defect. **Two loops can agree about every conclusion and disagree
>about whether a rule was ever defeated.**

The repair keeps the prefix scan: `overrides(A, B)` needs to know whether A
matched, A's overriders are read off the graph and there are usually one or two,
so `_is_defeated` matches **those** rather than the pool. A join, not a scan.
That took `defeated` off the accepted-loss list, which is now `{close}` alone.

⚠ It must test **matched, not survived**: once the winner applies, its
conclusion holds, it stops surviving, and the loser becomes undefeated and
overwrites it.

---

## The 58, classified

### A. Delete with the loop — 6 · **DONE**

These are about machinery that is going. The check goes with the code.

| check | why |
|---|---|
| `matching_is_incremental` (raises) | `_match_cache`, an optimisation of `_materialise` |
| the machine counted its selections | `m.selections`, the old tick's counter |
| and the tick reports which silence it was | the old `Step.state` taxonomy |
| what it keeps, it no longer re-weighs | weighing an **option set** the new loop never builds |
| ...and it is LINEAR in the corpus (weighing) | same |
| a higher score outranks a lower one — cardinals | the old preference score; the table **is** the score now |

### B. Accepted losses — 3 · **DONE**

Claims about a set the prefix scan deliberately never materialises.

| | |
|---|---|
| `close` | already accepted, and the only entry in `ACCEPTED_LOSSES` |
| **`forgone`** | ⚠ **decide before deleting.** *Taking one way passes up the others* is called a **safety** property in its own check — *an act cannot be taken back* — and 4 checks rest on it. It is the same shape as `close`, but the argument for keeping it is stronger |
| and once one is clearly better, there is no doubt left | doubt over the whole option set |

### C. Port — the real work, ~20

**Stopping (10).** ✅ **DONE.** The table loop has `stop`, a postcondition. It has no
`enough` and no open-goal veto. The design's own position is that *done is the
output of a rule*, so the port is to make `enough` a rule that spends `stop`
rather than to re-add `_enough` in Python — and the veto is the hard half,
because *nothing else is wanted and unmet* is an aggregate.

**Effort records (6).** `widened`, `reached`, `bounded`. The table loop widens
794 times on `dungeon` and deposits nothing. These are worth porting rather than
dropping: *a rule can act on how hard the agent had to try* is a feature, and it
is §1's deposit-the-record discipline.

**Suppositions (4).** Proposing one, leaving one as an occasion, `enough`
inside a hypothesis ending the branch rather than the run.

**Recall (2).** Dormancy and callbacks — `dormant` until something claims `due`.
⚠ Possibly subsumed: a dormant rule is a rule at the floor, and the table
already expresses that. Decide whether this is one mechanism or two.

### D. Re-baseline — 2

Not semantic losses. Both count work **through** the loop, and the table loop
re-matches on every widening, so the constants move.

| | |
|---|---|
| a self-join is linear in the corpus | ⚠ and check it is still **linear** — 794 widenings is a lot of re-matching |
| ...and the delta half decides nothing here | recall-budget bookkeeping |

### E. Investigate — the rest

Learning and credit (~8): `supersedes` is unimplemented in the new loop and
defeats per **case** rather than per rule, so it cannot be settled by asking
whether a rule matched. A fact's own history being matchable also fails, and it
should not depend on the loop at all — that one is a genuine unknown.

---

## And one thing to settle first

>**`python -m ugm.arbitration` is failing — 4 disagreements — and was failing
>before any of this.**

That is the floor gate for *the move*: `_choose` against `_materialise`. Both
arms live inside the loop being deleted, so deleting it retires the gate. It
would be better to know why it disagrees while there is still something to ask.


---

## Progress

| | checks | failing |
|---|---|---|
| the flip, as first measured | 545 | 58 (+1 raising) |
| defeat restored (`_is_defeated`) | 545 | 58 |
| **stopping ported** | 545 | **48** |
| **A and B deleted** | **535** | **39** |

**Stopping** is `Machine._enough` called from the table loop, rather than a
second copy: it reads `enough(...)` at the focus and exercises the open-goal veto
once per seat. `stop` remains the rule-level route and the recommended one; this
is the half that cannot be a rule, because *nothing else is wanted and unmet* is
an aggregate. Inside a hypothesis it is `_leave` -- enough here ends the branch,
not the run -- and it deliberately writes no `quiet`.

**Deleted with the loop**: `matching_is_incremental` (the `_match_cache`), the
selection counter, the old `Step.state` taxonomy, two checks about weighing an
option set, the old cardinal preference score, and the four `forgone` checks.

>⚠ `forgone` was the author's call and the reasoning is recorded at
>`ACCEPTED_LOSSES`: its own check argued it is a **safety** property, so dropping
>it means the agent no longer records which act it passed up.

**Remaining 39**, in rough order of size: effort records (`widened`, `reached`,
`bounded`) 6 · suppositions 4 · recall, dormancy and callbacks 5 · `supersedes`
per-case defeat 3 · learning and credit 8 · re-ask and re-suppose termination 3 ·
the rest to investigate, including *a fact's own history is matchable*, which
should not depend on the loop at all.


---

## Can the remaining 39 just be dropped? — measured, and the answer is *most, not all*

The test is not *does the check fail* but **is the capability absent**. Run each
selftest function on its own (`scratchpad/classify.py`) and read its failures
against its passes: a function whose outcome checks all pass while one
bookkeeping check fails is gripping the old loop's internals; a function whose
outcome checks fail has lost something.

23 functions carry the 39.

### Droppable — the check grips old internals, the capability is intact (~15)

The clearest case, and it is the pattern:

    ### rule_driven_supposition -- 1 of 7 failing
        FAIL  a rule proposed the supposition

The other six pass: **modality crossed the whole pipeline, the hedge fired on
the wrapped conclusion, the guard held, nothing carried out of the frame.**
Suppositions work perfectly. What fails is `s.state == "supposed"` -- a Step
label the new loop does not emit.

Same shape: the old `_in_play` preference key (3), doubt and tolerance over the
option set (2), the old recall table and its widening (3), *the apparatus wins
most of the agent's choices* (1), the self-join unification count (1), and the
overrides-cycle fallback (1). The table **is** the preference now, and it has
its own doubt and its own widening, so these are one mechanism measured twice.

### Not droppable — four things the new loop genuinely does not do (~24)

**1. Termination guards — 4 checks, and this is the one that matters.**

    FAIL  waking is once per seat, so the occasion cannot re-arm itself
    FAIL  an occasion the re-asking can itself CREATE warrants a re-ask forever

>⚠⚠⚠ These are not bookkeeping. They are the guards that stop the agent asking
>the same question **100+ times**. Dropping them does not remove a record, it
>removes a bound -- and `_wake` per seat is exactly the shape this repository
>has recorded runaways in before.

**2. Learning — ~8 checks across 5 functions.** An episode teaching the next
one, generalising to a case neither example mentioned, a learned rule losing to
an authored one, an adopted rule actually applying. This is not a check
artefact; learning is substantially broken under the new loop, and much of it is
downstream of (3).

**3. `supersedes` — 4 checks.** Per-CASE defeat: only applications sharing a
consumed entry with the winner are out. `_is_defeated` cannot answer it, because
the question is not *did that rule match* but *did that application share this
premise* -- and the prefix scan holds only a window of applications.

**4. Effort records — 7 checks.** `widened`, `reached`, `bounded`. The new loop
widens 794 times on `dungeon` and deposits nothing. `bounded(ticks)` is written
but does not fire -- the condition tests the last Step and the last Step is not
`applied`. Cheap, and worth having: *a rule can act on how hard the agent had to
try*.

### So

Dropping the ~15 is free and honest. Dropping the other ~24 means giving up
learning, per-case defeat, effort-awareness -- and, in one case, **a termination
guarantee**, which is not a feature to trade away in an experimental engine so
much as a thing that will waste an afternoon later.


---

## Effort records, done — and what it taught about the *other* three

Asked as *port to the new loop, or move out to rules?*, and the answer turned
out to be **neither**, which is the finding.

>**`widened`, `reached` and `bounded` are not portable to rules, and they were
>never really Python "logic" either. They are the loop reporting its own event**
>-- the same shape as `quiet` and `arrived`: the smallest unarguable record of
>something only the loop can know. A rule cannot conclude that the shortlist ran
>dry, for the same reason a rule cannot conclude that a channel spoke.

So the work was to call what already exists rather than to rewrite or relocate
it: `Machine._widen` and `Machine._recover` already read the budget knob off the
graph, guard once per seat, and deposit. The table loop now calls them, in the
old tick's order.

**9 failing → 0**, and it took two real bugs with it.

**One Step per tick.** The table loop appended nothing on the paths that
`continue` -- widening, waking, leaving a frame, depositing a doubt -- so a run
of 40 ticks returned 20 steps and every caller comparing `len(steps)` against its
own limit was wrong. The old loop returned a Step for every tick, and a caller
counting them has to see the ticks that did something other than apply.

**The widening guard was never reset.** The old tick clears `_widened` whenever
something applies -- *widening is a state the agent is in, not a mode it is
switched into* -- and this loop did not, so after the first dry shortlist it
never reached past one again for the whole run.

>⚠ Neither was on the work list. Both were found by porting a **record** and
>then asking why the record was still wrong, which is the argument for doing
>these one at a time rather than in a batch.

One check dropped with the old recall: *three widenings at one seat are ONE
claim*. The property still holds (deposits == 1); what cannot be met is its own
vacuity guard, `widenings > 1`, which needed the old recall's narrow-and-widen
arrangement. **The table's window IS the shortlist now** -- one mechanism where
there were two.

### Where that leaves it

| | checks | failing |
|---|---|---|
| the flip, as first measured | 545 | 58 |
| stopping ported | 545 | 48 |
| A and B deleted | 535 | 39 |
| the 15 dropped | 523 | 27 |
| **effort records** | **522** | **14** |

**The remaining 14 are two things, not four.** `supersedes` (per-case defeat)
and everything downstream of it: learning, credit, generalisation, and the
harmonization checks that need a learned rule to lose to an authored one. Plus
three singletons -- dormancy's pointer, a re-ask costing one tick, and *a fact's
own history is matchable*, which still has no explanation.


---

## `supersedes` — ported, and the three routes that were tried first

The proposal was that `supersedes` is like `forbidden`: something that has to be
**reasoned** rather than computed, with a buff on the superseding rule as the
mechanism. The first half is right and the second is measurably wrong, which is
worth recording because the correction is one the author has already made once.

**A buff cannot defeat.** Two rules concluding opposite signs from one premise,
in the table loop:

| | applied | what `q` reads |
|---|---|---|
| nothing -- authored order | `A1, A2` | `-` |
| **A2 first in the table** (the strongest possible buff) | `A2, A1` | **`+`** |
| `overrides(A2, A1)` | `A2` | `-` |

Boosting the winner gets it applied *first*, and then the loser applies second
and **overwrites it** -- the buff produced the opposite conclusion, worse than
doing nothing. This is *ordering is not defeasibility*, and it is why the author's
own resolution for norms made `+lawful(?a)` **a premise, never a boost**.

**Consumption cannot either**, and the reason is a rule this repository already
has. Make `<outcome>` spend its trigger -- `{ +did(?a), +achieves(?a, ?y) } =>
{ +?y, -did(?a) }` -- and the act is asserted anyway, because `did` is
re-derived from `emitted` by a bundled rule. **Never consume what you were told**,
arriving from the far side: the trigger is downstream of a boundary record.

**A negated member cannot either**: *this act has no declared outcome* is
negation over an open domain, which is exactly what §9 refuses.

So the property `supersedes` exists for -- *substitute where an outcome is
declared, otherwise assume* -- is not expressible any other way, and it is
**ported rather than dropped**, in `_is_defeated`'s shape one construct along:
the question is about a PAIR of applications, so match only the rules that
supersede this one and ask whether any of their applications shares a consumed
entry. A join where the old loop materialised everything it had.

>⚠ And a census point that argued for deleting it and does not: **no `.ugm`
>corpus uses `supersedes`.** Only its own tests. That is the shape that retired
>the grade and the precedence table -- but the property here is one no other
>construct can carry, so *unused* is an argument about corpora rather than about
>the relation.

⚠⚠ **A near-miss worth recording.** Both supersedes clusters were first reported
green -- because the functions were run **without the flip applied**, so they
exercised the old loop and passed as they always had. Re-run under the flip, one
was genuinely fixed and the other was never about `supersedes` at all. *A check
that is not running the thing under test agrees with everything.*

### Where it stands

| | checks | failing |
|---|---|---|
| the flip, as first measured | 545 | 58 |
| stopping | 545 | 48 |
| A and B deleted | 535 | 39 |
| the 15 dropped | 523 | 27 |
| effort records | 522 | 14 |
| **`supersedes`** | **522** | **13** |

**The remaining 13 are one cluster and three singletons.** Learning: an episode
teaching the next, generalising to an unmentioned case, a learned rule losing to
an authored one, a preference row not double-counting. Then dormancy's pointer,
a re-ask costing one tick, and *a fact's own history is matchable* -- still
unexplained, and still the one I would look at before assuming it is cosmetic.


---

## *A disabled mark on the rule* — the idea is right and it already has a name

Proposed: mark a rule disabled and have the engine ignore it. That capability
exists, and the form it exists in is the point.

    dormant(<R>)      not considered
    due(<R>)          ...until something claims this

Both are **ordinary facts**, not a field on the rule. The table loop was ignoring
them -- it built its pool and never asked -- so it now reads them every tick, at
the register's own position. **13 → 12.**

>⚠ **Why a claim and not a mark, since the behaviour is the same.** A mark
>authored once is relative to nothing: not to the situation, not to the goal, not
>to who is asking. That is §12's *achievability is not a mark*, this design's
>earliest instance of the error it generalises everywhere else -- and the same
>argument that retired the grade, moved norms out of the engine, and deleted the
>precedence table. As claims, `dormant` and `due` are dated, attributable,
>deniable, and readable by rules; *which rules is this hypothesis carrying* is a
>query rather than a field, and `due` can be concluded by anything at all.

And read **per tick**, never once when the pool is built: `due` can be concluded
mid-run, and a callback attached inside a hypothesis must wake only there.

>⚠⚠ It is also not the answer to `supersedes`, and the difference is worth
>keeping straight. Dormancy is *this rule is not worth considering right now* --
>an attention claim, recoverable, and safe to be wrong about. Defeat is *this
>rule must not apply here* -- and being wrong about it means the loser
>re-asserts and quietly undoes the winner. One is recall, the other is a veto.


---

## Teaching's gate, and the four checks it retired

Asked whether the old offline learning is superseded by buffs. **Half of it is**,
and the measurement decided which half.

`learned()` and `induce()` emit **`prefer` rows** -- *in situations like this,
prefer X*. That is what a table score is, in a second notation. What they also
emit is **rules** -- anti-unification generalising from examples -- and no
amount of score-tuning produces a rule the agent did not have. Attention and
acquisition are different capabilities and only the first was doubled.

### But the replacement had to be shown to work first

`ugm.teaching` was failing its own gate on both corpora, so retiring `prefer`
rows would have deleted a working mechanism for a worse one.

>⚠⚠⚠ **It was not failing. The gate was pointed at the wrong thing, and it read
>the mechanism working as the mechanism failing.** It counted every proposition
>a taught run did not reach -- and a calibrated table **hesitates less**, so it
>deposits fewer `close`, `settled` and `spent(<settle-doubt>, ...)` records.
>Measured on `quest-p1`: all nine "lost" conclusions were doubt bookkeeping and
>**not one was about the world.**

This is `ugm.attention`'s own rule one construct along -- *the comparison has to
be over conclusions rather than over moves, because two runs that reach the same
beliefs by different routes agree about the world.* `BOOKKEEPING` now names the
four relations that are the agent's account of **how** it decided, and the raw
figure is printed beside the excluded one so the exclusion is visible rather
than silently applied.

⚠ The gate keeps its teeth: `intends` is a domain relation and **is** lost on the
dungeon -- by the uncalibrated arm too, which is what says the loss is not
calibration's doing. Kill-probed: empty `BOOKKEEPING` and 5 failures return.

### And then it pays, which is the result

| | moves | matched/move | domain conclusions lost |
|---|---|---|---|
| `quest-p1` uncalibrated | 21 | 18.8 | 0 |
| **calibrated** | **18** | **11.1** | **0** |
| `dungeon` uncalibrated | 143 | 31.6 | 3 |
| **calibrated** | **139** | **16.0** | **3** |

**Roughly half the matching, for the same conclusions** -- the saving the design
predicted from the table, measured for the first time, and the thing that makes
`prefer` rows redundant rather than merely duplicated.

| | checks | failing |
|---|---|---|
| dormancy | 522 | 12 |
| **teaching's gate, and the 4 `prefer` checks retired** | **518** | **8** |

**The remaining 8 are acquisition and three singletons.** Anti-unification
producing a rule that fits a case neither example mentioned; an adopted rule
applying; a learned rule losing to an authored one; a learned rule concluding
wrapped. Then a re-ask costing one tick, and *a fact's own history is
matchable*, still unexplained.


---

## The flip is permanent

`Machine.run` is the table loop. The suite is **518 checks, 0 failing under BOTH
loops** -- every check that survives is loop-agnostic, and every check that was
not is either ported or deleted with the machinery it described.

The last four, and two of them were nothing to do with learning:

**The anchor.** `asking(<seat>)` is minted by a bare expression in the old tick,
and minting it is the whole of that line: a stratum-0 rule has to have something
to bind, and a corpus has no hand to seed it with. Without it *it was on, then it
was not* is well formed, matches on every other member, and **silently never
applies**. That was the unexplained failure carried for three rounds.

**The table could not learn.** `adopt` moves the rule set at run time and the
table was built once, so a rule the agent authored was live, was the node the
graph described, and had **no score** -- the round trip was open. `Table.absorb`
takes new rules in at the floor. That one closed five checks.

**Two exact counts were a loop's signature, not a property.** A re-ask costs 16
ticks under one loop and 19 under the other, the three being doubts deposited and
settled -- so the check is a bound now, which still bites if a re-ask ever became
a second search. And `supersedes` being too narrow showed as a **300-tick
runaway** under the option-set loop and as a quiescent wrong answer in 7 under
the table loop; the check asserted the runaway, so it was asserting one loop's
way of being wrong and would have read as *fixed* while the narrowness was
untouched. It asserts the defect now.

### What is red, and why

| | |
|---|---|
| `ugm.quiescence` | ⚠ **pre-existing** -- fails on the option-set loop too. Its `<silent>` rule is BLIND: suppressing it changes nothing, so the fixture does not exercise it |
| `ugm.learning`, `ugm.practice` | **caused by this**, and by one thing: `forgone` |

>**Complete forgoing is the option set, and that is the honest statement of it.**
>*What else could have served this want* ranges over every rule, so a prefix scan
>cannot answer it. The loop now forgoes the rivals it **actually weighed** -- the
>window -- which is arguably the better record (*what did you consider and not
>take*, rather than *what existed*), and it is not the same set.

That leaves a decision rather than a bug. Either **retire `ugm.learning` and
`ugm.practice` with the `prefer`-row subsystem** they instrument -- which is the
one already agreed superseded, now that a taught table reaches the same
conclusions with half the matching -- or **restore completeness for `forgone`
alone**, which may be affordable: rules are already indexed by what they
conclude, so *which other rules could serve this want* is a lookup rather than a
materialisation. The same join-not-scan move that brought back `overrides` and
`supersedes`.


---

## Complete forgoing, via an index — the third aggregate that wasn't one

*What else could have served this want* looked like it ranged over every rule.
It does, **if you ask it that way round.** `_wants` reads what an application
**consumed** -- one that consumed `goal(w)` is a response to wanting `w` -- so a
rival is a rule that could consume `goal(w)` too, and **only a rule whose
antecedent reads `goal` can**. That is a lookup, and it is usually a handful.

So the prefix scan keeps its window for **choosing** and asks a second, narrow
question for **passing up**. Same join-not-scan that recovered `overrides` and
`supersedes`, and the third time an apparent aggregate has turned into an index.

⚠ Paid only when the move serves a want at all -- most moves consume no goal and
cost nothing.

| | before | after |
|---|---|---|
| `ugm.learning` | 5 of 8 failing | **3** -- and forgoing itself passes |
| `ugm.practice` | 4 of 8 failing | **1 of 8** |

### ...and the gate had gone vacuous, which is the lesson of the day repeated

`Machine.run` **is** the table loop now, so `ugm.attention` was comparing the
table loop with itself. It reported `dungeon 0 / 143` -- one arm not running at
all -- and still exited 0.

>⚠⚠⚠ **A gate loses its other arm the moment the thing it gated becomes the
>default.** Nothing announces it; the comparison goes on printing. The option-set
>loop survives as `Machine.tick`, so the comparison drives that directly and the
>gate is a gate again: 11/16, 12/11, 18/21, 141/143.

### What remains red, and it is now one thing

`ugm.learning` (3) and `ugm.practice` (1) fail on the **`prefer`-row mechanism**
and nothing else -- an episode teaching the next one. That is the half already
established as superseded: `learned()` emits `fact prefer(<R>, key, score)`, and
the table's preference is its **score**, so the rows are written and never read.

The endpoint is the design's own sentence -- *the rules stay fixed; the
postconditions are what a learning process calibrates.* `learned()` should emit
**buffs** rather than `prefer` rows:

    fact prefer(<R>, water, 3)   ->   when { +water(?x) } => boost(<R>, 3)

Then offline learning writes what the loop actually obeys, and the two mechanisms
become one. `ugm.quiescence` stays red and is **pre-existing** -- its `<silent>`
rule is blind on either loop.
