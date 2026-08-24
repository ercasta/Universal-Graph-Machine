# Plans and subgoals

Chapter 11 got one real mechanism out of "reading a rule backwards": recall,
a lookup from a goal's relation to the rules that could conclude it. What
this chapter is about — turning a recalled rule into a **plan**, and its
antecedent into **subgoals** to satisfy in order — is the design this project
argues for next. Some of it is running code. Most of it is not, and this
chapter says which is which as it goes.

## The part that is built: the gap between here and there

A plan starts from a difference: what holds now, and what you want to hold.
That's not something a rule can compute — a rule matches one entry at a time
and can say nothing about a *set* — so it's a tool. `delta` answers a request
naming two states and a node to hang the answer on:

```
fact +at(home)
fact +holds(p1, torch)

fact +delta(state(at(home), holds(p1, torch)),
            wanted(at(work), holds(p1, key1), holds(p1, torch)),
            gap1)

rule <want-what-is-missing> = implies(
  { +missing(gap1, $p), no goal($p) }, { +goal($p) } )
```

```
3 ticks, ended quiescent

what it believes, newest first:
  goal(at(work))
  goal(holds(p1, key1))
  holds(p1, torch)
  at(home)
```

`missing(gap1, at(work))` and `missing(gap1, holds(p1, key1))` are what the
tool wrote; `<want-what-is-missing>` is an ordinary rule deciding what's worth
wanting. What the torch shows is that a difference is only what differs —
both states hold it, so it appears in neither `missing` nor `extra`.

That `no goal($p)` guard is load-bearing, not decoration. Leave it off and the
rule matches the same `missing` entry every tick forever — writing a fact
that's already believed is a no-op, but the engine still counts it as an
**application**, and only a genuinely empty match set ends a run
`quiescent`. Every corpus in this chapter that concludes something durable
needs a guard like this one, the same way `ugm/rules/worked.ugm`'s own
`<boil>` guards on `no boiling($w)`.

And when the two states differ in **nothing**, the tool says that outright:

```
fact +at(work)
fact +delta(state(at(work)), wanted(at(work)), gap1)
```

```
matched(gap1): believed
```

Which looks like a convenience and is not:

> A rule reads differences one at a time, so it can act on every `missing`
> there is — and it can never conclude that there were none. *No missing* is
> a claim about the whole set. The tool is the only party that has seen the
> whole set, so the tool is the one that says it.

Try to write "no missing" as a rule guard instead and the loader refuses it,
for the same reason absence never picks out a variable (Chapter 6):

```
rule <bad> = implies( { no missing(gap1, $p) }, { +done(gap1) } )
```

```
rule 'bad' asks `no missing(gap1, $p)` with a variable no earlier
member binds -- an absence is a check on things already picked out,
never a way of picking them out
```

`matched($g)` is what a corpus reads instead — the tool's own claim that the
set closed, not a rule's attempt to say so:

```
rule <done> = implies( { +matched($g) }, { +enough($g) } )
```

Set a goal, compute the gap against where you are, and stop when it closes.
Chapter 26 has what `enough` then does with that.

A state here is either a compound you built — read one deep, so `at(work)` is
a proposition *in* the state while `at` and `work` are what that proposition
is made of — or `state(...)`/`now`, which is already how *the world as it
stands* gets built without anybody assembling it: `now` reads the whole
scratchpad, minus the machinery's own bookkeeping.

## The part that is design, not yet running code

`delta` computes a difference. Getting from *a goal is worth having* to *a
plan that discharges it* — matching the goal against a recalled rule's
consequent, turning its antecedent into subgoals with the same binding
carried through — is not built. `docs/feature-requests.md` lists it as open
("Subgoal splitting", "Goal-as-commitment vs. goal-as-belief"); this book's
own gap chapter, `horizon/34-not-built.md`, doesn't single it out by name but
its classification applies squarely: nothing in the design resists it, it's
simply not built yet.

The argument for why it has to work a particular way is worth keeping,
because it's the same argument that shaped `delta`, and it will bind whatever
eventually gets built:

**A subgoal must be checked inside its plan's bindings.** *Is this goal
already met* has to be computed with the *same* bindings that produced it,
not asked cold. Otherwise a subgoal `tap($t)` gets satisfied by *some* tap —
say `sink` — while `under(kettle, $t)` gets satisfied by a *different* one —
say `drain` — and the plan is wrong with nothing saying so. A plan that binds
`$t` once and carries it through both checks doesn't have that failure mode;
one that re-asks each subgoal independently does. That's a constraint on
*any* implementation of "check", not a property of one that happens to exist.

**Every antecedent member is a subgoal — deliberately, not by omission.**

*To unbolt it, it must be on the bench, and you may put it there. It must
also be a Tuesday.*

The obvious fix is to mark the members not worth planning for. The argument
against doing that is worth keeping intact:

**Achievability is not a property of the member.** It's relative to four
things the rule's author doesn't know:

| relative to | *make it Tuesday* is |
|---|---|
| **who is planning** | out of reach for me, in reach for whoever can move the meeting |
| **the deadline** | achievable with a week, not within the hour |
| **the situation** | already true, on a Tuesday |
| **the rules known** | achievable exactly when `wait` is among them |

A mark authored once, at rule-writing time, is relative to none of them, and
it's the wrong shape besides — achievability is *derived*, so stored on the
rule it's a cache of a derived value, invalidated by learning a rule or
gaining an authority. What the mark would have been doing is three things,
each with a different honest home: *don't expand this, you'll thrash* is what
comes to mind (Chapter 27); *achievable but only by waiting, or only for the
boss* is an ordinary claim, attributed and deniable; *you could, and you must
not* is a prohibition (Chapter 18), checked at the write. A mark lets a
prohibition masquerade as a physical impossibility, and those must never
share a slot. So every antecedent member stays a required entry, and *is this
one worth planning for* is a question for the agent to answer with its own
rules, not one baked into the rule being planned over.

**Waiting is an action**, so a precondition that takes time is achievable at
a price:

```
+tuesday($d)                                   an ordinary requirement
timing(<WAIT>, start(<A>), end(<B>))           what discharging it costs
bound(<WAIT>, 0, 7days)
```

`timing` and `bound` are **design notation, not shipped vocabulary** — no
corpus can write them today, and nothing in `ugm/core/text.py` lexes either
name. Chapter 23 has what's actually available for talking about duration.
This block is the shape the argument points at, marked as exactly that.

!!! note "A sketch that's still just a sketch: forgoing"
    When several rules fit a goal, choosing one shouldn't erase the rest —
    the design's proposal is a fact, `forgone(<R>, w)`, recording *this way of
    getting it was passed up* rather than refuted, so a failed plan has
    somewhere to look next. Nothing writes `forgone` today; `grep`ping the
    engine for it returns nothing. It's here because the reasoning behind it
    doesn't depend on it being built: a rule that loses to a more specific
    one is still right about every case the specific rule doesn't cover, and
    a chooser that can't record "passed up, not wrong" would eventually have
    to start treating losing as being wrong.

## Plans would carry their bindings

If a plan is ever minted, it shouldn't be a list of steps to be re-derived
later — it should hold what it bound, the way `delta`'s gap already holds
what it computed. That's what would make the check above possible, and what
would make a plan something you could be *surprised* by (Chapter 25) rather
than merely something you execute. Recall already gives away why plans would
need no separate minting step if they existed: substitution *interns*, so
the same rule expanding the same goal would always name the same node,
without anyone allocating one.

---

**Next:** what the machine says when it runs out of ideas, and why that
answer is harder to get right than it looks.
[Blocked, and what silence means →](13-blocked.md)
