"""PROBE — A MOCK MUST MAP *CONDITIONS* TO EXPECTATIONS (the user, 2026-08-02)

> Expectations must be **conditioned**; a mock must **map conditions to expectations**, so even during
> planning we know what to expect if we perform an action **on a given state**.

`probe_anticipation.py` showed a mock CAN read the world and predict from it. But it did so by **branching
inside its own body**, and that makes the condition invisible: you learn what `anticipate` assumes only by
running it in a particular state. Two things follow, and both are measured here:

  (A) **`driver.establishes` DOES NOT READ BRANCHES** — its own comment says so: *"a conditional write is
      reported as unconditional"*. So a branching mock claims **both** of its outcomes, unconditionally.
      ⚠⚠ And this reopens a settled question: HANDOFF recorded on 2026-08-01 that control flow darkens
      nothing in practice (*"8 of 10 already exact… not one is darkened by control flow"*). **That was
      measured over a library in which no mock was conditional** — §6p has since established that every
      mock in this repo was written as a CONSTANT. The premise of that measurement is gone.

  (B) **MOCK SELECTION IGNORES THE STATE.** `workbench.step` takes `outcomes[0]` — declaration order —
      unless a caller names one with `assume=`. So *"what to expect if we perform this action on a given
      state"* is answered today without consulting the state at all.

⭐ The candidate fix needs **no new representation**: a mock is an ordinary microfunction with **typed
parameters**, and a parameter type is already a schema over a subgraph — i.e. already a condition, already
declarative, already enforced by `fn.invoke`. So *condition → expectation* is:

    fn found_dirty(t: dirty_tree) -> report mocks git_status   # condition IS the parameter type
    fn found_clean(t: clean_tree) -> report mocks git_status

and selection is *the first mock whose condition holds in this state*. Each body is then branch-free, so
`establishes` is exact per outcome instead of claiming both.

⚠ The control throughout: the branch-free encoding must give **different** predictions in the two worlds,
or it has merely traded a readable condition for no condition at all.
"""
from __future__ import annotations
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from microfunctions import asm, driver as DR, function as fn, types as TY, workbench as W  # noqa: E402
from microfunctions.graph import new_graph                                                 # noqa: E402
from microfunctions.types import Req                                                       # noqa: E402

declare = TY.declare_type
bar = "=" * 88

HEADER = [
    "fn edit(t: tree) -> tree:",
    '    NEW R(f) "file"',
    '    LINK F(t) "changed_file" R(f)',
    "",
    "fn git_status(t: tree) -> report:",
    '    DISPATCH R(out) "git_status" F(t)',
    '    SET F(t) "reported" true',
    "",
]

BRANCHING = HEADER + [
    "# ONE mock that branches internally. The condition is real but UNREADABLE.",
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
]

CONDITIONED = HEADER + [
    "# TWO mocks, each branch-free, each declaring its CONDITION as a parameter type.",
    "fn found_dirty(t: dirty_tree) -> report mocks git_status:",
    '    SET F(t) "reported" true',
    '    SET F(t) "dirty" true',
    "",
    "fn found_clean(t: clean_tree) -> report mocks git_status:",
    '    SET F(t) "reported" true',
    '    SET F(t) "dirty" false',
]


def world(lines, *, edited: bool, conditioned: bool):
    g = new_graph()
    declare(g, "tree", attrs={"kind_of": "tree"})
    declare(g, "report", base="tree", attrs={"reported": True})
    if conditioned:
        # ⭐ THE CONDITION, as an ordinary type: a tree with at least one changed file, and one with none.
        declare(g, "dirty_tree", {"changed_file": Req(kind="file", lo=1)}, attrs={"kind_of": "tree"})
        declare(g, "clean_tree", {"changed_file": Req(kind="file", lo=0, hi=0)}, attrs={"kind_of": "tree"})
    asm.load_text(g, "\n".join(lines))
    t = g.mint("tree", kind_of="tree")
    g.link("root", "has", t)
    if edited:
        fn.invoke(g, "edit", {"t": t})
    return g, t


# --- (A) does `establishes` read the branch? ------------------------------------------------------------
print(bar)
print("  (A) A BRANCHING MOCK: what does `establishes` think `git_status` does?")
print(bar)
gb, tb = world(BRANCHING, edited=True, conditioned=False)
eff, unknown = DR.establishes(gb, "git_status")
dirty_claims = sorted({v for k, lbl, _s, v in eff if k == "attr" and lbl == "dirty"}, key=str)
print(f"  values it claims for `dirty`  : {dirty_claims}")
print(f"  so it claims BOTH outcomes    : {len(dirty_claims) > 1}")
print(f"  and `unknown` does NOT say so : {not unknown or unknown == frozenset({None})}")
A_blind = len(dirty_claims) > 1

# --- (B) does mock selection consult the state? ---------------------------------------------------------
print()
print(bar)
print("  (B) MOCK SELECTION: does the prediction depend on the state?")
print(bar)


def predicted(g, t, *, assume=None):
    """⚠ Returns a STRING on refusal rather than raising: what happens when the default mock's condition
    does not hold is the measurement, not an accident to be worked around."""
    wb = W.open_workbench(g, t)
    f0 = W.root_frame(g, wb)
    try:
        f1, _tr = W.step(g, wb, f0, "git_status", {"t": W.mapping_for(g, f0, t)}, assume=assume)
    except TY.TypeViolation as e:
        return f"REFUSED: {getattr(e, 'param', '?')} is not a {getattr(e, 'want', '?')}"
    return {k: v for _m, k, v in W.predicted_changes(g, f0, f1)["attrs"]}


gd, td = world(CONDITIONED, edited=True, conditioned=True)
gc, tc = world(CONDITIONED, edited=False, conditioned=True)
print(f"  declared outcomes, in order   : {fn.mocks_of(gd, 'git_status')}")
print(f"  EDITED world, default choice  : {predicted(gd, td)}")
print(f"  CLEAN  world, default choice  : {predicted(gc, tc)}")
print()
print("  ⚠⚠ BEFORE THE FIX the clean world did not merely predict WRONGLY - it COULD NOT BE PLANNED AT")
print("     ALL: `step` took outcomes[0], `fn.invoke` enforced that mock's parameter type, and the")
print("     condition that should have SELECTED the other outcome instead REFUSED the only one offered")
print("     ('TypeViolation: t is not a dirty_tree'). The machinery already knew the condition failed;")
print("     nothing asked it before choosing. `workbench.step` now asks - see `fn.applicable`.")
default_follows_state = predicted(gd, td) != predicted(gc, tc)

# --- the fix: choose the mock whose CONDITION holds ------------------------------------------------------
print()
print(bar)
print("  THE CANDIDATE FIX: pick the first mock whose PARAMETER TYPES hold in this state")
print(bar)


def applicable(g, function: str, args: dict):
    """The declared outcomes whose conditions hold of these arguments, most preferred first.

    ⭐ No new representation: a mock's condition IS its parameter types, which `fn.invoke` already
    enforces on every call. This only asks the question *before* choosing rather than after."""
    out = []
    for outcome in fn.mocks_of(g, function):
        ptypes = fn.param_types(g, outcome)
        if all(want is None or not TY.violations(g, args[p], want)
               for p, want in ptypes.items() if p in args):
            out.append(outcome)
    return tuple(out)


for label, (g, t) in (("EDITED", (gd, td)), ("CLEAN ", (gc, tc))):
    fits = applicable(g, "git_status", {"t": t})
    print(f"  {label} world -> conditions that hold: {fits}")
    if fits:
        print(f"            -> it would predict     : {predicted(g, t, assume=fits[0])}")

fits_d = applicable(gd, "git_status", {"t": td})
fits_c = applicable(gc, "git_status", {"t": tc})
chosen_differs = bool(fits_d) and bool(fits_c) and fits_d[0] != fits_c[0]

# --- and is each branch-free mock now EXACT? ------------------------------------------------------------
print()
print(bar)
print("  AND IS `establishes` EXACT ONCE THE BODIES ARE BRANCH-FREE?")
print(bar)
for outcome in fn.mocks_of(gd, "git_status"):
    e, u = DR.establishes(gd, outcome)
    vals = sorted({v for k, lbl, _s, v in e if k == "attr" and lbl == "dirty"}, key=str)
    print(f"  {outcome:14} claims dirty in {vals}   unknown={set(u) or '{}'}")
per_mock_exact = all(
    len({v for k, lbl, _s, v in DR.establishes(gd, o)[0] if k == "attr" and lbl == "dirty"}) == 1
    for o in fn.mocks_of(gd, "git_status"))

print()
print(bar)
print("  VERDICT")
print(bar)
print(f"  (A) a branching mock claims BOTH outcomes, silently   : {A_blind}")
print(f"  (B) the default now FOLLOWS the state (was a crash)   : {default_follows_state}")
print(f"  the CONDITION is readable as a parameter type         : {chosen_differs}")
print(f"  CONTROL - the two worlds select DIFFERENT mocks       : {chosen_differs}")
print(f"  and each branch-free mock is exact on its own         : {per_mock_exact}")
