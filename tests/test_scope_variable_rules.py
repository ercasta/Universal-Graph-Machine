"""Scope generalization Slice 2, PART (b): SCOPE-VARIABLE rules — the one genuinely new mechanism.

A rule ATOM may carry a RELATIVIZER `@?t` (`Pat.rel`): the atom is matched / written RELATIVIZED to the
temporal scope KEYED to `?t`, so a rule can BIND a fact's scope and RELATE two — the frame axiom
`has(x,y)@?t1 ∧ ?t1 before ?t2 ⇒ has(x,y)@?t2`, which persists a BINARY fact across time (the O2b wall,
dissolved). Tested at the ENGINE layer via `write_rule` (the CNL `@?t` surface is a separate slice).
"""
from ugm.attrgraph import AttrGraph
from ugm.production_rule import Pat, Rule
from ugm.cnl.rule_graph import write_rule, rules_in_graph
from ugm.check import check, POSITIVE, ASSUMED_NO
from ugm.scope_kinds import at_time, holds_at, order, indices_holding


def _frame_kb():
    """has(lion,mane)@t1 ; t1<t2<t3 ; the binary-fact frame axiom as a scope-variable rule."""
    g = AttrGraph()
    at_time(g, "t1", ("lion", "has", "mane"))
    order(g, "t1", "t2"); order(g, "t2", "t3")
    write_rule(g, Rule(key="frame.has",
                       lhs=[Pat("?x", "has", "?y", rel="?t1"), Pat("?t1", "before", "?t2")],
                       rhs=[Pat("?x", "has", "?y", rel="?t2")]))
    return g


# --- THE ACCEPTANCE: a binary fact persists across time (O2b dissolved) ----------------------------

def test_binary_fact_persists_one_hop():
    g = _frame_kb()
    assert holds_at(g, "t1", ("has", "lion", "mane")) == POSITIVE     # source
    assert holds_at(g, "t2", ("has", "lion", "mane")) == POSITIVE     # frame axiom @t1 → @t2


def test_persistence_chains_across_the_order():
    """Full persistence to ANY later index uses a TRANSITIVE order (`precedes`, the recursive rule of
    spike O1): `t1 precedes t3` holds, so the frame axiom carries the fact straight to t3. (With the
    direct-`before` axiom, a relativized body atom reads existing pencils rather than recursively
    demanding them, so multi-hop needs the intermediate materialized or a transitive order — this is
    the clean way to say 'holds at all later times'.)"""
    g = AttrGraph()
    at_time(g, "t1", ("lion", "has", "mane"))
    order(g, "t1", "t2"); order(g, "t2", "t3")
    write_rule(g, Rule(key="precedes.trans",           # transitive closure of `before` (O1)
                       lhs=[Pat("?a", "before", "?b"), Pat("?b", "precedes", "?c")],
                       rhs=[Pat("?a", "precedes", "?c")]))
    write_rule(g, Rule(key="precedes.base",
                       lhs=[Pat("?a", "before", "?b")], rhs=[Pat("?a", "precedes", "?b")]))
    write_rule(g, Rule(key="frame.has",                # frame axiom over the transitive order
                       lhs=[Pat("?x", "has", "?y", rel="?t1"), Pat("?t1", "precedes", "?t2")],
                       rhs=[Pat("?x", "has", "?y", rel="?t2")]))
    assert holds_at(g, "t2", ("has", "lion", "mane")) == POSITIVE
    assert holds_at(g, "t3", ("has", "lion", "mane")) == POSITIVE     # straight to t3 via t1 precedes t3


def test_a_timed_derivation_stays_non_veridical_globally():
    g = _frame_kb()
    holds_at(g, "t2", ("has", "lion", "mane"))                        # fire the frame axiom
    assert check(g, ("has", "lion", "mane")) == ASSUMED_NO            # still not the timeless world's


def test_the_conclusion_lands_in_the_right_scope():
    g = _frame_kb()
    holds_at(g, "t2", ("has", "lion", "mane"))
    assert "t2" in indices_holding(g, ("lion", "has", "mane"))        # penned AT t2, keyed correctly


# --- the relativizer actually BINDS and the ordering join actually CONSTRAINS ----------------------

def test_the_before_join_constrains_which_index_receives_it():
    """The `?t1 before ?t2` join is load-bearing: a timed fact whose index has NO ordering edge to the
    queried index is not persisted there. Otherwise `@?t` would leak every timed fact to every index."""
    g = AttrGraph()
    at_time(g, "t5", ("cat", "has", "fur"))                          # t5 is unordered w.r.t. t2
    order(g, "t1", "t2")
    write_rule(g, Rule(key="frame.has",
                       lhs=[Pat("?x", "has", "?y", rel="?t1"), Pat("?t1", "before", "?t2")],
                       rhs=[Pat("?x", "has", "?y", rel="?t2")]))
    assert holds_at(g, "t2", ("has", "cat", "fur")) == ASSUMED_NO    # t5 not before t2 → not carried


def test_a_relativized_body_atom_does_not_bind_an_index_from_ink():
    """A relativized atom `has(?x,?y)@?t1` reads TEMPORAL pencils only — an ink fact has no index, so
    the frame axiom cannot bind `?t1` from it and pens NO timed copy. (An ink fact still reads as
    holding at any index — it is timeless — so we assert the axiom did not FIRE, not that the read is
    negative.)"""
    from ugm import assemble_facts
    from ugm.machine import Machine
    g = AttrGraph()
    Machine().run(g, assemble_facts([("lion", "has", "mane")]))      # INK, not timed
    order(g, "t1", "t2")
    write_rule(g, Rule(key="frame.has",
                       lhs=[Pat("?x", "has", "?y", rel="?t1"), Pat("?t1", "before", "?t2")],
                       rhs=[Pat("?x", "has", "?y", rel="?t2")]))
    holds_at(g, "t2", ("has", "lion", "mane"))
    assert indices_holding(g, ("lion", "has", "mane")) == []         # no timed pencil was penned


# --- round-trip + additivity ----------------------------------------------------------------------

def test_relativizer_round_trips_through_the_graph():
    g = _frame_kb()
    r = next(x for x in rules_in_graph(g) if x.key == "frame.has")
    body_rels = sorted((p.p, p.rel) for p in r.lhs)
    assert ("before", "") in body_rels
    assert ("has", "?t1") in body_rels
    assert [(p.p, p.rel) for p in r.rhs] == [("has", "?t2")]


def test_un_relativized_rules_are_unaffected():
    """The relativizer is additive: an ordinary rule with no `@?t` reasons over ink exactly as before."""
    from ugm import assemble_facts
    from ugm.machine import Machine
    g = AttrGraph()
    Machine().run(g, assemble_facts([("socrates", "is_a", "man"), ("man", "is_a", "mortal")]))
    write_rule(g, Rule(key="isa.trans",
                       lhs=[Pat("?a", "is_a", "?b"), Pat("?b", "is_a", "?c")],
                       nac=[Pat("?a", "is_a", "?c")],
                       rhs=[Pat("?a", "is_a", "?c")]))
    assert check(g, ("is_a", "socrates", "mortal")) == POSITIVE
