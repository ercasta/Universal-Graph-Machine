"""Assembly — the §3b correction, pinned (`docs/design/substrate_inversion.md` §3, §3b, §4).

The claim under test is §4's: **scope is not a primitive, it is a chain.** What makes that true is not the
index — the index ALONE collapses the chains completely — but a purely local spawn policy over the
topology that already exists. These tests pin both halves, because the negative one is what would rot
silently.
"""
from __future__ import annotations

from units import FORMS, Budget, Fact, Net, Triple, Unit, Var, branch, given, mint, role

X, Y, Z = Var("x"), Var("y"), Var("z")
LHS = (Triple(X, "likes", Y), Triple(Y, "is", Z))
RHS = Triple(X, "admires", Z)


def _world():
    jack, mary, rich, poor = mint("jack"), mint("mary"), mint("rich"), mint("poor")
    net = Net()
    base = net.spawn(given("base", [Fact(jack, "likes", mary)]))
    h1 = net.spawn(branch("H1", add=[Fact(mary, "is", rich)]))
    h2 = net.spawn(branch("H2", add=[Fact(mary, "is", poor)]))
    net.wire(base, h1)
    net.wire(base, h2)
    return net


def _conclusions(net) -> list:
    return [{(f.s.name, f.o.name) for f in net.units[i].derived("admires")}
            for i in net.instances["E"]]


def test_the_policy_separates_the_chains():
    net = _world()
    net.declare("E", LHS, RHS)
    net.run(Budget(limit=200))
    assert _conclusions(net) == [{("jack", "rich")}, {("jack", "poor")}]
    assert len(net.instances["E"]) == 2, "one instance per independent branch"


def test_indexing_alone_would_collapse_them():
    """THE NEGATIVE CASE, and the reason §3b exists. Wire every producer of a matching predicate into one
    instance — which is what predicate-level indexing on its own licenses — and that instance sees BOTH
    hypotheses and derives both conclusions. §4's emergence claim goes with it."""
    net = _world()
    net.propagate()
    naive = net.spawn(Unit("E_naive", LHS, RHS))
    for p in ("base", "H1", "H2"):
        net.wire(p, naive)
    net.propagate()
    assert {(f.s.name, f.o.name) for f in naive.derived("admires")} == \
        {("jack", "rich"), ("jack", "poor")}


def test_the_quantifier_is_load_bearing():
    """`comparable with EVERY existing input`, not ANY. `base` is an ancestor of BOTH branches, so an
    any-test lets H2 join the instance already holding H1 and the chains collapse regardless."""
    net = _world()
    net.propagate()
    assert net.comparable("base", "H1") and net.comparable("base", "H2")
    assert not net.comparable("H1", "H2"), "sibling branches must be incomparable"


def test_assembly_is_order_independent_in_result():
    """Lazy assembly is order-DEPENDENT in the labels it produces and must not be in the conclusions.
    Building the branches in the opposite order must give the same set of chains."""
    net = Net()
    jack, mary, rich, poor = mint("jack"), mint("mary"), mint("rich"), mint("poor")
    base = net.spawn(given("base", [Fact(jack, "likes", mary)]))
    h2 = net.spawn(branch("H2", add=[Fact(mary, "is", poor)]))     # H2 FIRST this time
    h1 = net.spawn(branch("H1", add=[Fact(mary, "is", rich)]))
    net.wire(base, h2); net.wire(base, h1)
    net.declare("E", LHS, RHS)
    net.run(Budget(limit=200))
    assert sorted(map(sorted, _conclusions(net))) == \
        sorted(map(sorted, [{("jack", "poor")}, {("jack", "rich")}]))


def test_assembly_is_idempotent():
    net = _world()
    net.declare("E", LHS, RHS)
    net.run(Budget(limit=200))
    before = (len(net.units), sum(len(v) for v in net.producers.values()))
    assert net.assemble(Budget(limit=200)) == 0
    assert (len(net.units), sum(len(v) for v in net.producers.values())) == before


def test_lazy_spawn_materializes_nothing_nobody_needed():
    """§3: a template with no producer for its LHS is never instantiated. [[agent-not-theorem-prover]],
    structurally rather than by policy — and §4b's ATMS exponential is contained by exactly this."""
    net = _world()
    net.declare("E", LHS, RHS)
    net.declare("UNUSED", (Triple(X, "orbits", Y),), Triple(X, "is_a", Y))
    net.run(Budget(limit=200))
    assert net.instances["UNUSED"] == []
    assert net.instances["E"]


def test_a_rules_output_can_feed_another_rule():
    """Wiring completeness: nothing connects two templates by hand — the LHS/RHS index does, so a
    consumer is woken by a fact a producer DERIVED, not only by one that was asserted."""
    a, b, c = mint("a"), mint("b"), mint("c")
    net = Net()
    net.spawn(given("base", [Fact(a, "p", b), Fact(b, "q", c)]))
    net.declare("R1", (Triple(X, "p", Y), Triple(Y, "q", Z)), Triple(X, "r", Z))
    net.declare("R2", (Triple(X, "r", Y),), Triple(X, "s", Y))
    net.run(Budget(limit=200))
    assert net.derived_anywhere("s"), "R2 must be fed by what R1 derived"


def test_accretion_makes_cycles_the_default_and_the_assembler_refuses_them():
    """FOUND BY RUNNING, not by designing (§3b). Accretion means every downstream unit carries its
    ancestors' facts through, so it looks like a producer of every UPSTREAM predicate — and the assembler
    will happily wire a consumer back into its own producer. That is not a corner case, it is what happens
    by default on a two-rule chain."""
    a, b, c = mint("a"), mint("b"), mint("c")
    net = Net()
    net.spawn(given("base", [Fact(a, "p", b), Fact(b, "q", c)]))
    net.declare("R1", (Triple(X, "p", Y), Triple(Y, "q", Z)), Triple(X, "r", Z))
    net.declare("R2", (Triple(X, "r", Y),), Triple(X, "s", Y))
    net.run(Budget(limit=200))

    for consumer, producers in net.producers.items():
        for p in producers:
            assert consumer not in net.upstream(p), f"cycle: {p} -> {consumer}"


def test_unrolling_is_allowed_where_a_cycle_is_not():
    """The distinction §0's depth claim rests on. A rule unit's output never re-enters its own view, so it
    cannot iterate on its own — transitive closure gets its depth from a CHAIN OF INSTANCES. Forbid a unit
    from feeding a new instance of its own template and transitivity becomes inexpressible; allow it back
    into an EXISTING one and you have a cycle."""
    a, b, c, d = mint("a"), mint("b"), mint("c"), mint("d")
    net = Net()
    net.spawn(given("base", [Fact(a, "next", b), Fact(b, "next", c), Fact(c, "next", d)]))
    net.declare("T", (Triple(X, "next", Y),), Triple(X, "reaches", Y))
    net.declare("STEP", (Triple(X, "reaches", Y), Triple(Y, "next", Z)), Triple(X, "reaches", Z))
    net.run(Budget(limit=500))

    assert len(net.instances["STEP"]) > 1, "depth comes from repeated instantiation"
    reached = {(f.s.name, f.o.name) for _u, f in net.derived_anywhere("reaches")}
    assert ("a", "d") in reached


def test_projection_dedup_terminates_assembly():
    """Without it, a downstream unit re-spawns every upstream rule whose predicates it happens to be
    carrying, forever. Restricting the comparison to the predicates a template actually READS is what
    makes assembly stop — the propagation idempotence condition, one level up."""
    a, b, c = mint("a"), mint("b"), mint("c")
    net = Net()
    net.spawn(given("base", [Fact(a, "p", b), Fact(b, "q", c)]))
    net.declare("R1", (Triple(X, "p", Y), Triple(Y, "q", Z)), Triple(X, "r", Z))
    net.declare("R2", (Triple(X, "r", Y),), Triple(X, "s", Y))
    budget = net.run(Budget(limit=500))
    assert not budget.exhausted, "assembly must terminate on its own, not by running out of fuel"
    assert len(net.units) == 3, f"one instance per template, no churn: {sorted(net.units)}"


def test_the_only_global_structure_is_the_unit_index():
    """§1's falsifiable test. The index keys are PREDICATES — computation — never node or fact
    identities, and there is no registry of data anywhere in the package."""
    net = _world()
    net.declare("E", LHS, RHS)
    net.run(Budget(limit=200))
    keys = set(net.lhs_index) | set(net.rhs_index)
    # Since §22.5 the keys are ROLE NODES rather than strings — and the claim sharpens rather than
    # weakens: they must be roles the FORM SET supplies (L0), never ENTITY identities from the data.
    assert keys and all(FORMS.known(k.name) for k in keys)
    entities = ({f.s for u in net.units.values() for f in u.output}
                | {f.o for u in net.units.values() for f in u.output})
    assert not (keys & entities), "the index must never key on a datum"
    assert {k.name for k in keys} <= {"likes", "is", "admires"}
