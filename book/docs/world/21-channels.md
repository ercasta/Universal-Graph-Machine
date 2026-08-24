# Who said it

Something outside the machine says something. A person, a sensor, another
agent. What happens?

```
say user:  +raining(here)
say gauge: not(boiling(kettle))
```

What is written down is **that the channel said so**. Not that it's
raining.

```
+arrived(user, raining(here))
+says(user, raining(here))      concluded by the bundled <intake> rule
```

Whether you believe it is a **rule's** business:

```
rule <trust_user> = implies( { +says(user, $p), no likely($p) },
                             { +likely($p) } )
rule <gauge_yes>  = implies( { +says(gauge, $p), no $p },
                             { +$p } )
rule <gauge_no>   = implies( { +says(gauge, not($p)), no not($p) },
                             { +not($p) } )
```

```
$ python -m ugm channels.ugm --ask "likely(raining(here))"
channels.ugm: 3 ticks, ended quiescent

what it believes, newest first:
  likely(raining(here))
  says(user, raining(here))
  arrived(user, raining(here))

likely(raining(here)): believed
```

```
$ python -m ugm channels.ugm --ask "not(boiling(kettle))"
not(boiling(kettle)): believed
```

The user is trusted only as far as *likely*. The gauge is taken at its word,
including its denials — written as `not(boiling(kettle))`, an ordinary
proposition, never a third sign on the arrival. Both are one-line claims a
corpus makes and can revise.

## Trust is a rule, never a hard-wired intake

This is the design decision, and it's worth being explicit about what it
buys.

If believing a channel were built into the machinery, then *how far do I
trust this speaker* would be the one question the agent could not reason
about — and you could not have two channels trusted differently without a
configuration option.

As a rule, it is:

- **askable** — *which of my beliefs came in this way?* is a query;
- **arguable** — a rule can override it, retire it, or hedge it;
- **attributable** — `says(channel, p)` names the channel every time.

The bare-variable consequent `{ +$p }` is what makes *whatever the channel
said, believe it* one rule rather than one rule per proposition. It's also,
read backwards, completely vacuous (Chapter 11) — which is why the backward
reader declines it.

## Every rule here needs its own brake

Notice the `no likely($p)` and `no $p` guards above. They were not needed
under the old chain, where a repeated conclusion cost nothing — the read
simply found the same answer. They are load-bearing now.

Belief here is a scratchpad, not a history: asserting something already
anchored is a no-op, but the **match** that produced it happens again on the
very next tick, because nothing tells the loop that this application already
ran and changed nothing:

> **An application that changes nothing is offered again.** A trust rule
> with no guard doesn't corrupt anything — `likely(raining(here))` stays
> exactly as believed either way — but it never lets the run go quiescent.
> Left ungated, `<trust_user>` above burns through four hundred ticks doing
> nothing after the third one, and the CLI reports it never finished.

## Confidence lives on the source

Chapter 15 separated four things that look like uncertainty, and this is
where the second one lands.

*How sure am I of this rule*, *how sure am I of this sensor*, and *how far
do I trust this speaker* are **one question asked of three sources**. Every
`says(channel, p)` names the source it arrived through, so one mechanism
covers all three. Rule-confidence is simply the case where the source is the
knowledge base.

A confidence field on rules would have covered the first and needed
reinventing twice.

## Channel is not authority

Two separate things, easily conflated:

- **Channel** — how it got here. The microphone, the file, the socket.
- **Authority** — whose word it is, and what that's worth.

The boss's instruction relayed by an assistant arrives on the assistant's
channel and carries the boss's authority. Nothing stops a corpus writing
both — `says(assistant, instructed(boss, ...))` — and settling conflicting
claims by reading the second fact rather than the first.

## What a channel reports has no sign of its own

An older design gave an arrival a third field, the sign: a channel reported
`+p`, `-p`, or `?p`, which made it the one party outside the agent that
could say what to believe rather than merely what it had heard. That field
is gone with the entry that used to carry it — an arrival is a bare
proposition, and denial is written the way it's written everywhere else,
as an ordinary term:

```
say gauge: not(boiling(kettle))
```

Trying to report a denial with `-` is refused outright at the door, not
silently mangled:

```
say gauge: -boiling(kettle)
```
```
ParseError: a channel reports what it heard, not what to do about it.
To report a denial, say `not(...)`.
```

That's a cleaner shape than the old three-field arrival — a channel can no
longer smuggle *what to do about it* past the boundary, because there is no
slot left for it to smuggle it in.

## An arrival is not something the agent does

Crossing the boundary is irreducible — a channel is anchored and a rule is
generic. Crossing it **on the agent's schedule** is a claim, and a false
one.

> **An arrival is an external event, and an external event is not something
> the agent does.**

So delivery happens the moment the world speaks — `Channels.deliver` writes
straight through the gate — rather than waiting for the next tick to ask.
What arrives is on the graph immediately; *what it means* still waits for
`<intake>` to be selected, which is an ordinary rule like any other.

!!! note "Deep dive: never consume what you were told"
    Chapter 7's advice — if a rule models something *happening*, something
    in its antecedent must stop being true because it happened — has
    exactly one exception, and it's here.

    A corpus applied that rule to an arrival and oscillated forever. The
    trace is the whole argument:

    ```
    0  applied  intake  says(p1, want(p1, key1))
    1  applied  bad     wants(p1, key1), -says(p1, want(p1, key1))
    2  applied  intake  says(p1, want(p1, key1))
    3  applied  bad     -says(p1, want(p1, key1))
    4  applied  intake  says(p1, want(p1, key1))
    5  applied  bad     -says(p1, want(p1, key1))
    ```

    `arrived(...)` is never erased by anything the corpus wrote, and
    `<intake>`'s only guard is `no says(...)`. Deny `says` and that guard is
    satisfied again on the very next tick, `<intake>` restores it from the
    arrival that's still sitting there, and the cycle repeats until the
    tick limit intervenes.

    > **Consume what you concluded. Never consume what you were told.**

    What works at a boundary is not consumption but a **gate that
    legitimately closes**: guard on your own conclusion (`no
    wants(p1, key1)`), not on the channel's report, and let the world's
    own next word supersede whatever it said before.

## Reported speech

One more thing falls out with no new construct. Two claims, one authority:

```
fact +says(anna, possible(rain(afternoon)))
rule <hedge> = implies( { +says(anna, possible($x)), no possible($x) },
                        { +possible($x) } )
```

What is believed rides entirely in the **proposition** — that it's about the
afternoon, that it's hedged — and that it came from Anna rides in the
`says` fact naming her. Neither needed a new construct, and both are things
a rule can read and decline to act on.

An entry once carried a third member, a **locus**, so a claim could be
*deposited now and about the afternoon* structurally. Loci are gone
(Chapter 19), and *about the afternoon* was always part of what is
claimed — never part of where a claim sits.

---

**Next:** the machine knows nothing about numbers. Here's where they go.
[Arithmetic is not reasoning →](22-tools.md)
