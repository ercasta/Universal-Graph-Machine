# Handoff: does likeliness/band composition need privileged ISA support, or is it ordinary declared rules?

**Status: handoff note, written 2026-07-30 because the conversation that raised this question is running
low on context.** Written so a fresh session can pick up the actual open question rather than re-derive it.
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
