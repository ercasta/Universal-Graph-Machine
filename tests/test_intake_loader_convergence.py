"""Loader convergence (meaning_surfaces_audit.md §3 HIGH) — the COMPARATIVE mini-surface, previously
reachable ONLY through its standalone batch loader, now routes through `intake.ingest`. So a live
session (or `load_kb`/`load_corpus`) can mix `x is more D than y` with plain facts. Purely additive:
it sits in the fallback (the grammar refuses the surface), is keyword-gated so it never claims a
plain fact, and authors an ink relation — never a rule (transitivity is generated on demand).

⚠ HEDGES are deliberately NOT routed through intake — they author a banded FORK (family B) that does
not survive the fact path's whole-graph normalization on a later utterance; that composition is
scope-generalization's job (audit §2). Hedges stay on `world.load_world` (authored last)."""
from ugm.intake import ingest
from ugm.cnl.authoring import load_corpus
from ugm.cnl.comparative import ask_comparative


def _fresh():
    return load_corpus("")            # (kb, rules) — an empty session, default rule set


# --- COMPARISON route ------------------------------------------------------------------------------

def test_comparison_routes_and_is_queryable():
    kb, rules = _fresh()
    out = ingest(kb, rules, "x is more beautiful than y")
    assert out.kind == "comparison"
    assert ask_comparative(kb, "is x more beautiful than y") == "yes"
    assert ask_comparative(kb, "is y more beautiful than x") == "no"   # the strict order's opposite


def test_comparison_authors_no_rule():
    """Transitivity is generated ON DEMAND (`comparison_rules`), so a comparison never mutates the
    session's `rules` list — the read path brings its own rules per query."""
    kb, rules = _fresh()
    before = len(rules)
    ingest(kb, rules, "x is more beautiful than y")
    assert len(rules) == before


def test_less_is_the_reversed_arrow():
    kb, rules = _fresh()
    assert ingest(kb, rules, "y is less beautiful than x").kind == "comparison"
    assert ask_comparative(kb, "is x more beautiful than y") == "yes"   # `less` stored reversed


# --- the comparison route does not steal a plain fact ----------------------------------------------

def test_a_plain_fact_is_not_claimed_by_the_comparison_route():
    kb, rules = _fresh()
    assert ingest(kb, rules, "ada is a suspect").kind == "fact"         # no more/less/than
    assert ingest(kb, rules, "ada is happy").kind == "fact"


def test_a_hedge_line_is_not_routed_as_a_comparison():
    """A `x is likely P` line is NOT claimed by the comparison route (it has no more/less/than) — it
    falls through to the ordinary fact recognition. (Hedges route through `world.load_world`, not
    intake — see the module docstring.)"""
    kb, rules = _fresh()
    assert ingest(kb, rules, "cy is likely a thief").kind != "comparison"
