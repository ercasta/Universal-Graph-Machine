"""The interpreter (§14, §16).

The step is *select a rule, apply it* -- object-rules and meta-rules
indistinguishable to it, a flat tower rather than a stacked one.

The engine's business is: what is believed, which rules match it, which
one goes next, and what happens to the scratchpad when it does.

See docs/design/machine.md.
"""

from .. import corpora as _corpora
import inspect
from typing import Dict, List, NamedTuple, Optional, Tuple

from .channels import Arrival, Channels
from .gate import Gate
from .graph import Graph, NodeId
from .rules import (
    ABSENT,
    ASSERT,
    ERASE,
    GENERIC,
    Application,
    Member,
    Rule,
    RuleSet,
    already_there,
    match,
    substitute,
    _left_open,
)
from .scratchpad import Scratchpad


class Step(NamedTuple):
    """What one tick did, and -- when it did nothing -- which silence it was.

    `applied` is now a TUPLE, not a single `Application` (docs/design/
    intensity-gates.md): several rules -- several applications of one rule,
    even -- can fire in the same tick, because nothing picks a winner any
    more. Empty is what the table era's `None` was: this tick fired nothing.

    *Nothing applied* and *nothing came to mind* are different events (§15),
    and only the second should escalate.
    """

    arrivals: int
    matched: int  # applications FOUND this tick, before the fold/commit
    applied: Tuple[Application, ...]  # applications that actually FIRED
    wrote: Tuple[NodeId, ...]
    state: str  # applied | quiescent | stopped


class Answerer(NamedTuple):
    """A tool: something that answers a request without searching for it.

    Deliberately the same shape as a rule where anything looks at it -- a
    `name` in the `<...>` namespace and a `node` other statements can be about
    -- because a tool nothing could speak about would be a tool nothing could
    argue with.
    """

    name: str
    node: NodeId
    request: NodeId
    fn: object  # fn(machine, proposition) -> NodeId | None


class Machine:
    BUNDLE = _corpora.path("bundle.ugm")

    def __init__(self) -> None:
        self.g = Graph()
        self.pad = Scratchpad(self.g)
        self.gate = Gate(self.g, self.pad)
        self.rules = RuleSet(self.g)
        self.channels = Channels(self.g)

        # -- the boundary --------------------------------------------------
        self.SAYS = self.g.atom("says")
        self.ARRIVED = self.g.atom("arrived")
        # §9's denial as a TERM. There is no denying sign any more, so this is
        # the only way to say no -- which is the simplification the collapse
        # bought: `+not(p)` is an ordinary claim about an ordinary node, and
        # `no p` is the different question of whether anything anchors p.
        self.NOT = self.g.atom("not")

        # -- rules as data -------------------------------------------------
        self.RULE = self.g.atom("rule")
        self.ANT = self.g.atom("ant")
        self.CON = self.g.atom("con")
        self.NAMES = self.g.atom("names")
        # The mint marker: `+kind` in a consequent introduces one new thing per
        # application. Not a reserved NAME -- `+k` names nothing a corpus could
        # ask about, so reserving it would reserve a letter.
        self.NEW = self.g.atom("new")

        # -- the aggregate -------------------------------------------------
        # `count(p($x))` asks how many ground matches a pattern has, and
        # `counted(<ask>, n)` is the answer. This is the one thing `no` cannot
        # do: a consequent may carry an unbound variable, so absence is not a
        # quantifier and this is.
        self.COUNT = self.g.atom("count")
        self.COUNTED = self.g.atom("counted")

        # -- recall --------------------------------------------------------
        self.RECALL = self.g.atom("recall")
        self.RECALLED = self.g.atom("recalled")
        # Dormancy, and it is the right form of *disable a rule*: a pair of
        # ordinary claims rather than a mark on the rule, so it is
        # attributable, deniable and readable by rules -- and `due` can be
        # concluded by anything at all, which is all a callback is.
        self.DORMANT = self.g.atom("dormant")
        self.DUE = self.g.atom("due")
        # Which rules are in the table at the default rather than at the floor.
        self.STANDING = self.g.atom("standing")
        # Which LANE a rule runs in, and where that lane sits in the tick's
        # order (§ lanes). `lane(<R>, judge)` claims membership; unmarked
        # rules default to `main`, so a corpus that never mentions a lane
        # runs exactly as it did before lanes existed. `lane_order(judge, 1)`
        # claims where a lane sits -- a list, not a single winner, so it is
        # its own read rather than `_knob`'s highest-wins.
        self.LANE = self.g.atom("lane")
        self.LANE_ORDER = self.g.atom("lane_order")
        self.BOUNDED = self.g.atom("bounded")
        self.TICKS = self.g.atom("ticks")
        # Two rules matched and nothing separates them -- deposited rather than
        # decided, so a corpus can settle it.
        self.CLOSE = self.g.atom("close")

        # -- reference lines (`new_substrate.md`) --------------------------
        # `label($x, paul)` -- does $x carry this label. A PREDICATE (see
        # `rules.match`): a filter over an already-bound node, never
        # matched, never bound to. `attentioned($x)` was the other one and
        # is gone with the focus queue it asked about -- a rule that wants
        # to know whether something is in play asks whether it is ON, which
        # is what an ordinary member already does.
        self.LABEL = self.g.atom("label")
        # -- intensity (docs/design/intensity-gates.md) --------------------
        # `intensity($x) as $n` -- a NODE-COMPUTATOR (see `rules.match`):
        # `$x` must already be bound, and this reads its CURRENT number
        # rather than filtering or matching it. The one read half of "read
        # the current intensity, write a new one" needs; the write half is
        # an ordinary consequent member's `intensity $n` clause
        # (`text.py`'s `member`), applied by `firing.run`'s per-tick
        # commit rather than by anything registered here.
        self.INTENSITY = self.g.atom("intensity")

        # -- the tool seams ------------------------------------------------
        self.ANSWERS = self.g.atom("answers")
        self.ANSWERED = self.g.atom("answered")
        self.COMPUTES = self.g.atom("computes")
        # -- the action palette (`text._action`) ----------------------------
        self.AFFORDED = self.g.atom("action")
        self.LOADED = self.g.atom("loaded")
        self.SCOPED = self.g.atom("scoped")

        # -- triggers ------------------------------------------------------
        self.INTERCEPTS = self.g.atom("intercepts")
        self.PRODUCING = self.g.atom("producing")
        self.AFTER = self.g.atom("after")
        self.INSTEAD = self.g.atom("instead")
        self.DROP = self.g.atom("drop")
        self.REWROTE = self.g.atom("rewrote")

        # -- the gap between two states ------------------------------------
        # `delta(<have>, <want>, <gap>)`, and what a corpus reads off the gap
        # one difference at a time. Both states exist right now, so this is a
        # diff and not a memory -- which is why it survived the chain.
        self.DELTA = self.g.atom("delta")
        self.MISSING = self.g.atom("missing")
        self.MATCHED = self.g.atom("matched")
        self.EXTRA = self.g.atom("extra")
        # The state as it stands, which a corpus has no other hand to name.
        self.NOW = self.g.atom("now")
        self.ERASED = self.g.atom("erased")

        self.NUMERAL: Dict[int, NodeId] = {}

        # The knowledge base is a channel like any other (§13). Reading it
        # faithfully is guaranteed; what it *says* -- the rules -- stays as
        # contestable as anything else.
        self.KB = self.channels.open("kb")

        # Every name the machinery coins, in one place. The surface seeds its
        # table from this, so a name written in a rule is the SAME node the
        # machinery writes. Four separate bugs came from minting a reserved
        # atom beside this table -- each silent, each looking like a rule that
        # simply did not fire.
        self.reserved = {
            "says": self.SAYS, "arrived": self.ARRIVED, "kb": self.KB,
            "not": self.NOT,
            "rule": self.RULE, "ant": self.ANT, "con": self.CON,
            "names": self.NAMES,
            "count": self.COUNT, "counted": self.COUNTED,
            "recall": self.RECALL, "recalled": self.RECALLED,
            "dormant": self.DORMANT, "due": self.DUE,
            "standing": self.STANDING,
            "lane": self.LANE, "lane_order": self.LANE_ORDER,
            "bounded": self.BOUNDED, "ticks": self.TICKS,
            "close": self.CLOSE,
            "label": self.LABEL,
            "intensity": self.INTENSITY,
            "answers": self.ANSWERS, "answered": self.ANSWERED,
            "computes": self.COMPUTES, "action": self.AFFORDED,
            "loaded": self.LOADED, "scoped": self.SCOPED,
            "intercepts": self.INTERCEPTS, "producing": self.PRODUCING,
            "after": self.AFTER,
            "instead": self.INSTEAD, "drop": self.DROP,
            "rewrote": self.REWROTE,
            "delta": self.DELTA, "missing": self.MISSING,
            "matched": self.MATCHED, "extra": self.EXTRA, "now": self.NOW,
            "erased": self.ERASED,
            "believed": self.pad.BELIEVED,
            "implies": self.rules.IMPLIES,
            # The three modes as ARGUMENTS -- `ant($r, $p, assert, $i)`
            # mentions a mode where `+p` uses one.
            "assert": self.rules.MODE[ASSERT],
            "erase": self.rules.MODE[ERASE],
            "absent": self.rules.MODE[ABSENT],
        }
        # The numerals, seeded rather than minted on demand. A digit is
        # understood whether or not anything has asked for it yet -- `atom`
        # maps one to `_numeral` either way -- so a table that grew as the
        # session went reported the agent as understanding fewer names than it
        # did, which is the one thing a name census must not do.
        for i in range(10):
            self._numeral(i)

        # What the machinery keeps ABOUT its own conduct, as opposed to what
        # the world is about -- `_contents` uses it so a gap does not report
        # the apparatus as something to get rid of.
        self._bookkeeping = {
            self.RULE, self.ANT, self.CON, self.NAMES,
            self.COUNT, self.COUNTED, self.RECALL, self.RECALLED,
            self.DORMANT, self.DUE, self.STANDING,
            self.LANE, self.LANE_ORDER,
            self.BOUNDED, self.CLOSE,
            self.ANSWERS, self.ANSWERED, self.COMPUTES, self.AFFORDED,
            self.LOADED, self.SCOPED,
            self.INTERCEPTS, self.PRODUCING, self.REWROTE,
            self.DELTA, self.MISSING, self.MATCHED, self.EXTRA,
            self.ERASED, self.INTENSITY,
        }

        self.answerers: List[Answerer] = []
        self.selections = 0
        self.exhausted = 0
        self.matched = 0
        self.considered = 0
        self._reified: set = set()
        self._marker_cache: Dict[NodeId, Tuple[NodeId, ...]] = {}
        # Recorded by a firing's `stop` postcondition, obeyed by
        # `firing.run`'s own tick loop -- see that file's `_spend_one`.
        self._stopped: Optional[str] = None
        self._authoring_source: Optional[NodeId] = None
        self._saying_scope: Optional[str] = None
        # The bundle is not something the agent was TOLD -- it is what it reads
        # with.
        self._booting = True
        self.scopes: dict = {}
        # Empty until `_install_bundle` fills it, and read by the loader that
        # installs it -- a bundle rule is nameable from the corpus that is
        # loading it, including the bundle itself.
        self.bundle: List[Rule] = []

        #  Not corpus-registered, the way a `<dice>` computator is -- these
        # are language, not a tool: every corpus gets them, the way every
        # corpus gets `no`.
        self.rules.predicates[self.LABEL] = (
            lambda x, text: self.g.show(text) in self.g.labels_of(x))
        # `intensity($x) as $n` -- read `$x`'s CURRENT number. `$x` is a
        # PROPOSITION, not necessarily its own anchor -- the caller matched
        # it with an ordinary or `keep` member, which binds the proposition
        # (`Member.binds`), so this resolves through `occasion_intensity`
        # the same way `-p(a)` resolves an unbound ground pattern to
        # whichever occasion of that shape is believed. `0` -- not `None`,
        # not a refusal to answer -- for a node that is not currently
        # believed at all: asking how on an off thing is a legitimate
        # question with a legitimate answer, not a match failure, which is
        # why this is a node-computator (always answers, given a ground
        # node) rather than a predicate (answers about belonging, and this
        # is not that question).
        self.rules.node_computes[self.INTENSITY] = (
            lambda x: self._numeral(max(0, int(self.pad.occasion_intensity(x)))))

        self.rules.claims = self._claims
        self.rules.DORMANT = self.DORMANT
        self.rules.on_rule.append(self.reify)
        self.channels.sink = self._deliver
        self.gate.on_write.append(self._answer)
        self.gate.on_write.append(self._count)
        self.gate.on_write.append(self._remember)
        self.gate.on_write.append(self._delta)

        self._install_bundle()
        self._booting = False

    # -- the bundle --------------------------------------------------------

    def _install_bundle(self) -> None:
        """Load the conventions that ship as rules rather than as branches (§4).

        """
        from .text import load_file  # deferred: `text` imports `Machine`

        first = len(self.rules.rules)
        self._bundle_loader = load_file(self, self.BUNDLE)
        self.bundle = list(self.rules.rules[first:])
        self._vocabulary_is_surface_nameable()

    def _vocabulary_is_surface_nameable(self) -> None:
        """Every relation the bundle uses must be a name a corpus can write.

        Not a style rule. `Graph.atom` mints a fresh node per call -- names are
        not identity -- so a relation the bundle uses and `reserved` does not
        carry is a node the surface cannot reach. A corpus rule written against
        it would build a second node with the same name and never match, with
        nothing anywhere saying so.
        """
        known = set(self.reserved.values())
        known.add(self.NEW)
        missing: List[str] = []

        def visit(n: NodeId) -> None:
            rel = self.g.relation_of(n)
            if rel is None:
                # An ARGUMENT atom is a twin waiting to happen exactly as a
                # relation is.
                if (not self.g.is_var(n) and not self.g.members(n)
                        and n not in known and self.g.show(n) not in missing):
                    missing.append(self.g.show(n))
                return
            if rel not in known and self.g.show(rel) not in missing:
                missing.append(self.g.show(rel))
            if rel is self.NEW:
                return
            for m in self.g.members(n):
                visit(m)

        for r in self.bundle:
            for m in list(r.antecedent) + list(r.consequent):
                visit(m.pattern)
        if missing:
            raise RuntimeError(
                f"the bundle uses relations no corpus can name: {missing}. "
                f"Add them to `Machine.reserved` -- a name minted beside that "
                f"table is a second node with one name, and a corpus rule "
                f"about it would silently match nothing."
            )

    # -- rules as data -----------------------------------------------------

    def reify(self, rule: Rule) -> None:
        """Believe what a rule IS, so rules can be matched by rules.

        §14's worked example made real -- `+rule(<R>)` and the members of each
        side. Without it a rule is a node nobody anchored, so `match` cannot
        see it and R4's questions are answerable only by the engine.

        The patterns are **mentioned**, not used: `+ant(<R>, heat($a, $w))`
        claims something about a rule and binds nothing.
        """
        if rule.node in self._reified:
            return
        self._reified.add(rule.node)
        w = lambda p: self.gate.write(p, generic=True)
        w(self.g.rel(self.RULE, rule.node))
        for i, m in enumerate(rule.antecedent):
            w(self.g.rel(self.ANT, rule.node, m.pattern,
                         self.rules.MODE[m.sign], self._numeral(i)))
            self._reify_binds(w, self.ANT, rule.node, i, m)
        for i, m in enumerate(rule.consequent):
            w(self.g.rel(self.CON, rule.node, m.pattern,
                         self.rules.MODE[m.sign], self._numeral(i)))
            self._reify_binds(w, self.CON, rule.node, i, m)

    def _reify_binds(self, w, side, node, i, m) -> None:
        """...and the name the member gives what it matched (§12's `as`).

        A slot the graph does not record is a slot anything reading a rule back
        silently drops, and the rule that comes back is a different rule.
        """
        if m.binds is None:
            return
        w(self.g.rel(self.NAMES, side, node, self._numeral(i), m.binds))

    def _numeral(self, i: int):
        """A node for a small whole number. A numeral is an ordinary atom whose
        *name* reads as a number, so nothing in the graph learns arithmetic and
        only the reader that wants one does."""
        if i not in self.NUMERAL:
            self.NUMERAL[i] = self.g.atom(str(i))
            self.reserved.setdefault(str(i), self.NUMERAL[i])
        return self.NUMERAL[i]

    def reify_all(self) -> None:
        """Kept because instruments call it; it should find nothing to do.
        Rules are reified when they are authored (`RuleSet.on_rule`)."""
        for r in self.rules.rules:
            self.reify(r)

    # -- believing ---------------------------------------------------------

    def _note_that(self, relation: NodeId, *members: NodeId) -> NodeId:
        """Record that the machinery did something a rule may care about.

        A decision nobody can override still has to be legible, and the way to
        make it legible here is to put it in the same graph as everything else.

        Takes the PARTS, not the node, for `_claims`'s reason: this used to be
        `_note(g.rel(REL, ...))`, and the caller built a node whether or not
        the claim was already there. Returns the node the claim is on.
        """
        node = self.g.find_rel(relation, *members)
        if node is None:
            node = self.g.rel(relation, *members)
        elif self.pad.holds_any(node):
            return node
        self.gate.write(node, generic=True)
        return node

    def _claims(self, relation: NodeId, *members: NodeId) -> bool:
        """Is anything of this shape claimed? Builds nothing.

        Every caller used to be `self._claims(self.g.rel(REL, ...))`: a node
        minted for the asking and dropped. That is free only while `rel`
        interns. A node minted to ask a question is an occasion nobody
        claimed, and it stays in the relation and argument indexes the matcher
        walks -- so asking a question would slow down every later question.
        """
        p = self.g.find_rel(relation, *members)
        return p is not None and self.pad.holds_any(p)

    def holds(self, proposition: NodeId) -> bool:
        """Does the agent believe this? Presence of an anchor, and nothing
        else -- there is no last-claim-wins and no walk over a history.

        `holds_any` for `_claims`'s reason: callers reach this with
        `m.holds(kb.term("fled(hero)"))`, a node built from text to ask with.
        A caller holding a node it MATCHED, and asking about that node rather
        than about its shape, wants `pad.holds` directly.
        """
        return self.pad.holds_any(proposition)

    def _knob(self, relation: NodeId, default):
        """A knob a corpus can turn, read from the graph.

        Highest wins, so raising a bound is a claim and lowering it is a
        different claim about the same thing.
        """
        best = None
        for node in self.g.instances_of(relation):
            if not self.pad.holds(node):
                continue
            members = self.g.members(node)
            if not members:
                continue
            name = self.g.show(members[0])
            if name.isdigit() and (best is None or int(name) > best):
                best = int(name)
        return default if best is None else best

    # -- the tool seams ----------------------------------------------------

    def computator(self, name, fn) -> NodeId:
        """Register a function that is COMPUTED during a match (§12, §22).

        `{ +purse($a, $x), +cost($i, $c), minus($x, $c) as $new }`. Purity is
        structural here rather than declared: a computator is asked with ground
        arguments and answers with a node, and it claims nothing.
        """
        rel = self.g.atom(name) if isinstance(name, str) else name
        self.rules.computes[rel] = fn
        # ...and it is on the record, so *which of these exist* is a query
        # rather than a fact about the source (§17).
        self.gate.write(self.g.rel(self.COMPUTES, rel), generic=True)
        return rel

    def answerer(self, name: str, request: str, fn) -> "Answerer":
        """Register something that answers a request. A tool is not a new kind
        of thing: the name goes in the `<...>` namespace, which is the
        namespace of STATEMENTS, because a tool is something other statements
        are about."""
        try:
            inspect.signature(fn).bind(None, None)
        except TypeError:
            raise TypeError(
                f"answerer {name!r} does not take (machine, proposition) -- an "
                f"answerer is called with two arguments and returns the answer "
                f"node, or None for *I have nothing to say*"
            ) from None
        except (ValueError, AttributeError):
            pass  # a builtin or C callable has no signature to read
        rel = request if isinstance(request, int) else (
            self.reserved.get(request) or self.g.atom(request))
        node = self.g.atom(name)
        a = Answerer(name, node, rel, fn)
        self.answerers.append(a)
        self.gate.write(self.g.rel(self.ANSWERS, node, a.request), generic=True)
        return a

    def _answer(self, proposition: NodeId) -> None:
        """Call whatever answers this request, and record what it said.

        Deliberately not a conclusion. What lands is `answered(<M>, req, y)` --
        a record that M said so, the same treatment §17 gives every arrival.
        """
        if not self.answerers:
            return
        rel = self.g.relation_of(proposition)
        if rel is None:
            return
        for a in self.answerers:
            if a.request is not rel:
                continue
            if not self._claims(self.ANSWERS, a.node, a.request):
                continue
            said = a.fn(self, proposition)
            if said is None:
                continue
            answered = self.g.rel(self.ANSWERED, a.node, proposition, said)
            self.gate.write(answered, generic=True)

    def _count(self, proposition: NodeId) -> None:
        """Answer *how many ground matches does this pattern have?*

        `count(goblin($x))` is a request a corpus rule asks and
        `counted(<ask>, 2)` is the answer, and it always answers.
        """
        if self.g.relation_of(proposition) is not self.COUNT:
            return
        members = self.g.members(proposition)
        if len(members) != 1:
            return
        (pattern,) = members
        # A one-member probe, matched by the ordinary matcher.
        probe = Rule(proposition, [Member(ASSERT, pattern)], [], "<count>")
        # Distinct PROPOSITIONS, not applications: two ways of binding the same
        # proposition are one match of it. A guard rather than a repair.
        seen = set()
        for hit in match(self.g, self.pad, probe, computes=self.rules.computes):
            seen.add(substitute(self.g, pattern, hit.bindings))
        # Keyed on the ASK, not on the pattern, which is what makes the answer
        # readable at all.
        answer = self.g.rel(self.COUNTED, proposition, self._numeral(len(seen)))
        # A COUNT IS A FUNCTIONAL ATTRIBUTE, so the old one goes in the same
        # breath. Under the scratchpad that really is an erasure: the stale
        # answer is gone rather than outvoted by a fresher one.
        for old in list(self.g.instances_of(self.COUNTED)):
            if old == answer or self.g.member(old, 0) != proposition:
                continue
            self.gate.erase(old)
        self.gate.write(answer, generic=True)

    def _remember(self, proposition: NodeId) -> None:
        """Answer *what comes to mind about this?* (§19).

        What makes this an answer rather than a scan is `by_conclusion`: rules
        indexed by the relation they conclude, so *what could produce
        `w0_s8(item)`* is a lookup and not a search over the rule set. That is
        not experience -- it is an index, and it is exact.
        """
        if self.g.relation_of(proposition) is not self.RECALL:
            return
        members = self.g.members(proposition)
        if len(members) != 1:
            return
        self._answer_recall(members[0])

    def _answer_recall(self, about: NodeId) -> None:
        candidates = self.rules.by_conclusion.get(self.g.relation_of(about), ())
        for r in candidates:
            if (self._claims(self.DORMANT, r.node)
                    and not self._claims(self.DUE, r.node)):
                continue
            self.gate.write(self.g.rel(self.RECALLED, r.node, about),
                            generic=True)

    # -- the gap between two states ----------------------------------------

    def _contents(self, root: NodeId) -> set:
        """What a state holds, as propositions.

        Two kinds of root and they are one rule rather than two: `now` holds
        what is believed, and anything else holds its own members. A corpus
        builds a wanted state the way it builds any other compound --
        `state(at(work), holds(p1, key1))`.

        The apparatus's own records are not part of the world: the scratchpad
        holds `answers(...)` and `rule(...)` too, and a gap computed against
        them reports the machinery as something to be got rid of.
        """
        if root == self.NOW:
            return {p for p in self.pad.believed()
                    if self.g.relation_of(p) not in self._bookkeeping}
        return set(self.g.members(root))

    def _delta(self, proposition: NodeId) -> Optional[NodeId]:
        """`delta(<have>, <want>, <gap>)` -- what stands between two states.

        The answer is the gap node, and what a corpus reads off it is one
        difference at a time: `missing(<gap>, p)` for what the wanted state has
        and the held one lacks, `extra(<gap>, p)` for the reverse. Materialised
        rather than answered as a set, because a rule matches one proposition
        and there is nothing in the surface that walks a collection.

        A tool, so it PROPOSES: the gap is a record of what was computed here,
        and it is a rule that decides whether any of it is worth wanting.
        """
        if self.g.relation_of(proposition) is not self.DELTA:
            return None
        members = self.g.members(proposition)
        if len(members) != 3:
            return None
        have, want, gap = members
        #  By SHAPE, not by node. A difference between two states is a
        # difference between what they SAY, and the wanted state's `at(work)`
        # is a node the corpus built while the held one's is a node a rule
        # wrote. Those were one node while `rel` interned, so subtracting the
        # sets of ids answered the question by accident; subtracting them now
        # reports every proposition as both missing and extra.
        shape = self.g.shape_of
        held = {shape(p): p for p in self._contents(have)}
        wanted = {shape(p): p for p in self._contents(want)}
        absent = {k: wanted[k] for k in wanted.keys() - held.keys()}
        spare = {k: held[k] for k in held.keys() - wanted.keys()}
        # A gap asked again is asked about NOW, so a difference that has closed
        # since the last answer is ERASED rather than left standing. Under the
        # chain this took a denial and the records accumulated -- the water
        # arrives, the want is met, and `missing(<gap>, water(kettle))` still
        # read `+`. Here the stale difference simply stops being there.
        for rel, still in ((self.MISSING, absent), (self.EXTRA, spare)):
            for node in list(self.g.instances_of(rel)):
                mm = self.g.members(node)
                if len(mm) != 2 or mm[0] != gap:
                    continue
                if shape(mm[1]) not in still:
                    self.gate.erase(node)
        differed = False
        for props, rel in ((absent, self.MISSING), (spare, self.EXTRA)):
            for p in sorted(props.values()):
                if self.g.has_var(p):
                    # A description is not a difference: `at($x)` says which
                    # states would count, not that one of them is absent.
                    continue
                differed = True
                if not self._claims(rel, gap, p):
                    self.gate.write(self.g.rel(rel, gap, p), generic=True)
        matched = self.g.find_rel(self.MATCHED, gap)
        if differed:
            if matched is not None:
                self.gate.erase(matched)
        else:
            # The empty gap, said outright. A rule can read every difference
            # one at a time and still not be able to say there were none: that
            # is a claim about the whole set, and the tool is the only party
            # here that has seen the whole set.
            self._note_that(self.MATCHED, gap)
        return gap

    # -- the boundary ------------------------------------------------------

    def _deliver(self, a: Arrival) -> None:
        """Cross the boundary, and nothing else -- when the world speaks, not
        when the loop next gets round to asking.

        What an arrival MEANS is `<intake>`, which is a rule: crossing is
        anchored and a rule is generic, so the crossing stays machinery and the
        reading does not.
        """
        node = self.g.rel(self.ARRIVED, a.channel, a.proposition)
        self.gate.write(node)


    # -- the loop ----------------------------------------------------------

    def tick(self) -> Step:
        """One move of the loop, for a caller that wants to step and look.

        There is no table left to persist across calls (docs/design/
        intensity-gates.md): a tick matches every rule against whatever the
        graph holds right now, so stepping by hand and running straight
        through are the same loop at two different limits, not two
        different mechanisms the way the table era's `tick`/`run` split
        needed to be.
        """
        from .firing import run as _run

        steps = _run(self, limit=1).steps
        return steps[0] if steps else Step(0, 0, (), (), "quiescent")

    def run(self, limit: int = 100) -> List[Step]:
        """Bounded, and it returns a result *and* a state -- because a search
        that stopped is not a search that found nothing (§9, §15)."""
        from .firing import run as _run

        return _run(self, limit=limit).steps

    # -- applying ----------------------------------------------------------

    def _markers(self, rule) -> Tuple[NodeId, ...]:
        """The `+kind` marks in a rule's consequent, cached on the rule node.

        Scanned rather than declared, so a corpus writes `+person` where it
        wants one and nothing else changes.
        """
        got = self._marker_cache.get(rule.node)
        if got is None:
            found: List[NodeId] = []

            def walk(n: NodeId) -> None:
                if self.g.relation_of(n) is self.NEW:
                    if n not in found:
                        found.append(n)
                    return
                for mm in self.g.members(n):
                    walk(mm)

            for m in rule.consequent:
                walk(m.pattern)
            got = tuple(found)
            self._marker_cache[rule.node] = got
        return got

    def _pending(self, app: Application):
        """Everything one FIRING wants to write, computed but not yet done.

        Where `_apply` used to write straight into the scratchpad, this
        stops one step short (docs/design/intensity-gates.md's firing loop
        needs to): several rules fire in one tick now, order must not
        change the result, and "combine by max" is a question about every
        write TOGETHER, which nothing can answer while writes are landing
        one application at a time. So this returns the ingredients --

            app       the application, its bindings enriched with any
                      `+kind` marks this firing mints (a fresh entity per
                      distinct mark, same as `_apply` always did)
            pending   `(node, sign)` pairs, ASSERT or ERASE, after triggers
                      have had their say (`_intercept`, unchanged)
            values    of those, the ones that named their OWN intensity --
                      `+p(x) intensity $n` -- node -> the grounded number.
                      A node not in here that ends up in `pending` at
                      ASSERT gets the ordinary default (`scratchpad.ON`)
                      at the point something actually commits it.
            discharge every node this firing's own antecedent CONSUMED: a
                      `+` (not `keep`, not `no`) member that matched
                      something. Committing these at `0` is what makes
                      firing spend by default; a caller that wants a member
                      exempted writes `keep` at the surface, which is
                      already why `discharge` only holds `ASSERT`-matched
                      nodes and not `KEEP`-matched ones (`rules.match`
                      treats the two identically for MATCHING; this is the
                      one place they part company).

        and leaves turning them into a single set of writes, and applying
        those, to the caller -- which is `firing.run`, over every
        application that fired this tick at once.
        """
        # A rule may introduce a thing that did not exist. One node per
        # distinct marker per APPLICATION, so `+a(+p)` and `+b(+p)` in one
        # consequent are about the same new thing, and two firings are about
        # two things.
        marks = self._markers(app.rule)
        if marks:
            app = app._replace(bindings={
                **app.bindings,
                **{mk: self.g.entity() for mk in marks},
            })
        # What the rule concluded, before anything is written -- which is the
        # one moment a trigger can speak about it.
        pending: List[Tuple[NodeId, str]] = []
        values: Dict[NodeId, NodeId] = {}
        for m in app.rule.consequent:
            if _left_open(self.g, m.pattern, app.bindings):
                continue
            if m.sign == ERASE:
                #  Looked up, never built. A `-` names an occasion that is
                # already there, and building one to name it mints a node
                # nothing anchors -- which is `-p(a)` erasing nothing while
                # `p(a)` sits believed. Nothing of the shape means nothing to
                # stop believing, so the member drops out here rather than
                # travelling to the gate as a no-op a trigger could see.
                got = already_there(self.g, m.pattern, app.bindings)
                if got is None or got is GENERIC:
                    continue
                pending.append((got, ERASE))
                continue
            node = substitute(self.g, m.pattern, app.bindings)
            pending.append((node, m.sign))
            if m.write is not None:
                # The general intensity write (docs/design/intensity-gates.md):
                # `+p(x) intensity $n` grounds `$n` the same way `pattern`
                # itself just was, and the RESULT -- an atom whose name is a
                # number, `_numeral`'s own shape -- is read by the committer
                # below rather than resolved here, because a value bound to
                # an unfinished intercept rewrite (`instead(...)`) should
                # follow the node it now names rather than the one it was
                # written against.
                values[node] = substitute(self.g, m.write, app.bindings)
        pending = self._intercept(app, pending)
        discharge: List[NodeId] = [
            app.matched[i] for i, m in enumerate(app.rule.antecedent)
            if m.sign == ASSERT and app.matched[i] is not None
        ]
        return app, pending, values, discharge

    def _commit(self, writes: Dict[NodeId, float],
               generic: "set") -> Tuple[NodeId, ...]:
        """Turn one tick's collected `node -> intensity` map into the actual
        graph writes -- the other half of what `_apply` used to do in one
        breath, now done once for every application that fired together.

        `writes` already IS the max: the caller folds every application's
        contribution in with Python's own `max`, so by the time this runs
        there is exactly one number per node and no order left to depend
        on. A node whose number comes out at zero or below is erased --
        which is what a plain, unrecharged consumption looks like, and what
        an explicit `intensity 0` write means too (docs/design/
        intensity-gates.md: "`-p`... is retired... subsumed by the general
        intensity write") -- and a node above zero is written (mint or
        recharge) at that number.
        """
        wrote: List[NodeId] = []
        for node, value in writes.items():
            if value <= 0:
                if self.gate.erase(node):
                    wrote.append(node)
                continue
            # A CHANGE, not merely a touch: `<loud>` in `book/docs/watching/
            # 28-the-table.md`'s own example matches every tick forever and
            # writes the same `shouted` back at the same strength every
            # time -- and that is not new business, it is the fixpoint
            # `run`'s own quiescence check is watching for. Comparing
            # against the anchor's CURRENT number (0.0 if it has none) is
            # what tells "this tick re-affirmed what already held" from
            # "this tick actually moved something".
            anchor = self.pad.anchor(node)
            before = self.pad.intensity(anchor) if anchor is not None else 0.0
            self.gate.write(node, generic=(node in generic or self.g.has_var(node)),
                            intensity=value)
            if value != before:
                wrote.append(node)
        return tuple(wrote)

    # -- triggers ----------------------------------------------------------

    def _triggers(self) -> List["Rule"]:
        """The rules a corpus has marked as triggers, in the order the table
        would consider them: a trigger is an ordinary rule, so which one runs
        first is decided the way everything else is."""
        if not self.g.instances_of(self.INTERCEPTS):
            return []
        marked = [r for r in self.rules.rules
                  if self._claims(self.INTERCEPTS, r.node, self.AFTER)]
        standing = {r for r in marked
                    if self._claims(self.STANDING, r.node)}
        return sorted(marked, key=lambda r: (r not in standing,
                                             self.rules.rules.index(r)))

    def _intercept(self, app: Application,
                   pending: List[Tuple[NodeId, str]]) -> List[Tuple[NodeId, str]]:
        """Let the triggers rewrite what this application is about to write.

        A trigger sees each pending conclusion as `producing(<rule>, p)` -- a
        fact that exists only for this question, anchored for the length of it
        and taken back afterwards, because what a rule is ABOUT to conclude is
        not something the world holds. What a trigger concludes about one is
        read as an instruction:

            instead(p, q)   q lands where p would have
            drop(p)         p does not land at all
            anything else   lands as well, beside what the rule concluded

        So marking is adding, refusing is dropping, and wrapping is replacing,
        and a corpus writes all three as ordinary rules. Triggers run in table
        order and each sees the delta the one before it left, which is what
        makes two triggers on one conclusion answerable rather than a race.
        """
        triggers = self._triggers()
        if not triggers:
            return pending
        for t in triggers:
            if t is app.rule:
                continue  # a trigger does not intercept itself
            asked = self._producing(app, pending)
            try:
                found = match(self.g, self.pad, t, computes=self.rules.computes,
                              predicates=self.rules.predicates,
                              node_computes=self.rules.node_computes)
            finally:
                for node in asked:
                    self.gate.erase(node)
            if not found:
                continue
            pending = self._obey(t, pending, found)
        return pending

    def _producing(self, app: Application,
                   pending: List[Tuple[NodeId, str]]) -> List[NodeId]:
        """The pending conclusions, anchored for the length of the question and
        no longer. A claim that outlived the question would be a claim that the
        rule had concluded something it has not -- which the chain could only
        avoid by keeping these out of the state entirely. A scratchpad can put
        something down and pick it back up, so it does."""
        out = []
        for prop, _sign in pending:
            said = self.g.rel(self.PRODUCING, app.rule.node, prop)
            if not self.pad.holds_any(said):
                self.gate.write(said, generic=True)
                out.append(said)
        return out

    def _obey(self, trigger: "Rule", pending: List[Tuple[NodeId, str]],
              found) -> List[Tuple[NodeId, str]]:
        """Read a trigger's conclusions as instructions about the delta.

        An instruction names its operand by SHAPE. `instead(deploy($s),
        pending(deploy($s)))` is a pattern the trigger grounds, so the
        `deploy(web)` inside it is a node built to say WHICH conclusion --
        never the conclusion node itself, which the intercepted rule built.
        Those were one node while `rel` interned, and keying on the node meant
        the instruction silently matched nothing the moment they parted: the
        approval corpus wrote `deploy(web)` straight out, unapproved.
        """
        replaced: Dict[Tuple, NodeId] = {}
        dropped: set = set()
        added: List[Tuple[NodeId, str]] = []
        shape = self.g.shape_of
        for a in found:
            for m in trigger.consequent:
                # The EXISTING node of this shape, looked up rather than
                # minted, wherever one already exists -- `already_there`,
                # `-p(a)`'s own resolver. A trigger's conclusion is a
                # description built fresh from the trigger's own pattern
                # and this application's bindings, and two DIFFERENT
                # applications of one trigger describing the SAME thing
                # (docs/design/intensity-gates.md: several applications can
                # intercept the same tick now, one per firing that
                # triggered this trigger) must resolve to the SAME node,
                # or `added`'s own dedup below -- keyed on node identity --
                # cannot see that they agree, and each redundant derivation
                # mints its own twin. `circuit_breaker.ugm`'s `<watchdog>`
                # is exactly this: re-derived once per firing it observes,
                # and every twin it ever minted for `tries(...)` is a node
                # its OWN antecedent matches again next tick, compounding
                # without bound if this were not resolved here.
                got = already_there(self.g, m.pattern, a.bindings)
                if got is GENERIC:
                    continue  # a description is not an instruction
                said = got if got is not None else substitute(
                    self.g, m.pattern, a.bindings)
                if self.g.has_var(said):
                    continue  # a description is not an instruction
                rel = self.g.relation_of(said)
                if rel is self.INSTEAD and len(self.g.members(said)) == 2:
                    old, new = self.g.members(said)
                    replaced[shape(old)] = new
                elif rel is self.DROP and len(self.g.members(said)) == 1:
                    (gone,) = self.g.members(said)
                    dropped.add(shape(gone))
                else:
                    added.append((said, m.sign))
        if not (replaced or dropped or added):
            return pending
        out: List[Tuple[NodeId, str]] = []
        for prop, sign in pending:
            here = shape(prop)
            if here in dropped:
                self._rewrote(trigger, prop, None)
                continue
            if here in replaced:
                self._rewrote(trigger, prop, replaced[here])
                out.append((replaced[here], sign))
                continue
            out.append((prop, sign))
        for prop, sign in added:
            if (prop, sign) not in out:
                out.append((prop, sign))
        return out

    def _rewrote(self, trigger: "Rule", old: NodeId,
                 new: Optional[NodeId]) -> NodeId:
        """On the record, because a conclusion that is not what the rule said
        it concluded has to name who changed it."""
        return self._note_that(self.REWROTE, trigger.node, old,
                               new if new is not None else self.DROP)

    # -- asking ------------------------------------------------------------

    def web(self, rules=None) -> Tuple[dict, dict]:
        """For each relation name: how often it is READ (an antecedent member)
        and WRITTEN (a consequent member, or something believed).

        Meaning in an open class is given by the web. A VARIABLE in relation
        position is not a name, and reporting one was this instrument's own bug.
        """
        read: dict = {}
        written: dict = {}

        def name(node):
            rel = self.g.relation_of(node)
            if rel is None or self.g.is_var(rel):
                return None
            return self.g.show(rel)

        for r in (self.rules.rules if rules is None else rules):
            for x in r.antecedent:
                got = name(x.pattern)
                if got is not None:
                    read[got] = read.get(got, 0) + 1
            for x in r.consequent:
                got = name(x.pattern)
                if got is not None:
                    written[got] = written.get(got, 0) + 1
        for p in self.pad.believed():
            got = name(p)
            if got is not None:
                written[got] = written.get(got, 0) + 1
        return read, written

    def unwebbed(self, rules=None) -> List[str]:
        """Names some rule READS that nothing anywhere writes.

        The engine's own names are excluded, because the MACHINERY supplies
        them. Only this direction is a signal, and it was measured rather than
        assumed: *written and never read* reports a dozen names on healthy
        corpora -- the bookkeeping, plus a corpus's own OUTPUTS, since nobody
        reads an answer.
        """
        read, written = self.web(rules)
        return sorted(n for n in read
                      if not written.get(n) and n not in self.reserved)
