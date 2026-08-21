# The read

Because a moment stores only what changed, a moment does not contain its state.

> **The state is what the chain answers.**

So *does `on(a, b)` hold?* means: of everything ever claimed about that
proposition, what stands now?

This chapter is the single most important program in the machine. Everything in
Part 1 exists so that this can answer well, and everything after Part 1 is
written against its answers.

## The whole of it

> **Later supersedes earlier.**

Claims about a proposition are kept in the order they were deposited. The read
takes the last one. If there is none, nothing has been said — which is
*inherit*, not *false* (Chapter 3).

That is the entire rule, and in the code it is one index lookup. It is worth
dwelling on how much it is *not* doing:

- It does not walk backwards through moments.
- It does not compare depths, or test ancestry.
- It does not ask *at which moment* — there is no second time to ask about.

A claim is superseded only by a later claim **about the same proposition**.
Nothing else can displace it, so nothing else has to be consulted.

!!! note "This used to be a walk, and the walk was the design's biggest cost"
    An entry used to carry a **locus** — what it was *about* — beside its
    deposit moment, so the read had to use both keys in a fixed order:
    *latest locus, then latest deposit*. An entry was a candidate only if its
    locus was at-or-before the moment being asked about, and *at-or-before* had
    to be **ancestry** rather than a depth comparison, because supposing forked
    the chain.

    Two keys and two ancestry walks bought a real capability: *what did I think
    at M7* was the same walk from a different starting point, so revising a
    view of the past was ordinary. It also made reading **86% of runtime**.

    Both the locus and the fork are gone. What remains answers one question —
    *what do I think now* — and answers it in a lookup. Saying something about
    a past moment is a corpus's job now, written into the proposition where a
    rule can argue with it (Chapters 19 and 23), and the machinery keeps every
    entry in deposit order so the raw history is still there to walk when a
    rule wants it.

## Nothing is thrown away

The claim that lost is still in the chain. Superseding is **appending**, not
overwriting, so:

- `why` can name the entry that won *and* the ones it beat;
- a rule can walk the raw chain and find what was true earlier (Chapter 23);
- and *the world moved* stays distinguishable from *I was wrong*, which is what
  the two levels of Chapter 2 were bought for.

> **The superseded claim was never lost. It was never in the *state***, which
> is a different thing.

## One order throughout

The read settles *which* entry wins. It does not, by itself, settle the order
things are enumerated in elsewhere — and that order is what "the most recent
one" means when several entries fit a description.

Measured, the walk once disagreed with itself: ancestry was newest-first and a
moment's delta was oldest-first, so two candidates deposited by one connective
came out in the opposite order to two deposited by the other. Which connective a
rule used has nothing to do with what a description refers to. One reversal made
the walk one order throughout.

> **A deterministic computation whose result depends on an undeclared
> enumeration order has a tie-break nobody authored.**

That line comes up again for rankings (Chapter 27) and for random draws. It's
one of this project's standing lessons.

## What it cost, and what was done about it

While the read was a walk it was the largest recurring cost in the design. On
one goal fixture, before anything was done, resolving reads was **86% of
runtime**, and sixteen of every seventeen walks were the same walk repeated.
Everything below was measured then, and every one of the optimisations still
stands — the read got cheaper again when the locus went, but the state is still
kept and still indexed, because *the state* and *one proposition's answer* are
different questions.

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
    the precedence table Chapter 17 describes was deleted and the state index
    was not.

One column of that gate is the one no test suite can supply, and it's worth
stating because it generalises:

> **Nothing that asserts what the agent concluded can see what it was thinking
> about while it concluded it.** A wrong key set makes a *worse choice*, never a
> *wrong conclusion*, and every fixture asserts an outcome the loop reaches
> anyway.

## The scoring

| | overwrite in place | keep every claim, read the last | **and also keep a locus** |
|---|---|---|---|
| not leaking | a revision and the claim it revises are indistinguishable | each claim survives; the last one governs | each key answers the question it is for |
| not lossy | history is gone | nothing is overwritten | nothing is overwritten |
| readable | a lookup | **a lookup** | a walk with two comparisons and two ancestry tests |
| composable | two writers contend | appending is the only write | two authors revising one locus collide |

The third column is what this design ran for a long time, and the middle column
is what it runs now. The trade is stated rather than hidden: a question was
given up — *what did I think back then*, answered directly — and the read
became a lookup.

---

That's Part 1. You now know what memory looks like: nodes with ordered members;
propositions that claim nothing; entries that claim them, with a sign;
moments that hold what changed; and one rule that answers.

Everything from here is **taught**, not built in.

**Next:** the first and most important thing you teach it.
[A rule is a fact about two moments →](../rules/06-a-rule-is-a-fact.md)
