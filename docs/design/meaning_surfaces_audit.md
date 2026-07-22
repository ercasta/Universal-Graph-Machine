# Meaning-surfaces audit — "define X's meaning and use it", and where the sprawl is

> **Status: AUDIT (2026-07-22), then PARTLY BUILT.** Commissioned before adding a first-class
> *definition* surface. Method: read every meaning-giving surface + trace its live callers, not
> intuition.
>
> **BUILT 2026-07-22 (suite 873 green):**
> - **The QUOTE token `'?a`** (production_rule §QUOTE) — §5's "wall" removed *in the language*: a rule
>   writes a variable-bearing rule with quoted vars. `tests/test_quote_token.py`.
> - **The `define` surface** (`cnl/define_surface.py`, §4) — `define H as B` (sufficient rule) /
>   `define H iff B` (+ necessary direction via a shared-skolem witness), wired into the MAIN intake
>   (`Outcome("define")`), not a new loader. `tests/test_define_surface.py`.
> - **⭐ The META-PATTERN surface** (`define schema <trigger> : <template>`) — a user defines what a
>   relation-property MEANS as a rule template, IN THE LANGUAGE: `define schema ?r is transitive : ?a ?r
>   ?c when ?a ?r ?b and ?b ?r ?c`, then `ancestor is transitive` (a plain fact) materialises the
>   transitivity rule for `ancestor`. Quote-vs-bind principle: a template var in the TRIGGER is bound
>   (the parameter), one that is not is quoted. `compile_schema`/`apply_schemas`, wired on the fact
>   route (run forward + harvested when a triggering declaration lands; order-independent, idempotent).
>   `tests/test_schema_surface.py`. **This is the in-language replacement for the Python
>   relation-property expanders — the deepest form of "define meaning and use it".**
> - **⭐ Loader convergence LANDED 2026-07-22 (suite 886 green) — comparison converged, hedge deferred,
>   batch loader reimplemented.**
>   - **STEP 1 (§3 HIGH) — COMPARISON routes through `intake.ingest`:** an additive fallback route
>     (`Outcome("comparison")`) recognized by `parse_comparative`, keyword-gated (more/less/than) so it
>     never claims a plain fact, above the crisp fact route. MEASURED: the canonical grammar REFUSES the
>     surface, so it steals nothing (grammar KB reaches it by fall-through). Authors an ink relation
>     (transitivity on demand — no `rules` mutation), which SURVIVES later fact-path normalization.
>   - **⚠ HEDGE was tried on intake and REVERTED — a real finding.** A hedge authors a banded FORK
>     (family B), and a fork does NOT survive the fact path's whole-graph `normalize_surface` re-run on a
>     LATER utterance (measured: author a fork, ingest any fact, the fork reads back `assumed-no`). So a
>     hedge intake route silently corrupts — worse than none. This is exactly the §2 family-B composition
>     that "leave hedges/forks to scope generalization" refers to: forks must be unified INTO the kinded-
>     scope mechanism before they compose with the fact path. Hedge stays on `world.load_world`.
>   - **STEP 2 (§3 MEDIUM) — `load_corpus` is now ingest-in-a-loop** (kept its `(kb, rules)` signature,
>     per the "reimplement, keep signature" decision). ONE recognition/routing path (the same
>     `intake.route`), declare-before-use like a live session. Measured fallout: 2 tests
>     (`test_new_core`) that inspected rule-source GRAPH internals — now assert the `rules` LIST; one also
>     used the Stage-3 loose/lexicon-frame sugar, which the ingest path has no route for (that sugar is
>     superseded by the prose->CNL layer, and was already slated for retirement here). `load_world` folds
>     onto `load_corpus` for facts/rules/comparisons, authoring hedges LAST (forks can't interleave).
>   - Guard extended (`test_at_most_one_router_recognizer_claims_a_surface` +comparison surface) +
>     `tests/test_intake_loader_convergence.py`.
>   - **STILL OPEN:** retire `load_loose_rules` + the loose/translation subsystem (approved, but a
>     feature+subsystem deletion — deferred to its own focused slice rather than rushed at the tail of
>     this one). And hedge-on-intake awaits scope generalization absorbing family B.
> - **⚠ Perf note:** `apply_schemas` runs the meta-bank forward on EVERY fact assertion when any schema
>   exists (O(schemas) per fact; free when none). Correct but the O(session) shape this repo has fought;
>   gate on "the fact's predicate is a schema trigger" if a session with schemas ever bends.

## 0. The headline (so it is not re-derived)

1. **"Define meaning and use it" is NOT a missing engine primitive.** A definition's *sufficient*
   direction is an ordinary rule (`grandparent := parent∘parent` → `grandparent(alice,carol)` is
   POSITIVE); its *necessary/existential* direction is a bound-literal skolem head (given
   `grandparent(a,d)`, "someone a parents" and "someone parents d" are POSITIVE). Both NATIVE
   (binder spike E1/E2). **The gap is ergonomic**: no first-class biconditional-definition construct,
   and meaning-giving is scattered across many surfaces.
2. **The sprawl is TWO axes, and only one is bounded by the meta-wall:**
   - **Loaders (entry points): ~13 distinct `load_*`/`ingest`/`parse_*` functions.** Pure accretion —
     each feature grew its own CNL loader; the modern intake (`ingest`/`load_kb`) was meant to subsume
     them and comparative/uncertainty/corpus never migrated. **Fully collapsible. This is the real
     drastic simplification.**
   - **Expanders (declaration → rules): per-relation/per-dimension RULE GENERATORS.** Long assumed to
     be quote-wall-bound — **but §5 (corrected) shows the wall is already CLIMBED**: `learner.py`
     writes variable-bearing rules today. The expanders are Python §8 tools by pragmatic **choice**,
     not necessity. Collapsible in principle; whether to is a purity/extensibility call, not a
     capability one — see §5.

## 1. The table — meaning surfaces × {LOC, live entry, produces, can-be-a-rule?}

| # | Surface | Module (LOC) | Live entry point | Produces | Can be a *pure* rule? |
|---|---|---|---|---|---|
| 1 | Production / machine rules | `machine_rules` (210), `production_rule` | `ingest`→grammar route; `load_machine_rules` | `Rule` (sufficient-cond definition) | **IS a rule** |
| 2 | Forms (`form K : H when B`) | `form_authoring` (217) | `ingest` authoring cluster; `load_forms` | `Rule` over the token chain (a recognizer definition) | **IS a rule** (stable key is the only extra) |
| 3 | Relation-properties (`R is transitive`) | `rule_graph` (`_property_rule`) | **`expand_relation_properties` — TOOL, not in `ingest`** | declaration fact → generated `Rule`(s) | **Python tool BY CHOICE** — could be a rule-writing-rule (§5) |
| 4 | Category disjointness (`A disjoint from B`) | `rule_graph` (`_disjoint_rule`) | same tool | fact → generated contradiction `Rule` | **Python tool by choice** (§5) |
| 5 | Comparatives (`x more D than y`) | `comparative` (304) | **`load_comparative` — standalone, only `world.py`+tests** | `<comparison>` edge + generated per-dim transitivity `Rule`s + bespoke ask/explain/lint | transitivity generated (rule-able, §5); surface+bridge bespoke |
| 6 | Uncertainty / hedge (`x is likely P`) | `uncertainty` (221) | **`load_uncertain`/`load_line` — only `world.py`+`grammar`** | banded **FORK** (an epistemic SCOPE), not a rule | **N/A — it authors a SCOPE** (family B) |
| 7 | Universal reasoning (`is_a` trans, `same_as`, entailed-neg) | `universal` (134) | exported `UNIVERSAL_RULES`/generators, wired into the reasoning setup | hand `Rule`s + per-predicate generated `Rule`s | hand rules ARE rules; generators = Python by choice (§5) |
| — | L0 vocabulary (`wolf is a noun`) | `grammar_intake` `VOCABULARY_FORMS` | `ingest` (route: `vocabulary`) | lexicon REGISTER entry (data, not meaning) | n/a (data emitter) |
| — | Procedures (`to N : A then B`) | `procedure_surface` (88) | `ingest` (`parse_define`) | `step`/`step_before` FACTS for the stepping bank | n/a (data emitter) |

## 2. Three families (the classification that organizes the cut)

- **A. Rule-definitions** — 1, 2, 3, 4, 5(part), 7. All ARE or COMPILE TO `Rule`s; a rule is a
  (sufficient-condition) definition. This is what a **`define`** surface unifies at the authoring
  layer.
- **B. Scope-authoring (relativized meaning)** — 6 (hedge→epistemic fork), and the arc's own
  `holder`/`temporal`/`@?t`. These author KINDED SCOPES. **Already being unified** by scope
  generalization; `uncertainty.py`'s forks are the same object as a `holder` scope minus/plus a band.
- **C. Data/lexicon emitters** — vocabulary, procedures. Not definitions; leave alone.

The insight: the system reinvented **A** seven times because each concept shipped its own
*surface + expander + reader + linter*. **B** was the same story until scope generalization started
folding it into one kinded mechanism. The "define meaning" capability the user wants is **A**'s
missing common surface; the "drastic simplification" is collapsing **A**'s loaders (§3) and, where
the wall allows, its expanders behind that surface (§4).

## 3. Immediate cuts — evidence-backed, confidence-labeled

**HIGH confidence (mechanical, no capability lost):**
- **⭐ Loader convergence DONE 2026-07-22 (suite 886 green).** The intake dispatch now has a
  `comparison` Outcome (an additive FALLBACK route reusing `parse_comparative`); the canonical grammar
  refuses the surface, so nothing is stolen, and an ink comparison survives later fact-path
  normalization. `load_comparative` had ZERO live non-test callers.
- **⚠ HEDGE (`load_uncertain`) was NOT converged onto intake** — it authors a FORK that does not survive
  the fact path's whole-graph normalization on a later utterance (measured), the §2 family-B composition
  problem. It stays on `world.load_world`, which now authors hedges LAST (after `load_corpus`).
- **`world.py` composite DEMO loader** now delegates facts/rules/comparisons to `load_corpus` (the one
  ingest path) and only special-cases hedges. So it is a thin partition-and-defer wrapper, not a second
  recognition path.

**MEDIUM (needs a design nod — it changes a contract, which the user has OK'd):**
- **The two batch loaders** `load_corpus` (legacy 2-pass, whole-batch) vs `load_kb` (declare-before-
  use) — the plan already flagged this as "a convergence question." Pick `load_kb`'s contract, port
  the corpus benches, delete `load_corpus` + `load_loose_rules`.
- **`rules_in_graph` (Pat reader) is used by NO reasoning-engine path** — only tests, the binder
  spike, and the `__init__` export (the demand chain reads `_read_atoms`; forward reads lowered ISA).
  It is a tool, not load-bearing; a candidate to demote/inline if the Pat 2-hop schema is retired in
  favor of the flat `<cond>` schema (they are two encodings of one thing — see §5).

**LOW / DO-NOT-CUT (load-bearing despite looking redundant):**
- The **two reified rule schemas** (Pat 2-hop vs flat `<cond>`) look like duplication but the flat one
  is the LEARNER-writable encoding (a rule's RHS cannot build the 2-hop shape — it cannot name the
  relation node). Keep both until the meta-circular story changes.
- The **three rule representations** (Pat, reified-graph, lowered-ISA) are each load-bearing (forward
  `run_bank` drives the grammar banks; demand drives reasoning). Converging them is the Rust/firmware
  long-game, NOT this cut.

## 4. The `define` surface — what it absorbs

A single authoring form, lowering to the rules that already work:

```
define grandparent(?x, ?z)  as  parent(?x, ?y) and parent(?y, ?z)      # sufficient (the rule)
define bachelor(?x)         as  man(?x) and not married(?x)            # with NAF
```

- **Lowers to a `Rule`** (family A) — identical to `load_machine_rules` output, so it rides the
  existing demand chain unchanged. This is 80% of the value: ONE surface, prose-adjacent, for what is
  now spread across machine-rules/forms/universal.
- **Biconditional option** (`define … iff …`) additionally emits the *necessary* rule(s) with
  bound-literal skolem heads for the existential witnesses — the E1/E2 pattern, already NATIVE. This
  is the genuinely new ergonomic: one statement, both directions.
- **Absorbs relation-properties and disjointness AS DECLARATIONS** — `define transitive R` / `define A
  disjoint from B` become spellings under the one `define` umbrella, **dispatching to the existing
  Python expanders** (§5). The user writes one kind of statement; the system still compiles the
  generated ones through the §8 tool.
- **Does NOT absorb family B** (hedges/forks): "x is likely P" is relativized meaning → a SCOPE, and
  belongs with `holder`/`temporal` under scope generalization, not `define`. Keeping them apart is the
  three-roles invariant (S2), not an oversight.

## 5. The quote/eval "wall" — ALREADY CLIMBED (corrected 2026-07-22)

> **This section originally claimed the wall makes the expanders un-rule-able. That was WRONG, and
> `learner.py` + a live probe disprove it.** Corrected here so the mistake is not propagated.

**A rule CAN write a rule containing a variable, today.** Probe: mark `tweety` (a bird that flies)
`observe`, run the learner — it WRITES the rule `?x can fly when ?x is_a bird`, and that written rule
is usable (`robin is_a bird` → `can(robin,fly)` is POSITIVE). So "rules that write rules" is live,
not deferred (`learner.COOCCURRENCE`).

**What actually makes it work — three primitives that SIDESTEP the wall without breaking it:**
1. the FLAT `<cond>` schema (`k_subj`/`k_pred`/`k_obj`), which an RHS *can* build (unlike the 2-hop
   `subj→pred→obj` path, which it cannot — that is the only thing still un-writable directly);
2. INTERNED pattern-variable nodes — a control node literally NAMED `?x`, referenced through a
   `pat_var` pool, so the learner never writes the *token* `?x` (which would be read as a variable);
   point `k_subj` at that node and `expand_rules` reads it back AS a variable;
3. REIFIED predicate tokens (`pred_tok` calculator) joined by a `ValueMatch`, so `k_pred` has a node
   to point at for a merely-observed predicate.

**So the real state of the wall:**
- **Rules-that-write-rules: OPEN** (proven). Every Python expander in the table (relation-properties,
  `disjoint`, comparative-transitivity, `same_as`, `entailed_negation`) **could** be a rule-that-
  writes-a-rule via primitives 1–3. They remain Python §8 tools by **pragmatic choice and history**
  (they predate the learner), **not by necessity.**
- **Still genuinely walled: only the ERGONOMIC form** — writing `'?a` DIRECTLY as a token in a rule's
  RHS. The classifier reads `?a` as a variable, and there is no QUOTE/staging token to say "literal
  `?a`". You don't need it (point at an interned node), but it is what would make a rule-writing rule
  *read* naturally instead of via the pool indirection.

**Consequence for the `define` surface (and the "address the wall?" question):** addressing the wall
is a *choice*, not a research problem, between (a) reexpress the expanders as rules-that-write-rules
using primitives 1–3 — no new mechanism, pure uniformity — or (b) add a genuine QUOTE token so
`define transitive R` and user-authored meta-patterns read naturally. Reasons to be cautious: full
metacircularity was **deliberately deferred as a PURITY milestone** (`CHANGELOG`: "deferred as a
purity milestone off Phase 4's path") because the capability was already met more cheaply; the Python
expanders are ~5 small correct functions and reexpressing them invites the learner's class of subtle
bugs (pred_tok non-termination, value-join-not-edge, the scaffolding filter). It buys UNIFORMITY, not
capability — **except** the one real capability gain: letting a USER define new rule-generating
*patterns* (their own `transitive`) at runtime, which (b)'s quote token would make in-language
authorable. That is the deepest form of "define meaning and use it," and the only reason to spend on
the wall now.

## 6. Recommended sequencing

1. **Loader convergence (HIGH cuts)** — ✅ **DONE 2026-07-22:** COMPARISON routes through `intake`
   (`comparison` Outcome). HEDGE was tried and REVERTED — a fork does not survive interleaved fact-path
   normalization (family B; awaits scope generalization). `load_world` now delegates all but hedges to
   `load_corpus`.
2. **Batch-loader convergence (MEDIUM)** — ✅ **DONE 2026-07-22 (reimplement, keep signature):**
   `load_corpus` is now ingest-in-a-loop (one recognition path, declare-before-use), keeping its
   `(kb, rules)` signature so ~132 call sites are untouched. **STILL OPEN:** retire `load_loose_rules` +
   the loose/translation subsystem (a feature+subsystem deletion — its own focused slice).
3. **The `define` surface (family A)** — one form → `Rule`; then fold relation-properties/disjoint
   spellings under it (dispatching to their expanders). Delivers the capability.
4. **Leave family B to scope generalization** — hedges are forks are scopes; that unification is
   already in flight and is where "in context C, X means …" (definitional/theory scopes) would land.
