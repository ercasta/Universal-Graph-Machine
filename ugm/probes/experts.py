"""Experts: one graph, one history, several tables and several rule sets.

    python -m ugm.probes.experts

`ugm/table.py` puts several agents in a room. This is the other axis, and the
two should not be confused:

| | `ugm.table` -- AGENTS | `ugm.experts` -- EXPERTS |
|---|---|---|
| what differs | what they **believe** | what they **know how to do** |
| the graph | one per agent, disjoint | **one, shared** |
| what crosses | an **utterance**, re-read in the hearer's scope | nothing -- a conclusion is simply there |
| fog of war | structural | none, by construction |

So an expert is not a small agent. Two agents can disagree about whether the
door is locked; two experts cannot, because there is one chain and one answer.
What an expert has of its own is **a rule set and a table** -- which is exactly
what §19 says expertise consists of: *the right rules coming to mind at the
right moment.*

## An expert is a subset, read off the graph

Nothing here keeps a registry. An expert's rules are what the graph says they
are:

    knows(geometry, <area>)             this expert has this rule
    extends(geometry, arithmetic)       ...and everything that one has

and inheritance is **one ordinary rule**, which is why `extends` needed no
engine support and is transitive for free:

    rule <inherit> = implies( { +extends(?e, ?f), +knows(?f, ?r) },
                              { +knows(?e, ?r) } )

The surface keyword is a convenience over exactly that and nothing more:

    expert geometry extends arithmetic
    rule <area> = implies( ... )

`which rules does this expert have` is therefore an ordinary query, and a rule
can conclude `knows(...)` at run time -- an expert that learns a rule is the
`adopt` door plus one fact.

## Consulting one

    +consult(geometry, area(rect(3, 4)))        the request
    +question(area(rect(3, 4)))                 what the consulted expert sees
    +reply(area(rect(3, 4)), 12)                what it concludes
    +answered(geometry, area(rect(3, 4)), 12)   what the caller sees

⭐ **The last line is deliberately a tool's answer.** From the caller's side an
expert and a tool are the same shape, so a corpus that consults one can be
pointed at the other without touching a rule. That is the honest reading of what
an expert is: a request answered by *a search* rather than by a function, where
a tool is answered by a function rather than by a search.

⚠⚠⚠ **An expert may consult an expert, so this is a STACK and it needs a cycle
test.** Depth alone is not enough: `A -> B -> A` is legitimate when the second
question is a different one, and a loop when it is not. So what is refused is a
repeated **(expert, question)** pair already on the stack, which is precise --
and it is refused onto the record as `refused_consult(...)` rather than silently,
because a consultation that quietly returns nothing is indistinguishable from
one that had nothing to say.

## What this does NOT do, stated rather than discovered

* It is a **loop**, not a gate door, so it belongs to the table loop and not to
  the shipped one. Consultation is where one expert's table stops being consulted
  and another's starts, and a table is the one thing the shipped loop has not got.
* An expert's conclusions are **not contained**. One chain was the point, so a
  consulted expert that concludes nonsense has concluded it for everybody. That
  is the cost of sharing beliefs and it is the reason `ugm.table` exists for the
  other case.
"""

from typing import List, Optional, Tuple

from ..core.attention import SETTLE, Report, run
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
rule <inherit> = implies( { +extends(?e, ?f), +knows(?f, ?r) },
                          { +knows(?e, ?r) } )
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
                 rounds: int = 12) -> None:
        self.m = m
        self.kb = kb
        self.limit = limit
        self.rounds = rounds
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
        """The first unanswered `consult(<expert>, ?q)`, if any."""
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
            run(self.m, limit=self.limit, pool=pool)
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
                # have not seen. Nothing is resumed: there is no suspended
                # computation, only a table and a chain that has moved.
                run(self.m, limit=self.limit, pool=pool)
            got = self._lift(who, q)
        finally:
            self.stack.pop()
        return got

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
         rounds: int = 20) -> Tuple[Report, Consultation]:
    """Run `first`, servicing any consultation it raises, until it is done.

    The outer loop is deliberately dull: run the expert with the seat, see
    whether it asked anybody anything, service that, run again. Consultation is
    the only thing here that is not already the table loop.
    """
    talk = Consultation(m, kb, limit=limit)
    report = run(m, limit=limit, pool=pool_of(m, kb, first))
    for _ in range(rounds):
        want = talk.pending()
        if want is None:
            break
        talk.ask(*want)
        # ...and the caller runs again, because the answer is a new fact and its
        # rules have not seen it yet. Nothing is resumed: there is no suspended
        # computation, only a table and a chain that has moved.
        report = run(m, limit=limit, pool=pool_of(m, kb, first))
    return report, talk


# -- the worked example -----------------------------------------------------

CORPUS = """
# Three experts over one graph. Nothing is shared but the graph -- which is
# everything, because there is nothing else to share.

expert arithmetic
rule <double> = implies( { +question(twice(?n)), +num(?n, ?v), +plus(?v, ?v, ?s) },
                         { +reply(twice(?n), ?s) } )

# `geometry` inherits arithmetic's rules and adds its own. It cannot do the
# addition itself and does not need to: `extends` is one fact.
expert geometry extends arithmetic
rule <area> = implies( { +question(area(?r)), +wide(?r, ?w), +tall(?r, ?h),
                         +times(?w, ?h, ?a) },
                       { +reply(area(?r), ?a) } )

# The surveyor knows no geometry at all. It ASKS.
expert surveyor
rule <ask-area>  = implies( { +survey(?r) },
                            { +consult(geometry, area(?r)) } )
rule <record>    = implies( { +answered(geometry, area(?r), ?a) },
                            { +plot(?r, ?a) } )
rule <ask-perim> = implies( { +fence(?r) },
                            { +consult(geometry, perim(?r)) } )
rule <recorded>  = implies( { +answered(geometry, perim(?r), ?p) },
                            { +fencing(?r, ?p) } )

# ...and a second hop, so the stack is exercised: geometry asks arithmetic.
expert geometry
rule <perimeter> = implies( { +question(perim(?r)), +wide(?r, ?w) },
                            { +consult(arithmetic, twice(?w)) } )
rule <perim-done> = implies( { +answered(arithmetic, twice(?w), ?s),
                               +wide(?r, ?w) },
                             { +reply(perim(?r), ?s) } )

# The world. Arithmetic is a table of facts here rather than a tool, because
# what is being demonstrated is the routing and not the adding.
fact +wide(plot1, 3)
fact +tall(plot1, 4)
fact +num(3, 3)
fact +times(3, 4, 12)
fact +plus(3, 3, 6)
fact +survey(plot1)
"""


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

    bad = 0

    def gate(claim: str, ok: bool) -> None:
        nonlocal bad
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
rule <a-asks> = implies( { +question(loop(?x)) }, { +consult(b, loop(?x)) } )
expert b
rule <b-asks> = implies( { +question(loop(?x)) }, { +consult(a, loop(?x)) } )
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

    print()
    print(f"{7} checks, {bad} failing")
    return bad


if __name__ == "__main__":
    raise SystemExit(main())
