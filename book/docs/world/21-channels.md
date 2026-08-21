# Who said it

Something outside the machine says something. A person, a sensor, another
agent. What happens?

```
say user:  +raining(here)
say gauge: -boiling(kettle)
```

What is written down is **that the channel said so**. Not that it's raining.

```
+arrived(user, raining(here), +)   via user, licensed by utterance(user, raining(here))
+says(user, raining(here), +)      licensed by applied(<intake>)
```

Whether you believe it is a **rule's** business:

```
rule <trust_user>  = implies( { +says(user, ?p, plus) },  { +likely(?p) } )
rule <gauge-yes>   = implies( { +says(gauge, ?p, plus) }, { +?p } )
rule <gauge-no>    = implies( { +says(gauge, ?p, minus) },{ -?p } )
```

```
why likely(raining(here))?
  +likely(raining(here)), licensed by applied(<trust_user>)
    because +says(user, raining(here), +), licensed by applied(<intake>)
    because +arrived(user, raining(here), +), via user, licensed by utterance(...)

why boiling(kettle)?
  -boiling(kettle), licensed by applied(<gauge-no>)
    because +says(gauge, boiling(kettle), -), licensed by applied(<intake>)
```

The user is trusted only as far as *likely*. The gauge is taken at its word,
including its denials. Both are one-line claims a corpus makes and can revise.

## Trust is a rule, never a hard-wired intake

This is the design decision, and it's worth being explicit about what it buys.

If believing a channel were built into the machinery, then *how far do I trust
this speaker* would be the one question the agent could not reason about — and
you could not have two channels trusted differently without a configuration
option.

As a rule, it is:

- **askable** — *which of my beliefs came in this way?* is a query;
- **arguable** — a rule can override it, retire it, or hedge it;
- **attributable** — the trail reaches the utterance, always.

That last one is checkable and checked: the trail from a belief goes all the way
back to `utterance(user, ...)`, not merely to "some external source".

The bare-variable consequent `{ +?p }` is what makes *whatever the channel said,
believe it* one rule rather than one rule per proposition. It's also, read
backwards, completely vacuous (Chapter 11) — which is why the backward reader
declines it.

## Confidence lives on the source

Chapter 15 separated four things that look like uncertainty, and this is where
the second one lands.

*How sure am I of this rule*, *how sure am I of this sensor*, and *how far do I
trust this speaker* are **one question asked of three sources**. Every entry
names the source it arrived through, so one mechanism covers all three.
Rule-confidence is simply the case where the source is the knowledge base.

A confidence field on rules would have covered the first and needed reinventing
twice.

## Channel is not authority

Two separate things, easily conflated:

- **Channel** — how it got here. The microphone, the file, the socket.
- **Authority** — whose word it is, and what that's worth.

The boss's instruction relayed by an assistant arrives on the assistant's
channel and carries the boss's authority. One entry, two different facts about
it, and arbitration between conflicting claims reads the second.

## What a channel reports is signed — and that's a compromise

An arrival needs a sign, and a proposition doesn't have one; only an entry does.
So *the gauge says it is not boiling* has nowhere to put the negation.

Writing `−says(gauge, p)` says the gauge **stayed silent**, which is a different
fact and not the one observed.

The shape in use is `says(channel, proposition, sign)`, with the entry always
positive: the channel did speak. That puts a sign inside a proposition, and
this design generally warns against exactly that.

It's a real compromise, and it costs you something visible. Because the sign is
an argument rather than a member, a rule can bind it with a variable and then
**ignore it**:

```
rule <careless> = implies( { +says(gauge, ?p, ?s) }, { +?p } )
```

That believes `boiling(kettle)` when the gauge said it was *not* boiling. It
loads fine. Nothing complains. Write a rule per sign.

Two better answers exist and neither is built. An arrival *should* be a
**moment** — a report is a signed delta, and trust would then be a rule relating
two moments rather than a rule per sign. Chapter 34 records it.

## An arrival is not something the agent does

Crossing the boundary is irreducible — a channel is anchored and a rule is
generic. Crossing it **on the agent's schedule** is a claim, and a false one.

> **An arrival is an external event, and an external event is not something the
> agent does.**

So delivery is the boundary calling in, at the moment the world speaks, rather
than a first line of the loop. What remains in the step is a *counter* — how
much arrived since the last one — because *nothing applied* and *nothing arrived
and nothing applied* have to be different silences (Chapter 26).

The behavioural difference is visible without running anything: a report is on
the graph the moment the world speaks, and *what it means* still waits for a
rule to be selected. Those were the same instant while intake was a phase, and
they are two different things.

!!! note "Deep dive: never consume what you were told"
    Chapter 7's advice — if a rule models something *happening*, something in its
    antecedent must stop being true because it happened — has exactly one
    exception, and it's here.

    A corpus applied that rule to an arrival and hung. Twice. The trace is the
    whole argument:

    ```
    150  + says(p1, want(p1, key1), +)
    149  - says(p1, want(p1, key1), +)
    149  + wants(p1, key1)
    ```

    `arrived` is the unarguable record of a boundary event that nothing
    retracts. So denying `says` restores it on the next tick, along with
    everything derived from it, for ever.

    > **Consume what you concluded. Never consume what you were told.**

    What works at a boundary is not consumption but a **gate that legitimately
    closes**: state the denial up front, and let the world's own change
    supersede it.

## Reported speech

One more thing falls out with no new construct. Three different times, one
authority:

```
<e1> = entry( <M9>,        says(anna, <p>),  + )     Anna spoke, at the moment of speaking
<e2> = entry( <afternoon>, possible(rain),   + )     licensed_by(<e2>, <e1>)
```

`<e2>` is deposited *now*, is about *the afternoon*, and is believed *on Anna's
word*. None of that needed anything that didn't already exist. And that the
claim is hedged is *in the proposition*, so a rule can decline to act on it.

---

**Next:** the machine knows nothing about numbers. Here's where they go.
[Arithmetic is not reasoning →](22-tools.md)
