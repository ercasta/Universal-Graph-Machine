# Above and below the horizon

*If a rule is data, and a goal is data, and even a half-run program is data —
what **isn't**, and why not?*

[Chapter 20](../deep/20-instruction-set.md) drew a line. Underneath it: the
substrate — nodes, arrows, running instructions, taking turns. Above it:
decisions — what a plan is, what a type is, what counts as a reason. The test
was *would someone rebuilding this from scratch have to make a decision here?*

That line is real, and it is not the only one. There is a **second** line,
higher up, and almost everything interesting about this project's current work
lives on it. Confusing the two is the easiest mistake in the building, so this
chapter names them apart.

## Two kinds of "primitive"

Take goals.

**Goals themselves are wide open.** Anybody can write one, the machine can mint
one mid-plan, a goal can be pointed at, compared, decomposed into other goals,
recorded as having been pursued. Nothing about goals is a fixed list. They are
ordinary data in the graph like everything else in this book.

But now look at what a goal is *made of*. Each thing it requires is a
constraint, and a constraint has a **sort** — this edge must exist, this slot
must have this value, this thing must fit this shape, this must never happen
along the way. That list is short and it is **fixed**. And you cannot get a new
one by writing rules: there is no arrangement of types and criteria and methods
that produces a genuinely new kind of requirement. The engine branches on the
sort, and that branch is the end of the road.

So two different questions pull apart:

- *Would somebody rebuilding this have to make a decision here?* — **yes**, for
  constraint sorts. Somebody chose those four. That puts them **above** Chapter
  20's kernel boundary: they are business, not machinery.
- *Can the layer above define them away?* — **no**. That puts them **below** a
  second line.

Two questions, two lines, three layers:

| layer | example | how you'd port it | can the layer above define it away? |
|---|---|---|---|
| **the substrate** | the graph, the instruction set, the single door | re-implement it | — |
| **the closed class** | constraint sorts, consequent kinds, tie-break stages, the proposition forms | re-implement it | **no** |
| **the web** | goals, types, criteria, methods, functions, norms, memories | carried over unchanged | n/a |

Notice where `goal` landed: in the **web**. It was tempting to call the whole
notion primitive, and it isn't — only its constraint vocabulary is. That is the
distinction this whole chapter is for, and it is easy to get wrong in the
direction that makes the closed class look bigger than it is.

The **kernel boundary** sits between the first two. The **horizon** sits between
the last two. This chapter is about the horizon.

## Above it: a web

Everything in the top row is authored data, and none of it is foundational.

A type is a shape, checked against other structure. A criterion speaks about
goals. A method decomposes into steps that mention other methods. A norm names a
speaker who is a node like any other. Pull on any one of them and the others
move.

That is the point rather than a weakness. A concept up here means what it means
because of **where it sits in the network** — not because it was defined once,
correctly, in terms of something more basic. Nothing in the web is individually
checkable against the world; you check the web against the world *as a whole*,
and when something doesn't fit you get a choice about which strand to revise.

This is where the outer loop of [Chapter 25](../watching/25-one-loop.md) works,
and it is where almost everything should live.

## Below it: a closed class

The bottom two rows are where the machine stops. A closed class is a **fixed,
named set** — the sorts a goal constraint may have, the kinds a rule's
conclusion may be, the stages a tie-break may use, the opcodes.

They are primitive not because they are simple — some of them run a great deal
of code — but because nothing above them reconstructs them.

Which raises the obvious hazard: a closed class grows one member at a time, each
addition individually reasonable, and after a while the "small fixed vocabulary"
is a hundred special cases nobody can hold in their head. So the machine holds
itself to a shape.

!!! note "What a well-formed closed class looks like"
    Three properties, and the third is the one people forget:

    1. **It is named** — there is a thing called `STAGES`, not a chain of `if`s
       spread over a file.
    2. **It is readable as data** — the machine can be asked what the members
       are, and each member has something that actually runs it. A tag with
       nothing behind it is worse than no tag at all, because it looks like a
       capability.
    3. **It states whether it has an escape.** Tie-break stages have one: you
       can supply your own comparison and the closed set becomes *what ships*
       rather than *what is possible*. A rule's conclusion kinds deliberately
       have **none** — and say so.

    Either answer is fine. Having no answer written down is not: that is a class
    that may be right by accident, and nobody will know when the next member is
    added by reflex.

    The genuine failure is a fourth thing — a closed class that is neither named
    nor readable, living only as a Python function nobody can see. That is an
    island, and this book has been about islands since Chapter 20.

## The same three layers, found from the other end

Here is the part that suggests the line is in the right place rather than merely
convenient.

A completely different piece of work asked a completely different question — not
*what can't be defined away?* but **what may a rule not do directly?** Chapter 34
is that story. It landed on three layers too:

| layer | membership | must it be complete? |
|---|---|---|
| the instruction set | fixed | closed |
| **the eight access names** | fixed | **closed, and must cover every case** |
| domain vocabulary — *the supports of*, *the wheels of* | open, grows forever | no, and never will be |

Different question, same shape, and the middle layer is forced for a reason that
has nothing to do with definitions: you cannot get **complete coverage** out of
an open-ended set. There is always one more name somebody hasn't written yet. So
the mediating layer has to be a fixed set, with the open vocabulary written *in
terms of* it.

Two independent routes to the same cut is about as much evidence as this kind of
thing ever offers.

## The direction of travel: make it smaller

None of the above says the closed class should be *comfortable*. The project's
active work is on shrinking it, and the surprise has been how much of it turned
out not to be primitive at all — six things confidently listed as irreducible,
of which four were plain arrow-reads once somebody actually tried. Chapter 34 is
that story in full.

So the working rule is not *classify things and move on*. It is:

> **A thing is primitive only after you have tried to take it apart and named
> what was missing.**

Which is why the register of closed classes above is written the way it is:
short, named, and expected to get shorter.

## The mistake that looks like progress

Here is why the distinction earns a chapter.

Sooner or later you try to express something and can't. The tempting reading is
that there are two ways out: add it to the built-in vocabulary, or give up.
There are **three**, and the third is the one that gets misused.

1. **Expand the closed class.** Costs a permanent member, and it must have
   something that runs it.
2. **Keep it opaque.** Named and declared, not broken down. An honest answer,
   and often the right one.
3. **Relate it in the web.** Write ordinary rules connecting the new thing to
   what already exists — *without claiming it reduces to them*.

The classic warning is a linguist's. *Kill* is not defined as *cause to die*.
The two are related — obviously, usefully, and you want the machine to know it —
but the relation is an inference the web supports, not a decomposition into
parts. Say *kill = cause to die* and you have written a definition that is subtly
and confidently wrong, and it will be wrong in a place far away from where you
wrote it.

So mistaking (3) for (1) is the error to watch for. You *feel* like you have
explained something, and what you have actually done is bolt a false definition
underneath the machine.

The pressure runs the other way too, and it is quieter: option 1 always looks
like the tidy answer in the moment. The way to keep the closed class small is to
make option 3 the **default** and force option 1 to argue its case.

## The economics, which settled the argument

There is a blunter reason this works out, and it is worth knowing because it
turned a philosophical preference into an ordinary engineering one.

The authored language **cannot grow itself**. Adding a new kind of block — a new
family of things a domain can write — is an edit to the parser, forever. That is
a deliberate choice rather than an oversight: a grammar that is itself data is a
real research commitment, and this project declined to take it on.

The consequence is that families are a **budget**. And once they are a budget,
*relate it in the web* stops being merely the principled answer and becomes the
**cheap** one — it costs nothing from the budget at all.

An audit of the whole system worked through eight cases of "this can only be
said in Python", and the pattern held every single time: **every expansion came
in smaller than its first estimate.** One was predicted to need a whole new
execution path and needed none. Another was predicted to be "the large one" and
cost two members inside a family that already existed. Two cost no capability
whatsoever — the fix was to write down a position that was already being held
silently.

That is the whole method in one line: **decide where the horizon is, deliberately,
and make crossing it argue for itself.**

---

**Next:** what all of this is *for* — the machine currently moving its own
planning out of Python, one decomposition at a time. [Moving the line
→](34-moving-the-line.md)
