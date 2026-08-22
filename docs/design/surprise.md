# `surprise.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

Learning from a prediction that failed.

    python -m ugm.learning.surprise

A `causes` rule deposits what it predicts -- `expects(p, +)` -- and four bundled
rules turn a contradicted prediction into `deviates(p)`. `ugm.dungeon` runs that
apparatus 392 times and finds nothing, because a game's rules are never wrong.
This is the other case: a world where the model IS wrong, which is the only kind
where the apparatus can pay.

## The whole loop, on the record

```
fact +heating(k1)     fact +contains(k1, water)
fact +heating(k2)     fact +contains(k2, sand)
rule <boils> = causes( { +heating($k) }, { +boiling($k) } )
say world: -boiling(k2)
```

```
why deviates(boiling(k2))?
  +deviates(boiling(k2)) @M2, licensed by applied(<deviation-+-contradicted>)
    because +expects(boiling(k2), +) @M1, licensed by applied(<boils>)
    because -boiling(k2) @M2, licensed by applied(<trust>)
    because +says(world, boiling(k2), -) @M0, licensed by applied(<intake>)
    because +arrived(world, boiling(k2), -) @M0, via world
```

Everything a learner needs is in that trail and nothing had to be instrumented
to get it:

    which prediction failed      `deviates(p)`
    which rule made it           the `expects` entry's licence, `applied(<R>)`
    about what                   the members of `p`
    and what did NOT fail        the same relation, holding, about something else

## What is learned, and what is not

**A discriminator, not a repair.** Abstract each fact about the failing subject
by replacing the subject with a hole, do the same for the subjects the rule got
right, and take the difference:

    k2 (failed)      heating(_), contains(_, sand)
    k1 (succeeded)   heating(_), contains(_, water)
    difference       contains(_, sand)

`heating(_)` is shared by a success and a failure, so it discriminates nothing.
That negative half is the check worth having: a learner that proposes the
premise the rule already has is proposing noise.

**It declines when it cannot know.** With one case and no contrast there is no
discriminator, and the honest output is nothing. *One mapping across premise and
conclusion is the difference between learning and noise*, and with a single
example there is no mapping to be had.

**And what it emits is a HYPOTHESIS, not a rule.** The knowledge is the author's;
what the agent may propose is a candidate, wrapped, so it cannot fight anything
authored. Promoting it is a separate act by something that can be held
responsible for it.

## What this is not

**Not the learner.** It is the smallest honest end-to-end: surprise detected,
localised to a rule, contrasted against a success, and reported as a candidate.
No anti-unification over many episodes, no calibration, no adoption. Those all
need this to work first, and this is the check that it does.
