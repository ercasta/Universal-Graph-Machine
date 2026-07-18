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
ASSUMES = "assumes"      # J --assumes--> <assumed> : a NAC the firing LEANED ON (possibilistic —
                         # the absence was assumed at some necessity, not proven; docs/possibilistic.md)
AXIOM = "<axiom>"
ASSUMED = "<assumed>"    # the inert record of one leaned-on absence: a_pred/a_subj/a_obj + a_pi (Π)
_J_PREFIX = "<j:"

# Predicate names the matcher/locality treats as inert (kept in sync with world_model).
PROVENANCE_PREDS: frozenset[str] = frozenset({PROVES, USES, ASSUMES})


# ---------------------------------------------------------------------------
# Justification node naming
# ---------------------------------------------------------------------------

def j_name(rule_key: str) -> str:
    """The name of the justification node for a firing of `rule_key` (canonicalize-proof:
    it starts with '<', so the merge tool skips it; the key is recoverable)."""
    return f"{_J_PREFIX}{rule_key}>"


def is_justification(name: str) -> bool:
    return name.startswith(_J_PREFIX)


def record_assumptions(graph: Graph, j: str,
                       assumed: list[tuple[str, str | None, str | None, float]]) -> None:
    """Journal the ABSENCES a firing leaned on: one inert `<assumed>` node per surviving NAC
    (`a_pred`/`a_subj`/`a_obj` + `a_pi` = how possible the counter-evidence was; 0.0 = crisp
    "no evidence was found"), wired `J --assumes--> <assumed>` — as a MINT program (the ONE
    minting path, shared by the demand chain and the forward `run_bank`). A None subject/object
    is a wildcard, recorded as `anyone`/`anything`. These records are what `why` renders as the
    firing's leaps and what RECONSIDER re-checks (docs/design/reconsider_design.md).

    An entry may carry a 5th element, the NAC GROUP tag (feedback #16): atoms of one conjunctive NAC
    were assumed absent JOINTLY, not each on its own, and saying "assumed not: l1 has anything" about a
    `l1` that demonstrably HAS something would be simply false. The tag is recorded as `a_group` so
    `assumption_groups` can render them as one joint clause; entries without it are their own group."""
    from .attrgraph import NAME, valued, graded
    from .machine import Machine, MINT, State
    ops = []
    for i, entry in enumerate(assumed):
        np, ns, no, pi = entry[:4]
        group = entry[4] if len(entry) > 4 else i
        ops.append(MINT(f"_a{i}", inert=True,
                        attrs={NAME: valued(ASSUMED),
                               "a_pred": valued(np),
                               "a_subj": valued(ns if ns is not None else "anyone"),
                               "a_obj": valued(no if no is not None else "anything"),
                               "a_group": valued(group),
                               "a_pi": valued(pi)}))
        ops.append(MINT(f"_ar{i}", attrs={ASSUMES: graded(1.0)},
                        in_edges=["_jr"], edges=[f"_a{i}"], inert=True))
    if ops:
        Machine().apply(graph, ops, State({"_jr": j}))


def record_firing(graph: Graph, rule_key: str, made: list[str], premises: list[str]) -> str:
    """RECORD (mode 9) as an ISA program — the ONE justification-minting path, shared by the forward
    driver (`run_bank`) and the demand driver (`apply._record`/`chain`). Mints `<j:RULEKEY>` with
    `proves -> each made fact` and `uses -> each premise rel node`, all inert, by ASSEMBLING a MINT
    program and running it through the interpreter (machine semantics are ISA programs — no Python
    helper pokes the substrate; exactly `assemble_facts`' discipline applied to provenance).
    The `<j:>` node carries its token as a GRADED key alongside its VALUED name (the `add_node`
    string-form dual-write both paths now share). Returns the justification node id."""
    from .attrgraph import NAME, valued, graded
    from .machine import Machine, MINT, State
    jn = j_name(rule_key)
    ops = [MINT("_j", attrs={NAME: valued(jn), jn: graded(1.0)}, inert=True)]
    regs: dict[str, str] = {}
    for i, c in enumerate(made):
        regs[f"_c{i}"] = c
        ops.append(MINT(f"_pv{i}", attrs={PROVES: graded(1.0)},
                        in_edges=["_j"], edges=[f"_c{i}"], inert=True))
    for i, p in enumerate(premises):
        regs[f"_u{i}"] = p
        ops.append(MINT(f"_us{i}", attrs={USES: graded(1.0)},
                        in_edges=["_j"], edges=[f"_u{i}"], inert=True))
    return Machine().apply(graph, ops, State(regs)).regs["_j"]


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


def assumptions_of(graph: Graph, j: str) -> list[tuple[str, str, str, float]]:
    """The ABSENCES the firing at `j` leaned on (NAF — `J --assumes--> <assumed>`): `(pred, subj,
    obj, Π)` per assumption, where Π is how possible the counter-evidence was when the negation
    was taken. A crisp firing journals its surviving NACs at Π = 0 (2026-07-16, the record half
    of the hard-vs-assumed capstone) — these are what RECONSIDER re-checks."""
    out: list[tuple[str, str, str, float]] = []
    for a in _objects_via(graph, j, ASSUMES):
        p, s, o, pi = (graph.get_attr(a, k) for k in ("a_pred", "a_subj", "a_obj", "a_pi"))
        if p is not None and s is not None and o is not None:
            out.append((str(p.value), str(s.value), str(o.value),
                        float(pi.value) if pi is not None else 0.0))
    return out


def assumption_groups(graph: Graph, j: str) -> list[list[tuple[str, str, str, float]]]:
    """The firing's leaned-on absences GROUPED by the NAC they came from (feedback #16). A group with
    one atom is an ordinary independent negation; a group with several is ONE conjunctive NAC whose
    atoms were assumed jointly absent — `why` must render those together, since no individual atom is
    being claimed absent. Order-preserving; an old record with no `a_group` is its own group."""
    groups: dict[str, list[tuple[str, str, str, float]]] = {}
    for i, a in enumerate(_objects_via(graph, j, ASSUMES)):
        p, s, o, pi, gp = (graph.get_attr(a, k)
                           for k in ("a_pred", "a_subj", "a_obj", "a_pi", "a_group"))
        if p is None or s is None or o is None:
            continue
        key = str(gp.value) if gp is not None else f"_{i}"
        groups.setdefault(key, []).append(
            (str(p.value), str(s.value), str(o.value), float(pi.value) if pi is not None else 0.0))
    return list(groups.values())


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
