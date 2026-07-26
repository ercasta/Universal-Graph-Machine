"""SELECTOR CHAINS — the expression builds the network (user proposal, 2026-07-26).

Spike: `bench/spike_selector_chain.py` (21/21). Asserted here: what a selector outputs, that the chain is
*assemblable* (unlike a wildcard rule), that each hop gates and reports its own failure, that the topology is a
tree, that belief is invariant under atom order — and the two defects the spike found.
"""
from __future__ import annotations

import pytest

from units import Budget, Fact, Net, Subgraph, Triple, Var, branch, given, mint, role
from units import discourse as D
from units.match import Absent
from units.vocab import lexeme as L

E, P, S, A, B = Var("e"), Var("p"), Var("s"), Var("a"), Var("b")
REF = role("<refers_to>")
NARROWS = role("<narrows>")
STEP = role("<step>")
RESOLVED, UNRESOLVED, AMBIG = role("<step_resolved>"), role("<unresolved>"), role("<step_ambiguous>")
ARG1, ARG2 = role("<arg1>"), role("<arg2>")     # POSITIONAL argument slots, never role labels

SENTENCE = [("movie_theater", []),
            ("garage", [Triple(E, "<near>", P)]),
            ("floor", [Triple(E, "<of>", P), Triple(E, "<ordinal>", L("third"))]),
            ("car", [Triple(E, "<parked_at>", P)])]


def _world(near_theater=True, two_garages_near=False, colour=None):
    th, g1, g2, f3, car = mint(""), mint(""), mint(""), mint(""), mint("")
    facts = [Fact(th, role("<word>"), L("movie_theater")),
             Fact(g1, role("<word>"), L("garage")),
             Fact(g2, role("<word>"), L("garage")),
             Fact(f3, role("<word>"), L("floor")), Fact(f3, role("<of>"), g1),
             Fact(f3, role("<ordinal>"), L("third")),
             Fact(car, role("<word>"), L("car")), Fact(car, role("<parked_at>"), f3)]
    if near_theater:
        facts.append(Fact(g1, role("<near>"), th))
    if two_garages_near:
        facts.append(Fact(g2, role("<near>"), th))
    if colour is not None:
        facts.append(Fact(car, role("<colour>"), colour))
    return Subgraph(facts), dict(garage=g1, other_garage=g2, floor=f3, car=car)


def _chain(w, steps, terminal=None):
    net = Net()
    net.spawn(given("world", w))
    nodes, prev, parse = [], None, []
    for i, (word, extra) in enumerate(steps, start=1):
        sk = mint(f"<s{i}>")
        nodes.append(sk)
        parse.append(Fact(sk, role("<is_a>"), STEP))
        lhs = ([] if prev is None else [Triple(prev, REF, P)]) + [Triple(E, "<word>", L(word))] + list(extra)
        net.declare(f"S{i}", tuple(lhs), Triple(sk, REF, E))
        if prev is not None:
            parse.append(Fact(sk, NARROWS, prev))
        prev = sk
    call = mint("<call>")
    if terminal:
        # POSITIONAL, not role-labelled: the call carries its lexeme through the same `<word>` predicate a
        # mention uses, and its argument is NUMBERED and points at the STEP.
        net.declare("CALL", (Triple(prev, REF, E),), Triple(call, ARG1, prev))
        parse += [Fact(call, role("<word>"), L(terminal)), Fact(call, NARROWS, prev)]
    net.spawn(branch("parse", add=Subgraph(parse)))     # DOWNSTREAM of the world — see the test below
    net.wire("world", "parse")
    return net, nodes, call


def _demands(net):
    net.declare("SELF", *D.self_rule())
    net.declare("RESOLVED", (Triple(S, REF, E),), Triple(S, RESOLVED, S))
    net.declare("UNRESOLVED", (Triple(S, "<is_a>", STEP), Absent(Triple(S, RESOLVED, S))),
                Triple(S, UNRESOLVED, S))
    net.declare("STEP_AMBIG", (Triple(S, REF, A), Triple(S, REF, B), Absent(Triple(A, D.SELF, B))),
                Triple(S, AMBIG, S))


def _got(net, pred):
    return {f for _, f in net.derived_anywhere(pred)}


@pytest.fixture
def resolved():
    w, ent = _world()
    net, steps, call = _chain(w, SENTENCE, terminal="wash")
    net.run(Budget(200000))
    return net, steps, call, ent


# -- what a selector outputs -----------------------------------------------------------------------

def test_the_chain_resolves_and_the_call_argument_dereferences_to_the_entity(resolved):
    net, steps, call, ent = resolved
    assert Fact(call, ARG1, steps[-1]) in _got(net, "<arg1>")
    refs = {f.s: f.o for f in _got(net, "<refers_to>")}
    assert refs[steps[-1]] == ent["car"]


def test_a_call_is_positional_not_role_labelled(resolved):
    """⭐ A call is just another discourse node: a lexeme through the same `<word>` predicate a mention uses,
    plus NUMBERED arguments. The Davidsonian shape rejected for facts is not reintroduced for commands."""
    net, steps, call, ent = resolved
    assert Fact(call, role("<word>"), L("wash")) in set(net.units["parse"].output)
    assert not any(f.s == call and f.p not in (ARG1, ARG2, NARROWS, role("<word>"))
                   for u in net.units.values() for f in u.output)


def test_an_n_ary_call_stays_positional():
    """⭐ The case the original rejection of role-labelled edges was really about, arriving for COMMANDS.
    *"wash the car with the sponge"*: two arguments, each its own selector chain, numbered — no `<instrument>`."""
    w, ent = _world()
    sponge = mint("")
    w = w | Subgraph([Fact(sponge, role("<word>"), L("sponge"))])
    net = Net()
    net.spawn(given("world", w))
    sA, sB, call = mint("<a1>"), mint("<a2>"), mint("<call>")
    net.declare("A1", (Triple(E, "<word>", L("car")), Triple(E, "<parked_at>", ent["floor"])),
                Triple(sA, REF, E))
    net.declare("A2", (Triple(E, "<word>", L("sponge")),), Triple(sB, REF, E))
    net.declare("CALL1", (Triple(sA, REF, E),), Triple(call, ARG1, sA))
    net.declare("CALL2", (Triple(sB, REF, E),), Triple(call, ARG2, sB))
    net.spawn(branch("parse", add=Subgraph([Fact(call, role("<word>"), L("wash")),
                                            Fact(call, NARROWS, sA), Fact(call, NARROWS, sB)])))
    net.wire("world", "parse")
    net.run(Budget(200000))
    refs = {f.s: f.o for f in _got(net, "<refers_to>")}
    assert refs[sA] == ent["car"] and refs[sB] == sponge
    assert Fact(call, ARG1, sA) in _got(net, "<arg1>")
    assert Fact(call, ARG2, sB) in _got(net, "<arg2>")


def test_each_step_emits_one_reference_keyed_on_the_step_not_a_subgraph(resolved):
    """⭐ A description IDENTIFIES rather than CONSTITUTES: the entity stays a node and the subgraph is the
    constraint set on it. So a selector emits `<step> <refers_to> entity`, not the entity's subgraph."""
    net, steps, call, ent = resolved
    for i in range(1, 5):
        derived = net.units[f"S{i}#1"].last_derived
        assert len(derived) == 1
        fact = next(iter(derived))
        assert fact.s == steps[i - 1] and fact.p == REF


def test_the_chain_narrows(resolved):
    net, steps, call, ent = resolved
    assert ent["other_garage"] not in {f.o for f in _got(net, "<refers_to>")}


# -- the finding that matters: it is assemblable ----------------------------------------------------

def test_the_assembler_wires_every_selector_without_authoring(resolved):
    """⭐ The contrast with a wildcard rule. Every selector atom names its predicate, so the assembler can
    complete each join by itself — the expression contributes only ground STEP NODES, as data."""
    net, steps, call, ent = resolved
    for i in range(1, 5):
        prods = net.producers[f"S{i}#1"]
        assert "parse" in prods or "world" in prods
        if i > 1:
            assert f"S{i - 1}#1" in prods
    assert sorted(net.producers["parse"]) == ["world"]


def test_a_wildcard_rule_is_still_not_assemblable():
    """⚠ And the contrast is real, not an artifact of the world-comparability fix: coreference substitution
    still needs an authored merge, because its wildcard atom is satisfied by its own control facts."""
    m_a, f_a = D.mention("lion", D.INDEFINITE, [(role("roars"), role("#loudly"))])
    m_the, f_the = D.mention("lion", D.DEFINITE, [(role("sleeps"), role("#now"))])
    net = Net()
    net.spawn(given("discourse", D.utterance((m_a, f_a), (m_the, f_the))))
    D.declare_all(net, substitution=True)
    net.run(Budget(200000))
    out = set()
    for u in net.units.values():
        out |= set(u.output)
    assert Fact(m_the, role("roars"), role("#loudly")) not in out


# -- gating, failure, ambiguity ---------------------------------------------------------------------

def test_a_failing_hop_starves_everything_downstream():
    net, steps, call = _chain(_world(near_theater=False)[0], SENTENCE, terminal="wash")
    net.run(Budget(200000))
    assert not net.units["S2#1"].last_derived
    assert not _got(net, "<arg1>")
    assert len(_got(net, "<refers_to>")) == 1


def test_the_failing_step_is_named_not_merely_silent():
    net, steps, call = _chain(_world(near_theater=False)[0], SENTENCE, terminal="wash")
    _demands(net)
    net.run(Budget(400000))
    assert {f.s for f in _got(net, UNRESOLVED)} == set(steps[1:])


def test_ambiguity_is_named_at_the_step_that_has_two_referents():
    net, steps, call = _chain(_world(two_garages_near=True)[0], SENTENCE, terminal="wash")
    _demands(net)
    net.run(Budget(400000))
    assert {f.s for f in _got(net, AMBIG)} == {steps[1]}


# -- the two defects the spike found ---------------------------------------------------------------

def test_the_utterance_must_enter_downstream_of_the_kb_not_as_a_sibling_given():
    """⚠ Two independent `given`s are two WORLDS, so a rule needing the parse AND a derived fact cannot be
    assembled — and if the missing premise is negated its NAF goes vacuously true. Entering the parse as a
    carrier below the world makes it a descendant, hence joinable."""
    w, ent = _world(near_theater=False)
    sibling = Net()
    sibling.spawn(given("world", w))
    s1 = mint("<s1>")
    sibling.declare("S1", (Triple(E, "<word>", L("movie_theater")),), Triple(s1, REF, E))
    sibling.spawn(given("parse", [Fact(s1, role("<is_a>"), STEP)]))     # a SIBLING given — the wrong shape
    _demands(sibling)
    sibling.run(Budget(200000))
    assert not sibling.comparable("parse", "RESOLVED#1")
    assert {f.s for f in _got(sibling, UNRESOLVED)} == {s1}             # s1 DID resolve; this is the false report

    net, steps, call = _chain(w, SENTENCE, terminal="wash")             # the right shape
    _demands(net)
    net.run(Budget(400000))
    assert steps[0] not in {f.s for f in _got(net, UNRESOLVED)}


def test_only_a_carrier_forks_a_world_so_sibling_rules_may_be_joined():
    """⭐ Under subset output, computing anything means several sibling rules over one carrier. Judging worlds
    by raw reachability made those siblings incomparable, so a rule needing premises from two of them was
    unassemblable — and a negated one went vacuously true."""
    net, steps, call = _chain(_world(two_garages_near=True)[0], SENTENCE, terminal="wash")
    _demands(net)
    net.run(Budget(400000))
    assert net.comparable("SELF#1", "S1#1")                  # sibling RULES: same world
    assert any("SELF" in p for p in net.producers["STEP_AMBIG#1"])
    assert net.carriers("SELF#1") == net.carriers("S1#1")


def test_sibling_hypotheses_are_still_two_worlds():
    """⚠ The guard the carrier test must not weaken: sibling CARRIERS still fork."""
    a, b = mint("a"), mint("b")
    net = Net()
    net.spawn(given("base", [Fact(a, role("p1"), b)]))
    net.spawn(branch("H1", add=[Fact(a, role("block"), b)]))
    net.wire("base", "H1")
    net.spawn(branch("H2", add=[]))
    net.wire("base", "H2")
    net.declare("J", (Triple(Var("x"), "p1", Var("y")),
                      Absent(Triple(Var("x"), "block", Var("y")))), Triple(Var("x"), "ok", Var("y")))
    net.run(Budget(6000))
    assert not net.comparable("H1", "H2")
    assert len(net.instances["J"]) == 2
    assert sorted(bool(net.units[i].last_derived) for i in net.instances["J"]) == [False, True]


# -- tree, and surface-sensitivity -----------------------------------------------------------------

def test_the_topology_is_a_tree_not_a_pipeline():
    """⭐ "Postfix" would imply a linear stack. Two selectors read the SAME step, so a shared step has two
    consumers and the network is a DAG."""
    w, ent = _world()
    truck = mint("")
    w = w | Subgraph([Fact(truck, role("<word>"), L("truck")),
                      Fact(truck, role("<parked_at>"), ent["floor"])])
    net, steps, _ = _chain(w, SENTENCE[:3])
    s3 = steps[-1]
    c_car, c_truck = mint("<call_car>"), mint("<call_truck>")
    net.declare("CAR", (Triple(s3, REF, P), Triple(E, "<word>", L("car")),
                        Triple(E, "<parked_at>", P)), Triple(c_car, ARG1, E))
    net.declare("TRUCK", (Triple(s3, REF, P), Triple(E, "<word>", L("truck")),
                          Triple(E, "<parked_at>", P)), Triple(c_truck, ARG1, E))
    net.run(Budget(200000))
    targets = {(f.s, f.o) for f in _got(net, "<arg1>")}
    assert (c_car, ent["car"]) in targets and (c_truck, truck) in targets
    assert len(net.consumers["S3#1"]) == 2


def test_belief_is_invariant_under_atom_order():
    """⭐ The surface/epistemic line. Permuting a selector's atoms — same antecedent — gives the identical
    referent. Only *attachment* changes meaning, and attachment is what the chain encodes."""
    red = mint("red")
    w, ent = _world(colour=red)

    def sel(order):
        net = Net()
        net.spawn(given("world", w))
        sk = mint("<sx>")
        atoms = [Triple(E, "<word>", L("car")), Triple(E, "<parked_at>", ent["floor"]),
                 Triple(E, "<colour>", red)]
        if order == "B":
            atoms = [atoms[0], atoms[2], atoms[1]]
        net.declare("SEL", tuple(atoms), Triple(sk, REF, E))
        net.run(Budget(100000))
        return {f.o for f in _got(net, "<refers_to>")}

    assert sel("A") == sel("B") == {ent["car"]}


def test_the_chain_is_walkable_off_the_graph(resolved):
    """⭐ The duality, in the safe direction: the unfolded expression is readable by following `<narrows>`."""
    net, steps, call, ent = resolved
    facts = set(net.units["parse"].output)
    path, cur = [], call
    while True:
        nxt = next((f.o for f in facts if f.s == cur and f.p == NARROWS), None)
        if nxt is None:
            break
        path.append(nxt)
        cur = nxt
    assert path == list(reversed(steps))
    refs = {f.s for f in _got(net, "<refers_to>")}
    assert all(s in refs for s in steps)
