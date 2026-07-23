# Core-axis composition — architecture probe (2026-07-23)

> Status: ARCHITECTURE PROBE, answering a design question raised while reassessing priorities toward
> **clean composition of the independently-designed reasoning axes** (the core, not the grammar surface).
> Memory: `epistemic-closure-under-composition`, `firmware-over-isa-design`, `possibilistic-layer`.

## The question

The widened composition audit (`tests/test_epistemic_closure.py`, PASS 10 / REFUSED 7 / LEAK 1) found that
every composition that PASSES shares one evaluation mechanism — `chain_sip` over rules under a policy — and
every one that FAILS involves a mechanism outside it (the hedge FORK, the propositional-cause BRIDGE). The
natural hypothesis:

> Isn't `chain_sip` a hardcoded imperative Python procedure? Should we convert it to firmware (ISA
> instructions) and make it event-based, so the axes compose?

## The finding — the EVALUATOR already composes; the PRODUCERS don't

**`chain_sip` is already firmware, and it already treats every axis as a composable ANNOTATION on ONE
evaluation.** Concretely, from the code:

- **Matching is ISA firmware.** `_facts_matching` builds an ISA program and runs it on `_ISA_READER =
  Machine()`; there is no second matcher. (`firmware-over-isa-design`, ARC COMPLETE.)
- **The per-goal closure is an ISA ControlMachine program.** Each frame is a `_frame_program` (PRIM round +
  BRANCH_IF fixpoint + budget); `chain_sip` itself is a thin DRIVER over an explicit STACK of suspended
  machines. Converting that thin driver buys nothing.
- **Negation is ALREADY event-based** at the machine boundary: a frame's NAC SUSPENDs with the subgoal as its
  `Continuation.request`; the driver pushes a child frame and RESUMEs the parent mid-round (`isa-control-machine`).
- **The band is ALREADY a composable annotation.** Under a banded policy the reader's rel-guard uses
  `OVERLAY_BAND` over a `{rel → band}` map and the band RIDES THE MATCH SCORE (min t-norm). The code comment is
  explicit: "banded reasoning composes with SUPPOSE for free." Scope (suppose/pencils) is the sibling overlay.

**Proof the evaluator composes degree × negation (the audit's one hard LEAK):** hand-build a banded `has_not`
(`add_fork(g, 0.75, [("lion","has_not","mane")])`) — bypassing intake — and run a rule over it:

```
?x is safe when ?x has_not mane      # a rule whose premise is a banded NEGATION
-> chain_sip derives (is, lion, safe) with band = 0.75
```

The banded negation reasons through the rule and carries its band. **The evaluator has no composition
problem.** (An earlier probe that "derived nothing" was a harness bug — the wrong goal tuple.)

### So where does the leak actually live? At the PRODUCERS.

Two producers emit facts that DON'T carry the annotation the reader already composes:

1. **hedge × negation — the intake SURFACE FOLD.** `the lion generally has no mane` routes `fact` but emits
   **nothing banded** (measured: banded `has_not` = 0.0, banded `has` = 0.0). The grammar hclause has folds
   for a hedged POSITIVE (`hclause hedges subj pred obj unless neg`) but **no negated counterpart** (no
   `hclause denies … when neg` that would emit a banded `has_not` fork). The composition is dropped before
   `chain_sip` ever runs — exactly the "failure is at INTAKE" note in `epistemic-closure-under-composition`.

2. **causation × hedge/negation — the reification BRIDGE.** `that lion generally is hungry causes that lion
   is dangerous` emits crisp propositional HANDLES that do **not** carry the underlying proposition's band
   (measured: banded `is(lion,hungry)` = 0.0). The MP bridge then reasons over a crisp proxy, so the band /
   negation of the antecedent is lost across the reification boundary.

## Consequence for the fix

**Do NOT rewrite `chain_sip`.** It is already firmware, already event-based at the negation boundary, and
already composes band/scope as annotations on the one reader. The lever is **local, at the producers**: make
them EMIT into the annotated representation the evaluator already carries.

- **hedge × negation (the hard LEAK, highest leverage):** give the intake fold a hedged-negation production
  that emits a **banded `has_not` fork** (grammar: an `hclause denies … when neg` counterpart; and/or the
  `uncertainty` fold for a hedged relational negation). The reader then composes it for free — proven above.
  This also lights up `suppose × hedge` (same fork representation flowing into the suppose scope, which the
  overlay already carries).
- **causation × hedge/negation (the two DROP gaps):** carry the band/negation THROUGH the reification —
  the handle's truth should be a banded read of the underlying fact (or the reify bridge should stamp the
  antecedent's band onto the handle), so MP over the handle preserves status.

## The principle, and the honest nuance

The instinct behind the question is **correct and already realized in the evaluator**: "one evaluation, N
composable annotations" is exactly what the ISA reader does with band (score) + scope (overlay). The gap is
that a couple of producers bypass that representation, not that the evaluator is imperative.

Honest nuance for later (NOT what blocks the current failures): the annotations the reader composes today
(band, scope) are threaded as Python parameters (`policy`, `scope`) + Python-computed overlays
(`_band_overlay`, `_scope_pencils`), so adding a genuinely NEW annotation axis (a new modality, temporal
validity as a first-class band) still means editing `chain_sip`/`_facts_matching`, not pure data. Making the
annotation set itself OPEN/data-driven is a separate, larger arc. But the current composition LEAK and GAPS
need none of it — their annotation (the band) already exists and already composes; only the producers must
emit it.

## Recommended next slice

Close `degree ∘ negation` at the producer: a hedged negation → a banded `has_not` fork. Anchor: the committed
`tests/test_epistemic_closure.py` cell `hedge x negation` flips LEAK → PASS (the ratchet), and re-check
`suppose x hedge` (expected to improve as the same fork flows through the suppose overlay). Small, local,
architecturally faithful — and it validates that the evaluator was right all along.

## §GAPS — what the producer fixes closed (2026-07-23, shipped 1046 green)

Every fix predicted above landed AT THE PRODUCER, none touched the evaluator — validating the finding.

- **`degree ∘ negation` LEAK → PASS (CLOSED).** `grammar._hedge_rules` emits a hedged-DENY variant (a banded
  `has_not` fork). See the plan's ⭐⭐ block. Audit LEAK count now 0.

- **`suppose ∘ hedge` REFUSED → PASS (CLOSED).** Two-part producer fix, no evaluator change:
  1. `suppose_surface.parse_suppose_banded` / `_strip_hedge` — the hedge word was read as the PREDICATE
     (`suppose lion generally is hungry` → `(lion, generally, is)`, garbage), so the assumption never held.
     Now the hedge is stripped and its band returned.
  2. `suppose(assumption_bands=…, policy=…)` — a hedged assumption is entertained as a FORK (not a certain
     in-scope pencil, which `chain._rel_env` reads as ∅-env certainty by design), so under a banded stance the
     band composes through the rules into the prediction and CONFIRM wears it (`result.band` → `band_word`).
     Under a CRISP stance the fork is invisible (nothing readable ⇒ `no (assumed)`), so no new leak. Certain
     assumptions stay in-scope pencils; a mixed suppose is per-assumption correct (each hedged one its own fork).

- **`causation ∘ {hedge, negation}` — producer fixed, but the CELL stays REFUSED (a SEPARATE blocker).**
  `cause_surface._clause` was the producer bug: it read the negator as the object (`has no mane` →
  `(lion, has, no)`) and the hedge as the predicate. Now it folds `S V no|not O` → `neg_pred` (matching the
  fact route's `has_not`) and strips a hedge word. **Antecedent-first, both compositions now REASON correctly**
  on the grammar route (`test_propositional_cause_over_a_negated_antecedent_reasons`,
  `…_over_a_hedged_antecedent_carries_the_band`). The epistemic-closure cells use **link-first** order, which is
  blocked by a DIFFERENT, known issue: a `that A causes that B` stated before its antecedent mints a THIRD
  co-named `lion` node (the handle's `subj`, interned by name) that has no `denotes` link to the grammar fold's
  entity, so the reify bridge's `?s ?p ?o` join misses it (measured: 3 `lion` nodes). This is the
  node-identity/canonicalization problem the derivation-frame boundary handles for token↔entity but not for an
  independently-minted handle node — a separate arc, not the composition axis. The producer fix is a prerequisite
  for those cells to pass once the order-dependence is closed.

**Audit now PASS 12 / REFUSED 6 / LEAK 0** — the two remaining causation REFUSEDs are "closed, not reasoned"
by the link-first node-duplication issue, not by any composition gap.
