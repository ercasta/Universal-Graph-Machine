"""
Surface — narration and explanation as thin readers over the graph + journal.

There are no bespoke narrator/explainer subsystems (vision §3, §9):
  - Narration of a step is just rendering the canonical CNL nodes the firing
    asserted (a render-for-display tool at the output boundary).
  - Explanation is reading the append-only firing journal back: "why does X hold"
    = the firing that created X, recursively over the firing's preconditions.

Because the graph IS CNL, both render faithfully from node names — no lossy
re-rendering of logic into English.
"""
from __future__ import annotations

from .. import provenance as prov
from ..production_rule import Firing
from ..world_model import Graph


def _subject_of(graph: Graph, rel_id: str) -> str | None:
    """The subject of a relation node, skipping provenance in-edges (`proves`/`uses`
    point INTO a fact relation, so a naive `into` would pick one of them)."""
    for n in graph.into(rel_id):
        if graph.name(n) not in prov.PROVENANCE_PREDS:
            return n
    return None


# ---------------------------------------------------------------------------
# Rendering (the narrator's only remaining job)
# ---------------------------------------------------------------------------

def render_relation(graph: Graph, rel_id: str) -> str | None:
    """Render a relation node  subject --> [rel] --> object  as 'subject rel object'."""
    subj = _subject_of(graph, rel_id)
    obj = next(iter(graph.out(rel_id)), None)
    if subj is None or obj is None:
        return None
    return f"{graph.name(subj)} {graph.name(rel_id)} {graph.name(obj)}"


def narrate(graph: Graph, journal: list[Firing]) -> list[str]:
    """One line per asserted relation, in firing order: 'subj rel obj   [rule]'."""
    lines: list[str] = []
    for f in journal:
        for nid in f.created:
            rel = render_relation(graph, nid)
            if rel is not None:
                lines.append(f"{rel}   [{f.rule_key}]")
    return lines


# ---------------------------------------------------------------------------
# Explanation — traversing the in-graph support (proves / uses), not a journal
# ---------------------------------------------------------------------------
#
# A derivation trace is now a graph traversal of the justification structure
# (provenance.py): the J that PROVES a fact names the rule; the premises it USES are
# the indented sub-derivations. Leaves are facts with no rule-J — '(given)' (asserted /
# tokenized / axiom). The `journal` and `rules` parameters are accepted for backward
# compatibility but no longer read: provenance lives in the substrate (vision §9).

def _find_rel(graph: Graph, s_id: str, pname: str, o_id: str) -> str | None:
    for r in graph.out(s_id):
        if graph.name(r) == pname and o_id in graph.out(r):
            return r
    return None


def _explain_rel(graph: Graph, rel: str, depth: int, seen: set[str]) -> list[str]:
    parts = render_relation(graph, rel)
    pad = "  " * depth
    if parts is None:
        return [f"{pad}(unreadable)"]
    head = f"{pad}{parts}"
    j = prov.rule_support_j(graph, rel)
    if j is None:
        return [f"{head}  (given)"]
    lines = [f"{head}  <- {prov.rule_of_j(graph, j)}"]
    if rel in seen:
        return lines
    seen.add(rel)
    for pre in prov.premises_of(graph, j):
        lines += _explain_rel(graph, pre, depth + 1, seen)
    return lines


def explain(
    graph: Graph,
    journal: list[Firing] | None,
    rules: list | None,
    s_name: str,
    pname: str,
    o_name: str,
    *,
    depth: int = 0,
    _seen: set[str] | None = None,
) -> list[str]:
    """A derivation trace for `s_name pname o_name`, read from the in-graph support.

    Each line is the fact and the rule that produced it; preconditions are indented
    beneath. Leaves are '(given)' (asserted / tokenized) or '(not present)'.
    """
    seen = set() if _seen is None else _seen
    pad = "  " * depth
    rel = None
    for si in graph.nodes_named(s_name):
        for oi in graph.nodes_named(o_name):
            r = _find_rel(graph, si, pname, oi)
            if r is not None:
                rel = r
                break
        if rel is not None:
            break
    if rel is None:
        return [f"{pad}{s_name} {pname} {o_name}  (not present)"]
    return _explain_rel(graph, rel, depth, seen)
