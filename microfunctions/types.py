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

from typing import NamedTuple

from . import path as P
from . import native as N
from .graph import Graph


class TypeViolation(Exception):
    """Refused at the boundary, loudly, with expected-versus-actual — never a half-executed call."""


UNBOUNDED = None            # a count with no upper limit; `hi=None` reads as "as many as you like"


class Req(NamedTuple):
    """What a type demands of ONE edge label: what the targets must be, and how many there must be.

    ⭐ **`kind` and `type` are independent, and only `type` recurses.** A `kind` is what a node was minted
    as — a substrate fact, one level deep by construction, and cheap. A `type` is a whole schema, checked
    the same way this node is being checked, to whatever depth the declarations go. Keeping both means the
    cheap check stays cheap and the deep one is asked for on purpose; collapsing them into "the name means
    a type if one is declared, else a kind" was considered and rejected, because declaring a type later
    would then silently change what an older declaration demanded."""
    kind: str | None = None
    type: str | None = None
    lo: int = 0
    hi: int | None = UNBOUNDED


class AttrReq(NamedTuple):
    """What a type demands of one attribute — the STATE half. `op` is one of `== != < <= > >= between`."""
    op: str = "=="
    value: object = None
    hi: object = None                    # only `between` uses it


class Rel(NamedTuple):
    """⭐⭐ A demand relating **two places inside the subgraph** — the thing a flat schema could not say.

    `Rel("wheel[0].pressure", "==", "wheel[1].pressure")` is a constraint no per-label requirement can
    express, because it is not about a label at all: it is about two nodes reached from the same subject
    agreeing. Both sides are `path.py` references resolved from the node being checked, so depth is
    unbounded here for the same reason it is unbounded there — nothing counts hops.

    `right_is_path` is what distinguishes `pressure > spare.pressure` from `pressure > 30`, and it is
    recorded rather than inferred so that the meaning of a stored declaration can never drift.

    ⚠ **`is` / `is not` compare node IDENTITY; every other operator compares VALUES.** That is the
    position-demands-it rule from `path.py`, and it is the only thing that decides whether the last segment
    of each side is walked as an edge or read as an attribute."""
    left: str = ""
    op: str = "=="
    right: object = None
    right_is_path: bool = True


VALUE_OPS = ("==", "!=", "<", "<=", ">", ">=")
IDENTITY_OPS = ("is", "is not")


def _as_req(spec) -> Req:
    """Accepts what callers already write, and what the wider forms need.

    `("wheel", 4)` is the original two-tuple and still means *four targets of kind wheel* — every existing
    declaration in the codebase is written that way, and none of them changes meaning."""
    if isinstance(spec, Req):
        return spec
    if isinstance(spec, dict):
        return Req(**spec)
    if isinstance(spec, int):
        return Req(lo=spec, hi=spec)
    kind, n = spec
    return Req(kind=kind, lo=n, hi=n)


def _as_attr_req(spec) -> AttrReq:
    return spec if isinstance(spec, AttrReq) else AttrReq("==", spec)


def _as_rel(spec) -> Rel:
    if isinstance(spec, Rel):
        return spec
    left, op, right = spec
    return Rel(left, op, right, P.is_reference(str(right)) or op in IDENTITY_OPS)


# --- authoring: one requirement at a time -----------------------------------------------------------
# ⭐ `declare_type` is now built out of these rather than the other way round, because the CNL surface
# authors a type line by line and had no way in short of assembling the whole dict first. A block that
# refuses halfway must leave nothing behind, and `intake.read` already gets that from the journal.

def require_edge(g: Graph, t: str, label: str, spec) -> str:
    r = _as_req(spec)
    node = g.mint("requires", label=label, target_kind=r.kind, target_type=r.type, lo=r.lo, hi=r.hi)
    g.link(t, "requires", node)
    return node


def require_value(g: Graph, t: str, key: str, spec) -> str:
    a = _as_attr_req(spec)
    node = g.mint("requires_attr", key=key, op=a.op, value=a.value, hi=a.hi)
    g.link(t, "requires_attr", node)
    return node


def require_relation(g: Graph, t: str, spec) -> str:
    r = _as_rel(spec)
    node = g.mint("requires_rel", left=r.left, op=r.op, right=r.right, right_is_path=r.right_is_path)
    g.link(t, "requires_rel", node)
    return node


def declare_type(g: Graph, name: str, requires: dict | None = None,
                 attrs: dict | None = None, base: str | None = None,
                 relates=None) -> str:
    """`requires` maps an edge label to what that label must hold; `attrs` constrains attribute values;
    `relates` states demands relating two places inside the subgraph; `base` inherits another type.

        declare_type(g, "car", {"body": ("body", 1), "wheel": ("wheel", 4)})
        declare_type(g, "serviced_car", base="car", attrs={"serviced": True})

        declare_type(g, "car", {"wheel": Req(type="wheel", lo=4, hi=4)},   # ← RECURSIVE: each target
                     attrs={"weight": AttrReq("between", 800, 2000)},      #   is itself checked
                     relates=[Rel("wheel[0].pressure", "==", "wheel[1].pressure")])

    **A type is a schema over a subgraph — structure AND attributes** — the way a Pydantic schema
    constrains a frame. That is what removes any need to represent mutation explicitly: `service(c: car)
    -> serviced_car` is a **cast**, and whatever it changes in the graph is merely how the cast is
    achieved. Nothing records that a mutation happened, because nothing needs to — a node either satisfies
    the stronger schema or it does not, checkable at any moment rather than being a historical claim.
    Precondition and effect reduce to parameter type and return type, so `plan.py` chains casts.

    **⚠ Schemas used to be ONE LEVEL DEEP, and that limit is gone.** `("wheel", 4)` demanded four targets
    of graph *kind* `wheel` and said nothing about what a wheel is, so "on a block which is on a block" had
    no schema and a magnitude like height had to be smuggled in as an attribute. `Req(type=…)` recurses
    into the target's own schema, `Rel` relates two places within one subgraph, and both are ordinary graph
    data like everything else here — a KB can author one, a microfunction can read one and write one."""
    t = g.mint("type", name=name)
    if base:
        g.put(t, base=base)
    for label, spec in (requires or {}).items():
        require_edge(g, t, label, spec)
    for key, spec in (attrs or {}).items():
        require_value(g, t, key, spec)
    for spec in (relates or ()):
        require_relation(g, t, spec)
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
    out.update({g.attr(r, "label"): Req(g.attr(r, "target_kind"), g.attr(r, "target_type"),
                                        g.attr(r, "lo"), g.attr(r, "hi"))
                for r in g.targets(t, "requires")})
    return out


def _attrs_at(g: Graph, t) -> dict:
    if t is None:
        return {}
    base = g.attr(t, "base")
    out = _attrs_at(g, find_type(g, base)) if base else {}
    out.update({g.attr(r, "key"): AttrReq(g.attr(r, "op"), g.attr(r, "value"), g.attr(r, "hi"))
                for r in g.targets(t, "requires_attr")})
    return out


def _rels_at(g: Graph, t) -> tuple:
    """⚠ Relations ACCUMULATE where the other two OVERRIDE, and the asymmetry is not an oversight. A
    subtype restating `weight` replaces the inherited demand about weight, because they are two claims
    about one slot and the nearer one wins. Two relations are two independent claims about the subgraph
    with no slot to collide over, so a subtype adds to what its base already demanded."""
    if t is None:
        return ()
    base = g.attr(t, "base")
    out = list(_rels_at(g, find_type(g, base))) if base else []
    for r in g.targets(t, "requires_rel"):
        rel = Rel(g.attr(r, "left"), g.attr(r, "op"), g.attr(r, "right"), g.attr(r, "right_is_path"))
        if rel not in out:
            out.append(rel)
    return tuple(out)


def schema_of(g: Graph, name: str) -> dict:
    """Edge requirements as `{label: Req}`, including any inherited through `base`."""
    return _schema_at(g, find_type(g, name))


def attrs_of(g: Graph, name: str) -> dict:
    """Attribute requirements as `{key: AttrReq}`, inherited ones included — the STATE half of a type."""
    return _attrs_at(g, find_type(g, name))


def rels_of(g: Graph, name: str) -> tuple:
    """Demands relating two places inside the subgraph, inherited ones included."""
    return _rels_at(g, find_type(g, name))


def requirements(g: Graph, type_name: str):
    """A type's demands, gathered once: `(schema, attrs)`, or `None` if it is undeclared.

    **⭐ For a caller testing MANY nodes against ONE type — which is what candidate enumeration is — this
    is the loop-invariant half of `violations`.** Resolving the name, walking the `base` chain and building
    the two requirement dicts depends only on the type, yet it was being redone per candidate:
    `driver.proposals` over a world with 200 nodes that bind to nothing did it 1,025 times per enumeration.

    ⚠ **Not a cache, and deliberately not one.** Nothing is stored, so nothing can drift — this is the same
    answer `schema_of`/`attrs_of` give, computed at the point where it is still valid to hoist. A caller
    that mutates a type mid-loop must re-ask, which is the honest contract; a cache would have to guess."""
    t = find_type(g, type_name)
    return None if t is None else (_schema_at(g, t), _attrs_at(g, t), _rels_at(g, t))


def compare(op, got, want, hi=None) -> bool:
    """One comparison, total. **THE comparator** — `goal.holds`, `criterion._holds` and every schema check
    share it, so `>=` cannot come to mean different things in a `type` block and in a goal.

    ⚠ It was private (`_holds`) while only schemas compared values. The moment the comparison operators
    were widened past `type`, a second implementation was the obvious thing to write and would have been
    the drift this codebase keeps finding — three parsers for one proposition grammar, most recently. ⚠ Returns `False` where Python would raise — comparing a string to a number
    is a failed constraint, never a crash, because a schema is checked against whatever the world happens
    to hold and the world is not obliged to cooperate."""
    try:
        if op == "==":
            return got == want
        if op == "!=":
            return got != want
        if op == "between":
            return want <= got <= hi
        if op == "<":
            return got < want
        if op == "<=":
            return got <= want
        if op == ">":
            return got > want
        if op == ">=":
            return got >= want
    except TypeError:
        return False
    return False                                   # an operator nothing declared: refuse, never assume


def _phrase(r: Req) -> str:
    what = " ".join(x for x in ((f"of kind {r.kind}" if r.kind else ""),
                                (f"that is a {r.type}" if r.type else "")) if x)
    if r.hi is None:
        how = f"at least {r.lo}"
    elif r.lo == r.hi:
        how = str(r.lo)
    else:
        how = f"{r.lo} to {r.hi}"
    return f"{how} {what}".strip()


def _attr_phrase(a: AttrReq) -> str:
    return f"between {a.value!r} and {a.hi!r}" if a.op == "between" else f"{a.op} {a.value!r}"


def _rel_sides(g: Graph, node, rel: Rel):
    """Both operands of a relation, resolved from `node`. `is`/`is not` want NODES, everything else wants
    VALUES — the position deciding how the last segment of each path is read (`path.py`)."""
    want = "node" if rel.op in IDENTITY_OPS else "value"
    try:
        left = P.resolve(g, node, rel.left, want=want)
        right = (P.resolve(g, node, str(rel.right), want=want) if rel.right_is_path else rel.right)
    except P.BadPath:
        return None, None, False
    return left, right, True


def _rel_holds(g: Graph, node, rel: Rel) -> bool:
    left, right, readable = _rel_sides(g, node, rel)
    if not readable:
        return False
    if rel.op == "is":
        return left is not None and left == right
    if rel.op == "is not":
        return left is not None and right is not None and left != right
    return compare(rel.op, left, right)


def _target_ok(g: Graph, x, req: Req, sub, seen: frozenset) -> bool:
    if req.kind is not None and g.kind(x) != req.kind:
        return False
    if req.type is None:
        return True
    key = (x, req.type)
    if key in seen:
        # ⚠ **A cycle in the DATA is satisfied, not failed.** A `person` whose `friend` must be a `person`
        # is a perfectly ordinary declaration, and two people who are friends make the check re-enter. The
        # coinductive answer — assume it holds while proving it holds — is the only one that terminates
        # without banning recursive types outright, and it is what every structural type system does.
        return True
    return not fails(g, x, sub, seen | {key})


def _matching(g: Graph, node, label: str, req: Req, sub, seen: frozenset) -> tuple:
    """The targets of `label` that SATISFY this requirement — the thing a count is a count *of*.

    ⭐ Extracted so `fails` and `offenders` cannot disagree: one counts these, the other names them
    (§5m's *one implementation and nothing that can disagree*, which is the structural answer rather than
    a guarded one). Order is `g.targets`, which is insertion order — never a `set`."""
    return tuple(x for x in g.targets(node, label) if _target_ok(g, x, req, sub, seen))


def offenders(g: Graph, node, type_name: str) -> dict:
    """⭐⭐ **WHICH targets make this node fail — the names behind the count.**

    `{label: (node, …)}`, empty when the node satisfies the type. This is the *planning* half of a
    universal, and without it a universal constraint is a yes/no: `plural_step.md` §1 measured that even a
    **singular** action that would close `d is a tidied_dir` scored band 1, because `goal.unmet` could say
    *that* the constraint was false and never *which members* made it so — §5d's founding defect
    (*"a goal that can only answer yes/no forces blind search"*) reappearing one level up.

    ⚠⚠ **ONLY the too-many case has witnesses, and the asymmetry is the open world, not an omission.**
    `has no file each a ungone_file` fails because *these* files are un-gone, and each of them is a thing
    an action could change. `has 4 wheel` failing with three wheels has **no witness at all** — the missing
    wheel does not exist, so there is nothing to point at. That case is already served, from the other
    side, by `relevance`'s existential branch: *something of this type must exist* is answered by an
    operator that MINTS one. Between them the two directions are covered; conflating them would mean
    inventing a node to blame.

    ⚠ **Derived, never stored.** §5f faced this exact choice for expectations and refused to materialise
    them, because the driver imagines hundreds of frames and a node per step is a node per step. The same
    reasoning applies with more force here, and §5i is the other half of it: a stored witness list is a
    claim about the past, and this is a question about now."""
    reqs = requirements(g, type_name)
    if reqs is None or node is None:
        return {}
    schema, _attrs, _rels = reqs
    out = {}
    for label, req in schema.items():
        if req.hi is None:
            continue                                 # no upper bound: too many is not a way to fail
        sub = requirements(g, req.type) if req.type is not None else None
        if req.type is not None and sub is None:
            continue                                 # undeclared target type: `fails` reports it, we cannot
        hits = _matching(g, node, label, req, sub, frozenset())
        if len(hits) > req.hi:
            out[label] = hits
    return out


def offending_type(g: Graph, type_name: str, label: str) -> str | None:
    """The type a target must STOP satisfying for `label`'s count to come down, or `None`.

    ⭐ This is what keeps the witness branch a *discriminating* ranker rather than an optimistic one: it
    lets a caller ask whether an effect could plausibly change the offending membership at all, instead of
    scoring every write to a witness as though it helped."""
    reqs = requirements(g, type_name)
    if reqs is None:
        return None
    schema, _a, _r = reqs
    req = schema.get(label)
    return None if req is None else req.type


def fails(g: Graph, node, reqs, _seen: frozenset = frozenset()) -> dict:
    """`violations` against already-gathered `requirements`. The shared implementation of both.

    `_seen` carries the `(node, type)` pairs already being proved, so recursion terminates — see
    `_target_ok`. A caller never passes it."""
    if node is None:
        return {"<node>": ("a node", "None")}
    schema, attrs, rels = reqs
    bad = {}
    for label, req in schema.items():
        sub = None
        if req.type is not None:
            sub = requirements(g, req.type)
            if sub is None:
                bad[label] = (f"targets that are a {req.type}", f"no type {req.type} is declared")
                continue
        n = len(_matching(g, node, label, req, sub, _seen))
        if n < req.lo or (req.hi is not None and n > req.hi):
            bad[label] = (_phrase(req), str(n))
    for key, a in attrs.items():
        got = g.attr(node, key)
        if not compare(a.op, got, a.value, a.hi):
            bad[f"@{key}"] = (_attr_phrase(a), repr(got))
    for rel in rels:
        if not _rel_holds(g, node, rel):
            left, right, _ = _rel_sides(g, node, rel)
            bad[f"{rel.left} {rel.op} {rel.right}"] = (str(rel.right), f"{left!r} vs {right!r}")
    return bad


def violations(g: Graph, node, type_name: str) -> dict:
    """Every way `node` fails to be a `type_name`, as `{label: (expected, actual)}`; empty means valid.

    Returned as data rather than raised, so a caller that wants to *ask* (a selection layer ranking
    candidates) uses the same code as one that wants to *insist* (`check`).

    ⚠ The name is resolved **once**. It used to be resolved four times — here, inside `schema_of`, inside
    `attrs_of`, and again per `base` hop — which was invisible while `find_type` looked cheap and dominated
    planning once it was measured. A caller testing many nodes against one type should hoist that out
    entirely with `requirements` + `fails`, which is what this is made of."""
    reqs = requirements(g, type_name)
    if reqs is None:
        return {"<type>": (type_name, "undeclared")}
    return fails(g, node, reqs)


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
    a `serviced_car`, and a planner that compared type *names* would miss it.

    ⚠ **Now that a constraint can be a RANGE, "tighter" is a real comparison and no longer plain equality**
    — `weight between 900 and 1000` must count as tighter than `weight between 800 and 2000`, or every
    widened type would stop subsuming its own base. Where the comparison cannot be decided (`!=`, values
    that do not order), this answers **False**, and the direction of that default is deliberate: `subsumes`
    feeds `function.producers`, so a false negative loses a candidate the planner could have used, while a
    false positive would offer one that does not actually satisfy the goal. Losing an option is recoverable;
    an unsound one is not."""
    return _subsumes(g, general, specific, frozenset())


def _bound_ok(tighter, looser, *, lower: bool) -> bool:
    """Is one interval endpoint at least as restrictive as another? Endpoints are `(value, inclusive)`."""
    tv, ti = tighter
    lv, li = looser
    try:
        if tv != lv:
            return tv > lv if lower else tv < lv
    except TypeError:
        return False
    return li or not ti                                  # equal values: an open bound is the tighter one


_NEG, _POS = (float("-inf"), False), (float("inf"), False)


def _window(a: AttrReq):
    """An attribute demand as an interval, or `None` where it is not one (`!=`, or anything unrecognised)."""
    if a.op == "==":
        return (a.value, True), (a.value, True)
    if a.op == "between":
        return (a.value, True), (a.hi, True)
    if a.op in ("<", "<="):
        return _NEG, (a.value, a.op == "<=")
    if a.op in (">", ">="):
        return (a.value, a.op == ">="), _POS
    return None


def _attr_tighter(s: AttrReq | None, gen: AttrReq) -> bool:
    if s is None:
        return False
    if s == gen:
        return True
    sw, gw = _window(s), _window(gen)
    if sw is None or gw is None:
        return False                                     # `!=` implies nothing we are willing to claim
    return _bound_ok(sw[0], gw[0], lower=True) and _bound_ok(sw[1], gw[1], lower=False)


def _req_tighter(g: Graph, s: Req | None, gen: Req, seen: frozenset) -> bool:
    if s is None:
        return False
    if gen.kind is not None and s.kind != gen.kind:
        return False
    if gen.type is not None and not (s.type == gen.type or
                                     (s.type is not None and _subsumes(g, gen.type, s.type, seen))):
        return False
    if s.lo < gen.lo:
        return False
    return gen.hi is None or (s.hi is not None and s.hi <= gen.hi)


def _subsumes(g: Graph, general: str, specific: str, seen: frozenset) -> bool:
    if general == specific:
        return True
    key = (general, specific)
    if key in seen:
        return True                                      # the same coinductive stance as `_target_ok`
    seen = seen | {key}
    gs, ss = schema_of(g, general), schema_of(g, specific)
    ga, sa = attrs_of(g, general), attrs_of(g, specific)
    gr, sr = rels_of(g, general), rels_of(g, specific)
    if not gs and not ga and not gr:
        return False                       # an undeclared or empty "general" subsumes nothing meaningful
    return (all(_req_tighter(g, ss.get(k), v, seen) for k, v in gs.items())
            and all(_attr_tighter(sa.get(k), v) for k, v in ga.items())
            and all(r in sr for r in gr))               # relations: structural containment, conservative


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
        if schema_of(g, n) or attrs_of(g, n) or rels_of(g, n)))


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


def _count_surface(r: Req) -> str:
    if r.hi is None:
        return "some" if r.lo == 1 else f"at least {r.lo}"
    if r.lo == 0 and r.hi == 0:
        return "no"
    if r.lo == r.hi:
        return str(r.lo)
    if r.lo == 0:
        return f"at most {r.hi}"
    return f"{r.lo} to {r.hi}"


def _value_surface(v) -> str:
    return f'"{v}"' if isinstance(v, str) else {True: "true", False: "false", None: "null"}.get(v, str(v))


def describe(g: Graph, name: str) -> str:
    """Render a declared type back to the surface it can be authored in — the round trip a model reads to
    check itself, and the same discipline `intake.describe` already applies to goals.

    ⚠ Renders what THIS type declares, not what it inherits. A block that repeated its base's requirements
    would round-trip into a different (flattened) declaration, and a round trip a model checks itself
    against must not be able to lie about where a demand came from."""
    t = find_type(g, name)
    if t is None:
        raise TypeViolation(f"no type {name!r} is declared")
    lines = [f"type {name}:"]
    if g.attr(t, "base"):
        lines.append(f"    is a {g.attr(t, 'base')}")
    for r in g.targets(t, "requires"):
        req = Req(g.attr(r, "target_kind"), g.attr(r, "target_type"), g.attr(r, "lo"), g.attr(r, "hi"))
        each = (f" each a {req.type}" if req.type else
                f" each of kind {req.kind}" if req.kind else "")
        lines.append(f"    has {_count_surface(req)} {g.attr(r, 'label')}{each}")
    for r in g.targets(t, "requires_attr"):
        a = AttrReq(g.attr(r, "op"), g.attr(r, "value"), g.attr(r, "hi"))
        lines.append(f"    {g.attr(r, 'key')} " + (
            f"between {_value_surface(a.value)} and {_value_surface(a.hi)}" if a.op == "between"
            else f"{a.op} {_value_surface(a.value)}"))
    for r in g.targets(t, "requires_rel"):
        right = g.attr(r, "right")
        lines.append(f"    {g.attr(r, 'left')} {g.attr(r, 'op')} "
                     f"{right if g.attr(r, 'right_is_path') else _value_surface(right)}")
    return "\n".join(lines)


# ⚠ `check` was the `CHECK` opcode, which made `isa.py` import this module — a type is a representation
# we decided, so the instruction set was carrying type semantics. Same fix as the planner's: registered
# here, reached by name. See `native.py`.
N.register("check", lambda g, _act, node, name: check(g, node, name))


__all__ = ["TypeViolation", "UNBOUNDED", "Req", "AttrReq", "Rel", "VALUE_OPS", "IDENTITY_OPS", "compare",
           "offenders", "offending_type",
           "declare_type", "require_edge", "require_value", "require_relation",
           "find_type", "schema_of", "attrs_of", "rels_of", "requirements", "fails",
           "violations", "is_a", "subsumes", "subtypes", "check", "instances",
           "type_names", "recognize", "tag", "tagged_as", "describe"]
