"""
The COMPOSITE surface — one text, every layer. The additive mini-surfaces (possibilistic
`uncertainty.py`, comparative `comparative.py`) each consume their own lines and hand the rest on;
this module is the line-by-line composition the playground and quickstarts use, so a world can mix
plain facts, rules, hedged facts, `either…or`, and comparisons in ONE block of CNL.

`load_world(text)` — partition by the mini-surfaces' PURE parsers (the hedge lexicon is pre-scanned
from the text's own `X means N` declarations, so a declared hedge routes correctly on the same
load), feed the remainder to the ordinary `load_corpus`, then author the special lines INTO the
returned KB.

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
from .comparative import (
    parse_comparative, add_comparison, parse_comparative_question, ask_comparative,
    explain_comparative,
)


def _is_special(line: str, hedges: dict[str, float]) -> bool:
    return (parse_hedge_decl(line) is not None or parse_either(line) is not None
            or parse_hedge_fact(line, hedges) is not None
            or parse_comparative(line) is not None)


def load_world(text: str, *, policy=None) -> tuple[AttrGraph, list[Rule]]:
    """Author `text` across every surface: `(kb, rules)` exactly like `load_corpus`, with the
    possibilistic and comparative lines routed to their own loaders (into the same KB)."""
    lines = text.splitlines()
    hedges = dict(HEDGE_BAND)
    for ln in lines:                                       # pre-scan: a hedge declared in this very
        d = parse_hedge_decl(ln)                           # text routes its uses correctly below
        if d is not None:
            hedges[d[0]] = d[1]
    plain, special = [], []
    for ln in lines:
        (special if ln.strip() and _is_special(ln, hedges) else plain).append(ln)
    kb, rules = load_corpus("\n".join(plain), policy=policy)
    for ln in special:
        if not _load_uncertain_line(kb, ln):
            parsed = parse_comparative(ln)
            if parsed is not None:
                add_comparison(kb, *parsed)
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
