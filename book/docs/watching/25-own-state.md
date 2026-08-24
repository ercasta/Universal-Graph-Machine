# The agent's own state

One of the seven requirements this design was built around says:

> **The agent's own state is in the world it reasons about.**

Expectations, commitments and in-progress procedures must be facts on the graph,
not variables in an interpreter. Otherwise the agent cannot notice that an
expectation failed, cannot have a claim about its own conduct denied by another
rule, and cannot have a strategy overridden by a statement in its knowledge
base.

This chapter is what that buys, and it starts with the sharpest example — with
one honest correction up front: the graph tells any rule *what* is currently
believed, and that includes an agent's own predictions and commitments. It
does not tell anyone *why* a belief arrived — that gap is tracked in
[`../horizon/34-not-built.md`](../horizon/34-not-built.md). The argument in
this chapter is about the first claim, not the second.

## Surprise is a match

> **Surprise is a match.** It is an *expected* entry and an *observed* entry
> that disagree.

That's the mechanism, and it only works if the expectation is actually
*there*, as an ordinary claim, in the graph. If expectations lived in
interpreter variables, an expectation would go unmatched not because the rule
was weak but because there was nothing to match against.

Two obligations follow.

**1. A rule that predicts has to deposit the prediction, itself.** A rule that
wants to be surprised has to say what it expects, as an ordinary consequent
member, the same as anything else it concludes.

```
rule <boils> = implies(
    { +heating($k), no boiling($k) },
    { +boiling($k), +expects(boiling($k), plus) } )
```

Note the shape. A sign appears here **as an argument**, not inside the
proposition: `expects(p, plus)` mentions a sign where `+p` uses one, which is
what makes the prediction an ordinary readable claim rather than a new kind of
thing.

**2. The continuation is a fact, not a stack frame.** What the agent is doing
and what it's waiting for should be readable, not opaque interpreter state.
Suspending a line of work for another (`push`/`pop`, Chapter 28) is on the
record — every push and pop deposits a claim (`pushed(x)`, `popped(x)`) a rule
can read. The frame itself — the queue of what the agent is currently
attending to — is engine state kept outside the graph (`Machine._frames`), not
a node a rule can select among: opening and closing a frame is on the record,
but its contents are not selectable the way a rule is. What **is** fully on
the record and fully selectable is which rule runs next, which is the next
point.

**3. Surprise is an ordinary rule, and it wins its turn like any other.**

```
rule <deviation> = implies(
    { +expects($p, plus), +not($p), no deviates($p) },
    { +deviates($p) } )

rule <explain> = implies(
    { +deviates($p), no goal(explain_failure($p)) },
    { +goal(explain_failure($p)) } )
```

`deviates($p)` is arity **one**, and it is what a corpus's own deviation rule
concludes; there is no `due`/`after` the engine consults on its behalf —
nothing bundled watches predictions.

> **There is no interrupt mechanism.**

Preemption is `<explain>` being selected over the rule that would have
continued what the agent was doing — which is possible only because *continue
what you were doing* is itself an ordinary, selectable rule. That is exactly
what a stack frame is not.

## Surprise, run for real

An agent heats water and expects it to boil. A gauge reports it is not
boiling. Reconstructing the whole chain as an ordinary corpus — `<boils>`, a
trust rule reading an arrival, `<deviation>`, `<explain>` — and running it:

```
fact +heating(k1)
fact +heating(k2)
say world: +not(boiling(k2))
```

```
surprise.ugm: 9 ticks, ended quiescent

what it believes, newest first:
  goal(explain_failure(boiling(k2)))
  deviates(boiling(k2))
  not(boiling(k2))
  expects(boiling(k1), plus)
  boiling(k1)
  expects(boiling(k2), plus)
  boiling(k2)
  says(world, not(boiling(k2)))
  arrived(world, not(boiling(k2)))
  heating(k2)
  heating(k1)
```

`<explain>` gets its turn — `intake`, `boils` twice, a trust rule, `<deviation>`,
`<explain>`, in that order — and the run quiesces at 9 ticks. No oscillation to
break, because nothing re-derives a conclusion it already holds:

> **A guarded rule does not re-derive what it has already derived.** Nothing
> retracts the rule that produced a belief. Either something outranks a rival
> that would contradict it, or — as here — each side of the disagreement
> simply concludes once and stands, on the record, for something else to
> reconcile.

A strategy stopped by a statement in the knowledge base rather than by an
interpreter. That's still the whole point: it's a corpus's job, not the
engine's.

!!! note "Deep dive: starvation is not only the surprise rule's problem"
    A rule that would *settle* a conflict can be starved by the conflict it
    would settle: two rules disagreeing forever, and the referee never gets a
    turn. Same shape from a third side, and it takes the same answer —
    `standing`, the claim that a rule must always be considered (Chapter 28).

## Not one comparison

The deviation check is two rules: an `expects(p, plus)` contradicted by
`+not(p)`, and an `expects(p, minus)` contradicted by `+p`. A member's sign is
`+`, `-`, or `no` (Chapter 3) — there's no third state, and unknown is
expressed by simply not yet asserting anything.

> **A `for` loop over these cases is a branch wearing a row's clothes.**

Written out as separate rules rather than folded into one comparison
function, each case is something a corpus can keep, drop, or override on its
own — which a branch, by construction, cannot offer.

> **Data rots in a way a branch does not.** A dead branch is dead code. A rule
> that never applies costs nothing, breaks nothing, and looks exactly like a
> rule that works.

That's why this project's gate for its shipped rules **deletes each one and
re-runs the suite**, and reports any rule whose removal breaks nothing.

## Procedures are data

The same argument, one level up.

> **Procedures exist, but as data that biases selection — never as control flow
> that owns the loop.**

A procedure written as control flow owns the agent until it returns. Nothing can
preempt it, nothing can ask where it is, and nothing can override it. Written as
data — a sequence of claims about what to do next, biasing which rule is
selected — it can be interrupted at every step, inspected, and argued with.

This is not primarily about speed. An automatic thought is fast, unexamined, and
effective right up to the point where it is wrong; what makes it changeable is
being able to slow it down and look at it.

That gives three states rather than two:

| | fast | inspectable | interruptible |
|---|---|---|---|
| **the floor** | — | n/a | n/a |
| **convention, interpreted** | no | yes | yes |
| **convention, compiled** | yes | no | only at rule boundaries |

> **Nothing may exist only in the third state.**

Which decides *how* to compile, if you compile at all:

> **Compile rules, not control flow.**

Compile a whole chain walk into one host-language function and preemption is
gone — nothing can surprise the agent mid-read. Compile each rule's *matching*
into a fast closure and leave the selection loop interpreted, and every
preemption point survives while nearly all the speed is captured, because the
cost is in matching and not in the loop.

---

**Next:** knowing when you're finished, which turns out to be two different
questions.
[Stopping →](26-stopping.md)
