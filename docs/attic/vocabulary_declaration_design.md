# Vocabulary declaration — design (Phase 2.5)

> **Status: DONE / AS-BUILT (2026-07-11, 342 passed/1 skipped).** Crux §7 was ratified by the user:
> **"consolidate"** (Tier 1 = fixed substrate vocabulary centralized in `ugm/vocabulary.py`, NOT genuinely
> KB-declared). The migration below ran as specified with ONE refinement recorded in §Migration/As-built:
> Tier-2 coref de-hardcoding derives predicates content-blind via `relation_predicates(graph)` (relations
> in play) rather than declared-relations-only, which is the faithful additive-coref analog AND handles
> the default-grammar predicates (`in`/`has`/`before`). See `CHANGELOG.md` (Phase 2.5 entry) for the
> as-built summary. The active plan is `implementation_plan.md`; companion of `name_demotion_design.md`
> (Phase 2.3).

## The problem — logic-vocabulary strings hardcoded in engine code

The engine's reasoning modules hardcode English predicate strings as Python constants, and several are
DUPLICATED across modules:

- `COPULA = "is"` — defined FOUR times: `decide.py:47`, `goal.py:76`, `check.py:39`, `cnl/query.py:36`.
- `NEG_COPULA = "is_not"` — `decide.py:48`, `goal.py:77`.
- `NEG_SUFFIX = "_not"` — `goal.py:78`; `check._neg_pred` hardcodes `f"{pred}_not"` independently.
- `CWA = "<closed_world>"`, `CLOSES = "closes"` — `decide.py:45–46`.
- `SAME_AS_RULES = same_as_rules(["is_a", "is", "target", "type"])` — `cnl/universal.py:71` (a hardcoded
  default predicate list).
- `_COREF_PREDS = {"is_a", "is", "wants", "in", "has", "before", "target", "type", "disjoint_from",
  "every_is_a", "is_unique", "rel_property", "closes"}` — `cnl/authoring.py:218` (the moved
  `session.CONTENT_PREDS`, the Phase-5.4b tracked residual **B**). **This mixes substrate and domain
  vocabulary** — the core leak.
- `entailed_negation_rules` (`cnl/universal.py:106–109`) emits literal `"is"`/`"is_not"`/`"is_a"`/
  `"is_a_not"`.
- `DEFAULT_COPULA_SYNONYMS = ("are",)` — `cnl/forms.py:176` (lexical morphology `are`→`is`).

Grep count: ~69 logic-vocabulary string literals across 12 files (`is`/`is_not`/`is_a`/`same_as`/
`disjoint_from`/`_not`). Not all are leaks — see the three-tier split below.

## The KB-vs-engine boundary — three tiers

The judgment Phase 2.5 needs is *which* of these strings are a leak. They are not all the same kind of
thing. Three tiers:

### Tier 1 — SUBSTRATE / logic-fragment vocabulary (FIXED, engine-intrinsic)
The closed logical vocabulary `logic_fragment.md` fixes — universal to EVERY KB, not domain-specific.
`logic_fragment.md` §5 already treats `same_as` as a fixed distinguished predicate (declared congruence);
the same status extends to the membership/negation/subsumption primitives:

  - `is` (copula / membership), `is_not` (negated copula), `_not` (the `R`→`R_not` negation-naming
    convention), `is_a` (subsumption), `is_a_not`;
  - `same_as` (congruence), `disjoint_from` (→ entailed negation);
  - `closes` + `<closed_world>` (CWA policy marker), `rel_property` (relation-property declaration),
    `every_is_a`, `is_unique`, `transitive`, `transitive_closure_of`;
  - provenance `proves`/`uses` (already centralized as `_INERT_NAMES`).

These are NOT domain vocabulary — no KB "declares" its copula any more than it declares its `same_as`.
The defect is that they are **scattered and duplicated magic strings**, not that they are hardcoded per
se. **Disposition: consolidate into ONE canonical source of truth** (`ugm/vocabulary.py`), imported
everywhere. After this, each substrate string appears ONCE, as the declared substrate vocabulary — which
is what "grep-clean" should mean for Tier 1. (See §7 for the alternative reading — genuinely KB-declaring
the copula — and why this doc recommends against it.)

### Tier 2 — DOMAIN vocabulary (OPEN, KB-declared — the real leak)
Predicates the engine has NO business knowing: `wants`, `in`, `has`, `before`, `target`, `type` — the
domain entries in `_COREF_PREDS` and `SAME_AS_RULES`'s default list. The engine already has the right
hook: `_coref_propagation` (`authoring.py:222`) unions `_COREF_PREDS` with `declared_relations(graph) |
declared_prepositions(graph)`. **Disposition: the domain predicates come SOLELY from the KB's declared
relations; the engine constant keeps only Tier-1 substrate predicates** (which always compose across
coref). So `_COREF_PREDS` splits into `SUBSTRATE_COREF_PREDS` (Tier 1, fixed, → `vocabulary.py`) + the
KB-declared relations already read at load time. `SAME_AS_RULES`'s default list similarly reduces to
substrate predicates; `target`/`type` are reclassified (structural → Tier 1, or domain → dropped from
the default, TBD per §7 note).

### Tier 3 — CNL SURFACE grammar (STAYS literal — legitimately knows English)
Recognizing the English words "is" / "is a" / "are" in the tokenizer and grammar (`cnl/forms.py`,
`cnl/query.py` recognition, `cnl/universal.py` rule generation) is the SURFACE layer's job — it is the
natural-language lexicon, not reasoning policy. `DEFAULT_COPULA_SYNONYMS = ("are",)` is lexical
morphology. **Disposition: STAYS** — but every surface site references the Tier-1 canonical constant for
the CANONICAL predicate it folds to (so there is still one source of truth for the canonical name, and
the surface's English lexicon is clearly separated from the canonical vocabulary). The exit-gate
"engine grep-clean" applies to REASONING code (`goal`/`decide`/`check`/`demand`/`coref_walk`), NOT the
surface grammar (which is *allowed* to know English — that is its entire purpose).

## Proposed design

**Part A — consolidate substrate vocabulary (`ugm/vocabulary.py`).** A new leaf module (no intra-package
imports, so anything can import it without cycles) holding the Tier-1 constants + the derived helpers:

    COPULA = "is"; NEG_COPULA = "is_not"; NEG_SUFFIX = "_not"
    IS_A = "is_a"; IS_A_NOT = "is_a_not"
    SAME_AS = "same_as"; DISJOINT = "disjoint_from"
    CLOSES = "closes"; CWA = "<closed_world>"
    REL_PROPERTY = "rel_property"; TRANSITIVE = "transitive"; ...
    SUBSTRATE_COREF_PREDS = frozenset({IS_A, COPULA, SAME_AS, DISJOINT, REL_PROPERTY, CLOSES,
                                       "every_is_a", "is_unique"})
    def neg_pred(pred): return pred + NEG_SUFFIX          # the single R->R_not convention

Then replace the duplicate definitions in `decide`/`goal`/`check`/`query`/`universal` with imports from
`vocabulary`. `check._neg_pred` and `goal._neg_pred` both delegate to `vocabulary.neg_pred`.

**Part B — de-hardcode domain coref predicates.** `_COREF_PREDS` → `SUBSTRATE_COREF_PREDS` (Tier 1) at
its structural entries; `_coref_propagation` reads `SUBSTRATE_COREF_PREDS | declared_relations(graph) |
declared_prepositions(graph)`. The domain entries (`wants`/`in`/`has`/`before`) are DROPPED from the
constant — they must be present as declared relations for coref to compose them (verify against the
benches that they are; if a bench relies on an undeclared domain predicate composing, that is itself a
missing declaration to add in the harness KB, not an engine constant). `universal.SAME_AS_RULES` becomes
`same_as_rules(sorted(SUBSTRATE_COREF_PREDS))` or is removed in favour of the per-KB `_coref_propagation`.

**What explicitly does NOT change:** the CNL surface grammar's English lexicon (Tier 3); `same_as`'s
existing `coref_prop`-declared-role mechanism (Phase 5.4b already de-sniffed it); the `logic_fragment.md`
fixed-vocabulary status of these predicates.

## Migration steps (for the executing session)

1. Create `ugm/vocabulary.py` with the Tier-1 constants + `neg_pred`. Export via `ugm/__init__.py`.
2. Replace `COPULA`/`NEG_COPULA`/`NEG_SUFFIX`/`CWA`/`CLOSES` definitions in `decide`/`goal`/`check`/
   `query` with imports; delegate both `_neg_pred`s to `vocabulary.neg_pred`. (Behaviour-neutral — same
   strings, single source.)
3. Split `_COREF_PREDS`: Tier-1 entries → `SUBSTRATE_COREF_PREDS` in `vocabulary`; drop domain entries;
   point `_coref_propagation` at `SUBSTRATE_COREF_PREDS | declared_relations | declared_prepositions`.
4. Reduce `SAME_AS_RULES` / `entailed_negation_rules` literals to `vocabulary` constants.
5. Run the full in-repo suite after each step (342 baseline). The bench-sensibility half (card-trader /
   coref / ProofWriter) is harness-side — flag any coref-composition regression there for the harness KB
   to declare the missing relation, do NOT re-add a domain string to the engine.

**As-built refinement (step 3).** Dropping the domain entries and reading only `declared_relations |
declared_prepositions` regressed two in-repo tests (`test_isa_ask` CWA elimination, `test_new_core`
defeasible placement) — both need `in` to compose across coref, but `in`/`has`/`before` come from the
DEFAULT surface forms (`form.of`/`form.has`/`form.then`), not a `X is a relation` declaration, so
`declared_relations` never returns them. The fix keeps NO domain string in the engine but derives the set
content-blind: `SUBSTRATE_COREF_PREDS | relation_predicates(graph) | declared_relations | declared_
prepositions`. `relation_predicates(graph)` ("every relation predicate in play", already the blessed
driver of `same_as_rules` in tests) is the faithful additive-coref analog — the destructive merge shared
ALL of a mention's relations, so coref must compose over whatever relations are actually present. `in` is
materialized (by recognition) before `_coref_propagation` reads the graph, so both tests pass with zero
domain vocabulary named in the engine. This is stronger than the design's original "declared-relations-
only" reading and subsumes it.

## Exit gate

- Engine reasoning modules (`goal`/`decide`/`check`/`demand`/`coref_walk`) grep-clean of domain-predicate
  string literals; substrate predicates appear ONLY in `vocabulary.py` (single source).
- CNL surface may still name English words, but folds them to `vocabulary` canonical constants.
- In-repo suite green (342+); harness benches produce sensible coref/negation answers (run in `harneskills`).

## Risks

- **Import cycles.** `vocabulary.py` MUST be a leaf (stdlib-only) so `world_model`/`attrgraph`/`goal`/
  `cnl/*` can all import it. Verify no back-edge.
- **A bench relying on an undeclared domain predicate composing across coref** will regress when the
  domain entries leave `_COREF_PREDS`. That is a REAL missing declaration surfaced by the change — fix it
  in the harness KB (declare the relation), not by restoring the engine constant. This is the whole point
  of Phase 2.5, so expect one or two such surfacings.
- **Scope creep into Tier 3.** Do NOT try to de-string the CNL surface grammar — recognizing English is
  its job. Touch only reasoning code + the shared vocabulary source.

## §7 — Crux question — RATIFIED "CONSOLIDATE" (2026-07-11)

**RESOLVED: the user ratified "consolidate" — Tier 1 is fixed substrate vocabulary centralized in
`ugm/vocabulary.py`, NOT genuinely KB-declared. The recommendation below was adopted verbatim. Kept for
the rationale trail.**

**Is Tier 1 (`is`/`is_not`/`_not`/`same_as`/…) "fixed substrate vocabulary to CONSOLIDATE" (this doc's
recommendation), or should the copula be genuinely KB-DECLARED (a KB names its own membership predicate)?**

- **Recommendation: consolidate as fixed substrate vocabulary.** The copula is the logic fragment's fixed
  membership primitive, universal to every KB; `logic_fragment.md` §5 already treats `same_as` as a fixed
  distinguished predicate. KB-declaring the copula adds ceremony (every KB re-declares "is") with no
  benefit, and would ripple into the CNL surface (which must still recognize the English word "is"
  regardless). "Grep-clean" is satisfied by a single source of truth, not by parameterizing the copula.
- **The alternative** (genuine KB-declaration) only makes sense if the vision wants NON-English or
  swappable logical vocabulary (e.g. a KB whose membership predicate is a different token). If so, the
  design is larger: a `Vocabulary` object threaded through `GoalSolver`/`decide`/`check` (like `tools`/
  `open_preds`), and the surface grammar declares its lexicon→vocabulary mapping. Bigger, and only worth
  it if swappable vocabulary is a real goal.

The rest of the design (Tier 2 de-hardcoding, Tier 3 staying) holds under EITHER answer — only Tier 1's
treatment changes. Answer this, and the executing session runs §Migration.
