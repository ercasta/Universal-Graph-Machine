# The Inference Inventory — epistemic RULE forms and their fixed lowering

> **Status: companion to `form_inventory.md` (user question, 2026-07-20).** That document asks *what
> kinds of commitment can an utterance carry*. This one asks the dual: **what kinds of inference can
> a rule perform**, and is that set finite, composable, and lowered by a predetermined mapping.
>
> Read `form_inventory.md` first — §1's test is reused here verbatim, on a different axis.

## 1. The question, and the premise that needed correcting

> *"Would it be possible to define a finite, composable set of epistemic rule forms, whose lowering
> to ISA is predetermined, instead of creating custom lowering for each rule form the grammar can
> express?"*

**The premise is half wrong, and the half that is wrong is the encouraging half: there is no custom
lowering per grammar form, and there never was.** `assert_bank` is a rule GENERATOR, not a lowering
extension. `clause asserts subj pred obj when guard` compiles to ordinary `Rule` objects which go
through exactly the same lowering as a hand-written domain rule. The generator branches — `ask`/
`goal`/`command` emit no rule at all, `hedges` emits `Band` rules, `denies` takes the `neg_of` hop —
but every branch lands in the SAME fixed lowering.

Verified structurally, not assumed: `lowering.py` has one lowering function per DECLARED RULE FORM,
and its dispatch is over the `Rule` dataclass's own fields (`for c in rule.graded`, `for b in
rule.bands`, …). Nothing in it mentions a grammar category, an assertion verb, or a form key.

**So the inventory the question asks for already exists. What it lacks is being NAMED, CLOSED, and
JUSTIFIED** — which is precisely what `form_inventory.md` did for the utterance side, and precisely
why the force axis then became cheap to extend.

## 2. The inventory

The `Rule` dataclass **is** the inventory. Each row is a declared form with a predetermined lowering
to a fixed opcode alphabet.

| # | inference form | `Rule` field | lowering | ISA opcodes |
|---|---|---|---|---|
| 1 | positive premise / join | `lhs` | `lower_lhs` → `lower_conj` | `SEED` `FOLLOW` `TEST` `MEMBER` `OVERLAY` |
| 2 | negation as failure | `nac` | `lower_nac_programs` | separate programs + match-time filter |
| 3 | degree premise (α-cut) | `graded` | `lower_graded` | `GRADE` |
| 4 | value join | `value_matches` | `lower_value_matches` | `VMATCH` |
| 5 | distinctness | `distinct` | `lower_distinct` | `DISTINCT` |
| 6 | conclusion (assert) | `rhs` | `lower_rhs` | `MINT` `EMIT` |
| 7 | graded / scoped conclusion | `bands` | `_lower_bands` | `MINT` + graded attrs, scope pen |
| 8 | aggregation | `propagate` | `lower_propagate` | `EMIT` |
| 9 | retraction | `drop` | `lower_drop` | `SWEEP` `REDIRECT` |

Everything else on `Rule` is a KNOB or a DECLARED ROLE, not an inference form: `probability`,
`priority`, `max_steps` (scheduling/confidence), `meta` and `learned` (roles read by TMS and by
`learned_support`). They change no inference *shape*.

**Composition is by conjunction and by fixpoint**, both already fixed: conditions AND within a rule,
rules compose into derivations through `run_bank`'s stratified fixpoint. No rule form composes with
another by a special case.

## 3. The test, transferred

`form_inventory.md` §1 asks whether a construction can be paraphrased into existing forms *without
changing what the system believes*. The dual:

> An inference shape is **FUNDAMENTAL** iff it cannot be paraphrased into the existing rule forms
> **without changing what the system can CONCLUDE**. Otherwise it is sugar over them.

**This test has already been operating informally, and its verdicts are on record — which is the
main evidence the inventory is real rather than imposed:**

- **`Band` — judged FUNDAMENTAL, added.** "A triple-only RHS could not write a graded attribute at
  all, which is why the whole possibilistic representation was unreachable from rules." No
  paraphrase existed; the conclusion-kind was unreachable.
- **`MINT.key_reg` — added by COMPLETENESS reasoning over a closed set.** The argument was that the
  mechanism "existed on `EMIT` but not `MINT`". **That argument is only coherent if you already
  believe you are looking at an inventory** with cells that can be empty.
- **Predicate INVENTION — judged fundamental and deliberately WITHHELD.** `lower_rhs` accepts an
  LHS-bound predicate variable and still rejects an RHS-only one, on the stated ground that
  inventing one "is predicate INVENTION … deliberately NOT smuggled in through the lowering."
- **The DENY collapse — the clearest case of the question's own thesis.** `assert_bank` generated
  one rule PER LEXICON WORD because the head predicate was a string derivation and the ISA has no
  string ops (133 → 61 rules). The repair was to put the positive/negative pairing in the graph as
  DATA so the rule could BIND the negative instead of computing it: 61 → 32, no expressiveness lost.
  **That is exactly "we lacked the right composable primitive, so we generated N variants," and the
  fix is exactly "express it once by composition."**

## 4. The ceiling — what is deliberately NOT lowerable

Recorded because a closed set is only meaningful if its complement is stated. `lowering.Unlowerable`
is the loud wall.

| excluded | status |
|---|---|
| predicate invention (RHS-only predicate variable) | rejected on principle; the `predicates-are-keys` learning primitive stops short of it |
| inverted graded condition (*"not at all"*) | "a later slice" — raises `Unlowerable` |
| materialized-positive NAC lowering | "a later slice" — raises `Unlowerable` |
| string operations on predicates | absent by design; the DENY collapse is what you do instead |

## 5. Where the analogy to `form_inventory.md` BREAKS

Recorded so the companion is not read as a stronger claim than it is.

- **The finiteness arguments are not the same kind.** The grammar's rests on epistemology — kinds of
  *commitment* are plausibly bounded. Here the equivalent claim is that kinds of *inference* are
  bounded, which is far stronger. It is defensible in THIS system only because it deliberately is
  not a general theorem prover (stratified negation, fuel budgets, honest UNKNOWN, demand-driven
  negation). **That is a design choice being leaned on, not a discovered fact.**
- **"Composable" means something different on each axis.** Grammar productions compose into
  unbounded SENTENCES; rule forms compose into unbounded DERIVATIONS. The second is where
  undecidability lives — which is why stratification and `max_rounds` exist. A clean inventory does
  not dissolve that, and should not be sold as if it might.
- **Lowering was never the expensive part.** The costly defects of the grammar arc were about which
  LAYER a fact lands in, bank idempotency, and join order. None would have been prevented by a
  better rule-form inventory. Same conclusion the parser-rewrite discussion reached: the pain was
  epistemic and semantic, not mechanism.

## 6. What this document is FOR

Not performance, and not a refactor. Its value is that **"should we extend the lowering for X?"
stops being a case-by-case judgement and becomes a test against a stated set** — with §4's
exclusions as the standing answer for the cases already decided.

The precedent is direct: force was cheap to extend the moment §4b wrote the axis down. Three verbs
(`asks` / `intends` / `commands`) then landed as table entries plus declarations, because the
question "is this a new mechanism or a new entry?" had an answer to check against.

**Falsification, so this is not a taxonomy exercise:** the inventory is adequate when a corpus of
reasoning tasks yields zero "we had no rule form for it" entries — the same stopping criterion
`form_inventory.md` §5 uses. Until such an audit is run, §2 is a description of what exists, not a
demonstration that it suffices.

## 7. Lead worth checking, NOT a citation

This is close to what the Datalog± / existential-rules literature calls choosing a **fragment**:
stratified negation + existentials (value invention) + aggregation is a well-studied fixed set with
known decidability boundaries. **Treat as a search query, not a fact** — `form_inventory.md` §6
carries the same warning about unverified leads, for the same reason.
