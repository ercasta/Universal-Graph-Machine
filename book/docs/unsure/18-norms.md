# What it may never do

Everything in this book so far has been arguable. Rules lose to other rules,
claims are superseded, precedence is itself a claim you can deny.

There is one thing that is not arranged that way, and the reason is precise.

```
fact <no-harm> = forbidden(doing(harm(?x)))

rule <angry> = implies( { +threatens(?x, me) }, { +doing(harm(?x)) } )

fact +threatens(bo, me)
```

```
3 ticks, ended quiescent

refused:
  refused(doing(harm(bo)), +, forbidden(doing(harm(?x))))
```

The rule applied. The conclusion was reached. The write was **refused**, and the
refusal landed on the record — naming what was refused, its sign, and which
prohibition refused it.

## Checked at the write, never in the competition

> **A prohibition is a gate on application, not a competitor in recall.**

This is the one carve-out in a design that otherwise puts everything into the
same arena, and it follows from something already established.

Chapter 27 is going to say that *what comes to mind* is a learned, incomplete,
opaque function. Recall may fail to surface a good rule; that's a recoverable
mistake, and the machine widens and tries again.

But then:

> **The opaque component may not be load-bearing for safety.**

If a prohibition were a rule competing for attention, then the machine failing
to *think of* the prohibition would be the machine doing the forbidden thing.
Not surfacing a helpful rule costs you a worse plan. Not surfacing a prohibition
costs you the thing the prohibition existed to prevent.

So prohibitions come off the recall path entirely, and are checked at the one
place effects and claims leave — the write.

Which also means the norm check is cheap and total. It doesn't have to win an
argument; it doesn't get scheduled; it can't be deferred. It just holds.

## Why it needs a name

```
fact <no-harm> = forbidden(doing(harm(?x)))
```

Note the name in angle brackets. Facts don't normally need one — reference is
binding, and anything deposited can be bound by an antecedent.

A norm is the exception, and Chapter 2's rule about variables says why:
`forbidden(doing(harm(?x)))` contains a variable, and a statement's variables
belong to it. Write it twice and you have written two nodes that say a similar
thing. A description has no identity but the one an author gives it — so without
a name, a prohibition could be stated and never retired.

## Not beyond argument

Keeping norms out of the competition doesn't put them beyond reach.

> **Norms are kept out of recall. That never said they were beyond argument.**

A rule can retire a norm. What it cannot do is *fail to notice* one. Those are
different properties, and only the second one is a safety claim.

That's the same distinction Chapter 12 insisted on when it refused to mark
antecedent members unachievable:

> **A mark lets a prohibition masquerade as a physical impossibility, and those
> must not share a slot.**

*You cannot* and *you must not* are different facts about the world, and a
system that stores them in one place has lost the ability to explain itself.

## Once exploring is safe, no comparison is needed

There's a pleasant consequence for the rest of the design.

If the forbidden things are gated at the write, then trying things out is safe
by construction — and a lot of machinery that would otherwise be needed to
*compare* options carefully before committing simply isn't. The machine can
consider a bad idea. It cannot enact a forbidden one.

## A census, and what it found

Before building any of this, the honest question was: how often does a
prohibition actually bite in a real corpus?

The answer, across this repository, was that there was **not one unplanned
conflict** to detect — which meant a detector could not be gated, because a
corpus with no pathology cannot measure a detector for it.

> **A corpus with no pathology cannot measure a detector for it.**

That's a general lesson about instruments, and it recurs. A check that reports
zero on every real input gives the same output as a check that has stopped
working. So the norm gate ships with a **planted violation carried as a
control** — the corpus above is essentially it — and the check asserts that the
refusal happens, not merely that nothing bad did.

!!! note "Deep dive: what a norm costs"
    Almost nothing, and that's measured. A norm is indexed by what it forbids,
    checked once at the write, and never proposed or arbitrated. The refusal is
    deposited as an ordinary fact, so a corpus can react to it — *I was about to
    do something forbidden* is an occasion like any other.

    The one real limitation is Chapter 6's wall showing through: deciding whether
    a stored generic pattern covers a particular proposition is matching, and
    matching is floor. So the norm gate does that in the machinery, and a *rule*
    cannot ask *would this be forbidden?* without being told. Chapter 34 records
    it.

---

That's Part 4. The machine can now hedge, suppose, prefer one rule over another,
and refuse.

**Next:** claims that aren't about instants at all.
[Stretches, not instants →](../world/19-spans.md)
