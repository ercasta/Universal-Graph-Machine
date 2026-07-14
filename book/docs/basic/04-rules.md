# Rules: the word "when"

So far the machine only knows what we hand it. Tell it `ada is nervous` and it
knows ada is nervous — no more, no less. That's a filing cabinet, not a mind.

This chapter adds the one thing that turns facts into *reasoning*: **rules**. A
rule lets the machine **work things out for itself**. And it all hinges on one
small word — **`when`**.

## Your first rule

Here's a rule:

```
?someone is watched when ?someone is nervous
```

Read it out loud and it's just common sense: *"someone is watched **when** they
are nervous."* Now, in a world where `ada is nervous`, watch what happens:

```
is ada watched            →  yes
is bo watched             →  no
```

We never wrote `ada is watched` anywhere. The machine **derived** it — it applied
the rule to a fact it already had and reached a brand-new conclusion. That's the
whole idea of a rule.

### The anatomy of a rule

Every rule has two halves joined by `when`:

```
   ?someone is watched   when   ?someone is nervous
   └─────────┬────────┘         └────────┬────────┘
        the CONCLUSION               the CONDITION
     (what becomes true …)        (… whenever this is true)
```

- The **condition** (after `when`) is what the machine looks for.
- The **conclusion** (before `when`) is what it gets to add if the condition holds.

And `?someone`? That's our **stand-in for anybody**, from Chapter 0. The `?`
marks it as a variable — a blank the machine fills with whoever fits. This one
rule works for ada, bo, cy, or a thousand suspects, because `?someone` matches
them all.

## Rules can feed other rules

Here's where it gets powerful. A rule's conclusion is a fact like any other — so
**it can trigger the next rule.** Watch a chain form:

```
?someone is innocent when ?someone in library
?someone is cleared when ?someone is innocent
```

Now ask about bo, who was in the library:

```
is bo cleared             →  yes
```

Think about everything that just happened. Bo being *cleared* was never stated,
and no single rule concludes it directly from a fact we gave. The machine had to
**chain**:

1. `bo in library` — a fact we gave it.
2. …so by the first rule, `bo is innocent`.
3. …so by the second rule, `bo is cleared`.

Don't take my word for it — make it show its work:

```
why bo is cleared
```

```
bo is cleared  <- rule.?someone.is.cleared
  bo is innocent  <- rule.?someone.is.innocent
    bo in library  (given)
```

Read it bottom-up and it's the exact chain: *in the library → innocent →
cleared*, each `<-` a rule firing, resting finally on the one fact we `given`.
**This** is what "reasoning" means here — not one lookup, but a trail of
conclusions, each standing on the last.

## Rules with "and" — more than one condition

A `when` can demand several things at once, joined with **`and`**:

```
?someone is cleared when ?someone is alibied
```

Add that alongside the first cleared-rule and now there are *two* ways to be
cleared — an alibi **or** being innocent. Ask `who is cleared` and both ada (the
alibi) and bo (the library) come back. Conditions joined by `and` must **all**
hold; separate rules for the same conclusion give **alternative** ways to reach
it.

## Rules with "not" — a first taste

Finally, the rule we opened the whole book with:

```
?someone is thief when ?someone is a suspect and ?someone is not cleared
```

Two conditions: be a suspect, **and** *not* be cleared. That little `not` is
doing something deep. How does the machine decide someone is **not** cleared?

It does exactly what you'd do: it **goes looking for a reason they're cleared,
and if it can't find one, it concludes they're not.** In the playground's step
view, that's the 🔍 check you can watch happen:

> *"is cy cleared?" → found no evidence → so cy is **not** cleared → cy is the
> thief.*

For cy — no alibi, not in the library — the search comes up empty, so `not
cleared` holds, and the thief rule fires.

!!! warning "Here be dragons (the good kind)"
    "Look for a reason, and if you can't find one, assume the opposite" is a
    surprisingly bold move. What if the machine's information is just
    *incomplete*? What if there's an alibi it hasn't been told about? That exact
    question — when it's safe to treat *"I couldn't find it"* as *"it's false"*
    — is the doorway into **Part 2**, and one of the most important ideas in the
    book. For now, enjoy that the thief rule works; soon we'll ask when it
    *should*.

## It only bothers when you ask

One last thing, tying back to Chapter 0's "lazy on purpose." The machine does
**not** grind through every rule the moment you load them. All this
chaining — innocent, cleared, thief — happens **on demand**, only for the
question you actually ask. Ask `is bo cleared` and it works out bo's story and
stops; it never bothers deciding whether ada is watched unless you ask. Rules
are *potential* conclusions; a question is what makes the machine cash them in.

## Putting it all together

You now know every piece of the case from Chapter 0. Here it is, whole — facts,
then rules — and there's nothing in it you can't read:

```
ada is a suspect
bo is a suspect
cy is a suspect

bo in library
ada is alibied

?someone is innocent when ?someone in library
?someone is cleared when ?someone is innocent
?someone is cleared when ?someone is alibied
?someone is thief when ?someone is a suspect and ?someone is not cleared
```

Six facts, four rules, and a machine that can name the thief **and** explain how
it knows. That's the entirety of Part 1.

## Try it

Open the playground, ask `who is thief`, and this time **watch the step view**:
the questions it asks itself, the checks that come up empty, the conclusion. Then
change a rule — make being nervous enough to be a suspect, or add a third way to
be cleared — and see how the machine's reasoning shifts.

[:material-play-circle: **Open the playground**](../playground/detective.md){ .md-button .md-button--primary }

---

## End of Part 1

You can now describe a world, ask it questions, and teach it rules that reason —
with answers it can always justify. That's a genuinely capable little mind.

**Part 2 — Intermediate** opens up *how* it thinks: why it's lazy, the deep
difference between *"no"* and *"I don't know,"* the controlled language you've
been speaking all along, and how the "because" trail really works.

[Begin Part 2 → "No" and "I don't know"](../intermediate/05-no-and-unknown.md)
