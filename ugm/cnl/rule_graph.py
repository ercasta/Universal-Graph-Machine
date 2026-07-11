"""
Rules as graph nodes — the homoiconic rule representation (vision §2).

A rule is stored in the substrate as a **literal-subgraph fragment**, in the same
shape as the facts it will rewrite:

  - the rule is a node whose NAME is its key;
  - it points, through role relations 'lhs' / 'rhs' / 'nac' / 'drop', at the
    PREDICATE node of each of its Pats;
  - a Pat (s, p, o) is the 2-hop path  subj --> pred --> obj, where the three nodes
    are NAMED by the pattern tokens ('?a', 'is_a', '?b').  Predicate nodes are FRESH
    per Pat (so reading one Pat back is unambiguous — each pred has exactly one
    non-role in-edge and one out-edge).  Subject/object nodes are SHARED by token
    name within a rule, so a shared variable ('?b' as the object of one Pat and the
    subject of the next) is ONE node — the pattern's join structure is visible as
    graph structure, exactly as the homoiconic vision intends.

`write_rule` materializes an in-memory `Rule` into this shape; `rules_in_graph`
reads the shape back into executable `Rule` objects.

`rules_in_graph` is a §8 calculator TOOL: it reflects rule-nodes that already live
in the graph into the engine's matchable form — the seam-free counterpart of a
compiler (same substrate in, executable view out), and exactly the function a
meta-circular `run` would call per step (the b2 step, still future).

For now rules live in a dedicated rule-graph, kept separate from the fact graph so
their placeholder nodes ('?a') never bind as facts.  Folding them into the one
graph (with scope segregation between pattern-space and fact-space) is the
meta-circular milestone — the schema here does not change for it.

Limitations (b1): only the structural fields (lhs/rhs/nac/drop) round-trip. The
graded layer (`probability`, `graded`, `priority`, `propagate`) is not yet encoded
as nodes — that needs the datum-node encodings and is deliberately deferred so the
first slice stays minimal.
"""
from __future__ import annotations

from ..production_rule import Pat, Rule
from ..world_model import Graph
from ..attrgraph import valued

# The role relations that wire a rule node to the predicate node of each Pat.
ROLE_NAMES: tuple[str, ...] = ("lhs", "rhs", "nac", "drop")

# A reified graded condition: `<rule> -[graded]-> <graded>` where the `<graded>` node carries the
# α-cut as VALUED attrs (`gc_var`/`gc_dim`/`gc_threshold`), one per (var, dim) — the reified form of a
# `GradedCondition`, so the demand-driven firmware (`chain._read_graded`) can apply the α-cut DURING
# matching exactly as the forward `GRADE` op does (Phase 5.2's graded-α-cut companion, on the chain).
GRADED_ROLE = "graded"


def write_rule(graph: Graph, rule: Rule) -> str:
    """Materialize `rule` into `graph` as a literal-subgraph fragment.

    Returns the rule node id (named by `rule.key`). Subject/object positions are
    shared by token name within this rule; predicate positions are fresh per Pat.

    Phase 3.1 (canonical shape, 2.1/2.2-aligned): the whole fragment is CONTROL-layer
    structure — rule / pattern-predicate / shared-var nodes are never facts — so a folded
    one-graph can segregate pattern-space from fact-space by the `control` flag rather than
    a separate graph. And each pattern atom is built in FACT SHAPE via `add_relation`
    (`subj --> [pred node carrying the predicate as a graded KEY] --> obj`), so the reified
    rule is literally in the shape of the facts it rewrites — the firmware's APPLY can seed a
    pattern predicate through `nodes_with_key`/`has_key` exactly as it seeds a fact.
    """
    rule_node = graph.add_node(rule.key, control=True)
    shared: dict[str, str] = {}                      # subj/obj token -> node id (this rule only)

    def so_node(tok: str) -> str:
        if tok not in shared:
            shared[tok] = graph.add_node(tok, control=True)
        return shared[tok]

    for role, pats in (("lhs", rule.lhs), ("rhs", rule.rhs),
                       ("nac", rule.nac), ("drop", rule.drop)):
        for pat in pats:
            s = so_node(pat.s)
            o = so_node(pat.o)
            p = graph.add_relation(s, pat.p, o, control=True)   # pattern atom in fact shape (keyed pred)
            graph.add_relation(rule_node, role, p, control=True)  # rule --[role]--> pred
    # Graded conditions (the α-cut match filter). Reified as `<graded>` nodes so the demand-driven
    # firmware can apply them; one per (var, dim) — mirroring `lowering.lower_graded`'s one-GRADE-per-dim.
    # An INVERTED α-cut ('not at all') is a later slice (as in `lower_graded`), so it is skipped here.
    for gc in rule.graded:
        if gc.inverted:
            continue
        for dim in gc.embedding:
            g = graph.add_node("<graded>", control=True)
            graph.set_attr(g, "gc_var", valued(gc.var))
            graph.set_attr(g, "gc_dim", valued(dim))
            graph.set_attr(g, "gc_threshold", valued(gc.threshold))
            graph.add_relation(rule_node, GRADED_ROLE, g, control=True)
    return rule_node


def _read_pat(graph: Graph, pred: str, role_node: str) -> Pat:
    """Reconstruct a Pat from its predicate node (pred's single non-role in/out edges)."""
    ins = [n for n in graph.into(pred) if n != role_node]
    outs = list(graph.out(pred))
    return Pat(graph.name(ins[0]), graph.predicate(pred), graph.name(outs[0]))


def _pat_key(p: Pat) -> tuple[str, str, str]:
    return p.tokens()


def rules_in_graph(graph: Graph) -> list[Rule]:
    """Read every rule-node in `graph` back into an executable `Rule` (the b1 tool).

    A rule node is identified as the subject of any role relation. Pats are sorted
    within each role for deterministic output (order is irrelevant to matching).
    """
    by_rule: dict[str, dict[str, list[Pat]]] = {}
    for nid in graph.nodes():
        for role_node, pred in graph.relations_from(nid):
            role = graph.predicate(role_node)
            if role not in ROLE_NAMES:
                continue
            by_rule.setdefault(nid, {}).setdefault(role, []).append(
                _read_pat(graph, pred, role_node)
            )

    rules: list[Rule] = []
    for rid in sorted(by_rule, key=graph.name):
        roles = by_rule[rid]
        rules.append(Rule(
            key=graph.name(rid),
            lhs=sorted(roles.get("lhs", []), key=_pat_key),
            rhs=sorted(roles.get("rhs", []), key=_pat_key),
            nac=sorted(roles.get("nac", []), key=_pat_key),
            drop=sorted(roles.get("drop", []), key=_pat_key),
        ))
    return rules


# ---------------------------------------------------------------------------
# Meta: relation-property declarations -> concrete rule-nodes
# ---------------------------------------------------------------------------
#
# This recreates the old `universal.cnl` lines ('is_a is transitive', ...) in the
# new paradigm. A declaration is ordinary CNL parsed by the forms below into a
# canonical `R --rel_property--> transitive` relation. The EXPANSION (declaration ->
# the concrete transitivity/symmetry rule) is a §8 TOOL, not a Pat-rule: emitting a
# rule fragment requires creating nodes literally NAMED '?a'/'?b', but the token
# language reads '?a' as a variable, not a name — that quote/eval gap is the same
# wall the meta-circular engine (b2) would have to climb. Tooling around it keeps
# this in the established calculator category (cf. canonicalize, rules_in_graph).
#
# Static, not live: run the forms, expand to rule-nodes, then `rules_in_graph` for
# the reasoning run. No live-rule machinery is needed (b2 is parked).

PROPERTY_REL = "rel_property"   # canonical predicate: R --rel_property--> <property>
DISJOINT_REL = "disjoint_from"  # category disjointness: A --disjoint_from--> B
CONTRADICTION = "<contradiction>"   # a derived inconsistency marker (vision §5)


def _contradiction_rhs(reason: str, *offenders: str) -> list[Pat]:
    """RHS that flags an inconsistency: a FRESH `<contradiction>` node (a bound-literal
    so it is minted, not reused) wired `--about--> X` to each offender and `--violates-->`
    the declared constraint. Detection only ADDS a marker (vision §5: never reject/delete);
    a guard/linter/human reads it. `contradictions`/`is_consistent` are the readers."""
    rhs = [Pat(f"{CONTRADICTION}?", "about", x) for x in offenders]
    rhs.append(Pat(f"{CONTRADICTION}?", "violates", reason))
    return rhs


# The acceptance forms for "R is transitive" / "R is symmetric". Kept here (not in
# FORM_RULES) so the core grammar stays free of this feature; compose them in when
# you want relation-property declarations. Anchored to the sentence's first token
# and keyed on the specific property keyword, so they never overgeneralize "X is Y".
def _property_form(prop: str) -> Rule:
    """The acceptance form `R is <prop>` -> `R --rel_property--> <prop>` (anchored to the
    sentence's first token, keyed on the property keyword so it never overgeneralizes)."""
    return Rule(
        key=f"form.{prop}",
        lhs=[Pat("?s", "first", "?r"),
             Pat("?r", "next", "is?"), Pat("is?", "next", f"{prop}?")],
        rhs=[Pat("?r", PROPERTY_REL, prop)],
    )


# `R is transitive|symmetric|irreflexive|asymmetric|acyclic` declarations.
RELATION_PROPERTY_FORMS: list[Rule] = [
    _property_form(p) for p in
    ("transitive", "symmetric", "irreflexive", "asymmetric", "acyclic")
]

# `A is disjoint from B` -> `A --disjoint_from--> B` (the category-pair constraint).
DISJOINT_FORMS: list[Rule] = [
    Rule(
        key="form.disjoint_from",
        lhs=[Pat("?s", "first", "?a"), Pat("?a", "next", "is?"),
             Pat("is?", "next", "disjoint?"), Pat("disjoint?", "next", "from?"),
             Pat("from?", "next", "?b")],
        rhs=[Pat("?a", DISJOINT_REL, "?b")],
    ),
]

# All the universal-constraint declaration forms (compose into FORM_RULES when wanted).
CONSTRAINT_FORMS: list[Rule] = RELATION_PROPERTY_FORMS + DISJOINT_FORMS


def _property_rule(rel: str, prop: str) -> list[Rule]:
    """The concrete rule(s) a relation `rel` gets from being declared `prop`.

    Two families (vision: a domain-independent property applied by generalization):
      - GAP-FILLING (`transitive`, `symmetric`) — derive the implied fact.
      - CONTRADICTION-DETECTING (`irreflexive`, `asymmetric`, `acyclic`) — derive a
        `<contradiction>` marker on the offending configuration. None of these needs an
        inequality primitive: `irreflexive`/`asymmetric` read self/mutual edges directly,
        and `acyclic` = transitive (closure) + irreflexive, so a cycle surfaces as a
        self-loop `?a R ?a` after closure. (`functional`/`injective` DO need distinctness
        and are deferred — see docs/consistency_design.md.)
    """
    if prop == "transitive":
        return [Rule(
            key=f"{rel}.transitive",
            lhs=[Pat("?a", rel, "?b"), Pat("?b", rel, "?c")],
            nac=[Pat("?a", rel, "?c")],
            rhs=[Pat("?a", rel, "?c")],
        )]
    if prop == "symmetric":
        return [Rule(
            key=f"{rel}.symmetric",
            lhs=[Pat("?a", rel, "?b")],
            nac=[Pat("?b", rel, "?a")],
            rhs=[Pat("?b", rel, "?a")],
        )]
    # NB: detection rules carry NO idempotency NAC. A NAC on the produced `<contradiction>
    # --about--> X` would make every detection rule both produce AND negate `about`, which
    # is a cross-rule negation cycle under stratification (`run_rules` would refuse to run a
    # bank with two such constraints). Re-running over a standing violation therefore creates
    # duplicate markers; the `contradictions` reader DEDUPES them for display, and a session
    # can GC them. Run detection with plain `run` (no inter-rule negation among constraints).
    if prop == "irreflexive":
        return [Rule(
            key=f"{rel}.irreflexive",
            lhs=[Pat("?a", rel, "?a")],
            rhs=_contradiction_rhs(rel, "?a"),
        )]
    if prop == "asymmetric":          # mutual edges contradict (subsumes irreflexive at ?a==?b)
        return [Rule(
            key=f"{rel}.asymmetric",
            lhs=[Pat("?a", rel, "?b"), Pat("?b", rel, "?a")],
            rhs=_contradiction_rhs(rel, "?a", "?b"),
        )]
    if prop == "acyclic":             # transitive closure + irreflexive check on the closure
        return _property_rule(rel, "transitive") + [Rule(
            key=f"{rel}.acyclic",
            lhs=[Pat("?a", rel, "?a")],
            rhs=_contradiction_rhs(rel, "?a"),
        )]
    return []


def _disjoint_rule(cat_a: str, cat_b: str) -> Rule:
    """A category-disjointness constraint: nothing is BOTH `cat_a` and `cat_b`.

    `?x is_a cat_a, ?x is_a cat_b ⇒ <contradiction>`. Needs no inequality (the two
    categories are distinct literal nodes) and composes with `is_a` transitivity
    (UNIVERSAL_RULES), so it fires through is_a generalization for any specific thing —
    e.g. `poodle is_a dog`, `dog disjoint_from cat`, then `rex is_a poodle, rex is_a cat`
    flags `rex`. This is the cleanest 'universal law' in the substrate."""
    return Rule(
        key=f"disjoint.{cat_a}.{cat_b}",
        lhs=[Pat("?x", "is_a", cat_a), Pat("?x", "is_a", cat_b)],
        rhs=_contradiction_rhs(f"{cat_a}|{cat_b}", "?x"),
    )


def expand_relation_properties(graph: Graph, rule_graph: Graph | None = None) -> Graph:
    """Read constraint/property declarations from `graph` and emit the concrete rule-nodes
    into `rule_graph` (a §8 tool). Returns the rule-graph.

    Handles `R --rel_property--> <prop>` (transitive/symmetric/irreflexive/asymmetric/
    acyclic) and `A --disjoint_from--> B`. `rules_in_graph(returned_graph)` then yields the
    executable rules. Unknown properties are ignored; each declaration is expanded once.
    """
    rg = rule_graph if rule_graph is not None else Graph()
    seen: set[tuple[str, ...]] = set()
    for nid in graph.nodes():
        for rel_node, obj in graph.relations_from(nid):
            rname = graph.predicate(rel_node)
            if rname == PROPERTY_REL:
                key = (rname, graph.name(nid), graph.name(obj))
                if key in seen:
                    continue
                seen.add(key)
                for rule in _property_rule(graph.name(nid), graph.name(obj)):
                    write_rule(rg, rule)
            elif rname == DISJOINT_REL:
                key = (rname, graph.name(nid), graph.name(obj))
                if key in seen:
                    continue
                seen.add(key)
                write_rule(rg, _disjoint_rule(graph.name(nid), graph.name(obj)))
    return rg


# ---------------------------------------------------------------------------
# Reading the inconsistency markers (the guarded read — vision §5)
# ---------------------------------------------------------------------------

def contradictions(graph: Graph) -> list[dict]:
    """Every distinct `<contradiction>` as `{"about": [...], "violates": [...]}`.

    Detection only ADDS these markers (vision §5); this is the guarded read that surfaces
    them. `about` = the offending node name(s), `violates` = the constraint that fired.
    DEDUPED: detection rules carry no idempotency NAC (it would cause a stratification
    cycle — see `_property_rule`), so a standing violation may have several identical
    markers; they collapse to one here."""
    seen: set = set()
    out: list[dict] = []
    for c in graph.nodes_named(CONTRADICTION):
        about, violates = [], []
        for r, o in graph.relations_from(c):
            if graph.has_key(r, "about"):
                about.append(graph.name(o))
            elif graph.has_key(r, "violates"):
                violates.append(graph.name(o))
        key = (frozenset(about), frozenset(violates))
        if key in seen:
            continue
        seen.add(key)
        out.append({"about": sorted(about), "violates": sorted(violates)})
    return out


def is_consistent(graph: Graph) -> bool:
    """True iff no `<contradiction>` marker has been derived."""
    return not graph.nodes_named(CONTRADICTION)
