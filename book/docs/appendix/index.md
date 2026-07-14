# Appendix — concepts, in plain language

The book tries to teach every idea when you first need it. This appendix is for
when you want a little *more* on a concept, or you jumped straight here. Each
entry is short, plain, and ends with a pointer or two if you want to go deeper.

These will grow as the book does. Here are the first few.

---

## What is a graph?

A **graph** is just a collection of **dots** connected by **lines** (or arrows).
The dots are called **nodes**; the connections are called **edges**.

You already know dozens of graphs:

- A **subway map** — stations are nodes, tracks are edges.
- A **friend network** — people are nodes, "is friends with" is an edge.
- A **family tree** — people are nodes, "is a parent of" is an edge.

When the edges have a *direction* (an arrow, like "is a parent of" — which only
goes one way), it's called a **directed graph**. The Universal Graph Machine
lives in a directed graph: every fact is an arrow pointing from one thing to
another.

That's the whole idea. Everything else is just *lots* of dots and arrows.

> **Go deeper:** search for "graph theory for beginners." The very first
> concepts — nodes, edges, directed vs. undirected — are all you need to read
> this book.

---

## Closed world vs. open world

This is one of the most important ideas in the whole book, and it's really a
question about *attitude*.

Imagine you look someone up in the school directory and they're not listed.
Two reasonable reactions:

- **"Then they don't go to this school."** You're trusting the directory to be
  *complete*. This is the **closed-world assumption**: if it's not written down,
  it's false.
- **"Then I don't know whether they go here — the directory might be missing
  someone."** You're *not* assuming the list is complete. This is the
  **open-world assumption**: if it's not written down, it's simply *unknown*.

Neither attitude is "correct" — it depends on the situation. A closed world is
right for a complete database (a chessboard, a train timetable). An open world
is right when your knowledge is partial (a detective who hasn't gathered every
clue yet).

The Universal Graph Machine lets you *choose* the attitude, and it takes the
consequences seriously: under a closed world an unprovable fact is **no**; under
an open world the very same fact is **unknown**. You saw this in
[Chapter 0](../basic/00-a-machine-that-explains-itself.md#one-more-thing-it-knows-what-it-doesnt-know)
with the stranger, zz.

> **Go deeper:** the terms to search are "closed-world assumption" and
> "open-world assumption." They come up constantly in databases and in
> artificial intelligence.

---

## Demand-driven vs. fixpoint (why the machine is lazy)

There are two ways a reasoning machine can work.

- **Fixpoint (eager):** start from everything you know and grind out *every*
  conclusion you possibly can, over and over, until nothing new appears. Now the
  answer to any question is already sitting there, pre-computed. Thorough — but
  it might work out a million facts you never asked about.
- **Demand-driven (lazy):** start from the *question* and chase only the facts
  needed to answer *it*. Nothing else gets computed.

In Chapter 0, when we asked *who is the thief?*, the machine never worked out
whether anyone owned a bicycle — it didn't need to. That's demand-driven
reasoning, and it's the machine's normal mode. (It *can* do the eager,
work-everything-out version too, when you actually want a complete snapshot.)

The lazy approach is usually far less work, and it has a surprising bonus we'll
meet later: because the machine only looks as far as the question demands, it
can honestly tell you when it *ran out of things to check* — the difference
between "I've proven no" and "I didn't find anything."

> **Go deeper:** in computer science this lazy style is related to "backward
> chaining"; the eager style is "forward chaining." Both are worth a look once
> the intuition here feels solid.

---

## Negation-as-failure

How does a machine decide something is *false*? One powerful answer:
**negation-as-failure**. To decide *"cy is **not** cleared,"* the machine tries
its hardest to prove the **positive** — *"cy is cleared"* — and if that search
**fails**, it concludes the negative.

It's exactly how you'd reason: *"Is there any reason to think cy is cleared? …No?
Then cy isn't cleared."* In the playground's step view, it's the 🔍 check —
*"is cy cleared? → found no evidence."*

This is efficient and intuitive, but it leans on an assumption: that if the fact
were true, you'd have found it. That's the [closed-world
assumption](#closed-world-vs-open-world) again — which is why negation-as-failure
and the open/closed-world question are two sides of one coin.

> **Go deeper:** the phrases to search are "negation as failure" and "closed-world
> assumption." They're foundational ideas in logic programming (the tradition
> behind languages like Prolog and Datalog).

---

## Provenance

**Provenance** means *a record of where something came from.* When the machine
derives a new fact, it also stores a little receipt: which rule fired, and which
facts that rule stood on. Do that for every conclusion and you get a complete
trail from any belief back to the raw facts it rests on.

That trail is what the machine reads back when you ask **`why`** — so an
explanation isn't a story generated *about* the reasoning, it's the recorded
reasoning itself, replayed. It's what lets you *trust* and *correct* the machine
instead of taking its word on faith.

> **Go deeper:** the ideas here live under "provenance" and "truth maintenance
> systems" in computer science, and "proof" in logic — in this machine, the three
> turn out to be the same thing.

---

## Controlled natural language (CNL)

A **controlled natural language** is a deliberately restricted slice of an
ordinary language (here, English), narrowed down so that every accepted sentence
has exactly **one** meaning. `ada is a suspect` can't be read two ways.

Ordinary English is full of ambiguity, which is fine for people but poison for a
machine that has to reason precisely. A CNL keeps the friendly, readable feel of
English while removing the guesswork — and, importantly, it tells you when you've
written something outside its rules rather than misinterpreting you (a property
called *habitability*).

> **Go deeper:** look up "controlled natural language" and, for the specific
> tradition UGM draws on, "Attempto Controlled English (ACE)."

---

*This appendix grows with the book. Spotted a concept you'd like explained here?
The project lives on [GitHub](https://github.com/ercasta/Universal-Graph-Machine).*
