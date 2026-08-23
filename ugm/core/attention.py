"""The loop: a table over rules, take the first that matches, then spend.

The engine does not do any semantic work, it only does:

    a score per rule    ordered, tie broken by declaration order
    apply the first     highest-scoring rule whose antecedent matches
    then spend          run that rule's postconditions
    ...and STOP         if one of them said so, the run is over

No goal, no completeness, no widening. Those are corpus rules whose
postconditions spend attention: *refocusing* is a rule (`unattend`), *done* is
the output of a rule that checks against the goal (`stop`), and *suspend this
line of work for another* is two more (`push`, `pop`). Nothing here knows what
any of them is for.

See docs/design/attention.md.
"""

import time
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

from .graph import NodeId
from .machine import Machine, Step
from .rules import (STOP, UNATTEND, Application, Attend, Member, Pop, Push,
                    Rule, match, substitute)

# A rule the bundle marks `standing` is in the table at the default; everything
# else is in it at the floor. The author's own correction to an earlier sketch:
# do not mark a subset as *in* the table, because a rule nothing ever boosts
# would be dead, and deadness should be a thing the agent can be asked about
# rather than a thing the table quietly enforces.
STANDING = 10
FLOOR = 1

# How close is close, and how many rules may be in one window. Both are knobs,
# so in a corpus both are facts -- `tolerance(2)` already is one. The window is
# a PREFIX of the table: scores only fall as you go down it, so once a match is
# found at `s`, everything below `s - TOLERANCE` is irrelevant without being
# matched. The cap is a guard against a pathological table where forty rules
# sit on one score, not the mechanism.
TOLERANCE = 2
WINDOW = 3

# How many rules are matched before the loop admits its table was wrong.
# → docs/design/attention.md#how-many-rules-are-matched-before-the-loop-admit
SHORTLIST = 5

# The range a shortlist's own scores are mapped onto before a reranker's nudge
# is added to them. Small enough that a nudge can move something, wide enough
# that a strong preference is not thrown away.
NORM = 6

# How long a buff lives, and how far a rule may be lifted. Life.
# → docs/design/attention.md#how-long-a-buff-lives-and-how-far-a-rule-may-be
PULL = 6

# The default doubt-settling rule, and the author's correction to an earlier
# sketch of mine: the loop does not need to HOLD a tick waiting for doubt to be
# resolved, because a settling rule fires. 
# → docs/design/attention.md#the-default-doubt-settling-rule-and-the-author
SETTLE = """
rule <settle-doubt> = implies( { +close($a, $b) }, { +settled($a, $b) } )
"""
SETTLING = ("settle-doubt",)


class Post(NamedTuple):
    """A postcondition: a query, and what it SPENDS if the query holds.
    `query` is the name of a rule authored in the corpus whose ANTECEDENT is the
    query -- so the surface parses it, and this file adds no notation. Such
    rules never enter the table.

    `frozen` marks what a calibration process may not touch. It changes nothing
    about how the postcondition runs.
    """

    of: str  # the rule this hangs off
    query: Optional[str]
    spends: Tuple[object, ...]
    frozen: bool = False


class Table:
    """Scores over rules, ordered. `STANDING` or `FLOOR`, and nothing moves
    them after `absorb` -- the only thing that ever did was a buff."""

    def __init__(self, g, rules: Sequence[Rule], standing: set) -> None:
        self.g = g
        self.name_of: Dict[NodeId, str] = {}
        self.score: Dict[NodeId, int] = {}
        self.rank: Dict[NodeId, int] = {}
        self.by_name: Dict[str, Rule] = {}
        for i, r in enumerate(rules):
            self.score[r.node] = (
                STANDING if (r.node in standing or r.name in SETTLING) else FLOOR
            )
            # Declaration order, first declared winning, in case of a tie break.
            self.rank[r.node] = i
            if r.name:
                self.by_name[r.name] = r
                self.name_of[r.node] = r.name
        self.rules = list(rules)
        # Attention's rule-side lookup, built once because a rule's antecedent
        # does not change. `absorb` is the only thing that can invalidate it.
        self.by_relation = _by_relation(self.rules, self.g)
        # Why the run ended, if a postcondition ended it. A name rather than a
        # flag, because *why did you stop?* has to be answerable -- the same
        # reason the shipped loop's `_enough` returns what was named.
        self.stopped: Optional[str] = None
        # The score is FIXED once built: `STANDING` or `FLOOR`, moved only
        # by `absorb`.  What varies move to move is
        # the attention lift, and `order` takes that as an argument and keeps it
        # nowhere -- which is the whole of this file's line between the two kinds
        # of attention.
        self.now = 0
        # How many ticks this table has been run through. A table handed back for
        # a second run continues the count, and `now == 0` cannot tell *never
        # ran* from *ran tick 0* -- the exact case a host stepping one tick at a
        # time produces.
        self.ticked = 0

    def absorb(self, rules: Sequence[Rule], standing: set) -> int:
        """Take in rules the agent did not start with.

        **`adopt` means the rule set moves at run time**, and a table built
        once cannot see it: the rule was live, it was the node the graph
        described, and it never applied because nothing had a score for it. The
        round trip was open at the last step.

        A new rule enters at the floor like any other -- `standing` if the bundle
        says so. Nothing already in the table is touched.
        """
        added = 0
        for r in rules:
            if r.node in self.score:
                continue
            self.score[r.node] = (
                STANDING if (r.node in standing or r.name in SETTLING) else FLOOR
            )
            # Ranked after everything present, which IS authored order: a rule
            # adopted on tick 40 was authored on tick 40.
            self.rank[r.node] = len(self.rules)
            self.rules.append(r)
            if r.name:
                self.by_name[r.name] = r
                self.name_of[r.node] = r.name
            added += 1
        if added:
            # Rebuilt rather than appended to, because a rule adopted at run
            # time is the case `absorb` exists for and a stale lookup here fails
            # in the quietest way there is: the rule is in the table, at the
            # floor, and attention can never reach it. That is `adopt`'s own
            # round-trip defect one index along.
            self.by_relation = _by_relation(self.rules, self.g)
        return added

    def order(self, extra=None) -> List[Rule]:
        """Highest score first, ties by declaration order. `extra` is the
        ranking-time nudge, added but never kept: a reranker reorders what is
        in front of the agent now, and next move it is recomputed."""
        lift = extra or {}
        return sorted(
            self.rules,
            key=lambda r: (-(self.score[r.node] + lift.get(r.node, 0)),
                           self.rank[r.node]),
        )

    def _target(self, target: NodeId, bindings) -> Optional[NodeId]:
        """A rule node, or a variable the query bound to one."""
        if self.g.is_var(target):
            return None if not bindings else bindings.get(target)
        return target

class Report(NamedTuple):
    ticks: int
    applied: List[str]
    seconds: float
    tried: int  # rules whose antecedent was matched, over the whole run
    state: set
    table: "Table"
    doubts: int = 0
    windows: List[int] = []
    widenings: int = 0
    # One `Step` per move. `applied` above is
    # the same sequence as names; this carries the `Application` itself, which
    # is what a caller reading `s.applied.rule.name` needs.
    steps: List["Step"] = []
    # Members that could not be indexed and were answered by a scan, over this
    # run -- the totals beside `widenings`, and the per-member breakdown that
    # says which one to go and change. `scans` counts the fallbacks and
    # `scanned_nodes` the instances they walked, which is the one that ranks
    # them. `scanned` is `member as written -> [times, nodes]`.
    # See `rules._narrowed`.
    scans: int = 0
    scanned: Dict[str, List[int]] = {}
    scanned_nodes: int = 0


def _dormant(m: Machine, r: Rule) -> bool:
    """Claimed `dormant` and not yet claimed `due`.

    Deliberately NOT a mark on the rule that the engine reads. A mark authored
    once is relative to nothing: not to the situation, not to the goal, not to
    who is asking. As a pair of ordinary claims
    it is dated, attributable, deniable, and readable by rules, and `due` can be
    concluded by anything at all.
    """
    return (m._claims(m.g.rel(m.DORMANT, r.node))
            and not m._claims(m.g.rel(m.DUE, r.node)))


def _standing(m: Machine) -> set:
    """The rules the bundle deposits `standing(<R>)` about -- the default table,
    which already exists in all but name."""
    out = set()
    for node in m.g.instances_of(m.STANDING):
        members = m.g.members(node)
        if len(members) == 1 and m._claims(node):
            out.add(members[0])
    return out


def _by_relation(rules: Sequence[Rule], g) -> Dict[NodeId, List[NodeId]]:
    """Which rules could be about a relation: antecedent relation -> rule nodes.

    The rule-side half of attention's join, and it is built once per table
    rather than per move because a rule's antecedent does not change. `absorb`
    is what keeps it current when the rule set does.

    A member whose pattern is a bare variable or whose relation is a variable
    is filed under nothing. `+$p` is a rule about anything, and lifting it
    whenever anything is attended would lift it always -- which is the same
    thing as never, and costs a slot in every shortlist to say so.
    """
    out: Dict[NodeId, List[NodeId]] = {}
    for r in rules:
        seen = set()
        for mm in r.antecedent:
            if g.is_var(mm.pattern):
                continue
            rel = g.relation_of(mm.pattern)
            if rel is None or g.is_var(rel) or rel in seen:
                continue
            seen.add(rel)
            out.setdefault(rel, []).append(r.node)
    return out


def _pull(m: Machine, table: "Table",
          attended: Sequence[NodeId]) -> Dict[NodeId, int]:
    """Attention's rule-level lift: two dict reads and no matching.

    The join, and the reason attention is affordable where a query is not.
    Not summed over attended nodes.

    See docs/design/attention.md#pull.
    """
    lift: Dict[NodeId, int] = {}
    # POSITION is the strength. attended arrives newest-first, so what the
    # agent turned to last lifts hardest and what is about to fall off the
    # bottom barely lifts at all. A rule reachable from two attended nodes
    # takes the STRONGER, not the sum.
    # See docs/design/attention.md#position-is-the-strength-attended-arr
    weights = m._attention_weights()
    for i, node in enumerate(attended):
        # **Position times the learned multiplier.** Depth says how
        # recently the agent turned to a thing; the multiplier says how much a
        # lesson thinks it is worth. Neither alone is enough -- everything one
        # move wrote arrives at the same depth, so without a weight the queue
        # cannot separate them, which is exactly what sank attending the
        # right-hand side twice (20d, 20h).
        weight = max(1, PULL - i) * weights.get(node, 1)
        for rel in m.pad.relations_of(node):
            for r in table.by_relation.get(rel, ()):
                # By magnitude again, and for the same reason: a rule reachable
                # from a damped node and an attended one takes the stronger
                # signal, whichever way it points.
                if abs(weight) > abs(lift.get(r, 0)):
                    lift[r] = weight
    return lift


def _attended_first(found: List[Application], attended: Sequence[NodeId],
                    weights: Optional[dict] = None) -> List[Application]:
    """Order a rule's own applications by what the agent is thinking about.

    This is the half no rule-keyed buff can express, and it costs nothing.
    Stable, and that is what keeps the existing tie-break intact.

    See docs/design/attention.md#attended-first.
    """
    if len(found) < 2:
        return found
    at = set(attended)
    weights = weights or {}

    rank = {node: (len(attended) - i) * weights.get(node, 1)
            for i, node in enumerate(attended)}

    def weight(a: Application) -> int:
        # Weighted by POSITION here too, so an application binding what the
        # agent just turned to beats one binding what it is about to forget.
        # Summed, unlike the rule lift: binding two attended things really is
        # more about them than binding one, because a binding is the whole
        # move rather than a reason to look.
        return sum(rank.get(v, 0) for v in a.bindings.values() if v in at)

    scored = [(weight(a), i, a) for i, a in enumerate(found)]
    if not any(w for w, _i, _a in scored):
        return found  # nothing attended is in play here; do not touch the order
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [a for _w, _i, a in scored]


def _queries(m: Machine, posts: Sequence[Post]) -> set:
    return {p.query for p in posts if p.query}


def run(m: Machine, posts: Sequence[Post] = (), limit: int = 400,
        chooser=None, watch=None,
        pool: Optional[Sequence[Rule]] = None,
        table: Optional["Table"] = None) -> Report:
    """The loop, in full. Everything else in this file is bookkeeping."""

    
    queries = _queries(m, posts)
    # pool is what makes an EXPERT possible: one shared graph, one shared
    # chain, and a table over a SUBSET of the rules. Whether the pool was
    # HANDED to us decides whether it may grow.
    # → docs/design/attention.md#pool-is-what-makes-an-expert-possible-one-s
    fixed = pool is not None
    if pool is None:
        pool = m.rules.rules
    pool = [r for r in pool if r.name not in queries]
    # A caller may bring its own table, and docs/interpretation-feedback.md
    # is right that the day it matters is the day something else changes.
    # The ticks continue from table.now rather than restarting at 0.
    # → docs/design/attention.md#a-caller-may-bring-its-own-table-and-doc
    if table is None:
        table = Table(m.g, pool, _standing(m))
    # The frame this run serves, and the floor it may not pop past. A
    # nested run -- a consultation, a supposition, a table of agents -- starts on
    # whatever frame its caller was in, and popping the caller's frame out from
    # under it would be this stack's version of the bug `probes/experts.py`
    # records: a structure that looks like a stack and is not one.
    root = len(m._frames) - 1
    served = m._frames[root]
    # Set unconditionally, and this was a `if served.table is None`. A frame
    # keeps its table so a SUSPENDED line of work can be resumed inside a run;
    # across runs the caller decides, by passing one or not. Guarding the
    # assignment meant a second `run()` over a different pool resumed the FIRST
    # run's table -- the settling run's, holding one rule -- and the loop went
    # quiescent the moment it popped back to the root, with nothing to say why.
    served.table = table
    root_table = table
    prev_floor = m._floor
    m._floor = root
    base = table.now + 1 if table.ticked else 0
    by_rule: Dict[str, List[Post]] = {}
    for p in posts:
        by_rule.setdefault(p.of, []).append(p)

    applied: List[str] = []
    steps: List[Step] = []
    arrivals = 0
    tried = 0
    doubts = 0
    widenings = 0
    windows: List[int] = []
    # Sampled rather than reset: the graph is shared -- an expert, a table of
    # agents and a supposition all run over one -- so a run reports the scans
    # IT caused and clears nothing another caller is still counting.
    scans0 = {k: list(v) for k, v in m.g.scans.items()}
    t0 = time.time()
    for tick in range(base, base + limit):
        # Not a phase: the world may have spoken since the last move, and the
        # loop asks the same question in the same place. The anchor a corpus
        # reads the raw chain from, minted once per tick at the chain's end.
        # One anchor rather than one per moment, and the reason is cost: the
        # rule-level read is a fixpoint, so an unanchored one gives every
        # proposition its candidates and its winner. See `ask_read`.
        # → docs/design/attention.md#not-a-phase-the-world-may-have-spoken-since-the
        # *Whose line of work is this?** A `push` spent last tick left a
        # new frame on the stack, and the loop picks up ITS table here. That is
        # the whole of what turns a consultation into a resume: `experts.py`
        # re-runs the caller with a FRESH table on every return, and `tick`'s own
        # docstring says what that costs -- *a caller stepping by hand would lose
        # every buff between one tick and the next and be measuring a different
        # agent each time*.
        #
        # A frame with no expert keeps the rules of the frame below, table and
        # all: a push that discriminated nothing suspends attention without
        # changing whose rules are in play, and that case is worth having alone.
        current = m._frames[-1]
        if current is not served:
            served = current
            if current.table is None:
                current.table = (
                    Table(m.g, m._expert_pool(current.expert), _standing(m))
                    if current.expert is not None else table
                )
            table = current.table
        # A rule the agent authored since the last tick enters the table now.
        if current.expert is not None:
            # **From the EXPERT's pool, re-read, and this was `do not absorb
            # at all`.** Absorbing every authored rule into a consulted expert's
            # table would undo the `pool` argument one construct along -- but
            # absorbing NOTHING is the other error, and it is the one `absorb`
            # was written about: *the rule was live, it was the node the graph
            # described, and it never applied because nothing had a score for
            # it.* Measured: an expert that concludes `knows(medic, <splint>)`
            # mid-run has `<splint>` in its POOL and not in its TABLE, so a
            # resumed consultation is STALER than the re-run it replaces --
            # `set(bob)` never concluded. A frame holds its expert by name
            # precisely so the pool can grow; this is the half of that which
            # reaches the table.
            table.absorb([r for r in m._expert_pool(current.expert)
                          if r.name not in queries], _standing(m))
        elif not fixed:
            table.absorb([r for r in m.rules.rules if r.name not in queries],
                         _standing(m))

        arrivals = m.channels.since_last_tick() or 0

        table.now = tick
        table.ticked += 1

        window: List[Application] = []
        top = None
        # Dormancy, and it is the right form of *disable a rule*. A rule
        # claimed dormant is not considered until something claims it due --
        # which is all a callback is. Read every tick and at the register's
        # own position, never once when the pool is built: due can be concluded
        # mid-run, and a callback attached inside a...
        # → docs/design/attention.md#dormancy-and-it-is-the-right-form-of-dis
        attended = m._attended()
        # The queue has two uses and only one of them can starve. Ordering
        # a rule's own BINDINGS costs nothing -- the applications are already
        # in hand.
        # → docs/design/attention.md#the-queue-has-two-uses-and-only-one-of-the
        lift = None
        asked = m._attention_asked()
        if asked:
            lift = _pull(m, table, asked) or None
        ordered = [r for r in table.order(lift) if not _dormant(m, r)]
        cut = 0
        while cut < len(ordered) and not window:
            # One shortlist at a time. Score decides WHO is matched, which is
            # the whole proposal: a rule below the cut costs nothing at all.
            chunk = ordered[cut:cut + SHORTLIST]
            if cut:
                widenings += 1
            cut += SHORTLIST
            for r in chunk:
                if top is not None and table.score[r.node] < top - TOLERANCE:
                    break  # the prefix ends here, and the rest is not matched
                tried += 1
                found = match(m.g, m.pad, r, computes=m.rules.computes,
                              predicates=m.rules.predicates)
                # ...and WHICH of them, which the loop has never chosen. It
                # takes the first survivor and breaks, so the binding was
                # decided by the walk. Free: `found` is already here.
                if attended:
                    found = _attended_first(found, attended,
                                            m._attention_weights())
                #  There is NO per-candidate filter left. An application
                # that was tried and changed nothing is offered again, because
                # deciding that a rule has nothing further to give is the
                # corpus's judgement and not the engine's. A rule stops itself
                # by spending what it matched -- `-may(hero)` -- or by asking
                # for the absence of what it wrote. An occasion is consumed,
                # and a fact is not.
                for a in found:
                    window.append(a)
                    if top is None:
                        top = table.score[r.node]
                    break
                if len(window) >= WINDOW:
                    break
        if not window:
            # Nothing in the table matched. These are NOT ported logic.
            # →
            # docs/design/attention.md#nothing-in-the-table-matched-the-engine-says-so
            if m._widen():
                steps.append(Step(arrivals, 0, tried, None, (), "widened"))
                continue
            # The run is over, and WHICH silence it was goes on the record: the
            # option-set loop's callers read `steps[-1].state` in 33 places to
            # tell a finished search from one that hit the limit.
            steps.append(Step(arrivals, 0, tried, None, (), "quiescent"))
            break
        windows.append(len(window))
        # Who picks. The table picks by default -- that is System 1 -- but a
        # human stepping the corpus by hand, or the shipped arbitration acting
        # as a gold teacher, is the same signature and the same loop. The first
        # user of a KB is a person choosing moves; the table is what that use
        # leaves behind.
        chosen = window[0] if chooser is None else chooser(m, table, window)
        if chosen is None:
            break
        if len(window) > 1:
            # The doubt is DEPOSITED, not recorded: an entry a rule can match,
            # so a corpus reacts to it -- tiebreaking, or asking. The machinery
            # noticing something it must not decide and depositing a fact is
            # this repo's standing answer (`unsupported`, `contested`,
            # `defeated`, `blocked`), and `close` was the one occasion that was
            # written and never reacted to.
            fresh = False
            for rival in window[1:]:
                node = m.g.rel(m.CLOSE, chosen.rule.node, rival.rule.node)
                if not m.pad.holds(node):
                    m._note(node)
                    fresh = True
            if fresh:
                # Depositing IS the move. A settling rule -- the default one, or
                # a corpus's own -- is in the table and gets the next turn.
                doubts += 1
                steps.append(Step(arrivals, len(window), tried, None, (),
                                  "applied"))
                continue
            # ...and the backstop: the doubt already stands and nothing settled
            # it, so restating it changes nothing and the winner applies. A
            # corpus with no settling rule loses a tick, not the loop. 
            # Something applied, so the shortlist is trusted again.
            # →
            # docs/design/attention.md#and-the-backstop-the-doubt-already-stands-an
        m._widened = False
        wrote = m._apply(chosen)
        m._attend_written(wrote)
        applied.append(chosen.rule.name or "?")
        steps.append(Step(arrivals, len(window), tried, chosen,
                          tuple(wrote or ()), "applied"))
        if watch is not None:
            # AFTER the move, not at the choice: a tick that deposits a doubt
            # chooses and then does not apply, so watching at the choice
            # recorded a rule that never ran -- and a lesson built from that
            # sequence teaches a move that never happened.
            # →
            # docs/design/attention.md#after-the-move-not-at-the-choice-a-tick-that-d
            watch(m, table, window, chosen, tick, steps[-1])
        _spend_posts(m, table, chosen, tick)
        if table.stopped is not None:
            steps.append(Step(arrivals, 0, tried, None, (), "stopped"))
            # *Completion is the output of a rule*, and this is the loop obeying
            # one. It knows a rule spent `stop`; it does not know what a goal is,
            # which is the line this file has held from the start.
            break
    # The loop ran out of ITERATIONS, not out of work.
    # → docs/design/attention.md#the-loop-ran-out-of-iterations-not-out-of-w
    m._floor = prev_floor
    if steps and steps[-1].state == "applied":
        m.exhausted += 1
        m._note(m.g.rel(m.BOUNDED, m.TICKS))
    scanned = {}
    for k, v in m.g.scans.items():
        was = scans0.get(k, [0, 0])
        if v[0] > was[0]:
            scanned[k] = [v[0] - was[0], v[1] - was[1]]
    return Report(
        # The ROOT table, not whichever frame the run ended in. A caller that
        # handed its table in gets that table back, which is what `a table can
        # outlive a run` is about, and a consulted expert's table belongs to its
        # frame rather than to this report.
        len(applied), applied, time.time() - t0, tried, _state(m), root_table,
        doubts, windows, widenings, steps,
        sum(v[0] for v in scanned.values()), scanned,
        sum(v[1] for v in scanned.values()),
    )


def _ground(m: Machine, table: Table, term, bindings):
    """What a spend NAMES, with the move's own bindings put in.

    `Table._target` answers for a bare variable and hands a COMPOUND back
    unchanged, which reads as an answer and is not one: `push(area($r))` came
    back as the pattern, still generic, and was dropped as *ground only* one
    layer from the mistake. A spend may name a whole proposition -- that is what
    `push` is for -- so the bindings go in the way they go into a postcondition's
    query, by substitution.
    """
    node = table._target(term, bindings)
    if node is None:
        node = term
    if node is not None and m.g.has_var(node) and bindings:
        node = substitute(m.g, node, bindings)
    return node


def _spend_one(m: Machine, table: Table, tick: int, by: str, spends, frozen,
               bindings, rule_node) -> None:
    """Spend one postcondition: attention to the machine, a stop to the table.

    **The split is the design, not plumbing.** A deposit writes a claim the
    corpus can read, deny and reason about, and a table that could write claims
    would be an interpreter with a memory. A stop writes nothing and only says
    the run is over, so it is the one thing recorded on the table.

    """
    for target, _delta in spends:
        if isinstance(target, Attend):
            node = _ground(m, table, target.term, bindings)
            # Ground only, and silently so. A postcondition naming a variable
            # the move did not bind has nothing to attend TO, and depositing
            # `attention($x)` would be a claim about no one -- which `_attended`
            # would then refuse to read, one layer further from the mistake.
            if node is not None and not m.g.has_var(node):
                # The learned WEIGHT rides along: `attend($x, 3)` says this
                # node matters more than whatever else is in the queue at the
                # same depth -- a calibration that names a node instead of a
                # rule.
                m._attend(node, weight=target.weight)
            continue
        if isinstance(target, Push):
            # A CALL. The nodes are the host rule's own variables, bound by
            # the move that spent this -- and the expert is computed from them,
            # never named. Ground only, like `attend`, and for the same reason.
            nodes = []
            for term in target.terms:
                node = _ground(m, table, term, bindings)
                if node is not None and not m.g.has_var(node):
                    nodes.append(node)
            m._push_frame(nodes)
            continue
        if isinstance(target, Pop):
            # ...and a RETURN. The loop finds the restored frame at the top of
            # the next tick and picks its table back up, which is what makes the
            # caller's re-run a resume.
            node = _ground(m, table, target.term, bindings)
            m._pop_frame(node if node is not None and not m.g.has_var(node)
                         else None)
            continue
        if target is UNATTEND:
            m._unattend()
            continue
        if target is STOP:
            # Recorded here, obeyed by the loop. Keeping the decision out of the
            # spend is what lets *why did you stop?* answer with a rule's name
            # rather than a flag.
            table.stopped = by


def _spend_posts(m: Machine, table: Table, chosen: Application,
                 tick: int) -> None:
    """Run the applied rule's postconditions and move the table.

    The query is matched with the application's own bindings already
    substituted in, which is what makes it a POSTcondition rather than a second
    rule: `after { +p($x) }` asks about the `$x` this rule just bound. A
    bare `after` has no query and holds always.
    """
    name = chosen.rule.name or "?"
    for query, spends, frozen, _learned in m.rules.triggers.get(
            chosen.rule.node, ()):
        if not query:
            _spend_one(m, table, tick, name, spends, frozen, chosen.bindings,
                       chosen.rule.node)
            continue
        probe = Rule(
            chosen.rule.node,
            [Member(mm.sign, substitute(m.g, mm.pattern, chosen.bindings),
                    mm.binds) for mm in query],
            [], f"{name}-after",
        )
        for hit in match(m.g, m.pad, probe, computes=m.rules.computes,
                         predicates=m.rules.predicates):
            bound = dict(chosen.bindings)
            bound.update(hit.bindings)
            _spend_one(m, table, tick, name, spends, frozen, bound,
                       chosen.rule.node)


def _state(m: Machine) -> set:
    """What the agent ends up holding, as printed propositions. The comparison
    has to be over conclusions rather than over moves: two loops that reach the
    same beliefs by different routes agree about the world, and that is the
    question."""
    return {m.g.show(p) for p in m.pad.believed()}
