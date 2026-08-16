# What is not built

Every book about a system should have this chapter, and most don't.

The useful thing here is not the list but the **classification**. "Unsayable"
covers four quite different situations, and confusing them wastes time in both
directions — arguing with a wall that's really a to-do, or designing around a
to-do as if it were a wall.

> **Ask which of these four kinds you're hitting before you design around it.**
> And if the answer isn't obvious, that is itself the signal.

## The four kinds

**1. Deliberate, and load-bearing.** Changing it would be wrong.

**2. Deliberate, and a real cost.** Changing it would be wrong; the cost is
still real, and you should know what it is.

**3. Simply not built.** Nothing in the design resists it; it's implementation
order.

**4. Never a wall at all.** It looked unsayable because three separate things
declined it and nobody asked which one was the reason.

That fourth category is the one worth taking seriously. **Two items on this
project's open list changed status in a single afternoon**, purely because
somebody asked *why* instead of accepting the list.

- **`?p(?x)` — a class named by data.** Listed as a wall. It was three
  independent refusals — the parser wouldn't read it, the unifier compared the
  relation slot by identity, and substitution wouldn't rebuild one — and the
  substrate had been able to construct the node all along. About an hour to
  allow. It is now the pattern Chapter 8 recommends you build on.
- **"It falls by 3."** Listed as unsayable. It was **two questions filed as
  one**. A known amount is arithmetic, arithmetic is a function, and a function
  is a tool. An unknown amount wants a **node** rather than a value slot — which
  is the plurality move sitting one section away from the item that said it was
  missing.
- **`unless`.** Described in three documents as the only unbuilt row. It was a
  *name* for a negated antecedent member, available since there were members.
  Zero lines of engine were written to close it.

> If you hit something and it smells like a wall, say so loudly rather than
> routing around it.

## Deliberate, and load-bearing

**Silence means *unchanged*, never *false*.** Open-world semantics. Chapter 3.
The cost is real — your rules get longer, and a missing denial fails silently —
and the alternative is worse.

**A statement's variables are scoped to it.** Which means you cannot assemble a
rulebook out of facts, and a guard written beside a rule doesn't bind the rule's
variables. Chapter 10. Both of those are the feature, not the bug: it's what
makes a rule a self-contained claim.

**Ordinary rules may not amend other rules.** *Add a guard to a rule you didn't
write and cannot edit* is refused **by decision**, not missing by omission. An
ordinary rule may not reach into another rule's application, and amending a rule
belongs to acquisition: the agent authors a better rule through adoption, so the
amendment is itself a claim you can date, attribute and argue with.

**Contradiction is permitted and undetected.** Consistency is a question you ask,
not an invariant the substrate maintains. Chapter 2.

## Deliberate, and a real cost

**You cannot ask *why did you read it that way*.** Promoting the read into the
ordinary stratum reinstates the bootstrap circle. Chapter 31.

**You cannot ask *why did you consider that rule*.** Recall is a function, not a
search. Which is why nothing load-bearing for safety may depend on it —
Chapter 18.

**Composition across `causes` is refused.** Measured to lose conclusions.
Chapter 29.

## Genuinely absent

**No vocabulary for incompatibility.** You can deny a proposition. You cannot
say that two propositions **cannot both hold**. That's a real gap, noticed when
an older engine's `refutes` had nothing to port to.

**Calibration currently costs conclusions.** The table's attention-spending
mechanism is built (Chapter 28); the learning process that is supposed to
calibrate it is not working. Gated against the uncalibrated table: on one corpus
the teacher agreed with the table's own order **21 of 21** times, so there was
nothing to teach and every lesson made it worse; on the other there was plenty to
teach and the lessons still lost up to **213** conclusions. Chapter 29 has both
rows and why they have to be read together.

**Two agents can never refer to the same time.** Every moment renders as
`moment()`, so a moment cannot cross a wire even if a parser accepted it.
*The goblin acts after the hero* is writable within one agent; *you attacked
before I did* has no route at all. A moment would need a renderable,
re-readable name.

**No agent can teach another a rule.** It falls out of *a fact may not contain a
variable*, so it is presumably deliberate — but it means a DM can say *the door
is locked* and can never say *locked doors need keys*. Whether that's a position
or an accident is genuinely undecided.

**Every clarification request about a rule is decided on and never emitted.** A
rule node is generic by construction, and an intent with an unbound member is
refused — so *ask the author about the rule that lost* can be concluded and can
never leave the agent. The entry already carries the information needed to tell
use from mention at the boundary, and nothing reads it. Chapter 14.

**An arrival should be a moment, and isn't.** A report is a signed delta, so
trust ought to be a rule relating two moments rather than a rule per sign. The
current shape puts a sign inside a proposition, which is a compromise with a
visible cost. Chapter 21.

**A rule cannot ask *would this be forbidden?*** Deciding whether a stored
generic pattern covers a particular proposition is matching, and matching is
floor. So the norm gate does it in the machinery. Chapter 18.

**Silence about an unnamed channel.** *Nothing was said* over a **named** channel
is sayable — it's *nothing arrived on this channel over this stretch*, and
Chapter 19's spans are what make it bounded and checkable. Over an **open**
domain of channels it is not, because a corpus relation cannot be structural.

**A `?` conclusion crossing out of a supposition** has no defined form. `+` and
`−` both become terms under the wrapper; `?` is a statement about *reading* and
cannot.

## Open design questions

These aren't gaps. They're places where two answers are both defensible and the
measurement hasn't been done.

**Should an ordinary rule read the skeleton?** Partly resolved — `rests_on` is
readable now — but the general question of how much of the machine's own
construction should be visible to its rules is large and open.

**Should the compiled path be derived from the rules rather than written by
hand?** With frequency and surprise deciding what gets compiled. Sketched,
unbuilt.

**Where should a learned model sit?** Chapter 22 argues *where there is no
algorithm*, and names the two places. Nothing is built.

**What should be rehearsed?** Practice generates a goal from every achievable
relation the corpus names (Chapter 29), which is affordable for one corpus and is
not a policy. The shape of the answer already exists — a claim that gates what is
even considered — and joining the two is untried.

**Buffs are supplied from the host language.** The surface for a postcondition —
`after { … } => boost(<R>, n)` — is deliberately left open until the loop has
been watched running for longer. Until it closes, the one part of the table that
is *not* data is the part learning is supposed to write.

**Loop detection.** Designed, measured, and deliberately not built — because the
corpora available could not measure a detector for it, and a detector nobody can
falsify reports thousands of false positives. The census ships so the deferral
stays revisitable: the day the last column isn't zero is the day it can be
gated.

## Two standing rules

Two things this project holds itself to, which are worth carrying away
regardless of whether you ever use this machine.

> **No feature is novel until something falsifies the claim.** Nearly everything
> here has a literature. What's claimed is the assembly and the discipline, and
> both stay hypotheses.

> **A claim with no measurement behind it is an opinion, and it should be marked
> as one.**

Several paragraphs in this book exist because a probe disagreed with prose that
had already been written up as a finding. That's the failure mode to watch for,
and the only defence is to run the check before writing the sentence.

---

That's the book.

If you want to see the machine actually run, the playground pages run the real
engine in your browser: [run a corpus](../playground/corpus.md), or
[make it check itself](../playground/selftest.md).

And the design document — `docs/rules-design.md` in the repository — is the full
argument, with every decision scored in a table before it's taken.
