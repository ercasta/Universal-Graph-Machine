# Reading is a walk

Because a moment stores only what changed, a moment does not contain its state.

> **The state is what the chain answers.**

So *does `on(a, b)` hold here?* means: walk back along the predecessor
relation, collecting entries that name this proposition, and decide between them.

This chapter is the single most important program in the machine. Everything in
Part 1 exists so that this walk can answer well, and everything after Part 1 is
written against its answers.

## Two indices, in this order

An entry has both a **locus** (what it's about) and a **deposit moment** (when it
was claimed) — Chapter 2. The walk uses both, in a fixed order:

> **Latest locus, then latest deposit.**

An entry is a *candidate* if its locus is at or before the moment you're asking
about. That's inheritance, and it's why the locus can't simply be matched for
equality — `on(a, b)` asserted at `M3` is what makes it hold at `M7`, where no
entry mentions it at all.

Among the candidates, the **latest locus** wins, because the most recent claim
about the world is the one that governs.

Only when two claims share a locus does the **latest deposit** decide. That is
exactly the revision case: two things said about the same moment, and the later
thought supersedes the earlier one.

Neither key alone will do:

- **Locus alone** cannot tell a revision from the claim it revises.
- **Deposit alone** would let a newly formed belief about the distant past
  overrule a settled belief about the recent past — the machine would forget
  that the world had moved on.

## Two questions, one structure

Now the payoff.

*What do I now think about M7?* — walk back from where you are standing.

*What did I think at M7?* — walk back from M7 instead. The entries deposited
later are simply not on that walk.

Same walk, different starting point, and no second mechanism. A design with a
single index would have had to choose which of those two questions to keep.

In the common case — an entry deposited at its own locus — the two questions
coincide, which is why the distinction is easy to miss until it matters.

## At-or-before is ancestry, never depth

The candidacy test walks the predecessor relation. It cannot be a comparison of
depth numbers, and the reason is worth knowing before you need it:

**supposing forks the chain by construction.** Two moments at the same depth on
different branches aren't comparable at all — neither is before the other.

This is the cheapest place in the design to introduce a bug that only appears
once you start using hypotheticals. It's also what makes containment (Chapter
16) free rather than enforced: your imaginings can't leak into the real world,
not because something forbids it, but because the walk from the real world
cannot reach them.

The two stand or fall together.

## One order throughout

The two indices settle *which* entry wins. They don't, by themselves, settle the
order the walk enumerates in — and that order is what "the most recent one"
means when several entries fit a description.

Measured, the walk once disagreed with itself: ancestry was newest-first and a
moment's delta was oldest-first, so two candidates deposited by one connective
came out in the opposite order to two deposited by the other. Which connective a
rule used has nothing to do with what a description refers to. One reversal made
the walk one order throughout.

> **A deterministic computation whose result depends on an undeclared
> enumeration order has a tie-break nobody authored.**

That line comes up again for rankings (Chapter 27) and for random draws. It's
one of this project's standing lessons.

## What it costs, and what was done about it

The walk is the largest recurring cost in the design. On one goal fixture,
before anything was done, resolving reads was **86% of runtime**, and sixteen of
every seventeen walks were the same walk repeated.

Three changes, each measured before the next, and none of them touching what the
read *means*:

- ask the walk once per tick rather than once per rule,
- index the resolved state by (sign, relation),
- index the resolution by proposition.

Together: **67×**.

Later, a second round. Keeping the resolved state and then rebuilding everything
derived from it keeps the cost you were paying; maintaining all three where the
state lives — the state, its index, and the keys read off it — took the loop
from quadratic to **linear**. Measured: 1,600 facts from 4.79s to **0.48s**, and
12,800 facts in less time than 1,600 used to take. Doubling doubles.

!!! note "Deep dive: why that's an optimisation and not a debt"
    Chapter 32 draws the line explicitly, and this is the cleanest example of
    the good side of it.

    The kept state is an *optimisation of a semantics*. The slow definition —
    the actual walk — still exists, and a gate holds the fast path to it on
    **every look, in every fixture**: 7,288 looks, 0 disagreements on the run
    that established it. If they ever disagree, that's a bug, findable and
    reported.

    A cache of a *claim* has no slow definition to be held to, because the claim
    is the definition. When it goes wrong, the failure is silence. That's why
    the precedence table of Chapter 17 was deleted and the state index was not.

One column of that gate is the one no test suite can supply, and it's worth
stating because it generalises:

> **Nothing that asserts what the agent concluded can see what it was thinking
> about while it concluded it.** A wrong key set makes a *worse choice*, never a
> *wrong conclusion*, and every fixture asserts an outcome the loop reaches
> anyway.

## The scoring

| | locus only | deposit only | **two keys, locus first** |
|---|---|---|---|
| not leaking | a revision and the claim it revises are indistinguishable; one silently wins | a new belief about the distant past overrules a settled one about the recent past | each key answers the question it is for |
| not lossy | yes | yes | both the original and the revision remain readable |
| readable | one walk | one walk | one walk, two comparisons |
| composable | two authors revising one locus collide | — | later deposit settles it, and both survive |

---

That's Part 1. You now know what memory looks like: nodes with ordered members;
propositions that claim nothing; entries that claim them, with a sign and a
locus; moments that hold what changed; and a walk that answers.

Everything from here is **taught**, not built in.

**Next:** the first and most important thing you teach it.
[A rule is a fact about two moments →](../rules/06-a-rule-is-a-fact.md)
