# `hindsight.py` — the argument

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

Reading a proposition's PAST, which a rule could not do at all.

    python -m ugm.probes.hindsight

§12's `at ?m` looks like *evaluate this at m* and is not. It binds the LOCUS OF
THE ENTRY THAT SATISFIED the member -- and the resolved state keeps one entry
per proposition, the winner. So a corpus can say

    the goblin acted after the hero          two propositions, two loci

and cannot say

    p held then, and does not now            one proposition, two times

because the earlier claim is not in the state to be matched against. Probed:
`?then` bound to a real moment where `ill(paul)` held, and `+ill(?x) at ?then`
matched nothing. That is the check below, kept as the motivation rather than
described.

`Chain.resolve(p, locus, seat)` has always answered the question. What was
missing was any way for a rule to say **which locus to resolve at**:

    holds_at(<proposition>, <moment>, <sign>)

Computed rather than stored or walked, like `entry_of` -- the third kind of
structural relation, and it needed no new member kind, so `reify`, `compose` and
`adopt` have nothing new to drop.

## Three decisions, each of which could have gone the other way

**The seat is the moment itself.** So the answer is *as believed AT that moment*
rather than *as believed now about that moment*. That is the situation reading --
what the world looked like from there -- and it is the only one available,
because a structural walker is handed no seat. The other question is a different
relation, and it should say so in its name rather than quietly meaning something
else.

**An unanchored moment finds nothing**, for `_stored`'s reason: asking about
every moment there is would walk the whole history, and containment holds
compositionally -- `?m` can only be bound by a walk the frame could make, so a
sibling branch's moment is unreachable to bind in the first place.

**Nothing is minted.** Building the answer as a node and unifying against it
would intern it, so the harness's question would afterwards be findable as its
own answer -- the interning trap's fourth face, which `ugm.quiescence` records
paying for. Only the sign slot can need binding, so it is bound by hand, and the
check below asserts the graph stayed clean.
