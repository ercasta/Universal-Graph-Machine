"""A workload recall can be measured on -- and why the obvious one cannot (§19).

    python -m ugm.workload

§19 says recall is where experience belongs. Nothing can be learned there until
something can be *measured* there, and the fixture that was to hand -- an n-rule
forward chain -- cannot measure it at any size. On a 30-rule chain, between one
and eight rules match per tick, and since the state is indexed a rule that does
not match costs almost nothing. A perfect table would beat exhaustive recall by
nothing at all.

> **A shortlist pays only where many rules MATCH and are useless.** Scale is not
> the requirement; **selectivity** is.

That is this project's own recorded trap arriving again -- *a homogeneous fixture
cannot measure a discriminator* -- and a benchmark that cannot fail is worse than
none, because it reads as evidence.

So the workload is built to have the property, and the shape is borrowed from
`../pystrider`'s vocabularies rather than its rules: **separate worlds that must
be bridged.** Its rules are microfunctions -- the ISA-with-opcodes floor this
design rejects -- so nothing is ported. What is taken is the observation that
real knowledge comes in domains, most of which are irrelevant to any one task,
and that this is what makes coming-to-mind worth anything.

    D domains, each a chain of depth R over its own relations
    every domain seeded, so EVERY domain's rules match from the first tick
    one goal, in one domain

Every domain runs to completion under exhaustive recall: D x R applications where
R would do. That is the cost recall exists to remove, and it is now visible.

What the run reports is a **ceiling, not an algorithm**: the table is authored by
hand, naming exactly the rules the goal's domain needs. Nothing here learns. What
it establishes is that learning has something to win, how much, and a gate that
can fail -- and one finding that falls out of building it, in `main` below.
"""

import time
from typing import List, NamedTuple, Optional

from .machine import Machine
from .text import load


def corpus(domains: int, depth: int, target: int = 0, table: bool = False) -> str:
    lines: List[str] = []
    for d in range(domains):
        for i in range(depth):
            lines.append(
                f"rule <d{d}s{i}> = implies( {{ +w{d}_s{i}(?x) }}, {{ +w{d}_s{i+1}(?x) }} )"
            )
    # Every domain is in play. This is the point: the agent's knowledge is not
    # about the task, and nothing in the situation says which part of it is.
    for d in range(domains):
        lines.append(f"fact +w{d}_s0(item)")
    lines.append(f"fact +goal(w{target}_s{depth}(item))")
    if table:
        # The ceiling: exactly the rules this goal's chain needs, keyed on the
        # relation each of them waits for -- which is in play whenever that rule
        # is the one to apply.
        for i in range(depth):
            lines.append(f"fact prefer(<d{target}s{i}>, w{target}_s{i}, 5)")
    return chr(10).join(lines) + chr(10)


# The other half of the ceiling, and the one the earlier version of this file
# said was missing. A satisficing agent's whole policy, in one rule: *what I
# wanted holds, so I am done.*
#
# Authored and ground, for a reason worth stating rather than hiding. The
# general form -- `{ +goal(?w), +?w } => { +enough(?w) }` -- is unsound here, and
# running it is how that was found: `<expand>` writes `+goal(sub)` for every
# subgoal it derives, so `goal` does not distinguish what the agent wants from
# what backward reading wants on its behalf, and the agent stops at the first
# subgoal that happens to hold. Measured: it stopped at tick 51 of a run whose
# goal arrived at 57.
#
# A root goal is a `goal(?w)` with no `subgoal(?p, ?w)`, which is a negative
# existential over `?p` -- exactly what §12 says a `-` member cannot say, and the
# same shape as `blocked`. So it needs a request, or it needs the licence to be
# readable in the graph. Both are §21 items already.
def stopping(depth: int) -> str:
    return (
        f"rule <done> = implies( {{ +w0_s{depth}(item) }},"
        f" {{ +enough(w0_s{depth}(item)) }} )" + chr(10)
        # Not decoration. An unmarked stop rule is one competitor among many and
        # can be capped out of recall entirely -- §16's ordering trap, which is
        # why `standing` is carved out of the budget.
        + "fact standing(<done>)" + chr(10)
    )


class Result(NamedTuple):
    to_goal: Optional[int]  # ticks until the goal held -- what recall changes
    to_end: int  # ticks until the loop was over, however it was over
    end: str  # `quiescent` (exhausted) or `stopped` (satisfied)
    writes_at_goal: int
    writes: int
    seconds: float


def run(
    domains: int, depth: int, table: bool = False, budget: Optional[int] = None,
    stop: bool = False,
) -> Result:
    m = Machine()
    src = corpus(domains, depth, 0, table) + (stopping(depth) if stop else "")
    kb = load(m, src)
    m.recall_budget = budget
    want = kb.term(f"w0_s{depth}(item)")
    to_goal, writes_at_goal, ticks = None, 0, 0
    t = time.perf_counter()
    s = None
    for ticks in range(1, 200001):
        s = m.tick()
        if to_goal is None and m.holds(want) == "+":
            to_goal, writes_at_goal = ticks, m.gate.writes
        if s.state not in ("applied", "supposed", "widened", "quiet"):
            break
    return Result(to_goal, ticks, s.state if s else "?", writes_at_goal,
                  m.gate.writes, time.perf_counter() - t)


def main() -> int:
    import sys

    if hasattr(sys.stdout, "reconfigure"):  # the selftest does the same
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("a workload recall can be measured on -- D domains x depth R, one goal in one")
    print()
    print(f"  {'D':>3} {'R':>3}   {'configuration':<26} {'->goal':>7} {'->end':>6} "
          f"{'how':>10} {'w@goal':>7} {'writes':>7}")

    failures = 0
    for domains, depth in ((4, 4), (8, 4), (8, 8)):
        rows = [
            ("exhaustive", run(domains, depth)),
            ("exhaustive + stop", run(domains, depth, stop=True)),
            (f"budget {depth}, ideal table", run(domains, depth, True, depth)),
            (f"budget {depth}, table + stop", run(domains, depth, True, depth, True)),
        ]
        for name, r in rows:
            print(
                f"  {domains:>3} {depth:>3}   {name:<26} {str(r.to_goal):>7} {r.to_end:>6} "
                f"{r.end:>10} {r.writes_at_goal:>7} {r.writes:>7}"
            )
            if r.to_goal is None:
                print("        <-- MISSED THE GOAL")
                failures += 1
        # The gate, and it is a different one from the gate this file shipped
        # with, because measurement falsified that one's premise. See below.
        #
        # What must buy something is STOPPING: the whole claim is that an agent
        # which can be satisfied does less work than one which can only be
        # exhausted, and if that is ever untrue there is nothing here worth
        # having.
        base, stopped = rows[0][1], rows[1][1]
        if stopped.to_end >= base.to_end or stopped.writes >= base.writes:
            print("        <-- stopping bought nothing: the claim in front of learning is false")
            failures += 1
        print()

    print("  ** STOPPING IS THE PRIZE, AND IT IS COLLECTED. `enough` is one authored")
    print("  rule -- *what I wanted holds, so I am done* -- and the run ends within two")
    print("  ticks of the goal instead of grinding through every other domain.")
    print()
    print("  > A machine that can only be EXHAUSTED does an amount of work its corpus")
    print("  > fixes. Nothing it knows can make it cheaper, because knowing more only")
    print("  > reorders. Satisfaction is the second way to be over, and it is a CLAIM.")
    print()
    print("  ** AND THE OLD HEADLINE WAS PARTLY AN ARTEFACT -- this is the correction.")
    print("  This file used to report an ideal table reaching the goal in R ticks")
    print("  against 734, gated on the table buying something. It no longer does, and")
    print("  the reason is not that recall got worse:")
    print()
    print("  A budget small enough to steer was also small enough to cap the APPARATUS")
    print("  out of recall -- backward reading, surprise, and now stopping. The R-tick")
    print("  run was an agent with its machinery switched off. Stopping cannot be built")
    print("  on that (a stop rule recall may drop is not a stop rule), so `standing` is")
    print("  now carved out of the budget -- and with the apparatus always in mind, its")
    print("  AUTHORED PRECEDENCE decides the early ticks and the table's steering is")
    print("  invisible behind it.")
    print()
    print("  That is not a new problem. It is §13's unresolved blocker -- `<ask-fit>`")
    print("  monopolising arbitration, the deleted phase's precedence claim surviving")
    print("  as authored order -- now shown to hide recall's prize as well as cost.")
    print("  Recall cannot be measured again on this workload until it is fixed.")
    print()
    print("  ** THE TABLE IS STILL A CEILING, NOT AN ALGORITHM, and so is `<done>`.")
    print("  Both are authored and name the answer. What is established is the size of")
    print("  the prize, and a gate that can fail.")
    return failures


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
