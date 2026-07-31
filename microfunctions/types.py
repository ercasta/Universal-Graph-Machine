"""TYPES — a type is a subgraph schema, and a schema is ordinary graph data.

`north_star.md` §5c: *a `car` is a chunk with a body and four wheels.* Named edges make this read directly
off the graph — a requirement is "this label, this many targets, of this kind."

**Matching lives here now, and only here.** Checking a chunk against a schema IS a graph pattern match.
What changed is its job: it validates ONE argument at ONE call site, bounded and terminating, instead of
deciding what fires across the whole graph. Say it that way — "matching was eliminated" is wrong and easy
to disprove. Prior art sits exactly here: SHACL shapes, and Minsky's frames.

**Types are data, not Python classes** — a `type` node with `requires` edges. A KB can author one, a
microfunction can read one, and a microfunction can write one.
"""
from __future__ import annotations

from .graph import Graph


class TypeViolation(Exception):
    """Refused at the boundary, loudly, with expected-versus-actual — never a half-executed call."""


def declare_type(g: Graph, name: str, requires: dict | None = None,
                 attrs: dict | None = None, base: str | None = None) -> str:
    """`requires` maps an edge label to `(target_kind, exact_count)`; `attrs` requires attribute values;
    `base` inherits another type's requirements.

        declare_type(g, "car", {"body": ("body", 1), "wheel": ("wheel", 4)})
        declare_type(g, "serviced_car", base="car", attrs={"serviced": True})

    **A type is a schema over a subgraph — structure AND attributes** — the way a Pydantic schema
    constrains a frame. That is what removes any need to represent mutation explicitly: `service(c: car)
    -> serviced_car` is a **cast**, and whatever it changes in the graph is merely how the cast is
    achieved. Nothing records that a mutation happened, because nothing needs to — a node either satisfies
    the stronger schema or it does not, checkable at any moment rather than being a historical claim.
    Precondition and effect reduce to parameter type and return type, so `plan.py` chains casts.
    """
    t = g.mint("type", name=name)
    if base:
        g.put(t, base=base)
    for label, (kind, n) in (requires or {}).items():
        g.link(t, "requires", g.mint("requires", label=label, target_kind=kind, count=n))
    for key, value in (attrs or {}).items():
        g.link(t, "requires_attr", g.mint("requires_attr", key=key, value=value))
    return t


def find_type(g: Graph, name: str):
    """⚠ Reached about four times per `violations` call (here, `schema_of`, `attrs_of`, plus a hop per
    `base`), so this being a scan of every node in the graph was the dominant cost of planning — see
    `Graph.of_kind`, which is what makes it a lookup over declared types instead."""
    for n in g.of_kind("type"):
        if g.attr(n, "name") == name:
            return n
    return None


def _schema_at(g: Graph, t) -> dict:
    """`schema_of` given the type NODE — so a caller that already resolved the name does not resolve it
    again. See `violations`, which used to resolve the same name four times over."""
    if t is None:
        return {}
    base = g.attr(t, "base")
    out = _schema_at(g, find_type(g, base)) if base else {}
    out.update({g.attr(r, "label"): (g.attr(r, "target_kind"), g.attr(r, "count"))
                for r in g.targets(t, "requires")})
    return out


def _attrs_at(g: Graph, t) -> dict:
    if t is None:
        return {}
    base = g.attr(t, "base")
    out = _attrs_at(g, find_type(g, base)) if base else {}
    out.update({g.attr(r, "key"): g.attr(r, "value") for r in g.targets(t, "requires_attr")})
    return out


def schema_of(g: Graph, name: str) -> dict:
    """Edge requirements, including any inherited through `base`."""
    return _schema_at(g, find_type(g, name))


def attrs_of(g: Graph, name: str) -> dict:
    """Attribute requirements, including inherited ones — the STATE half of a type."""
    return _attrs_at(g, find_type(g, name))


def violations(g: Graph, node, type_name: str) -> dict:
    """Every way `node` fails to be a `type_name`, as `{label: (expected, actual)}`; empty means valid.

    Returned as data rather than raised, so a caller that wants to *ask* (a selection layer ranking
    candidates) uses the same code as one that wants to *insist* (`check`).

    ⚠ The name is resolved **once**. It used to be resolved four times — here, inside `schema_of`, inside
    `attrs_of`, and again per `base` hop — which was invisible while `find_type` looked cheap and dominated
    planning once it was measured."""
    t = find_type(g, type_name)
    if t is None:
        return {"<type>": (type_name, "undeclared")}
    if node is None:
        return {"<node>": ("a node", "None")}
    bad = {}
    for label, (kind, n) in _schema_at(g, t).items():
        right_kind = [x for x in g.targets(node, label) if g.kind(x) == kind]
        if len(right_kind) != n:
            bad[label] = (f"{n} of kind {kind}", str(len(right_kind)))
    for key, want in _attrs_at(g, t).items():
        got = g.attr(node, key)
        if got != want:
            bad[f"@{key}"] = (repr(want), repr(got))
    return bad


def is_a(g: Graph, node, type_name: str) -> bool:
    return not violations(g, node, type_name)


def subsumes(g: Graph, general: str, specific: str) -> bool:
    """Is every `specific` also a `general`? True when `specific`'s constraints are a superset.

    **Subtyping here is structural, not nominal**, and falls out of what a type already is. A type is a
    set of constraints on a subgraph; a *supertype* relaxes them and a *subtype* tightens them. So
    `washed_car` (body, 4 wheels, serviced, washed) is a subtype of `serviced_car` (body, 4 wheels,
    serviced) because it demands everything that one demands and more — and `declare_type(..., base=...)`
    is merely a convenient way to write that, never the thing that makes it true. Two types declared
    independently stand in the same relation if their constraints do.

    This matters most for planning: a function returning a `washed_car` genuinely satisfies a goal wanting
    a `serviced_car`, and a planner that compared type *names* would miss it."""
    if general == specific:
        return True
    gs, ss = schema_of(g, general), schema_of(g, specific)
    ga, sa = attrs_of(g, general), attrs_of(g, specific)
    if not gs and not ga:
        return False                       # an undeclared or empty "general" subsumes nothing meaningful
    return (all(ss.get(k) == v for k, v in gs.items())
            and all(sa.get(k) == v for k, v in ga.items()))


def subtypes(g: Graph, general: str) -> tuple:
    """Every declared type that is a subtype of `general`, itself included."""
    return tuple(sorted(n for n in (g.attr(t, "name") for t in g.of_kind("type"))
                        if subsumes(g, general, n)))


def check(g: Graph, node, type_name: str) -> None:
    bad = violations(g, node, type_name)
    if bad:
        raise TypeViolation(f"{node} is not a {type_name}: {bad}")


def instances(g: Graph, type_name: str, under: str = "root") -> tuple:
    """Every node under `under` satisfying the schema — **enumerated by traversal, never by scanning.**

    ⚠ **This used to scan every node in the graph and filter out workbench copies, and that filter was a
    mistake worth recording.** Copies are ordinary nodes, so an unfiltered scan would find the system's own
    imaginings and offer them as candidate arguments — planning about the products of planning. The first
    fix was an exclusion parameter plus a test guarding it. The real fix is not to scan: enumerate what is
    reachable from a root, and workbench copies are *structurally* unreachable, because nothing in the real
    graph points at a copy (only a mapping does, via `image`) and nothing points at a workbench (a workbench
    points at its subject). No filter, no marker, no test — the isolation was already there.

    Passing a workbench copy as `under` enumerates inside that workbench, by the same mechanism and with no
    special case.

    **The discipline this relies on: real things hang off `root`.** That is what makes "the real world" a
    well-defined region rather than "whatever happens to be in the dict", and it is what the substrate's
    single starting node was always for."""
    from .workbench import reachable
    return tuple(n for n in reachable(g, under) if is_a(g, n, type_name))


def type_names(g: Graph) -> tuple:
    """Every declared type that constrains anything. A type with no requirements at all is satisfied by
    everything, so it is not recognition — the same stance `subsumes` already takes."""
    return tuple(sorted(
        n for n in (g.attr(t, "name") for t in g.of_kind("type"))
        if schema_of(g, n) or attrs_of(g, n)))


def recognize(g: Graph, node) -> tuple:
    """⭐ **What IS this?** — the bottom-up direction, which was the one missing from this module.

    Every entry point here was top-down: `is_a` asks about a *named* type, `instances` enumerates for a
    *named* type. Nothing asked what a node turns out to be. That question is five lines, because typing was
    already structural and dynamic; only the direction was absent.

    Two properties fall out rather than needing mechanism, which is the evidence the shape is right:
    **multi-type** (a washed car is also a serviced car and a car — independent structural predicates, so
    of course), and **de-recognition** (remove a wheel and it stops being a car, with nothing to invalidate
    because nothing was stored)."""
    if node is None or g.kind(node) == "type":
        return ()
    return tuple(name for name in type_names(g) if is_a(g, node, name))


def tag(g: Graph, node, type_name: str):
    """Validate loudly, and leave a **hint** for later readers.

    ⚠ The hint is not the answer, and treating it as one was a live defect. `is_a` is computed from current
    structure; a stamped attribute is a claim about the past. Remove a wheel from a tagged car and the
    stamp still says `car` while the structure says otherwise — measured, and `application.generalise` was
    reading it as authoritative, so a learned function took its parameter name and declared type from a
    class the node no longer belonged to.

    **The rule: cache the candidate, re-validate on read.** The cost is the *search over all types*
    (linear in how many are declared); one check against a *named* type is ~25µs, so re-validating is
    nearly free and drift becomes structurally impossible rather than merely unlikely. Read it through
    `tagged_as`, never as a raw attribute."""
    check(g, node, type_name)
    g.put(node, is_a=type_name)
    return node


def tagged_as(g: Graph, node):
    """The node's hinted type — **only if it still holds**. `None` when it never had one or has drifted.

    This is the sanctioned reader. `g.attr(node, "is_a")` is a hint about what to check, not a fact."""
    hint = g.attr(node, "is_a")
    if hint is None:
        return None
    return hint if is_a(g, node, hint) else None


__all__ = ["TypeViolation", "declare_type", "find_type", "schema_of",
           "attrs_of", "violations", "is_a", "subsumes", "subtypes", "check", "instances",
           "type_names", "recognize", "tag", "tagged_as"]
