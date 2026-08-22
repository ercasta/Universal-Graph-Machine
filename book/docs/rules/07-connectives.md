# Two connectives, and why exactly two

```
rule <boil>    = causes(  { +heat($a, $w), +water($w) }, { +boiling($w) } )
rule <weather> = implies( { +cloudy($d, morning) },  { +likely(rain($d, afternoon)) } )
```

There are two, and the interesting question isn't *why does the engine know
about them* — it must not, and Chapter 32 explains why — but **why exactly two**.

## The membership test

> **A connective earns its place only if it licenses a different (forward,
> backward) reading pair.**

If two candidates read the same way in both directions, they're one connective,
and whatever distinguished them belongs in a member instead. Apply the test to
the obvious candidates and they fall:

- **`prevents(A, B)`** is `causes(A, {−B})`. Consequents are signed, so
  prevention is already sayable.
- **`enables(A, B)`** is `causes(A, {+possible(B)})`. Read backwards, the two
  are told apart by what the consequent *says*: a bare `B` means doing `A`
  achieves it; a wrapped one means `A` is a precondition and something else must
  still happen.

Interval relations — *before*, *during*, *overlaps* — aren't connectives either.
They're ordinary facts about moments, which are already nodes. Adding
them to a closed set would buy nothing and would start multiplicative growth:
`likely_causes`, `possibly_prevents`, and so on forever, each fusing strength
with defeasibility and recording neither.

## Why the remaining two don't collapse

The distinction is **not** *logical versus worldly*. It's mechanical, and you
can test it on any rule you write:

> **Retract the antecedent. Does the consequent go with it?**
>
> **Yes → `implies`.** The entry is *derived*. It lands in the **same** moment.
>
> **No → `causes`.** The entry is *asserted*. It persists, and lands in a
> **later** moment.

Water you have stopped heating stays boiled. That's inertia, and it's why a
zero-delay cause is still not an implication — the two cannot be merged by
setting a delay to zero.

## The rule that shows why both are needed

*A cloudy morning means rain is likely in the afternoon.*

Passes the persistence test as `implies` — learn it wasn't cloudy after all and
the rain claim goes with it. But the English reads just as easily as causal, and
clouds don't cause the afternoon's rain; a weather front causes both.

Write it as `causes`, and the backward reader (Part 3) produces **a plan to make
it rain by making it cloudy**.

The two-connective split is precisely what makes that plan unwritable.

## The thing nobody expected the connective to decide

`implies` deposits into the same moment. `causes` advances the chain to a successor.

Which means the connective silently decides whether your loop terminates.

```
rule <tick> = implies( { +quiet($m) }, { +turn($m) } )
```

```
3 ticks, ended quiescent
```

```
rule <tick> = causes( { +quiet($m) }, { +turn($m) } )
```

```
400 ticks, ended applied
  stopped at the tick limit (400); it had not finished
```

Same rule, one word different. `quiet` is an occasion the machinery deposits
when nothing else applied. `causes` advances the chain, which mints a *fresh* quiet,
which warrants the next firing, forever.

The criterion is:

> **An occasion warrants a re-ask only if re-asking cannot produce one.**

It is stated, it has been violated in three separate places in this project's
own code, and it is **not enforced**. Neither reading of the connective is about
looping, so nothing on the page warns you. If a rule keys on an occasion the
machinery deposits — `quiet`, `left`, `stopped` — reach for `implies` first.

!!! note "Deep dive: an occasion is consumed; a fact is not"
    The same hazard from the other side, and it's the single most expensive
    thing for a new corpus author to learn.

    If a rule models something *happening*, something in its antecedent must
    stop being true **because** it happened. Nothing does that for you.

    A damage rule without a retraction beats a goblin to death in one swing
    (5−2=3, 3−2=1, 1−2=0, all in one tick). A turn rule keyed on
    `+turn(hero, 1)` — a perfectly good fact, true for as long as it *is* the
    hero's turn — re-fires as fast as the mechanics resolve. What's missing
    isn't a denial; it's **a right that acting spends**:

    ```
    rule <swing> = causes( { +turn($x, $r), +may($x, $r) },
                           { -may($x, $r), +attack($x, $r) } )
    ```

    Nothing catches this. Every pass genuinely concludes something new, so
    quiescence can't help, and no check about the *outcome* can either: one such
    fight was decided correctly and then went on for ever, reaching round 417
    across 8,072 entries with every outcome check green.

    The exception: **never consume what you were told.** Denying a fact that
    arrived on a channel just restores it next tick, because the arrival is an
    unarguable record that nothing retracts. At a boundary you want a gate that
    legitimately closes — state the denial up front and let the world's own
    change supersede it.

## Neither connective needs engine support

This is what the design's central test demands, and it's worth showing rather
than asserting.

The two connectives differ in exactly one respect: **which moment the
consequent's entries are deposited in.** Same moment for `implies`, a successor
for `causes`.

The write operation is told *where* to deposit. It is not told which connective
was involved and has no way to ask. So the connective is consumed by whatever
applies rules — and the design's claim is that this should be **ordinary,
shipped data**, two rules of one shape:

```
<F-implies> = causes(
    given  +rule($r), +conn($r, implies), +matched($app, $r, $m)
    then   +deposit_into($app, $m) )

<F-causes> = causes(
    given  +rule($r), +conn($r, causes), +matched($app, $r, $m), $m' = succ($m)
    then   +deposit_into($app, $m') )
```

A third connective would be a third rule of the same shape.

> **Adding a connective adds rows, not branches.**

!!! warning "Where the shipped engine actually stands on this"
    Those two rules are **not in the bundle**. Applying a rule tests the
    connective in Python — one branch, deciding whether to advance the chain —
    so for this construct the design's own test is currently an *aspiration*
    rather than a description.

    It is worth being exact about how much that costs, because the rest of the
    claim does hold: `conn(<R>, causes)` is a real deposited fact that rules can
    read and reason about (Chapter 10), and everything *else* the loop
    consults — stopping, what to attend to, which rules are out — really is data. What is
    still a branch is the one line that turns a connective into a destination.

That test is what this whole design is built to pass, and Chapter 32 shows what
happens when you run it against the implementation and count.

---

**Next:** enough theory. Let's write a working corpus, and meet the patterns
worth building on.
[Writing a corpus →](08-writing-a-corpus.md)
