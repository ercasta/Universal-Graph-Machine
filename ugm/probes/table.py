"""Several agents, each with its own beliefs, talking. The layer BELOW the machine.

    python -m ugm.probes.table

An agent's beliefs are its own chain. Nothing is shared: two machines hold two
graphs, and a node in one names nothing in the other.  Keep it that way: the
moment this file decides which utterances are worth believing, §13's hard-wired
intake is back and the corpus cannot argue with it.

See docs/design/table.md.
"""

import multiprocessing as mp
import os
import sys
from typing import Callable, Dict, List, NamedTuple, Optional, Sequence, Tuple

from ..core.machine import Machine
from ..core.text import Loader

VOICE = "voice"  # the actuator every agent speaks through


class Utterance(NamedTuple):
    """What crosses. Strings only -- so the same value goes down a
    `multiprocessing.Queue` unchanged, and no graph object can leak through."""

    speaker: str
    hearer: str
    text: str


class Spec(NamedTuple):
    """An agent, as data that survives a pickle.  `tools` names module-level
    functions in `TOOLS`, never a closure: under spawn the child re-imports this
    module and a closure would not arrive."""

    name: str
    corpus: str
    tools: Tuple[Tuple[str, str, str], ...] = ()  # (tool name, request, TOOLS key)
    limit: int = 2000
    # ...and computators, which are the other kind of tool: values in, a value
    # out, no access to anything. A die is an answerer because it is the world
    # speaking; comparing two numbers the agent already has is not.
    computes: Tuple[Tuple[str, str], ...] = ()  # (name, TOOLS key)
    # Which loop this agent thinks with: the shipped one, which weighs an
    # option set, or the table (`ugm.attention`), which works a score down to
    # the first rule that matches and spends attention afterwards. Per agent,
    # because that is the interesting comparison -- a DM and a player need not
    # think the same way.
    loop: str = "shipped"


# Tools by name, so a spec can carry a reference to one across a process
# boundary. Registered here rather than passed in, for the reason above.
TOOLS: Dict[str, Callable] = {}


# -- one agent, in whatever process it happens to live ------------------------


class Agent:
    """One machine, its name scope, and the channels it hears on."""

    def __init__(self, spec: Spec) -> None:
        self.name = spec.name
        self.limit = spec.limit
        self.loop = spec.loop
        # An observer for the table loop's moves, set from outside. This is how
        # a lesson is taken from ordinary play rather than from a rig: the agent
        # plays, and what it did is watched.
        self.watch = None
        self.m = Machine()
        self.kb = Loader(self.m, scope=spec.name)
        for tool, request, key in spec.tools:
            self.kb.answerer(tool, request, TOOLS[key])
        for name, key in spec.computes:
            self.kb.computator(name, TOOLS[key])
        self.m.actuator(VOICE)
        self.kb.load(spec.corpus)
        self._said = 0  # how much of `m.emitted` has already been shipped

    def hear_or_refuse(self, u: Utterance) -> Optional[str]:
        """Hear it, or say why it could not be heard.

         An agent really will try to say the unsayable, and the wire must
        not die of it.

        See docs/design/table.md#hear-or-refuse.
        """
        try:
            back = self.kb.term(u.text)
            got = self.m.g.show(back)
            if got != u.text:
                return f"{u.speaker}->{u.hearer}: {u.text}  (heard as {got})"
            self.hear(u)
            return None
        except Exception as ex:  # the hearer's parser, refusing
            return f"{u.speaker}->{u.hearer}: {u.text}  ({type(ex).__name__})"

    def hear(self, u: Utterance) -> None:
        """An arrival, on a channel named for the speaker.

         Through `Loader.say`, which is the SCOPED door: it resolves the text
        against this agent's own table, so the same words become this agent's
        own nodes. A bare `channels.deliver` would mint a channel beside the one
        the corpus's trust rule names, and the rule would never match -- the twin
        trap, which is exactly what the scoped door exists to prevent.
        """
        self.kb.say(u.speaker, u.text)

    def think(self) -> List[Utterance]:
        """Run to quiescence, then ship whatever was said.

         `m.emitted` is cumulative, so only the tail is new. Shipping the whole
        list each round re-delivers everything ever said, which reads as an agent
        repeating itself for ever and is quiescence-proof, because each arrival
        is a fresh entry (§10's two indices).
        """
        if self.loop == "table":
            from ..core.attention import run as table_run
            table_run(self.m, limit=self.limit, watch=self.watch)
        else:
            self.m.run(limit=self.limit)
        fresh, self._said = self.m.emitted[self._said:], len(self.m.emitted)
        out = []
        for node in fresh:
            u = self._utterance(node)
            if u is not None:
                out.append(u)
        return out

    def _utterance(self, node) -> Optional[Utterance]:
        """`tell(<hearer>, <what>)` becomes an utterance; any other act is left
        alone -- an agent may do things that are not speaking."""
        g = self.m.g
        rel = g.relation_of(node)
        if rel is None or g.show(rel) != "tell" or len(g.members(node)) != 2:
            return None
        hearer, what = g.members(node)
        return Utterance(self.name, g.show(hearer), g.show(what))

    def believes(self, text: str) -> bool:
        return self.m.holds(self.kb.term(text)) == "+"

    def beliefs(self) -> List[str]:
        """Everything this agent currently holds, as text -- the only honest way
        to compare two agents, since their node ids mean nothing to each other."""
        seen = {}
        for mo in self.m.chain.moments:
            for e in mo.delta:
                seen[self.m.g.show(e.proposition)] = e.sign
        return sorted(p for p, s in seen.items() if s == "+")


# -- the wire -----------------------------------------------------------------


class Local:
    """Everything in one process. The default, and the reference transcript."""

    def __init__(self, specs: Sequence[Spec]) -> None:
        self.agents = [Agent(s) for s in specs]
        self.by_name = {a.name: a for a in self.agents}
        self.refused: List[str] = []

    def order(self) -> List[str]:
        return [a.name for a in self.agents]

    def deliver(self, us: Sequence[Utterance]) -> None:
        for u in us:
            if u.hearer in self.by_name:
                why = self.by_name[u.hearer].hear_or_refuse(u)
                if why is not None:
                    self.refused.append(why)

    def think(self) -> List[Utterance]:
        out: List[Utterance] = []
        for a in self.agents:  # declared order, never a dict's
            out.extend(a.think())
        return out

    def beliefs(self) -> Dict[str, List[str]]:
        return {a.name: a.beliefs() for a in self.agents}

    def where(self) -> Dict[str, int]:
        return {a.name: os.getpid() for a in self.agents}

    def close(self) -> None:
        pass


def _worker(spec: Spec, inbox, outbox) -> None:
    """One agent, in its own process. Module-level, because Windows spawns.

    The protocol is one message per round and a reply per round, so the parent
    is a barrier and the transcript cannot depend on who finished first.
    """
    agent = Agent(spec)
    while True:
        msg = inbox.get()
        if msg is None:
            outbox.put(("bye", spec.name, None))
            return
        kind, payload = msg
        if kind == "hear":
            no = [w for w in (agent.hear_or_refuse(u) for u in payload) if w]
            outbox.put(("heard", spec.name, no))
        elif kind == "think":
            outbox.put(("said", spec.name, agent.think()))
        elif kind == "beliefs":
            outbox.put(("beliefs", spec.name, agent.beliefs()))
        elif kind == "where":
            #  Which process am I in? Without this the equivalence check
            # below cannot fail: a `Processes` that quietly ran everything in
            # the parent would produce an identical transcript for the most
            # boring reason there is, and report it as a ⭐⭐⭐ result.
            outbox.put(("where", spec.name, os.getpid()))


class Processes:
    """One OS process per agent, talking over queues.

     This exists to be MEASURED against `Local`, not because it is faster. A
    round is a barrier, so the processes serialise anyway and buy no wall clock.
    What they buy is that disjointness stops being a promise: no instrument, and
    no mistake of mine, can reach across a process boundary into another agent's
    graph. This design's own idiom -- *structural rather than promised*.
    """

    def __init__(self, specs: Sequence[Spec]) -> None:
        ctx = mp.get_context("spawn")  # the portable one; Windows has no fork
        self.names = [s.name for s in specs]
        self.procs, self.inboxes, self.outbox = {}, {}, ctx.Queue()
        self.refused: List[str] = []
        for s in specs:
            box = ctx.Queue()
            p = ctx.Process(target=_worker, args=(s, box, self.outbox), daemon=True)
            p.start()
            self.procs[s.name], self.inboxes[s.name] = p, box

    def order(self) -> List[str]:
        return list(self.names)

    def _round_trip(self, kind: str, per_agent=None) -> Dict[str, object]:
        """Ask every agent, then collect every reply, keyed by NAME.

         **Keyed by name and re-sorted into the declared order**, never taken
        in arrival order. One queue serves every child, so replies arrive in
        whatever order the scheduler ran them -- which is the one place a process
        table could quietly stop being reproducible.
        """
        for n in self.names:
            self.inboxes[n].put((kind, per_agent.get(n) if per_agent else None))
        got: Dict[str, object] = {}
        while len(got) < len(self.names):
            _, name, payload = self.outbox.get()
            got[name] = payload
        return got

    def deliver(self, us: Sequence[Utterance]) -> None:
        per = {n: [u for u in us if u.hearer == n] for n in self.names}
        got = self._round_trip("hear", per)
        for n in self.names:  # declared order here too
            self.refused.extend(got.get(n) or ())

    def collect(self, got: Dict[str, object]) -> List[Utterance]:
        """Replies, in the DECLARED agent order rather than the order they
        arrived in.

         **Extracted so it can be checked without a race.** One queue serves
        every child, so `got`'s insertion order is whatever the OS scheduler
        produced -- which means a transport that used arrival order agrees with
        `Local` on most runs and disagrees on some. A check that only notices
        when the scheduler misbehaves is a check that reports green while the
        bug is present, which is worse than not having it. As a pure function of
        `got` it can be handed a deliberately reversed dict, every run.
        """
        out: List[Utterance] = []
        for n in self.names:
            out.extend(Utterance(*u) for u in got.get(n, ()))
        return out

    def think(self) -> List[Utterance]:
        return self.collect(self._round_trip("think"))

    def beliefs(self) -> Dict[str, List[str]]:
        return {n: list(v) for n, v in self._round_trip("beliefs").items()}

    def where(self) -> Dict[str, int]:
        """Each agent's process id, so *these really are processes* is a
        measurement rather than an assumption."""
        return {n: int(v) for n, v in self._round_trip("where").items()}

    def close(self) -> None:
        for n in self.names:
            self.inboxes[n].put(None)
        for p in self.procs.values():
            p.join(timeout=10)


class Table:
    """Round-robin over agents, with a barrier per round."""

    def __init__(self, specs: Sequence[Spec], transport=Local) -> None:
        self.wire = transport(specs)
        self.transcript: List[Tuple[int, Utterance]] = []

    def play(self, rounds: int = 12) -> int:
        """Until nobody says anything. Returns the round it went quiet in."""
        for r in range(1, rounds + 1):
            said = self.wire.think()
            for u in said:
                self.transcript.append((r, u))
            if not said:
                return r
            self.wire.deliver(said)
        return rounds

    def beliefs(self) -> Dict[str, List[str]]:
        return self.wire.beliefs()

    @property
    def refused(self) -> List[str]:
        """Utterances the hearer's parser would not read. Surfaced rather than
        swallowed -- an agent that cannot be understood is a finding."""
        return list(getattr(self.wire, "refused", ()))

    def close(self) -> None:
        self.wire.close()


# -- the scenario -------------------------------------------------------------
#
# Three agents and one fact. The DM knows the door is locked and that p1 can see
# it; p1 believes the DM and gossips to p2; p2 believes p1. Nothing is shared, so
# p2 can only come to know it by being TOLD -- twice over.

DM = """
# The DM narrates what a player can perceive. Nothing else leaves it.
rule <narrate> = implies( { +locked($d), +sees($who, $d) },
                          { +doing(tell($who, locked($d))) } )
fact +locked(door1)
fact +sees(p1, door1)
"""

P1 = """
# ⭐ The trust rule is the whole of what makes an utterance a belief, and it is
# the CORPUS's, not the wire's. Delete it and p1 hears the DM and believes
# nothing -- which is the property being tested, not a bug.
rule <trust-dm> = implies( { +says(dm, $p, plus) }, { +$p } )
rule <gossip>   = implies( { +locked($d) }, { +doing(tell(p2, locked($d))) } )
"""

P2 = """
rule <trust-p1> = implies( { +says(p1, $p, plus) }, { +$p } )
"""

# The same agent with nothing that turns hearing into believing.  Written out
# rather than string-edited from `P1`: the first version replaced the rule's NAME
# and left its body attached to the next declaration, so the trust rule was still
# there under another name and the check passed for the wrong reason.
P1_DEAF = """
rule <gossip> = implies( { +locked($d) }, { +doing(tell(p2, locked($d))) } )
"""

SCENARIO = (
    Spec("dm", DM),
    Spec("p1", P1),
    Spec("p2", P2),
)

#  **A second scenario, because the first cannot measure ordering.** In
# SCENARIO exactly one agent speaks per round, so arrival order and declared
# order are the same sequence and a transport that collected replies in
# whichever order the OS scheduler finished them would agree with `Local` every
# time. Here the DM tells BOTH players in round one and both gossip back in
# round two, so a round carries utterances from two speakers and the order they
# are collected in is a real choice that a check can see.
CROSSTALK = (
    Spec("dm", """
rule <narrate> = implies( { +locked($d), +sees($who, $d) },
                          { +doing(tell($who, locked($d))) } )
fact +locked(door1)
fact +sees(p1, door1)
fact +sees(p2, door1)
"""),
    Spec("p1", """
rule <trust-dm> = implies( { +says(dm, $p, plus) }, { +$p } )
rule <tell-dm>  = implies( { +locked($d) }, { +doing(tell(dm, heard(p1, $d))) } )
"""),
    Spec("p2", """
rule <trust-dm> = implies( { +says(dm, $p, plus) }, { +$p } )
rule <tell-dm>  = implies( { +locked($d) }, { +doing(tell(dm, heard(p2, $d))) } )
"""),
)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    failing, ran = 0, 0

    def gate(name: str, ok: bool) -> None:
        nonlocal failing, ran
        ran += 1
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
        if not ok:
            failing += 1

    print(__doc__)
    print("Three agents, one fact, nothing shared\n")

    t = Table(SCENARIO)
    quiet = t.play()
    for r, u in t.transcript:
        print(f"    round {r}  {u.speaker} -> {u.hearer}: {u.text}")
    print(f"    (quiet in round {quiet})\n")
    b = t.beliefs()
    for n in ("dm", "p1", "p2"):
        print(f"    {n:4} believes locked(door1): "
              f"{'yes' if 'locked(door1)' in b[n] else 'no '}   "
              f"({len(b[n])} beliefs)")
    print()

    gate("the word travels two hops: dm -> p1 -> p2",
         all("locked(door1)" in b[n] for n in ("dm", "p1", "p2")))

    #  **Two checks that exist because a kill-probe found nothing without
    # them.** Comparing `Local` against `Processes` cannot see a bug in `Agent`,
    # which both transports share -- an A/B is blind to whatever is common to
    # both arms. Shipping the whole of `m.emitted` each round instead of the
    # tail, and delivering every utterance to every agent, were both invisible
    # to all nine checks that existed first.
    said_twice = [u for u in {tuple(u) for _, u in t.transcript}
                  if sum(1 for _, v in t.transcript if tuple(v) == tuple(u)) > 1]
    gate("⭐⭐ nobody repeats themselves, and the table goes QUIET -- `m.emitted` "
         "is cumulative, so shipping it whole re-tells everything every round "
         "and the table never settles",
         not said_twice and quiet < 12)
    gate("⭐⭐⭐ an utterance is DIRECTED: the DM spoke to p1, and p2 has no "
         "record of the DM speaking at all -- broadcast would leak the world to "
         "an agent no rule ever told",
         not any(s.startswith(("arrived(dm", "says(dm"))
                 for s in t.wire.agents[2].beliefs()))
    gate("⭐ and it took two rounds to get there -- a barrier means an utterance "
         "made in one round is heard in the next, never mid-thought",
         max(r for r, _ in t.transcript) >= 2)

    # -- fog of war, structurally ------------------------------------------
    half = Table(SCENARIO)
    half.wire.agents[0].think()          # only the DM thinks
    b2 = half.beliefs()
    gate("⭐⭐⭐ FOG OF WAR IS STRUCTURAL: before anyone is told, p1 and p2 hold "
         "nothing about the door -- not because the corpus was careful, but "
         "because the fact is in a graph they cannot reach",
         "locked(door1)" not in b2["p1"] and "locked(door1)" not in b2["p2"])

    deaf = Table((SCENARIO[0], Spec("p1", P1_DEAF), SCENARIO[2]))
    deaf.play(rounds=4)
    bd = deaf.beliefs()
    heard = [u for _, u in deaf.transcript if u.hearer == "p1"]
    gate("⭐⭐ the TRUST RULE is what makes an utterance a belief, and it belongs "
         "to the corpus: delete p1's and it is TOLD and still believes nothing",
         heard and "locked(door1)" not in bd["p1"] and "locked(door1)" not in bd["p2"])
    gate("...and what it was told is still on its record -- heard, not believed, "
         "which is the distinction `arrived` and `says` exist to keep",
         any(s.startswith("arrived(dm") or s.startswith("says(dm")
             for s in deaf.wire.agents[1].beliefs()))

    # -- what cannot cross --------------------------------------------------
    a = Table(SCENARIO).wire.agents[0]
    refused = []
    for label, txt in (("a moment", a.m.g.show(a.m.chain.moments[0].node)),
                       ("a rule", "<narrate>"),
                       ("a variable", "locked($d)")):
        try:
            Table(SCENARIO).wire.agents[1].hear(Utterance("dm", "p1", txt))
        except Exception:
            refused.append(label)
    gate(" an agent cannot utter a time, a rule, or anything generic -- all "
         f"three refused at the receiver's parser, not silently mangled: {refused}",
         len(refused) == 3)

    #  **The mishearing that raises nothing.** `a(b)(c)` is a real structure
    # -- a node whose relation is itself a node, which is how *a composed with b,
    # applied to c* differs from *a applied to b of c* -- and `Loader.term`
    # returns `a(b)` for it with no exception. Without the round-trip guard the
    # hearer believes `a(b)`, the wire reports a clean delivery, and nothing
    # anywhere disagrees.
    lone = Table(SCENARIO)
    why = lone.wire.agents[1].hear_or_refuse(Utterance("dm", "p1", "a b"))
    # ⭐⭐⭐ And the engine now refuses it at the source, so this check changed
    # what it is watching.  So the assertion is *refused, and nothing was
    # believed* rather than *refused by this particular layer* -- otherwise the
    # check fails the moment the defect it...
    # → docs/design/table.md#and-the-engine-now-refuses-it-at-the-sourc
    gate("⭐⭐⭐ an utterance that does not ROUND-TRIP is refused, and nothing is "
         "believed -- the wire re-renders what was understood, and the parser "
         f"now refuses the truncation at source as well -- {why}",
         why is not None
         and not any(s.startswith("arrived(dm")
                     for s in lone.wire.agents[1].beliefs()))

    # ⭐ And the case this guard was FIRST written against is now a fix rather
    # than a trap: `a(b)(c)` -- a node whose relation is itself a structure --
    # used to parse to `a(b)` and be heard as something nobody said. The parser
    # learned chained application, so it now crosses intact.
    comp = Table(SCENARIO)
    ok_why = comp.wire.agents[1].hear_or_refuse(Utterance("dm", "p1", "a(b)(c)"))
    gate("⭐⭐ a COMPOSITE RELATION survives the wire: `a(b)(c)` is heard as "
         "itself, and is a different node from `a(b(c))` at the far end -- "
         "which is what stops *a composed with b* and *a applied to b of c* "
         "being one thing between two agents",
         ok_why is None
         and comp.wire.agents[1].kb.term("a(b)(c)")
             != comp.wire.agents[1].kb.term("a(b(c))"))

    # -- the same transcript across OS processes ---------------------------
    print("\n  the same table, one OS process per agent:")
    p = Table(SCENARIO, transport=Processes)
    try:
        where = p.wire.where()
        print(f"    parent pid {os.getpid()}, agents {where}")
        pquiet = p.play()
        ptrans = [(r, tuple(u)) for r, u in p.transcript]
        pb = p.beliefs()
    finally:
        p.close()
    for r, u in ptrans:
        print(f"    round {r}  {u[0]} -> {u[1]}: {u[2]}")
    gate(" ...and they really ARE processes: three distinct pids, none of "
         "them the parent's -- without this the equivalence below passes for "
         "the most boring reason there is",
         len(set(where.values())) == 3 and os.getpid() not in set(where.values()))
    gate("⭐⭐⭐ processes produce the IDENTICAL transcript, round for round -- "
         "which is what makes the transport a swap rather than a redesign",
         ptrans == [(r, tuple(u)) for r, u in t.transcript] and pquiet == quiet)
    gate("...and the identical beliefs, agent for agent",
         all(pb[n] == b[n] for n in ("dm", "p1", "p2")))

    # -- ordering, where it can actually be measured ------------------------
    cl = Table(CROSSTALK)
    cl.play()
    cp = Table(CROSSTALK, transport=Processes)
    try:
        cp.play()
        cpt = [(r, tuple(u)) for r, u in cp.transcript]
    finally:
        cp.close()
    clt = [(r, tuple(u)) for r, u in cl.transcript]
    crowded = max((sum(1 for r, _ in clt if r == n) for n in {r for r, _ in clt}),
                  default=0)
    speakers = {r: len({u[0] for rr, u in clt if rr == r}) for r, _ in clt}
    print("\n  crosstalk -- two speakers in one round:")
    for r, u in clt:
        print(f"    round {r}  {u[0]} -> {u[1]}: {u[2]}")
    gate(" the ordering check has something to measure: some round carries "
         f"utterances from two different speakers (max speakers/round "
         f"{max(speakers.values(), default=0)}, max utterances/round {crowded})",
         max(speakers.values(), default=0) >= 2)
    gate("⭐⭐⭐ and WITH two speakers in a round the transcripts still match "
         "exactly -- replies are keyed by name and re-sorted into the declared "
         "order, never taken in the order the scheduler happened to finish",
         cpt == clt)

    #  The same claim, without a race. Handed a reply dict in exactly the
    # wrong order, `collect` must still produce declared order -- and the probe
    # that made this necessary is recorded on `collect` itself: an arrival-order
    # transport passes the check above on most runs.
    probe = Processes.__new__(Processes)
    probe.names = ["dm", "p1", "p2"]
    scrambled = {
        "p2": [("p2", "dm", "b")], "dm": [("dm", "p1", "a")], "p1": [("p1", "dm", "c")],
    }
    gate("⭐⭐⭐ ...and it is the ORDER that does it, checked without waiting for "
         "the scheduler to misbehave: replies handed over backwards still come "
         "out in the order the agents were declared",
         [u.speaker for u in probe.collect(scrambled)] == ["dm", "p1", "p2"])

    print(f"\n{ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
