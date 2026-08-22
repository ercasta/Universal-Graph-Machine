"""The agent takes one move; the world runs to quiescence; then it is asked again.

    python -m ugm.probes.alternation

Two pools over one graph, and neither corpus mentions the other's vocabulary:
the world's rules say what follows from an act, the agent's rules say what to do
about an open gap. `probes.experts` built the mechanism -- a table over a SUBSET
of the rules -- for consultation between experts; this uses it to separate
deliberation from physics.

What the alternation buys and what it does not is the point of the file. It
fixes the TIMING: the world has settled before the agent is asked again, so
there are no commitment races and nothing needs a guard saying *I am already
doing something about this*. It does NOT fix the WANTING: with rules keyed on
`goal(...)`, the agent still acts twice, because a goal outlives its own
satisfaction. Keyed on the GAP -- recomputed at a settled world -- a want cannot
outlive what closes it, and one act per want falls out with no bookkeeping at
all.

See docs/design/alternation.md.
"""

import sys
from typing import List, Tuple

from ..core.attention import Table, run, _standing
from ..core.chain import PLUS
from ..core.machine import Machine
from ..core.text import load

# The world: what follows from an act. It never mentions a want.
WORLD = """rule <eff>  = implies( { +did($a), +achieves($a, $y) }, { +$y } )
rule <cost> = implies( { +did(smash($j)) }, { -intact($j) } )
fact +tap(sink)
fact +under(kettle, sink)
fact +jug(jug1)
fact +holds(jug1, kettle)
fact +intact(jug1)
fact +achieves(smash(jug1), water(kettle))
"""
WORKS = "fact +achieves(fill(kettle), water(kettle))\n"

# The agent: what to do about an open gap. It never mentions `did` or `achieves`.
GAP_KEYED = """rule <use-jug> = implies( { +missing(gap, water($w)), +jug($j), +holds($j, $w) },
                        { +doing(smash($j)) } )
rule <use-tap> = implies( { +missing(gap, water($w)), +tap($t), +under($w, $t) },
                        { +doing(fill($w)) } )
"""
# ...and the control: the same agent, wanting by `goal` instead of by gap.
GOAL_KEYED = """rule <use-jug> = implies( { +goal(water($w)), +jug($j), +holds($j, $w) },
                        { +doing(smash($j)) } )
rule <use-tap> = implies( { +goal(water($w)), +tap($t), +under($w, $t) },
                        { +doing(fill($w)) } )
fact +goal(water(kettle))
"""

AGENT_RULES = {"use-jug", "use-tap"}


def alternate(src: str, cycles: int = 6, ask_gap: bool = True) -> Tuple[Machine, object, List[str]]:
    """One move from the agent, then the world to quiescence, then ask again."""
    m = Machine()
    m.actuator("hands")
    kb = load(m, src)
    agent = [r for r in m.rules.rules if r.name in AGENT_RULES]
    world = [r for r in m.rules.rules if r.name not in AGENT_RULES]
    at, wt = Table(m.g, agent, _standing(m)), Table(m.g, world, _standing(m))
    # The request is a fact, so asking again is writing it again: what makes the
    # answer fresh is that it is asked at a settled world, not that the question
    # changed.
    req = kb.term("delta(now, wanted(water(kettle)), gap)")
    trace: List[str] = []
    for _ in range(cycles):
        if ask_gap:
            m.gate.write(req, PLUS, source=m.KB)
        moved = run(m, limit=1, pool=agent, table=at)
        settled = run(m, limit=200, pool=world, table=wt)
        took = [s.applied.rule.name for s in moved.steps if s.applied]
        trace.append(f"{took[0] if took else '-':9} "
                     f"(world settled in {len([s for s in settled.steps if s.applied])})")
    return m, kb, trace


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

    # -- 1. one act per want, with nothing guarding it ----------------------
    m, kb, trace = alternate(WORLD + WORKS + GAP_KEYED)
    print("  untaught, keyed on the gap:")
    for i, row in enumerate(trace):
        print(f"    cycle {i}  {row}")
    print(f"    emitted {[m.g.show(x) for x in m.emitted]}\n")
    gate("one act leaves the agent, and no rule says *I am already doing that*: "
         "the gap it was answering is closed by the time it is asked again",
         len(m.emitted) == 1)
    gate("...and the agent then stops, because nothing is missing -- wanting "
         "runs out before the tick limit does",
         all(row.startswith("-") for row in trace[2:]))

    # -- 2. competence chooses among the OPEN routes ------------------------
    taught, kb_t, _ = alternate(WORLD + WORKS + GAP_KEYED + "fact +attention(sink, 3)\n")
    print(f"  taught (attention(sink, 3)): emitted "
          f"{[taught.g.show(x) for x in taught.emitted]}\n")
    gate("a lesson decides WHICH open route is taken, and the jug survives -- "
         "which is all competence has to do once the architecture guarantees one",
         [taught.g.show(x) for x in taught.emitted] == ["fill(kettle)"]
         and taught.holds(kb_t.term("intact(jug1)")) == PLUS)
    gate("...and untaught it does not: the fixture can fail",
         m.holds(kb.term("intact(jug1)")) != PLUS)

    # -- 2b. and WHICH one is style ------------------------------------------
    careful, kb_c, _ = alternate(WORLD + WORKS + GAP_KEYED
                                 + "fact +attention(sink, 3)" + chr(10))
    barbarian, kb_b, _ = alternate(WORLD + WORKS + GAP_KEYED
                                   + "fact +attention(sink, -3)" + chr(10))
    print(f"  careful   (attention(sink,  3)): "
          f"{[careful.g.show(x) for x in careful.emitted]}")
    print(f"  barbarian (attention(sink, -3)): "
          f"{[barbarian.g.show(x) for x in barbarian.emitted]}")
    print()
    gate("two agents, one corpus, one weight apart: where there is more than "
         "one way to a want, which way is taken is STYLE -- and a negative "
         "weight is what lets a corpus say a way is against its character "
         "without saying it is unavailable",
         [careful.g.show(x) for x in careful.emitted] == ["fill(kettle)"]
         and [barbarian.g.show(x) for x in barbarian.emitted] == ["smash(jug1)"])
    gate("...and the barbarian is not broken: it reaches the want, by the way "
         "it prefers", barbarian.holds(kb_b.term("intact(jug1)")) != PLUS
         and careful.holds(kb_c.term("intact(jug1)")) == PLUS)

    # -- 3. the control: alternation alone is NOT enough ---------------------
    goals, kb_g, trace_g = alternate(WORLD + WORKS + GOAL_KEYED, ask_gap=False)
    print("  the control -- same alternation, wanting by `goal`:")
    for i, row in enumerate(trace_g):
        print(f"    cycle {i}  {row}")
    print(f"    emitted {[goals.g.show(x) for x in goals.emitted]}\n")
    gate("wanting by `goal`, the agent acts TWICE even though the world settled "
         "in between: a goal outlives its own satisfaction, and settling cannot "
         "fix what is still asserted",
         len(goals.emitted) == 2)

    # -- 4. the chosen route fails ------------------------------------------
    # Taught to prefer the tap, and the tap does not deliver: the lesson picks
    # the route, the world declines to cooperate, and the gap is what notices.
    failed, kb_f, trace_f = alternate(
        WORLD + GAP_KEYED + "fact +attention(sink, 3)" + chr(10))
    print("  taught to prefer the tap, and the tap does not deliver:")
    for i, row in enumerate(trace_f):
        print(f"    cycle {i}  {row}")
    print(f"    emitted {[failed.g.show(x) for x in failed.emitted]}\n")
    gate("a route that did not deliver leaves the gap open, so the alternative "
         "is taken on the next cycle -- passing up is revisable by construction, "
         "and nothing had to be un-said to revise it",
         [failed.g.show(x) for x in failed.emitted] == ["fill(kettle)", "smash(jug1)"])

    # -- 5. and the failing route is not retried -----------------------------
    only = WORLD.replace("fact +achieves(smash(jug1), water(kettle))\n", "")
    lone, kb_l, trace_l = alternate(only + """rule <use-tap> = implies(
        { +missing(gap, water($w)), +tap($t), +under($w, $t) },
        { +doing(fill($w)) } )
""")
    gate("with one route and no delivery the agent tries it ONCE and stops: "
         "refraction already says *not again on these grounds*, so nothing has "
         "to weigh a re-attempt down. A weight could say the way is against "
         "the agent's character, which is a different claim and orders rather "
         "than removes",
         [lone.g.show(x) for x in lone.emitted] == ["fill(kettle)"])

    print(f"\n{ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
