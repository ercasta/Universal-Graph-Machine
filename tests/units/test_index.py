"""THE COMPUTED INDEX (§28) and THE ASSEMBLER-COMPLETENESS SWEEP (§29).

Spikes: `bench/spike_computed_index.py` (37/37), `bench/spike_assembler_completeness.py` (27/27).

What is asserted here is what must not regress: the pruning, the SOUNDNESS of the pruning (three ways a
shape filter can silently drop a derivation), the validation gate against §27's journal — and then the
**four defects** the two probes found, every one of which was silent and three of which changed an answer.
"""
from __future__ import annotations

import pytest

from units import Budget, Fact, Net, Subgraph, Triple, Var, given, mint, role
from units import band as B
from units import index as IX
from units.match import Absent, Mint

X, Y, Z, P = Var("x"), Var("y"), Var("z"), Var("p")
IS_A = role("is_a")


@pytest.fixture
def voc():
    return mint("man"), mint("mortal"), mint("socrates")


# -- the primitive ---------------------------------------------------------------------------------

def test_a_fact_that_agrees_on_the_predicate_and_not_the_object_cannot_satisfy_the_atom(voc):
    """§24.7's dead wire, at the level where it is decided."""
    man, mortal, socrates = voc
    assert IX.can_satisfy(Fact(socrates, IS_A, man), Triple(X, "is_a", man))
    assert not IX.can_satisfy(Fact(socrates, IS_A, mortal), Triple(X, "is_a", man))


def test_a_variable_slot_accepts_anything_including_the_predicate(voc):
    man, mortal, socrates = voc
    assert IX.can_satisfy(Fact(socrates, IS_A, mortal), Triple(X, "is_a", Y))
    assert IX.can_satisfy(Fact(socrates, IS_A, mortal), Triple(X, P, Y))


def test_a_mint_head_cannot_feed_a_ground_body_slot_but_may_feed_a_variable_one(voc):
    """A minted node is FRESH (§23.1), so it can never be a node the form set supplied — a real bit of
    selectivity rather than bookkeeping."""
    man, _, _ = voc
    assert not IX.can_feed(Triple(X, "is_a", Mint("g")), Triple(X, "is_a", man))
    assert IX.can_feed(Triple(X, "is_a", Mint("g")), Triple(X, "is_a", Y))


# -- the static index ------------------------------------------------------------------------------

def test_the_static_index_is_a_pure_function_of_the_library(voc):
    man, mortal, socrates = voc
    net = Net()
    net.declare("MORTAL", (Triple(X, "is_a", man),), Triple(X, "is_a", mortal))
    net.declare("SHADE", (Triple(X, "is_a", mortal),), Triple(X, "is_a", role("shade")))
    ix = IX.ComputedIndex(net.library)
    assert "SHADE" in ix.feeds("MORTAL")
    assert "MORTAL" not in ix.feeds("MORTAL")            # the §24.7 spurious instance, refused statically
    assert not net.units                                # nothing was run to learn it


def test_a_wildcard_template_is_diagnosed_from_the_form_set_alone():
    """§19's actual payoff is a DIAGNOSIS, not a speedup: §22.5's wildcard — the coref-merge shape — is fed
    by everything, and the index says so before a unit exists."""
    ix = IX.ComputedIndex({
        "COREF": ((Triple(X, P, Y), Triple(X, "same_as", Z)), (Triple(Z, P, Y),)),
        "MORTAL": ((Triple(X, "is_a", mint("man")),), (Triple(X, "is_a", mint("mortal")),)),
    })
    assert ix.wildcards() == {"COREF"}
    assert "COREF" in ix.feeds("MORTAL") and "COREF" in ix.feeds("COREF")


def test_the_trace_reading_templates_get_no_static_restriction():
    """⚠ §26.2 hoped a trace consumer *"could be restricted statically to the units whose conclusions it
    actually grades"*. It cannot: the shape does not say which those are. Asserted so the hope is not
    re-raised as an oversight."""
    lhs, _ = B.inheritance_rule()
    assert IX.selectivity(lhs) == 0.0


# -- soundness: three ways a shape filter can silently drop a derivation ----------------------------

def test_a_naf_relevant_fact_is_feasible_even_though_it_can_never_justify_a_firing(voc):
    man, _, socrates = voc
    dead = mint("dead")
    lhs = (Triple(X, "is_a", man), Absent(Triple(X, "is_a", dead)))
    assert IX.feasible(Subgraph([Fact(socrates, IS_A, dead)]), lhs)
    assert not IX.feasible(Subgraph([Fact(socrates, IS_A, mint("elsewhere"))]), lhs)
    assert IX.spawn_need((Absent(Triple(X, "is_a", dead)),)) == frozenset()


def test_a_negated_premise_reaches_the_rule_and_suppresses_it(voc):
    """⭐⭐ A LIVE DEFECT, found by spiking the index (§28.1). A negated premise's predicate was in no need
    set, so its producer was never wired — and under SUBSET OUTPUT that means the NAF was evaluated against
    a value the fact never reached and the rule FIRED, concluding something FALSE, silently.

    Both atoms here carry the SAME predicate, which is what a predicate-level need could not express."""
    man, _, socrates = voc
    dead, walker = mint("dead"), mint("walker")
    net = Net()
    net.spawn(given("base", [Fact(socrates, IS_A, man)]))
    net.declare("DEATH", (Triple(X, "is_a", man),), Triple(X, "is_a", dead))
    net.declare("WALK", (Triple(X, "is_a", man), Absent(Triple(X, "is_a", dead))),
                Triple(X, "is_a", walker))
    net.run(Budget(600))
    assert not {f for _, f in net.derived_anywhere("is_a") if f.o == walker}
    assert any("DEATH" in p for p in net.producers["WALK#1"])
    assert len(net.instances["WALK"]) == 1               # never SPAWNED on the negative evidence


def test_two_independent_givens_are_two_worlds(voc):
    """⚠ Looks like the same case and is not. `base` and `morgue` share no lineage, so §3b's
    incomparability refuses to join them — which is the whole of §4's emergence claim. Joining worlds is
    what a MERGE unit is for, and there is none here."""
    man, _, socrates = voc
    dead, walker = mint("dead"), mint("walker")
    net = Net()
    net.spawn(given("base", [Fact(socrates, IS_A, man)]))
    net.spawn(given("morgue", [Fact(socrates, IS_A, dead)]))
    net.declare("WALK", (Triple(X, "is_a", man), Absent(Triple(X, "is_a", dead))),
                Triple(X, "is_a", walker))
    net.run(Budget(400))
    assert {f for _, f in net.derived_anywhere("is_a") if f.o == walker}


def test_a_given_is_described_by_no_template_and_still_feeds_one(voc):
    """The static index knows only templates, so it may not gate a wire — a `given`, `branch` or `carrier`
    would be cut off from every rule that reads it."""
    man, mortal, socrates = voc
    net = Net()
    net.spawn(given("base", [Fact(socrates, IS_A, man)]))
    net.declare("MORTAL", (Triple(X, "is_a", man),), Triple(X, "is_a", mortal))
    net.run(Budget(200))
    assert any(f.o == mortal for _, f in net.derived_anywhere("is_a"))
    assert "base" not in IX.ComputedIndex(net.library).templates


def test_a_variable_head_slot_may_feed_a_ground_body_slot():
    ix = IX.ComputedIndex({
        "ANY": ((Triple(X, "saw", Y),), (Triple(X, "is_a", Y),)),
        "MAN": ((Triple(X, "is_a", mint("man")),), (Triple(X, "is_a", mint("mortal")),)),
    })
    assert "MAN" in ix.feeds("ANY")


# -- the pruning, and the gate ---------------------------------------------------------------------

def _mortal_net(computed: bool) -> Net:
    man, mortal, socrates = mint("man"), mint("mortal"), mint("socrates")
    net = Net(computed_index=computed)
    net.spawn(given("base", [Fact(socrates, IS_A, man)]))
    net.declare("MORTAL", (Triple(X, "is_a", man),), Triple(X, "is_a", mortal))
    net.run(Budget(400))
    return net


def test_the_dead_instance_is_never_born_and_the_answer_is_unchanged():
    before, after = _mortal_net(False), _mortal_net(True)
    assert len(before.instances["MORTAL"]) == 2          # §24.7, reproduced
    assert len(after.instances["MORTAL"]) == 1
    assert ({f.p for _, f in before.derived_anywhere("is_a")}
            == {f.p for _, f in after.derived_anywhere("is_a")})


def test_the_audit_reports_both_directions_and_nothing_was_dropped():
    """§27.2's gate: what the index PROPOSED against what actually FIRED. The two directions are not
    symmetric — an idle wire is wasted work, a dropped derivation is silent and wrong."""
    man, mortal, socrates = mint("man"), mint("mortal"), mint("socrates")
    net = Net()
    net.spawn(given("base", [Fact(socrates, IS_A, man), Fact(mint("plato"), IS_A, man)]))
    net.declare("MORTAL", (Triple(X, "is_a", man),), Triple(X, "is_a", mortal))
    net.declare("SHADE", (Triple(X, "is_a", mortal),), Triple(X, "is_a", role("shade")))
    net.run(Budget(800))
    audit = net.index_audit()
    assert audit["unsound"] == []
    assert audit["wires"] and "idle_wires" in audit
    assert audit["wildcards"] == set()


def test_the_index_is_not_an_accumulation():
    net = _mortal_net(True)
    journal, units = net.journal, len(net.units)
    net.run(Budget(400))
    assert net.journal == journal and len(net.units) == units


def test_only_a_carrier_can_drop_so_an_ordinary_join_is_not_a_bypass(voc):
    """⚠ The second defect (§28.1). Under SUBSET OUTPUT every rule lacks all of its ancestor's facts, so
    `restores_a_drop` read every ordinary JOIN as a bypass — harmless while it was only a report, wrong the
    moment it became a wiring test. Only a CARRIER's omission is a deliberate drop."""
    man, _, socrates = voc
    dead = mint("dead")
    net = Net()
    net.spawn(given("base", [Fact(socrates, IS_A, man)]))
    net.declare("DEATH", (Triple(X, "is_a", man),), Triple(X, "is_a", dead))
    net.run(Budget(400))
    assert net.restores_a_drop("DEATH#1", extra="base") is None
    assert net.wellformed() == []


# -- §29: does the assembler DELIVER every kind of LHS? --------------------------------------------
# Sweep: `bench/spike_assembler_completeness.py` (27/27). §28.1 found the assembler silently delivering
# only half an LHS, and the consequence was a false conclusion — so the shapes it can be asked for are
# swept rather than assumed. These are the two further defects that sweep found.

def test_two_sibling_worlds_differing_only_under_negation_both_get_an_instance():
    """⭐⭐ §29.1, and it is §4's emergence claim failing in the one place it is supposed to hold. Two
    branches that differ only in a NAF-relevant fact PROJECT IDENTICALLY on the positive half, so the second
    was declined as *nothing new* — and the world where the answer is YES silently had no instance at all.

    The general lesson: **what may START a computation and what DISTINGUISHES two of them are different
    questions.** The trigger is positive; the projection is an IDENTITY and must span both polarities."""
    from units import branch
    a, b = mint("a"), mint("b")
    net = Net()
    net.spawn(given("base", [Fact(a, role("p1"), b)]))
    net.spawn(branch("H1", add=[Fact(a, role("block"), b)]))
    net.wire("base", "H1")
    net.spawn(branch("H2", add=[]))
    net.wire("base", "H2")
    net.declare("J", (Triple(X, "p1", Y), Absent(Triple(X, "block", Y))), Triple(X, "ok", Y))
    net.run(Budget(6000))
    assert len(net.instances["J"]) == 2
    fired = sorted(bool(net.units[i].last_derived) for i in net.instances["J"])
    assert fired == [False, True]                    # blocked world silent, open world derives


def test_a_template_with_no_ground_predicate_is_instantiated():
    """⚠ §29.2. The fork test was `not need` — *reads no ground OBJECT predicate* — which also describes an
    ALL-VARIABLE template, so it went to the TRACE fork, matched nothing there and never ran at all. The
    right test is the positive one: does this template read ONLY firing predicates?"""
    a, b = mint("a"), mint("b")
    net = Net()
    net.spawn(given("base", [Fact(a, role("roars"), b)]))
    net.declare("W", (Triple(X, P, Y),), Triple(Y, P, X))
    budget = net.run(Budget(6000))
    assert net.instances["W"]
    assert {f for _, f in net.derived_anywhere("roars")}
    assert budget.spent < 20                          # and it terminates
    assert "W" in IX.ComputedIndex(net.library).wildcards()   # paying §22.5's price, honestly


def test_a_negated_premise_derived_two_hops_away_is_still_wired(voc):
    """§28.1's regression at depth: the producer arrives several passes after the instance was spawned."""
    man, _, socrates = voc
    doomed, dead, walker = mint("doomed"), mint("dead"), mint("walker")
    net = Net()
    net.spawn(given("base", [Fact(socrates, IS_A, man)]))
    net.declare("D1", (Triple(X, "is_a", man),), Triple(X, "is_a", doomed))
    net.declare("D2", (Triple(X, "is_a", doomed),), Triple(X, "is_a", dead))
    net.declare("WALK", (Triple(X, "is_a", man), Absent(Triple(X, "is_a", dead))),
                Triple(X, "is_a", walker))
    net.run(Budget(6000))
    assert not {f for _, f in net.derived_anywhere("is_a") if f.o == walker}
    assert any("D2" in p for p in net.producers["WALK#1"])


def test_a_join_of_n_premises_each_arriving_on_a_later_pass():
    a, b = mint("a"), mint("b")
    for k in (2, 3, 4):
        net = Net()
        net.spawn(given("base", [Fact(a, role("p0"), b)]))
        for i in range(k - 1):
            net.declare(f"H{i}", (Triple(X, f"p{i}", Y),), Triple(X, f"p{i + 1}", Y))
        net.declare("J", tuple(Triple(X, f"p{i}", Y) for i in range(k)), Triple(X, "all", Y))
        net.run(Budget(20000))
        assert {f for _, f in net.derived_anywhere("all")}, f"k={k}"


def test_a_branch_that_removes_the_premise_starves_its_own_world_and_is_not_bypassed():
    from units import branch
    a, b = mint("a"), mint("b")
    net = Net()
    net.spawn(given("base", [Fact(a, role("p1"), b)]))
    net.spawn(branch("H", remove=[Fact(a, role("p1"), b)]))
    net.wire("base", "H")
    net.declare("R", (Triple(X, "p1", Y),), Triple(X, "q", Y))
    net.run(Budget(3000))
    assert len(net.instances["R"]) == 1
    assert sorted(net.producers["R#1"]) == ["base"]
