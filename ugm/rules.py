"""Rules (§8), matching and arbitration (§14).

A rule is a fact relating two moments -- `causes(A, B)` or `implies(A, B)` -- and
because it is a node, everything else about it is an ordinary fact. Direction is a
query over the rule, never a field in it: one statement, two readings.

Slice one carries the one-locus case only. An antecedent whose members all sit at
the same moment needs no skeleton, and the skeleton is what §8 adds for chains.
"""

from typing import Callable, Dict, List, NamedTuple, Optional, Sequence, Tuple

from .chain import Chain, Entry, Moment, weaker
from .graph import Graph, NodeId

CAUSES = "causes"
IMPLIES = "implies"


class Member(NamedTuple):
    """A signed entry in a rule's antecedent or consequent. In the antecedent the
    grade is unused: what a premise was worth is read off the entry that matched
    it, not asserted by the rule."""

    sign: str
    pattern: NodeId
    grade: str = "certain"


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
        # Authored precedence (§14): the bottom-most arbitrator is a lookup that
        # always returns and never searches.
        self.overrides: List[Tuple[Rule, Rule]] = []
        # ...and defeat about a CASE. `overrides` is per tick: a rule overridden
        # by another that matched anywhere this step does not apply at all, which
        # is right when the two are rival answers to one situation (the boss's
        # rule and the vice's) and wrong when they are rival answers to each of
        # several. Pointing `overrides` at a real pair showed it: making the
        # outcome of an action replace the assumption that the action happened
        # also suppressed the assumption for every OTHER action in the step.
        #
        # Two intents, two relations, rows rather than branches. `supersedes`
        # defeats only the applications that share **evidence** -- a consumed
        # entry -- with an application of the higher rule, which is what *about
        # the same case* means when the two rules bind different variables and
        # cannot be compared any other way.
        self.supersedes: List[Tuple[Rule, Rule]] = []
        # What each composed rule collapses. The trail of a shortcut, so
        # `decompose on surprise` knows which sub-steps to re-run (§21).
        self.composed_from: Dict[NodeId, Tuple["Rule", "Rule"]] = {}
        # Authoring a rule is an event, the way a write is. The machine
        # subscribes so that a rule becomes DATA the moment it exists rather than
        # when somebody remembers to ask -- which matters once rules read rules:
        # a reader that enumerates `+rule(?r)` sees whatever was reified, and a
        # rule authored afterwards was invisible to it with nothing reporting so.
        self.on_rule: List[Callable[["Rule"], None]] = []
        # Rules by the relation they CONCLUDE. §3 gives the substrate one index,
        # over instances by relation, and argues for it in one line: *a rule
        # whose antecedent names a relation has to start somewhere, and scanning
        # every node is the alternative.* Read backwards the same argument holds
        # of the rule set -- a reader asking *what could produce this goal* has
        # to start somewhere, and asking every rule is the alternative.
        #
        # It is an index over what was ASSERTED (the authored consequent), never
        # over what was derived, which is §12's condition on any index here.
        #
        # A consequent that is a bare variable is deliberately absent: it claims
        # it can conclude anything, which §12 calls vacuous backwards, and `fit`
        # already declines it.
        self.by_conclusion: Dict[Optional[NodeId], List["Rule"]] = {}

    def rule(
        self,
        connective: str,
        antecedent: Sequence[Member],
        consequent: Sequence[Member],
        name: str = "",
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
        node = self.g.instance(
            rel, self._moment(antecedent), self._moment(consequent)
        )
        r = Rule(node, connective, antecedent, consequent, name)
        self.rules.append(r)
        for m in consequent:
            if m.sign != "+" or self.g.is_var(m.pattern):
                continue
            bucket = self.by_conclusion.setdefault(self.g.relation_of(m.pattern), [])
            if r not in bucket:
                bucket.append(r)
        for hook in self.on_rule:
            hook(r)
        return r

    def _moment(self, members: Sequence[Member]) -> NodeId:
        """A generic moment: signed members, and no anchored predecessor (§4).

        The sign is in the graph rather than beside it, so *which rules disturb
        position* stays a query over the consequent's members -- which is R4.
        """
        entries = [
            self.g.instance(self.ENTRY, m.pattern, self.SIGN[m.sign]) for m in members
        ]
        return self.g.instance(self.MOMENT, *entries)

    def overrides_rule(self, higher: Rule, lower: Rule) -> None:
        self.overrides.append((higher, lower))

    def supersedes_rule(self, higher: Rule, lower: Rule) -> None:
        self.supersedes.append((higher, lower))

    def compose(self, first: Rule, second: Rule, name: str = "") -> Optional[Rule]:
        """Collapse `first` then `second` into one rule (§4).

        This is the design's largest available speedup, because it removes steps
        rather than making them cheaper, and the artifact is an ordinary node --
        askable, attributable, defeasible.

        Three things §21 requires, and each is a line here rather than a promise:

        **Standardise apart.** Both rules may say `?w` and mean different things.

        **Unify pattern against pattern.** Not match: `boiling(?w)` against
        `boiling(?x)` binds a variable to a variable, which matching never does.

        **Inherit the defeats.** Anything that overrides either constituent must
        override the composition, or the shortcut fires where the reasoning it
        replaces would have been defeated -- §21's *a shortcut that has outlived
        its guards*, arriving immediately rather than after a context change.

        Two things are NOT done, and saying so is the point of writing it down.

        `unless` **is not implemented anywhere in this engine**, so the half of
        guard inheritance that §12 describes cannot be carried. Only `overrides`
        can, and it is. A composed rule is therefore as defeasible as its parts
        only with respect to precedence.

        The **grade** is not composed. §21 records why: it would be a minimum
        computed once, from constituents that are themselves defeasible, which is
        a cache of a derived value -- §16's own objection one level up. Until
        that is settled, composition is refused for anything but `certain`.
        """
        fa = {}
        f_ant = [Member(m.sign, rename(self.g, m.pattern, fa), m.grade) for m in first.antecedent]
        f_con = [Member(m.sign, rename(self.g, m.pattern, fa), m.grade) for m in first.consequent]
        sa: Dict[NodeId, NodeId] = {}
        s_ant = [Member(m.sign, rename(self.g, m.pattern, sa), m.grade) for m in second.antecedent]
        s_con = [Member(m.sign, rename(self.g, m.pattern, sa), m.grade) for m in second.consequent]

        if any(m.grade != "certain" for m in f_con + s_con):
            return None

        for i, want in enumerate(s_ant):
            for made in f_con:
                if made.sign != want.sign:
                    continue
                b = unify_patterns(self.g, made.pattern, want.pattern)
                if b is None:
                    continue
                antecedent = [
                    Member(m.sign, ground(self.g, m.pattern, b), m.grade) for m in f_ant
                ] + [
                    Member(m.sign, ground(self.g, m.pattern, b), m.grade)
                    for j, m in enumerate(s_ant)
                    if j != i
                ]
                consequent = [
                    Member(m.sign, ground(self.g, m.pattern, b), m.grade) for m in s_con
                ]
                composed = self.rule(
                    second.connective if first.connective == second.connective else CAUSES,
                    antecedent,
                    consequent,
                    name or f"{first.name}+{second.name}",
                )
                self.composed_from[composed.node] = (first, second)
                for higher, lower in list(self.overrides):
                    if lower is first or lower is second:
                        self.overrides.append((higher, composed))
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
        return bindings if bound == node else None
    if pattern == node:
        return bindings
    prel, nrel = g.relation_of(pattern), g.relation_of(node)
    if prel is None or nrel is None or prel != nrel:
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

    §21 asked whether pattern-against-pattern is the same operation as match. It
    is not, and the differences are not incidental:

    | | match (§7) | this |
    |---|---|---|
    | sides | generic against **anchored** | generic against generic |
    | a variable binds to | a thing | a thing **or another variable** |
    | needs `walk` | no | yes -- bindings chain |
    | needs `occurs` | no | yes -- `?x = f(?x)` is constructible |
    | needs standardising apart | no | yes -- two rules may reuse `?w` |

    So the floor's item 2 does not cover it. What follows is that composition
    (§4) cannot be built out of `fit`, and needs its own service -- which is the
    same conclusion `fit` reached for a different reason, and for the same
    underlying one: the caller cannot hold the answer, so the machinery must
    finish the job.
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
    members = g.members(p)
    new = [ground(g, m, bindings) for m in members]
    if p == pattern and all(a == b for a, b in zip(new, members)):
        return p
    return g.rel(r, *new)


def substitute(g: Graph, pattern: NodeId, bindings: Dict[NodeId, NodeId]) -> NodeId:
    """Ground a consequent pattern. Anything still generic afterwards is a rule
    whose consequent names something its antecedent never bound, and the gate
    refuses it rather than minting a node nobody can read.

    **A subterm nothing changed is returned unchanged**, and that is correctness
    rather than a shortcut. Rebuilding goes through `g.rel`, which interns, so a
    subterm minted by `instance` comes back as a *different node*. A rule node is
    exactly that -- §5 needs a rule to be a node other facts can be about, so
    rule nodes do not intern.

    The test cannot be *is it ground*, because a rule node is not: it contains
    the variables of its own patterns. `+resume(?h, <cb>)` binds `?h` and touches
    nothing inside `<cb>`, whose variables belong to `<cb>` and are bound by
    nobody. Rebuild it anyway and the conclusion is about an interned **twin** of
    the rule, so every later question about the real one answers nothing --
    silently, and only when rules started being pointed at.
    """
    if g.is_var(pattern):
        return bindings.get(pattern, pattern)
    members = g.members(pattern)
    if not members:
        return pattern
    rel = g.relation_of(pattern)
    assert rel is not None
    new = [substitute(g, m, bindings) for m in members]
    if all(a == b for a, b in zip(new, members)):
        return pattern
    return g.rel(rel, *new)


# -- match ------------------------------------------------------------------


def current_state(chain: Chain, locus: Moment, seat: Moment) -> List[Entry]:
    """Every proposition the chain has an answer for at `locus`, as believed at
    `seat`, resolved to the one entry that governs it. This is the walk of §4,
    and it is the design's single most consequential cost."""
    props: List[NodeId] = []
    seen = set()
    for m in seat.ancestors():  # newest moment first
        for e in reversed(m.delta):  # ...and newest within a moment
            if e.proposition not in seen:
                seen.add(e.proposition)
                props.append(e.proposition)
    out = []
    for p in props:
        e = chain.resolve(p, locus, seat)
        if e is not None:
            out.append(e)
    return out


class Situation:
    """The current state, plus the one index matching actually asks for.

    §3 gives the substrate exactly one index, over instances by relation, and
    says why: *a rule whose antecedent names a relation has to start somewhere,
    and scanning every node is the alternative*. That argument is about the
    graph; it is just as true of the state, and it was not being made there --
    every antecedent member was unified against every entry.

    Signed, because a member's sign is fixed and half the entries are the wrong
    one. A member that is a **bare variable** has no relation to key on and still
    scans everything, which is correct: `+?p` is a rule that says *believe what
    this channel reported*, and it genuinely is about anything.

    ⭐⭐⭐ **And it is MAINTAINED, not rebuilt.** The index was built from the
    whole state once per tick, which is the same disease `state` cured one layer
    down: the state itself stopped being rebuilt and the index over it did not,
    so a tick stayed O(everything known) whatever matching cost. Measured:
    `Situation.__init__` was the single largest cost in the loop.

    A state changes by one claim at a time -- §4 says so -- so the index changes
    by one claim at a time too. `add` and `drop` are what a caller holding a kept
    state calls instead of constructing a new one; the constructor is still there
    for the callers that genuinely have a fresh list (a delta, the instrument).

    ⚠ **Order is part of the answer.** Entries arrive here **newest-first** and
    §18's *a description with two candidates resolves to the most recent* rests
    on it. So a bucket is a dict in ARRIVAL order -- oldest first, which is the
    order a maintained state can append to -- and read back reversed. The
    reversal is cached per bucket and dropped when that bucket changes, so a
    rule reading a bucket nothing touched this tick pays nothing.

    ⚠⚠ And the honest limit of that, measured rather than assumed: reversing
    the STATE breaks 6 checks, and reversing the BUCKETS breaks none. Since
    `heap` the within-rule order is a stamp off the consumed entries' nodes, not
    the order they were discovered in, so nothing downstream reads a bucket's
    order any more. It is kept because it is what the walk says and this is a
    replacement for the walk -- not because a check would notice. `ugm.state`
    is what notices.
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
        for e in reversed(list(entries)):
            self.add(e)

    def _keys(self, e: Entry) -> Tuple[Tuple[str, object], Tuple[str, object]]:
        return (e.sign, self.g.relation_of(e.proposition)), (e.sign, self.ANY)

    def add(self, e: Entry) -> None:
        """Claim `e`, at the newest end."""
        self._order[e.node] = e
        for k in self._keys(e):
            self._by.setdefault(k, {})[e.node] = e
            self._read.pop(k, None)
        self._entries = None

    def drop(self, e: Entry) -> None:
        """`e` is no longer what the state claims -- superseded, or out of mind."""
        self._order.pop(e.node, None)
        for k in self._keys(e):
            bucket = self._by.get(k)
            if bucket is not None and bucket.pop(e.node, None) is not None:
                self._read.pop(k, None)
        self._entries = None

    @property
    def entries(self) -> List[Entry]:
        """The state as a list, newest-first. Materialised only when asked for:
        the loop stopped needing it, and `_materialise` still does."""
        if self._entries is None:
            self._entries = list(reversed(self._order.values()))
        return self._entries

    def candidates(self, g: Graph, want: Member) -> List[Entry]:
        key = (want.sign, self.ANY if g.is_var(want.pattern)
               else g.relation_of(want.pattern))
        out = self._read.get(key)
        if out is None:
            bucket = self._by.get(key)
            if bucket is None:
                return []
            out = self._read[key] = list(reversed(bucket.values()))
        return out


def match(
    g: Graph,
    chain: Chain,
    rule: Rule,
    locus: Moment,
    seat: Moment,
    state: Optional["Situation"] = None,
    fresh: Optional["Situation"] = None,
) -> List[Application]:
    """Unify a generic moment against an anchored one, over the current state.

    Records which entries it matched. That is not overhead: it is what makes a
    misbehaving rule distinguishable from a misresolving chain.

    `state` may be supplied by a caller that is matching several rules at one
    seat, and the loop does. It is the same walk for all of them -- recomputing
    it per rule was 86% of the engine's runtime, measured, because every
    proposition is `resolve`d and `resolve` is itself a walk. Not an
    optimisation of the read: the read is unchanged, and asked once.

    ⭐⭐⭐ `fresh` is the **delta**, and it is what makes the loop stop
    rediscovering what it already knew. Measured before building it: of 5,775
    applications a 600-fact corpus matched, **75 were new and 5,700 were
    re-derived** -- 98.7% waste; and 92.9% on the kettle fixture, so this was
    never a big-corpus concern. The loop recomputed its whole option set on
    every move and threw all but one away.

    An application is NEW only if it consumes at least one entry deposited since
    the last look. So with `fresh` given, this runs one pass per antecedent
    member: that member draws from the delta, the others from the full state.
    Union over the passes, deduped -- an application consuming two fresh entries
    is found once per fresh member and must be reported once.

    ⚠ The delta is a `Situation` like any other, so this adds no representation.
    §4 already says *a moment is a signed delta*; the matcher simply had not
    been reading it that way.
    """
    if state is None:
        state = Situation(g, current_state(chain, locus, seat))
    results: List[Application] = []
    seen: set = set()

    def run(pivot: Optional[int]) -> None:
        def step(
            i: int, bindings: Dict[NodeId, NodeId], consumed: Tuple[Entry, ...]
        ) -> None:
            if i == len(rule.antecedent):
                if pivot is not None:
                    k = (rule.node, frozenset(bindings.items()))
                    if k in seen:
                        return
                    seen.add(k)
                results.append(Application(rule, bindings, consumed))
                return
            want = rule.antecedent[i]
            source = fresh if (pivot is not None and i == pivot) else state
            for e in source.candidates(g, want):
                b = unify(g, want.pattern, e.proposition, bindings)
                if b is not None:
                    step(i + 1, b, consumed + (e,))

        step(0, {}, ())

    if fresh is None:
        run(None)
    else:
        for pivot in range(len(rule.antecedent)):
            run(pivot)
    return results


# -- arbitrate --------------------------------------------------------------


def arbitrate(
    rs: RuleSet,
    applications: Sequence[Application],
    priority: Optional[Callable[["Rule"], Tuple]] = None,
) -> Optional[Application]:
    """Among the rules that matched, choose one. Total: it always answers.

    Two steps, and they are not the same step.

    **Defeat first.** `overrides` is defeasibility (§12), not a ranking: a rule
    that is overridden by another rule *that also matched here* does not apply at
    all. Merely ordering them would let the loser apply on the following tick and
    overwrite the winner, so the boss's rule would be obeyed and then quietly
    undone by the vice's.

    **Then choose.** Three keys, in this order, and the order is the argument.

        authority     `overrides` -- already applied, above, as defeat
        apparatus     a `standing` rule keeps its authored place
        helpfulness   what the situation recommends (`prefer`)
        authoring     the order they were written in

    Authority first is not negotiable: the boss's rule beating the vice's is a
    claim about who decides, and no amount of *this one usually works* may
    outrank it. That is why defeat runs first and is not folded in here as
    another score.

    The apparatus next, and this one was found by breaking it. Preference is
    derived from *what serves the current goal*, and let loose over everything it
    outranked the rules that notice a **surprise** -- so the agent carried on
    pursuing a goal while a channel was telling it the world had moved. Being
    helpful towards a goal is not a reason to outrank the machinery that decides
    whether the goal still makes sense. `standing` rules therefore keep the
    authored order they already had, and preference orders what is left.

    Helpfulness third is the change, and what it replaces is worth naming. The
    tie among applicable, undefeated rules used to be broken by **the order they
    happened to be written in** -- an accident of authoring, deciding which of
    several possible moves an agent makes, including the irreversible ones. A
    derived preference is not obviously right, but it is not an accident, and it
    is a claim the trail records and a corpus can argue with.

    Still a lookup that never searches (§14), so it stays total: with no
    preferences it is exactly the authored order it always was.
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

    This runs on everything that **matched**, before any quiescence filter --
    and the order is load-bearing. Defeat is about whose antecedent holds, not
    about who still has work to do. Filter first and the winner disappears as
    soon as its conclusion is already written, whereupon the loser is
    unopposed and quietly overwrites it: the boss's rule obeyed once, then
    undone by the vice's on the following tick.

    ⭐ Which is exactly why `matched` is a separate argument. The loop now passes
    only the applications that still have work to do -- that is what stops the
    tick being linear in everything ever matched -- and the rules that matched
    are carried alongside, so nothing above changes. `_defeated` reads only the
    rule set, so the two can come apart without the guarantee coming apart.

    ⚠ `supersedes` is the one test that genuinely needs the applications
    themselves, because it compares CONSUMED ENTRIES rather than rules. A caller
    that is withholding applications cannot answer it, so a rule set that uses
    `supersedes` gets the whole set and the old cost. That is stated rather than
    hidden: the fast path is for corpora that do not order two rules *for the
    same case*, which is all of them so far.
    """
    matched = list(matched) if matched is not None else [a.rule for a in applications]
    surviving = [
        a
        for a in applications
        if not _defeated(rs, a.rule, matched) and not _superseded(rs, a, applications)
    ]
    if surviving:
        return surviving
    # A cycle in `overrides` would defeat everything. Arbitration must stay
    # total (§14), so fall back rather than answer nothing.
    #
    # ⚠⚠⚠ **Asked of the RULES, not of the applications handed in.** With a
    # withheld set, *nothing here survived* and *nothing survived at all* are
    # different claims: a quiet application whose rule is undefeated means the
    # old code returned it and quiescence then dropped it, ending the tick with
    # no move. Falling back on the short list instead would revive a defeated
    # rule and make a move the agent had decided against. The fallback is for a
    # cycle, and a cycle is a property of the rule set.
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
    if not rs.supersedes:
        return False
    mine = {e.node for e in app.consumed}
    for higher, lower in rs.supersedes:
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
    return any(higher in matched and lower is rule for higher, lower in rs.overrides)


def effective_grade(authored: str, consumed: Sequence[Entry]) -> str:
    """`min(authored, support)` (§12).

    A rule states how strongly it would conclude, given its premises. What its
    premises were worth is not its to say -- without this, a rule asserting
    `@certain` on the strength of a merely-possible input launders a weak premise
    into a strong conclusion, and the weak link vanishes from the trail the whole
    soundness argument walks.
    """
    out = authored
    for e in consumed:
        out = weaker(out, e.grade)
    return out
