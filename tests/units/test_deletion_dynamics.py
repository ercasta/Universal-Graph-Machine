"""What happens when a unit deletes its own power source?

`docs/units/revision-02-two-planes.md` §6. Deletion is the only effect that can subtract a unit's own
premise, so it is the only one that introduces a dynamic the other four cannot.

The prediction under test: *"if the unit deletes its power source, at the next turn it does not
revive."*
"""
from units.graph import EMPTY, named
from units.overlay import BASE, Retract, SetAttr
from units.turn import Machine, Unit


def world():
    g, paul = named(EMPTY, "Paul", age=42)
    return g, paul


# -- the control: deleting something else ------------------------------------------------------

def test_deleting_someone_elses_fact_is_stable():
    """The baseline. A computation unit whose premise is untouched by its own effect reaches a fixpoint
    and produces the same thing every turn."""
    g, paul = named(EMPTY, "Paul", age=42)
    g, mary = named(g, "Mary", age=30)
    m = Machine(g, (Unit("u", (paul, "age"), (Retract(mary, "age"),)),))

    for _ in range(3):
        r = m.turn()
        assert r.ended() == "stable" and r.fired == ("u",)
        assert m.view(r.effects).read(mary, "age") is None
        assert m.view(r.effects).read(paul, "age").value == 42
        # …and a computation unit's deletion NEVER reaches the asserted layer. It hides while powered;
        # it does not remove. Every turn re-hides it from scratch (`revision-01` §2).
        assert r.applied == ()
        assert m.asserted.attr(mary, "age") == 30


def test_an_oscillating_turn_writes_nothing_back():
    """No fixpoint, no write-back. A turn that could not settle must not leave a durable trace, or an
    unstable configuration would edit the world a little on every attempt.

    The oscillation is supplied by a self-deleting *computation* unit; the mutating rule downstream of
    it is the one that would write, and must not."""
    g, paul = named(EMPTY, "Paul", age=42)
    g, mary = named(g, "Mary", age=30)
    m = Machine(g, (
        Unit("flapper", (paul, "age"), (Retract(paul, "age"),)),
        Unit("writer", (paul, "age"), (Retract(mary, "age"),), mutating=True),
    ))

    r = m.turn()
    assert r.ended() == "oscillating"
    assert r.applied == ()
    assert r.effects == ()                               # no phase is *the* answer; none is reported
    assert m.asserted.attr(mary, "age") == 30            # the world is untouched
    assert m.asserted.attr(paul, "age") == 42


def test_an_oscillating_turn_reports_no_phase_even_when_a_phase_is_nonempty():
    """The stronger form of the previous test.

    A self-deleting unit alongside one that always fires: the cycle's two phases are *both* non-empty,
    so the detector stops on a state with conclusions in it — and reporting them would mean the turn's
    output depends on where the scan happened to begin.

    Worth a test of its own because the simpler oscillation always halts on the empty phase, so it
    cannot tell a principled answer from a lucky one.

    (A first attempt built the cycle out of two units deleting each other's premises. It **converged** —
    deletions only ever subtract, so one unit falling silent is a self-consistent state. Self-deletion
    is the only genuine 2-cycle available, which is the point of §6's remark that deletion is the only
    effect able to undermine its own support.)"""
    g, paul = named(EMPTY, "Paul", age=42)
    g, mary = named(g, "Mary", age=30)
    g, zoe = named(g, "Zoe", age=7)
    m = Machine(g, (
        Unit("steady", (mary, "age"), (Retract(zoe, "age"),)),        # premise never touched
        Unit("selfeater", (paul, "age"), (Retract(paul, "age"),)),    # deletes its own premise
    ))

    r = m.turn()
    assert r.ended() == "oscillating"
    assert r.effects == ()                               # …though the phase it halted on was not empty
    assert m.view().read(zoe, "age").value == 7          # nothing from either phase leaked out
    assert m.asserted.attr(paul, "age") == 42


def test_a_truncated_turn_writes_nothing_back():
    """`model.md` §9 — *write-back happens after stabilization, never during.* A turn cut short by the
    budget has conclusions in hand and must still apply none of them, or an under-resourced turn would
    edit the world on the strength of a partial computation."""
    g, paul = named(EMPTY, "Paul", age=42)
    g, mary = named(g, "Mary", age=30)
    m = Machine(g, (Unit("writer", (paul, "age"), (Retract(mary, "age"),), mutating=True),))

    r = m.turn(fuel=1)
    assert r.ended() == "out_of_fuel"
    assert r.effects != ()                               # it *had* concluded something…
    assert r.applied == ()                               # …and applied none of it
    assert m.asserted.attr(mary, "age") == 30


# -- the case in question ----------------------------------------------------------------------

def test_a_computation_unit_that_deletes_its_own_premise_OSCILLATES():
    """**The prediction is wrong for a computation unit, and the failure is loud rather than quiet.**

    Reading through the overlays is what does it. Fire → the premise is deleted → the premise is no
    longer readable → the unit does not fire → the deletion is not produced → the premise is readable
    again. There is no fixpoint, and the turn says so.

    This is the right outcome, not a defect: it is `model.md` §8's discipline holding under a case that
    genuinely has no answer. Compare a design that propagates once and stops — it would report a stable
    state that is an artifact of evaluation order."""
    g, paul = world()
    m = Machine(g, (Unit("u", (paul, "age"), (Retract(paul, "age"),)),))

    r = m.turn()
    assert r.ended() == "oscillating"
    assert len(r.oscillating) == 2               # fires / does not fire
    assert m.asserted.attr(paul, "age") == 42    # and the asserted layer is untouched


def test_the_oscillation_does_not_reach_the_asserted_layer_and_the_next_turn_is_identical():
    """No fixpoint means no write-back, so the world does not drift. The next turn re-runs from the same
    axioms and reaches the same non-conclusion — *recomputed, never maintained*, holding even when what
    is recomputed is a failure."""
    g, paul = world()
    m = Machine(g, (Unit("u", (paul, "age"), (Retract(paul, "age"),)),))

    first, second = m.turn(), m.turn()
    assert first.ended() == second.ended() == "oscillating"
    assert m.asserted.attr(paul, "age") == 42


def test_a_MUTATING_rule_that_deletes_its_own_premise_does_not_revive():
    """**The prediction is exactly right for a mutating rule** — and the two dispositions are the whole
    of the difference.

    Turn 1: the rule fires and its deletion is applied to the asserted layer at write-back. Turn 2:
    there is no premise to fire from, so it does not fire, and *nothing was retracted to make that
    true*. The unit is still standing and still wired; it simply is not powered (`revision-01` §3).

    Note it does **not** oscillate, and the reason is the write-back boundary: within the turn the
    deletion is a proposal on a wire and the premise stays readable, so the fixpoint is reached before
    anything is applied. `model.md` §9's *"a deletion is invisible within its own step"* is what makes
    the self-undermining case terminate."""
    g, paul = world()
    m = Machine(g, (Unit("u", (paul, "age"), (Retract(paul, "age"),), mutating=True),))

    first = m.turn()
    assert first.ended() == "stable" and first.fired == ("u",)
    assert len(first.applied) == 1
    assert m.asserted.attr(paul, "age") is None          # gone from the world

    second = m.turn()
    assert second.ended() == "stable"
    assert second.fired == ()                            # not powered, nothing retracted
    assert second.effects == ()


def test_readability_and_power_are_not_the_same_thing():
    """The distinction the oscillation is really about.

    A downstream unit reads through the overlays and so sees the deletion. Whether the *deleting* unit
    keeps firing is a question about power, and power comes from what is readable at the moment it is
    asked — which is why the self-deleting case has no answer while this one is fine."""
    g, paul = named(EMPTY, "Paul", age=42)
    g, mary = named(g, "Mary", age=30)
    m = Machine(g, (
        Unit("deleter", (paul, "age"), (Retract(mary, "age"),)),
        Unit("downstream", (mary, "age"), (SetAttr(paul, "seen", True),)),
    ))

    r = m.turn()
    assert r.ended() == "stable"
    assert r.fired == ("deleter",)                       # downstream lost its premise
    assert m.view(r.effects).read(paul, "seen") is None


def test_a_mutating_deletion_starves_a_downstream_unit_permanently():
    """The two dispositions again, one hop further out: a real deletion removes a downstream unit's
    premise for good, and no invalidation ran to make that happen."""
    g, paul = named(EMPTY, "Paul", age=42)
    m = Machine(g, (
        Unit("cleanup", (paul, "age"), (Retract(paul, "age"),), mutating=True),
        Unit("consumer", (paul, "age"), (SetAttr(paul, "noted", True),)),
    ))

    first = m.turn()
    assert set(first.fired) == {"cleanup", "consumer"}   # both fire: the deletion is not yet applied
    assert m.view(first.effects).read(paul, "noted").value is True

    second = m.turn()
    assert second.fired == ()
    assert m.view(second.effects).read(paul, "noted") is None
