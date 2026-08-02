"""PROBE — ANTICIPATION: is an expectation an ASSUMPTION about a call, or a MODEL of a tool?

The user's example, 2026-08-02:

> I change some files, I expect `git status` to not return empty. In some way, I **related the two**. I
> think it's because I can **anticipate the behaviour of `git status`** when I know some files have changed.

⚠⚠ This names a source that `probe_where_expectations_come_from.py`'s ladder does not have. Every mock in
this repo's fixtures asserts a CONSTANT — `found_two` always predicts two files, `list_empty` always
predicts none. Those are **assumptions**: *suppose it turns out this way*. The user's expectation is not an
assumption. It is an **inference from world state he already knows**, through a model of what the tool
reports. He did not *suppose* git status is non-empty; he *worked it out* from having changed the files.

The question, and it is decisive for whether anything needs building:

  **Can a mock READ THE GRAPH and compute its prediction from world state, rather than assert a constant?**

If it can, anticipation needs no new mechanism — a mock is an ordinary microfunction, and one that reads
what I know I changed IS the model of the tool. If it cannot, there is a real gap.

⚠⚠ THE VACUITY GUARD IS THE WHOLE PROBE: it must be the **same mock**, unedited, in both runs, and the two
predictions must differ **because the world differs**. A probe that used two mocks would be measuring the
ordinary constant-assumption machinery and would light up meaninglessly.

⚠ And a second thing this example exposes: `git status` is a **look**, not an **act**. An expectation on an
act asks *did my action do what I thought*. An expectation on a look asks *was my belief about the world
right*. The user's chain is act → belief → look, and the look is where the belief gets tested.
"""
from __future__ import annotations
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from microfunctions import asm, dispatch as D, execution as X, function as fn   # noqa: E402
from microfunctions import types as TY, workbench as W                          # noqa: E402
from microfunctions.graph import new_graph                                      # noqa: E402

declare = TY.declare_type
bar = "=" * 86


def repo(*, edited: bool):
    """A working tree, and `git_status` — a LOOK whose mock is a MODEL, not an assumption.

    ⭐ `anticipate` is the only mock, and it **branches on the graph**: if the tree holds a `changed` file
    it predicts the report is dirty, otherwise clean. That is the user's sentence as a microfunction."""
    g = new_graph()
    declare(g, "tree", attrs={"kind_of": "tree"})
    declare(g, "report", base="tree", attrs={"reported": True})
    asm.load_text(g, "\n".join([
        "# Edit a file in the working tree. An ACT: it changes the world.",
        "fn edit(t: tree) -> tree:",
        '    NEW R(f) "file"',
        '    SET R(f) "changed" true',
        '    LINK F(t) "changed_file" R(f)',
        "",
        "# Ask git what it thinks. A LOOK: it only reports.",
        "fn git_status(t: tree) -> report:",
        '    DISPATCH R(out) "git_status" F(t)',
        '    SET F(t) "reported" true',
        "",
        "# ⭐ THE MODEL. Not 'suppose it comes back dirty' but 'work out what it will say'.",
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
    ]))
    t = g.mint("tree", kind_of="tree")
    g.link("root", "has", t)
    if edited:
        fn.invoke(g, "edit", {"t": t})            # I changed some files, and I KNOW I did
    return g, t


def what_it_anticipates(g, t):
    """Plan one `git_status` step and read the prediction back off the two frames."""
    wb = W.open_workbench(g, t)
    f0 = W.root_frame(g, wb)
    f1, tr = W.step(g, wb, f0, "git_status", {"t": W.mapping_for(g, f0, t)}, assume="anticipate")
    return wb, f0, f1, tr, W.predicted_changes(g, f0, f1)


print(bar)
print("  THE SAME MOCK, TWO WORLDS. Does the prediction follow the world?")
print(bar)

g_clean, t_clean = repo(edited=False)
_, _, _, _, pred_clean = what_it_anticipates(g_clean, t_clean)
attrs_clean = {k: v for _m, k, v in pred_clean["attrs"]}

g_dirty, t_dirty = repo(edited=True)
wb, f0, f1, tr, pred_dirty = what_it_anticipates(g_dirty, t_dirty)
attrs_dirty = {k: v for _m, k, v in pred_dirty["attrs"]}

print(f"  nothing edited -> it anticipates : {attrs_clean}")
print(f"  files edited   -> it anticipates : {attrs_dirty}")
same_mock = fn.mocks_of(g_clean, "git_status") == fn.mocks_of(g_dirty, "git_status") == ("anticipate",)
differs = attrs_clean != attrs_dirty
print(f"  ONE mock, identical in both      : {same_mock}")
print(f"  and the predictions DIFFER       : {differs}")
print(f"  -> the expectation was INFERRED FROM THE WORLD, not asserted: {same_mock and differs}")

print()
print(bar)
print("  AND DOES A WORLD THAT CONTRADICTS THE ANTICIPATION DIVERGE?")
print(bar)


def lying_git(gr, target):
    """Reality: git reports CLEAN even though files were changed. The surprise the user would want caught."""
    gr.put(target, dirty=False)


def honest_git(gr, target):
    gr.put(target, dirty=True)


D.register("git_status", lying_git, observes=True)
diverged = X.execute(g_dirty, wb, f1)
dev = diverged["deviation"] or {}

g_ok, t_ok = repo(edited=True)
wb2, _, f1b, _, _ = what_it_anticipates(g_ok, t_ok)
D.register("git_status", honest_git, observes=True)
matched = X.execute(g_ok, wb2, f1b)

print(f"  I edited files, git says clean   : DIVERGED = {not diverged['completed']}")
print(f"    it says                        : {dev.get('unmet_expectations')}")
print(f"    the CAST itself passed         : {W.deviates(g_dirty, tr, t_dirty) == {}}")
print(f"  CONTROL, git agrees              : completed = {matched['completed']}")

print()
print(bar)
print("  IS THIS EVEN AN ACT? `verb_of` on the tool")
print(bar)
print(f"  git_status registered as observing: {D.observes(None, 'git_status')}")
print("  -> the expectation is on a LOOK. It tests a BELIEF about the world,")
print("     not the effect of an action.")

print()
print(bar)
print("  VERDICT")
print(bar)
print(f"  a mock can READ THE WORLD and anticipate rather than assume : {same_mock and differs}")
print(f"  a contradicting world is caught as a divergence            : {not diverged['completed']}")
print(f"  the control (world agrees) completes                       : {matched['completed']}")
