"""Which reserved names is anything actually reading? (§20)

    python -m ugm.gates.necessity [name ...]

`ugm.vocabulary` says what the engine's names are **for**. This says which of
them are **doing anything** -- and the two questions are not the same, which is
the whole reason this file exists.

## The instrument

A **kill-probe** is this repository's standing discipline: break the thing on
purpose and confirm that some check notices. It tests the *test*, not the code.
`ugm.bundle` states it for rules:

> Every gate must delete each rule of the thing it checks, one at a time, and
> report any rule the fixture cannot kill. **A rule no fixture can kill is a rule
> the fixture is not testing.**

The same sentence is true of a *name*. So: for each reserved name, suppress every
entry the machinery deposits about it, run the whole suite, and see whether
anything fails. A name the suite cannot kill is one of two things, and the report
does not pretend to tell them apart:

* **dead** -- nothing reads it, and it can go; or
* **untested** -- something reads it and no check does.

Both are findings. `Moment.licence` was written and never read for the whole life
of this branch (`docs/observations.md` §1.2), and `_tolerance` outlived the
generalisation that replaced it, so the prior that every name is load-bearing is
not good.

## How suppression works, and why this shape

⚠ Not by deleting the atom -- a name is minted in `Machine.__init__` and half the
engine holds a reference to it, so deletion is a crash rather than an experiment.
Instead every deposit **about** that relation is re-pointed at a dead one:

    quiet(<m>)   -->   suppressed(quiet(<m>))

The entry still exists, so no caller gets a `None` it did not expect, and the
chain's own bookkeeping is untouched. What changes is the only thing that should:
`quiet(?m)` in a rule now matches nothing, and `relation_of(e.proposition) is
self.QUIET` in Python is now false. **The occasion stops being sayable**, which
is exactly the thing under test.

⭐ One choke point makes this honest: every write in the design goes through
`Chain.deposit` (§13's gate is the only stamper), so a single patch reaches every
route -- rules, tools, the bundle, and the machinery's own `_note`.

⚠ A suppression that makes the suite **crash** counts as killed, not as an error
of this instrument. A crash is the suite noticing in the loudest available way,
and scoring it otherwise would flatter every name whose absence breaks Python
before it breaks a check.

## Reading the report

`killed n` is how many checks the suppression broke. The interesting column is
the one at the bottom: names where **n = 0**.
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

    # ⚠⚠⚠ **Which names this probe can even reach, measured rather than assumed.**
    # Suppression rewrites the relation of a deposited PROPOSITION, so a name
    # that is never one -- a connective (`causes`), a sign (`plus`), an argument
    # atom (`ticks`), or a structural relation, which is minted beside an entry
    # and never deposited as one -- is untouched by the patch and would score 0
    # for a reason that has nothing to do with whether anything reads it.
    # Reporting those as *unkillable* would be this instrument's own version of
    # the label census that read 0.0% and looked like a finding.
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
