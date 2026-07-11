"""
Predicate-NAC generalization on the goal path — the ISA arc, Phase 1 (the MAIN gap).

The NAC->materialized-positive completion of `test_isa_goal_nac.py` was shown for the COPULA
(`not ?c is P` -> `is_not`). The card trader's NACs are on RELATION MARKERS —
`not ?act overridden <yes>`, `not ?o stance encouraged`, `not ?o dominated <yes>` — a literal
predicate with a ground object and a body-bound subject. This file pins that `GoalSolver` now
lowers those to `R_not` completion (the copula being the `R = is` special case) and, crucially,
DIFFERENTIAL-TESTS it against the SHIPPED engine on the two REAL banks:

  - `corpus/preference.cnl` stance rules (`encouraged`/`discouraged`/`neutral`, where `neutral`
    is the DEFAULT defended by two ground-object NACs), and
  - `corpus/policy.cnl` class-norm rules (a forbidden action `excluded` UNLESS `overridden` by a
    higher-ranked source — the card trader's keystone override).

The oracle is `authoring.run_rules` (the STRATIFIED forward driver the card trader runs under via
`planning.solve`), NOT `rewriter.run` (the naive single-fixpoint driver, which evaluates a NAC
against a partial graph and so derives the unsound `op stance neutral` alongside `op stance
encouraged`). The goal-directed completion's nested-complete-solve IS the goal-directed analog of
stratifying the producer below the consumer, so it must reproduce the stratified answer exactly.
"""
import pathlib

import ugm as h
from ugm.cnl.authoring import run_rules
from ugm.cnl.machine_rules import load_machine_rules
from ugm import to_attrgraph, derived_triples, Goal, GoalSolver

_CORPUS = pathlib.Path(__file__).resolve().parent.parent / "corpus"


def _graph(triples: list[tuple[str, str, str]]) -> h.Graph:
    g = h.Graph()
    seen: dict[str, str] = {}

    def node(n: str) -> str:
        if n not in seen:
            seen[n] = g.add_node(n)
        return seen[n]

    for s, p, o in triples:
        g.add_relation(node(s), p, node(o))
    return g


def _forward_marks(triples: list[tuple[str, str, str]], rules, pred: str) -> set[tuple[str, str]]:
    """The stratified forward engine's derived `pred` (subject, object) pairs — the oracle."""
    g = _graph(triples)
    run_rules(g, rules, provenance=False)
    return {(g.name(s), g.name(o))
            for s in g.nodes() for r, o in g.relations_from(s) if g.has_key(r, pred)}


def _goal_marks(triples, rules, pred: str, subjects: list[str], obj: str | None = None,
                objs: list[str] | None = None) -> set[tuple[str, str]]:
    """The goal-directed solver's answers for `pred`, demanded per (subject, object) — mirrors
    what a forward run materializes, but only for the demanded goals."""
    ag, _ = to_attrgraph(_graph(triples))
    solver = GoalSolver(ag, rules)
    out: set[tuple[str, str]] = set()
    for s in subjects:
        for o in (objs if objs is not None else [obj]):
            out |= solver.solve(Goal(pred, s, o))
    return out


# ============================================================================================
# Bank 1 — preference.cnl stance rules: the DEFAULT (`neutral`) defended by two ground NACs
# ============================================================================================

_STANCE_RULES = load_machine_rules("""
?o stance encouraged when ?o is_a ?act and ?act encouraged ?src
?o stance discouraged when ?o is_a ?act and ?act discouraged ?src
?o stance neutral when ?o add ?c and not ?o stance encouraged and not ?o stance discouraged
""")

# op1 -> encouraged (buy is encouraged), op2 -> discouraged (sell is discouraged),
# op3 -> neutral (trade has no advice, so both NACs pass).
_STANCE_FACTS = [
    ("op1", "is_a", "buy"), ("buy", "encouraged", "today"), ("op1", "add", "gg"),
    ("op2", "is_a", "sell"), ("sell", "discouraged", "standing"), ("op2", "add", "gg"),
    ("op3", "is_a", "trade"), ("op3", "add", "gg"),
]
_STANCES = ["encouraged", "discouraged", "neutral"]


def test_stance_neutral_default_fires_only_when_both_nacs_pass():
    # op3 has no deontic advice -> both `not stance encouraged` / `not stance discouraged` hold
    # -> neutral. op1/op2 have advice -> their neutral default is DEFEATED.
    ag, _ = to_attrgraph(_graph(_STANCE_FACTS))
    solver = GoalSolver(ag, _STANCE_RULES)
    assert solver.solve(Goal("stance", "op3", "neutral")) == {("op3", "neutral")}
    assert solver.solve(Goal("stance", "op1", "neutral")) == set()   # defeated by `encouraged`
    assert solver.solve(Goal("stance", "op2", "neutral")) == set()   # defeated by `discouraged`


def test_stance_matches_the_stratified_forward_engine():
    # the whole stance relation, demanded per (op, stance), equals the stratified forward run.
    forward = _forward_marks(_STANCE_FACTS, _STANCE_RULES, "stance")
    goal = _goal_marks(_STANCE_FACTS, _STANCE_RULES, "stance",
                       subjects=["op1", "op2", "op3"], objs=_STANCES)
    assert goal == forward
    assert goal == {("op1", "encouraged"), ("op2", "discouraged"), ("op3", "neutral")}


def test_stance_not_is_materialized_as_a_positive_fact():
    # the completion mints an explicit `op3 stance_not encouraged` (and `_not discouraged`) — a
    # positive fact matched positively, the decide line generalized past the copula.
    ag, _ = to_attrgraph(_graph(_STANCE_FACTS))
    solver = GoalSolver(ag, _STANCE_RULES)
    before = derived_triples(solver.ag)
    solver.solve(Goal("stance", "op3", "neutral"))
    new = derived_triples(solver.ag) - before
    assert ("op3", "stance_not", "encouraged") in new
    assert ("op3", "stance_not", "discouraged") in new
    # op1 IS encouraged, so its default was defeated and no `op1 stance_not encouraged` minted
    assert ("op1", "stance_not", "encouraged") not in derived_triples(solver.ag)


# ============================================================================================
# Bank 2 — policy.cnl class norms: `excluded` UNLESS `overridden` (the keystone override)
# ============================================================================================

_POLICY_RULES = load_machine_rules(
    (_CORPUS / "policy.cnl").read_text(encoding="utf-8"))

# A standing prohibition on selling. Without an override, sell_x (is_a sell) is excluded.
_FORBID_FACTS = [
    ("sell_x", "is_a", "sell"), ("sell", "forbidden", "standing"),
]
# ... plus a higher-ranked source encouraging the same action -> `sell` is overridden -> NOT excluded.
_OVERRIDE_FACTS = _FORBID_FACTS + [
    ("sell", "encouraged", "today"), ("today", "outranks", "standing"),
]


def test_forbidden_action_excludes_its_operator():
    # no override -> the `not ?act overridden <yes>` NAC passes -> sell_x excluded.
    ag, _ = to_attrgraph(_graph(_FORBID_FACTS))
    solver = GoalSolver(ag, _POLICY_RULES)
    assert solver.solve(Goal("excluded", "sell_x", "<yes>")) == {("sell_x", "<yes>")}


def test_override_defeats_the_exclusion():
    # today's encouragement outranks the standing prohibition -> `sell overridden <yes>` -> the
    # `not overridden` NAC FAILS -> sell_x is NOT excluded (the demo's keystone, goal-directed).
    ag, _ = to_attrgraph(_graph(_OVERRIDE_FACTS))
    solver = GoalSolver(ag, _POLICY_RULES)
    assert solver.solve(Goal("excluded", "sell_x", "<yes>")) == set()
    # ... and the override itself is derived (the positive that defeats the default).
    assert solver.solve(Goal("overridden", "sell", "<yes>")) == {("sell", "<yes>")}


def test_exclusion_matches_the_stratified_forward_engine():
    for facts in (_FORBID_FACTS, _OVERRIDE_FACTS):
        forward = _forward_marks(facts, _POLICY_RULES, "excluded")
        goal = _goal_marks(facts, _POLICY_RULES, "excluded", subjects=["sell_x"], obj="<yes>")
        assert goal == forward
