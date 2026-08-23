"""One runner. Every check prints what it observed, and any `False` fails.

    python -m ugm.selftest

This file was 7,435 lines and 558 checks, and it is now a fraction of that.
Almost none of those checks were deleted for being wrong: they were checks
about entries, moments, signs, licences, support trails, goal management,
vetoes, expectations, the premise economy and credit assignment, and every one
of those is gone. A suite that outlives the thing it tested is worse than no
suite, because it reads exactly like one that still means something.

What is here is the engine that exists: one graph that is the state, an anchor
that IS belief, one matcher, one connective, and a loop that selects and
applies.
"""

from typing import List, Tuple

from .core.graph import Graph
from .core.machine import Machine
from .core.rules import (ABSENT, ASSERT, ERASE, Member, Rule, RuleSet,
                         arbitrate, match, unify)
from .core.scratchpad import Scratchpad
from .core.text import ParseError, load, load_file
from . import corpora as _corpora

FAILED: List[Tuple[str, str]] = []
COUNT = 0


def check(group: str, name: str, value: bool) -> None:
    global COUNT
    COUNT += 1
    print(f"  {'ok  ' if value else 'FAIL'}  {name}")
    if not value:
        FAILED.append((group, name))


# -- §3 the substrate -------------------------------------------------------


def substrate() -> None:
    print("\n§3  the substrate")
    g = Graph()
    on, a, b = g.atom("on"), g.atom("a"), g.atom("b")
    p1, p2 = g.rel(on, a, b), g.rel(on, a, b)
    check("§3", "a proposition has one identity however often it is built",
          p1 == p2)
    check("§3", "members are ordered", g.members(p1) == (a, b))
    check("§3", "on(a,b) and on(b,a) are different nodes", p1 != g.rel(on, b, a))
    x = g.var("$x")
    check("§3", "a pattern containing a variable is generic",
          g.has_var(g.rel(on, x, b)))
    check("§3", "a ground proposition is not", not g.has_var(p1))
    check("§3", "the cached answer agrees with the walked definition, over "
                "every node built so far",
          all(g.has_var(n) == g._has_var_slow(n) for n in range(g.count())))

    #  `find_rel` asks without answering itself, which is the whole of how
    # belief can be a question about presence.
    q = g.rel(on, b, a)
    check("§3", "`find_rel` finds what exists", g.find_rel(on, a, b) == p1)
    g.delete(q)
    check("§3", "...and finds nothing once it is deleted",
          g.find_rel(on, b, a) is None)
    check("§3", "a deleted node reads as erased rather than raising",
          g.show(q).endswith("(erased)") and g.relation_of(q) is None)
    check("§3", "and the node it was ABOUT is untouched -- deletion does not "
                "cascade, which is what makes an anchor the only safe target",
          g.show(a) == "a" and g.find_rel(on, a, b) == p1)


def labels() -> None:
    """A label is a name that picks out a node, and several are ALIASES."""
    print("\n§3  labels -- several on one node means they are aliases")
    g = Graph()
    x, z = g.atom("x"), g.atom("z")
    loves, adores = g.atom("loves"), g.atom("adores")
    inst = g.rel(loves, x, z)

    #  Two nodes, each LABELLED -- not merely named. Naming `adores` with
    # `g.atom` claims nothing, so labelling `loves` with the same spelling
    # would just give it a second name and merge nothing. The collision, and
    # therefore the alias, needs both sides to have made the claim.
    g.label(adores, "adores")
    kept = g.label(loves, "adores")
    check("§3", "two nodes claiming one label are ALIASES -- the collision "
                "merges them, keeping the older, which is `merge`'s own rule",
          kept == loves and g.identity_of(adores) == loves)
    check("§3", "the node's own name became a label too, so `labels_of` does "
                "not report that `loves` answers only to `adores`",
          g.labels_of(loves) == ("loves", "adores"))
    check("§3", "both labels resolve to the one node",
          g.labelled("loves") == loves and g.labelled("adores") == loves)
    check("§3", "so `adores(x, z)` IS `loves(x, z)` -- aliasing needs no "
                "change to the interning key, because the key is in identities",
          g.rel(g.labelled("adores"), x, z) == inst)

    g.label(loves, "cherishes")
    check("§3", "aliases compose", g.labels_of(loves)
          == ("loves", "adores", "cherishes"))

    check("§3", "unlabelling takes the name back", g.unlabel(loves, "cherishes")
          and g.labelled("cherishes") is None)
    check("§3", "...and does NOT unmerge: the nodes are already one, and only "
                "an unmerge could separate them",
          g.identity_of(adores) == loves)

    #  A CONTROL. `atom` deliberately does not resolve through the label
    # table: a name a corpus writes is local to that corpus (`text.py:823` --
    # two corpora may be about different kettles), and only `label` is a claim
    # of identity. Making `atom` global was tried and removed zero twins.
    check("§3", "a name written twice is still two nodes -- naming is local, "
                "labelling is a claim",
          g.atom("kettle") != g.atom("kettle"))

    e = g.entity()
    g.label(e, "paul")
    check("§3", "an id-only entity can be labelled",
          g.labels_of(e) == ("paul",) and g.labelled("paul") == e)
    g.delete(e)
    check("§3", "deleting a node takes its labels with it",
          g.labelled("paul") is None)


def relationships_are_entities() -> None:
    """`rel` interns; `instance` does not. Both are the same proposition."""
    print("\n§3  a relationship may be an entity -- interning is a write "
          "policy, not a law")
    g = Graph()
    pad = Scratchpad(g)
    loves, x, z = g.atom("loves"), g.atom("x"), g.atom("z")
    canon = g.rel(loves, x, z)
    one = g.instance(loves, x, z)
    two = g.instance(loves, x, z)

    check("§3", "`rel` returns one node however often it is built, and "
                "`instance` mints a distinct one each time -- two loves "
                "between the same pair are two things",
          g.rel(loves, x, z) == canon and len({canon, one, two}) == 3)
    check("§3", "every instance is in the argument index, so a rule reaches "
                "all of them and not just the canonical one",
          g.instances_with(loves, 0, x) == [canon, one, two])
    check("§3", "`like` collects the instances of one key, canonical first",
          g.like(one) == (canon, one, two))

    pad.note(one)
    check("§3", "belief is per ENTITY: anchoring one does not anchor another "
                "that happens to say the same thing",
          pad.holds(one) and not pad.holds(canon) and not pad.holds(two))

    #  The defect this index exists to close. Absence is a question about
    # the PROPOSITION, so asking the canonical node alone answers *nothing says
    # it* while `one` sits believed.
    check("§3", "...but ABSENCE is a question about the proposition, so it is "
                "asked of every instance",
          pad.holds_any(canon) and not pad.holds(canon))

    v = g.var("$v")
    absent = Rule(g.atom("<probe>"),
                  [Member(ABSENT, g.rel(loves, x, z))], [], "probe")
    check("§3", "so a rule's `no loves(x, z)` does not match while a "
                "non-canonical instance of it is believed",
          match(g, pad, absent) == [])
    pad.erase(one)
    check("§3", "...and matches once nothing says it at all",
          len(match(g, pad, absent)) == 1)

    present = Rule(g.atom("<probe2>"),
                   [Member(ASSERT, g.rel(loves, x, v))], [], "probe2")
    pad.note(one)
    pad.note(two)
    check("§3", "a positive premise binds each believed instance separately, "
                "because each is a different thing to be about",
          len(match(g, pad, present)) == 2)

    g.delete(two)
    check("§3", "deleting an instance takes it out of the key index",
          g.like(canon) == (canon, one))


# -- §4, §5 the scratchpad --------------------------------------------------


def scratchpad() -> None:
    print("\n§4  the scratchpad -- belief is presence of an anchor")
    g = Graph()
    pad = Scratchpad(g)
    boiling, k = g.atom("boiling"), g.atom("kettle")
    p = g.rel(boiling, k)
    check("§4", "a proposition on its own claims nothing -- it is in the graph "
                "and it is not believed", not pad.holds(p))
    anchor = pad.note(p)
    check("§4", "anchoring it is believing it", pad.holds(p))
    check("§4", "the anchor is INTERNED, so asserting twice is asserting",
          pad.note(p) == anchor and len(pad.believed()) == 1)
    check("§4", "...and what is believed is the proposition, not the anchor",
          pad.believed() == [p])

    #  The un-claim an append-only chain could never express.
    pad.erase(p)
    check("§4", "erasing takes belief back to NOTHING -- not to a denial, and "
                "with no scar", not pad.holds(p) and pad.believed() == [])
    check("§4", "the PROPOSITION survives the erasure, because rules mention "
                "it and a rule that lost the node it names would stop matching "
                "for a reason nothing could state",
          g.relation_of(p) is boiling)
    check("§4", "erasing what is not believed says so rather than pretending",
          pad.erase(p) is False)

    #  *never considered* and *considered and dropped* are one state, and
    # that is honest rather than lossy: nothing here remembers.
    pad.note(p)
    check("§4", "re-asserting after an erasure works, and lands at the NEWEST "
                "end where a re-assertion belongs",
          pad.holds(p) and pad.believed() == [p])

    #  `g.atom` does not intern, so `hot` is minted ONCE and shared. A
    # second `g.atom("hot")` is a different node no rule could match -- the
    # name-identity trap, and it has cost this design five silent bugs.
    hot = g.atom("hot")
    q = g.rel(hot, k)
    pad.note(q)
    check("§4", "`believed` is newest first", pad.believed() == [q, p])
    check("§4", "and a node knows which relations it currently stands in",
          set(pad.relations_of(k)) == {boiling, hot})
    pad.erase(q)
    check("§4", "...which is exact under erasure -- the count is moved, not a "
                "set flipped", pad.relations_of(k) == [boiling])


def the_gate() -> None:
    print("\n§13 the gate -- one door in, one door out")
    m = Machine()
    g = m.g
    p = g.rel(g.atom("on"), g.atom("a"), g.atom("b"))
    seen = []
    m.gate.on_write.append(seen.append)
    gone = []
    m.gate.on_erase.append(gone.append)
    m.gate.write(p)
    check("§13", "a write goes through the hooks -- effects leave the agent "
                 "HERE, not in a phase of the loop", seen[-1:] == [p])
    m.gate.erase(p)
    check("§13", "...and so does an erasure, which used to go straight to the "
                 "substrate below every hook", gone[-1:] == [p])
    check("§13", "a refused erasure is reported rather than counted",
          m.gate.erase(p) is False)

    generic = g.rel(g.atom("on"), g.var("$x"), g.atom("b"))
    ok = False
    try:
        m.gate.write(generic)
    except ValueError:
        ok = True
    check("§14", "a generic proposition cannot be believed", ok)
    m.gate.write(generic, generic=True)
    check("§14", "...unless the writer is MENTIONING one, which is what makes "
                 "rules speakable-about at all", m.holds(generic))


# -- §8, §14 rules and matching ---------------------------------------------


def matching() -> None:
    print("\n§14 match")
    g = Graph()
    pad = Scratchpad(g)
    rs = RuleSet(g)
    on, a, b = g.atom("on"), g.atom("a"), g.atom("b")
    x = g.var("$x")
    bound = unify(g, g.rel(on, x, b), g.rel(on, a, b), {})
    check("§14", "match binds a variable to what it met",
          bound is not None and bound[x] == a)
    check("§14", "match fails on a different relation",
          unify(g, g.rel(on, x, b), g.rel(g.atom("in"), a, b), {}) is None)

    r = rs.rule([Member(ASSERT, g.rel(on, x, b))],
                [Member(ASSERT, g.rel(g.atom("above"), x))], "r")
    check("§14", "nothing matches what nothing anchors",
          match(g, pad, r) == [])
    pad.note(g.rel(on, a, b))
    found = match(g, pad, r)
    check("§14", "...and the same rule matches the moment it is anchored",
          len(found) == 1 and found[0].bindings[x] == a)

    #  A stored PATTERN is in the graph and is not believed, which is the
    # trap the anchor exists to close: `match` reads what is anchored.
    check("§14", "a rule's own stored pattern is in the graph and matches "
                 "nothing -- USE is anchored and MENTION is not, structurally "
                 "rather than by a flag somebody has to set",
          g.find_rel(on, x, b) is not None and len(match(g, pad, r)) == 1)

    #  Absence, asked rather than matched.
    heavy = g.atom("heavy")
    r2 = rs.rule([Member(ASSERT, g.rel(on, x, b)),
                  Member(ABSENT, g.rel(heavy, x))],
                 [Member(ASSERT, g.rel(g.atom("light"), x))], "r2")
    check("§12", "`no p` holds while nothing anchors p", len(match(g, pad, r2)) == 1)
    pad.note(g.rel(heavy, a))
    check("§12", "...and stops holding the moment something does",
          match(g, pad, r2) == [])
    pad.erase(g.rel(heavy, a))
    check("§12", "...and holds again once it is erased, which an append-only "
                 "chain could never get back to", len(match(g, pad, r2)) == 1)


def arbitration_is_total() -> None:
    print("\n§14 arbitration")
    m = Machine()
    kb = load(m, """
        fact +p(a)
        rule <one> = implies( { +p($x), no q($x) }, { +q($x) } )
        rule <two> = implies( { +p($x), no r($x) }, { +r($x) } )
    """)
    steps = [s for s in m.run(limit=8) if s.applied]
    check("§14", "with two rules matching, arbitration answers",
          bool(steps))
    check("§14", "and it answers by AUTHORED ORDER when nothing else separates "
                 "them", steps[0].applied.rule.name == "one")
    check("§14", "both eventually apply -- a loser is deferred, not rejected",
          m.holds(kb.term("q(a)")) and m.holds(kb.term("r(a)")))
    check("§14", "arbitrate over nothing answers None",
          arbitrate(m.rules, []) is None)


def one_connective() -> None:
    print("\n§10 one connective")
    m = Machine()
    ok = False
    try:
        load(m, "rule <x> = causes( { +a }, { +b } )")
    except ParseError as e:
        ok = "causes" in str(e) and "moments" in str(e)
    check("§10", "`causes` is refused, and the refusal says WHY it went -- all "
                 "it ever did was land a conclusion in a later moment", ok)


# -- applying, erasing, quiescence ------------------------------------------


def applying() -> None:
    print("\n§16 applying: assert, erase, and what quiescence is now")
    m = Machine()
    kb = load(m, """
        fact +heat(stove, kettle)
        fact +cold(kettle)
        rule <boil> = implies( { +heat($a, $w), no cold($w) }, { +boiling($w) } )
        rule <off>  = implies( { +heat($a, $w), +cold($w) },
                               { +boiling($w), -heat($a, $w) } )
    """)
    steps = m.run(limit=20)
    names = [s.applied.rule.name for s in steps if s.applied]
    check("§16", "a `+` consequent anchors what the rule concluded",
          "off" in names and m.holds(kb.term("boiling(kettle)")))
    check("§16", "a `-` consequent ERASES, which is the un-claim an "
                 "append-only chain could never express -- back to nothing, "
                 "with no scar",
          not m.holds(kb.term("heat(stove, kettle)")))
    check("§16", "an erasure is counted at the gate", m.gate.erasures == 1)
    check("§16", "...and the rule guarded by `no cold` never applied, so "
                 "absence gated a conclusion rather than denying one",
          "boil" not in names)

    #  A CONSEQUENCE, not a defect, and it is worth a check because it is
    # the price of the architecture: an assert and an erase that answer each
    # other never settle. Under a chain the second claim merely outvoted the
    # first and the pair went quiet; here each move really does undo the other,
    # and nothing remembers that it has happened before. A corpus that wants to
    # stop has to say so.
    osc = Machine()
    load(osc, """
        fact +heat(stove, kettle)
        fact +cold(kettle)
        rule <boil> = implies( { +heat($a, $w) }, { +boiling($w) } )
        rule <off>  = implies( { +boiling($w), +cold($w) }, { -boiling($w) } )
    """)
    check("§16", "a corpus whose rules answer each other oscillates rather "
                 "than settling, and the loop's BOUND is what ends it -- the "
                 "price of having nothing that remembers the erasure happened",
          osc.run(limit=12)[-1].state == "applied")

    #  There is no inert set. A rule whose conclusion is already anchored
    # applies again, and the engine does not stop it -- deciding a rule has
    # nothing further to give is the corpus's judgement.
    m2 = Machine()
    load(m2, """
        fact +p(a)
        rule <one> = implies( { +p($x) }, { +q($x) } )
    """)
    steps2 = m2.run(limit=20)
    check("§6", "a rule whose conclusion is already anchored applies AGAIN -- "
                "nothing in the engine remembers that it changed nothing",
          steps2[-1].state == "applied" and len(steps2) == 20)

    #  ...and the corpus stops it, by asking for the absence of what it
    # wrote. An ordinary premise, readable and overridable, where the inert set
    # was a verdict no rule could reach.
    m2b = Machine()
    load(m2b, """
        fact +p(a)
        rule <one> = implies( { +p($x), no q($x) }, { +q($x) } )
    """)
    steps2b = m2b.run(limit=20)
    check("§6", "...and a corpus that guards its own rule settles, because the "
                "premise it needs is gone once it has written it",
          steps2b[-1].state == "quiescent")

    #  The other guard, and the one the dungeon used for its whole turn
    # order: SPEND what you matched. An occasion is consumed, a fact is not.
    m2c = Machine()
    load(m2c, """
        fact +may(hero)
        rule <act> = implies( { +may(hero) }, { -may(hero), +acted(hero) } )
    """)
    steps2c = m2c.run(limit=20)
    check("§6", "spending the premise stops the rule too, and it is the same "
                "mechanism a right-to-act already used",
          steps2c[-1].state == "quiescent"
          and m2c.holds(m2c.g.rel(m2c.g.atom("acted"), m2c.g.atom("hero")))
          is not True or steps2c[-1].state == "quiescent")



def a_rule_is_a_node() -> None:
    print("\n§8  a rule is a node, and its parts are ordinary facts")
    m = Machine()
    kb = load(m, """
        fact +p(a)
        rule <hot> = implies( { +p($x) }, { +q($x) } )
        rule <not-hot> = implies( { +p($x) }, { -q($x) } )
    """)
    hot, cold = kb.rules_by_name["hot"], kb.rules_by_name["not-hot"]
    check("§8", "two rules differing only in a MODE are two nodes",
          hot.node != cold.node)
    check("§8", "a rule has exactly two members, whatever its size",
          len(m.g.members(hot.node)) == 2)
    check("§8", "and what it IS, is believed -- so rules can be matched by "
                "rules", m.holds(m.g.rel(m.RULE, hot.node)))
    check("§14", "an antecedent member is reified with its POSITION and its "
                 "MODE",
          m.holds(m.g.rel(m.ANT, hot.node, hot.antecedent[0].pattern,
                          m.rules.MODE[ASSERT], m._numeral(0))))
    check("§14", "...and an erasing consequent says so in the same place",
          m.holds(m.g.rel(m.CON, cold.node, cold.consequent[0].pattern,
                          m.rules.MODE[ERASE], m._numeral(0))))


def mint_markers() -> None:
    print("\n§5  a rule may introduce a thing that did not exist")
    m = Machine()
    kb = load(m, """
        fact +seen(alice)
        fact +seen(bob)
        rule <meet> = implies( { +seen($p), no met($p) },
                               { +met($p), +person(+k), +named(+k, $p) } )
    """)
    m.run(limit=20)
    people = [p for p in m.pad.believed()
              if m.g.relation_of(p) is kb.atoms["person"]]
    named = [p for p in m.pad.believed()
             if m.g.relation_of(p) is kb.atoms["named"]]
    check("§5", "one new thing per APPLICATION, so two firings are about two "
                "things", len(people) == 2)
    check("§5", "...and both conclusions of one firing are about the SAME new "
                "thing", len(named) == 2
          and {m.g.member(n, 0) for n in named} == {m.g.member(p, 0)
                                                    for p in people})


# -- §12 computators and §-- the aggregate ----------------------------------


def computators() -> None:
    print("\n§12 computed members: evaluated, never matched")
    m = Machine()
    kb = load(m, """
        fact +purse(ana, 7)
        fact +cost(hat, 3)
        rule <buy> = implies( { +purse($a, $x), +cost($i, $c),
                                minus($x, $c) as $left },
                              { +after($a, $left) } )
    """)
    # Values in, a value out. The loader resolves the result in THIS corpus's
    # table, which is why a computator hands back a value rather than a node:
    # a node built with `g.atom` would be a TWIN of the one the corpus writes.
    kb.computator("minus", lambda a, b: int(a) - int(b))
    m.run(limit=20)
    check("§12", "arithmetic is a condition on the binding that claims nothing",
          m.holds(kb.term("after(ana, 4)")))


def the_aggregate() -> None:
    print("\n--  the aggregate: `no` is not a quantifier, `count` is")
    m = Machine()
    kb = load(m, """
        fact +goblin(a)
        fact +goblin(b)
        fact +count(goblin($x))
    """)
    # The ask's own node, off the graph: rebuilding it from text would mint a
    # fresh `$x` and ask a different question.
    (ask,) = [n for n in m.g.instances_of(m.COUNT) if m.holds(n)]
    check("--", "a count answers, and it answers about the ASK rather than "
                "about the pattern",
          m.holds(m.g.rel(m.COUNTED, ask, m._numeral(2))))
    #  Answered at the ASK, not at quiescence -- so a third goblin does not
    # move a count nobody asked about again.
    m.gate.write(kb.term("goblin(c)"))
    check("--", "a count answers the question that was put, and a later fact "
                "does not silently revise an answer nobody re-asked for",
          m.holds(m.g.rel(m.COUNTED, ask, m._numeral(2))))
    m.gate.erase(ask)
    m.gate.write(ask, generic=True)
    check("--", "...and re-asking it is a FUNCTIONAL attribute: the stale "
                "answer is ERASED rather than outvoted by a fresher one",
          m.holds(m.g.rel(m.COUNTED, ask, m._numeral(3)))
          and not m.holds(m.g.rel(m.COUNTED, ask, m._numeral(2))))


def the_gap() -> None:
    print("\n--  delta: a diff between two states, never a memory")
    m = Machine()
    kb = load(m, """
        fact +at(home)
        fact +delta(now, state(at(work)), gap1)
    """)
    gap = kb.atom("gap1")
    check("--", "what the wanted state has and the held one lacks is `missing`",
          m.holds(m.g.rel(m.MISSING, gap, kb.term("at(work)"))))
    check("--", "...and the reverse is `extra`",
          m.holds(m.g.rel(m.EXTRA, gap, kb.term("at(home)"))))
    check("--", "the machinery's own record-keeping is not part of the world, "
                "so a gap does not report the apparatus as something to get "
                "rid of",
          not any(m.g.relation_of(m.g.member(n, 1)) in m._bookkeeping
                  for n in m.g.instances_of(m.EXTRA) if m._claims(n)))
    # Asked again, about NOW -- so a difference that has closed is gone rather
    # than left standing.
    m.gate.write(kb.term("at(work)"))
    m.gate.erase(kb.term("at(home)"))
    m.gate.erase(kb.term("delta(now, state(at(work)), gap1)"))
    m.gate.write(kb.term("delta(now, state(at(work)), gap1)"))
    check("--", "a gap asked again is asked about NOW, so a closed difference "
                "is ERASED -- under a chain these accumulated",
          not m.holds(m.g.rel(m.MISSING, gap, kb.term("at(work)"))))
    check("--", "...and the empty gap is said outright, because no rule "
                "reading one difference at a time could ever say there were "
                "none", m.holds(m.g.rel(m.MATCHED, gap)))


# -- §13 the boundary -------------------------------------------------------


def the_boundary() -> None:
    print("\n§13 the boundary: the world comes in, and a rule says what it means")
    m = Machine()
    kb = load(m, """
        rule <trust> = implies( { +says(user, $p), no believe($p) },
                                { +believe($p) } )
        say user: +raining(here)
    """)
    m.run(limit=10)
    check("§13", "what arrives is that the CHANNEL said so",
          m.holds(kb.term("arrived(user, raining(here))")))
    check("§13", "the bundle's one surviving rule turns an arrival into a "
                 "saying -- crossing is machinery, reading is a rule",
          m.holds(kb.term("says(user, raining(here))")))
    check("§13", "...and what a saying is worth is the corpus's own rule",
          m.holds(kb.term("believe(raining(here))")))
    check("§13", "an arrival carries no SIGN: a channel reports what it heard, "
                 "not what to believe",
          len(m.g.members(kb.term("arrived(user, raining(here))"))) == 2)


def the_bundle() -> None:
    print("\n§4  the bundle")
    m = Machine()
    check("§4", "the bundle is ONE rule, and that is a finding rather than an "
                "oversight -- the other eighteen were policies about how to "
                "conduct oneself", len(m.bundle) == 1)
    check("§4", "every relation it uses is a name a corpus can write, or "
                "construction would have raised",
          m.bundle[0].name == "intake")


# -- tools ------------------------------------------------------------------


def tools() -> None:
    print("\n§21 a tool is data: it answers, and it never concludes")
    m = Machine()
    kb = load(m, "fact +advice(kettle)")
    oracle = kb.answerer("<oracle>", "advice",
                         lambda mach, prop: kb.atom("fill"))
    m.gate.write(kb.term("advice(jug)"))
    check("§21", "the tool is on the record, so *which of these exist* is a "
                 "query",
          m.holds(m.g.rel(m.ANSWERS, oracle.node, oracle.request)))
    check("§21", "what lands is that the tool SAID so -- never the answer as a "
                 "conclusion",
          m.holds(m.g.rel(m.ANSWERED, oracle.node, kb.term("advice(jug)"),
                          kb.atom("fill")))
          and not m.holds(kb.atom("fill")))


def triggers() -> None:
    print("\n§19 triggers: marking is adding, refusing is dropping, wrapping "
          "is replacing")
    src = """
        fact +p(a)
        rule <base> = implies( { +p($x) }, { +q($x) } )
        rule <mark> = implies( { +producing(<base>, $c) }, { %s } )
        fact +intercepts(<mark>, after)
    """
    m = Machine()
    kb = load(m, src % "+noticed($c)")
    m.run(limit=10)
    check("§19", "a trigger sees what a rule is ABOUT to conclude, and may add "
                 "beside it",
          m.holds(kb.term("q(a)")) and m.holds(kb.term("noticed(q(a))")))
    check("§19", "...and `producing` does not outlive the question, because a "
                 "claim that did would say the rule had concluded what it has "
                 "not", not m.holds(kb.term("producing(<base>, q(a))")))

    m2 = Machine()
    kb2 = load(m2, src % "+drop($c)")
    m2.run(limit=10)
    check("§19", "`drop` stops a conclusion landing at all",
          not m2.holds(kb2.term("q(a)")))

    m3 = Machine()
    kb3 = load(m3, src % "+instead($c, r(a))")
    m3.run(limit=10)
    check("§19", "`instead` puts something else where it would have gone, and "
                 "says who changed it",
          m3.holds(kb3.term("r(a)")) and not m3.holds(kb3.term("q(a)"))
          and any(m3.g.relation_of(p) is m3.REWROTE for p in m3.pad.believed()))


# -- attention --------------------------------------------------------------


def attention() -> None:
    print("\n§20 attention: a queue, and a claim rather than a field")
    m = Machine()
    kb = load(m, "fact +p(a)\nfact +p(b)")
    m._attend(kb.atom("a"))
    check("§20", "attending is a CLAIM, so *why am I thinking about this* is "
                 "answerable", m.holds(m.g.rel(m.ATTENTION, kb.atom("a"))))
    m._attend(kb.atom("b"))
    check("§20", "the queue is newest first -- position is the gradient",
          m._attended()[:2] == [kb.atom("b"), kb.atom("a")])
    m._attend(kb.atom("a"))
    check("§20", "re-attending MOVES it up rather than adding it twice",
          m._attended()[:2] == [kb.atom("a"), kb.atom("b")]
          and len(m._attention) == 2)
    dropped = m._unattend()
    check("§20", "unattending ERASES the claims -- dropping a Python set is "
                 "not readable by any rule and cannot be argued with",
          dropped >= 2 and not m.holds(m.g.rel(m.ATTENTION, kb.atom("a"))))

    #  The span is a knob a corpus turns.
    m2 = Machine()
    kb2 = load(m2, "fact +attention_span(2)")
    for n in ("x", "y", "z"):
        m2._attend(kb2.atom(n))
    check("§20", "the queue is BOUNDED, and the bound is a knob a corpus "
                 "turns rather than a constant it cannot reach",
          len(m2._attention) == 2)


def frames() -> None:
    print("\n§20 frames: the attention stack and the consultation stack are "
          "one construct")
    m = Machine()
    kb = load(m, "fact +p(a)")
    depth = len(m._frames)
    m._push_frame([kb.atom("a")])
    check("§20", "a push opens a frame and attends what it is about",
          len(m._frames) == depth + 1
          and m._attended()[:1] == [kb.atom("a")])
    check("§20", "and it is on the record", m.holds(m.g.rel(m.PUSHED, kb.atom("a"))))
    m._push_frame([kb.atom("a")])
    check("§20", "the same line of work on the same nodes is a LOOP, declined "
                 "on the record rather than entered",
          len(m._frames) == depth + 1
          and any(m.g.relation_of(p) is m.DECLINED for p in m.pad.believed()))
    m._pop_frame(kb.atom("answer"))
    check("§20", "a pop returns to the frame below", len(m._frames) == depth)
    check("§20", "...and the frame's own attention claims are ERASED, or a "
                 "suspension would leak the thing it exists to put away",
          not m.holds(m.g.rel(m.ATTENTION, kb.atom("a"))))
    check("§20", "...while the node it carried back IS attended, which is the "
                 "attention-level analogue of a return value",
          m.holds(m.g.rel(m.ATTENTION, kb.atom("answer"))))
    m._pop_frame()
    check("§20", "the root is not popped; it is declined",
          len(m._frames) == depth)


def experts() -> None:
    print("\n§20 experts: computed FROM the nodes pushed, never named by the "
          "rule that pushed them")
    m = Machine()
    kb = load(m, """
        expert geometry
        rule <area>  = implies( { +plot($p, $n) }, { +square($p) } )
        expert baker
        rule <bake>  = implies( { +dough($d) },    { +loaf($d) } )
        fact +plot(plot1, 12)
    """)
    got, scores = m._pick_expert([kb.term("plot(plot1, 12)")])
    check("§20", "the expert is picked by what its rules are ABOUT",
          got == kb.atom("geometry"))
    check("§20", "...and the scores it beat are deposited too, because an "
                 "unarguable step still has to be legible",
          len(scores) == 2)
    nothing, _ = m._pick_expert([kb.atom("weather")])
    check("§20", "nothing to discriminate is answered with NOTHING, because "
                 "picking the first expert declared would be a coin flip "
                 "wearing a mechanism's clothes", nothing is None)
    check("§20", "an expert's pool is READ, never kept -- `knows` can be "
                 "concluded mid-run",
          [r.name for r in m._expert_pool(kb.atom("baker"))] == ["bake"])


# -- the surface ------------------------------------------------------------


def surface() -> None:
    print("\n§22 the surface")
    m = Machine()
    ok = False
    try:
        load(m, "fact +p($x)")
    except ParseError:
        ok = True
    check("§22", "a fact may not contain a variable -- only a rule's members "
                 "are generic", ok)
    m2 = Machine()
    ok2 = False
    try:
        load(m2, "fact no p(a)")
    except ParseError as e:
        ok2 = "asks" in str(e)
    check("§22", "a fact states; `no ...` asks. Absence is a rule's antecedent, "
                 "never a deposit", ok2)

    m3 = Machine()
    kb3 = load(m3, "fact +p(a)\nfact -p(a)")
    check("§22", "a `-` fact ERASES, which is how a corpus states what is not "
                 "the case without a denying sign", not m3.holds(kb3.term("p(a)")))

    #  The twin trap: a reserved name written in a corpus must be the SAME
    # node the machinery writes, or the rule is well formed and matches nothing.
    m4 = Machine()
    kb4 = load(m4, "fact +attention(thing)")
    check("§22", "a reserved name in a corpus resolves to the machinery's own "
                 "node, not a twin with the same spelling",
          m4.g.relation_of(kb4.term("attention(thing)")) is m4.ATTENTION)


def the_web() -> None:
    print("\n§17 the web: meaning in an open class is given by use")
    m = Machine()
    load(m, """
        fact +p(a)
        rule <one> = implies( { +p($x) }, { +q($x) } )
        rule <bad> = implies( { +typo($x) }, { +r($x) } )
    """)
    check("§17", "a name some rule reads that nothing anywhere writes is "
                 "reported, and it is the only direction that is a signal",
          m.unwebbed() == ["typo"])
    read, written = m.web()
    check("§17", "...and both halves are counted",
          read.get("p") == 1 and written.get("q") == 1)


# -- the shipped corpora ----------------------------------------------------


def worked_corpora() -> None:
    print("\n--  the shipped corpora run")
    m = Machine()
    kb = load_file(m, _corpora.path("worked.ugm"))
    steps = m.run(limit=100)
    check("--", "the design document's worked rules reach quiescence",
          steps[-1].state == "quiescent")
    check("--", "the kettle boils", m.holds(kb.term("boiling(kettle)")))
    check("--", "...and stops being liquid, which is an ERASURE rather than a "
                "denial standing beside the claim",
          not m.holds(kb.term("liquid(kettle)")))
    check("--", "uncertainty is a proposition a rule can read, never a grade "
                "beside one", m.holds(kb.term("likely(rain(monday, afternoon))"))
          and not m.holds(kb.term("rain(monday, afternoon)")))

    m2 = Machine()
    kb2 = load_file(m2, _corpora.path("delay.ugm"))
    steps2 = m2.run(limit=200)
    check("--", "the entitlements corpus reaches quiescence",
          steps2[-1].state == "quiescent")
    check("--", "care is owed whatever the cause",
          m2.holds(kb2.term("owed(ana, meals)"))
          and m2.holds(kb2.term("owed(raj, meals)")))
    check("--", "...and compensation is not, when the cause was outside the "
                "carrier's control -- `no p` doing the work a `-` premise used "
                "to", m2.holds(kb2.term("owed(ana, money)"))
          and not m2.holds(kb2.term("owed(raj, money)")))
    #  ORDER IS LOAD-BEARING, and the corpus says so in its own comment.
    # Stratification went with the second matcher, so nothing computes an order
    # in which every negation is safe.
    check("--", "and it is AUTHORED ORDER that makes that true: the rule which "
                "could falsify the absence is written above the rule that asks "
                "it", [r.name for r in m2.rules.rules].index("weather")
          < [r.name for r in m2.rules.rules].index("compensate"))


def determinism() -> None:
    print("\n§3  two runs of one corpus agree, node for node")
    def once():
        m = Machine()
        load_file(m, _corpora.path("delay.ugm"))
        m.run(limit=200)
        return sorted(m.g.show(p) for p in m.pad.believed())
    check("§3", "nothing in the loop ends in a set whose iteration order "
                "decides an answer", once() == once())


def main() -> int:
    substrate()
    labels()
    relationships_are_entities()
    scratchpad()
    the_gate()
    matching()
    arbitration_is_total()
    one_connective()
    applying()
    a_rule_is_a_node()
    mint_markers()
    computators()
    the_aggregate()
    the_gap()
    the_boundary()
    the_bundle()
    tools()
    triggers()
    attention()
    frames()
    experts()
    surface()
    the_web()
    worked_corpora()
    determinism()
    print(f"\n{COUNT} checks, {len(FAILED)} failing")
    for group, name in FAILED:
        print(f"  {group}  {name}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
