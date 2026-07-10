"""
Universal rules — domain-independent reasoning, as ordinary graph-rewrite rules.

These are reusable `Rule`s (not surface forms): they operate on canonical relations
the forms produce. Authored here as `Rule` objects for now; in the homoiconic limit
they too would be loaded from CNL.
"""
from __future__ import annotations

from ..production_rule import Pat, Rule


UNIVERSAL_RULES: list[Rule] = [
    # IS-A transitivity (subsumption): a is_a b, b is_a c  =>  a is_a c.
    # NAC keeps it idempotent and bounds the loop to the transitive closure.
    Rule(
        key="is_a.transitive",
        lhs=[Pat("?a", "is_a", "?b"), Pat("?b", "is_a", "?c")],
        nac=[Pat("?a", "is_a", "?c")],
        rhs=[Pat("?a", "is_a", "?c")],
    ),
    # Goal satisfaction: a goal wanting (target is_a type) is satisfied once that holds.
    Rule(
        key="goal.satisfied",
        lhs=[Pat("?g", "target", "?x"), Pat("?g", "type", "?y"), Pat("?x", "is_a", "?y")],
        nac=[Pat("?g", "is", "satisfied")],
        rhs=[Pat("?g", "is", "satisfied")],
    ),
]


# Coreference as RULES (vision §3): instead of a tool MERGING same-named nodes (crude,
# destructive, and a recurring corruption source), mentions are linked by an ADDITIVE
# `same_as` relation and facts PROPAGATE across the link. Monotone (never deletes), so it
# never corrupts; and `same_as` can be wired SELECTIVELY (two genuinely distinct `Paul`s
# need not be linked), which a merge cannot express. `same_as` is an equivalence: symmetric
# (below), and transitive for free (the subject rule with ?p = same_as carries it).
#
# Propagation copies a node's relations to anything it is `same_as`. This is equality
# saturation — it can be costly at scale (every fact copied across each link); the merge
# was cheaper. The trade is correctness/monotonicity + selectivity for that cost.
# Propagation is generated PER PREDICATE (literal), NOT with a generic variable predicate.
# A variable-predicate rule (`?a same_as ?b, ?a ?p ?o => ?b ?p ?o`) is tempting and concise,
# but the engine REUSES the bound predicate node, so propagating reuses the relation
# instance — giving it multiple subjects, which densely cross-connects the graph and blows up
# (equality saturation runs away). A literal predicate mints a FRESH, deduped relation node
# (`_relation_exists`), so propagation stays clean and terminating. Cost: one rule pair per
# predicate of interest — callers pass the predicates that matter (incl. "same_as" itself,
# which carries transitivity). No NAC needed (dedup + fired-set terminate; keeps stratify happy).

def same_as_rules(predicates) -> list[Rule]:
    """Coreference propagation rules over `predicates` (vision §3): a `same_as` link carries
    each named relation across it, in both subject and object position. Include "same_as" to
    get transitivity. See the note above on why literal (not variable) predicates."""
    # Each rule carries `coref_prop=True` — the DECLARED role (Phase 5.4) `GoalSolver` reads to
    # turn coref-following ON and drop these rules as subsumed by its union-find, replacing the old
    # `_is_same_as_prop` key-prefix sniffing. The role is data ON the rule, set where it's defined.
    rules = [Rule(key="same_as.symmetric", coref_prop=True,
                  lhs=[Pat("?a", "same_as", "?b")], rhs=[Pat("?b", "same_as", "?a")])]
    for p in sorted(set(predicates) | {"same_as"}):
        rules.append(Rule(key=f"same_as.subj.{p}", coref_prop=True,
                          lhs=[Pat("?a", "same_as", "?b"), Pat("?a", p, "?o")],
                          rhs=[Pat("?b", p, "?o")]))
        rules.append(Rule(key=f"same_as.obj.{p}", coref_prop=True,
                          lhs=[Pat("?a", "same_as", "?b"), Pat("?s", p, "?a")],
                          rhs=[Pat("?s", p, "?b")]))
    return rules


# A reusable default over the universal predicates (domains add their own via `same_as_rules`).
SAME_AS_RULES: list[Rule] = same_as_rules(["is_a", "is", "target", "type"])


# ENTAILED NEGATION (decision-cwa-default): disjointness ENTAILS a negation — if `A disjoint_from B`
# and `x is A`, then `x is_not B` (a HARD `no`, provably-false, distinct from the defeasible CWA
# `assumed-no`). This lets an agent trust a `no` from disjointness the way it trusts a `yes`, and it
# makes CWA-default SAFER: the negations that matter can be ENTAILED rather than assumed.
#
# Generated PER DISJOINT PAIR with LITERAL predicates (like `rule_graph._disjoint_rule`, the
# detection twin), NOT a variable `?a` join — a literal `?z is A` matches every mention of the
# concept A by NAME, so it does not depend on the two `A` mentions (alice's state vs the disjoint
# category) being one node (they are distinct under additive coref). Both directions (disjointness is
# symmetric) and both the copula (`is`/`is_not`) and category (`is_a`/`is_a_not`) forms; the is_a
# form composes with is_a transitivity (`rex is_a poodle`, `poodle is_a dog`, `dog disjoint_from cat`
# -> `rex is_a_not cat`). Additive + demand-driven (derived only when a negation goal asks), §5-safe.

def entailed_negation_rules(graph) -> list[Rule]:
    """Per-disjoint-pair `is_not`/`is_a_not` entailment rules read off `graph`'s `disjoint_from`
    declarations (`A disjoint_from B` -> `?z is A => ?z is_not B`, both directions, copula + is_a)."""
    pairs: set[frozenset] = set()
    for n in graph.nodes():
        a = graph.name(n)
        if graph.is_inert(n) or a.startswith("<"):   # Phase 2.2: inert FLAG (proves/uses); `<…>` catches token names
            continue
        for r in graph.out(n):
            if graph.name(r) != "disjoint_from":
                continue
            for o in graph.out(r):
                b = graph.name(o)
                if not graph.is_inert(o) and not b.startswith("<") and a != b:
                    pairs.add(frozenset((a, b)))
    rules: list[Rule] = []
    for pair in pairs:
        a, b = sorted(pair)
        for x, y in ((a, b), (b, a)):
            rules.append(Rule(key=f"disjoint.is_not.{x}.{y}",
                              lhs=[Pat("?z", "is", x)], rhs=[Pat("?z", "is_not", y)]))
            rules.append(Rule(key=f"disjoint.is_a_not.{x}.{y}",
                              lhs=[Pat("?z", "is_a", x)], rhs=[Pat("?z", "is_a_not", y)]))
    return rules
