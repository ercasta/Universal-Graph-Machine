# Stretches, not instants

Some claims aren't about a moment at all.

*They are taking turns* isn't true of any instant. Its subject is a
**stretch**. So is *it rained throughout*, and so is any constraint on the
order in which things happen.

This is the one chapter in the book where the answer changed **twice**. The
design built a mechanism for stretches, ran it, and removed it. Then it
removed the very substrate the replacement depended on, and had to answer the
question a third time. All three answers are worth knowing, because the
reason each one fell is the whole lesson.

## Attempt one: a stretch as a place

An entry used to carry a **locus** — where the claim sits. Normally a moment.
The idea was to let it be a stretch instead: mint a span node with a start and
an end, and locate an entry there instead of at a single moment.

It worked, and it is long gone. Dating every claim to a place cost more than
it bought — a second index to maintain, a second question at every read (*at
this moment, or that one?*), and an ancestry test on every resolution.

## Attempt two: a stretch as a walk

What replaced the locus was an append-only **chain** of moments, each holding
the entries deposited in it, ordered by an ancestry relation a rule could
walk: `anc`, `pred`, `in_delta`, `entry_of`. A stretch stopped being a place
an entry could sit and became two moments named in an ordinary proposition,
read by walking the history between them.

That worked too, and it is *also* gone. The chain itself was removed —
`ugm/core/rules.py` says so in as many words:

> "There is also one MATCHER. The second one read the chain's skeleton —
> `pred`, `in_delta`, `anc` — as structure rather than as claims... The
> skeleton went with the chain."

Belief is no longer a history of deposits with a winner at the end. It is a
single **scratchpad**: a proposition is believed or it isn't, right now.
Asserting is minting an anchor; retracting is deleting it. There is no
record of what used to be true, because nothing here keeps one:

> "There is no history: what the agent believes now is what is in the graph
> now, and a retraction is a deletion rather than a later claim that wins."
> — `ugm/core/scratchpad.py`

So `anc`, `pred`, `in_delta`, `entry_of` are not deprecated spelling for
something else. They are not reserved words at all any more. A rule that
writes them gets an ordinary, unpopulated relation nobody derives anything
from.

## What says a stretch now: two ordinary arguments, and nothing else

With no chain to walk and no locus to bind, a stretch collapses to the
plainest thing left: **two node names, carried as arguments of an ordinary
proposition, asserted by the corpus like anything else.** Nothing mints them,
nothing orders them, nothing derives their contents. What you assert about
the stretch is what you know about it — no more.

Adapted from the passenger-rights domain in `ugm/rules/delay.ugm`: a
disruption stretches from the scheduled departure to whenever the flight
actually left, and a rule about the whole stretch reads the two endpoints
without ever being told what happened between them.

```
rule <span>
  +disrupted($f)
  +scheduled($f, $s)
  +departed($f, $a)
  no stretch($f, $s, $a)
->
  +stretch($f, $s, $a)

rule <care>
  +stretch($f, $s, $a)
  +booked($p, $f)
  no owed($p, meals)
->
  +owed($p, meals)

fact +disrupted(bl204)
fact +scheduled(bl204, 09:40)
fact +departed(bl204, 13:15)
fact +booked(ana, bl204)
```

```
$ python -m ugm span.ugm --ask "owed(ana, meals)"
span.ugm: 2 ticks, ended quiescent

what it believes, newest first:
  owed(ana, meals)
  stretch(bl204, 09:40, 13:15)
  ...

owed(ana, meals): believed
```

`stretch(bl204, 09:40, 13:15)` is not engine vocabulary. It is a relation
this corpus invented, the same way `owed` and `booked` are. `<care>` reads it
the way it reads any other proposition — no walk, no ancestry check, because
there is nothing left to walk.

That `no stretch($f, $s, $a)` guard on `<span>` is not decoration. Under the
old chain, re-asserting a fact that already held cost nothing worth guarding
against — the read simply found the same answer again. Under the scratchpad,
an application that writes nothing new is still an *application*, and it is
offered again on the next tick, and the one after that, for as long as its
antecedent still matches:

> **An application that changes nothing is offered again.** Guard your own
> recursion, or the loop never reaches quiescence — it hits the tick limit
> instead, having done nothing since the second tick.

## What stays true about representing a stretch

The representation questions attempt one settled did not go away, and the
answers are sharper now, because there is no derivation left to lean on.

**Endpoints, never contents — but now for a stronger reason.** Attempt two
could at least *derive* a stretch's contents by walking the chain between two
moments. There is no such walk now. What you know about a stretch is
*exactly* what you asserted and nothing else — not "derivable but not
listed," but genuinely absent until said.

| | endpoints only | enumerate the moments | a description of the stretch |
|---|---|---|---|
| not leaking | asserted, not derived — nothing to disagree with | invents a number of intervening events | fine |
| not lossy | fine | records the extent, not why those | fine |
| readable | fixed 2-ary | arity varies with duration | — |
| composable | compare two pairs of endpoints | comparing stretches means comparing lists | comparing descriptions isn't expressible |

**Participants stay out.** `anna` and `bo` are members of the *proposition* —
`taking_turns($a, $b, $s)` — never of the stretch itself. One stretch can
still host several unrelated claims: *they took turns* and *it rained
throughout*, over the same two named endpoints.

**Ordering stays out too, unless you assert it.** Attempt two got `anc` for
free. This design doesn't. If a corpus needs *the scheduled time comes before
the actual one*, that is a fact it writes (`before(09:40, 13:15)`) or a
computator it calls — never something the engine checks on its behalf.

## What was lost, stated plainly

Attempt two could still answer one question honestly:

> *They took turns over M7..M12* — is that so at M14?

because the chain kept every entry in deposit order and a later moment could
walk back to check. That question has no answer now, and not because
stretches specifically got weaker — because **nothing has a history**.
`believed(p)` is a fact about right now. Ask what was believed five ticks ago
and there is no record anywhere to consult; the anchor for what used to be
true was deleted the moment it stopped being true, which is what a retraction
*is* under the scratchpad.

That is a much larger trade than the one attempt two made, and it is worth
saying so rather than pretending the two removals cost the same thing:

> **The first cut traded "can I ask about the past from any point" for "later
> supersedes earlier." The second traded the past itself for a dict lookup.**

What replaces it is not a weaker query — it's a different discipline. If a
corpus needs to remember something after the world moves on, it writes the
memory down as an ordinary fact, on purpose, before whatever would have made
it unrecoverable happens. Nothing does that for you any more.

## The one thing that did not change

Both removals were driven by the same measurement, restated a second time
now that the second removal has happened too: the *feature* was never the
expensive part. Loci cost almost nothing to add and almost nothing to
remove. What cost real time, twice, was the machinery built on the
assumption the feature would always be there — a write that reified a locus
nobody asked for any more, a quiescence check keyed on a place rather than a
proposition, a resolved-state key that assumed exactly one entry per claim.

> **A feature's cost is rarely in the feature. It is in the assumptions the
> rest of the system made while the feature did not exist.**

---

**Next:** claims with no fixed length at all.
[Shapes →](20-shapes.md)
