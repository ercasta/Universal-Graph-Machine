"""
NAC -> materialized-positive completion on the goal path — the last reasoning piece.

Negation here is NOT a CHECK-ABSENT filter. A rule's copula NAC `H :- BODY, not ?c is P` is
rewritten (`_lower_nac`) into a POSITIVE body clause `?c is_not P`, and the negative is produced
by ONE demand-driven COMPLETION step (`GoalSolver._complete_negative`): to answer a demanded
`is_not(c, P)`, solve the positive `is(c, P)` to completion in a self-contained nested solve, and
materialize `c is_not P` iff the positive has no answer. The matching core stays purely positive
(memory `decision_forcing_a_decision`, `harneskills/decide.py`).

These tests reproduce contract scenario 1's routing on the goal-directed path (the handoff's
"closes the goal path over the full defeasible contract scenario"): a graded `is urgent` is
derived, a NAC-gated `served regular` default fires when it CANNOT be derived and is DEFEATED
where it can, and `served express` needs the positive. They also pin the two soundness edges:
the negative is materialized and matched positively, and a non-stratifiable NAC is rejected
(never silently mis-answered).
"""
import pytest

import ugm as h
from ugm import Pat, Rule, GradedCondition
from ugm import to_attrgraph, derived_triples, Goal, GoalSolver, NonStratifiable


# --- contract scenario 1, at the relation level -----------------------------------------------
# A graded urgency clears the α-cut for alice (0.9) but not bob (0.3). Routing must match the
# forward engine's: alice -> express (never regular), bob -> regular (never express).

URGENT = Rule(
    key="urgent",
    lhs=[Pat("?c", "is_a", "customer")],
    rhs=[Pat("?c", "is", "urgent")],
    graded=[GradedCondition("?c", {"urgency": 1.0}, 0.5)],
)
EXPRESS = Rule(
    key="express",
    lhs=[Pat("?c", "is", "urgent"), Pat("?c", "wants", "?f"), Pat("?f", "is", "in_stock")],
    rhs=[Pat("?c", "served", "express")],
)
REGULAR = Rule(
    key="regular",
    lhs=[Pat("?c", "wants", "?f"), Pat("?f", "is", "in_stock")],
    nac=[Pat("?c", "is", "urgent")],                       # ... and ?c is NOT urgent
    rhs=[Pat("?c", "served", "regular")],
)
ROUTING = [URGENT, EXPRESS, REGULAR]


def _routing_graph() -> h.Graph:
    g = h.Graph()
    ids: dict[str, str] = {}

    def node(n: str) -> str:
        ids[n] = ids[n] if n in ids else g.add_node(n)
        return ids[n]

    for s, p, o in [("alice", "is_a", "customer"), ("alice", "wants", "vanilla"),
                    ("vanilla", "is", "in_stock"),
                    ("bob", "is_a", "customer"), ("bob", "wants", "choc"),
                    ("choc", "is", "in_stock")]:
        g.add_relation(node(s), p, node(o))
    g.set_embedding(node("alice"), {"urgency": 0.9})       # clears the 0.5 cut -> urgent
    g.set_embedding(node("bob"), {"urgency": 0.3})         # below the cut -> not urgent
    return g


def _solver() -> GoalSolver:
    ag, _ = to_attrgraph(_routing_graph())
    return GoalSolver(ag, ROUTING)


# --- the default FIRES when the negated positive cannot be derived ----------------------------

def test_regular_default_fires_when_urgent_underivable():
    # bob is not urgent (below the cut) -> the NAC passes -> served regular
    assert _solver().solve(Goal("served", "bob", "regular")) == {("bob", "regular")}


# --- the default is DEFEATED where the positive IS derivable (the whole point of defeasibility) -

def test_regular_default_defeated_by_derived_urgent():
    # alice's graded `is urgent` is derivable -> the completion yields nothing -> the default
    # does NOT fire (soundness of the NAC, not just absence of an answer).
    assert _solver().solve(Goal("served", "alice", "regular")) == set()


def test_express_needs_the_positive():
    # alice is urgent -> express fires; bob is not urgent -> express refuses.
    assert _solver().solve(Goal("served", "alice", "express")) == {("alice", "express")}
    assert _solver().solve(Goal("served", "bob", "express")) == set()


# --- the negative is MATERIALIZED and matched POSITIVELY (the decide line, made observable) ----

def test_is_not_is_materialized_as_a_positive_fact():
    solver = _solver()
    before = derived_triples(solver.ag)
    solver.solve(Goal("served", "bob", "regular"))
    new = derived_triples(solver.ag) - before
    # the completion minted an explicit `bob is_not urgent` — a positive fact, not a NAF check
    assert ("bob", "is_not", "urgent") in new
    # ... and it was NOT minted for alice, whose positive defeated the completion
    assert ("alice", "is_not", "urgent") not in derived_triples(solver.ag)


# --- free-subject consumer: per-binding completion enumerates only the survivors ---------------

def test_free_object_enumerates_only_undefeated_defaults():
    # `who is served regular` — the positive residual binds ?c (alice, bob), then each gets its
    # own ground completion; only bob survives (alice is defeated by derived urgency).
    ans = _solver().solve(Goal("served", None, "regular"))
    assert ans == {("bob", "regular")}


# --- goal-directedness is preserved: a demanded route derives only what it needs --------------

def test_completion_stays_demand_scoped():
    solver = _solver()
    before = derived_triples(solver.ag)
    solver.solve(Goal("served", "bob", "regular"))
    new = derived_triples(solver.ag) - before
    # bob's route never demanded alice's `served`/`is urgent`, so none was materialized
    assert not any(s == "alice" for (s, r, o) in new)


# --- soundness edges: the SELECTION rule is rejected; a negative cycle is rejected -------------
# The GROUND-object NAC (`not ?act overridden <yes>`) lowers to completion (test_isa_goal_predicate_
# nac.py); the EXISTENTIAL NACs (¬∃o `not ?o blocked_by ?anyp`, grouped ¬∃x) now lower to a
# demand-driven emptiness check (test_isa_goal_existential_nac.py). What stays out of slice is a
# SELECTION rule — an existential NAC on the rule's OWN head — and a negative cycle.

def test_ground_object_nac_with_lhs_bound_object_is_not_existential():
    # `not ?a consume ?b` where ?b IS bound by the positive LHS (`?a wants ?b`) is a GROUND NAC
    # (both slots bound) — it lowers to `consume_not` completion, NOT the existential path. It must
    # NOT raise (the earlier over-strict `is_var(n.o)` check wrongly rejected a bound var object).
    ok = Rule(key="ground", lhs=[Pat("?a", "wants", "?b")],
              nac=[Pat("?a", "consume", "?b")],            # ?b bound by LHS -> ground, not ¬∃
              rhs=[Pat("?a", "ok", "?b")])
    ag, _ = to_attrgraph(_routing_graph())
    solver = GoalSolver(ag, [ok])
    # alice wants vanilla and does not consume it -> the completion holds -> ok
    assert solver.solve(Goal("ok", "alice", "vanilla")) == {("alice", "vanilla")}


def test_selection_rule_on_own_head_is_rejected():
    # `?o chosen <yes> when … not ?x chosen <yes>` — an existential NAC on the rule's OWN head is a
    # non-stratified SELECTION/choice (the forward engine resolves it by commit-order, not by
    # completion). Rejected explicitly, deferred to the operational planner (Phase 3).
    bad = Rule(key="select", lhs=[Pat("?o", "best", "<yes>")],
               nac=[Pat("?x", "chosen", "<yes>")],         # ?x free AND predicate == head -> selection
               rhs=[Pat("?o", "chosen", "<yes>")])
    ag, _ = to_attrgraph(_routing_graph())
    with pytest.raises(NonStratifiable):
        GoalSolver(ag, [bad])


def test_negative_cycle_through_distinct_predicates_is_detected():
    # A GENUINE non-stratifiable cycle through DIFFERENT predicates: p :- q, not r; r :- q, not p.
    # Completing is_not(x,r) demands is(x,r), which demands is_not(x,p) -> is(x,p) -> is_not(x,r):
    # a negative cycle the `_completing` up-stack guard catches (never silently mis-answered).
    g = h.Graph()
    x = g.add_node("x")
    g.add_relation(x, "is_a", g.add_node("q"))
    rp = Rule(key="rp", lhs=[Pat("?x", "is_a", "q")], nac=[Pat("?x", "is", "r")],
              rhs=[Pat("?x", "is", "p")])
    rr = Rule(key="rr", lhs=[Pat("?x", "is_a", "q")], nac=[Pat("?x", "is", "p")],
              rhs=[Pat("?x", "is", "r")])
    ag, _ = to_attrgraph(g)
    with pytest.raises(NonStratifiable):
        GoalSolver(ag, [rp, rr]).solve(Goal("is", "x", "p"))


def test_head_identical_self_nac_is_a_forward_idempotency_guard():
    # `p(?x) :- q(?x), not p(?x)` — the NAC is IDENTICAL to the head. In the forward engine this is
    # a fire-once dedup guard: p is derived and STAYS (monotone). The goal path now matches that —
    # it drops the head-identical NAC (redundant under tabling) and derives p, rather than the old
    # over-conservative reject (which diverged from `rewriter.run`, deriving nothing).
    g = h.Graph()
    x = g.add_node("x")
    g.add_relation(x, "is_a", g.add_node("q"))
    idem = Rule(key="idem", lhs=[Pat("?x", "is_a", "q")],
                nac=[Pat("?x", "is", "p")], rhs=[Pat("?x", "is", "p")])
    ag, _ = to_attrgraph(g)
    assert GoalSolver(ag, [idem]).solve(Goal("is", "x", "p")) == {("x", "p")}
