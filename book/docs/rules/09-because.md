# Because…

Here is a corpus about what an airline owes a passenger. It's a good example
because the domain is deliberately far from toys — entitlements, exceptions and
duties rather than blocks on a table.

```
rule <cancel>  = implies( { +cancelled(?f) },     { +disrupted(?f) } )
rule <late>    = implies( { +delayed(?f, long) }, { +disrupted(?f) } )

# the duty of care is owed whatever the cause
rule <care> = implies( { +disrupted(?f), +booked(?p, ?f) },
                       { +owed(?p, meals), +owed(?p, lodging) } )

# ...but compensation is not, if the cause was outside the carrier's control
rule <compensate> = implies(
    { +disrupted(?f), +booked(?p, ?f), -extraordinary(?f) },
    { +owed(?p, money) } )

rule <weather> = implies( { +cause(?f, storm) }, { +extraordinary(?f) } )
rule <crewing> = implies( { +cause(?f, crew) },  { -extraordinary(?f) } )

rule <far>  = implies( { +owed(?p, money), +flying(?p, ?f), +distance(?f, long) },
                       { +amount(?p, 600) } )
```

Ana's flight was cancelled because of a crew shortage. Raj's was delayed by a
storm.

```
fact +cancelled(bl204)   fact +cause(bl204, crew)    fact +booked(ana, bl204)
fact +flying(ana, bl204) fact +distance(bl204, long)

fact +delayed(kt881, long)  fact +cause(kt881, storm)  fact +booked(raj, kt881)
```

## Ask it

```
why amount(ana,600)?
  +amount(ana, 600) @M0, via kb, licensed by applied(<far>)
    because +owed(ana, money) @M0, via kb, licensed by applied(<compensate>)
    because +flying(ana, bl204) @M0, via kb, licensed by loaded(flying(ana, bl204))
    because +distance(bl204, long) @M0, via kb, licensed by loaded(distance(bl204, long))
    because +disrupted(bl204) @M0, via kb, licensed by applied(<cancel>)
    because +booked(ana, bl204) @M0, via kb, licensed by loaded(booked(ana, bl204))
    because -extraordinary(bl204) @M0, via kb, licensed by applied(<crewing>)
    because +cause(bl204, crew) @M0, via kb, licensed by loaded(cause(bl204, crew))
    because +cancelled(bl204) @M0, via kb, licensed by loaded(cancelled(bl204))
```

Eight lines, and every one of them is a claim that is still sitting in memory
with its own sign, locus, source and licence. Nothing was reconstructed.

And Raj:

```
why owed(raj,money)?
  nothing concluded it -- see what is BLOCKED above

why owed(raj,meals)?
  +owed(raj, meals) @M0, via kb, licensed by applied(<care>)
    because +disrupted(kt881) @M0, via kb, licensed by applied(<late>)
    because +booked(raj, kt881) @M0, via kb, licensed by loaded(booked(raj, kt881))
    because +delayed(kt881, long) @M0, via kb, licensed by loaded(delayed(kt881, long))
```

Meals yes, money no — and the machine can tell you why each way.

## Why the explanation is free

This is the part worth understanding, because it's the difference between an
auditable system and a system with an audit feature.

Nothing here logs. There is no explanation subsystem, no trace buffer, no
"reasoning mode". What happened is:

1. Every entry the machine deposits records what **licensed** it — which rule
   application, or which load, or which channel arrival.
2. Every application records which entries it **consumed**, in member order.

Those two records exist because the machinery needs them for other things
entirely. The strength of a conclusion drawn under a supposition depends on
them. Deciding whether one rule defeated another depends on them. Learning a new
rule from examples depends on them.

> **The trail a piece of reasoning leaves behind is not a debugging aid.**

So `why` is a walk over structure that was already there. Finding the answer and
finding the explanation were the same act.

## Read the licences

The licences are more informative than they look:

| licence | means |
|---|---|
| `loaded(p)` | you asserted it in the corpus |
| `applied(<R>)` | rule `<R>` was applied |
| `supposing(p)` | it holds because you're inside a supposition of `p` |
| `concluded(frame(...))` | it came *out* of a supposition, wrapped |

That fourth one matters: a hypothesis formed by reading a rule backwards is
distinguishable, permanently, from a conclusion drawn forwards. Reading a rule
backwards is reading its converse — *four wheels ⇒ car*, run backwards,
licenses *a cart is a car* — which is legitimate as a hypothesis and
catastrophic if a planner treats it as entailment.

The representation has to record which kind of step a given inference was, and
the licence is where it does.

## The one thing the trail can't answer

There's an honest limit, and it is structural rather than an oversight:

> **You cannot ask *why did you read it that way* through the same mechanism you
> ask *why do you believe that*.**

The walk that resolves the state (Chapter 5) is itself made of rules — but of a
special stratum that produces *structure*, not claims. If it deposited its
intermediate results as claims, it would be reading claims to do so, and the
whole thing would never start. Chapter 29 is that argument.

So the read's own working state is undated, unattributed and unexplained. Every
conclusion carries its support; the *resolution* that fed the conclusion does
not.

There's a second one, from a different direction. *Why did you consider that
rule?* has no answer either, because what comes to mind is a function rather
than a search (Chapter 26). In practice, then, the guarantee reads: *every
conclusion carries its support, among what surfaced.*

And that has a safety consequence which is stated as a principle rather than
discovered later:

> **The opaque component may not be load-bearing for safety.**

Which is exactly why prohibitions (Chapter 18) are checked at the write and
never compete for attention.

---

**Next:** rules are nodes, so let's actually ask some questions about them.
[Asking about rules →](10-rules-are-subjects.md)
