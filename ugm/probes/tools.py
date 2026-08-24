"""Tool activation gated by approval -- the worked example for
`docs/tools-approval.md`, run both ways.

    python -m ugm.probes.tools

`ugm/rules/tools_approval.ugm` declares the palette, the request, the
write-time hold and both resolutions. All this module supplies is the
`approve` tool: a Python function bound to the `pending` relation. Here it
answers a canned decision so the probe is deterministic; point the same seam
at `input()` and a corpus author is answering it themselves, at a terminal,
mid-run -- no session, no resume, nothing new to build.
"""

from typing import List

from .. import corpora as _corpora
from ..core.machine import Machine
from ..core.text import load, load_file

CORPUS = _corpora.path("tools_approval.ugm")


def run(decision: str, limit: int = 20):
    """Load the corpus with one `approve` tool that always answers
    `decision` ("yes" or "no"), and run it to quiescence."""
    m = Machine()
    pre = load(m, "", scope="ops")
    asked: List[str] = []

    def approve(mach, prop):
        asked.append(mach.g.show(prop))
        return pre.atom(decision)

    pre.answerer("approve", "pending", approve)

    kb = load_file(m, CORPUS, scope="ops")
    steps = m.run(limit=limit)
    return m, kb, asked, steps


def main() -> int:
    failed = 0

    m, kb, asked, steps = run("yes")
    ok = (steps[-1].state == "quiescent" and asked == ["pending(deploy(web))"]
          and m.holds(kb.term("deploy(web)")))
    print(f"approved: {'ok' if ok else 'FAIL'}  "
          f"({len(steps)} ticks, ended {steps[-1].state}, asked {asked})")
    failed += not ok

    m2, kb2, asked2, steps2 = run("no")
    ok2 = (steps2[-1].state == "quiescent" and asked2 == ["pending(deploy(web))"]
           and not m2.holds(kb2.term("deploy(web)"))
           and not m2.holds(kb2.term("pending(deploy(web))")))
    print(f"denied:   {'ok' if ok2 else 'FAIL'}  "
          f"({len(steps2)} ticks, ended {steps2[-1].state}, asked {asked2})")
    failed += not ok2

    print(f"\n{failed} failing")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
