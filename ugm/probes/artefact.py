"""Building something, noticing which half of the goal it already meets, and

repairing the other half -- then rendering it. ⚠ And the honest half, which
this file exists to pin: WITHOUT A RE-ASK THE SIGNAL IS STALE.

See docs/design/artefact.md.
"""

from typing import List

from ..core.machine import Machine
from ..core.text import Loader

WORLD = [
    # What each piece of the command does. Claims about a node, not text.
    "rule <lists> = implies( { +uses(?c, ls_py) },    { +finds(?c, py_files) } )",
    "rule <greps> = implies( { +uses(?c, grep_cls) }, { +finds(?c, class_defs) } )",
    # What was asked for -- a conjunction, so it splits into two subgoals.
    "rule <good> = implies(",
    "    { +finds(?c, py_files), +finds(?c, class_defs) },",
    "    { +good(?c) } )",
    # The repair, keyed on the machinery's own answer to *is this half already
    # satisfied*.
    "rule <repair> = implies(",
    "    { +unmet(?p, finds(?c, class_defs)) },",
    "    { +uses(?c, grep_cls) } )",
    # Render it -- but only once the claims say it is right. The request is a
    # rule's to make; what answers it is outside the agent.
    "rule <ask-spell> = implies( { +good(?c) }, { +spell(?c) } )",
    # One line, so that dropping it for the control drops the whole rule -- a
    # `drop` that cuts a rule in half is a ParseError, not a control.
    "rule <believe> = implies( { +answered(<render>, spell(?c), ?s) }, { +spelled(?c, ?s) } )",
    "fact +uses(cmd, ls_py)",
    "fact +goal(good(cmd))",
    "",
]

# One corpus line, and it is the difference between an agent that knows which
# half it has and one that only looks as though it does.
RECHECK = (
    "rule <recheck> = implies( { +unmet(?p, ?sub), +?sub },"
    " { +again(check(?p, ?sub), ?sub) } )"
)


def episode(extra: List[str] = (), drop: str = "", tool: bool = True):
    m = Machine()
    kb = Loader(m)
    asked: List[str] = []

    def render(mach, frame, e):
        """Compose the command from what is claimed about it.

        ⚠ Everything it touches goes through `kb`, never `g.atom`. A tool that
        mints its own nodes answers a request nobody made, with a term no rule
        can name -- measured twice in `ugm.tools`, silent both times.
        """
        command = mach.g.member(e.proposition, 0)
        asked.append(mach.g.show(command))
        parts = []
        if mach.holds(kb.term(f"finds({mach.g.show(command)}, py_files)")) == "+":
            parts.append("ls *.py")
        if mach.holds(kb.term(f"finds({mach.g.show(command)}, class_defs)")) == "+":
            parts.append("xargs grep -l '^class '")
        if not parts:
            return None  # nothing claimed: declining is an answer
        return kb.atom(" | ".join(parts))

    if tool:
        kb.answerer("render", "spell", render)
    body = [ln for ln in list(extra) + WORLD if drop not in ln or not drop]
    kb.load("\n".join(body))
    m.run(limit=600)
    return m, kb, asked


def _unspellable(kb, name: str) -> bool:
    """Is this node's name outside the surface's term syntax? Asked by trying,
    because a list of forbidden characters would be a second parser."""
    from ..core.text import ParseError

    try:
        kb.term(name)
    except ParseError:
        return True
    return False


def _props(m, rel):
    return sorted({m.g.show(e.proposition) for mm in m.chain.moments
                   for e in mm.delta
                   if m.g.relation_of(e.proposition) is rel and e.sign == "+"})


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

    print(__doc__)

    stale, kb_s, _ = episode()
    fixed, kb_f, asked = episode(extra=[RECHECK])
    already, kb_a, _ = episode(extra=[RECHECK, "fact +uses(cmd, grep_cls)"])

    print("  what the agent ended up with\n")
    for label, m, kb in (("first attempt = ls only", fixed, kb_f),
                         ("already complete", already, kb_a)):
        spelled = [m.g.show(m.g.member(n, 1)) for n in m.g.instances_of(
            m.g.relation_of(kb.term("spelled(cmd, x)")))
            if m.holds(n) == "+"]
        print(f"  {label:<26} good={m.holds(kb.term('good(cmd)'))}  "
              f"spelled={spelled[0] if spelled else '-'}")
    print()

    # -- the decomposition, and the repair --------------------------------
    gate("the conjunctive goal split into two subgoals, checked separately",
         any("finds(cmd, py_files)" in u for u in _props(fixed, fixed.UNMET))
         and any("finds(cmd, class_defs)" in u for u in _props(fixed, fixed.UNMET)))
    exercised = lambda m: {m.g.show(m.g.member(e.proposition, 0))
                           for mm in m.chain.moments for e in mm.delta
                           if m.g.relation_of(e.proposition) is m.EXERCISED}
    gate("⭐ the repair fired for the half that was missing",
         any("repair" in x for x in exercised(fixed)))
    gate("...and NOT when the command already did both -- it is keyed on the "
         "partial result, not on the goal",
         not any("repair" in x for x in exercised(already)))
    gate("and the goal was reached", fixed.holds(kb_f.term("good(cmd)")) == "+")

    # -- the finding: the signal is stale without a re-ask -----------------
    def satisfied(m):
        return {a for a in _props(m, m.ACHIEVED) if "finds" in a}

    gate("⚠⚠⚠ WITHOUT a re-ask the agent cannot say which half it has: nothing "
         "is ever recorded as an achieved half, though one held from the start",
         not satisfied(stale))
    gate("⭐ ...and ONE corpus line gives it back, using `again` and no machinery",
         satisfied(fixed) == {"achieved(finds(cmd, class_defs))",
                              "achieved(finds(cmd, py_files))"})

    # -- the boundary: rendering is a tool ---------------------------------
    gate("the artefact is rendered by a TOOL, asked for only once the claims "
         "say the command is right",
         asked == ["cmd"])
    # ⚠⚠ Asked STRUCTURALLY, and finding out why is worth more than the check.
    # → docs/design/artefact.md#asked-structurally-and-finding-out-why-is-wo
    def answers_of(m, kb):
        rel = m.g.relation_of(kb.term("answered(<render>, spell(cmd), x)"))
        return [m.g.show(m.g.member(n, 2)) for n in m.g.instances_of(rel)
                if m.holds(n) == "+" and len(m.g.members(n)) == 3]

    gate("⭐⭐ and what it produced is a RECORD, not a belief -- the string is "
         "`answered(...)` and a corpus rule is what turns it into a claim",
         answers_of(fixed, kb_f) == ["ls *.py | xargs grep -l '^class '"])
    nobelief, kb_n, _ = episode(extra=[RECHECK], drop="<believe>")
    gate("⭐⭐⭐ delete the trust rule and the text is still on the record, "
         "believed by nobody: a tool proposes at the artefact boundary too",
         answers_of(nobelief, kb_n) == ["ls *.py | xargs grep -l '^class '"]
         and not [n for n in nobelief.g.instances_of(
             nobelief.g.relation_of(kb_n.term("spelled(cmd, x)")))
             if nobelief.holds(n) == "+"])
    gate("⚠⚠ and a corpus CANNOT name that string: the surface has no syntax "
         "for it, so a rule reaches a rendered artefact by binding or not at all",
         _unspellable(kb_f, "ls *.py | xargs grep -l '^class '"))
    retired, kb_r, asked_r = episode(extra=[RECHECK, "fact -answers(<render>, spell)"])
    gate("and a corpus can retire the renderer, which is the whole point of the "
         "binding being a fact",
         not asked_r and retired.holds(kb_r.term("good(cmd)")) == "+")

    print(f"\n{ran} checks, {failing} failing")
    print("""
  ⚠ WHAT THIS DOES NOT SHOW, stated so the demonstration is not read for more
  than it is.

  **Parsing is absent.** This is the generation direction only, and generation
  is a function. Going the other way -- shell text, or prose, into claims -- is
  the intake seam, measured at 0/50 on raw prose and 26% on a book corpus in
  the previous arc, and the retired `ugm.workload` recorded it as a seam with no algorithm
  at all. That is where a model belongs, and it is a different project.

  **The repair ADDS; it cannot REPLACE.** `cmd` is one node accumulating
  properties, so `uses(cmd, grep_cls)` composes with what was already claimed.
  A repair that had to withdraw `ls_py` would need a binding reconsidered, and
  nothing in this design reconsiders one.""")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
