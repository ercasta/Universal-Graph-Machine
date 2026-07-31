# The Universal Graph Machine

**A machine that works things out — and can always show you how.**

Most computers are oracles. You ask, they answer, and you just have to trust
them. This machine is different. It works things out from what it knows, and
whenever you want, it can tell you *exactly* how it got there — or honestly
admit that it doesn't know, which turns out to be just as important.

This is a book for the curious. You don't need to be a programmer. If you can
follow someone planning a trip — *I'll need to book the train before I can
confirm the hotel* — you can follow this machine thinking.

---

## What makes it unusual

Three things, and they turn out to be the same thing wearing different hats.

**It never guesses about its own reasoning.** When it tells you *yes*, it can
hand you the chain of steps that got there. Not a summary written afterwards —
the actual steps, still sitting in memory.

**"I don't know" is a real answer.** Most systems collapse *false* and *not
found* into the same shrug. This one keeps them apart, because "nothing I know
proves it" and "it's untrue" are very different claims, and confusing them is
how a reasoner starts lying.

**Everything it knows is made of the same stuff.** Facts, rules, goals, plans,
memories — all of it is ordinary data in one graph. So the machine can reason
*about* a rule as easily as it reasons *with* one. That sounds like a
technicality. It's the whole game, and by the end of Part 2 you'll see why.

---

## How to read this book

Four parts, each building on the last. The fourth is an optional deep dive.

<div class="grid cards" markdown>

- :material-numeric-1-circle:{ .lg .middle } **Basic — you can use it**

    ---

    Nodes, facts, questions, and what a rule really is here. By the end you can
    hand the machine a small world and get honest answers out of it.

    [:octicons-arrow-right-24: Start here](basic/00-a-machine-that-explains-itself.md)

- :material-numeric-2-circle:{ .lg .middle } **Intermediate — how it decides**

    ---

    Wanting something, imagining before acting, finding a plan, and answering
    *why*. The part where the machine stops being a lookup table.

    [:octicons-arrow-right-24: Part 2](intermediate/05-wanting-something.md)

- :material-numeric-3-circle:{ .lg .middle } **Advanced — when things go wrong**

    ---

    Reality disagreeing with the plan, contingencies, hard limits on what it
    may ever do, memory, and learning from what it did.

    [:octicons-arrow-right-24: Part 3](advanced/10-when-reality-disagrees.md)

- :material-numeric-4-circle:{ .lg .middle } **The internals — for the curious**

    ---

    Optional. The instruction set, types as schemas, and how the machine reads
    a rule's consequences straight off the rule itself.

    [:octicons-arrow-right-24: Part 4](deep/16-instruction-set.md)

</div>

Scattered through the book are optional **deep dive** boxes. Skip them on the
first read and come back when you're curious.

!!! tip "You can read this on your phone"
    Everything here is built to read comfortably on a small screen.

---

## A taste

Here's the machine being asked something it has to work out. Paul is a person,
and one rule says people are mortal. Nobody ever wrote down that Paul is mortal.

```
ask is paul mortal?:
    paul.mortal = true
```

```
YES - derived in 1 step(s)
yes, because:
  conclude_mortal(p=paul)
```

Two things are worth noticing before you read another word.

It didn't just say *yes*. It said **which rule it used, and what it applied that
rule to**. And it didn't find that explanation by looking back over its notes —
finding the answer and finding the explanation were *the same act*. That isn't a
feature bolted on for auditability. It falls out of how the machine searches,
and Chapter 8 is where it clicks.

Now ask it about someone it knows nothing about:

```
UNKNOWN - no derivation found - this says nothing about the world
```

Not *no*. **Unknown** — and it tells you what its own silence does and doesn't
mean.

Ready? [**Meet a machine that shows its work →**](basic/00-a-machine-that-explains-itself.md)
