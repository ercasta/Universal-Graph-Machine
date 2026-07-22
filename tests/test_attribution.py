"""Scope generalization SLICE 1 (docs/design/scope_generalization.md §5): the `holder` scope KIND.

The first scope kind beyond `epistemic`. It validates KIND DISPATCH and delivers the §4a attribution
block. The two properties under test are exactly the two the slice promises:

  - NON-VERIDICAL globally: a penned attribution is not the world's (`is the lion a cat` → assumed-no).
  - ONTOLOGICAL for the holder: for N, the attributed fact holds DEFINITELY — no possibility discount,
    even under a banded policy (contrast an epistemic fork, which reads back `likely`).
"""
from ugm.attrgraph import AttrGraph
from ugm.check import check, collapse, POSITIVE, ASSUMED_NO
from ugm.policy import FirmwarePolicy
from ugm.possibility import add_fork, band_word
from ugm.suppose import SCOPE_KIND, KIND_HOLDER, HOLDER, scope_kind, KIND_EPISTEMIC
from ugm.scope_kinds import consider, holder_scope_of, holds_for, holders_considering

BANDED = FirmwarePolicy(uncertainty="banded")


def _considered() -> AttrGraph:
    """N considers the lion a cat. Nothing is inked — the world has no opinion on lions being cats."""
    g = AttrGraph()
    consider(g, "N", ("lion", "is_a", "cat"))
    return g


# --- THE ACCEPTANCE (scope_generalization.md §5, Slice 1) -------------------------------------------

def test_acceptance_no_globally_yes_relative_to_the_holder():
    g = _considered()
    assert collapse(check(g, ("is_a", "lion", "cat"))) == "no"          # no, globally
    assert collapse(holds_for(g, "N", ("is_a", "lion", "cat"))) == "yes"  # yes, relative to N


def test_global_check_is_non_veridical():
    """A penned proposition is NOT the world's: the global verdict is the DEFEASIBLE assumed-no, not a
    hard entailed-no — the world simply has no record, exactly the CWA default."""
    g = _considered()
    assert check(g, ("is_a", "lion", "cat")) == ASSUMED_NO


def test_relativized_check_is_positive():
    g = _considered()
    assert holds_for(g, "N", ("is_a", "lion", "cat")) == POSITIVE


# --- ONTOLOGICAL vs EPISTEMIC — the kind dispatch that is the point of the slice -------------------

def test_holder_read_is_ontological_not_discounted():
    """The kind distinction, made visible under a banded policy: an EPISTEMIC fork reads back
    discounted (`likely`), but a HOLDER scope holds DEFINITELY for its holder — full strength, no
    possibility discount. Same read op, dispatched by the scope's kind (band-absence)."""
    g = AttrGraph()
    add_fork(g, 0.5, [("lion", "is_a", "predator")])       # epistemic: a weighed possibility
    consider(g, "N", ("lion", "is_a", "cat"))              # holder: N holds it definitely

    assert check(g, ("is_a", "lion", "predator"), policy=BANDED) == band_word(0.5)   # 'likely'
    assert holds_for(g, "N", ("is_a", "lion", "cat"), policy=BANDED) == POSITIVE      # certain, ontological


def test_holder_pencil_does_not_leak_into_the_global_banded_read():
    """Ontological non-veridicality holds under banding too: a holder pencil carries no band, so the
    global possibility overlay never surfaces it — `is the lion a cat` is assumed-no even banded."""
    g = _considered()
    assert check(g, ("is_a", "lion", "cat"), policy=BANDED) == ASSUMED_NO


# --- KEYING: one scope per holder, kinded and findable --------------------------------------------

def test_one_scope_per_holder_is_reused():
    g = AttrGraph()
    s1 = consider(g, "N", ("lion", "is_a", "cat"))
    s2 = consider(g, "N", ("lion", "is_a", "mammal"))      # same holder → same scope, accreted
    assert s1 == s2
    assert holds_for(g, "N", ("is_a", "lion", "cat")) == POSITIVE
    assert holds_for(g, "N", ("is_a", "lion", "mammal")) == POSITIVE


def test_holders_do_not_see_each_others_attributions():
    g = AttrGraph()
    consider(g, "N", ("lion", "is_a", "cat"))
    consider(g, "M", ("lion", "is_a", "dog"))
    assert holds_for(g, "N", ("is_a", "lion", "cat")) == POSITIVE
    assert holds_for(g, "N", ("is_a", "lion", "dog")) == ASSUMED_NO       # N does not hold M's view
    assert holds_for(g, "M", ("is_a", "lion", "dog")) == POSITIVE


def test_scope_carries_the_holder_kind_and_key():
    g = _considered()
    scope = holder_scope_of(g, "N")
    assert scope is not None
    assert scope_kind(g, scope) == KIND_HOLDER
    assert g.get_attr(scope, HOLDER).value == "N"


def test_holds_for_an_unknown_holder_is_assumed_no():
    """No scope for the holder ⇒ the goal is checked globally and, being unpenned, is assumed-no —
    never a crash."""
    g = _considered()
    assert holds_for(g, "STRANGER", ("is_a", "lion", "cat")) == ASSUMED_NO


def test_holders_considering_is_the_inverse():
    g = AttrGraph()
    consider(g, "N", ("lion", "is_a", "cat"))
    consider(g, "M", ("lion", "is_a", "cat"))
    consider(g, "M", ("lion", "is_a", "dog"))
    assert sorted(holders_considering(g, ("lion", "is_a", "cat"))) == ["M", "N"]
    assert holders_considering(g, ("lion", "is_a", "dog")) == ["M"]
    assert holders_considering(g, ("lion", "is_a", "fish")) == []


# --- ADDITIVITY: epistemic (unkinded) scopes are untouched ----------------------------------------

def test_epistemic_scopes_default_to_the_epistemic_kind():
    """The generalization is additive: an ordinary fork carries NO kind attr and dispatches as
    epistemic. Slice 1 must not have retroactively kinded existing scopes."""
    g = AttrGraph()
    scope = add_fork(g, 0.5, [("lion", "is_a", "predator")])
    assert g.get_attr(scope, SCOPE_KIND) is None
    assert scope_kind(g, scope) == KIND_EPISTEMIC
