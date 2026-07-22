"""Grammar-route REASONING coverage — the committed regression gate for the default-grammar route.

WHY THIS EXISTS (2026-07-22). The shipped suite exercises the grammar route's SURFACE (routing, forces,
vocabulary, hedging, reconsider — `test_grammar_intake.py`) but almost none of its deep REASONING, so an
engine change could pass the whole suite 953-green and still regress grammar-route reasoning — measured
directly: a `denotes`-resolution change to `chain.py` stayed 953-green yet broke banded/enumeration
reasoning that only a scratchpad flip-harness caught. This module runs representative REASONING scenarios
THROUGH the grammar route (a declared grammar, `open_class="noun"` — the default-grammar config) so those
regressions are gated by the committed suite, not a monkeypatch.

SCOPE: reasoning correctness (rules, coref, NAF, banded, enumeration), NOT surface coverage. Known SURFACE
gaps (open-class verb morphology `outrank`/`outranks`; predicating `X prep Y` clauses; `is_a` vs `is a`
rendering) are the prose->CNL translator's / grammar-file's job and are deliberately OUT — asserting them
here would test the surface, which is the last concern. Phrasings are chosen to be morphology-clean so each
test isolates reasoning.
"""
from __future__ import annotations

import pathlib

import pytest

from ugm import AttrGraph
from ugm.cnl import grammar_intake as gi
from ugm.intake import ingest
from ugm.policy import FirmwarePolicy

CORPUS = pathlib.Path(__file__).resolve().parent.parent / "corpus" / "loudon_grammar.cnl"
BANDED = FirmwarePolicy(uncertainty="banded")


@pytest.fixture
def gkb():
    """A KB whose reasoning path IS the grammar route: the canonical grammar declared with open
    vocabulary (`open_class="noun"`), the config a default grammar would run under."""
    g = AttrGraph()
    gi.declare_grammar(g, CORPUS.read_text(encoding="utf-8"), open_class="noun")
    return g, []


def _ingest_all(kb, rules, lines):
    for line in lines:
        ingest(kb, rules, line)


def test_a_stored_fact_answers_its_yesno_question(gkb):
    kb, rules = gkb
    ingest(kb, rules, "lion has mane")
    assert ingest(kb, rules, "does lion have mane").answer == ["yes"]


def test_a_copula_rule_derives_over_a_grammar_fact(gkb):
    # A rule reaches the rule layer (above the grammar dispatch) and fires over a fact folded on the
    # grammar route — the derived conclusion is then found by a yes/no question.
    kb, rules = gkb
    _ingest_all(kb, rules, ["lion is strong", "?x is fierce when ?x is strong"])
    assert ingest(kb, rules, "is lion fierce").answer == ["yes"]


def test_a_two_premise_rule_joins_across_coreferent_mentions(gkb):
    # Two facts about one entity stated in SEPARATE sentences must intern to ONE entity, or the
    # two-premise join derives nothing. This is the coref half of the token/entity duality: content
    # from distinct mentions composes on the interpretation entity.
    kb, rules = gkb
    _ingest_all(kb, rules, ["rex is a pet", "rex is strong",
                            "?x is cool when ?x is a pet and ?x is strong"])
    assert ingest(kb, rules, "is rex cool").answer == ["yes"]


def test_negation_as_failure_decides_a_defeasible_rule(gkb):
    # `?x is thief when ?x is a suspect and ?x is not cleared`: with no clearance the NAF premise holds
    # (closed-world), so the defeasible conclusion is drawn.
    kb, rules = gkb
    _ingest_all(kb, rules, ["ada is a suspect",
                            "?x is thief when ?x is a suspect and ?x is not cleared"])
    assert ingest(kb, rules, "is ada thief").answer == ["yes"]


def test_a_clearance_defeats_the_defeasible_conclusion(gkb):
    # The re-break of the NAF test: a positive `cleared` fact makes the `not cleared` premise fail, so
    # the conclusion is withdrawn — the reasoning is genuinely defeasible, not monotone.
    kb, rules = gkb
    _ingest_all(kb, rules, ["ada is a suspect", "ada is cleared",
                            "?x is thief when ?x is a suspect and ?x is not cleared"])
    assert ingest(kb, rules, "is ada thief").answer == ["no (assumed)"]


def test_wh_enumeration_returns_the_witnesses_without_a_surface_leak(gkb):
    # The wh-enumeration reads the GUARDED fact enumerator: exactly the two suspects, and NO empty-named
    # `' is_a suspect'` row from a scaffolding node (the leak the crisp who-branch had before it used
    # `_facts_matching`). Rendered `is_a` (the internal predicate) — a surface nicety, out of scope.
    kb, rules = gkb
    _ingest_all(kb, rules, ["ada is a suspect", "bo is a suspect"])
    assert sorted(ingest(kb, rules, "who is a suspect").answer) == \
        ["ada is_a suspect", "bo is_a suspect"]


def test_a_banded_question_wears_its_doubt_over_a_hedged_premise(gkb):
    # A hedge authors a FORK; under a banded policy a rule reading through the fork answers at the
    # fork's band — the defeasible jump WEARS its doubt (`likely`) rather than collapsing to assumed-no.
    kb, rules = gkb
    _ingest_all(kb, rules, ["cy is a suspect",
                            "?p is thief when ?p is a suspect and ?p is not alibied",
                            "cy is unlikely alibied"])
    assert ingest(kb, rules, "is cy thief", policy=BANDED).answer == ["likely"]


def test_a_why_question_traces_the_derivation(gkb):
    # `why` returns the derivation trace (rule + given premise + NAF leap), not a yes/no, over the
    # grammar route's interpretation — no surface artifacts in the trace.
    kb, rules = gkb
    _ingest_all(kb, rules, ["ada is a suspect",
                            "?x is thief when ?x is a suspect and ?x is not cleared"])
    out = ingest(kb, rules, "why is ada thief")
    assert out.kind == "why"
    trace = "\n".join(out.explanation or [])
    assert "ada is thief" in trace and "ada is_a suspect" in trace
