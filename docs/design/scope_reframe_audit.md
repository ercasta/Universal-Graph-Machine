# Scope reframe audit — relativization as the one scoping primitive

> Status: AUDIT / NORTH STAR (2026-07-24). Supersedes `unified_representation.md` as the steering doc:
> it kept "one interned proposition node, axes as annotations, truth as a vantage" but drifted toward
> COLLAPSING a reference into its referent (§4 "interns to the very node a later assertion inks"), which
> re-manufactures the mention-vs-assert conflict. This audit re-bases the whole substrate on the primitive
> `form_inventory.md` §9.3 already isolated — **① scope generalization: relativizing a fact to a context,
> with rule-bindable scopes** — sharpened by a design conversation (2026-07-23/24) into a concrete data
> model: **scopes as nested nodes, relativization as the ONLY scoping operator, interposing nodes instead
> of guard-attributes, isolation-by-default with copy-to-cross.**
>
> Read together with the two arcs it must not break: `composition_architecture.md` (the EVALUATOR already
> composes band/scope as annotations on one ISA reader — do NOT rewrite `chain_sip`; fix PRODUCERS) and
> `form_inventory.md` §9 (the set must be CLOSED under composition at depth, through ONE evaluation
> mechanism). **Unification and composition are the twin north stars; this audit is how the substrate is
> reshaped to serve them without adding a seam.**
>
> Memory: [[unified-representation-north-star]], [[composability-principle]],
> [[epistemic-closure-under-composition]], [[binding-is-the-missing-axis]],
> [[scope-generalization-slice1-holder]], [[scope-generalization-slice2-temporal]],
> [[derivation-frame-consolidation]], [[spo-directed-path-no-labeled-edges]],
> [[scope-nodes-survive-incidental-gc]], [[force-is-the-missing-axis]], [[baroque-vs-fundamental]].

## 0. The one-sentence thesis

> **The graph is mostly AFFIRMATIONS, lazily bound to instances — not entities that physically exist.**
> A relativizer ("John says", "at time T", "under hypothesis H", "that … causes …") creates a SCOPE NODE;
> facts and other scopes are born UNDER it; composition is NESTING; isolation is the default; and to USE
> what is under a scope a rule must explicitly CROSS the boundary (a data rule, typically a
> copy-with-provenance). The engine knows only that *relativization exists*; it is agnostic about what any
> particular scope MEANS. Everything a scope means lives in its crossing rules — data, not Python.

This dissolves the recurring error the whole substrate has made: treating every `subj → rel → obj` path
as an asserted fact of the world ("existence = holds"). That law governs only the BASE scope. A referenced
proposition (a mention, an attribution, a hypothetical, a past state) is a fact of ITS scope, reachable
only by crossing — so "mention vs assert" is not a tension to engineer around, it is base-vs-non-base
position in the scope tree.

## 1. The classifying lens (five reframe tests)

Every subsystem below is scored against these. A row is a *reframe target* if it fails one.

1. **Relativization is the only scoping primitive.** No hardcoded scope *categories*. FLAG every place
   the engine knows what a scope MEANS.
2. **Isolation by default; reach by explicit copy/cross.** Whitelist, not blacklist. FLAG every opt-*out*
   guard (a growing `absent=True` exclusion set) and every default-visible non-base content.
3. **Interposing nodes carrying attribute-sets — never labeled edges, never special guard-attributes.**
   FLAG every "special attribute you must remember to test" and every string-mangled key. Each becomes a
   nested scope, an ON-PATH interposing node, or a plain fact.
4. **Identity = read-time union of copies via a SPECIFIC, non-contaminating link — never physical-node
   collapse, never one edge doing both identity and visibility.** FLAG every place identity and visibility
   ride the same relation.
5. **Meaning is data; the engine is a small relativization + interposition + copy + union mechanism.**
   FLAG every Python island doing domain semantics (a crossing/promotion decision that should be a rule).

## 2. The reframe map

Legend for CLASS: **SUP** imposed superstructure (test 1) · **GUARD** opt-out guard-attribute (test 2/3) ·
**KEY** string-mangled key / labeled-edge (test 3) · **CONFL** conflated identity/visibility (test 4) ·
**ISLAND** Python domain-semantics island (test 5) · **CORE** legitimately irreducible mechanism (keep).

| # | subsystem | today (grounded in code) | class | reframed shape |
|---|---|---|---|---|
| 1 | `scope_kinds.py` `SCOPE_KIND` = epistemic/holder/temporal, with `resolve_key`/`materialize` policy flags | the engine dispatches on what a scope MEANS | **SUP** | a scope is JUST a node; kind becomes an ordinary attribute a CROSSING RULE reads; `resolve_key`/`materialize` become data on the relativizer |
| 2 | scope membership = single-valued `SCOPE` attr on a control rel (`possibility._fork_scope_of`, `apply.SCOPE`) | one fact in ONE scope; no nesting ⇒ no structural composition | **GUARD**, blocks composition | membership = a structural `under`/`MEMBER` edge to a scope NODE; a fact under N scopes = N `under` edges (nesting); composition is the parent chain |
| 3 | pencil = **control-marked** rel + `SCOPE` tag (`possibility._pencil`) | invisibility-to-base done by the CONTROL kind marker, not by scope position | **GUARD** (the redundancy the user named) | a pencil is just "a fact under scope H"; drop the control mark — isolation comes from position, not a kind marker |
| 4 | `CONTROL_MARK` / `INERT_MARK` + `chain._guard` (`TEST(absent=True)` on every fact read) | opt-out blacklist; grows one entry per non-fact kind; only protects reads routed through `_guard` | **GUARD** for the SCOPE-like uses; **CORE** for the true non-fact kinds | keep `inert` (provenance is genuinely never-a-fact) and the scaffolding sense of `control`; MOVE the pencil/scope use onto scope position. The blacklist stops growing |
| 5 | negation `neg_pred`: `R → R_not` string (`is_not`, `is_a_not`) + `neg_of` pairing (`vocabulary.py`) | negation is a mangled predicate KEY; NAF keys on the paired predicate's absence | **KEY** | negation = an INTERPOSING PREDICATE-NODE (occupies the predicate position, linked to the base predicate), carrying attributes; NAF reads the interposing node, not a string suffix. NOT a scope (else NAF must cross to ask the positive) |
| 6 | propositional causation `prop:X:Y:Z` handle + 3 bridge rules (`cause_surface.py`) | a stringly re-implementation of `MINT(dedup)` topology-interning; orphan participant refs | **KEY** + **CONFL** | the STATEMENT is a scope: `causes` between two proposition-references, each a scoped structure whose participants are references dereferenced lazily by crossing (the reify tail IS the crossing rule) |
| 7 | references / `denotes` / `chain._canon_class` (derivation-frame boundary) | token→entity dereference, read-time class union — the RIGHT model, one level down | **CORE** (the template), but watch **CONFL** | GENERALIZE it as the cross-scope IDENTITY link — but it must NOT also grant visibility (see §3 trap); identity link ≠ copy/visibility link |
| 8 | bands / degree `_band_overlay`, `OVERLAY_BAND`, fork `<likeliness>` | already a composable annotation on the ONE reader (score, min t-norm) | **CORE** (evaluator) but band lives on a SCOPE | keep the reader; a band is an attribute on the scope node — fits nesting cleanly (a hedged scope is one nested context) |
| 9 | force: intake router ladder + `<goal>`/`<query>`/`<call>` control tokens (`intake._ingest_gen`, form_inventory §4b) | force lives in the ROUTER, not on the proposition | **ISLAND** (partial) | force = an annotation ON the proposition read by the loop (`F asserted`/`asked`/`commanded`) — an interposing node or a scope over the proposition, not a routing decision before it exists |
| 10 | the vantage: `policy`, `scope=`, `focus_scope`, `max_rounds` threaded as Python params (`chain_sip`, `_facts_matching`; unified-rep §7) | the READING CONTEXT is Python, not data; a rule cannot reason about the stance; crossing is a `scope=` argument | **ISLAND** | the active vantage (stance, active scope, time, holder, focus, budget) becomes a NODE the reader consults; "does F hold?" = "is F entailed FROM this vantage"; crossing becomes data |
| 11 | interpretation scope: structural `MEMBER` edges + copy-on-coref (`interpretation.py`, surface/interpretation split) | ALREADY the copy-to-cross model, with structural membership | **CORE** (the precedent) | this IS the general mechanism generalized: born-in-scope, copy to cross, discard to retract. Unify pencils/kinded scopes ONTO this membership shape (edges, not the `SCOPE` attr) |
| 12 | `MINT` `dedup` (topology-intern) matches EXACT endpoint ids, not `_canon_class` (`machine.py`) | the "one fact-writer" doesn't canonicalize endpoints, so mention-then-assert splits | **CONFL**-adjacent | `MINT(dedup)` with endpoints canonicalized through the identity link = the one fact-writer; a reference and its later assertion reconcile structurally (unified-rep §4, corrected: reconcile, don't collapse) |
| 13 | scope-variable rules `@?t` hardcoded to `temporal` in `chain.py` (`scope_kinds.py` note) | rule can bind ONLY the temporal kind | **SUP** | a rule binds ANY scope (`@?s`); relativization is kind-agnostic — the deferred "family-B" work falls out of test 1 |

## 3. The two traps that re-introduce contamination (design constraints, not rows)

**Trap A — identity vs visibility on one edge (test 4).** The cross-scope "same lion" link must not be
read-time-unioned the way `denotes` is today, or a BASE read of `lion` pulls in its hypothesis-copy's
facts and isolation is gone — the exact bug we are removing. The interposing identity node must carry
BOTH bits distinctly: *same referent* (for coreference) and *facts do NOT flow* (visibility granted only
by an explicit copy/cross). One relation cannot do both jobs. This is why references generalize `denotes`
but crossing is a SEPARATE, explicit act.

**Trap B — an annotation off to the side is still a guard (test 3).** Negation as a node HANGING OFF a
still-intact `lion —[has]→ mane` path does not escape guard-everywhere: base matching still finds the
positive path unless it tests for the negation. It escapes only if the interposing node occupies the
PREDICATE POSITION (`lion —[not(has)]→ mane`, the interposing node linked to `has`), so a positive query
for `has` structurally misses with no guard. State the line explicitly: **relativizers → scopes (nesting,
cross to reach); polarity/force/degree → on-path interposing nodes or scope attributes; never a
beside-the-path attribute that must be guarded.**

## 4. The convergence — one primitive, many axes (why this serves composition)

`form_inventory.md` §9.3 already proved the binding programme reduces to **① scope generalization**; this
audit says what ① *is* structurally, and the convergence widens:

- **references / mention** = a proposition under a statement scope; dereference = cross.
- **attribution** ("John says X") = a holder scope; promotion = a crossing rule that copies X to base with
  provenance, then reconsider retracts on refute (all parts shipped — [[reconsider-arc]]).
- **tense** = an ontological ordered scope; the `@?t` frame axiom is a cross-scope rule.
- **hypothesis / suppose / fork** = a scope carrying a band; the possibility layer's env-sets become the
  parent chain.
- **propositional causation** = `causes` between two scoped statements; MP is the crossing.
- **negative-band leak** (composition_architecture's one-time LEAK) = a band on a scope, read on the
  negative path — already closed at the producer, and it stays closed because band-on-scope is uniform.
- **force** = an annotation over the proposition, not a router decision.

Every one is "a fact relativized to a context, read/bound correctly." That is exactly the
[[epistemic-closure-under-composition]] target — *band, scope, negation, force as composable annotations
on ONE evaluation, not N mode-specific drivers* — made structural. **Crucially, per
`composition_architecture.md`: the EVALUATOR already composes annotations on the one ISA reader. This
audit does not touch `chain_sip`.** It reshapes how PRODUCERS and REPRESENTATIONS emit into scopes so the
already-composing reader sees them — the same "fix the producer" lever, generalized from two cells to the
whole substrate.

## 5. What stays irreducible (the small engine core)

"Agnostic" cannot be literal, or nothing could isolate or cross. The engine's whole commitment shrinks to
**four mechanism-level primitives, none a category**:

1. **relativizer marking** — a *declarable* mark (like the grammar declares categories, so the LLM can
   coin a relativizer as data; structure frozen, vocabulary open — [[force-is-the-missing-axis]] §4d);
2. **`under` / nesting** — the structural containment relation between a fact/scope and its scope node;
3. **cross / reach** — a generic primitive a DATA RULE invokes to read or copy across a boundary;
4. **identity union** — read-time union of a reference with its referent via a specific link (the
   generalized `denotes`), kept distinct from visibility.

Plus the genuinely-non-fact kinds that are NOT scopes: `inert` (provenance) and scaffolding `control`.
Everything else — what each scope means, when to cross it, what to promote — is data.

## 6. Migration sequence (each step reduces the partition count, gated, no new seam)

Discipline (unified-rep §9, kept): every step lands ON the target, gated by
`tests/test_epistemic_closure.py` as a ratchet + differential forward==demand parity; no step adds a
partition to undo later. Composition cells are the acceptance test, not a fix to rush.

- **Step 0 — this doc.** Re-ratify the reification/reference decision with the user (§7). Correct
  `unified_representation.md` §4/§5 to "reconcile, don't collapse; reference ≠ referent, dereferenced
  lazily."
- **Step 1 — scope as a nested NODE with structural membership.** Unify pencils/kinded scopes onto the
  interpretation scope's `MEMBER`-edge shape (row 11); membership becomes an `under` edge (rows 2, 3);
  the base fast-path (materialized "holds-in-base" index) designed in from the start so reads don't
  regress (unified-rep §5, the coloring demoted to a cache). **Gate: existing suppose/fork/holder/temporal
  suites stay green; the `SCOPE`-attr reads migrate to `under`-edge reads.**
- **Step 2 — relativization as the sole primitive.** Dissolve `SCOPE_KIND` (row 1) — kind becomes an
  attribute crossing rules read; `@?t` generalizes to `@?s` over any scope (row 13). Prove references on
  the propositional-causation case: the `prop:` handle retires (row 6); `causes` between scoped statements;
  the reify tail becomes the one crossing rule. **Acceptance: causation ∘ {hedge, negation} cells pass
  LINK-FIRST, closed by scoping — no content-key, no guard on base.**
- **Step 3 — negation as an interposing predicate-node.** Retire `R_not`/`neg_of` (row 5); NAF reads the
  interposing node. Riskiest (reshapes NAF); isolate, re-break the negation/coref suite, differential-gate
  (unified-rep §8; form_inventory §9.1 "carry the band on the negative read").
- **Step 4 — force + vantage as data.** Force annotates the proposition (row 9); the reading context
  becomes a vantage node (row 10). Turns "closed for the built axes" into "closed AND extensible": a NEW
  axis is a new relativizer + a crossing rule, with NO edit to `chain_sip`.

Steps 1–2 are the load-bearing pair (they realize ①); 3–4 are the completion. Each is independently
shippable and strictly reduces off-to-the-side representations.

## 7. Open decisions (surfaced this conversation, not yet settled — the user's calls)

1. **Membership: born-in-scope + copy-to-cross (the user's lean, row 11 precedent) vs edges-with-lazy-
   references (no copy).** The user chose copy-to-cross with an interposing identity node carrying
   attributes ("identity yes, visibility no"). Confirm this is the general model, honouring Trap A.
2. **Re-ratify reification/reference** (unified-rep §8 re-opened [[spo-directed-path-no-labeled-edges]]):
   the fact-node/statement becomes first-class, but NO role-labeled/Davidsonian edges and NO n-arity
   change — n-arity stays a separate question driven by >2-participant relations.
3. **The relativizer/annotation LINE** (Trap B): which constructions are relativizers (→ scopes) vs
   on-path interposing nodes (negation, force, degree). Draft above; confirm before Step 3.
4. **Order/identity of the scope chain**: the user's resolution is to make ambiguous orderings
   STRUCTURALLY IMPOSSIBLE in the CNL (we control the surface), so the engine need not know which
   relativizers commute. Record as a CNL-design constraint.

## 8. Relationship to the three arc docs

- `unified_representation.md` — CORRECTED and subsumed: its "one node, annotations, vantage" survives;
  its §4 "collapse into the very node" is REPLACED by "reconcile reference to referent, kept distinct."
  This doc is the new north star.
- `composition_architecture.md` — HONOURED unchanged: the evaluator composes; the fix is at producers/
  representations. This audit is that lever generalized substrate-wide. `chain_sip` is not touched.
- `form_inventory.md` — this doc is the STRUCTURAL realization of its §9.3 primitive ① and its §9 closure
  demand (one evaluation mechanism, composable annotations). Its residue-log method for DISCOVERING forms
  is unchanged; this changes how the discovered forms are REPRESENTED so the set is an algebra.
