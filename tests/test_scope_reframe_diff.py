"""Differential oracle for the scope reframe (scope_reframe_audit.md; user-requested, 2026-07-24).

The reframe CHANGES answers by design (base isolation from a relativizer scope), so a plain "old == new"
oracle is wrong. The right form partitions the query space (audit's conservative-extension framing):

  * INVARIANT partition (must AGREE with the shipped global-union read): base-only reasoning and the
    derivation-frame token/entity coref. Current data has NO cross-relativizer-boundary union (kinded
    scopes SHARE the entity node), so scope-local union == global union on everything that exists —
    a regression here means the read change altered an old entailment.
  * REFRAME partition (must DIVERGE, in the expected direction): a fact born UNDER a relativizer scope
    is isolated from a base read (global would LEAK). This is the new behavior, pinned here.

Kept temporary + scoped ([[differential-oracle-retired]]): the shipped `_canon_class` is the oracle,
invoked directly; no second engine is maintained. Retire this diff when membership migration (1c) lands
and the old global path is deleted."""
from __future__ import annotations

import ugm.chain as chain
from ugm import ById
from ugm.attrgraph import AttrGraph, NAME, valued
from ugm.cnl import grammar_intake as gi
from ugm.cnl.query import ask_goal
from ugm.scope_tree import UNDER, put_under, scope_of, scope_chain, is_visible
from ugm.vocabulary import DENOTES
import ugm as h
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
GRAMMAR = (ROOT / "corpus" / "loudon_grammar.cnl").read_text(encoding="utf-8")


def _named(g, name, *, under=None):
    n = g.add_node({NAME: valued(name)})
    if under is not None:
        put_under(g, n, under)
    return n


def _ask(g, subj_id, obj):
    return ask_goal(g, ("yesno", ById(subj_id), "has", obj), [])


# ── the scope_tree primitive (1a) ────────────────────────────────────────────

def test_scope_of_and_chain():
    g = AttrGraph()
    base = _named(g, "lion")
    s1 = g.add_node({NAME: valued("<hypothesis>")}, control=True)
    s2 = g.add_node({NAME: valued("<hypothesis>")}, control=True)
    put_under(g, s2, s1)                       # s2 nested under s1
    child = _named(g, "cub", under=s2)
    assert scope_of(g, base) is None           # a base node has no scope
    assert scope_of(g, child) == s2
    assert scope_chain(g, s2) == [s2, s1]      # itself + ancestor
    assert is_visible(g, base, None)           # base visible from base
    assert not is_visible(g, child, None)      # scoped node NOT visible from base
    assert is_visible(g, child, s2)            # visible from its own scope
    assert is_visible(g, child, s1) is False   # NOT visible from an ancestor-only vantage
    assert is_visible(g, base, s2)             # base visible from inside a scope


def test_put_under_idempotent():
    g = AttrGraph()
    n = _named(g, "lion")
    s = g.add_node({NAME: valued("<hypothesis>")}, control=True)
    put_under(g, n, s)
    put_under(g, n, s)
    assert sum(1 for rel, _o in g.relations_from(n) if g.has_key(rel, UNDER)) == 1


# ── REFRAME partition: isolation (must diverge from global) ───────────────────

def test_scoped_fact_isolated_from_base_read():
    """`John says the lion has a mane`: the scoped fact must NOT leak to a BASE read, though the shipped
    GLOBAL union would leak it (the divergence the reframe intends)."""
    g = AttrGraph()
    L = _named(g, "lion")                       # base entity
    S = g.add_node({NAME: valued("<hypothesis>")}, control=True)
    Lp = _named(g, "lion", under=S)             # a reference to the lion, born under S
    mane = _named(g, "mane")
    g.add_relation(Lp, "has", mane)             # the scoped fact
    g.add_relation(Lp, DENOTES, L)              # identity link

    # scope-local (production): base is isolated
    assert _ask(g, L, "mane") != ["yes"]
    # oracle: the shipped GLOBAL union WOULD leak (proving the reframe actually did something)
    leaked = _oracle_ask_global(g, L, "mane")
    assert leaked == ["yes"]


def _oracle_ask_global(g, subj_id, obj):
    """Run the read with the SHIPPED global-union `_canon_class` (no scope filter) — the differential
    oracle. Temporarily disables `reframe_active` so `_scope_visible` is the identity."""
    import ugm.scope_tree as st
    orig = st.reframe_active
    st.reframe_active = lambda _g: False        # force the read hot path to skip scope filtering
    try:
        return _ask(g, subj_id, obj)
    finally:
        st.reframe_active = orig


# ── INVARIANT partition: derivation-frame coref preserved ─────────────────────

def test_derivation_frame_token_entity_fusion_preserved():
    """token --denotes--> entity, fact on the entity, both in BASE: a read pinned to the token must still
    fuse to the entity (the shipped coref). Scope-local union keeps it because both are co-scoped in base."""
    g = AttrGraph()
    T = _named(g, "lion")
    E = _named(g, "lion")
    mane = _named(g, "mane")
    g.add_relation(T, DENOTES, E)
    g.add_relation(E, "has", mane)
    assert _ask(g, T, "mane") == ["yes"]        # fusion survives
    assert _oracle_ask_global(g, T, "mane") == ["yes"]   # and agrees with the oracle (invariant)


# ── INVARIANT partition: normal grammar-route reasoning unchanged ─────────────

def test_conservative_extension_grammar_route():
    """A normal assert+ask through the real grammar route is unchanged by the (inactive) scope filter —
    there are no `<under>` edges, so `reframe_active` is False and the read is byte-identical."""
    kb = AttrGraph()
    gi.declare_grammar(kb, GRAMMAR + "safe is a adj\n", open_class="noun")
    rules: list = []
    h.ingest(kb, rules, "the lion has a mane")
    from ugm import rule_control
    active = rule_control.active_rules(kb, rules)
    assert ask_goal(kb, ("yesno", "lion", "has", "mane"), active) == ["yes"]
    assert ask_goal(kb, ("yesno", "lion", "has", "wings"), active) != ["yes"]
