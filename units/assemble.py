"""THE ASSEMBLER — step 2 of the loop (`model.md` §7), reading the wiring register.

> **The outer driver does no semantics.** It retrieves, wires, runs, and writes. It does not match,
> decide, scope, or interpret. Every judgement lives inside a unit. That line is load-bearing: erode it
> — make the driver *"smart about relevance"* — and you have rebuilt the central machine this design
> exists to escape.

So this module is deliberately dull, and its dullness is the property under test. It **wires only what
is described** (§11) and mints nothing that the description did not ask for. In particular it does not
*unroll*: it has no idea what a statement means, only that a `statement` node has ordered `step` roles.

**Is decoding a pattern "interpretation"?** No, and it is worth being explicit since the line matters.
Decoding is total, mechanical and injective — the same category as the boundary's transcription
(`cnl.md` §1). It makes no choices: every atom in the description becomes exactly one `Pat`, and there
is no input for which the assembler must decide between two readings. If that ever stops being true,
this module has started doing semantics.

⚠ **This is where `model.md` §12 invariant 2 will break** — *nesting → tunnel → nesting round-trips.*
The failure mode migrated rather than vanishing: `ugm` died of every rule juggling scope, and here the
assembler owns it. One place instead of every rule is a real reduction, but it is the same class of bug.
"""
from __future__ import annotations

from dataclasses import dataclass

from .circuit import Circuit, Statement
from .graph import Graph, Node
from .match import Pat
from .unit import Emit, Stamp, Unit, rule


def _roles(g: Graph, occ: Node, name: str) -> list:
    """Targets of `occ`'s `name` roles, ordered by the `index` attribute on the role node."""
    found = []
    for r in g.out(occ):
        if g.attr(r, "name") != name:
            continue
        for target in g.out(r):
            found.append((g.attr(r, "index"), target))
    found.sort(key=lambda p: (p[0] is None, p[0]))
    return [t for _, t in found]


def _one(g: Graph, occ: Node, name: str) -> Node | None:
    got = _roles(g, occ, name)
    return got[0] if got else None


def _kind(g: Graph, n: Node) -> str | None:
    return g.attr(n, "name")


# -- decoding ---------------------------------------------------------------------------------

def _pat(g: Graph, n: Node) -> Pat:
    attrs = tuple(sorted((g.attr(c, "key"), g.attr(c, "value")) for c in _roles(g, n, "constraint")))
    graded = tuple(g.attr(x, "key") for x in _roles(g, n, "graded"))
    out = tuple(_pat(g, c) for c in _roles(g, n, "out"))
    return Pat(var=g.attr(n, "var"), attrs=attrs, graded=graded, out=out)


def _effect(g: Graph, n: Node):
    kind = _kind(g, n)
    if kind == "mint":
        args = tuple((g.attr(a, "role"), g.attr(a, "var")) for a in _roles(g, n, "arg"))
        return Emit(g.attr(n, "occurrence"), roles=args, graded=g.attr(n, "graded"))
    if kind == "stamp":
        return Stamp(g.attr(n, "target"), g.attr(n, "attr"), g.attr(n, "band"))
    raise ValueError(f"undescribed effect kind {kind!r}")


# -- assembly ---------------------------------------------------------------------------------

@dataclass
class Assembly:
    """A circuit, plus the handles the description named. `by_label` is the only way back from the
    description to the built thing, and it holds **statements** — never their interiors (§6)."""

    circuit: Circuit
    by_label: dict
    entries: list

    def feed(self, label: str, value: Graph):
        return self.circuit.feed(self.by_label[label], value)

    def port(self, label: str):
        return self.by_label[label].end


def assemble(desc: Graph) -> Assembly:
    """Build a circuit from a wiring-register graph. Nothing is inferred; if it is not described, it is
    not wired."""
    circuit = Circuit()
    built: dict = {}
    by_label: dict = {}

    statements = [n for n in desc.nodes if _kind(desc, n) == "statement"]
    nested = {t for s in statements for t in _roles(desc, s, "step")}
    roots = [s for s in statements if s not in nested]

    def build(n: Node):
        if n in built:
            return built[n]
        kind = _kind(desc, n)
        if kind == "unit":
            pattern = tuple(_pat(desc, p) for p in _roles(desc, n, "pattern"))
            effects = tuple(_effect(desc, e) for e in _roles(desc, n, "effect"))
            obj = rule(desc.attr(n, "label") or "unit", pattern, *effects,
                       theta=desc.attr(n, "theta"))
        elif kind == "statement":
            steps = tuple(build(s) for s in _roles(desc, n, "step"))
            obj = circuit.statement(desc.attr(n, "label") or "statement", *steps)
            by_label[desc.attr(n, "label")] = obj
        else:
            raise ValueError(f"{kind!r} is not a step kind")
        built[n] = obj
        return obj

    for r in roots:
        build(r)

    for w in [n for n in desc.nodes if _kind(desc, n) == "wire"]:
        src, dst = _one(desc, w, "from"), _one(desc, w, "to")
        s = build(src)
        # A described wire out of a bare unit is handed to `wire` unchanged, so the seal refuses it
        # there rather than here — one rule, one place (§6).
        circuit.wire(s.end if isinstance(s, Statement) else s, build(dst))

    for wb in [n for n in desc.nodes if _kind(desc, n) == "write-back"]:
        p = build(_one(desc, wb, "port"))
        if not isinstance(p, Statement):
            raise ValueError("write-back names a statement's end marker, never a unit")
        circuit.write_back(p.end)

    entries = [desc.attr(_one(desc, e, "at"), "label")
               for e in desc.nodes if _kind(desc, e) == "entry"]

    return Assembly(circuit, by_label, entries)


__all__ = ["assemble", "Assembly"]
