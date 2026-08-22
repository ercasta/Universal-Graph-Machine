# The Universal Graph Machine

**A machine that works things out — and can always show you how.**

Most computers are oracles. You ask, they answer, and you just have to trust
them. This machine is different. It works things out from what it knows, and
whenever you want, it can tell you *exactly* how it got there — or honestly
admit that nothing it knows settles the question, which turns out to be just as
important.

This is a book for the curious. You don't need to be a programmer. If you can
follow someone reasoning out loud — *the flight was cancelled because of a crew
shortage, so the airline owes her money* — you can follow this machine thinking.

---

## What makes it unusual

Three things, and by Part 7 you'll see they are the same thing wearing
different hats.

**It never guesses about its own reasoning.** When it tells you *yes*, it can
hand you the chain of steps that got there. Not a summary written afterwards —
the actual steps, still sitting in memory, each one naming the rule that made it
and the claims that rule stood on.

**Almost none of it is the machine.** Belief, time, evidence, uncertainty,
plans, prohibitions — none of that is built into the engine. All of it is
*taught*: ordinary data, in the same graph as everything else, which you can
read, argue with, and replace. What is genuinely built in is five things, and
not one of them mentions the world.

**So it can reason about a rule as easily as it reasons with one.** That sounds
like a technicality. It's the whole game. A rule is a node, so a rule can be the
subject of a fact, the answer to a question, and — in Part 6 — the *conclusion*
of another rule.

---

## How to read this book

Eight parts, each building on the last. Parts 6, 7 and 8 are optional deep
dives; you can use the machine perfectly well having read the first five.

<div class="grid cards" markdown>

- :material-numeric-1-circle:{ .lg .middle } **What the world is made of**

    ---

    Nodes and members, propositions and claims, the three signs, and the walk
    that answers *is this true here?* By the end you know what the machine's
    memory actually looks like.

    [:octicons-arrow-right-24: Start here](basic/00-shows-its-work.md)

- :material-numeric-2-circle:{ .lg .middle } **Rules**

    ---

    A rule is a fact relating two moments. Two connectives, and a precise test
    for why there are exactly two. Then: write one, run it, and ask it why.

    [:octicons-arrow-right-24: Part 2](rules/06-a-rule-is-a-fact.md)

- :material-numeric-3-circle:{ .lg .middle } **Wanting something**

    ---

    The same rule, read the other way round: from what you want, back to what
    would bring it about. Plans, subgoals, honest dead ends, and acting.

    [:octicons-arrow-right-24: Part 3](wanting/11-backwards.md)

- :material-numeric-4-circle:{ .lg .middle } **Not being sure**

    ---

    Uncertainty is not a number here — it's a word in the sentence. Supposing,
    disagreement between rules, and the one thing checked at the write rather
    than argued about.

    [:octicons-arrow-right-24: Part 4](unsure/15-how-strongly.md)

- :material-numeric-5-circle:{ .lg .middle } **Out in the world**

    ---

    Claims about stretches rather than instants, patterns with no fixed length,
    who told you and whether you believe them, where arithmetic goes — and what
    happens when there is more than one mind.

    [:octicons-arrow-right-24: Part 5](world/19-spans.md)

- :material-numeric-6-circle:{ .lg .middle } **Watching itself**

    ---

    Optional. The machine's own expectations and commitments as ordinary facts;
    knowing when to stop; what comes to mind; the table of scores that decides
    it; and writing itself a new rule.

    [:octicons-arrow-right-24: Part 6](watching/25-own-state.md)

- :material-numeric-7-circle:{ .lg .middle } **The floor**

    ---

    Optional. The five things that genuinely cannot be taught, the test that
    decides, and how a machine made of rules ever gets started reading one.

    [:octicons-arrow-right-24: Part 7](floor/30-the-floor.md)

- :material-numeric-8-circle:{ .lg .middle } **Where the line is**

    ---

    Optional. If meaning is what follows from a word, then a word nothing
    follows from means nothing — and that is measurable. Plus an honest list of
    what isn't built.

    [:octicons-arrow-right-24: Part 8](horizon/33-the-web.md)

</div>

Scattered through the book are optional **deep dive** boxes. Skip them on the
first read and come back when you're curious.

!!! tip "You can read this on your phone"
    Everything here is built to read comfortably on a small screen.

---

## A taste

Here's the machine being asked something it has to work out. Ana's flight was
cancelled because of a crew shortage; the rules say what an airline owes a
passenger when a flight is disrupted. Nobody ever wrote down that Ana is owed
money.

```
rule <cancel>     = implies( { +cancelled($f) }, { +disrupted($f) } )
rule <crewing>    = implies( { +cause($f, crew) }, { -extraordinary($f) } )
rule <compensate> = implies(
    { +disrupted($f), +booked($p, $f), -extraordinary($f) },
    { +owed($p, money) } )

fact +cancelled(bl204)
fact +cause(bl204, crew)
fact +booked(ana, bl204)
```

Ask it why:

```
why owed(ana,money)?
  +owed(ana, money), via kb, licensed by applied(<compensate>)
    because +disrupted(bl204), via kb, licensed by applied(<cancel>)
    because +booked(ana, bl204), via kb, licensed by loaded(booked(ana, bl204))
    because -extraordinary(bl204), via kb, licensed by applied(<crewing>)
    because +cause(bl204, crew), via kb, licensed by loaded(cause(bl204, crew))
    because +cancelled(bl204), via kb, licensed by loaded(cancelled(bl204))
```

Three things are worth noticing before you read another word.

It didn't just say *yes*. It named **which rules it used, what it applied them
to, and where each supporting claim came from** — `applied(<cancel>)` for a
derived one, `loaded(...)` for one you typed in. And it didn't find that
explanation by looking back over its notes: making the conclusion and making the
explanation were *the same act*. Chapter 9 is where that clicks.

The third thing is the `-extraordinary(bl204)` line. That's a **denial**, and
the rule demanded one. Not "we couldn't find that the cause was extraordinary" —
an actual claim, derived by an actual rule, that it wasn't. Ask about Raj, whose
flight was delayed by a storm:

```
why owed(raj,money)?
  nothing concluded it -- see what is BLOCKED above
```

Not *no*. Nothing concluded it — and the machine will tell you what it was
missing. Chapter 3 is about why those are different answers, and Chapter 13 is
about why confusing them is how a reasoner starts lying.

Ready? [**Meet a machine that shows its work →**](basic/00-shows-its-work.md)
