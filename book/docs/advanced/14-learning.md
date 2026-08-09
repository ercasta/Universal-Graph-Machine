# Learning from what it did

The machine did a few things to a jar. Here's the whole chapter in one move: it
turns that into a rule it can use again.

## Watch it happen

We sealed the salt, then labelled it. The machine kept the sequence:

```
episode steps: ['seal', 'label_jar']
```

Now turn that into a rule:

```
# Learned from what I did to the salt: seal then label_jar
fn prepare_jar(jar):
    INVOKE R(_) "seal" j=F(jar)
    INVOKE R(_) "label_jar" j=F(jar)
```

That's a real rule, minted by the machine. Point it at a different jar:

```
pepper sealed? True | labelled? True
```

## What's *not* here

No learning system. No training. No separate representation for "learned" rules
as opposed to authored ones.

Look at the rule again — it's the same shape as `seal` from Chapter 4, stored
the same way, in the same graph. It shows up in the catalogue alongside
everything else, it can be pointed at, planned with, read, explained, and
compiled into by another episode. There's no way to tell by looking that a
machine wrote it rather than a person.

That's Chapter 4's "a rule is data" paying its largest dividend. Writing a rule
is just writing nodes and edges — which is something every rule can already do.
So learning needed no new mechanism at all; it needed someone to write the rule
that does it.

## The generalisation is the interesting bit

The machine did those things to the *salt*. The rule it wrote works on **any**
jar. Turning the specific into the general is the actual content of learning
here, and it's done by asking a simple question: which parts of what I did were
*this particular thing*, and which were incidental?

The salt was the subject throughout, so the salt becomes the parameter.

!!! note "Deep dive: this is why the substrate is ordered"
    A sequence of actions has to be replayed *in order*. An earlier version of
    this experiment found that applications had no inherent order, and needed a
    counter stamped on each one by whatever was driving. Once arrows became
    ordered (Chapter 1), the episode simply *is* an ordered list, and the
    counter disappeared. A small substrate decision removing a whole piece of
    bookkeeping is usually a sign the decision was right.

## The honest limit

This handles a sequence of single-argument actions on one subject. Extend it to
actions with several arguments and you hit a genuine question, not a missing
feature:

> If I did something to *the salt* and *the top shelf*, and now I'm replaying it
> with a different jar — what plays the part of the shelf?

Sometimes the shelf should stay fixed. Sometimes it should vary along with the
jar. Sometimes it depends. That's a question about **analogy**, and it doesn't
have a mechanical answer. The machine doesn't guess, which is why the limit is
where it is.

## Where this is going

Two things become possible once episodes accumulate, neither of which is built
yet, and both of which are worth naming so the shape is clear:

**Choosing better.** Right now, when several rules could apply, the machine
takes them in a declared order. What it *wants* is to prefer the sequences that
have worked. That needs a corpus of episodes — which is exactly what this
chapter produces. So it comes after, not with.

**Noticing its own patterns.** A rule assembled from an episode is a hypothesis
about a useful sequence. Whether it's actually useful is something the machine
could measure, on the same evidence.

---

**Next:** the machine can act, remember, and learn. Now what happens when two of
its own intentions get in each other's way.
[When two intentions collide →](15-collisions.md)
