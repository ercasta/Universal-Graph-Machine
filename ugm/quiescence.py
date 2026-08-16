"""§20's floor gate for quiescence: the verdict *this would change nothing*,
native against rule-level.

`agreement` does it for the read, `arbitration` for the move, `state` for what
is kept. This does it for the thing that stops the loop -- `Machine._would_change`
-- which is the next item on the list Part 5 of `docs/observations.md` leaves,
and the one the rewrite was blocked on:

> several tier-3 definitions may not be expressible today, because `_recall`,
> `_would_change` and `_choose` are all aggregates over a set of matches, and a
> rule sees one binding at a time.

**They are two different aggregates, and only one of them is the gap.** §4's
missing primitive is a claim about a set of ENTRIES -- *nothing was told about
this*, *exactly one thing answers this description* -- and there a `-` member
says only *something denies it*, never *for no `?x`*. Quiescence's universal
(*no conclusion of this application would change anything*) ranges over the
application's own consequent members, which are **structure**: they have no
entry, so a `-` on one can only mean *not derived*, which is exactly the
universal wanted. So the negative existential §4 cannot state, this one states
for free -- and it is the same line `agreement`'s `<best>` already relies on.

That is the finding this file exists to hold to a number rather than assert:
`<quiet>` below is the universal, written as one negated member.

## What is compared, and what a proposal is

An application is a rule plus bindings, and bindings are not in the graph -- so
the rule-level side is handed the grounded conclusions as facts:

    proposes(<a>, <seat>, <locus>, <prop>, <sign>)

Grounding a pattern under bindings is `substitute`, which the author's line
names as permitted -- *unify* is on the substrate side, along with the walk and
the index. What is NOT handed over is the verdict: whether the proposition
already holds there, and therefore whether applying would change anything, is
derived by the rules below from `best` -- `agreement`'s rule-level read,
imported rather than copied, because a second read is a twin.

## What is out of scope, counted rather than hidden

Four branches of `_decide_change` are not compared, and the run prints how many
candidates fell into each, so that a fixture which never reaches one cannot be
read as a fixture which agreed about it:

  * **a stratum-0 rule**, whose verdict is *is this structure already in the
    graph* rather than a read. Minting `proposes(...)` interns the conclusion,
    which is the interning trap's fourth face -- the harness's question would
    consume its own answer -- so these are excluded rather than measured wrong.
  * **a forbidden conclusion**, whose verdict is about the refusal record.
    `_forbid` unifies a stored generic pattern against the proposition, and
    `unifies(?pat, ?prop)` is not a structural relation, so a rule cannot ask
    it.
  * **a conclusion at a span**, because the imported read walks `anc` over
    moments (§11).
  * **a generic conclusion** -- a rule concluding ABOUT a rule's pattern. Its
    verdict turns on §14's use/mention, and that is the one part of quiescence
    which is NOT expressible, for a reason worth stating exactly.

## The fifth branch, and it is a defect in the READ rather than in this gate

**§7 tells the matcher that a node containing a variable is a pattern rather
than a fact, and the chain's own skeleton facts about mentions contain
variables.** A reified rule is deposited as a mention, its proposition is the
rule's pattern, and that pattern has variables in it -- so the entry node does
too, and so does every `mentioned`, `in_delta` and `delta_next` fact about it.
Measured on this file's own fixture: **97 of 125 `mentioned` facts and 175 of
216 `delta_next` facts are invisible to the matcher**, although every one of
them was deposited by the chain and none was authored as a pattern.

That is why the mention half of quiescence cannot be written: the facts a rule
would need to read are exactly the ones it cannot see.

**And it breaks the read itself, which no existing gate could show.**
`delta_next` is a chain: sever one link and deposit order stops being
transitive across it. A generic entry deposited between two revisions of one
proposition in a single delta severs it, both revisions come out unbeaten, and
the rule-level read has two answers where `Chain.resolve` has one.
`ugm.agreement` reports 28/28 because its fixture deposits nothing generic;
this one reaches it in a four-line corpus. Such candidates are counted as
*could not settle* rather than as quiescence disagreeing, because misattributing
a defect is worse than not finding it -- and it is why the read's five ordering
rules come out blind below.

    python -m ugm.quiescence
"""

import os
from typing import Dict, List, Optional, Tuple

from .agreement import READ
from .machine import Machine
from .rules import Application, Member, _bounded, substitute
from .text import load, load_file

# Quiescence, as rules. Every member is structural -- the imported read's `best`
# and `entry_of`, the chain's `mentioned`, and the five relations the harness
# mints about the candidate -- so every rule here is stratum 0 by §6's own test
# and concludes structure. That is what makes the two negations below mean *not
# derived* rather than *something denies it*.
QUIET = """
rule <holds> = implies(
  { best(?seat, ?locus, ?prop, ?e), entry_of(?e, ?le, ?pe, ?sign) },
  { holds_as(?seat, ?locus, ?prop, ?sign) } )

rule <mention-inherited> = implies(
  { consumed_by(?a, ?e), mentioned(?e) },
  { mentioning(?a) } )

rule <mention-authored> = implies(
  { about_rules(?a) },
  { mentioning(?a) } )

rule <silent> = implies(
  { unbound(?a), -mentioning(?a) },
  { silent(?a) } )

rule <changes> = implies(
  { proposes(?a, ?seat, ?locus, ?prop, ?sign),
    -holds_as(?seat, ?locus, ?prop, ?sign), -silent(?a) },
  { would_change(?a) } )

rule <quiet> = implies(
  { candidate(?a), -would_change(?a) },
  { settled(?a) } )
"""

# The harness's own relations: what a candidate application IS, in the graph.
# Registered as structural for `_bounded`'s stated reason -- these exist only
# because the gate asked, so enumerating them enumerates what the anchor already
# admitted -- and because an application is machinery's own bookkeeping and not
# a claim about a world. A `-` on one has to mean *not derived*, which is what
# the whole comparison turns on.
SUPPLIED = ("candidate", "proposes", "unbound", "consumed_by", "about_rules")

# **The probe deletes nothing, and the first version did.** A rule's
# conclusion becomes structural by §6's fixpoint, so removing the rule also
# unregisters its relation -- and `strata` skips a structural relation as *the
# floor*, so `-holds_as` and `-mentioning` stopped ordering the layers that make
# them mean anything. Declaring the derived relations structural to hold the
# classification still is what I tried first, and it broke the same thing from
# the other side: 18 disagreements, every one of them the probe measuring its
# own repair. A rule is SUPPRESSED instead -- kept, still stratum 0, still in
# the dependency graph, with one member no instance can ever satisfy.
NEVER = "never-satisfied"

# The corpora used as fixtures, and how far to run each. Several stopping points
# per corpus, because a candidate set harvested only at quiescence is all quiet
# and a gate over it would agree with anything. The run prints the mix.
CORPORA = ("delay.ugm", "worked.ugm", "quest-p1.ugm")
STOPS = (0, 1, 3, 8)
# ...and a shorter set for the kill-probe, which runs the whole comparison once
# per rule. The rule-level read is a fixpoint over the chain, so it grows with
# the history; the probe asks a cheaper question -- *can deleting this rule be
# noticed at all* -- and does not need the deepest stop to answer it.
PROBE_STOPS = (0, 1, 3)

# A fourth fixture, written here because three real corpora between them reach
# none of these shapes -- and a gate whose fixture cannot reach a rule is a gate
# that reports agreement about it forever.
#
#   <keep>   two entries about one proposition in ONE delta: only deposit order
#            decides, which is what `dep-*` and `beaten-deposit` are for
#   <mess>   ...and a denial at a LATER moment, which is `beaten-locus`
#   <echo>   a conclusion that is generic because it is ABOUT a rule's pattern.
#            Its premise is a reified fact, which is a mention, so the verdict
#            turns on §14's inheritance -- <mention-inherited>
#   <attach> the other source of mention: a rule that NAMES a rule, whose vars
#            no antecedent binds or should -- <mention-authored>. It names
#            <echo>, not <keep>: a rule with no variables of its own makes the
#            conclusion GROUND, and then nothing about mention decides anything
#            and the rule reads as blind.
SHAPES = """
fact tidy(room)
fact -tidy(room)
fact dirty(room)
rule <keep> = implies( { +dirty(room) }, { +tidy(room) } )

fact clean(hall)
fact swept(hall)
rule <mess>  = causes(  { +dirty(room) }, { -clean(hall) } )
rule <again> = implies( { +swept(hall) }, { +clean(hall) } )

rule <echo>   = implies( { +con(?r, ?pat, plus, ?i) }, { +echoed(?pat) } )
rule <attach> = implies( { +swept(hall) }, { +resume(hall, <echo>) } )
"""


class Harvest:
    """One stopping point: the candidates, their native verdicts, and which of
    them the rule-level side is allowed to be asked about."""

    def __init__(self) -> None:
        self.apps: List[Application] = []
        self.native: Dict[int, bool] = {}
        self.skipped: Dict[str, int] = {
            "stratum0": 0, "forbidden": 0, "span": 0, "generic": 0,
        }


def _harvest(m: Machine) -> Harvest:
    """Every candidate application here, and `_would_change` on each.

    Taken BEFORE anything is loaded or minted. `_decide_change` calls
    `substitute`, which interns, and the stratum-0 branch asks whether the
    conclusion is already in the graph -- so a harness that minted first would
    be reading its own footprints.
    """
    h = Harvest()
    proposed = m._recall()
    state = m._situation()
    for app in m._applications(proposed, state, materialise=True):
        h.native[id(app)] = m._would_change(app)
        h.apps.append(app)
    return h


def _admissible(m: Machine, h: Harvest, app: Application) -> Optional[List[tuple]]:
    """The conclusions this application would write, as (locus, prop, sign) --
    or None if it falls in one of the four uncompared branches, tallied."""
    if m.rules.is_stratum0(app.rule):
        h.skipped["stratum0"] += 1
        return None
    out = []
    for mem in app.rule.consequent:
        grounded = substitute(m.g, mem.pattern, app.bindings)
        if m._forbid(m.focus, grounded, mem.sign) is not None:
            h.skipped["forbidden"] += 1
            return None
        at = m._conclude_at(mem, app.bindings, strict=False) or m.focus.topic
        if m.chain._moment_by_node.get(at.node) is None:
            h.skipped["span"] += 1
            return None
        out.append((at, grounded, mem.sign))
    return out


def _describe(m: Machine, ldr, h: Harvest, admitted) -> Dict[int, int]:
    """Mint what the rules read: one node per candidate and one fact per
    conclusion it would write.

    That is the whole of what is handed over. Grounding is `substitute`; the
    locus is `_conclude_at`, which is a lookup once the binding is made; the
    seat is where the register is standing. No verdict, no comparison, and
    nothing about whether the proposition already holds -- which is the half
    being tested."""
    g = m.g
    rel = {name: ldr.term(name) for name in SUPPLIED}
    names: Dict[int, int] = {}
    for i, (app, conclusions) in enumerate(admitted):
        a = g.atom(f"candidate-{i}")
        names[id(app)] = a
        g.rel(rel["candidate"], a)
        for at, grounded, sign in conclusions:
            g.rel(rel["proposes"], a, m.focus.seat.node, at.node,
                  grounded, m.rules.SIGN[sign])
            if g.has_var(grounded):
                # `has_var` is the substrate's own question about a node, so it
                # may be handed over. What it MEANS -- nothing to deposit,
                # unless the conclusion is about a rule -- is <silent>'s to say,
                # and that is the half being compared.
                g.rel(rel["unbound"], a)
        for e in app.consumed:
            g.rel(rel["consumed_by"], a, e.node)
        if app.rule.mentions:
            # The one input with no graph counterpart: `reify` records a rule's
            # members, their loci and their `as` names, and not this. The other
            # source of mention -- §14's inheritance, a conclusion drawn from a
            # mentioned entry -- is derived rather than handed over, by
            # <mention-inherited>, and until §7's test was fixed it could not be.
            g.rel(rel["about_rules"], a)
    return names


def _ambiguous(m: Machine, ldr, admitted) -> set:
    """Candidates whose verdict the rule-level READ cannot settle, because more
    than one sign survives for a proposition it would write.

    `agreement` raises on this and calls it the point: a read answers with one
    entry, so several unbeaten candidates means the ordering rules are
    incomplete. Here it is tallied instead of raised, because it is not
    quiescence's failure and hiding it inside one would misattribute the defect
    -- see the module docstring's fifth branch.
    """
    holds = {}
    for n in m.g.instances_of(ldr.term("holds_as")):
        if m.g.has_var(n):
            continue
        seat, locus, prop, sign = m.g.members(n)
        holds.setdefault((seat, locus, prop), set()).add(sign)
    out = set()
    for app, conclusions in admitted:
        for at, grounded, _ in conclusions:
            if len(holds.get((m.focus.seat.node, at.node, grounded), ())) > 1:
                out.add(id(app))
    return out


def _ruled(m: Machine, ldr, names: Dict[int, int]) -> Dict[int, Tuple[bool, bool]]:
    """The rule-level verdict for each candidate: (would_change, settled).

    Both are read, not one and its negation, because they are derived by
    different rules and a gate that read one and inverted it could not tell
    <quiet> from arithmetic.
    """
    changing = {m.g.members(n)[0] for n in m.g.instances_of(ldr.term("would_change"))}
    settled = {m.g.members(n)[0] for n in m.g.instances_of(ldr.term("settled"))}
    return {k: (a in changing, a in settled) for k, a in names.items()}


def _compare(drop: Tuple[str, ...] = (), stops: Tuple[int, ...] = STOPS) -> dict:
    tally = {
        "compared": 0, "changing": 0, "quiet": 0,
        "disagreed": [], "unsettled": [], "skipped": {"stratum0": 0, "forbidden": 0, "span": 0, "generic": 0},
        "corpora": 0, "ambiguous": 0,
    }
    for corpus in CORPORA + ("shapes",):
        for stop in stops:
            m = Machine()
            if corpus == "shapes":
                load(m, SHAPES)
            else:
                load_file(m, os.path.join(os.path.dirname(__file__), "rules", corpus))
            for _ in range(stop):
                if m.tick().state in ("stopped", "quiescent"):
                    break
            h = _harvest(m)
            admitted = []
            for app in h.apps:
                conclusions = _admissible(m, h, app)
                if conclusions is not None:
                    admitted.append((app, conclusions))
            for k, v in h.skipped.items():
                tally["skipped"][k] += v
            if not admitted:
                continue
            tally["corpora"] += 1

            # The rules go in AFTER the harvest, and the machine is not ticked
            # again: this is an observer, and a gate that added rules to a
            # running loop would be a second agent (`arbitration`'s own note).
            ldr = load(m, READ + QUIET)
            for name in SUPPLIED:
                m.rules.structural[ldr.term(name)] = _bounded
            m.rules._skeleton = None
            if drop:
                # GENERIC, and the first version was ground -- which minted
                # `candidate(never-satisfied)` and thereby created the very
                # instance it was supposed to be unable to find. Every rule of
                # the read then read as exercised-by-nothing, 0/10, which is the
                # interning trap wearing the probe's own clothes. A pattern with
                # a variable in it is skipped by `_bounded` as a pattern rather
                # than a fact (§7), so nothing can ever satisfy it.
                dead = m.g.rel(m.g.atom(NEVER), m.g.var("z"))
                m.rules.structural[m.g.relation_of(dead)] = _bounded
                m.rules._skeleton = None
                impossible = Member("+", dead)
                for r in m.rules.rules:
                    if r.name in drop:
                        r.antecedent = list(r.antecedent) + [impossible]

            names = _describe(m, ldr, h, admitted)
            # ...and about WHAT. The read is a fixpoint, so without this it
            # derives candidates, beatings and a winner for every proposition
            # the chain mentions, to answer a question about the handful this
            # gate is comparing. Measured on `agreement`'s own fixture once §7
            # stopped hiding the reified entries: 10,638 derived facts and 90
            # seconds, against 61 facts and 0.3 seconds asked this way.
            m.ask_read(m.focus.seat, about=[p for _, cs in admitted
                                            for _, p, _ in cs])
            m.settle_structure()
            verdicts = _ruled(m, ldr, names)
            ambiguous = _ambiguous(m, ldr, admitted)

            for app, _ in admitted:
                if id(app) in ambiguous:
                    tally["ambiguous"] += 1
                    continue
                native = h.native[id(app)]
                ruled, settled = verdicts[id(app)]
                tally["compared"] += 1
                tally["changing" if native else "quiet"] += 1
                if native != ruled:
                    tally["disagreed"].append(
                        f"{corpus}@{stop} {app.rule.name}: native={native} rules={ruled}"
                    )
                if settled == ruled:
                    # <quiet> is the universal, and it must be the complement of
                    # <changes> on every candidate. Equal means one of them
                    # derived nothing at all.
                    tally["unsettled"].append(
                        f"{corpus}@{stop} {app.rule.name}: "
                        f"would_change={ruled} settled={settled}"
                    )
    return tally


def _names(text: str) -> List[str]:
    return [line.split("<")[1].split(">")[0]
            for line in text.splitlines() if line.startswith("rule <")]


def run() -> int:
    t = _compare()
    print("§20 floor gate -- quiescence, native against rule-level")
    print("  the rule-level side is ORDINARY RULES, under the ordinary matcher")
    print(f"  candidates compared   {t['compared']}")
    print(f"    native says CHANGES {t['changing']}")
    print(f"    native says QUIET   {t['quiet']}")
    print(f"  and {t['ambiguous']} more the rule-level READ could not settle "
          f"-- see the fifth branch")
    print("  uncompared branches, by why:")
    for k, v in t["skipped"].items():
        print(f"    {k:10} {v}")
    for f in t["disagreed"][:6]:
        print(f"  FAIL  {f}")
    if len(t["disagreed"]) > 6:
        print(f"  ...   and {len(t['disagreed']) - 6} more")
    for f in t["unsettled"][:6]:
        print(f"  FAIL  the universal and the existential agree: {f}")
    if not t["disagreed"] and not t["unsettled"]:
        print("  ok    every verdict agrees, and <quiet> is <changes>'s complement")

    print()
    print("  can this fixture fail? -- one rule suppressed at a time")
    quiet_names = _names(QUIET)
    blind = []
    for name in quiet_names + _names(READ):
        d = _compare((name,), PROBE_STOPS)
        n = len(d["disagreed"]) + len(d["unsettled"])
        note = ""
        if name not in quiet_names:
            # The imported read's own rules. Their gate is `ugm.agreement`,
            # whose fixture is built for them; printed here because a read this
            # gate leans on is worth watching, and NOT counted as this gate's
            # blindness. The five ordering rules come out blind for a reason
            # worth reading -- see the fifth branch above: the cases that would
            # exercise them are the cases §7 turns into an ambiguous read.
            note = "   (agreement's)"
        elif not n:
            blind.append(name)
            note = "   <-- BLIND"
        print(f"    {name:18} {n:>4} disagree{note}")

    print()
    bad = len(t["disagreed"]) + len(t["unsettled"])
    print(f"{t['compared']} candidates, {bad} disagreeing; "
          f"{len(quiet_names) - len(blind)}/{len(quiet_names)} of quiescence's "
          f"own rules exercised")
    if t["changing"] == 0 or t["quiet"] == 0:
        print("  every candidate got the SAME verdict: this run measured nothing")
        return 1
    return bad + len(blind)


if __name__ == "__main__":
    raise SystemExit(1 if run() else 0)
