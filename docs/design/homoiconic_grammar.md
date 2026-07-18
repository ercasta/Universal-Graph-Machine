# Homoiconic grammar — the intake grammar as CNL data, interpreted by rules

> **Status: SPIKE RUN, GREEN (2026-07-18) — `bench/spike_homoiconic_grammar.py`.** All four §5
> questions answered; the §3 crux answered POSITIVELY and in-engine. Results in §8 below; the
> arc is buildable. Original proposal text (§1-§7) kept verbatim — it was written before the
> spike and the spike did not contradict it.
>
> User proposal, arrived at from the
> book-corpus evidence: *"express the grammar in CNL and have rules that process the grammar to
> intake sentences in that grammar, instead of hardcoding forms."*
>
> Evidence base: `bench/spike_loudon.py` + `bench/loudon_lion_corpus.py` (50 verbatim sentences of
> Mrs. Loudon's *Entertaining Naturalist*). Companion: `learning_design.md` (the arc this
> unblocks), `../vision.md` §10 (what was rejected, and why this is not that),
> `surface_interpretation.md` (the substrate split §11 produced).

## 0. THE DESIGN AS IT NOW STANDS (read this first)

Four spikes produced this; §§8-11 are their narrative results, in order, and should be read as
evidence rather than as the spec. The system they describe:

**Everything is declared in CNL and generates rules; no Python is edited to add a shape.**

    lion is a noun                                          -- LEXICON (shipped `X is a Y` surface)
    np expands to determiner plus np                        -- PRODUCTION (binary / unary = CNF)
    slot head in np from determiner plus np is right head   -- how a parent's slot is filled
    mint head in np from modifier plus np under right head  -- ... or is a FRESH described entity
    clause asserts subj pred obj unless neg                 -- which slots become a fact
    clause denies  subj pred obj when   neg                 -- ... and which become a negative one

**A span is a relation, not a node.** `a --span_np--> b` runs from the span's first token to the
token just past its last (a `<eos>` sentinel gives the last token a successor), so composition is a
plain two-premise join. The chart is what "every enabled rule fires, nothing selects" builds —
**token-passing IS chart parsing**, which is why the ambiguity crux (§3) dissolved.

**Ambiguity is detected, never resolved.** A top-down USEFULNESS pass marks the spans a complete
parse actually uses (a chart also holds dead constituents), and a `Distinct` on the split point
flags a useful span built two ways. No parse → REFUSE. Two parses → ASK. One parse → fold.

**Identity is minted only for what survives.** The chart stays packed while parsing; span NODES are
minted only for useful spans (O(n), not the chart), which is what gives slots somewhere to hang
without paying for an unpacked forest (measured: 4.7 s at 11 tokens).

**A modified NP denotes a fresh NAMELESS entity described by its parts** (`<e> is_a lion`,
`<e> is guzerat`) — decomposition fully intact, only the carrying node changes; nameless per the
`ByDesc` identity law. This is what stops one `lion` node carrying both `has mane` and
`has_not mane`.

**Denotation is defeasible.** The parse is the permanent record; every judgement about what it MEANS
(coreference, denotation, subkind-vs-same-entity) lives in a discardable scope of copies, so a
contradiction defeats the READING rather than corrupting the KB. Full design:
**`surface_interpretation.md`**.

    tokenize -> chart -> useful+ambiguity -> [REFUSE | ASK] -> mint spans
             -> interpret (entities, coreference) -> slots -> assert -> contradiction

**Status (2026-07-18): STEP 1 OF INTEGRATION DONE.** The machinery is in `ugm/cnl/grammar.py` +
`ugm/interpretation.py`, the grammar itself is `corpus/lion_grammar.cnl`, and the behaviours are
pinned by `tests/test_grammar.py` (22 tests; suite 705 green). The benches keep only the
MEASUREMENTS that decided design questions, and import the modules — the two spikes whose entire
content had moved were deleted. **No existing path changed**: nothing calls the grammar yet.

Remaining integration, in order: (2) wire it as an OPT-IN intake route (a KB that declares a
grammar gets the grammar path; everything else keeps the shipped forms — the declare-before-use
discipline, so the suite stays green by construction); (3) run the real corpora, Loudon's 50
sentences first; (4) optimize (§9.6); (5) retire what it subsumes.

**Coverage is still measured on 7 hand-picked sentences chosen to exercise known gaps, NOT on the
50-sentence corpus that motivated the arc.** Step 3 is the honest instrument, and it needs
`<contradiction>` derivation, which `consistency_design.md` still sketches rather than builds
(`interpretation.contradiction_bank` is a local stand-in).

## 1. Half of it already exists, and is proven

The project ALREADY does "grammar as CNL data → rules generated from it", for **word classes**:

```
X is a relation     X is a determiner     X is a variable     X is an auxiliary
```

`forms.surface_forms` and `authoring.relation_forms` GENERATE recognition rules from those
declarations at runtime (`declared_*` unions the user's declarations with the default closed-class
sets). This is not hypothetical — measured 2026-07-18:

```
"the lion lives in africa"                       -> ('lives','is','lion'), ('lives','in','africa')   GARBAGE
"lives_in is a relation" + "the lion lives_in africa" -> ('lion','lives_in','africa')                CORRECT
```

A declaration fixed a mis-parse with no code change.

**What is hardcoded is COMPOSITION** — how constituents combine. `FORM_RULES` / `FACT_FORMS`
enumerate specific surface shapes, so a sentence outside them either fails (`the lion roars` —
intransitive, only two slots) or is absorbed by a neighbouring pattern and folds to nonsense.

So the proposal is not a rewrite. It extends an established, working gradient from CLASSES to
COMPOSITION — and it is the same homoiconic move the project keeps making (ISA programs as data,
`form KEY :` as data, rules-as-graph-data in the learning arc). It introduces no new KIND of thing.

## 2. This is not the rejected PCFG (but it inherits the crux)

Vision §10 rejected the PCFG **grammar structure** (terminals/non-terminals) and **probability as a
branch selector**, on this ground:

> control is now token-passing, not branch-selection: every enabled rule fires; nothing *selects* a
> branch

A declarative, NON-probabilistic composition grammar is not that. But the reason for the rejection
is exactly the crux below, so the distinction must not be used to wave the problem away.

## 3. THE CRUX — ambiguity, and the no-branch-selection commitment

A real grammar yields multiple parses. The engine's core commitment is that every enabled rule
fires and nothing selects a branch, so **two competing parses would both fire and write
contradictory facts**. Ambiguity demands selection; selection is what was rejected.

**Proposed answer: do not select — REFUSE AND ASK.** Ambiguity becomes a discriminating question
("two readings; which did you mean?"), preserving the no-branch-selection commitment and reusing
the `can_ask` wait-set. This is the FOURTH independent time that shape has fallen out of this work
(k>=2 licensing, the sparse-KB bootstrapping paradox, discrepancy contrast, now parsing), which is
some evidence it is the architecture rather than a coincidence.

This must be settled by the spike, not assumed.

## 4. The strongest argument: the current failure mode is a SILENT MIS-PARSE

`('lives','is','lion')` is the form bank GUESSING instead of REFUSING. The line routed as success
and wrote nonsense — strictly worse than the unrecognized case it replaced.

That is the same defect class as S1 and S1b (`learning_design.md` §9, §9.1), which this session
spent its time eliminating: *quietly does something wrong* rather than *says it does not know*. A
declared grammar can answer "does not conform"; a bank of independent surface patterns structurally
cannot, because there is no notion of the whole sentence being accounted for.

## 5. What the spike must find out (wall-first)

1. **Ambiguity.** Does refuse-and-ask work, or does the graph fill with half-parses? Can "this
   sentence has two readings" even be DETECTED with rules that all fire, or does detection itself
   need a selector?
2. **Cost.** A rule-interpreted grammar per sentence, against the ~12ms/utterance budget. Intake
   normalization alone already cost 7.1 → 11.2 ms.
3. **Coverage on the residual failures**, which are the real target: intransitive (`the lion
   roars`), negation (`has no mane` — the exception-bearing construction), comparative
   (`is smaller than`), prepositional with an undeclared verb.
4. **Does it subsume the existing forms**, or sit alongside them? A grammar that cannot express
   what `FACT_FORMS` already does is a second system, not a replacement.

## 6. Why it matters beyond parsing

- **Exceptions.** Negation is the construction that carries them (§ plan, "partial intake coverage
  is not neutral"). Until it parses, the defeasible-exception work has no data.
- **Form learning (T3).** Learning a form becomes learning a COMPOSITION rather than a whole
  template, which is a far smaller and better-posed induction problem — and the discriminating
  question already exists to disambiguate it.
- **Loudness.** "Does not conform" is a diagnostic the current architecture cannot produce.

## 7. Known tension to resolve

Multi-word noun phrases currently DECOMPOSE by design (`the african lion` → head `lion` +
`lion is african`, never an `african_lion` entity — `forms.py` §2, "structure exposed to reasoning,
not hidden in an opaque string"). Measured consequence on a taxonomy corpus: every subspecies
collapses onto ONE `lion` node, so `lion has mane` (from the Bengal lion) and the Guzerat lion's
manelessness would land on the SAME entity — a contradiction manufactured by the grammar, not by
the source. Whether composition should be able to MINT a distinct entity is a real question the
grammar arc has to answer.

## 8. SPIKE RESULTS (2026-07-18) — `bench/spike_homoiconic_grammar.py`

### 8.0 The mechanism that was tried

A grammar declared in CNL as a LEXICON (`lion is a noun` — the shipped `X is a <class>` surface,
unchanged) plus PRODUCTIONS (`np expands to determiner plus np` — ONE new form pair, binary +
unary). A §8 tool generates recognition rules from those declarations, exactly the established
`relation_forms`/`nary_forms` gradient. The generated rules build a CHART, where a span is a
RELATION named for its category, running from its first token to the token just past its last:

    lexical  `w is a C`             :  w --next--> u                       =>  w --span_C--> u
    unary    `Z expands to X`       :  a --span_X--> b                     =>  a --span_Z--> b
    binary   `Z expands to X plus Y`:  a --span_X--> m, m --span_Y--> b    =>  a --span_Z--> b

A sentence is accepted iff `clause` spans it end to end (a `<eos>` sentinel gives the last token a
successor, so every span is `[begin, end)` and composition is a plain two-premise join with no
adjacency arithmetic). 30 CNL lines generated 152 rules.

**No engine change. Nothing new in the substrate.** It ran on `run_bank` first try.

### 8.1 The headline: token-passing IS chart parsing

The §3 crux assumed ambiguity forces branch selection. It does not, because a CHART is precisely
"every enabled rule fires, nothing selects": the chart holds ALL constituents of ALL parses at
once. The engine's core commitment is not something the grammar has to survive — it is the
control regime chart parsing already wanted. This was the spike's one genuinely load-bearing
finding, and it was cheap to get.

### 8.2 Coverage — every residual Loudon failure parses (§5.3)

| sentence | grammar | shipped bank today |
|---|---|---|
| `the lion has a mane` | parsed | `fact: (lion has mane)` ✓ |
| `the lion roars` (intransitive) | **parsed** | unrecognized |
| `the guzerat lion has no mane` (**the exception-bearing sentence**) | **parsed** | unrecognized, but still writes `lion is guzerat` |
| `the lion lives in africa` (prepositional) | **parsed** | `fact: (lives is lion), (lives in africa)` — GARBAGE |
| `the lion is smaller than the tiger` (comparative) | **parsed** | unrecognized |
| `the lion eats the fish in africa` | parsed (ambiguous, see 8.3) | `(fish is eats), (fish is lion), (fish in africa)` — GARBAGE |
| `glorp the flarn` | **REFUSED** | unrecognized |

The two silent mis-parses pinned in the plan are exactly the two the grammar gets right, and it
REFUSES gibberish rather than folding a neighbouring pattern onto it. §4's argument holds:
"does not conform" is a diagnostic this architecture can produce and the form bank cannot.

### 8.3 The crux, answered: ambiguity is detectable in-engine, with no selector (§5.1)

Three representations were measured on the PP-attachment sentence (3 parses):

1. **Count root spans** — the obvious detector. **FAILS.** `root=1` for the 3-parse sentence,
   because packing is exactly the erasure of derivation identity. Worth recording: this is the
   detector one would reach for first, and it silently reports "unambiguous".
2. **Unpacked forest** (every derivation mints its own `<span>` node with child pointers).
   Ambiguity becomes one `Distinct` rule — two span nodes, same cat/begin/end. **Correct, and
   unaffordable**: 5.2 s at 11 tokens (189 span nodes) against 27 ms packed. The derivation count
   is Catalan; representing it is representing every parse.
3. **Packed chart + a USEFULNESS pass** — the answer. Two generated rule families, both ordinary
   rules: (a) top-down, the root span is useful and a useful span makes the children of every
   production licensing it useful; (b) a USEFUL span of category Z licensed two ways — different
   split (`Distinct` on the midpoint) or different production at the same split — is `ambiguous`.
   **Flags exactly the ambiguous sentence, zero false positives on the other six, and names the
   two ambiguous spans** (the `vp` and the `np` "the fish in africa"). 41 generated rules.

The usefulness pass is what separates real ambiguity from a locally-ambiguous DEAD constituent — a
chart holds constituents no complete parse uses, so detecting ambiguity anywhere in the chart would
cry wolf. Top-down usefulness is the ordinary fix and it is rule-shaped.

**So refuse-and-ask is available at the price of one extra generated pass**, and the §3 answer
stands: do not select, ask. (Fifth independent time that shape has fallen out of this work.)

### 8.4 The lexicon wall, and that refusal survives it (a §5 question that was not asked)

A chart grammar needs every word classified; real prose does not oblige. The default tried: a word
in NO declared closed class also spans as `noun` — ONE rule with a NAC over a declared tag, no
hardcoded stop-list (closed classes are themselves CNL data). Results:

- gibberish is **still refused** (`glorp the flarn` → noun det noun, no `clause`), which was the
  thing at risk — the open default could have destroyed the loudness the whole arc is for;
- undeclared content words parse (`the bramble is smaller than the tiger`, `the lion eats the
  bramble`), each with exactly 1 tree;
- it is **cheaper** (one rule instead of one per lexicon word): 15 ms vs 33 ms mean.

This matters more than it looks: it means the grammar does not need a closed vocabulary to be
loud, so the closed-class function words are the only lexicon a domain must declare.

### 8.5 Cost (§5.2)

Mean per sentence over the 7 cases, unoptimized Python, bank REGENERATED per parse:

    packed, closed lexicon    6.2 ms      packed + ambiguity pass    23.7 ms
    packed, open vocabulary   5.3 ms      unpacked (derivations)     32.1 ms

**Parsing fits the ~12 ms/utterance budget with room to spare**; the ambiguity pass is 2× over it
and is the thing to optimize (it is also skippable when only acceptance is wanted). Scaling in
sentence length (packed, open vocabulary), the number that decides viability:

     5 tok   3.9 ms   14 spans    1 tree
     9 tok   8.4 ms   34 spans    9 trees
    13 tok  15.3 ms   62 spans   90 trees

> These numbers are 5× better than the first measurement, and the reason is worth recording: the
> original run read the lexicon naively and picked up `is_a <mention>` (written on every entity by
> `mark_mentions`), declaring all 36 words members of a bogus `<mention>` category and generating
> 152 chart rules instead of 30. An accidental cross-layer read was ~80% of the runtime. See §9.4.

**Spans grow polynomially while trees explode.** That is the whole argument for the packed
representation in one line, and the reason the answer to ambiguity must be ASK, never enumerate.
Cost is a real but ordinary problem: linear in tokens on this grammar, and the bank is rebuilt
every parse (the `_surface_strata` memo is the obvious fix, worth most of the constant).

### 8.6 What the spike did NOT settle

- **THE FOLD — parse → facts is not built.** The spike measures ACCEPTANCE only, deliberately:
  acceptance is what discriminates "guesses" from "refuses", which was the argument. Subsumption
  of `FACT_FORMS` (§5.4) is therefore *unanswered*, and it is the next slice's real content —
  production-attached semantics is where a second system would show up if there is going to be one.
- **§7's entity-minting tension is now actionable but undecided.** A parse gives `guzerat lion` a
  span of its own, which is exactly the place a distinct entity could be minted. Nothing decided.
- **Ambiguity → discriminating question** is unwired (the `can_ask` wait-set exists; the spike only
  produces the `ambiguous` marker).
- **Grammar authoring loudness** — a bad production declaration currently fails silently as
  "sentence does not parse", which is the same defect class one level up.

### 8.7 Build order this implies

1. **The fold** (production-attached semantics), against `FACT_FORMS` as the subsumption gate.
   — **DONE, see §9.**
2. **Ambiguity → discriminating question**, reusing `can_ask`.
3. **Memoize the generated bank**, then re-measure against the 12 ms budget.
4. Only then: retire the surface-pattern forms it subsumes.

## 9. SLICE 1 — THE FOLD (2026-07-18) — `bench/spike_grammar_fold.py`

### 9.1 The surface: semantics is CNL too

Semantics attached in Python would BE the second system §5.4 asks about, so the fold is declared
in CNL — two more form families and nothing else:

    slot head in np from determiner plus np is right head    -- how a parent's slot is filled
    slot pred in vp from intransitive is only head           -- (unary productions use `only`)
    np     asserts head is   attr                            -- which slots become a FACT
    clause asserts subj pred obj  unless neg
    clause denies  subj pred obj  when   neg                 -- ... and which become a NEGATIVE one

The predicate position is read as a SLOT if it names a declared slot, else as a literal word —
data-driven, not string-sniffing. `when`/`unless` guards are a positive premise / a NAC. The whole
grammar + semantics for the test domain is **68 CNL lines**, generating 206 rules (30 chart, 41
usefulness/ambiguity, 17 mint, 32 slot, 86 assert).

### 9.2 The one architectural move: mint identity only for the parse that survives

Slots need something to hang on, and a packed span is a relation triple with no node a rule can
bind. Minting per DERIVATION is the unpacked forest measured at 4.7 s/11 tokens. The resolution:
**the chart stays packed while parsing; identity is minted only for the spans that survive.** The
usefulness pass built for ambiguity detection already names exactly the spans a complete parse
uses — O(n), not the whole chart — so minting after it is linear-ish, and the slots hang on those
nodes. Parsing and denotation are separated by which spans EXIST as nodes, not by a phase wall.

Pipeline, each stage a bank run to fixpoint (the `normalize_surface` strata shape):

    tokenize -> chart -> useful + ambiguity -> [REFUSE | ASK] -> mint useful spans -> slots -> assert

### 9.3 What it writes

| sentence | grammar | today |
|---|---|---|
| `the lion has a mane` | `(lion has mane)` | `(lion has mane)` — **identical** |
| `the lion roars` | `(lion roars true)` | unrecognized |
| `the guzerat lion has no mane` | **`(lion has_not mane)`**, `(lion is guzerat)` | unrecognized, but writes `(lion is guzerat)` anyway |
| `the lion lives in africa` | `(lion lives true)`, `(lion in africa)` | `(lives is lion)`, `(lives in africa)` |
| `the lion is smaller than the tiger` | `(lion smaller tiger)` | unrecognized |
| `glorp the flarn` | **refused** (1.3 ms — fails fast) | unrecognized |
| `the lion eats the fish in africa` | **ambiguous → ask** | `(fish is eats)`, `(fish is lion)`, `(fish in africa)` |

**The exception-bearing sentence now writes its exception.** That was the whole point of the
re-point: `has_not` is the fact the learner needed and never got, and the reason
`bench/spike_loudon.py` §4 could report an unrefutable over-generalization.

The two silent mis-parses are gone in the two available ways: one becomes a correct fold, the
other becomes a QUESTION. Note the shape of the last row — today's bank produces three facts, all
wrong, from a sentence it cannot actually parse; the grammar declines to write anything and asks
which reading was meant.

### 9.4 Subsumption (§5.4 — the question this slice existed to answer)

**No second system, on the evidence available.** The baseline shape folds to the byte-identical
triple; the shapes today rejects fold sensibly; nothing needed a Python escape hatch. Three
qualifications, all real:

- **Dynamic predicates must be in the lexicon.** The ISA rejects a non-plain RHS predicate
  (`lower_rhs`: "RHS non-plain predicate is a later slice"), so a slot-valued predicate generates
  one rule per lexicon word. That is *exactly* `relation_forms`' existing discipline — declare the
  relation and a form is generated for it — arrived at independently. Consequence worth stating:
  open vocabulary works for ENTITIES but not for PREDICATES, which is the same controlled-CNL
  boundary the project already draws.
- **`comparative.py` was not compared against.** `(lion smaller tiger)` is plausible but the
  shipped comparative surface has its own encoding; subsumption there is UNTESTED.
- **§7's tension is now visible as data, and is unresolved.** The fold writes
  `(lion has_not mane)` and `(lion is guzerat)` — i.e. the Guzerat lion's manelessness lands on the
  SAME `lion` node that carries every other lion's mane, manufacturing the contradiction §7
  predicted. The span for `guzerat lion` now EXISTS as a node, so it is the obvious place to mint a
  distinct entity; nothing was decided.

### 9.5 Two accidental cross-layer reads, in one slice

Both are evidence for the substrate-layering question, and neither was hypothetical:

1. **`is_a <mention>` polluted the lexicon.** `mark_mentions` writes `is_a <mention>` on every
   entity, and the lexicon reader uses the same `is_a` predicate — so every word was declared a
   `<mention>` and got a chart rule. 152 rules instead of 30; ~80% of runtime (§8.5).
2. **A `yes` in a declaration was DELETED.** `authoring._recognize` strips nodes named `yes` as
   ephemeral NAC scaffolding, so the CNL line `clause asserts subj pred yes unless obj` silently
   lost its object and read back as a malformed declaration.

Both are name-keyed global partitions leaking into user data: one shares a PREDICATE (`is_a`)
between engine bookkeeping and domain vocabulary, the other reserves a NAME (`yes`) engine-wide.
Note that neither is a node-visibility failure — a node-level `<stratum>` tag would not have caught
either, because in both cases the node was legitimately shared and it was the *reading rule* that
had no business seeing it.

### 9.6 Cost, and the open items

Full pipeline: **mean 89 ms**, max 173 ms — 7× the budget. This is pure EXECUTION: the banks are
generated once and reused across sentences, so memoizing them buys nothing (an earlier note here
claimed otherwise and was wrong). Profiled per stage on `the guzerat lion has no mane`:

    chart        5.8 ms      slots       81.7 ms   <- the cost
    useful+amb  13.8 ms      assert      30.8 ms
    mint         3.0 ms

The slot stage dominates because all 32 slot rules independently redo the SAME 6-way parent/child
structural join. Materializing the parse tree once — one rule per production writing `?p kidL ?l` /
`?p kidR ?r`, after which every slot rule is a 2-premise lookup — takes the stage from **81.7 ms to
21.7 ms (3.8×)** with 13 extra rules. Measured, not projected.

The `assert` stage's 86 rules are 86 only because a slot-valued predicate must be expanded per
lexicon word (`lower_rhs` rejects a non-plain RHS predicate as "a later slice"). With RHS variable
predicates it is ~6 rules. Worth noting that **the learning arc wants the same primitive**
(`predicates-are-keys`, `learning_design.md`) — two arcs converge on one engine change.

Open, in order:
1. **Materialize the parse tree** (3.8× on the dominant stage, measured) and re-profile.
2. **Ambiguity → discriminating question** (`can_ask`); today the pipeline returns `ambiguous` and
   the driver decides.
3. ~~**§7: mint a distinct entity for a modified NP?**~~ **RESOLVED — see §10.**
4. **Declaration loudness** — a malformed `slot`/`asserts` line still fails silently as "does not
   parse". Same defect class, one level up.
5. **Compare against `comparative.py`** before claiming full subsumption.

## 10. §7 RESOLVED (2026-07-18) — `bench/spike_grammar_subkind.py`

### 10.1 The dichotomy was false

§7 framed it as "decompose onto the head" vs "mint an opaque `african_lion` entity", and the
second was rightly rejected — structure must stay exposed to reasoning, not hidden in a string.
But there is a third option that keeps decomposition **completely intact** and only changes WHICH
NODE carries it: mint a distinct node and write the decomposition as its DESCRIPTION.

    <e> is_a    lion       <- the head, still exposed, now as subsumption
    <e> is      guzerat    <- the modifier, still exposed as an attribute
    <e> has_not mane       <- the exception, on its own entity

Nothing is opaque; "is it a lion?" and "what is guzerat about it?" both still answer. And the node
is **NAMELESS**, per the precedent already set in feedback #15 ("the substrate is supposed to be
nameless" — no fabricated `guzerat_lion` skolem names): its identity is its defining relations,
which is exactly `ByDesc`/`_find_skolem_witness`'s existing identity law. No new concept.

One declaration line carries the whole change, and no other declaration moves:

    -  slot head in np from modifier plus np is right head
    +  mint head in np from modifier plus np under right head

### 10.2 Before and after, on the corpus that produced the problem

    BEFORE (decompose onto head)            AFTER (mint a described subkind)
      lion has     mane                       lion                     has     mane
      lion has_not mane   <- CONTRADICTION    <is guzerat & is_a lion>  has_not mane
      lion is      guzerat                    <is guzerat & is_a lion>  is      guzerat
                                              <is guzerat & is_a lion>  is_a    lion

### 10.3 Why it matters beyond tidiness

The generalization and its counterexample now stand on **different nodes, linked by `is_a`**. So
for the candidate law `?x has mane when ?x is_a lion`, the minted subkind IS a witness of the
body and carries `has_not mane` — a reachable counterexample. Under decomposition there was no
second entity to be a counterexample *at all*: the exception overwrote the generalization on one
node and the learner saw a flat contradiction instead of a defeasible rule. **This is the
structure the defeasible-exception arc has been missing, and it was a grammar problem.**

### 10.4 Cross-sentence identity: interning has to become description-keyed

A nameless node is minted PER FIRING, so two mentions of `the guzerat lion` are two nodes, and
name-keyed `intern_mentions` is structurally blind to them (there is no name to key on). The
counterpart is `intern_described`: group nameless entities by their DEFINING relations only — not
by everything they have since acquired, or two mentions that learned different facts would never
merge — and fold. On the 3-sentence corpus it folds 10 nodes to 1 and the KB reads correctly.

Note *why* it was 10 and not 2: an RHS-only `?e` is VALUE INVENTION, minted fresh on every bank
run, and this pipeline re-runs the banks over the accumulating graph per sentence. So
**description-interning is not a tidy-up, it is required for correctness in an accumulating KB.**
That is a genuine cost of the minting design and the main thing to watch when wiring it into a
real driver (focus-scoped re-running would cut the re-firing, not the requirement).

### 10.5 What is still open here

- **Restrictive vs non-restrictive modification.** `the guzerat lion` restricts a KIND; `the bald
  eagle` may just describe an individual. This slice mints in both cases, which is *weaker* rather
  than wrong (it declines to assert that the entity called `eagle` is bald) — but it does break
  the automatic coreference the old merge gave for free. The existing definiteness machinery
  (`declared_definites` / `is_unique` / `_merge_unique`) is the obvious signal to route on, and is
  already opt-in per domain. UNTESTED.
- **Duplicate defining relations survive folding.** `_fold_node` rewires without deduping, so an
  interned node carries N copies of `is_a lion`. Harmless to the triple view (a set), untidy in
  the graph, and deleting them would be fact deletion (§5) — needs the retraction path, not a
  loader.

> **SUPERSEDED IN PART by §11.** The restrictive/non-restrictive question above assumes the
> reading must be settled at authoring time. It need not be: §11 makes it a defeasible commitment.

## 11. SURFACE / INTERPRETATION — the split (2026-07-18) — `bench/spike_interpretation_scope.py`

> User proposal. §10 left mint-vs-percolate as a per-production DECLARATION, which asks the domain
> author to know the right reading in advance. This removes that requirement.

### 11.1 The proposal

The nodes representing the SENTENCE are never touched — they are the permanent, monotone record of
what was said. Every JUDGEMENT about what it MEANS — which entity a mention denotes, whether two
mentions corefer, whether a modified NP is a subkind — lives in a SCOPE holding COPIES, with
provenance back to the surface. **Inside the scope the merge may be destructive** (one node per
entity: the fast representation, no `same_as` clique, no representative hop), because reversal is
never needed — you discard the scope and re-derive.

That is what makes it affordable. The earlier objection to defeasible coreference was that
reversing an in-place merge is impossible once `_fold_node` has deleted the victim; copying moves
the problem out of existence rather than solving it.

### 11.2 The loop, demonstrated end to end

    surface: 2 sentences parsed ONCE -> 231 nodes (tokens, chains, spans; no entity, no denotation)
      -> interpretation A (percolate):  lion has mane / lion has_not mane / lion is guzerat
      -> <contradiction> about `lion` because `mane`          [derived, paraconsistent marker]
      -> provenance: that entity was interpreted from 2 surface mentions -> a JUDGEMENT is in the
         support, so ASK, do not pick
      -> discard scope: 90 nodes gone, 231/231 surface nodes intact, 0 contradictions
      -> interpretation B (mint): lion has mane / <is guzerat & is_a lion> has_not mane / is guzerat
      -> 0 contradictions, NO RE-PARSE

**The system discovers the reading was wrong instead of being told.** That is the capability §10
could not offer.

### 11.3 Why this is the answer to the substrate-layering question

The earlier proposal was a `<stratum>` attribute on nodes; the objection (§9.5) was that the strata
on offer were ENGINEERING distinctions (control vs fact) while the actual failures were reading
rules over legitimately shared nodes. **Observation vs inference is not an engineering
distinction.** It is epistemic, it is exactly two layers, and it decides membership unambiguously:
what the sentence said never changes, what it means is always revisable. That is a stratification
with a defensible basis.

### 11.4 Two findings that cost bugs

1. **The interpretation is not only the ENTITIES.** Every derived denotation edge — `denotes`, and
   every slot (`head`, `subj`, `pred`, …) — is a judgement too, even though it is written ONTO a
   surface span node. Leaving them behind left spans holding stale heads pointing at deleted
   entities, and the second interpretation silently inherited the first one's decisions. **The line
   between the layers is not "which node it hangs on", it is "structure vs denotation":** the
   surface is tokens, chains, and `cat`/`begin`/`end`, and nothing else.
2. **A scope node has no name to be addressed by.** Marking membership with a rule
   (`Pat(scope_id, "member", "?e")`) silently marked nothing — `Pat` reads its subject as a NAME,
   so it interned a node named `n417`. Defining the scope as the DELTA against a pre-interpretation
   snapshot needs no bookkeeping and cannot miss a node. Addressing a scope from inside a rule
   would need `ByDesc` — the same nameless-identity law §10 relies on.

### 11.5 What this spike did NOT do

- **The scope is materialized, not copy-on-write.** Fine for one utterance; at session scale the
  scope must hold only the DELTA and fall through to the base, or it grows into a full KB shadow.
  `OVERLAY` is the existing mechanism.
- **No promotion.** An interpretation that survives uncontested should collapse into the base and
  stop costing. This is the same "promotion by survival" queued for rules — the mechanism
  generalizes, which is some evidence it is the right shape.
- **One live interpretation is assumed, not enforced.** If two can coexist, reads become ambiguous
  and branch selection returns through the back door.
- **Culprit selection is demonstrated on a case with exactly one judgement in the support.** Real
  contradictions will have several, and choosing among them is the hard part — the answer here is
  the same as everywhere else in this project (ask), but it is untested at that scale.
- **`suppose`/`SCOPE`/`OVERLAY` were not used**; the spike hand-rolls the scope. The production
  path should reuse them, noting that this is a STANDING scope (the default read context) rather
  than a hypothesis fork, which may not want identical semantics.
- **Re-interpretation re-derives everything.** `reconsider`'s dirty-grain cascade is the obvious
  way to scope it to the affected region.

## 12. INTEGRATION STEP 3 — the Loudon corpus (2026-07-18) — `bench/spike_loudon_grammar.py`

> The first time this met prose nobody wrote for it. Everything before ran on 7 sentences chosen
> to exercise gaps we already knew about.
>
> PROTOCOL: `corpus/loudon_grammar.cnl` was written in ONE pass from the corpus VOCABULARY plus
> ordinary English constructions, BEFORE running it. A grammar iterated against its own failures
> would measure nothing.

### 12.1 Coverage: 19/19 on the first pass

    parsed    19/19  (100%)      ambiguous 0/19      refused 0/19      28.5 ms/line

Better than predicted. The grammar needed three constructions beyond `corpus/lion_grammar.cnl` —
predicative adjectives (`the lion is strong`), copula-with-NP subsumption (`the lion is a cat`),
and a second preposition — all expressible as declarations, no Python touched. For comparison,
`spike_loudon.py` measured the shipped bank at 0% before the surface-normalization wiring and 79%
"routed" after, where routed included two silent mis-parses.

**Caveat that keeps this honest:** these are the 19 CNL lines an LLM produced from 50 sentences,
not the 50 sentences. The corpus is 26% facts by construction (`spike_loudon.py` §1) and the
translation already targeted a controlled subset.

### 12.2 The exception, finally in the KB

    <is bengal & is_a lion>   has     mane
    <is persian & is_a lion>  has     mane
    <is guzerat & is_a lion>  has_not mane
    lion                      has     mane

The generalization and its counterexample now coexist on distinct entities linked by `is_a`. Under
the PERCOLATING reading the same corpus derives **1 contradiction** (`about 'lion' because 'mane'`,
25 surface mentions behind it); under MINTING, **0**. That is the whole arc in two numbers.

### 12.3 Three real defects, and only one was in the new code

1. **`load_facts` was QUADRATIC in batch size** — `authoring._recognize` called
   `normalize_surface` once per sentence, but that function ignores its `anchor` and runs each
   stratum over the WHOLE graph to fixpoint. N sentences = N global fixpoints over a graph growing
   with N. Measured on the simplest possible CNL: 26 ms/line at 10 lines, **161 ms/line at 80**; an
   85-line KB file took 24 s. Fixed by hoisting to ONE batch pass (the content forms already ran
   whole-batch for exactly this reason): per-line cost is now FLAT at ~5 ms, 80 lines went
   **12.9 s → 0.44 s (29×)**, grammar load **24.3 s → 1.1 s**, and the test suite 78 s → 42 s.
   **This is shipped-code debt the grammar arc merely exposed** — it bites `load_facts`,
   `load_corpus`, and `load_kb` equally.
2. **The same defect shape in the new code.** `parse` runs its banks over the whole graph, so
   calling it per sentence into an accumulating KB was quadratic too. Added `parse_batch`. Worth
   noting as a PATTERN: "run_bank over the whole graph, once per utterance" is quadratic by
   construction, and it is an easy thing to write without noticing.
3. **Identity must be settled before predication.** `the african lion is strong` produced an entity
   described as `<is african & is strong & is_a lion>`, which then failed to intern with
   `<is african & is_a lion>` from another sentence — an ACQUIRED fact had entered the IDENTITY,
   because the NP-level attribute assertion and the clause-level predicative assertion both write
   the predicate `is`, and a description keyed on predicate NAMES cannot tell them apart. Fixed
   structurally: assertions whose category is a MINTING category are DEFINING and run first, then
   description-keyed interning settles which entities exist, and only then does anything get said
   about them. The description is additionally STAMPED at that moment (`DESCR_ATTR`), because
   recomputing it live re-introduces the same leak.

### 12.4 Still not answered

- **Who writes the grammar for open prose?** This one was hand-written from a known vocabulary. The
  open-class default covers ENTITIES but not PREDICATES, so a new corpus needs its verbs declared.
  That is the learning arc's T3 form learning, now with a concrete target.
- **The 31 sentences that yield no facts** are untouched by any of this: they are anecdote, quoted
  narrative, and hedged attribution — a property of the SOURCE, not of the grammar.
