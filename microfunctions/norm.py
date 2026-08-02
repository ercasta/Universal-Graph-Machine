"""NORM — a prohibition that can be DEFEATED, arbitrated as data.

`docs/feedback_from_harneskills.md` §3 asked for this and offered "out of scope" as an acceptable answer.
The user's ruling, 2026-08-02: *"Why would it not be? Anything expressable should be in scope; we can
decide the HOW, but not the whether. And these things must be in data, not Python, otherwise we start
creating islands."*

**The gap it fills, in their words.** Their card-trader domain has standing house norms of differing
strength (*don't sell* — a default stance; *never counterfeit* — inviolable), transient daily instructions
(*today it is good to sell*), and an authority ranking (*today outranks standing*, and nothing outranks
the law). Every existing force was wrong for it:

| | why not |
|---|---|
| `never f` | prunes absolutely — right for the law, wrong for a defeasible default |
| `prefer` / `avoid` | reorders only, deliberately: *"advice quietly becoming a correctness rule"* is what it exists to prevent |
| `criterion` / `directive` | names an action to **take**; there is no *do not* |

So they composed the `never` lines in **~17 lines of Python** before building the goal. It worked, and the
loss was specific and is the whole reason this module exists: *"it used to be auditable"* — their old
engine could answer *"why is selling not excluded?"* by tracing to the outranking encouragement, and
Python that runs before the engine sees anything can answer nothing.

## ⭐⭐⭐ A NORM'S SOURCE IS ITS SPEAKER

The arbitration this needs — a transitive ranking over sources, with a default — already exists, built for
something else entirely: `discourse.authority`. *"Today outranks standing"* is the same shape as
*"the supervisor outranks the agent"*, and a norm is **an utterance by a source**. So there is no second
ranking mechanism, no norm-specific notion of strength, and *"who says so"* is answered by the ordinary
discourse record. ⭐ That also makes the audit trail free: the winning norm is a node, its source is a
node, and the losing norms are still there with the reason they lost.

## ⚠⚠ ARBITRATION HAPPENS BEFORE THE GOAL, NOT INSIDE THE PLANNER

HarneSkills flagged the shape they did **not** want and were right: a *"soft never"* that prunes unless
outranked would put arbitration inside the frontier. What makes their version work is that arbitration
happens when all the norms are in hand and **none of them is about a search state**. `settle` is therefore
a composition step that runs against the world, and `apply` writes ordinary `never` constraints — so
everything downstream (`goal.breached`, `driver.relevance`, `why`) is untouched and cannot tell the
difference. There is no fourth force in the planner.

⚠ **A tie is REFUSED, never broken silently.** Two conflicting norms whose sources are unranked relative
to each other is a question the author has not answered; picking one by declaration order would be an
undeclared tie-break inside a deterministic computation, which is exactly `search-was-irreproducible-set-
tiebreak`'s defect. The refusal names both sources and the action.
"""
from __future__ import annotations

from . import goal as G
from .graph import Graph

FORBID, PERMIT = "forbid", "permit"
STANCES = (FORBID, PERMIT)

#: Force, and it is the project's fourth force pair rather than a new idea — `method`/`procedure`,
#: `criterion`/`directive`, `prefer`/`avoid` all say the same thing about failure. ⚠ Declared, never
#: inferred: two norms can read identically and behave oppositely, so the author says which they mean.
DEFEASIBLE, INVIOLABLE = "defeasible", "inviolable"
FORCES = (DEFEASIBLE, INVIOLABLE)


class Undecidable(Exception):
    """Conflicting norms whose sources are not ranked. Loud, and naming both."""


def declare(g: Graph, *, action: str, stance: str = FORBID, source, force: str = DEFEASIBLE,
            because: str | None = None) -> str:
    """Declare one norm about one operator. `source` is an agent node (or a label)."""
    if stance not in STANCES:
        raise ValueError(f"a norm forbids or permits, not {stance!r}")
    if force not in FORCES:
        raise ValueError(f"force must be one of {FORCES}, not {force!r}")
    from .discourse import speaker
    n = g.mint("norm", action=action, stance=stance, force=force,
               **({"because": because} if because else {}))
    g.link(n, "source", source if source in g.nodes else speaker(g, source))
    g.link("root", "has", n)          # a norm is a real thing: it can be quoted, doubted, withdrawn
    return n


def norms(g: Graph, action: str | None = None) -> tuple:
    """Declared norms, withdrawn ones skipped — *"ignore that"* has to reach the thing that enumerates."""
    from .discourse import live
    return tuple(n for n in live(g, g.of_kind("norm"))
                 if action is None or g.attr(n, "action") == action)


def outranks(g: Graph, a: str, b: str) -> bool:
    """Does source `a` outrank source `b`? **The discourse ranking, unchanged** — see the module docstring."""
    from .path import reaches
    return a != b and reaches(g, a, "authority_over", b)


def settle(g: Graph, action: str) -> dict:
    """Arbitrate every norm about `action`. Returns `{stance, by, beat, because}`, or `stance=None`.

    ⭐ **Inviolable first, and it is not merely a high rank.** A source ranking says *whose word goes*; an
    inviolable norm says *this one is not up for discussion*. Ranking the law at the top would express the
    first and only approximate the second — someone could later declare a source above it, and nothing
    would object. ⚠ Two conflicting inviolable norms are a contradiction in the domain, not a tie: refused.
    """
    here = norms(g, action)
    if not here:
        return {"stance": None, "by": None, "beat": (), "because": None}

    absolute = [n for n in here if g.attr(n, "force") == INVIOLABLE]
    if absolute:
        stances = {g.attr(n, "stance") for n in absolute}
        if len(stances) > 1:
            raise Undecidable(
                f"{action!r} is both inviolably forbidden and inviolably permitted; that is a "
                f"contradiction in the domain, not something to arbitrate")
        return _won(g, absolute[0], [n for n in here if n is not absolute[0]])

    # Defeasible: the one whose source outranks every other source with a DIFFERENT stance.
    winners = []
    for n in here:
        mine = g.target(n, "source")
        beaten = all(g.attr(o, "stance") == g.attr(n, "stance") or outranks(g, mine, g.target(o, "source"))
                     for o in here if o is not n)
        if beaten:
            winners.append(n)
    stances = {g.attr(n, "stance") for n in winners}
    if not winners or len(stances) > 1:
        # ⚠ Nobody dominates, or two undominated norms disagree. Refuse and name them.
        disputing = sorted({g.attr(g.target(n, "source"), "label") or g.target(n, "source")
                            for n in here})
        raise Undecidable(
            f"norms about {action!r} disagree and their sources are not ranked: "
            f"{', '.join(disputing)}. Say who outranks whom (`discourse.authority`) — arbitrating by "
            f"declaration order would be an undeclared tie-break.")
    return _won(g, winners[0], [n for n in here if n is not winners[0]])


def _won(g: Graph, winner: str, beaten: list) -> dict:
    return {"stance": g.attr(winner, "stance"), "by": winner,
            "beat": tuple(n for n in beaten if g.attr(n, "stance") != g.attr(winner, "stance")),
            "because": g.attr(winner, "because")}


def actions(g: Graph) -> tuple:
    """Every operator any norm speaks about, in declaration order."""
    seen = {}
    for n in norms(g):
        seen.setdefault(g.attr(n, "action"), None)
    return tuple(seen)


def apply(g: Graph, goal: str) -> tuple:
    """Settle every norm and write the surviving prohibitions onto `goal` as ordinary `never` constraints.

    ⭐ **Nothing downstream learns a new concept.** `goal.breached`, `driver.relevance` and `why` see the
    same `never` they always saw, so a defeasible norm costs the planner nothing and the arbitration is
    over before the search begins. Returns the constraints written."""
    out = []
    for action in actions(g):
        verdict = settle(g, action)
        if verdict["stance"] == FORBID:
            c = G.forbid_action(g, goal, function=action,
                                reason=verdict["because"] or f"forbidden by {verdict['by']}")
            g.link(c, "by_norm", verdict["by"])
            out.append(c)
    return tuple(out)


def explain(g: Graph, action: str) -> str:
    """*"Why is selling not excluded?"* — the audit the Python version could not give.

    This is the whole point of the module rather than a nicety: HarneSkills' loss was **auditability**,
    not capability, since their Python got the right answer every time."""
    try:
        v = settle(g, action)
    except Undecidable as e:
        return f"{action}: undecided — {e}"
    if v["stance"] is None:
        return f"{action}: no norm speaks about it"
    who = g.attr(g.target(v["by"], "source"), "label")
    line = f"{action}: {v['stance']} — {who}" + (f" ({v['because']})" if v["because"] else "")
    if g.attr(v["by"], "force") == INVIOLABLE:
        line += ", inviolable"
    for lost in v["beat"]:
        lost_who = g.attr(g.target(lost, "source"), "label")
        line += f"; overriding {lost_who}'s {g.attr(lost, 'stance')}"
    return line


__all__ = ["FORBID", "PERMIT", "STANCES", "DEFEASIBLE", "INVIOLABLE", "FORCES", "Undecidable",
           "declare", "norms", "outranks", "settle", "actions", "apply", "explain"]
