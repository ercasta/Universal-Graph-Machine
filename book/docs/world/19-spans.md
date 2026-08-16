# Stretches, not instants

Some claims aren't about a moment at all.

*They are taking turns* isn't true of any instant. Its subject is a **stretch**.
So is *it rained throughout*, and so is any constraint on the order in which
things happen.

A **span** is a node with exactly two members: a start moment and an end moment.

```
<s> = span(<M7>, <M12>)                       position 0 = start, 1 = end
<e> = entry(<s>, taking_turns(anna, bo), +)   the locus of this entry is the span
```

Spans are **loci**. Nothing else about the entry changes — which is the point.
An entry's locus is a moment *or a span*, and nothing in the read had to grow to
accommodate the second.

## Writing one

```
rule <a> = causes( { +ready(anna) }, { +acts(anna), -ready(anna), +ready(bo) } )
rule <b> = causes( { +ready(bo) },   { +acts(bo), -ready(bo) } )

rule <turns> = implies( { +acts(?p) at ?mp, +acts(?q) at ?mq, sanc(?mq, ?mp),
                          span_of(?s, ?mp, ?mq) },
                        { +took_turns(?p, ?q) at ?s } )

fact +ready(anna)
```

```
why took_turns(anna,bo)?
  +took_turns(anna, bo) @S1..2, licensed by applied(<turns>)
    because +acts(anna) @M1, licensed by applied(<a>)
    because +acts(bo) @M2, licensed by applied(<b>)
```

`@S1..2` — the claim's locus is the stretch from M1 to M2, not either endpoint.

Three pieces of notation are doing the work:

- **`at ?mp`** binds the locus of a matched entry.
- **`sanc(?mq, ?mp)`** is a skeleton member: `?mq` strictly follows `?mp`.
- **`span_of(?s, ?start, ?end)`** mints the stretch, and read the other way
  round it decomposes a bound span into its two members.

And the consequent's **`at ?s`** is what makes a span a locus in fact: a rule
concludes at a locus its antecedent bound. No new notation — `at` was already in
the surface on both sides of a rule.

## Membership is not stored

The moments an anchored span *contains* are not listed anywhere.

The reason is structural: **the predecessor relation is single-valued.** A
moment has one parent; forking produces several successors, never several
parents. So the walk back from M12 is unique, and if M7 lies on it, the span's
contents are fully determined by the chain.

| | endpoints only | enumerate the moments | a description of the stretch |
|---|---|---|---|
| not leaking | contents derived from the chain, so they can't disagree with it | two answers to *what is in this span* | fine |
| not lossy | fine | records the extent, not why those | fine |
| readable | fixed 2-ary | an extent claim wearing positional clothes; arity varies with duration | — |
| composable | interval relations compare two pairs of endpoints | comparing spans means comparing lists | comparing descriptions isn't expressible |

Two things also stay out of a span:

**Participants.** `anna` and `bo` are members of the *proposition*, never of the
span. That's what lets one span host several unrelated recognitions — *they took
turns* and *it rained throughout* — over the same stretch.

**Disjunction.** *On Monday and on Wednesday* is two spans plus a fact relating
them, never one span with a hole in it. A span with holes would smuggle
disjunction into a shape nothing can consume.

## Inheritance is within a kind of locus

This is the subtle rule, and it has to be got right or a claim quietly becomes
stronger than anyone said.

| | reads | |
|---|---|---|
| a **moment** asking about a **span**-located claim | *they took turns over M7..M12; is that so at M14?* | **yes**, once the stretch is over |
| a **span** asking about a **moment**-located claim | *it rained at M9; did it rain throughout M7..M12?* | **no** |
| a **span** asking about another **span** | *it held over M7..M12; over M9..M11?* | not read — that's an interval relation, and a corpus's to conclude |

The middle row is the load-bearing one:

| | a moment's claim inherits into a span | it does not |
|---|---|---|
| not leaking | answers *did it hold throughout* from an entry saying only *it held then* — and since the read returns one winner rather than scanning, **a denial in the middle of the stretch is invisible** | nothing is inherited that nobody claimed |
| not lossy | — | *it held at the start, so it held throughout* is a rule a corpus writes, and then it's dated, attributed and deniable |
| readable | *sometimes true* is the hardest kind of rule to state | one sentence |

Inheriting would be free and wrong only sometimes, which is the worst
combination this design knows. So it doesn't, and the arguable version is
written by whoever wants it.

That's the same trade Chapter 15 made in the other direction: **the free ordinal
becomes the arguable one.**

## Where the wall actually was

This is worth telling because it's a good story about estimating.

The design listed three costs for spans: normalising direction, the quadratic
population, and an ancestry check. Those were an afternoon between them.

What actually stood between the page and a running example was **three lines
that read a locus and ignored it**, none of which appears anywhere in the spans
section, because each was correct exactly while every locus was a moment:

| where | what it did |
|---|---|
| the **write** | a consequent's `at ?m` was parsed, checked and reified — and the gate stamped the frame's topic anyway |
| **quiescence** | asked whether the conclusion already held at the frame's *topic*, so a second recognition of one proposition was *nothing to do*, however different the stretch |
| the **resolved state's key** | one entry per proposition — which is an assumption about **loci**, not about propositions |

The first two are the same defect twice, and fixing only the write bought
nothing: the loop never reached the write, because the verdict was computed
about a different locus than the one the conclusion would land at.

That third one is worth stating as a rule. One entry per proposition is right
exactly while every two loci are **comparable** — on a chain of moments one is
always at or before the other, so the later governs. Two spans are not
comparable. So a claim is superseded only by a claim it is comparable *with*,
and the state is keyed by the proposition **and the span it is about**.

## The costs, as checks rather than cautions

- Spans are **directional**, so equality has to be normalised by chain order.
  Settled by interning on the ordered pair: `span(M7, M12)` is one node however
  many recognisers reach it, and the inverted pair is not a span at all.
- Any two moments form a span, so the population is quadratic. Spans are
  therefore **minted by recognisers, never enumerated** — `span_of` finds
  nothing when neither the span nor both endpoints are bound.
- A span whose start isn't an ancestor of its end is meaningless, so the check
  belongs at the **minting site**, where it's cheap and the mistake is still
  attributable. A **degenerate** span is refused with it: `span(M7, M7)` is a
  second name for a moment, and two ways to say one locus is exactly the
  ambiguity the read can't afford.

---

**Next:** claims with no fixed length at all.
[Shapes →](20-shapes.md)
