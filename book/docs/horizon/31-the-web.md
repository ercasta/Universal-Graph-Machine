# Meaning is a web

Here is a claim that sounds abstract and turns out to be measurable.

> **You never implement the meaning of `owning` or `selling`.** You coin the
> proposition, and the meaning arrives later — as rules, written by someone else,
> without touching what is already there.

A conventional program cannot defer that. `sell()` needs a body before it does
anything; that body is one meaning, chosen once, by one author; and a second
reading of the same event is a change to the first.

Here meaning is **inferential rather than denotational**. `owns(hero, sword)`
denotes nothing and means whatever follows from it. So the same proposition can
carry several unrelated meanings at once — a trade rule, a theft rule and an
encumbrance rule may each read it, none knowing the others exist.

That's why a whole new trade in Chapter 8 was 5 facts and 0 rules.

## What the engine reserves

If the engine had a world model hiding in it, this claim would be quietly false.
So: count.

| what the reserved names serve | how many |
|---|---|
| literals (numerals) | 10 |
| the surface — connectives, signs, `at` | 7 |
| the chain — moments, entries, signs, spans | 10 |
| rules as data | 14 |
| **the agent's own deliberation** | **48** |
| the seam where a world reaches it — `arrived`, `says`, `did`, `forbidden` | 12 |
| **about any world** | **0** |

**Not one reserved name is a domain word.** There's no engine name for a thing,
a place, an amount of anything, or an act of any particular kind. `did` and
`says` are about the *act*, never about what was done or said.

And what a corpus borrows, with one control designed to make the classification
falsifiable:

| corpus | about | its own | borrowed |
|---|---|---|---|
| a D&D fight | a world | 23 | 5 |
| passenger rights when a flight is disrupted | a world | 13 | **1** |
| the design's worked examples | a world | 8 | 4 |
| **the shipped rulebase** | **the agent** | **0** | **25** |

The last row borrows everything because it's the one corpus that's *about the
agent's own reasoning*. That's the result, not an exception — and it's why the
check is signed by what a corpus is about. A table where every row agrees is not
evidence.

## The price is the same property

Because a proposition needs no implementation, **the engine cannot distinguish
one awaiting its meaning from a mistake.** Both are well formed, both are inert,
and nothing says which is which.

That's not hypothetical. It's most of the traps this project has recorded:

| | |
|---|---|
| a typo — `watns` for `wants` | loads without complaint, derives nothing, says nothing |
| `pred` | was the reflexive walk under the immediate one's name — *a name whose meaning is not what the name says is worse than an absent one* |
| `plus` / `minus` | reserved, and a foreign corpus found out **silently** — now reported at load |
| `unless(<R>, +C)` written as a fact | parses, is read by nothing, and survived in **three documents** as an open item |

A conventional language front-loads that error into a compile failure. This
back-loads it into silence. For a session-sized agent that's the right trade, and
it is exactly the wrong one at Cyc's scale.

## …and the same property is what detects it

**Meaning is the web, so a name with no web is a mistake.** That follows from the
paragraph above rather than being a heuristic about spelling: if a proposition
means what follows from it, then a name nothing ever draws a conclusion from, or
nothing ever establishes, means nothing.

Chapter 8 has the measurement. Only one of the two directions is a signal, and
that had to be measured to find out which.

## Two webs, and they answer different questions

| | nodes | edges | says |
|---|---|---|---|
| **type level** | relation **names** (14 in the passenger corpus) | rules | what *could* connect |
| **token level** | **entries** (25) | `rests_on` (23) | what *did* connect |

The first is terminology joined by rules, and it's blind to arguments:
`owns(smith, sword)` grounds `owns` for every rule reading `owns(?a, ?b)`.

The second is the **trail** — ground, argument-exact, per-run. It long predates
this analysis, because explaining a conclusion needs it. Of those 25 entries, 14
rest on nothing: they're the facts and arrivals, the boundary where a world
enters.

## The shape is islands joined by bridges

Predicted before it was measured, and then measured:

| | relations | links | density | islands |
|---|---|---|---|---|
| passenger rights | 13 | 13 | 0.167 | [13] |
| the design's worked examples | 8 | 7 | 0.250 | **[4, 4]** |
| two domains + the shipped rulebase | 43 | 37 | **0.041** | [1,2,2,3,3,4,5,10,13] |

The worked-examples file reporting **two** islands is the measure being right
about something known independently: that file is a kettle and some rain, two
unrelated examples.

And the bridging terms — those whose removal splits the web — divide as
predicted: each domain's own hubs (`disrupted`, `owed`, `amount`; `likely`)
alongside the agent's **common** vocabulary (`says`, `did`, `goal`, `subgoal`,
`verdict`).

> **A domain's special terminology clusters. The shared terminology is what holds
> the clusters together.**

## Four ways meaning fails, and one of them isn't a failure

| | what's wrong | caught by |
|---|---|---|
| **an unwebbed name** | the term is unknown | nothing writes it |
| **a dead rule** | its premise can never be established | a reachability fixpoint |
| **an isolated relation** | joined only to itself | connectivity |
| **an utterance with no path** | both terms known and richly connected, and **nothing relates them at any distance** | a path query over the web |

The first three are static defects in a corpus. **The fourth is not a defect at
all** — it's the shape of *"I ate, so tomorrow will rain."*

Both terms are meaningful. The sentence is well formed. What's absent is any
path between the eating island and the weather island. Measured: with the
sentence asserted as a rule the web is one island of 8; without it, [4, 4].

> **The honest response is not *I did not understand*, but *I have nothing that
> connects eating and rain*** — a report about the agent, never about the world.

A healthy knowledge base that simply hasn't learned some real connection says
exactly the same thing, and should.

**And that's why it isn't a censor.** The natural reply — *what does eating have
to do with rain?* — asks for the missing link. If the speaker supplies it, the
agent has acquired a **bridge** between two islands, which is what Chapter 27's
adoption is for.

> **Failing to understand and learning are the same event seen from two sides.**

And a lone bridge is also exactly what a genuine discovery looks like.

## tonk, and what the surface refuses by accident

The standing philosophical objection to inferential meaning is Prior's `tonk`: a
connective with the introduction rule *A ⊢ A tonk B* and the elimination rule
*A tonk B ⊢ B*, which lets anything be derived from anything. If a word's
meaning is just its inferential role, `tonk` has a meaning, and that's absurd.

Two things here are worth recording.

**The surface already refuses tonk-introduction**, for an unrelated reason:

```
rule <tonk-in> = implies( { +?a }, { +tonk(?a, ?b) } )
   REFUSED — concludes about a variable its antecedent never binds
```

That refusal exists so the write never deposits a generic proposition.
*Conclude something arbitrary* turns out to be unsayable — a harmony constraint
arriving through the side door.

**But a bound variable smuggles it back in.** With `{+holds(?a), +claim(?b)} ⟹
{+tonk(?a, ?b)}` and `{+tonk(?a, ?b)} ⟹ {+?b}`, the agent concludes
`slippery(moon)` and `bankrupt(alice)` from nothing but someone having uttered
them — and every structural check above reports **0 problems**, because they all
hunt for too *little* meaning and tonk has too much.

What catches it is Belnap's own criterion, **conservative extension**, and it
discriminates cleanly:

| adding | new conclusions in the **old** vocabulary |
|---|---|
| tonk | **2** — `bankrupt(alice)`, `slippery(moon)` |
| an ordinary rule (`slippery ⟹ careful`) | **0** |

So: no, tonk is not detectable by the shape of the web. And yes, by a dynamic
test this implementation is already tooled for, since the rulebase gate does
exactly this mutation-and-rerun.

## Where this sits in the literature

Almost none of it is new, and the pieces come from at least six places.

- **The web itself is Quine's** — *Two Dogmas of Empiricism* (1951), and *The Web
  of Belief* (Quine and Ullian, 1970). One honest difference: Quine's structure
  is a **revisability gradient** — periphery and core — where what's measured
  here is **connectivity components**. Islands are not a periphery.
- **Meaning as inferential role** is Wittgenstein's *meaning is use*, Sellars on
  material inference, and Brandom's inferentialism (*Making It Explicit*, 1994).
  *"I ate, so tomorrow will rain"* asserts a **material inference**, which is
  exactly the unit Brandom makes primary.
- **tonk and its answer**: Prior, *The Runabout Inference-Ticket* (1960);
  Belnap, *Tonk, Plonk and Plink* (1962); Dummett on harmony.
- **Conservative extension** is the standard formal criterion for ontology
  **modularity** in description logics — Lutz, Walther and Wolter; module
  extraction by Cuenca Grau, Horrocks, Kazakov and Sattler. So *islands* and
  *conservativeness* aren't two separate ideas; they're **one known research
  programme**, and this work arrived at both ends of it empirically.
- **Semantic distance and no-path** is spreading activation — Collins and
  Quillian (1969), Collins and Loftus (1975). **Relevance theory** (Sperber and
  Wilson, 1986) is arguably the closest match to what the path test measures.
- **The repair has a name, and it's nearly the same word.** Clark's *bridging*
  (1975) is the inference a hearer must supply to connect new material to given
  material — and Clark's own description is that bridging *results in the
  addition of one or more propositions to memory*. That is adoption, described in
  1975.
- **Dead rules** are reachability analysis. **The token web** is a justification
  network — Doyle's TMS (1979), de Kleer's ATMS. **Islands** are Cyc's
  **microtheories**, which Lenat partitioned by hand for the reason measured
  here.

So what, if anything, is not already known? Stated conservatively:

1. Nothing in the *concepts*.
2. What may be uncommon is the **assembly**: one running system in which the
   type-level web is computed statically, the token-level web is the provenance
   trail the same engine already keeps for explanation, and the static web is
   then used **at run time** to judge an incoming utterance — with the failure
   and the learning opportunity being the same event.
3. And one measurement about this artifact rather than about the world: **101
   reserved names and not one of them about any world**, against a corpus that
   needed to borrow one.

Points 2 and 3 are **hypotheses, not results**. Neither has been checked against
the modularity literature by anyone who works in it, and the right disposition is
the one this project takes everywhere else: it stays a hypothesis until someone
who would know says otherwise.

---

**Next:** the honest list.
[What is not built →](32-not-built.md)
