# What comes to mind

Before the machine can choose a rule, something has to hand it a set of rules to
choose from.

That step is called **recall**, and it is the most consequential *policy* in the
design — which is why the fact that it was once listed as a primitive is worth
correcting out loud. Earlier drafts named four primitives: recall, match, write,
arbitrate. Against the actual floor (Chapter 28) they decompose unevenly:

| earlier primitive | verdict |
|---|---|
| **match** | floor |
| **write** | floor — a register to write into, a stamp on the result |
| **arbitrate** | *totality* is floor. *Precedence* is a claim in the graph. |
| **recall** | **entirely convention.** An index plus a policy. |

One of the four was never a primitive at all. Calling it one obscured that it is
a **choice**.

## Index, then prefer, then learn

That's the build order, and each stage is cheap before the next is worth
anything.

> **Index, then prefer, then learn.** An index makes the candidate set small and
> costs nothing in correctness. A preference orders what's left. Learning tunes
> the preference.

The index is over **what a rule concludes**. Its effect, measured on one corpus:
**751 ticks down to 57**. That's not a subtle optimisation; that's most of the
work being avoided.

And it gives one earlier decision a natural home rather than a special case: a
rule whose consequent is a bare variable has no bucket, so it's never proposed
to the backward reader (Chapter 11). The vacuous reading declines itself.

## Recall returns a set *and a state*

> **Recall returns a set plus a state, never a set.**

Because recall is **incomplete by design**. It may fail to surface a rule that
would have helped. That's an acceptable cost only if the failure is
distinguishable from the other kind:

> **Nothing came to mind is not nothing is left to do.**

A shortlist that ran dry must **widen** — look harder, consider more. A search
that finished must escalate outward. They look identical from the outside, and
conflating them is how a reasoner starts claiming things it hasn't earned.

There is one thing recall may not be incomplete about, and it's stated as a
carve-out because it's a safety property:

> **Recall may be incomplete about what to do. It may not be incomplete about
> what you must not do.**

Prohibitions come off the recall path entirely and are checked at the write.
Chapter 18.

## A preference is a score, and doubt is a tie

Preferences are **scores**, summed. Which has a nice consequence: because
several preference rules can each contribute, preference is natively an
**ensemble** rather than a single ranking.

> **Two rules are close when their scores differ by no more than the tolerance.**
> Confidence is a gap.

And two rules that don't help you choose — because the apparatus has already
decided — cost nothing to rank.

Which is the measurement that most changed how this design thinks about
learning:

> **Experience has almost nothing to decide, because the apparatus wins most of
> the agent's choices — and permuting a dependency chain cannot shorten it.**

Most of what the loop does is forced. Read the goal, recall, fit, expand, check.
There's no freedom there to be clever about. What learning can touch is the
narrow band where two genuinely different options are available, and that band
is smaller than it looks from outside.

## Two things must order, and never exclude

Two hard rules about preference, both of which were violated first and then
fixed:

**A preference must order, not exclude.** A preference that removes an option
has silently become a prohibition, and it's the wrong kind — unattributed, and
checked in the wrong place.

**A preference may never outrank the apparatus.** *This is relevant to my goal*
is one signal among several, and as a **filter** it is silent about everything
it is not about. Something being irrelevant to the current goal is not a reason
it can't matter.

## What trains it, and the trap

Recall learns from outcomes — which rules, having been proposed, actually helped.

And there's a failure mode with a name:

> **Training recall on its own accepted outputs narrows it monotonically.**

A rule that never gets proposed never gets a chance to be useful, so it never
earns a better score, so it never gets proposed. The shortlist contracts
towards whatever it happened to like first, and nothing in the loop can notice.

Which is why *widen when dry* is not politeness. It is the only thing keeping
the distribution honest.

!!! note "Deep dive: where the cost actually was"
    This project spent a while assuming recall was where the time went. It was
    not. Measured: the **read** was 86% of runtime on the fixture that mattered,
    and the fix was 67×. Recall was a rounding error next to it.

    > Measure before optimising. The named lever was 6% of the cost.

    And the second measurement, which is the one that reordered the roadmap:
    **an ideal recall table saves nothing while the loop runs to quiescence.**
    Narrowing changes the order and nothing else, until there is a reason to
    stop.

    So: stopping first, then recall, then learning. Not the order anyone
    proposed.

## Callbacks are directed recall

An **occasion** is a fact the machinery deposits when something notable happens:
`quiet`, `blocked`, `left`, `defeated`, `bounded`, `unsupported`.

A corpus keys on one, and that's the first thing a corpus can say to recall:
*when this happens, think of me*.

> **A callback is directed recall, not invocation.** The woken rule still has to
> match, can still lose, and can still be defeated.

That distinction is the whole reason this is safe. A callback that *invoked*
would be control flow that owns the loop, which Chapter 24 spent its length
arguing against.

And a request can be **re-asked**, with a rule to govern when:

> **An occasion warrants a re-ask only if re-asking cannot produce one.**

Otherwise you have built a loop. Chapter 7 has the two-line demonstration.

---

**Next:** the agent writing its own rules.
[Learning →](27-learning.md)
