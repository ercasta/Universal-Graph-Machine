"""Learning from a prediction that failed.

    python -m ugm.learning.surprise

A `causes` rule deposits what it predicts -- `expects(p, +)` -- and four bundled
rules turn a contradicted prediction into `deviates(p)`. `ugm.dungeon` runs that
apparatus 392 times and finds nothing, because a game's rules are never wrong.
This is the other case: a world where the model IS wrong, which is the only kind
where the apparatus can pay.

## The whole loop, on the record

```
fact +heating(k1)     fact +contains(k1, water)
fact +heating(k2)     fact +contains(k2, sand)
rule <boils> = causes( { +heating(?k) }, { +boiling(?k) } )
say world: -boiling(k2)
```

```
why deviates(boiling(k2))?
  +deviates(boiling(k2)) @M2, licensed by applied(<deviation-+-contradicted>)
    because +expects(boiling(k2), +) @M1, licensed by applied(<boils>)
    because -boiling(k2) @M2, licensed by applied(<trust>)
    because +says(world, boiling(k2), -) @M0, licensed by applied(<intake>)
    because +arrived(world, boiling(k2), -) @M0, via world
```

Everything a learner needs is in that trail and nothing had to be instrumented
to get it:

    which prediction failed      `deviates(p)`
    which rule made it           the `expects` entry's licence, `applied(<R>)`
    about what                   the members of `p`
    and what did NOT fail        the same relation, holding, about something else

## What is learned, and what is not

**A discriminator, not a repair.** Abstract each fact about the failing subject
by replacing the subject with a hole, do the same for the subjects the rule got
right, and take the difference:

    k2 (failed)      heating(_), contains(_, sand)
    k1 (succeeded)   heating(_), contains(_, water)
    difference       contains(_, sand)

`heating(_)` is shared by a success and a failure, so it discriminates nothing.
That negative half is the check worth having: a learner that proposes the
premise the rule already has is proposing noise.

**It declines when it cannot know.** With one case and no contrast there is no
discriminator, and the honest output is nothing. *One mapping across premise and
conclusion is the difference between learning and noise*, and with a single
example there is no mapping to be had.

**And what it emits is a HYPOTHESIS, not a rule.** The knowledge is the author's;
what the agent may propose is a candidate, wrapped, so it cannot fight anything
authored. Promoting it is a separate act by something that can be held
responsible for it.

## What this is not

**Not the learner.** It is the smallest honest end-to-end: surprise detected,
localised to a rule, contrasted against a success, and reported as a candidate.
No anti-unification over many episodes, no calibration, no adoption. Those all
need this to work first, and this is the check that it does.
"""

from typing import Dict, List, Optional, Set, Tuple

from ..core.machine import Machine
from ..core.text import load

WORLD = """
fact +heating(k1)
fact +contains(k1, water)
fact +heating(k2)
fact +contains(k2, sand)

rule <boils> = causes( { +heating(?k) }, { +boiling(?k) } )
rule <trust> = implies( { +says(world, ?p, minus) }, { -?p } )
"""

TOLD = "say world: -boiling(k2)\n"

# One kettle only, so nothing succeeded to contrast against.
LONELY = """
fact +heating(k2)
fact +contains(k2, sand)

rule <boils> = causes( { +heating(?k) }, { +boiling(?k) } )
rule <trust> = implies( { +says(world, ?p, minus) }, { -?p } )
say world: -boiling(k2)
"""

# Both kettles hold sand and only one failed, so the feature that looks like a
# discriminator is shared. There is nothing to learn and saying so is the answer.
MUDDLED = """
fact +heating(k1)
fact +contains(k1, sand)
fact +heating(k2)
fact +contains(k2, sand)

rule <boils> = causes( { +heating(?k) }, { +boiling(?k) } )
rule <trust> = implies( { +says(world, ?p, minus) }, { -?p } )
say world: -boiling(k2)
"""


class Found(object):
    """What one failed prediction taught, or did not."""

    def __init__(self, proposition: str, rule: Optional[str],
                 subject: str, discriminators: List[str],
                 shared: List[str], contrasts: List[str]) -> None:
        self.proposition = proposition
        self.rule = rule
        self.subject = subject
        self.discriminators = discriminators
        self.shared = shared
        self.contrasts = contrasts

    @property
    def hypothesis(self) -> Optional[str]:
        """Ground, and wrapped. A fact may not contain a variable, so the
        candidate names the distinguishing ARGUMENT rather than a pattern -- and
        it is `likely(...)` so it can never fight anything authored."""
        if self.rule is None or len(self.discriminators) != 1:
            return None
        return f"fact +likely(prevents({self.discriminators[0]}, <{self.rule}>))"


def _state(m: Machine) -> Dict[int, object]:
    """The newest claim about each proposition, which is all a contrast needs."""
    out: Dict[int, object] = {}
    for mo in m.chain.moments:
        for e in mo.delta:
            out[e.proposition] = e
    return out


def features(m: Machine, kb, x, lift: bool = False,
             state: Optional[Dict[int, object]] = None) -> Dict[str, str]:
    """Every current claim mentioning `x`, abstracted: `x` is replaced by a
    hole, so `contains(k2, sand)` and `contains(k1, sand)` are the same feature
    and `contains(k1, water)` is not.

    With `lift`, each feature is ALSO offered with one argument replaced by a
    kind the world model gives it -- `contains(_, :solid)` beside
    `contains(_, sand)`. One argument at a time, so nothing combinatorial.

    ⚠ Module level rather than a closure inside `learn`, because the held-out
    test has to ask *does this lesson cover that case* with the SAME function
    that produced the lesson. A second copy would degrade with the first and
    agree with it while both were wrong.
    """
    g = m.g
    state = _state(m) if state is None else state
    IS_A = kb.atoms.get("is_a")

    def kinds_of(n) -> List[int]:
        """What the world model says this is. Read off the state, so a corpus
        rule making `is_a` transitive widens the lift with no change here."""
        if IS_A is None:
            return []
        return [g.member(e.proposition, 1) for e in state.values()
                if g.relation_of(e.proposition) is IS_A and e.sign == "+"
                and len(g.members(e.proposition)) == 2
                and g.member(e.proposition, 0) is n]

    out: Dict[str, str] = {}
    for e in state.values():
        members = g.members(e.proposition)
        if x not in members:
            continue
        rel = g.relation_of(e.proposition)
        if rel is None:
            continue
        shown = ", ".join("_" if mm is x else g.show(mm) for mm in members)
        out[f"{g.show(rel)}({shown})"] = e.sign
        if not lift:
            continue
        for k, mm in enumerate(members):
            if mm is x:
                continue
            for kind in kinds_of(mm):
                parts = ["_" if q is x else (f":{g.show(kind)}" if jj == k
                                             else g.show(q))
                         for jj, q in enumerate(members)]
                out[f"{g.show(rel)}({', '.join(parts)})"] = e.sign
    return out


def learn(m: Machine, kb, lift: bool = False) -> List[Found]:
    """What each failed prediction taught, one contrast at a time.

    `lift` abstracts features through the world model. Without it a second
    failure teaches a second VALUE and nothing transfers -- measured: sand and
    gravel share no raw discriminator at all. The ontology is what makes a
    lesson about a KIND rather than about a thing.
    """
    g = m.g
    DEVIATES = kb.atoms.get("deviates") or g.atom("deviates")
    state = _state(m)
    about = lambda n: features(m, kb, n, lift=lift, state=state)

    out: List[Found] = []
    for e in list(state.values()):
        if g.relation_of(e.proposition) is not DEVIATES or e.sign != "+":
            continue
        failed = g.member(e.proposition, 0)
        rel = g.relation_of(failed)

        # which rule predicted it -- the `expects` entry's own licence
        rule = None
        for x in state.values():
            if (g.relation_of(x.proposition) is m.EXPECTS
                    and g.member(x.proposition, 0) is failed
                    and x.licence is not None
                    and g.relation_of(x.licence) is m.APPLIED):
                rule = g.show(g.member(x.licence, 0)).strip("<>")

        members = g.members(failed)
        if not members:
            continue
        subject = members[0]

        # ...and what the same rule got RIGHT: the same relation, holding, about
        # something else. Without a success there is no contrast and no lesson.
        others = [g.member(p, 0) for p, x in state.items()
                  if g.relation_of(p) is rel and x.sign == "+"
                  and g.members(p) and g.member(p, 0) is not subject]

        mine = {k for k, sg in about(subject).items() if sg == "+"}
        theirs: Set[str] = set()
        for o in others:
            theirs |= {k for k, sg in about(o).items() if sg == "+"}
        # the predicted relation itself is not evidence about why it failed
        drop = lambda ks: {k for k in ks if not k.startswith(g.show(rel) + "(")}
        mine, theirs = drop(mine), drop(theirs)

        # ⚠⚠⚠ **A difference against the empty set is not a difference.** With
        # no success to contrast against, `mine - theirs` is all of `mine`, so
        # every fact about the failure reads as an explanation of it -- which is
        # precisely the noise this is supposed to refuse. The one-case fixture
        # caught it; without that check the learner would have looked confident
        # exactly where it knew least.
        if not others:
            mine = set()

        out.append(Found(
            proposition=g.show(failed),
            rule=rule,
            subject=g.show(subject),
            discriminators=sorted(mine - theirs),
            shared=sorted(mine & theirs),
            contrasts=sorted(g.show(o) for o in others),
        ))
    return out


def common(founds: List[Found]) -> List[str]:
    """What discriminates EVERY failure, not merely one.

    A feature that explains one failure and not another is not the lesson --
    it is the value that happened to be there. Intersecting is what turns
    several contrasts into one claim, and it is also what makes the answer
    empty when the failures have nothing in common, which is the honest result
    rather than a shortfall."""
    live = [f for f in founds if f.discriminators]
    if not live:
        return []
    out = set(live[0].discriminators)
    for f in live[1:]:
        out &= set(f.discriminators)
    return sorted(out)


def _run(src: str) -> Tuple[Machine, object, List[Found]]:
    m = Machine()
    kb = load(m, src, None, None)
    m.run(limit=400)
    return m, kb, learn(m, kb)


def main() -> int:
    import sys
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

    m, kb, found = _run(WORLD + TOLD)
    _, _, lonely = _run(LONELY)
    _, _, muddled = _run(MUDDLED)

    print("  one kettle boiled and one did not:\n")
    for f in found:
        print(f"    failed        {f.proposition}")
        print(f"    predicted by  <{f.rule}>")
        print(f"    contrasted with {f.contrasts}")
        print(f"    shared        {f.shared}")
        print(f"    DISCRIMINATOR {f.discriminators}")
        print(f"    hypothesis    {f.hypothesis}")
    print()

    gate("SURPRISE IS DETECTED: the contradicted prediction became a deviation, "
         "and the one that held did not",
         [f.proposition for f in found] == ["boiling(k2)"])
    gate("...and the trail names the RULE that predicted it, so a failure is "
         "localised without anything being instrumented to do it",
         found and found[0].rule == "boils")
    gate("THE DISCRIMINATOR IS FOUND: what is true of the failure and not of "
         f"the success ({found[0].discriminators if found else None})",
         found and found[0].discriminators == ["contains(_, sand)"])
    gate("...and the SHARED feature is not proposed: `heating(_)` holds of both, "
         "so it discriminates nothing -- a learner that offered the premise the "
         f"rule already has would be offering noise ({found[0].shared})",
         found and found[0].shared == ["heating(_)"])

    gate("IT DECLINES WITH ONE CASE: nothing succeeded, so there is no contrast "
         "and no lesson -- and the honest output is no candidate rather than a "
         f"guess ({lonely[0].discriminators if lonely else None})",
         lonely and lonely[0].discriminators == []
         and lonely[0].hypothesis is None)
    gate("IT DECLINES WHEN THE FEATURE IS SHARED: both kettles hold sand and "
         "only one failed, so the thing that looks like an explanation explains "
         f"nothing ({muddled[0].discriminators if muddled else None})",
         muddled and muddled[0].discriminators == []
         and muddled[0].hypothesis is None)

    gate("WHAT IT EMITS IS A HYPOTHESIS: ground, because a fact may not contain "
         "a variable, and wrapped, so it cannot fight anything the author wrote",
         found and found[0].hypothesis is not None
         and found[0].hypothesis.startswith("fact +likely(prevents(")
         and "<boils>" in found[0].hypothesis)

    print(f"\n{ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
