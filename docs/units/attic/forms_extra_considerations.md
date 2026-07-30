# Forms — extra considerations (Q&A trail)

**Status: reasoning trail, 2026-07-28. Filed to attic 2026-07-30 hygiene pass — it said "not a
specification, nothing here should be cited outward" from the day it was written, so it was never load-
bearing on its own.** A record of a working-session discussion that pressure-tested `../forms_discourse.md`
and `../forms_llm.md` from first principles, working through concrete examples until the confusions
resolved. Read those two first; this document only adds what came out of arguing with them.

---

## 1. Is the human brain also just a bounded, lossy reasoning machine? — yes, and the parallel is exact

`forms_llm.md` §7 argues the LLM case is not "LLMs are weak," but **discipline and reporting**: encoding is not
composing (§4), and depth-bound failure is *silent* — a model that runs out of layers emits a confident wrong
answer rather than reporting exhaustion.

Applying the same split to brains:

- **Representation**: present. Every language grammaticalizes negation, quantification, tense, conditionality —
  the closed class is there, the same evidence base (`form_inventory`'s Schank/NSM catalogs) that argues it for
  LLMs argues it for humans.
- **Composition under depth**: fails in the *predicted shape*. Belief-bias in syllogistic reasoning, the Wason
  selection task, nested-conditional confusion, a ~4-chunk working-memory cap on bound variables — these are
  composition failures under depth and interference, not recognition failures. Nobody fails to know what "not"
  means; people fail to propagate it correctly through three nested conditionals. That is §4's row 1 (no
  intro/elim enforced) and row 2 (approximate composition degrading multiplicatively), not a vocabulary gap.
- **Silent exhaustion (§7, the decisive point)**: this is the sharpest parallel. A person out of reasoning depth
  does not emit `OUT_OF_FUEL` — they emit a confident wrong answer. Confabulation research (split-brain
  patients inventing justifications post-hoc; choice-blindness experiments where people defend a choice they
  did not actually make) is a *behavioral* demonstration of exactly the failure §7 names: budget exhaustion
  reported as an answer, no distinct signal.

**Where the analogy breaks, and it matters:** humans are not purely one forward pass. Deliberate, serial,
externally-notated reasoning (writing out a proof, checking a derivation on paper) is a CoT-like capability
available to a bounded, silently-approximating reasoner — and that is not incidental. **The entire history of
formal notation and proof-checking is the species-level version of the same fix this project is arguing for
locally**: don't trust the bounded reasoner's forward pass to self-report when it has run out of road; give it
an external, exact, checkable substrate with a real exhaustion signal instead. §7's four-outcome contract
(`satisfied` / `starved` / `out_of_fuel` / `awaiting` / `surged`) is the engineered version of what formal logic
already does for human cognition.

⭐ **Not "the brain is fine, LLMs are flawed."** Both are bounded-depth associative reasoners with the same two
failure modes (approximate composition, silent exhaustion). The fix generalizes past LLMs specifically —
consistent with `forms_llm.md` §11's "not grounds for the boundary to interpret," and strengthens §7's claim
that the argument survives arbitrary improvement in the reasoner, biological or artificial.

---

## 2. "Check all combinations" — of what, exactly?

Raised against `forms_discourse.md` §4.2's harmony claim ("checking N forms is linear; probing pairwise
composition is not") and the sieve's measured result (`sieve-measures-the-axes.md`: **composition needs an
entry per pair**, sum = floor, product = ceiling).

**Not the axes.** CONTENT × FORCE × LEVEL (§2.2) are the coordinates that locate one form — an orthogonal
classification, no more compositional content than a type signature's shape. Two forms can each sit at a
well-defined point in that product and still fail to combine safely; the axes carry no closure guarantee.

**Pairs of closed-class *forms*** (inventory entries — negation, degree, quantification, conditionality, tense,
causation, …, each already a point on the three axes). That is where §3.2's "1,225 pairs" comes from
(≈ C(50,2) for a ~50-entry inventory), and it is where the sieve's 65%-leak measurement was actually taken.

**Three ways this understates the real space, in increasing order of how much they matter:**

1. **Order may matter.** `negation(degree(X))` and `degree(negation(X))` are not obviously the same reading —
   if composition is non-commutative, unordered pairs (~1,225) undercount; ordered pairs (~2,450) is the honest
   floor.
2. **Self-composition** — a form nesting with itself (double negation, nested conditionals) sits on the
   diagonal, outside "pairs of two *distinct* forms" if the enumeration only walks off-diagonal cells.
3. **⚠ The one that actually matters: n ≥ 3.** Pairwise safety does not imply n-wise safety — same shape as
   pairwise-independent-but-not-jointly-independent random variables, or local confluence not implying global
   confluence in a rewriting system. Three forms nested (negation under quantification under conditionality)
   can leak even when every pairwise composition among them was individually verified clean. `forms_discourse.md`
   §4.2 already says this out loud — "1,225 pairs **and unbounded nestings**" — but the sieve's measured number
   is a pairwise number. Depth ≥ 3 is untested. This is the same open problem as the depth-4/depth-5
   surge-detector finding (§10.3), one axis over: there it was *recursion* depth that broke silently past a
   threshold, here it would be *composition* depth.

**So: the honest target is unbounded, pairwise checking is the first tractable slice of it, and completeness
has not been argued past that slice.**

---

## 3. Composition failure vs. misrecognized non-composition

Raised against the `degree ∘ negation` leak: doesn't every apparent composition failure just mean the surface
form was never really a composition in the first place?

**Partly — and there is already a test for exactly this, reused from a different part of the argument.**
Fodor's kill/cause-to-die objection (§7.2) *is* the test: a proposed decomposition is wrong if it licenses
inferences the original does not (*"caused to die on Sunday by stabbing Saturday"* is fine; *"killed... by
stabbing"* on a different day is not — so *kill* was never *cause+become+not-alive*). §3.6's promotion criteria
say the same thing generally: *"if it cannot be verified by desugaring, it must be closed"* — i.e. give it its
own atomic entry rather than keep pretending it decomposes.

**Litotes ("not very beautiful" read as understatement) passes that test toward *reclassify*.** It is not
computed by composing NOT with (VERY BEAUTIFUL); it is a conventionalized, lexicalized pattern — §3.4's
"boundary runs through the item, not between items," one level up at the phrasal idiom scale rather than the
single-lexeme scale.

**But this cannot be the general answer, and treating it as one is itself a risk.** Negation genuinely *is*
meant to compose productively with arbitrary gradable predicates — "not very expensive," "not very fast," "not
very likely" are freely generated, which is exactly what makes negation closed-class rather than idiomatic in
general. Most instances of `not very X` really are literal scope composition and must compose correctly. Tonk
(§4.2 glossary) is the sharpest counterexample in the abstract: two individually fine connective rules whose
*combination* derives anything — nobody would say the connectives "aren't really composing"; the composition is
real and unsound.

**⚠ The risk to flag explicitly:** "this must not really be a composition" is a free pass if applied without the
test. Taken as a default, it lets genuine ruleset bugs hide forever behind reclassification instead of being
fixed. The discipline needs the positive test (Fodor's — does the decomposition license exactly what the whole
licenses, no more no less?) to choose between *fix the composition* and *promote to atomic*, not a preference
for one answer.

---

## 4. Intro/elim rules, worked examples (for readers who cannot picture them from the definition alone)

| connective | introduction | elimination |
|---|---|---|
| **AND** | from `A` and from `B`, write `A∧B` | from `A∧B`, derive `A`; from `A∧B`, derive `B` |
| **OR** | from `A` alone, write `A∨B` (any `B`) | from `A∨B` plus `A⊢C` and `B⊢C`, derive `C` (case split) |
| **IMPLIES** | assume `A`, derive `B`, discharge: conclude `A→B` | from `A→B` and `A`, derive `B` (modus ponens) |
| **NOT** (constructive) | assume `A`, derive `⊥`, discharge: conclude `¬A` | from `A` and `¬A`, derive `⊥` |
| **tonk** (Prior's broken connective) | OR's cheap intro: from `A` alone, write `A tonk B` (any `B`) | AND's strong elim: from `A tonk B`, derive `B` outright |

Tonk's leak, spelled out: from any true `A`, introduce `A tonk B` for an arbitrary `B` you want, then eliminate
straight to `B`. An arbitrary conclusion from an unrelated premise. Each half is a legitimate rule borrowed from
a real connective; the mismatch is the whole defect.

Mapped onto this project's own vocabulary:

| form | introduction | elimination |
|---|---|---|
| **role (`agent:`)** | a rule matching a transitive-verb occurrence + subject filler writes `agent: <filler>` | a rule reading `occurrence.agent` to conclude "X performed this," or to answer "who did this" — trivially matched, which is why roles are largely uncontroversial |
| **degree (`~band`)** | a rule seeing a gradable predicate + intensifier writes `degree: band(high)` | a rule reading the band to license a comparative, or a threshold match |
| **this engine's negation** | a rule marking an occurrence negated on an explicit surface negation | deliberately weak: licenses only `starved` ("nothing matched"), never `underivable` ("provably false") |

---

## 5. Is engine negation "wrong" in the harmony sense? — no, that conflates two different things

**Negation's own intro/elim pair is harmonious, and its usefulness comes from that, not despite it.** Classical
negation is the one that is *not* harmonious — double-negation elimination (`¬¬A ⊢ A`) eliminates to more than
any introduction rule earned. This engine avoids that by using constructive negation: weak introduction
(`starved`, never claims falsity), matched weak elimination (never license `underivable` from it). §4.5 already
says this is exactly the kind harmony *can* certify, and that the epistemic position and the composition
discipline "want the same logic." Weak-but-matched is not a compromise; it is the sound case, the same reason
`Option`/`Result` beat null-and-hope.

**The measured `degree ∘ negation` leak was a different failure**, in the composition machinery, not in
negation's own definition: two separate write paths (a fold, and the interpretation layer) built pieces of the
composite with no shared elimination reading both together. A wiring defect connecting negation to something
else, orthogonal to whether negation's own semantics are sound.

---

## 6. Three layers that get conflated: entailment, implicature, idiom — worked example

> *"not not tall"* → *"tall"*, but *"not very beautiful"* is also satisfied by *"not beautiful [at all]"* — how
> do these fit together?

Different phenomena, and keeping three layers apart resolves the confusion:

1. **Strict compositional entailment.** `not(very(beautiful))` is a **threshold** claim — "degree of beauty
   does not reach the 'very' threshold" — true across the entire range below the threshold, zero included. So
   "not beautiful at all" genuinely *satisfies* "not very beautiful." No contradiction, no leak; a threshold
   negation is supposed to behave exactly like this ("I don't have a lot of money" is true whether you have $50
   or $0).
2. **Scalar (Gricean) implicature — defeasible, not truth-conditional.** The "somewhat beautiful, just not very"
   reading comes from the maxim of quantity: if the speaker knew "zero beauty," they would have used the
   stronger, more informative "not beautiful"; choosing the weaker form implicates the stronger one is false.
   **The test that separates this from entailment is cancelability**: *"She's not very beautiful — actually,
   she's not beautiful at all"* is coherent (implicature canceled without contradiction); canceling a real
   entailment produces a contradiction. This is the same mechanism as "some" implicating "not all" while
   remaining literally compatible with "all."
3. **Lexicalized idiom (litotes proper).** A different case from either of the above — a frozen collocation
   whose meaning has drifted and is no longer computed from its parts at all (§3, above). Not what's happening
   in the "not very beautiful" example — that one *is* live threshold composition (layer 1) plus live
   implicature (layer 2) — but the same *surface shape* ("not X-modifier") can, in other collocations, have
   drifted all the way to layer 3.
4. **"not not tall" → "tall" is layer 1 done twice — classical DNE**, exactly the non-harmonious case (§5).
   Note ordinary English rarely runs this transparently: doubled negation via prefixes ("not unattractive," "not
   incorrect") usually does *not* cancel back to the plain positive — it stays hedged, closer to "passable"
   than to "attractive." That is itself evidence that natural-language double negation is not running clean
   classical DNE either; it is doing something weaker and implicature-flavored, the same pattern as layer 2.

**⭐ The concrete danger for this project's ruleset:** an elimination rule for degree-negation that concludes
"some X is present" from `not(very(X))` has **baked a layer-2 implicature into a layer-1 entailment**. That is a
genuine harmony leak — the elimination now derives more than the introduction's truth conditions support
(specifically, it wrongly rules out the zero case that a threshold negation must still allow). The correct
elimination rule stops at "below threshold" and stays silent on whether any X is present at all; anything
implicature-flavored belongs in a separate, explicitly defeasible mechanism, never folded into the hard logical
elimination rule.

---

## 7. Open

- §2's n≥3 composition-depth question is unmeasured — same shape as §10.3's recursion-depth finding, one axis
  over.
- §3's reclassify-vs-fix test (Fodor's) has not been run systematically against the sieve's other leaked cells
  — worth doing before assuming they are all machinery bugs or all misclassified idioms.
- §6's entailment/implicature distinction is not yet reflected anywhere in the entry format (§5.2 of
  `forms_discourse.md`) — an entry currently has no field distinguishing what it strictly entails from what it
  merely (defeasibly) suggests. That is plausibly a missing field, not just a missing worked example.
