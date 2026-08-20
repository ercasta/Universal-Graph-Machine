"""One runner. Every check prints its named observations; any False is a failure.

Checks are grouped by the section of `docs/rules-design.md` they hold to account.
"""

from . import corpora as _corpora
from typing import List, Tuple

from .core.chain import MINUS, PLUS, UNSURE
from .core.graph import Graph
from .core.machine import Machine
from .core.rules import (CAUSES, IMPLIES, Member, RuleSet, match,
                    structural_relations, unify)

_results: List[Tuple[str, str, bool]] = []


# ⚠ `BUNDLE_STRATUM0 = {"span-complete", "span-itself"}` was here -- §11's
# containment policy, which `Moment.at_or_after` consulted, and which two checks
# filtered out so they measured a CORPUS's recognisers rather than the bundle's.
# Both rules went with the locus, so the filter matched nothing and hid nothing:
# a set of names that no longer exist is not a guard, it is a check that has
# stopped looking. The bundle ships no stratum-0 rule now, and if it ever does
# again the layering check below should fail and say so.


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


def chain_reads() -> None:
    m = Machine()
    g, c = m.g, m.chain
    on, a, b = g.atom("on"), g.atom("a"), g.atom("b")
    p = g.rel(on, a, b)

    m1 = c.succeed(c.root, None)
    c.deposit(proposition=p, sign=PLUS)
    check("§6", "an asserted proposition holds", c.holds(p) == PLUS)
    m2 = c.succeed(m1, None)
    check("§6", "a moment with no entry about it changes nothing", c.holds(p) == PLUS)
    check("§5", "a proposition with no entry claims nothing", c.holds(g.rel(on, b, a)) is None)

    c.succeed(m2, None)
    c.deposit(proposition=p, sign=MINUS)
    check("§6", "a later claim overrides an earlier one", c.holds(p) == MINUS)
    # ⚠ LOST with the second time: `the earlier moment is unchanged by the later
    # claim` was `c.holds(p, m1, m3) == PLUS` -- the locus index. `resolve`
    # answers about the chain's end and nothing else. *Did this hold THEN* is a
    # corpus rule over `in_delta`/`anc`/`entry_of` now, not a Python service:
    # see `Chain.resolve`. What survives of it is the next check.
    check("§4", "the earlier entry is still in its own moment",
          any(e.proposition == p and e.sign == PLUS for e in m1.delta))

    m4 = c.succeed(c.now, None)
    lvl = g.rel(g.atom("level"), g.atom("tank"))
    c.deposit(proposition=lvl, sign=PLUS)
    c.succeed(m4, None)
    c.deposit(proposition=lvl, sign=UNSURE)
    check(
        "§6",
        "`?` invalidates without replacing -- it does not return the old value",
        c.holds(lvl) == UNSURE,
    )


def a_revision_is_a_second_entry() -> None:
    """What is left of §17's two indices, and it is the half that was never
    about a locus.

    ⚠⚠⚠ The group this replaces was `two_indices`: deposit about M7 from M12,
    then ask both *what I now think about M7* and *what I thought at M7* and get
    different answers. Neither question is askable -- an entry has no locus, so
    there is no second time to index by. What remains is the claim §12 makes
    about any revision: it ADDS, so the original is still findable.
    """
    m = Machine()
    g, c = m.g, m.chain
    tt = g.rel(g.atom("taking_turns"), g.atom("anna"), g.atom("bo"))

    m7 = c.succeed(c.root, None)
    for _ in range(4):
        m7 = c.succeed(m7, None)
    c.deposit(proposition=tt, sign=PLUS)

    m12 = m7
    for _ in range(5):
        m12 = c.succeed(m12, None)
    # I now think they were not taking turns.
    c.deposit(proposition=tt, sign=MINUS)

    check("§17", "what I now think", c.holds(tt) == MINUS)
    check(
        "§12",
        "nothing was invalidated: the original entry is still in its moment",
        any(e.proposition == tt and e.sign == PLUS for e in m7.delta),
    )
    check(
        "§12",
        "and both claims are still enumerable, in order",
        [e.sign for e in c.claims_about(tt)] == [PLUS, MINUS],
    )


# -- §13 the gate ------------------------------------------------------------


def gate() -> None:
    """⚠⚠⚠ Four of this group's seven checks were about the FRAME, and there is
    no frame. The stamp was *proposition and sign from the rule; locus, deposit,
    licence and source from the frame* -- and two of those four came from a
    register that said where the agent was standing. Gone with it:

        the locus is stamped from the frame's topic
        about-when and believed-since differ, honestly
        a seat before its topic is refused where it is minted
        topic defaults to the seat

    What is left is the half §13 was actually for: the rule gives two of the
    stamp's parts and may not give the rest, and the deposit lands where nothing
    chose it.
    """
    m = Machine()
    g, c, gate_ = m.g, m.chain, m.gate
    p = g.rel(g.atom("rain"), g.atom("tuesday"))

    c.succeed(c.root, None)
    now = c.succeed(c.now, None)

    # ⚠ Held in a variable, not re-minted: `g.atom` does not intern, so
    # `g.atom("supposing")` asked twice is two nodes and the comparison below
    # fails while looking right. The name-identity trap, caught writing this.
    why = g.atom("supposing")
    e = gate_.write(p, PLUS, licence=why)
    check("§13", "the deposit lands at the chain's end, which nothing chose",
          e in now.delta and c.now is now)
    check("§13", "licence is stamped, not claimed by the rule", e.licence is why)

    ok = False
    try:
        gate_.write(g.rel(g.atom("rain"), g.var("?d")), PLUS)
    except ValueError:
        ok = True
    check("§13", "a generic proposition cannot be deposited", ok)

    # ...unless it is MENTIONED (§14). The machinery reifying a rule is
    # mentioning; a rule's consequent is using. That distinction outlived the
    # frame because it was never about where anyone was standing.
    e2 = gate_.write(g.rel(g.atom("rain"), g.var("?d")), PLUS, mention=True)
    check("§14", "a mentioned generic proposition can be", e2.mention)


# -- §12 uncertainty ---------------------------------------------------------


def uncertainty_is_a_proposition() -> None:
    """There is no grade, and `@` is refused. (§10, §12)

    @likely was a field on an entry and a closed set of five names in Python,
    composed by weakest link on every write. ⚠ What is lost is that weakest
    link was AUTOMATIC and TOTAL.

    See docs/design/selftest.md#uncertainty-is-a-proposition.
    """
    from .core.text import load

    check("§10", "`@` is refused, and says what to write instead",
          _refuses("rule <r> = implies( { +p(a) }, { +q(a) @likely } )"))

    # Crossing: what a grade did for free, as corpus lines. ⚠ Since situations
    # went, the rule is written ANCHORED -- `holds_in(?w, ...)` on both sides --
    # because there is no frame to unwrap the assumption into. The uncertainty
    # is still a proposition a rule can read; what changed is that carrying it
    # is the corpus's to write. See `docs/descriptions-to-rules.md` for the
    # five-rule compiler that writes the anchored twin from the bare rule.
    m = Machine()
    kb = load(m, chr(10).join([
        "rule <wet> = implies( { +holds_in(?w, rain(?x)) },",
        "                      { +holds_in(?w, wet(?x)) } )",
        "fact +holds_in(likely, rain(street))", ""]))
    m.run(limit=80)
    check("§12", "an uncertain premise carries its uncertainty to the "
          "conclusion -- as a WRAPPER a rule can read, not a field it cannot",
          m.holds(kb.term("holds_in(likely, wet(street))")) == PLUS)
    check("§12", "...and the bare conclusion is never asserted, so nothing "
          "downstream can quietly treat it as certain",
          m.holds(kb.term("wet(street)")) is None)

    # ⚠⚠⚠ **What went with situations, recorded rather than quietly dropped.**
    # Two independent uncertainties used to give a NESTED conclusion --
    # `likely(possible(c(t)))` -- because each supposition unwrapped its own
    # premise into one frame and discharge re-wrapped what came out. Anchored
    # rules cannot reproduce it: `holds_in(likely, a(t))` and
    # `holds_in(possible, b(t))` are in two anchors, and a rule needing both
    # fires in neither. **The weakest link as structure is a capability this
    # deletion cost**, and nothing here replaces it.


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


def _move(m, limit: int = 20):
    """Step until something APPLIES, and hand back that step.

    ⚠ `Machine.tick` is one move of the table loop, and a move is not always an
    application: the loop spends a tick DEPOSITING a doubt when two rules score
    within tolerance, which is its own documented behaviour -- *depositing is
    the move*. A check about what arbitration answered wants the answer, not the
    tick it happened on.
    """
    for _ in range(limit):
        one = m.tick()
        if one.applied is not None or one.state in ("quiescent", "stopped"):
            return one
    return one


def arbitration_is_total() -> None:
    m = Machine()
    g = m.g
    p, q = g.atom("p"), g.atom("q")
    lit = g.atom("lit")
    r1 = m.rules.rule(IMPLIES, [Member(PLUS, g.rel(lit, p))], [Member(PLUS, g.rel(lit, q))], "R1")
    r2 = m.rules.rule(IMPLIES, [Member(PLUS, g.rel(lit, p))], [Member(MINUS, g.rel(lit, q))], "R2")
    m.gate.write(g.rel(lit, p), PLUS)

    step = _move(m)
    check("§14", "with two rules matching, arbitration still answers", step.applied is not None)
    check("§14", "and it answers by authored order when nothing overrides", step.applied.rule is r1)

    m2 = Machine()
    g2 = m2.g
    lit2, p2, q2 = g2.atom("lit"), g2.atom("p"), g2.atom("q")
    a1 = m2.rules.rule(IMPLIES, [Member(PLUS, g2.rel(lit2, p2))], [Member(PLUS, g2.rel(lit2, q2))], "A1")
    a2 = m2.rules.rule(IMPLIES, [Member(PLUS, g2.rel(lit2, p2))], [Member(MINUS, g2.rel(lit2, q2))], "A2")
    # ⚠ Deposited, not called. Precedence is what the graph claims -- this used
    # to reach into a Python table, and it was the only thing in the suite that
    # broke when the table went, which is what said the table was the anomaly.
    m2.gate.write(g2.rel(m2.OVERRIDES, a2.node, a1.node), PLUS,
                  source=m2.KB, mention=True)
    m2.gate.write(g2.rel(lit2, p2), PLUS)
    step2 = _move(m2)
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
    m.gate.write(heat, PLUS)
    m.gate.write(water, PLUS)
    before = m.chain.now
    m.run(limit=5)
    check("§10", "`causes` lands in a later moment", m.chain.now.depth > before.depth)
    check("§10", "and the effect is believed", m.holds(boiling) == PLUS)

    m2 = Machine()
    g2 = m2.g
    cloudy = g2.rel(g2.atom("cloudy"), g2.atom("mon"))
    rain = g2.rel(g2.atom("rain"), g2.atom("mon"))
    m2.rules.rule(IMPLIES, [Member(PLUS, cloudy)], [Member(PLUS, rain)], "R2")
    m2.gate.write(cloudy, PLUS)
    seat_before = m2.chain.now
    m2.run(limit=5)
    check("§10", "`implies` lands in the same moment", m2.chain.now is seat_before)
    check("§10", "...and the conclusion is there to be read",
          m2.chain.resolve(rain) is not None)


def quiescence() -> None:
    m = Machine()
    g = m.g
    p, q = g.rel(g.atom("f"), g.atom("p")), g.rel(g.atom("f"), g.atom("q"))
    m.rules.rule(IMPLIES, [Member(PLUS, p)], [Member(PLUS, q)], "pq")
    m.gate.write(p, PLUS)
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
        IMPLIES, [Member(PLUS, said)], [Member(PLUS, raining)], "trust-user"
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
    e = m.chain.resolve(raining)
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
    e1 = m2.chain.deposit(proposition=p2, sign=PLUS)
    e2 = m2.chain.deposit(proposition=p2, sign=MINUS)
    check("§5", "two claims about one proposition are two distinct entry nodes", e1.node != e2.node)
    check("§5", "so a fact about one does not land on the other", m2.chain.entry_by_node(e1.node).sign == PLUS)


# -- the surface ------------------------------------------------------------


def _loads(src: str):
    from .core.text import load

    m = Machine()
    return m, load(m, src)


def _refuses(src: str) -> bool:
    from .core.text import ParseError

    try:
        _loads(src)
        return False
    except ParseError:
        return True


def surface() -> None:
    """One grammar for rules, facts and facts about rules -- because a rule is a
    relation instance like any other, which is R3 and R4 in the surface."""
    from .core.text import ParseError, Parser, tokenise

    m, kb = _loads("fact +on(a, b)\nfact -in(b, c)   # a comment\n")
    check("§3", "the surface writes a fact", m.holds(kb.term("on(a, b)")) == PLUS)
    check("§6", "and a signed one", m.holds(kb.term("in(b, c)")) == MINUS)
    check("§13", "a loaded fact is stamped as having come from the KB", m.chain.resolve(kb.term("on(a, b)")).source == m.KB)

    check("§4", "a fact may not contain a variable", _refuses("fact +on(?x, b)"))
    check(
        "§13",
        "a consequent naming a variable the antecedent never binds is refused",
        _refuses("rule <r> = implies( { +p(?x) }, { +q(?y) } )"),
    )
    check("§10", "a third connective is refused", _refuses("rule <r> = enables( { +p(a) }, { +q(a) } )"))
    check("§10", "`@` is refused: grades are gone, and a corpus written against "
          "the old notation means something this one does not",
          _refuses("rule <r> = implies( { +p(a) }, { +q(a) @0.7 } )"))
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
    check("§14", "and `overrides` in the surface is read as precedence",
          len(m2.rules.precedence(m2.OVERRIDES)) == 1)
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
    e = m.chain.resolve(said)
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
        m2.chain.resolve(s2) is None,
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
    step = _move(m5)
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
    m3.gate.write(g3.rel(m3.DOING, heat), PLUS)
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
    m4.gate.write(g4.rel(m4.DOING, h4), PLUS)
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
    from .core.text import load

    m = Machine()
    kb = load(m, "rule <r> = implies( { +a(x) }, { -b(x) } )")
    # ⚠⚠⚠ **What went with situations.** A denial concluded under a supposition
    # used to cross out INSIDE the wrapper -- `likely(not(b(x)))` and never
    # `-likely(b(x))` -- and that was `discharge` re-wrapping on the way out.
    # With no frame there is no way out and nothing to re-wrap, so the sign
    # stays a sign. **The claim §16 makes is still true and nothing in the
    # engine now enforces it**; a corpus that wants the distinction writes
    # `not(...)` itself. Recorded here rather than deleted in silence.

    # The two forms are one claim, so a corpus need not know which it is
    # looking at. The rules are written against the sign.
    m2 = Machine()
    kb2 = load(m2, "rule <s> = implies( { -b(x) }, { +noticed(x) } )")
    m2.gate.write(m2.g.rel(m2.NOT, kb2.term("b(x)")), PLUS)
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

    +con(?r, ?pat, +) binds ?pat to a stored pattern, so anything concluded
    about ?pat is a ground claim that happens to contain variables.

    See docs/design/selftest.md#mention-propagates.
    """
    from .core.text import load

    m = Machine()
    load(m, "rule <boil> = implies( { +heat(?w) }, { +boiling(?w) } )")
    m.reify_all()
    g = m.g
    concludes = g.atom("concludes")
    r, pat = g.var("?r"), g.var("?pat")
    m.rules.rule(
        IMPLIES,
        [Member(PLUS, g.rel(m.CON, r, pat, m.rules.SIGN[PLUS], g.var("?i")))],
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
        m.gate.write(g.rel(m.EXPECTS, p, m.rules.SIGN[expected]), PLUS, mention=True
        )
        m.gate.write(p, observed)
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
    m.gate.write(g.rel(m.EXPECTS, p, m.rules.SIGN[PLUS]), PLUS, mention=True)
    m.gate.write(p, PLUS)
    m.run(limit=8)
    check(
        "§18",
        "an expectation the world met is not a deviation",
        m.holds(g.rel(m.DEVIATES, p)) is None,
    )


def the_surface_can_say_what_the_apparatus_is_made_of() -> None:
    """The bundle is authored in the surface, so a corpus can argue with it.

    §2's expressibility criterion, applied to the apparatus itself.

    See docs/design/selftest.md#the-surface-can-say-what-the-apparatus-is-made-of.
    """
    from .core.text import load

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


def a_verdict_names_what_it_settled() -> None:
    """*What am I stuck on?* -- answerable out loud. (§14, §19)

    docs/quest-feedback.md §1. ⚠ Instantiated at the VERDICT rather than at the
    subgoal, because a verdict is asked at quiescence -- the latest moment
    there is, and therefore the one that...

    See docs/design/selftest.md#a-verdict-names-what-it-settled.
    """
    from .core.text import load

    def blocked(src):
        m = Machine()
        load(m, src)
        m.run(limit=300)
        return sorted({m.g.show(e.proposition) for mo in m.chain.moments
                       for e in mo.delta
                       if m.g.show(e.proposition).startswith("blocked(")})

    one = blocked(chr(10).join([
        "rule <unlock> = implies( { +have(?w, ?k), +opens(?k, ?d) }, { +open(?d) } )",
        "fact +opens(key1, door1)", "fact +goal(open(door1))", ""]))
    check("§19", "⭐⭐⭐ a verdict names what the plan had already bound -- the "
          "sibling premise was satisfied, so the key it was satisfied BY is in "
          "the report", one == ["blocked(have(?w, key1))"])

    ground = blocked(chr(10).join([
        "rule <unlock> = implies( { +opens(?k, ?d), +me(?w), +have(?w, ?k) },",
        "                        { +open(?d) } )",
        "fact +opens(key1, door1)", "fact +me(p1)", "fact +goal(open(door1))", ""]))
    check("§14", "...and with every variable bound it is GROUND, so the agent can "
          "utter it -- which is what turns *ask someone for help* from a special "
          "case into the general one", ground == ["blocked(have(p1, key1))"])

    # ⚠⚠⚠ **One report per PLAN.** A rule fitted to two goals shares its variable
    # nodes, so both plans carry the same `?k` bound differently and subgoal the
    # same `have(?w, ?k)` node. The first version of this collected every
    # relevant binding into one environment, let the last one win, and reported
    # ONE key: the agent was stuck on two and said one. Arbitrary and silent.
    two = blocked(chr(10).join([
        "rule <unlock> = implies( { +have(?w, ?k), +opens(?k, ?d) }, { +open(?d) } )",
        "fact +opens(key1, door1)", "fact +opens(key2, door2)",
        "fact +goal(open(door1))", "fact +goal(open(door2))", ""]))
    check("§19", "⚠⚠⚠ ...and two plans give two reports, because one rule fitted "
          "twice shares its variables -- collapsing them lets the last binding "
          "win and the agent says one of the things it is stuck on",
          two == ["blocked(have(?w, key1))", "blocked(have(?w, key2))"])


def the_tick_limit_is_on_the_record() -> None:
    """*Did I run out of time?* -- askable at last. (§13, §21)

    ⭐⭐⭐ A foreign corpus asked for this ahead of every feature on its list
    (docs/quest-feedback.md §0).

    See docs/design/selftest.md#the-tick-limit-is-on-the-record.
    """
    from .core.text import load

    m = Machine()
    kb = load(m, chr(10).join([
        "rule <a> = implies( { +p(x) }, { +q(x) } )", "fact +p(x)", ""]))
    steps = m.run(limit=60)
    check("§13", "a run that finishes is NOT reported as bounded -- a corpus "
          "with nothing left to do was stopped by nothing, and saying otherwise "
          "would make the record useless in the other direction",
          steps[-1].state == "quiescent"
          and m.chain.holds(kb.term("bounded(ticks)")) is None)

    m2 = Machine()
    kb2 = load(m2, chr(10).join([
        "rule <spin>  = causes( { +quiet(?m) }, { +turn(?m) } )",
        "rule <panic> = implies( { +bounded(ticks) }, { +noticed(runaway) } )", ""]))
    steps2 = m2.run(limit=40)
    check("§21", "⭐⭐⭐ ...and a run still working when the budget bites SAYS so, "
          "so a runaway stops being indistinguishable from a finished corpus",
          len(steps2) == 40 and steps2[-1].state == "applied"
          and m2.chain.holds(kb2.term("bounded(ticks)")) == PLUS)
    m2.run(limit=10)
    check("§19", "...and it is an OCCASION, so a corpus reacts to its own "
          "runaway rather than being cut off in silence",
          m2.chain.holds(kb2.term("noticed(runaway)")) == PLUS)

    # ⚠⚠⚠ `Loader.term` parsed one term and dropped the rest of the string, and
    # `Loader.say` uses it -- so an agent could say one thing and the hearer
    # believe another, with nothing reporting a difference. A truncation is
    # still a valid term, so it failed as a WRONG ANSWER rather than a crash.
    from .core.text import ParseError
    m3 = Machine()
    kb3 = load(m3, "fact +z(z)" + chr(10))
    refused = []
    for src in ("a b", "a(b) junk here"):
        try:
            kb3.term(src)
        except ParseError:
            refused.append(src)
    check("§8", "⚠⚠⚠ `term` refuses leftovers rather than silently truncating -- "
          "what one agent says is what another believes, or the wire is a lie",
          refused == ["a b", "a(b) junk here"])
    check("§8", "...and a term that is genuinely one term still reads, including "
          "a chained application",
          m3.g.show(kb3.term("a(b)(c)")) == "a(b)(c)"
          and m3.g.show(kb3.term("on(a, b)")) == "on(a, b)")


def silence_over_a_stretch_is_sayable() -> None:
    """*Nothing was declared this round* -- without negation as failure. (§9, §11)

    docs/dungeon-feedback.md §4 asked for negation as failure over an open
    domain: *the hero attacks by default when the player has declared nothing
    this round*, which no corpus can write as -declares(hero, ?what), because
    §9's - needs an entry that DENIES and absence is not denial. ⚠ The channel
    is a ground atom here.

    See docs/design/selftest.md#silence-over-a-stretch-is-sayable.
    """
    from .core.text import load

    # ⚠⚠⚠ `span_of(?s, ?a, ?b)` went with the locus, and it is NOT missed here.
    # It minted one node standing for a stretch, because an entry could be dated
    # to a stretch and `Moment.at_or_after` had to decide whether such a claim
    # was visible. Nothing is dated to anything now, so the two endpoints are
    # just two moments and a recogniser carries them itself. `bundle.ugm` says
    # exactly this where the span rules used to be: *§11's recognitions over a
    # stretch are still sayable -- the claim is deposited now, like every other
    # claim, rather than dated to the stretch.* This is that sentence, run.
    src = chr(10).join([
        "rule <round> = implies(",
        "  { asking(?q), anc(?q, ?m), in_delta(?m, ?e),",
        "    entry_of(?e, turn(hero, ?r), plus) },",
        "  { round_span(?r, ?m, ?q) } )",
        "rule <heard> = implies(",
        "  { round_span(?r, ?a, ?b), anc(?b, ?m), anc(?m, ?a),",
        "    in_delta(?m, ?e), entry_of(?e, arrived(?c, ?what, ?sign), plus) },",
        "  { heard(?r, ?c) } )",
        "rule <silent> = implies( { round_span(?r, ?a, ?b), -heard(?r, player) },",
        "                        { silent(?r, player) } )",
        "rule <hero-acts>  = implies( { silent(?r, player), +turn(hero, ?r) },",
        "                             { +attacks(hero, ?r) } )",
        "rule <hero-holds> = implies( { +says(player, hold(hero), ?g), +turn(hero, ?r) },",
        "                             { +holds(hero, ?r) } )",
        "fact +turn(hero, 1)", ""])

    def round_of(declare: bool):
        m = Machine()
        kb = load(m, src)
        if declare:
            kb.say("player", "hold(hero)")
        m.run(limit=60)
        # ⚠ A ROUND IS A STRETCH, so it has duration whether or not anyone spoke.
        # Minting the span only when the chain happened to move made silence
        # unrepresentable: there was no span for nothing to have happened in.
        now = m.chain.succeed(m.chain.now, None)
        m.ask_read(now)
        # ⚠ Unfiltered, and it used to be filtered: the bundle shipped two
        # stratum-0 rules of its own and they sat in layer 0. Both went with the
        # locus, so what this enumerates is the corpus's own recognisers and
        # nothing else -- and a bundle rule appearing in layer 0 again would now
        # show up here rather than being quietly dropped.
        layers = [[r.name for r in layer] for layer in m.rules.strata()]
        m.settle_structure()
        m.run(limit=120)
        at = lambda q: m.chain.holds(kb.term(q))
        return layers, at("attacks(hero, 1)"), at("holds(hero, 1)")

    layers, attacks, holds = round_of(declare=False)
    check("§6", "the three recognisers are stratum 0 by §6's own test, and the "
          "layers are DERIVED -- silence must not be decided before what would "
          "refute it has finished deriving",
          layers == [["round"], ["heard"], ["silent"]])
    check("§11", "⭐⭐⭐ *nothing was declared this round* is sayable, with no "
          "negation as failure over an open domain: it is *nothing arrived on "
          "this channel over this stretch*, and the stretch is named by the "
          "entry that opened it",
          attacks == PLUS and holds is None)

    _, attacks2, holds2 = round_of(declare=True)
    check("§9", "...and one word from the player withdraws it -- the default is "
          "a CONDITION the rule states, not a precedence between two rules, "
          "which is the cost the dungeon named",
          attacks2 is None and holds2 == PLUS)


def a_guard_is_an_ordinary_member() -> None:
    """`unless` is *if not*, and *if not* has been built all along. (§12, §21)

    ⭐⭐⭐ An open item that was a NAME rather than a gap. ⚠ What is genuinely
    absent is not unless, it is AMENDMENT AT A DISTANCE -- adding a guard to a
    rule you did not write.

    See docs/design/selftest.md#a-guard-is-an-ordinary-member.
    """
    from .core.text import load

    m = Machine()
    kb = load(m, chr(10).join([
        "rule <regen> = implies( { +wounded(?x), -poisoned(?x) }, { +heals(?x) } )",
        "fact +wounded(hero)", "fact +wounded(ally)",
        "fact +poisoned(hero)", "fact -poisoned(ally)", ""]))
    m.run(limit=80)
    at = lambda p: m.chain.holds(kb.term(p))
    check("§12", "⭐⭐⭐ a negated member IS `unless`: the per-entity exception "
          "that §14's precedence cannot express -- `overrides` is per rule and "
          "per tick, `supersedes` needs a shared consumed entry, and this needs "
          "neither",
          at("heals(ally)") == PLUS and at("heals(hero)") is None)

    # R3, *rules are subjects*: the one thing writing it as a separate FACT
    # would buy. `reify` already deposits every member with its sign and
    # position, so *what would cancel this rule* is an ordinary query.
    said = {m.g.show(e.proposition) for mo in m.chain.moments for e in mo.delta}
    check("R3", "...and it is ASKABLE, which is all a separate `unless` relation "
          "would have bought: what would cancel a rule is a query over `ant` "
          "with a minus sign",
          "ant(<regen>, poisoned(?x), -, 1)" in said)

    # ⚠⚠ Construction and behaviour are two properties and need two checks --
    # `adopt`'s lesson about a grade that was recorded and not obeyed.
    for where, ant_a, ant_b in (
        ("the first", "{ +wounded(?x), -poisoned(?x) }", "{ +stable(?x) }"),
        ("the second", "{ +wounded(?x) }", "{ +stable(?x), -poisoned(?x) }"),
    ):
        m2 = Machine()
        kb2 = load(m2, chr(10).join([
            f"rule <a> = implies( {ant_a}, {{ +stable(?x) }} )",
            f"rule <b> = implies( {ant_b}, {{ +heals(?x) }} )",
            "fact +wounded(hero)", "fact +wounded(ally)",
            "fact +poisoned(hero)", "fact -poisoned(ally)", ""]))
        ra = [r for r in m2.rules.rules if r.name == "a"][0]
        rb = [r for r in m2.rules.rules if r.name == "b"][0]
        composed = m2.rules.compose(ra, rb, "ab")
        carried = any(x.sign == MINUS
                      and m2.g.show(x.pattern).startswith("poisoned")
                      for x in composed.antecedent)
        apps = match(m2.g, m2.chain, composed,
                     structural=structural_relations(m2.chain))
        reaches = {m2.g.show(v) for a in apps for v in a.bindings.values()
                   if m2.g.show(v) in ("hero", "ally")}
        check("§21", f"⭐ guard inheritance is COMPLETE -- a guard in {where} "
              "constituent is carried by CONSTRUCTION, because composition takes "
              "the union of the antecedents and a guard is one of them",
              carried)
        check("§21", f"...and OBEYED: the composite declines the poisoned case, "
              f"with the guard in {where} constituent", reaches == {"ally"})


# ⚠⚠⚠ DELETED WITH THE LOCUS: `a_span_is_a_locus`, and this is the LARGEST
# single loss of the cut. Eleven checks, and §11's *a locus is a moment or a
# span* went with the locus that the "or" was about.
#
# What a span WAS: one interned node with two members, minted by `Chain.span`,
# refusing an inverted or degenerate stretch at the minting site. An entry could
# be dated to it, and `Moment.at_or_after` consulted the bundle's `<span-
# complete>`/`<span-itself>` to decide whether such a claim was visible from a
# moment. `bundle.ugm` carries the argument for why all of that is gone: an
# entry has no locus, so nothing can be about a stretch, and there is nothing
# for the policy to decide.
#
# The checks, so each is findable from the thing that used to prove it:
#
#   §11  a span is a node with two members, and it is INTERNED
#   §11  an INVERTED span is refused where it is minted, and so is a degenerate
#        one -- two ways to say one locus is the ambiguity the read cannot afford
#   §10  a recognition over a stretch is an ordinary fact once the stretch is
#        OVER -- and not before it is over
#   §11  ⭐⭐⭐ a claim about an INSTANT does not become a claim about a stretch.
#        The load-bearing refusal: inheriting it would answer *did it hold
#        throughout* from an entry that cannot see a denial in the middle
#   §10  ⭐⭐⭐ two recognitions over DIFFERENT stretches are both in view --
#        `_state` was keyed by `(proposition, span)` for this, and its comment
#        records the collapse to `proposition` alone
#   §8   ⭐⭐⭐ a rule concludes at the locus its antecedent bound: `+noted(?p)
#        at ?mp` lands where the act was, not where the frame is
#   §13  ⭐⭐⭐ **THE DESIGN DOCUMENT'S OWN WORKED EXAMPLE RAN HERE** -- *taking
#        turns* recognised over all ten stretches it holds over, by a recursive
#        stratum-0 definition whose base case is two turns and whose step
#        consumes one and defers the rest, with the argument swap carrying the
#        alternation. §11's *DESCRIBED, never enumerated* went with it.
#   §18  ...and quiescence asked at the consequent's own LOCUS, or the recursion
#        halted after its first recognition with everything green
#
# ⭐ What survives, and it is not nothing: `silence_over_a_stretch_is_sayable`
# is the same claim without the span node -- a recogniser carries its two
# endpoints itself and deposits an ordinary claim. That is `bundle.ugm`'s
# *§11's recognitions over a stretch are still sayable*, run. What is NOT
# recovered by it is the part that made a span a LOCUS: dating a claim to a
# stretch, and therefore telling *it held throughout* from *it held then*.
# ⚠⚠⚠ That distinction has no replacement anywhere in the tree. `docs/todo.md`
# carries it as the sharpest open question of the scratchpad design.


def worked_examples() -> None:
    """§8's rules, as printed in the design, actually run."""
    import os

    from .core.text import load_file

    path = _corpora.path("worked.ugm")
    m = Machine()
    kb = load_file(m, path)
    authored = [r for r in m.rules.rules if r not in m.bundle]
    check("§8", "the document's worked rules parse", len(authored) == 3)

    steps = m.run(limit=30)
    check("§15", "and run to quiescence", steps[-1].state == "quiescent")

    check("§8", "<R1> concluded", m.holds(kb.term("boiling(kettle)")) == PLUS)
    check("§6", "including its negative member", m.holds(kb.term("liquid(kettle)")) == MINUS)
    # ⚠ `<R2>` concludes `likely(rain(...))` where it used to conclude
    # `rain(...) @likely`. The bare claim is reached only through `<cross>`,
    # and that it comes back WRAPPED is what a grade used to say in a field.
    check("§8", "<R2> concluded, and what it concluded says how strongly",
          m.holds(kb.term("likely(rain(monday, afternoon))")) == PLUS)
    check(
        "§12",
        "<R2>'s uncertainty survives crossing: supposed bare inside the frame, "
        "carried back out wrapped -- weakest link as structure",
        m.holds(kb.term("rain(monday, afternoon)")) is None,
    )

    # The trust rule's consequent is a bare variable: whatever the channel says.
    raining = kb.term("likely(raining(here))")
    check("§13", "a rule whose consequent is a variable believes what a channel said", m.holds(raining) == PLUS)
    e = m.chain.resolve(raining)
    check("§13", "the channel in the rule is the channel delivered on", e is not None and any(t.source == kb.term("user") for t in m.chain.trail(e)))
    check("R5", "the trail reaches the utterance", len(m.why(raining)) > 1)


def rules_as_data() -> None:
    """§14: a rule is a node, so a rule can be matched by a rule -- once what a
    rule IS has been deposited as entries."""
    from .core.text import load

    src = chr(10).join([
        "rule <a> = implies( { +p(x) }, { +q(x) } )",
        "rule <b> = implies( { +q(x) }, { +r(x) } )",
        "rule <lift> = implies( { +likely(?u), +ant(?rl, ?u, plus, ?i), "
        "+con(?rl, ?v, plus, ?j) },",
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
    check("§13", "its patterns are MENTIONED, not used", m.holds(kb.term("ant(<a>, p(x), plus, 0)")) == PLUS)

    m.run(limit=30)
    check("§14", "one generic rule lifts modality across the bare pipeline", m.holds(kb.term("likely(r(x))")) == PLUS)
    check("§12", "and the guard holds: the bare conclusion was never asserted", m.holds(kb.term("r(x)")) is None)

    ok = False
    try:
        m.gate.write(m.g.rel(m.g.atom("f"), m.g.var("?z")), PLUS)
    except ValueError:
        ok = True
    check("§13", "mention is a gate parameter, not a hole in the gate", ok)


def backward_reading() -> None:
    """R1: one statement, two readings. R2: the reading is recoverable, because
    a subgoal is licensed `wanted` and a conclusion `applied`."""
    from .core.text import load

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
    # R2 -- the reading stays recoverable -- but it moved from the licence to
    # the trail when the phase went, and that is worth stating rather than
    # noticing.
    # → docs/design/selftest.md#r2-the-reading-stays-recoverable-but-it-mo
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
    # rather than a refactor: it ran ahead of recall and returned early, so
    # while any goal was unexpanded no ordinary rule could apply.
    # → docs/design/selftest.md#what-the-phase-cost-and-the-reason-retiring-it
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
    from .core.text import load

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
    # ⭐⭐⭐ And it NAMES the tap the plan committed to.
    # → docs/design/selftest.md#and-it-names-the-tap-the-plan-committed-to
    check("§14", "bindings disagree, so the sibling is blocked, not achieved -- "
          "and the report names the binding that made it fail",
          "blocked(under(kettle, sink))" in props(m2, m2.BLOCKED))
    check("§14", "and the false achievement does not appear",
          "achieved(under(kettle, ?t))" not in props(m2, m2.ACHIEVED))


def the_loop_closes() -> None:
    """Plan, act, be wrong, notice. §11 acting, §16 surprise."""
    from .core.text import load

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
    check("R3", "a fact may NAME a rule, though a rule node contains variables",
          len(m.rules.precedence(m.OVERRIDES)) == 1)

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


def recall_is_narrowable() -> None:
    """§19's first slice: recall stops proposing everything, and what narrows it

    is a knob a corpus can set. ⚠⚠⚠ THE prefer TABLE THAT USED TO BE HERE IS
    GONE, AND SO IS THE ORDERING IT FED.

    See docs/design/selftest.md#recall-is-narrowable.
    """
    from .core.text import load

    chain = chr(10).join([
        "rule <a> = implies( { +p(?x) }, { +q(?x) } )",
        "rule <b> = implies( { +q(?x) }, { +r(?x) } )",
        "rule <c> = implies( { +r(?x) }, { +s(?x) } )",
        "rule <d> = implies( { +u(?x) }, { +v(?x) } )",
        "rule <e> = implies( { +m(?x) }, { +n(?x) } )",
        "fact +p(a)",
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

    m1, kb1, _ = run(chain, 3)
    check("§19", "a narrowed recall reaches the same conclusion",
          m1.holds(kb1.term("s(a)")) == PLUS)

    # A ranking that ended in a set would make two runs of one corpus differ with
    # nothing recording why. This project has hit that bug; the tie-break is
    # authored order, the same one arbitration uses.
    a, _, sa = run(chain, 3)
    b, _, sb = run(chain, 3)
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
    # → docs/design/selftest.md#could-that-have-failed-not-on-this-fixture-any
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

    # ⚠⚠⚠ A FIXTURE THAT WAS BUILT, RUN, AND NEVER ASSERTED ON.
    # → docs/design/selftest.md#a-fixture-that-was-built-run-and-never-a


def the_better_move_wins() -> None:
    """Given several applicable rules, choose the best one -- and *best* has to

    mean something the agent can point at. Before this, the tie among
    applicable, undefeated rules was broken by the order they happened to be
    written in. ⚠ <relevant> IS GONE WITH prefer, AND THE MOVE GOES BACK TO
    AUTHORED ORDER.

    See docs/design/selftest.md#the-better-move-wins.
    """
    from .core.text import load

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
        "the agent still works out for itself which rule serves its goal -- the "
        "backward reader says so in `fits`, and that is untouched",
        m.holds(kb.term("fits(<toward>, nearer(a))")) == PLUS
        and m.holds(kb.term("fits(<wander>, nearer(a))")) is None,
    )
    # ⚠⚠⚠ ...and it no longer ACTS on it. This check used to read *and without
    # `<relevant>` the authored order picks the useless one* and was the
    # control; the control is now the behaviour. Stated as a loss, in the
    # fixture that used to demonstrate the gain, because a retirement whose cost
    # is only in a handoff is a retirement nobody can measure later.
    check(
        "§14",
        "⚠⚠⚠ ...and with `<relevant>` retired it does NOT act on it: knowing "
        "which rule serves the goal and preferring it were two things, and only "
        "the first survives keying on nodes",
        move == "wander",
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
    from .core.text import load

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
        m.gate.write(kb.term("at(home)"), PLUS)
        m.run(limit=600)
        return m, kb

    m, kb = plan()
    check(
        "§15",
        "an action's declared outcome carries the plan forward -- no plan machinery",
        m.holds(kb.term("inside(work)")) == PLUS,
    )
    check(
        "§15",
        "⚠⚠⚠ ...and with situations gone the agent ACTS while it plans: there is no "
        "hypothesis to plan inside, so `doing` emits. Planning without acting is now "
        "a corpus's discipline -- conclude something that is not `doing` until the "
        "decision to act has been taken",
        m.emitted != [],
    )

    # A corpus can NAME a bundled rule. Every section that says *a corpus can
    # override this* depended on it, and none of it was true: the loader knew
    # only the names a corpus declared itself, so the bundle shipped as data and
    # was reachable only from Python.
    m2, kb2 = plan("fact overrides(<outcome>, <assert-act>)" + chr(10))
    check(
        "R3",
        "a corpus can name a bundled rule, so the bundle is finally arguable",
        len(m2.rules.precedence(m2.OVERRIDES)) == 1,
    )
    check(
        "§15",
        "...and overriding `<assert-act>` substitutes the call: only the outcome is asserted",
        m2.holds(kb2.term("inside(work)")) == PLUS
        and m2.holds(kb2.term("travel(work)")) is None,
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
        m3.holds(kb3.term("greet(bo)")) is None,
    )
    m4, kb4 = plan("rule <wave> = implies( { +at(work) }, { +doing(greet(bo)) } )" + chr(10))
    check(
        "§15",
        "...which it keeps when nothing overrides -- so the check is about defeat, not the act",
        m4.holds(kb4.term("greet(bo)")) == PLUS,
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
        m5.holds(kb5.term("inside(work)")) == PLUS
        and m5.holds(kb5.term("travel(work)")) is None,
    )
    check(
        "§12",
        "...and the undeclared act in the same step keeps its fallback -- which `overrides` could not",
        m5.holds(kb5.term("greet(bo)")) == PLUS,
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
    from .core.text import load

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
    seat = m1.chain.now.node
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

    # ⚠⚠ **What went with situations.** `enough` used to end the BRANCH and not
    # the run when it fired inside a hypothesis -- *is this plan settled* and
    # *is this woken rule done* getting a local answer for free, because a frame
    # was already the unit that could be over. With no frame there is nothing
    # smaller than the run to end, so `enough` always stops the agent.


def no_goal_is_dropped_silently() -> None:
    """An agent that can stop can stop on something it was asked for, and the

    first version of enough did exactly that -- silently (§19).

    See docs/design/selftest.md#no-goal-is-dropped-silently.
    """
    from .core.text import load

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
    from .core.text import load

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
    # so what an agent takes forward is ordinary readable corpus text. ⚠ This
    # world cannot supply a lesson any more, and that is the rewrite showing
    # rather than a fixture going stale.
    # → docs/design/selftest.md#what-is-deposited-is-a-fact-about-the-trail-wha
    check("§19", "an episode with nothing to regret writes nothing -- credit alone "
          "is not a lesson once a lesson has to name a thing rather than a rule",
          m.learned() == [])

    from .learning.learning import Episode as _Ep, world as _world
    ep = _Ep(_world(jug_first=True))
    rows = ep.rows
    check("§19", "what it learned is a corpus, not a weight: readable, editable, and "
          "deniable, which is the only way being wrong in recall stays recoverable",
          rows == ["fact +attention(sink, 3)"])
    # ⚠ This USED to read `a second episode reads it back and reaches the same
    # conclusion` against the kettle world, where the conclusion was reached
    # with or without the rows -- a check that could not fail. Read back here it
    # has to change an outcome to pass.
    again = _Ep(_world(jug_first=True) + chr(10).join(rows) + chr(10))
    check("§19", "a second episode reads it back and the run comes out differently "
          "-- the jug it smashed the first time survives",
          ep.harmed and not again.harmed)
    # ⭐ What transfers is a PART, not a thing. Pruned to its binder the lesson
    # reads *whatever plays the tap's part here* -- so it is checked on a world
    # built out of different objects rather than on a rerun that would have
    # succeeded anyway.
    generic = ep.m.learned(conditional=True)
    fresh = _Ep(_world("pot", "jug2", jug_first=True), "pot", "jug2")
    taught = _Ep(_world("pot", "jug2", jug_first=True)
                 + chr(10).join(generic) + chr(10), "pot", "jug2")
    check("§19", "and the lesson GENERALISES: a rule keyed on what plays the tap's "
          "part saves a jug in a world of objects it was never told about",
          fresh.harmed and not taught.harmed
          and any("+attention(?" in r for r in generic))
    # ⚠⚠⚠ **The second half of this check is DELETED with the option-set loop.**
    # It measured `_choose`'s recall budget -- how a narrowed shortlist ranked
    # the apparatus -- by spying on a method the table loop does not call, using
    # `ugm.workload` as its corpus. Both are gone (20l). What remains is the
    # half about the LESSON, which is about what was learned rather than about
    # which function the loop happened to call.

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
    from .core.text import load

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

    # -- and what rooted does NOT unblock, which is the finding ---------- ⚠⚠⚠
    # Checking a root goal for SATISFACTION needs one more thing, and it is not
    # rootedness.
    # → docs/design/selftest.md#and-what-rooted-does-not-unblock-which-is
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

    ⭐⭐⭐ The request never needed to be fresh. The ENTRY did.

    See docs/design/selftest.md#a-request-can-be-re-asked.
    """
    from .core.text import load

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
          # ⚠ A BOUND rather than an exact count, because the exact count is a
          # property of the loop and not of re-asking: the option-set loop takes
          # 16 and the table loop 19, the three being doubts deposited and
          # settled. What the check is for is that a re-ask is not a second
          # SEARCH, and a second search is nowhere near this cheap -- so the
          # bound still bites while the constant stops being a loop's signature.
          len(steps) <= 20)

    # ⭐⭐ And it is bound the way a TOOL is, not the way the other eight
    # write-time hooks are -- so a corpus can see it and retire it. ⚠ The
    # criterion for which hooks may follow, because it is not all of them: a
    # capability whose absence is the status quo ante is safe to retire.
    # → docs/design/selftest.md#and-it-is-bound-the-way-a-tool-is-not-the-wa
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

    # ⚠⚠⚠ WHEN may a request be re-asked, and it is not free choice. An
    # occasion the re-asking itself can produce warrants the next re-ask, which
    # produces the occasion after that.
    # → docs/design/selftest.md#when-may-a-request-be-re-asked-and-it-is
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

    def oracle(machine, e):
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

    The agent has always narrowed which rules come to mind: dormant until
    something claims due. It has never narrowed which facts do. ⚠ Unloading is
    safe to be wrong about (worst case the domain comes back), which is exactly
    why it may be an ordinary defeasible rule.

    See docs/design/selftest.md#a-domain-can-be-taken-out-of-mind.
    """
    from .core.text import load

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
    owes = m4.chain.resolve(b4.term("owes(acme, 100)"))
    check("§13", "a document declares its name table and its domain separately: "
          "one scope, so the rule and the fact mean the same `owes` -- two "
          "domains, so unloading the data does not unload the rules that read it",
          r4.atom("owes") == b4.atom("owes")
          and owes is not None
          and m4.g.show(owes.source) == "billing")


def its_own_effort_is_reasonable_over() -> None:
    """§21's hidden state, for the counters -- and the user's reason is the right

    one: these should be reasonable over. An agent that reached past its
    shortlist, or was stopped by a bound, knows something about its own effort.
    ⚠ _enter's comment has said *each reports that it was hit rather than
    stopping silently (§13)* since it was written, and the report was
    self.exhausted += 1.

    See docs/design/selftest.md#its-own-effort-is-reasonable-over.
    """
    from .core.text import load

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

    Three knobs are FACTS -- how many rules recall may propose, how deep a
-- for a reason the design states
    out loud: *how careful am I being is a claim with a trail, and a rule can
    raise it before an irreversible step.* As Python fields they were the one
    kind of decision this design does not allow: one nobody can ask about.

    ⚠ `tolerance(n)` was the fourth and is RETIRED. Its only reader was
    `_close`, which compared two `prefer` scores, and both went with the buffs.
    It was left parseable for a while on the argument that a corpus should be
    able to say a number -- but a number nothing reads is not a claim, it is
    decoration, so it is gone. ⚠ `depth(n)` and `hypotheses(n)` went the same
    way and for the same reason, with situations: both were read only by
    `_enter`, which bounded supposing.

    ⚠ The DEFAULT stays in Python. A default nobody has to choose is not a
    hidden decision; it is the absence of one.
    """
    from .core.text import load

    m = Machine()
    load(m, "fact +x(a)" + chr(10))
    check("§15", "with nothing said, the defaults hold and no constant was chosen",
          m._knob(m.BUDGET, m.recall_budget) is None)

    c = Machine()
    load(c, "fact budget(3)" + chr(10))
    check("§21", "⭐ a corpus can turn it, so *how careful am I being* is "
          "answerable rather than compiled in",
          c._knob(c.BUDGET, c.recall_budget) == 3)

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
    # A denial turns it off again, because it is an ordinary claim.
    off = Machine()
    load(off, chain + chr(10).join(["fact budget(1)", "fact -budget(1)", ""]))
    off.run(limit=400)
    check("§9", "...and denying it restores the default, since it is a fact like "
          "any other", off.widenings == 0)


def a_session_can_be_saved_and_resumed() -> None:
    """A session is **what it was told**, and §3's determinism is why that is

    enough. Measured before building it: the same corpus reproduces the same
    619 entries byte for byte, across four PYTHONHASHSEEDs. ⚠ Replaying a
    session must not re-do it.

    See docs/design/selftest.md#a-session-can-be-saved-and-resumed.
    """
    import json
    import os
    import tempfile

    from .core.text import load

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
    from .core.text import load

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
    from .core.text import load

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
    m.gate.write(p, PLUS)
    m.gate.write(q, PLUS)
    m.gate.write(p, PLUS)   # ...and claim the first one again
    order = [e.proposition for e in m._state()]
    check("§18", "a proposition claimed again is the most recent in the state, "
          "which is what *a description with two candidates resolves to the most "
          "recent* rests on -- the order is semantics, not a detail of the walk",
          order and order[0] == p and order.index(p) < order.index(q))

    # ⚠⚠⚠ TWO of this group's three checks were about the two indices, and both
    # are gone with the locus. They were:
    #
    #   a later DEPOSIT about an earlier LOCUS does not displace a claim about a
    #   later one -- latest locus first, and only then latest deposit
    #   a claim about a moment later than what I am reasoning ABOUT is not in
    #   that moment's state
    #
    # Both were *the kept state reproduces `resolve`'s ordering exactly*, and
    # `resolve`'s ordering is now a list index. What is left to get wrong is the
    # incremental growth itself, which is the check above and the one below.
    m2 = Machine()
    m2.chain.succeed(m2.chain.now, None)
    m2._state()                      # cache built AT the new moment, then grown
    m2.chain.deposit(proposition=p, sign=PLUS)
    m2.chain.deposit(proposition=p, sign=MINUS)
    held = {e.proposition: e.sign for e in m2._state()}
    check("§17", "the later of two claims in one delta governs, incrementally",
          held.get(p) == MINUS)

    # ...and a claim deposited in a LATER moment than the one the cache was
    # built at is picked up, rather than being missed because the cache is keyed
    # by the seat it was built for.
    m3 = Machine()
    m3._state()
    m3.chain.succeed(m3.chain.now, None)
    m3.chain.deposit(proposition=q, sign=PLUS)
    check("§4", "a claim deposited after the state was cached is in it",
          q in {e.proposition for e in m3._state()})


def a_scope_can_span_documents() -> None:
    """§13's name scope, named -- so a book can be more than one document.

    A corpus is a bound, and that is why coreference does not arise in authored
    knowledge: kettle means one node inside the bound by construction, not by
    inference, and a name outside a scope names nothing. ⚠ What this
    deliberately is NOT: sameas(a, b) in the graph.

    See docs/design/selftest.md#a-scope-can-span-documents.
    """
    from .core.text import load

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


# ⚠⚠⚠ DELETED WITH THE LOCUS: `a_rule_can_relate_two_moments`.
#
# *The goblin acts after the hero* (§8, §12, §20), written as `at ?m`:
#
#     rule <order> = implies( { +acts(hero) at ?mh, +acts(goblin) at ?mg },
#                            { +sequence(?mh, ?mg) } )
#
# It proved three things and each is gone for a different reason. That a member
# says WHERE its entry sits, and the locus binds -- `at ?m` is not parseable,
# because an entry has no second time to bind to. That the two moments are
# distinct rather than one bound twice. And, the part that would rot in silence,
# that the locus SURVIVES the round trip through `reify`/`_read_rule` -- the
# twin-trap family, whose fifth appearance this was.
#
# ⭐ The capability is not lost, and this is a queued conversion rather than a
# concession: `in_delta`, `anc`, `entry_of` and `sanc` are ordinary structural
# relations, so the same rule is writable in a corpus and answers the same. It
# was PROBED before this was deleted, not assumed --
#
#     rule <after> = implies( { asking(?s), anc(?s, ?mq), in_delta(?mq, ?eq),
#                               entry_of(?eq, acts(?q), plus),
#                               anc(?s, ?mp), in_delta(?mp, ?ep),
#                               entry_of(?ep, acts(?p), plus),
#                               sanc(?mq, ?mp) },
#                            { acted_after(?q, ?p) } )
#     → acted_after(goblin, hero)
#
# ⚠ What that version is NOT the same as: it is stratum 0, so its conclusion is
# MINTED structure rather than a deposited entry, and `_state()` will not show
# it. `docs/todo.md` carries the conversion.


def a_computation_happens_inside_the_application() -> None:
    """Arithmetic in the antecedent, and the transfer becomes atomic. (§12, §22)

    A computator is a function given VALUES and returning a value.

    See docs/design/selftest.md#a-computation-happens-inside-the-application.
    """
    from .core.text import Loader

    m = Machine(); kb = Loader(m)
    kb.computator("minus", lambda a, b: int(a) - int(b))
    kb.computator("plus", lambda a, b: int(a) + int(b))
    kb.load(chr(10).join([
        "rule <watch> = implies( { +purse(hero, ?x), +purse(smith, ?y) },",
        "                       { +total(?x, ?y) } )",
        "fact standing(<watch>)",
        "rule <pay> = causes(",
        "    { +pays(?a, ?b, ?n), +purse(?a, ?x), +purse(?b, ?y),",
        "      minus(?x, ?n) as ?x2, plus(?y, ?n) as ?y2 },",
        "    { ? purse(?a, ?x), +purse(?a, ?x2),",
        "      ? purse(?b, ?y), +purse(?b, ?y2), -pays(?a, ?b, ?n) } )",
        "fact +purse(hero, 10)", "fact +purse(smith, 5)",
        "fact +pays(hero, smith, 3)", ""]))
    m.run(limit=300)
    sums = sorted({sum(int(v) for v in m.g.show(e.proposition)[6:-1].split(", "))
                   for e in m._state() if e.sign == PLUS
                   and m.g.show(e.proposition).startswith("total(")})
    check("§22", "⭐⭐⭐ the transfer is ATOMIC: the same standing observer that "
          "saw twelve gold where fifteen existed never sees it again",
          sums == [15])
    check("§12", "...and the arithmetic happened -- 10 and 5 became 7 and 8, "
          "in one application",
          m.holds(kb.term("purse(hero, 7)")) == PLUS
          and m.holds(kb.term("purse(smith, 8)")) == PLUS)

    # ⚠ A computator consumes no ENTRY, so it contributes nothing to the trail.
    # That is the honest record rather than a gap: nothing was matched. The
    # antecedent has five members and three of them are entries.
    deposited = [e for e in m._state() if e.sign == PLUS
                 and m.g.show(e.proposition) == "purse(hero, 7)"]
    check("§12", "...and a computed member consumes no entry, because it "
          "matched none: five members, three on the trail",
          bool(deposited) and len(deposited[0].consumed) == 3)

    # The arguments must be ground when it runs, so a computator member only
    # computes once earlier members have bound them -- here n(?x) is DERIVED,
    # so the rule matches from a delta rather than on the opening pass. ⚠ The
    # engine also skips pivoting on a computator, and that is an OPTIMISATION
    # rather than a correctness fix -- measured both ways, the results are
    # identical...
    # → docs/design/selftest.md#the-arguments-must-be-ground-when-it-runs-so-a
    m2 = Machine(); kb2 = Loader(m2)
    kb2.computator("double", lambda a: int(a) * 2)
    kb2.load(chr(10).join([
        "rule <mk> = implies( { +seed(?s) }, { +n(?s) } )",
        "rule <d> = implies( { +n(?x), double(?x) as ?y }, { +twice(?x, ?y) } )",
        "fact +seed(4)", ""]))
    m2.run(limit=60)
    check("§4", "...and it matches from a DELTA too, once earlier members have "
          "bound what it computes from",
          m2.holds(kb2.term("twice(4, 8)")) == PLUS)


def a_member_can_name_what_it_matched() -> None:
    """`+on(?x, ?y) as ?t` -- reference, not description. (§8, §12)

    `at ?m` said WHERE an entry sits and went with the locus; `as ?t` says WHAT
    it says, under a name, and stays -- it was never about a second time. Same
    one-line mechanism, and it answers a question that had two unsatisfying
    answers before it. ⚠ And two members hoping to co-refer -- +tagged(?t),
    +on(?x, ?y) -- is coincidence, not reference: nothing links them, and it
    appears to work only while there...

    See docs/design/selftest.md#a-member-can-name-what-it-matched.
    """
    from .core.text import load

    m = Machine()
    kb = load(m, chr(10).join([
        "rule <r> = implies( { +on(?x, ?y) as ?t, +thing(?x) },",
        "                   { +about(?t, ?x) } )",
        "fact +on(a, b)", "fact +thing(a)", ""]))
    m.run(limit=60)
    got = [e for e in m._state() if e.sign == PLUS
           and m.g.show(e.proposition).startswith("about(")]
    check("§12", "⭐ a member names what it matched, so a rule refers to the "
          "proposition instead of describing it again",
          [m.g.show(e.proposition) for e in got] == ["about(on(a, b), a)"])
    check("§8", "...and it is the SAME node, so this is reference and not a "
          "copy -- propositions have one identity however often built",
          bool(got) and m.g.member(got[0].proposition, 0) is kb.term("on(a, b)"))

    # ⚠⚠⚠ Same argument as the locus, and the fifth time it has been made: a
    # slot `reify` does not record is one `adopt` and `compose` drop, and the
    # rule that comes back is a different rule.
    r = [x for x in m.rules.rules if x.name == "r"][0]
    built = m._read_rule(r.node)
    check("§20", "...and it survives the round trip through the graph",
          built is not None
          and [x.binds for x in built[1]] == [x.binds for x in r.antecedent])


# ⚠⚠⚠ DELETED WITH THE LOCUS: `the_skeleton_is_an_ordinary_member`.
#
# Three fixtures (§5, §6, §11, §12), and all three bound a moment with `at ?m`:
#
#     <after>  +acts(?p) at ?mp, +acts(?q) at ?mq, sanc(?mq, ?mp)
#              → acted_after(goblin, hero)   -- an ordinary rule matches the
#                SKELETON directly: no request, no answerer, no second matcher
#     <down>   +acts(?p) at ?mp, +step2(x), sanc(?any, ?mp)
#              → a DOWNWARD pattern is not refused: it loads and finds nothing
#                even where descendants exist, so *nothing is prohibited* holds
#     <reach>  +noted(?x) at ?mx, sanc(?mx, ?up)
#              → and it holds STRUCTURALLY: every moment a structural member
#                reached is on the walk of the entry its conclusion sits in
#
# The third also read `e.locus.at_or_after(up)` in Python, and there is no
# locus to walk from.
#
# ⭐ The HEADLINE claim is not uncovered: `the_matchers_are_one` and the seven
# groups around it run stratum-0 rules over `asking`/`anc`/`pred`/`in_delta`/
# `entry_of` and are untouched by this. What goes with these three is the part
# that bound a moment from an ORDINARY member -- which is the same thing
# `a_rule_can_relate_two_moments` lost, and the same conversion recovers it.
# `docs/todo.md` carries both.

def the_matchers_are_one() -> None:
    """§5's *one interpreter* and §6's *one more row, not one more branch*, made
    true of the code rather than of the intent.

    `stratum0.py` is deleted. It was a second engine -- its own rule type, its
    own item type, its own solver -- matching the very same nodes, and §6
    explicitly disclaims it. What replaces it is ordinary rules under the
    ordinary matcher, and `ugm.agreement` runs the whole read that way.

    Three things had to exist, and each is §6's own sentence made operational
    rather than a construct invented for it. The checks below are for the two
    that are engine, not corpus.
    """
    from .core.text import load

    # ⭐⭐⭐ §6's test decides WHERE A CONCLUSION LANDS. *Every antecedent member
    # is structural* is computable, so a rule that reads only structure
    # concludes structure -- which is §6's price (*stratum 0 must produce
    # structure, not entries*) charged by §6's own definition.
    m = Machine()
    kb = load(m, chr(10).join([
        "rule <up> = implies( { asking(?s), anc(?s, ?a) }, { above(?s, ?a) } )",
        "rule <ord> = implies( { +seen(?x) }, { +noted(?x) } )",
        "fact +seen(a)", ""]))
    up = [r for r in m.rules.rules if r.name == "up"][0]
    ord_ = [r for r in m.rules.rules if r.name == "ord"][0]
    check("§6", "⭐⭐⭐ §6's test is computable, so the strata are DERIVED and not "
          "assigned: a rule reading only structure is stratum 0, one reading an "
          "entry is not",
          m.rules.is_stratum0(up) and not m.rules.is_stratum0(ord_))

    # ⚠⚠⚠ Driven by the ORDINARY LOOP, not by `settle_structure`. The first
    # version of this check ran the settler, which calls `_mint_structure`
    # directly -- so a kill-probe removing the branch in `_conclude` broke
    # nothing and the check passed for the wrong reason. `_conclude` is the path
    # that matters: it is where a stratum-0 rule reached by ordinary recall
    # would otherwise deposit a claim and reinstate §6's circle. A check about
    # which of two paths is taken has to take the path.
    m.chain.succeed(m.chain.root, None)
    m.ask_read(m.chain.moments[-1])
    m.run(limit=60)
    above = kb.term("above")
    facts = [n for n in m.g.instances_of(above) if not m.g.has_var(n)]
    check("§6", "⭐⭐⭐ ...and its conclusion is STRUCTURE -- an interned relation "
          "instance, so the read does not deposit claims and §6's circle stays "
          "closed, on the ORDINARY loop's path and not only the settler's",
          len(facts) > 0
          and not [e for e in m._state()
                   if m.g.relation_of(e.proposition) == above])

    # ⚠ Interning is what makes the fixpoint detectable, and the count has to
    # be taken BEFORE substitution -- substitute builds the grounded node with
    # g.rel, which interns, so a novelty test made afterwards always finds the
    # fact already present.
    # → docs/design/selftest.md#interning-is-what-makes-the-fixpoint-detectabl
    m.settle_structure()
    check("§6", "⚠ a stratum-0 fixpoint that has settled derives NOTHING on a "
          "second run -- the novelty test survives interning",
          m.settle_structure() == 0)

    # ⭐⭐⭐ Negation as failure, and it needed no notation. On an ordinary member
    # a sign says what an entry claims; a structural member has no entry, so the
    # only thing a sign can mean there is *not derived*.
    m2 = Machine()
    kb2 = load(m2, chr(10).join([
        "rule <r1> = implies( { asking(?s), anc(?s, ?a) }, { reach(?s, ?a) } )",
        "rule <r2> = implies( { asking(?s), pred(?s, ?p) }, { near(?s, ?p) } )",
        "rule <r3> = implies( { reach(?s, ?a), -near(?s, ?a) }, { far(?s, ?a) } )",
        ""]))
    a = m2.chain.succeed(m2.chain.root, None)
    b = m2.chain.succeed(a, None)
    m2.ask_read(b)
    m2.settle_structure()
    far = kb2.term("far")
    reached = {m2.g.members(n)[1]
               for n in m2.g.instances_of(kb2.term("reach"))
               if not m2.g.has_var(n)}
    got = {m2.g.members(n)[1]
           for n in m2.g.instances_of(far) if not m2.g.has_var(n)}
    check("§6", "⭐⭐⭐ a MINUS on a structural member is negation as failure, and "
          "needs no notation -- there is no entry for a sign to be a claim about",
          got == reached - {a.node} and b.node in got)

    # ⚠⚠⚠ And it is safe only because the strata are ORDERED. `far` negates
    # `near`; run in one layer, `far` is derived against a half-built `near` and
    # the answer depends on the order the rules were tried. Structure has no
    # sign, so a wrong one cannot be taken back -- an entry would merely be
    # superseded. The layering is what makes the negation mean what it says.
    layers = m2.rules.strata()
    names = [[r.name for r in L] for L in layers]
    check("§6", "⚠⚠⚠ ...and the negated relation is settled in an EARLIER layer, "
          "because structure has no sign and a wrong fact cannot be denied",
          len(names) > 1 and "r3" in names[-1] and "r2" in names[0])

    # ⚠ Recursion is not a cycle to be refused -- dep_after is transitive and
    # reads itself -- but negation INSIDE a recursion has no stratification at
    # all, and refusing it loudly is the only honest answer.
    # → docs/design/selftest.md#recursion-is-not-a-cycle-to-be-refused-dep
    m3 = Machine()
    load(m3, chr(10).join([
        "rule <x> = implies( { asking(?s), anc(?s, ?a) }, { p(?s, ?a) } )",
        "rule <y> = implies( { p(?s, ?a), -q(?s, ?a) }, { q(?s, ?a) } )",
        ""]))
    lone = [r for r in m3.rules.rules if r.name == "y"][0]
    check("§6", "⚠⚠ a relation that appears ONLY negated in its own definition "
          "never enters the skeleton -- the fixpoint works from below, so it is "
          "not stratum 0 and there is nothing to stratify",
          not m3.rules.is_stratum0(lone) and m3.rules.strata())

    m3b = Machine()
    load(m3b, chr(10).join([
        "rule <x> = implies( { asking(?s), anc(?s, ?a) }, { p(?s, ?a) } )",
        "rule <q0> = implies( { p(?s, ?a) }, { q(?s, ?a) } )",
        "rule <y> = implies( { p(?s, ?a), -q(?s, ?a) }, { q(?s, ?a) } )",
        ""]))
    try:
        m3b.rules.strata()
        refused = False
    except ValueError:
        refused = True
    check("§6", "⚠ ...and once it IS structure, negating it recursively is "
          "refused, naming itself -- there is no order over it that gives one "
          "answer",
          refused)

    # ⚠⚠⚠ `pred` was the reflexive-transitive walk under the name of the
    # immediate one. Registered for corpora to write, and written by nothing, so
    # nothing could see it. A name whose meaning is not what the name says is
    # worse than an absent one: a corpus that used it would have been right to
    # trust it.
    m4 = Machine()
    kb4 = load(m4, chr(10).join([
        "rule <p> = implies( { asking(?s), pred(?s, ?x) }, { parent(?s, ?x) } )",
        "rule <a> = implies( { asking(?s), anc(?s, ?x) }, { ancestor(?s, ?x) } )",
        ""]))
    c0 = m4.chain.root
    c1 = m4.chain.succeed(c0, None)
    c2 = m4.chain.succeed(c1, None)
    m4.ask_read(c2)
    m4.settle_structure()
    parents = {m4.g.members(n)[1] for n in m4.g.instances_of(kb4.term("parent"))
               if not m4.g.has_var(n)}
    ancestors = {m4.g.members(n)[1]
                 for n in m4.g.instances_of(kb4.term("ancestor"))
                 if not m4.g.has_var(n)}
    check("§11", "⚠⚠⚠ `pred` is the IMMEDIATE predecessor and `anc` is the "
          "reflexive walk -- one name, one meaning, and `pred` used to be the "
          "walk",
          parents == {c1.node} and ancestors == {c0.node, c1.node, c2.node})

    # ⚠⚠⚠ A fixpoint has to be shown to REACH one, and *nothing new on the
    # second run* cannot show it: a novelty test that never fires satisfies
    # that trivially, and the kill-probe proved it -- breaking novelty broke
    # zero checks.
    # → docs/design/selftest.md#a-fixpoint-has-to-be-shown-to-reach-one
    m6 = Machine()
    kb6 = load(m6, chr(10).join([
        "rule <p1> = implies( { asking(?s), pred(?s, ?x) }, { step(?s, ?x) } )",
        "rule <p2> = implies( { step(?a, ?b), pred(?b, ?c) }, { step(?a, ?c) } )",
        ""]))
    walk_up = [m6.chain.root]
    for _ in range(5):
        walk_up.append(m6.chain.succeed(walk_up[-1], None))
    m6.ask_read(walk_up[-1])
    m6.settle_structure()
    steps = {m6.g.members(n)[1] for n in m6.g.instances_of(kb6.term("step"))
             if not m6.g.has_var(n)}
    check("§6", "⚠⚠⚠ the stratum-0 fixpoint REACHES one -- a transitive closure "
          "five deep is complete, which *nothing new on the second run* cannot "
          "show and a broken novelty test satisfies trivially",
          steps == {mo.node for mo in walk_up[:-1]})

    # ⭐⭐⭐ A fact's own history, on the ORDINARY loop, ending in a claim.
    # → docs/design/selftest.md#a-fact-s-own-history-on-the-ordinary-loop
    m7 = Machine()
    kb7 = load(m7, chr(10).join([
        # ⚠ The order used to be `sanc(?l2, ?l1)` over the two entries' LOCI.
        # An entry has no locus, so the order is over the moments they were
        # deposited in -- which is the only time there is now, and which is
        # exactly what `resolve` reads.
        "rule <flip> = implies(",
        "  { asking(?s), anc(?s, ?d1), in_delta(?d1, ?e1),",
        "    entry_of(?e1, ?p, plus),",
        "    anc(?s, ?d2), in_delta(?d2, ?e2),",
        "    entry_of(?e2, ?p, minus), sanc(?d2, ?d1) },",
        "  { flipped(?p) } )",
        "rule <note> = implies( { flipped(?p), +watching(x) },",
        "                      { +changed(?p) } )",
        "fact +watching(x)", ""]))
    door = m7.g.rel(m7.g.atom("open"), m7.g.atom("door"))
    d1 = m7.chain.succeed(m7.chain.root, None)
    m7.gate.write(door, "+")
    m7.chain.succeed(d1, None)
    m7.gate.write(door, "-")
    steps = m7.run(limit=60)
    changed = [e for e in m7._state()
               if m7.g.relation_of(e.proposition) == kb7.term("changed")]
    check("§6", "⭐⭐⭐ a fact's OWN HISTORY is matchable -- *it was on, then it was "
          "not* reads the raw chain, concludes structure, and an ordinary rule "
          "turns it into a claim",
          len(changed) == 1
          and m7.g.show(changed[0].proposition) == "changed(open(door))")

    # ⚠⚠⚠ ...and it STOPS. Quiescence asks `resolve` about what a rule would
    # write; a stratum-0 conclusion never enters the chain, so `resolve` answers
    # None for ever and the verdict is *yes, this changes something* on every
    # tick. Worse, the verdict is cached and retired only when a proposition it
    # READ changes -- and a stratum-0 rule reads none, so the True was permanent.
    # Measured before fixing: 60 ticks of `applied`, identical bindings.
    check("§6", "⚠⚠⚠ ...and the loop goes QUIET on it -- a stratum-0 rule is asked "
          "about the graph, not the state, and its verdict is never cached",
          steps[-1].state == "quiescent" and len(steps) < 10)

    # ⚠⚠⚠ And asking must not answer.
    # → docs/design/selftest.md#and-asking-must-not-answer-for-a-stratu
    m8 = Machine()
    kb8 = load(m8, chr(10).join([
        "rule <up> = implies( { asking(?s), anc(?s, ?a) }, { above(?s, ?a) } )",
        ""]))
    m8.chain.succeed(m8.chain.root, None)
    m8.ask_read(m8.chain.moments[-1])
    from .core.rules import match as _match, Situation as _Sit
    up8 = [r for r in m8.rules.rules if r.name == "up"][0]
    apps = _match(m8.g, m8.chain, up8, _Sit(m8.g, []),
                  computes=m8.rules.computes, structural=m8.rules.skeleton())
    before_n = m8.g.count()
    first = [m8._would_change(a) for a in apps]
    again = [m8._would_change(a) for a in apps]
    check("§6", "⚠⚠⚠ ...and ASKING does not answer: the stratum-0 quiescence "
          "verdict mints nothing, so the same question put twice gets the same "
          "answer and two paths over one state agree",
          first == again and any(first) and m8.g.count() == before_n)


    # ⭐⭐⭐ Containment, with the anchoring discipline doing the work. `in_delta`
    # is bounded by whatever anchored it, so a read seeded at one branch never
    # names an entry on its sibling -- measured on a fork rather than argued.
    m5 = Machine()
    kb5 = load(m5, chr(10).join([
        "rule <mine> = implies( { asking(?s), anc(?s, ?d), in_delta(?d, ?e) },",
        "                      { held(?s, ?e) } )",
        # ⚠⚠⚠ The DISCRIMINATING case, and the check was vacuous without it.
        # → docs/design/selftest.md#the-discriminating-case-and-the-check-was-v
        "rule <loose> = implies( { asking(?s), in_delta(?d, ?e) },",
        "                       { anywhere(?s, ?e) } )", ""]))
    # ⚠ The two writes are INTERLEAVED with the forking, and they have to be:
    # a deposit lands at `chain.now`, which is the latest moment made, so both
    # writes issued after both `succeed`s would land on the right branch and
    # leave the left one empty -- and the check below passes vacuously on an
    # empty reach. It used to be a frame's seat that put them apart.
    r = m5.chain.root
    left = m5.chain.succeed(r, None)
    m5.gate.write(m5.g.rel(m5.g.atom("on"), m5.g.atom("l")), "+")
    right = m5.chain.succeed(r, None)
    m5.gate.write(m5.g.rel(m5.g.atom("on"), m5.g.atom("r")), "+")
    m5.ask_read(left)
    m5.settle_structure()
    reached_entries = {m5.g.members(n)[1]
                       for n in m5.g.instances_of(kb5.term("held"))
                       if not m5.g.has_var(n)}
    sibling = {e.node for e in right.delta}
    check("§17", "⭐⭐⭐ containment holds on a FORK: a read anchored at one branch "
          "reaches no entry on its sibling, because every member is bounded by "
          "what anchored it",
          reached_entries and not (reached_entries & sibling))

    # ⭐ has_var is decided at mint, and an index is a re-implementation of what
    # it indexes.
    # → docs/design/selftest.md#has-var-is-decided-at-mint-and-an-index-i
    drift = 0
    nodes = 0
    for mm in (m7, m5, m2):
        for n in range(mm.g.count()):
            nodes += 1
            if mm.g.has_var(n) != mm.g._has_var_slow(n):
                drift += 1
    check("§3", "⭐ the cached genericity agrees with the walked definition on "
          f"every node three machines built ({nodes})",
          nodes > 0 and drift == 0)

    loose = [n for n in m5.g.instances_of(kb5.term("anywhere"))
             if not m5.g.has_var(n)]
    check("§4", "⚠⚠⚠ ...and an UNANCHORED skeleton member finds nothing rather "
          "than the whole history -- nothing is prohibited, it simply has no "
          "bound to walk from, which is what the fork check needs to be able to "
          "fail",
          not loose)


def a_half_finished_change_is_observable_and_actionable() -> None:
    """A transfer, mid-flight, looks exactly like a finished state. (§8, §19)

    Predicted by a foreign corpus and constructed here. ⚠ And an ordinary rule
    acts on it.

    See docs/design/selftest.md#a-half-finished-change-is-observable-and-actionable.
    """
    from .core.text import Loader

    def calc(mm, e):
        op, a, b = mm.g.members(e.proposition)
        x, y = int(mm.g.show(a)), int(mm.g.show(b))
        return mm.g.atom(str(x - y if mm.g.show(op) == "sub" else x + y))

    BODY = chr(10).join([
        "rule <debit>  = implies( { +pays(?a, ?b), +purse(?a, ?x) },"
        " { +calc(sub, ?x, 3) } )",
        "rule <take>   = causes(  { +pays(?a, ?b), +purse(?a, ?x),",
        "                           +answered(<arith>, calc(sub, ?x, 3), ?r) },",
        "                         { ? purse(?a, ?x), +purse(?a, ?r),"
        " +owed(?b, 3), -pays(?a, ?b) } )",
        "rule <credit> = implies( { +owed(?b, 3), +purse(?b, ?y) },"
        " { +calc(add, ?y, 3) } )",
        "rule <give>   = causes(  { +owed(?b, 3), +purse(?b, ?y),",
        "                           +answered(<arith>, calc(add, ?y, 3), ?r) },",
        "                         { ? purse(?b, ?y), +purse(?b, ?r), -owed(?b, 3) } )",
        "fact +purse(hero, 10)", "fact +purse(smith, 5)",
        "fact +pays(hero, smith)", ""])

    m = Machine(); kb = Loader(m)
    kb.answerer("arith", "calc", calc)
    kb.load("rule <watch> = implies( { +purse(hero, ?x), +purse(smith, ?y) },"
            " { +total(?x, ?y) } )" + chr(10) + "fact standing(<watch>)"
            + chr(10) + BODY)
    m.run(limit=300)
    tot = [m.g.show(e.proposition) for e in m._state()
           if e.sign == PLUS and m.g.show(e.proposition).startswith("total(")]
    sums = sorted(sum(int(x) for x in t[6:-1].split(", ")) for t in tot)
    check("§8", "⚠⚠⚠ a transfer mid-flight is OBSERVABLE: an observer sees a "
          "total that never existed, and nothing contradicts anything",
          12 in sums and 15 in sums)

    # ...and the atomic version, so the check says what is available rather than
    # only what is missing. One application deposits every consequent into one
    # moment, so a transfer needing no tool cannot be caught half-done.
    m2 = Machine(); kb2 = Loader(m2)
    kb2.load(chr(10).join([
        "rule <watch> = implies( { +purse(hero, ?x), +purse(smith, ?y) },"
        " { +total(?x, ?y) } )",
        "fact standing(<watch>)",
        "rule <pay> = causes( { +pays(?a, ?b), +purse(?a, 10), +purse(?b, 5) },",
        "                     { ? purse(?a, 10), +purse(?a, 7),"
        " ? purse(?b, 5), +purse(?b, 8) } )",
        "fact +purse(hero, 10)", "fact +purse(smith, 5)",
        "fact +pays(hero, smith)", ""]))
    m2.run(limit=200)
    tot2 = [m2.g.show(e.proposition) for e in m2._state()
            if e.sign == PLUS and m2.g.show(e.proposition).startswith("total(")]
    sums2 = {sum(int(x) for x in t[6:-1].split(", ")) for t in tot2}
    check("§12", "...while a consequent IS atomic -- a transfer written in one "
          "rule is never caught half-done", sums2 == {15})


def a_reserved_name_no_longer_changes_meaning_silently() -> None:
    """One node with two meanings. (§5, Appendix C)

    Reported by a foreign corpus, which lost a session to it. ⚠ A report and
    not a refusal, and that is forced.

    See docs/design/selftest.md#a-reserved-name-no-longer-changes-meaning-silently.
    """
    from .core.text import load

    m = Machine()
    kb = load(m, "rule <sub> = implies( { +hp(?x,?h) }, { +calc(minus, ?h, 2) } )"
                 + chr(10) + "fact +hp(gob, 5)" + chr(10))
    check("§5", "a corpus naming a reserved node in an argument position is "
          "TOLD -- it used to change meaning in silence",
          "minus" in kb.shadowed)
    # ...and the collision is real, not merely reported: what landed is the sign.
    m.run(limit=40)
    landed = [m.g.show(e.proposition) for e in m._state()
              if m.g.show(e.proposition).startswith("calc(")]
    check("§3", "...and the report is about something true: what landed names "
          "the sign, not a fresh atom", landed and "calc(-," in landed[0])

    m2 = Machine()
    kb2 = load(m2, "rule <ok> = implies( { +hp(?x,?h) }, { +calc(sub, ?h, 2) } )"
                   + chr(10) + "fact cost(sword, 3)" + chr(10))
    check("§5", "...while a corpus that collides with nothing is not nagged, "
          "and a NUMERAL is sharing rather than shadowing", not kb2.shadowed)


def a_relation_can_be_named_by_a_variable() -> None:
    """`?p(?t)` -- the effect named by data. (§3, §5, §12)

    The substrate could always BUILD a relation instance whose relation slot is
    a variable; it is an ordinary generic node. ⚠ The cost is §3's index, and
    it lands only on an ANTECEDENT member.

    See docs/design/selftest.md#a-relation-can-be-named-by-a-variable.
    """
    from .core.text import load

    m = Machine()
    kb = load(m, chr(10).join([
        "rule <resolve> = implies( { +did(?a, ?t), +effect(?a, ?p) }, { +?p(?t) } )",
        "fact effect(fireball, burned)",
        "fact effect(frostbolt, chilled)",
        "fact +did(fireball, goblin)",
        "fact +did(frostbolt, orc)", ""]))
    m.run(limit=80)
    check("§12", "⭐ a rule concludes the relation its antecedent bound, so one "
          "rule serves a catalogue that would otherwise be a fact per pair",
          m.holds(kb.term("burned(goblin)")) == PLUS
          and m.holds(kb.term("chilled(orc)")) == PLUS)
    # ⚠ ...and it does not smear across the catalogue. The kill-probe that
    # matters: bind the relation but not the argument and every spell hits every
    # target, which is the shape a wrong binding takes here.
    # ⚠ The positives are restated here deliberately. Asked about the absences
    # alone this passes when the whole mechanism is off and everything is None
    # -- a check that cannot fail under the mutation it exists for, which is the
    # default rather than the exception in this file.
    check("§4", "...and it binds the pair, not the cross product",
          m.holds(kb.term("burned(goblin)")) == PLUS
          and m.holds(kb.term("chilled(orc)")) == PLUS
          and m.holds(kb.term("burned(orc)")) is None
          and m.holds(kb.term("chilled(goblin)")) is None)
    # A consequent whose RELATION nothing bound is still refused, exactly as
    # one whose argument nothing bound always was -- the gate's rule did not
    # need to learn about this, which is the sign it was the right place for
    # it. ⚠ This used to LOAD and then quietly mint nothing, and the note here
    # said the gate was the right place for it.
    # →
    # docs/design/selftest.md#a-consequent-whose-relation-nothing-bound-is-sti
    from .core.text import ParseError

    m2 = Machine()
    refused = False
    try:
        load(m2, "rule <bad> = implies( { +go(?t) }, { +?p(?t) } )" + chr(10)
             + "fact +go(x)" + chr(10))
    except ParseError:
        refused = True
    check("§17", "...while a consequent whose RELATION nothing bound is refused "
          "at load, like any other unbound consequent", refused)
    # An ANTECEDENT member may name one too -- it just cannot be indexed.
    m3 = Machine()
    kb3 = load(m3, chr(10).join([
        "rule <flee> = implies( { +?p(?t), +dangerous(?p) }, { +run(?t) } )",
        "fact +dangerous(fire)",
        "fact +fire(room)",
        "fact +quiet_thing(room)", ""]))
    m3.run(limit=60)
    check("§3", "...and an antecedent member may name a relation by variable "
          "too, at the price of the index -- it takes the ANY bucket and scans",
          m3.holds(kb3.term("run(room)")) == PLUS)


def a_verb_is_defined_once_and_a_world_is_declared() -> None:
    """Define *buying*; then declare a world in facts. (§3, §12, §20)

    The question this answers is whether an open-class vocabulary buys anything
    an author can feel: can a generic interaction be written once, in no domain
    vocabulary at all, and then a world be *declared* rather than coded?

    See docs/design/selftest.md#a-verb-is-defined-once-and-a-world-is-declared.
    """
    from .core.text import load

    VERB = chr(10).join([
        "rule <can-buy> = implies(",
        "    { +wants(?b, ?item), +sells(?s, ?kind), +?kind(?item),",
        "      +stocks(?s, ?item), +purse(?b, ?coin) },",
        "    { +offer(?b, ?s, ?item) } )",
        "rule <buy> = causes(",
        "    { +offer(?b, ?s, ?item), +purse(?b, ?coin) },",
        "    { +owns(?b, ?item), -stocks(?s, ?item),",
        "      ? purse(?b, ?coin), +falls(purse(?b)) } )", ""])

    def world(extra):
        mm = Machine(); kk = load(mm, VERB + extra); mm.run(limit=200)
        return mm, kk

    m, kb = world(chr(10).join([
        "fact sells(smith, weapon)", "fact +weapon(sword)",
        "fact +stocks(smith, sword)", "fact +purse(hero, 20)",
        "fact +wants(hero, sword)", ""]))
    check("§12", "⭐ a generic verb over a DECLARED world: the smith sells "
          "weapons, a sword is a weapon, and the trade goes through",
          m.holds(kb.term("owns(hero, sword)")) == PLUS
          and m.holds(kb.term("stocks(smith, sword)")) == MINUS)
    # ⚠ And the purse is INVALIDATED, not silently stale -- §16's pair. The
    # first version of this fixture wrote `? purse(?b)` against a `purse(b, n)`
    # fact, so it invalidated a proposition nobody had ever asserted and the
    # old amount went on reading `+`. An arity slip is silent here.
    check("§16", "...and what changed is unreadable rather than stale, because "
          "the rule invalidated the proposition it actually named",
          m.holds(kb.term("purse(hero, 20)")) == UNSURE)

    m2, kb2 = world(chr(10).join([
        "fact sells(armourer, armour)", "fact +armour(shield)",
        "fact +stocks(armourer, shield)", "fact +purse(hero, 20)",
        "fact +wants(hero, shield)", ""]))
    check("§20", "...a whole new trade is FACTS -- new merchant, new class, new "
          "stock, and not one new rule",
          m2.holds(kb2.term("owns(hero, shield)")) == PLUS)

    m3, kb3 = world(chr(10).join([
        "rule <steal> = causes(",
        "    { +covets(?b, ?item), +sells(?s, ?kind), +?kind(?item),",
        "      +stocks(?s, ?item) },",
        "    { +owns(?b, ?item), -stocks(?s, ?item), +angry(?s) } )",
        "fact sells(smith, weapon)", "fact +weapon(sword)",
        "fact +stocks(smith, sword)", "fact +covets(thief, sword)", ""]))
    check("§2", "...and a SECOND verb reuses the same declarations untouched, "
          "which is what open class is for",
          m3.holds(kb3.term("owns(thief, sword)")) == PLUS
          and m3.holds(kb3.term("angry(smith)")) == PLUS)

    m4, kb4 = world(chr(10).join([
        "rule <blades> = implies( { +blade(?x) }, { +weapon(?x) } )",
        "fact sells(smith, weapon)", "fact +blade(dagger)",
        "fact +stocks(smith, dagger)", "fact +purse(hero, 20)",
        "fact +wants(hero, dagger)", ""]))
    check("§13", "...and a class hierarchy is one ordinary rule: the smith "
          "sells daggers, and nothing ever said he did",
          m4.holds(kb4.term("owns(hero, dagger)")) == PLUS)


def an_amount_is_a_tool_and_an_unknown_amount_is_a_node() -> None:
    """*It falls by 3*, and *it rises by an unknown amount*. (§13, §16, §17, §22)

    §22 recorded these as one open item — *a value member that is constrained
    rather than bound*. They are three questions with three answers, and only
    the last is open.

    See docs/design/selftest.md#an-amount-is-a-tool-and-an-unknown-amount-is-a-node.
    """
    from .core.text import Loader

    m = Machine(); kb = Loader(m)

    def minus(machine, entry):
        who, a, b = machine.g.members(entry.proposition)
        return machine.g.rel(kb.atom("purse"), who,
                             kb.atom(str(int(machine.g.show(a))
                                         - int(machine.g.show(b)))))

    kb.answerer("calc", "minus", minus)
    kb.load(chr(10).join([
        "rule <spend> = implies( { +purse(?b, ?n), +buying(?b, ?i), +cost(?i, ?c) },",
        "                        { +minus(?b, ?n, ?c) } )",
        "rule <apply-it> = implies( { +answered(<calc>, minus(?b, ?n, ?c), ?r) },",
        "                        { +?r, ? purse(?b, ?n), -buying(?b, sword) } )",
        "fact +purse(hero, 20)", "fact +buying(hero, sword)",
        "fact cost(sword, 3)", ""]))
    m.run(limit=200)
    check("§17", "⭐ a KNOWN magnitude needs no representation: arithmetic is a "
          "function, so it is a tool, and the purse goes 20 to 17",
          m.holds(kb.term("purse(hero, 17)")) == PLUS
          and m.holds(kb.term("purse(hero, 20)")) == UNSURE)
    # ⚠ The retraction of the trigger is load-bearing, not tidiness: without it
    # the rule debits forever, which is §14's re-ask criterion arriving in a
    # corpus. The first version of this fixture did exactly that.

    m2 = Machine(); kb2 = Loader(m2)
    kb2.load(chr(10).join([
        "rule <pour> = causes( { +level(?g, ?v), +poured(?g) },",
        "                      { ? level(?g, ?v), +greater(after(?g), ?v),",
        "                        +rises(level(?g)) } )",
        "fact +level(glass, 2)", "fact +poured(glass)", ""]))
    m2.run(limit=80)
    check("§13", "⭐ an UNKNOWN magnitude is a node, not a slot: name the "
          "quantity and say what is known of it",
          m2.holds(kb2.term("greater(after(glass), 2)")) == PLUS
          and m2.holds(kb2.term("rises(level(glass))")) == PLUS
          and m2.holds(kb2.term("level(glass, 2)")) == UNSURE)

    m3 = Machine(); kb3 = Loader(m3)
    kb3.load(chr(10).join([
        "rule <pour> = causes( { +level(?g, ?v), +poured(?g) },",
        "                      { ? level(?g, ?v), +greater(after(?g), ?v) } )",
        "rule <spill> = implies( { +greater(after(?g), ?v), +brim(?g, ?v) },",
        "                        { +overflows(?g) } )",
        "fact +level(glass, 2)", "fact +poured(glass)", "fact +brim(glass, 2)", ""]))
    m3.run(limit=80)
    check("§16", "...and it is REASONED WITH, not merely recorded -- a rule "
          "reads what is known of the unknown and concludes from it",
          m3.holds(kb3.term("overflows(glass)")) == PLUS)

    # ⚠ What stays open, as a check so it cannot be forgotten: the direct form.
    # A consequent naming a value its antecedent never bound is an existential,
    # and it is refused at LOAD with a message rather than silently dropped.
    from .core.text import ParseError
    m4 = Machine(); kb4 = Loader(m4)
    try:
        kb4.load("rule <p> = causes( { +level(?g, ?v) }, { +level(?g, ?w) } )" + chr(10))
        refused = False
    except ParseError:
        refused = True
    check("§12", "...while a value slot that is constrained rather than bound "
          "stays refused, at load, because it is an existential",
          refused)


def a_corpus_can_shorten_its_own_reasoning() -> None:
    """§4's larger optimisation, given a trigger. (§4, §19, §21)

    Composition removes STEPS where compilation only makes them cheaper, and it
    had no way in: `RuleSet.compose` existed and only Python called it, which is
    exactly where `adopt` was before it was a door.

    What decides *which* rules are worth collapsing is a judgement, and §21's
    judgement census says a judgement the machinery makes alone is a seam -- the
    agent could not notice it was composing the wrong things, because a bad
    shortcut makes worse work and never a wrong conclusion, so no fixture fails
    and nothing reports it. So the request is answered and never proposed:
    **the corpus decides, the function executes.**
    """
    from .core.text import load

    m = Machine()
    kb = load(m, chr(10).join([
        "rule <s1> = implies( { +p1(?a,?b), +p2(?b,?c) }, { +i1(?a,?c) } )",
        "rule <s2> = implies( { +i1(?a,?c), +p3(?c,?d) }, { +q(?a,?d) } )",
        "fact +compose(<s1>, <s2>)",
        "fact +p1(a, b)", "fact +p2(b, c)", "fact +p3(c, d)", ""]))
    m.run(limit=80)
    made = [r for r in m.rules.rules if r.name.startswith("s1+s2")]
    check("§4", "a corpus asks, and a rule it did not author is live: "
          "composition has a trigger", len(made) == 1)
    # ⭐ Arity and the JOIN are what composition builds, and they are what no
    # schema rule could take as data -- a rule's antecedent is fixed structure,
    # and there is no way to pass it *join member 0 with member 2 on `?c`*.
    ant = made[0].antecedent if made else []
    check("§12", "...and it carries the union of the premises with the join "
          "threaded -- 2 + 2 members become 3, not 4",
          len(ant) == 3 and len(made[0].consequent) == 1)
    # ⚠ `composed_from` was a Python dict, so *which rules is this a shortcut
    # for* was unanswerable -- §1's defect, and the one §21 needs for
    # *decompose on surprise*, since the agent has to know which sub-steps to
    # re-run. Kill-probe: drop the deposit and only this check falls.
    rec = [p for p in m.g.instances_of(m.COMPOSED) if m.holds(p) == PLUS]
    check("§1", "...and what it is a shortcut FOR is on the record, so the "
          "constituents are askable rather than kept in the machinery",
          len(rec) == 1 and made and m.g.member(rec[0], 0) is made[0].node)
    check("§4", "...and the shortcut reaches the same conclusion",
          m.holds(kb.term("q(a, d)")) == PLUS)

    # ⚠⚠⚠ **What went with situations.** `compose` used to be REFUSED inside a
    # supposition, for `_adopt`'s reason exactly: one rule set is shared by
    # every frame, so a shortcut built while supposing would apply after the
    # frame was discharged and to everything. The refusal was also the third
    # place §5 lets the machinery decline on the record. Both are gone.

    # ⚠⚠⚠ **`has_var` is not a usable guard for anything naming a rule**, and
    # copying `_adopt`'s was the bug this fixture found. A LIVE rule node holds
    # the variables of its own patterns, so `compose(<s1>, <s2>)` reads generic
    # however ground the claim is -- §5's use/mention distinction, arriving at
    # the composer. Membership of the live set is what tells them apart.
    m3 = Machine()
    kb3 = load(m3, chr(10).join([
        "rule <s1> = implies( { +p1(?a) }, { +i1(?a) } )",
        "rule <anything> = implies( { +go(?x, ?y) }, { +compose(?x, ?y) } )",
        "fact +go(notarule, alsonot)", ""]))
    n3 = len(m3.rules.rules)
    m3.run(limit=60)
    check("§5", "...and naming something that is not a live rule composes "
          "nothing, which is also what refuses a generic request",
          len(m3.rules.rules) == n3)

    # ⚠⚠⚠ **Composing across a `causes` flattens two moments into one
    # antecedent and LOSES CONCLUSIONS.** §14: a `causes` consequent lands in a
    # successor, so the second rule's other premises are read one moment later
    # than the first rule's own. The composite asks for all of them together.
    # The world below is the discriminator: `r` appears only after `p` has
    # acted, so the derivation reaches `s` and the flattened rule cannot.
    def reaches(compose: bool) -> bool:
        mm = Machine()
        kk = load(mm, chr(10).join([
            "rule <a> = causes(  { +p(?x) },         { +q(?x) } )",
            "rule <b> = implies( { +q(?x), +r(?x) }, { +s(?x) } )",
            "rule <late> = implies( { +q(?x) }, { +r(?x) } )",
            "fact +p(t)", ""]))
        byy = {r.name: r for r in mm.rules.rules if r.name}
        if compose:
            c = mm.rules.compose(byy["a"], byy["b"], name="ab")
            if c is None:
                return None  # refused, which is the point
            mm.rules.rules = [r for r in mm.rules.rules
                              if r.node not in (byy["a"].node, byy["b"].node)]
        mm.run(limit=60)
        return mm.holds(kk.term("s(t)")) == PLUS
    check("§4", "⚠⚠⚠ composing across a `causes` would lose a conclusion, so "
          "it is REFUSED -- *n steps become one* has to mean with the SAME "
          "conclusion", reaches(False) is True and reaches(True) is None)
    # ...and exactly the unsound shape, not every mixed pair: only members
    # BEYOND the seam are relocated, so a second rule that is just the seam
    # composes across a `causes` soundly.
    m5 = Machine()
    kb5 = load(m5, chr(10).join([
        "rule <a> = causes(  { +p(?x) }, { +q(?x) } )",
        "rule <b> = implies( { +q(?x) }, { +s(?x) } )", ""]))
    by5 = {r.name: r for r in m5.rules.rules if r.name}
    still = m5.rules.compose(by5["a"], by5["b"], name="ok")
    check("§14", "...and the refusal is exact, not cautious: a second rule "
          "that is only the seam relocates nothing and still composes, as "
          "`causes`, because the chain crossed a causal step",
          still is not None and still.connective == CAUSES)

    # ⚠⚠⚠ The twin trap INVERTED, and this fixture is what found it.
    # → docs/design/selftest.md#the-twin-trap-inverted-and-this-fixture-i
    from .core.text import Loader, ParseError
    m4 = Machine()
    kb4 = Loader(m4)
    try:
        kb4.answerer("mine", "compose", lambda mm, e: None)
        refused_reg = False
    except ParseError:
        refused_reg = True
    check("§19", "⚠⚠⚠ ...and a corpus tool may not share a request relation "
          "with the apparatus -- refused at registration, where the claim is "
          "made", refused_reg)
    # ...and a request of its own is still fine, or the refusal would have
    # closed the door instead of guarding it.
    # ⚠ A DIFFERENT tool name, because the first registration is refused and a
    # probe that removes the refusal would otherwise trip the name check
    # instead -- a kill-probe that raises where the answer is False reports
    # nothing, and that trap is now recorded five times in this file.
    check("§17", "...while a request of its own is registered as ever",
          kb4.answerer("ownreq", "shorten", lambda mm, e: None) is not None)


def an_example_becomes_a_rule() -> None:
    """Two cases in, one rule out, and it applies to a third. (§17, §14)

    generalise is the dual of unify -- matching asks what two structures must
    agree about, anti-unification asks what they already do -- and it is the
    operation *learn from examples* is made of. ⚠ The tool DECLINES rather than
    generalising anything.

    See docs/design/selftest.md#an-example-becomes-a-rule.
    """
    from .core.rules import generalise
    from .core.text import Loader

    # The operation first, on its own, because a check about a learned rule
    # cannot tell a least generalisation from a lazy one.
    g = Graph()
    f, a, b, c = g.atom("f"), g.atom("a"), g.atom("b"), g.atom("c")
    lgg = generalise(g, g.rel(f, a, b), g.rel(f, a, c), {})
    # ⚠ Guarded, not indexed. A lazy generalisation returns a bare variable,
    # which has no member 0 -- so the first version of this check RAISED where
    # the answer is False, and a runner that cannot say False about an absence
    # reports nothing. Fourth time in this file.
    check("§7", "anti-unification KEEPS what the two examples agree about and "
          "varies only what they do not -- otherwise it is a generalisation but "
          "not the least one",
          g.relation_of(lgg) is f and len(g.members(lgg)) == 2
          and g.member(lgg, 0) is a and g.is_var(g.member(lgg, 1)))
    shared: dict = {}
    same = generalise(g, g.rel(f, a, a), g.rel(f, b, b), shared)
    check("§7", "...and one disagreement is one variable however often it "
          "appears: f(a,a) and f(b,b) generalise to f(?g, ?g), not to f(?1, ?2)",
          len(g.members(same)) == 2 and g.member(same, 0) is g.member(same, 1))

    # Now the loop: two examples, a tool, the door, and a case neither example
    # mentioned.
    def build(src: str):
        mm = Machine()
        kbb = Loader(mm)

        def learn(machine, entry):
            """Two `pair(premise, conclusion)` arguments in, a rule node out."""
            gg = machine.g
            one, two = gg.members(entry.proposition)
            mapping: dict = {}
            # ⭐ The SAME mapping for both halves. This is the crux.
            ant = generalise(gg, gg.member(one, 0), gg.member(two, 0), mapping)
            con = generalise(gg, gg.member(one, 1), gg.member(two, 1), mapping)
            if not gg.has_var(ant) or gg.is_var(ant) or gg.is_var(con):
                # Nothing was learned (the examples are the same), or everything
                # was (they share no structure). Declining is an answer.
                return None
            node = gg.instance(kbb.atom("learned"))
            w = lambda p: machine.gate.write(p, PLUS, licence=entry.node,
                                             source=machine.KB, mention=True)
            w(gg.rel(machine.RULE, node))
            w(gg.rel(machine.CONN, node, machine.rules.IMPLIES))
            w(gg.rel(machine.ANT, node, ant, machine.chain.SIGN[PLUS],
                     machine._numeral(0)))
            # ⚠ WRAPPED, and the reason is §12 rather than modesty: a rule
            # nobody authored is exactly the kind whose conclusions must stay
            # weaker than what it was told -- and since grades went, saying so
            # is saying it in the conclusion, where a rule can read it and a
            # corpus can ask which of its beliefs rest on something learned.
            w(gg.rel(machine.CON, node, gg.rel(kbb.atom("likely"), con),
                     machine.chain.SIGN[PLUS], machine._numeral(0)))
            return node

        kbb.answerer("learner", "generalise", learn)
        kbb.load(src)
        return mm, kbb

    corpus = chr(10).join([
        "rule <ask> = implies( { +example(?p1, ?c1), +example(?p2, ?c2),",
        "                        +sooner(?p1, ?p2) },",
        "                      { +generalise(pair(?p1, ?c1), pair(?p2, ?c2)) } )",
        "rule <take> = implies( { +answered(<learner>, generalise(?x, ?y), ?r) },",
        "                      { +adopt(?r) } )",
        "fact +example(seen(door), known(door))",
        "fact +example(seen(window), known(window))",
        "fact +sooner(seen(door), seen(window))",
        "fact +seen(gate)", ""])

    m, kb = build(corpus)
    before = len(m.rules.rules)
    m.run(limit=120)
    check("§17", "⭐ two examples become a rule the agent did not have",
          len(m.rules.rules) > before)
    check("§14", "⭐⭐⭐ ...and it applies to a case NEITHER example mentioned, "
          "which is the whole of what generalising is for",
          m.holds(kb.term("likely(known(gate))")) == PLUS)
    check("§12", "...and says so no more strongly than a rule nobody authored "
          "should -- in the conclusion, where a corpus can ask which of its "
          "beliefs rest on something learned",
          m.holds(kb.term("known(gate)")) is None)

    # ⚠ Unrelated examples have a BARE VARIABLE as their generalisation -- a
    # rule that fires on everything. The tool declines, which §17 says is an
    # answer and not a failure.
    junk, kb_j = build(chr(10).join([
        "rule <ask> = implies( { +example(?p1, ?c1), +example(?p2, ?c2),",
        "                        +sooner(?p1, ?p2) },",
        "                      { +generalise(pair(?p1, ?c1), pair(?p2, ?c2)) } )",
        "rule <take> = implies( { +answered(<learner>, generalise(?x, ?y), ?r) },",
        "                      { +adopt(?r) } )",
        "fact +example(seen(door), known(door))",
        "fact +example(heard(bell), rang(bell))",
        "fact +sooner(seen(door), heard(bell))",
        "fact +seen(gate)", ""]))
    j_before = len(junk.rules.rules)
    junk.run(limit=120)
    check("§17", "⚠ and two examples with nothing in common teach nothing: the "
          "tool declines rather than proposing a rule that fires on everything",
          len(junk.rules.rules) == j_before
          and junk.holds(kb_j.term("likely(known(gate))")) is None)


def a_rule_can_author_a_rule() -> None:
    """The reverse of `reify`, and the door the whole acquisition family needs.

    A rule has been data since §14's worked example -- rule(<R>), conn, ant,
    con -- and it went one way: RuleSet.rule was called by the parser and by
    tests and by nothing else. ⚠ The tool PROPOSES.

    See docs/design/selftest.md#a-rule-can-author-a-rule.
    """
    from .core.text import Loader

    def build(src: str):
        """A machine with the composer registered, then the corpus. Registered
        BEFORE loading, because a rule names the tool (`<builder>`) and `<...>`
        is resolved at authoring."""
        mm = Machine()
        kbb = Loader(mm)

        def compose(machine, entry):
            """Builds `{+seen(?x)} => {+known(?x)}` and returns its node.

            The variable is minted here, once, and used in both patterns --
            which is exactly what no corpus can do, and the whole reason this
            is a function rather than a rule. ⚠ In the CORPUS's name scope, and
            the first version was not.

            See docs/design/selftest.md#compose.
            """
            g = machine.g
            x = g.var("?x")
            node = g.instance(kbb.atom("built"))
            w = lambda p: machine.gate.write(p, PLUS,
                                             licence=entry.node,
                                             source=machine.KB, mention=True)
            w(g.rel(machine.RULE, node))
            w(g.rel(machine.CONN, node, machine.rules.IMPLIES))
            w(g.rel(machine.ANT, node, g.rel(kbb.atom("seen"), x),
                    machine.chain.SIGN[PLUS], machine._numeral(0)))
            # ⚠ The conclusion is WRAPPED -- `likely(known(?x))` -- and that is
            # the check rather than the flavour. A rule nobody authored should
            # not conclude as strongly as one that was told, and since grades
            # went that is said in the consequent itself, where a rule can read
            # it. It used to be a fifth member of `con` carrying a grade, and
            # recording it and obeying it were two properties needing two
            # checks; now there is nothing extra to obey.
            w(g.rel(machine.CON, node,
                    g.rel(kbb.atom("likely"), g.rel(kbb.atom("known"), x)),
                    machine.chain.SIGN[PLUS], machine._numeral(0)))
            return node

        kbb.answerer("builder", "build", compose)
        kbb.load(src)
        return mm, kbb

    src = chr(10).join([
        "rule <ask> = implies( { +want(?w) }, { +build(?w) } )",
        "rule <take> = implies( { +answered(<builder>, build(?w), ?r) },",
        "                      { +adopt(?r) } )",
        "fact +want(a_rule)",
        "fact +seen(door)", ""])

    m, kb = build(src)
    before = len(m.rules.rules)
    m.run(limit=80)

    check("§14", "⭐ a rule the agent did not start with is live: the graph "
          "described one, a corpus adopted it, and the loop reads it",
          len(m.rules.rules) == before + 1)
    # ⚠⚠⚠ And it IS the node the graph described. Minting a fresh one made the
    # live rule a twin: everything a corpus had said about the described rule
    # went to a node that was not a rule, and everything the machinery said
    # about the live one named a node no corpus could reach. Invisible until a
    # standing policy tried to order a learned rule and quietly did nothing --
    # the twin trap, eighth time, and the only check that can see it.
    adopted = [r for r in m.rules.rules if r.name.startswith("built")]
    described = [p for p in m.g.instances_of(m.RULE)
                 if m.holds(p) == PLUS and m.g.show(m.g.member(p, 0)).startswith("built")]
    check("§3", "...and it IS the rule the graph described, not a twin of it: "
          "a precedence, a defeat or any later claim names the same node",
          len(adopted) == 1 and len(described) == 1
          and adopted[0].node is m.g.member(described[0], 0))
    check("§14", "...and it APPLIES -- the round trip is closed, not merely "
          "recorded", m.holds(kb.term("likely(known(door))")) == PLUS)
    check("§12", "...and what it concluded is WRAPPED, so how strongly a rule "
          "nobody authored may speak is itself a claim a rule can read",
          m.holds(kb.term("known(door)")) is None)
    # The tool proposed and the corpus disposed: delete the adopting rule and
    # the same offer is on the record and believed by nobody. `artefact`'s
    # measurement at the same boundary.
    inert, kb_i = build(chr(10).join([
        "rule <ask> = implies( { +want(?w) }, { +build(?w) } )",
        "fact +want(a_rule)", "fact +seen(door)", ""]))
    n_before = len(inert.rules.rules)
    inert.run(limit=80)
    check("§17", "...and a tool only PROPOSES: without the rule that adopts, "
          "the offer is on the record and nothing is live",
          len(inert.rules.rules) == n_before
          and inert.holds(kb_i.term("likely(known(door))")) is None
          and any(inert.g.relation_of(p) is inert.ANSWERED
                  for p in inert.g.instances_of(inert.ANSWERED)
                  if inert.holds(p) == PLUS))

    # ⚠⚠⚠ **What went with situations, and it was a real guard.** Adopting
    # inside a supposition used to be REFUSED: `RuleSet.rules` is one list
    # shared by every frame, so a rule adopted while supposing would apply
    # after the frame was discharged, and to everything. With no frame there is
    # nothing to refuse and nothing to be inside, so **the guard is gone rather
    # than satisfied.** `docs/descriptions-to-rules.md` argues the replacement:
    # propose/dispose belongs at the boundary a description crosses.

    # ⚠ The POSITION, which `reify` did not record until this needed it.
    # Without it the members are ordered by the accident of minting -- which
    # reproduces authored order for anything `reify` wrote, so a check over it
    # could never fail. Deposited out of order on purpose.
    from .core.text import load as _load
    back = Machine()
    kb_b = _load(back, "rule <two> = implies( { +a(?x), +b(?x) }, { +c(?x) } )\n")
    (two,) = [r for r in back.rules.rules if r.name == "two"]
    order = []
    for p in back.g.instances_of(back.ANT):
        if back.g.member(p, 0) is two.node and back.holds(p) == PLUS:
            order.append((back.g.show(back.g.member(p, 3)),
                          back.g.relation_of(back.g.member(p, 1))))
    check("§14", "a rule's antecedent records WHICH POSITION each member is at, "
          "so reading it back is not a guess about minting order",
          sorted(order) == [("0", back.g.relation_of(kb_b.term("a(z)"))),
                            ("1", back.g.relation_of(kb_b.term("b(z)")))])
    # ⚠ There is no grade member any more: `con` is four, like `ant`. The fifth
    # carried the grade a consequent would conclude at, and it went with `@` --
    # an uncertain conclusion is `+likely(p)`, which is already in the pattern.
    con = [p for p in back.g.instances_of(back.CON)
           if back.g.member(p, 0) is two.node and back.holds(p) == PLUS]
    check("§14", "...and a consequent records no grade, because there is none: "
          "how strongly a rule concludes is now IN what it concludes",
          len(con) == 1 and len(back.g.members(con[0])) == 4)


def the_agent_harmonizes_itself() -> None:
    """Do the four pieces compose? (§2, §14, §19)

    defeated, adopt, generalise and the wrapper story all landed the same day
    and had never met. ⚠ And a conflict starves the rule that would settle it.

    See docs/design/selftest.md#the-agent-harmonizes-itself.
    """
    from .core.text import load

    # -- 1. a precedence a RULE concluded is obeyed -------------------------
    m = Machine()
    kb = load(m, chr(10).join([
        "rule <hot> = implies( { +go(?x) }, { +q(?x) } )",
        "rule <cold> = implies( { +go(?x) }, { -q(?x) } )",
        "rule <referee> = implies( { +p(?x) }, { +overrides(<cold>, <hot>) } )",
        "fact standing(<referee>)",
        "fact +p(a)", "fact +go(a)", ""]))
    steps = m.run(limit=60)
    check("§14", "⭐ a precedence a RULE concluded is obeyed -- the table is what "
          "the graph claims, not what the loader read",
          [(h.name, l.name) for h, l in m.rules.precedence(m.OVERRIDES)]
          == [("cold", "hot")])
    check("§14", "...so the agent settles its own conflict: it decides the "
          "precedence, the loser is defeated, and the run reaches quiescence",
          m.holds(kb.term("defeated(<hot>, <cold>)")) == PLUS
          and steps[-1].state == "quiescent"
          and len([s for s in steps if s.applied]) < 5)

    # ⚠ The control, and it is the finding: without the precedence the two
    # rules undo each other forever, and the rule that would settle it is
    # starved. Same corpus, one word (`standing`) removed.
    loud = Machine()
    kb_loud = load(loud, chr(10).join([
        "rule <hot> = implies( { +go(?x) }, { +q(?x) } )",
        "rule <cold> = implies( { +go(?x) }, { -q(?x) } )",
        "rule <referee> = implies( { +p(?x) }, { +overrides(<cold>, <hot>) } )",
        "fact +p(a)", "fact +go(a)", ""]))
    noisy = loud.run(limit=60)
    # This check used to assert the OPPOSITE, and the finding it recorded was
    # real: without standing, <hot> and <cold> undid each other for ever and
    # <referee> -- the rule that would settle the conflict -- never got a turn.
    # → docs/design/selftest.md#this-check-used-to-assert-the-opposite-and-the
    check("§19", "...and a conflict no longer starves the rule that would "
          "settle it: refraction stops the pair looping, so the referee gets "
          "its turn and the contradiction is deposited rather than run",
          noisy[-1].state == "quiescent"
          and "referee" in {s.applied.rule.name for s in noisy if s.applied}
          and loud.holds(loud.g.rel(loud.CONTESTED, kb_loud.rule_ref("hot"),
                                    kb_loud.term("q(a)"))) == PLUS)

    # -- 2. and it can be withdrawn ----------------------------------------
    undone = Machine()
    load(undone, chr(10).join([
        "rule <hot> = implies( { +go(?x) }, { +q(?x) } )",
        "rule <cold> = implies( { +go(?x) }, { -q(?x) } )",
        "fact overrides(<cold>, <hot>)",
        "rule <undo> = implies( { +oops }, { -overrides(<cold>, <hot>) } )",
        "fact standing(<undo>)",
        "fact +oops", ""]))
    undone.run(limit=40)
    check("§14", "...and a precedence can be WITHDRAWN, which is what makes it a "
          "claim rather than a configuration",
          not undone.rules.precedence(undone.OVERRIDES))

    # -- 3. the whole arc, end to end --------------------------------------
    #
    # ⭐⭐⭐ Two examples become a rule (`generalise`), the rule becomes live
    # (`adopt`), the corpus decides an authored rule outranks anything it
    # learned (`overrides`, concluded), and the loser is on the record
    # (`defeated`). Four commits, one run.
    from .core.rules import generalise
    from .core.text import Loader

    # ⚠ One learner PER LOADER, and the first version had one closing over the
    # first machine's. A name resolved through `kb.atom` is a node in THAT
    # machine's graph, so the second machine got node ids from the first --
    # ints that mean something else. The twin trap across two graphs, which is
    # the same mistake a denial check in this suite made an hour earlier.
    def make_learner(kb):
        def learn(machine, entry):
            gg = machine.g
            one, two = gg.members(entry.proposition)
            mapping: dict = {}
            ant = generalise(gg, gg.member(one, 0), gg.member(two, 0), mapping)
            con = generalise(gg, gg.member(one, 1), gg.member(two, 1), mapping)
            if not gg.has_var(ant) or gg.is_var(ant) or gg.is_var(con):
                return None
            node = gg.instance(kb.atom("learned"))
            w = lambda p: machine.gate.write(p, PLUS, licence=entry.node,
                                             source=machine.KB, mention=True)
            w(gg.rel(machine.RULE, node))
            w(gg.rel(machine.CONN, node, machine.rules.IMPLIES))
            w(gg.rel(machine.ANT, node, ant, machine.chain.SIGN[PLUS],
                     machine._numeral(0)))
            w(gg.rel(machine.CON, node, con, machine.chain.SIGN[PLUS],
                     machine._numeral(0)))
            return node
        return learn

    mm = Machine()
    kbb = Loader(mm)
    kbb.answerer("learner", "generalise", make_learner(kbb))
    kbb.load(chr(10).join([
        # What it already knew, and what it is about to learn contradicts it.
        "rule <secret> = implies( { +sealed(?x) }, { -open(?x) } )",
        "rule <ask> = implies( { +example(?p1, ?c1), +example(?p2, ?c2),",
        "                        +sooner(?p1, ?p2) },",
        "                      { +generalise(pair(?p1, ?c1), pair(?p2, ?c2)) } )",
        "rule <take> = implies( { +answered(<learner>, generalise(?x, ?y), ?r) },",
        "                      { +adopt(?r) } )",
        # ⭐ The corpus's standing policy about what it learns, written once and
        # applying to a rule that does not exist yet -- which is only sayable
        # because the precedence is concluded rather than parsed.
        "rule <trust-what-i-was-told> = implies( { +rule(?r), +adopt(?r) },",
        "                      { +overrides(<secret>, ?r) } )",
        "fact standing(<trust-what-i-was-told>)",
        "fact +example(hinged(a), open(a))",
        "fact +example(hinged(b), open(b))",
        "fact +sooner(hinged(a), hinged(b))",
        "fact +hinged(vault)", "fact +sealed(vault)", ""]))
    mm.run(limit=200)
    learned_rules = [r for r in mm.rules.rules if r.name.startswith("learned")]
    check("§2", "⭐⭐⭐ the whole arc composes: two examples become a live rule, "
          "and a standing policy orders it against what the agent was told -- "
          "a precedence about a rule that did not exist when it was written",
          len(learned_rules) == 1
          and any(l is learned_rules[0]
                  for _, l in mm.rules.precedence(mm.OVERRIDES)))
    # ⚠ Built with `g.rel`, not `kb.term`: a rule adopted at runtime is named
    # after its node and does not print as anything the surface can parse.
    # That is the wall `artefact` recorded from the other side -- a rule reaches
    # what a tool made by BINDING, never by naming it literally.
    (secret,) = [r for r in mm.rules.rules if r.name == "secret"]
    # ⚠⚠ ...and the author does not have to know the order. Written the other
    # way round -- the precedence in the SAME consequent as the adoption, and
    # before it -- the fact lands while `?r` is not yet a rule, so the write
    # hook drops it. `_adopt` re-reads what the graph already says about the
    # rule it is making live. §16's ordering trap, and here the author has no
    # way to see it: both orders read the same.
    early = Machine()
    kbe = Loader(early)
    kbe.answerer("learner", "generalise", make_learner(kbe))
    kbe.load(chr(10).join([
        "rule <secret> = implies( { +sealed(?x) }, { -open(?x) } )",
        "rule <ask> = implies( { +example(?p1, ?c1), +example(?p2, ?c2),",
        "                        +sooner(?p1, ?p2) },",
        "                      { +generalise(pair(?p1, ?c1), pair(?p2, ?c2)) } )",
        "rule <take> = implies( { +answered(<learner>, generalise(?x, ?y), ?r) },",
        "                      { +overrides(<secret>, ?r), +adopt(?r) } )",
        "fact +example(hinged(a), open(a))",
        "fact +example(hinged(b), open(b))",
        "fact +sooner(hinged(a), hinged(b))",
        "fact +hinged(vault)", "fact +sealed(vault)", ""]))
    early.run(limit=200)
    early_learned = [r for r in early.rules.rules if r.name.startswith("learned")]
    check("§16", "⚠ a precedence written BEFORE the rule is live still counts: "
          "the author may say it in either order and cannot tell which they "
          "chose",
          len(early_learned) == 1
          and any(l is early_learned[0]
                  for _, l in early.rules.precedence(early.OVERRIDES))
          and early.holds(kbe.term("open(vault)")) == MINUS)
    check("§14", "...and the learned rule LOSES to the authored one about the "
          "sealed vault, with the defeat on the record",
          mm.holds(kbb.term("open(vault)")) == MINUS
          and mm.holds(mm.g.rel(mm.DEFEATED, learned_rules[0].node,
                                secret.node)) == PLUS)


def what_a_learned_rule_may_conclude() -> None:
    """A learned rule that concludes WRAPPED cannot fight what it was told.

    Acquisition's normal case: the agent generalises {+hinged(?x)} ⟹ open(?x)
    from two examples, and it already knows {+sealed(?x)} ⟹ -open(?x). ⚠ And
    supersedes is too narrow.

    See docs/design/selftest.md#what-a-learned-rule-may-conclude.
    """
    from .core.rules import generalise
    from .core.text import Loader

    def episode(wrapped: bool, precedence: str):
        m = Machine()
        kb = Loader(m)

        def learn(machine, entry):
            gg = machine.g
            one, two = gg.members(entry.proposition)
            mp: dict = {}
            ant = generalise(gg, gg.member(one, 0), gg.member(two, 0), mp)
            con = generalise(gg, gg.member(one, 1), gg.member(two, 1), mp)
            if not gg.has_var(ant) or gg.is_var(ant) or gg.is_var(con):
                return None
            if wrapped:
                con = gg.rel(kb.atom("likely"), con)
            node = gg.instance(kb.atom("learned"))
            w = lambda p: machine.gate.write(p, PLUS, licence=entry.node,
                                             source=machine.KB, mention=True)
            w(gg.rel(machine.RULE, node))
            w(gg.rel(machine.CONN, node, machine.rules.IMPLIES))
            w(gg.rel(machine.ANT, node, ant, machine.chain.SIGN[PLUS],
                     machine._numeral(0)))
            w(gg.rel(machine.CON, node, con, machine.chain.SIGN[PLUS],
                     machine._numeral(0)))
            return node

        kb.answerer("learner", "generalise", learn)
        kb.load(chr(10).join([
            "rule <secret> = implies( { +sealed(?x) }, { -open(?x) } )",
            "rule <ask> = implies( { +example(?p1, ?c1), +example(?p2, ?c2),",
            "                        +sooner(?p1, ?p2) },",
            "                      { +generalise(pair(?p1, ?c1), pair(?p2, ?c2)) } )",
            "rule <take> = implies( { +answered(<learner>, generalise(?x, ?y), ?r) },",
            "                      { " + precedence + "+adopt(?r) } )",
            "fact +example(hinged(a), open(a))",
            "fact +example(hinged(b), open(b))",
            "fact +sooner(hinged(a), hinged(b))",
            "fact +hinged(vault)", "fact +sealed(vault)",
            "fact +hinged(gate)", ""]))
        steps = m.run(limit=300)
        return m, kb, steps

    broad, kb_b, _ = episode(False, "+overrides(<secret>, ?r), ")
    check("§14", "⚠ `overrides` is too broad for what an agent learns: one "
          "sealed object suppresses the learned rule about every object, "
          "including the one it is right about",
          broad.holds(kb_b.term("open(vault)")) == MINUS
          and broad.holds(kb_b.term("open(gate)")) is None)

    narrow, kb_n, steps_n = episode(False, "+supersedes(<secret>, ?r), ")
    check("§14", "⚠ ...and `supersedes` is too narrow: it defeats applications "
          "sharing a consumed entry, and two rules reaching one conclusion from "
          "different premises share none -- so they oscillate and never stop",
          # ⚠ The DEFECT, not the symptom.
          # →
          # docs/design/selftest.md#the-defect-not-the-symptom-supersedes-bein
          narrow.holds(kb_n.term("open(gate)")) == PLUS)

    kept, kb_k, steps_k = episode(True, "")
    check("§12", "⭐⭐⭐ ...and a learned rule that concludes WRAPPED needs no "
          "precedence at all: it never contradicts what the agent was told, so "
          "the generalisation and the specific fact are held at once",
          kept.holds(kb_k.term("likely(open(gate))")) == PLUS
          and kept.holds(kb_k.term("open(vault)")) == MINUS
          and steps_k[-1].state == "quiescent")
    check("§15", "...and it does not assert the bare claim about EITHER, so "
          "nothing downstream acts on a generalisation the agent merely drew",
          kept.holds(kb_k.term("open(gate)")) is None
          and kept.holds(kb_k.term("likely(open(vault))")) == PLUS)


def a_defeat_is_on_the_record() -> None:
    """`defeated(<loser>, <winner>)` -- §21's defect for the **tenth** time.

    Measured before building it, because *knowledge acquisition and rule
    harmonization are the pain* (Cyc) is a claim about scale and this repo's
    corpora are one author and a few days old. ⚠ overrides only.

    See docs/design/selftest.md#a-defeat-is-on-the-record.
    """
    from .core.text import load

    src = chr(10).join([
        "rule <hot> = implies( { +p(?x) }, { +q(?x) } )",
        "rule <cold> = implies( { +p(?x) }, { -q(?x) } )",
        "fact overrides(<cold>, <hot>)",
        "fact +p(a)", ""])
    m = Machine()
    kb = load(m, src)
    m.run(limit=60)
    check("§14", "when a precedence is exercised, WHICH rule beat which is on "
          "the record -- the loop's own answer, which nothing else could "
          "reconstruct",
          m.holds(kb.term("defeated(<hot>, <cold>)")) == PLUS)
    check("§14", "...and it is directional: the winner was not defeated",
          m.holds(kb.term("defeated(<cold>, <hot>)")) is None)
    # Deduped by reading the graph, like every other record of *this happened
    # here*: the defeat is recomputed on every tick and restating is not
    # revising (§8).
    entries = [e for mo in m.chain.moments for e in mo.delta
               if e.proposition == kb.term("defeated(<hot>, <cold>)")]
    check("§8", "...and recorded once however many ticks it kept happening",
          len(entries) == 1)

    # ⚠ The control, and it is the distinction the whole record turns on: a rule
    # that merely LOSES arbitration is not defeated. Losing is being deferred,
    # not rejected -- it applies on the next tick -- and recording that as a
    # defeat would report a rule base as fighting when it is merely ordered.
    quiet = Machine()
    kb_q = load(quiet, chr(10).join([
        "rule <one> = implies( { +p(?x) }, { +a(?x) } )",
        "rule <two> = implies( { +p(?x) }, { +b(?x) } )",
        "fact +p(a)", ""]))
    quiet.run(limit=60)
    check("§14", "...while a rule that merely lost the tick is NOT defeated: "
          "arbitration is scheduling, and both conclusions arrive",
          quiet.holds(kb_q.term("a(a)")) == PLUS
          and quiet.holds(kb_q.term("b(a)")) == PLUS
          and not [p for p in quiet.g.instances_of(quiet.DEFEATED)
                   if quiet.holds(p) == PLUS])

    # ⚠⚠ And nothing is recorded when arbitration IGNORED the defeat. A cycle in
    # `overrides` defeats everybody, so §14's fallback lets everybody through to
    # keep arbitration total -- and then nobody was defeated.
    cycle = Machine()
    kb_c = load(cycle, chr(10).join([
        "rule <up> = implies( { +p(?x) }, { +q(?x) } )",
        "rule <down> = implies( { +p(?x) }, { -q(?x) } )",
        "fact overrides(<up>, <down>)",
        "fact overrides(<down>, <up>)",
        "fact +p(a)", ""]))
    cycle.run(limit=60)

    # ⭐ What the occasion is FOR: a corpus reacting to its own rule base
    # fighting. This is the acquisition loop's first half -- the agent noticing
    # that two things it was told disagree, and asking.
    asked = Machine()
    load(asked, src + chr(10).join([
        "rule <harmonize> = implies( { +defeated(?l, ?w) }, { +doing(ask(?l)) } )",
        "fact standing(<harmonize>)", ""]))
    asked.run(limit=60)
    check("§19", "⭐ and a corpus can act on it -- it decides to ask about the "
          "rule that lost, which is harmonization as a rule and not as machinery",
          any(asked.g.show(p) == "doing(ask(<hot>))"
              for p in asked.g.instances_of(asked.DOING)
              if asked.holds(p) == PLUS))
    # ⚠⚠⚠ ...and it CANNOT leave the agent, which is the wall this fixture
    # found and the first thing acquisition runs into.
    # → docs/design/selftest.md#and-it-cannot-leave-the-agent-which-is-t
    check("§15", "⚠ but an intent NAMING A RULE never leaves the agent: a rule "
          "node is generic, and the act boundary refuses a description",
          not asked.emitted)


def a_join_is_not_a_scan() -> None:
    """A rule joined against itself over one relation -- **what recognition is**.

    rule <s1> = implies( { +child(?p, ?x), +child(?x, ?y) }, { +grand(?p, ?y) }
    ) Reported by pystrider, who read the index and predicted the cause before
    measuring it, and it was a SECOND quadratic: quiet, weigh, heap and kept
    all address the option set -- n ticks, each weighing what could apply --
    and this one has a constant option set and does its damage inside one tick.
    ⚠ What is reordered is the WALK, never the antecedent.

    See docs/design/selftest.md#a-join-is-not-a-scan.
    """
    from .core import rules as R
    from .core.text import load

    def counted(n: int):
        """(unifications, grandparent conclusions) over a binary tree."""
        src = ["rule <s1> = implies( { +child(?p, ?x), +child(?x, ?y) }, "
               "{ +grand(?p, ?y) } )"]
        src += [f"fact +child(n{i // 2}, n{i})" for i in range(1, n)]
        m = Machine()
        kb = load(m, chr(10).join(src) + chr(10))
        calls = [0]
        original = R.unify

        def counting(g, pattern, node, bindings):
            calls[0] += 1
            return original(g, pattern, node, bindings)

        R.unify = counting
        try:
            m.run(limit=n * 4 + 50)
        finally:
            # In a `finally`: a probe that mutates a module and crashes leaves
            # every later check in this run counting into a dead list.
            R.unify = original
        # ⚠ Ground instances that are CLAIMED, not `instances_of` -- the rule's
        # own consequent `grand(?p, ?y)` is an instance of the relation and
        # holds nothing, and counting it read 99 where the answer is 98. The
        # same miscount this file has recorded once already; and `g.atom` mints
        # rather than interns, so the relation is taken off a real term.
        rel = m.g.relation_of(kb.term("grand(n0, n2)"))
        return calls[0], sum(
            1 for p in m.g.instances_of(rel)
            if not m.g.has_var(p) and m.holds(p) == PLUS
        )

    small_calls, small_found = counted(100)
    large_calls, large_found = counted(200)

    # ⭐ The claim is the SHAPE, because a count on one size cannot tell a scan
    # from a lookup. Doubling the tree doubles the work; before it quadrupled.
    # ...and the control that makes it an optimisation rather than a change: a
    # narrowed candidate list must lose only what `unify` would have rejected.
    # Every node with a grandchild, and nothing else.
    check("§7", "...and it finds every grandparent it used to: narrowing drops "
          "only what would have failed to unify",
          (small_found, large_found) == (98, 198))

    # ⚠⚠⚠ **And `consumed` is filled by MEMBER, not by the order walked.** This
    # needs its own check because no outcome can show it: permuting `consumed`
    # permutes `heap`'s stamp and §12's trail, and the suite -- and
    # the retired `ugm.arbitration`, which compared two paths that would permute alike --
    # both pass with it broken. Kill-probed exactly that way, 0 failing, which
    # is why the invariant is asserted here directly rather than through what
    # the agent concludes.
    m = Machine()
    kb = load(m, chr(10).join([
        "rule <j> = implies( { +a(?x), +b(?x) }, { +c(?x) } )",
        "fact +a(t)", "fact +b(t)", ""]))
    state = m._situation()
    (rule,) = [r for r in m.rules.rules if r.name == "j"]
    # ⚠ The delta holds member 1's entry ONLY, which is the case that walks
    # member 1 before member 0. Handing it the whole state instead finds the
    # application on the first pivot and dedups the second away -- so the walk
    # under test never runs, and the check passes vacuously. It did.
    later = m.chain.resolve(kb.term("b(t)"))
    found = R.match(m.g, m.chain, rule, state,
                    fresh=R.Situation(m.g, [later]))
    rel_of = lambda e: m.g.relation_of(e.proposition)
    check("§12", "however the join is walked, the trail records what each "
          "ANTECEDENT MEMBER matched, in the order the rule was written",
          len(found) == 1
          and all(rel_of(app.consumed[0]) is m.g.relation_of(kb.term("a(t)"))
                  and rel_of(app.consumed[1]) is m.g.relation_of(kb.term("b(t)"))
                  for app in found))


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
    from .core.text import load

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

    PROPOSITION rather than as an entry field (§14, §21). ⚠ The reaction half
    is NOT here, and the blocker is §6's, not a new one.

    See docs/design/selftest.md#a-rule-says-that-it-ran.
    """
    from .core.text import load

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

    A tool is not a new kind of thing.

    See docs/design/selftest.md#a-tool-is-data.
    """
    from .probes.tools import episode

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

    # ⚠ And the registration says so when it is wrong. Reported by `pystrider`:
    # a two-argument function registered through the scoped door raised out of
    # `gate.write` at the first write, naming neither the tool nor the
    # registration -- one cycle to find, and easy to write because the
    # apparatus's own reifier takes `(frame, entry)` and wraps it.
    from .core.machine import Machine as _Machine
    from .core.text import load as _load
    refused = _Machine()
    kb_r = _load(refused, "fact +nothing(x)\n")
    try:
        # ⚠ The WRONG arity is three now, and it used to be two. The protocol
        # was `(machine, frame, entry)`; the frame went with the seat, so a
        # `(frame, entry)` stub -- which is what this check used to hand in --
        # is a correctly-shaped answerer today and would be accepted.
        kb_r.answerer("stub", "guess", lambda mach, frame, entry: None)
        raised = ""
    except TypeError as exc:
        raised = str(exc)
    check("§5", "an answerer that cannot take (machine, entry) is refused "
          "AT REGISTRATION, naming itself -- not at the first write, from inside "
          "the gate", "stub" in raised and "machine, entry" in raised)
    check("§5", "...and the two-argument one it should have been is accepted, "
          "so the refusal is about arity and not about tools",
          kb_r.answerer("ok", "guess", lambda m, e: None) is not None)

    # The restriction that makes an unreliable tool safe to be wrong.
    from .core.machine import Machine
    from .core.text import Loader
    m = Machine()
    m.actuator("hands")
    kb2 = Loader(m)
    kb2.answerer("oracle", "advice", lambda mach, e: kb2.term("smash(jug1)"))
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

    Everything upstream of this existed: review credits, blame attributes a
    lost subgoal, learned writes surface text, and forgoing made arbitration
    into a decision instead of a schedule.

    See docs/design/selftest.md#an-episode-teaches-the-next-one.
    """
    from .learning.learning import Episode, world

    ep1 = Episode(world(jug_first=True))
    check("§19", "a world where the wrong choice costs something: the agent "
          "smashed the jug it also needed", ep1.harmed)
    check("§19", "and the loss is attributed to the DECISION, not the physics",
          "use-jug" in ep1.blamed)
    # ⭐⭐⭐ **And it names the THING, not the rule.** `<use-tap>` was the
    # alternative; `sink` is what makes it available. A lesson keyed on the rule
    # goes stale the moment that rule is adopted, composed or renamed -- keyed
    # on an identity, one level up from bindings -- and a lesson keyed on what
    # is salient transfers to a rule authored afterwards.
    check("§19", "what it carries forward names the alternative it passed up -- "
          "blame alone could only suppress the rule that did the damage",
          any("attention(sink" in r for r in ep1.rows))
    check("§19", "...and it names it by what it is ABOUT, so no rule id appears in "
          "anything an episode writes down",
          ep1.rows and not any("<" in r for r in ep1.rows))

    # ⚠ These three were computed and never checked -- the fixture ran the
    # transfer and asserted nothing about it. Reading them is the whole point.
    ep2 = Episode(world(jug_first=True) + chr(10).join(ep1.rows) + chr(10))
    check("§19", "the taught episode does not repeat the damage", not ep2.harmed)
    fresh = Episode(world("pot", "jug2", jug_first=True), "pot", "jug2")
    taught = Episode(world("pot", "jug2", jug_first=True)
                     + chr(10).join(ep1.rows) + chr(10), "pot", "jug2")
    check("§19", "and the fresh world can still fail, so the transfer is measured "
          "against something", fresh.harmed and not taught.harmed)


def subgoals_make_blame_sayable() -> None:
    """Splitting a task into subgoals is what makes FAILURE attributable (§19).

    review credits and deliberately refuses to blame, because an episode that
    achieved nothing may have been an impossible one -- many rules ran, one
    outcome was bad, and nothing points at an author.

    See docs/design/selftest.md#subgoals-make-blame-sayable.
    """
    from .core.text import load

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

    Arbitration is described as choosing one rule among those that matched.

    See docs/design/selftest.md#taking-one-way-passes-up-the-others.
    """
    from .core.text import load

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

    passed_up = next(r for r in m.rules.rules if r.name == "use-jug")
    taken = next(r for r in m.rules.rules if r.name == "use-tap")
    # The learning consequence, which is why this sits beside `review`. Before
    # forgoing, credit recommended the jug-smasher because smashing was on the
    # support of the water it got.

    # ⚠ The judgement, stated as a check because it is the one place this could
    # be wrong: forgoing is the DEFAULT, so an agent that should have done both
    # under-does.
    # → docs/design/selftest.md#the-judgement-stated-as-a-check-because-it-is
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
    """Doubt is deposited when the agent has more than one move -- and what that

    replaced was a SCORE. ⚠⚠⚠ THIS FUNCTION'S SUBJECT IS RETIRED, AND THE COST
    IS GATED BELOW.

    See docs/design/selftest.md#doubt-is-a-tie.
    """
    from .core.text import load

    tie = chr(10).join([
        "rule <byA> = implies( { +a(?x) }, { +at(?x) } )",
        "rule <byB> = implies( { +b(?x) }, { +at(?x) } )",
        "fact +a(p)",
        "fact +b(p)",
        "fact +goal(at(p))",
        "",
    ])
    # The control, and the reason the check above is not free: one candidate,
    # so nothing to be in two minds about.
    alone = chr(10).join([
        "rule <byA> = implies( { +a(?x) }, { +at(?x) } )",
        "fact +a(p)",
        "fact +goal(at(p))",
        "",
    ])

    def first_corpus_move(src, ignore=()):
        machine = Machine()
        load(machine, src)
        skip = {r.name for r in machine.bundle} | set(ignore)
        first = None
        for s in machine.run(limit=600):
            if first is None and s.applied and s.applied.rule.name not in skip:
                first = s.applied.rule.name
        return first, machine

    def doubted(machine):
        """`close` between two of the CORPUS's moves.

        ⚠ Not any `close` at all. The bundle is in the table too, and it is in
        two minds about its own apparatus on every run -- `close(<plan>,
        <expand>)` and `close(<ask-recall>, <ask-check>)` are deposited even by
        a corpus with a single rule. Counting those made the control below pass
        for a reason that had nothing to do with the corpus, which is the same
        mistake `first_corpus_move` already exists to avoid.
        """
        bundled = {r.name for r in machine.bundle}
        for mm in machine.chain.moments:
            for e in mm.delta:
                if machine.g.relation_of(e.proposition) is not machine.CLOSE:
                    continue
                if e.sign != PLUS:
                    continue
                names = [machine.g.show(n).strip("<>")
                         for n in machine.g.members(e.proposition)]
                if not any(n in bundled for n in names):
                    return True
        return False

    _, m = first_corpus_move(tie)
    _, solo = first_corpus_move(alone)
    check("§19", "an agent with two candidate moves deposits `close`, and one "
          "with a single candidate does not -- so the doubt is about having a "
          "CHOICE, not about a tie in any score",
          doubted(m) and not doubted(solo))
    check(
        "§14",
        "and the choice was still made -- arbitration stays total, it is just "
        "no longer silent",
        first_corpus_move(tie)[0] == "byA",
    )

    # ⚠⚠⚠ THE LOSS, ASSERTED RATHER THAN FILED. Every one of these used to move
    # the outcome; none of them moves anything now. Written as a check so that
    # the day a score-keyed mechanism comes back, this FAILS and sends whoever
    # brought it back to the paragraph above.
    variants = [
        tie + "fact +prefer(<byB>, at(p), 5)" + chr(10),
        tie + "fact +prefer(<byB>, at(p), 5)" + chr(10)
            + "fact -prefer(<byB>, at(p), 5)" + chr(10),
    ]
    outcomes = {(first_corpus_move(v)[0], doubted(first_corpus_move(v)[1]))
                for v in variants}
    check("§19", "⚠ and NOTHING a corpus can say about preference changes the "
          "move any more: a `prefer` row and its denial both give the same "
          "first move and the same doubt as the bare tie",
          outcomes == {("byA", True)})


def support_can_be_withdrawn() -> None:
    """*Nothing holds this up any more* -- the third negative existential, and

    the one that deliberately stops short of doing anything about it. ⚠ It is
    ASKED, never volunteered, for blocked's reason: a proposition may rest on
    several things, so one withdrawal says nothing until the rest have been...

    See docs/design/selftest.md#support-can-be-withdrawn.
    """
    from .core.text import load

    base = chr(10).join([
        "rule <derive> = implies( { +p(a) }, { +q(a) } )",
        # Authored after <derive>, so the conclusion is drawn before its premise
        # is withdrawn -- which is the case that matters. A premise denied before
        # anything used it leaves nothing to be unsupported.
        "rule <recant> = implies( { +told(bad) }, { -p(a) } )",
        # Asked when the loop has stopped, which is the only moment at which
        # *nothing holds this up* is about a finished search.
        "rule <ask>    = implies( { +quiet(?m) }, { +support(q(a)) } )",
        "fact +p(a)",
        "fact +told(bad)",
        "",
    ])
    m = Machine()
    kb = load(m, base)
    m.run(limit=200)

    check("§12", "the premise was withdrawn after the conclusion was drawn",
          m.holds(kb.term("p(a)")) == MINUS)
    check("§12", "and the machinery says so: nothing holds the conclusion up",
          m.holds(kb.term("unsupported(q(a))")) == PLUS)
    check(
        "§17",
        "⭐⭐⭐ ...and it did NOT retract -- losing a reason is not acquiring a "
        "counter-reason, so the claim stands until a rule says otherwise",
        m.holds(kb.term("q(a)")) == PLUS,
    )

    # The reaction, which is one corpus line and could have been three others.
    tear = base + "rule <tear> = implies( { +unsupported(?x) }, { -?x } )" + chr(10)
    m2 = Machine()
    kb2 = load(m2, tear)
    m2.run(limit=200)
    check("§19", "one corpus rule tears it down, and that is where the choice "
          "belongs -- teardown and keep-believing are both right, for different "
          "deployments",
          m2.holds(kb2.term("q(a)")) == MINUS)

    # The control: nothing was withdrawn, so nothing is unsupported. Without this
    # the answerer could be writing `unsupported` for everything it is asked.
    intact = base.replace("fact +told(bad)", "")
    m3 = Machine()
    kb3 = load(m3, intact)
    m3.run(limit=200)
    check("§15", "and with the premise intact, the same question answers nothing",
          m3.holds(kb3.term("q(a)")) == PLUS
          and m3.holds(kb3.term("unsupported(q(a))")) is None)

    # ⚠ Unsupported and false are different in BOTH directions, which is the
    # distinction the whole design of this rests on. `p(a)` is denied and yet not
    # unsupported: it was asserted, so it rests on nothing and has not lost a
    # reason -- it has been contradicted, which is a different thing.
    m4 = Machine()
    kb4 = load(m4, base + "rule <ask-p> = implies( { +quiet(?m) }, { +support(p(a)) } )" + chr(10))
    m4.run(limit=200)
    check(
        "§9",
        "⚠ a denied fact is not an unsupported one: it was asserted, so it never "
        "had a reason to lose",
        m4.holds(kb4.term("p(a)")) == MINUS
        and m4.holds(kb4.term("unsupported(p(a))")) is None,
    )

    # -- and the support is in the GRAPH now, not only in a Python field -------
    #
    # §21's defect for the ninth time. `Entry.consumed` was a Python tuple, so no
    # rule could ask what anything rested on and `why()` had to be a native walk.
    # `rests_on` joins `pred` and `in_delta` in the structural mirror: nobody
    # asserted it, it cannot be denied, dated or attributed.
    derived = m.chain.resolve(kb.term("q(a)"))
    check("§6", "an entry's support is readable from the graph",
          derived is not None and bool(m.chain.rests_on(derived)))
    check(
        "§20",
        "⚠ and it AGREES with the field it mirrors -- an index is a "
        "re-implementation of what it indexes, and only a check says they match",
        all(
            {x.node for x in mm.chain.rests_on(e)} == set(e.consumed)
            for mm in (m, m2, m3, m4)
            for moment in mm.chain.moments
            for e in moment.delta
        ),
    )


def a_binding_can_be_reconsidered() -> None:
    """The last of the four hats: *when may a binding be reconsidered?*

    It was stuck for a smaller reason than it looked. ⚠ And BOTH halves are
    needed -- either alone is worse than neither.

    See docs/design/selftest.md#a-binding-can-be-reconsidered.
    """
    from .core.text import load

    base = chr(10).join([
        "rule <boil> = implies( { +heat(?a, ?w), +water(?w) }, { +boiling(?w) } )",
        "rule <pour> = implies( { +tap(?t), +under(?w, ?t) },  { +water(?w) } )",
        "fact +tap(sink)",
        "fact +tap(butt)",
        "fact +under(kettle, sink)",
        "fact +under(kettle, butt)",
        "fact +heat(anna, kettle)",
        "fact +goal(boiling(kettle))",
        "",
    ])
    # Asked at `quiet`, which is where a recovery belongs: the loop has finished,
    # so reconsidering cannot starve anything that was still going to run.
    redo = chr(10).join([
        "rule <redo> = implies( { +quiet(?m), +binds(?p, ?v, butt), +subgoal(?p, ?s) },",
        "                      { +excluded(?p, ?v, butt), -binds(?p, ?v, butt),",
        "                        +again(check(?p, ?s), ?m) } )",
        "",
    ])

    def taps(src, limit=800):
        m = Machine()
        kb = load(m, src)
        steps = m.run(limit=limit)
        got = [m.g.show(m.g.member(e.proposition, 2))
               for mm in m.chain.moments for e in mm.delta
               if m.g.relation_of(e.proposition) is m.BINDS and e.sign == PLUS
               and m.g.show(m.g.member(e.proposition, 1)) == "?t"]
        return got, steps, m, kb

    plain, plain_steps, _, kb0 = taps(base)
    check("§18", "with nothing reconsidered, the plan binds one tap and keeps it",
          plain == ["butt"] and plain_steps[-1].state == "quiescent")

    both, both_steps, m_both, kb_both = taps(base + redo)
    check(
        "§21",
        "⭐ a rule can reconsider a binding: the plan rebinds to the other tap "
        "and still gets there",
        both == ["butt", "sink"]
        and both_steps[-1].state == "quiescent"
        and m_both.holds(kb_both.term("boiling(kettle)")) == PLUS,
    )

    only_excl, _, _, _ = taps(base + redo.replace("-binds(?p, ?v, butt),", ""))
    check("§18", "⚠ excluding alone is inert -- the surviving binding pins the "
          "variable before the exclusion is consulted",
          only_excl == ["butt"])

    only_deny, deny_steps, _, _ = taps(
        base + redo.replace("+excluded(?p, ?v, butt),", ""), limit=300)
    check(
        "§15",
        "⚠⚠⚠ ...and denying alone RUNS AWAY: the same candidate is chosen again "
        "and denied again, which is the re-ask criterion in a third place",
        len(only_deny) > 50 and deny_steps[-1].state == "applied",
    )

    # The wall this ran into, kept as a check because it is the reason the
    # exclusion is concluded by a rule and never written as a fact.
    asfact, _, _, _ = taps(
        base + "fact +excluded(plan(<pour>, water(kettle)), ?t, butt)" + chr(10))
    check(
        "§8",
        "⚠⚠ and it cannot be a corpus FACT: a statement's variables are scoped "
        "to it, so that `?t` is a different node and excludes nothing",
        asfact == ["butt"],
    )


def withdrawing_a_binding_withdraws_what_used_it() -> None:
    """The two halves of this arc composing, and the hole that stopped them.

    _settle builds its env by READING the plan's bindings, and wrote its answer
    with consumed=(e, s) -- so a conclusion that relied on *which tap* did not
    rest on the entry that said which tap. ⚠ Only the bindings the goal
    actually USES are consumed.

    See docs/design/selftest.md#withdrawing-a-binding-withdraws-what-used-it.
    """
    from .core.text import load

    base = chr(10).join([
        "rule <boil> = implies( { +heat(?a, ?w), +water(?w) }, { +boiling(?w) } )",
        "rule <pour> = implies( { +tap(?t), +under(?w, ?t) },  { +water(?w) } )",
        "fact +tap(sink)",
        "fact +tap(butt)",
        "fact +under(kettle, sink)",
        "fact +under(kettle, butt)",
        "fact +heat(anna, kettle)",
        "fact +goal(boiling(kettle))",
        "",
    ])
    drop = ("rule <drop> = implies( { +quiet(?m), +binds(?p, ?v, butt) },"
            " { -binds(?p, ?v, butt) } )" + chr(10))
    # ⚠ Asked on the DENIAL, not at `quiet`. Both rules key on the same occasion
    # otherwise, and the one authored first runs first -- so the question was
    # answered while the binding was still intact and reported nothing. §16's
    # ordering trap, in a fixture rather than in the engine.
    ask = ("rule <ask> = implies( { -binds(?p, ?v, butt) },"
           " { +support(achieved(under(kettle, ?v))) } )" + chr(10))
    intact = ("rule <askq> = implies( { +quiet(?m), +binds(?p, ?v, butt) },"
              " { +support(achieved(under(kettle, ?v))) } )" + chr(10))

    def run(src):
        m = Machine()
        load(m, src)
        m.run(limit=400)
        return {m.g.show(n) for n in m.g.instances_of(m.UNSUPPORTED)
                if m.holds(n) == PLUS}, m

    withdrawn, m1 = run(base + drop + ask)
    held, m2 = run(base + intact)

    check(
        "§12",
        "⭐ withdraw a binding and what relied on it is unsupported -- the two "
        "halves of this arc join up",
        "unsupported(achieved(under(kettle, ?t)))" in withdrawn,
    )
    check("§15", "...and with the binding intact, the same question answers nothing",
          not held)

    # The trail is what makes it work, so the trail is what is checked. Without
    # the binding among the consumed entries this is a conclusion with a premise
    # nothing records -- which is how it was for the whole arc until now.
    ach = None
    for mm in m2.chain.moments:
        for e in mm.delta:
            if m2.g.relation_of(e.proposition) is m2.ACHIEVED and e.sign == PLUS:
                if "under" in m2.g.show(e.proposition):
                    ach = e
    check(
        "R5",
        "the conclusion RESTS ON the binding it assumed, in the graph",
        ach is not None
        and any(m2.g.relation_of(x.proposition) is m2.BINDS
                for x in m2.chain.rests_on(ach)),
    )
    check(
        "§18",
        "⚠ ...and only on the bindings its own goal uses, not on every sibling's "
        "choice",
        ach is not None
        and all(
            m2.g.show(m2.g.member(x.proposition, 1)) == "?t"
            for x in m2.chain.rests_on(ach)
            if m2.g.relation_of(x.proposition) is m2.BINDS
        ),
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
    from .core.text import load

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

    # A norm is a belief, and it is consulted as one -- resolved at the
    # writer's own position, so a hypothesis can carry one.
    # → docs/design/selftest.md#a-norm-is-a-belief-and-it-is-consulted-as-one
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
    # opposite is easy to assume.
    # → docs/design/selftest.md#and-it-never-needed-the-name-which-is-worth
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
    for a fixture and wrong at scale, so it is checked against a brute-force
    walk over a world with a revision about an earlier moment, which separates
    the two orderings.

    ⚠ The walk it is checked against has SHRUNK with the read. It used to take
    the greatest `(locus depth, seat depth, position)` over every claim, filtered
    by `locus.at_or_after(e.locus)` and by *is this deposit on my branch*. Both
    filters answered questions that no longer exist, so the brute force is now
    *the last entry about this proposition, oldest moment to newest*. It is
    still a genuinely different implementation from `_claims` -- it walks the
    moments and their deltas, where the index is maintained at the deposit --
    which is the whole point of keeping it.
    """
    from .core.text import load

    m = Machine()
    kb = load(m, chr(10).join([
        "rule <a> = causes(  { +p(?x) }, { +q(?x) } )",
        "rule <b> = implies( { +q(?x) }, { +r(?x) } )",
        # ⚠ A third `causes` step, because supposing was what used to make this
        # chain deep. Without it the same fixture makes four moments where it
        # used to make more, and the breadth check below is what noticed.
        "rule <c> = causes(  { +r(?x) }, { +s(?x) } )",
        "fact +p(one)",
        "fact +p(two)",
        "",
    ]))
    m.run(limit=400)
    # A revision: a later claim about a proposition the run already settled.
    m.gate.write(kb.term("q(one)"), MINUS)
    m.gate.write(kb.term("p(three)"), PLUS)
    m.run(limit=400)

    def brute(proposition):
        """The last claim about it, found by walking rather than by index."""
        best = None
        for mo in m.chain.moments:          # oldest first, so later overwrites
            for e in mo.delta:
                if e.proposition == proposition:
                    best = e
        return best

    props = {e.proposition for mo in m.chain.moments for e in mo.delta}
    disagreements, comparisons = [], 0
    for p in props:
        comparisons += 1
        if m.chain.resolve(p) is not brute(p):
            disagreements.append(p)

    check(
        "§4",
        f"the indexed read agrees with the walk it replaced, {comparisons} comparisons",
        not disagreements,
    )
    # ⚠ The old bound was `comparisons > 1000`, and it counted seat x locus x
    # proposition. With one time there is one comparison per proposition, so the
    # number falls by three orders of magnitude and the bound has to fall with
    # it -- ⚠⚠⚠ but the thing it was GUARDING must not: a run whose chain never
    # revised anything would agree trivially.
    revised = [p for p in props if len(m.chain.claims_about(p)) > 1]
    check(
        "§4",
        "...over a world that revises, so the comparison could have failed",
        len(m.chain.moments) > 6 and comparisons > 20 and bool(revised),
    )


# ⚠⚠⚠ DELETED WITH THE SEAT: `a_cause_moves_the_register`.
#
# §17 said *every seat move is a write*, and §21 carried it as owed for as long
# as it existed. `Gate.reseat` paid it: advancing the register deposited
# `moved(?from, ?to)`, licensed by the rule that moved it, so an ordinary rule
# could read the move -- which was the point. The four checks were that the
# entry exists, that it names the seat left and the seat taken, that its licence
# is the application, and that a corpus rule matches it.
#
# ⭐ The debt is not paid off, it is DISSOLVED. There is no register to move.
# `Chain.now` is the chain's own end and nothing assigns it, so a `causes`
# application appends a moment and there is no second thing to keep in step with
# it. What `moved(?from, ?to)` reported is `pred(?to, ?from)`, which is ordinary
# skeleton and which every structural rule already reads.
#
# ⚠ `Gate.MOVED`, `Gate.FRAME` and `Gate.PROCESS` were left as dead atoms by
# this cut, and `moved` stayed in `gates/vocabulary.py`'s reserved list. All
# four are gone now -- and it was `ugm.gates.vocabulary` that found them, not a
# reading: its census reports a name that is classified and never minted, and
# it named six at once.


def reference_is_binding() -> None:
    """What a rule can refer to, and how -- measured rather than assumed.

    The question that prompted it: does a supposition need a name? a plan? Mostly
    not. Language rarely names things either; it says *the plan we made before*.
    The engine's version of that is **binding**: anything deposited as an entry
    can be bound by an antecedent, and that is reference.

    What that leaves is the harder half -- *which* one. Several plans match *a
    plan*, and nothing in a rule can say *the latest*.
    """
    from .core.text import load

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

    # ⚠ **A hypothesis used to be referable the same way** -- `left(?frame, ?a)`
    # bound the occasion of leaving one, so a corpus could name a hypothesis it
    # had never been given a name for. There are no frames to leave now, and the
    # `left`/`resume` vocabulary went with them.

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



def the_chain_mirrors_nothing_of_its_own() -> None:
    """Every field of `Entry` and `Moment` is a cache of the graph, and this is

    what holds it to that. The rule this enforces: Python may keep an index to
    make a lookup fast; it may not be the only place something is known.

    See docs/design/selftest.md#the-chain-mirrors-nothing-of-its-own.
    """
    from .core.text import load

    m = Machine()
    kb = load(m, chr(10).join([
        "rule <boil> = causes( { +heat(?a, ?w), +water(?w) }, { +boiling(?w) } )",
        "rule <warn> = implies( { +boiling(?w) }, { +doing(say(hot(?w))) } )",
        "fact +heat(anna, kettle)", "fact +water(kettle)", ""]))
    m.actuator("say")
    ch, g = m.chain, m.g
    m.run(limit=200)

    bad = []
    n_entries = 0
    for mo in ch.moments:
        for e in mo.delta:
            n_entries += 1
            if g.relation_of(e.node) is not ch.ENTRY:
                bad.append(("relation", e.node))
            # ⚠ Member 0 was the LOCUS and is the proposition now -- an entry
            # is two members, not three. A mirror check that kept the old
            # offsets would compare the proposition against a moment node and
            # report every entry as broken, which is the loud failure; the
            # quiet one is the opposite, and is why the count below matters.
            if g.member(e.node, 0) != e.proposition:
                bad.append(("proposition", e.node))
            if g.member(e.node, 1) != ch.SIGN[e.sign]:
                bad.append(("sign", e.node))
            if len(g.members(e.node)) != 2:
                bad.append(("arity", e.node))
            rests = {g.member(n, 1) for n in g.instances_of(ch.RESTS_ON)
                     if g.member(n, 0) == e.node}
            if rests != set(e.consumed):
                bad.append(("consumed", e.node))
            lic = {g.member(n, 1) for n in g.instances_of(ch.LICENSED_BY)
                   if g.member(n, 0) == e.node}
            if lic != ({e.licence} if e.licence is not None else set()):
                bad.append(("licence", e.node))
            src = {g.member(n, 1) for n in g.instances_of(ch.ARRIVED_ON)
                   if g.member(n, 0) == e.node}
            if src != ({e.source} if e.source is not None else set()):
                bad.append(("source", e.node))
            seen = any(g.member(n, 0) == e.node
                       for n in g.instances_of(ch.MENTIONED))
            if seen != bool(e.mention):
                bad.append(("mention", e.node))

    check("§20", "every Entry field is a cache of the graph and agrees with it",
          n_entries > 20 and not bad)

    mbad = []
    for mo in ch.moments:
        preds = {g.member(n, 1) for n in g.instances_of(ch.PRED)
                 if g.member(n, 0) == mo.node}
        want = {mo.predecessor.node} if mo.predecessor is not None else set()
        if preds != want:
            mbad.append(("pred", mo.node))
        in_delta = {g.member(n, 1) for n in g.instances_of(ch.IN_DELTA)
                    if g.member(n, 0) == mo.node}
        if in_delta != {e.node for e in mo.delta}:
            mbad.append(("delta", mo.node))
        walk, cur = 0, mo
        while cur.predecessor is not None:
            walk += 1
            cur = cur.predecessor
        if walk != mo.depth:
            mbad.append(("depth", mo.node))
    check("§20", "...and every Moment field is too -- pred, delta and depth",
          len(ch.moments) >= 2 and not mbad)

    # ⚠ Three mirror checks went with the span: that a `Span` is its own node
    # with two ordered members and nothing of its own but the end's depth, that
    # `locus_by_node` resolves a bound node back to EITHER kind -- the one place
    # a moment and a span met -- and that a span is interned. There is one kind
    # of locus now, and no locus, so there is nothing for either to mirror.
    check("§4", "...and a Moment carries no licence: it was written and never "
          "read, so it is not a cache of anything", not hasattr(ch.root, "licence"))
    # ⭐ ...and neither does an Entry. This is the same rule applied to the field
    # the cut removed: nothing may know an entry's locus, because there is none
    # to know, and a leftover attribute is exactly how a deleted field survives.
    check("§20", "...and an Entry has no locus field left to be a cache of "
          "nothing", not any(hasattr(e, "locus")
                             for mo in ch.moments for e in mo.delta))


def a_cached_application_can_be_retracted() -> None:
    """§6, §12. Negation as failure on a structural member is evaluated **at

    match time, and the delta-match cache carries applications across ticks --
    so a structural fact appearing later has to be able to take one back. ⚠⚠⚠
    It could not.

    See docs/design/selftest.md#a-cached-application-can-be-retracted.
    """
    from .core.rules import _stored
    from .core.text import load

    m = Machine()
    BLOCK = m.g.atom("blocks")
    m.rules.structural[BLOCK] = _stored
    m.rules._skeleton = None
    m.reserved["blocks"] = BLOCK
    kb = load(m, chr(10).join([
        "rule <act> = implies( { +person(?x), -blocks(?x) }, { +acted(?x) } )",
        "fact +person(ann)",
        "fact +person(bob)",
        "",
    ]))
    m.tick()  # one of them acts; BOTH applications are now cached
    waiting = [n for n in ("ann", "bob")
               if m.chain.holds(kb.term(f"acted({n})")) is None]
    check(
        "§6", "both applications are cached before the structural fact appears",
        len(waiting) == 1,
    )
    m.g.rel(BLOCK, kb.term(waiting[0]))
    m._structure_touched.add(BLOCK)
    m.run(limit=50)
    check(
        "§12",
        "a structural fact appearing retracts the cached application it blocks",
        m.chain.holds(kb.term(f"acted({waiting[0]})")) is None,
    )


def a_structural_member_needs_a_ground_anchor() -> None:
    """§3, §12. `_stored` refuses an unanchored pattern because it would
    enumerate the history. The test asked `is_var`, which is False for every
    relation instance -- so `licensed_by(?e, loaded(?p))` counted `loaded(?p)`
    as an anchor although nothing in it was known, and the walk read the whole
    history. Any structured argument did it: `rests_on(?e, foo(?p))`.

    ⚠ `has_var` is not the test either -- it cannot see through bindings, and
    `loaded(?p)` with `?p` bound is ground in fact and generic in shape. So the
    question is asked of the binding, recursively.
    """
    from .core.rules import _ground

    m = Machine()
    p = m.g.atom("p")
    x = m.g.var("?x")
    loaded_x = m.g.rel(m.LOADED, x)
    check("§3", "a bare variable is not an anchor", not _ground(m.g, x, {}))
    check("§3", "an atom is", _ground(m.g, p, {}))
    check(
        "§12", "a structure containing a free variable is not an anchor",
        not _ground(m.g, loaded_x, {}) and not m.g.is_var(loaded_x),
    )
    check(
        "§12", "...and the same structure IS one once the variable is bound",
        _ground(m.g, loaded_x, {x: p}),
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
    from .core.text import load

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
        m.holds(m.g.rel(m.QUIET, m.chain.now.node)) == PLUS,
    )
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


# -- docs/interpretation-feedback.md ----------------------------------------


def an_unindexed_member_says_so() -> None:
    """§3: a member that fell off the index and was answered by a scan.

    `_narrowed` cannot key a bucket on a structure that still carries a
    variable, so it falls back to every instance of the relation. That is
    correct, its own docstring sanctions the cost, and it was **silent** -- and
    a grammar is the corpus that changes the stakes, because its members are
    pattern-heavy by construction and hundreds of rules are the difference
    between a parse and a hang. The information existed at the point where it
    was discarded.

    ⚠ **Both numbers, because the count alone does not rank them.** Measured on
    `ugm.interpret` below: the member that falls back most often is not the one
    that costs most, because the relation it scans has almost nothing in it.
    """
    from .core.text import load
    from .core.attention import run as table_run
    from .probes import interpret as I

    m = Machine()
    load(m, I.SYSTEM + I.AS_FACTS, None, None)
    r = table_run(m, limit=600)
    check("§3", "a corpus whose members are pattern-heavy reports the scans it "
          "paid for -- previously silent, and the whole of the ask",
          r.scans > 0 and r.scanned_nodes > 0)
    check("§3", "...and NAMES the member, which is what an author has to go and "
          "change",
          any("(" in k or "?" in k for k in r.scanned))

    native = Machine()
    load(native, I.NATIVE, None, None)
    rn = table_run(native, limit=600)
    # ⭐ The gate: the same content authored the way the engine already reads it.
    # A counter that reported scans on ANY corpus would be noise rather than an
    # instrument -- this is the `unwebbed` direction, quiet on healthy input.
    check("§3", "...and the same content authored natively reports none, so the "
          "counter is an instrument and not a constant",
          rn.scans == 0)

    print()
    print(f"        interpreted  {r.scans:5} scans  {r.scanned_nodes:6} nodes walked")
    for k, (n, nodes) in sorted(r.scanned.items(), key=lambda kv: -kv[1][1]):
        print(f"          {n:5} x {nodes:7} nodes   {k}")
    print(f"        native       {rn.scans:5} scans  {rn.scanned_nodes:6} nodes walked")
    print("        The count and the size disagree about which member matters,")
    print("        which is why both are reported.")
    print()


def a_line_of_work_can_run_dry_unnoticed() -> None:
    """§2: widening is global, and the record of it is bound to the wrong event.

    The harness asked for a scoped widening -- *this line of work found
    nothing* rather than *the machine found nothing* -- and marked the request
    checkable and unchecked, with the honest note that if the window goes empty
    often enough in practice the request evaporates. ⚠ And the tier is reached
    only once the other line of work is exhausted, so the agent answers the
    utterance after the room goes quiet rather than while it is...

    See docs/design/selftest.md#a-line-of-work-can-run-dry-unnoticed.
    """
    from .core.text import load
    from .core.attention import run as table_run

    CORPUS = chr(10).join([
        "fact +tick(t0)",
        "fact +next(t0, t1)", "fact +next(t1, t2)", "fact +next(t2, t3)",
        "fact +next(t3, t4)", "fact +next(t4, t5)",
        "rule <upkeep> = causes( { +tick(?a), +next(?a, ?b) },",
        "                        { -tick(?a), +tick(?b) } )",
        "rule <parse>  = implies( { +heard(?w), +word(?w) }, { +read(?w) } )",
        "rule <repair> = implies( { +heard(?w) }, { +guessed(?w) } )",
        "fact standing(<upkeep>)",
        "fact standing(<parse>)",
        "fact +heard(gobln)", ""])

    m = Machine()
    kb = load(m, CORPUS)
    r = table_run(m, limit=40)
    empty = sum(1 for w in r.windows if w == 0)
    first_repair = next((i for i, n in enumerate(r.applied) if n == "repair"),
                        None)
    upkeep_left = sum(1 for n in r.applied[first_repair:] if n == "upkeep") \
        if first_repair is not None else 0

    check("§2", "the window is NEVER empty while another line of work has "
          "something to do, so the deposit that says *I had to go and get "
          "that* never fires -- the request does not evaporate",
          empty == 0)
    check("§2", "...while the shortlist widened repeatedly, which is the same "
          "event and is counted only in a Report field no rule can read",
          r.widenings > 0)
    check("§2", "...and the floor tier IS reached, so the ladder works and it "
          "is the record that is missing, not the reaching",
          m.holds(kb.term("guessed(gobln)")) == PLUS)
    check("§2", "...but only after the other line of work ran out, so the "
          "agent answers once the room has gone quiet",
          first_repair is not None and upkeep_left == 0)

    print()
    print(f"        ticks {len(r.windows)}   empty windows {empty}   "
          f"shortlist widenings {r.widenings}")
    print(f"        applied: {r.applied}")
    print("        `_widen` deposits on an empty window; the window is never")
    print("        empty; so `widened(<seat>)` and `reached(<seat>)` are")
    print("        unreachable for an agent that has any other work at all.")
    print()


def the_watcher_is_handed_the_move() -> None:
    """§4: hand `watch` the `Step` the loop has just appended.

    A watcher runs after the move, deliberately -- watching at the choice
    records a rule that never ran. The cost was that `_spend` has appended its
    refraction bookkeeping by then, so a watcher asking the chain *what did that
    move write* over-reports by a `spent(...)` term, and the harness was
    wrapping `Machine._apply` on the instance to get the honest answer. The
    `Step` already carries `wrote`.
    """
    from .core.text import load
    from .core.attention import run as table_run

    seen = []

    def watching(m, table, window, chosen, tick, step=None):
        seen.append((chosen, step))

    m = Machine()
    load(m, chr(10).join([
        "rule <a> = implies( { +p(?x) }, { +q(?x) } )",
        "fact +p(x)", ""]))
    table_run(m, limit=20, watch=watching)

    check("§4", "a watcher is handed the step the loop just appended",
          bool(seen) and all(s is not None for _c, s in seen))
    check("§4", "...and it is the step for THAT move, not the one before",
          all(s.applied is c for c, s in seen))
    check("§4", "...carrying what the application itself wrote, which is the "
          "number the harness was reaching inside the engine for",
          all(isinstance(s.wrote, tuple) for _c, s in seen))
    # ⚠ The point of the ask: `wrote` is the application's own deposit, so it
    # cannot contain the refraction bookkeeping `_spend` adds after it.
    check("§4", "...and it does NOT contain `_spend`'s refraction bookkeeping, "
          "which is what over-reported before",
          all(not any(m.g.show(e.proposition).startswith("spent(")
                      for e in s.wrote) for _c, s in seen))


def attention_is_about_a_node_not_a_rule() -> None:
    """§19: the table, keyed on a thing instead of on a rule.

    prefer(<R>, key, n) is the shipped way of saying *this is worth reaching
    for*, and everything it can say is about a RULE.

    See docs/design/selftest.md#attention-is-about-a-node-not-a-rule.
    """
    from .core.text import load
    from .core.attention import run as table_run

    def order(extra):
        m = Machine()
        load(m, chr(10).join([
            "rule <attack> = implies( { +enemy(?x) }, { +struck(?x) } )",
            "fact +enemy(goblin1)",
            "fact +enemy(goblin2)",
        ] + extra + [""]))
        rep = table_run(m, limit=6)
        return [m.g.show(list(st.applied.bindings.values())[0])
                for st in rep.steps if st.applied is not None]

    plain = order([])
    check("§18", "with nothing attended, which of two goblins is struck first "
          "is the WALK's answer -- most-recent-first, so the last declared",
          plain == ["goblin2", "goblin1"])
    check("§19", "⭐⭐⭐ attention on a node reorders a rule's own applications: "
          "the same rule, the other goblin, and no rule was named to say so",
          order(["fact +attention(goblin1)"]) == ["goblin1", "goblin2"])
    check("§18", "...and it is STABLE, so attending to what the walk already "
          "chose changes nothing -- attention overrides the tie-break where it "
          "has an opinion and defers to it everywhere else",
          order(["fact +attention(goblin2)"]) == plain)

    # ...and the rule half, which needs a table deep enough for the shortlist to
    # be a real cut: twelve rules, of which only the last three can match at all.
    rules = [f"rule <r{i}> = implies( {{ +a{i}(?x) }}, {{ +b{i}(?x) }} )"
             for i in range(12)]
    facts = [f"fact +a{i}(thing{i})" for i in (9, 10, 11)]

    def run(extra):
        m = Machine()
        load(m, chr(10).join(rules + facts + extra + [""]))
        return table_run(m, limit=20)

    bare, lifted = run([]), run(["fact +attention(thing11)"])
    check("§19", "⭐⭐⭐ a rule twelfth in the table, which no shortlist reaches "
          "without widening, applies FIRST when the thing it is about is "
          "attended",
          bare.applied[0] == "r9" and lifted.applied[0] == "r11")
    check("§19", "...and it is cheaper, not merely reordered: the shortlist "
          f"stopped widening past it ({bare.tried} rules matched over the run, "
          f"{lifted.tried} with attention)",
          lifted.tried < bare.tried and lifted.widenings < bare.widenings)
    # ⚠⚠⚠ This has now been wrong TWICE, in two different columns, and both
    # times it read as a finding.
    # → docs/design/selftest.md#this-has-now-been-wrong-twice-in-two-diff
    everything = run(["fact +attention(thing9)", "fact +attention(thing10)",
                      "fact +attention(thing11)"])
    check("§19", "⚠ attention that names everything cannot say which one "
          "matters: attend one and its rule goes first, attend three and the "
          "one you named does not",
          lifted.applied[0] == "r11" and everything.applied[0] != "r11")
    check("§19", "...and it is not that the lift stopped working -- the order "
          f"still moves ({bare.applied[:3]} bare, {everything.applied[:3]} "
          f"attended) and it is still cheaper ({bare.tried} rules matched, "
          f"{everything.tried} attended), it is just not the thing the lesson "
          "was about that came forward",
          everything.applied != bare.applied
          and everything.tried < bare.tried
          and everything.widenings < bare.widenings)
    check("§19", "⚠ and the STATE is what the lift is read through, not the "
          "graph: attending to a node the agent holds nothing about lifts "
          "nothing at all",
          run(["fact +attention(nowhere)"]).applied == bare.applied)

    # The index the rule half rests on, held to what it indexes. `ugm.state`
    # compares it on every look in the whole suite; this names it.
    m = Machine()
    kb = load(m, chr(10).join([
        "fact +enemy(goblin1)", "fact +wounded(goblin1)",
        "fact +enemy(goblin2)", ""]))
    sit = m._situation()
    rels = [m.g.show(r) for r in sit.relations_of(kb.term("goblin1"))]
    check("§3", "the state can be asked which relations a NODE is spoken of "
          "under -- the third index, and the one arriving from the end that "
          "has a node and no relation",
          sorted(rels) == ["enemy", "wounded"])
    check("§3", "...and a node nothing is claimed about is spoken of under "
          "nothing",
          sit.relations_of(kb.term("goblin1")) != []
          and m._situation().relations_of(m.g.atom("goblin3")) == [])


def attention_is_learned_from_what_the_move_bound() -> None:
    """§19: a postcondition that deposits attention, and a lesson made of them.

    ⭐⭐⭐ **Attention has to be SPENT, not won.** `docs/HANDOFF.md` 2026-08-15
    measured a learned recogniser written as a rule firing **twice out of
    sixteen**, for a structural reason: in a one-move-per-tick loop, spending a
    move on recognising something competes with doing the work. A postcondition
    is evaluated for free after whatever applied, so that is where a lesson
    about attention can live -- and `attend(?x)` says *think about what this
    move just bound*, in the host rule's own variables.

    ⚠ It is the first postcondition that DEPOSITS rather than moving a score, so
    the table does not run it: `Table.spend` stays a pure account of scores and
    the loop hands attends to the machine.
    """
    from .core.text import load
    from .core.attention import run as table_run

    base = [
        "rule <spot>   = implies( { +leader(?x) }, { +marked(?x) } )",
        "rule <strike> = implies( { +enemy(?y) }, { +struck(?y) } )",
        "fact +enemy(goblin1)",
        "fact +enemy(goblin2)",
        "fact +leader(goblin1)",
    ]

    def go(extra):
        m = Machine()
        kb = load(m, chr(10).join(base + extra + [""]))
        rep = table_run(m, limit=12)
        order = [(st.applied.rule.name,
                  m.g.show(list(st.applied.bindings.values())[0]))
                 for st in rep.steps if st.applied is not None]
        return m, kb, order

    _m, _kb, plain = go([])
    # ⭐⭐⭐ This check used to assert the opposite, and the change is the result.
    # ⚠ Which means a focus lesson no longer has to teach THIS.
    # → docs/design/selftest.md#this-check-used-to-assert-the-opposite-an
    check("§18", "⭐⭐⭐ untaught, the move after `<spot>` is already about the "
          "goblin `<spot>` bound -- the machinery attends what a move wrote, so "
          "the walk no longer decides and no lesson had to say so",
          plain == [("spot", "goblin1"), ("strike", "goblin1"),
                    ("strike", "goblin2")])

    m, kb, taught = go(["after <spot> => attend(?x)"])
    check("§19", "⭐⭐⭐ `after <spot> => attend(?x)` makes the next move about "
          "what the last one bound: the same rules, the other order, and no "
          "rule was named to say so",
          taught == [("spot", "goblin1"), ("strike", "goblin1"),
                     ("strike", "goblin2")])
    check("§19", "...and what it spent is an ordinary CLAIM, so it can be "
          "asked about",
          m.holds(kb.term("attention(goblin1)")) == PLUS)

    m2, kb2, both = go(["after <spot> => attend(?x)",
                        "after <strike> => unattend"])
    check("§19", "⚠ `unattend` is `reset` for attention, and it DENIES rather "
          "than forgets -- so a focus that has moved on is on the record",
          both == taught and m2.holds(kb2.term("attention(goblin1)")) == MINUS)

    # ...and a ranking-time trigger is now REFUSED rather than ignored. ⚠ It
    # used to be accepted and silently unable to write: _rerank ran it on rules
    # that had not applied and may never apply, so a deposit from there would
    # have...
    # → docs/design/selftest.md#and-a-ranking-time-trigger-is-now-refused-rat
    from .core.text import ParseError
    refused = None
    try:
        m3 = Machine()
        load(m3, chr(10).join(base + ["when { +leader(?z) } => attend(?z)", ""]))
    except ParseError as exc:
        refused = str(exc)
    check("§19", "⚠⚠⚠ a RANKING-time trigger is REFUSED, not quietly ignored -- "
          "nothing runs one any more, and the error says to hang the lesson off "
          "the rule that RUNS",
          refused is not None and "after <R>" in refused)


def a_lesson_about_attention_is_learned_from_play() -> None:
    """§19: the lesson, learned from an ordinary run with no teacher at all.

    The signal is **carry-over** -- the next move was about this too -- which is
    a fact about the sequence the agent produced and needs nobody's judgement.
    See `a_teacher_cannot_supervise_what_it_cannot_see` for why it cannot be
    anything else.

    ⭐ **And which variable is the whole design.** Two of `<spot>`'s variables
    carry into the following move every time; one of them is always bound to
    `red`. The one that VARIES is the one attention exists for, because
    attention is for telling two of a kind apart -- so the lesson is chosen by
    how many distinct things the variable was ever bound to, which is
    `generalise`'s own signal read one level up.
    """
    from .core.text import load
    from .core.attention import run as table_run
    from .learning.teaching import Lesson, install_focuses

    src = chr(10).join([
        "rule <spot>   = implies( { +leader(?x), +side(?s) }, { +marked(?x) } )",
        "rule <strike> = implies( { +marked(?y), +side(?t) }, { +struck(?y) } )",
        # ⚠ Was `after <spot> => boost(<strike>, 9)`. The buff's only job here
        # was to INTERLEAVE the two rules, so that what `<spot>` bound carried
        # into the next move and carry-over had something to count. `standing`
        # is the authored floor-raise and produces the identical run -- measured,
        # spot/strike three times either way -- so the fixture's subject (which
        # VARIABLE the lesson is about) is untouched by the retirement.
        "fact standing(<strike>)",
        "fact +side(red)",
        "fact +leader(g1)", "fact +leader(g2)", "fact +leader(g3)", ""])

    m = Machine()
    load(m, src)
    lesson = Lesson()
    played = table_run(m, limit=30, watch=lesson.watching)
    check("§19", "an ordinary run, watched -- no teacher, no gold, no labels",
          played.applied == ["spot", "strike"] * 3)
    check("§19", "...and both of `<spot>`'s variables carried into the next "
          "move every time, so counting carry-over alone cannot choose",
          lesson.carried[("spot", "?x")] == 3
          and lesson.carried[("spot", "?s")] == 3)

    learned = lesson.focuses(m)
    check("§19", "⭐ the variable that VARIES is the lesson: `?x` took three "
          "goblins, `?s` was always `red`, and attention is for telling two of "
          "a kind apart",
          learned["rules"]["spot"][0] == "?x")

    student = Machine()
    ldr = load(student, src)
    added = install_focuses(student, ldr, learned)
    check("§19", "...and it reads back into a machine that was never taught, "
          "as a postcondition and not as a rule",
          added == 2
          and any(any(repr(t).startswith("attend") for t, _d in buffs)
                  for _q, buffs, _f, _l in student.rules.triggers.get(
                      ldr.rules_by_name["spot"].node, ()))) 


def a_teacher_cannot_supervise_what_it_cannot_see() -> None:
    """§19: why the attention lesson is learned from play and not from the gold
    teacher.

    ⚠⚠⚠ **`arbitrate` is binding-blind, and so is every teacher built on it.**
    Its key is `(score(rule), rules.index(rule))`, so two applications of ONE
    rule tie exactly and the first in walk order wins. Asking *where did the
    table pick the wrong binding* of a teacher that cannot pick a binding
    returns nothing, for ever, and reads as a corpus with nothing to teach.

    So the signal is **carry-over**, which needs no judgement at all: the next
    move was about this too, which is a fact about the sequence the agent
    actually produced.
    """
    from .core.text import load
    from .core.rules import arbitrate

    m = Machine()
    kb = load(m, chr(10).join([
        "rule <strike> = implies( { +enemy(?y) }, { +struck(?y) } )",
        "fact +enemy(goblin1)",
        "fact +enemy(goblin2)", ""]))
    rule = kb.rules_by_name["strike"]
    apps = m._materialise([rule], m._situation())
    check("§14", "one rule, two goblins, two applications -- so there IS a "
          "binding to choose", len(apps) == 2)
    chosen = arbitrate(m.rules, apps, lambda r: ())
    check("§19", "⚠⚠⚠ ...and arbitration returns the FIRST of them whatever the "
          "priority says, because its key is over rules: a teacher built on it "
          "can never demonstrate a binding",
          chosen is apps[0]
          and arbitrate(m.rules, apps, lambda r: (99,)) is apps[0])


def a_recursion_is_a_node_with_a_phase() -> None:
    """§18: an ordered plan cannot be guarded on the state of the world.

    Hanoi's recursion is depth-first and ORDERED -- unstack, then place, then
    restack -- and ugm.hanoi records four corpora that failed before this one
    worked. ⚠ Minted per OCCASION, not per parameters, and Hanoi is where that
    stops being a nicety: solve(d1, x, z, y) occurs TWICE in a three-disk
    solution, so a call...

    See docs/design/selftest.md#a-recursion-is-a-node-with-a-phase.
    """
    import re
    from .probes.hanoi import RULES, optimal, solve

    named = sorted(set(re.findall(r"\bd\d+\b|\b[xyz]\b", RULES)))
    check("§18", "⭐ not one rule of the recursion names a disk or a peg, which "
          "is what makes the SAME corpus the answer at every size",
          named == [])

    three, four = solve(3), solve(4)
    check("§18", "⭐⭐⭐ three disks: solved, in the optimal sequence, by a "
          "corpus with no teacher and no learned table",
          three["solved"] and three["moves"] == three["optimal"]
          and len(three["moves"]) == 7)
    check("§18", "⭐⭐⭐ ...and four disks by the same rules, unchanged and "
          "unretuned -- 15 moves, identical to the recursive solution",
          four["solved"] and four["moves"] == four["optimal"]
          and len(four["moves"]) == 15)
    check("§14", "⚠ a call is minted per OCCASION: the same parameters recur "
          "within one solution, so a node keyed on them would collide with "
          "itself and refraction would block the second",
          optimal(3).count(("d1", "x", "z")) == 2)

    for rule in ("descend", "ascend", "placed"):
        gone = solve(4, without=rule, limit=2000)
        check("§18", "⚠ without <%s> the puzzle is not solved, so the phase "
              "machine is load-bearing rather than decoration" % rule,
              not gone["solved"])
    blind = solve(4, without="finished", limit=2000)
    check("§9", "⭐ ...and without <finished> it builds the tower optimally and "
          "never NOTICES: solved and knowing you are solved are two claims, and "
          "`enough` is only the second",
          blind["moves"] == blind["optimal"] and not blind["solved"])


def a_recursion_can_be_learned_from_watching_it() -> None:
    """§17: two demonstrations in, the recursion out.

    ⭐⭐⭐ What is learned is the PERMUTATION, which is the whole insight of
    Hanoi: `tower(?d,?f,?t,?s)` spawns `tower(?e,?f,?s,?t)` going down and
    `tower(?e,?s,?t,?f)` coming back. `generalise` reads both off two examples;
    nothing searches.

    ⚠ ONE demonstration is not experience -- rules that fire once are declined,
    and what is induced does not solve even the size it was taught on. That is
    the check that makes the two-demonstration result mean anything.
    """
    from .probes.hanoi import (RULES, _authored, _canonical, demonstrate, induce,
                        solve_learned)

    examples, data = demonstrate((3, 4))
    learned, declined = induce(examples)
    check("§17", "⭐ watching two authored solves induces every domain rule, "
          "with nothing declined",
          len(learned) == 12 and declined == {})
    check("§17", "...and the strategy comes off the demonstration as DATA, "
          "because the order of the steps is a fact and not a rule",
          data == ["advances(unstacking, placing)", "closes(waiting)"])

    authored = _authored()
    same = [k for k in learned
            if k in authored and _canonical(learned[k]) == _canonical(authored[k])]
    check("§17", "⭐⭐⭐ ten of the twelve are the rule a PERSON wrote, modulo "
          "what they called a variable -- including <descend> and <ascend>, "
          "whose peg permutation is the whole of Hanoi",
          len(same) == 10 and "descend" in same and "ascend" in same)
    check("§17", "⚠ and the two it misses are `d1` where a person wrote `?d`: "
          "the smallest disk is called d1 at EVERY size, so varying n never "
          "varies that argument -- what a demonstration holds constant is what "
          "a learner believes is necessary",
          sorted(set(learned) - set(same)) == ["base", "leaf"])

    five = solve_learned(5, learned, data)
    check("§17", "⭐⭐⭐ the LEARNED rules alone solve five disks -- a size never "
          "demonstrated -- in the optimal sequence",
          five["solved"] and five["moves"] == five["optimal"])

    thin, thin_data = demonstrate((3,))
    only, thin_declined = induce(thin)
    check("§17", "⚠⚠⚠ ONE demonstration is not experience: rules that fire once "
          "are declined, and what is induced does not solve even three disks",
          thin_declined != {}
          and not solve_learned(3, only, thin_data, limit=4000)["solved"])


def the_action_palette_is_declared_and_discoverable() -> None:
    """§4: what the agent may DO, as data.

    ⭐⭐⭐ conn(?r, causes) was the nearest thing to an action palette and it
    answers a different question: how a rule relates to the world, not that the
    agent may deliberately do it. ⚠ The signature is generic, so it is
    MENTIONED rather than claimed -- the gate refuses to deposit a proposition
    with a variable in it, and rightly.

    See docs/design/selftest.md#the-action-palette-is-declared-and-discoverable.
    """
    from .core.text import load

    m = Machine()
    kb = load(m, chr(10).join([
        "action move(?x, ?y)",
        "action rest(?who)",
        "rule <survey> = implies( { +afforded(?a) }, { +available(?a) } )",
        ""]))
    m.run(limit=30)
    declared = [m.g.show(m.g.member(n, 0)) for n in m.g.instances_of(m.AFFORDED)
                if m.holds(n) == PLUS]
    check("§4", "an action is declared as a SIGNATURE and lands in the graph, "
          "where the pattern is mentioned rather than claimed -- a proposition "
          "with a variable in it cannot be deposited at all",
          sorted(declared) == ["move(?x, ?y)", "rest(?who)"])

    found = [m.g.show(m.g.member(n, 0))
             for n in m.g.instances_of(kb.atoms["available"]) if m.holds(n) == PLUS]
    check("§4", "⭐ ...and a rule RANGES over the palette: one rule, every "
          "action, none of them named in it",
          sorted(found) == ["move(?x, ?y)", "rest(?who)"])

    # ⭐⭐⭐ The round trip, which is the whole argument for reifying rather than
    # keeping the palette in Python: an action declared after the rule was
    # written is still found, so a new action needs no new fallback.
    load(m, "action climb(?who, ?what)" + chr(10))
    m.run(limit=30)
    later = [m.g.show(m.g.member(n, 0))
             for n in m.g.instances_of(kb.atoms["available"]) if m.holds(n) == PLUS]
    check("§4", "⭐⭐⭐ an action declared AFTER the rule that ranges over the "
          "palette is found by it anyway -- which is what a corpus with a "
          "hand-written fallback per action can never have",
          "climb(?who, ?what)" in later)

    # And the contrast that says the mention is doing real work: the surface
    # REFUSES the same term as a fact, and says why.
    from .core.text import ParseError
    refused = None
    try:
        load(Machine(), "fact +move(?x, ?y)" + chr(10))
    except ParseError as e:
        refused = str(e)
    check("§4", "⚠ ...while the same generic term written as a FACT is refused "
          "outright -- *a fact may not contain a variable* -- which is why an "
          "action has to be a claim ABOUT a pattern and not the pattern itself",
          refused is not None and "may not contain a variable" in refused)


def a_bad_attempt_is_declined_rather_than_ignored() -> None:
    """§9: *nothing happened* and *nothing was wrong* are different answers.

    ⭐⭐⭐ docs/HANDOFF.md 19c measured the old behaviour: a policy concluding
    do(teleport, ann, pet) deposits it and nothing happens, because no action
    rule matches.

    See docs/design/selftest.md#a-bad-attempt-is-declined-rather-than-ignored.
    """
    from .probes.hanoi import misbehave
    from .core.text import load

    m = Machine()
    kb = load(m, chr(10).join([
        "action move(?x, ?y)",
        "rule <policy> = implies( { +wants(?w) }, { +attempt(?w) } )",
        "fact +wants(move(d1, z))",
        "fact +wants(teleport(ann, pet))", ""]))
    m.run(limit=60)
    check("§9", "⭐⭐⭐ an attempt at something the palette does not afford is "
          "DECLINED by the machinery, where before it was deposited and nothing "
          "happened at all",
          m.holds(kb.term("declined(teleport(ann, pet), unafforded)")) == PLUS)
    check("§9", "...and an afforded one is left alone, because whether it is "
          "LEGAL is not the machinery's question",
          m.holds(kb.term("declined(move(d1, z), unafforded)")) is None
          and m.holds(kb.term("attempt(move(d1, z))")) == PLUS)

    # ⭐⭐⭐ **The palette is the AUTHOR's**, and 19c's whole safety argument
    # rests on it: a learned rule may only REQUEST, never widen what exists.
    # Probed before this was enforced -- a rule concluding
    # `+afforded(teleport(a, b))` widened the palette, its own attempt was
    # accepted, and nothing said a word.
    greedy = Machine()
    kg = load(greedy, chr(10).join([
        "action move(?x, ?y)",
        "rule <grant> = implies( { +wants(?w) }, { +afforded(teleport(a, b)) } )",
        "fact +wants(anything)",
        "rule <try>   = implies( { +afforded(teleport(a, b)) },",
        "                       { +attempt(teleport(a, b)) } )", ""]))
    greedy.run(limit=60)
    check("§19", "⭐⭐⭐ a RULE cannot widen the action palette: it may conclude "
          "an affordance, and the attempt leaning on it is declined anyway -- "
          "an entry's licence says what produced it, and a rule's conclusion "
          "carries `applied(<R>)` where a declaration does not",
          greedy.holds(kg.term("afforded(teleport(a, b))")) == PLUS
          and greedy.holds(
              kg.term("declined(teleport(a, b), unafforded)")) == PLUS)

    bad = misbehave(3)
    check("§9", "⭐ on Hanoi, both declines happen and by different routes: a "
          "covered disk by the world model's own rule, an action that does not "
          "exist by the machinery",
          bad["covered"] and bad["unafforded"])
    check("§20", "⚠ and the world model's decline is load-bearing -- correct "
          "play never makes an illegal move, so SOLVING cannot kill that rule "
          "and the ablation had to be pointed at the misbehaviour instead",
          not misbehave(3, without="covered")["covered"])


def outstanding_business_is_not_dropped_in_silence() -> None:
    """§9: an agent may not walk away from a request without saying so.

    ⭐⭐⭐ Low priority as a PREMISE, not a score. ⚠ Both endings, and they are
    disjoint.

    See docs/design/selftest.md#outstanding-business-is-not-dropped-in-silence.
    """
    from .probes.hanoi import corpus
    from .core.text import load

    m = Machine()
    kb = load(m, "action move(?x, ?y)" + chr(10)
              + "fact +attempt(move(a, b))" + chr(10))
    m.run(limit=40)
    check("§9", "⭐ a run that RAN DRY with a request outstanding says so: "
          "nothing resolved it, and that is a fact rather than a silence",
          m.holds(kb.term("declined(move(a, b), unattended)")) == PLUS)

    # ...and the other ending, which no `quiet` ever reaches.
    sat = Machine()
    ksat = load(sat, corpus(3, "covered")
                + "fact +attempt(move(d3, y))" + chr(10))
    sat.run(limit=400)
    check("§9", "⭐⭐⭐ ...and so does one that stopped SATISFIED -- Hanoi solves "
          "the puzzle and never writes `quiet` at all, so the request would "
          "otherwise be dropped by an agent that believed itself finished",
          sat.holds(ksat.term("declined(move(d3, y), unattended)")) == PLUS)

    # The world model still gets first refusal where it has an opinion.
    own = Machine()
    kown = load(own, corpus(3) + "fact +attempt(move(d3, y))" + chr(10))
    own.run(limit=400)
    check("§9", "⚠ where the world model DOES have a rule, its own decline is "
          "what stands -- the watchdog is the last word, not the first",
          own.holds(kown.term("declined(move(d3, y), covered)")) == PLUS
          and own.holds(kown.term("declined(move(d3, y), unattended)")) is None)


def what_was_learned_is_a_document() -> None:
    """§20: a lesson you cannot read is a lesson you cannot argue with.

    ⭐⭐⭐ ugm.teaching has claimed since it was written that a lesson is *a
    document -- savable, diffable, arguable, and loadable into a corpus that
    was never taught* -- and it had no open and no write in it. ⚠ Three
    provenance levels over one construct, and only the marker tells them apart
    once they are in one file: frozen the machinery may not touch this
    (plain)...

    See docs/design/selftest.md#what-was-learned-is-a-document.
    """
    from .core.machine import Machine as M
    from .core.text import load

    m = M()
    kb = load(m, chr(10).join([
        "rule <a> = implies( { +p(?x), +s(?y) }, { +q(?x) } )",
        "rule <b> = implies( { +q(?x) }, { +r(?x) } )",
        "after <a> => attend(?x)",
        "learned after <a> => attend(?y)",
        "frozen after <a> => attend(?x)",
        "fact +p(x)", "fact +s(y)", ""]))
    posts = m.rules.triggers[kb.rules_by_name["a"].node]
    check("§20", "⭐ the surface tells an authored lesson from a learned one "
          "from a frozen one, over one construct and with no change to how any "
          "of them runs",
          [(f, l) for _q, _b, f, l in posts] == [(False, False), (False, True),
                                                 (True, False)])

    # ...and the adjustment needs no arithmetic: each one attends, and the
    # agent ends up thinking about everything they named.
    from .core.attention import Table, _standing, run as table_run
    t = Table(m.g, list(m.rules.rules), _standing(m))
    table_run(m, limit=6, table=t)
    attended = {m.g.show(n) for n in m._attended()}
    check("§20", "⭐⭐⭐ ...and a learned lesson ADJUSTS the authored one rather "
          "than replacing it -- the authored post attends `?x`, the learned one "
          "attends `?y`, and the agent is thinking about BOTH",
          {"x", "y"} <= attended)

    # The round trip: emit, load into a machine that was never taught, and the
    # lessons are there and still marked.
    from .learning.teaching import Lesson, emit, install_focuses
    from .core.attention import run as loop

    src = chr(10).join([
        "rule <spot>   = implies( { +leader(?x), +side(?s) }, { +marked(?x) } )",
        "rule <strike> = implies( { +marked(?y), +side(?t) }, { +struck(?y) } )",
        "fact standing(<strike>)",
        "fact +side(red)",
        "fact +leader(g1)", "fact +leader(g2)", "fact +leader(g3)", ""])
    played = M()
    pldr = load(played, src)
    lesson = Lesson()
    loop(played, limit=30, watch=lesson.watching)
    learned = lesson.focuses(played, conditional=True)
    doc = emit(played, pldr, learned, "a note")

    check("§20", "what was learned is ORDINARY CORPUS TEXT -- `learned after "
          "<R> ... => attend(?v)`, readable and editable",
          "learned after <spot>" in doc and "attend(" in doc
          and "# a note" in doc)

    student = M()
    sldr = load(student, src)
    sldr.load(doc)
    host = sldr.rules_by_name["spot"].node
    marks = [l for _q, _b, _f, l in student.rules.triggers.get(host, ())]
    check("§20", "⭐⭐⭐ ...and it LOADS BACK into a machine that was never "
          "taught, still marked as learned -- a document that cannot be read "
          "back is a log, not a lesson",
          marks.count(True) == 1)

    # And what the installer runs is what the document says, from one renderer.
    twin = M()
    tldr = load(twin, src)
    added = install_focuses(twin, tldr, lesson.focuses(played, conditional=True))
    check("§20", "⚠ the installer and the document come from ONE renderer, so "
          "the lesson that is inspectable is the lesson that ran",
          added == doc.count("learned after"))


def attention_is_a_bounded_queue() -> None:
    """§19: what the agent is thinking about is a QUEUE, and position is weight.

    ⭐⭐⭐ It replaces three things at once. ⚠ Decay by displacement is the better
    notion than a timer: ten quiet ticks should not forget what you were doing,
    and ten busy ones should.

    See docs/design/selftest.md#attention-is-a-bounded-queue.
    """
    from .core.machine import ATTENTION_SPAN
    from .core.text import load

    m = Machine()
    ns = [m.g.atom("n%d" % i) for i in range(ATTENTION_SPAN + 3)]
    for n in ns:
        m._push_attention(n)
    check("§19", "the queue is BOUNDED, and what fell off the bottom is "
          "forgotten -- no `unattend`, no timer, and nothing to tune but the "
          "span",
          len(m._attention) == ATTENTION_SPAN
          and m._attention[0][0] is ns[-1]
          and ns[0] not in [n for n, _w in m._attention])

    m._push_attention(ns[-3])
    check("§19", "⚠ re-attending something already held MOVES it up rather than "
          "adding it twice, or one node would crowd out everything else the "
          "agent knows it is doing",
          m._attention[0][0] is ns[-3]
          and len({n for n, _w in m._attention}) == len(m._attention))

    # The span is a knob a corpus can turn, the way `budget` already is.
    narrow = Machine()
    load(narrow, "fact +attention_span(2)" + chr(10))
    for n in [narrow.g.atom("a"), narrow.g.atom("b"), narrow.g.atom("c")]:
        narrow._push_attention(n)
    check("§19", "...and the span is a KNOB a corpus turns, so concentrating -- "
          "a steeper gradient over fewer things -- is something a corpus can "
          "say rather than something the engine decides",
          len(narrow._attention) == 2)

    # A standing claim still counts, and ranks below what is recent.
    m2 = Machine()
    kb2 = load(m2, chr(10).join([
        "rule <r> = implies( { +enemy(?x) }, { +struck(?x) } )",
        "fact +enemy(a)", "fact +enemy(b)",
        "fact +attention(a)", ""]))
    m2._push_attention(kb2.term("b"))
    order = m2._attended()
    check("§19", "⭐ a standing `attention(...)` claim is not lost, and ranks "
          "BELOW what the agent was just doing -- lasting and recent are "
          "different claims and the queue is about the second",
          order[0] is kb2.term("b") and kb2.term("a") in order)


def a_table_can_outlive_a_run() -> None:
    """§4: let a caller pass its table in.

    A host driving the agent one tick at a time rebuilds the table per step.
    With the buffs retired that is now free in general and not merely while
    nothing has moved the table: a score is `STANDING` or `FLOOR` and only
    `absorb` changes it, so a rebuilt table differs from the kept one exactly in
    the rules the agent ADOPTED since -- which is the case this check is for.

    ⚠ **The ticks continue rather than restarting.** Nothing decays any more, so
    this no longer guards a lift's age; it is what keeps the count a host can
    read monotone across calls.
    """
    from .core.text import load
    from .core.attention import Table, run as table_run, _standing

    src = chr(10).join([
        "rule <a> = implies( { +p(?x) }, { +q(?x) } )",
        "rule <b> = implies( { +q(?x) }, { +r(?x) } )",
        "fact +p(x)", ""])

    m = Machine()
    load(m, src)
    table = Table(m.g, [r for r in m.rules.rules], _standing(m))
    first = table_run(m, limit=3, table=table)
    check("§4", "a caller may hand its own table in, and gets it back",
          first.table is table)
    ticked = table.ticked
    second = table_run(m, limit=3, table=table)
    check("§4", "...and a second run continues the same table rather than a "
          "fresh one",
          second.table is table and table.ticked > ticked)
    check("§4", "...continuing the tick count rather than restarting it, so a "
          "caller stepping one tick at a time sees a monotone count and not a "
          "saw-tooth",
          table.now >= ticked)
    # A table nobody supplied is still built here, so the default path is
    # untouched -- the whole suite is the check for that, and this names it.
    plain = Machine()
    load(plain, src)
    check("§4", "...and a caller that supplies nothing still gets a table built "
          "for it, so the default path is unchanged",
          table_run(plain, limit=3).table is not None)


def the_aggregate_over_bindings_is_one_primitive() -> None:
    """§1: *how many ground matches does this pattern have here?*

    `docs/observations.md` §4 reaches this from four directions -- *nothing was
    told about this*, *it held throughout*, ***the*** goblin, *nothing has
    handled this yet* -- and they collapse to one question with an ordinary
    comparison on the answer. The three shipped asks (`rooted`, `unsupported`,
    `blocked`) are each a threshold on it, and each answers only *yes* because
    each is a negative existential. This answers with the number.

    ⭐ **The corpus writes the meaning.** Nothing below is a bundled sense of
    *the* or *ambiguous* -- they are three ordinary rules over 0, 1 and 2, which
    is *rows, not branches* at the level of the feature itself.
    """
    from .core.text import load

    SRC = chr(10).join([
        "fact +goblin(gob_a)",
        "fact +goblin(gob_b)",
        "fact +elf(elf_e)",
        "fact <goblins> = count(goblin(?x))",
        "fact <elves>   = count(elf(?x))",
        "fact <trolls>  = count(troll(?x))",
        "rule <ambiguous> = implies( { +counted(<goblins>, 2) }, { +ambiguous(g) } )",
        "rule <definite>  = implies( { +counted(<elves>, 1) },   { +definite(e) } )",
        "rule <untold>    = implies( { +counted(<trolls>, 0) },  { +untold(t) } )",
        ""])
    m = Machine()
    kb = load(m, SRC)
    m.run(limit=60)

    # ⚠ Named through `rule_nodes`, not rebuilt with `kb.term`: a statement's
    # variables are scoped to it, so re-parsing `count(goblin(?x))` mints a
    # fresh `?x` and asks about a different description. That is exactly what
    # forced the answer to be keyed on the ask, and it catches a test author
    # the same way it catches a corpus author.
    def counted(name, n):
        return m.holds(m.g.rel(m.COUNTED, kb.rule_nodes[name], m._numeral(n)))

    check("§1", "⭐⭐⭐ the machinery answers *how many things satisfy this "
          "description*, which no rule can ask -- a rule sees one binding at a "
          "time and the set lives only inside `match`",
          counted("goblins", 2) == PLUS)
    check("§1", "...and a corpus writes AMBIGUITY as an ordinary rule over the "
          "number, rather than the engine learning what two readings mean",
          m.holds(kb.term("ambiguous(g)")) == PLUS)
    check("§1", "...the definite article the same way -- exactly one satisfies "
          "it (§2.23's gap, from the corpus side)",
          m.holds(kb.term("definite(e)")) == PLUS)
    check("§1", "...and the negative existential the other two asks each "
          "special-case: nothing was told about a troll",
          m.holds(kb.term("untold(t)")) == PLUS)

    # ⚠⚠⚠ Could this have failed? A count that always answered 2 would pass the
    # first check, and a corpus reading a constant would pass the rest. Three
    # counts over one corpus, each a different number, is what makes the
    # instrument an instrument -- and the elf is the control for the goblins.
    check("§1", "⚠ and the answer TRACKS THE WORLD rather than being a "
          "constant: three descriptions over one corpus, three numbers",
          counted("elves", 1) == PLUS and counted("trolls", 0) == PLUS)


def a_count_is_not_monotone() -> None:
    """§1, and the second of the design's four constraints on it.

    A count is true of a moment and the next entry can falsify it -- so
    counted(p, 2) and counted(p, 3) are different propositions and asserting
    the second leaves the first standing. ⚠ Re-asking is the corpus's job and
    it is the ordinary discipline: a request is a fact, so it is SPENT and
    re-asserted.

    See docs/design/selftest.md#a-count-is-not-monotone.
    """
    from .core.text import load

    m = Machine()
    kb = load(m, chr(10).join([
        "fact +goblin(gob_a)",
        "fact +goblin(gob_b)",
        "fact <goblins> = count(goblin(?x))", ""]))
    m.run(limit=20)
    ask = kb.rule_nodes["goblins"]

    def counted(n):
        return m.holds(m.g.rel(m.COUNTED, ask, m._numeral(n)))

    check("§1", "the count of two goblins is two", counted(2) == PLUS)

    third = kb.term("goblin(gob_c)")
    m.gate.write(third, PLUS,
                 licence=m.g.rel(m.LOADED, third), source=m.KB)
    for sign in (MINUS, PLUS):  # spend the request, then ask again
        m.gate.write(ask, sign,
                     licence=m.g.rel(m.LOADED, ask), source=m.KB, mention=True)
    m.run(limit=20)

    check("§1", "⭐⭐⭐ ...and when the world moves and the corpus asks again, the "
          "new count lands",
          counted(3) == PLUS)
    check("§1", "...and the OLD one is denied in the same breath, so the agent "
          "never holds two answers to one question",
          counted(2) == MINUS)


def a_computed_numeral_is_not_a_twin() -> None:
    """§1, and the trap that had to be closed before any of it could be read.

    `Machine.NUMERAL` shares the small numerals so a score written in a corpus
    and a score written by a rule are one node, and `reserved` seeds every
    loader's table from it -- **but that snapshot stops at nine.** Nothing had
    ever computed a numeral, so nothing had noticed that `12` fell through to
    `g.atom` and minted one node per document.

    A count is the first thing that computes one, and a count of twelve would
    have been a twin of every authored 12: the rule fires, the fact lands, and
    every question about it answers nothing.
    """
    from .core.text import load

    src = ["fact +thing(t%d)" % i for i in range(12)]
    src += ["fact <things> = count(thing(?x))",
            "rule <dozen> = implies( { +counted(<things>, 12) }, { +dozen(yes) } )",
            ""]
    m = Machine()
    kb = load(m, chr(10).join(src))
    m.run(limit=60)
    check("§1", "⚠ a count past nine is the SAME node as the numeral a corpus "
          "wrote, so a rule can read it -- the twin trap, seventh time",
          m.holds(m.g.rel(m.COUNTED, kb.rule_nodes["things"],
                          m._numeral(12))) == PLUS
          and m.holds(kb.term("dozen(yes)")) == PLUS)


def two_things_can_turn_out_to_be_one() -> None:
    """Identity: coreference decided LATE, and what it costs to decide it.

    Until now identity was settled by construction and never inferred -- the
    loader's name table decides it at intake (text.py: *a corpus is a bound,
    kettle means one node inside it, by construction and not by inference,
    which is why coreference does not arise in authored knowledge at all*), and
    interning decides it for compounds. ⚠ The repoint is the whole of the
    implementation.

    See docs/design/selftest.md#two-things-can-turn-out-to-be-one.
    """
    from .core.text import load

    m = Machine()
    kb = load(m, chr(10).join([
        "fact +bright(morning_star)",
        "fact +rises(morning_star, dawn)",
        "fact +bright(evening_star)",
        "fact +seen_by(galileo, evening_star)", ""]))
    m.run(limit=20)
    g = m.g
    ms, es = kb.atom("morning_star"), kb.atom("evening_star")
    bright = g.relation_of(kb.term("bright(morning_star)"))
    b_ms = kb.term("bright(morning_star)")

    check("§3", "before anything is merged, two names are two things -- which "
          "is intake deciding identity, and is right until something knows "
          "better",
          b_ms != kb.term("bright(evening_star)"))

    moved = g.merge(ms, es)

    check("§3", "⭐⭐⭐ ...and once a merge says they are one thing, CONGRUENCE "
          "follows: every relationship either stood in is a relationship of the "
          "one thing, so `bright(evening)` IS `bright(morning)`",
          g.rel(bright, es) == b_ms)
    check("§3", "⚠ ...and what was said BEFORE the merge is still reachable, "
          "which is what the repoint buys -- without it the pre-merge nodes are "
          "orphaned in the index and the belief is silently gone",
          m.holds(kb.term("seen_by(galileo, evening_star)")) == PLUS
          and m.holds(kb.term("rises(morning_star, dawn)")) == PLUS
          and m.holds(kb.term("bright(evening_star)")) == PLUS)
    check("§3", "...and the merge reports what it moved, so the cost of "
          "deciding two things are one is a number rather than a mystery",
          moved > 0)

    # ⭐ The cascade. Merging two LEAVES has to unify the compounds built on
    # them, and the compounds built on those -- congruence is transitive or it
    # is not congruence.
    m2 = Machine()
    kb2 = load(m2, chr(10).join([
        "fact +knows(sam, bright(morning_star))",
        "fact +knows(sam, bright(evening_star))", ""]))
    m2.run(limit=20)
    g2 = m2.g
    k1 = kb2.term("knows(sam, bright(morning_star))")
    inner = g2.relation_of(kb2.term("bright(morning_star)"))
    g2.merge(kb2.atom("morning_star"), kb2.atom("evening_star"))
    check("§3", "⭐⭐ ...and it CASCADES: merging two leaves unifies what was "
          "built on them two levels up, or congruence stops at the first join",
          g2.rel(g2.relation_of(k1), kb2.atom("sam"),
                 g2.rel(inner, kb2.atom("evening_star"))) == k1)

    # ⚠⚠⚠ **A merge is now UNCONDITIONAL, and that is what situations cost
    # here.** Deciding two things are the same is a decision, and it used to be
    # containable: a merge made inside a branch was invisible outside it, so an
    # agent could ask *what if these were one thing* without committing. With no
    # branch there is nowhere for a tentative merge to live, and `identity_of`
    # answers the same everywhere for ever. **There is no un-merge**, so this is
    # the one deletion here that removed a guard rather than a mechanism.
    m3 = Machine()
    kb3 = load(m3, chr(10).join([
        "fact +bright(morning_star)", "fact +bright(evening_star)", ""]))
    m3.run(limit=20)
    g3 = m3.g
    a3, b3 = kb3.atom("morning_star"), kb3.atom("evening_star")
    br3 = g3.relation_of(kb3.term("bright(morning_star)"))
    g3.merge(a3, b3)
    check("§3", "⚠⚠⚠ a merge holds everywhere and cannot be taken back -- what "
          "used to be containable in a branch is now a commitment, and nothing "
          "in the engine records that it was ever in doubt",
          g3.rel(br3, b3) == kb3.term("bright(morning_star)"))

    # ⚠ The cost discipline: an unmerged graph must compute the key it computed
    # before identity existed, or every corpus that never corefers pays for one
    # that does. Asked structurally rather than by timing, because a timing
    # check on a shared machine reports the weather.
    plain = Machine()
    check("§3", "⚠ ...and a graph where nothing has merged computes the same "
          "interning key it did before identity existed, so nothing that never "
          "corefers pays for this",
          plain.g._key(1, (2, 3)) == (1, (2, 3)) and not plain.g._merges)

    # ⭐⭐⭐ TWO VOCABULARIES, AND NO RULE MENTIONS A DENOTATION. This is what the
    # identity layer is FOR, and it is the answer to *must every rule be full
    # of denoted by*. ⚠ It took three layers to be true, and each was silent on
    # its own: interning and the argument index (the candidate is filed), unify
    # (the candidate is not...
    # → docs/design/selftest.md#two-vocabularies-and-no-rule-mentions-a-d
    v = Machine()
    kbv = load(v, chr(10).join([
        "fact +owes(acme, 500)",
        "fact +debt(zeta, 900)",
        "rule <chase> = implies( { +owes(?who, ?amt) }, { +chase(?who) } )", ""]))
    v.run(limit=60)
    before = v.holds(kbv.term("chase(zeta)"))
    v.g.merge(kbv.atom("owes"), kbv.atom("debt"))
    v.run(limit=60)
    check("§3", "⭐⭐⭐ ...and once two WORDS are committed to one relationship, a "
          "rule written in one vocabulary reads the other's facts -- with no "
          "denotation anywhere in the rule",
          before is None and v.holds(kbv.term("chase(zeta)")) == PLUS
          and v.holds(kbv.term("chase(acme)")) == PLUS)


def a_rule_can_introduce_a_thing() -> None:
    """`+kind`: a consequent may name something that did not exist.

    Everything a consequent could name came from a binding or was written
    literally, so *there is some new person here* was unsayable. ⚠ Refraction
    is what stops it running away, and it already existed.

    See docs/design/selftest.md#a-rule-can-introduce-a-thing.
    """
    from .core.text import load

    m = Machine()
    kb = load(m, chr(10).join([
        "fact +said(u1, paul)",
        "fact +said(u2, paul)",
        "fact +said(u3, mary)",
        "rule <name> = implies( { +said(?u, ?x) },",
        "                       { +named(+person, ?x),",
        "                         +is(+person, person) } )", ""]))
    m.run(limit=200)
    g = m.g
    named = [n for n in g.instances_of(kb.atoms["named"]) if m.holds(n) == PLUS]
    people = {g.member(n, 0) for n in named}
    pauls = [n for n in named if g.member(n, 1) == kb.atom("paul")]

    check("§4", "⭐⭐⭐ a rule introduces a thing that did not exist -- which the "
          "binding check refuses to let a bare variable do, and rightly",
          len(named) == 3 and all(g.relation_of(p) is None for p in people))
    check("§4", "⭐⭐⭐ ...and TWO utterances of one name are two things, because "
          "the mint is per occasion and not per name",
          len(pauls) == 2 and g.member(pauls[0], 0) != g.member(pauls[1], 0))
    check("§4", "⭐ ...and one marker used twice in ONE consequent is one thing, "
          "so a rule can say several things about what it just introduced",
          all(m.holds(g.rel(kb.atoms["is"], p, kb.atom("person"))) == PLUS
              for p in people))
    check("§4", "⚠⚠⚠ ...and REFRACTION is what bounds it: three premises, three "
          "firings, three nodes -- a minting rule never re-fires on bindings it "
          "has already used, which quiescence could not have caught because a "
          "fresh node always changes something",
          len(people) == 3)

    # ⚠ The honest limit, stated because it is the failure mode this invites.
    # Refraction bounds re-firing on ONE set of premises. It cannot bound a
    # generative CHAIN -- mint, conclude about the new node, mint again -- since
    # those are different bindings every time. `bounded(ticks)` is the backstop
    # and it reports after the fact, which is exactly the static check
    # `docs/quest-feedback.md` §0 asked for and nobody has built.
    m2 = Machine()
    kb2 = load(m2, chr(10).join([
        "fact +thing(a)",
        "rule <spawn> = implies( { +thing(?x) }, { +thing(+thing) } )", ""]))
    m2.run(limit=40)
    check("§21", "⚠⚠⚠ ...but a GENERATIVE CHAIN is not bounded by refraction, and "
          "the run says so through the one record that can: `bounded(ticks)`",
          m2.holds(kb2.term("bounded(ticks)")) == PLUS)


def main() -> int:
    import sys

    if hasattr(sys.stdout, "reconfigure"):  # section signs, on a cp1252 console
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    substrate()
    chain_reads()
    a_revision_is_a_second_entry()
    gate()
    uncertainty_is_a_proposition()
    matching()
    arbitration_is_total()
    a_rule_is_a_node()
    rules_as_data()
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
    recall_is_narrowable()
    the_better_move_wins()
    an_action_is_substituted_by_its_outcome()
    an_agent_that_can_stop()
    no_goal_is_dropped_silently()
    experience_is_offline()
    a_root_goal_is_askable()
    a_request_can_be_re_asked()
    a_domain_can_be_taken_out_of_mind()
    its_own_effort_is_reasonable_over()
    the_knobs_are_claims()
    a_session_can_be_saved_and_resumed()
    the_agent_can_say_what_became_of_it()
    a_dry_search_reaches_for_what_is_out_of_mind()
    the_state_is_kept_not_rebuilt()
    a_scope_can_span_documents()
    a_rule_can_author_a_rule()
    a_computation_happens_inside_the_application()
    a_member_can_name_what_it_matched()
    a_guard_is_an_ordinary_member()
    a_verdict_names_what_it_settled()
    the_tick_limit_is_on_the_record()
    silence_over_a_stretch_is_sayable()
    the_matchers_are_one()
    a_half_finished_change_is_observable_and_actionable()
    a_reserved_name_no_longer_changes_meaning_silently()
    a_relation_can_be_named_by_a_variable()
    a_verb_is_defined_once_and_a_world_is_declared()
    an_amount_is_a_tool_and_an_unknown_amount_is_a_node()
    a_corpus_can_shorten_its_own_reasoning()
    an_example_becomes_a_rule()
    the_agent_harmonizes_itself()
    what_a_learned_rule_may_conclude()
    a_defeat_is_on_the_record()
    a_join_is_not_a_scan()
    the_apparatus_eats_its_own_cooking()
    a_rule_says_that_it_ran()
    a_tool_is_data()
    an_episode_teaches_the_next_one()
    subgoals_make_blame_sayable()
    taking_one_way_passes_up_the_others()
    doubt_is_a_tie()
    support_can_be_withdrawn()
    a_binding_can_be_reconsidered()
    withdrawing_a_binding_withdraws_what_used_it()
    prohibitions_are_not_recalled()
    the_index_agrees_with_the_walk()
    reference_is_binding()
    the_chain_mirrors_nothing_of_its_own()
    a_cached_application_can_be_retracted()
    a_structural_member_needs_a_ground_anchor()
    quiescence_is_an_occasion()
    surface()
    the_surface_can_say_what_the_apparatus_is_made_of()
    worked_examples()
    an_unindexed_member_says_so()
    a_line_of_work_can_run_dry_unnoticed()
    the_watcher_is_handed_the_move()
    a_table_can_outlive_a_run()
    the_aggregate_over_bindings_is_one_primitive()
    a_count_is_not_monotone()
    a_computed_numeral_is_not_a_twin()
    two_things_can_turn_out_to_be_one()
    a_rule_can_introduce_a_thing()
    attention_is_about_a_node_not_a_rule()
    attention_is_learned_from_what_the_move_bound()
    a_lesson_about_attention_is_learned_from_play()
    a_teacher_cannot_supervise_what_it_cannot_see()
    a_recursion_is_a_node_with_a_phase()
    a_recursion_can_be_learned_from_watching_it()
    the_action_palette_is_declared_and_discoverable()
    a_bad_attempt_is_declined_rather_than_ignored()
    outstanding_business_is_not_dropped_in_silence()
    what_was_learned_is_a_document()
    attention_is_a_bounded_queue()

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
