"""
The ISA FORWARD driver for RECOGNITION — `isa.lowering.run_bank` (the reference opcode `Machine`
+ a dumb `Rule`->program lowering, driven to fixpoint) replacing `rewriter.run` on the recognition
path (decision-attrgraph-rehost, the "one engine" move).

`run_bank` is a forward, seed-and-walk matcher (SEED a rel by name, FOLLOW bare edges) — NOT the
backward demand-all-heads `solve_all` (which over-recognized globally and was ~28x slower per
sentence). The opcode set stays PURELY POSITIVE: a NAC is lowered to a positive sub-program the
DRIVER runs as a match-time filter (faithful to `rewriter.nac_blocks`), never a CHECK-ABSENT opcode.
Value invention (`<cond>?`/`<rule>?` skolem, tag literals) reproduces `rewriter.apply_rule`'s
per-firing `fresh` dict.

These are the differential tests pinning that `run_bank(_ALL_FORMS)` reproduces `rewriter.run`
EXACTLY — recognized RULES identical AND real domain FACTS identical — which is what licenses
routing production `load_facts`/`load_corpus` recognition through it (`authoring._recognize`).
"""
import ugm as h
from ugm.cnl import forms as F
from ugm.cnl.authoring import _ALL_FORMS, _corpus_lines, expand_rules, load_corpus
from ugm.cnl.forms import tokenize
from ugm.cnl.rewriter import run as rw_run
from ugm import run_bank, derived_triples
from ugm.attrgraph import _is_inert


# A deliberately DIVERSE corpus: plain facts, a relation, gradable declaration, disjointness, an
# `if/then` universal, a plural-noun universal, a bare-body rule, a graded-body rule, a NAC rule,
# a lexicon frame + a loose imperative, and a closed-world declaration — every recognition shape.
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
serve ?x first means ?x served express when ?x wants ?f and ?f is in_stock
serve urgent customers first
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


def test_run_bank_matches_rewriter_whole_batch():
    """Whole-batch: `run_bank` reproduces `rewriter.run` on `_ALL_FORMS` — facts AND rules."""
    sents = _corpus_lines(CORPUS)
    gf = _recognize(rw_run, sents)
    gb = _recognize(run_bank, sents)
    assert _real_facts(gb) == _real_facts(gf)
    assert _rule_shapes(gb) == _rule_shapes(gf)


def test_run_bank_matches_rewriter_per_sentence():
    """Per-sentence isolation is also faithful (the property that made whole-batch safe): every
    single statement recognizes byte-for-byte the same under both engines."""
    for s in _corpus_lines(CORPUS):
        gf = _recognize(rw_run, [s])
        gb = _recognize(run_bank, [s])
        assert _real_facts(gb) == _real_facts(gf), s
        assert _rule_shapes(gb) == _rule_shapes(gf), s


def test_run_bank_nac_guard_blocks_generic_clause():
    """The match-time NAC filter really fires: `?c is a customer` must fold ONLY as the `is_a`
    sugar, NOT also as a spurious generic `?c is a` clause (the generic body clause's NAC on the
    is_kw-tagged `a` blocks it). A race here (applying a firing before its guard tag) would leak
    the extra clause — this pins the collect-then-apply discipline."""
    g = _recognize(run_bank, ["?c is urgent when ?c is a customer and ?c is very urgent"])
    rule = next(r for r in expand_rules(g) if r.key == "rule.?c.is.urgent")
    assert [p.tokens() for p in rule.lhs] == [("?c", "is_a", "customer")]   # no ('?c','is','a')


def test_run_bank_recursive_rule_terminates():
    """The `fired` set (keyed over LHS binders) terminates a recognition fixpoint that keeps
    matching — a whole realistic corpus reaches fixpoint and its rules are the rewriter set."""
    g = _recognize(run_bank, _corpus_lines(CORPUS))
    assert _rule_shapes(g) == _rule_shapes(_recognize(rw_run, _corpus_lines(CORPUS)))


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
