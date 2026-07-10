"""
The ISA machine as the PRODUCTION forward reasoning engine (the re-host, Phase B beachhead:
decision-attrgraph-rehost). `isa.solve_all` forward-materializes a whole rule bank by demanding
every head predicate through one `GoalSolver` — reusing its positive core + NAC-as-COMPLETION +
graded gate + tools. It reproduces the shipped forward engine (`rewriter.run` / stratified
`run_rules`) at the ANSWER level WITHOUT `nac_blocks`/`_nac_groups`/`graded_degree`, and WITHOUT
ever deleting a fact edge (negation is a materialized positive, not a retraction) — so §5 holds
by construction.

These are the differential tests proving that beachhead, and pinning the one finding it surfaced:
a `closed world` declaration currently PRE-COMPILES negation into `decide`'s aggressive-completion
+ retraction form, which is the machinery being retired; routed to `GoalSolver` as a plain NAC, the
same reasoning is subsumed by demand-completion (no deletion). Retiring `decide` (Phase C) = keeping
the NAC on the GoalSolver path instead of compiling the aggressive form.
"""
import ugm as h
from ugm import derived_triples, solve_all


# Contract scenario 1 (graded + defeasible routing) — a real NAC + graded bank.
ICE_CREAM = """
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
ICE_QUESTIONS = [
    "is alice served express", "is bob served regular", "is carol offered alternative",
    "is bob served express", "is alice served regular", "who served express",
]

# The thief elimination as a plain NAC (no `closed world` pre-compilation) — the form GoalSolver's
# demand-completion subsumes soundly (cf. decide.solve's aggressive-complete-then-RETRACT form).
THIEF_NAC = """
    ada is a suspect
    bo is a suspect
    cy is a suspect
    bo in library
    ada is alibied
    ?x is innocent when ?x in library
    ?x is cleared when ?x is innocent
    ?x is cleared when ?x is alibied
    ?x is thief when ?x is a suspect and ?x is not cleared
"""


def test_solve_all_matches_run_rules_on_a_real_nac_and_graded_bank():
    # The ISA machine (GoalSolver forward-driven) reproduces the shipped stratified forward engine
    # EXACTLY at the answer level — including NAC-gated defeasible defeat and graded urgency.
    kb_a, rules_a = h.load_corpus(ICE_CREAM)
    h.run_rules(kb_a, rules_a)
    ans_run_rules = [h.ask(kb_a, q) for q in ICE_QUESTIONS]

    kb_b, rules_b = h.load_corpus(ICE_CREAM)
    solve_all(kb_b, rules_b)
    ans_solve_all = [h.ask(kb_b, q) for q in ICE_QUESTIONS]

    assert ans_solve_all == ans_run_rules
    assert ans_solve_all[0] == ["yes"]                       # alice -> express (graded urgency)
    assert ans_solve_all[3] == ["no"]                        # bob NOT express (NAC defeat is real)
    assert ans_solve_all[4] == ["no"]                        # alice NOT regular (NAC defeat is real)


def test_solve_all_subsumes_closed_world_elimination_via_completion():
    # Contract scenario 2's reasoning, given as a NAC: only cy cannot be cleared, so the completed
    # closed-world negative makes cy uniquely the thief — via demand-completion, NOT retraction.
    kb, rules = h.load_corpus(THIEF_NAC)
    solve_all(kb, rules)
    assert h.ask(kb, "who is thief") == ["cy is thief"]
    assert h.ask(kb, "is cy thief") == ["yes"]
    assert h.ask(kb, "is ada thief") == ["no"]               # ada alibied -> cleared -> not thief
    assert h.ask(kb, "is bo thief") == ["no"]                # bo in library -> cleared -> not thief


def test_solve_all_never_deletes_a_fact_edge():
    # §5 by construction: the forward driver only ever MINTs. Every base/derived triple present
    # before a re-solve is still present after — the closure only grows, never shrinks.
    kb, rules = h.load_corpus(THIEF_NAC)
    solver = solve_all(kb, rules)
    before = derived_triples(kb)
    solve_all(kb, rules)                                     # idempotent re-run
    after = derived_triples(kb)
    assert before <= after                                   # monotone: nothing was retracted
    assert solver.derived > 0


# `decide.py`'s aggressive-completion + RETRACTION scenario (the unit `test_decide.py`), reproduced on
# the backward engine as a plain NAC — the evidence that retiring `decide` (item #4) keeps the answers
# while dropping the ONE remaining production fact-edge CUT (the `retraction.py` interpose, reached only
# via `decide.solve`'s phase-2 defeat cascade). `decision-attrgraph-rehost`, `decision-forcing-a-decision`.
#   producer:  ?c is urgent      :- ?c wants rush
#   consumer:  ?c served regular  :- ?c is a customer, NOT ?c is urgent   (NAC, completed on demand)
_DECIDE_PRODUCER = h.Rule(key="urgent.rush",
                          lhs=[h.Pat("?c", "wants", "rush")], rhs=[h.Pat("?c", "is", "urgent")])
_DECIDE_CONSUMER = h.Rule(key="serve.regular",
                          lhs=[h.Pat("?c", "is_a", "customer")], nac=[h.Pat("?c", "is", "urgent")],
                          rhs=[h.Pat("?c", "served", "regular")])


def _decide_bank():
    """alice is an urgent customer (wants rush); bob is a customer who is not (test_decide._setup)."""
    g = h.Graph()
    for who in ("alice", "bob"):
        g.add_relation(g.add_node(who), "is_a", g.add_node("customer"))
    g.add_relation(g.nodes_named("alice")[0], "wants", g.add_node("rush"))
    return g


def test_backward_engine_subsumes_decide_defeat_without_retraction():
    # The DEFEAT case (`test_decide.test_derivable_positive_defeats_the_completion_and_cascades`) is
    # where `decide.solve` seeds a `<retract>` and cuts fact edges. The backward engine reaches the
    # SAME answers with NO retraction: completion is computed against the COMPLETE `is urgent` extension
    # on demand, so a derivable positive yields NOTHING to over-assert (nothing to later cut).
    g = _decide_bank()
    solver = solve_all(g, [_DECIDE_PRODUCER, _DECIDE_CONSUMER])

    def served(name):
        return sorted({g.name(o) for s in g.nodes_named(name)
                       for r, o in g.relations_from(s) if g.name(r) == "served"})

    # bob: `is urgent` NOT derivable -> demand-completion yields `is_not urgent` -> consumer fires
    # (decide's "completion materializes the negative, consumer matches positively" — no over-assertion).
    assert served("bob") == ["regular"]
    # alice: `is urgent` derivable -> the NAC blocks the consumer. decide aggressively completed THEN
    # retracted-on-defeat (a fact-edge CUT + cascade); here `served regular` is simply never asserted.
    assert served("alice") == []
    # §5: the closure only GREW across an idempotent re-solve — the retraction interpose is never reached.
    before = derived_triples(g)
    solve_all(g, [_DECIDE_PRODUCER, _DECIDE_CONSUMER])
    assert before <= derived_triples(g)
    assert solver.derived > 0


# RETIRED (Phase 2.2, 2026-07-08): two tests that pinned RECOGNITION through the GoalSolver
# (`solve_all` over `_ALL_FORMS`) — `test_solve_all_recognizes_rule_source_identically_to_rewriter`
# and `test_recognition_nac_completions_are_control_and_invisible`.
#
# They are obsolete by design, not regressed:
#   1. Production recognition runs on the forward `run_bank`, NOT `solve_all` (ratified,
#      decision-attrgraph-rehost; the batch loaders use `_recognize`). `solve_all`-over-forms was an
#      exploration that "over-recognized globally" (authoring.py) and has NO production callers.
#   2. Phase 2.2 control-types the surface scaffolding (`tokenize` marks the `next`/`first` chain
#      control; `run_bank(control_preds=SCAFFOLD_PREDS)` marks form-minted bridges/tags control) so
#      `DROP_CTRL` can legally strip determiners / decompose NPs on the ISA engine. GoalSolver is the
#      REASONING engine: its `_facts_matching` skips control (§5 control-invisibility, goal.py:674+),
#      so it can no longer see the (now correctly control) surface chain to recognize over it. That is
#      the intended split — recognition sees scaffolding (run_bank), reasoning does not (GoalSolver).
#   3. Zero production impact: by the time GoalSolver answers, `_strip_surface` has already removed the
#      surface chain, so GoalSolver never sees it regardless. Test 1 also differentialed against the
#      `rewriter` being deleted in Phase 0.5.
# run_bank's recognition parity is covered by `test_isa_runbank`; the control-typing by
# `finding-surface-rewriting-blocks-rewriter-deletion` and `test_new_core`/`test_verb_catalog` (the
# real Session decomposition/recognition, now on run_bank).
