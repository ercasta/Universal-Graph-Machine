"""THE ASSEMBLY JOURNAL — `docs/design/substrate_inversion.md` §27.

§8 said a dynamically-wired system cannot be statically checked, *so the trace is the only thing there is
to inspect* — and then the assembler, the part that does the dynamic wiring, was left outside the trace
entirely. §22.1 named the fix; §26 supplied the missing half.

The test that motivates the rest is `test_a_form_can_be_accepted_and_silently_never_wired`: intake can
succeed and the network can still ignore the result, with `wellformed()` clean and the budget untouched.
That is [[book-corpus-experiment]]'s failure mode one layer below the parser.
"""
from __future__ import annotations

from units import Budget, Fact, Net, Triple, Var, given, journal as J, mint

X, Y = Var("x"), Var("y")
T = Var("t")


def _net(with_watcher: bool = False) -> Net:
    a, b, kind = mint("a"), mint("b"), mint("kind")
    n = Net()
    n.spawn(given("g", [Fact(a, "p", b)]))
    n.declare("USED", (Triple(X, "p", Y),), Triple(X, "r", Y))
    n.declare("ORPHAN", (Triple(X, "is_a", kind),), Triple(X, "seen", kind))
    if with_watcher:
        n.declare("WATCH", (Triple(T, J.UNUSED, J.NEVER_WIRED),),
                  Triple(T, "needs_attention", J.NEVER_WIRED))
    return n


def test_a_form_can_be_accepted_and_silently_never_wired():
    """⚠ THE FAILURE MODE THAT MOTIVATES §27. A template is well-formed, accepted into the library, and
    never instantiated — and before the journal, nothing anywhere said so."""
    n = _net()
    bud = n.run(Budget(500))
    assert n.instances["USED"] and not n.instances["ORPHAN"]
    assert n.wellformed() == [] and not bud.exhausted, "every other signal is clean"
    assert {f.s.name for f in n.journal.by_pred(J.UNUSED)} == {"ORPHAN"}


def test_the_journal_records_spawns_and_wires():
    n = _net()
    n.run(Budget(500))
    assert n.journal.by_pred(J.SPAWNED), "which template each instance came from"
    assert n.journal.by_pred(J.WIRE_FROM) and n.journal.by_pred(J.WIRE_TO)


def test_a_refusal_is_a_fact():
    """The assembler already refused cycles, bypasses and already-consumed projections. None of it was
    recorded, so *"what did you not consider?"* had no answer at all."""
    # A transitive closure is the shape that actually exercises refusal: unrolling repeatedly offers a
    # producer that would close a cycle, and the assembler repeatedly says no. A two-rule chain refuses
    # nothing, which is why the first version of this test measured nothing at all.
    Z = Var("z")
    ns = [mint(f"a{i}") for i in range(5)]
    n = Net()
    n.spawn(given("base", [Fact(ns[i], "next", ns[i + 1]) for i in range(4)]))
    n.declare("STEP", (Triple(X, "next", Y),), Triple(X, "reaches", Y))
    n.declare("TRANS", (Triple(X, "reaches", Y), Triple(Y, "next", Z)), Triple(X, "reaches", Z))
    n.run(Budget(3000))
    declines = n.journal.by_pred(J.DECLINED)
    assert declines, "candidates were considered and declined"
    assert {f.o.name for f in declines} == {"<would_cycle>"}


def test_a_unit_can_read_the_journal_and_notice_the_silent_failure():
    """⭐ THE POINT. *"Which forms did you accept and never use?"* becomes an ordinary rule, because an
    assembly decision is an ordinary fact. Observable, never writable — nothing here lets a unit wire
    anything, so §8's line is untouched."""
    n = _net(with_watcher=True)
    n.run(Budget(2000))
    flagged = {f.s.name for u in n.units.values() for f in u.output if f.p.name == "needs_attention"}
    assert flagged == {"ORPHAN"}


def test_the_journal_is_stable_so_the_fixpoint_survives_it():
    """§22.8's standing rule reaching a fourth construct: a wire's identity is a function of its
    endpoints, not a fresh mint, or re-running the assembler would emit a different journal every pass.

    An already-wired producer is also skipped SILENTLY — logging it as *nothing new* made the journal grow
    on every re-run of a quiesced net, and the journal rides a trace wire."""
    n = _net(with_watcher=True)
    n.run(Budget(2000))
    before = (n.journal, {u.name: u.output for u in n.units.values()})
    n.run(Budget(2000))
    assert before[0] == n.journal
    assert all(before[1][u.name] == u.output for u in n.units.values())


def test_unused_is_a_state_claim_and_is_withdrawn_when_it_stops_holding():
    """⚠ Found by building. Firings ACCRETE (§20) but `<unused>` is a CURRENT-STATE claim, so a stale one
    is a false report — and the watcher flagged ITSELF, because at the pass where orphans were computed it
    had no instance yet. It is withdrawn, and its readers refire (§7: nothing is retracted, downstream
    recomputes). Same shape as §16.6's supersession stub, reached from the journal side."""
    n = _net(with_watcher=True)
    n.run(Budget(2000))
    assert n.instances["WATCH"], "the watcher did get instantiated"
    assert "WATCH" not in {f.s.name for f in n.journal.by_pred(J.UNUSED)}
    flagged = {f.s.name for u in n.units.values() for f in u.output if f.p.name == "needs_attention"}
    assert "WATCH" not in flagged, "and its readers were refired, not left stale"


def test_the_journal_is_provenance_so_ordinary_units_cannot_see_it():
    """§23.2's test: *which fact a handle denotes* is content; *how it came about* is provenance. How the
    NETWORK came about is the same kind of thing, so journal predicates join `FIRING_PREDICATES` — which
    also means §26.1's stratification covers them for free."""
    from units import trace as TR
    assert J.JOURNAL_PREDICATES <= TR.FIRING_PREDICATES
    n = _net(with_watcher=True)
    n.run(Budget(2000))
    used = n.units[n.instances["USED"][0]]
    assert not (used.view().predicates() & J.JOURNAL_PREDICATES), "an ordinary unit sees none of it"
    assert n.trace_leaks() == []


def test_the_journal_is_not_a_unit():
    """It was one, briefly, and it polluted every count, every `wellformed` walk and every `upstream`.
    The assembler's record is not part of the computation it records."""
    n = _net()
    n.run(Budget(500))
    assert Net.JOURNAL not in n.units
    assert set(n.units) == {"g", "USED#1"}
