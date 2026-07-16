# Nine ways to think

We've named the machine's *instructions* — the small verbs of looking and
writing. This chapter answers the next question: **when does it use them, and
how?** It turns out the machine has exactly **nine ways of thinking**, and the
list is closed *on purpose*. Not "nine so far" — nine, full stop, with a strict
test any tenth would have to pass (and so far none does).

That deliberate smallness is a design stance. Reasoning systems have a bad habit
of sprouting clever machinery — search trees, backtracking trails, agendas with
priority knobs — most of it borrowed from textbooks rather than from how thinking
actually feels. The nine modes are chosen instead to mirror **what deliberate,
one-thing-at-a-time reasoning really does**. If a would-be new mode can't be named
by an ordinary person in plain words, can't show all its work, and can't stop
gracefully when it runs out of effort, it doesn't get in.

## The nine

Here they are, each in the plainest words we can manage — and where you already
met it in this book.

1. **Saturate** — *work out the immediate consequences.* Given what's on the
   table, what follows right now? (Used in small, scoped bursts, never on the
   whole world at once.)
2. **Iterate** — *go through a list, one at a time.* Check each cache, try each
   suspect. A list is a real thing in memory, walked with a cursor — not a
   hidden loop.
3. **Chain** — *"what would make this true?"* Start from the question and pull
   only the threads it needs. This is the demand-driven backward reasoning of
   [Chapter 6](../intermediate/06-only-what-you-need.md), and it's the machine's
   workhorse.
4. **Check** — *look for something, and be ready not to find it.* Enumerate what
   the question demands, and if it's not there, say so honestly. This is the
   **no / unknown** of [Chapter 5](../intermediate/05-no-and-unknown.md) — the 🔍
   checks in the playground, and the bounded search behind a defeasible "no."
5. **Choose** — *compare options and pick the best.* Line the candidates up, rank
   them by how well they fit, take the winner (offer a genuine tie rather than
   break it arbitrarily).
6. **Suppose** — *"what if?"* Entertain an idea in pencil, chase its consequences,
   and either commit it to ink or rub it out — the hypothesis machinery of
   [Chapter 9](../advanced/09-supposing.md).
7. **Walk** — *scout at a distance.* Send fueled "walkers" across long stretches of
   the graph to bring back a far-off connection, without grinding over everything
   in between.
8. **Call** — *use a tool.* Fingers, paper, a calculator, a clock, a person to
   ask. When a value has to be *computed* or *fetched* rather than reasoned out,
   the machine reaches for a tool — the "let me find out" of
   [Chapter 13](../advanced/13-gathering-evidence.md).
9. **Record** — *remember what you did and why.* Every firing leaves a receipt.
   This is the **because-trail** of [Chapter 8](../intermediate/08-because.md), and
   it's the one mode that's always on and costs nothing.

Eight of them spend **effort** (there's a budget — "think harder" literally means
"more budget"). The ninth, Record, is free and never optional.

## The book's tricks were compositions all along

Here's the satisfying part. Several things we presented as distinct "features"
aren't separate machinery at all — they're **recipes** that stitch these nine
together. The machine doesn't have a "suppose engine" and an "explain engine" and
an "ask engine" bolted on the side. It has nine verbs, and:

- **Explaining** is just **Record, replayed.** The receipts were kept while
  reasoning; "why" reads them back in your language. There's no separate explainer
  that could drift from the truth — the proof *is* the record.
- **Supposing** is **Suppose + Chain + Check.** Pencil the assumption, *chain* its
  consequences inside the scope, *check* each prediction. Confirmed → ink it;
  refuted → rub it out.
- **Gathering evidence** — and the whole "try a plan, check the result, adjust"
  loop — is **Call + Check.** Do the thing (or ask), then check whether the world
  came out as expected.
- **"No" versus "I don't know"** is **Check** read under an attitude. Same search;
  what a failed search *means* is the firmware setting of Chapter 18.

This is why the machine stays small and trustworthy. New abilities come from
composing old verbs in the knowledge base — recipes an author writes in plain
language — not from growing the engine. A procedure is *never* a new mode; it's a
new arrangement of the nine.

## The test a tenth mode would have to pass

The inventory stays closed because anything proposed for it must clear five bars
at once: it has to be **nameable in plain language**, keep **all its state
visible** (no hidden stacks or trails), **stop gracefully** when the budget runs
out, **journal itself** so its work explains as ordinary language, and **not
already be expressible** as a recipe over the existing nine. Backtracking search,
unification stacks, probability loops, reinforcement scoring — the usual suspects
— each fail at least one bar, and each has a plainer substitute among the nine.
The full list, with the rejected reflexes, is in the
[appendix](../appendix/index.md#the-nine-processing-modes).

---

**Next:** a machine that says *likely* sounds like it needs probabilities. It
doesn't — it reuses the modes you just met. [Shades of maybe →](17-uncertain-world-internals.md)
