"""THE ENGINE — one machine.

Supersedes `standing.py` (propagating, fragment-union reads, `Cell.within`/`Cell.scope`) and `turn.py`
(fixpoint iteration, no matching). Those were three partial machines that did not compose; this is the
consolidation, and it implements `model.md` as revised by `revision-01` and `revision-02`.

## What the consolidation actually joins

`revision-02` §3 said *scope is support* and both halves were built without ever meeting: `overlay.py`
took a configuration as **declared**, and `standing.py` computed one by **walking the wiring**. Here they
meet, and the join turns out to need less than expected:

> **A unit needs no configuration at all.** It sees only what its gates delivered (`model.md` §5), and a
> supposition's contributions reach exactly the units wired downstream of it. Scope is not read, it is
> *wiring* — the tunnel, free, as §6 always promised.

Configurations are needed only for **reads of the assembled whole**, where `powering()` says which
suppositions each unit's output rests on. So `under` appears in `Network.graph()` and never in a unit.

## Power is plane 2; readability is plane 1

The distinction that decides this module's shape. A value arriving on a wire is what makes a unit fire;
what a unit can *read* is the overlay composition of its gates. A deletion changes readability. It does
**not** un-deliver anything, so it cannot withdraw the power that produced it.

⚠ `turn.py` conflated the two — it recomputed every unit's premise from the current view each round, so a
deletion could unpower its own producer, and the self-undermining case oscillated. That oscillation is a
property of *that* evaluation strategy, not of deletion. See `test_engine.py`.

## What each piece is

| | plane | |
|---|---|---|
| `Graph` (asserted) | 1 | what came from outside, plus what mutating rules applied |
| effects on a wire | 1 | proposals — overlays, composed lazily by `Overlays` |
| `Cell` | 2 | a *record of what a unit contributed*, not a box a fact lives in |
| `StandingUnit`, wires, gate energy | 2 | the running circuit |
| `unit.node` | 1 | the unit **as data**, so a fact can be about it (homoiconicity) |
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .graph import EMPTY, Graph, Node, role_edge
from .match import Absent, AttrVar, Match, Pat, atom, role, solve
from .overlay import (BASE, AddEdge, Grade, Identify, Mint, Overlays, Retract, SetAttr, View)

SURGE_AT = 6            # times one gate's input may CHANGE before the loop is burned — wide enough
                        # for realistic narrowing depth (`forms_discourse.md` §10.3's four-step
                        # reference example), since a genuine cycle (fresh mint every pass, never
                        # repeating or shrinking — no local signal distinguishes it, verified against
                        # the code, not just recalled) is caught just as surely a few passes later, at
                        # negligible fuel cost. Raising this only buys width, never proof; see
                        # `Network._unit_burned` for the half that matters — a burned unit's stale
                        # in-flight value must not leak into a read as if it were a finished answer.
SILENCED = "silenced"   # a unit carrying this produces nothing — see `bundled_silence_rule`
SURGED = "surged"       # the engine's only write: it reports, and a rule decides (`rev-02` §7)
ENGINE = "<engine>"     # the only source the engine contributes under

# -- tier 0: the wiring register's vocabulary (`forms_cnl.md` §6) ---------------------------------
#
# The whole of it, and it is now used in full: `pattern:` reaches a unit's left-hand side, described in
# the graph like everything else — and `effect:`, below, reaches its right-hand side.

WIRE = "<wire>"         # the occurrence: a 3-place relation, source × target × gate (`rev-02` §5)
CONFLICT = "conflict"   # the engine's second report: two live values for one slot (`rev-02` §6)
ABOUT = "about"         # …which node it is about
UNDER = "under"         # …and which supposition it is confined to, if any
SOURCE = "source"       # …and which unit produced each disagreeing reading
FROM = "from"
TO = "to"
GATE = "gate"
OUT = "out"             # a unit → the cell its output is held in; and container → contained (§6)
PATTERN = "pattern"     # a unit → the description of what it matches

# …and the occurrences a pattern is made of. **No new role**: `out:` is the one containment relation,
# and what a described node *is* comes from its `name`, matched explicitly like every other fact
# (`model.md` §4). That keeps tier 0 at five roles while the register learns to hold a whole LHS.

PAT = "<pattern>"        # the conjunction; `out:` → its conjuncts, in mint order
ATOM = "<atom>"          # one atom; `var` names it, `out:` → its constraints and sub-atoms
CONSTRAINT = "<constraint>"   # `key` + one of `value` / `attrvar` / `graded`
ABSENT = "<absent>"      # a negative conjunct; `out:` → the atoms that must not match
KEY = "key"
VALUE = "value"
ATTRVAR = "attrvar"     # …the constraint is an AttrVar of this name, not a literal
GRADED = "graded"       # …the attribute must be present, and its band enters the match strength
VAR = "var"

# -- tier 0 GREW, and the growth is the finding ---------------------------------------------------
#
# ⚠ `forms_cnl.md` §6 declares tier 0 closed at five roles. It is six now. The five were designed to
# describe **wiring** — what feeds what — and describing a whole *unit* is a job the register was never
# sized for: with `pattern:` in, plane 1 could say what a unit matches and what reaches it, and still
# not what it **concludes**. `effect:` is that missing half. Recorded rather than quietly absorbed: a
# tier declared closed and then grown is exactly the sort of thing that should be visible.

EFFECT = "effect"       # a unit → one of its effect templates, in mint order

EMIT = "<emit>"          # `mints` names the occurrence; `out:` → its `<role>`s; `as`, `grades`
ROLE = "<role>"          # `key` = the role name, `var` = what fills it
ATTRIBUTE = "<attribute>"     # `var` `key` `value`
STAMP = "<stamp>"        # `var` `key` `band`
LINK = "<link>"          # `var` → `dst`, optionally through a role node named `key`
MERGE = "<merge>"        # `left` `right`
DROP = "<drop>"          # `var`, optionally `key`, and `value` / `attrvar` for the source
MINTS = "mints"
AS = "as"
GRADES = "grades"       # …the attribute the firing's own match band is written to
BAND = "band"
DST = "dst"
LEFT = "left"
RIGHT = "right"


# -- a pattern, as data ---------------------------------------------------------------------------
#
# `forms_cnl.md` §9 step 1's remaining half. A unit's left-hand side was a Python object, so the one
# part of plane 2 that plane 1 could not describe was *what a unit looks for* — and a front end whose
# target is an engine API is what `model.md` §11 forbids.
#
# ⚠ **Order is mint order**, as it is for wires. Conjunct order is semantically inert for atoms and is
# **not** inert for `Absent`, which is evaluated against the bindings established so far (`match.py`);
# a rule's effects mint in authoring order, so authoring order is what survives. Nothing else in the
# graph could express the intent, and inventing a role to carry it would grow tier 0.


def _targets(g: Graph, n: Node, role_name: str) -> list:
    """Everything reached from `n` through a role node called `role_name`, in mint order.

    ⚠ **`Graph.out` is unordered** — edges live in a frozenset, so iteration follows hash order. Any
    reader that cares about sequence has to impose one, and `nid` is the only sequence the substrate
    records (invariant 15: nothing semantic may rest on it, and here only `Absent` does)."""
    found = [d for e in sorted(g.out(n), key=lambda x: x.nid)
             if g.attr(e, "name") == role_name for d in g.out(e)]
    return sorted(found, key=lambda x: x.nid)


def write_pattern(g: Graph, pattern) -> tuple:
    """A pattern, described in the graph. Returns `(graph, node)`."""
    p = Node(PAT)
    g = g.with_node(p, name=PAT)
    for item in pattern:
        g, n = _write_conjunct(g, item)
        g = role_edge(g, p, OUT, n)
    return g, p


def _write_conjunct(g: Graph, item) -> tuple:
    if isinstance(item, Absent):
        a = Node(ABSENT)
        g = g.with_node(a, name=ABSENT)
        for sub in item.atoms:
            g, n = _write_atom(g, sub)
            g = role_edge(g, a, OUT, n)
        return g, a
    return _write_atom(g, item)


def _write_atom(g: Graph, pat: Pat) -> tuple:
    a = Node(ATOM)
    g = g.with_node(a, name=ATOM, **({VAR: pat.var} if pat.var is not None else {}))
    for k, v in pat.attrs:
        c = Node(CONSTRAINT)
        g = (g.with_node(c, name=CONSTRAINT, **{KEY: k},
                         **({ATTRVAR: v.name} if isinstance(v, AttrVar) else {VALUE: v})))
        g = role_edge(g, a, OUT, c)
    for k in pat.graded:
        c = Node(CONSTRAINT)
        g = role_edge(g.with_node(c, name=CONSTRAINT, **{KEY: k, GRADED: True}), a, OUT, c)
    for sub in pat.out:
        g, n = _write_atom(g, sub)
        g = role_edge(g, a, OUT, n)
    return g, a


def read_pattern(g: Graph, node: Node) -> tuple:
    """The described pattern, as the matcher's own objects. The inverse of `write_pattern`.

    ⚠ **An unreadable member is refused, never skipped.** `assemble()` skips a wire naming something
    unbuilt, because a missing wire is a *smaller* circuit — visible, and it fails safe. A dropped
    constraint is the opposite: the pattern matches **more** than its author wrote, silently. Same
    asymmetry as `P9`, so this raises.

    ⚠ **A described conjunction with no conjuncts is refused too**, for the same reason at the limit: an
    empty pattern matches **vacuously**, so a truncated description would fire its unit on anything. An
    authored `()` is still legal — a Python author can mean it; a half-written description cannot."""
    conjuncts = tuple(_read_conjunct(g, c) for c in _targets(g, node, OUT))
    if not conjuncts:
        raise ValueError(f"{node!r} describes an empty pattern, which matches vacuously")
    return conjuncts


def _read_conjunct(g: Graph, n: Node):
    if g.attr(n, "name") == ABSENT:
        return Absent(tuple(_read_atom(g, s) for s in _targets(g, n, OUT)))
    return _read_atom(g, n)


def _read_atom(g: Graph, n: Node) -> Pat:
    if g.attr(n, "name") != ATOM:
        raise ValueError(f"{n!r} is not an atom (name={g.attr(n, 'name')!r})")
    attrs: list = []
    graded: list = []
    subs: list = []
    for t in _targets(g, n, OUT):
        kind = g.attr(t, "name")
        if kind == ATOM:
            subs.append(_read_atom(g, t))
        elif kind == CONSTRAINT:
            key = g.attr(t, KEY)
            if key is None:
                raise ValueError(f"constraint {t!r} carries no {KEY!r}")
            if g.attr(t, GRADED):
                graded.append(key)
            elif (av := g.attr(t, ATTRVAR)) is not None:
                attrs.append((key, AttrVar(av)))
            else:
                attrs.append((key, g.attr(t, VALUE)))
        else:
            raise ValueError(f"{n!r} contains {t!r}, which is neither an atom nor a constraint")
    return Pat(var=g.attr(n, VAR), attrs=tuple(sorted(attrs, key=lambda kv: kv[0])),
               graded=tuple(graded), out=tuple(subs))


# -- effect templates: what a rule says, before a match instantiates it --------------------------
#
# A rule is written against *variables*; `overlay.py`'s effects name *nodes*. These are the templates,
# and `instantiate` is the only place the two meet.

@dataclass(frozen=True)
class Emit:
    """Mint an occurrence: a node, its role nodes, and optionally a band from the firing's own match
    strength (§4, *a firing may inherit its match strength*).

    `as_` names the minted occurrence **for the rest of this firing**, so a later effect can point at it
    (`instantiate_all`). Without it every filler is a node the *match* found, and a rule can therefore
    build only stars around pre-existing nodes — never an edge between two things it just made."""

    name: str
    roles: tuple = ()              # ((role_name, var_name), …)
    graded: str | None = None
    as_: str | None = None


@dataclass(frozen=True)
class Attribute:
    """A crisp attribute derived onto a bound node. Applies as a **reified attribution**, never a write
    (`rev-02` §6) — which is what keeps two live disagreeing derivations visible as a conflict."""

    target: str
    attr: str
    value: Any


@dataclass(frozen=True)
class Stamp:
    """A gradable attribute at a stated band. Bands **meet** rather than conflict (`overlay.Grade`)."""

    target: str
    attr: str
    band: str


@dataclass(frozen=True)
class Link:
    target: str
    dst: str
    role: str | None = None


@dataclass(frozen=True)
class Merge:
    """Identify two bound nodes — the *applied* coreference decision. The decision is a rule's
    (`cnl.md` §1, create-never-merge); this is only its application."""

    left: str
    right: str


@dataclass(frozen=True)
class Drop:
    """Remove something. A **computation unit**'s drop hides while powered; a **mutating rule**'s is
    applied to the asserted layer at write-back and is real (`rev-01` §2).

    `source_var` names an **AttrVar** rather than a literal, so a rule can drop *the reading it
    matched* instead of one its author knew about in advance. Without it a conflict-resolving rule can
    only name a source hardcoded at authoring time, which is not resolution — `rev-02` §6 describes the
    loop *conflict → rule → retraction → clean read* and this is the binding it needs."""

    target: str
    attr: str | None = None
    source: str | None = None
    source_var: str | None = None


BOUND = "<bound>"       # in a premise-bound rule, the node the premise matched


def effects_of(g: Graph) -> tuple:
    """A graph, expressed as the proposals that would produce it.

    This is what makes *"a turn begins by firing from the axioms"* literal (`rev-01` §3): the asserted
    layer is not an ambient store units dip into, it is a set of contributions **with no predecessors**,
    delivered on wires like everything else. A unit that wants to read `name` must be wired to where the
    name is — subset output (`0008`), and the discipline the whole design rests on."""
    out: list = []
    for n in g.nodes:
        out.append(Mint(n, tuple(sorted(g.attrs.get(n, {}).items()))))
        for k, b in g.degrees.get(n, {}).items():
            out.append(Grade(n, k, b))
    out += [AddEdge(a, b) for a, b in g.edges]
    return tuple(out)


def _filler(var: str, m: Match, minted: dict) -> Node:
    """The node a template's filler names — **one namespace per firing**, match bindings and minted
    locals together. Not two lookups with a precedence rule: a local shadowing a bound variable is a
    rule contradicting itself, and it is refused rather than resolved (`P9` — the visible failure)."""
    if var in minted:
        return minted[var]
    return m[var]


def instantiate(template, m: Match, minted: dict | None = None) -> tuple:
    """One template plus one match becomes zero or more overlay effects.

    `minted` is the firing's local names (see `instantiate_all`); passing none means this template can
    neither read nor write one, which is the old behaviour and is fine for a single-effect rule."""
    if minted is None:
        minted = {}
    if isinstance(template, Emit):
        occ = Node(template.name)
        if template.as_ is not None:
            if template.as_ in m.bindings:
                raise ValueError(f"{template.as_!r} is already a match binding in this firing")
            if template.as_ in minted:
                raise ValueError(f"{template.as_!r} was already minted in this firing")
            minted[template.as_] = occ
        out = [Mint(occ, (("name", template.name),))]
        for role_name, var in template.roles:
            r = Node(role_name)
            out += [Mint(r, (("name", role_name),)), AddEdge(occ, r),
                    AddEdge(r, _filler(var, m, minted))]
        if template.graded is not None and m.band is not None:
            out.append(Grade(occ, template.graded, m.band))
        return tuple(out)
    if isinstance(template, Attribute):
        return (SetAttr(_filler(template.target, m, minted), template.attr, template.value),)
    if isinstance(template, Stamp):
        return (Grade(_filler(template.target, m, minted), template.attr, template.band),)
    if isinstance(template, Link):
        src, dst = _filler(template.target, m, minted), _filler(template.dst, m, minted)
        if template.role is None:
            return (AddEdge(src, dst),)
        r = Node(template.role)
        return (Mint(r, (("name", template.role),)), AddEdge(src, r), AddEdge(r, dst))
    if isinstance(template, Merge):
        a, b = _filler(template.left, m, minted), _filler(template.right, m, minted)
        return () if a is b else (Identify(a, b),)
    if isinstance(template, Drop):
        src = template.source
        if template.source_var is not None:
            src = m.values.get(template.source_var)
            if src is None:
                return ()
        return (Retract(_filler(template.target, m, minted), template.attr, src),)
    raise TypeError(f"unknown effect template {template!r}")


def instantiate_all(templates, m: Match) -> tuple:
    """A whole right-hand side against one match — **the effects instantiated together**, sharing one
    binding map.

    ⚠ **This is what lets a rule connect two nodes it minted.** Instantiated one template at a time,
    every filler is `m[var]`, i.e. a node the *left*-hand side found; two `Emit`s therefore produce two
    occurrences with nothing between them. Measured 2026-07-27, and it is on the critical path twice:
    a two-atom `pattern:` needs atom →`out:`→ atom, and a conditional needs the `when:` link between two
    claims — so *a rule writes a rule* was impossible independently of how patterns are reified.

    The fix adds no kind and no privileged namespace: the LHS has variables, so give the RHS names too,
    scoped to one firing exactly like a match binding."""
    out: list = []
    minted: dict = {}
    for t in templates:
        out.extend(instantiate(t, m, minted))
    return tuple(out)


# -- an effect, as data ---------------------------------------------------------------------------
#
# The last part of a unit that plane 1 could not describe: **what it concludes**. Same shape as a
# pattern — one node per template, `name` says which, attributes carry the fields — and the same
# ordering discipline, which here is not a nicety: RHS local names are resolved in authoring order
# (`instantiate_all`), so a described right-hand side is read in **mint order** or it is a different
# rule.

_EFFECT_FIELDS = {
    EMIT: ("name", MINTS, "graded", GRADES, "as_", AS),
    ATTRIBUTE: ("target", VAR, "attr", KEY, "value", VALUE),
    STAMP: ("target", VAR, "attr", KEY, "band", BAND),
    LINK: ("target", VAR, "dst", DST, "role", KEY),
    MERGE: ("left", LEFT, "right", RIGHT),
    DROP: ("target", VAR, "attr", KEY, "source", VALUE, "source_var", ATTRVAR),
}
_EFFECT_KIND = {EMIT: Emit, ATTRIBUTE: Attribute, STAMP: Stamp,
                LINK: Link, MERGE: Merge, DROP: Drop}
# What the template cannot be built without. Everything else has a default, and a missing default is
# the author declining an option; a missing *required* field is a truncated description.
_EFFECT_REQUIRED = {EMIT: (MINTS,), ATTRIBUTE: (VAR, KEY), STAMP: (VAR, KEY, BAND),
                    LINK: (VAR, DST), MERGE: (LEFT, RIGHT), DROP: (VAR,)}


def write_effect(g: Graph, template) -> tuple:
    """One effect template, described in the graph. Returns `(graph, node)`."""
    kind = next((k for k, cls in _EFFECT_KIND.items() if type(template) is cls), None)
    if kind is None:
        raise TypeError(f"unknown effect template {template!r}")
    fields = _EFFECT_FIELDS[kind]
    crisp = {"name": kind}
    for attr, key in zip(fields[::2], fields[1::2]):
        v = getattr(template, attr)
        if v is not None:
            crisp[key] = v
    e = Node(kind)
    g = g.with_node(e, **crisp)
    for role_name, var in getattr(template, "roles", ()):
        r = Node(ROLE)
        g = role_edge(g.with_node(r, name=ROLE, **{KEY: role_name, VAR: var}), e, OUT, r)
    return g, e


def read_effect(g: Graph, node: Node):
    """The described effect, as the template `instantiate` expects. The inverse of `write_effect`.

    ⚠ **Refused, not skipped**, for the reason `read_pattern` gives — and here it is sharper. A dropped
    `Emit` merely makes a unit conclude less, but a dropped `Drop` makes the graph read **more**:
    deletion is the one non-monotone effect (`rev-02` §6), so *"skip what you cannot read"* would widen
    the world in exactly the case that matters."""
    kind = g.attr(node, "name")
    if kind not in _EFFECT_KIND:
        raise ValueError(f"{node!r} is not an effect (name={kind!r})")
    fields = _EFFECT_FIELDS[kind]
    missing = [k for k in _EFFECT_REQUIRED[kind] if g.attr(node, k) is None]
    if missing:
        raise ValueError(f"{node!r} is a truncated {kind}: no {', '.join(missing)}")
    kwargs = {attr: g.attr(node, key) for attr, key in zip(fields[::2], fields[1::2])}
    if kind == EMIT:
        kwargs["roles"] = tuple((g.attr(r, KEY), g.attr(r, VAR)) for r in _targets(g, node, OUT))
    return _EFFECT_KIND[kind](**kwargs)


# -- what travels, and what records ---------------------------------------------------------------

@dataclass(frozen=True)
class Value:
    """What travels on a wire: **effects**, not a graph.

    ⚠ `standing.py` carried `graph: Graph` *and* `merges: tuple` beside it, because `Merge` rewrites
    every mention and could not be expressed as a fragment. One effect type not fitting the container was
    the container being wrong (`rev-02` §6). Here every effect is the same kind of thing.

    ⚠ There is no `path`. Energy lives at the **gate** as a count of input *changes*, so a long acyclic
    chain costs nothing and no history is carried."""

    effects: tuple = ()
    band: str | None = None


class Cell:
    """A **record of what a unit contributed** — plane 2, holding plane-1 content.

    ⚠ `within` and `scope` are gone (`rev-02` §3). They made containment a second axis of *position*,
    when scope is **support**: not a place a fact sits but which configuration powers it. That mistake is
    also what `revision-01` §8's "seal leak" really was.

    `node` is the cell **as data** — what a wire's `from:` names. Without it the wiring register has
    nothing to point at and topology stays a Python list."""

    __slots__ = ("name", "axiom", "supposes", "held", "node", "owner")

    def __init__(self, name: str, *, axiom: bool = False, supposes: str | None = None) -> None:
        self.name = name
        self.axiom = axiom
        self.supposes = supposes        # this cell IS a supposition, named
        self.held: Value | None = None
        self.node = Node(name)
        self.owner: "StandingUnit | None" = None

    def __repr__(self) -> str:
        return f"<Cell {self.name}{' axiom' if self.axiom else ''}{'' if self.held else ' empty'}>"


class StandingUnit:
    """A unit that stands. It matches over the composition of its gates and records what it derived.

    **It sees only its gates** (invariant 3). There is no ambient store, and therefore no configuration
    to be in: a supposition's contributions arrive because something wired them here, or they do not
    arrive at all. That is the tunnel, and it costs nothing."""

    def __init__(self, name: str, pattern: tuple | None, *effects, gates: tuple = ("in",),
                 theta: str | None = None, mutating: bool = False,
                 bind: str | None = None) -> None:
        self.name = name
        # `None` is *"my pattern is described in the graph"* — the assembler fills it each revive. It is
        # not the same as `()`, which is a pattern that matches vacuously and fires on anything.
        #
        # ⚠ `pattern` is **derived** and `authored` is what it falls back to, exactly as `Network.wires`
        # is derived. Without the fallback, un-describing a pattern would leave the last one read still
        # running — the same defect the wiring register was built to remove, one level in.
        self.authored = pattern
        self.pattern = pattern
        # …and the same for the right-hand side. `()` here is a unit that concludes nothing, which is
        # legitimate — so unlike a pattern there is no `None`, and *described* simply replaces it.
        self.authored_effects = effects
        self.effects = effects
        self.gates = tuple(gates)
        self.theta = theta
        self.mutating = mutating
        self.bind = bind                # premise variable a BOUND effect refers to
        self.node = Node(name)          # the unit AS DATA — homoiconicity (`rev-02` §§1, 5)
        self.latched: dict = {g: None for g in self.gates}
        self.changes: dict = {g: 0 for g in self.gates}
        self.cell = Cell(f"{name}:out")
        self.cell.owner = self
        self.firings = 0

    def clear(self) -> None:
        """A revive throws away *values*, never wiring (`rev-01` §3)."""
        self.latched = {g: None for g in self.gates}
        self.changes = {g: 0 for g in self.gates}
        self.cell.held = None
        self.firings = 0

    def view(self) -> View:
        """Everything this unit can see: its gates, composed. Nothing else exists for it."""
        effects: list = []
        for v in self.latched.values():
            if v is not None:
                effects.extend((self.name, e) for e in v.effects)
        return Overlays(EMPTY, effects).view()

    def deliver(self, gate: str, value: Value) -> Value | None:
        if gate not in self.latched:
            raise KeyError(f"{self.name} has no gate {gate!r} (gates: {self.gates})")
        self.latched[gate] = value
        return self.fire()

    def fire(self) -> Value | None:
        """Match and emit. `None` is *a unit that had nothing to say* — not an error and not a miss."""
        self.firings += 1
        if self.pattern is None:
            return None                 # described, and nothing has described it — a dangling LHS
        if not any(v is not None for v in self.latched.values()):
            return None
        produced: list = []
        band = None
        for m in solve(self.view(), self.pattern, self.theta):
            # The whole RHS at once, per match — so effects of one firing can name each other.
            produced.extend(instantiate_all(self.effects, m))
            band = m.band if band is None else band
        if not produced:
            return None
        out = Value(tuple(produced), band)
        self.cell.held = out
        return out

    def dangling(self) -> tuple:
        """Gates with nothing on them. Not an error: this is what asks (§9's miss), what holds attention
        (§7), and what makes a standing watch (`rev-01` §5)."""
        return tuple(g for g, v in self.latched.items() if v is None)

    def __repr__(self) -> str:
        return f"<Unit {self.name} fired={self.firings} dangling={self.dangling()}>"


# The register's whole grammar, as an ordinary pattern over ordinary data. Nothing privileged: it finds
# wires because it *names* `<wire>`, `from`, `to` and `gate` — invariant 19, and the reason machinery
# needs no partition. The gate arrives as an attribute value, not a node, via `AttrVar`.
_WIRE_PATTERN = (atom("w", name=WIRE, out=(role(FROM, atom("src")),
                                           role(TO, atom("dst")),
                                           role(GATE, atom("g", name=AttrVar("gate"))))),)


def _grew(prior: Value, value: Value) -> bool:
    """Did this input only **gain** effects? Then it is not energy.

    `rev-02` §6's monotonicity theorem, applied one level down. That argument — *mint, edge and
    attribute only ever make more things readable, so a gate going present → absent is proof a
    non-monotone effect fired* — is about a gate's **readable set**; the same reasoning holds of the
    value on the wire, and without it a value that merely accumulates registers as a change.

    ⚠ **Found by the corrector burning itself.** Once `bundled:silence` could fire at all, a network
    with four loops surged four times, and each surge extended the report on the rule's one gate — so
    at the third the detector burned the *corrector*, and the fourth loop went uncorrected. That is
    counting growth as cycling, which is `model.md` §5's per-hop mistake in new clothes.

    ⚠ **The cost is that monotone-but-infinite is now even more squarely fuel's job** — a `rev-02` §9
    open item, and this narrows the detector's remit onto the case its theorem actually covers."""
    try:
        return set(prior.effects) <= set(value.effects)
    except TypeError:                   # an unhashable effect payload: no claim, so no exemption
        return False


@dataclass(frozen=True)
class Surge:
    """A gate whose input kept changing. A **positive fact** naming the unit, the gate and the loop —
    never an absence to be noticed, which is why energy grows rather than decays."""

    unit: str
    gate: str
    loop: tuple
    flips: int


class Network:
    """Asserted data, standing units, standing wiring. `revive()` is the turn.

    ⚠ **The wiring is not a field.** `self.wires` used to be a Python list of tuples, which made
    invariant 18 false (*everything persistent is plane 1*) and made the front end's target an **engine
    API** — the one thing `model.md` §11 forbids. Topology is now **derived** from `self.asserted` by
    `assemble()`, and `wire()` is a convenience that writes the fact `assemble()` reads. Anything that
    can write a graph can wire — including a mutating rule, which is invariant 4's *units propose
    wirings as facts* actually cashed."""

    def __init__(self, asserted: Graph = EMPTY) -> None:
        self.asserted = asserted
        self.units: list = []
        self.axioms: list = []
        self.surges: list = []
        self.burned: set = set()
        self.out_of_fuel = False
        self.applied: tuple = ()
        self._built: dict = {}          # plane-1 node → the plane-2 object it describes
        self._wiring: tuple = ()
        self._wiring_of: Graph | None = None
        # The engine's report, as a cell — see `reports`.
        self.reports = Cell(ENGINE)
        self._describe(self.reports.node, self.reports, name=ENGINE)

    # -- construction -----------------------------------------------------------------------------

    def axiom(self, *effects, name: str = "axiom", supposes: str | None = None) -> Cell:
        c = Cell(name, axiom=True, supposes=supposes)
        c.held = Value(tuple(effects))
        self.axioms.append(c)
        self._describe(c.node, c, name=name)
        return c

    def given(self, g: Graph, *, name: str = "given") -> Cell:
        """Assert a graph. It joins the store **and** becomes an axiom that delivers it onto wires."""
        self.asserted = self.asserted.union(g)
        return self.axiom(*effects_of(g), name=name)

    def supposing(self, g: Graph, *, name: str) -> Cell:
        """*"Suppose it rains."* Delivered on wires like an axiom, but **not** joined to the store — a
        supposition is not a thing that happened."""
        return self.axiom(*effects_of(g), name=name, supposes=name)

    def suppose(self, *effects, name: str) -> Cell:
        """*"Suppose it rains."* An axiom whose contributions carry its own name as support, so anything
        downstream of it is inside it — and nothing else can see it, because nothing else is wired."""
        return self.axiom(*effects, name=name, supposes=name)

    def add(self, unit: StandingUnit) -> StandingUnit:
        self.units.append(unit)
        # Units are plane-1 data: the node goes in the same graph as everything else, with no machinery
        # partition (`rev-02` §5). Ordinary rules do not match it for the ordinary reason — nothing
        # matches implicitly (invariant 19).
        self._describe(unit.node, unit, name=unit.name)
        self._describe(unit.cell.node, unit.cell, name=unit.cell.name)
        # …and the unit's `out:` role, so a wire can be written naming only the unit.
        self.asserted = role_edge(self.asserted, unit.node, OUT, unit.cell.node)
        return unit

    def wire(self, src: Cell, dst: StandingUnit, gate: str = "in") -> None:
        """The only way a unit reaches anything. Wiring out of a supposition's cell is `model.md` §6's
        crossing: one explicit act, no permission rule, no crossing predicate.

        ⚠ **This is not where wiring lives.** It writes a `<wire>` occurrence — source, target and gate,
        each through its own role node, because an edge is nameless and a 3-place relation cannot be one
        (`rev-02` §5). `assemble()` reads it back. Write the same occurrence by hand, or conclude it from
        a rule, and the circuit is wired just the same."""
        w, gate_node = Node(WIRE), Node(gate)
        g = self.asserted.with_node(w, name=WIRE).with_node(gate_node, name=gate)
        g = role_edge(g, w, FROM, src.node)
        g = role_edge(g, w, TO, dst.node)
        self.asserted = role_edge(g, w, GATE, gate_node)

    def describe_pattern(self, unit: StandingUnit, pattern) -> Node:
        """Give a unit a left-hand side **by writing it down**. The counterpart of `wire()`: it writes
        the facts `assemble_units()` reads, and a rule concluding the same occurrences gives the unit
        the same pattern."""
        self.asserted, p = write_pattern(self.asserted, pattern)
        self.asserted = role_edge(self.asserted, unit.node, PATTERN, p)
        return p

    def describe_effects(self, unit: StandingUnit, *templates) -> tuple:
        """Give a unit a right-hand side by writing it down. Order is mint order, and here that is
        load-bearing: RHS local names resolve in authoring order (`instantiate_all`)."""
        out: list = []
        for t in templates:
            self.asserted, e = write_effect(self.asserted, t)
            self.asserted = role_edge(self.asserted, unit.node, EFFECT, e)
            out.append(e)
        return tuple(out)

    def _describe(self, node: Node, obj, **crisp) -> Node:
        """Put a plane-2 object's description in the graph and record the crossing.

        This map is **the assembler**, and it is the only place plane 1 and plane 2 meet. It holds
        nothing invariant 18 forbids: it is rebuilt by construction, never carried across a revive."""
        self.asserted = self.asserted.with_node(node, **crisp)
        self._built[node] = obj
        return node

    # -- the wiring register ------------------------------------------------------------------------

    def assemble(self) -> tuple:
        """**Read the topology out of the graph.** `forms_cnl.md` §1's assembler: it wires what the
        register describes and never sees a statement.

        A description naming something that was never built is **skipped, not an error** — the same
        stance as a dangling gate (invariant 14). Ordered by the wire node's mint order so a run is
        reproducible; nothing semantic rests on it (invariant 15)."""
        found: list = []
        for m in solve(self.asserted, _WIRE_PATTERN):
            src, dst = self._built.get(m["src"]), self._built.get(m["dst"])
            if not isinstance(src, Cell) or not isinstance(dst, StandingUnit):
                continue
            found.append((m["w"].nid, src, dst, m.values["gate"]))
        return tuple((s, d, g) for _nid, s, d, g in sorted(found, key=lambda t: t[0]))

    def assemble_units(self) -> None:
        """**Read each unit's left- and right-hand side out of the graph**, where they are described.

        The other half of `assemble()`, and the same stance: it reads a description and never sees a
        statement. A unit with nothing described keeps whatever Python handed it — which is how the
        register grows into the engine rather than replacing it in one step.

        ⚠ **Two patterns is an error, not a conjunction.** Two wires are two deliveries and compose
        harmlessly; two patterns are a unit whose author cannot be identified, and picking one silently
        is exactly the unrecoverable direction (`P9`). Two *effects* are fine and ordinary — a right-hand
        side is a sequence, and mint order is what orders it."""
        for u in self.units:
            described = _targets(self.asserted, u.node, PATTERN)
            if len(described) > 1:
                raise ValueError(f"{u.name} has {len(described)} described patterns")
            u.pattern = read_pattern(self.asserted, described[0]) if described else u.authored

            effects = _targets(self.asserted, u.node, EFFECT)
            u.effects = (tuple(read_effect(self.asserted, e) for e in effects) if effects
                         else u.authored_effects)

    @property
    def wires(self) -> tuple:
        """Derived, and cached against the graph value it was derived from. `Graph` is immutable, so an
        identity check is exact: a new graph is a new value, and re-assembly is due."""
        if self._wiring_of is not self.asserted:
            self._wiring_of = self.asserted
            self._wiring = self.assemble()
        return self._wiring

    # -- the turn ---------------------------------------------------------------------------------

    def revive(self, fuel: int = 10_000) -> "Network":
        """Fire from the axioms and stabilize. Everything derived is recomputed from *(axioms, wiring)*
        alone — invariant 15, where *wiring* now includes the units' own patterns."""
        self.assemble_units()
        for u in self.units:
            u.clear()
        self.surges = []
        self.burned = set()
        self.reports.held = None
        self.out_of_fuel = False
        reported: set = set()

        seen_conflicts: set = set()

        queue = [(c, c.held) for c in self.axioms if c.held is not None]
        while True:
            fuel = self._drain(queue, self.burned, reported, fuel)
            if self.out_of_fuel:
                break
            # ⚠ **Conflicts have to be delivered, not merely readable.** `rev-02` §6 describes the loop
            # *conflict → a rule matches it → the rule concludes a retraction → the next revive reads
            # cleanly*, and it could not happen: `conflicts()` is a read-layer method and nothing put a
            # conflict on a wire, so no unit ever saw one. Same defect as `surged`, in the other
            # governance path. Detection runs after the queue drains, because a conflict is a property
            # of what everything concluded, not of any one firing.
            fresh = self.detect_conflicts(seen_conflicts)
            if not fresh:
                break
            queue.append(self.report(*fresh))

        self.write_back()
        return self

    def _drain(self, queue: list, burned: set, reported: set, fuel: int) -> int:
        while queue:
            if fuel <= 0:
                self.out_of_fuel = True
                break
            fuel -= 1
            cell, value = queue.pop(0)
            for (src, unit, gate) in self.wires:
                if src is not cell or (src.name, unit.name, gate) in burned:
                    continue
                # Energy at the gate: has this input CHANGED again? A first arrival is not a change, so
                # a chain — which delivers once per gate — costs nothing at any depth.
                prior = unit.latched.get(gate)
                if prior is not None and prior != value and not _grew(prior, value):
                    unit.changes[gate] += 1
                    if unit.changes[gate] >= SURGE_AT:
                        key = (src.name, unit.name, gate)
                        if key not in reported:
                            self.surges.append(
                                Surge(unit.name, gate, self.loop_through(unit), unit.changes[gate]))
                            reported.add(key)
                            queue.append(self.report(SetAttr(unit.node, SURGED, gate)))
                        burned.add(key)
                        continue
                if self.silenced(unit):
                    continue
                out = unit.deliver(gate, value)
                if out is not None:
                    queue.append((unit.cell, out))
        return fuel

    def configurations(self) -> list:
        """The base world, and each supposition on its own. What conflicts are looked for *in*."""
        return [(frozenset(), None)] + [(frozenset({c.supposes}), c)
                                        for c in self.axioms if c.supposes]

    def detect_conflicts(self, seen: set) -> tuple:
        """Every disagreement not yet reported, as **facts on a wire**.

        ⭐ **A conflict found only under a supposition is attributed to it**, and the report itself is
        *not* inside it. That is what makes reductio expressible without breaking §3: `reports` has
        empty support, so a rule wired to it concludes in the **base world** — which is right, because
        *"H leads to a contradiction"* is a fact about the reasoning, not a fact inside the hypothesis.
        The alternative — a declared support-breaking unit — would have cost scope-as-backward-walk its
        only virtue."""
        o = self.overlays()
        base = {(c.node, c.attr) for c in o.conflicts(frozenset())}
        out: list = []
        for under, cell in self.configurations():
            for c in o.conflicts(under):
                # A conflict already present in the base world is the base world's, not this
                # supposition's — otherwise every hypothesis inherits the blame for every prior mess.
                if cell is not None and (c.node, c.attr) in base:
                    continue
                key = (c.node, c.attr, cell.name if cell else None)
                if key in seen:
                    continue
                seen.add(key)
                out.extend(self._conflict_facts(c, cell))
        return tuple(out)

    def _conflict_facts(self, conflict, cell: Cell | None) -> list:
        """One conflict as an ordinary occurrence — `model.md` §8's discipline, that an outcome is a
        positive fact and never an absence. Nothing here is a new kind of thing."""
        occ = Node(CONFLICT)
        facts: list = [Mint(occ, (("name", CONFLICT), ("attr", conflict.attr)))]
        # One `source:` role per disagreeing reading, pointing at the **unit that produced it** — which
        # is only possible because a unit is plane-1 data (`rev-02` §1). It is what lets a resolving
        # rule name a side; without it a rule can see that there is a disagreement and not who is in it.
        sources = [(SOURCE, u.node) for r in conflict.readings
                   if (u := next((x for x in self.units if x.name == r.source), None)) is not None]
        named_targets = {u.node: u.name for u in self.units}
        if cell is not None:
            named_targets[cell.node] = cell.name
        for role_name, target in ((ABOUT, conflict.node),
                                  *([(UNDER, cell.node)] if cell is not None else ()),
                                  *sources):
            r = Node(role_name)
            facts += [Mint(r, (("name", role_name),)), AddEdge(occ, r), AddEdge(r, target)]
            # ⚠ **Mentioning a node is not delivering it.** A unit sees only its gates, so a report that
            # points at a unit without carrying that unit's *name* gives a rule something it cannot
            # identify — `0008`'s subset-output discipline, hit from the reporting side. The reductio
            # rule did not notice, because it only needed the node; a resolving rule needs the name.
            if target in named_targets:
                facts.append(Mint(target, (("name", named_targets[target]),)))
        return facts

    def report(self, *effects) -> tuple:
        """The engine's **only** contribution, and it now travels like everything else.

        ⚠ A report the engine merely *writes into the read layer* is one no rule can act on, because a
        unit sees only its gates (invariant 3). That is the shape the surge correction was in: `surged`
        appeared in `graph()` and reached no unit, so `bundled:silence` could not fire whatever its
        pattern said. Reporting on a **cell** puts the plane-1 → plane-2 interface where every other
        value already crosses, and costs no new mechanism.

        Accumulative within a turn: `rev-02` §6's *"a report must persist for the turn; a conclusion
        must not"*."""
        prior = self.reports.held.effects if self.reports.held is not None else ()
        self.reports.held = Value(prior + tuple(effects))
        return (self.reports, self.reports.held)

    def write_back(self) -> tuple:
        """Apply what **mutating rules** concluded to the asserted layer — after stabilization, never
        during (`model.md` §9). A computation unit's output is never applied; it is recomputed.

        ⚠ **Not after a turn that failed to settle.** A surge means no answer was reached, so applying
        a partial one would let an unstable configuration edit the world a little on every attempt.

        ⚠ **Identifications are applied last, deliberately.** `revision-02` §6 finding 4: applying a
        merge eagerly rewrites only the mentions that exist *at that moment*, so a later effect naming
        the dropped node re-introduces it. Reads avoid this by being lazy; the store cannot, because it
        is a `Graph`. Ordering identifications last is the narrowest fix, and it is the one place in the
        design where effect order still matters."""
        if self.surges or self.out_of_fuel:
            return ()
        applied: list = []
        for u in self.units:
            # ⚠ **A rule inside a supposition has not acted.** `rev-02` §6 argued scoping is free —
            # *"a deletion inside a supposition does not reach the base world, with no extra
            # machinery"* — and that is true of **overlays**, which are read under a configuration. It
            # was never true of write-back, which applies to the store with no configuration at all. So
            # *"suppose it rains"* wired to a mutating rule really took the umbrella.
            #
            # Support is the filter, exactly as it is on the read path (§3). Measured 2026-07-27 while
            # probing whether `suppose` can discharge; this was the other half of that probe.
            if u.mutating and u.cell.held is not None and not self.powering(u):
                applied.extend(u.cell.held.effects)
        merges = [e for e in applied if isinstance(e, Identify)]
        for e in [x for x in applied if not isinstance(x, Identify)] + merges:
            if isinstance(e, Mint):
                self.asserted = self.asserted.with_node(e.node, **dict(e.attrs))
            elif isinstance(e, AddEdge):
                self.asserted = self.asserted.with_edge(e.src, e.dst)
            elif isinstance(e, SetAttr):
                self.asserted = self.asserted.with_node(e.target, **{e.attr: e.value})
            elif isinstance(e, Grade):
                self.asserted = self.asserted.with_degree(e.target, e.attr, e.band)
            elif isinstance(e, Retract):
                self.asserted = self.asserted.without(e.target, e.attr)
            elif isinstance(e, Identify):
                self.asserted = self.asserted.merge(e.keep, e.drop)
        self.applied = tuple(applied)
        return self.applied

    def _unit_burned(self, u: StandingUnit) -> bool:
        """Did *any* of this unit's gates get burned this turn?

        `cnl_engine_goal_plan.md` Phase D: a burned gate stops delivering, but the unit's `cell.held`
        still holds whatever it last derived **before** burning — an in-flight, unfinished value, not
        an answer. Nothing upstream of `_live()` used to check this, so a burned unit's stale value
        read exactly like a settled one: the *"depth ≥ 5 is silently partial"* finding in
        `forms_discourse.md` §10.3. Excluding it here makes that unit's contribution read as absent —
        honest *"nothing came to mind"* (`model.md` §7–8), not a wrong or half-finished answer — while
        `SURGED` (written on the unit's own node, see `_drain`) still says why, for whatever reads
        that far."""
        return any(name == u.name for (_src, name, _gate) in self.burned)

    def silenced(self, unit: StandingUnit) -> bool:
        """Has a rule concluded that this unit should stop? Read from the graph, because the correction
        is *a rule's conclusion* and rules conclude facts (invariant 4, *units propose wirings as
        facts*)."""
        return self.graph().attr(unit.node, SILENCED) is not None

    # -- reads ------------------------------------------------------------------------------------

    def _live(self) -> tuple:
        held = self.reports.held
        effects = [(ENGINE, e) for e in (held.effects if held is not None else ())]
        support = {ENGINE: frozenset()}
        for c in self.axioms:
            if c.held is None:
                continue
            effects += [(c.name, e) for e in c.held.effects]
            support[c.name] = frozenset({c.supposes} if c.supposes else ())
        for u in self.units:
            if u.cell.held is not None and not self._unit_burned(u):
                effects += [(u.name, e) for e in u.cell.held.effects]
            support[u.name] = self.powering(u)
        return tuple(effects), support

    def overlays(self) -> Overlays:
        effects, support = self._live()
        return Overlays(self.asserted, list(effects), support)

    def graph(self, under: frozenset | None = None) -> View:
        """**The** graph in a configuration. `under=None` means *everything live*, which is the
        debugging view; `world()` is the honest one."""
        o = self.overlays()
        if under is None:
            under = frozenset(c.supposes for c in self.axioms if c.supposes)
        return o.view(under)

    def world(self) -> View:
        """The base world: what is derived by units **not powered by any supposition**.

        ⚠ Not a place — a *filter*. A conclusion reached inside a hypothesis is simply not here, and
        nothing computed a projection to exclude it (`rev-02` §3)."""
        return self.overlays().view(frozenset())

    def powering(self, unit: StandingUnit) -> frozenset:
        """The suppositions this unit's output rests on — walked **backwards over the wiring**.

        This is scope, and it is the reason no rule ever names one (invariant 1). A contradiction
        condemns whatever configuration fed the detector, and the configuration is not something a
        detector is told: it is what the wiring already records."""
        found, seen, stack = set(), set(), [unit]
        while stack:
            u = stack.pop()
            if id(u) in seen:
                continue
            seen.add(id(u))
            for (src, dst, _g) in self.wires:
                if dst is not u:
                    continue
                if src.supposes:
                    found.add(src.supposes)
                owner = self._owner(src)
                if owner is not None:
                    stack.append(owner)
        return frozenset(found)

    def loop_through(self, unit: StandingUnit) -> tuple:
        """The cycle this unit sits on, read off the **wiring** by walking backwards. The loop was never
        in the value; it is in the topology, and provenance here is the wiring."""
        def back(u, seen):
            for (src, dst, _g) in self.wires:
                if dst is not u:
                    continue
                owner = self._owner(src)
                if owner is None:
                    continue
                if owner is unit:
                    return seen
                if owner.name in seen:
                    continue
                found = back(owner, seen + [owner.name])
                if found:
                    return found
            return None
        return tuple(dict.fromkeys(back(unit, [unit.name]) or [unit.name]))

    def _owner(self, cell: Cell):
        return cell.owner

    def _unit_named(self, name: str):
        return next(u for u in self.units if u.name == name)

    def dangling(self) -> list:
        return [(u.name, g) for u in self.units for g in u.dangling()]


def bundled_silence_rule(net: Network) -> StandingUnit:
    """**The surge correction, shipped as an ordinary rule** — *anything that surged: stop its output.*

    No privileged status and no engine hook. It is written *about units*, which it can only be because a
    unit is plane-1 data with a node of its own. Shipping it as a rule rather than as engine policy is
    the composability principle: a governance mechanism hardcoded in Python is an unreachable island.

    ⚠ **Two defects were found here by trying to make it fire**, and both were invisible to a test that
    only checked the engine's half:

    1. the pattern was `surged=None`, which reads as *"`surged` equals `None`"* — and `attr` returns
       `None` for an attribute that is **absent**, so it matched every node **except** the surged one.
       The matcher has no *"present, any value"* atom; `AttrVar` **is** one, because it fails when the
       attribute is missing. That is this rule's whole fix, and it is also the general answer;
    2. it was wired to whatever the author happened to wire it to, and `surged` was never on a wire at
       all. It is wired to `net.reports` here, which is the only place it can see one."""
    u = net.add(StandingUnit("bundled:silence", (atom("s", **{SURGED: AttrVar("gate")}),),
                             Attribute("s", SILENCED, True)))
    net.wire(net.reports, u)
    return u


def readable(view: View, nodes) -> dict:
    """Every crisp attribute readable about these nodes, as a plain dict.

    A comparison surface for order-independence testing (invariant 15). It reads *content*, not node
    identity, because `Emit` mints a fresh node per firing — so two runs that agree perfectly still hold
    different `Node` objects, and identity comparison would report a difference that is not one."""
    out: dict = {}
    for n in nodes:
        keys = set(view._o.base.attrs.get(n, {}))
        keys |= {a for a, _v, _s in view._o._attribs.get(view._o.resolve(n), ())}
        for k in keys:
            v = view.attr(n, k)
            if v is not None:
                out[(n.nid, k)] = v
    return out


__all__ = ["Emit", "Attribute", "Stamp", "Link", "Merge", "Drop", "instantiate", "instantiate_all",
           "effects_of", "write_pattern", "read_pattern", "write_effect", "read_effect",
           "CONFLICT", "ABOUT", "UNDER", "SOURCE",
           "Value", "Cell", "StandingUnit", "Surge", "Network", "bundled_silence_rule", "readable",
           "SURGE_AT", "SILENCED", "SURGED", "ENGINE", "BOUND",
           "WIRE", "FROM", "TO", "GATE", "OUT", "PATTERN", "EFFECT",
           "PAT", "ATOM", "CONSTRAINT", "ABSENT", "KEY", "VALUE", "ATTRVAR", "GRADED", "VAR",
           "EMIT", "ROLE", "ATTRIBUTE", "STAMP", "LINK", "MERGE", "DROP",
           "MINTS", "AS", "GRADES", "BAND", "DST", "LEFT", "RIGHT"]
