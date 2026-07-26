"""THE TRACE NETWORK — `docs/design/substrate_inversion.md` §16.6, §20.

Promoted from `bench/spike_trace_network.py` (40/40). Written as the document's claims, not as unit tests
of the code — so a claim that stops being true fails here by name.

§16.6 REASONED this and did not measure it: `why` is not a backward walk along wires (three independent
reasons, §20), and the replacement is a parallel, forward-built, append-only network over firing events.
Four of these tests exist because the reasoning could not have found what they found — see §20.1.
"""
from __future__ import annotations

import pytest

from units import Budget, Fact, Net, Subgraph, Triple, Var, branch, given, mint, rule, role
from units import trace as T
from units.match import Absent

X, Y, Z = Var("x"), Var("y"), Var("z")


def cited_units(node) -> set:
    if node is None:
        return set()
    got = {node["unit"].name} if node["unit"] is not None else set()
    for b in node["because"]:
        got |= cited_units(b)
    return got


def deepest(node) -> int:
    """Max over ALL premises. A single-branch walk measures the hash seed, not the depth."""
    return 0 if not node or not node["because"] else 1 + max(deepest(b) for b in node["because"])


@pytest.fixture
def syllogism():
    socrates, man, mortal = mint("socrates"), mint("man"), mint("mortal")
    n = Net()
    n.spawn(given("base", [Fact(socrates, "is_a", man)]))
    n.declare("MORTAL", (Triple(X, "is_a", man),), Triple(X, "is_a", mortal))
    n.run(Budget(200))
    return n, socrates, man, mortal


@pytest.fixture
def two_hop():
    a, b, c = mint("a"), mint("b"), mint("c")
    n = Net()
    n.spawn(given("g", [Fact(a, "p", b), Fact(b, "q", c)]))
    n.declare("R1", (Triple(X, "p", Y),), Triple(X, "r", Y))
    n.declare("R2", (Triple(X, "r", Y), Triple(Y, "q", Z)), Triple(X, "s", Z))
    n.run(Budget(400))
    return n, a, b, c


# -- why reads what FIRED ------------------------------------------------------------------------------

def test_why_attributes_the_conclusion_to_the_unit_that_derived_it(syllogism):
    n, socrates, man, mortal = syllogism
    w = n.why(Fact(socrates, "is_a", mortal))
    assert w is not None and w["unit"].name == "MORTAL#1"
    assert [b["fact"] for b in w["because"]] == [Fact(socrates, "is_a", man)]


def test_a_given_is_in_degree_zero_and_needs_no_special_case(syllogism):
    """§2: *"you told me"* is not a special case in `why` — it is a firing with no premises."""
    n, socrates, man, mortal = syllogism
    w = n.why(Fact(socrates, "is_a", mortal))
    assert w["because"][0]["fact"] == Fact(socrates, "is_a", man)
    assert w["because"][0]["because"] == []


def test_the_unit_handle_is_opaque(syllogism):
    """§16.6: a firing may name its form only as an OPAQUE HANDLE, or `form_inventory.md` §4d's L0 leaks
    out through the trace."""
    n, *_ = syllogism
    tr = n.units["MORTAL#1"].trace_output
    reachable = {f.o for f in tr.by_pred(T.FIRED_BY)}
    assert reachable == {u.handle for u in n.units.values() if u.handle in reachable}
    assert not (tr.predicates() - T.TRACE_PREDICATES)   # nothing but vocabulary — no lhs, no rhs, no form


def test_the_walk_reaches_a_given_two_hops_up(two_hop):
    n, a, b, c = two_hop
    w = n.why(Fact(a, "s", c))
    assert deepest(w) >= 2
    assert cited_units(w) >= {"R2#1", "R1#1", "g"}


def test_the_explanation_is_deterministic(two_hop):
    """Premises live in a frozenset, so an unsorted walk makes an explanation's SHAPE depend on the hash
    seed — [[perf-hash-seed-sensitivity]] in a new place. An explanation read twice must read the same."""
    n, a, b, c = two_hop
    assert T.render(n.why(Fact(a, "s", c))) == T.render(n.why(Fact(a, "s", c)))


# -- the two accretions run in opposite directions -----------------------------------------------------

def test_object_wire_is_subset_and_trace_wire_is_append_only(two_hop):
    """§16 vs §20: a rule emits only what it derived, while its trace still carries the whole chain.
    That is why they must be separate wires."""
    n, a, b, c = two_hop
    r1 = n.units["R1#1"]
    assert all(f.p == role("r") for f in r1.output)
    assert T.handle_of(r1.trace_output, Fact(a, "p", b)) is not None


def test_no_trace_leak_into_any_object_value(two_hop):
    """§16.6's constraint, asserted rather than intended — same spirit as the no-import rule."""
    n, *_ = two_hop
    assert n.trace_leaks() == []


def test_the_data_graph_stays_nameless(two_hop):
    """§21.2 — `ugm/attrgraph.py`'s guarantee, inherited. It used to need a CARVE-OUT: `value.sym` was
    name-equal so a predicate could sit in a firing record's node slot, and `Net.symbol_leaks()` policed
    the boundary. §22.5 retired both — a role is a real node — so namelessness is now UNIFORM and there is
    no exception left to guard. What remains is the claim itself, in the two places it can fail."""
    n, *_ = two_hop
    assert all(f.s.nid >= 1 and f.p.nid >= 1 and f.o.nid >= 1
               for u in n.units.values() for f in u.output)
    a1, a2 = mint("mary"), mint("mary")
    assert a1 != a2, "entities are never equal by name"
    assert role("likes") is role("likes"), "roles come from the form set, so they ARE shared"
    assert role("likes") != mint("likes"), "but a minted node is not a role — no interning by name"


def test_exact_naf_cannot_see_the_trace():
    """If provenance accreted into the object value, `Absent` would silently change question: from *"is P
    absent from the world I was handed?"* to *"was P mentioned in the derivation?"* (§6a)."""
    a, b = mint("a"), mint("b")
    n = Net()
    n.spawn(given("g", [Fact(a, "p", b)]))
    n.declare("NAF", (Triple(X, "p", Y), Absent(Triple(X, "blocked", Y))), Triple(X, "ok", Y))
    n.run(Budget(200))
    inst = n.units["NAF#1"]
    assert any(f.p == role("ok") for f in inst.output)
    assert not (inst.view().predicates() & T.TRACE_PREDICATES)


# -- BREAK ATTEMPTS: the four things the reasoning could not have found ---------------------------------

def test_minting_a_firing_node_does_not_destroy_termination():
    """§20.1(a). Every firing needs a fresh node; a fresh node per RUN means the trace differs every run,
    so "output unchanged" — the whole termination story (§7) — never holds. The signature guard is what
    makes the fixpoint survive the record of it."""
    a, b = mint("a"), mint("b")
    n = Net()
    n.spawn(given("g", [Fact(a, "p", b)]))
    n.declare("R", (Triple(X, "p", Y),), Triple(X, "r", Y))
    bud = n.run(Budget(500))
    assert not bud.exhausted
    before = {u.name: u.trace_output for u in n.units.values()}
    n.run(Budget(500))
    assert all(before[u.name] == u.trace_output for u in n.units.values())


def test_a_gate_that_shuts_takes_the_conclusion_back_and_leaves_a_stub():
    """§17.C on the trace side. Nothing is retracted and nothing cascades (§7) — but *"why did you change
    your mind?"* must still be answerable, which is §16.6's supersession stub."""
    lion, mane, h = mint("lion"), mint("mane"), mint("H")
    n = Net()
    g = n.spawn(given("g", [Fact(lion, "is_a", mane)]))
    gate = n.spawn(rule("GATE", (Triple(X, "is_a", mane),), Triple(X, "has", mane)))
    n.wire(g, gate)
    n.propagate(Budget(200))
    assert T.handle_of(gate.trace_output, Fact(lion, "has", mane)) is not None

    g.adds = Subgraph([Fact(lion, "is_a", h)])
    n.propagate(Budget(200))
    assert not any(f.p == role("has") for f in gate.output)
    stubs = list(gate.trace_output.by_pred(T.RETRACTED))
    assert len(stubs) == 1
    old = T.conclusion(gate.trace_output,
                       next(t.o for t in gate.trace_output.by_pred(T.CONCLUDED) if t.s == stubs[0].s))
    assert old == Fact(lion, "has", mane)


def test_stub_lifetime_is_measured_in_revisions_not_runs():
    """§20.1(b), and the first version of this test asserted the opposite. An IDLE run rebuilds nothing,
    so the stub stays — which is right: the answer to *"why did you change your mind?"* stays valid
    exactly as long as the mind has not changed again. What must not happen is ACCUMULATION."""
    lion, mane, h = mint("lion"), mint("mane"), mint("H")
    n = Net()
    g = n.spawn(given("g", [Fact(lion, "is_a", mane)]))
    gate = n.spawn(rule("GATE", (Triple(X, "is_a", mane),), Triple(X, "has", mane)))
    n.wire(g, gate)
    n.propagate(Budget(200))

    g.adds = Subgraph([Fact(lion, "is_a", h)])
    n.propagate(Budget(200))
    n.propagate(Budget(200))
    n.propagate(Budget(200))
    assert len(list(gate.trace_output.by_pred(T.RETRACTED))) == 1        # idle runs do not disturb it

    g.adds = Subgraph([Fact(lion, "is_a", mane)])                       # mind changed back
    n.propagate(Budget(200))
    assert not list(gate.trace_output.by_pred(T.RETRACTED))
    assert any(f.p == role("has") for f in gate.output)

    g.adds = Subgraph([Fact(lion, "is_a", h)])                          # and away again
    n.propagate(Budget(200))
    assert len(list(gate.trace_output.by_pred(T.RETRACTED))) == 1        # exactly one, never two


def test_pruning_keeps_the_chain_but_not_the_litter(two_hop):
    """§16.6: keep the last firing per unit plus whatever a kept one still cites. A rule emits only its
    conclusion, so every premise's firing is reachable ONLY through `<from>` — get that walk wrong and
    `why` quietly degrades to one hop while everything else still passes."""
    n, a, b, c = two_hop
    r2 = n.units["R2#1"]
    assert len(list(r2.trace_output.by_pred(T.FIRED_BY))) >= 3
    junk = mint("junk")
    assert T.handle_of(r2.trace_output, Fact(junk, "p", junk)) is None
    assert max(len(u.trace_output) for u in n.units.values()) < 60       # bounded, not accumulating


def test_the_trace_does_not_fuse_same_named_entities():
    """§5's identity requirement asked of the trace rather than of the join."""
    m1, m2, rich = mint("mary"), mint("mary"), mint("rich")
    n = Net()
    g = n.spawn(given("g", [Fact(m1, "is_a", rich)]))
    n.propagate(Budget(100))
    assert T.handle_of(g.trace_output, Fact(m1, "is_a", rich)) is not None
    assert T.handle_of(g.trace_output, Fact(m2, "is_a", rich)) is None


# -- the two claims that make this worth having --------------------------------------------------------

def test_an_ordinary_unit_can_consume_firing_events():
    """THE COMPOSABILITY CLAIM (§17.G, [[composability-principle]]). A trace fact is an ordinary fact, so
    a unit reads it with NO NEW CONSTRUCT. If it could not, the trace would be exactly the unreachable
    Python island it was built to remove.

    Hand-wired: the ASSEMBLER does not know about trace wires yet, which is honest scope for §20."""
    a, b = mint("a"), mint("b")
    n = Net()
    g = n.spawn(given("g", [Fact(a, "p", b)]))
    n.declare("R", (Triple(X, "p", Y),), Triple(X, "r", Y))
    n.run(Budget(300))
    src = n.units["R#1"]

    meta = n.spawn(rule("META", (Triple(Var("f"), T.FIRED_BY, Var("u")),
                                 Triple(Var("f"), T.CONCLUDED, Var("c"))),
                        Triple(Var("u"), "produced", Var("c"))))
    meta.inputs["R#1"] = src.trace_output
    meta.run()
    assert len(meta.derived("produced")) > 0
    assert {f.s.name for f in meta.derived("produced")} <= {u.name for u in n.units.values()}


def test_sibling_hypotheses_get_separate_records_and_minimal_ones():
    """§3b asked of the trace: if two sibling instances shared a record, `why` would attribute H2's
    conclusion to H1 — and read perfectly well while being wrong.

    ⭐ AND §4b's MINIMAL LABEL ARRIVES FREE (§20.1c): a firing cites what it CONSUMED, not the chain it
    travelled, so the penguin conclusion does not mention base at all. The ATMS's expensive computation,
    as a side effect of recording the run."""
    bird, penguin, flies, tweety = mint("bird"), mint("penguin"), mint("flies"), mint("tweety")
    n = Net()
    base = n.spawn(given("base", [Fact(tweety, "is_a", bird)]))
    h1 = n.spawn(branch("H1", add=[Fact(tweety, "is_a", penguin)]))
    h2 = n.spawn(branch("H2", add=[Fact(tweety, "is_a", flies)]))
    n.wire(base, h1)
    n.wire(base, h2)
    n.declare("SEE", (Triple(X, "is_a", Y),), Triple(X, "seen_as", Y))
    n.run(Budget(600))

    assert len(n.instances["SEE"]) >= 2
    pen = cited_units(n.why(Fact(tweety, "seen_as", penguin)))
    fly = cited_units(n.why(Fact(tweety, "seen_as", flies)))
    assert "H1" in pen and "H2" not in pen
    assert "H2" in fly and "H1" not in fly
    assert "base" not in pen and "base" not in fly                       # minimal, not padded
    assert "base" in cited_units(n.why(Fact(tweety, "seen_as", bird)))   # and nothing is lost
    assert n.wellformed() == []
