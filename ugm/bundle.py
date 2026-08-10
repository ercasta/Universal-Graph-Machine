"""Is every bundled rule load-bearing? (§20)

    Every gate must delete each rule of the thing it checks, one at a time, and
    report any rule the fixture cannot kill. A rule no fixture can kill is a rule
    the fixture is not testing.

The bundle (§4) is the part of the design that used to be interpreter phases and
is now data. Data can rot in a way a branch cannot: a rule that never applies
costs nothing, breaks nothing, and looks exactly like a rule that works. So this
deletes each bundled rule in turn and re-runs the whole selftest.

It found three the first time it ran. Noticing a deviation had been one Python
comparison -- *the observed sign is not the expected one* -- and writing it as
rules turned its four cases into four nodes, of which only one had ever been
exercised. The phase was not tested either; the rules made that visible.

    python -m ugm.bundle
"""

import contextlib
import io
from typing import List, Tuple

from .machine import Machine


def _failures_without(drop: Tuple[str, ...]) -> int:
    """Run the selftest with named bundled rules deleted, and count failures."""
    from . import selftest

    original = Machine.__init__

    def patched(self) -> None:  # type: ignore[no-untyped-def]
        original(self)
        if drop:
            self.rules.rules = [r for r in self.rules.rules if r.name not in drop]

    Machine.__init__ = patched  # type: ignore[method-assign]
    selftest._results.clear()
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            selftest.main()
    except Exception:
        # A deleted rule may make a check raise rather than return False. That is
        # still evidence the rule was load-bearing.
        return max(1, sum(1 for _, _, ok in selftest._results if not ok))
    finally:
        Machine.__init__ = original  # type: ignore[method-assign]
    return sum(1 for _, _, ok in selftest._results if not ok)


def run() -> int:
    names = [r.name for r in Machine().bundle]

    baseline = _failures_without(())
    print("§20 -- is every bundled rule load-bearing?")
    print(f"  baseline        {baseline} failing")
    if baseline:
        print("  the selftest is not green; fix that before reading anything below")
        return baseline

    blind: List[str] = []
    for name in names:
        n = _failures_without((name,))
        print(f"    {name:28} {n:>3} failing" + ("" if n else "   <-- BLIND"))
        if not n:
            blind.append(name)

    print()
    print(f"{len(names)} bundled rules, {len(names) - len(blind)} exercised")
    return len(blind)


if __name__ == "__main__":
    raise SystemExit(1 if run() else 0)
