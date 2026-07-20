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
       - (`rewire` — the raw cut/link edge edit behind the pre-Axis-A `<retracted>`
         interposition — was DELETED 2026-07-16 with the INTERPOSE/RESTORE opcodes;
         retraction is copy-on-delete + `RETIRE` now.)

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
    skolem binders (`<rule>?`/`<cond>?`, and any `<name>?` head) are excluded — they are `is_bound_literal`,
    not `is_var`. That exclusion is DELIBERATE and is the supported minting path: a bound-literal head skolem
    anchored to LHS-bound endpoints IS genuine value invention (a skolem FUNCTION of the match), minted once
    per firing forward and re-found by its defining relation on demand (`chain._resolve_skolems`). Only the
    unanchored `?x` — a node from nowhere — is unsound and rejected."""
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
class Distinct:
    """A DISTINCTNESS condition on two LHS-bound variables (pystrider feedback #11): the condition
    holds iff `var_a` and `var_b` are bound to provably DIFFERENT nodes — the inequality the join
    language cannot otherwise express (the default topological join can only require SAMENESS, by
    reusing a variable). This is what makes the disjointness family of constraints ("no two DISTINCT
    S share an O" — a frame rule, `functional`/`injective`) writable as one rule instead of O(n²)
    hand-authored `distinct_from` facts.

    Like `ValueMatch` it is a DECLARED condition as DATA, executed by the one `DISTINCT` op both
    engines run (forward lowers to it; the demand chain runs it as an ephemeral program). Semantics:
    the two registers' DENOTATIONS must be DISJOINT — the same node (or a name-pointer overlapping
    the other side's node) is NOT distinct, so a self-join `?a writes ?c and ?b writes ?c` stops
    producing the ?a==?b false positive. Node IDENTITY only: two nodes coref'd by `same_as` rules
    still count as distinct here (identity-as-rules is bank data the engine does not consult).
    CNL surface: a machine-rule body clause `?a != ?b` lifts to this condition at load."""
    var_a: str
    var_b: str


@dataclass
class ValueMatch:
    """A value-EQUALITY (or graded 'close-enough') LHS condition joining TWO bound variables by an
    ATTRIBUTE VALUE — the substrate's first DECLARED value-join, added deliberately beside the default
    topological join (`docs/attic/coreference_as_rules_design.md`).

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


@dataclass(frozen=True)
class Band:
    """A declared RHS EFFECT: set a GRADED attribute on an RHS node to a fixed degree, and
    (optionally) tag other RHS-minted relations as belonging to it.

    THE GAP IT CLOSES. A rule RHS is a conjunction of `Pat` TRIPLES, so it can mint relations but has
    no way to write an ATTRIBUTE with a numeric degree. That made one whole representation
    unreachable from rules: a possibilistic FORK is a `<hypothesis>` scope carrying a graded
    `<likeliness>` band (`possibility._new_fork_scope`), so authoring a hedged fact — "the lion
    GENERALLY has a mane" — could only ever be done by a Python driver. This is the declared-data
    counterpart, in the same family as `GradedCondition` / `ValueMatch` / `Distinct`: rule
    expressiveness grows by adding a DECLARED structure the lowering executes, never by sniffing a
    Pat's shape (a numeric-looking object token stays an ordinary node literal).

    `scope` (optional): the RHS tokens whose minted relations are written in PENCIL behind this
    scope — the `<scope>` VALUED tag `suppose._pencil` writes by hand. Those relations become
    scope-visible rather than ink, which is the point: a hedged claim must NOT be a certain fact.

    A `<…>`-named bound-literal skolem already mints `{name: valued(n), n: graded(1.0)}`, so
    `Band(var="<hypothesis>?", key="<likeliness>", degree=0.7)` completes exactly the three-attribute
    shape `_new_fork_scope` builds.

    IDEMPOTENT ACROSS RUNS — but only because it is minted FIND-OR-CREATE, and that took a new
    mechanism. A bound-literal skolem mints FRESH PER FIRING, so the first version re-minted the
    scope every pass: 5 -> 6 -> 7 -> 8 nodes over four runs of the same bank on an unchanged graph.
    It was SILENT, because the penned HEAD dedups (`MINT(dedup=True)`) so the fork count stayed right
    and every band reader still answered correctly — the FIFTH member of the family that has bitten
    `<span>?`, the remint mark, `intern_described` and `<contradiction>?`. It mattered here because
    the grammar FOLD re-runs its banks over the whole graph on every utterance, so it would have
    reintroduced exactly the accretion the step-4 optimization arc removed.

    A scope has NEITHER existing identity — no NAME to intern by, no subject/object edges to dedup
    on — which is why `MINT` gained `reuse_attr_of`: the scope's identity is the `<scope>` tag its
    own penned fact already carries, so a found head yields a found scope. Pinned by
    `test_a_band_is_idempotent_across_runs` (re-break verified).

    GENERALIZED 2026-07-20: THE DEGREE IS AN OPTIONAL DECORATION ON "PEN THESE HEADS BEHIND THIS
    NODE". The core effect is the SCOPE — mint a node and write the named RHS relations in pencil
    behind it. A graded attribute is one thing you may then say ABOUT that node, and it is what a
    possibilistic fork happens to need; it is not what makes the primitive.

    Attribution is the second user and is why this was generalized before it landed: *some
    naturalists consider the lion a cat* needs the same pencil scope MINUS the degree, plus an
    ordinary `held_by` triple the RHS can already write. Leaving `key`/`degree` mandatory would have
    forced attribution to invent a meaningless degree — and a fabricated 0.5 is exactly the "silent
    default" the hedge path refuses to make. With both omitted this pens without grading, which is
    the general case; `possibility` remains the decorated one.

    (The name stays `Band` deliberately. Renaming to `Scope` is SURFACE — churn across the lowering,
    the grammar and the tests for no change in what any rule can express. The mandatory graded key
    was the real entrenchment, and that is what came off.)"""
    var: str                          # RHS token naming the node (a skolem, or an LHS-bound var)
    scope: tuple[str, ...] = ()       # RHS subject tokens whose relations are penned behind `var`
    key: str | None = None            # graded attribute key, e.g. `<likeliness>` — OPTIONAL
    degree: float | None = None       # its degree; omit BOTH to pen without grading


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
    probability: float = 1.0                            # prior; flows into derived confidence
    graded: list[GradedCondition] = field(default_factory=list)
    value_matches: list[ValueMatch] = field(default_factory=list)   # declared value-JOIN conditions
                                                        # (`ValueMatch`): the coreference-as-rules enabler.
    distinct: list[Distinct] = field(default_factory=list)          # declared DISTINCTNESS conditions
                                                        # (`Distinct`, feedback #11): two LHS-bound vars
                                                        # must bind provably different nodes (`?a != ?b`).
    bands: list[Band] = field(default_factory=list)     # declared RHS EFFECTS (`Band`): write a graded
                                                        # attribute at a fixed degree, and optionally pen
                                                        # RHS relations behind it as a scope. The
                                                        # fork-authoring primitive — the one representation
                                                        # a triple-only RHS could not reach.
    propagate: dict | None = None                       # e.g. {"op": "weighted_sum", "weights": [...]}
    priority: float = 0.0                               # provisional scheduling tie-break
    max_steps: int = 5
    meta: bool = False                                  # META/TMS rule: fires PROVENANCE-SILENT even in a
                                                        # prov-on run (the regress guard — a meta-rule that
                                                        # names proves/uses would else re-match its own <j:>).
                                                        # Lets reasoning + TMS rules share ONE run().
    learned: bool = False                               # DECLARED role: this rule was LEARNED, not
                                                        # authored (docs/design/learning_design.md
                                                        # §6.1a). Read by `learned.learned_support`
                                                        # so a conclusion standing on it can be
                                                        # rendered wearing its kind. Carried through
                                                        # the flat schema as `rl_learned`. NOT a
                                                        # confidence: `Rule.probability` below is a
                                                        # dead field (nothing in the package reads
                                                        # it), and provisionality is answered from
                                                        # PROVENANCE at query time, not stored.
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
# Mint keys — what a skolem head is a FUNCTION of (feedback #21, a diagnostic)
# ---------------------------------------------------------------------------
# A bound-literal skolem head (`n?`) mints one node per LHS MATCH, so its arity is the rule's whole
# positive body — not its head. Nothing in a rule's TEXT shows that, and a body atom added for an
# unrelated reason silently multiplies the mint:
#
#     n? is_a made and n? of ?x when ?x is_a thing                   -> one node per (?x)
#     n? is_a made and n? of ?x when ?x is_a thing and ?x tag ?y     -> one node per (?x, ?y)
#
# `?y` is in no head atom and is used for nothing; it still multiplies. The duplicates are then
# interchangeable (the head names no `?y`), so nothing fails — the emitted result is correct while
# the graph is quietly wrong, and a later rule that DOES mention `?y` turns nondeterministic.
# This is reporting only: the semantics are correct and deliberately unchanged.


@dataclass(frozen=True)
class MintKey:
    """What one skolem head mints, and per what. `key` is the tuple of LHS-bound variables the mint
    is a function of, in first-appearance order. `unused_in_head` are those key variables that
    appear in NO head atom — a variable that can only multiply the mint, never distinguish its
    results.

    `unused_in_head` is REPORTED, never warned on, because it does not separate the accidental case
    from the ANCHOR IDIOM: a body variable binding the sentence/statement a mint belongs to is
    deliberately absent from the head, and ugm's own recognition banks use it 24 times
    (`RULE_FORMS`, `QUESTION_FORMS`, `MACHINE_RULE_FORMS`). So it is a thing worth SEEING when you
    go looking, not a signal worth interrupting on."""
    rule: str
    head: str                          # the skolem token, e.g. 'n?'
    key: tuple[str, ...]
    unused_in_head: tuple[str, ...]

    def describe(self) -> str:
        per = f"({', '.join(self.key)})" if self.key else "firing"
        line = f"rule {self.rule!r}: mints `{self.head}` — one node per {per}"
        if self.unused_in_head:
            names = ", ".join(self.unused_in_head)
            line += (f"   [{names} appear{'s' if len(self.unused_in_head) == 1 else ''} in no head "
                     f"atom — multiplies the mint without distinguishing it]")
        return line


def mint_keys(rule: Rule) -> list[MintKey]:
    """The skolem heads `rule` mints, and what each is keyed on. Empty for a rule that mints nothing.

    A skolem head is a bound-literal token (`n?`) in a head ENDPOINT slot that appears nowhere in
    the body — the runtime twin of `chain._head_skolems`, which decides the same question over
    lowered triples rather than `Pat`s. An RHS-only VARIABLE is not a skolem (it is unsound and
    rejected at authoring by `reject_rhs_only_head_vars`); a plain RHS literal is not one either
    (it interns to its graph-wide node)."""
    body_toks = {t for pats in (rule.lhs, rule.nac) for pat in pats for t in pat.tokens()}
    heads = [t for pat in rule.rhs for t in (pat.s, pat.o)
             if is_bound_literal(t) and t not in body_toks]
    if not heads:
        return []

    key: list[str] = []                        # LHS variables, first-appearance order (the match)
    for pat in rule.lhs:
        for tok in pat.tokens():
            if is_var(tok) and tok not in key:
                key.append(tok)
    head_toks = {t for pat in rule.rhs for t in pat.tokens()}
    unused = tuple(v for v in key if v not in head_toks)

    out: list[MintKey] = []
    for h in dict.fromkeys(heads):             # dedupe, preserve order
        out.append(MintKey(rule=rule.key, head=h, key=tuple(key), unused_in_head=unused))
    return out


def describe_rules(rules: list[Rule]) -> list[str]:
    """One human-readable line per skolem head across `rules` — the authoring-time answer to
    'what is this mint a function of?'. Rules that mint nothing produce no line."""
    return [mk.describe() for rule in rules for mk in mint_keys(rule)]


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


# ---------------------------------------------------------------------------
# Stratification — a STATIC property of a rule bank (Datalog stratified negation)
# ---------------------------------------------------------------------------
# Lives here, next to `Rule`, rather than in the CNL authoring layer: it is pure rule analysis
# (no graph, no surface), and the forward driver `lowering.run_bank` must be able to call it
# WITHOUT importing the CNL layer — recognition banks are built and run at import time, so an
# upward import would be circular (feedback #18).

_WILD = object()   # sentinel: a producer with a variable object (a wildcard for any NAC on its pred)


def _prod_key(pat: Pat):
    """The producer key a head pattern registers: `(pred, obj)`, or `(pred, _WILD)` for a variable
    object. Uniform over all predicates — no relation name is special-cased."""
    return (pat.p, _WILD if is_var(pat.o) else literal_name(pat.o))


def stratify(rules: list[Rule]) -> list[list[Rule]]:
    """Partition `rules` into strata so a rule's NAC is evaluated only AFTER every
    rule that could PRODUCE the negated predicate has reached fixpoint.

    This is Datalog's stratified negation (vision §11), the static-analysis cure for
    the order-dependence of NAC over a *derived* fact (e.g. `serve_regular`'s
    `is not urgent` must see the `mark`-derived `is urgent`). Positive dependencies
    need no stratum — same-stratum forward chaining resolves them. Keyed OBJECT-AWARE on
    `(pred, literal-obj)` (`_prod_key`) — uniformly, no relation name special-cased — so `P young`
    and `P rough` don't falsely cycle. Sound (it only ever delays, never reorders wrongly). Raises
    if negation is cyclic. The scheduler stays dumb (vision §6): within a stratum every rule fires.
    """
    producers: dict = {}
    for i, r in enumerate(rules):
        for pat in r.rhs:                                # EVERY head atom produces (a multi-head
            producers.setdefault(_prod_key(pat), set()).add(i)   # skolem rule produces all of them)

    def deps_of(pat: Pat) -> set[int]:
        """The rules that could PRODUCE a fact matching this body/NAC atom."""
        if is_var(pat.o):                                # variable object: any producer of the pred
            return set().union(*(v for k, v in producers.items() if k[0] == pat.p), set())
        return (producers.get((pat.p, literal_name(pat.o)), set())
                | producers.get((pat.p, _WILD), set()))

    # Dependency edges i -> (j, negated): rule j must reach fixpoint BEFORE i is decided —
    # at the SAME stratum for a positive premise, a STRICTLY EARLIER one for a negated premise.
    edges: list[list[tuple[int, bool]]] = []
    for i, r in enumerate(rules):
        e: set[tuple[int, bool]] = set()
        for pat in r.lhs:
            e |= {(j, False) for j in deps_of(pat) if j != i}   # positive: same-or-earlier
        for pat in r.nac:
            e |= {(j, True) for j in deps_of(pat) if j != i}    # negated: strictly earlier
        edges.append(sorted(e))

    # Longest-path relaxation (a bank is tens of rules; this is simpler than condensing SCCs and
    # handles positive RECURSION naturally — a positive cycle relaxes to one shared stratum, while a
    # cycle through a NEGATED edge grows without bound and is caught by the round cap).
    strata_of = [0] * len(rules)
    for _round in range(len(rules) + 1):
        changed = False
        for i, e in enumerate(edges):
            want = max((strata_of[j] + (1 if neg else 0) for j, neg in e), default=0)
            if want > strata_of[i]:
                strata_of[i] = want
                changed = True
        if not changed:
            break
    else:
        # No fixpoint: a dependency cycle passes through a NEGATED edge. Strict Datalog calls that
        # unstratifiable, but ugm banks legitimately contain them (a recursively-derived predicate
        # that is also negated somewhere), and the engines cope — the demand chain has its own NAF
        # cycle guard, and the forward path has run them flat for as long as they have existed. So do
        # NOT newly reject them here: fall back to the historical NAC-only ordering, which ignores
        # positive edges and therefore cannot diverge on a positive cycle. Every bank that worked keeps
        # working, while a bank WITHOUT such a cycle gets the positive-dependency ordering above (which
        # is what stops a producer being scheduled after its consumer).
        return _stratify_nac_only(rules, deps_of)

    layers: dict[int, list[Rule]] = {}
    for i, s in enumerate(strata_of):
        layers.setdefault(s, []).append(rules[i])
    return [layers[s] for s in sorted(layers)]


def _stratify_nac_only(rules: list[Rule], deps_of) -> list[list[Rule]]:
    """The HISTORICAL stratification: order by NEGATED dependencies only, ignoring positive ones.

    Retained as `stratify`'s fallback for a bank whose dependency graph cycles through a negated edge.
    It cannot diverge, because it never follows a positive edge — which is also precisely its weakness:
    a producer pushed into a later stratum than its positive CONSUMER starves that consumer (the
    consumer reaches fixpoint before the fact it needs exists, and nothing re-runs it). That is why
    `stratify` prefers the sound ordering and only falls back here."""
    memo: dict[int, int] = {}

    def stratum(i: int, stack: tuple[int, ...]) -> int:
        if i in memo:
            return memo[i]
        if i in stack:
            raise ValueError("rules are not stratifiable (negation cycle)")
        deps = set().union(*(deps_of(pat) for pat in rules[i].nac)) if rules[i].nac else set()
        deps.discard(i)                                  # self-NAC (idempotency) is fine
        s = 1 + max((stratum(d, stack + (i,)) for d in deps), default=-1)
        memo[i] = s
        return s

    for i in range(len(rules)):
        stratum(i, ())
    layers: dict[int, list[Rule]] = {}
    for i, s in memo.items():
        layers.setdefault(s, []).append(rules[i])
    return [layers[s] for s in sorted(layers)]
