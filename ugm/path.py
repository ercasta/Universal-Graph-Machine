"""PATHS — the one way to refer to something that is not directly at hand.

**This language already existed, three times, undeclared.** `driver.role_node` resolved `c.right` and
`c.child[2]` against the world; `intake._constrain` split `b.clear` by hand; `establishes` emitted dotted
roles and nothing said what a dotted role *was*. Three copies of a grammar that was never written down is
the shape a missing module makes, and the cost was that no *other* part of the surface could refer to
anything more than one hop away — which is exactly why type schemas were one level deep.

**The grammar, and it is the whole grammar:**

```
path := seg ('.' seg)*
seg  := ['^'] label ('[' int ']')?
```

* `car.wheel` — every hop is a **named edge**, walked in traversal order, left to right.
* `car.wheel[1]` — an **index** into that label's ordered targets. Negative indices count from the end,
  so `car.wheel[-1]` is the last one. The substrate has ordered targets natively (`Graph.at`), so this is
  addressing, not searching.
* `wheel.^has` — a **backward** hop, along an incoming edge (`Graph.sources`). ⚠ It resolves only when
  **exactly one** node points that way; two candidates yield nothing rather than a guess. That is
  `intake.resolve`'s stance about names, applied to references: *never identify by ambiguity*.

**⭐ There is no depth limit and never was one.** A hop is a hop; nothing here counts them.

## ⭐⭐ The last segment is an attribute or a node according to WHAT THE POSITION DEMANDS

`car.wheel[1].pressure` denotes a *value*; `car.wheel[1]` denotes a *node*. Both are written the same way,
and the reader knows which because the position it sits in demands one or the other — `==` compares values,
`is` compares identities. So `value_at` walks every hop but the last and reads the last as an **attribute**,
while `node_at` walks them all as **edges**.

⚠ **This is type-directed resolution, not a guess about the graph, and the difference matters here.** The
tempting version — "follow the edge if there is one, else read the attribute" — would make the meaning of a
written path depend on what the world happens to contain at the moment it is read, so adding an edge could
silently change what an old declaration said. That is the drift class this codebase keeps re-finding
(`types.tag`, the kind index). Nothing in this module ever looks at the graph to decide what a path *means*;
it looks at the graph only to find what the path *denotes*.

**Attributes and edges stay distinct** for the same reason `graph.py` keeps `Ref` distinct from an edge: an
edge is a relation the graph asserts, an attribute is a value a node holds. A reference language that blurred
them would be a labelling error, not a convenience.

## Writing a reference versus writing a value

Any bare word is a legal one-hop path, so on the **left** of a comparison `weight` means *this node's
weight*. On the **right**, a bare word is a **literal** — `colour == red` compares against the string
`"red"`, not against something reached by an edge called `red`. To mean a reference on the right, write a
path with a hop in it (`colour == body.colour`). Ambiguity is resolved by making the author say which,
never by the parser preferring one; `is_reference` is where that rule lives, in one place, so every block
of the surface applies it identically.
"""
from __future__ import annotations

import re
from typing import NamedTuple

from .graph import Graph

# ⚠ The label charset is CLOSED, and it was not at first. `[^.\[\]^]+` accepted anything, so `contains*`
# and `contains+` parsed happily — as a label *literally named* `contains*`, which matches nothing, silently.
# Someone writing that is reaching for transitive closure (see `REPETITION` below), and the grammar owes
# them an answer rather than a label that will never match.
_SEG = re.compile(r"(\^?)([A-Za-z_][A-Za-z0-9_-]*)(?:\[(-?\d+)\])?$")
_REPETITION = ("*", "+", "?", "{", "}", "(", ")", "|")
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?$")
_WORDS = ("true", "false", "null", "none")


class BadPath(Exception):
    """A reference that cannot be read. Loud, like every other refusal at this border."""


class Hop(NamedTuple):
    label: str
    index: int | None = None
    back: bool = False


class Path(NamedTuple):
    """Parsed hops, plus the surface they were written as — kept so a message or a round trip can quote
    the author's own words rather than a reconstruction of them."""
    hops: tuple
    text: str

    def __str__(self) -> str:
        return self.text


def parse(text: str) -> Path:
    """`"car.wheel[1].pressure"` → a `Path`. Raises `BadPath` on anything the grammar does not cover."""
    if not text or not text.strip():
        raise BadPath("an empty reference refers to nothing")
    hops = []
    for seg in text.split("."):
        m = _SEG.fullmatch(seg)
        if m is None:
            if any(ch in seg for ch in _REPETITION):
                raise BadPath(
                    f"cannot read {seg!r} in {text!r} — a path is a FIXED sequence of hops and has "
                    f"no repetition operator. Transitive reach EXISTS, but only as a PREDICATE: write "
                    f"`{seg.rstrip(''.join(_REPETITION))}+` in a link position (a goal or a query), where "
                    f"it asks *is this reachable at any depth*. It cannot appear in a reference, because "
                    f"a reference must denote ONE node and reach denotes a set — see `path.reaches`")
            raise BadPath(f"cannot read {seg!r} in {text!r} — a segment is "
                          f"[^]label or [^]label[index], with a label of letters, digits, _ and -")
        hops.append(Hop(m.group(2), None if m.group(3) is None else int(m.group(3)), bool(m.group(1))))
    return Path(tuple(hops), text)


# --- transitive reach: the one genuine closed-class gap this project measured -------------------------
#
# ⭐⭐ **`closed_class_rechallenged.md` probed five relational forms and found four pure sugar — causation,
# quantification's open case, force/level, identity/merge — with TRANSITIVITY the one that needed a real
# engine extension.** the design notes arrived at the same single item from a completely different direction, by
# asking what the word *where* needs: a parcel inside a box inside a warehouse is not reachable by a
# fixed-depth type, a goal's link constraint reads false because it is not a *direct* target, and this
# grammar has no repetition operator. Two independent routes to one item is the strongest evidence
# available here that it is a genuine closed-class member rather than a convenience.
#
# ⚠⚠ **PREDICATE POSITION ONLY, and that restriction is the whole design.** *Is X reachable from Y?* stays
# boolean and single-valued, so it breaks no contract here. A *reference* — `a.contains+.label` — would
# denote a **set**, which breaks `node_at`'s promise to return one node or `None` and every caller that
# assumes it. `parse` therefore still refuses `+` in a path, and points at this instead.

CLOSURE = "+"


def parse_link(text: str) -> tuple:
    """A relation in a **link position**: `"contains"` → `("contains", False)`, `"contains+"` → transitive.

    ⚠ Deliberately not part of `parse`. A path is a reference and this is a predicate; letting one grammar
    produce both is how `node_at` would end up sometimes returning a set."""
    if text.endswith(CLOSURE):
        label = text[:-1]
        if not label:
            raise BadPath(f"{text!r} is a repetition of nothing — write a label before the {CLOSURE!r}")
        if _SEG.fullmatch(label) is None or "." in label:
            raise BadPath(f"cannot read {label!r} in {text!r} — transitive reach applies to ONE named "
                          f"edge, not to a path. Write `contains+`, never `a.contains+`")
        return label, True
    if _SEG.fullmatch(text) is None:
        raise BadPath(f"cannot read {text!r} as a relation — a label of letters, digits, _ and -, "
                      f"optionally followed by {CLOSURE!r} for reach at any depth")
    return text, False


def reaches(g: Graph, start, label: str, dst, *, back: bool = False) -> bool:
    """Is `dst` reachable from `start` by **one or more** `label` hops?

    ⚠ **One or more, never zero** — a node does not contain itself. Reflexivity would make every containment
    goal trivially true of its own subject, which is the kind of vacuity this codebase keeps catching.

    ⚠ Cycle-safe, and it has to be: containment is *supposed* to be acyclic and a graph does not enforce
    that, so a mis-authored world would hang the planner. The discipline is `types._target_ok`'s — carry
    what has already been visited — and it is why this returns rather than recurses."""
    if start is None or dst is None:
        return False
    seen, frontier = {start: None}, [start]
    while frontier:
        here = frontier.pop(0)                       # breadth-first: nearest first, and deterministic
        for nxt in (g.sources(here, label) if back else g.targets(here, label)):
            if nxt == dst:
                return True
            if nxt not in seen:
                seen[nxt] = None
                frontier.append(nxt)
    return False


def via(g: Graph, start, label: str, *, back: bool = False) -> tuple:
    """Everything reachable from `start` by one or more `label` hops, **nearest first**.

    ⚠ Offered for a caller that has somewhere to put a set — `where is it kept?` answered as a list. It is
    **not** wired into any path, and must not be: a reference that denoted a set would break `node_at`.
    Ordered breadth-first rather than returned as a `set`, per `search-was-irreproducible-set-tiebreak`."""
    seen, out, frontier = {start: None}, [], [start]
    while frontier:
        here = frontier.pop(0)
        for nxt in (g.sources(here, label) if back else g.targets(here, label)):
            if nxt not in seen:
                seen[nxt] = None
                out.append(nxt)
                frontier.append(nxt)
    return tuple(out)


def render(p: Path) -> str:
    """Hops back to surface — the round trip a model reads to check itself."""
    return ".".join(("^" if h.back else "") + h.label + ("" if h.index is None else f"[{h.index}]")
                    for h in p.hops)


def is_reference(token: str) -> bool:
    """Does this token, in a position where either is allowed, mean a **reference** rather than a literal?

    ⚠ Only a token with a hop in it does. See the module docstring: a bare word on the right of a
    comparison is a value, and an author who means a reference says so with a dot."""
    if not token or token.startswith('"') or token in _WORDS or _NUMBER.fullmatch(token):
        return False
    return "." in token or "[" in token or token.startswith("^")


def _step(g: Graph, node, hop: Hop):
    if node is None:
        return None
    if hop.back:
        srcs = g.sources(node, hop.label)
        return srcs[0] if len(srcs) == 1 else None      # ⚠ never guess between two
    return g.target(node, hop.label) if hop.index is None else g.at(node, hop.label, hop.index)


def node_at(g: Graph, start, path: Path, upto: int | None = None):
    """The **node** a path reaches from `start`, or `None` if any hop misses. Every segment is an edge."""
    node = start
    for hop in path.hops[:upto]:
        node = _step(g, node, hop)
        if node is None:
            return None
    return node


def value_at(g: Graph, start, path: Path):
    """The **value** a path reaches: every hop but the last is an edge, the last is an attribute.

    `None` when the holder cannot be reached — indistinguishable from an attribute that is genuinely
    `None`, deliberately, because a constraint about a value that is not there and one about a value that
    is `None` both fail, and inventing a third answer would only move the decision somewhere worse."""
    holder = node_at(g, start, path, upto=-1)
    return None if holder is None else g.attr(holder, path.hops[-1].label)


def split_base(text: str) -> tuple:
    """`"c.right.value"` → `("c", Path)`; `"c"` → `("c", None)`.

    For a surface whose first segment names something OTHER than a node in the graph — a **parameter** in
    `driver.establishes`, a **role** in a method step, a **label** in a goal — the base is resolved by that
    caller and the rest is an ordinary path from whatever it resolved to. That split is what lets one
    reference language serve blocks whose starting points have nothing in common."""
    base, _, rest = text.partition(".")
    if not base:
        raise BadPath(f"{text!r} starts with a dot; a reference needs something to start from")
    return base, (parse(rest) if rest else None)


def resolve(g: Graph, start, text: str, *, want: str = "node"):
    """Parse and follow in one call. `want` is `"node"` or `"value"` — the position's demand, which is
    what decides how the last segment is read (see the module docstring)."""
    p = parse(text)
    return node_at(g, start, p) if want == "node" else value_at(g, start, p)


__all__ = ["BadPath", "Hop", "Path", "CLOSURE", "parse", "parse_link", "render",
           "is_reference", "reaches", "via", "node_at", "value_at", "split_base", "resolve"]
