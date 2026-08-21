# Supposing

*Suppose it rains on Monday.* Then the streets are wet, the match is off, and
none of that is something you believe — it is something that **follows from an
assumption you are holding at arm's length**.

Any reasoner that plans has to do this. The question is what it costs, and this
chapter is the one place in the book where the answer changed after the fact:
the machine had a supposition mechanism, it worked, and it was **removed**. What
is here now is what the removal left, why it happened, and what a corpus does
instead — which turns out to be less machinery and one more ordinary claim.

## What was built

Supposing forked the chain. Entering a hypothesis opened a **frame** whose seat
was a successor moment; conclusions drawn inside it were deposited there, and
the design's rule for modality was:

> **Unwrap on the way in. Re-wrap on the way out.**

Assume `likely(rain(monday))` and you enter with `rain(monday)` plain — inside
the hypothesis it simply holds — and whatever you conclude comes back out
wrapped: `likely(wet(streets))`.

Containment was **free rather than enforced**. Nothing forbade a hypothetical
claim from reaching the real world; the read simply could not see it, because
resolving a proposition meant walking back from where you stood, and the
hypothesis was down a branch that walk never took. Chapter 5 tells that story
from the other side.

## Why it is gone

The fork went with the locus, and for the same reason: it made every read ask
questions it now has no need to ask. *Is this entry on my branch?* was one of
two ancestry tests inside a read that measured at 86% of runtime. With the locus
removed there is one chain, one order, and one rule — **later supersedes
earlier** — and there is no branch for a hypothesis to live down.

So `suppose(...)` is now an ordinary atom that nothing in the engine consumes.
Write it and it deposits, like any other fact, and no frame opens.

The honest scorecard:

| | with the fork | now |
|---|---|---|
| entering a hypothesis | machinery: a frame, a seat, a re-wrap on the way out | a corpus's own claim |
| containment of **conclusions** | free — the walk could not reach them | the corpus's, by keeping them wrapped |
| the read | two ancestry tests | one lookup |
| **what a rule concluded under an assumption** | discoverable by leaving the frame | whatever relation the corpus wrote it in |

## What a corpus does instead

Hold the hypothesis in the **proposition**. The wrapper is the containment:

```
rule <wet>   = implies( { +rain(?d) }, { +wet(streets) } )
rule <carry> = implies( { +given(?h, rain(?d)) }, { +given(?h, wet(streets)) } )

fact +given(h1, rain(monday))
```

```
given(h1, rain(monday))   -> +
given(h1, wet(streets))   -> +     the consequence, under h1
rain(monday)              -> None  nothing is believed outright
wet(streets)              -> None  and <wet> never fired
```

`<wet>` is the ordinary rule about the world and it does not fire, because
nothing asserts `rain(monday)` — only `given(h1, ...)` does. That is the whole
of the containment, and it is visible in the corpus rather than in the engine.

What it costs is honest and stated: **you write the hypothetical version of the
rules you want to reason with**, where the frame used to give you every rule for
free. `<carry>` above is `<wet>` again, one level in. For a corpus that
supposes about a narrow question that is a line; for one that wants to reason
hypothetically about everything, it is the whole rule set twice, and that is the
capability that was given up.

## The lessons that outlived the mechanism

These were learned while the fork existed and none of them depended on it.

**Supposing must not change what the agent believes.** That was the whole point
of containment, and it is now a property of how you write the rules rather than
one the engine can guarantee. If a hypothetical rule concludes something
unwrapped, it *is* believed — nothing will stop it.

> **The engine's guarantee became a corpus's property.** That is the same trade
> the norms decision made in Chapter 18, and the same one Chapter 28 makes for
> stopping. It is only acceptable when the property is stated out loud, which
> is what this paragraph is for.

**Containing what is *said* is not containing what is *derived*.** The old
mechanism contained entries and never contained **structure** — a stratum-0
rule concludes into the graph itself, where there is no branch and no sign, so
structure derived inside a hypothesis stayed derived after it. The modern form
of the same trap: a rule that concludes structure from `given(?h, ...)` is
concluding it *outright*, because structure has no wrapper to carry the
hypothesis.

**A leak with no licence cannot be found by asking why.** Anything that arrives
in the world without a trail is invisible to `why`, so the fix has to be at the
place the thing is written, never a check afterwards.

**Crossing a modality is a decision, not a mechanism.** *It is likely to rain*
does not license reasoning as though it rains — some rule has to say so, and
which one is a corpus's business (Chapter 15). The old mechanism made crossing
cheap enough to be tempting; the current one makes the decision explicit,
because you must write the rule that carries the wrapper.

> **The first branch is free and every branch after it is exponential.**

That was the argument for making crossing deliberate rather than automatic, and
it is unchanged: reasoning under two independent assumptions at once is four
worlds, and nothing about the representation makes that cheaper.

---

**Next:** two rules that disagree, and what settles it.
[When two rules disagree →](17-disagreement.md)
