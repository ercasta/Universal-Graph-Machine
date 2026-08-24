# When things happened

Time shows up in three places, and only one of them is engine machinery:

| | what it is | where it lives |
|---|---|---|
| **believed-since** | when the agent came to think so | not tracked — belief is presence, not history |
| **about-when** | the stretch a claim concerns | a claim the corpus makes — Chapter 19 |
| **event description** | *afternoon*, *Tuesday*, *morning* | members of a proposition |

**Believed-since** has no record anywhere: a proposition is anchored or it
isn't, right now, and asking *when did I come to think this* has nothing to
answer it from.

**About-when** was already handed to the corpus in Chapter 19 — two node
names, asserted, never derived.

**Event description** is an ordinary proposition a rule can read:
`cloudy($day, morning)` is exactly as valid as anything else.

So the rule that governs all three is one rule:

> **Calendar terms denote. Nothing orders them but what you assert.**

## There is nothing to walk

A member matches an anchored proposition, or it is computed, or it asks
about absence. There is no clock, either: no wall-clock stamp, no
`time(<moment>, ...)` relation, nothing seeded at boot that a rule can read.
Time, in this engine, is *now* — one word, no argument — and everything else
about ordering or duration is vocabulary a corpus invents and maintains by
hand.

## What "the record" means

A matcher sees the state — one anchor per proposition — so `+ill($x)` finds
whatever currently holds and nothing about what used to. Erasing a claim
deletes its anchor outright: there is no "was true, isn't now" left lying
around anywhere. If a rule needs that fact later, it has to write it down
itself, in the same breath as the erasure, or it's gone:

```
fact +ill(paul)
rule <heal> = implies( { +ill($x), no healthy($x) },
                       { -ill($x), +healthy($x), +was_ill($x) } )
rule <recovered> = implies( { +healthy($x), +was_ill($x), no recovered($x) },
                            { +recovered($x) } )
```

```
$ python -m ugm heal.ugm --ask "recovered(paul)"
heal.ugm: 3 ticks, ended quiescent
recovered(paul): believed
```

Drop `+was_ill($x)` from `<heal>`'s consequent and try the obvious rule
instead — read `+ill($x)` alongside `+healthy($x)` to notice the change —
and it never fires:

```
rule <recovered> = implies( { +healthy($x), +ill($x) }, { +recovered($x) } )
```

```
$ python -m ugm heal_bad.ugm --ask "recovered(paul)"
recovered(paul): not believed
```

`ill(paul)` was erased the instant `<heal>` ran, so nothing is ever
simultaneously `healthy` and `ill`. Which is the whole point, restated:

> **The superseded claim is not kept anywhere unless a rule keeps it.** A
> rule has to make that decision, once, in the same application that does
> the superseding — or the fact is gone.

## Ordering is entirely the corpus's to build — and check the arithmetic

Nothing derives order. A corpus that needs *this happened before that* has
to say so, and has to be honest that saying so is all it gets — the engine
will not catch a corpus that asserts an inconsistent order. The cheapest
honest version uses ordinary round numbers and a computator to compare
them:

```
kb.computator("less", lambda a, b: "yes" if int(a) < int(b) else None)
```

```
rule <first_of_two> = implies(
  { +happened($e1, $r1), +happened($e2, $r2), less($r1, $r2) as $yes },
  { +before($e1, $e2) } )

fact +happened(spark, 1)
fact +happened(flame, 3)
```

```
$ python -m ugm order.ugm --ask "before(spark, flame)"
before(spark, flame): believed
```

`less` answers `None` — *declines* — for anything that isn't strictly
smaller, so the rule simply doesn't match the other way round. Nothing here
is more principled than the number the corpus chose to write on
`happened(spark, 1)`. Ordering is arithmetic over labels the corpus
assigned, checked by a computator the corpus registered, with no engine
opinion anywhere in the loop.

## Saying *five minutes later*

Expressing *…and it boils five minutes later* takes three decisions:

**1. Say which endpoints.** *The heating takes five minutes*, *boiling
starts five minutes after heating starts*, and *boiling starts five minutes
after heating stops* are three different claims that plan differently. So a
timing fact relates **named endpoints**, never a bare scalar:

```
fact +timing(<boil>, start(heating), start(boiling))
fact +bound(<boil>, 4min, 7min)
```

**2. It's a constraint, not a number.** A closed interval, a lower bound
alone, *eventually*, and *unknown* must all be sayable — or precision-by-
silence returns one level up. **Absent timing means unknown timing**, and
that's both legal and readable.

**3. It's a fact about the rule, not a slot on a connective.** There's only
one connective, `implies`, and it has no timing member — so this question
doesn't arise. Timing is an ordinary fact naming the rule.

| | timing as a connective member | timing as a fact about the rule |
|---|---|---|
| not leaking | an absent delay defaults to something nobody stated | absent means absent |
| not lossy | one delay per rule, no provenance | several claims, each attributed |
| readable | — | *which rules are slower than five minutes* is a query |
| composable | the connective's arity varies | timing joins independently |

That third row is the real one: *the manual says five, I measured seven* is
a thing people actually say, and it's unsayable if the delay is a slot.

## Timing is read both ways

**Forwards**, it says when to expect the effect — and therefore when its
absence is a **deviation** rather than merely patience.

**Backwards**, it's a **filter**: needing boiling water within two minutes
rules a seven-minute rule out of the plan.

A rule with no timing expresses neither, and that's the honest answer
rather than a default.

And because **waiting is an action**, this is also how a precondition the
agent cannot *make* true gets planned for. *It must be a Tuesday* is
achievable at a price of up to seven days, and the price is a timing
constraint — sayable, absent when unknown, and comparable against a
deadline.

---

**Next:** point two agents' channels at each other, and something else
appears.
[Several agents →](24-several-agents.md)
