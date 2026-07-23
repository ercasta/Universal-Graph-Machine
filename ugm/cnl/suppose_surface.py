"""Counterfactual — the `suppose A : P` / `what if A : P` surface (causation core §9.2, third direction).

An agent plans and diagnoses by asking "what if?" — entertain a state that is not (yet) the case and
read off a consequence. The REASONING is native: `suppose.suppose(commit=False)` pens the assumption in
a `<hypothesis>` scope, chains in pencil, checks the prediction in-scope, and inks NOTHING. This is the
ADDITIVE counterfactual ("if A *were* so, would P hold?"). The SUBTRACTIVE one ("if A were *not* so,
would P still hold?") needs non-monotone retraction-under-hypothesis — the theorem-prover completion,
out of the agentic core (§9.2).

Pure keyword-led recognizer (like `why_surface`/`comparative`), so the canonical grammar refuses it and
a grammar KB reaches it by fall-through. Each clause is an assertion-shaped triple, PREDICATE-FAITHFUL
with the `have`->`has` fold (`normalize_lexical`), so `suppose lion has hunger : lion has aggression`
reads the same predicate the KB stores.

  suppose A : P     A, P each one of:  S P O   |   S is O   |   S is a|an O
  what if A : P

DEGREE ∘ SCOPE(suppose) composition (2026-07-23, docs/design/composition_architecture.md §GAPS). A
clause may carry a HEDGE adverb (`suppose lion generally is hungry : …`) — the same producer gap the
`degree ∘ negation` fix closed one layer along: without stripping it, `generally` was read as the
PREDICATE (`lion generally is`, a garbage triple) and the hedge dropped silently. `_clause` now strips
a recognized hedge word and returns the BAND it denotes, so the suppose route can entertain the
assumption AT ITS DEGREE (a fork the banded reader composes for free). `parse_suppose` keeps its
band-free triple-pair contract (the router recognizer + the shipped tests); `parse_suppose_banded` is
the hedge-aware sibling the intake suppose route uses.
"""
from __future__ import annotations

from .forms import normalize_lexical

Triple = tuple[str, str, str]
_KEYWORDS = ("suppose ", "what if ")


def _strip_hedge(toks: list[str], hedges: dict[str, float]) -> tuple[float | None, list[str]]:
    """Remove ONE recognized hedge word from `toks`, returning `(band, remaining)`. A two-word hedge
    (`very likely`) wins over a one-word prefix, matching `uncertainty.parse_hedge_fact`. `band` is
    None (and `toks` unchanged) when no hedge is present."""
    for i in range(len(toks) - 1):
        two = f"{toks[i]} {toks[i + 1]}"
        if two in hedges:
            return hedges[two], toks[:i] + toks[i + 2:]
    for i, w in enumerate(toks):
        if w in hedges:
            return hedges[w], toks[:i] + toks[i + 1:]
    return None, toks


def _triple(toks: list[str]) -> Triple | None:
    """The assertion-shaped triple of an already-hedge-stripped, normalized token list."""
    if len(toks) >= 4 and toks[1] == "is" and toks[2] in ("a", "an"):
        return (toks[0], "is_a", toks[3])                  # S is a O   -> a KIND
    if len(toks) >= 3 and toks[1] == "is":
        return (toks[0], "is", toks[2])                    # S is O     -> a PROPERTY
    if len(toks) >= 3:
        return (toks[0], toks[1], toks[2])                 # S P O      -> literal predicate
    return None


def _clause(text: str, hedges: dict[str, float] | None = None) -> tuple[Triple | None, float | None]:
    """One assertion-shaped clause -> `(triple, band)`, predicate-faithful (`have`->`has`). A hedge
    adverb (when `hedges` is supplied) is stripped and its band returned; `band` is None otherwise."""
    toks = normalize_lexical(text).replace("?", " ").lower().split()
    band = None
    if hedges:
        band, toks = _strip_hedge(toks, hedges)
    return _triple(toks), band


def parse_suppose_banded(text: str, hedges: dict[str, float] | None = None
                         ) -> tuple[tuple[Triple, float | None], tuple[Triple, float | None]] | None:
    """Recognize `suppose A : P` / `what if A : P` into `((assumption, a_band), (prediction, p_band))`,
    else `None`. Each `*_band` is the degree of a hedge adverb in that clause (None when crisp). The
    `:` separates the entertained assumption from the queried consequence."""
    stripped = text.strip()
    low = stripped.lower()
    for kw in _KEYWORDS:
        if low.startswith(kw):
            body = stripped[len(kw):]
            if ":" not in body:
                return None                                # `suppose A` with no consequence to check
            a_text, p_text = body.split(":", 1)
            (a, ab), (p, pb) = _clause(a_text, hedges), _clause(p_text, hedges)
            return ((a, ab), (p, pb)) if (a and p) else None
    return None


def parse_suppose(text: str) -> tuple[Triple, Triple] | None:
    """Recognize `suppose A : P` / `what if A : P` into `(assumption, prediction)` triples, else `None`.
    The band-free contract kept for the router recognizer and the shipped tests; the hedge-aware
    `parse_suppose_banded` is what the intake suppose route uses to reason at a degree."""
    r = parse_suppose_banded(text, None)
    if r is None:
        return None
    (a, _ab), (p, _pb) = r
    return (a, p)
