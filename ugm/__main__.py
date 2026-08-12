"""Run a corpus, or resume a session, and say what became of it.

    python -m ugm <corpus.ugm> [--limit N] [--why TERM] [--save FILE]
    python -m ugm --resume FILE [--limit N] [--why TERM] [--save FILE]

§2's not-lossy criterion at the one boundary nobody had crossed. Everything this
prints was already in the graph: a corpus with a typo ends `quiescent` with
`blocked(water(kettle))` deposited -- the agent has diagnosed itself exactly --
and until now there was no way to be told. Every `__main__` in this package was
an instrument; none of them was a door.

⚠ A resumed session does **not** act again. The boundary is muted for the whole
replay, so what it did lands as `taken` and becomes `did` through the bundle:
the agent remembers acting, and nothing leaves twice.
"""

import json
import sys

from .machine import Machine
from .text import load, load_file


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0

    path, limit, asked, save, resume = None, 400, [], None, None
    i = 0
    if not argv[0].startswith("--"):
        path, i = argv[0], 1
    while i < len(argv):
        flag = argv[i]
        if flag in ("--limit", "--why", "--save", "--resume") and i + 1 >= len(argv):
            print(f"{flag} needs a value")
            return 2
        if flag == "--limit":
            limit = int(argv[i + 1]); i += 2
        elif flag == "--why":
            asked.append(argv[i + 1]); i += 2
        elif flag == "--save":
            save = argv[i + 1]; i += 2
        elif flag == "--resume":
            resume = argv[i + 1]; i += 2
        else:
            print(f"unexpected argument {flag!r}")
            return 2
    if path is None and resume is None:
        print("give a corpus to run, or --resume a saved session")
        return 2

    m = Machine()
    kb = None
    if resume:
        with open(resume, encoding="utf-8") as fh:
            m.replay(json.load(fh)["journal"], limit=limit)
        print(f"{resume}: resumed, {len(m.journal)} recorded steps, without acting again")
    if path:
        kb = load_file(m, path)
        steps = m.run(limit=limit)
        last = steps[-1].state if steps else "nothing to do"
        print(f"{path}: {len(steps)} ticks, ended {last}")
        if last == "applied":
            print(f"  ⚠ stopped at the tick limit ({limit}); it had not finished")
    print()
    for line in m.report():
        print(line)
    if save:
        m.save(save)
        print()
        print(f"saved to {save}")
    for q in asked:
        print()
        print(f"why {q}?")
        scope = kb if kb is not None else load(m, "", None, None)
        lines = m.why(scope.term(q))
        # A proposition nothing concluded has no trail, and saying so is the
        # answer rather than an empty list (§5's whole argument about silence).
        print("\n".join("  " + l for l in lines) if lines
              else "  nothing concluded it -- see what is BLOCKED above")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
