# Reconsider — demand-driven revision of assumed-absence conclusions

> **Status: BUILT (2026-07-16, same day — `ugm/reconsider.py`, hooks in `ask_goal`/intake,
> `tests/test_reconsider.py` ×8, suite 546 green). D2 (provenance always-on for committed asks)
> ratified by the user; measured +15% on the heaviest whole-graph ask (625→719ms), ~27ms/utterance
> on a full ingest session. Grain refined during build: `(pred, object-literal)`, not bare
> predicate — copula-heavy CNL puts everything under `is`, the object discriminates.**
> Closes the gap found while validating runtime rule authoring:
> a NAF-derived conclusion MATERIALIZED by an earlier ask survives new knowledge that
> contradicts the absence it leaned on. Mechanism exists (assumed-records, the cascade,
> copy-on-delete retraction); this designs the missing POLICY: when and how to re-check.
> Companion rationale: `../attic/mechanism_policy_separation.md`, `../possibilistic.md` S7,
> `ask_goal`'s "capstone follow-up" note.

## 1. The gap, reproduced

```
rules: ?x is thief when ?x is a suspect and ?x is not cleared
ada is a suspect
is ada thief            -> yes        (NAF: no clearing derivable; `ada is thief` INKED)
ada is alibied
?x is cleared when ?x is alibied      (rule authored mid-session)
is ada thief            -> yes        <- STALE: `thief` and (on a fresh demand) `cleared`
                                         now BOTH stand in the graph
```

Asked fresh *after* the rule, the answer is correctly `no` — the demand machinery handles
runtime rules (head index rebuilt idempotently per `chain_sip`; `active_rules` filters
disables; agendas/subsumption/`closed` are per-run). The staleness is only in conclusions
**materialized under the old knowledge**. Negative verdicts never materialize, so they are
immune; the problem is exactly: *inked positives whose journaled assumptions broke*.

## 2. Principles (all pre-ratified elsewhere)

- **Demand-driven**: nothing is eagerly re-checked at intake time; new knowledge only MARKS.
  The truth is settled when a question needs it — the same move as demand-driven negation.
- **Monotone within a pass, revision between passes**: reconsider runs BETWEEN reasoning
  passes (like `retract`), never inside one.
- **Reuse, don't rebuild**: the check IS mode-4 CHECK (re-ask the assumption's positive);
  the withdrawal IS the existing cascade + copy-on-delete `retract`. Reconsider is a
  COMPOSITION, not a new mode.
- **Over-forget and re-derive**: the aggressive single-support cascade may over-retract;
  monotone re-derivation on demand recovers anything still supported. Sound, never stale.
- **Two homes**: the dirty set is stepping/bookkeeping state no rule reasons about →
  `kb.registers`, not graph nodes. The *outcome* (what was withdrawn and why) is
  explanation → graph (history records).

## 3. The dirty set (intake side — the "mark")

`kb.registers["reconsider"]`: an insertion-ordered dict-as-set of **predicate names**
whose derivability may have changed since the last sweep. Writers:

| event                                | dirties                                   |
|--------------------------------------|-------------------------------------------|
| user-asserted fact (intake fact route)| the fact's predicate                      |
| authored rule (rule route)            | every head predicate of the new rule      |
| rule DISABLE / re-enable              | every head predicate of the toggled rule  |
| `ask_user` / tool-materialized fact   | the fact's predicate                      |

Facts EMITted by reasoning itself do **not** dirty: a closure under an unchanged
bank+base cannot make a previously-closed absence derivable (the NAF check already ran
that closure). O(1) per utterance; registers travel with `copy()`.

## 4. The sweep (question side — the "check")

Gated at the committed-ask entry: if `registers["reconsider"]` is empty → zero overhead.
Else, BEFORE the question's own closure:

1. **Affected predicates** = the dirty set closed transitively over the CURRENT active
   bank's body→head dependency edges (a new `alibied` fact can flip a `cleared`
   assumption through `cleared ← alibied`). Computed from the reified rules; small.
2. **Candidates** = every `<assumed>` record `A` (via `J --assumes--> A`) with
   `a_pred ∈ affected`, whose `J` still proves at least one LIVE fact (a J proving only
   history records is already settled — natural filter, no extra marking).
3. **Re-check** each candidate, one at a time, on the live graph: demand the positive
   `(a_pred, a_subj, a_obj)` (mapping the stored `anyone`/`anything` wildcards back to
   unbound endpoints) with the current active bank — exactly `_nac_blocks`' question,
   re-asked. Crisp: broken iff any fact matches. Banded: broken iff the best compatible
   `Π ≥ policy.theta` — the same θ-gate, so reconsider generalizes to the uncertain world
   with no extra machinery.
4. **Withdraw** on break: `seed_retract` each fact `J` proves; run the cascade; retire
   (copy-on-delete archives pre-images, provenance redirected onto the records). Stamp
   each history record `broken_assumption -> A` (inert), so `why` can answer *"withdrawn
   because `ada is cleared` became derivable"* — the book's revision promise, kept in-graph.
5. Clear the dirty set. The triggering question then runs normally: its own demand
   closure re-derives whatever the aggressive cascade over-retracted *that the question
   needs*; anything else re-derives when next demanded.

**Ordering/termination.** Checks only ADD derivability (monotone closures), retractions
only REMOVE facts; one ordered pass suffices. A candidate checked before an earlier
break's retraction may lean on a soon-retracted fact and over-break — recovered by
re-derivation (the established motto). No fixpoint loop needed.

**Regress guard.** The sweep's check closures run with the dirty set already detached
(read once, cleared at the end); facts they materialize do not re-dirty (§3).

## 5. Decisions taken (with rationale)

- **D1 — Trigger site: `ask_goal` (committed asks), not the intake loop.** Every consumer
  of committed answers gets revision (intake, tests, embedders); nested/internal closures
  (`chain_sip`, `check` inside NAF, `suppose`) never trigger — they are *within* a pass.
  `commit=False` asks do NOT trigger (they promise not to mutate); they may see stale ink
  until a committed ask runs — documented.
- **D2 — Committed intake asks flip to `provenance=True`.** Without receipts there are no
  assumed-records and reconsider is blind. The vision already calls RECORD (mode 9)
  "always on"; today's `provenance=trace` in intake was a perf shortcut. Cost to be
  measured; the crisp Π=0 journaling (2026-07-16) already pays most of the shape.
- **D3 — Rule-disable revision INCLUDED but minimal**: disabling dirties the rule's head
  predicates; a candidate whose `J` names a now-disabled rule is broken without any
  check (its support is gone by fiat). The dual case (disable breaking a *positive*
  chain) rides the same cascade.
- **D4 — Whole-KB sweep in v1** (candidates are session-sized). A focus-bounded variant
  (only in-focus assumptions) is a later knob; it would trade staleness-out-of-mind for
  latency, mirroring bounded attention.

## 6. Out of scope (named, not forgotten)

- **Forward path**: `run_bank` NAC firings don't journal assumed-records; forward-derived
  NAF conclusions stay unrevised. Same recipe applies later (journal in the NAC filter).
- **Banded re-weakening**: a conclusion whose assumption's Π rose but stayed < θ could
  have its band *lowered* rather than retracted — needs the propagation-strength knob
  (possibilistic open list); v1 is binary (retract at θ).
- **CNL stance** (`be skeptical` / reconsider-eagerness dial) — after v1.

## 7. Cost model

- Intake: O(1) register write per utterance.
- Question, clean session: one empty-dict check.
- Question after changes: |affected candidates| × one bounded demand check (each is the
  NAF question it originally was — typically ms-scale) + retraction cost only on breaks.

## 8. Test plan

1. The §1 transcript flips: re-ask after fact+rule → `no`; `cleared` inked; `thief`
   archived with `broken_assumption` stamped; `why` renders the withdrawal.
2. New-fact-only break (no new rule): `ada is alibied` alone with `cleared ← alibied`
   already in the bank.
3. Transitive dirtying: dirty pred reaches the assumption only through the dependency
   closure.
4. Multi-support survivor: conclusion with an independent non-NAF derivation is
   re-derived by the triggering question after the cascade.
5. Cascade depth: a conclusion standing ON the stale conclusion falls with it.
6. Disable: `forget that rule` + re-ask withdraws the rule's materialized conclusions.
7. No-op: unrelated dirty predicate → no retraction, dirty set cleared.
8. Banded: fork raising Π above θ breaks the assumption; below θ leaves it.
9. Determinism: sweep order = insertion order (registers dict) — bit-for-bit stable.
10. `commit=False` ask does not trigger and does not mutate.
