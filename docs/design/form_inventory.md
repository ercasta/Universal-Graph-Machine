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
| conditionality | *a lion is dangerous when a lion is hungry* | the rule layer (`load_machine_rules`) | needs the genericity call (`det` slot); suppression built |
| genericity | *a lion* vs *the lion* | `det` slot | one declaration line, probed |

### Fundamental — NO MECHANISM

| form | example | note |
|---|---|---|
| tense | *were formerly found … now confined to* | nothing exists. Expensive. |
| exclusivity / *only* | *confined to Africa* | CWA/NAF exist; no surface, and no way to say "only" |
| quantification | *all the varieties*, *some naturalists* | partial |
| causation | *indebted to*, *therefore* | nothing |
| resemblance-in-a-respect | *resembles a cat in his mode of stealing* | distinct from `is_a`; conflating them produced a real distortion (Loudon 39). cf. Brachman, "What IS-A is and isn't" |

### Baroque — desugar, never represent

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

**Two limits of the definition, recorded so they are not discovered later.** (1) It is INDEXED TO A
REPERTOIRE — understanding is relative to the form set held, which is the evidentiality point
(§6) applied to ourselves. (2) It is PROPOSITIONAL understanding, not grounding: `has(lion, mane)`
maps correctly while `mane` stays an uninterpreted token. That is a scope, not a defect — but the
word "understanding" will invite the objection, so claim the narrow thing.
