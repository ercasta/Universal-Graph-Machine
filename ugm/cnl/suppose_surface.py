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
"""
from __future__ import annotations

from .forms import normalize_lexical

Triple = tuple[str, str, str]
_KEYWORDS = ("suppose ", "what if ")


def _clause(text: str) -> Triple | None:
    """One assertion-shaped clause -> `(subj, pred, obj)`, predicate-faithful (`have`->`has`)."""
    toks = normalize_lexical(text).replace("?", " ").lower().split()
    if len(toks) >= 4 and toks[1] == "is" and toks[2] in ("a", "an"):
        return (toks[0], "is_a", toks[3])                  # S is a O   -> a KIND
    if len(toks) >= 3 and toks[1] == "is":
        return (toks[0], "is", toks[2])                    # S is O     -> a PROPERTY
    if len(toks) >= 3:
        return (toks[0], toks[1], toks[2])                 # S P O      -> literal predicate
    return None


def parse_suppose(text: str) -> tuple[Triple, Triple] | None:
    """Recognize `suppose A : P` / `what if A : P` into `(assumption, prediction)` triples, else `None`.
    The `:` separates the entertained assumption from the queried consequence."""
    stripped = text.strip()
    low = stripped.lower()
    for kw in _KEYWORDS:
        if low.startswith(kw):
            body = stripped[len(kw):]
            if ":" not in body:
                return None                                # `suppose A` with no consequence to check
            a_text, p_text = body.split(":", 1)
            a, p = _clause(a_text), _clause(p_text)
            return (a, p) if (a and p) else None
    return None
