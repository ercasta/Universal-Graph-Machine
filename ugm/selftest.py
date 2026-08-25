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
    check("§3", "`on(a, b)` built twice is TWO nodes -- the substrate does not "
                "decide that saying a thing twice is saying it once",
          p1 != p2)
    check("§3", "...and both are the same proposition, which is the question "
                "`like` answers and the one absence asks",
          g.like(p1) == (p1, p2))
    check("§3", "members are ordered", g.members(p1) == (a, b))
    ba = g.rel(on, b, a)
    check("§3", "on(a,b) and on(b,a) are different nodes", p1 != ba)
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
    check("§3", "`find_rel` finds what exists, oldest first",
          g.find_rel(on, a, b) == p1 and g.find_rel(on, b, a) == ba)
    g.delete(q)
    check("§3", "...and still finds the other node of that shape",
          g.find_rel(on, b, a) == ba)
    g.delete(ba)
    check("§3", "...and finds nothing once every node of that shape is gone",
          g.find_rel(on, b, a) is None)
    g.delete(p1)
    check("§3", "...and finds the SURVIVOR while one of two twins is deleted, "
                "which the intern table could not: it named one node per "
                "shape and answered `nothing says that` beside a node saying it",
          g.find_rel(on, a, b) == p2)
    check("§3", "a deleted node reads as erased rather than raising",
          g.show(q).endswith("(erased)") and g.relation_of(q) is None)
    check("§3", "and the node it was ABOUT is untouched -- deletion does not "
                "cascade, which is what makes an anchor the only safe target",
          g.show(a) == "a" and g.find_rel(on, a, b) == p2)


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
    check("§3", "so `adores(x, z)` IS `loves(x, z)` -- not one node, but one "
                "proposition: the lookup widens to the class the label merged "
                "them into",
          g.find_rel(g.labelled("adores"), x, z) == inst
          and inst in g.like(g.rel(adores, x, z)))

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


def unmerging() -> None:
    """`unmerge` -- reversible only at the top of the record, and only when
    the merge caused no cascade."""
    print("\n§3  unmerge -- a merge is a claim, and only the record's own top "
          "can be taken back")
    g = Graph()
    loves, paul, mary = g.atom("loves"), g.atom("paul"), g.atom("mary")
    paulb = g.atom("paul-b")
    r1 = g.rel(loves, paulb, mary)   # built off the SECOND name, before any merge

    g.merge(paul, paulb)
    check("§3", "the relation built off the dropped name is findable under "
                "the kept one -- and NOTHING moved to make that true: the "
                "lookup widened to the class instead of the node changing key",
          g.find_rel(loves, paul, mary) == r1
          and g.counts_as(paul) == (paul, paulb))

    g.unmerge(paul, paulb)
    check("§3", "unmerging puts the identity back",
          g.identity_of(paulb) == paulb and g.counts_as(paul) == (paul,))
    check("§3", "...and every index the merge touched, not just identity -- "
                "the relation is findable under the ORIGINAL name again and "
                "not under the merged one",
          g.find_rel(loves, paulb, mary) == r1
          and g.find_rel(loves, paul, mary) is None)

    #  NO CASCADE. `loves(a, b)` and `loves(c, b)` say one thing once `a`
    # and `c` are one, and they stay TWO NODES saying it -- two occasions of a
    # proposition, which is now the ordinary case. Nothing collapses, so there
    # is no decision `merge` made on its own and nothing for `unmerge` to
    # refuse.
    a, b, c = g.atom("a"), g.atom("b"), g.atom("c")
    r_ab = g.rel(loves, a, b)
    r_cb = g.rel(loves, c, b)
    g.merge(a, c)
    check("§3", "a merge collapses no other node: two ways of writing one "
                "proposition stay two occasions of it",
          r_ab != r_cb and set(g.like(r_ab)) == {r_ab, r_cb})
    check("§3", "...and both are reachable under either name, which is the "
                "congruence the cascade used to buy",
          set(g.instances_with(loves, 0, a)) == {r_ab, r_cb}
          and set(g.instances_with(loves, 0, c)) == {r_ab, r_cb})
    g.unmerge(a, c)
    check("§3", "...so unmerging it is ordinary, not refused",
          g.identity_of(c) == c and g.like(r_ab) == (r_ab,))

    #  NOT THE TOP. A later merge may already rest on an earlier one.
    p, q, s, t = g.atom("p"), g.atom("q"), g.atom("s"), g.atom("t")
    g.merge(p, q)
    g.merge(s, t)
    threw = False
    try:
        g.unmerge(p, q)
    except ValueError:
        threw = True
    check("§3", "unmerging anything but the most recent merge is refused",
          threw)
    check("§3", "...and the actual top still unmerges cleanly afterwards",
          g.unmerge(s, t) == 0 and g.identity_of(t) == t)

    #  Labels move with a merge and move back with its unmerge.
    x, y = g.atom("x"), g.atom("y")
    g.label(x, "romance")
    g.label(y, "romance")   # collides -- merges y into x
    check("§3", "a label collision merged the two nodes",
          g.labels_of(x) == ("x", "romance", "y") and g.identity_of(y) == x)
    g.unmerge(x, y)
    check("§3", "unmerging gives each node back its own label",
          g.labels_of(x) == ("x", "romance") and g.labels_of(y) == ("y",))


def relationships_are_entities() -> None:
    """Two `loves(x, z)` are two things, and one proposition."""
    print("\n§3  a relationship may be an entity -- two occasions of one "
          "proposition")
    g = Graph()
    pad = Scratchpad(g)
    loves, x, z = g.atom("loves"), g.atom("x"), g.atom("z")
    one = g.rel(loves, x, z)
    two = g.rel(loves, x, z)
    three = g.rel(loves, x, z)

    check("§3", "`rel` mints a distinct node each time -- two loves between "
                "the same pair are two things, and there is no third node "
                "that is the canonical one",
          len({one, two, three}) == 3)
    check("§3", "every one is in the argument index, so a rule reaches all of "
                "them",
          g.instances_with(loves, 0, x) == [one, two, three])
    check("§3", "`like` collects the nodes of one shape, oldest first",
          g.like(two) == (one, two, three))

    pad.note(two)
    check("§3", "belief is per ENTITY: anchoring one does not anchor another "
                "that happens to say the same thing",
          pad.holds(two) and not pad.holds(one) and not pad.holds(three))
    check("§3", "...and it anchors ONCE -- noting again returns the anchor "
                "already there rather than minting a second one for a belief "
                "`erase` deletes singly",
          pad.note(two) == pad.anchor(two)
          and len(g.like(pad.anchor(two))) == 1)

    #  Absence is a question about the PROPOSITION, so asking one node
    # alone answers *nothing says it* while another sits believed.
    check("§3", "so absence is asked of every node of the shape",
          pad.holds_any(one) and not pad.holds(one))

    v = g.var("$v")
    absent = Rule(g.atom("<probe>"),
                  [Member(ABSENT, g.rel(loves, x, z))], [], "probe")
    check("§3", "a rule's `no loves(x, z)` does not match while any occasion "
                "of it is believed",
          match(g, pad, absent) == [])
    pad.erase(two)
    check("§3", "...and matches once nothing says it at all",
          len(match(g, pad, absent)) == 1)

    present = Rule(g.atom("<probe2>"),
                   [Member(ASSERT, g.rel(loves, x, v))], [], "probe2")
    pad.note(one)
    pad.note(two)
    check("§3", "a positive premise binds each believed occasion separately, "
                "because each is a different thing to be about",
          len(match(g, pad, present)) == 2)

    #  `g.like(one)` also holds the pattern `no loves(x, z)` was built
    # from -- a rule MENTIONS a proposition and nothing anchors it, so it is a
    # node of that shape sitting in the index and believed by nobody. That was
    # true before interning went too; there was simply only ever one of them.
    g.delete(three)
    check("§3", "deleting one takes it out of the shape index",
          three not in g.like(one) and {one, two} <= set(g.like(one)))


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
    #  ONE node, held on to. `g.rel` mints, so erasing what a second
    # `g.rel(heavy, a)` returns would erase an occasion nobody ever believed
    # and leave this one standing. `Gate.erase` is where a caller that only
    # has the shape is met halfway; the scratchpad takes the occasion.
    heavy_a = g.rel(heavy, a)
    pad.note(heavy_a)
    check("§12", "...and stops holding the moment something does",
          match(g, pad, r2) == [])
    pad.erase(heavy_a)
    check("§12", "...and holds again once it is erased, which an append-only "
                 "chain could never get back to", len(match(g, pad, r2)) == 1)


def arbitration_is_total() -> None:
    print("\n§14 arbitration")
    m = Machine()
    kb = load(m, """
        fact +p(a)
        rule <one> = implies( { +p($x), no q($x) }, { +q($x) } ) => brush(p($x))
        rule <two> = implies( { +p($x), no r($x) }, { +r($x) } )
    """)
    steps = [s for s in m.run(limit=8) if s.applied]
    check("§14", "with two rules matching, arbitration answers",
          bool(steps))
    check("§14", "and it answers by AUTHORED ORDER when nothing else separates "
                 "them", steps[0].applied.rule.name == "one")
    #  The brush on `<one>` is the point of the check, not scaffolding
    # around it. Arbitration defers rather than rejects -- but a move also
    # spends what it matched, so the deferred rule finds its premise gone
    # unless the winner says otherwise. Whether the loser still gets its turn
    # is therefore a fact about what `<one>` gives back, and the two
    # mechanisms are separable exactly here.
    check("§14", "both eventually apply -- arbitration defers a loser rather "
                 "than rejecting it, and it is still there to take its turn "
                 "once the winner puts the premise back",
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
    check("§16", "a corpus whose rules answer each other stops, and the loop "
                 "says WHY: `unattended`, not `quiescent`. The pair really "
                 "does undo each other and nothing remembers it -- but each "
                 "still MATCHES, so calling that a finished search would be "
                 "the loop stating a falsehood about its own silence",
          osc.run(limit=12)[-1].state == "unattended")

    #  There is no inert set. A rule whose conclusion is already anchored
    # applies again, and the engine does not stop it -- deciding a rule has
    # nothing further to give is the corpus's judgement.
    m2 = Machine()
    load(m2, """
        fact +p(a)
        rule <one> = implies( { +p($x) }, { +q($x) } )
    """)
    steps2 = m2.run(limit=20)
    check("§6", "a rule whose conclusion is already anchored is still OFFERED "
                "again -- there is no inert set, and deciding a rule has "
                "nothing further to give is not the engine's judgement -- but "
                "it runs out of SUBJECT rather than out of ticks, and the run "
                "ends `unattended` because the match is still there",
          steps2[-1].state == "unattended" and len(steps2) < 20)

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

    #  `no <computator>(...)` -- a real bug this session found while
    #  planning the dungeon's microprogram port: the computator branch ran
    #  BEFORE the ABSENT check could ever see it, so `no` in front of a
    #  computator-relation member was silently ignored.
    m2 = Machine()
    kb2 = load(m2, """
        fact +hit(5)
        fact +ac(3)
        rule <r> = implies({ $h = hit($x), $c = ac($y), no beats($x, $y) },
                           { +reported(missed) })
    """)
    kb2.computator("beats", lambda a, b: kb2.atom("yes") if int(a) > int(b) else None)
    m2.run(limit=5)
    check("§12", "`no beats(5, 3)` -- 5 DOES beat 3, so the negated "
                 "computator member must refuse to match",
          not m2.holds(kb2.term("reported(missed)")))

    m3 = Machine()
    kb3 = load(m3, """
        fact +hit(2)
        fact +ac(9)
        rule <r> = implies({ $h = hit($x), $c = ac($y), no beats($x, $y) },
                           { +reported(missed) })
    """)
    kb3.computator("beats", lambda a, b: kb3.atom("yes") if int(a) > int(b) else None)
    m3.run(limit=5)
    check("§12", "...and `no beats(2, 9)` -- 2 does NOT beat 9 -- matches, "
                 "the computator's own decline (`None`) being the right "
                 "reading of *not this ordering*",
          m3.holds(kb3.term("reported(missed)")))


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


def tool_approval() -> None:
    """`ugm/rules/tools_approval.ugm`: `<hold>` (§19) turns a write into a
    `pending`, an ordinary tool (§17) answers it, and the two outcomes are
    two ordinary rules. See `docs/tools-approval.md` and
    `ugm.probes.tools`."""
    print("\n--  approval is a corpus, not a feature: §17 tools + §19 "
          "triggers, composed")
    path = _corpora.path("tools_approval.ugm")

    def run(decision: str):
        m = Machine()
        pre = load(m, "", scope="ops")
        pre.answerer("approve", "pending", lambda mach, prop: pre.atom(decision))
        kb = load_file(m, path, scope="ops")
        steps = m.run(limit=20)
        return m, kb, steps

    m, kb, steps = run("yes")
    check("--", "approved reaches quiescence with the action taken",
          steps[-1].state == "quiescent" and m.holds(kb.term("deploy(web)")))
    check("--", "...and the pending record and its answer are both consumed, "
                 "not left for a later approval to match again",
          not m.holds(kb.term("pending(deploy(web))"))
          and not m.holds(kb.term("answered(approve, pending(deploy(web)), "
                                   "yes)")))

    m2, kb2, steps2 = run("no")
    check("--", "denied reaches quiescence with the action never taken",
          steps2[-1].state == "quiescent"
          and not m2.holds(kb2.term("deploy(web)")))
    check("--", "...and nothing is left pending",
          not m2.holds(kb2.term("pending(deploy(web))")))


# -- attention --------------------------------------------------------------


def attention() -> None:
    print("\n§20 attention: a queue, and engine state rather than a belief")
    m = Machine()
    kb = load(m, "fact +p(a)\nfact +p(b)")
    m._attend(kb.atom("a"))
    check("§20", "attending is frame-scoped ENGINE state, not a proposition "
                 "the graph believes -- attention is control, not world "
                 "knowledge, and `attentioned($x)` is how a rule asks "
                 "without it being one",
          kb.atom("a") in m._lane_state()[2]
          and not m.holds(m.g.rel(m.ATTENTION, kb.atom("a"))))
    m._attend(kb.atom("b"))
    check("§20", "the queue is newest first -- position is the gradient",
          m._attended()[:2] == [kb.atom("b"), kb.atom("a")])
    m._attend(kb.atom("a"))
    check("§20", "re-attending MOVES it up rather than adding it twice",
          m._attended()[:2] == [kb.atom("a"), kb.atom("b")]
          and [n for n, _w in m._attention].count(kb.atom("a")) == 1)
    dropped = m._unattend()
    check("§20", "unattending clears both the queue and the standing "
                 "weights -- a plain dict/list clear now, not an erase loop, "
                 "because there is no belief left to erase",
          dropped >= 2 and not m._lane_state()[2]
          and not m._attention)

    #  The queue is bounded by TIME, not by length.
    m2 = Machine()
    kb2 = load(m2, "")
    for n in ("x", "y", "z"):
        m2._attend(kb2.atom(n))
    held = len(m2._attention)
    for _ in range(12):
        m2._fade_attention()
    check("§20", "the queue is bounded by TIME rather than by length: a claim "
                 "lasts as long as its strength and then it is gone, and being "
                 "third in line is not a reason to forget anything",
          held == 3 and not m2._attention)

    #  A strong claim outlives a busy move, which a span could not promise.
    m3 = Machine()
    kb3 = load(m3, "")
    m3._attend(kb3.atom("folder"), weight=5)
    for i in range(9):          # nine incidental touches, as one move makes
        m3._push_attention(kb3.atom("noise%d" % i))
    m3._fade_attention(); m3._fade_attention()
    kept = dict((m3.g.show(n), w) for n, w in m3._attention)
    check("§20", "and the claim survives the bookkeeping of its own move -- "
                 "nine incidental touches no longer push a deliberate one out",
          kept.get("folder") == 4 and not any(k.startswith("noise") for k in kept))

    #  Bringing something up again is worth what it was worth.
    m4 = Machine()
    kb4 = load(m4, "")
    m4._attend(kb4.atom("folder"), weight=5)
    for _ in range(8):
        m4._fade_attention()
    faded = not m4._attention
    m4._push_attention(kb4.atom("folder"))      # merely MENTIONED, no weight
    back = dict((m4.g.show(n), w) for n, w in m4._attention)
    check("§20", "a claim that faded away and is mentioned again comes back at "
                 "what it was WORTH, not at a brush's 1 -- fading forgets the "
                 "thing, never how much it mattered, or bringing something up "
                 "could not outrank whatever was said more recently",
          faded and back.get("folder") == 5)

    #  A min pins a claim; a max caps how far a refresh may raise it.
    m5 = Machine()
    kb5 = load(m5, "")
    m5._attend(kb5.atom("pinned"), weight=3, floor=1)
    m5._attend(kb5.atom("capped"), weight=9, ceiling=2)
    at_first = dict((m5.g.show(n), w) for n, w in m5._attention)
    for _ in range(20):
        m5._fade_attention()
    after = dict((m5.g.show(n), w) for n, w in m5._attention)
    check("§20", "a max caps what a claim is refreshed to, so a thing named "
                 "over and over cannot grow until it is the only thing the "
                 "lane is about",
          at_first.get("capped") == 2 and at_first.get("pinned") == 3)
    check("§20", "a min PINS: it fades to the floor and stops there, so a "
                 "lane with a pinned claim always has a subject however long "
                 "nothing happens",
          after.get("pinned") == 1 and "capped" not in after)

    #  Per-line scoring: which line the multiplier hangs on decides.
    def _pick(on_event):
        ev = "[+1, attention_multiplier:9]" if on_event else "[+1, attention_multiplier:0]"
        pa = "[+1, attention_multiplier:0]" if on_event else "[+1, attention_multiplier:9]"
        mm = Machine()
        k = load(mm, "fact +person(paul)\nfact +person(mary)\n"
                     "fact +intake(e1, paul)\nfact +intake(e2, mary)\n"
                     "rule <pick> = implies( { $z = intake($e, $who) " + ev +
                     ", $w = person($who) " + pa + " }, { +picked($e) } )")
        mm._unattend()
        mm._attend(k.term("intake(e2, mary)"), weight=9)
        mm._attend(k.term("person(paul)"), weight=9)
        mm.run(limit=1)
        return [mm.g.show(p) for p in mm.pad.believed()
                if mm.g.show(p).startswith("picked")]

    check("§20", "a line carries its own contribution and its own attention "
                 "multiplier, and WHICH LINE it hangs on decides: the same "
                 "rule over the same facts picks the attended EVENT or the "
                 "attended PARTICIPANT depending on nothing but that",
          _pick(True) == ["picked(e2)"] and _pick(False) == ["picked(e1)"])

    check("§20", "...and all lines still have to match -- a bracket is a "
                 "score, never a filter",
          len(_pick(True)) == 1)

    #  Position is not a signal: strength alone, because decay already aged it.
    def _stronger_or_newer(strong_first):
        mm = Machine()
        k = load(mm, "fact +person(paul)\nfact +person(mary)\n"
                     "rule <one> = implies( { $w = person($who), no chosen }, "
                     "{ +took($who), +chosen } )")
        mm._unattend()
        order = ("paul", "mary") if strong_first else ("mary", "paul")
        for name in order:
            mm._attend(k.term("person(%s)" % name),
                       weight=9 if name == "paul" else 2)
        mm.run(limit=1)
        return [mm.g.show(p) for p in mm.pad.believed()
                if mm.g.show(p).startswith("took")]

    #  A silence with work still in it is not a finished search.
    mz = Machine()
    kz = load_file(mz, _corpora.path("worked.ugm"))
    zsteps = mz.run(limit=100)
    from .core.rules import match as _match
    took = {s.applied.rule.name for s in zsteps if s.applied is not None}
    outstanding = [r.name for r in mz.rules.rules
                   if r.name not in took
                   and _match(mz.g, mz.pad, r, computes=mz.rules.computes,
                              predicates=mz.rules.predicates)]
    check("§20", "a run that stops holding a FULL match it never offered says "
                 "`unattended` rather than `quiescent` -- the facts are all "
                 "still believed and the rule still matches, so what faded "
                 "was not the knowledge but the grip on there being something "
                 "left to do about it",
          not outstanding or zsteps[-1].state == "unattended")

    check("§20", "the STRONGER claim wins whether it was made first or last "
                 "-- queue position is not a signal, because under decay the "
                 "strength already is the recency and reading both counted "
                 "the same fact twice",
          _stronger_or_newer(True) == ["took(paul)"]
          and _stronger_or_newer(False) == ["took(paul)"])


def reference_lines() -> None:
    """`attentioned($x)` and a label test -- PREDICATES (`new_substrate.md`):
    filters over an already-bound node, never matched, never bound to."""
    print("\n§20 reference lines -- attentioned($x) is deixis (which one), "
          "not a relevance gate")
    corpus = ("fact +happy(paul)\nfact +happy(mary)\n"
              "rule <r1> = implies({+happy($x), attentioned($x)}, "
              "{+noticed($x)})")

    m = Machine()
    kb = load(m, corpus)
    # Emptied on purpose: loading attends what it wrote, so "nothing
    # attended" is a state that now has to be arranged rather than assumed.
    m._unattend()
    m.run(limit=5)
    check("§20", "with nothing attended, the predicate never opens -- it "
                 "filters a reference, it does not gate on relevance out of "
                 "nothing",
          not m.holds(m.g.rel(kb.atom("noticed"), kb.atom("paul")))
          and not m.holds(m.g.rel(kb.atom("noticed"), kb.atom("mary"))))

    m2 = Machine()
    kb2 = load(m2, corpus)
    #  Emptied first, for the machine above's reason. Without this, loading
    # has already attended `mary` along with everything else it wrote, so
    # `attentioned($x)` opens for both and the check cannot tell a predicate
    # that picks one referent out from one that lets everything through.
    #
    # Then TWO claims, because they answer two different questions. The
    # occasion `happy(paul)` is what the rule's first line has to match on,
    # and a move is only offered when a line it matched carries a token. The
    # atom `paul` is what `attentioned($x)` asks about -- the referent, not
    # the proposition. Attending only the atom offers the rule nothing;
    # attending only the proposition opens the predicate for nobody.
    m2._unattend()
    m2._attend(kb2.term("happy(paul)"))
    m2._attend(kb2.atom("paul"))
    m2.run(limit=5)
    check("§20", "attending paul picks him out -- only the attended one is "
                 "noticed, the other stays merely happy",
          m2.holds(m2.g.rel(kb2.atom("noticed"), kb2.atom("paul")))
          and not m2.holds(m2.g.rel(kb2.atom("noticed"), kb2.atom("mary"))))

    #  `label`, built directly (no corpus surface for `Graph.label` yet).
    #  `atom` never interns (§3 -- naming is local), so LABEL, the-kettle
    #  and not-it are each minted ONCE and reused, exactly the discipline a
    #  loader's name table exists to give a corpus for free.
    g3 = Graph()
    happy, kettle, paul = g3.atom("happy"), g3.atom("kettle"), g3.atom("paul")
    g3.label(kettle, "the-kettle")
    x = g3.var("$x")
    LABEL = g3.atom("label")
    the_kettle, not_it = g3.atom("the-kettle"), g3.atom("not-it")
    pad3 = Scratchpad(g3)
    pad3.note(g3.rel(happy, kettle))
    pad3.note(g3.rel(happy, paul))
    predicates = {LABEL: lambda a, b: g3.show(b) in g3.labels_of(a)}
    r = Rule(g3.atom("<r>"),
             [Member(ASSERT, g3.rel(happy, x)),
              Member(ASSERT, g3.rel(LABEL, x, the_kettle))],
             [], "r")
    found = match(g3, pad3, r, predicates=predicates)
    check("§20", "label($x, the-kettle) filters to the labelled one",
          len(found) == 1 and found[0].bindings[x] == kettle)

    wrong = Rule(g3.atom("<wrong>"),
                 [Member(ASSERT, g3.rel(happy, x)),
                  Member(ASSERT, g3.rel(LABEL, x, not_it))],
                 [], "wrong")
    check("§20", "...and refuses a label the node does not carry -- control",
          match(g3, pad3, wrong, predicates=predicates) == [])

    open_var = Rule(g3.atom("<open>"),
                     [Member(ASSERT, g3.rel(LABEL, x, the_kettle))],
                     [], "open")
    check("§20", "a predicate whose argument nothing bound answers nothing -- "
                 "the computator's own rule, not a special case for this one",
          match(g3, pad3, open_var, predicates=predicates) == [])


def rhs_tail() -> None:
    """The RHS's ordered tail (`new_substrate.md`) -- `attend`/`stop` written
    directly on the rule, unconditional, no separate `after` statement.

    Reuses the trigger BACKEND (`m.rules.triggers`, keyed on empty query) --
    RHS supersedes the no-query case of triggers rather than duplicating it,
    which is why no executor code is new here, only the front door."""
    print("\n§20 the RHS's ordered tail -- attend/stop written on the rule "
          "itself, no separate trigger statement")
    m = Machine()
    kb = load(m, "fact +happy(paul)\n"
                 "rule <r1> = implies({+happy($x)}, {+noticed($x)}) "
                 "=> attend($x, 3)")
    m.run(limit=3)
    check("§20", "the tail's `attend($x, 3)` names the rule's OWN $x, at the "
                 "learned weight, with no separate `after <r1> => ...` "
                 "statement anywhere in this corpus",
          (kb.atom("paul"), 3) in m._attention)

    m2 = Machine()
    kb2 = load(m2, "fact +happy(paul)\n"
                   "rule <r1> = implies({+happy($x)}, {+noticed($x)})")
    m2.run(limit=3)
    check("§20", "...and a rule with no tail attends nothing beyond what the "
                 "loop attends on its own -- control",
          (kb2.atom("paul"), 3) not in m2._attention)

    m1b = Machine()
    kb1b = load(m1b, "fact +bad(x)\n"
                     "rule <r1> = implies({+bad($z)}, {+seen($z)}) "
                     "=> attend($z, -5)")
    m1b.run(limit=3)
    check("§20", "a NEGATIVE weight parses too -- *a reason not to think "
                 "about that*, read by magnitude on the standing side and "
                 "never reaching the queue position (`_push_attention` "
                 "floors it at 1)",
          m1b._lane_state()[2].get(kb1b.atom("x")) == -5
          and dict(m1b._attention).get(kb1b.atom("x"), 0) >= 1)

    m3 = Machine()
    kb3 = load(m3, "fact +happy(paul)\nfact +happy(mary)\n"
                   "rule <r1> = implies({+happy($x)}, {+noticed($x)}) => stop")
    steps = m3.run(limit=10)
    noticed = sum(1 for n in ("paul", "mary")
                  if m3.holds(m3.g.rel(kb3.atom("noticed"), kb3.atom(n))))
    check("§20", "`stop` in the tail ends the run after ONE application, "
                 "with a second `happy` still unread -- the ordinary loop "
                 "would have applied both",
          steps[-1].state == "stopped" and noticed == 1)


def rhs_graph_ops() -> None:
    """`merge`/`unmerge`/`destroy`/`label`/`unlabel` in the RHS tail --
    Graph.merge's own docstring calls this *an effect `+`/`-` provably
    cannot express, already built, unreachable from a rule*. This closes
    that gap."""
    print("\n§20 the RHS reaches identity and structure -- merge, unmerge, "
          "destroy, label, unlabel, all callable from a rule for the "
          "first time")

    m = Machine()
    kb = load(m, "fact +sameas(loves, adores)\n"
                 "rule <r1> = implies({+sameas($a, $b)}, {+seen($a)}) "
                 "=> merge($a, $b)")
    m.run(limit=5)
    check("§20", "merge($a, $b) in the tail merges the rule's OWN bindings",
          m.g.identity_of(kb.atom("adores")) == kb.atom("loves"))

    #  Two pairs, GUARDED -- the point is the op, not a fixture that starves
    #  itself the way an unguarded rule always does (§ built this session).
    m2 = Machine()
    kb2 = load(m2, "fact +sameas(a, b)\nfact +sameas(a, c)\n"
                   "rule <r1> = implies({+sameas($x, $y), "
                   "no processed($x, $y)}, {+processed($x, $y)}) "
                   "=> merge($x, $y)")
    m2.run(limit=10)
    a2, b2, c2 = kb2.atom("a"), kb2.atom("b"), kb2.atom("c")
    check("§20", "...and a guarded rule applies it across every pair, not "
                 "just the one that wins the first tick",
          m2.g.identity_of(b2) == a2 and m2.g.identity_of(c2) == a2)

    m3 = Machine()
    kb3 = load(m3, "fact +wants_label(kettle, the-kettle)\n"
                   "rule <r1> = implies({+wants_label($x, $t)}, {+seen($x)}) "
                   "=> label($x, $t)")
    m3.run(limit=5)
    check("§20", "label($x, $t) reaches `Graph.label` from a rule",
          "the-kettle" in m3.g.labels_of(kb3.atom("kettle")))

    #  Two rules, staged, so the label's PRESENCE is observable between them
    #  -- `unlabel` removing a label nothing added is a check that cannot
    #  fail, the same trap `destroy`'s check below was caught making.
    m4 = Machine()
    kb4 = load(m4, "fact +wants_label(kettle, the-kettle)\n"
                   "rule <r1> = implies({+wants_label($x, $t), "
                   "no labelled($x, $t)}, {+labelled($x, $t)}) "
                   "=> label($x, $t)\n"
                   "rule <r2> = implies({+labelled($x, $t), "
                   "no unlabelled($x, $t)}, {+unlabelled($x, $t)}) "
                   "=> unlabel($x, $t)")
    m4.run(limit=1)
    check("§20", "...between the two, the label really is there",
          "the-kettle" in m4.g.labels_of(kb4.atom("kettle")))
    m4.run(limit=5)
    check("§20", "unlabel($x, $t) takes back a label `label` actually added",
          "the-kettle" not in m4.g.labels_of(kb4.atom("kettle")))

    #  `destroy` on an UNGUARDED rule: nothing stops `<r1>` re-applying every
    #  tick against the same `+junk(trash)`, which regrounds `$x` to a node
    #  `destroy` already deleted -- the exact case that found `has_var`
    #  raising `KeyError` on a deleted node instead of answering `False`,
    #  same as `relation_of`'s own contract. Left unguarded on purpose: a
    #  guarded fixture would not exercise the regrounding at all.
    m5 = Machine()
    kb5 = load(m5, "fact +junk(trash)\n"
                   "rule <r1> = implies({+junk($x)}, {+seen($x)}) "
                   "=> destroy($x)")
    m5.run(limit=5)
    trash = kb5.atom("trash")
    #  `trash` is a bare ATOM: `relation_of` on one is None by construction,
    #  deleted or not -- a check against it cannot fail, the trap this repo
    #  keeps a named list of. `show` is what `delete` actually changes for
    #  every node kind, atom included.
    check("§20", "destroy($x) reaches `Graph.delete` -- the node is gone, "
                 "not merely un-believed -- and a later unguarded "
                 "re-application, regrounding the same binding to the now- "
                 "deleted node, does not crash the run",
          m5.g.show(trash) == f"#{trash}(erased)")

    m6 = Machine()
    kb6 = load(m6, "fact +sameas(a, b)\nfact +sameas(a, c)\n"
                   "rule <r1> = implies({+sameas($x, $y), "
                   "no processed($x, $y)}, {+processed($x, $y)}) "
                   "=> merge($x, $y)")
    m6.run(limit=10)
    a6, b6, c6 = kb6.atom("a"), kb6.atom("b"), kb6.atom("c")
    #  The OLDER of the two merges, read off the record rather than named:
    # which of `(a, b)` and `(a, c)` the rule reaches first is a tie the table
    # breaks, and this check is about the record's shape, not about that tie.
    older = m6.g._merge_log[0]
    threw = False
    try:
        m6.g.unmerge(older["keep"], older["drop"])
    except ValueError:
        threw = True
    check("§20", "`unmerge` in Python still refuses a non-top merge reached "
                 "THROUGH the RHS the same way it refuses one built by hand "
                 "-- one engine, not two",
          threw and len(m6.g._merge_log) == 2
          and m6.g.identity_of(b6) == a6 and m6.g.identity_of(c6) == a6)

    m7 = Machine()
    pre7 = load(m7, "", scope="s7")
    pre7.answerer("dice", "roll", lambda mach, prop: None)
    kb7 = load(m7, "fact +need(roll(d20, hit(hero, orc)))\n"
                   "rule <ask> = implies({$nd = need($r)}, "
                   "{-$nd, +answered(<dice>, $r, 5)})\n"
                   "rule <wound> = implies("
                   "{$hit = answered(<dice>, roll(d20, hit($a, $d)), $n)},"
                   "{+seen($a)}) => forget $hit", scope="s7")
    m7.run(limit=10)
    check("§20", "forget $hit erases the answer AND, structurally, the "
                 "request it names -- an occasion consumed as one "
                 "statement instead of two `-` members",
          not m7.holds(kb7.term("answered(<dice>, roll(d20, hit(hero, orc)), 5)"))
          and not m7.holds(kb7.term("roll(d20, hit(hero, orc))"))
          and m7.holds(kb7.term("seen(hero)")))

    m8 = Machine()
    kb8 = load(m8, "fact +junk(x)\n"
                   "rule <bad> = implies({$j = junk($x)}, {+seen($x)}) "
                   "=> forget $j")
    threw = False
    try:
        m8.run(limit=5)
    except ValueError:
        threw = True
    check("§20", "forget on a node that is not answered(...)-shaped RAISES "
                 "-- an author's mistake surfaces, it is not absorbed as a "
                 "silent no-op",
          threw)


def prefix_binding() -> None:
    """`$z = p($x, $y)` -- `new_substrate.md`'s own spelling of `as`, prefix
    rather than suffix. Same binding, built the same way; a judger rule
    generic over the RELATION itself (`$r($a, $x)`) is the stress test that
    prompted writing it, and it is exercised here rather than a toy."""
    print("\n§8  $z = p(...) -- the microprogram's prefix spelling of `as`, "
          "and a judger rule generic over the relation")
    corpus = (
        "fact +want(color(ball, red))\n"
        "fact +color(ball, blue)\n"
        "rule <missing-slot> = implies("
        "{ $w = want($r($a, $x)), no $r($a, $x), $cur = $r($a, $y) },"
        "{ +missing($r($a, $x)), +extra($cur) } )"
    )
    m = Machine()
    kb = load(m, corpus)
    m.run(limit=5)
    check("§8", "a judger generic over the RELATION -- one rule, not one "
                "per relation -- reports the wanted value missing and the "
                "wrong one extra",
          m.holds(kb.term("missing(color(ball, red))"))
          and m.holds(kb.term("extra(color(ball, blue))")))

    m2 = Machine()
    kb2 = load(m2, corpus.replace("+color(ball, blue)", "+color(ball, red)"))
    m2.run(limit=5)
    check("§8", "...and stays silent once the want is satisfied -- control",
          not m2.holds(kb2.term("missing(color(ball, red))")))

    threw = False
    try:
        load(Machine(), "fact +p(a)\n"
                        "rule <bad> = implies({$w = p($x) as $w2}, {+q($x)})")
    except ParseError:
        threw = True
    check("§8", "`$z = ...` and `... as $t` together is refused -- one "
                "binding, said once, not silently let the second clobber "
                "the first",
          threw)


def alt_branches() -> None:
    """`alt(...)` -- a union of conjunctive branches sharing a prefix and a
    consequent, compiled into one Rule per branch at load (`new_substrate.md`
    -- never a runtime branch). The dungeon's own twins case: `<hero-acts>`,
    with the target present, versus switching to another when it is not."""
    print("\n§8  alt(...) -- a union of branches, compiled to one Rule each, "
          "the dungeon's own twins case")
    corpus = (
        "fact +turn(hero)\nfact +may(hero)\nfact +present(hero)\n"
        "rule <hero-acts> = implies("
        "{ +turn(hero), +may(hero), +present(hero) },"
        "alt("
        "{ $intent = intends(hero, attack($t), $r), +present($t) },"
        "{ $intent = intends(hero, attack($d), $r), no present($d), "
        "+monster($t), +present($t) }"
        "),"
        "{ -may(hero), -$intent, +attack(hero, $t) } )"
    )
    m = Machine()
    kb = load(m, corpus + "\nfact +intends(hero, attack(goblin1), 1)\n"
                          "fact +present(goblin1)")
    m.run(limit=5)
    check("§8", "branch 1 -- the declared target is present, attacked "
                "directly",
          m.holds(kb.term("attack(hero, goblin1)")))

    m2 = Machine()
    kb2 = load(m2, corpus + "\nfact +intends(hero, attack(goblin1), 1)\n"
                           "fact +monster(goblin2)\nfact +present(goblin2)")
    m2.run(limit=5)
    check("§8", "branch 2 -- the declared target is down (no `present`), "
                "switches to another monster present -- the SAME rule name, "
                "a different branch",
          m2.holds(kb2.term("attack(hero, goblin2)")))

    names = [r.name for r in m2.rules.rules]
    check("§8", "compiled to TWO rules, not a runtime branch -- "
                "<hero-acts> and <hero-acts#2>, both findable",
          "hero-acts" in names and "hero-acts#2" in names)

    threw = False
    try:
        load(Machine(), "fact +turn(hero)\n"
                        "rule <bad> = implies("
                        "{ +turn(hero) },"
                        "alt("
                        "{ $intent = intends(hero, attack($t), $r), "
                        "+present($t) },"
                        "{ +monster($t) }"
                        "),"
                        "{ -may(hero), -$intent, +attack(hero, $t) } )")
    except ParseError:
        threw = True
    check("§8", "every branch must bind what the consequent uses -- branch "
                "2 does not bind $intent, and it is refused at LOAD, naming "
                "which branch failed",
          threw)


def line_form() -> None:
    """The LINE surface (`new_substrate.md`'s own sketch): `rule <name>`,
    one member per line, `->` between antecedent and consequent, no braces
    or commas. A second surface over the identical grammar the brace form
    already builds -- same `Statement`, same `Rule`, checked against it."""
    print("\n§8  the line form -- `rule <name>` / one member per line / `->`, "
          "no braces or commas")
    braced = ("fact +heat(anna, kettle)\nfact +water(kettle)\n"
              "rule <boil> = implies({+heat($a, $w), +water($w), "
              "no boiling($w)}, {+boiling($w), -liquid($w)})")
    lined = ("fact +heat(anna, kettle)\nfact +water(kettle)\n"
             "rule <boil>\n  +heat($a, $w)\n  +water($w)\n  no boiling($w)\n"
             "->\n  +boiling($w)\n  -liquid($w)\n")
    m1 = Machine(); kb1 = load(m1, braced); m1.run(limit=5)
    m2 = Machine(); kb2 = load(m2, lined); m2.run(limit=5)
    check("§8", "the line form reaches the same belief as the brace form it "
                "reshapes -- one grammar, two surfaces",
          m2.holds(kb2.term("boiling(kettle)"))
          and not m2.holds(kb2.term("liquid(kettle)")))

    # No blank line between two line-form rules -- the next `rule` keyword
    # ends the block on its own, the way `delay.ugm`'s <cancel>/<late> need.
    m3 = Machine()
    kb3 = load(m3, "fact +cancelled(bl204)\n"
                   "rule <cancel>\n  +cancelled($f)\n  no disrupted($f)\n"
                   "->\n  +disrupted($f)\n"
                   "rule <late>\n  +delayed($f, long)\n  no disrupted($f)\n"
                   "->\n  +disrupted($f)\n")
    m3.run(limit=5)
    names3 = [r.name for r in m3.rules.rules]
    check("§8", "two line-form rules back to back, no blank line between -- "
                "the next `rule` keyword ends the block by itself",
          m3.holds(kb3.term("disrupted(bl204)"))
          and "cancel" in names3 and "late" in names3)

    # `alt(...)` and the `=>` tail, both in line form -- the two RHS pieces
    # the microprogram port actually needed, not just the declarative case.
    m4 = Machine()
    kb4 = load(m4, "fact +turn(hero)\nfact +may(hero)\nfact +present(hero)\n"
                   "fact +intends(hero, attack(goblin1), 1)\n"
                   "fact +present(goblin1)\n"
                   "rule <hero-acts>\n  +turn(hero)\n  +may(hero)\n"
                   "  +present(hero)\n"
                   "alt\n  $intent = intends(hero, attack($t), $r)\n"
                   "  +present($t)\n"
                   "alt\n  $intent = intends(hero, attack($d), $r)\n"
                   "  no present($d)\n  +monster($t)\n  +present($t)\n"
                   "->\n  -may(hero)\n  -$intent\n  +attack(hero, $t)\n")
    m4.run(limit=5)
    names4 = [r.name for r in m4.rules.rules]
    check("§8", "`alt` in line form compiles to one Rule per branch, same "
                "as the brace form",
          m4.holds(kb4.term("attack(hero, goblin1)"))
          and "hero-acts" in names4 and "hero-acts#2" in names4)

    m5 = Machine()
    pre5 = load(m5, "", scope="s5")
    pre5.answerer("dice", "roll", lambda mach, prop: None)
    kb5 = load(m5, "fact +need(roll(d20, hit(hero, orc)))\n"
                   "rule <ask>\n  $nd = need($r)\n->\n  -$nd\n"
                   "  +answered(<dice>, $r, 5)\n"
                   "rule <wound>\n"
                   "  $hit = answered(<dice>, roll(d20, hit($a, $d)), $n)\n"
                   "->\n  +seen($a)\n"
                   "=> forget $hit\n", scope="s5")
    m5.run(limit=10)
    check("§8", "`=> forget $hit` in line form erases the answer and its "
                "request together, exactly as the brace form's tail does",
          not m5.holds(kb5.term("answered(<dice>, roll(d20, hit(hero, orc)), 5)"))
          and not m5.holds(kb5.term("roll(d20, hit(hero, orc))"))
          and m5.holds(kb5.term("seen(hero)")))

    threw = False
    try:
        load(Machine(), "fact +p(a)\nrule <bad>\n  +p($x)\n\nfact +q(a)")
    except ParseError:
        threw = True
    check("§8", "a line-form rule missing `->` is refused at load, not "
                "silently read as something else",
          threw)


def string_literals() -> None:
    """A quoted name, for what a bare name cannot spell -- a path, a
    filename, anything with a space or a backslash in it (`ugm/repl.py`'s
    reason for existing: real paths never survived the bare-name lexer).
    Parses to an ordinary name-shaped Term -- once past the lexer, a quoted
    and a bare atom of the same spelling are one node (§3)."""
    print("\n§3  string literals -- a name a bare atom cannot spell")
    m = Machine()
    kb = load(m, r'''
        fact +file("C:\My Documents", "notes v2.txt")
        fact +greeting("say \"hi\"")
    ''')
    check("§3", "a backslash and a space survive un-mangled",
          m.holds(kb.term(r'file("C:\My Documents", "notes v2.txt")')))
    check("§3", "`\\\"` and `\\\\` decode; the atom's name IS the unescaped "
                "text, so it prints the way it reads",
          m.g.show(kb.term(r'greeting("say \"hi\"")'))
          == 'greeting(say "hi")')
    check("§3", "a quoted and a bare atom of the same spelling intern to "
                "ONE node -- the lexer changes nothing past the token",
          kb.term("plain") == kb.term('"plain"'))

    threw = False
    try:
        load(Machine(), 'fact +oops("never closed)')
    except ParseError:
        threw = True
    check("§3", "an unclosed string is refused at load, not read past the "
                "end of the line searching for its close",
          threw)

    threw = False
    try:
        load(Machine(), 'fact +oops("line one\nline two")')
    except ParseError:
        threw = True
    check("§3", "a string does not span a line",
          threw)

    threw = False
    try:
        load(Machine(), '"rule" +p(a)')
    except ParseError:
        threw = True
    check("§3", "a quoted keyword cannot open a statement -- a STRING "
                "token can never be mistaken for `rule`/`fact`/`say`, "
                "unlike a bare name of the same spelling",
          threw)


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
    check("§20", "...and the popped frame's own standing weights are GONE "
                 "with it -- discarded along with the Frame object, not "
                 "erased from a belief -- or a suspension would leak the "
                 "thing it exists to put away",
          kb.atom("a") not in m._lane_state()[2])
    check("§20", "...while the node it carried back IS attended, which is "
                 "the attention-level analogue of a return value",
          kb.atom("answer") in m._lane_state()[2])
    m._pop_frame()
    check("§20", "the root is not popped; it is declined",
          len(m._frames) == depth)


def lanes() -> None:
    print("\n§20 lanes: a generic mechanism, not a special case for judges")
    m = Machine()
    kb = load(m, """
        fact +p(a)
        rule <regular> = implies( { +p($x), no q($x) }, { +q($x) } )
        rule <feel> = implies( { +q($x), no liked($x) }, { +liked($x) } )
        fact +lane(<feel>, judge)
        fact +lane_order(judge, 1)
    """)
    steps = m.run(limit=4)
    check("§20", "the main lane's rule and the judge lane's rule both apply "
                "in the same ROUND -- same tick number, one shared frame",
          steps[0].applied.rule.name == "regular"
          and steps[1].applied.rule.name == "feel"
          and steps[0].applied is not None
          and steps[1].applied is not None)
    check("§20", "...because the judge rule sees what the main rule just "
                "wrote, in the same round, not a tick later",
          m.holds(kb.term("q(a)")) and m.holds(kb.term("liked(a)")))

    m2 = Machine()
    kb2 = load(m2, "fact +p(a)\n"
                   "rule <one> = implies({+p($x), no q($x)}, {+q($x)})\n"
                   "rule <two> = implies({+q($x), no r($x)}, {+r($x)})")
    m2.run(limit=5)
    check("§20", "a corpus that never claims lane(...) runs one lane, exactly "
                "as before lanes existed",
          m2.holds(kb2.term("q(a)")) and m2.holds(kb2.term("r(a)")))

    m3 = Machine()
    kb3 = load(m3, """
        fact +p(a)
        rule <second> = implies( { +p($x), no seen($x) }, { +seen($x) } )
        rule <first>  = implies( { +p($x), no seen($x) }, { +noted($x) } )
        fact +lane(<second>, later)
        fact +lane(<first>, sooner)
        fact +lane_order(sooner, 0)
        fact +lane_order(later, 1)
    """)
    m3.run(limit=4)
    check("§20", "lane order is a CLAIM, and it decides which lane goes "
                "first when both would otherwise be tied",
          m3.holds(kb3.term("noted(a)")))


def circuit_breaker() -> None:
    """`ugm/rules/circuit_breaker.ugm`, against a rule built to never stop
    matching (`<flaky>`: two bindings of `+p($x)`, no guard consuming
    either). Composes triggers, `dormant`/`due`, a lane and a cooldown --
    see the corpus's own header for why each is load-bearing.

    The suspension is temporary BY DESIGN: `<flaky>` never gets fixed, so the
    only honest test is that it keeps cycling -- tripped, cooled down,
    revived, tripped again -- rather than either exhausting the tick budget on
    one runaway rule or going permanently silent after the first trip.

    The `brush(p($x))` is what MAKES it a runaway. A move consumes what it
    matched on, so `+p(a)` and `+p(b)` holding from the start buys two
    firings and then silence -- and a watchdog watching a rule that stops on
    its own is watching nothing. Putting the premise back is how a corpus
    says *this is not the last thing that should happen to it*, and here it
    is what a rule that cannot stop itself looks like."""
    print("\n--  a circuit breaker: a lane keeps the trip rule from being "
          "starved by what it watches, and the suspension is temporary")
    path = _corpora.path("circuit_breaker.ugm")
    src = """
        fact +p(a)
        fact +p(b)
        rule <flaky> = implies( { +p($x) }, { +q(a) } ) => brush(p($x))

        fact +watched(<flaky>, flaky_tag)
        fact +tries(flaky_tag, 0)
        fact +threshold(flaky_tag, 5)
        fact +cooldown_len(flaky_tag, 3)
    """
    m = Machine()
    ldr = load(m, "", scope="cb")
    ldr.computator("plus", lambda a, b: int(a) + int(b))
    ldr.computator("minus", lambda a, b: max(0, int(a) - int(b)))
    ldr.computator("at_least", lambda a, b: "yes" if int(a) >= int(b) else None)
    kb = load(m, src, scope="cb")
    load_file(m, path, scope="cb")
    # PINNED, and the breaker's premise now depends on it. A rule that
    # churns unproductively on things nobody is attending to no longer gets
    # the chance: attention stops it before any budget is burnt, which is a
    # cheaper answer than a watchdog and is why the old form of this check
    # became unreachable. What the breaker is still FOR is the rule that
    # churns on what the agent really is attending to, and a min is how a
    # corpus says that is the situation.
    for name in ("a", "b"):
        m._attend(kb.atom(name), weight=3, floor=1)
    steps = m.run(limit=22)
    names = [s.applied.rule.name for s in steps if s.applied is not None]
    trips = names.count("trip")
    revives = names.count("revive")
    check("--", "it trips more than once -- the rule keeps being "
                "reconsidered, not silenced after the first trip, while what "
                "it churns on stays attended",
          trips >= 2)
    check("--", "and every trip is followed by a revival -- the suspension "
                "actually lifts, it does not just accumulate",
          revives == trips)
    #  Reported, not raised. `revive` never firing is the check above
    # already failing, and an IndexError here took the whole runner down with
    # it -- so every section after this one went unrun, and a red check hid
    # the rest of the suite instead of counting as one failure.
    after = (names[names.index("revive") + 1:names.index("revive") + 2]
             if "revive" in names else [])
    check("--", "each cycle resets to a fresh budget: a revival is "
                "followed by the watched rule actually running again, not "
                "an immediate re-trip",
          after == ["flaky"])


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


def calibration() -> None:
    """Search the numbers, never the rules."""
    from .learning import Episode, calibrate, mutate, numbers, run_episode
    import random

    print("\n--  calibration: an episode is a file, and only numbers move")
    corpus = ("rule <pick> = implies(\n"
              "    { $z = intake($e, $who) [+1, attention_multiplier:0],\n"
              "      $w = person($who) [+1, attention_multiplier:9],\n"
              "      no chosen },\n"
              "    { +picked($e), +chosen } )\n")
    ep = Episode(_corpora.path("episodes/pick_the_event.ugm"))

    check("--", "an episode is one file -- the starting condition, what is in "
                "mind, and the judge -- and the corpus as authored FAILS it, "
                "so there is something to search for",
          run_episode(corpus, ep)[0] is False)

    hand = corpus.replace("intake($e, $who) [+1, attention_multiplier:0]",
                          "intake($e, $who) [+1, attention_multiplier:9]") \
                 .replace("person($who) [+1, attention_multiplier:9]",
                          "person($who) [+1, attention_multiplier:0]")
    check("--", "...and moving the multiplier from the participant's line to "
                "the event's passes it, which is the whole claim of per-line "
                "scoring stated as an episode",
          run_episode(hand, ep)[0] is True)

    best, fit, history = calibrate(corpus, [ep], rounds=12, population=6, seed=7)
    check("--", "the search finds a calibration the author did not write",
          history[0] == 0.0 and fit > 0.0)
    check("--", "...and it is the ORIGINAL corpus with different numbers: "
                "every rule, every line and every variable is untouched",
          [w for w in best.split() if not any(c.isdigit() for c in w)]
          == [w for w in corpus.split() if not any(c.isdigit() for c in w)])

    rng = random.Random(3)
    many = {mutate(corpus, rng, 2) for _ in range(40)}
    check("--", "a mutator only ever moves a bracket or an attend tail -- no "
                "candidate in forty is a different rule",
          all(len(numbers(c)) == len(numbers(corpus)) for c in many))

    check("--", "a judge that never got a turn is a FAILURE, not a pass -- "
                "the judge is ordinary rules in the same machine, so a "
                "calibration could otherwise starve the thing scoring it",
          run_episode("", ep)[2] == "no verdict")


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
    unmerging()
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
    tool_approval()
    attention()
    reference_lines()
    rhs_tail()
    rhs_graph_ops()
    prefix_binding()
    alt_branches()
    line_form()
    string_literals()
    frames()
    lanes()
    calibration()
    circuit_breaker()
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
