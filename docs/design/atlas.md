# `atlas.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

A map of a corpus: what can be inferred from what, and what never can.

    python -m ugm.probes.atlas <corpus.ugm> [--mermaid]

`ugm.vocabulary` asks whether a NAME has a web. This asks the same question of
the whole corpus and one step further out: **which relations can ever be
established, and therefore which rules can ever apply.**

⭐⭐⭐ **A name with no web is a typo; a rule with no reachable premise is a dead
rule, and it is the same defect one join further on.** `unwebbed` catches
`+bokked(?p, ?f)` because nothing writes `bokked`. It does not catch a rule whose
premise is written only by another rule that itself can never apply -- and that
is the shape a corpus acquires as it grows, because each link looks fine on its
own. The fixpoint below is what sees it.

**The reading.** A relation is *grounded* if a fact asserts it, the machinery
supplies it, or a channel delivers it. A rule is *live* if every relation in its
antecedent is grounded; a live rule grounds everything in its consequent. Iterate
to a fixpoint -- monotone, so it converges -- and whatever is left over is
unreachable **from this corpus's own text**.

⚠ **It is a static over-approximation, and saying which direction matters.** It
ignores arguments entirely: `owns(smith, sword)` grounds `owns` for every rule
that reads `owns(?a, ?b)`, whatever the arguments. So a rule this calls live may
still never fire, and a rule it calls **dead genuinely cannot** -- there is no
binding of anything that would satisfy it. The false direction is the safe one:
every report is a real defect, and the silence is not a guarantee.

⚠ Negated members are premises for this purpose -- a `-p(?x)` member needs an
entry that denies `p`, so `p` still has to be established by something.

## A bare-variable consequent concludes ANYTH

⚠⚠⚠ **A bare-variable consequent concludes ANYTHING, and
every corpus that believes what it is told has one.** The
quest's `{ +says(dm, ?p, plus) } ⟹ { +?p }` is the trust
rule -- the thing that makes an utterance a belief -- and
once it is live nothing downstream of it is unreachable.
Read literally it also writes no relation NAME, so this
walk saw a corpus whose every fact arrives by trust as a
corpus where nothing is written: it reported `nothing
writes have`, `<unlock> can never apply` and `says is
joined to nothing`, all three wrong and all three the same
cause. The bare variable, distorting a measurement for the
fifth time in this repository.

## `latent_conflicts`

Pairs of the corpus's own rules that could conclude opposite signs of one
    thing -- the offline half of harmonization.

    ⚠⚠⚠ **Filtered to a SPECIFIC unifier, and that filter is the whole
    instrument.** `ugm.harmony` measured the unfiltered version across this
    repository: **3,551 latent pairs, of which 3,545 unify only through a bare
    variable** -- `<denial>` concludes `-?p`, so it latently fights every
    positive rule ever written. Reporting those would bury the six real ones.

    ⚠ And *latent* is all it is: two rules that could disagree may have
    antecedents that never hold together, which is a join this does not compute.
    So it is a question for an author, not a defect -- which is why it prints
    separately from the things that are.

    ⚠⚠⚠ **Measured, and the rate says how far to trust it**: **1 pair** on the
    passenger-rights corpus -- `weather vs crewing`, a real question, since a
    flight delayed by a storm AND short of crew has two answers and nobody said
    which -- against **28** on the dungeon. The dungeon's are almost all the
    normal grant-and-spend cycle of a world model: it retracts in its own
    consequent in 57% of its rules, so `-may(hero, ?r)` and `+may(?y, ?r)`
    latently fight and are simply the corpus working. **A corpus that CHANGES
    the world trips this far more than one that concludes about it** -- which is
    the same gap the shape census found between the bundle and the dungeon, seen
    from the conflict side. Read it as a prompt, never as a defect list.
