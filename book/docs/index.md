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

**It never guesses about its own reasoning.** When it tells you *yes*, that's
because the claim is sitting in its beliefs, not because it produced a
plausible-sounding answer. When it can't find something, it says exactly
that — *nothing here settles it* — instead of quietly assuming *no*.

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

    A rule is a fact relating two sides — what must hold, and what follows.
    One connective, and a precise test for why a second one didn't earn its
    place. Then: write one, run it, and ask what it believes.

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

Here's the machine being asked something it has to work out. This is the real
`ugm/rules/delay.ugm` corpus, run for real, output copied verbatim. Ana's
flight was cancelled because of a crew shortage; Raj's was delayed by a storm.
The rules say what an airline owes a passenger when a flight is disrupted.
Nobody ever wrote down that Ana is owed money.

```
rule <cancel>
  +cancelled($f)
  no disrupted($f)
->
  +disrupted($f)

rule <care>
  +disrupted($f)
  +booked($p, $f)
  no owed($p, meals)
->
  +owed($p, meals)

rule <weather>
  +cause($f, storm)
  no extraordinary($f)
->
  +extraordinary($f)

rule <compensate>
  +disrupted($f)
  +booked($p, $f)
  no extraordinary($f)
  no owed($p, money)
->
  +owed($p, money)

fact +cancelled(bl204)
fact +cause(bl204, crew)
fact +booked(ana, bl204)

fact +delayed(kt881, long)
fact +cause(kt881, storm)
fact +booked(raj, kt881)
```

Run it and ask:

```
$ python -m ugm taste.ugm --ask "owed(ana, money)" --ask "owed(raj, money)" --ask "owed(raj, meals)"
taste.ugm: 10 ticks, ended quiescent

what it believes, newest first:
  owed(ana, money)
  extraordinary(kt881)
  owed(ana, meals)
  owed(raj, meals)
  disrupted(kt881)
  disrupted(bl204)
  booked(raj, kt881)
  cause(kt881, storm)
  delayed(kt881, long)
  booked(ana, bl204)
  cause(bl204, crew)
  cancelled(bl204)

owed(ana, money): believed
owed(raj, money): not believed
owed(raj, meals): believed
```

Two things are worth noticing before you read another word.

Nobody wrote `owed(ana, money)` anywhere in the corpus. It's not a fact — it's
four rules away from one, and the machine got there on its own. And it isn't
guessing: `<compensate>` demanded `no extraordinary($f)`, which is a real
question the machine asked and got a real answer to — a storm makes a flight
`extraordinary`, a crew shortage doesn't, and nothing else on Ana's flight
claims otherwise.

The second thing is Raj. Ana and Raj are both disrupted, both get meals — that
much is unconditional (`<care>` doesn't check the cause). Only Raj is refused
compensation, because his flight *is* `extraordinary`: a storm. Not a missing
fact, not a shrug — a rule fired, on purpose, and blocked him. Chapter 3 is
about why *nothing concluded it* and *something concluded the opposite* are
different situations, and why confusing them is how a reasoner starts lying.

Ready? [**Meet a machine that shows its work →**](basic/00-shows-its-work.md)
