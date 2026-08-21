# Plans and subgoals

A goal that fits a rule produces a **plan** and a set of **subgoals**.

```
asked for:
  boiling(kettle)  [held]  via <boil>
    water(kettle)  [held]
    heat(anna, kettle)  [held]
```

That indentation is not the report being tidy. It is the search's own shape: a
goal, the plans that fit it, and each plan's subgoals in the order they were
needed. Nothing was recomputed to print it.

## Plans need no minting

`plan(?r, ?w)` is built by substituting into a consequent — and substitution
*interns*, so the same rule expanding the same goal names the same node.

Which is what a plan is: not an object someone allocated, but a name for the
pairing of a rule with a want.

## The trap: a subgoal must be checked inside its plan's bindings

This is the one that would silently produce wrong plans, and it's worth
understanding because it's not obvious.

There are two questions the planner has to ask, and they look like the same
question pointed in two directions:

```
+fit(<R>, goal)        could this rule produce it?         → fits / need / unfit
+check(<plan>, goal)   does the world already answer it?   → achieved + binds / unmet
```

They are different services, deliberately.

*Is this goal already met?* must be computed **inside the plan's bindings**.
Otherwise a subgoal `tap(?t)` gets satisfied by *some* tap — say `sink` — while
`under(kettle, ?t)` gets satisfied by a *different* one — say `drain` — and the
plan is wrong with nothing saying so.

The plan's bindings are what tie the two subgoals to the same tap. Ask the
question outside them and you get two independently-true answers to a question
that had to be answered jointly.

## Every antecedent member is a subgoal — and that was a decision

Read backwards, an antecedent member becomes a subgoal. But not every member
*should* be one:

*To unbolt it, it must be on the bench, and you may put it there. It must also
be a Tuesday.*

The obvious fix is to mark the members that aren't worth planning for. This
design refuses to, and the argument is the earliest instance of a mistake it
generalises everywhere else.

**Achievability is not a property of the member.** It's relative to four things
the rule's author doesn't know:

| relative to | *make it Tuesday* is |
|---|---|
| **who is planning** | out of reach for me, in reach for whoever can move the meeting |
| **the deadline** | achievable with a week, not within the hour |
| **the situation** | already true, on a Tuesday |
| **the rules known** | achievable exactly when `wait` is among them |

A mark authored once, at rule-writing time, is relative to none of them. And
it's the wrong shape besides: achievability is *derived* from capabilities,
budget and the rule set, so stored on the rule it's a cache of a derived value
— invalidated by learning a rule or gaining an authority. Chapter 1's condition
on indexes, failing at the level of a mark.

What the mark would have been doing is three things, each with a home already:

| the work | where it belongs |
|---|---|
| *don't expand this, you'll thrash* | **what comes to mind** (Chapter 27) — learned, and recoverable when wrong |
| *achievable, but only by waiting, or only for the boss* | a **claim**, attributed and deniable, with its cost as timing |
| *you could, and you must not* — seeding clouds to make it rain | a **prohibition** (Chapter 18), checked at the write |

The third is the reason to insist. A mark lets a prohibition masquerade as a
physical impossibility, and those must never share a slot.

So every antecedent member is simply a required entry, and *is this one worth
planning for* is asked of the agent, not read off the rule.

**Waiting is an action**, so a precondition that takes time is achievable at a
price:

```
+tuesday(?d)                                   an ordinary requirement
timing(<WAIT>, start(<A>), end(<B>))           what discharging it costs
bound(<WAIT>, 0, 7days)
```

⚠ `timing` and `bound` are **design notation, not shipped vocabulary** — no
corpus can write them today and nothing reads them. Chapter 23 says what is
actually available for talking about duration (`time(<moment>, <millis>)`, and
ordering by ancestry); this block is the shape the design argues for.

The bill: backward search loses a static bound. *Make it Tuesday* is now a
subgoal a planner may genuinely expand. Chapter 13 is the discipline that
replaces the bound.

## The gap between here and there

A plan starts from a difference: what holds now, and what you want to hold. That
sounds like something a rule should compute, and it is the one shape a rule
cannot — a rule matches one entry at a time and can say nothing about a *set*.

So it is a tool. `<difference>` answers a request naming two spans and a node to
hang the answer on:

```
fact +delta(state(at(home), holds(p1, torch)),
            wanted(at(work), holds(p1, key1), holds(p1, torch)),
            gap1)
```

```
missing(gap1, at(work))            extra(gap1, at(home))
missing(gap1, holds(p1, key1))
```

One entry per difference, which is the half that matters: a set answered *as* a
set would need something to walk it, and one entry per difference is read by an
ordinary member. What the torch shows is that a difference is only what differs
— both spans hold it, so it appears in neither column.

Turning that into a plan needs no plan machinery:

```
rule <want-what-is-missing> = implies( { +missing(gap1, ?p) }, { +goal(?p) } )
```

The tool proposes the gap; a rule decides what is worth wanting. Which is the
same division of labour every tool in this design has (Chapter 22): a tool
computes, and it never concludes.

A span here is either a compound you built — read one deep, so `at(work)` is a
proposition *in* the span while `at` and `work` are what that proposition is made
of — or a **moment**, which is already a node and holds whatever is asserted
there. That is how *the world as it stands* becomes one of the two arguments
without anybody assembling it.

## Plans carry their bindings

A plan is not a list of steps to be re-derived later. It holds what it bound,
which is what makes the check above possible and what makes a plan something you
can be *surprised* by (Chapter 25) rather than merely something you execute.

!!! note "Deep dive: taking one way passes up the others"
    When several rules fit a goal, choosing one is not the same as rejecting the
    rest. This design records `forgone(A, w)` — *this way of getting it was
    passed up* — because a choice that cannot be forgone is not a choice, and
    because when the chosen route fails, the alternatives are the first place to
    look.

    Losing an argument is not being wrong, either. A rule that loses to a more
    specific one is still right about every case the specific rule doesn't
    cover, and retiring it for losing once throws all of those away
    (Chapter 29).

---

**Next:** what the machine says when it runs out of ideas, and why that answer
is harder to get right than it looks.
[Blocked, and what silence means →](13-blocked.md)
