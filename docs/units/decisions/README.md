# Decision records

One decision per file. Each stands alone — you should not have to read its neighbours to understand it.

**Shape:** Context (what forced the choice) → Decision → Evidence (what was measured, including what broke) →
Consequences. `Status` is one of *Accepted*, *Deferred*, *Designed, not built*, *OPEN — needs a decision*,
*Superseded by NNNN*.

**These records are not a changelog.** They say why the system is the way it is. For what it *is*, read
`../reference.md`; for what is happening now, `../STATUS.md`.

## The principle

| | |
|---|---|
| [0039](0039-guards-yes-kinds-no-the-uniformity-principle-and-its-price.md) | **Guards yes, kinds no** — the uniformity principle and its price |
| [0040](0040-the-fact-layout-is-edge-labelled-the-semantics-are-path-fait.md) | The fact layout is edge-labelled; the semantics are path-faithful |

## Foundations

| | |
|---|---|
| [0001](0001-computation-units-are-the-substrate.md) | Computation units are the substrate |
| [0002](0002-one-unit-class-the-taxonomy-is-read-off-in-degree.md) | One unit class; taxonomy is read off in-degree |
| [0003](0003-the-store-is-bounded-not-abolished.md) | The store is bounded, not abolished |
| [0004](0004-functional-semantics-the-cache-is-what-makes-the-fixpoint-wo.md) | Functional semantics; the cache makes the fixpoint work |
| [0031](0031-units-may-not-import-from-ugm.md) | `units/` may not import from `ugm/` |

## Wiring and scope

| | |
|---|---|
| [0005](0005-the-index-indexes-computation-never-data.md) | The index indexes computation, never data |
| [0006](0006-a-producer-joins-an-instance-only-if-comparable-with-every-p.md) | Join only if comparable with **every** producer |
| [0007](0007-scope-is-a-chain-never-a-key.md) | Scope is a chain, never a key |
| [0009](0009-frontier-first-wiring-is-a-correctness-requirement.md) | Frontier-first wiring is a correctness requirement |
| [0010](0010-units-never-touch-wiring-the-assembler-is-observable-never-w.md) | Units never touch wiring |
| [0022](0022-two-indexes-a-runtime-filter-may-gate-a-wire-a-static-index.md) | Two indexes: only the runtime filter may gate |
| [0023](0023-what-may-start-a-computation-and-what-distinguishes-two-of-t.md) | Trigger vs projection are different questions |
| [0024](0024-the-object-trace-fork-test-must-be-positive.md) | The object/trace fork test must be positive |
| [0025](0025-wildcard-topology-must-be-authored-not-inferred.md) | Wildcard topology must be authored |
| [0038](0038-only-a-carrier-can-fork-a-world.md) | **Only a carrier can fork a world** — amends 0006 |

## What flows

| | |
|---|---|
| [0008](0008-subset-output-a-rule-emits-only-what-it-derived.md) | Subset output — a rule emits only what it derived |
| [0011](0011-there-are-two-negations-and-only-one-of-them-is-cheap.md) | Two negations, one of them cheap |
| [0014](0014-anything-minted-per-run-must-be-keyed.md) | Anything minted per run must be keyed |
| [0015](0015-a-facts-handle-is-a-pure-function-of-the-fact.md) | A fact's handle is a pure function of the fact |
| [0016](0016-degree-is-banded-not-continuous.md) | Degree is banded, not continuous |
| [0017](0017-roles-are-nodes-and-the-vocabulary-belongs-to-the-form-set.md) | Roles are nodes; the vocabulary is the form set's |
| [0018](0018-explicit-negation-is-a-graded-denial-about-a-reified-fact.md) | Explicit negation is a graded denial |
| [0019](0019-revision-is-recomputing-forward-the-retraction-apparatus-dis.md) | Revision is recomputing forward |
| [0030](0030-an-exhausted-budget-is-unknown-never-no.md) | An exhausted budget is UNKNOWN, never NO |

## Provenance

| | |
|---|---|
| [0012](0012-provenance-travels-on-its-own-wire-and-a-unit-sees-it-only-i.md) | Provenance on its own wire, seen only if asked |
| [0013](0013-trace-consumers-are-stratified-to-one-level.md) | Trace consumers are stratified to one level |
| [0029](0029-a-refusal-is-a-fact-the-assembler-s-decisions-are-recorded.md) | A refusal is a fact |

## Language in, language out

| | |
|---|---|
| [0020](0020-a-cnl-front-end-must-target-a-subgraph-never-the-net-api.md) | A CNL front-end must target a subgraph |
| [0026](0026-the-lexeme-is-the-licensed-bridge-entities-stay-nameless.md) | The lexeme is the licensed bridge |
| [0027](0027-a-missing-relation-between-terms-is-a-missing-fact-not-a-mis.md) | A missing relation is a missing fact |
| [0028](0028-decide-reference-asymmetrically-then-symmetrise.md) | Decide asymmetrically, then symmetrise |
| [0035](0035-a-description-identifies-rather-than-constitutes-a-selector.md) | A description identifies rather than constitutes |
| [0036](0036-the-expression-authors-the-topology-selector-chains-are-asse.md) | **The expression authors the topology** |
| [0037](0037-an-utterance-enters-as-a-carrier-downstream-of-the-kb.md) | An utterance enters as a carrier below the KB |
| [0041](0041-calls-are-positional-not-role-labelled.md) | Calls are positional, not role-labelled |

## Open, or designed and not built

| | | status |
|---|---|---|
| [0032](0032-can-a-rule-remove-monotonicity-and-derived-rewrites.md) | Can a rule remove? | **OPEN — needs a decision** |
| [0021](0021-an-in-node-isa-is-deferred-an-assembler-isa-is-refused.md) | In-node ISA | Deferred |
| [0033](0033-force-is-unit-shape-not-a-router.md) | Force is unit shape | Designed, not built |
| [0034](0034-one-form-one-force-one-atomic-structure.md) | One form = one force = one atomic structure | Designed, not built |
