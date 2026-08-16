# Deleting the option-set loop — the work list

The author's decision: **the table loop is the loop, and the option-set loop
goes.** The engine is experimental and owes nobody stability, so a check that
only makes sense for the loop being deleted may be deleted with it.

This file is the measured work list rather than a plan. Every line below comes
from running the suite with `Machine.run` pointed at `attention.run`, which is
now a one-line change because the table loop returns `Step`s.

    58 of 545 checks fail, and 1 raises.

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

### A. Delete with the loop — 6

These are about machinery that is going. The check goes with the code.

| check | why |
|---|---|
| `matching_is_incremental` (raises) | `_match_cache`, an optimisation of `_materialise` |
| the machine counted its selections | `m.selections`, the old tick's counter |
| and the tick reports which silence it was | the old `Step.state` taxonomy |
| what it keeps, it no longer re-weighs | weighing an **option set** the new loop never builds |
| ...and it is LINEAR in the corpus (weighing) | same |
| a higher score outranks a lower one — cardinals | the old preference score; the table **is** the score now |

### B. Accepted losses — 3

Claims about a set the prefix scan deliberately never materialises.

| | |
|---|---|
| `close` | already accepted, and the only entry in `ACCEPTED_LOSSES` |
| **`forgone`** | ⚠ **decide before deleting.** *Taking one way passes up the others* is called a **safety** property in its own check — *an act cannot be taken back* — and 4 checks rest on it. It is the same shape as `close`, but the argument for keeping it is stronger |
| and once one is clearly better, there is no doubt left | doubt over the whole option set |

### C. Port — the real work, ~20

**Stopping (10).** The table loop has `stop`, a postcondition. It has no
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
