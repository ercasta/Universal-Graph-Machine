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

Everything a corpus can do, this REPL asks for the same way a corpus does --
`.ugm` text, one line at a time. There used to be `:ls`/`:cleanup` shortcuts
that built `+want(...)` facts directly in Python, because a real path or
filename (colons, spaces, backslashes) could not survive the tokenizer.
Gone: the tokenizer now reads a quoted string (`core/text.py`'s lexer), so
`fact +want(list("C:\\Users\\ercas\\Documents"))` is ordinary, typeable
`.ugm` text, and `<list>` (`ugm/rules/fs_demo.ugm`) is the tool -- driven by
the engine, not by a REPL command that knew what a directory listing meant.
"""

import sys
from typing import Optional, TextIO

from .core.machine import Machine
from .core.text import Loader, ParseError

HELP = """\
:show      what is believed right now
:load PATH load another .ugm file into this session
:quit      leave
anything else is fed to the loader as ordinary .ugm text -- a fact, a rule,
a `say` -- and the machine runs to quiescence before the next prompt. A path
or filename needing a space or a backslash is a quoted string: "like this".
example:  fact +want(list("C:\\Users\\ercas\\Documents"))
"""


def _visible(m: Machine, p) -> bool:
    return m.g.relation_of(p) not in m._bookkeeping


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
