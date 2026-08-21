# The agent's own state

One of the seven requirements this design was built around says:

> **The agent's own state is in the world it reasons about.**

Expectations, commitments and in-progress procedures must be facts on the graph,
not variables in an interpreter. Otherwise the agent cannot notice that an
expectation failed, cannot be asked why it abandoned a plan, and cannot have a
strategy overridden by a statement in its knowledge base.

This chapter is what that buys, and it starts with the sharpest example.

## Surprise is a match

> **Surprise is a match.** It is an *expected* entry and an *observed* entry
> that disagree.

That's the entire mechanism. And it only works if the expectation is actually
*there*, as an entry, in the graph. If expectations lived in interpreter
variables, an expectation would go unmatched not because the rule was weak but
because there was nothing to match against.

Three obligations follow.

**1. Applying a rule deposits what it predicts.** Applying `causes(A, B)`
writes `+expects(<B>, plus)` — a claim *about* a proposition and a sign.
Without the deposit there is nothing to be surprised against.

Note the shape. A sign appears here **as an argument**, not inside the
proposition: `expects(p, plus)` mentions a sign where `+p` uses one, which is
what makes the prediction an ordinary readable claim rather than a new kind of
thing. (The design first proposed a *predicted moment* instead — a whole
successor carrying B's entries and a due-time. What shipped is smaller, and it
gave up the due-time with it: the agent notices that a prediction was
contradicted, never that one is *late*.)

**2. The continuation is a moment.** What the agent is doing, where it is in it,
and what it's waiting for are signed entries — not a stack frame.

*Stack frame* here means the interpreter's: opaque, owned by the runtime, and
unreachable by a rule. This design's frames are the opposite in every respect —
process nodes, readable, writable, and **selectable** — which is why they can be
preempted and an interpreter's cannot.

**3. Surprise is an ordinary rule, and it wins its turn like any other.**

```
rule <S> = causes( { +deviates(?p) },
                   { +goal(explain_failure(?p)) } )
```

`deviates(?p)` is arity **one** and it is what the four bundled rules below
conclude; there is no `due`/`after` to consult, for the reason just given.

> **There is no interrupt mechanism.**

Preemption is `<S>` being selected over the rule that would have continued what
the agent was doing — which is possible only because *continue what you were
doing* was itself a selectable rule. That is exactly what a stack frame is not.

## What this used to need, and what actually fixed it

Built early, the loop didn't merely respond slowly. It never responded at all,
and the failure wasn't the one you'd predict.

An agent heats water and expects it to boil. The gauge reports it is not
boiling. Now **two rules apply forever**: the causal rule re-concludes `+boiling`
because its antecedent still holds, and the trust rule re-concludes `−boiling`
because the gauge still said so. They alternate.

The surprise rule is **never selected**, because arbitration prefers the rule
authored first, and the oscillation starves it.

The fix at the time was one authored fact — a precedence saying the surprise
rule beat the causal one. It worked, and it was the wrong diagnosis. Run the
same corpus today, with nothing outranking anything:

```
after the gauge speaks:  6 moves, ended quiescent

  intake → trustF → deviation-+-contradicted → why → ask-recall → give-up
```

`<why>` gets its turn, and the pair does not oscillate. What stopped the
oscillation was **refraction**: an application is spent on the premises it
matched, so *this instantiation has run* is a different claim from *this rule
scored low*, and a rule that has already concluded from these exact premises does
not do it again.

That is the general shape, and it survives the mechanism that used to carry it:

> **A contradicted expectation does not stop being re-derived.** Nothing retracts
> the rule that produced it. Either something outranks it, or the loop stops
> re-deriving what it has already derived from the same premises — and it is the
> second.

!!! note "Deep dive: two riders that outlived the mechanism"
    While precedence existed, two things about it were learned the hard way, and
    both are worth keeping as facts about *any* scheme for making one rule beat
    another:

    - Being outranked has to mean **not applying at all**, never merely applying
      second — or the loser re-asserts on the following tick and quietly undoes
      the winner. Ordering is not defeasibility.
    - **Whether a rule is out is about whose antecedent holds, not about who
      still has work to do.** Filtering rules whose conclusions are already
      written has to happen *after* that question, not before, or the winner
      disappears the moment its conclusion is present and the loser is left
      unopposed.

    Precedence is gone (Chapter 17) and both lessons are why: neither could be
    bought with a score, and once the exception moved into the premise there was
    nothing left for the relation to do.

A strategy stopped by a statement in the knowledge base rather than by an
interpreter. That's the whole point.

!!! note "Deep dive: starvation is not only the surprise rule's problem"
    A rule that would *settle* a conflict can be starved by the conflict it would
    settle: `hot`, `cold`, `hot`, `cold`, and the referee never gets a turn.

    Same shape from a third side, and it takes the same answer — `standing`, the
    claim that a rule must always be considered.

## Four rules, not one comparison

Noticing a deviation could be one comparison: expected sign against observed
sign. It isn't. It's four rules — two expected signs against the two ways an
observation can contradict one: the opposite sign, and `?`.

As a single comparison, the machinery was quietly asserting that *invalidated,
and I cannot say what replaced it* disappoints an expectation exactly as much as
the opposite outcome does.

That's a real claim. It may be wrong. And as a branch there was nowhere to argue
with it.

> **A `for` loop over four tuples is a branch wearing a row's clothes.**

Written out as four rules, the claim became arguable — and three of the four
turned out to be unexercised, which a branch would have hidden forever.

Which is the other half of the same lesson:

> **Data rots in a way a branch does not.** A dead branch is dead code. A rule
> that never applies costs nothing, breaks nothing, and looks exactly like a rule
> that works.

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
