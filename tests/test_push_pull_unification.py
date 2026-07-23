"""PUSH/PULL UNIFICATION — the reactive-core arc's payoff (STEP C.3, docs/design/reactive_core.md).

`test_forward_demand_parity.py` guards that the two ENGINES (forward `run_bank`, demand `chain_sip`) answer
the same question the same way. This gate adds the reactive-core claim on top: the reactive PUSH — a cascade
that materializes eagerly at the firing gate (`reactive.fire`) with NO query — is a THIRD entry that agrees
with both, because the DERIVE reaction (`reactive._derive`) materializes each grain by calling `chain_sip`.
So PUSH is *event-triggered PULL*: there is no second evaluator on the reactive path, both read the same
canonical + guarded `_facts_matching` view (STEP A), and the forward/demand guard-divergence class cannot
recur on it — demonstrated over the SAME guard-sensitive battery, three-way:

    PUSH(reactive fire)  ==  PULL(demand ask)  ==  FORWARD(run_bank)

The load-bearing case is `negation_over_derived` (feedback #18): PUSH writes a derived fact INTO the graph
eagerly, and a downstream NAC reads it — the exact configuration where a NAIVE push (firing reactions in
dirty order rather than stratified) would manufacture a mis-stratified world. It agrees because each reactive
grain's `chain_sip` is a full stratified demand derivation, so cross-grain firing order cannot mis-stratify.
"""
import warnings

import pytest

import ugm as h
from ugm import load_machine_rules, ask_goal
from ugm.production_rule import literal_name
from ugm.reconsider import mark_dirty
from ugm.reactive import declare_reactive, fire

# The guard-divergence battery (mirrors test_forward_demand_parity.py: some subsets put the engines in the
# disagreeing configuration — conjunctive vs independent NAC (#16), negation over a derived fact (#18),
# recursion, a positive dependency chain). Kept independent of that file so the two gates cannot co-fail.
EDGES = [
    ("l1", "has", "c1"), ("l1", "has", "c2"), ("l2", "has", "z"),
    ("c1", "before", "c2"), ("z", "before", "c1"),
    ("c1", "emitted", "yes"), ("c1", "is_a", "seed"),
]

SHAPES = [
    ("conjunctive_nac", "?c ok yes when ?l has ?c and not ?x before ?c and not ?l has ?x"),
    ("independent_nacs", "?c ok yes when ?l has ?c and not ?c emitted yes and not ?c is_a seed"),
    ("negation_over_derived",
     "?c reachable yes when ?a before ?c\n?c ok yes when ?l has ?c and not ?c reachable yes"),
    ("positive_dependency_chain",
     "?c tagged yes when ?c is_a seed\n?c staged yes when ?c tagged yes\n?c ok yes when ?c staged yes"),
    ("recursion_then_negation",
     "?a reaches ?b when ?a before ?b\n?a reaches ?b when ?a before ?m and ?m reaches ?b\n"
     "?c ok yes when ?l has ?c and not ?c reaches ?c"),
    ("positive_join", "?c ok yes when ?l has ?c and ?c before ?o"),
]


def _world(mask: int) -> h.Graph:
    g = h.Graph()
    ids: dict[str, str] = {}
    def n(x):
        if x not in ids:
            ids[x] = g.add_node(x)
        return ids[x]
    for k, (s, p, o) in enumerate(EDGES):
        if mask >> k & 1:
            g.add_relation(n(s), p, n(o))
    return g


def _forward(mask, rules):
    g = _world(mask)
    h.run_bank(g, rules)
    return sorted({t[0] for t in h.derived_triples(g) if t[1] == "ok"})


def _demand(mask, rules):
    answers = ask_goal(_world(mask), "who ok yes", rules)
    return sorted({a.split(" ")[0] for a in answers if a != "(no answer)"})


def _push(mask, rules):
    """The PUSH entry: every head predicate declared reactive, the base facts marked as the landed events,
    the gate fired ONCE — the reactive cascade materializes eagerly. No query for `ok`; the DATA drove it."""
    g = _world(mask)
    for hp in {literal_name(pat.p) for r in rules for pat in r.rhs}:
        declare_reactive(g, hp)
    mark_dirty(g, [(p, o) for k, (s, p, o) in enumerate(EDGES) if mask >> k & 1])
    fire(g, rules)
    return sorted({t[0] for t in h.derived_triples(g) if t[1] == "ok"})


@pytest.mark.parametrize("shape,rule", SHAPES)
def test_push_pull_and_forward_agree_over_every_world(shape, rule):
    rules = load_machine_rules(rule)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for mask in range(1 << len(EDGES)):
            fwd, dem, psh = _forward(mask, rules), _demand(mask, rules), _push(mask, rules)
            assert fwd == dem == psh, (
                f"{shape}: entries disagree on world {mask:0{len(EDGES)}b}\n"
                f"  facts   = {[e for k, e in enumerate(EDGES) if mask >> k & 1]}\n"
                f"  forward = {fwd}\n  demand  = {dem}\n  push    = {psh}")


def test_the_push_sweep_is_not_vacuous():
    """Each shape must PUSH-derive something in some world and nothing in another, so the agreement above
    has content (a gate that only ever sees the empty answer proves nothing)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for shape, rule in SHAPES:
            rules = load_machine_rules(rule)
            seen = {bool(_push(mask, rules)) for mask in range(1 << len(EDGES))}
            assert seen == {True, False}, f"{shape} never discriminates under push (always {seen})"


def test_the_push_column_rides_the_demand_engine(monkeypatch):
    """The gate's own gate: PUSH must be the DEMAND engine, not a lookalike. Re-break feedback #16 (decide
    each NAC atom SEPARATELY instead of grouping by shared free var) and require PUSH to then diverge from
    FORWARD on the conjunctive shape — proving the push column genuinely runs `chain_sip` and would surface
    a real engine regression, not silently agree because it shares nothing with the demand path."""
    from ugm import chain
    monkeypatch.setattr(chain, "_nac_atom_groups", lambda fact_g, st, atoms: [[a] for a in atoms])
    rules = load_machine_rules(dict(SHAPES)["conjunctive_nac"])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        divergences = [mask for mask in range(1 << len(EDGES)) if _forward(mask, rules) != _push(mask, rules)]
    assert divergences, "push no longer detects the #16 conjunctive-NAC divergence — it is not riding chain_sip"
