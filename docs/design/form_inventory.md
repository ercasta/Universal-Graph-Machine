# The Form Inventory — baroque surface vs epistemically fundamental form

> **Status: FOUNDATIONAL (user decision, 2026-07-20).** This is the design principle the form-set
> work is organised around, and the typed inventory it produces. Read it before adding anything to
> `corpus/*_grammar.cnl`.
>
> Context: `implementation_plan.md`'s 2026-07-20 re-point ("the target is a minimum form set, not
> form learning") and the refusal experiment recorded there.

## 1. The distinction

A construction that appears in real prose is one of two things.

**BAROQUE** — ornamental variation on a commitment the substrate can already hold. Word order,
synonyms, clefts, passives, `not only … but`, `an` vs `a`, `are` vs `is`. Unbounded in number.

**EPISTEMICALLY FUNDAMENTAL** — it carries a *kind of commitment* the substrate has no way to hold.
Degree, attribution, negation, conditionality, quantification, tense, causation. Small in number.

**"Commitment" has TWO dimensions, and §4 is organised by them:** *what* is claimed (CONTENT) and
*what is being done* with the claim (FORCE — asserting it, asking it, commanding it, authoring it).
Asking is not a weaker way of asserting; it commits to nothing and changes no beliefs. This document
listed only the first dimension until 2026-07-20, which made it incomplete as a reference in a way
that was invisible precisely because every *content* entry was correct.

**The test — and it is a real test, not a vibe:**

> Can it be paraphrased into existing forms **without changing what the system believes**?
> Yes → baroque. No → fundamental.

"Believes" is doing the work. Losing *detail* is attenuation and keeps it baroque. Changing the
*epistemic status* of what remains — asserting what was attributed, asserting flatly what was
hedged, asserting identity where the source said resemblance — means the construction was
fundamental and the paraphrase was a lie.

## 2. Why this is foundational and not taxonomy

**(a) It is why "minimum form set + LLM translator" is viable rather than wishful.** English's
baroque surface cannot be enumerated. The kinds of epistemic commitment roughly *can*. The
architecture works because the translator absorbs the unbounded half and the form set only has to
cover the bounded one. Without this split, "minimum form set" is just a wish that English be small.

**(b) It is the same line as "learning surface is verifiable, learning semantics is not."** A
baroque form is learnable *because* it desugars: you can check a learned alias by confirming it
produces the same structure as the core form. A fundamental form cannot be learned, because there is
no target to check against — it must be designed. `learning_design.md` §7.1's T1/T3 split was
derived from the *translation-target* argument; this reaches the same line from *epistemology*. Two
independent routes to one boundary is decent evidence the boundary is real.

**(c) It predicts cost.** A fundamental form is cheap iff a substrate mechanism already exists.
Hedging landed in a day because the possibilistic layer had been built weeks earlier; tense would be
expensive because nothing exists. That is the estimate to make before scoping, and §4 records it
per entry.

## 3. The classification is NOT obvious — measured, both directions

This is why entries get PROBED, never assigned by intuition (five for five wrong this session).

- **Looked fundamental, was baroque.** `the mane is thick`, `the captive lion has a mane` — both
  predicted as expressiveness gaps; both parse once the words are declared. `captive lion` is
  modifier+np, structurally identical to `african lion`.
- **Looked baroque, was fundamental.** Hedging. The obvious cheap fix is "declare `generally` a
  modifier" — which *parses*, and asserts `lion is generally`. Nonsense. The baroque-shaped fix
  produced garbage precisely because the distinction was epistemic. It needed bands, a fork, a scope.

## 4. The inventory

**⚠ READ THIS FIRST: THE INVENTORY HAS TWO AXES, AND EVERY ENTRY BELONGS TO EXACTLY ONE.** Until
2026-07-20 this document listed only the first, which made it silently incomplete as a reference.

| axis | question it answers | examples |
|---|---|---|
| **CONTENT** (§4a) | *what is claimed?* | degree, negation, conditionality, tense, quantification |
| **FORCE** (§4b) | *what is being DONE with the claim?* | assert, ask, command, author, retract |
| **LEVEL** (§4d) | *what is the claim ABOUT?* | the world (L2), the theory (L1), the language (L0) |

**They are ORTHOGONAL, and that is why they cannot share a table.** Any content can carry any force:
*the lion generally has a mane* (hedged assertion) vs *does the lion generally have a mane?* (hedged
question) vs *assume the lion generally has a mane* (hedged supposition). A single list would have to
enumerate the product; two axes enumerate the sum.

**Do not confuse ATTRIBUTION (content) with FORCE.** *Some naturalists consider the lion a cat*
REPORTS someone else's assertion — the force of THIS utterance is still plain assertion, and what is
asserted is a proposition about a holder. Force is a property of the utterance being made, never of
the proposition inside it. The two feel similar because both involve "who is committing to what";
the discriminator is whose act is being performed rather than described.

### 4a. CONTENT — what is claimed

`mechanism` = does the substrate already have somewhere to put it.

### Fundamental — REPRESENTED

| form | example | mechanism | state |
|---|---|---|---|
| degree / hedging | *the lion generally has a mane* | possibilistic band (fork + `<likeliness>`) | BUILT 2026-07-20 |
| negation / exception | *the guzerat lion has no mane* | `has_not`, reachable counterexample | BUILT |
| certainty (default) | *the lion has a mane* | ink | BUILT |

### Fundamental — MECHANISM EXISTS, SURFACE UNBUILT

| form | example | mechanism | note |
|---|---|---|---|
| attribution | *some naturalists consider the lion a cat* | holder-keyed pencil scope | non-veridicality already free: `check` returns `assumed-no` for a penned proposition |
| genericity | *a lion* vs *the lion* | `det` slot | one declaration line, probed. But see conditionality below: the determiner is a BAROQUE carrier for a FUNDAMENTAL distinction (the definite generic — *the lion is dangerous* — is standard English), so it belongs in the sugar layer over an explicit core form, never as the thing the engine keys on |

### Fundamental — REPRESENTED, but the layers did not meet

| form | example | mechanism | state |
|---|---|---|---|
| conditionality | *?x is dangerous when ?x is hungry* | the rule layer (`load_machine_rules`) | **surface and mechanism BOTH already existed — and did not meet.** FIXED 2026-07-20 |

**The 2026-07-20 probe, and why it is the sharpest instance of §3 so far.** Conditionality was scoped
as "mechanism exists, surface unbuilt", needing an `implies` verb. Both halves of that were wrong:

- **The explicit core surface already ships.** `?x is dangerous when ?x is hungry` is unambiguous by
  construction and intake routes it to the rule layer *ahead of* the grammar fork. So no new
  fundamental form was needed — and `a lion is dangerous when a lion is hungry` is **T1 sugar** over
  it, which by §5's criterion must be justified from the residue log, not built speculatively.
- **But the rule layer and the grammar route did not actually meet.** The rule MATCHED its premise on
  the interpretation entity and EMITted its conclusion onto the discourse TOKEN, so the derived fact
  landed outside the interpretation scope — unattributable, undiscardable, and outliving the premise
  that produced it. The query answered `yes` only because name resolution also picked the token
  first. Right by luck, with a `UserWarning` as the only trace.

**THE LESSON FOR THIS DOC, and it is a new one: "the mechanism exists" is not the same as "the
mechanism is REACHABLE from the surface".** §2(c) says a fundamental form is cheap iff a substrate
mechanism already exists. That is necessary and not sufficient — the mechanism and the surface must
land in the same LAYER, and here they did not. Every entry in the "mechanism exists" table above
should be probed end to end (assert through the real route, then *ask*) before being called cheap.
Attribution is next and has exactly this shape: its mechanism (the pencil scope) is written by the
fold, so it is on the entity side — but that must be measured, not assumed. **This end-to-end check
is now `bench/spike_epistemic_closure.py` (§9): assert→ask through the real `ingest`, classified
PASS / REFUSED / LEAK. Run every "mechanism exists" claim through it before graduating it to
REPRESENTED.**

**And it is a distinction question, which is why it belongs here.** The epistemic question was never
"which determiner marks generality". It was *"when the system derives through a conditional, what
does it believe, and in which layer does that belief live?"* No surface choice could fix an answer of
"an ink fact on a discourse token". Surface/epistemic separation is what surfaced it: asking which of
the design decisions were paraphrasable is what moved attention off the declaration syntax and onto
the layer boundary.

### Fundamental — NO MECHANISM

| form | example | note |
|---|---|---|
| ~~use vs mention~~ | *produces is a relation* | **RE-DIAGNOSED AND FIXED 2026-07-20 — it was never a missing CONTENT form.** Found by `bench/spike_force_coverage.py`, and it is the first entry the system found in ITSELF rather than in a corpus. The OBSERVATION was right (the declaration sentence parses while the word is unknown and REFUSES once declared, because a verb-category word cannot head an np) but the diagnosis was wrong: it is a **LEVEL violation** (§4d), not a gap in what can be said. An L0 declaration was being read by the very grammar it modifies. Kept here as the worked example of §3 — a fundamental-looking gap that was a layering fault |
| tense | *were formerly found … now confined to* | nothing exists. Expensive. |
| exclusivity / *only* | *confined to Africa* | CWA/NAF exist; no surface, and no way to say "only" |
| quantification | *all the varieties*, *some naturalists* | partial |
| causation | *indebted to*, *therefore* | nothing |
| resemblance-in-a-respect | *resembles a cat in his mode of stealing* | distinct from `is_a`; conflating them produced a real distortion (Loudon 39). cf. Brachman, "What IS-A is and isn't" |

### 4b. FORCE — what is being done with the claim

**FORCE IS EPISTEMICALLY FUNDAMENTAL under §1's own test, and it is the axis this document was
missing.** *Is the lion dangerous?* cannot be paraphrased into an assertion without changing what the
system does — it requests rather than commits, and answering it changes no beliefs. Likewise *focus
on ada* moves attention, *forget that rule* retracts a licence, *to build : …* authors a procedure.
None of these is a claim about the world at all.

**UGM HAS ALWAYS HAD FORCE. It is simply not represented as FORM** — it lives in the ordered if-ladder
of intake routes in `intake._ingest_gen` (question → rule → form → procedure → focus → stance → fact).
That is why the grammar does not subsume CNL: **the grammar models content; force lives in the
router.** The forms below are what that ladder implements.

| force | example | where it lives today | state |
|---|---|---|---|
| ASSERT | *the lion has a mane* | the fact route / `clause asserts …` | **FORM** — the only one that is |
| DENY | *the lion has no mane* | `clause denies …` | **FORM** |
| HEDGE | *the lion generally has a mane* | `hclause hedges …` | **FORM** (2026-07-20) |
| ASK | *is the lion dangerous* | `qclause asks …` | **FORM** (2026-07-20) |
| GOAL | *goal ada is a target* | `gclause intends …` | **FORM** (2026-07-20) |
| COMMAND | *focus on ada*, *be cautious*, *run build* | `iclause commands …` → registers / `<run>` | **FORM** (2026-07-20) |
| AUTHOR | *?x is dangerous when ?x is hungry*, *form K : …*, *to N : …* | intake route → `Rule` / procedure | route only |
| RETRACT | *forget that rule* | `rule_control` | route only |
| NORM | *don't sell rare cards* | `deontic._mint_object_norm` | route only |

**⭐ THE THREE COMMITMENT VERBS ARE ALREADY FORCE MARKERS.** `asserts` / `denies` / `hedges` differ in
exactly one thing — WHAT THEY COMMIT — which is the definition of force. So the declaration axis
already exists and is one third built; `asks` / `authors` / `commands` extend it rather than
introducing a new mechanism.

**STATUS 2026-07-20: THE AXIS IS BUILT EXCEPT FOR AUTHORING.** Six verbs now share one `(verb, mode)`
table in `grammar._assert_forms` — `asserts` / `denies` / `hedges` commit (ink, ink-negative, pencil);
`asks` / `intends` / `commands` commit nothing and generate no fold rule at all, differing only in
what they LEAVE BEHIND (nothing / a `<goal>` node / a change of stepping state). The prediction above
held exactly: each was a table entry plus declarations, never a new mechanism.

**AUTHOR and RETRACT are deliberately NOT verbs, and this is the settled boundary.** They author a
BANK — a `Rule`, a form, a procedure — which the fold structurally cannot produce (class (b) below).
They stay as intake routes ahead of the grammar, recognized by their own forms. Measured, not
assumed: the grammar refuses every authoring surface, so their position ahead of the dispatch is not
a routing decision. That is also what keeps conditionals reaching the rule layer.

**MEASURED 2026-07-20, and this is why force is the priority rather than a curiosity.** Over the 68
unique CNL utterances the repo's own tests actually ingest, a canonical grammar covers 37 (54%), and
**25 of the 31 failures are force** (18 questions, 4 goals, 3 speech acts). The remainder is a genuine
long tail (one quantifier, one degree adverb, one PP attachment). **The migration to a
grammar-subsumes-CNL intake is not blocked by a breadth of constructions; it is blocked by one
missing axis.**

**MECHANISM: `run NAME` is the precedent, and it means force needs no new fold capability.** It
already works by seeding a reified `<run> proc NAME` node that a driver acts on. So the fold writes a
REIFIED INTENT (graph data, which it can already write) and the ROUTE dispatches on it. Classes (a)
graph-writes and (c) speech acts are reachable that way; only (b) authoring a `Rule` needs machinery
the fold does not have, and that is deliberately hand-authored (T2).

**PROBED: syntax is not the obstacle.** Given productions, the grammar parses *is lion dangerous*,
*be cautious*, *focus on lion*, *run build* and *don't sell rare cards* from DECLARATIONS ONLY, with
zero ambiguity against the fact corpus (which stays 23/23). **And force composes cleanly for a
structural reason worth recording: English marks it POSITIONALLY, at the LEFT EDGE.** An
imperative/prohibitive/copula in initial position is unambiguous against a fact beginning with an np.
The root category (`clause` / `qclause` / `iclause` / `pclause`) then recovers the force, so routing
can become declarative rather than an ordered ladder.

**~~WHAT IS STILL OPEN.~~ SETTLED 2026-07-20 BY BUILDING IT: force is a VERB.** The question was
whether force should be a verb on the assertion declaration (`qclause asks subj pred obj`) or a
CATEGORY property (`qclause is interrogative`). The verb won, and the deciding argument was not the
aesthetic one (matching the existing three) but a structural one that only appeared under
construction: **a force needs to say WHICH SLOTS carry its triple**, and the assertion surface
already has exactly that shape, including the `when`/`unless` guards. A category property would have
needed a second declaration to carry the slots, i.e. the verb surface again under another name.

### 4d. LEVEL — what the claim is ABOUT

**BUILT 2026-07-20 (user proposal, option C).** A claim is about the **WORLD** (L2 — *the lion has a
mane*), the **THEORY** (L1 — *?x is dangerous when ?x is hungry*, a form, a procedure), or the
**LANGUAGE ITSELF** (L0 — *produces is a relation*). L0 does not describe anything; it constitutes
what can be said next.

**ORTHOGONAL TO BOTH OTHER AXES, and measured so:** `is produces a relation` is a QUESTION (force)
about the LANGUAGE (level). Any level can carry any force. Three axes enumerate the sum where one
would have to enumerate the product — the same argument §4 makes for separating content from force.

**THE FALSIFIABLE TEST THAT ESTABLISHED IT.** If the use-mention defect was a LAYER violation rather
than a missing form, then the non-idempotent surfaces should be *exactly* the L0 ones. Round-tripped
12 surfaces (same line ingested twice): **every L1 and L2 surface routed identically twice; the only
failure was L0.** The axis predicted the defect exactly. ⚠ The *assignment* never failed across 15
surfaces, but those were hand-chosen — no adversarial attempt to find an unclassifiable surface has
been made, and that is the test that would put the axis at risk.

**THE TWO DESIGN RULES, and they are independent — each has its own failure mode:**

1. **L0 is recognized by a FIXED form, never by the object grammar.** Otherwise a declaration is
   destroyed by its own effect. This is what makes re-declaration idempotent.
2. **L0 lives in a REGISTER, never as graph facts.** As facts it LEAKED (`?y is meta when ?y is a
   relation` derived `produces is meta`) and it hit the token/entity duality at the meta level
   (`produces` resolved to two nodes). A meta *scope* in the graph would make the leak avoidable
   only by discipline in every present and future reader; a register makes it impossible.

Re-breaking confirms they are separable: restoring (1) alone fixes idempotency but not the leak;
restoring (2) alone fixes the leak but not idempotency.

**L0 HAS THREE TIERS, AND THE RUNTIME LINE SITS BETWEEN THE SECOND AND THIRD** (user decision,
2026-07-20: *"a session should not be able to extend the grammar structure at runtime"*). An earlier
draft of this section drew the line as schema-vs-instances, which is WRONG — a production is an
instance of the schema and still must not grow at runtime.

| tier | what it is | where it lives | grows at runtime? |
|---|---|---|---|
| **schema** | what KINDS of declaration exist | Python (`DECLARATION_FORMS`, `VOCABULARY_FORMS`) | **never** — not even at load time |
| **structure** | which productions / slots / force verbs this language HAS | the grammar `.cnl` file, load-time | **no** (user decision) |
| **vocabulary** | which WORDS are in which category | grammar file *or* a live session | **yes** — the register |

**WHY THE LINE IS THERE, and it is not arbitrary:**

- **Translator stability.** New vocabulary does not change the SHAPE of the language: an SLM told
  what the constructions are can handle a new noun without being retold. A new production changes
  which sentences are grammatical, so the translator would have to be re-briefed — and the plan's
  settled position is that *"the target language must be FIXED AND KNOWN for a translator to aim
  at it."* Vocabulary is safe to grow; structure is not.
- **Blast radius of ambiguity.** Adding a word can only make existing productions apply to more
  strings — any ambiguity it creates involves *that word*. Adding a production can make sentences
  ambiguous that contain no new token at all. Ambiguity is DETECTED here but deliberately never
  auto-resolved, so the second kind silently widens what must be asked about.
- **The schema tier is what bounds the regress** at two levels: the metalanguage cannot be extended
  from inside the object language, so there is no meta-meta.

**ALREADY ENFORCED, verified rather than assumed.** `np expands to noun`, `slot … is only head`,
`clause asserts …` and `qclause asks …` all route `unrecognized` in a session, and `load_kb` RAISES
on them, naming the line. The decision therefore ratifies the status quo and costs nothing — but it
is recorded because the behaviour previously had no stated reason, and "it happens not to work" is
not the same as "it must not work".

**⚠ ONE INCONSISTENCY THE DECISION EXPOSES: hedge bands.** `rarely means 0.15` is VOCABULARY by this
table (a word and the degree it denotes — it adds no production and changes no sentence's shape), so
the line above says it *should* be runtime-declarable. It currently routes `unrecognized`, i.e. it is
treated as structure. Not resolved here; flagged so the tiering stays honest.

**WHAT IT COST, honestly:** `is produces a relation` no longer answers. Nothing else — the grammar
itself was never in the graph, and the parse surface, the interpretation, its facts and all
provenance are untouched. Querying the language belongs back as a deliberate §8 READER over the
register, not as a side effect of leaving L0 in the reasoning graph.

**THE LEXICON NO-OP, FIXED 2026-07-20.** `wolf is a noun` used to route `fact` and extend nothing —
a success verdict and an inert fact, §8's "understanding ≠ parsing" at the meta level and the worst
of the L0 defects because it was *silent* rather than refused. One form now covers the family
(`W is a K`, kind BOUND rather than literal), and `resolve_vocabulary` asks the LIVE GRAMMAR whether
`K` names a category — so `wolf is a noun` and `snarls is a intransitive` declare, while
`ada is a suspect` stays a fact. **The shape match is deliberately NOT the decision**: dropping the
category check makes `ada is a suspect` a silent lexicon declaration committing no fact (re-break
verified). `relation` is the one kind word that is not itself a category — it is the KB-level
spelling the shipped route has always used, and it means a transitive verb.

**STILL OPEN AT L0.** `np expands to noun` and `X means N` remain loader-only — a session can
declare WORDS but not PRODUCTIONS or bands. The shipped (non-grammar) route still lands
`R is_a relation` as a graph fact, because `load_corpus` bypasses intake and `forms.relation_forms`
rebuilds from the graph; `sync_vocabulary` reads the union of both homes until that half is retired.

### 4c. BAROQUE — desugar, never represent

Applies to BOTH axes: a construction can be an ornamental way of saying something already sayable
(content) or an ornamental way of performing an act already performable (force — *could you tell me
whether…* is a baroque question).

Already normalized mechanically: `an`→`a` (`forms.tokenize`), `are`→`is` (`uncertainty._norm`).
Both docstrings call this "mechanical and meaning-free", which is this distinction operating before
it had a name. Candidates for the sugar layer (T1): clefts (*it is generally in the night that he
prowls* ≡ *he generally prowls at night*), passives, `not only … but`, word order, synonyms.

## 5. How entries arrive — the residue log

Entries are **corpus-derived, never designed a priori** (§3). The mechanism is the four-outcome
translation contract:

| outcome | when |
|---|---|
| CNL | complete capture |
| CNL + RESIDUE | attenuated — emit, and record what was dropped |
| CANNOT-EXPRESS | capturing anything would distort |
| NOTHING-TO-ASSERT | the source asserts nothing |

Every RESIDUE and every CANNOT-EXPRESS is a candidate inventory entry. Ranked by frequency across
corpora, the log *is* the inventory, generated rather than audited by hand. Convergence across
corpora is the signal the set is adequate.

**Attenuation must never be silent, and the reason is not bookkeeping.** Attenuation is safe for
DEDUCTION — the KB merely knows less. It is *not* safe for INDUCTION: dropping *the guzerat lion has
no mane* was a pure attenuation, and it let the learner propose "lions have manes" with its only
counterexample removed. **To a learner, absence looks like confirmation.** So the residue is
evidence the learner needs, not a to-do list.

## 6. Precedents

Recorded because the distinction is almost certainly not new, and the literature should be checked
rather than reinvented.

> **⚠ THESE ARE LEADS, NOT VERIFIED CITATIONS. They were produced from an LLM's recall and NONE has
> been checked against a source.** That failure mode is specific and well known: plausible author +
> plausible title + plausible year, with the claim subtly or entirely wrong. Treat every name, date
> and paraphrase below as a search query, not a fact. The same session that wrote this was wrong
> five times out of five about things it could have probed (§3) — assume the same rate here, with
> the aggravating factor that these cannot be probed from inside the repo.
>
> **Start with the first two** — they are the closest and the most consequential if true.

- **Jakobson**, *On Linguistic Aspects of Translation* (1959) — the closest precedent. Roughly:
  languages differ essentially in what they **must** convey, not in what they **may** convey.
  Obligatory (grammaticalized) vs optional (periphrastic) is our fundamental/baroque line, drawn
  for natural language.
- **Evidentiality** (Aikhenvald, *Evidentiality*, 2004) — some languages grammatically REQUIRE
  marking information source (direct / hearsay / inference). Our "attribution" entry, obligatory.
  Important consequence: **different languages draw the line in different places**, so the boundary
  is a design choice, not a natural kind. That is a caution for us, not a comfort.
- **Natural Semantic Metalanguage** (Wierzbicka; Goddard) — a claimed set of ~65 universal semantic
  primes, everything else defined by reductive paraphrase into them. This is the minimum-form-set
  programme carried out for natural language, and their method *is* our test.
- **Attempto Controlled English (ACE)** and Common Logic Controlled English — the direct engineering
  precedent for a fixed, bounded target language with a defined construction set.
- **McCarthy & Hayes** (1969), "Some Philosophical Problems from the Standpoint of AI" — the notion
  of **epistemological adequacy**: can the representation express the facts one actually has, as
  distinct from metaphysical and heuristic adequacy. Very close to §1's test.
- **Brachman** (1983), "What IS-A is and isn't" — conflating distinct relations under `is_a`. Loudon
  39 is an instance in the wild.
- **Frege**, *Begriffsschrift* (1879) — notation invented to make certain inferences expressible and
  checkable; the historical case that representational repertoire bounds reasoning.
- Linguistic relativity (Sapir–Whorf) is the tempting frame and should be handled carefully: the
  strong form is not well supported. See §7.

**Why the first two matter most.** Jakobson would mean the distinction is already named and we
should adopt the vocabulary rather than coin our own. Evidentiality would mean something stronger
and less comfortable: that **the fundamental/baroque line is drawn differently by different
languages**, so it is not a natural kind we are discovering but a DESIGN CHOICE we are making. If
that holds, "is this construction fundamental?" has no answer independent of what we decide this
system must be able to commit to — and the inventory in §4 is a specification, not a survey.

## 7. Does the repertoire BOUND reasoning?

**For this system: yes, and it is measured, not speculative.** UGM cannot represent tense, so it
cannot reason about change. Before 2026-07-20 it could not represent degree, so *the lion generally
has a mane* became either `lion has mane` (false) or nothing (lost). The set of reachable
conclusions is bounded by the set of representable commitments.

**And the bound is not neutral — it SKEWS.** `implementation_plan` §10a: partial coverage does not
lose sentences at random, it loses the *linguistically marked* ones, which are disproportionately
the exceptions — so a missing form does not merely narrow what can be concluded, it biases induction
toward overconfident generalization in a predictable direction. That is the strongest form of the
claim and we have direct evidence for it.

**For humans: weaker, and the honest answer is "shapes rather than bounds."** The strong Whorfian
reading (you cannot think what you cannot say) is not well supported. The defensible version is that
grammaticalized categories affect what is *habitually attended to* and *cheap to transmit* —
evidentiality-marking languages force attention to information source. The stronger human analogue
is **notation**: positional numerals, algebraic symbolism, Frege's quantifiers each unlocked
reasoning that was previously infeasible, which is the human version of adding a fundamental form.

**A form can also be deliberately WITHHELD, and Orwell is the useful case** (user, 2026-07-20).
Newspeak assumes the strong Whorfian claim — remove the word, remove the thought — which is why it
should not be leaned on. But two of its notions invert the direction this section has been arguing
and are worth keeping:

- **doublethink** is not a MISSING form but a deliberately MAINTAINED one: holding P and ¬P without
  deriving the contradiction. This system does the opposite BY CONSTRUCTION —
  `interpretation.contradiction_bank` derives it, and the revision loop asks. Refusing to derive it
  would be a policy, and one we have deliberately not got.
- **crimestop** — refusing to follow an inference — is the closer analogue, and we have a benign,
  honest version: the `max_rounds` fuel budget returns UNKNOWN rather than grinding on
  (`agent, not theorem prover`). The distinction that matters is that ours is DECLARED and its
  verdict WEARS ITS KIND ("unknown", not "no"), where crimestop is concealed.

The general point: a repertoire bounds reasoning from below (a form you lack) and can be bounded
from above (an inference you decline to draw). Both should be visible. Ours are: the residue log for
the first, the honest UNKNOWN for the second.

**The disanalogy matters to us, and it is by design.** Humans can invent a new fundamental form
mid-thought. UGM deliberately cannot — predicate invention is rejected, T3 (induced semantics) is
displaced, and a fundamental form must be *designed in*. So this system's repertoire is a harder
bound than a human's, on purpose. The residue log (§5) is the compensating mechanism: it makes the
bound VISIBLE, so the missing form becomes a recorded observation instead of a silent distortion.

## 8. This gives an operational definition of UNDERSTANDING (user, 2026-07-20)

> **X is understood iff it maps onto epistemic form(s), the mapping is UNAMBIGUOUS, and it PRESERVES
> EPISTEMIC STATUS.**

Checkable, not a vibe — and it earns its keep by making three distinctions the system actually
exhibits:

- **Understanding ≠ parsing.** `the lion generally hunts at night` parsed, routed as `fact`, and
  committed nothing (the slice-2b defect). Recognized; not understood, because no form held its
  commitment.
- **Understanding ≠ truth.** Understanding *some naturalists consider the lion a cat* does not
  require lions to be cats. The attribution is what is understood.
- **Misunderstanding is a MIS-MAPPING, not an absence.** Loudon 39, *resembles a cat in his mode of
  stealing* → `the lion is a cat`, maps onto identity where the source said resemblance-in-a-respect.
  A specific diagnosis, not "wrong".

The two qualifiers are load-bearing: **unambiguous** makes a two-reading parse *not-yet-understood*
(hence ASK, never pick), and **status-preserving** makes a distorting paraphrase a failure to
understand rather than a lossy success.

**The §5 contract is therefore a taxonomy of understanding states:** CNL = understood;
CNL+RESIDUE = partially understood, and WHICH part is known; CANNOT-EXPRESS = not understood, and
WHY is known; ambiguous = understood two ways, ask; NOTHING-TO-ASSERT = nothing to understand. That
is a far better failure than `unrecognized`: the system can report the KIND of claim it cannot hold.

**The consequence that matters for what we build next:**
- adding a BAROQUE form = a new way to **say** something;
- adding a FUNDAMENTAL form = a new way to **understand** something.

So §4's fundamental column is literally *the list of things this system can understand*, and its
"no mechanism" rows (tense, exclusivity, quantification, causation, resemblance) are a precise
statement of its ceiling. UGM can learn facts and learn rules; it **cannot expand its own modes of
understanding**. That is deliberate, not an oversight.

**⭐ AND UNDERSTANDING REQUIRES BOTH AXES — CONTENT MAPPING ALONE IS NOT IT (added 2026-07-20 with
§4b).** Map *is the lion dangerous?* onto the proposition `lion is dangerous` with perfect fidelity,
then ASSERT it, and every content check passes while the utterance has been comprehensively
misunderstood — a question was taken for a claim, and the KB now believes something nobody said.
So the definition is:

> X is understood iff its CONTENT maps onto held epistemic forms, unambiguously and
> status-preservingly, **AND its FORCE is recognised** — what the utterance is *doing*, not merely
> what it is about.

This is not hypothetical: it is exactly the failure the conditional probe found in the wild. `a lion
is dangerous when a lion is hungry` parsed perfectly, mapped both halves to correct propositions, and
**asserted both** — because the grammar read content and had no notion that a conditional's halves are
not being asserted. Perfect content mapping, zero force. The suppression gate (`<cat> suppresses`) is
a force mechanism arrived at before force had a name here.

**Two limits of the definition, recorded so they are not discovered later.** (1) It is INDEXED TO A
REPERTOIRE — understanding is relative to the form set held, which is the evidentiality point
(§6) applied to ourselves. (2) It is PROPOSITIONAL understanding, not grounding: `has(lion, mane)`
maps correctly while `mane` stays an uninterpreted token. That is a scope, not a defect — but the
word "understanding" will invite the objection, so claim the narrow thing.

## 9. CLOSURE UNDER COMPOSITION — the set must be an algebra, not a checklist (user, 2026-07-22)

**THE PROPERTY.** §4 asks whether each fundamental block can be REPRESENTED. §8 upgrades that to
whether it can be UNDERSTOOD (mapped, unambiguously, status-preservingly). Both are per-block. Neither
catches the failure a *combination* of blocks produces. A set of blocks can be individually perfect
and still not compose — so the property this section adds is:

> The fundamental blocks are CLOSED under composition iff every legal composition of them lands in
> {reasoned-over correctly} ∪ {explicitly refused}, and NEVER in {silently mis-mapped}.

This is the useful half of a mathematical analogy, and the analogy must be stated at its real
strength and no more. It is **closure**, not a **group**: there are no guaranteed inverses (asserting
then denying is not identity — it is a contradiction the revision loop must handle), and composition
is **not commutative** (hedge-of-negation is not negation-of-hedge). The right picture is a **field
with a defined division-by-zero**: refusing a composition we cannot yet reason over is CLOSED —
understanding includes knowing you cannot (§8). Only the SILENT mis-map — an unsaid ink fact, a wrong
answer, certainty manufactured from an uncertain premise — violates closure. Composition is a TOTAL
classification (every combination gets a verdict), never a total FUNCTION (not every combination
reasons).

**CLAUSE 3 — "reasoned-over", the operational upgrade of §8.** The conditionality probe (§4a) is why
this is not pedantry: the mechanism existed, the surface mapped, the query answered `yes` — and it was
right only by name-resolution luck, with the derived fact on the discourse token. Mapping is not
reasoning. So a block is NAILED DOWN iff (1) it is representable, (2) surface→block maps unambiguously
and status-preservingly, AND (3) *assert-it, then ask a query that cannot be answered without
reasoning over it, through the real `ingest`, and get the right answer with the right epistemic kind.*
Clause 3 is what `bench/spike_epistemic_closure.py` measures.

**MINIMALITY AND COMPOSABILITY ARE IN TENSION, AND COMPOSABILITY WINS.** The re-point's goal
("minimum form set") is under-specified as stated. A *truly minimal* set expresses some concepts as
compositions of others; if those compositions leak, minimality has bought an unsound system.
Sometimes ADDING a primitive is what makes the algebra close. So the objective is not the smallest
count — it is:

> the SMALLEST set that is CLOSED under composition **and** covers the corpus.

The closure constraint can legitimately force the set LARGER. (NSM's ~65 primes, §6, are chosen for
*definitional closure*, not raw minimality — the same tension, resolved the same way.) The
consequence for method: **composability must GATE the choice of a block's representation, not merely
validate it afterward.** A representation that cannot compose is the wrong representation even if it
covers its concept perfectly in isolation.

**AND CLOSURE MUST HOLD AT ARBITRARY DEPTH — which is a firmware demand, not a form demand.** Pairwise
closure does not imply depth-n closure. There are TWO kinds of depth and they behave oppositely; the
probe measures both.

- **DERIVATIONAL depth (chaining / subgoals) is mechanically arbitrary, and this is SETTLED.** A chain
  of rules reasons to its tail (measured: depth 5), and — the load-bearing part — an UNCERTAIN root
  PROPAGATES its band through the chain without hardening into certainty (measured: `likely` preserved
  through a depth-3 chain under a banded ask). This is the axis the subgoal stack already covers: the
  ISA-control-machine arc de-recursed the NAF subgoal chain onto an explicit stack, proven on a
  601-deep closure under `recursionlimit` 200, so depth here is not Python-recursion-bound.
- **REPRESENTATIONAL depth (nesting operators structurally) is NOT closed, and it fails at depth 2.**
  `the lion generally has no mane` — a hedge OVER a negation — parses to a span carrying both an
  `hclause` and a `negator`, routes `fact` (a SUCCESS verdict), and commits NOTHING: no ink, no band.
  Negation alone works (`lion has_not mane`); hedge alone works (band 0.75); composed, they silently
  drop. That is §8's recognized-not-understood at depth 2, so depth-n nesting is a fortiori not
  closed. **The subgoal stack cannot help, because the failure is at INTAKE — before any subgoal is
  raised.**

**THE UNIFYING THESIS, and the probe is direct evidence for it: closure-at-depth ⟺ ONE uniform
evaluation mechanism.** The two composition results are not a mixed verdict; they are the same law
seen from both sides.

- `conditional ∘ degree` **PASSES** (band propagates to `likely`, and keeps propagating through a
  depth-3 chain) **because `chain_sip` under a banded policy is a SINGLE mechanism** that spans
  degree and conditionality — it evaluates the rule over the banded premise as one recursive fold.
- `degree ∘ negation` **LEAKS** **because it is TWO mechanisms** — hedge as a fork/band written at
  the interpretation layer, negation as `has_not` written by the fold — meeting at intake with no
  shared production for the nest.

So "do subgoals allow groups at arbitrary depth?" and "is the set composable?" are the SAME question
asked at the firmware level. Depth-n composition stays sound only if band, scope, force and negation
are **composable annotations on one evaluation**, not N mode-specific drivers handing off to each
other — because with N drivers every new pair is a new integration and depth explodes
combinatorially. The design target this yields: **evaluate every fundamental block through one
mechanism.** That is also the precondition under which closure could stop being an empirical probe
and become a PROVABLE property (below).

**HOW YOU WOULD PROVE IT INSTEAD OF PROBING IT — leads, uncited per §6's discipline.** Formal systems
that GUARANTEE closure all do it the same way: they FREEZE the language first, so closure is a theorem
proved once rather than a property tested. This maps exactly onto §4d's settled decision that
*structure must not grow at runtime while vocabulary may* — freezing the structure is the precondition
that makes the theorem reachable.
- **Conservative extension / module extraction** (Description Logics, OWL) — "does adding this piece
  change any entailment over the old vocabulary?" The formal cousin of "a new block does not corrupt
  the old ones."
- **Cut-elimination / logical harmony** (Prawitz, Dummett; proof-theoretic semantics) — each
  connective's introduction/elimination rules must "fit" so combinations cannot derive garbage. The
  theoretical cousin of "no LEAK under composition."
- **The gradual guarantee** (gradual typing) — a system mixing a precise and an imprecise mode proves
  that mixing DEGRADES PREDICTABLY rather than silently. Structurally identical to "certain-from-
  uncertain is a LEAK".
- **Possibilistic / many-valued logics** (possibilistic logic; Belnap's 4-valued) — DO define
  composition over degrees and truth-gaps, but as a FIXED algebra, not a runtime-extensible set.

None of these offers a runtime check for an OPEN, heterogeneous operator set, because such systems
refuse to be open. Until UGM's structure is frozen and a single evaluation mechanism is in place,
`bench/spike_epistemic_closure.py` is the honest empirical stand-in for the theorem.

**WHAT THE PROBE FOUND ON ITS FIRST HONEST RUN (2026-07-22), stable across two identical runs.**
8 PASS, 3 REFUSED (closed), **1 LEAK**, 0 UNKNOWN.
- REASONED-OVER end to end: certainty, negation (a HARD `no`, not merely assumed), degree (banded ask
  → `likely`), conditionality (derived AND in scope — the by-luck bug stays fixed).
- CLOSED by honest refusal: attribution (no surface yet), quantification (partial), `conditional ∘
  negation` (the ink rule does not fire on a negated premise — conservative, not reasoned).
- **THE ONE LEAK: `degree ∘ negation`**, the depth-2 nest above. It is the exact analogue of the
  use-mention defect `spike_force_coverage.py` found — a composition that the system reports SUCCESS
  on while representing nothing. A probe measuring reasoning found it where a coverage probe measuring
  parsing could not.

**CONSEQUENCE FOR THIS INVENTORY.** §4's tables gain an implicit second question per row: not only
"is it represented?" but "does it COMPOSE — at depth, through one mechanism?" The residue log (§5) is
the discovery process for what the set CONTAINS; the closure probe is the discovery process for
whether the set is an ALGEBRA. **A set cannot be called "discovered" until it is shown closed under
composition at depth** — an unclosed set is, precisely, still missing something structural (a
representation choice to revise, or a primitive to add). Coverage and closure are not two work items;
they are one, and closure is the gating half.

### 9.1 The composition redesign is TWO capabilities, not one — annotation vs binding (2026-07-22)

**A MACHINE-LAYER AUDIT (intake deliberately excluded) split the composition problem cleanly in two,
and the split is the whole result.** The question "make the blocks compose through one mechanism"
turned out to conflate two architecturally independent things, and keeping them fused is how the
redesign would have tumbled.

**(1) ANNOTATION composition — WITHIN a fact.** band, negation, scope. Measured at the fold: these are
UNARY, LOCAL tags and the POSITIVE side of evaluation already composes them uniformly — band
propagates through a rule to depth 3 (`likely` preserved), a fork simply IS a scope with a
`<likeliness>`, a banded positive reads correctly. **The one leak is an ASYMMETRY, not a silo: the
NEGATIVE evaluation path is second-class.** `check`'s `ENTAILED_NEG` is crisp-only (its own docstring:
"a graded hard-negative is out of slice"), VERIFIED at the machine layer with no intake — a fork
`has_not(lion,mane)@0.75` reads `possibility=0.75` (representation composes) but `check` under a banded
policy answers `assumed-no`, dropping the band, where the positive twin answers `likely`. So annotation
composition is a SURGICAL target: carry the band on the negative read the way the positive read
already does. It fixes `hedge∘negation` and `conditional∘negation` in one place, and — because it is
within-fact — it is safe to do INDEPENDENTLY of (2).

**(2) BINDING / relating — ACROSS facts.** This is where the unbuilt shape-classes live, and they are
NOT annotations. Each demands the fold RANGE or JOIN across a dimension the annotation frame has no
primitive for:

| block | dimension it binds across | native binder today |
|---|---|---|
| tense | an ORDERED index (change joins a fact at *t* with one at *t+1*) | none — the rule `?x` is unordered set-membership, not arithmetic-over-index |
| quantification | a variable over a SET, with scope/dependency (nested ∀∃), + existential witnesses | UNIVERSAL only, and only inside a rule body |
| causation | an EDGE BETWEEN FACTS (+ interventional/counterfactual) | provenance relates DERIVATIONS; ontological cause unverified |

**The only binder that exists is the rule layer's universal `?x` over ENTITIES** — which is exactly
why the partially-covered cases (universal quantification; derivation-as-cause via provenance/`<j:>`)
are the ones that ride the rule layer, and the uncovered cases are the ones needing a binder it does
not provide.

**⭐ THE CARD-CASTLE RESULT: three scary open blocks reduce to ONE question about ONE mechanism —**
*can the rule layer's binder generalize: to an ORDERED INDEX (tense), to EXISTENTIAL/COUNTED/NESTED
(quantification), to ranging over FACTS not entities (causation)?* This is the assumption a
"one annotation protocol" redesign would silently bake in, and the one those three would later break.
Deciding it BEFORE the redesign is what prevents the tumble.

**Settled decisions already pre-constrain the binder, and asymmetrically:**
- **tense** is the hardest: identity is fine (VERIFIED — scope lets the same S-P-O coexist under two
  indices), but scope semantics are EPISTEMIC (a possibility overlay) where a time index is
  ONTOLOGICAL, AND the event-reification route is CLOSED by the no-labeled-edges / no-Davidsonian
  decision ([[spo-directed-path-no-labeled-edges]]). Two of three routes shut.
- **quantification**: universal is NATIVE; existential witnesses collide with no-RHS-skolem /
  no-predicate-invention ([[skolem-minting-lhs-keyed]]).
- **causation**: most tractable — the substrate already reifies facts (rel-nodes) and relates them
  (provenance), and counterfactuals have a home (`SUPPOSE`). The gap (an ontological edge between
  fact-nodes) is structurally plausible but UNVERIFIED (a probe-tooling error left it unmeasured).

**THE DE-RISK FOR THE REDESIGN.** Frame it as the two capabilities above and DO NOT let #1 silently
claim #2. #1 (annotation composition) is correct as a per-fact frame and nearly closed; do it now. #2
(binding) is an explicit DECISION — generalize the rule binder along those axes, or declare the
shape-classes that need it OUT OF SCOPE as a stated ceiling (§7-style honest bound). The value of the
stress-test is that it pulled that decision into the open instead of leaving it as an assumption.
**The in-scope/out-of-scope decision itself is §9.2 (open).**
