"""
EXPERIMENT — can UGM learn from a real book? (Mrs. Loudon's *Entertaining Naturalist*, Lion entry.)

Everything in the learning arc so far was measured on 2-4 hand-built entities, and three slices in
a row ended with "the remainder is undecidable on this evidence" — the instrument was exhausted.
This runs the pipeline against prose nobody wrote for it.

Corpus and protocol: `bench/loudon_lion_corpus.py` (fixed contiguous span, every sentence
recorded, nothing silently dropped — the translator is an LLM and would otherwise bias the result
by keeping only what parses).

THREE NUMBERS, deliberately separated, because conflating them would hide where the loss is:
  1. TRANSLATABILITY — sentences that assert an extractable fact. Measures the SOURCE.
  2. INTAKE COVERAGE — CNL lines UGM recognises. Measures UGM's grammar.
  3. LEARNING — rules proposed, and what survives refutation. Measures the arc.

Run: python bench/spike_loudon.py
"""
from __future__ import annotations

import ugm as h
from ugm import AttrGraph, derived_triples
from ugm.learner import learn, observe
from ugm.licensing import refute, render_refutation

from loudon_lion_corpus import SENTENCES, cnl_lines, stats


def hdr(s: str) -> None:
    print(f"\n{'=' * 78}\n{s}\n{'=' * 78}")


_ARTICLES = ("the ", "a ", "an ")
# Multi-word entity names this corpus actually uses (from the book's own vocabulary, not invented).
_ENTITIES = ("african lion", "asiatic lion", "bengal lion", "persian lion", "guzerat lion")


def _strip_article(s: str) -> str:
    for art in _ARTICLES:
        if s.startswith(art):
            return s[len(art):]
    return s


def _join_entities(s: str) -> str:
    for ent in _ENTITIES:
        s = s.replace(ent, ent.replace(" ", "_"))
    return s


def _is_spo(s: str) -> bool:
    """A bare three-slot S P O — no preposition, no missing object."""
    toks = [t for t in s.split() if t not in ("a", "an", "the")]
    return len(toks) == 3


def _parses(line: str) -> bool:
    try:
        return h.ingest(AttrGraph(), [], line).kind == "fact"
    except Exception:
        return False


def _why(line: str) -> str:
    toks = [t for t in line.split() if t not in ("a", "an", "the")]
    if len(toks) < 3:
        return "intransitive: fewer than three slots"
    if len(toks) > 3:
        return "more than three slots (preposition / comparative / negation)"
    return "three slots but still unrecognised"


def main() -> None:
    hdr("1  TRANSLATABILITY — what fraction of real prose asserts an extractable fact?")
    st = stats()
    n, yielded = st["sentences"], st["sentences_yielding_facts"]
    print(f"  sentences in the fixed span            : {n}")
    print(f"  sentences yielding at least one fact   : {yielded}  ({yielded / n:.0%})")
    print(f"  CNL lines produced                     : {st['cnl_lines']} "
          f"({st['distinct_cnl_lines']} distinct)")
    print("\n  Why the rest yielded nothing (grouped):")
    reasons: dict[str, int] = {}
    for _i, _src, lines, why in SENTENCES:
        if not lines:
            key = why.split(";")[0].split(",")[0].strip()
            reasons[key] = reasons.get(key, 0) + 1
    for why, count in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"    {count:3}  {why}")

    hdr("2  INTAKE COVERAGE — how much of the produced CNL does UGM recognise?")
    kb = AttrGraph()
    rules: list = []
    recognized, unrecognized = [], []
    for line in dict.fromkeys(cnl_lines()):            # distinct, in order
        try:
            out = h.ingest(kb, rules, line)
            kind = out.kind
        except Exception as e:
            kind = f"error:{type(e).__name__}"
        (recognized if kind not in ("unrecognized",) and not kind.startswith("error")
         else unrecognized).append((line, kind))
    total = len(recognized) + len(unrecognized)
    print(f"  distinct CNL lines fed : {total}")
    print(f"  RECOGNISED             : {len(recognized)}  ({len(recognized) / total:.0%})")
    print(f"  unrecognised           : {len(unrecognized)}")
    print("\n  recognised (line -> route):")
    for line, kind in recognized:
        print(f"    ok   {line:52} [{kind}]")
    if unrecognized:
        print("\n  UNRECOGNISED:")
        for line, kind in unrecognized:
            print(f"    XX   {line:52} [{kind}]")

    print("\n  facts actually in the KB after ingest:")
    for t in sorted(derived_triples(kb)):
        print(f"    {t}")

    hdr("2b  WHICH BLOCKER DOMINATES? coverage under progressive normalisation")
    print("  Each step is a CNL-grammar gap, applied cumulatively. This says what to BUILD,")
    print("  rather than leaving the result at a flat 0%.\n")
    lines = list(dict.fromkeys(cnl_lines()))
    for label, fn in (("raw (as translated)          ", lambda s: s),
                      ("+ strip leading article      ", _strip_article),
                      ("+ join multi-word entities   ", lambda s: _join_entities(_strip_article(s))),
                      ("+ drop prepositional/intrans.", lambda s: _join_entities(_strip_article(s)))):
        variants = [fn(x) for x in lines]
        if label.startswith("+ drop"):
            variants = [v for v in variants if _is_spo(v)]
        ok = sum(1 for v in variants if _parses(v))
        denom = len(lines)
        print(f"    {label} {ok:2}/{denom}  ({ok / denom:.0%})")

    print("\n  residual failures after all normalisations:")
    for line in lines:
        v = _join_entities(_strip_article(line))
        if not _parses(v):
            print(f"    XX  {line:50} -> {v!r}  [{_why(v)}]")



    hdr("3  LEARNING — what does the learner propose from real book facts?")
    # Built from the NORMALISED lines (§2b), so learning is measured on the facts the grammar can
    # actually take in. The normalisation is the two gaps §2b identified, nothing more — no
    # sentence is rewritten to suit the learner.
    kb = AttrGraph()
    for line in dict.fromkeys(cnl_lines()):
        v = _join_entities(_strip_article(line))
        if _parses(v):
            h.ingest(kb, [], v)
    print(f"  facts ingested from the book: {len(derived_triples(kb))}")
    for t in sorted(derived_triples(kb)):
        print(f"    {t}")
    subjects = sorted({s for s, _p, _o in derived_triples(kb)})
    print(f"  observing {len(subjects)} subject(s): {subjects}")
    observe(kb, *subjects)
    try:
        candidates = learn(kb)
    except Exception as e:
        print(f"  learn RAISED {type(e).__name__}: {e}")
        return
    print(f"  candidates proposed: {len(candidates)}")
    for r in candidates:
        body = " and ".join(f"{p.s} {p.p} {p.o}" for p in r.lhs)
        head = " and ".join(f"{p.s} {p.p} {p.o}" for p in r.rhs)
        print(f"    {head}  when  {body}")

    survivors, refuted = refute(candidates, kb)
    print(f"\n  with NO entity marked fully_described: survivors={len(survivors)} "
          f"refuted={len(refuted)}")
    print("  (nothing is refutable without a completeness discriminator — §7.2a)")

    hdr("4  THE RESULT THAT MATTERS — partial intake coverage is NOT neutral")
    facts = set(derived_triples(kb))
    proposed_mane = any("has mane" in " ".join(f"{p.s} {p.p} {p.o}" for p in r.rhs)
                        and "is_a lion" in " ".join(f"{p.s} {p.p} {p.o}" for p in r.lhs)
                        for r in candidates)
    guzerat = sorted(t for t in facts if t[0] == "guzerat_lion")
    print(f"  the learner proposed `?x has mane when ?x is_a lion` : {proposed_mane}")
    print(f"  everything the KB knows about the guzerat lion       : {guzerat}")
    print("""
  The book STATES the exception — sentence 7: "...and the Lion of Guzerat is of a reddish
  brown, WITHOUT ANY MANE." It is in the corpus. It was translated. And it is the sentence the
  grammar could not take in (negation -> more than three slots), so it is absent from the KB.

  The learner therefore proposes the generalization with its one counterexample REMOVED, and
  nothing can refute it. This is not bad luck. Exceptions are LINGUISTICALLY MARKED — "without",
  "no", "unlike", "except", "only ... that" — and those are exactly the constructions a bare
  S-P-O grammar drops. So a partially-covering parser does not lose sentences at random: it
  systematically loses the EXCEPTIONS and keeps the GENERALIZATIONS, biasing whatever learns
  downstream toward confident over-generalization.

  That reframes the intake gaps of §2b. They are not merely a coverage number to improve later;
  while they stand, every learning result over real prose is optimistically biased, and the
  defeasible-exception work has no data to run on.""")


if __name__ == "__main__":
    main()
