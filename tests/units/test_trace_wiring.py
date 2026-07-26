"""TRACE-WIRE ASSEMBLY — `docs/design/substrate_inversion.md` §26.

Promoted from `bench/spike_trace_wiring.py` (23/23). §25.3 made degree inheritance expressible as a rule;
the remaining half was that `Net.assemble` did not know about trace wires, so such a unit had to be
hand-wired — and §23.4 established `explain`-as-units hits the same wall. **One blocker, two seams.**

The last test is the one the design did not predict correctly: §17.G said stratification *"must be
designed in, not discovered"*, and it was discovered.
"""
from __future__ import annotations

from units import Budget, Fact, Net, Subgraph, Triple, Var, band as B, given, mint, reify as R
from units import trace as T
from units.match import Absent

X, Y = Var("x"), Var("y")
F, C, P = Var("f"), Var("c"), Var("pc")


def _graded_net():
    d, h = mint("danger"), mint("high")
    n = Net()
    src = n.spawn(given("src", []))
    src.adds = B.grade(Subgraph([Fact(d, "is_a", h)]), Fact(d, "is_a", h), B.LIKELY)
    n.declare("R", (Triple(X, "is_a", h),), Triple(X, "needs", h))
    return n, d, h


def test_a_trace_consuming_template_assembles_itself():
    """⭐ The win. A mixed template — `<band>` from the object wire, `<from>` from the trace — spawns on
    its object half and completes on its trace half, and the conclusion inherits its premise's band with
    no Python in the loop."""
    n, d, h = _graded_net()
    n.declare("INHERIT", *B.inheritance_rule())
    bud = n.run(Budget(5000))
    assert n.instances["INHERIT"]
    assert any(n.trace_producers.get(i) for i in n.instances["INHERIT"]), "the ASSEMBLER wired the trace"
    target = Fact(R.handle_key(Fact(d, "needs", h)), B.BAND, B.LIKELY)
    assert any(target in u.output for u in n.units.values())
    assert not bud.exhausted


def test_an_explanation_hop_assembles_too():
    """The second seam. §23.4's replacement for the Python `explain` walk is an ordinary unit, and it is
    now wired by the assembler rather than by hand."""
    a, b = mint("a"), mint("b")
    n = Net()
    n.spawn(given("g", [Fact(a, "p", b)]))
    n.declare("R", (Triple(X, "p", Y),), Triple(X, "r", Y))
    n.declare("HOP", (Triple(F, T.CONCLUDED, C), Triple(F, T.FROM, P)), Triple(C, "<because>", P))
    n.run(Budget(2000))
    assert any(any(f.p.name == "<because>" for f in u.output) for u in n.units.values())


def test_the_no_accretion_rule_becomes_conditional_and_stays_enforced():
    """§16.6 said the trace must NEVER accrete into the object value. It becomes: **never, unless the unit
    asked** — a unit whose LHS names a firing predicate has asked, and refusing would make metareasoning
    unsayable. What contains it is SUBSET OUTPUT: such a unit emits only what it derived."""
    n, d, h = _graded_net()
    n.declare("INHERIT", *B.inheritance_rule())
    n.run(Budget(5000))
    inh = n.units[n.instances["INHERIT"][0]]
    assert not (n.units["R#1"].view().predicates() & T.FIRING_PREDICATES), "an ordinary unit sees none"
    assert inh.view().predicates() & T.FIRING_PREDICATES, "the one that asked does"
    assert not (inh.output.predicates() & T.FIRING_PREDICATES), "and it emits none — subset output"
    assert n.trace_leaks() == []


def test_exact_naf_is_unaffected_for_units_that_did_not_ask():
    """§6a's guarantee has to survive the concession above, or the whole point of §20's two wires is lost."""
    n, d, h = _graded_net()
    n.declare("SAFE", (Triple(X, "is_a", h), Absent(Triple(X, "blocked", h))), Triple(X, "safe", h))
    n.declare("INHERIT", *B.inheritance_rule())
    n.run(Budget(5000))
    safe = n.units[n.instances["SAFE"][0]]
    assert any(f.p.name == "safe" for f in safe.output)
    assert not (safe.view().predicates() & T.FIRING_PREDICATES)


def test_trace_wires_are_covered_by_the_cycle_guard_and_the_fixpoint():
    n, d, h = _graded_net()
    n.declare("INHERIT", *B.inheritance_rule())
    n.run(Budget(5000))
    assert n.wellformed() == []
    before = {u.name: (u.output, u.trace_output) for u in n.units.values()}
    n.run(Budget(5000))
    assert all(before[u.name] == (u.output, u.trace_output) for u in n.units.values())


def test_a_pure_trace_template_needs_stratification_to_terminate():
    """⚠ §26.1, and it had to be DISCOVERED. A template reading ONLY firing predicates has an empty object
    need, so it spawns on its trace half — and then: every unit has a trace, a trace consumer IS a unit,
    so consumers feed consumers forever. Firing nodes are MINTED, so the projection never repeats and
    §15.1(c)'s dedup never fires. **Measured before the guard: 57 instances, fuel exhausted.**

    The guard is one local test — *a unit that reads the trace is never wired to the trace of a unit that
    reads the trace*. Level 0 is the world, level 1 is about level 0, and level 2 needs a deliberate act
    that does not exist.

    ⭐ §17.G predicted exactly this (*"firing on stability DESTABILISES… requires stratification, and must
    be designed in, not discovered"*). It was discovered anyway."""
    a, b = mint("a"), mint("b")
    n = Net()
    n.spawn(given("g", [Fact(a, "p", b)]))
    n.declare("R", (Triple(X, "p", Y),), Triple(X, "r", Y))
    n.declare("HOP", (Triple(F, T.CONCLUDED, C), Triple(F, T.FROM, P)), Triple(C, "<because>", P))
    bud = n.run(Budget(500))
    assert not bud.exhausted
    assert len(n.instances["HOP"]) <= 3
    assert all(not n.reads_trace(pr) for ps in n.trace_producers.values() for pr in ps)
