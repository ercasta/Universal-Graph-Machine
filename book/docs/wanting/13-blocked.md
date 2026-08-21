# Blocked, and what silence means

```
asked for:
  boiling(kettle)  [open]  via <boil>
    water(kettle)  [held]
    heat(?a, kettle)  [BLOCKED]
```

`BLOCKED` is the machine reporting on **itself**. It means: I expanded this
goal, nothing fit, and I have stopped trying.

It does not mean *there is no way*. It means *I found no way*.

## Why `blocked` cannot be an ordinary conclusion

Here's the natural rule, and it's wrong:

```
implies( { +goal(?w), +unfit(?r, ?w) }, { +blocked(?w) } )
```

That fires when **some** rule doesn't fit. What `blocked` claims is that **no**
rule does.

That's an aggregate over a *finished* search, and positive rules can't say it.
Nor does a `−` member help: *an entry says this does not hold* and *no entry*
are neither of them *for no `?r`*.

So:

> **Bounded expansion returns a result and a state. `blocked` is the state.**

A state is what a searcher reports about *itself* when it stops. And this design
gives it a home rather than a special case: the aggregate becomes legitimate at
`quiet` — the fact that says a search has finished. Until such a fact existed,
there was nowhere in the graph where such a claim was true.

You can see it in the licence:

```
because +blocked(heat(anna, kettle)), licensed by verdict(heat(anna, kettle))
because +verdict(heat(anna, kettle)), licensed by applied(<give-up>)
because +quiet(moment()), licensed by quiet(moment())
```

`quiet` first. Then a rule called `<give-up>` reaches a verdict. Then `blocked`.
Every step is a dated claim.

## Two silences that must stay different

This is the general principle, and it runs through the whole design:

> **Nothing came to mind is not nothing is left to do.**

Only the second should escalate outward. The first is a report about the
agent's own attention, and the right response to it is to widen — look harder,
consider more — not to conclude anything about the world.

A shortlist that ran dry and a search that finished look identical from
outside, and confusing them is how a reasoner starts making claims it hasn't
earned.

The same shape, one more time, from a different direction:

| silence | means |
|---|---|
| no entry for a proposition | **unchanged** — inherit from before (Chapter 3) |
| the walk found nothing | I have no claim about this |
| nothing came to mind | my attention was too narrow |
| the search finished, nothing fit | `blocked` — a claim about the search |
| this application would change nothing | quiescence — and it is **silent by construction** |

That last row is the dangerous one, and it's the one this project found by
building rather than by argument. Matching returning nothing is observable. A
write refusing is observable. *This would change nothing* is indistinguishable
from *there was nothing to apply* — so a whole capability can be quietly
dropped and look exactly like correct behaviour. Chapter 10 has the case where
that actually happened.

## `blocked` is an occasion

The useful thing about `blocked` being a deposited fact rather than an internal
state is that a corpus can key on it.

```
rule <ask-for-it> = implies( { +blocked(have(p1, ?k)) },
                             { +doing(tell(dm, want(p1, ?k))) } )
```

*When I have exhausted what I can do alone, ask somebody.* That's the one moment
where another mind is worth anything, and the agent can now notice it.

And the same for running out of budget. A run that is still working when the
tick limit bites deposits `bounded(ticks)`, so a corpus can notice its own
runaway rather than being cut off silently:

```
rule <panic> = implies( { +bounded(ticks) }, { +goal(diagnose(myself)) } )
```

## Stopping with a goal still open

There's a stronger claim in the same family, and it's worth stating now because
it constrains Chapter 26:

> **The loop may end. It may not end quietly on something it was asked for.**

Quiescence — nothing further to apply — is *exhaustion*. It is not the same as
having got what you wanted. An open goal is a veto that outranks a satisfaction
signal, and a stop with a goal still open has to be reported as such.

---

**Next:** the machine has a plan and a subgoal it can discharge. What does
"doing" actually mean here?
[Acting →](14-acting.md)
