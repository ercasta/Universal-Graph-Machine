"""
BENCH — the SURFACE / INTERPRETATION loop, end to end.

Machinery: `ugm/interpretation.py` (behaviours pinned by `tests/test_grammar.py`).
Design: `docs/design/surface_interpretation.md`.

What this shows that a test cannot: the LOOP, legibly.

    surface (immutable)
      -> interpretation A: `the guzerat lion` IS the lion we were discussing   [percolate]
      -> `lion has mane` AND `lion has_not mane`  ->  <contradiction>
      -> walk provenance to the interpretation choices in its support
      -> ASK (do not pick): "one entity, or a kind of it?"
      -> discard the scope, interpret again as a distinct subkind               [mint]
      -> no contradiction; the surface never moved and nothing was re-parsed

Run: python bench/spike_interpretation_scope.py
"""
from __future__ import annotations

import pathlib

from ugm import AttrGraph
from ugm.cnl.grammar import PARSED, compile_grammar, load_grammar, parse
from ugm.interpretation import (contradictions, culprits, describe, discard_scope, interpret,
                                open_scope, scope_facts)

CORPUS = pathlib.Path(__file__).resolve().parent.parent / "corpus"
GRAMMAR_FILE = CORPUS / "lion_grammar.cnl"

PERCOLATE = "slot head in np from modifier plus np is right head"
MINT = "mint head in np from modifier plus np under right head"

SENTENCES = ["the lion has a mane", "the guzerat lion has no mane"]


def hdr(s: str) -> None:
    print(f"\n{'=' * 78}\n{s}\n{'=' * 78}")


def main() -> None:
    text = GRAMMAR_FILE.read_text(encoding="utf-8")
    banks_a = compile_grammar(load_grammar(text))                       # percolate
    banks_b = compile_grammar(load_grammar(text.replace(PERCOLATE, MINT)))   # mint a subkind

    hdr("A  THE SURFACE — parsed once, and never touched again")
    g = AttrGraph()
    for line in SENTENCES:
        print(f"    {parse(g, line, banks_a)[0]:9} {line}")
    surface = set(g.nodes())
    print(f"\n    surface nodes: {len(surface)}  (tokens, chains, spans — structure only;")
    print("    no entity and no denotation, because a denotation is already a judgement)")

    hdr("B  INTERPRETATION A — `the guzerat lion` is the lion we were discussing")
    scope_a = open_scope(g)
    interpret(g, banks_a, scope_a)
    for t in scope_facts(g, scope_a):
        print(f"        {t}")

    hdr("C  CONTRADICTION — derived, not detected by a checker")
    cs = contradictions(g)
    if not cs:
        print("    none — the demo does not hold")
        return
    for about, because in cs:
        print(f"    <contradiction> about {describe(g, about)!r} because {describe(g, because)!r}")
        mentions = culprits(g, about)
        print(f"    that entity was interpreted from {len(mentions)} surface mentions:")
        for m in mentions:
            print(f"        token {m} {g.name(m)!r}")

    hdr("D  THE QUESTION — the support names a JUDGEMENT, so ask; do not pick")
    print("    Two surface mentions were committed to ONE entity, and that commitment is in the")
    print("    contradiction's support. Nothing about the sentences is in doubt; the reading is.\n")
    print('        "You said lions have manes, and that the guzerat lion has none.')
    print('         Is the guzerat lion the same lion, or a kind of lion?"\n')
    print("    A person answers that instantly and a solver cannot. Same refuse-and-ask shape the")
    print("    ambiguity crux took — culprit selection is a SELECTION problem, so: do not select.")

    hdr("E  DEFEAT THE INTERPRETATION — discard the scope, re-derive")
    gone = discard_scope(g, scope_a, banks_a.slot_preds)
    after = set(g.nodes())
    print(f"    interpretation nodes/edges discarded : {gone}")
    print(f"    surface still intact                 : {surface <= after}  "
          f"({len(surface & after)}/{len(surface)} nodes)")
    print(f"    contradictions remaining             : {len(contradictions(g))}")

    hdr("F  INTERPRETATION B — a distinct subkind, over the SAME untouched surface")
    scope_b = open_scope(g)
    interpret(g, banks_b, scope_b)
    for t in scope_facts(g, scope_b):
        print(f"        {t}")
    print(f"\n    contradictions: {len(contradictions(g))}")
    print("\n    The surface was parsed ONCE. Two readings were built over it and one was thrown")
    print("    away, with no re-parse, no un-merge, and nothing lost — which is the whole claim:")
    print("    the merge can stay destructive because it is destructive only inside a copy.")


if __name__ == "__main__":
    main()
