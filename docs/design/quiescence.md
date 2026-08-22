# `quiescence.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

§20's floor gate for quiescence: the verdict *this would change nothing*,
native against rule-level.

`agreement` does it for the read, `arbitration` for the move, `state` for what
is kept. This does it for the thing that stops the loop -- `Machine._would_change`
-- which is the next item on the list Part 5 of `docs/observations.md` leaves,
and the one the rewrite was blocked on:

> several tier-3 definitions may not be expressible today, because `_recall`,
> `_would_change` and `_choose` are all aggregates over a set of matches, and a
> rule sees one binding at a time.

**They are two different aggregates, and only one of them is the gap.** §4's
missing primitive is a claim about a set of ENTRIES -- *nothing was told about
this*, *exactly one thing answers this description* -- and there a `-` member
says only *something denies it*, never *for no `$x`*. Quiescence's universal
(*no conclusion of this application would change anything*) ranges over the
application's own consequent members, which are **structure**: they have no
entry, so a `-` on one can only mean *not derived*, which is exactly the
universal wanted. So the negative existential §4 cannot state, this one states
for free -- and it is the same line `agreement`'s `<best>` already relies on.

That is the finding this file exists to hold to a number rather than assert:
`<quiet>` below is the universal, written as one negated member.

## What is compared, and what a proposal is

An application is a rule plus bindings, and bindings are not in the graph -- so
the rule-level side is handed the grounded conclusions as facts:

    proposes(<a>, <seat>, <locus>, <prop>, <sign>)

Grounding a pattern under bindings is `substitute`, which the author's line
names as permitted -- *unify* is on the substrate side, along with the walk and
the index. What is NOT handed over is the verdict: whether the proposition
already holds there, and therefore whether applying would change anything, is
derived by the rules below from `best` -- `agreement`'s rule-level read,
imported rather than copied, because a second read is a twin.

## What is out of scope, counted rather than hidden

Four branches of `_decide_change` are not compared, and the run prints how many
candidates fell into each, so that a fixture which never reaches one cannot be
read as a fixture which agreed about it:

  * **a stratum-0 rule**, whose verdict is *is this structure already in the
    graph* rather than a read. Minting `proposes(...)` interns the conclusion,
    which is the interning trap's fourth face -- the harness's question would
    consume its own answer -- so these are excluded rather than measured wrong.
  * **a forbidden conclusion**, whose verdict is about the refusal record.
    `_forbid` unifies a stored generic pattern against the proposition, and
    `unifies($pat, $prop)` is not a structural relation, so a rule cannot ask
    it.
  * **a conclusion at a span**, because the imported read walks `anc` over
    moments (§11).
  * **a generic conclusion** -- a rule concluding ABOUT a rule's pattern. Its
    verdict turns on §14's use/mention, and that is the one part of quiescence
    which is NOT expressible, for a reason worth stating exactly.

## The fifth branch, and it is a defect in the READ rather than in this gate

**§7 tells the matcher that a node containing a variable is a pattern rather
than a fact, and the chain's own skeleton facts about mentions contain
variables.** A reified rule is deposited as a mention, its proposition is the
rule's pattern, and that pattern has variables in it -- so the entry node does
too, and so does every `mentioned`, `in_delta` and `delta_next` fact about it.
Measured on this file's own fixture: **97 of 125 `mentioned` facts and 175 of
216 `delta_next` facts are invisible to the matcher**, although every one of
them was deposited by the chain and none was authored as a pattern.

That is why the mention half of quiescence cannot be written: the facts a rule
would need to read are exactly the ones it cannot see.

**And it breaks the read itself, which no existing gate could show.**
`delta_next` is a chain: sever one link and deposit order stops being
transitive across it. A generic entry deposited between two revisions of one
proposition in a single delta severs it, both revisions come out unbeaten, and
the rule-level read has two answers where `Chain.resolve` has one.
`ugm.agreement` reports 28/28 because its fixture deposits nothing generic;
this one reaches it in a four-line corpus. Such candidates are counted as
*could not settle* rather than as quiescence disagreeing, because misattributing
a defect is worse than not finding it -- and it is why the read's five ordering
rules come out blind below.

## `<silent>` is blind, and the fixture is not what is wrong with it

`<silent>` says *this conclusion contains a variable and is not about rules, so
there is nothing to deposit*. Suppress it and nothing disagrees, which reads as
a fixture that never got round to the case. Measured, it is not:

  * **0 ground derivations at all twelve corpus@stop points.** Its raw instance
    count is 2 everywhere, which is the interning trap again -- a rule's own
    consequent member is interned among the instances of its relation -- and
    counting without filtering `has_var` is what made it look exercised.
  * **21,477 to 0 across the whole of `ugm.selftest`.** The native branch it
    mirrors is `has_var(grounded) and not _is_mention(app)`; instrumented at that
    call site, the guard was reached 21,477 times and `_is_mention` answered True
    **every** time. Its `return False` has never executed. So the dead thing is
    the branch, not the fixture for it.

Why it looks unreachable by construction rather than merely unreached:

  1. a free consequent variable is refused at AUTHORING (§13), so the variable
     has to arrive through a binding;
  2. var-carrying bindings come only from reified rule structure, and every
     entry carrying one is deposited `mention=True` -- reification, `_expert_fact`,
     and an ordinary `fact` that names a rule alike;
  3. the one mention-free route left is a STRUCTURAL premise, which consumes no
     entry and so can inherit nothing. But an all-structural rule is stratum 0,
     which `_admissible` excludes by design; and a mixed rule cannot anchor onto
     a var-carrying entry, because `_stored` refuses the unanchored pattern and
     the surface has no name for a moment -- `<root>` interns a FRESH node, which
     is the trap's sixth outing.

⚠ This is recorded rather than acted on. Exempting `<silent>` from the blindness
count would be a gate agreeing it cannot be tested, and deleting it and its
native twin is a claim about reachability that wants the author, not a session.

    python -m ugm.gates.quiescence

## The probe deletes nothing, and the first versi

**The probe deletes nothing, and the first version did.** A rule's
conclusion becomes structural by §6's fixpoint, so removing the rule also
unregisters its relation -- and `strata` skips a structural relation as *the
floor*, so `-holds_as` and `-mentioning` stopped ordering the layers that make
them mean anything. Declaring the derived relations structural to hold the
classification still is what I tried first, and it broke the same thing from
the other side: 18 disagreements, every one of them the probe measuring its
own repair. A rule is SUPPRESSED instead -- kept, still stratum 0, still in
the dependency graph, with one member no instance can ever satisfy.

## A fourth fixture, written here because three rea

A fourth fixture, written here because three real corpora between them reach
none of these shapes -- and a gate whose fixture cannot reach a rule is a gate
that reports agreement about it forever.

  <keep>   two entries about one proposition in ONE delta: only deposit order
           decides, which is what `dep-*` and `beaten-deposit` are for
  <mess>   ...and a denial at a LATER moment, which is `beaten-locus`
  <echo>   a conclusion that is generic because it is ABOUT a rule's pattern.
           Its premise is a reified fact, which is a mention, so the verdict
           turns on §14's inheritance -- <mention-inherited>
  <attach> the other source of mention: a rule that NAMES a rule, whose vars
           no antecedent binds or should -- <mention-authored>. It names
           <echo>, not <keep>: a rule with no variables of its own makes the
           conclusion GROUND, and then nothing about mention decides anything
           and the rule reads as blind.

## The probe used to re-run the whole fixture

⭐⭐⭐ **The probe used to re-run the whole fixture for every rule, and
four fifths of the gate's 16 minutes were spent doing it.** Profiled
before changing anything, because the obvious suspect was wrong: setting
up the machines, ticking them and harvesting the candidates is 0.14s of a
41s pass, and `ask_read` + `settle_structure` -- the rule-level read's own
fixpoint -- is the other 99.7%. Caching the harvest, which is what *a
smaller corpus first* sounded like it meant, would have bought 0.3%.

So the fixpoint is not made cheaper; it is run fewer times, two ways, and
neither changes a verdict:

  * **Prune.** A rule that derived nothing in the baseline pass cannot be
    noticed by suppressing it there -- suppression only removes
    conclusions, and it had none to remove, so the fixpoint is identical
    by construction. Pruning is by CONCLUSION RELATION, which is coarse
    where two rules share one (`beaten`, `dep_after`, `mentioning`): that
    errs towards running a fixture that cannot matter, never towards
    skipping one that can.
  * **Cheapest first, then stop at the first disagreement.** The question
    is *can this be noticed at all*, and the verdict below is `n == 0`.
    The order is the baseline pass's own measured cost, so it tunes itself
    to the corpora rather than to a constant somebody has to maintain.

⚠ And the count it used to print is gone deliberately, because with an
early exit it would mean *how far we got*, not *how wrong it is*. What
replaces it says more: WHERE a rule was noticed, and -- for one that was
not -- whether the fixture ran and disagreed nowhere, or never gave the
rule anything to do in the first place. `<silent>` is the second, and that
is a stronger statement than the count ever made.
