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

## Defeasible reasoning

A conclusion is **defeasible** if the machine holds it only *until better
information arrives* — a "for now," not a "forever." Most of the machine's everyday
**no**s are defeasible: *"cy is not cleared"* means *"nothing I currently know
points that way,"* and it will flip the moment you add a clearing fact.

Contrast that with a **hard** no — one the machine can actually *prove* (e.g. from
two incompatible categories: *a penguin is not a flyer*). A hard no is not
defeasible; it's as trustworthy as a yes.

Defeasibility is the honest partner of the [closed-world
assumption](#closed-world-vs-open-world): if you're going to read "I couldn't prove
it" as "false," that "false" had better be revisable when your knowledge grows.
Because every conclusion keeps a [receipt](#provenance), the machine knows exactly
which beliefs to withdraw when a supporting fact is removed — so revising is clean,
not guesswork.

> **Go deeper:** the terms to search are "defeasible reasoning" and "belief
> revision" (and, for the deletion/repair mechanics, "truth maintenance system").

---

## Retraction — taking a fact back

Withdrawing a fact is more than erasing an arrow: conclusions were *built* on
it, and they have to go too. The machine's **retraction** procedure uses the
[receipts](#provenance) to do this cleanly, in three separated steps: **decide**
(a rule cascades the withdrawal along the receipts — everything that stood on
the retracted fact is marked, but facts you *stated* are never swept up),
**record** (each doomed fact is first archived, content and receipt, into an
in-graph *historical record* — invisible to ordinary reasoning, readable to
reflection), and **retire** (only then is the live fact really deleted, by the
one privileged instruction ordinary rules can't emit).

Because the archive stays in the graph, a retracted fact can later be
**resurrected** from its record. And note what retraction is *not*: it's not a
pencil world or an undo-scope — it's honest deletion from the inked graph, made
safe by the receipts. See [Chapter 20](../deep/20-firmware.md#taking-a-fact-back).

Retraction also fires *automatically*: a conclusion that leaned on an absence
(`no evidence that X`) is re-examined at the next question after knowledge
arrives that could make X derivable — and withdrawn if its assumption broke
([Chapter 8](../intermediate/08-because.md#when-the-machine-changes-its-own-mind)).

> **Go deeper:** the tradition is "truth maintenance systems" and "belief
> revision"; the design's own name for archive-then-delete is *copy-on-delete*.

---

## Possibility — "likely" and "unlikely"

Beyond **yes / no / unknown**, the machine can hold an answer *in between*: a fact
it thinks is **likely**, or **unlikely**, or somewhere on a small scale
(*certain · very likely · likely · unlikely · very unlikely*). A hedged fact
(*cy is unlikely alibied*) is stored as a **pencil world** — like a
[supposition](../advanced/09-supposing.md) it entertains without believing — tagged with how **possible** it
is (its *band*).

Crucially, this is **qualitative**, not probability: the machine only ever
*compares* bands, never does arithmetic on them. Reasoning through a *likely* fact
yields a *likely* conclusion — a chain is as strong as its **weakest link** — and a
conclusion that leans on *"probably not P"* is only as strong as P is genuinely
unlikely (the **possibility/necessity duality**). How boldly the machine jumps on a
faint possibility is a single dial (a threshold, θ) you control, not a bias hidden
in the code.

> **Go deeper:** the tradition here is **possibility theory** (Dubois & Prade) and
> **possibilistic logic** — the *qualitative* cousin of probability. See
> [Living in an uncertain world](../advanced/10-uncertain-world.md) and, for the
> machinery, [Shades of maybe](../deep/19-uncertain-world-internals.md).

---

## Environments — worlds that can't both be true

When the machine reasons through possibilities, every "maybe" it derives quietly
remembers the **set of assumptions it stands on** — its *environment*. Join two
facts and their environments merge; draw a conclusion and it inherits the merged
set. One rule then keeps things honest: an *either… or…* records its options as
**mutually-exclusive alternatives**, and any environment that ends up needing *two
alternatives of the same choice* is **impossible** and is thrown away.

That's why the machine will never secretly stitch *tall-and-quiet* together with
*short-and-loud* to reach a conclusion — even several rules later, the contradiction
is caught the moment those environments meet. This bookkeeping-of-assumptions is what
makes reasoning-with-maybes **sound** rather than merely suggestive.

> **Go deeper:** the classic device is an **assumption-based truth maintenance
> system (ATMS)**, due to Johan de Kleer.

---

## Comparisons — more, less, and honest gaps

*Cy is more suspicious than ada* is a ranking without a measurement: one **arrow**
on a dimension (suspicion), where the direction *is* the meaning — *less* is the
same arrow read backwards. Arrows chain (cy > ada and ada > bo settles cy vs bo),
but they don't have to connect everyone: two suspects no chain joins get an honest
**unknown**, because a comparison-order is a **partial order** and its gaps are
real answers, not holes to fill.

There's a second way to rank — put things on **rungs** with the graded words
(*very suspicious*, *slightly suspicious*) — and the two meet: two suspects who
were never compared directly can still be ordered by their rungs. A story that
contradicts itself (a cycle of *more-than*s, or an arrow fighting the rungs) is
**flagged for you to investigate**, never silently "fixed".

> **Go deeper:** the underlying picture is a **strict partial order** per
> dimension, with transitivity as an ordinary rule. See
> [More or less](../advanced/11-more-or-less.md).

---

## Focus — the working set

A long conversation accretes knowledge; a machine that re-reads *everything it
has ever learned* to answer *today's* question gets slower with every topic it
closes. The **focus** is the answer: a small, visible **working set** of the
entities currently in play — the case file open on the desk, while the archive
stays in the room.

Mentioning something puts it in play (individuals, never categories — a shared
category would drag the whole archive back). Topic *switches* are explicit CNL
(`focus on X` / `forget that` / `back to X`), never guessed. Answering with
**bounded attention** reasons only within the focus and what connects to it, so
per-question cost tracks the *case*, not the *career* — and the trade is honest:
an off-focus fact is genuinely out of mind, so a focused answer can differ from
a whole-archive one, and the system using the machine chooses the mode per
question. The focus doubles as the conversation's *who-are-we-talking-about* —
the plain-data ground for resolving "he" and "it". Leaving a topic sweeps its
conversational scaffolding (stale goals, pending calls); **facts always stay**.

> **Go deeper:** [Paying attention](../advanced/14-paying-attention.md).

---

## The instruction set — the data path

Everything the machine *does* to the graph is one of a small set of instructions.
They divide into the **match** phase (looking — reads only) and the **apply** phase
(writing — the only part that changes anything). A rule compiles to a short
sequence of these. See [Chapter 17](../deep/17-instruction-set.md).

**Looking (the match phase):**

| Verb | Real name | What it does |
|------|-----------|--------------|
| find | `SEED` | Bind to every dot carrying a given mark (where a search starts). |
| follow | `FOLLOW` | Step along an arrow to a neighbour dot. |
| check | `TEST` | Keep the dot only if it carries a mark… |
| check-absent | `TEST` (absent) | …or only if it does **not** — the heart of "not." |
| join | `JOIN` | Follow an arrow *and* check the far end in one step. |
| same? | `SAME` | Keep it only if two registers hold the **same** dot. |
| different? | `DISTINCT` | Keep it only if two dots are **provably** different. |
| copy / set | `DUP` / `SET` | Move a known dot into a working slot. |
| loop | `ITERATE` | Fork the work once per item in a bounded range. |
| in focus? | `MEMBER` / `OVERLAY` | Restrict (or extend) matching to a working set / scope. |
| by degree | `FUZZY` / `GRADE` | Match on a *degree* rather than a plain yes/no. |
| by likeliness | `OVERLAY_BAND` | Step through a pencil world's fact, dimming the running score to its likeliness (weakest-link *min*) — how a *likely* is read ([Shades of maybe](../deep/19-uncertain-world-internals.md)). |
| by value | `VMATCH` | Join two dots that **agree on a value** (e.g. the same name). |

**Writing (the apply phase):**

| Verb | Real name | What it does |
|------|-----------|--------------|
| make | `MINT` | Create a fresh dot and wire arrows to it. |
| write | `EMIT` | Assert a fact (a mark, or a value) on a dot. |
| drop (control) | `DROP_CTRL` | Remove a *scaffolding* edge — **refuses** to touch a fact. |
| sweep | `SWEEP` | Remove a whole *scaffolding* dot (a resolved what-if scope, a used-up tool call) — **refuses** a fact or a receipt. |
| retire | `RETIRE` | Really delete a fact — the **privileged** deletion ordinary rules can't reach; only [retraction](#retraction-taking-a-fact-back) assembles it, after archiving the fact (see [Chapter 20](../deep/20-firmware.md#taking-a-fact-back)). |
| re-anchor | `REDIRECT` | Swing an arrow's endpoint onto the archive record — retraction's other **privileged** move, so receipts survive the delete. |

The whole list fits on a page — and there is **no** fact-deleting verb among the
ones a rule can compile to. That's what makes the because-trail safe.

---

## The instruction set — the control path

The verbs above are one straight run of look-then-write. To *loop*, to ask a
sub-question mid-thought, or to pause for the outside world, the machine needs a
**control path** — a "finger" pointing at the current instruction, and ways to move
it (see [Chapter 17](../deep/17-instruction-set.md)).

| Transfer | Real name | What it does |
|----------|-----------|--------------|
| fall through | `FALL` | Go to the next line (the default). |
| jump | `BRANCH` | Move the finger to another line. |
| jump if | `BRANCH_IF` | Jump only if a counter still qualifies (how a loop knows to stop). |
| call / return | `CALL` / `RET` | Step into a sub-task and come back — subgoals to any depth. |
| suspend / resume | `SUSPEND` / *resume* | **Pause the whole machine**, hand out a request, and later continue at the exact spot — the mechanism behind "let me find out" and stepping into a *suppose*. |
| stop | `HALT` | Done. |
| counters | `SETI` / `DEC` | Set and decrement a loop counter (control-register scratch, not facts). |

The point of making control *instructions* (rather than hiding loops and recursion
in the surrounding code) is that **how the machine thinks lives in the same visible
place as what it thinks** — nothing about the reasoning hides in a language the
graph can't see.

---

## The nine processing modes

Every computation the machine performs is one of **nine** ways of thinking — or a
knowledge-base recipe composed from them. The list is closed on purpose (see
[Chapter 18](../deep/18-modes.md)).

| # | Mode | In plain words | Where in the book |
|---|------|----------------|-------------------|
| 1 | **Saturate** | Work out the immediate consequences. | (used in small scoped bursts) |
| 2 | **Iterate** | Go through a list, one at a time. | — |
| 3 | **Chain** | "What would make this true?" — pull only the threads the question needs. | [Ch 6](../intermediate/06-only-what-you-need.md) |
| 4 | **Check** | Look for something, ready not to find it → a defeasible "no." | [Ch 5](../intermediate/05-no-and-unknown.md) |
| 5 | **Choose** | Compare options and pick the best. | — |
| 6 | **Suppose** | "What if?" — reason in pencil, then ink or erase. | [Ch 9](../advanced/09-supposing.md) |
| 7 | **Walk** | Scout a far-off connection without grinding over everything between. | — |
| 8 | **Call** | Use a tool — a calculator, a clock, a person to ask. | [Ch 11](../advanced/13-gathering-evidence.md) |
| 9 | **Record** | Remember what you did and why (always on, free). | [Ch 8](../intermediate/08-because.md) |

And the machine's headline abilities are **compositions** of these, not separate
engines:

- **Explain** = Record, replayed.
- **Suppose** = Suppose + Chain + Check.
- **Gather evidence / try-check-replan** = Call + Check.
- **"No" vs "unknown"** = Check, read under the [firmware](../deep/20-firmware.md)
  stance.

A tenth mode may be added *only* if it's nameable in plain language, keeps all its
state visible, stops gracefully when effort runs out, journals itself, and isn't
already expressible as a recipe over the nine. Backtracking trails, unification
stacks, probability loops and the like each fail at least one bar — which is why
they're deliberately kept out.

> **Go deeper:** the design calls this the "closed inventory of processing modes."
> The reasoning tradition behind Chain/Check is "logic programming" (Prolog,
> Datalog); the pencil/ink split behind Suppose relates to "assumption-based" and
> "hypothetical" reasoning.

---

*This appendix grows with the book. Spotted a concept you'd like explained here?
The project lives on [GitHub](https://github.com/ercasta/Universal-Graph-Machine).*
