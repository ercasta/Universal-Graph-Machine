"""Committed regression floor for EPISTEMIC CLOSURE UNDER COMPOSITION — the widened composition audit.

The reasoning axes were each DESIGNED INDEPENDENTLY (negation, degree/hedge, conditionality, scope/
suppose, causation, force). The load-bearing property is that they COMPOSE cleanly: every legal
composition must land in {reasoned-over} ∪ {explicitly refused}, NEVER {silently mis-mapped} (a wrong
answer, unsaid ink, or a status not preserved). See `bench/spike_epistemic_closure.py` and
`docs/design/form_inventory.md` §9; memory `epistemic-closure-under-composition`.

This test PINS the whole matrix (from the bench probe) so the map is a regression floor:
  - a NEW leak (a composition that starts silently mis-mapping) fails here;
  - a REGRESSION (a PASS cell dropping to REFUSED/LEAK) fails here;
  - CLOSING a gap (REFUSED→PASS) or the leak (LEAK→PASS) requires updating EXPECTED at the diff — a
    VISIBLE ratchet toward closure, reviewed rather than silent.

THE HEADLINE INVARIANT is the LEAK set: closure forbids silent mis-maps, so the leaks must stay a
known, shrinking set. Today it is exactly the one `degree ∘ negation` leak (`the lion generally has no
mane` routes `fact` but represents nothing). The REFUSED cells are CLOSED, not failures — several are
"closed but not reasoned" (an axis silently dropped, answered conservatively): those are the composition
GAPS the core-composition arc targets (degree/causation are the poor composers), but they do not violate
closure, so they are tracked here, not treated as leaks.
"""
from __future__ import annotations

import warnings

import pytest

warnings.simplefilter("ignore")

from bench.spike_epistemic_closure import CASES, run, PASS, REFUSED, LEAK, UNKNOWN  # noqa: E402

#: The pinned verdict for every case. PASS = the axis/axes are reasoned over end-to-end; REFUSED =
#: honestly declined or answered conservatively (CLOSED — includes "axis dropped but no mis-map"); LEAK
#: = a silent mis-map (closure violation). Update ONLY with a rationale at the diff — an improvement
#: (→PASS) is the ratchet; a regression must be investigated, never re-pinned to hide it.
EXPECTED: dict[str, str] = {
    # isolated blocks
    "certainty": PASS,
    "negation": PASS,
    "hedging": PASS,
    "conditionality": PASS,
    "attribution": REFUSED,              # no intake surface yet — closed
    "quantification": REFUSED,           # partial — closed
    # compositions
    # ⭐ CLOSED 2026-07-23 (LEAK→PASS): the hedged-negation PRODUCER now emits a banded `has_not` fork
    # (grammar `_hedge_rules` hedged-deny variant), which the demand reader composes for free. The
    # architecture probe (docs/design/composition_architecture.md) proved the evaluator was never the
    # problem — the fix was local to the producer. Closure is now LEAK 0.
    "hedge x negation": PASS,
    "conditional x negation": REFUSED,   # negated premise not matched — conservative, closed
    "conditional x hedge": PASS,         # band propagates through the rule (one mechanism)
    "hedge x question": PASS,
    "suppose x negation": PASS,          # counterfactual reasons over a ¬-assumption
    # ⭐ CLOSED 2026-07-23 (REFUSED→PASS): the hedged suppose PRODUCER now strips the hedge word and
    # entertains the assumption as a banded FORK (`suppose_surface.parse_suppose_banded` +
    # `suppose(assumption_bands=…, policy=…)`), so under a banded stance the band composes through the
    # rules into the prediction (`suppose lion generally is hungry : lion is dangerous` → `likely`).
    # Same producer-fix shape as `hedge x negation`; the reader was never the problem.
    "suppose x hedge": PASS,
    "causation x hedge": REFUSED,        # band DROPPED at the reification bridge — closed, not reasoned
    "causation x negation": REFUSED,     # negation not consulted at the bridge — closed, not reasoned
    "negation x question": PASS,
    "hedged rule": REFUSED,              # degree-on-the-rule not surfaced — closed
    # depth
    "derivational depth": PASS,
    "band-propagation depth": PASS,
}

#: The closure headline: the set of cells allowed to LEAK. Shrinking this is the whole goal.
KNOWN_LEAKS = {name for name, v in EXPECTED.items() if v == LEAK}

_RESULTS = {c.name: run(c)[0] for c in CASES}


def test_every_case_is_pinned():
    """The audit and the pin-map stay in sync — a new probe case must be given an expected verdict."""
    assert set(_RESULTS) == set(EXPECTED), (
        f"probe/pin drift: only-in-probe={set(_RESULTS) - set(EXPECTED)}, "
        f"only-in-pin={set(EXPECTED) - set(_RESULTS)}")


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_composition_verdict_is_pinned(name):
    """Each composition cell holds its pinned verdict — regressions and silent improvements both surface."""
    got = _RESULTS[name]
    assert got == EXPECTED[name], (
        f"{name!r}: verdict {got} != pinned {EXPECTED[name]}. If this is an IMPROVEMENT (→PASS), update "
        f"EXPECTED with a note. If a REGRESSION, a composition started leaking/dropping — investigate.")


def test_no_new_leaks():
    """THE HEADLINE INVARIANT: silent mis-maps stay a known, shrinking set. A NEW leak fails loudly."""
    leaks_now = {name for name, v in _RESULTS.items() if v == LEAK}
    new = leaks_now - KNOWN_LEAKS
    closed = KNOWN_LEAKS - leaks_now
    assert not new, f"NEW closure LEAK(s) — a composition silently mis-maps: {sorted(new)}"
    assert not closed, (
        f"a known leak is now CLOSED: {sorted(closed)} — update EXPECTED/KNOWN_LEAKS to lock the win.")


def test_no_unknown_verdicts():
    """An UNKNOWN means the probe could not classify the composition — it needs a human judgement, not a
    silent pass. Keep the matrix fully classified."""
    unknown = {name for name, v in _RESULTS.items() if v == UNKNOWN}
    assert not unknown, f"unclassified composition(s) need a human epistemic judgement: {sorted(unknown)}"
