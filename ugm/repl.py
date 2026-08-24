"""A REPL: load a corpus, run to quiescence, take a line, repeat.

`ugm/__main__.py` deliberately has none of this -- it runs one corpus once
and exits, because `--save`/`--resume` were never built (see its own
docstring). This is not that. There is still no session file: the state
that would need saving is the one `Machine` this process holds, for as long
as the process runs. What a REPL adds over one run is a human answering a
tool mid-session -- `ugm/repl_fs.py`'s `approve` calls `input()` -- and
typing a NEW rule once the facts it would read already exist, which is the
"compounding" this exists to show (see `docs/tools-approval.md`).

One Loader for the whole session, not one per line: a rule named `<hold>` on
line 1 has to still resolve when line 40 writes `<producing(<hold>, ...)>`
about it, and name resolution lives on the Loader instance, not the scope
string (see `Loader.rule_nodes`).
"""

import sys
from typing import Optional, TextIO

from .core.machine import Machine
from .core.text import Loader, ParseError

HELP = """\
:show              what is believed right now
:ls DIR            +want(list(DIR)) -- list a directory (read-only)
:cleanup DIR DAYS  +want(stale_after(DIR, DAYS)) -- flag and propose renames
:load PATH         load another .ugm file into this session
:quit              leave
anything else is fed to the loader as ordinary .ugm text -- a fact, a rule,
a `say` -- and the machine runs to quiescence before the next prompt.
"""


def _visible(m: Machine, p) -> bool:
    return m.g.relation_of(p) not in m._bookkeeping


def _rel(ldr: Loader, head: str, *members):
    return ldr.m.g.rel(ldr.atom(head), *members)


def _want(ldr: Loader, head: str, *args: str):
    """Believe `+want(head(args...))` directly, bypassing the parser -- a
    path or a filename is not necessarily well-formed `.ugm` text (colons,
    spaces, backslashes), so a REPL command builds the fact the way a tool
    does (`repl_fs.deposit`), not by asking the loader to read it back."""
    m = ldr.m
    inner = _rel(ldr, head, *[ldr.atom(a) for a in args])
    goal = _rel(ldr, "want", inner)
    if not m.pad.holds(goal):
        m.gate.write(goal)


def run(m: Machine, ldr: Loader, limit: int = 400,
        prompt: str = "ugm> ", stdin: Optional[TextIO] = None,
        echo_prompt: bool = True) -> int:
    stdin = stdin or sys.stdin
    print(HELP)
    seen = set(m.pad.believed())

    def settle(label: str = "") -> None:
        nonlocal seen
        steps = m.run(limit=limit)
        now = set(m.pad.believed())
        for p in sorted(now - seen):
            if _visible(m, p):
                print(f"  + {m.g.show(p)}")
        for p in sorted(seen - now):
            if _visible(m, p):
                print(f"  - {m.g.show(p)}")
        seen = now
        ended = steps[-1].state if steps else "nothing to do"
        print(f"  ({len(steps)} ticks{label}, ended {ended})")

    while True:
        if echo_prompt:
            sys.stdout.write(prompt)
            sys.stdout.flush()
        line = stdin.readline()
        if line == "":
            break
        line = line.strip()
        if not line:
            continue
        if line in (":q", ":quit", ":exit"):
            break
        if line == ":show":
            for p in sorted(seen):
                if _visible(m, p):
                    print(f"  {m.g.show(p)}")
            continue
        if line.startswith(":ls "):
            _want(ldr, "list", line[4:].strip())
            settle()
            continue
        if line.startswith(":cleanup "):
            dir_, days = line[9:].rsplit(None, 1)
            _want(ldr, "stale_after", dir_.strip(), days.strip())
            settle()
            continue
        if line.startswith(":load "):
            path = line[6:].strip()
            with open(path, "r", encoding="utf-8") as fh:
                ldr.load(fh.read())
            settle()
            continue
        try:
            ldr.load(line)
        except ParseError as e:
            print(f"  ! {e}")
            continue
        settle()
    return 0
