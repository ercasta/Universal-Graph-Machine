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

    failures = checks = 0
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
            checks += 1
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
        checks += 1
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

    checks += 8  # the fallible-advisor section's own gates
    failures += fallible_advisor()
    # A summary line at all, which this instrument never had: it printed prose
    # and returned a number nobody saw. `0 failing` over no checks is the failure
    # mode; no summary at all is worse.
    print()
    print(f"  {checks} checks, {failures} failing")
    return failures


def advisor(kind: str, domains: int, depth: int, wrong_at: int = 5) -> str:
    """A table an ADVISOR produced, right or wrong. The point is the wrong one.

    A learned table is authored by something fallible, and a model is fallible by
    construction -- so the question §19's carve-out turns on is not *how good can
    advice be* but **what does bad advice cost**. `ideal` is the ceiling this file
    already had; `wrong` is an advisor that is confident and mistaken, pointing at
    every domain except the one the goal is in.
    """
    if kind == "ideal":
        return chr(10).join(
            f"fact prefer(<d0s{i}>, w0_s{i}, {wrong_at})" for i in range(depth)
        ) + chr(10)
    if kind == "wrong":
        return chr(10).join(
            f"fact prefer(<d{d}s{i}>, w{d}_s{i}, {wrong_at})"
            for d in range(1, domains) for i in range(depth)
        ) + chr(10)
    return ""


def _advised(domains: int, depth: int, kind: str) -> Result:
    m = Machine()
    kb = load(m, corpus(domains, depth, 0, False) + stopping(depth)
              + advisor(kind, domains, depth))
    m.recall_budget = depth
    want = kb.term(f"w0_s{depth}(item)")
    to_goal, writes_at_goal, ticks, s = None, 0, 0, None
    t = time.perf_counter()
    for ticks in range(1, 40001):
        s = m.tick()
        if to_goal is None and m.holds(want) == "+":
            to_goal, writes_at_goal = ticks, m.gate.writes
        if s.state not in ("applied", "supposed", "widened", "quiet"):
            break
    return Result(to_goal, ticks, s.state if s else "?", writes_at_goal,
                  m.gate.writes, time.perf_counter() - t)


def fallible_advisor() -> int:
    """What does bad advice at this seam cost -- and what does good advice buy?

    Asked because the next thing anyone would put here is a **model**, and the
    design's stated reason for putting learning in recall is that *being wrong
    there is recoverable*. That claim had never been measured. It is true, and it
    is not the whole story.
    """
    depth, failures = 6, 0
    print()
    print("\n  ** WHAT A FALLIBLE ADVISOR COSTS -- the question a MODEL here turns on\n")
    print(f"  {'D':>3}   {'advice':<20} {'->goal':>7} {'->end':>7} {'writes':>8}")
    seen = {}
    for domains in (6, 12, 24):
        for kind, label in (("", "none"), ("ideal", "ideal"), ("wrong", "confidently wrong")):
            r = _advised(domains, depth, kind)
            seen[(domains, kind)] = r
            print(f"  {domains:>3}   {label:<20} {str(r.to_goal):>7} {r.to_end:>7} "
                  f"{r.writes:>8}")
            if r.to_goal is None:
                print("        <-- MISSED THE GOAL")
                failures += 1
        print()

    # ⚠ Two gates that pass on TODAY'S behaviour, deliberately, so the day either
    # changes someone is sent to this argument rather than left to rediscover it.
    for domains in (6, 12, 24):
        if seen[(domains, "ideal")].to_goal != seen[(domains, "")].to_goal:
            print(f"        <-- at D={domains} the ideal table now MOVES time-to-goal.")
            print("            §13's blocker may be fixed; recall is measurable again.")
            failures += 1
    if not (seen[(24, "wrong")].to_goal > seen[(12, "wrong")].to_goal
            > seen[(6, "wrong")].to_goal):
        print("        <-- bad advice no longer costs more as the agent knows more.")
        failures += 1

    # The control, and it turns a cost into a soundness result. `_widen` was
    # built against a budget too small to reach a rule that was there; it is now
    # measured against a different adversary -- an ADVISOR that is confident and
    # wrong -- and it is the only thing between that and a false `quiescent`.
    original = Machine._widen
    Machine._widen = lambda self, *a, **k: False  # type: ignore[assignment]
    try:
        blind = {d: _advised(d, depth, "wrong") for d in (6, 24)}
        base = {d: _advised(d, depth, "") for d in (6, 24)}
    finally:
        Machine._widen = original  # type: ignore[assignment]
    print("  with `_widen` disabled -- the guard that escalates a dry shortlist:\n")
    for d in (6, 24):
        for label, r in (("none", base[d]), ("confidently wrong", blind[d])):
            print(f"  {d:>3}   {label:<20} {str(r.to_goal):>7} {r.to_end:>7} "
                  f"{r.end:>10}")
    print()
    if blind[6].to_goal is not None or blind[24].to_goal is not None:
        print("        <-- bad advice no longer needs `_widen` to be survivable.")
        failures += 1
    if base[6].to_goal is None:
        print("        <-- `_widen` is now load-bearing for the UNADVISED run too.")
        failures += 1

    print("""  ⭐⭐⭐ **AND THAT IS A SOUNDNESS RESULT, NOT A COST ONE.** Take `_widen` away
  and a confidently wrong advisor does not merely slow the agent down: the goal
  is **never reached**, and the run ends `quiescent` -- *nothing left to do* --
  at tick 52. The agent does not fail; it reports success at having nothing to
  do while the thing it wanted is still unreached. §19's *a shortlist that ran
  dry is not a search that finished* was argued about a budget too small to
  reach a rule that was there. A bad advisor is the same error with an author,
  and the same one line answers both.

  > A model at this seam is safe **exactly to the extent that `_widen` is**, and
  > not one step further.

  > **AN ADVISOR AT THIS SEAM CAN ONLY LOSE.** A perfect table buys exactly
  > nothing at every scale; a confident wrong one costs 2.4x, 4.1x, 7.4x as the
  > agent's knowledge grows. The risk scales with what it knows and the prize
  > does not exist.

  Being wrong IS recoverable, which is what §19 claimed and what `_widen`
  delivers -- the goal is reached and the agent still stops, every time, and the
  widening count is the guard firing (30, 66, 138). ⚠ But **recoverable is not
  free**, and nothing in §19 said what recovery costs.

  ⚠⚠⚠ WHY THE PRIZE IS ZERO, and it is not §13's blocker alone. `->goal` is 43
  at D=6, D=12 and D=24 -- it does not move with the agent's knowledge AT ALL.
  The agent is already perfectly selective, because §14's `by_conclusion` index
  answers *what could produce this* EXACTLY. A model here would spend inference
  approximating something an index computes precisely.

  > **Put a model where there is no exact algorithm, not where there is one.**
  Intake (prose -> propositions, measured at 0/50) and grounding (`achieves(a,w)`,
  authored by hand today) are seams with no algorithm at all. Recall is not one.""")
    return failures


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
