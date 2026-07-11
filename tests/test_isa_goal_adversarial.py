"""
Phase 1.4 (implementation_plan.md) — adversarial tests for `GoalSolver`, the oracle every later
firmware phase is differentially checked against. These pin the exact invariants Phase 1.1/1.2
fixed, so a regression is caught immediately rather than surfacing as a mysterious downstream
answer flip:

  1. a `same_as` a RULE derives mid-solve (not just the `universal.same_as_rules` propagation set,
     which the solver filters out of its own rule list) must update node-level identity live;
  2. that update must be visible to the OUTER solver even when a NESTED solver (an existential-NAC
     group check, a negative completion) is the one that derives it;
  3. `_group_satisfiable`'s memoization (Phase 1.2) must never serve a stale verdict once the
     solver itself derives a new fact that would flip it;
  4. a genuine cross-goal negation cycle is caught (`NonStratifiable`) regardless of which side of
     the cycle is asked first — detection must not depend on goal-visitation order;
  5. independent goals answered through ONE solver instance get the same per-goal verdict
     regardless of the order they are asked in (no cross-goal state bleed through the tables /
     semi-naive delta bookkeeping a single instance shares across `.solve()` calls).
"""
import pytest

import ugm as h
from ugm import Goal, GoalSolver, NonStratifiable


# A bank DECLARING coref-following (any `same_as_rules` propagation rule — each carries the declared
# `coref_prop=True` role the solver reads in `__init__` to turn following ON, then filters the rules
# themselves out of `self.rules` as subsumed by the union-find). Without this the solver is coref-BLIND by design (each node its own
# identity regardless of `same_as` edges), so `GoalSolver(g, [])` would NOT be an adversarial test
# of the union-find fix at all — it would just be exercising the documented blind mode.
_FOLLOW_COREF_BANK = h.same_as_rules(["is_a"])


# ---- 1: a rule-derived `same_as` updates identity live -------------------------------------

def test_materialize_same_as_mid_solve_updates_identity_live():
    g = h.Graph()
    p1 = g.add_node("paul")
    p2 = g.add_node("paul")
    solver = GoalSolver(g, _FOLLOW_COREF_BANK)
    tok1 = solver._token(p1)          # caches p1 as its own singleton class
    tok2 = solver._token(p2)          # caches p2 as its own singleton class (the LOSING rep once
                                       # unioned, since `_sa_union`'s canonical rep is min(p1, p2))
    solver._materialize("same_as", tok1, tok2)     # a RULE deriving `same_as`, not pre-existing data
    assert solver._sa_find(p1) == solver._sa_find(p2)
    assert set(solver._nodes_of_token(solver._token(p1))) == {p1, p2}
    assert set(solver._nodes_of_token(solver._token(p2))) == {p1, p2}


# ---- 1b: identity tokens are NAME-FREE (Phase 2.4) ------------------------------------------

def test_duplicated_name_identity_token_is_name_free():
    # Phase 2.4: a coref class token carries only its class-rep NODE ID, never the surface name — the
    # name lives on the graph and is recovered at the render boundary (`_render`). A regression that
    # re-baked `name + SEP + rep` would put "paul" back into the token; this pins that it does not.
    g = h.Graph()
    p1 = g.add_node("paul")
    p2 = g.add_node("paul")
    solver = GoalSolver(g, _FOLLOW_COREF_BANK)
    solver._materialize("same_as", solver._token(p1), solver._token(p2))
    tok = solver._token(p1)
    assert tok == solver.SEP + solver._sa_find(p1)        # SEP + class-rep nid, nothing more
    assert "paul" not in tok                              # the NAME is not encoded in the identity
    assert solver._render(tok) == "paul"                  # ...it is recovered at the boundary
    # both mentions share ONE name-free identity, and it still denotes the whole class
    assert solver._token(p2) == tok
    assert set(solver._nodes_of_token(tok)) == {p1, p2}


# ---- 2: a NESTED solver's derived `same_as` is visible to the OUTER solver ------------------

def test_nested_solver_same_as_union_is_visible_to_the_outer_solver():
    g = h.Graph()
    p1 = g.add_node("paul")
    p2 = g.add_node("paul")
    outer = GoalSolver(g, _FOLLOW_COREF_BANK)
    outer._token(p1)
    outer._token(p2)                  # outer has already cached both as DISTINCT classes
    nested = GoalSolver(g, outer.rules, _materialized=outer._materialized, _justified=outer._justified,
                        _skolem=outer._skolem, _follow_coref=outer._follow_coref,
                        _name_ids=outer._name_ids, _sa_parent=outer._sa_parent,
                        _tok_cache=outer._tok_cache, _token_class=outer._token_class,
                        _group_sat_cache=outer._group_sat_cache)
    nested._materialize("same_as", outer._token(p1), outer._token(p2))
    # the OUTER instance must see the union immediately, not a private nested-only copy that is
    # discarded when the nested frame returns
    assert outer._sa_find(p1) == outer._sa_find(p2)
    assert set(outer._nodes_of_token(outer._token(p1))) == {p1, p2}


# ---- 3: `_group_satisfiable` memoization never serves a stale verdict -----------------------

def test_group_satisfiable_cache_does_not_serve_a_stale_unsatisfiable_verdict():
    g = h.Graph()
    x = g.add_node("x")
    anyp = g.add_node("p1")
    solver = GoalSolver(g, [])
    group = [h.Pat("?x", "blocked_by", "?anyp")]
    env = {"?x": x}
    assert solver._group_satisfiable(group, env) is False    # nothing blocks it yet
    assert solver._group_sat_cache                            # the miss got memoized
    solver._materialize("blocked_by", x, anyp)                # the solver ITSELF derives a blocker
    assert solver._group_satisfiable(group, env) is True      # must not be served the cached False


# ---- 4: a cross-goal negation cycle is caught regardless of start goal ----------------------

_CYC_P1 = h.Rule(key="cyc.p1", lhs=[h.Pat("?x", "is_a", "item")],
                  nac=[h.Pat("?x", "p2", "<yes>")], rhs=[h.Pat("?x", "p1", "<yes>")])
_CYC_P2 = h.Rule(key="cyc.p2", lhs=[h.Pat("?x", "is_a", "item")],
                  nac=[h.Pat("?x", "p1", "<yes>")], rhs=[h.Pat("?x", "p2", "<yes>")])


def _cycle_graph():
    g = h.Graph()
    g.add_relation(g.add_node("x"), "is_a", g.add_node("item"))
    return g


def test_cross_goal_negation_cycle_raises_regardless_of_start_goal():
    with pytest.raises(NonStratifiable):
        GoalSolver(_cycle_graph(), [_CYC_P1, _CYC_P2]).solve(Goal("p1", "x", "<yes>"))
    with pytest.raises(NonStratifiable):
        GoalSolver(_cycle_graph(), [_CYC_P1, _CYC_P2]).solve(Goal("p2", "x", "<yes>"))


# ---- 5: goal-visitation-order independence within ONE solver instance -----------------------

_ICE_CREAM = """
    urgent is gradable
    vanilla is in_stock
    chocolate is in_stock
    alice is a customer
    alice wants vanilla
    alice is very urgent
    bob is a customer
    bob wants chocolate
    carol is a customer
    carol wants strawberry
    ?c is urgent when ?c is a customer and ?c is very urgent
    ?c served express when ?c is urgent and ?c wants ?f and ?f is in_stock
    ?c served regular when ?c wants ?f and ?f is in_stock and ?c is not urgent
    ?c offered alternative when ?c is a customer and ?c wants ?f and ?f is not in_stock
"""
_GOALS = [Goal("served", "alice", "express"), Goal("served", "bob", "regular"),
          Goal("served", "bob", "express"), Goal("served", "alice", "regular"),
          Goal("offered", "carol", "alternative")]


def _answers_in_order(order):
    kb, rules = h.load_corpus(_ICE_CREAM)
    solver = GoalSolver(kb, rules)
    return {g: bool(solver.solve(g)) for g in order}


def test_single_solver_goal_visitation_order_independent():
    forward = _answers_in_order(_GOALS)
    backward = _answers_in_order(list(reversed(_GOALS)))
    assert forward == backward
    assert forward[Goal("served", "alice", "express")] is True
    assert forward[Goal("served", "bob", "express")] is False     # NAC-completed defeat, either order
    assert forward[Goal("served", "alice", "regular")] is False   # NAC-completed defeat, either order
    assert forward[Goal("offered", "carol", "alternative")] is True


# ---- 6: the coref-follow strategy is a DECLARED tag, not sniffed rule shape (Phase 5.4) ------

def test_coref_following_is_driven_by_the_declared_flag_not_the_rule_key():
    # The `coref_prop` role (set by `same_as_rules`) — NOT the rule's key/shape — is what turns
    # coref-following ON and drops the propagation rules as subsumed by the union-find. This
    # replaces the deleted `_is_same_as_prop` key-prefix sniffing (`feedback-no-hardcoded-engine-policy`).
    from ugm import Pat, Rule
    from ugm import to_attrgraph

    ag, _ = to_attrgraph(h.Graph())

    tagged = h.same_as_rules(["is_a"])
    assert all(r.coref_prop for r in tagged)                       # the declared role is on every rule
    s = GoalSolver(ag, list(tagged))
    assert s._follow_coref is True                                 # declaration read -> following ON
    assert s.rules == []                                           # all dropped as subsumed

    # A rule with the SAME key/shape but the flag OFF is an ordinary rule: not a propagation rule.
    untagged = [Rule(key="same_as.subj.is_a", coref_prop=False,
                     lhs=[Pat("?a", "same_as", "?b"), Pat("?a", "is_a", "?o")],
                     rhs=[Pat("?b", "is_a", "?o")])]
    s2 = GoalSolver(ag, untagged)
    assert s2._follow_coref is False                               # the FLAG decides, not the key
    assert len(s2.rules) == 1                                      # kept — not filtered as coref-prop
