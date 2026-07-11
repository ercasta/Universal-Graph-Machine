"""
Provenance in the substrate — justifications are NODES, not a Python journal
(docs/coreference_design.md §4, vision §2/§9).

Every rule firing `P1..Pn => C1..Cm` materializes a **justification node** `J` wired
into the graph:

    J --proves--> Ci      (one per fact the firing created)
    J --uses--> Pj        (one per premise relation it matched)

`J` is named `<j:RULEKEY>` (a keyword node, so `canonicalize` never merges two firings
of the same rule, and the rule that fired is recoverable by name). An ASSERTED fact may
additionally get `<axiom> --proves--> fact`, so "is this still supported?" is a single
EXISTENTIAL question ("some live J proves it") with no counting.

The payoff (design §4): retraction becomes graph traversal (the support graph is
matchable), explanation becomes traversal of `proves`/`uses` (no lossy re-render), and it
is homoiconic. Affordable because evaluation is on-demand (firings are bounded by what a
query needs — see `demand.py`).

`proves`/`uses` are DISTINCT predicate names, inert to every domain rule, and the matcher
locality (`Graph.within`) skips them — so provenance never perturbs reasoning.
"""
from __future__ import annotations

from .world_model import Graph

# The provenance vocabulary (all ordinary nodes; the names are the only convention).
PROVES = "proves"
USES = "uses"
AXIOM = "<axiom>"
_J_PREFIX = "<j:"

# Predicate names the matcher/locality treats as inert (kept in sync with world_model).
PROVENANCE_PREDS: frozenset[str] = frozenset({PROVES, USES})


# ---------------------------------------------------------------------------
# Justification node naming
# ---------------------------------------------------------------------------

def j_name(rule_key: str) -> str:
    """The name of the justification node for a firing of `rule_key` (canonicalize-proof:
    it starts with '<', so the merge tool skips it; the key is recoverable)."""
    return f"{_J_PREFIX}{rule_key}>"


def is_justification(name: str) -> bool:
    return name.startswith(_J_PREFIX)


def rule_of_j(graph: Graph, j: str) -> str:
    """The rule key a justification node records (or '<axiom>')."""
    nm = graph.name(j)
    return nm[len(_J_PREFIX):-1] if is_justification(nm) else nm


# ---------------------------------------------------------------------------
# Readers over the support graph
# ---------------------------------------------------------------------------

def support_js(graph: Graph, rel: str) -> list[str]:
    """Every justification node (rule-J or `<axiom>`) that PROVES relation `rel`.

    A proof is the path  J --[proves node]--> rel ; this walks `rel`'s incoming
    `proves` relation nodes back to their J subjects.
    """
    js: list[str] = []
    for pn in graph.into(rel):
        if graph.has_key(pn, PROVES):
            js.extend(graph.into(pn))
    return js


def rule_support_j(graph: Graph, rel: str) -> str | None:
    """The first RULE justification (a `<j:...>`, not an axiom) proving `rel`, else None.
    Used by explanation: an axiom-only / unproven fact is a leaf ('(given)')."""
    for j in support_js(graph, rel):
        if is_justification(graph.name(j)):
            return j
    return None


def _objects_via(graph: Graph, subj: str, pred: str) -> list[str]:
    """Objects reached as  subj --[pred node]--> obj, walking raw edges (NOT
    `relations_from`, which deliberately hides provenance — this READS provenance)."""
    out: list[str] = []
    for rn in graph.out(subj):
        if graph.has_key(rn, pred):
            out.extend(graph.out(rn))
    return out


def premises_of(graph: Graph, j: str) -> list[str]:
    """The premise relation nodes a justification `uses`."""
    return _objects_via(graph, j, USES)


def proven_of(graph: Graph, j: str) -> list[str]:
    """The fact relation nodes a justification `proves`."""
    return _objects_via(graph, j, PROVES)


def justifications_using(graph: Graph, node: str) -> list[str]:
    """Every justification node that `uses` `node` as a premise."""
    js: list[str] = []
    for un in graph.into(node):
        if graph.has_key(un, USES):
            js.extend(graph.into(un))
    return js


def derived_facts(graph: Graph) -> set[str]:
    """Every fact relation that has at least one justification proving it (i.e. was
    DERIVED, or axiomatized). Asserted base facts with no proof are NOT included — they
    are never cascade candidates."""
    out: set[str] = set()
    for pn in graph.nodes_with_key(PROVES):           # Phase 2.3: a proves-relation is found by its key
        out.update(graph.out(pn))
    return out


# ---------------------------------------------------------------------------
# Axioms — ground asserted facts so they survive a cascade (existential support)
# ---------------------------------------------------------------------------

def ensure_axiom(graph: Graph) -> str:
    found = graph.nodes_named(AXIOM)
    return found[0] if found else graph.add_node(AXIOM, inert=True)  # Phase 2.2: inert flag


def axiomatize(graph: Graph, predicates: list[str]) -> str:
    """Wire `<axiom> --proves--> rel` onto every currently-unproven relation named by
    `predicates`. So a later cascade never retracts an asserted base fact (its axiom is a
    live proof). Returns the `<axiom>` node id."""
    axiom = ensure_axiom(graph)
    for pname in predicates:
        for rel in list(graph.nodes_with_key(pname)):     # Phase 2.3: relation instances by predicate key
            # a real relation instance has a subject and an object
            if not graph.out(rel) or not graph.into(rel):
                continue
            if not support_js(graph, rel):
                graph.add_relation(axiom, PROVES, rel, inert=True)  # Phase 2.2: inert flag
    return axiom
