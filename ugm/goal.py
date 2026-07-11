"""
Goal-directed evaluation — acting toward a goal, NOT forward-rushing to fixpoint.

This is the §6a "Everything is goal-directed" pillar (`decision_labelless_substrate`,
`docs/vision.md` §6a): the driver is **demand-forward** — a rule-head index + magic-sets-style
sideways-information-passing (SIP) + tabling — over the SAME positive, monotone opcode core
(no trail, no NAF). A goal is a partial attribute-node / partial relation, the same shape as a
fact; answering it materializes ONLY the facts the goal demands, in contrast to
`run_to_fixpoint` (which derives the whole closure whether or not the query needs it).

Contrast, concretely: over two disjoint `isa` chains, `run_to_fixpoint` computes the full
transitive closure of BOTH; `GoalSolver.solve(isa, x, w)` answers using only x's chain and
never materializes a fact from the other chain. That is the shift this module realizes.

Scope of this slice: positive relational rules with LITERAL predicates (the fragment
`lowering.py` already lowers), evaluated over the bridged `AttrGraph`. The graded α-cut is
wired in (see `_graded_degree`).

**Identity is NODE-LEVEL, not name-level** (decision-labelless-substrate; the coref-probe
finding). The solver's identity currency is a TOKEN, not a raw name: a name is only an
accelerator. A UNIQUE-named node's token IS its name (so a name-canonicalized / distinct-entity
KB is unchanged — token == name everywhere), but a name borne by SEVERAL nodes (coref MENTIONS,
the additive-`same_as` path) is split by `same_as` EQUIVALENCE CLASS — mentions LINKED by
`same_as` share a token (their facts compose), UNLINKED same-named nodes get different tokens and
stay distinct (two Pauls). Whether `same_as` is FOLLOWED at the read boundary is GATED by the bank
(`_follow_coref`, `__init__`): a bank that carries the `same_as` propagation rules DECLARES coref —
the solver then follows the class (the union-find is those rules' fast evaluation, and they are
dropped as subsumed); a bank without them (recognition / the graded surface-chain pass) is coref-
BLIND (each node its own identity), so a non-unique surface token is matched STRUCTURALLY. A rule LITERAL is a concept
reference by NAME (matches any class); a bound VARIABLE is identity by token (`_endpoint_matches`).
The name<->token boundary is `_entry_tokens` (top goal in) and `_render` (answers out).

**Negation is NAC → materialized-positive completion (the `decide` line, on the goal path).**
A rule's NAC on an ARBITRARY relation — `H :- BODY, not ?s R o` — is not a CHECK-ABSENT filter;
it is rewritten (`_lower_nac`) into a POSITIVE body clause `?s R_not o`, and the negative is
produced by a single demand-driven COMPLETION step (`_complete_negative`): to answer a demanded
`R_not(c, P)`, solve the positive `R(c, P)` to COMPLETION (a self-contained nested solve), and
materialize `c R_not P` iff the positive has no answer. The copula NAC (`not ?c is P` -> `is_not`)
is just this scheme with `R = is`; the card trader's marker NACs (`not ?act overridden <yes>`,
`not ?o stance encouraged`, `not ?o dominated <yes>`) lower the same way. The matching core thus
stays PURELY POSITIVE (no NAF opcode) — negation lives at ONE producer, matched positively
everywhere else (memory `decision_forcing_a_decision`, `harneskills/decide.py`). This is SOUND for
STRATIFIED negation: the nested solve computes the positive's complete extension independently of
the outer round, so a completed negative is final (a positive that later coexists DEFEATS the
default — here directly: if `R(c, P)` is derivable the completion yields nothing, so the default
rule does not fire) — the goal-directed analog of stratifying the producer below the consumer. A
negative cycle (non-stratifiable) is DETECTED and rejected, not silently mis-answered.

**Existential NACs (¬∃) — the planner's ground shape (Phase 2).** A NAC clause that introduces a
NAC-LOCAL FREE variable — a variable OBJECT (`not ?o blocked_by ?anyp`, ¬∃p) or a free SUBJECT
shared across clauses (`not ?x chosen <yes> and not ?x add ?c`, ¬∃x) — cannot lower to a ground
`R_not` fact (there is no single negative to materialize). It is grouped by shared free var
(`_nac_groups_free`, the forward engine's `not (A and B)` vs `not A and not B` partition) and
applied as a demand-driven EMPTINESS check per env (`_exist_nac_blocks`/`_group_satisfiable`): the
head fires iff the group has NO witness, the group solved to completion in a nested solve. This is
what makes the planner's block/unblock idiom lower goal-directed: `viable(o) :- candidate(o),
¬∃p blocked_by(o, p)` computes `blocked_by` against COMPLETE reachability, so it never asserts a
stale block — the forward engine's `drop ?o blocked_by ?p` (control retraction / `DROP_CTRL`) is
SUBSUMED, not needed. Out of slice, rejected (never silent): a SELECTION rule whose existential NAC
references the rule's OWN head (`?o chosen <yes> when … not ?x chosen …`) — a non-stratified choice
the forward engine resolves by commit-order, deferred to the operational planner (Phase 3).

The evaluator is tabled (a global least-fixpoint over the demanded goals only), so recursive
rules (transitivity) terminate.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from .production_rule import Pat, Rule, binder, is_bound_literal, is_var, literal_name
from .attrgraph import AttrGraph, GRADED, valued, _is_inert
from .lowering import derived_triples
from .walker import Walker


COPULA = "is"            # positive copula predicate: P(c) == c is P
NEG_COPULA = "is_not"    # the materialized negative copula, matched positively (the decide line)
NEG_SUFFIX = "_not"      # a NAC on `?s R o` materializes the negative predicate `R_not`


def _neg_pred(pos: str) -> str:
    """The materialized-negative predicate name for a positive relation `pos`. The copula
    `is` -> `is_not` is just this convention with `R = is`, so the general scheme subsumes the
    copula one; the reverse (strip the suffix) is the positive it completes against."""
    return pos + NEG_SUFFIX


class NonStratifiable(Exception):
    """A NAC could not be lowered to demand-driven completion within the stratified fragment
    (a negated VARIABLE object/predicate, a NAC subject the positive body never binds, or a
    detected negative cycle). Raised explicitly rather than silently mis-answering — negation is
    stratified-only by design."""


# A goal / subgoal: a partial relation. `subj`/`obj` are a concrete node name or None (= any).
@dataclass(frozen=True)
class Goal:
    rel: str
    subj: str | None = None
    obj: str | None = None


def _closure_declarations(ag: AttrGraph) -> dict[str, str]:
    """Map each relation the KB DECLARES a transitive closure -> the BASE relation to walk for a
    ground reachability goal on it (Phase 5.4 — the walker strategy is DECLARED DATA read from the
    substrate, NOT reverse-engineered from rule shape; `feedback-no-hardcoded-engine-policy`). Two
    declaration forms, both recognized into ordinary facts and read here like any other:

      `R is transitive`                    ->  {R: R}   the SAME-relation closure `R(a,c):-R(a,b),R(b,c)`.
                                                        Recognized (`RELATION_PROPERTY_FORMS`) into the
                                                        CANONICAL `R -[rel_property]-> transitive` fact — the
                                                        SAME declaration that generates the transitivity RULE
                                                        (`rule_graph.expand_relation_properties`); it now does
                                                        double duty, also declaring the walker's base.
      `D is the transitive closure of B`   ->  {D: B}   linear recursion over a DIFFERENT base (`D:-B`,
                                                        `D:-B,D`): walk `B`'s edges, mint the shortcut as `D`
                                                        (a `D -[transitive_closure_of]-> B` fact).

    A ground reachability goal on a declared key is then carried by a fuel-bounded walker over the
    mapped base (`GoalSolver._walk_goal`). The bank AUTHOR asserts the closure (which is knowledge
    about the relation), so the engine stays content-blind — it only reads the map."""
    from .cnl.rule_graph import PROPERTY_REL                   # late import: avoid a load-time cycle
    out: dict[str, str] = {}
    for r in ag.nodes_with_key(PROPERTY_REL):                   # `R is transitive` -> {R: R}
        subj = next((n for n in ag.into(r) if not ag.is_inert(n)), None)
        obj = next((n for n in ag.out(r) if not ag.is_inert(n)), None)
        if subj is not None and obj is not None and ag.name(obj) == "transitive":
            out[ag.name(subj)] = ag.name(subj)
    for r in ag.nodes_with_key("transitive_closure_of"):       # `D is the transitive closure of B` -> {D: B}
        subj = next((n for n in ag.into(r) if not ag.is_inert(n)), None)
        obj = next((n for n in ag.out(r) if not ag.is_inert(n)), None)
        if subj is not None and obj is not None:
            out[ag.name(subj)] = ag.name(obj)
    return out


def _nac_groups_free(nac: list[Pat], lhs_vars: set[str]) -> list[list[Pat]]:
    """Partition existential NAC clauses into INDEPENDENT groups connected by a shared NAC-local
    free variable (a binder not in `lhs_vars`). This is the goal-path twin of the forward engine's
    `rewriter._nac_groups`: two clauses sharing a free var are ONE existential conjunction
    (`not ?x chosen and not ?x add ?c` = "no ?x that is BOTH chosen AND adds ?c"); two clauses
    with no shared free var are SEPARATE negations (each blocks independently)."""
    def free(pat: Pat) -> set[str]:
        return {b for t in pat.tokens() if (b := binder(t)) is not None and b not in lhs_vars}

    groups: list[tuple[set[str], list[Pat]]] = []
    for pat in nac:
        fv = free(pat)
        cur_vars, cur_pats = set(fv), [pat]
        merged: list[tuple[set[str], list[Pat]]] = []
        for gv, gp in groups:
            if fv and gv & fv:
                cur_vars |= gv
                cur_pats = gp + cur_pats
            else:
                merged.append((gv, gp))
        merged.append((cur_vars, cur_pats))
        groups = merged
    return [pats for _, pats in groups]


class GoalSolver:
    """A demand-driven, tabled evaluator over `rules` and the label-less `ag`. Materializes
    derived facts into `ag` as it proves them; `derived` counts the facts it minted (the metric
    that shows it did less work than a full fixpoint)."""

    def __init__(self, ag: AttrGraph, rules: list[Rule], *, walk_fuel: int | None = None,
                 tools: dict | None = None, provenance: bool = False,
                 control_completions: bool = False,
                 closures: dict[str, str] | None = None,
                 _completing: frozenset[Goal] = frozenset(),
                 _follow_coref: bool | None = None,
                 _neg_of: dict[str, str] | None = None,
                 _exist_nac: dict[str, list[list[Pat]]] | None = None,
                 _serviced: set[str] | None = None,
                 _materialized: set[tuple[str, str, str]] | None = None,
                 _justified: set[tuple[str, str]] | None = None,
                 _skolem: dict | None = None,
                 _name_ids: dict[str, str] | None = None,
                 _sa_parent: dict[str, str] | None = None,
                 _tok_cache: dict[str, str] | None = None,
                 _token_class: dict[str, list[str]] | None = None,
                 _group_sat_cache: dict[tuple, tuple[int, bool]] | None = None) -> None:
        self.ag = ag
        # provenance: when True, MINT an in-graph justification (`<j:rulekey>` + `proves`/`uses`
        # edges, `provenance.py`) each time a rule materializes a head — the SAME substrate trace
        # `rewriter.run` writes, so `surface.explain` / `why` reads the backward engine's derivations
        # (the re-host's provenance-MINT parity, decision-attrgraph-rehost work-item 3). Default off:
        # answering usually does not need the trace, and the J-nodes cost writes; the `why`/`decide`-
        # retirement path turns it on. Nested solvers inherit it so a fact first minted in a nested
        # completion is justified too.
        self.provenance = provenance
        # control_completions: when True, a NAC negative this solver materializes (`_complete_negative`)
        # is marked CONTROL-layer, so it is invisible to fact matching and can never pollute reasoning.
        # This is what a RECOGNITION solve passes: running the FORM rules through this forward driver
        # lowers their guard NACs to demand-completions (`is_kw_not`, `kw_not_not`, …) whose negatives
        # are pure surface scaffolding — the forward `rewriter` never materialized them at all (its NAC
        # is a match-time check), so demoting them to control restores that invisibility. A REASONING
        # solve leaves it False: there `is_not P`/`overridden_not …` are real facts consumers match
        # positively (the `decide` line). Nested solvers inherit it so a completion demanded inside a
        # recognition run is demoted too. (decision-attrgraph-rehost, item #3.)
        self.control_completions = control_completions
        # _materialized (shared across nested solvers) is a fast-path memo of reified relations
        # already written to the monotone `ag`: a repeat `_materialize` is then an O(1) set hit
        # instead of an O(degree) graph re-check. The naive fixpoint re-derives every answer each
        # round, so this is the difference between O(1) and a graph traversal per re-derivation.
        # Pure/safe: the graph is monotone (goal path never deletes), so a triple once present
        # stays present; the graph existence check remains the correctness backstop on a memo miss.
        self._materialized: set[tuple[str, str, str]] = set() if _materialized is None else _materialized
        self._rel_node: dict[tuple[str, str, str], str] = {}   # (s,rel,o) -> its reified relation node
        # _group_sat_cache (shared across nested solvers, like `_materialized`) memoizes
        # `_group_satisfiable`: an existential-NAC group re-checked against the same relevant
        # bindings today re-runs a whole fresh nested `GoalSolver` from scratch (Phase 1.2). Keyed by
        # (group identity, the env restricted to vars the group actually references) so unrelated
        # outer bindings don't fragment the cache; a cached entry is valid only while `len(self.
        # _materialized)` — a cheap monotonic proxy for "has anything new been derived anywhere,
        # including by a nested solve" — hasn't grown since it was recorded, so a group that was
        # UNSATISFIABLE before a later derivation is never served stale (correctness over hit-rate).
        self._group_sat_cache: dict[tuple, tuple[int, bool]] = (
            {} if _group_sat_cache is None else _group_sat_cache)
        # (head_node, rule.key) already justified -> emit ONE <j:> per (fact, rule) despite semi-naive
        # re-derivation across rounds / nested re-solves (a fact CAN carry several Js from diff rules).
        self._justified: set[tuple[str, str]] = set() if _justified is None else _justified
        # SKOLEM / value-invention (the recognition-parity gap): a `<...>?` head token is a FRESH node
        # per FIRING (rewriter.apply_rule's `fresh` dict; the ISA `MINT`). Keyed by (rule, token, env)
        # so a rule's several RHS clauses share ONE fresh node in a firing, distinct firings get distinct
        # nodes, and re-derivation (semi-naive / nested) is IDEMPOTENT. Shared across nested solvers.
        self._skolem: dict = {} if _skolem is None else _skolem
        # tools maps a TOOL-BACKED relation name -> a calculator `f(ag)` that materializes its
        # facts (the §8 `<call>` boundary, demand-driven: when a subgoal on that relation is first
        # demanded, the calculator runs ONCE and the demand then reads the facts it minted). This is
        # how a comparison/aggregation gadget the positive core can't express — `cheaper_than` from a
        # cost `rank`, a `count` — folds into demand-forward evaluation without a `<call>` rule.
        # `_serviced` (shared across nested solvers) records which tools have already fired.
        self.tools: dict = tools or {}
        self._serviced: set[str] = set() if _serviced is None else _serviced
        # _exist_nac maps a rule key -> its EXISTENTIAL NAC groups (¬∃ over a shared NAC-local free
        # var). These are NOT lowered to a positive body clause (there is no single ground negative
        # to materialize); they are demand-driven emptiness checks applied per env in `_join_body`.
        # A top-level solver BUILDS it while lowering NACs; a nested solver is HANDED it (its rules
        # are already lowered, so re-running `_lower_nac` would find no NACs to partition).
        self._exist_nac: dict[str, list[list[Pat]]] = {} if _exist_nac is None else _exist_nac
        # _neg_of maps each materialized-negative predicate -> the positive it completes against
        # (`is_not` -> `is`, `overridden_not` -> `overridden`, …). A top-level solver BUILDS it by
        # lowering NACs; a nested completion solver (which receives ALREADY-lowered rules, so their
        # NACs are gone) is HANDED the map so it still recognizes negative subgoals downstream.
        if _neg_of is None:
            self._neg_of: dict[str, str] = {}
            # GATED coref-following — DATA-DRIVEN, not a hardcoded engine policy (user directive
            # 2026-07-07; decision-labelless-substrate). Whether the engine FOLLOWS `same_as` as
            # identity is DECLARED by the bank: a bank that carries the `same_as` propagation rules
            # (`universal.same_as_rules` — the DATA meaning "compose facts across coref links") turns
            # coref-following ON. The engine then evaluates that composition via the fast union-find
            # (`_token` reads a whole `same_as` class) and DROPS the rules themselves (subsumed — the
            # union-find is their optimized evaluation, not extra Herbrand saturation). A bank WITHOUT
            # them — RECOGNITION / the graded surface-chain pass — is coref-BLIND: each node is its own
            # identity, so a NON-UNIQUE surface token (`is`/`very`) is matched STRUCTURALLY, node by
            # node, with no class merge (the fix for the graded cross-product). So recognition-vs-
            # reasoning differ by which BANK runs, not by a Python branch. (Perf note: keeping the
            # union-find as the ON-path evaluator is a temporary optimization; making the propagation
            # purely rule-driven + fast is a separate later effort — correctness first.)
            self._follow_coref = any(r.coref_prop for r in rules)
            rules = [r for r in rules if not r.coref_prop]
            self.rules = [self._lower_nac(r) for r in rules]   # NAC -> positive `R_not` body clauses
        else:
            self._neg_of = _neg_of
            self._follow_coref = bool(_follow_coref)            # inherited (parent's rules already lowered)
            self.rules = rules                                  # already lowered by the parent
        self._completing = _completing                   # negative goals being completed up-stack (cycle guard)
        self._neg_cache: dict[Goal, set[tuple[str, str]]] = {}
        # rule-head index: head relation name -> [(rule, head_pat)] (literal-predicate heads).
        self.head_index: dict[str, list[tuple[Rule, Pat]]] = {}
        for r in self.rules:
            for hp in r.rhs:
                if not is_var(hp.p):
                    self.head_index.setdefault(literal_name(hp.p), []).append((r, hp))
        self.tables: dict[Goal, set[tuple[str, str]]] = {}   # demanded goal -> answer (s,o) pairs
        self.degree: dict[tuple[str, str, str], float] = {}  # derived (rel,s,o) -> graded degree
        self.derived = 0
        # Semi-naive delta evaluation (the honest-gate parity win 2). A goal is joined in FULL
        # exactly once — its first evaluation, which seeds from whatever its subgoals hold — and
        # thereafter only against the previous round's DELTA (facts newly added anywhere), so a
        # round no longer re-joins the whole body to rediscover facts it already found. See `solve`.
        self._full_joined: set[Goal] = set()                 # goals whose seeding full join ran
        self._delta_by_rel: dict[str, set[tuple[str, str]]] = {}   # last round's new facts, by rel
        self.full_joins = 0                                  # count of FULL body joins (semi-naive
        #   pins this at <= one per demanded goal; a naive fixpoint re-joins every round)
        self.walked = 0                                      # ground reachability goals sent to a walker
        # Long-range demand: relations with a transitive-closure rule. A GROUND reachability
        # goal on one of these is answered by a fuel-bounded WALKER (bounded effort, materializes
        # a shortcut) instead of tabling the whole chain — the walker-as-demand integration
        # (decision_walkers_locality, vision §6a). `walk_fuel=None` disables it (pure tabling).
        self.walk_fuel = walk_fuel
        # derived relation -> base relation to WALK for a ground reachability goal on it (the
        # relation itself for same-relation transitive closure, a DIFFERENT base for linear
        # recursion `D:-B` / `D:-B,D`). A walkable ground goal — top-level OR an interior subgoal
        # — is carried by a fuel-bounded walker (`_walk_goal`) instead of tabling the chain. The
        # map is DECLARED DATA read from the substrate (`_closure_declarations`, Phase 5.4), not
        # sniffed from rule shape; a nested solver is HANDED the parent's map so it isn't re-read.
        self._closure_base: dict[str, str] = (
            _closure_declarations(self.ag) if closures is None else closures)
        self._walked_goals: set[Goal] = set()                # ground goals already sent to a walker
        # NODE-LEVEL IDENTITY (decision-labelless-substrate; the coref-probe finding). The solver's
        # identity currency is a TOKEN, not a raw name: a name is only an accelerator. When a name is
        # borne by ONE node the token IS the name (so a name-canonicalized KB — every load_corpus /
        # unique-name bank — is byte-for-byte unchanged, token == name everywhere). When a name is
        # borne by SEVERAL nodes (coref MENTIONS, the additive-`same_as` Session path), each `same_as`
        # EQUIVALENCE CLASS gets its own token `name\x00rep`, so two mentions LINKED by `same_as`
        # share a token (their facts compose) while two UNLINKED same-named nodes (two distinct Pauls)
        # get different tokens and stay separate — selective coreference, the label-less-faithful
        # semantics. `same_as` is FOLLOWED at the read boundary (`_facts_matching` reads a whole class)
        # ONLY WHEN the bank declares coref (`_follow_coref`); the union-find is then the propagation
        # rules' fast evaluation. Coref-blind (no such rules) -> the class rep is the NODE, so no merge.
        # SHARED across nested solvers (like `_materialized`/`_justified`/`_skolem` above): a nested
        # completion (`_group_satisfiable`, `_complete_negative`) can itself derive a `same_as` mid-solve
        # (`_materialize` unions it), and the outer solver must see that union and its token/class
        # updates immediately — a private per-nested-instance copy would go stale the moment the
        # nested frame returns (Phase 1.1, `finding`/`decision_cwa_default` staleness note).
        fresh_identity = _sa_parent is None
        self._name_ids: dict[str, str] = {} if _name_ids is None else _name_ids
        self._sa_parent: dict[str, str] = {} if _sa_parent is None else _sa_parent
        self._tok_cache: dict[str, str] = {} if _tok_cache is None else _tok_cache
        self._token_class: dict[str, list[str]] = {} if _token_class is None else _token_class
        if fresh_identity:
            for nid in ag.nodes():
                nm = ag.name(nid)                 # VALUED entity name only (Phase 2.3: skips a graded
                if nm:                            # `name`-predicate rel node, which reports "")
                    self._name_ids.setdefault(nm, nid)
            for r in ag.nodes_with_key("same_as"):  # Phase 2.1: predicate key, not name
                subs, objs = list(ag.pred(r)), list(ag.succ(r))
                for s in subs:
                    for o in objs:
                        self._sa_union(s, o)
            # `_token_class` is NOT warmed here: it is a pure CACHE of `_nodes_of_token`'s scan, safe
            # to build lazily on first read (see `_nodes_of_token`) — eagerly touching every node
            # would just recompute the same lazy result up front for no benefit.

    def _lower_nac(self, rule: Rule) -> Rule:
        """Lower a rule's NAC. Each clause is classified by whether it introduces a NAC-LOCAL FREE
        variable (a binder the positive LHS does not bind), which splits into two mechanisms:

        GROUND NAC (no free var) — a LITERAL predicate, a LITERAL/ground object, and a subject the
        LHS binds. Rewritten (the decide line) into a positive `R_not` body clause appended AFTER
        the positive LHS: `not ?c is P` -> `?c is_not P`, `not ?act overridden <yes>` ->
        `?act overridden_not <yes>` (the copula being `R = is`). `self._neg_of[R_not] = R` is
        recorded; the ground negative is produced by `_complete_negative` (nested-complete-solve).

        EXISTENTIAL NAC (has a NAC-local free var) — the ¬∃ shapes the planner uses: a variable
        OBJECT (`not ?o blocked_by ?anyp`, ¬∃p) or a free SUBJECT shared across clauses
        (`not ?x chosen <yes> and not ?x add ?c`, ¬∃x). These CANNOT lower to a per-clause `R_not`
        fact (there is no single ground negative to materialize — the negative is "no witness
        exists"). They are grouped by shared free var (`_nac_groups`, exactly the forward engine's
        partition of `not (A and B)` vs `not A and not B`) and stored in `self._exist_nac[key]`;
        `_join_body` applies each group as a demand-driven EMPTINESS check per env.

        Out of slice, rejected (raise `NonStratifiable`, never silent): a variable PREDICATE; a
        SELECTION rule — an existential NAC group that references the rule's OWN head relation
        (`?o chosen <yes> when … not ?x chosen …`), which is a non-stratified choice (the forward
        engine resolves it by commit-order, not by completion) and belongs to the operational
        planner (Phase 3), not to monotone completion. Idempotent: a rule with no NAC returns
        unchanged (a nested solver's rules are already lowered)."""
        if not rule.nac:
            return rule
        lhs_vars = {binder(t) for pat in rule.lhs for t in (pat.s, pat.p, pat.o) if is_var(t)}
        head_preds = {literal_name(h.p) for h in rule.rhs if not is_var(h.p)}
        head_tokens = {h.tokens() for h in rule.rhs}
        ground: list[Pat] = []
        existential: list[Pat] = []
        for n in rule.nac:
            if n.tokens() in head_tokens:
                # A NAC clause IDENTICAL to the head (`is_a(a,c) :- …, not is_a(a,c)`) is a
                # FORWARD-engine idempotency/termination guard — don't re-derive a fact already
                # present. On the tabled goal path re-derivation is a set no-op, so the guard is
                # redundant; worse, lowering it to completion makes the head depend NEGATIVELY on
                # itself (a spurious `NonStratifiable`). Drop it — answer-preserving under tabling.
                continue
            if is_var(n.p):
                raise NonStratifiable(
                    f"{rule.key}: a variable-predicate NAC {n.tokens()} is out of slice")
            free = {b for t in n.tokens() if (b := binder(t)) is not None and b not in lhs_vars}
            if free:                                    # a NAC-local free var -> existential ¬∃
                existential.append(n)
            else:                                       # fully bound -> ground completion
                neg = _neg_pred(literal_name(n.p))
                self._neg_of[neg] = literal_name(n.p)
                ground.append(Pat(n.s, neg, n.o))
        if existential:
            groups = _nac_groups_free(existential, lhs_vars)
            for group in groups:
                for pat in group:
                    if literal_name(pat.p) in head_preds:
                        raise NonStratifiable(
                            f"{rule.key}: an existential NAC on the rule's own head "
                            f"{pat.tokens()} is a SELECTION/choice rule (non-stratified — the "
                            "forward engine resolves it by commit-order); out of slice (Phase 3)")
            self._exist_nac[rule.key] = groups
        return replace(rule, lhs=[*rule.lhs, *ground], nac=[])

    def _walk_applicable(self, goal: Goal) -> bool:
        """A ground reachability goal on a transitive-closure relation (same-relation OR linear
        recursion over a different base) — the long-range case a walker answers boundedly
        (rather than tabling the full chain). Holds for a top-level goal AND an interior subgoal."""
        return (self.walk_fuel is not None and goal.subj is not None and goal.obj is not None
                and goal.rel in self._closure_base)

    def _walk_goal(self, goal: Goal) -> set[tuple[str, str]]:
        """Answer a ground reachability `goal` with a fuel-bounded walker over its closure BASE
        (the goal relation itself for same-relation transitive closure; a DIFFERENT base for
        linear recursion, walked as `B` but materialized as `D`). Walking the base edges IS the
        transitive reachability, so for a relation whose meaning is exactly that closure this is
        complete within fuel — same yes/no as tabling, materializing only the shortcut."""
        self.walked += 1
        base = self._closure_base[goal.rel]
        before = derived_triples(self.ag)
        res = Walker(self.ag, base, mint_rel=goal.rel).walk(goal.subj, goal.obj, self.walk_fuel)
        self.derived += len(derived_triples(self.ag) - before)
        return {(goal.subj, goal.obj)} if res.reached else set()

    # ------------------------------------------------------------------
    # Public entry
    # ------------------------------------------------------------------

    def solve(self, goal: Goal) -> set[tuple[str, str]]:
        """Answer `goal` demand-driven, materializing only the facts it needs. Returns the set of
        (subject, object) IDENTITY-TOKEN pairs that satisfy it (token == name for every unique-named
        entity; `_render` maps a token back to its name at the answer boundary).

        A top-level goal whose subject/object is a DUPLICATED name (a coref entity with several
        mentions) FANS OUT over its `same_as` classes — each class is a distinct identity to try —
        and the answers are unioned. The internal currency is TOKENS; this public boundary RENDERS
        each answer back to a NAME (token == name on any name-canonicalized / unique-name KB, so this
        is the identity map there)."""
        return {(self._render(s), self._render(o)) for (s, o) in self._solve_tokens(goal)}

    def _solve_tokens(self, goal: Goal) -> set[tuple[str, str]]:
        """`solve` without the name-render — returns TOKEN pairs. Used by nested completion /
        existential-NAC solvers, which feed results back into token-level `_extend` joins."""
        subj_toks, obj_toks = self._entry_tokens(goal.subj), self._entry_tokens(goal.obj)
        if subj_toks is None and obj_toks is None:
            return self._solve1(goal)
        out: set[tuple[str, str]] = set()
        for st in (subj_toks if subj_toks is not None else [goal.subj]):
            for ot in (obj_toks if obj_toks is not None else [goal.obj]):
                out |= self._solve1(Goal(goal.rel, st, ot))
        return out

    def _solve1(self, goal: Goal) -> set[tuple[str, str]]:
        """The demand-driven tabled fixpoint for ONE token-level goal (endpoints are tokens or free)."""
        # Long-range demand: a GROUND reachability goal on a transitive-closure relation is
        # carried by a fuel-bounded walker (bounded effort; materializes a shortcut) instead of
        # tabling the entire chain. A pure reachability TOP goal is answered outright here, no
        # fixpoint needed; a walkable ground SUBGOAL is handled inside the loop below (so a walker
        # can be spawned for a reachability subgoal arising within a larger tabled query).
        if self._walk_applicable(goal):
            self._walked_goals.add(goal)
            answers = self._walk_goal(goal)
            self.tables[goal] = answers
            return answers

        self.tables.setdefault(goal, set())
        # SEMI-NAIVE least-fixpoint over the demanded goals ONLY (the magic set). Each round
        # re-evaluates every currently-demanded goal against the current tables; join_body
        # lazily demands subgoals (adding them to `tables`, starting empty). Both the answer
        # sets and the demanded-goal set grow monotonically over a finite Herbrand base, so the
        # loop terminates; we iterate while EITHER still grows.
        #
        # The "semi-naive" part (parity win 2): a goal's body is joined in FULL exactly ONCE (its
        # first evaluation, which seeds from whatever its subgoals already hold), and thereafter
        # only against `_delta_by_rel` — the facts newly added ANYWHERE in the previous round —
        # via `_delta_join` (each body clause takes a turn drawing from the delta while the others
        # draw from the full tables, the classic delta-substitution). So a round no longer re-joins
        # the whole body to rediscover facts it already found; work becomes proportional to
        # derivations, not to rounds x closure-size. CORRECTNESS (the arc invariant): EVERY table
        # growth this round — whether a join derived it OR `_facts_matching` picked up a
        # cross-materialized graph fact — is folded into `next_new`, so the delta propagates through
        # BOTH channels (join tables + the graph side-channel) and no derivation is missed (a head
        # fires the round after its LAST body fact enters the delta). Answers are thus identical to
        # the naive fixpoint (differential-tested against the forward closure); only the work drops.
        changed = True
        while changed:
            changed = False
            n_goals = len(self.tables)
            next_new: dict[str, set[tuple[str, str]]] = {}
            for g in list(self.tables):
                if self._walk_applicable(g):         # a ground reachability SUBGOAL -> walker
                    if g not in self._walked_goals:
                        self._walked_goals.add(g)
                        before = self.tables[g]
                        ans = self._walk_goal(g)     # bounded walk; materializes only the shortcut
                        if ans != before:
                            self.tables[g] = ans
                            changed = True
                            next_new.setdefault(g.rel, set()).update(ans - before)
                    continue                         # walked goals are not tabled/joined
                before = self.tables[g]
                if g.rel in self.tools and g.rel not in self._serviced:
                    # a tool-backed relation is demanded -> run its §8 calculator ONCE (it
                    # materializes its facts into `ag`), then read them like any other fact.
                    self._serviced.add(g.rel)
                    self.tools[g.rel](self.ag)
                    changed = True
                answers = set(before)
                answers |= self._facts_matching(g)       # base + cross-materialized graph facts
                if g.rel in self._neg_of:                # a materialized negative -> completion
                    answers |= self._complete_negative(g)
                elif g not in self._full_joined:         # first eval: FULL join (the seed)
                    self._full_joined.add(g)
                    self.full_joins += 1
                    for rule, head in self.head_index.get(g.rel, []):
                        answers |= self._join_body(rule, head, g)
                else:                                    # later evals: only the delta
                    for rule, head in self.head_index.get(g.rel, []):
                        answers |= self._delta_join(rule, head, g)
                if answers != before:
                    self.tables[g] = answers
                    changed = True
                    next_new.setdefault(g.rel, set()).update(answers - before)
            if len(self.tables) != n_goals:    # new subgoals demanded -> full-join them next round
                changed = True
            self._delta_by_rel = next_new
        return self.tables[goal]

    # ------------------------------------------------------------------
    # Facts and derivation
    # ------------------------------------------------------------------

    def _node_name(self, nid: str) -> str | None:
        nm = self.ag.name(nid)                    # VALUED entity name only (Phase 2.3)
        return nm if nm else None

    # ---- node-level identity: tokens, same_as classes, name<->token at the boundary ----
    # Phase 2.4 (name-free identity): an identity token is `SEP + class-rep-nid` — the class rep is a
    # NODE ID, never the name; the name is recovered by looking up the rep's `name` at the render
    # boundary (`_render`), not baked into the token. SEP (a control char, never in a surface name)
    # stays the discriminator between an IDENTITY token and a plain NAME (concept/literal reference).
    SEP = "\x00"                                              # identity token = SEP + class-rep nid

    def _sa_union(self, a: str, b: str) -> None:
        ra, rb = self._sa_find(a), self._sa_find(b)
        if ra != rb:
            lo, hi = (ra, rb) if ra < rb else (rb, ra)
            self._sa_parent[hi] = lo                          # canonical rep = min id (stable)
            self._invalidate_class(hi)                        # hi's per-node tokens are now WRONG
            self._invalidate_class(lo)                        # lo's ENUMERATION is now incomplete

    def _invalidate_class(self, rep: str) -> None:
        """A `same_as` union just touched class-rep `rep` (either it was retired — its members'
        cached tokens now point at the wrong rep — or it just gained members via the union, so its
        cached ENUMERATION (`_token_class`) is stale even though the rep itself didn't move). Evict
        every node cached under a class token ending in `rep`, and drop the `_token_class` bucket
        itself, so the next `_token()`/`_nodes_of_token()` call recomputes from the current
        union-find instead of serving a pre-union answer — this is what makes a `same_as` derived
        MID-SOLVE (e.g. a domain rule whose head is `same_as`, not just the `universal.same_as_rules`
        propagation set filtered out of `self.rules`) visible immediately, from EITHER side of the
        union, rather than only to whichever node happens to be queried again first."""
        stale = [tok for tok in self._token_class if tok == self.SEP + rep]  # class token IS SEP+rep now
        for tok in stale:
            for nid in self._token_class.pop(tok):
                self._tok_cache.pop(nid, None)

    def _sa_find(self, x: str) -> str:
        p = self._sa_parent.get(x, x)
        if p == x:
            return x
        r = self._sa_find(p)
        self._sa_parent[x] = r
        return r

    def _token(self, nid: str) -> str:
        """The identity TOKEN of node `nid`: the name if it is unique-noded (a unique name IS a stable
        1:1 identity, so token == name — the concept/entity coincide), else the NAME-FREE `SEP + classrep`
        (Phase 2.4) so each `same_as` class of a DUPLICATED name is a distinct identity keyed only by its
        class-rep node id (the name is recovered at render, not stored). Pure per-node computation —
        `_token_class` (the CLASS's full membership) is a separate cache `_nodes_of_token` owns; see there
        for why this must not also write it."""
        t = self._tok_cache.get(nid)
        if t is not None:
            return t
        nm = self._node_name(nid)
        if nm is None:
            t = nid                                          # unnamed: identity is the node itself
        elif self.ag.name_count(nm) <= 1:
            t = nm                                           # unique name: token == name
        else:
            # coref-following: the token is the `same_as` CLASS (mentions compose). coref-blind
            # (recognition/graded): the token is the NODE itself (a singleton class) — non-unique
            # surface tokens stay STRUCTURALLY distinct. Gated by the bank (`_follow_coref`).
            rep = self._sa_find(nid) if self._follow_coref else nid
            t = self.SEP + rep                               # name-free per-class (or per-node) token
        self._tok_cache[nid] = t
        return t

    def _nodes_of_token(self, token: str) -> list[str]:
        """The node ids a token denotes: the `same_as` class for a class-token, else every node
        currently named `token` — a plain name is a CONCEPT/LITERAL reference (matched by name, so
        any class), which for a unique name is its single node.

        `_token_class` is a CACHE, not a ledger some other method incrementally maintains: on a miss
        for a class token (`SEP` in `token`) this SCANS every node named `token`'s name and keeps
        exactly those `_token()` itself maps BACK to this token — correct regardless of whether any
        given member happened to have `_token()` called on it before. (An earlier version had
        `_token()` append just the ONE node it was asked about, which left the cache permanently
        PRESENT-BUT-INCOMPLETE for any class member never individually queried — `cls is not None`
        then short-circuited this scan forever. Recomputing the whole class on a miss, and
        invalidating the whole bucket key on a union rather than patching it, is what keeps this
        correct. MUST go through `_token()`, not re-derive the rep from `_sa_find` directly: a
        coref-BLIND solver (`_follow_coref=False`) has `_token()` ignore the union-find entirely
        (`rep = nid`, not `_sa_find(nid)`) so `same_as`-linked-but-blind mentions stay distinct — a
        raw `_sa_find` comparison here would silently re-merge them, exactly the composition the
        blind mode exists to refuse.)"""
        cls = self._token_class.get(token)
        if cls is not None:
            return cls
        name = self._render(token)
        if self.SEP in token:
            cls = [nid for nid in self.ag.nodes_named(name) if self._token(nid) == token]
            self._token_class[token] = cls
            return cls
        return self.ag.nodes_named(name)

    def _endpoint_matches(self, tok: str, want: str | None) -> bool:
        """Does fact-token `tok` satisfy a goal/pattern endpoint `want`? A CLASS token (`want`
        carries the SEP — a bound entity variable) demands EXACT identity; a plain name (a literal
        CONCEPT, matched by name, or a unique entity) matches any token that renders to it. This is
        the literal-vs-token split: concepts are name-identified, entities are token-identified."""
        if want is None:
            return True
        if self.SEP in want:
            return tok == want
        return self._render(tok) == want

    def _node_of_token(self, token: str | None) -> str | None:
        """A canonical node id for `token` (for reading node attributes), or None if it denotes no
        node yet (an absent concept)."""
        if token is None:
            return None
        nodes = self._nodes_of_token(token)
        return min(nodes) if nodes else None

    def _render(self, token: str | None) -> str | None:
        """The user-facing NAME of a token — the OUTPUT-BOUNDARY rendering (Phase 2.4). A NAME-FREE
        identity token (`SEP + classrep-nid`) has its name looked up from the rep node HERE, at the
        boundary, rather than carried in the token. A plain name (concept/unique entity) or a bare nid
        (unnamed node) renders to itself. token == name for every unique-named entity, so this stays the
        identity map on name-canonicalized KBs."""
        if token is None:
            return None
        if token.startswith(self.SEP):                       # identity token: recover the rep's name
            return self.ag.name(token[len(self.SEP):])
        return token

    def _entry_tokens(self, endpoint: str | None) -> list[str] | None:
        """Top-level name resolution: map a goal endpoint NAME to the token(s) to solve. Returns
        None when no fan-out is needed — the endpoint is None (free), already a token (a nested
        subgoal, which carries the SEP or a unique name), or an absent name (kept as-is so a
        completion can mint it). Returns a LIST of class tokens only for a DUPLICATED name (a coref
        entity), so the top goal fans out over its `same_as` classes."""
        if endpoint is None or self.SEP in endpoint:
            return None
        toks = {self._token(nid) for nid in self.ag.nodes_named(endpoint)}
        if not toks or toks == {endpoint}:
            return None                                      # absent, or unique (token == name)
        return sorted(toks)

    def _facts_matching(self, g: Goal) -> set[tuple[str, str]]:
        """Existing facts in `ag` that satisfy goal `g`.

        SEED FROM THE GROUND ENDPOINT (the honest-gate parity win): a demanded subgoal almost
        always has its subject (or object) bound by SIP, so instead of scanning EVERY derived
        triple (`derived_triples` is O(graph) and its version cache is invalidated by every
        `_materialize`, which profiled as the dominant cost), traverse LOCALLY from the bound
        node's edges — O(degree), not O(graph). This is the same seed-from-ground discipline
        `rewriter._match` uses (rarest anchor first); a relation instance `s -[rel]-> o` is a
        rel-node with `name=rel`, so from a bound subject its facts are `succ(succ(s) named rel)`.
        Only a fully-unbound goal (a genuine free-variable enumeration) falls back to a scan.

        PROVENANCE IS INERT (like `rewriter._match`/`relations_from`): a `proves`/`uses`/`<j:…>`/
        `<axiom>`/`<retracted>` node is never a real domain subject or object, so it is skipped. This
        keeps a rule from binding a provenance node (else a derived `x is T` would leak `proves is T`
        into a free-variable enumeration — decision-attrgraph-rehost)."""
        if g.subj is not None:
            if _is_inert(self._render(g.subj)):
                return set()
            out: set[tuple[str, str]] = set()
            for s_id in self._nodes_of_token(g.subj):        # FOLLOW the same_as class
                for r in self.ag.succ(s_id):
                    if not self.ag.has_key(r, g.rel) or self.ag.is_control(r):  # Phase 2.1: predicate key
                        continue                             # skip CONTROL scaffolding (never a fact)
                    for o_id in self.ag.succ(r):
                        on = self._node_name(o_id)
                        if on is None or self.ag.is_inert(o_id):  # Phase 2.2: inert flag, not name
                            continue
                        o_tok = self._token(o_id)
                        if self._endpoint_matches(o_tok, g.obj):
                            out.add((g.subj, o_tok))
            return out
        if g.obj is not None:
            if _is_inert(self._render(g.obj)):
                return set()
            out = set()
            for o_id in self._nodes_of_token(g.obj):         # FOLLOW the same_as class
                for r in self.ag.pred(o_id):
                    if not self.ag.has_key(r, g.rel) or self.ag.is_control(r):  # Phase 2.1: predicate key
                        continue                             # skip CONTROL scaffolding (never a fact)
                    for s_id in self.ag.pred(r):
                        sn = self._node_name(s_id)
                        if sn is not None and not self.ag.is_inert(s_id):  # Phase 2.2: inert flag
                            out.add((self._token(s_id), g.obj))
            return out
        # Fully-free: enumerate the reified relation instances named `g.rel` (each a node with the
        # subject as in-edges and the object as out-edges), tokenizing both endpoints.
        out = set()
        for r in self.ag.nodes_with_key(g.rel):  # Phase 2.1: predicate key, not name
            if self.ag.is_control(r):                         # skip CONTROL scaffolding (never a fact)
                continue
            objs = [o for o in self.ag.succ(r)]
            for s_id in self.ag.pred(r):
                sn = self._node_name(s_id)
                if sn is None or self.ag.is_inert(s_id):  # Phase 2.2: inert flag, not name
                    continue
                for o_id in objs:
                    on = self._node_name(o_id)
                    if on is not None and not self.ag.is_inert(o_id):  # Phase 2.2: inert flag
                        out.add((self._token(s_id), self._token(o_id)))
        return out

    def _delta_join(self, rule: Rule, head: Pat, g: Goal) -> set[tuple[str, str]]:
        """The semi-naive re-evaluation of `rule` for goal `g`: the sum, over each body clause
        position, of the join with THAT clause restricted to the previous round's delta (the
        others full). A new head fact requires at least one body fact to be new, so this covers
        exactly the derivations the naive full re-join would find that it had not found before,
        without re-walking the all-old x all-old cross product. A bodiless rule (no positions)
        contributes nothing here — it fired once in its full-join seed."""
        out: set[tuple[str, str]] = set()
        for j in range(len(rule.lhs)):
            out |= self._join_body(rule, head, g, delta_pos=j)
        return out

    def _delta_matching(self, sub: Goal) -> set[tuple[str, str]]:
        """The previous round's newly-added facts that satisfy subgoal `sub` — the delta the
        semi-naive pass draws one body clause from. Indexed by relation (`_delta_by_rel`), then
        filtered by whatever endpoint SIP has already bound (usually one side), so this is cheap."""
        cand = self._delta_by_rel.get(sub.rel)
        if not cand:
            return set()
        if sub.subj is None and sub.obj is None:
            return set(cand)
        # The delta holds TOKEN pairs; match the subgoal endpoints with the same literal-vs-token
        # semantics as `_facts_matching` (a literal concept matches any class by name, a bound
        # token matches exactly) — else a delta fact `('alice','happy\x00n1')` is dropped against a
        # literal subgoal `is(alice, happy)` and the semi-naive round misses the derivation.
        return {(s, o) for (s, o) in cand
                if self._endpoint_matches(s, sub.subj) and self._endpoint_matches(o, sub.obj)}

    def _join_body(self, rule: Rule, head: Pat, g: Goal,
                   delta_pos: int | None = None) -> set[tuple[str, str]]:
        """Solve `rule`'s body left-to-right under the demand from goal `g` (SIP: goal args
        seed head vars, and each body clause's answers bind the next), demanding each body
        clause as a subgoal. Materialize + return the head answers.

        `delta_pos` selects semi-naive mode: when it is a clause index, that clause draws its
        tuples from the previous round's DELTA (`_delta_matching`) instead of the full table
        (the others stay full) — the delta-substitution of one body atom. `None` = the FULL
        join (every clause full), used once as a goal's seed. Every subgoal is DEMANDED either
        way, so demand-expansion is identical between modes."""
        env0 = self._unify_head(head, g)
        if env0 is None:
            return set()
        envs: list[dict[str, str]] = [env0]
        for idx, bpat in enumerate(rule.lhs):
            if bpat.p_kind == 1:
                return set()                       # variable-predicate body clause: out of slice
            new_envs: list[dict[str, str]] = []
            for env in envs:
                sub = self._pat_goal(bpat, env)
                self.tables.setdefault(sub, set())   # DEMAND this subgoal
                pairs = self._delta_matching(sub) if idx == delta_pos else self.tables[sub]
                for (s, o) in pairs:
                    e2 = self._extend(env, bpat, s, o)
                    if e2 is not None:
                        new_envs.append(e2)
            envs = new_envs
        answers: set[tuple[str, str]] = set()
        for env in envs:
            if self._exist_nac_blocks(rule, env):    # a ¬∃ NAC group is satisfiable -> blocked
                continue
            s = self._head_endpoint(rule, head.s, env)
            o = self._head_endpoint(rule, head.o, env)
            if s is None or o is None:
                continue
            deg = self._graded_degree(rule, env)     # the α-cut gate in the goal path
            if deg is None:                          # a graded condition failed its α-cut
                continue
            answers.add((s, o))
            self._record_degree(literal_name(head.p), s, o, deg)
            head_node = self._materialize(literal_name(head.p), s, o)
            if self.provenance:
                self._justify(rule, head_node, env)
        return answers

    def _exist_nac_blocks(self, rule: Rule, env: dict[str, str]) -> bool:
        """True if any of `rule`'s EXISTENTIAL NAC groups is satisfiable under `env` (so the head
        must NOT fire) — the ¬∃ shapes (`not ?o blocked_by ?anyp`, the grouped `not ?x chosen and
        not ?x add ?c`). `not A and not B` is `¬A ∧ ¬B`, so ANY satisfiable group blocks (mirrors
        the forward engine's `nac_blocks`, which blocks if any independent group matches)."""
        groups = self._exist_nac.get(rule.key)
        if not groups:
            return False
        return any(self._group_satisfiable(group, env) for group in groups)

    def _group_satisfiable(self, group: list[Pat], env: dict[str, str]) -> bool:
        """Is the existential NAC `group` satisfiable under `env` — does a witness exist for its
        NAC-local free vars? Join its clauses left-to-right, DEMANDING each as a subgoal solved to
        COMPLETION in a self-contained nested solve (the same soundness discipline as
        `_complete_negative`: read the group's COMPLETE positive extension, not a partial outer
        round — a block must not be missed merely because a producer had not run yet). The group is
        satisfiable iff at least one env survives the join. A bound token in `env` grounds its
        slot; a NAC-local free var is left open (`_pat_goal` -> None) and bound by the answers,
        `?x`-repeated across clauses via `_extend`. Memoized (Phase 1.2): keyed by (group identity,
        env restricted to the group's own vars), valid only while `len(self._materialized)` — a
        cheap monotonic derivation epoch, shared across nested solvers — hasn't grown since caching,
        so a later derivation (anywhere) that would flip an UNSATISFIABLE verdict is never missed."""
        group_vars = {b for pat in group for t in (pat.s, pat.p, pat.o) if (b := binder(t)) is not None}
        key = (id(group), tuple(sorted((v, env[v]) for v in group_vars if v in env)))
        cached = self._group_sat_cache.get(key)
        if cached is not None and cached[0] == len(self._materialized):
            return cached[1]
        nested = GoalSolver(self.ag, self.rules, walk_fuel=self.walk_fuel, tools=self.tools,
                            provenance=self.provenance, control_completions=self.control_completions,
                            closures=self._closure_base,
                            _completing=self._completing, _neg_of=self._neg_of,
                            _exist_nac=self._exist_nac, _serviced=self._serviced,
                            _materialized=self._materialized, _justified=self._justified,
                            _skolem=self._skolem, _follow_coref=self._follow_coref,
                            _name_ids=self._name_ids, _sa_parent=self._sa_parent,
                            _tok_cache=self._tok_cache, _token_class=self._token_class,
                            _group_sat_cache=self._group_sat_cache)
        envs: list[dict[str, str]] = [dict(env)]
        for pat in group:
            new_envs: list[dict[str, str]] = []
            for e in envs:
                for (s, o) in nested._solve_tokens(self._pat_goal(pat, e)):
                    e2 = self._extend(e, pat, s, o)
                    if e2 is not None:
                        new_envs.append(e2)
            envs = new_envs
            if not envs:
                break
        self.derived += nested.derived                    # fold nested derivation into the metric
        result = bool(envs)
        self._group_sat_cache[key] = (len(self._materialized), result)
        return result

    def _complete_negative(self, g: Goal) -> set[tuple[str, str]]:
        """Answer a demanded negative `R_not(c, P)` by DEMAND-DRIVEN COMPLETION (the `decide` line
        on the goal path), for an ARBITRARY predicate R (`is_not`, `overridden_not`, `stance_not`,
        …): solve the positive `R(c, P)` to COMPLETION in a self-contained nested solve; if the
        positive has NO answer, the closed-world negative holds — materialize `c R_not P` (matched
        positively everywhere else) and answer it; if the positive IS derivable it DEFEATS the
        default, so answer nothing.

        The nested solve computes the positive's COMPLETE extension independently of the outer
        fixpoint round, which is what makes reading "the positive failed" SOUND (a partial outer
        table could be empty merely because a producer had not run yet — the classic NAF-in-a-
        fixpoint bug); this is the goal-directed analog of stratifying the producer BELOW the
        consumer. Sound for STRATIFIED negation; a negative cycle (the nested solve re-demands this
        very negative) is caught by `_completing` and rejected, never silently mis-answered.

        Free-subject `R_not` (enumerate every c that is-not R P) needs the candidate universe and is
        out of slice — the consumer's positive residual always grounds the subject before the
        negative clause is demanded (`_lower_nac` appends it last, and rejects a NAC subject the
        positive body never binds), so this is never hit in-slice."""
        if g.subj is None or g.obj is None:
            return set()
        if g in self._neg_cache:
            return self._neg_cache[g]
        if g in self._completing:
            raise NonStratifiable(f"non-stratifiable negation: {g.rel}({g.subj}, {g.obj}) "
                                  "depends negatively on itself")
        positive = Goal(self._neg_of[g.rel], g.subj, g.obj)
        nested = GoalSolver(self.ag, self.rules, walk_fuel=self.walk_fuel, tools=self.tools,
                            provenance=self.provenance, control_completions=self.control_completions,
                            closures=self._closure_base,
                            _completing=self._completing | {g}, _neg_of=self._neg_of,
                            _exist_nac=self._exist_nac, _serviced=self._serviced,
                            _materialized=self._materialized, _justified=self._justified,
                            _skolem=self._skolem, _follow_coref=self._follow_coref,
                            _name_ids=self._name_ids, _sa_parent=self._sa_parent,
                            _tok_cache=self._tok_cache, _token_class=self._token_class,
                            _group_sat_cache=self._group_sat_cache)
        pos_answers = nested._solve_tokens(positive)
        self.derived += nested.derived                    # fold nested derivation into the metric
        if pos_answers:
            res: set[tuple[str, str]] = set()             # positive derivable -> default defeated
        else:
            res = {(g.subj, g.obj)}                        # completion: materialize the negative
            neg_node = self._materialize(g.rel, g.subj, g.obj)
            if self.control_completions:                  # recognition scaffolding -> control-layer,
                self.ag.set_control(neg_node)             # invisible to fact matching (never a fact)
            if self.provenance:                           # a closed-world negative holds by ABSENCE
                self._justify_completion(g.rel, neg_node)  # of the positive -> a premise-less `complete` J
        self._neg_cache[g] = res
        return res

    def _graded_degree(self, rule: Rule, env: dict[str, str]) -> float | None:
        """The degree in (0, 1] for `rule`'s graded conditions under `env`, or None if any
        α-cut fails. This is `rewriter.graded_degree` on the goal path: per condition, the min
        over its dims of the bound node's graded attribute; α-cut at the threshold; min across
        conditions. A demanded goal is thus filtered by graded membership exactly as the forward
        rule is (the graded gate meets goal-direction). Inverted conditions are out of slice."""
        if not rule.graded:
            return 1.0
        degs: list[float] = []
        for c in rule.graded:
            if c.inverted:
                return None
            nid = self._node_of_token(env.get(c.var))
            if nid is None:
                return None
            scores = [self._graded_attr(nid, d) for d in c.embedding]
            score = min(scores) if scores else 0.0
            if score < c.threshold:
                return None
            degs.append(score)
        return min(degs) if degs else 1.0

    def _graded_attr(self, nid: str, dim: str) -> float:
        a = self.ag.get_attr(nid, dim)
        return float(a.value) if (a is not None and a.kind == GRADED) else 0.0

    def _record_degree(self, rel: str, s: str, o: str, deg: float) -> None:
        key = (rel, s, o)
        self.degree[key] = max(self.degree.get(key, 0.0), deg)   # possibilistic: most-confident

    # ------------------------------------------------------------------
    # Binding helpers (concept/name level)
    # ------------------------------------------------------------------

    def _unify_head(self, head: Pat, g: Goal) -> dict[str, str] | None:
        env: dict[str, str] = {}
        for kind, key, name, want in ((head.s_kind, head.s_bind, head.s_name, g.subj),
                                      (head.o_kind, head.o_bind, head.o_name, g.obj)):
            if want is None:
                continue
            if kind == 1:                                    # variable
                if env.get(key, want) != want:
                    return None
                env[key] = want
            elif name != self._render(want):   # plain OR bound literal: match the demand by name only
                return None
        return env

    def _pat_goal(self, bpat: Pat, env: dict[str, str]) -> Goal:
        sk = bpat.s_kind
        s = env.get(bpat.s_bind) if sk == 1 else (env.get(bpat.s_bind, bpat.s_name) if sk == 2
                                                  else bpat.s_name)
        ok = bpat.o_kind
        o = env.get(bpat.o_bind) if ok == 1 else (env.get(bpat.o_bind, bpat.o_name) if ok == 2
                                                  else bpat.o_name)
        return Goal(bpat.p_name, s, o)

    def _resolve(self, slot: str, env: dict[str, str]) -> str | None:
        """The concrete identity a slot resolves to under `env`, or None if a free variable. A
        BOUND-LITERAL (`is?`/`a?`) is a name-constrained variable: once PINNED (matched in an earlier
        body clause) it resolves to that specific NODE token, so its later occurrences reference the
        SAME node (`rewriter` pins it in `bindings`); unpinned, it resolves to its name (any node so
        named). Without this, `?cs next is?, is? next a?` floats over every `is` node (cross-product)."""
        if is_var(slot):
            return env.get(binder(slot))
        if is_bound_literal(slot):
            return env.get(binder(slot), literal_name(slot))
        return literal_name(slot)

    @staticmethod
    def _is_skolem(slot: str) -> bool:
        """A `<...>?` head token — a bound-literal keyword (`<cond>?`/`<rule>?`/`<use>?`) that a form
        MINTS FRESH per firing (value invention). Excludes plain-literal keywords (`is?`/`a?`, no `<`)
        which resolve by name, and bare singletons (`<closed_world>`, no `?` -> not a bound-literal)."""
        return is_bound_literal(slot) and literal_name(slot).startswith("<")

    def _head_endpoint(self, rule: Rule, slot: str, env: dict[str, str]) -> str | None:
        """Resolve a head subject/object token to an identity token — Skolemizing a `<...>?` token to a
        FRESH node keyed by (rule, token, env), so a rule's RHS clauses share one fresh node per firing
        and distinct firings stay distinct (the value-invention `rewriter.apply_rule`/`MINT` did, which
        the demand-driven engine lacked). Non-Skolem slots resolve as before (`_resolve`)."""
        if not self._is_skolem(slot):
            return self._resolve(slot, env)
        key = (rule.key, slot, frozenset(env.items()))
        tok = self._skolem.get(key)
        if tok is None:
            nid = self.ag.add_node({"name": valued(literal_name(slot))})   # fresh `<cond>`/`<rule>`/…
            tok = self.SEP + nid                             # Phase 2.4: name-free identity token = the
            #                                                  fresh node id (unique; render recovers name)
            self._token_class[tok] = [nid]
            self._tok_cache[nid] = tok
            self._skolem[key] = tok
        return tok

    def _extend(self, env: dict[str, str], bpat: Pat, s: str, o: str) -> dict[str, str] | None:
        e = dict(env)
        for kind, key, name, val in ((bpat.s_kind, bpat.s_bind, bpat.s_name, s),
                                     (bpat.o_kind, bpat.o_bind, bpat.o_name, o)):
            if kind == 1:                                    # variable: bind to the TOKEN (identity)
                if key in e and e[key] != val:
                    return None
                e[key] = val
            elif kind == 2:                                  # bound literal: a NAME-CONSTRAINED var —
                if name != self._render(val):                # check the name, then PIN the node so later
                    return None                              # clauses use the SAME node (as `rewriter`
                if key in e and e[key] != val:               # binds it) — no cross-product over same-
                    return None                              # named tokens
                e[key] = val
            elif name != self._render(val):                  # a plain literal matches by NAME (concept)
                return None
        return e

    def _ensure_node(self, token: str) -> str:
        """The canonical node for identity `token`, minting (and registering) it if absent. For a
        class token the canonical `same_as`-class member; for a unique/absent name the node named it
        (a completion object like `urgent` may live only as a rule literal with no base node — the
        negative `c is_not urgent` must still reify against a `urgent` node)."""
        nid = self._node_of_token(token)
        if nid is None:
            name = self._render(token)
            nid = self.ag.add_node({"name": valued(name)})
            self._name_ids[name] = nid
            self._tok_cache[nid] = token
            if self.SEP in token:                             # a class token: keep `_token_class` live
                self._token_class.setdefault(token, []).append(nid)
        return nid

    def _materialize(self, rel: str, s: str, o: str) -> str:
        """MINT the reified relation s -> [rel] -> o into `ag`, if not already present, and RETURN
        the relation node id (existing or fresh — so a caller can wire provenance onto it). The
        existence check is LOCAL (a rel-node named `rel` from s to o) — same seed-from-ground
        reason as `_facts_matching`: avoid an O(graph) `derived_triples` scan per materialize."""
        s_id, o_id = self._ensure_node(s), self._ensure_node(o)
        if rel == "same_as":
            # A rule head can derive `same_as` MID-SOLVE (not just the `universal.same_as_rules`
            # propagation set, which is filtered entirely out of `self.rules` -- see the
            # `_follow_coref` split in `__init__`). Join the union-find the moment the endpoints
            # are resolved so `_token`/`_nodes_of_token` see the merged class on every read after.
            self._sa_union(s_id, o_id)
        if (s, rel, o) not in self._materialized:        # not yet written this run: find or mint
            existing = None
            for r in self.ag.succ(s_id):
                if self.ag.has_key(r, rel) and o_id in self.ag.succ(r):  # Phase 2.1: predicate key
                    existing = r                         # present (perhaps via a nested solver)
                    break
            if existing is None:
                # Phase 2.1/2.3: mint via add_relation (predicate rides the graded key; no name bridge).
                existing = self.ag.add_relation(s_id, rel, o_id)
                self.derived += 1
            self._rel_node[(s, rel, o)] = existing
            self._materialized.add((s, rel, o))
        node = self._rel_node.get((s, rel, o))
        if node is None:                                 # materialized in a sibling solver (shared
            for r in self.ag.succ(s_id):                 # _materialized, private _rel_node) -> re-find
                if self.ag.has_key(r, rel) and o_id in self.ag.succ(r):  # Phase 2.1: predicate key
                    node = r
                    break
            self._rel_node[(s, rel, o)] = node
        return node

    def _find_fact_node(self, s: str, pname: str, o: str) -> str | None:
        """The reified relation node witnessing premise `s -[pname]-> o` (or None). For provenance
        `uses` wiring: the fact was already joined so it exists; find it by identity (memo first,
        then a local succ scan). Non-minting — a premise never absent when this is called."""
        key = (s, pname, o)
        if key in self._rel_node:
            return self._rel_node[key]
        s_id, o_id = self._node_of_token(s), self._node_of_token(o)
        if s_id is None or o_id is None:
            return None
        for r in self.ag.succ(s_id):
            if self.ag.has_key(r, pname) and o_id in self.ag.succ(r):  # Phase 2.1: predicate key
                self._rel_node[key] = r
                return r
        return None

    def _justify(self, rule: Rule, head_node: str, env: dict[str, str]) -> None:
        """MINT an in-graph justification for a freshly derived head (provenance.py): a `<j:rulekey>`
        node with `proves -> head_node` and `uses -> each positive body clause's relation node` under
        `env` — the SAME substrate trace `rewriter.run` writes (`_apply_rule`), so `surface.explain`
        reads the backward engine's derivations. Deduped per (fact, rule) so semi-naive re-derivation
        does not multiply Js. The reified relation form matches `add_relation` (a 2-hop proves/uses)."""
        from .provenance import PROVES, USES, j_name     # lazy: provenance -> world_model would cycle
        if head_node is None or (head_node, rule.key) in self._justified:
            return
        self._justified.add((head_node, rule.key))
        j = self.ag.add_node({"name": valued(j_name(rule.key))}, inert=True)  # Phase 2.2
        self.ag.add_relation(j, PROVES, head_node, inert=True)
        for bpat in rule.lhs:
            s, o = self._resolve(bpat.s, env), self._resolve(bpat.o, env)
            if s is None or o is None:
                continue
            pnode = self._find_fact_node(s, literal_name(bpat.p), o)
            if pnode is not None:
                self.ag.add_relation(j, USES, pnode, inert=True)

    def _justify_completion(self, rel: str, neg_node: str) -> None:
        """MINT a premise-less `<j:complete.REL>` justification for a closed-world negative — it holds
        by the ABSENCE of the positive's derivation (no `uses`), which is exactly what makes `explain`
        render it as the elimination step ("could not derive the positive"). The `decide`-line analog
        of the forward completion rule's justification, on the goal path (decision-forcing-a-decision)."""
        from .provenance import PROVES, j_name
        key = f"complete.{rel}"
        if (neg_node, key) in self._justified:
            return
        self._justified.add((neg_node, key))
        j = self.ag.add_node({"name": valued(j_name(key))}, inert=True)  # Phase 2.2
        self.ag.add_relation(j, PROVES, neg_node, inert=True)


def solve_goal(ag: AttrGraph, rules: list[Rule], goal: Goal) -> tuple[set[tuple[str, str]], int]:
    """Convenience: answer `goal` demand-driven over `ag` (mutated in place: only demanded facts
    are materialized). Returns (answers, number_of_facts_derived)."""
    solver = GoalSolver(ag, rules)
    return solver.solve(goal), solver.derived


def solve_all(ag: AttrGraph, rules: list[Rule], *, walk_fuel: int | None = None,
              tools: dict | None = None, provenance: bool = False,
              control_completions: bool = False) -> "GoalSolver":
    """Forward-materialize the whole closure by DEMANDING every rule-head predicate (subject and
    object both free) through ONE `GoalSolver` — the goal-directed engine used as a forward driver.

    This is the re-host beachhead (`decision-attrgraph-rehost`, Phase B): the ISA machine serving
    as the PRODUCTION reasoning engine. It reuses `GoalSolver`'s positive core + NAC-as-COMPLETION
    (`_complete_negative`) + existential-NAC emptiness + graded α-cut + tools, so it reproduces a
    stratified `run_rules` materialization at the answer level WITHOUT `rewriter`'s forward
    `nac_blocks`/`_nac_groups`/`graded_degree` — and WITHOUT deleting a fact edge (negation is a
    materialized positive `is_not`/`R_not`, never a retraction), so §5 holds by construction.

    Demanding each head fully (free/free) drives the whole Herbrand base of the demanded predicates;
    completion of any negative body clause happens on demand as a nested complete solve. `ag` is
    mutated in place (only reachable facts are materialized). Returns the solver (read `.derived`,
    `.degree`, `.tables`)."""
    solver = GoalSolver(ag, rules, walk_fuel=walk_fuel, tools=tools, provenance=provenance,
                        control_completions=control_completions)
    for rel in list(solver.head_index):
        solver.solve(Goal(rel))
    return solver
