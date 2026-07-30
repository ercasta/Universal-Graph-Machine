"""Causation crossing over the scope-tree (scope_reframe_audit.md Step 2, `ugm/scope_crossing.py`).

Propositional causation as the scope reframe realizes it: `that A causes that B` mints two proposition
SCOPES related by a base `causes` fact; DECLARED rules over the `@?h` scope-tree read decide `holds_base`
(reify + causal MP) and promote a held scope's members to base — no `prop:` handle, no orphan refs. Proven
end-to-end in `bench/spike_scopetree_rel_read.py`; this pins it as a regression floor.
"""
import warnings

from ugm.attrgraph import AttrGraph, NAME, valued
from ugm.chain import ById, _facts_matching
from ugm.cnl.query import ask_goal
from ugm.scope_crossing import (
    decide_rules, promote_rules, mint_causal_link, resolve_crossings, CROSSES_SCOPE,
)

warnings.simplefilter("ignore")

ANTE = ("lion", "has_not", "mane")           # that lion has no mane
CONS = ("lion", "is", "safe")                # ... causes that lion is safe


def _graph(order: str, base: bool) -> tuple[AttrGraph, str]:
    """Build `that lion has no mane causes that lion is safe`, with the base fact `lion has no mane`
    present iff `base`, stated link-first or antecedent-first. Returns `(graph, consequent_scope)`."""
    g = AttrGraph()

    def statement():
        return mint_causal_link(g, ANTE, CONS)

    def base_fact():
        g.add_relation(g.add_node({NAME: valued("lion")}), "has_not",
                       g.add_node({NAME: valued("mane")}))

    if order == "link-first":
        s_a, s_b = statement()
        if base:
            base_fact()
    else:
        if base:
            base_fact()
        s_a, s_b = statement()
    return g, s_b


def _holds(g, scope) -> bool:
    return bool(list(_facts_matching(g, "holds_base", ById(scope), "yes")))


# ── the crossing DECISION (reify + causal MP) ─────────────────────────────────

def test_consequent_holds_in_base_link_first():
    g, s_b = _graph("link-first", base=True)                    # link stated BEFORE the base fact
    resolve_crossings(g)
    assert _holds(g, s_b)


def test_consequent_holds_in_base_antecedent_first():
    g, s_b = _graph("antecedent-first", base=True)
    resolve_crossings(g)
    assert _holds(g, s_b)


def test_negative_control_does_not_cross():
    # No base fact => the antecedent does not hold in base => nothing crosses (the link alone asserts
    # nothing — soundness).
    g, s_b = _graph("link-first", base=False)
    resolve_crossings(g)
    assert not _holds(g, s_b)


# ── end to end: the consequent becomes true in base ───────────────────────────

def _answer(order: str, base: bool):
    g, _s_b = _graph(order, base)
    resolve_crossings(g)                                        # decide + materialize base referents
    return ask_goal(g, ("yesno", "lion", "is", "safe"), list(promote_rules()))


def test_end_to_end_lion_is_safe_link_first():
    assert _answer("link-first", base=True) == ["yes"]


def test_end_to_end_lion_is_safe_antecedent_first():
    assert _answer("antecedent-first", base=True) == ["yes"]


def test_end_to_end_negative_control():
    assert _answer("link-first", base=False) != ["yes"]


def test_links_chain_through_base():
    # A --> B --> C: the middle proposition B is promoted to base (during the fixpoint), so the second
    # link's reify reads it and C crosses too. `resolve_crossings` interleaves promote for exactly this.
    g = AttrGraph()
    mint_causal_link(g, ("door", "is", "open"), ("cat", "is", "scared"))
    mint_causal_link(g, ("cat", "is", "scared"), ("dog", "is", "alert"))
    g.add_relation(g.add_node({NAME: valued("door")}), "is", g.add_node({NAME: valued("open")}))
    resolve_crossings(g)
    assert ask_goal(g, ("yesno", "cat", "is", "scared"), []) == ["yes"]     # B promoted
    assert ask_goal(g, ("yesno", "dog", "is", "alert"), []) == ["yes"]      # C crossed via B


# ── the rules are well-formed data ────────────────────────────────────────────

def test_crossing_rules_load():
    # reify + causal MP = 2 rules; promote = 1. All parse as machine rules (no Python island).
    assert len(decide_rules()) == 2
    assert len(promote_rules()) == 1


# ── generalization: a SECOND declared crossing relation reuses the SAME driver ────────────────
# docs/units/STATUS.md's "generalize resolve_crossings" step: `causes` was hardcoded throughout this
# module; `relations` is now a parameter, so a different relation (here `enables`) crosses scopes through
# the identical decide -> promote fixpoint, with no new Python module and no change to the driver itself —
# the outer-loop metaprocessor shape (select region -> demand-decide -> promote -> repeat), checked against
# a second data point rather than assumed to generalize from one.

def test_a_second_declared_relation_crosses_through_the_same_driver():
    g = AttrGraph()
    mint_causal_link(g, ("switch", "is", "on"), ("light", "is", "lit"), relation="enables")
    g.add_relation(g.add_node({NAME: valued("switch")}), "is", g.add_node({NAME: valued("on")}))
    resolve_crossings(g, relations=("enables",))
    assert ask_goal(g, ("yesno", "light", "is", "lit"), []) == ["yes"]


def test_two_different_relations_cross_in_one_driver_call():
    g = AttrGraph()
    mint_causal_link(g, ANTE, CONS)                                          # causes
    mint_causal_link(g, ("switch", "is", "on"), ("light", "is", "lit"), relation="enables")
    g.add_relation(g.add_node({NAME: valued("lion")}), "has_not",
                   g.add_node({NAME: valued("mane")}))
    g.add_relation(g.add_node({NAME: valued("switch")}), "is", g.add_node({NAME: valued("on")}))
    resolve_crossings(g, relations=("causes", "enables"))
    assert ask_goal(g, ("yesno", "lion", "is", "safe"), []) == ["yes"]
    assert ask_goal(g, ("yesno", "light", "is", "lit"), []) == ["yes"]


def test_undeclared_relation_does_not_cross():
    # A crossing link over a relation NOT in `relations` is invisible to this driver call — region
    # selection is real, not a blanket "promote everything scoped."
    g = AttrGraph()
    mint_causal_link(g, ("switch", "is", "on"), ("light", "is", "lit"), relation="enables")
    g.add_relation(g.add_node({NAME: valued("switch")}), "is", g.add_node({NAME: valued("on")}))
    resolve_crossings(g, relations=("causes",))                              # enables not requested
    assert ask_goal(g, ("yesno", "light", "is", "lit"), []) != ["yes"]


def test_a_kb_declared_relation_crosses_with_no_caller_kwarg():
    # `enables crosses_scope yes` as ordinary KB data is enough — no `relations=` argument at the call
    # site, mirroring how `causes propagates has` (test_causal_propagation.py) authors a relation property
    # as a fact rather than a Python change.
    g = AttrGraph()
    g.add_relation(g.add_node({NAME: valued("enables")}), CROSSES_SCOPE, g.add_node({NAME: valued("yes")}))
    mint_causal_link(g, ("switch", "is", "on"), ("light", "is", "lit"), relation="enables")
    g.add_relation(g.add_node({NAME: valued("switch")}), "is", g.add_node({NAME: valued("on")}))
    resolve_crossings(g)                                                     # default relations=("causes",)
    assert ask_goal(g, ("yesno", "light", "is", "lit"), []) == ["yes"]       # picked up from declared data


def test_the_default_causes_still_crosses_without_any_declaration():
    # Backward compatibility: `causes` ships as the built-in default and needs no `crosses_scope` fact.
    g, s_b = _graph("link-first", base=True)
    resolve_crossings(g)
    assert _holds(g, s_b)


# ── focus_scope bounds the region — ugm/focus.py's attention register as the metaprocedure's seed ────
# docs/units/STATUS.md's "focus.py as the region-selection seed" item: `focus_scope` (already threaded
# through `chain_sip`/`_facts_matching`, the mechanism `suppose()` uses to bound hypothesis reasoning) now
# bounds `resolve_crossings` the identical way — the driver runs over the working set the conversation is
# currently about, not blindly over every crossing link in the whole graph.

def test_focus_scope_bounds_which_crossing_runs():
    g = AttrGraph()
    mint_causal_link(g, ANTE, CONS)                                          # lion has no mane -> lion is safe
    mint_causal_link(g, ("switch", "is", "on"), ("light", "is", "lit"), relation="enables")
    g.add_relation(g.add_node({NAME: valued("lion")}), "has_not",
                   g.add_node({NAME: valued("mane")}))
    g.add_relation(g.add_node({NAME: valued("switch")}), "is", g.add_node({NAME: valued("on")}))
    resolve_crossings(g, relations=("causes", "enables"), focus_scope=frozenset({"lion", "mane"}))
    assert ask_goal(g, ("yesno", "lion", "is", "safe"), []) == ["yes"]        # in focus: crosses
    assert ask_goal(g, ("yesno", "light", "is", "lit"), []) != ["yes"]        # out of focus: does not
