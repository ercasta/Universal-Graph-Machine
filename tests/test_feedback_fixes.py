"""Regression tests for the pystrider consumer feedback (docs/feedback_from_pystrider.md).

Theme: silent failures made LOUD. A non-triple machine-rule clause (#1), a skolem RHS-only head var
(#2), a case-folded query that silently misses (#3), a `Rule` object where a node-id is expected (#4),
and an unrecognized fact line (#5) now signal instead of quietly doing less. Plus a session ergonomics
gap: `suppose` now accepts `focus_scope` like `ask_goal` (#7). Round 3 (the CNL-rule-module asks):
`load_machine_rules` is memoized on the bank text (#9), `?a != ?b` is a declared DISTINCTNESS condition
honoured by the join on both engines (#11), and `ask_goal(commit=False)` is a read-only query over an
ephemeral pencil scope (#12). Round 4 (performance): the ~2.8ms fixed `ask_goal` floor (#13) — question
recognition and per-rule bank lowering are memoized (pure functions of text/rule), and `query_goal` is
the tuple-goal read-only sibling of `ask_goal` that skips the CNL layer entirely.
"""
import inspect
import warnings

import pytest

import ugm as h
from ugm import (load_machine_rules, write_rule, AttrGraph,
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
        assert ask_goal(g, "is eB a attribute", []) == ["no (assumed)"]          # still the folded miss...
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
    assert h.ask_goal(kb, "is ada wet", rules) == ["no (assumed)"]


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
    assert h.ask_goal(kb, "is ada wet", rules) == ["no (assumed)"]     # still read-only


# --- #9: load_machine_rules is memoized on the bank text (was: re-fold + re-validate per call) --------

def test_load_machine_rules_memoized_on_text():
    text = "?p made child when ?p is_a parent\n?x safe yes when ?x clear yes"
    a, b = load_machine_rules(text), load_machine_rules(text)
    assert a is not b                                       # the LIST is fresh per call...
    assert all(x is y for x, y in zip(a, b)) and len(a) == len(b) == 2   # ...the Rules are the memo's


def test_load_machine_rules_memo_ignores_comments_and_blank_lines():
    plain = "?p made child when ?p is_a parent"
    noisy = "# the parenthood rule\n\n  ?p made child when ?p is_a parent  \n"
    assert load_machine_rules(plain)[0] is load_machine_rules(noisy)[0]  # same normalized body


def test_load_machine_rules_defect_raises_every_call():
    # failures are NOT cached — each call re-raises (and the good bank is unaffected).
    for _ in range(2):
        with pytest.raises(ValueError, match="triple"):
            load_machine_rules("?e reached when ?e is_a attribute")


# --- #11: distinctness — `?a != ?b` is a declared condition the join honours (was: inexpressible) ----

_CONFLICT_NEQ = "?c write_conflict yes when ?a writes ?c and ?b writes ?c and ?a != ?b"


def _writes_world():
    # ok & yes BOTH write submit (a real conflict); cancel writes only its own slot (NOT a conflict).
    g = h.Graph(); ids = {}
    n = lambda x: ids.setdefault(x, ids.get(x) or g.add_node(x))
    for s, o in [("ok", "submit"), ("yes", "submit"), ("cancel", "cancel.slot")]:
        g.add_relation(n(s), "writes", n(o))
    return g


def test_neq_lifts_to_declared_distinct_condition():
    rule = load_machine_rules(_CONFLICT_NEQ)[0]
    assert [(d.var_a, d.var_b) for d in rule.distinct] == [("?a", "?b")]
    assert not any(p.p == "!=" for p in rule.lhs)           # lifted OUT of the match patterns


def test_neq_kills_self_join_false_positive_on_demand_path():
    # without `!=` the self-join (?a == ?b) flags EVERY written channel; with it, only the contested one.
    answers = ask_goal(_writes_world(), "who write_conflict yes", load_machine_rules(_CONFLICT_NEQ))
    assert answers == ["submit write_conflict yes"]         # cancel.slot's single writer stays clean


def test_neq_forward_driver_agrees():
    from ugm import run_bank, derived_triples
    g = _writes_world()
    run_bank(g, load_machine_rules(_CONFLICT_NEQ))
    assert {t[0] for t in derived_triples(g) if t[1] == "write_conflict"} == {"submit"}


def test_distinct_same_named_nodes_count_as_distinct():
    # a name is a label, not an identity: two DISTINCT nodes both named 'w' are two writers.
    g = h.Graph()
    c = g.add_node("chan")
    g.add_relation(g.add_node("w"), "writes", c)
    g.add_relation(g.add_node("w"), "writes", c)            # a second, distinct 'w'
    answers = ask_goal(g, "who write_conflict yes", load_machine_rules(_CONFLICT_NEQ))
    assert answers == ["chan write_conflict yes"]


def test_neq_bad_shapes_raise_loudly():
    for bad, why in ((_CONFLICT_NEQ.replace("?a != ?b", "?a != ?z"), "bound"),       # ?z bound nowhere
                     ("?c bad yes when ?a writes ?c and ?a != submit", "variables"),  # literal side
                     ("?a != ?b when ?a writes ?c and ?b writes ?c", "head"),         # != as a head
                     ("?c bad yes when ?a writes ?c and ?b writes ?c and not ?a != ?b", "not")):
        with pytest.raises(ValueError):
            load_machine_rules(bad)


# --- #12: ask_goal(commit=False) is READ-ONLY — a check-query never mutates what it checks -----------

def _contested_world():
    g = h.Graph(); ids = {}
    n = lambda x: ids.setdefault(x, ids.get(x) or g.add_node(x))
    g.add_relation(n("a"), "writes", n("c")); g.add_relation(n("b"), "writes", n("c"))
    return g


_CONTESTED = "?c contested yes when ?a writes ?c and ?b writes ?c and ?a != ?b"


def test_ask_goal_commit_false_yesno_is_read_only():
    assert "commit" in inspect.signature(ask_goal).parameters
    g = _contested_world()
    assert ask_goal(g, "is c contested yes", load_machine_rules(_CONTESTED), commit=False) == ["yes"]
    # the feedback's own poison test: with an EMPTY rulebank the derived fact must NOT still be there.
    assert ask_goal(g, "is c contested yes", load_machine_rules("")) == ["no (assumed)"]
    assert not [x for x in g.nodes() if g.name(x) == "<query>"]         # the pencil scope was swept


def test_ask_goal_commit_false_who_is_read_only():
    g = _contested_world()
    assert ask_goal(g, "who contested yes", load_machine_rules(_CONTESTED), commit=False) == ["c contested yes"]
    assert ask_goal(g, "is c contested yes", load_machine_rules("")) == ["no (assumed)"]


def test_ask_goal_default_still_commits():
    g = _contested_world()
    assert ask_goal(g, "is c contested yes", load_machine_rules(_CONTESTED)) == ["yes"]
    assert ask_goal(g, "is c contested yes", load_machine_rules("")) == ["yes"]     # inked, as documented


def test_ask_goal_commit_false_why_raises():
    g = _contested_world()
    with pytest.raises(ValueError, match="commit=False"):
        ask_goal(g, "why c contested yes", load_machine_rules(_CONTESTED), commit=False)


# --- #13: the fixed per-call floor — query_goal (tuple goal, no CNL layer) + compile-once memos ------

def test_query_goal_returns_matching_facts_read_only():
    from ugm import query_goal
    g = _contested_world()
    # bound goal: the yes/no shape — the matching fact comes back as data, nothing is inked.
    assert query_goal(g, ("contested", "c", "yes"), rules=load_machine_rules(_CONTESTED)) == \
        [("c", "contested", "yes")]
    assert ask_goal(g, "is c contested yes", load_machine_rules("")) == ["no (assumed)"]      # poison test (#12)
    assert not [x for x in g.nodes() if g.name(x) == "<query>"]         # the pencil scope was swept


def test_query_goal_free_slot_returns_id_pin():
    from ugm import query_goal, ById
    g = _contested_world()
    out = query_goal(g, ("contested", None, "yes"), rules=load_machine_rules(_CONTESTED))
    assert len(out) == 1
    s, p, o = out[0]
    assert p == "contested" and o == "yes"
    assert isinstance(s, ById) and g.name(s.node_id) == "c"             # witness as a collision-free pin


def test_query_goal_commit_true_materializes():
    from ugm import query_goal
    g = _contested_world()
    assert query_goal(g, ("contested", "c", "yes"), rules=load_machine_rules(_CONTESTED),
                      commit=True) == [("c", "contested", "yes")]
    assert ask_goal(g, "is c contested yes", load_machine_rules("")) == ["yes"]     # inked, as asked


def test_query_goal_accepts_reified_rule_graph():
    from ugm import query_goal
    from ugm.cnl.rule_graph import write_rule as write_rule_g
    rg = h.Graph()
    for r in load_machine_rules(_CONTESTED):
        write_rule_g(rg, r)
    for _ in range(2):                                   # reify-once reuse converges (no accretion bug)
        g = _contested_world()
        assert query_goal(g, ("contested", "c", "yes"), rules=rg) == [("c", "contested", "yes")]


def test_query_goal_underivable_is_empty():
    from ugm import query_goal
    g = h.Graph(); ids = {}
    n = lambda x: ids.setdefault(x, ids.get(x) or g.add_node(x))
    g.add_relation(n("a"), "writes", n("c"))             # ONE writer -> no conflict derivable
    assert query_goal(g, ("contested", "c", "yes"), rules=load_machine_rules(_CONTESTED)) == []


def test_lower_bank_rule_is_memoized_per_rule():
    from ugm.lowering import _lower_bank_rule
    rule = load_machine_rules(_CONTESTED)[0]
    first = _lower_bank_rule(rule)
    assert _lower_bank_rule(rule) is first               # compile-once: the same cached tuple
    assert _lower_bank_rule(rule, guard=True) is not first   # a distinct configuration lowers its own


def test_parse_question_memo_returns_isolated_copies():
    from ugm.cnl.query import _parse_question
    q1 = _parse_question("is c contested yes")
    q1["p"] = "corrupted"                                # a caller mutating its result…
    q2 = _parse_question("is c contested yes")
    assert q2["p"] == "contested"                        # …can never poison the memo


# --- #14: the read-side split-join diagnostic must not crash on a shared-literal / phantom endpoint ---

_DISCOUNT = "?m gets_discount yes when ?m premium yes and ?m big_spender yes"


def _discount_world():
    g = h.Graph(); ids = {}
    n = lambda x: ids.setdefault(x, ids.get(x) or g.add_node(x))
    g.add_relation(n("alice"), "premium", n("yes"))      # 'yes' is ONE shared object node across both facts
    g.add_relation(n("alice"), "big_spender", n("yes"))
    return g


def test_why_provenance_over_shared_literal_object():
    # #14: a why-trace whose decision object ('yes') is a literal shared across facts used to raise
    # KeyError in the split-join guard (_is_fact_entity -> is_control on the shared 'yes'). Both the
    # plain and provenance=True paths now render the same correct trace.
    g = _discount_world()
    plain = ask_goal(g, "why alice gets_discount yes", load_machine_rules(_DISCOUNT))
    prov = ask_goal(g, "why alice gets_discount yes", load_machine_rules(_DISCOUNT), provenance=True)
    assert plain[0].startswith("alice gets_discount yes")
    assert prov[0].startswith("alice gets_discount yes")


def test_split_join_guard_tolerates_phantom_endpoint():
    # #14 root cause: the read-only diagnostic guard walks EDGE endpoints, which are not guaranteed to
    # be minted nodes (a consumer that passes a raw label as an object id wires an edge to an
    # unregistered id). The guard must skip such a phantom endpoint, not crash on is_control's KeyError.
    from ugm.chain import _is_fact_entity
    g = h.Graph()
    alice = g.add_node("alice")
    g.add_relation(alice, "premium", "yes")              # 'yes' passed as a raw label — never minted
    assert _is_fact_entity(g, alice) is False            # the sole neighbour is a phantom -> no crash
