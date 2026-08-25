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
    print("\n§14 firing is not arbitrated any more (docs/design/"
          "intensity-gates.md) -- every rule whose gates are on fires, so "
          "there is no winner to pick and nothing for one rule to defer to "
          "another. `arbitrate` itself survives as a generic utility (a "
          "caller that wants ONE application from several still has "
          "something total to call), but the LOOP does not call it.")
    m = Machine()
    kb = load(m, """
        fact +p(a)
        rule <one> = implies( { keep p($x), no q($x) }, { +q($x) } )
        rule <two> = implies( { keep p($x), no r($x) }, { +r($x) } )
    """)
    steps = [s for s in m.run(limit=8) if s.applied]
    check("§14", "two rules matching one tick's opening state both fire "
                 "that tick -- neither is deferred, because nothing is "
                 "choosing between them",
          bool(steps) and
          {a.rule.name for a in steps[0].applied} == {"one", "two"})
    check("§14", "...and both conclusions land -- `keep` is what let both "
                 "rules read `p(a)` without either's firing spending the "
                 "other's premise",
          m.holds(kb.term("q(a)")) and m.holds(kb.term("r(a)"))
          and m.holds(kb.term("p(a)")))
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
    names = [a.rule.name for s in steps for a in s.applied]
    check("§16", "a `+` consequent anchors what the rule concluded",
          "off" in names and m.holds(kb.term("boiling(kettle)")))
    check("§16", "a `-` consequent ERASES, which is the un-claim an "
                 "append-only chain could never express -- back to nothing, "
                 "with no scar",
          not m.holds(kb.term("heat(stove, kettle)")))
    check("§16", "TWO erasures land at the gate, and only one of them is "
                 "the rule's own explicit `-heat` -- `<off>`'s antecedent "
                 "also plainly matches `cold($w)`, and default consumption "
                 "spends that occasion too even though nothing in the "
                 "consequent ever mentions it", m.gate.erasures == 2)
    check("§16", "...and the rule guarded by `no cold` never applied, so "
                 "absence gated a conclusion rather than denying one",
          "boil" not in names)

    #  Firing discharges by default (docs/design/intensity-gates.md) -- and
    # this is exactly the "guarded rule doesn't re-derive" pattern
    # (watching/25-own-state.md) becoming the SUBSTRATE's default instead
    # of something a corpus writes by hand. Two rules that answer each
    # other -- `<boil>` derives `boiling`, `<off>` retracts it -- used to
    # need a guard of their own or oscillate forever; here `<boil>` cannot
    # re-match once its own `heat` premise is spent, and `<off>` cannot
    # re-match once ITS `boiling` premise is spent, so the pair settles on
    # its own with no guard written anywhere in the corpus.
    osc = Machine()
    osc_kb = load(osc, """
        fact +heat(stove, kettle)
        fact +cold(kettle)
        rule <boil> = implies( { +heat($a, $w) }, { +boiling($w) } )
        rule <off>  = implies( { +boiling($w), +cold($w) }, { -boiling($w) } )
    """)
    osc_steps = osc.run(limit=12)
    check("§16", "a corpus whose rules answer each other still reaches "
                 "quiescence -- consumption is what used to need writing by "
                 "hand (§25's guard) and does not any more",
          osc_steps[-1].state == "quiescent")
    check("§16", "...and the LAST thing to hold the floor is `<off>`'s own "
                 "erasure: `boiling` fired, then was retracted, and nothing "
                 "is left to re-derive it because `heat` is spent too",
          not osc.holds(osc_kb.term("boiling(kettle)"))
          and not osc.holds(osc_kb.term("heat(stove, kettle)")))

    #  There is no inert set EITHER -- but there does not need to be one any
    # more. A rule whose premise firing just spent cannot match again
    # without something recharging it, so "a rule that already gave what it
    # has costs nothing to re-offer" (the old inert-set argument) is now
    # true for a different, cheaper reason: there is nothing left to offer
    # it against.
    m2 = Machine()
    kb2 = load(m2, """
        fact +p(a)
        rule <one> = implies( { +p($x) }, { +q($x) } )
    """)
    steps2 = m2.run(limit=20)
    check("§6", "a rule fires once against a plain fact and then has nothing "
                "left to match -- quiescent well under the tick limit, with "
                "no guard (`no q($x)`) written anywhere",
          steps2[-1].state == "quiescent" and len(steps2) < 20
          and m2.holds(kb2.term("q(a)")) and not m2.holds(kb2.term("p(a)")))

    #  A corpus that wants today's persistence writes `keep` where it reads
    # the fact -- the escape hatch, and this is the direct comparison: same
    # rule, `keep` added, and `p(a)` survives its own firing.
    m2b = Machine()
    kb2b = load(m2b, """
        fact +p(a)
        rule <one> = implies( { keep p($x), no q($x) }, { +q($x) } )
    """)
    steps2b = m2b.run(limit=20)
    check("§6", "...`keep` gets today's persistence back -- p(a) survives, "
                "and the rule still settles because its OWN `no q($x)` "
                "guard is what stops the re-derivation this time, not "
                "spending the premise",
          steps2b[-1].state == "quiescent"
          and m2b.holds(kb2b.term("p(a)")) and m2b.holds(kb2b.term("q(a)")))

    #  The other guard, and the one the dungeon used for its whole turn
    # order: SPEND what you matched. An occasion is consumed, a fact is not
    # -- and this used to be something `-may(hero)` had to say explicitly.
    # It is now what a bare `+may(hero)` already does.
    m2c = Machine()
    kb2c = load(m2c, """
        fact +may(hero)
        rule <act> = implies( { +may(hero) }, { +acted(hero) } )
    """)
    steps2c = m2c.run(limit=20)
    check("§6", "spending the premise stops the rule too, and it is now the "
                "DEFAULT rather than an explicit `-may(hero)` a corpus had "
                "to remember to write",
          steps2c[-1].state == "quiescent"
          and m2c.holds(kb2c.term("acted(hero)"))
          and not m2c.holds(kb2c.term("may(hero)")))



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


# -- reference lines and the RHS tail ---------------------------------------


def reference_lines() -> None:
    """`label($x, the-kettle)` -- a PREDICATE (`new_substrate.md`): a filter
    over an already-bound node, never matched, never bound to.

    `attentioned($x)` was the other one and is retired with the focus pool
    it asked about (docs/design/intensity-gates.md); its three checks are
    in `focus_is_retired()` now, as *this surface is gone* rather than
    *this surface works*. It picked a REFERENT out of what the agent was
    thinking about -- deixis, not a relevance gate -- and there is nothing
    left to pick a referent out of. A corpus that wants "the one in play"
    reads an ordinary claim about it, which is what `dungeon_gut.ugm`'s
    `eyeing(hero, $e)` became.
    """
    print("\n§20 reference lines -- label($x, the-kettle) filters an "
          "already-bound node, it does not match or bind one")
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
    """The RHS's ordered tail (`new_substrate.md`) -- an op written directly
    on the rule, unconditional, no separate `after` statement.

    Reuses the trigger BACKEND (`m.rules.triggers`, keyed on empty query) --
    RHS supersedes the no-query case of triggers rather than duplicating it,
    which is why no executor code is new here, only the front door.

    The tail's original tenant was `attend($x, 3)` -- three checks about a
    learned weight, a control with no tail, and a negative weight read by
    magnitude. All three are retired with the focus pool
    (docs/design/intensity-gates.md); what they were really demonstrating,
    that the tail names the HOST RULE's own variable rather than a fresh
    one, is checked below with an op that survived.
    """
    print("\n§20 the RHS's ordered tail -- an op written on the rule itself, "
          "no separate trigger statement")
    m = Machine()
    kb = load(m, "fact +happy(paul)\n"
                 "rule <r1> = implies({+happy($x)}, {+noticed($x)}) "
                 "=> destroy($x)")
    paul = kb.atom("paul")
    m.run(limit=3)
    #  `show` is what `delete` changes for every node kind, atom included
    #  -- see `rhs_graph_ops`'s own note on why `relation_of` cannot answer
    #  this for a bare atom.
    check("§20", "the tail's `destroy($x)` names the rule's OWN $x -- the "
                 "node this application bound, with no separate "
                 "`after <r1> => ...` statement anywhere in this corpus",
          m.g.show(paul) == f"#{paul}(erased)")

    m2 = Machine()
    kb2 = load(m2, "fact +happy(paul)\n"
                   "rule <r1> = implies({+happy($x)}, {+noticed($x)})")
    paul2 = kb2.atom("paul")
    m2.run(limit=3)
    check("§20", "...and the same rule with no tail leaves it alone -- "
                 "control",
          m2.g.show(paul2) == "paul")

    m3 = Machine()
    kb3 = load(m3, "fact +happy(paul)\nfact +happy(mary)\n"
                   "rule <r1> = implies({+happy($x)}, {+noticed($x)}) => stop")
    steps = m3.run(limit=10)
    noticed = sum(1 for n in ("paul", "mary")
                  if m3.holds(kb3.term(f"noticed({n})")))
    check("§20", "`stop` ends the RUN, not one application -- both bindings "
                 "of `<r1>` matched the SAME tick's opening state and both "
                 "fired together (docs/design/intensity-gates.md: firing "
                 "order inside a tick cannot matter, so there is no "
                 "'partway through this tick' left for `stop` to cut at), "
                 "and `stopped` is what ends the tick AFTER",
          steps[-1].state == "stopped" and noticed == 2)


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
    m1 = Machine(); kb1 = load(m1, braced)
    m1.run(limit=5)
    m2 = Machine(); kb2 = load(m2, lined)
    m2.run(limit=5)
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


def focus_is_retired() -> None:
    """The focus pool and the frame stack, both gone (docs/design/
    intensity-gates.md).

    This function is what is left of `attention()` and `frames()`, which
    between them held sixteen checks: a queue bounded by time rather than
    length, a claim outliving its own move's bookkeeping, a faded claim
    coming back at what it was worth, `floor`/`ceiling` as pin and cap,
    `push` opening a frame and `pop` returning one node to the frame below,
    a re-push of the same nodes declined as a loop, and the popped frame's
    standing weights going with the frame.

    All sixteen answered *which of the things it could work on does the
    agent work on next*, and nothing asks that any more: a rule fires
    whenever its own antecedent is on. What survives of the question is
    ON/OFF itself, which is `firing.py`'s own worked examples and the
    `keep`/discharge checks in `applying()`. What is checked here is only
    that the vocabulary is gone rather than quietly ignored -- a corpus
    written against the old surface must fail to load, not load and do
    nothing.
    """
    print("\n§20 the focus pool and the frame stack are retired -- their "
          "surface is refused at load rather than accepted and ignored")
    for src, what in (("rule <r> = implies({+p($x)}, {+q($x)}) => attend($x, 3)",
                       "attend"),
                      ("rule <r> = implies({+p($x)}, {+q($x)}) => brush($x)",
                       "brush"),
                      ("rule <r> = implies({+p($x)}, {+q($x)}) => unattend",
                       "unattend"),
                      ("rule <r> = implies({+p($x)}, {+q($x)}) => push($x)",
                       "push"),
                      ("rule <r> = implies({+p($x)}, {+q($x)}) => pop($x)",
                       "pop")):
        try:
            load(Machine(), src)
            refused = False
        except ParseError:
            refused = True
        check("§20", f"`{what}` as a postcondition is a ParseError, not a "
                     f"silent no-op", refused)

    m = Machine()
    try:
        load(m, "fact +happy(paul)\n"
                "rule <r> = implies({+happy($x), attentioned($x)}, "
                "{+noticed($x)})")
        m.run(limit=3)
        # It loads -- `attentioned` is an ordinary name now, so this is an
        # ordinary MEMBER nothing anchors rather than a predicate. What must
        # not happen is it opening on its own.
        opened = m.holds(m.g.rel(m.g.atom("noticed"), m.g.atom("paul")))
    except ParseError:
        opened = False
    check("§20", "`attentioned($x)` is no longer a predicate the engine "
                 "answers -- a rule asking it gets nothing, rather than a "
                 "filter over a pool that is not there", not opened)

    check("§20", "and the machinery it drove is gone from `Machine` "
                 "outright, not left dormant",
          not any(hasattr(Machine(), a) for a in
                  ("_attend", "_attended", "_unattend", "_fade_attention",
                   "_push_attention", "_attend_written", "_consume",
                   "_frames", "_push_frame", "_pop_frame", "_lane_state")))


def lanes() -> None:
    print("\n§20 lanes are retired (docs/design/intensity-gates.md) -- "
          "starvation was a fact about ONE selection per tick, and there is "
          "no selection any more")
    # `lane(...)`/`lane_order(...)` are gone: nothing interprets them now
    # (the atoms stay reserved so a corpus that still writes them loads
    # rather than erroring, but they do nothing -- see `machine.py`'s
    # comment on `STANDING`/`LANE`/`LANE_ORDER`). The scenario lanes existed
    # to solve -- book/docs/watching/28-the-table.md's `<loud>`/`<watch>` --
    # is this function's replacement: a rule that matches every tick and
    # never stops matching used to starve any rule ranked with or below it,
    # because only one rule was picked per tick. Nothing picks now, so
    # `<watch>` needs no lane of its own to get a turn -- it just fires
    # whenever ITS OWN gates are on, the same tick as `<loud>` or any other.
    m = Machine()
    kb = load(m, """
        fact +running
        rule <loud>  = implies( { keep running }, { +shouted } )
        rule <watch> = implies( { keep running, no watched }, { +watched } )
    """)
    m.run(limit=3)
    check("§20", "the never-yielding rule and the rule that only needs one "
                "turn both fire -- no lane, no starvation, because there "
                "was never a single per-tick slot to starve `<watch>` out "
                "of",
          m.holds(kb.term("shouted")) and m.holds(kb.term("watched")))

    m2 = Machine()
    kb2 = load(m2, "fact +p(a)\n"
                   "rule <one> = implies({+p($x), no q($x)}, {+q($x)})\n"
                   "rule <two> = implies({+q($x), no r($x)}, {+r($x)})")
    m2.run(limit=5)
    check("§20", "a chain of two rules still reaches the end of the chain -- "
                "one more tick than the lane era's same-round visibility "
                "bought it (a tick matches the state as it STARTS, so "
                "`<two>` sees `q(a)` the tick after `<one>` writes it, not "
                "the same one), but it gets there. `q(a)` itself is spent "
                "by the time it does -- `<two>`'s own plain `+q($x)` "
                "discharges it on the very firing that reads it, which is "
                "this file's other running theme and not a lane question",
          not m2.holds(kb2.term("q(a)")) and m2.holds(kb2.term("r(a)")))


def circuit_breaker() -> None:
    """`ugm/rules/circuit_breaker.ugm`, against a rule built to never stop
    matching (`<flaky>`: two bindings of `+p($x)`, RECHARGED by its own
    consequent rather than never spending it in the first place -- see
    below). Composes triggers, `dormant`/`due`, and a cooldown counter; see
    the corpus's own header for why each is load-bearing and why lanes,
    the fourth piece the old version needed, are not any more.

    The suspension is temporary BY DESIGN: `<flaky>` never gets fixed, so the
    only honest test is that it keeps cycling -- tripped, cooled down,
    revived, tripped again -- rather than either exhausting the tick budget on
    one runaway rule or going permanently silent after the first trip.

    Firing discharges by default now (docs/design/intensity-gates.md), so
    `brush(p($x))` -- the table era's way of putting a spent premise back --
    is retired along with the mechanism it was for: `<flaky>`'s own
    consequent recharges `p($x)`, the SAME node its antecedent just
    matched (a bound variable, not a fresh ground literal -- see
    `core/firing.py`'s own worked example for why that distinction is
    load-bearing), so the discharge and the recharge fold to the same
    number this tick and `p($x)` never actually goes off. That is what a
    rule that cannot stop itself looks like now."""
    print("\n--  a circuit breaker: every rule fires whenever its own gates "
          "are on, so the trip/cooldown/revive rules need no guaranteed "
          "turn independent of the rule they watch -- and the suspension "
          "is still temporary")
    path = _corpora.path("circuit_breaker.ugm")
    src = """
        fact +p(a)
        fact +p(b)
        rule <flaky> = implies( { +p($x) }, { +q(a), +p($x) } )

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
    #  531 ticks -- the same budget `book/docs/watching/28-the-table.md`
    # measured the table-era breaker against (31 clean cycles there). Both
    # bindings of `<flaky>` fire every tick they can now rather than one
    # being picked, so the trip rate is not expected to match -- what has
    # to match is the CLAIM: never stuck, every trip followed by a revival.
    steps = m.run(limit=531)
    names = [a.rule.name for s in steps for a in s.applied]
    trips = names.count("trip")
    revives = names.count("revive")
    check("--", "it trips more than once -- the rule keeps being "
                "reconsidered, not silenced after the first trip",
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
    print(f"     ({trips} trip/cooldown/revive cycles over "
          f"{len(steps)} ticks)")


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
    kb4 = load(m4, "fact +dormant(thing)")
    check("§22", "a reserved name in a corpus resolves to the machinery's own "
                 "node, not a twin with the same spelling",
          m4.g.relation_of(kb4.term("dormant(thing)")) is m4.DORMANT)


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
    """Search the numbers, never the rules.

    What the numbers ARE has moved twice. Per-line scoring's own episode
    (`pick_the_event.ugm`) went with the pick it demonstrated: it existed to
    show a search finding which of a rule's several matched applications an
    `attention_multiplier` bracket should favour, and every application a
    rule finds fires now. `attend(...)` tails went with the focus pool one
    step later. What a corpus carries that a search can move is an
    INTENSITY -- how far ON a write turns something -- so that is what
    `numbers`/`mutate` walk (`ugm/learning/calibrate.py`). The
    judge-starvation guard below is a claim about the LOOP, not about
    scoring, and holds through all of it.
    """
    from .learning import Episode, mutate, numbers, run_episode
    import random

    print("\n--  calibration: search the numbers, never the rules -- and "
          "the numbers are intensities now")
    corpus = ("fact +happy(paul)\n"
              "rule <r1> = implies({+happy($x)}, {+noticed($x) intensity 3})\n")

    check("--", "an `intensity` write is what a mutator can see -- one "
                "number in this corpus, and it is that one",
          [corpus[a:b] for a, b, _k in numbers(corpus)] == ["3"])

    rng = random.Random(3)
    many = {mutate(corpus, rng, 2) for _ in range(40)}
    check("--", "a mutator only ever moves an intensity -- no candidate in "
                "forty is a different rule",
          len(many) > 1
          and all(len(numbers(c)) == len(numbers(corpus)) for c in many))
    check("--", "...and every candidate still LOADS -- a search that "
                "proposed unparseable text would be scoring nonsense",
          all(load(Machine(), c) is not None for c in many))
    check("--", "an intensity is never nudged below zero: zero is OFF, and "
                "there is nothing further down to reach",
          all(float(c[a:b]) >= 0
              for c in many for a, b, _k in numbers(c)))

    ep = Episode(_corpora.path("episodes/pick_the_event.ugm"))
    check("--", "a judge that never got a turn is a FAILURE, not a pass -- "
                "the judge is ordinary rules in the same machine, so a "
                "calibration could otherwise starve the thing scoring it",
          run_episode("", ep)[2] == "no verdict")


# -- the shipped corpora ----------------------------------------------------


def worked_corpora() -> None:
    print("\n--  the shipped corpora run")
    m = Machine()
    kb = load_file(m, _corpora.path("worked.ugm"))
    #  No kickoff needed any more. A `m._attend(...)` pair sat here while a
    # rule had to be thought about before it could be offered, so a corpus
    # whose start was purely loaded `fact`s did nothing at all. A rule
    # fires whenever its own antecedent is ON, and a loaded fact is on.
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


def todo_stack() -> None:
    """`ugm/rules/todo.ugm`: a standing anchor a corpus loads alongside its
    own (SAME `scope=`, or `task(...)` in each file mints a twin -- the
    same discipline `tool_approval()` above needs). Two arrivals landing
    together, arranged as a stack, both closed by a `judge`-lane rule the
    host corpus supplies -- todo.ugm writes no closing rule of its own."""
    print("\n--  the todo stack: a standing anchor, tasks pushed and popped, "
          "closed by the host corpus's own judge")
    path = _corpora.path("todo.ugm")

    m = Machine()
    load(m, "", scope="host")
    kb = load_file(m, path, scope="host")
    kb2 = load(m, """
        say user: +raining(here)
        say user: +snowing(there)

        rule <trust>
          +says($ch, $p)
          no believed($p)
        ->
          +believed($p)

        # The judge: todo.ugm ships no rule that concludes `completed(...)`
        # -- that is the host corpus's own business (its header says so).
        # `keep believed($said)`: firing discharges what it matches by
        # default now (docs/design/intensity-gates.md), and this judge is
        # not the rule that should retire a belief -- only the one that
        # reads it to decide a task is answered.
        rule <task-answered>
          +about($t, $said)
          keep believed($said)
          no completed($t)
        ->
          +completed($t)
        fact +lane(<task-answered>, judge)
    """, scope="host")
    steps = m.run(limit=100)

    check("--", "loading the file alone claims `pinned(internal_todo)` -- "
                "the anchor stands whether or not the host corpus ever says "
                "anything, off `todo.ugm`'s OWN arrival rather than the "
                "host's",
          m.holds(kb.term("pinned(internal_todo)")))
    tasks = [p for p in m.pad.believed() if m.g.relation_of(p) is kb.atom("task")]
    check("--", "two arrivals landing together are both opened as tasks, not "
                "just the one that wins the first tick -- the same starvation "
                "`delay.ugm` needed its own hop against",
          len(tasks) == 2)
    completed = [p for p in m.pad.believed()
                if m.g.relation_of(p) is kb.atom("completed")]
    check("--", "the host corpus's own judge rule closes both -- `keep` on "
                "`believed($said)` is what leaves the belief standing for "
                "the second to read after the first has fired",
          len(completed) == 2
          and m.holds(kb2.term("believed(raining(here))"))
          and m.holds(kb2.term("believed(snowing(there))")))
    #  LEFT RED, deliberately, rather than patched into a false green:
    # `<push-task>` reads the CURRENT top and writes the new one in the
    # same firing -- a read-modify-write -- and the two tasks this test
    # opens both become pushable in the SAME tick. Under the table era's
    # one-selection-per-tick arbitration that serialised them for free:
    # one push won the tick, the other's `$prev` was stale next tick, and
    # it re-read the fresh top and pushed correctly above it. Under this
    # design every application matches the tick's OPENING state and
    # firing order cannot matter (docs/design/intensity-gates.md) -- which
    # is exactly what removes the serialisation `<push-task>` was leaning
    # on: both pushes read the SAME stale `$prev` and both write a new
    # top, so the stack ends up with two simultaneous tops rather than one
    # stacked on the other. A stack's push is inherently sequential, and
    # nothing about "several rules fire together, order-independently" can
    # make two order-dependent writes to one pointer agree -- `todo.ugm`
    # would need restructuring (a push that only admits one task per tick,
    # or a stack that tolerates -- or is not modelled as -- concurrent
    # arrivals) to fix this honestly, which is out of this pass's scope.
    top = [p for p in m.g.instances_of(kb.atom("top")) if m.pad.holds(p)]
    check("--", "both popped -- the stack is back at its own sentinel, "
                "empty rather than merely quiet -- KNOWN RED: concurrent "
                "pushes in one tick race for the stack pointer, see the "
                "comment above",
          len(top) == 1 and m.g.member(top[0], 1) == kb.term("internal_todo"))
    #  `tasks` holds the `task($t)` PROPOSITIONS; `$t` is member 0. The
    # check this replaced read the focus pool and was handed the same list,
    # where every lookup missed and the `all(...)` passed vacuously.
    check("--", "a closed task is marked retired, so a rule can tell one "
                "the stack is done with from one still open",
          all(m.holds(m.g.rel(kb.atom("retired"), m.g.member(t, 0)))
              for t in tasks))


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
    reference_lines()
    rhs_tail()
    rhs_graph_ops()
    prefix_binding()
    alt_branches()
    line_form()
    string_literals()
    focus_is_retired()
    lanes()
    calibration()
    circuit_breaker()
    surface()
    the_web()
    worked_corpora()
    todo_stack()
    determinism()
    print(f"\n{COUNT} checks, {len(FAILED)} failing")
    for group, name in FAILED:
        print(f"  {group}  {name}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
