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

    # The inbound crossing does not wait for a tick. Intake used to be the first
    # line of the loop -- drain a queue, stamp what arrived -- and nothing
    # required that. An arrival is an external event, and an external event is
    # not something the agent does, so it has no place in the agent's step.
    m5 = Machine()
    g5 = m5.g
    chan = m5.channels.open("gauge")
    hot = g5.rel(g5.atom("boiling"), g5.atom("kettle"))
    report = g5.rel(m5.ARRIVED, chan, hot, m5.rules.SIGN[PLUS])
    check("§17", "nothing has arrived yet", m5.holds(report) is None)
    m5.channels.deliver(chan, hot)
    check("§17", "delivery writes when the world speaks, not at the next tick", m5.holds(report) == PLUS)
    check(
        "§5",
        "but what it MEANS still waits for a rule to be selected",
        m5.holds(g5.rel(m5.SAYS, chan, hot, m5.rules.SIGN[PLUS])) is None,
    )
    step = m5.tick()
    check("§19", "and the tick can still name which silence it was", step.arrivals == 1)
    check(
        "§5",
        "one selection later, the report has a meaning",
        m5.holds(g5.rel(m5.SAYS, chan, hot, m5.rules.SIGN[PLUS])) == PLUS,
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


def denial_nests() -> None:
    """§9's open question, settled by running it.

    A sign is a member of an entry, so it cannot sit inside another term — and
    §16 nests terms by construction. Concluding `-b` under a `likely` supposition
    means *likely, not-b*; with only a sign to carry it, what crossed out was
    `-likely(b)`, which says *not likely that b*. A different claim, and the
    wrong one. That was live, not hypothetical.

    The answer is not *replace the sign with a wrapper*. It is the same pairing
    §16 reaches for modality: the member is what the machinery computes with, the
    term is what survives nesting.
    """
    from .text import load

    m = Machine()
    kb = load(m, "rule <r> = implies( { +a(x) }, { -b(x) } )")
    f = m.suppose(kb.term("a(x)"), wrap=kb.term("likely"))
    m.run(limit=20)

    likely = kb.term("likely")
    b = kb.term("b(x)")
    check(
        "§9",
        "a denial concluded under a supposition crosses out INSIDE the wrapper",
        [(e.sign, m.g.show(e.proposition)) for e in f.carried]
        == [(PLUS, "likely(not(b(x)))")],
    )
    check(
        "§16",
        "so *probably not-b* and *not probably-b* stay different claims",
        m.holds(m.g.rel(likely, m.g.rel(m.NOT, b))) == PLUS
        and m.holds(m.g.rel(likely, b)) is None,
    )

    # And the two forms are one claim, so a corpus need not know which it is
    # looking at. Crossing back into a supposition unwraps to the term; the rules
    # inside are written against the sign.
    m2 = Machine()
    kb2 = load(m2, "rule <s> = implies( { -b(x) }, { +noticed(x) } )")
    m2.gate.write(m2.focus, m2.g.rel(m2.NOT, kb2.term("b(x)")), PLUS)
    m2.run(limit=10)
    check("§9", "a term denial reads as a sign denial", m2.holds(kb2.term("b(x)")) == MINUS)
    check(
        "§9",
        "so a rule written against `-b` sees it",
        m2.holds(kb2.term("noticed(x)")) == PLUS,
    )
    check(
        "§9",
        "and the translation runs one way, so nothing builds not(not(p))",
        all(s.state != "applied" for s in m2.run(limit=20)),
    )


def mention_propagates() -> None:
    """A rule's consequent can MENTION, and §14 said it could not.

    `+con(?r, ?pat, +)` binds `?pat` to a stored pattern, so anything concluded
    about `?pat` is a ground claim that happens to contain variables. §14 settles
    use against mention by *who is writing* -- machinery mentions, a rule uses --
    and that turned out to be too strong.

    What tells them apart is inheritance: mention propagates through bindings,
    which is checkable because the entries match consumed are already recorded
    for the trail.

    Until this, such a rule was not refused -- it was silently filtered by
    quiescence, because a conclusion still containing variables looked exactly
    like a rule with nothing left to do.
    """
    from .text import load

    m = Machine()
    load(m, "rule <boil> = implies( { +heat(?w) }, { +boiling(?w) } )")
    m.reify_all()
    g = m.g
    concludes = g.atom("concludes")
    r, pat = g.var("?r"), g.var("?pat")
    m.rules.rule(
        IMPLIES,
        [Member(PLUS, g.rel(m.CON, r, pat, m.rules.SIGN[PLUS]))],
        [Member(PLUS, g.rel(concludes, r, pat))],
        "what-does-it-conclude",
    )
    m.run(limit=30)

    derived = [
        e
        for mo in m.chain.moments
        for e in mo.delta
        if g.relation_of(e.proposition) is concludes
    ]
    check("R3", "a rule can derive facts about rules", len(derived) >= 1)
    check(
        "§14",
        "and the derived claim is recorded as a mention, not as a generic claim",
        all(e.mention for e in derived),
    )
    check(
        "§14",
        "including about the bundle -- the machinery's own rules are askable",
        any("did(?what)" in g.show(e.proposition) for e in derived),
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
    # Reification used to be something a caller remembered to do. It is now a
    # subscription on rule authoring, because backward reading is rules and it
    # enumerates `+rule(?r)` -- a rule loaded after a `reify_all()` would have
    # been invisible to the reader with nothing reporting so.
    check("§14", "a rule is data the moment it is authored", m.holds(kb.term("rule(<a>)")) == PLUS)
    m.reify_all()
    check("§14", "and reifying again is idempotent", m.holds(kb.term("rule(<a>)")) == PLUS)
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
    f = m.suppose(kb.term("reading(pump7, low)"), wrap=kb.term("likely"))
    check("§13", "supposing seats the frame in a successor", f.seat.predecessor is f.parent.seat)
    check("§13", "and the frame is a child of the caller", f.parent is not None)

    # No nested run: reasoning inside a supposition is ordinary ticks of the
    # ordinary loop, and the frame is left when the loop runs out of work there.
    m.run(limit=30)
    check("§13", "conclusions come out wrapped", len(f.carried) == 3)
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
    outer = m2.suppose(kb2.term("seen(x)"), wrap=kb2.term("likely"))
    inner = m2.suppose(kb2.term("a(x)"), wrap=kb2.term("possible"))
    m2.run(limit=30)
    check(
        "§4",
        "nested suppositions wrap in order -- likely(possible(b(x)))",
        any(m2.g.show(e.proposition) == "likely(possible(b(x)))" for e in outer.carried),
    )
    check(
        "§18",
        "each frame was left because the loop ran out of work there, not by a return",
        inner.state == "discharged" and outer.state == "discharged",
    )

    # Nothing owns the loop (§18). Supposing used to call `run()` inside itself,
    # so the caller regained control only once the whole hypothesis was
    # exhausted. Now every step inside a supposition is an ordinary top-level
    # tick: the caller can stop between any two of them, and the reasoning done
    # under the hypothesis appears in the caller's own trace.
    m3 = Machine()
    kb3 = load(m3, chr(10).join([
        "rule <a> = implies( { +p(?x) }, { +q(?x) } )",
        "rule <b> = implies( { +q(?x) }, { +r(?x) } )",
        "",
    ]))
    f3 = m3.suppose(kb3.term("p(x)"), wrap=kb3.term("likely"))
    one = m3.tick()
    check("§18", "one tick inside a supposition applies exactly one rule", one.state == "applied")
    check("§18", "and the caller has control back between ticks", m3.focus is f3)
    rest = m3.run(limit=20)
    check(
        "R7",
        "the reasoning done under a hypothesis is in the caller's own trace",
        sum(1 for s in rest if s.state == "applied") >= 1,
    )

    # The world does not stop talking while the agent hypothesises, and what it
    # says belongs to the agent rather than to the hypothesis. Delivering into
    # the register turned the channel record -- which §17 calls unforgeable --
    # into `likely(says(...))`: the world's own testimony, hedged, and the plain
    # record unreadable.
    m4 = Machine()
    kb4 = load(m4, "rule <a> = implies( { +p(x) }, { +q(x) } )")
    user = m4.channels.open("user")
    rain = m4.g.rel(m4.g.atom("raining"), m4.g.atom("here"))
    m4.suppose(kb4.term("p(x)"), wrap=kb4.term("likely"))
    m4.channels.deliver(user, rain)
    m4.run(limit=20)
    said = m4.g.rel(m4.SAYS, user, rain, m4.rules.SIGN[PLUS])
    check("§17", "a report arriving mid-supposition lands at the agent's own seat", m4.holds(said) == PLUS)
    check(
        "§17",
        "and is not hedged by a hypothesis it had nothing to do with",
        m4.holds(m4.g.rel(kb4.term("likely"), said)) is None,
    )
    check(
        "§16",
        "while the supposition itself still concludes, on its own branch",
        m4.holds(m4.g.rel(kb4.term("likely"), kb4.term("q(x)"))) == PLUS,
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
    m.run(limit=400)

    def props(rel):
        return [m.g.show(e.proposition) for mm in m.chain.moments for e in mm.delta
                if m.g.relation_of(e.proposition) is rel and e.sign == PLUS]

    goals, blocked, achieved = props(m.GOAL), props(m.BLOCKED), props(m.ACHIEVED)

    check("R1", "the same rule read backwards proposes subgoals", "goal(water(kettle))" in goals)
    check("R1", "and recurses through a second rule", "goal(under(kettle, ?t))" in goals)
    # R2 -- the reading stays recoverable -- but it moved from the licence to the
    # trail when the phase went, and that is worth stating rather than noticing.
    # The phase wrote a subgoal itself and stamped it `wanted`. Now `<expand>`
    # writes it, so its licence is `applied(<expand>)` like any rule's. What
    # carries the reading is one hop further back: `<expand>` consumed a `need`
    # entry, and `_fit` licences everything it answers `wanted(<R>, goal)`. So
    # the guarantee is the ordinary trail rather than a special stamp, which is
    # §17's own argument -- and it is now checked by walking it.
    subgoals = [
        e for mm in m.chain.moments for e in mm.delta
        if m.g.relation_of(e.proposition) is m.GOAL
        and m.g.show(e.proposition) != "goal(boiling(kettle))"
    ]
    check(
        "R2",
        "a subgoal's trail reaches an entry licensed `wanted`, never `applied` alone",
        bool(subgoals) and all(
            any(m.g.relation_of(s.licence) is m.WANTED for s in m.chain.trail(e) if s.licence)
            for e in subgoals
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
    # The phase carried its own expansion counter because it ran outside
    # arbitration and nothing else could stop it. Backward reading is rules now,
    # so the budget is the loop's and termination is quiescence's.
    plans = {m.g.show(e.proposition) for mm in m.chain.moments for e in mm.delta
             if m.g.relation_of(e.proposition) is m.EXPANDS and e.sign == PLUS}
    check("§9", "two rules were read backwards, and no bound was hit silently",
          m.exhausted == 0 and len(plans) == 2)

    # The count that the whole arc was for. `tick` selects a rule and applies it;
    # everything a phase used to decide is now a rule or a request.
    check("§18", "no phase remains in the loop", not hasattr(m, "_expand_goal"))
    check(
        "§18",
        "and backward reading is data -- five rules a corpus can override",
        all(any(r.name == n for r in m.bundle)
            for n in ("ask-fit", "plan", "expand", "ask-check", "give-up")),
    )

    # What the phase cost, and the reason retiring it was a behavioural change
    # rather than a refactor: it ran ahead of recall and returned early, so while
    # any goal was unexpanded no ordinary rule could apply. A goal the corpus can
    # satisfy forwards read as blocked.
    # And what it did NOT fix. `<ask-check>` asks once, when the subgoal appears;
    # `water(kettle)` is derived forwards a few ticks later and nothing asks
    # again, because a request is a fact and quiescence refuses to re-conclude
    # one. The phase had the same blind spot for a different reason and could not
    # be fixed from a corpus; this one can. §21 carries the re-ask.
    check(
        "§21",
        "a request can only be made once, so a goal satisfied later is not re-checked",
        m.holds(kb.term("water(kettle)")) == PLUS
        and "achieved(water(kettle))" not in achieved,
    )

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
        m.run(limit=400)
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
    steps = m.run(limit=400)

    check("§11", "planning reached an act and emitted it", [m.g.show(x) for x in m.emitted] == ["heat(anna, kettle)"])
    check("§11", "acting makes the event-fact true", m.holds(kb.term("heat(anna, kettle)")) == PLUS)
    check("§16", "and forward application deposits what it predicts",
          m.holds(kb.term("expects(boiling(kettle), plus)")) == PLUS)
    check("§16", "without which there would be nothing to be surprised against",
          m.holds(kb.term("boiling(kettle)")) == PLUS)

    m.channels.deliver(gauge, kb.term("boiling(kettle)"), sign="-")
    after = m.run(limit=400)

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


def callbacks_on_a_hypothesis() -> None:
    """A pointer to a rule, hung on a hypothesis, picked up when it returns.

    The mechanism is three ordinary facts and one bundled rule. What makes it
    worth having is what it is NOT: `<cb>` is never called. `<resuming>` reads
    the pointer and says only *this rule's turn has come*; the machinery then
    proposes it, and it applies -- or is defeated, or does not match -- like
    anything else. A continuation, without a call.

    The worked case is reductio: what a hypothesis concluded can only be judged
    from outside it, after it is over, which is exactly what no rule inside the
    frame and no generic rule outside it can time for itself.
    """
    from .text import load

    src = chr(10).join([
        # The callback. It names no hypothesis: the pointer supplies that.
        "rule <cb>     = implies( { +left(?f, ?a), +hyp(?q), -?q }, { -?a } )",
        "fact dormant(<cb>)",
        # Attaching it is a rule's job, not the loader's -- a hypothesis is
        # raised in the middle of reasoning, so its callback has to be too.
        "rule <start>  = implies( { +testing(?h) },",
        "                        { +resume(?h, <cb>), +suppose(?h, hyp) } )",
        "rule <derive> = implies( { +h(?x) }, { +q(?x) } )",
        "fact -q(a)",
        "fact +testing(h(a))",
        "",
    ])
    m = Machine()
    kb = load(m, src)
    steps = m.run(limit=80)

    check("§13", "a rule attached a rule to a hypothesis", m.holds(kb.term("resume(h(a), <cb>)")) == PLUS)
    check("§13", "leaving a hypothesis is recorded as an occasion", any(s.state == "supposed" for s in steps))
    check(
        "§15",
        "the pointer woke a dormant rule -- recall, not invocation",
        m.holds(m.g.rel(m.DUE, kb.rules_by_name["cb"].node)) == PLUS,
    )
    check(
        "§13",
        "and the callback drew reductio: the hypothesis contradicted a belief, so it is false",
        m.holds(kb.term("h(a)")) == MINUS,
    )
    check(
        "§17",
        "what the hypothesis concluded stayed inside it",
        m.holds(kb.term("q(a)")) == MINUS and m.holds(kb.term("hyp(q(a))")) == PLUS,
    )
    check("§14", "and the loop settled", steps[-1].state == "quiescent" and m.exhausted == 0)

    # The pointer is load-bearing, not decoration: without it the same rule is
    # never proposed, and the same reasoning stops one step short.
    m2 = Machine()
    kb2 = load(m2, src.replace("+resume(?h, <cb>), ", ""))
    m2.run(limit=80)
    check(
        "§15",
        "delete the pointer and the callback never runs -- dormancy is what makes it a pointer",
        m2.holds(kb2.term("h(a)")) is None,
    )


def recall_is_narrowable() -> None:
    """§19's first slice: recall stops proposing everything, and what narrows it
    is a table of ordinary facts.

    `prefer(<R>, k)` says *when k is in play, bring R to mind*. Authored here;
    §19 says it is learned from the trail, and the trail is already deposited for
    R5, so nothing new has to be measured for that to happen.

    The key is not the register. Attention is the register (§4's one privileged
    pointer, `Machine.focus` -- seat and topic), but a seat is a fresh moment
    every tick, so a table keyed on it would never see the same key twice. What
    recurs is what the situation is about, so the key is a relation in play.
    """
    from .text import load

    chain = chr(10).join([
        "rule <a> = implies( { +p(?x) }, { +q(?x) } )",
        "rule <b> = implies( { +q(?x) }, { +r(?x) } )",
        "rule <c> = implies( { +r(?x) }, { +s(?x) } )",
        "rule <d> = implies( { +u(?x) }, { +v(?x) } )",
        "rule <e> = implies( { +m(?x) }, { +n(?x) } )",
        "fact +p(a)",
        "",
    ])
    table = chr(10).join([
        "fact prefer(<a>, p, 5)",
        "fact prefer(<b>, q, 5)",
        "fact prefer(<c>, r, 5)",
        "",
    ])

    def run(src, budget):
        m = Machine()
        kb = load(m, src)
        m.recall_budget = budget
        steps = m.run(limit=2000)
        return m, kb, steps

    m0, kb0, _ = run(chain, None)
    check("§19", "the default is still exhaustive -- a fresh agent has learned nothing",
          m0.holds(kb0.term("s(a)")) == PLUS and m0.widenings == 0)

    m1, kb1, _ = run(chain + table, 3)
    check("§19", "a narrowed recall reaches the same conclusion",
          m1.holds(kb1.term("s(a)")) == PLUS)
    check("§19", "and the table steered it: the rules it needed came to mind",
          m1.widenings == 1)

    m2, kb2, _ = run(chain, 3)
    check(
        "§15",
        "without a table it still gets there, by recalling harder -- *nothing came "
        "to mind* is not *nothing is left to do*",
        m2.holds(kb2.term("s(a)")) == PLUS and m2.widenings > m1.widenings,
    )

    # A ranking that ended in a set would make two runs of one corpus differ with
    # nothing recording why. This project has hit that bug; the tie-break is
    # authored order, the same one arbitration uses.
    a, _, sa = run(chain + table, 3)
    b, _, sb = run(chain + table, 3)
    check("§14", "and the same corpus recalls the same rules in the same order twice",
          [s.state for s in sa] == [s.state for s in sb] and a.widenings == b.widenings)

    # The soundness condition, and it only appeared once the phase had gone.
    # `<give-up>` asks its verdict at `quiet`, and `blocked` claims that NO rule
    # fits -- an aggregate over a finished search. A shortlist that ran dry has
    # finished a shortlist.
    goal = chr(10).join([
        "rule <boil> = implies( { +heat(?a, ?w), +water(?w) }, { +boiling(?w) } )",
        "rule <pour> = implies( { +tap(?t), +under(?w, ?t) },  { +water(?w) } )",
        "fact +tap(sink)",
        "fact +under(kettle, sink)",
        "fact +goal(boiling(kettle))",
        "",
    ])
    m3, kb3, _ = run(goal, 3)
    check(
        "§19",
        "a narrowed recall does not invent a verdict: nothing reads blocked that is not",
        m3.holds(kb3.term("blocked(water(kettle))")) is None
        and m3.holds(kb3.term("pursued(water(kettle))")) == PLUS,
    )

    # Could that have failed? Take the widening away and the same run gives up on
    # a goal it could reach -- which is the whole reason the line is there.
    m4 = Machine()
    kb4 = load(m4, goal)
    m4.recall_budget = 3
    m4._widen = lambda: False  # type: ignore[assignment]
    m4.run(limit=200)
    check(
        "§19",
        "and without widening it gives up on a reachable goal -- the check can fail",
        m4.holds(kb4.term("pursued(water(kettle))")) is None,
    )


def the_better_move_wins() -> None:
    """Given several applicable rules, choose the best one -- and *best* has to
    mean something the agent can point at.

    Before this, the tie among applicable, undefeated rules was broken by **the
    order they happened to be written in**. That is an accident of authoring
    deciding which move an agent makes, including the moves it cannot take back.

    What it is replaced by was already being computed and thrown away.
    `fits(<R>, w)` is `_fit`'s answer to *could this rule produce what you want*,
    so `<relevant>` turns it into a preference in one line -- and means-ends
    analysis is a bundled rule rather than a policy in the loop.

    Two limits, both found by breaking something:

    **Preference orders; it must not exclude.** Used to filter recall it starved
    `{+blocked(heat(?a, ?w))} => {+doing(heat(anna, ?w))}` -- the most useful rule
    in that corpus, which does not fit the goal at all. Relevance to a goal is
    silent about everything it is not about.

    **The apparatus is not a competitor.** Let loose over everything, preference
    outranked the rules that notice a surprise, so the agent pursued a goal while
    a channel was saying the world had moved. `standing` rules keep their
    authored place.
    """
    from .text import load

    src = chr(10).join([
        # Authored first, so authored order alone would pick it -- and it does
        # nothing for the goal.
        "rule <wander> = implies( { +at(?x) }, { +wandered(?x) } )",
        "rule <toward> = implies( { +at(?x) }, { +nearer(?x) } )",
        "fact +at(a)",
        "fact +goal(nearer(a))",
        "",
    ])

    def first_corpus_move(machine):
        bundled = {r.name for r in machine.bundle}
        for s in machine.run(limit=400):
            if s.applied and s.applied.rule.name not in bundled:
                return s.applied.rule.name
        return None

    m = Machine()
    kb = load(m, src)
    move = first_corpus_move(m)
    check(
        "§19",
        "the agent works out for itself which rule serves its goal",
        m.holds(kb.term("prefer(<toward>, nearer(a), 1)")) == PLUS
        and m.holds(kb.term("prefer(<wander>, nearer(a), 1)")) is None,
    )
    check(
        "§14",
        "given two applicable rules, the one that serves the goal is chosen",
        move == "toward",
    )

    # Could that have failed? Delete the rule that derives the preference and the
    # accident of authoring decides again.
    m2 = Machine()
    load(m2, src)
    m2.rules.rules = [r for r in m2.rules.rules if r.name != "relevant"]
    m2.bundle = [r for r in m2.bundle if r.name != "relevant"]
    check(
        "§14",
        "and without `<relevant>` the authored order picks the useless one",
        first_corpus_move(m2) == "wander",
    )


def crossing_opens_hypotheses() -> None:
    """Crossing a modality is **one hypothesis, and more when something says so**
    -- and the number is not a parameter anywhere.

    `likely(p)` is crossed by an ordinary rule concluding `+suppose(p, likely)`.
    Considering the other case is another such rule. So *how many branches* is
    however many `suppose` facts get concluded, gated on whatever the corpus
    gates them on: there is no `k` in the machinery to set, and adding one would
    be §18's mistake again.

    Why the default has to be one: at one branch per uncertain fact the cost is a
    frame per **derivation**, which is linear, and `ugm.modality` measures that.
    At two, n independent uncertainties give 2^n combinations.

    > **The first branch is free and every branch after it is exponential** --
    > which is exactly why the second must be earned rather than assumed.

    Two things this took that were not obvious, and both are the same shape.
    """
    from .text import load

    world = [
        "rule <cross> = implies( { +uncertain(?p) },   { +suppose(?p, likely) } )",
        "rule <ifso>  = implies( { +rain(here) },      { +wet(street) } )",
        "rule <ifnot> = implies( { +not(rain(here)) }, { +dry(street) } )",
        "fact +uncertain(rain(here))",
    ]

    def run(extra):
        m = Machine()
        kb = load(m, chr(10).join(world + extra) + chr(10))
        steps = m.run(limit=600)
        return m, kb, steps

    m, kb, _ = run([])
    check(
        "§13",
        "crossing a modality opens one hypothesis, and its conclusion comes back wrapped",
        len(m.focus.children) == 1 and m.holds(kb.term("likely(wet(street))")) == PLUS,
    )
    check(
        "§16",
        "and the other case was never considered -- nothing said it should be",
        m.holds(kb.term("otherwise(dry(street))")) is None,
    )

    # **The alternative has to be opened ON RESUME.** Proposed at the same time
    # as the first, it is enacted while the register is already inside it, so it
    # becomes a sub-hypothesis rather than a sibling and the second case ends up
    # wrapped in the first. `left(?f, ?p)` is the occasion for *this hypothesis
    # is over*, and opening the alternative there is what makes them siblings --
    # which is what the frame FOREST was for.
    branch = [
        "rule <also>  = implies( { +left(?f, ?p), +uncertain(?p), +goal(doing(?q)) },",
        "                       { +suppose(not(?p), otherwise) } )",
        "fact +goal(doing(cross(road)))",
    ]
    m2, kb2, steps2 = run(branch)
    siblings = m2.focus.children
    check(
        "§13",
        "a rule opens a second hypothesis on resume, and the two are siblings",
        len(siblings) == 2 and all(f.state == "discharged" for f in siblings),
    )
    check(
        "§16",
        "so both cases are on the record, each wrapped in what it was supposed under",
        m2.holds(kb2.term("likely(wet(street))")) == PLUS
        and m2.holds(kb2.term("otherwise(dry(street))")) == PLUS,
    )
    check(
        "§17",
        "and neither leaked -- containment is structural, whatever the branching factor",
        m2.holds(kb2.term("wet(street)")) is None
        and m2.holds(kb2.term("dry(street)")) is None,
    )

    # ⚠ **A crossing rule that can match its own output runs away.** `<also>` on
    # `+left(?f, ?p)` alone fires again when the alternative is itself left, and
    # the run reached 32 sibling frames before its budget did. §9 records the
    # same trap for `<denial>`: translating both ways builds `not(not(p))` the
    # moment it meets its own output. The corpus stops it -- here by requiring
    # the hypothesis to be one it called `uncertain` in the first place.
    m3, _, steps3 = run([
        "rule <also> = implies( { +left(?f, ?p) }, { +suppose(not(?p), otherwise) } )",
    ])
    check(
        "§9",
        "a crossing rule matching its own output runs away; the corpus must stop it",
        len(m3.focus.children) > 8 and len(siblings) == 2,
    )
    check("§14", "and the gated version settles", steps2[-1].state == "quiescent")


def a_hypothesis_does_not_happen() -> None:
    """Supposing something must not bring it about -- and the reason to insist is
    not tidiness.

    The point of opening a hypothesis about a course of action is to find out
    whether it leads anywhere unacceptable. An agent that finds that out **by
    doing it** has not considered anything. So containment has to cover effects
    before a hypothesis is any use for the question, and it did not: dispatch is
    at the write (§16), and the write never asked where it was standing.

    Measured before the fix: supposing a premise whose rule concludes
    `+doing(fire(missile))` fired the missile. Not a leak in the chain -- the
    conclusion stayed inside and crossed out wrapped, exactly as designed. The
    boundary was ignoring the register, which no amount of correct wrapping fixes
    afterwards, because the act has already happened.

    What this makes possible is the veto §19 already built for norms, used
    forward in time: **explore the branch, and see whether it is refused.**
    Nothing has to be compared -- a hypothesis that reaches a prohibition has
    answered the question by itself.
    """
    from .text import load

    m = Machine()
    kb = load(m, "rule <act> = implies( { +p(x) }, { +doing(fire(missile)) } )")
    m.suppose(kb.term("p(x)"), wrap=kb.term("likely"))
    m.run(limit=100)
    check(
        "§17",
        "an act concluded inside a hypothesis does NOT leave the agent",
        m.emitted == [],
    )
    check(
        "§16",
        "and what it concluded still crosses out wrapped, so the agent knows it would have",
        m.holds(kb.term("likely(doing(fire(missile)))")) == PLUS,
    )
    check(
        "§11",
        "so nothing was done, and nothing claims it was",
        m.holds(kb.term("did(fire(missile))")) is None,
    )

    # The same thing, acted on for real when it is not a hypothesis -- otherwise
    # the check above would pass on an agent that simply never acts.
    m2 = Machine()
    kb2 = load(m2, chr(10).join([
        "rule <act> = implies( { +p(x) }, { +doing(fire(missile)) } )",
        "fact +p(x)",
        "",
    ]))
    m2.run(limit=100)
    check(
        "§11",
        "...while the same rule outside a hypothesis still acts",
        [m2.g.show(x) for x in m2.emitted] == ["fire(missile)"],
    )

    # And the use it was for: ask whether a course of action is acceptable by
    # supposing it, and let the norm answer. No comparison, no ranking -- the
    # branch that reaches a prohibition has disqualified itself.
    m3 = Machine()
    kb3 = load(m3, chr(10).join([
        "rule <act>    = implies( { +route(cliff) }, { +doing(drive(cliff)) } )",
        "fact <no-harm> = forbidden(doing(drive(cliff)))",
        "",
    ]))
    f = m3.suppose(kb3.term("route(cliff)"), wrap=kb3.term("likely"))
    m3.run(limit=100)
    check(
        "§19",
        "a hypothesis that reaches a prohibition refuses it, and says so on the record",
        m3.gate.refusals == 1 and m3.emitted == [],
    )
    check(
        "§13",
        "so the branch answers *is this acceptable* without anything being compared",
        f.state == "discharged",
    )


def doubt_is_a_tie() -> None:
    """A preference is a **score**, and doubt is what a score makes sayable.

    An order alone cannot distinguish *one clear best* from *two I cannot
    separate*, and those call for different behaviour: take the move, or think
    harder about it. So `prefer` is scored on §10's ordinal grade scale -- the
    entry's own grade, reused rather than invented -- and

    > **two rules are close exactly when they tie.**

    Ordinal, so this needs no threshold constant, which a numeric score would.
    §12 also says ordinals do not add, which is the other reason not to invent
    a cardinal one here.
    """
    from .text import load

    # Two candidates, nothing to separate them: both merely FIT the goal, which
    # `<relevant>` records `@possible`.
    tie = chr(10).join([
        "rule <byA> = implies( { +a(?x) }, { +at(?x) } )",
        "rule <byB> = implies( { +b(?x) }, { +at(?x) } )",
        "fact +a(p)",
        "fact +b(p)",
        "fact +goal(at(p))",
        "",
    ])
    def first_corpus_move(src):
        machine = Machine()
        load(machine, src)
        bundled = {r.name for r in machine.bundle}
        first = None
        for s in machine.run(limit=600):
            if first is None and s.applied and s.applied.rule.name not in bundled:
                first = s.applied.rule.name
        return first, machine

    _, m = first_corpus_move(tie)
    closes = [
        e for mm in m.chain.moments for e in mm.delta
        if m.g.relation_of(e.proposition) is m.CLOSE and e.sign == PLUS
    ]
    check("§19", "two equally-recommended rules are recorded as close", bool(closes))
    check(
        "§14",
        "and the choice was still made -- arbitration stays total, it is just no longer silent",
        first_corpus_move(tie)[0] == "byA",
    )

    # A stronger claim breaks the tie, because a preference is a score and not a
    # flag. `@certain` beats the `@possible` that mere candidacy earns.
    stronger = tie + "fact +prefer(<byB>, at(p), 5)" + chr(10)
    move, m2 = first_corpus_move(stronger)
    check(
        "§12",
        "a higher score outranks a lower one -- the table is compared as cardinals",
        move == "byB",
    )
    def doubted(machine):
        return any(
            machine.g.relation_of(e.proposition) is machine.CLOSE and e.sign == PLUS
            for mm in machine.chain.moments for e in mm.delta
        )

    check(
        "§19",
        "and once one is clearly better, there is no doubt left to record",
        not doubted(m2),
    )

    # *How close is close* is a knob, so it is a fact. Zero by default, so the
    # default is an exact tie and nothing depends on a constant nobody chose.
    _, m3 = first_corpus_move(stronger + "fact +tolerance(9)" + chr(10))
    check(
        "§19",
        "raising the tolerance makes a clear winner doubtful again",
        doubted(m3),
    )
    _, m3b = first_corpus_move(stronger + "fact +tolerance(1)" + chr(10))
    check(
        "§19",
        "...and a tolerance too small to span the gap leaves it decided",
        not doubted(m3b),
    )

    # The payoff: an agent that is harder to convince when the next step cannot
    # be taken back. *How careful am I being* becomes a claim with a trail,
    # rather than a threshold somebody chose once.
    careful = chr(10).join([
        "rule <byA> = implies( { +a(?x) }, { +doing(at(?x)) } )",
        "rule <byB> = implies( { +b(?x) }, { +doing(at(?x)) } )",
        "rule <care> = implies( { +goal(doing(?p)) }, { +tolerance(9) } )",
        # ...and being careful must come BEFORE the move it is about, which is
        # what `standing` says: apparatus ahead of opinions. Without it the
        # agent commits and then decides to be careful, which is no use.
        "fact standing(<care>)",
        "fact +a(p)",
        "fact +b(p)",
        "fact +prefer(<byB>, doing(at(p)), 5)",
        "fact +goal(doing(at(p)))",
        "",
    ])
    _, m4 = first_corpus_move(careful)
    check(
        "R4",
        "a rule can widen doubt when the step is irreversible -- the knob is arguable",
        doubted(m4),
    )


def prohibitions_are_not_recalled() -> None:
    """§19's carve-out, which is the one place the design refuses to be
    incomplete.

    > Recall may be incomplete about what to do. It may not be incomplete about
    > what you must not do.

    So a norm is not a rule. It is a veto at the gate, consulted on every write,
    indexed by what is about to be written -- never proposed, never matched,
    never arbitrated. The check that earns it is the last one here: narrow recall
    until the agent cannot even bring its own norms to mind, and the forbidden
    act still does not happen.
    """
    from .text import load

    src = chr(10).join([
        "rule <fix>  = implies( { +broken(?x) }, { +doing(repair(?x)) } )",
        "rule <burn> = implies( { +broken(?x) }, { +doing(harm(?x)) } )",
        "fact forbidden(doing(harm(?x)))",
        "fact +broken(pump)",
        "",
    ])
    m = Machine()
    kb = load(m, src)
    steps = m.run(limit=200)

    check("§19", "the permitted act happens", m.holds(kb.term("doing(repair(pump))")) == PLUS)
    check(
        "§19",
        "and the forbidden one does not -- the entry never exists, so nothing dispatched it",
        m.holds(kb.term("doing(harm(pump))")) is None
        and [m.g.show(x) for x in m.emitted] == ["repair(pump)"],
    )
    check(
        "§19",
        "refusing is not being silent: the refusal is an entry, with the norm as its licence",
        m.gate.refusals == 1
        and any(m.g.relation_of(e.proposition) is m.REFUSED
                for mm in m.chain.moments for e in mm.delta),
    )
    check(
        "§14",
        "a rule whose conclusion is always refused applies once, not forever",
        steps[-1].state == "quiescent",
    )

    # A norm is a belief, and it is consulted as one -- resolved at the writer's
    # own position, so a hypothesis can carry one. But it CANNOT yet be revised
    # from the surface, and the reason is worth pinning rather than discovering:
    # a norm's argument is a description, a description is an authored statement,
    # and §8 scopes a statement's variables to it. So `-forbidden(doing(harm(?x)))`
    # written a second time is a different node saying a similar thing, and the
    # denial lands on nothing.
    #
    # That is the project's own *never identify by name alone* arriving somewhere
    # new. Revising a norm needs a way to NAME one, the way `<...>` names a rule.
    # §21 carries it.
    m2 = Machine()
    kb2 = load(m2, src + chr(10) + "fact -forbidden(doing(harm(?x)))" + chr(10))
    m2.run(limit=200)
    check(
        "§8",
        "restating a norm does not deny it -- two descriptions are two nodes",
        m2.holds(kb2.term("doing(harm(pump))")) is None and m2.gate.refusals == 1,
    )
    # Which is what naming is for. `<...>` is the namespace of STATEMENTS, and a
    # description is a statement, so the same marker that lets a fact be about a
    # rule lets a fact be about a norm.
    named = chr(10).join([
        "rule <fix>  = implies( { +broken(?x) }, { +doing(repair(?x)) } )",
        "rule <burn> = implies( { +broken(?x) }, { +doing(harm(?x)) } )",
        "fact <no-harm> = forbidden(doing(harm(?x)))",
        "fact +broken(pump)",
        "",
    ])
    m3 = Machine()
    kb3 = load(m3, named + "fact -<no-harm>" + chr(10))
    m3.run(limit=200)
    check(
        "§12",
        "denied by name, a norm stops forbidding -- it was an ordinary belief all along",
        m3.holds(kb3.term("doing(harm(pump))")) == PLUS and m3.gate.refusals == 0,
    )

    # §19 keeps norms out of RECALL. It never said they were beyond argument, and
    # a rule can retire one.
    m4 = Machine()
    kb4 = load(m4, named + chr(10).join([
        "rule <emergency> = implies( { +says(fire, evacuate, plus) }, { -<no-harm> } )",
        "say fire: +evacuate",
        "",
    ]))
    m4.run(limit=300)
    check("R3", "a rule can retire a norm by naming it", m4.holds(kb4.term("doing(harm(pump))")) == PLUS)
    check(
        "§19",
        "and until it did, the norm held: the refusal is still on the record",
        m4.gate.refusals >= 1,
    )

    # ...and it never needed the name, which is worth pinning because the
    # opposite is easy to assume. Matching a rule's generic antecedent against a
    # stored DESCRIPTION treats the description's variables as ordinary nodes, so
    # `?y` binds to the stored `?x` and substitution rebuilds exactly the node
    # that was written. A rule refers to a norm the way it refers to a plan or a
    # frame: by BINDING it, not by naming it.
    #
    # So naming buys authoring -- a second surface statement about a description
    # -- and a handle to hang ordinary facts on. It never bought reference.
    m5 = Machine()
    kb5 = load(m5, chr(10).join([
        "rule <fix>   = implies( { +broken(?x) }, { +doing(repair(?x)) } )",
        "rule <burn>  = implies( { +broken(?x) }, { +doing(harm(?x)) } )",
        "rule <lift>  = implies( { +says(fire, evacuate, plus), +forbidden(doing(harm(?y))) },",
        "                       { -forbidden(doing(harm(?y))) } )",
        "fact forbidden(doing(harm(?x)))",
        "fact +broken(pump)",
        "say fire: +evacuate",
        "",
    ]))
    m5.run(limit=400)
    check(
        "R3",
        "and it did not need the name -- a rule can describe a norm's shape and retire it",
        m5.holds(kb5.term("doing(harm(pump))")) == PLUS and m5.gate.refusals == 1,
    )

    # One namespace, so the marker keeps doing its job.
    clash = False
    try:
        load(Machine(), "rule <n> = implies( { +a }, { +b } )" + chr(10) + "fact <n> = forbidden(c(?x))")
    except Exception:
        clash = True
    check("§3", "a rule and a norm cannot share a name -- one statement namespace", clash)

    # The carve-out, measured. Narrow recall to one rule and the agent cannot
    # reliably bring anything to mind -- but a norm was never in the running.
    m6 = Machine()
    kb6 = load(m6, src)
    m6.recall_budget = 1
    m6.run(limit=400)
    check(
        "§19",
        "under a recall budget the forbidden act is STILL refused -- a norm is not a competitor",
        m6.holds(kb6.term("doing(harm(pump))")) is None and m6.gate.refusals >= 1,
    )
    check(
        "§19",
        "while what to DO stayed incomplete-able: the same budget still let the agent act",
        m6.holds(kb6.term("doing(repair(pump))")) == PLUS,
    )


def the_index_agrees_with_the_walk() -> None:
    """§4's read, indexed -- and checked against the walk it replaced.

    `resolve` used to scan every entry ever deposited to answer a question about
    one proposition. Measured, that was 86% of the engine's runtime, then 70% of
    it again after the loop stopped repeating the same walk once per rule. It is
    now an index over what was asserted, which is the licence §3 gives the
    substrate and §12 puts a condition on: **index what was asserted, never what
    was derived.**

    Replacing a walk with an index is exactly the kind of change that is right
    for a fixture and wrong for a fork, so it is checked against a brute-force
    walk over a world that has both -- nested suppositions (which fork) and a
    revision about an earlier moment (which separates the two orderings).
    """
    from .text import load

    m = Machine()
    kb = load(m, chr(10).join([
        "rule <a> = causes(  { +p(?x) }, { +q(?x) } )",
        "rule <b> = implies( { +q(?x) }, { +r(?x) } )",
        "rule <c> = implies( { +likely(?p) }, { +suppose(?p, likely) } )",
        "fact +p(one)",
        "fact +likely(p(two))",
        "",
    ]))
    m.run(limit=400)
    # A revision about an earlier moment: same locus, later deposit (§17).
    old = m.focus.seat.ancestors()[-1]
    m.gate.write(m.gate.frame(m.focus.seat, topic=old), kb.term("q(one)"), MINUS)
    m.suppose(kb.term("p(three)"), wrap=kb.term("possible"))
    m.run(limit=400)

    def brute(proposition, locus, seat):
        best = None
        for mo in seat.ancestors():
            for e in reversed(mo.delta):
                if e.proposition != proposition or not locus.at_or_after(e.locus):
                    continue
                if best is None or e.locus.depth > best.locus.depth:
                    best = e
        return best

    props = {e.proposition for mo in m.chain.moments for e in mo.delta}
    seats = m.chain.moments
    disagreements, comparisons = [], 0
    for p in props:
        for seat in seats:
            for locus in seat.ancestors():
                comparisons += 1
                if m.chain.resolve(p, locus, seat) is not brute(p, locus, seat):
                    disagreements.append((p, locus, seat))

    check(
        "§4",
        f"the indexed read agrees with the walk it replaced, {comparisons} comparisons",
        not disagreements,
    )
    check(
        "§4",
        "...over a world that forks and revises, so the comparison could have failed",
        len(m.chain.moments) > 6
        and any(f.state == "discharged" for f in _frames(m))
        and comparisons > 1000,
    )


def a_cause_moves_the_register() -> None:
    """Found by a fixture that was trying to measure something else.

    A `causes` rule lands in a *later* moment, so applying one advances the seat.
    That was done by minting a fresh frame -- which dropped the parent, the
    purpose and the wrap. Under a hypothesis it orphaned the register: `_leave`
    could never fire, the frame was never discharged, and everything concluded
    under that hypothesis stayed inside it with nothing anywhere saying so.

    §4 allows exactly one register. Advancing it is a **seat move**, not a new
    frame, and §17 already says every seat move is a write -- which is what
    `reseat` is for. Discharge then needs the frame's *origin* rather than its
    current seat, because those stop being the same thing the moment it moves.
    """
    from .text import load

    out = {}
    for conn in ("implies", "causes"):
        m = Machine()
        kb = load(m, f"rule <a> = {conn}( {{ +p(?x) }}, {{ +q(?x) }} )")
        f = m.suppose(kb.term("p(x)"), wrap=kb.term("likely"))
        m.run(limit=60)
        out[conn] = (f, m, kb)

    for conn, (f, m, kb) in out.items():
        check(
            "§13",
            f"a hypothesis whose reasoning used `{conn}` is still left and discharged",
            f.state == "discharged" and len(f.carried) == 1,
        )
        check(
            "§16",
            f"...and its conclusion crosses out wrapped, not bare (`{conn}`)",
            m.holds(kb.term("likely(q(x))")) == PLUS and m.holds(kb.term("q(x)")) is None,
        )

    # Two moments deep inside one hypothesis: discharge must carry BOTH, which is
    # what reading the start of the frame off `seat` would have got wrong.
    m2 = Machine()
    kb2 = load(m2, chr(10).join([
        "rule <a> = causes( { +p(?x) }, { +q(?x) } )",
        "rule <b> = causes( { +q(?x) }, { +r(?x) } )",
        "",
    ]))
    f2 = m2.suppose(kb2.term("p(x)"), wrap=kb2.term("likely"))
    m2.run(limit=60)
    check(
        "§13",
        "every moment inside a frame is discharged, not just the last one",
        m2.holds(kb2.term("likely(q(x))")) == PLUS
        and m2.holds(kb2.term("likely(r(x))")) == PLUS,
    )


def _frames(m) -> list:
    out, seen = [], []
    f = m.focus
    while f is not None:
        seen.append(f)
        f = f.parent
    for f in seen:
        out.append(f)
        out.extend(f.children)
    return out


def reference_is_binding() -> None:
    """What a rule can refer to, and how -- measured rather than assumed.

    The question that prompted it: does a supposition need a name? a plan? Mostly
    not. Language rarely names things either; it says *the plan we made before*.
    The engine's version of that is **binding**: anything deposited as an entry
    can be bound by an antecedent, and that is reference.

    What that leaves is the harder half -- *which* one. Several plans match *a
    plan*, and nothing in a rule can say *the latest*.
    """
    from .text import load

    m = Machine()
    kb = load(m, chr(10).join([
        "rule <boil> = implies( { +heat(?w) }, { +boiling(?w) } )",
        "rule <p>    = implies( { +expands(?plan, ?w, ?r) }, { +noted(?plan) } )",
        "fact +goal(boiling(kettle))",
        "",
    ]))
    m.run(limit=300)
    check(
        "R3",
        "a plan is referable without a name -- the rule that made it binds it",
        m.holds(kb.term("noted(plan(<boil>, boiling(kettle)))")) == PLUS,
    )

    m1 = Machine()
    kb1 = load(m1, chr(10).join([
        "rule <in> = implies( { +h(?x) },            { +q(?x) } )",
        "rule <f>  = implies( { +left(?frame, ?a) }, { +noted(?a) } )",
        "fact +suppose(h(a), hyp)",
        "",
    ]))
    m1.run(limit=300)
    check(
        "R3",
        "and so is a hypothesis, from the occasion of leaving it",
        m1.holds(kb1.term("noted(h(a))")) == PLUS,
    )

    # Which one, though. Two candidates match one description, and the order they
    # are tried in was undeclared until this check: `ancestors()` is newest-first,
    # but a moment's delta was oldest-first, so two facts written by `implies`
    # came out in the opposite order to two written by `causes` -- and which
    # connective a rule used has nothing to do with reference.
    def order(conn):
        mm = Machine()
        load(mm, chr(10).join([
            f"rule <one> = {conn}( {{ +trigger(a) }},    {{ +plan(first, x) }} )",
            f"rule <two> = {conn}( {{ +plan(first, x) }}, {{ +plan(second, x) }} )",
            "rule <ref> = implies( { +plan(?p, x) },      { +chose(?p) } )",
            "fact +trigger(a)",
            "",
        ]))
        steps = mm.run(limit=60)
        return [mm.g.show(e.proposition) for s in steps if s.applied
                for e in s.wrote if mm.g.show(e.proposition).startswith("chose")]

    check(
        "§3",
        "a description with two candidates resolves to the most recent",
        order("implies")[0] == "chose(second)",
    )
    check(
        "§3",
        "and the same, whichever connective deposited them -- the walk is one order",
        order("implies") == order("causes"),
    )



def quiescence_is_an_occasion() -> None:
    """§5 named two places the machinery declines. The third is the loop running
    out of work, and it was the one that declined in silence.

    A watchdog needs no trigger table and no second loop: `quiet(<m>)` is a fact,
    so a watchdog is an ordinary rule that names it in its antecedent -- inert
    until the loop stops, because nothing else ever writes it.

    The cost, found by hitting it: **the occasion persists.** `quiet` is an
    entry, not an event, so a watchdog is armed from quiescence onwards rather
    than fired once. One whose conclusion creates new matches for itself --
    `+quiet(?m), +blocked(?g) => +goal(ask(?g))`, where the new goal is blocked
    in turn -- runs until its budget. Quiescence is what stops the honest ones,
    and it is not enough on its own.
    """
    from .text import load

    src = chr(10).join([
        "rule <watch> = implies( { +quiet(?m), +blocked(?g) }, { +stuck(?g) } )",
        "rule <escal> = implies( { +stuck(?g) },               { +doing(ask(user, ?g)) } )",
        "fact +goal(fixed(pump))",
        "",
    ])
    m = Machine()
    kb = load(m, src)
    steps = m.run(limit=400)

    check(
        "§5",
        "the loop running out of work is deposited, not merely returned",
        m.holds(m.g.rel(m.QUIET, m.focus.seat.node)) == PLUS,
    )
    check("§5", "and the tick reports which silence it was", any(s.state == "quiet" for s in steps))
    check(
        "§15",
        "a watchdog catches reasoning stopping with a goal still open",
        m.holds(kb.term("stuck(fixed(pump))")) == PLUS,
    )
    check(
        "§15",
        "and the agent escalates instead of dying quietly -- an act, not a log line",
        m.holds(kb.term("did(ask(user, fixed(pump)))")) == PLUS,
    )
    check(
        "§18",
        "the watchdog is an ordinary rule -- nothing about it is a phase",
        kb.rules_by_name["watch"] in m.rules.rules,
    )
    check(
        "§14",
        "waking is once per seat, so the occasion cannot re-arm itself",
        sum(1 for s in steps if s.state == "quiet") == 1,
    )
    check("§14", "and the loop settles after the watchdog has had its say",
          steps[-1].state == "quiescent")


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
    denial_nests()
    mention_propagates()
    surprise_is_four_rows()
    callbacks_on_a_hypothesis()
    recall_is_narrowable()
    the_better_move_wins()
    crossing_opens_hypotheses()
    a_hypothesis_does_not_happen()
    doubt_is_a_tie()
    prohibitions_are_not_recalled()
    the_index_agrees_with_the_walk()
    a_cause_moves_the_register()
    reference_is_binding()
    quiescence_is_an_occasion()
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
