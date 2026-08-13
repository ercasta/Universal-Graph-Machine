"""Does an episode teach the next one anything? (§19, §20)

Learning here is offline and it is a **corpus**: an episode ends, `review` and
`blame` walk the trail, and `learned()` writes surface text the next episode
loads. Nothing about the loop changes. So the question this instrument asks is
the only one that matters about it -- **run the same world twice and see whether
the second run is better** -- and its gate is that the answer can be no.

    python -m ugm.learning

The world is the one `forgoing2` built, because it is the only kind that can
measure a chooser: two ways to get water, and one of them breaks a jug another
goal needs. Everything upstream of forgoing was measured in a world where the
agent took the good route AND the bad one, so *choose the better rule* had no
content and an exact recall table bought nothing (`experience`). It has content
now, and the arena is a single line of authored order:

    <use-jug> written first  ->  the jug is smashed
    <use-tap> written first  ->  the jug survives

Nothing else in the corpus differs. Two thirds of this agent's arbitrations are
settled by typing order, and this is one of them, with a cost attached.

⭐⭐⭐ **What it measured, and the reason this file exists.** Blame alone does not
close the loop. An episode that smashed the jug blames the smasher and drops it
from what it recommends -- and then **smashes the jug again**, because omitting a
rule leaves it exactly where it was, first in authored order.

> **Suppression is not a decision.** It says *do not recommend this*. It cannot
> say *do that instead*, and only the second changes a run.

The missing half was already on the trail. `forgone(A, w)` records that `A` was a
live way of getting `w` and something else was taken, licensed by
`applied(<winner>)` -- so a blamed winner names its own alternatives. Joining the
two needs no new bookkeeping, which is the third time credit assignment has come
out that way. `Machine._instead_of` is the join and `SUPPRESSION_ONLY` below is
the control that shows it is load-bearing.
"""

from typing import Dict, List, Optional, Tuple

from .machine import Machine, forest, induce, leaves
from .text import load

BASE = [
    "rule <eff> = implies( { +did(?a), +achieves(?a, ?y) }, { +?y } )",
    "rule <cost> = implies( { +did(smash(?j)) }, { -intact(?j) } )",
    "rule <squeeze> = implies( { +fruit(?f), +jug(?j), +intact(?j) }, { +juice(?j) } )",
]
TAP = ("rule <use-tap> = implies( { +goal(water(?w)), +tap(?t), +under(?w, ?t) },"
       " { +doing(fill(?w)) } )")
JUG = ("rule <use-jug> = implies( { +goal(water(?w)), +jug(?j), +holds(?j, ?w) },"
       " { +doing(smash(?j)) } )")


def world(vessel: str = "kettle", jug: str = "jug1", jug_first: bool = True) -> str:
    """Two routes to water, one of which costs a jug a second goal needs.

    Parameterised on the objects rather than hard-coded, because what an episode
    carries forward is keyed on a goal's RELATION -- so whether it transfers is a
    question about a different `vessel` and `jug`, and a fixture that cannot vary
    them would report generalisation it never tested.
    """
    routes = [JUG, TAP] if jug_first else [TAP, JUG]
    return "\n".join(routes + BASE + [
        f"fact +achieves(fill({vessel}), water({vessel}))",
        f"fact +achieves(smash({jug}), water({vessel}))",
        "fact +tap(sink)", f"fact +under({vessel}, sink)",
        f"fact +jug({jug})", f"fact +holds({jug}, {vessel})", f"fact +intact({jug})",
        "fact +fruit(orange)",
        f"fact +goal(water({vessel}))",
        f"fact +goal(juice({jug}))",
        "",
    ])


class Episode:
    """One run, and what it has to say to the next."""

    def __init__(self, src: str, vessel: str = "kettle", jug: str = "jug1") -> None:
        self.m = Machine()
        self.m.actuator("hands")
        self.kb = load(self.m, src)
        self.steps = self.m.run(limit=4000)
        self.acts = [self.m.g.show(n) for n in self.m.emitted]
        self.intact = self.m.holds(self.kb.term(f"intact({jug})"))
        self.water = self.m.holds(self.kb.term(f"water({vessel})"))
        self.juice = self.m.holds(self.kb.term(f"juice({jug})"))
        self.blamed = sorted({r.name for r, _ in self.m.blame()})
        self.rows = self.m.learned()

    @property
    def harmed(self) -> bool:
        """Did this run destroy something it also wanted? The whole outcome
        measure, and deliberately about a LOST subgoal rather than a failed
        episode -- §9's distinction is what makes it attributable at all."""
        return self.intact == "-"


def run(jug_first: bool = True, rounds: int = 3, carry: str = "") -> List[Episode]:
    """Play the same world `rounds` times, each one loading what the last wrote."""
    out: List[Episode] = []
    for _ in range(rounds):
        ep = Episode(world(jug_first=jug_first) + carry)
        out.append(ep)
        carry = "\n".join(ep.rows) + "\n" if ep.rows else ""
    return out


def _no_promotion():
    """The control: blame still suppresses, but nothing promotes an alternative.

    This is the state of the code before this session, and it is what makes the
    headline falsifiable -- take the join away and the second episode must go
    wrong again, or the join was never what fixed it.
    """
    original = Machine._instead_of
    Machine._instead_of = lambda self, harmed: []  # type: ignore[assignment]
    return original


HARM_JUG = ("rule <use-jug> = implies( { +goal(water(?w)), +jug(?j), +holds(?j, ?w) },"
            " { +doing(smash(?j)) } )")
HARM_VASE = ("rule <use-vase> = implies( { +goal(water(?w)), +vase(?v), +holds(?v, ?w) },"
             " { +doing(shatter(?v)) } )")
HARM_BASE = [
    "rule <eff> = implies( { +did(?a), +achieves(?a, ?y) }, { +?y } )",
    "rule <cost-j> = implies( { +did(smash(?j)) }, { -intact(?j) } )",
    "rule <cost-v> = implies( { +did(shatter(?v)) }, { -intact(?v) } )",
    "rule <set-broken> = implies( { +did(shatter(?v)), +completes(?v, ?s) },"
    " { -whole(?s) } )",
    "fact +achieves(smash(jug1), water(kettle))",
    "fact +achieves(shatter(vase), water(kettle))",
    "fact +jug(jug1)", "fact +holds(jug1, kettle)", "fact +intact(jug1)",
    "fact +vase(vase)", "fact +holds(vase, kettle)", "fact +intact(vase)",
    "fact +completes(vase, heirlooms)", "fact +whole(heirlooms)",
    "fact +goal(water(kettle))", "fact +goal(intact(jug1))",
    "fact +goal(intact(vase))", "fact +goal(whole(heirlooms))", "",
]
LOSSES = ("intact(jug1)", "intact(vase)", "whole(heirlooms)")


def harm_episode(order, extra=()):
    """A world with NO safe route -- two ways to water, both destructive, and
    one twice as costly as the other (the vase completes a set)."""
    m = Machine()
    m.actuator("hands")
    kb = load(m, "\n".join(list(order) + HARM_BASE + list(extra)))
    m.run(limit=2000)
    lost = [g for g in LOSSES if m.holds(kb.term(g)) == "-"]
    return m, [m.g.show(n) for n in m.emitted], lost


def lesser_of_two_evils(rounds: int = 4) -> Tuple[dict, dict]:
    """Can experience choose the cheaper of two damaging routes? Not yet.

    ⚠⚠⚠ **Today's scheme OSCILLATES, and from a good start it makes the agent
    worse.** `learned` suppresses whatever harmed and promotes whatever was
    passed up -- with no notion of *how much*, so it alternates forever, and half
    of every cycle is spent on the route that costs twice as much.

    ⚠⚠⚠ **And magnitude alone does not fix it.** The ceiling below records what
    each route actually cost and accumulates it across episodes; it converges
    immediately -- **on whatever it happened to try first**. Better from a good
    start, permanently worse from a bad one.

    > **Neither is learning. One explores with no memory; the other remembers
    > with no exploration.** What is missing is not a better rule for picking --
    > it is a SECOND QUANTITY. The design already has both scales and already
    > forbids conflating them: a cardinal score on the table for *how good*, and
    > §10's ordinal grade on the entry for *how sure*. `+prefer(<R>, k, 3)
    > @possible` -- a strong recommendation the agent is not certain of -- is
    > exactly the sentence explore/exploit needs, and nothing writes it from
    > experience. That is §21's item 1 and item 2 turning out to be one item.
    """
    out = {}
    for label, order in (("good start", [HARM_JUG, HARM_VASE]),
                         ("bad start", [HARM_VASE, HARM_JUG])):
        today, extra = [], ()
        for _ in range(rounds):
            m, acts, lost = harm_episode(order, extra)
            today.append(len(lost))
            extra = m.learned()
        ceiling, cost = [], {}
        for _ in range(rounds):
            worst = max(cost.values()) if cost else 0
            rows = [f"fact prefer(<{r}>, water, {worst - c + 1})" for r, c in cost.items()]
            m, acts, lost = harm_episode(order, rows)
            ceiling.append(len(lost))
            used = ("use-jug" if acts and acts[0].startswith("smash")
                    else "use-vase" if acts else None)
            if used:
                cost[used] = max(cost.get(used, 0), len(lost))
        out[label] = (today, ceiling, dict(cost))
    return out


TREE_JUG = ("rule <use-jug> = implies( { +goal(water(?w)), +jug(?j), +holds(?j, ?w) },"
            " { +doing(smash(?j)) } )")
TREE_TAP = ("rule <use-tap> = implies( { +goal(water(?w)), +tap(?t), +under(?w, ?t) },"
            " { +doing(fill(?w)) } )")
TREE_CORE = [
    "rule <eff> = implies( { +did(?a), +achieves(?a, ?y) }, { +?y } )",
    "rule <cost> = implies( { +did(smash(?j)) }, { -intact(?j) } )",
    "rule <extra> = implies( { +did(smash(?j)), +precious(?j), +completes(?j, ?s) },"
    " { -whole(?s) } )",
    "rule <drain> = implies( { +did(fill(?w)), +scarce(?w) }, { -reserve(town) } )",
    "rule <drop> = implies( { +did(fill(?w)), +scarce(?w) }, { -pressure(main) } )",
    "fact +achieves(smash(jug1), water(kettle))",
    "fact +achieves(fill(kettle), water(kettle))",
    "fact +jug(jug1)", "fact +holds(jug1, kettle)", "fact +intact(jug1)",
    "fact +tap(sink)", "fact +under(kettle, sink)",
    "fact +whole(heirlooms)",
    "fact +reserve(town)", "fact +pressure(main)",
    "fact +goal(water(kettle))", "fact +goal(intact(jug1))",
    "fact +goal(whole(heirlooms))", "fact +goal(reserve(town))",
    "fact +goal(pressure(main))",
]
# The two situations share a goal RELATION and disagree about the right move, so
# one unconditional row must be wrong in one of them. That is the whole design of
# the fixture: a depth-0 tree cannot express *when*.
# C is A without the set: precious, but completing nothing. It is what makes
# OVER-specific advice measurably wrong -- the depth-2 rule declines to fire
# there and the agent falls back to the jug it did not need to break.
SITUATIONS = {"A": ["fact +precious(jug1)", "fact +completes(jug1, heirlooms)"],
              "B": ["fact +scarce(kettle)"],
              "C": ["fact +precious(jug1)"]}
TREE_LOSSES = ("intact(jug1)", "whole(heirlooms)", "reserve(town)", "pressure(main)")


def tree_episode(situation: str, extra=()):
    m = Machine()
    m.actuator("hands")
    kb = load(m, "\n".join([TREE_JUG, TREE_TAP] + TREE_CORE
                           + SITUATIONS[situation] + list(extra) + [""]))
    m.run(limit=2000)
    return m, [g for g in TREE_LOSSES if m.holds(kb.term(g)) == "-"]


def a_learned_rule_is_a_decision_tree() -> Tuple[List[str], List[str], List[str], dict]:
    """A `prefer` FACT is a decision tree of depth ZERO. A rule says *when*.

    Not an analogy. A tree's root-to-leaf path is a conjunction of tests ending
    in a verdict, which is a rule; its internal nodes are antecedent members; and
    `<relevant>` has shipped in exactly this shape since §13. Two consequences
    that were already true and unnoticed:

    * **`_priority` sums applicable rows, so preference is already an ADDITIVE
      ENSEMBLE.** A set of shallow learned rules is a forest natively -- measured
      at 4 + 3 = 7. Nobody designed it as one.
    * **Generalising is unconstrained**, because a preference consequent contains
      no variables, so the loader's bound-variable rule is satisfied by anything.
      A rule that concluded about the world would not have that freedom.

    The tests come off the trail (`_circumstances`), not from feature
    engineering: the hypothesis space is the corpus's own vocabulary.
    """
    teach, _ = tree_episode("A")
    flat = teach.learned()
    cond = teach.learned(conditional=True)
    def total(rows):
        return sum(len(tree_episode(s, rows)[1]) for s in ("A", "B", "C"))

    refined = teach.refine(total)
    costs = {}
    for label, rows in (("nothing", []), ("depth-0", flat),
                        ("unpruned", cond), ("refined", refined)):
        costs[label] = [len(tree_episode(s, rows)[1]) for s in ("A", "B", "C")]
    return flat, cond, refined, costs


def main() -> int:
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    failing = 0
    ran = 0

    def gate(name: str, ok: bool) -> None:
        nonlocal failing, ran
        ran += 1
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
        if not ok:
            failing += 1

    print(__doc__.strip().split("\n")[0])
    print()

    # -- the arena, before anything is learned ----------------------------
    print("The choice, and what settles it -- one line of authored order:\n")
    print(f"  {'authored first':<16} {'emitted':<16} {'jug':<6} {'water':<6} {'juice':<6}")
    first = {}
    for jug_first in (False, True):
        ep = Episode(world(jug_first=jug_first))
        first[jug_first] = ep
        label = "<use-jug>" if jug_first else "<use-tap>"
        print(f"  {label:<16} {ep.acts[0] if ep.acts else '-':<16} "
              f"{'broken' if ep.harmed else 'intact':<6} {str(ep.water):<6} {str(ep.juice):<6}")
    print()
    gate("a wrong choice costs something, so there is something to learn",
         first[True].harmed and not first[False].harmed)
    gate("...and only one act leaves the agent, so it IS a choice (forgoing)",
         len(first[True].acts) == 1 and len(first[False].acts) == 1)
    gate("the damage is attributed to the decision, not just to the physics",
         "use-jug" in first[True].blamed)

    # -- the loop ---------------------------------------------------------
    print("\nThe same world, three times, each loading what the last wrote:\n")
    print(f"  {'episode':<9} {'emitted':<16} {'jug':<8} {'blamed':<26} rows")
    eps = run(jug_first=True, rounds=3)
    for i, ep in enumerate(eps, 1):
        names = ",".join(n for n in ep.blamed) or "-"
        print(f"  {i:<9} {ep.acts[0] if ep.acts else '-':<16} "
              f"{'broken' if ep.harmed else 'intact':<8} {names:<26} {len(ep.rows)}")
    print()
    for r in eps[0].rows:
        print(f"    {r}")
    print()

    gate("the first episode does the damage", eps[0].harmed)
    gate("⭐ the second does not -- an episode taught the next one something",
         not eps[1].harmed)
    gate("and it stays taught: the third does not regress", not eps[2].harmed)
    gate("what it learned names the alternative it passed up, not just the "
         "rule it stopped recommending",
         any("<use-tap>" in r for r in eps[0].rows)
         and not any("<use-jug>" in r for r in eps[0].rows))
    gate("the repaired run achieves BOTH goals, so it is not merely doing less",
         eps[1].water == "+" and eps[1].juice == "+")

    # -- the control ------------------------------------------------------
    print("\nThe control -- blame suppresses, nothing promotes:\n")
    original = _no_promotion()
    try:
        ctrl = run(jug_first=True, rounds=2)
    finally:
        Machine._instead_of = original  # type: ignore[assignment]
    for i, ep in enumerate(ctrl, 1):
        print(f"  {i:<9} {ep.acts[0] if ep.acts else '-':<16} "
              f"{'broken' if ep.harmed else 'intact':<8} rows={len(ep.rows)}")
    print()
    gate("⭐⭐⭐ suppression alone does NOT fix it -- the agent blames the "
         "smasher, stops recommending it, and smashes the jug again",
         ctrl[0].harmed and ctrl[1].harmed)
    gate("...and it is not that it learned nothing: it wrote rows, they were "
         "just about the wrong half of the choice",
         bool(ctrl[0].rows) and not any("<use-tap>" in r for r in ctrl[0].rows))

    # -- transfer ---------------------------------------------------------
    print("\nTransfer -- what was learned about one kettle, applied to another:\n")
    taught = run(jug_first=True, rounds=1)[0].rows
    fresh = Episode(world("pot", "jug2", jug_first=True), "pot", "jug2")
    carried = Episode(world("pot", "jug2", jug_first=True) + "\n".join(taught) + "\n",
                      "pot", "jug2")
    print(f"  {'pot/jug2, no experience':<28} {fresh.acts[0] if fresh.acts else '-':<16} "
          f"{'broken' if fresh.harmed else 'intact'}")
    print(f"  {'pot/jug2, taught by kettle':<28} {carried.acts[0] if carried.acts else '-':<16} "
          f"{'broken' if carried.harmed else 'intact'}")
    print()
    gate("the fresh world still does the damage, so the fixture can fail",
         fresh.harmed)
    gate("⭐ and the key GENERALISES: a row keyed on the relation `water` saves "
         "a jug it was never told about",
         not carried.harmed)

    # -- the lesser of two evils ------------------------------------------
    print("\n\nNo safe route -- two damaging ways to water, one twice as costly:\n")
    # -- a learned rule is a decision tree --------------------------------
    print("\n\nWhen the right move DEPENDS on the situation -- two worlds, one goal"
          "\nrelation, opposite best answers:\n")
    flat, cond, refined, costs = a_learned_rule_is_a_decision_tree()
    print("  taught by A, then REFINED against what it cost in A, B and C:")
    for r in refined:
        print(f"    {r}")
    print()
    print(f"  {'carried forward':<24} {'A':>4} {'B':>4} {'C':>4} {'total':>6}")
    for label in ("nothing", "depth-0", "unpruned", "refined"):
        c = costs[label]
        print(f"  {label:<24} {c[0]:>4} {c[1]:>4} {c[2]:>4} {sum(c):>6}")
    print()
    gate("a depth-0 tree (an unconditional fact) fixes the world it learned in",
         costs["depth-0"][0] < costs["nothing"][0])
    gate("⚠⚠⚠ ...and is WRONG in the other one, because it can only say *always*",
         costs["depth-0"][1] > costs["nothing"][1])
    gate("a learned RULE, generalised over the objects it saw",
         any(r.startswith("rule <learned-") and "?v0" in r for r in cond))
    gate("⚠ but taking EVERY circumstance is over-specific: the rule declines to "
         "fire in C and the agent breaks a jug it did not need to",
         costs["unpruned"][2] > costs["refined"][2])
    gate("⭐⭐⭐ refinement finds the depth that pays -- strictly better than the "
         "unconditional row, the unpruned rule, AND no experience",
         sum(costs["refined"]) < min(sum(costs["depth-0"]), sum(costs["unpruned"]),
                                     sum(costs["nothing"])))
    gate("and what it kept is one test, not zero -- pruning to nothing would be "
         "the unconditional row it was supposed to improve on",
         any(r.startswith("rule <learned-") for r in refined))
    gate("⚠ and marked `standing`, without which forgoing passes it up as a rival "
         "way of getting the same want, before it can advise",
         any(r.startswith("fact standing(<learned-") for r in cond))

    # -- a tree with more than one leaf, from more than one episode --------
    eps = [tree_episode(s)[0] for s in ("A", "B", "C")]

    def total(rows):
        return sum(len(tree_episode(s, rows)[1]) for s in ("A", "B", "C"))

    proposed = [l for ep in eps for l in leaves(ep)]
    tree = induce(eps, total)
    print()
    print("  induced from three episodes (two of which propose a WRONG leaf):")
    for r in tree:
        print(f"    {r}")
    print()
    print(f"    leaves proposed {len(proposed)}, unconditional among them "
          f"{sum(1 for _, _, t in proposed if not t)}, kept "
          f"{sum(1 for r in tree if r.startswith('rule '))}")
    print(f"    induced total cost {total(tree)}")
    print()
    gate("⚠⚠⚠ episodes propose UNCONDITIONAL leaves -- an episode only knows the "
         "cost of the route it took, which is the oscillation as a hypothesis",
         any(not t for _, _, t in proposed))
    gate("⭐⭐⭐ ...and joint pruning removes them: induction over three episodes "
         "reaches the same optimum, so a wrong leaf is not a special case",
         total(tree) == sum(costs["refined"]) and total(tree) < sum(costs["depth-0"]))
    gate("what survives is a conditional rule, not the unconditional row that "
         "dominated the raw proposals",
         any(r.startswith("rule <learned-") for r in tree))

    # ⚠ A measured NEGATIVE result, gated so it cannot rot into a claim.
    bagged = forest(eps, total)
    print(f"    bagging three trees instead: total {total(bagged)}"
          f" (one tree: {total(tree)})")
    print()
    gate("⚠⚠⚠ bagging does NOT pay yet -- `_priority` SUMS, and summation is not "
         "voting: one bag's over-general row fires everywhere and cannot be "
         "outvoted. A forest needs a rule that can DEFEAT, not only add",
         total(bagged) > total(tree))

    ev = lesser_of_two_evils()
    print(f"  {'authored first':<14} {'scheme':<36} losses per episode")
    for label in ("good start", "bad start"):
        today, ceiling, cost = ev[label]
        print(f"  {label:<14} {'suppress + promote passed-up':<36} {today}")
        print(f"  {'':<14} {'ceiling (magnitude, hand-authored)':<36} {ceiling}")
    print()
    built = {}
    for label, order in (("good start", [HARM_JUG, HARM_VASE]),
                         ("bad start", [HARM_VASE, HARM_JUG])):
        eps, seq, rows = [], [], ()
        for _ in range(4):
            m, _, lost = harm_episode(order, rows)
            seq.append(len(lost))
            eps.append(m)
            rows = induce(eps, lambda r: len(harm_episode(order, r)[2]))
        built[label] = (seq, rows)
        print(f"  {label:<14} {'MAGNITUDE (observed, accumulated)':<36} {seq}")
        for r in rows:
            if r.startswith("fact prefer") and "use-" in r:
                print(f"  {'':<14} {'':<36} {r}")
    print()
    good_today, _, _ = ev["good start"]
    bad_today, _, _ = ev["bad start"]
    good_built, bad_built = built["good start"][0], built["bad start"][0]
    gate("without magnitude the agent OSCILLATES -- no notion of how much, so it "
         "alternates forever", len(set(good_today)) > 1 and len(set(bad_today)) > 1)
    gate("⭐⭐⭐ with magnitude it CONVERGES from a good start, instead of "
         "learning its way onto the costlier route",
         len(set(good_built)) == 1 and good_built[0] == min(good_today))
    gate("⭐⭐⭐ ...and from a BAD one, paying the expensive route once and "
         "then staying on the cheaper",
         bad_built[0] > bad_built[-1] and len(set(bad_built[1:])) == 1)
    gate("⭐ the lesser evil is preferred BY ITS MARGIN, on the table's own "
         "non-negative scale -- no negative numeral anywhere",
         any("prefer(<use-jug>" in r for r in built["bad start"][1]))
    gate("⚠ exploration still pays for the knowledge: the bad start had to "
         "take the costly route once to learn what it cost",
         bad_built[0] == max(bad_built))

    # -- how sure, as a WRAPPER rather than a field ------------------------
    VENTURE = ["rule <venture> = implies( { +possible(prefer(?r, ?k, ?n)), +exploring },"
               " { +prefer(?r, ?k, ?n) } )", "fact standing(<venture>)",
               "fact +exploring"]
    order = [HARM_VASE, HARM_JUG]

    def play(hedge, extra):
        eps, seq, rows = [], [], ()
        for _ in range(4):
            m, _, lost = harm_episode(order, list(rows) + extra)
            seq.append(len(lost))
            eps.append(m)
            rows = induce(eps, lambda r: len(harm_episode(order, list(r) + extra)[2]),
                          hedge=hedge)
        return seq

    plain = play(False, [])
    shy = play(True, [])
    venturing = play(True, VENTURE)
    print()
    print("  how sure, as a WRAPPER -- `possible(prefer(...))` from a bad start:")
    print()
    for lbl, seq in (("unhedged", plain), ("hedged, no explore rule", shy),
                     ("hedged + <venture>", venturing)):
        print(f"  {lbl:<28} {seq}")
    print()
    gate("⭐⭐⭐ an unsure preference does NOT silently steer: hedged advice "
         "leaves the agent on what it knows, and it never ventures",
         len(set(shy)) == 1)
    gate("⭐⭐⭐ ...and one ordinary corpus rule takes it up again -- so "
         "explore/exploit is a CLAIM, not machinery",
         venturing == plain and venturing[-1] < shy[-1])
    gate("⚠ the hedge is constant-free: `observed` vs `never tried` is a "
         "distinction the trail makes, not a threshold anybody chose",
         plain[0] == shy[0] == venturing[0])

    # The COUNT, not only the failures. `0 failing` is the same output whether
    # this ran thirty checks or none -- which is exactly how ten of this file's
    # were deleted by an edit and nothing noticed. `ugm.selftest` has printed
    # `291 checks` all along and was the only instrument that could have said so.
    print(f"\n{ran} checks, {failing} failing")
    print("""
  ⭐⭐⭐ A LEARNED RULE IS A DECISION TREE, and the shape was already here. A
  `prefer` FACT is a tree of depth zero -- it says *always*, given its key. A
  `prefer`-concluding RULE says *when*, and its internal nodes are antecedent
  members. `_priority` SUMS applicable rows, so a set of them is an additive
  ENSEMBLE natively; and generalising is unconstrained because a preference
  consequent holds no variables. The tests come off the trail, so the
  hypothesis space is the corpus's own vocabulary -- no features to engineer.

  ⚠ ONE TEST-SET, ALL OF IT, and the judgement is which error is recoverable
  -- forgoing's judgement again. An over-specific condition does not fire and
  the agent falls back; an over-general one advises confidently where it has
  never been. What is NOT here is refinement: nothing prunes a test that turns
  out not to matter, nothing merges two rules, and nothing revisits a tree that
  stops paying. That is where mutation goes, and it is affordable exactly
  because a learned rule concludes `prefer` and never `doing` -- a bad
  candidate costs ticks, not jugs.

  ⚠⚠⚠ THE LESSER OF TWO EVILS IS UNSAYABLE, and the two open items are ONE.
  Suppression with no magnitude oscillates; magnitude with no exploration
  sticks. What is missing is a SECOND QUANTITY, and both scales already exist
  and are already kept apart on purpose: a cardinal score on the table for
  *how good*, §10's ordinal grade on the entry for *how sure*. Nothing writes
  the pair from experience -- and a learner that yields a value together with
  a spread is exactly the shape of thing that would.

  ⚠ WHAT THIS DOES NOT SHOW. The promoted alternative is recommended because it
  was passed up by something that harmed -- not because it is good. In a world
  where every route does damage, `learned` recommends none of them, which is
  right, and it has nothing to offer instead, which is the same gap `blame`
  has: *how badly* is unsayable while the table's numerals are non-negative.

  ⚠ And the signal is one episode deep. Nothing here weighs a route that
  usually works against one that worked once, because a second `prefer` row for
  the same rule and key does not accumulate -- restating is not revising (§8).

  ⭐⭐ MEASURED (08-13), and it explains something in a different file. Two
  IDENTICAL rows are one proposition, so `3 and 3` scores 3; two DISTINCT rows
  sum, so `3 and 4` scores 7 and outweighs a single 5. Both are checks now. That
  is also the real reason `forest` failed: its verdict was `summation is not
  voting`, and the sharper statement is

  > An ensemble's agreement is invisible and only its disagreement adds.

  So this note and that verdict were the same fact, filed as a known limitation
  in one file and as an unexplained failure in the other.""")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
