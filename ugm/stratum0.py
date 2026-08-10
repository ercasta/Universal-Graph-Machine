"""Stratum 0 (§6): the rules that are applied without a read, and the read
written in them.

The bootstrap is that reading a rule requires applying rules. §6 closes it by
noticing that only one of the four steps of applying a rule is circular -- step
three, checking that the antecedent's entries hold -- and that the rules which
*implement* that check have a property none of the others has:

    Stratum 0 -- every antecedent member is structural. Applied without a read.

`pred`, `in_delta`, `delta_next` and the members of an entry node are all facts
about how the graph is built. Nobody asserted them; they cannot be denied, dated
or attributed. So matching them needs only the floor's substitution (§4 item 2),
and the rules below bottom out.

What this module is FOR is §20's floor gate: the rule-level definition of the
read must exist, and must agree with `Chain.resolve`. Until it does, `these are
conventions` is a claim about intent rather than a measured property.

It is deliberately slow. That is the point -- it is the interpreted path the
compiled one is checked against, and §4's *primitive is not native* is only
meaningful if both exist.

Two things this engine needs that the rule language of §12 does not yet have,
and both are honest costs rather than conveniences:

  * a body item may **capture the node it matched**, so a rule can refer to an
    entry and to its members at once. §12's notation already writes this
    (`?e1 = entry(?m, on(?x, ?y), +)`); nothing implemented it.
  * a body item may be **negated**. Selecting an extremum -- the latest locus --
    cannot be done with positive rules alone, and negation is safe here only
    because the strata are ordered: a negated item may name a relation only from
    a strictly lower stratum, so nothing is ever asked about a relation still
    being derived.
"""

from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

from .chain import Chain, Entry, Moment
from .graph import Graph, NodeId
from .rules import unify


class Ambiguous(Exception):
    """More than one candidate survived. The read has no answer, and saying so is
    the point: a silent choice among them would agree with the native walk
    whenever the two happened to enumerate in the same order."""


class Item(NamedTuple):
    """One antecedent member of a stratum-0 rule.

    `pattern` is a structure whose relation is known and whose members may be
    variables. `capture` optionally binds the matched node itself, which is what
    lets a rule name an entry and read its members in the same breath.
    """

    pattern: NodeId
    capture: Optional[NodeId] = None
    negated: bool = False


class S0Rule(NamedTuple):
    name: str
    stratum: int
    body: Tuple[Item, ...]
    head: NodeId  # a pattern; grounded by the bindings and minted


class Stratum0:
    """A forward-chaining engine over structural facts, evaluated in strata.

    Derived facts are ordinary interned relation instances, so a fixpoint is
    reached when a pass mints nothing new. They are *not* entries: stratum 0 may
    not deposit claims, or it would be reading entries in order to read entries
    and §6's circle would return. That is the price §6 states -- the read's own
    working state is undated and unattributed, so *why did you read it that way*
    is not answerable by the mechanism that answers *why do you believe that*.
    """

    def __init__(self, g: Graph, chain: Chain) -> None:
        self.g = g
        self.chain = chain

        v = g.var
        self.ANC = g.atom("anc")  # reflexive-transitive ancestry over moments
        self.SANC = g.atom("sanc")  # strict ancestry
        self.DEP_AFTER = g.atom("dep_after")  # deposited later, on one branch
        self.CAND = g.atom("cand")  # a candidate answer to a read
        self.BEATEN = g.atom("beaten")  # a candidate another candidate outranks
        self.BEST = g.atom("best")  # what the read returns

        m, p, a, x = v("?m"), v("?p"), v("?a"), v("?x")
        e, f, n, d = v("?e"), v("?f"), v("?n"), v("?d")
        seat, locus, prop, sign = v("?seat"), v("?locus"), v("?prop"), v("?sign")
        le, lf, se, sf = v("?le"), v("?lf"), v("?se"), v("?sf")
        pe, pf = v("?pe"), v("?pf")

        C, PRED, IND, DN, MOM = (
            chain, chain.PRED, chain.IN_DELTA, chain.DELTA_NEXT, chain.IS_MOMENT
        )
        rel = g.rel

        self.rules: List[S0Rule] = [
            # -- ancestry (stratum 1) --------------------------------------
            # Reflexive over every moment, so a history of one moment still
            # answers. Deriving reflexivity from `pred` alone would leave the
            # root unreachable in exactly that case.
            S0Rule("anc-self", 1, (Item(rel(MOM, m)),), rel(self.ANC, m, m)),
            S0Rule(
                "anc-step", 1,
                (Item(rel(PRED, m, x)), Item(rel(self.ANC, x, a))),
                rel(self.ANC, m, a),
            ),
            S0Rule("sanc-base", 1, (Item(rel(PRED, m, a)),), rel(self.SANC, m, a)),
            S0Rule(
                "sanc-step", 1,
                (Item(rel(PRED, m, x)), Item(rel(self.SANC, x, a))),
                rel(self.SANC, m, a),
            ),
            # -- deposit order (stratum 2) ---------------------------------
            # Across moments, ancestry decides. Within one, the delta chain does.
            S0Rule(
                "dep-across", 2,
                (
                    Item(rel(IND, m, e)),
                    Item(rel(IND, n, f)),
                    Item(rel(self.SANC, m, n)),
                ),
                rel(self.DEP_AFTER, e, f),
            ),
            S0Rule(
                "dep-within", 2,
                (Item(rel(DN, e, f)),),
                rel(self.DEP_AFTER, e, f),
            ),
            S0Rule(
                "dep-within-step", 2,
                (Item(rel(DN, e, x)), Item(rel(self.DEP_AFTER, x, f))),
                rel(self.DEP_AFTER, e, f),
            ),
            # -- candidates (stratum 3) ------------------------------------
            # An entry is a candidate answer when its deposit moment is on the
            # seat's walk AND its locus is at or before the moment asked about.
            # The second is inheritance, and it is why the locus cannot simply be
            # matched for equality (§10).
            S0Rule(
                "cand", 3,
                (
                    Item(rel(self.ANC, seat, d)),
                    Item(rel(IND, d, e)),
                    Item(rel(C.ENTRY, locus, prop, sign), capture=e),
                    Item(rel(self.ANC, locus, locus)),  # `?locus` ranges over moments
                ),
                rel(self.CAND, seat, locus, prop, e),
            ),
            # The clause above binds `?locus` to the entry's own locus. The read
            # asks about a moment that may be LATER than the entry's locus, so a
            # second clause carries inheritance forward down the chain.
            S0Rule(
                "cand-inherit", 3,
                (
                    Item(rel(self.CAND, seat, x, prop, e)),
                    Item(rel(self.SANC, locus, x)),
                ),
                rel(self.CAND, seat, locus, prop, e),
            ),
            # -- who loses (stratum 4) -------------------------------------
            # Latest locus first.
            S0Rule(
                "beaten-locus", 4,
                (
                    Item(rel(self.CAND, seat, locus, prop, e)),
                    Item(rel(self.CAND, seat, locus, prop, f)),
                    Item(rel(C.ENTRY, le, pe, se), capture=e),
                    Item(rel(C.ENTRY, lf, pf, sf), capture=f),
                    Item(rel(self.SANC, lf, le)),
                ),
                rel(self.BEATEN, seat, locus, prop, e),
            ),
            # Then latest deposit, and only then.
            S0Rule(
                "beaten-deposit", 4,
                (
                    Item(rel(self.CAND, seat, locus, prop, e)),
                    Item(rel(self.CAND, seat, locus, prop, f)),
                    Item(rel(C.ENTRY, le, pe, se), capture=e),
                    Item(rel(C.ENTRY, le, pf, sf), capture=f),  # same locus `?le`
                    Item(rel(self.DEP_AFTER, f, e)),
                ),
                rel(self.BEATEN, seat, locus, prop, e),
            ),
            # -- the answer (stratum 5) ------------------------------------
            S0Rule(
                "best", 5,
                (
                    Item(rel(self.CAND, seat, locus, prop, e)),
                    Item(rel(self.BEATEN, seat, locus, prop, e), negated=True),
                ),
                rel(self.BEST, seat, locus, prop, e),
            ),
        ]

    # -- evaluation --------------------------------------------------------

    def run(self) -> int:
        """Evaluate every stratum in order, each to fixpoint. Returns the number
        of derived facts, which is the cost this path pays for being readable."""
        derived = 0
        for s in sorted({r.stratum for r in self.rules}):
            layer = [r for r in self.rules if r.stratum == s]
            while True:
                added = 0
                for r in layer:
                    for b in self._solve(r.body, 0, {}):
                        node = self._ground(r.head, b)
                        if node is not None:
                            added += 1
                if not added:
                    break
                derived += added
        return derived

    def _solve(
        self, body: Sequence[Item], i: int, b: Dict[NodeId, NodeId]
    ) -> List[Dict[NodeId, NodeId]]:
        if i == len(body):
            return [b]
        item = body[i]
        rel = self.g.relation_of(item.pattern)
        assert rel is not None
        if item.negated:
            # Safe only because of the strata: a negated item names a relation
            # from a lower stratum, which is already at fixpoint.
            for node in self._facts(rel):
                if unify(self.g, item.pattern, node, b) is not None:
                    return []
            return self._solve(body, i + 1, b)
        out: List[Dict[NodeId, NodeId]] = []
        # If the captured node is already bound, there is exactly one candidate.
        # That is what turns `?e = entry(?l, ?p, ?s)` from a scan into a lookup.
        bound = b.get(item.capture) if item.capture is not None else None
        candidates = [bound] if bound is not None else self._facts(rel)
        for node in candidates:
            nb = unify(self.g, item.pattern, node, b)
            if nb is None:
                continue
            if item.capture is not None and bound is None:
                if item.capture in nb and nb[item.capture] != node:
                    continue
                nb = dict(nb)
                nb[item.capture] = node
            out.extend(self._solve(body, i + 1, nb))
        return out

    def _facts(self, rel: NodeId) -> List[NodeId]:
        """Anchored instances only. The rules' own patterns are instances of the
        same relations and are indexed beside the facts, so the anchored/generic
        split of §7 is what tells a fact from the pattern that looks for it --
        *match is unifying a generic structure against an anchored one*, and this
        is that sentence being load-bearing rather than descriptive."""
        return [n for n in self.g.instances_of(rel) if not self.g.has_var(n)]

    def _ground(self, head: NodeId, b: Dict[NodeId, NodeId]) -> Optional[NodeId]:
        """Mint the head, and report whether it was new. Interning is what makes
        the fixpoint detectable: a fact already derived mints no node."""
        rel = self.g.relation_of(head)
        assert rel is not None
        members = []
        for m in self.g.members(head):
            g = b.get(m, m)
            if self.g.is_var(g):
                return None
            members.append(g)
        before = self.g.count()
        self.g.rel(rel, *members)
        return None if self.g.count() == before else 1

    # -- the read, as this engine answers it -------------------------------

    def resolve(
        self, proposition: NodeId, locus: Moment, seat: Optional[Moment] = None
    ) -> Optional[NodeId]:
        """The entry node the rule-level read returns, or None.

        Compare with `Chain.resolve`, which returns the same answer by walking in
        Python. That comparison is §20's floor gate.
        """
        if seat is None:
            seat = self.chain.moments[-1]
        found = [
            self.g.members(n)[3]
            for n in self._facts(self.BEST)
            if self.g.members(n)[:3] == (seat.node, locus.node, proposition)
        ]
        if len(found) > 1:
            # Never pick the first. A read answers with *one* entry, so several
            # unbeaten candidates means the ordering rules are incomplete -- and
            # taking the first would hide exactly that, agreeing with the native
            # walk by luck of enumeration order. Deleting the deposit tiebreak
            # was invisible until this raised.
            raise Ambiguous(
                f"{len(found)} unbeaten candidates for {self.g.show(proposition)} "
                f"at {locus} from {seat}"
            )
        return found[0] if found else None
