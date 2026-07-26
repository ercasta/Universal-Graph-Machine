"""CLOSURE — the system's output becoming computation (`substrate_inversion.md` §24.7).

Promoted from `bench/spike_closure.py` (26/26). The user's question decided an architecture:

> *"The OUTPUT of the system should be usable to create more network wirings... so either we convert
> subgraphs to CNL and ingest it back, or we also need a transpiler from output graph to network."*

**The CNL round-trip is unsound here**, not merely slow: text names nodes, and re-ingesting names means
resolving them — §22.5's forbidden interning and §24.3's *reference is not lookup*. So the loop goes
graph→structure directly, and that path is **the only transpiler**: the CNL front-end's job is to produce
the same subgraph a unit produces.
"""
from __future__ import annotations

import pytest

from units import Budget, Fact, Net, Subgraph, Triple, Var, authoring as A, given, mint, role
from units.match import Absent, Mint

X, Y = Var("x"), Var("y")


def test_a_rule_round_trips_through_a_value():
    man, mortal = mint("man"), mint("mortal")
    enc = A.encode("MORTAL", (Triple(X, "is_a", man),), (Triple(X, "is_a", mortal),))
    name, lhs, rhs = A.rules_in(enc)[0]
    assert (name, lhs, rhs) == ("MORTAL", (Triple(X, "is_a", man),), (Triple(X, "is_a", mortal),))


def test_negation_and_minting_survive_the_encoding():
    man, mortal = mint("man"), mint("mortal")
    enc = A.encode("N", (Triple(X, "is_a", man), Absent(Triple(X, "is_a", mortal))),
                   (Triple(X, "h", Mint("g")),))
    _, lhs, rhs = A.rules_in(enc)[0]
    assert isinstance(lhs[1], Absent) and isinstance(rhs[0].o, Mint)


def test_the_encoding_reuses_reifys_vocabulary():
    """A pattern atom is described exactly as a FACT is — [[learning-arc]]'s *"only the FLAT reification
    is learner-writable"*, arriving as a consequence rather than a design."""
    enc = A.encode("R", (Triple(X, "p", Y),), (Triple(X, "q", Y),))
    assert any(f.p == role("<of_s>") for f in enc)


def test_a_value_declares_a_template_and_the_network_runs_it():
    man, mortal, socrates = mint("man"), mint("mortal"), mint("socrates")
    enc = A.encode("MORTAL", (Triple(X, "is_a", man),), (Triple(X, "is_a", mortal),))
    net = Net()
    net.spawn(given("base", [Fact(socrates, "is_a", man)]))
    assert A.declare_all(net, enc) == ["MORTAL"]
    net.run(Budget(300))
    assert Fact(socrates, "is_a", mortal) in net.units[net.instances["MORTAL"][0]].output


def test_declaring_the_same_rule_twice_adds_nothing():
    """[[extend-equals-rebuild]]: saying the same thing twice must not double the network."""
    man, mortal, socrates = mint("man"), mint("mortal"), mint("socrates")
    enc = A.encode("MORTAL", (Triple(X, "is_a", man),), (Triple(X, "is_a", mortal),))
    net = Net()
    net.spawn(given("base", [Fact(socrates, "is_a", man)]))
    A.declare_all(net, enc)
    net.run(Budget(300))
    before = (len(net.library), len(net.units))
    A.declare_all(net, enc)
    A.declare_all(net, enc)
    net.run(Budget(300))
    assert (len(net.library), len(net.units)) == before


# -- ⭐ the two that matter -----------------------------------------------------------------------------

def test_the_systems_own_output_becomes_computation():
    """⭐ CLOSURE. A unit emits a rule-shaped value; the bridge declares it; the assembler wires it; and
    the network derives a conclusion **no authored template could produce**."""
    kind, risky, lion, dangerous = mint("kind"), mint("risky"), mint("lion"), mint("dangerous")
    net = Net()
    net.spawn(given("facts", [Fact(lion, "is_a", kind), Fact(lion, "is_a", risky)]))
    author = net.spawn(given("author", A.encode("LEARNED", (Triple(X, "is_a", risky),),
                                                (Triple(X, "is_a", dangerous),),
                                                key=mint("learned_rule"))))
    net.run(Budget(300))
    assert not any(Fact(lion, "is_a", dangerous) in u.output for u in net.units.values())

    assert A.declare_all(net, author.output) == ["LEARNED"]
    net.run(Budget(400))
    assert any(Fact(lion, "is_a", dangerous) in u.output for u in net.units.values())


def test_the_bridge_adds_shapes_and_never_wires():
    """⭐ §8's line, and §16.6's wording is the test: *the discourse adds SHAPES, not wiring policy*.
    The bridge declares templates; §3b's spawn policy still decides who feeds them. Asserted two ways —
    behaviourally, and by the absence of any wiring call in the module."""
    import pathlib
    risky, lion, dangerous = mint("risky"), mint("lion"), mint("dangerous")
    net = Net()
    net.spawn(given("facts", [Fact(lion, "is_a", risky)]))
    author = net.spawn(given("author", A.encode("L", (Triple(X, "is_a", risky),),
                                                (Triple(X, "is_a", dangerous),), key=mint("k"))))
    A.declare_all(net, author.output)
    net.run(Budget(400))
    wires = sum(len(v) for v in net.producers.values())
    A.declare_all(net, author.output)
    assert sum(len(v) for v in net.producers.values()) == wires
    assert all(net.units[i].in_degree >= 1 for i in net.instances["L"]), "the ASSEMBLER wired it"

    src = pathlib.Path(A.__file__).read_text(encoding="utf-8")
    assert ".wire(" not in src, "nothing in `authoring` may wire"


# -- ⚠ the limits -------------------------------------------------------------------------------------

def test_a_derived_rule_must_be_keyed_or_it_never_settles():
    """⚠ §22.8's standing rule reaching a THIRD construct, after the trace's firing nodes and the band's
    handles: **anything minted per run must be keyed.** A rule is minted structure."""
    k = mint("r")
    assert A.encode("R", (Triple(X, "p", Y),), (Triple(X, "q", Y),), key=k) == \
        A.encode("R", (Triple(X, "p", Y),), (Triple(X, "q", Y),), key=k)
    assert A.encode("R", (Triple(X, "p", Y),), (Triple(X, "q", Y),)) != \
        A.encode("R", (Triple(X, "p", Y),), (Triple(X, "q", Y),))


def test_two_rules_using_the_same_variable_name_do_not_collide():
    """Variable scoping is structural: `?x` in rule A and `?x` in rule B are different nodes."""
    a = A.encode("A", (Triple(X, "p", Y),), (Triple(X, "q", Y),))
    b = A.encode("B", (Triple(X, "r", Y),), (Triple(X, "s", Y),))
    va = {f.s for f in a if f.p == A.IS_A and f.o == A.VAR}
    vb = {f.s for f in b if f.p == A.IS_A and f.o == A.VAR}
    assert va and vb and not (va & vb)


def test_a_malformed_rule_is_refused_not_guessed_at():
    """[[epistemic-closure-under-composition]]: reasoned ∪ refused, never silently mis-mapped. A bridge
    that guesses is how [[book-corpus-experiment]]'s optimistic bias gets in."""
    r = mint("bad")
    with pytest.raises(A.NotARule):
        A.rules_in(Subgraph([Fact(r, A.IS_A, A.RULE)]))              # no head

    r2, a2 = mint("bad2"), mint("atom")
    with pytest.raises(A.NotARule):
        A.rules_in(Subgraph([Fact(r2, A.IS_A, A.RULE), Fact(r2, A.RHS, a2),
                             Fact(a2, role("<of_s>"), r2)]))         # half-described atom


def test_the_index_keys_on_the_predicate_alone_and_spawns_a_dead_instance():
    """⚠ §10.5 arriving concretely. `MORTAL#1` emits `socrates is_a mortal`; the index keys on the
    PREDICATE only; `is_a` is what the template reads — so the assembler unrolls onto a conclusion whose
    object the LHS requires to be something else. The instance writes nothing, which is the documented
    *woke and correctly wrote nothing* case, so nothing is WRONG — it is a dead unit and a wasted round.

    ⭐ **And it is the argument for §19's COMPUTED index**: the form already says this LHS needs
    object=`man`, so a static index could have refused the wire before spawning anything."""
    man, mortal, socrates = mint("man"), mint("mortal"), mint("socrates")
    enc = A.encode("MORTAL", (Triple(X, "is_a", man),), (Triple(X, "is_a", mortal),))
    net = Net()
    net.spawn(given("base", [Fact(socrates, "is_a", man)]))
    A.declare_all(net, enc)
    net.run(Budget(300))
    dead = [i for i in net.instances["MORTAL"] if not net.units[i].output]
    assert len(dead) == 1
