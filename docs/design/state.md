# `state.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

Does what the agent keeps agree with what the walk says?

`Machine._kept` is an optimisation of a semantics, and §20's floor gate is this
design's standing answer to that: the slow definition stays, so the fast one can
be **held to it** rather than trusted. `agreement` does it for the read,
`ugm.arbitration` for the move; this does it for the state.

The slow definition is §4's walk -- `rules.current_state`, every proposition the
chain has ever claimed on this branch, each one `resolve`d, newest-first --
filtered by what is out of mind. Nothing in the loop calls it any more.

Three things are compared on **every look at the state, in every fixture in the
suite**, and they are three because a state can be right while what is read off
it is wrong:

    state     the entries, IN ORDER -- §18's *the most recent wins* rests on it
    index     what `Situation.candidates` answers, per sign and relation
    keys      `_in_play`: what the situation is about, which orders arbitration
    mentions  `relations_of`: which relations a NODE is spoken of under, which
              is what attention lifts a rule with

⚠ The three fail in different ways and only the first is loud. A wrong state
concludes from a premise that was denied; a wrong index silently stops a rule
applying; wrong keys only make a worse choice, which no fixture asserting an
outcome can see. That is why the keys are compared here rather than left to the
checks that read them.

⚠ What this cannot check is the fixtures it is given -- the homogeneous-fixture
trap, recorded twice in this repo. A state that is wrong only after a denial is
wrong invisibly if nothing denies anything, so the tally prints how many looks
followed a supersession and how many had a live goal, and a run where either is
small is a run that measured very little.

Kill-probed five ways, and each lands in its own column. The last row is the
one that justifies the instrument existing at all:

| break | the suite | state | index | keys | mentions |
|---|---|---|---|---|---|
| never drop a superseded entry | 2 | 806 | 806 | 0 | -- |
| never decrement a goal's key | 1 | 0 | 0 | 8 | -- |
| never invalidate a bucket's read | 29 | 0 | 3,884 | 0 | -- |
| rebuild the state newest-first | 6 | 6,456 | 6,456 | 0 | -- |
| **one key cache for every seat** | **0** | 0 | 0 | **1,597** | -- |
| **never decrement a node's relation** | **0** | 0 | 0 | 0 | **992** |

⭐ The suite cannot see the fifth, and that is not a gap in the fixtures: a
wrong key set makes a worse choice, and every fixture here asserts an outcome
that the loop reaches anyway. Nothing that asserts what the agent concluded can
see what it was thinking about while it concluded it. The sixth is the same
sentence one index along -- a stale mention makes a worse SHORTLIST -- which is
why it is here and not in `ugm.selftest`.

⚠⚠⚠ **And the mentions column had to be made to fail before it was worth
anything.** A first version compared which relations a node is spoken of under
and reported 0 disagreements with the decrement removed entirely. The reason is
worth keeping: a denial does not remove an entry, it replaces `+q(a)` with
`-q(a)`, and those are two keys mentioning one node under one relation. Across
the one operation the column exists to watch, the relation SET does not move and
the count is off by one. So the comparison is over the counts.

⚠ Two branches of `_mention` are NOT exercised by anything here, and saying so
is cheaper than implying otherwise. Re-adding an entry already in a bucket
(`fresh`) and a count actually reaching zero both probe clean at 0 -- the first
because nothing adds one entry twice, the second because a supersession always
pairs the drop with an add of the same node under the same relation. A count
reaches zero only when a proposition leaves the state entirely.

## The index, asked of every key either side has an

The index, asked of every key either side has an opinion about -- the
bare-variable bucket, the per-relation ones, and the per-argument ones
a join narrows to.

⚠ Asked through `bucket`, never off `_by`, and the difference is the
whole value of the column: a first version compared the dicts directly
and could not see one read back in the wrong ORDER, or a stale
reversal handed out after the state moved on. Choosing the key is not
compared, because choosing it is a pure function of the pattern --
what is maintained, and so what can drift, is the bucket.

## The fourth, and it is the quietest of the four:

The fourth, and it is the quietest of the four: `relations_of` is
read to LIFT a rule, so a stale count makes a worse shortlist and
never a wrong conclusion. Exactly the column `keys` is here for, one
index along -- and the counting is the part that can drift, because
`add` and `drop` are the only two places it is ever right or wrong.

⚠⚠⚠ **The COUNTS, not the relations, and the difference is whether
this column measures anything at all.** A first version compared the
relation sets and could not see `drop` disabled entirely: a denial
does not remove an entry, it REPLACES `+q(a)` with `-q(a)`, and the
two are different keys mentioning one node under one relation. So the
set is unchanged across the one operation the column exists to watch,
and the count is off by one. Probed: with the decrement removed the
set comparison reported 0 disagreements over 7,126 looks.
