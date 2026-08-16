# Three signs, and silence

An entry's third member says *how* the proposition is claimed at its locus.
There are three signs, plus a fourth possibility that is not a sign at all —
having no entry.

| sign | in a real moment | in a rule's pattern |
|---|---|---|
| `+` | holds here | must hold |
| `−` | **does not hold here** | must not hold |
| `?` | held before; does not now; and I cannot say what does | — |
| *no entry* | **unchanged — inherit from before** | don't care |

The last row is the one that will cost you an afternoon if you skip it, so let's
do it first.

## Silence means *unchanged*, not *unknown*

A moment stores only what changed (Chapter 4). So when the machine looks for a
claim and finds no entry at this moment, it keeps walking backwards and finds an
older one.

Which means that in a real moment, **silence is a positive claim**: *this is as
it was*.

That is open-world reasoning done honestly, and it has a consequence that trips
up everyone arriving from a database or from Prolog:

> **`−` means denied. It never means absent.**

Here is the trap, run for real. The rule says *heal the wounded, unless
poisoned*:

```
rule <regen> = implies( { +wounded(?x), -poisoned(?x) }, { +heals(?x) } )

fact +wounded(a)
fact +poisoned(a)
fact +wounded(b)
```

`b` is wounded and nobody has ever mentioned poison in connection with `b`. Does
`b` heal?

```
why heals(b)?
  nothing concluded it -- see what is BLOCKED above
```

**No.** The `−poisoned(?x)` member is looking for an entry that says *this does
not hold*. It does not match *no entry*. There is nothing anywhere claiming that
`b` isn't poisoned, so the rule simply never applies — silently, with nothing
printed and nothing to distinguish it from a rule that had no work to do.

Write the denial and it works:

```
fact -poisoned(b)
```

```
why heals(b)?
  +heals(b) @M0, via kb, licensed by applied(<regen>)
    because +wounded(b) @M0, via kb, licensed by loaded(wounded(b))
    because -poisoned(b) @M0, via kb, licensed by loaded(poisoned(b))
```

> **Write your negatives.** A state description that lists only what *is* true
> will not drive rules that ask what is *not*.

You don't have to write them all by hand. Deriving them is an ordinary rule:

```
rule <clean> = implies( { +wounded(?x), -bitten(?x) }, { -poisoned(?x) } )
```

...which of course needs `-bitten` to come from somewhere in turn. At some point
a corpus has to say what its defaults are, and here it says so in the corpus,
where you can read it and argue with it, rather than in the engine's semantics,
where you cannot.

!!! note "Deep dive: why not just make absence mean false?"
    Because then the machine could never distinguish *nothing I know settles
    this* from *this is untrue*, and every "I don't know" would be reported as a
    denial. That's the failure mode Chapter 0 opened with.

    The cost is real and it is paid here: your rules get longer, and a missing
    denial fails silently. What you buy is that when the machine says `−`,
    something actually claimed it, and you can ask who.

## Why `?` has to exist

`?` is the odd one, and there's a specific problem it solves.

*Pouring raises the level, by an unknown amount.*

You cannot write that by writing nothing, because writing nothing means the
chain returns the **old** level. And you cannot write a new level, because you
don't know it. Without a third sign, the one thing you were trying to say is
precisely the thing that cannot be said.

`?` **invalidates without replacing**. It stops the walk and reports ignorance.

```
rule <hit> = causes( { +strike(?a, ?t) }, { ? hp(?t), +falls(hp(?t)) } )
```

Take that `?` away and `hp(goblin, 10)` still reads `10` after the hit, because
silence means unchanged. With it, the read honestly reports that it doesn't
know — and `+falls(hp(goblin))` records the direction, which downstream rules
can still reason with.

Chapter 22 shows the same move for a transfer that takes more than one step:
during the transfer both purses read `?`, so an observer **cannot form a total
at all**, rather than forming a wrong one. The tempting alternative — a
`+transferring(...)` flag observers are supposed to check — is worse, because it
is a separate read that can be skipped. The sign cannot be skipped: it's a
member of the entry, so nothing can obtain the fact without it.

## Sign and *not* are not rivals

There is also a proposition `not(p)`. Isn't that the same thing as the `−` sign?

No, and both exist, for one reason each:

| | what it is | what it's for |
|---|---|---|
| the `−` **sign** | a member of the entry | the ordinary case — matched, and never forgettable, because match cannot return an entry without it |
| `not(p)` | a **proposition** | the nested case, where only a term can sit inside another term |

The second one earns its place in Chapter 16. Conclude `−b` inside a *likely*
supposition and what you have learned is *likely, not-b*. With only a sign, what
comes back out is `−likely(b)` — *it is not likely that b* — which is a different
claim, and a stronger one.

> **The member is what the machinery computes with. The term is what survives
> nesting.**

The translation runs one way only: `+not(p)` becomes `−p`, and not the reverse.
Minting `+not(p)` for every denial would double every negative fact and would
build `not(not(p))` on meeting its own output.

> **A rule that translates both ways meets its own output.** That's a general
> hazard here, and it shows up again in Chapter 16 with a supposition rule that
> supposes its own conclusions. Self-applying rules need a corpus to stop them.

`?` stays a sign alone. It is a statement about *reading* — stop the walk,
report ignorance — and wrapping it as a term would make it look like a claim
about the world.

---

**Next:** we keep saying *at this moment* and *walk backwards*. Time to say what
a moment actually is.
[Moments →](04-moments.md)
