"""
Firmware v3 — DEMAND-DRIVEN NEGATION (`docs/demand_driven_negation_design.md`), steps 1 & 2.

`chain_sip` decides a rule's NAC clause `not L` by NEGATION-AS-FAILURE: demand the positive `L`
(bound by the body so far), run it to CLOSURE (a nested negative demand), and take ABSENCE as the
answer. Nothing is materialized for the negative — the verdict is read from the empty demand-closure.
This is the agent-not-theorem-prover model: ask the positive on demand, absence decides.

  - Step 1: single-stratum NAC (the THIEF elimination) + existential (wildcard-endpoint) NAC.
  - Step 2: nested negation (a NAC over a NAC-derived predicate) and the STRATIFICATION guard —
    a genuine negative cycle is rejected at LOAD by the object-aware `lint_stratifiable`, and the chain
    prunes-and-continues on a spurious re-entry (never a silent wrong answer, never a hang).

The intended answers are asserted directly: plain `run_bank` is NOT a valid closed-world-NAC oracle
(see the note below), and the differential-vs-`decide.solve` gate runs on the real banks (step 4).
"""
import pytest

import ugm as h
from ugm import (
    AttrGraph, Pat, Rule, derived_triples, match_pats,
    chain_sip,
    check, POSITIVE, ASSUMED_NO, UNKNOWN,
)
from ugm.cnl.authoring import lint_stratifiable


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


# NOTE ON THE ORACLE: plain `run_bank` is NOT a valid oracle for closed-world NAC. Its FORWARD
# stratifier collapses when the copula `is` is overloaded (cleared/thief/innocent all share `is`), so
# it fires the thief NAC before `cleared` is derived and wrongly makes every suspect a thief. That is
# precisely why the forward `decide.solve` (aggressive completion + defeat) exists — and precisely why
# demand-driven NAF (goal-directed, per-tuple closure of the negated positive) is the RIGHT model. The
# differential-vs-`decide.solve` gate (design step 4) runs on the real riddle banks; here we assert the
# intended answers directly.


# --- Step 1: the THIEF elimination — a single-stratum closed-world NAC ----------------------------

THIEF_FACTS = [("ada", "is_a", "suspect"), ("bo", "is_a", "suspect"), ("cy", "is_a", "suspect"),
               ("bo", "in", "library"), ("ada", "is", "alibied")]
THIEF_RULES = [
    Rule(key="innocent", lhs=[Pat("?x", "in", "library")], rhs=[Pat("?x", "is", "innocent")]),
    Rule(key="cleared.innocent", lhs=[Pat("?x", "is", "innocent")], rhs=[Pat("?x", "is", "cleared")]),
    Rule(key="cleared.alibi", lhs=[Pat("?x", "is", "alibied")], rhs=[Pat("?x", "is", "cleared")]),
    Rule(key="thief", lhs=[Pat("?x", "is_a", "suspect")],
         nac=[Pat("?x", "is", "cleared")], rhs=[Pat("?x", "is", "thief")]),
]


def test_thief_elimination_by_naf_single_stratum():
    # cy is cleared by nothing -> `not cleared` holds on demand -> cy is the thief; ada/bo are cleared.
    g = _facts(THIEF_FACTS)
    rg = _reify(THIEF_RULES)
    chain_sip(g, rg, ("is", None, "thief"))
    thieves = {b["?x"] and g.name(b["?x"]) for b in match_pats(g, [Pat("?x", "is", "thief")])}
    assert thieves == {"cy"}


def test_thief_naf_derives_exactly_the_uncleared_suspect():
    g = _facts(THIEF_FACTS)
    chain_sip(g, _reify(THIEF_RULES), ("is", None, "thief"))
    got = {t for t in derived_triples(g) if t[1] == "is" and t[2] == "thief"}
    assert got == {("cy", "is", "thief")}
    # and the cleared suspects were genuinely cleared (the multi-step deduction ran under demand)
    assert {g.name(b["?x"]) for b in match_pats(g, [Pat("?x", "is", "cleared")])} == {"ada", "bo"}


def test_thief_naf_materializes_no_is_not_fact():
    # the whole point: absence DECIDES; no `is_not cleared` is ever written (unlike forward completion).
    g = _facts(THIEF_FACTS)
    chain_sip(g, _reify(THIEF_RULES), ("is", None, "thief"))
    assert not match_pats(g, [Pat("?x", "is_not", "cleared")])
    assert not any(t[1] == "is_not" for t in derived_triples(g))


# --- Step 1: existential (wildcard-endpoint) NAC — `not L(x, ·)` ----------------------------------

def test_existential_nac_holds_when_no_object_matches():
    # `?x is lonely when ?x is a person and NOT ?x likes ?anyone` — an unbound NAC object is ∃.
    facts = [("ada", "is_a", "person"), ("bo", "is_a", "person"), ("ada", "likes", "cat")]
    rules = [Rule(key="lonely", lhs=[Pat("?x", "is_a", "person")],
                  nac=[Pat("?x", "likes", "?anyone")], rhs=[Pat("?x", "is", "lonely")])]
    g = _facts(facts)
    chain_sip(g, _reify(rules), ("is", None, "lonely"))
    lonely = {g.name(b["?x"]) for b in match_pats(g, [Pat("?x", "is", "lonely")])}
    assert lonely == {"bo"}                                 # ada likes something -> not lonely


# --- Step 1: an idempotency NAC on a recursive (transitive) rule still terminates -----------------

def test_transitive_with_idempotency_nac_via_naf():
    # `?a rel ?c when ?a rel ?b and ?b rel ?c and NOT ?a rel ?c` — the NAC is check-before-derive.
    rule = Rule(key="rel.trans",
                lhs=[Pat("?a", "rel", "?b"), Pat("?b", "rel", "?c")],
                nac=[Pat("?a", "rel", "?c")], rhs=[Pat("?a", "rel", "?c")])
    facts = [("a", "rel", "b"), ("b", "rel", "c"), ("c", "rel", "d")]
    g = _facts(facts)
    chain_sip(g, _reify([rule]), ("rel", "a", None))
    got = {(g.name(b["?a"]), "rel", g.name(b["?c"]))
           for b in match_pats(g, [Pat("?a", "rel", "?c")]) if g.name(b["?a"]) == "a"}
    # a reaches b, c, d transitively (the NAC never blocks a genuinely-new edge)
    assert ("a", "rel", "c") in got and ("a", "rel", "d") in got


# --- Step 2: nested negation (a NAC over a NAC-derived predicate) ---------------------------------

def test_nested_negation_two_strata():
    # q is derived through a NAC (not r); s is guarded by a NAC on q (a NAC over a NAC-derived pred).
    facts = [("a", "is", "base"), ("a", "is", "t"), ("a", "is", "r")]   # a: r present -> q blocked
    rules = [
        Rule(key="q", lhs=[Pat("?x", "is", "base")], nac=[Pat("?x", "is", "r")],
             rhs=[Pat("?x", "is", "q")]),
        Rule(key="s", lhs=[Pat("?x", "is", "t")], nac=[Pat("?x", "is", "q")],
             rhs=[Pat("?x", "is", "s")]),
    ]
    g = _facts(facts)
    chain_sip(g, _reify(rules), ("is", None, "s"))
    # r(a) holds -> q(a) BLOCKED -> not q(a) holds -> s(a) DERIVED
    assert match_pats(g, [Pat("a", "is", "s")])
    assert not match_pats(g, [Pat("a", "is", "q")])


def test_nested_negation_flips_when_lower_negative_flips():
    # same bank, but NO r(a): now q(a) is derivable -> not q(a) FAILS -> s(a) is NOT derived.
    facts = [("a", "is", "base"), ("a", "is", "t")]
    rules = [
        Rule(key="q", lhs=[Pat("?x", "is", "base")], nac=[Pat("?x", "is", "r")],
             rhs=[Pat("?x", "is", "q")]),
        Rule(key="s", lhs=[Pat("?x", "is", "t")], nac=[Pat("?x", "is", "q")],
             rhs=[Pat("?x", "is", "s")]),
    ]
    g = _facts(facts)
    chain_sip(g, _reify(rules), ("is", None, "s"))
    assert match_pats(g, [Pat("a", "is", "q")])
    assert not match_pats(g, [Pat("a", "is", "s")])


# --- Step 2: stratification is enforced at BANK LOAD (object-aware lint), the chain prunes ---------

def test_nac_identical_to_head_is_an_idempotency_memo_not_a_cycle():
    # `?x is p when ?x is base and not ?x is p` — the NAC is IDENTICAL to the head, so it is a
    # check-before-derive memo (native to the monotone chain), NOT epistemic self-negation. It derives
    # p(a) once and stops — consistent with `run_bank` — rather than raising a spurious cycle.
    rules = [Rule(key="p", lhs=[Pat("?x", "is", "base")], nac=[Pat("?x", "is", "p")],
                  rhs=[Pat("?x", "is", "p")])]
    g = _facts([("a", "is", "base")])
    chain_sip(g, _reify(rules), ("is", "a", "p"))
    assert match_pats(g, [Pat("a", "is", "p")])


EVEN_CYCLE = [
    Rule(key="p", lhs=[Pat("?x", "is", "base")], nac=[Pat("?x", "is", "q")], rhs=[Pat("?x", "is", "p")]),
    Rule(key="q", lhs=[Pat("?x", "is", "base")], nac=[Pat("?x", "is", "p")], rhs=[Pat("?x", "is", "q")]),
]


def test_genuine_negative_cycle_is_rejected_at_load_by_the_object_aware_lint():
    # p :- not q ; q :- not p — a 2-cycle through negation (no stratified model). The OBJECT-AWARE
    # static lint (the arbiter, run at bank load) REJECTS it — never a silent wrong answer.
    with pytest.raises(ValueError):
        lint_stratifiable(EVEN_CYCLE, source="even-cycle")


def test_chain_prunes_re_entry_and_terminates_rather_than_hanging():
    # If a non-stratifiable bank ever reached the chain unlinted, the ground-goal re-entry is PRUNED
    # (block + no recurse), so the closure TERMINATES (does not hang) — the load-time lint is what
    # guarantees the answer is also sound; the chain only guarantees termination here.
    g = _facts([("a", "is", "base")])
    chain_sip(g, _reify(EVEN_CYCLE), ("is", "a", "p"))       # must return, not recurse forever


# --- Step 3: fuel -> UNKNOWN (the agent-not-theorem-prover payoff) --------------------------------

TRANS = Rule(key="reach.trans",
             lhs=[Pat("?a", "reach", "?b"), Pat("?b", "reach", "?c")], rhs=[Pat("?a", "reach", "?c")])
CHAIN_FACTS = [("a", "reach", "b"), ("b", "reach", "c"), ("c", "reach", "d"), ("d", "reach", "e")]


def test_positive_goal_truncated_is_unknown_not_no():
    # (reach a e) needs several closure rounds; with a tiny budget the closure is NOT exhausted, so the
    # honest verdict is UNKNOWN ("I didn't finish looking"), never a decided no.
    g = _facts(CHAIN_FACTS)
    assert check(g, _reify([TRANS]), ("reach", "a", "e"), max_rounds=1) == UNKNOWN


def test_same_goal_is_positive_with_enough_fuel():
    g = _facts(CHAIN_FACTS)
    assert check(g, _reify([TRANS]), ("reach", "a", "e")) == POSITIVE     # default budget closes it


def test_nac_whose_nested_closure_truncates_is_unknown():
    # `?x is thief when ?x is a suspect and not ?x is cleared`, but throttle the fuel so the multi-step
    # cleared deduction (in library -> innocent -> cleared, 2 rounds) can't finish for bo: the NAC's
    # nested negative demand is un-exhausted, so bo's thief-status is UNKNOWN, not a decided ASSUMED_NO.
    g = _facts(THIEF_FACTS)
    rg = _reify(THIEF_RULES)
    assert check(g, rg, ("is", "bo", "thief"), max_rounds=1) == UNKNOWN


# --- Brick #3 (docs/isa_control_machine.md §9.3): the NAC subgoal descent runs on an EXPLICIT control
# stack, not Python recursion. A deeply-stratified NAF chain (p0 :- not p1, p1 :- not p2, …, pN base)
# closes by descending N negative subgoals. The old code recursed `chain_sip -> _solve_demand_rule ->
# _nac_blocks -> chain_sip` per stratum (~4 Python frames/level), so a deep chain blew Python's
# recursion limit; the ported driver carries the descent on its own stack (O(1) Python depth), so it
# completes even with the interpreter's recursion limit turned WAY down — the definitive de-recursion test.

def test_deep_nac_stratification_uses_the_control_stack_not_python_recursion():
    import sys
    N = 601                                              # far deeper than the recursion limit below
    # pI(a) :- q(a) and not p{I+1}(a);  pN has no rule (base). derived(pN)=F and
    # derived(pI) = not derived(p{I+1}), so derived(p0) is True iff N is odd. N=601 -> p0(a) derived.
    rules = [Rule(key=f"p{i}",
                  lhs=[Pat("?x", "q", "yes")],
                  nac=[Pat("?x", f"p{i+1}", "yes")],
                  rhs=[Pat("?x", f"p{i}", "yes")])
             for i in range(N)]
    g = _facts([("a", "q", "yes")])
    rg = _reify(rules)

    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(200)                           # the OLD recursive descent (~2400 frames) would
    try:                                                 # RecursionError here; the explicit stack does not
        chain_sip(g, rg, ("p0", "a", None))
    finally:
        sys.setrecursionlimit(old_limit)

    # and the answer is correct: the 601-deep negative closure resolves p0(a) as derived (N odd)
    derived = {g.name(b["?x"]) for b in match_pats(g, [Pat("?x", "p0", "yes")])}
    assert "a" in derived


def test_nac_consumer_is_decided_no_with_enough_fuel():
    # with the full budget the cleared deduction finishes -> bo IS cleared -> the NAC fails -> bo is not
    # the thief, and the verdict is a DECIDED ASSUMED_NO (closed-world), not UNKNOWN.
    g = _facts(THIEF_FACTS)
    rg = _reify(THIEF_RULES)
    assert check(g, rg, ("is", "bo", "thief")) == ASSUMED_NO
