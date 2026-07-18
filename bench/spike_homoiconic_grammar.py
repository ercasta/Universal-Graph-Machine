"""
SPIKE — the intake grammar as CNL data, interpreted by rules (design/homoiconic_grammar.md).

Wall-first. The design doc's §5 lists four things the spike must find out; this runs them.

THE MECHANISM UNDER TEST. A grammar is declared in CNL as a LEXICON (`lion is a noun`, already
the shipped `X is a <class>` surface) plus PRODUCTIONS (`np expands to determiner plus np`, one
new form pair). A §8 tool GENERATES recognition rules from those declarations — exactly the
established `relation_forms` / `nary_forms` gradient, one step further up from CLASSES to
COMPOSITION. The generated rules build a CHART: a span is a relation named for its category,
running from the span's first token to the token just past its last (`the --span_np--> has`).

  lexical   `w` is a `C`        :  w --next--> u              =>  w --span_C--> u
  unary     `Z expands to X`    :  a --span_X--> b            =>  a --span_Z--> b
  binary    `Z expands to X plus Y` : a --span_X--> m, m --span_Y--> b  =>  a --span_Z--> b

THE POINT, for the crux in §3. Chart parsing needs NO branch selection: every enabled rule fires
and every constituent gets built, which is what a chart IS. Token-passing forward chaining and
chart parsing are the same control regime. So the engine's core commitment is not merely
survivable here — it is the natural fit. What the spike has to find out is what that costs, and
whether the ambiguity you refuse to select on is still VISIBLE enough to ask about.

Run: python bench/spike_homoiconic_grammar.py
"""
from __future__ import annotations

import time

import ugm as h
from ugm import AttrGraph, Distinct, Pat, Rule, run_bank
from ugm.cnl.authoring import load_facts
from ugm.cnl.forms import tokenize


def hdr(s: str) -> None:
    print(f"\n{'=' * 78}\n{s}\n{'=' * 78}")


# ---------------------------------------------------------------------------
# 1. The grammar-declaration surface — two forms, and that is the whole kernel
# ---------------------------------------------------------------------------
#
# `Z expands to X`           -> a UNARY production
# `Z expands to X plus Y`    -> a BINARY production
#
# Binary+unary (Chomsky normal form) is not a limitation of the idea, it is the shape that makes
# composition a two-premise JOIN — i.e. an ordinary rule. A wider production would just be more
# premises. The lexicon needs no new form at all: `lion is a noun` is the shipped `X is a Y`.

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
        nac=[Pat("?x", "next", "?more")],          # a bare `Z expands to X`, nothing after X
        rhs=[Pat("<prod>?", "gcat", "?z"), Pat("<prod>?", "gonly", "?x")],
    ),
]


# The grammar itself — DATA, in CNL. Nothing below this line is specific to it.
GRAMMAR_CNL = """
the is a determiner
a is a determiner
no is a negator
guzerat is a modifier
lion is a noun
mane is a noun
tiger is a noun
africa is a noun
fish is a noun
has is a transitive
eats is a transitive
roars is a intransitive
lives is a intransitive
is is a copula
smaller is a comparative
than is a comparator
in is a preposition
np expands to noun
np expands to determiner plus np
np expands to modifier plus np
np expands to negator plus np
np expands to np plus pp
pp expands to preposition plus np
vp expands to intransitive
vp expands to transitive plus np
vp expands to vp plus pp
cp expands to comparator plus np
ap expands to comparative plus cp
vp expands to copula plus ap
clause expands to np plus vp
"""

# The closed classes: a word declared one of these is a FUNCTION word, so the open-class default
# (§3 below) must not also read it as a noun. Declared here as data, not sniffed.
CLOSED_CLASSES = ("determiner", "negator", "comparator", "preposition", "copula")

ROOT = "clause"


# ---------------------------------------------------------------------------
# 2. Reading the declared grammar back out (a §8 reader, like `declared_relations`)
# ---------------------------------------------------------------------------

def read_grammar(text: str) -> tuple[dict[str, list[str]], list[tuple[str, str]],
                                     list[tuple[str, str, str]]]:
    """Load `text` as CNL and read back (lexicon, unary productions, binary productions)."""
    g = AttrGraph()
    load_facts(g, text, extra_forms=PRODUCTION_FORMS)

    lex: dict[str, list[str]] = {}
    for n in g.nodes():
        for r, o in g.relations_from(n):
            # `<...>` categories are ENGINE bookkeeping that rides the same `is_a` predicate the
            # lexicon uses — `mark_mentions` writes `is_a <mention>` on every entity, so reading
            # the lexicon naively declares every word a `<mention>` and generates a chart rule for
            # it. Harmless here (no production mentions it) but it is a real contamination, and one
            # of two this slice hit; see the findings on substrate layering.
            if g.has_key(r, "is_a") and not g.name(o).startswith("<"):
                lex.setdefault(g.name(n), []).append(g.name(o))

    unary: list[tuple[str, str]] = []
    binary: list[tuple[str, str, str]] = []
    for n in g.nodes():
        slot = {}
        for r, o in g.relations_from(n):
            for k in ("gcat", "gleft", "gright", "gonly"):
                if g.has_key(r, k):
                    slot[k] = g.name(o)
        if "gcat" not in slot:
            continue
        if "gonly" in slot:
            unary.append((slot["gcat"], slot["gonly"]))
        elif "gleft" in slot and "gright" in slot:
            binary.append((slot["gcat"], slot["gleft"], slot["gright"]))
    return lex, sorted(set(unary)), sorted(set(binary))


# ---------------------------------------------------------------------------
# 3. The generated chart bank
# ---------------------------------------------------------------------------

def sp(cat: str) -> str:
    return f"span_{cat}"


def chart_bank(lex, unary, binary, *, open_class: str | None = None,
               closed: tuple[str, ...] = CLOSED_CLASSES) -> tuple[list[Rule], frozenset[str]]:
    """Generate the chart rules from the declared grammar (a §8 tool).

    `open_class`: if set, ANY token not declared in a closed class also spans as that category —
    the open-vocabulary default that lets an undeclared content word parse (see §3 of the run)."""
    rules: list[Rule] = []
    cats = {c for cs in lex.values() for c in cs} | {z for z, _ in unary} \
        | {z for z, *_ in binary} | {x for _, x, y in binary for x in (x, y)}
    for w, cs in sorted(lex.items()):
        for c in sorted(cs):
            rules.append(Rule(key=f"chart.lex.{c}.{w}",
                              lhs=[Pat(f"{w}?", "next", "?u")],
                              rhs=[Pat(f"{w}?", sp(c), "?u")]))
    if open_class:
        # Tag every word declared in a closed class, then span everything else as `open_class`.
        # NAC over a DECLARED tag — no hardcoded stop-list, same shape as `surf.*` tagging.
        for w, cs in sorted(lex.items()):
            if any(c in closed for c in cs):
                rules.append(Rule(key=f"chart.closed.{w}",
                                  lhs=[Pat(f"{w}?", "next", "?u")],
                                  rhs=[Pat(f"{w}?", "closed_class", "yes")]))
        rules.append(Rule(key=f"chart.open.{open_class}",
                          lhs=[Pat("?t", "next", "?u")],
                          nac=[Pat("?t", "closed_class", "yes")],
                          rhs=[Pat("?t", sp(open_class), "?u")]))
        cats.add(open_class)
    for z, x in unary:
        rules.append(Rule(key=f"chart.un.{z}.{x}",
                          lhs=[Pat("?a", sp(x), "?b")], rhs=[Pat("?a", sp(z), "?b")]))
    for z, x, y in binary:
        rules.append(Rule(key=f"chart.bin.{z}.{x}.{y}",
                          lhs=[Pat("?a", sp(x), "?m"), Pat("?m", sp(y), "?b")],
                          rhs=[Pat("?a", sp(z), "?b")]))
    preds = frozenset({"next", "first", "closed_class"} | {sp(c) for c in cats})
    return rules, preds


def ambiguity_bank(unary, binary, root: str = ROOT) -> tuple[list[Rule], frozenset[str]]:
    """Detect ambiguity IN THE PACKED CHART, in-engine, with no branch selection.

    Two passes, both ordinary rules:

    1. USEFULNESS, top-down. The root span is useful; a useful span makes the children of every
       production that licenses it useful. This is what separates a real ambiguity from a
       locally-ambiguous DEAD constituent (a chart holds constituents that no complete parse uses).
    2. AMBIGUITY. A USEFUL span of category Z licensed two different ways — a different split point
       (`Distinct` on the midpoint) or a different production at the same split — is ambiguous.

    Both halves are generated from the grammar DATA, so they extend with it."""
    rules: list[Rule] = [
        Rule(key="amb.useful.root",
             lhs=[Pat("?s", "first", "?a"), Pat("?a", sp(root), "?b"), Pat("?b", "is_eos", "yes")],
             rhs=[Pat("?a", f"useful_{root}", "?b")]),
    ]
    for z, x in unary:
        rules.append(Rule(key=f"amb.down.{z}.{x}",
                          lhs=[Pat("?a", f"useful_{z}", "?b"), Pat("?a", sp(x), "?b")],
                          rhs=[Pat("?a", f"useful_{x}", "?b")]))
    for z, x, y in binary:
        rules.append(Rule(key=f"amb.down.{z}.{x}.{y}",
                          lhs=[Pat("?a", f"useful_{z}", "?b"), Pat("?a", sp(x), "?m"),
                               Pat("?m", sp(y), "?b")],
                          rhs=[Pat("?a", f"useful_{x}", "?m"), Pat("?m", f"useful_{y}", "?b")]))

    # A useful span built two ways. Same production, different split -> Distinct on the midpoint;
    # different productions -> distinct premises already, no condition needed.
    for i, (z, x, y) in enumerate(binary):
        rules.append(Rule(key=f"amb.split.{z}.{x}.{y}",
                          lhs=[Pat("?a", f"useful_{z}", "?b"), Pat("?a", sp(x), "?m"),
                               Pat("?m", sp(y), "?b"), Pat("?a", sp(x), "?n"),
                               Pat("?n", sp(y), "?b")],
                          distinct=[Distinct("?m", "?n")],
                          rhs=[Pat("?a", "ambiguous", "?b")]))
        for z2, x2, y2 in binary[i + 1:]:
            if z2 != z:
                continue
            rules.append(Rule(key=f"amb.prod.{z}.{x}.{y}.{x2}.{y2}",
                              lhs=[Pat("?a", f"useful_{z}", "?b"), Pat("?a", sp(x), "?m"),
                                   Pat("?m", sp(y), "?b"), Pat("?a", sp(x2), "?n"),
                                   Pat("?n", sp(y2), "?b")],
                              rhs=[Pat("?a", "ambiguous", "?b")]))
        for z2, x2 in unary:
            if z2 != z:
                continue
            rules.append(Rule(key=f"amb.mixed.{z}.{x}.{y}.{x2}",
                              lhs=[Pat("?a", f"useful_{z}", "?b"), Pat("?a", sp(x), "?m"),
                                   Pat("?m", sp(y), "?b"), Pat("?a", sp(x2), "?b")],
                              rhs=[Pat("?a", "ambiguous", "?b")]))
    for i, (z, x) in enumerate(unary):
        for z2, x2 in unary[i + 1:]:
            if z2 == z:
                rules.append(Rule(key=f"amb.un.{z}.{x}.{x2}",
                                  lhs=[Pat("?a", f"useful_{z}", "?b"), Pat("?a", sp(x), "?b"),
                                       Pat("?a", sp(x2), "?b")],
                                  rhs=[Pat("?a", "ambiguous", "?b")]))
    cats = {z for z, _ in unary} | {z for z, *_ in binary} | {x for _, x, y in binary
                                                              for x in (x, y)} \
        | {x for _, x in unary} | {root}
    return rules, frozenset({"is_eos", "ambiguous"} | {f"useful_{c}" for c in cats})


def _chain(g, anchor) -> list[str]:
    first = next((o for r, o in g.relations_from(anchor) if g.has_key(r, "first")), None)
    toks, cur = [], first
    while cur is not None:
        toks.append(cur)
        cur = next((o for r, o in g.relations_from(cur) if g.has_key(r, "next")), None)
    return toks


def parse(sentence: str, bank, preds):
    """Tokenize + run the chart bank. Returns (graph, tokens, eos)."""
    g = AttrGraph()
    anchor = tokenize(g, sentence)
    toks = _chain(g, anchor)
    eos = g.add_node("<eos>", control=True)
    g.add_relation(toks[-1], "next", eos, control=True)   # spans are [begin, end): every token
    g.add_relation(eos, "is_eos", g.add_node("yes"), control=True)   # needs a successor, incl. the
    run_bank(g, bank, control_preds=preds)                           # last -> a sentinel
    return g, toks, eos


def spans(g, toks, eos) -> dict[tuple[str, int, int], int]:
    """Every derived span, as {(cat, i, j): number of RELATION NODES carrying it}."""
    pos = {t: i for i, t in enumerate(toks)}
    pos[eos] = len(toks)
    out: dict[tuple[str, int, int], int] = {}
    for t in toks:
        for r, o in g.relations_from(t):
            p = g.predicate(r)
            if p.startswith("span_") and o in pos:
                out[(p[5:], pos[t], pos[o])] = out.get((p[5:], pos[t], pos[o]), 0) + 1
    return out


def root_spans(g, toks, eos) -> int:
    """How many distinct RELATION NODES assert `clause` over the whole sentence."""
    return sum(1 for r, o in g.relations_from(toks[0])
               if g.has_key(r, sp(ROOT)) and o == eos)


def lexical_spans(lex, toks, names, *, open_class: str | None = None,
                  closed: tuple[str, ...] = CLOSED_CLASSES) -> set[tuple[str, int]]:
    """{(cat, i)} — the categories token `i` carries DIRECTLY from the lexicon (the base case of
    the derivation count; a width-1 span reached by a unary production is not one of these)."""
    out: set[tuple[str, int]] = set()
    for i, nm in enumerate(names):
        cs = lex.get(nm, [])
        for c in cs:
            out.add((c, i))
        if open_class and not any(c in closed for c in cs):
            out.add((open_class, i))
    return out


def count_derivations(chart, unary, binary, lexset, cat, i, j, memo=None, depth=0) -> int:
    """Number of distinct parse TREES for (cat, i, j), reconstructed from the packed chart.

    This is Python, deliberately: the point is that after packing, the derivation count is NOT in
    the graph — it has to be recomputed FROM THE GRAMMAR, which is only possible because the
    grammar is data. See the verdict."""
    memo = {} if memo is None else memo
    key = (cat, i, j)
    if key in memo:
        return memo[key]
    if depth > 24:
        return 1
    if (cat, i, j) not in chart:
        return 0
    total = 1 if (j == i + 1 and (cat, i) in lexset) else 0
    for z, x in unary:
        if z == cat:
            total += count_derivations(chart, unary, binary, lexset, x, i, j, memo, depth + 1)
    for z, x, y in binary:
        if z != cat:
            continue
        for m in range(i + 1, j):
            if (x, i, m) in chart and (y, m, j) in chart:
                total += (count_derivations(chart, unary, binary, lexset, x, i, m, memo, depth + 1)
                          * count_derivations(chart, unary, binary, lexset, y, m, j, memo, depth + 1))
    memo[key] = total
    return total


# ---------------------------------------------------------------------------
# 4. The unpacked variant — derivations as first-class NODES
# ---------------------------------------------------------------------------

def unpacked_bank(lex, unary, binary) -> tuple[list[Rule], frozenset[str]]:
    """The same grammar, but every DERIVATION mints its own `<span>` node (cat/begin/end/children).

    This is what makes ambiguity directly rule-visible: two distinct span nodes with the same
    cat+begin+end IS the ambiguity, and one `Distinct` rule detects it in-engine, with no selector.
    The price is that the forest is no longer packed."""
    rules: list[Rule] = []
    for w, cs in sorted(lex.items()):
        for c in sorted(cs):
            rules.append(Rule(key=f"u.lex.{c}.{w}",
                              lhs=[Pat(f"{w}?", "next", "?u")],
                              rhs=[Pat("<span>?", "cat", c), Pat("<span>?", "begin", f"{w}?"),
                                   Pat("<span>?", "end", "?u")]))
    for z, x in unary:
        rules.append(Rule(key=f"u.un.{z}.{x}",
                          lhs=[Pat("?p", "cat", x), Pat("?p", "begin", "?a"), Pat("?p", "end", "?b")],
                          rhs=[Pat("<span>?", "cat", z), Pat("<span>?", "begin", "?a"),
                               Pat("<span>?", "end", "?b"), Pat("<span>?", "kid", "?p")]))
    for z, x, y in binary:
        rules.append(Rule(key=f"u.bin.{z}.{x}.{y}",
                          lhs=[Pat("?p", "cat", x), Pat("?p", "begin", "?a"), Pat("?p", "end", "?m"),
                               Pat("?q", "cat", y), Pat("?q", "begin", "?m"), Pat("?q", "end", "?b")],
                          rhs=[Pat("<span>?", "cat", z), Pat("<span>?", "begin", "?a"),
                               Pat("<span>?", "end", "?b"), Pat("<span>?", "kid", "?p"),
                               Pat("<span>?", "kid", "?q")]))
    # AMBIGUITY, in-engine, with no branch selection: two DIFFERENT derivations of the same span.
    rules.append(Rule(
        key="u.ambiguous",
        lhs=[Pat("?p", "cat", "?c"), Pat("?q", "cat", "?c"),
             Pat("?p", "begin", "?a"), Pat("?q", "begin", "?a"),
             Pat("?p", "end", "?b"), Pat("?q", "end", "?b")],
        distinct=[Distinct("?p", "?q")],
        rhs=[Pat("?a", "ambiguous_span", "?b")],
    ))
    preds = frozenset({"next", "first", "cat", "begin", "end", "kid", "ambiguous_span"})
    return rules, preds


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------

# The residual failures the Loudon corpus left behind (`spike_loudon.py` §2b), plus a baseline,
# a gibberish line that MUST be refused, and a classic PP-attachment ambiguity.
CASES = [
    ("the lion has a mane",              "baseline — parses today too"),
    ("the lion roars",                   "INTRANSITIVE — two slots, no form today"),
    ("the guzerat lion has no mane",     "NEGATION + modifier — THE EXCEPTION-BEARING SENTENCE"),
    ("the lion lives in africa",         "PREPOSITIONAL — folds to garbage today"),
    ("the lion is smaller than the tiger", "COMPARATIVE"),
    ("glorp the flarn",                  "GIBBERISH — must be REFUSED"),
    ("the lion eats the fish in africa", "AMBIGUOUS — PP attachment"),
]


def today(line: str) -> str:
    """What the shipped form bank does with `line` today."""
    try:
        kb = AttrGraph()
        out = h.ingest(kb, [], line)
        facts = sorted(h.derived_triples(kb))
        return f"{out.kind}: {facts}" if facts else out.kind
    except Exception as e:                              # noqa: BLE001 — reporting a bench result
        return f"error:{type(e).__name__}"


def main() -> None:
    hdr("0  THE GRAMMAR, READ BACK OUT OF CNL")
    lex, unary, binary = read_grammar(GRAMMAR_CNL)
    print(f"  lexicon     : {len(lex)} words")
    print(f"  unary  prods: {unary}")
    print(f"  binary prods: {len(binary)}")
    for b in binary:
        print(f"      {b[0]} -> {b[1]} {b[2]}")
    if not unary or not binary:
        print("  !! the production forms did not read back — everything below is meaningless")
        return

    bank, preds = chart_bank(lex, unary, binary)
    print(f"\n  generated chart rules: {len(bank)}")

    hdr("1  COVERAGE — the residual failures, closed lexicon")
    print("  A parse EXISTS iff `clause` spans the whole sentence. No parse = REFUSE, which is the")
    print("  diagnostic a bank of independent surface patterns structurally cannot produce.\n")
    for line, note in CASES:
        g, toks, eos = parse(line, bank, preds)
        n = root_spans(g, toks, eos)
        verdict = "REFUSED " if n == 0 else f"parsed({n} root split{'s' if n > 1 else ''})"
        print(f"    {verdict}  {line:36}  [{note}]")
        print(f"{'':14}  today: {today(line)}")

    hdr("2  AMBIGUITY — is it VISIBLE without selecting a branch?")
    print("  Three numbers per sentence:")
    print("    root  = distinct relation nodes asserting `clause` over the whole span (in-graph)")
    print("    trees = actual parse trees, recomputed from the packed chart + the grammar")
    print("    amb   = does the UNPACKED bank's one `Distinct` rule flag an ambiguous span?\n")
    for line, _note in CASES:
        g, toks, eos = parse(line, bank, preds)
        chart = spans(g, toks, eos)
        if not root_spans(g, toks, eos):
            print(f"    {line:36}  (no parse)")
            continue
        lexset = lexical_spans(lex, toks, [g.name(t) for t in toks])
        trees = count_derivations(chart, unary, binary, lexset, ROOT, 0, len(toks))
        ub, upreds = unpacked_bank(lex, unary, binary)
        g2, toks2, eos2 = parse(line, ub, upreds)
        flagged = any(g2.has_key(r, "ambiguous_span") for t in toks2
                      for r, _o in g2.relations_from(t))
        print(f"    {line:36}  root={root_spans(g, toks, eos)}  trees={trees}  amb={flagged}")

    hdr("2b  AMBIGUITY IN THE PACKED CHART — usefulness pass + one Distinct")
    print("  If this works, the crux is answered WITHOUT paying for the unpacked forest: the")
    print("  packed chart stays polynomial AND says `this sentence has two readings`.\n")
    abank, apreds = ambiguity_bank(unary, binary)
    print(f"  generated ambiguity rules: {len(abank)}\n")
    for line, _note in CASES:
        g, toks, eos = parse(line, bank + abank, preds | apreds)
        n = root_spans(g, toks, eos)
        if not n:
            print(f"    {line:36}  (no parse)")
            continue
        chart = spans(g, toks, eos)
        lexset = lexical_spans(lex, toks, [g.name(t) for t in toks])
        trees = count_derivations(chart, unary, binary, lexset, ROOT, 0, len(toks))
        flagged = [(g.name(t), g.name(o)) for t in toks
                   for r, o in g.relations_from(t) if g.has_key(r, "ambiguous")]
        print(f"    {line:36}  trees={trees}  flagged={bool(flagged)}  at={flagged}")

    hdr("3  OPEN VOCABULARY — the lexicon wall")
    print("  A chart grammar needs every word classified. Real prose does not oblige. The default:")
    print("  a word in NO declared closed class also spans as a noun (one NAC rule over a declared")
    print("  tag). Question: does refusal survive it?\n")
    obank, opreds = chart_bank(lex, unary, binary, open_class="noun")
    extra = CASES + [("the bramble is smaller than the tiger", "UNDECLARED content word"),
                     ("the lion eats the bramble", "UNDECLARED object")]
    for line, note in extra:
        g, toks, eos = parse(line, obank, opreds)
        n = root_spans(g, toks, eos)
        chart = spans(g, toks, eos)
        lexset = lexical_spans(lex, toks, [g.name(t) for t in toks], open_class="noun")
        trees = count_derivations(chart, unary, binary, lexset, ROOT, 0, len(toks)) if n else 0
        print(f"    {'REFUSED ' if n == 0 else 'parsed  ':9} trees={trees:<4} {line:38} [{note}]")

    hdr("4  COST — against the ~12 ms/utterance budget")
    for label, (bnk, prd) in (("packed, closed lexicon", (bank, preds)),
                              ("packed, open vocabulary", (obank, opreds)),
                              ("packed + ambiguity pass", (obank + abank, opreds | apreds)),
                              ("unpacked (derivations)", unpacked_bank(lex, unary, binary))):
        times = []
        for line, _n in CASES:
            t0 = time.perf_counter()
            parse(line, bnk, prd)
            times.append((time.perf_counter() - t0) * 1000)
        print(f"    {label:28} mean {sum(times) / len(times):6.1f} ms   max {max(times):6.1f} ms")

    print("\n  scaling in sentence length (packed, open vocabulary):")
    base = "the lion eats the fish"
    for k in range(0, 5):
        line = base + " in africa" * k
        t0 = time.perf_counter()
        g, toks, eos = parse(line, obank, opreds)
        ms = (time.perf_counter() - t0) * 1000
        chart = spans(g, toks, eos)
        lexset = lexical_spans(lex, toks, [g.name(t) for t in toks], open_class="noun")
        trees = count_derivations(chart, unary, binary, lexset, ROOT, 0, len(toks))
        print(f"    {len(toks):2} tokens  {ms:7.1f} ms  spans={len(chart):4}  trees={trees}")

    print("\n  scaling in sentence length (unpacked / derivation nodes):")
    ub, upreds = unpacked_bank(lex, unary, binary)
    for k in range(0, 4):
        line = base + " in africa" * k
        t0 = time.perf_counter()
        g2, toks2, _e = parse(line, ub, upreds)
        ms = (time.perf_counter() - t0) * 1000
        nodes = sum(1 for n in g2.nodes() if g2.name(n) == "<span>")
        print(f"    {len(toks2):2} tokens  {ms:7.1f} ms  span nodes={nodes}")


if __name__ == "__main__":
    main()
