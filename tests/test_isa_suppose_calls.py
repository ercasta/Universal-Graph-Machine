"""
Phase 5.5 slice 3c — SUPPOSE scope authoring as a `<call>` mode (variable-length assumptions/predictions).

CHECK/CHOOSE (slices 1–2) are fixed-slot `<call>`s. SUPPOSE cannot be — a hypothesis carries a
VARIABLE-LENGTH list of assumptions and predictions, so slice 2 deliberately left it out of the
registry. Slice 3c supplies the list-argument encoding: a `<call> --tool--> suppose` carries any number
of `assume`/`predict` REIFIED TRIPLES (`<t> -[k_subj/k_pred/k_obj]-> …`, the machine-rule clause
vocabulary), and `mode_calls.suppose_tool` decodes them, runs the firmware `suppose` (mint `<hypothesis>`
scope → pencil → CHAIN+CHECK in-scope → CONFIRM/REFUTE/INCONCLUSIVE), and folds a `<suppose>` verdict
back — exactly the 3a/3b shape (rules emit calls, the EXISTING `<call>` loop services them, the effect
feeds back), extended to a construct whose args don't fit fixed slots.

Consistent with the 3a/3b ratification ("reuse the existing `<call>` machine-rule grammar; prose sugar
is later"), the authoring here is the EXISTING grammar — zero new prose forms, zero SLM debt. A prose
`suppose … predict …` sugar that folds to this reified encoding is a tracked follow-on (like `to NAME`).

Obligations pinned:
  1. servicing a suppose-call reproduces the direct `suppose(...)` verdict for all 3 outcomes, and
     CONFIRM's ink commit survives (the pencil/ink split works through the call boundary);
  2. the verdict is a CONTROL `<suppose>` node a downstream rule can branch on;
  3. a RULE authored in the existing grammar emits the call, the existing loop services it, and the
     verdict feeds back to drive a downstream rule.
"""
import ugm as h
from ugm import Pat, Rule
from ugm import (
    AttrGraph, run_bank, derived_triples, mode_registry, service_modes, suppose_results,
    CONFIRMED, REFUTED, INCONCLUSIVE, HYPOTHESIS,
    SUPPOSE_TOOL, SUPPOSE_RESULT, STATUS, ASSUME, PREDICT, LABEL, K_SUBJ, K_PRED, K_OBJ,
)
from ugm.dispatch import emit_call


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


def _has(g: AttrGraph, s: str, p: str, o: str) -> bool:
    return (s, p, o) in derived_triples(g)


def _ink(g: AttrGraph) -> set:
    """The INK layer only (non-control, non-inert rel nodes with real endpoints) — a committed
    assumption must be read out of ink (`derived_triples` includes control/pencil rels)."""
    out: set = set()
    for r in g.nodes():
        if g.is_control(r) or g.is_inert(r) or not g.predicate(r):
            continue
        preds = [s for s in g.pred(r) if not (g.is_control(s) or g.is_inert(s))]
        succs = [o for o in g.succ(r) if not (g.is_control(o) or g.is_inert(o))]
        for s in preds:
            for o in succs:
                if g.name(s) and g.name(o):
                    out.add((g.name(s), g.predicate(r), g.name(o)))
    return out


def _triple(g: AttrGraph, s: str, p: str, o: str) -> str:
    """A reified (subj, pred, obj) triple node — the list-element encoding a variable-length call slot
    points at. Authored uniformly in natural (subj, pred, obj) order; the tool re-orders for `suppose`.
    The slot components are FRESH name-carrying nodes (never `nodes_named`, which would alias a live
    predicate rel node — the interning hazard the machine-rule path avoids via the 3b key-aware INTERN
    fix): the tool reads only their NAMES, and `suppose` re-resolves the real entities by name."""
    t = g.add_node("<t>")                                  # control scaffolding
    g.add_relation(t, K_SUBJ, g.add_node(s))
    g.add_relation(t, K_PRED, g.add_node(p))
    g.add_relation(t, K_OBJ, g.add_node(o))
    return t


def _emit_suppose(g: AttrGraph, assumptions, predictions, label: str | None = None) -> str:
    """Materialize a `<call> --tool--> suppose` with N `assume` + N `predict` reified triples."""
    c = emit_call(g, SUPPOSE_TOOL, {LABEL: _ensure(g, label)} if label is not None else {})
    for s, p, o in assumptions:
        g.add_relation(c, ASSUME, _triple(g, s, p, o))
    for s, p, o in predictions:
        g.add_relation(c, PREDICT, _triple(g, s, p, o))
    return c


# --- 1: servicing a suppose-call reproduces the direct verdict, for each outcome --------------------

def test_suppose_call_confirms_and_commits_the_assumption_to_ink():
    # observed: tweety flies. Hypothesis `tweety is bird` predicts it -> confirmed, inked.
    g = _facts([("tweety", "is", "flyer")])
    rule_g = _reify([BIRD_FLIES])
    _emit_suppose(g, [("tweety", "is", "bird")], [("tweety", "is", "flyer")], label="h1")

    service_modes(g, rule_g)

    assert suppose_results(g) == [{STATUS: CONFIRMED, "of": "h1"}]
    assert ("tweety", "is", "bird") in _ink(g)             # the assumption entered ink and survived teardown
    assert g.nodes_named(HYPOTHESIS) == []                 # no pencil scaffolding lingers
    assert g.nodes_named("<call>") == []                   # the call was consumed


def test_suppose_call_refutes_on_a_contradiction_and_inks_nothing():
    # tweety is a penguin => `tweety is_not flyer` entailed. Supposing `tweety is bird` predicts
    # `tweety is flyer` — the supposition entails the OPPOSITE -> refuted, nothing inked.
    g = _facts([("tweety", "is", "penguin")])
    rule_g = _reify([BIRD_FLIES, PENGUIN_NOFLY])
    ink_before = _ink(g)
    _emit_suppose(g, [("tweety", "is", "bird")], [("tweety", "is", "flyer")], label="h")

    service_modes(g, rule_g)

    assert suppose_results(g)[0][STATUS] == REFUTED
    assert _ink(g) == ink_before                           # MONOTONE: ink untouched, pencil swept
    assert g.nodes_named(HYPOTHESIS) == []


def test_suppose_call_is_inconclusive_when_a_prediction_is_underivable():
    g = _facts([])
    rule_g = _reify([BIRD_FLIES])
    before = _ink(g)
    _emit_suppose(g, [("tweety", "is", "bird")], [("tweety", "is", "swimmer")])   # nothing derives swimmer

    service_modes(g, rule_g)

    assert suppose_results(g)[0][STATUS] == INCONCLUSIVE
    assert _ink(g) == before


# --- 2: the verdict is a CONTROL node (invisible to fact matching) ---------------------------------

def test_suppose_verdict_is_a_control_token():
    g = _facts([("tweety", "is", "flyer")])
    _emit_suppose(g, [("tweety", "is", "bird")], [("tweety", "is", "flyer")])
    service_modes(g, _reify([BIRD_FLIES]))
    res = g.nodes_named(SUPPOSE_RESULT)
    assert len(res) == 1
    assert g.is_control(res[0])
    assert str(g.get_attr(res[0], STATUS).value) == CONFIRMED


# --- 3: variable-length lists — several assumptions + several predictions in one call --------------

def test_suppose_call_carries_multiple_assumptions_and_predictions():
    # two assumptions, two predictions; every prediction holds under the supposition -> confirmed.
    g = _facts([])
    rule_g = _reify([BIRD_FLIES,
                     Rule(key="small_chirps", lhs=[Pat("?x", "is", "small")], rhs=[Pat("?x", "is", "chirper")])])
    _emit_suppose(g,
                  assumptions=[("robin", "is", "bird"), ("robin", "is", "small")],
                  predictions=[("robin", "is", "flyer"), ("robin", "is", "chirper")], label="robin")

    service_modes(g, rule_g)

    assert suppose_results(g) == [{STATUS: CONFIRMED, "of": "robin"}]
    assert ("robin", "is", "bird") in _ink(g)
    assert ("robin", "is", "small") in _ink(g)             # BOTH assumptions committed


# --- 4: a RULE authored in the EXISTING grammar emits the call; the loop services it; it feeds back -

def test_a_cnl_authored_rule_emits_a_suppose_call_and_a_downstream_rule_reacts():
    from ugm.cnl.machine_rules import load_machine_rules

    g = _facts([("tweety", "is", "flyer"), ("tweety", "is", "candidate")])
    rule_g = _reify([BIRD_FLIES])                          # the SUPPOSE tool's in-scope reasoning bank

    # Authored with the EXISTING `<call>? SLOT VALUE and …` machine-rule grammar (no new form, no SLM
    # debt): emit a suppose call whose `assume`/`predict` slots point at reified triples, then react to
    # the `<suppose>` verdict. `<suppose>?` binds the verdict node; `of` carries the label back.
    forward = load_machine_rules(
        "<call>? tool suppose and <call>? assume <a>? and <a>? k_subj tweety and <a>? k_pred is "
        "and <a>? k_obj bird and <call>? predict <p>? and <p>? k_subj tweety and <p>? k_pred is "
        "and <p>? k_obj flyer and <call>? label tweety when tweety is candidate\n"
        "?x confirmed_a_bird <yes> when <suppose>? status confirmed and <suppose>? of ?x")

    run_bank(g, forward, tools=mode_registry(rule_g))

    assert ("tweety", "is", "bird") in _ink(g)             # the serviced suppose confirmed + inked the assumption
    assert _has(g, "tweety", "confirmed_a_bird", "<yes>")  # the downstream rule reacted to the fed-back verdict
    assert g.nodes_named("<call>") == []
