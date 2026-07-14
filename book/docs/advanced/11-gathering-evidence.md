# Gathering evidence

Until now, the machine has worked with whatever facts it was handed. But real
investigation isn't like that. Sometimes you reach a point where you need one
particular fact to move forward — and you simply don't have it. A good detective
doesn't guess. They **go and find out**.

The machine can do this too: when its reasoning stalls on a missing fact, it can
**ask**.

## When "I don't know" becomes "let me find out"

Remember the open-minded stance from Chapter 5: on an open question, absence of
evidence is `unknown`, not `no`. That `unknown` is really an *opportunity* — a
precisely identified gap the machine could fill if someone told it the answer.

So instead of stopping at `unknown`, the machine can turn to a source — a person,
a sensor, a database — and ask for exactly the fact it's missing. Watch a real
exchange. Suppose we have this rule and this suspect:

```
cy is a suspect
?someone is guilty when ?someone is suspicious
```

and we ask a question the machine can't yet answer, because it doesn't know
whether cy is suspicious:

```
is cy guilty?

   machine:  "Is it true that cy is suspicious?"   ← it asks!
   you:      yes
   machine:  → yes, cy is guilty
```

The machine reached the edge of what it knew, identified the **one** missing
premise — *is cy suspicious?* — asked for it, took the answer, and finished the
job. It didn't assume. It didn't stall. It gathered evidence.

## It asks for exactly what it needs — no more

Notice what it *didn't* ask. It didn't interrogate you about every suspect or
every fact. Because reasoning is demand-driven (Chapter 6), the machine knows
precisely which missing fact is blocking *this* conclusion, and asks only for
that. The questions it puts to you are the exact gaps on the path to your answer —
which is what makes it a good partner rather than a pestering one.

## Calculators and other tools

Asking a human is one kind of "going to find out." There are others. Some facts
aren't known by anyone — they have to be **computed**. What's 47 + 58? Is this
date before that one? What's the current price of a rare card?

For these, the machine can call out to a **tool** — a calculator, a clock, a
price lookup, an outside service — at exactly the moment it needs a value, and
fold the result back into its reasoning as an ordinary fact. The reasoning stays
pure logic; the arithmetic and lookups live in tools it calls, the way you'd reach
for a calculator mid-thought rather than doing long division in your head.

## The bigger idea: a mind that knows its own edges

Step back and see what these pieces add up to. The machine knows what it knows
(Part 1). It knows what it *doesn't* know, and says so honestly (Chapter 5). And
now: when it hits a gap, it can **reach across it** — asking a person, consulting
a sensor, calling a calculator — and carry on.

That's a genuinely capable way to think: not a sealed box that only echoes back
what it was told, but an agent that recognizes the boundary of its own knowledge
and deliberately crosses it to get the job done.

!!! note "A note on the playground"
    The in-page playground doesn't wire up a "someone to ask" or external tools —
    those need a real program around the engine to answer the machine's questions.
    The exchange above is real behavior from the full library (the engine calls a
    handler you provide whenever it needs an open fact).

---

**Next:** the grand reveal — the tiny machine that's been running under
*everything* you've seen. [The machine underneath →](12-the-machine-underneath.md)
