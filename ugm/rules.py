"""Rules (§8), matching and arbitration (§14).

A rule is a fact relating two moments -- `causes(A, B)` or `implies(A, B)` -- and
because it is a node, everything else about it is an ordinary fact. Direction is a
query over the rule, never a field in it: one statement, two readings.

Slice one carries the one-locus case only. An antecedent whose members all sit at
the same moment needs no skeleton, and the skeleton is what §8 adds for chains.
"""

from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

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
    ) -> None:
        self.node = node
        self.connective = connective
        self.antecedent = list(antecedent)
        self.consequent = list(consequent)
        self.name = name

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
    def __init__(self, g: Graph) -> None:
        self.g = g
        self.CAUSES = g.atom(CAUSES)
        self.IMPLIES = g.atom(IMPLIES)
        self.rules: List[Rule] = []
        # Authored precedence (§14): the bottom-most arbitrator is a lookup that
        # always returns and never searches.
        self.overrides: List[Tuple[Rule, Rule]] = []

    def rule(
        self,
        connective: str,
        antecedent: Sequence[Member],
        consequent: Sequence[Member],
        name: str = "",
    ) -> Rule:
        rel = self.CAUSES if connective == CAUSES else self.IMPLIES
        # The rule's two members are generic moments; here they are represented
        # by the patterns themselves, since slice one has no skeleton to relate.
        node = self.g.rel(rel, *[m.pattern for m in antecedent + list(consequent)])
        r = Rule(node, connective, antecedent, consequent, name)
        self.rules.append(r)
        return r

    def overrides_rule(self, higher: Rule, lower: Rule) -> None:
        self.overrides.append((higher, lower))


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


def substitute(g: Graph, pattern: NodeId, bindings: Dict[NodeId, NodeId]) -> NodeId:
    """Ground a consequent pattern. Anything still generic afterwards is a rule
    whose consequent names something its antecedent never bound, and the gate
    refuses it rather than minting a node nobody can read."""
    if g.is_var(pattern):
        return bindings.get(pattern, pattern)
    if not g.members(pattern):
        return pattern
    rel = g.relation_of(pattern)
    assert rel is not None
    return g.rel(rel, *[substitute(g, m, bindings) for m in g.members(pattern)])


# -- match ------------------------------------------------------------------


def current_state(chain: Chain, locus: Moment, seat: Moment) -> List[Entry]:
    """Every proposition the chain has an answer for at `locus`, as believed at
    `seat`, resolved to the one entry that governs it. This is the walk of §4,
    and it is the design's single most consequential cost."""
    props: List[NodeId] = []
    seen = set()
    for m in seat.ancestors():
        for e in m.delta:
            if e.proposition not in seen:
                seen.add(e.proposition)
                props.append(e.proposition)
    out = []
    for p in props:
        e = chain.resolve(p, locus, seat)
        if e is not None:
            out.append(e)
    return out


def match(
    g: Graph, chain: Chain, rule: Rule, locus: Moment, seat: Moment
) -> List[Application]:
    """Unify a generic moment against an anchored one, over the current state.

    Records which entries it matched. That is not overhead: it is what makes a
    misbehaving rule distinguishable from a misresolving chain.
    """
    state = current_state(chain, locus, seat)
    results: List[Application] = []

    def step(
        i: int, bindings: Dict[NodeId, NodeId], consumed: Tuple[Entry, ...]
    ) -> None:
        if i == len(rule.antecedent):
            results.append(Application(rule, bindings, consumed))
            return
        want = rule.antecedent[i]
        for e in state:
            if e.sign != want.sign:
                continue
            b = unify(g, want.pattern, e.proposition, bindings)
            if b is not None:
                step(i + 1, b, consumed + (e,))

    step(0, {}, ())
    return results


# -- arbitrate --------------------------------------------------------------


def arbitrate(rs: RuleSet, applications: Sequence[Application]) -> Optional[Application]:
    """Among the rules that matched, choose one. Total: it always answers.

    Authored precedence first, then the order rules were given in. The second is
    the table §14 requires -- a lookup that never searches, so no decision hangs.
    """
    if not applications:
        return None
    best = applications[0]
    for cand in applications[1:]:
        if _beats(rs, cand.rule, best.rule):
            best = cand
    return best


def _beats(rs: RuleSet, a: "Rule", b: "Rule") -> bool:
    if (a, b) in rs.overrides:
        return True
    if (b, a) in rs.overrides:
        return False
    return rs.rules.index(a) < rs.rules.index(b)


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
