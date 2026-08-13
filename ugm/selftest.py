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

    # ⚠ None-safe, and the reason is a probe. Deleting <intake> from the bundle
    # made this raise an AttributeError instead of failing -- so a mutation that
    # ought to send someone here crashed the runner three checks earlier and
    # every check after it went unreported. A runner whose contract is *any False
    # is a failure* has to be able to say False about an absence.
    e = m.chain.resolve(raining, m.focus.topic, m.focus.seat)
    check("§12", "the conclusion is no stronger than the rule allowed", e is not None and e.grade == "likely")
    check("§5", "the conclusion names what produced it", e is not None and e.licence is not None)

    trail = m.chain.trail(e) if e is not None else []
    check("§13", "the trail reaches the utterance", any(t.proposition == said for t in trail))
    check(
        "§13",
        "and the utterance names the channel it arrived through",
        any(t.source == user for t in trail),
    )
    check("R5", "why() answers with more than the claim itself", len(m.why(raining)) > 1)
    check("§13", "a derived entry's channel is the KB, not the rule", e is not None and e.source == m.KB)
    check("§13", "and the rule is its licence, not its channel", e is not None and e.licence != e.source)

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

    trail = m.chain.trail(e) if e is not None else []
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


def the_surface_can_say_what_the_apparatus_is_made_of() -> None:
    """The bundle is authored in the surface, so a corpus can argue with it.

    §2's expressibility criterion, applied to the apparatus itself. While the
    bundle was built in Python it was *data* in every sense the design asks for
    -- nameable, reifiable, defeasible -- except the one nobody had checked:
    that the vocabulary it is written in is the vocabulary a corpus writes in.
    Two relations were not (`arrived`, `not`), and the failure mode was silence
    rather than an error, because `Graph.atom` mints a fresh node per call. A
    corpus rule about `arrived` built a TWIN, matched nothing, and reported
    nothing -- the trap this codebase has now paid for five times.

    So these are interoperation checks, not parse checks. Each pairs a corpus
    rule against a bundled one over the same relation: if the two names were
    different nodes, the bundled half would still work and the corpus half would
    be silently dead, which is exactly what a parse check would miss.
    """
    from .text import load

    # `arrived` -- <intake>'s antecedent. The corpus rule reads the same
    # arrival <intake> does.
    m = Machine()
    kb = load(m, chr(10).join([
        "rule <watch> = implies( { +arrived(?c, ?p, ?s) }, { +noticed(?c) } )",
        "",
    ]))
    # ⚠ Through the LOADER's table, both of them. The first version of this check
    # used `channels.open("user")` and `g.rel(g.atom("raining"), ...)`, which mint
    # fresh nodes -- so it failed on twins, in a check written about twins. That
    # is `channels.use` earning its place: a surface that has already coined a
    # node is the normal case, and minting beside it is the bug.
    user, raining = kb.term("user"), kb.term("raining(here)")
    m.channels.deliver(m.channels.use(user), raining, PLUS)
    m.run(limit=12)
    check(
        "§2",
        "a corpus rule reads the same arrival the bundle does",
        m.holds(kb.term("noticed(user)")) == PLUS,
    )
    check(
        "§2",
        "...and the bundled reading of it still happened",
        m.holds(kb.term("says(user, raining(here), plus)")) == PLUS,
    )

    # `not` -- <denial>'s antecedent. A corpus states §9's denial-as-a-term and
    # the bundled rule turns it into a denial-as-a-sign.
    m = Machine()
    kb = load(m, chr(10).join([
        "fact +not(raining(here))",
        "",
    ]))
    m.run(limit=12)
    check(
        "§9",
        "a corpus can state denial as a term, and <denial> reads it",
        m.holds(kb.term("raining(here)")) == MINUS,
    )

    # `unsure` -- not load-bearing for the bundle (see `Machine.reserved`), so it
    # is checked on its own account. What it buys is the ability to SAY the third
    # sign, not merely to use it: §9 insists `?` is a claim, and a vocabulary in
    # which two signs are speakable and the third is not makes *I expected to be
    # unable to say* unwritable.
    m = Machine()
    kb = load(m, chr(10).join([
        "rule <vague> = implies( { +expects(?p, unsure) }, { +hedged(?p) } )",
        "fact +expects(raining(here), unsure)",
        "",
    ]))
    m.run(limit=12)
    check(
        "§9",
        "the third sign can be spoken about, not only used",
        m.holds(kb.term("hedged(raining(here))")) == PLUS,
    )
    check(
        "§9",
        "and it is the machinery's own sign node, not a lookalike",
        kb.term("unsure") == m.rules.SIGN[UNSURE],
    )

    # And the guard that keeps this from reopening. A bundled rule reaching for a
    # relation `reserved` does not carry is a construction error now -- deleting
    # either name above fails `Machine()`, which is how the two were found.
    m = Machine()
    saved = dict(m.reserved)
    ok = False
    try:
        m.reserved.pop("goal")
        m._vocabulary_is_surface_nameable()
    except RuntimeError:
        ok = True
    finally:
        m.reserved.clear()
        m.reserved.update(saved)
    check(
        "§2",
        "a bundled relation a corpus cannot name is refused, not tolerated",
        ok,
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
    check("§12", "and it is no stronger than the rule allowed", e is not None and e.grade == "likely")
    check("§13", "the channel in the rule is the channel delivered on", e is not None and any(t.source == kb.term("user") for t in m.chain.trail(e)))
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


def rival_hypotheses_are_comparable() -> None:
    """Which hypothesis concluded WHAT -- §21's defect for the eighth time.

    The deleted `ugm/hypothesis.py` had `rivals(about)`, and its docstring made
    coexisting rivals the headline advantage over one-at-a-time supposition:
    *two hypotheses coexist, both readable, and choosing between them is an
    ordinary comparison.* This floor kept the first half and lost the second.
    Two suppositions about the same symptom both cross their conclusions to the
    same parent as `likely(q)`, and which frame produced which was recorded only
    as the crossed entry's LICENCE -- `concluded(<frame>)`, a Python field, so no
    rule could ask. A corpus could open rivals and then not compare them.

    Same defect and same fix as `applied(<R>)` -> `exercised`, the entry's grade
    -> the `possible` wrapper, a tool's binding -> `answers(<M>, ask)`, and the
    effort counters -> `widened`/`reached`/`bounded`: **deposit the record.**

        concluded(<frame>, <what>)     this hypothesis reached this

    The discriminating case is deliberately NOT *the two rivals disagree*. Both
    predict `wet(floor)`, which is what makes them rivals worth comparing at all;
    what tells them apart is a prediction only one of them makes. So the join is
    over a shared conclusion and a distinguishing one, and a record that merely
    said *something was concluded here* would pass the first and fail the second.
    """
    from .text import load

    src = chr(10).join([
        # Two rival diagnoses of one symptom. Both predict a wet floor; only the
        # broken pipe predicts the tap losing pressure.
        "rule <wet-a>  = implies( { +broken(pipe) },  { +wet(floor) } )",
        "rule <wet-b>  = implies( { +spilled(jug) },  { +wet(floor) } )",
        "rule <dry-a>  = implies( { +broken(pipe) },  { +nopressure(tap) } )",
        # Entertained one after the other rather than nested: the second is
        # proposed on the occasion of the first being LEFT, so both are children
        # of the agent's own frame and their conclusions are siblings.
        "rule <first>  = implies( { +maybe(?p) }, { +suppose(?p, likely) } )",
        "rule <second> = implies( { +left(?f, broken(pipe)) },",
        "                        { +suppose(spilled(jug), likely) } )",
        # ...and the comparison, which is the line no corpus could write before.
        "rule <blame>  = implies( { +left(?f, ?a), +concluded(?f, likely(nopressure(tap))) },",
        "                        { +explains(?a, nopressure(tap)) } )",
        "fact +maybe(broken(pipe))",
        "",
    ])
    m = Machine()
    kb = load(m, src)
    steps = m.run(limit=400)

    # ⚠ By NODE, never by name. Every frame prints as `frame(moment(), moment())`,
    # so a set of `g.show` strings collapses two rivals into one -- the twin trap
    # this repo has recorded six times, here in an instrument rather than in the
    # engine. Names are not identity; that is what makes them safe to print.
    frames = {
        m.g.member(e.proposition, 0)
        for mm in m.chain.moments for e in mm.delta
        if m.g.relation_of(e.proposition) is m.LEFT and e.sign == PLUS
    }
    check("§13", "two rival hypotheses were entertained, neither nested in the other",
          len(frames) == 2 and steps[-1].state == "quiescent")
    check("§16", "and both crossed the shared prediction out",
          m.holds(kb.term("likely(wet(floor))")) == PLUS)

    # ⚠ Arity-guarded, so a record that forgot the WHAT reports False instead of
    # raising. A runner that cannot say False about an absence is the instrument
    # bug this suite has now hit three times, and it was hit again here: the
    # first version indexed member 1 unconditionally, so the mutation that
    # deposits `concluded(<frame>)` alone crashed the run rather than failing.
    recorded = {
        (m.g.member(e.proposition, 0), m.g.show(m.g.member(e.proposition, 1)))
        for mm in m.chain.moments for e in mm.delta
        if m.g.relation_of(e.proposition) is m.CONCLUDED and e.sign == PLUS
        and len(m.g.members(e.proposition)) == 2
    }
    check(
        "§21",
        "the shared conclusion is recorded against BOTH frames -- rivals agreeing is sayable",
        len({f for f, what in recorded if what == "likely(wet(floor))"}) == 2,
    )
    check(
        "§21",
        "...and the distinguishing one against exactly one of them",
        len({f for f, what in recorded if what == "likely(nopressure(tap))"}) == 1,
    )
    # The payoff, and the gate: delete the deposit and this is the check that
    # goes out. A corpus rule discriminated between two hypotheses by what each
    # one concluded, which is `rivals(about)`'s whole purpose.
    check(
        "§21",
        "so a corpus rule can say WHICH hypothesis explains a prediction",
        m.holds(kb.term("explains(broken(pipe), nopressure(tap))")) == PLUS,
    )
    check(
        "§12",
        "...and does not credit the rival that concluded no such thing",
        m.holds(kb.term("explains(spilled(jug), nopressure(tap))")) is None,
    )
    # It is a record about the frame, not a claim about the world: bookkeeping,
    # so a nested frame does not carry `likely(concluded(...))` out. Same
    # treatment `left` and `quiet` get, and for the same reason.
    # The record is bookkeeping, so a nested frame does not carry
    # `likely(concluded(...))` out -- the treatment `left` and `quiet` get.
    #
    # ⚠ This needs its OWN fixture, and finding that out is the finding. Asked of
    # the rivals above it is a check that cannot fail: they are siblings, so every
    # `concluded` record is written at the root and no wrapper is ever in a
    # position to reach one. A `concluded` has to be written INSIDE a frame for
    # the crossing to have anything to wrap, and only nesting puts it there.
    # *A fixture can only see a filter that its rules can reach* -- recorded
    # about a one-member antecedent, arriving here from the frame side.
    nested = chr(10).join([
        "rule <outer>  = implies( { +ask(?p) }, { +suppose(?p, likely) } )",
        "rule <inner>  = implies( { +a },       { +suppose(b, likely) } )",
        "rule <derive> = implies( { +b },       { +c } )",
        "fact +ask(a)",
        "",
    ])
    m2 = Machine()
    kb2 = load(m2, nested)
    m2.run(limit=400)
    likely = m2.g.relation_of(kb2.term("likely(c)"))
    wrapped = [
        m2.g.show(e.proposition)
        for mm in m2.chain.moments for e in mm.delta
        if m2.g.relation_of(e.proposition) is likely
        and m2.g.relation_of(m2.g.member(e.proposition, 0)) is m2.CONCLUDED
    ]
    check(
        "§13",
        "a hypothesis inside a hypothesis records its conclusion in the outer one",
        any(
            m2.g.relation_of(e.proposition) is m2.CONCLUDED and e.sign == PLUS
            for mm in m2.chain.moments for e in mm.delta
        ) and m2.holds(kb2.term("likely(likely(c))")) == PLUS,
    )
    check(
        "§13",
        "...and the record is bookkeeping -- nothing carries it out of a frame wrapped",
        not wrapped,
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

    # Could that have failed? Not on THIS fixture, any more, and the reason is
    # worth more than the check was.
    #
    # It used to: with a budget of 3 the shortlist filled with bundled rules by
    # authored order, `<ask-fit>` was never proposed, and the verdict reported a
    # goal blocked that the corpus could reach. Two later changes each remove that
    # independently -- §14 moved *what could produce this* off the shortlist and
    # into `by_conclusion`, so backward reading no longer goes through `_recall`
    # at all; and §19's third carve-out keeps `standing` rules out of the cap, so
    # the apparatus cannot be narrowed away in the first place.
    #
    # So the negative control is reported rather than quietly dropped: the
    # VERDICT half of the widening argument is now guarded twice over, and this
    # fixture can no longer kill the line. What still can is below -- widening is
    # load-bearing for reaching a conclusion, which is the other half and the one
    # §15 states.
    m4 = Machine()
    kb4 = load(m4, goal)
    m4.recall_budget = 3
    m4._widen = lambda: False  # type: ignore[assignment]
    m4.run(limit=200)
    check(
        "§19",
        "the verdict half is now guarded twice over -- an unwidened shortlist no "
        "longer invents `blocked` here, so this fixture cannot kill the line",
        m4.holds(kb4.term("pursued(water(kettle))")) == PLUS,
    )

    # ...and the line is still load-bearing, on the fixture that can kill it.
    m5 = Machine()
    kb5 = load(m5, chain)
    m5.recall_budget = 3
    m5._widen = lambda: False  # type: ignore[assignment]
    m5.run(limit=2000)
    check(
        "§15",
        "without widening the same corpus never reaches a conclusion it could -- "
        "the check can fail",
        m5.holds(kb5.term("s(a)")) is None,
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


def what_the_situation_is_about() -> None:
    """`_in_play` -- the one judgement in the loop that nothing argued for.

    §19 says a preference row is *matched when that key is in play* and never
    says what **in play** means. It is `Machine._in_play`: the relations in the
    current delta, plus each live goal's content and that content's relation.
    A convention, in Python, that no rule can read -- and until this it had no
    check of its own, no section, and no measurement. Every mutation of it was
    caught only incidentally, by checks about something else.

    Four variants against the same fixture as `the_better_move_wins`, which is
    the smallest thing that can tell a goal-serving rule from a useless one.

    | `_in_play` returns | first corpus move |
    |---|---|
    | as shipped | `toward` |
    | nothing | `wander` |
    | the delta only, no goals | `wander` |
    | goals only, no delta | `toward` |
    | everything the state asserts | `wander` |

    ⭐ **The key is not a subset of what is asserted**, which is the finding and
    the reason a sweep is not a substitute. Nothing ever claims `nearer(a)`; what
    is claimed is `goal(nearer(a))`. So an indiscriminate pass over every
    proposition and relation in the state -- strictly more than the shipped key
    -- still misses the one node the preference is keyed on, because the key
    reaches INSIDE a proposition for its argument. More is not nearer.

    ⚠ And the two halves are not one idea. The goal half decides this; the delta
    half decides nothing here, and over the whole suite it carries two checks,
    both about the recall BUDGET rather than about arbitration. They also differ
    in character: a goal is never denied, so the goal half already accumulates,
    while the delta half is genuinely per-moment. Whether the first should be
    facts is therefore open; the second could not be, on an append-only chain.
    """
    from .text import load

    src = chr(10).join([
        "rule <wander> = implies( { +at(?x) }, { +wandered(?x) } )",
        "rule <toward> = implies( { +at(?x) }, { +nearer(?x) } )",
        "fact +at(a)",
        "fact +goal(nearer(a))",
        "",
    ])

    def move() -> str:
        machine = Machine()
        load(machine, src)
        bundled = {r.name for r in machine.bundle}
        for s in machine.run(limit=400):
            if s.applied and s.applied.rule.name not in bundled:
                return s.applied.rule.name
        return None

    def nothing(self):
        return set()

    def delta_only(self):
        out = set()
        for e in self.focus.seat.delta:
            rel = self.g.relation_of(e.proposition)
            if rel is not None:
                out.add(rel)
        return out

    def goals_only(self):
        out = set()
        for s in self._state():
            if s.sign == PLUS and self.g.relation_of(s.proposition) is self.GOAL:
                wanted = self.g.member(s.proposition, 0)
                out.add(wanted)
                rel = self.g.relation_of(wanted)
                if rel is not None:
                    out.add(rel)
        return out

    def everything_asserted(self):
        out = set()
        for s in self._state():
            rel = self.g.relation_of(s.proposition)
            if rel is not None:
                out.add(rel)
            out.add(s.proposition)
        return out

    original = Machine._in_play
    moves = {}
    try:
        for name, fn in (
            ("shipped", original),
            ("nothing", nothing),
            ("delta-only", delta_only),
            ("goals-only", goals_only),
            ("everything-asserted", everything_asserted),
        ):
            Machine._in_play = fn
            moves[name] = move()
    finally:
        # In a `finally`, because a probe that mutates and crashes before
        # restoring is how a whole turn's edits were once thrown away. Here it
        # would leave every later check in this run measuring a mutant.
        Machine._in_play = original

    check("§19", "the key as shipped picks the rule that serves the goal",
          moves["shipped"] == "toward")
    check("§19", "an empty key ranks nothing, and authored order decides again",
          moves["nothing"] == "wander")
    check("§19", "the GOAL half is what decides -- drop it and the useless rule wins",
          moves["delta-only"] == "wander")
    check("§19", "...and the delta half decides nothing here; it serves the recall budget",
          moves["goals-only"] == "toward")
    check(
        "§19",
        "⭐ the key is not a subset of what is asserted: every proposition in the "
        "state is strictly more, and still misses the goal's content",
        moves["everything-asserted"] == "wander",
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

    # **Deciding to act is a conclusion; planning needs the action's assumed
    # outcome.** Blocking the emission is not enough -- the first repair here
    # also stopped the reasoning, so a plan died at its first action instead of
    # continuing past it. The record is deposited under a different name
    # (`taken`), `<taken>` makes it a `did`, and §15's `<assert-act>` supplies
    # the assumption that it worked. One row, not one branch.
    m1 = Machine()
    kb1 = load(m1, chr(10).join([
        "rule <step1> = implies( { +at(home) },     { +doing(travel(work)) } )",
        "rule <step2> = implies( { +travel(work) }, { +doing(open(door)) } )",
        "rule <step3> = implies( { +open(door) },   { +arrived(work) } )",
        "",
    ]))
    m1.suppose(kb1.term("at(home)"), wrap=kb1.term("likely"))
    m1.run(limit=400)
    check(
        "§15",
        "planning continues PAST an action, on its assumed outcome",
        m1.holds(kb1.term("likely(arrived(work))")) == PLUS,
    )
    check(
        "§17",
        "...and a three-step plan was worked out with nothing done at all",
        m1.emitted == [],
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


def an_action_is_substituted_by_its_outcome() -> None:
    """Planning should take a rule that suggests an action and **substitute the
    call with the expected outcome** -- operator semantics, and it needs no plan
    machinery at all.

        rule <outcome> = implies( { +did(?a), +achieves(?a, ?y) }, { +?y } )
        fact achieves(travel(work), at(work))

    One rule and a fact per action. The bare-variable consequent is the same
    shape `<assert-act>` uses and legal for the same reason: `?y` is bound by the
    antecedent. Measured: a two-step plan runs to its end inside a hypothesis
    with nothing emitted, and the actions' effects rather than the actions carry
    it.
    """
    from .text import load

    src = chr(10).join([
        "rule <go>      = implies( { +at(home) }, { +doing(travel(work)) } )",
        "rule <enter>   = implies( { +at(work) }, { +doing(open(door)) } )",
        "rule <outcome> = implies( { +did(?a), +achieves(?a, ?y) }, { +?y } )",
        "fact achieves(travel(work), at(work))",
        "fact achieves(open(door), inside(work))",
        "",
    ])

    def plan(extra=""):
        m = Machine()
        kb = load(m, src + extra)
        m.suppose(kb.term("at(home)"), wrap=kb.term("likely"))
        m.run(limit=600)
        return m, kb

    m, kb = plan()
    check(
        "§15",
        "an action's declared outcome carries the plan forward -- no plan machinery",
        m.holds(kb.term("likely(inside(work))")) == PLUS and m.emitted == [],
    )

    # A corpus can NAME a bundled rule. Every section that says *a corpus can
    # override this* depended on it, and none of it was true: the loader knew
    # only the names a corpus declared itself, so the bundle shipped as data and
    # was reachable only from Python.
    m2, kb2 = plan("fact overrides(<outcome>, <assert-act>)" + chr(10))
    check(
        "R3",
        "a corpus can name a bundled rule, so the bundle is finally arguable",
        len(m2.rules.overrides) == 1,
    )
    check(
        "§15",
        "...and overriding `<assert-act>` substitutes the call: only the outcome is asserted",
        m2.holds(kb2.term("likely(inside(work))")) == PLUS
        and m2.holds(kb2.term("likely(travel(work))")) is None,
    )

    # ⚠ And what that cannot express. §12's defeat is about the RULE and the
    # TICK, not about the binding: `<outcome>` matching for one action defeats
    # `<assert-act>` for every action in that step. So an act with no declared
    # outcome loses the fallback too, and *substitute where an outcome is
    # declared, otherwise assume* is not sayable with precedence.
    m3, kb3 = plan(chr(10).join([
        "fact overrides(<outcome>, <assert-act>)",
        "rule <wave> = implies( { +at(work) }, { +doing(greet(bo)) } )",
        "",
    ]))
    check(
        "§12",
        "defeat is rule-level and per-tick, so an undeclared act loses its fallback too",
        m3.holds(kb3.term("likely(greet(bo))")) is None,
    )
    m4, kb4 = plan("rule <wave> = implies( { +at(work) }, { +doing(greet(bo)) } )" + chr(10))
    check(
        "§15",
        "...which it keeps when nothing overrides -- so the check is about defeat, not the act",
        m4.holds(kb4.term("likely(greet(bo))")) == PLUS,
    )

    # So there are two intents and one relation could not carry both.
    # `overrides` is right when two rules are rival answers to ONE situation --
    # `overrides(<why>, <boil>)` defeats a rule that shares no evidence with it
    # at all, and must. `supersedes` is right when they are rival answers to each
    # of SEVERAL, and defeats only the applications triggered by the same
    # evidence. Rows, not branches.
    m5, kb5 = plan(chr(10).join([
        "fact supersedes(<outcome>, <assert-act>)",
        "rule <wave> = implies( { +at(work) }, { +doing(greet(bo)) } )",
        "",
    ]))
    check(
        "§12",
        "`supersedes` defeats per CASE: the declared act is replaced by its outcome",
        m5.holds(kb5.term("likely(inside(work))")) == PLUS
        and m5.holds(kb5.term("likely(travel(work))")) is None,
    )
    check(
        "§12",
        "...and the undeclared act in the same step keeps its fallback -- which `overrides` could not",
        m5.holds(kb5.term("likely(greet(bo))")) == PLUS,
    )


def an_agent_that_can_stop() -> None:
    """The design had one way to be over -- running out of work -- and that is
    **exhaustion**, not satisfaction (§19).

    It is why recall could be measured and could not pay. An ideal table reached
    a goal in 8 ticks instead of 734 and saved nothing at all, because the loop
    went to quiescence and did every domain anyway. Narrowing changes the ORDER
    in which everything is done, not how much is done.

    So: `enough(x)` -- *there is nothing more worth doing about x*. A claim, so a
    rule's to make, because *worth* is a judgement and §4 puts judgements in data.
    The loop's whole part is to read it and stop, and to deposit the smallest
    unarguable record of having done so (`stopped(<seat>, x)`), which is §17's
    treatment for `arrived`, `emitted`, `left` and `quiet` arriving a fifth time.
    """
    from .text import load

    chain = chr(10).join([
        "rule <a> = implies( { +p(?x) }, { +q(?x) } )",
        "rule <b> = implies( { +q(?x) }, { +r(?x) } )",
        "rule <far> = implies( { +q(?x) }, { +far(?x) } )",
        "rule <far2> = implies( { +far(?x) }, { +far2(?x) } )",
        "fact +p(a)",
        "",
    ])
    stop = chr(10).join([
        "rule <done> = implies( { +r(?x) }, { +enough(r(?x)) } )",
        "fact standing(<done>)",
        "",
    ])

    def go(src):
        m = Machine()
        kb = load(m, src)
        steps = m.run(limit=200)
        return m, kb, steps

    m0, kb0, s0 = go(chain)
    check("§19", "with nothing claiming enough, the loop still runs to quiescence -- "
          "the default is unchanged, which is what makes stopping a claim",
          s0[-1].state == "quiescent" and m0.holds(kb0.term("far2(a)")) == PLUS)

    m1, kb1, s1 = go(chain + stop)
    check("§19", "a rule can say when there is nothing more worth doing, and the loop stops",
          s1[-1].state == "stopped")
    check("§19", "and it stopped SHORT -- work the corpus could have done was not done",
          m1.holds(kb1.term("r(a)")) == PLUS and m1.holds(kb1.term("far2(a)")) is None
          and len(s1) < len(s0))

    # *Why did you stop?* has to have an answer, or stopping is the fourth silent
    # decline (§5) -- which is the criterion §2 calls not-lossy.
    seat = m1.focus.seat.node
    check("§19", "the stop is on the record, and it names what made here over",
          m1.holds(kb1.term("stopped")) is None
          and any(m1.g.show(n).startswith("stopped(") and "r(a)" in m1.g.show(n)
                  for n in m1.g.instances_of(m1.STOPPED)))

    # It is NOT `quiet`, and this is the finding rather than a tidiness point.
    # `<give-up>` asks its verdict at `quiet`, and `blocked` claims that no rule
    # fits -- an aggregate over a FINISHED search. A search that stopped because
    # it was satisfied has not finished, so reporting the goals it never reached
    # as blocked would be exactly the unsoundness `_widen` exists to prevent,
    # arriving from a second side.
    check("§19", "a satisfied search is not a finished one: stopping writes no `quiet`, "
          "so nothing downstream reads it as *no rule fits*",
          m1.widenings == 0 and not any(
              m1.holds(n) == PLUS for n in m1.g.instances_of(m1.QUIET)))

    # Inside a hypothesis, `enough` ends the BRANCH and not the run -- through the
    # door that already existed. This is *when is a plan settled* and *when is a
    # woken rule done* getting their local answer for free, because a frame is
    # already the unit that can be over.
    branch = chr(10).join([
        "rule <cross> = implies( { +likely(?p) }, { +suppose(?p, likely) } )",
        "rule <a> = implies( { +p(?x) }, { +q(?x) } )",
        "rule <b> = implies( { +q(?x) }, { +far(?x) } )",
        "fact +likely(p(a))",
        "",
    ])
    says_done = "rule <done> = implies( { +q(?x) }, { +enough(q(?x)) } )" + chr(10)
    m2, kb2, s2 = go(branch)
    m3, kb3, s3 = go(branch + says_done + "fact standing(<done>)" + chr(10))
    check("§19", "enough inside a hypothesis ends the BRANCH: work the branch had left "
          "is not done, and what it did conclude still crosses out wrapped",
          m2.holds(kb2.term("likely(far(a))")) == PLUS
          and m3.holds(kb3.term("likely(far(a))")) is None
          and m3.holds(kb3.term("likely(q(a))")) == PLUS)
    check("§19", "...and not the run: the frame is left and the loop goes on to quiesce, "
          "so *is this plan settled* gets its answer at the door that already existed",
          any(s.state == "supposed" for s in s3) and s3[-1].state == "quiescent"
          and any(m3.holds(n) == PLUS for n in m3.g.instances_of(m3.LEFT)))

    # §16's ordering trap, arriving a third time and deciding a design again.
    # Reading `enough` at the top of the tick is necessary and not sufficient:
    # the rule that CONCLUDES it competes like any other, so an ordinary rule
    # authored earlier takes one more step first. Being careful has to come
    # before the move it is about, and `standing` is what says so.
    #
    # > **Stopping is only as prompt as the recall and arbitration of the rule
    # > that says stop.** That is why the third carve-out below is not a tidiness
    # > point: a cap that can drop the rule is a cap that can defer stopping
    # > indefinitely.
    m4, kb4, _ = go(branch + says_done)
    check("§19", "and an unmarked stop rule stops LATE -- it is one competitor among "
          "many, so the branch takes another step before it ends",
          m4.holds(kb4.term("likely(far(a))")) == PLUS)


def no_goal_is_dropped_silently() -> None:
    """An agent that can stop can stop on something it was asked for, and the
    first version of `enough` did exactly that -- silently (§19).

    Measured: with a stop rule and two goals, the run ended with the second
    neither achieved nor blocked nor pursued, and nothing anywhere recording that
    it had been open. The stop was on the record; the abandonment was not.

    The repair is a **veto**, and the argument is §19's own, transferred:

    > Recall may be incomplete about what to do. It may not be incomplete about
    > what you must not do -- or about a goal it is dropping.

    A convention every corpus must remember is the kind this design keeps finding
    it has lost, so this is not the rule a well-written corpus would have written.
    It is machinery at one decision, the third of exactly three that all make the
    same move -- **escalate before believing a decline**: `_widen` at a dry
    shortlist, `_forbid` at a write, this at a stop.
    """
    from .text import load

    world = [
        "rule <a> = implies( { +p(?x) }, { +q(?x) } )",
        "rule <b> = implies( { +q(?x) }, { +s(?x) } )",
        "rule <done> = implies( { +q(?x) }, { +enough(q(?x)) } )",
        "fact standing(<done>)",
        "fact +p(a)",
        "fact +goal(q(a))",
    ]

    def go(lines, **kw):
        m = Machine()
        for name in kw.pop("actuators", ()):
            m.actuator(name)
        kb = load(m, chr(10).join(lines) + chr(10))
        return m, kb, m.run(limit=400)

    m0, kb0, s0 = go(world)
    check("§19", "with every goal achieved the veto costs nothing -- the agent stops, "
          "which is what keeps the saving in the case the saving was measured on",
          s0[-1].state == "stopped" and m0.holds(kb0.term("open(q(a))")) is None)

    # ...and with one still outstanding it does not stop, and says which.
    m1, kb1, s1 = go(world + ["fact +goal(s(a))"])
    check("§19", "a stop with a goal still open is not a stop: the veto refuses it and "
          "deposits which goal, so nothing is dropped in silence",
          m1.holds(kb1.term("open(s(a))")) == PLUS and s1[-1].state != "stopped")
    check("§19", "and the goal is then actually reached -- an outstanding goal OUTRANKS "
          "an `enough`, so the agent finishes the only way that was ever a claim",
          m1.holds(kb1.term("s(a)")) == PLUS and s1[-1].state == "quiescent")

    # The veto hands the loop back rather than costing it a tick. Reacting to an
    # open goal is ordinary reasoning of whatever length it takes, and an `enough`
    # consulted again next tick would cut it off after one -- which is what the
    # first version did, and why the diagnosis below never used to appear.
    blocked = [
        "rule <boil> = implies( { +heat(?w), +water(?w) }, { +boiling(?w) } )",
        "rule <ask> = implies( { +open(?w), +blocked(?w) }, { +doing(ask(?w)) } )",
        "fact standing(<ask>)",
        "rule <trust> = implies( { +says(?c, ?p, plus) }, { +?p } )",
        "fact +water(kettle)",  # ...and nothing anywhere concludes a `heat`
        "fact +goal(boiling(kettle))",
    ]
    m2, kb2, _ = go(world + blocked, actuators=("voice",))
    check("§19", "an open goal is DIAGNOSED and not merely noted -- and by `<give-up>`, "
          "which was already there, because outranking an `enough` means quiescence "
          "still happens and `quiet` is still the occasion",
          m2.holds(kb2.term("blocked(heat(kettle))")) == PLUS)

    # What the diagnosis is for. Where a question goes is a fact about a
    # deployment, so the reaction is a corpus rule and not bundled -- but it has
    # to be *possible*, and the boundary is what makes it so. Note which node it
    # asked about: not the goal it was given, but the precise subgoal backward
    # reading found it was missing. Nothing arranged that.
    check("§19", "so the agent can ask -- and it asks for exactly what it lacked, which "
          "backward reading worked out and no rule here named",
          [m2.g.show(n) for n in m2.emitted] == ["ask(heat(kettle))"])

    # And the run ends, because a question is not work. The user answers on an
    # ordinary channel, and resumption needs nothing: `<intake>` was always there.
    user = m2.channels.open("user")
    m2.channels.deliver(user, kb2.term("heat(kettle)"))
    s3 = m2.run(limit=400)
    check("§19", "the loop can end on a question and a later utterance resumes it -- "
          "an arrival is an ordinary write, so nothing was waiting and nothing polled",
          m2.holds(kb2.term("boiling(kettle)")) == PLUS and len(s3) < 10)


def experience_is_offline() -> None:
    """*Which rules earned the outcome?* -- asked of a finished episode (§19).

    Learning is offline because credit needs the outcome and the outcome is not
    known until the episode ends. It needs **no new bookkeeping**: R5 already
    licenses every derived entry with `applied(<R>)`, because the trail is
    load-bearing for §12's weakest link, so walking back from what was achieved
    reaches the rules that produced it and only those.
    """
    from .text import load

    # Two ways to get water, and the agent only needs one of them.
    kettle = chr(10).join([
        "rule <boil> = implies( { +heat(?a, ?w), +water(?w) }, { +boiling(?w) } )",
        "rule <pour> = implies( { +tap(?t), +under(?w, ?t) }, { +water(?w) } )",
        "rule <fill> = implies( { +jug(?j), +near(?w, ?j) }, { +water(?w) } )",
        # ...and one that runs, concludes, and contributes nothing. Without it
        # this fixture cannot tell a credit pass from a list of what applied --
        # `<fill>` never wins arbitration, so ANY scheme excludes it, and the
        # check below read as discrimination while testing something else.
        "rule <idle> = implies( { +jug(?j) }, { +rinsed(?j) } )",
        "fact +tap(sink)", "fact +under(kettle, sink)",
        "fact +jug(jug1)", "fact +near(kettle, jug1)",
        "fact +heat(anna, kettle)",
        "fact +goal(boiling(kettle))",
        "",
    ])
    m = Machine()
    kb = load(m, kettle)
    m.run(limit=2000)
    earned = {r.name for r, _ in m.review()}

    check("§19", "the trail can say which rules earned the outcome, with no bookkeeping "
          "R5 was not already keeping for the weakest link",
          {"boil", "pour"} <= earned)
    # The discriminating half, and it needs a rule that RAN: a pass that credited
    # everything applied would look identical without one.
    check("§19", "and it credits what was on the support of the outcome, not what "
          "merely ran -- `<idle>` applied, concluded, and earned nothing",
          m.holds(kb.term("rinsed(jug1)")) == PLUS and "idle" not in earned)
    check("§19", "nor what was merely available: `<fill>` would have served too",
          "fill" not in earned)
    check("§19", "an episode that achieved nothing credits nothing -- and does not "
          "blame either, since a failed episode may have been an impossible one",
          not Machine().review())

    # What is deposited is a fact about the trail; what it is worth is a claim,
    # so the row an agent takes forward is ordinary readable corpus text.
    rows = m.learned()
    check("§19", "what it learned is a corpus, not a weight: readable, editable, and "
          "deniable, which is the only way being wrong in recall stays recoverable",
          any(r.startswith("fact prefer(<boil>, boiling,") for r in rows))

    # The key is the goal's RELATION, and that is the whole of what transfers.
    m2 = Machine()
    kb2 = load(m2, kettle + chr(10).join(rows) + chr(10))
    m2.recall_budget = 3
    m2.run(limit=2000)
    check("§19", "a second episode reads it back and reaches the same conclusion",
          m2.holds(kb2.term("boiling(kettle)")) == PLUS)
    # The key is the whole of what transfers, so it is checked as a property of
    # the row rather than inferred from a run that would have succeeded anyway.
    check("§19", "and the key GENERALISES: every row is keyed on a relation, so what "
          "the agent learned about `boiling(kettle)` is available for `boiling(pot)`",
          rows and all("(<" in r and ", " in r for r in rows)
          and not any("(" in r.split(", ")[1] for r in rows))

    # ...and the honest half. §13's blocker is measured, not assumed: it is why
    # an exact table buys nothing, and why this cannot yet be shown to pay.
    import ugm.machine as MM
    from .workload import corpus, stopping

    tally = {"arb": 0, "apparatus": 0}
    orig = MM.arbitrate

    def spy(rules, applications, rank):
        if applications:
            tally["arb"] += 1
            if min(rank(a.rule) for a in applications)[0] == 0:
                tally["apparatus"] += 1
        return orig(rules, applications, rank)

    MM.arbitrate = spy
    try:
        m3 = Machine()
        load(m3, corpus(4, 4, 0, True) + stopping(4))
        m3.recall_budget = 4
        m3.run(limit=9999)
    finally:
        MM.arbitrate = orig
    check("§19", "and what stops it paying is measured: the apparatus wins most of the "
          "agent's choices, so a table about domain rules has almost nothing to decide",
          tally["apparatus"] * 4 > tally["arb"] * 3)


def a_root_goal_is_askable() -> None:
    """§6's *a root goal is never checked*, closed the way `blocked` was (§12).

    *A root goal is a `goal(?w)` with **no** `subgoal(?p, ?w)`* is a negative
    existential, and §12 says a `-` member cannot say it -- a `-` member says
    *an entry denies this*, never *for no `?p`*. That is the same shape as
    `blocked`, so it gets the same treatment: a REQUEST the machinery answers by
    looking, depositing only when the answer is yes.

    What it unblocks is one line no corpus could write before -- *what I was
    ASKED for holds, so I am done* -- where the version without `rooted` stops at
    whatever subgoal backward reading happened to satisfy first.
    """
    from .text import load

    m = Machine()
    kb = load(m, chr(10).join([
        "rule <boil> = implies( { +heat(?a, ?w), +water(?w) }, { +boiling(?w) } )",
        "rule <ask-root> = implies( { +goal(?w) }, { +root(?w) } )",
        "fact standing(<ask-root>)",
        "rule <done> = implies( { +goal(?w), +rooted(?w), +?w }, { +enough(?w) } )",
        "fact standing(<done>)",
        "fact +heat(anna, kettle)", "fact +water(kettle)",
        "fact +goal(boiling(kettle))", ""]))
    steps = m.run(limit=400)

    check("§6", "what the agent was asked for is askable: a goal nothing made a "
          "subgoal of answers `rooted`",
          m.holds(kb.term("rooted(boiling(kettle))")) == PLUS)
    # The discrimination, and it needs a subgoal that HOLDS -- one that did not
    # would prove nothing, since an unsatisfied subgoal could never stop anything.
    subs = [n for n in m.g.instances_of(m.SUBGOAL) if m.holds(n) == PLUS]
    held = [m.g.member(n, 1) for n in subs
            if not m.g.has_var(m.g.member(n, 1))
            and m.holds(m.g.member(n, 1)) == PLUS]
    check("§12", "...and one backward reading made up on its own does NOT, even "
          "though it holds -- which is the whole distinction",
          bool(held) and all(m.holds(m.g.rel(m.ROOTED, w)) is None for w in held))
    check("§17", "the machinery answers only when the answer is yes: a negative "
          "existential of its own would be the thing it exists to avoid",
          not any(m.g.show(m.g.relation_of(n)) == "rooted"
                  and m.holds(n) == MINUS for n in m.g.instances_of(m.ROOTED)))
    check("§15", "so the general stop rule is writable and the agent is SATISFIED "
          "rather than exhausted",
          steps[-1].state == "stopped"
          and m.holds(kb.term("boiling(kettle)")) == PLUS)

    # -- and what `rooted` does NOT unblock, which is the finding ----------
    #
    # ⚠⚠⚠ Checking a root goal for SATISFACTION needs one more thing, and it is
    # not rootedness. With `rooted` in hand a corpus can ask -- `{+goal(?w),
    # +rooted(?w)} => {+check(?w, ?w)}`, the goal as its own plan, which needs no
    # engine change because a root goal binds nothing -- and the whole chain
    # fires: `root`, `rooted`, `check`. `achieved` still does not appear.
    #
    # The reason is §6's OTHER item: **a request can only be made once.** The
    # check is asked the moment the goal appears, the state is scanned then, and
    # re-concluding `+check(w, w)` changes nothing, so quiescence drops it. A
    # goal satisfied three ticks later is never looked at again.
    #
    # Measured as a contrast pair rather than asserted, because the two cases
    # differ only in WHEN the goal became true -- which is the whole claim.
    rc = [
        "rule <ask-root> = implies( { +goal(?w) }, { +root(?w) } )",
        "fact standing(<ask-root>)",
        "rule <check-root> = implies( { +goal(?w), +rooted(?w) }, { +check(?w, ?w) } )",
        "fact standing(<check-root>)",
    ]
    now = Machine()
    kb_now = load(now, chr(10).join(["fact +q(x)"] + rc + ["fact +goal(q(x))", ""]))
    now.run(limit=400)
    later = Machine()
    kb_later = load(later, chr(10).join(
        ["rule <r> = implies( { +p(x) }, { +q(x) } )", "fact +p(x)"]
        + rc + ["fact +goal(q(x))", ""]))
    later.run(limit=400)

    check("§6", "a root goal CAN be checked once it is askable -- the goal as its "
          "own plan, and no engine change, because a root goal binds nothing",
          now.holds(kb_now.term("achieved(q(x))")) == PLUS)
    check("§6", "⚠ ...but only if it already held when the question was asked: with "
          "no re-ask a goal reached LATER is never looked at again, because a "
          "request can be made once. `rooted` was necessary and is not sufficient",
          later.holds(kb_later.term("q(x)")) == PLUS
          and later.holds(kb_later.term("achieved(q(x))")) is None)
    # ...and the same fixture with a re-ask is `a_request_can_be_re_asked` below,
    # which is why this one stays: it is now the CONTROL for that, rather than an
    # open item. The two runs differ by two corpus lines and nothing else.


def a_request_can_be_re_asked() -> None:
    """§6's *a request can only be made once*, and §21's first of the last two hats.

    ⭐⭐⭐ **The request never needed to be fresh. The ENTRY did.** §10's two
    indices exist so that *the same claim, later* is expressible, and `deposit`
    has always taken a second entry about a proposition it has seen. What forbids
    a re-ask is `_would_change` -- quiescence -- and quiescence forbids it of a
    RULE. The machinery re-delivering a request is not a rule restating one, so
    the prohibition never covered this act.

    So the whole of it is a wrapper and one write:

        again(<request>, <occasion>)

    ordinary node, different per occasion, so concluding it is a step; and what
    the machinery does with it is write the wrapped request through the gate,
    where every answerer already listens.
    """
    from .text import load

    ROOT = [
        "rule <ask-root> = implies( { +goal(?w) }, { +root(?w) } )",
        "fact standing(<ask-root>)",
        "rule <check-root> = implies( { +goal(?w), +rooted(?w) }, { +check(?w, ?w) } )",
        "fact standing(<check-root>)",
    ]
    WORLD = ["rule <r> = implies( { +p(x) }, { +q(x) } )", "fact +p(x)"]

    def run(recheck, limit=300):
        m = Machine()
        kb = load(m, chr(10).join(
            WORLD + ROOT + recheck + ["fact +goal(q(x))", ""]))
        return m, kb, m.run(limit=limit)

    def recheck(connective):
        return [
            f"rule <recheck> = {connective}( "
            "{ +unmet(?w, ?w), +quiet(?m) }, { +again(check(?w, ?w), ?m) } )",
            "fact standing(<recheck>)",
        ]

    # ⚠ Count the GROUND ones. `instances_of` returns the rule's own consequent
    # pattern too -- `again(check(?w, ?w), ?m)` is an instance of the relation and
    # holds nothing -- so a raw count reads one too many, which is what the first
    # version of this check did.
    minted = lambda mm: sum(1 for n in mm.g.instances_of(mm.AGAIN) if mm.holds(n) == PLUS)

    m, kb, steps = run(recheck("implies"))
    check("§6", "a goal satisfied AFTER the question was asked is noticed, once "
          "the question can be asked again -- the exact contrast pair "
          "`a_root_goal_is_askable` measures the other half of",
          m.holds(kb.term("q(x)")) == PLUS
          and m.holds(kb.term("achieved(q(x))")) == PLUS)
    check("§21", "...and the occasion is on the record, so *why did you ask that "
          "twice* has an answer -- which is the whole of why it is a member and "
          "not a counter",
          any(m.holds(n) == PLUS and m.g.members(n)[1] in
              [x.node for x in m.chain.moments]
              for n in m.g.instances_of(m.AGAIN)))
    check("§6", "it costs one tick, because a re-ask is one application and one "
          "write and not a second search",
          len(steps) == 16)

    # ⭐⭐ And it is bound the way a TOOL is, not the way the other eight
    # write-time hooks are -- so a corpus can see it and retire it. §21's *the
    # apparatus does not eat its own cooking* had been true of every one of
    # them: `answers(<M>, ask)` shipped with exactly zero apparatus users.
    #
    # ⚠ The criterion for which hooks may follow, because it is not all of them:
    # **a capability whose absence is the status quo ante is safe to retire.**
    # Deny this and each question is asked once, which is what the agent did
    # before and was sound. Deny `_fit` and backward reading stops, which is
    # §19's carve-out and a different argument.
    off = Machine()
    kb_off = load(off, chr(10).join(
        WORLD + ROOT + recheck("implies")
        + ["fact -answers(<re-ask>, again)", "fact +goal(q(x))", ""]))
    off.run(limit=300)
    check("§21", "re-asking is bound by a FACT and not by a Python line: one "
          "corpus line retires it, and the agent is back to asking once",
          off.holds(kb_off.term("q(x)")) == PLUS
          and off.holds(kb_off.term("achieved(q(x))")) is None
          and m.holds(kb.term("answers(<re-ask>, again)")) == PLUS)

    # ⚠⚠⚠ **WHEN may a request be re-asked, and it is not free choice.** An
    # occasion the re-asking itself can produce warrants the next re-ask, which
    # produces the occasion after that. Here the author picks that trap or avoids
    # it with ONE WORD, and neither reading of the word is about re-asking:
    #
    #   implies  the re-ask is part of this moment       -- `quiet` is once per
    #                                                       seat, and the seat
    #                                                       does not move
    #   causes   the re-ask moves the world on           -- so the seat moves, so
    #                                                       a fresh `quiet` is
    #                                                       written, so re-ask
    #
    # Measured rather than reasoned about, because I expected the first to run
    # away too and it does not.
    slow, _, slow_steps = run(recheck("causes"))
    check("§21", "⚠⚠⚠ an occasion the re-asking can itself CREATE warrants a "
          "re-ask forever: the same rule with `causes` advances the seat, `quiet` "
          "is once per seat, and the agent asks the same question 100+ times",
          len(slow_steps) >= 300 and minted(slow) > 50)
    check("§6", "...where the `implies` version asks exactly once more and stops -- "
          "so the criterion is *an occasion warrants a re-ask only if re-asking "
          "cannot produce one*, and it is the connective that decides",
          minted(m) == 1 and steps[-1].state == "quiescent")

    # ⭐⭐ It is one write, so it reaches every answerer -- and a TOOL is an
    # answerer. Nothing in `_answer` knows re-asking exists, which is the
    # composability criterion (§2) rather than a convenience: re-asking and
    # answering were designed against each other by nobody.
    calls: List[int] = []
    scope: List = []

    def oracle(machine, frame, e):
        calls.append(1)
        # ⚠ `scope[0].atom`, not `machine.g.atom`. An answer built outside the
        # loader's table is a node no rule can name, and the first version of
        # this check built one -- so the tool answered, the record landed, and
        # `kb.term(...)` asking about it resolved a TWIN that held nothing. The
        # trap `ugm.tools` records, in a check written after it was recorded.
        return scope[0].atom("yes") if len(calls) > 1 else None

    tm = Machine()
    tkb = load(tm, chr(10).join([
        "rule <ask> = implies( { +wondering(?x) }, { +guess(?x) } )",
        "fact standing(<ask>)",
        "rule <retry> = implies( { +guess(?x), +quiet(?m) }, { +again(guess(?x), ?m) } )",
        "fact standing(<retry>)",
        "fact +wondering(vessel)", ""]))
    scope.append(tkb)
    tkb.answerer("oracle", "guess", oracle)
    tm.run(limit=100)
    check("§21", "a TOOL is re-askable by the same line, and `_answer` knows "
          "nothing about it: a stub that declines the first time answers the "
          "second",
          len(calls) == 2
          # `<oracle>`, because a tool's name is in the namespace of STATEMENTS
          # -- the same table as a rule's, so the two cannot collide. Written
          # bare, `oracle` resolves as an ordinary atom and the question is about
          # a twin: the same trap, one namespace along.
          and tm.holds(tkb.term("answered(<oracle>, guess(vessel), yes)")) == PLUS)

    # ⭐⭐ And the generic wrapper turns out to be RETRY, which §21 wanted as a
    # corpus rule. `_dispatch` dedups on the ENTRY node rather than on the
    # proposition, so a second entry crosses the boundary a second time -- which
    # was always the right dedup and had nothing to retry with until now.
    am = Machine()
    am.actuator("hands")
    load(am, chr(10).join([
        "rule <try> = implies( { +need_open(?d) }, { +doing(open(?d)) } )",
        "fact standing(<try>)",
        "rule <retry> = implies( { +doing(open(?d)), +quiet(?m), +stuck(?d) },"
        "                        { +again(doing(open(?d)), ?m) } )",
        "fact standing(<retry>)",
        "fact +need_open(door)", "fact +stuck(door)", ""]))
    am.run(limit=100)
    check("§15", "an ACT re-asked is an act done again, so retry is a corpus rule "
          "and not a mechanism -- the act leaves the agent twice",
          [am.g.show(x) for x in am.emitted] == ["open(door)", "open(door)"])
    # The control for it, and it is the one that can fail: without the occasion
    # the retry rule needs, the act leaves once. A fixture where everything is
    # retried cannot tell retrying from acting.
    cm = Machine()
    cm.actuator("hands")
    load(cm, chr(10).join([
        "rule <try> = implies( { +need_open(?d) }, { +doing(open(?d)) } )",
        "fact standing(<try>)",
        "rule <retry> = implies( { +doing(open(?d)), +quiet(?m), +stuck(?d) },"
        "                        { +again(doing(open(?d)), ?m) } )",
        "fact standing(<retry>)",
        "fact +need_open(door)", ""]))
    cm.run(limit=100)
    check("§15", "...and the door that is not stuck is opened once, so the fixture "
          "can fail",
          [cm.g.show(x) for x in cm.emitted] == ["open(door)"])


def a_domain_can_be_taken_out_of_mind() -> None:
    """§19's recall, for FACTS -- the half it never had.

    The agent has always narrowed which **rules** come to mind: `dormant` until
    something claims `due`. It has never narrowed which **facts** do. The user's
    proposal, and it needs no new vocabulary -- the same relation, a second kind
    of thing, which is the design's own test that a thing belongs (rows, not
    branches).

    A domain is a **channel**: §13 already says the knowledge base is one, and
    every loaded fact is stamped with its source, so *which domain is this from*
    was already recorded and never read.

    Measured on three domains with a goal in one: 22.6s over 600 ticks with all
    of it in mind, 1.6s over 198 with two domains dormant -- **14.5x, and the
    identical 196 conclusions.** It cuts both factors at once, which is why it
    beats either cache built before it.

    ⚠ Unloading is safe to be wrong about (worst case the domain comes back),
    which is exactly why it may be an ordinary defeasible rule. §19's ESCALATION
    -- reaching for more when the search comes up dry -- may not be, and is not
    built here: §21.
    """
    from .text import load

    corpus = [
        "rule <r> = implies( { +owes(?c, ?n), +overdue(?c) }, { +chase(?c) } )",
        "rule <s> = implies( { +late(?c, ?p) }, { +apologise(?c) } )",
    ]
    billing = ["fact +owes(acme, 100)", "fact +overdue(acme)"]
    shipping = ["fact +late(acme, milan)"]

    def run(dormant):
        m = Machine()
        kb = load(m, chr(10).join(corpus + [""]), scope="world", domain="rules")
        load(m, chr(10).join(billing + [""]), scope="world", domain="billing")
        load(m, chr(10).join(shipping + [""]), scope="world", domain="shipping")
        if dormant:
            load(m, chr(10).join([f"fact dormant({d})" for d in dormant] + [""]),
                 scope="world", domain="ctl")
        m.run(limit=200)
        return m, kb

    m0, kb0 = run(None)
    check("§19", "with everything in mind the agent draws both domains' conclusions",
          m0.holds(kb0.term("chase(acme)")) == PLUS
          and m0.holds(kb0.term("apologise(acme)")) == PLUS)

    m1, kb1 = run(["shipping"])
    check("§19", "a domain the goal does not need can be taken out of mind: its "
          "facts stop driving inference, and the other domain's conclusion is "
          "unchanged -- which is what makes unloading safe to be wrong about",
          m1.holds(kb1.term("chase(acme)")) == PLUS
          and m1.holds(kb1.term("apologise(acme)")) is None)

    # ⭐⭐⭐ **Out of mind is not untrue, and the difference is the whole design.**
    # The fact is still in the chain, still stamped with where it came from,
    # still on any trail that used it -- `holds` answers, and `why` would. What
    # dormancy takes away is ATTENTION, never the record. Unloading from the
    # chain instead would break §12's weakest link and put `why()` in the dark,
    # which is the one thing this may not cost.
    check("§4", "...and the unloaded fact is still TRUE and still attributable -- "
          "dormancy takes attention, not the record",
          m1.holds(kb1.term("late(acme, milan)")) == PLUS)

    # ...and the one that must fail: take away what it DOES need, and it stops
    # concluding. A fixture where unloading never costs anything cannot tell
    # narrowing from doing nothing.
    m2, kb2 = run(["billing"])
    check("§19", "...and taking away a domain it DOES need stops the conclusion, "
          "so the fixture can fail",
          m2.holds(kb2.term("chase(acme)")) is None)

    # ⚠⚠ **And facts that ARRIVE while the agent is running**, which is the case
    # on-demand loading actually produces: the state is kept across ticks, so a
    # dormant domain has to be filtered on the incremental path as well as the
    # rebuild. Kill-probed separately -- with only the rebuild filter in place,
    # nothing here failed, because no fixture loaded anything mid-run.
    m5 = Machine()
    kb5 = load(m5, chr(10).join(corpus + [""]), scope="world", domain="rules")
    # The domain exists BEFORE it is made dormant, so what is in mind does not
    # change when the second fact arrives -- which is what keeps the kept state
    # in play instead of rebuilding it. A fixture where the domain first appears
    # mid-run forces a rebuild and cannot see this at all: measured, killing the
    # incremental filter failed nothing until this was written the other way.
    load(m5, chr(10).join(shipping + [""]), scope="world", domain="shipping")
    load(m5, chr(10).join(["fact dormant(shipping)", ""]),
         scope="world", domain="ctl")
    m5.run(limit=100)                       # ...quiesce, so the state is kept
    load(m5, "fact +late(acme, roma)" + chr(10), scope="world", domain="shipping")
    m5.run(limit=100)
    check("§19", "a fact ARRIVING into a dormant domain does not come to mind "
          "either -- the kept state and the delta that feeds matching are "
          "filtered alike, and filtering only the first let it match once",
          m5.holds(kb5.term("late(acme, roma)")) == PLUS
          and m5.holds(kb5.term("apologise(acme)")) is None)

    # ⚠⚠⚠ ...and the KEPT STATE's own filter needs a JOIN to be visible at all.
    # With a one-member rule the dormant fact is always the pivot, so the delta
    # filter above already excludes it and killing the state's filter changes
    # nothing. A second member is drawn from the full state instead -- so a
    # dormant fact that slipped into the kept state matches there. Two filters,
    # two paths, and only a two-member rule can tell them apart.
    m6 = Machine()
    kb6 = load(m6, chr(10).join([
        "rule <t> = implies( { +late(?c, ?p), +vip(?c) }, { +sorry(?c) } )", ""]),
        scope="w6", domain="rules")
    load(m6, "fact +anchor(x)" + chr(10), scope="w6", domain="shipping")
    load(m6, "fact dormant(shipping)" + chr(10), scope="w6", domain="ctl")
    m6.run(limit=100)                                  # the kept state is built
    load(m6, "fact +late(acme, roma)" + chr(10), scope="w6", domain="shipping")
    m6.run(limit=100)                                  # ...arrives, must be filtered
    load(m6, "fact +vip(acme)" + chr(10), scope="w6", domain="crm")
    m6.run(limit=100)                                  # ...pivots here, joins the above
    check("§19", "a dormant fact that arrived earlier is not available to JOIN "
          "against a live one later -- the kept state is filtered too, not only "
          "the delta",
          m6.holds(kb6.term("vip(acme)")) == PLUS
          and m6.holds(kb6.term("sorry(acme)")) is None)

    # `due` wakes it again, exactly as it does for a rule -- same relation, same
    # meaning, second kind of thing.
    m3 = Machine()
    kb3 = load(m3, chr(10).join(corpus + [""]), scope="world", domain="rules")
    load(m3, chr(10).join(billing + [""]), scope="world", domain="billing")
    load(m3, chr(10).join(
        ["fact dormant(billing)", "fact due(billing)", ""]),
        scope="world", domain="ctl")
    m3.run(limit=200)
    check("§19", "...and `due` brings it back, the same pair that wakes a rule",
          m3.holds(kb3.term("chase(acme)")) == PLUS)

    # ⚠⚠⚠ Sharing NAMES and sharing PROVENANCE are different things, and tying
    # them together was the first version of this. Rules about billing must
    # resolve `owes` to the node the billing facts use -- one scope -- while not
    # being billing data, or unloading billing would unload the rules that read
    # it. Caught by the first fixture that needed both.
    m4 = Machine()
    r4 = load(m4, chr(10).join(corpus + [""]), scope="world", domain="rules")
    b4 = load(m4, chr(10).join(billing + [""]), scope="world", domain="billing")
    owes = m4.chain.resolve(b4.term("owes(acme, 100)"), m4.focus.topic, m4.focus.seat)
    check("§13", "a document declares its name table and its domain separately: "
          "one scope, so the rule and the fact mean the same `owes` -- two "
          "domains, so unloading the data does not unload the rules that read it",
          r4.atom("owes") == b4.atom("owes")
          and owes is not None
          and m4.g.show(owes.source) == "billing")


def a_hypothesis_can_be_re_entered() -> None:
    """The user's case: *explore a hypothesis, find you need something you do not
    have, go and get it, and finish the reasoning.*

    ⚠⚠⚠ It could not be done, and the block was one line with a reason true only
    while nothing changes: *supposing the same thing twice derives nothing new.*
    Measured -- explore `broken(pipe)`, want `wet(pipe)`, conclude nothing,
    discharge; then be told `wet(pipe)`, and the hypothesis is **never
    revisited**, not even when a corpus asks for it outright.

    ⭐ The answer is the one session resume gave: **re-enter, do not freeze.**
    Nothing is paused mid-flight -- the frame ran to quiescence and discharged
    honestly -- and what a corpus asks for is the supposition *again*, on the
    occasion of learning something. That is `again`'s own argument, so the
    licence already on the entry is the discriminator and nothing new is
    recorded to know it.

    ⚠ Note what is NOT claimed: this does not pause a half-explored hypothesis.
    A supposition still runs to quiescence inside and discharges. What it buys
    is that finding out more is a reason to think again.
    """
    from .text import load

    world = [
        "rule <s> = implies( { +odd(?x) }, { +suppose(broken(?x), likely) } )",
        "rule <c> = implies( { +broken(?x), +wet(?x) }, { +leaks(?x) } )",
        "rule <trust> = implies( { +says(user, ?p, plus) }, { +?p } )",
        "fact standing(<trust>)", "fact +odd(pipe)",
    ]
    redo = [
        "rule <redo> = implies( { +says(user, wet(?x), plus) },"
        "                       { +again(suppose(broken(?x), likely), ?x) } )",
        "fact standing(<redo>)",
    ]

    def run(with_redo):
        m = Machine()
        kb = load(m, chr(10).join(world + (redo if with_redo else []) + [""]),
                  scope="hy")
        m.run(limit=300)
        before = m.holds(kb.term("likely(leaks(pipe))"))
        kb.say("user", "wet(pipe)")
        steps = m.run(limit=300)
        return m, kb, before, steps

    m, kb, before, steps = run(True)
    check("§16", "the hypothesis concludes nothing while the fact is missing",
          before is None)
    check("§16", "⭐ ...and once the agent is told, it thinks again and finishes: "
          "finding something out is a reason to re-enter a hypothesis",
          m.holds(kb.term("likely(leaks(pipe))")) == PLUS)
    check("§15", "...and it terminates, for the reason re-asking does: one "
          "`again` node per occasion, so the same occasion asks once",
          steps[-1].state in ("quiescent", "stopped") and len(steps) < 300)

    # ⚠⚠⚠ And the re-ask criterion transfers whole: **an occasion warrants a
    # re-ask only if re-asking cannot produce one.** A corpus that re-supposes
    # on `left` -- the record of leaving a frame -- generates the occasion for
    # the next re-entry by re-entering, and never stops. Not a machinery
    # failure: the criterion is stated and unenforced, and this is an author
    # writing the `causes`-shaped mistake in a second place.
    away = Machine()
    load(away, chr(10).join([
        "rule <s> = implies( { +odd(?x) }, { +suppose(broken(?x), likely) } )",
        "rule <l> = implies( { +left(?f, ?a) },"
        "                    { +again(suppose(?a, likely), ?f) } )",
        "fact +odd(pipe)", ""]), scope="hy2")
    ran = away.run(limit=200)
    check("§21", "⚠ re-supposing on an occasion the re-entry itself creates does "
          "not terminate -- the same criterion as re-asking, in a second place",
          len(ran) == 200)

    # The control, and it is the whole claim: without the corpus asking, the
    # hypothesis stays unrevisited even though the fact is now known.
    c, kbc, _, _ = run(False)
    check("§16", "...where a corpus that does not ask gets no re-entry, even "
          "with the fact in hand -- the machinery does not decide this",
          c.holds(kbc.term("wet(pipe)")) == PLUS
          and c.holds(kbc.term("likely(leaks(pipe))")) is None)


def its_own_effort_is_reasonable_over() -> None:
    """§21's hidden state, for the counters -- and the user's reason is the right
    one: these should be **reasonable over**.

    An agent that reached past its shortlist, or was stopped by a bound, knows
    something about its own effort. That lived in Python counters, so no rule
    could ask.

    ⭐ **Events, not counts.** A count cannot be a fact here: `widened(2)` and
    `widened(3)` are different propositions and both would hold. §17's pattern
    was always the right one -- deposit the smallest unarguable record and let
    rules say what it means, as `quiet`, `left`, `stopped` and `emitted` do. So
    the claim is *this happened here*, deduped by reading the graph, and *how
    often* stays a question nobody has had to ask.

    ⚠⚠ `_enter`'s comment has said *each reports that it was hit rather than
    stopping silently (§13)* since it was written, and the report was
    `self.exhausted += 1`. **The code claimed a property it did not have.**
    """
    from .text import load

    chain = ["rule <a> = implies( { +p(?x) }, { +q(?x) } )",
             "rule <b> = implies( { +q(?x) }, { +r(?x) } )", "fact +p(a)"]

    wide = Machine(); load(wide, chr(10).join(chain + [""])); wide.run(limit=200)
    tight = Machine()
    load(tight, chr(10).join(chain + ["fact budget(1)", ""])); tight.run(limit=200)
    said = lambda m, rel: [n for n in m.g.instances_of(rel) if m.holds(n) == PLUS]
    check("§21", "reaching past a shortlist is on the record, not only in a "
          "counter", said(tight, tight.WIDENED) and not said(wide, wide.WIDENED))
    # ⚠ Counted as ENTRIES, not as nodes. `instances_of` returns propositions,
    # and three deposits of one proposition are one node -- so a node count
    # cannot see duplication at all, and the first version of this check could
    # not fail when the dedup was removed.
    deposits = sum(1 for mo in tight.chain.moments for e in mo.delta
                   if tight.g.relation_of(e.proposition) is tight.WIDENED)
    check("§17", "...as an event and not a count: three widenings at one seat are "
          "ONE claim deposited once, because restating is not revising",
          tight.widenings > 1 and deposits == 1)

    b2 = Machine()
    load(b2, chr(10).join([
        "rule <s> = implies( { +odd(?x) }, { +suppose(broken(?x), likely) } )",
        "fact +odd(pipe)", "fact hypotheses(0)", ""]))
    b2.run(limit=200)
    check("§13", "...and so does the other bound, by name",
          [b2.g.show(n) for n in
           [x for x in b2.g.instances_of(b2.BOUNDED) if b2.holds(x) == PLUS]]
          == ["bounded(hypotheses)"])

    # Reaching for a domain that was put out of mind is the same kind of record.
    esc = Machine()
    kb_e = load(esc, chr(10).join([
        "rule <r> = implies( { +owes(?c, ?n) }, { +chase(?c) } )", ""]),
        scope="eff", domain="rules")
    load(esc, "fact +owes(acme, 100)" + chr(10), scope="eff", domain="billing")
    load(esc, chr(10).join(
        ["fact dormant(billing)", "fact +goal(chase(acme))", ""]),
        scope="eff", domain="ctl")
    esc.run(limit=300)
    check("§19", "reaching for a domain out of mind is on the record too, so "
          "*I had to go and get that* is askable",
          esc.recoveries == 1
          and [n for n in esc.g.instances_of(esc.REACHED) if esc.holds(n) == PLUS]
          and esc.holds(kb_e.term("chase(acme)")) == PLUS)

    b = Machine()
    load(b, chr(10).join([
        "rule <s> = implies( { +odd(?x) }, { +suppose(broken(?x), likely) } )",
        "fact +odd(pipe)", "fact depth(0)", ""]))
    b.run(limit=200)
    check("§13", "⚠ a bound that was hit says WHICH one, where the code had "
          "claimed to report and only counted",
          [b.g.show(n) for n in said(b, b.BOUNDED)] == ["bounded(depth)"])

    # The point of all of it: a corpus can reason over the agent's own effort.
    act = Machine()
    act.actuator("out")
    load(act, chr(10).join(chain + [
        "fact budget(1)",
        "rule <patience> = implies( { +widened(?m) }, { +doing(ask(help)) } )",
        "fact standing(<patience>)", ""]))
    act.run(limit=200)
    check("§19", "⭐ so a rule can act on how hard the agent had to try -- *I had "
          "to reach for that, ask for help* is now a sentence a corpus can write",
          [act.g.show(x) for x in act.emitted] == ["ask(help)"])

    # ...and the control, so the fixture can fail: no reaching, no asking.
    calm = Machine()
    calm.actuator("out")
    load(calm, chr(10).join(chain + [
        "rule <patience> = implies( { +widened(?m) }, { +doing(ask(help)) } )",
        "fact standing(<patience>)", ""]))
    calm.run(limit=200)
    check("§19", "...and an agent that never had to reach does not ask",
          calm.emitted == [])


def the_knobs_are_claims() -> None:
    """§21's hidden state, for the knobs -- and the argument was already written.

    `tolerance` is a **fact** for a reason the design states out loud: *how
    careful am I being is a claim with a trail, and a rule can raise it before an
    irreversible step.* Three other knobs -- how many rules recall may propose,
    how deep a hypothesis may nest, how many may be open -- stayed Python
    fields, which made them the one kind of decision this design does not allow:
    one nobody can ask about or argue with.

    ⚠ The DEFAULT stays in Python, exactly as `tolerance`'s zero does. A default
    nobody has to choose is not a hidden decision; it is the absence of one.
    """
    from .text import load

    m = Machine()
    load(m, "fact +x(a)" + chr(10))
    check("§15", "with nothing said, the defaults hold and no constant was chosen",
          m._tolerance() == 0
          and m._knob(m.BUDGET, m.recall_budget) is None)

    c = Machine()
    load(c, chr(10).join([
        "fact tolerance(2)", "fact budget(3)", "fact depth(9)",
        "fact hypotheses(7)", ""]))
    check("§21", "⭐ a corpus can turn every one of them, so *how careful am I "
          "being* is answerable rather than compiled in",
          (c._tolerance(), c._knob(c.BUDGET, c.recall_budget),
           c._knob(c.DEPTH, c.max_depth),
           c._knob(c.HYPOTHESES, c.supposition_budget)) == (2, 3, 9, 7))

    # ...and it really steers: a budget written as a fact narrows recall, which
    # is what `m.recall_budget = 3` did from Python and nothing could argue with.
    chain = chr(10).join([
        "rule <a> = implies( { +p(?x) }, { +q(?x) } )",
        "rule <b> = implies( { +q(?x) }, { +r(?x) } )",
        "fact +p(a)", ""])
    wide = Machine(); load(wide, chain); wide.run(limit=400)
    tight = Machine(); load(tight, chain + "fact budget(1)" + chr(10))
    tight.run(limit=400)
    check("§19", "...and the fact steers the machinery: a budget written in the "
          "corpus makes recall narrow, and widening reports itself",
          wide.widenings == 0 and tight.widenings > 0)

    # ⚠ ...and it steers BOTH places the budget is read: whether to widen, and
    # how much of the shortlist to keep. Gated by comparing against the Python
    # field it replaces -- with only the first site reading the fact, the run
    # widens and never narrows, and the tick counts come apart. The `widenings`
    # check above could not see that.
    pyb = Machine(); load(pyb, chain); pyb.recall_budget = 1
    pysteps = pyb.run(limit=400)
    factb = Machine(); load(factb, chain + "fact budget(1)" + chr(10))
    factsteps = factb.run(limit=400)
    check("§19", "a budget written as a fact behaves exactly as the Python field "
          "it replaces -- same ticks, same widenings, both places it is read",
          (len(pysteps), pyb.widenings) == (len(factsteps), factb.widenings))

    # ...and the other two steer as well. ⚠ Checking that they READ was not
    # enough: with only the reader in place, mutating the depth bound back to
    # its Python field failed nothing. A knob that is read and not obeyed is
    # the same defect wearing the fix's clothes.
    supposing = [
        "rule <s> = implies( { +odd(?x) }, { +suppose(broken(?x), likely) } )",
        "rule <c> = implies( { +broken(?x) }, { +leaks(?x) } )",
        "fact +odd(pipe)", "",
    ]
    free = Machine(); kb_f = load(free, chr(10).join(supposing)); free.run(limit=200)
    deep = Machine(); kb_d = load(deep, chr(10).join(
        supposing[:-1] + ["fact depth(0)", ""])); deep.run(limit=200)
    many = Machine(); kb_m = load(many, chr(10).join(
        supposing[:-1] + ["fact hypotheses(0)", ""])); many.run(limit=200)
    check("§21", "a depth bound written in the corpus stops the agent supposing, "
          "and says it was hit rather than declining in silence",
          free.holds(kb_f.term("likely(leaks(pipe))")) == PLUS
          and free.exhausted == 0
          and deep.holds(kb_d.term("likely(leaks(pipe))")) is None
          and deep.exhausted > 0)
    check("§21", "...and so does a bound on how many hypotheses may be open",
          many.holds(kb_m.term("likely(leaks(pipe))")) is None
          and many.exhausted > 0)

    # A denial turns it off again, because it is an ordinary claim.
    off = Machine()
    load(off, chain + chr(10).join(["fact budget(1)", "fact -budget(1)", ""]))
    off.run(limit=400)
    check("§9", "...and denying it restores the default, since it is a fact like "
          "any other", off.widenings == 0)


def a_session_can_be_saved_and_resumed() -> None:
    """A session is **what it was told**, and §3's determinism is why that is
    enough.

    Measured before building it: the same corpus reproduces the same 619 entries
    byte for byte, across four `PYTHONHASHSEED`s. So the journal -- corpora
    loaded, arrivals delivered, runs asked for -- is a complete description of
    what the agent knows, and unlike a pickle it is one a person can read, diff
    and argue with.

    ⚠⚠⚠ **Replaying a session must not re-do it.** The boundary is the one place
    effects leave and it cannot tell a repeat from a first time: resume a session
    that opened a door and the door opens again. This is `_hypothetical`'s
    argument in a second place -- supposing must not bring it about, and neither
    must remembering -- and it needs no new vocabulary, because `taken` has
    always meant *decided on and not emitted*, and the bundle already turns it
    into `did`.
    """
    import json
    import os
    import tempfile

    from .text import load

    def history(m):
        return [(m.g.show(e.proposition), e.sign, mo.depth)
                for mo in m.chain.moments for e in mo.delta]

    corpus = [
        "rule <go> = implies( { +need(?d) }, { +doing(open(?d)) } )",
        "rule <t> = implies( { +says(user, ?p, plus) }, { +?p } )",
        "fact standing(<t>)", "fact +need(door)", "",
    ]
    m = Machine()
    m.actuator("hands")
    kb = load(m, chr(10).join(corpus), scope="w")
    m.run(limit=80)
    kb.say("user", "cold(room)")
    m.run(limit=80)
    check("§13", "the lived session acted", [m.g.show(a) for a in m.emitted]
          == ["open(door)"])

    path = os.path.join(tempfile.mkdtemp(), "session.json")
    m.save(path)
    with open(path, encoding="utf-8") as fh:
        saved = json.load(fh)
    check("§2", "what is saved is what it was TOLD -- RENDERED out of the graph, "
          "not kept beside it in a journal that could drift",
          saved["session"][0]["kind"] == "load"
          and any(j["kind"] == "say" for j in saved["session"])
          and "rule <go>" in saved["session"][0]["src"])

    r = Machine()
    r.actuator("hands")
    # ⚠⚠ A render that cannot be read back is not a save file, and it fails by
    # RAISING -- a `ParseError` on a sign printed as `+` where the surface reads
    # `plus`, or a rule that was never emitted. §20's lesson from `bundlefile`,
    # in a check written after it: a runner whose contract is *any False is a
    # failure* has to be able to say False about a crash.
    try:
        r.replay(saved["session"])
        readable = True
    except Exception:
        readable = False
    check("§20", "the rendered session RE-PARSES: every rule is in it, and a "
          "sign in argument position is written the way the surface reads it",
          readable)
    if not readable:
        return
    w = load(r, "", "w", None)
    check("§3", "⭐ resuming reproduces the history exactly -- same length, and "
          "the determinism measured across hash seeds is what makes that true",
          len(history(r)) == len(history(m)))
    check("§13", "⭐⭐⭐ ...and it does NOT act again: the door is not opened twice",
          r.emitted == [])
    check("§13", "...while still remembering that it acted, because `taken` "
          "becomes `did` through the bundle",
          r.holds(w.term("did(open(door))")) == PLUS)
    check("§13", "...and remembering what the world said",
          r.holds(w.term("cold(room)")) == PLUS)

    # The two histories differ in exactly one way, which is the whole design of
    # this: which record says it acted.
    differ = {(a[0], b[0]) for a, b in zip(history(m), history(r)) if a != b}
    check("§17", "the only difference between a lived session and a resumed one "
          "is the record of acting -- `emitted` where it happened, `taken` "
          "where it is remembered",
          differ and all("emitted" in a or "<did>" in a for a, _ in differ))

    # ...and the report reads `did` from the GRAPH, so a resumed session can
    # still say what it did. It held a Python list first, and reported nothing.
    check("§2", "a resumed session still reports what it did",
          any("open(door)" in line for line in r.report()))


def the_agent_can_say_what_became_of_it() -> None:
    """§2's not-lossy criterion at the one boundary nobody had crossed.

    A corpus with a one-character typo ends `quiescent` with
    `blocked(water(kettle))` deposited -- the agent has diagnosed itself
    exactly -- and there was no way to be told. Every `__main__` in this package
    was an instrument; none was a door.

    Depth first, left to right, because `<plan>` and `<expand>` already built
    the tree. ⭐ **Indent where there is a choice; chain where there is not** --
    one way of getting something is not a branch, and indenting it claims a
    decision was made where none was, the same reason `likely(not(p))` reads as
    one line rather than three.
    """
    from .text import load

    m = Machine()
    kb = load(m, chr(10).join([
        "rule <boil> = implies( { +heated(?w), +water(?w) }, { +boiling(?w) } )",
        "rule <heat> = causes( { +doing(switch(?w)) }, { +heated(?w) } )",
        "rule <intend> = implies( { +goal(doing(?a)) }, { +doing(?a) } )",
        "fact standing(<intend>)",
        "fact +water(kettle)", "fact +goal(boiling(kettle))", ""]))
    m.run(limit=300)
    lines = m.report()
    body = chr(10).join(lines)
    check("§2", "a rule prints as the name its author gave it, not as ninety "
          "characters of its own structure",
          "<boil>" in body and "moment(entry(" not in body)
    check("§2", "the report is the search's own shape: what was asked, how it "
          "was pursued, and what it did",
          "boiling(kettle)" in body and "via <boil>" in body
          and "  switch(kettle)" in body)
    check("§2", "...and the apparatus's own goals are not in it -- `need` and "
          "`fits` are what `why` is for",
          "need(" not in body and "fits(" not in body)

    # The one that matters, and the reason this exists: a typo diagnoses itself.
    bad = Machine()
    kb2 = load(bad, chr(10).join([
        "rule <boil> = implies( { +heated(?w), +water(?w) }, { +boiling(?w) } )",
        "fact +heated(kettle)", "fact +watre(kettle)",
        "fact +goal(boiling(kettle))", ""]))
    bad.run(limit=300)
    told = chr(10).join(bad.report())
    check("§2", "⭐ a corpus with a typo says so: the goal is open, and the "
          "subgoal nothing can produce is named BLOCKED",
          "boiling(kettle)" in told and "water(kettle)  [BLOCKED]" in told)
    check("§5", "...and asking why something absent is believed says nothing "
          "concluded it, rather than returning an empty list",
          bad.why(kb2.term("boiling(kettle)")) == [])
    check("§2", "the working corpus's report does NOT say blocked, so the "
          "fixture can fail", "BLOCKED" not in body)

    # The scoped door for channels, the last of the twin traps to get one.
    ch = Machine()
    kb3 = load(ch, "rule <t> = implies( { +says(user, ?p, plus) }, { +?p } )"
               + chr(10))
    user = kb3.channel("user")
    ch.channels.deliver(user, kb3.term("raining"), "+")
    ch.run(limit=60)
    check("§13", "`kb.channel(name)` opens a channel in the corpus's own scope, "
          "so the socket the world speaks on is the one the rule reads",
          ch.holds(kb3.term("raining")) == PLUS)


def a_dry_search_reaches_for_what_is_out_of_mind() -> None:
    """§19's carve-out, the fourth time, and the argument transfers whole.

        Recall may be incomplete about what to do.
        It may not be incomplete about what it has NOT looked at.

    Unloading a domain is **safe to be wrong about** -- worst case it comes back
    -- which is exactly why *when to unload* may be an ordinary defeasible rule.
    Reaching for it again may not be: `blocked` claims that **nothing** answers a
    goal, an aggregate over a *finished* search, and a goal whose evidence is
    merely dormant would be reported unreachable. That is `_widen`'s unsoundness
    from a fourth side, and it gets the same answer: escalate before believing a
    decline.
    """
    from .text import load

    def run(dormant, goal):
        m = Machine()
        kb = load(m, chr(10).join([
            "rule <r> = implies( { +owes(?c, ?n), +overdue(?c) }, { +chase(?c) } )",
            ""]), scope="esc", domain="rules")
        load(m, chr(10).join(
            ["fact +owes(acme, 100)", "fact +overdue(acme)", ""]),
            scope="esc", domain="billing")
        ctl = (["fact dormant(billing)"] if dormant else []) + \
              (["fact +goal(chase(acme))"] if goal else [])
        if ctl:
            load(m, chr(10).join(ctl + [""]), scope="esc", domain="ctl")
        m.run(limit=300)
        return m, kb

    m0, kb0 = run(dormant=False, goal=True)
    check("§19", "with the domain in mind the agent reaches what it was asked for",
          m0.holds(kb0.term("chase(acme)")) == PLUS and m0.recoveries == 0)

    m1, kb1 = run(dormant=True, goal=True)
    check("§19", "⭐ and with it OUT of mind it still does -- a dry search reaches "
          "for what it put aside rather than reporting the goal unreachable",
          m1.holds(kb1.term("chase(acme)")) == PLUS and m1.recoveries == 1)

    # ⚠⚠⚠ **Only when something is outstanding**, and this is what keeps the
    # escalation from undoing the saving it guards. A run with nothing asked of
    # it is declining nothing, so there is nothing to be wrong about -- and
    # escalating anyway wakes every domain at the end of every run. Measured:
    # without this condition, two dormancy checks failed and were right to.
    m2, kb2 = run(dormant=True, goal=False)
    check("§19", "...but a run with no outstanding goal does not reach for "
          "anything, so unloading keeps paying",
          m2.recoveries == 0 and m2.holds(kb2.term("chase(acme)")) is None)

    # Once per dry search, like widening: it terminates because something
    # applying is what makes the agent trust its shortlist again.
    check("§15", "it escalates once, not once per tick", m1.recoveries == 1)


def the_state_is_kept_not_rebuilt() -> None:
    """§4's walk, carried instead of redone -- and the three ways that is wrong.

    `current_state` collects every proposition the chain has claimed and
    `resolve`s each; it ran twice a tick, and once `delta` took matching out of
    the way it was the binding constraint. A moment is a delta, so the state
    after a write is the state before plus one claim.

    ⚠⚠⚠ Kill-probed four ways when it landed, and **three of the four changed
    nothing that 323 checks could see**. These are those three. An incremental
    state has to reproduce `resolve`'s ordering exactly, and each of these is a
    place where it silently might not.
    """
    m = Machine()
    g, c = m.g, m.chain
    p = g.rel(g.atom("pp"), g.atom("a"))
    q = g.rel(g.atom("qq"), g.atom("a"))

    m._state()                       # build the cache, then grow it
    m.gate.write(m.focus, p, PLUS)
    m.gate.write(m.focus, q, PLUS)
    m.gate.write(m.focus, p, PLUS)   # ...and claim the first one again
    order = [e.proposition for e in m._state()]
    check("§18", "a proposition claimed again is the most recent in the state, "
          "which is what *a description with two candidates resolves to the most "
          "recent* rests on -- the order is semantics, not a detail of the walk",
          order and order[0] == p and order.index(p) < order.index(q))

    # §17's two indices, inside the kept state: a claim about an EARLIER moment,
    # deposited later, must not displace a claim about a later one.
    m2 = Machine()
    early = m2.focus.seat
    later = m2.chain.succeed(early, None)
    m2.gate.reseat(m2.focus, later)
    m2._state()
    m2.chain.deposit(seat=later, locus=later, proposition=p, sign=PLUS)
    m2.chain.deposit(seat=later, locus=early, proposition=p, sign=MINUS)
    held = {e.proposition: e.sign for e in m2._state()}
    check("§17", "a later DEPOSIT about an earlier LOCUS does not displace a claim "
          "about a later one -- latest locus first, and only then latest deposit",
          held.get(p) == PLUS)

    # ...and reasoning about the past does not see the present.
    m3 = Machine()
    e0 = m3.focus.seat
    e1 = m3.chain.succeed(e0, None)
    m3.focus = m3.gate.frame(e1, topic=e0)
    m3._state()
    m3.chain.deposit(seat=e1, locus=e1, proposition=q, sign=PLUS)
    check("§4", "a claim about a moment later than what I am reasoning ABOUT is "
          "not in that moment's state",
          q not in {e.proposition for e in m3._state()})


def a_scope_can_span_documents() -> None:
    """§13's name scope, named -- so a book can be more than one document.

    A corpus is a **bound**, and that is why coreference does not arise in
    authored knowledge: `kettle` means one node inside the bound by
    construction, not by inference, and a name outside a scope names nothing.
    The price was that each `load` had a private table, so two documents could
    not be about the same kettle and a book split into chapters was that many
    disconnected islands.

    ⚠ What this deliberately is NOT: `sameas(a, b)` in the graph. Asserting
    identity needs equals-for-equals in matching, and congruence is either
    machinery -- a decision nobody can argue with -- or a rule per relation per
    position. Deciding identity where the name is READ keeps it a construction,
    and identity discovered later becomes a **revision of intake** rather than
    an inference, which is the shape `learned()` already has for rules.
    """
    from .text import load

    m = Machine()
    a = load(m, "fact +red(kettle)" + chr(10), scope="book")
    b = load(m, "fact +hot(kettle)" + chr(10), scope="book")
    check("§13", "two documents under one scope are about the same kettle -- by "
          "construction, which is what keeps it from being a guess",
          a.atom("kettle") == b.atom("kettle")
          and m.holds(b.term("red(kettle)")) == PLUS
          and m.holds(a.term("hot(kettle)")) == PLUS)

    # ...and a rule authored in one document reasons over facts from the others,
    # which is the thing a book actually needs.
    m2 = Machine()
    load(m2, "rule <r> = implies( { +red(?x), +hot(?x) }, { +dangerous(?x) } )"
         + chr(10), scope="book")
    d = load(m2, "fact +red(kettle)" + chr(10), scope="book")
    load(m2, "fact +hot(kettle)" + chr(10), scope="book")
    m2.run(limit=60)
    check("§13", "...so a rule in one document applies to facts in another",
          m2.holds(d.term("dangerous(kettle)")) == PLUS)

    # The control, and it is the default: an unnamed scope stays private, so
    # nothing here weakened the bound. A fixture where everything is shared
    # cannot tell sharing from a global namespace.
    priv = load(m, "fact +cold(kettle)" + chr(10))
    check("§13", "an unscoped document keeps its own names -- the default is "
          "still that a bare name outside a scope names nothing",
          priv.atom("kettle") != a.atom("kettle")
          and m.holds(priv.term("red(kettle)")) is None)


def matching_is_incremental() -> None:
    """§4's *a moment is a signed delta*, finally read by the matcher.

    The loop was stateless between ticks: it re-ran every rule's join over the
    whole state, weighed the result, applied one, threw the rest away, and did
    all of it again next tick. Measured before building anything: of 5,775
    applications matched over a 600-fact corpus, **75 were new** -- and 92.9% of
    the kettle fixture's were re-derived too, so this was never a big-corpus
    concern. It has been true since the first tick ever ran.

    Nothing new is represented. `Chain.deposit` already records each entry's
    position in its moment's delta, so *what is new since I last looked* was
    always available and never read.
    """
    from .text import load

    m = Machine()
    kb = load(m, chr(10).join([
        "rule <boil> = implies( { +heat(?a, ?w), +water(?w) }, { +boiling(?w) } )",
        "rule <ask-root> = implies( { +goal(?w) }, { +root(?w) } )",
        "fact standing(<ask-root>)",
        "fact +heat(anna, kettle)", "fact +water(kettle)",
        "fact +goal(boiling(kettle))", ""]))
    m.run(limit=400)
    check("§4", "the loop weighs far more applications than matching produces, "
          "because it keeps them: what it re-derived is now what changed",
          m.considered > 3 * m.matched and m.matched > 0)
    check("§4", "...and it still gets there", m.holds(kb.term("boiling(kettle)")) == PLUS)

    # ⭐ And what it does NOT re-weigh. An application known to be a no-op is
    # withheld from the candidate list until something it reads changes, so a
    # tick costs O(new + revived) rather than O(everything ever matched).
    #
    # ⚠ This is the check the optimisation itself needs, and it is a different
    # kind from the three around it: removing the withholding breaks nothing, so
    # nothing else here can tell whether it is still happening. Measured over the
    # suite, 89.4% of verdicts are no-ops -- so a fixture where the kept set and
    # the live set are the same size means it has silently stopped working.
    (cache,) = m._match_cache.values()
    check(
        "§18",
        "the applications are KEPT but not re-weighed: most are withheld as no-ops",
        len(cache["apps"]) > 0 and len(cache["live"]) * 2 < len(cache["apps"]),
    )
    # ...and `defeat` is not told the short list, because whose antecedent holds
    # is a different question from who still has work to do (`rules.py:617`).
    check(
        "§12",
        "...while the rules that MATCHED are carried whole, for defeat to read",
        set(m._matched_rules) >= {a.rule.node for a in
                                  (cache["apps"][k] for k in cache["live"])},
    )

    # ⚠⚠⚠ **The one that is not bookkeeping.** The chain is append-only but
    # `resolve` is not monotone: a denial deposited later makes what a cached
    # application consumed no longer the current claim. Keep it anyway and the
    # agent concludes from a premise it has DENIED.
    #
    # Kill-probed: disable the invalidation pass and `z(a)` becomes `+` --
    # and all 316 other checks still pass. Nothing else in the suite sees it,
    # which is the reason this check exists rather than a reason to trust it.
    d = Machine()
    kbd = load(d, chr(10).join([
        "rule <deny> = implies( { +trigger }, { -p(a) } )",
        "rule <slow> = implies( { +p(?x) }, { +z(?x) } )",
        "fact +p(a)", "fact +trigger", ""]))
    d.run(limit=60)
    check("§8", "an application whose premise is denied before it runs is retired, "
          "not applied -- a remembered option is not a settled one",
          d.holds(kbd.term("p(a)")) == MINUS
          and d.holds(kbd.term("z(a)")) is None)

    # ...and the control, so the fixture can fail: without the denial it applies.
    c = Machine()
    kbc = load(c, chr(10).join([
        "rule <slow> = implies( { +p(?x) }, { +z(?x) } )",
        "fact +p(a)", ""]))
    c.run(limit=60)
    check("§8", "...against a control with nothing denied, where it does apply",
          c.holds(kbc.term("z(a)")) == PLUS)


def the_apparatus_eats_its_own_cooking() -> None:
    """§21: `answers(<M>, ask)` was built so a TOOL's binding could be data, and
    it shipped with **zero apparatus users**. Every request the machinery
    answered, it answered because a Python line said so -- which is this
    codebase's most frequent defect, *something the machinery knows and no rule
    can ask about*, and the same one `exercised`, the entry's grade and a tool's
    binding each closed. The fix is always: put it in the graph.

    Six requests, six bindings, all facts. ⚠⚠⚠ And **deniable is not the same as
    forgettable**: four are §19's carve-out, where denying is *refused* on the
    record rather than obeyed.
    """
    from .text import load

    m = Machine()
    kb = load(m, "fact +nothing(x)\n")
    # The binding NODES exist for all six -- asked structurally rather than by
    # resolving each, so that `ugm.bundle` denying one of them does not turn
    # this into a false failure about a property that has not changed.
    bound = {m.g.show(m.g.member(n, 0)) for n in m.g.instances_of(m.ANSWERS)}
    check("§21", "every request the apparatus answers has its binding in the "
          "GRAPH, so *what answers `fit`* is a query and not a Python line",
          bound >= {"fit", "settle", "verdict", "root", "remember", "re-ask"}
          and all(m.holds(m.g.rel(m.ANSWERS, a.node, a.request)) is not None
                  for a in m.answerers))

    # The two that may be turned off, and the criterion that says which: **a
    # capability whose absence is the status quo ante is safe to retire.**
    off = Machine()
    kb_off = load(off, chr(10).join([
        "rule <boil> = implies( { +heat(?a, ?w), +water(?w) }, { +boiling(?w) } )",
        "rule <ask-root> = implies( { +goal(?w) }, { +root(?w) } )",
        "fact standing(<ask-root>)",
        "rule <done> = implies( { +goal(?w), +rooted(?w), +?w }, { +enough(?w) } )",
        "fact standing(<done>)",
        "fact -answers(<root>, root)",
        "fact +heat(anna, kettle)", "fact +water(kettle)",
        "fact +goal(boiling(kettle))", ""]))
    steps_off = off.run(limit=400)
    check("§21", "a retirable binding really retires: deny `<root>` and nothing "
          "is `rooted`, so the general stop rule never fires -- and the agent is "
          "still SOUND, it just runs to quiescence, which is what it did before "
          "`rooted` existed",
          off.holds(kb_off.term("rooted(boiling(kettle))")) is None
          and off.holds(kb_off.term("boiling(kettle)")) == PLUS
          and steps_off[-1].state == "quiescent")

    # ⚠⚠⚠ §19's carve-out, a fifth time. Deny `<fit>` and backward reading stops
    # -- silently, on one corpus line. So the four it applies to are `standing`,
    # which is the fact the bundle already uses for exactly this claim, and the
    # denial is REFUSED rather than ignored: a fourth silent decline is what §5
    # spent the design's vocabulary avoiding.
    keep = Machine()
    kb_keep = load(keep, chr(10).join([
        "rule <boil> = implies( { +heat(?a, ?w), +water(?w) }, { +boiling(?w) } )",
        "fact -answers(<fit>, fit)",
        "fact +water(kettle)", "fact +goal(boiling(kettle))", ""]))
    keep.run(limit=400)
    subs = [n for n in keep.g.instances_of(keep.SUBGOAL) if keep.holds(n) == PLUS]
    # ⚠ About THIS binding, not a count of every refusal in the run. The first
    # version asserted `== 1` over all of them, and `ugm.bundle` -- which denies
    # one binding per run across the whole suite -- turned that into a false
    # anomaly on three other answerers. A check that counts globals cannot
    # survive an instrument that mutates globals.
    fit_binding = keep.g.rel(
        keep.ANSWERS,
        [a.node for a in keep.answerers if a.name == "fit"][0], keep.FIT)
    refusals = [n for n in keep.g.instances_of(keep.REFUSED)
                if keep.holds(n) == PLUS and keep.g.member(n, 0) == fit_binding]
    check("§19", "...and a STANDING binding may be argued with and not forgotten: "
          "`fact -answers(<fit>, fit)` does not stop backward reading",
          len(subs) == 2)
    check("§5", "...and the refusal is on the record, so *I tried to turn that "
          "off and was not allowed* is answerable rather than a fourth silent "
          "decline",
          len(refusals) == 1)
    # The control: the same corpus without the denial reaches the same subgoals
    # and records no refusal, so the pair can fail.
    ctl = Machine()
    load(ctl, chr(10).join([
        "rule <boil> = implies( { +heat(?a, ?w), +water(?w) }, { +boiling(?w) } )",
        "fact +water(kettle)", "fact +goal(boiling(kettle))", ""]))
    ctl.run(limit=400)
    check("§19", "...against a control that denies nothing: same reading, no "
          "refusal",
          len([n for n in ctl.g.instances_of(ctl.SUBGOAL) if ctl.holds(n) == PLUS]) == 2
          and not [n for n in ctl.g.instances_of(ctl.REFUSED) if ctl.holds(n) == PLUS])

    # ⚠⚠⚠ I put `<remember>` in the retirable column first, and the measurement
    # moved it. The reasoning was *narrowing off means exhaustive recall, which
    # is the default* -- wrong about which thing this answers. `_remember` is not
    # the narrowing; it is the ANSWER to the recall request, and `<ask-fit>` keys
    # on `recalled(?r, ?w)`, so nothing asks `fit` about anything without it.
    check("§21", "⚠ `<remember>` answers the recall REQUEST, it is not recall's "
          "narrowing -- so it is standing too, and the criterion is only as good "
          "as knowing what a thing does",
          keep.holds(keep.g.rel(keep.STANDING,
                                [a.node for a in keep.answerers
                                 if a.name == "remember"][0])) == PLUS)


def a_rule_says_that_it_ran() -> None:
    """`exercised(<R>)` -- the claim `applied(<R>)` was already making, as a
    PROPOSITION rather than as an entry field (§14, §21).

    R5 licenses every derived entry with `applied(<R>)`, so *that this rule ran*
    has been on the trail all along -- and unreadable, because a licence is a
    Python field on the entry. That is the third thing this arc has found in that
    shape, after an entry's grade (§21 item 5) and a tool's binding before
    `answers`, and all three close the same way: put it in the graph.

    What it is FOR: **deadness as a blocked goal.** The user's framing --
    *dying is searching for a rule and finding none* -- means the machinery for
    noticing a dead rule already exists, and the only addition is being able to
    die on it. `ugm.bundle` has caught two dead rules offline this arc
    (`<relevant>` shipping blind, `+open(?w) => +verdict(?w)`); this is the same
    question asked from inside.

    ⚠⚠ **The reaction half is NOT here, and the blocker is §6's, not a new one.**
    `blocked(exercised(<R>))` is deposited whether or not the rule ran, because
    `blocked` means *no RULE fits this* -- true either way, since what concludes
    `exercised` is the machinery. The discriminator would be `achieved`, and §6
    already records that **a root goal is never checked for satisfaction**:
    `<ask-check>` keys on `subgoal(plan, ?w)`, and a goal with no plan is not
    expressible. So this ships the half that is sound and leaves the half that
    needs the root-goal check, which was already §21's.
    """
    from .text import load

    ran = Machine()
    kb = load(ran, chr(10).join([
        "rule <r> = implies( { +p(x) }, { +q(x) } )", "fact +p(x)", ""]))
    ran.run(limit=200)
    dead = Machine()
    kb2 = load(dead, chr(10).join([
        "rule <r> = implies( { +z(x) }, { +q(x) } )", "fact +p(x)", ""]))
    dead.run(limit=200)

    check("§14", "a rule that ran says so, as a proposition a rule could match",
          ran.holds(kb.term("exercised(<r>)")) == PLUS)
    check("§14", "and one that never ran says nothing -- which is the whole "
          "discrimination `ugm.bundle` makes offline",
          dead.holds(kb2.term("exercised(<r>)")) is None)
    check("§5", "it is deposited once, not once per application: it is a claim "
          "about the rule, not a count",
          len([n for n in ran.g.instances_of(ran.EXERCISED)]) == 1)
    check("§21", "⚠ and the reaction half is still blocked on §6's root-goal check: "
          "`blocked` is written either way, because it means *no rule fits* and "
          "what concludes `exercised` is the machinery",
          ran.holds(kb.term("achieved(exercised(<r>))")) is None)


def a_tool_is_data() -> None:
    """§21's honest debt, taken: what binds an answerer to a request (§5, §17).

    A tool is not a new kind of thing. `_fit` and `_verdict` are already requests
    **answered by a function rather than by a search** -- stratum 0's escape from
    §5's wall -- and that is the only shape something outside the agent can take,
    because a search the agent cannot inspect is not reasoning it can be held to.
    What was wrong was that the binding was a Python line, so a corpus could not
    ask which tools existed, retire one, or reason about one.

    ⭐⭐⭐ **A tool proposes; it never concludes.** `answered(<M>, ask, y)` is a
    record, and an authored rule with an authored grade turns it into a claim --
    the `arrived` -> `says` path channels have had all along. Otherwise §12's
    weakest link has a link with nothing behind it and `why()` goes dark at the
    one place the agent cannot introspect.

    ⭐⭐ **One credit walk reaches rules and tools alike**, because it follows
    licences and a tool's answer carries one. That is the whole of what *jointly
    trained* honestly means: a shared credit assignment, not a shared update rule.
    """
    from .tools import episode

    good, kb, _ = episode("fill(kettle)")
    bad, _, _ = episode("smash(jug1)")
    check("§21", "what binds a tool to a request is an ordinary fact, so a corpus "
          "can ask which tools it has", good.holds(kb.term("answers(<oracle>, advice)")) == PLUS)

    retired, _, called = episode("smash(jug1)", extra=["fact -answers(<oracle>, advice)"])
    check("§21", "and can retire one on evidence -- the thing a Python-registered "
          "hook could never be", not called and not retired.emitted)

    check("§19", "credit reaches a tool whose answer was on the support of what "
          "was achieved", "oracle" in {r.name for r, _ in good.review()})
    check("§19", "and blame reaches one whose answer cost a goal, which is what "
          "lets one walk supervise rules and tools together",
          "oracle" in {r.name for r, _ in bad.blame()})
    check("§19", "a tool that advised well is not blamed", not good.blame())

    # The restriction that makes an unreliable tool safe to be wrong.
    from .machine import Machine
    from .text import Loader
    m = Machine()
    m.actuator("hands")
    kb2 = Loader(m)
    kb2.answerer("oracle", "advice", lambda mach, f, e: kb2.term("smash(jug1)"))
    kb2.load(chr(10).join([
        "fact +achieves(smash(jug1), water(kettle))",
        "fact +intact(jug1)", "fact +goal(water(kettle))",
        "rule <ask-route> = implies( { +goal(water(?w)) }, { +advice(?w) } )",
        ""]))
    m.run(limit=200)
    check("§12", "a tool PROPOSES and does not conclude: with no rule trusting it, "
          "the answer is on the record and nothing acted on it",
          m.holds(kb2.term("answered(<oracle>, advice(kettle), smash(jug1))")) == PLUS
          and not m.emitted)

    # ⚠ The trap this cost three times before it was written down.
    twin, _, called_t = episode("fill(kettle)", scoped=False)
    check("§3", "a tool registered by NAME mints its own request relation and is "
          "never called -- anything binding a name goes through the table that "
          "resolves it", not called_t)


def an_episode_teaches_the_next_one() -> None:
    """The learning loop, closed (§19). `ugm.learning` measures it; this holds it.

    Everything upstream of this existed: `review` credits, `blame` attributes a
    lost subgoal, `learned` writes surface text, and forgoing made arbitration
    into a decision instead of a schedule. What did not exist was the join, and
    the run that found it is the check below.

    ⭐⭐⭐ **Suppression is not a decision.** An episode that smashed a jug for
    water blamed the smasher and dropped it from what it recommends -- and then
    smashed the jug again, because omitting a rule leaves it exactly where it
    was: first in authored order. `learned` could say *do not recommend this*
    and could not say *do that instead*, and only the second changes a run.

    ⭐⭐ The missing half was already on the trail. `forgone(A, w)` says `A` was a
    live way of getting `w` and something else was taken, licensed by
    `applied(<winner>)` -- so a blamed winner names its own alternatives. Third
    time credit assignment has needed no new bookkeeping.
    """
    from .learning import Episode, world

    ep1 = Episode(world(jug_first=True))
    check("§19", "a world where the wrong choice costs something: the agent "
          "smashed the jug it also needed", ep1.harmed)
    check("§19", "and the loss is attributed to the DECISION, not the physics",
          "use-jug" in ep1.blamed)
    check("§19", "what it carries forward names the alternative it passed up -- "
          "blame alone could only suppress the rule that did the damage",
          any("<use-tap>" in r for r in ep1.rows)
          and not any("<use-jug>" in r for r in ep1.rows))

    ep2 = Episode(world(jug_first=True) + chr(10).join(ep1.rows) + chr(10))
    check("§19", "so the next episode in the same world makes the other choice",
          not ep2.harmed and ep2.acts == ["fill(kettle)"])
    check("§19", "...and achieves both goals, so it is not merely doing less",
          ep2.water == PLUS and ep2.juice == PLUS)

    # The key is a relation, so what it learned is not a cache of this episode.
    fresh = Episode(world("pot", "jug2", jug_first=True), "pot", "jug2")
    taught = Episode(world("pot", "jug2", jug_first=True)
                     + chr(10).join(ep1.rows) + chr(10), "pot", "jug2")
    check("§19", "and it generalises: a row keyed on the relation `water` saves a "
          "jug the episode was never told about",
          fresh.harmed and not taught.harmed)


def subgoals_make_blame_sayable() -> None:
    """Splitting a task into subgoals is what makes FAILURE attributable (§19).

    `review` credits and deliberately refuses to blame, because an episode that
    achieved nothing may have been an impossible one -- many rules ran, one
    outcome was bad, and nothing points at an author.

    A lost **subgoal** is different, and the difference is §9's, doing real work
    somewhere new:

    | no entry at all   | it was never reached. Many causes, no author.        |
    | an entry says `-` | something MADE it false, and that entry has a licence |

    So blame is the credit walk run over a denial instead of an assertion. What
    makes it land is that the decomposition names the damage without anyone
    anticipating it: backward reading expanded `juice(jug1)` into subgoals
    including `intact(jug1)`, so the thing the other branch broke was already a
    goal, and its loss is on the record with a licence attached.
    """
    from .text import load

    # No tap, so smashing is the ONLY way to the water. That matters: now that
    # the agent forgoes, a world with a safe alternative no longer produces the
    # harm, and this fixture would have measured the forgoing rather than the
    # blame. Sometimes the only way costs something, and that is the case blame
    # is for.
    src = chr(10).join([
        "rule <use-jug> = implies( { +goal(water(?w)), +jug(?j), +holds(?j, ?w) },"
        " { +doing(smash(?j)) } )",
        "rule <eff> = implies( { +did(?a), +achieves(?a, ?y) }, { +?y } )",
        "rule <cost> = implies( { +did(smash(?j)) }, { -intact(?j) } )",
        "rule <squeeze> = implies( { +fruit(?f), +jug(?j), +intact(?j) }, { +juice(?j) } )",
        "fact +achieves(smash(jug1), water(kettle))",
        "fact +jug(jug1)", "fact +holds(jug1, kettle)", "fact +intact(jug1)",
        "fact +fruit(orange)",
        "fact +goal(water(kettle))",
        "fact +goal(juice(jug1))",
        "",
    ])
    m = Machine()
    m.actuator("hands")
    kb = load(m, src)
    m.run(limit=4000)
    blamed = {r.name for r, _ in m.blame()}

    check("§19", "a lost subgoal names its own author -- the walk reaches the DECISION "
          "and not only the physics that carried it out",
          "use-jug" in blamed and "cost" in blamed)
    check("§19", "and the subgoal that was lost is one nobody wrote down: backward "
          "reading produced `intact(jug1)`, so the damage was already a goal",
          m.holds(kb.term("intact(jug1)")) == "-"
          and any("intact" in m.g.show(n) for n in m.g.instances_of(m.HARMED)))
    # The discriminating half: an episode where nothing was broken must blame
    # nothing, or "blame" is just a second name for "ran".
    m2 = Machine()
    m2.actuator("hands")
    load(m2, src.replace(
        "fact +achieves(smash(jug1), water(kettle))",
        "fact +unused(smash(jug1))").replace(
        "rule <use-jug> = implies( { +goal(water(?w)), +jug(?j), +holds(?j, ?w) },"
        " { +doing(smash(?j)) } )", ""))
    m2.run(limit=4000)
    check("§19", "an episode that broke nothing blames nobody, so blame is not a second "
          "name for *applied*",
          not m2.blame())

    # ⚠ The trap, and it is why blame needs `-` rather than absence. Most
    # unachieved subgoals in a run are GENERIC (`heat(?a, kettle)`) and were never
    # meant to hold as stated. Counting those as failures blames every rule for
    # every search it ever ran.
    m3 = Machine()
    kb3 = load(m3, chr(10).join([
        "rule <boil> = implies( { +heat(?a, ?w), +water(?w) }, { +boiling(?w) } )",
        "rule <pour> = implies( { +tap(?t), +under(?w, ?t) }, { +water(?w) } )",
        "fact +tap(sink)", "fact +under(kettle, sink)", "fact +heat(anna, kettle)",
        "fact +goal(boiling(kettle))", "",
    ]))
    m3.run(limit=4000)
    check("§19", "⚠ and a search that left generic subgoals unmet blames nobody -- "
          "`heat(?a, kettle)` was never meant to hold as stated",
          m3.holds(kb3.term("boiling(kettle)")) == PLUS and not m3.blame())


def taking_one_way_passes_up_the_others() -> None:
    """Forgoing: the thing arbitration was assumed to do and did not (§14, §18).

    Arbitration is described as choosing one rule among those that matched. What
    it did was choose one to run **first** -- the losers were deferred, and a
    loop that runs to quiescence applied every one of them eventually. Measured
    before this existed, with acts: `emitted: ['fill(kettle)', 'smash(jug1)']`.
    The agent filled the kettle AND smashed the jug.

    > **A choice that cannot be forgone is not a choice.** That is why ordering
    > could only permute a fixed amount of work, why an exact recall table bought
    > nothing, and why *choose the better rule* had no measurable content: the
    > agent took the better rule and the worse one.

    So `forgone(<R>, <w>)` -- *R was a live way of getting w and I took another*.
    A fourth way for a rule not to run, and the only one that is a **decision**:
    defeat says a rival is better, the veto says never, recall says it did not
    come to mind. This says it was reasonable and was passed up.

    Two things it is deliberately not. It is not a retraction of the goal, which
    was the first thing tried: retract it and credit cannot find what it achieved,
    and a failed act loses the want with nothing left to notice it. And it is not
    silent -- the deposit is licensed by the winner, so *what did you not do, and
    why* is answerable, which is what makes passing up recoverable.
    """
    from .text import load

    src = chr(10).join([
        "rule <use-tap> = implies( { +goal(water(?w)), +tap(?t), +under(?w, ?t) },"
        " { +doing(fill(?w)) } )",
        "rule <use-jug> = implies( { +goal(water(?w)), +jug(?j), +holds(?j, ?w) },"
        " { +doing(smash(?j)) } )",
        "rule <eff> = implies( { +did(?a), +achieves(?a, ?y) }, { +?y } )",
        "rule <cost> = implies( { +did(smash(?j)) }, { -intact(?j) } )",
        "rule <squeeze> = implies( { +fruit(?f), +jug(?j), +intact(?j) }, { +juice(?j) } )",
        "fact +achieves(fill(kettle), water(kettle))",
        "fact +achieves(smash(jug1), water(kettle))",
        "fact +tap(sink)", "fact +under(kettle, sink)",
        "fact +jug(jug1)", "fact +holds(jug1, kettle)", "fact +intact(jug1)",
        "fact +fruit(orange)",
        "fact +goal(water(kettle))",
        "fact +goal(juice(jug1))",
        "",
    ])
    m = Machine()
    m.actuator("hands")
    kb = load(m, src)
    m.run(limit=4000)
    emitted = [m.g.show(n) for n in m.emitted]

    check("§18", "taking one way of getting something passes up the others: one act "
          "left the agent, not both",
          emitted == ["fill(kettle)"])
    check("§18", "so the alternative's cost is not paid -- and this is a safety property "
          "before it is a learning one, because an act cannot be taken back",
          m.holds(kb.term("intact(jug1)")) == PLUS
          and m.holds(kb.term("juice(jug1)")) == PLUS)
    passed_up = next(r for r in m.rules.rules if r.name == "use-jug")
    taken = next(r for r in m.rules.rules if r.name == "use-tap")
    check("§18", "and *what did you not do, and why* is answerable: the deposit names "
          "the rule passed up, licensed by the one that was taken",
          m.holds(m.g.rel(m.FORGONE, passed_up.node, kb.term("water(kettle)"))) == PLUS
          and m.holds(m.g.rel(m.FORGONE, taken.node, kb.term("water(kettle)"))) is None)
    # The learning consequence, which is why this sits beside `review`. Before
    # forgoing, credit recommended the jug-smasher because smashing was on the
    # support of the water it got.
    check("§19", "credit now names the choice that was made and not the one that was "
          "passed up",
          "use-tap" in {r.name for r, _ in m.review()}
          and "use-jug" not in {r.name for r, _ in m.review()})

    # ⚠ The judgement, stated as a check because it is the one place this could
    # be wrong: forgoing is the DEFAULT, so an agent that should have done both
    # under-does. That is chosen on which error is recoverable -- and this is the
    # recovery, as one ordinary corpus rule rather than machinery.
    # Note which three mechanisms have to meet for this to work, none of them
    # built for it: `enough` makes the agent try to stop, the veto refuses the
    # stop and deposits `open`, and the retry rule reads that. *What I wanted is
    # still outstanding, so reconsider what I passed up* -- §21's backtracking
    # item arriving as a consequence rather than as machinery.
    retry = chr(10).join([
        "rule <retry> = implies( { +open(?w), +forgone(?r, ?w) }, { -forgone(?r, ?w) } )",
        "fact standing(<retry>)",
        "rule <done> = implies( { +juice(?j) }, { +enough(juice(?j)) } )",
        "fact standing(<done>)",
        "",
    ])
    m2 = Machine()
    m2.actuator("hands")
    kb2 = load(m2, src.replace(
        "fact +achieves(fill(kettle), water(kettle))", "") + retry)
    m2.run(limit=4000)
    check("§18", "⚠ and passing up is REVISABLE: the chosen way did not deliver, so the "
          "goal stayed open and one corpus rule handed the alternative back",
          [m2.g.show(n) for n in m2.emitted] == ["fill(kettle)", "smash(jug1)"]
          and m2.holds(kb2.term("water(kettle)")) == PLUS)


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
    def first_corpus_move(src, ignore=()):
        machine = Machine()
        load(machine, src)
        # `ignore` is for a corpus rule that is apparatus rather than a
        # competitor -- a `standing` rule that denies a preference is not one of
        # the moves being chosen between, and counting it as the first move
        # measures the wrong thing.
        skip = {r.name for r in machine.bundle} | set(ignore)
        first = None
        for s in machine.run(limit=600):
            if first is None and s.applied and s.applied.rule.name not in skip:
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

    # ⚠⚠ Two properties of the table that the `forest` commit got wrong, measured
    # here so the record cannot drift again.
    #
    # `_priority` resolves each row through the chain and requires `+`, so a
    # preference is an ordinary DENIABLE claim. `forest` concluded that the
    # ensemble "has a way for advice to accumulate and no way for it to be
    # overruled"; the second half is false, and the experiment simply never
    # reached for the mechanism.
    denied = stronger + "fact -prefer(<byB>, at(p), 5)" + chr(10)
    check(
        "§12",
        "a preference row is deniable -- advice can be overruled, not only outweighed",
        first_corpus_move(denied)[0] == "byA",
    )
    vetoed = stronger + chr(10).join([
        "rule <veto> = implies( { +b(?x) }, { -prefer(<byB>, at(?x), 5) } )",
        "fact standing(<veto>)",
        "",
    ])
    check(
        "§19",
        "...and by a rule, not only by a fact -- so overruling is itself arguable",
        first_corpus_move(vetoed, ignore=("veto",))[0] == "byA",
    )
    # ⭐⭐ And the sharper reason bagging failed, which is R7 rather than the
    # combination rule: propositions intern, so the SAME row twice is one node.
    #
    # > An ensemble's agreement is invisible and only its disagreement adds.
    #
    # Two trees that learned the same row contribute once; two that learned
    # different scores accumulate. That is why the summation is left alone -- it
    # is a representation fact, not a policy choice.
    twice = stronger + chr(10).join([
        "fact +prefer(<byA>, at(p), 3)",
        "fact +prefer(<byA>, at(p), 3)",
        "",
    ])
    check(
        "R7",
        "the same preference row twice is ONE proposition -- 3 and 3 do not make 6",
        first_corpus_move(twice)[0] == "byB",
    )
    distinct = stronger + chr(10).join([
        "fact +prefer(<byA>, at(p), 3)",
        "fact +prefer(<byA>, at(p), 4)",
        "",
    ])
    check(
        "§19",
        "...while two DISTINCT rows do sum, and outweigh the stronger single row",
        first_corpus_move(distinct)[0] == "byA",
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
    rival_hypotheses_are_comparable()
    recall_is_narrowable()
    the_better_move_wins()
    what_the_situation_is_about()
    crossing_opens_hypotheses()
    a_hypothesis_does_not_happen()
    an_action_is_substituted_by_its_outcome()
    an_agent_that_can_stop()
    no_goal_is_dropped_silently()
    experience_is_offline()
    a_root_goal_is_askable()
    a_request_can_be_re_asked()
    a_domain_can_be_taken_out_of_mind()
    a_hypothesis_can_be_re_entered()
    its_own_effort_is_reasonable_over()
    the_knobs_are_claims()
    a_session_can_be_saved_and_resumed()
    the_agent_can_say_what_became_of_it()
    a_dry_search_reaches_for_what_is_out_of_mind()
    the_state_is_kept_not_rebuilt()
    a_scope_can_span_documents()
    matching_is_incremental()
    the_apparatus_eats_its_own_cooking()
    a_rule_says_that_it_ran()
    a_tool_is_data()
    an_episode_teaches_the_next_one()
    subgoals_make_blame_sayable()
    taking_one_way_passes_up_the_others()
    doubt_is_a_tie()
    prohibitions_are_not_recalled()
    the_index_agrees_with_the_walk()
    a_cause_moves_the_register()
    reference_is_binding()
    quiescence_is_an_occasion()
    surface()
    the_surface_can_say_what_the_apparatus_is_made_of()
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
