"""
Phase 5.5 (slice 1) — firmware MODES as §8 `<call>` calculators (`harneskills/isa/mode_calls.py`).

A CHECK mode is invoked exactly like a tool: a `<call> --tool--> check` node with goal slots, serviced
by the dumb dispatcher (`dispatch.service_calls`), which runs the firmware `check` and folds a `<check>`
verdict node back. Obligations pinned here:
  1. servicing a check-call produces the SAME verdict the direct `check(...)` call does (all 4 statuses);
  2. the verdict is a CONTROL node carrying the goal + status (a control-token program can branch on it);
  3. the dispatcher is content-blind — several mode-calls in one graph each get their own verdict, and
     WHICH mode / WHEN is decided by the calls present (data), not the dispatcher.
"""
import ugm as h
from ugm import Pat, Rule
from ugm import (
    AttrGraph, check, POSITIVE, ASSUMED_NO, ENTAILED_NEG, UNKNOWN,
    set_candidate, winners_of, run_bank, derived_triples,
)
from ugm.mode_calls import (
    CHECK_TOOL, CHOOSE_TOOL, PRED, SUBJ, OBJ, GOAL, ALPHA, STATUS, CHECK_RESULT,
    service_modes, check_results, choice_results, mode_registry,
)
from ugm.dispatch import emit_call


def _has(g: AttrGraph, s: str, p: str, o: str) -> bool:
    return (s, p, o) in derived_triples(g)


BIRD_FLIES = Rule(key="bird_flies", lhs=[Pat("?x", "is", "bird")], rhs=[Pat("?x", "is", "flyer")])
PENGUIN_NOFLY = Rule(key="peng_nofly", lhs=[Pat("?x", "is", "penguin")], rhs=[Pat("?x", "is_not", "flyer")])


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


def _ensure(g: AttrGraph, name: str) -> str:
    found = g.nodes_named(name)
    return found[0] if found else g.add_node(name)


def _emit_check(g: AttrGraph, pred: str, subj: str | None = None, obj: str | None = None) -> str:
    slots = {PRED: _ensure(g, pred)}
    if subj is not None:
        slots[SUBJ] = _ensure(g, subj)
    if obj is not None:
        slots[OBJ] = _ensure(g, obj)
    return emit_call(g, CHECK_TOOL, slots)


# --- 1: servicing a check-call reproduces the direct verdict, for each status --------------------

def test_check_call_emits_the_positive_verdict_and_materializes_the_fact():
    g = _facts([("robin", "is", "bird")])
    rule_g = _reify([BIRD_FLIES])
    _emit_check(g, "is", "robin", "flyer")

    service_modes(g, rule_g)

    results = check_results(g)
    assert results == [{"pred": "is", "subj": "robin", "obj": "flyer", "status": POSITIVE}]
    # the same verdict the direct firmware call returns (the call is just the dispatch shell)
    assert check(_facts([("robin", "is", "bird")]), rule_g, ("is", "robin", "flyer")) == POSITIVE


def test_check_call_emits_assumed_no_for_a_closed_world_miss():
    g = _facts([("robin", "is", "bird")])
    _emit_check(g, "is", "robin", "penguin")
    service_modes(g, _reify([BIRD_FLIES]))
    assert check_results(g) == [{"pred": "is", "subj": "robin", "obj": "penguin", "status": ASSUMED_NO}]


def test_check_call_emits_unknown_for_an_open_concept():
    g = _facts([("robin", "is", "bird")])
    _emit_check(g, "is", "robin", "hungry")
    service_modes(g, _reify([BIRD_FLIES]), open_preds=frozenset({"hungry"}))
    assert check_results(g) == [{"pred": "is", "subj": "robin", "obj": "hungry", "status": UNKNOWN}]


def test_check_call_emits_entailed_no_when_the_negative_is_derivable():
    g = _facts([("tweety", "is", "penguin")])
    _emit_check(g, "is", "tweety", "flyer")
    service_modes(g, _reify([BIRD_FLIES, PENGUIN_NOFLY]))
    assert check_results(g) == [{"pred": "is", "subj": "tweety", "obj": "flyer", "status": ENTAILED_NEG}]


# --- 2: the verdict is a CONTROL node (invisible to fact matching) -------------------------------

def test_check_verdict_is_a_control_token():
    g = _facts([("robin", "is", "bird")])
    _emit_check(g, "is", "robin", "penguin")
    service_modes(g, _reify([BIRD_FLIES]))
    res = g.nodes_named(CHECK_RESULT)
    assert len(res) == 1
    assert g.is_control(res[0])                            # control-layer — never touches reasoning
    assert str(g.get_attr(res[0], STATUS).value) == ASSUMED_NO


# --- 3: the dispatcher is content-blind; composition is the set of calls present (data) ----------

def test_several_mode_calls_are_each_serviced_and_the_call_is_consumed():
    g = _facts([("robin", "is", "bird"), ("tweety", "is", "penguin")])
    _emit_check(g, "is", "robin", "flyer")                 # -> positive (derivable)
    _emit_check(g, "is", "robin", "penguin")               # -> assumed-no
    service_modes(g, _reify([BIRD_FLIES]))

    by_goal = {(r["subj"], r["obj"]): r["status"] for r in check_results(g)}
    assert by_goal == {("robin", "flyer"): POSITIVE, ("robin", "penguin"): ASSUMED_NO}
    assert g.nodes_named("<call>") == []                   # every serviced call was consumed


# --- 4: CHOOSE as a call — goal (candidates pre-registered) -> argmax winner (slice 2) -----------

def _choose_graph() -> tuple[AttrGraph, str, dict[str, str]]:
    g = AttrGraph()
    goal = g.add_node("treatment")
    opts = {n: g.add_node(n) for n in ("aspirin", "ibuprofen", "paracetamol")}
    set_candidate(g, goal, opts["aspirin"], 0.6)
    set_candidate(g, goal, opts["ibuprofen"], 0.9)
    set_candidate(g, goal, opts["paracetamol"], 0.4)
    return g, goal, opts


def test_choose_call_selects_the_argmax_winner():
    g, goal, _ = _choose_graph()
    emit_call(g, CHOOSE_TOOL, {GOAL: goal})
    service_modes(g, AttrGraph())                          # CHOOSE needs no rule bank
    assert [g.name(w) for w in winners_of(g, goal)] == ["ibuprofen"]
    assert choice_results(g) == {"treatment": ["ibuprofen"]}


def test_choose_call_respects_the_alpha_cut():
    g, goal, _ = _choose_graph()
    emit_call(g, CHOOSE_TOOL, {GOAL: goal, ALPHA: g.add_node("0.95")})   # cut above every fit
    service_modes(g, AttrGraph())
    assert winners_of(g, goal) == []                       # all α-pruned -> no winner
    assert choice_results(g) == {}


def test_check_and_choose_compose_in_one_control_token_program():
    # A heterogeneous program: a CHECK call and a CHOOSE call in ONE graph, both serviced by the
    # content-blind dispatcher — the composition is the set of calls present (DATA), slice-2 shape.
    g = _facts([("robin", "is", "bird")])
    goal = g.add_node("treatment")
    a, b = g.add_node("aspirin"), g.add_node("ibuprofen")
    set_candidate(g, goal, a, 0.3)
    set_candidate(g, goal, b, 0.8)
    _emit_check(g, "is", "robin", "flyer")
    emit_call(g, CHOOSE_TOOL, {GOAL: goal})

    service_modes(g, _reify([BIRD_FLIES]))

    assert check_results(g) == [{"pred": "is", "subj": "robin", "obj": "flyer", "status": POSITIVE}]
    assert choice_results(g) == {"treatment": ["ibuprofen"]}
    assert g.nodes_named("<call>") == []


# --- 5: slice 3a — a RULE emits a mode-call, the EXISTING loop services it, the effect FEEDS BACK.
#        No new driver: `run_bank(..., tools=mode_registry(rule_g))` already services `<call>`s at
#        fixpoint. The forward bank ([emit, react]) does NOT contain the reasoning that answers the
#        goal — only the mode-call, serviced against `rule_g`, produces it. -----------------------

def test_a_rule_emitting_a_check_call_materializes_the_positive_and_a_downstream_rule_fires():
    g = _facts([("robin", "is", "bird")])
    rule_g = _reify([BIRD_FLIES])                          # the CHECK tool's backward bank
    # forward bank: emit a check for `?x is flyer` (NAC-deduped on the derived fact), then react to it.
    emit = Rule(key="emit.check.flyer",
                lhs=[Pat("?x", "is", "bird")], nac=[Pat("?x", "is", "flyer")],
                rhs=[Pat("<call>?", "tool", "check"), Pat("<call>?", "subj", "?x"),
                     Pat("<call>?", "obj", "flyer")])   # copula check: pred defaults to `is`
    react = Rule(key="react.flyer",
                 lhs=[Pat("?x", "is", "flyer")], rhs=[Pat("?x", "can_migrate", "<yes>")])

    run_bank(g, [emit, react], tools=mode_registry(rule_g))

    # `robin is flyer` exists ONLY because the check-call ran chain_sip over rule_g in the loop
    assert _has(g, "robin", "is", "flyer")
    assert _has(g, "robin", "can_migrate", "<yes>")        # the downstream rule fired on the fed-back fact
    assert g.nodes_named("<call>") == []                   # the call was consumed


def test_a_rule_reacts_to_a_negative_check_verdict_fed_back_by_the_loop():
    # The interesting case: the CWA `assumed-no` verdict is NOT a materialized fact — it feeds back
    # as the matchable `<check> -[status]-> assumed-no` / `-[of]-> ?x` control relations.
    g = _facts([("robin", "is", "bird")])
    rule_g = _reify([BIRD_FLIES])
    emit = Rule(key="emit.check.penguin",
                lhs=[Pat("?x", "is", "bird")], nac=[Pat("?c", "of", "?x")],   # dedup: stop once a verdict exists
                rhs=[Pat("<call>?", "tool", "check"), Pat("<call>?", "subj", "?x"),
                     Pat("<call>?", "obj", "penguin")])   # copula check: pred defaults to `is`
    react = Rule(key="react.assumed_no",
                 lhs=[Pat("?c", "status", "assumed-no"), Pat("?c", "of", "?x")],
                 rhs=[Pat("?x", "flagged", "<yes>")])

    run_bank(g, [emit, react], tools=mode_registry(rule_g))

    assert not _has(g, "robin", "is", "penguin")           # nothing materialized for the miss (§5-safe)
    assert _has(g, "robin", "flagged", "<yes>")            # yet the negative verdict drove the reaction


def test_a_rule_emitting_a_choose_call_drives_selection_and_a_downstream_rule():
    g = AttrGraph()
    goal = g.add_node("treatment")
    a, b = g.add_node("aspirin"), g.add_node("ibuprofen")
    set_candidate(g, goal, a, 0.4)
    set_candidate(g, goal, b, 0.9)
    emit = Rule(key="emit.choose",
                lhs=[Pat("?g", "candidate", "?o")], nac=[Pat("?g", "satisfied_by", "?w")],
                rhs=[Pat("<call>?", "tool", "choose"), Pat("<call>?", "goal", "?g")])
    react = Rule(key="react.choice",
                 lhs=[Pat("?g", "satisfied_by", "?w")], rhs=[Pat("?w", "selected", "<yes>")])

    run_bank(g, [emit, react], tools=mode_registry(AttrGraph()))

    assert [g.name(w) for w in winners_of(g, goal)] == ["ibuprofen"]
    assert _has(g, "ibuprofen", "selected", "<yes>")       # the winner drove the downstream rule
    assert g.nodes_named("<call>") == []


# --- 6: slice 3b — mode-calls composed via the EXISTING CNL machine-rule grammar (no new surface),
#        and a RELATIONAL check (pred != is), unblocked by the key-aware INTERN fix. --------------

EATS = Rule(key="eats", lhs=[Pat("?x", "is", "predator"), Pat("?y", "is", "prey")],
            rhs=[Pat("?x", "eats", "?y")])


def test_a_cnl_authored_rule_emits_a_relational_check_call_and_the_effect_feeds_back():
    from ugm.cnl.machine_rules import load_machine_rules

    g = _facts([("lion", "is", "predator"), ("zebra", "is", "prey")])
    rule_g = _reify([EATS])                                # the CHECK tool's backward bank

    # authored with the EXISTING `<call>? SLOT VALUE and ...` grammar (like planning_requests.cnl) —
    # no new form, no SLM debt. The goal predicate `eats` is carried as a literal: pre-fix this ran
    # away (INTERN aliased `eats` to the eats predicate); the key-aware INTERN fix makes it sound.
    forward = load_machine_rules(
        "<call>? tool check and <call>? subj ?x and <call>? pred eats and <call>? obj ?y "
        "when ?x is predator and ?y is prey and not ?x eats ?y\n"
        "?x is dangerous when ?x eats ?y")

    run_bank(g, forward, tools=mode_registry(rule_g))

    # the RELATIONAL goal was answered by the serviced check-call (chain_sip over rule_g) and fed back
    assert _has(g, "lion", "eats", "zebra")
    assert _has(g, "lion", "is", "dangerous")              # the downstream rule reacted to the derived fact
    assert g.nodes_named("<call>") == []
