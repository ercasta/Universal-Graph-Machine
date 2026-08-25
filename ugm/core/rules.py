"""Rules (§8), matching and arbitration (§14).

A rule is a fact relating two sides -- `implies(A, C)` -- and because it is a
node, everything else about it is an ordinary fact. Direction is a query over
the rule, never a field in it: one statement, two readings.

There is one connective. `causes` was the other, and the only thing it did was
land its conclusion in a LATER moment; with the moments gone it does nothing
that `implies` does not, so it went rather than being kept as a label. What a
corpus wants to say about time it says in rules of its own, over a vocabulary
of its own -- time is an open class and tying it to the engine was the mistake.

There is also one MATCHER. The second one read the chain's skeleton -- `pred`,
`in_delta`, `anc` -- as structure rather than as claims, and the whole
stratification apparatus existed to keep the two from chasing each other. The
skeleton went with the chain, so what is left is: a member matches an anchored
proposition, or it is computed, or it asks about absence.

See docs/design/rules.md.
"""

from typing import Callable, Dict, List, NamedTuple, Optional, Sequence, Tuple

from .graph import Graph, NodeId
from .scratchpad import Scratchpad

# The four modes a member may be in. Three of them are what the old signs
# became: a `+` member asks whether something is anchored, and a `+` consequent
# anchors it. `-` survives only in a CONSEQUENT, where it erases the anchor --
# which is the un-claim an append-only chain could never express, and the whole
# reason it went. There is no `-` premise, because there is no denying entry to
# find: what used to be `-p` is either `no p` (nothing anchors it) or
# `+not(p)` (something anchors its denial), and the corpus has to say which.
ASSERT = "+"
ERASE = "-"
ABSENT = "no"
# The fourth is new (docs/design/intensity-gates.md): an ANTECEDENT-only mode,
# matched exactly like `ASSERT` -- same pool, same "is it on" question -- but
# exempted from what `ASSERT` now costs. Firing discharges every `+` member it
# matched by default; `keep` is the per-line opt-out, a non-consuming read the
# same as a Petri net's test arc. There is no `keep` in a consequent: writing
# is not a place `keep` has anything to say about, and the loader refuses it
# there the same way it refuses `no` there.
KEEP = "keep"

#: The connective, as the surface spells it. One, so this is what the parser
#: checks a rule's head against rather than a closed set of two.
IMPLIES = "implies"

#  `?` is gone, and it is a reduction rather than a loss. It existed because
# absence was ambiguous in an append-only chain -- never considered, or not yet
# derived? -- so ignorance had to be written down to be distinguishable from
# silence. A scratchpad has nothing to disambiguate: absence is ignorance, and
# there is no third thing for a sign to say.


class _Stop:
    """The postcondition that ends the run, as a sentinel rather than a node."""

    def __repr__(self) -> str:
        return "STOP"


STOP = _Stop()


class Attend:
    """`attend $x` -- put a node at the front of what the agent is thinking
    about. A post rather than a member: it changes what is considered next, and
    claims nothing about the world."""

    def __init__(self, term, weight=None, decay=None,
                 floor=None, ceiling=None) -> None:
        self.term = term
        # The weight rides along: `attend($x, 3)` says this node matters more
        # than whatever else lands in the queue at the same depth -- a
        # calibration that names a NODE rather than a rule, which is what makes
        # it survive a rule being renamed or rewritten.
        #
        # It is also a LIFESPAN: the strength a claim starts at and is restored
        # to when a move touches it again, losing `decay` a tick until it is
        # gone. None for either means *no opinion* -- `Machine` supplies the
        # medium, because a corpus that does not care how long should not have
        # to name a number to say so.
        self.weight = weight
        self.decay = decay
        # `floor` is the least it may fade to -- above zero it never fades
        # away at all, which is how a lane keeps a subject when nothing is
        # happening. `ceiling` is the most a refresh may raise it to, so a
        # thing mentioned over and over cannot grow until it is the only
        # thing the lane is about.
        self.floor = floor
        self.ceiling = ceiling

    def __repr__(self) -> str:
        return (f"attend({self.term}, {self.weight}, {self.decay}, "
                f"{self.floor}, {self.ceiling})")


class _Unattend:
    """`unattend` -- drop what is being attended to.

    attend deposits a claim, unattend denies one, and this stops. There
    is no third construct here: it is the same post list, one more row.
    """

    def __repr__(self) -> str:
        return "unattend"


UNATTEND = _Unattend()


class Push:
    """`push $x, $y` -- open a frame whose queue is these nodes.

    A frame is a sub-line of work: what it attends to is its own, and what it
    concludes lands in the same one graph as everything else.
    """

    def __init__(self, terms) -> None:
        self.terms = list(terms)

    def __repr__(self) -> str:
        return f"push({self.terms})"


class Pop:
    """`pop $x` -- close the innermost frame, carrying one node back.

    `pop` is `stop` scoped to a frame, and it is a row beside it rather than a
    mechanism of its own.
    """

    def __init__(self, term) -> None:
        self.term = term

    def __repr__(self) -> str:
        return f"pop({self.term})"


class Merge:
    """`merge($a, $b)` -- `$b` counts as `$a` from here on (`Graph.merge`).

    The doc's own strongest argument for a microprogram: `merge` is built,
    `unify` and the scratchpad both respect it, and no rule could call it --
    an effect `+`/`-` provably cannot express. `$a` is KEEP, `$b` is DROP, the
    same order `Graph.merge` takes; a rule authors the claim, the engine only
    computes its consequence (`merge`'s own docstring).
    """

    def __init__(self, keep, drop) -> None:
        self.keep = keep
        self.drop = drop

    def __repr__(self) -> str:
        return f"merge({self.keep}, {self.drop})"


class Unmerge:
    """`unmerge($a, $b)` -- undo `merge($a, $b)`, if it is the record's own
    top and caused no cascade (`Graph.unmerge`). Refuses (`ValueError`)
    rather than guess otherwise; the RHS does not catch it, the same way a
    rule that mints past a run limit is not caught -- an author's mistake
    should stop the run, not be absorbed."""

    def __init__(self, keep, drop) -> None:
        self.keep = keep
        self.drop = drop

    def __repr__(self) -> str:
        return f"unmerge({self.keep}, {self.drop})"


class Destroy:
    """`destroy($e)` -- take a node out of the graph entirely (`Graph.delete`).

    Structural, not belief: `-p` erases an ANCHOR and leaves the proposition
    for other rules to mention; `destroy` removes the node itself. The
    hazard `wanting.md` §7 measured stands unchanged by wrapping it in a
    microprogram op -- *the only safe target is the anchor* -- so this is
    for entities the corpus has established nothing else still mentions, an
    authoring discipline the engine does not enforce.
    """

    def __init__(self, term) -> None:
        self.term = term

    def __repr__(self) -> str:
        return f"destroy({self.term})"


class Label:
    """`label($z, paul)` -- give `$z` the label `paul` (`Graph.label`).

    A LABEL is a claim of identity and may itself merge two nodes -- see
    `Graph.label`'s own docstring -- so this can be a merge wearing a
    shorter name. `text` is a ground atom, in the corpus's existing bare-name
    style; there is no string-literal syntax to spell `"paul"` with.
    """

    def __init__(self, term, text) -> None:
        self.term = term
        self.text = text

    def __repr__(self) -> str:
        return f"label({self.term}, {self.text})"


class Unlabel:
    """`unlabel($z, paul)` -- take the label back (`Graph.unlabel`). Does
    NOT unmerge: see `Graph.unlabel`'s own docstring."""

    def __init__(self, term, text) -> None:
        self.term = term
        self.text = text

    def __repr__(self) -> str:
        return f"unlabel({self.term}, {self.text})"


class Forget:
    """`forget $hit` -- erase a tool's answer AND the request it named,
    together (`new_substrate.md`'s `<wound>`).

    Sugar over two erasures, but not load-time sugar: `$hit` is bound to an
    `answered(<tool>, request, value)` instance at MATCH time, and the
    request to erase alongside it -- `g.member($hit, 1)` -- is not known
    until then. This is the corpus's own first law (an occasion is
    consumed, a fact is not) as one statement instead of a pair of `-`
    members restating the request's own pattern.

    Refuses (raises) rather than silently doing nothing when the bound node
    is not `answered(...)`-shaped -- the same standing as `Unmerge`: an
    author's mistake should surface, not be absorbed.
    """

    def __init__(self, term) -> None:
        self.term = term

    def __repr__(self) -> str:
        return f"forget({self.term})"


class Member(NamedTuple):
    """One entry in a rule's antecedent or consequent.

    `binds` is `as $t` -- a name for WHAT matched, so a rule can refer to the
    very thing it matched rather than describing it again.
    """

    sign: str
    pattern: NodeId
    binds: Optional[NodeId] = None
    # A CONSEQUENT-only extra (docs/design/intensity-gates.md): `+p(x)
    # intensity $n` names the write's own strength instead of taking the
    # default (`scratchpad.ON`, "fully on"). `write` is the still-generic
    # TERM -- substituted with the application's bindings the same way
    # `pattern` is, at apply time, since `$n` is usually a variable the
    # antecedent computed (`plus($n, 1) as $n2`) rather than a load-time
    # constant. `None` is *no opinion*, which is every ordinary `+p(x)` and
    # every antecedent member: intensity is a RHS concept, and nothing here
    # stops an antecedent member from carrying one because nothing reads it
    # if it did.
    write: Optional[NodeId] = None


class Rule:
    def __init__(
        self,
        node: NodeId,
        antecedent: Sequence[Member],
        consequent: Sequence[Member],
        name: str = "",
        mentions: bool = False,
    ) -> None:
        self.node = node
        self.antecedent = list(antecedent)
        self.consequent = list(consequent)
        self.name = name
        # Whether this rule was AUTHORED naming a rule -- `+ant(<R>, $p)`. A
        # rule node contains the variables of its own patterns, so a consequent
        # that names one is a ground claim that happens to be generic, and the
        # gate would otherwise refuse it. §14 settles use/mention by
        # inheritance, and inheritance has to start somewhere: a pattern
        # written with `<...>` is the source.
        self.mentions = mentions
        self._orders: Optional[List[Tuple[int, ...]]] = None

    def walk_order(self, pivot: Optional[int]) -> Tuple[int, ...]:
        """Which order `match` walks the antecedent in, for a given pivot.

        The pivot first and the rest in authored order, so every later member
        is narrowed by what the pivot bound. Cached on the rule because it
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
        return f"<{self.name or 'rule'}>"


class Application(NamedTuple):
    """What match found: a rule, what it bound, and what each line matched.

    `matched` is one entry per antecedent member, in authored order: the node
    that member bound, or None for an `absent` member, which bound nothing
    because there was nothing there.

    It is back because nothing else can reconstruct it. While `rel` interned,
    `substitute(pattern, bindings)` handed back the very node the line matched
    -- rebuilding a proposition and finding it were the same act. They are not
    any more: a rebuild MINTS, so a caller asking *what did this line bind*
    got a node nobody believed, nobody attended, and nobody else would ever
    see. Attention reads this, and attention deciding what a move spends is
    the whole of the token line.
    """

    rule: Rule
    bindings: Dict[NodeId, NodeId]
    matched: Tuple[Optional[NodeId], ...] = ()


class RuleSet:
    def __init__(self, g: Graph) -> None:
        self.g = g
        self.IMPLIES = g.atom(IMPLIES)
        # A rule's two sides, and the members inside them, as nodes -- so that
        # `rule($r)`, `ant($r, $p, $mode, $i)` and `con(...)` are ordinary
        # facts about ordinary structure rather than a reader's invention.
        self.SIDE = g.atom("side")
        self.MEMBER = g.atom("member")
        # The three modes, as ARGUMENTS, for the reader that asks what mode a
        # member is in. `+p` uses a mode; `ant($r, $p, assert, $i)` mentions
        # one. Taken from here by everything that needs them: `atom` does not
        # intern, so a second `g.atom("assert")` is a different node no rule
        # could match -- the name-identity trap, which has cost this design
        # five silent bugs.
        self.MODE = {
            ASSERT: g.atom("assert"),
            ERASE: g.atom("erase"),
            ABSENT: g.atom("absent"),
            KEEP: g.atom("keep"),
        }
        self.rules: List[Rule] = []
        # Experience, kept apart from world knowledge: what to reach for after
        # a rule applies (keyed by its node) and what to reach for at ranking
        # time (keyed by None). A rule says what is the case; a trigger says
        # when it is worth thinking of. Read only by a loop that has a table.
        self.triggers: Dict[Optional[NodeId], List[Tuple]] = {}
        self.DORMANT: Optional[NodeId] = None
        self.claims: Optional[Callable[[NodeId], object]] = None
        # Relations that are COMPUTED rather than matched (§12's skeleton).
        # Set by the Machine, which owns the registry; a bare RuleSet has none,
        # which is what a rule set with no host functions should say.
        self.computes: Dict[NodeId, Callable] = {}
        # Relations that are FILTERED rather than matched -- a computator's
        # cousin, over nodes rather than shown strings, answering a bool
        # rather than a value (`new_substrate.md`'s `attentioned($x)` and a
        # label test). Also set by the Machine.
        self.predicates: Dict[NodeId, Callable] = {}
        # A third cousin: BINDS, like a computator, but over the node itself
        # rather than its shown text -- `intensity($x) as $n`
        # (docs/design/intensity-gates.md) is the one this shipped for. Also
        # set by the Machine, which is the one thing that knows what a
        # node's intensity currently is.
        self.node_computes: Dict[NodeId, Callable] = {}
        self.by_node: Dict[NodeId, "Rule"] = {}
        # Authoring a rule is an event, the way a write is. The machine
        # subscribes so that a rule becomes DATA the moment it exists rather
        # than when somebody remembers to ask -- which matters once rules read
        # rules: a reader that enumerates `rule($r)` sees whatever was reified,
        # and a rule authored afterwards was invisible to it with nothing
        # reporting so.
        self.on_rule: List[Callable[["Rule"], None]] = []
        # Rules by the relation they CONCLUDE, so recall starts somewhere.
        self.by_conclusion: Dict[Optional[NodeId], List["Rule"]] = {}

    def rule(
        self,
        antecedent: Sequence[Member],
        consequent: Sequence[Member],
        name: str = "",
        node: Optional[NodeId] = None,
    ) -> Rule:
        """A rule is a fact relating **two** sides (§8) -- never a flat list of
        its patterns.

        Two things go wrong if the patterns are flattened onto the connective.
        The arity varies with how many members the rule happens to have, which
        is exactly the shape §5 refuses: a node whose members mean different
        things depending on how many there are. And the *modes* end up nowhere,
        so `{+p} => {+q}` and `{+p} => {-q}` are the same node -- one rule,
        silently.

        Two rules that happen to say the same thing are still two rules, with
        different authors and different provenance -- which is now what the
        substrate does anyway, and used to need saying because `rel` did not.
        """
        if node is None:
            node = self.g.rel(
                self.IMPLIES, self._side(antecedent), self._side(consequent)
            )
        r = Rule(node, antecedent, consequent, name)
        self.rules.append(r)
        self.by_node[node] = r
        for m in consequent:
            if m.sign != ASSERT or self.g.is_var(m.pattern):
                continue
            bucket = self.by_conclusion.setdefault(self.g.relation_of(m.pattern), [])
            if r not in bucket:
                bucket.append(r)
        for hook in self.on_rule:
            hook(r)
        return r

    def _side(self, members: Sequence[Member]) -> NodeId:
        """One side of a rule: its members, as nodes, in authored order.

        The mode is in the graph rather than beside it, so *which rules erase*
        stays a query over the consequent's members.
        """
        made = [
            self.g.rel(self.MEMBER, m.pattern, self.MODE[m.sign])
            for m in members
        ]
        return self.g.rel(self.SIDE, *made)


# -- unification ------------------------------------------------------------


def unify(
    g: Graph, pattern: NodeId, node: NodeId, bindings: Dict[NodeId, NodeId]
) -> Optional[Dict[NodeId, NodeId]]:
    """Bind a generic pattern to an anchored node. One-sided: only `pattern`
    may contain variables, which is what makes this cheaper than unification
    and is true of everything match does."""
    if g.is_var(pattern):
        got = bindings.get(pattern)
        if got is None:
            out = dict(bindings)
            out[pattern] = node
            return out
        return bindings if got == node else None
    if pattern == node:
        return bindings
    pr, nr = g.relation_of(pattern), g.relation_of(node)
    if pr is None or nr is None:
        # An atom against an atom that is not the same atom, once identity has
        # been followed. Through identity, so a fact written with one
        # vocabulary matches a member written with another after a merge.
        if g._identity and g.identity_of(pattern) == g.identity_of(node):
            return bindings
        return None
    cur: Optional[Dict[NodeId, NodeId]] = bindings
    if pr != nr:
        if g.is_var(pr):
            cur = unify(g, pr, nr, cur)
            if cur is None:
                return None
        elif not (g._identity and g.identity_of(pr) == g.identity_of(nr)):
            return None
    pm, nm = g.members(pattern), g.members(node)
    if len(pm) != len(nm):
        return None
    for p, n in zip(pm, nm):
        cur = unify(g, p, n, cur)
        if cur is None:
            return None
    return cur


def generalise(
    g: Graph, a: NodeId, b: NodeId, seen: Dict[Tuple[NodeId, NodeId], NodeId]
) -> NodeId:
    """The least general generalisation of two ground structures: where they
    agree, keep it; where they differ, a variable -- and the SAME variable
    wherever the same pair differs, which is what makes this a generalisation
    and not a wildcard."""
    if a == b:
        return a
    key = (a, b)
    if key in seen:
        return seen[key]
    ar, br = g.relation_of(a), g.relation_of(b)
    if ar is not None and ar == br and len(g.members(a)) == len(g.members(b)):
        return g.rel(ar, *[generalise(g, x, y, seen)
                           for x, y in zip(g.members(a), g.members(b))])
    v = g.var(f"${len(seen)}")
    seen[key] = v
    return v


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
    """Does `var` appear inside `n`? Binding `$x` to `f($x)` builds a structure
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
    """Unify two structures that may **both** be generic."""
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

    Two rules written independently both say `$w`, and they mean different
    things. Matching never notices because only one side has variables.
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
    reason: rebuilding it mints a second node saying the same thing, and a
    caller grounding a pattern wants the parts it was given."""
    p = walk(g, pattern, bindings)
    if g.is_var(p) or not g.members(p):
        return p
    r = g.relation_of(p)
    assert r is not None
    r2 = walk(g, r, bindings) if g.is_var(r) else r
    members = g.members(p)
    new = [ground(g, m, bindings) for m in members]
    if p == pattern and r2 == r and all(a == b for a, b in zip(new, members)):
        return p
    return g.rel(r2, *new)


def _left_open(g, pattern, bindings) -> bool:
    """Did this member leave a variable of its OWN unbound?

    The question `has_var` over the grounded node was standing in for, and the
    two part company exactly where §14 does. A rule reading `con($r, $pat, $i)`
    binds `$pat` to a stored pattern, so its conclusion contains variables and
    every one of them is bound -- a ground claim that happens to be about a
    generic thing. A rule whose consequent names a variable its antecedent
    never bound is the other case, and only that one has nothing to write.
    """
    from .text import _vars_in  # deferred: `text` imports this module
    return any(v not in bindings for v in _vars_in(g, pattern))


def substitute(g: Graph, pattern: NodeId, bindings: Dict[NodeId, NodeId]) -> NodeId:
    """Ground a consequent pattern. Anything still generic afterwards is a rule
    whose consequent names something its antecedent never bound, and the gate
    refuses it rather than minting a node nobody can read."""
    if g.is_var(pattern):
        return bindings.get(pattern, pattern)
    # A whole TERM may be bound, not only a variable -- which is how a `+kind`
    # mark becomes the node this application minted. Nothing else binds a
    # compound, so this costs one dict get on a path that runs per member.
    got = bindings.get(pattern)
    if got is not None:
        return got
    members = g.members(pattern)
    if not members:
        return pattern
    rel = g.relation_of(pattern)
    assert rel is not None
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
    """The node `substitute` WOULD produce, if one of that shape exists.
    Never mints.

    `substitute` MINTS, so asking with it does not answer the question -- it
    manufactures a yes. This resolves the pattern against the bindings and
    looks the result up instead, and it is what an `absent` member and a `-`
    consequent both ask with.

    Three answers, not two: a node, `None` for *ground and nothing says it*,
    and `GENERIC` for *still open*.
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
            # A ground subterm nothing in the graph has: nothing can have the
            # whole either, since a member is a node. New without looking
            # further.
            return None
        new.append(got)
    return g.find_rel(rel, *new)


# -- match ------------------------------------------------------------------


def candidates(
    g: Graph, pad: Scratchpad, want: Member,
    bindings: Optional[Dict[NodeId, NodeId]] = None,
) -> List[NodeId]:
    """The anchored propositions a member could match, newest first.

    There is no Situation any more, and this is what replaced it. The old one
    was a second index over the state, maintained incrementally beside the
    graph's own, and it had to be: belief lived in a chain, so the graph could
    not be asked what was believed. Now it can. §3's indexes over instances --
    by relation, and by what sits in each argument position -- already narrow
    the pool exactly as `Situation._narrowest` did, and belief is one lookup
    per candidate on top.

    That the two agreed was checked by a gate of its own (`gates/state.py`),
    which is the cost an index pays: it is a re-implementation of the thing it
    indexes, and it has to be held to it. This one cannot disagree with the
    graph, because it *is* the graph.
    """
    p = want.pattern
    if g.is_var(p):
        return pad.believed()  # a bare variable: anything believed will do
    rel = g.relation_of(p)
    if rel is None:
        # An atom as a whole member. It is anchored or it is not; there is
        # nothing to enumerate.
        return [p] if pad.holds(p) else []
    if g.is_var(rel):
        # A variable in the RELATION slot. Nothing is known about what it names
        # until it matches, so it takes the same pool a bare variable does --
        # the index cost of allowing one, stated here rather than discovered on
        # a workload.
        return pad.believed()
    if g._identity:
        rel = g.identity_of(rel)
    pool = None
    if bindings:
        for i, m in enumerate(g.members(p)):
            if g.is_var(m):
                m = bindings.get(m)
                if m is None:
                    continue  # not bound yet; this member says nothing here
            #  Atoms only: `unify` reduces to identity for a node with no
            # relation and no members, and to a structural comparison for
            # anything else -- which can accept a twin an identity key drops.
            if g.relation_of(m) is not None or g.members(m):
                continue
            bucket = g.instances_with(rel, i, m)
            if not bucket:
                return []  # nothing is even SAID with that argument there
            if pool is None or len(bucket) < len(pool):
                pool = bucket
    if pool is None:
        pool = g.instances_of(rel)
    holds = pad.holds
    return [n for n in reversed(pool) if holds(n)]


def match(
    g: Graph,
    pad: Scratchpad,
    rule: Rule,
    computes: Optional[Dict[NodeId, Callable]] = None,
    fresh: Optional[Sequence[NodeId]] = None,
    predicates: Optional[Dict[NodeId, Callable]] = None,
    node_computes: Optional[Dict[NodeId, Callable]] = None,
) -> List[Application]:
    """Unify a rule's generic antecedent against what is anchored.

    `fresh` is the propositions written since the last pass. Given one, every
    member is tried as the PIVOT -- drawn from `fresh` rather than from the
    whole state -- so a pass costs what changed rather than what is known. It
    is the same walk either way; only where the first member's candidates come
    from differs.

    `predicates` is a computator's cousin: evaluated, not matched, arguments
    ground by now, and the arguments are NODES rather than `computes`'s
    strings -- a predicate is a question about identity (is this node in the
    attention pool, does this node carry that label) that a shown-and-rebuilt
    string cannot answer honestly. It returns a bool rather than a value: a
    predicate line filters, it does not bind (`new_substrate.md`'s
    `attentioned($x)` and a label test are the two this shipped for).
    """
    computes = computes or {}
    predicates = predicates or {}
    node_computes = node_computes or {}
    results: List[Application] = []
    seen: set = set()
    width = len(rule.antecedent)

    def run(pivot: Optional[int]) -> None:
        order = rule.walk_order(pivot)

        def step(j: int, bindings: Dict[NodeId, NodeId],
                 matched: Dict[int, NodeId]) -> None:
            if j == width:
                if pivot is not None:
                    k = (rule.node, frozenset(bindings.items()))
                    if k in seen:
                        return
                    seen.add(k)
                results.append(Application(
                    rule, bindings,
                    tuple(matched.get(x) for x in range(width))))
                return
            i = order[j]
            want = rule.antecedent[i]
            rel = g.relation_of(want.pattern)
            fn = computes.get(rel)
            if fn is not None:
                # A computator: evaluated, not matched. §12's skeleton is
                # *conditions on the binding that claim nothing* --
                # distinctness is already one -- and arithmetic is exactly
                # that. The arguments must be ground by now.
                args = [walk(g, a, bindings) for a in g.members(want.pattern)]
                if any(g.is_var(a) for a in args):
                    return
                try:
                    got = fn(*[g.show(a) for a in args])
                except Exception:
                    got = None  # a computator that raises answers nothing
                if want.sign == ABSENT:
                    # `no beats($hit, $c)` -- an ordering the computator
                    # answers, asked in the negative. Found as a real bug,
                    # not designed in: this branch used to run BEFORE the
                    # `sign == ABSENT` check below could ever see it, so a
                    # `no` in front of a computator-relation member was
                    # silently ignored and the member matched whenever the
                    # function answered anything at all -- the opposite of
                    # what `no` says. `got is None` is what a computator's
                    # own convention already uses for *declines to answer*,
                    # which is the right reading of *not this ordering*.
                    if got is not None:
                        return
                    b = bindings
                    if want.binds is not None:
                        grounded = substitute(g, want.pattern, bindings)
                        b = unify(g, want.binds, grounded, bindings)
                    if b is not None:
                        step(j + 1, b, matched)
                    return
                if got is None:
                    return
                #  `got` is a NODE, resolved by whoever registered the function
                # in the corpus's own table. Building one here with `g.atom`
                # mints a fresh node, so the result would be a TWIN of the value
                # the corpus writes -- the rule fires, the fact lands, and asking
                # about it answers nothing.
                b = bindings
                if want.binds is not None:
                    b = unify(g, want.binds, got, bindings)
                if b is not None:
                    step(j + 1, b, matched)
                return
            nfn = node_computes.get(rel)
            if nfn is not None:
                # A computator's twin, over the NODE rather than its shown
                # text -- `intensity($x)` (docs/design/intensity-gates.md)
                # is the one this shipped for. `computes` calls `fn(*shown)`,
                # which is right for arithmetic (`plus("2", "3")`) and wrong
                # here: `intensity` is a question about WHICH occasion `$x`
                # is, not about what its name spells, and two differently-
                # named nodes that happen to print the same text must not
                # answer it the same way. The arguments must be ground by
                # now, exactly as a computator's must.
                args = [walk(g, a, bindings) for a in g.members(want.pattern)]
                if any(g.is_var(a) for a in args):
                    return
                try:
                    got = nfn(*args)
                except Exception:
                    got = None
                if want.sign == ABSENT:
                    if got is not None:
                        return
                    b = bindings
                    if want.binds is not None:
                        grounded = substitute(g, want.pattern, bindings)
                        b = unify(g, want.binds, grounded, bindings)
                    if b is not None:
                        step(j + 1, b, matched)
                    return
                if got is None:
                    return
                b = bindings
                if want.binds is not None:
                    b = unify(g, want.binds, got, bindings)
                if b is not None:
                    step(j + 1, b, matched)
                return
            pfn = predicates.get(rel)
            if pfn is not None:
                # A predicate: same shape as a computator's ground-and-call,
                # but it answers a bool over the NODES themselves rather than
                # over their shown names, and it never binds -- it filters an
                # already-bound reference, which is what a reference line is
                # for. `as` on a predicate member is refused at load, not
                # ignored here: see `text.py`.
                args = [walk(g, a, bindings) for a in g.members(want.pattern)]
                if any(g.is_var(a) for a in args):
                    return
                try:
                    ok = pfn(*args)
                except Exception:
                    return  # a predicate that raises answers no, either sign
                if want.sign == ABSENT:
                    # ⚠ The sign is READ here, and this branch returns before
                    # the `sign == ABSENT` arm below ever sees the member. It
                    # did not use to be, so `no attentioned($x)` parsed, was
                    # evaluated as though the `no` were absent, and therefore
                    # meant its own opposite -- silently, with no error at
                    # load and none at match. A predicate answers a question;
                    # `no` asks the other one.
                    ok = not ok
                if ok:
                    step(j + 1, bindings, matched)
                return
            if want.sign == ABSENT:
                # Absence, asked rather than matched: holds when nothing
                # anchors the (now ground) proposition. Ground by construction
                # -- the loader refuses a `no` member whose variables an earlier
                # member does not bind, and the walk order keeps authored
                # relative order, so an open pattern here is a bug upstream,
                # answered with nothing rather than with everything.
                #  `already_there`, not `substitute`. Rebuilding the
                # proposition to ask about it MINTS one, so asking *is nothing
                # believed here* left an unbelieved occasion of exactly that
                # shape behind -- once per member per candidate, in the index
                # every later match walks. This resolves the pattern against
                # the bindings and looks the node up instead.
                grounded = already_there(g, want.pattern, bindings)
                if grounded is GENERIC:
                    return
                if grounded is not None and pad.holds_any(grounded):
                    #  `holds_any`, not `holds`. `p(x)` said twice is two
                    # nodes, and asking one of them reports *nothing says it*
                    # while the other sits believed.
                    return  # something anchors it: the absence fails
                b = bindings
                if want.binds is not None:
                    # A name for what is NOT there. Nothing of that shape
                    # exists to name, so this is the one place the absence
                    # branch has to build.
                    if grounded is None:
                        grounded = substitute(g, want.pattern, bindings)
                        if g.has_var(grounded):
                            return
                    b = unify(g, want.binds, grounded, bindings)
                if b is not None:
                    step(j + 1, b, matched)
                return
            pool = (fresh if i == pivot and fresh is not None
                    else candidates(g, pad, want, bindings))
            for node in pool:
                b = unify(g, want.pattern, node, bindings)
                if b is not None and want.binds is not None:
                    # ...and what it says, as a whole, under a name.
                    b = unify(g, want.binds, node, b)
                if b is not None:
                    step(j + 1, b, {**matched, i: node})

        step(0, {}, {})

    if fresh is None:
        run(None)
    else:
        for pivot in range(width):
            #  Never pivot on a computator -- and this is an OPTIMISATION, not
            # a correctness fix. A computator walked first has nothing bound to
            # compute from, so that pass finds nothing; but every pivot is
            # tried, and the pass whose pivot is the changed proposition finds
            # the applications anyway.
            if g.relation_of(rule.antecedent[pivot].pattern) in computes:
                continue
            #  Never pivot on an absence: there is nothing for it to have
            # matched. The machine re-matches the whole rule when a claim about
            # the absent relation lands, which is this pass's job done
            # elsewhere.
            if rule.antecedent[pivot].sign == ABSENT:
                continue
            #  Never pivot on a predicate, for the computator's own reason: a
            # predicate has nothing to enumerate FROM, only a reference to
            # check once its argument is already bound.
            if g.relation_of(rule.antecedent[pivot].pattern) in predicates:
                continue
            #  Never pivot on a node-computator, the same reason exactly:
            # `intensity($x)` has nothing to enumerate FROM until `$x` is
            # already bound by an earlier member.
            if g.relation_of(rule.antecedent[pivot].pattern) in node_computes:
                continue
            run(pivot)
    return results


# -- arbitrate --------------------------------------------------------------


def arbitrate(
    rs: RuleSet,
    applications: Sequence[Application],
    priority: Optional[Callable[["Rule"], Tuple]] = None,
) -> Optional[Application]:
    """Among the rules that matched, choose one. Total: it always answers.

    Authored order is the floor, and a priority function may reorder above it.
    Being total is the whole requirement: the last stage cannot be allowed to
    decline, or the loop has a case with nothing to do and no way to say so.
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
