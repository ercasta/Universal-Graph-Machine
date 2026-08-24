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
from .rules import (ABSENT, STOP, UNATTEND, Application, Attend, Destroy, Forget, Label,
                    Member, Merge, Pop, Push, Rule, Unlabel, Unmerge, match,
                    substitute)

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


def _lane_of(m: Machine, r: Rule) -> str:
    """Which lane a rule runs in -- `lane(<R>, $name)`, claimed.

    Unmarked rules default to `main`, which is the whole of what makes lanes
    additive: a corpus that never writes `lane(...)` runs exactly one lane,
    every tick, exactly as it did before lanes existed.
    """
    for node in m.g.instances_of(m.LANE):
        members = m.g.members(node)
        if len(members) != 2 or members[0] is not r.node:
            continue
        if not m._claims(node):
            continue
        return m.g.show(members[1])
    return "main"


def _lane_order(m: Machine) -> List[str]:
    """The lanes a tick drives, in order.

    `lane_order(<name>, $n)` ranks the lanes a corpus cares to order,
    numeral-sorted; a lane that is claimed (by some rule's `lane(...)`) but
    never ranked runs after every ranked one, in the order the graph met it --
    so adding a lane costs nothing beyond naming it. `main` always exists,
    because an unmarked rule has to land somewhere.
    """
    ranked: Dict[str, int] = {}
    for node in m.g.instances_of(m.LANE_ORDER):
        members = m.g.members(node)
        if len(members) != 2 or not m._claims(node):
            continue
        digits = m.g.show(members[1])
        if digits.isdigit():
            ranked[m.g.show(members[0])] = int(digits)
    seen: List[str] = ["main"]
    for node in m.g.instances_of(m.LANE):
        members = m.g.members(node)
        if len(members) != 2 or not m._claims(node):
            continue
        name = m.g.show(members[1])
        if name not in seen:
            seen.append(name)
    declared = sorted((n for n in seen if n in ranked), key=lambda n: ranked[n])
    rest = [n for n in seen if n not in ranked]
    return declared + rest


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
    # STRENGTH is the strength, and position is nothing. Decay already puts
    # what the agent turned to last at the top of the numbers, so lifting by
    # queue position as well counted recency twice. A rule reachable from two
    # attended nodes takes the STRONGER, not the sum.
    weights = m._attention_weights()
    for node in attended:
        # The claim's own number, which is what a lesson calibrates and what
        # decay has already aged. Everything one move wrote arrives at the
        # same strength, and separating those is the weight's job -- which is
        # exactly what sank attending the right-hand side twice (20d, 20h).
        weight = weights.get(node, 1)
        for rel in m.pad.relations_of(node):
            for r in table.by_relation.get(rel, ()):
                # By magnitude again, and for the same reason: a rule reachable
                # from a damped node and an attended one takes the stronger
                # signal, whichever way it points.
                if abs(weight) > abs(lift.get(r, 0)):
                    lift[r] = weight
    return lift


def _attended_first(found: List[Application], attended: Sequence[NodeId],
                    weights: Optional[dict] = None,
                    g=None) -> List[Application]:
    """Pick a rule's applications by what the agent is thinking about, and
    order what is left. This is the half no rule-keyed buff can express.

    Stable, and that is what keeps the existing tie-break intact.
    """
    if not found or g is None:
        return found
    rule_antecedent = found[0].rule.antecedent
    at = set(attended)
    weights = weights or {}

    # STRENGTH, and position not at all. Under decay the strength already IS
    # the recency -- a claim made three ticks ago has had three ticks taken
    # off it -- so multiplying by where the node sits in the queue counts the
    # same fact twice. It also counted it in the half a corpus cannot reach:
    # `attend($x, start, decay, min, max)` says what a claim is worth and how
    # fast it goes, and says nothing about queue position, so a calibration
    # could not have moved the positional half however hard it searched.
    rank = {node: weights.get(node, 1) for node in attended}

    seen_nodes: dict = {}

    def parts(node):
        """Every node a grounded line is made of, cached across applications."""
        got = seen_nodes.get(node)
        if got is None:
            got = set()
            stack = [node]
            while stack:
                n = stack.pop()
                if n is None or n in got:
                    continue
                got.add(n)
                rel = g.relation_of(n)
                if rel is not None:
                    stack.append(rel)
                stack.extend(g.members(n))
            seen_nodes[node] = got
        return got

    def score(a: Application):
        """`sum_i c_i * m_i(what line i bound)`, and whether it overlaps.

        PER LINE, which is the whole of it. Summing attention over everything
        an application touched cannot say *attention on the event matters,
        attention on the participants does not* -- and a rule-level priority
        cannot say it either. The multiplier hangs on the line, so the corpus
        chooses which binding attention is allowed to lift.

        An `absent` member matched by NOT being there bound nothing, so it
        contributes its constant and no attention.
        """
        total = 0.0
        overlaps = False
        for member in rule_antecedent:
            att = 0
            if member.sign != ABSENT:
                try:
                    node = substitute(g, member.pattern, a.bindings)
                except Exception:
                    node = None
                if node is not None:
                    # WHAT THE LINE BOUND, not everything it is made of.
                    # `$z=intake($x, $y)` binds the event; taking the max over
                    # the decomposition would let attention on a participant
                    # lift the event's line, and then a multiplier hung on the
                    # event says nothing a rule-level priority could not. The
                    # participants get their own lines, with their own numbers.
                    here = a.bindings.get(member.binds) if member.binds else None
                    att = rank.get(here if here is not None else node, 0)
                    if att:
                        overlaps = True
                    # The GATE asks about the LINE'S OWN node, never its
                    # parts. A token sits on a proposition, not on the atoms
                    # it is made of -- and asking about parts let a spent
                    # occasion stay enabled because something else had
                    # re-attended one of its constituents. Measured: `<boil>`
                    # firing for ever off `heat(stove, kettle)` because the
                    # `boiling(kettle)` it wrote re-attended `kettle`.
                    if not overlaps and node in at:
                        overlaps = True
            total += member.weight * (1.0 + member.att_mult * att)
        return total, overlaps

    scored = []
    for i, a in enumerate(found):
        total, overlaps = score(a)
        scored.append((total if overlaps else 0, i, a))
    # An application about NOTHING the agent is attending to does not apply.
    # Not merely last: gone. That is the whole of what a corpus otherwise has
    # to write by hand, and writing it by hand is worse than useless -- it
    # looks like a filter over folders when it is really the loop's own
    # question asked in the wrong place.
    #
    # There is NO exception for an empty pool. Attending to nothing means
    # there is nothing for work to be about, and the computation is meant to
    # fade out rather than idle on. Whatever must keep running says so, with
    # a min.
    overlapping = [t for t in scored if t[0]]
    if not overlapping:
        return []
    # Otherwise attention DECIDES, and not merely orders. An application
    # binding nothing the agent is attending to is dropped while one that
    # does exists, so a rule does not have to say `attentioned($x)` to mean
    # *the one I am looking at* -- which was the corpus writing out, by hand,
    # the question the loop is already asking. Highest score first, and the
    # score is position times strength, so it is the thing most recently and
    # most strongly turned to.
    overlapping.sort(key=lambda t: (-t[0], t[1]))
    return [a for _w, _i, a in overlapping]


def _queries(m: Machine, posts: Sequence[Post]) -> set:
    return {p.query for p in posts if p.query}


def run(m: Machine, posts: Sequence[Post] = (), limit: int = 400,
        chooser=None, watch=None,
        table: Optional["Table"] = None) -> Report:
    """The loop, in full. Everything else in this file is bookkeeping."""

    queries = _queries(m, posts)
    rules = [r for r in m.rules.rules if r.name not in queries]
    # A caller may bring its own table, and docs/interpretation-feedback.md
    # is right that the day it matters is the day something else changes.
    # The ticks continue from table.now rather than restarting at 0.
    # → docs/design/attention.md#a-caller-may-bring-its-own-table-and-doc
    if table is None:
        table = Table(m.g, rules, _standing(m))
    # The frame this run serves, and the floor it may not pop past. A
    # nested run -- a supposition, a table of agents -- starts on whatever
    # frame its caller was in, and popping the caller's frame out from under
    # it would be a structure that looks like a stack and is not one.
    root = len(m._frames) - 1
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
    # Sampled rather than reset: the graph is shared -- a table of agents and
    # a supposition all run over one -- so a run reports the scans IT caused
    # and clears nothing another caller is still counting.
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
        # A rule the agent authored since the last tick enters the table now.
        # A push suspends attention, not whose rules are in play, so the one
        # table serves every frame this run touches.
        table.absorb([r for r in m.rules.rules if r.name not in queries],
                     _standing(m))

        arrivals = m.channels.since_last_tick() or 0

        table.now = tick
        table.ticked += 1


        # Lanes (§ lanes): one pass through the table per lane, in order,
        # against the ONE shared frame -- a judge rule sees what a regular
        # rule just wrote, in the same tick, because a gut feeling is meant
        # to be a reaction to what just happened rather than a deliberation
        # of its own. A corpus that never claims `lane(...)` gets exactly one
        # lane (`main`), so this is a superset of the old single-pass tick,
        # not a different loop.
        round_applied = False
        doubted = False
        stopped = False
        unattended = 0
        for lane_name in _lane_order(m):
            # Everything attention-shaped below resolves through this.
            m._lane = lane_name
            window: List[Application] = []
            top = None
            # Dormancy, and it is the right form of *disable a rule*. A rule
            # claimed dormant is not considered until something claims it due
            # -- which is all a callback is. Read every tick and at the
            # register's own position, never once when the pool is built:
            # due can be concluded mid-run, and a callback attached inside a...
            # → docs/design/attention.md#dormancy-and-it-is-the-right-form-of-dis
            attended = m._attended()
            # Recomputed per LANE, not once per tick: the previous lane in
            # this same round may just have written something, and the next
            # lane's pick has to see it -- the one new cost lanes add.
            lift = None
            asked = m._attention_asked()
            if asked:
                lift = _pull(m, table, asked) or None
            ordered = [r for r in table.order(lift) if not _dormant(m, r)
                      and _lane_of(m, r) == lane_name]
            cut = 0
            while cut < len(ordered) and not window:
                # One shortlist at a time. Score decides WHO is matched, which
                # is the whole proposal: a rule below the cut costs nothing.
                chunk = ordered[cut:cut + SHORTLIST]
                if cut:
                    widenings += 1
                cut += SHORTLIST
                for r in chunk:
                    if top is not None and table.score[r.node] < top - TOLERANCE:
                        break  # the prefix ends here, the rest is not matched
                    tried += 1
                    found = match(m.g, m.pad, r, computes=m.rules.computes,
                                  predicates=m.rules.predicates)
                    # ...and WHICH of them, which the loop has never chosen.
                    # It takes the first survivor and breaks, so the binding
                    # was decided by the walk. Free: `found` is already here.
                    had = len(found)
                    found = _attended_first(found, attended,
                                            m._attention_weights(), m.g)
                    if had and not found:
                        # MATCHED and then discarded on attention grounds.
                        # Free to notice -- the work of matching is already
                        # done -- and the loop is otherwise about to call
                        # this silence a finished search.
                        unattended += 1
                    #  There is NO per-candidate filter left. An application
                    # that was tried and changed nothing is offered again,
                    # because deciding that a rule has nothing further to give
                    # is the corpus's judgement and not the engine's. A rule
                    # stops itself by spending what it matched -- `-may(hero)`
                    # -- or by asking for the absence of what it wrote. An
                    # occasion is consumed, and a fact is not.
                    for a in found:
                        window.append(a)
                        if top is None:
                            top = table.score[r.node]
                        break
                    if len(window) >= WINDOW:
                        break
            if not window:
                # This lane offered nothing this round -- the next lane still
                # gets its turn. Only when EVERY lane comes up empty is the
                # run over (below, once the lane loop ends).
                continue
            windows.append(len(window))
            # Who picks. The table picks by default -- that is System 1 -- but
            # a human stepping the corpus by hand, or the shipped arbitration
            # acting as a gold teacher, is the same signature and the same
            # loop. The first user of a KB is a person choosing moves; the
            # table is what that use leaves behind.
            chosen = window[0] if chooser is None else chooser(m, table, window)
            if chosen is None:
                continue
            if len(window) > 1:
                # The doubt is DEPOSITED, not recorded: an entry a rule can
                # match, so a corpus reacts to it -- tiebreaking, or asking.
                # The machinery noticing something it must not decide and
                # depositing a fact is this repo's standing answer
                # (`unsupported`, `contested`, `defeated`, `blocked`), and
                # `close` was the one occasion that was written and never
                # reacted to.
                fresh = False
                for rival in window[1:]:
                    node = m.g.rel(m.CLOSE, chosen.rule.node, rival.rule.node)
                    if not m.pad.holds(node):
                        m._note(node)
                        fresh = True
                if fresh:
                    # Depositing IS the move. A settling rule -- the default
                    # one, or a corpus's own -- is in the table and gets the
                    # next turn. Ends the ROUND, not just this lane: the doubt
                    # is what this tick did.
                    doubts += 1
                    steps.append(Step(arrivals, len(window), tried, None, (),
                                      "applied"))
                    doubted = True
                    break
                # ...and the backstop: the doubt already stands and nothing
                # settled it, so restating it changes nothing and the winner
                # applies. A corpus with no settling rule loses a tick, not
                # the loop. Something applied, so the shortlist is trusted
                # again.
                # →
                # docs/design/attention.md#and-the-backstop-the-doubt-already-stands-an
            # CONSUMED, and consumed globally. Attention is not memory: it
            # is what the agent still has to get to, so using a thing is what
            # takes it off the list. A rule that leaves work for another rule
            # on the same node says so with `brush` -- explicitly, because
            # two rules sharing an occasion is a claim about the corpus and
            # not something the engine should infer.
            m._consume(_matched_nodes(m, chosen))
            wrote = m._apply(chosen)
            # ...and what it wrote is new business.
            m._attend_written(wrote)
            applied.append(chosen.rule.name or "?")
            steps.append(Step(arrivals, len(window), tried, chosen,
                              tuple(wrote or ()), "applied"))
            round_applied = True
            if watch is not None:
                # AFTER the move, not at the choice: a tick that deposits a
                # doubt chooses and then does not apply, so watching at the
                # choice recorded a rule that never ran -- and a lesson built
                # from that sequence teaches a move that never happened.
                # →
                # docs/design/attention.md#after-the-move-not-at-the-choice-a-tick-that-d
                watch(m, table, window, chosen, tick, steps[-1])
            _spend_posts(m, table, chosen, tick)
            if table.stopped is not None:
                steps.append(Step(arrivals, 0, tried, None, (), "stopped"))
                # *Completion is the output of a rule*, and this is the loop
                # obeying one. It knows a rule spent `stop`; it does not know
                # what a goal is, which is the line this file has held from
                # the start.
                stopped = True
                break
        if stopped:
            break
        if not round_applied and not doubted:
            # Nothing in ANY lane applied, and the shortlist walk above has
            # already been through every non-dormant rule in every lane -- so
            # there is nothing left to widen to.
            # The run is over, and WHICH silence it was goes on the record:
            # the option-set loop's callers read `steps[-1].state` in 33
            # places to tell a finished search from one that hit the limit.
            #
            # ⚠ `unattended` is NOT `quiescent`, and conflating them made the
            # loop state a falsehood. A rule can match completely and be
            # discarded because nothing it is about is in mind -- and
            # widening cannot rescue that, because widening matches MORE
            # rules and the filter drops those too. Reporting a finished
            # search there breaks this file's own guarantee that a dry
            # shortlist is not a finished search. Measured on `worked.ugm`:
            # `quiescent` with <boil> and <weather> both fully matched and
            # neither ever offered.
            if unattended:
                m._note(m.g.rel(m.UNATTENDED, m.g.atom(str(unattended))))
                steps.append(Step(arrivals, 0, tried, None, (), "unattended"))
            else:
                steps.append(Step(arrivals, 0, tried, None, (), "quiescent"))
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
        # outlive a run` is about.
        len(applied), applied, time.time() - t0, tried, _state(m), root_table,
        doubts, windows, widenings, steps,
        sum(v[0] for v in scanned.values()), scanned,
        sum(v[1] for v in scanned.values()),
    )


def _matched_nodes(m: Machine, a: Application) -> "List[NodeId]":
    """Every grounded antecedent line of an application.

    An `absent` member matched by NOT being there consumes nothing: there was
    no occasion to spend.
    """
    out = []
    for member in a.rule.antecedent:
        if member.sign == ABSENT:
            continue
        try:
            node = substitute(m.g, member.pattern, a.bindings)
        except Exception:
            continue
        if node is not None:
            out.append(node)
    return out


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
                m._attend(node, weight=target.weight, decay=target.decay,
                          floor=target.floor, ceiling=target.ceiling)
            continue
        if isinstance(target, Push):
            # A CALL. The nodes are the host rule's own variables, bound by
            # the move that spent this. Ground only, like `attend`, and for
            # the same reason.
            nodes = []
            for term in target.terms:
                node = _ground(m, table, term, bindings)
                if node is not None and not m.g.has_var(node):
                    nodes.append(node)
            m._push_frame(nodes)
            continue
        if isinstance(target, Pop):
            # ...and a RETURN. The loop finds the restored frame at the top of
            # the next tick and carries on against the one shared table, which
            # is what makes the caller's re-run a resume rather than a restart.
            node = _ground(m, table, target.term, bindings)
            m._pop_frame(node if node is not None and not m.g.has_var(node)
                         else None)
            continue
        if isinstance(target, (Merge, Unmerge)):
            # Identity. Ground only, like `attend` -- a claim about a
            # variable nothing bound has nothing to merge -- but a
            # `ValueError` `Graph.unmerge` raises (not the top of the
            # record, or it cascaded) is NOT caught here: that is an
            # author's mistake surfacing, the same standing this repo takes
            # on a run limit rather than absorbing the symptom.
            keep = _ground(m, table, target.keep, bindings)
            drop = _ground(m, table, target.drop, bindings)
            if (keep is not None and not m.g.has_var(keep)
                    and drop is not None and not m.g.has_var(drop)):
                (m.g.merge if isinstance(target, Merge) else m.g.unmerge)(
                    keep, drop)
            continue
        if isinstance(target, Destroy):
            node = _ground(m, table, target.term, bindings)
            if node is not None and not m.g.has_var(node):
                m.g.delete(node)
            continue
        if isinstance(target, (Label, Unlabel)):
            node = _ground(m, table, target.term, bindings)
            text = _ground(m, table, target.text, bindings)
            if (node is not None and not m.g.has_var(node)
                    and text is not None and not m.g.has_var(text)):
                (m.g.label if isinstance(target, Label) else m.g.unlabel)(
                    node, m.g.show(text))
            continue
        if isinstance(target, Forget):
            # `forget $hit` -- erase the answer and, structurally, the
            # request it names (`g.member(node, 1)` of `answered(<tool>,
            # request, value)`). Ground only, like the others; but a bound,
            # ground node that is not `answered(...)`-shaped is an author's
            # mistake and RAISES rather than silently doing nothing -- the
            # same standing as `Unmerge`.
            node = _ground(m, table, target.term, bindings)
            if node is not None and not m.g.has_var(node):
                if (m.g.relation_of(node) is not m.ANSWERED
                        or len(m.g.members(node)) < 2):
                    raise ValueError(
                        f"forget {m.g.show(node)}: not an answered(...) "
                        f"instance -- forget erases a request and its "
                        f"answer together, and there is no request to find "
                        f"on this node"
                    )
                m.gate.erase(m.g.member(node, 1))
                m.gate.erase(node)
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
