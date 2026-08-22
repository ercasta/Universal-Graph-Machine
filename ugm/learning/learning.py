"""Does an episode teach the next one anything? (§19, §20)

Learning here is offline and it is a corpus: an episode ends, review and blame
walk the trail, and learned() writes surface text the next episode loads.
Nothing about the loop changes.  The cost is real too, and it is measured
rather than conceded.

See docs/design/learning.md.
"""

from typing import List, Tuple

from ..core.machine import Machine, forest, induce, leaves
from ..core.text import ParseError, load

BASE = [
    "rule <eff> = implies( { +did($a), +achieves($a, $y) }, { +$y } )",
    "rule <cost> = implies( { +did(smash($j)) }, { -intact($j) } )",
    "rule <squeeze> = implies( { +fruit($f), +jug($j), +intact($j) }, { +juice($j) } )",
]
# Both routes SPEND the want they serve, and that is what makes taking one
# passing up the other. Nothing in the engine does it: an occasion is consumed,
# and a goal is an occasion. Without the denial both routes run, the agent fills
# the kettle AND smashes the jug, and the episode has no choice to learn from.
TAP = ("rule <use-tap> = implies( { +goal(water($w)), +tap($t), +under($w, $t) },"
       " { -goal(water($w)), +doing(fill($w)) } )")
JUG = ("rule <use-jug> = implies( { +goal(water($w)), +jug($j), +holds($j, $w) },"
       " { -goal(water($w)), +doing(smash($j)) } )")


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


def run(jug_first: bool = True, rounds: int = 3, carry: str = "",
        keep: bool = True) -> List[Episode]:
    """Play the same world `rounds` times, each one loading what came before.

     What is carried ACCUMULATES, and it has to, which is a finding about
    the rewrite rather than a convenience.

    See docs/design/learning.md#run.
    """
    out: List[Episode] = []
    learned: List[str] = [line for line in carry.split(chr(10)) if line.strip()]
    for _ in range(rounds):
        ep = Episode(world(jug_first=jug_first)
                     + chr(10).join(learned) + chr(10))
        out.append(ep)
        if not keep:
            learned = list(ep.rows)
            continue
        #  Deduped by identity, so restating is not revising (§8) -- two
        # copies of one lesson are one proposition, exactly as two identical
        # `prefer` rows always were.
        for row in ep.rows:
            if row not in learned:
                learned.append(row)
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


# Spending the want, for the third time in this file and the same reason: with
# both routes live the agent takes both, every start costs the same, and *which
# start you had* -- the thing this fixture varies -- stops being measurable.
HARM_JUG = ("rule <use-jug> = implies( { +goal(water($w)), +jug($j), +holds($j, $w) },"
            " { -goal(water($w)), +doing(smash($j)) } )")
HARM_VASE = ("rule <use-vase> = implies( { +goal(water($w)), +vase($v), +holds($v, $w) },"
             " { -goal(water($w)), +doing(shatter($v)) } )")
HARM_BASE = [
    "rule <eff> = implies( { +did($a), +achieves($a, $y) }, { +$y } )",
    "rule <cost-j> = implies( { +did(smash($j)) }, { -intact($j) } )",
    "rule <cost-v> = implies( { +did(shatter($v)) }, { -intact($v) } )",
    "rule <set-broken> = implies( { +did(shatter($v)), +completes($v, $s) },"
    " { -whole($s) } )",
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


def the_lesser_of_two_evils_is_unsayable(rounds: int = 3):
    """ A route can only be preferred over one it is NOT about. Measured.

    This used to be lesser_of_two_evils, and it used to report a result: with
    magnitude accumulated across episodes the agent converged on the cheaper of
    two damaging routes, from a good start and from a bad one.

    See docs/design/learning.md#the-lesser-of-two-evils-is-unsayable.
    """
    out = {}
    for label, order in (("good start", [HARM_JUG, HARM_VASE]),
                         ("bad start", [HARM_VASE, HARM_JUG])):
        seq, rows, eps = [], [], []
        for _ in range(rounds):
            m, acts, lost = harm_episode(order, rows)
            seq.append(len(lost))
            eps.append(m)
            rows = induce(eps, lambda r: len(harm_episode(order, r)[2]))
        out[label] = (seq, rows, eps[0])
    return out


def a_lesson_outlives_its_rule() -> dict:
    """Carry a lesson into a world where the rule it is about was RENAMED.

    ⭐⭐⭐ The whole argument for keying on nodes, and it is one run. A rule id is
    not stable: rules are adopted, composed, rewritten and edited, and §21 is
    full of mechanisms that do it.  The rename is the whole difference.

    See docs/design/learning.md#a-lesson-outlives-its-rule.
    """
    ep = Episode(world(jug_first=True))
    renamed = world(jug_first=True).replace("<use-tap>", "<faucet>")
    out = {}
    for label, rows in (("nothing", []),
                        ("attention lesson", ep.rows),
                        ("prefer row", ["fact prefer(<use-tap>, water, 3)"])):
        try:
            m = Machine()
            m.actuator("hands")
            kb = load(m, renamed + chr(10).join(rows) + chr(10))
            m.run(limit=4000)
            out[label] = ([m.g.show(n) for n in m.emitted],
                          m.holds(kb.term("intact(jug1)")) == "-", None)
        except ParseError as exc:
            out[label] = (None, None, str(exc).split(" -- ")[0])
    return out


# ...and these spend the want they serve too, for the reason `ROUTES` does: with
# nothing passing up the other way the agent takes BOTH in every world, every
# world costs the same, and a fixture about which advice is worth having has
# nothing left to measure. Measured: all four rows scored 2 3 1 without it.
TREE_JUG = ("rule <use-jug> = implies( { +goal(water($w)), +jug($j), +holds($j, $w) },"
            " { -goal(water($w)), +doing(smash($j)) } )")
TREE_TAP = ("rule <use-tap> = implies( { +goal(water($w)), +tap($t), +under($w, $t) },"
            " { -goal(water($w)), +doing(fill($w)) } )")
TREE_CORE = [
    "rule <eff> = implies( { +did($a), +achieves($a, $y) }, { +$y } )",
    "rule <cost> = implies( { +did(smash($j)) }, { -intact($j) } )",
    "rule <extra> = implies( { +did(smash($j)), +precious($j), +completes($j, $s) },"
    " { -whole($s) } )",
    "rule <drain> = implies( { +did(fill($w)), +scarce($w) }, { -reserve(town) } )",
    "rule <drop> = implies( { +did(fill($w)), +scarce($w) }, { -pressure(main) } )",
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

    Not an analogy.

    See docs/design/learning.md#a-learned-rule-is-a-decision-tree.
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
    #  The control for the line above, and it is the code as it stood.
    # Under `prefer` a good episode re-derived the lesson by CREDIT, so
    # replacing the carry each round was invisible. With credit gone, an
    # episode that goes well says nothing at all -- and the lesson is forgotten
    # the moment it starts working.
    forgetful = run(jug_first=True, rounds=3, keep=False)
    gate(" ...and it stays taught only because what is carried ACCUMULATES: "
         "keep just the last episode's rows and the third smashes the jug again, "
         "because the second had nothing to say",
         not forgetful[1].harmed and forgetful[2].harmed)
    gate("what it learned names the alternative it passed up, not just the "
         "rule it stopped recommending",
         any("attention(sink" in r for r in eps[0].rows))
    gate("⭐⭐⭐ ...and it names it by the THING that makes that route available "
         "-- no rule id appears in anything an episode writes down",
         bool(eps[0].rows) and not any("<" in r for r in eps[0].rows))
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
    gate(" ...and with credit gone it now writes NOTHING AT ALL, where it used "
         "to write rows about the wrong half of the choice -- suppression on "
         "its own has no sentence left to say",
         not ctrl[0].rows)

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
    gate("⭐ and the lesson GENERALISES: what it named -- the tap -- is in a "
         "world of objects it was never told about, and saves a jug there",
         not carried.harmed)

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
    gate(" ...and is WRONG in the other one, because it can only say *always*",
         costs["depth-0"][1] > costs["nothing"][1])
    gate("a learned RULE, generalised over the objects it saw",
         any(r.startswith("rule <learned-") and "$v0" in r for r in cond))
    gate(" but taking EVERY circumstance is over-specific: the rule declines to "
         "fire in C and the agent breaks a jug it did not need to",
         costs["unpruned"][2] > costs["refined"][2])
    gate("⭐⭐⭐ refinement finds the depth that pays -- strictly better than the "
         "unconditional row, the unpruned rule, AND no experience",
         sum(costs["refined"]) < min(sum(costs["depth-0"]), sum(costs["unpruned"]),
                                     sum(costs["nothing"])))
    gate("and what it kept is one test, not zero -- pruning to nothing would be "
         "the unconditional row it was supposed to improve on",
         any(r.startswith("rule <learned-") for r in refined))
    gate(" and marked `standing`, without which it is passed up as a rival "
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
          f"{sum(1 for leaf in proposed if not leaf[2])}, kept "
          f"{sum(1 for r in tree if r.startswith('rule '))}")
    print(f"    induced total cost {total(tree)}")
    print()
    gate(" episodes propose UNCONDITIONAL leaves -- an episode only knows the "
         "cost of the route it took, which is the oscillation as a hypothesis",
         any(not leaf[2] for leaf in proposed))
    gate("⭐⭐⭐ ...and joint pruning removes them: induction over three episodes "
         "reaches the same optimum, so a wrong leaf is not a special case",
         total(tree) == sum(costs["refined"]) and total(tree) < sum(costs["depth-0"]))
    gate("what survives is a conditional rule, not the unconditional row that "
         "dominated the raw proposals",
         any(r.startswith("rule <learned-") for r in tree))

    #  A measured NEGATIVE result, gated so it cannot rot into a claim.
    bagged = forest(eps, total)
    print(f"    bagging three trees instead: total {total(bagged)}"
          f" (one tree: {total(tree)})")
    print()
    #  The VERDICT survives the rewrite and the REASON does not, which is
    # worth more than the number.
    # → docs/design/learning.md#the-verdict-survives-the-rewrite-and-the-rea
    gate(" bagging still does NOT pay, and no longer because of summation: "
         "attention takes the stronger, not the sum, and is MONOTONE -- one "
         "over-general leaf attends and no number of leaves declining to "
         "attend can overrule it",
         total(bagged) > total(tree))
    gate(" and it is exactly the over-general leaf: the bag keeps a lesson "
         "with no test at all beside two that learned the condition",
         any(r.startswith("rule <t") and "+precious" not in r for r in bagged))

    # -- what a lesson NAMES, and what that buys ---------------------------
    print(chr(10) * 2
          + "The same lesson carried into a world where the rule was RENAMED:"
          + chr(10))
    ren = a_lesson_outlives_its_rule()
    print(f"  {'carried forward':<22} {'emitted':<16} {'jug':<8} loaded")
    for label in ("nothing", "attention lesson", "prefer row"):
        acts, harmed, err = ren[label]
        print(f"  {label:<22} {str(acts[0] if acts else '-'):<16} "
              f"{('-' if harmed is None else 'broken' if harmed else 'intact'):<8} "
              f"{err or 'yes'}")
    print()
    gate("the renamed world can still fail, so the comparison is against "
         "something", ren["nothing"][1])
    gate("⭐⭐⭐ a lesson keyed on a NODE survives its rule being renamed -- "
         "`sink` is there whatever the rule that reads it is called",
         ren["attention lesson"][1] is False)
    gate("⭐⭐⭐ ...and the row it replaced does not merely go stale, it FAILS "
         "TO LOAD: a corpus of experience made unreadable by an edit elsewhere",
         ren["prefer row"][2] is not None)

    #  **THE CREDIT COMPARISON IS RETIRED, BECAUSE IT STOPPED BEING ONE.**
    # It ran the taught episode with the old `prefer(<squeeze>, juice, 3)` rows
    # added back by hand and reported that they changed nothing -- on the stated
    # reason that those rules *had no rivals to be lifted over*. With `prefer`
    # and `_priority` gone that reason is false: the rows change nothing because
    # NOTHING READS THEM, so the two arms were identical by construction and the
    # gate could not fail. `docs/HANDOFF.md` 20o predicted exactly this and
    # asked for it to be re-read once the buffs went; this is that read.
    #
    # What it claimed is not refuted, it is UNMEASURABLE here -- there is no
    # longer any way to add credit back and see. Recorded rather than repaired,
    # because repairing it would mean re-adding the mechanism it was about.

    # -- and what cannot be said at all ------------------------------------
    print(chr(10) * 2
          + "No safe route -- two damaging ways to water, one twice as costly:"
          + chr(10))
    ev = the_lesser_of_two_evils_is_unsayable()
    print(f"  {'authored first':<14} {'losses per episode':<24} learned")
    for label in ("good start", "bad start"):
        seq, rows, ep0 = ev[label]
        print(f"  {label:<14} {str(seq):<24} {rows or 'nothing'}")
    print()
    good, bad = ev["good start"], ev["bad start"]
    gate(" nothing is learned in either direction -- where both routes "
         "are ABOUT the same things, no node lifts one and not the other",
         not good[1] and not bad[1])
    gate("...so the bad start never improves, and the good one never decays: "
         "the agent is exactly where authored order put it",
         len(set(good[0])) == 1 and len(set(bad[0])) == 1 and bad[0][0] > good[0][0])
    # ⭐ The kill-probe for the refusal. `_salient` is what declines to write the
    # lesson, and a check that only observed *nothing happened* could not tell
    # that from a learner that ran and found nothing worth saying.
    ep0 = bad[2]
    harmed = {r.node for r, _ in ep0.blame()}
    choosers = ep0._choosers(harmed)
    alts = ep0._instead_of(harmed)
    gate("⭐ and it is a REFUSAL, not a silence: the alternative was found and "
         "named, and `_salient` declined to key a lesson on it",
         bool(alts) and all(ep0._salient(r, choosers) is None for r, _ in alts))
    gate(" the two routes are symmetric in what they are about, which is the "
         "whole of the reason -- `holds` is required by both",
         bool(set.intersection(*[ep0._relations_required(c) for c in choosers]
                               + [ep0._relations_required(alts[0][0])])))

    # The COUNT, not only the failures. `0 failing` is the same output whether
    # this ran thirty checks or none -- which is exactly how ten of this file's
    # were deleted by an edit and nothing noticed. `ugm.selftest` has printed
    # `291 checks` all along and was the only instrument that could have said so.
    print(f"\n{ran} checks, {failing} failing")
    print("""
  ⭐⭐⭐ A LESSON NAMES A THING, NOT A RULE, and the gain is a kind rather than a
  degree. `prefer(<use-tap>, water, 3)` was keyed on an identity, one level up
  from bindings; `attention(sink, 3)` is keyed on what makes that route
  available. Rename the rule and the attention lesson still saves the jug,
  while the row it replaced does not merely go stale -- it FAILS TO LOAD,
  because it refers to a statement that is not there. A corpus of experience
  could be made unreadable by an edit somewhere else.

  ⭐⭐⭐ A LEARNED RULE IS STILL A DECISION TREE, and the shape did not depend on
  what the leaf concluded. A ground `attention` fact is a tree of depth zero --
  it says *always, this thing*. A rule pruned to its BINDER is depth zero and
  generic -- *always, whatever plays that part*. Add tests and it says *when*.
  The tests still come off the trail, so the hypothesis space is still the
  corpus's own vocabulary, and there are still no features to engineer.

   WHAT A NODE CANNOT SAY, measured rather than conceded. A node separates
  two routes only when they are ABOUT different things. Where both hold their
  vessel -- `holds(jug1, kettle)` and `holds(vase, kettle)` -- no node lifts one
  and not the other, so the lesser of two evils, which `prefer` could state,
  cannot be stated at all.

  > **Rule-keyed advice can always separate two routes. Node-keyed advice can
  > separate only routes that are about different things.**

  And with it went the arms that stood on it: the magnitude result, the
  oscillation it repaired, and `possible(prefer(...))` with its `<venture>`
  rule. `how sure is a WRAPPER, not a field` is untouched as a claim -- `induce`
  still hedges an unobserved leaf -- but nothing here exercises it any more.

   CREDIT WAS LOAD-BEARING, AND NOT WHERE IT LOOKED. Recommending the rules
  that HELPED reads like decoration beside regret, and dropping it changes no
  single run here. What it was quietly doing was RE-WRITING the lesson every
  round: episode 2 took the tap, the tap was on the support of the outcome, so
  the row came back without anyone regretting anything. Take credit away and

  > **a lesson learned from regret is written once**, and an episode that goes
  > well has nothing to say at all.

  So the carry has to accumulate, which is what a corpus of experience always
  claimed to be. The control is in the run above: keep only the last episode's
  rows and the third smashes the jug again.

   AN ENSEMBLE STILL DOES NOT PAY, through a different mechanism. The old
  reason was that `_priority` SUMS and summation is not voting. Attention takes
  the stronger, not the sum -- and fails one step deeper, because attending is
  MONOTONE: one over-general leaf attends the tap where two others would not,
  and there is no sentence for *not this one, here*. `unattend` clears the whole
  queue. A forest still needs something that can DEFEAT.

   AND THE SIGNAL IS STILL ONE EPISODE DEEP. Nothing here weighs a route that
  usually works against one that worked once. The weight on an `attention` claim
  is now a place to put that -- `attention(x, n)` carries its evidence count the
  way `attend($x, n)` always has -- and nothing yet accumulates into it.""")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
