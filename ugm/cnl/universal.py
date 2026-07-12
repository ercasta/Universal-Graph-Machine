"""
Universal rules — domain-independent reasoning, as ordinary graph-rewrite rules.

These are reusable `Rule`s (not surface forms): they operate on canonical relations
the forms produce. Authored here as `Rule` objects for now; in the homoiconic limit
they too would be loaded from CNL.
"""
from __future__ import annotations

from ..production_rule import Pat, Rule, ValueMatch
from ..attrgraph import NAME
from ..vocabulary import COPULA, NEG_COPULA, IS_A, IS_A_NOT, SAME_AS, DISJOINT, TARGET, TYPE, MENTION


UNIVERSAL_RULES: list[Rule] = [
    # IS-A transitivity (subsumption): a is_a b, b is_a c  =>  a is_a c.
    # NAC keeps it idempotent and bounds the loop to the transitive closure.
    Rule(
        key="is_a.transitive",
        lhs=[Pat("?a", IS_A, "?b"), Pat("?b", IS_A, "?c")],
        nac=[Pat("?a", IS_A, "?c")],
        rhs=[Pat("?a", IS_A, "?c")],
    ),
    # Goal satisfaction: a goal wanting (target is_a type) is satisfied once that holds.
    Rule(
        key="goal.satisfied",
        lhs=[Pat("?g", TARGET, "?x"), Pat("?g", TYPE, "?y"), Pat("?x", IS_A, "?y")],
        nac=[Pat("?g", COPULA, "satisfied")],
        rhs=[Pat("?g", COPULA, "satisfied")],
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
                  lhs=[Pat("?a", SAME_AS, "?b")], rhs=[Pat("?b", SAME_AS, "?a")])]
    for p in sorted(set(predicates) | {SAME_AS}):
        rules.append(Rule(key=f"same_as.subj.{p}", coref_prop=True,
                          lhs=[Pat("?a", SAME_AS, "?b"), Pat("?a", p, "?o")],
                          rhs=[Pat("?b", p, "?o")]))
        rules.append(Rule(key=f"same_as.obj.{p}", coref_prop=True,
                          lhs=[Pat("?a", SAME_AS, "?b"), Pat("?s", p, "?a")],
                          rhs=[Pat("?s", p, "?b")]))
    return rules


# A reusable default over the universal predicates (domains add their own via `same_as_rules`).
SAME_AS_RULES: list[Rule] = same_as_rules([IS_A, COPULA, TARGET, TYPE])


# SAME-NAME coreference as ONE DECLARED value-match RULE (coreference-as-rules Stage 4) — the principled
# replacement for the mechanical `wire_same_as` ingest default. `wire_same_as` baked a "same name ⇒ same
# thing" NLP judgment into the loader; here coreference is bank DATA a rule expresses, which the
# id-addressed core (env binds ids, so two same-named mentions are DISTINCT vars) + the value-JOIN op
# (`chain._value_matches_ok` / forward `machine.VMATCH`) can fire. The binding is the UNIVERSAL surface
# mention marker `is_a <mention>` that `forms.mark_mentions` tags every entity with — so BOTH vars seed
# over any entity, POSITION-AGNOSTICALLY (an entity carries the marker whether it appeared as a subject or
# an object), and untyped entities corefer without a per-domain type. `same_as_rules` then propagate facts
# across the derived `same_as` link, exactly as for asserted identity. An author who wants narrower/graded/
# no coref keeps, replaces, or drops this rule (or writes a typed/embedding one — coref is DATA).

def same_name_coref_rules(graph=None) -> list[Rule]:
    """The universal same-NAME coreference rule: `?x same_as ?y when ?x is_a <mention> and ?y is_a
    <mention> and <same-value ?x ?y name>` — distinct nodes marked as mentions that share a `name` derive
    `same_as` (the reflexive self-pair is a harmless self-loop). `graph` is accepted for call-site symmetry
    with the graph-reading generators and ignored (the rule is graph-independent — the marker is the handle)."""
    return [Rule(key="coref.same_name",
                 lhs=[Pat("?x", IS_A, MENTION), Pat("?y", IS_A, MENTION)],
                 rhs=[Pat("?x", SAME_AS, "?y")],
                 value_matches=[ValueMatch("?x", "?y", NAME)])]


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
            if not graph.has_key(r, DISJOINT):
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
                              lhs=[Pat("?z", COPULA, x)], rhs=[Pat("?z", NEG_COPULA, y)]))
            rules.append(Rule(key=f"disjoint.is_a_not.{x}.{y}",
                              lhs=[Pat("?z", IS_A, x)], rhs=[Pat("?z", IS_A_NOT, y)]))
    return rules
