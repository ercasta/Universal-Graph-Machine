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
