"""PROBE — THE ACT/LOOK RELATION. What relates "I changed some files" to "git status will be dirty"?

The user's example, 2026-08-02:

> I change some files, I expect `git status` to not return empty. **In some way, I related the two.**

`probe_anticipation.py` measured that the anticipation itself already works: a mock can read the graph and
predict from world state. What it could not answer is where the *relation* lives. In that probe
`anticipate` reads `changed_file` **because it was authored that way**, and nothing checks that `edit`
actually writes `changed_file`. Rename one and the anticipation still parses, still runs, and silently
models the wrong thing — the verdict `islands.md` says has no name.

**The hypothesis.** The relation is derivable and needs no new representation, because both halves are
already graph data:

  * what an ACT writes — `driver.establishes`, already built, roles-as-paths and all;
  * what a LOOK's model reads — **nothing; this is the missing dual**, prototyped here as `reads`.

  related(act, look)  ==  { (kind,label) written by act }  ∩  { (kind,label) read by look's MOCK }

⚠ **The asymmetry is the point and is not an accident.** You read the ACT's *body* — that is what it does.
You read the LOOK's *mock* — because a look's body is a `DISPATCH` and therefore says nothing at all. The
mock is the only account of what the tool reports on. `establishes` already found this out from the other
side ("`scan_dir`'s own body establishes almost nothing").

⚠⚠ **THE CONTROL IS THE WHOLE PROBE.** If every look relates to every act the measure is vacuous, and this
repo has twice built a probe whose control went dark (`probe_consequent.py`). So three pairs are measured:

  (1) edit + git_status   -> MUST be related
  (2) edit + disk_free    -> MUST NOT be (an unrelated look; the control)
  (3) edit_renamed + git_status -> MUST NOT be (the drift defect the relation exists to catch)

Pair (2) failing would mean the measure says "related" about everything. Pair (3) failing would mean it
cannot catch the thing it is for.

--------------------------------------------------------------------------------------------------------
⭐ MEASURED, AND BUILT. All three pairs behaved:

    (1) edit         + git_status : [('link', 'changed_file')]
    (2) edit         + disk_free  : UNRELATED      <- the control held
    (3) edit_renamed + git_status : UNRELATED      <- the drift defect is caught

So the relation DISCRIMINATES, and it went into the engine as `driver.reads` / `driver.reports_on` /
`driver.confirms` (suite 217 -> 220, 0 FAILED). ⚠ This file now CALLS those rather than keeping the
prototype it was written with: the prototype duplicated `_effects`' register bookkeeping, and two copies of
that is the drift shape the built version exists to prevent — a probe carrying its own copy would be the
same defect one level out.

⚠⚠ ONE THING THE PROTOTYPE GOT WRONG, worth keeping because it is the general trap: its vacuity guard
asserted that *no* read names a bare parameter. That is false — `GET R(s) F(t) "sub"` is itself a read *of
`t`* — and the guard was rejecting a correct answer. The navigation being checked is the read that comes
*after* the `GET`, which is what the built check now asserts.
"""
from __future__ import annotations
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from microfunctions import asm, driver as DR, function as fn, isa, types as TY  # noqa: E402
from microfunctions.graph import new_graph                                      # noqa: E402
from microfunctions.isa import F, R                                             # noqa: E402

declare = TY.declare_type
bar = "=" * 86

reads, model_of, relates = DR.reads, DR.reports_on, DR.confirms


# --- the world ------------------------------------------------------------------------------------------
def repo():
    g = new_graph()
    declare(g, "tree", attrs={"kind_of": "tree"})
    declare(g, "report", base="tree", attrs={"reported": True})
    asm.load_text(g, "\n".join([
        "# THE ACT: change some files.",
        "fn edit(t: tree) -> tree:",
        '    NEW R(f) "file"',
        '    SET R(f) "changed" true',
        '    LINK F(t) "changed_file" R(f)',
        "",
        "# THE SAME ACT, REFACTORED to write a different slot. Nothing else changed.",
        "fn edit_renamed(t: tree) -> tree:",
        '    NEW R(f) "file"',
        '    SET R(f) "changed" true',
        '    LINK F(t) "modified_file" R(f)',
        "",
        "# THE LOOK: ask git. Its body is a DISPATCH and says nothing.",
        "fn git_status(t: tree) -> report:",
        '    DISPATCH R(out) "git_status" F(t)',
        '    SET F(t) "reported" true',
        "",
        "# ITS MODEL: what git status reports ON.",
        "fn anticipate(t: tree) -> report mocks git_status:",
        '    SET F(t) "reported" true',
        '    COUNT R(n) F(t) "changed_file"',
        '    JMPNOT R(n) .clean',
        '    SET F(t) "dirty" true',
        "    JMP .done",
        "    .clean:",
        '    SET F(t) "dirty" false',
        "    .done:",
        "    HALT",
        "",
        "# AN UNRELATED LOOK - THE CONTROL. Also a DISPATCH, also has a model, reads something else.",
        "fn disk_free(t: tree) -> report:",
        '    DISPATCH R(out) "df" F(t)',
        '    SET F(t) "reported" true',
        "",
        "fn guess_disk(t: tree) -> report mocks disk_free:",
        '    SET F(t) "reported" true',
        '    ATTR R(b) F(t) "free_bytes"',
        '    SET F(t) "roomy" true',
    ]))
    t = g.mint("tree", kind_of="tree")
    g.link("root", "has", t)
    return g, t


g, t = repo()

print(bar)
print("  WHAT EACH SIDE SAYS")
print(bar)
eff, _ = DR.establishes(g, "edit")
print(f"  edit WRITES        : {sorted((k, l) for k, l, _s, _o in eff)}")
print(f"  git_status's model READS : {sorted((k, l) for k, l, _s in model_of(g, 'git_status')[0])}")
print(f"  disk_free's model READS  : {sorted((k, l) for k, l, _s in model_of(g, 'disk_free')[0])}")
print(f"  git_status's BODY reads  : {sorted(reads(g, 'git_status')[0])}   <- a DISPATCH says nothing")

print()
print(bar)
print("  THE THREE PAIRS")
print(bar)
p1 = relates(g, "edit", "git_status")
p2 = relates(g, "edit", "disk_free")
p3 = relates(g, "edit_renamed", "git_status")
print(f"  (1) edit          + git_status : {sorted(p1) or 'UNRELATED'}")
print(f"  (2) edit          + disk_free  : {sorted(p2) or 'UNRELATED'}   <- THE CONTROL")
print(f"  (3) edit_renamed  + git_status : {sorted(p3) or 'UNRELATED'}   <- THE DRIFT DEFECT")

print()
print(bar)
print("  VERDICT")
print(bar)
print(f"  (1) the related pair IS related        : {bool(p1)}")
print(f"  (2) the CONTROL is not                 : {not p2}")
print(f"  (3) drift is CAUGHT                    : {not p3}")
print(f"  -> the relation DISCRIMINATES          : {bool(p1) and not p2 and not p3}")
print()
print("  If all three hold, 'I related the two' is DERIVABLE and needs no new representation:")
print("  the act's body and the look's mock already say it, and nothing had asked them.")
