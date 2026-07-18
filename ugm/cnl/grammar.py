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
    grammar: Grammar


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
    interpretation layer (`surface_interpretation.md` §2)."""
    return ([Rule(key=f"surf.span.{c}",
                  lhs=[Pat("?a", f"useful_{c}", "?b")],
                  rhs=[Pat("<span>?", "cat", c), Pat("<span>?", "begin", "?a"),
                       Pat("<span>?", "end", "?b")])
             for c in sorted(gram.categories)], frozenset({"cat", "begin", "end"}))


def slot_bank(gram: Grammar) -> tuple[list[Rule], frozenset[str]]:
    """A percolation rule per declared slot, plus a minting rule per declared `mint`."""
    rules: list[Rule] = []
    for i, d in enumerate(gram.slots):
        s, z, side, cs = d["sname"], d["scat"], d["sside"], d["scslot"]
        parent = [Pat("?p", "cat", z), Pat("?p", "begin", "?a"), Pat("?p", "end", "?b")]
        if "sonly" in d:
            kids = [Pat("?q", "cat", d["sonly"]), Pat("?q", "begin", "?a"), Pat("?q", "end", "?b")]
            src = "?q"
        else:
            kids = [Pat("?l", "cat", d["sleft"]), Pat("?l", "begin", "?a"), Pat("?l", "end", "?m"),
                    Pat("?r", "cat", d["sright"]), Pat("?r", "begin", "?m"), Pat("?r", "end", "?b")]
            src = "?l" if side == "left" else "?r"
        rules.append(Rule(key=f"fold.slot.{i}.{z}.{s}",
                          lhs=[*parent, *kids, Pat(src, cs, "?v")],
                          rhs=[Pat("?p", s, "?v")]))
    for i, d in enumerate(gram.mints):
        z, x, y = d["mcat"], d["mleft"], d["mright"]
        src = "?l" if d["mside"] == "left" else "?r"
        rules.append(Rule(
            key=f"fold.mint_entity.{i}.{z}",
            lhs=[Pat("?p", "cat", z), Pat("?p", "begin", "?a"), Pat("?p", "end", "?b"),
                 Pat("?l", "cat", x), Pat("?l", "begin", "?a"), Pat("?l", "end", "?m"),
                 Pat("?r", "cat", y), Pat("?r", "begin", "?m"), Pat("?r", "end", "?b"),
                 Pat(src, d["mcslot"], "?v")],
            # `?e` is an RHS-only variable, which is what makes it NAMELESS: `lower_rhs` gives a
            # bound literal a name and a plain literal graph-wide interning, but a bare `?e` mints
            # an unnamed node per firing. That is the `ByDesc` identity law.
            rhs=[Pat("?e", "is_a", "?v"), Pat("?p", d["mname"], "?e")]))
    return rules, frozenset(gram.slot_names)


def assert_bank(gram: Grammar) -> list[Rule]:
    """A fact-emitting rule per assertion declaration.

    The PREDICATE position reads as a SLOT if it names a declared slot, else as a literal word —
    data-driven, not string-sniffing. A slot predicate is DYNAMIC, and the ISA rejects a non-plain
    RHS predicate (`lower_rhs`: "RHS non-plain predicate is a later slice"), so it generates one
    rule per lexicon word. That is exactly `relation_forms`' existing discipline — declare the
    relation and a form is generated for it — and it means open vocabulary works for ENTITIES but
    not for PREDICATES, the same controlled-CNL boundary the project already draws."""
    rules: list[Rule] = []
    names = gram.slot_names
    for i, d in enumerate(gram.assertions):
        z, mode = d["acat"], d["amode"]
        subj, pred, obj = d["asubj"], d["apred"], d.get("aobj")
        if obj is None:
            continue
        guards = [Pat("?p", d["awhen"], "?gw")] if "awhen" in d else []
        nacs = [Pat("?p", d["aunless"], "?gu")] if "aunless" in d else []
        base = [Pat("?p", "cat", z), Pat("?p", subj, "?s"), *guards]
        obj_prem, obj_tok = ([Pat("?p", obj, "?o")], "?o") if obj in names else ([], obj)
        if pred in names:
            for w in sorted(gram.lexicon):
                p = neg_pred(w) if mode == "deny" else w
                rules.append(Rule(key=f"fold.assert.{i}.{z}.{w}",
                                  lhs=[*base, Pat("?p", pred, f"{w}?"), *obj_prem],
                                  nac=nacs, rhs=[Pat("?s", p, obj_tok)]))
        else:
            p = neg_pred(pred) if mode == "deny" else pred
            rules.append(Rule(key=f"fold.assert.{i}.{z}.{p}",
                              lhs=[*base, *obj_prem], nac=nacs, rhs=[Pat("?s", p, obj_tok)]))
    return rules


def compile_grammar(gram: Grammar, *, open_class: str | None = None,
                    closed: tuple[str, ...] = CLOSED_CLASSES) -> GrammarBanks:
    """Generate every bank from `gram`. Do this ONCE per grammar and reuse across sentences."""
    chart, cpreds = chart_bank(gram, open_class=open_class, closed=closed)
    amb, apreds = ambiguity_bank(gram)
    spans, sppreds = span_bank(gram)
    slots, spreds = slot_bank(gram)
    return GrammarBanks(chart=chart, chart_preds=cpreds, ambiguity=amb, ambiguity_preds=apreds,
                        spans=spans, span_preds=sppreds, slots=slots, slot_preds=spreds,
                        asserts=assert_bank(gram), grammar=gram)


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
    return PARSED, toks, eos


def ambiguous_spans(g, toks) -> list[tuple[str, str]]:
    """The (begin, end) token pairs flagged ambiguous — what a discriminating question is about."""
    return [(t, o) for t in toks for r, o in g.relations_from(t) if g.has_key(r, "ambiguous")]
