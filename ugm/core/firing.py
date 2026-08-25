"""The firing loop (docs/design/intensity-gates.md).

What this file used to be: a TABLE, ranked by a score, worked top to bottom,
one rule taken and spent per tick -- see the module's own history if you want
the shape that replaced (`git log`, or `book/docs/watching/28-the-table.md`
for the doc that was written about it while it still existed). Score,
`standing`, declaration-order-as-tiebreak, the attention LIFT that decided
which rules were even matched (`_pull`) and the PICK that chose one
application among a matched rule's several (`_attended_first`), and lanes --
all of that is gone, and nothing here replaces it with something similar.
What replaces it is smaller:

    every node has an intensity  "on" is "above zero" -- `Scratchpad`
    a tick matches every rule    not the top of a ranked table
    every match fires            nothing picks a winner any more
    firing discharges by default `keep` opts one member out, per line
    same-node writes combine     by MAX, across every application that
                                 fired this tick, so order cannot matter

Firing order not mattering is not a claim taken on faith: `run` computes
every application against the tick's OPENING state, folds every write with
Python's own `max`, and only then commits -- so there is no step at which
"which application ran first" is a question with an answer to depend on.
`python -m ugm.core.firing` is this file's own worked demonstration of
that, and of discharge/`keep`/the general intensity write, the same way
`book/docs/watching/28-the-table.md` used to point at this file for the table
loop's.

The FOCUS system went with the table, one step later: `Machine._attend`/
`_attended`/`_fade_attention`, the frame stack (`_push_frame`/`_pop_frame`,
`Frame` and its standing weights), `attend(...)`/`brush(...)`/`unattend`/
`push(...)`/`pop(...)` as postconditions, and `attentioned($x)` as a
predicate. It answered *what is the agent thinking about* with a decaying
queue beside the graph, and intensity answers it in the graph instead --
a node is in play when it is ON, which is the same question an antecedent
member already asks. Nothing here schedules by it, so there was nothing
left for it to be for.

Dormancy (`dormant`/`due`) stays: it is a rule-level kill switch,
attributable and readable, orthogonal to both lanes and focus, and
`ugm/rules/circuit_breaker.ugm` still uses it (its own header, rewritten,
explains what it no longer needs).
"""

import time
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

from .graph import NodeId
from .machine import Machine, Step
from .rules import (ASSERT, ERASE, KEEP, Application, Rule, match, substitute)
from .scratchpad import ON


def _dormant(m: Machine, r: Rule) -> bool:
    """Claimed `dormant` and not yet claimed `due`.

    Unchanged from the table era: still a pair of ordinary claims rather
    than a mark the engine owns, still readable, deniable and concludable by
    anything at all. What changed is only WHERE this is consulted -- once
    per rule per tick, to decide whether it is even offered to `match`,
    rather than once per rule per lane pass.
    """
    return (m._claims(m.DORMANT, r.node)
            and not m._claims(m.DUE, r.node))


class Report(NamedTuple):
    """What one run did, and how much work it cost.

    Slimmer than the table era's: `doubts`/`windows`/`widenings`/`scans`/
    `scanned`/`scanned_nodes` were all questions about a ranked shortlist
    that does not exist any more -- there is no window to widen, no doubt
    to deposit when two applications tie (both just fire), no scan to blame
    on an unindexed member the shortlist had to fall back to matching every
    rule finds every tick regardless. What is left answers the same
    top-level question the table era's did: how many ticks, what fired,
    how long it took, and what the run ended believing.
    """

    ticks: int
    applied: List[str]
    seconds: float
    tried: int  # rule/tick pairs matched, over the whole run
    state: set
    steps: List["Step"] = []


def run(m: Machine, limit: int = 400, watch=None) -> Report:
    """The loop, in full. Everything else in this file is bookkeeping.

    One tick: match every non-dormant rule against the state as it stands at
    the START of the tick (an opening snapshot no application's own effect
    can see -- which is what makes "firing order does not matter" true
    rather than merely intended); fold every firing application's writes
    into one `node -> intensity` map with `max`; commit once. A tick that
    commits nothing -- nothing matched, or everything that matched was
    already exactly what it asked for -- is quiescent, and the run is over.
    """
    applied: List[str] = []
    steps: List[Step] = []
    tried = 0
    t0 = time.time()
    # Recorded here, obeyed by the loop below -- see `_spend_one`'s STOP
    # branch and this loop's own check of it after every firing. Reset per
    # RUN rather than per machine: a caller stepping one tick at a time
    # calls this repeatedly, and a `stop` two calls ago must not silently
    # end a run that never asked for it.
    m._stopped = None
    tried = _tick_loop(m, limit, watch, applied, steps)

    return Report(len(applied), applied, time.time() - t0, tried, _state(m), steps)


def _tick_loop(m: Machine, limit: int, watch, applied: List[str],
               steps: List[Step]) -> int:
    """The tick-by-tick body of `run`, split out only so `run` itself can
    wrap it in the floor's try/finally without the indentation swallowing
    the whole loop. Returns the number of rule/tick pairs matched."""
    tried = 0
    # REFRACTION, and it lives on the MACHINE rather than on the run. A
    # caller stepping one line at a time -- a REPL -- calls `run` once per
    # line, so a run-scoped memory forgets every instantiation between
    # calls and the whole history fires again. (Measured. The opposite
    # lifetime to `_stopped` above, which must reset per run.)
    fired_keys = m.__dict__.setdefault("_fired_keys", set())
    clock = m.CLOCK
    for tick in range(limit):
        # Not a phase: the world may have spoken since the last tick, and a
        # rule reads the same channel the same way every time (§13/§16).
        arrivals = m.channels.since_last_tick() or 0

        # THE CLOCK -- the one change this engine makes unprompted, and it
        # has to be the engine's because nothing else can be. A rule fires
        # when an input CHANGED; a corpus oscillator would need something
        # to tick IT, which is the same problem one level down. Erase last
        # tick's occasion, mint a fresh one: minting is minting, so the new
        # node IS the change. A rule that never reads `clock` never sees
        # it, so time is opt-in and costs the rest of the machine nothing.
        for old in [q for q in m.pad.believed()
                    if m.g.relation_of(q) is clock]:
            m.gate.erase(old)
        m.gate.write(m.g.rel(clock, m._numeral(tick)))

        applications: List[Application] = []
        for r in m.rules.rules:
            if _dormant(m, r):
                continue
            tried += 1
            applications.extend(
                match(m.g, m.pad, r, computes=m.rules.computes,
                      predicates=m.rules.predicates,
                      node_computes=m.rules.node_computes))

        # An application already fired is not new business. The key is the
        # rule plus the nodes it MATCHED: because minting is minting, a
        # proposition rewritten is a different node, so "the input changed"
        # and "this key is new" are the same statement and edge-triggering
        # needs no diff of its own.
        fresh = [a for a in applications
                 if (a.rule.node, tuple(a.matched)) not in fired_keys]

        if not fresh:
            steps.append(Step(arrivals, len(applications), (), (), "quiescent"))
            break

        # -- fold: every firing application's writes, combined by MAX -----
        #
        # `writes` starts empty, not at each node's PRIOR value -- the max
        # is over what THIS TICK's applications are asking for, never
        # against what was already true, or a node nothing touched this
        # tick would be dragged into the fold by its own standing value and
        # "nothing wrote this node" and "something wrote it back to what it
        # already was" would look the same below. They are not the same:
        # only the second is a "write" a caller could point at.
        writes: Dict[NodeId, float] = {}
        generic_nodes: set = set()
        fired: List[Tuple[Application, List[Tuple[NodeId, str]]]] = []
        for app in fresh:
            app, pending, values, _discharge = m._pending(app)
            fired.append((app, pending))
            if app.rule.mentions:
                generic_nodes.update(n for n, _s in pending)
            for node, sign in pending:
                if sign == ERASE:
                    val = 0.0
                else:
                    got = values.get(node)
                    # `values[node]` is a NODE -- `_pending` substitutes the
                    # write term the same way it substitutes the pattern --
                    # and its NAME is the number, the numeral convention
                    # every computator already uses. No opinion (`+p(x)`,
                    # no `intensity` clause) is the ordinary default.
                    val = float(m.g.show(got)) if got is not None else ON
                prev = writes.get(node)
                writes[node] = val if prev is None else max(prev, val)

        wrote = m._commit(writes, generic_nodes)
        fired_keys.update((a.rule.node, tuple(a.matched)) for a in fresh)
        if not wrote and not fired:
            # Every application that matched asked for exactly what already
            # held -- a FIXPOINT, and the honest reading of "nothing left to
            # do" once picking a winner is no longer a thing that happens.
            # (§20's old `unattended`/`quiescent` split does not survive
            # this file: there is no shortlist to have widened past, so
            # there is only one silence left to name.)
            steps.append(Step(arrivals, len(applications), (), (), "quiescent"))
            break

        # -- spend: postconditions and the focus queue, per firing ---------
        #
        # In a stable (declaration, then match) order -- deterministic, so
        # two runs of one corpus still agree node for node, but NOT a claim
        # that the GRAPH's own end state depends on it: that guarantee was
        # made above, by the fold, before any of this runs.
        stopped = False
        for app, _pending in fired:
            _spend_posts(m, app, tick)
            applied.append(app.rule.name or "?")
            if watch is not None:
                watch(m, app, tick)
            if m._stopped is not None:
                # *Completion is the output of a rule*, and this is the loop
                # obeying one -- `stop` still ends the RUN, not just this
                # firing's own postconditions; the rest of `fired` already
                # ran (a firing's graph writes are already committed above,
                # by the time any postcondition runs), but no further tick
                # happens.
                stopped = True
                break
        steps.append(Step(arrivals, len(applications), tuple(a for a, _ in fired),
                          wrote, "stopped" if stopped else "applied"))
        if stopped:
            break
    else:
        # The loop ran out of ITERATIONS, not out of work -- `bounded(ticks)`
        # is the same signal the table era gave a run that hit its limit
        # while something was still willing to fire.
        m.exhausted += 1
        m._note_that(m.BOUNDED, m.TICKS)

    return tried


def _spend_posts(m: Machine, chosen: Application, tick: int) -> None:
    """Run one firing's postconditions.

    Unchanged in shape from the table era's `_spend_posts`: a query is an
    ordinary antecedent, matched with this application's own bindings
    already substituted in, so `after { +p($x) }` asks about the `$x` THIS
    firing bound. A bare `after` has no query and holds always.
    """
    name = chosen.rule.name or "?"
    for query, spends, frozen, _learned in m.rules.triggers.get(
            chosen.rule.node, ()):
        if not query:
            _spend_one(m, tick, name, spends, chosen.bindings)
            continue
        probe = Rule(
            chosen.rule.node,
            [mm._replace(pattern=substitute(m.g, mm.pattern, chosen.bindings))
             for mm in query],
            [], f"{name}-after",
        )
        for hit in match(m.g, m.pad, probe, computes=m.rules.computes,
                         predicates=m.rules.predicates,
                         node_computes=m.rules.node_computes):
            bound = dict(chosen.bindings)
            bound.update(hit.bindings)
            _spend_one(m, tick, name, spends, bound)


def _ground(m: Machine, term, bindings):
    """What a spend NAMES, with the firing's own bindings put in."""
    if m.g.is_var(term):
        node = bindings.get(term)
    else:
        node = term
    if node is not None and m.g.has_var(node) and bindings:
        node = substitute(m.g, node, bindings)
    return node


def _spend_one(m: Machine, tick: int, by: str, spends, bindings) -> None:
    """Spend one postcondition -- an identity op, a structural one, or
    `stop`. What is NOT here any more is the focus half (`attend`, `brush`,
    `unattend`, `push`, `pop`): a node being in play is its intensity now,
    which is state in the graph rather than a queue beside it, so there is
    nothing for a postcondition to put on that queue.
    """
    from .rules import (STOP, Destroy, Forget, Label, Merge, Unlabel, Unmerge)

    for target, _delta in spends:
        if isinstance(target, (Merge, Unmerge)):
            keep = _ground(m, target.keep, bindings)
            drop = _ground(m, target.drop, bindings)
            if (keep is not None and not m.g.has_var(keep)
                    and drop is not None and not m.g.has_var(drop)):
                (m.g.merge if isinstance(target, Merge) else m.g.unmerge)(
                    keep, drop)
            continue
        if isinstance(target, Destroy):
            node = _ground(m, target.term, bindings)
            if node is not None and not m.g.has_var(node):
                m.g.delete(node)
            continue
        if isinstance(target, (Label, Unlabel)):
            node = _ground(m, target.term, bindings)
            text = _ground(m, target.text, bindings)
            if (node is not None and not m.g.has_var(node)
                    and text is not None and not m.g.has_var(text)):
                (m.g.label if isinstance(target, Label) else m.g.unlabel)(
                    node, m.g.show(text))
            continue
        if isinstance(target, Forget):
            node = _ground(m, target.term, bindings)
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
        if target is STOP:
            # `stop` still ends a RUN -- but there is no table to record it
            # on any more, so this file just breaks out of its own loop the
            # next time `run`'s tick boundary comes around. See `run`: a
            # firing that spends `stop` sets `m._stopped`, and the tick loop
            # checks it once, after every application this tick has had its
            # turn -- so `stop` still means "the run is over", not
            # "everything else this tick is cancelled".
            m._stopped = by


def _state(m: Machine) -> set:
    """What the agent ends up holding, as printed propositions."""
    return {m.g.show(p) for p in m.pad.believed()}


# -- worked examples, run as this file's own checks --------------------------
#
# `python -m ugm.core.firing` -- the convention `book/docs/watching/
# 28-the-table.md` pointed at this file for, kept for the file that replaced
# what that chapter described. Every claim in docs/design/intensity-gates.md's
# "Firing" and "RHS" sections gets one small, direct, runnable demonstration
# here rather than an assertion buried in `ugm.selftest` -- so a reader who
# wants to know *is this actually true* can run this file alone and watch it
# happen, the same promise the table era's chapter made about itself.


def _demo(name: str, ok: bool) -> None:
    print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
    if not ok:
        raise SystemExit(f"demo failed: {name}")


def _main() -> None:
    from .text import load

    print("firing: every rule whose full antecedent is on fires, not the "
          "top of a ranked table")
    m = Machine()
    kb = load(m, """
        fact +p(a)
        fact +q(a)
        rule <one> = implies( { +p($x) }, { +got_p($x) } )
        rule <two> = implies( { +q($x) }, { +got_q($x) } )
    """)
    m.run(limit=5)
    _demo("two independent rules both fire in the same run, neither "
          "starving the other -- there is no table for one to win",
          m.holds(kb.term("got_p(a)")) and m.holds(kb.term("got_q(a)")))

    print("\nfiring discharges by default: a plain `+p($x)` spends what it "
          "matched")
    m2 = Machine()
    kb2 = load(m2, """
        fact +p(a)
        rule <once> = implies( { +p($x) }, { +saw($x) } )
    """)
    m2.run(limit=5)
    _demo("the antecedent's own occasion is off after firing -- the "
          "guarded-rule-doesn't-re-derive pattern is now the substrate's "
          "default rather than something a corpus writes by hand",
          m2.holds(kb2.term("saw(a)")) and not m2.holds(kb2.term("p(a)")))

    print("\n`keep` opts a member out: a non-consuming read")
    m3 = Machine()
    kb3 = load(m3, """
        fact +p(a)
        rule <read> = implies( { keep p($x), no read1($x) }, { +read1($x) } )
        rule <read2> = implies( { keep p($x), no read2($x) }, { +read2($x) } )
    """)
    m3.run(limit=5)
    _demo("two rules both read the same fact with `keep`, and neither "
          "spent it -- p(a) is still on, and both readers got their turn",
          m3.holds(kb3.term("p(a)"))
          and m3.holds(kb3.term("read1(a)"))
          and m3.holds(kb3.term("read2(a)")))

    print("\n...but a plain (non-`keep`) reader sharing the same node still "
          "discharges it, however many `keep` readers there also were")
    m4 = Machine()
    kb4 = load(m4, """
        fact +p(a)
        rule <spender> = implies( { +p($x) }, { +spent($x) } )
        rule <reader>  = implies( { keep p($x), no read($x) }, { +read($x) } )
    """)
    m4.run(limit=5)
    _demo("one non-consuming and one consuming reader of the same "
          "occasion, one tick: the consuming one still turns it off",
          m4.holds(kb4.term("spent(a)"))
          and m4.holds(kb4.term("read(a)"))
          and not m4.holds(kb4.term("p(a)")))

    print("\nsame-node, same-tick writes combine by max, regardless of "
          "declaration order")
    #  Both rules bind `$y` to the ONE EXISTING occasion `p(a)` matched --
    # `keep` so neither spends it, `$y = p(a)` so both name the SAME node
    # rather than each authoring their own fresh (twin) `p(a)` literal.
    # This is not incidental: this substrate does not intern ground text
    # (§3 -- "on(a,b) built twice is two nodes"), so two rules that each
    # write a ground `+p(a)` of their OWN would be writing two separate
    # OCCASIONS, correctly (this is what lets `p(a)` be derived twice and
    # remembered as two tokens) -- "the same node" in the design doc's
    # sense is the node a match BOUND, not a shape two authors happened to
    # spell alike, and binding through the match (`as`/`$y =`) is how a
    # corpus says which one it means.
    def _combine(low_first: bool):
        mm = Machine()
        lines = ["rule <low> = implies( { keep $y = p(a) }, { +$y intensity 2 } )",
                 "rule <high> = implies( { keep $y = p(a) }, { +$y intensity 9 } )"]
        if not low_first:
            lines.reverse()
        kk = load(mm, "fact +p(a)\n" + "\n".join(lines))
        mm.run(limit=3)
        return mm.pad.occasion_intensity(kk.term("p(a)"))
    _demo("the higher write wins whichever rule is declared first",
          _combine(True) == 9.0 and _combine(False) == 9.0)

    print("\nthe runaway guard: a rule's own consequent recharges the exact "
          "occasion its own antecedent just discharged")
    from .text import Loader
    m5 = Machine()
    ldr = Loader(m5)
    ldr.computator("plus", lambda a, b: int(a) + int(b))
    #  `$g = count(a)` binds the EXISTING `count(a)` occasion (see the
    # comment above); `intensity($g) as $n` reads THAT node's number, and
    # the consequent writes back to `$g` -- the identical node, not a fresh
    # `count(a)` twin -- which is what makes this a recharge of one
    # growing occasion rather than a new one minted each tick.
    kb5 = ldr.load("""
        fact +count(a)
        fact +always
        rule <guard> = implies(
            { keep always, keep $g = count(a), intensity($g) as $n,
              plus($n, 1) as $n2 },
            { +$g intensity $n2, +fired } )
    """)
    m5.run(limit=4)
    _demo("the guard's own count keeps climbing tick over tick rather than "
          "being spent to zero by its own antecedent read -- the RHS's "
          "recharge outbids the antecedent's implicit discharge in the "
          "same fold",
          m5.pad.occasion_intensity(ldr.term("count(a)")) >= 3.0)

    print("\nfiring order does not change the end state: shuffled "
          "declaration order, same believed set")
    def _order(reverse: bool):
        mm = Machine()
        src = """
            fact +p(a)
            fact +q(a)
            fact +r(a)
            rule <one>   = implies( { +p($x) }, { +got1($x) } )
            rule <two>   = implies( { +q($x) }, { +got2($x) } )
            rule <three> = implies( { +r($x) }, { +got3($x) } )
        """
        lines = src.strip("\n").split("\n")
        if reverse:
            rules = [l for l in lines if l.strip().startswith("rule")]
            facts = [l for l in lines if l.strip().startswith("fact")]
            lines = facts + list(reversed(rules))
        kk = load(mm, "\n".join(lines))
        mm.run(limit=5)
        return {mm.g.show(p) for p in mm.pad.believed()}
    _demo("declaration order reversed, believed set identical",
          _order(False) == _order(True))

    print(f"\n{'-' * 60}\nevery worked example above held.")


if __name__ == "__main__":
    _main()
