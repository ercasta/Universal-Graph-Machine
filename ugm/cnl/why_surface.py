"""Backward diagnosis — the `why S P O` surface (causation core, docs/design/form_inventory.md §9.2).

An agent that cannot ask "why does this hold?" cannot diagnose or recover — backward causal reasoning
is half of causation's agentic core. The REASONING already exists: a rule firing records provenance
(`proves`/`uses`, `provenance.py`), and `surface.explain` walks it into a derivation trace (the asked
fact, the rule that produced it, its premises recursed beneath — including the `causes` link an
entity-level causal rule used). What was missing is a QUESTION SURFACE on the unified `ingest` route.

This is a PURE recognizer (like `comparative.parse_comparative` / `uncertainty.load_line`), keyword-led
on `why`, so the canonical grammar — which has no `why` — REFUSES it and a grammar KB reaches it by
fall-through, a non-grammar KB directly. The forms are PREDICATE-FAITHFUL (the stored predicate is
written literally), which is what keeps them clear of the `has`/`have` inflection gap that a `does …
have …` auxiliary form would hit: that gap is orthogonal and deferred.

  why S P O        -> (S, P, O)      e.g. `why lion has aggression`  (P written as stored)
  why is S O       -> (S, is, O)     e.g. `why is ada thief`         (a property)
  why is S a|an O  -> (S, is_a, O)   e.g. `why is bo a suspect`      (a kind)
"""
from __future__ import annotations

Triple = tuple[str, str, str]


def parse_why(text: str) -> Triple | None:
    """Recognize a `why …` diagnosis request into the `(subj, pred, obj)` it asks about, else `None`.
    Keyword-led on `why`; predicate-faithful (no `does`/`have` normalization — see the module note)."""
    toks = text.replace("?", " ").lower().replace(" are ", " is ").split()
    if len(toks) < 4 or toks[0] != "why":            # need `why` + at least three content tokens
        return None
    rest = toks[1:]
    if rest[0] == "is":
        if len(rest) >= 4 and rest[2] in ("a", "an"):
            return (rest[1], "is_a", rest[3])          # why is S a O   -> a KIND
        if len(rest) >= 3:
            return (rest[1], "is", rest[2])            # why is S O     -> a PROPERTY
        return None
    if len(rest) >= 3:
        return (rest[0], rest[1], rest[2])             # why S P O      -> literal predicate
    return None
