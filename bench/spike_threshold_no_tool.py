"""THRESHOLD-WITHOUT-A-TOOL PROBE — can the governor's count+threshold be 100% data+rules (no arithmetic)?

Two candidates:
  (B) GRADED degree + gradable comparison — RULED OUT: the possibilistic combination is max-of-min (idempotent
      max), so N flare events deriving "stuck" collapse to ONE degree. Degrees don't ACCUMULATE, so they
      cannot count. (possibility.py: "qualitative max-of-min".)
  (A) COUNT via an N-fold SELF-JOIN with `!=` (the one native comparison) — "reached level-k" = "there exist k
      DISTINCT flare events." No arithmetic, no tool. And a bounded LADDER of named levels makes the ACTIVE
      threshold a SWAPPABLE FACT (`abandon_at ?level`), so the limit is data even though each level's join is
      structural. This is the 100%-data+rules governor.

Accumulator here = the monotone SET of distinct `flared` event facts (the bridge mints one per exhaustion —
no non-monotone attribute-set even needed). The whole count+threshold+recovery is rules+facts.
"""
from __future__ import annotations

import warnings

from ugm import AttrGraph
from ugm.cnl.machine_rules import load_machine_rules
from ugm.cnl.query import ask_goal

warnings.simplefilter("ignore")

# The governor bank — count-to-a-level by distinct-event self-join, then abandon at the DECLARED level.
# `!=` is the only native comparison; N distinct events = an N-fold self-join. Pure data+rules.
GOVERNOR = "\n".join([
    "?g reached mild when ?e1 flared ?g",
    "?g reached moderate when ?e1 flared ?g and ?e2 flared ?g and ?e1 != ?e2",
    "?g reached severe when ?e1 flared ?g and ?e2 flared ?g and ?e3 flared ?g "
    "and ?e1 != ?e2 and ?e1 != ?e3 and ?e2 != ?e3",
    "?g abandoned yes when ?g reached ?level and ?c abandon_at ?level",   # threshold = a SWAPPABLE FACT
])


def _world(n_events, abandon_at):
    kb = AttrGraph()
    def node(x):
        got = kb.nodes_named(x); return got[0] if got else kb.add_node(x)
    g = node("stuck_goal")
    for i in range(n_events):
        kb.add_relation(node(f"e{i}"), "flared", g)          # distinct monotone event facts (the accumulator)
    kb.add_relation(node("cfg"), "abandon_at", node(abandon_at))   # the threshold, as DATA
    return kb, g


def _abandoned(n_events, abandon_at):
    kb, _g = _world(n_events, abandon_at)
    return ask_goal(kb, ("yesno", "stuck_goal", "abandoned", "yes"), load_machine_rules(GOVERNOR)) == ["yes"]


def main():
    cases = [
        # (events, abandon_at, expect_abandoned, note)
        (2, "severe",   False, "2 events < severe(3): keep going"),
        (3, "severe",   True,  "3 distinct events reaches severe: abandon"),
        (2, "moderate", True,  "same events, threshold LOWERED by DATA -> abandon earlier"),
        (1, "moderate", False, "1 event < moderate(2): keep going"),
    ]
    ok = True
    for n, lvl, expect, note in cases:
        got = _abandoned(n, lvl)
        mark = "OK" if got == expect else "XX"
        ok &= (got == expect)
        print(f"  [{mark}] events={n} abandon_at={lvl:8s} -> abandoned={got!s:5s}  ({note})")
    print("=" * 72)
    print(f"THRESHOLD-NO-TOOL: {'GO — count+threshold+recovery are 100% data+rules; NO arithmetic tool'
                               if ok else 'GAP'}")
    print("  (limit is swappable DATA among declared levels; degrees ruled out — max-of-min cannot count)")


if __name__ == "__main__":
    main()
