"""SPIKE — subset output + merge units, vs accretion (`docs/design/substrate_inversion.md` §5, §15.1).

THE PROPOSAL (user, 2026-07-26): a unit emits only a SUBSET — its own conclusion — rather than its whole
view carried through, and dedicated MERGE units recombine. `units/unit.py:97` (`view.with_facts(fresh)`)
is the entire accretion decision, so the change is one line and the question is what it costs.

WHY IT MIGHT BE FREE, and this is the hypothesis under test. `units/unit.py` already has three kinds by
degree, and `branch` is a CARRIER, not a rule. So there are two accretions, not one:

  * BRANCH accretion — a hypothesis carries base through. §3b's spawn policy DEPENDS on it: a sibling
    instance wired only to H2 sees base solely because H2 carries it ("neither feature works alone").
  * RULE accretion — a rule unit re-emits everything it read. §15.1(a) says this is what makes CYCLES the
    assembler's default, and §15.1(c) says it is what forced PROJECTION DEDUP to make assembly terminate.

If they are separable, subset-output-for-rules-only removes both guards and keeps the policy. That is
cases 2-4. Cases 1 and 5 ask what accretion was silently BUYING: inheritance of annotations (a band) and
of context markers (a relativizer), which under subset output someone must do explicitly.

DISCIPLINE: every positive verdict carries a NEGATIVE CONTROL — this repo's rule is that a trace which
confirms the hypothesis is the one to distrust. Deterministic; no `ugm/` import (the package rule).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from units.fuel import Budget                                       # noqa: E402
from units.match import Triple, Var, solve, ground                  # noqa: E402
from units.net import Net                                           # noqa: E402
from units.unit import Unit, branch, given, rule                    # noqa: E402
from units.value import EMPTY, Fact, Subgraph, mint                 # noqa: E402
from units.vocab import role

RESULTS: list = []


def report(case: str, ok: bool, detail: str) -> None:
    RESULTS.append((case, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {case}: {detail}")


# ---------------------------------------------------------------------------
# THE VARIANT. Subset output changes RULE units only; givens and carriers (which is what `branch` is)
# keep emitting their view, because a carrier IS the merge node the proposal asks for.
# ---------------------------------------------------------------------------

class AccretionUnit(Unit):
    """The OLD behaviour, kept here because the package now ships subset output (§16). A rule re-emits its
    whole view plus what it derived — which is what made cycles the assembler's default, forced projection
    dedup, and left a non-firing unit transparent instead of a gate."""

    def run(self) -> bool:
        self.runs += 1
        view = self.view()
        derived = set()
        if self.rhs:
            for b in solve(self.lhs, view):
                for head in self.rhs:
                    derived.add(ground(head, b))
        fresh = frozenset(f for f in derived if f not in view)
        new = view.with_facts(fresh) if fresh else view
        if fresh:
            self.fired += 1
        self.last_derived = fresh
        changed = new != self.output
        self.output = new
        return changed


def acc_rule(name: str, lhs, rhs) -> AccretionUnit:
    return AccretionUnit(name, lhs=tuple(lhs), rhs=(rhs,) if isinstance(rhs, Triple) else tuple(rhs))


class SubsetUnit(Unit):
    """Emits only what it DERIVED. A merge is just `kind == 'carrier'`, which already exists."""

    def run(self) -> bool:
        self.runs += 1
        view = self.view()
        derived = set()
        firing = []
        if self.rhs:
            for b in solve(self.lhs, view):
                consumed = tuple(
                    f for a in self.lhs if isinstance(a, Triple)
                    for f in view.by_pred(a.p)
                    if _matches(a, f, b)
                )
                for head in self.rhs:
                    g = ground(head, b)
                    derived.add(g)
                    firing.append((g, consumed))
        fresh = frozenset(derived)
        # THE ONE LINE. A rule emits its conclusions; anything else emits its view (= merge).
        new = Subgraph(fresh) if self.rhs else view
        if fresh:
            self.fired += 1
        self.last_derived = fresh
        self.last_firing = firing               # premises per conclusion — cases 1 and 5 need this
        changed = new != self.output
        self.output = new
        return changed


def _matches(atom: Triple, f: Fact, b: dict) -> bool:
    s = b[atom.s] if isinstance(atom.s, Var) else atom.s
    o = b[atom.o] if isinstance(atom.o, Var) else atom.o
    return f.s == s and f.p == atom.p and f.o == o


def subset_rule(name: str, lhs, rhs) -> SubsetUnit:
    u = SubsetUnit(name, lhs=tuple(lhs), rhs=(rhs,) if isinstance(rhs, Triple) else tuple(rhs))
    u.last_firing = []
    return u


def merge(name: str) -> Unit:
    """A MERGE UNIT — in-degree >= 2, no delta, no rule. §2's degree taxonomy already had this cell."""
    return Unit(name)


# ---------------------------------------------------------------------------
# An assembler whose guards can be switched OFF, so cases 2-3 can ask whether they are still needed.
# Copied from `Net.assemble` rather than imported, because the point is to vary its guards.
# ---------------------------------------------------------------------------

@dataclass
class ProbeNet(Net):
    cycle_guard: bool = True
    dedup_guard: bool = True
    subset: bool = False
    lineage_dedup: bool = False
    frontier_first: bool = False
    spawned_cycles: int = 0

    def assemble(self, budget: Budget | None = None) -> int:
        budget = budget or Budget()
        added = 0
        for tname, (lhs, rhs) in self.library.items():
            need = {a.p for a in lhs if isinstance(a, Triple)}
            seen = self.consumed.setdefault(tname, set())
            cands = list(self.units.values())
            if self.frontier_first:
                # DEEPEST FIRST. Two producers in one lineage can project identically while the deeper
                # one carries strictly more context; taking the first-seen silently picks the shallowest.
                cands.sort(key=lambda u: len(self.upstream(u.name)), reverse=True)
            for prod in cands:
                if not (prod.output.predicates() & need):
                    continue
                projection = frozenset(f for f in prod.output if f.p in need)
                if self.dedup_guard:
                    if self.lineage_dedup:
                        # A projection is only a reason to SKIP if the producer that already supplied it
                        # is in the SAME LINEAGE. Two incomparable producers can project identically and
                        # still be different contexts -- §3b's quantifier, applied to dedup.
                        if any(projection == pj and self.comparable(prod.name, other)
                               for pj, other in seen):
                            continue
                    elif any(projection == pj for pj, _ in seen):
                        continue
                if any(prod.name in self.producers.get(i, ()) for i in self.instances[tname]):
                    continue
                if not budget.spend(1, f"assemble {tname}<-{prod.name}"):
                    return added
                up = self.upstream(prod.name)
                target = None
                for iname in self.instances[tname]:
                    if iname == prod.name:
                        continue
                    if self.cycle_guard and iname in up:
                        continue
                    if iname in up:
                        self.spawned_cycles += 1        # measured, not merely permitted
                    if all(self.comparable(prod.name, q) for q in self.producers.get(iname, ())):
                        target = iname
                        break
                if target is None:
                    n = len(self.instances[tname]) + 1
                    target = f"{tname}#{n}"
                    mk = subset_rule if self.subset else acc_rule
                    self.spawn(mk(target, lhs, rhs))
                    self.instances[tname].append(target)
                    budget.spawns += 1
                self.wire(prod.name, target)
                seen.add((projection, prod.name))
                added += 1
        return added


# ---------------------------------------------------------------------------

A, B, C = "a", "b", "c"


def two_rule_chain(subset: bool, cycle_guard: bool, dedup_guard: bool):
    """base emits (x a y); R1: a -> b; R2: b -> c. §15.1(a)'s minimal cycle case."""
    x, y = mint("x"), mint("y")
    n = ProbeNet(cycle_guard=cycle_guard, dedup_guard=dedup_guard, subset=subset)
    n.spawn(given("base", [Fact(x, A, y)]))
    n.declare("R1", (Triple(Var("s"), A, Var("o")),), Triple(Var("s"), B, Var("o")))
    n.declare("R2", (Triple(Var("s"), B, Var("o")),), Triple(Var("s"), C, Var("o")))
    b = n.run(Budget(limit=4000))
    return n, b, x, y


def _has_back_edge(n) -> bool:
    return any(c in n.upstream(p) for p, cs in n.consumers.items() for c in cs)


def case_2_cycles():
    print("\nCASE 2 - are cycles the assembler's DEFAULT? (BOTH guards off, so the question is honest)")
    # With dedup ON, dedup ALREADY suppresses the re-wire -- so testing the cycle guard alone measures
    # nothing. The §15.1(a) claim is only testable with both off.
    acc_d, _, _, _ = two_rule_chain(subset=False, cycle_guard=False, dedup_guard=True)
    report("2a accretion, cycle guard off but DEDUP ON -> no cycle (dedup was masking it)",
           not _has_back_edge(acc_d), f"back edge={_has_back_edge(acc_d)} units={len(acc_d.units)}")

    acc, ab, _, _ = two_rule_chain(subset=False, cycle_guard=False, dedup_guard=False)
    sub, sb, _, _ = two_rule_chain(subset=True, cycle_guard=False, dedup_guard=False)
    report("2b accretion, BOTH off -> cycle appears (§15.1a)", _has_back_edge(acc),
           f"back edge={_has_back_edge(acc)} cycles_taken={acc.spawned_cycles} units={len(acc.units)}")
    report("2c subset, BOTH off -> still NO cycle", not _has_back_edge(sub),
           f"back edge={_has_back_edge(sub)} cycles_taken={sub.spawned_cycles} units={len(sub.units)}")


def case_3_termination():
    print("\nCASE 3 - does assembly terminate without PROJECTION DEDUP? (§15.1c)")
    acc, ab, _, _ = two_rule_chain(subset=False, cycle_guard=True, dedup_guard=False)
    sub, sb, _, _ = two_rule_chain(subset=True, cycle_guard=True, dedup_guard=False)
    report("3a accretion, dedup off -> runs away (fuel-bounded)", ab.exhausted,
           f"exhausted={ab.exhausted} spawns={ab.spawns} units={len(acc.units)}")
    report("3b subset, dedup off -> terminates on its own", not sb.exhausted,
           f"exhausted={sb.exhausted} spawns={sb.spawns} units={len(sub.units)}")


def case_4_sibling_isolation():
    """§3b / spike case 6: base + two incomparable hypothesis branches must NOT collapse."""
    print("\nCASE 4 - sibling isolation under subset output (§3b's 'neither feature works alone')")
    for label, subset, fro in (("accretion", False, False), ("subset", True, False),
                               ("subset + frontier-first", True, True)):
        jack, tall, rich, h1, h2 = mint("jack"), mint("tall"), mint("rich"), mint("h1"), mint("h2")
        n = ProbeNet(subset=subset, frontier_first=fro)
        n.spawn(given("base", [Fact(jack, "is", tall)]))
        n.spawn(branch("H1", add=[Fact(jack, "has", h1)]))
        n.spawn(branch("H2", add=[Fact(jack, "has", h2)]))
        n.wire("base", "H1")
        n.wire("base", "H2")
        n.declare("E", (Triple(Var("p"), "is", tall), Triple(Var("p"), "has", Var("h"))),
                  Triple(Var("p"), "concludes", Var("h")))
        n.run(Budget(limit=2000))
        insts = n.instances["E"]
        per = {i: {f.o.name for f in n.units[i].derived("concludes")} for i in insts}
        clean = len(insts) >= 2 and all(len(v) <= 1 for v in per.values()) and \
            {frozenset(v) for v in per.values()} == {frozenset({"h1"}), frozenset({"h2"})}
        report(f"4 {label}: two instances, one conclusion each", clean, f"{per}")


def case_1_band_inheritance():
    """Does the FIRING RECORD support annotation inheritance, and does it need to?"""
    print("\nCASE 1 - band propagation (composition_architecture.md's 'separate, larger arc')")
    lion, hungry, danger = mint("lion"), mint("hungry"), mint("dangerous")
    band75 = mint("b75")

    def build(subset: bool):
        n = ProbeNet(subset=subset)
        n.spawn(given("src", [Fact(lion, "is", hungry), Fact(hungry, "band", band75)]))
        n.declare("R", (Triple(Var("x"), "is", hungry),), Triple(Var("x"), "is", danger))
        n.run(Budget(limit=500))
        return n

    acc = build(False)
    inst = acc.instances["R"][0]
    out = acc.units[inst].output
    # Under ACCRETION the band survives as a carried fact -- but is it ON the conclusion?
    carried = any(f.p == role("band") for f in out)
    attached = any(f.p == role("band") and f.s == danger for f in out)
    report("1a accretion carries the premise's band forward", carried, f"band facts in output={carried}")
    report("1b ...but it is NOT attached to the conclusion", not attached,
           f"band on 'dangerous'={attached} -> inheritance is UNDONE either way")

    sub = build(True)
    inst = sub.instances["R"][0]
    u = sub.units[inst]
    report("1c subset output drops the band entirely", not any(f.p == role("band") for f in u.output),
           f"output={u.output}")

    # THE INHERITANCE RULE: one generic rule over the firing record, not one clause per template.
    def inherit(unit, view):
        out = set()
        for concl, consumed in getattr(unit, "last_firing", []):
            for prem in consumed:
                for bf in view.by_pred("band"):
                    if bf.s == prem.o or bf.s == prem.s:
                        out.add(Fact(concl.o, "band", bf.o))
        return out

    got = inherit(u, u.view())
    report("1d one generic inheritance rule over the firing record recovers it",
           Fact(danger, "band", band75) in got, f"derived={sorted(map(repr, got))}")

    # NEGATIVE CONTROL: with no inheritance rule the band must be ABSENT, never silently certain.
    plain = SubsetUnit("ctl", lhs=(Triple(Var("x"), "is", hungry),), rhs=(Triple(Var("x"), "is", danger),))
    plain.last_firing = []
    plain.inputs["src"] = Subgraph([Fact(lion, "is", hungry)])       # premise present, NO band fact
    plain.run()
    got2 = inherit(plain, plain.view())
    report("1e control: no band on the premise -> nothing inherited (not certainty)", not got2,
           f"derived={got2}")


def case_5_marker_relativization():
    """A context marker (`<at> t1`) is not a PREMISE, so consumed-premise inheritance cannot carry it."""
    print("\nCASE 5 - does a CONTEXT MARKER survive subset output? (form_inventory §9.3)")
    lion, mane, t1, chain = mint("lion"), mint("mane"), mint("t1"), mint("chain")
    marker = Fact(chain, "at", t1)

    # ASSEMBLED, both modes -- the question is which producer the assembler picks.
    for label, subset in (("accretion", False), ("subset", True)):
        n = ProbeNet(subset=subset)
        n.spawn(given("base", [Fact(lion, "has", mane)]))
        n.spawn(branch("T1", add=[marker]))             # the chain carries its relativizer
        n.wire("base", "T1")
        n.declare("R", (Triple(Var("x"), "has", mane),), Triple(Var("x"), "is", lion))
        n.run(Budget(limit=500))
        u = n.units[n.instances["R"][0]]
        wired = sorted(n.producers.get(u.name, ()))
        # DEFECT, recorded as an expectation: the assembler wires the SHALLOWEST producer, so the
        # marker never reaches the rule. Identical in both modes -> pre-existing, not a cost of subset.
        report(f"5a {label}: assembled instance MISSES the marker (defect, fixed in case 6)",
               marker not in u.view(), f"wired to {wired}; view={u.view()}")

    # HAND-WIRED to the branch, isolating the output question from the assembly question.
    n = ProbeNet(subset=True)
    n.spawn(given("base2", [Fact(lion, "has", mane)]))
    n.spawn(branch("T1h", add=[marker]))
    n.wire("base2", "T1h")
    n.spawn(subset_rule("Rh", (Triple(Var("x"), "has", mane),), Triple(Var("x"), "is", lion)))
    n.wire("T1h", "Rh")
    n.propagate(Budget(limit=200))
    u = n.units["Rh"]
    report("5a' hand-wired to the branch, the VIEW has the marker", marker in u.view(), f"view={u.view()}")
    report("5b but its OUTPUT does not -> downstream loses the context",
           marker not in u.output, f"output={u.output}")
    inherit_reach = any(marker in Subgraph(c) for _, c in getattr(u, "last_firing", []))
    report("5c consumed-premise inheritance CANNOT recover it (the marker was never a premise)",
           not inherit_reach, "marker is not in any firing's consumed set")

    # 5d: the architectural consequence -- wire the CONSUMER to the merge/branch as well.
    n2 = ProbeNet(subset=True)
    n2.spawn(given("base2", [Fact(lion, "has", mane)]))
    n2.spawn(branch("T1b", add=[marker]))
    n2.wire("base2", "T1b")
    n2.spawn(subset_rule("Rb", (Triple(Var("x"), "has", mane),), Triple(Var("x"), "is", lion)))
    n2.wire("T1b", "Rb")
    n2.spawn(merge("M"))
    n2.wire("Rb", "M")
    n2.wire("T1b", "M")                                 # the merge re-supplies the context
    n2.propagate(Budget(limit=200))
    ok = marker in n2.units["M"].output and Fact(lion, "is", lion) in n2.units["M"].output
    report("5d a MERGE wired to both rule and branch restores it", ok, f"merge output={n2.units['M'].output}")


def case_6_lineage_dedup():
    """The 5a defect and its candidate fix — dedup scoped to a LINEAGE, not global per template."""
    print("\nCASE 6 - is projection dedup wrong? (it skips an incomparable producer that projects alike)")
    lion, mane, t1, chain = mint("lion"), mint("mane"), mint("t1"), mint("chain")
    marker = Fact(chain, "at", t1)
    for label, lin, fro in (("global dedup (as built)", False, False),
                            ("lineage dedup", True, False),
                            ("FRONTIER-FIRST (deepest producer wins)", False, True)):
        n = ProbeNet(subset=True, lineage_dedup=lin, frontier_first=fro)
        n.spawn(given("base", [Fact(lion, "has", mane)]))
        n.spawn(branch("T1", add=[marker]))
        n.wire("base", "T1")
        n.declare("R", (Triple(Var("x"), "has", mane),), Triple(Var("x"), "is", lion))
        b = n.run(Budget(limit=500))
        sees = any(marker in n.units[i].view() for i in n.instances["R"])
        report(f"6 {label}: some instance sees the marker", sees == fro,
               f"sees={sees} instances={n.instances['R']} exhausted={b.exhausted}")

    # The fix must not reintroduce the runaway (case 3) or collapse the siblings (case 4).
    _, b3, _, _ = two_rule_chain(subset=False, cycle_guard=True, dedup_guard=True)
    n3 = ProbeNet(subset=False, frontier_first=True)
    x, y = mint("x"), mint("y")
    n3.spawn(given("base3", [Fact(x, A, y)]))
    n3.declare("R1", (Triple(Var("s"), A, Var("o")),), Triple(Var("s"), B, Var("o")))
    n3.declare("R2", (Triple(Var("s"), B, Var("o")),), Triple(Var("s"), C, Var("o")))
    b3l = n3.run(Budget(limit=4000))
    report("6c control: frontier-first still terminates under ACCRETION", not b3l.exhausted,
           f"exhausted={b3l.exhausted} units={len(n3.units)} (global-dedup baseline "
           f"exhausted={b3.exhausted})")


def case_7_gate():
    """THE GUARD (user, 2026-07-26): a chain represents scope by DEACTIVATING — a unit whose input does
    not match emits nothing, silencing everything downstream. So a bypass is not an optimization, it is
    the defeat of a guard. The question this asks is whether the guard is REAL under each mode."""
    print("\nCASE 7 - is a non-firing unit actually a GATE? (user's chain-as-guard)")
    lion, danger, key, absent = mint("lion"), mint("dangerous"), mint("key"), mint("absent")
    gate_lhs = (Triple(Var("x"), "has", key),)                  # never satisfied: nothing has `key`
    src = [Fact(lion, "is", danger)]

    for label, mk in (("accretion", lambda: AccretionUnit("G", lhs=gate_lhs, rhs=(Triple(Var("x"), "is", key),))),
                      ("subset", lambda: subset_rule("G", gate_lhs, Triple(Var("x"), "is", key)))):
        n = ProbeNet()
        n.spawn(given("src", src))
        g = n.spawn(mk())
        n.wire("src", "G")
        n.propagate(Budget(limit=100))
        leaked = Fact(lion, "is", danger) in g.output
        report(f"7 {label}: gate does not fire -> does its input LEAK downstream?",
               leaked == (label == "accretion"),
               f"fired={g.fired} output={g.output} leaked={leaked}")

    # THE BYPASS CONTROL: wire a consumer around the gate and the guard is defeated even under subset.
    n = ProbeNet()
    n.spawn(given("src2", src))
    n.spawn(subset_rule("G2", gate_lhs, Triple(Var("x"), "is", key)))
    n.wire("src2", "G2")
    n.spawn(subset_rule("D", (Triple(Var("x"), "is", danger),), Triple(Var("x"), "is", absent)))
    n.wire("G2", "D")
    n.propagate(Budget(limit=100))
    report("7c subset, gated: downstream derives NOTHING", not n.units["D"].derived(),
           f"D derived={n.units['D'].derived()}")

    n.wire("src2", "D")                                         # the skip connection
    n.propagate(Budget(limit=100))
    report("7d ...and a BYPASS wire defeats the gate", bool(n.units["D"].derived()),
           f"D derived={n.units['D'].derived()} -> a skip is not a shortcut, it is a semantic change")


def main() -> int:
    print(__doc__.split("\n\n")[0])
    case_1_band_inheritance()
    case_2_cycles()
    case_3_termination()
    case_4_sibling_isolation()
    case_5_marker_relativization()
    case_6_lineage_dedup()
    case_7_gate()
    n_ok = sum(1 for _, ok, _ in RESULTS if ok)
    print(f"\n{'=' * 78}\n{n_ok}/{len(RESULTS)} checks as predicted")
    for c, ok, d in RESULTS:
        if not ok:
            print(f"  UNEXPECTED: {c} -- {d}")
    return 0 if n_ok == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
