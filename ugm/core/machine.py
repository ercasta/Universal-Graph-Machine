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

    *Nothing applied* and *nothing came to mind* are different events (§15),
    and only the second should escalate.
    """

    arrivals: int
    proposed: int
    matched: int
    applied: Optional[Application]
    wrote: Tuple[NodeId, ...]
    state: str  # applied | quiescent


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


#: What `attend($x)` is worth when nobody says -- the MEDIUM. A corpus that
#: cares says a number; one that merely means *this one* should not have to
#: invent a scale to say so.
ATTENTION_START = 5

#: What a claim loses per tick when nobody says.
ATTENTION_DECAY = 1

#: What an incidental touch is worth -- what `_attend_written` gives a node
#: no one ever claimed. One tick, and then it is somebody else's turn. The
#: SAME for a channel arrival and for a corpus being loaded: choosing that
#: what the world said outweighs what a move wrote is the engine deciding
#: something only a corpus can.
ATTENTION_BRUSH = 1

#: The least a claim may fade to. Zero means it fades away entirely, which
#: is what almost everything wants. Above zero it is PINNED: it never leaves
#: the pool, so there is always something to be about.
ATTENTION_FLOOR = 0


#: How deep the attention stack may go. A backstop against a corpus that pushes
#: its way down for ever on ever-changing nodes, which the cycle test cannot
#: see -- the nodes are different every time.
FRAME_DEPTH = 8


class Frame:
    """One turn of attention: a queue of nodes, and what was pushed to open it.

    `push` suspends a line of work for another and `pop` returns to it. A
    frame is not only a queue of nodes: it is everything a sub-line of work
    has that the line above it must not lose.

    The graph is untouched by push and pop. This is not a transaction, there is
    no rollback, and nothing derived inside a frame stops existing when it is
    popped. Attention management is the whole of this. The one thing a pop does
    take back is the frame's own STANDING weights, and it does so simply by
    being discarded with the frame -- there is nothing to erase separately.
    """

    __slots__ = ("queue", "spec", "weights", "on")

    def __init__(self, on=()) -> None:
        # ONE pool, shared by every lane. It was briefly per-lane, on the
        # argument that what a reflex is about is not what the main line is
        # about -- but lanes that each remember something different are
        # lanes that can DIVERGE, and then which lane ran last decides what
        # the agent is thinking about. There is one agent.
        self.queue: List[Tuple[NodeId, int]] = []
        # node -> (start, decay, min, max).
        self.spec: Dict[NodeId, Tuple[int, int, int, int]] = {}
        self.on: Tuple[NodeId, ...] = tuple(on)
        # STANDING attention, by MAGNITUDE rather than position -- what
        # `attend($x, n)` means beside pushing `$x` onto `queue`. This used to
        # be a believed `attention(x, n)` proposition, argued for on the
        # ground that *dropping a Python set is not readable by any rule and
        # cannot be argued with*. It is engine state instead: attention is
        # control, not world knowledge, the same category error the RHS/
        # trigger split exists to keep out of a rule's declarative side
        # (`new_substrate.md`), and the "not readable" objection is answered
        # differently now -- `attentioned($x)` (a PREDICATE, not a belief)
        # lets a rule ask without the engine's scheduling state living in the
        # graph. Popped for free: this dict goes with the Frame object, no
        # erase loop needed.
        self.weights: Dict[NodeId, int] = {}


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

        # -- attention -----------------------------------------------------
        self.ATTENTION = self.g.atom("attention")
        self.SPAN = self.g.atom("attention_span")
        self.DEPTH = self.g.atom("frame_depth")
        self.PUSHED = self.g.atom("pushed")
        self.POPPED = self.g.atom("popped")
        self.DECLINED = self.g.atom("declined")
        self.UNATTENDED = self.g.atom("unattended")
        # -- reference lines (`new_substrate.md`) --------------------------
        # `attentioned($x)` -- which one, not a relevance gate (the 08-22
        # finding is about ORDERING moves and does not apply to picking a
        # referent). `label($x, paul)` -- does $x carry this label. Both are
        # PREDICATES (see `rules.match`): filters over an already-bound node,
        # never matched, never bound to.
        self.ATTENTIONED = self.g.atom("attentioned")
        self.LABEL = self.g.atom("label")

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
            "attention": self.ATTENTION,
            "attention_span": self.SPAN,
            "frame_depth": self.DEPTH,
            "pushed": self.PUSHED, "popped": self.POPPED,
            "declined": self.DECLINED, "unattended": self.UNATTENDED,
            "attentioned": self.ATTENTIONED, "label": self.LABEL,
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
        # the world is about. A queue full of these is a queue that says
        # nothing about the situation, so `_attend_written` skips them.
        self._bookkeeping = {
            self.RULE, self.ANT, self.CON, self.NAMES,
            self.COUNT, self.COUNTED, self.RECALL, self.RECALLED,
            self.DORMANT, self.DUE, self.STANDING,
            self.LANE, self.LANE_ORDER,
            self.BOUNDED, self.CLOSE,
            self.ATTENTION, self.SPAN, self.DEPTH,
            self.PUSHED, self.POPPED, self.DECLINED,
            self.ANSWERS, self.ANSWERED, self.COMPUTES, self.AFFORDED,
            self.LOADED, self.SCOPED,
            self.INTERCEPTS, self.PRODUCING, self.REWROTE,
            self.DELTA, self.MISSING, self.MATCHED, self.EXTRA,
            self.ERASED,
        }
        #  What is not worth THINKING ABOUT, which is a different question
        # from what is not part of the world. `_bookkeeping` answers the
        # second: `_contents` uses it so a gap does not report the apparatus
        # as something to get rid of.
        #
        # An ANSWER is in the first set and not the second. It is the agent's
        # own record that a tool said so -- not world state -- but it is also
        # NEW BUSINESS arriving from outside any rule, and the rule waiting on
        # it is never enabled unless it carries a token. Sharing one list made
        # `_answer`'s own `_attend_written` call a no-op, with a comment above
        # it saying exactly what must not happen.
        #
        # A DOUBT is the same shape one layer up: `close(...)` is still not
        # world state (`_contents` must keep excluding it), but it is what a
        # settling rule waits on, and a settling rule unattended is a
        # settling rule `_attended_first` throws away regardless of its table
        # score. Invisible while attention never decayed -- whatever was
        # already in the pool kept overlapping by accident -- and load-
        # bearing the moment it does (`attention.run`'s doubt branch).
        self._incidental = self._bookkeeping - {self.ANSWERED, self.CLOSE}

        self.answerers: List[Answerer] = []
        self.selections = 0
        self.exhausted = 0
        self.matched = 0
        self.considered = 0
        self._reified: set = set()
        self._marker_cache: Dict[NodeId, Tuple[NodeId, ...]] = {}
        
        self._evicted: set = set()
        self._readmitted = 0
        # Which lane is being run right now. The loop sets it per lane pass;
        # everything that reads or writes attention resolves through it, so
        # a reflex rule's `attend` lands in the reflex lane's own queue and
        # `attentioned($x)` asks about the lane doing the asking.
        self._lane = "main"
        # Attended since the last fade. A claim keeps its full strength
        # through the tick AFTER the one that made it -- otherwise
        # `_attend_written`, whose whole job is to lift the next tick,
        # would be faded to nothing before that tick ever matched.
        self._fresh_attention: set = set()
        self._frames: List[Frame] = [Frame()]
        self._floor = 0
        self._step_table = None
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
        self.rules.predicates[self.ATTENTIONED] = (
            lambda x: x in self._attended())
        self.rules.predicates[self.LABEL] = (
            lambda x, text: self.g.show(text) in self.g.labels_of(x))

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

    # -- the attention stack -----------------------------------------------

    def _lane_state(self, lane=None):
        """`(queue, spec, weights)` on the top frame. `lane` is accepted and
        ignored -- attention is shared, so every lane reads the one pool."""
        f = self._frames[-1]
        return (f.queue, f.spec, f.weights)

    @property
    def _attention(self) -> List[Tuple[NodeId, int]]:
        """The top frame's queue, which is what every reader of it wants."""
        return self._frames[-1].queue

    @_attention.setter
    def _attention(self, queue) -> None:
        self._frames[-1].queue = list(queue)

    def _push_frame(self, nodes):
        """Suspend what the agent was doing and open a frame on `nodes`.

        This is a call: `push($a, $b)` suspends the current line of work and
        opens a new one about the nodes named. What it runs there is whatever
        the table finds -- picking is attention's job, not push's.

        Returns None if the push did not happen, and that is RECORDED: a
        consultation that returned nothing and one that was never opened are
        two different things.
        """
        nodes = [n for n in nodes if n is not None and not self.g.has_var(n)]
        if not nodes:
            # Ground only, and silently so. A frame about no one is not a frame.
            return None
        key = frozenset(nodes)
        if any(frozenset(f.on) == key for f in self._frames):
            # `A -> B -> A` about something NEW is ordinary recursion and must
            # stay allowed; the same nodes again is the loop.
            self._declined_frame(self.PUSHED, nodes[0], "already_open")
            return None
        if len(self._frames) >= (self._knob(self.DEPTH, FRAME_DEPTH)
                                 or FRAME_DEPTH):
            self._declined_frame(self.PUSHED, nodes[0], "too_deep")
            return None
        frame = Frame(nodes)
        self._frames.append(frame)
        # Reversed, so the FIRST node named ends up at the front of the new
        # queue: `push($a, $b)` reads left to right and position is the
        # gradient, so the leftmost has to lift hardest.
        for node in reversed(nodes):
            self._attend(node)
        for node in nodes:
            self._note_that(self.PUSHED, node)
        return frame

    def _pop_frame(self, node: Optional[NodeId] = None) -> bool:
        """Return to the frame below, attending `node` on it.

        `pop($x)` carries one node back: the attention-level analogue of a
        return value.

        The frame's own standing weights go with it, and nothing else is
        touched. Everything the frame concluded stands -- popping a set of
        graph changes is a different feature, it does not exist, and it is not
        wanted. Gone rather than left standing, because a weight the frame set
        would go on lifting rules from the bottom of `_attended()` for the
        rest of the run, and the suspension would leak the very thing it exists
        to put away.
        """
        if len(self._frames) - 1 <= self._floor:
            # The root is not popped. A pop with nothing to return to is
            # declined on the record rather than raised, because a corpus that
            # pops too often is arguing with itself and that is its business.
            self._declined_frame(self.POPPED, node, "at_root")
            return False
        self._frames.pop()
        if node is not None and not self.g.has_var(node):
            self._attend(node)
            self._note_that(self.POPPED, node)
        return True

    def _declined_frame(self, what: NodeId, node, why: str) -> None:
        """A push or a pop that did not happen, on the record.

        Never silent: a stack that quietly did nothing would be
        indistinguishable from one that had nothing to do.
        """
        if node is None:
            return
        self._note_that(self.DECLINED, what, node, self.g.atom(why))

    def _attend(self, node: NodeId, weight=None, decay=None,
                floor=None, ceiling=None) -> bool:
        """*Think about this one.* -- what a postcondition spends when it
        attends, and an ordinary claim when it lands. Engine state, scoped to
        the frame -- see `Frame.weights`'s own comment for why this is not a
        believed proposition. True if this changed the standing weight."""
        if weight is None:
            weight = ATTENTION_START
        #  The OCCASION, not the description. A caller naming a term --
        # `attend(intake($e, $who), 3)` on a right-hand side, or a probe
        # asking in Python -- hands a node built for the naming, and attention
        # on a node nobody believes is a claim no rule can be lifted by.
        node = self.pad.occasion(node)
        self._push_attention(node, weight, decay, floor=floor, ceiling=ceiling)
        _q, _s, weights = self._lane_state()
        if weights.get(node) == weight:
            return False
        weights[node] = weight
        return True

    def _attend_written(self, wrote, start=None, floor=None) -> None:
        """What a move just wrote goes on the queue, at weight 1.

        Everything one move writes arrives at the same depth, so the queue
        alone cannot tell those nodes apart -- and a queue permanently full of
        undifferentiated nodes made the agent chase its own tail and quiesce 30
        moves early. A claimed `attention($x, 3)` outweighs them: weight 1 is
        *this is what just happened*, a multiplier is *and something says this
        part mattered*.
        """
        for prop in reversed(tuple(wrote or ())):
            # NOT the agent's own record-keeping: those are how the machinery
            # remembers what it did, not things the world is about.
            if self.g.relation_of(prop) in self._incidental:
                continue
            for node in self._nodes_of(prop, []):
                if self.g.relation_of(node) in self._incidental:
                    continue
                self._push_attention(node, start, floor=floor)

    def _nodes_of(self, node: NodeId, out: List[NodeId]) -> List[NodeId]:
        """A proposition, decomposed into every node it is made of."""
        if node in out:
            return out
        out.append(node)
        rel = self.g.relation_of(node)
        if rel is not None:
            self._nodes_of(rel, out)
        for m in self.g.members(node):
            self._nodes_of(m, out)
        return out

    def _push_attention(self, node: NodeId, start=None, decay=None,
                        lane=None, floor=None, ceiling=None) -> None:
        """To the top, at its strength. Nothing falls off the bottom.

        Re-attending something already in the queue MOVES it up rather than
        adding it twice: a thing thought about twice is one thing thought about
        recently, and a queue that held duplicates would let one node crowd out
        everything else the agent knows it is doing.
        """
        queue, spec, _w = self._lane_state(lane)
        if node in self._evicted:
            # The number the stack has to justify itself against: a node that
            # fell off the bottom and is wanted AGAIN is an outer focus a
            # sub-line evicted while it was still live.
            self._readmitted += 1
            self._evicted.discard(node)
        # `start is None` is a REVISIT: the right-hand side of some rule
        # touched this node without saying anything about how much it
        # matters. That RESTORES the claim to its own start -- it does not
        # restate it at the toucher's strength. `_attend_written` brushes
        # every node a move wrote, and a deliberate `attend($dir, 5)` names a
        # folder the very move that named it also writes to; restating would
        # let the move's own bookkeeping demote the claim it was making, in
        # the tick it was made. Touched again is *not forgotten yet*, and a
        # node no one ever claimed is worth a brush and no more.
        held = spec.get(node)
        if start is None:
            # A revisit keeps every field: nothing was said, so nothing
            # changes except that the claim is fresh again.
            start, decay, floor, ceiling = held or (
                ATTENTION_BRUSH, ATTENTION_DECAY, ATTENTION_FLOOR, None)
        else:
            start = max(1, start)
            # Each field falls back to what the node already had, so a rule
            # may change ONE of them by restating the ones before it -- the
            # price of a positional surface, and the reason `attend($x)`
            # alone means *just refresh it*.
            prev = held or (start, ATTENTION_DECAY, ATTENTION_FLOOR, None)
            decay = prev[1] if decay is None else max(1, decay)
            floor = prev[2] if floor is None else max(0, floor)
            ceiling = prev[3] if ceiling is None else max(1, ceiling)
        spec[node] = (start, decay, floor, ceiling)
        queue[:] = [(n, w) for n, w in queue if n != node]
        # Refreshed UP TO the ceiling and no further: a node named over and
        # over is not thereby the only thing the lane is about. NO ceiling
        # unless something asked for one -- an incidental brush must not set
        # one, or the brush a move gives a node it happened to write would
        # cap the deliberate claim the same move was making.
        queue.insert(0, (node, start if ceiling is None else min(start, ceiling)))
        self._fresh_attention.add(node)
        # NOTHING is dropped here. The queue used to be truncated to a span,
        # which asked only WHEN a thing arrived and never how much it was
        # said to matter -- so a deliberate `attend($dir, 5)` could be shoved
        # out by the seven nodes its own move incidentally wrote, in the tick
        # it was made. Length is the wrong bound. The only way out is
        # `_fade_attention`: a claim lasts as long as its strength and then
        # it is gone, and being third in line is not a reason for anything.

    def _fade_attention(self) -> int:
        """One tick of forgetting: every claim loses a point, and a claim at
        zero is not a claim. Returns how many fell out.

        Attention is a QUEUE whose strength is a NUMBER OF TICKS, not a
        position in a list of fixed length. `attend($x, 5)` means *this
        matters for five ticks*, and after five it is gone without anything
        having to say so. That is what replaced the span outright rather than
        merely backing it up: what a move incidentally wrote arrives at
        strength 1 and is gone by the tick after next, so the details of one
        move stop crowding out a standing claim made three moves ago -- which
        they did,
        because eviction only ever asked WHEN a thing arrived and never HOW
        MUCH it was said to matter.

        Nothing attended since the last fade is touched. A node pushed during
        tick N is meant to lift tick N+1; decrementing it at the top of N+1
        would delete it unmatched, and `_attend_written`'s weight of 1 would
        mean *never seen* rather than *seen once*.
        """
        queue, spec, _w = self._lane_state()
        before = len(queue)
        faded = []
        for n, w in queue:
            if n in self._fresh_attention:
                faded.append((n, w))
                continue
            rec = spec.get(n, (1, ATTENTION_DECAY, ATTENTION_FLOOR, None))
            faded.append((n, max(rec[2], w - rec[1])))
        kept = [(n, w) for n, w in faded if w > 0]
        alive = {n for n, _w in kept}
        for node, _w in faded:
            if node not in alive:
                # The claim goes; what it was WORTH stays. Discarding the
                # spec here throws away the one fact that makes a later
                # mention mean anything: a folder attended at 5, faded out,
                # and then named again came back at a brush's 1 -- so
                # bringing something up again could never outrank whatever
                # had been said more recently, however deliberate the
                # original claim. Forgetting a thing is not the same as
                # forgetting how much it mattered, and only the first of
                # those is what fading is for.
                self._evicted.add(node)
        queue[:] = kept
        self._fresh_attention.clear()
        return before - len(kept)

    def _consume(self, nodes) -> int:
        """Spend the attention on what a move used. Globally: one occasion,
        one use. Returns how many were on the list."""
        queue, spec, weights = self._lane_state()
        # The PROPOSITIONS matched, not the atoms they are made of. Spending
        # `kettle` because a rule used `heat(stove, kettle)` would strip
        # attention from everything else that mentions the kettle, which is
        # not what was used.
        gone = set(nodes)
        before = len(queue)
        queue[:] = [(n, w) for n, w in queue if n not in gone]
        for n in gone:
            spec.pop(n, None)
            weights.pop(n, None)
        return before - len(queue)

    def _unattend(self) -> int:
        """Stop thinking about whatever it was -- `reset`, for attention.

        Both the queue and the standing weights, cleared -- something must say
        it, or attention accumulates and attention that names everything
        narrows nothing. Plain dict/list clears now, not an erase loop: this
        is frame-scoped engine state (`Frame.weights`'s own comment), not a
        belief a corpus could be reading.
        """
        dropped = len(self._attended())
        queue, spec, weights = self._lane_state()
        queue[:] = []
        spec.clear()
        weights.clear()
        return dropped

    def _attended(self) -> List[NodeId]:
        """What the agent is thinking ABOUT: the nodes it claims `attention` of.

        The QUEUE first, then any standing weight not in it. ORDER IS NOT A
        SIGNAL: nothing reads position any more. Under decay the strength is
        the recency -- a claim made three ticks ago has had three taken off
        it -- so `_attended_first` and `_pull` rank by the number and by
        nothing else.

        It used to be a signal, and the bug that cost was this: `weights` is
        a dict in insertion order, so iterating it plainly put the node
        attended FIRST nearest the top, and a `len(attended) - i` gradient
        then handed the OLDEST claim the larger multiplier. The tail is still
        appended newest-first, which is now merely tidy rather than
        load-bearing.
        """
        out: List[NodeId] = [n for n, _w in self._attention]
        for node in reversed(list(self._lane_state()[2])):
            if node not in out:
                out.append(node)
        return out

    def _attention_asked(self) -> List[NodeId]:
        """Only what something CLAIMED attention of.

        The line is claimed vs derived, not weighted vs plain. Someone saying
        *attend to this* is a reason to bring rules to mind; the machinery
        noticing *this just happened* is not, and conflating them starved the
        shortlist -- an agent quiesced 32 moves early because a queue full of
        the last move's nodes decided which rules were matched at all.

        CLAIM order for the tail, never a set: which standing claim lifts
        hardest must not be decided by how many atoms the machinery happened
        to mint before the corpus was loaded -- and it no longer is, now that
        the claim order is `weights`'s own insertion order rather than a scan
        over the graph in mint order, which is what this docstring used to
        have to rule out rather than simply not produce.
        """
        claimed = list(self._lane_state()[2])
        want = set(claimed)
        out = [n for n, _w in self._attention if n in want]
        for n in claimed:
            if n not in out:
                out.append(n)
        return out

    def _attention_weights(self) -> dict:
        """Node -> its multiplier, for the lift. The STRONGER of the two, never
        the sum: a node both queued and claimed is not twice as salient, and
        adding them would make the weight a popularity count."""
        out = {n: w for n, w in self._attention}
        for node, weight in self._lane_state()[2].items():
            # By MAGNITUDE, not by value: a claimed `-5` is a stronger signal
            # than a queued `+1`, and comparing by value would let any lift at
            # all bury something that says *not this*.
            if abs(weight) > abs(out.get(node, 0)):
                out[node] = weight
        return out

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
            # An answer is NEW BUSINESS. It comes from outside any rule's
            # consequent, so it is in no `wrote` list and would carry no
            # attention -- and then the rule waiting for it is never enabled
            # and the request hangs answered but unread. Measured: the
            # approval corpus reaching `unattended` with
            # `answered(approve, pending(deploy(web)), yes)` believed and
            # `<approved>` never offered.
            self._attend_written((answered,))

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
        holds `answers(...)` and `attention(...)` too, and a gap computed
        against them reports the machinery as something to be got rid of.
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
        # And it is now what the agent is thinking about. Not via
        # `_attend_written`: an arrival whose proposition is ALREADY believed
        # writes nothing, so saying the same words a second time would move
        # nothing at all -- which is exactly the case a rule wants to notice,
        # because an utterance is identified by its content here and the
        # repetition is otherwise invisible. Attention is the one part of the
        # machine that can tell *said again* from *still true*: the claim is
        # restored to its start whether or not the belief changed, and fades
        # from there. The queue only -- `_push_attention` rather than
        # `_attend` -- because a standing weight never fades, and every
        # sentence ever typed keeping a permanent multiplier is not a memory
        # of anything.
        # ...and it is attended at the STARTING strength, not a brush's.
        # This used to match what a move's own incidental write gets, on the
        # ground that ranking arrival above write is the engine deciding for
        # the corpus -- but a loaded `fact` no longer gets a token AT ALL
        # (§20: background is not something to take care of), and a channel
        # is where "take care of this" now comes from BY DEFAULT. A brush's
        # one tick is enough runway for a rule that was already in play to
        # notice something changed; it is not enough for the crossing itself
        # to survive being one of several arrivals delivered in the same
        # batch (`m2.holds` needing the SECOND `say` in a corpus to still be
        # reachable a few ticks later). Still queue-only, still fades, still
        # no permanent multiplier -- `start` is a lifetime, not a `floor`.
        # The ARRIVAL, not only what arrived. `<intake>` reads
        # `arrived($channel, $said)`, and a token on the sentence is not a
        # token on the fact that it turned up -- with the gate asking about a
        # line's own node, attending the parts and not the whole left the
        # crossing rule unenabled and the run silent.
        self._attend_written((node,), start=ATTENTION_START)


    # -- the loop ----------------------------------------------------------

    def tick(self) -> Step:
        """One move of the loop, for a caller that wants to step and look.

        The table PERSISTS across calls, or a caller stepping by hand would be
        measuring a different agent each time.
        """
        from .attention import Table, _standing, run as _table_run

        if self._step_table is None:
            self._step_table = Table(self.g, self.rules.rules, _standing(self))
        steps = _table_run(self, limit=1, table=self._step_table).steps
        return steps[0] if steps else Step(0, 0, 0, None, (), "quiescent")

    def run(self, limit: int = 100) -> List[Step]:
        """Bounded, and it returns a result *and* a state -- because a search
        that stopped is not a search that found nothing (§9, §15)."""
        from .attention import run as _table_run

        return _table_run(self, limit=limit).steps

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

    def _apply(self, app: Application) -> Tuple[NodeId, ...]:
        """Write what the rule concluded into the scratchpad.

        `+p` anchors p; `-p` takes the anchor away. That is the whole of it,
        and it is why one connective is enough: there is no later moment for a
        conclusion to land in, so there is nothing for a second connective to
        mean.
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
            pending.append((substitute(self.g, m.pattern, app.bindings), m.sign))
        pending = self._intercept(app, pending)
        generic = app.rule.mentions
        wrote: List[NodeId] = []
        for grounded, sign in pending:
            if sign == ERASE:
                if self.gate.erase(grounded):
                    wrote.append(grounded)
                continue
            #  There is NO *already believed, so write nothing* here any
            # more. It was the one place the engine still said that a thing
            # said twice was said once, and that is the claim interning made
            # in the substrate: a second derivation is a second occasion, with
            # a token of its own for attention to spend. What stops a rule
            # re-deriving for ever is that it consumed what it matched on.
            self.gate.write(grounded, generic=generic or self.g.has_var(grounded))
            wrote.append(grounded)
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
                              predicates=self.rules.predicates)
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
                said = substitute(self.g, m.pattern, a.bindings)
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
