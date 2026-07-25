"""§16 — subset output, the gate, and the join. Promoted from `bench/spike_subset_output.py`.

These are the document's claims, written as tests rather than as unit tests of the code. The spike keeps
the head-to-head against accretion (it has to carry an `AccretionUnit` to do so); what lives here is what
must not silently regress.
"""
from units.fuel import Budget
from units.match import Triple, Var
from units.net import Net
from units.unit import Unit, branch, given, rule
from units.value import Fact, Subgraph, mint

X, Y, Z = Var("x"), Var("y"), Var("z")


def test_a_rule_emits_only_its_conclusion():
    """§16: a rule's output no longer contains its premises. That single change is what removes the need
    for the cycle guard and for projection dedup — a consumer can no longer look like a producer of the
    predicates it consumed."""
    a, b = mint("a"), mint("b")
    net = Net()
    net.spawn(given("src", [Fact(a, "next", b)]))
    r = net.spawn(rule("R", (Triple(X, "next", Y),), Triple(X, "reaches", Y)))
    net.wire("src", "R")
    net.propagate(Budget(limit=100))
    assert r.output.predicates() == {"reaches"}, "a rule must not re-emit what it read"
    assert Fact(a, "next", b) not in r.output


def test_a_non_firing_unit_is_a_real_gate():
    """THE GUARD (user, 2026-07-26): a chain expresses scope by DEACTIVATION. A unit whose input does not
    match emits nothing, and everything downstream is starved. Under accretion this leaked — the unit
    passed its whole view through — so the guard was decorative. It is now real, and that is what makes
    bypassing a unit a semantic change rather than a shortcut."""
    lion, danger, key = mint("lion"), mint("dangerous"), mint("key")
    net = Net()
    net.spawn(given("src", [Fact(lion, "is", danger)]))
    gate = net.spawn(rule("G", (Triple(X, "has", key),), Triple(X, "is", key)))   # never satisfied
    net.wire("src", "G")
    net.propagate(Budget(limit=100))
    assert gate.fired == 0
    assert not gate.output, "a gate that does not fire must not pass its input through"


def test_a_bypass_wire_defeats_the_gate():
    """The negative control for the claim above, and the reason `assemble` refuses a bypass: routing a
    consumer around a gate revives a conclusion the chain had silenced."""
    lion, danger, key, absent = mint("lion"), mint("dangerous"), mint("key"), mint("absent")
    net = Net()
    net.spawn(given("src", [Fact(lion, "is", danger)]))
    net.spawn(rule("G", (Triple(X, "has", key),), Triple(X, "is", key)))
    net.wire("src", "G")
    d = net.spawn(rule("D", (Triple(X, "is", danger),), Triple(X, "is", absent)))
    net.wire("G", "D")
    net.propagate(Budget(limit=100))
    assert not d.derived(), "gated: the chain must silence this"

    net.wire("src", "D")                                    # the skip connection
    net.propagate(Budget(limit=100))
    assert d.derived(), "a bypass revives it — which is why it is a semantic change, not a shortcut"


def test_the_assembler_completes_a_two_premise_lhs_by_joining():
    """§16's cost, and its answer. `?x reaches ?y AND ?y next ?z` needs `reaches` from the chain and `next`
    from base; accretion carried `next` along and the assembler never had to notice. It notices now, and
    supplying a predicate NO CHAIN UNIT PRODUCES is a JOIN — the merge node, made automatic."""
    a, b, c, d = mint("a"), mint("b"), mint("c"), mint("d")
    net = Net()
    net.spawn(given("base", [Fact(a, "next", b), Fact(b, "next", c), Fact(c, "next", d)]))
    net.declare("T", (Triple(X, "next", Y),), Triple(X, "reaches", Y))
    net.declare("T2", (Triple(X, "reaches", Y), Triple(Y, "next", Z)), Triple(X, "reaches", Z))
    net.run(Budget(limit=500))
    reached = {(f.s.name, f.o.name) for _u, f in net.derived_anywhere("reaches")}
    assert ("a", "d") in reached, "transitive depth needs the join the assembler now performs"


def test_the_assembler_wires_the_deepest_producer_not_the_first():
    """FRONTIER FIRST (§16). `base` and a branch carrying a context marker project identically onto the
    predicates the template reads, so projection dedup skips whichever comes second. Taking the first found
    wires the SHALLOWEST and silently drops the marker — which is a bypass, and it was a live defect."""
    lion, mane, t1, chain = mint("lion"), mint("mane"), mint("t1"), mint("chain")
    marker = Fact(chain, "at", t1)
    net = Net()
    net.spawn(given("base", [Fact(lion, "has", mane)]))
    net.spawn(branch("T1", add=[marker]))
    net.wire("base", "T1")
    net.declare("R", (Triple(X, "has", mane),), Triple(X, "is", lion))
    net.run(Budget(limit=500))
    assert any(marker in net.units[i].view() for i in net.instances["R"]), \
        "the rule must see the context of the chain it was wired into"


def test_a_firing_records_the_premises_it_consumed():
    """The INHERITANCE RECORD (§16). Once a rule emits only its conclusion there is no afterwards in which
    to work out which facts produced it, so annotations (a band, an attribution) must ride the firing
    record. One generic rule over `last_firing`, never a clause per template."""
    lion, hungry, danger, b75 = mint("lion"), mint("hungry"), mint("dangerous"), mint("b75")
    net = Net()
    net.spawn(given("src", [Fact(lion, "is", hungry), Fact(hungry, "band", b75)]))
    r = net.spawn(rule("R", (Triple(X, "is", hungry),), Triple(X, "is", danger)))
    net.wire("src", "R")
    net.propagate(Budget(limit=100))

    def inherit(unit, view):                                # ONE rule, over any template
        return {Fact(concl.o, "band", bf.o)
                for concl, consumed in unit.last_firing
                for prem in consumed
                for bf in view.by_pred("band") if bf.s in (prem.s, prem.o)}

    assert Fact(danger, "band", b75) in inherit(r, r.view())

    # CONTROL: no band on the premise must yield NOTHING, never a silent certainty.
    net2 = Net()
    net2.spawn(given("src2", [Fact(lion, "is", hungry)]))
    r2 = net2.spawn(rule("R2", (Triple(X, "is", hungry),), Triple(X, "is", danger)))
    net2.wire("src2", "R2")
    net2.propagate(Budget(limit=100))
    assert r2.derived(), "the rule must still fire"
    assert not inherit(r2, r2.view()), "absent annotation inherits nothing — it does not become certain"


def test_a_merge_is_the_carrier_cell_not_a_new_construct():
    """§2's taxonomy is by degree, and the merge node the proposal asked for is the cell it already had:
    in-degree >= 2, no delta, no rule. It is what re-supplies context downstream of a rule."""
    lion, mane, t1, chain = mint("lion"), mint("mane"), mint("t1"), mint("chain")
    marker = Fact(chain, "at", t1)
    net = Net()
    net.spawn(given("base", [Fact(lion, "has", mane)]))
    net.spawn(branch("T1", add=[marker]))
    net.wire("base", "T1")
    net.spawn(rule("R", (Triple(X, "has", mane),), Triple(X, "is", lion)))
    net.wire("T1", "R")
    m = net.spawn(Unit("M"))
    net.wire("R", "M")
    net.wire("T1", "M")
    net.propagate(Budget(limit=200))
    assert m.kind == "carrier"
    assert marker in m.output and Fact(lion, "is", lion) in m.output


def test_sibling_isolation_survives_subset_output():
    """§3b, re-checked under the change: the spawn policy depended on BRANCH accretion, which survives.
    Two incomparable hypotheses must still give two instances with one conclusion each."""
    jack, tall, h1, h2 = mint("jack"), mint("tall"), mint("h1"), mint("h2")
    net = Net()
    net.spawn(given("base", [Fact(jack, "is", tall)]))
    net.spawn(branch("H1", add=[Fact(jack, "has", h1)]))
    net.spawn(branch("H2", add=[Fact(jack, "has", h2)]))
    net.wire("base", "H1")
    net.wire("base", "H2")
    net.declare("E", (Triple(Var("p"), "is", tall), Triple(Var("p"), "has", Var("h"))),
                Triple(Var("p"), "concludes", Var("h")))
    net.run(Budget(limit=2000))
    per = {i: {f.o.name for f in net.units[i].derived("concludes")} for i in net.instances["E"]}
    assert {frozenset(v) for v in per.values()} == {frozenset({"h1"}), frozenset({"h2"})}, per
