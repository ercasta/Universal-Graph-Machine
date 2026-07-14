"""
Firmware STANCE as declared data (`ugm/policy.py`) — the CWA/OWA default and the on-cycle behaviour
are now a swappable `FirmwarePolicy`, not forked Python. Also the `merge_tools` collision-safe registry
composition (the tool extension point). See `docs/architecture.md` + the engine developer guide.
"""
import pytest

from ugm import (
    AttrGraph, Pat, Rule, write_rule, check, FirmwarePolicy, DEFAULT_POLICY, merge_tools,
)
from ugm.check import POSITIVE, ASSUMED_NO, UNKNOWN
from ugm.cnl.authoring import load_rules


def _rg(rules):
    rg = AttrGraph()
    for r in rules:
        write_rule(rg, r)
    return rg


# --- negation_default: how CHECK reads an unprovable goal's absence ------------------------------

def test_closed_default_reads_absence_as_assumed_no():
    g, rg = AttrGraph(), _rg([])                        # empty KB: `bob is happy` is underivable
    assert check(g, ("is", "bob", "happy"), rules=rg) == ASSUMED_NO           # the shipped stance (CWA)


def test_open_default_reads_absence_as_unknown():
    g, rg = AttrGraph(), _rg([])
    owa = FirmwarePolicy(negation_default="open")
    assert check(g, ("is", "bob", "happy"), policy=owa, rules=rg) == UNKNOWN  # flipped firmware stance


def test_open_default_with_closed_exception():
    g, rg = AttrGraph(), _rg([])
    owa = FirmwarePolicy(negation_default="open", closed_preds=frozenset({"happy"}))
    # `happy` is a CWA exception under the open default -> a decided assumed-no again
    assert check(g, ("is", "bob", "happy"), policy=owa, rules=rg) == ASSUMED_NO


def test_open_preds_kwarg_still_folds_into_the_closed_default():
    g, rg = AttrGraph(), _rg([])                        # back-compat: the legacy kwarg == closed + exc
    assert check(g, ("is", "bob", "happy"), open_preds=frozenset({"happy"}), rules=rg) == UNKNOWN


def test_positive_goal_is_stance_independent():
    g = AttrGraph()
    bob = g.add_node("bob")
    g.add_relation(bob, "is", g.add_node("happy"))
    rg = _rg([])
    for pol in (DEFAULT_POLICY, FirmwarePolicy(negation_default="open")):
        assert check(g, ("is", "bob", "happy"), policy=pol, rules=rg) == POSITIVE


# --- on_cycle: a loader's behaviour on a non-stratifiable bank ------------------------------------

_CYCLE = "?x foo ?y when not ?x bar ?y\n?x bar ?y when not ?x foo ?y\n"   # p:-¬q, q:-¬p


def test_on_cycle_raise_is_the_default():
    with pytest.raises(ValueError):
        load_rules(_CYCLE)                              # shipped stance rejects a negation cycle at load


def test_on_cycle_degrade_defers_to_the_forward_path():
    # the degrade stance skips the load-time raise (run_rules drops the NAF rules instead)
    rules = load_rules(_CYCLE, policy=FirmwarePolicy(on_cycle="degrade"))
    assert rules                                        # loaded without raising


# --- merge_tools: collision-safe tool registry composition ---------------------------------------

def test_merge_tools_composes_disjoint_registries():
    a = {"x": lambda g, c: set()}
    b = {"y": lambda g, c: set()}
    assert set(merge_tools(a, b)) == {"x", "y"}


def test_merge_tools_raises_on_name_collision():
    a = {"x": lambda g, c: set()}
    with pytest.raises(ValueError):
        merge_tools(a, {"x": lambda g, c: set()})
