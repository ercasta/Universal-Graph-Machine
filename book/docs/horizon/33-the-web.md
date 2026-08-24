# Meaning is a web

Here is a claim that sounds abstract and turns out to be measurable.

> **You never implement the meaning of `owning` or `selling`.** You coin the
> proposition, and the meaning arrives later — as rules, written by someone
> else, without touching what is already there.

A conventional program cannot defer that. `sell()` needs a body before it does
anything; that body is one meaning, chosen once, by one author; and a second
reading of the same event is a change to the first.

Here meaning is **inferential rather than denotational**. `owns(hero, sword)`
denotes nothing and means whatever follows from it. So the same proposition
can carry several unrelated meanings at once — a trade rule, a theft rule and
an encumbrance rule may each read it, none knowing the others exist.

That's why a whole new trade in Chapter 8 was five facts and zero rules.

## What the engine reserves

If the engine had a world model hiding in it, this claim would be quietly
false. So: count. `python -m ugm.gates.vocabulary` classifies every reserved
name once, by what it's *for*:

| what the reserved names serve | how many |
|---|---|
| literals (numerals) | 10 |
| the surface — the connective, the three modes | 5 |
| belief itself — `believed`, `erased` | 2 |
| rules as data | 6 |
| **the agent's own deliberation** | **35** |
| the seam where a world reaches it — `arrived`, `says`, `answered` | 4 |
| **about any world** | **0** |
| **total** | **62** |

**Not one reserved name is a domain word.** There's no engine name for a
thing, a place, an amount of anything, or an act of any particular kind.
`says` is about the *act*, never about what was said.

And what a corpus borrows, with one control designed to make the
classification falsifiable — run for real against the shipped corpora:

| corpus | about | its own | borrowed |
|---|---|---|---|
| passenger rights when a flight is disrupted | a world | 13 | **0** |
| the design's worked examples | a world | 8 | 1 (`says`) |
| **the bundle itself** | **the agent** | **0** | **2** |

The last row borrows everything because it's the one corpus that's *about the
agent's own reasoning*. That's the result, not an exception — and it's why the
check is signed by what a corpus is about: a world-corpus that borrowed more
than it invented, or an agent-corpus that had to invent its own vocabulary,
would each fail the gate. A table where every row could only agree is not
evidence.

## The price is the same property

Because a proposition needs no implementation, **the engine cannot
distinguish one awaiting its meaning from a mistake.** Both are well formed,
both are inert, and nothing says which is which.

That's not hypothetical. The gate plants exactly this typo — `watns` for
`wants` — in a rule that trades a sword, and reports it:

```
a planted typo (watns/wants)   1 unwebbed  ['wants']
```

It loads without complaint, derives nothing, and says nothing on its own. A
conventional language front-loads that error into a compile failure. This
back-loads it into a report at load time: a name a rule *reads* and nothing
anywhere *writes*. The three real corpora above — passenger rights, the
design's worked examples, the bundle itself — all report zero, which is the
check's own control working: an instrument that always fires is worth
nothing, and one that never fires on a planted fault is worse.

## …and the same property is what detects it

**Meaning is the web, so a name with no web is a mistake.** That follows from
the paragraph above rather than being a heuristic about spelling: if a
proposition means what follows from it, then a name nothing ever draws a
conclusion from, or nothing ever establishes, means nothing.

Chapter 8 has the load-time version of this measurement in a smaller corpus,
worked by hand. Here it's the general instrument, run against everything this
repository ships.

## What this chapter used to measure, and no longer can

An earlier version of this engine kept a full derivation trail — every belief
stamped with which rule produced it and what that rule consumed — and this
chapter used to build a second web on top of that trail: entries as nodes,
`rests_on` as edges, connectivity components as "islands," the terms whose
removal disconnects the web as "bridges." It was a real measurement, on a
real corpus, and it agreed with a prediction made before the numbers came
back.

That machinery is gone. Belief is now presence — `believed(p)` holds or it
doesn't — and there is, on purpose, no provenance trail attached to a belief
to build a token-level web out of (Chapter 34 has the honest accounting of
what that costs). The **type-level** web above — relation names joined by the
rules that read them — survives, because it never depended on the trail: it's
read off the rules themselves, statically, before anything runs. The
**token-level** web — which particular claim rested on which — does not
survive, and nothing in this repository currently recomputes an equivalent.

The same is true of the standing philosophical objection to inferential
meaning, Prior's `tonk` — a connective that lets anything be derived from
anything, which a purely structural web-of-relations check cannot catch
(both `tonk`'s introduction and elimination rules are perfectly ordinary
`implies` rules; nothing about their *shape* is wrong). Belnap's answer,
**conservative extension** — does adding this rule license new conclusions in
the *old* vocabulary? — is still the right test in principle. What measured it
here was a gate that mutated a rulebase and reran the suite, and that gate is
one of the instruments this rewrite did not keep. The argument stands; the
measurement of it, for now, does not, and a claim with no measurement behind
it is marked as one rather than asserted as fact.

## Where this sits in the literature

Almost none of it is new, and the pieces come from at least four places.

- **The web itself is Quine's** — *Two Dogmas of Empiricism* (1951), and *The
  Web of Belief* (Quine and Ullian, 1970). One honest difference: Quine's
  structure is a **revisability gradient** — periphery and core — where what's
  measured here is a static graph of *which relations a rule connects*.
- **Meaning as inferential role** is Wittgenstein's *meaning is use*, Sellars
  on material inference, and Brandom's inferentialism (*Making It Explicit*,
  1994).
- **`tonk` and its answer**: Prior, *The Runabout Inference-Ticket* (1960);
  Belnap, *Tonk, Plonk and Plink* (1962); Dummett on harmony.
- **Conservative extension** is the standard formal criterion for ontology
  **modularity** in description logics — Lutz, Walther and Wolter; module
  extraction by Cuenca Grau, Horrocks, Kazakov and Sattler.

So what, if anything, is not already known? Stated conservatively: nothing in
the *concepts*. What may be uncommon is a system where the reserved
vocabulary is small enough — 62 names, zero of them about any world — to
audit by hand and to check by machine, on every commit, against corpora that
actually run. That itself is a hypothesis, not a result, and stays one until
someone who works in this literature says otherwise.

---

**Next:** the honest list.
[What is not built →](34-not-built.md)
