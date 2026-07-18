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
from ..chain import ById
from ..production_rule import Firing
from ..world_model import Graph


def _subject_of(graph: Graph, rel_id: str) -> str | None:
    """The subject of a relation node, skipping provenance in-edges (`proves`/`uses`
    point INTO a fact relation, so a naive `into` would pick one of them)."""
    for n in graph.into(rel_id):
        if graph.predicate(n) not in prov.PROVENANCE_PREDS:
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
    return f"{graph.name(subj)} {graph.predicate(rel_id)} {graph.name(obj)}"


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
        if graph.has_key(r, pname) and o_id in graph.out(r):
            return r
    return None


def _band_suffix(graph: Graph, rel: str) -> str:
    """The possibilistic band a FORK fact carries, rendered as ` (likely)` etc — "" for ink and for
    transient SUPPOSE pencils (no band). The proof tree shows each fact's OWN confidence (the
    band+env half of a banded `why`, docs/possibilistic.md S7.5 step 6)."""
    from ..apply import SCOPE
    from ..possibility import LIKELINESS, band_word
    a = graph.get_attr(rel, SCOPE)
    if a is None or not graph.has(a.value):
        return ""
    b = graph.get_attr(a.value, LIKELINESS)
    if b is None or float(b.value) >= 1.0:
        return ""
    return f" ({band_word(float(b.value))})"


def _env_lines(graph: Graph, rel: str, depth: int) -> list[str]:
    """The WORLDS a derived fork stands on — the ENV half of a banded `why` (docs/possibilistic.md
    S7.5 step 6; the band half is `_band_suffix`). One line per assumption-world in the fork's stored
    ATMS environment, rendering the world's own CO-SCOPED pencil facts — so a conclusion reached
    through `intruder is either tall and quiet or …` shows it stands on the WHOLE tall∧quiet world,
    a correlation the premise lines alone don't reveal. Empty for ink, base forks, and crisp runs."""
    from ..apply import SCOPE
    from ..possibility import DERIVED_ENV, band_of_scope, band_word
    from ..suppose import scope_members
    a = graph.get_attr(rel, SCOPE)
    if a is None or not graph.has(a.value):
        return []
    env = graph.get_attr(a.value, DERIVED_ENV)
    if env is None or not env.value:
        return []
    lines: list[str] = []
    for w in sorted(env.value):
        if not graph.has(w):
            continue
        facts = sorted(f for f in (render_relation(graph, m) for m in scope_members(graph, w)) if f)
        if facts:
            lines.append(f"{'  ' * depth}standing on the {band_word(band_of_scope(graph, w))} "
                         f"world where: {'; '.join(facts)}")
    return lines


def _explain_rel(graph: Graph, rel: str, depth: int, seen: set[str]) -> list[str]:
    parts = render_relation(graph, rel)
    pad = "  " * depth
    if parts is None:
        return [f"{pad}(unreadable)"]
    head = f"{pad}{parts}{_band_suffix(graph, rel)}"
    j = prov.rule_support_j(graph, rel)
    if j is None:
        return [f"{head}  (given)"]
    lines = [f"{head}  <- {prov.rule_of_j(graph, j)}"]
    lines += _env_lines(graph, rel, depth + 1)         # the worlds this conclusion stands on (banded)
    if rel in seen:
        return lines
    seen.add(rel)
    for pre in prov.premises_of(graph, j):
        lines += _explain_rel(graph, pre, depth + 1, seen)
    for group in prov.assumption_groups(graph, j):         # what the firing LEANED ON (decision 6)
        from ..possibility import band_word
        pi = max((p for *_r, p in group), default=0.0)
        how = ("no evidence for it was found" if pi <= 0.0
               else f"the counter-evidence is only {band_word(pi)}")
        # A CONJUNCTIVE NAC (feedback #16) was assumed absent JOINTLY — no single atom is claimed
        # absent, and saying so could be flatly false (`l1 has anything` when l1 demonstrably does).
        clause = " and ".join(f"{ns} {np} {no}" for np, ns, no, _pi in group)
        joint = "  (together)" if len(group) > 1 else ""
        lines.append(f"{'  ' * (depth + 1)}assumed not: {clause}{joint}  ({how})")
        # The negative's DECOMPOSITION (the linked subgoal chain, recorded under provenance): what
        # deciding this absence actually searched — absent (a run without the chain) it adds nothing.
        for np, ns, no, _pi in group:
            lines += _searched_lines(graph, np, ns, no, depth + 2)
    return lines


def _searched_lines(graph: Graph, pred: str, subj: str | None, obj: str | None,
                    depth: int, _seen: set | None = None) -> list[str]:
    """The 'looked for' lines under an `assumed not:` — a cycle-guarded walk of the linked subgoal
    chain (`chain.subgoal_decomposition`): each sub-demand deciding the absence raised, indented,
    recursively.

    DOMAIN GRAIN (the same cut `on_subgoal`'s frame grain makes): the walk renders only FULLY-BOUND,
    non-`same_as` children — the coref congruence's probes and the machinery rules' wildcard seeds
    are real searches (and stay matchable in the graph chain), but they narrate the machinery, not
    the case. A skipped child is not descended into (its own domain-grain searches surface via their
    direct domain parents, which the chain also links)."""
    from ..chain import subgoal_decomposition
    from ..vocabulary import SAME_AS
    seen = set() if _seen is None else _seen
    if (pred, subj, obj) in seen:
        return []
    seen.add((pred, subj, obj))
    lines: list[str] = []
    for p, s, o in subgoal_decomposition(graph, pred, subj, obj):
        if p == SAME_AS or s is None or o is None:         # machinery grain — recorded, not narrated
            continue
        lines.append(f"{'  ' * depth}looked for: {s} {p} {o}")
        lines += _searched_lines(graph, p, s, o, depth + 1, seen)
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

    ID-ADDRESSED ENDPOINTS (feedback #15). Either endpoint may be a `ById` instead of a name, which
    PINS it to exactly that node rather than iterating the same-named candidate set. This is what makes
    a rule-MINTED node explainable: a skolem head (`c?`) mints one node per firing, all carrying the
    head's literal name, so `nodes_named('c')` is a set of genuinely-distinct nodes and a name can only
    ever reach the first one that happens to carry the relation. The substrate is LABEL-LESS by design —
    a name is a label, never an identity — so the fix is to address the node, not to fabricate
    distinguishing names for it.
    """
    seen = set() if _seen is None else _seen
    pad = "  " * depth
    s_cands = [s_name.node_id] if isinstance(s_name, ById) else graph.nodes_named(s_name)
    o_cands = [o_name.node_id] if isinstance(o_name, ById) else graph.nodes_named(o_name)
    s_name = graph.name(s_name.node_id) if isinstance(s_name, ById) else s_name
    o_name = graph.name(o_name.node_id) if isinstance(o_name, ById) else o_name
    rel = None
    for si in s_cands:
        for oi in o_cands:
            r = _find_rel(graph, si, pname, oi)
            if r is not None:
                rel = r
                break
        if rel is not None:
            break
    if rel is None:
        return [f"{pad}{s_name} {pname} {o_name}  (not present)"]
    return _explain_rel(graph, rel, depth, seen)
