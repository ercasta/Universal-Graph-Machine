"""One runner. Every check prints its named observations; any False is a failure.

Checks are grouped by the section of `docs/rules-design.md` they hold to account.
"""

from typing import List, Tuple

from .chain import MINUS, PLUS, UNSURE, weaker
from .graph import Graph
from .machine import Machine
from .rules import CAUSES, IMPLIES, Member, RuleSet, effective_grade, unify

_results: List[Tuple[str, str, bool]] = []


def check(group: str, name: str, value: bool) -> None:
    _results.append((group, name, value))


# -- §3 the substrate -------------------------------------------------------


def substrate() -> None:
    g = Graph()
    on, a, b = g.atom("on"), g.atom("a"), g.atom("b")
    p1, p2 = g.rel(on, a, b), g.rel(on, a, b)
    check("§3", "a proposition has one identity however often it is built", p1 == p2)
    check("§3", "members are ordered", g.members(p1) == (a, b))
    check("§3", "on(a,b) and on(b,a) are different nodes", p1 != g.rel(on, b, a))
    x = g.var("?x")
    check("§3", "a pattern containing a variable is generic", g.has_var(g.rel(on, x, b)))
    check("§3", "a ground proposition is not", not g.has_var(p1))


# -- §4, §5, §6 moments, entries, signs -------------------------------------


def chain_reads() -> None:
    m = Machine()
    g, c = m.g, m.chain
    on, a, b = g.atom("on"), g.atom("a"), g.atom("b")
    p = g.rel(on, a, b)

    m0 = c.root
    m1 = c.succeed(m0, None)
    m2 = c.succeed(m1, None)

    c.deposit(seat=m1, locus=m1, proposition=p, sign=PLUS)
    check("§6", "an asserted proposition holds at its own locus", c.holds(p, m1, m2) == PLUS)
    check("§6", "no entry means inherit, not unknown", c.holds(p, m2, m2) == PLUS)
    check("§5", "a proposition with no entry claims nothing", c.holds(g.rel(on, b, a), m2, m2) is None)

    m3 = c.succeed(m2, None)
    c.deposit(seat=m3, locus=m3, proposition=p, sign=MINUS)
    check("§6", "a later locus overrides an earlier one", c.holds(p, m3, m3) == MINUS)
    check("§4", "the earlier moment is unchanged by the later claim", c.holds(p, m1, m3) == PLUS)

    m4 = c.succeed(m3, None)
    lvl = g.rel(g.atom("level"), g.atom("tank"))
    c.deposit(seat=m1, locus=m1, proposition=lvl, sign=PLUS)
    c.deposit(seat=m4, locus=m4, proposition=lvl, sign=UNSURE)
    check(
        "§6",
        "`?` invalidates without replacing -- it does not return the old value",
        c.holds(lvl, m4, m4) == UNSURE,
    )


def two_indices() -> None:
    """§17's first new gate: after revising a belief about an earlier moment, both
    questions answer, and answer differently."""
    m = Machine()
    g, c = m.g, m.chain
    tt = g.rel(g.atom("taking_turns"), g.atom("anna"), g.atom("bo"))

    m7 = c.succeed(c.root, None)
    for _ in range(4):
        m7 = c.succeed(m7, None)
    c.deposit(seat=m7, locus=m7, proposition=tt, sign=PLUS)

    m12 = m7
    for _ in range(5):
        m12 = c.succeed(m12, None)
    # I now think they were not taking turns then: same locus, later deposit.
    c.deposit(seat=m12, locus=m7, proposition=tt, sign=MINUS)

    check("§17", "what I now think about M7", c.holds(tt, m7, m12) == MINUS)
    check("§17", "what I thought at M7", c.holds(tt, m7, m7) == PLUS)
    check(
        "§17",
        "the two indices give different answers, so neither was lost",
        c.holds(tt, m7, m12) != c.holds(tt, m7, m7),
    )
    check(
        "§12",
        "nothing was invalidated: the original entry is still in its moment",
        any(e.proposition == tt and e.sign == PLUS for e in m7.delta),
    )


# -- §13 the gate and frames ------------------------------------------------


def gate() -> None:
    m = Machine()
    g, c, gate_ = m.g, m.chain, m.gate
    p = g.rel(g.atom("rain"), g.atom("tuesday"))

    past = c.succeed(c.root, None)
    now = c.succeed(past, None)

    f = gate_.frame(seat=now, topic=past)
    e = gate_.write(f, p, PLUS, licence=g.atom("supposing"))
    check("§13", "the locus is stamped from the frame's topic", e.locus is past)
    check("§13", "the deposit is the frame's seat", e in now.delta)
    check("§13", "about-when and believed-since differ, honestly", e.locus is not now)

    ok = False
    try:
        gate_.frame(seat=past, topic=now)
    except ValueError:
        ok = True
    check("§13", "a seat before its topic is refused where it is minted", ok)

    ok = False
    try:
        gate_.write(f, g.rel(g.atom("rain"), g.var("?d")), PLUS)
    except ValueError:
        ok = True
    check("§13", "a generic proposition cannot be deposited", ok)

    f2 = gate_.frame(seat=now)
    check("§13", "topic defaults to the seat", f2.topic is now)
    check("§13", "frames form a forest: ancestry is derived", gate_.frame(now, parent=f2).ancestry()[-1] is f2)


# -- §12 grades -------------------------------------------------------------


def grades() -> None:
    check("§12", "weakest link picks the weaker", weaker("certain", "possible") == "possible")
    check("§12", "and is symmetric", weaker("possible", "certain") == "possible")

    m = Machine()
    g, c = m.g, m.chain
    p = g.rel(g.atom("said"), g.atom("x"))
    e = c.deposit(seat=c.root, locus=c.root, proposition=p, sign=PLUS, grade="possible")
    check(
        "§17",
        "no laundering: a @certain rule over a merely-possible premise concludes possible",
        effective_grade("certain", [e]) == "possible",
    )
    check(
        "§12",
        "a rule cannot strengthen its own premises",
        effective_grade("certain", [e]) != "certain",
    )


# -- §8, §14 rules, match, arbitration --------------------------------------


def matching() -> None:
    g = Graph()
    on, a, b = g.atom("on"), g.atom("a"), g.atom("b")
    x = g.var("?x")
    bound = unify(g, g.rel(on, x, b), g.rel(on, a, b), {})
    check("§14", "match binds a variable to what it met", bound is not None and bound[x] == a)
    check("§14", "match fails on a different relation", unify(g, g.rel(on, x, b), g.rel(g.atom("in"), a, b), {}) is None)
    y = g.var("?y")
    check(
        "§14",
        "a variable used twice must bind consistently",
        unify(g, g.rel(on, y, y), g.rel(on, a, b), {}) is None,
    )


def arbitration_is_total() -> None:
    m = Machine()
    g = m.g
    p, q = g.atom("p"), g.atom("q")
    lit = g.atom("lit")
    r1 = m.rules.rule(IMPLIES, [Member(PLUS, g.rel(lit, p))], [Member(PLUS, g.rel(lit, q))], "R1")
    r2 = m.rules.rule(IMPLIES, [Member(PLUS, g.rel(lit, p))], [Member(MINUS, g.rel(lit, q))], "R2")
    m.gate.write(m.focus, g.rel(lit, p), PLUS)

    step = m.tick()
    check("§14", "with two rules matching, arbitration still answers", step.applied is not None)
    check("§14", "and it answers by authored order when nothing overrides", step.applied.rule is r1)

    m2 = Machine()
    g2 = m2.g
    lit2, p2, q2 = g2.atom("lit"), g2.atom("p"), g2.atom("q")
    a1 = m2.rules.rule(IMPLIES, [Member(PLUS, g2.rel(lit2, p2))], [Member(PLUS, g2.rel(lit2, q2))], "A1")
    a2 = m2.rules.rule(IMPLIES, [Member(PLUS, g2.rel(lit2, p2))], [Member(MINUS, g2.rel(lit2, q2))], "A2")
    m2.rules.overrides_rule(a2, a1)
    m2.gate.write(m2.focus, g2.rel(lit2, p2), PLUS)
    step2 = m2.tick()
    check("§14", "authored precedence beats authored order", step2.applied.rule is a2)

    # Defeat, not ranking: ordering alone would let the loser apply next tick and
    # overwrite the winner, so the boss's rule is obeyed and quietly undone.
    m2.run(limit=6)
    check("§12", "an overridden rule does not apply at all", m2.holds(g2.rel(lit2, q2)) == MINUS)
    check("§12", "and the defeated rule never wrote", all(e.sign == MINUS for m_ in m2.chain.moments for e in m_.delta if e.proposition == g2.rel(lit2, q2)))


def a_rule_is_a_node() -> None:
    """§8: a rule is a fact relating *two* moments -- never a flat list of its
    patterns, which loses the signs and varies its arity with its size."""
    m = Machine()
    g = m.g
    p, q = g.rel(g.atom("f"), g.atom("a")), g.rel(g.atom("g"), g.atom("a"))
    hot = m.rules.rule(IMPLIES, [Member(PLUS, p)], [Member(PLUS, q)], "hot")
    cold = m.rules.rule(IMPLIES, [Member(PLUS, p)], [Member(MINUS, q)], "cold")
    check("§8", "two rules differing only in a sign are two nodes", hot.node != cold.node)
    check("§8", "a rule has exactly two members, whatever its size", len(g.members(hot.node)) == 2)
    big = m.rules.rule(IMPLIES, [Member(PLUS, p), Member(PLUS, q)], [Member(PLUS, p)], "big")
    check("§5", "so arity does not vary with how much it says", len(g.members(big.node)) == 2)
    check("§8", "the antecedent moment carries its signed members", len(g.members(g.member(hot.node, 0))) == 1)
    check(
        "R4",
        "and the sign is in the graph, so *which rules disturb this* is a query",
        g.members(g.member(g.member(cold.node, 1), 0))[1] == m.rules.SIGN[MINUS],
    )
    check("§8", "two rules that say the same thing are still two rules", m.rules.rule(IMPLIES, [Member(PLUS, p)], [Member(PLUS, q)], "twin").node != hot.node)


def connectives_differ() -> None:
    """§10: retract the antecedent and does the consequent go with it? The
    mechanical difference is where the entry lands."""
    m = Machine()
    g = m.g
    heat, water = g.rel(g.atom("heat"), g.atom("w")), g.rel(g.atom("water"), g.atom("w"))
    boiling = g.rel(g.atom("boiling"), g.atom("w"))
    m.rules.rule(CAUSES, [Member(PLUS, heat), Member(PLUS, water)], [Member(PLUS, boiling)], "boil")
    m.gate.write(m.focus, heat, PLUS)
    m.gate.write(m.focus, water, PLUS)
    before = m.focus.seat
    m.run(limit=5)
    check("§10", "`causes` lands in a later moment", m.focus.seat.depth > before.depth)
    check("§10", "and the effect is believed", m.holds(boiling) == PLUS)

    m2 = Machine()
    g2 = m2.g
    cloudy = g2.rel(g2.atom("cloudy"), g2.atom("mon"))
    rain = g2.rel(g2.atom("rain"), g2.atom("mon"))
    m2.rules.rule(IMPLIES, [Member(PLUS, cloudy)], [Member(PLUS, rain, "likely")], "R2")
    m2.gate.write(m2.focus, cloudy, PLUS)
    seat_before = m2.focus.seat
    m2.run(limit=5)
    check("§10", "`implies` lands in the same moment", m2.focus.seat is seat_before)
    check("§12", "and carries the rule's authored grade", m2.chain.resolve(rain, m2.focus.topic).grade == "likely")


def quiescence() -> None:
    m = Machine()
    g = m.g
    p, q = g.rel(g.atom("f"), g.atom("p")), g.rel(g.atom("f"), g.atom("q"))
    m.rules.rule(IMPLIES, [Member(PLUS, p)], [Member(PLUS, q)], "pq")
    m.gate.write(m.focus, p, PLUS)
    steps = m.run(limit=20)
    check("§15", "the loop stops rather than reapplying forever", len(steps) < 20)
    check("§15", "and says which silence it was", steps[-1].state == "quiescent")


# -- the demo: trusting a channel -------------------------------------------


def trusting_a_channel() -> None:
    """What arrives is that a channel said so. Turning that into a claim about
    the world is a rule -- one the agent can be asked about, and overridden."""
    m = Machine()
    g = m.g
    user = m.channels.open("user")
    raining = g.rel(g.atom("raining"), g.atom("here"))

    said = g.rel(m.SAYS, user, raining, m.rules.SIGN["+"])
    trust = m.rules.rule(
        IMPLIES, [Member(PLUS, said)], [Member(PLUS, raining, "likely")], "trust-user"
    )

    m.channels.deliver(user, raining)
    steps = m.run(limit=10)

    check("§13", "the arrival was stamped as something the channel said", m.holds(said) == PLUS)
    check("§13", "and the world claim is separate from the saying", said != raining)
    check("§13", "the trust rule concluded about the world", m.holds(raining) == PLUS)

    e = m.chain.resolve(raining, m.focus.topic, m.focus.seat)
    check("§12", "the conclusion is no stronger than the rule allowed", e.grade == "likely")
    check("§5", "the conclusion names what produced it", e.licence is not None)

    trail = m.chain.trail(e)
    check("§13", "the trail reaches the utterance", any(t.proposition == said for t in trail))
    check(
        "§13",
        "and the utterance names the channel it arrived through",
        any(t.source == user for t in trail),
    )
    check("R5", "why() answers with more than the claim itself", len(m.why(raining)) > 1)
    check("§13", "a derived entry's channel is the KB, not the rule", e.source == m.KB)
    check("§13", "and the rule is its licence, not its channel", e.licence != e.source)

    # §5: an entry is an act of claiming, so two claims are two nodes.
    m2 = Machine()
    g2 = m2.g
    p2 = g2.rel(g2.atom("tt"), g2.atom("anna"))
    m0 = m2.chain.root
    e1 = m2.chain.deposit(seat=m0, locus=m0, proposition=p2, sign=PLUS)
    e2 = m2.chain.deposit(seat=m0, locus=m0, proposition=p2, sign=MINUS)
    check("§5", "two claims about one proposition are two distinct entry nodes", e1.node != e2.node)
    check("§5", "so a fact about one does not land on the other", m2.chain.entry_by_node(e1.node).sign == PLUS)
    check("§16", "the machine counted its selections", m.selections == len([s for s in steps if s.state == "applied"]))


# -- the surface ------------------------------------------------------------


def _loads(src: str):
    from .text import load

    m = Machine()
    return m, load(m, src)


def _refuses(src: str) -> bool:
    from .text import ParseError

    try:
        _loads(src)
        return False
    except ParseError:
        return True


def surface() -> None:
    """One grammar for rules, facts and facts about rules -- because a rule is a
    relation instance like any other, which is R3 and R4 in the surface."""
    from .text import ParseError, Parser, tokenise

    m, kb = _loads("fact +on(a, b)\nfact -in(b, c)   # a comment\n")
    check("§3", "the surface writes a fact", m.holds(kb.term("on(a, b)")) == PLUS)
    check("§6", "and a signed one", m.holds(kb.term("in(b, c)")) == MINUS)
    check("§13", "a loaded fact is stamped as having come from the KB", m.chain.resolve(kb.term("on(a, b)"), m.focus.topic).source == m.KB)

    check("§4", "a fact may not contain a variable", _refuses("fact +on(?x, b)"))
    check(
        "§13",
        "a consequent naming a variable the antecedent never binds is refused",
        _refuses("rule <r> = implies( { +p(?x) }, { +q(?y) } )"),
    )
    check("§10", "a third connective is refused", _refuses("rule <r> = enables( { +p(a) }, { +q(a) } )"))
    check("§10", "a grade outside the ordinal set is refused", _refuses("rule <r> = implies( { +p(a) }, { +q(a) @0.7 } )"))
    check(
        "§8",
        "a locus member says slice one carries the one-locus case only",
        _refuses("rule <r> = implies( { +p(a) @ ?m }, { +q(a) } )"),
    )

    toks = tokenise("rule <TT-base> = implies( { +acts(?a) }, { +done(?a) } )")
    check("§3", "a hyphenated name is one token", any(t.text == "TT-base" for t in toks))

    m2, kb2 = _loads(
        "rule <hot> = implies( { +p(a) }, { +q(a) } )\n"
        "rule <cold> = implies( { +p(a) }, { -q(a) } )\n"
        "fact overrides(<cold>, <hot>)\n"
        "fact +p(a)\n"
    )
    # By name, not by position: the machine installs its bundled rules first
    # (§4), so any index into the rule list counts the bundle as well.
    cold = next(r for r in m2.rules.rules if r.name == "cold")
    check("R3", "a rule is a thing a fact can be about", kb2.term("<cold>") == cold.node)
    check("§14", "and `overrides` in the surface seeds the precedence table", len(m2.rules.overrides) == 1)
    m2.run(limit=5)
    check("§14", "so the overriding rule is the one that applied", m2.holds(kb2.term("q(a)")) == MINUS)


def the_bundle() -> None:
    """A convention that used to be an interpreter phase, now shipped as a rule.

    `says` was written by `_intake` and was therefore a name the engine knew --
    one line of Appendix C's census. What stays machinery is crossing the
    boundary, because a channel is anchored and a rule is generic; what an
    arrival *means* is a rule, and this checks that the rule is load-bearing
    rather than decorative.
    """
    m = Machine()
    g = m.g
    user = m.channels.open("user")
    raining = g.rel(g.atom("raining"), g.atom("here"))
    m.channels.deliver(user, raining)
    m.run(limit=6)

    said = g.rel(m.SAYS, user, raining, m.rules.SIGN[PLUS])
    e = m.chain.resolve(said, m.focus.topic, m.focus.seat)
    check("§5", "a report becomes a saying", e is not None)
    check("§5", "and a rule application licensed it", e is not None and e.licence is not None)

    trail = m.chain.trail(e)
    check(
        "§17",
        "the raw arrival is underneath it, sourced to the channel",
        any(g.relation_of(t.proposition) == m.ARRIVED and t.source == user for t in trail),
    )

    # Delete the rule and the conclusion goes with it. Without this the check
    # above passes whether or not the phase was ever really removed -- which is
    # the vacuity `ugm.agreement` ran into three times in one afternoon.
    m2 = Machine()
    m2.rules.rules = [r for r in m2.rules.rules if r.name != "intake"]
    u2 = m2.channels.open("user")
    r2 = m2.g.rel(m2.g.atom("raining"), m2.g.atom("here"))
    m2.channels.deliver(u2, r2)
    m2.run(limit=6)
    s2 = m2.g.rel(m2.SAYS, u2, r2, m2.rules.SIGN[PLUS])
    check(
        "§5",
        "and nothing else writes it -- delete the rule and there is no saying",
        m2.chain.resolve(s2, m2.focus.topic, m2.focus.seat) is None,
    )

    # The outbound half. Acting used to be a phase; now only the crossing is.
    m3 = Machine()
    g3 = m3.g
    heat = g3.rel(g3.atom("heat"), g3.atom("anna"), g3.atom("kettle"))
    m3.actuator("hands")
    m3.gate.write(m3.focus, g3.rel(m3.DOING, heat), PLUS)
    m3.run(limit=8)
    check("§15", "an intent crosses the boundary at the write", m3.emitted == [heat])
    check("§15", "a rule turns the crossing into *I acted*", m3.holds(g3.rel(m3.DID, heat)) == PLUS)
    check("§15", "and a rule asserts the act itself", m3.holds(heat) == PLUS)

    # §18's whole argument, made concrete: a strategy written as code cannot be
    # overridden by a statement in the knowledge base. `the agent asserts the
    # act` was such a strategy. As a rule, an agent that does not assume its acts
    # succeed is expressible -- and it still acts, and still knows it acted.
    m4 = Machine()
    g4 = m4.g
    m4.rules.rules = [r for r in m4.rules.rules if r.name != "assert-act"]
    h4 = g4.rel(g4.atom("heat"), g4.atom("anna"), g4.atom("kettle"))
    m4.gate.write(m4.focus, g4.rel(m4.DOING, h4), PLUS)
    m4.run(limit=8)
    check("§18", "drop that rule and the agent still acts", m4.emitted == [h4])
    check("§18", "and still knows it acted", m4.holds(g4.rel(m4.DID, h4)) == PLUS)
    check(
        "§18",
        "but no longer assumes the act succeeded -- a strategy defeated by data",
        m4.holds(h4) is None,
    )


def surprise_is_four_rows() -> None:
    """Every way an observation can disappoint an expectation.

    As a phase this was one comparison — *observed sign is not the expected one*
    — and three of its four cases were never tested. Written as rules the cases
    became four nodes, and a rule nothing can kill is a rule nothing is checking,
    so they are checked here. This is `adding a connective adds rows, not
    branches` (§5) turning into `and each row needs its own evidence`.
    """
    for expected, observed in (
        (PLUS, MINUS), (PLUS, UNSURE), (MINUS, PLUS), (MINUS, UNSURE),
    ):
        m = Machine()
        g = m.g
        p = g.rel(g.atom("boiling"), g.atom("kettle"))
        # An expectation, then an observation that disappoints it.
        m.gate.write(
            m.focus, g.rel(m.EXPECTS, p, m.rules.SIGN[expected]), PLUS, mention=True
        )
        m.gate.write(m.focus, p, observed)
        m.run(limit=8)
        check(
            "§18",
            f"expected {expected}, observed {observed} -- a deviation",
            m.holds(g.rel(m.DEVIATES, p)) == PLUS,
        )

    # And the case that must NOT be a deviation, or the rules would fire on
    # every expectation the world met.
    m = Machine()
    g = m.g
    p = g.rel(g.atom("boiling"), g.atom("kettle"))
    m.gate.write(m.focus, g.rel(m.EXPECTS, p, m.rules.SIGN[PLUS]), PLUS, mention=True)
    m.gate.write(m.focus, p, PLUS)
    m.run(limit=8)
    check(
        "§18",
        "an expectation the world met is not a deviation",
        m.holds(g.rel(m.DEVIATES, p)) is None,
    )


def worked_examples() -> None:
    """§8's rules, as printed in the design, actually run."""
    import os

    from .text import load_file

    path = os.path.join(os.path.dirname(__file__), "rules", "worked.ugm")
    m = Machine()
    kb = load_file(m, path)
    authored = [r for r in m.rules.rules if r not in m.bundle]
    check("§8", "the document's worked rules parse", len(authored) == 3)

    steps = m.run(limit=30)
    check("§15", "and run to quiescence", steps[-1].state == "quiescent")

    check("§8", "<R1> concluded", m.holds(kb.term("boiling(kettle)")) == PLUS)
    check("§6", "including its negative member", m.holds(kb.term("liquid(kettle)")) == MINUS)
    check("§8", "<R2> concluded", m.holds(kb.term("rain(monday, afternoon)")) == PLUS)
    check(
        "§12",
        "<R2>'s conclusion carries the grade it authored",
        m.chain.resolve(kb.term("rain(monday, afternoon)"), m.focus.topic).grade == "likely",
    )

    # The trust rule's consequent is a bare variable: whatever the channel says.
    raining = kb.term("raining(here)")
    check("§13", "a rule whose consequent is a variable believes what a channel said", m.holds(raining) == PLUS)
    e = m.chain.resolve(raining, m.focus.topic)
    check("§12", "and it is no stronger than the rule allowed", e.grade == "likely")
    check("§13", "the channel in the rule is the channel delivered on", any(t.source == kb.term("user") for t in m.chain.trail(e)))
    check("R5", "the trail reaches the utterance", len(m.why(raining)) > 1)


def rules_as_data() -> None:
    """§14: a rule is a node, so a rule can be matched by a rule -- once what a
    rule IS has been deposited as entries."""
    from .text import load

    src = chr(10).join([
        "rule <a> = implies( { +p(x) }, { +q(x) } )",
        "rule <b> = implies( { +q(x) }, { +r(x) } )",
        "rule <lift> = implies( { +likely(?u), +ant(?rl, ?u, plus), +con(?rl, ?v, plus) },",
        "                      { +likely(?v) } )",
        "fact +likely(p(x))",
        "",
    ])
    m = Machine()
    kb = load(m, src)
    check("§14", "before reification a rule is a node nobody asserted", m.holds(kb.term("rule(<a>)")) is None)
    m.reify_all()
    check("§14", "reified, a rule is an ordinary fact", m.holds(kb.term("rule(<a>)")) == PLUS)
    check("§14", "and its connective is askable", m.holds(kb.term("conn(<a>, implies)")) == PLUS)
    check("§13", "its patterns are MENTIONED, not used", m.holds(kb.term("ant(<a>, p(x), plus)")) == PLUS)

    m.run(limit=30)
    check("§14", "one generic rule lifts modality across the bare pipeline", m.holds(kb.term("likely(r(x))")) == PLUS)
    check("§12", "and the guard holds: the bare conclusion was never asserted", m.holds(kb.term("r(x)")) is None)

    ok = False
    try:
        m.gate.write(m.focus, m.g.rel(m.g.atom("f"), m.g.var("?z")), PLUS)
    except ValueError:
        ok = True
    check("§13", "mention is a gate parameter, not a hole in the gate", ok)


def supposing() -> None:
    """§13's frames, used for modality: enter the guard, reason bare, wrap on
    the way out. The alternative to a lifting rule, and it does what lifting
    cannot -- work over rules that carry variables."""
    from .text import load

    src = chr(10).join([
        "rule <sympt> = implies( { +reading(?p, low) },        { +symptom(?p, restricted) } )",
        "rule <cause> = implies( { +symptom(?p, restricted) }, { +diag(?p, blocked) } )",
        "rule <act>   = implies( { +diag(?p, blocked) },       { +action(replace, ?p) } )",
        "",
    ])
    m = Machine()
    kb = load(m, src)
    f = m.suppose(kb.term("reading(pump7, low)"))
    check("§13", "supposing seats the frame in a successor", f.seat.predecessor is f.parent.seat)
    check("§13", "and the frame is a child of the caller", f.parent is not None)

    out = m.discharge(f, kb.term("likely"))
    check("§13", "conclusions come out wrapped", len(out) == 3)
    check(
        "§12",
        "supposing lifts modality over rules with VARIABLES, which lifting cannot",
        m.holds(kb.term("likely(symptom(pump7, restricted))")) == PLUS,
    )
    check("§12", "across the whole chain", m.holds(kb.term("likely(action(replace, pump7))")) == PLUS)
    check(
        "§17",
        "containment: nothing concluded inside is readable as current belief",
        m.holds(kb.term("symptom(pump7, restricted)")) is None
        and m.holds(kb.term("action(replace, pump7)")) is None,
    )
    check("§13", "the caller is back in its own frame", m.focus.seat is f.parent.seat)
    check("§13", "and the frame reports how it ended", f.state == "discharged")

    # Nesting needs no mechanism: it is a path in the frame forest.
    m2 = Machine()
    kb2 = load(m2, "rule <r1> = implies( { +a(?x) }, { +b(?x) } )")
    outer = m2.suppose(kb2.term("seen(x)"))
    inner = m2.suppose(kb2.term("a(x)"))
    m2.discharge(inner, kb2.term("possible"))
    nested = m2.discharge(outer, kb2.term("likely"))
    check(
        "§4",
        "nested suppositions wrap in order -- likely(possible(b(x)))",
        any(m2.g.show(e.proposition) == "likely(possible(b(x)))" for e in nested),
    )


def rule_driven_supposition() -> None:
    """The whole of it, with no Python driving: a rule PROPOSES crossing the
    guard, the machinery enacts it, and the conclusions come back wrapped."""
    from .text import load

    src = chr(10).join([
        "rule <sympt> = implies( { +reading(?p, low) },        { +symptom(?p, restricted) } )",
        "rule <cause> = implies( { +symptom(?p, restricted) }, { +diag(?p, blocked) } )",
        "rule <act>   = implies( { +diag(?p, blocked) },       { +action(replace, ?p) } )",
        "rule <cross> = implies( { +likely(?p) },              { +suppose(?p, likely) } )",
        "rule <hedge> = implies( { +likely(diag(?p, blocked)) }, { +goal(corroborate(?p)) } )",
        "fact +likely(reading(pump7, low))",
        "",
    ])
    m = Machine()
    kb = load(m, src)
    steps = m.run(limit=200)

    check("§14", "the loop settles rather than exhausting its budget", steps[-1].state == "quiescent")
    check("§9", "and no bound was hit silently", m.exhausted == 0)
    check("§13", "a rule proposed the supposition", any(s.state == "supposed" for s in steps))
    check("§12", "modality crossed the whole pipeline", m.holds(kb.term("likely(diag(pump7, blocked))")) == PLUS)
    check("§12", "and the hedge fired on the wrapped conclusion", m.holds(kb.term("goal(corroborate(pump7))")) == PLUS)
    check(
        "§17",
        "the guard held: nothing acted on the unwrapped conclusion",
        m.holds(kb.term("action(replace, pump7)")) is None,
    )
    check(
        "§13",
        "a suppose request is bookkeeping and never carries out of a frame",
        m.holds(kb.term("likely(suppose(reading(pump7, low), likely))")) is None,
    )


def backward_reading() -> None:
    """R1: one statement, two readings. R2: the reading is recoverable, because
    a subgoal is licensed `wanted` and a conclusion `applied`."""
    from .text import load

    src = chr(10).join([
        "rule <boil> = implies( { +heat(?a, ?w), +water(?w) }, { +boiling(?w) } )",
        "rule <pour> = implies( { +tap(?t), +under(?w, ?t) },  { +water(?w) } )",
        "fact +tap(sink)",
        "fact +under(kettle, sink)",
        "fact +goal(boiling(kettle))",
        "",
    ])
    m = Machine()
    kb = load(m, src)
    m.run(limit=60)

    def props(rel):
        return [m.g.show(e.proposition) for mm in m.chain.moments for e in mm.delta
                if m.g.relation_of(e.proposition) is rel and e.sign == PLUS]

    goals, blocked, achieved = props(m.GOAL), props(m.BLOCKED), props(m.ACHIEVED)

    check("R1", "the same rule read backwards proposes subgoals", "goal(water(kettle))" in goals)
    check("R1", "and recurses through a second rule", "goal(under(kettle, ?t))" in goals)
    check(
        "R2",
        "a subgoal is licensed `wanted`, never `applied`",
        all(
            m.g.relation_of(e.licence) is m.WANTED
            for mm in m.chain.moments for e in mm.delta
            if m.g.relation_of(e.proposition) is m.GOAL and e.licence is not None
            and m.g.relation_of(e.licence) is not None
            and m.g.show(e.proposition) != "goal(boiling(kettle))"
        ),
    )
    check(
        "§15",
        "a goal nothing concludes is BLOCKED -- an action, not a failure",
        "blocked(heat(?a, kettle))" in blocked,
    )
    check(
        "§14",
        "*is this goal already met* is a match, not a lookup",
        "achieved(tap(?t))" in achieved and "achieved(under(kettle, ?t))" in achieved,
    )
    check("§9", "expansion is budgeted and reported", m.exhausted == 0 and m.expansions == 2)

    # §14's printed backward reader cannot work: `con(?r, ?f, plus)` stores the
    # rule's generic PATTERN, and a goal is ground, so one variable cannot bind
    # to both. Deciding they correspond is `match`, which no rule can call.
    m2 = Machine()
    kb2 = load(m2, chr(10).join([
        "rule <boil2> = implies( { +heat(?a, ?w) }, { +boiling(?w) } )",
        "rule <back>  = implies( { +goal(?f), +con(?r, ?f, plus) }, { +candidate(?r, ?f) } )",
        "fact +goal(boiling(kettle))",
        "",
    ]))
    m2.reify_all()
    m2.run(limit=20)
    check(
        "§14",
        "the document's backward reader as rules does NOT fire -- it needs match",
        m2.holds(kb2.term("candidate(<boil2>, boiling(kettle))")) is None,
    )


def plan_bindings() -> None:
    """A conjunctive goal must be satisfied on bindings that AGREE. Checked
    independently, `tap(sink)` and `under(kettle, drain)` both look achieved and
    the plan is wrong -- silently, which is the worst kind."""
    from .text import load

    def world(facts):
        m = Machine()
        kb = load(m, chr(10).join([
            "rule <boil> = implies( { +heat(?a, ?w), +water(?w) }, { +boiling(?w) } )",
            "rule <pour> = implies( { +tap(?t), +under(?w, ?t) },  { +water(?w) } )",
        ] + facts + ["fact +goal(boiling(kettle))", ""]))
        m.run(limit=60)
        return m, kb

    def props(m, rel):
        return [m.g.show(e.proposition) for mm in m.chain.moments for e in mm.delta
                if m.g.relation_of(e.proposition) is rel and e.sign == PLUS]

    m, kb = world(["fact +tap(sink)", "fact +under(kettle, sink)"])
    check("§14", "bindings agree, so both siblings are achieved",
          "achieved(tap(?t))" in props(m, m.ACHIEVED) and "achieved(under(kettle, ?t))" in props(m, m.ACHIEVED))
    check("R7", "and the binding is a fact on the graph, not an interpreter variable",
          any("?t, sink" in x for x in props(m, m.BINDS)))

    m2, kb2 = world(["fact +tap(sink)", "fact +under(kettle, drain)"])
    check("§14", "bindings disagree, so the sibling is blocked, not achieved",
          "blocked(under(kettle, ?t))" in props(m2, m2.BLOCKED))
    check("§14", "and the false achievement does not appear",
          "achieved(under(kettle, ?t))" not in props(m2, m2.ACHIEVED))


def the_loop_closes() -> None:
    """Plan, act, be wrong, notice. §11 acting, §16 surprise."""
    from .text import load

    src = chr(10).join([
        "rule <boil>   = causes(  { +heat(?a, ?w), +water(?w) },   { +boiling(?w) } )",
        "rule <do>     = implies( { +blocked(heat(?a, ?w)) },      { +doing(heat(anna, ?w)) } )",
        "rule <trustT> = implies( { +says(gauge, ?p, plus) },      { +?p } )",
        "rule <trustF> = implies( { +says(gauge, ?p, minus) },     { -?p } )",
        "rule <why>    = implies( { +deviates(?p) },               { +goal(explain(?p)) } )",
        "fact overrides(<why>, <boil>)",
        "fact +water(kettle)",
        "fact +goal(boiling(kettle))",
        "",
    ])
    m = Machine()
    kb = load(m, src)
    check("R3", "a fact may NAME a rule, though a rule node contains variables", len(m.rules.overrides) == 1)

    gauge = kb.term("gauge")
    m.channels.use(gauge)
    steps = m.run(limit=60)

    check("§11", "planning reached an act and emitted it", [m.g.show(x) for x in m.emitted] == ["heat(anna, kettle)"])
    check("§11", "acting makes the event-fact true", m.holds(kb.term("heat(anna, kettle)")) == PLUS)
    check("§16", "and forward application deposits what it predicts",
          m.holds(kb.term("expects(boiling(kettle), plus)")) == PLUS)
    check("§16", "without which there would be nothing to be surprised against",
          m.holds(kb.term("boiling(kettle)")) == PLUS)

    m.channels.deliver(gauge, kb.term("boiling(kettle)"), sign="-")
    after = m.run(limit=60)

    check("§13", "a channel reports a SIGNED content, and the saying itself is positive",
          m.holds(kb.term("says(gauge, boiling(kettle), minus)")) == PLUS)
    check("§16", "surprise is a match: expected and observed disagree",
          m.holds(kb.term("deviates(boiling(kettle))")) == PLUS)
    check("§16", "and the response is an ordinary rule, so it can be overridden",
          m.holds(kb.term("goal(explain(boiling(kettle)))")) == PLUS)
    check("§16", "precedence stops the contradicted rule re-asserting forever",
          after[-1].state == "quiescent")
    check("R5", "the deviation carries its whole trail back to the channel",
          len(m.why(kb.term("deviates(boiling(kettle))"))) >= 4)

    # A consequent that is a bare variable is exact forwards and vacuous
    # backwards: it proposes itself for every goal, without end.
    m2 = Machine()
    kb2 = load(m2, chr(10).join([
        "rule <trust> = implies( { +says(x, ?p, plus) }, { +?p } )",
        "fact +goal(anything(here))",
        "",
    ]))
    m2.run(limit=30)
    check("R1", "the backward reader declines a consequent it cannot use",
          m2.holds(kb2.term("blocked(anything(here))")) == PLUS)


def main() -> int:
    import sys

    if hasattr(sys.stdout, "reconfigure"):  # section signs, on a cp1252 console
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    substrate()
    chain_reads()
    two_indices()
    gate()
    grades()
    matching()
    arbitration_is_total()
    a_rule_is_a_node()
    rules_as_data()
    supposing()
    rule_driven_supposition()
    backward_reading()
    plan_bindings()
    the_loop_closes()
    connectives_differ()
    quiescence()
    trusting_a_channel()
    the_bundle()
    surprise_is_four_rows()
    surface()
    worked_examples()

    failed = 0
    group = None
    for grp, name, ok in _results:
        if grp != group:
            print(f"\n{grp}")
            group = grp
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
        if not ok:
            failed += 1
    print(f"\n{len(_results)} checks, {failed} failing")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
