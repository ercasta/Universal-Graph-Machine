"""Shipped-vs-grammar ROUTE AGREEMENT — a parametrized reasoning-equivalence gate.

WHY THIS EXISTS (2026-07-22). `test_grammar_route_reasoning.py` pins the grammar route against FIXED
expected answers; this module is the complementary, stronger gate: it runs each reasoning scenario through
BOTH routes — the shipped route (a plain KB, no grammar) and the grammar route (a declared grammar,
`open_class="noun"`, the default-grammar config) — and asserts the two routes reason IDENTICALLY, and that
they land on the expected answer. Any engine change that makes the grammar route diverge from the shipped
route (the exact class of regression that stayed 953-green while breaking banded/enumeration reasoning) now
fails here, in the committed suite, with the scenario named.

SCOPE: reasoning correctness only, over MORPHOLOGY-CLEAN phrasings. Known SURFACE gaps (open-class verb
morphology, predicating `X prep Y`, `is_a` rendering) are deliberately OUT — a scenario is admitted only
when both routes can carry it, so a failure here is a REASONING divergence, never a surface gap. When the
grammar route grows a surface (e.g. predicating `X prep Y` clauses), add the scenario here to lock the two
routes together on it.
"""
from __future__ import annotations

import pathlib

import pytest

from ugm import AttrGraph
from ugm.cnl import grammar_intake as gi
from ugm.intake import ingest
from ugm.policy import FirmwarePolicy

CORPUS = (pathlib.Path(__file__).resolve().parent.parent / "corpus" / "loudon_grammar.cnl").read_text(
    encoding="utf-8"
)
BANDED = FirmwarePolicy(uncertainty="banded")


# (id, lines-to-ingest-then-the-query-is-the-last-line, expected-answer, policy)
SCENARIOS = [
    (
        # A COPULA fact (both routes carry it). Arbitrary S-V-O intake (`lion has mane`) is deliberately
        # NOT here: the shipped route only recognizes copula facts, so an S-V-O yes/no is a grammar-route
        # CAPABILITY, not a shared reasoning shape — testing it would compare against a route that never
        # stored the fact. S-V-O agreement belongs in the grammar-only gate.
        "stored-fact-yesno",
        ["lion is proud", "is lion proud"],
        ["yes"],
        None,
    ),
    (
        "copula-rule-derivation",
        ["lion is strong", "?x is fierce when ?x is strong", "is lion fierce"],
        ["yes"],
        None,
    ),
    (
        "multi-hop-rule-chain",
        [
            "lion is strong",
            "?x is fierce when ?x is strong",
            "?x is scary when ?x is fierce",
            "is lion scary",
        ],
        ["yes"],
        None,
    ),
    (
        "two-premise-join-across-mentions",
        [
            "rex is a pet",
            "rex is strong",
            "?x is cool when ?x is a pet and ?x is strong",
            "is rex cool",
        ],
        ["yes"],
        None,
    ),
    (
        "naf-defeasible-holds",
        [
            "ada is a suspect",
            "?x is thief when ?x is a suspect and ?x is not cleared",
            "is ada thief",
        ],
        ["yes"],
        None,
    ),
    (
        "naf-defeated-by-clearance",
        [
            "ada is a suspect",
            "ada is cleared",
            "?x is thief when ?x is a suspect and ?x is not cleared",
            "is ada thief",
        ],
        ["no (assumed)"],
        None,
    ),
    (
        "negative-control-unknown-fact",
        ["ada is a suspect", "is bo a suspect"],
        ["no (assumed)"],
        None,
    ),
    (
        "wh-enumeration",
        ["ada is a suspect", "bo is a suspect", "who is a suspect"],
        ["ada is_a suspect", "bo is_a suspect"],
        None,
    ),
    (
        "banded-question-over-hedge",
        [
            "cy is a suspect",
            "?p is thief when ?p is a suspect and ?p is not alibied",
            "cy is unlikely alibied",
            "is cy thief",
        ],
        ["likely"],
        BANDED,
    ),
]


def _run(lines, *, grammar, policy):
    """Ingest all lines through the chosen route; return the final query's answer (order-normalized)."""
    kb, rules = AttrGraph(), []
    if grammar:
        gi.declare_grammar(kb, CORPUS, open_class="noun")
    out = None
    for line in lines[:-1]:
        ingest(kb, rules, line)
    out = ingest(kb, rules, lines[-1], policy=policy) if policy else ingest(kb, rules, lines[-1])
    return sorted(out.answer or [])


@pytest.mark.parametrize("scenario_id, lines, expected, policy",
                         SCENARIOS, ids=[s[0] for s in SCENARIOS])
def test_the_two_routes_reason_identically(scenario_id, lines, expected, policy):
    shipped = _run(lines, grammar=False, policy=policy)
    grammar = _run(lines, grammar=True, policy=policy)
    # The routes must AGREE — an engine change that splits them fails here first.
    assert grammar == shipped, f"{scenario_id}: grammar {grammar!r} != shipped {shipped!r}"
    # ...and both must land on the intended answer, so an agreement on a WRONG answer is caught too.
    assert grammar == sorted(expected), f"{scenario_id}: {grammar!r} != expected {sorted(expected)!r}"
