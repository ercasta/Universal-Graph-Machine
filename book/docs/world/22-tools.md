# Arithmetic is not reasoning

Nothing in this machine knows about numbers.

A numeral is an ordinary atom whose *name* happens to read as a number. `20` is
a node, exactly like `kettle` is a node. Nothing in the graph knows that `20` is
bigger than `17`, and no rule can work it out.

That's deliberate, and it's the right shape: arithmetic is a **function**, and a
function is not a search.

## A computator runs during the match

```python
kb.computator("minus", lambda a, b: int(a) - int(b))
kb.computator("plus",  lambda a, b: int(a) + int(b))
```

```
rule <pay> = causes(
    { +pays(?a, ?b, ?n), +purse(?a, ?x), +purse(?b, ?y),
      minus(?x, ?n) as ?x2, plus(?y, ?n) as ?y2 },
    { ? purse(?a, ?x), +purse(?a, ?x2), ? purse(?b, ?y), +purse(?b, ?y2),
      -pays(?a, ?b, ?n) } )

fact +purse(anna, 10)
fact +purse(bo, 5)
fact +pays(anna, bo, 3)
```

```
purse(anna, 7)  -> +
purse(bo, 8)    -> +
purse(anna, 10) -> ?
```

A **computator** is a function given values and returning a value. It never sees
the graph. So it runs *during the match*, which means the whole transfer lands
in one application: a standing observer sees `total(10, 5)` and then
`total(7, 8)`, and **never the 12 in between**.

Three details in that rule are load-bearing:

- **`as ?x2`** names what the computator returned, so the consequent can use it.
- **`? purse(?a, ?x)`** invalidates the old amount. Without it, silence means
  unchanged and the purse still reads 10.
- **`-pays(?a, ?b, ?n)`** consumes the trigger. Without it the rule debits
  **forever** — the first version of this fixture took the purse down in threes
  until the budget stopped it. Chapter 7's turn loop, arriving in a corpus
  instead of the machinery.

## A tool answers through the write

A **tool** is a request answered by a function rather than by a search. Unlike a
computator, it can talk to the world — a clock, a file, a network — and its
answer therefore lands a **tick later**.

```python
kb.answerer("calc", "minus", fn)
```

```
rule <spend>    = implies( { +purse(?b, ?n), +buying(?b, ?i), +cost(?i, ?c) },
                           { +minus(?b, ?n, ?c) } )
rule <apply-it> = implies( { +answered(<calc>, minus(?b, ?n, ?c), ?r) },
                           { +?r, ? purse(?b, ?n), -buying(?b, sword) } )
```

Use a **computator** wherever the arithmetic is pure. Keep a **tool** for
anything that talks to the world.

And the rule for both:

> **A tool proposes; it never concludes.**

The answer arrives as a fact, and an ordinary rule decides what to make of it.
A tool that concluded directly would be a piece of the world's authority hidden
inside the machinery, unattributable and unarguable.

This is also why the tool's own binding is deposited — `answers(<calc>, minus)`
— rather than kept in a registry. The machinery knew which function answered
which request, and no rule could ask.

## When a change takes more than one tick

If your transfer waits on a die roll, a person, or anything outside, then
part-way through you genuinely **do not know** what the purses hold.

So say `?`, and assert the numbers only on settlement:

```
rule <start>    = causes( { +pays(?a, ?b, ?n), +purse(?a, ?x), +purse(?b, ?y) },
                          { ? purse(?a, ?x), ? purse(?b, ?y), +pending(...) } )
rule <complete> = causes( { +pending(...), +confirmed(?a, ?b),
                            minus(?x, ?n) as ?x2, plus(?y, ?n) as ?y2 },
                          { +purse(?a, ?x2), +purse(?b, ?y2), -pending(...) } )
```

Measured: mid-transfer the purses read `?`, an observer **cannot form a total at
all**, and on confirmation it's `total(7, 8)`, conserved.

No marker fact anyone has to remember to consult. A reader cannot get the value
without the sign, because the sign is a member of the entry.

The tempting alternative — a `+transferring(...)` flag observers are supposed to
check — is worse, and for exactly the reason Chapter 15 rejected grades: **it is
a separate read, so it can be obtained without the facts it qualifies.** An
observer that doesn't think to ask sees a settled state.

> Prefer `?`.

## Where a model would go

A last note, because it's the question everyone asks.

If you wanted to put a learned model in this machine — a classifier, a language
model, a scorer — where would it go?

**Where there is no algorithm.** Not in the read, not in the match, not in the
arbitration: those have definitions, and a model there can only approximate
something already correct. Measured directly, an ideal lookup table replacing
the read bought **zero**, and a wrong one costs more as knowledge grows.

The place a model belongs is where the current answer is a guess: what comes to
mind (Chapter 27), and how good an option looks. And the shape it should return
is a **pair** — a score (*how good*) and a strength (*how sure*) — because those
are two different things and this design has already learned not to collapse
them into one number.

A model reached through a tool is data like anything else: it proposes, a rule
decides, and the decision carries a trail.

---

**Next:** clocks, calendars, and the one ordering that governs.
[When things happened →](23-time.md)
