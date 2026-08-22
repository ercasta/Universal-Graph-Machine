# `forest.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

Can an ensemble VOTE, and can it hand its work back? (§3, §12, §17, §19)

`machine.forest` is a gated NEGATIVE result: bagging loses to one tree, because

    `_priority` SUMS, and summation is not VOTING

-- an over-general member fires everywhere and no majority can overrule it. That
verdict was filed as a limitation of ensembles. It is not. It is a property of
combining members **through the preference table**, and this file is the same
ensemble combined somewhere else.

    python -m ugm.learning.forest

⭐⭐⭐ **An ensemble is a TOOL, and then voting is available.** `ugm.tools`
established the shape: `answers(<M>, ask)` binds an answerer in data, its answer
lands as `answered(...)` -- a record, not a claim -- and a corpus rule with an
authored rule turns it into a belief. Combination happens inside the answerer,
so five trees that disagree produce *one* answer with a count on it, and nothing
about `_priority` is involved. Measured below against the same ensemble loaded as
rules, which gets a romanesque cathedral wrong for exactly the recorded reason.

> **Rules ACCUMULATE. Only a function can take a vote.**

⚠⚠⚠ **And what the tool buys is not accuracy -- it is the ability for a minority
to LOSE.** Two attempts to explain the win were wrong and both are kept as
sections rather than deleted. It is *not* the class overlap: on a fixture where
one property separates the two kinds perfectly, the rules encoding still fails,
because a bootstrap bag that happens to draw a single class grows an **empty**
tree that fires on everything -- bagging manufactures the over-general member by
itself. The control that does isolate the mechanism is an ensemble that *cannot*
disagree (no resampling, no feature subsampling, five copies of one tree), and
there voting and accumulating tie exactly.

⚠⚠⚠ **The first fixture could not measure any of it, and read as three passing
gates.** `pointed` was on every gothic and no romanesque, so every bag learned
the same one-test tree and every vote was 5-0. A homogeneous fixture cannot
measure a discriminator -- the third time here. The repair is the transitional
building, which is what the real record looks like anyway: Durham is romanesque
with pointed arches and rib vaults, Laon is gothic and keeps a round arcade.
**And per-split feature subsampling turned out to be load-bearing**, not a
detail of the training loop: bagging rows alone left every tree identical,
because a perfectly pure property wins every split of every bag.

⭐⭐⭐ **And a forest is the one model class that can pay a tool's price.**
`ugm.tools` states the cost honestly: a tool's answer is §12's weakest link with
nothing behind it, and `why()` stops at the one place the agent cannot look. A
root-to-leaf path **is a rule** -- `a_learned_rule_is_a_decision_tree` read
backwards -- so this answerer renders its deciding path as ordinary corpus text.
Gated: load that text, **retire the forest**, and the verdict is reproduced by
the rules alone. The model hands its work to the engine and leaves.

⚠ **Positive tests only, and that is §9 rather than a simplification.** A tree
wants *not pointed*, and `-pointed($a)` does not mean it: §9's `-` is *an entry
denies this*, never *there is no such entry*. So a path here is a monotone
conjunction, and the two classes are learned as two positive concepts rather than
one predicate and its complement. What would otherwise be the negative branch is
`is_romanesque`, learned the same way -- and *neither fired* stays a real third
answer instead of collapsing into the majority class.

⚠ **The seed is on the record, because §3 forbids reading a derived result out of
an unseeded source.** Bagging is where the *random* in random forest actually
bites; inference is deterministic. `ugm.tools` closes on this caveat and this is
it arriving: `fact +seeded(<forest>, 7)` is in the corpus, and two runs of this
file are the same run.

## NO single property separates these, and th

⚠⚠⚠ **NO single property separates these, and the first version of this file
had one that did.** `pointed` was on every gothic and no romanesque, so every
bag learned the identical one-test tree, every vote was 5-0, and three gates
passed while measuring nothing -- a homogeneous fixture cannot measure a
discriminator, for the third time in this project.

The repair is the transitional building, which is also what the real record
looks like: Durham is romanesque and has pointed arches and rib vaults; Laon
is gothic and keeps a round arcade; Wells is gothic with romanesque wall
thickness. Every column below is now impure, so which test a bag prefers
depends on the bag -- which is the only condition under which an ensemble has
anything to disagree about.

## `_grow`

One tree: the conjunction of tests that best isolates `label`.

    Greedy and positive-only, and it stops when no test improves purity -- so a
    bag with nothing to separate returns the EMPTY conjunction, which matches
    everything. That degenerate tree is not a bug to be prevented: it is the
    over-general member `machine.forest` failed on, and the comparison below
    depends on the fixture being able to produce one.

    ⚠⚠⚠ **Per-split FEATURE subsampling, and leaving it out is what made the
    first fixture unmeasurable.** Bagging the examples alone was not enough:
    `flying` is perfectly pure here, so it won every split of every bag and all
    five trees came out identical. That is the *random* in random forest doing
    the job it exists for -- diversity comes from withholding the obvious
    feature from some trees, not from resampling rows.

## -- was it the OVERLAP? measured, and the answer

-- was it the OVERLAP? measured, and the answer was no ----------------

⚠⚠⚠ This section was written to confirm that transitional buildings are
what break the rules encoding, on a fixture where `pointed` separates the
classes perfectly. It refuted that: the rules still lose. A degenerate BAG
-- one that happens to draw a single class -- grows an empty tree whatever
the data looks like, so bagging manufactures the over-general member by
itself. Kept as the refutation rather than deleted as a failed control.

## What this corpus is willing to act on, in t

⚠⚠ **What this corpus is willing to act on, in two lines.** The two
encodings say the verdict differently -- a rules-as-ensemble member
concludes `is_gothic($c)` flat, the tool's corpus concludes
`possible(is_gothic($c))` -- so the corpus has to say which of those
it will treat a cathedral on.

⭐ And this corpus is RECKLESS, deliberately: it acts on a merely
possible classification, which is what costs it the goal below. Under
grades that recklessness was invisible -- `<treat>` matched
`is_gothic($c)` whatever grade the entry carried, because nothing
could read a grade -- so an agent could not have declined even if its
author had wanted it to. Now the recklessness is one line, and
deleting it is how you get a careful agent.
