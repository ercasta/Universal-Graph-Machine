# Noticing it's taking too long

This is the chapter the last two were for.

The machine can plan, act, explain, and refuse. All of those are about the
**world**. Here it does something about **itself**: it notices that its own
thinking is dragging on, decides that's a problem, and stops.

Not because a timeout fired somewhere in the machinery. Because a rule — written
as text, by someone who is not the author of this engine — read a computation in
progress and formed a judgement about it.

## The watcher

Here it is, in full. There is nothing else.

```
# Am I taking too long over this? If so, stop planning.
fn watch_planning(s, budget):
    .again:
    ATTR R(over) F(s) "done"   ;  JMPIF R(over) ".end"
    ATTR R(n)    F(s) "steps"  ;  ATTR R(b) F(budget) "value"
    LT   R(ok)   R(n) R(b)     ;  JMPIF R(ok) ".again"
    SET  F(s) "stop"     "REFUSE"
    SET  F(s) "stop_why" "planning has gone on too long"
    .end:
```

Read it as English. *Is the search finished? Then I've nothing to say. How many
states has it imagined? Fewer than my budget? Fine, look again. Otherwise: stop,
and here is why.*

Every instruction in it is one you met in Chapter 20. `ATTR` reads an attribute.
`SET` writes one. There is no `WATCH` opcode, no monitoring subsystem, no hook.
The thing being watched is a **search node**, and a search node is ordinary data
like everything else.

## What happens

Schedule the goal and the watcher on the same agenda from Chapter 25, give the
watcher a budget of 8, and let it run:

```
judged while the search was still open:  yes, 15 states in, phase 'planning'
the judgement stopped it:                REFUSE
in the rule's own words:                 "planning has gone on too long"
the world:                               untouched
```

And the control, which is what makes it mean anything — the *same* search, same
world, same goal, with a generous budget:

```
imagined all 67 states, and succeeded
```

So the stop is what ended it. Not exhaustion, not an impossible goal, not luck.

## Three things had to already be true

None of them was built for this. That's the claim worth checking, and it's why
this chapter sits at the end of Part 6 rather than the start.

**The state of a running computation has to be data.** How many states a search
has imagined, what phase it's in, where the program counter sits — Chapters 25's
work, and Chapter 7's search before it. Nothing to add.

**The watcher has to run *while* the watched thing runs.** It's a task on the
same agenda, and the agenda rotates. Without that, a watcher could only ever
deliver a post-mortem: *that took too long*, reported after it took too long.

**And the judgement has to be able to have an effect.** This was the one missing
piece, and it was a single line — `stop` as an ordinary attribute, honoured
wherever the machine was already checking whether it was finished.

One line. The rest was already there because of decisions made for other reasons.

!!! note "Monitoring and control come apart, and it's worth knowing which you have"
    Break the machine deliberately in two different ways and you get two
    different failures.

    Make `stop` be ignored: the watcher still judges perfectly, says the right
    thing at the right moment — and the tower gets built anyway. Perfect
    monitoring, no control.

    Remove the interleaving instead: it cannot even judge. No monitoring at all.

    Two halves, and a system can have either without the other.

## What it costs to stop something

Stopping a **search** is cheap. Nothing has happened; the machine gives up
honestly and says so.

Stopping the machine partway through **carrying out a plan** is the valuable case
and the dangerous one. Valuable because *do not take the next irreversible
action* is exactly what you'd want a monitor to be able to say. Dangerous because
it leaves a plan half done.

That's honest rather than new. Chapter 10's divergence already leaves one, and
nothing here is ever undone — real effects have left the graph, and a record of
them is the only thing anybody gets. What's different is that now the machine can
choose to be in that state on purpose, having read the reason for it.

## Say what this is, and don't say more

It's worth being exact, because this is the kind of capability that attracts
grander words than it deserves.

What the machine does here is **inspect and steer its own computational
process**, the same way it inspects a goal or a plan. Its thinking is an object
in its world. That is a specific, checkable property: you can plant a bug in it
and watch the right test go red.

It is not a claim about anything else the word "self" gets used for. The machine
does not have opinions about itself in any other sense, and the fact that a rule
can read a program counter is not evidence that it does.

!!! note "Why the ordinary version still exists"
    The machine already had a way to influence a search: hand it a ranking
    function when you start it (Chapter 16). That's a Python callable, consulted
    once per proposal — the right frequency for a ranker, and the wrong shape for
    something a domain expert writes.

    `stop`-as-data is the same kind of decision expressed as data, which is what
    this project's whole premise demands. The two deliberately produce the
    **same verdict and the same report**, through the same code, so a caller
    cannot tell which route fired. Two report builders would have drifted apart
    invisibly, and one of them would have been wrong.

## The argument this settled

There was a plan, written down three times as the destination of this arc, to
**remove the looping instructions** from Chapter 20 — no backward jumps, so a
rule's termination could be proved by looking at it.

The watcher above is what killed it. A watcher has to poll. Under that plan it
could not have been written as a single rule at all.

Two other measurements said the same thing from other directions: the exactness
it was supposed to buy measured at **zero** on this library, and the termination
guarantee it promised turned out to be relocated one level up rather than
delivered. Three independent routes, one answer, and the strong version does not
survive any of them.

That is what probing a plan is for. It had been the destination for three
sections, and eleven lines of measurement retired it.

---

**Next:** the machine now remembers everything it ever thought. That turns out to
be a bug. [Forgetting is the default →](27-forgetting.md)
