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


def test_a_propositional_cause_link_derives_over_grammar_folded_propositions(gkb):
    # THE NODE-BOUND-JOIN case (the token/entity duality). A `that A causes that B` link emits content-keyed
    # HANDLES whose `subj`/`obj` edges intern by name to the proposition's TOKENS (on the grammar route those
    # names are surface tokens denoting the interpretation ENTITIES the fold wrote to). The reify-bridge's
    # node-bound `?s` then binds the token — but the demand fetch reads a bound endpoint as its CANONICAL
    # CLASS (`chain._canon_class`, the derivation-frame identity boundary), so the join sees the entity's
    # folded content and the consequent derives. Regression gate for that boundary (which RETIRED the
    # per-site `intern_denoted` write patch, 2026-07-23; a union, not the reverted slice-1c single PICK
    # that dropped the token-resident comparison fact). See docs/design/derivation_frame.md.
    kb, rules = gkb
    _ingest_all(kb, rules, ["door1 is open", "that door1 is open causes that cat is scared"])
    assert ingest(kb, rules, "is cat scared").answer == ["yes"]


def test_a_propositional_cause_link_alone_does_not_assert_the_consequent(gkb):
    # The re-break of the test above: with the antecedent NOT stated, the link derives nothing — the
    # consequent is a CONSEQUENCE of A holding, not a free-standing assertion (soundness).
    kb, rules = gkb
    ingest(kb, rules, "that door1 is open causes that cat is scared")
    assert ingest(kb, rules, "is cat scared").answer == ["no (assumed)"]


def _adj_gkb():
    """A grammar KB with the copula adjectives declared (so `is safe`/`is hungry`/`is dangerous` are
    properties, not open nouns) — the config the epistemic-closure causation cells run under."""
    g = AttrGraph()
    gi.declare_grammar(g, CORPUS.read_text(encoding="utf-8")
                       + "\nsafe is a adj\nhungry is a adj\ndangerous is a adj\n", open_class="noun")
    return g, []


def test_propositional_cause_over_a_negated_antecedent_reasons():
    # CAUSATION ∘ NEGATION (docs/design/composition_architecture.md §GAPS). A `that A causes that B`
    # whose antecedent is a NEGATION now folds the handle to the faithful `has_not` predicate — the
    # producer bug was `_clause` reading `(lion, has, no)` (the negator as object), so the reify bridge
    # never matched the fact route's `has_not`. Antecedent-first: link-first is blocked by the SEPARATE
    # handle-node-duplication order issue (a third co-named `lion` node with no `denotes` link), not the
    # composition axis.
    kb, rules = _adj_gkb()
    _ingest_all(kb, rules, ["the lion has no mane",
                            "that lion has no mane causes that lion is safe"])
    assert ingest(kb, rules, "is lion safe").answer == ["yes"]


def test_propositional_cause_over_a_hedged_antecedent_carries_the_band():
    # CAUSATION ∘ DEGREE (composition_architecture.md §GAPS). A hedged antecedent (`that lion generally
    # is hungry causes …`) now strips the hedge in `_clause` so the handle matches the banded FORK the
    # fact route pens; under a banded stance the band rides the reification bridge into the consequent.
    # Antecedent-first (same order caveat as the negation case).
    kb, rules = _adj_gkb()
    _ingest_all(kb, rules, ["lion generally is hungry",
                            "that lion generally is hungry causes that lion is dangerous"])
    assert ingest(kb, rules, "is lion dangerous", policy=BANDED).answer == ["likely"]


def test_a_define_schema_materialises_over_the_grammar_route(gkb):
    # THE FORWARD-MATCH CONTROL-GUARD case. `define schema ?r is transitive : …` then the trigger fact
    # `ancestor is transitive` (folded on the grammar route) fires the schema meta-bank FORWARD to
    # materialise the transitivity rule. On the grammar route the folded fact leaves its `is_a` content
    # on BOTH the entity AND an interpretation CONTROL node; forward matching keeps control nodes visible
    # (unlike the demand `_guard`), so before the `fact_only` guard the meta-rule bound the unnamed
    # control node too and reflected a MALFORMED rule -> `expand_rules` CRASHED (`k_pred resolves to no
    # token`). With the guard the meta-bank matches facts only, and the concrete rule derives correctly.
    from ugm.lowering import assemble_facts
    from ugm.machine import Machine
    from ugm.cnl.query import ask_goal
    kb, rules = gkb
    ingest(kb, rules, "define schema ?r is transitive : ?a ?r ?c when ?a ?r ?b and ?b ?r ?c")
    Machine().run(kb, assemble_facts([("alice", "ancestor", "bob"), ("bob", "ancestor", "carol"),
                                      ("carol", "ancestor", "dave")]))
    ingest(kb, rules, "ancestor is transitive")            # grammar route — was the crash
    assert ask_goal(kb, ("yesno", "alice", "ancestor", "dave"), rules) == ["yes"]   # transitive
    assert ask_goal(kb, ("yesno", "dave", "ancestor", "alice"), rules) != ["yes"]   # not symmetric


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
