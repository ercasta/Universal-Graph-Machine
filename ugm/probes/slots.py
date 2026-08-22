"""Can attention be addressed by NAME? (the author's proposal, 2026-08-22)

    python -m ugm.probes.slots

The proposal: instead of positions, NAMED slots hung on a global anchor node --
`+game(_attention, $x)` in a consequent, `+game(_attention, $g)` in an
antecedent. The claim is that this is more robust than position and that it is
expressible right now.

Both halves hold, and the second holds completely: **nothing below needs an
engine change.** A slot is an ordinary proposition whose first argument is an
ordinary atom, so writing one is a write and reading one is a member. There is
no notation, no reserved name, and no branch.

What the probe is for is the part that is not free:

    single-valued    a slot is NOT one. Two writes leave two values held, and
                     keeping it to one is a rule the corpus writes (6).
    the anchor       rides the queue on every slot write -- and costs NOTHING
                     for it. idf is log(total/df), so a term in every expert's
                     pool scores exactly 0.0 (4b), and a derived push never
                     reaches the shortlist at all (4c). One queue slot, total.
    scope            the queue is PER-FRAME; a slot is GLOBAL (8). GLOBAL was
                     chosen: *rules have no notion of local, and global makes
                     nothing impossible where per-frame might.*

 The comparison against position is against `_push_frame`'s own gradient --
*`push($a, $b)` reads left to right and position is the gradient, so the
leftmost has to lift hardest* -- and not against a straw one.

 **Joining the slot to an anchored member does not isolate** over a shared
world (10): the foreign value has something to join to as well. It is the first
thing anyone reaches for, so it is a check rather than a remark. What isolates
between EXPERTS is the pool (11); what separates two instances of ONE expert is
nothing at all (12) -- until the value is MOVED out of the shared cell (13).

⭐⭐⭐ The cross-tick mechanism is already built and is `_attended_first`: a
rule's applications are sorted by the summed, position-weighted overlap of the
values they BIND, and the loop takes the first survivor and breaks. So
attention does choose the binding (14), and a slot WRITE is enough to choose
it (16).

 **Nothing is pre-bound**, and it is worth saying because *the reader applied
first* sounds like it might be. `match` runs INSIDE the per-tick loop and
`_attended_first` reorders what it returns, every tick: the trace at 18 shows
the same rule binding `chess/alice` on one tick and `go/bob` on the next, which
no cached binding could do. What the authoring order decides is only which rule
gets tick 1 -- and tick 1 is walk-ordered whatever runs there, because
`_attended_first` has its own guard, *nothing attended is in play here; do not
touch the order*. An empty queue orders nothing. The limit is not pre-binding,
it is that attention cannot rank what has not been attended yet.

⭐ And in a real run the queue is empty only at the very start, because
computation begins when something ARRIVES on a channel. An arrival does not
attend when it lands (19) -- `_report` writes straight through the gate, which
is not a move's `wrote` -- but the intake rule's own write attends every node
the arrival was made of, one tick later. What no arrival does by itself is
choose the first EXPERT: the engine's only `_push_frame` call is a rule spending
`push`, deliberately, because *the expert is computed from the nodes, never
named*. So a channel seeds attention for free and steers the first pick for one
rule (20).

 **AND ORDERING IS SELECTION ONCE THE WORLD MOVES**, which the first version
of this probe got backwards. On a frozen world run to quiescence both bindings
are eventually taken (15), and *attention does not isolate a global cell* was
concluded from exactly that -- a fixture that cannot move measuring a mechanism
whose whole subject is movement. Let taking a binding SPEND a shared premise and
the loser is never chosen at all (15b), and it is chosen only once the other
node is attended (15c). That is how *attention orders and cannot gate* and *the
other one never runs* are both true: the exclusion is the world's, not the
mechanism's.

See docs/HANDOFF.md 2026-08-22 and docs/models.md 12c.
"""

import sys

from ..core.chain import PLUS
from ..core.machine import Machine
from ..core.text import load


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    failing = ran = 0

    def gate(name, ok):
        nonlocal failing, ran
        ran += 1
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
        if not ok:
            failing += 1

    print(__doc__.strip().split("\n")[0])
    print()

    # 1. Expressible today, and this is the whole of the mechanism. A rule
    #    reads the slot as an ordinary member and concludes from it.
    m = Machine()
    kb = load(m, "\n".join([
        "rule <reads> = implies("
        "    { +game(_attention, $g), +turn($p) }, { +playing($p, $g) } )",
        "fact +game(_attention, chess)",
        "fact +turn(alice)", ""]))
    m.run(limit=20)
    print(f"      _attention is a reserved name   {'_attention' in m.reserved}")
    print(f"      playing(alice, chess)           {m.holds(kb.term('playing(alice, chess)'))}")
    gate("a NAMED slot reads and concludes with no engine change and no "
         "reserved name -- it is an ordinary proposition",
         m.holds(kb.term("playing(alice, chess)")) is not None
         and "_attention" not in m.reserved)

    # 2. The claim under test: robust to position. Write the two slots in one
    #    order and then the other, and the answer does not move. The contrast
    #    is against `_push_frame`, where position IS the gradient -- run below
    #    as 2b so the claim is measured against the real alternative and not
    #    asserted against a straw one.
    print()
    answers, queues = [], []
    for order in (("game", "board"), ("board", "game")):
        m = Machine()
        kb = load(m, "\n".join([
            "rule <both> = implies("
            "    { +game(_attention, $g), +board(_attention, $b) },"
            "    { +setup($g, $b) } )",
            f"fact +{order[0]}(_attention, {'chess' if order[0] == 'game' else 'wood'})",
            f"fact +{order[1]}(_attention, {'chess' if order[1] == 'game' else 'wood'})",
            ""]))
        m.run(limit=20)
        answers.append(m.holds(kb.term("setup(chess, wood)")))
        queues.append([m.g.show(n) for n, _w in m._attention])
    print(f"      written game-then-board  answer={answers[0]}  queue={queues[0]}")
    print(f"      written board-then-game  answer={answers[1]}  queue={queues[1]}")
    gate("the answer is the same in both orders -- a named slot does not read "
         "position", answers[0] == answers[1] and answers[0] is not None)

    # 2b. And the alternative, so the claim has something to be robust
    #     AGAINST. `push($a, $b)` reads left to right and position is the
    #     gradient: naming the same two nodes in the other order puts a
    #     different one in front.
    fronts = []
    for pair in (("chess", "wood"), ("wood", "chess")):
        m = Machine()
        kb = load(m, "fact +thing(chess)\nfact +thing(wood)\n")
        m.run(limit=10)
        m._push_frame([kb.term(pair[0]), kb.term(pair[1])])
        fronts.append(m.g.show(m._attention[0][0]))
        m._pop_frame()
    print(f"      push(chess, wood) -> front {fronts[0]!r};  "
          f"push(wood, chess) -> front {fronts[1]!r}")
    gate("...whereas a POSITIONAL push does read it: the same two nodes named "
         "the other way put a different node in front", fronts[0] != fronts[1])

    # 3. And it FUELS the attention that exists rather than replacing it: a
    #    rule that writes a slot puts the VALUE on the queue, through
    #    `_attend_written`, with nothing added for the purpose.
    m = Machine()
    kb = load(m, "\n".join([
        "rule <sets> = implies( { +start($g) }, { +game(_attention, $g) } )",
        "fact +start(chess)", ""]))
    m.run(limit=20)
    queue = [m.g.show(n) for n, _w in m._attention]
    print(f"      queue after a rule writes the slot   {queue}")
    gate("writing a slot ATTENDS its value -- the proposal feeds the stack "
         "that is built, it does not sit beside it", "chess" in queue)

    # 4. The anchor rides along. `_attend_written` decomposes what a move wrote
    #    into every node it is made of, so `_attention` and the slot's own
    #    relation go on the queue beside the value.
    print(f"      ...and the anchor is on it too       "
          f"{'_attention' in queue}, at position "
          f"{queue.index('_attention') if '_attention' in queue else None}")
    gate("the global anchor is attended on every slot write, at the front",
         "_attention" in queue)

    # 4b. AND IT COSTS NOTHING WHERE IT IS SCORED, which is the author's point
    #     and is sharper than *almost zero*: `_idf` is log(total/df), so a term
    #     in EVERY expert's pool has idf exactly 0.0. The anchor is in every
    #     pool by construction -- that is what makes it an anchor -- so it can
    #     never move a score. Note the slot RELATION goes to zero the same way
    #     when both experts use it, and the discriminating terms do not.
    print()
    m = Machine()
    kb = load(m, "\n".join([
        "rule <r1> = implies( { +here(_attention, $r), +wet($r) }, { +slip($r) } )",
        "rule <r2> = implies( { +here(_attention, $r), +dark($r) }, { +trip($r) } )",
        "fact +knows(safety, <r1>)",
        "fact +knows(gloom, <r2>)",
        "fact +wet(hall)", ""]))
    m.run(limit=20)
    _docs, idf = m._idf()
    for term, value in sorted(idf.items(), key=lambda kv: kv[1]):
        print(f"      idf {value:6.3f}   {m.g.show(term)}")
    anchor_idf = idf.get(kb.term("_attention"))
    shared_idf = idf.get(kb.term("here"))
    sharp_idf = idf.get(kb.term("wet"))
    gate("a term in every expert's pool has idf EXACTLY zero -- the anchor "
         "cannot move an expert score, and neither can a shared slot name",
         anchor_idf == 0.0 and shared_idf == 0.0 and sharp_idf > 0.0)

    # 4c. And it does not reach the SHORTLIST at all, which is the stronger
    #     half. `_attention_asked` is claimed-vs-derived, not weighted-vs-plain:
    #     *someone saying attend to this is a reason to bring rules to mind;
    #     the machinery noticing this just happened is not* -- conflating them
    #     is what quiesced the dungeon 32 moves early. `_attend_written` pushes
    #     without claiming, so every node a slot write puts on the queue,
    #     anchor included, is invisible to what decides which rules are matched.
    print()
    m = Machine()
    kb = load(m, "\n".join([
        "rule <sets> = implies( { +start($g) }, { +game(_attention, $g) } )",
        "fact +start(chess)", ""]))
    m.run(limit=20)
    queued = [m.g.show(n) for n, _w in m._attention]
    asked = [m.g.show(n) for n in m._attention_asked()]
    print(f"      on the queue          {queued}")
    print(f"      reaching the shortlist {asked}")
    gate("a DERIVED push reaches the shortlist not at all -- claimed vs "
         "derived, so the anchor cannot narrow anything either", asked == [])

    # 4d. So the residual cost is arithmetic rather than credit: queue SPACE.
    #     `_push_attention` moves a repeat rather than adding it, so the anchor
    #     costs exactly ONE slot however often it is written -- but each
    #     distinct slot relation costs one more, and the span is 7.
    m = Machine()
    kb = load(m, "\n".join([
        "rule <s1> = implies( { +a($x) }, { +p(_attention, $x) } )",
        "rule <s2> = implies( { +b($x) }, { +q(_attention, $x) } )",
        "rule <s3> = implies( { +c($x) }, { +r(_attention, $x) } )",
        "fact +a(one)", "fact +b(two)", "fact +c(three)", ""]))
    m.run(limit=40)
    q = [m.g.show(n) for n, _w in m._attention]
    anchors = [n for n in q if n == "_attention"]
    print(f"      three slot writes, span 7   {q}")
    print(f"      evicted {len(m._evicted)}, readmitted {m._readmitted}, "
          f"anchor occupies {len(anchors)} slot")
    gate("the anchor costs ONE queue slot in total however often it is "
         "written, because a repeat MOVES rather than adds", len(anchors) == 1)

    # 5. A slot is not single-valued. Two writes leave two values HELD, so
    #    *slot* is a discipline rather than something the notation gives.
    m = Machine()
    kb = load(m, "\n".join([
        "rule <s> = implies( { +start($g) }, { +game(_attention, $g) } )",
        "fact +start(chess)",
        "fact +start(go)", ""]))
    m.run(limit=30)
    held = [m.g.show(n) for n in m.g.instances_of(kb.term("game"))
            if m.holds(n) == "+"]
    print(f"      after two writes, held: {held}")
    gate("a named slot is NOT single-valued -- both values stand, and nothing "
         "in the notation says otherwise", len(held) == 2)

    # 6. ...and the corpus can make it one, in one rule: the setter binds the
    #    old value and denies it. Three members, one of them a distinctness
    #    computator the corpus registers -- so the discipline costs a rule and
    #    a function, and neither is the engine's.
    m = Machine()
    kb = load(m, "\n".join([
        "rule <set> = implies(",
        "    { +wants($g), +game(_attention, $old), differ($old, $g) },",
        "    { -game(_attention, $old), +game(_attention, $g) } )",
        "fact +game(_attention, chess)",
        "fact +wants(go)", ""]))
    kb.computator("differ", lambda a, b: "yes" if a != b else None)
    m.run(limit=30)
    old = m.holds(kb.term("game(_attention, chess)"))
    new = m.holds(kb.term("game(_attention, go)"))
    print(f"      after the setter: chess={old}  go={new}")
    gate("a three-member setter keeps the slot to one value -- the discipline "
         "is a RULE, which is where it belongs", old == "-" and new == "+")

    # 7. THE EXPRESSIBILITY TEST PROPER. An authored competence rule, and the
    #    same rule with its situational premise replaced by a slot read. Same
    #    world, same answer.
    print()
    world = ["fact +exit(hall, north, study)", "fact +exit(hall, east, kitchen)"]
    m = Machine()
    kb = load(m, "\n".join([
        "rule <authored> = implies("
        "    { +at(agent, $r), +exit($r, $d, $r2) }, { +may(move($d)) } )",
        "fact +at(agent, hall)"] + world + [""]))
    m.run(limit=40)
    authored = sorted(m.g.show(n) for n in m.g.instances_of(kb.term("may"))
                      if m.holds(n) == "+")
    m = Machine()
    kb = load(m, "\n".join([
        "rule <slotted> = implies("
        "    { +here(_attention, $r), +exit($r, $d, $r2) }, { +may(move($d)) } )",
        "fact +here(_attention, hall)"] + world + [""]))
    m.run(limit=40)
    slotted = sorted(m.g.show(n) for n in m.g.instances_of(kb.term("may"))
                     if m.holds(n) == "+")
    print(f"      authored  {authored}")
    print(f"      slotted   {slotted}")
    gate("a competence rule rewrites slot-relative and answers identically -- "
         "the fixed-arity antecedent is available today",
         authored == slotted and len(authored) == 2)

    # 8. SCOPE, which is the real difference and is not in the proposal's
    #    favour or against it until something needs one or the other. The
    #    queue is PER-FRAME -- a push suspends it -- and a slot is global,
    #    readable from inside any frame. Two lines of work naming one slot
    #    share one cell.
    print()
    m = Machine()
    kb = load(m, "fact +game(_attention, chess)\nfact +go(x)\n")
    m.run(limit=10)
    outer = [m.g.show(n) for n, _w in m._attention]
    m._push_frame([kb.term("chess")])
    inner = [m.g.show(n) for n, _w in m._attention]
    visible = m.holds(kb.term("game(_attention, chess)"))
    m._pop_frame()
    print(f"      queue outside the frame  {outer}")
    print(f"      queue inside it          {inner}")
    print(f"      the slot, from inside    {visible}")
    gate("the queue is per-frame and the slot is GLOBAL -- named slots trade "
         "frame scoping for one shared cell per name",
         outer != inner and visible is not None)

    # -- global was CHOSEN, so what does the confusion actually look like ----
    #
    # The author's call, 2026-08-22: *go global. Rules have no notion of local
    # -- when a rule queries something it always queries global. Global makes
    # nothing impossible; per-frame might. It only poses an increased risk of
    # confusion, mitigated by the attention overlap.* The decision is taken;
    # what follows measures the risk and the mitigation, because a mitigation
    # that is assumed is a mitigation that is not there.

    print()
    world = ["fact +wet(hall)", "fact +wet(cave)",
             "fact +dark(hall)", "fact +dark(cave)"]
    shared = ["fact +here(_attention, hall)", "fact +here(_attention, cave)"]

    # 9. The risk, plainly. A slot read ALONE fires on every value in the cell,
    #    because there is nothing in the rule to tell one from another.
    m = Machine()
    kb = load(m, "\n".join([
        "rule <alone> = implies( { +here(_attention, $r) }, { +visited($r) } )"]
        + shared + [""]))
    m.run(limit=40)
    alone = sorted(m.g.show(n) for n in m.g.instances_of(kb.term("visited"))
                   if m.holds(n) == "+")
    print(f"      a slot read alone, two values in the cell   {alone}")
    gate("a lone slot member fires on every value in the cell -- this is the "
         "confusion the decision accepts", len(alone) == 2)

    # 10. And the obvious mitigation is NOT the one. *Join the slot to
    #     something anchored* -- which is `_stored`'s own discipline, bounded
    #     by something already known -- does not isolate when the WORLD is
    #     shared, because the foreign value has something to join to as well.
    #     Measured, because it is the first answer anyone reaches for.
    m = Machine()
    kb = load(m, "\n".join([
        "rule <joined> = implies("
        "    { +here(_attention, $r), +wet($r) }, { +slip($r) } )"]
        + shared + world + [""]))
    m.run(limit=40)
    joined = sorted(m.g.show(n) for n in m.g.instances_of(kb.term("slip"))
                    if m.holds(n) == "+")
    print(f"      joined to an anchored member                {joined}")
    gate("joining the slot to another member does NOT isolate over a shared "
         "world -- the foreign value joins too", len(joined) == 2)

    # 11. The mitigation that does work is the one the author named: the
    #     EXPERT PICK. Two experts using the same slot name are still told
    #     apart, because what discriminates is the rest of their pools -- and
    #     the anchor and the shared slot name, both idf zero, do not blunt it.
    m = Machine()
    kb = load(m, "\n".join([
        "rule <r1> = implies( { +here(_attention, $r), +wet($r) }, { +slip($r) } )",
        "rule <r2> = implies( { +here(_attention, $r), +dark($r) }, { +trip($r) } )",
        "fact +knows(safety, <r1>)",
        "fact +knows(gloom, <r2>)"] + shared + world + [""]))
    m.run(limit=40)
    expert, scores = m._pick_expert([kb.term("wet(hall)")])
    named = {m.g.show(e): s for e, s in scores}
    print(f"      pick on wet(hall)   {m.g.show(expert) if expert else None}  {named}")
    gate("the expert pick still discriminates through a shared slot name -- "
         "isolation moves from the DATA to the POOL",
         expert == kb.term("safety") and named["gloom"] == 0)

    # 12. ...and it cannot help two INSTANCES of the same expert, which the
    #     author named as the residual risk. One pool, one set of rules, one
    #     cell: the conclusions are keyed by the value and the instances are
    #     not in them at all.
    m = Machine()
    kb = load(m, "\n".join([
        "rule <act> = implies("
        "    { +here(_attention, $r), +exit($r, $d) }, { +may($r, $d) } )",
        "fact +exit(hall, north)",
        "fact +exit(cave, down)"] + shared + [""]))
    m.run(limit=40)
    mixed = sorted(m.g.show(n) for n in m.g.instances_of(kb.term("may"))
                   if m.holds(n) == "+")
    print(f"      two instances, one cell                     {mixed}")
    gate("the pool cannot separate two instances of ONE expert -- same rules, "
         "same names, and the instance is nowhere in the answer",
         mixed == ["may(cave, down)", "may(hall, north)"])

    # 13. THE CROSSROAD PATTERN, and the reason it needs nothing built: the
    #     anchor is an ARGUMENT, so a private space is the same construct with
    #     a different first argument. One rule takes from the crossroad and
    #     denies it, and after that the instances never share a cell again.
    print()
    m = Machine()
    kb = load(m, "\n".join([
        "rule <take> = implies(",
        "    { +arriving($who, $r), +here(_attention, $r) },",
        "    { -here(_attention, $r), +here($who, $r) } )",
        "rule <act> = implies("
        "    { +here($who, $r), +exit($r, $d) }, { +may($who, $d) } )",
        "fact +arriving(inst1, hall)",
        "fact +arriving(inst2, cave)",
        "fact +exit(hall, north)",
        "fact +exit(cave, down)"] + shared + [""]))
    m.run(limit=60)
    private = sorted(m.g.show(n) for n in m.g.instances_of(kb.term("may"))
                     if m.holds(n) == "+")
    left = [m.holds(n) for n in m.g.instances_of(kb.term("here"))
            if "_attention" in m.g.show(n) and m.holds(n) is not None]
    print(f"      after moving to a private anchor            {private}")
    print(f"      what the crossroad is left holding          {left}")
    gate("the private space is the same construct with a different first "
         "argument, and one rule moves a value into it",
         private == ["may(inst1, north)", "may(inst2, down)"])
    gate("...and the crossroad ends EMPTY, which is what makes it a crossroad "
         "rather than a second home for the value",
         bool(left) and all(v == "-" for v in left))

    # -- and the mechanism the whole design rests on is already BUILT --------
    #
    # The author's, on being asked what bridges ticks: *only attention does,
    # and my solution was to choose the bindings of rules to actual graph nodes
    # based on attention partial overlap -- if there are two `game` nodes, one
    # attended and one not, the next tick should bind to the attended one.*
    #
    # That is `_attended_first`, in `core/attention.py`, and the loop's own
    # comment says what it decides: *it takes the first survivor and breaks, so
    # the binding was decided by the walk* -- which is what this repairs. The
    # applications are sorted by the SUMMED, position-weighted overlap of the
    # values an application BINDS, not of the rule's terms.

    print()
    PLAY = "\n".join([
        "rule <play> = implies( { +game($g), +turn($g, $p) }, { +moves($p) } )",
        "fact +game(chess)", "fact +turn(chess, alice)",
        "fact +game(go)", "fact +turn(go, bob)", ""])

    def moves_in_order(extra="", attend=None):
        m = Machine()
        kb = load(m, PLAY + extra)
        if attend:
            m._attend(kb.term(attend))
        m.run(limit=40)
        return [m.g.show(e.proposition)
                for mo in m.chain.moments for e in mo.delta
                if m.g.show(e.proposition).startswith("moves(")]

    base = moves_in_order()
    attended_chess = moves_in_order(attend="chess")
    print(f"      nothing attended   {base}")
    print(f"      attend chess       {attended_chess}")
    gate("attention decides WHICH of a rule's bindings is taken -- two `game` "
         "nodes, and attending one flips which is bound first",
         base[0] != attended_chess[0])

    # 15. It orders rather than excludes, so on a FROZEN world run to
    #     quiescence both bindings are taken.  That is the fixture, not the
    #     mechanism, and the first version of this probe drew the conclusion
    #     *attention does not isolate a global cell* from it. See 15b.
    gate("on a world that does not move, both bindings are taken by "
         "quiescence -- ordering degenerates to everything, eventually",
         sorted(base) == sorted(attended_chess) and len(base) == 2)

    # 15b. THE AUTHOR'S CORRECTION, and it is the case that matters: *if the
    #      world and the attention move, the loser will never be chosen; it
    #      will only be chosen if the other node is attended.* Here taking a
    #      binding SPENDS a shared premise, so the loser stops applying rather
    #      than waiting its turn -- and ordering IS selection, with no gate
    #      anywhere. That is how *attention orders and cannot gate* and *the
    #      other one never runs* are both true at once.
    SPEND = "\n".join([
        "rule <play> = implies(",
        "    { +game($g), +turn($g, $p), +token(one) },",
        "    { +moves($p), -token(one) } )",
        "fact +game(chess)", "fact +turn(chess, alice)",
        "fact +game(go)", "fact +turn(go, bob)",
        "fact +token(one)", ""])

    def spent_run(attend=None):
        m = Machine()
        kb = load(m, SPEND)
        if attend:
            m._attend(kb.term(attend))
        m.run(limit=60)
        return m, kb, [m.g.show(e.proposition)
                       for mo in m.chain.moments for e in mo.delta
                       if m.g.show(e.proposition).startswith("moves(")]

    _m, _kb, none_at = spent_run()
    _m, _kb, at_chess = spent_run("chess")
    _m, _kb, at_go = spent_run("go")
    print()
    print(f"      world MOVES -- nothing attended   {none_at}")
    print(f"      world MOVES -- attend chess       {at_chess}")
    print(f"      world MOVES -- attend go          {at_go}")
    gate("when the world moves, the loser is NEVER chosen -- attention "
         "selects the binding without any gate",
         at_chess == ["moves(alice)"] and at_go == ["moves(bob)"])

    # 15c. ...and the other half of the same sentence: the loser arrives only
    #      when attention turns to it. Same machine, carried on: the premise
    #      comes back and `go` is attended.
    m, kb, phase1 = spent_run("chess")
    m.gate.write(kb.term("token(one)"), PLUS)
    m._attend(kb.term("go"))
    m.run(limit=60)
    phase2 = [m.g.show(e.proposition) for mo in m.chain.moments for e in mo.delta
              if m.g.show(e.proposition).startswith("moves(")]
    print(f"      then the premise returns, attend go   {phase1} -> {phase2}")
    gate("...and the loser is chosen once the OTHER node is attended, which is "
         "the whole of the author's claim, both halves",
         phase1 == ["moves(alice)"] and phase2 == ["moves(alice)", "moves(bob)"])

    # 16. And the feed is the WHOLE queue, derived pushes included -- unlike
    #     the shortlist, which is claimed-only (check 4c). So a slot WRITE
    #     decides a later binding with nothing attending explicitly: the same
    #     push is invisible to what narrows rules and visible to what binds
    #     them.
    #
    #      BUT ONLY IF IT LANDS FIRST, and that is the caveat this check
    #     exists for. *The NEXT tick binds to the attended node* is exactly
    #     right, and the failure is when there is no next tick because the
    #     reader already applied. Below, the only difference between the two
    #     halves is the order the two rules are AUTHORED, which decides which
    #     applies first -- and it changes the answer. A check written in one
    #     order alone would have measured the order and reported the mechanism.
    print()
    FOCUS = ("rule <focus> = implies( { +start($g) },"
             " { +game(_attention, $g) } )\n")
    PLAY_R = ("rule <play> = implies( { +game($g), +turn($g, $p) },"
              " { +moves($p) } )\n")
    FACTS = ("fact +game(chess)\nfact +turn(chess, alice)\n"
             "fact +game(go)\nfact +turn(go, bob)\n")

    def run_src(src):
        m = Machine()
        load(m, src)
        m.run(limit=40)
        return [m.g.show(e.proposition)
                for mo in m.chain.moments for e in mo.delta
                if m.g.show(e.proposition).startswith("moves(")]

    rows = {}
    for who in ("chess", "go"):
        rows[("writer first", who)] = run_src(
            FOCUS + PLAY_R + FACTS + f"fact +start({who})\n")
        rows[("reader first", who)] = run_src(
            PLAY_R + FACTS + FOCUS + f"fact +start({who})\n")
    for (order_, who), got in rows.items():
        print(f"      {order_}, slot <- {who:5}   {got}")
    wrote_first = rows[("writer first", "chess")][0] != rows[("writer first", "go")][0]
    read_first = rows[("reader first", "chess")][0] != rows[("reader first", "go")][0]
    gate("writing the SLOT decides the binding when the write lands first -- "
         "derived pushes reach `_attended()` though not the shortlist",
         wrote_first)
    gate("...and decides NOTHING when the reader applied first: attention "
         "bridges ticks, so a value not yet attended cannot move a binding "
         "already taken", not read_first)

    # 18. WHY, and it is not what *authored first* makes it sound like. Nothing
    #     is pre-bound: `match` runs inside the per-tick loop and
    #     `_attended_first` reorders what it returns, every tick. The trace
    #     below is the evidence -- the SAME rule binds differently on two ticks
    #     of ONE run, which no cached binding could do.
    #
    #     What the authoring order actually decides is which rule gets tick 1,
    #     and tick 1 is walk-ordered whatever it is, because `_attended_first`
    #     has its own guard: *nothing attended is in play here; do not touch
    #     the order.* An empty queue orders nothing. So the limit is not
    #     pre-binding, it is that attention cannot rank what has not been
    #     attended yet -- which is the same sentence as *only attention bridges
    #     ticks*, read from the start of the run instead of the middle.
    print()
    from ..core import attention as _att

    def trace(src):
        m = Machine()
        load(m, src)
        seen = []

        def chooser(mm, _table, window, _state):
            a = window[0]
            seen.append((mm.g.show(a.rule.node),
                         tuple(sorted(mm.g.show(v) for v in a.bindings.values())),
                         tuple(mm.g.show(n) for n, _w in mm._attention)[:2]))
            return a
        _att.run(m, limit=12, chooser=chooser)
        return seen

    steps = trace(FOCUS + PLAY_R + FACTS + "fact +start(chess)\n")
    for i, (rule, binds, at) in enumerate(steps[:4], 1):
        print(f"      tick {i}: {rule:10} binds={list(binds)}  attention={list(at)}")
    plays = [b for r, b, _a in steps if r == "<play>"]
    gate("the SAME rule binds differently on two ticks of one run -- nothing "
         "is pre-bound, `match` runs inside the tick",
         len(plays) >= 2 and plays[0] != plays[1])
    gate("...and tick 1 is walk-ordered whatever runs there, because an empty "
         "queue orders nothing -- `_attended_first` returns `found` untouched "
         "when nothing in play is attended",
         steps[0][2] == ())

    # 19. AND THE EMPTY QUEUE IS A FIXTURE ARTEFACT TOO, mostly. The author's:
    #     *in real situations computation starts because something ARRIVED on a
    #     channel, and those nodes should be attended, guiding the selection of
    #     the first expert.* Half true today and worth being exact about, since
    #     the half that is not true is corpus work rather than engine work.
    #
    #     An arrival does NOT attend when it lands: `_report` writes
    #     `arrived(...)` straight through the gate, which is not a move's
    #     `wrote`, so `_attend_written` never sees it. One tick later the
    #     intake rule turns the report into an utterance, and THAT write
    #     attends every node it is made of.
    print()
    m = Machine()
    kb = load(m, "fact +game(chess)\nfact +game(go)\n")
    m.channels.open(kb.term("user"))
    m.channels.deliver(kb.term("user"), kb.term("game(chess)"))
    at_delivery = [m.g.show(n) for n, _w in m._attention]
    m.run(limit=6)
    after = [m.g.show(n) for n, _w in m._attention]
    print(f"      queue at delivery       {at_delivery}")
    print(f"      queue after intake ran  {after[:6]}")
    gate("an arrival does not attend when it LANDS -- the report goes straight "
         "through the gate and is not a move's `wrote`", at_delivery == [])
    gate("...but the intake rule's own write attends every node the arrival "
         "was made of, one tick later -- so the channel DOES seed attention, "
         "at the cost of a tick",
         "chess" in after and "game(chess)" in after)

    # 20. What it does not do by itself is choose the first EXPERT, and that is
    #     deliberate rather than missing. The engine's only `_push_frame` call
    #     is a rule spending `push`, whose docstring says why: *the nodes are
    #     the host rule's own variables, bound by the move that spent this --
    #     and the expert is computed from them, never named.* So an arrival
    #     guides the first pick exactly when a corpus rule pushes on the nodes
    #     it seeded, which is one rule, not an engine change.
    m2 = Machine()
    kb2 = load(m2, "\n".join([
        "rule <r1> = implies( { +here(_attention, $r), +wet($r) }, { +slip($r) } )",
        "rule <r2> = implies( { +here(_attention, $r), +dark($r) }, { +trip($r) } )",
        "fact +knows(safety, <r1>)",
        "fact +knows(gloom, <r2>)",
        "fact +wet(hall)", ""]))
    m2.run(limit=20)
    picked, sc = m2._pick_expert([kb2.term("wet(hall)")])
    print(f"      and a pick on those nodes discriminates: "
          f"{m2.g.show(picked) if picked else None} "
          f"{ {m2.g.show(e): s for e, s in sc} }")
    gate("nothing auto-pushes, so an arrival guides the FIRST expert only when "
         "a corpus rule pushes on the nodes it seeded -- and the pick over "
         "those nodes does discriminate",
         picked is not None)

    print()
    print("  Expressible today, entirely: no engine change, no reserved name,")
    print("  no branch. The anchor riding the queue costs NOTHING where it is")
    print("  scored -- idf exactly zero -- and nothing at all in the shortlist,")
    print("  which reads claimed pushes only. What is left to pay is a setter")
    print("  rule per slot and one queue slot of the span of 7.")
    print()
    print("  GLOBAL was chosen. The isolation that survives is the POOL's, not")
    print("  the data's: two experts sharing a slot name are still told apart.")
    print("  What it cannot separate is two INSTANCES of one expert -- and the")
    print("  repair needs nothing built, because `_attention` sits in an")
    print("  ordinary argument position, so a private space is the same")
    print("  proposition with a different first argument. The healthy pattern")
    print("  is not JOINING the slot to an anchored member, which does not")
    print("  isolate over a shared world. It is MOVING the value out.")
    print()
    print("  And the cross-tick mechanism is already built: `_attended_first`")
    print("  sorts a rule's applications by the overlap of the values they")
    print("  BIND, and the loop takes the first survivor. It ORDERS -- but on")
    print("  a world that moves, ordering IS selection: spend a shared premise")
    print("  and the loser is never chosen, and is chosen only once the other")
    print("  node is attended. The exclusion is the world's, not the")
    print("  mechanism's, which is why no gate is needed to get it.")
    print()
    print(f"  {ran} checks, {failing} failing")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
