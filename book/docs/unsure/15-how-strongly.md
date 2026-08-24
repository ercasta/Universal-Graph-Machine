# How strongly

*Rain is likely this afternoon.*

Where does the *likely* go?

The obvious answer is: on the claim, as a number or a grade. It isn't. Uncertainty
here is a **word in the sentence** — a wrapping proposition — never a score attached
to a fact.

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
machinery that decides which rule is even in the running (Chapter 17).

**Confidence is a property of the source, not of the rule.** *How sure am I of
this rule*, *how sure am I of this sensor*, and *how far do I trust this
speaker* are one question asked of three sources — and every entry already names
the source it arrived through. A confidence slot on rules would cover the first
case only, and would have to be reinvented for the other two.

## Why not a grade on the fact

Attaching a number or an ordinal to a proposition — *rain is likely* as
`rain(...) @0.6` — looks like the obvious shortcut, and it fails on structure,
not on taste.

*Not on the proposition node*, because that's a cache of a derived value: the
claim holds only given the support that produced it, so when the support
changes the cache has to be invalidated — general invalidation over a web of
dependencies is a truth-maintenance system, a second machine with its own
consistency problem running underneath the first.

*Not as a separate tag beside the fact*, because a tag is a separate read: you
could obtain the fact without the tag, and an untagged conclusion reads as
certain when it may not be.

*A number also can't be reasoned with the way a proposition can*: nothing can
ask *is this merely likely* about a number, there's no guard for a rule to
cross before acting on it, and it doesn't nest (`thinks(anna, likely(rain))`
has nowhere for a bare grade to sit).

Grading a claim with `@` is refused at load with a message pointing here —
write `+likely(p)` in the consequent instead. There is no closed, fixed set of
modality words either: whatever names a corpus writes (`likely`, `possible`,
`doubtful`, ...) and whatever order it wants among them is the corpus's own
claim, not the engine's.

## What replaces it

Modality is a **proposition**. `likely(p)` is a wrapping node — the same
construction as `on(a, b)`, with one arm rather than two.

```
rule <weather> = implies( { +cloudy($d, morning) },
                          { +likely(rain($d, afternoon)) } )
```

Three things this buys that a grade cannot, none of them arguments:

| | grade on the entry | term |
|---|---|---|
| a **rule** can ask *is this merely likely* | no — a grade is not a term | yes |
| the **guard holds** — nothing acts on the unwrapped claim | no; a grade annotates a conclusion the actor still sees | yes, structurally |
| it **nests** — `thinks(anna, likely(rain))` | no | yes |

The second row is the one with teeth. A rule matching `is_gothic($c)` matches
the plain claim, however it's qualified elsewhere — a rule that must not act on
a merely-possible classification has to say so, by matching `likely(...)`
directly rather than the bare proposition. Declining is one line, and *what
this corpus is willing to act on* is a claim with a trail.

## Weakest link, as structure

Two uncertain premises give `likely(possible(c(t)))` — the nest records both
qualifiers, in order, rather than collapsing them into one number that forgets
which premise was weak.

Nothing is concluded from an uncertain premise unless a corpus deliberately
crosses it (Chapter 16), and what comes back is nested. Collapsing the nest —

```
rule <collapse> = implies( { +likely(possible($x)) }, { +possible($x) } )
```

— is a corpus's table, and its ordering is a corpus's claim.

> **The ordinal stops being free and starts being arguable.**

That's the trade this design makes everywhere else, too.

---

**Next:** if uncertainty is a word in the sentence, how does anything follow
from it?
[Supposing →](16-supposing.md)
