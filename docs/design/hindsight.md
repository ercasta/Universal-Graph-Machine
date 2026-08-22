# `hindsight.py` — the argument

> ⚠⚠⚠ **The module is DELETED (2026-08-20).** It went with the locus, and every
> one of its eight checks was about the second index: `at $m`, which bound the
> locus of the entry that satisfied a member, and `holds_at(p, $m, $sign)`,
> which resolved a proposition at a named moment. An entry has no locus, so
> neither is expressible and `Chain.HOLDS_AT` does not exist.
>
> ⭐ Its subject — *reading a proposition's PAST, which a rule could not do at
> all* — is recoverable and queued: `in_delta`, `anc`, `sanc` and `entry_of` are
> ordinary structural relations, and a rule over them reads the raw chain
> instead of the resolved state. `docs/todo.md` carries the conversion.
>
> ⚠ What that conversion must reproduce, because it is the whole point of the
> file: an UNANCHORED moment finds nothing rather than walking the history, and
> a GENERIC proposition finds nothing rather than inventing a subject.

Moved out of the module so the code reads as code. Each section is the
prose that stood at the place the module now points from.

## Module overview

Reading a proposition's PAST, which a rule could not do at all.

    python -m ugm.probes.hindsight

§12's `at $m` looks like *evaluate this at m* and is not. It binds the LOCUS OF
THE ENTRY THAT SATISFIED the member -- and the resolved state keeps one entry
per proposition, the winner. So a corpus can say

    the goblin acted after the hero          two propositions, two loci

and cannot say

    p held then, and does not now            one proposition, two times

because the earlier claim is not in the state to be matched against. Probed:
`$then` bound to a real moment where `ill(paul)` held, and `+ill($x) at $then`
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
compositionally -- `$m` can only be bound by a walk the frame could make, so a
sibling branch's moment is unreachable to bind in the first place.

**Nothing is minted.** Building the answer as a node and unifying against it
would intern it, so the harness's question would afterwards be findable as its
own answer -- the interning trap's fourth face, which `ugm.quiescence` records
paying for. Only the sign slot can need binding, so it is bound by hand, and the
check below asserts the graph stayed clean.
