"""Backward reading, as rules -- and how far that gets (§5, §18, §21).

Goal expansion is the last interpreter phase, and it is the one §5's wall runs
through: reading a rule backwards means deciding that a ground goal corresponds
to a rule's stored generic pattern, and that is `match`, which is floor.

This runs the experiment rather than arguing it. `Machine._fit` answers a match
**request**, and the rules below use it to expand a goal. What is measured is
whether they reach the same subgoals as the phase does.

    python -m ugm.backward

What the request has to return is the finding. The obvious design -- answer with
a yes and a binding -- does not work, and not for an implementation reason: a
binding is a map from variables to nodes, and a rule cannot hold one, let alone
apply it. Applying is substitution, which is floor. So the answer has to arrive
already instantiated:

    +fits(<R>, goal)             it could
    +need(<R>, goal, <subgoal>)  one per antecedent member, already substituted

> **Match and substitute travel together, because the caller cannot do the
> second half.**

That is the argument for `match` reified as a request rather than as a sixth
floor item. A primitive a rule invokes would still hand back a binding it cannot
use.
"""

from typing import List, Set, Tuple

from .chain import PLUS
from .graph import NodeId
from .machine import Machine
from .rules import IMPLIES, Member
from .text import load

CORPUS = chr(10).join([
    "rule <boil>  = implies( { +heat(?w), +water(?w) },  { +boiling(?w) } )",
    "rule <heat>  = implies( { +on(?s), +over(?w, ?s) }, { +heat(?w) } )",
    "rule <tea>   = implies( { +boiling(?w), +leaf(?l) }, { +tea(?w, ?l) } )",
    "",
])
GOAL = "tea(kettle, green)"


def _rule_level(m: Machine) -> None:
    """Two rules, and between them the whole of backward reading's core step.

    Neither could be written before: the first concludes about a rule node, which
    contains variables, and the second reads an answer that only exists because
    the machinery was asked to match.
    """
    g = m.g
    r, w, sub = g.var("?r"), g.var("?wanted"), g.var("?sub")

    # Ask every rule whether it could produce this goal. Asking everything is
    # what recall exists to narrow (§19); doing it exhaustively here is the
    # deliberate-reasoning setting, not a shortcut.
    m.rules.rule(
        IMPLIES,
        [Member(PLUS, g.rel(m.GOAL, w)), Member(PLUS, g.rel(m.RULE, r))],
        [Member(PLUS, g.rel(m.FIT, r, w))],
        "ask-fit",
    )
    # What fits, becomes subgoals. `?sub` arrives instantiated, which is the
    # whole reason the request answers with `need` rather than with a binding.
    m.rules.rule(
        IMPLIES,
        [Member(PLUS, g.rel(m.FITS, r, w)), Member(PLUS, g.rel(m.NEED, r, w, sub))],
        [Member(PLUS, g.rel(m.GOAL, sub))],
        "expand",
    )


def _goals(m: Machine) -> Set[str]:
    out: Set[str] = set()
    for mo in m.chain.moments:
        for e in mo.delta:
            if e.sign == PLUS and m.g.relation_of(e.proposition) is m.GOAL:
                (what,) = m.g.members(e.proposition)
                out.add(m.g.show(what))
    return out


def _phase() -> Set[str]:
    m = Machine()
    kb = load(m, CORPUS)
    m.gate.write(m.focus, m.g.rel(m.GOAL, kb.term(GOAL)), PLUS, mention=True)
    m.run(limit=80)
    return _goals(m)


def _rules(drop: Tuple[str, ...] = ()) -> Tuple[Set[str], int]:
    m = Machine()
    kb = load(m, CORPUS)
    m.reify_all()
    _rule_level(m)
    if drop:
        m.rules.rules = [r for r in m.rules.rules if r.name not in drop]
    # The phase would expand the same goals in parallel and the two would agree
    # by construction rather than by measurement, so it is turned off.
    m.expansion_budget = 0
    m.gate.write(m.focus, m.g.rel(m.GOAL, kb.term(GOAL)), PLUS, mention=True)
    m.run(limit=200)
    return _goals(m), m.gate.writes


def run() -> int:
    by_phase = _phase()
    by_rules, writes = _rules()

    print("backward reading -- the phase against rules over a match request")
    print(f"  goal            {GOAL}")
    print(f"  by the phase    {len(by_phase)} goals")
    print(f"  by rules        {len(by_rules)} goals, {writes} writes")
    print()

    missing = sorted(by_phase - by_rules)
    extra = sorted(by_rules - by_phase)
    for x in sorted(by_phase & by_rules):
        print(f"    both      {x}")
    for x in missing:
        print(f"    PHASE ONLY  {x}")
    for x in extra:
        print(f"    RULES ONLY  {x}")

    print()
    if not missing and not extra:
        print("  ok    the rules reach exactly the goals the phase does")

    # Could it have disagreed? Three checks that reported success in this project
    # turned out to be unable to fail, so agreement is not reported without it.
    print()
    print("  can this comparison fail? -- one rule deleted at a time")
    blind: List[str] = []
    for name in ("ask-fit", "expand"):
        got, _ = _rules((name,))
        diff = len(by_phase ^ got)
        print(f"    {name:10} {diff:>3} goals differ" + ("" if diff else "   <-- BLIND"))
        if not diff:
            blind.append(name)

    print()
    print(f"{len(missing)} missing, {len(extra)} extra, {len(blind)} blind")
    return len(missing) + len(extra) + len(blind)


if __name__ == "__main__":
    raise SystemExit(1 if run() else 0)
