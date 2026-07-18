"""
BENCH — the homoiconic grammar against the Loudon corpus (integration step 3).

Everything the grammar arc measured so far ran on 7 sentences chosen to exercise gaps we already
knew about. This runs it against `bench/loudon_lion_corpus.py` — 50 verbatim sentences of Mrs.
Loudon's *Entertaining Naturalist*, translated to CNL with every sentence recorded — which is the
same instrument `bench/spike_loudon.py` used to re-point the plan, so the numbers are comparable.

PROTOCOL. `corpus/loudon_grammar.cnl` was written in ONE pass from the corpus VOCABULARY plus
ordinary English constructions, BEFORE running it. The first-pass number is recorded below whatever
it turns out to be; a grammar iterated against its own failures would measure nothing.

FOUR NUMBERS:
  1. COVERAGE — parsed / refused / ambiguous, against what the shipped bank does today.
  2. FACTS — what actually lands in the KB, and whether it is right.
  3. THE EXCEPTION — this corpus contains the generalization AND its counterexample
     (bengal/persian lions have manes; the Guzerat lion has none). Does the KB now hold both?
  4. CONTRADICTION — under the percolating reading it should DERIVE one; under the minting
     reading it should not.

Run: python bench/spike_loudon_grammar.py
"""
from __future__ import annotations

import pathlib
import time

import ugm as h
from ugm import AttrGraph, derived_triples
from ugm.cnl.grammar import (AMBIGUOUS, PARSED, REFUSED, compile_grammar, load_grammar,
                             parse, parse_batch)
from ugm.interpretation import (contradictions, culprits, describe, interpret,
                                open_scope, scope_facts)

from loudon_lion_corpus import cnl_lines

CORPUS = pathlib.Path(__file__).resolve().parent.parent / "corpus"
GRAMMAR_FILE = CORPUS / "loudon_grammar.cnl"

PERCOLATE = "slot head in np from modifier plus np is right head"
MINT = "mint head in np from modifier plus np under right head"


def hdr(s: str) -> None:
    print(f"\n{'=' * 78}\n{s}\n{'=' * 78}")


def today(line: str) -> str:
    try:
        kb = AttrGraph()
        out = h.ingest(kb, [], line)
        facts = sorted(derived_triples(kb))
        return f"{out.kind}: {facts}" if facts else out.kind
    except Exception as e:                       # noqa: BLE001 — reporting a bench result
        return f"error:{type(e).__name__}"


def main() -> None:
    lines = list(dict.fromkeys(cnl_lines()))
    text = GRAMMAR_FILE.read_text(encoding="utf-8")
    banks = compile_grammar(load_grammar(text))
    mint_banks = compile_grammar(load_grammar(text.replace(PERCOLATE, MINT)))

    hdr("1  COVERAGE — the whole corpus, one line at a time")
    n = len(lines)
    t0 = time.perf_counter()
    verdicts = [parse(AttrGraph(), ln, banks)[0] for ln in lines]   # each in its own graph
    ms = (time.perf_counter() - t0) * 1000
    for kind in (PARSED, AMBIGUOUS, REFUSED):
        got = [v for v in verdicts if v == kind]
        print(f"    {kind:9} {len(got):2}/{n}  ({len(got) / n:.0%})")
    print(f"\n    {ms / n:.1f} ms/line\n")
    for line, outcome in zip(lines, verdicts):
        flag = "    " if outcome == PARSED else " !! "
        print(f"  {flag}{outcome:9} {line:44}")
        if outcome != PARSED:
            print(f"{'':16}today: {today(line)}")

    hdr("2  FACTS — the whole corpus into one KB (minting reading)")
    g = AttrGraph()
    accepted = [ln for ln, v in zip(lines, verdicts) if v == PARSED]
    parsed = [ln for ln, v in zip(accepted, parse_batch(g, accepted, mint_banks)) if v == PARSED]
    scope = open_scope(g)
    interpret(g, mint_banks, scope)          # interning is part of the pass now (identity first)
    facts = scope_facts(g, scope)
    print(f"    lines folded: {len(parsed)}/{n}    facts: {len(facts)}\n")
    for t in facts:
        print(f"        {t}")

    hdr("3  THE EXCEPTION — does the KB hold the generalization AND its counterexample?")
    manes = [t for t in facts if t[1] in ("has", "has_not") and t[2] == "mane"]
    for t in manes:
        print(f"        {t}")
    pos = [t for t in manes if t[1] == "has"]
    neg = [t for t in manes if t[1] == "has_not"]
    print(f"\n    subkinds asserted to HAVE a mane      : {len(pos)}")
    print(f"    subkinds asserted to LACK one         : {len(neg)}")
    print("\n    `bench/spike_loudon.py` §4: the exception was in the corpus, was translated, and")
    print("    was the one sentence the grammar could not take in — so the learner proposed the")
    print("    generalization with its only counterexample removed, and nothing could refute it.")

    hdr("4  CONTRADICTION — percolating vs minting reading")
    for label, bk in (("percolate (one entity per name)", banks),
                      ("mint (a described subkind)", mint_banks)):
        g2 = AttrGraph()
        parse_batch(g2, accepted, bk)
        sc = open_scope(g2)
        interpret(g2, bk, sc)
        cs = contradictions(g2)
        print(f"\n    {label}: {len(cs)} contradiction(s)")
        for about, because in cs:
            print(f"        about {describe(g2, about)!r} because {describe(g2, because)!r}"
                  f"  ({len(culprits(g2, about))} surface mentions behind it)")


if __name__ == "__main__":
    main()
