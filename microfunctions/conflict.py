"""CONFLICT — noticing that two things disagree, instead of letting one silently win.

`HANDOFF.md` §5 records this as a **regression, not a deferral**: the old rule engine surfaced two
conclusions disagreeing rather than letting one overwrite the other, and the composition-safety argument for
an open middle tier rested on that. The new engine had nothing.

**⚠ But the old notion does not transfer, and copying it would have been wrong.** That engine *derived
facts*: two rules concluding contradictory things at once is a contradiction, full stop. This engine
*performs actions in sequence*, and a later action overriding an earlier one is not a disagreement — it is
what doing things looks like. `stack` sets `clear` false on one block and true on another every time it
runs. Reporting that as a conflict would bury the real ones.

So what actually survives of the concern? **Interference** — the telecom feature-interaction problem
`function.py` cites as the prior art. Two independently-authored functions, composed by a library that grew
without either author knowing about the other, writing the same thing for unrelated reasons. That is the
risk the open middle tier really carries, and it is a different question from "did a value change twice".

**Two detectors, because two genuinely different things are being asked.**

* **`unsatisfiable`** — *this goal cannot be met, and we can prove it before searching.* Decidable cases
  only, so there are no false positives: two attribute constraints on the same slot demanding different
  values; `never f` together with `must f`; a budget of zero. Cheap, and it turns a fruitless search into
  an immediate honest answer.
* **`interference`** — *two applications serving **different goals** wrote the same slot different ways.*
  The different-goal requirement is what separates interference from an ordinary sequel: steps within one
  plan are a deliberate sequence, and treating them as conflicting would be noise.

**⭐ A detected conflict needs no new node kind.** It is a `connection` between two thread entries with the
relation `conflicts` — the cross-link mechanism `thread.py` already has, and which exists precisely so that
distant moments can be related. That is the "needs no new mechanism, only writing them" claim made good,
and it means a conflict is ordinary data: pointable-at, disputable, and readable by a rule.

**⚠ What is read, and how approximate it is.** A claim is read off a function's stored body — a `SET` whose
key *and* value are literals and whose subject is a parameter. That is deliberately narrow: if the key, the
value or the subject is computed, nothing is claimed, so this **under-reports rather than over-reports**.
An honest miss is much better here than a false alarm, because a conflict report nobody trusts is worse than
no report at all.
"""
from __future__ import annotations

from . import application as ap
from . import function as fn
from . import goal as G
from . import thread as T
from .graph import Graph
from .isa import F


# --- what a function claims ---------------------------------------------------------------------
def claims_of(g: Graph, name: str) -> tuple:
    """`(param, key, value)` for every literal attribute this function writes to a parameter.

    Narrow on purpose — see the module docstring. A computed key or value claims nothing."""
    params, program = fn.load(g, name)
    out = []
    for ins in program:
        if isinstance(ins, str) or ins.op != "SET" or len(ins.args) < 3:
            continue
        subject, key, value = ins.args[0], ins.args[1], ins.args[2]
        if not (isinstance(subject, F) and subject.name in params):
            continue                    # a computed subject — we cannot say whose slot this is
        if not isinstance(key, str):
            continue                    # a computed key — we cannot say which slot
        if not (value is None or isinstance(value, (str, bool, int, float))):
            continue                    # a computed value — we cannot say what was claimed
        out.append((subject.name, key, value))
    return tuple(out)


def wrote(g: Graph, application: str) -> dict:
    """`{(node, key): value}` — what this application claimed, with parameters resolved to real nodes."""
    name = g.attr(application, "function")
    if name is None or fn.find(g, name) is None:
        return {}
    bindings = ap.bindings_of(g, application)
    out = {}
    for param, key, value in claims_of(g, name):
        node = bindings.get(param)
        if node is not None:
            out[(node, key)] = value
    return out


# --- interference between goals -------------------------------------------------------------------
def interference(g: Graph, thread: str, *, record: bool = True) -> tuple:
    """Applications serving **different goals** that wrote the same slot different ways.

    Returns the conflicts as `(earlier, later, node, key, old, new)`. With `record`, each is also tied
    together on the thread as a `conflicts` connection, so the finding is data rather than a return value
    somebody has to remember to look at.

    ⚠ **Grouped by goal, not scanned as a running latest-value.** The first version kept only the most
    recent write per slot and compared each new one against it — which silently lost the very pairs it was
    looking for: the second goal re-imagined the *same* action before its differing one, so the running
    value was overwritten by a same-goal entry and the cross-goal disagreement never met. Interference is a
    property of two intents, not of two adjacent writes, so the claims have to be collected per intent
    first and compared afterwards.

    ⚠ **Only what was actually DONE.** The driver records every proposal it considers, most from branches
    it abandons, so the thread holds the *search* as well as the actions. Comparing what two goals merely
    imagined would report interference between two ideas neither of them acted on — and did, in the first
    version: a goal that considered `paint` before choosing `varnish` looked like it claimed both.

    ⚠ An entry with no recorded goal is left out of every pair. Its provenance is unknown, and this module
    would rather miss a conflict than invent one."""
    claims: dict = {}
    for entry in T.entries(g, thread):
        if g.kind(entry) != "application" or not g.attr(entry, "done"):
            continue
        goal = g.target(entry, "for_goal")
        if goal is None:
            continue
        for slot, value in wrote(g, entry).items():
            claims.setdefault(slot, {})[goal] = (entry, value)   # a goal's net claim is its last

    found = []
    for (node, key), by_goal in claims.items():
        pairs = sorted(by_goal.items())
        for i, (goal_a, (entry_a, value_a)) in enumerate(pairs):
            for goal_b, (entry_b, value_b) in pairs[i + 1:]:
                if value_a == value_b:
                    continue
                found.append((entry_a, entry_b, node, key, value_a, value_b))
                if record:
                    T.connect(g, entry_b, entry_a, "conflicts",
                              note=f"{key}: {value_a!r} vs {value_b!r}")
    return tuple(found)


def conflicts_on(g: Graph, thread: str) -> tuple:
    """Every conflict already recorded on this thread — a lookup, not a re-computation."""
    out = []
    for entry in T.entries(g, thread):
        out.extend(c for c in T.connections(g, entry, "conflicts") if c not in out)
    return tuple(out)


# --- a goal that cannot be met ----------------------------------------------------------------------
def unsatisfiable(g: Graph, goal: str) -> tuple:
    """Why this goal cannot be met, provable before any searching. Empty means "no proof either way".

    ⚠ **Decidable cases only, so there are no false positives.** Nothing here is a heuristic: two attribute
    constraints demanding different values of one slot, a forbidden operator that is also required, and a
    budget of zero are each impossible by inspection. Anything subtler — "a on b" together with "b on a" —
    is left to the search, because calling it impossible would need domain knowledge the engine does not
    have and must not pretend to."""
    reasons = []
    wants: dict = {}
    for c in G.world_constraints(g, goal):
        if g.attr(c, "sort") != "attr":
            continue
        slot = (g.target(c, "subject"), g.attr(c, "key"))
        if slot in wants and wants[slot][1] != g.attr(c, "value"):
            reasons.append(f"{G.describe_constraint(g, wants[slot][0])} contradicts "
                           f"{G.describe_constraint(g, c)}")
        wants[slot] = (c, g.attr(c, "value"))

    banned = {g.attr(c, "function") for c in G.constraints(g, goal)
              if g.attr(c, "sort") == "never" and g.attr(c, "function")}
    for c in G.constraints(g, goal):
        if g.attr(c, "sort") == "eventually" and g.attr(c, "function") in banned:
            reasons.append(f"{g.attr(c, 'function')!r} is both required and forbidden")
        if g.attr(c, "sort") == "at_most" and g.attr(c, "limit", 0) < 1 \
                and G.world_constraints(g, goal):
            reasons.append("a budget of zero steps cannot change anything")
    return tuple(reasons)


def describe(g: Graph, thread: str) -> str:
    found = conflicts_on(g, thread)
    if not found:
        return "no conflicts recorded"
    lines = [f"{len(found)} conflict(s):"]
    for c in found:
        a, b = g.target(c, "from"), g.target(c, "to")
        lines.append(f"  {g.attr(b, 'function')} and {g.attr(a, 'function')} — {g.attr(c, 'note')}")
    return "\n".join(lines)


__all__ = ["claims_of", "wrote", "interference", "conflicts_on", "unsatisfiable", "describe"]
