"""Backward reading, as rules -- and what deleting the phase changed (§5, §18).

Goal expansion was the last interpreter phase. It is gone (`nophases`), and what
replaced it ships in the bundle: `<ask-fit>`, `<plan>`, `<expand>`, `<ask-check>`,
`<give-up>`, over three requests the machinery answers at the write.

    python -m ugm.backward

This file used to *compare the two readers*, and that comparison is the reason
the phase could go, so the result is kept here rather than deleted with it:

    by the phase    28 facts
    by rules        29 facts

    RULES ONLY      achieved(water(kettle))

**The phase starved forward reasoning.** It ran ahead of recall and returned
early, so while any goal was unexpanded no ordinary rule could apply.
`water(kettle)` is derivable forwards from this corpus, and the phase judged it
unsatisfied because it had not let anything derive it yet. That is not a
disagreement about backward reading -- it is a precedence claim that had been
written in control flow, where §18 says nothing can see it or override it.

**That extra fact is not reproduced by this run, and the reason is a second
finding.** Backward reading now ships in the bundle, so it is authored *before*
the corpus rather than after, and `<ask-check>` reaches `water(kettle)` earlier --
before anything has derived it. It answers `unmet`, and nothing ever asks again:
a request is a fact, so **a request can only be made once**. Quiescence stops the
re-ask (`+check` is already written, so re-concluding it changes nothing).

So the phase's starvation was real and its repair is not automatic. What the
rules gain is that the timing is now a corpus's to fix -- a rule may re-ask under
a fresh request node -- where under the phase it was not expressible at all.
`ugm.backward`'s original 29th fact is therefore recorded here as a *claim about
the phase*, not as a current output.

⚠ **The re-ask now exists** (`again(<request>, <occasion>)`, §13) and this run
still does not use one, deliberately: what it measures is the replacement on its
own, and a corpus rule that recovers the fact would measure the corpus. The
`a_request_can_be_re_asked` checks in `ugm.selftest` are where the recovery is
shown, on a fixture built for it.

What the run measures now is the replacement, on its own: does it reach the plan,
and is every one of the five rules load-bearing? The second half is not optional.
Three checks in this project reported success while unable to fail, and the one
that caught them each time was **delete each rule of the thing you are checking,
one at a time, and report any rule the fixture cannot kill.**

What the request has to return was the finding that made any of it possible. The
obvious design -- answer with a yes and a binding -- does not work, and not for
an implementation reason: a binding is a map from variables to nodes, and a rule
cannot hold one, let alone apply it. So the answer arrives already instantiated:

    +fits(<R>, goal)             it could
    +need(<R>, goal, <subgoal>)  one per antecedent member, already substituted

> **Match and substitute travel together, because the caller cannot do the
> second half.**

And the last verdict cannot be a rule at all. The natural sixth rule is

    implies( {+goal(?w), +unfit(?r, ?w)}, {+blocked(?w)} )

and it is wrong: it fires when **some** rule does not fit, while `blocked` claims
that **no** rule does -- an aggregate over a *finished* search. A `-` member
cannot say it either (§9's `-` is *an entry denies this*, never *for no `?r`*).
So `blocked` is answered by the machinery, to a `+verdict(?w)` request that
`<give-up>` makes at `quiet` -- when the search that the aggregate is over has
actually finished.
"""

from typing import List, Set, Tuple

from .chain import PLUS
from .machine import Machine
from .text import load

def _corpus(taps: Tuple[str, ...]) -> str:
    return chr(10).join([
        "rule <boil>  = implies( { +heat(?w), +water(?w) },  { +boiling(?w) } )",
        "rule <heat>  = implies( { +on(?s), +over(?w, ?s) }, { +heat(?w) } )",
        "rule <tea>   = implies( { +boiling(?w), +leaf(?l) }, { +tea(?w, ?l) } )",
        # Two subgoals sharing a variable, and a world where checking them
        # independently gets it wrong: `tap(?t)` is satisfiable by either tap,
        # and `under(kettle, ?t)` only by `drain`. §18's failure, made reachable.
        "rule <fill>  = implies( { +tap(?t), +under(kettle, ?t) }, { +water(kettle) } )",
    ] + [f"fact +tap({t})" for t in taps] + [
        "fact +under(kettle, drain)",
        "fact +leaf(green)",
        "",
    ])


# The SAME world, authored in two orders. `current_state` walks newest-first, so
# which tap `_settle` tries first is the one written last -- and nothing
# backtracks over a binding once it is taken.
AGREES = _corpus(("sink", "drain"))     # newest tap is `drain`; the siblings agree
DISAGREES = _corpus(("drain", "sink"))  # newest tap is `sink`; they do not
CORPUS = DISAGREES
GOAL = "tea(kettle, green)"

# What the plan is made of. The request traffic (`fit`, `fits`, `need`, `check`,
# `unfit`) is not read: what matters is the plan the reader arrives at.
SHARED = ("GOAL", "EXPANDS", "SUBGOAL", "BINDS", "ACHIEVED", "BLOCKED")

# The plan the phase produced, recorded before it was deleted, over the same
# vocabulary minus `blocked` (which the phase wrote, but as a state it reached
# rather than a verdict it asked for). Anything the rules no longer reach is a
# regression.
BY_PHASE = 28
PLAN_ONLY = ("GOAL", "EXPANDS", "SUBGOAL", "BINDS", "ACHIEVED")


def _facts(m: Machine) -> Set[str]:
    """Every fact the plan is made of.

    An earlier version compared only the goals reached, and three of the five
    rules were unkillable as a result -- the plan, the satisfaction check and the
    verdict all write facts the comparison never looked at. A gate is only as
    strong as what it reads.
    """
    wanted = {getattr(m, name) for name in SHARED}
    out: Set[str] = set()
    for mo in m.chain.moments:
        for e in mo.delta:
            if e.sign == PLUS and m.g.relation_of(e.proposition) in wanted:
                out.add(m.g.show(e.proposition))
    return out


def _read(drop: Tuple[str, ...] = (), corpus: str = CORPUS) -> Tuple[Set[str], int, int]:
    m = Machine()
    kb = load(m, corpus)
    if drop:
        m.rules.rules = [r for r in m.rules.rules if r.name not in drop]
    m.gate.write(m.focus, m.g.rel(m.GOAL, kb.term(GOAL)), PLUS, mention=True)
    steps = m.run(limit=2000)
    return _facts(m), m.gate.writes, len(steps)


def run() -> int:
    facts, writes, steps = _read()

    print("backward reading -- the rules that replaced the last phase")
    print(f"  goal            {GOAL}")
    print(f"  by rules        {len(facts)} facts, {steps} steps, {writes} writes")
    print(f"  by the phase    {BY_PHASE} facts, before it was deleted")
    print()
    for x in sorted(facts):
        print(f"    {x[:88]}")
    print()

    # The plan itself, and the sibling-agreement case §18 warns about: `tap(?t)`
    # must be satisfied by the tap that `under(kettle, ?t)` agrees with.
    wanted = [
        ("the goal is expanded by a rule that fits it", "expands(plan(", "tea(kettle, green)"),
        ("its antecedent becomes subgoals, instantiated", "goal(boiling(kettle))", ""),
        ("recursion reaches the second rule", "goal(over(kettle, ?s))", ""),
        ("satisfaction is checked inside the plan's bindings", "binds(plan(", "water(kettle)"),
        # §18's silent failure, made reachable: `tap(?t)` is satisfiable by
        # `sink`, `under(kettle, ?t)` only by `drain`. Checked independently both
        # report achieved and the plan is wrong with nothing saying so.
        ("and siblings must agree, so the second is blocked", "blocked(under(kettle, ?t))", ""),
        ("nothing fits it, and the verdict says so after the loop stopped", "blocked(on(?s))", ""),
    ]
    failures = 0
    checked = 0
    for name, needle, also in wanted:
        ok = any(needle in f and also in f for f in facts)
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
        checked += 1
        failures += 0 if ok else 1

    # The same world, authored the other way round. This is not a second fixture
    # -- it is the measurement of what the sibling check does and does not buy.
    other, _, _ = _read(corpus=AGREES)
    agreed_ok = (
        "achieved(under(kettle, ?t))" in other and "blocked(under(kettle, ?t))" not in other
    )
    print(f"  {'ok  ' if agreed_ok else 'FAIL'}  "
          f"...and with the taps authored the other way round, the SAME world plans")
    checked += 1
    failures += 0 if agreed_ok else 1
    print()
    print("        Checking siblings inside the plan's bindings stops a wrong plan")
    print("        being reported as a good one. It does not FIND the right one:")
    print("        `_settle` takes the first entry that satisfies a subgoal and")
    print("        nothing reconsiders it, so which tap gets tried is decided by")
    print("        the walk -- newest first -- and therefore by authoring order.")
    print("        That is §21's backtracking item, measured rather than asserted.")
    print()

    plan_facts = {f for f in facts if not f.startswith("blocked(")}
    if len(plan_facts) < BY_PHASE:
        print(f"  FAIL  the rules reach fewer plan facts than the phase did "
              f"({len(plan_facts)} < {BY_PHASE})")
        failures += 1

    # Could this have failed? Three checks in this project reported success while
    # unable to, so agreement is never reported without asking.
    print()
    print("  can this gate fail? -- one rule deleted at a time")
    blind: List[str] = []
    for name in ("ask-fit", "plan", "expand", "ask-check", "give-up"):
        got, _, _ = _read((name,))
        diff = len(facts ^ got)
        print(f"    {name:10} {diff:>3} facts differ" + ("" if diff else "   <-- BLIND"))
        if not diff:
            blind.append(name)

    print()
    # ⚠ The COUNT, not only the failures: `0 failing` reads the same
    # whether this ran every check or none. `ugm.selftest` has printed its
    # count all along and is the only instrument that could have said so
    # when ten of `ugm.learning`'s were deleted by an edit.
    print(f"{checked} checks, {failures} failing, {len(blind)} blind")
    return failures + len(blind)


if __name__ == "__main__":
    raise SystemExit(1 if run() else 0)
