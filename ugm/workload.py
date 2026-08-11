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


class Result(NamedTuple):
    to_goal: Optional[int]  # ticks until the goal held -- what recall changes
    to_quiet: int  # ticks until nothing was left -- what recall does not
    writes_at_goal: int
    writes: int
    seconds: float


def run(
    domains: int, depth: int, table: bool = False, budget: Optional[int] = None
) -> Result:
    m = Machine()
    kb = load(m, corpus(domains, depth, 0, table))
    m.recall_budget = budget
    want = kb.term(f"w0_s{depth}(item)")
    to_goal, writes_at_goal, ticks = None, 0, 0
    t = time.perf_counter()
    for ticks in range(1, 200001):
        s = m.tick()
        if to_goal is None and m.holds(want) == "+":
            to_goal, writes_at_goal = ticks, m.gate.writes
        if s.state not in ("applied", "supposed", "widened", "quiet"):
            break
    return Result(to_goal, ticks, writes_at_goal, m.gate.writes, time.perf_counter() - t)


def main() -> int:
    import sys

    if hasattr(sys.stdout, "reconfigure"):  # the selftest does the same
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("a workload recall can be measured on -- D domains x depth R, one goal in one")
    print()
    print(f"  {'D':>3} {'R':>3}   {'recall':<24} {'->goal':>7} {'->quiet':>8} "
          f"{'w@goal':>7} {'writes':>7}")

    failures = 0
    for domains, depth in ((4, 4), (8, 4), (8, 8)):
        rows = [
            ("exhaustive", run(domains, depth)),
            (f"budget {depth}, no table", run(domains, depth, False, depth)),
            (f"budget {depth}, ideal table", run(domains, depth, True, depth)),
        ]
        for name, r in rows:
            print(
                f"  {domains:>3} {depth:>3}   {name:<24} {str(r.to_goal):>7} {r.to_quiet:>8} "
                f"{r.writes_at_goal:>7} {r.writes:>7}"
            )
            if r.to_goal is None:
                print("        <-- MISSED THE GOAL")
                failures += 1
        # The gate: on this workload the table must buy something, or the
        # workload is the n-rule chain again with more rules.
        base, ideal = rows[0][1], rows[2][1]
        if ideal.to_goal is None or base.to_goal is None or ideal.to_goal > base.to_goal / 4:
            print("        <-- the table bought nothing: this workload cannot measure recall")
            failures += 1
        print()

    print("  ** The table reaches the goal in exactly R ticks -- it is perfect, and it")
    print("     was INVISIBLE in the ->quiet column, which is the same for all three.")
    print()
    print("  > **Recall cannot save work in a machine that runs to quiescence.**")
    print("  > Narrowing changes the ORDER in which everything is done, not how much")
    print("  > is done. The prize is real and only an agent that can STOP collects it.")
    print()
    print("  So the thing in front of learning is not a bigger corpus. It is a reason")
    print("  to stop -- the same open question as *when is a plan settled*, *when is a")
    print("  `due` rule done*, *when may a request be re-asked*.")
    print()
    print("  ** THE TABLE IS A CEILING, NOT AN ALGORITHM. It is authored, it names the")
    print("  answer, and nothing here learns. What it establishes is the size of the")
    print("  prize and a gate that can fail.")
    return failures


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
