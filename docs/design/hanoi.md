# `hanoi.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

Hanoi: the fixture that isolates BINDING choice, and a recursion that transfers.

    python -m ugm.probes.hanoi

Every other fixture here measures which RULE to reach for. None could measure
which BINDING, and `ugm.workload` -- the one built for scale -- has exactly ONE
individual (`item`), so it cannot measure it even in principle. That gap is why
the binding conclusions drawn from the dungeon were worth so little: it has
three combatants.

Hanoi has one action, and every step of the puzzle is a choice of binding for
it. Rule selection contributes nothing. That is the whole reason to have it.

## It can fail, and four earlier versions did

A benchmark that cannot fail is worse than none, because it reads as evidence.
This one failed four times before it worked, and each failure is a finding:

| what was written | what happened |
|---|---|
| a free-standing `<move>` | only LEGAL moves, and `d1` shuttles for ever: 155 moves, never solved |
| the decomposition under `goal(...)` | the bundle's backward reader took **153 of 200 ticks** while `<move>` had one live application -- the correct one -- and never got a turn |
| `built`/`at`/`site` as derived facts | the engine does not retract (§12), so `built(d2, d3)` still stood after d2 had moved to `y`, and the want was met by a memory |
| the recursion guarded on WORLD STATE | `on(d2, d3)` holds again on the way back, so `<unstack>` re-fired and recreated a want it had already met |

⭐⭐⭐ **The fourth is the one that matters, and it is why the phase exists.**
Hanoi's recursion is depth-first and ORDERED -- unstack, then place, then
restack -- and world state cannot say which of the three you are in: `at(d1, x)`
is equally true on the way out and on the way back. Guards read off the world
are therefore ambiguous by construction, and no number of them fixes it.

So a call is a NODE, minted per occasion, carrying its own pegs and its own
PHASE. *Which step of this call am I on* becomes a fact. That is
`docs/HANDOFF.md`'s *a multi-tick plan is a NODE, not a string* -- reached from
the other direction, by writing the alternative and watching it fail.

 Minted per OCCASION and not per parameters, which matters here rather than in
principle: `solve(d1, x, z, y)` occurs TWICE in a three-disk solution, so a call
node keyed on its arguments would collide with itself and refraction would block
the second. `+call` mints one node per application, which is exactly right.

## The stack is the bundle's; the strategy is Hanoi's

⭐⭐⭐ **The plumbing is three bundled rules and mentions no domain at all**:
`<call-spawn>`, `<call-advance>`, `<call-return>`. What makes them shareable is
that a call carries its parameters as ONE node -- `call($c, tower($d,$f,$t,$s))`
rather than five arguments -- so the arity is the domain's business and the
stack never sees it. The stage ORDER is data a corpus deposits
(`advances(unstacking, placing)`, `closes(waiting)`), because the order of the
steps is exactly what differs between one recursive plan and the next.

 **One domain cannot show that a mechanism is general**, so there are two.
`COUNTDOWN` below shares nothing with Hanoi -- no disks, no pegs, no `want`, no
action -- and runs on the same three rules. Before the split, `<unstacked>` and
`<restacked>` were rules in this file; they are now the bundle's `<call-advance>`
and `<call-return>` plus two facts.

 And this is NOT a second planner. `<expand>` in the bundle is a STRATEGY --
means-ends, decompose a goal by some rule's antecedents -- and it stays exactly
what it was. What is shared here is what any strategy needs underneath it.

## What it establishes

    disks   optimal   moves made        rules naming a disk or peg
    3         7         7  identical                 0
    4        15        15  identical                 0
    5        31        31  identical                 0
    6        63        63  identical                 0
    7       127       127  identical                 0

Not *close to* optimal: the move sequence is identical to the recursive solution
at every size. And the transfer result is the strongest form there is -- **the
same rules, unchanged, are optimal at every size, and not one of them names an
individual.** Nothing was retuned, and there is nothing in them that could be.

## ...and the recursion is LEARNED, not only authored

Watching the authored solve on 3 and 4 disks and anti-unifying each rule's own
firings recovers **10 of the 12 rules exactly**, modulo what a person called a
variable -- including the two that matter:

    <descend>  parent tower($d,$f,$t,$s)  spawns  tower($e,$f,$s,$t)
    <ascend>   parent tower($d,$f,$t,$s)  spawns  tower($e,$s,$t,$f)

That permutation IS Hanoi. Nothing here searches: `generalise` is the dual of
`unify` and it reads the mapping straight off two examples.

**The learned rules alone -- nothing authored but the puzzle itself -- solve 5,
6 and 7 disks in the optimal sequence, having seen only 3 and 4.**

 **Two demonstrations, and ONE is not enough** -- which is what makes the
result mean anything. Taught on 3 alone, two rules fire once and are declined
outright, and what is induced does not solve even the size it was taught on.
Taught on 3 and 4, nothing is declined. The repo already had this as *experience
means more than one fight*; here it is a pass/fail rather than a degradation.

 **The two rules it does NOT recover are the sharp finding.** `<base>` and
`<leaf>` keep `d1` where a person wrote `$d`, and no number of SIZES fixes it:
the smallest disk is called `d1` at every size, so varying `n` never varies that
argument. Varying the size does not vary everything, and what a demonstration
holds constant is what a learner will believe is necessary. They still solve --
`d1` is genuinely the smallest in every puzzle this generator makes -- so the
defect is invisible in the outcome and visible only in the diff against what a
person wrote. Which is the reason to compare against the authored rule at all,
rather than only against the behaviour.

 What is NOT learned is the plumbing: `<call-spawn>`, `<call-advance>` and
`<call-return>` are the bundle's, and the demonstration teaches the domain.

 And the teacher demonstrates CALLS, not only moves. Inferring the call tree
from a bare move trace is program induction and is not attempted here -- stated
because the difference is the whole of what this result claims.

 The recursion below is AUTHORED, and learning it is measured against it. What this fixture provides is the
target: a corpus whose knowledge is entirely structural, on a task where an
identity-keyed version cannot work at all, and a teacher that CAN supervise a
binding -- which `ugm.teaching`'s cannot, because `arbitrate` keys on
`(score(rule), rules.index(rule))`, so two applications of one rule tie and the
first in walk order wins. Asked where the table took a binding it would not
have, it answered 0 times in 148 dungeon moves.

## -- learning the recursion from watching it -----

-- learning the recursion from watching it -------------------------------

⭐⭐⭐ **What is learned is the PERMUTATION**, and it is the whole insight of
Hanoi: a parent call `tower($d, $f, $t, $s)` spawns `tower($e, $f, $s, $t)` on
the way down and `tower($e, $s, $t, $f)` on the way back. Anti-unification --
`generalise`, the dual of `unify`, which this repository already had -- reads
both straight off two demonstrations.

 **Examples cross as TEXT.** A node id means nothing outside the graph that
minted it, so two demonstrations on two machines cannot share one, and this is
the repo's own rule for what may cross (`ugm/table.py`) arriving on the
learning side.

 **A minted node has no name, and the whole call stack is minted**, so
every example about `stage($c, ...)` was unsayable -- which is every example
about the recursion. `_sayable` gives one a placeholder, and the placeholder
has to be UNIQUE PER EXAMPLE: the same within an example so `$c` co-refers,
and different across them, or two unrelated calls anti-unify to a constant and
the rule is about one call for ever.

## `misbehave`

Two bad attempts, and what becomes of them.

    ⭐⭐⭐ The whole of what step 2 buys. Before it, an attempt to move a covered
    disk simply matched nothing -- and *nothing happened* is indistinguishable
    from *nothing was wrong*. Now:

        covered      the world model declines it, and says why
        unafforded   the MACHINERY declines it, because no such action exists

     **The decline is LATE.** The attempt stands from tick 0 and is not
    declined until tick ~101, because `<covered>` sits at the floor and the
    shortlist is busy with the recursion. Correct, and slow: a refusal the agent
    only learns about after it has finished is a poor thing to learn from. That
    is the concrete argument for attending to what a move just wrote -- an
    attempt is a fresh fact, and nothing currently lifts the rules about it.

     The two are declined by different things on purpose. What is LEGAL is the
    world model's business and a rule says it; what EXISTS is the palette's, and
    only the machinery can check it, because subsumption runs the pattern
    against the entry and here the entry is the generic one.
