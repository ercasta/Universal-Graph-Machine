"""Rules (§8), matching and arbitration (§14).

A rule is a fact relating two moments -- `causes(A, B)` or `implies(A, B)` -- and
because it is a node, everything else about it is an ordinary fact. Direction is a
query over the rule, never a field in it: one statement, two readings.

Slice one carries the one-locus case only. An antecedent whose members all sit at
the same moment needs no skeleton, and the skeleton is what §8 adds for chains.
"""

from typing import Callable, Dict, List, NamedTuple, Optional, Sequence, Tuple

from .chain import Chain, Entry, MINUS, Moment
from .graph import Graph, NodeId

CAUSES = "causes"
IMPLIES = "implies"


class _Stop:
    """The postcondition that ends the run, as a sentinel rather than a node.

    ⭐ attend deposits a claim, unattend denies one, and this stops. ⚠ There
    were three more -- boost, damp and reset -- and they moved a SCORE.

    See docs/design/rules.md#stop.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return "stop"


STOP = _Stop()


class Attend:
    """The postcondition that deposits attention on what the move just bound.

    ⭐⭐⭐ A different KIND of row from the ones it outlived. boost, damp and
    reset moved a score and stop ends the run -- all of them the loop's own
    bookkeeping. ⚠ That is the point rather than a wrinkle.

    See docs/design/rules.md#attend.
    """

    __slots__ = ("term", "weight")

    def __init__(self, term, weight: int = 1) -> None:
        self.term = term
        self.weight = weight

    def __repr__(self) -> str:
        return f"attend({self.term}, {self.weight})"


class _Unattend:
    """...and the one that takes it back, which is `reset` for attention.

    ⚠ It denies what is attended rather than forgetting it, and the difference
    is the whole of `deposit-dont-decide.md`: *the agent stopped attending to
    this here* is a dated, attributable, deniable claim, where dropping a Python
    set is nothing anyone can read or argue with.

    ⚠⚠ And something has to, or attention accumulates until it names everything
    -- which is measurably the same as naming nothing (`ugm.selftest`:
    *attention that names everything narrows nothing*). A buff had `LIFE` for
    this reason; a claim has a denial.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return "unattend"


UNATTEND = _Unattend()


class Member(NamedTuple):
    """A signed entry in a rule's antecedent or consequent.

    Two members, and there was a third: the **grade** a consequent would
    conclude at. It is gone with the rest of `@likely`. What a rule says about
    the strength of its conclusion is now *in* the conclusion -- `+likely(p)` --
    which a rule can read and a corpus can argue with, and a grade never was."""

    sign: str
    pattern: NodeId
    # ⚠ `at ?m` -- WHERE the entry must sit -- went with the locus itself. An
    # entry has no second time to bind to. A rule that wants history reads
    # `in_delta`/`anc`/`entry_of`, which are ordinary structural relations.
    # ⭐ ...and a name for WHAT matched. at ?m says where the entry sits; as ?t
    # says what its proposition is, so a rule can refer to the very thing it
    # matched rather than describing it again.
    # → docs/design/rules.md#and-a-name-for-what-matched-at-m-says-w
    binds: Optional[NodeId] = None


class Rule:
    def __init__(
        self,
        node: NodeId,
        connective: str,
        antecedent: Sequence[Member],
        consequent: Sequence[Member],
        name: str = "",
        mentions: bool = False,
    ) -> None:
        self.node = node
        self.connective = connective
        self.antecedent = list(antecedent)
        self.consequent = list(consequent)
        self.name = name
        # Whether this rule was AUTHORED naming a rule -- `+resume(?h, <cb>)`.
        # A rule node contains the variables of its own patterns, so a consequent
        # that names one is a ground claim that happens to be generic, and the
        # gate would otherwise refuse it. §14 settles use/mention by inheritance,
        # and inheritance has to start somewhere: a pattern written with `<...>`
        # is the source. Without this a rule that ATTACHES a rule to something is
        # dropped by quiescence -- silently, and only at `_would_change`.
        self.mentions = mentions
        # What this rule spends when it applies (the author's design): a list of
        # (query, buffs, frozen), where a query is an ordinary antecedent and a
        # buff moves another rule's score. Empty for every rule that does not
        # say otherwise, and read only by a loop that has a table -- the shipped
        # loop does not look at it.
        self.posts: Tuple = ()
        self._orders: Optional[List[Tuple[int, ...]]] = None

    def walk_order(self, pivot: Optional[int]) -> Tuple[int, ...]:
        """Which order `match` walks the antecedent in, for a given pivot.

        The pivot first and the rest in authored order, so every later member is
        narrowed by what the delta's member bound. Cached on the rule because it
        depends on nothing else: built once, and `match` asked for it 40,000
        times in a 1,600-fact run.
        """
        if self._orders is None:
            w = len(self.antecedent)
            self._orders = [tuple(range(w))] + [
                (p,) + tuple(i for i in range(w) if i != p) for p in range(w)
            ]
        return self._orders[0 if pivot is None else pivot + 1]

    def __repr__(self) -> str:
        return f"<{self.name or self.connective}>"


class Application(NamedTuple):
    """What match found: a rule, what it bound, and what it consumed. The last is
    half the trail (§13), and without it *because a was on b, on Anna's word* has
    no answer."""

    rule: Rule
    bindings: Dict[NodeId, NodeId]
    consumed: Tuple[Entry, ...]


class RuleSet:
    def __init__(self, g: Graph, chain: Optional[Chain] = None) -> None:
        self.g = g
        self.CAUSES = g.atom(CAUSES)
        self.IMPLIES = g.atom(IMPLIES)
        # Shared with the chain, never minted beside it. `Graph.atom` does not
        # intern, so two `g.atom("entry")` calls are two nodes and a rule written
        # against one can never match an entry built from the other.
        self.ENTRY = chain.ENTRY if chain is not None else g.atom("entry")
        self.MOMENT = chain.MOMENT if chain is not None else g.atom("moment")
        self.SIGN = dict(chain.SIGN) if chain is not None else {
            s: g.atom(s) for s in ("+", "-", "?")
        }
        self.rules: List[Rule] = []
        # Experience, kept apart from world knowledge: what to reach for after a
        # rule applies (keyed by its node) and what to reach for at ranking time
        # (keyed by None). A rule says what is the case; a trigger says when it
        # is worth thinking of, and the second is learned while the first is
        # authored. Read only by a loop that has a table.
        self.triggers: Dict[Optional[NodeId], List[Tuple]] = {}
        # STOP (below) may appear as a trigger's target.
        # → docs/design/rules.md#stop-below-may-appear-as-a-trigger-s-target
        self.OVERRIDES: Optional[NodeId] = None
        self.SUPERSEDES: Optional[NodeId] = None
        self.claims: Optional[Callable[[NodeId], object]] = None
        # Relations that are COMPUTED rather than matched (§12's skeleton).
        # Set by the Machine, which owns the registry; a bare RuleSet has none,
        # which is what a rule set with no host functions should say.
        self.computes: Dict[NodeId, Callable] = {}
        # ...and relations that are READ OFF THE CHAIN rather than matched --
        # pred, sanc. §12 calls these the skeleton: *no sign, no locus, no
        # licence; nobody asserted them*.
        # → docs/design/rules.md#and-relations-that-are-read-off-the-chain-rat
        self.structural: Dict[NodeId, Callable] = {}
        # ...and the CLOSURE of that under §6's test, cached. See `skeleton`.
        self._skeleton: Optional[Dict[NodeId, Callable]] = None
        self.by_node: Dict[NodeId, "Rule"] = {}
        # ...and defeat about a CASE.
        # → docs/design/rules.md#and-defeat-about-a-case-overrides-is-per-t

        # What each composed rule collapses. The trail of a shortcut, so
        # `decompose on surprise` knows which sub-steps to re-run (§21).
        self.composed_from: Dict[NodeId, Tuple["Rule", "Rule"]] = {}
        # Authoring a rule is an event, the way a write is. The machine
        # subscribes so that a rule becomes DATA the moment it exists rather than
        # when somebody remembers to ask -- which matters once rules read rules:
        # a reader that enumerates `+rule(?r)` sees whatever was reified, and a
        # rule authored afterwards was invisible to it with nothing reporting so.
        self.on_rule: List[Callable[["Rule"], None]] = []
        # Rules by the relation they CONCLUDE.
        # → docs/design/rules.md#rules-by-the-relation-they-conclude-3-gives-th
        self.by_conclusion: Dict[Optional[NodeId], List["Rule"]] = {}

    def rule(
        self,
        connective: str,
        antecedent: Sequence[Member],
        consequent: Sequence[Member],
        name: str = "",
        node: Optional[NodeId] = None,
    ) -> Rule:
        """A rule is a fact relating **two** moments (§8) -- never a flat list of
        its patterns.

        Two things go wrong if the patterns are flattened onto the connective.
        The arity varies with how many members the rule happens to have, which is
        exactly the shape §5 refuses: a node whose members mean different things
        depending on how many there are. And the *signs* end up nowhere, so
        `{+p} => {+q}` and `{+p} => {-q}` are the same node -- one rule, silently,
        and `overrides(cold, hot)` then names a rule as overriding itself.

        Nothing here interns. A rule is an authored statement, not an idea: two
        rules that happen to say the same thing are still two rules, with
        different authors, precedence and provenance.
        """
        rel = self.CAUSES if connective == CAUSES else self.IMPLIES
        # ⚠⚠⚠ A caller may supply the node, and adopt must.
        # → docs/design/rules.md#a-caller-may-supply-the-node-and-adopt
        if node is None:
            node = self.g.instance(
                rel, self._moment(antecedent), self._moment(consequent)
            )
        r = Rule(node, connective, antecedent, consequent, name)
        self.rules.append(r)
        # ⚠ A new rule can move the fixpoint -- it may read only structure and
        # so make its own conclusion structural. `adopt` makes this a run-time
        # event, not a load-time one.
        self._skeleton = None
        self.by_node[node] = r
        for m in consequent:
            if m.sign != "+" or self.g.is_var(m.pattern):
                continue
            bucket = self.by_conclusion.setdefault(self.g.relation_of(m.pattern), [])
            if r not in bucket:
                bucket.append(r)
        for hook in self.on_rule:
            hook(r)
        return r

    # -- §6's test ---------------------------------------------------------

    def skeleton(self) -> Dict[NodeId, Callable]:
        """Every relation an ordinary rule reads as STRUCTURE rather than as a

        claim: the chain's own (self.structural) plus whatever a stratum-0 rule
        concludes. ⭐⭐⭐ The strata are derived, not assigned. ⚠ Recomputed when
        a rule is added, because adopt means the rule set moves at run time and
        a stratum a rule was classified into before it existed is a stale...

        See docs/design/rules.md#skeleton.
        """
        if self._skeleton is None:
            out = dict(self.structural)
            changed = True
            while changed:
                changed = False
                for r in self.rules:
                    if not self.is_stratum0(r, out):
                        continue
                    for m in r.consequent:
                        rel = self.g.relation_of(m.pattern)
                        if rel is not None and rel not in out:
                            out[rel] = _bounded
                            changed = True
            self._skeleton = out
        return self._skeleton

    def strata(self) -> List[List["Rule"]]:
        """The stratum-0 rules, grouped into layers that must run in order.

        ⚠⚠⚠ Negation makes the ORDER load-bearing, and structure cannot be
        taken back. best is *a candidate nothing beats*.

        See docs/design/rules.md#strata.
        """
        rules = [r for r in self.rules if self.is_stratum0(r)]
        if not rules:
            return []
        rel_of = self.g.relation_of
        chain_rels = set(self.structural)

        # What each derived relation is read FROM, and which of those reads are
        # negated. Chain relations are the floor and depend on nothing.
        deps: Dict[NodeId, set] = {}
        negated: Dict[NodeId, set] = {}
        for r in rules:
            for m in r.consequent:
                c = rel_of(m.pattern)
                deps.setdefault(c, set())
                negated.setdefault(c, set())
                for a in r.antecedent:
                    b = rel_of(a.pattern)
                    if b in chain_rels:
                        continue
                    deps[c].add(b)
                    if a.sign == MINUS:
                        negated[c].add(b)

        # ⚠ RECURSION is not a cycle to be refused -- `dep_after` is transitive
        # and reads itself. Mutually recursive relations must share a layer and
        # settle together, so the layers are over the strongly connected
        # components rather than over the relations. Iterative, because the
        # derivation graph of a corpus's read is not the recursion depth of this
        # process.
        comp = _components(deps)

        level: Dict[int, int] = {}
        for _ in range(len(comp) + 1):
            changed = False
            for c, members in comp.items():
                want = 0
                for rel in members:
                    for b in deps.get(rel, ()):
                        cb = _find(comp, b)
                        if cb is None:
                            continue
                        step = 1 if (cb != c or b in negated.get(rel, ())) else 0
                        if cb == c and b in negated.get(rel, ()):
                            # ⚠⚠⚠ Negation INSIDE a recursion has no
                            # stratification: the answer depends on the order
                            # the rules happened to be tried, and this is the
                            # one component whose whole purpose is to agree with
                            # the walk on every look.
                            raise ValueError(
                                f"{self.g.show(rel)} negates a relation it is "
                                f"mutually recursive with -- the read has no "
                                f"order that gives one answer"
                            )
                        want = max(want, level.get(cb, 0) + step)
                if level.get(c, 0) < want:
                    level[c] = want
                    changed = True
            if not changed:
                break

        layers: Dict[int, List["Rule"]] = {}
        for r in rules:
            n = max(
                (level.get(_find(comp, rel_of(m.pattern)), 0) for m in r.consequent),
                default=0,
            )
            layers.setdefault(n, []).append(r)
        return [layers[n] for n in sorted(layers)]

    def is_stratum0(
        self, rule: "Rule", structural: Optional[Dict[NodeId, Callable]] = None
    ) -> bool:
        """§6's test: *every antecedent member is structural*.

        Such a rule is applied without a read, so it must also CONCLUDE without
        one -- §6's price, stated: *stratum 0 must produce structure, not
        entries. If the walk deposited its intermediate results as claims, it
        would be reading entries and the circle would return.* So this one
        predicate decides both halves, which is why there is no second rule
        type, no marker on the surface and no second interpreter.

        ⚠ An antecedent-less rule is NOT stratum 0. It claims unconditionally,
        and a conclusion nothing structural licensed is a claim about the world
        however few premises it has.
        """
        structural = self.skeleton() if structural is None else structural
        if not rule.antecedent:
            return False
        return all(
            self.g.relation_of(m.pattern) in structural for m in rule.antecedent
        )

    def _moment(self, members: Sequence[Member]) -> NodeId:
        """A generic moment: signed members, and no anchored predecessor (§4).

        The sign is in the graph rather than beside it, so *which rules disturb
        position* stays a query over the consequent's members -- which is R4.
        """
        entries = [
            self.g.instance(self.ENTRY, m.pattern, self.SIGN[m.sign]) for m in members
        ]
        return self.g.instance(self.MOMENT, *entries)

    def precedence(self, relation: Optional[NodeId]) -> List[Tuple[Rule, Rule]]:
        """Which rules the graph says outrank which, here and now.

        ⚠ Empty when nothing claims one, which is the common case and the fast
        path: `instances_of` on a relation nobody has written is empty, so this
        costs a dict lookup before it costs anything else.
        """
        if relation is None or self.claims is None:
            return []
        out: List[Tuple[Rule, Rule]] = []
        for p in self.g.instances_of(relation):
            members = self.g.members(p)
            if len(members) != 2:
                continue
            higher = self.by_node.get(members[0])
            lower = self.by_node.get(members[1])
            if higher is None or lower is None or not self.claims(p):
                continue
            out.append((higher, lower))
        return out

    def compose(self, first: Rule, second: Rule, name: str = "") -> Optional[Rule]:
        """Collapse `first` then `second` into one rule (§4).

        This is the design's largest available speedup, because it removes
        steps rather than making them cheaper, and the artifact is an ordinary
        node -- askable, attributable, defeasible. ⚠ What is genuinely absent
        is amendment at a distance -- adding a guard to a rule you did not
        write -- and calling that unless is what made a one-member rule...

        See docs/design/rules.md#compose.
        """
        # ⚠⚠⚠ Composing across a causes FLATTENS TWO MOMENTS INTO ONE
        # ANTECEDENT, and it loses conclusions.
        # → docs/design/rules.md#composing-across-a-causes-flattens-two-m
        if first.connective == CAUSES and len(second.antecedent) > 1:
            return None
        fa = {}
        f_ant = [Member(m.sign, rename(self.g, m.pattern, fa)) for m in first.antecedent]
        f_con = [Member(m.sign, rename(self.g, m.pattern, fa)) for m in first.consequent]
        sa: Dict[NodeId, NodeId] = {}
        s_ant = [Member(m.sign, rename(self.g, m.pattern, sa)) for m in second.antecedent]
        s_con = [Member(m.sign, rename(self.g, m.pattern, sa)) for m in second.consequent]

        for i, want in enumerate(s_ant):
            for made in f_con:
                if made.sign != want.sign:
                    continue
                b = unify_patterns(self.g, made.pattern, want.pattern)
                if b is None:
                    continue
                antecedent = [
                    Member(m.sign, ground(self.g, m.pattern, b)) for m in f_ant
                ] + [
                    Member(m.sign, ground(self.g, m.pattern, b))
                    for j, m in enumerate(s_ant)
                    if j != i
                ]
                consequent = [
                    Member(m.sign, ground(self.g, m.pattern, b)) for m in s_con
                ]
                composed = self.rule(
                    second.connective if first.connective == second.connective else CAUSES,
                    antecedent,
                    consequent,
                    name or f"{first.name}+{second.name}",
                )
                self.composed_from[composed.node] = (first, second)
                # ⚠ Inheriting the defeats is now a CLAIM, deposited by whoever
                # asked for the composition, because precedence lives in the
                # graph. `Machine.compose` writes them; a caller that composes
                # without a world gets a rule with no inherited precedence,
                # which is the honest answer rather than a silent one.
                self.inherit = [
                    (higher, composed)
                    for higher, lower in self.precedence(self.OVERRIDES)
                    if lower is first or lower is second
                ]
                return composed
        return None


# -- unification ------------------------------------------------------------


def unify(
    g: Graph, pattern: NodeId, node: NodeId, bindings: Dict[NodeId, NodeId]
) -> Optional[Dict[NodeId, NodeId]]:
    """Structural unification of a generic pattern against an anchored node."""
    if g.is_var(pattern):
        bound = bindings.get(pattern)
        if bound is None:
            out = dict(bindings)
            out[pattern] = node
            return out
        return bindings if bound == node or (
            g._merges and g.identity_of(bound) == g.identity_of(node)) else None
    if pattern == node:
        return bindings
    # ⭐⭐⭐ Identity, at BIND TIME -- and without this the rest of the identity
    # layer is half a feature. ⚠ Guarded on _merges, so a corpus that never
    # corefers compares two ints as it always did.
    # → docs/design/rules.md#identity-at-bind-time-and-without-th
    if g._merges and g.identity_of(pattern) == g.identity_of(node):
        return bindings
    prel, nrel = g.relation_of(pattern), g.relation_of(node)
    if prel is None or nrel is None:
        return None
    if prel != nrel and g._merges:
        # The relation slot, through identity: two vocabularies that have been
        # committed to being one relationship match each other's facts, and no
        # rule mentions a denotation to do it.
        if g.identity_of(prel) == g.identity_of(nrel):
            prel = nrel
    if prel != nrel:
        # ⭐ A variable in the RELATION slot. ⚠ It costs §3's only index: a
        # pattern whose relation is unknown has no bucket, so
        # Situation.candidates falls back to the ANY bucket and scans.
        # → docs/design/rules.md#a-variable-in-the-relation-slot-the-subst
        if not g.is_var(prel):
            return None
        bindings = unify(g, prel, nrel, bindings)
        if bindings is None:
            return None
    pm, nm = g.members(pattern), g.members(node)
    if len(pm) != len(nm):
        return None
    cur: Optional[Dict[NodeId, NodeId]] = bindings
    for p, n in zip(pm, nm):
        cur = unify(g, p, n, cur)
        if cur is None:
            return None
    return cur


def generalise(
    g: Graph, a: NodeId, b: NodeId, mapping: Dict[Tuple[NodeId, NodeId], NodeId]
) -> NodeId:
    """The least general structure both `a` and `b` are instances of (Plotkin).

    The dual of unify, and the operation *learn from examples* is made of:
    matching asks what two structures have to agree about, and this asks what
    they already agree about. ⚠ What agrees is KEPT.

    See docs/design/rules.md#generalise.
    """
    if a == b:
        return a
    ra, rb = g.relation_of(a), g.relation_of(b)
    if ra is not None and ra == rb:
        ma, mb = g.members(a), g.members(b)
        if len(ma) == len(mb):
            return g.rel(ra, *[
                generalise(g, x, y, mapping) for x, y in zip(ma, mb)
            ])
    key = (a, b)
    if key not in mapping:
        mapping[key] = g.var(f"?g{len(mapping)}")
    return mapping[key]


def walk(g: Graph, n: NodeId, bindings: Dict[NodeId, NodeId]) -> NodeId:
    """Follow a chain of variable-to-variable bindings to its end.

    Matching never needs this: it binds a generic side to an anchored one, so a
    variable's value is a thing and never another variable. Two-sided
    unification does, and that is the first sign it is a different operation.
    """
    seen = set()
    while g.is_var(n) and n in bindings and n not in seen:
        seen.add(n)
        n = bindings[n]
    return n


def occurs(g: Graph, var: NodeId, n: NodeId, bindings: Dict[NodeId, NodeId]) -> bool:
    """Does `var` appear inside `n`? Binding `?x` to `f(?x)` builds a structure
    that contains itself, and every later walk over it runs forever. Matching
    cannot produce the situation; unification can, so it has to be checked."""
    n = walk(g, n, bindings)
    if n == var:
        return True
    if g.is_var(n):
        return False
    r = g.relation_of(n)
    if r is not None and occurs(g, var, r, bindings):
        return True
    return any(occurs(g, var, m, bindings) for m in g.members(n))


def unify_patterns(
    g: Graph, a: NodeId, b: NodeId, bindings: Optional[Dict[NodeId, NodeId]] = None
) -> Optional[Dict[NodeId, NodeId]]:
    """Unify two structures that may **both** be generic.

    §21 asked whether pattern-against-pattern is the same operation as match.

    See docs/design/rules.md#unify-patterns.
    """
    bindings = {} if bindings is None else bindings
    a, b = walk(g, a, bindings), walk(g, b, bindings)
    if a == b:
        return bindings
    if g.is_var(a):
        if occurs(g, a, b, bindings):
            return None
        out = dict(bindings)
        out[a] = b
        return out
    if g.is_var(b):
        if occurs(g, b, a, bindings):
            return None
        out = dict(bindings)
        out[b] = a
        return out
    ar, br = g.relation_of(a), g.relation_of(b)
    if ar is None or br is None or ar != br:
        return None
    am, bm = g.members(a), g.members(b)
    if len(am) != len(bm):
        return None
    cur: Optional[Dict[NodeId, NodeId]] = bindings
    for x, y in zip(am, bm):
        cur = unify_patterns(g, x, y, cur)
        if cur is None:
            return None
    return cur


def rename(g: Graph, pattern: NodeId, fresh: Dict[NodeId, NodeId]) -> NodeId:
    """Standardise apart: give a rule's variables identities nobody else uses.

    Two rules written independently both say `?w`, and they mean different
    things. Matching never notices because only one side has variables.

    Ground structures pass through untouched -- same reason as `substitute`.
    """
    if not g.has_var(pattern):
        return pattern
    if g.is_var(pattern):
        if pattern not in fresh:
            fresh[pattern] = g.var(f"{g.show(pattern)}'")
        return fresh[pattern]
    if not g.members(pattern):
        return pattern
    r = g.relation_of(pattern)
    assert r is not None
    return g.rel(r, *[rename(g, m, fresh) for m in g.members(pattern)])


def ground(g: Graph, pattern: NodeId, bindings: Dict[NodeId, NodeId]) -> NodeId:
    """Apply a two-sided substitution, following variable chains.

    A subterm nothing changed passes through untouched, for `substitute`'s
    reason: interning a rebuilt copy of something minted un-interned makes a
    twin."""
    p = walk(g, pattern, bindings)
    if g.is_var(p) or not g.members(p):
        return p
    r = g.relation_of(p)
    assert r is not None
    # ...and the relation slot substitutes like any other, or a rule could bind
    # `?p` and then be unable to build `?p(?x)` back -- match and substitute
    # travel together (§5), and half of it is worse than neither.
    r2 = walk(g, r, bindings) if g.is_var(r) else r
    members = g.members(p)
    new = [ground(g, m, bindings) for m in members]
    if p == pattern and r2 == r and all(a == b for a, b in zip(new, members)):
        return p
    return g.rel(r2, *new)


def _left_open(g, pattern, bindings) -> bool:
    """Did this member leave a variable of its OWN unbound?

    The question `has_var` over the grounded node was standing in for, and the
    two part company exactly where §14 does. A rule reading `con(?r, ?pat, +, ?i)`
    binds `?pat` to a stored pattern, so its conclusion contains variables and
    every one of them is bound -- a ground claim that happens to be about a
    generic thing. A rule whose consequent names a variable its antecedent never
    bound is the other case, and only that one has nothing to deposit.

    Told apart by asking of the MEMBER rather than of the result: a variable
    that survives substitution and belongs to this member is unbound; one that
    arrived inside a binding's value does not belong to it.
    """
    from .text import _vars_in  # deferred: `text` imports this module
    return any(v not in bindings for v in _vars_in(g, pattern))


def substitute(g: Graph, pattern: NodeId, bindings: Dict[NodeId, NodeId]) -> NodeId:
    """Ground a consequent pattern. Anything still generic afterwards is a rule

    whose consequent names something its antecedent never bound, and the gate
    refuses it rather than minting a node nobody can read.

    See docs/design/rules.md#substitute.
    """
    if g.is_var(pattern):
        return bindings.get(pattern, pattern)
    # ⭐ A whole TERM may be bound, not only a variable -- which is how a `+kind`
    # mark becomes the node this application minted. Nothing else binds a compound,
    # so this costs one dict get on a path that runs per consequent member.
    got = bindings.get(pattern)
    if got is not None:
        return got
    members = g.members(pattern)
    if not members:
        return pattern
    rel = g.relation_of(pattern)
    assert rel is not None
    # ...and the relation slot substitutes too, or a rule may bind `?p` in its
    # antecedent and be unable to conclude `?p(?t)`. Anything still generic here
    # is refused by the gate as before, which now correctly includes a
    # consequent whose RELATION nothing bound.
    new_rel = bindings.get(rel, rel) if g.is_var(rel) else rel
    new = [substitute(g, m, bindings) for m in members]
    if new_rel == rel and all(a == b for a, b in zip(new, members)):
        return pattern
    return g.rel(new_rel, *new)


class _Generic:
    """The third answer `already_there` needs: *still open*, told apart from
    *ground and absent* so the caller never has to build one to find out."""

    def __repr__(self) -> str:
        return "GENERIC"


GENERIC = _Generic()


def already_there(
    g: Graph, pattern: NodeId, bindings: Dict[NodeId, NodeId]
) -> Optional[NodeId]:
    """The node `substitute` WOULD produce, if it already exists. Never mints.

    ⚠⚠⚠ substitute interns, so asking with it changes the answer.

    See docs/design/rules.md#already-there.
    """
    if g.is_var(pattern):
        got = bindings.get(pattern)
        return GENERIC if got is None or g.is_var(got) else got
    members = g.members(pattern)
    if not members:
        return pattern
    rel = g.relation_of(pattern)
    if rel is not None and g.is_var(rel):
        rel = bindings.get(rel)
        if rel is None or g.is_var(rel):
            return GENERIC
    new = []
    for m in members:
        got = already_there(g, m, bindings)
        if got is GENERIC:
            return GENERIC
        if got is None:
            # A subterm that is ground and not interned: the whole cannot be
            # interned either, so this is new without looking further.
            return None
        new.append(got)
    return g.find_rel(rel, *new)


# -- match ------------------------------------------------------------------


def current_state(chain: Chain) -> List[Entry]:
    """Every proposition the chain has an answer for, resolved to the one entry
    that governs it. Newest first.

    ⭐⭐⭐ This was *the design's single most consequential cost* (§4): a walk over
    every moment's delta, newest first, keyed by proposition AND by the span it
    was about, asking `resolve` per key. With no locus there is no second key
    and no walk -- the governing entry is the last one deposited, and `_claims`
    already holds them in that order.
    """
    return [got[-1] for got in reversed(list(chain._claims.values())) if got]


class Situation:
    """The current state, plus the one index matching actually asks for.

    §3 gives the substrate exactly one index, over instances by relation, and
    says why: *a rule whose antecedent names a relation has to start somewhere,
    and scanning every node is the alternative*. ⚠ Order is part of the answer.

    See docs/design/rules.md#situation.
    """

    ANY = "*"  # the bare-variable bucket; a relation is a NodeId, so no collision

    def __init__(self, g: Graph, entries: Sequence[Entry] = ()) -> None:
        self.g = g
        # Oldest-first, keyed by the entry's own node: a delta may hold two
        # entries about one proposition, and both are candidates.
        self._order: Dict[NodeId, Entry] = {}
        self._by: Dict[Tuple[str, object], Dict[NodeId, Entry]] = {}
        self._read: Dict[Tuple[str, object], List[Entry]] = {}
        self._entries: Optional[List[Entry]] = None
        # ⭐⭐⭐ The third index, and it is the one attention needs: which
        # RELATIONS a node is currently spoken of under. The two above are read
        # by a pattern that already knows its relation. ⚠ Counted, not a set,
        # because drop has to be exact.
        # → docs/design/rules.md#the-third-index-and-it-is-the-one-attenti
        self._rels: Dict[NodeId, Dict[NodeId, int]] = {}
        for e in reversed(list(entries)):
            self.add(e)

    def _keys(self, e: Entry) -> List[Tuple]:
        # ⭐ Through identity, so a fact written with one vocabulary is offered
        # to a member written with another once the two have been merged. The
        # reading half of `Graph.merge`: without it the index repoints, the
        # candidate is never OFFERED, and the rule silently matches nothing.
        rel = self.g.relation_of(e.proposition)
        if rel is not None and self.g._merges:
            rel = self.g.identity_of(rel)
        keys = [(e.sign, rel), (e.sign, self.ANY)]
        if rel is not None:
            # ⚠ Atoms here too, and for the same reason read from the other
            # end: the only thing that ever looks in one of these buckets is a
            # pattern member that is an atom, and an atom cannot equal a
            # structure.
            # →
            # docs/design/rules.md#atoms-here-too-and-for-the-same-reason-read-f
            keys += [
                (e.sign, rel, i, m)
                for i, m in enumerate(self.g.members(e.proposition))
                if self.g.relation_of(m) is None and not self.g.members(m)
            ]
        return keys

    def add(self, e: Entry) -> None:
        """Claim `e`, at the newest end."""
        self._order[e.node] = e
        for k in self._keys(e):
            bucket = self._by.setdefault(k, {})
            # ⚠ Only a bucket this entry was not already in moves the count.
            # `add` is idempotent everywhere else -- a dict assignment over the
            # same key -- and a count is the one thing that would not be.
            fresh = e.node not in bucket
            bucket[e.node] = e
            self._read.pop(k, None)
            if fresh and len(k) == 4:
                self._mention(k[3], k[1], 1)
        self._entries = None

    def drop(self, e: Entry) -> None:
        """`e` is no longer what the state claims -- superseded, or out of mind."""
        self._order.pop(e.node, None)
        for k in self._keys(e):
            bucket = self._by.get(k)
            if bucket is not None and bucket.pop(e.node, None) is not None:
                self._read.pop(k, None)
                if len(k) == 4:
                    self._mention(k[3], k[1], -1)
        self._entries = None

    def _mention(self, node: NodeId, rel: NodeId, d: int) -> None:
        held = self._rels.setdefault(node, {})
        n = held.get(rel, 0) + d
        if n > 0:
            held[rel] = n
        else:
            # Dropped rather than left at zero, so `relations_of` is a plain
            # read and the dict does not grow a tail of relations nothing is
            # spoken of under any more.
            held.pop(rel, None)
            if not held:
                self._rels.pop(node, None)

    def relations_of(self, node: NodeId) -> List[NodeId]:
        """The relations this node is currently spoken of under, in the order
        they were first claimed.

        *What is believed about `goblin1` right now* -- the state's answer, not
        the graph's. That is the right half for attention: a node the agent knew
        about last week and holds nothing about now is not a node any rule is
        going to be about.
        """
        return list(self._rels.get(node, ()))

    @property
    def entries(self) -> List[Entry]:
        """The state as a list, newest-first. Materialised only when asked for:
        the loop stopped needing it, and `_materialise` still does."""
        if self._entries is None:
            self._entries = list(reversed(self._order.values()))
        return self._entries

    def candidates(
        self, g: Graph, want: Member, bindings: Optional[Dict[NodeId, NodeId]] = None
    ) -> List[Entry]:
        rel = None if g.is_var(want.pattern) else g.relation_of(want.pattern)
        if rel is not None and g._merges:
            rel = g.identity_of(rel)
        # ⚠ A pattern whose RELATION is a variable has no bucket either: nothing
        # is known about what it names until it matches. It takes the same ANY
        # bucket a bare variable does, which is the index cost of allowing one
        # -- stated here rather than discovered on a workload.
        if rel is None or g.is_var(rel):
            key: Tuple = (want.sign, self.ANY)
        else:
            key = (want.sign, rel)
            if rel is not None and bindings:
                key = self._narrowest(g, want, rel, bindings, key)
                if key is None:
                    return []  # nothing claims that argument there
        return self.bucket(key)

    def bucket(self, key: Tuple) -> List[Entry]:
        """One bucket, newest-first. Split out from `candidates` because it is
        the half that is MAINTAINED -- choosing the key is a pure function of
        the pattern -- and so it is the half `ugm.state` compares."""
        out = self._read.get(key)
        if out is None:
            held = self._by.get(key)
            if held is None:
                return []
            out = self._read[key] = list(reversed(held.values()))
        return out

    def _narrowest(self, g, want, rel, bindings, key):
        """The smallest bucket an already-bound argument gives, or `key`.

        `None` means an argument is bound to something nothing claims in that
        position, so there are no candidates at all -- which is the case worth
        having: the answer is reached without touching a single entry.
        """
        best = None
        for i, m in enumerate(g.members(want.pattern)):
            if g.is_var(m):
                m = bindings.get(m)
                if m is None:
                    continue  # not bound yet; this member says nothing here
            # ⚠ Atoms only: `unify` reduces to identity for a node with no
            # relation and no members, and to a structural comparison for
            # anything else -- which can accept a twin an identity key drops.
            if g.relation_of(m) is not None or g.members(m):
                continue
            bucket = self._by.get((want.sign, rel, i, m))
            if bucket is None:
                return None
            if best is None or len(bucket) < best:
                best, key = len(bucket), (want.sign, rel, i, m)
        return key


def match(
    g: Graph,
    chain: Chain,
    rule: Rule,
    state: Optional["Situation"] = None,
    fresh: Optional["Situation"] = None,
    computes: Optional[Dict[NodeId, Callable]] = None,
    structural: Optional[Dict[NodeId, Callable]] = None,
) -> List[Application]:
    """Unify a generic moment against an anchored one, over the current state.

    Records which entries it matched. That is not overhead: it is what makes a
    misbehaving rule distinguishable from a misresolving chain. ⚠ The delta is
    a Situation like any other, so this adds no representation.

    See docs/design/rules.md#match.
    """
    if state is None:
        state = Situation(g, current_state(chain))
    computes = computes or {}
    structural = structural or {}
    results: List[Application] = []
    seen: set = set()
    width = len(rule.antecedent)

    def run(pivot: Optional[int]) -> None:
        # The pivot first, then the rest in authored order. With `pivot` None
        # this is authored order, and the full match is untouched.
        order = rule.walk_order(pivot)
        slots: List[Optional[Entry]] = [None] * width

        def step(j: int, bindings: Dict[NodeId, NodeId]) -> None:
            if j == width:
                if pivot is not None:
                    k = (rule.node, frozenset(bindings.items()))
                    if k in seen:
                        return
                    seen.add(k)
                # ⚠ A computator consumes no ENTRY, so its slot stays empty and
                # is dropped here. §12 says `consumed` is filled by member
                # position, and that is about ORDER rather than arity -- nothing
                # indexes it positionally (checked), every reader iterates, and
                # the relative order of the entries that do exist is unchanged.
                # A member that matched nothing contributing nothing to the
                # trail is the honest record, not a gap in it.
                results.append(Application(
                    rule, bindings, tuple(e for e in slots if e is not None)))
                return
            i = order[j]
            want = rule.antecedent[i]
            rel = g.relation_of(want.pattern)
            walk_fn = structural.get(rel)
            if walk_fn is not None:
                # An evaluated member that reads the chain. It yields each way
                # its arguments can be satisfied, anchored by what is bound.
                # ⭐⭐⭐ A MINUS here is negation as failure, and it needs no
                # notation. ⚠ Safe only because the strata are ORDERED.
                # →
                # docs/design/rules.md#an-evaluated-member-that-reads-the-chain-it-yie
                if want.sign == MINUS:
                    for _ in walk_fn(g, chain, want, bindings):
                        return  # something satisfies it: the negation fails
                    step(j + 1, bindings)
                    return
                for b in walk_fn(g, chain, want, bindings):
                    step(j + 1, b)
                return
            fn = computes.get(rel)
            if fn is not None:
                # ⭐ A computator: evaluated, not matched. §12's skeleton is
                # *conditions on the binding that claim nothing* --
                # distinctness is already one -- and arithmetic is exactly
                # that. ⚠ The arguments must be ground by now.
                # → docs/design/rules.md#a-computator-evaluated-not-matched-12
                args = [walk(g, a, bindings) for a in g.members(want.pattern)]
                if any(g.is_var(a) for a in args):
                    return
                try:
                    got = fn(*[g.show(a) for a in args])
                except Exception:
                    return  # a computator that raises answers nothing
                if got is None:
                    return
                # ⚠⚠⚠ `got` is a NODE, resolved by whoever registered the
                # function in the corpus's own table. Building one here with
                # `g.atom` mints a fresh node, so the result would be a TWIN of
                # the value the corpus writes -- the rule fires, the fact lands,
                # and asking about it answers nothing. Committed while writing
                # this feature, minutes after documenting the trap.
                b = bindings
                if want.binds is not None:
                    b = unify(g, want.binds, got, bindings)
                if b is not None:
                    step(j + 1, b)
                return
            source = fresh if i == pivot else state
            for e in source.candidates(g, want, bindings):
                b = unify(g, want.pattern, e.proposition, bindings)
                if b is not None and want.binds is not None:
                    # ...and what it says, as a whole, under a name.
                    b = unify(g, want.binds, e.proposition, b)
                if b is not None:
                    slots[i] = e
                    step(j + 1, b)
            slots[i] = None

        step(0, {})

    if fresh is None:
        run(None)
    else:
        for pivot in range(len(rule.antecedent)):
            # ⚠ Never pivot on a computator -- and this is an OPTIMISATION,
            # not a correctness fix, which is worth saying because the first
            # comment here claimed the opposite. A computator walked first has
            # nothing bound to compute from, so that pass finds nothing; but
            # every pivot is tried, and the pass whose pivot is the changed
            # ENTRY finds the applications anyway. Measured both ways: identical
            # results, one wasted walk. Skipping it saves the walk.
            r_ = g.relation_of(rule.antecedent[pivot].pattern)
            if r_ in computes or r_ in structural:
                continue
            run(pivot)
    return results


def _anchored(g, chain, want, bindings, strict: bool):
    """`pred(?m, ?n)` / `sanc(?m, ?n)` -- read off the chain, anchored upward.

    ⭐⭐⭐ This is where containment stays structural.

    See docs/design/rules.md#anchored.
    """
    args = g.members(want.pattern)
    if len(args) != 2:
        return
    here = walk(g, args[0], bindings)
    if g.is_var(here):
        return  # unanchored: this would be a downward walk, and yields nothing
    start = chain.moment_by_node(here)
    if start is None:
        return
    m = start.predecessor if strict else start
    while m is not None:
        b = unify(g, args[1], m.node, bindings)
        if b is not None:
            yield b
        if strict and m is start.predecessor and g.is_var(args[1]) is False:
            pass
        m = m.predecessor


def _ground(g, n, bindings) -> bool:
    """Is this argument fully known, once bindings are followed?

    `walk` resolves a variable to its value but does not substitute inside a
    structure, so neither `is_var` nor `has_var` answers this on its own: the
    first is blind to `loaded(?p)`, the second is blind to `?p` being bound.
    """
    w = walk(g, n, bindings)
    if g.is_var(w):
        return False
    if w != n:
        # n was a variable and this is its VALUE -- a thing the match has
        # already found, so it anchors this member however generic what is
        # INSIDE it may be.
        # → docs/design/rules.md#n-was-a-variable-and-this-is-its-value-a-th
        return True
    rel = g.relation_of(n)
    if rel is not None and not _ground(g, rel, bindings):
        return False
    return all(_ground(g, m, bindings) for m in g.members(n))


def _stored(g, chain, want, bindings):
    """A skeleton relation that is IN the graph -- `pred`, `in_delta`,

    delta_next, rests_on, and whatever a stratum-0 rule concludes -- matched by
    unifying against its ground instances. ⭐⭐⭐ This is the whole of the second
    matcher, and it is four lines. ⚠ At least one argument must be bound, and
    the discipline is *bounded by something already known* rather than *bounded
    by a named position*.

    See docs/design/rules.md#stored.
    """
    rel = g.relation_of(want.pattern)
    args = g.members(want.pattern)
    # ⚠⚠⚠ GROUND, not merely not-a-variable.
    # → docs/design/rules.md#ground-not-merely-not-a-variable-this
    if not any(_ground(g, a, bindings) for a in args):
        return  # unbounded: this would enumerate the history, so it finds nothing
    for node in _narrowed(g, rel, want, bindings):
        b = _as_fact(g, want, node, bindings)  # a pattern is not a fact (§7)
        if b is not None:
            yield b



def _components(deps: Dict[NodeId, set]) -> Dict[int, set]:
    """Strongly connected components of a dependency graph, iteratively.

    Tarjan, without recursion: a corpus's read may be deeper than this process's
    stack, and a stratifier that crashes on a large rule set is a stratifier
    that decides how many rules a corpus may have.
    """
    index: Dict[NodeId, int] = {}
    low: Dict[NodeId, int] = {}
    on: Dict[NodeId, bool] = {}
    stack: List[NodeId] = []
    out: Dict[int, set] = {}
    counter = [0]

    for root in list(deps):
        if root in index:
            continue
        work = [(root, iter(deps.get(root, ())))]
        index[root] = low[root] = counter[0]
        counter[0] += 1
        stack.append(root)
        on[root] = True
        while work:
            node, it = work[-1]
            for nxt in it:
                if nxt not in deps:
                    continue  # a chain relation: the floor, not a component
                if nxt not in index:
                    index[nxt] = low[nxt] = counter[0]
                    counter[0] += 1
                    stack.append(nxt)
                    on[nxt] = True
                    work.append((nxt, iter(deps.get(nxt, ()))))
                    break
                if on.get(nxt):
                    low[node] = min(low[node], index[nxt])
            else:
                work.pop()
                if work:
                    low[work[-1][0]] = min(low[work[-1][0]], low[node])
                if low[node] == index[node]:
                    group = set()
                    while True:
                        w = stack.pop()
                        on[w] = False
                        group.add(w)
                        if w == node:
                            break
                    out[index[node]] = group
    return out


def _find(comp: Dict[int, set], rel) -> Optional[int]:
    for c, members in comp.items():
        if rel in members:
            return c
    return None


# Pairs already checked by `occurs`. A variable and a value are the same two
# nodes every time the same fact is offered to the same member, and the answer
# cannot change: node identity is immutable here. Profiled before adding it,
# `occurs` was 6,021,023 calls and a third of the read's runtime.
_SAFE = set()


def _narrowed(g, rel, want, bindings):
    """The instances worth offering this member, using §3's argument-position

    index instead of every instance of the relation. ⚠ Counted on the GRAPH
    rather than reported by return value, because this is a generator's inner
    loop reached through two structural readers that have no...

    See docs/design/rules.md#narrowed.
    """
    best = None
    for i, a in enumerate(g.members(want.pattern)):
        node = walk(g, a, bindings) if g.is_var(a) else a
        if g.is_var(node) or g.has_var(node):
            continue
        bucket = g.instances_with(rel, i, node)
        if best is None or len(bucket) < len(best):
            best = bucket
    if best is None:
        every = g.instances_of(rel)
        seen = g.scans.setdefault(g.show(want.pattern), [0, 0])
        seen[0] += 1
        seen[1] += len(every)
        return every
    return list(best)


def _as_fact(g, want, node, bindings):
    """Unify a structural want against a candidate node, and answer only if the

    candidate is a FACT rather than a pattern. §7 splits generic from anchored,
    and this seam asked it as has_var over the whole candidate node.

    See docs/design/rules.md#as-fact.
    """
    if not g.has_var(node):
        # The common case, and the one this seam always handled: a ground fact
        # cannot bind a variable to a variable and cannot contain one, so the
        # two guards below have nothing to do and are not paid for. Measured
        # before adding this line: the checks cost 30x on a fixture where they
        # changed no answer at all.
        return unify(g, want.pattern, node, bindings)
    if any(g.is_var(a) for a in g.members(node)):
        # A cheap reject for the pattern case: an authored member has variables
        # in its own argument positions, and a fact the chain deposited never
        # does -- its arguments are entries, moments and propositions, however
        # generic what is INSIDE them may be. Without this the seam pays a full
        # unification per authored pattern per member.
        return None
    if node == want.pattern:
        # The member finding ITSELF. `g.rel` interns, so a rule's own member is
        # among the instances of its relation, and `unify` returns early on
        # identity -- binding nothing, and therefore binding nothing to a
        # variable either, which is how this walked past the test below and
        # derived `near(M, ?p)` with `?p` free.
        return None
    b = unify(g, want.pattern, node, bindings)
    if b is None:
        return None
    for k, v in b.items():
        if g.is_var(v):
            return None
        if g.has_var(v) and (k, v) not in _SAFE and occurs(g, k, v, {}):
            # A rule reading the reification of ITSELF: `<echo>`'s antecedent
            # `con(?r, ?pat, plus, ?i)` meets the entry that reifies `<echo>`,
            # whose stored pattern contains that very `?pat` node -- and binding
            # it builds a structure that contains itself, which every later walk
            # runs forever on. `occurs` exists for exactly this and says match
            # cannot produce it; once a chain fact about a generic proposition
            # is visible, match can, so the check comes with the visibility.
            return None
        if g.has_var(v):
            _SAFE.add((k, v))
    return b


def _bounded(g, chain, want, bindings):
    """A skeleton relation that needs no anchor, because it is bounded by

    construction: asking(<seat>), and whatever a stratum-0 rule concludes. ⭐⭐⭐
    This is where the anchoring discipline actually divides, and it is not
    where I first drew it. ⚠ The containment argument therefore rests on the
    SEED.

    See docs/design/rules.md#bounded.
    """
    rel = g.relation_of(want.pattern)
    for node in _narrowed(g, rel, want, bindings):
        b = _as_fact(g, want, node, bindings)
        if b is not None:
            yield b


def _members_of(g, chain, want, bindings):
    """`entry_of(?e, ?locus, ?prop, ?sign)` -- an entry's own three members.

    §12's `?t = entry(?m, p, +)` prefix form, as a member rather than as
    notation. An entry node IS `entry(locus, proposition, sign)`, so this reads
    what is already there; nothing is stored for it.

    ⚠ Anchored on the ENTRY. Decomposing is single-valued -- one entry has one
    locus, one proposition, one sign -- so from an anchored entry this yields at
    most one binding, and unanchored it would enumerate the whole history.
    """
    args = g.members(want.pattern)
    if len(args) != 4:
        return
    e = walk(g, args[0], bindings)
    if g.is_var(e) or g.relation_of(e) != chain.ENTRY:
        return
    parts = g.members(e)
    if len(parts) != 3:
        return
    b = bindings
    for pattern, got in zip(args[1:], parts):
        b = unify(g, pattern, got, b)
        if b is None:
            return
    yield b


def structural_relations(chain) -> Dict[NodeId, Callable]:
    """The skeleton, as members an ordinary rule may write (§6, §12).

    §6 says stratum 0 is *a property of a rule* -- every antecedent member is
    structural -- decided *by inspecting an antecedent rather than by a
    designer assigning layers*, and that it *runs under the same interpreter*.
    ⚠ entry_of is a third thing again: not stored and not walked, but *read off
    the node's own members*.

    See docs/design/rules.md#structural-relations.
    """
    # ⚠⚠⚠ pred was the reflexive-transitive walk, under the name of the
    # immediate one.
    # → docs/design/rules.md#pred-was-the-reflexive-transitive-walk
    return {
        chain.PRED: _stored,
        chain.ANC: lambda g, c, w, b: _anchored(g, c, w, b, strict=False),
        chain.SANC: lambda g, c, w, b: _anchored(g, c, w, b, strict=True),
        chain.IN_DELTA: _stored,
        chain.DELTA_NEXT: _stored,
        chain.RESTS_ON: _stored,
        chain.LICENSED_BY: _stored,
        chain.ARRIVED_ON: _stored,
        chain.MENTIONED: _stored,
        chain.ENTRY_OF: _members_of,
        chain.ASKING: _bounded,
        chain.ASKED: _bounded,
        # `time(?m, ?t)` -- stored, so it refuses an unbound moment for
        # `_stored`'s reason: it is a fact about the whole history, and an
        # unanchored read would walk all of it.
        chain.TIME: _stored,
    }


# -- arbitrate --------------------------------------------------------------


def arbitrate(
    rs: RuleSet,
    applications: Sequence[Application],
    priority: Optional[Callable[["Rule"], Tuple]] = None,
) -> Optional[Application]:
    """Among the rules that matched, choose one. Total: it always answers.

    Two steps, and they are not the same step. Defeat first.

    See docs/design/rules.md#arbitrate.
    """
    if not applications:
        return None
    score = priority or (lambda r: ())
    best = applications[0]
    best_key = (score(best.rule), rs.rules.index(best.rule))
    for cand in applications[1:]:
        key = (score(cand.rule), rs.rules.index(cand.rule))
        if key < best_key:
            best, best_key = cand, key
    return best


def defeat(
    rs: RuleSet,
    applications: Sequence[Application],
    matched: Optional[Sequence["Rule"]] = None,
) -> List[Application]:
    """Drop the applications whose rule is overridden by another that matched.

    This runs on everything that matched, before any quiescence filter -- and
    the order is load-bearing. Defeat is about whose antecedent holds, not
    about who still has work to do. ⚠ supersedes is the one test that genuinely
    needs the applications themselves, because it compares CONSUMED ENTRIES
    rather than rules.

    See docs/design/rules.md#defeat.
    """
    matched = list(matched) if matched is not None else [a.rule for a in applications]
    surviving = [
        a
        for a in applications
        if not _defeated(rs, a.rule, matched) and not _superseded(rs, a, applications)
    ]
    if surviving:
        return surviving
    # A cycle in overrides would defeat everything. Arbitration must stay total
    # (§14), so fall back rather than answer nothing. ⚠⚠⚠ Asked of the RULES,
    # not of the applications handed in.
    # → docs/design/rules.md#a-cycle-in-overrides-would-defeat-everything
    if any(not _defeated(rs, r, matched) for r in matched):
        return []
    return list(applications)


def _superseded(rs: RuleSet, app: Application, applications: Sequence[Application]) -> bool:
    """Defeated **for this case** rather than for this step.

    Two applications are about the same case when they were triggered by the
    same evidence, and a shared consumed entry is the only comparison available:
    the rules bind different variables, so their bindings cannot be lined up.
    It is also the honest one -- the trail already records what each application
    matched, because R5 needs it, so nothing is measured that was not already
    kept.
    """
    pairs = rs.precedence(rs.SUPERSEDES)
    if not pairs:
        return False
    mine = {e.node for e in app.consumed}
    for higher, lower in pairs:
        if lower is not app.rule:
            continue
        for other in applications:
            if other.rule is higher and mine & {e.node for e in other.consumed}:
                return True
    return False


def _defeated(rs: RuleSet, rule: "Rule", matched: Sequence["Rule"]) -> bool:
    """Overridden by something that matched here. A rule overridden by a rule
    whose antecedent does not hold is not defeated -- that is what makes
    defeasibility about the situation rather than about the rule set."""
    return any(higher in matched and lower is rule
               for higher, lower in rs.precedence(rs.OVERRIDES))


def _defeaters(rs: RuleSet, rule: "Rule", matched: Sequence["Rule"]) -> List["Rule"]:
    """*Which* rules defeated it, and that is the whole difference between
    knowing a rule lost and being able to say to whom.

    `_defeated` answers the question arbitration asks -- may this apply -- and
    throws the answer away. Nothing else could ever reconstruct it: the losing
    rule leaves no trace, so *which of my rules actually fight* was a question
    about a run that no run recorded.
    """
    return [
        higher for higher, lower in rs.precedence(rs.OVERRIDES)
        if lower is rule and higher in matched
    ]


# `effective_grade` was here: `min(authored, every consumed entry's grade)` --
# §12's weakest link, computed on every write. Gone with the grade itself. What
# propagates uncertainty now is a supposition's WRAPPER: cross `likely(p)`,
# reason inside with the ordinary rules, and what comes out is `likely(q)`. Two
# uncertain premises give `likely(possible(q))` -- the weakest link as STRUCTURE
# rather than as a number, and collapsing that is a corpus's table and a
# corpus's claim about which of its modalities is weaker than which.
