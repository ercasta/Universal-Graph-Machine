# Design — the SURFACE / INTERPRETATION split

> **Status: SPIKED GREEN, NOT INTEGRATED (2026-07-18).** User proposal; end-to-end demonstration in
> `bench/spike_interpretation_scope.py`, narrative results in `homoiconic_grammar.md` §11. This
> document is the design as it now stands, separated from the grammar arc that produced it because
> it is a SUBSTRATE-level decision that outlives that arc: it governs coreference, retraction,
> revision, and the "how should the substrate be layered" question.
>
> Read first: `../vision.md` §5 (two layers, fact immutability), `../reference/logic_fragment.md`,
> `homoiconic_grammar.md` §10-§11 (what produced this), `consistency_design.md` §0 (the
> contradiction marker this depends on), `reconsider_design.md` (the revision machinery).
>
> Supersedes in part: the §10 decision that mint-vs-percolate is a per-production DECLARATION.

## 1. The problem this solves

Three separate threads arrived at the same wall.

1. **Coreference cannot be revised.** `intern_mentions` folds same-named mentions into one node and
   `_fold_node` deletes the victims. The decision is therefore irreversible: once two mentions are
   merged, the evidence for splitting them is gone. This was accepted because the alternative
   (link-based `same_as` coref) was measured 3-6× slower with a super-linear clique
   (`attic/demand_driven_coref_plan.md`).
2. **The grammar arc created a new judgement with no right default.** A modified noun phrase
   (`the guzerat lion`) is either a distinct subkind or the entity already under discussion.
   `homoiconic_grammar.md` §10 made this a per-production declaration — which requires the domain
   author to know the correct reading in advance, per production, for every domain.
3. **The substrate-layering question had no principled answer.** A proposed `<stratum>` attribute on
   nodes was rejected (§9.5) because the strata on offer were ENGINEERING distinctions (control vs
   fact) while the observed failures were reading rules over legitimately shared nodes.

All three are the same defect: **judgements are written as though they were observations.**

## 2. The split

> **The nodes representing the SENTENCE are never touched.** They are the permanent, monotone
> record of what was said. Every JUDGEMENT about what it MEANS lives in a SCOPE holding COPIES,
> with provenance back to the surface.

**SURFACE (observation, immutable, monotone).** Tokens, the `first`/`next` chains, and parse spans
(`cat`/`begin`/`end`). What the sentence said. Never revised, never deleted, never read as fact.

**INTERPRETATION (inference, scoped, discardable).** Entities; `denotes` (token → the entity it is
taken to denote); every slot (`head`, `subj`, `pred`, `obj`, …); every fact folded from the parse;
coreference; subkind minting. What the sentence is taken to mean.

**Membership rule — the finding that cost a bug (§11.4):** the line is **NOT** "which node it hangs
on". Slot edges are written ONTO surface span nodes and are still interpretation. The line is
**structure vs denotation**: the surface is tokens, chains, and `cat`/`begin`/`end`, and nothing
else. Leaving slot edges out of the scope let a second interpretation silently inherit the first
one's decisions while appearing to work.

## 3. The load-bearing consequence

**Inside the scope, the merge may be destructive.** One node per entity — the fast representation,
no `same_as` clique, no representative-pointer hop, i.e. exactly today's cost. This is legal
because reversal is never needed: an interpretation is not repaired, it is **discarded and
re-derived** from a surface that never moved.

This is what makes defeasible coreference affordable, and it is why the 2026-07-13 interning
decision does not have to be reopened. Interning stays; what changes is its STATUS — from an
irreversible reader policy to a defeasible commitment carrying provenance.

## 4. The loop

    surface: parse ONCE
      -> interpretation: commit (coreference, denotation, subkind-vs-same-entity)
      -> derive <contradiction> markers (monotone, paraconsistent — consistency_design §0)
      -> walk provenance from the marker to the JUDGEMENTS in its support
      -> if a judgement is implicated: ASK, do not pick
      -> discard the scope; re-derive with the answer
      -> the surface never moved, and nothing was re-parsed

Culprit selection is a SELECTION problem, and this project's answer to selection problems is
consistently the same: **do not select — ask.** A contradiction whose support contains a
coreference commitment produces "is the guzerat lion the same lion, or a kind of lion?" — a
question a person answers instantly and a solver cannot.

## 5. Invariants

1. **The surface is append-only.** Nothing in the interpretation may write to or delete from it.
2. **Exactly one live interpretation.** Two would make reads ambiguous and reintroduce branch
   selection. Contested alternatives are QUESTIONS, not parallel worlds.
3. **Every interpretation node carries provenance to the surface it came from** (`interprets`),
   because that chain is the input to culprit selection.
4. **Discarding a scope removes every node AND every denotation edge it created** (invariant 2 of
   §2 restated operationally).
5. **Reads default to the interpretation**, not the surface. This is a STANDING scope — the primary
   view, with the surface as archive — which is inverted from `suppose`'s hypothesis-fork
   semantics even though it may share the machinery.

## 6. Why this is the right stratification

The rejected `<stratum>` proposal failed because control-vs-fact is an engineering distinction, so
membership was a judgement call and the coloring leaked (`homoiconic_grammar.md` §9.5 documents two
real leaks in one slice). **Observation vs inference is epistemic.** It is exactly two layers, and
membership is decidable without taste: *what the sentence said never changes; what it means is
always revisable.*

## 7. Mechanisms: reused, and missing

**Exists and should be reused:** `suppose` / `SCOPE` tags / `OVERLAY` (scoping and the delta read);
provenance (`proves`/`uses`, always-on for committed intake asks); copy-on-delete retraction;
`reconsider`'s dirty-grain cascade (to scope re-derivation to the affected region rather than
redoing the session); `ByDesc` (a scope node has no name, so rules cannot address it by one).

**Missing:** `<contradiction>` derivation. `consistency_design.md` is still a SKETCH — the marker
convention is designed and paraconsistent-by-design, but nothing derives it. The spike hand-rolls a
per-predicate contradiction bank.

## 8. Open before this is production

- **Copy-on-WRITE, not materialized.** The spike materializes the scope. At session scale it must
  hold only the DELTA and fall through to the base, or it grows into a full KB shadow. `OVERLAY` is
  the mechanism.
- **Promotion.** An interpretation that survives uncontested should collapse into the base and stop
  costing. This is the same "promotion by survival" queued for rules — the mechanism generalizes,
  which is some evidence the shape is right.
- **Enforce invariant 2** (one live interpretation); today it is assumed.
- **Culprit selection at realistic scale.** The spike demonstrates a contradiction with exactly ONE
  judgement in its support. Real ones will have several, and choosing among them is the hard part.
- **A property is given up:** today the token node IS the entity ("canonical structure accretes on
  the same nodes the surface chain uses — the no-seam payoff"). Under this split the token stops
  doubling as the entity. The no-compile-seam property survives (both layers are graph-resident and
  rule-written), but that identification does not, and a lot of existing code assumes it.

## 9. Evidence

`bench/spike_interpretation_scope.py`, 2026-07-18: 2 sentences parsed once (231 surface nodes) →
interpretation A (percolate) derives `lion has mane` + `lion has_not mane` → `<contradiction>` →
provenance shows the entity was interpreted from 2 surface mentions → discard (90 nodes, 231/231
surface intact, 0 contradictions) → interpretation B (mint subkind) → 0 contradictions, no re-parse.
