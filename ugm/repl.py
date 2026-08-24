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
`+want(list("C:\\Users\\ercas\\Documents"))` is ordinary, typeable `.ugm`
text, and `<list>` (`ugm/rules/fs_demo.ugm`) is the tool -- driven by the
engine, not by a REPL command that knew what a directory listing meant.

## Typing at this prompt is talking on a channel, not authoring

A `fact` is standing knowledge; what a PERSON types is an utterance, and
§13 says an arrival is not a belief until a rule trusts it -- the same
distinction the engine already draws for every other channel. So a bare
line (`+want(list("..."))`) is wrapped as `say user: <line>` before it
reaches the loader, and `TRUST_USER` below is the rule that turns it into
a belief -- unconditional, because the person at the keyboard IS the
authority a REPL exists to ask. It is an ORDINARY rule, loaded like any
other: replace it (or add a condition to it) in your own corpus and the
REPL's trust in `user` is whatever you wrote, not a hidden default.

`/godmode` and `/usermode` switch which one a line IS, for every line until
the other is typed -- an explicit, visible session state (the prompt shows
it), not sniffed per line from what the text happens to start with. In
user mode a line can only ever be a proposition (`say` reads nothing else);
authoring a rule live needs `/godmode` first.
"""

import sys
from typing import Optional, TextIO

from .core.machine import Machine
from .core.text import Loader, ParseError

# `no trusted($p)` is not optional. Without it this rule matches the same
# `says(user, $p)` -- which nothing ever retracts, an utterance stays said
# -- forever, winning arbitration every tick without producing anything
# new and starving every other rule out. Same discipline as
# `fs_demo.ugm`'s `<flag-stale>`: the guard is consumed in the SAME firing
# that acts on it, not a later stage.
TRUST_USER = ('rule <trust-user> = implies( { +says(user, $p), no trusted($p) }, '
              '{ +$p, +trusted($p) } )')

HELP = """\
/show      what is believed right now
/load PATH load another .ugm file into this session
/godmode   author directly -- a line is `.ugm` text (fact, rule, say, ...)
/usermode  back to the default -- a line is what you're SAYING
/quit      leave

Starts in user mode: a line is wrapped as `say user: <line>` and believed
only because <trust-user> (loaded at start) trusts this channel
unconditionally -- an ORDINARY rule, replaceable in your own corpus. A path
or filename needing a space or a backslash is a quoted string: "like this".
example:  +want(list("C:\\Users\\ercas\\Documents"))
"""


def _visible(m: Machine, p) -> bool:
    return m.g.relation_of(p) not in m._bookkeeping


def run(m: Machine, ldr: Loader, limit: int = 400,
        prompt: str = "ugm", stdin: Optional[TextIO] = None,
        echo_prompt: bool = True) -> int:
    stdin = stdin or sys.stdin
    ldr.load(TRUST_USER)
    print(HELP)
    seen = set(m.pad.believed())
    god = False

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
            sys.stdout.write(f"{prompt}{'[god]' if god else ''}> ")
            sys.stdout.flush()
        line = stdin.readline()
        if line == "":
            break
        line = line.strip()
        if not line:
            continue
        if line in ("/q", "/quit", "/exit"):
            break
        if line == "/show":
            for p in sorted(seen):
                if _visible(m, p):
                    print(f"  {m.g.show(p)}")
            continue
        if line == "/godmode":
            god = True
            print("  authoring directly -- /usermode to go back")
            continue
        if line == "/usermode":
            god = False
            print("  back to talking on the `user` channel")
            continue
        if line.startswith("/load "):
            path = line[6:].strip()
            with open(path, "r", encoding="utf-8") as fh:
                ldr.load(fh.read())
            settle()
            continue
        if not god:
            line = f"say user: {line}"
        try:
            ldr.load(line)
        except ParseError as e:
            print(f"  ! {e}")
            continue
        settle()
    return 0
