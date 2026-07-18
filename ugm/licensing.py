"""
Licensing — deciding whether a PROPOSED rule is any good (learning arc §6, S6).

`ugm/learner.py` only proposes; nothing there judges. This module judges, by ELIMINATION: a
candidate that CONTRADICTS what is already observed is refuted, and the refutation carries its own
reason. No frequency is counted anywhere — that was settled when k>=2 licensing was measured
(`bench/spike_k2_intersection.py`): examples narrow the HYPOTHESIS SPACE, while provisionality
(`ugm/learned.py`) carries how much to trust what survives. Two orthogonal axes.

OVER-PREDICTION IS THE SIGNAL. A candidate is refuted when it derives something about a
FULLY-DESCRIBED entity that was not observed of it. The completeness qualifier is load-bearing and
is the design finding of this slice: deriving a NEW fact about a novel entity is the whole point of
a rule (`robin flies`), while deriving a new fact about an entity we already know everything about
is a false prediction. Without saying which entities are complete, the two are indistinguishable
and elimination cannot run — the same shape as the bootstrapping paradox in §6.2b, where refutation
needed declared constraints a sparse KB does not have.

WHAT THIS DOES NOT DO. It does not rank, score, or promote. A surviving candidate is merely
unrefuted, which for an under-determined dataset can still be several mutually-inconsistent rules —
measured: contrast between one failed and one succeeded step cuts 12 candidates to 8, and the
remainder are genuinely undecidable on that evidence. Closing that gap is the DISCRIMINATING
QUESTION (`bench/spike_discriminating_question.py`), not more filtering.
"""
from __future__ import annotations

from .attrgraph import AttrGraph
from .lowering import derived_triples, run_bank
from .production_rule import Rule

Triple = tuple[str, str, str]

# Marker relation naming an entity whose description is COMPLETE — everything true of it is already
# recorded, so anything further derived about it is a false prediction.
COMPLETE = "fully_described"


def complete_entities(graph: AttrGraph) -> set[str]:
    """Entity names marked `fully_described` in the graph."""
    out: set[str] = set()
    for nid in graph.nodes():
        for rel, _obj in graph.relations_from(nid):
            if graph.predicate(rel) == COMPLETE:
                name = graph.name(nid)
                if name:
                    out.add(name)
    return out


def mark_complete(graph: AttrGraph, *entity_names: str) -> None:
    """Declare that everything true of these entities is already recorded."""
    marker = _intern(graph, "<complete>")
    for name in entity_names:
        for nid in graph.nodes_named(name):
            if not any(graph.predicate(r) == COMPLETE
                       for r, _o in graph.relations_from(nid)):
                graph.add_relation(nid, COMPLETE, marker, control=True)


def _intern(graph: AttrGraph, name: str) -> str:
    existing = [n for n in graph.nodes_named(name) if graph.is_control(n)]
    return existing[0] if existing else graph.add_node(name, control=True)


def _replay(facts: set[Triple]) -> AttrGraph:
    """A fresh graph holding exactly `facts` — so testing a candidate never mutates the KB.

    Entity nodes are interned by name (`add_node` always mints, so a shared object must be reused
    explicitly or a literal pattern would match only one of the duplicates)."""
    g = AttrGraph()
    nodes: dict[str, str] = {}

    def node(name: str) -> str:
        if name not in nodes:
            nodes[name] = g.add_node(name)
        return nodes[name]

    for s, p, o in facts:
        g.add_relation(node(s), p, node(o))
    return g


def overpredictions(rule: Rule, facts: set[Triple], complete: set[str],
                    *, max_rounds: int = 20) -> list[Triple]:
    """Facts `rule` derives about a FULLY-DESCRIBED entity that were not observed of it.

    Empty means the candidate is consistent with what we know. Non-empty IS the refutation, and
    each triple is a printable reason: "it predicts `microwave discrepancy hot_coffee`, and we know
    everything about microwave"."""
    if not complete:
        return []
    g = _replay(facts)
    before = set(derived_triples(g))
    try:
        run_bank(g, [rule], max_rounds=max_rounds)
    except Exception:
        return []                      # an unrunnable candidate is not evidence of falsehood
    new = set(derived_triples(g)) - before
    return sorted(t for t in new if t[0] in complete)


def refute(candidates: list[Rule], graph: AttrGraph, *,
           complete: set[str] | None = None) -> tuple[list[Rule], list[tuple[Rule, list[Triple]]]]:
    """Split `candidates` into (survivors, [(refuted_rule, why)]) against the observations.

    `complete` defaults to the entities marked `fully_described` in the graph. With no complete
    entities NOTHING can be refuted — that is the honest outcome, not a silent pass: absence of a
    discriminator is exactly the §6.2b bootstrapping paradox, and the caller should ask a
    discriminating question rather than believe every candidate."""
    facts = set(derived_triples(graph))
    known = complete_entities(graph) if complete is None else complete
    survivors: list[Rule] = []
    refuted: list[tuple[Rule, list[Triple]]] = []
    for rule in candidates:
        why = overpredictions(rule, facts, known)
        if why:
            refuted.append((rule, why))
        else:
            survivors.append(rule)
    return survivors, refuted


def render_refutation(rule: Rule, why: list[Triple]) -> str:
    """One line saying what the candidate got wrong, in the author's own vocabulary."""
    head = " and ".join(f"{s} {p} {o}" for s, p, o in (x.tokens() for x in rule.rhs))
    body = " and ".join(f"{s} {p} {o}" for s, p, o in (x.tokens() for x in rule.lhs))
    preds = ", ".join(f"{s} {p} {o}" for s, p, o in why)
    return (f"refuted `{head} when {body}` — it predicts {preds}, "
            "about entities we already know everything about")
