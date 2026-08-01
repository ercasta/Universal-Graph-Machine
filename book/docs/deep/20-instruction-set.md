# The instruction set

Part 5 is optional. If you've read this far you can use the machine without any
of it. What follows is how the pieces actually work, for the curious.

We start at the bottom: what a rule's body is really made of.

## A rule body is a program

Chapter 4 showed you this and asked you to take it on faith:

```
fn seal(j: jar) -> sealed_jar:
    SET F(j) "sealed" true
```

`SET` is an **instruction**. There's a fixed, small set of them, and every rule
in the machine — authored or learned — is a list of them stored in the graph.

Here's the whole vocabulary:

```
ADD  ATTR  BACK  CALL  CHECK  CLOSE  CONST  COPY  COUNT  DEREF  DISPATCH
DROP  EPROP  EQ  FOCUS  FOLLOW  FORK  GET  GET_AT  HALT  HASFOCUS  HEAD
INVOKE  JMP  JMPIF  JMPNOT  LINK  LINK_AT  LT  MOVE  NEW  NOT  RET
SET  SETREF  SOURCES  SPREAD  UNLINK
```

Roughly: read something (`GET`, `ATTR`, `COUNT`), write something (`SET`,
`LINK`, `NEW`, `UNLINK`), move around (`MOVE`, `BACK`, `FOLLOW`, `SPREAD`),
branch (`JMPIF`, `CALL`, `RET`), call another rule (`INVOKE`), and exactly one
that reaches the outside world (`DISPATCH`).

## Three kinds of thing an instruction can point at

This is the only genuinely unusual part, and it's what makes a rule *pointed*
rather than free-floating:

| written | means |
|---|---|
| `true`, `"sealed"`, `3` | a literal value |
| `R(v)` | a **register** — scratch space, local to this run |
| `F(j)` | a **head** — one of the things this rule was handed |

`F(j)` is the important one. It's how the body refers to *the thing you pointed
me at*. A rule can't reach out and find things to operate on; it works on what
it was given.

And a rule gets a **fresh set of heads** when it's called, holding only its own
arguments — never the caller's. Sharing them would make every rule quietly
sensitive to where its caller happened to be looking, which is exactly the
ambient-context problem the whole design exists to avoid.

## Why not just write Python?

A fair question, since these programs are interpreted by Python anyway.

Because a program that is **data** can be stored, inspected, generated, and
learned. A Python function is faster and more readable and completely opaque —
you can't ask it what it writes, you can't build one from an episode, and you
can't hand it to something for critique.

The dividing line the machine uses:

> **Python for machinery nothing reasons about. Instructions for anything that
> must be inspectable, generated, or learned.**

Chapter 14's learned rule is the proof this isn't theoretical. So is Chapter 22,
which is entirely about reading a rule's instructions to work out what it does.

## Failing loudly

A runaway program doesn't get quietly truncated:

```
MAX_STEPS: 100000
```

Past that, it raises. Knowing in general whether a program will finish is
unsolvable, so the machine doesn't pretend to. It picks a large number and fails
noisily when it's hit, because a silently truncated program produces a plausible
wrong answer — and this book's recurring theme is that those are the expensive
kind.

## One instruction is different

`DISPATCH` is the only way to affect anything outside the graph. That's Chapter
12's single door, and its being a single *instruction* is what makes the door
enforceable: whether a rule can reach the world is a question you answer by
reading its body, which is exactly what Chapter 23 does.

## The undo journal, and its deliberately small claim

The machine can roll back its own graph. Its one job: **a rule that fails
halfway leaves no half-written graph.**

It is emphatically *not* how the machine imagines things — that's Chapter 6's
workbench — and it cannot undo anything that went through the door. Hence the
rule that recurs throughout:

> A rollback boundary must never span a dispatch.

It's kept because it's tiny and makes a failing rule safe by default. It is not
something to build on, and the machine's own notes say that if nothing outside
its test suite turns out to use it, delete it.

---

**Next:** the type system, which is smaller than you'd think and removes more
than you'd expect. [Types as shapes →](21-types-as-shapes.md)
