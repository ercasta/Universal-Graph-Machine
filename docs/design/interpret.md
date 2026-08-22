# `interpret.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

A rule, as a fact, applied by rules. The first step of the interpretation arc.

    python -m ugm.probes.interpret

`agreement` writes the READ as rules and holds it to `Chain.resolve`.
`quiescence` writes *this would change nothing* as rules and holds it to
`Machine._would_change`. This is the third of that family and the one they were
building towards: **apply**, as rules, held to the loop that already applies.

## The convention

A rule-as-fact is written in the open class, and nothing here is a notation the
engine knows about:

    +implies(<ant>, <con>)              the rule
    +member(<set>, <proposition>, plus|minus)   one premise, or one conclusion

Membership rather than a moment with the entries inside it, because §5 refuses a
shape whose arity varies with how much is known about it. `plus` and `minus`
resolve to the engine's own sign nodes -- the loader says so, and that is wanted
rather than tolerated: the convention and the reification agree about what a
sign is.

## The five system rules, and what each one costs

    <said>   every proposition anything ever claimed, as STRUCTURE
    <unmet>  a premise that was never said -- so the antecedent fails
    <met>    an antecedent with no unmet premise
    <fire>   a met rule's plus conclusions, deposited
    <deny>   ...and its minus conclusions

`<said>` is the whole trick. The interpreter needs *this premise was never
claimed*, and over ENTRIES a `-` member says only *something denies it*, never
*for no `$x`* -- open-world, deliberate, and correct. `<said>` is stratum 0
(every antecedent member is structural), so §6's test lands its conclusion in
the SKELETON, and a `-` on a structural member can only mean *not derived*.
That is the same line `agreement`'s `<best>` and `quiescence`'s `<quiet>` both
rely on, reached from a third direction.

So `<unmet>` and `<met>` are stratum 0 too, and the derived strata are
`said(0) -> unmet(1) -> met(2)` -- computed, not assigned, and `strata()` would
refuse the set aloud if it were not stratifiable.

`<fire>` and `<deny>` each carry ONE entry-level member (`+implies($a, $c)`),
and that is not decoration. A rule whose antecedent is entirely structural
concludes structure, and structure has no sign and cannot be taken back -- so an
interpreter written wholly in stratum 0 could not deposit a belief at all. The
entry member is what buys the right to make a claim, and it is the honest price:
the rule reads an assertion, so it may make one.

## What this does not do, stated rather than discovered

**`causes` is not interpretable here.** Applying one advances the register, and
moving the register is the one irreducible part of the design (§4 item 3):
finding where to write requires a read, and a read requires somewhere to stand.
A rule is generic and a frame is anchored, so no rule can reseat. `implies`
needs no such move, which is why it is the whole of this step.

**Premises must be ground.** Unifying a pattern against the state is what the
matcher is for, and `unifies` was retired on the grounds that the matcher IS the
coverage test. A rule-as-fact carrying variables therefore needs the matcher,
not another copy of it -- which is `adopt`, not this file.

**No defeat, no preference, no refraction.** An interpreted rule is invisible to
`overrides`, to the attention table, and to `forgone`, because the loop sees only
`<fire>`. That is the standing argument against interpreting rather than
adopting, and this file is the measurement of what it costs, not a refutation.

## The defect this found, which 518 checks could not

`_narrowed` picks an index pivot from any argument that is "a value already --
an atom or a structure written in the pattern". A structure that still carries a
VARIABLE is not a value: `said(implies($a, $c))` asked the argument index for
the bucket of the pattern node `implies($a, $c)` itself, which nothing is ever
an instance against, so the bucket was empty and the member matched **nothing**.
No error and no scan -- the rule is well formed, every other member is fine, and
it silently never applies.

A corpus that only writes atoms in argument positions cannot reach it. Every
member of this interpreter has that shape, which is why the arc found it in its
first hour. `main` runs the check with the fix reverted, so the fix is covered
rather than merely made.
