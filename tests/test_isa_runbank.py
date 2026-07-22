"""
The ISA FORWARD driver for RECOGNITION — `isa.lowering.run_bank` (the reference opcode `Machine`
+ a dumb `Rule`->program lowering, driven to fixpoint), the ONE production engine for the
recognition path (decision-attrgraph-rehost, the "one engine" move).

`run_bank` is a forward, seed-and-walk matcher (SEED a rel by name, FOLLOW bare edges) — NOT the
backward demand-all-heads `solve_all` (which over-recognized globally and was ~28x slower per
sentence). The opcode set stays PURELY POSITIVE: a NAC is lowered to a positive sub-program the
DRIVER runs as a match-time filter, never a CHECK-ABSENT opcode. Value invention (`<cond>?`/
`<rule>?` skolem, tag literals) reproduces the per-firing fresh-node-minting discipline.

These pin `run_bank(_ALL_FORMS)`'s OWN recognized RULES and real domain FACTS against a FIXED
expected value (equivalence with the previous rewriter/name-based generation is NOT a correctness
target, implementation_plan.md 2026-07-10 ratification) — this is what licenses routing production
`load_facts`/`load_corpus` recognition through it (`authoring._recognize`).
"""
import ugm as h
from ugm.cnl import forms as F
from ugm.cnl.authoring import _ALL_FORMS, _corpus_lines, expand_rules, load_corpus
from ugm.cnl.forms import tokenize
from ugm import run_bank, derived_triples
from ugm.attrgraph import _is_inert


# A deliberately DIVERSE corpus: plain facts, a relation, gradable declaration, disjointness, an
# `if/then` universal, a plural-noun universal, a bare-body rule, a graded-body rule, a NAC rule,
# and a closed-world declaration — every recognition shape. (The loose/lexicon-frame shapes were
# dropped 2026-07-22 with the retirement of the Stage-3 loose subsystem.)
CORPUS = """
alice is a customer
alice wants vanilla
bob is a customer
vanilla is in_stock
urgent is gradable
solid is disjoint from liquid
if someone is rough then they are young
Cold things are kind
?c served express when ?c wants ?f
?c is urgent when ?c is a customer and ?c is very urgent
?x is thief when ?x is a suspect and ?x is not cleared
cleared is closed world
"""

_SCAFFOLD = set(F.SURFACE_TAGS) | {"next", "first", "a", "an", "the", "<sentence>"}


def _is_scaffold(nm: str | None) -> bool:
    return nm is None or nm in _SCAFFOLD or nm.startswith(
        ("k_", "rl_", "u_", "is_kw", "is_bnd", "kw_", "<", "frame_", "body", "if_ctx"))


def _real_facts(g) -> set[tuple[str, str, str]]:
    """The DOMAIN facts (not recognition/surface scaffolding, not control, not inert)."""
    ctrl = {g.name(n) for n in g.nodes() if g.is_control(n)}
    out: set[tuple[str, str, str]] = set()
    for s, r, o in derived_triples(g):
        if any(_is_inert(x) for x in (s, r, o)):
            continue
        if r == "next" or r in ctrl or _is_scaffold(s) or _is_scaffold(o):
            continue
        out.add((s, r, o))
    return out


def _rule_shapes(g) -> list:
    return sorted(
        (rl.key,
         tuple(sorted(p.tokens() for p in rl.lhs)),
         tuple(sorted(p.tokens() for p in rl.nac)),
         tuple(sorted(p.tokens() for p in rl.rhs)),
         tuple(sorted((gc.var, tuple(sorted(gc.embedding.items())), gc.threshold)
                      for gc in rl.graded)))
        for rl in expand_rules(g))


def _recognize(driver, sentences):
    g = h.Graph()
    for s in sentences:
        tokenize(g, s)
    driver(g, _ALL_FORMS)
    return g


# The FIXED expected recognition result of `run_bank(_ALL_FORMS)` on the whole CORPUS — every
# recognition shape in one batch (plain facts, a relation, gradable declaration, disjointness, an
# if/then universal, a plural-noun universal, a bare-body rule, a graded-body rule, a NAC rule, a
# closed-world declaration).
_WHOLE_BATCH_FACTS = {
    ("alice", "is_a", "customer"), ("alice", "wants", "vanilla"),
    ("bob", "is_a", "customer"), ("vanilla", "is", "in_stock"), ("urgent", "is", "gradable"),
    ("rough", "before", "they"), ("then", "is_bnd", "yes"), ("and", "is_bnd", "yes"),
    ("very", "is_kw", "yes"), ("when", "is_bnd", "yes"),
    ("not", "is_kw", "yes"), ("not", "kw_not", "yes"),
}
_WHOLE_BATCH_RULES = [
    ("rule.?c.is.urgent",
     (("?c", "is_a", "customer"),), (),
     (("?c", "is", "urgent"),), (("?c", (("urgent", 1.0),), 0.8),)),
    ("rule.?c.served.express",
     (("?c", "wants", "?f"),), (), (("?c", "served", "express"),), ()),
    ("rule.?x.are.young",
     (("?x", "is", "rough"),), (), (("?x", "are", "young"),), ()),
    ("rule.?x.is.thief",
     (("?x", "is_a", "suspect"),), (("?x", "is", "cleared"),),
     (("?x", "is", "thief"),), ()),
]


def test_run_bank_reproduces_the_expected_whole_batch_recognition():
    """Whole-batch: `run_bank` recognizes `_ALL_FORMS` over the diverse CORPUS as expected —
    facts AND rules pinned directly."""
    sents = _corpus_lines(CORPUS)
    gb = _recognize(run_bank, sents)
    assert _real_facts(gb) == _WHOLE_BATCH_FACTS
    assert _rule_shapes(gb) == _WHOLE_BATCH_RULES


# Per-sentence expected (facts, rule-shapes) — the property that made whole-batch safe: every
# single statement recognizes deterministically in isolation, and the per-sentence results union
# to the whole-batch result above.
_PER_SENTENCE = {
    "alice is a customer": ({("alice", "is_a", "customer")}, []),
    "alice wants vanilla": ({("alice", "wants", "vanilla")}, []),
    "bob is a customer": ({("bob", "is_a", "customer")}, []),
    "vanilla is in_stock": ({("vanilla", "is", "in_stock")}, []),
    "urgent is gradable": ({("urgent", "is", "gradable")}, []),
    "solid is disjoint from liquid": (set(), []),
    "if someone is rough then they are young": (
        {("rough", "before", "they"), ("then", "is_bnd", "yes")},
        [("rule.?x.are.young", (("?x", "is", "rough"),), (), (("?x", "are", "young"),), ())],
    ),
    "Cold things are kind": (set(), []),
    "?c served express when ?c wants ?f": (
        {("when", "is_bnd", "yes")},
        [("rule.?c.served.express", (("?c", "wants", "?f"),), (),
          (("?c", "served", "express"),), ())],
    ),
    "?c is urgent when ?c is a customer and ?c is very urgent": (
        {("and", "is_bnd", "yes"), ("very", "is_kw", "yes"), ("when", "is_bnd", "yes")},
        [("rule.?c.is.urgent", (("?c", "is_a", "customer"),), (),
          (("?c", "is", "urgent"),), (("?c", (("urgent", 1.0),), 0.8),))],
    ),
    "?x is thief when ?x is a suspect and ?x is not cleared": (
        {("and", "is_bnd", "yes"), ("not", "is_kw", "yes"), ("not", "kw_not", "yes"),
         ("when", "is_bnd", "yes")},
        [("rule.?x.is.thief", (("?x", "is_a", "suspect"),), (("?x", "is", "cleared"),),
          (("?x", "is", "thief"),), ())],
    ),
    "cleared is closed world": (set(), []),
}


def test_run_bank_reproduces_the_expected_per_sentence_recognition():
    """Per-sentence isolation is also as expected: every single statement recognizes
    deterministically, pinned directly against a fixed expectation."""
    for s in _corpus_lines(CORPUS):
        gb = _recognize(run_bank, [s])
        exp_facts, exp_rules = _PER_SENTENCE[s]
        assert _real_facts(gb) == exp_facts, s
        assert _rule_shapes(gb) == exp_rules, s


def test_run_bank_nac_guard_blocks_generic_clause():
    """The match-time NAC filter really fires: `?c is a customer` must fold ONLY as the `is_a`
    sugar, NOT also as a spurious generic `?c is a` clause (the generic body clause's NAC on the
    is_kw-tagged `a` blocks it). A race here (applying a firing before its guard tag) would leak
    the extra clause — this pins the collect-then-apply discipline."""
    g = _recognize(run_bank, ["?c is urgent when ?c is a customer and ?c is very urgent"])
    rule = next(r for r in expand_rules(g) if r.key == "rule.?c.is.urgent")
    assert [p.tokens() for p in rule.lhs] == [("?c", "is_a", "customer")]   # no ('?c','is','a')


def test_load_corpus_reasons_correctly_on_run_bank_recognition():
    """End-to-end: production `load_corpus` (now recognizing via `run_bank`) still routes the
    ice-cream contract exactly — the public answer contract is unchanged by the engine swap."""
    ice = """
        urgent is gradable
        vanilla is in_stock
        chocolate is in_stock
        alice is a customer
        alice wants vanilla
        alice is very urgent
        bob is a customer
        bob wants chocolate
        carol is a customer
        carol wants strawberry
        ?c is urgent when ?c is a customer and ?c is very urgent
        ?c served express when ?c is urgent and ?c wants ?f and ?f is in_stock
        ?c served regular when ?c wants ?f and ?f is in_stock and ?c is not urgent
        ?c offered alternative when ?c is a customer and ?c wants ?f and ?f is not in_stock
    """
    kb, rules = load_corpus(ice)
    h.run_rules(kb, rules)
    assert h.ask(kb, "is alice served express") == ["yes"]
    assert h.ask(kb, "is bob served regular") == ["yes"]
    assert h.ask(kb, "is carol offered alternative") == ["yes"]
    assert h.ask(kb, "is bob served express") == ["no"]
    assert sorted(h.ask(kb, "who served express")) == ["alice served express"]
