# Stretches, not instants

Some claims aren't about a moment at all.

*They are taking turns* isn't true of any instant. Its subject is a **stretch**.
So is *it rained throughout*, and so is any constraint on the order in which
things happen.

This chapter is about how that gets said — and it is the one chapter in the
book where the answer changed after the fact. The design built a mechanism for
it, ran it, and then **removed it**, and the removal is more instructive than
the mechanism was.

## What was built: a stretch as a *place*

An entry used to carry a **locus** — where the claim sits. Normally a moment.
The idea was to let it be a stretch instead:

```
<s> = span(<M7>, <M12>)                       start and end
<e> = entry(<s>, taking_turns(anna, bo), +)   an entry located at the stretch
```

Spans were **loci**, and nothing else about the entry changed. It worked. It is
gone anyway, and the reason is the whole lesson: the *locus* itself is gone.
Dating every claim to a place turned out to cost more than it bought — a second
index to maintain, a second question at every read (*at this moment, or at that
one?*), and an ancestry test on every resolution. What replaced it is one
sentence: **later supersedes earlier**, and nothing is dated to anything.

So a stretch stopped being a place a claim could sit.

## What says it now: an ordinary relation

The claim is deposited like every other claim, and the corpus carries the
stretch itself — two moments, in a relation it names:

```
rule <round> = implies(
  { asking(?q), anc(?q, ?m), in_delta(?m, ?e),
    entry_of(?e, turn(hero, ?r), plus) },
  { round_span(?r, ?m, ?q) } )

rule <heard> = implies(
  { round_span(?r, ?a, ?b), anc(?b, ?m), anc(?m, ?a),
    in_delta(?m, ?e), entry_of(?e, arrived(?c, ?what, ?sign), plus) },
  { heard(?r, ?c) } )

rule <silent> = implies( { round_span(?r, ?a, ?b), -heard(?r, player) },
                         { silent(?r, player) } )
```

`round_span(?r, ?a, ?b)` is not engine vocabulary — it is a relation this
corpus invented, holding two moments. Everything else is the chain read as
ordinary structure:

- **`anc(?a, ?b)`** — `?b` is an ancestor of `?a`; `sanc` is the strict version.
- **`in_delta(?m, ?e)`** — entry `?e` was deposited in moment `?m`.
- **`entry_of(?e, p, plus)`** — what `?e` actually claims.

Read together, those three are *walk the history between two moments and look
at what was deposited there* — which is what a span-located entry was for, done
by a rule instead of by the read.

And note what `<silent>` gets for free: **a stretch has duration whether or not
anything happened in it.** The old mechanism minted a span only when the chain
moved, so silence was unrepresentable — there was no span for nothing to have
happened in. A stretch a corpus carries has no such gap.

## What stays true about representing a stretch

The representation questions the span work settled did not go away with it, and
the answers are the same for a corpus's own stretch relation.

**Endpoints, never contents.** The moments a stretch *contains* are not listed
anywhere, and need not be: **the predecessor relation is single-valued**, so the
walk back from the end is unique, and if the start lies on it the contents are
fully determined by the chain.

| | endpoints only | enumerate the moments | a description of the stretch |
|---|---|---|---|
| not leaking | contents derived from the chain, so they can't disagree with it | two answers to *what is in this stretch* | fine |
| not lossy | fine | records the extent, not why those | fine |
| readable | fixed 2-ary | an extent claim wearing positional clothes; arity varies with duration | — |
| composable | interval relations compare two pairs of endpoints | comparing stretches means comparing lists | comparing descriptions isn't expressible |

**Participants stay out.** `anna` and `bo` are members of the *proposition*,
never of the stretch. That is what lets one stretch host several unrelated
recognitions — *they took turns* and *it rained throughout* — over the same two
moments.

**Disjunction stays out.** *On Monday and on Wednesday* is two stretches plus a
fact relating them, never one stretch with a hole in it. A stretch with holes
would smuggle disjunction into a shape nothing can consume.

## What was lost, stated plainly

The old mechanism could answer one question that nothing answers now:

> *They took turns over M7..M12* — is that so at M14?

Inheritance **within a kind of locus** was the rule: a moment asking about a
stretch-located claim got a yes once the stretch was over; a stretch asking
about a moment-located claim got nothing, because *it rained at M9* is not *it
rained throughout*. That asymmetry was carefully argued and is simply not
expressible now — with no locus, there is no *at M14* to ask from. What the
chain gives instead is that a revision **adds**: what the agent used to think is
still findable, in deposit order.

The honest summary is that a capability was traded for a much simpler read, and
the trade is visible rather than hidden. That is the same shape as Chapter 15's
trade in the other direction: **the free answer becomes the arguable one.**

## Where the wall actually was

This is worth keeping because it is a good story about estimating, and it is
still true of the code it was about.

The design listed three costs for spans: normalising direction, the quadratic
population, and an ancestry check. Those were an afternoon between them.

What actually stood between the page and a running example was **three lines
that read a locus and ignored it**, none of which appeared anywhere in the spans
design, because each was correct exactly while every locus was a moment:

| where | what it did |
|---|---|
| the **write** | a consequent's locus was parsed, checked and reified — and the gate stamped the frame's topic anyway |
| **quiescence** | asked whether the conclusion already held at the frame's *topic*, so a second recognition of one proposition was *nothing to do*, however different the stretch |
| the **resolved state's key** | one entry per proposition — which is an assumption about **loci**, not about propositions |

The first two are the same defect twice, and fixing only the write bought
nothing: the loop never reached the write, because the verdict was computed
about a different locus than the one the conclusion would land at.

That third one is worth stating as a rule, and it is exactly why the locus was
eventually removed rather than extended. One entry per proposition is right
exactly while every two loci are **comparable** — on a chain of moments one is
always at or before the other, so the later governs. Two stretches are not
comparable. Making them loci meant keying the state by the proposition *and*
the thing it was about, and that key is the cost that never came back down.

> **A feature's cost is rarely in the feature. It is in the assumptions the
> rest of the system made while the feature did not exist.**

---

**Next:** claims with no fixed length at all.
[Shapes →](20-shapes.md)
