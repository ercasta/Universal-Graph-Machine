"""
DROP_CTRL lowering in `run_bank` (implementation_plan.md Phase 0.3): a control rule's `drop`
deletes a reified control relation, while the opcode REFUSES a fact edge — so control-ness is
established by the PRODUCER (a rule touching a `<…>` control token), never by the drop itself.

Differential intent: a control relation minted by a `<…>`-gated rule and then dropped disappears;
a fact relation a drop rule targets (no control provenance) survives the refusal. These pin the
§5 fact-immutability invariant as an ENGINE-enforced structural property, not lint-time discipline.
"""
import pytest

import ugm as h
from ugm.production_rule import Pat, Rule
from ugm import run_bank, derived_triples
from ugm.lowering import _rule_touches_control
from ugm.machine import ControlEdgeError


def _triples(g):
    return set(derived_triples(g))          # already (subj-name, rel-name, obj-name) tuples


def test_touches_control_is_content_blind():
    """The classifier reads the reserved `<…>` syntax, never a predicate name."""
    ctrl = Rule(key="c", lhs=[Pat("?o", "candidate", "?c"), Pat("<need>?", "for", "?c")],
                rhs=[Pat("?o", "picked", "<yes>")])
    fact = Rule(key="f", lhs=[Pat("?x", "wants", "?y")], rhs=[Pat("?x", "happy", "?y")])
    assert _rule_touches_control(ctrl) is True     # body has <need>, head has <yes>
    assert _rule_touches_control(fact) is False


def test_control_relation_is_dropped():
    """A `<…>`-gated producer mints a CONTROL relation; a gated drop removes it via DROP_CTRL."""
    g = h.Graph()
    a = g.add_node("a")
    g.add_node("<go>")                                    # a bare control token present
    # producer: ?x picked <yes> when ?x seen <go>   (touches <go>/<yes> -> control output)
    produce = Rule(key="prod", lhs=[Pat("?x", "seen", "<go>")], rhs=[Pat("?x", "picked", "<yes>")])
    # seed the trigger fact
    go = next(n for n in g.nodes() if g.name(n) == "<go>")
    g.add_relation(a, "seen", go)
    run_bank(g, [produce])
    assert ("a", "picked", "<yes>") in _triples(g)        # control relation derived
    picked = next(n for n in g.nodes() if g.predicate(n) == "picked")
    assert g.is_control(picked)                            # stamped control at MINT

    # drop it: drop ?x picked <yes> when ?x picked <yes> and ?x seen <go>
    drop = Rule(key="drop", lhs=[Pat("?x", "picked", "<yes>"), Pat("?x", "seen", "<go>")],
                rhs=[], drop=[Pat("?x", "picked", "<yes>")])
    run_bank(g, [drop])
    assert ("a", "picked", "<yes>") not in _triples(g)    # gone
    assert not any(g.predicate(n) == "picked" for n in g.nodes())   # orphan rel node gc'd


def test_drop_of_a_fact_is_refused():
    """A drop whose target is a genuine FACT (produced by a control-free rule) is REFUSED by
    DROP_CTRL — the invariant has teeth independent of the drop rule's own gating."""
    g = h.Graph()
    a = g.add_node("a")
    b = g.add_node("b")
    g.add_relation(a, "likes", b)                         # a plain fact (not control)
    # a (mis-authored) drop targeting the fact, gated by a control token so it is well-formed
    g.add_node("<go>")
    drop = Rule(key="baddrop",
                lhs=[Pat("?x", "likes", "?y"), Pat("?z", "trigger", "<go>")],
                rhs=[], drop=[Pat("?x", "likes", "?y")])
    # no <go> trigger present, so it will not even match; assert the fact survives regardless
    run_bank(g, [drop])
    assert ("a", "likes", "b") in _triples(g)

    # now force the match and confirm the refusal fires.
    # Phase 2.2 (control-ness at mint): a bare `<go>` is now control-flagged, so the phase-1 run_bank
    # above GC'd it as an orphan control node (no edges — `lowering.py`'s orphan-control sweep). That is
    # the composition of two ratified behaviors (reserved `<…>` ⟹ control; orphan control is ephemeral),
    # so re-establish the token before wiring it (real control tokens always carry edges and never orphan).
    z = g.add_node("z")
    go = next((n for n in g.nodes() if g.name(n) == "<go>"), None) or g.add_node("<go>")
    g.add_relation(z, "trigger", go)
    with pytest.raises(ControlEdgeError):
        run_bank(g, [drop])
