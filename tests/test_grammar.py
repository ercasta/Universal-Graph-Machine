"""The CNL-declared intake grammar (`cnl/grammar.py`) and the interpretation scope
(`interpretation.py`).

Designs: `docs/design/homoiconic_grammar.md` (read §0), `docs/design/surface_interpretation.md`.
These pin the behaviours the four bench spikes established, so the machinery can move out of
`bench/` without losing them.
"""
from __future__ import annotations

import pathlib

import pytest

from ugm import AttrGraph
from ugm.cnl.grammar import (AMBIGUOUS, PARSED, REFUSED, compile_grammar, load_grammar,
                             load_grammar_file, ambiguous_spans, parse)
from ugm.interpretation import (UNINTERPRETED, contradictions, culprits, describe,
                                discard_scope, interpret, intern_described, open_scope,
                                scope_facts)

CORPUS = pathlib.Path(__file__).resolve().parent.parent / "corpus"
GRAMMAR_FILE = CORPUS / "lion_grammar.cnl"

# ONE LINE decides whether a modified noun phrase denotes the SAME entity as its head or a distinct
# described subkind (`homoiconic_grammar.md` §10).
PERCOLATE = "slot head in np from modifier plus np is right head"
MINT = "mint head in np from modifier plus np under right head"


@pytest.fixture(scope="module")
def gram():
    return load_grammar_file(GRAMMAR_FILE)


@pytest.fixture(scope="module")
def banks(gram):
    return compile_grammar(gram)


@pytest.fixture(scope="module")
def subkind_banks():
    text = GRAMMAR_FILE.read_text(encoding="utf-8").replace(PERCOLATE, MINT)
    assert MINT in text, "the percolate line must be present to be swapped"
    return compile_grammar(load_grammar(text))


def _fold(banks, *sentences):
    """Parse + interpret `sentences` into one graph; returns (graph, scope, facts)."""
    g = AttrGraph()
    for s in sentences:
        assert parse(g, s, banks)[0] == PARSED, f"expected {s!r} to parse"
    scope = open_scope(g)
    interpret(g, banks, scope)
    return g, scope, scope_facts(g, scope)


# ---------------------------------------------------------------------------
# The declarations round-trip
# ---------------------------------------------------------------------------

def test_grammar_reads_back_out_of_cnl(gram):
    assert ("np", "noun") in gram.unary
    assert ("clause", "np", "vp") in gram.binary
    assert len(gram.slots) == 32
    assert len(gram.assertions) == 6
    # `<...>` categories are engine bookkeeping riding the same `is_a` the lexicon uses; reading
    # them would declare every word a `<mention>` (~80% of parse runtime before the filter).
    assert all(not c.startswith("<") for cs in gram.lexicon.values() for c in cs)


def test_lexicon_is_only_the_declared_words(gram):
    assert gram.lexicon["lion"] == ["noun"]
    assert gram.lexicon["has"] == ["transitive"]
    assert "expands" not in gram.lexicon and "slot" not in gram.lexicon


# ---------------------------------------------------------------------------
# Acceptance: the residual Loudon failures, and REFUSAL
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("sentence", [
    "the lion has a mane",                    # the shipped bank handles this one too
    "the lion roars",                         # intransitive: two slots, no shipped form
    "the guzerat lion has no mane",           # negation + modifier: THE exception-bearing sentence
    "the lion lives in africa",               # prepositional: folds to garbage today
    "the lion is smaller than the tiger",     # comparative
])
def test_parses_the_shapes_the_shipped_bank_cannot(banks, sentence):
    assert parse(AttrGraph(), sentence, banks)[0] == PARSED


def test_gibberish_is_refused_not_guessed(banks):
    # The diagnostic a bank of independent surface patterns structurally cannot produce: there is
    # no notion of the WHOLE sentence being accounted for.
    assert parse(AttrGraph(), "glorp the flarn", banks)[0] == REFUSED


def test_ambiguity_is_detected_and_asked_about(banks):
    g = AttrGraph()
    outcome, toks, _eos = parse(g, "the lion eats the fish in africa", banks)
    assert outcome == AMBIGUOUS
    assert ambiguous_spans(g, toks), "the ambiguous spans must be nameable for a question"


def test_unambiguous_sentences_are_not_flagged(banks):
    for s in ("the lion has a mane", "the guzerat lion has no mane"):
        assert parse(AttrGraph(), s, banks)[0] == PARSED


def test_open_vocabulary_keeps_refusal(gram):
    # The open-class default must not destroy loudness — that is the whole point of the arc.
    ob = compile_grammar(gram, open_class="noun")
    assert parse(AttrGraph(), "glorp the flarn", ob)[0] == REFUSED
    assert parse(AttrGraph(), "the lion eats the bramble", ob)[0] == PARSED


# ---------------------------------------------------------------------------
# The fold
# ---------------------------------------------------------------------------

def test_fold_matches_the_shipped_bank_on_a_shared_shape(banks):
    _g, _s, facts = _fold(banks, "the lion has a mane")
    assert ("lion", "has", "mane") in facts


def test_fold_writes_the_exception(banks):
    # The fact the learner needed and never got: a partial parser drops linguistically MARKED
    # exceptions and keeps the generalizations (`bench/spike_loudon.py` §4).
    _g, _s, facts = _fold(banks, "the guzerat lion has no mane")
    assert ("lion", "has_not", "mane") in facts
    assert ("lion", "is", "guzerat") in facts


def test_fold_handles_intransitive_and_prepositional(banks):
    _g, _s, facts = _fold(banks, "the lion lives in africa")
    assert ("lion", "lives", "true") in facts
    assert ("lion", "in", "africa") in facts


def test_fold_handles_comparative(banks):
    _g, _s, facts = _fold(banks, "the lion is smaller than the tiger")
    assert ("lion", "smaller", "tiger") in facts


# ---------------------------------------------------------------------------
# Minting a described subkind (§10)
# ---------------------------------------------------------------------------

def test_minting_removes_the_manufactured_contradiction(banks, subkind_banks):
    _g, _s, percolated = _fold(banks, "the lion has a mane", "the guzerat lion has no mane")
    assert ("lion", "has", "mane") in percolated
    assert ("lion", "has_not", "mane") in percolated       # the contradiction, on ONE node

    _g2, _s2, minted = _fold(subkind_banks, "the lion has a mane", "the guzerat lion has no mane")
    assert ("lion", "has", "mane") in minted
    assert ("lion", "has_not", "mane") not in minted
    sub = "<is guzerat & is_a lion>"
    assert (sub, "has_not", "mane") in minted
    assert (sub, "is_a", "lion") in minted                 # decomposition still exposed


def test_minted_entity_is_nameless_and_described(subkind_banks):
    g, scope, _f = _fold(subkind_banks, "the guzerat lion has no mane")
    anon = [n for n in g.nodes()
            if not g.name(n) and not g.is_control(n) and not g.is_inert(n)
            and any(g.predicate(r) == "is_a" for r, _o in g.relations_from(n))]
    assert len(anon) == 1
    assert g.name(anon[0]) == ""                           # `ByDesc`: no name, only relations
    assert describe(g, anon[0]) == "<is guzerat & is_a lion>"


def test_exception_is_reachable_from_the_generalization(subkind_banks):
    # The point of minting: `<e> is_a lion` makes the exception a WITNESS of
    # `?x has mane when ?x is_a lion`, so it can refute it. Under percolation there was no
    # second entity to be a counterexample at all.
    g, _s, _f = _fold(subkind_banks, "the lion has a mane", "the guzerat lion has no mane")
    witnesses = [n for n in g.nodes() for r, o in g.relations_from(n)
                 if g.predicate(r) == "is_a" and g.name(o) == "lion"]
    assert witnesses
    assert any(g.predicate(r) == "has_not" for w in witnesses for r, _o in g.relations_from(w))


def test_description_keyed_interning_folds_repeat_mentions(subkind_banks):
    # Name-keyed `intern_mentions` is structurally blind to nameless nodes, so `interpret` runs the
    # description-keyed counterpart as part of the pass. REQUIRED for correctness, not tidiness:
    # value invention re-mints on every bank run.
    g, _s, facts = _fold(subkind_banks, "the guzerat lion has no mane",
                         "the guzerat lion is smaller than the tiger")
    anon = [n for n in g.nodes()
            if not g.name(n) and not g.is_control(n) and not g.is_inert(n)
            and any(g.predicate(r) == "is_a" for r, _o in g.relations_from(n))]
    assert len(anon) == 1, "two mentions of one subkind must land on ONE entity"
    sub = "<is guzerat & is_a lion>"
    assert (sub, "has_not", "mane") in facts        # both sentences' facts, on that one entity
    assert (sub, "smaller", "tiger") in facts


def test_identity_is_settled_before_predication(subkind_banks):
    # An ACQUIRED fact must not enter the description, or the entity fails to intern with the same
    # subkind mentioned elsewhere. `the african lion is strong` described its subject as
    # `<is african & is strong & is_a lion>` until the defining assertions were split out and run
    # first. Found on the Loudon corpus (`homoiconic_grammar.md` §12).
    g, _s, facts = _fold(subkind_banks, "the guzerat lion is smaller than the tiger",
                         "the guzerat lion has no mane")
    sub = "<is guzerat & is_a lion>"
    assert any(t[0] == sub for t in facts), f"expected the subkind described as {sub}: {facts}"
    assert not any("smaller" in t[0] or "has_not" in t[0] for t in facts), \
        "an acquired fact leaked into the entity's description"


# ---------------------------------------------------------------------------
# The surface / interpretation split (§11)
# ---------------------------------------------------------------------------

def test_contradiction_is_derived_and_names_its_culprits(banks):
    g, _s, _f = _fold(banks, "the lion has a mane", "the guzerat lion has no mane")
    cs = contradictions(g)
    assert cs, "a contradiction must be DERIVED, not detected by a checker"
    about, _because = cs[0]
    # More than one surface mention behind the entity means a coreference JUDGEMENT is in the
    # support — the thing to ASK about rather than guess.
    assert len(culprits(g, about)) == 2


def test_interpretation_is_discardable_and_the_surface_survives(banks, subkind_banks):
    g = AttrGraph()
    for s in ("the lion has a mane", "the guzerat lion has no mane"):
        assert parse(g, s, banks)[0] == PARSED
    # The delta marks (`unfolded`) are TRANSIENT scaffolding that the fold consumes and retires --
    # they are not part of the surface record, so they are excluded from what must survive. Tokens,
    # chains and spans are.
    surface = {n for n in g.nodes() if not g.has_key(n, UNINTERPRETED)}

    scope_a = open_scope(g)
    interpret(g, banks, scope_a)
    assert contradictions(g)

    discard_scope(g, scope_a, banks.slot_preds)
    assert surface <= set(g.nodes()), "the surface record must be untouched"
    assert not contradictions(g)

    # Re-interpret over the SAME surface — no re-parse — with the other reading.
    scope_b = open_scope(g)
    interpret(g, subkind_banks, scope_b)
    assert not contradictions(g)
    assert ("lion", "has", "mane") in scope_facts(g, scope_b)


def test_surface_carries_no_denotation(banks):
    # A head is already a judgement, so parsing must not write one.
    g = AttrGraph()
    parse(g, "the lion has a mane", banks)
    assert not any(g.predicate(r) in ("head", "subj", "denotes")
                   for n in g.nodes() for r, _o in g.relations_from(n))


def test_decompositions_tile_their_parent(banks):
    """Every materialized decomposition's children EXACTLY tile the parent's extent.

    This is the invariant that makes the parse tree safe to read as pointer hops. The chart is
    PACKED, so one span can carry several decompositions; a flat `?p kidl ?l` / `?p kidr ?r` pair
    would let the left child of one reading pair with the right child of another and feed a slot
    from a tree that was never parsed. Reifying the decomposition keeps a pairing atomic — and this
    test is what says so, since a mispairing shows up precisely as children that do not tile."""
    g = AttrGraph()
    parse(g, "the guzerat lion has no mane", banks)

    def slot(n, key):
        return next((o for r, o in g.relations_from(n) if g.has_key(r, key)), None)

    decs = [n for n in g.nodes() if slot(n, "dparent") is not None]
    assert decs, "the parse must materialize decompositions"
    for d in decs:
        p = slot(d, "dparent")
        only = slot(d, "donly")
        if only is not None:                          # unary: child covers the parent exactly
            assert (slot(only, "begin"), slot(only, "end")) == (slot(p, "begin"), slot(p, "end"))
            continue
        left, right = slot(d, "dleft"), slot(d, "dright")
        assert left is not None and right is not None, "a binary decomposition needs both children"
        assert slot(left, "begin") == slot(p, "begin")
        assert slot(left, "end") == slot(right, "begin"), "children must MEET at one split point"
        assert slot(right, "end") == slot(p, "end")


def test_parse_banks_are_idempotent(banks):
    """Re-running the parse banks over an UNCHANGED graph must add nothing.

    `parse` runs every bank over the WHOLE graph, so a non-idempotent surface rule makes a session's
    accretion QUADRATIC: `<span>?` is a bound literal (named, but minted fresh per firing), so before
    the span rule's NAC every re-run re-minted all 13 spans — parsing one sentence five times grew
    the graph by 104, 149, 201, 253, 305 instead of a flat 97."""
    g = AttrGraph()
    parse(g, "the lion has a mane", banks)
    settled = len(list(g.nodes()))
    for _ in range(3):
        parse(g, "the lion has a mane", banks)   # re-parsing writes a new chain...
    grown = len(list(g.nodes()))
    assert (grown - settled) % 3 == 0
    per_sentence = (grown - settled) // 3
    g2 = AttrGraph()
    parse(g2, "the lion has a mane", banks)
    base = len(list(g2.nodes()))
    parse(g2, "the lion has a mane", banks)
    assert len(list(g2.nodes())) - base == per_sentence, "accretion must be FLAT per sentence"


def _dec_count(g):
    return sum(1 for n in g.nodes() if g.has_key(n, "dparent"))


def test_fresh_marks_do_not_survive_a_parse(banks):
    """`FRESH` is a per-utterance delta and MUST be retired.

    This is a guard against a SILENT regression, which is why it is worth its own test: if
    `clear_fresh` stops being called, every answer stays correct and the system merely gets slower
    and slower, because the seed set the delta exists to keep small now grows with the session.
    Measured while building it -- leaving the marks standing took the span/decomposition stage from
    0.51s back up to 1.55s over eight sentences."""
    from ugm.cnl.grammar import FRESH
    g = AttrGraph()
    for s in ("the lion has a mane", "the lion roars", "the lion lives in africa"):
        parse(g, s, banks)
        assert not g.nodes_with_key(FRESH), "the FRESH delta must not outlive its utterance"


def test_unparsed_marks_do_not_survive_a_parse(banks):
    """Same contract as `test_fresh_marks_do_not_survive_a_parse`, for the TOKEN delta -- plus the
    trap that is specific to it.

    `FRESH` is written by a rule at the end of a successful parse, so it can only leak on the happy
    path. `UNPARSED` is written BEFORE the first bank runs, and `parse` can return REFUSED or
    AMBIGUOUS from the middle of the pipeline -- so it has to be retired on EVERY exit path, which is
    why `parse` clears it in a `finally`. A refused sentence that left its tokens marked would
    silently enlarge the seed set of every later parse: the exact failure mode this delta exists to
    remove, reintroduced by an early return."""
    from ugm.cnl.grammar import UNPARSED
    g = AttrGraph()
    assert parse(g, "glorp the flarn", banks)[0] == REFUSED
    assert not g.nodes_with_key(UNPARSED), "a REFUSED parse must still retire the token delta"
    assert parse(g, "the lion has a mane", banks)[0] == PARSED
    assert not g.nodes_with_key(UNPARSED), "the UNPARSED delta must not outlive its utterance"


def test_the_token_delta_skips_no_work(banks):
    """The chart/usefulness/span banks are seeded on the new sentence's TOKENS, and that is sound
    only because a span never crosses a sentence -- every derivation a parse can add BEGINS at a
    token of that sentence.

    If it ever stops holding, a later sentence gets LESS chart than the same sentence parsed alone.
    This is the token-level counterpart of `test_the_fresh_delta_skips_no_work`, and it is a
    separate test because the two deltas are seeded on different layers: that one could pass while
    this one fails (spans built, tree not), and vice versa."""
    def _span_count(g):
        return sum(1 for n in g.nodes() if g.has_key(n, "cat"))

    alone = AttrGraph()
    assert parse(alone, "the lion lives in africa", banks)[0] == PARSED
    expected = _span_count(alone)
    assert expected, "the sentence must materialize spans at all"

    session = AttrGraph()
    parse(session, "the lion has a mane", banks)
    parse(session, "the lion roars", banks)
    before = _span_count(session)
    assert parse(session, "the lion lives in africa", banks)[0] == PARSED
    assert _span_count(session) - before == expected


def test_the_fresh_delta_skips_no_work(banks):
    """Seeding decompositions on FRESH must not make a later sentence get LESS structure.

    The delta is sound only because a span never crosses a sentence boundary. If that ever stops
    holding, this is where it shows: the same sentence must materialize the same parse tree whether
    it is parsed alone or as the third utterance of a session."""
    alone = AttrGraph()
    assert parse(alone, "the lion lives in africa", banks)[0] == PARSED
    expected = _dec_count(alone)
    assert expected, "the sentence must materialize decompositions at all"

    session = AttrGraph()
    parse(session, "the lion has a mane", banks)
    parse(session, "the lion roars", banks)
    before = _dec_count(session)
    assert parse(session, "the lion lives in africa", banks)[0] == PARSED
    assert _dec_count(session) - before == expected


# ---------------------------------------------------------------------------
# THE OPEN-VOCABULARY DEFAULT IS FOR *UNDECLARED* WORDS
# ---------------------------------------------------------------------------

_LOUDON = pathlib.Path(__file__).resolve().parent.parent / "corpus" / "loudon_grammar.cnl"


def _open_banks(extra: str = ""):
    from ugm.cnl.grammar import compile_grammar, load_grammar
    return compile_grammar(load_grammar(_LOUDON.read_text(encoding="utf-8") + extra),
                           open_class="noun")


def _outcome(sentence: str, banks) -> str:
    from ugm.attrgraph import AttrGraph
    from ugm.cnl.grammar import parse
    g = AttrGraph()
    return parse(g, sentence, banks)[0]


def test_opening_the_vocabulary_does_not_make_declared_words_ambiguous():
    """⭐ THE BLOCKER FOR MAKING THE GRAMMAR ROUTE THE DEFAULT INTAKE PATH, and it was found by
    measuring that migration rather than by any parse failure.

    The open-class default used to exclude only `CLOSED_CLASSES`, so a word declared `adj` was STILL
    eligible as an open noun — two categories, two readings. Opening the vocabulary therefore
    MANUFACTURED ambiguity in sentences that already parsed, and an ambiguous utterance commits
    NOTHING. Measured on the shipped corpus before the fix: `the lion is strong` went from `parsed`
    (closed vocabulary) to `ambiguous`. So the grammar did not degrade gracefully as vocabulary grew
    — it degraded into silence, and the two ways to widen coverage pulled against each other."""
    banks = _open_banks()
    assert _outcome("the lion is strong", banks) == PARSED
    assert _outcome("the african lion is strong", banks) == PARSED


def test_the_open_default_still_refuses_gibberish():
    """Refusal must survive the open vocabulary — otherwise the default is just 'accept everything'."""
    banks = _open_banks()
    for junk in ("glorp the flarn", "flarn glorp zibble"):
        assert _outcome(junk, banks) == REFUSED


def test_a_word_needing_two_categories_must_DECLARE_both():
    """THE TRADE, pinned in both directions — the capability is not lost, it MOVED to a declaration.

    A nominalized adjective (`the strong …`) refuses while `strong` is declared only `adj`, and parses
    once the grammar also says `strong is a noun` — at which point `the lion is strong` becomes
    ambiguous HONESTLY, because the grammar really has said the word is two things. Declaring is how
    a grammar says what a word can be; the default only fills in for words it has not spoken about.

    Note the loss case is a REFUSAL — loud and countable — where the old behaviour's cost was
    silence. That is the direction this project trades in."""
    adj_only = _open_banks()
    assert _outcome("the strong is smaller than the lion", adj_only) == REFUSED

    both = _open_banks("strong is a noun\n")
    assert _outcome("the strong is smaller than the lion", both) == PARSED
    assert _outcome("the lion is strong", both) == AMBIGUOUS, (
        "with two DECLARED categories the ambiguity is earned and must be reported")
