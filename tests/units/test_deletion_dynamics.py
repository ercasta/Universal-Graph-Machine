"""What happens when a unit deletes its own power source?

`docs/units/revision-02-two-planes.md` §6. Deletion is the only effect that can subtract a unit's own
premise, so it is the only one that introduces a dynamic the other four cannot.

The prediction under test: *"if the unit deletes its power source, at the next turn it does not
revive."*
"""
from units.graph import EMPTY, named
from units.overlay import BASE, Identify, Retract, SetAttr
from units.turn import (ANY, BOUND, ENGINE, SILENCED, SURGE_AT, Machine, Unit,
                        bundled_silence_rule)


# -- the detector: a gate that keeps switching on and off ---------------------------------------

def test_a_surge_names_the_unit_and_the_gate():
    """A positive fact, not an absence to be noticed. It has to be matchable, because the correction is
    a bundled rule's job and the engine's involvement ends at reporting (§7)."""
    g, paul = named(EMPTY, "Paul", age=42)
    m = Machine(g, (Unit("selfeater", (paul, "age"), (Retract(paul, "age"),)),))

    (s,) = m.turn().surges
    assert s.unit == "selfeater"
    assert s.gate == (paul, "age")
    assert s.flips >= SURGE_AT


def test_one_flip_is_normal_and_does_not_surge():
    """A deletion landing and a downstream unit correctly losing its premise is a single present →
    absent transition, and it settles. Only a *repeated* flip means no fixpoint exists — which is why
    the threshold is on the count rather than on the first transition."""
    g, paul = named(EMPTY, "Paul", age=42)
    g, mary = named(g, "Mary", age=30)
    m = Machine(g, (
        Unit("deleter", (paul, "age"), (Retract(mary, "age"),)),
        Unit("downstream", (mary, "age"), (SetAttr(paul, "seen", True),)),
    ))

    r = m.turn()
    assert r.surges == () and r.ended() == "stable"
    assert r.fired == ("deleter",)


def test_the_detector_is_not_deletion_specific_identify_surges_too():
    """The monotonicity argument's second half. Mint, edge and attribute only ever make more readable,
    so a gate can only go absent → present; **`Identify` is non-monotone too**, because merging two
    nodes that disagree produces a conflict and a conflict reads as absent.

    Here that is self-undermining in exactly the way a self-deletion is, and the same local detector
    catches it — which is the evidence that a flipping gate is the general signal rather than a
    deletion-shaped special case."""
    g, paul = named(EMPTY, "Paul", age=42)
    g, other = named(g, "P.", age=43)
    m = Machine(g, (Unit("coref", (paul, "age"), (Identify(paul, other),)),))

    r = m.turn()
    assert r.surges and r.ended() == "out_of_fuel"
    assert r.surges[0].unit == "coref"


def test_there_is_no_global_quiescence_test():
    """`model.md` §2 — *no work-list running to quiescence, no output-unchanged termination test.* The
    detector must be local to a gate, so the machine may not keep a history of whole states to compare
    against. Structural, because this is the kind of thing that grows back."""
    import inspect

    import units.turn as turn
    src = inspect.getsource(turn.Machine.turn)
    assert "seen" not in src                     # no set of previously-visited global states
    assert "flips" in src and "was" in src       # per-gate presence, and nothing wider


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
    assert r.surges and r.ended() == "out_of_fuel"
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
    assert r.surges and r.ended() == "out_of_fuel"
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
    assert r.fired != ()                                 # it *had* concluded something…
    assert r.applied == ()                               # …and applied none of it
    assert r.effects == ()                               # …and reports no phase, for the same reason
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
    assert r.surges and r.ended() == "out_of_fuel"
    assert m.asserted.attr(paul, "age") == 42    # and the asserted layer is untouched


def test_the_oscillation_does_not_reach_the_asserted_layer_and_the_next_turn_is_identical():
    """No fixpoint means no write-back, so the world does not drift. The next turn re-runs from the same
    axioms and reaches the same non-conclusion — *recomputed, never maintained*, holding even when what
    is recomputed is a failure."""
    g, paul = world()
    m = Machine(g, (Unit("u", (paul, "age"), (Retract(paul, "age"),)),))

    first, second = m.turn(), m.turn()
    assert first.surges and second.surges
    assert first.ended() == second.ended() == "out_of_fuel"
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


# -- the correction: a rule, not the engine ------------------------------------------------------

def test_the_bundled_rule_silences_a_surged_unit_and_the_turn_completes():
    """**The engine reports; a rule decides.** The surge lands as a fact on the unit's own node, the
    bundled rule matches it, and silencing the output breaks the feedback — so the premise stays
    readable and the turn reaches a fixpoint instead of spinning to the budget.

    Note what the correction is: a **containment**, not a repair. Nothing was fixed; the turn was merely
    allowed to finish and report."""
    g, paul = named(EMPTY, "Paul", age=42)
    eater = Unit("selfeater", (paul, "age"), (Retract(paul, "age"),))
    m = Machine(g, (eater, bundled_silence_rule()))

    r = m.turn()
    assert r.ended() == "stable"                         # …where without the rule it runs out of fuel
    assert r.surges and r.surges[0].unit == "selfeater"  # the report is still made, and still loud
    assert m.view(r.effects).read(paul, "age").value == 42


def test_the_surge_is_a_fact_about_the_unit_and_that_needs_homoiconicity():
    """The surge is written **onto the unit's own node**, so it is matchable by an ordinary premise.

    This is the first place the design needs a unit to be plane-1 data for a reason other than
    tidiness: without a node for the unit there is nothing for the fact to be *about*, and the
    correction would have to be engine code (`revision-02` §§1, 5)."""
    g, paul = named(EMPTY, "Paul", age=42)
    eater = Unit("selfeater", (paul, "age"), (Retract(paul, "age"),))
    m = Machine(g, (eater,))

    r = m.turn()
    assert m.view(r.effects) is not None
    view = m.view([(s, e) for s, e in [(ENGINE, SetAttr(eater.node, "surged", "age"))]])
    assert view.read(eater.node, "surged").value == "age"
    assert view.read(eater.node, "surged").source == ENGINE      # the engine's only contribution


def test_without_the_bundled_rule_nothing_fixes_the_surge():
    """The composability claim, made falsifiable: **remove the rule and the behaviour changes.**

    If the engine silenced on its own, this would still end `stable` and the rule would be decoration.
    It ends at the budget instead, which is the honest outcome of *reported, unhandled*."""
    g, paul = named(EMPTY, "Paul", age=42)
    m = Machine(g, (Unit("selfeater", (paul, "age"), (Retract(paul, "age"),)),))

    r = m.turn()
    assert r.surges and r.ended() == "out_of_fuel"


def test_silencing_touches_no_wiring_and_no_asserted_data():
    """Invariant 17 — no engine code mutates wiring — and the reason silencing is the least invasive
    correction available. The unit is still standing, still wired, still has its premise; only its
    output stopped, and only for this turn."""
    g, paul = named(EMPTY, "Paul", age=42)
    eater = Unit("selfeater", (paul, "age"), (Retract(paul, "age"),))
    m = Machine(g, (eater, bundled_silence_rule()))
    before = list(m.units)

    r = m.turn()
    assert m.units == before                             # wiring untouched
    assert m.asserted.attr(paul, "age") == 42            # asserted layer untouched
    assert r.applied == ()
    assert eater in m.units                              # the unit still stands


def test_the_correction_is_an_ordinary_fact_not_a_new_effect_kind():
    """`model.md` invariant 4 already reserved this shape — *units **propose** wirings as facts* — and
    taking it literally means there is nothing new to add.

    A first attempt made `Silence` a sixth effect type. It failed immediately, because `Overlays` had
    never heard of it: a control decision is not a graph overlay. The fix was not to teach the overlay
    layer about it but to notice the effect was unnecessary — the rule concludes an ordinary attribute
    on the unit's node, and the machine reads it."""
    import units.turn as turn
    assert not hasattr(turn, "Silence")

    (effect,) = bundled_silence_rule().effects
    assert isinstance(effect, SetAttr) and effect.attr == SILENCED


def test_unit_nodes_share_the_graph_and_ordinary_rules_do_not_see_them():
    """Invariant 19, and `revision-02` §5's *no machinery partition*.

    Unit nodes live in the same graph as Paul — there is no separate universe — and an ordinary rule
    patterning `age` does not find them, for the ordinary reason that nothing matches implicitly
    (invariant 7). Nothing is hidden; it simply does not match."""
    g, paul = named(EMPTY, "Paul", age=42)
    watcher = Unit("watcher", (ANY, "age"), (SetAttr(BOUND, "noted", True),))
    m = Machine(g, (watcher,))

    assert watcher.node in m.asserted.nodes                  # same graph, no partition
    r = m.turn()
    noted = [n for n in m.view(r.effects).nodes()
             if m.view(r.effects).read(n, "noted") is not None]
    assert noted == [paul]                                   # the unit node was not swept up
