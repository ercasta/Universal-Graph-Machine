# Reading a rule

Chapter 7 said the machine works out which moves might help by **reading the
rule's instructions**. This chapter is that mechanism, and it's where "a rule is
data" stops being an architectural preference and starts doing something no
other arrangement could.

## The problem

The planner has a goal with something missing — *`a` must be on `b`* — and a
library of rules. It needs to know which of them could possibly make that true.

The conventional answer is to have each rule declare its effects. Classical
planners do exactly this, and it works. It also means every rule carries a
second description of itself, written by hand, that can quietly stop matching
what the rule actually does.

## The answer here

A rule *is* graph data. So:

```
# Make the comparison easier to pass by lowering its threshold.
fn lower_threshold(c: comparison) -> comparison:
    GET R(rhs) F(c) "right"
    ATTR R(v) R(rhs) "value"
    ADD R(v2) R(v) -1
    SET R(rhs) "value" R(v2)
```

```
effects : [('attr', 'value', 'c.right', None)]
unknown : frozenset()
```

*It sets the attribute `value`, on the thing reached by following `c`'s `right`.*

Nobody wrote that down. It was read off the instructions at the moment of
asking, so it cannot be out of date — it **is** the body.

## Roles, and why the path matters

Look at what the effect names: not `c`, but **`c.right`**.

That distinction was missing at first, and the failure is instructive. The early
version only recognised writes to a **parameter**. But look at the body: it
navigates to `c`'s right-hand side, holds it in a register, and writes *there*.
The write lands on a register, not on `c` — so the rule was reported as
**changing nothing at all.**

A rule whose entire purpose is to modify part of its argument appeared inert.

And this isn't an exotic case. *Read a part, write to that part* is what most
operations on structured data look like. So the rules that were invisible were
precisely the ones doing real work.

The fix is provenance, and it's free: `R(rhs)` was assigned by `GET R(rhs) F(c)
"right"`, so it denotes *`c`'s right*. Three forms of role, each distinguishable
by inspection:

| role | means |
|---|---|
| `c` | the parameter itself |
| `c.right` | what the body navigated to |
| `$it` | something the body created, with no name outside |

**And the path is resolved late.** Reading the body says *"`c`'s right"* without
knowing which node that is. Only a caller holding actual arguments can turn that
into a specific thing and ask whether it's the one the goal is about. Static
reading plus late resolution — neither half does anything alone.

Without it, the guided search couldn't reach its top confidence band for any
navigating rule, which made it, in measured practice, the same as no guidance
at all.

## Saying what it couldn't read

Sometimes a body can't be read. A label computed at runtime, a call to something
else, a jump that makes the order unclear.

`unknown` reports that — and reports **which parts** it's unsure about, rather
than a single flag. That granularity was a fix too: an unreadable write to `y`
used to darken a description that was provably complete for `x`. Something
consuming the description had to abstain entirely, even though the part it cared
about was fully known.

## The same reading, two opposite safeties

Here's the subtlety that has to be said out loud, because the same answer means
different things to different readers:

> **What a rule establishes is an over-approximation. On purpose.**

It's built to **order** candidates and never to rule one out, so it errs toward
saying a rule *might* do something. For the planner that's exactly right — the
cost of overstating is trying a move that doesn't help, and no solution is ever
lost.

But something using it to decide that a rule **definitely** does something
inherits false positives, and must guard them itself. Same return value,
opposite safety. That property should have been documented the first time; it
was learned when a consumer built recognition on top of it.

## Where assumptions come in

One more piece, and it closes a loop from Chapter 10.

```
fn scan_dir(d: dir) -> listing:
    DISPATCH R(out) "ls" F(d)
    SET F(d) "listed" true
```

Read that body and it establishes almost nothing — everything interesting is on
the far side of the door. It never mentions a file. So a goal of *"some file must
exist"* could never find it.

But the machine reads a rule's **assumed outcomes** too, and the assumption that
listing produces files is exactly what those record. So the knowledge that
scanning yields files lives in the assumption — and the goal finds the action.

Which is something neither the parameter shape nor the result shape could
express, and it's why an opaque outside call isn't simply a blind spot.

---

**Next:** the last chapter, and the sharpest line in the machine.
[Concluding versus acting →](23-concluding-vs-acting.md)
