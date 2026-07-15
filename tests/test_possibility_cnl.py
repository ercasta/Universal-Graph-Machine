"""
Possibilistic CNL surface SLICE 1 (docs/possibilistic.md S7.5): the hedge-on-a-fact form, the first
disjunctive `either…or` form, and banded yes/no verdicts. See `ugm/cnl/uncertainty.py`.
"""
from ugm.attrgraph import AttrGraph
from ugm.apply import SCOPE
from ugm.possibility import possibility
from ugm.cnl.uncertainty import parse_hedge_fact, parse_either, load_uncertain, ask


def _scope_of(g: AttrGraph, subj: str, obj: str):
    """The fork-scope id holding the pencil `subj is obj`, or None — for the correlation check."""
    for s_id in g.nodes_named(subj):
        for r in g.out(s_id):
            if g.is_control(r) and any(g.name(o) == obj for o in g.out(r)):
                a = g.get_attr(r, SCOPE)
                return a.value if a is not None else None
    return None


# --- form 1: hedge on a fact ------------------------------------------------

def test_hedge_parse():
    assert parse_hedge_fact("cy is likely a thief") == ("cy", "is_a", "thief", 0.6)
    assert parse_hedge_fact("x is unlikely male") == ("x", "is", "male", 0.3)
    assert parse_hedge_fact("x is very likely male") == ("x", "is", "male", 0.85)
    assert parse_hedge_fact("x is very unlikely male") == ("x", "is", "male", 0.15)


def test_degree_adverb_is_not_a_hedge():
    """DISAMBIGUATION: a membership degree adverb is never routed as a hedge (the crisp/degree
    surface is untouched)."""
    assert parse_hedge_fact("x is very urgent") is None
    assert parse_hedge_fact("alice is somewhat urgent") is None
    assert parse_hedge_fact("alice is slightly cold") is None


def test_hedge_load_and_ask():
    g = AttrGraph()
    rest = load_uncertain(g, "cy is likely a thief\nx is very unlikely male")
    assert rest == []
    assert ask(g, "is cy a thief") == "likely"
    assert ask(g, "is x male") == "very unlikely"
    assert ask(g, "is x female") == "assumed-no"                 # unmentioned, closed
    assert ask(g, "is x female", closed=False) == "unknown"


def test_load_uncertain_returns_plain_lines():
    """Plain facts are NOT intercepted — they come back for the ordinary loader."""
    g = AttrGraph()
    rest = load_uncertain(g, "cy is likely a thief\nbob likes mary\nx is unlikely tall")
    assert rest == ["bob likes mary"]
    assert ask(g, "is cy a thief") == "likely"
    assert possibility(g, "is", "x", "tall") == 0.3             # `unlikely tall` -> a fork, not a degree


# --- form 2: the first disjunctive form -------------------------------------

def test_either_parse():
    assert parse_either("x is either male and tall or female and short") == (
        "x", ["male", "tall"], ["female", "short"])


def test_either_or_makes_two_correlated_forks():
    g = AttrGraph()
    load_uncertain(g, "x is either male and tall or female and short")
    # both alternatives visible at the even band
    for attr in ("male", "tall", "female", "short"):
        assert possibility(g, "is", "x", attr) == 0.5
    # CORRELATION (the point of the form): male∧tall share ONE fork; female∧short another.
    assert _scope_of(g, "x", "male") == _scope_of(g, "x", "tall")
    assert _scope_of(g, "x", "female") == _scope_of(g, "x", "short")
    assert _scope_of(g, "x", "male") != _scope_of(g, "x", "female")
