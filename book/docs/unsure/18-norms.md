# What it may never do

Everything in this book so far has been arguable. Rules lose to other rules,
claims are superseded, a rule can be put to sleep by another rule.

There is one thing that is not arranged that way, and the reason is precise.

```
rule <no-harm> = implies( { +producing(?r, doing(harm(?x))) },
                         { +drop(doing(harm(?x))) } )
fact intercepts(<no-harm>, after)

rule <angry> = implies( { +threatens(?x, me) }, { +doing(harm(?x)) } )

fact +threatens(bo, me)
```

```
1 tick, ended quiescent

refused:
  refused(doing(harm(bo)), +, <no-harm>)

emitted: nothing
```

`<angry>` applied. The conclusion was reached. The write was **refused**, and the
refusal landed on the record — naming what was refused, its sign, and which norm
refused it.

## A norm is a trigger

`intercepts(<no-harm>, after)` is what makes an ordinary rule a norm. It says:
consult this rule *after* another rule has concluded and *before* the write
lands — the one moment at which a conclusion can still be stopped.

Such a rule matches `producing(<R>, p)`: the conclusion `<R>` is about to write.
That fact exists only while the question is being asked and is never deposited,
because what a rule is *about* to conclude is not something the world holds.
What the norm concludes is read as an instruction — here, `drop`.

Which means a prohibition is a **query**. It can ask anything a rule can ask:
what else holds, who is acting, whether an emergency was declared. It is not a
list of forbidden shapes; it is a rule, and the shape lives in its antecedent
where every other pattern in this design lives.

## Consulted, never recalled

> **A prohibition is consulted on what a rule concluded, not a competitor in
> recall.**

This is the one carve-out in a design that otherwise puts everything into the
same arena, and it follows from something already established.

Chapter 27 is going to say that *what comes to mind* is a learned, incomplete,
opaque function. Recall may fail to surface a good rule; that's a recoverable
mistake, and the machine widens and tries again.

But then:

> **The opaque component may not be load-bearing for safety.**

If a prohibition had to be *recalled* like any other rule, then the machine
failing to think of it would be the machine doing the forbidden thing. Not
surfacing a helpful rule costs you a worse plan. Not surfacing a prohibition
costs you the thing the prohibition existed to prevent.

So triggers are read straight off the graph — every rule marked `intercepts`,
in table order, on every application. Never proposed, never ranked, never
arbitrated, never deferred.

That claim is measured rather than asserted. Starve recall to a single rule, so
the agent cannot reliably bring anything to mind at all:

```
recall_budget = 1

  doing(harm(bo))     nothing        the norm still bit
  doing(repair(pump)) +              and the agent could still act
```

*What you must not do* stayed complete while *what to do* stayed
incomplete-able. That is the whole of the carve-out, and it is why the norm is
not simply a rule like the others.

## Not beyond argument

Keeping norms out of recall doesn't put them beyond reach.

> **Norms are kept out of recall. That never said they were beyond argument.**

A rule can retire a norm — deny `intercepts(<no-harm>, after)` and the rule
stops being one. What a rule cannot do is *fail to notice* a norm that is still
in force. Those are different properties, and only the second one is a safety
claim.

Retiring binds what comes after it. An act already refused stays refused — that
application is spent — while the next thing the rule reaches is not. So lifting
a norm in an emergency lets the *next* act through rather than retroactively
permitting the last one.

That's the same distinction Chapter 12 insisted on when it refused to mark
antecedent members unachievable:

> **A mark lets a prohibition masquerade as a physical impossibility, and those
> must not share a slot.**

*You cannot* and *you must not* are different facts about the world, and a
system that stores them in one place has lost the ability to explain itself.

## Once exploring is safe, no comparison is needed

There's a pleasant consequence for the rest of the design.

If the forbidden things are stopped before they land, then trying things out is
safe by construction — and a lot of machinery that would otherwise be needed to
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

!!! note "Deep dive: what a norm used to be"
    A norm used to be a different kind of thing: `forbidden(doing(harm(?x)))`,
    a stored pattern consulted by the machinery at every write and indexed by
    the relation about to be written. It was fast, and it was off the recall
    path, which was the property that mattered.

    What it could not do was ask a question. A stored pattern says *never this
    shape* and nothing else, so a conditional norm — *not this, unless an
    evacuation was ordered* — had to be assembled out of rules that concluded
    and denied the prohibition itself.

    Folding it into the trigger seam removed a whole mechanism and made
    prohibitions conditional in the ordinary way. It also cost something honest:
    the old gate ran on **every** write, and a trigger runs on what a rule
    concludes. A norm now binds what the agent concludes and does, not what a
    channel reports — which is the right line, since recording that someone said
    something is not the agent doing it, but it is less reach than before.

    One limitation from Chapter 6 also went with it. Deciding whether a stored
    generic pattern covers a particular proposition is matching, and matching is
    floor — so a *rule* could not ask *would this be forbidden?*. A trigger is a
    rule asking exactly that, about a conclusion that has not landed yet.

---

That's Part 4. The machine can now hedge, suppose, put a rule to sleep, and
refuse.

**Next:** claims that aren't about instants at all.
[Stretches, not instants →](../world/19-spans.md)
