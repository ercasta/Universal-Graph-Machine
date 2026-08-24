# What is not built

Every book about a system should have this chapter, and most don't.

The useful thing here is not the list but the **classification**. "Unsayable"
covers four quite different situations, and confusing them wastes time in
both directions — arguing with a wall that's really a to-do, or designing
around a to-do as if it were a wall.

> **Ask which of these four kinds you're hitting before you design around
> it.** And if the answer isn't obvious, that is itself the signal.

## The four kinds

**1. Deliberate, and load-bearing.** Changing it would be wrong.

**2. Deliberate, and a real cost.** Changing it would be wrong; the cost is
still real, and you should know what it is.

**3. Simply not built.** Nothing in the design resists it; it's
implementation order.

**4. Never a wall at all.** It looked unsayable because three separate
things declined it and nobody asked which one was the reason.

That fourth category is the one worth taking seriously. Two items from this
project's own history changed status in a single afternoon, purely because
somebody asked *why* instead of accepting the list.

- **`$p($x)` — a class named by data.** Looked like a wall. It was three
  independent refusals — the parser wouldn't read a variable in relation
  position, the unifier compared the relation slot by identity, and
  substitution wouldn't rebuild one — and the substrate had been able to
  construct the node all along. About an hour to allow. It's now the
  pattern `authoring.md` §4 recommends you build on: `+$kind($item)` lets
  *the smith sells weapons* be a fact rather than a rule per weapon.
- **`unless`.** Described in three separate documents as the only unbuilt
  row. It was a *name* for a negated antecedent member, available since
  there were antecedent members: `{+wounded($x), no poisoned($x)}` already
  says it. Zero lines of engine were written to close it.

> If you hit something and it smells like a wall, say so loudly rather than
> routing around it.

## Deliberate, and load-bearing

**Silence means *unchanged*, never *false*.** Open-world semantics.
`no poisoned($x)` holds only when nothing — no `+poisoned($x)` anywhere —
is on record; `+not(poisoned($x))` is a separate, ordinary claim a corpus can
assert and a rule can read, and asserting it does not by itself make
`no poisoned($x)` fail for anyone but the one individual it was written
about. The cost is real: a state block that lists only what's true won't
drive a rule that asks what isn't, and the fix is always to write the
negative, not to hope absence gets inferred. The alternative — treating a
proposition nobody has mentioned as false by default — is worse, because it
can never be told apart from *not yet considered*.

**A statement's variables are scoped to it.** `fact unless(<regen>,
poisoned($x))` parses and does *nothing*: that `$x` is a different variable
from the one in `<regen>`'s own antecedent. A guard belongs inside the rule
it guards, not beside it. This is what makes a rule a self-contained claim
rather than something a second file can quietly amend.

**Precedence doesn't carve out per-entity exceptions.** `overrides(<a>,
<b>)` defeats `<b>` for the whole tick if `<a>` matched *anywhere*, not just
for the entity `<a>` bound. Poisoning one character while another is merely
wounded, with `overrides(<poison>, <regen>)`, stops the second character
from healing too. The exception belongs inside the rule, as a negated
member — that's what `unless`, above, is for. `overrides` is still the right
tool when the exceptions genuinely aren't enumerable in advance.

**Arbitration is scheduling, not a verdict.** The table always answers
something — that's a floor guarantee — but a rule that loses a tick is
*deferred*, never rejected: a run to quiescence applies it eventually unless
something forgoes or forbids it outright. There is no way to ask the engine
to decide a rule is wrong; only a corpus can say that, in a rule of its own.

## Deliberate, and a real cost

**A belief carries no record of how it was reached.** It's worth being
honest about the size of this: belief here is presence — `believed(p)` holds
or it doesn't — and that presence carries no sign, no licence, no chain back
to what produced it. The cost is concrete: nothing in this engine can
currently answer *why do you believe this*, for any belief, of any kind.
What you get instead is what's believed *now*, newest-first, and — at load
time — a report of every name a rule reads that nothing anywhere writes,
which catches a large fraction of the corpus bugs a trail would have
explained. It does not catch all of them, and there is no programmatic
substitute for "walk me back from this conclusion to the facts it rests on."
Chapter 9's "shows its work" is that report plus what's currently believed,
not a kept derivation.

**No connective carries persistence-through-time.** `implies` is the only
connective, and its consequent lands now, with no built-in way for a
conclusion to persist once its antecedent stops holding (*water you stopped
heating stays boiled*, say). The cost: a corpus that wants
persistence-through-time has to write time as an ordinary relation of its
own and reason over it explicitly — nothing reserved does that for you.

**Only the static, type-level web is measured.** Which relations a rule's
antecedent and consequent connect is computed straight off the rules, with
nothing run, and is what Chapter 33 measures. The dynamic, per-run
version — which particular claim rested on which, at runtime — is not:
nothing here recomputes dead rules, isolated relations or connected
components against a live derivation.

## Genuinely absent

These are real gaps against the engine as it stands today — cross-checked
against `docs/feature-requests.md`, and re-verified rather than copied.

**A wildcard absence member.** `no p(*)` does not lex — `*` is simply not a
token the grammar accepts anywhere. This blocks episode-scoring triggers
(*did anything at all go wrong this episode?*), and it's been raised
independently at least three times across this project's history. It's the
highest-value item on this list precisely because nothing else on it is
blocked by a single missing token.

**`_` is not a wildcard.** It reads as an ordinary name, like any other atom
— so two members that both write `_` in an argument position are quietly
forced to agree on the *same* thing, which is the opposite of what a wildcard
promises. Writing `_` where you mean *don't care* currently traps silently
rather than refusing at load, which is worse than either working correctly or
erroring loudly.

**Scored alternatives inside one antecedent.** `alt(...)` gives you a union of
branches that each independently satisfy one antecedent — useful, and built —
but there's no way to say *these several branches all satisfy this rule, rank
them, and take the best*. Each branch is equally good as far as the engine is
concerned.

**A global, no-host-rule trigger.** Every trigger today hangs off a named
rule (`fact +intercepts(<hold>, after)`). A trigger with no rule to hang off,
evaluated every tick and installable or cancellable at runtime by a
postcondition, doesn't exist.

**Cross-agent time reference.** An agent can currently say *this happened*,
but it has no name for *when*, that a second agent's own rules could compare
against their own timeline. *You attacked before I did*, agreed between two
agents rather than asserted by one about itself, has no route through the
channel mechanism today.

**Calibration policy for attention weights.** The table's scoring mechanism —
a per-rule score, a window, a tolerance around it — is built and runs every
tick. What's missing is a corpus-side policy that reads back a reward signal
and revises the scoring: credit assignment is left entirely to the corpus
author's own arbitration rules, not learned.

**No vocabulary for incompatibility.** You can assert a proposition's denial
(`+not(p($x))`). You cannot say that two *distinct* propositions can't both
hold — there's no relation meaning *these two are mutually exclusive*, only
whatever a corpus's own rules manage to enforce case by case.

**Teaching another agent a rule, not just a fact.** A fact may not contain a
variable, and a rule's antecedent and consequent are generic by construction
— so an agent can utter *the door is locked* to another agent, and currently
cannot utter *locked doors need keys*. Whether that's deliberate, following
from the same restriction that keeps a rule's variables scoped to itself, or
simply unbuilt, is genuinely unclear.

**Magnitude of cost for a rule's failure.** Whether something went wrong is,
where a corpus tracks it at all, a yes/no fact today. A corpus that wants to
weigh *how badly* has to build that scale itself; nothing reserved carries a
notion of degree here.

## Open design questions

These aren't gaps so much as places where two answers are both defensible
and no corpus here has forced a decision yet.

**Goal "discharge" as a first-class notion.** Achieved, refused, handed to
someone else, abandoned — a goal currently just stops being pursued or
doesn't; there's no vocabulary distinguishing *why* it stopped.

**Multi-episode learning.** Whatever a corpus can learn from experience, it
learns from one episode at a time; nothing here carries a lesson from one run
into the next except through what the corpus author writes down by hand.

**Exploration versus exploitation.** When should an agent stop trying what
worked last time and try something new? No shipped corpus answers this, and
the engine has no opinion.

**Backtracking.** Who decides to reconsider a binding already made, and on
what signal, is unresolved — every shipped example either commits or
restarts, never partially reconsiders.

**Statically checking that nothing bypasses the gate.** `Gate.write` is
still the one door a belief enters or leaves through, by construction — but
that it's the *only* door is true by placement in the code, not by anything
that checks it.

**Loop detection.** A rule whose own consequent restores its own antecedent
can run forever, caught only by `bounded(ticks)` after the fact. Detecting
the pattern ahead of time is deliberately left unbuilt, for want of a
second, different failing example to check a detector against. A detector
nobody can falsify is not a detector; it's a guess with a green checkmark on
it.

## Two standing rules

Two things this project holds itself to, which are worth carrying away
regardless of whether you ever use this machine.

> **No feature is novel until something falsifies the claim.** Nearly
> everything here has a literature. What's claimed is the assembly and the
> discipline, and both stay hypotheses.

> **A claim with no measurement behind it is an opinion, and it should be
> marked as one.**

---

That's the book.

If you want to see the machine actually run, the playground pages run the
real engine in your browser: [run a corpus](../playground/corpus.md), or
[make it check itself](../playground/selftest.md).

And `docs/feature-requests.md`, in the repository, is this chapter's own
source material — ideas raised along the way that never got built, kept
there rather than lost, not a roadmap.
