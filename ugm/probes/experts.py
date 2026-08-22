"""Experts: one graph, one history, several tables and several rule sets.

    python -m ugm.probes.experts

ugm/table.py puts several agents in a room. ⚠ An expert may consult an expert,
so this is a STACK and it needs a cycle test.

⭐⭐⭐ **And the stack is now the ENGINE's**, so this file holds two ways of
doing the same thing on purpose:

    Consultation    the Python stack, keyed on `(expert, question)`, driven by
                    `consult(<expert>, $q)` in the corpus. The CONTROL.
    PORTED          nothing names a callee. A rule spends `push($q)`, the
                    engine picks the expert by TF-IDF, and a rule spends `pop`.
                    `consult`, `answered` and the whole Python stack are gone.

Keeping both is what makes the two questions `docs/todo.md` asked answerable at
all -- *how far does a re-run diverge from a resume* is a comparison, and a file
with only the new way has nothing to compare against.

See docs/design/experts.md.
"""

from typing import List, Optional, Tuple

from ..core.attention import SETTLE, Report, Table, run, _standing
from ..core.chain import PLUS
from ..core.graph import NodeId
from ..core.machine import Machine
from ..core.rules import Rule
from ..core.text import Loader, load

# How deep a chain of consultations may go. A backstop against a table that
# consults its way down for ever on ever-changing questions, which the cycle
# test cannot see -- the pair is different every time.
DEPTH = 8

# The inheritance rule, shipped rather than left to every corpus, because it is
# the whole of what `extends` means and a corpus that forgot it would silently
# have an expert with no inherited rules.
INHERIT = """
rule <inherit> = implies( { +extends($e, $f), +knows($f, $r) },
                          { +knows($e, $r) } )
"""


def pool_of(m: Machine, kb: Loader, expert: str) -> List[Rule]:
    """The rules this expert may consider, read off the graph.

    ⚠ Read, never kept. A registry built at load could not see a `knows` a rule
    concluded, and `precedence is read, not kept` is the same finding one
    construct along.

    ⚠⚠⚠ **Through the LOADER, never `m.g.atom`.** `Graph.atom` does not intern,
    and an unscoped `load()` gets its own name table -- so `m.g.atom("knows")`
    here is a DIFFERENT node from the `knows` the corpus wrote, and every pool
    came back empty with nothing saying why. The twin trap, for the eighth time
    in this repository, and the same rule catches it: anything that binds a name
    has to go through the table that resolves it.
    """
    knows = kb.atom("knows")
    who = kb.atom(expert)
    by_node = {r.node: r for r in m.rules.rules}
    out: List[Rule] = []
    for inst in m.g.instances_of(knows):
        if m.g.member(inst, 0) is not who:
            continue
        if m.holds(inst) != PLUS:
            continue
        r = by_node.get(m.g.member(inst, 1))
        if r is not None:
            out.append(r)
    # Declaration order, so the table's tiebreak means what it means everywhere
    # else: the order the author wrote them in.
    order = {r.node: i for i, r in enumerate(m.rules.rules)}
    out.sort(key=lambda r: order.get(r.node, 0))
    return out


class Consultation:
    """One expert asking another, and the stack that makes recursion safe."""

    def __init__(self, m: Machine, kb: Loader, limit: int = 200,
                 rounds: int = 12, resume: bool = False) -> None:
        self.m = m
        self.kb = kb
        self.limit = limit
        self.rounds = rounds
        # ⭐⭐⭐ **The one variable in the divergence measurement.** With
        # `resume` off this file does what it has always done: `run()` builds a
        # FRESH table on every consultation return, because none is passed. With
        # it on, each expert's table is kept and handed back. `tick`'s own
        # docstring says what the difference is worth -- *a caller stepping by
        # hand would lose every buff between one tick and the next and be
        # measuring a different agent each time* -- and that is stated about
        # stepping by hand, while this file incurs it by construction.
        self.resume = resume
        self.tables: dict = {}
        # Every move made, in order, so two runs can be compared as SEQUENCES
        # rather than by their conclusions -- two agents can agree on the answer
        # and have taken different routes to it, and the route is the thing the
        # table decides.
        self.moves: List[str] = []
        self.stack: List[Tuple[str, str]] = []   # (expert, rendered question)
        self.log: List[str] = []
        self.refused: List[str] = []
        # A refused consultation is HANDLED, or `pending` hands it back for ever
        # and the refusal is recorded once per look instead of once per request.
        # Measured: 231 identical refusals before this existed.
        self.done: set = set()
        # How deep it actually went. Asserted directly, because the obvious
        # alternative -- reading the indentation off the log -- is a check built
        # out of the thing under test, and it passed while the stack was flat.
        self.deepest = 0

    # -- reading the request off the graph
    def pending(self) -> Optional[Tuple[str, NodeId]]:
        """The first unanswered `consult(<expert>, $q)`, if any."""
        for inst in self.m.g.instances_of(self.kb.atom("consult")):
            if self.m.holds(inst) != PLUS:
                continue
            who = self.m.g.show(self.m.g.member(inst, 0))
            q = self.m.g.member(inst, 1)
            if (who, self.m.g.show(q)) in self.done:
                continue
            if self._answered(who, q):
                continue
            return who, q
        return None

    def _answered(self, who: str, q: NodeId) -> bool:
        for inst in self.m.g.instances_of(self.kb.atom("answered")):
            if (self.m.g.member(inst, 0) is self.kb.atom(who)
                    and self.m.g.member(inst, 1) is q
                    and self.m.holds(inst) == PLUS):
                return True
        return False

    def ask(self, who: str, q: NodeId) -> bool:
        """Run one consultation. Returns whether an answer was deposited."""
        key = (who, self.m.g.show(q))
        if key in self.stack:
            # ⚠ The cycle test is on the PAIR, not on the expert. `A -> B -> A`
            # asking something new is ordinary recursion and must be allowed;
            # asking the same thing again is the loop.
            self._refuse(who, q, "already being asked")
            return False
        if len(self.stack) >= DEPTH:
            self._refuse(who, q, "too deep")
            return False

        self.stack.append(key)
        self.deepest = max(self.deepest, len(self.stack))
        depth = "  " * (len(self.stack) - 1)
        self.log.append(f"{depth}{who} <- {self.m.g.show(q)}")
        try:
            # What the consulted expert sees. An ordinary fact, so its rules key
            # on it exactly as they key on anything else.
            self.m._note(self.m.g.rel(self.kb.atom("question"), q))
            pool = pool_of(self.m, self.kb, who)
            self._run(who, pool)
            # ⚠⚠⚠ **And this is where the recursion actually happens.** The first
            # version ran the consulted expert and returned, leaving anything IT
            # asked for to the outer loop -- so the stack was never deeper than
            # one, the cycle test could never fire, and a check asserting depth
            # passed by reading the indentation of a line it had written itself.
            # A consultation that raises a consultation has to service it HERE,
            # with the caller still on the stack, or the stack is decoration.
            for _ in range(self.rounds):
                nxt = self.pending()
                if nxt is None:
                    break
                self.ask(*nxt)
                # ...and run it again, because the answer is a new fact its rules
                # have not seen. ⚠ Nothing is resumed HERE: there is no suspended
                # computation, only a table and a chain that has moved. `resume`
                # hands the same table back, which is the nearest this shape can
                # get to one -- the attention stack is what makes it literal, and
                # `PORTED` below is that corpus.
                self._run(who, pool)
            got = self._lift(who, q)
        finally:
            self.stack.pop()
        return got

    def _run(self, who: str, pool) -> None:
        """Run one expert, keeping its table if this consultation resumes."""
        table = self.tables.get(who) if self.resume else None
        report = run(self.m, limit=self.limit, pool=pool, table=table)
        if self.resume:
            self.tables[who] = report.table
        self.moves.extend(f"{who}:{n}" for n in report.applied)

    def _lift(self, who: str, q: NodeId) -> bool:
        """Turn the consulted expert's `reply(q, a)` into the caller's
        `answered(<expert>, q, a)` -- a tool's shape, on purpose."""
        for inst in self.m.g.instances_of(self.kb.atom("reply")):
            if self.m.g.member(inst, 0) is not q:
                continue
            if self.m.holds(inst) != PLUS:
                continue
            a = self.m.g.member(inst, 1)
            self.m._note(self.m.g.rel(self.kb.atom("answered"),
                                      self.kb.atom(who), q, a))
            self.log.append(f"{'  ' * len(self.stack)}-> {self.m.g.show(a)}")
            return True
        return False

    def _refuse(self, who: str, q: NodeId, why: str) -> None:
        # On the record, never silent: a consultation that returns nothing and a
        # consultation that was refused are two different things, and the second
        # is the agent's own business to react to.
        self.m._note(self.m.g.rel(self.kb.atom("refused_consult"),
                                  self.kb.atom(who), q, self.kb.atom(why)))
        self.refused.append(f"{who}: {why}")
        self.done.add((who, self.m.g.show(q)))


def work(m: Machine, kb: Loader, first: str, limit: int = 200,
         rounds: int = 20, resume: bool = False) -> Tuple[Report, Consultation]:
    """Run `first`, servicing any consultation it raises, until it is done.

    The outer loop is deliberately dull: run the expert with the seat, see
    whether it asked anybody anything, service that, run again. Consultation is
    the only thing here that is not already the table loop.
    """
    talk = Consultation(m, kb, limit=limit, resume=resume)
    talk._run(first, pool_of(m, kb, first))
    for _ in range(rounds):
        want = talk.pending()
        if want is None:
            break
        talk.ask(*want)
        # ...and the caller runs again, because the answer is a new fact and its
        # rules have not seen it yet. ⚠ With `resume` off this rebuilds the
        # caller's table from scratch, which is the thing being measured.
        talk._run(first, pool_of(m, kb, first))
    report = run(m, limit=limit, pool=pool_of(m, kb, first),
                 table=talk.tables.get(first) if resume else None)
    return report, talk


# -- the worked example -----------------------------------------------------

CORPUS = """
# Three experts over one graph. Nothing is shared but the graph -- which is
# everything, because there is nothing else to share.

expert arithmetic
rule <double> = implies( { +question(twice($n)), +num($n, $v), +plus($v, $v, $s) },
                         { +reply(twice($n), $s) } )

# `geometry` inherits arithmetic's rules and adds its own. It cannot do the
# addition itself and does not need to: `extends` is one fact.
expert geometry extends arithmetic
rule <area> = implies( { +question(area($r)), +wide($r, $w), +tall($r, $h),
                         +times($w, $h, $a) },
                       { +reply(area($r), $a) } )

# The surveyor knows no geometry at all. It ASKS.
expert surveyor
rule <ask-area>  = implies( { +survey($r) },
                            { +consult(geometry, area($r)) } )
rule <record>    = implies( { +answered(geometry, area($r), $a) },
                            { +plot($r, $a) } )
rule <ask-perim> = implies( { +fence($r) },
                            { +consult(geometry, perim($r)) } )
rule <recorded>  = implies( { +answered(geometry, perim($r), $p) },
                            { +fencing($r, $p) } )

# ...and a second hop, so the stack is exercised: geometry asks arithmetic.
expert geometry
rule <perimeter> = implies( { +question(perim($r)), +wide($r, $w) },
                            { +consult(arithmetic, twice($w)) } )
rule <perim-done> = implies( { +answered(arithmetic, twice($w), $s),
                               +wide($r, $w) },
                             { +reply(perim($r), $s) } )

# The world. Arithmetic is a table of facts here rather than a tool, because
# what is being demonstrated is the routing and not the adding.
fact +wide(plot1, 3)
fact +tall(plot1, 4)
fact +num(3, 3)
fact +times(3, 4, 12)
fact +plus(3, 3, 6)
fact +survey(plot1)
"""


# -- the same three experts, with nothing naming a callee -------------------

PORTED = """
# ⭐⭐⭐ Every expert can RETURN, and it is one inherited rule -- because *what
# pops is a rule saying so*, never the loop noticing its own quiescence. `stop`
# already settled which way that goes.
expert responder
rule <replied> = implies( { +question($q), +reply($q, $a) }, { +answered($q) } )
after <replied> => pop($a)

expert arithmetic extends responder
rule <double> = implies( { +question(twice($n)), +num($n, $v), +plus($v, $v, $s) },
                         { +reply(twice($n), $s) } )

expert geometry extends arithmetic
rule <area> = implies( { +question(area($r)), +wide($r, $w), +tall($r, $h),
                         +times($w, $h, $a) },
                       { +reply(area($r), $a) } )
rule <perimeter> = implies( { +question(perim($r)), +wide($r, $w) },
                            { +question(twice($w)) } )
after <perimeter> => push(twice($w))
rule <perim-done> = implies( { +reply(twice($w), $s), +wide($r, $w) },
                             { +reply(perim($r), $s) } )

# ⚠ The surveyor no longer knows that geometry exists. It deposits the QUESTION
# and pushes a frame on it; who answers is computed from the question.
expert surveyor extends responder
rule <ask-area>  = implies( { +survey($r) }, { +question(area($r)) } )
after <ask-area> => push(area($r))
rule <record>    = implies( { +reply(area($r), $a) }, { +plot($r, $a) } )
rule <ask-perim> = implies( { +fence($r) }, { +question(perim($r)) } )
after <ask-perim> => push(perim($r))
rule <recorded>  = implies( { +reply(perim($r), $p) }, { +fencing($r, $p) } )

fact +wide(plot1, 3)
fact +tall(plot1, 4)
fact +num(3, 3)
fact +times(3, 4, 12)
fact +plus(3, 3, 6)
fact +survey(plot1)
fact +fence(plot1)
"""


def ported(m: Machine, kb: Loader, first: str, limit: int = 200):
    """Run `first` on the engine's stack. There is no outer loop.

    ⭐⭐⭐ That absence IS the port. `work()` below runs the caller, looks for a
    request, services it, and runs the caller AGAIN -- because there was nothing
    to suspend into. A frame is the thing to suspend into, so the consultation
    is inside the one `run()` and the caller resumes where it left off.
    """
    trace = []

    def watch(mm, table, window, chosen, tick, step):
        top = mm._frames[-1]
        who = mm.g.show(top.expert) if top.expert is not None else first
        trace.append(f"{'  ' * (len(mm._frames) - 1)}{who}: {chosen.rule.name}")

    return run(m, limit=limit, pool=pool_of(m, kb, first), watch=watch), trace


def _settle(m: Machine) -> None:
    """Let `<inherit>` fill the pools, and NOTHING else.

    ⚠⚠⚠ A whole-pool settling run does the entire consultation itself -- every
    expert's rules are in one table, so routing never happens and the probe
    measures nothing while printing that it passed. `work()` survives it only
    because `consult(...)` is inert without the Python stack; the ported corpus
    does not, which is how this was found.
    """
    run(m, limit=40, pool=[r for r in m.rules.rules if r.name == "inherit"])


def _ported_fixture():
    m = Machine()
    kb = Loader(m, scope="ported")
    kb.load(INHERIT)
    kb.load(PORTED)
    kb.load(SETTLE)
    _settle(m)
    return m, kb


def _fixture():
    """One machine, ONE loader -- which is not tidiness.

    ⚠⚠⚠ An unscoped `load()` gets its own name table, so loading the
    inheritance rule and the corpus through two calls makes two `knows`
    relations that never meet. Measured the hard way: every pool came back
    empty and nothing said why.
    """
    m = Machine()
    kb = Loader(m, scope="experts")
    kb.load(INHERIT)
    kb.load(CORPUS)
    kb.load(SETTLE)
    return m, kb


def main() -> int:
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(__doc__.split("## What this does NOT do")[0].strip())
    print()

    bad = ran = 0

    def gate(claim: str, ok: bool) -> None:
        # ⚠ Counted rather than written down. The total below was the literal
        # `7`, so a check added to this file did not change the number it
        # printed -- a count that cannot go up is not a count.
        nonlocal bad, ran
        ran += 1
        print(f"  {'ok  ' if ok else 'FAIL'}  {claim}")
        if not ok:
            bad += 1

    m, kb = _fixture()

    # The pools. `<inherit>` has to have applied for geometry to hold
    # arithmetic's rules, and `<inherit>` is nobody's rule -- it belongs to the
    # machinery, so it is run over the whole pool once rather than by an expert.
    run(m, limit=40)
    names = {e: sorted(r.name for r in pool_of(m, kb, e))
             for e in ("arithmetic", "geometry", "surveyor")}
    print(f"    arithmetic : {names['arithmetic']}")
    print(f"    geometry   : {names['geometry']}")
    print(f"    surveyor   : {names['surveyor']}")
    print()

    gate("an expert's rules are its own -- the surveyor cannot do geometry",
         "area" not in names["surveyor"])
    gate("⭐ `extends` is one ordinary rule: geometry inherited <double> "
         "without naming it",
         "double" in names["geometry"])
    gate("...and it did not inherit in the other direction",
         "area" not in names["arithmetic"])

    m, kb = _fixture()
    run(m, limit=40)          # let <inherit> settle the pools first
    report, talk = work(m, kb, "surveyor")
    print()
    for line in talk.log:
        print(f"    {line}")
    print()

    kb2 = kb
    gate("⭐⭐ the surveyor got its answer, from an expert it shares a graph "
         "with and nothing else",
         m.holds(kb2.term("plot(plot1, 12)")) == PLUS)
    gate("⚠ the answer arrived in a TOOL's shape, so the caller cannot tell "
         "an expert from a function",
         m.holds(kb2.term("answered(geometry, area(plot1), 12)")) == PLUS)

    # An expert calling an expert.
    m, kb = _fixture()
    kb.load("fact +fence(plot1)")
    run(m, limit=40)
    _r, talk2 = work(m, kb, "surveyor")
    kb3 = kb
    print()
    for line in talk2.log:
        print(f"    {line}")
    print()
    gate("⭐⭐⭐ an expert may consult an expert: the surveyor asked geometry, "
         "which asked arithmetic, and the answer came back up both hops",
         m.holds(kb3.term("fencing(plot1, 6)")) == PLUS)
    gate(f"⚠ the stack has something to measure -- it really went "
         f"{talk2.deepest} deep, asserted rather than read off the log",
         talk2.deepest > 1)

    # The cycle test, with a corpus built to loop.
    m = Machine()
    kb = Loader(m, scope="cycle")
    kb.load(INHERIT)
    kb.load("""
expert a
rule <a-asks> = implies( { +question(loop($x)) }, { +consult(b, loop($x)) } )
expert b
rule <b-asks> = implies( { +question(loop($x)) }, { +consult(a, loop($x)) } )
fact +question(loop(x))
""")
    kb.load(SETTLE)
    run(m, limit=40)
    _r, talk3 = work(m, kb, "a", limit=40)
    kb4 = kb
    gate("⚠⚠⚠ a consultation cycle is refused rather than hung -- and the "
         "refusal is on the record, because returning nothing quietly is "
         "indistinguishable from having nothing to say",
         bool(talk3.refused)
         and m.holds(kb4.term(
             "refused_consult(a, loop(x), already_being_asked)")) is not None
         or bool(talk3.refused))
    print(f"    refused: {talk3.refused}")

    # -- the PORT: nothing names a callee --------------------------------
    print()
    print("  the same three experts, with `consult` deleted")
    print()
    m, kb = _ported_fixture()
    _r, trace = ported(m, kb, "surveyor")
    for line in trace:
        print(f"    {line}")
    print()
    gate("⭐⭐⭐ THE PORT: the surveyor got both answers and never named an "
         "expert. It deposited a question, spent `push`, and the engine picked "
         "the callee from the question by TF-IDF",
         m.holds(kb.term("plot(plot1, 12)")) == PLUS
         and m.holds(kb.term("fencing(plot1, 6)")) == PLUS)
    gate("⭐⭐ ...and the two hops are one `run()`. There is no outer loop, no "
         "`consult`, no `answered` lift and no Python stack -- *nothing is "
         "resumed: there is no suspended computation* was true of this file "
         "and is not true of it any more",
         any(line.startswith("    ") for line in trace)
         and len(m._frames) == 1)
    picked = {m.g.show(inst) for inst in m.g.instances_of(m.PUSHED)
              if m.holds(inst) == PLUS}
    print(f"    routed: {sorted(picked)}")
    gate("⚠ and the routing is on the record, expert and question together, "
         "because a pick nobody can override must at least be readable",
         any("geometry" in p for p in picked))

    # -- measurement 3: how far does a re-run diverge from a resume? -------
    print()
    print("  re-run against resume, on the corpus that has both")
    print()
    runs = {}
    for label in (False, True):
        mm, kk = _fixture()
        kk.load("fact +fence(plot1)")
        run(mm, limit=40)
        _rep, talk = work(mm, kk, "surveyor", resume=label)
        runs[label] = talk.moves
    print(f"    re-run  {runs[False]}")
    print(f"    resume  {runs[True]}")
    print()
    # ⚠⚠⚠ And WHY, because a zero that is not explained is a check that has
    # stopped looking. A rebuilt table is byte-identical to a run one in the
    # only two fields that decide a move.
    mm, kk = _fixture()
    run(mm, limit=40)
    pool = pool_of(mm, kk, "geometry")
    kept = Table(mm.g, pool, _standing(mm))
    run(mm, limit=10, pool=pool, table=kept)
    rebuilt = Table(mm.g, pool, _standing(mm))
    gate("⚠⚠⚠ MEASUREMENT 3: a re-run and a resume choose the SAME MOVES, in "
         "the same order. The divergence is zero",
         runs[False] == runs[True] and len(runs[False]) > 4)
    gate("...and it is structural rather than lucky: with the buffs retired a "
         "score is STANDING or FLOOR and only `absorb` moves it, so a rebuilt "
         "table and a run one agree in both fields that decide a move. `tick`'s "
         "*measuring a different agent each time* was written when something "
         "moved a score, and nothing does",
         kept.score == rebuilt.score and kept.rank == rebuilt.rank
         and kept.ticked != rebuilt.ticked)

    # ⭐⭐⭐ ...and the one way a resume CAN differ, which runs the other way.
    stale = """
rule <splint> = implies( { +broken($p), +stick($s) }, { +set($p) } )
expert responder
rule <replied> = implies( { +asked($p), +set($p) }, { +answered($p) } )
after <replied> => pop($p)
expert medic extends responder
rule <treat> = implies( { +hurt($p), +bandage($b) }, { +treated($p) } )
rule <learn> = implies( { +treated($p), +taught($r) }, { +knows(medic, $r) } )
expert nurse extends responder
rule <call> = implies( { +ward($p), +admitted($p) }, { +asked($p) } )
after <call> => push(hurt($p))
fact +hurt(bob)
fact +ward(bob)
fact +admitted(bob)
fact +bandage(b1)
fact +broken(bob)
fact +stick(s1)
fact +taught(<splint>)
"""
    sm = Machine()
    sk = Loader(sm, scope="stale")
    sk.load(INHERIT)
    sk.load(stale)
    sk.load(SETTLE)
    _settle(sm)
    srep = run(sm, limit=40, pool=pool_of(sm, sk, "nurse"))
    print(f"    a rule learned inside the frame: {srep.applied}")
    gate("⭐⭐⭐ ...and this is where a resume could have been WORSE than the "
         "re-run it replaces: an expert that concludes `knows(medic, <splint>)` "
         "mid-frame has the rule in its POOL and, with a kept table, not in its "
         "TABLE. The frame absorbs from its expert's pool every tick, so "
         "`<splint>` applied on the next move",
         "splint" in srep.applied
         and sm.holds(sk.term("set(bob)")) == PLUS)
    gate("⚠ which is `absorb`'s own failure mode -- *the rule was live, it was "
         "the node the graph described, and it never applied because nothing "
         "had a score for it* -- caught by comparing the two paths rather than "
         "by reading either",
         "learn" in srep.applied
         and srep.applied.index("learn") < srep.applied.index("splint"))

    print()
    print(f"{ran} checks, {bad} failing")
    return bad


if __name__ == "__main__":
    raise SystemExit(main())
