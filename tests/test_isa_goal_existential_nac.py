"""Existential NACs (¬∃) on the goal path — the ISA arc, Phase 2 (the planner's ground shape).

Phase 1 lowered GROUND NACs (`not ?act overridden <yes>`) to `R_not` completion. The planner's
block/unblock idiom needs the EXISTENTIAL shapes: a variable-OBJECT NAC (`not ?o blocked_by ?anyp`,
¬∃p) and a grouped free-SUBJECT NAC (`not ?x add ?c and not ?x preferred`, ¬∃x). These cannot lower
to a single ground negative — there is no one fact to materialize; the negative is "no witness
exists". `GoalSolver` groups them by shared free var (the forward engine's `not (A and B)` vs
`not A and not B` partition) and applies each group as a demand-driven EMPTINESS check, the group
solved to COMPLETION in a nested solve (the soundness discipline of `_complete_negative`).

THE KEYSTONE (why this is the whole point of Phase 2): the block/unblock idiom
    ?o blocked_by ?p when ?o candidate ?g and ?o pre ?p and not ?p reachable <yes>
    drop ?o blocked_by ?p when ?o blocked_by ?p and ?p reachable <yes>          # <- DROP_CTRL
    ?o viable <yes> when ?o candidate ?g and not ?o blocked_by ?anyp            # <- ¬∃p
computes `blocked_by` against COMPLETE reachability on the demand path, so it never asserts a stale
block — the `drop` (control-layer retraction / `DROP_CTRL`) is SUBSUMED, not needed. We prove this
by DIFFERENTIAL TEST against the forward engine's actual planner driver: the repeat-`run_rules`-
until-stable loop (`planning.plan`), where `drop` IS load-bearing (a block asserted in one sweep is
dropped in the next as its precondition becomes reachable). The goal-directed solver, with the
`drop` rule INERT (empty rhs, never indexed), reproduces the loop's final `viable`/`reachable`.
"""
import warnings
import pathlib

import pytest

import ugm as h
from ugm.cnl.authoring import run_rules
from ugm.cnl.machine_rules import load_machine_rules
from ugm import to_attrgraph, derived_triples, Goal, GoalSolver, NonStratifiable

_CORPUS = pathlib.Path(__file__).resolve().parent.parent / "corpus"


# ---------------------------------------------------------------------------
# Helpers: build a graph, and the forward planner-loop oracle
# ---------------------------------------------------------------------------

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


def _fingerprint(g: h.Graph) -> frozenset:
    return frozenset((g.name(s), g.name(r), g.name(o))
                     for s in g.nodes() for r, o in g.relations_from(s))


def _forward_loop_marks(triples, rules, pred, *, max_sweeps: int = 30) -> set[tuple[str, str]]:
    """The forward engine's derived `pred`, run under the ACTUAL planner driver — repeat
    `run_rules` until the graph stabilizes (`planning.plan`'s loop), which is where `drop`-based
    control retraction converges. This, not a single stratified sweep, is the block/unblock oracle."""
    g = _graph(triples)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")               # the block/unblock idiom warns on a partial sweep
        for _ in range(max_sweeps):
            before = _fingerprint(g)
            run_rules(g, rules, provenance=False)
            if _fingerprint(g) == before:
                break
    return {(g.name(s), g.name(o))
            for s in g.nodes() for r, o in g.relations_from(s) if g.name(r) == pred}


def _goal_marks(triples, rules, pred, subjects, obj="<yes>") -> set[tuple[str, str]]:
    ag, _ = to_attrgraph(_graph(triples))
    solver = GoalSolver(ag, rules)
    out: set[tuple[str, str]] = set()
    for s in subjects:
        out |= solver.solve(Goal(pred, s, obj))
    return out


# ============================================================================================
# The block/unblock fragment — ¬∃p, and DROP_CTRL subsumed
# ============================================================================================

_BLOCK_RULES = load_machine_rules("""
?c reachable <yes> when <now> true ?c
?o blocked_by ?p when ?o candidate ?g and ?o pre ?p and not ?p reachable <yes>
drop ?o blocked_by ?p when ?o blocked_by ?p and ?p reachable <yes>
?o viable <yes> when ?o candidate ?g and not ?o blocked_by ?anyp
?c reachable <yes> when ?o viable <yes> and ?o add ?c
""")

# a 2-step chain: opa (pre water, now-true) produces coffee; opb (pre coffee) produces done.
_CHAIN_FACTS = [
    ("<now>", "true", "water"),
    ("opa", "candidate", "coffee"), ("opa", "pre", "water"), ("opa", "add", "coffee"),
    ("opb", "candidate", "done"), ("opb", "pre", "coffee"), ("opb", "add", "done"),
]


def test_variable_object_nac_now_lowers_to_an_emptiness_check():
    # `not ?o blocked_by ?anyp` (?anyp NAC-local free) is grouped as a ¬∃p existential — it must
    # NOT raise (Phase 1 rejected it), and it lands in `_exist_nac`, not as a ground body clause.
    ag, _ = to_attrgraph(_graph(_CHAIN_FACTS))
    solver = GoalSolver(ag, _BLOCK_RULES)
    groups = [grp for grps in solver._exist_nac.values() for grp in grps]
    assert any(pat.p == "blocked_by" for grp in groups for pat in grp)


def test_viable_matches_the_forward_planner_loop():
    # the crux: demand-driven `viable` (¬∃p blocked_by) equals the repeat-until-stable forward loop,
    # in which `drop` retracts stale blocks. Both derive {opa, opb} viable.
    forward = _forward_loop_marks(_CHAIN_FACTS, _BLOCK_RULES, "viable")
    goal = _goal_marks(_CHAIN_FACTS, _BLOCK_RULES, "viable", ["opa", "opb"])
    assert goal == forward == {("opa", "<yes>"), ("opb", "<yes>")}


def test_reachable_matches_the_forward_planner_loop():
    # reachability propagates through the mutual recursion (viable -> reachable -> viable): the
    # goal path pulls the full chain {water, coffee, done} exactly as the loop derives it.
    forward = _forward_loop_marks(_CHAIN_FACTS, _BLOCK_RULES, "reachable")
    goal = _goal_marks(_CHAIN_FACTS, _BLOCK_RULES, "reachable", ["water", "coffee", "done"])
    assert goal == forward == {("water", "<yes>"), ("coffee", "<yes>"), ("done", "<yes>")}


def test_drop_ctrl_is_subsumed_no_stale_block_materialized():
    # the forward loop ENDS with blocked_by == {} (every block dropped once its pre became
    # reachable). The goal path never asserts a stale block in the first place — demand-driven
    # `blocked_by` is computed against COMPLETE reachability. So `blocked_by` is empty here too,
    # WITHOUT any drop firing (the drop rule has empty rhs -> inert / never indexed on the goal path).
    assert _forward_loop_marks(_CHAIN_FACTS, _BLOCK_RULES, "blocked_by") == set()
    ag, _ = to_attrgraph(_graph(_CHAIN_FACTS))
    solver = GoalSolver(ag, _BLOCK_RULES)
    solver.solve(Goal("viable", "opa", "<yes>"))
    solver.solve(Goal("viable", "opb", "<yes>"))
    blocked = {(s, o) for (s, r, o) in derived_triples(solver.ag) if r == "blocked_by"}
    assert blocked == set()
    # and no `drop` rule was indexed as a producer (empty rhs)
    assert "blocked_by" not in solver.head_index or all(
        r.rhs for r, _ in solver.head_index.get("blocked_by", []))


def test_goal_direction_is_preserved_no_saturation():
    # THE DIRECTION-PRESERVATION GATE (a second session flagged the hole: a full-set-parity oracle is
    # blind to goal-direction — GoalSolver could pass every parity test by saturating into a forward
    # fixpoint). So we ALSO assert the demand-driven property test_isa_goal.py measured, now on the
    # planner's block/unblock bank: demanding ONE goal derives a STRICT SUBSET of the forward closure.
    # `viable opa` is provable from `water` alone (pre met, now-true) WITHOUT touching opb/coffee/done.
    ag, _ = to_attrgraph(_graph(_CHAIN_FACTS))
    solver = GoalSolver(ag, _BLOCK_RULES)
    before = derived_triples(solver.ag)
    solver.solve(Goal("viable", "opa", "<yes>"))
    new = derived_triples(solver.ag) - before
    marks = {(s, r, o) for (s, r, o) in new if r in ("viable", "reachable", "blocked_by")}
    # what the goal NEEDS is materialized ...
    assert ("opa", "viable", "<yes>") in marks
    assert ("water", "reachable", "<yes>") in marks
    # ... and the irrelevant rest of the closure is NOT (the anti-saturation assertion)
    assert ("opb", "viable", "<yes>") not in marks
    assert ("coffee", "reachable", "<yes>") not in marks
    assert ("done", "reachable", "<yes>") not in marks
    # strictly fewer facts than the full forward closure would derive (which includes opb + coffee + done)
    full = (_forward_loop_marks(_CHAIN_FACTS, _BLOCK_RULES, "viable")
            | _forward_loop_marks(_CHAIN_FACTS, _BLOCK_RULES, "reachable"))
    got = {(s, o) for (s, r, o) in marks if r in ("viable", "reachable")}
    assert got < full                                        # PROPER subset — no saturation


def test_an_unreachable_precondition_leaves_the_op_nonviable():
    # opb's precondition `coffee` is now unmet AND unproducible (remove opa) -> opb stays blocked ->
    # NOT viable, in both the forward loop and the goal path.
    facts = [
        ("<now>", "true", "water"),
        ("opb", "candidate", "done"), ("opb", "pre", "coffee"), ("opb", "add", "done"),
    ]
    forward = _forward_loop_marks(facts, _BLOCK_RULES, "viable")
    goal = _goal_marks(facts, _BLOCK_RULES, "viable", ["opb"])
    assert goal == forward == set()


# ============================================================================================
# Grouped ¬∃x — a shared free subject across two NAC clauses (`not (A and B)`)
# ============================================================================================

_GROUP_RULES = load_machine_rules("""
?o sole ?c when ?o add ?c and not ?x add ?c and not ?x preferred <yes>
""")

# opa/opb both add gg, opb preferred -> for BOTH, exists x=opb (adds gg AND preferred) -> blocked.
# opc alone adds hh -> no rival -> sole hh.
_GROUP_FACTS = [
    ("opa", "add", "gg"), ("opb", "add", "gg"), ("opb", "preferred", "<yes>"),
    ("opc", "add", "hh"),
]


def test_grouped_existential_nac_is_one_conjunctive_group():
    ag, _ = to_attrgraph(_graph(_GROUP_FACTS))
    solver = GoalSolver(ag, _GROUP_RULES)
    groups = [grp for grps in solver._exist_nac.values() for grp in grps]
    # the two clauses share free ?x -> ONE group of two patterns (not two independent negations)
    assert len(groups) == 1 and len(groups[0]) == 2


def test_grouped_existential_nac_matches_the_forward_engine():
    # the conjunctive ¬∃x ("no rival that BOTH adds ?c AND is preferred") equals the forward run.
    forward = _forward_loop_marks(_GROUP_FACTS, _GROUP_RULES, "sole")
    ag, _ = to_attrgraph(_graph(_GROUP_FACTS))
    solver = GoalSolver(ag, _GROUP_RULES)
    goal: set[tuple[str, str]] = set()
    for s in ("opa", "opb", "opc"):
        for o in ("gg", "hh"):
            goal |= solver.solve(Goal("sole", s, o))
    assert goal == forward == {("opc", "hh")}


def test_independent_negations_block_separately():
    # `not ?x foo ?c and not ?y bar ?c` — two DISTINCT free vars, so TWO independent groups; the
    # rule is blocked if EITHER holds (¬A ∧ ¬B). Here a `foo`-witness alone blocks even with no `bar`.
    rules = load_machine_rules(
        "?o clear ?c when ?o add ?c and not ?x foo ?c and not ?y bar ?c")
    ag, _ = to_attrgraph(_graph(_GROUP_FACTS))
    solver = GoalSolver(ag, rules)
    groups = [grp for grps in solver._exist_nac.values() for grp in grps]
    assert len(groups) == 2                                  # ?x and ?y are independent
    facts = [("op1", "add", "aa"), ("someone", "foo", "aa")]  # a foo-witness blocks op1/aa
    assert _goal_marks(facts, rules, "clear", ["op1"], obj="aa") == set()
    assert _forward_loop_marks(facts, rules, "clear") == set()


# ============================================================================================
# The selection boundary — the real `chosen` rule is rejected (not silently mis-answered)
# ============================================================================================

def test_planner_chosen_rule_is_rejected_as_a_selection():
    # `?o chosen <yes> when … not ?x chosen <yes> and not ?x add ?c` — the grouped NAC references
    # the rule's OWN head (`chosen`), a non-stratified selection the forward engine resolves by
    # commit-order. Goal-directed completion cannot express choice; reject, never silently answer.
    chosen = load_machine_rules(
        "?o chosen <yes> when ?o best <yes> and ?o add ?c "
        "and not ?x chosen <yes> and not ?x add ?c")
    ag, _ = to_attrgraph(h.Graph())
    with pytest.raises(NonStratifiable):
        GoalSolver(ag, chosen)


def test_full_planner_bank_isolates_exactly_the_selection_rule():
    # loading the WHOLE planner bank raises on the `chosen` selection rule — the one Phase-3
    # residual. Every other rule (positive, ground-NAC, ¬∃p) lowers; only choice is out of slice.
    planner = load_machine_rules((_CORPUS / "planning.cnl").read_text(encoding="utf-8"))
    ag, _ = to_attrgraph(h.Graph())
    with pytest.raises(NonStratifiable) as exc:
        GoalSolver(ag, planner)
    assert "chosen" in str(exc.value) and "selection" in str(exc.value).lower()
