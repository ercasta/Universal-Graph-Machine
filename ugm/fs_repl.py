"""The filesystem REPL demo.

    python -m ugm.fs_repl [corpus.ugm ...]

Wires `repl_fs`'s tools, the three computators the shipped corpus reads,
and an `approve` tool that asks at the terminal, then hands off to
`ugm.repl`. `circuit_breaker.ugm` is shared infrastructure (§ any domain
might watch a rule) and loads first, always; everything under
`ugm/rules/fs/` is THIS domain's own corpus and loads next, whatever is
there -- drop a `.ugm` file in that folder (a rename policy of your own
overriding `<hold-rename>`, a rule that reads `<flag-stale>`'s facts) and
it is picked up on the next run, no path to edit here. Extra corpus paths
on the command line load last, for a one-off addition that is not meant to
live in the folder.
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

    def minus(a, b):
        return max(0, int(a) - int(b))

    ldr.computator("age_days", age_days)
    ldr.computator("at_least", at_least)
    ldr.computator("prefixed", prefixed)
    ldr.computator("plus", plus)
    ldr.computator("minus", minus)


def build(ask=input) -> tuple[Machine, Loader]:
    """A machine with the fs tools, the approval tool, `circuit_breaker.ugm`
    and everything under `ugm/rules/fs/` loaded, ready for `ugm.repl.run`.
    `ask` is the approval prompt -- a function from a message to a line of
    text -- swappable for a test."""
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
    loaded = []
    for corpus_path in _corpora.folder("fs"):
        with open(corpus_path, "r", encoding="utf-8") as fh:
            ldr.load(fh.read())
        loaded.append(corpus_path)
    if loaded:
        print("loaded:", ", ".join(loaded))
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
