"""Run a corpus and say what became of it.

    python -m ugm <corpus.ugm> [--limit N] [--ask TERM]

What is gone from this file is the same thing that is gone from the engine.
`--save` and `--resume` wrote and replayed a SESSION -- everything the agent
had been told, in order -- and `--why` walked a belief's support back to what
it rested on. Both were readings of a history, and there is no history: one
graph, one current state, and what it holds is all there is to print. A
scratchpad the agent could reload is a memory system, and it will be built as
one rather than fallen into.
"""

import sys

from .core.machine import Machine
from .core.text import load_file, _report_unwebbed


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0

    path, limit, asked = None, 400, []
    i = 0
    if not argv[0].startswith("--"):
        path, i = argv[0], 1
    while i < len(argv):
        flag = argv[i]
        if flag in ("--limit", "--ask") and i + 1 >= len(argv):
            print(f"{flag} needs a value")
            return 2
        if flag == "--limit":
            limit = int(argv[i + 1]); i += 2
        elif flag == "--ask":
            asked.append(argv[i + 1]); i += 2
        else:
            print(f"unexpected argument {flag!r}")
            return 2
    if path is None:
        print("give a corpus to run")
        return 2

    m = Machine()
    kb = load_file(m, path)
    # The one place an author loads a corpus in order to RUN it, which is the
    # audience for this note. See `text._report_unwebbed`.
    _report_unwebbed(m)
    steps = m.run(limit=limit)
    last = steps[-1].state if steps else "nothing to do"
    print(f"{path}: {len(steps)} ticks, ended {last}")
    if last == "applied":
        # ASCII, deliberately. This is the ONE line a runaway corpus reaches,
        # and a console whose encoding cannot carry the character turns the
        # diagnostic into a traceback -- the report about the failure failing,
        # which is the worst place in the program for it.
        print(f"  stopped at the tick limit ({limit}); it had not finished")

    print()
    print("what it believes, newest first:")
    for p in m.pad.believed():
        if m.g.relation_of(p) in m._bookkeeping:
            continue  # the machinery's own record-keeping is not the world
        print(f"  {m.g.show(p)}")

    for q in asked:
        print()
        term = kb.term(q)
        print(f"{q}: {'believed' if m.holds(term) else 'not believed'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
