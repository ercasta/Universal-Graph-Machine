"""FACTS-AS-TRUTH-BEARERS (primitive ② / causation C3) — propositional modus ponens over facts.

"A holds and A causes B ⇒ B holds" where A and B are whole PROPOSITIONS. The binder spike recorded C3
as a flat GAP ("clauses must be S-P-O, no dereify"); the facts-as-truth-bearers spike RE-PROBED it and
found the real, narrower wall: PREDICATE-VARIABLE MATCHING. With that primitive built, propositional
causation is DECLARED DATA — a reification bridge of three ordinary rules (bench/
spike_facts_as_truth_bearers.py), honouring "domain logic ONLY in banks" / "causation is not privileged".

The primitive is GENERAL (not causation-specific): reading a fact through a bound predicate variable,
plus a variable-predicate head that derives a runtime-chosen predicate — which also lights up generic
relation-property rules (transitivity written once over `?r`). Both engines: forward `run_bank` AND the
demand chain (`check`), so forward/demand parity holds.

Tested at the machine/rule layer (like the binder spike): the primitive, not any question surface.
"""
from ugm import assemble_facts, derived_triples, run_bank
from ugm.attrgraph import AttrGraph
from ugm.check import POSITIVE, ASSUMED_NO, check
from ugm.cnl.machine_rules import load_machine_rules
from ugm.cnl.rule_graph import write_rule
from ugm.machine import Machine

# The declared reification bridge (propositional causation as ordinary rules):
REIFY = "?h truth yes when ?h subj ?s and ?h pred ?p and ?h obj ?o and ?s ?p ?o"
MP = "?b truth yes when ?a truth yes and ?a causes ?b"
DEREIFY = "?s ?p ?o when ?h subj ?s and ?h pred ?p and ?h obj ?o and ?h truth yes"
BRIDGE = [REIFY, MP, DEREIFY]

# A = (door1 is open), B = (cat flees yes), reified into handles, with the propositional link A causes B.
HANDLES = ["ha subj door1", "ha pred is", "ha obj open",
           "hb subj cat", "hb pred flees", "hb obj yes",
           "ha causes hb"]


def _kb(facts, rules_text=()):
    g = AttrGraph()
    triples = [tuple(f.split()) if isinstance(f, str) else f for f in facts]
    if triples:
        Machine().run(g, assemble_facts(triples))
    for rt in rules_text:
        for rule in load_machine_rules(rt):
            write_rule(g, rule)
    return g


def _forward(facts, rules_text):
    g = _kb(facts)
    rules = [r for rt in rules_text for r in load_machine_rules(rt)]
    run_bank(g, rules)
    return g, set(derived_triples(g))


# --- the primitive itself: predicate-variable matching --------------------------------------------

def test_reify_reads_a_fact_through_a_bound_predicate_variable():
    """`?h truth yes when … ?h pred ?p … and ?s ?p ?o` — the reify direction reads the fact `(door1 is
    open)` through the predicate `?p` names (bound to the value node `is`). This is THE wall the spike
    named ("no ground anchor"); the dynamic-key TEST (`key_reg`) removed it."""
    _g, tr = _forward(["door1 is open"] + HANDLES, [REIFY])
    assert ("ha", "truth", "yes") in tr


def test_dereify_writes_a_runtime_chosen_predicate():
    """`?s ?p ?o when … ?h pred ?p … and ?h truth yes` — a variable-predicate HEAD asserts the edge the
    handle names. Native forward already (the MINT `key_reg`); pinned here as half the round trip."""
    _g, tr = _forward(["ha subj cat", "ha pred flees", "ha obj yes", "ha truth yes"], [DEREIFY])
    assert ("cat", "flees", "yes") in tr


# --- propositional causation as declared data (the full bridge) -----------------------------------

def test_propositional_causation_forward():
    """The three declared bridge rules together: the antecedent proposition holds ⇒ the consequent
    proposition is asserted as an ordinary fact. Propositional modus ponens, no engine privilege."""
    _g, tr = _forward(["door1 is open"] + HANDLES, BRIDGE)
    assert ("cat", "flees", "yes") in tr


def test_propositional_causation_forward_negative():
    """RE-BREAK / soundness: when the antecedent does NOT hold, the consequent must NOT be derived —
    the reify never fires, so nothing propagates. Guards against the bridge asserting B unconditionally."""
    _g, tr = _forward(HANDLES, BRIDGE)     # (door1 is open) absent
    assert ("cat", "flees", "yes") not in tr
    assert ("hb", "truth", "yes") not in tr


def test_propositional_causation_demand():
    """The same, on the DEMAND path (`check`), with NO forward pass — the var-pred rules must be
    reachable (wildcard head index) and applied (head-pred bound from the demand, body read via the
    bound pred). Forward/demand parity for the primitive."""
    g = _kb(["door1 is open"] + HANDLES, BRIDGE)
    assert check(g, ("flees", "cat", "yes")) == POSITIVE


def test_propositional_causation_demand_negative():
    """RE-BREAK on demand: antecedent absent ⇒ assumed-no (NAF), never a spurious positive."""
    g = _kb(HANDLES, BRIDGE)
    assert check(g, ("flees", "cat", "yes")) == ASSUMED_NO


# --- the primitive is GENERAL, not causation-specific ---------------------------------------------

def test_generic_transitivity_over_a_predicate_variable_demand():
    """The SAME primitive lights up a relation-property rule written ONCE over `?r`: generic
    transitivity. On demand the query supplies the anchor (`?x` = a), so predicate-variable reads bind
    and chain. (Causation is not privileged — this is the point.)"""
    g = _kb(["a rel b", "b rel c"], ["?x ?r ?z when ?x ?r ?y and ?y ?r ?z"])
    assert check(g, ("rel", "a", "c")) == POSITIVE


def test_variable_predicate_does_not_overreach():
    """RE-BREAK / soundness: a variable-predicate transitive rule must not manufacture a cross-predicate
    edge — `?x ?r ?z` binds ONE `?r` per firing, so `a rel b` + `b other c` does NOT yield `a rel c`
    (nor `a other c`). Guards the dynamic key against collapsing distinct predicates."""
    g = _kb(["a rel b", "b other c"], ["?x ?r ?z when ?x ?r ?y and ?y ?r ?z"])
    assert check(g, ("rel", "a", "c")) == ASSUMED_NO
    assert check(g, ("other", "a", "c")) == ASSUMED_NO


# --- the boundary that stays out ------------------------------------------------------------------

def test_two_token_holds_clause_still_rejected():
    """The spike's stated stop was really an ARITY one: a 2-token `?b holds` (unary truth predicate) is
    still not authorable — a clause is `S P O`. Facts-as-truth-bearers routes truth through a 3-token
    `?h truth yes`, never a bare `holds`. Pinned so the arity boundary is explicit, not accidental."""
    import pytest
    with pytest.raises(Exception):
        load_machine_rules("?b holds when ?a causes ?b")
