# Handoff: does likeliness/band composition need privileged ISA support, or is it ordinary declared rules?

**RESOLVED, 2026-07-30, same day — CORRECTED the same day after a fresh pass caught an error in the first
pass of this resolution (below), then the fix was ACTUALLY APPLIED AND VERIFIED end-to-end the same day
(§7). Verdict: CONFIRMED SUGAR (retirement candidate), not a `transitivity`-style exception. See §6 for the
corrected diagnosis and §7 for the applied fix; §§1–5 are kept verbatim as the probe material that produced
it.**

## 6. Resolution (corrected)

The first pass of this resolution claimed `Pat.rel`'s relativizer needed a third dispatch arm for
`KIND_HYPOTHESIS` (fork) scopes, reasoning by analogy from `KIND_TEMPORAL`'s kind-specific dispatch without
actually checking whether the *other* existing relativized reader, `chain._relativized_st_matching` (the
`@?h` scope-tree reader), already covers forks. **It does, and the claim was wrong — caught by a direct
question ("isn't relativization just a convention now? we should be able to just point the machinery at a
local area of the subgraph"), verified by running it, not by re-reading docstrings more carefully.**

`OVERLAY_BAND` bundles three concerns, and two of them are already fully generic — but not the two the first
pass named:

1. **Visibility of a control-marked pencil rel to the demand read at all.** Unchanged from the first pass:
   the same "OR is an overlaid pencil" gate plain `OVERLAY` already does for crisp SUPPOSE scopes — already
   justified, never actually in question.

2. **Binding *which fork scope* a matched atom's rel belongs to — ALREADY GENERIC, verified empirically.**
   `possibility.fork_fact` writes a fork's facts via `suppose._relativize` → `scope_tree.put_under`, the
   exact same `<under>`-edge structural membership every scope kind uses (temporal, scope-tree holds,
   forks — one convention, not three). `chain._relativized_st_matching` (the `@?h` reader) never tests scope
   kind — it walks "entities born under *some* scope" generically. Direct test: building a fork
   (`load_uncertain(g, "x is likely male")`, band 0.6) and firing an ordinary `Rule(lhs=[Pat("?p", "is",
   "male", rel="?fork")], rhs=[Pat("?p", "is", "suspicious")])` through `chain_sip` with **no** banded policy
   and **no** engine change **binds `?fork` to the fork scope today, with zero new code**. There is no
   missing arm. `_relativized_matching` (the `KIND_TEMPORAL`-only reader) is legacy/narrower than
   `_relativized_st_matching`, not a template that needed a sibling.

3. **Composing the resulting band into the match score — the ACTUAL remaining gap, and it is NOT the score
   math.** `GRADE` (`machine.py:207`) does correctly compute the min-composed degree when run as an ephemeral
   program (confirmed by reading `Machine`'s GRADE case: `st.scaled(deg, self.tnorm)`). But
   `chain._grades_pass` (`chain.py:1078`), the function `GradedCondition`'s α-cut actually runs through in the
   demand chain, discards that computed score:
   ```python
   prog = [GRADE(var, dim, threshold=thr) for var, dim, thr in graded]
   return bool(_ISA_READER.match(fact_g, prog, init=[st]))
   ```
   `bool(...)` keeps only pass/fail; the achieved degree is thrown away and never folded into `band` the way
   `_facts_matching(bands=True)`'s fork-band results already are (`chain.py:1557`,
   `band if fb >= band else fb`). **Verified by running the same probe above and checking the result**: the
   rule fires (`chain_sip` returns 1), but `check(g, ("is", "x", "suspicious"), rules=rg)` reports `"positive"`
   (CERTAIN), not `"likely"` (0.6) — the conclusion is written crisp, silently dropping the fork's band. This
   is the real, narrow gap: not a missing relativizer arm, not new opcode machinery, but one function
   (`_grades_pass`) that needs to return the achieved score instead of a bool, and its one caller
   (`chain.py:1560`) needs to fold that score into `band` — the identical pattern already used for fork bands
   two lines away.

4. **"Best band wins across derivations"** — unchanged from the first pass: ordinary monotone-fixpoint
   behaviour (re-emit only at a strictly better degree, `Band`'s own docstring, `production_rule.py:246`),
   not fork-specific, needs nothing new.

**Corrected answer: THREE of the four pieces are already fully generic/ordinary (visibility, scope-binding,
best-of-derivations) — the scope-binding piece in particular needs NO new relativizer arm, contrary to the
first pass. The one real gap is a small, LOCAL plumbing fix in `chain._grades_pass` and its single call
site — thread the achieved graded score through instead of collapsing it to a bool, and fold it into `band`
exactly where fork-bands already are. This is smaller and more local than the first pass's claim, not larger:
no new engine concept, no new dispatch arm, one function's return value and ~2 lines at its call site.**
Retiring `OVERLAY_BAND` itself (and `_band_overlay`/`_scope_pencils`) is still real follow-up work, but it is
now gated on that one local fix plus reproducing `test_body_through_fork_bands_the_conclusion` and
`test_best_band_wins_across_derivations` with ordinary `Pat(rel="?fork")` + `GradedCondition` rules — not
done in this session, left as the scoped next task.

## 7. The fix, applied and verified — but it needed a THIRD thing first, unrelated to this question

Applying §6's `_grades_pass` fix immediately hit a real infinite-accretion bug: the banded-emit
idempotence check (`chain.py`'s "has a strictly-better fork already been derived?" guard) could never find
a fork it had just derived, so it re-derived a brand-new one every round, forever. Tracing that down found
a THIRD, much bigger, unrelated pre-existing bug: `possibility(g, "is", "x", "male")` returned `0.0` for a
fork that unambiguously existed, **on a clean checkout, with no rule or policy involved at all** — the
entire base-vantage possibilistic read path was already broken before this session touched anything, root
cause being a silent collision between the `_pencil`->`_relativize` structural migration and two older
mechanisms (`scope_tree.is_visible`'s base-vantage filter, and `machine.OVERLAY_BAND`'s `CONTROL_MARK`-keyed
admit-logic) that never got updated to match. Full root-cause and fix:
`docs/units/scope_visibility_blocks_forks.md`.

**With that fixed, `_grades_pass`'s fix works exactly as predicted:** an ordinary declared rule —
`Rule(lhs=[Pat("?p", "is", "male", rel="?fork")], graded=[GradedCondition("?fork", {LIKELINESS: 1.0}, 0.0)],
rhs=[Pat("?p", "is", "suspicious")])` — derives `x is suspicious` ONCE (no accretion) at band `0.6`
(`check()` reports `"likely"`, not `"positive"`), reproducing `OVERLAY_BAND`'s automatic banding with zero
fork-specific engine support. This is the concrete, working confirmation the original question asked for.
Side effect: the documented pre-existing failure bucket in the four `test_possibility_*.py` files went from
31 failed / 12 passed to 2 failed / 41 passed (the `scope_visibility_blocks_forks.md` fix's doing, not
`_grades_pass`'s — but found and fixed in the same continuous investigation).

---

**Original probe material below (§§1–5), written 2026-07-30 because the conversation that raised this
question was running low on context.** Written so a fresh session could pick up the actual open question
rather than re-derive it — kept verbatim as the record of how the resolution above was reached.
Read `arc_recap.md`'s current Act for the full narrative this sits on top of; this document only covers
the one open question left at the end of that Act, plus enough grounding to probe it without re-reading
the whole session.

---

## 1. Why this document exists

This session made a foundation decision (build forward on `ugm/`'s substrate, not `units/`'s — see
`attic/handoff_ugm_reversion_evaluation.md`, resolved), generalized `scope_crossing.py`'s `resolve_
crossings` into a real outer-loop metaprocedure (region-selection + demand-decide + apply, now driven by
declared data), and wrote `metaprocedure_model.md` — the goal-driven/materialized/centrally-gated
computation model, corrected twice in the writing (see that document's §1a/§1b).

Working through the model's requirements led to a side investigation: `ugm/suppose.py`'s "PENCIL/INK"
terminology turned out to be stale documentation for a mechanism that had already migrated to structural
scope-tree relativization (confirmed in code, not assumed — `_pencil`'s own docstring documented its own
migration). That got fixed: `_pencil` renamed to `_relativize` across `suppose.py`, `scope_kinds.py`,
`possibility.py`, and their test callers; `suppose.py`'s module docstring rewritten to match the actual
mechanism. Full suite re-verified clean afterward (79 failed / 1133 passed — unchanged from the session's
established baseline, no regressions).

**That cleanup surfaced a real, separate, deeper question that was deliberately NOT resolved, to avoid
deciding it by assumption while renaming things:** does the possibilistic/band layer's automatic degree
composition need privileged ISA support (`machine.py`'s `OVERLAY_BAND` opcode), or is it — like everything
else this session found — fully expressible as ordinary declared rules over scope-relativized facts plus
the graded-condition primitives (`production_rule.py`'s `GradedCondition`/`Band`) that already exist as
ordinary rule-authoring tools? This document is the probe material for that question.

---

## 2. The precise mechanism in question

`machine.py`'s `OVERLAY_BAND` opcode (the "GRADED sibling of OVERLAY"):

> *"keep the state iff the node in `reg` lacks `key` (the BASE — an ink/fact rel, CERTAIN, score
> unchanged), OR it is an overlaid FORK pencil. The difference: `live` here holds a MAP `{rel_id -> band}`
> (all forks' pencils keyed to their `<likeliness>` scope band, not a plain set), and admitting a fork rel
> SCALES the state's score by that band (the t-norm — min — so a multi-hop derivation accumulates the
> WEAKEST-LINK band automatically, S7.2)."*

Concretely: as a match proceeds through several hops, and one of those hops reads through a fork
(possibility scope) with likeliness 0.7 and another through a fork with likeliness 0.5, the *match's own
score* automatically becomes `min(0.7, 0.5) = 0.5` — with no rule author writing anything to make that
happen. This is baked into the ISA's matching primitive itself (`chain.py`'s `_band_overlay` builds the
`{rel_id -> band}` map that `OVERLAY_BAND` consumes).

**The general finding this whole session kept re-confirming, in every other subsystem checked** (`reactive.
py`'s `fire()`, `resolve_crossings`, `learner.py`'s rule-writing, `expand_rules`'s rule-lifting): the fixed
Python/ISA layer should be doing *mechanism nothing reasons about*, and anything a rule needs to reason
*through* should be an ordinary declared rule. `OVERLAY_BAND` is the one place a numeric composition
happens *inside the matcher itself*, invisibly to any declared rule — worth checking against that same
standard rather than assuming it's a justified exception.

---

## 3. What the "ordinary declared rules" alternative would look like

`production_rule.py` already has the raw material:

- `GradedCondition` — *"a graded LHS condition on one bound variable... degree = min over dimensions of the
  node's embedding alignment... a t-norm — non-compensatory."* Already exists, already ordinary declared
  data.
- `Band` — *"a declared RHS EFFECT: set a GRADED attribute on an RHS node to a fixed degree."* Already
  exists, already how a fork's own `<likeliness>` gets written.

In principle, a rule chaining through two forks could instead be written to explicitly read both scopes'
`<likeliness>` attributes as ordinary graded conditions and assert `min(band_a, band_b)` on its own
conclusion — i.e., the *rule author* (or a shared, engine-provided "compose these two bands" schema, the
same idiom `causes propagates has` already uses for the crossing generalization this session built) writes
the composition, rather than the matcher doing it silently underneath every match.

**What isn't yet known, and is the actual thing to probe:** whether this is *tractable* for real multi-hop
chains (a derivation touching N forks would need N-way min composition — does that stay a small, generic,
reusable rule/schema, or does it explode per-arity the way the old Python-hosted business-rule banks did,
which is exactly the kind of thing this project has repeatedly found "confirmed sugar" for other relational
forms — see `closed_class_rechallenged.md`), and whether losing automatic composition breaks anything
observable (would a rule author now need to *remember* to compose bands, the same "trusting each rule to
remember" failure mode `metaprocedure_model.md` §4 already named for a different case).

---

## 4. Concrete first probe, proposed

1. Pick the smallest existing test that exercises multi-hop band composition —
   `tests/test_possibility_rules.py::test_best_band_wins_across_derivations` or
   `test_body_through_fork_bands_the_conclusion` look like the right size (both already in the
   session's established 79-failure baseline — see §5 note below on why that matters).
2. Reproduce the same scenario using *only* ordinary declared rules: forks written with `Band`, a
   composition rule reading both via `GradedCondition`/an explicit value-join, asserting the composed
   degree onto the conclusion — no `OVERLAY_BAND` involved in the reasoning path.
3. Check whether the result matches what `OVERLAY_BAND` produces today (once its own pre-existing test
   failures are set aside — see below) and whether the declared-rule version generalizes past 2-hop chains
   without combinatorial rule-authoring.
4. If it holds: `OVERLAY_BAND` (and the broader "pencil"/discount-on-read machinery in `chain.py`'s
   `_band_overlay`/`_scope_pencils`) is a candidate for retirement in favor of ordinary declared
   composition — a real simplification, following the same discipline that already retired `run_bank` as
   the default outer loop and the control-flag pencil mechanism this session's cleanup already removed.
   If it doesn't hold cleanly (real combinatorial blowup, or a capability genuinely lost): that's the
   answer too, and it should be written up as a confirmed (not assumed) exception to the "mechanism must
   be reasoned-through" standard, the same way transitivity was `closed_class_rechallenged.md`'s one
   confirmed non-sugar exception among five probed relational forms.

**Important framing note:** `test_possibility_rules.py` and `test_possibility_guess.py` are *already*
failing on the current `grammar` branch tip — 18 of the session's known 79 pre-existing failures live
exactly in this subsystem (band/hedge/possibility). That is itself a hint this layer may already be under
some strain independent of this question, but it also means: **do not treat those tests' current failing
state as a baseline to preserve.** The probe should check the *declared-rule* alternative against what the
band mechanism is *supposed* to do (per its own docstrings and the passing band tests), not against
already-broken tests.

---

## 5. Pointers

- `docs/units/metaprocedure_model.md` — the computation model this question extends; §1b's mechanism/
  policy distinction is the direct precedent for how to think about this.
- `docs/units/STATUS.md` — the running work tracker; this handoff is a new, unstarted item there.
- `docs/units/arc_recap.md` — the narrative this session sits inside.
- `ugm/machine.py` — `OVERLAY_BAND`, `OVERLAY`, and the module's own opcode-level discussion of the
  mechanism/policy split (§8 of `attic/mechanism_policy_separation.md`, cited throughout).
- `ugm/possibility.py`, `ugm/chain.py` (`_band_overlay`, `_scope_pencils`, `_rel_env`) — the fork/band
  vocabulary and its ISA-level read path.
- `ugm/production_rule.py` — `GradedCondition`, `Band`, `ValueMatch` — the declared-rule primitives any
  alternative would be built from.
- `tests/test_possibility_rules.py`, `tests/test_possibility_guess.py`, `tests/test_possibility_band.py`,
  `tests/test_possibility_cnl.py` — the existing band-composition test suite (currently 18+ pre-existing
  failures among them — see the framing note in §4).
- This document's own future: once the question in §4 is resolved (probed, not assumed), fold the outcome
  into `arc_recap.md`'s next Act and retire this document to `attic/` with a row in `attic/README.md`,
  the same discipline `attic/handoff_ugm_reversion_evaluation.md` already followed.
