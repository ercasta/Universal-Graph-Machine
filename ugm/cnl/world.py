"""
The COMPOSITE surface — one text, every layer. A world mixes plain facts, rules, hedged facts,
`either…or`, and comparisons in ONE block of CNL.

`load_world(text)` — PARTLY CONVERGED 2026-07-22 (meaning_surfaces_audit.md §3 step 2): facts, rules
AND comparisons now go through `load_corpus`, which is the ONE ingest path (comparison routes through
intake; `load_corpus` is ingest-in-a-loop). Only HEDGES stay on their own loader, and are authored
LAST — a hedge is a banded FORK (family B) that does NOT survive the fact path's whole-graph
`normalize_surface` re-run on a later line, so it must be written after all fact/rule loading, not
interleaved. Unifying forks with the fact path is scope-generalization's job (audit §2 family B), at
which point hedges can move onto intake too and this special-casing goes away.

`ask_world(kb, rules, question)` — routes a question to its surface: a comparative shape to
`ask_comparative`; `guess X` to the defeasible-guess act (rendered as its honest `why` line);
everything else to `ask_goal` (which, under a banded policy, answers with the band words).
"""
from __future__ import annotations

from ..attrgraph import AttrGraph
from ..production_rule import Rule
from .authoring import load_corpus
from .uncertainty import (
    HEDGE_BAND, parse_hedge_decl, parse_hedge_fact, parse_either, load_line as _load_uncertain_line,
)
from .comparative import parse_comparative_question, ask_comparative, explain_comparative


def _is_hedge(line: str, hedges: dict[str, float]) -> bool:
    return (parse_hedge_decl(line) is not None or parse_either(line) is not None
            or parse_hedge_fact(line, hedges) is not None)


def load_world(text: str, *, policy=None) -> tuple[AttrGraph, list[Rule]]:
    """Author `text`: facts/rules/comparisons through `load_corpus` (the one ingest path), then the
    HEDGE lines LAST (forks do not survive interleaved fact-path normalization — see the module
    docstring). Returns `(kb, rules)`. The hedge lexicon is pre-scanned from the text's own `X means
    N` declarations so a declared hedge routes correctly regardless of its position."""
    lines = text.splitlines()
    hedges = dict(HEDGE_BAND)
    for ln in lines:                                       # pre-scan: a hedge declared anywhere in the
        d = parse_hedge_decl(ln)                           # text applies to every hedged line here
        if d is not None:
            hedges[d[0]] = d[1]
    plain, hedge_lines = [], []
    for ln in lines:
        (hedge_lines if ln.strip() and _is_hedge(ln, hedges) else plain).append(ln)
    kb, rules = load_corpus("\n".join(plain), policy=policy)   # facts/rules/comparisons: one ingest path
    for ln in hedge_lines:                                     # forks LAST, after all fact-path passes
        _load_uncertain_line(kb, ln)
    return kb, rules


def ask_world(kb: AttrGraph, rules: list[Rule], question: str, *, policy=None, **ask_kwargs
              ) -> list[str]:
    """Answer `question` on the composite world. Comparative shapes (`is X more D than Y` /
    `is X as D as Y`) go to the comparative reader; `guess X` performs the defeasible-guess act on
    X's open `is`-slot and answers with its inspectable `why` line; everything else is `ask_goal`
    (pass a `FirmwarePolicy(uncertainty="banded")` to get the graded verdicts)."""
    q = question.strip()
    if parse_comparative_question(q) is not None:
        return [ask_comparative(kb, q)]
    if q.lower().startswith("why ") and parse_comparative_question(q[4:]) is not None:
        return explain_comparative(kb, q[4:])              # the comparative `why`: chain / rungs / gap
    t = q.lower().split()
    if len(t) == 2 and t[0] == "guess":
        from ..possibility import guess, render_guess
        rec = guess(kb, ("is", t[1], None))
        if rec is None:
            return [f"nothing to guess about {t[1]} — no possibility is reachable"]
        return [render_guess(kb, rec)]
    from .query import ask_goal
    return ask_goal(kb, q, rules, policy=policy, **ask_kwargs)
