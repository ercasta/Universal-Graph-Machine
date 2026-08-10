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

    Two steps, and they are not the same step.

    **Defeat first.** `overrides` is defeasibility (§12), not a ranking: a rule
    that is overridden by another rule *that also matched here* does not apply at
    all. Merely ordering them would let the loser apply on the following tick and
    overwrite the winner, so the boss's rule would be obeyed and then quietly
    undone by the vice's.

    **Then choose**, by the order rules were authored in -- the table §14
    requires, a lookup that never searches, so no decision hangs.
    """
    if not applications:
        return None
    best = applications[0]
    for cand in applications[1:]:
        if rs.rules.index(cand.rule) < rs.rules.index(best.rule):
            best = cand
    return best


def defeat(rs: RuleSet, applications: Sequence[Application]) -> List[Application]:
    """Drop the applications whose rule is overridden by another that matched.

    This runs on everything that **matched**, before any quiescence filter --
    and the order is load-bearing. Defeat is about whose antecedent holds, not
    about who still has work to do. Filter first and the winner disappears as
    soon as its conclusion is already written, whereupon the loser is
    unopposed and quietly overwrites it: the boss's rule obeyed once, then
    undone by the vice's on the following tick.
    """
    matched = [a.rule for a in applications]
    surviving = [a for a in applications if not _defeated(rs, a.rule, matched)]
    # A cycle in `overrides` would defeat everything. Arbitration must stay
    # total (§14), so fall back rather than answer nothing.
    return surviving or list(applications)


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
