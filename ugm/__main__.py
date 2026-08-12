"""Run a corpus and say what became of it.

    python -m ugm <corpus.ugm> [--limit N] [--why TERM ...]

§2's not-lossy criterion at the one boundary nobody had crossed. Everything this
prints was already in the graph: a corpus with a typo ends `quiescent` with
`blocked(water(kettle))` deposited -- the agent has diagnosed itself exactly --
and until now there was no way to be told. Every `__main__` in this package was
an instrument; none of them was a door.
"""

import sys

from .machine import Machine
from .text import load_file


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    path, limit, asked = argv[0], 400, []
    i = 1
    while i < len(argv):
        if argv[i] == "--limit":
            limit = int(argv[i + 1]); i += 2
        elif argv[i] == "--why":
            asked.append(argv[i + 1]); i += 2
        else:
            print(f"unexpected argument {argv[i]!r}")
            return 2
    m = Machine()
    kb = load_file(m, path)
    steps = m.run(limit=limit)
    last = steps[-1].state if steps else "nothing to do"
    print(f"{path}: {len(steps)} ticks, ended {last}")
    if last == "applied":
        print(f"  ⚠ stopped at the tick limit ({limit}); it had not finished")
    print()
    for line in m.report():
        print(line)
    for q in asked:
        print()
        print(f"why {q}?")
        lines = m.why(kb.term(q))
        # A proposition nothing concluded has no trail, and saying so is the
        # answer rather than an empty list (§5's whole argument about silence).
        print("\n".join("  " + l for l in lines) if lines
              else "  nothing concluded it -- see what is BLOCKED above")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
