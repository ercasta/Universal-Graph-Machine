"""How much conflict is in the rules we have -- latent, and actual?

*Knowledge acquisition and rule harmonization are the pain* is Cyc's lesson and
the reason this file exists. It is a **census, not a detector**: it reports what
is there, so that a decision to build harmonization machinery can be made
against a number rather than against a reputation.

Two questions, and they answer differently.

**Latent.** Two rules could contradict each other if their consequents unify
under opposite signs -- `+p(?x)` against `-p(?y)`, standardised apart, since both
rules say `?x` and mean different things. This is the one incompatibility the
floor can already express: `-p` IS the negation of `p`, and what cannot be said
is that two *distinct* propositions are incompatible (`sitting(x)` against
`standing(x)`). That relation -- `refutes` -- did not survive the restart.

**Actual.** `_defeated` returning True: a precedence that was exercised, on a
real run, over rules that really both matched.

    python -m ugm.harmony

## What it said the day it was written

| | |
|---|---|
| machines / rules / rule pairs | 187 / 3,645 / 33,989 |
| latent: consequents unify under opposite signs | 3,551 |
| ...where the unifier is a **bare variable** | **3,545** |
| ...genuinely specific | **6** |
| ...ungoverned by an authored precedence | **1** |
| actual: `_defeated` asked / True | 19,486 / 149 |
| distinct pairs that ever fought | **6**, every one authored on purpose |

⭐⭐⭐ **There is not one unplanned conflict in this repository.** The single
ungoverned pair is `<expand>` (`+goal(?sub)`) against a fixture's `<done>`
(`-goal(nearer(?x))`), written the same day to test that a denied goal leaves
`_in_play` -- and the two never collide on one proposition, so it is latent and
never actual. A static detector shipped against this corpus would report 3,545
false positives, one true positive already harmonized, and one that is a
fixture: unfalsifiable, in the way `loop detection` warned from the other side.

> **A corpus with no pathology cannot measure a detector for it.**

⚠ **The 3,545 are not noise, they are a fact about the bundle.** `<denial>`
concludes `-?p` -- a bare variable -- so it is in latent conflict with every
positive rule in every corpus. No filter on the consequent removes that; the
real discriminator is whether two antecedents can hold at once, which is a join
and still only says *potential*. That is the finding that makes static pair
analysis the wrong shape to start from.

⚠⚠⚠ **And the suite now CONTAINS deliberate conflicts**, added the same day by
`a_defeat_is_on_the_record` -- including an `overrides` cycle that accounts for
120 of the 149 defeats. So the actual-conflict *rate* can no longer be read off
this suite without splitting the fixtures out. That is exactly what loop
detection recorded about deliberate runaways, arriving again and caused by the
checks written for this very census.

⚠⚠ **The first version of this instrument under-counted by 3.5×** -- 53 machines
where there are 187 -- because it remembered which machines it had seen as a set
of `id()`, and CPython reuses an address as soon as a machine is collected. It
reported **0 ungoverned** where the answer is 1. The conclusion survived; the
numbers it was argued from did not.

⚠ So this is not evidence that harmonization does not matter. It is evidence
that **these corpora cannot measure it**: one author, a few days, a few dozen
rules per fixture, where Cyc's pain is volume and many hands. The number to
watch is the last column, and the day it is not zero is the day a detector can
be gated.
"""

import contextlib
import io
import sys

import ugm.rules as R
from .machine import Machine
from .rules import rename, unify_patterns

_tally = {
    "machines": 0, "rules": 0, "pairs": 0,
    "latent": 0, "bare_variable": 0, "specific": 0,
    "specific_bundled": 0, "specific_authored": 0, "ungoverned": 0,
    "defeat_asked": 0, "defeat_true": 0,
}
_fights: dict = {}
_examples: list = []


def _census(m: Machine) -> None:
    g = m.g
    rules = list(m.rules.rules)
    bundled = {r.node for r in m.bundle}
    ordered = {(h.node, l.node) for h, l in
               m.rules.precedence(m.OVERRIDES) + m.rules.precedence(m.SUPERSEDES)}
    _tally["machines"] += 1
    _tally["rules"] += len(rules)
    for i, r1 in enumerate(rules):
        for r2 in rules[i + 1:]:
            _tally["pairs"] += 1
            hit = specific = False
            for m1 in r1.consequent:
                for m2 in r2.consequent:
                    if m1.sign == m2.sign or "?" in (m1.sign, m2.sign):
                        continue
                    # Standardised apart: both rules say `?x`, and they mean
                    # different things. `rename` exists for exactly this.
                    a, b = rename(g, m1.pattern, {}), rename(g, m2.pattern, {})
                    if unify_patterns(g, a, b) is None:
                        continue
                    hit = True
                    if not (g.is_var(m1.pattern) or g.is_var(m2.pattern)):
                        specific = True
            if not hit:
                continue
            _tally["latent"] += 1
            if not specific:
                _tally["bare_variable"] += 1
                continue
            _tally["specific"] += 1
            if r1.node in bundled and r2.node in bundled:
                _tally["specific_bundled"] += 1
                continue
            _tally["specific_authored"] += 1
            if (r1.node, r2.node) in ordered or (r2.node, r1.node) in ordered:
                continue
            _tally["ungoverned"] += 1
            if len(_examples) < 10:
                _examples.append(f"{r1.name or r1.connective} vs "
                                 f"{r2.name or r2.connective}")


def install() -> None:
    run = Machine.run

    def counted_run(self, limit=100):
        # ⚠⚠ A flag on the machine, never a set of `id()`. The first version
        # kept `id(self)` and CPython reuses an address the moment a machine is
        # collected -- so a later fixture's machine was silently taken for one
        # already counted, and the census under-reported by five machines and a
        # hundred rules without anything looking wrong.
        if not getattr(self, "_censused", False):
            self._censused = True
            _census(self)
        return run(self, limit)

    Machine.run = counted_run

    original = R._defeated

    def counted(rs, rule, matched):
        _tally["defeat_asked"] += 1
        out = original(rs, rule, matched)
        if out:
            _tally["defeat_true"] += 1
            for higher in R._defeaters(rs, rule, matched):
                key = (higher.name or "?", rule.name or "?")
                _fights[key] = _fights.get(key, 0) + 1
        return out

    # ⚠ Both bindings. `machine.py` imported the name, so patching only
    # `rules._defeated` leaves the loop calling the original -- and the
    # instrument reports zero and reads as a finding.
    R._defeated = counted
    import ugm.machine as M
    M._defeated = counted


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    install()
    from . import selftest

    with contextlib.redirect_stdout(io.StringIO()) as buf:
        selftest.main()
    suite = buf.getvalue().strip().splitlines()[-1]

    print(__doc__)
    print(f"  the suite, under the census: {suite}")
    print()
    for k in ("machines", "rules", "pairs", "latent", "bare_variable",
              "specific", "specific_bundled", "specific_authored",
              "ungoverned", "defeat_asked", "defeat_true"):
        print(f"  {_tally[k]:8d}  {k}")
    print()
    print(f"  {len(_fights)} distinct pairs actually fought:")
    for (w, l), n in sorted(_fights.items(), key=lambda kv: -kv[1]):
        print(f"         {w} beat {l}, {n} times")
    for e in _examples:
        print(f"         UNGOVERNED: {e}")
    print()
    if _tally["defeat_true"] == 0:
        print("  ⚠ NOTHING was ever defeated: this run measured no conflict at all.")
        return 1
    print(f"  {_tally['ungoverned']} latent conflicts with nothing on the record "
          f"saying who wins")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
