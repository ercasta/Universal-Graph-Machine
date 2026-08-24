"""The filesystem REPL demo.

    python -m ugm.fs_repl [corpus.ugm ...]

Wires `repl_fs`'s tools, the three computators `fs_demo.ugm` reads, and an
`approve` tool that asks at the terminal, then hands off to `ugm.repl`.
Extra corpus paths load after `ugm/rules/fs_demo.ugm`, so a rename policy of
your own can override `<hold-rename>` without editing the shipped one.
"""

import sys
import time

from .core.machine import Machine
from .core.text import Loader, load
from . import corpora as _corpora
from . import repl, repl_fs


def _computators(ldr: Loader) -> None:
    def age_days(now, created):
        return (int(now) - int(created)) // 86400

    def at_least(age, days):
        return "yes" if int(age) >= int(days) else None

    def prefixed(name):
        return f"stale-{name}"

    def plus(a, b):
        return int(a) + int(b)

    ldr.computator("age_days", age_days)
    ldr.computator("at_least", at_least)
    ldr.computator("prefixed", prefixed)
    ldr.computator("plus", plus)


def build(ask=input) -> tuple[Machine, Loader]:
    """A machine with the fs tools, the approval tool and `fs_demo.ugm`
    loaded, ready for `ugm.repl.run`. `ask` is the approval prompt -- a
    function from a message to a line of text -- swappable for a test."""
    m = Machine()
    ldr = load(m, "", scope="fs")
    repl_fs.register(ldr)
    _computators(ldr)

    def approve(mach, prop):
        said = ask(f"approve {mach.g.show(prop)}? [y/N] ").strip().lower()
        return ldr.atom("yes" if said in ("y", "yes") else "no")

    ldr.answerer("approve", "pending", approve)

    node = m.g.rel(ldr.atom("now"), ldr.atom(str(int(time.time()))))
    if not m.pad.holds(node):
        m.gate.write(node)

    with open(_corpora.path("circuit_breaker.ugm"), "r", encoding="utf-8") as fh:
        ldr.load(fh.read())
    with open(_corpora.path("fs_demo.ugm"), "r", encoding="utf-8") as fh:
        ldr.load(fh.read())
    return m, ldr


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    m, ldr = build()
    for path in argv:
        with open(path, "r", encoding="utf-8") as fh:
            ldr.load(fh.read())
    return repl.run(m, ldr)


if __name__ == "__main__":
    raise SystemExit(main())
