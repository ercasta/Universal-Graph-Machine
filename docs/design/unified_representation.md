# Unified representation — one proposition node, axes as annotations, truth as vantage

> ⚠ **SUPERSEDED 2026-07-24 by `docs/design/scope_reframe_audit.md`** — read that as the north star.
> This doc's diagnosis (the evaluator composes; failures are producers/representations that bypass the one
> evaluation) STANDS and is inherited. Its **§4 was WRONG in one load-bearing way** and is CORRECTED below:
> "a reference-before-assertion interns to the VERY NODE a later assertion inks" (COLLAPSE reference into
> referent) re-manufactures the mention-vs-assert conflict — treating a statement's participant as the
> entity rather than a REFERENCE to it. The correction is **reconcile, don't collapse**: a reference and its
> referent stay DISTINCT nodes, unioned at read time SCOPE-LOCALLY (spiked GO, `bench/spike_scope_local_identity.py`).
> The reframe generalizes "truth as a vantage" (§5) into **relativization as the only scoping primitive:
> scopes as nested nodes, a relativizer = a base fact whose object is a scope, isolation by default, crossing
> a data rule.** See the audit for the full map, the settled relativizer/annotation line, and the migration.
>
> Status (original): DESIGN / NORTH STAR, 2026-07-23. Came out of the core-axis-composition arc: the widened
> closure audit (`composition_architecture.md`) proved the EVALUATOR composes cleanly and every failure
> is a PRODUCER or a REPRESENTATION that bypasses the one evaluation. This doc names the target the
> whole composition arc should converge on, so every later diff is checked against it rather than
> patched toward a local green. It supersedes "close the remaining composition cells" as the framing:
> the cells become the acceptance test for Step 1, not a fix to rush.
>
> Memory: [[scope-reframe-relativization]], [[epistemic-closure-under-composition]], [[composability-principle]],
> [[facts-as-truth-bearers-built]], [[derivation-frame-consolidation]], [[binding-is-the-missing-axis]],
> [[spo-directed-path-no-labeled-edges]], [[baroque-vs-fundamental]].

## 0. The one-sentence invariant

> **Every proposition is ONE interned node; every reasoning axis is an ordinary relation on that node;
> "does it hold?" is evaluated relative to a VANTAGE that is itself facts — so the single matcher reads
> them all together and composition is STRUCTURAL, not engineered.**

Everything below is the argument for that sentence, the mapping of today's mechanisms onto it, the
honest cost, the foundational decision it re-opens, and the migration sequence that reaches it WITHOUT
adding a new seam on the way.

## 1. The diagnosis: seams are partitions that bypass the one evaluation

The closure audit's sharpest finding: composition is hard **only** where an axis is represented off to
the side of `chain_sip`, and free everywhere it is a scope/overlay the matcher already reads.

| axis | representation TODAY | composes? |
|---|---|---|
| degree / hedge | band on a scope node, read via `OVERLAY_BAND` | ✅ |
| scope / suppose | `<scope>` tag on the relnode, read via overlay | ✅ |
| conditionality | a rule in `chain_sip` | ✅ |
| **negation** | a **different predicate** (`R_not`) + `neg_of` pairing data | partial (needs the pairing traversal) |
| **causation (propositional)** | a **content-keyed handle** `prop:X:Y:Z` + 3 bridge rules | ❌ (duality + order bug) |
| **force** (assert/ask/command) | a routing decision at **intake** + a `<goal>` node | not on the fact at all |
| tense / attribution | a kinded scope (`<temporal-index>` / `<holder>`) | mostly (scope machinery) |

The composers share ONE mechanism (a scope/annotation the matcher reads). The non-composers each have
their OWN representation, each a small island ([[composability-principle]]: an island is unreachable by
the rest of the substrate). **The fix is not more mechanism — it is making the ONE representation
mandatory**, because the substrate already contains every primitive it needs (§3).

## 2. What is a "proposition", uniformly

A fact today is an S-P-O directed path `subj → relnode → obj`, direction carrying the roles, the relnode
carrying the predicate as a key ([[spo-directed-path-no-labeled-edges]]). **The relnode is ALREADY a
first-class node** — it is where the band hangs, where a `<scope>` tag hangs, where provenance hangs. So
the substrate already half-reifies every fact. The unification is to take that seriously and make the
relnode the UNIFORM carrier of every axis, with a STABLE identity, read relative to a vantage.

Three things must become true of that node:

1. **It has structural identity** (two references to "lion has mane" are the same node). §4.
2. **Its truth is contextual** (it holds relative to a vantage; "ink" is holds-in-base). §5.
3. **Every axis is a relation on it**, read by the one evaluation (§6), where the vantage is data (§7).

## 3. The primitives already exist — the gap is uniformity

This is not a rewrite-the-engine proposal. Each unification is grounded in a shipped primitive that a
handful of axes currently DECLINE to use:

- **Structural fact interning** — `MINT(dedup=True)` already reuses a relation node by TOPOLOGY
  (subject + predicate + object back-reference), and honours a dynamic/variable predicate via `key_reg`
  (`machine.py` MINT docstring). The causation handle's content-key is a stringly-typed re-implementation
  of exactly this.
- **Predicate-as-data** — `key_reg` on SEED/TEST/EMIT/MINT reads and writes a fact through a bound
  predicate variable (`?s ?p ?o`), the [[facts-as-truth-bearers-built]] primitive. A fact whose predicate
  is data is native on both engines.
- **Kinded scopes** — `scope_kind` already dispatches epistemic / holder / temporal
  (`scope_generalization.md`); attribution and tense are ALREADY "a fact relative to a scope."
- **Entity identity** — `_canon_class` / `denotes` (the derivation-frame boundary,
  [[derivation-frame-consolidation]]) already unify a token with the entity it denotes at read time.
- **Bands on scopes + the banded read** — `_band_overlay` + `OVERLAY_BAND` already carry a degree on the
  match score (min t-norm), composing with SUPPOSE "for free" (`chain.py`).

The unification uses these five, uniformly, for every axis — instead of causation minting content-keys,
negation minting a second predicate, and force living at intake.

## 4. Keystone — fact identity is entity identity, one level up

The hardest and most load-bearing piece; do it first (§8, Step 1).

**Problem it solves.** The propositional-causation handle exists to NAME a proposition before its parts
are asserted (`that A causes that B`, stated before A). It content-keys `prop:lion:has_not:mane` so the
name is stable. But that key is a SECOND identity for a proposition whose parts also live as an interned
relnode — and the two never reconcile: link-first mints a THIRD co-named `lion` node with no `denotes`
edge, and the reify join misses it (measured: 3 `lion` nodes; `spike_causation_representation.py`).

**The unification (CORRECTED 2026-07-24 — reconcile, DON'T collapse).** A proposition's identity is a
FUNCTION of its participant identities and predicate: `id(F) = (canon(subj), pred, canon(obj))`. Entities
are already interned (name-interning + `denotes` + `_canon_class`); a proposition is an entity ABOUT a
relation, so the SAME boundary, lifted one level, gives it identity. **But a statement's participant is a
REFERENCE to an entity, not the entity** (`that A causes …`, stated before A, mentions A without asserting
it). So the reference and its referent stay DISTINCT nodes, reconciled at READ time by the identity boundary
— NOT collapsed into one node (the original "interns to the very node a later assertion inks" was the error:
collapse re-manufactures the mention-vs-assert conflict, because minting the referent-node to mention it
would assert it). Mechanically: `MINT(dedup=True)` with endpoints canonicalized through `_canon_class`
writes facts; a reference dereferences to its referent via the identity link; and that union is
**SCOPE-LOCAL** (`spike_scope_local_identity.py` GO) — across a relativizer boundary identity holds but
facts don't flow, which is what keeps a mention from leaking into base while still coreferring. No
content-key. (This is the audit's point 1; a mention is simply a fact deeper in the scope tree, not a
second identity to reconcile away.)

**Consequence.** The causation composition cells close the RIGHT way — by structural identity — not by
the rule-lowering quick win that merely DODGES minting (`spike_causation_representation.py` showed the
rule works precisely because it never mints a `lion`; the moment you need the link-as-fact, identity
returns). Step 1 is the foundation, not a workaround.

## 5. Truth is contextual — pencil/ink is base-vs-non-base vantage

A pencil fact today is a control relnode tagged `scope=<hypothesis>`, invisible to ordinary matching,
visible within its scope; ink is an untagged relnode. So a pencil fact IS ALREADY "a fact in a scope",
and ink is "a fact in the base scope." The pencil/ink **coloring is a special case of scoping**, and the
user's question — can we drop it? — is answered: as a CONCEPT, yes.

**The unification.** There is ONE notion — a fact HOLDS relative to a vantage — and the base vantage is
the committed, monotone, always-visible one. `ink = holds-in-base`. Suppose/fork/holder/temporal are
non-base vantages. Reading a fact is always "does it hold from HERE", where the base is the default here.

**The irreducible residue, named honestly.** You cannot delete the dualism, only relocate it: there must
be a COMMITTED/monotone layer (never retracted, always visible) versus ENTERTAINED layers (swept on
refute). Unify into scopes and the base becomes a distinguished, never-swept scope — which is ink by
another name. And the coloring earns its keep as a FAST PATH (the `_guard` skips non-base facts with one
attribute test instead of consulting scope machinery per match). So the coloring survives — but demoted
from a semantic primitive to a MATERIALIZED index of "holds-in-base." The win is not fewer concepts; it
is that a hedged-negated-supposed fact is ONE kind of thing (a scoped, annotated relnode), so the
operators compose. (This is already what closed `suppose ∘ hedge`: the hedged assumption penned as a
fork scope, composed by the banded reader with no evaluator change.)

## 6. Every axis is an annotation-relation on the fact node

With identity (§4) and contextual truth (§5), each axis becomes an ordinary relation FROM the fact node,
read by the one matcher:

- **degree** — `F likeliness 0.75` (equivalently: F scoped behind a band; today's fork, generalized).
- **scope / suppose / fork** — `F holds-in <vantage>` (today's `<scope>` tag).
- **tense** — `F at <temporal-index>` (today's temporal scope, already kinded).
- **attribution** — `F according-to bob` (today's holder scope, already kinded).
- **negation** — `F polarity negative` — an ANNOTATION, not a second predicate. This is the biggest
  representational change: `R_not` + the `neg_of` pairing retire, so hedge∘negation, cond∘negation,
  causation∘negation compose with no special traversal, and NAF reads a polarity annotation rather than a
  paired predicate's absence (§8 flags this as the riskiest step).
- **causation** — `F causes G` between two INTERNED fact nodes — what the handle wanted, on the shared
  representation. Links chain because they are facts; the link is queryable because it is a fact (the one
  capability the rule-lowering could not give — now free).
- **force** — `F asserted` / `F asked` / `F commanded` as an annotation, so force is a property OF the
  proposition read by the loop, not a routing decision made before the proposition exists
  ([[force-is-the-missing-axis]]).

Composition is now structural: two axes on one fact are two relations on one node, read together. There
is no partition, so there is no seam. This is the [[epistemic-closure-under-composition]] design target
("band/scope/negation as composable ANNOTATIONS on ONE fold, not N mode-specific drivers") made literal.

## 7. The vantage is facts, not Python parameters

The residual island the `firmware-over-isa` vision has not absorbed: the reading CONTEXT rides through
`chain_sip` / `_facts_matching` as Python parameters and Python-assembled overlays, NOT as graph data —

- `policy` (banded/crisp stance, θ, on-cycle) — a Python object; a rule cannot reason about the stance,
  and the stance is global-per-call.
- `scope` / `focus_scope` — node-ids, but WHICH is active is a call argument.
- `_band_overlay` / `_scope_pencils` — Python functions that RECOMPUTE the `{rel → band}` overlay each
  call into `registers`.
- `max_rounds` / fuel — a budget parameter.

**The unification.** These become a VANTAGE node the reader consults (stance, active scope, time, holder,
focus, budget = relations on the vantage). "Does F hold?" = "is F entailed FROM this vantage", the vantage
read like any other facts. This is what makes a GENUINELY NEW axis pure data — declare an annotation + how
the vantage reads it — instead of an edit to `chain_sip`. It is the largest piece and the one that turns
"closed for the built axes" into "closed AND extensible."

Honest scope line: freeze the annotation-set GRAMMAR before making the vantage data-driven (the standing
rule — structure frozen at runtime, vocabulary open; [[force-is-the-missing-axis]] §4d). The vantage makes
the axes' PARAMETERS data; it does not license new structural axes to appear at runtime.

## 8. Cost, the re-opened decision, and what must be frozen

**This is reification — and it re-opens a foundational call.** [[spo-directed-path-no-labeled-edges]]
rejected Davidsonian / role-labeled edges as "would only complicate the engine." What is proposed here is
NOT that: it does not put role-labeled edges on every fact for n-arity; it makes the fact-NODE (already
present as the relnode) the uniform carrier, with axes as ORDINARY relations. N-arity / labeled edges stay
a SEPARATE question, driven by >2-participant relations, not by composition. Still — this makes the
fact-node first-class where the earlier decision kept it incidental, so it must be re-opened EXPLICITLY,
not drifted into. (Recommended: re-ratify with the user before Step 1 code.)

**Performance.** Reading relative to a vantage risks paying scope resolution per read; today's coloring is
the fast path. The coloring must survive as a MATERIALIZED "holds-in-base" index, designed in from the
start, or reads regress. Correctness before performance — but do not delete the index thinking it is only
a coloring; it is the coloring's real job.

**Riskiest single step: negation-as-annotation** reshapes NAF (which keys on `R_not` absence today).
Isolate it, re-break the negation/coref suite, differential-gate it.

**Freeze first:** the annotation-set grammar (which axes exist, their relation names) before §7. The ISA
is already frozen (the Rust boundary); this freezes the axis vocabulary above it.

## 9. Migration WITHOUT new seams — the sequence

The discipline that separates "design for unification" from "a quick win reworked later": **every step
lands ON the target architecture (reduces the partition count, converges toward §0), gated by
`tests/test_epistemic_closure.py` as a ratchet + differential parity.** No step introduces a partition to
undo later.

- **Step 0 — this doc.** The north star. Every later diff is checked against §0 ("does this move toward
  one-fact-node / many-annotations / vantage-as-data, or add a partition?"). Re-ratify the reification
  decision (§8).
- **Step 1 — fact identity (the keystone, §4).** Lift `_canon_class` to facts; make `MINT(dedup)` the ONE
  fact-writer; retire the causation content-key so a link interns to the canonical fact node. **Acceptance
  test: the causation ∘ {hedge, negation} closure cells pass LINK-FIRST** — closed by identity, not by the
  rule-lowering dodge. Kills the "3 co-named nodes" class of order bugs. Fully on-target; the foundation
  the rest stands on.
- **Step 2 — negation-as-annotation (§6).** `F polarity negative`; retire `R_not` / `neg_of`; NAF reads
  polarity. Negation composes uniformly. Riskiest; heavily gated.
- **Step 3 — vantage-as-facts (§7).** Migrate policy / scope / focus into a vantage node; pencil/ink
  collapses into holds-in-vantage with the coloring demoted to a cache (§5). Turns closed-for-built into
  closed-and-extensible.

Each step is independently shippable, green-gated, and strictly reduces the number of off-to-the-side
representations. Step 1 alone retires a whole class of node-identity bugs and is where the causation cells
get closed the RIGHT way.

## 10. Acceptance — how we know unification landed

- The axis-representation table in §1 collapses: every ✅ and ❌ row reads "a relation on the fact node,
  read by the one evaluation." No row says "a different predicate", "a content-keyed handle", or "a routing
  decision at intake".
- `test_epistemic_closure.py`: every composition cell PASS (not merely closed) — INCLUDING link-first
  causation — with the LEAK set empty and no cell regressed to REFUSED.
- A NEW axis (e.g. source/trust as a band, temporal-validity) is added as DATA — an annotation relation +
  a vantage-read rule — with NO edit to `chain_sip` / `_facts_matching`. This is the §7 acceptance and the
  proof that composition is now open, not just complete.
- `test_substrate_purity.py` ([[composability-principle]]) still green: the unification added no new
  substrate-writer island; the fact-writer is the ONE categorized `MINT` path.
