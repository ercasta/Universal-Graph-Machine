# Concluding versus acting

One last idea, and it's the one this machine's design makes unavoidable.

In most systems, working something out and doing something are obviously
different — one is inference, the other is an API call, and they live in
different parts of the code. Here they're both "running a rule". Same mechanism,
same storage, same way of being called.

Which raises a question no other arrangement has to answer: **when you ask a
question, what stops the machine from going and doing something to answer it?**

## Two rules that reach the same conclusion

```
  ask_the_registrar      pure? False
  conclude_mortal        pure? True
```

Both of these establish that Paul is mortal. One works it out. The other picks
up the phone.

If you ask *"is Paul mortal?"*, only one of them is an acceptable way to find
out. Not because of what it concludes — they conclude the same thing — but
because of what it *does on the way*.

## The bar

```
usable to answer a question: ('conclude_mortal',)
```

> A rule may be used to answer a question only if it **provably never reaches
> the outside** — read off its stored instructions, following every rule it
> calls in turn.

That's Chapter 18's machinery, used for something different. And it's a
**proof**, not a guess — which by Chapter 7's rule means it *prunes*. The
impure rule isn't ranked lower and left available. It's not offered at all.

## Conservative in the opposite direction

Chapter 18's reading is an over-approximation: it errs toward saying a rule
might do something. This one errs the other way.

If the machine **can't tell** whether a rule reaches outside — a call to
something it can't identify, a body it can't parse — the answer is **no**. The
rule is barred.

Both choices are correct because the cost of being wrong differs:

| reading | if wrong | cost |
|---|---|---|
| what a rule establishes | tries a move that doesn't help | wasted step |
| whether a rule is safe to think with | reaches the world while you asked a question | an email you can't unsend |

Same underlying mechanism, opposite defaults, each chosen by asking what happens
when it's wrong.

## What removing it actually does

This is worth measuring rather than assuming, and the answer is more interesting
than the scary version.

Remove the bar, ask a question, and the machine does **not** quietly send the
email. The search happens on a workbench, and Chapter 12's door refuses any
target that exists only in imagination. What you get instead is a crash:

```
Imagined: refusing to dispatch 'registrar'
```

So the immediate effect of removing the bar is that questions stop working — not
that they become dangerous.

The real exposure is one step later. When you decide to **keep** what the machine
worked out, its reasoning is replayed against the real world. There, the outside
call is entirely genuine. A proof containing an impure step sends the mail at the
moment you accept the answer.

So the bar does two jobs, and they're both worth having:

1. it keeps the search from crashing on a candidate it was never entitled to try;
2. it makes *keeping an answer* safe by construction, rather than by you
   inspecting the proof first and hoping you'd notice.

## The general shape

The two guards are layered, not redundant, and the reason generalises well past
this machine:

- the door is the **last** line of defence — it stops effects, wherever they came
  from, but far too late to stop a bad plan being made;
- the bar is what lets questions **work at all** — it keeps the machine from
  ever considering a route it couldn't have taken.

Put a guarantee only in the convenient place and it becomes a habit. Put it
where it can't be forgotten and it's a wall.

---

## That's the book

Where you've been:

- **Part 1** — a world of nodes and named arrows; shapes rather than badges; and
  a rule that runs only when you point it at something.
- **Part 2** — wanting things, imagining them, finding routes, and explaining
  what happened without inventing what didn't.
- **Part 3** — reality disagreeing, contingencies, hard limits, memory, learning,
  and noticing its own intentions colliding.
- **Part 4** — the instructions underneath, and the two readings of a rule's body
  that make planning and safety possible.

The thread running through all of it is one property. **Everything is made of
the same stuff.** Rules, goals, plans, memories, explanations, conflicts — all
ordinary data in one graph. Every capability in Parts 2 to 4 is a consequence:
the machine can plan because it can read its rules, explain because its
reasoning is an object, learn because it can write a rule, and refuse to reason
with a dangerous rule because it can inspect one before running it.

None of those needed a subsystem. They needed the same substrate, asked a
different question.

[Back to the start :octicons-arrow-left-24:](../index.md){ .md-button }
