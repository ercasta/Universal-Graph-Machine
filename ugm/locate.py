"""LOCATE — *what* / *where* / *when*: three questions that needed a verb and no machinery.

**⭐ The shape they share, which is why none of them needed anything built.** `goal` / `ask` / `why` /
`plan` all say a whole proposition and differ only in **force** (`intake.py`). These three have a **gap**
in them, and answering one is not searching for anything: it is **locating an individual in a structure
the world already has**.

| verb | the structure it locates you in | the machinery, which already existed |
|---|---|---|
| `what` | the **subsumption** order — which declared types this satisfies | `types.recognize` (§5i) |
| `where` | the **containment** order — what holds it, at any depth | `path.via` over one named edge (§6h) |
| `when` | the **temporal** order — what it precedes, follows or spans | comparisons on two endpoints |

⚠ **The three are not quite one operation, and saying they are would be too neat.** `what` compares a node
against a population of *types*; `where` and `when` compare it against a population of *nodes*. What is
genuinely common is the part that matters here: each reads an order that is already in the graph, so each
is an ordinary traversal rather than a question anybody has to search for.

**⭐⭐ A reader RECORDS NOTHING, and that is a rule rather than laziness.** §6g: *keep what you cannot
re-derive.* Every answer here is a function of current structure and can be recomputed at any moment for
the cost of a traversal, so storing one would be exactly the drift this codebase keeps re-finding —
`types.tag`'s stamp said `car` after the wheel came off (§5i). Contrast `ask`, which **settles** by default
and is right to: a derivation *ran*, and re-deriving it costs a search. Recomputing beats remembering
precisely when recomputing is cheap, and here it always is.

**⚠ The vocabulary is content; the traversal is machinery — and only the second had to be earned.** §5x's
standing line is that *content shipping with the engine is fine, machinery has to justify itself against
the closed class*. `contains` and `at` / `start` / `end` are conventions, and every one of them is
overridable per question (`by`), so nothing here is wired to a domain word. Transitive reach is the one
piece that **was** a genuine closed-class extension, and it was built in §6h.

**⭐ `where` is the caller `path.via` was written for and did not have.** §6h shipped `via` returning a
set-shaped answer and deliberately left it unwired, because a *reference* that denoted a set would break
`node_at`'s promise of one node. A question is exactly the position with somewhere to put a set: *where is
it?* has no single answer — a parcel is in a box **and** in a warehouse — so the answer is a tuple,
nearest first, and reach stays a predicate everywhere a single node is demanded.

**⚠ Allen's interval relations are a RENDERING of comparisons, not a capability.** §5x measured `when` as
sugar: ordering and interval containment over a comparable value, with before / during / overlaps / meets
reducing to comparisons on two endpoints. `relate` is that reduction written out, and it is thirteen names
for eleven comparisons — it adds no expressive power to what a `type` block could already demand with a
`Rel`. That claim is *checked* rather than asserted: the self-test authors the same judgement as a type
block and requires the two to agree.

**⚠ A point is an interval whose endpoints coincide**, which is what keeps *"when did it happen"* and
*"how long did it last"* one question instead of two. The degenerate cases really are ambiguous — a point
at the start of an interval both `starts` it and is `met_by` it — so `relate` fixes an order of preference
and says which reading wins, rather than pretending the ambiguity is not there.
"""
from __future__ import annotations

from . import path as P
from . import types as TY
from .graph import Graph
from .workbench import reachable

# The conventional vocabulary. Content, not machinery — every one of these is overridable per question.
#
# ⭐ `UPWARD` is written in `path.py`'s own notation, **as the hop is walked from the thing being located**:
# a warehouse `contains` a box, so getting from the box to the warehouse is the backward hop `^contains`.
# A world that writes the relation the other way round (`wheel part_of car`) is asked with `by part_of`,
# forwards, and the same traversal answers. Neither direction is privileged and neither is hard-coded —
# which is what stops `where` from being about containment rather than about reach.
CONTAINMENT = "contains"
UPWARD = "^" + CONTAINMENT
AT, START, END = "at", "start", "end"

VERBS = ("what", "where", "when")

# Allen's thirteen. ⚠ `includes` is Allen's `contains`, renamed here so that the temporal word cannot be
# mistaken for the containment edge `where` walks. Two orders, two vocabularies, one graph.
BEFORE, AFTER, EQUAL = "before", "after", "equal"
MEETS, MET_BY = "meets", "met by"
OVERLAPS, OVERLAPPED_BY = "overlaps", "overlapped by"
STARTS, STARTED_BY = "starts", "started by"
FINISHES, FINISHED_BY = "finishes", "finished by"
DURING, INCLUDES = "during", "includes"


def _name(g: Graph, n) -> str:
    return g.attr(n, "label") or n


# --- what ----------------------------------------------------------------------------------------
def what(g: Graph, node) -> tuple:
    """Every declared type this node satisfies **now**. `types.recognize`, under a verb.

    Multi-type is the ordinary case rather than a complication — a washed car is also a serviced car and a
    car — because the types are independent structural predicates and nothing was ever stored."""
    return TY.recognize(g, node)


# --- where ---------------------------------------------------------------------------------------
def where(g: Graph, node, *, by: str = UPWARD) -> tuple:
    """What holds this node, at any depth, **nearest first**.

    `by` is one hop written as it is walked **from the thing**, `^label` for the backward direction — so
    the default `^contains` climbs out of a container, and `part_of` climbs the other convention. Ancestry,
    part-of and dependency are then the same question asked of a different word, which is the
    domain-neutrality §5x required of the primitive.

    ⚠ One hop, never a path. Reach repeats a *single* edge; a chain of different labels is a fixed
    reference and belongs in `path.py` (§6h: transitive reach applies to ONE named edge)."""
    label, back = (by[1:], True) if by.startswith("^") else (by, False)
    if not label:
        raise P.BadPath(f"{by!r} climbs nothing — write a label, optionally with a leading '^'")
    return P.via(g, node, label, back=back)


# --- when ----------------------------------------------------------------------------------------
def interval(g: Graph, node, *, by: str = AT) -> tuple | None:
    """`(start, end)` for this node, or `None` if nothing here says when it was.

    ⚠ **`None` means the question does not apply, not that the time is unknown-but-existent.** An
    open-world reader must not turn *nothing here says* into *it has no time*, and the two are told apart
    by the caller getting `None` rather than a fabricated endpoint."""
    lo, hi = g.attr(node, START), g.attr(node, END)
    if lo is not None and hi is not None:
        return (lo, hi)
    point = g.attr(node, by)
    return None if point is None else (point, point)


def relate(a: tuple, b: tuple) -> str | None:
    """Allen's relation between two intervals — **eleven comparisons on four endpoints, and nothing else.**

    `None` when the endpoints cannot be compared at all (a string against a number): incomparable is a
    third answer, and inventing an order between two vocabularies would be worse than admitting there is
    none.

    ⚠ The order of the tests is the tie-break for degenerate points, and it is deliberate: containment
    readings (`starts` / `finishes` / `during`) are preferred over adjacency (`meets`), because a point at
    the beginning of an interval is much more usefully described as starting it than as being met by it."""
    (a1, a2), (b1, b2) = a, b
    try:
        if a2 < b1:
            return BEFORE
        if a1 > b2:
            return AFTER
        if a1 == b1 and a2 == b2:
            return EQUAL
        if a1 == b1:
            return STARTS if a2 < b2 else STARTED_BY
        if a2 == b2:
            return FINISHES if a1 > b1 else FINISHED_BY
        if a1 > b1 and a2 < b2:
            return DURING
        if a1 < b1 and a2 > b2:
            return INCLUDES
        if a2 == b1:
            return MEETS
        if a1 == b2:
            return MET_BY
        return OVERLAPS if a1 < b1 else OVERLAPPED_BY
    except TypeError:
        return None


def when(g: Graph, node, *, by: str = AT, under: str = "root") -> tuple:
    """How this node sits in time against everything else that is dated. `((other, relation), …)`.

    Empty when the node itself is undated — there is nothing to relate — which a caller must distinguish
    from *dated and alone in the world*; `interval` is the question that tells them apart.

    ⚠ Enumerated by **traversal from `under`**, never by scanning, for `types.instances`' reason: a scan
    would date the system's own imaginings and offer a workbench copy as something that happened."""
    mine = interval(g, node, by=by)
    if mine is None:
        return ()
    out = []
    for other in reachable(g, under):
        if other == node:
            continue
        theirs = interval(g, other, by=by)
        if theirs is None:
            continue
        rel = relate(mine, theirs)
        if rel is not None:
            out.append((other, rel))
    return tuple(out)


# --- one call, and the rendering the surface hands back ------------------------------------------
def locate(g: Graph, verb: str, node, *, by: str | None = None, under: str = "root") -> tuple:
    """Answer one wh-question about one individual. The verb decides which order is read."""
    if verb == "what":
        return what(g, node)
    if verb == "where":
        return where(g, node, by=by or UPWARD)
    if verb == "when":
        return when(g, node, by=by or AT, under=under)
    raise ValueError(f"{verb!r} is not one of {VERBS}")


def describe(g: Graph, verb: str, node, *, by: str | None = None, under: str = "root") -> str:
    """One line of answer. ⚠ **Says what it found, and says plainly when it found nothing** — an empty
    answer rendered as an empty list reads as a bug at the surface, and *nothing here contains it* is a
    different claim from *it is contained by nothing*, which is the open-world distinction `query.py`
    keeps for verdicts and this keeps for readers."""
    me = _name(g, node)
    found = locate(g, verb, node, by=by, under=under)
    if verb == "what":
        return (f"{me} is: " + ", ".join(found)) if found else f"nothing here says what {me} is"
    if verb == "where":
        word = (by or UPWARD).lstrip("^")
        return ((f"{me} is in: " + ", ".join(_name(g, n) for n in found) + "   (nearest first)")
                if found else f"nothing here holds {me}, by {word}")
    span = interval(g, node, by=by or AT)
    if span is None:
        return f"nothing here says when {me} was"
    at = f"{span[0]}" if span[0] == span[1] else f"{span[0]}-{span[1]}"
    return f"{me} at {at}" + ("".join(f"; {rel} {_name(g, n)}" for n, rel in found) if found
                              else "; nothing else here is dated")


__all__ = ["CONTAINMENT", "UPWARD", "AT", "START", "END", "VERBS", "BEFORE", "AFTER", "EQUAL", "MEETS", "MET_BY",
           "OVERLAPS", "OVERLAPPED_BY", "STARTS", "STARTED_BY", "FINISHES", "FINISHED_BY", "DURING",
           "INCLUDES", "what", "where", "interval", "relate", "when", "locate", "describe"]
