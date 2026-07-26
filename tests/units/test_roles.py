"""PREDICATE-AS-NODE — `docs/design/substrate_inversion.md` §22.3, §22.5.

Promoted from `bench/spike_predicate_as_node.py` (26/26). The user's move: edges need no labels, because a
predicate can be a ROLE NODE. §17.E had recorded the predicate variable as the one missing primitive after
two independent requirements hit it in two days, and recommended BUILDING it. **This removes the need for
it instead** — `?p` is an ordinary node variable, so `?s ?p ?o` costs nothing anywhere.

The last two tests are the price, and they are the reason this file exists rather than a changelog entry.
"""
from __future__ import annotations

from units import Budget, Fact, Net, Subgraph, Triple, Var, given, mint, role, rule
from units import trace as T
from units.match import solve

S, P, O = Var("s"), Var("p"), Var("o")
A, B = Var("a"), Var("b")


# -- §17.E dissolved -----------------------------------------------------------------------------------

def test_the_predicate_variable_falls_out_with_no_new_primitive():
    """§17.E's hole, gone. `?p` binds like any other slot because it IS any other slot."""
    jack, mary, rich = mint("jack"), mint("mary"), mint("rich")
    view = Subgraph([Fact(jack, "likes", mary), Fact(mary, "is_a", rich)])
    bindings = solve((Triple(S, P, O),), view)
    assert len(bindings) == 2
    assert {b[P] for b in bindings} == {role("likes"), role("is_a")}


def test_a_bound_predicate_variable_survives_into_the_head():
    """And safety is the SAME rule, not a new one: bound by the body, refused otherwise."""
    jack, mary = mint("jack"), mint("mary")
    u = rule("SWAP", (Triple(S, P, O),), Triple(O, P, S))
    u.inputs["x"] = Subgraph([Fact(jack, "likes", mary)])
    u.run()
    assert Fact(mary, "likes", jack) in u.output


def test_an_unbound_head_predicate_is_still_refused():
    import pytest
    from units.match import UnsafePattern
    with pytest.raises(UnsafePattern):
        rule("BAD", (Triple(S, "is_a", O),), Triple(S, P, O))


def test_coref_merge_is_one_generic_unit():
    """§17.D, unblocked. *"Nothing may conclude 'same entity' FROM an id — a coref-merge unit DECIDES and
    the ids downstream merely record that decision."* That unit needed a generic substitution, which
    needed a predicate variable. Two atoms, and no clause per template
    (`form_inventory.md` §9's combinatorial explosion avoided)."""
    jack, mary, mary2, rich = mint("jack"), mint("mary"), mint("mary"), mint("rich")
    world = Subgraph([Fact(jack, "likes", mary2), Fact(mary2, "is_a", rich),
                      Fact(mary, "same_as", mary2)])
    u = rule("COREF", (Triple(A, "same_as", B), Triple(B, P, O)), Triple(A, P, O))
    u.inputs["w"] = world
    u.run()
    assert Fact(mary, "is_a", rich) in u.output, "B->A substituted, generically"
    assert len(u.lhs) == 2


def test_a_fact_can_occupy_a_node_slot():
    """§17.E's other requirement — entity boundaries as data — needs reification, and it is the SAME
    shape `units/trace.py` already uses for a conclusion handle. Third independent arrival at one
    construct."""
    jack, mary, boundary = mint("jack"), mint("mary"), mint("boundary")
    h = mint("f")
    f = Fact(jack, "likes", mary)
    view = Subgraph([f, Fact(h, "<subj>", f.s), Fact(h, "<role>", f.p), Fact(h, "<obj>", f.o),
                     Fact(boundary, "<member>", h)])
    hits = solve((Triple(Var("h"), "<subj>", Var("x")), Triple(Var("h"), "<role>", Var("r"))), view)
    assert len(hits) == 1 and hits[0][Var("r")] == role("likes")


# -- the index stays crisp: §22.3's table was too pessimistic ------------------------------------------

def test_a_role_is_an_identity_so_the_index_stays_crisp():
    """⭐ THE CORRECTION TO §22.3. It assumed all five predicate-keyed mechanisms go graded the moment
    predicates become nodes. They do not — a role is an IDENTITY, so this is still a dict lookup. They go
    graded only when SIMILARITY MATCHING arrives, which is a separate decision. So the one dangerous
    mechanism (§16.2's join/bypass test, a SEMANTIC guard) does not have to be taken to get §17.E."""
    view = Subgraph([Fact(mint("e"), "likes", mint("e")) for _ in range(20)]
                    + [Fact(mint("e"), "is_a", mint("e")) for _ in range(20)])
    assert len(view.by_pred("likes")) == 20
    assert len(view.by_pred(role("likes"))) == 20


def test_role_identity_comes_from_the_form_set_not_from_interning():
    """§22.5, and it is the load-bearing constraint. Two independently MINTED `likes` do not match —
    namelessness applies to roles exactly as to entities. So roles cannot be interned from a surface word
    at run time: that registry would be §3's forbidden second global structure, fusing two utterances of
    "likes" BY NAME. Forms mint them at load; utterances do not."""
    novel = mint("likes")
    view = Subgraph([Fact(mint("a"), novel, mint("b"))])
    assert not solve((Triple(S, role("likes"), O),), view), "a minted role is not the form set's role"
    assert solve((Triple(S, novel, O),), view), "it is only itself"


# -- THE PRICE ------------------------------------------------------------------------------------------

def test_a_wildcard_rule_consumes_its_own_control_predicate():
    """⚠ THE NEW COST (§22.5). A `?s ?p ?o` rule has no predicate to key on, so it matches the very
    `same_as` fact that LICENSES it and derives a reflexive junk fact from nothing.

    Generalised: **a generic rule cannot tell the object language from the control vocabulary that drives
    it.** This is `Net.trace_leaks()`'s problem arriving on the object wire, and the fix §20 already built
    and justified is the same one: give control its own wire. An inequality guard would work too, but it
    is a new primitive AND it puts the control vocabulary by hand into every generic rule."""
    jack, mary, mary2 = mint("jack"), mint("mary"), mint("mary")
    world = Subgraph([Fact(jack, "likes", mary2), Fact(mary, "same_as", mary2)])
    u = rule("COREF_OBJ", (Triple(A, "same_as", B), Triple(S, P, B)), Triple(S, P, A))
    u.inputs["w"] = world
    u.run()
    assert Fact(mary, "same_as", mary) in u.output, "the wildcard ate its own licence"


def test_a_wildcard_rule_defeats_the_index():
    """§10.5, made concrete and uncomfortable: the generic rule that AVOIDS the combinatorial explosion is
    the same one that makes *wake broadly* mean *wake always*. A variable role contributes no index key,
    so the template is a wildcard consumer — recorded rather than papered over."""
    n = Net()
    n.spawn(given("g", [Fact(mint("a"), "likes", mint("b"))]))
    n.spawn(rule("WILD", (Triple(S, P, O),), Triple(S, P, O)))
    assert not any("WILD" in names for names in n.lhs_index.values())
    n.spawn(rule("NARROW", (Triple(S, "likes", O),), Triple(S, "seen", O)))
    assert "NARROW" in n.lhs_index[role("likes")]


def test_the_trace_needs_no_name_equal_symbol_any_more():
    """`value.sym` (nid=0, equal BY NAME) existed only so a predicate could sit in a firing record's
    `<predicate>` slot, and it forced a guard to keep it out of the data graph. Both are retired: the role
    node goes in directly, and namelessness is uniform (§21.2, §22.5)."""
    import units.value as V
    assert not hasattr(V, "sym")
    assert not hasattr(Net, "symbol_leaks")
    a, b = mint("a"), mint("b")
    n = Net()
    g = n.spawn(given("g", [Fact(a, "likes", b)]))
    n.propagate(Budget(100))
    slot = next(t.o for t in g.trace_output.by_pred(T.PREDICATE))
    assert slot is role("likes"), "the trace holds the role node itself"
