"""The kind-parameterized scope CORE (ugm/scope_kinds.py) driven at the GENERIC layer.

`attribution` (holder) and `temporal` were collapsed into one `(kind, key_attr)`-parameterized core.
The holder/temporal tests exercise it through their two kind-bound facades and are the equivalence
proof. THIS file drives the generic functions directly through a SYNTHETIC THIRD kind — proving the
core is genuinely parameterized, not two hardcoded paths wearing a shared signature — with negative
controls on the two load-bearing properties (kind dispatch, non-veridicality).
"""
from ugm.attrgraph import AttrGraph
from ugm.check import check, collapse, POSITIVE, ASSUMED_NO
from ugm.suppose import KIND_HOLDER, scope_kind
from ugm.scope_kinds import scope_of, pen_scoped, holds_in, scopes_holding

KIND_SYNTH = "synthetic"          # a kind no facade knows — the core must serve it purely from params
KEY_SYNTH = "<synth-key>"


def _penned() -> AttrGraph:
    """Pen `lion is_a cat` in a SYNTHETIC-kind scope keyed to `k1`, through the generic core alone."""
    g = AttrGraph()
    pen_scoped(g, KIND_SYNTH, KEY_SYNTH, "k1", ("lion", "is_a", "cat"))
    return g


def test_generic_core_serves_an_unknown_kind():
    """The parameterization is real: a kind with no facade is ontological in-scope, non-veridical
    globally — exactly the holder/temporal behaviour, from params only."""
    g = _penned()
    assert check(g, ("is_a", "lion", "cat")) == ASSUMED_NO                      # non-veridical globally
    assert holds_in(g, KIND_SYNTH, KEY_SYNTH, "k1", ("is_a", "lion", "cat")) == POSITIVE  # ontological
    assert collapse(check(g, ("is_a", "lion", "cat"))) == "no"


def test_scopes_holding_finds_the_key():
    assert scopes_holding(g := _penned(), KIND_SYNTH, KEY_SYNTH, ("lion", "is_a", "cat")) == ["k1"]


def test_the_scope_is_kinded_and_keyed():
    g = _penned()
    n = scope_of(g, KIND_SYNTH, KEY_SYNTH, "k1")
    assert n is not None and scope_kind(g, n) == KIND_SYNTH


# --- NEGATIVE CONTROLS: the two properties the core must not lose -----------------------------------

def test_kind_dispatch_is_load_bearing():
    """scopes_holding filters on kind: the same key_attr under the WRONG kind finds nothing. If the
    filter were dropped, a holder query would wrongly read a synthetic-kind scope's contents."""
    g = _penned()
    assert scopes_holding(g, KIND_HOLDER, KEY_SYNTH, ("lion", "is_a", "cat")) == []


def test_materialize_flag_governs_read_time_minting():
    """holds_in(materialize=False) on a never-penned key does NOT mint a scope and answers assumed-no;
    materialize=True mints it (so a cross-scope rule could pen into it) — the temporal-vs-holder read
    difference, as a pure flag."""
    g = AttrGraph()
    assert holds_in(g, KIND_SYNTH, KEY_SYNTH, "ghost", ("is_a", "x", "y")) == ASSUMED_NO
    assert scope_of(g, KIND_SYNTH, KEY_SYNTH, "ghost") is None                  # not materialized
    holds_in(g, KIND_SYNTH, KEY_SYNTH, "ghost", ("is_a", "x", "y"), materialize=True)
    assert scope_of(g, KIND_SYNTH, KEY_SYNTH, "ghost") is not None              # materialized


def test_one_scope_per_key_is_reused():
    """Successive pens on the same key accrete in ONE scope (candidates-by-key)."""
    g = _penned()
    pen_scoped(g, KIND_SYNTH, KEY_SYNTH, "k1", ("lion", "is_a", "pet"))
    assert scope_of(g, KIND_SYNTH, KEY_SYNTH, "k1") is not None
    assert sorted(scopes_holding(g, KIND_SYNTH, KEY_SYNTH, t)[0] for t in
                  [("lion", "is_a", "cat"), ("lion", "is_a", "pet")]) == ["k1", "k1"]
