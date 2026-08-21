"""The loop: a table over rules, take the first that matches, then spend.

    python -m ugm.core.attention

⭐⭐⭐ **This is the loop, and it is the only one.** `Machine.run` is three lines
that call it and `Machine.tick` is five; every probe, gate, corpus and check in
the tree arrives here. Four things it knows, and none of them is semantic:

    a score per rule    ordered, tie broken by declaration order
    apply the first     highest-scoring rule whose antecedent matches
    then spend          run that rule's postconditions
    ...and STOP         if one of them said so, the run is over

No goal, no completeness, no widening. Those are corpus rules whose
postconditions spend attention: *refocusing* is a rule (`unattend`), *done* is
the output of a rule that checks against the goal (`stop`), and *suspend this
line of work for another* is two more (`push`, `pop`). Nothing here knows what
any of them is for.

⚠ It arrived as a PROPOSAL beside a loop that weighed an option set -- recall
proposes, everything matches, defeat and quiescence filter, arbitration ranks,
one move is taken. That loop is deleted and the comparison that held the two
side by side with it. The argument for this one, and the measurements that
decided it, are in the design doc rather than in the present tense here.

⚠⚠ ...and the file is still called `attention` after the feature that
distinguished it from the incumbent. Most of attention proper -- the queue, the
stack, the claims -- is in `machine.py`; what is here is the loop, plus the two
places attention touches it (`_pull`, `_attended_first`).

See docs/design/attention.md.
"""

import time
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

from .graph import NodeId
from .machine import Machine, Step
from .rules import (STOP, UNATTEND, Application, Attend, Member, Pop, Push,
                    Rule,
                    Situation, _superseded, match, substitute)
from .text import load

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
# resolved, because a settling rule fires. ⚠ It used to carry frozen after
# <settle-doubt> => boost(?a, 1) -- the settlement was a buff, so it was
# calibratable.
# → docs/design/attention.md#the-default-doubt-settling-rule-and-the-author
SETTLE = """
rule <settle-doubt> = implies( { +close(?a, ?b) }, { +settled(?a, ?b) } )
"""
SETTLING = ("settle-doubt",)


class Post(NamedTuple):
    """A postcondition: a query, and what it SPENDS if the query holds.
    `query` is the name of a rule authored in the corpus whose ANTECEDENT is the
    query -- so the surface parses it, and this file adds no notation. Such
    rules never enter the table.

    ⚠ `spends` used to be `buffs`, and the rename is the retirement in one word:
    what a postcondition may now say is `attend`, `unattend` and `stop`. None of
    them moves a score, so there is no table to keep an account of and no trace
    to keep it in.

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
            # Declaration order, first declared winning. This is §18's tiebreak
            # already -- authored order -- and it is not decorative: two thirds
            # of this agent's arbitrations are settled by the order of the
            # bundle file. ⚠ It can only BE the tiebreak because buffs do the
            # specificity work: `bird -> flies` declared before
            # `penguin -> flightless` wins for ever unless something lifts the
            # specific rule.
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
        # ⚠ The score is now FIXED once built: `STANDING` or `FLOOR`, moved only
        # by `absorb`. There is nothing to age, expire or rebuild, because the
        # only thing that used to move it was a buff. What varies move to move is
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

        ⭐⭐⭐ **`adopt` means the rule set moves at run time**, and a table built
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
            # ⚠ Rebuilt rather than appended to, because a rule adopted at run
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
    # One `Step` per move, in the shape the option-set loop returned, so this
    # loop can BE `Machine.run` rather than sit beside it. `applied` above is
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


def _is_defeated(m: Machine, rule: Rule, state) -> bool:
    """Does anything that overrides this rule match here?

    ⭐ The option-set loop answered this by having matched everything already.
    A prefix scan has not, so it asks the question the other way round: read the
    rules that override this one -- precedence is read from the graph, and there
    are usually one or two -- and match only those.

    ⚠ `supersedes` is NOT here. It defeats per CASE rather than per rule: only
    the applications sharing a consumed entry with the winner are out, so it
    cannot be settled by asking whether a rule matched. It is applied where the
    applications are, below.
    """
    higher = [h for h, lower in m.rules.precedence(m.rules.OVERRIDES)
              if lower is rule]
    # ⚠⚠⚠ EVERY overrider that matched, not the first.
    # → docs/design/attention.md#every-overrider-that-matched-not-the-firs
    beaten = False
    for h in higher:
        found = match(
            m.g, m.chain, h, state,
            computes=m.rules.computes, structural=m.rules.skeleton(),
        )
        # ⚠⚠⚠ **Matched, NOT survived**, and the difference is the whole of it.
        # `_survives` asks whether the winner still has work to do -- and once it
        # has applied, its conclusion holds, so it stops surviving and the loser
        # is suddenly undefeated. Measured: A2 applied, then A1 applied straight
        # after and overwrote it, which is exactly the failure the option-set
        # loop records as *defeat is about whose antecedent holds, not about who
        # still has work*.
        if found:
            # On the record, because *which of my rules actually fight* is a
            # question about a run that no run recorded until it was deposited.
            m._note(m.g.rel(m.DEFEATED, rule.node, h.node))
            beaten = True
    return beaten


def _rivals(m: Machine, chosen: Application, state) -> List[Application]:
    """The other ways of getting what this move is getting.

    ⭐⭐⭐ Complete forgoing looked like it needed the option set, and it does
    not. *What else could have served this want* ranges over every rule only if
    you ask it that way round. ⚠ Only when the move serves a want at all, which
    is the common case being cheap rather than an optimisation: most moves
    consume no goal and pay nothing.

    See docs/design/attention.md#rivals.
    """
    if not m._wants(chosen):
        return []
    out: List[Application] = []
    for r in m.rules.rules:
        if r is chosen.rule:
            continue
        if not any(m.g.relation_of(mm.pattern) is m.GOAL for mm in r.antecedent):
            continue
        out.extend(match(
            m.g, m.chain, r, state,
            computes=m.rules.computes, structural=m.rules.skeleton(),
        ))
    return out


def _dormant(m: Machine, r: Rule) -> bool:
    """Claimed `dormant` and not yet claimed `due`.

    ⚠ Deliberately NOT a mark on the rule that the engine reads. A mark authored
    once is relative to nothing -- not to the situation, not to the goal, not to
    who is asking -- which is §12's *achievability is not a mark*, the earliest
    instance of the error this design generalises. As a pair of ordinary claims
    it is dated, attributable, deniable, and readable by rules, and `due` can be
    concluded by anything at all.
    """
    return (m._claims(m.g.rel(m.DORMANT, r.node))
            and not m._claims(m.g.rel(m.DUE, r.node)))


def _is_superseded(m: Machine, app: Application, state) -> bool:
    """Defeated **for this case** rather than for this step.

    ⭐ The property supersedes exists for is *substitute where an outcome is
    declared, otherwise assume* -- and it is not expressible any other way.

    See docs/design/attention.md#is-superseded.
    """
    higher = [h for h, lower in m.rules.precedence(m.rules.SUPERSEDES)
              if lower is app.rule]
    if not higher:
        return False
    others: List[Application] = []
    for h in higher:
        others.extend(match(
            m.g, m.chain, h, state,
            computes=m.rules.computes, structural=m.rules.skeleton(),
        ))
    return _superseded(m.rules, app, others)


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

    ⚠ A member whose pattern is a bare variable or whose relation is a variable
    is filed under nothing. `+?p` is a rule about anything, and lifting it
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


def _pull(m: Machine, table: "Table", state: Situation,
          attended: Sequence[NodeId]) -> Dict[NodeId, int]:
    """Attention's rule-level lift: two dict reads and no matching.

    ⭐⭐⭐ The join, and the reason attention is affordable where a query is not.
    ⚠ Not summed over attended nodes.

    See docs/design/attention.md#pull.
    """
    lift: Dict[NodeId, int] = {}
    # ⭐⭐⭐ POSITION is the strength. attended arrives newest-first, so what the
    # agent turned to last lifts hardest and what is about to fall off the
    # bottom barely lifts at all. ⚠ A rule reachable from two attended nodes
    # takes the STRONGER, not the sum.
    # → docs/design/attention.md#position-is-the-strength-attended-arr
    weights = m._attention_weights()
    for i, node in enumerate(attended):
        # ⭐⭐⭐ **Position times the learned multiplier.** Depth says how
        # recently the agent turned to a thing; the multiplier says how much a
        # lesson thinks it is worth. Neither alone is enough -- everything one
        # move wrote arrives at the same depth, so without a weight the queue
        # cannot separate them, which is exactly what sank attending the
        # right-hand side twice (20d, 20h).
        weight = max(1, PULL - i) * weights.get(node, 1)
        for rel in state.relations_of(node):
            for r in table.by_relation.get(rel, ()):
                if weight > lift.get(r, 0):
                    lift[r] = weight
    return lift


def _attended_first(found: List[Application], attended: Sequence[NodeId],
                    weights: Optional[dict] = None) -> List[Application]:
    """Order a rule's own applications by what the agent is thinking about.

    ⭐⭐⭐ This is the half no rule-keyed buff can express, and it costs nothing.
    ⚠ Stable, and that is what keeps the existing tie-break intact.

    See docs/design/attention.md#attended-first.
    """
    if len(found) < 2:
        return found
    at = set(attended)
    weights = weights or {}

    rank = {node: (len(attended) - i) * weights.get(node, 1)
            for i, node in enumerate(attended)}

    def weight(a: Application) -> int:
        # ⚠ Weighted by POSITION here too, so an application binding what the
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
    """The loop, in full. Everything else in this file is bookkeeping.

    ⚠ `reflex` used to be a parameter here -- damp a rule that was tried and
    missed, boost the one that applied, the cheapest calibration imaginable. It
    went with the buffs, and with it the only thing in this file that wrote a
    score from the loop's own experience. What survives is attention, which is
    written by a rule rather than by the loop.
    """
    queries = _queries(m, posts)
    # ⭐ pool is what makes an EXPERT possible: one shared graph, one shared
    # chain, and a table over a SUBSET of the rules. ⚠ Whether the pool was
    # HANDED to us decides whether it may grow.
    # → docs/design/attention.md#pool-is-what-makes-an-expert-possible-one-s
    fixed = pool is not None
    if pool is None:
        pool = m.rules.rules
    pool = [r for r in pool if r.name not in queries]
    # ⭐⭐⭐ A caller may bring its own table, and docs/interpretation-feedback.md
    # §4 is right that the day it matters is the day something else changes. ⚠
    # The ticks continue from table.now rather than restarting at 0.
    # → docs/design/attention.md#a-caller-may-bring-its-own-table-and-doc
    if table is None:
        table = Table(m.g, pool, _standing(m))
    # ⭐⭐⭐ **The frame this run serves, and the floor it may not pop past.** A
    # nested run -- a consultation, a supposition, a table of agents -- starts on
    # whatever frame its caller was in, and popping the caller's frame out from
    # under it would be this stack's version of the bug `probes/experts.py`
    # records: a structure that looks like a stack and is not one.
    root = len(m._frames) - 1
    served = m._frames[root]
    # ⚠⚠⚠ Set unconditionally, and this was a `if served.table is None`. A frame
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
        # shipped loop asks the same question in the same place. ⭐⭐⭐ The anchor
        # a corpus reads the raw chain from. ⚠ Anchored at the SEAT rather than
        # at every moment, which is the containment story as well as the cheap
        # one: what the agent may read the chain about is where...
        # →
        # docs/design/attention.md#not-a-phase-the-world-may-have-spoken-since-the
        m.g.rel(m.chain.ASKING, m.chain.now.node)

        # ⭐⭐⭐ **Whose line of work is this?** A `push` spent last tick left a
        # new frame on the stack, and the loop picks up ITS table here. That is
        # the whole of what turns a consultation into a resume: `experts.py`
        # re-runs the caller with a FRESH table on every return, and `tick`'s own
        # docstring says what that costs -- *a caller stepping by hand would lose
        # every buff between one tick and the next and be measuring a different
        # agent each time*.
        #
        # ⚠ A frame with no expert keeps the rules of the frame below, table and
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
            # ⚠⚠⚠ **From the EXPERT's pool, re-read, and this was `do not absorb
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

        # ⭐⭐⭐ Satisfaction, ported from the tick this loop replaces.
        # → docs/design/attention.md#satisfaction-ported-from-the-tick-this-lo
        reason = m._enough()
        if reason is not None:
            m._halt(reason)
            steps.append(Step(arrivals, 0, tried, None, (), "stopped"))
            break

        state = m._situation()
        table.now = tick
        table.ticked += 1

        window: List[Application] = []
        top = None
        # ⭐⭐⭐ Dormancy, and it is the right form of *disable a rule*. A rule
        # claimed dormant is not considered until something claims it due --
        # which is all a callback is. ⚠ Read every tick and at the register's
        # own position, never once when the pool is built: due can be concluded
        # mid-run, and a callback attached inside a...
        # → docs/design/attention.md#dormancy-and-it-is-the-right-form-of-dis
        attended = m._attended()
        # ⚠⚠⚠ The queue has two uses and only one of them can starve. Ordering
        # a rule's own BINDINGS costs nothing -- the applications are already
        # in hand.
        # → docs/design/attention.md#the-queue-has-two-uses-and-only-one-of-the
        lift = None
        asked = m._attention_asked()
        if asked:
            lift = _pull(m, table, state, asked) or None
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
                found = match(
                    m.g, m.chain, r, state,
                    computes=m.rules.computes,
                    structural=m.rules.skeleton(),
                )
                # ...and WHICH of them, which the loop has never chosen. It
                # takes the first survivor and breaks, so the binding was
                # decided by the walk. Free: `found` is already here.
                if attended:
                    found = _attended_first(found, attended,
                                            m._attention_weights())
                # _survives is the shipped per-candidate filter: passed up,
                # quiescent, or already spent on these premises. ⚠ The gate
                # agreeing was not wrong, it was WEAK: it compares final
                # conclusions, and a loop that runs to quiescence applies the
                # loser eventually anyway --...
                # →
                # docs/design/attention.md#survives-is-the-shipped-per-candidate-filter
                if _is_defeated(m, r, state):
                    continue
                for a in found:
                    if m._survives(a) and not _is_superseded(m, a, state):
                        window.append(a)
                        if top is None:
                            top = table.score[r.node]
                        break
                if len(window) >= WINDOW:
                    break
        if not window:
            # Nothing in the table matched. ⚠ These are NOT ported logic.
            # →
            # docs/design/attention.md#nothing-in-the-table-matched-the-engine-says-so
            if m._widen():
                steps.append(Step(arrivals, 0, tried, None, (), "widened"))
                continue
            if m._recover():
                steps.append(Step(arrivals, 0, tried, None, (), "widened"))
                continue
            if m._wake():
                steps.append(Step(arrivals, 0, tried, None, (), "quiet"))
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
        chosen = window[0] if chooser is None else chooser(m, table, window, state)
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
                if m.chain.resolve(node) is None:
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
            # corpus with no settling rule loses a tick, not the loop. ⚠
            # Something applied, so the shortlist is trusted again.
            # →
            # docs/design/attention.md#and-the-backstop-the-doubt-already-stands-an
        m._forgo(window + _rivals(m, chosen, state), chosen)
        m._widened = False
        wrote = m._apply(chosen)
        m._attend_written(wrote)
        m._spend(chosen, wrote)
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
        _spend_posts(m, table, chosen, tick, state)
        if table.stopped is not None:
            steps.append(Step(arrivals, 0, tried, None, (), "stopped"))
            # *Completion is the output of a rule*, and this is the loop obeying
            # one. It knows a rule spent `stop`; it does not know what a goal is,
            # which is the line this file has held from the start.
            break
    # ⚠ The loop ran out of ITERATIONS, not out of work.
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
        # ⚠ The ROOT table, not whichever frame the run ended in. A caller that
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

    ⚠⚠⚠ `Table._target` answers for a bare variable and hands a COMPOUND back
    unchanged, which reads as an answer and is not one: `push(area(?r))` came
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

    ⭐⭐⭐ **The split is the design, not plumbing.** A deposit writes a claim the
    corpus can read, deny and reason about, and a table that could write claims
    would be an interpreter with a memory. A stop writes nothing and only says
    the run is over, so it is the one thing recorded on the table.

    ⚠ The licence is the rule that spent it, so *why am I thinking about this*
    answers with a rule and a moment.
    """
    licence = m.g.rel(m.APPLIED, rule_node)
    for target, _delta in spends:
        if isinstance(target, Attend):
            node = _ground(m, table, target.term, bindings)
            # ⚠ Ground only, and silently so. A postcondition naming a variable
            # the move did not bind has nothing to attend TO, and depositing
            # `attention(?x)` would be a claim about no one -- which `_attended`
            # would then refuse to read, one layer further from the mistake.
            if node is not None and not m.g.has_var(node):
                # ⭐ The learned WEIGHT rides along: `attend(?x, 3)` says this
                # node matters more than whatever else is in the queue at the
                # same depth -- a calibration that names a node instead of a
                # rule.
                m._attend(node, licence, target.weight)
            continue
        if isinstance(target, Push):
            # ⭐⭐⭐ A CALL. The nodes are the host rule's own variables, bound by
            # the move that spent this -- and the expert is computed from them,
            # never named. ⚠ Ground only, like `attend`, and for the same reason.
            nodes = []
            for term in target.terms:
                node = _ground(m, table, term, bindings)
                if node is not None and not m.g.has_var(node):
                    nodes.append(node)
            m._push_frame(nodes, licence)
            continue
        if isinstance(target, Pop):
            # ...and a RETURN. The loop finds the restored frame at the top of
            # the next tick and picks its table back up, which is what makes the
            # caller's re-run a resume.
            node = _ground(m, table, target.term, bindings)
            m._pop_frame(node if node is not None and not m.g.has_var(node)
                         else None, licence)
            continue
        if target is UNATTEND:
            m._unattend(licence)
            continue
        if target is STOP:
            # Recorded here, obeyed by the loop. Keeping the decision out of the
            # spend is what lets *why did you stop?* answer with a rule's name
            # rather than a flag.
            table.stopped = by


def _spend_posts(m: Machine, table: Table, chosen: Application, tick: int,
                 state: Situation) -> None:
    """Run the applied rule's postconditions and move the table.

    The query is matched with the application's own bindings already
    substituted in, which is what makes it a POSTcondition rather than a second
    rule: `after { +penguin(?x) }` asks about the `?x` this rule just bound. A
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
            chosen.rule.node, chosen.rule.connective,
            [Member(mm.sign, substitute(m.g, mm.pattern, chosen.bindings),
                    mm.binds) for mm in query],
            [], f"{name}-after",
        )
        for hit in match(
            m.g, m.chain, probe, state,
            computes=m.rules.computes, structural=m.rules.skeleton(),
        ):
            bound = dict(chosen.bindings)
            bound.update(hit.bindings)
            _spend_one(m, table, tick, name, spends, frozen, bound,
                       chosen.rule.node)


def _state(m: Machine) -> set:
    """What the agent ends up holding, as (proposition, sign). The comparison
    has to be over conclusions rather than over moves: two loops that reach the
    same beliefs by different routes agree about the world, and that is the
    question."""
    return {(m.g.show(e.proposition), e.sign) for e in m._state()}


# -- the comparison ---------------------------------------------------------

PENGUIN = """
fact bird(tweety)
fact bird(pingu)
fact penguin(pingu)
fact asked(pingu)
fact asked(tweety)

rule <flies>      = implies( {{ +bird(?x), +considered(?x) }},    {{ +can_fly(?x) }} )
rule <flightless> = implies( {{ +penguin(?x), +considered(?x) }}, {{ +grounded(?x) }} )
rule <classify>   = implies( {{ +asked(?x) }},                    {{ +considered(?x) }} )
{post}
"""


def penguin() -> int:
    """The author's example, and it found the mechanism's real boundary.

    <flies> is declared first, so under declaration order it wins for every
    bird, penguin included. The general rule IS the more foundational one,
    which is what declaration order says. ⚠ THE BUFF NEVER FIXED THE PENGUIN,
    AND RETIRING IT COSTS NOTHING HERE.

    See docs/design/attention.md#penguin.
    """
    print()
    print("  the penguin -- ordering is not defeasibility")
    wrong = 0
    DENIED = PENGUIN.replace(
        "fact penguin(pingu)",
        "fact penguin(pingu)" + chr(10) + "fact -penguin(tweety)").replace(
        "+bird(?x), +considered(?x) }}",
        "+bird(?x), +considered(?x), -penguin(?x) }}")
    cases = (
        ("declaration order alone", PENGUIN.format(post="")),
        ("standing(<flightless>)",
         PENGUIN.format(post="fact standing(<flightless>)")),
        ("overrides(<flightless>, <flies>)",
         PENGUIN.format(post="fact overrides(<flightless>, <flies>)")),
        ("the KB states -penguin(tweety)", DENIED.format(post="")),
    )
    for label, src in cases:
        m = Machine()
        kb = load(m, src)
        load(m, SETTLE)
        run(m, limit=12)
        held = lambda t: m.holds(kb.term(t)) == "+"
        pingu_flies, tweety_flies = held("can_fly(pingu)"), held("can_fly(tweety)")
        print(f"    {label:32} pingu flies: {str(pingu_flies):5}  "
              f"grounded: {str(held('grounded(pingu)')):5}  "
              f"tweety flies: {tweety_flies}")
        if label.startswith(("overrides", "the KB")):
            # The two that claim to answer it: the penguin must not fly, and an
            # ordinary bird must still be able to.
            if pingu_flies:
                print(f"    FAIL  {label} left the penguin flying")
                wrong += 1
            if label.startswith("the KB") and not tweety_flies:
                print(f"    FAIL  {label} grounded tweety as well, which is not "
                      f"solving the penguin but breaking flight")
                wrong += 1
        elif not pingu_flies:
            print(f"    FAIL  {label} is an ORDERING and must not remove a "
                  f"conclusion -- if it does, ordering has become defeat")
            wrong += 1
    return wrong


# -- stopping, which is what makes a score mean anything --------------------

_IDLE = "\n".join(
    "rule <f%d> = implies( { +wood(?x) }, { +step%d(?x) } )" % (i, i)
    for i in range(1, 13))
_DEEP = "\n".join(
    "rule <g%d> = implies( { +step%d(?x) }, { +after%d(?x) } )" % (i, i, i)
    for i in range(1, 13))

# ⚠ `want`, not `goal`. `goal` is the apparatus's own relation and the backward
# reader deposits its own, so a completion check written over `goal(?w)` fires
# on the machinery's subgoals -- measured, and it reported the check firing
# BEFORE the thing was built. A corpus's vocabulary is not the apparatus's.
STOPPING = """
fact +want(assembled(cart))
fact +wood(cart)
rule <wheel> = implies( { +wood(?x) },       { +have(wheel) } )
rule <axle>  = implies( { +have(wheel) },    { +have(axle) } )
rule <bed>   = implies( { +have(axle) },     { +have(bed) } )
rule <build> = implies( { +have(bed) },      { +assembled(cart) } )
rule <done>  = implies( { +want(?w), +?w },  { +finished(?w) } )
""" + _IDLE + "\n" + _DEEP + "\n"

# Two things wanted, one reachable: the stop fires on the one that was built
# while the other is still wanted and still unmet.
OPEN_WANT = """
fact +want(assembled(cart))
fact +want(painted(cart))
fact +wood(cart)
rule <wheel> = implies( { +wood(?x) },       { +have(wheel) } )
rule <build> = implies( { +have(wheel) },    { +assembled(cart) } )
rule <done>  = implies( { +want(?w), +?w },  { +finished(?w) } )
after <done> => stop
"""


def _stopping_run(src, limit=400):
    m = Machine()
    load(m, src)
    load(m, SETTLE)
    return m, run(m, limit=limit)


def stopping() -> int:
    """`stop`, and the two things measuring it settled.

    This file's own design says *done is the output of a rule that checks
    against the goal* -- and the loop had no way to obey one: the check
    concluded and the agent carried straight on to quiescence. ⚠ TWO OF THE
    FIVE ROWS ARE GONE WITH THE BUFFS.

    See docs/design/attention.md#stopping.
    """
    print()
    print("  stopping -- a cart to build, and a check that says when it is done")
    bad = 0
    seen = {}
    cases = (
        ("", "no postcondition"),
        ("after <done> => stop", "stop, <done> at the floor"),
        ("after <done> => stop\nfact standing(<done>)",
         "stop, and <done> standing"),
    )
    for post, label in cases:
        _m, r = _stopping_run(STOPPING + "\n" + post)
        done = any(p == "finished(assembled(cart))" and sg == "+"
                   for p, sg in r.state)
        seen[label] = r.ticks
        print(f"    {label:32} {r.ticks:>4} moves   finished: {done}   "
              f"stopped by {r.table.stopped}")
        if not done:
            bad += 1
    # The claim, as a number: obeying the rule is what shortens the run.
    if seen["stop, <done> at the floor"] >= seen["no postcondition"]:
        print("    FAIL  `stop` did not shorten the run")
        bad += 1
    # ...and the null result, kept as a check so it cannot quietly come back.
    # ⚠ A BOUND, not an equality -- see the docstring. It has to stay far
    # tighter than what `stop` buys, or it would stop being able to fail.
    drift = abs(seen["stop, and <done> standing"]
                - seen["stop, <done> at the floor"])
    worth = seen["no postcondition"] - seen["stop, <done> at the floor"]
    if drift > 1 or drift * 10 >= worth:
        print(f"    FAIL  raising the check's priority changed the run by "
              f"{drift} moves against {worth} for `stop` -- the null result "
              f"moved")
        bad += 1

    # ⚠⚠⚠ THE COST, measured rather than asserted. The shipped loop refuses to
    # stop QUIETLY on something it was asked for: an open goal outranks an
    # `enough`. This loop cannot, because that veto is an aggregate -- *nothing
    # else is wanted and unmet* -- and a rule cannot speak about the set of its
    # matches. So the guarantee becomes a corpus's, exactly as it did for norms,
    # and this is the instrument that watches it rather than a claim that it is
    # fine.
    _m, r = _stopping_run(OPEN_WANT, limit=200)
    held = {p for p, sg in r.state if sg == "+"}
    quiet_on_open = ("want(painted(cart))" in held
                     and "painted(cart)" not in held
                     and r.table.stopped is not None)
    print(f"    {'stopped with a want still open':32} {r.ticks:>4} moves   "
          f"unmet want left behind: {quiet_on_open}")
    if not quiet_on_open:
        print("    FAIL  the open-want probe has nothing to measure")
        bad += 1
    return bad


def main() -> int:
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(__doc__.split("## What is deliberately NOT here")[0].strip())
    print()
    return penguin() + stopping()


if __name__ == "__main__":
    raise SystemExit(main())
