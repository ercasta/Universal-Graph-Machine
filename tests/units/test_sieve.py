"""`units/forms.py` + `units/sieve.py` — the closed class, probed rather than asserted.

The sieve is an instrument, so most of these tests are about the **instrument**: that it catches a
planted leak, that it can report success, and that its verdicts are not artifacts of how the cells are
built. The findings it produces are pinned separately at the bottom.
"""
import pytest

from units.forms import (ASK, ASSERT, CANDIDATES, DEGREE, HEDGE, LANGUAGE, NEGATION, POSITIVE,
                         PREDICATE, SEED, Attribute, Ctx, Form, claim_pattern, competes, excludes,
                         frame, run, signal_audit, slots)
from units.graph import Node
from units.engine import StandingUnit
from units.sieve import (BASELINE, INERT, LEAK, PASS, REFUSED, axis_appeals, axis_audit, baseline,
                         factorization_audit, guard_density, impure_slots, interactions, probe,
                         seed_is_sound, sweep)


# -- 1. the instrument ------------------------------------------------------------------------------

@pytest.mark.parametrize("guarded", [False, True])
def test_the_seed_is_sound_before_anything_is_composed(guarded):
    """The precondition. If the all-defaults cell — an unqualified affirmation about the world —
    violates anything, no verdict about a composite means anything."""
    assert seed_is_sound(guarded) == ()


def test_the_sieve_catches_a_planted_leak():
    """**The negative control for the instrument.** A form whose elimination fires unconditionally is
    exactly the failure the sieve exists to find; if this passed, nothing else here would mean
    anything."""
    reckless = Form(
        "reckless", "content",
        introduce=lambda ctx: ctx.set("reckless", True),
        eliminate=lambda ctx: StandingUnit(
            "elim:reckless", claim_pattern(ctx), Attribute("s", PREDICATE, True)),
    )
    assert probe((reckless, ASK), guarded=True).outcome == LEAK
    assert probe((reckless, LANGUAGE), guarded=True).outcome == LEAK


def test_the_sieve_can_report_success():
    """**The control in the other direction.** A sieve that only ever says LEAK is measuring nothing.
    With every elimination guarded *and* a pair entry for the composite, one cell composes."""
    assert probe((NEGATION, DEGREE), guarded=True, composed=True).outcome == PASS


def test_a_cell_with_one_non_default_form_grades_nothing():
    """It is its own control, so calling it INERT would be an artifact of comparing it to itself."""
    assert probe((NEGATION,), guarded=True).outcome == BASELINE


def test_incompatible_forms_refuse_rather_than_overwrite():
    """`cnl.md` §1 — create, never merge. Two forms wanting one slot at different values is a genuine
    incompatibility, and REFUSED is a closed, honest outcome."""
    assert probe((POSITIVE, NEGATION)).outcome == REFUSED
    assert probe((ASSERT, ASK)).outcome == REFUSED


# -- 2. the axes, measured --------------------------------------------------------------------------

def test_the_measured_slots_outnumber_the_declared_axes():
    """⭐ **The finding.** Two forms occupy one slot iff they exclude each other — the standard move in
    feature theory, and the only evidence available about how many axes there are. `content` is not one
    axis: polarity and strength combine freely, so they are two."""
    audit = axis_audit()
    assert audit["n_declared"] == 3
    assert audit["n_measured"] == 4
    assert "content" in audit["axes_split_by_evidence"]


def test_polarity_is_a_slot_and_degree_is_not_in_it():
    assert excludes(POSITIVE, NEGATION)
    assert not excludes(POSITIVE, DEGREE)
    assert not excludes(NEGATION, DEGREE)


def test_framing_by_the_declared_axis_cannot_give_a_graded_claim_a_polarity():
    """The sharpest evidence that `content` is not one axis: **the declared assignment prevents the
    cells from being built correctly.** Framing by axis sees `degree` fill `content` and adds no
    polarity, so a guarded elimination is handed a claim with no polarity to read."""
    by_slot = {f.name for f in frame((DEGREE,))}
    assert "positive" in by_slot, "framing by measured slot supplies the missing polarity"

    filled_axes = {f.axis for f in (DEGREE,)}
    assert "content" in filled_axes, "…which framing by declared axis would treat as already filled"


# -- 3. what the sweep finds ------------------------------------------------------------------------

def test_asking_a_question_asserts_it_when_the_elimination_ignores_force():
    """`forms_discourse` §8's worked failure, mechanized: map the content perfectly, then assert it —
    every content check passes and the utterance has been comprehensively misunderstood."""
    v = probe((POSITIVE, ASK))
    assert v.outcome == LEAK and "asking it committed the system" in v.detail


def test_a_claim_about_the_word_commits_the_system_about_the_thing():
    v = probe((POSITIVE, LANGUAGE))
    assert v.outcome == LEAK and "about the WORD" in v.detail


def test_the_documented_degree_negation_leak_reproduces():
    """⚠ The one leak on record (`forms_discourse` §4.2), which was measured on the **retired** engine
    with mechanisms that no longer exist. It is a phenomenon to re-probe, not a bug to reproduce — and
    it is still here: a degree elimination that does not consult polarity concludes the predicate under
    a denial, so the graph holds the claim and its denial at once."""
    ctx, view, _net = run(frame((NEGATION, DEGREE)), guarded=False)
    assert view.attr(ctx.subject, PREDICATE) is True
    assert view.attr(ctx.subject, f"not_{PREDICATE}") is True
    assert probe((NEGATION, DEGREE)).outcome == LEAK


def test_guarding_stops_the_leak_by_going_silent_which_is_not_composing():
    """⚠ **The result that matters.** Guarding removes every leak and buys nothing: the composite goes
    quiet, and *"not very dangerous"* becomes indistinguishable from *"not dangerous"* — the band is
    dropped rather than carried. `P8` calls introduction-without-elimination inert, and that is what a
    guard converts a leak into."""
    ctx, view, _net = run(frame((NEGATION, DEGREE)), guarded=True)
    assert view.attr(ctx.subject, PREDICATE) is None            # no leak
    assert view.attr(ctx.subject, f"not_{PREDICATE}") is True
    assert view.degree(ctx.subject, f"not_{PREDICATE}") is None  # …and no degree either
    assert probe((NEGATION, DEGREE), guarded=True).outcome == INERT


def test_a_pair_entry_composes_what_a_guard_only_silenced():
    """And the fix is an entry **per pair**, which is the O(n²) a local harmony check was supposed to
    make unnecessary."""
    ctx, view, _net = run(frame((NEGATION, DEGREE)), guarded=True, composed=True)
    assert view.attr(ctx.subject, f"not_{PREDICATE}") is True
    assert view.degree(ctx.subject, f"not_{PREDICATE}") == "likely"
    assert view.attr(ctx.subject, PREDICATE) is None


def test_guards_alone_never_produce_a_single_composing_cell():
    """The whole guarded sweep: zero leaks, and **zero passes**. Every composite either refuses, is its
    own baseline, or goes inert."""
    verdicts = sweep(guarded=True)
    assert not [v for v in verdicts if v.outcome == LEAK]
    assert not [v for v in verdicts if v.outcome == PASS]


def test_one_pair_entry_buys_exactly_one_composing_cell():
    """The cost curve, at n=1. Nothing about a pair entry generalizes to the other pairs."""
    verdicts = sweep(guarded=True, composed=True)
    assert len([v for v in verdicts if v.outcome == PASS]) == 1


# -- 4. the numbers this exists to produce ----------------------------------------------------------

def test_most_pairs_that_can_combine_do_not():
    """`forms_discourse` §4.2's tractability claim is that a local per-form harmony check *buys* global
    closure. Measured over pairs that can co-occur at all, more than half leak."""
    naive = interactions(guarded=False)
    assert naive["pairs_that_combine"] >= 12
    assert naive["leak_rate"] > 0.5


def test_guard_density_is_high_and_the_guards_only_silence():
    d = guard_density()
    assert d["density"] > 0.5
    assert not d["still_leaking"]
    # …and nearly every "fix" was a composite going quiet rather than composing.
    assert len(d["guard_made_inert"]) >= d["fixed_by_guard"] - 2


def test_a_commitment_cannot_be_stated_without_naming_other_slots():
    """The specification-level form of the same problem. If the axes were orthogonal this would be
    zero: a commitment on one axis would be statable in that axis's own terms."""
    appeals = axis_appeals()
    assert appeals["needing_other_axes"] >= 3
    assert "force" in appeals["detail"]["degree"] and "polarity" in appeals["detail"]["degree"]


# -- 5. the candidate pool: each form is a hypothesis test on a documented decision ------------------

def test_the_candidate_pool_measures_eight_slots_against_three_declared_axes():
    """⭐ Enumerate **forms** and let the axes be measured. Fifteen forms drawn from the typological
    pool `forms_discourse` §3.6 names give eight slots — and neither `content` nor `force` is one."""
    audit = axis_audit(CANDIDATES)
    assert audit["n_declared"] == 3
    assert audit["n_measured"] == 8
    assert set(audit["axes_split_by_evidence"]) == {"content", "force"}


def test_three_of_the_six_declared_forces_are_not_forces():
    """⭐ **The drop from nine forces to six was right, and for reasons nobody recorded.** `deny` sits
    in the polarity slot, `hedge` in the strength slot, `norm` with modality. Only assert/ask/command
    actually compete for the force slot."""
    groups = slots(CANDIDATES)
    force_slot = next(sorted(m.name for m in v) for v in groups.values()
                      if any(m.name == "assert" for m in v))
    assert force_slot == ["ask", "assert", "command"]
    declared = {f.name for f in CANDIDATES if f.axis == "force"}
    assert declared - set(force_slot) == {"deny", "hedge", "norm"}


def test_deny_is_negation_under_another_name():
    """⭐ **The factorization sieve's first catch**, and the collision predicted from the documents:
    CONTENT lists *negation* and FORCE lists *deny*, which is the enumerate-the-product error `P1`
    exists to prevent. They effect the identical state change, so by `P3` they are one form."""
    audit = factorization_audit(CANDIDATES)
    assert ("deny",) in audit["composite"]["negation"]
    assert ("negation",) in audit["composite"]["deny"]


def test_hedge_shares_degrees_slot_without_being_degree():
    """The distinction the factorization sieve is for. `hedge` and `degree` compete for one field, so
    they are one slot — but they effect *different* state changes, so neither reduces to the other.
    **Same slot, different value.** That is what an axis with values looks like, measured."""
    assert competes(HEDGE, DEGREE)
    audit = factorization_audit(CANDIDATES)
    assert "hedge" in audit["prime"] and "degree" in audit["prime"]


def test_evidentiality_and_mirativity_land_in_slots_of_their_own():
    """⚠ The forms that fit no declared axis. Neither is *what is claimed*, *what is done with it*, nor
    *what it is about* — one is how the claim was come by, the other the speaker's stance on it. Both
    are in `forms_discourse`'s own typological pool and neither has ever been placed."""
    groups = slots(CANDIDATES)
    singles = {next(iter(v)).name for v in groups.values() if len(v) == 1}
    assert {"evidential", "mirative"} <= singles


def test_the_two_slot_signals_agree_wherever_both_can_see():
    """The cross-check that keeps `slots()` from measuring nothing but the author's field names. Every
    refusal is also a shared field; the extra pairs signal B catches are the graded ones, where bands
    `meet` instead of conflicting and refusal is structurally blind."""
    audit = signal_audit(CANDIDATES)
    assert audit["refusal_only"] == []
    assert ("degree", "hedge") in audit["shared_field_only"]


def test_a_form_whose_conclusion_is_untracked_looks_identical_to_every_other_one():
    """⚠ The instrument bug that produced a page of nonsense: `P3` makes a form's identity its state
    change, so a form whose marker is missing from `CONCLUSIONS` has **no** measurable identity and
    factors into anything. Pinned because it fails silently and plausibly."""
    from units.forms import CONCLUSIONS
    for f in CANDIDATES:
        _c, _v, sig = baseline(f, guarded=False, inventory=CANDIDATES)
        assert sig is not None, f"{f.name} refused in its own frame"
    assert {"normative", "permitted", "held_then", "sourced", "surprising"} <= set(CONCLUSIONS)
