# How strongly

*Rain is likely this afternoon.*

Where does the *likely* go?

The obvious answer is: on the claim, as a number or a grade. This design tried
that, argued for it at length, built it, **measured it**, and deleted it. This
chapter is that story, because the reasoning is more useful than the conclusion.

## Four things called possibility

First, a distinction that has to be made before anything else, because these
four must not share a slot:

| | what it is | where it goes |
|---|---|---|
| **strength** | how firmly this is claimed | a **wrapping proposition**: `likely(p)` |
| **confidence** | how far you trust where it came from | an ordinary **claim about the source** |
| **defeasibility** | what would cancel it | **not a number** — a relation to other rules |
| **achievability** | whether *this* agent can bring it about, now, within budget | **nowhere** — derived at read time |

Collapse those into one number and `0.6` means three things at once, and
combining two such numbers is arithmetic nonsense.

Two of them are worth dwelling on.

**Defeasibility** is the load-bearing one for reasoning — *unless the front has
already passed* — and it needs no numeric apparatus at all. It's the same
precedence machinery that makes the boss's rule beat the vice's (Chapter 17).

**Confidence is a property of the source, not of the rule.** *How sure am I of
this rule*, *how sure am I of this sensor*, and *how far do I trust this
speaker* are one question asked of three sources — and every entry already names
the source it arrived through. A confidence slot on rules would cover the first
case only, and would have to be reinvented for the other two.

## The answer that was rejected

The candidate was an ordinal **grade**, stored as a fourth member of the entry.
The argument was good.

*Not on the proposition node*, because a grade there is a cache of a derived
value: *rain is likely* holds only given the support that produced it, so when
the support changes the tag must be invalidated — and general invalidation over
a web of dependencies is a truth-maintenance system, a second machine with its
own consistency problem running underneath the first.

*Not as a separate tag*, because a tag is a separate read: you could obtain the
fact without the grade, and an ungraded conclusion reads as certain.

*So put it on the entry.* An entry cannot be matched without its sign, because
the sign is a member. Put the grade there and it can't be matched without its
grade either. One read, or none. And the entry had to exist anyway, so the slot
cost nothing structurally.

**Every step of that is valid.** It settles *where a grade should live* and
never asks *what a grade is for* — and the second question has an answer that
dissolves the first.

Measured three ways, and they agreed:

- **It ranked last of three treatments.** A grade is not a term, so no rule can
  ask *is this merely likely*. There is no guard to cross. And it doesn't nest.
- **Almost nothing used it.** Across a whole suite: **4 of 3,740 rules** authored
  a non-certain grade, and **6 of 32,289 entries** carried one.
- **Nothing ever decided on it.** The function comparing two grades was called
  from exactly one place. Every other read carried it forward or printed it.

> **The grade was carried, composed and printed, and never obeyed.**
>
> **A knob that is read and not obeyed is the same defect wearing the fix's
> clothes.**

So the fourth member is gone, and the entry is back to three members and never a
fourth.

And the larger half: **the closed set went with it.** Five ordinal names the
engine knew became whatever modalities a corpus cares to write, with whatever
ordering it authors.

## What replaces it

Modality is a **proposition**. `likely(p)` is a wrapping node — the same
construction as `on(a, b)`, with one arm rather than two.

```
rule <weather> = implies( { +cloudy(?d, morning) },
                          { +likely(rain(?d, afternoon)) } )
```

Three things this buys that a grade cannot, none of them arguments:

| | grade on the entry | term |
|---|---|---|
| a **rule** can ask *is this merely likely* | no — a grade is not a term | yes |
| the **guard holds** — nothing acts on the unwrapped claim | no; a grade annotates a conclusion the actor still sees | yes, structurally |
| it **nests** — `thinks(anna, likely(rain))` | no | yes |

The second row is the one with teeth. An agent acting on a merely-possible
classification used to be indistinguishable from one acting on a certain one,
because a rule matching `is_gothic(?c)` matched whatever grade the entry carried
— nothing could read a grade, so nothing could decline.

Now declining is one line, and *what this corpus is willing to act on* is a
claim with a trail.

## Weakest link, as structure

Two uncertain premises give `likely(possible(c(t)))`.

Where `min` over two ordinals gave one number and forgot which premise was weak,
the nest records **both, in order**. That's a better answer to the same
requirement.

**What is lost, stated rather than buried.** Weakest link used to be automatic
and total — every write, every rule, nothing authored. Now nothing is concluded
from an uncertain premise unless a corpus deliberately crosses it (Chapter 16),
and what comes back is nested. Collapsing the nest —

```
rule <collapse> = implies( { +likely(possible(?x)) }, { +possible(?x) } )
```

— is a corpus's table, and its ordering is a corpus's claim.

> **The ordinal stops being free and starts being arguable.**

That's the trade, and it is the trade this design makes everywhere else.

!!! note "Deep dive: a deletion that fixed something two sections away"
    Composing a chain of rules into one shortcut (Chapter 27) used to refuse
    anything but a certain conclusion, because composing a grade would have been
    a minimum computed once from defeasible constituents — the very objection
    that ruled out storing a grade on a proposition, arriving one level up.

    With grades gone, the objection went with them, and the restriction was
    **deleted rather than solved**. A limitation nobody was working on
    disappeared because something unrelated was removed.

---

**Next:** if uncertainty is a word in the sentence, how does anything follow
from it?
[Supposing →](16-supposing.md)
