"""Can a tool be data? (§5, §17, §19, §21)

A tool -- a lookup, a solver, a small model -- is not a new kind of thing in
this design. ⚠ A tool mints nodes, and minting is where this design keeps
getting hurt.

See docs/design/tools.md.
"""

from typing import List, Optional

from ..core.machine import Machine
from ..core.text import Loader

WORLD = [
    "rule <ask-route> = implies( { +goal(water($w)) }, { +advice($w) } )",
    "rule <follow> = implies( { +answered(<oracle>, advice($w), $act) },"
    " { +doing($act) } )",
    "rule <eff> = implies( { +did($a), +achieves($a, $y) }, { +$y } )",
    "rule <cost> = implies( { +did(smash($j)) }, { -intact($j) } )",
    "fact +achieves(fill(kettle), water(kettle))",
    "fact +achieves(smash(jug1), water(kettle))",
    "fact +intact(jug1)",
    "fact +goal(water(kettle))",
    "fact +goal(intact(jug1))",
    "",
]


def episode(advice: Optional[str], extra: List[str] = (), scoped: bool = True):
    """One run whose route is chosen by a tool rather than by a rule.

    `advice=None` is a tool that DECLINES, which is a real answer and not a
    failure -- a tool that must answer everything is one nothing can call
    uncertain. `scoped=False` is the twin control: the same tool registered by
    name through `Machine.answerer`, which mints its own `advice` relation.
    """
    m = Machine()
    m.actuator("hands")
    kb = Loader(m)
    called: List[str] = []

    def oracle(mach, e):
        called.append(mach.g.show(e.proposition))
        return kb.term(advice) if advice else None

    if scoped:
        kb.answerer("oracle", "advice", oracle)
    else:
        a = m.answerer("oracle", "advice", oracle)
        kb.rule_nodes["oracle"], kb.rules_by_name["oracle"] = a.node, a
    kb.load("\n".join(list(extra) + WORLD))
    m.run(limit=400)
    return m, kb, called


def main() -> int:
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    failing = 0
    ran = 0

    def gate(name: str, ok: bool) -> None:
        nonlocal failing, ran
        ran += 1
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
        if not ok:
            failing += 1

    print("Can a tool be data?\n")

    good, kb, called = episode("fill(kettle)")
    bad, kbb, _ = episode("smash(jug1)")
    quiet, kbq, called_q = episode(None)

    print(f"  {'the tool advised':<20} {'emitted':<16} {'jug':<8} "
          f"{'credited':<34} blamed")
    for label, m, k in (("fill(kettle)", good, kb), ("smash(jug1)", bad, kbb),
                        ("nothing", quiet, kbq)):
        acts = [m.g.show(n) for n in m.emitted]
        print(f"  {label:<20} {acts[0] if acts else '-':<16} "
              f"{('broken' if m.holds(k.term('intact(jug1)')) == '-' else 'intact'):<8} "
              f"{','.join(sorted({r.name for r,_ in m.review()})) or '-':<34} "
              f"{','.join(sorted({r.name for r,_ in m.blame()})) or '-'}")
    print()

    # -- the binding is data ----------------------------------------------
    gate("the binding is an ordinary fact a corpus can ask about (R4)",
         good.holds(kb.term("answers(<oracle>, advice)")) == "+")
    gate("what the tool said is on the record, as a record and not a claim",
         good.holds(kb.term("answered(<oracle>, advice(kettle), fill(kettle))")) == "+")

    retired, kbr, called_r = episode("smash(jug1)",
                                     extra=["fact -answers(<oracle>, advice)"])
    gate("⭐ a corpus can RETIRE a tool -- the one thing a Python-registered "
         "hook could never be",
         not called_r and not retired.emitted)

    # -- propose, never conclude ------------------------------------------
    no_trust = [ln for ln in WORLD if "<follow>" not in ln]
    m2 = Machine()
    m2.actuator("hands")
    kb2 = Loader(m2)
    kb2.answerer("oracle", "advice", lambda mach, e: kb2.term("smash(jug1)"))
    kb2.load("\n".join(no_trust))
    m2.run(limit=400)
    gate("⭐⭐⭐ a tool PROPOSES: delete the trust rule and the answer is on the "
         "record, believed by nobody, and no act leaves the agent",
         m2.holds(kb2.term("answered(<oracle>, advice(kettle), smash(jug1))")) == "+"
         and not m2.emitted)

    m3 = Machine()
    kb3 = Loader(m3)
    kb3.answerer("oracle", "guess", lambda mach, e: kb3.atom("vessel"))
    kb3.load("\n".join([
        "rule <ask> = implies( { +thing($x) }, { +guess($x) } )",
        "rule <trust> = implies( { +answered(<oracle>, guess($x), $k) },"
        " { +possible(kind($x, $k)) } )",
        "fact +thing(kettle)", ""]))
    m3.run(limit=80)
    # ⚠ The corpus's WRAPPER, where this used to read the corpus's GRADE. Same
    # argument, and now a rule can act on it: what the tool said is believed
    # only as `possible(...)`, and the bare claim is never asserted.
    gate("...and the CORPUS governs, not the tool's confidence -- a "
         "certain-sounding tool cannot launder a weak answer",
         m3.holds(kb3.term("possible(kind(kettle, vessel))")) == "+"
         and m3.holds(kb3.term("kind(kettle, vessel)")) is None)

    gate("a tool may DECLINE, and declining is an answer rather than a failure",
         called_q and not quiet.emitted
         and quiet.holds(kbq.term("intact(jug1)")) == "+")

    # -- the credit walk ---------------------------------------------------
    gate("⭐⭐ credit reaches a tool: its advice was on the support of what was "
         "achieved, and the walk does not know it was not a rule",
         "oracle" in {r.name for r, _ in good.review()})
    gate("⭐⭐⭐ and so does BLAME: a tool whose answer cost a goal is named, "
         "which is what makes one credit walk supervise rules and tools alike",
         "oracle" in {r.name for r, _ in bad.blame()})
    gate("a tool that advised well is not blamed", not good.blame())

    rows = bad.learned()
    gate("⚠ but a tool is not RECOMMENDED -- a `prefer` row is read by recall "
         "and recall proposes rules, so a row naming a tool would be inert",
         not any("<oracle>" in r for r in rows))

    # -- the trap, encoded -------------------------------------------------
    twin, kbt, called_t = episode("fill(kettle)", scoped=False)
    gate("⚠⚠⚠ the twin control: registering a tool by NAME mints its own "
         "request relation, and it waits forever for a request nobody can make",
         not called_t)

    # The count, not only the failures -- see `ugm.learning` for what it cost to
    # learn that `0 failing` and `0 checks, 0 failing` print the same thing.
    print(f"\n{ran} checks, {failing} failing")
    print("""
  ⚠ WHAT IS STILL PYTHON, and it is the honest half. The answerer's BODY is
  native and always will be -- that is the point of a tool. What moved is the
  binding, the record and the licence. The remaining debt is narrower and
  worth stating exactly: `_fit`, `_verdict`, `_settle`, `_dispatch` and
  `_enter` are still bound in Python rather than through `answers`, so the
  apparatus does not yet eat its own cooking. Converting them is mechanical
  and was deliberately not done here -- they answer requests the machinery
  needs answered to run at all, and a corpus that could retire `_fit` could
  retire backward reading, which is a different argument (§19's carve-out).

  ⚠ AND WHAT A MODEL WOULD ADD that this stub does not test: nondeterminism.
  §3 forbids reading a derived result out of an unseeded source, and a
  sampled answer is exactly that -- two runs would diverge with the trail
  recording neither the choice nor the reason. A real answerer needs a seed
  on the record, or it is not reproducible reasoning.""")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
