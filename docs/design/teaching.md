# `teaching.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

Bootstrapping the table from use. (the author's design)

    python -m ugm.learning.teaching

> A human is the first, manual user of the KB.

⭐⭐⭐ **AND IT PAYS, which is measured here for the first time.** A table taught
from one demonstration reaches the same conclusions about the world and gets
there with **roughly half the matching**:

    quest-p1   21 -> 18 moves, 18.8 -> 11.1 matched/move, 0 domain conclusions lost
    dungeon   143 -> 139 moves, 31.6 -> 16.0 matched/move, 0 additional lost

⚠⚠⚠ **The gate said the opposite until it was pointed at the right thing.** It
counted every proposition the taught run did not reach, and a calibrated table
**hesitates less** -- so it deposits fewer `close`, `settled` and
`spent(<settle-doubt>, ...)` records, and the gate read the mechanism working as
the mechanism failing. Measured on `quest-p1`: all nine "lost" conclusions were
doubt bookkeeping and **not one was about the world**.

Not a labelling task run beside the system: the ordinary first use of a corpus,
by a person who steps it and picks the next rule. They are doing exactly what
the table will later do, so what they leave behind is the table. The learning is
the residue of the use, which is this repo's recurring shape.

Two signals come out of that use and only one of them is calibration:

    the wrong order        a buff -- this rule should have come first here
    none of these fits     a MISSING RULE, which no calibration can supply

The second is the more valuable one early, and only manual use surfaces it. This
file is about the first.

## Why there is a teacher here that is not a human

The reflex experiment in `ugm.attention` settled what a demonstration may
produce: damping every rule that was tried and missed cost 125 conclusions,
because *tried and missed* is not evidence a rule is unimportant -- it is
evidence it did not apply **in that state**. So a demonstration has to produce
something CONDITIONAL, keyed on what was true at the time:

    rule <A> = ...
      learned after <A> { ... } => attend(?x, n)

⚠⚠⚠ **The bigram arms are gone, and the measurement is why.** The smallest
conditional thing that carries a sequence used to be a bigram on the rule that
just applied -- `after <A> => boost(<R>, n)`, *after A, prefer R* -- with a query
added by anti-unification. Three arms were built on it (`bigram`, `query`,
`occasion`) and every one named a RULE. On the dungeon the node-keyed arm beat
all three (13.0 matched/move against 17.2, 32.8 and 44.4, the last WORSE than
doing nothing), so they are retired with the buffs they spent. What survives is
`focus`, and the anti-unification that built their queries survives with it --
it is `_query`, and it now conditions an attention lesson instead.

**And the mechanism can be validated with no human at all.** The shipped loop's
arbitration already picks a move at every step, deterministically, over the full
option set. Let it teach; then ask whether the table loop, calibrated from its
sequence, makes the same moves it does. If bootstrapping cannot imitate a
teacher that is right by construction, it will not learn from a person either.

Three things are measured, and they are the three claims:

    agreement    does the table pick what the teacher picked
    matched/move does the cost claim move (29.6 uncalibrated)
    conclusions  does anything get lost

## ...and a fourth lesson, which is not about rules at all

Every arm above teaches the table which RULE to reach for. `focus` teaches the
agent what to think ABOUT -- `after <A> => unattend, attend(?x)`, keyed on a
node -- and so it is the only one that can reach the BINDING, which no buff can
name.

⚠⚠⚠ **It cannot be learned from the teacher, and finding that out is half the
result.** `arbitrate`'s key is `(score(rule), rules.index(rule))`, so two
applications of one rule tie exactly and the first in walk order wins: **the gold
teacher is binding-blind in precisely the way the table is.** Asked *where did
the table take a binding you would not have*, it answered **0 times in 148
dungeon moves**. A teacher cannot supervise what it cannot see, and a lesson
built on that question would learn nothing for ever and read as a corpus with
nothing to teach.

So the signal is **carry-over**, taken from play alone: the next move was about
this too. Which variable to attend to is then decided by how many DISTINCT
things it was ever bound to -- the one that varies. On the dungeon `<check-ac>`
has four variables that carry every single time, and attending to four things is
attending to nothing.

⚠ **What it is worth, honestly: nothing this harness can see.** Measured, it
costs nothing and loses nothing -- and it does not deliver the bigram's speed
either.

| dungeon | posts | moves | matched/move | agrees | domain conclusions lost |
|---|---|---|---|---|---|
| none | -- | 143 | 31.6 | -- | 3 |
| bigram | 30 | 139 | **16.0** | 131/148 | 3 |
| **focus** | 15 | 142 | 30.3 | 134/148 | **3** |

The 15 extra conclusions the focus arm reaches are its own `attention` deposits
and doubt bookkeeping -- **not one is about the world**, which is why `attention`
is in `BOOKKEEPING`. What it buys is the binding, and this harness's teacher is
exactly the instrument that cannot show that. `ugm.selftest` shows it on a
constructed case instead, which is the honest place for it.

## What the move just bound, and whether the

⭐⭐⭐ **What the move just bound, and whether the next move was about
it too.** `(rule, "?x") -> times the value `?x` took carried into the
following move`, beside `values`, which is how many DISTINCT things
that variable was ever bound to.

⚠⚠⚠ **This signal comes from PLAY and not from the teacher, and it
has to.** The gold teacher is `arbitrate`, whose key is
`(score(rule), rules.index(rule))` -- so two applications of one rule
tie exactly and the first in walk order wins. **The teacher is
binding-blind in precisely the way the table is**, and measured on the
dungeon it never once preferred a binding the walk would not have
taken: 0 occasions in 148 moves. A teacher cannot supervise what it
cannot see, so a binding lesson learned by asking *where was the table
wrong* would learn nothing, for ever, and look like a corpus problem.

Carry-over needs no judgement: it is a fact about the sequence the
agent actually produced. *The next move was about this too* is
observable from play alone.

## THE RULE'S OWN SITUATION -- what made this move

THE RULE'S OWN SITUATION -- what made this move available -- and the
keying went round a full circle to get back here. As a learned RULE a
recogniser keyed this way can never fire in time, because by the time
its query holds the target is already applicable; that is why it was
moved to the precursor, the state one move earlier. As a RERANKER the
objection is gone: it is consulted while the shortlist is being
ordered, which is exactly when the target is applicable.

And the precursor turned out to be unusable here for a reason worth
keeping: a player's moves are separated by bookkeeping -- settling a
doubt, recording an act -- so the previous move's premises share
nothing across 15 demonstrations and generalise to nothing at all.
A pipeline has stable precursors; a decision does not.

As TEXT, from the start: experience comes from several fights, a fight
is its own machine, and a node id from one means nothing in another.
The utterance is what crosses (`ugm/table.py`), here at the moment the
example is taken rather than at the end.

## `focuses`

What to think ABOUT after each rule: one variable per rule, learned
        from what carried into the following move.

        ⭐⭐⭐ **One per rule, and choosing which is the whole design.** On the
        dungeon, `<check-ac>` has four variables that carry into the next move
        every single time it fires. Attending to all four is attending to
        everything, which is measurably the same as attending to nothing.

        So the variable is chosen by **how many distinct things it was ever
        bound to** -- the one that VARIES. A variable always bound to `me` or to
        one constant individuates nobody and lifting on it lifts always; a
        variable that took a different goblin each time is the one attention
        exists for. That is `generalise`'s own signal, which turns a constant
        into a variable across demonstrations, read one level up to decide what
        is worth attending to rather than what is worth saying.

        ⚠ Two firings at least, for this file's standing reason: one example
        generalises to itself.

## `emit`

What was learned about ATTENTION, as a document a person can read.

    ⭐⭐⭐ **This file has claimed since it was written that a lesson is a
    document** -- *savable, diffable, arguable, and loadable into a corpus that
    was never taught* -- and it had no `open` and no `write` in it. The text was
    built, loaded, and dropped on the floor. This is the missing half.

    ⚠ It is the ORDINARY SURFACE, so it round-trips by construction: `Loader`
    reads it back with no special path, a person can edit a line in place, and
    an edited line and a learned one are indistinguishable to the machine. That
    is the property wanted for *bootstrapped by authors, refined by play, edited
    again* -- and it is why the marker exists, since it is the only thing that
    then tells them apart.

    ⚠⚠ Only attention. `prefer` and the score buffs are not emitted, because
    they name other rules and are on their way out for exactly that reason.

## The trigger form, as text: a lesson is a documen

The trigger form, as text: a lesson is a document.

⚠ There were two more -- `WHEN` and `AFTER`, both writing `boost(<R>, n)`.
They are retired with the buffs, and with them `Lesson.lessons`,
`Lesson.recognisers`, `install` and `install_recognisers`.
⭐⭐⭐ **A learned lesson ADJUSTS rather than replaces**, and for attention that
is the absence of `unattend`: the lesson says *and also think about this*,
adding to whatever else is attended rather than clearing the field first.

⚠ It was `unattend, attend(?v)` and the clearing was doing real work -- a
claim has no `LIFE`, so attention accumulates without something to take it
back. What replaces it is the automatic half, which is not built:
`docs/HANDOFF.md` 20d records attending the last move's right-hand side being
tried and backed out. Until that lands this is the only thing bounding the
set, and the measurement below is what says whether it matters.
⭐⭐⭐ **The weight is the EVIDENCE.** A lesson seen nine times says the node
matters more than one seen twice, and that multiplier is what lets a learned
lesson stand out from the nodes a move merely wrote -- which all arrive at the
same depth in the queue and cannot otherwise be told apart.

## What a taught table is allowed to conclude

⭐⭐⭐ **What a taught table is allowed to conclude differently.** Every one of
these is the agent's own bookkeeping about HOW it decided, never a claim about
the world: `close` is a doubt, `settled` is that doubt resolved, `spent` names
the premises a move consumed, and `exercised` records which rule ran.

Counting them made the gate measure the wrong thing, and it measured it
backwards. A calibrated table hesitates LESS -- that is the whole point of
calibrating it -- so it deposits fewer doubts, and the gate read the mechanism
working as the mechanism failing. Measured on `quest-p1`: **all nine "lost"
conclusions were `close`, `settled` and `spent(<settle-doubt>, ...)`, and not
one was about the world.**

This is `ugm.attention`'s rule one construct along -- *the comparison has to be
over conclusions rather than over moves, because two runs that reach the same
beliefs by different routes agree about the world, and that is the question.*

⚠ The gate keeps its teeth: `intends` is a domain relation and IS lost on the
dungeon -- by the UNCALIBRATED arm too, which is what says the loss is not
calibration's doing.
⚠⚠⚠ **`attention` is here, and leaving it out flattered the mechanism.** A
focus lesson deposits `attention(...)` and denies it again, so the focus arm
reached **538 conclusions against 523** uncalibrated -- and counted naively
that reads as *attention makes the agent conclude more*. Measured: all 15 were
`attention` (18 of them) and doubt bookkeeping, and **not one was about the
world**. The same trap this list already records for `close` and `settled`,
arriving from the arm that was added last.

## none is the UNCALIBRATED arm, and it went mi

⚠ `none` is the UNCALIBRATED arm, and it went missing. This function's
own docstring says the loop runs twice, uncalibrated and calibrated, and
the gate in `main` still read `before`/`after` -- keys nothing here has
produced for some time. So the gate raised `KeyError` on the first corpus
every run: it could not fail, because it never got as far as comparing,
and `dungeon` was never measured at all. A gate that crashes reports the
same thing as a gate that passes -- nothing -- and it does it loudly
enough that nobody reads the rest.
⚠⚠⚠ **THREE ARMS ARE GONE WITH THE BUFFS**: `bigram`, `query` and
`occasion` all installed `boost(<R>, n)` rows, and `both` was `focus`
plus `bigram`. Every one of them named a RULE, which is what the
retirement is about -- and the measurement that motivated it is on the
record: on the dungeon, focus scored 13.0 matched/move against bigram
17.2, query 32.8 and occasion 44.4, so the node-keyed arm beat all three
and `occasion` was worse than doing nothing.

## The claim being gated: calibration must not cost

The claim being gated: calibration must not cost conclusions the
uncalibrated table already reached. It may cost MOVES -- that is the
point of it -- and it may disagree with the teacher, who is one
person on one run. Losing an answer is the failure.
⭐ What was learned about ATTENTION, as a document. Printed rather
than written to a path: a module run that leaves files behind is a
side effect nobody asked for, and `open(p,"w").write(emit(...))` is
the whole of saving it.
