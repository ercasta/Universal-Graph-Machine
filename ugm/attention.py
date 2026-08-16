"""A table-driven loop, beside the one that exists. (the author's design)

    python -m ugm.attention

The loop this repo ships weighs an option set: recall proposes, everything
matches, defeat and quiescence filter, arbitration ranks, one move is taken.
Measured, 99.6% of those candidates genuinely applied -- the option set is not
waste, it is the price of being able to say *nothing else applied*, which is
what `blocked` and `<give-up>` are built on.

The author's proposal is a different loop, and its claim is that the price is
not worth paying most of the time:

> The system need not explain why it preferred a rule. That is not reasoning,
> it is System-1. You never proceed to match all possible rules: you work the
> current table from top to bottom and stop at the first rule that matches.
> Each applied rule then spends attention -- a list of query -> buff -- which
> moves the scores of other rules. The rules stay fixed; the postconditions are
> what a learning process calibrates.

Three things the engine knows here, and none of them is semantic:

    a score per rule    ordered, tie broken by declaration order
    apply the first     highest-scoring rule whose antecedent matches
    then spend          run that rule's postconditions to move the table

No goal, no completeness, no widening. Those are corpus rules whose
postconditions reset buffs -- *refocusing* is a rule, *done* is the output of a
rule that checks against the goal. Nothing in this file knows what either is.

## What is deliberately NOT here

**An instruction set.** This project deleted an ISA once already; the floor is
four primitives and the standing test is that a feature adds rows rather than
branches. A postcondition is not an opcode: it is a query -- an ordinary
antecedent, parsed by the ordinary surface -- and a buff naming a rule. Buffs
are supplied from Python for now so the surface stays open until the loop has
been watched running.

**A replacement.** This is an instrument. It runs beside the shipped loop on the
same corpora and reports where they differ, which is the only way to find out
what first-match costs in conclusions rather than in theory.

## The trace

Every buff is recorded as (tick, by whom, target, delta), so the table at step
k is the defaults plus the deltas up to k. That is what makes a frozen
postcondition's effect showable after the fact -- *authority was in fact
considered* -- without the loop having to justify an ordering it does not
reason about.
"""

import os
import time
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

from .graph import NodeId
from .machine import Machine
from .rules import Application, Member, Rule, Situation, match, substitute
from .text import load, load_file

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

# How many rules are matched before the loop admits its table was wrong. The
# author's proposal, and it is what makes the design's performance claim
# testable: score FIRST, then match only the top of the table. Everything below
# is never matched at all -- unless nothing up here applies, and then the
# shortlist widens.
#
# Widening is the guarantee that keeps this honest, and it is the shipped rule:
# *a dry shortlist is not a finished search*. Without it a miss in the top N
# would deposit `quiet` while work remained, the agent would give up on goals it
# could have reached, and the trail would show a completed search that never
# ran. With it, the worst case is exactly today's cost and the best case is N.
SHORTLIST = 5

# The default doubt-settling rule, and the author's correction to an earlier
# sketch of mine: the loop does not need to HOLD a tick waiting for doubt to be
# resolved, because a settling rule fires. Depositing the doubt IS the move;
# this rule gets the next turn, and what it does is spend attention -- so the
# settlement is a buff like every other, calibratable and learnable rather than
# a branch. A corpus replaces it with something better (ask the user, apply a
# domain criterion) by writing a rule that outscores it.
#
# `?a` in the buff is the winner as the doubt named it. That is only writable
# because rules are subjects here -- `close(<A>, <B>)` names them -- and because
# `_note` deposits it as a MENTION, so a rule concluding about `?a` is not
# dropped by quiescence as having nothing to deposit.
SETTLE = """
rule <settle-doubt> = implies( { +close(?a, ?b) }, { +settled(?a, ?b) } )
  frozen after => boost(?a, 1)
"""
SETTLING = ("settle-doubt",)


class Buff(NamedTuple):
    """What a postcondition does: move one rule's score.

    `target` is a rule's name as `<...>` writes it -- or a VARIABLE the query
    bound, which is what makes a doubt-settling rule writable at all: the doubt
    is about two rules nobody knew when the postcondition was authored, so
    `boost(?a, 1)` has to mean *the rule this query found*. That works because
    rules are already subjects here: `close(<A>, <B>)` names them, and a
    conclusion naming a rule is a mention -- the case that was invisible to the
    matcher until this session.
    """

    target: str  # `<name>`, or `?var` bound by the postcondition's query
    delta: int


class Post(NamedTuple):
    """A postcondition: a query, and what it does to the table if the query
    holds. `query` is the name of a rule authored in the corpus whose
    ANTECEDENT is the query -- so the surface parses it, and this file adds no
    notation. Such rules never enter the table.

    `frozen` marks what a calibration process may not touch. It changes nothing
    about how the postcondition runs, and it is recorded on the trace.
    """

    of: str  # the rule this hangs off
    query: Optional[str]
    buffs: Tuple[Buff, ...]
    frozen: bool = False


class Spend(NamedTuple):
    tick: int
    by: str
    target: str
    delta: int
    frozen: bool


class Table:
    """Scores over rules, ordered, with the trace that rebuilds them."""

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
        self._defaults = dict(self.score)
        self.trace: List[Spend] = []

    def order(self) -> List[Rule]:
        return sorted(
            self.rules, key=lambda r: (-self.score[r.node], self.rank[r.node])
        )

    @staticmethod
    def _bare(name: str) -> str:
        """`<flightless>` and `flightless` name the same rule. The surface
        writes the marker, `Rule.name` does not carry it, and a buff that
        silently hits nothing is the twin-node trap in its cheapest form -- the
        run stayed green and the penguin kept flying."""
        return name[1:-1] if name.startswith("<") and name.endswith(">") else name

    def spend(self, tick: int, by: str, buffs, frozen: bool, bindings) -> None:
        for target, delta in buffs:
            node = self._target(target, bindings)
            if node is None or node not in self.score:
                continue
            self.score[node] = self.score[node] + delta
            self.trace.append(
                Spend(tick, by, self.name_of.get(node, "?"), delta, frozen))

    def _target(self, target: NodeId, bindings) -> Optional[NodeId]:
        """A rule node, or a variable the query bound to one."""
        if self.g.is_var(target):
            return None if not bindings else bindings.get(target)
        return target

    def rebuilt(self, upto: int) -> Dict[NodeId, int]:
        """The table as it stood after `upto` ticks, from the defaults and the
        trace alone.

        This is what the author asked for in place of explaining a preference:
        not a justification of the ordering, which is chemistry and owes none,
        but a record from which any step's table can be reconstructed -- so that
        *authority was in fact considered* is showable after the fact. Checked
        against the live table on every run below, because a trace that has
        quietly stopped being complete is a log, not a record.
        """
        out = dict(self._defaults)
        for s in self.trace:
            if s.tick > upto:
                break
            t = self.by_name.get(self._bare(s.target))
            if t is not None:
                out[t.node] = out[t.node] + s.delta
        return out


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


def _standing(m: Machine) -> set:
    """The rules the bundle deposits `standing(<R>)` about -- the default table,
    which already exists in all but name."""
    out = set()
    for node in m.g.instances_of(m.STANDING):
        members = m.g.members(node)
        if len(members) == 1 and m._claims(node):
            out.add(members[0])
    return out


def _queries(m: Machine, posts: Sequence[Post]) -> set:
    return {p.query for p in posts if p.query}


def run(m: Machine, posts: Sequence[Post] = (), limit: int = 400,
        reflex: bool = False) -> Report:
    """The loop, in full. Everything else in this file is bookkeeping.

    `reflex` is the cheapest calibration imaginable and it is here to answer one
    question: can *rules matched per move* be moved at all? A rule that was
    tried and did not match is damped by one; the rule that applied is boosted
    by one. No model, no gold, no human -- just the fact that the table was
    wrong about who was worth trying, which the loop already knows for free at
    the moment it finds out. If this does not move the number, no learning will.
    """
    queries = _queries(m, posts)
    pool = [r for r in m.rules.rules if r.name not in queries]
    table = Table(m.g, pool, _standing(m))
    by_rule: Dict[str, List[Post]] = {}
    for p in posts:
        by_rule.setdefault(p.of, []).append(p)

    applied: List[str] = []
    tried = 0
    doubts = 0
    widenings = 0
    windows: List[int] = []
    t0 = time.time()
    for tick in range(limit):
        # Not a phase: the world may have spoken since the last move, and the
        # shipped loop asks the same question in the same place.
        m.channels.since_last_tick()
        state = m._situation()
        window: List[Application] = []
        top = None
        ordered = table.order()
        cut = 0
        while cut < len(ordered) and not window:
            # One shortlist at a time. Score decides WHO is matched, which is
            # the whole proposal: a rule below the cut costs nothing at all.
            chunk = ordered[cut:cut + SHORTLIST]
            if cut:
                widenings += 1
            cut += SHORTLIST
            missed: List[Rule] = []
            for r in chunk:
                if top is not None and table.score[r.node] < top - TOLERANCE:
                    break  # the prefix ends here, and the rest is not matched
                tried += 1
                found = match(
                    m.g, m.chain, r, m.focus.topic, m.focus.seat, state,
                    computes=m.rules.computes,
                    structural=m.rules.skeleton(),
                )
                # `_survives` is the shipped per-candidate filter: passed up,
                # quiescent, or already spent on these premises. Refraction
                # stays, because *this instantiation has run* is not the same
                # claim as *this rule's score is low*, and keying firing-once to
                # the rule would stop it ever applying to new data.
                hit = False
                for a in found:
                    if m._survives(a):
                        window.append(a)
                        hit = True
                        if top is None:
                            top = table.score[r.node]
                        break
                if not hit:
                    missed.append(r)
                if len(window) >= WINDOW:
                    break
            if reflex:
                for r in missed:
                    # The DELTA ACTUALLY APPLIED goes on the trace, not the one
                    # intended: the floor clamps it, and recording the intent
                    # made the trace unable to rebuild the table. Caught by the
                    # assertion below the first time it ran, which is what that
                    # assertion is for.
                    was = table.score[r.node]
                    table.score[r.node] = max(0, was - 1)
                    table.trace.append(
                        Spend(tick, "reflex", r.name, table.score[r.node] - was,
                              False))
        if not window:
            # Nothing in the table matched. The engine says so and nothing
            # more: `quiet(<seat>)` is a fact about the machinery, like the
            # doubt, and it is what every rule that reacts to the loop having
            # stopped is waiting for -- `<give-up>`, the watchdogs, `blocked`.
            # Without it the bundle never gets its turn, which is why the first
            # version of this loop never acted at all on `quest-p1`.
            if m._wake():
                continue
            # ...and the register: nothing more applies HERE, and here may be
            # inside a supposition. Moving the register is chemistry -- the
            # same move `causes` makes -- and the decision to make it is the
            # empty window, so no notion of a goal is involved.
            if m._leave():
                continue
            break
        windows.append(len(window))
        chosen = window[0]
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
                if m.chain.resolve(node, m.focus.topic, m.focus.seat) is None:
                    m._note(node)
                    fresh = True
            if fresh:
                # Depositing IS the move. A settling rule -- the default one, or
                # a corpus's own -- is in the table and gets the next turn.
                doubts += 1
                continue
            # ...and the backstop: the doubt already stands and nothing settled
            # it, so restating it changes nothing and the winner applies. A
            # corpus with no settling rule loses a tick, not the loop.
        wrote = m._apply(chosen)
        m._spend(chosen, wrote)
        applied.append(chosen.rule.name or "?")
        if reflex:
            table.score[chosen.rule.node] = table.score[chosen.rule.node] + 1
            table.trace.append(Spend(tick, "reflex", chosen.rule.name, 1, False))
        _spend_posts(m, table, chosen, tick, state)
    # The trace is held to the table on every run: same scores, rebuilt from
    # the defaults and the spends alone.
    assert table.rebuilt(limit) == table.score, "the trace cannot rebuild the table"
    return Report(
        len(applied), applied, time.time() - t0, tried, _state(m), table,
        doubts, windows, widenings
    )


def _spend_posts(m: Machine, table: Table, chosen: Application, tick: int,
                 state: Situation) -> None:
    """Run the applied rule's postconditions and move the table.

    The query is matched with the application's own bindings already
    substituted in, which is what makes it a POSTcondition rather than a second
    rule: `after { +penguin(?x) }` asks about the `?x` this rule just bound. A
    bare `after` has no query and holds always.
    """
    name = chosen.rule.name or "?"
    for query, buffs, frozen in chosen.rule.posts:
        if not query:
            table.spend(tick, name, buffs, frozen, chosen.bindings)
            continue
        probe = Rule(
            chosen.rule.node, chosen.rule.connective,
            [Member(mm.sign, substitute(m.g, mm.pattern, chosen.bindings),
                    mm.locus, mm.binds) for mm in query],
            [], f"{name}-after",
        )
        for hit in match(
            m.g, m.chain, probe, m.focus.topic, m.focus.seat, state,
            computes=m.rules.computes, structural=m.rules.skeleton(),
        ):
            bound = dict(chosen.bindings)
            bound.update(hit.bindings)
            table.spend(tick, name, buffs, frozen, bound)


def _holds(m: Machine, table: Table, query: str, state: Situation):
    """Does the postcondition's query hold here? It is an ordinary antecedent,
    matched by the ordinary matcher -- the query rule is loaded with the corpus
    and kept out of the table."""
    r = table.by_name.get(query)
    if r is None:
        for x in m.rules.rules:
            if x.name == query:
                r = x
                break
    if r is None:
        return []
    return match(
        m.g, m.chain, r, m.focus.topic, m.focus.seat, state,
        computes=m.rules.computes, structural=m.rules.skeleton(),
    )


def _state(m: Machine) -> set:
    """What the agent ends up holding, as (proposition, sign). The comparison
    has to be over conclusions rather than over moves: two loops that reach the
    same beliefs by different routes agree about the world, and that is the
    question."""
    return {(m.g.show(e.proposition), e.sign) for e in m._state()}


# -- the comparison ---------------------------------------------------------

CORPORA = ("delay.ugm", "worked.ugm", "quest-p1.ugm", "dungeon")


DEFAULT_POSTS = (Post("settle-doubt", None, (Buff("?a", 1),), frozen=True),)


def _load(name: str, settling: bool = False) -> Machine:
    m = Machine()
    load_file(m, os.path.join(os.path.dirname(__file__), "rules", name))
    if settling:
        load(m, SETTLE)
    return m


def _fight(run_it: bool):
    """The dungeon, which is the largest corpus here -- 21 rules of its own, a
    fight that takes tens of moves, and three tools. It cannot be loaded from
    the file alone: `<dice>`, `<arith>` and `<beats>` are answerers registered
    in Python, so the machine is built the way `ugm.dungeon` builds it and only
    the loop differs."""
    from . import dungeon

    m, _kb, _asked = dungeon.fight(seed=7, limit=400 if run_it else 0)
    return m


def compare(name: str) -> dict:
    """Both loops on one corpus, from the same text."""
    if name == "dungeon":
        t0 = time.time()
        a = _fight(True)
        shipped = {"ticks": a.selections, "seconds": time.time() - t0,
                   "state": _state(a), "applied": []}
        b = _fight(False)
        load(b, SETTLE)
        r = run(b, limit=400)
        return {"corpus": name, "shipped": shipped, "table": {
            "ticks": r.ticks, "seconds": r.seconds, "state": r.state,
            "tried": r.tried, "applied": r.applied,
            "doubts": r.doubts, "windows": r.windows,
            "widenings": r.widenings}}
    a = _load(name)
    t0 = time.time()
    steps = a.run(limit=400)
    shipped = {
        "ticks": len(steps),
        "seconds": time.time() - t0,
        "state": _state(a),
        "applied": [s.applied.rule.name for s in steps if s.applied is not None],
    }
    b = _load(name, settling=True)
    r = run(b)
    return {
        "corpus": name,
        "shipped": shipped,
        "table": {
            "ticks": r.ticks, "seconds": r.seconds, "state": r.state,
            "tried": r.tried, "applied": r.applied,
            "doubts": r.doubts, "windows": r.windows,
            "widenings": r.widenings,
        },
    }


PENGUIN = """
fact bird(tweety)
fact bird(pingu)
fact penguin(pingu)
fact asked(pingu)

rule <flies>      = implies( {{ +bird(?x), +considered(?x) }},    {{ +can_fly(?x) }} )
rule <flightless> = implies( {{ +penguin(?x), +considered(?x) }}, {{ +grounded(?x) }} )
rule <classify>   = implies( {{ +asked(?x) }},                    {{ +considered(?x) }} )
{post}
"""

CALIBRATED = "  after { +penguin(?x) } => boost(<flightless>, 20)"


def penguin() -> int:
    """The author's example, and it found the mechanism's real boundary.

    `<flies>` is declared first, so under declaration order it wins for every
    bird, penguin included. Nothing about the tiebreak can fix that -- the
    general rule IS the more foundational one, which is what declaration order
    says. The specificity has to come from a buff.

    **But ordering alone is not defeasibility, and running it is how that
    showed.** A loop that continues to quiescence applies BOTH rules whatever
    the order: a low score delays a rule, it never removes one, and removal is
    the thing this design refuses on purpose (preference orders, it does not
    exclude). So the penguin comes out flying and grounded, twice, and the buff
    changes nothing you can see.

    What makes the order into a default is **stopping**: ask, take the first
    rule that matches, act on it. That is the System-1 reading taken seriously,
    and it is why *completion is the output of a rule* is not a detail of the
    author's design -- it is what turns a score into a default. Below, one move
    per question.
    """
    print()
    print("  the penguin -- ask, and take the first rule that matches")
    wrong = 0
    for post in ("", CALIBRATED):
        m = Machine()
        load(m, PENGUIN.format(post=post))
        load(m, SETTLE)
        r = run(m, limit=6)
        first = next((x for x in r.applied if x in ("flies", "flightless")), "-")
        answer = {"flies": "can_fly(pingu)", "flightless": "grounded(pingu)"}
        label = "with the postcondition" if post else "declaration order alone"
        print(f"    {label:24} {r.doubts} doubt(s), applied {r.applied}")
        print(f"    {'':24} first answer -> {answer.get(first, '-')}")
        if post and first != "flightless":
            wrong += 1
    return wrong


def main() -> int:
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(__doc__.split("## What is deliberately NOT here")[0].strip())
    print()
    print(f"  {'corpus':16} {'ticks':>12} {'seconds':>14} {'conclusions':>22}")
    bad = 0
    for name in CORPORA:
        c = compare(name)
        s, t = c["shipped"], c["table"]
        missing = s["state"] - t["state"]
        extra = t["state"] - s["state"]
        w = t["windows"] or [0]
        print(f"  {name:16} {s['ticks']:>5} {t['ticks']:>6} "
              f"{s['seconds']:>7.2f} {t['seconds']:>6.2f} "
              f"{len(s['state']):>10} {len(t['state']):>6}"
              f"   -{len(missing)} +{len(extra)}"
              f"   doubt {t['doubts']}/{len(w)}, "
              f"{t['tried'] / max(1, len(w)):.1f} matched/move, "
              f"{t['widenings']} widenings")
        if missing or extra:
            # By RELATION, because the interesting question is not which
            # proposition is absent but which piece of the shipped tick was
            # responsible for it. Everything this loop drops -- doubt, forgone,
            # leaving a supposition, saying `quiet` -- is machinery the author's
            # design moves into rules, so the diff is the work list.
            for label, diff in (("only shipped", missing), ("only table", extra)):
                by_rel: Dict[str, int] = {}
                for p, sign in diff:
                    by_rel[p.split("(")[0]] = by_rel.get(p.split("(")[0], 0) + 1
                if by_rel:
                    worst = sorted(by_rel.items(), key=lambda kv: -kv[1])[:6]
                    print(f"      {label:12} " +
                          ", ".join(f"{k} x{v}" for k, v in worst))
    print()
    print("  shipped | table, per column. A difference is not a failure here:")
    print("  everything the table loop drops is a record the shipped tick keeps")
    print("  BECAUSE it materialises an option set -- `close` is doubt, `quiet`")
    print("  is the loop saying it stopped, `left` is a supposition being exited.")
    print("  Each is a rule to write, and this list is the work list.")
    return bad + penguin()


if __name__ == "__main__":
    raise SystemExit(main())
