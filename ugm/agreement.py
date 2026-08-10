"""§20's floor gate: the rule-level read must agree with the native one.

    For every bundled convention, the rule-level definition exists, and the
    compiled path produces identical answers.

This runs it for the one convention an implementation is most certain to have
compiled into itself -- §10's read. `Chain.resolve` walks in Python;
`Stratum0.resolve` derives the same answer from rules whose antecedents mention
only structure (§6). If they disagree, either the walk is not a program or the
rules are wrong, and both are worth knowing.

    python -m ugm.agreement
"""

from typing import List, Tuple

from .chain import Chain, Moment
from .graph import Graph
from .gate import Gate
from .stratum0 import Ambiguous, Stratum0


def _fixture() -> Tuple[Graph, Chain, Gate, dict]:
    """A history with everything the two indices are for: inheritance, a change
    of the world, a revision of the past, and a fork."""
    g = Graph()
    chain = Chain(g)
    gate = Gate(g, chain)

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

    return g, chain, gate, {
        "moments": [m0, m1, m2, m3, s1],
        "props": [p_ab, p_bc],
    }


def _compare(drop: Tuple[str, ...] = ()) -> Tuple[int, List[str], int]:
    """Run every read both ways. `drop` deletes named rules from the rule-level
    path, which is how the fixture is tested for having any power at all."""
    g, chain, gate, fx = _fixture()
    s0 = Stratum0(g, chain)
    if drop:
        s0.rules = [r for r in s0.rules if r.name not in drop]
    derived = s0.run()

    moments: List[Moment] = fx["moments"]
    props = fx["props"]

    checks = 0
    failures: List[str] = []
    for seat in moments:
        for locus in moments:
            if not seat.at_or_after(locus):
                continue  # a seat that precedes its topic is meaningless (§17)
            for p in props:
                native = chain.resolve(p, locus, seat)
                checks += 1
                nn = None if native is None else native.node
                try:
                    ruled = s0.resolve(p, locus, seat)
                except Ambiguous as exc:
                    failures.append(f"seat={seat} locus={locus} {g.show(p)}: {exc}")
                    continue
                if nn != ruled:
                    failures.append(
                        f"seat={seat} locus={locus} {g.show(p)}: "
                        f"native={nn} rules={ruled}"
                    )
    return checks, failures, derived


def run() -> int:
    checks, failures, derived = _compare()

    print("§20 floor gate -- the read, native against rule-level")
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
    g, chain, _, _ = _fixture()
    names = [r.name for r in Stratum0(g, chain).rules]
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
