"""Which reserved names is anything actually reading? (§20)

    python -m ugm.gates.necessity [name ...]

[name ...] ugm.vocabulary says what the engine's names are for. This says which
of them are doing anything -- and the two questions are not the same, which is
the whole reason this file exists. ⚠ A suppression that makes the suite crash
counts as killed, not as an error of this instrument.

See docs/design/necessity.md.
"""

import contextlib
import io
import sys
from typing import Dict, List, Tuple

from ..core.chain import Chain
from ..core.machine import Machine

# Not vocabulary at all -- `ugm.vocabulary` says so, and suppressing a numeral
# would test the parser rather than a name.
SKIP = set("0123456789")


def _run_suite() -> Tuple[int, int]:
    """The whole suite, in-process. Returns (checks, failing).

    In-process rather than by subprocess because this runs ~90 times and an
    interpreter start each way would be most of the wall clock. The cost is that
    `selftest`'s accumulator is module state, so it has to be cleared by hand --
    stated here rather than discovered later.
    """
    from .. import selftest as ST

    ST._results.clear()
    buf = io.StringIO()
    try:
        # ⚠ stderr too: the loader writes authoring notes there (`name reserved
        # nodes...`), and a hundred runs of them buries the report this exists
        # to print.
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            ST.main()
    except BaseException:
        # ⚠ A crash IS the suite noticing. Scored as killed rather than skipped,
        # for the reason in the module docstring.
        done = len(ST._results)
        return done, max(1, sum(1 for _, _, ok in ST._results if not ok))
    return len(ST._results), sum(1 for _, _, ok in ST._results if not ok)


def probe(names: List[str]) -> List[Tuple[str, int, int]]:
    """Suppress each name in turn and report how many checks it took with it."""
    original = Chain.deposit
    out: List[Tuple[str, int, int]] = []

    for name in names:
        def patched(self, seat, locus, proposition, sign, *a, _n=name, **kw):
            # ⚠⚠⚠ Guarded, and the null control is what forced it. A fixture
            # deposits a node built in a DIFFERENT machine's graph, so
            # `relation_of` raises `KeyError` -- and the crash handler below
            # then scored the probe's own failure as `killed 1`. Every name
            # looked load-bearing by exactly one check, including a name that
            # does not exist. A proposition this graph cannot describe is one it
            # cannot suppress, so it passes straight through.
            try:
                rel = self.g.relation_of(proposition)
            except KeyError:
                rel = None
            if rel is not None and self.g.show(rel) == _n:
                dead = self.g.atom("suppressed")
                proposition = self.g.rel(dead, proposition)
            return original(self, seat, locus, proposition, sign, *a, **kw)

        Chain.deposit = patched
        try:
            total, failed = _run_suite()
        finally:
            Chain.deposit = original
        out.append((name, failed, total))
        print(f"  {name:16} killed {failed:4}", flush=True)
    return out


def main() -> int:
    wanted = [a for a in sys.argv[1:] if not a.startswith("-")]
    m = Machine()
    names = wanted or sorted(n for n in m.reserved if n not in SKIP)

    print(f"Suppressing each reserved name in turn, over the whole suite.")
    print(f"{len(names)} names.\n")

    # ⚠⚠⚠ Which names this probe can even reach, measured rather than assumed.
    # → docs/design/necessity.md#which-names-this-probe-can-even-reach-mea
    seen: set = set()
    real = Chain.deposit

    def watch(self, seat, locus, proposition, sign, *a, **kw):
        try:
            rel = self.g.relation_of(proposition)
        except KeyError:
            rel = None
        if rel is not None:
            seen.add(self.g.show(rel))
        return real(self, seat, locus, proposition, sign, *a, **kw)

    Chain.deposit = watch
    try:
        base_total, base_failed = _run_suite()
    finally:
        Chain.deposit = real
    print(f"  baseline         {base_total} checks, {base_failed} failing")
    if base_failed:
        print("  ⚠ the suite is not green; every number below is against a moving target")

    reachable = [n for n in names if n in seen]
    unreachable = [n for n in names if n not in seen]
    print(f"  reachable        {len(reachable)} of {len(names)} names are ever "
          f"deposited as a proposition's relation")
    print(f"  out of scope     {len(unreachable)}  {unreachable}\n")

    rows = probe(reachable)
    dead = [r for r in rows if r[1] == 0]

    print()
    print("Names no check can kill -- dead, or untested; this cannot tell which")
    print()
    if not dead:
        print("  none: every reachable reserved name is load-bearing for a check")
    for name, _, _ in dead:
        print(f"  {name}")
    print()
    print(f"  {len(dead)} of {len(reachable)} reachable names unkillable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
