# When two intentions collide

You gave the machine two jobs. Make the crate red. Varnish the crate.

Both succeeded. The crate is not red.

```
interference on 'colour': varnish wrote 'clear', paint wrote 'red'
  for goals: varnish it / make it red
```

Nobody made a mistake. `paint` is correct. `varnish` is correct. Neither knows
the other exists. They were written independently, they do exactly what they
say, and composing them quietly destroyed one of the two outcomes.

This chapter is about noticing that.

## Why this needed rethinking, not copying

An earlier version of this project had conflict detection, and the temptation
was to bring it across. That would have been wrong, and the reason is worth
understanding.

That engine **derived facts**. Two rules concluding contradictory things was a
contradiction, flatly — you can't have a thing be both red and not red.

This engine **performs actions in sequence**. A later write legitimately
overriding an earlier one isn't a contradiction; it's what doing things *is*.
Every single time `stack` runs it sets one crate's top to covered and another's
to clear. Reporting all of that as conflict would bury the handful of cases that
matter under thousands that don't.

So the old notion doesn't transfer. What survives is narrower and more useful:
**interference** — two independently authored actions, brought together by a
library that grew, writing the same thing for unrelated reasons.

That's not a new problem. It's the feature-interaction problem, which the
telephone industry spent decades on: call-forwarding is correct, do-not-disturb
is correct, and together they do something neither author intended.

## The distinction that makes it work

Look at the output again: **for goals: varnish it / make it red.**

That's the whole filter. Two writes to one slot are:

- a **deliberate sequel** if they serve the same goal — the plan meant to paint
  and then varnish, and that's a plan, not a bug;
- **interference** if they serve different goals — nobody decided this.

Without that requirement, the detector reports every ordinary sequence of
actions and becomes noise. With it, the report is small and every item deserves
a look.

## Three wrong versions, each caught by asking "would this notice nothing?"

Worth recording, because each failed in a way that *looked* like it was working.

**Comparing against a running latest value.** This silently lost exactly the
pairs it was hunting for: the second goal re-imagined the *same* action before
its differing one, so a same-goal write overwrote the running value and the
cross-goal disagreement never met. Interference is a property of two *intents*,
so claims have to be grouped by intent and compared afterwards.

**Analysing the search instead of the actions.** Chapter 13's warning, in the
wild. The machine records every proposal it considers, most from branches it
abandons — so a goal that merely *considered* painting looked like it had
claimed to paint. Fixing it meant recording what actually ran, marked as done,
and looking only at that. Which closed a gap that had been open for a while:
until then, execution never reached the notes at all.

**Recording the imagined stand-in as the subject.** Two goals open two
workbenches, so their entries referred to different copies and could never be
lined up. The machine now records the *real* thing a copy stands for — which is
more truthful anyway, since what you did it to is the crate, not your idea of
the crate.

## It needed no new kind of thing

A conflict is recorded as ordinary data:

```
recorded as data: ['connection']
```

That's Chapter 13's cross-link — the same "these two moments are related"
object, with the relation `conflicts`. No new node kind, no new mechanism. The
prediction that this would need "only writing them, not building anything"
turned out to be true.

## Contradictions it can prove in advance

A different question, asked before any work happens: is this goal *impossible on
its face*?

```
unsatisfiable: ("a.colour = 'red' contradicts a.colour = 'blue'",)
```

The machine refuses that goal immediately rather than searching for it. Same for
`never seal` alongside `must seal`, or a budget of zero.

And it reports **only** what it can prove. "You can't build a tower with two
crates" needs knowledge about towers, so it's left to the search to find out
honestly. A detector that guesses produces false alarms, and a conflict report
nobody trusts is worse than none at all — you stop reading it, including on the
day it's right.

## Before the fact

There's a third form, and it's the one with teeth: given two plans that haven't
run yet, would they collide?

That's nearly free — it's the same comparison over two sets of intended writes —
and it reports a problem **before either plan starts**. It's also the only one of
the three that can be *wrong*, because it's a claim about the future. Which is
why it records nothing on the thread: a prediction shouldn't leave a trace that
later reads like history.

---

That's Part 3. The machine plans, acts, recovers, remembers, learns, and notices
when it's working against itself.

**Next, and optional:** how the pieces actually work.
[The instruction set →](../deep/16-instruction-set.md)
