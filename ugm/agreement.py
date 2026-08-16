"""§20's floor gate: the rule-level read must agree with the native one.

    For every bundled convention, the rule-level definition exists, and the
    compiled path produces identical answers.

This runs it for the one convention an implementation is most certain to have
compiled into itself -- §10's read. `Chain.resolve` walks in Python; the rules
below derive the same answer under **the ordinary interpreter**. If they
disagree, either the walk is not a program or the rules are wrong, and both are
worth knowing.

⭐⭐⭐ **The baseline moved, and that is the point of this commit.** Until now
the rule-level side was `stratum0.py` -- a second engine with its own rule type,
its own item type and its own solver, which §5's *one interpreter* forbids and
§6 explicitly disclaims. It is deleted. What replaces it is a list of ordinary
rules, written in the surface a corpus writes, matched by the matcher every
other rule is matched by.

Three things had to exist for that, and each is §6's own sentence made
operational rather than a new construct:

  * the **skeleton as members** -- `anc`, `in_delta`, `entry_of`, `delta_next`
    (`rules.structural_relations`), so an antecedent can mention the raw chain
    instead of the resolved state;
  * **§6's test deciding where a conclusion lands** -- *every antecedent member
    is structural* is computable, so a rule that reads only structure concludes
    structure, which is the price §6 states and the reason the circle does not
    return;
  * **negation as failure on a structural member**, which needs no notation: a
    structural member has no entry, so a `-` on one can only mean *not derived*.

    python -m ugm.agreement
"""

from typing import List, Tuple

from .chain import Chain, Moment
from .graph import Graph
from .gate import Gate
from .machine import Machine
from .text import load

# The read, as rules. Written in the surface, so this is also the expressibility
# claim: nothing here is a notation the document invented for the engine.
#
# ⚠ The order within a delta is walked back from a CANDIDATE, not closed over
# every entry. Both give `<beaten-deposit>` the same answers -- it only ever
# asks about two entries that are already candidates for one proposition -- but
# the closure is the difference between one walk per candidate and one per pair
# of entries in the history. It went unnoticed while §7 hid two thirds of the
# chain from the matcher: with the reified entries visible the same fixture
# stopped finishing at all (docs/observations.md Part 6.6).
#
# ⚠ Every member is ANCHORED, and the order is what anchors it. `anc(?seat, ?d)`
# walks upward from a bound seat; `in_delta(?d, ?e)` enumerates a bound moment's
# entries; `entry_of(?e, ...)` reads a bound entry's own three members. A member
# whose turn comes before anything binds it finds nothing -- so the authored
# order is load-bearing here in a way §12 already says it is everywhere.
READ = """
rule <cand> = implies(
  { asking(?seat), anc(?seat, ?locus), anc(?seat, ?d), in_delta(?d, ?e),
    entry_of(?e, ?x, ?prop, ?sign), asked(?prop), anc(?locus, ?x) },
  { cand(?seat, ?locus, ?prop, ?e) } )

rule <beaten-locus> = implies(
  { cand(?seat, ?locus, ?prop, ?e), cand(?seat, ?locus, ?prop, ?f),
    entry_of(?e, ?le, ?pe, ?se), entry_of(?f, ?lf, ?pf, ?sf),
    sanc(?lf, ?le) },
  { beaten(?seat, ?locus, ?prop, ?e) } )

rule <dep-within> = implies(
  { cand(?seat, ?locus, ?prop, ?e), delta_next(?e, ?f) },
  { dep_after(?e, ?f) } )

rule <dep-within-step> = implies(
  { dep_after(?e, ?x), delta_next(?x, ?f) },
  { dep_after(?e, ?f) } )

rule <dep-across> = implies(
  { cand(?seat, ?locus, ?prop, ?e), cand(?seat, ?locus, ?prop, ?f),
    in_delta(?m, ?e), in_delta(?n, ?f), sanc(?m, ?n) },
  { dep_after(?e, ?f) } )

rule <beaten-deposit> = implies(
  { cand(?seat, ?locus, ?prop, ?e), cand(?seat, ?locus, ?prop, ?f),
    entry_of(?e, ?le, ?pe, ?se), entry_of(?f, ?le, ?pf, ?sf),
    dep_after(?f, ?e) },
  { beaten(?seat, ?locus, ?prop, ?e) } )

rule <best> = implies(
  { cand(?seat, ?locus, ?prop, ?e), -beaten(?seat, ?locus, ?prop, ?e) },
  { best(?seat, ?locus, ?prop, ?e) } )
"""


class Ambiguous(Exception):
    """More than one candidate survived. The read has no answer, and saying so is
    the point: a silent choice among them would agree with the native walk
    whenever the two happened to enumerate in the same order."""


def _fixture() -> Tuple[Machine, dict]:
    """A history with everything the two indices are for: inheritance, a change
    of the world, a revision of the past, and a fork."""
    m = Machine()
    g, chain, gate = m.g, m.chain, m.gate

    on = g.atom("on")
    a, b, c = g.atom("a"), g.atom("b"), g.atom("c")
    p_ab = g.rel(on, a, b)
    p_bc = g.rel(on, b, c)

    m0 = chain.root
    m1 = chain.succeed(m0, None)
    m2 = chain.succeed(m1, None)
    m3 = chain.succeed(m2, None)

    # asserted early, inherited later -- silence means *as it was*
    gate.write(gate.frame(m1), p_ab, "+")
    # a second proposition, so a read has something to not answer with
    gate.write(gate.frame(m2), p_bc, "+")
    # the world moves: same proposition, later locus, opposite sign
    gate.write(gate.frame(m3), p_ab, "-")

    # A revision of the past: the SAME locus as the first claim, deposited later.
    # This is the one case the deposit index exists for, and it is the case a
    # fixture omits by accident -- an earlier version of this file wrote the
    # revision at a different locus, whereupon the locus key decided every read
    # and `beaten-deposit` could be deleted with no effect at all.
    # Two revisions of the same claim inside ONE moment's delta, SEPARATED by an
    # entry about something else. The delta's own order is the only thing that
    # decides between them, and the separation is what makes the order need to be
    # transitive: the entry in between does not compete, so it cannot pass the
    # verdict along. Adjacent revisions leave the transitive rule unexercised,
    # and an unexercised rule is one no fixture can kill.
    f = gate.frame(m3, topic=m1)
    gate.write(f, p_bc, "?", locus=m1)
    gate.write(f, p_ab, "-", locus=m1)
    gate.write(f, p_bc, "-", locus=m1)

    # a fork, so ancestry is not depth
    s1 = chain.succeed(m2, None)
    gate.write(gate.frame(s1), p_ab, "?")

    return m, {"moments": [m0, m1, m2, m3, s1], "props": [p_ab, p_bc]}


def _ruled(m: Machine, best, proposition, locus: Moment, seat: Moment):
    """The entry node the rule-level read returns, or None.

    ⚠ `best` is resolved through the LOADER's table, not minted here. `g.atom`
    does not intern, so a `best` built beside the corpus is a twin of the one
    the rules conclude and this would answer nothing, however well the read ran.
    The trap this repo has paid for eight times.
    """
    g = m.g
    found = [
        g.members(n)[3]
        for n in g.instances_of(best)
        if not g.has_var(n)
        and g.members(n)[:3] == (seat.node, locus.node, proposition)
    ]
    if len(found) > 1:
        # Never pick the first. A read answers with *one* entry, so several
        # unbeaten candidates means the ordering rules are incomplete -- and
        # taking the first would hide exactly that, agreeing with the native
        # walk by luck of enumeration order. Deleting the deposit tiebreak was
        # invisible until this raised.
        raise Ambiguous(
            f"{len(found)} unbeaten candidates for {g.show(proposition)} "
            f"at {locus} from {seat}"
        )
    return found[0] if found else None


def _compare(drop: Tuple[str, ...] = ()) -> Tuple[int, List[str], int]:
    """Run every read both ways. `drop` deletes named rules from the rule-level
    path, which is how the fixture is tested for having any power at all."""
    m, fx = _fixture()
    ldr = load(m, READ)
    if drop:
        m.rules.rules = [r for r in m.rules.rules if r.name not in drop]
        m.rules._skeleton = None
    best = ldr.term("best")
    # The read is anchored on the question, so the gate asks for every seat it
    # is about to compare. Each derived fact is keyed by its seat, so one
    # fixpoint answers all of them.
    m.ask_read(*fx["moments"], about=fx["props"])
    derived = m.settle_structure()

    moments: List[Moment] = fx["moments"]
    checks = 0
    failures: List[str] = []
    for seat in moments:
        for locus in moments:
            if not seat.at_or_after(locus):
                continue  # a seat that precedes its topic is meaningless (§17)
            for p in fx["props"]:
                native = m.chain.resolve(p, locus, seat)
                checks += 1
                nn = None if native is None else native.node
                try:
                    ruled = _ruled(m, best, p, locus, seat)
                except Ambiguous as exc:
                    failures.append(f"seat={seat} locus={locus} {m.g.show(p)}: {exc}")
                    continue
                if nn != ruled:
                    failures.append(
                        f"seat={seat} locus={locus} {m.g.show(p)}: "
                        f"native={nn} rules={ruled}"
                    )
    return checks, failures, derived


def run() -> int:
    checks, failures, derived = _compare()

    print("§20 floor gate -- the read, native against rule-level")
    print("  the rule-level side is ORDINARY RULES, under the ordinary matcher")
    print(f"  derived facts   {derived}")
    print(f"  reads compared  {checks}")
    for f in failures:
        print(f"  FAIL  {f}")
    if not failures:
        print("  ok    every read agrees")

    # An agreement gate that agrees is worth nothing until it is shown that it
    # could have disagreed. Delete each rule of the rule-level read in turn: a
    # rule the fixture cannot kill is a rule the fixture is not testing, and this
    # file has already been vacuous twice -- once for the deposit index and once
    # for the order within a delta.
    print()
    print("  can this fixture fail? -- one rule deleted at a time")
    names = [
        line.split("<")[1].split(">")[0]
        for line in READ.splitlines() if line.startswith("rule <")
    ]
    blind = []
    for name in names:
        _, f, _ = _compare((name,))
        print(f"    {name:18} {len(f):>3} disagree" + ("" if f else "   <-- BLIND"))
        if not f:
            blind.append(name)

    print()
    print(
        f"{checks} comparisons, {len(failures)} disagreeing; "
        f"{len(names) - len(blind)}/{len(names)} rules exercised"
    )
    return len(failures) + len(blind)


if __name__ == "__main__":
    raise SystemExit(1 if run() else 0)
