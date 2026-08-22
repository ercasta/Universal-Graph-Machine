# A machine that shows its work

Let's start with the smallest interesting thing this machine can do, and then
take it apart.

Here is a complete program. It is two lines.

```
rule <mortality> = implies( { +person($p) }, { +mortal($p) } )

fact +person(paul)
```

Run it, and ask about Paul:

```
$ python3 -m ugm mortal.ugm --why "mortal(paul)"
mortal.ugm: 3 ticks, ended quiescent

why mortal(paul)?
  +mortal(paul), via kb, licensed by applied(<mortality>)
    because +person(paul), via kb, licensed by loaded(person(paul))
```

Nobody wrote down that Paul is mortal. The machine worked it out, and then
answered a second question — *how did you get there?* — without being asked to
keep a log.

## Read the answer slowly

That four-line reply has more in it than it looks.

```
+mortal(paul), via kb, licensed by applied(<mortality>)
```

- **`+`** — the sign. This is *claimed to hold*. There are three signs and they
  are not decoration; Chapter 3 is about what the other two are for.
- **`mortal(paul)`** — the proposition. On its own it claims nothing; it is
  just the *idea* that Paul is mortal. Chapter 2 is about why that separation
  is forced rather than fussy.
- **`via kb`** — where it came from. Here, the knowledge base you typed. It
  could have been a person, a sensor, or a message.
- **`licensed by applied(<mortality>)`** — what authorised it. A rule was
  applied. That rule is a node with a name, and you can ask other questions
  about it.

And the `because` line is not a paraphrase. It is the actual claim the rule
consumed, with its own sign, source and licence — `loaded(...)` this time,
because nothing derived it; you asserted it.

## Now ask about somebody it has never heard of

```
why mortal(sara)?
  nothing concluded it -- see what is BLOCKED above
```

Not *false*. **Nothing concluded it** — and the machine is careful to say that
this is a report about itself, not about Sara.

That distinction is the reason most of this book exists. Systems that collapse
*I have no reason to believe it* into *it is untrue* are systems that will
eventually tell you something false with complete confidence. Here the two are
different shapes in memory, and Chapter 3 shows you both.

## Three ticks

The run said `3 ticks, ended quiescent`. A tick is one move: the machine chose
one rule, applied it, and wrote down what followed. It stopped when applying
anything further would change nothing — which is what *quiescent* means, and
which is itself a fact it deposits about itself rather than a state hidden in an
interpreter. Chapter 26 is about stopping.

There is no compile step, no phase order, no "inference engine" with a fixed
pipeline inside it. There is one loop, and everything that happens on it —
believing what a channel told you, entering a hypothesis, expanding a goal,
deciding you're done — happens because some rule was selected and applied.

## What this book is going to do

Roughly, it will strip away layers.

Part 1 shows you the memory: what a claim looks like, what a moment is, and how
*is this true?* is answered by walking rather than by looking up.

Parts 2 to 5 show you what you can teach it: rules, goals, uncertainty, time,
other people.

Parts 6 to 8 turn the machine around to look at itself: its own commitments as
ordinary facts, the five things that genuinely could not be taught, and how
something made of rules manages to read its first rule at all.

!!! note "Deep dive: what you just ran"
    `python -m ugm <file>` loads a corpus, runs the loop to quiescence, prints
    what became of anything you asked for, and answers `--why` questions. That
    is the whole command-line surface. Everything it prints was already in the
    graph before it printed it — the reporting reads the same structures your
    rules read, which is why nothing in this book has an "explanation mode".

---

**Next:** before we can talk about claims, we need to see what everything here
is built out of — and it's shorter than you'd expect.
[Nodes, members, and nothing else →](01-the-substrate.md)
