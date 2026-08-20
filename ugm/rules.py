"""Rules (§8), matching and arbitration (§14).

A rule is a fact relating two moments -- `causes(A, B)` or `implies(A, B)` -- and
because it is a node, everything else about it is an ordinary fact. Direction is a
query over the rule, never a field in it: one statement, two readings.

Slice one carries the one-locus case only. An antecedent whose members all sit at
the same moment needs no skeleton, and the skeleton is what §8 adds for chains.
"""

from typing import Callable, Dict, List, NamedTuple, Optional, Sequence, Tuple

from .chain import Chain, Entry, MINUS, Moment, Span, scope_of
from .graph import Graph, NodeId

CAUSES = "causes"
IMPLIES = "implies"


class _Stop:
    """The postcondition that ends the run, as a sentinel rather than a node.

    ⭐ `boost` and `damp` move a score, `reset` returns the table to its
    defaults, and this stops. All four are what an applied rule SPENDS, so all
    four are rows in one vocabulary rather than branches -- which is the test
    this design applies to connectives and applies here for the same reason.

    ⚠ Deliberately not `g.atom("stop")`. A corpus may name a rule `<stop>`, and
    a reserved atom would make the verb and the rule one node with two meanings
    -- the twin trap, which this repository has now recorded seven times. A
    sentinel cannot collide with anything a corpus can write.

    ⚠ And it is not a *score*. The design's line about norms applies exactly:
    a thing that must not be outweighed is a premise, never a number. Stopping
    is decided by the rule's own antecedent -- the query that had to hold for
    the postcondition to run at all -- and never by outranking anybody.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return "stop"


STOP = _Stop()


class Attend:
    """The postcondition that deposits attention on what the move just bound.

    ⭐⭐⭐ **The sixth row in the same vocabulary, and it is a different KIND of
    row.** `boost` and `damp` move a score, `reset` returns the table to its
    defaults, `stop` ends the run -- all four are the loop's own bookkeeping.
    This one deposits an ordinary CLAIM, which nothing a postcondition could
    spend has done before.

    ⚠ That is the point rather than a wrinkle. Attention is a fact about a node
    -- readable by rules, deniable, attributable, dated -- and a postcondition is
    the only place a lesson about it can live. `docs/HANDOFF.md` 2026-08-15
    measured why: a learned recogniser written as a RULE has to win a move to be
    heard and fired twice out of sixteen, because *in a one-move-per-tick loop,
    spending a move on recognition competes with doing the work*. A
    postcondition is evaluated for free after whatever applied.

    ⚠ So the deposit is NOT the table's business, and this file's sentinel is
    where it stops: `Table.spend` stays a pure account of scores and the loop
    hands attends to the machine. A table that could write claims would be an
    interpreter with a memory, which is the thing the four primitives exist
    instead of.

    ⚠ A class rather than a sentinel because it carries the term to attend to,
    which `stop` and `reset` do not. `term` is a node once the loader has built
    it, and the parser's own term before that.
    
    ⭐⭐⭐ **And it carries a WEIGHT, which is what a learned buff now is.**
    `attend(?x, 3)` says *of the things this move touched, THAT one matters* --
    a multiplier on a node's place in the attention queue rather than a number
    added to some other rule's score.

    That is the whole of the retirement `prefer` and `boost` were blocking: a
    calibration that names a NODE goes stale for nothing, where one naming
    `<R>` goes stale the moment a rule is adopted, composed or renamed. And it
    is the differentiation the queue's position alone cannot supply, because
    everything one move wrote arrives at the same instant.
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
    # ⭐ WHERE the entry must sit, as a pattern to bind (§8, §12). Defaulted, so
    # every construction site that does not care is untouched -- which is the
    # whole reason a NamedTuple was the right shape for a member.
    #
    # §12 says a member IS an entry and the short form is an abbreviation whose
    # locus the frame supplies. That was true of the document and false of the
    # engine: there was nowhere to put a locus, so *the goblin acts after the
    # hero* was unwritable and a foreign corpus spent 24% of itself
    # re-implementing a moment ordinal as a round counter.
    #
    # ⚠ The matcher had the locus all along -- every `Entry` carries one. What
    # was missing was a pattern for it, which is the third time this session a
    # wall turned out to be information nothing looked at.
    locus: Optional[NodeId] = None
    # ⭐ ...and a name for WHAT matched. `at ?m` says where the entry sits; `as
    # ?t` says what its proposition is, so a rule can refer to the very thing it
    # matched rather than describing it again.
    #
    # Without it a corpus reaches the same place by reconstruction -- match
    # `+?r(?x, ?y)` and rebuild `?r(?x, ?y)`, which interning makes the SAME
    # node, so it is genuine reference rather than a copy. That works and costs
    # §3's index, because a variable relation has no bucket. This keeps the
    # index and says the thing directly.
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
        # `STOP` (below) may appear as a trigger's target. It is a sentinel and
        # not a node on purpose: a rule named `stop` must go on meaning that
        # rule, and encoding the verb as a reserved atom is the twin trap in its
        # cheapest form -- one name, two meanings.
        # Authored precedence (§14): the bottom-most arbitrator is a lookup that
        # always returns and never searches.
        # ⭐⭐⭐ **Precedence is READ, not kept.** These were two Python lists,
        # seeded by the loader once and unreachable from the graph -- so a rule
        # could conclude `overrides(A, B)`, the fact would hold, and the
        # arbitrator would never look. Now `precedence()` reads what the graph
        # claims, at the position the agent is standing, exactly as `_recall`
        # reads `dormant`/`due`. That makes it **dated, deniable and about a
        # rule that may not have existed yet** -- and it deleted a write hook,
        # a re-scan on adoption, two seeders and a loader method.
        #
        # Measured before deleting, because the previous version was kept for
        # speed: the whole suite runs in **6.42s against 6.38s**. The table was
        # buying nothing.
        #
        # Set by the Machine, which owns the nodes and the position. Unset, a
        # bare RuleSet has no precedence, which is what a RuleSet with no world
        # to read should say.
        self.OVERRIDES: Optional[NodeId] = None
        self.SUPERSEDES: Optional[NodeId] = None
        self.claims: Optional[Callable[[NodeId], object]] = None
        # Relations that are COMPUTED rather than matched (§12's skeleton).
        # Set by the Machine, which owns the registry; a bare RuleSet has none,
        # which is what a rule set with no host functions should say.
        self.computes: Dict[NodeId, Callable] = {}
        # ...and relations that are READ OFF THE CHAIN rather than matched --
        # `pred`, `sanc`. §12 calls these the skeleton: *no sign, no locus, no
        # licence; nobody asserted them*. They are structure, so they are not
        # entries, so the state does not hold them -- which is why an ordinary
        # rule could never see one and stratum 0 needed a second matcher.
        #
        # ⭐ Given an ANCHORED moment they generate upward, and upward on a tree
        # is single-valued (§11), so a structural member cannot reach a sibling
        # branch. **Containment stays structural rather than becoming enforced**:
        # nothing is refused, a downward pattern simply finds nothing, exactly as
        # a rule matching an entry nobody wrote finds nothing.
        self.structural: Dict[NodeId, Callable] = {}
        # ...and the CLOSURE of that under §6's test, cached. See `skeleton`.
        self._skeleton: Optional[Dict[NodeId, Callable]] = None
        self.by_node: Dict[NodeId, "Rule"] = {}
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
        # ⚠⚠⚠ **A caller may supply the node, and `adopt` must.** A rule the
        # graph describes is already a node -- a corpus concluded `ant(<R>,
        # ...)` about it, and `<R>` is what any precedence, any `defeated`
        # record and any later claim will name. Minting a fresh node here made
        # the live rule a TWIN of the described one: everything a corpus had
        # said about it went to a node that was not a rule, and everything the
        # machinery said about it named a node no corpus could reach. Found by
        # a standing policy that ordered a learned rule and quietly did
        # nothing. The twin trap, eighth time.
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
        claim: the chain's own (`self.structural`) plus whatever a stratum-0
        rule concludes.

        ⭐⭐⭐ **The strata are derived, not assigned.** §6 defines stratum 0 as
        *a property of a rule* -- every antecedent member is structural --
        decided *by inspecting an antecedent rather than by a designer assigning
        layers*. That is computable, so it is computed: start from what the
        chain deposits, and add the conclusions of every rule that reads only
        those. Monotone, so it converges; and because it is a fixpoint from
        BELOW, a relation is structural only if something grounded in the chain
        makes it so. A cycle of rules concluding about each other adds nothing.

        ⚠ Recomputed when a rule is added, because `adopt` means the rule set
        moves at run time and a stratum a rule was classified into before it
        existed is a stale answer. Cached because `match` asks per member.
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

        ⚠⚠⚠ **Negation makes the ORDER load-bearing, and structure cannot be
        taken back.** `best` is *a candidate nothing beats*. Applied before
        `beaten` has finished deriving, it mints a fact that is wrong and that
        nothing can deny -- a skeleton fact has no sign, which is the whole
        point of it. An entry would merely be superseded; this is permanent. So
        the layers are not a convenience, they are what makes the negation mean
        what it says.

        Standard stratification, and it is DERIVED like everything else here:
        a relation's layer is at least that of every relation a rule reads to
        conclude it, and strictly greater than that of any relation it reads
        NEGATED. Chain relations are layer 0. Iterated to a fixpoint, with a
        ceiling: if the layers keep rising, the rules negate each other in a
        cycle and there is no stratification to find.

        ⚠ Refused loudly rather than run in some order that happens to work.
        An unstratifiable set gives a different answer depending on the order
        the rules are tried, and this is the one component whose whole purpose
        is to agree with the walk on every look.
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

        ⭐⭐⭐ **And guard inheritance is COMPLETE, which this docstring spent
        several commits apologising for.** It said `unless` is not implemented
        anywhere in this engine, so the half of guard inheritance §12 describes
        cannot be carried. That was false, and the mistake was a NAME: `unless`
        is *if not*, and *if not* is an ordinary negated antecedent member.
        Composition takes the **union of the antecedents**, so a guard is
        inherited by construction rather than by a mechanism -- verified from
        either constituent, and verified as behaviour and not only as structure,
        since a member carried and not obeyed is `adopt`'s own defect.

        ⚠ What is genuinely absent is **amendment at a distance** -- adding a
        guard to a rule you did not write -- and calling that `unless` is what
        made a one-member rule look like a missing language feature. It is now
        refused by decision rather than open by omission: an ordinary rule may
        not reach into another rule's application (§5's wall), and amending a
        rule belongs to harmonization, where the agent authors a better rule
        through `adopt` and the amendment is itself an arguable claim.

        ⭐ **The grade used to block this.** §21 argued that composing one would
        be a minimum computed once from constituents that are themselves
        defeasible -- a cache of a derived value, §16's objection one level up --
        so composition refused anything but `certain`. With grades gone the
        objection goes with them: an uncertain conclusion is `+likely(p)`, an
        ordinary consequent pattern, and composing it is composing a pattern.
        The restriction was deleted rather than solved.
        """
        # ⚠⚠⚠ **Composing across a `causes` FLATTENS TWO MOMENTS INTO ONE
        # ANTECEDENT, and it loses conclusions.** §14: a `causes` consequent
        # lands in a SUCCESSOR, so the second rule's other premises are read
        # where the first rule's effect holds -- one moment later than the
        # first rule's own premises. The composite asks for all of them
        # together, which is a different and stricter question.
        #
        # Measured, on `causes({+p}, {+q})` then `implies({+q, +r}, {+s})`:
        #
        #   | r holds from the start        | derivation `s` | composite `s` |
        #   | r appears only AFTER p        | **True**       | **False**     |
        #
        # The composite under-derives -- the safer direction, and still a
        # violation of §4's claim that *n* steps become one **with the same
        # conclusion**. An over-derivation was looked for and not found, which
        # is not the same as it being impossible.
        #
        # ⭐ This is why the mixed-connective question was the wrong one. What
        # looked like *which connective should a mixed composition get* is
        # really *some compositions must not happen at all*; and once the
        # unsound ones are refused, the connective is FORCED rather than chosen
        # -- a chain that crosses a causal step has advanced a moment, so the
        # result is `causes`, by §14's own persistence test.
        #
        # The condition is exact rather than cautious: only members BEYOND the
        # seam are relocated, so a second rule whose antecedent is just the
        # seam composes soundly across a `causes` and is allowed. Refusing is
        # `None`, which this door already means as *I have nothing to say*.
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
    # ⭐⭐⭐ **Identity, at BIND TIME** -- and without this the rest of the
    # identity layer is half a feature. `merge` repoints the indices, so after
    # merging `debt` into `owes` a rule reading `+owes(?x, ?y)` is OFFERED
    # `debt(zeta, 900)` by the argument index and then rejects it here, because
    # a node's own `_rel` field still says `debt`. Candidates found and thrown
    # away: the rule matches nothing, reports nothing, and looks like a corpus
    # bug. Measured exactly that way before this line existed.
    #
    # ⚠ Guarded on `_merges`, so a corpus that never corefers compares two ints
    # as it always did. `identity_of` is called on the hottest path in the
    # engine and it has to cost nothing until something has merged.
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
        # ⭐ **A variable in the RELATION slot.** The substrate has always been
        # able to build `?p(?x)` -- it is a node whose relation happens to be a
        # variable -- and this is the line that decided it could never match.
        # Binding it is what makes *apply the effect named by this ability* a
        # rule rather than one fact per (ability, target) pair.
        #
        # ⚠ It costs §3's only index: a pattern whose relation is unknown has no
        # bucket, so `Situation.candidates` falls back to the ANY bucket and
        # scans. That is the same trade the design already takes for a
        # bare-variable pattern, and it is why this is allowed rather than
        # encouraged -- §12 says the same of a bare-variable consequent.
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

    The **dual of `unify`**, and the operation *learn from examples* is made of:
    matching asks what two structures have to agree about, and this asks what
    they already agree about. `unify_patterns` is the two-sided version of the
    first; nothing was the second, so an agent could recognise an instance of a
    rule it had and never propose the rule from the instances.

    ⭐⭐⭐ **`mapping` is the whole of it, and it is why this takes one.** The
    same disagreement must produce the same variable *everywhere it appears*,
    including across the two structures a caller generalises in turn. Without
    that, `f(a, a)` and `f(b, b)` generalise to `f(?1, ?2)` -- true, useless,
    and strictly more general than the answer -- and a premise and a conclusion
    generalised separately share no variable at all, so the rule built from them
    concludes about something nothing binds. That is the crux of building a rule
    out of two examples, and it is one dictionary.

    ⚠ What agrees is KEPT. `f(a, b)` and `f(a, c)` give `f(a, ?1)`, never
    `f(?1, ?2)`: an implementation that variabilises everything returns a
    generalisation, just not the least one, and the rule it yields fires on
    everything.
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

    ⚠⚠⚠ **`substitute` interns, so asking with it changes the answer.** For an
    ordinary conclusion that is harmless -- a proposition nobody has claimed
    anything about is inert, and quiescence goes on to ask the CHAIN about it.
    For a stratum-0 conclusion the node's existence *is* the fact, so
    quiescence asking *would this change anything* by building the thing made
    the answer no, permanently, for whoever asked next.

    That surfaced as `ugm.arbitration` reporting the fast path choosing a move
    the slow path then found nothing to do -- **two paths over one state, where
    the first one's question consumed the second one's answer.** A predicate
    with a side effect, and this is the predicate without one.

    Three answers, and they have to be three: `GENERIC` when the consequent is
    still open (it mints nothing and changes nothing), `None` when it is ground
    and not yet derived (it would change something), and the node when it is
    already there. Collapsing the first two sends the caller back to
    `substitute` to tell them apart, which is the mint this exists to avoid.
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


def current_state(chain: Chain, locus: Moment, seat: Moment) -> List[Entry]:
    """Every proposition the chain has an answer for at `locus`, as believed at
    `seat`, resolved to the one entry that governs it. This is the walk of §4,
    and it is the design's single most consequential cost."""
    # ⚠ Keyed by proposition AND by the span it is about (`scope_of`): two
    # recognitions over different stretches supersede nothing of each other, so
    # each is asked about separately. On a chain of moments the scope is always
    # `None` and this is the walk it always was.
    keys: List[Tuple[NodeId, Optional["Span"]]] = []
    seen = set()
    for m in seat.ancestors():  # newest moment first
        for e in reversed(m.delta):  # ...and newest within a moment
            k = (e.proposition, scope_of(e.locus))
            if k not in seen:
                seen.add(k)
                keys.append((e.proposition, e.locus if k[1] is not None else None))
    out = []
    for p, span in keys:
        if span is None:
            e = chain.resolve(p, locus, seat)
        elif locus.at_or_after(span):
            # A stretch that is not over yet is not yet anything to read.
            e = chain.resolve(p, span, seat)
        else:
            e = None
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

    ⭐⭐⭐ **And by ARGUMENT POSITION, which is the second index and a different
    quadratic.** Keyed on the relation alone, a member that has already bound
    one of its arguments still draws every instance of that relation and unifies
    each: `{ +child(?p, ?x), +child(?x, ?y) }` over N facts is N candidates for
    each of N bindings, so **one tick costs 2N² unifications** with no option set,
    no arbitration and no candidate walk involved. Reported from `pystrider`,
    who measured it as the shape their whole corpus has -- *a broad structural
    join over one relation is not a corner of what recognition does, it is what
    recognition IS* -- and reproduced here before anything was changed.

    So an entry is also filed under each of its arguments: `(sign, relation,
    position, node)`. A member whose argument is bound looks there instead, and
    the join becomes O(N × matches).

    ⚠ **Only when the argument is an ATOM**, and that is soundness rather than
    conservatism. `unify` compares a ground *structure* member-by-member, so it
    accepts a structurally equal node that is not the same node -- the twin
    trap, which this repo has recorded six times -- and an index keyed on
    identity would silently drop those. An atom has no members and no relation,
    so `unify` reduces to identity for it and the bucket is exactly the set that
    could match.

    ⭐ **The narrowing keeps the ORDER**, which is why nothing else had to change:
    every candidate it removes is one `unify` would have rejected, so the
    matching candidates and their sequence are identical. `pystrider` flagged
    picking the narrowest MEMBER as the risky part -- it reorders the antecedent,
    and §18's tiebreaks read the consumed entries -- and it is not needed: the
    narrowing is per member, in the authored order.
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
        # ⭐⭐⭐ **The third index, and it is the one attention needs: which
        # RELATIONS a node is currently spoken of under.**
        #
        # The two above are read by a pattern that already knows its relation.
        # Attention arrives from the other end -- it has a NODE and no relation
        # at all -- so neither answers it, and the question *which rules could be
        # about `goblin1`* has no cheap answer without this. With it: the node's
        # relations are a lookup, and the rules using those relations are a
        # second one, so a lift costs two dict reads and no matching. That is
        # what makes attention cheaper than the reranker it competes with, whose
        # every trigger is a match.
        #
        # ⚠ **Counted, not a set**, because `drop` has to be exact. Two entries
        # can mention one node under one relation, and dropping either would
        # take the relation away from a node the other still speaks of.
        #
        # ⚠ It is maintained off the SAME keys the argument index files under,
        # which is what keeps it honest: it indexes what that index indexes, and
        # `ugm.state` holds it to a rebuild. So it inherits that index's own
        # limit -- an argument that is a structure is not filed, and neither is
        # it here.
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
            # ⚠ Atoms here too, and for the same reason read from the other end:
            # the only thing that ever looks in one of these buckets is a
            # pattern member that is an atom, and an atom cannot equal a
            # structure. Filing the structured members as well is a bucket per
            # deposit that nothing can ever read -- worth 4% of the suite
            # (6.60s against 6.33s), which is small and is the whole of it: I
            # first wrote 15% here from two runs that differed in another way
            # as well, and the A/B says otherwise.
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
    locus: Moment,
    seat: Moment,
    state: Optional["Situation"] = None,
    fresh: Optional["Situation"] = None,
    computes: Optional[Dict[NodeId, Callable]] = None,
    structural: Optional[Dict[NodeId, Callable]] = None,
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

    ⭐⭐⭐ **And the pivot is walked FIRST**, which is what makes the delta pass
    cost what the delta costs. Walked in authored order, a pass pivoting on
    member 1 draws member 0 from the whole state before it ever reaches the
    delta -- so a corpus deriving one fact per tick pays O(state) per tick and
    the join is quadratic again, in the one shape `Situation`'s argument index
    cannot help with. Measured: 4,994,004 unifications over a 1,000-node tree,
    of which the index removed a third and the ordering removed the rest.

    ⚠ **What may be reordered is the WALK, never the antecedent.** `consumed` is
    filled by member position, so §12's trail and `heap`'s stamp -- which reads
    the consumed entries' nodes -- see exactly what authored order would have
    given them. What does change is the order applications are *discovered* in,
    and that is measured not to be load-bearing: since `heap` nothing reads it,
    and `ugm.arbitration` compares the move on every tick of every fixture.
    """
    if state is None:
        state = Situation(g, current_state(chain, locus, seat))
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
                #
                # ⭐⭐⭐ **A MINUS here is negation as failure, and it needs no
                # notation.** On an ordinary member the sign says what an entry
                # claims; a structural member has no entry, so the only thing a
                # sign can mean is *this was not derived*. `-beaten(...)` is
                # exactly `stratum0`'s `Item(negated=True)`, written in the
                # surface a corpus already has.
                #
                # ⚠⚠⚠ Safe only because the strata are ORDERED. §6's fixpoint
                # is built from below, so a negated member names a relation
                # whose derivation is finished before this rule is reached --
                # and `_settled` below is what makes that true of the run and
                # not only of the classification. Negating a relation still
                # being derived would answer from a half-built extension, which
                # is the one way a rule-level read could disagree with the walk
                # non-deterministically.
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
                # ⭐ **A computator: evaluated, not matched.** §12's skeleton is
                # *conditions on the binding that claim nothing* -- distinctness
                # is already one -- and arithmetic is exactly that. Evaluating
                # it HERE is what makes an application atomic: the result is
                # available to the same consequent, in one moment, so a transfer
                # cannot be caught half-done (§22).
                #
                # ⚠ The arguments must be ground by now. A member whose
                # arguments are still open computes nothing and matches nothing,
                # rather than guessing -- and the pivot never lands on one (see
                # `run`), so authored order is what decides.
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
                if b is not None and want.locus is not None:
                    # The entry knows where it sits; bind the pattern to it.
                    b = unify(g, want.locus, e.locus.node, b)
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

    ⭐⭐⭐ **This is where containment stays structural.** The first argument must
    already be bound: from an anchored moment we walk toward the root, and §11
    guarantees that walk is single-valued -- *a moment has one parent; forking
    produces several successors, never several parents.* So a structural member
    can only ever name moments on the frame's own walk, and a rule inside a
    hypothesis cannot reach a sibling.

    Nothing is refused to make that true. A pattern that would need to walk
    DOWNWARD -- an unbound first argument -- simply yields nothing, in the same
    way a rule matching an entry nobody wrote matches nothing. §4's *nothing is
    prohibited* survives, and an author who genuinely wants another frame's
    chain has §17's door: inspecting is matching, with an explicit anchor.
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
        # `n` was a variable and this is its VALUE -- a thing the match has
        # already found, so it anchors this member however generic what is
        # INSIDE it may be. Recursing further asks whether some other rule's
        # pattern, quoted inside an entry about a rule, is ground; it is not,
        # and answering no refused the walk an anchor it had. That is what kept
        # deposit order from crossing a reified entry: `in_delta(?m, ?e)` bound
        # `?e` to such an entry, and `delta_next(?e, ?f)` then found no anchor
        # and enumerated nothing (docs/observations.md Part 6.3).
        return True
    rel = g.relation_of(n)
    if rel is not None and not _ground(g, rel, bindings):
        return False
    return all(_ground(g, m, bindings) for m in g.members(n))


def _stored(g, chain, want, bindings):
    """A skeleton relation that is IN the graph -- `pred`, `in_delta`,
    `delta_next`, `rests_on`, and whatever a stratum-0 rule concludes --
    matched by unifying against its ground instances.

    ⭐⭐⭐ **This is the whole of the second matcher, and it is four lines.**
    `stratum0._facts` read exactly this: the ground instances of a relation,
    told apart from the patterns that look for them by §7's anchored/generic
    split. A separate engine was never needed to do it; the relations simply
    were not in the resolved state, which is what `match` was being handed.

    ⚠⚠ **At least one argument must be bound**, and the discipline is *bounded
    by something already known* rather than *bounded by a named position*. My
    first version fixed the anchor at argument 0, which reads `in_delta` only as
    *a moment's entries* -- and deposit order across moments needs it the other
    way, as *an entry's moment*. Both directions are bounded; neither
    enumerates the history.

    ⚠⚠⚠ **This is weaker than `_anchored`'s guarantee and the difference is
    worth stating.** An upward walk cannot reach a sibling branch *whatever* is
    bound (§11: one parent, several successors). Here containment holds
    COMPOSITIONALLY instead -- the binding that anchors this member came from
    somewhere, and if that somewhere was on the frame's walk so is this. The
    forking-chain check is what holds it, and it is a measurement rather than a
    construction now. Recorded, not hidden.
    """
    rel = g.relation_of(want.pattern)
    args = g.members(want.pattern)
    # ⚠⚠⚠ **GROUND, not merely not-a-variable.** This asked `is_var`, which is
    # False for any relation instance -- so `licensed_by(?e, loaded(?p))` counted
    # `loaded(?p)` as an anchor although nothing in it was known, and the walk
    # enumerated every instance in the history. That is exactly the leak the
    # paragraph above says this line prevents, available to any corpus writing a
    # structured argument: `rests_on(?e, foo(?p))`, `in_delta(?m, bar(?x))`.
    #
    # `has_var` is not the test either, because it cannot see through bindings:
    # `loaded(?p)` with `?p` already bound is ground in fact and generic in
    # shape, and refusing it would break the anchored reads §12 relies on. So
    # the question is asked of the binding, recursively. Measured:
    # docs/observations.md §3.1, finding 2.
    if not any(_ground(g, a, bindings) for a in args):
        return  # unbounded: this would enumerate the history, so it finds nothing
    for node in _narrowed(g, rel, want, bindings):
        b = _as_fact(g, want, node, bindings)  # a pattern is not a fact (§7)
        if b is not None:
            yield b



def _holds_at(g, chain, want, bindings):
    """`holds_at(?p, ?m, ?sign)` -- what a proposition RESOLVED TO at a moment.

    §12's `at ?m` binds the LOCUS OF THE ENTRY THAT SATISFIED a member, and the
    resolved state keeps one entry per proposition -- the winner. So a corpus
    can say *the goblin acted after the hero* (two propositions, two loci) and
    cannot say *p held then and does not now* (one proposition, two times): the
    earlier claim is not in the state to be matched against. Probed: `?then`
    bound to a real moment where `ill(paul)` held, and `+ill(?x) at ?then` still
    matched nothing.

    `Chain.resolve` has always answered the question. What was missing was any
    way for a rule to say WHICH LOCUS TO RESOLVE AT, and this is it.

    **The seat is the moment itself**, so the answer is *as believed AT that
    moment* rather than *as believed now about that moment*. That is the
    situation reading -- what the world looked like from there -- and it is the
    only one available, because a structural walker is handed no seat. The other
    question is a different relation and should say so in its name rather than
    quietly meaning something else.

    Containment holds compositionally, as it does for `_stored`: `?m` can only
    be bound by a walk the frame could make, so a moment on a sibling branch is
    unreachable to bind in the first place.

    ⚠ Nothing is minted. Building the answer as a node and unifying against it
    would intern it, and the harness's question would then be findable as its
    own answer -- the interning trap's fourth face. Only the sign slot can need
    binding, so it is bound by hand.
    """
    args = g.members(want.pattern)
    if len(args) != 3:
        return
    prop = substitute(g, args[0], bindings)
    if g.has_var(prop):
        return  # the proposition is not yet ground: nothing to resolve
    mnode = walk(g, args[1], bindings) if g.is_var(args[1]) else args[1]
    if g.is_var(mnode):
        return  # unanchored: this would ask about every moment there is
    moment = chain.moment_of(mnode)
    if moment is None:
        return
    entry = chain.resolve(prop, moment, moment)
    if entry is None:
        return  # nothing was ever claimed about it there, which is not a denial
    sign = chain.SIGN[entry.sign]
    slot = args[2]
    current = walk(g, slot, bindings) if g.is_var(slot) else slot
    if g.is_var(current):
        out = dict(bindings)
        out[current] = sign
        yield out
    elif current is sign:
        yield dict(bindings)


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
    index instead of every instance of the relation.

    The pivot is the bound argument with the FEWEST instances, which is the same
    choice the entry side makes and for the same reason: a join is not a scan.
    An argument counts as bound if it is a value already -- an atom or a
    structure written in the pattern -- or a variable this match has bound.
    With none bound the answer is what it always was, every instance, and
    `_stored`'s anchor rule refuses that case before it is reached.

    A STRUCTURE THAT STILL CARRIES A VARIABLE IS NOT A VALUE, and reading it as
    one is the interning trap wearing an index. `said(implies(?a, ?c))` asks the
    bucket for the pattern node `implies(?a, ?c)` itself -- a node the graph
    minted when the rule was authored, which nothing was ever an instance
    against -- so the bucket is empty and the member matches NOTHING. No error,
    no scan, no candidate: the rule is well formed, every other member is fine,
    and it silently never applies. Found while writing an interpreter for
    rules-as-facts, where every member has this shape; a corpus that only ever
    writes atoms in argument positions cannot reach it, which is why 549 checks
    could not.

    Skipping it falls back to `instances_of`, which is the answer this function
    already gives when nothing is bound -- so the cost is the scan the docstring
    above already sanctions, paid only by a member that could not be indexed
    anyway.

    ⭐⭐⭐ **...and the fallback SAYS SO, which is
    `docs/interpretation-feedback.md` §3.** The paragraph above sanctions the
    cost and is silent about the count, and those are different things: an
    author cannot tell a member that joins from a member that scans, because
    both are well formed, both find the right answers, and only one of them is
    the difference between a parse and a hang on a corpus whose members are
    pattern-heavy by construction. The information exists exactly here, at the
    point where it was being discarded.

    ⚠ Counted on the GRAPH rather than reported by return value, because this
    is a generator's inner loop reached through two structural readers that have
    no report to write on and no rule in hand. Keyed by the member as written,
    which is what an author has to go and change.

    ⚠⚠ **Both the count and the SIZE, because the count alone does not rank
    them.** Measured on `ugm.interpret`: `asking(?s)` falls back 169 times and
    `met(?a)` 16, which reads as one problem and one footnote -- and `asking`
    has a single instance, so those 169 fallbacks visit 169 nodes between them
    while the 16 walk a bucket that grows with the run. A member that cannot be
    indexed over a relation with one instance costs nothing and is not worth an
    author's afternoon. What was being discarded here is the join that did not
    happen; what decides whether that matters is how big the scan was.
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
    candidate is a FACT rather than a pattern.

    §7 splits generic from anchored, and this seam asked it as `has_var` over
    the whole candidate node. That is the wrong question for a chain-deposited
    relation, and the cost was measured: a reified rule is deposited as a
    mention, so its proposition is the rule's pattern, so the entry node carries
    that pattern's variables -- and with them every `mentioned`, `in_delta` and
    `delta_next` fact about it. On one four-line corpus, 97 of 125 `mentioned`
    facts and 175 of 216 `delta_next` facts were invisible to the matcher,
    although the chain deposited every one of them and nobody authored any of
    them as a pattern. `delta_next` is a chain, so each hidden link severed
    deposit order across it, and the rule-level read came back with two answers
    where `Chain.resolve` has one (docs/observations.md Part 6.3).

    The question §7 actually asks is already written down in `unify_patterns`'s
    own table: in MATCH, *a variable binds to a thing*; binding a variable to
    another variable is the pattern-against-pattern operation, and that is a
    different service. So that is the test -- match, and refuse the result if it
    bound a variable to a variable. A rule's own member, interned and therefore
    found among the instances of its relation, unifies with itself variable for
    variable and is refused; a chain fact about a generic proposition binds a
    variable to a STRUCTURE that contains variables, which is exactly what a
    rule reading about rules is for.
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
    construction: `asking(<seat>)`, and whatever a stratum-0 rule concludes.

    ⭐⭐⭐ **This is where the anchoring discipline actually divides, and it is
    not where I first drew it.** `_stored` refuses an unbound pattern because
    the chain's own relations are facts about the WHOLE HISTORY -- deposited
    whether or not anything asked -- so an unanchored `in_delta` would walk all
    of it and reach another frame's delta.

    These are not that. `asking` IS the question, and a derived relation exists
    only because the question was asked: every instance of `cand` was reached
    through an anchored walk from a seeded seat, so enumerating them enumerates
    what the anchor already admitted. Requiring an anchor here refuses the read
    its own conclusions -- which it did, and `beaten` and `best` derived
    nothing at all while `cand` derived 193.

    ⚠ The containment argument therefore rests on the SEED. A machinery that
    seeds a seat the frame cannot see would derive facts about it, and nothing
    structural would stop it. `Machine.ask_read` is the one caller.
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


def _span_of(g, chain, want, bindings):
    """`span_of(?s, ?start, ?end)` -- a stretch of the chain (§11).

    `entry_of`'s shape one construct along, and read the same two ways:

      * **endpoints bound** -- the span is MINTED. §11 says spans are *minted by
        recognisers, never enumerated*, and a rule with this member is what a
        recogniser is: `<TT-base>` builds the stretch it has just recognised.
      * **the span bound** -- it is decomposed, like any other node's members.

    ⚠ Unanchored it yields nothing, and here that is not politeness but the
    population: any two moments form a span, so enumerating them is quadratic in
    the history and every one of them meaningless until something recognises
    over it.

    ⚠⚠⚠ **Yes, this MINTS while matching, and the interning trap is why that
    needs an argument rather than a shrug.** A quiescence verdict computed with
    `substitute` was unsound precisely because minting made the conclusion exist
    -- so a matcher that creates nodes is the same shape. The difference is what
    the node's existence means. A stratum-0 conclusion IS the fact, so creating
    it answers the question being asked; a span node is a *name for a pair of
    moments*, and nothing anywhere reads whether one exists -- `span` is in no
    structural relation, so no rule can enumerate spans and no walk visits them.
    Interning then makes this idempotent: the same endpoints give the same node
    however many times any path asks. So the match is pure in the only sense the
    trap is about -- asking twice gives the same answer, and asking does not
    change what anything else would answer.
    """
    args = g.members(want.pattern)
    if len(args) != 3:
        return
    s = walk(g, args[0], bindings)
    if not g.is_var(s):
        span = chain.span_by_node(s)
        if span is None:
            return  # not a span: a member that names one matches nothing
        b = bindings
        for pattern, got in zip(args[1:], (span.start.node, span.end.node)):
            b = unify(g, pattern, got, b)
            if b is None:
                return
        yield b
        return
    start = walk(g, args[1], bindings)
    end = walk(g, args[2], bindings)
    if g.is_var(start) or g.is_var(end):
        return  # unanchored: quadratic, and meaningless until recognised over
    first, last = chain.moment_by_node(start), chain.moment_by_node(end)
    if first is None or last is None:
        return
    # §11's ancestry check, at the minting site. In the matcher it is a member
    # that finds nothing -- the engine's uniform answer to a pattern nothing
    # satisfies -- while `Chain.span` raises, because a machinery reaching there
    # with an inverted pair has made a mistake that is still attributable.
    if last is first or not last.at_or_after(first):
        return
    b = unify(g, args[0], chain.span(first, last).node, bindings)
    if b is not None:
        yield b


def structural_relations(chain) -> Dict[NodeId, Callable]:
    """The skeleton, as members an ordinary rule may write (§6, §12).

    §6 says stratum 0 is *a property of a rule* -- every antecedent member is
    structural -- decided *by inspecting an antecedent rather than by a designer
    assigning layers*, and that it *runs under the same interpreter*. A separate
    engine with its own rule and item types is the branch that sentence forbids.
    This is what removes it.

    Two kinds, and the difference is whether the fact is stored:

      * **stored** -- `pred`, `in_delta`, `delta_next`, `rests_on` are relation
        instances the chain deposits as it builds. Matched against the graph.
      * **walked** -- `anc`, `sanc` are transitive closures, and §3 says a
        stored closure would be a cache of something derived. Anchored, upward,
        and single-valued by §11, which is what keeps containment structural.

    ⚠ `entry_of` is a third thing again: not stored and not walked, but *read
    off the node's own members*. An entry is a relation instance like any other
    and always was.
    """
    # ⚠⚠⚠ **`pred` was the reflexive-transitive walk, under the name of the
    # immediate one.** It was registered for corpora to write (`machine.py`'s
    # name table) and no rule in this repo or the foreign one ever wrote it, so
    # nothing could see that `pred(?m, ?n)` yielded every ancestor AND `?m`
    # itself. `anc` is that walk and now carries the name; `pred` is the stored
    # immediate-predecessor fact the chain actually deposits. A name a corpus
    # may write whose meaning is not what the name says is worse than an absent
    # one, because a corpus that used it would have been right to trust it.
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
        chain.SPAN_OF: _span_of,
        chain.ASKING: _bounded,
        chain.ASKED: _bounded,
        # `time(?m, ?t)` -- stored, so it refuses an unbound moment for
        # `_stored`'s reason: it is a fact about the whole history, and an
        # unanchored read would walk all of it.
        chain.TIME: _stored,
        chain.HOLDS_AT: _holds_at,
    }


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
