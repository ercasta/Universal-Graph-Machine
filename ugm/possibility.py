"""
Possibilistic layer — SLICE 1 (docs/possibilistic.md S7): banded forks + marker-mode read + θ-NAF.

Additive and OUT of the crisp hot path (chain.py untouched): a standalone MARKER-MODE reader that
sees ink at CERTAIN plus EVERY fork's pencil at its scope band, so a fact can be read `likely` /
`unlikely` WITHOUT taking a stance (the opposite of the binary in/out SUPPOSE scope read).

A FORK is a `<hypothesis>` scope carrying a `<likeliness>` band — that band is what distinguishes a
persisted possibilistic alternative from a transient SUPPOSE hypothesis (which has no band and is NOT
overlaid here). Likeliness lives on the scope, not on the edge primitive (S7.0, ratified 2026-07-15).

Later slices fold this into the ISA OVERLAY read op (`OVERLAY_BAND`) and add cross-fork environments
(combined assumption-sets, min band) + graded negation. This module is the SLICE-1 vertical.
"""
from __future__ import annotations

from .attrgraph import AttrGraph, graded
from .apply import SCOPE
from .suppose import HYPOTHESIS, _pencil

LIKELINESS = "<likeliness>"      # graded band on a fork's <hypothesis> scope node; absent ⇒ CERTAIN
CERTAIN = 1.0

# Provisional band → word scale (S7.7 is OPEN: reuse the degree-adverb lexicon very=0.8/somewhat=0.5/
# slightly=0.3, vs a dedicated 5-rung enum). Ordered high→low; interpreted ORDINALLY (decision F).
_BANDS = [(1.0, "certain"), (0.8, "very likely"), (0.5, "likely"),
          (0.3, "unlikely"), (0.0, "very unlikely")]


def band_word(b: float) -> str:
    for thr, word in _BANDS:
        if b >= thr:
            return word
    return "very unlikely"


def _entity(g: AttrGraph, name: str) -> str:
    """Reuse an existing same-named entity node or mint one (so a fork's `x` is the ink `x`)."""
    found = g.nodes_named(name)
    return min(found) if found else g.add_node(name)


def set_band(g: AttrGraph, scope: str, degree: float) -> None:
    g.set_attr(scope, LIKELINESS, graded(degree))


def band_of_scope(g: AttrGraph, scope: str) -> float:
    a = g.get_attr(scope, LIKELINESS)
    return float(a.value) if a is not None else CERTAIN


def add_fork(g: AttrGraph, degree: float, triples: list[tuple[str, str, str]]) -> str:
    """Author a possibilistic FORK: a `<hypothesis>` scope with band `degree`, holding `triples`
    (name triples) as CO-SCOPED pencil facts — a correlated alternative lives behind ONE fork
    (S1: joints via co-scoping). Returns the scope id. Mutual exclusion between two forks is the
    existing `disjoint_from` concern, not enforced here."""
    scope = g.add_node(HYPOTHESIS, control=True)
    set_band(g, scope, degree)
    for s, p, o in triples:
        _pencil(g, scope, _entity(g, s), p, _entity(g, o))
    return scope


def all_fork_bands(g: AttrGraph) -> dict[str, float]:
    """`rel_id -> band` for every pencil rel whose scope is a FORK (carries `<likeliness>`). Transient
    SUPPOSE scopes (no band) are excluded — they are not overlaid in marker mode. This is the
    marker-mode sibling of `chain._scope_pencils` (which returns ONE scope's set, binary)."""
    out: dict[str, float] = {}
    for r in g.nodes_with_key(SCOPE):
        a = g.get_attr(r, SCOPE)
        if a is None or not g.has(a.value):
            continue
        b = g.get_attr(a.value, LIKELINESS)
        if b is not None:
            out[r] = float(b.value)
    return out


def facts_matching_banded(g: AttrGraph, pred: str, s_name: str, o_name: str
                          ) -> list[tuple[str, str, float]]:
    """MARKER-MODE read: `(s, o, band)` for every `s pred o` visible as INK (band CERTAIN) or as ANY
    fork's pencil (band = the fork's scope band). All forks overlaid at once. Both endpoints bound
    (the yes/no query shape); wildcard endpoints are a later slice."""
    fork = all_fork_bands(g)
    out: list[tuple[str, str, float]] = []
    for s_id in g.nodes_named(s_name):
        for r in g.out(s_id):
            if g.is_inert(r) or not g.has_key(r, pred):
                continue
            if g.is_control(r):
                if r not in fork:            # control scaffolding that is not a fork pencil ⇒ not a fact
                    continue
                band = fork[r]
            else:
                band = CERTAIN               # ink
            if any(g.name(o_id) == o_name for o_id in g.out(r)):
                out.append((s_name, o_name, band))
    return out


def possibility(g: AttrGraph, pred: str, s: str, o: str) -> float:
    """The possibility of `s pred o`: the BEST (max) band over the derivations reaching it —
    qualitative max-of-min (here single-hop, so just max). 0.0 if unreachable."""
    return max((band for _, _, band in facts_matching_banded(g, pred, s, o)), default=0.0)


def naf_holds(g: AttrGraph, pred: str, s: str, o: str, theta: float) -> bool:
    """θ-crisp NAF: `not (s pred o)` HOLDS unless the positive is reachable at band ≥ `theta`.
    `theta` is the BIAS-vs-DECISIVENESS dial (S7.3): high θ ignores unlikely alternatives (decisive,
    bias-prone); low θ refuses to lean on an absence when the positive is even slightly possible."""
    return possibility(g, pred, s, o) < theta


def verdict(g: AttrGraph, pred: str, s: str, o: str, *, closed: bool = True) -> str:
    """The possibilistic verdict: `certain` (ink) / `very likely` … `very unlikely` (only gated
    derivations) / `assumed-no` (unreachable, closed) / `unknown` (unreachable, open). Subsumes the
    crisp four-verdict space — no forks present ⇒ `certain` or `assumed-no`, as today."""
    p = possibility(g, pred, s, o)
    if p <= 0.0:
        return "assumed-no" if closed else "unknown"
    return band_word(p)
