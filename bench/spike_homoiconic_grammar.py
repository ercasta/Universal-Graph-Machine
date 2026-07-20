"""
BENCH — the measurements behind the homoiconic-grammar design decisions.

The machinery now lives in `ugm/cnl/grammar.py` (behaviours pinned by `tests/test_grammar.py`);
what stays here is the EVIDENCE, because each number decided a design question and none of it is
reproducible from the module alone:

  1. coverage + refusal on the residual Loudon failures, against what the shipped bank does today
  2. AMBIGUITY: why counting root spans fails, why the unpacked forest is unaffordable, and that
     the packed usefulness pass is exact  (`homoiconic_grammar.md` §8.3 — the crux)
  3. open vocabulary, and that REFUSAL SURVIVES IT
  4. cost, and the span-vs-tree curve that is the whole argument for keeping the chart packed

Run: python bench/spike_homoiconic_grammar.py
"""
from __future__ import annotations

import pathlib
import time

import ugm as h
from ugm import AttrGraph, Pat, Rule, derived_triples, run_bank
from ugm.cnl.forms import _chain_tokens, tokenize
from ugm.cnl.grammar import (AMBIGUOUS, PARSED, REFUSED, ROOT, ambiguity_bank,
                             chart_bank, compile_grammar, load_grammar_file, parse, sp)

CORPUS = pathlib.Path(__file__).resolve().parent.parent / "corpus"
GRAMMAR_FILE = CORPUS / "lion_grammar.cnl"


def hdr(s: str) -> None:
    print(f"\n{'=' * 78}\n{s}\n{'=' * 78}")


CASES = [
    ("the lion has a mane",                 "baseline — parses today too"),
    ("the lion roars",                      "INTRANSITIVE — two slots, no form today"),
    ("the guzerat lion has no mane",        "NEGATION + modifier — THE EXCEPTION-BEARING SENTENCE"),
    ("the lion lives in africa",            "PREPOSITIONAL — folds to garbage today"),
    ("the lion is smaller than the tiger",  "COMPARATIVE"),
    ("glorp the flarn",                     "GIBBERISH — must be REFUSED"),
    ("the lion eats the fish in africa",    "AMBIGUOUS — PP attachment"),
]


def today(line: str) -> str:
    """What the shipped form bank does with `line`."""
    try:
        kb = AttrGraph()
        out = h.ingest(kb, [], line)
        facts = sorted(derived_triples(kb))
        return f"{out.kind}: {facts}" if facts else out.kind
    except Exception as e:                       # noqa: BLE001 — reporting a bench result
        return f"error:{type(e).__name__}"


# ---------------------------------------------------------------------------
# Measurement-only: the two rejected ambiguity representations
# ---------------------------------------------------------------------------

def _tokenize(g, sentence):
    anchor = tokenize(g, sentence)
    toks = _chain_tokens(g, anchor)
    eos = g.add_node("<eos>", control=True)
    g.add_relation(toks[-1], "next", eos, control=True)
    g.add_relation(eos, "is_eos", g.add_node("yes"), control=True)
    return toks, eos


def spans(g, toks, eos) -> dict[tuple[str, int, int], int]:
    pos = {t: i for i, t in enumerate(toks)}
    pos[eos] = len(toks)
    out: dict[tuple[str, int, int], int] = {}
    for t in toks:
        for r, o in g.relations_from(t):
            p = g.predicate(r)
            if p.startswith("span_") and o in pos:
                key = (p[5:], pos[t], pos[o])
                out[key] = out.get(key, 0) + 1
    return out


def lexical_spans(gram, names, *, open_class=None) -> set[tuple[str, int]]:
    """{(cat, i)} — categories token `i` carries DIRECTLY from the lexicon: the base case of the
    derivation count (a width-1 span reached by a unary production is not one of these).

    MIRRORS `chart_bank`'s open-class rule and must be re-checked whenever that changes — this
    harness duplicating the pipeline is the trap the plan has recorded twice. Updated 2026-07-20:
    the default applies to words the grammar declares NOTHING about, not to every word outside a
    closed class."""
    out: set[tuple[str, int]] = set()
    for i, nm in enumerate(names):
        cs = gram.lexicon.get(nm, [])
        for c in cs:
            out.add((c, i))
        if open_class and not cs:
            out.add((open_class, i))
    return out


def count_derivations(chart, gram, lexset, cat, i, j, memo=None, depth=0) -> int:
    """Parse TREES for (cat, i, j), reconstructed from the packed chart.

    Python, deliberately: after packing, the derivation count is NOT in the graph — it has to be
    recomputed FROM THE GRAMMAR, which is only possible because the grammar is data."""
    memo = {} if memo is None else memo
    key = (cat, i, j)
    if key in memo:
        return memo[key]
    if depth > 24 or (cat, i, j) not in chart:
        return 1 if depth > 24 else 0
    total = 1 if (j == i + 1 and (cat, i) in lexset) else 0
    for z, x in gram.unary:
        if z == cat:
            total += count_derivations(chart, gram, lexset, x, i, j, memo, depth + 1)
    for z, x, y in gram.binary:
        if z != cat:
            continue
        for m in range(i + 1, j):
            if (x, i, m) in chart and (y, m, j) in chart:
                total += (count_derivations(chart, gram, lexset, x, i, m, memo, depth + 1)
                          * count_derivations(chart, gram, lexset, y, m, j, memo, depth + 1))
    memo[key] = total
    return total


def unpacked_bank(gram) -> tuple[list[Rule], frozenset[str]]:
    """The REJECTED alternative: every DERIVATION mints its own node, so ambiguity is one `Distinct`
    rule — correct, and unaffordable (the count is Catalan)."""
    rules: list[Rule] = []
    for w, cs in sorted(gram.lexicon.items()):
        for c in sorted(cs):
            rules.append(Rule(key=f"u.lex.{c}.{w}",
                              lhs=[Pat(f"{w}?", "next", "?u")],
                              rhs=[Pat("<span>?", "cat", c), Pat("<span>?", "begin", f"{w}?"),
                                   Pat("<span>?", "end", "?u")]))
    for z, x in gram.unary:
        rules.append(Rule(key=f"u.un.{z}.{x}",
                          lhs=[Pat("?p", "cat", x), Pat("?p", "begin", "?a"), Pat("?p", "end", "?b")],
                          rhs=[Pat("<span>?", "cat", z), Pat("<span>?", "begin", "?a"),
                               Pat("<span>?", "end", "?b"), Pat("<span>?", "kid", "?p")]))
    for z, x, y in gram.binary:
        rules.append(Rule(key=f"u.bin.{z}.{x}.{y}",
                          lhs=[Pat("?p", "cat", x), Pat("?p", "begin", "?a"), Pat("?p", "end", "?m"),
                               Pat("?q", "cat", y), Pat("?q", "begin", "?m"), Pat("?q", "end", "?b")],
                          rhs=[Pat("<span>?", "cat", z), Pat("<span>?", "begin", "?a"),
                               Pat("<span>?", "end", "?b"), Pat("<span>?", "kid", "?p"),
                               Pat("<span>?", "kid", "?q")]))
    return rules, frozenset({"next", "first", "cat", "begin", "end", "kid"})


def main() -> None:
    gram = load_grammar_file(GRAMMAR_FILE)
    banks = compile_grammar(gram)
    obanks = compile_grammar(gram, open_class="noun")

    hdr("0  THE GRAMMAR, READ BACK OUT OF CNL")
    print(f"  lexicon {len(gram.lexicon)}   unary {len(gram.unary)}   binary {len(gram.binary)}")
    print(f"  generated: chart {len(banks.chart)}  useful/ambiguity {len(banks.ambiguity)}"
          f"  spans {len(banks.spans)}  slots {len(banks.slots)}  assert {len(banks.asserts)}")

    hdr("1  COVERAGE + REFUSAL — the residual Loudon failures")
    for line, note in CASES:
        outcome = parse(AttrGraph(), line, banks)[0]
        print(f"    {outcome:9} {line:36} [{note}]")
        print(f"{'':14} today: {today(line)}")

    hdr("2  AMBIGUITY — the three representations (the crux, §8.3)")
    print("    root   = distinct relation nodes asserting `clause` over the whole span")
    print("    trees  = actual parse trees, recomputed from the packed chart + the grammar")
    print("    packed = does the USEFULNESS pass + `Distinct` flag it?  (the answer)")
    print("    unpckd = does the unpacked forest flag it?  (correct but unaffordable)\n")
    ub, upreds = unpacked_bank(gram)
    for line, _n in CASES:
        g = AttrGraph()
        toks, eos = _tokenize(g, line)
        run_bank(g, banks.chart, control_preds=banks.chart_preds)
        root = sum(1 for r, o in g.relations_from(toks[0])
                   if g.has_key(r, sp(ROOT)) and o == eos)
        if not root:
            print(f"    {line:36} (no parse)")
            continue
        chart = spans(g, toks, eos)
        lexset = lexical_spans(gram, [g.name(t) for t in toks])
        trees = count_derivations(chart, gram, lexset, ROOT, 0, len(toks))
        run_bank(g, banks.ambiguity, control_preds=banks.ambiguity_preds)
        packed = any(g.has_key(r, "ambiguous") for t in toks for r, _o in g.relations_from(t))
        g2 = AttrGraph()
        t2, _e2 = _tokenize(g2, line)
        run_bank(g2, ub, control_preds=upreds)
        seen: dict[tuple, int] = {}
        for n in g2.nodes():
            if g2.name(n) != "<span>":
                continue
            k = tuple(next((o for r, o in g2.relations_from(n) if g2.has_key(r, s)), None)
                      for s in ("cat", "begin", "end"))
            seen[k] = seen.get(k, 0) + 1
        unpckd = any(v > 1 for v in seen.values())
        print(f"    {line:36} root={root} trees={trees:<3} packed={packed!s:5} unpckd={unpckd}")

    hdr("3  OPEN VOCABULARY — and that REFUSAL SURVIVES IT")
    extra = [(l, n) for l, n in CASES] + [
        ("the bramble is smaller than the tiger", "UNDECLARED content word"),
        ("the lion eats the bramble", "UNDECLARED object")]
    for line, note in extra:
        print(f"    {parse(AttrGraph(), line, obanks)[0]:9} {line:38} [{note}]")

    hdr("4  COST")
    for label, bk in (("packed, closed lexicon", banks), ("packed, open vocabulary", obanks)):
        times = []
        for line, _n in CASES:
            t0 = time.perf_counter()
            parse(AttrGraph(), line, bk)
            times.append((time.perf_counter() - t0) * 1000)
        print(f"    {label:26} mean {sum(times) / len(times):6.1f} ms  max {max(times):6.1f} ms")

    print("\n  SPANS GROW POLYNOMIALLY WHILE TREES EXPLODE — the whole argument for the packed")
    print("  chart in one table, and the reason the answer to ambiguity must be ASK, never enumerate:")
    base = "the lion eats the fish"
    for k in range(5):
        line = base + " in africa" * k
        g = AttrGraph()
        toks, eos = _tokenize(g, line)
        t0 = time.perf_counter()
        run_bank(g, obanks.chart, control_preds=obanks.chart_preds)
        ms = (time.perf_counter() - t0) * 1000
        chart = spans(g, toks, eos)
        lexset = lexical_spans(gram, [g.name(t) for t in toks], open_class="noun")
        trees = count_derivations(chart, gram, lexset, ROOT, 0, len(toks))
        print(f"    {len(toks):2} tokens  {ms:7.1f} ms  spans={len(chart):4}  trees={trees}")

    print("\n  the UNPACKED alternative on the same curve (rejected):")
    for k in range(4):
        line = base + " in africa" * k
        g = AttrGraph()
        toks, _e = _tokenize(g, line)
        t0 = time.perf_counter()
        run_bank(g, ub, control_preds=upreds)
        ms = (time.perf_counter() - t0) * 1000
        nodes = sum(1 for n in g.nodes() if g.name(n) == "<span>")
        print(f"    {len(toks):2} tokens  {ms:7.1f} ms  span nodes={nodes}")


if __name__ == "__main__":
    main()
