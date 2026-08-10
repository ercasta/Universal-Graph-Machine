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
    # Two subgoals sharing a variable, and a world where checking them
    # independently gets it wrong: `tap(?t)` is satisfied by `sink`, and
    # `under(kettle, ?t)` by `drain`. §18's failure, made reachable.
    "rule <fill>  = implies( { +tap(?t), +under(kettle, ?t) }, { +water(kettle) } )",
    "fact +tap(sink)",
    "fact +tap(drain)",
    "fact +under(kettle, drain)",
    "fact +leaf(green)",
    "",
])
GOAL = "tea(kettle, green)"

# The vocabulary both readers write. `fit`, `fits`, `need`, `check` and `unfit`
# are the request traffic and exist only on the rule side, so they are not
# compared -- what must agree is the plan the two arrive at.
#
# `blocked` is deliberately NOT here, and that is a finding rather than a
# convenience; see `_blocked_is_not_a_fact` below.
SHARED = ("GOAL", "EXPANDS", "SUBGOAL", "BINDS", "ACHIEVED")


def _rule_level(m: Machine) -> None:
    """Backward reading, entire, as five rules over two requests.

    None of them could be written before this session: each concludes about a
    rule node, which contains variables, and three read answers that exist only
    because the machinery was asked to match.

    Note what a rule turns out to be able to build. `plan(?r, ?w)` is constructed
    by **substitution into a consequent**, and substitution interns -- so the same
    rule expanding the same goal names the same plan, which is what a plan is.
    Minting fresh nodes is not needed and would be wrong.
    """
    g = m.g
    r, w, sub = g.var("?r"), g.var("?wanted"), g.var("?sub")
    plan = g.rel(m.PLAN, r, w)

    # Ask every rule whether it could produce this goal. Asking everything is
    # what recall exists to narrow (§19); doing it exhaustively here is the
    # deliberate-reasoning setting, not a shortcut.
    m.rules.rule(
        IMPLIES,
        [Member(PLUS, g.rel(m.GOAL, w)), Member(PLUS, g.rel(m.RULE, r))],
        [Member(PLUS, g.rel(m.FIT, r, w))],
        "ask-fit",
    )
    # A rule that fits is a plan. R7 for the search's own working state.
    m.rules.rule(
        IMPLIES,
        [Member(PLUS, g.rel(m.FITS, r, w))],
        [Member(PLUS, g.rel(m.EXPANDS, plan, w, r))],
        "plan",
    )
    # What it needs becomes a subgoal of that plan. `?sub` arrives instantiated,
    # which is the whole reason the request answers with `need` rather than with
    # a binding.
    m.rules.rule(
        IMPLIES,
        [Member(PLUS, g.rel(m.FITS, r, w)), Member(PLUS, g.rel(m.NEED, r, w, sub))],
        [Member(PLUS, g.rel(m.SUBGOAL, plan, sub)), Member(PLUS, g.rel(m.GOAL, sub))],
        "expand",
    )
    # Before expanding a subgoal, ask whether the world already answers it --
    # under this plan's bindings, so that siblings agree (§18).
    m.rules.rule(
        IMPLIES,
        [Member(PLUS, g.rel(m.SUBGOAL, plan, sub))],
        [Member(PLUS, g.rel(m.CHECK, plan, sub))],
        "ask-check",
    )
    # There is no sixth rule, and the missing one is the finding. See
    # `_blocked_is_not_a_fact`.


def _blocked_is_not_a_fact() -> str:
    """Why backward reading's last verdict cannot be a rule.

    The natural sixth rule is

        implies( {+goal(?w), +unfit(?r, ?w)}, {+blocked(?w)} )

    and it is wrong, because it fires when **some** rule does not fit. What
    `blocked` claims is that **no** rule does -- a statement about the absence of
    any fitting rule, which is an aggregate over a *finished* search.

    Positive rules cannot say it. Nor can a `-` antecedent member: §9's `-` means
    *an entry says this does not hold*, and *no entry* means inherit. Neither is
    *for no `?r`*.

    That is not a missing feature. It is §13 and §19 arriving at the last phase:

    > **Bounded expansion returns a result AND a state.** `blocked` is the state.

    A state is what the searcher reports about itself when it stops, and nothing
    that stopped is a fact about the world. So `blocked` stays with whatever runs
    the search -- or becomes a request answered once the search settles, which is
    the same thing said politely.
    """
    return "blocked is a state, not a fact"


def _facts(m: Machine) -> Set[str]:
    """Every machinery fact both readers are supposed to produce.

    An earlier version compared only the goals reached, and three of the five
    rules were unkillable as a result -- the plan, the satisfaction check and the
    blocking rule all write facts the comparison never looked at. A gate is only
    as strong as what it reads.
    """
    wanted = {getattr(m, name) for name in SHARED}
    out: Set[str] = set()
    for mo in m.chain.moments:
        for e in mo.delta:
            if e.sign == PLUS and m.g.relation_of(e.proposition) in wanted:
                out.add(m.g.show(e.proposition))
    return out


def _phase() -> Set[str]:
    m = Machine()
    kb = load(m, CORPUS)
    m.gate.write(m.focus, m.g.rel(m.GOAL, kb.term(GOAL)), PLUS, mention=True)
    m.run(limit=400)
    return _facts(m)


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
    m.run(limit=400)
    return _facts(m), m.gate.writes


def run() -> int:
    by_phase = _phase()
    by_rules, writes = _rules()

    print("backward reading -- the phase against rules over a match request")
    print(f"  goal            {GOAL}")
    print(f"  by the phase    {len(by_phase)} facts")
    print(f"  by rules        {len(by_rules)} facts, {writes} writes")
    print()

    missing = sorted(by_phase - by_rules)
    extra = sorted(by_rules - by_phase)
    print(f"    agreed      {len(by_phase & by_rules)}")
    for x in missing:
        print(f"    PHASE ONLY  {x[:88]}")
    for x in extra:
        print(f"    RULES ONLY  {x[:88]}")

    print()
    if not missing and not extra:
        print("  ok    the rules produce exactly what the phase does")
    elif not missing:
        # The rules reaching MORE is not a disagreement about backward reading.
        # The phase runs before recall/match/arbitrate and returns early, so
        # while any goal is unexpanded no ordinary rule can apply: backward
        # search monopolises the loop. `water(kettle)` is derivable forwards
        # from the corpus, and the phase judges it unsatisfied because it has
        # not let anything derive it yet.
        print("  ok    the rules produce everything the phase does, and more:")
        print("        the phase orders itself ahead of forward reasoning and")
        print("        starves it, so a goal that IS satisfiable reads as not.")

    # Could it have disagreed? Three checks that reported success in this project
    # turned out to be unable to fail, so agreement is not reported without it.
    print()
    print("  can this comparison fail? -- one rule deleted at a time")
    blind: List[str] = []
    for name in ("ask-fit", "plan", "expand", "ask-check"):
        got, _ = _rules((name,))
        diff = len(by_phase ^ got)
        print(f"    {name:10} {diff:>3} facts differ" + ("" if diff else "   <-- BLIND"))
        if not diff:
            blind.append(name)

    print()
    print(f"{len(missing)} missing, {len(extra)} extra, {len(blind)} blind")
    return len(missing) + len(blind)


if __name__ == "__main__":
    raise SystemExit(1 if run() else 0)
