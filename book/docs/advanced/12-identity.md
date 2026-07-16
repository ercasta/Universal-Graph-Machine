# Same name, same person?

A witness says *"the butler was acting nervous."* A separate note in the file
says *"cy has no alibi."* Are the butler and cy the **same person**? On that
question the whole case might turn — and it's trickier than it looks.

This chapter is about **identity**: how the machine decides when two mentions
refer to one and the same thing.

## The easy case: same name

Start with the simplest rule, and the machine's default. If two facts use the
**same name**, the machine treats them as the **same thing**:

```
cy is a suspect
cy is nervous
```

There's only one cy here — everything said about "cy" piles up on one individual.
You've relied on this since Chapter 0 without noticing. Same name, same node.

## The hard case: different names, one thing

But people and things collect *aliases*. "The butler," "cy," "the man in the
library" might all be one person. The machine will **not** assume that on its own
— different names could easily be different people — so *you* tell it, with a
plain statement of identity:

```
butler is nervous
cy is a suspect
butler is the same as cy
```

That last line asserts that butler and cy are one and the same. And now watch
what happens — facts flow **across** the identity:

```
is cy nervous             →  yes
is butler a suspect       →  yes
```

We never wrote *"cy is nervous"* or *"butler is a suspect"* directly. But once the
machine knows butler **is** cy, everything true of one is true of the other. The
nervousness attaches to the person, not the name.

## Why the machine is so careful about this

It would be easy — and wrong — to just mash together anything that looks similar.
Two different people can share a name; one person can go by many. Getting identity
wrong corrupts everything downstream: merge two suspects by mistake and you'll
"clear" a guilty party with someone else's alibi.

So the machine keeps identity as a **deliberate decision**, not a guess. Same-name
merging is a safe default you can rely on; cross-name identity is something you
must *assert*, because only you (or a careful translation step before the machine)
can know that "the butler" and "cy" are the same suspect.

??? info "Deep dive: it reasons by connections, not by names"
    Here's the surprising foundation. Deep down, the machine doesn't actually
    trust names at all. A name is just a convenient *handle* for finding things;
    what the machine really reasons about is the web of **connections** around a
    thing — remember the label-less dots and arrows from Chapter 1. Two mentions
    are "the same" when they're wired into the same identity, not merely when they
    spell the same. That's why it can hold two *different* people who happen to
    share a name without confusing them, and why declaring `butler is the same as
    cy` genuinely fuses their facts. Identity is about structure, not spelling.

## Try it

In the playground, add these two lines to the world —

```
butler is nervous
butler is the same as cy
```

— then ask `is cy nervous`. Watch a fact you attached to "butler" show up when you
ask about "cy." You've just told the machine that two names are one person, and
seen the knowledge flow across.

[:material-play-circle: **Open the playground**](../playground/detective.md){ .md-button }

---

**Next:** what happens when the machine needs a fact it simply doesn't have?
[Gathering evidence →](13-gathering-evidence.md)
