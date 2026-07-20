"""
The intake grammar as CNL DATA, interpreted by generated rules.

Design: `docs/design/homoiconic_grammar.md` (read its §0). Companion:
`docs/design/surface_interpretation.md` for the layer this feeds.

Everything a sentence shape needs is DECLARED in CNL and GENERATES rules — no Python is edited to
add a shape. Six declaration surfaces, of which only the last five are new (the lexicon reuses the
shipped `X is a Y`):

    lion is a noun                                          LEXICON
    np expands to determiner plus np                        PRODUCTION (binary; unary drops `plus Y`)
    slot head in np from determiner plus np is right head   how a parent's slot is filled
    mint head in np from modifier plus np under right head  ... or is a FRESH described entity
    clause asserts subj pred obj unless neg                 which slots become a fact
    clause denies  subj pred obj when   neg                 ... and which become a negative one

A SPAN IS A RELATION, not a node: `a --span_np--> b` runs from the span's first token to the token
just past its last, so composition is a plain two-premise join and the chart is exactly what
"every enabled rule fires, nothing selects" builds. Token-passing IS chart parsing — which is why
ambiguity needs no branch selection (`homoiconic_grammar.md` §8.1).

AMBIGUITY IS DETECTED, NEVER RESOLVED. `ambiguity_bank` runs a top-down USEFULNESS pass (a chart
also holds constituents no complete parse uses, so detecting ambiguity anywhere in it would cry
wolf) and then flags a useful span licensed two ways. No parse -> REFUSE. Two parses -> ASK.

IDENTITY IS MINTED ONLY FOR WHAT SURVIVES: span NODES are created only for USEFUL spans (O(n), not
the whole chart), which is what gives slots somewhere to hang without paying for an unpacked
derivation forest (measured at 4.7 s/11 tokens; see §8.3).
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from functools import lru_cache

from ..production_rule import Band, Distinct, Pat, Rule
from ..lowering import run_bank
from ..possibility import LIKELINESS
from ..vocabulary import INTERPRETS, neg_pred
from ..world_model import Graph
from .forms import _chain_tokens, tokenize

ROOT = "clause"

#: Word classes that are FUNCTION words. NO LONGER GATES the open-vocabulary default — ANY declared
#: category does (see `DECLARED` / `chart_bank`), because gating on function words alone left every
#: declared content word doubling as an open noun. Retained as linguistic data (and used by
#: `bench/spike_homoiconic_grammar.py`); it should itself become a CNL declaration.
CLOSED_CLASSES: tuple[str, ...] = ("determiner", "negator", "comparator", "preposition", "copula")

#: Marks a token the grammar DECLARES something about, gating the open-vocabulary default so it
#: applies only to words the grammar has not spoken about. Was `closed_class`, and the rename is the
#: fix: it used to mark only FUNCTION words, which left every declared content word ALSO eligible as
#: an open noun and so silently ambiguous. See `chart_bank`.
DECLARED = "declared"


#: `has -[neg_of]-> has_not` — the positive/negative predicate pairing, as GRAPH DATA.
#:
#: Exists so a `denies` rule can BIND its negative predicate instead of computing the string
#: `neg_pred(w)` at compile time, which forced ONE RULE PER LEXICON WORD (26 of `assert_bank`'s 61).
#: A PLAIN name, deliberately: a `<...>`-named premise would make `_rule_touches_control` classify
#: every deny rule as control-writing and the fold would produce zero facts while firing correctly
#: (this file's lesson 1). Skipped by entity-side readers via `SURFACE_PREDS`, like `cat`/`begin`.
NEG_OF = "neg_of"


def author_negative_pairing(g, lexicon) -> None:
    """Write `w -[neg_of]-> w_not` for each lexicon word, ONCE per graph.

    The DENY collapse's data half. Authored through the ISA (`load_fact_triples` -> `assemble_facts`
    -> `Machine.run`), not by poking the substrate: intern + dedup make it idempotent, which matters
    because the fold re-runs over the whole graph every utterance.

    Guarded on the key index so it is authored once and then costs an O(1) lookup — the vocabulary is
    static, and re-running a 2N-instruction program per utterance would give back part of what the
    collapse just won."""
    if g.nodes_with_key(NEG_OF):
        return
    from ..lowering import load_fact_triples
    load_fact_triples(g, [(w, NEG_OF, neg_pred(w)) for w in sorted(lexicon)])


def sp(cat: str) -> str:
    """The predicate naming a span of category `cat`."""
    return f"span_{cat}"


# ---------------------------------------------------------------------------
# 1. The declaration surfaces
# ---------------------------------------------------------------------------
#
# Binary + unary productions (Chomsky normal form) is not a limitation of the idea: it is the shape
# that makes composition a two-premise JOIN, i.e. an ordinary rule. A wider production is just more
# premises. The binary and unary shapes need no NAC to tell apart — after the left child a binary
# line has `plus` and a unary line has the next keyword.

PRODUCTION_FORMS: list[Rule] = [
    Rule(
        key="gram.expands.binary",
        lhs=[Pat("?s", "first", "?z"), Pat("?z", "next", "expands?"),
             Pat("expands?", "next", "to?"), Pat("to?", "next", "?x"),
             Pat("?x", "next", "plus?"), Pat("plus?", "next", "?y")],
        rhs=[Pat("<prod>?", "gcat", "?z"), Pat("<prod>?", "gleft", "?x"),
             Pat("<prod>?", "gright", "?y")],
    ),
    Rule(
        key="gram.expands.unary",
        lhs=[Pat("?s", "first", "?z"), Pat("?z", "next", "expands?"),
             Pat("expands?", "next", "to?"), Pat("to?", "next", "?x")],
        nac=[Pat("?x", "next", "?more")],
        rhs=[Pat("<prod>?", "gcat", "?z"), Pat("<prod>?", "gonly", "?x")],
    ),
]

SLOT_FORMS: list[Rule] = [
    Rule(
        key="gram.slot.binary",
        lhs=[Pat("?s", "first", "slot?"), Pat("slot?", "next", "?name"),
             Pat("?name", "next", "in?"), Pat("in?", "next", "?z"),
             Pat("?z", "next", "from?"), Pat("from?", "next", "?x"),
             Pat("?x", "next", "plus?"), Pat("plus?", "next", "?y"),
             Pat("?y", "next", "is?"), Pat("is?", "next", "?side"),
             Pat("?side", "next", "?cslot")],
        rhs=[Pat("<slot>?", "sname", "?name"), Pat("<slot>?", "scat", "?z"),
             Pat("<slot>?", "sleft", "?x"), Pat("<slot>?", "sright", "?y"),
             Pat("<slot>?", "sside", "?side"), Pat("<slot>?", "scslot", "?cslot")],
    ),
    Rule(
        key="gram.slot.unary",
        lhs=[Pat("?s", "first", "slot?"), Pat("slot?", "next", "?name"),
             Pat("?name", "next", "in?"), Pat("in?", "next", "?z"),
             Pat("?z", "next", "from?"), Pat("from?", "next", "?x"),
             Pat("?x", "next", "is?"), Pat("is?", "next", "?side"),
             Pat("?side", "next", "?cslot")],
        rhs=[Pat("<slot>?", "sname", "?name"), Pat("<slot>?", "scat", "?z"),
             Pat("<slot>?", "sonly", "?x"), Pat("<slot>?", "sside", "?side"),
             Pat("<slot>?", "scslot", "?cslot")],
    ),
]

#: `mint <slot> in <cat> from <X> plus <Y> under <side> <childslot>` — the parent's slot is a FRESH
#: NAMELESS entity subsumed by the named child slot. Nameless per the `ByDesc` identity law
#: (feedback #15, "the substrate is supposed to be nameless"): a minted node has no name of its own,
#: only the defining relations it was minted with. See `homoiconic_grammar.md` §10.
MINT_FORMS: list[Rule] = [
    Rule(
        key="gram.mint",
        lhs=[Pat("?s", "first", "mint?"), Pat("mint?", "next", "?name"),
             Pat("?name", "next", "in?"), Pat("in?", "next", "?z"),
             Pat("?z", "next", "from?"), Pat("from?", "next", "?x"),
             Pat("?x", "next", "plus?"), Pat("plus?", "next", "?y"),
             Pat("?y", "next", "under?"), Pat("under?", "next", "?side"),
             Pat("?side", "next", "?cslot")],
        rhs=[Pat("<mint>?", "mname", "?name"), Pat("<mint>?", "mcat", "?z"),
             Pat("<mint>?", "mleft", "?x"), Pat("<mint>?", "mright", "?y"),
             Pat("<mint>?", "mside", "?side"), Pat("<mint>?", "mcslot", "?cslot")],
    ),
]


#: `HEDGE means NUMBER` — the band a hedge word denotes, e.g. `generally means 0.7`.
#:
#: DECLARED IN THE GRAMMAR because the band has to be a COMPILE-TIME constant: `assert_bank` emits
#: one rule per hedge word so the degree is a literal in the rule's `Band`, with no runtime numeric
#: lookup (the same per-word expansion `deny` already uses). Deliberately the SAME SURFACE as the
#: KB-level hedge lexicon (`uncertainty.parse_hedge_decl`, `HEDGE means NUMBER`) so there is one
#: syntax for "what degree does this word mean", not two.
HEDGE_BAND_FORMS: list[Rule] = [
    Rule(
        key="gram.hedgeband",
        lhs=[Pat("?s", "first", "?w"), Pat("?w", "next", "means?"),
             Pat("means?", "next", "?n")],
        rhs=[Pat("<hb>?", "hword", "?w"), Pat("<hb>?", "hband", "?n")],
    ),
]


#: `<cat> hedges under <slot>` — which slot of this category carries the hedge WORD.
#:
#: A PROPERTY OF THE CATEGORY, not of each assertion, and that is what makes the hedged forms
#: complete. The first version took the band from the assertion's own `when` guard
#: (`hclause hedges subj pred obj when hedge`), which works for the shapes that need no other
#: guard — and SILENTLY EXCLUDES the ones that do. The declaration surface allows ONE guard, so the
#: hedged INTRANSITIVE (`… subj pred true unless obj`) and PREPOSITIONAL (`… subj prep pobj when
#: pobj`) could not be written at all, and their sentences parsed while committing nothing.
#: Declaring the hedge slot once frees every assertion's guard for its own job.
HEDGE_SLOT_FORMS: list[Rule] = [
    Rule(
        key="gram.hedgeslot",
        lhs=[Pat("?s", "first", "?z"), Pat("?z", "next", "hedges?"),
             Pat("hedges?", "next", "under?"), Pat("under?", "next", "?slot")],
        rhs=[Pat("<hu>?", "hucat", "?z"), Pat("<hu>?", "huslot", "?slot")],
    ),
]

#: `<cat> suppresses` — spans this category dominates do not assert (see `SUPPRESSED`).
SUPPRESS_FORMS: list[Rule] = [
    Rule(
        key="gram.suppresses",
        lhs=[Pat("?s", "first", "?z"), Pat("?z", "next", "suppresses?")],
        nac=[Pat("suppresses?", "next", "?more")],
        rhs=[Pat("<sup>?", "supcat", "?z")],
    ),
]


def _assert_forms() -> list[Rule]:
    """`<cat> asserts|denies|hedges A B C [when|unless G]` — nine shapes, generated over the three
    verbs and the three guard shapes rather than written out.

    `hedges` is the possibilistic verb: the triple is written in PENCIL behind a fork banded by the
    guard slot's hedge word, so a hedged sentence commits no INK. It is a VERB and not a flavour of
    `asserts` for the same reason `denies` is one — the three differ in what they commit, which is
    exactly what a declaration should say."""
    forms: list[Rule] = []
    for verb, mode in (("asserts", "assert"), ("denies", "deny"), ("hedges", "hedge"),
                       ("asks", "ask"), ("intends", "goal")):
        head = [Pat("?s", "first", "?z"), Pat("?z", "next", f"{verb}?"),
                Pat(f"{verb}?", "next", "?a"), Pat("?a", "next", "?b"), Pat("?b", "next", "?c")]
        core = [Pat("<ass>?", "acat", "?z"), Pat("<ass>?", "amode", mode),
                Pat("<ass>?", "asubj", "?a"), Pat("<ass>?", "apred", "?b"),
                Pat("<ass>?", "aobj", "?c")]
        forms.append(Rule(key=f"gram.{verb}.bare", lhs=head,
                          nac=[Pat("?c", "next", "?more")], rhs=core))
        for guard, key in (("when", "awhen"), ("unless", "aunless")):
            forms.append(Rule(
                key=f"gram.{verb}.{guard}",
                lhs=[*head, Pat("?c", "next", f"{guard}?"), Pat(f"{guard}?", "next", "?g")],
                rhs=[*core, Pat("<ass>?", key, "?g")]))
    return forms


ASSERT_FORMS: list[Rule] = _assert_forms()

#: Every declaration form, for loading a grammar file.
DECLARATION_FORMS: list[Rule] = (PRODUCTION_FORMS + SLOT_FORMS + MINT_FORMS + ASSERT_FORMS
                                 + HEDGE_BAND_FORMS + HEDGE_SLOT_FORMS + SUPPRESS_FORMS)

_DECL_KEYS = ("sname", "scat", "sleft", "sright", "sonly", "sside", "scslot",
              "acat", "amode", "asubj", "apred", "aobj", "awhen", "aunless",
              "mname", "mcat", "mleft", "mright", "mside", "mcslot",
              "hword", "hband", "supcat", "hucat", "huslot")


# ---------------------------------------------------------------------------
# 2. Reading a declared grammar back out (a §8 reader, like `declared_relations`)
# ---------------------------------------------------------------------------

@dataclass
class Grammar:
    """A grammar, as read back from its CNL declarations."""
    lexicon: dict[str, list[str]] = field(default_factory=dict)
    unary: list[tuple[str, str]] = field(default_factory=list)
    binary: list[tuple[str, str, str]] = field(default_factory=list)
    slots: list[dict] = field(default_factory=list)
    assertions: list[dict] = field(default_factory=list)
    mints: list[dict] = field(default_factory=list)
    #: hedge word -> the band it denotes (`generally means 0.7`). Overlays the shipped
    #: `uncertainty.HEDGE_BAND` defaults, exactly as `uncertainty.hedge_bands` overlays them for a KB.
    hedge_bands: dict[str, float] = field(default_factory=dict)
    #: categories that SUPPRESS assertion in everything they dominate (`ccl suppresses`).
    suppressing: set[str] = field(default_factory=set)
    #: category -> the slot carrying its hedge WORD (`hclause hedges under hedge`). Declared once
    #: per category so each hedged assertion's own `when`/`unless` guard stays free.
    hedge_slots: dict[str, str] = field(default_factory=dict)

    @property
    def categories(self) -> set[str]:
        return ({z for z, _ in self.unary} | {z for z, *_ in self.binary}
                | {x for _, x in self.unary}
                | {x for _, a, b in self.binary for x in (a, b)} | {ROOT})

    @property
    def slot_names(self) -> set[str]:
        return {d["sname"] for d in self.slots} | {d["mname"] for d in self.mints} | {"head"}


@lru_cache(maxsize=32)
def _parse_grammar(body: str) -> Grammar:
    """Comment-stripped declaration text -> `Grammar`. PURE, hence cacheable.

    THE EXPENSIVE HALF, AND BY A LONG WAY. Profiled 2026-07-20: 1424 ms for the 124-line Loudon
    grammar against `compile_grammar`'s 13 ms (108×) — i.e. loading a grammar cost MORE THAN AN
    ENTIRE 8-SENTENCE SESSION (1.39 s). The cost is `load_facts` running the 17 declaration forms
    over the whole graph on the naive `run_bank` (863k matcher steps), which is the documented
    whole-graph-bank shape and NOT fixed here.

    Cached instead, because the same static grammar file is re-read constantly: measured **47 calls
    totalling 59.2 s** across the two grammar test modules alone — 63% of their runtime spent
    re-parsing two unchanging files. Bounded (`maxsize`) rather than unbounded: callers can generate
    grammars programmatically (benches and probes do), and an unbounded text-keyed cache would be a
    leak."""
    from ..attrgraph import AttrGraph
    from .authoring import load_facts
    g = AttrGraph()
    load_facts(g, body, extra_forms=DECLARATION_FORMS)
    return read_grammar(g)


def load_grammar(text: str) -> Grammar:
    """Load CNL grammar declarations and read the grammar back out of the resulting graph.

    `#` comments are stripped, matching every other CNL file loader (`load_machine_rules`,
    `load_kb`, intake) — `load_facts` itself does not strip them.

    ⚠ RETURNS A COPY, AND THAT IS LOAD-BEARING, NOT HYGIENE. `Grammar` is MUTABLE and is mutated in
    normal operation: `grammar_intake.sync_vocabulary` adds each of a KB's declared relations to
    `lexicon` as the session runs. Handing out the cached instance would let one KB's derived
    vocabulary appear in every other KB built from the same file — a cross-contamination bug that
    would surface as "a word parses in a test only when some earlier test ran", i.e. order-dependent
    and silent. The copy is what makes caching a pure optimization."""
    body = "\n".join(s for line in text.splitlines()
                     if (s := line.strip()) and not s.startswith("#"))
    return deepcopy(_parse_grammar(body))


def load_grammar_file(*paths) -> Grammar:
    """Load a grammar from one or more `.cnl` files (multi-file, like `load_kb`)."""
    import pathlib
    return load_grammar("\n".join(pathlib.Path(p).read_text(encoding="utf-8") for p in paths))


def read_grammar(g) -> Grammar:
    """Read a `Grammar` out of a graph the declaration forms have already run over.

    THE KEY INDEX DECIDES WHICH RELATIONS TO LOOK AT, rather than probing every relation for every
    declaration key. Profiled 2026-07-20: this function made **3,278,010 `has_key` calls** on the
    124-line Loudon grammar — 30 candidate keys against every relation in the graph — and its cost
    grew 122× for 8.3× more input (3.9 ms at 15 lines, 476 ms at 124), i.e. QUADRATIC in a plain
    Python sweep rather than in any bank. `nodes_with_key` is O(1) off an always-maintained index, so
    the candidate sets below turn the 30-key probe into a set membership test and it is only paid on
    relations that actually carry a declaration.

    ITERATION ORDER IS DELIBERATELY UNCHANGED — still `g.nodes()` then `relations_from`, with
    non-candidates skipped. `slot_bank`/`assert_bank` derive RULE KEYS from list POSITION
    (`fold.slot.{i}`), so reordering `gram.slots` would silently rename every generated rule."""
    gram = Grammar()
    decl_keys = ("gcat", "gleft", "gright", "gonly", *_DECL_KEYS)
    isa_rels = set(g.nodes_with_key("is_a"))
    decl_rels: set[str] = set()
    for k in decl_keys:
        decl_rels.update(g.nodes_with_key(k))
    for n in g.nodes():
        for r, o in g.relations_from(n):
            # `<...>` categories are ENGINE bookkeeping riding the same `is_a` predicate the lexicon
            # uses (`mark_mentions` writes `is_a <mention>` on every entity). Reading them as
            # lexicon entries declares every word a `<mention>` and generates a chart rule for it —
            # measured at ~80% of parse runtime before this filter. See `homoiconic_grammar.md` §9.5.
            if r in isa_rels and not g.name(o).startswith("<"):
                gram.lexicon.setdefault(g.name(n), []).append(g.name(o))
    seen_u, seen_b = set(), set()
    for n in g.nodes():
        d = {}
        for r, o in g.relations_from(n):
            if r not in decl_rels:
                continue
            for k in decl_keys:
                if g.has_key(r, k):
                    d[k] = g.name(o)
        if "gcat" in d and "gonly" in d:
            if (d["gcat"], d["gonly"]) not in seen_u:
                seen_u.add((d["gcat"], d["gonly"]))
                gram.unary.append((d["gcat"], d["gonly"]))
        elif "gcat" in d and "gleft" in d and "gright" in d:
            key = (d["gcat"], d["gleft"], d["gright"])
            if key not in seen_b:
                seen_b.add(key)
                gram.binary.append(key)
        elif "sname" in d:
            gram.slots.append(d)
        elif "mname" in d:
            gram.mints.append(d)
        elif "acat" in d:
            gram.assertions.append(d)
        elif "hucat" in d and "huslot" in d:
            gram.hedge_slots[d["hucat"]] = d["huslot"]
        elif "supcat" in d:
            gram.suppressing.add(d["supcat"])
        elif "hword" in d and "hband" in d:
            try:                                   # a non-numeric band is not a declaration
                v = float(d["hband"])
            except ValueError:
                continue
            if 0.0 < v <= 1.0:                     # same admissible range as `parse_hedge_decl`
                gram.hedge_bands[d["hword"]] = v
    gram.unary.sort()
    gram.binary.sort()
    return gram


def hedge_band_of(gram: Grammar, word: str) -> float | None:
    """The band `word` denotes: the grammar's own declarations over the shipped defaults."""
    from .uncertainty import HEDGE_BAND
    if word in gram.hedge_bands:
        return gram.hedge_bands[word]
    return HEDGE_BAND.get(word)


# ---------------------------------------------------------------------------
# 3. Generated banks
# ---------------------------------------------------------------------------

@dataclass
class GrammarBanks:
    """Every bank generated from a `Grammar`, plus the control predicates each writes."""
    chart: list[Rule]
    chart_preds: frozenset[str]
    ambiguity: list[Rule]
    ambiguity_preds: frozenset[str]
    spans: list[Rule]
    span_preds: frozenset[str]
    slots: list[Rule]
    slot_preds: frozenset[str]
    asserts: list[Rule]
    defining_asserts: list[Rule]
    grammar: Grammar
    #: The revision loop's two extra banks (see `remint_mark_bank` / `reinterpretation_slots`).
    remint_marks: list[Rule] = field(default_factory=list)
    remint_preds: frozenset[str] = frozenset()
    reinterp_slots: list[Rule] = field(default_factory=list)
    reinterp_slot_preds: frozenset[str] = frozenset()
    #: The open-vocabulary default these banks were built with, REMEMBERED so a recompile (when the
    #: session's vocabulary grows — `grammar_intake.sync_vocabulary`) reproduces the same grammar
    #: instead of silently dropping open vocabulary.
    open_class: str | None = None


def chart_bank(gram: Grammar, *, open_class: str | None = None) -> tuple[list[Rule], frozenset[str]]:
    """The chart rules: one per lexicon entry, per unary production, per binary production.

    `open_class`: with it set, any token the grammar declares NOTHING about also spans as that
    category — the open-vocabulary default. One rule with a NAC over a DECLARED tag (no hardcoded
    stop-list), REFUSAL SURVIVES IT (gibberish still fails to parse), and cheaper than one lexical
    rule per word. See `homoiconic_grammar.md` §8.4.

    ⭐ THE DEFAULT IS FOR *UNDECLARED* WORDS — NOT AN EXTRA CATEGORY STAPLED ONTO DECLARED ONES
    (fixed 2026-07-20; it used to exclude only `CLOSED_CLASSES`). Under the old rule a word declared
    `adj` was STILL also eligible as an open noun, so it carried two categories and its sentences
    parsed two ways. Measured: with `open_class="noun"` the shipped Loudon corpus dropped from 23/23
    to 21 parsed + **2 AMBIGUOUS** — `the lion is strong` and `the african lion is strong` — and an
    ambiguous utterance commits NOTHING. So opening the vocabulary MANUFACTURED silence in sentences
    that already worked, and the two obvious ways to widen coverage (declare more words / open the
    vocabulary) pulled against each other. This is the blocker for making the grammar route the
    default intake path, found by measuring that migration rather than by a parse failure.

    THE CAPABILITY IS NOT LOST, IT MOVED TO AN EXPLICIT DECLARATION — which is the point.
    `the strong is smaller than the lion` (a nominalized adjective) now REFUSES with `strong`
    declared only `adj`, and parses again once the grammar says `strong is a noun` — at which point
    `the lion is strong` becomes ambiguous HONESTLY, because the grammar really has said the word is
    two things. Declaring is how a grammar says what a word can be; the default only fills in for
    words it has not spoken about. And the loss case is a REFUSAL — loud and countable — where the
    old behaviour's cost was silence.

    MEASURED AFTER: Loudon 23/23 with the vocabulary open, gibberish still refused, closed-vocabulary
    behaviour bit-identical.

    EVERY RULE LEADS WITH `UNPARSED` so the chart is built over the NEW SENTENCE rather than the
    whole session — see that constant for why this is the lever and why it is sound. The mark binds
    the token (or the span's begin token), so each remaining premise is a FOLLOW from a bound
    endpoint instead of a SEED over every `next`/`span_*` node standing in the session."""
    rules: list[Rule] = []
    cats = set(gram.categories)
    for w, cs in sorted(gram.lexicon.items()):
        for c in sorted(cs):
            cats.add(c)
            rules.append(Rule(key=f"chart.lex.{c}.{w}",
                              lhs=[Pat(f"{w}?", UNPARSED, "?up"), Pat(f"{w}?", "next", "?u")],
                              rhs=[Pat(f"{w}?", sp(c), "?u")]))
    if open_class:
        for w, cs in sorted(gram.lexicon.items()):
            if cs:                      # ANY declared category, not merely a closed one — see above
                rules.append(Rule(key=f"chart.declared.{w}",
                                  lhs=[Pat(f"{w}?", UNPARSED, "?up"), Pat(f"{w}?", "next", "?u")],
                                  rhs=[Pat(f"{w}?", DECLARED, "yes")]))
        rules.append(Rule(key=f"chart.open.{open_class}",
                          lhs=[Pat("?t", UNPARSED, "?up"), Pat("?t", "next", "?u")],
                          nac=[Pat("?t", DECLARED, "yes")],
                          rhs=[Pat("?t", sp(open_class), "?u")]))
        cats.add(open_class)
    for z, x in gram.unary:
        rules.append(Rule(key=f"chart.un.{z}.{x}",
                          lhs=[Pat("?a", UNPARSED, "?up"), Pat("?a", sp(x), "?b")],
                          rhs=[Pat("?a", sp(z), "?b")]))
    for z, x, y in gram.binary:
        rules.append(Rule(key=f"chart.bin.{z}.{x}.{y}",
                          lhs=[Pat("?a", UNPARSED, "?up"),
                               Pat("?a", sp(x), "?m"), Pat("?m", sp(y), "?b")],
                          rhs=[Pat("?a", sp(z), "?b")]))
    return rules, frozenset({"next", "first", DECLARED, UNPARSED}
                            | {sp(c) for c in cats})


def ambiguity_bank(gram: Grammar, root: str = ROOT) -> tuple[list[Rule], frozenset[str]]:
    """Detect ambiguity IN THE PACKED CHART, in-engine, with NO branch selection.

    Two generated families, both ordinary rules:

    1. USEFULNESS, top-down: the root span is useful, and a useful span makes the children of every
       production licensing it useful. This is what separates a real ambiguity from a locally
       ambiguous DEAD constituent — a chart holds constituents no complete parse uses.
    2. AMBIGUITY: a USEFUL span licensed two ways — a different split point (`Distinct` on the
       midpoint) or a different production at the same split — is `ambiguous`.

    Counting root spans instead DOES NOT WORK: packing erases derivation identity, so a 3-parse
    sentence reports one root span. The unpacked alternative is correct but costs 4.7 s at 11
    tokens. See `homoiconic_grammar.md` §8.3.

    DELTA-SEEDED ON `UNPARSED` like the chart, and on the same anchor: every rule here is about a
    span, and a span's BEGIN (`?a`) is always a real token of its sentence — never `<eos>`, which
    begins nothing. So leading with the mark on `?a` scopes the whole usefulness pass to the new
    sentence without changing what it derives."""
    delta = [Pat("?a", UNPARSED, "?up")]
    rules: list[Rule] = [
        Rule(key="amb.useful.root",
             lhs=[*delta,
                  Pat("?s", "first", "?a"), Pat("?a", sp(root), "?b"), Pat("?b", "is_eos", "yes")],
             rhs=[Pat("?a", f"useful_{root}", "?b")]),
    ]
    for z, x in gram.unary:
        rules.append(Rule(key=f"amb.down.{z}.{x}",
                          lhs=[*delta, Pat("?a", f"useful_{z}", "?b"), Pat("?a", sp(x), "?b")],
                          rhs=[Pat("?a", f"useful_{x}", "?b")]))
    for z, x, y in gram.binary:
        rules.append(Rule(key=f"amb.down.{z}.{x}.{y}",
                          lhs=[*delta, Pat("?a", f"useful_{z}", "?b"), Pat("?a", sp(x), "?m"),
                               Pat("?m", sp(y), "?b")],
                          rhs=[Pat("?a", f"useful_{x}", "?m"), Pat("?m", f"useful_{y}", "?b")]))
    for i, (z, x, y) in enumerate(gram.binary):
        rules.append(Rule(key=f"amb.split.{z}.{x}.{y}",
                          lhs=[*delta, Pat("?a", f"useful_{z}", "?b"), Pat("?a", sp(x), "?m"),
                               Pat("?m", sp(y), "?b"), Pat("?a", sp(x), "?n"),
                               Pat("?n", sp(y), "?b")],
                          distinct=[Distinct("?m", "?n")],
                          rhs=[Pat("?a", "ambiguous", "?b")]))
        for z2, x2, y2 in gram.binary[i + 1:]:
            if z2 == z:
                rules.append(Rule(key=f"amb.prod.{z}.{x}.{y}.{x2}.{y2}",
                                  lhs=[*delta, Pat("?a", f"useful_{z}", "?b"), Pat("?a", sp(x), "?m"),
                                       Pat("?m", sp(y), "?b"), Pat("?a", sp(x2), "?n"),
                                       Pat("?n", sp(y2), "?b")],
                                  rhs=[Pat("?a", "ambiguous", "?b")]))
        for z2, x2 in gram.unary:
            if z2 == z:
                rules.append(Rule(key=f"amb.mixed.{z}.{x}.{y}.{x2}",
                                  lhs=[*delta, Pat("?a", f"useful_{z}", "?b"), Pat("?a", sp(x), "?m"),
                                       Pat("?m", sp(y), "?b"), Pat("?a", sp(x2), "?b")],
                                  rhs=[Pat("?a", "ambiguous", "?b")]))
    for i, (z, x) in enumerate(gram.unary):
        for z2, x2 in gram.unary[i + 1:]:
            if z2 == z:
                rules.append(Rule(key=f"amb.un.{z}.{x}.{x2}",
                                  lhs=[*delta, Pat("?a", f"useful_{z}", "?b"), Pat("?a", sp(x), "?b"),
                                       Pat("?a", sp(x2), "?b")],
                                  rhs=[Pat("?a", "ambiguous", "?b")]))
    cats = gram.categories | {c for cs in gram.lexicon.values() for c in cs}
    return rules, frozenset({"is_eos", "ambiguous", UNPARSED} | {f"useful_{c}" for c in cats})


def span_bank(gram: Grammar) -> tuple[list[Rule], frozenset[str]]:
    """One span NODE per USEFUL span — the parse, not the chart.

    Deliberately writes NO `head`: a head is already a DENOTATION, and denotation belongs to the
    interpretation layer (`surface_interpretation.md` §2).

    IDEMPOTENT BY NAC. `<span>?` is a BOUND literal: it gets a name but is minted FRESH per firing,
    so re-running this bank over an unchanged graph re-minted every span — 52 nodes per run, turning
    session-long surface accretion QUADRATIC (parsing one sentence five times: +104, +149, +201,
    +253, +305). Every `parse` runs the banks over the WHOLE graph, so every utterance paid to
    re-mint all of the session's earlier spans. The NAC says "unless a span with this cat/begin/end
    already stands", which makes the rule self-guarding and the bank re-runnable. This is the
    structural counterpart of `intern_described`, which fixes exactly this re-minting for minted
    ENTITIES — the same defect, the other layer.

    DELTA-SEEDED ON `UNPARSED` too, and THAT IS A SEPARATE FIX FROM THE NAC ABOVE. The NAC stops the
    re-MINT; it does not stop the re-JOIN, so this bank still walked every `useful_*` span in the
    session on every utterance — measured as the STEEPEST curve of the three surface banks (4.3 →
    179 ms across 7 sentences, 42×) while accreting nothing. Same distinction as
    `decomposition_bank`: idempotency makes accretion flat, the delta makes COST flat. The NAC
    remains, as defence in depth for a re-parse of an already-parsed sentence."""
    return ([Rule(key=f"surf.span.{c}",
                  lhs=[Pat("?a", UNPARSED, "?up"), Pat("?a", f"useful_{c}", "?b")],
                  # NAC premise order matters for the same reason the LHS's does in
                  # `decomposition_bank`: `?s cat c` first has no bound endpoint and SEEDs every
                  # `cat` node in the session, so lead with the boundary token the LHS already bound.
                  nac=[Pat("?s", "begin", "?a"), Pat("?s", "cat", c), Pat("?s", "end", "?b")],
                  # FRESH marks the spans this parse actually minted — the NAC above means that is
                  # exactly the new sentence's spans. `decomposition_bank` SEEDS on it, so the tree
                  # is built over the new sentence instead of the whole session (`clear_fresh`).
                  rhs=[Pat("<span>?", "cat", c), Pat("<span>?", "begin", "?a"),
                       Pat("<span>?", "end", "?b"), Pat("<span>?", FRESH, "<yes>"),
                       Pat("<span>?", UNINTERPRETED, "<yes>")])
             for c in sorted(gram.categories)],
            frozenset({"cat", "begin", "end", FRESH, UNINTERPRETED, UNPARSED}))


#: The materialized parse tree — one node per DECOMPOSITION of a span into its children.
DEC_PREDS = frozenset({"dprod", "dparent", "dleft", "dright", "donly"})

#: Marks a span minted by the CURRENT parse. The semi-naive delta `run_bank` does not have, carried
#: as declared rule structure instead of an engine change (`clear_fresh` retires it per utterance).
FRESH = "<fresh>"

#: Marks a span the INTERPRETATION has not folded yet — the same delta, for the other layer.
#:
#: TWO MARKS, NOT ONE, because the two layers consume the delta at different moments and must clear
#: it at different moments: `FRESH` dies at the end of `parse` (its consumer, `decomposition_bank`,
#: is done), while this one must survive into `interpret` and dies there. Sharing a single mark
#: would couple the two lifecycles and make `parse` unusable on its own. Both are written by the
#: same rule at the same instant (`span_bank`), so nothing is derived twice — only retired twice.
#:
#: REBUILD re-marks EVERY span (`mark_all_spans`), which is exactly what makes "discard and re-read
#: the whole surface" still expressible: the delta is "what to interpret", and for a rebuild that is
#: everything.
UNINTERPRETED = "unfolded"

#: Marks a TOKEN of the sentence currently being parsed — the same delta again, one layer BELOW the
#: spans. `FRESH`/`UNINTERPRETED` hang on span nodes and so can only seed the banks that run once
#: spans exist (`decomposition_bank`, the fold). The three banks that BUILD the spans — `chart_bank`,
#: `ambiguity_bank`, `span_bank` — have no span to seed from, so their delta has to hang on the one
#: thing that exists before them: the tokens `tokenize` just emitted.
#:
#: WHY IT IS THE LEVER. `lower_conj` drives each join from a BOUND endpoint and, with no endpoint
#: bound, SEEDs the whole predicate class — so `?a span_np ?m` seeded EVERY `span_np` in the session
#: and `{w}? next ?u` seeded every `next`. Leading each rule with this mark binds the span's BEGIN
#: token first, and every later premise becomes a FOLLOW from it. Measured: all three banks grew with
#: the session (`span_bank` steepest at 42× over 7 sentences) even though nothing was re-derived.
#:
#: SOUND for the same reason `FRESH` is: a span never crosses a sentence, so every derivation this
#: parse can add BEGINS at a token of this sentence, and all of those are marked. Earlier sentences
#: reached their own fixpoint when they were parsed.
#:
#: PLAIN-NAMED, DELIBERATELY. A `<…>`-named premise turns a fact-writing rule into a control-writing
#: one (`_rule_touches_control`), which is how the fold once produced zero facts while every rule
#: fired. These three banks write control/surface predicates only, so `<…>` would be safe here — but
#: the mark is one edit away from a fact-writing rule at all times, and `unfolded` is the precedent:
#: surface scaffolding with a plain name, listed in `SURFACE_PREDS` so every reader skips it.
UNPARSED = "unparsed"

#: Marks a span whose content must NOT be asserted, because it sits inside a suppressing context.
#:
#: ASSERTION IS GATED BY CONTEXT, NOT BY CATEGORY. The first non-asserting construction (hedging)
#: got its own category, `hclause`, so that `clause asserts …` structurally could not fire on it.
#: That works but DOES NOT COMPOSE: a conditional's two halves genuinely ARE clauses, so giving them
#: a non-asserting category means duplicating every clause production, and an attributed complement
#: needs the same again — each non-asserting context multiplying the grammar. Measured before the
#: fix: `a lion is dangerous when a lion is hungry` parsed, reported `fact`, and wrote
#: `(lion is dangerous)` AND `(lion is hungry)` — two claims the sentence does not make.
#:
#: This mark is the general form: a category DECLARES that it suppresses (`ccl suppresses`), and
#: every span it dominates is marked. The assert rules NAC on it. No engine change is needed because
#: `decomposition_bank` already reifies the parse tree, so domination is an ordinary closure.
#:
#: PLAIN-NAMED, AND THAT IS LOAD-BEARING: `_rule_touches_control` inspects the NAC too, so a
#: `<…>`-named mark here would turn every assert rule into a control-writing one and the fold would
#: produce ZERO facts while firing correctly — the same silent failure that hit the `unfolded` delta.
SUPPRESSED = "suppressed"


def _prod_key(z: str, x: str, y: str | None = None) -> str:
    """A production's identity as a literal, so a slot rule can SEED on it."""
    return f"{z}<-{x}" if y is None else f"{z}<-{x}+{y}"


def decomposition_bank(gram: Grammar) -> tuple[list[Rule], frozenset[str]]:
    """Materialize the parse tree: one `<dec>` node per (parent, children) decomposition.

    WHY THIS EXISTS — it is 88.5% of a session, measured. Every slot rule used to carry the SAME
    6-way parent/left/right join over `cat`/`begin`/`end` (9 premises), and all 32 of them redid it
    from scratch, once per utterance, over the whole standing surface. Deriving each decomposition
    ONCE turns every slot rule into a 4-premise pointer hop seeded on `dprod`.

    WHY A REIFIED NODE AND NOT `?p kidl ?l` / `?p kidr ?r`: the chart is PACKED, so one span can
    have SEVERAL decompositions (that is exactly what ambiguity is). Two flat edge sets would let
    the left child of one reading pair with the right child of another and derive a slot value from
    a tree that was never parsed. The decomposition node keeps a pairing atomic.

    IDEMPOTENT BY NAC, the `span_bank` lesson applied one layer up: `<dec>?` is a BOUND literal, so
    it mints fresh per firing, and this bank runs over the whole graph every utterance. Without the
    self-guard it would re-mint every earlier decomposition each time — quadratic accretion, the
    defect this bank exists to remove.

    This is SURFACE structure (spans and their tree, no denotation), so it runs in `parse` beside
    `span_bank` and never sees the interpretation layer.

    SEEDED ON `FRESH`, WHICH IS WHAT MAKES IT PER-UTTERANCE. `lower_conj` seeds each rule from its
    FIRST pattern, so leading with `?p cat np` seeded EVERY span in the session and then joined —
    the bank was 71.5% of `parse` and `parse` 59% of a session, all of it re-deriving decompositions
    that already stood (the NAC stopped the re-MINT, but the join still ran). Leading with the
    `FRESH` mark instead seeds only the spans this parse minted. This is the semi-naive delta
    `run_bank` explicitly does not have ("Naive — no semi-naive delta / df-seeding"), carried as
    DECLARED rule structure rather than an engine change.

    SOUND because a span never crosses a sentence: spans are bounded by `begin`/`end` within one
    token chain, so a decomposition of a new span can only involve other spans of the SAME sentence,
    which are fresh too. The NAC stays as defence in depth (re-parsing a sentence re-marks spans
    whose decompositions already stand).

    AND THE PREMISE ORDER MATTERS AS MUCH AS THE SEED — the delta alone left this bank still growing
    with the session (27.7 → 86 ms over 7 sentences) and the biggest stage in `parse`. `lower_conj`
    drives a join from a BOUND endpoint and otherwise SEEDs the whole predicate class, so leading a
    child with `?l cat np` seeded EVERY `cat` node in the session and then filtered. Reaching the
    child from the boundary token instead (`?l begin ?a`, which FOLLOWs from the already-bound `?a`)
    starts from the handful of spans at that position. The conjunction is IDENTICAL either way —
    this is join order, not semantics — which is exactly what makes it easy to regress silently."""
    fresh = [Pat("?p", FRESH, "?fr")]
    rules: list[Rule] = []
    for z, x, y in sorted(set(gram.binary)):
        rules.append(Rule(
            key=f"surf.dec.{z}.{x}.{y}",
            # PREMISE ORDER IS LOAD-BEARING (see the join-order note in the docstring): reach each
            # child from the boundary token already bound, never by its category.
            lhs=[*fresh,
                 Pat("?p", "cat", z), Pat("?p", "begin", "?a"), Pat("?p", "end", "?b"),
                 Pat("?l", "begin", "?a"), Pat("?l", "cat", x), Pat("?l", "end", "?m"),
                 Pat("?r", "begin", "?m"), Pat("?r", "cat", y), Pat("?r", "end", "?b")],
            nac=[Pat("?d", "dparent", "?p"), Pat("?d", "dleft", "?l"), Pat("?d", "dright", "?r")],
            rhs=[Pat("<dec>?", "dprod", _prod_key(z, x, y)), Pat("<dec>?", "dparent", "?p"),
                 Pat("<dec>?", "dleft", "?l"), Pat("<dec>?", "dright", "?r")]))
    for z, x in sorted(set(gram.unary)):
        rules.append(Rule(
            key=f"surf.dec.{z}.{x}",
            lhs=[*fresh,
                 Pat("?p", "cat", z), Pat("?p", "begin", "?a"), Pat("?p", "end", "?b"),
                 Pat("?q", "begin", "?a"), Pat("?q", "cat", x), Pat("?q", "end", "?b")],
            nac=[Pat("?d", "dparent", "?p"), Pat("?d", "donly", "?q")],
            rhs=[Pat("<dec>?", "dprod", _prod_key(z, x)), Pat("<dec>?", "dparent", "?p"),
                 Pat("<dec>?", "donly", "?q")]))
    return rules, DEC_PREDS | {FRESH}


def suppression_bank(gram: Grammar) -> tuple[list[Rule], frozenset[str]]:
    """Mark every span DOMINATED by a declared suppressing category (see `SUPPRESSED`).

    A base case per child edge (a direct child of a suppressing span) plus a transitive case (a
    direct child of an already-suppressed span) — an ordinary closure over the reified parse tree,
    which is exactly why this needs no engine change. It is SURFACE (it reads `cat` and the
    decomposition tree, never a denotation), so it runs in `parse` beside `decomposition_bank`.

    IDEMPOTENT BY NAC (`unless already suppressed`), and DELTA-SEEDED on `FRESH` for the same
    reason `decomposition_bank` is: without the seed the closure re-walks every suppressed span in
    the session on every utterance. SOUND on the same argument — a span's dominators are spans of
    the same sentence, which are fresh too. Premise order is the join plan: `?p` is bound by the
    mark first, so `cat` / `dparent` / the child edge are all FOLLOWs from a bound endpoint."""
    cats = sorted(gram.suppressing)
    if not cats:
        return [], frozenset()
    rules: list[Rule] = []
    fresh = [Pat("?p", FRESH, "?fr")]
    guard = [Pat("?c", SUPPRESSED, "?s")]
    for edge in ("dleft", "dright", "donly"):
        for c in cats:
            rules.append(Rule(
                key=f"surf.supp.{c}.{edge}",
                lhs=[*fresh, Pat("?p", "cat", c), Pat("?d", "dparent", "?p"), Pat("?d", edge, "?c")],
                nac=guard, rhs=[Pat("?c", SUPPRESSED, "<yes>")]))
        rules.append(Rule(
            key=f"surf.supp.trans.{edge}",
            lhs=[*fresh, Pat("?p", SUPPRESSED, "?y"), Pat("?d", "dparent", "?p"),
                 Pat("?d", edge, "?c")],
            nac=guard, rhs=[Pat("?c", SUPPRESSED, "<yes>")]))
    return rules, frozenset({SUPPRESSED})


def clear_fresh(g) -> int:
    """Retire the `FRESH` marks once the tree is built. Returns how many went.

    The mark is a per-utterance delta, so it MUST NOT survive the utterance: left standing, the seed
    set grows with the session and the optimization silently undoes itself (the whole point is that
    the seed stays small). O(marked), via the key index — not a graph sweep, which would reintroduce
    the per-utterance whole-graph cost this exists to remove."""
    return _retire_mark(g, FRESH)


def mark_tokens(g, toks) -> int:
    """Mark this sentence's tokens `UNPARSED` — the seed for the three surface banks.

    Written from Python rather than derived by a rule because it is the delta's BASE CASE: it must
    exist before the first bank runs, and the tokens are exactly what `tokenize` just returned.
    Guarded so re-parsing a sentence does not stack duplicate marks."""
    marked = 0
    yes = g.add_node("<yes>", control=True)
    for t in toks:
        if not any(g.has_key(r, UNPARSED) for r, _o in g.relations_from(t)):
            g.add_relation(t, UNPARSED, yes, control=True)
            marked += 1
    return marked


def clear_unparsed(g) -> int:
    """Retire the token delta once the spans are built. Same contract as `clear_fresh`, same silent
    failure mode — and one extra trap: `parse` can return REFUSED before the banks finish, so this
    has to run on EVERY exit path, not just the successful one (hence the `try/finally` there).
    A refused sentence that left its tokens marked would enlarge every later parse's seed set."""
    return _retire_mark(g, UNPARSED)


def clear_uninterpreted(g) -> int:
    """Retire the interpretation delta once `interpret` has folded it. Same contract as
    `clear_fresh`, and the same silent-failure mode: leave these standing and every answer is still
    right, the seed set just grows with the session until the delta buys nothing."""
    return _retire_mark(g, UNINTERPRETED)


def _retire_mark(g, key: str) -> int:
    """Drop every relation node carrying `key`. O(marked) via the key index — NOT a graph sweep,
    which would reintroduce the per-utterance whole-graph cost these marks exist to remove.

    DELETES VIA THE GATED `SWEEP` OPCODE, not a raw `remove_node`: control-node deletion is an ISA
    privilege (the lowering-compliance pass), and every other driver that retires scaffolding
    (`focus`, `dispatch`, `possibility`) goes through it. Not box-ticking — `SWEEP` REFUSES a fact or
    provenance node, so if a delta mark ever lands somewhere it should not, this fails LOUDLY instead
    of quietly deleting content. The marks are born control (`add_relation(..., control=True)`), so
    the gate passes by construction."""
    from ..machine import Machine, SWEEP, State
    doomed = [r for r in g.nodes_with_key(key) if r in g.nodes()]
    if doomed:
        Machine().apply(g, [SWEEP(f"_n{i}") for i in range(len(doomed))],
                        State({f"_n{i}": n for i, n in enumerate(doomed)}))
    return len(doomed)


def mark_all_spans(g) -> int:
    """Mark EVERY standing span uninterpreted — what a REBUILD means, expressed as the delta.

    `reinterpret` discards the live interpretation and re-reads the whole standing surface; with the
    fold now seeded on `UNINTERPRETED`, "the whole standing surface" is spelled "mark all of it".
    So rebuild and extend run the SAME banks and differ only in how much they mark, which is what
    keeps the two paths from drifting apart."""
    marked = 0
    yes = g.add_node("<yes>", control=True)
    for s in list(g.nodes_with_key("cat")):
        for span in list(g.into(s)):                  # `cat` hangs on a rel node; its subject is the span
            if not any(g.has_key(r, UNINTERPRETED) for r, _o in g.relations_from(span)):
                g.add_relation(span, UNINTERPRETED, yes, control=True)
                marked += 1
    return marked


def slot_bank(gram: Grammar) -> tuple[list[Rule], frozenset[str]]:
    """A percolation rule per declared slot, plus a minting rule per declared `mint`.

    Reads the materialized parse tree (`decomposition_bank`), so each rule is a seek on `dprod` plus
    two pointer hops — not the 6-way `begin`/`end` join it used to redo per rule."""
    rules: list[Rule] = []
    for i, d in enumerate(gram.slots):
        s, z, cs = d["sname"], d["scat"], d["scslot"]
        prem, src = _production_lhs(d)
        rules.append(Rule(key=f"fold.slot.{i}.{z}.{s}",
                          lhs=[*prem, Pat(src, cs, "?v")],
                          rhs=[Pat("?p", s, "?v")]))
    for i, d in enumerate(gram.mints):
        side = "dleft" if d["mside"] == "left" else "dright"
        rules.append(Rule(
            key=f"fold.mint_entity.{i}.{d['mcat']}",
            lhs=[Pat("?p", UNINTERPRETED, "?u"),
                 Pat("?d", "dparent", "?p"),
                 Pat("?d", "dprod", _prod_key(d["mcat"], d["mleft"], d["mright"])),
                 Pat("?d", side, "?c"), Pat("?c", d["mcslot"], "?v")],
            # `?e` is an RHS-only variable, which is what makes it NAMELESS: `lower_rhs` gives a
            # bound literal a name and a plain literal graph-wide interning, but a bare `?e` mints
            # an unnamed node per firing. That is the `ByDesc` identity law.
            rhs=[Pat("?e", "is_a", "?v"), Pat("?p", d["mname"], "?e")]))
    return rules, frozenset(gram.slot_names)


def assert_bank(gram: Grammar, *, defining: bool | None = None) -> list[Rule]:
    """A fact-emitting rule per assertion declaration.

    `defining` splits the bank by whether an assertion contributes to a minted entity's IDENTITY —
    i.e. whether its category is one that MINTS. `np asserts head is attr` is defining (it says what
    the minted subkind IS); `clause asserts subj is adjc` is not (it says something ABOUT it).

    The split exists because both write the predicate `is`, so a description keyed on predicate
    NAMES cannot tell them apart — and `the african lion is strong` then described an entity as
    `<is african & is strong & is_a lion>`, which failed to intern with `<is african & is_a lion>`
    from another sentence. **Identity must be settled before predication**: run the defining
    assertions, intern by description, and only then say things about the entities. Found on the
    Loudon corpus (`homoiconic_grammar.md` §12).

    The PREDICATE position reads as a SLOT if it names a declared slot, else as a literal word —
    data-driven, not string-sniffing. A slot predicate is DYNAMIC, and the ISA rejects a non-plain
    RHS predicate (`lower_rhs`: "RHS non-plain predicate is a later slice"), so it generates one
    rule per lexicon word. That is exactly `relation_forms`' existing discipline — declare the
    relation and a form is generated for it — and it means open vocabulary works for ENTITIES but
    not for PREDICATES, the same controlled-CNL boundary the project already draws."""
    rules: list[Rule] = []
    names = gram.slot_names
    minting = {d["mcat"] for d in gram.mints}
    for i, d in enumerate(gram.assertions):
        z, mode = d["acat"], d["amode"]
        subj, pred, obj = d["asubj"], d["apred"], d.get("aobj")
        if obj is None:
            continue
        if mode in ("ask", "goal"):
            # ⭐ FORCE, not content: these COMMIT NO FACT, so it generates no fact rule at all.
            # The declaration still records WHICH SLOTS carry the asked triple, and the ROUTER reads
            # them (`grammar_intake.question_of`). This is the `<cat> asks subj pred obj` half of the
            # force axis (`design/form_inventory.md` §4b): `asserts`/`denies`/`hedges` differ in what
            # they commit, and `asks` commits nothing — which is a difference in force, exactly what
            # a declaration verb is for. `intends` is the same shape one step along: it commits no
            # fact either, but unlike a question it LEAVES SOMETHING BEHIND (a `<goal>` node driving
            # the act loop), so the router reifies rather than merely answering.
            continue
        if defining is not None and (z in minting) != defining:
            continue
        guards = [Pat("?p", d["awhen"], "?gw")] if "awhen" in d else []
        nacs = [Pat("?p", d["aunless"], "?gu")] if "aunless" in d else []
        # CONTEXT GATE: a span inside a suppressing context asserts nothing, whatever its category
        # says (see `SUPPRESSED`). Added only when some category actually suppresses, so a grammar
        # that declares none pays no extra premise.
        if gram.suppressing:
            nacs = [*nacs, Pat("?p", SUPPRESSED, "?sup")]
        # Led by the mark, so an assert rule seeds the new sentence's spans rather than every span
        # carrying `cat` (see `_production_lhs` on premise order being the join plan).
        base = [Pat("?p", UNINTERPRETED, "?u"), Pat("?p", "cat", z), Pat("?p", subj, "?s"), *guards]
        obj_prem, obj_tok = ([Pat("?p", obj, "?o")], "?o") if obj in names else ([], obj)
        if mode == "hedge":
            rules.extend(_hedge_rules(gram, i, d, z, base, obj_prem, obj_tok, pred, names, nacs))
        elif pred in names and mode != "deny":
            # ONE rule, with the predicate as an LHS-bound VARIABLE — the slot's filler names the
            # predicate, resolved at apply time by the dynamic-key MINT (`lower_rhs`/`MINT.key_reg`).
            rules.append(Rule(key=f"fold.assert.{i}.{z}",
                              lhs=[*base, Pat("?p", pred, "?w"), *obj_prem],
                              nac=nacs, rhs=[Pat("?s", "?w", obj_tok)]))
        elif pred in names:
            # ⭐ THE DENY COLLAPSE (2026-07-20): ONE rule, not one per lexicon word.
            #
            # This used to expand per word because the head predicate is `neg_pred(?w)` — a STRING
            # derivation from the matched word — and the ISA has no string ops. The fix is the one
            # this file predicted: put the positive/negative pairing in the GRAPH as data
            # (`has -[neg_of]-> has_not`, authored by `author_negative_pairing`) so the rule BINDS
            # the negative instead of computing it. `?wn` is then an ordinary LHS-BOUND predicate
            # variable, which `lower_rhs`/`MINT.key_reg` already support (the second step-4 lever).
            #
            # The vocabulary is now DATA (one fact per word, minted once per session, interned and
            # deduped) rather than RULES (matched every round of every fixpoint). That is the whole
            # saving: facts are looked up, rules are re-matched.
            # ⚠ THE PAIRING IS ON THE SURFACE TOKEN, SO THE RULE HOPS BACK ACROSS THE LAYER.
            # `?w` is an ENTITY (the `pred` slot is filled through `HEAD_BRIDGE`, which resolves a
            # one-token span's head to what its token DENOTES). `author_negative_pairing` interns by
            # NAME, and the token was created first, so the `neg_of` edge lands on the TOKEN — the
            # token/entity duality again, one layer along from the `resolve_write_node` fix. Rather
            # than duplicate the pairing onto entities that are minted per session, the rule reaches
            # the surface explicitly via `interprets` (the entity's own provenance to its mention).
            # This keeps the vocabulary where it belongs — on the permanent surface record, authored
            # once — instead of inside the discardable interpretation.
            rules.append(Rule(key=f"fold.assert.{i}.{z}.deny",
                              lhs=[*base, Pat("?p", pred, "?w"),
                                   Pat("?w", INTERPRETS, "?t"), Pat("?t", NEG_OF, "?wn"),
                                   *obj_prem],
                              nac=nacs, rhs=[Pat("?s", "?wn", obj_tok)]))
        else:
            p = neg_pred(pred) if mode == "deny" else pred
            rules.append(Rule(key=f"fold.assert.{i}.{z}.{p}",
                              lhs=[*base, *obj_prem], nac=nacs, rhs=[Pat("?s", p, obj_tok)]))
    return rules


def _hedge_rules(gram: Grammar, i: int, d: dict, z: str, base, obj_prem, obj_tok,
                 pred: str, names, nacs) -> list[Rule]:
    """`<cat> hedges subj pred obj when hedge` — the triple in PENCIL behind a banded fork.

    ONE RULE PER HEDGE WORD, which is what makes the band a COMPILE-TIME literal: the guard slot is
    pinned to a specific word (`Pat("?p", guard, "generally?")`) so that rule's `Band` carries that
    word's degree directly. The alternative — one rule reading the degree at apply time — would need
    a numeric lookup the ISA has no operation for. This is exactly the expansion `deny` already
    does, and the cost is the same shape: bounded by the DECLARED hedge vocabulary (4 words here),
    not by the lexicon.

    A hedged clause writes NO ink: `Band.scope` pens the head, so the relation is a control node
    tagged into the fork (`suppose._pencil`'s shape). The band readers see it at its degree;
    the certain layer does not see it at all.

    A hedge with no declared band is SKIPPED rather than defaulted — a silent 0.5 for a word nobody
    scaled would be inventing a degree, and `declare_grammar`'s loudness rule says a malformed
    declaration must not pass quietly.

    THE BAND SLOT COMES FROM THE CATEGORY (`hclause hedges under hedge`), NOT from this assertion's
    guard. Taking it from the guard silently excluded every hedged shape that needs a guard of its
    own: the declaration surface allows ONE, so the hedged INTRANSITIVE (`unless obj`) and
    PREPOSITIONAL (`when pobj`) were unwritable, and their sentences parsed while committing
    nothing. Found by a cold-context translator reading the declarations — not by the tests, which
    only covered the two shapes that had been built."""
    hslot = gram.hedge_slots.get(z)
    if hslot is None:
        raise ValueError(
            f"`{z} hedges …` needs a `{z} hedges under <slot>` declaration naming the slot that "
            f"carries the hedge word — without it there is no word to take a band from")
    out: list[Rule] = []
    words = sorted({w for w, cs in gram.lexicon.items() if "hedge" in cs} | set(gram.hedge_bands))
    for w in words:
        band = hedge_band_of(gram, w)
        if band is None:
            continue                       # undeclared scale: skip loudly-by-absence, never default
        pred_prem, head_pred = ([Pat("?p", pred, "?w")], "?w") if pred in names else ([], pred)
        out.append(Rule(
            key=f"fold.hedge.{i}.{z}.{w}",
            # `base` already carries this assertion's own `when` guard; the band slot is pinned to
            # THIS word separately, which is what lets the two coexist.
            lhs=[*base, Pat("?p", hslot, f"{w}?"), *pred_prem, *obj_prem], nac=nacs,
            rhs=[Pat("?s", head_pred, obj_tok)],
            bands=[Band(var="<hypothesis>?", key=LIKELINESS, degree=band, scope=("?s",))]))
    return out


# ---------------------------------------------------------------------------
# 3b. EVIDENCE-DRIVEN RE-MINTING — the mechanism behind the revision loop
# ---------------------------------------------------------------------------

#: Marker written onto ONE span that a contradiction implicates, gating that span's mint rule.
REMINT = "<remint>"

#: The slot that IS a span's denotation (`Grammar.slot_names` seeds it, `HEAD_BRIDGE` writes it).
HEAD_SLOT = "head"


def mintable_slots(gram: Grammar) -> list[dict]:
    """The head-slot declarations at which minting a subkind would be MEANINGFUL.

    Minting is meaningful exactly where the parent gets a DESCRIPTION from its other child, and the
    grammar already says where that is: a category declares an assertion whose subject is a head slot
    and whose object is another slot **from the same production**. `np asserts head is attr`, with
    `head` and `attr` both filled from `np from modifier plus np`, is the case — the minted entity
    gets `is_a lion` from the head and `is guzerat` from the attr.

    Derived, never sniffed. Reading it off category NAMES ("mint under a `modifier`") would hardcode
    one grammar's vocabulary into the engine, which the standing rule forbids. Note what this
    correctly EXCLUDES: `np from determiner plus np` has a head slot but no companion slot feeding an
    assertion, so `the lion` mints nothing — there is no description to distinguish.

    The subject slot must be the span's `head`, not merely SOME slot. Minting replaces what a span
    DENOTES, so it is only meaningful at the slot that is the denotation. Without this,
    `clause asserts subj pred obj` qualifies — subj and obj both come from `clause from np plus vp` —
    and a re-interpretation mints an entity at every CLAUSE, which is both meaningless and
    explosive (a 3-sentence session stopped terminating). `head` is already the system-level slot
    name (`Grammar.slot_names` seeds it, `HEAD_BRIDGE` writes it), not a new magic string."""
    by_name: dict[str, list[dict]] = {}
    for d in gram.slots:
        if "sonly" not in d:                         # binary productions only
            by_name.setdefault(d["sname"], []).append(d)
    out: list[dict] = []
    seen: set[tuple] = set()
    for a in gram.assertions:
        subj, obj = a.get("asubj"), a.get("aobj")
        if obj is None or subj != HEAD_SLOT:         # only at the span's DENOTATION slot
            continue
        for h in by_name.get(subj, []):
            if h["scat"] != a["acat"]:
                continue
            prod = (h["scat"], h["sleft"], h["sright"])
            if any((c["scat"], c["sleft"], c["sright"]) == prod for c in by_name.get(obj, [])):
                if prod not in seen:
                    seen.add(prod)
                    out.append(h)
    return out


def _production_lhs(d: dict, *, delta: bool = True) -> tuple[list, str]:
    """The premises binding a slot declaration's parent `?p` and its head-side child, and that
    child's register.

    Reads the materialized parse tree rather than re-joining spans on `cat`/`begin`/`end`: seed on
    the production's `dprod` literal, hop to the parent, hop to the declared side. The unused
    sibling is not bound at all — `dprod` already pins which production this is, so nothing is lost
    by not matching it. THE one chokepoint for the shape (`slot_bank`, `remint_mark_bank`,
    `reinterpretation_slots` all come through here)."""
    only = "sonly" in d
    key = _prod_key(d["scat"], d["sonly"]) if only else \
        _prod_key(d["scat"], d["sleft"], d["sright"])
    side = "donly" if only else ("dleft" if d["sside"] == "left" else "dright")
    if not delta:
        # WHOLE-GRAPH variant, for a bank that must see spans the fold has already consumed —
        # `remint_mark_bank` runs AFTER `interpret` has retired the delta marks, and has to find
        # contradiction sites anywhere in the session. Delta-seeding it makes it match NOTHING, which
        # is silent: `reconsider` simply reports ASK forever because it never finds a site to re-read.
        return ([Pat("?d", "dprod", key), Pat("?d", "dparent", "?p"),
                 Pat("?d", side, "?c")], "?c")
    # PREMISE ORDER IS THE JOIN PLAN. `lower_conj` seeds from the first pattern and thereafter drives
    # from whichever endpoint is already bound, so leading with the mark seeds the new sentence's
    # spans and every later premise is a pointer hop off it. Putting `?d dprod KEY` first instead
    # would seed EVERY decomposition in the session — the exact cost this is removing.
    return ([Pat("?p", UNINTERPRETED, "?u"),      # seed: spans still to fold
             Pat("?d", "dparent", "?p"),          # ?p bound -> follow IN to its decompositions
             Pat("?d", "dprod", key),             # ?d bound -> test the production
             Pat("?d", side, "?c")], "?c")


def remint_mark_bank(gram: Grammar) -> tuple[list[Rule], frozenset[str]]:
    """Mark the spans a contradiction implicates — the CULPRIT SELECTION, as rules.

    Fires while the contradicted interpretation is still LIVE, so `head` is available: a span whose
    head-side child percolated the contradicted entity up is a site where the merge happened, and
    marking it says "mint here next time". Structural — it re-derives the contradiction condition
    inline (like `contradiction_bank`) rather than addressing the `<contradiction>` node, which has
    no stable identity to match on.

    Marks only MODIFIED spans, which is why the bare `the lion` mention survives re-interpretation
    unsplit: it heads no mintable production."""
    rules: list[Rule] = []
    for d in mintable_slots(gram):
        prem, src = _production_lhs(d, delta=False)
        for w in sorted(gram.lexicon):
            rules.append(Rule(
                key=f"remint.mark.{d['scat']}.{d['sleft']}.{w}",
                lhs=[Pat("?e", w, "?x"), Pat("?e", neg_pred(w), "?x"),
                     *prem, Pat(src, d["scslot"], "?e")],
                # A PLAIN literal, which the lowering interns graph-wide — NOT a bound literal
                # (`<remint>?`), which mints a fresh node per firing. The mark is a flag on the span,
                # so it must be ONE node: with a bound literal every mark rule that fired left its
                # own marker, and the mint rule then matched once per marker and minted a separate
                # entity for each — 35 marks and a 5x node blowup on three sentences.
                rhs=[Pat("?p", REMINT, REMINT)]))
    return rules, frozenset({REMINT})


def reinterpretation_slots(gram: Grammar) -> tuple[list[Rule], frozenset[str]]:
    """The slot bank as re-read under the marks: percolate everywhere EXCEPT a marked span, and mint
    there instead.

    The two rules are exclusive by construction — the percolation rule for a mintable head slot
    carries the mark as a NAC, the mint rule carries it as a premise — so a re-interpretation is
    still ONE reading, not a branch."""
    base, preds = slot_bank(gram)
    marked = {f"fold.slot.{i}.{d['scat']}.{d['sname']}"
              for i, d in enumerate(gram.slots) if d in mintable_slots(gram)}
    gate = [Pat("?p", REMINT, "?g")]
    rules = [Rule(key=r.key, lhs=r.lhs, nac=[*r.nac, *gate], rhs=r.rhs) if r.key in marked else r
             for r in base]
    for i, d in enumerate(mintable_slots(gram)):
        prem, src = _production_lhs(d)
        rules.append(Rule(
            key=f"remint.mint.{i}.{d['scat']}",
            # `?e` is RHS-only, which is what makes the minted node NAMELESS — its identity is its
            # description (`ByDesc`), settled afterwards by `intern_described`.
            lhs=[*prem, *gate, Pat(src, d["scslot"], "?v")],
            rhs=[Pat("?e", "is_a", "?v"), Pat("?p", d["sname"], "?e")]))
    return rules, preds | {REMINT}


def compile_grammar(gram: Grammar, *, open_class: str | None = None) -> GrammarBanks:
    """Generate every bank from `gram`. Do this ONCE per grammar and reuse across sentences.

    (`closed=` removed 2026-07-20 — the open-vocabulary default is now gated by whether the grammar
    declares ANYTHING about a word, so a closed-class list no longer enters into it. Dead parameters
    rot; see `chart_bank`.)"""
    chart, cpreds = chart_bank(gram, open_class=open_class)
    amb, apreds = ambiguity_bank(gram)
    spans, sppreds = span_bank(gram)
    decs, dpreds = decomposition_bank(gram)
    supp, suppreds = suppression_bank(gram)
    slots, spreds = slot_bank(gram)
    marks, mpreds = remint_mark_bank(gram)
    rslots, rpreds = reinterpretation_slots(gram)
    # The decomposition bank runs with the spans (both are surface), so its rules ride the span
    # bank's slot in `parse` and its predicates join the span predicates.
    return GrammarBanks(chart=chart, chart_preds=cpreds, ambiguity=amb, ambiguity_preds=apreds,
                        spans=spans + decs + supp, span_preds=sppreds | dpreds | suppreds,
                        slots=slots, slot_preds=spreds,
                        asserts=assert_bank(gram, defining=False),
                        defining_asserts=assert_bank(gram, defining=True), grammar=gram,
                        remint_marks=marks, remint_preds=mpreds,
                        reinterp_slots=rslots, reinterp_slot_preds=rpreds,
                        open_class=open_class)


# ---------------------------------------------------------------------------
# 4. Parsing — the SURFACE half of the pipeline
# ---------------------------------------------------------------------------

PARSED, REFUSED, AMBIGUOUS = "parsed", "refused", "ambiguous"


def parse(g, sentence: str, banks: GrammarBanks, root: str = ROOT) -> tuple[str, list[str], str]:
    """Tokenize and parse `sentence` into `g`. Returns (outcome, tokens, eos).

    Outcome is `parsed` / `refused` (no complete parse — the diagnostic a bank of independent
    surface patterns structurally cannot produce) / `ambiguous` (two readings; ASK, do not pick).
    Writes only SURFACE structure: tokens, chains, and span `cat`/`begin`/`end`."""
    toks, eos = _tokenize_with_sentinel(g, sentence)
    if not toks:
        return REFUSED, [], ""
    # The token delta: all three surface banks below are seeded on it, so it must be written before
    # the first of them runs and retired however this function exits (see `clear_unparsed`).
    mark_tokens(g, toks)
    try:
        run_bank(g, banks.chart, control_preds=banks.chart_preds)
        if not any(g.has_key(r, sp(root)) and o == eos for r, o in g.relations_from(toks[0])):
            return REFUSED, toks, eos
        run_bank(g, banks.ambiguity, control_preds=banks.ambiguity_preds)
        if any(g.has_key(r, "ambiguous") for t in toks for r, _o in g.relations_from(t)):
            return AMBIGUOUS, toks, eos
        run_bank(g, banks.spans, control_preds=banks.span_preds)
    finally:
        clear_unparsed(g)
    clear_fresh(g)                                   # the delta is per-utterance; see `clear_fresh`
    return PARSED, toks, eos


def _tokenize_with_sentinel(g, sentence: str) -> tuple[list[str], str]:
    anchor = tokenize(g, sentence)
    toks = _chain_tokens(g, anchor)
    if not toks:
        return [], ""
    eos = g.add_node("<eos>", control=True)
    # Spans are [begin, end), so every token needs a successor — including the last.
    g.add_relation(toks[-1], "next", eos, control=True)
    g.add_relation(eos, "is_eos", g.add_node("yes"), control=True)
    return toks, eos


def _outcome(g, toks, eos, root) -> str:
    if not toks:
        return REFUSED
    if not any(g.has_key(r, sp(root)) and o == eos for r, o in g.relations_from(toks[0])):
        return REFUSED
    if any(g.has_key(r, "ambiguous") for t in toks for r, _o in g.relations_from(t)):
        return AMBIGUOUS
    return PARSED


def parse_batch(g, sentences, banks: GrammarBanks, root: str = ROOT) -> list[str]:
    """Parse MANY sentences into `g` with ONE pass of each bank. Returns per-sentence outcomes.

    Use this for corpus loading. `parse` runs every bank over the WHOLE graph, so calling it per
    sentence into an accumulating graph is QUADRATIC in corpus size — the same defect that made
    `authoring._recognize` take 24 s on an 85-line file (fixed 2026-07-18 the same way). The chart
    rules match within a token chain, so one global pass does every sentence.

    NOTE: spans are minted for every sentence with a complete parse, INCLUDING ambiguous ones.
    Callers that fold must filter to `PARSED` first — an ambiguous sentence is a question, not
    input."""
    pairs = [_tokenize_with_sentinel(g, s) for s in sentences]
    # ONE delta covering the whole batch — the same "the delta is what to (re-)read" move
    # `mark_all_spans` makes for a rebuild. Marking every batched sentence at once is what keeps
    # this a single pass while still excluding whatever the session already parsed.
    for toks, _eos in pairs:
        mark_tokens(g, toks)
    try:
        run_bank(g, banks.chart, control_preds=banks.chart_preds)
        run_bank(g, banks.ambiguity, control_preds=banks.ambiguity_preds)
        run_bank(g, banks.spans, control_preds=banks.span_preds)
    finally:
        clear_unparsed(g)
    clear_fresh(g)                                   # the delta is per-utterance; see `clear_fresh`
    return [_outcome(g, toks, eos, root) for toks, eos in pairs]


def ambiguous_spans(g, toks) -> list[tuple[str, str]]:
    """The (begin, end) token pairs flagged ambiguous — what a discriminating question is about."""
    return [(t, o) for t in toks for r, o in g.relations_from(t) if g.has_key(r, "ambiguous")]
