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
    for n in g.nodes:
        if g.kind(n) == "type" and g.attr(n, "name") == name:
            return n
    return None


def schema_of(g: Graph, name: str) -> dict:
    """Edge requirements, including any inherited through `base`."""
    t = find_type(g, name)
    if t is None:
        return {}
    out = dict(schema_of(g, g.attr(t, "base"))) if g.attr(t, "base") else {}
    out.update({g.attr(r, "label"): (g.attr(r, "target_kind"), g.attr(r, "count"))
                for r in g.targets(t, "requires")})
    return out


def attrs_of(g: Graph, name: str) -> dict:
    """Attribute requirements, including inherited ones — the STATE half of a type."""
    t = find_type(g, name)
    if t is None:
        return {}
    out = dict(attrs_of(g, g.attr(t, "base"))) if g.attr(t, "base") else {}
    out.update({g.attr(r, "key"): g.attr(r, "value") for r in g.targets(t, "requires_attr")})
    return out


def violations(g: Graph, node, type_name: str) -> dict:
    """Every way `node` fails to be a `type_name`, as `{label: (expected, actual)}`; empty means valid.

    Returned as data rather than raised, so a caller that wants to *ask* (a selection layer ranking
    candidates) uses the same code as one that wants to *insist* (`check`)."""
    if find_type(g, type_name) is None:
        return {"<type>": (type_name, "undeclared")}
    if node is None:
        return {"<node>": ("a node", "None")}
    bad = {}
    for label, (kind, n) in schema_of(g, type_name).items():
        right_kind = [t for t in g.targets(node, label) if g.kind(t) == kind]
        if len(right_kind) != n:
            bad[label] = (f"{n} of kind {kind}", str(len(right_kind)))
    for key, want in attrs_of(g, type_name).items():
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
    return tuple(sorted(n for n in (g.attr(t, "name") for t in g.nodes if g.kind(t) == "type")
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


def tag(g: Graph, node, type_name: str):
    """Record a validated type on the node, so later callers pass a pointer instead of re-validating."""
    check(g, node, type_name)
    g.put(node, is_a=type_name)
    return node


__all__ = ["TypeViolation", "declare_type", "find_type", "schema_of",
           "attrs_of", "violations", "is_a", "subsumes", "subtypes", "check", "instances", "tag"]
