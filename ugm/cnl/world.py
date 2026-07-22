"""
The COMPOSITE surface — one text, every layer. A world mixes plain facts, rules, hedged facts,
`either…or`, and comparisons in ONE block of CNL.

`load_world(text)` — FULLY CONVERGED 2026-07-22 (meaning_surfaces_audit.md §3): now a thin alias for
`load_corpus`. Every layer — facts, rules, hedged facts, `either…or`, comparisons — routes through the
ONE ingest path (`intake.route`): comparison + hedge each have an intake route, and `load_corpus` is
ingest-in-a-loop. A hedge fork now SURVIVES interleaved fact ingestion (the scope-GC fix,
`scope-nodes-survive-incidental-gc`), so hedges no longer need authoring-last. NOTE: the hedge lexicon
is DECLARE-BEFORE-USE (`P means N` must precede its uses), the intake contract — the old whole-text
pre-scan (order-independent) is gone; corpora in use already declare-before-use.

`ask_world(kb, rules, question)` — routes a question to its surface: a comparative shape to
`ask_comparative`; `guess X` to the defeasible-guess act (rendered as its honest `why` line);
everything else to `ask_goal` (which, under a banded policy, answers with the band words).
"""
from __future__ import annotations

from ..attrgraph import AttrGraph
from ..production_rule import Rule
from .authoring import load_corpus
from .comparative import parse_comparative_question, ask_comparative, explain_comparative


def load_world(text: str, *, policy=None) -> tuple[AttrGraph, list[Rule]]:
    """Author `text` across every surface: `(kb, rules)`. A thin alias for `load_corpus`, since intake
    routes comparison + hedge and `load_corpus` is the one ingest path (loader convergence)."""
    return load_corpus(text, policy=policy)


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
