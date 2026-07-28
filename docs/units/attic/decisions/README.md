# Decision records — the pre-inversion design, mostly contradicted

> ⚠ **ATTIC, 2026-07-28.** These 41 records were written for the `units` design *before* the substrate
> inversion of 2026-07-26 and the two revisions that followed. **Seven survive and are in force. The rest are
> reversed, dropped, halved, or historical.** Each file now carries a `**Status — current**` line stating which
> it is, above the status it was recorded with; the tables below summarise.
>
> For what the system *is*, read `../../model.md`. For what is happening now, `../../STATUS.md`. The original
> pointer here was to `../reference.md`, which no longer exists.

One decision per file. Each stands alone — you should not have to read its neighbours to understand it.
**Shape:** Context (what forced the choice) → Decision → Evidence (what was measured, including what broke) →
Consequences.

**These records are not a changelog.** They say why the design was the way it was, and several of them are
worth reading precisely *because* they were later reversed — the reversal is only re-derivable if the original
argument is legible.

---

## In force

| | | current status |
|---|---|---|
| [0003](0003-the-store-is-bounded-not-abolished.md) | The store is bounded, not abolished | **SURVIVES** — carried as the revive-cost question, `model.md` §13 |
| [0005](0005-the-index-indexes-computation-never-data.md) | The index indexes computation, never data | **SURVIVES** |
| [0008](0008-subset-output-a-rule-emits-only-what-it-derived.md) | Subset output — a rule emits only what it derived | **SURVIVES, strengthened** — mutation testing found positioning is what makes it *correct*, reversing the carry-forward it was in tension with |
| [0010](0010-units-never-touch-wiring-the-assembler-is-observable-never-w.md) | Units never touch wiring | **SURVIVES** as invariants 4 and 17, amended: a wiring change is a mutating rule's conclusion at write-back |
| [0019](0019-revision-is-recomputing-forward-the-retraction-apparatus-dis.md) | Revision is recomputing forward | **SURVIVES, vindicated** — revive-from-axioms is what makes it literally true. Invariant 11 |
| [0031](0031-units-may-not-import-from-ugm.md) | `units/` may not import from `ugm/` | **SURVIVES** — invariant 10, pinned by `tests/units/test_no_ugm_import.py` |
| [0039](0039-guards-yes-kinds-no-the-uniformity-principle-and-its-price.md) | **Guards yes, kinds no** | **SURVIVES**, and load-bearing. `model.md` §11 |

## Contradicted by the current model

| | | current status |
|---|---|---|
| [0001](0001-computation-units-are-the-substrate.md) | Computation units are the substrate | **REVERSED** — data is the substrate. Partly rehabilitated: units persist and are themselves data, but *over* the data, not it |
| [0002](0002-one-unit-class-the-taxonomy-is-read-off-in-degree.md) | One unit class; taxonomy from in-degree | **DROPPED** — no `kind`, no in-degree taxonomy |
| [0004](0004-functional-semantics-the-cache-is-what-makes-the-fixpoint-wo.md) | Functional semantics; the cache makes the fixpoint work | **HALF DEAD** — the cache half is dead (nothing is cached); the fixpoint half returns, bounded by surge |
| [0006](0006-a-producer-joins-an-instance-only-if-comparable-with-every-p.md) | Join only if comparable with every producer | **REPLACED** by scope-as-support |
| [0007](0007-scope-is-a-chain-never-a-key.md) | Scope is a chain, never a key | **HALF** — neither a chain nor a key; it is which configuration powers a conclusion |
| [0009](0009-frontier-first-wiring-is-a-correctness-requirement.md) | Frontier-first wiring | **REPLACED** — the seal and end-marker attachment are deleted |
| [0011](0011-there-are-two-negations-and-only-one-of-them-is-cheap.md) | Two negations, one of them cheap | **DEAD** — graded matching removes the cheap one |
| [0012](0012-provenance-travels-on-its-own-wire-and-a-unit-sees-it-only-i.md) | Provenance on its own wire | **SUPERSEDED TWICE** — provenance is neither a wire nor data; it **is** the wiring |
| [0013](0013-trace-consumers-are-stratified-to-one-level.md) | Trace consumers stratified to one level | **SUPERSEDED** — stratification is dropped with the provenance wire |
| [0017](0017-roles-are-nodes-and-the-vocabulary-belongs-to-the-form-set.md) | Roles are nodes; the vocabulary is the form set's | **HALF** — roles are nodes, yes; the shared vocabulary is deleted |
| [0026](0026-the-lexeme-is-the-licensed-bridge-entities-stay-nameless.md) | The lexeme is the licensed bridge | **HALF** — the bridge is deleted; identity is decided by a rule, gradedly |
| [0030](0030-an-exhausted-budget-is-unknown-never-no.md) | An exhausted budget is UNKNOWN, never NO | **REPLACED** — `out_of_fuel` is one of five positive outcome facts |
| [0038](0038-only-a-carrier-can-fork-a-world.md) | Only a carrier can fork a world | **REPLACED** — a conclusion is inside a hypothesis because its units are powered by it |
| [0040](0040-the-fact-layout-is-edge-labelled-the-semantics-are-path-fait.md) | The fact layout is edge-labelled | **REPLACED** by role nodes |
| [0041](0041-calls-are-positional-not-role-labelled.md) | Calls are positional, not role-labelled | **REPLACED** by role nodes |

## Settled since

| | | current status |
|---|---|---|
| [0032](0032-can-a-rule-remove-monotonicity-and-derived-rewrites.md) | Can a rule remove? | **SETTLED — yes.** A rule concludes a retraction, applied at write-back. Deletion is the fifth effect and the one non-monotone one (`model.md` §5, §9) |

## Historical — not contradicted by name, not carried forward either

Read these as context, not as decisions in force. They predate the inversion; where the current model has an
opinion it is in `../../model.md`, and where it does not, these have not been re-argued.

| | |
|---|---|
| [0014](0014-anything-minted-per-run-must-be-keyed.md) | Anything minted per run must be keyed |
| [0015](0015-a-facts-handle-is-a-pure-function-of-the-fact.md) | A fact's handle is a pure function of the fact |
| [0016](0016-degree-is-banded-not-continuous.md) | Degree is banded, not continuous |
| [0018](0018-explicit-negation-is-a-graded-denial-about-a-reified-fact.md) | Explicit negation is a graded denial about a reified fact |
| [0020](0020-a-cnl-front-end-must-target-a-subgraph-never-the-net-api.md) | A CNL front-end must target a subgraph, never the API |
| [0021](0021-an-in-node-isa-is-deferred-an-assembler-isa-is-refused.md) | In-node ISA deferred; assembler ISA refused |
| [0022](0022-two-indexes-a-runtime-filter-may-gate-a-wire-a-static-index.md) | Two indexes: only the runtime filter may gate |
| [0023](0023-what-may-start-a-computation-and-what-distinguishes-two-of-t.md) | Trigger vs projection are different questions |
| [0024](0024-the-object-trace-fork-test-must-be-positive.md) | The object/trace fork test must be positive |
| [0025](0025-wildcard-topology-must-be-authored-not-inferred.md) | Wildcard topology must be authored, not inferred |
| [0027](0027-a-missing-relation-between-terms-is-a-missing-fact-not-a-mis.md) | A missing relation is a missing fact |
| [0028](0028-decide-reference-asymmetrically-then-symmetrise.md) | Decide reference asymmetrically, then symmetrise |
| [0029](0029-a-refusal-is-a-fact-the-assembler-s-decisions-are-recorded.md) | A refusal is a fact |
| [0033](0033-force-is-unit-shape-not-a-router.md) | Force is unit shape, not a router |
| [0034](0034-one-form-one-force-one-atomic-structure.md) | One form = one force = one atomic structure |
| [0035](0035-a-description-identifies-rather-than-constitutes-a-selector.md) | A description identifies rather than constitutes |
| [0036](0036-the-expression-authors-the-topology-selector-chains-are-asse.md) | The expression authors the topology |
| [0037](0037-an-utterance-enters-as-a-carrier-downstream-of-the-kb.md) | An utterance enters as a carrier below the KB |
