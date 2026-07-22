"""Scope generalization Slice 2, PART (b) — the CNL `@?t` SURFACE for scope-variable rules.

The engine mechanism (`Pat.rel`, the per-atom relativizer) landed via `write_rule` and is tested in
`test_scope_variable_rules.py`. THIS file tests the machine-rule CNL surface that authors it: a clause
suffix `@?t` on a head or body atom (`?x has ?y @?t2 when ?x has ?y @?t1 and ?t1 before ?t2`) folds a
`k_rel` slot that `authoring._cond_pat` reflects into `Pat.rel`. So the frame axiom — persisting a
BINARY fact across time (the O2b wall, dissolved) — is now expressible in the language, not only by hand.
"""
from ugm.attrgraph import AttrGraph
from ugm.cnl.machine_rules import load_machine_rules
from ugm.cnl.rule_graph import write_rule
from ugm.check import check, POSITIVE, ASSUMED_NO
from ugm.temporal import at_time, holds_at, order, indices_holding


FRAME = "?x has ?y @?t2 when ?x has ?y @?t1 and ?t1 before ?t2"


# --- the fold: `@?t` becomes Pat.rel, `@` stripped to the scope-key variable -----------------------

def test_the_relativizer_folds_into_pat_rel():
    (r,) = load_machine_rules(FRAME)
    body = sorted((p.p, p.rel) for p in r.lhs)
    assert body == [("before", ""), ("has", "?t1")]          # `?t1 before ?t2` plain, `has @?t1`
    assert [(p.p, p.rel) for p in r.rhs] == [("has", "?t2")]  # head relativized to `?t2`


def test_the_at_prefix_is_stripped_to_a_variable():
    (r,) = load_machine_rules(FRAME)
    rels = {p.rel for p in (*r.lhs, *r.rhs) if p.rel}
    assert rels == {"?t1", "?t2"}                             # `@?t1`/`@?t2` -> `?t1`/`?t2`, no `@`


def test_the_relativized_atom_keeps_its_spo_slots():
    """The relativizer is NOT an S-P-O slot: `tokens()` stays (s, p, o) and the object is `?y`, not the
    `@?t` token — i.e. the relativizer did not get mis-folded as the clause object."""
    (r,) = load_machine_rules(FRAME)
    has = next(p for p in r.lhs if p.p == "has")
    assert has.tokens() == ("?x", "has", "?y")
    assert has.rel == "?t1"


# --- the acceptance: a binary fact persists across time, authored in CNL ---------------------------

def _frame_kb_from_cnl():
    g = AttrGraph()
    at_time(g, "t1", ("lion", "has", "mane"))
    order(g, "t1", "t2"); order(g, "t2", "t3")
    for r in load_machine_rules(FRAME):
        write_rule(g, r)
    return g


def test_binary_fact_persists_one_hop_from_cnl():
    g = _frame_kb_from_cnl()
    assert holds_at(g, "t1", ("has", "lion", "mane")) == POSITIVE     # source
    assert holds_at(g, "t2", ("has", "lion", "mane")) == POSITIVE     # frame axiom @t1 -> @t2


def test_the_cnl_derivation_stays_non_veridical_globally():
    g = _frame_kb_from_cnl()
    holds_at(g, "t2", ("has", "lion", "mane"))
    assert check(g, ("has", "lion", "mane")) == ASSUMED_NO
    assert "t2" in indices_holding(g, ("lion", "has", "mane"))


# --- additivity + re-break -------------------------------------------------------------------------

def test_an_un_relativized_machine_rule_is_unaffected():
    """The `@?t` surface is additive: a plain machine rule with no relativizer folds with empty rel on
    every atom, exactly as before (re-break — the defer NAC must not steal plain clauses)."""
    (r,) = load_machine_rules("?a is_a ?c when ?a is_a ?b and ?b is_a ?c")
    assert all(p.rel == "" for p in (*r.lhs, *r.rhs))
    assert [(p.s, p.p, p.o) for p in r.rhs] == [("?a", "is_a", "?c")]


def test_only_the_relativized_clause_fires_on_a_relativized_atom():
    """The plain and relativized clause forms are mutually exclusive on the presence of `@?t`: a
    relativized body atom folds EXACTLY ONE condition (with a rel), never a spurious second un-relativized
    copy — the plain clause defers via its `?co next @?t` NAC."""
    (r,) = load_machine_rules(FRAME)
    has_atoms = [p for p in r.lhs if p.p == "has"]
    assert len(has_atoms) == 1 and has_atoms[0].rel == "?t1"
