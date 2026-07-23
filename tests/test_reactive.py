"""The reactive DERIVE gate (STEP B of the reactive-core arc, docs/design/reactive_core.md).

A predicate DECLARED reactive proactively materializes its consequence at the next committed ask when its
trigger has landed — the DATA drives it — while undeclared predicates stay pull-only (lazy). The gate rides
`reconsider`'s standing work-list (DIRTY_REG -> _affected), fires demand-gated, and is sound by construction
(presence-triggered, monotone). These tests drive END-TO-END through `ask_goal`'s commit gate, so the wiring
(react before reconsider, shared dirty set) is exercised, not just the unit.
"""
from __future__ import annotations

from ugm import AttrGraph
from ugm.machine import Machine
from ugm.lowering import assemble_facts
from ugm.cnl.machine_rules import load_machine_rules
from ugm.cnl.query import ask_goal
from ugm.reconsider import mark_dirty
from ugm.reactive import declare_reactive, react
from ugm.chain import _facts_matching

RULE = "?x endangers ?y when ?x hunts ?y"       # a positive binary-relation rule (no copula ambiguity)


def _kb(trigger=("wolf", "hunts", "sheep")):
    kb = AttrGraph()
    rules = load_machine_rules(RULE)
    Machine().run(kb, assemble_facts([trigger]))
    mark_dirty(kb, [(trigger[1], trigger[2])])       # what intake records when a fact lands
    return kb, rules


def _materialized(kb, pred, s, o) -> bool:
    """A DIRECT read of PRESENT facts — no derivation. Did the consequence get materialized proactively?"""
    return bool(_facts_matching(kb, pred, s, o))


def test_reactive_predicate_materializes_on_a_committed_ask():
    # `endangers` declared reactive: a committed ask (about anything) fires the gate, so the consequence
    # of the landed trigger is materialized WITHOUT a query for it — the data drove it.
    kb, rules = _kb()
    declare_reactive(kb, "endangers")
    assert not _materialized(kb, "endangers", "wolf", "sheep")     # not there before the act
    ask_goal(kb, ("yesno", "wolf", "hunts", "sheep"), rules)       # a committed act on an unrelated goal
    assert _materialized(kb, "endangers", "wolf", "sheep")         # proactively derived at the gate


def test_a_non_reactive_predicate_stays_lazy():
    # Without the declaration the consequence is NOT materialized proactively — but is still derivable ON
    # DEMAND (laziness preserved, not lost).
    kb, rules = _kb()
    ask_goal(kb, ("yesno", "wolf", "hunts", "sheep"), rules)       # committed act, nothing reactive
    assert not _materialized(kb, "endangers", "wolf", "sheep")     # stayed pull-only
    assert ask_goal(kb, ("yesno", "wolf", "endangers", "sheep"), rules) == ["yes"]   # demand derives it


def test_reactive_firing_is_demand_gated_not_eager():
    # The reaction fires at the COMMITTED ASK, not at ingestion time: before any ask, nothing is
    # materialized even though the trigger and the declaration are both present.
    kb, rules = _kb()
    declare_reactive(kb, "endangers")
    assert not _materialized(kb, "endangers", "wolf", "sheep")     # no act yet -> no push
    ask_goal(kb, ("yesno", "wolf", "hunts", "sheep"), rules)
    assert _materialized(kb, "endangers", "wolf", "sheep")


def test_reactive_firing_does_not_re_fire_after_the_dirty_set_is_consumed():
    # Idempotence: after the first committed act (react derives, reconsider detaches the dirty set), a
    # second act finds nothing dirty -> react is zero-cost, and the fact stays materialized (monotone).
    kb, rules = _kb()
    declare_reactive(kb, "endangers")
    ask_goal(kb, ("yesno", "wolf", "hunts", "sheep"), rules)
    assert react(kb, rules) == 0                                   # dirty consumed -> nothing to fire
    assert _materialized(kb, "endangers", "wolf", "sheep")         # still there (monotone)


def test_a_reactive_cycle_drains_rather_than_loops():
    # The recall-autofire re-break, cycle form: two MUTUALLY reactive rules (p<->q). Presence-triggering +
    # monotone materialization mean the reaction cannot re-enqueue an absence -> the cycle DRAINS (both
    # facts settle) instead of self-reinforcing into a loop. The ask returns (does not hang).
    kb = AttrGraph()
    rules = load_machine_rules("?x q ?y when ?x p ?y") + load_machine_rules("?x p ?y when ?x q ?y")
    Machine().run(kb, assemble_facts([("a", "p", "b")]))
    mark_dirty(kb, [("p", "b")])
    declare_reactive(kb, "p")
    declare_reactive(kb, "q")
    ask_goal(kb, ("yesno", "a", "p", "b"), rules)                  # must terminate
    assert _materialized(kb, "q", "a", "b")                        # the cycle derived q and settled
    assert _materialized(kb, "p", "a", "b")
