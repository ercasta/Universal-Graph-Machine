"""Regression tests for the pystrider consumer feedback (docs/feedback_from_pystrider.md).

Theme: silent failures made LOUD. A non-triple machine-rule clause (#1), a skolem RHS-only head var
(#2), a case-folded query that silently misses (#3), a `Rule` object where a node-id is expected (#4),
and an unrecognized fact line (#5) now signal instead of quietly doing less. Plus a session ergonomics
gap: `suppose` now accepts `focus_scope` like `ask_goal` (#7).
"""
import inspect
import warnings

import pytest

import ugm as h
from ugm import (load_machine_rules, write_rule, AttrGraph, apply_rule, apply_to_fixpoint,
                 rules_in_graph, load_facts, ask_goal, suppose)


# --- #1: machine-rule CNL raises on a clause that isn't a full S P O triple --------------------------

def test_machine_rule_absorbed_separator_raises():
    # `?e reached` is 2 tokens -> would swallow `when` as its object; must raise, not mangle.
    with pytest.raises(ValueError, match="triple"):
        load_machine_rules("?e reached when ?e is_a attribute")


def test_machine_rule_dropped_short_body_clause_raises():
    # the 2-token guard `?g guard_open` would silently vanish from the LHS, firing unconditionally.
    with pytest.raises(ValueError, match="guard_open"):
        load_machine_rules("?e reached yes when ?e within_guard ?g and ?g guard_open")


def test_machine_rule_valid_shapes_still_parse():
    for good in ("?e reached yes when ?e is_a attribute",
                 "?p made child when ?p is_a parent",
                 "?p succ ?p2 when ?p is_a state and ?p next ?p2",       # head var BOUND in the body: ok
                 "drop ?m mark done when ?m is_a task and ?m closed yes",
                 "?x safe yes when ?x clear yes and not ?x flagged yes"):
        assert len(load_machine_rules(good)) == 1


# --- #2: existential / skolem RHS-only head vars are rejected LOUDLY (was: silent garbage mint) ------

def test_rhs_only_head_var_rejected():
    # `?s2` is a head var absent from the body — forward mints a fresh unnamed node per firing; reject it.
    with pytest.raises(ValueError, match="RHS-only head variable"):
        load_machine_rules("?p succ ?s2 when ?p is_a state")
    # the prose surface rejects it too, and only AFTER the more specific malformed-clause check runs
    with pytest.raises(ValueError, match="RHS-only head variable"):
        h.load_rules("?x knows ?y when ?x is a person")            # ?y is RHS-only


def test_nac_only_body_binds_head_var_not_flagged():
    # a rule whose only body clause is a NAC still BINDS the head var (via the NAC) — must NOT be rejected.
    assert h.load_rules("?x is q when ?x is not p")                # ?x bound by the NAC, valid


# --- #2: the SUPPORTED minting primitive — the LHS-keyed skolem `<foo>?` — converges on the demand path.
# An RHS-only VARIABLE is unsound (rejected above); a bound-literal skolem is a value invention keyed on the
# firing's LHS args (`f(?p)`). It used to BLOW UP on the demand chain (a fresh node every round, fuel-capped
# at ~1000) because the bracket-named node is control and the reuse-by-name lookup skipped it. It is now
# re-found STRUCTURALLY by its defining relation, so check-before-derive converges.

def _skolem_rule():
    from ugm.production_rule import Rule, Pat
    # `s2?` is RHS-only, anchored to ?p by two defining relations — "the successor of ?p". A non-bracket
    # name makes it a FACT individual (matchable downstream); the identity is the anchoring relation.
    return Rule(key="mk", lhs=[Pat("?p", "is_a", "state")],
                rhs=[Pat("?p", "has_succ", "s2?"), Pat("s2?", "succ_of", "?p")])


def _demand_skolems(objs):
    from ugm import chain_sip
    rg = AttrGraph(); write_rule(rg, _skolem_rule())
    g = h.Graph()
    for nm in ("p1", "p2"):
        n = g.add_node(nm); g.add_relation(n, "is_a", g.add_node("state"))
    for pred_subj, pred_obj in objs:
        chain_sip(g, ("has_succ", pred_subj, pred_obj), rules=rg)
    return g, [x for x in g.nodes() if g.name(x) == "s2"]


def test_demand_skolem_converges_one_node_per_arg():
    # ONE fresh successor per state (not a fuel-capped flood), each linked back to its own argument.
    g, succ = _demand_skolems([("p1", None), ("p2", None)])
    assert len(succ) == 2                                          # was ~2000 (fuel-capped) before the fix
    backlinks = {g.name(o) for sn in succ for r, o in g.relations_from(sn)
                 if g.predicate(r) == "succ_of"}
    assert backlinks == {"p1", "p2"}                              # distinct skolem per LHS binding


def test_demand_skolem_is_idempotent_across_reasks():
    # re-serving the SAME demand re-finds the SAME node (the whole point: it terminates by reuse).
    _g, once = _demand_skolems([("p1", None)])
    _g2, twice = _demand_skolems([("p1", None), ("p1", None)])
    assert len(once) == len(twice) == 1


def test_demand_and_forward_skolem_agree_on_count():
    from ugm.lowering import run_bank, to_attrgraph
    fg = h.Graph()
    for nm in ("p1", "p2"):
        n = fg.add_node(nm); fg.add_relation(n, "is_a", fg.add_node("state"))
    ag, _ = to_attrgraph(fg); run_bank(ag, [_skolem_rule()], max_rounds=50)
    fwd = [x for x in ag.nodes() if ag.name(x) == "s2"]
    _g, dmd = _demand_skolems([("p1", None), ("p2", None)])
    assert len(fwd) == len(dmd) == 2                              # one skolem per firing, both paths


def test_demand_skolem_is_matchable_downstream():
    # the ACCESS path: a fact-layer skolem is re-bound by a later rule via ?x-threading and reasoned about,
    # all on the demand chain — no node ids ever leave the rule surface (the user's law).
    from ugm.production_rule import Rule, Pat
    from ugm import chain_sip
    r1 = Rule(key="mk", lhs=[Pat("?p", "is_a", "state")],
              rhs=[Pat("?p", "has_succ", "s2?"), Pat("s2?", "is_a", "state")])
    r2 = Rule(key="label", lhs=[Pat("?p", "has_succ", "?x"), Pat("?p", "is_a", "state")],
              rhs=[Pat("?x", "derived_from", "?p")])
    rg = AttrGraph(); write_rule(rg, r1); write_rule(rg, r2)
    g = h.Graph(); p = g.add_node("p1"); g.add_relation(p, "is_a", g.add_node("state"))
    chain_sip(g, ("derived_from", None, "p1"), rules=rg)                # demand the DOWNSTREAM fact
    sk = [x for x in g.nodes() if g.name(x) == "s2"]
    assert len(sk) == 1 and not g.is_control(sk[0])               # one fact-layer individual
    stamped = {(g.predicate(r), g.name(o)) for r, o in g.relations_from(sk[0])}
    assert ("derived_from", "p1") in stamped                      # re-bound via ?x and reasoned about


# --- #8: name-addressing on the retrieval path ------------------------------------------------------

def test_name_split_join_warns_at_query_time():
    # #8a: a query that NAMES a split entity warns (was: signalled only at write time).
    g = h.Graph()
    a1 = g.add_node("plan"); a2 = g.add_node("plan")          # two distinct nodes, same name
    g.add_relation(a1, "is_a", g.add_node("thing"))
    g.add_relation(a2, "flag", g.add_node("yes"))
    with pytest.warns(UserWarning, match="resolves to 2 distinct nodes"):
        ask_goal(g, "is plan a thing", [])
    # a single (non-split) node draws NO warning and the join composes.
    g2 = h.Graph()
    p = g2.add_node("plan")
    g2.add_relation(p, "is_a", g2.add_node("thing")); g2.add_relation(p, "flag", g2.add_node("yes"))
    rules = load_machine_rules("?p ok yes when ?p is_a thing and ?p flag yes")
    with warnings.catch_warnings():
        warnings.simplefilter("error")                        # no spurious warning on a clean single node
        assert ask_goal(g2, "who ok yes", rules) == ["plan ok yes"]


def test_assemble_facts_interns_repeated_name():
    # #8b (vision-aligned): building via the ISA program interns a repeated name to ONE node — the
    # get-or-create is MINT(intern=True), not a Python helper. No split, so the join that used to fail holds.
    from ugm import load_fact_triples
    g = h.Graph()
    load_fact_triples(g, [("plan", "is_a", "thing"), ("plan", "flag", "yes")])
    assert len([x for x in g.nodes() if g.name(x) == "plan"]) == 1       # 'plan' interned once via the ISA
    rules = load_machine_rules("?p ok yes when ?p is_a thing and ?p flag yes")
    assert ask_goal(g, "who ok yes", rules) == ["plan ok yes"]


def test_assemble_facts_is_a_mint_program_and_idempotent():
    from ugm import assemble_facts, load_fact_triples
    from ugm.machine import MINT
    prog = assemble_facts([("a", "r", "b")])
    assert all(isinstance(i, MINT) for i in prog)                        # capabilities are PROGRAMS, not helpers
    assert any(getattr(i, "intern", False) for i in prog)               # endpoints via MINT(intern=True)
    assert any(getattr(i, "dedup", False) for i in prog)                # relation via MINT(dedup=True)
    g = h.Graph()
    load_fact_triples(g, [("a", "r", "b")]); before = len(list(g.nodes()))
    load_fact_triples(g, [("a", "r", "b")])                              # re-load is a no-op (dedup)
    assert len(list(g.nodes())) == before


# --- #4: apply_* give a clear error for a Rule object instead of a cryptic TypeError -----------------

def test_apply_with_rule_object_gives_clear_error():
    rule = load_machine_rules("?p made child when ?p is_a parent")[0]
    rg = AttrGraph(); write_rule(rg, rule)
    got_rule_obj = rules_in_graph(rg)[0]                                # a Rule, NOT a node id
    g = h.Graph()
    for fn in (apply_rule, apply_to_fixpoint):
        with pytest.raises(TypeError, match="rule-NODE id"):
            fn(g, rg, got_rule_obj)


def test_apply_with_node_id_still_works():
    rule = load_machine_rules("?p made child when ?p is_a parent")[0]
    rg = AttrGraph(); node = write_rule(rg, rule)                       # the id you actually feed apply_*
    g = h.Graph(); p = g.add_node("p"); g.add_relation(p, "is_a", g.add_node("parent"))
    assert apply_to_fixpoint(g, rg, node) == 1


# --- #5: load_facts(strict=True) surfaces silently-dropped lines -------------------------------------

def test_load_facts_strict_raises_on_unrecognized_line():
    g = h.Graph()
    with pytest.raises(ValueError, match="assigns"):
        load_facts(g, "ada is a suspect\nstmt0 assigns y\nbo in library", strict=True)


def test_load_facts_lenient_default_unchanged():
    g = h.Graph()
    anchors = load_facts(g, "stmt0 assigns y")                          # no raise, stays raw
    assert anchors and not any(t[1] == "assigns" for t in h.derived_triples(g))


def test_load_facts_strict_passes_when_all_recognized():
    g = h.Graph()
    load_facts(g, "ada is a suspect\nbo in library", strict=True)       # no raise
    assert h.ask_goal(g, "is ada a suspect", []) == ["yes"]


# --- #3: a case-folded CNL query that would silently miss a case-variant node now WARNS ---------------

def test_case_folded_query_warns_on_variant_node():
    g = h.Graph(); e = g.add_node("eB"); g.add_relation(e, "is_a", g.add_node("attribute"))
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        assert ask_goal(g, "is eB a attribute", []) == ["no"]          # still the folded miss...
    assert any("case-variant" in str(rec.message) for rec in w)        # ...but no longer SILENT


def test_case_folded_query_quiet_when_no_variant():
    g = h.Graph(); load_facts(g, "ada is a suspect")                    # all lower-case, exact match
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        assert ask_goal(g, "is ada a suspect", []) == ["yes"]
        ask_goal(g, "is zzz a suspect", [])                            # genuinely absent, not a case issue
    assert not w                                                        # no noise on the normal paths


# --- #7: suppose accepts focus_scope (bounded attention on the outcome path), like ask_goal ----------

def test_suppose_accepts_focus_scope():
    assert "focus_scope" in inspect.signature(suppose).parameters
    kb, rules = h.load_corpus("?x is wet when ?x is rained_on")
    rg = AttrGraph()
    for r in rules:
        write_rule(rg, r)
    # in-scope entity -> the hypothesis reasons within the working set and still confirms
    res = suppose(kb, [("ada", "is", "rained_on")], [("is", "ada", "wet")], focus_scope=frozenset({"ada"}), rules=rg)
    assert res.status == "confirmed"


# --- #6: suppose(commit=False) is READ-ONLY — verdict + in-scope derivations, no ink -----------------

def _wet_world():
    kb, rules = h.load_corpus("?x is wet when ?x is rained_on")
    rg = AttrGraph()
    for r in rules:
        write_rule(rg, r)
    return kb, rules, rg


def test_suppose_commit_false_is_read_only_and_returns_derivations():
    assert "commit" in inspect.signature(suppose).parameters
    kb, rules, rg = _wet_world()
    res = suppose(kb, [("ada", "is", "rained_on")], [("is", "ada", "wet")], commit=False, rules=rg)
    assert res.status == "confirmed"
    assert res.committed == []                               # a READ-ONLY run inks NOTHING
    assert ("ada", "is", "wet") in res.derived              # the in-scope consequence, for inspection
    # the KB is unmutated: the assumption never entered ink, so the conclusion does not re-derive
    assert h.ask_goal(kb, "is ada wet", rules) == ["no"]


def test_suppose_default_still_commits_to_ink():
    kb, rules, rg = _wet_world()
    res = suppose(kb, [("ada", "is", "rained_on")], [("is", "ada", "wet")], rules=rg)   # commit=True default
    assert res.status == "confirmed" and ("ada", "is", "rained_on") in res.committed
    assert res.derived == []                                # default run: no read-only snapshot
    assert h.ask_goal(kb, "is ada wet", rules) == ["yes"]   # inked -> re-derives from ink


def test_suppose_commit_false_exposes_partial_derivations_on_inconclusive():
    # a prediction that does NOT derive makes the run inconclusive — but the partial consequence that
    # DID derive (and used to be swept unseen) is now inspectable, answering 'why inconclusive?'.
    kb, rules, rg = _wet_world()
    res = suppose(kb, [("ada", "is", "rained_on")], [("is", "ada", "wet"), ("is", "ada", "happy")], commit=False, rules=rg)
    assert res.status == "inconclusive"
    assert ("ada", "is", "wet") in res.derived
    assert h.ask_goal(kb, "is ada wet", rules) == ["no"]     # still read-only
