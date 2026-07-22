"""Loader convergence (meaning_surfaces_audit.md §3 HIGH) — the comparative and possibilistic
mini-surfaces, previously reachable ONLY through their standalone batch loaders, now route through
`intake.ingest`. So a live session (or `load_kb`) can mix `x is more D than y` / `x is likely P` /
`P means N` with plain facts. These routes are purely additive: they sit in the fallback (the grammar
refuses both surfaces), are keyword-gated so they never claim a plain fact, and author facts/forks —
never a rule (transitivity is generated on demand; a hedge authors an epistemic SCOPE)."""
from ugm.intake import ingest
from ugm.cnl.authoring import load_corpus
from ugm.cnl.comparative import ask_comparative
from ugm.cnl import uncertainty


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


# --- HEDGE route -----------------------------------------------------------------------------------

def test_hedge_fact_routes_and_answers_banded():
    kb, rules = _fresh()
    out = ingest(kb, rules, "cy is likely a thief")
    assert out.kind == "hedge"
    assert uncertainty.ask(kb, "is cy a thief") == "likely"


def test_hedge_disjunction_routes():
    kb, rules = _fresh()
    assert ingest(kb, rules, "x is either male or female").kind == "hedge"


def test_hedge_lexicon_is_incremental_declare_before_use():
    """`P means N` extends the KB's hedge lexicon; a later ingest of a fact using that hedge parses
    against it (declare-before-use — the intake contract, the incremental analog of world.py's
    whole-text pre-scan)."""
    kb, rules = _fresh()
    assert ingest(kb, rules, "probable means 0.7").kind == "hedge"      # declaration
    assert ingest(kb, rules, "bob is probable spy").kind == "hedge"     # uses the just-declared hedge
    assert uncertainty.ask(kb, "is bob spy") == "likely"


# --- neither route steals a plain fact -------------------------------------------------------------

def test_a_plain_fact_is_not_claimed_by_either_route():
    kb, rules = _fresh()
    assert ingest(kb, rules, "ada is a suspect").kind == "fact"         # no more/less/than, no hedge
    assert ingest(kb, rules, "ada is happy").kind == "fact"
