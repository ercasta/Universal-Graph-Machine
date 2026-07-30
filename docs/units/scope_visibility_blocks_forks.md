# Root-cause finding + FIX: the `_pencil`→`_relativize` migration silently broke fork readability

**Written 2026-07-30, mid-investigation of the `OVERLAY_BAND` composition question
(`attic/handoff_overlay_band_composition.md`). FIXED the same day — two production fixes applied and
verified; a third, related instance found and deliberately left as documented follow-up (§6).**

**Result: the documented pre-existing failure bucket in `test_possibility_rules.py` / `test_possibility_
guess.py` / `test_possibility_band.py` / `test_possibility_cnl.py` went from 31 failed / 12 passed to
2 failed / 41 passed. The two remaining failures are distinct, deeper issues (§6), not this bug.**

## 1. The bug, reproduced on a clean checkout

```python
from ugm.attrgraph import AttrGraph
from ugm.possibility import possibility, all_fork_bands
from ugm.cnl.uncertainty import load_uncertain

g = AttrGraph()
load_uncertain(g, "x is likely male")
possibility(g, "is", "x", "male")     # -> 0.0
all_fork_bands(g)                     # -> {'n3': 0.6, 'n6': 0.6, 'n9': 0.6}  (the fork IS there)
```

`possibility()` — the documented, direct API for reading a fork's band, no rules or policy involved — returns
`0.0` for a fork that unambiguously exists. This reproduces on `git stash` back to the branch tip, before any
change made in this session's `OVERLAY_BAND` investigation. It is the mechanical reason
`test_possibility_rules.py::test_body_through_fork_bands_the_conclusion` and 17+ siblings are in the
session's documented pre-existing-failure baseline (`attic/handoff_overlay_band_composition.md` §4's framing
note) — this finding gives that failure bucket a root cause, not just a "known broken" label.

## 2. Root cause

Two mechanisms, built at different times, now collide on the same graph structure:

- **The possibilistic overlay** (`chain.OVERLAY_BAND`/`_band_overlay`, pre-dates the scope-tree
  generalization): designed so a fork's pencil relation is admitted into a match regardless of reading
  vantage — that is the entire point of "banded" reading (forks are silent-until-assumed under the default
  policy, but visible-at-their-band under `banded`).
- **The scope-tree isolation filter** (`scope_tree.is_visible`/`chain._scope_visible`, the Slice 1c
  generalization, `docs/units/handoff_ugm_reversion_evaluation.md`-era work): `is_visible(node, active=None)`
  returns **False** for *any* scoped node when reading from base vantage — "a base read cannot see a scoped
  node," `scope_tree.py:176`. Correct and necessary for SUPPOSE-style hypothetical isolation.

Since the `_pencil` → `_relativize` migration (this session, `arc_recap.md`'s "documentation bug surfaced"
entry), forks are **also** stored as `<under>`-scoped structural copies (`possibility.fork_fact` →
`suppose._relativize` → `scope_tree.put_under`) — the same mechanism SUPPOSE and scope-tree scopes use. That
migration was the right call (it's what makes `Pat.rel`'s relativizer already reach forks generically, see
§3 of the `OVERLAY_BAND` handoff resolution) — but nobody updated `is_visible` to carve out an exception for
it, so **the moment any fork exists, `scope_tree.reframe_active(g)` flips true, and `is_visible` starts
rejecting the fork's own scoped entity references from base vantage — including from the possibilistic
overlay read that is supposed to admit them.**

Concretely: `_facts_matching`'s subject/object candidate expansion (`chain._candidate_nodes` →
`chain._scope_visible` → `scope_tree.is_visible`) filters OUT a fork's scoped reference node (e.g. `x`'s
private copy under the fork scope) before the walk even reaches the relation — so `OVERLAY_BAND`'s
admit-logic on the *relation* never gets a chance to run; the *endpoint* is already gone.

Verified directly:
```python
from ugm.scope_tree import reframe_active, is_visible, scope_of
reframe_active(g)                              # True — the fork's own <under> edge trips it
scope_of(g, x_scoped_copy)                      # the fork scope (not None)
is_visible(g, x_scoped_copy, active=None)       # False — filtered from a base-vantage read
```

## 3. Why this also broke my `_grades_pass` fix attempt

The demand chain's banded-emit idempotence check (`chain.py` ~line 1601, "has a strictly-better fork already
been derived for this head fact?") calls `_facts_matching(fact_g, hp, ById(s_id), ById(o_id), ...,
bands=True)` with **base** ids. That query goes through the exact same broken candidate path, so it *always*
returns "no existing fork" — even immediately after minting one — and the check-before-derive guard
(`have >= band: continue`) never fires. Attempting the `_grades_pass` score-threading fix (a real, independent,
small correctness fix — see `attic/handoff_overlay_band_composition.md` §6) exposed this pre-existing breakage
as an infinite accretion loop: every round re-derives a brand-new fork scope, forever, because "does one already
exist" can never see the previous one. This is not a new bug the `_grades_pass` fix introduced; it inherited an
existing one.

## 4. Two fixes actually applied (not the one first sketched)

The fix actually landed in two places, not one, and NOT in `scope_tree.is_visible` itself — mid-fix, testing
found that making `is_visible` unconditionally treat forks as reachable broke
`test_silent_default_keeps_forks_invisible`: under the SILENT/default policy, a fork must stay
invisible-until-assumed, and `is_visible` has no notion of "which policy is reading right now" to
distinguish that from a banded read. The fix instead lives one layer up, gated on whether a banded read is
actually in progress:

**Fix 1 — `chain._scope_visible` (chain.py), gated on the existing `_BAND_OVERLAY` register:**
```python
def _scope_visible(fact_g, nodes):
    ...
    active = fact_g.registers.get(_ACTIVE_SCOPE)
    if fact_g.registers.get(_BAND_OVERLAY) is not None:      # a banded read: forks are reachable too
        from .possibility import LIKELINESS
        def visible(n):
            if is_visible(fact_g, n, active):
                return True
            sc = scope_of(fact_g, n)
            return sc is not None and fact_g.get_attr(sc, LIKELINESS) is not None
        return [n for n in nodes if visible(n)]
    return [n for n in nodes if is_visible(fact_g, n, active)]
```
`_BAND_OVERLAY` is only parked in the registers by `_facts_matching(bands=True)` — never by a plain crisp
read — so this keeps `scope_tree.is_visible` itself untouched (its SUPPOSE-isolation semantics are correct
and unrelated) and confines the carve-out to the one stance that needs it.

**Fix 2 — `machine.py`'s `OVERLAY_BAND` opcode, check the band map before the key test:** even with fork
entities reachable, the relation itself was still silently treated as ink. `OVERLAY_BAND`'s test was "if the
node LACKS `CONTROL_MARK`, admit as CERTAIN ink; else check the band map" — but `_relativize` stopped setting
`CONTROL_MARK` on pencil relations (isolation moved entirely to structural `<under>` scoping), so EVERY fork
relation now takes the "lacks key → CERTAIN" branch unconditionally, and the band map is never even
consulted. Fixed by checking the map first:
```python
elif isinstance(ins, OVERLAY_BAND):
    nid = st.regs[ins.reg]
    bands = g.registers.get(ins.live)
    if bands is not None and nid in bands:
        yield st.scaled(bands[nid], self.tnorm)     # a fork pencil -> scale by its band
    elif not g.has_key(nid, ins.key):                # base: an ink (fact) rel -> CERTAIN
        yield st
```
The band map (`chain._band_overlay`/`possibility.all_fork_bands`) only ever contains genuine fork-scoped
nodes, so checking it first is safe for plain ink (never in the map) and correct for a fork pencil
regardless of whether it still carries `CONTROL_MARK`.

Both fixes are safe for SUPPOSE: SUPPOSE's isolation was never actually enforced by `OVERLAY`/`OVERLAY_BAND`
admitting-on-the-relation in the first place (its own reads never reach that far from base vantage, and
from in-scope vantage "admit as certain" is exactly the wanted behaviour) — it was, and remains, enforced by
`is_visible`'s ancestor-chain check on the CANDIDATE entities, untouched by either fix.

## 5. Verified

1. `possibility(g, "is", "x", "male")` on the §1 reproduction: `0.6`, not `0.0`. `verdict()` reports
   `"likely"`.
2. `test_silent_default_keeps_forks_invisible` (the guard against over-fixing): still passes — a fork stays
   invisible under the default/silent policy.
3. `tests/test_possibility_rules.py` + `test_possibility_guess.py` + `test_possibility_band.py` +
   `test_possibility_cnl.py`: **31 failed / 12 passed → 2 failed / 41 passed.** One of the two remaining
   failures was a stale test helper (`test_possibility_cnl.py::_scope_of`, fixed — see §6); the other two
   genuine remaining failures are distinct, deeper issues, not this bug (§6).
4. `_grades_pass`'s score-threading fix (`attic/handoff_overlay_band_composition.md` §6) — previously
   causing infinite fork-accretion because its idempotence check could never re-find a just-derived fork —
   now correctly derives ONE fork and stops: an ordinary declared rule (`Pat("?p", "is", "male",
   rel="?fork")` + `GradedCondition` reading `<likeliness>`) now reproduces `OVERLAY_BAND`'s automatic
   banding exactly, confirming the original `OVERLAY_BAND` retirement question's answer stands.

## 6. Two further findings from the same migration, left as follow-up

**A stale test helper, fixed in place.** `tests/test_possibility_cnl.py::_scope_of` checked
`g.is_control(r)` and read the old single-valued `apply.SCOPE` attribute — both retired by the structural
migration, so it always returned `None`. Fixed to read `scope_tree.scope_of(g, r)` directly; the two tests
that used it (`test_either_or_makes_two_correlated_forks`, `test_ranked_either_or`) now pass.

**A third instance of the same regression family, NOT fixed — `machine.SWEEP`.**
`test_possibility_guess.py::test_retract_sweeps_the_world_but_keeps_the_record` still fails:
`retract_guess`'s cleanup calls `SWEEP` on a guess's adopted pencil relations, and `SWEEP` refuses with
`"SWEEP refused: n43 is not a control node"` — the exact same pattern as fixes 1 and 2 (a mechanism keyed on
`is_control`/`CONTROL_MARK`, which pencil relations no longer carry). Deliberately NOT patched in this
session: `SWEEP`'s control-only guard is a **safety check** ("facts are RETIRE's privilege; inert
provenance is explanation and never swept"), not an incidental filter like `OVERLAY_BAND`'s — loosening it
needs its own careful look at what SWEEP is actually supposed to be allowed to delete post-migration, not a
quick copy of fixes 1/2's pattern.

**A separate, deeper multi-hop limitation, also NOT fixed** —
`test_possibility_band.py::test_overlay_band_min_accumulates_multi_hop`: two forks built by
`possibility.add_fork` that both reference "male" by name each mint their OWN private scoped copy of it
(`scoped_ref` is per-scope), so a derivation chaining fork1's `male` (its OBJECT) into fork2's `male` (its
SUBJECT) has no topological edge to cross — they are different nodes that happen to share a name. This is
a real gap in multi-hop composition through two INDEPENDENT forks referencing the same entity, not a
regression from this session's fixes (this test's own hand-rolled ISA program never contained
`_candidate_nodes`-style name-based cross-referencing, so it never worked past a single-fork hop). Left as
a distinct, separate finding — plausibly connected to the `OVERLAY_BAND` retirement question's own §4 concern
about N-hop chains, but not resolved here.

## 7. Full-suite regression check — done, clean

Ran the complete, unmodified `pytest tests/` (natural collection order) on a clean baseline checkout and
again with both fixes applied, and diffed the exact `FAILED` test names (not just counts, since counts alone
can hide a new failure and a fixed one cancelling out):

- Baseline: **79 failed / 1133 passed.**
- With both fixes: **31 failed / 1181 passed.**
- Exact-name diff: **zero new failures** — every one of the 31 remaining failures was already in the 79.
  **48 tests fixed, none broken.**

(One false alarm along the way: running a hand-picked SUBSET of test files together — not the real, full
`pytest tests/` — reproduced a pre-existing pytest test-ordering hang on BOTH baseline and fixed code,
in a file-adjacency the real full suite's natural collection order doesn't produce. Confirmed by running
that same subset against a clean baseline checkout: identical hang, unrelated to anything in this document.
Lesson: a manually-assembled file subset is not a substitute for the real, complete suite when judging
regressions — the full run is both the correct baseline AND the correct comparison, never a spot-check.)
