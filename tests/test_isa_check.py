"""
Phase 5.1 — CHECK firmware (`harneskills/isa/check.py`): bounded completion -> a 4-status verdict
under CWA-default, with a renderable "where I looked" trace.

Two obligations:
  1. the FOUR statuses are distinguished (positive / entailed-no / assumed-no / unknown), and
  2. the COLLAPSED verdict (yes/no/unknown) equals the reference `query.ask_goal` verdict, which
     `GoalSolver` computes — differentially, over many random positive banks and goals.
"""
import random

import ugm as h
from ugm import Pat, Rule
from ugm import (
    AttrGraph, to_attrgraph, Goal, GoalSolver,
    check, collapse, explain_check,
    POSITIVE, ENTAILED_NEG, ASSUMED_NO, UNKNOWN,
)


def _facts(triples) -> AttrGraph:
    g = AttrGraph()
    ids: dict[str, str] = {}

    def node(name: str) -> str:
        if name not in ids:
            ids[name] = g.add_node(name)
        return ids[name]

    for s, p, o in triples:
        g.add_relation(node(s), p, node(o))
    return g


def _reify(rules) -> AttrGraph:
    rg = AttrGraph()
    for r in rules:
        h.write_rule(rg, r)
    return rg


BIRD_FLIES = Rule(key="bird_flies", lhs=[Pat("?x", "is", "bird")], rhs=[Pat("?x", "is", "flyer")])
PENGUIN_NOFLY = Rule(key="peng_nofly", lhs=[Pat("?x", "is", "penguin")], rhs=[Pat("?x", "is_not", "flyer")])


# --- the four statuses ---------------------------------------------------------------------------

def test_positive_when_derivable():
    g = _facts([("robin", "is", "bird")])
    assert check(g, _reify([BIRD_FLIES]), ("is", "robin", "flyer")) == POSITIVE


def test_assumed_no_is_the_closed_world_default():
    g = _facts([("robin", "is", "bird")])
    # robin is not a penguin, nothing derives it, and `penguin` is closed-world by default
    assert check(g, _reify([BIRD_FLIES]), ("is", "robin", "penguin")) == ASSUMED_NO


def test_unknown_for_an_open_world_concept():
    g = _facts([("robin", "is", "bird")])
    # `hungry` is declared OPEN — absence is not falsity, so gather instead of assuming no
    assert check(g, _reify([BIRD_FLIES]), ("is", "robin", "hungry"),
                 open_preds=frozenset({"hungry"})) == UNKNOWN


def test_entailed_no_when_the_negative_is_derivable():
    g = _facts([("tweety", "is", "penguin")])
    # the positive `tweety is flyer` is not derivable, but `tweety is_not flyer` IS -> a HARD no
    assert check(g, _reify([BIRD_FLIES, PENGUIN_NOFLY]), ("is", "tweety", "flyer")) == ENTAILED_NEG


def test_collapse_maps_the_four_statuses_to_yes_no_unknown():
    assert collapse(POSITIVE) == "yes"
    assert collapse(ENTAILED_NEG) == "no"
    assert collapse(ASSUMED_NO) == "no"
    assert collapse(UNKNOWN) == "unknown"


def test_explain_check_renders_where_i_looked():
    g = _facts([("robin", "is", "bird")])
    rg = _reify([BIRD_FLIES])
    status = check(g, rg, ("is", "robin", "penguin"))
    lines = explain_check(status, rg)
    assert lines[0].startswith("assumed no")                   # the honest defeasible verdict
    assert "  looked for:" in lines
    assert any("robin is penguin" in ln for ln in lines)       # the demand it explored, rendered


# --- differential gate: collapse(check) == GoalSolver-based ask_goal verdict ----------------------

RULES = [
    Rule(key="is_a_trans",
         lhs=[Pat("?a", "is_a", "?b"), Pat("?b", "is_a", "?c")],
         rhs=[Pat("?a", "is_a", "?c")]),
    Rule(key="inherit",
         lhs=[Pat("?x", "is_a", "?t"), Pat("?t", "has", "?p")],
         rhs=[Pat("?x", "has", "?p")]),
    Rule(key="cold_slow", lhs=[Pat("?x", "has", "cold")], rhs=[Pat("?x", "has", "slow")]),
]
ATTRS = ["cold", "heavy", "hot"]
# `has` is open-world (its relational concept-key), `is_a` closed — so the sweep exercises all three
# verdicts: derivable -> yes, underivable is_a -> assumed-no, underivable has -> unknown.
OPEN = frozenset({"has"})


def _random_graph(rng):
    g = h.Graph()
    ids: dict[str, str] = {}

    def node(n):
        ids[n] = ids[n] if n in ids else g.add_node(n)
        return ids[n]

    ents = [f"e{i}" for i in range(rng.randint(2, 3))]
    types = [f"t{i}" for i in range(2)]
    for _ in range(rng.randint(2, 4)):
        g.add_relation(node(rng.choice(ents)), "is_a", node(rng.choice(types)))
    for _ in range(rng.randint(1, 3)):
        g.add_relation(node(rng.choice(types)), "has", node(rng.choice(ATTRS)))
    return g, ents + types + ATTRS + ["slow"]


def _oracle_verdict(g0, goal):
    rel, subj, obj = goal
    ag, _ = to_attrgraph(g0)
    found = bool(GoalSolver(ag, RULES).solve(Goal(rel, subj, obj)))
    if found:
        return "yes"
    key = obj if (rel == "is" and obj is not None) else rel     # concept_key
    return "unknown" if key in OPEN else "no"


def test_collapsed_check_matches_goalsolver_verdict_on_positive_banks():
    checked = 0
    for seed in range(12):
        rng = random.Random(seed)
        g0, names = _random_graph(rng)
        for rel in ("is_a", "has"):
            for subj in names:
                for obj in names:
                    want = _oracle_verdict(g0, (rel, subj, obj))
                    ag, _ = to_attrgraph(g0)
                    got = collapse(check(ag, _reify(RULES), (rel, subj, obj), open_preds=OPEN))
                    assert got == want, (
                        f"seed={seed} {rel}({subj},{obj}): firmware {got} != oracle {want}"
                    )
                    checked += 1
    assert checked > 500
