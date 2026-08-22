"""§20's floor gate: the rule-level read must agree with the native one.

For every bundled convention, the rule-level definition exists, and the
compiled path produces identical answers. This runs it for the one convention
an implementation is most certain to have compiled into itself -- §10's read.

See docs/design/agreement.md.
"""

from typing import List, Tuple

from ..core.chain import Chain, Moment
from ..core.machine import Machine
from ..core.text import load

# The read, as rules. Written in the surface, so this is also the
# expressibility claim: nothing here is a notation the document invented for
# the engine.  The order within a delta is walked back from a CANDIDATE, not
# closed over every entry.
# → docs/design/agreement.md#the-read-as-rules-written-in-the-surface-so-t
#
#  **`<beaten-locus>` is GONE, and every remaining rule lost a key.** The
# read used to be keyed by `(seat, locus, prop)` and ordered by locus FIRST --
# `sanc($lf, $le)` -- with the deposit order only breaking ties within one
# locus. An entry has no locus, so there is one order left and it is the one
# `<dep-within>`/`<dep-across>` already computed: **later supersedes earlier**.
#
#  This gate was not running while that was untrue. `tools_sweep.sh` grepped
# for `^def main` and this module's entry point is `run`, so nothing executed
# it -- and `entry_of` had silently gone from four arguments to three, which
# made every rule here match nothing.
READ = """
rule <cand> = implies(
  { asking($seat), anc($seat, $d), in_delta($d, $e),
    entry_of($e, $prop, $sign), asked($prop) },
  { cand($seat, $prop, $e) } )

rule <dep-within> = implies(
  { cand($seat, $prop, $e), delta_next($e, $f) },
  { dep_after($e, $f) } )

rule <dep-within-step> = implies(
  { dep_after($e, $x), delta_next($x, $f) },
  { dep_after($e, $f) } )

rule <dep-across> = implies(
  { cand($seat, $prop, $e), cand($seat, $prop, $f),
    in_delta($m, $e), in_delta($n, $f), sanc($m, $n) },
  { dep_after($e, $f) } )

rule <beaten-deposit> = implies(
  { cand($seat, $prop, $e), cand($seat, $prop, $f), dep_after($f, $e) },
  { beaten($seat, $prop, $e) } )

rule <best> = implies(
  { cand($seat, $prop, $e), -beaten($seat, $prop, $e) },
  { best($seat, $prop, $e) } )
"""

class Ambiguous(Exception):
    """More than one candidate survived. The read has no answer, and saying so is
    the point: a silent choice among them would agree with the native walk
    whenever the two happened to enumerate in the same order."""


def _fixture() -> Tuple[Machine, dict]:
    """A history with everything the read is for: inheritance, a change of the
    world, several claims in one delta, and a fork.

     It was *everything the TWO INDICES are for*, and the revision-of-the-past
    block -- three writes at `locus=m1` from a frame seated at `m3` -- went with
    them. What replaces it as the discriminating case is the run of three claims
    in ONE delta, which is what `<dep-within>` and `<dep-within-step>` order and
    what nothing else can.
    """
    m = Machine()
    g, chain, gate = m.g, m.chain, m.gate

    on = g.atom("on")
    a, b, c = g.atom("a"), g.atom("b"), g.atom("c")
    p_ab = g.rel(on, a, b)
    p_bc = g.rel(on, b, c)

    m0 = chain.root
    #  A deposit lands at the chain's end, so each write follows the `succeed`
    # that makes the moment it belongs in. The frame used to say where; nothing
    # says where now, which is why the order of these lines is the fixture.
    m1 = chain.succeed(m0, None)
    gate.write(p_ab, "+")            # asserted early, inherited later
    m2 = chain.succeed(m1, None)
    gate.write(p_bc, "+")            # a second proposition, to not answer with
    #  The fork comes BEFORE the main line continues, and it has to.
    # `Chain.resolve` says *later supersedes earlier* over the whole chain and
    # filters by no branch -- its own comment: "nothing forks, so every deposit
    # is on the one branch". Written last, the fork tip IS `chain.now`, and the
    # gate then compares a native read that ignores branches against a
    # rule-level one anchored on the other one. They disagreed, correctly, and
    # the rule-level answer was the better of the two.
    chain.succeed(m2, None)          # a fork, so ancestry is not depth
    s1 = chain.now
    gate.write(p_ab, "?")

    m3 = chain.succeed(m2, None)
    gate.write(p_ab, "-")            # the world moves: opposite sign, later

    # Three claims in ONE delta, so the order WITHIN a moment decides. This is
    # the case `<dep-within-step>` exists for -- one hop of `delta_next` is not
    # enough to beat the first of three.
    gate.write(p_bc, "?")
    gate.write(p_ab, "-")
    gate.write(p_bc, "-")

    return m, {"moments": [m0, m1, m2, s1, m3], "props": [p_ab, p_bc]}


def _ruled(m: Machine, best, proposition, seat: Moment):
    """The entry node the rule-level read returns, or None.

     `best` is resolved through the LOADER's table, not minted here. `g.atom`
    does not intern, so a `best` built beside the corpus is a twin of the one
    the rules conclude and this would answer nothing, however well the read ran.
    The trap this repo has paid for eight times.
    """
    g = m.g
    found = [
        g.members(n)[2]
        for n in g.instances_of(best)
        if not g.has_var(n)
        and g.members(n)[:2] == (seat.node, proposition)
    ]
    if len(found) > 1:
        # Never pick the first. A read answers with *one* entry, so several
        # unbeaten candidates means the ordering rules are incomplete -- and
        # taking the first would hide exactly that, agreeing with the native
        # walk by luck of enumeration order. Deleting the deposit tiebreak was
        # invisible until this raised.
        raise Ambiguous(
            f"{len(found)} unbeaten candidates for {g.show(proposition)} "
            f"from {seat}"
        )
    return found[0] if found else None


def _compare(drop: Tuple[str, ...] = ()) -> Tuple[int, List[str], int]:
    """Run every read both ways. `drop` deletes named rules from the rule-level
    path, which is how the fixture is tested for having any power at all.

     **The native side is asked from the CHAIN'S END and the rule-level side
    from each seat, and that is not a mismatch -- it is the whole remaining
    content of the gate.** `Chain.resolve` takes no seat now: it answers about
    the one standpoint there is. The rules still take one, because `asking($s)`
    is what BOUNDS the read, so they are compared at the seat that is the end.
    Every other seat is checked for a weaker property that still has teeth: the
    read anchored there must not reach past itself, so its answer is the last
    claim ON ITS OWN WALK -- which the fork makes discriminating.
    """
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
    end = m.chain.now
    checks = 0
    failures: List[str] = []
    for seat in moments:
        for p in fx["props"]:
            checks += 1
            try:
                ruled = _ruled(m, best, p, seat)
            except Ambiguous as exc:
                failures.append(f"seat={seat} {m.g.show(p)}: {exc}")
                continue
            if seat is end:
                native = m.chain.resolve(p)
                nn = None if native is None else native.node
                if nn != ruled:
                    failures.append(
                        f"seat={seat} {m.g.show(p)}: native={nn} rules={ruled}"
                    )
                continue
            # Not the end: the native read has nothing to say about this
            # standpoint, so what is checked is containment -- the answer is an
            # entry on this seat's OWN walk, and the fork is what makes that
            # able to fail.
            if ruled is None:
                continue
            got = m.chain.entry_by_node(ruled)
            mine = {n for a in seat.ancestors() for n in (a.node,)}
            where = [mo for mo in m.chain.moments if got in mo.delta]
            if not where or where[0].node not in mine:
                failures.append(
                    f"seat={seat} {m.g.show(p)}: the read reached an entry that "
                    f"is not on its own walk ({ruled})"
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
