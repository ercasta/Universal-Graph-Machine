"""Reachability — is there a name a rule can call?

`access.offenders` asks a compliance question about rule bodies: does this one touch the graph
without going through the vocabulary? This module asks the mirror question about *Python*: of the
machinery the engine runs, how much of it could a rule start?

The distinction matters because the de-Pythonization arc has been using a different criterion.
Everything moved to the surface so far — `workbench.step`, `goal.holds`, `deviates`,
`unmet_expectations`, `predicted_changes`, `execution.step` — is a **stepper**: it runs inside
machinery Python has already started. *You can watch the machine run; you cannot start it from a
rule.* Nothing measured that, so it was argued from a hand-written list, and a hand-written list is
the shape this codebase keeps recording as the thing that drifts. This is the measurement.

**A rule reaches Python through exactly two doors**, and that is what makes the question decidable
rather than a matter of taste:

* an **opcode**, which the kernel executes itself, and
* a **native**, which the kernel looks up by name in a table it does not populate.

There is no third. `INVOKE` reaches another stored body, which bottoms out in those two again. So
what a rule can reach is the transitive closure of the Python call graph from those doors, what the
engine *does* is the closure from its own entry points, and the difference is an inventory rather
than an opinion.

⚠ **This reads Python, and that is the point rather than a compromise.** The boundary being audited
is Python's, so nothing in the graph can see it — a pass written in the surface could only report
what the surface already reaches, which is the question begged. It is also why this module is not
part of the engine's own machinery and never runs during a plan.

**The call graph is over-approximated in one direction and under-approximated in another, and both
are stated rather than hidden.** A dynamic call — `_PHASES[phase](g, p)` — is followed only because
the table it indexes is a module global this reads through; a call through a value computed at run
time is invisible, and a function reached only that way will be reported unreachable when it is not.
The direction is chosen the way `precedence._covers` chooses its own: **a false "unreachable" costs
somebody a look, a false "reachable" hides work the arc has left to do.** Losing a look is
recoverable; a gap nobody can see is what this exists to prevent.

See `docs/HANDOFF.md` §0.
"""
from __future__ import annotations

import dis
import importlib
import pkgutil
import types as PY

#: Modules that are about the engine rather than part of it. A check is not machinery, and a
#: benchmark is not either — including them would report the harness as unreachable, truly and
#: uselessly.
NOT_MACHINERY = ("selftest", "bench", "reach")


def _modules() -> tuple:
    """Every engine module, imported. Registration is an import side effect (`native.py`), so the
    door list is only complete once they all are — asking this question of a half-imported package
    would report whatever happened to be loaded."""
    import ugm
    out = []
    for m in sorted(pkgutil.iter_modules(ugm.__path__), key=lambda m: m.name):
        if m.name not in NOT_MACHINERY:
            out.append(importlib.import_module(f"ugm.{m.name}"))
    return tuple(out)


def _is_ours(obj) -> bool:
    return isinstance(obj, PY.FunctionType) and getattr(obj, "__module__", "").startswith("ugm.")


def _in_module(obj) -> bool:
    return isinstance(obj, PY.ModuleType) and obj.__name__.startswith("ugm.")


def _codes(code):
    yield code
    for c in code.co_consts:
        if isinstance(c, PY.CodeType):
            yield from _codes(c)


def _held(value) -> set:
    """The engine functions a module-level container holds.

    `driver._PHASES` maps a phase name to the body that runs it, and `pursuit_step` calls it by
    subscript — so the phase machine hangs off a dictionary rather than off a name. Reading the
    container is what keeps a dispatch table from looking like a dead end."""
    if _is_ours(value):
        return {value}
    if isinstance(value, dict):
        out = set()
        for v in value.values():
            out |= _held(v)
        return out
    if isinstance(value, (tuple, list, set, frozenset)):
        out = set()
        for v in value:
            out |= _held(v)
        return out
    return set()


def calls(f) -> set:
    """The engine functions this one may call, read off its bytecode.

    Off `dis` rather than `co_names`, because `co_names` is a bag: a body naming the module `TY` and
    the local `check` would be read as calling `types.check` whether or not those two names are ever
    adjacent. Here a module reference only becomes an edge when the very next instruction takes an
    attribute off it, which is what a call actually looks like.

    Three ways one function names another here, and all three are in the corpus:
    a plain global; an attribute of a module imported at the top (`TY.subsumes`); and an attribute of
    a module imported **inside the body**, which most of this package does to break import cycles and
    which lands in a local rather than a global."""
    out, glob = set(), f.__globals__
    for code in _codes(f.__code__):
        local_mod, pending_from = {}, None
        ins = list(dis.get_instructions(code))
        for i, x in enumerate(ins):
            nxt = ins[i + 1] if i + 1 < len(ins) else None
            if x.opname == "IMPORT_FROM":
                pending_from = x.argval
            elif x.opname in ("STORE_FAST", "STORE_NAME", "STORE_DEREF") and pending_from:
                try:                                       # `from . import types as TY`
                    local_mod[x.argval] = importlib.import_module(f"ugm.{pending_from}")
                except ModuleNotFoundError:
                    pass
                pending_from = None
            elif x.opname == "LOAD_GLOBAL":
                got = glob.get(x.argval)
                if _is_ours(got):
                    out.add(got)
                elif _in_module(got) and nxt is not None and nxt.opname == "LOAD_ATTR":
                    attr = getattr(got, nxt.argval, None)
                    if _is_ours(attr):
                        out.add(attr)
                else:
                    out |= _held(got)                      # a dispatch table, e.g. `driver._PHASES`
            elif x.opname in ("LOAD_FAST", "LOAD_DEREF", "LOAD_NAME"):
                mod = local_mod.get(x.argval)
                if mod is not None and nxt is not None and nxt.opname == "LOAD_ATTR":
                    attr = getattr(mod, nxt.argval, None)
                    if _is_ours(attr):
                        out.add(attr)
    return out


def fronted(f) -> tuple:
    """The surface functions this Python one delegates to, by literal name.

    ⭐ **The correction that keeps this pass from reporting the arc's successes as its failures.**
    `workbench.deviates` is a thin wrapper around `rules/deviate.mf`; a rule never calls the Python at
    all, it calls `deviates`. Read as a Python call graph the wrapper is unreachable — and the more of
    the engine that moves to the surface, the *worse* the number gets, which is precisely backwards.
    A wrapper is not a gap: the capability has a name, which was the question.

    Derived from the wrapper's own shape rather than declared, because a declared list of what has
    been swapped is the thing that drifts. The tell is a **literal**: a wrapper names the body it
    stands for (`fn.invoke(g, "deviates", …)`), while Python calling the surface for its own reasons
    passes a name it was given (`precedence._by_function` invokes whatever stage names) and fronts
    nothing. One is a door with a sign on it; the other is a call.

    Deliberately does **not** propagate. What the wrapper calls around the invoke — `as_violations`
    renders the surface's node back into the dict its Python callers read — has no name of its own and
    stays in the inventory, which is right: it is Python the surface does not have and does not want.
    """
    from . import function
    out, glob = [], f.__globals__
    for code in _codes(f.__code__):
        local_mod = {}
        pending_from = None
        ins = list(dis.get_instructions(code))
        for i, x in enumerate(ins):
            nxt = ins[i + 1] if i + 1 < len(ins) else None
            if x.opname == "IMPORT_FROM":
                pending_from = x.argval
            elif x.opname in ("STORE_FAST", "STORE_NAME", "STORE_DEREF") and pending_from:
                try:
                    local_mod[x.argval] = importlib.import_module(f"ugm.{pending_from}")
                except ModuleNotFoundError:
                    pass
                pending_from = None
            got = None
            if x.opname == "LOAD_GLOBAL" and _is_ours(glob.get(x.argval)):
                got = glob.get(x.argval)
            elif nxt is not None and nxt.opname == "LOAD_ATTR":
                holder = (glob.get(x.argval) if x.opname == "LOAD_GLOBAL"
                          else local_mod.get(x.argval))
                if _in_module(holder):
                    got = getattr(holder, nxt.argval, None)
            if got is not function.invoke:
                continue
            # The name sits among the call's own arguments, a few instructions along.
            for y in ins[i + 1:i + 8]:
                if y.opname == "LOAD_CONST" and isinstance(y.argval, str):
                    out.append(y.argval)
                    break
    return tuple(out)


def closure(roots) -> set:
    seen, todo = set(), list(roots)
    while todo:
        f = todo.pop()
        if f in seen:
            continue
        seen.add(f)
        todo.extend(calls(f))
    return seen


# --- the doors ----------------------------------------------------------------------------------------
def doors() -> set:
    """Everything a rule can enter Python at: every opcode, and every registered native.

    Registered *values*, not registered names — most natives are lambdas closing over the real
    function, so the callable in the table is a door onto whatever it calls, and the lambda itself is
    nobody's machinery."""
    from . import isa, native
    _modules()                                             # every owner imported, so the table is whole
    out = set()
    for name in native.names():
        fn = native._REGISTRY[name]
        if _is_ours(fn):
            out.add(fn)
        out |= calls(fn) if isinstance(fn, PY.FunctionType) else set()
    for holder in (isa, isa.Machine):
        out |= {v for v in vars(holder).values() if _is_ours(v)}
    return out


def reachable() -> set:
    """Every engine function a rule could get to, however indirectly."""
    return closure(doors())


# --- the machinery ------------------------------------------------------------------------------------
#: Where the engine is entered from Python, as `(module, function)`. Roots rather than an inventory:
#: what each one *calls* is derived, which is the property that keeps this from becoming the
#: hand-written list it replaces. Adding one is a claim that a new thing is a way in.
ENTRY_POINTS = (
    ("driver", "carry_out"),        # the whole plan-act-check loop
    ("driver", "follow"),
    ("driver", "pursuit_step"),     # one primitive step of it
    ("driver", "open_pursuit"),     # starting one
    ("goal", "open_goal"),          # authoring what is pursued
    ("loop", "schedule"),           # putting it on an agenda
    ("loop", "run"),
)


def machinery() -> set:
    """Everything the engine does when it pursues a goal."""
    roots = set()
    for mod, name in ENTRY_POINTS:
        roots.add(getattr(importlib.import_module(f"ugm.{mod}"), name))
    return closure(roots)


def name_of(f) -> str:
    return f"{f.__module__[len('ugm.'):]}.{f.__qualname__}"


def _has_a_name(f) -> bool:
    """A lambda is not an answer to *is there a name a rule can call?* in either direction.

    Anonymous functions stay in the call graph, because the edges through them are real; they are
    left out of the **inventory**, because a reader cannot act on one. What a reader acts on is the
    function it is written inside, which is reported on its own account."""
    return "<" not in f.__qualname__


def unreachable() -> tuple:
    """The machinery no rule can start, by name and in order — the pass.

    Empty is the property the arc is trying to reach, exactly as `access.offenders` empty is the
    property mediation holds. It is not empty today and is not expected to be until P2–P4 land, so
    what this is for in the meantime is that the inventory **shrinks measurably** rather than being
    re-argued from prose each session."""
    gap = machinery() - reachable()
    return tuple(sorted(name_of(f) for f in gap if _has_a_name(f) and not fronted(f)))


def why(f) -> str:
    """One path from a door to `f`, so a *reachable* verdict can be checked rather than trusted.

    A pass whose positive answers cannot be inspected is the opaque predicate this project refuses
    everywhere else — and this one's positives are the load-bearing half, since a wrong *reachable*
    is what silently retires work the arc still has to do."""
    from collections import deque
    start = doors()
    back, seen, q = {}, set(start), deque(start)
    while q:
        cur = q.popleft()
        if cur is f:
            path = [cur]
            while path[-1] in back:
                path.append(back[path[-1]])
            return " <- ".join(name_of(x) for x in path)
        for c in calls(cur):
            if c not in seen:
                seen.add(c)
                back[c] = cur
                q.append(c)
    return "(no path from any door)"


def report() -> str:
    """The pass, for a reader. `python -m ugm.reach`."""
    m, r = machinery(), reachable()
    named = {f for f in m if _has_a_name(f)}
    gap = unreachable()
    fronts = sorted(name_of(f) for f in named - r if _has_a_name(f) and fronted(f))
    lines = [f"machinery: {len(named)}   reachable from a rule: {len(named & r)}   "
             f"fronted by a surface name: {len(fronts)}   UNREACHABLE: {len(gap)}", ""]
    lines += [f"  {n}" for n in gap]
    lines += ["", "fronted (a wrapper around a body a rule can call by name):"]
    lines += [f"  {n}" for n in fronts]
    return "\n".join(lines)


__all__ = ["ENTRY_POINTS", "calls", "closure", "doors", "reachable", "machinery",
           "unreachable", "why", "name_of", "report"]

if __name__ == "__main__":
    print(report())
