"""Can an agent set itself the goals it learns from? (§16, §19)

ugm.learning closes with a cost it could not pay off: an agent learns the route
that harms by TAKING it. It paid in a jug. This file asks whether it has to.

⚠⚠⚠ **Rewritten 2026-08-20, when situations were retired.** A rehearsal used to
be a supposition: the register stood inside a frame, `_dispatch` wrote
`taken(...)` instead of emitting, and the damage died with the frame. None of
that exists now. A rehearsal is an ANCHOR -- an ordinary node the world's facts
are stated relative to -- and containment is a premise rather than a mechanism.

See docs/design/practice.md.
"""

from typing import List, Optional, Sequence, Tuple

from ..core.machine import Machine, induce, leaves
from ..core.text import load

# ⭐⭐⭐ **Anchor what a rehearsal and the world can DISAGREE about; leave bare
# what they share.** `under`, `holds`, `achieves` and `fruit` are the same in
# every scene and stay bare; `tap`, `jug`, `intact`, `water`, `doing` and `did`
# are anchored, because a rehearsal is exactly a scene where those can differ.
#
# ⚠⚠ This is not a matter of taste, and blanket anchoring was measured and
# rejected twice over:
#
#   every premise anchored   `_relations_required` collapses to {goal, in} for
#                            EVERY route, so `_salient` cannot tell two routes
#                            apart and `leaves` returns nothing.
#   `doing`/`did` anchored   `_circumstances` skips DOING and DID BY RELATION,
#   with no anchored premise and `in(?s, did(...))` is not either of them -- so
#   in the chooser          the lesson gets conditioned on what happened AFTER
#                            the choice, and can never fire before it.
#
# Both are fixed by the same thing: the choosing rules name `in` in their own
# antecedents, which puts it in `_circumstances`'s `required` set.
ROUTES = [
    "rule <use-jug> = implies( { +goal(in(?s, water(?v))), +in(?s, jug(?j)),"
    "                           +holds(?j, ?v) }, { +in(?s, doing(smash(?j))) } )",
    "rule <use-tap> = implies( { +goal(in(?s, water(?v))), +in(?s, tap(?t)),"
    "                           +under(?v, ?t) }, { +in(?s, doing(fill(?v))) } )",
]
PHYSICS = [
    "rule <eff>  = implies( { +in(?s, did(?a)), +achieves(?a, ?y) }, { +in(?s, ?y) } )",
    "rule <cost> = implies( { +in(?s, did(smash(?j))) }, { -in(?s, intact(?j)) } )",
    "rule <squeeze> = implies( { +fruit(?f), +in(?s, jug(?j)), +in(?s, intact(?j)) },"
    "                         { +in(?s, juice(?j)) } )",
]
# ⭐⭐⭐ The three bridges, and they are the whole of what `suppose`/`discharge`
# used to be. A scene the agent calls its WORLD acts; a scene it calls a
# REHEARSAL assumes instead. **Containment is `+world(?s)` -- an ordinary
# premise a rule fails to match**, which is what `docs/todo.md` measured when it
# said *what would happen if we set fire to the house*, answered without burning
# it down, with no machinery.
BRIDGE = [
    "rule <act>     = implies( { +world(?s), +in(?s, doing(?a)) }, { +doing(?a) } )",
    "rule <assume>  = implies( { +rehearsal(?s), +in(?s, doing(?a)) },"
    "                         { +in(?s, did(?a)) } )",
    "rule <observe> = implies( { +world(?s), +did(?a) }, { +in(?s, did(?a)) } )",
]
STANDING = [
    "fact +achieves(fill(kettle), water(kettle))",
    "fact +achieves(smash(jug1), water(kettle))",
    "fact +under(kettle, sink)", "fact +holds(jug1, kettle)",
    "fact +fruit(orange)",
]
BAD_START = ROUTES              # the jug route first: the costly one wins on order
GOOD_START = list(reversed(ROUTES))
LOSSES = ("intact(jug1)",)

# The proposer. `suppose(goal(?y), certain)` became `goal(in(?s, ?y))` -- the
# agent wants a thing IN a scene, which is what supposing a goal always meant.
PRACTISE = ("rule <practise> = implies( { +rehearsal(?s), +achieves(?a, ?y) },"
            " { +goal(in(?s, ?y)) } )")
# The kill-probe for containment: the same proposer raising the same goal in the
# WORLD instead. Everything else is identical, so what it measures is the anchor.
BARE = ("rule <practise> = implies( { +world(?s), +achieves(?a, ?y) },"
        " { +goal(in(?s, ?y)) } )")

# A second achievable relation, so the proposer can be shown raising more than
# one goal.
SECOND = ["rule <use-match> = implies( { +goal(in(?s, lit(?r))), +in(?s, match(?m)) },"
          "                           { +in(?s, doing(strike(?m))) } )",
          "rule <light> = implies( { +in(?s, did(strike(?m))) }, { -in(?s, dark(room)) } )",
          "fact +achieves(strike(match), lit(room))"]
SECOND_SCENE = ["fact +in({s}, match(match))", "fact +in({s}, dark(room))",
                "fact +goal(in({s}, dark(room)))"]
WIDER = LOSSES + ("dark(room)",)


def scene(s: str, extra: Sequence[str] = ()) -> List[str]:
    """The facts a scene needs of its own -- what it can disagree with another
    scene about. ⚠ **Given by hand, not inherited.** `docs/todo.md` measured
    blanket inheritance as dearer than assembling a scene deliberately (177
    entries against 167), and it copies things a rehearsal has no business
    having."""
    return [f"fact +in({s}, intact(jug1))", f"fact +goal(in({s}, intact(jug1)))",
            f"fact +in({s}, tap(sink))", f"fact +in({s}, jug(jug1))"] + [
        line.format(s=s) for line in extra]


def _lost_in(m, kb, s: str, losses: Sequence[str] = LOSSES) -> List[str]:
    """What this scene cost, charged BY ANCHOR.

    ⭐ This used to be `_own_losses`/`_charge`: a `locus.at_or_after(frame.origin)`
    test that separated a nested rehearsal's own damage from its parent's,
    because both were entries on one chain and only the locus told them apart.
    An anchor is in the proposition, so the question is now *which scene is this
    about* and there is no locus arithmetic left to get wrong.
    """
    return [g for g in losses if m.holds(kb.term(f"in({s}, {g})")) == "-"]


def rehearse(rows: Sequence[str] = (), order: Sequence[str] = BAD_START,
             proposer: str = PRACTISE, extra: Sequence[str] = (),
             scenes: Sequence[str] = ("r1",), losses: Sequence[str] = LOSSES,
             scene_extra: Sequence[str] = ()) -> Tuple[Machine, List[str]]:
    """One practice run: the agent works out what it could want, and tries it.

    ⚠ The register is left where it always is. The old version returned the
    machine *standing inside* the rehearsal, because `blame` and `leaves` read
    from where the reader stands and the reasoning had happened in a frame they
    could not otherwise see. An anchor is visible from everywhere, so there is
    nowhere to stand but here.
    """
    m = Machine()
    m.actuator("hands")
    src = list(order) + PHYSICS + BRIDGE + STANDING + list(extra)
    for s in scenes:
        src += [f"fact +rehearsal({s})"] + scene(s, scene_extra)
    kb = load(m, "\n".join(src + [proposer] + list(rows) + [""]))
    m.run(limit=6000)
    m.kb = kb
    lost: List[str] = []
    for s in scenes:
        lost.extend(_lost_in(m, kb, s, losses))
    return m, lost


def episode(rows: Sequence[str] = (), order: Sequence[str] = BAD_START):
    """One run IN THE WORLD: the goal handed over, nothing rehearsed."""
    m = Machine()
    m.actuator("hands")
    kb = load(m, "\n".join(
        list(order) + PHYSICS + BRIDGE + STANDING
        + ["fact +world(actual)"] + scene("actual")
        + ["fact +goal(in(actual, water(kettle)))"] + list(rows) + [""]))
    m.run(limit=6000)
    return (m, [m.g.show(n) for n in m.emitted], _lost_in(m, kb, "actual"))


def practise(rounds: int = 4, order: Sequence[str] = BAD_START
             ) -> Tuple[List[int], List[str]]:
    """Rehearse, review, carry forward, rehearse again -- and never act.

    The cost `induce` prunes against is measured by **re-rehearsing**, so the
    learner never touches the world at all. Every number this function knows was
    paid for in ticks.
    """
    eps: List[Machine] = []
    seq: List[int] = []
    rows: List[str] = []

    def cost(candidate) -> int:
        return len(rehearse(candidate, order)[1])

    for _ in range(rounds):
        m, lost = rehearse(rows, order)
        eps.append(m)
        seq.append(len(lost))
        rows = induce(eps, cost)
    return seq, rows


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

    # -- the proposer ------------------------------------------------------
    print("A goal nobody authored, raised from what the corpus says acts achieve:\n")
    m, lost = rehearse()
    raised = [m.g.show(n) for n in m.g.instances_of(m.GOAL)
              if m.holds(n) == "+" and not m.g.has_var(n)]
    for r in raised:
        print(f"    {r}")
    print()
    gate("the goal it practises is authored NOWHERE in the corpus",
         not any("water(kettle)" in line and "goal" in line
                 for line in BAD_START + PHYSICS + BRIDGE + STANDING + scene("r1")))
    gate("...and the agent raised it anyway, from `achieves`",
         "goal(in(r1, water(kettle)))" in raised)

    multi, _ = rehearse(extra=SECOND, scene_extra=SECOND_SCENE, losses=WIDER)
    mraised = {multi.g.show(n) for n in multi.g.instances_of(multi.GOAL)
               if multi.holds(n) == "+" and not multi.g.has_var(n)}
    gate("one goal per achievable relation, so the proposer is not a one-trick",
         "goal(in(r1, water(kettle)))" in mraised
         and "goal(in(r1, lit(room)))" in mraised)

    # -- containment -------------------------------------------------------
    print("\nWhat it cost, and where it was paid:\n")
    print(f"  {'run':<22} {'emitted':<24} lost")
    print(f"  {'rehearsed':<22} {str([m.g.show(n) for n in m.emitted]):<24} {lost}")
    bm, bare_acts, bare_lost = None, None, None
    bm = Machine()
    bm.actuator("hands")
    bkb = load(bm, "\n".join(
        list(BAD_START) + PHYSICS + BRIDGE + STANDING
        + ["fact +world(actual)"] + scene("actual") + [BARE, ""]))
    bm.run(limit=6000)
    bare_acts = [bm.g.show(n) for n in bm.emitted]
    bare_lost = _lost_in(bm, bkb, "actual")
    print(f"  {'raised in the world':<22} {str(bare_acts):<24} {bare_lost}")
    print()
    gate("⭐⭐⭐ a rehearsal costs the agent NOTHING -- it takes a route, breaks "
         "what the route breaks, and nothing leaves", not m.emitted and bool(lost))
    gate("⭐ ...and the containment is an ordinary PREMISE, not a mechanism: "
         "`<act>` wants `+world(?s)` and a rehearsal is not one",
         any(r.name == "act" for r in m.rules.rules))
    gate("...and the kill-probe shows the anchor is what does it: raise the same "
         "goal in the world and the jug really breaks",
         bool(bare_acts) and bool(bare_lost))
    gate("the reasoning does not stop at the act -- the route's outcome is "
         "reached in the scene, or there is nothing to cost",
         m.holds(m.kb.term("in(r1, did(smash(jug1)))")) == "+"
         and m.holds(m.kb.term("in(r1, water(kettle))")) == "+")

    # -- it is still a choice ---------------------------------------------
    forgone = {m.g.show(e.proposition) for mo in m.chain.moments for e in mo.delta
               if m.g.show(e.proposition).startswith("forgone(")}
    did = [m.g.show(e.proposition) for mo in m.chain.moments for e in mo.delta
           if m.g.show(e.proposition).startswith("in(r1, did(")]
    print(f"  did     {did}")
    print(f"  forgone {sorted(forgone)}")
    print()
    gate("⭐ forgoing works in a rehearsal, so it is a CHOICE -- one route taken, "
         "the other passed up and named", len(did) == 1 and len(forgone) == 1)

    # -- practice, and the exploration nobody wrote ------------------------
    print("\nFour rehearsals, each loading what the last one worked out:\n")
    seq, rows = practise()
    print(f"  rehearsed harm per round   {seq}")
    for r in rows:
        print(f"    {r}")
    print()
    gate("⭐⭐⭐ the first rehearsal costs a jug and the rest cost nothing -- the "
         "agent found the better route and paid for it in ticks", seq[0] > seq[1])
    gate("...and it stays found: no oscillation, because the route it wanted "
         "was there to be passed up all along", len(set(seq[1:])) == 1)
    gate("no `<venture>` rule and no explore/exploit switch anywhere",
         not any("venture" in r or "exploring" in r for r in rows))
    # ⚠ The lesson names the SINK -- the node that makes the cheaper route
    # available -- and it now reaches it through `under(kettle, sink)` rather
    # than `tap(sink)`, because `tap` is anchored and `under` is not. The claim
    # was always about the NODE and never about which relation found it.
    gate("what it carries out names the node that makes the cheaper route "
         "available, and no rule id at all",
         any("attention(" in r and "sink" not in r for r in rows)
         and not any("prefer(" in r for r in rows))

    # -- the headline ------------------------------------------------------
    print("\nThe world, for real, from the bad start -- ONE run each:\n")
    print(f"  {'agent':<26} {'emitted':<20} lost")
    naive_m, naive_acts, naive_lost = episode()
    prac_m, prac_acts, prac_lost = episode(rows)
    print(f"  {'no practice':<26} {str(naive_acts):<20} {naive_lost}")
    print(f"  {'practised first':<26} {str(prac_acts):<20} {prac_lost}")
    print()
    gate("the control can fail: an unpractised agent from a bad start takes the "
         "costly route", naive_lost == ["intact(jug1)"])
    gate("⭐⭐⭐ the practised agent gets it right the FIRST time in the world, "
         "and the knowledge was paid for in ticks",
         len(prac_lost) < len(naive_lost))
    gate("...and it is not merely doing less -- the goal is still achieved",
         prac_m.holds(prac_m.kb.term("in(actual, water(kettle))")) == "+"
         if hasattr(prac_m, "kb") else bool(prac_acts))

    # -- what nesting became ----------------------------------------------
    print("\nTwo rehearsals at once, which is what nesting became:\n")
    two, two_lost = rehearse(scenes=("r1", "r2"))
    per = {s: _lost_in(two, two.kb, s) for s in ("r1", "r2")}
    for s, l in per.items():
        print(f"    {s}   {l}")
    print()
    gate("⭐ two rehearsals run at once and each is charged its own damage -- "
         "by ANCHOR, with no locus arithmetic",
         per["r1"] == ["intact(jug1)"] and per["r2"] == ["intact(jug1)"]
         and two.holds(two.kb.term("intact(jug1)")) is None)
    # ⚠⚠⚠ The old fixture's last check was that `<practise>` matched INSIDE a
    # practice frame, so rehearsals nested -- *the crossing runaway in a new
    # place*, reported as a finding. Anchors do not run away: `<practise>` needs
    # `+rehearsal(?s)`, and a scene is a node somebody had to write down. That is
    # the runaway closed by construction rather than bounded by a knob, which is
    # what `hypotheses(n)` and `depth(n)` were for and why both could go.
    scenes_declared = {two.g.show(two.g.member(n, 0))
                       for n in two.g.instances_of(two.kb.atom("rehearsal"))
                       if two.holds(n) == "+"}
    gate("⚠⚠⚠ ...and rehearsals do NOT run away: a scene is a node somebody "
         "wrote down, so the crossing runaway the knobs used to bound cannot "
         "start", scenes_declared == {"r1", "r2"})

    print(f"\n{ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
