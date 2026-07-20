"""
BENCH — the homoiconic grammar against RAW BOOK PROSE (the measurement the arc kept deferring).

WHY THIS EXISTS. Every coverage number the grammar arc has produced so far — including
"19/19 (100%) parsed on the FIRST pass" — was measured on the CNL LINES AN LLM PRODUCED FROM the
50 sentences, not on the sentences. That caveat is recorded in the plan and in
`bench/spike_loudon_grammar.py`, but it is easy to lose, and the arc's stated goal is to read BOOKS.
This runs the same grammar against the VERBATIM text and reports the gap.

THE EXPECTED RESULT IS BAD, AND THAT IS THE POINT. `corpus/loudon_grammar.cnl` was written for the
CNL translations; raw Victorian prose is 30-60 tokens a sentence with subordinate clauses, quoted
narrative and semicolons. A number near zero is the honest baseline. What makes the run WORTH
something is the DECOMPOSITION: of the sentences that fail, how many fail for a MECHANICAL reason
(the tokenizer splits on whitespace only, so `beasts,` is not `beasts`) versus a VOCABULARY reason
(the word was never declared) versus a CONSTRUCTION reason (every word is known and it still does
not parse). Those three have wildly different costs to fix, and only the third is the deep problem
that form learning (learning_design §7.1, slice S2b) exists to attack.

FOUR NUMBERS:
  1. VERBATIM COVERAGE — what fraction of raw sentences parse, as-is.
  2. THE TOKENIZER'S SHARE — the same, with punctuation stripped. The delta is a mechanical fix.
  3. VOCABULARY — token-level OOV against the declared lexicon, and how many sentences are
     FULLY covered by it. A sentence with an unknown word cannot parse, so this bounds 1 and 2.
  4. THE RESIDUAL — sentences whose every word IS declared and which STILL do not parse. This is
     the specification for what the grammar is missing, and it is the only number that describes a
     LINGUISTIC gap rather than a clerical one.

Run: python bench/spike_loudon_prose.py
"""
from __future__ import annotations

import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from ugm import AttrGraph
from ugm.cnl.grammar import (AMBIGUOUS, PARSED, REFUSED, compile_grammar, load_grammar, parse)

from loudon_lion_corpus import SENTENCES, cnl_lines

CORPUS = pathlib.Path(__file__).resolve().parent.parent / "corpus"
GRAMMAR_FILE = CORPUS / "loudon_grammar.cnl"

#: Whitespace-only tokenization is `forms.tokenize`'s documented contract ("a real tokenizer would
#: handle punctuation/casing — that is still a tool, never a rule"). Stripping it here measures what
#: that tool would buy; it does NOT change the grammar.
PUNCT = re.compile(r"[^a-z0-9\s]")


def hdr(s: str) -> None:
    print(f"\n{'=' * 78}\n{s}\n{'=' * 78}")


def depunctuate(s: str) -> str:
    return PUNCT.sub(" ", s.lower())


def verdict(sentence: str, banks) -> str:
    """Parse into a FRESH graph — this measures the grammar, not session accretion."""
    if not sentence.strip():
        return REFUSED
    return parse(AttrGraph(), sentence, banks)[0]


def main() -> None:
    gram = load_grammar(GRAMMAR_FILE.read_text(encoding="utf-8"))
    banks = compile_grammar(gram)
    known = set(gram.lexicon)
    verbatim = [(n, src) for n, src, _lines, _why in SENTENCES]

    hdr("0  THE BASELINE THIS IS BEING COMPARED AGAINST")
    cnl = list(dict.fromkeys(cnl_lines()))
    cnl_ok = sum(1 for ln in cnl if verdict(ln, banks) == PARSED)
    print(f"    CNL translations : {cnl_ok}/{len(cnl)} parsed  ({cnl_ok / len(cnl):.0%})")
    print("    ^ this is the number the arc has been quoting. It is a real result about the")
    print("      GRAMMAR, but it is not a result about reading a BOOK.")

    hdr("1  VERBATIM COVERAGE — the raw sentences, exactly as printed")
    t0 = time.perf_counter()
    raw = {n: verdict(src, banks) for n, src in verbatim}
    ms = (time.perf_counter() - t0) * 1000
    n = len(verbatim)
    for kind in (PARSED, AMBIGUOUS, REFUSED):
        got = [k for k, v in raw.items() if v == kind]
        print(f"    {kind:9} {len(got):2}/{n}  ({len(got) / n:.0%})")
    print(f"\n    {ms / n:.1f} ms/sentence")

    hdr("2  THE TOKENIZER'S SHARE — same sentences, punctuation stripped")
    clean = {n: verdict(depunctuate(src), banks) for n, src in verbatim}
    c_ok = sum(1 for v in clean.values() if v == PARSED)
    r_ok = sum(1 for v in raw.values() if v == PARSED)
    print(f"    parsed    {c_ok:2}/{n}  ({c_ok / n:.0%})   raw was {r_ok}/{n}")
    print(f"    delta attributable to whitespace-only tokenization: {c_ok - r_ok} sentence(s)")

    hdr("3  VOCABULARY — is the word even declared?")
    print(f"    declared lexicon: {len(known)} words\n")
    oov_total = tok_total = 0
    fully_covered: list[int] = []
    per_sentence: list[tuple[int, int, int, list[str]]] = []
    for i, src in verbatim:
        toks = depunctuate(src).split()
        oov = [t for t in toks if t not in known]
        tok_total += len(toks)
        oov_total += len(oov)
        per_sentence.append((i, len(toks), len(oov), oov))
        if not oov:
            fully_covered.append(i)
    print(f"    tokens              : {tok_total}")
    print(f"    out-of-vocabulary   : {oov_total}  ({oov_total / tok_total:.0%})")
    print(f"    sentences fully covered by the lexicon: {len(fully_covered)}/{n} "
          f"({len(fully_covered) / n:.0%})   {fully_covered}")
    lens = sorted(t for _i, t, _o, _w in per_sentence)
    print(f"\n    sentence length (tokens): min {lens[0]}, median {lens[len(lens) // 2]}, "
          f"max {lens[-1]}")
    print(f"    CNL line length         : median "
          f"{sorted(len(l.split()) for l in cnl)[len(cnl) // 2]}")
    print("\n    ^ A sentence containing an undeclared word CANNOT parse, so this bounds §1 and §2.")
    print("      Open-vocabulary mode exists (`compile_grammar(open_class=...)`) and would change")
    print("      this bound, at the cost of refusal — deliberately NOT enabled here, because the")
    print("      question is what the SHIPPED grammar does.")

    hdr("4  THE RESIDUAL — every word declared, and it still does not parse")
    residual = [i for i in fully_covered if clean[i] != PARSED]
    print(f"    fully-covered sentences that still fail: {len(residual)}/{len(fully_covered)}")
    for i in residual:
        src = next(s for j, s in verbatim if j == i)
        toks = len(depunctuate(src).split())
        print(f"\n      [{i}] ({toks} tokens) {src[:150]}")
        print(f"          verdict: {clean[i]}")
    if not residual:
        print("      (none — every failure above is a vocabulary or tokenizer failure)")

    hdr("5  WHERE THE FAILURES ACTUALLY LIVE")
    worst = sorted(per_sentence, key=lambda r: -r[2])[:8]
    print("    The 8 sentences with the most undeclared words — the vocabulary the grammar would")
    print("    need before any construction question can even be ASKED:\n")
    for i, ntok, noov, oov in worst:
        print(f"      [{i:2}] {noov:2}/{ntok:2} unknown: {' '.join(sorted(set(oov))[:12])}")

    hdr("6  LIFTING THE VOCABULARY WALL — open-vocabulary mode")
    print("    §4 came back 0/0: NO sentence is fully covered, so the construction question could")
    print("    not even be ASKED. Open-vocabulary mode (one NAC rule over the declared closed")
    print("    classes: any token not declared closed spans as `noun`) removes exactly that wall,")
    print("    which is what makes the residual measurable. This is the SHIPPED mechanism, not a")
    print("    bench trick — but note it trades away refusal, so a `parsed` here is weaker evidence")
    print("    than a `parsed` above.\n")
    obanks = compile_grammar(gram, open_class="noun")
    open_raw = {i: verdict(depunctuate(src), banks=obanks) for i, src in verbatim}
    o_ok = [i for i, v in open_raw.items() if v == PARSED]
    o_amb = [i for i, v in open_raw.items() if v == AMBIGUOUS]
    print(f"    parsed    {len(o_ok):2}/{n}  ({len(o_ok) / n:.0%})   {o_ok}")
    print(f"    ambiguous {len(o_amb):2}/{n}  ({len(o_amb) / n:.0%})   {o_amb}")
    print(f"    refused   {n - len(o_ok) - len(o_amb):2}/{n}")
    ocnl = sum(1 for ln in cnl if verdict(ln, obanks) == PARSED)
    print(f"\n    (sanity: the CNL baseline under the same open grammar is {ocnl}/{len(cnl)})")
    short = sorted((t, i) for i, t, _o, _w in per_sentence)[:10]
    print("\n    The 10 SHORTEST sentences and their open-vocabulary verdict — the most likely")
    print("    place for a construction to be within reach:\n")
    for ntok, i in short:
        src = next(s for j, s in verbatim if j == i)
        print(f"      [{i:2}] {ntok:2} tok  {open_raw[i]:9}  {src[:88]}")

    hdr("7  DISTANCE TO A PARSE — how much of each sentence can the chart actually span?")
    print("    '0/50 refused' does not say whether we are one construction away or nowhere near.")
    print("    The chart is built even when the parse fails, so the LONGEST constituent it derives")
    print("    is a real distance metric: a sentence whose best span covers 90% of its tokens is")
    print("    one missing production from parsing; one stuck at 10% is not a grammar-gap story.\n")
    widths: list[tuple[float, int, int, int]] = []
    for i, src in verbatim:
        g = AttrGraph()
        _out, toks, eos = parse(g, depunctuate(src), obanks)
        if not toks:
            continue
        pos = {t: k for k, t in enumerate(toks)}
        pos[eos] = len(toks)
        best = 1
        for t in toks:
            for r, o in g.relations_from(t):
                if o in pos and g.predicate(r).startswith("span_"):
                    best = max(best, pos[o] - pos[t])
        widths.append((best / len(toks), i, best, len(toks)))
    widths.sort(reverse=True)
    print("    BEST-COVERED sentences (longest constituent / sentence length):\n")
    for frac, i, best, ntok in widths[:10]:
        src = next(s for j, s in verbatim if j == i)
        print(f"      [{i:2}] {frac:4.0%}  {best:2}/{ntok:2} tok  {src[:78]}")
    avg = sum(f for f, _i, _b, _t in widths) / len(widths)
    near = [w for w in widths if w[0] >= 0.8]
    print(f"\n    mean coverage of the longest constituent: {avg:.0%}")
    print(f"    sentences within 80% of a full span      : {len(near)}/{len(widths)}")

    hdr("8  WHAT THIS MEANS FOR THE ARC")
    print(f"    translatability (the SOURCE's property, from spike_loudon): "
          f"{sum(1 for _n, _s, l, _w in SENTENCES if l)}/{n} sentences assert an extractable fact")
    print(f"    grammar on CNL       : {cnl_ok}/{len(cnl)}")
    print(f"    grammar on raw prose : {r_ok}/{n} as-printed, {c_ok}/{n} de-punctuated")
    print("\n    THE DECOMPOSITION CAME BACK DEGENERATE, AND THAT IS THE RESULT.")
    print("      * tokenizer  contributes 0 — de-punctuating changed nothing;")
    print("      * vocabulary contributes 0 — lifting the wall entirely (§6) changed nothing;")
    print("      * so the gap is 100% CONSTRUCTIONAL.")
    print("\n    And §7 says it is not a near miss. The longest constituent the chart can build")
    print("    covers ~13% of a sentence on average, best case 31%, and ZERO sentences come within")
    print("    80% of a full span. This is not 'a few missing productions' — the grammar builds")
    print("    3-4 token fragments inside 13-22 token sentences.")
    print("\n    CONSEQUENCE FOR THE PLAN. Two things that were on the roadmap are now measured as")
    print("    not-viable-as-stated, and it is better to know before building either:")
    print("      1. Growing `loudon_grammar.cnl` toward prose sentence-by-sentence. The distance is")
    print("         not incremental; real prose here is subordination, coordination, quoted speech,")
    print("         passives, relatives and possessives, all at once, in every sentence.")
    print("      2. FORM LEARNING BY ALIGNMENT (learning_design §7.1 / slice S2b) as the route to")
    print("         prose. Alignment mints a form by matching an unrecognized utterance against the")
    print("         structure its rephrasing produced — but at 13% coverage there is essentially no")
    print("         structure to align against. S2b may still be right for CNL-adjacent input; it")
    print("         is not a path from here to books.")
    print("\n    WHAT THE ARCHITECTURE ACTUALLY SAYS. The NL->CNL boundary is already assigned to an")
    print("    SLM in the Phase 8 client design, and `loudon_lion_corpus.py` is exactly that step")
    print("    done by hand. Read that way this run is not a failure: it says the LLM translation")
    print("    is LOAD-BEARING rather than scaffolding to be removed, and the grammar's real value")
    print("    is what it does ON the CNL — refusing cleanly, detecting ambiguity instead of")
    print("    guessing, landing the marked EXCEPTION (`has no mane`) that a form bank drops, and")
    print("    supporting contradiction-driven re-interpretation. Those are the things that were")
    print("    biasing the learner, and they are fixed. The open question is whether 'reading")
    print("    books' should mean raw prose in, or CNL-from-an-LLM in - that is a scope decision,")
    print("    and this bench exists so it is made on numbers rather than on the 19/19.")


if __name__ == "__main__":
    main()
