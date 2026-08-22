# `necessity.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

Which reserved names is anything actually reading? (§20)

    python -m ugm.gates.necessity [name ...]

`ugm.vocabulary` says what the engine's names are **for**. This says which of
them are **doing anything** -- and the two questions are not the same, which is
the whole reason this file exists.

## The instrument

A **kill-probe** is this repository's standing discipline: break the thing on
purpose and confirm that some check notices. It tests the *test*, not the code.
`ugm.bundle` states it for rules:

> Every gate must delete each rule of the thing it checks, one at a time, and
> report any rule the fixture cannot kill. **A rule no fixture can kill is a rule
> the fixture is not testing.**

The same sentence is true of a *name*. So: for each reserved name, suppress every
entry the machinery deposits about it, run the whole suite, and see whether
anything fails. A name the suite cannot kill is one of two things, and the report
does not pretend to tell them apart:

* **dead** -- nothing reads it, and it can go; or
* **untested** -- something reads it and no check does.

Both are findings. `Moment.licence` was written and never read for the whole life
of this branch (`docs/observations.md` §1.2), and `_tolerance` outlived the
generalisation that replaced it, so the prior that every name is load-bearing is
not good.

## How suppression works, and why this shape

 Not by deleting the atom -- a name is minted in `Machine.__init__` and half the
engine holds a reference to it, so deletion is a crash rather than an experiment.
Instead every deposit **about** that relation is re-pointed at a dead one:

    quiet(<m>)   -->   suppressed(quiet(<m>))

The entry still exists, so no caller gets a `None` it did not expect, and the
chain's own bookkeeping is untouched. What changes is the only thing that should:
`quiet($m)` in a rule now matches nothing, and `relation_of(e.proposition) is
self.QUIET` in Python is now false. **The occasion stops being sayable**, which
is exactly the thing under test.

⭐ One choke point makes this honest: every write in the design goes through
`Chain.deposit` (§13's gate is the only stamper), so a single patch reaches every
route -- rules, tools, the bundle, and the machinery's own `_note`.

 A suppression that makes the suite **crash** counts as killed, not as an error
of this instrument. A crash is the suite noticing in the loudest available way,
and scoring it otherwise would flatter every name whose absence breaks Python
before it breaks a check.

## Reading the report

`killed n` is how many checks the suppression broke. The interesting column is
the one at the bottom: names where **n = 0**.

## Which names this probe can even reach, mea

 **Which names this probe can even reach, measured rather than assumed.**
Suppression rewrites the relation of a deposited PROPOSITION, so a name
that is never one -- a connective (`causes`), a sign (`plus`), an argument
atom (`ticks`), or a structural relation, which is minted beside an entry
and never deposited as one -- is untouched by the patch and would score 0
for a reason that has nothing to do with whether anything reads it.
Reporting those as *unkillable* would be this instrument's own version of
the label census that read 0.0% and looked like a finding.
