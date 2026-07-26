"""§17 — the failure points, and the guarantees that survive them.

From `bench/spike_failure_points.py`. Two of the four cases FOUND something, and both were in constructs
§16 had just landed — which is the point of writing a spike to break your own work.
"""
from units.fuel import Budget
from units.match import Absent, Triple, Var
from units.net import Net
from units.unit import Unit, branch, given, rule
from units.value import Fact, mint

X, Y = Var("x"), Var("y")


def test_a_merge_can_restore_what_a_branch_dropped():
    """§17.A — the defect. §16.5 recommends a merge wired to both a rule and its branch to re-supply
    context; if the branch DROPPED a fact (§5's *"under H, not P"*), the merge hands it straight back."""
    lion, mane, h = mint("lion"), mint("mane"), mint("h")
    p = Fact(lion, "has", mane)
    net = Net()
    net.spawn(given("base", [p]))
    net.spawn(branch("H", add=[Fact(lion, "under", h)], remove=[p]))
    net.wire("base", "H")
    m = net.spawn(Unit("M"))
    net.wire("H", "M")
    net.wire("base", "M")
    net.propagate(Budget(limit=200))
    assert p in m.output, "the bypass is real — this test records it rather than wishing it away"
    assert net.restores_a_drop("M") == ("base", "H"), "and it is detectable from the wiring alone"
    assert any(k == "restores_a_drop" for k, _ in net.wellformed())


def test_a_well_formed_net_reports_nothing():
    """The negative control — without the ancestor wire there is no bypass and no complaint."""
    lion, mane, h = mint("lion"), mint("mane"), mint("h")
    p = Fact(lion, "has", mane)
    net = Net()
    net.spawn(given("base", [p]))
    net.spawn(branch("H", add=[Fact(lion, "under", h)], remove=[p]))
    net.wire("base", "H")
    m = net.spawn(Unit("M"))
    net.wire("H", "M")
    net.propagate(Budget(limit=200))
    assert p not in m.output
    assert net.wellformed() == []


def test_an_assembled_net_is_a_dag_which_is_where_the_fixpoint_comes_from():
    """§17.B — termination rests on "output unchanged", which is a fixpoint argument only if the network
    cannot oscillate. The assembler refuses back edges, so an assembled net is acyclic and settles."""
    a, p, q = mint("a"), mint("p"), mint("q")
    net = Net()
    net.spawn(given("base", [Fact(a, "is", a)]))
    net.declare("P", (Triple(X, "is", a), Absent(Triple(X, "is", q))), Triple(X, "is", p))
    net.declare("Q", (Triple(X, "is", p),), Triple(X, "is", q))
    budget = net.run(Budget(limit=400))
    assert not budget.exhausted, "it settles rather than running out of fuel"
    assert not any(k == "cycle" for k, _ in net.wellformed())


def test_a_hand_wired_cycle_is_reported_not_silently_tolerated():
    """The cycle guard's JUSTIFICATION MOVED (§17.B): built to contain accretion's runaway wiring, which
    §16 removed — but it is now the only thing between NAF and a silently order-dependent answer."""
    a, p, q = mint("a"), mint("p"), mint("q")
    net = Net()
    net.spawn(given("base", [Fact(a, "is", a)]))
    net.spawn(rule("P", (Triple(X, "is", a), Absent(Triple(X, "is", q))), Triple(X, "is", p)))
    net.spawn(rule("Q", (Triple(X, "is", a), Absent(Triple(X, "is", p))), Triple(X, "is", q)))
    net.wire("base", "P")
    net.wire("base", "Q")
    net.wire("P", "Q")
    net.wire("Q", "P")
    assert any(k == "cycle" for k, _ in net.wellformed())


def test_refire_takes_a_conclusion_back_when_a_gate_shuts():
    """§17.C — §16.7 listed refire as untested. Nothing is retracted; downstream simply re-runs (§7)."""
    a, b, key, out = mint("a"), mint("b"), mint("key"), mint("out")
    net = Net()
    src = net.spawn(given("src", [Fact(a, "raw", b)]))
    net.spawn(rule("G", (Triple(X, "raw", Y), Triple(X, "has", key)), Triple(X, "gated", Y)))
    net.wire("src", "G")
    d = net.spawn(rule("D", (Triple(X, "gated", Y),), Triple(X, "is", out)))
    net.wire("G", "D")
    net.propagate(Budget(limit=200))
    assert not d.derived()

    src.adds = src.adds.with_facts([Fact(a, "has", key)])
    net.propagate(Budget(limit=200))
    assert d.derived(), "gate opens -> the conclusion appears"

    src.adds = src.adds.without([Fact(a, "has", key)])
    net.propagate(Budget(limit=200))
    assert not d.derived(), "gate shuts -> it is taken back by recomputation, not by retraction"


def test_identity_is_sound_but_not_complete():
    """§17.D — the ceiling §14 never measured. Recorded so it cannot be mistaken for a guarantee."""
    from units.match import solve
    from units.value import Subgraph
    m1, m2, rich, john = mint("mary"), mint("mary"), mint("rich"), mint("john")
    v = Subgraph([Fact(john, "loves", m1), Fact(m2, "is", rich), Fact(m1, "same_as", m2)])
    assert not solve((Triple(Var("j"), "loves", X), Triple(X, "is", rich)), v), \
        "coreferent-but-distinct nodes do not join: id-equality is SOUND but INCOMPLETE"
    assert solve((Triple(Var("j"), "loves", X), Triple(X, "same_as", Y), Triple(Y, "is", rich)), v), \
        "a hand-authored coref-aware rule works — but that is a clause per template"


def test_the_assembler_splits_an_atomic_chain():
    """§18 — the DEFECT, recorded. A conditional's antecedent is internal to the concept; attaching to it
    reads a supposition as an assertion. The assembler does exactly that, and cannot be blamed: the
    syllogism below is structurally identical and attaching there is correct."""
    a, b, key = mint("a"), mint("b"), mint("key")
    net = Net()
    net.spawn(given("base", [Fact(a, "raw", b)]))
    net.spawn(rule("R1", (Triple(X, "raw", Y),), Triple(X, "mid", Y)))
    net.wire("base", "R1")
    net.spawn(rule("G", (Triple(X, "mid", Y), Triple(X, "has", key)), Triple(X, "gated", Y)))
    net.wire("R1", "G")
    net.propagate(Budget(limit=200))
    net.declare("OTHER", (Triple(X, "mid", Y),), Triple(X, "out", Y))
    net.run(Budget(limit=500))
    assert any(net.units[i].derived() for i in net.instances["OTHER"]), \
        "records the split rather than wishing it away — the fix needs FORCE, which units/ has no notion of"


def test_the_syllogism_must_keep_composing():
    """§18's contrast, and the negative control for any future fix: whatever forbids the split above must
    NOT forbid this, or transitive reasoning dies. Same shape, opposite verdict."""
    soc, plato, man, mortal, estate = (mint("socrates"), mint("plato"), mint("man"),
                                       mint("mortal"), mint("estate"))
    net = Net()
    net.spawn(given("socrates_is_a_man", [Fact(soc, "is_a", man)]))
    net.spawn(given("plato_is_a_man", [Fact(plato, "is_a", man)]))
    net.declare("MORTAL", (Triple(X, "is_a", man),), Triple(X, "is", mortal))
    net.declare("ESTATE", (Triple(X, "is", mortal),), Triple(X, "has", estate))
    net.run(Budget(limit=800))
    assert {f.s.name for _u, f in net.derived_anywhere("is")} == {"socrates", "plato"}
    assert {f.s.name for _u, f in net.derived_anywhere("has")}, "the intermediate MUST stay attachable"
