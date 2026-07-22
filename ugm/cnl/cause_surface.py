"""Propositional causation — the `that P causes that Q` surface (facts-as-truth-bearers, form_inventory
§9.3 / causation C3).

Entity-level causation (`hunger causes aggression`, C1) is native: `causes` is an ordinary relation and
a propagation rule derives the effect. What this surface adds is PROPOSITIONAL causation — a causal link
between whole PROPOSITIONS ("that the door is open causes that the cat flees"), so P holding DERIVES Q,
the link itself is a first-class fact, and links CHAIN. It rides the reification bridge the
predicate-variable-matching primitive enables (`bench/spike_facts_as_truth_bearers.py`): each proposition
becomes a content-keyed HANDLE carrying `subj`/`pred`/`obj`, joined by an ordinary `causes` edge, and
three declared bridge rules (reify / MP / dereify) carry truth across the link. Domain logic stays in
banks; causation is not privileged.

The `that` NOMINALIZER is what distinguishes this from entity-level `X causes Y` (which the fact route
handles) — `that door1 is open causes that cat flees` unambiguously marks two propositions, so this
surface never mis-claims a bare `A causes B`.

Pure keyword/structure recognizer (like `suppose_surface`/`why_surface`), so the canonical grammar
refuses it and a grammar KB reaches it by fall-through. Each clause is assertion-shaped and
predicate-faithful (the `have`->`has` fold), reusing the same clause shapes as `suppose_surface`:

  that A causes that B     A, B each one of:  S P O  |  S is O  |  S is a|an O
"""
from __future__ import annotations

from .forms import normalize_lexical

Triple = tuple[str, str, str]
_SEP = " causes that "
_LEAD = "that "


def _clause(text: str) -> Triple | None:
    """One assertion-shaped clause -> `(subj, pred, obj)`, predicate-faithful (`have`->`has`, `is a`->
    `is_a`). Identical shape menu to `suppose_surface._clause`."""
    toks = normalize_lexical(text).replace("?", " ").lower().split()
    if len(toks) >= 4 and toks[1] == "is" and toks[2] in ("a", "an"):
        return (toks[0], "is_a", toks[3])                  # S is a O   -> a KIND
    if len(toks) >= 3 and toks[1] == "is":
        return (toks[0], "is", toks[2])                    # S is O     -> a PROPERTY
    if len(toks) >= 3:
        return (toks[0], toks[1], toks[2])                 # S P O      -> literal predicate
    if len(toks) == 2:
        return (toks[0], toks[1], "yes")                   # S P (intransitive) -> `S P yes`
    return None


def parse_cause(text: str) -> tuple[Triple, Triple] | None:
    """Recognize `that A causes that B` into `(antecedent, consequent)` triples, else `None`. The `that`
    nominalizer + the ` causes that ` separator mark the two propositions; a bare `A causes B` (no
    `that`) is NOT this surface — it is entity-level causation, left to the fact route."""
    low = text.strip().lower()
    if not low.startswith(_LEAD) or _SEP not in low:
        return None
    stripped = text.strip()
    head = stripped[len(_LEAD):]                           # drop the leading `that`
    idx = head.lower().find(_SEP)
    if idx < 0:
        return None
    a_text, b_text = head[:idx], head[idx + len(_SEP):]
    a, b = _clause(a_text), _clause(b_text)
    return (a, b) if (a and b) else None


def handle_name(triple: Triple) -> str:
    """The content-keyed HANDLE name for a proposition — deterministic, so re-stating a link reuses the
    same handle (idempotent) and links about the same proposition share it (coherent `causes` graph). A
    plain name (no `<…>`), so its `subj`/`pred`/`obj`/`truth`/`causes` facts are ordinary facts the
    bridge rules read."""
    return "prop:" + ":".join(triple)


# The three declared bridge rules (facts-as-truth-bearers): reify a handle from its proposition holding,
# carry truth across a `causes` link (propositional modus ponens, pure S-P-O), dereify a true handle back
# to its edge. Installed ONCE per session (keyed by rule.key), then shared by every propositional link.
BRIDGE_RULES: tuple[str, ...] = (
    "?h truth yes when ?h subj ?s and ?h pred ?p and ?h obj ?o and ?s ?p ?o",
    "?b truth yes when ?a truth yes and ?a causes ?b",
    "?s ?p ?o when ?h subj ?s and ?h pred ?p and ?h obj ?o and ?h truth yes",
)


def handle_facts(a: Triple, b: Triple) -> list[Triple]:
    """The fact triples a `that A causes that B` statement emits: each proposition's handle carrying its
    subj/pred/obj, plus the propositional `causes` edge between the two handles."""
    ha, hb = handle_name(a), handle_name(b)
    return [(ha, "subj", a[0]), (ha, "pred", a[1]), (ha, "obj", a[2]),
            (hb, "subj", b[0]), (hb, "pred", b[1]), (hb, "obj", b[2]),
            (ha, "causes", hb)]
