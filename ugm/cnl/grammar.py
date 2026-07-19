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

from dataclasses import dataclass, field

from ..production_rule import Distinct, Pat, Rule
from ..lowering import run_bank
from ..vocabulary import neg_pred
from ..world_model import Graph
from .forms import _chain_tokens, tokenize

ROOT = "clause"

#: Word classes that are FUNCTION words: a word declared one of these is not eligible for the
#: open-vocabulary default. Data, overridable per call — it should itself become a CNL declaration.
CLOSED_CLASSES: tuple[str, ...] = ("determiner", "negator", "comparator", "preposition", "copula")


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


def _assert_forms() -> list[Rule]:
    """`<cat> asserts|denies A B C [when|unless G]` — six shapes, generated over the two verbs and
    the three guard shapes rather than written out."""
    forms: list[Rule] = []
    for verb, mode in (("asserts", "assert"), ("denies", "deny")):
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
DECLARATION_FORMS: list[Rule] = PRODUCTION_FORMS + SLOT_FORMS + MINT_FORMS + ASSERT_FORMS

_DECL_KEYS = ("sname", "scat", "sleft", "sright", "sonly", "sside", "scslot",
              "acat", "amode", "asubj", "apred", "aobj", "awhen", "aunless",
              "mname", "mcat", "mleft", "mright", "mside", "mcslot")


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

    @property
    def categories(self) -> set[str]:
        return ({z for z, _ in self.unary} | {z for z, *_ in self.binary}
                | {x for _, x in self.unary}
                | {x for _, a, b in self.binary for x in (a, b)} | {ROOT})

    @property
    def slot_names(self) -> set[str]:
        return {d["sname"] for d in self.slots} | {d["mname"] for d in self.mints} | {"head"}


def load_grammar(text: str) -> Grammar:
    """Load CNL grammar declarations and read the grammar back out of the resulting graph.

    `#` comments are stripped, matching every other CNL file loader (`load_machine_rules`,
    `load_kb`, intake) — `load_facts` itself does not strip them."""
    from ..attrgraph import AttrGraph
    from .authoring import load_facts
    g = AttrGraph()
    body = "\n".join(s for line in text.splitlines()
                     if (s := line.strip()) and not s.startswith("#"))
    load_facts(g, body, extra_forms=DECLARATION_FORMS)
    return read_grammar(g)


def load_grammar_file(*paths) -> Grammar:
    """Load a grammar from one or more `.cnl` files (multi-file, like `load_kb`)."""
    import pathlib
    return load_grammar("\n".join(pathlib.Path(p).read_text(encoding="utf-8") for p in paths))


def read_grammar(g) -> Grammar:
    """Read a `Grammar` out of a graph the declaration forms have already run over."""
    gram = Grammar()
    for n in g.nodes():
        for r, o in g.relations_from(n):
            # `<...>` categories are ENGINE bookkeeping riding the same `is_a` predicate the lexicon
            # uses (`mark_mentions` writes `is_a <mention>` on every entity). Reading them as
            # lexicon entries declares every word a `<mention>` and generates a chart rule for it —
            # measured at ~80% of parse runtime before this filter. See `homoiconic_grammar.md` §9.5.
            if g.has_key(r, "is_a") and not g.name(o).startswith("<"):
                gram.lexicon.setdefault(g.name(n), []).append(g.name(o))
    seen_u, seen_b = set(), set()
    for n in g.nodes():
        d = {}
        for r, o in g.relations_from(n):
            for k in ("gcat", "gleft", "gright", "gonly", *_DECL_KEYS):
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
    gram.unary.sort()
    gram.binary.sort()
    return gram


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


def chart_bank(gram: Grammar, *, open_class: str | None = None,
               closed: tuple[str, ...] = CLOSED_CLASSES) -> tuple[list[Rule], frozenset[str]]:
    """The chart rules: one per lexicon entry, per unary production, per binary production.

    `open_class`: with it set, any token NOT declared in a closed class also spans as that category
    — the open-vocabulary default. It is one rule with a NAC over a DECLARED tag (no hardcoded
    stop-list), REFUSAL SURVIVES IT (gibberish still fails to parse), and it is cheaper than
    one lexical rule per word. See `homoiconic_grammar.md` §8.4."""
    rules: list[Rule] = []
    cats = set(gram.categories)
    for w, cs in sorted(gram.lexicon.items()):
        for c in sorted(cs):
            cats.add(c)
            rules.append(Rule(key=f"chart.lex.{c}.{w}",
                              lhs=[Pat(f"{w}?", "next", "?u")],
                              rhs=[Pat(f"{w}?", sp(c), "?u")]))
    if open_class:
        for w, cs in sorted(gram.lexicon.items()):
            if any(c in closed for c in cs):
                rules.append(Rule(key=f"chart.closed.{w}",
                                  lhs=[Pat(f"{w}?", "next", "?u")],
                                  rhs=[Pat(f"{w}?", "closed_class", "yes")]))
        rules.append(Rule(key=f"chart.open.{open_class}",
                          lhs=[Pat("?t", "next", "?u")],
                          nac=[Pat("?t", "closed_class", "yes")],
                          rhs=[Pat("?t", sp(open_class), "?u")]))
        cats.add(open_class)
    for z, x in gram.unary:
        rules.append(Rule(key=f"chart.un.{z}.{x}",
                          lhs=[Pat("?a", sp(x), "?b")], rhs=[Pat("?a", sp(z), "?b")]))
    for z, x, y in gram.binary:
        rules.append(Rule(key=f"chart.bin.{z}.{x}.{y}",
                          lhs=[Pat("?a", sp(x), "?m"), Pat("?m", sp(y), "?b")],
                          rhs=[Pat("?a", sp(z), "?b")]))
    return rules, frozenset({"next", "first", "closed_class"} | {sp(c) for c in cats})


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
    tokens. See `homoiconic_grammar.md` §8.3."""
    rules: list[Rule] = [
        Rule(key="amb.useful.root",
             lhs=[Pat("?s", "first", "?a"), Pat("?a", sp(root), "?b"), Pat("?b", "is_eos", "yes")],
             rhs=[Pat("?a", f"useful_{root}", "?b")]),
    ]
    for z, x in gram.unary:
        rules.append(Rule(key=f"amb.down.{z}.{x}",
                          lhs=[Pat("?a", f"useful_{z}", "?b"), Pat("?a", sp(x), "?b")],
                          rhs=[Pat("?a", f"useful_{x}", "?b")]))
    for z, x, y in gram.binary:
        rules.append(Rule(key=f"amb.down.{z}.{x}.{y}",
                          lhs=[Pat("?a", f"useful_{z}", "?b"), Pat("?a", sp(x), "?m"),
                               Pat("?m", sp(y), "?b")],
                          rhs=[Pat("?a", f"useful_{x}", "?m"), Pat("?m", f"useful_{y}", "?b")]))
    for i, (z, x, y) in enumerate(gram.binary):
        rules.append(Rule(key=f"amb.split.{z}.{x}.{y}",
                          lhs=[Pat("?a", f"useful_{z}", "?b"), Pat("?a", sp(x), "?m"),
                               Pat("?m", sp(y), "?b"), Pat("?a", sp(x), "?n"),
                               Pat("?n", sp(y), "?b")],
                          distinct=[Distinct("?m", "?n")],
                          rhs=[Pat("?a", "ambiguous", "?b")]))
        for z2, x2, y2 in gram.binary[i + 1:]:
            if z2 == z:
                rules.append(Rule(key=f"amb.prod.{z}.{x}.{y}.{x2}.{y2}",
                                  lhs=[Pat("?a", f"useful_{z}", "?b"), Pat("?a", sp(x), "?m"),
                                       Pat("?m", sp(y), "?b"), Pat("?a", sp(x2), "?n"),
                                       Pat("?n", sp(y2), "?b")],
                                  rhs=[Pat("?a", "ambiguous", "?b")]))
        for z2, x2 in gram.unary:
            if z2 == z:
                rules.append(Rule(key=f"amb.mixed.{z}.{x}.{y}.{x2}",
                                  lhs=[Pat("?a", f"useful_{z}", "?b"), Pat("?a", sp(x), "?m"),
                                       Pat("?m", sp(y), "?b"), Pat("?a", sp(x2), "?b")],
                                  rhs=[Pat("?a", "ambiguous", "?b")]))
    for i, (z, x) in enumerate(gram.unary):
        for z2, x2 in gram.unary[i + 1:]:
            if z2 == z:
                rules.append(Rule(key=f"amb.un.{z}.{x}.{x2}",
                                  lhs=[Pat("?a", f"useful_{z}", "?b"), Pat("?a", sp(x), "?b"),
                                       Pat("?a", sp(x2), "?b")],
                                  rhs=[Pat("?a", "ambiguous", "?b")]))
    cats = gram.categories | {c for cs in gram.lexicon.values() for c in cs}
    return rules, frozenset({"is_eos", "ambiguous"} | {f"useful_{c}" for c in cats})


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
    ENTITIES — the same defect, the other layer."""
    return ([Rule(key=f"surf.span.{c}",
                  lhs=[Pat("?a", f"useful_{c}", "?b")],
                  nac=[Pat("?s", "cat", c), Pat("?s", "begin", "?a"), Pat("?s", "end", "?b")],
                  # FRESH marks the spans this parse actually minted — the NAC above means that is
                  # exactly the new sentence's spans. `decomposition_bank` SEEDS on it, so the tree
                  # is built over the new sentence instead of the whole session (`clear_fresh`).
                  rhs=[Pat("<span>?", "cat", c), Pat("<span>?", "begin", "?a"),
                       Pat("<span>?", "end", "?b"), Pat("<span>?", FRESH, "<yes>"),
                       Pat("<span>?", UNINTERPRETED, "<yes>")])
             for c in sorted(gram.categories)],
            frozenset({"cat", "begin", "end", FRESH, UNINTERPRETED}))


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
    whose decompositions already stand)."""
    fresh = [Pat("?p", FRESH, "?fr")]
    rules: list[Rule] = []
    for z, x, y in sorted(set(gram.binary)):
        rules.append(Rule(
            key=f"surf.dec.{z}.{x}.{y}",
            lhs=[*fresh,
                 Pat("?p", "cat", z), Pat("?p", "begin", "?a"), Pat("?p", "end", "?b"),
                 Pat("?l", "cat", x), Pat("?l", "begin", "?a"), Pat("?l", "end", "?m"),
                 Pat("?r", "cat", y), Pat("?r", "begin", "?m"), Pat("?r", "end", "?b")],
            nac=[Pat("?d", "dparent", "?p"), Pat("?d", "dleft", "?l"), Pat("?d", "dright", "?r")],
            rhs=[Pat("<dec>?", "dprod", _prod_key(z, x, y)), Pat("<dec>?", "dparent", "?p"),
                 Pat("<dec>?", "dleft", "?l"), Pat("<dec>?", "dright", "?r")]))
    for z, x in sorted(set(gram.unary)):
        rules.append(Rule(
            key=f"surf.dec.{z}.{x}",
            lhs=[*fresh,
                 Pat("?p", "cat", z), Pat("?p", "begin", "?a"), Pat("?p", "end", "?b"),
                 Pat("?q", "cat", x), Pat("?q", "begin", "?a"), Pat("?q", "end", "?b")],
            nac=[Pat("?d", "dparent", "?p"), Pat("?d", "donly", "?q")],
            rhs=[Pat("<dec>?", "dprod", _prod_key(z, x)), Pat("<dec>?", "dparent", "?p"),
                 Pat("<dec>?", "donly", "?q")]))
    return rules, DEC_PREDS | {FRESH}


def clear_fresh(g) -> int:
    """Retire the `FRESH` marks once the tree is built. Returns how many went.

    The mark is a per-utterance delta, so it MUST NOT survive the utterance: left standing, the seed
    set grows with the session and the optimization silently undoes itself (the whole point is that
    the seed stays small). O(marked), via the key index — not a graph sweep, which would reintroduce
    the per-utterance whole-graph cost this exists to remove."""
    return _retire_mark(g, FRESH)


def clear_uninterpreted(g) -> int:
    """Retire the interpretation delta once `interpret` has folded it. Same contract as
    `clear_fresh`, and the same silent-failure mode: leave these standing and every answer is still
    right, the seed set just grows with the session until the delta buys nothing."""
    return _retire_mark(g, UNINTERPRETED)


def _retire_mark(g, key: str) -> int:
    """Drop every relation node carrying `key`. O(marked) via the key index — NOT a graph sweep,
    which would reintroduce the per-utterance whole-graph cost these marks exist to remove."""
    gone = 0
    for r in list(g.nodes_with_key(key)):
        if r in g.nodes():
            g.remove_node(r)
            gone += 1
    return gone


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
        if defining is not None and (z in minting) != defining:
            continue
        guards = [Pat("?p", d["awhen"], "?gw")] if "awhen" in d else []
        nacs = [Pat("?p", d["aunless"], "?gu")] if "aunless" in d else []
        # Led by the mark, so an assert rule seeds the new sentence's spans rather than every span
        # carrying `cat` (see `_production_lhs` on premise order being the join plan).
        base = [Pat("?p", UNINTERPRETED, "?u"), Pat("?p", "cat", z), Pat("?p", subj, "?s"), *guards]
        obj_prem, obj_tok = ([Pat("?p", obj, "?o")], "?o") if obj in names else ([], obj)
        if pred in names and mode != "deny":
            # ONE rule, with the predicate as an LHS-bound VARIABLE — the slot's filler names the
            # predicate, resolved at apply time by the dynamic-key MINT (`lower_rhs`/`MINT.key_reg`).
            rules.append(Rule(key=f"fold.assert.{i}.{z}",
                              lhs=[*base, Pat("?p", pred, "?w"), *obj_prem],
                              nac=nacs, rhs=[Pat("?s", "?w", obj_tok)]))
        elif pred in names:
            # DENY still expands per word: the head predicate is `neg_pred(?w)`, a STRING derivation
            # from the matched word, and the ISA has no string ops. Collapsing this too needs the
            # positive/negative pairing to exist as graph data (`w -[neg_of]-> w_not`) so the rule
            # can BIND the negative rather than compute it — worth doing, but it is a vocabulary
            # change, not a lowering one.
            for w in sorted(gram.lexicon):
                rules.append(Rule(key=f"fold.assert.{i}.{z}.{w}",
                                  lhs=[*base, Pat("?p", pred, f"{w}?"), *obj_prem],
                                  nac=nacs, rhs=[Pat("?s", neg_pred(w), obj_tok)]))
        else:
            p = neg_pred(pred) if mode == "deny" else pred
            rules.append(Rule(key=f"fold.assert.{i}.{z}.{p}",
                              lhs=[*base, *obj_prem], nac=nacs, rhs=[Pat("?s", p, obj_tok)]))
    return rules


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


def compile_grammar(gram: Grammar, *, open_class: str | None = None,
                    closed: tuple[str, ...] = CLOSED_CLASSES) -> GrammarBanks:
    """Generate every bank from `gram`. Do this ONCE per grammar and reuse across sentences."""
    chart, cpreds = chart_bank(gram, open_class=open_class, closed=closed)
    amb, apreds = ambiguity_bank(gram)
    spans, sppreds = span_bank(gram)
    decs, dpreds = decomposition_bank(gram)
    slots, spreds = slot_bank(gram)
    marks, mpreds = remint_mark_bank(gram)
    rslots, rpreds = reinterpretation_slots(gram)
    # The decomposition bank runs with the spans (both are surface), so its rules ride the span
    # bank's slot in `parse` and its predicates join the span predicates.
    return GrammarBanks(chart=chart, chart_preds=cpreds, ambiguity=amb, ambiguity_preds=apreds,
                        spans=spans + decs, span_preds=sppreds | dpreds,
                        slots=slots, slot_preds=spreds,
                        asserts=assert_bank(gram, defining=False),
                        defining_asserts=assert_bank(gram, defining=True), grammar=gram,
                        remint_marks=marks, remint_preds=mpreds,
                        reinterp_slots=rslots, reinterp_slot_preds=rpreds)


# ---------------------------------------------------------------------------
# 4. Parsing — the SURFACE half of the pipeline
# ---------------------------------------------------------------------------

PARSED, REFUSED, AMBIGUOUS = "parsed", "refused", "ambiguous"


def parse(g, sentence: str, banks: GrammarBanks, root: str = ROOT) -> tuple[str, list[str], str]:
    """Tokenize and parse `sentence` into `g`. Returns (outcome, tokens, eos).

    Outcome is `parsed` / `refused` (no complete parse — the diagnostic a bank of independent
    surface patterns structurally cannot produce) / `ambiguous` (two readings; ASK, do not pick).
    Writes only SURFACE structure: tokens, chains, and span `cat`/`begin`/`end`."""
    anchor = tokenize(g, sentence)
    toks = _chain_tokens(g, anchor)
    if not toks:
        return REFUSED, [], ""
    eos = g.add_node("<eos>", control=True)
    # Spans are [begin, end), so every token needs a successor — including the last.
    g.add_relation(toks[-1], "next", eos, control=True)
    g.add_relation(eos, "is_eos", g.add_node("yes"), control=True)
    run_bank(g, banks.chart, control_preds=banks.chart_preds)
    if not any(g.has_key(r, sp(root)) and o == eos for r, o in g.relations_from(toks[0])):
        return REFUSED, toks, eos
    run_bank(g, banks.ambiguity, control_preds=banks.ambiguity_preds)
    if any(g.has_key(r, "ambiguous") for t in toks for r, _o in g.relations_from(t)):
        return AMBIGUOUS, toks, eos
    run_bank(g, banks.spans, control_preds=banks.span_preds)
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
    run_bank(g, banks.chart, control_preds=banks.chart_preds)
    run_bank(g, banks.ambiguity, control_preds=banks.ambiguity_preds)
    run_bank(g, banks.spans, control_preds=banks.span_preds)
    clear_fresh(g)                                   # the delta is per-utterance; see `clear_fresh`
    return [_outcome(g, toks, eos, root) for toks, eos in pairs]


def ambiguous_spans(g, toks) -> list[tuple[str, str]]:
    """The (begin, end) token pairs flagged ambiguous — what a discriminating question is about."""
    return [(t, o) for t in toks for r, o in g.relations_from(t) if g.has_key(r, "ambiguous")]
