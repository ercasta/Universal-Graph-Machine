# The Logic Fragment — what formal logic this system actually needs

> **Status: CANONICAL (2026-07-07, ratified in conversation with the user).** Given the
> decisions in force (CWA-default, bounded-defeasible semantics, brain-firmware direction —
> see `docs/reference.md`), this document fixes WHICH pieces of formal logic the system
> genuinely needs, which are replaced by "swiss-knife" system-2 procedures, and what that
> implies for the CNL authoring surface. **Backward compatibility with prior semantics is
> explicitly NOT a constraint** (user, 2026-07-07): the system is a stratification of research
> generations; this fragment is the going-forward contract.

## The stance

The system is NOT a theorem prover for an expressive logic. It is a **bounded, serial,
defeasible reasoner over a deliberately small fragment**, chosen to match (a) what CNL/KB
authors — business people, not logicians — actually write, and (b) what human system-2
deliberation actually does: chain rules forward, handle exceptions, enumerate small candidate
sets, compare, prefer, count via a calculator. Formal semantics are kept as **anchors** (each
mechanism corresponds to a known, well-understood formalism) — not as machinery to implement in
generality. Sequent calculus, natural deduction, resolution: these are proof-*search* formalisms
for arbitrary formula spaces. This system never searches an arbitrary formula space — its
derivations ARE forward/demand chains, and the provenance journal is already the proof object
(a derivation tree, which in this fragment is all the proof theory there is).

## What the system NEEDS (the fragment, with its anchors)

Each row: the mechanism, the formal anchor that makes it respectable, and the firmware/bank
realization.

1. **Definite (Horn) rules, conjunctive bodies.** The core. Anchor: least-fixpoint semantics of
   Datalog. Realization: APPLY/CHAIN firmware over reified rules; materialized facts are the
   memo table; `<demand>` nodes are magic-sets made literal.
2. **Stratified negation-as-completion.** `not P` answered by bounded enumeration of the
   demanded extension. Anchor: perfect-model semantics for stratified programs; the
   boundedness relaxation is licensed by CWA-default — an unprovable goal is a DEFEASIBLE
   `assumed-no`, not a theorem (`decision-cwa-default`; per-predicate OWA opt-in yields
   `unknown`). Consequence: exhaustive completeness is NOT promised; effort is a metareasoning
   dial. Stratification must be checked (lint at load, not discovered at runtime).
3. **Defeasible rules with priorities — deliberately WITHOUT contraposition.** Defaults,
   exceptions, overrides ("today's instruction outranks standing policy"). Anchor: defeasible
   logic (Nute; Governatori's variants), which also drops contraposition on purpose — matching
   both business usage and human reasoning. Realization: defeat/priority rules in banks;
   PREFER firmware arbitrates.
4. **Deontic statuses as reified predicates with a ranking.** `forbidden < discouraged <
   permitted < encouraged < obligatory` as ordinary graded/ranked facts about acts. Anchor:
   the defeasible-deontic fragment (LegalRuleML-shaped). NO modal-logic machinery: no nested
   modalities, no possible worlds — a status is a fact, an override is a defeat rule. The
   card-trader corpus is the existence proof.
5. **Equality as DECLARED congruence, not paramodulation.** `same_as` classes propagate only
   through KB-declared predicates. Anchor: congruence closure restricted to a declared
   signature. Realization: the coref-follow walk, selected by declarations (never engine
   sniffing — `feedback-no-hardcoded-engine-policy`).
6. **Existential witnesses as labelled nulls.** "There is a manager who…" mints a witness
   constant. Anchor: the chase / Datalog± existential rules. NO quantifier alternation, ever:
   ∀ is a rule, ∃ is a witness, and nothing nests beyond that (`decision-existentials`,
   `decision-universals-to-laws`).
7. **The graded layer.** Degrees in [0,1], t-norm conjunction, α-cut acceptance. Anchor:
   possibilistic logic (Dubois–Prade), NOT probability — no normalization, no posterior
   claims. Preference among valid matches lives here; truth does not.
8. **Calculators at a declared seam.** Arithmetic, aggregation (count/sum/max), temporal
   windows and deadlines, optimization, and genuinely disjunctive global constraints go to
   `<call>` tools (clingo where combinatorial). Anchor: stratified Datalog-with-aggregates
   puts aggregation OUTSIDE the rule fragment for good reasons; we follow it. NOTE: aggregation
   and temporal are NOT edge cases in business rules — they are bread and butter ("if total
   exposure exceeds X", "within 30 days") — so these two calculators are FIRST-CLASS, with
   dedicated CNL forms, not an escape hatch.

## What the system does NOT need (and must not grow)

- **Sequent calculus / natural deduction / resolution.** Proof search over arbitrary formulas.
  Nothing here ever needs it; the journal-as-derivation covers explanation.
- **Contraposition.** Authors who write "birds fly" do not mean "non-flyers are non-birds";
  defeasible logic formalizes exactly this refusal. Entailed negation comes ONLY from declared
  disjointness (`entailed_negation_rules`), never from flipping rules.
- **Disjunctive conclusions in general.** "A or B holds" as a derived fact (disjunctive
  Datalog/ASP expressiveness) is not supported in the substrate. What IS supported: bounded
  **elimination over a closed, declared candidate set** — the riddles mechanism — which is
  system-2 case-analysis, not disjunctive model theory. A rule wanting more calls clingo.
- **Proof by contradiction / refutation.** Conflict is handled by DEFEAT (priorities), not by
  deriving ⊥ and backtracking a world. There is no world to backtrack — facts are monotone.
- **Full FOL unification.** Matching binds node instances against attribute patterns; there
  are no function terms to unify, no occurs-check, no most-general unifiers.
- **Paraconsistency machinery.** Contradiction between rules = a defeat question (which rule
  wins); contradiction between facts = a coref/quantification question
  (`decision-quantification-coreference`). Neither needs a paraconsistent logic.
- **Model counting, abduction-in-general, higher-order anything.**

## The system-2 swiss-knife inventory (what replaces the missing logic)

The universal firmware procedures — each simple, iterative, bounded, and human-legible:

| Trick | Replaces | Firmware |
|---|---|---|
| Chain forward from what you know | modus ponens over Horn | APPLY/CHAIN |
| "Did I find any? No → assume not" | negation, CWA | COMPLETE (bounded) |
| Exception-first: default unless overridden | nonmonotonic logics | defeat rules + PREFER |
| Try each candidate in turn, strike out losers | disjunction over closed sets | elimination walk |
| Compare on a graded dimension, take the best above α | preference logics | PREFER/SELECT |
| Mint a placeholder for "someone" | existential quantification | witness MINT |
| Treat these two as the same, where declared | equality reasoning | coref-follow walk |
| Count/sum/compare numbers → use the calculator | arithmetic in logic | `<call>` seam |
| Look further only if it matters | proof search control | walkers + fuel (metareasoning) |

## The business-rules thesis (user, 2026-07-07) — assessment

**Thesis:** real-world business rules use a far simpler fragment than formal logic offers, and
CNL authors think in system-2 tricks, not formulas; the forms above cover what business rules
actually express.

**Assessment: substantially correct, with two amendments.** Supporting evidence from deployed
practice: production-rule engines (Drools/ODM: Horn + NAF + priorities) run a large share of the
world's operational business logic; DMN decision tables succeeded industrially with a
deliberately tiny expression language; OWL 2's EL profile (a small Horn-like fragment) suffices
for the largest real ontologies (SNOMED CT); SBVR and LegalRuleML both landed on
defeasible+deontic fragments for regulation. Psychology agrees: people reason over cases,
witnesses, and exceptions (mental-models tradition; the Wason task shows material implication is
not native, while deontic framings of the same task are easy). The full spectrum of FOL formulas
is writable but unwritten — nobody authors quantifier alternations.

**Amendment 1 — aggregation and temporal are core, not peripheral.** The fragment intuition
"simpler than logic" is right, but real rule books are FULL of sums, counts, thresholds,
deadlines, and windows. If these stay awkward, authors will fail on their FIRST realistic
policy, not their hundredth. Hence §8 above: first-class calculator forms.

**Amendment 2 — layered exceptions need tooling, not expressiveness.** The place real rule
books get hard is not the logic, it is CONSISTENCY: dozens of overrides whose priority order
was never stated. The fragment handles this (priorities are data), but the AUTHORING system
must lint it: detect conflicting rules with no declared superiority, surface them as questions.
This is a lint/interaction feature, not a logic feature — and it is where this system can beat
both Drools (which silently uses salience) and formal logic (which calls it inconsistency and
stops).

## Authoring consequence

The CNL surface should present the fragment natively and REFUSE the rest loudly:

- Forms map 1:1 to the fragment: `IF…THEN` (Horn), `…unless…` / `X outranks Y` (defeasible),
  `it is forbidden to…` (deontic), `there is a…` (witness), `exactly one of…` (closed-set
  elimination), `the total/number of…` (aggregation calculator form), `within N days`
  (temporal calculator form).
- The linter's contract: a sentence outside the fragment gets a NAMED rejection with the
  nearest in-fragment alternative or the calculator suggestion — the fragment boundary is a
  feature (predictable semantics) and must feel like one.
- Decision-table-shaped input (the DMN lesson) is a natural bulk-authoring form: rows lower to
  Horn+priority rules mechanically.
