"""Propositional causation — the `that P causes that Q` PARSER (form_inventory §9.3 / causation C3).

Entity-level causation (`hunger causes aggression`, C1) is native: `causes` is an ordinary relation and
a propagation rule derives the effect. What this surface adds is PROPOSITIONAL causation — a causal link
between whole PROPOSITIONS ("that the door is open causes that the cat flees"), so P holding DERIVES Q and
links CHAIN. This module is now PURELY the PARSER: `parse_cause` folds the two clauses to `(antecedent,
consequent)` triples; intake hands them to `ugm/scope_crossing.mint_causal_link`, which mints two
proposition SCOPES related by a base `causes` fact (the SCOPE REFRAME, scope_reframe_audit.md Step 2). The
crossing itself — reify + causal MP over the `@?h` scope-tree read, then promote — runs at the committed-ask
gate (`cnl/query.resolve_crossings`). The old content-keyed `prop:` HANDLE + three bridge rules are RETIRED
(row 6): a handle was a stringly re-implementation of interning with orphan participant refs.

The `that` NOMINALIZER is what distinguishes this from entity-level `X causes Y` (which the fact route
handles) — `that door1 is open causes that cat flees` unambiguously marks two propositions, so this
surface never mis-claims a bare `A causes B`.

Pure keyword/structure recognizer (like `suppose_surface`/`why_surface`), so the canonical grammar
refuses it and a grammar KB reaches it by fall-through. Each clause is assertion-shaped and
predicate-faithful (the `have`->`has` fold), reusing the same clause shapes as `suppose_surface`:

  that A causes that B     A, B each one of:  S P O  |  S is O  |  S is a|an O
"""
from __future__ import annotations

from ..vocabulary import neg_pred
from .forms import normalize_lexical
from .suppose_surface import _strip_hedge

Triple = tuple[str, str, str]
_SEP = " causes that "
_LEAD = "that "
_NEGATORS = ("no", "not")


def _clause(text: str, hedges: dict[str, float] | None = None) -> Triple | None:
    """One assertion-shaped clause -> `(subj, pred, obj)`, predicate-faithful (`have`->`has`, `is a`->
    `is_a`). Shape menu shared with `suppose_surface`.

    CAUSATION ∘ {NEGATION, DEGREE} composition (2026-07-23, docs/design/composition_architecture.md
    §GAPS). A clause may NEGATE (`that lion has no mane causes …`) or HEDGE (`that lion generally is
    hungry causes …`); both were mis-read by the bare S-P-O menu (the negator became the object, the
    hedge became the predicate), so the HANDLE never matched the proposition the reification bridge
    needs it to. Now: a negator between predicate and object flips the predicate to `neg_pred` (so the
    handle carries `has_not`, matching `the lion has no mane`), and a hedge word is stripped (the band
    rides the fork the fact route pens, not the crisp handle — the banded reader composes it). Same
    producer-fix shape as the hedge/negation surfaces one layer along."""
    toks = normalize_lexical(text).replace("?", " ").lower().split()
    if hedges:
        _band, toks = _strip_hedge(toks, hedges)           # DEGREE: the band lives on the fork, not here
    # NEGATION: `S V no|not O` -> the negative predicate (`has no mane` -> `has_not mane`), faithful to
    # the fact route's `neg_pred` representation so the reify bridge's `?s ?p ?o` premise matches.
    if len(toks) >= 4 and toks[2] in _NEGATORS:
        return (toks[0], neg_pred(toks[1]), toks[3])
    if len(toks) >= 4 and toks[1] == "is" and toks[2] in ("a", "an"):
        return (toks[0], "is_a", toks[3])                  # S is a O   -> a KIND
    if len(toks) >= 3 and toks[1] == "is":
        return (toks[0], "is", toks[2])                    # S is O     -> a PROPERTY
    if len(toks) >= 3:
        return (toks[0], toks[1], toks[2])                 # S P O      -> literal predicate
    if len(toks) == 2:
        return (toks[0], toks[1], "yes")                   # S P (intransitive) -> `S P yes`
    return None


def parse_cause(text: str, hedges: dict[str, float] | None = None
                ) -> tuple[Triple, Triple] | None:
    """Recognize `that A causes that B` into `(antecedent, consequent)` triples, else `None`. The `that`
    nominalizer + the ` causes that ` separator mark the two propositions; a bare `A causes B` (no
    `that`) is NOT this surface — it is entity-level causation, left to the fact route. `hedges` (the
    active lexicon) lets a clause carry a hedge adverb — stripped so the handle matches the banded fork."""
    low = text.strip().lower()
    if not low.startswith(_LEAD) or _SEP not in low:
        return None
    stripped = text.strip()
    head = stripped[len(_LEAD):]                           # drop the leading `that`
    idx = head.lower().find(_SEP)
    if idx < 0:
        return None
    a_text, b_text = head[:idx], head[idx + len(_SEP):]
    a, b = _clause(a_text, hedges), _clause(b_text, hedges)
    return (a, b) if (a and b) else None
