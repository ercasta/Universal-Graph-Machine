"""The horizon, measured — how much would it cost to change a closed set?

`docs/concepts.md` draws a line: below it, primitives the system executes but cannot argue about;
above it, a language and the machines written in it. A member is admissible below the line only if
*every decision it embodies can be an argument*. That is a criterion for admitting one, and it says
nothing about what admitting one **costs later** — which is the question that actually decides whether
a system can revise itself.

This measures that cost, and the finding it exists to record is that **"closed" is a rate rather than
a kind**. Nothing forbids a fifth constraint sort. It costs seventeen dispatchers, because seventeen
places switch on what the sorts are. A fifth precedence stage costs one table entry and one
comparator. Same word, two orders of magnitude apart — so *innate* and *learnable* are not two
categories of rule here, they are the two ends of a gradient whose steepness anyone can measure.

⭐ **And the cheap end is not an accident: it is where work has already been done.** The two sets with
**zero** dispatchers — precedence stages and strengths — are exactly the two this project already moved
above the horizon, by making the ranking authored data dispatched through a table (`precedence._COMPARE`)
instead of a switch. Nothing switches on them because *the switch is itself data*. That gives the
migration a mechanism rather than a hope: **a closed set becomes revisable when its dispatch becomes a
lookup keyed by the member.** It is the engineering form of grammaticalization, and it has happened twice
here already without anybody calling it that.

**What counts as a dependence, and why three earlier answers were wrong.** The first version of this
counted *mentions* of a member and produced a confident wrong number three times running: named
constants made table dispatch invisible (`BY_AUTHORITY` never appears as a string), overloaded words
inflated counts (`"force"` is also an attribute key), and one scan had the wrong corpus. The unit was the
defect — **a mention is not a dependence** — and one rule fixes all three:

> a function naming **two or more** members of the same closed set is switching on that set.

One word in isolation is not a switch, so `g.attr(c, "force")` drops out. Resolving a global to its value
is the same work as reading a literal, so named constants survive. And it asks about the *set*, so no
corpus can be missed by accident. ⚠ It measures the set, not the member, and that is the right
granularity anyway: nobody adds one constraint sort, what changes is *what the sorts are*.

⚠ **The set with the most dispatchers was the one that had never been declared**, which is this
document's own lesson arriving as a measurement: *a closed class earns its place by being declared*. What
stood in for `goal.WORLD_SORTS` was `intake._SORTS` — private to the parser, missing `known`, and
restated as a literal elsewhere. An undeclared class is what accretes switches, because there is nothing
for a reader to consult and nothing for a check to hold it to.

See `docs/reflection.md`.
"""
from __future__ import annotations

import collections
import dis
import types as PY

from .graph import Graph


def closed_sets() -> dict:
    """`{group: (where it is declared, members)}` — read from the owning modules, never restated here.

    Restating them would make this pass a second place the closed class is written down, and a second
    place is what drifts. Every entry names the constant it came from, so a reader can go and look."""
    from . import access, consequent, goal, precedence
    return {
        "access vocabulary": ("access.VOCABULARY", frozenset(access.VOCABULARY)),
        "constraint sort": ("goal.WORLD_SORTS", frozenset(goal.WORLD_SORTS)),
        "plan sort": ("goal.PLAN_SORTS", frozenset(goal.PLAN_SORTS)),
        "consequent kind": ("consequent.KINDS", frozenset(consequent.KINDS)),
        "precedence stage": ("precedence.STAGES", frozenset(precedence.STAGES)),
        "strength": ("precedence.STRENGTHS", frozenset(precedence.STRENGTHS)),
        "goal force": ("goal.FORCES", frozenset(goal.FORCES)),
    }


def _codes(code):
    yield code
    for c in code.co_consts:
        if isinstance(c, PY.CodeType):
            yield from _codes(c)


def names_of(f) -> set:
    """Every string this function names — as a literal, or through a global that holds one.

    The global case is not a refinement, it is the difference between working and not: a codebase
    disciplined enough to write `BY_AUTHORITY` instead of `"authority"` would otherwise measure as
    having no dependencies at all, which is exactly backwards."""
    out, glob = set(), f.__globals__
    for code in _codes(f.__code__):
        for k in code.co_consts:
            if isinstance(k, str):
                out.add(k)
        ins = list(dis.get_instructions(code))
        for i, x in enumerate(ins):
            if x.opname != "LOAD_GLOBAL":
                continue
            got = glob.get(x.argval)
            nxt = ins[i + 1] if i + 1 < len(ins) else None
            if isinstance(got, PY.ModuleType) and nxt is not None and nxt.opname == "LOAD_ATTR":
                got = getattr(got, nxt.argval, None)
            if isinstance(got, str):
                out.add(got)
    return out


def python_dispatchers() -> dict:
    """`{group: ((function, how many members it names), …)}` for the engine's Python."""
    from . import reach as RE
    out = collections.defaultdict(list)
    sets = closed_sets()
    for mod in RE._modules():
        for f in vars(mod).values():
            if not RE._is_ours(f):
                continue
            named = names_of(f)
            for group, (_where, members) in sets.items():
                hit = named & members
                if len(hit) >= 2:
                    out[group].append((RE.name_of(f), len(hit)))
    return {k: tuple(sorted(v, key=lambda t: (-t[1], t[0]))) for k, v in out.items()}


def surface_dispatchers(g: Graph) -> dict:
    """The same question of the stored rules in `g` — whatever corpus the caller has loaded.

    Takes a graph rather than finding one, because *which corpus* is the caller's business and a pass
    that quietly chose for itself is how the third wrong answer happened."""
    from . import function as fn
    out = collections.defaultdict(list)
    sets = closed_sets()
    for name in sorted(set(fn.names(g))):
        try:
            _params, program = fn.load(g, name)
        except Exception:
            continue
        seen = set()
        for ins in program:
            if isinstance(ins, str):
                continue
            for a in ins.args:
                if isinstance(a, str):
                    seen.add(a)
                elif isinstance(a, dict):
                    seen |= {v for v in a.values() if isinstance(v, str)}
        for group, (_where, members) in sets.items():
            hit = seen & members
            if len(hit) >= 2:
                out[group].append((name, len(hit)))
    return {k: tuple(sorted(v, key=lambda t: (-t[1], t[0]))) for k, v in out.items()}


def cost(g: Graph | None = None) -> tuple:
    """`(group, declared_at, members, python, surface, total)` per closed set, dearest first.

    `total` is the answer to *what would it cost to change what this set is* — and the spread across
    the sets is the whole finding."""
    py = python_dispatchers()
    mf = surface_dispatchers(g) if g is not None else {}
    rows = []
    for group, (where, members) in closed_sets().items():
        n_py, n_mf = len(py.get(group, ())), len(mf.get(group, ()))
        rows.append((group, where, len(members), n_py, n_mf, n_py + n_mf))
    return tuple(sorted(rows, key=lambda r: (-r[5], r[0])))


def table_dispatched(g: Graph | None = None) -> tuple:
    """The closed sets nothing switches on — the ones already above the horizon.

    Zero is not *unused*; it means every member is reached through a lookup keyed by the member, so
    adding one is data rather than an edit. This is the property the migration aims at, and naming it
    is what keeps a zero from being read as neglect.

    ⚠ Takes the same graph `cost` was asked with, and that is not tidiness: computing this without the
    corpus reported the **access vocabulary** as table-dispatched while the row above it said 9, because
    all nine of its dispatchers are rules. A second answer derived from a different population is the
    same defect that made three earlier versions of this measurement wrong."""
    return tuple(r[0] for r in cost(g) if r[5] == 0)


def report(g: Graph | None = None) -> str:
    """`python -m ugm.horizon`. Pass nothing for Python only; the surface needs a loaded corpus."""
    rows = cost(g)
    lines = [f"{'total':>6}{'python':>8}{'surface':>9}{'members':>9}   {'set':<20}declared at", "-" * 78]
    for group, where, n, n_py, n_mf, total in rows:
        lines.append(f"{total:>6}{n_py:>8}{n_mf:>9}{n:>9}   {group:<20}{where}")
    dear, cheap = rows[0], rows[-1]
    lines += ["", f"spread: {dear[0]} costs {dear[5]}, {cheap[0]} costs {cheap[5]} — "
                  f"'closed' is a rate, not a kind.",
              f"already above the horizon (dispatched by table): {', '.join(table_dispatched(g)) or '-'}"]
    return "\n".join(lines)


__all__ = ["closed_sets", "names_of", "python_dispatchers", "surface_dispatchers",
           "cost", "table_dispatched", "report"]

if __name__ == "__main__":
    from pathlib import Path

    from . import asm, function as fn
    from .graph import new_graph

    _g = new_graph()
    for _f in sorted((Path(fn.__file__).parent / "rules").glob("*.mf")):
        try:
            asm.load_file(_g, _f)
        except Exception:
            pass
    print(report(_g))
