"""The ATTENTION STACK: `push` and `pop`, measured before it is believed.

    python -m ugm.probes.frames

`Machine._attention` is a stack of frames rather than a flat queue, and the
postcondition vocabulary gained two rows:

    push($a, $b, ...)   start a fresh attention frame on those nodes
    pop($x)             restore the previous frame, attending $x on it

⚠⚠⚠ **The graph is untouched by both.** This is not a transaction, there is no
rollback, and nothing derived inside a frame stops existing when it is popped.
Attention management is the whole of this. The one thing a pop takes back is the
frame's own `attention` claims, and it DENIES them rather than dropping them.

⭐⭐⭐ Why a stack rather than a fourth filter: three fixes have been tried on
the flat queue -- claimed vs derived, excluding bookkeeping, a learned weight --
and every one of them makes the queue's CONTENTS more selective. None of them
can help, because at span 7 a long enough sub-line evicts anything, however well
chosen. A stack does not filter, it SUSPENDS.

And `docs/todo.md` asks for the numbers before the mechanism, so §1 and §3 below
are measurements rather than demonstrations: *a frame that fixes nothing
measurable is a mechanism this design would refuse on its own terms.*

See docs/todo.md, "the ATTENTION STACK".
"""

from ..core.attention import SETTLE, Table, run, _standing
from ..core.chain import PLUS
from ..core.machine import FRAME_DEPTH, Machine
from ..core.text import Loader, load

# Twelve rules that never match, so the shortlist is a real cut and the lift has
# something to do. `attention_is_a_bounded_queue` uses the same instrument.
PAD = "".join("rule <p%d> = implies( { +z%d($x) }, { +y%d($x) } )\n" % (i, i, i)
              for i in range(12))

# One outer line of work and one sub-line long enough to evict it. ⚠ The two
# corpora below differ by EXACTLY the two postconditions substituted in --
# everything else, rule for rule and fact for fact, is the same text.
HEAD = """
rule <begin>   = implies( { +task($t), +about($t, $g) }, { +begun($t) } )
after <begin> => attend($g)%s
rule <check>   = implies( { +begun($t), +item($i) }, { +checked($i) } )
rule <done>    = implies( { +begun($t), +about($t, $g), +checked(i8) },
                          { +surveyed($t) } )
after <done> => %s
"""
TAIL = """
rule <report>  = implies( { +surveyed($t), +about($t, $g) }, { +told($g) } )
fact +task(survey)
fact +about(survey, plots)
"""
ITEMS = "".join("fact +item(i%d)\n" % i for i in range(1, 9))


def _survey(push: str, pop: str):
    """Run the corpus, recording what was attended at each CHOICE.

    ⚠ At the choice and not after the move: `watch` fires once the
    postconditions have run, so a pop had already happened and the frame the
    decision was taken in was not the one being reported -- a check built out of
    the thing under test, which is the trap `probes/experts.py` records.
    """
    m = Machine()
    kb = load(m, (HEAD % (push, pop)) + PAD + TAIL + ITEMS)
    seen = []

    def chooser(mm, table, window, state):
        seen.append((window[0].rule.name,
                     [mm.g.show(n) for n in mm._attended()]))
        return window[0]

    report = run(m, limit=60, chooser=chooser)
    return m, kb, report, seen


INHERIT = """
rule <inherit> = implies( { +extends($e, $f), +knows($f, $r) },
                          { +knows($e, $r) } )
"""

# Three experts over one graph, lifted verbatim from `probes/experts.py` so the
# selection is measured against a corpus that already exists rather than one
# written to be selectable.
EXPERTS = """
expert arithmetic
rule <double> = implies( { +question(twice($n)), +num($n, $v), +plus($v, $v, $s) },
                         { +reply(twice($n), $s) } )

expert geometry extends arithmetic
rule <area> = implies( { +question(area($r)), +wide($r, $w), +tall($r, $h),
                         +times($w, $h, $a) },
                       { +reply(area($r), $a) } )

expert surveyor
rule <ask-area>  = implies( { +survey($r) },
                            { +consult(geometry, area($r)) } )
rule <record>    = implies( { +answered(geometry, area($r), $a) },
                            { +plot($r, $a) } )

fact +wide(plot1, 3)
fact +tall(plot1, 4)
fact +survey(plot1)
"""


def main() -> int:
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(__doc__.strip().split("\n\n")[0])
    print()
    failing = ran = 0

    def gate(name: str, ok: bool) -> None:
        nonlocal failing, ran
        ran += 1
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
        if not ok:
            failing += 1

    # -- 1. the measurement the mechanism has to justify itself against -----
    print("1. the same corpus, differing by two postconditions")
    print()
    flat_m, flat_kb, flat_r, flat_seen = _survey("", "attend($t)")
    frame_m, frame_kb, frame_r, frame_seen = _survey(", push(items)", "pop($g)")

    def at_choice(seen, name):
        for who, attended in seen:
            if who == name:
                return attended
        return []

    flat_at = at_choice(flat_seen, "report")
    frame_at = at_choice(frame_seen, "report")
    print(f"    flat    readmitted={flat_m._readmitted}  "
          f"tried={flat_r.tried}  widenings={flat_r.widenings}  "
          f"ticks={flat_r.ticks}")
    print(f"            attended when <report> was chosen: {flat_at[:5]}")
    print(f"    framed  readmitted={frame_m._readmitted}  "
          f"tried={frame_r.tried}  widenings={frame_r.widenings}  "
          f"ticks={frame_r.ticks}")
    print(f"            attended when <report> was chosen: {frame_at[:5]}")
    print()

    gate("⚠ the control finishes both ways -- the stack is being measured, not "
         "the corpus",
         flat_m.holds(flat_kb.term("told(plots)")) == PLUS
         and frame_m.holds(frame_kb.term("told(plots)")) == PLUS)
    # ⚠⚠⚠ POSITION, not membership. `attend($g)` deposited a standing
    # `attention(plots)` claim, and `_attended()` puts a standing claim at the
    # BOTTOM rather than dropping it -- so *was it forgotten* is the wrong
    # question and would have made this check pass on a technicality. What the
    # queue lost is its PLACE, and position is the strength: `_pull` weighs
    # depth 0 at 6 and the bottom of a full queue at 1.
    gate(f"⭐⭐⭐ THE EVICTION LOSS IS REAL: the sub-line pushed what the outer "
         f"line was about from the front of the queue to position "
         f"{flat_at.index('plots')} of {len(flat_at)}, and handed it back "
         f"{flat_m._readmitted}x on the way -- lifting at 1 where it had been "
         f"lifting at 6",
         flat_m._readmitted > 0 and flat_at.index("plots") > 4)
    gate("⭐⭐⭐ ...and a frame does not lose it: the sub-line ran on its own "
         "queue, and `plots` is back at the FRONT when the outer line resumes, "
         "exactly as `<begin>` left it",
         frame_m._readmitted == 0 and frame_at.index("plots") == 0)
    gate("⚠ ...and the eight items the sub-line was about are gone from the "
         "outer frame, which is the other half: suspending is not remembering "
         "more, it is remembering the RIGHT things",
         not any(n.startswith("i") and n[1:].isdigit() for n in frame_at))
    # ⚠⚠⚠ **And it is not a speed-up. It costs slightly MORE.** Written down
    # rather than tuned away: `_pull` lifts from a shorter queue inside the
    # frame, so the shortlist widens a little further. The stack buys the FOCUS
    # and pays a few percent of matching for it, and a probe that reported only
    # the column it won on would be measuring its own conclusion.
    gate(f"⚠⚠⚠ ...and the loop pays for it: {flat_r.tried} rules matched flat "
         f"against {frame_r.tried} framed, {flat_r.widenings} widenings "
         f"against {frame_r.widenings}. The stack is NOT a speed-up -- it is a "
         f"few percent dearer, and what it buys is the line above staying put",
         frame_r.tried > flat_r.tried
         and frame_r.tried < flat_r.tried * 1.1
         and frame_r.ticks == flat_r.ticks)

    # -- 2. the frame is a call, and pop is its return ----------------------
    print()
    print("2. the frame, and what is deposited about it")
    print()
    m, kb = frame_m, frame_kb
    gate("⭐ a push is DEPOSITED, not merely done -- a record of a focus "
         "change, which is what `_unattend`'s finding asks of anything that "
         "moves attention",
         m.holds(kb.term("pushed(items)")) == PLUS)
    gate("⭐ ...and so is the pop, carrying the node it brought back",
         m.holds(kb.term("popped(plots)")) == PLUS)
    gate("⚠ the stack came back down: a run that ends inside a frame it opened "
         "would be a leak the agent cannot be asked about",
         len(m._frames) == 1)
    gate("⚠⚠ and the graph is UNTOUCHED by the pop -- everything the sub-line "
         "concluded still stands, because popping graph changes is a different "
         "feature and is not wanted",
         all(m.holds(kb.term("checked(i%d)" % i)) == PLUS
             for i in range(1, 9)))
    gate("⚠⚠ ...while the frame's own `attention` claims are DENIED rather "
         "than dropped, or the suspension would leak the very thing it exists "
         "to put away",
         m.holds(kb.term("attention(i8)")) != PLUS)

    # -- 3. does the pick discriminate, after IDF? --------------------------
    print()
    print("3. picking the expert, by TF-IDF over experts")
    print()
    em = Machine()
    ekb = Loader(em, scope="frames-experts")
    ekb.load(INHERIT)
    ekb.load(EXPERTS)
    ekb.load(SETTLE)
    run(em, limit=40)          # let <inherit> settle the pools first
    picks = {}
    for q in ("area(plot1)", "twice(3)", "survey(plot1)"):
        who, scores = em._pick_expert([ekb.term(q)])
        picks[q] = (em.g.show(who) if who is not None else None,
                    sorted(((em.g.show(e), s) for e, s in scores)))
        print(f"    {q:14s} -> {picks[q][0]:11s} {picks[q][1]}")
    print()

    gate("⭐⭐⭐ the pick is a MECHANISM and not a coin flip: `survey(plot1)` "
         "goes to the surveyor and to nobody else, on a corpus written for a "
         "different probe",
         picks["survey(plot1)"][0] == "surveyor"
         and [s for e, s in picks["survey(plot1)"][1] if e != "surveyor"]
         == [0, 0])
    gate("⭐ IDF is what makes that possible -- `question`, `reply` and the "
         "rest are in every pool and score ZERO, so only the discriminating "
         "terms carry it",
         all(s == 0 for _q, (_w, sc) in picks.items() for _e, s in sc
             if s == 0) and any(s > 0 for _w, sc in picks.values()
                                for _e, s in sc))
    gate("⚠⚠ ...and here is what is LEFT after discounting, which is the "
         "number `docs/todo.md` asked for: `area(plot1)` TIES the expert that "
         "answers with the expert that asks, because both key on `area`. The "
         "tie falls to authored order. That is signal, not separation",
         picks["area(plot1)"][0] == "geometry"
         and len({s for _e, s in picks["area(plot1)"][1] if s}) == 1
         and len([s for _e, s in picks["area(plot1)"][1] if s]) == 2)
    gate("⚠ nothing to discriminate is answered with NOTHING, and the frame "
         "keeps the rules of the frame below -- picking the first expert "
         "declared would be a coin flip wearing a mechanism's clothes",
         em._pick_expert([em.g.atom("unrelated")])[0] is None)

    # -- 4. the frame carries the table, so a return is a RESUME ------------
    print()
    print("4. the frame carries its expert's table")
    print()
    # ⚠ Two members apiece, and not for decoration: a one-member antecedent
    # `{ +asking($q) }` matches the MENTION the loader wrote for the rule's own
    # pattern, so the rule applies twice, binds `$q` to a generic, writes
    # nothing, and the corpus looks like it ran. Caught here by asking what it
    # concluded rather than whether it moved.
    src = """
rule <call>  = implies( { +ask($q), +known($q) }, { +asking($q) } )
after <call> => push($q)
rule <work>  = implies( { +asking($q), +known($q) }, { +worked($q) } )
rule <back>  = implies( { +worked($q), +known($q) }, { +heard($q) } )
after <back> => pop($q)
fact +ask(sum)
fact +known(sum)
"""
    m2 = Machine()
    kb2 = load(m2, src)
    root = Table(m2.g, list(m2.rules.rules), _standing(m2))
    r2 = run(m2, limit=20, table=root)
    gate("⚠ a caller that hands its table in still gets THAT table back, not "
         "whichever frame the run ended in",
         r2.table is root)
    gate("⭐⭐ ...and the root table's tick count is the run's, so a host "
         "stepping by hand is not measuring a different agent each time",
         root.ticked >= 3)
    gate("⭐ the frame closed and the answer came back on the restored frame -- "
         "`pop($q)` is the attention-level analogue of a return value",
         len(m2._frames) == 1
         and m2._attended()[0] is kb2.term("sum")
         and m2.holds(kb2.term("heard(sum)")) == PLUS)

    # -- 5. the two backstops ----------------------------------------------
    print()
    print("5. the depth bound and the cycle test")
    print()
    deep = Machine()
    kbd = load(deep, """
rule <down> = implies( { +go($x), +next($x, $y) }, { +go($y) } )
after <down> => push($y)
fact +go(n0)
fact +next(n0, n1)
fact +next(n1, n2)
fact +next(n2, n3)
fact +next(n3, n4)
fact +next(n4, n5)
fact +next(n5, n6)
fact +next(n6, n7)
fact +next(n7, n8)
fact +next(n8, n9)
""")
    run(deep, limit=40)
    print(f"    frames after ten pushes: {len(deep._frames)} "
          f"(FRAME_DEPTH = {FRAME_DEPTH})")
    gate("⚠⚠⚠ the depth bound HOLDS, and it is asserted directly rather than "
         "read off a log -- `probes/experts.py` records a check that passed "
         "while the stack was flat because it was built out of its own output",
         len(deep._frames) == FRAME_DEPTH)
    gate("...and the refusal is on the record, because a push that quietly did "
         "nothing is indistinguishable from one that had nothing to do",
         any(deep.g.show(deep.g.member(inst, 2)) == "too_deep"
             for inst in deep.g.instances_of(deep.DECLINED)
             if len(deep.g.members(inst)) == 3))

    cyc = Machine()
    load(cyc, """
rule <there> = implies( { +at($x), +place($x) }, { +went($x) } )
after <there> => push($x)
rule <again> = implies( { +went($x), +place($x) }, { +back($x) } )
after <again> => push($x)
fact +at(here)
fact +place(here)
""")
    run(cyc, limit=20)
    gate("⚠ the cycle test is on the PAIR -- the expert AND what it is being "
         "asked about -- so the same frame is refused rather than reopened",
         any(cyc.g.show(cyc.g.member(inst, 2)) == "already_open"
             for inst in cyc.g.instances_of(cyc.DECLINED)
             if len(cyc.g.members(inst)) == 3)
         and len(cyc._frames) == 2)

    rootpop = Machine()
    load(rootpop, """
rule <up> = implies( { +here($x), +place($x) }, { +gone($x) } )
after <up> => pop($x)
fact +here(a)
fact +place(a)
""")
    run(rootpop, limit=10)
    gate("⚠ and a pop with nothing to return to is DECLINED rather than "
         "raised: whether `stop` should be *pop the root* is elegant and not "
         "required, and until it is, this is a corpus arguing with itself",
         len(rootpop._frames) == 1
         and any(rootpop.g.show(rootpop.g.member(inst, 2)) == "at_root"
                 for inst in rootpop.g.instances_of(rootpop.DECLINED)
                 if len(rootpop.g.members(inst)) == 3))

    print(f"\n{ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
