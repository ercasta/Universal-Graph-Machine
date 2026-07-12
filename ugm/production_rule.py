"""
The rule layer — graph-rewrite rules over the untyped-edge substrate (vision §4).

A rule rewrites a subgraph. Its LHS, RHS, and NAC are each a CONJUNCTION of
triple-patterns (`Pat`). Triple-patterns are joined into an arbitrary multi-node
subgraph by SHARED node bindings: a name appearing in several patterns binds to
the SAME node instance across all of them. That is how a flat list of triples
expresses a complex structure — the shared variables are the edges of the pattern.

A triple-pattern slot (s, p, o) is one of:
  - variable      "?x"     — matches any node; binds; same "?x" = same instance
  - bound literal "paul?"  — matches a node NAMED "paul" AND binds it (key "paul")
  - plain literal "is_a"   — LHS/NAC: match some node named "is_a" (no binding)
                             RHS:     create a FRESH node named "is_a"
The predicate slot may itself be a variable ("?p") — predicates are nodes.

Because edges are untyped, a pattern (s, p, o) matches the 2-hop path
    s_node --> p_node(named p) --> o_node
(the substrate's `add_relation` shape: subject --> [rel node] --> object).

Firing semantics (every enabled match fires — there is NO branch selection):
  1. The LHS subgraph is matched, binding node instances consistently across all Pats.
  2. NAC: if the NAC subgraph also matches under those bindings, the rule does NOT fire.
  3. Graded conditions (§13) α-cut the match and yield a degree in [0, 1].
  4. On fire:
       - RHS triples are materialized. A slot bound in the LHS resolves to that
         instance; an RHS name NOT bound in the LHS creates a FRESH node instance
         (one per distinct name, reused across the RHS so multi-triple structures
         can share a freshly-created node).
       - Created nodes take confidence = matched ⊗ probability ⊗ graded-degree.
       - Created-node embeddings come from `propagate` (declarative, not a closure).
       - `drop` triples are removed — control layer only (vision §5): deletion is
         permitted on control/ephemeral edges, never on monotone fact edges.
       - `rewire` ops edit RAW EDGES between BOUND nodes — `("cut", a, b)` removes the
         edge a->b, `("link", a, b)` adds it — the identity/provenance-preserving
         structural edit `drop`+re-add cannot express (docs/depythonization_design.md §4).
         Control-layer only, and it may cut BELOW the 2-hop relation shape, so it must
         leave well-formed relations (linter-guarded) and interpose only inert nodes.
         Used to hide a fact by splicing `<retracted>` into its path, and to resurrect it.

This module is pure data + token classification. The matcher/applier lives in
rewriter.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Triple-pattern
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Pat:
    """One triple-pattern: subject --> [predicate node] --> object.

    Each slot is a token interpreted by the helpers below (variable, bound
    literal, or plain literal).
    """
    s: str
    p: str
    o: str

    def __post_init__(self) -> None:
        # Precompute each slot's classification ONCE — kind (1=var, 2=bound-literal, 0=plain),
        # binder key, and literal name — matching `is_var`/`is_bound_literal`/`binder`/`literal_name`
        # exactly. These are pure functions of the fixed slot strings that the GoalSolver join loop
        # re-derived tens of millions of times (`_pat_goal`/`_resolve`/`_extend`/`_unify_head`); cached
        # as non-field attrs on the frozen instance (absent from __init__/__eq__/__hash__/__repr__).
        set = object.__setattr__
        for pre, tok in (("s_", self.s), ("p_", self.p), ("o_", self.o)):
            var = tok.startswith("?")
            bl = tok.endswith("?") and not var
            set(self, pre + "kind", 1 if var else 2 if bl else 0)
            set(self, pre + "bind", tok if var else (tok[:-1] if bl else None))
            set(self, pre + "name", tok[:-1] if bl else tok)

    def tokens(self) -> tuple[str, str, str]:
        return (self.s, self.p, self.o)


# Token classification — shared by the matcher (rewriter.py) and authoring tools.

def is_var(tok: str) -> bool:
    """A free variable: matches any node and binds it (e.g. '?x', '?p')."""
    return tok.startswith("?")


def is_bound_literal(tok: str) -> bool:
    """A bound literal: matches a node of that name AND binds it (e.g. 'paul?')."""
    return tok.endswith("?") and not tok.startswith("?")


def rhs_only_head_vars(rule) -> list[str]:
    """Head (RHS) VARIABLES that never appear in the body (LHS) — an existential / skolem head var
    (feedback #2). These are NOT usably supported by the drivers: the forward path mints a fresh UNNAMED
    node per firing (never suppressed by check-before-derive, so the rule re-fires and the result is
    invisible to `derived_triples`); the demand chain collapses the var onto the query's goal endpoint.
    Reported so a loader can REJECT the rule with guidance rather than silently misbehave. Bound-LITERAL
    skolem binders (`<rule>?`/`<cond>?`) are excluded — they are `is_bound_literal`, not `is_var` — so a
    reified rule fragment is untouched. When genuine minting lands (the deferred `MINT`-tool route), this
    hook is where support is added instead of the raise."""
    body = {t for pats in (rule.lhs, rule.nac) for pat in pats
            for t in (pat.s, pat.p, pat.o) if is_var(t)}
    body |= {g.var for g in rule.graded if is_var(g.var)}   # a graded condition binds its var too
    body |= {v for vm in rule.value_matches                 # a value-match references LHS-bound vars
             for v in (vm.var_a, vm.var_b) if is_var(v)}
    out: list[str] = []
    for pat in rule.rhs:
        for t in (pat.s, pat.p, pat.o):
            if is_var(t) and t not in body and t not in out:
                out.append(t)
    return out


def literal_name(tok: str) -> str:
    """The node name a literal/bound-literal token refers to ('paul?' -> 'paul')."""
    return tok[:-1] if is_bound_literal(tok) else tok


def binder(tok: str) -> str | None:
    """The binding key for a token, or None for a plain (non-binding) literal.

    '?x'    -> '?x'      (variable)
    'paul?' -> 'paul'    (bound literal)
    'is_a'  -> None      (plain literal: matches by name but binds nothing)
    """
    if is_var(tok):
        return tok
    if is_bound_literal(tok):
        return tok[:-1]
    return None


# ---------------------------------------------------------------------------
# Graded condition — embedding gate on a bound node (vision §13)
# ---------------------------------------------------------------------------

@dataclass
class GradedCondition:
    """A graded LHS condition on one bound variable (vision §13).

    var:       the bound node name, e.g. '?customer' or 'paul'
    embedding: reference direction per dimension, e.g. {'urgency': 1.0}
    threshold: α-cut. The adverb->degree scale is KB DATA, not engine config: degrees are
               declared (`very is 0.8`) and read by `authoring.degree_thresholds` (see there).
    inverted:  True for 'not at all' — passes when degree <= (1 - threshold)

    Degree = min over dimensions of the node's embedding alignment (a t-norm —
    non-compensatory). On fire, the degree scales the derived confidence.
    """
    var: str
    embedding: dict[str, float]
    threshold: float
    inverted: bool = False


@dataclass
class ValueMatch:
    """A value-EQUALITY (or graded 'close-enough') LHS condition joining TWO bound variables by an
    ATTRIBUTE VALUE — the substrate's first DECLARED value-join, added deliberately beside the default
    topological join (`docs/coreference_as_rules_design.md`).

    The path match language binds variables to NODES and joins on shared TOPOLOGY; it has no "these two
    nodes carry the same value" predicate, which is why coreference was a §8 tool (`wire_same_as`), never
    a rule. `ValueMatch` is that missing predicate, as DATA: the condition holds iff `var_a` and `var_b`
    (both LHS-bound) carry the same value on `dim`.
      * `threshold is None` — EXACT equality of the VALUED attribute `dim` (e.g. `name`).
      * `threshold` set     — graded 'close enough' on the GRADED attribute `dim`: their degrees are
                              within the threshold (see `chain._value_matches_ok`).
    The enabler for coreference-as-RULES: `?x same_as ?y when ?x is a person and ?y is a person and
    <same-value ?x ?y name>`, so identity is defeasible bank data, not a mechanical ingest merge. NOTE:
    exact same-NAME coref needs the id-addressed core (env binds ids), since today's name-keyed env
    collapses two same-named nodes to one binding; graded/cross-name value-coref already works."""
    var_a: str
    var_b: str
    dim: str = "name"                 # the reserved NAME attr (attrgraph.NAME); a graded dim when threshold set
    threshold: float | None = None


# ---------------------------------------------------------------------------
# Rule
# ---------------------------------------------------------------------------

@dataclass
class Rule:
    """A graph-rewrite rule. LHS/RHS/NAC/drop are subgraph patterns (see module doc)."""
    key: str
    lhs: list[Pat]
    rhs: list[Pat]
    nac: list[Pat] = field(default_factory=list)        # subgraph; blocks fire if present
    drop: list[Pat] = field(default_factory=list)       # control-layer deletions only
    rewire: list[tuple[str, str, str]] = field(default_factory=list)
    probability: float = 1.0                            # prior; flows into derived confidence
    graded: list[GradedCondition] = field(default_factory=list)
    value_matches: list[ValueMatch] = field(default_factory=list)   # declared value-JOIN conditions
                                                        # (`ValueMatch`): the coreference-as-rules enabler.
    propagate: dict | None = None                       # e.g. {"op": "weighted_sum", "weights": [...]}
    priority: float = 0.0                               # provisional scheduling tie-break
    max_steps: int = 5
    meta: bool = False                                  # META/TMS rule: fires PROVENANCE-SILENT even in a
                                                        # prov-on run (the regress guard — a meta-rule that
                                                        # names proves/uses would else re-match its own <j:>).
                                                        # Lets reasoning + TMS rules share ONE run().
    coref_prop: bool = False                            # DECLARED role (Phase 5.4): a `same_as`
                                                        # coreference-propagation rule (`universal.same_as_rules`).
                                                        # Its PRESENCE is the DATA that turns coref-following ON
                                                        # in `GoalSolver` (the union-find is these rules' fast
                                                        # evaluation, so they're dropped as subsumed). A declared
                                                        # property the engine READS — replaces the old
                                                        # `_is_same_as_prop` key-prefix SNIFFING. Like `meta`, a
                                                        # rule-datum's self-description, not engine inference.

    def __post_init__(self) -> None:
        if self.drop and not self._drops_only_bound():
            # Deletion must reference bound (matched) nodes — you cannot delete what
            # you did not match. Fresh-node deletion is meaningless.
            pass  # left as a soft note; rewriter enforces control-edge-only deletion

    def _drops_only_bound(self) -> bool:
        bound = self.bound_names()
        return all(binder(t) in bound or binder(t) is None
                   for d in self.drop for t in d.tokens())

    def bound_names(self) -> set[str]:
        """Binding keys introduced by the LHS (available to RHS/NAC/drop/graded)."""
        names: set[str] = set()
        for pat in self.lhs:
            for tok in pat.tokens():
                b = binder(tok)
                if b is not None:
                    names.add(b)
        return names

    def fresh_names(self) -> set[str]:
        """RHS binding keys NOT bound by the LHS — these create fresh node instances."""
        bound = self.bound_names()
        names: set[str] = set()
        for pat in self.rhs:
            for tok in pat.tokens():
                b = binder(tok)
                if b is not None and b not in bound:
                    names.add(b)
        return names


# ---------------------------------------------------------------------------
# Firing — one journal entry (vision §9). Lives here (a shared, engine-neutral type) so the
# journal consumers (surface.explain, driver, session) do not import the reference `rewriter`.
# ---------------------------------------------------------------------------

@dataclass
class Firing:
    """One journal entry (vision §9): the rule that fired, its bindings, the nodes it created,
    and the derived degree."""
    rule_key: str
    bindings: dict[str, str]
    created: set[str] = field(default_factory=set)
    degree: float = 1.0


# ---------------------------------------------------------------------------
# near_rules — the rules a ground locus would seed (walkers doc §7). Lives here (engine-neutral,
# reads only Rule.lhs anchors) so it survives independent of any one matching engine.
# ---------------------------------------------------------------------------

def _anchor_names(rule: Rule) -> set[str]:
    """Every GROUND anchor NAME in `rule`'s LHS — the names the lexical index can seed this
    rule from (literal predicates/subjects/objects and bound-literals; free variables are not
    anchors)."""
    return {literal_name(t) for pat in rule.lhs for t in pat.tokens() if not is_var(t)}


def near_rules(graph, rules: list["Rule"], locus: str) -> list["Rule"]:
    """The rules NEAR a ground locus (vision §11 / walkers doc §7): those the lexical index
    would seed from this node — i.e. whose LHS has a ground anchor matching the node's NAME. A
    walker is a persistent, moving ground locus (its token); calling this on the token gives its
    near-rule set, so two walkers with different tokens get DIFFERENT near-rules automatically."""
    nm = graph.name(locus)
    return [r for r in rules if nm in _anchor_names(r)]
