# Learning

Everything up to here takes the rule set as given. A corpus is authored, the
bundle ships, and the agent's cleverness is entirely in what it does with what
it was handed.

This chapter is the other half, and it's Part 2's claim taken seriously:

> **A rule is a node. So a rule can be the conclusion of a rule.**

Nothing new is needed for the agent to author one, and everything already true
of rules is true of what it authors.

## Three ways a rule gets made

### Composition — collapsing a derivation

Having derived `e` from `a` by way of `b`, `c` and `d`, mint the rule `a → e`
and use it directly next time.

Measured, over a chain of length *n*:

| n | uncomposed | composed |
|---|---|---|
| 2 | 2 | **1** |
| 4 | 4 | **1** |
| 8 | 8 | **1** |
| 16 | 16 | **1** |

*n* steps become one, for any *n*, with the same conclusion.

This is easily confused with compilation, and the two behave oppositely:

| | **compilation** | **composition** |
|---|---|---|
| produces | a host-language artifact | **a rule — an ordinary node** |
| reduces | the cost of one step | **the number of steps** |
| the gain | a constant factor | algorithmic |
| inspectable | no | yes |
| interruptible | at rule boundaries | it *is* a rule boundary |
| defeasible | no | yes |
| lives | outside the graph | in the graph |

> **Compilation makes a step cheaper. Composition makes the step unnecessary.**

A composed rule violates nothing: it's data, askable, attributable, defeasible
like any other rule, and it carries a licence naming the rules it collapses — so
the trail is recoverable one hop deeper rather than lost.

**Two things it must inherit, and both do.** Anything that overrides a
constituent overrides the composition — without that, a shortcut escapes a
defeat that bound its parts. And a **guard** is inherited by construction:
composition takes the union of the antecedents, and a guard is an ordinary
negated member, so it comes along without a mechanism.

**And composing across `causes` is refused.** A chain of `implies` collapses
soundly because every step is read in one moment. A `causes` deposits into a
*successor*, so the second rule's other premises are read a moment later than
the first rule's — and flattening them into one antecedent demands them all at
once. Measured, that loses conclusions. So it's refused.

What composition costs is epistemic rather than structural: intermediate
conclusions stop being deposited, so **nothing can be surprised inside a
shortcut**.

### Adoption — a rule concludes a rule

```
adopt(<R>)
```

**A door, not a question.** It belongs with entering a supposition and
dispatching an intent, rather than with the answerers. What decides that a rule
is worth having is a corpus concluding `adopt(?r)`; what happens then is not a
judgement, and there's no verdict for a rule to reach.

Two constraints, both found by building:

**Refused inside a supposition, and that is containment.** A frame's conclusions
are unreadable from outside by construction — but the rule set is one list
shared by every frame. A rule adopted while supposing would apply after the
frame is discharged, and to everything. **Supposing would change what the agent
believes**, which is the one thing supposing must not do.

(And the refusal is written *inside* the frame, so asking the root whether it
holds answers nothing however well it worked. Containment caught the check
before the check caught anything.)

**The adopted rule must be the node the graph describes.** Minting a fresh one
makes the live rule a **twin** of the described one: everything a corpus said
about the described rule goes to a node that is not a rule, and everything the
machinery says about the live one names a node no corpus can reach.

This is the **twin trap**, and it has been found seven separate times in this
project's history:

> **Anything that binds a name has to go through the table that resolves it.**

It was found here only when a standing policy tried to order a learned rule and
quietly did nothing.

### Learning from examples — anti-unification

Given two things that happened, what pattern do they already agree about?

That's the **dual of unification**, and it completes a family:

| operation | asks | answers with |
|---|---|---|
| **match** | does this pattern fit that thing? | a substitution |
| **unification** | can these two patterns be made the same? | a substitution over both |
| **anti-unification** | what do these two things already agree about? | **a pattern** |

The thing that makes it learning rather than noise is small and absolute:

> **One mapping across premise and conclusion.**

Generalise the premise and the conclusion with *separate* dictionaries and you
get a rule whose conclusion mentions things its premise never bound — which is
either vacuous or wrong. One dictionary across both is the difference.

Two riders. What the two examples **agree** about is kept — otherwise the result
isn't the *least* general generalisation. And the tool **declines** when they
share no structure at all, rather than returning something vacuous.

## Why the composer has to be a tool

A corpus cannot write a new rule's insides. Three separate refusals say so, each
clean rather than silent:

- a `fact` may not contain a variable at all, so a corpus cannot write a rule's
  patterns;
- a statement's variables are scoped to it, so parts written on separate lines
  could not share a `?x` even if it could;
- a rule's consequent may carry only variables its antecedent binds — and a rule
  being *built* has no antecedent yet.

So the corpus never names the new rule's insides. It reaches them by
**binding** — *reference is binding*, arriving where it is load-bearing.

Composing a rule is a function, and a request answered by a function is a
**tool** (Chapter 22). Learning from examples shares the same seam, for the same
reason.

## What a learned rule may conclude

This turned out to need nothing new.

A learned rule concludes **wrapped**: `likely(p)` rather than `p`.

> **A learned rule that concludes wrapped cannot fight what the agent was told.**

Which means acquisition's normal conflict — a rule the agent invented
contradicting a rule it was given — needs **no new precedence at all**.
`likely(p)` and `−p` are not rivals; they're different claims, and a corpus that
wants to act on the first has to cross it deliberately (Chapter 16).

## The agent harmonizes itself

Once rules can be authored, rules about rules become useful — and the first
fixture that made all of this meet broke in **two** places at once, neither
visible from inside any of the four pieces built separately.

> **Two conventions that have never met are two conventions that have not been
> tested.**

That's not a maxim. It's the measured behaviour of this design's own
construction, and it's why the acceptance gates run against a moving target
rather than a fixture.

What broke:

- **A concluded precedence was never read.** A rule said something and the
  machinery ignored it — the recurring defect, seen from the far side.
- **The adopted rule was a twin of the described one.** The eighth instance.

And one thing worked that shouldn't have been obvious: **a precedence claim
about a rule that did not exist when the claim was written**. That's what
`reference is binding` and *precedence is read, not kept* buy together.

## Retiring is not defeating

One last distinction, and it's the humane one:

> **Losing an argument is not being wrong.**

A rule that is right about a thousand cases and loses to a more specific one in
five is not a bad rule. Retiring it on `defeated` throws away every case it was
right about.

What ships is the **occasion** — `defeated(<loser>, <winner>)` — and what to do
about a rule that keeps losing is a corpus's decision: ask its author, raise a
precedence, mark it dormant.

And before adding any new relation for this sort of thing, there's a check worth
running first:

> **Before adding a relation, check whether the one you want is a count over the
> trail.**

Usually it is.

---

That's Part 6. Parts 7 and 8 are the last two, and they go underneath.

**Next:** the five things that genuinely could not be taught.
[What cannot be a convention →](../floor/28-the-floor.md)
