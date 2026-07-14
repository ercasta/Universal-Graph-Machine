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

*More entries — lattices, negation-as-failure, provenance, controlled natural
language — will land here as the matching chapters are written.*
