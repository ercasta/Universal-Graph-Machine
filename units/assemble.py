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

from dataclasses import dataclass, field

from .circuit import Circuit, Statement
from .graph import Graph, Node
from .match import Absent, AttrVar, Pat
from .unit import Emit, Same, ScopePointer, Stamp, Unit, rule


def roles_of(g: Graph, occ: Node, name: str) -> list:
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
    got = roles_of(g, occ, name)
    return got[0] if got else None


def kind_of(g: Graph, n: Node) -> str | None:
    return g.attr(n, "name")


# -- decoding ---------------------------------------------------------------------------------

def decode_pattern(g: Graph, n: Node):
    """One described conjunct — an atom, or an `absent` guard over atoms."""
    if kind_of(g, n) == "absent":
        return Absent(tuple(decode_pattern(g, a) for a in roles_of(g, n, "atom")))
    attrs = tuple(sorted(((g.attr(c, "key"),
                           AttrVar(g.attr(c, "var")) if g.attr(c, "var") is not None
                           else g.attr(c, "value"))
                          for c in roles_of(g, n, "constraint")), key=lambda kv: kv[0]))
    graded = tuple(g.attr(x, "key") for x in roles_of(g, n, "graded"))
    out = tuple(decode_pattern(g, c) for c in roles_of(g, n, "out"))
    return Pat(var=g.attr(n, "var"), attrs=attrs, graded=graded, out=out)


def _effect(g: Graph, n: Node):
    kind = kind_of(g, n)
    if kind == "mint":
        args = tuple((g.attr(a, "role"), g.attr(a, "var")) for a in roles_of(g, n, "arg"))
        return Emit(g.attr(n, "occurrence"), roles=args, graded=g.attr(n, "graded"))
    if kind == "stamp":
        return Stamp(g.attr(n, "target"), g.attr(n, "attr"), g.attr(n, "band"))
    if kind == "same":
        return Same(g.attr(n, "left"), g.attr(n, "right"))
    raise ValueError(f"undescribed effect kind {kind!r}")


# -- assembly ---------------------------------------------------------------------------------

@dataclass
class Assembly:
    """A circuit, plus the handles the description named. `by_label` is the only way back from the
    description to the built thing, and it holds **statements** — never their interiors (§6)."""

    circuit: Circuit
    by_label: dict
    entries: list
    scopes: dict = field(default_factory=dict)   # declared scope name -> ScopePointer

    def feed(self, label: str, value: Graph):
        return self.circuit.feed(self.by_label[label], value)

    def port(self, label: str):
        return self.by_label[label].end


def assemble(desc: Graph, *, only: tuple | None = None, cooldown=None, under=None,
             known_scopes: dict | None = None) -> Assembly:
    """Build a circuit from a wiring-register graph. Nothing is inferred; if it is not described, it is
    not wired.

    `only` restricts assembly to the named root statements — §7 step 2 mints units **for the rules that
    came to mind**, not for the library. Passing `None` builds everything, which is the convenience a
    test wants and never what a step does.

    `under` is the containment this whole assembly runs inside — how the loop instantiates a general
    rule inside an existing assumption so that its conclusions land there (`unit.ScopePointer`).

    `known_scopes` maps a declared scope label to the node already standing for it **in the full
    world**. It has to come from outside: the circuit is rebuilt every step, and a nested scope is
    hidden from the base projection by its own parent, so a statement re-assembling at base could not
    find the assumption it made last step and would mint a fresh one every time."""
    circuit = Circuit()
    built: dict = {}
    by_label: dict = {}

    statements = [n for n in desc.nodes if kind_of(desc, n) == "statement"]
    nested = {t for s in statements for t in roles_of(desc, s, "step")}
    roots = [s for s in statements if s not in nested]
    if only is not None:
        roots = [s for s in roots if desc.attr(s, "label") in only]

    scopes: dict = {}

    def build(n: Node, under=None):
        """`under` is the innermost `ScopePointer` in force. **This is the assembler owning
        nesting → tunnel → nesting** (§12 invariant 2), which is precisely where §6 says the failure
        mode migrated to — one place instead of every rule, but the same class of bug."""
        if n in built:
            return built[n]
        kind = kind_of(desc, n)
        if kind == "unit":
            pattern = tuple(decode_pattern(desc, p) for p in roles_of(desc, n, "pattern"))
            effects = tuple(_effect(desc, e) for e in roles_of(desc, n, "effect"))
            obj = rule(desc.attr(n, "label") or "unit", pattern, *effects,
                       theta=desc.attr(n, "theta"), cooldown=cooldown, under=under)
        elif kind == "statement":
            declared = desc.attr(n, "scope")
            # A guard does not discard the context — it moves the pointer one level deeper.
            inner = (ScopePointer(declared, under, node=(known_scopes or {}).get(declared))
                     if declared else under)
            if declared:
                scopes[declared] = inner
            steps = tuple(build(s, inner) for s in roles_of(desc, n, "step"))
            obj = circuit.statement(desc.attr(n, "label") or "statement", *steps)
            by_label[desc.attr(n, "label")] = obj
        else:
            raise ValueError(f"{kind!r} is not a step kind")
        built[n] = obj
        return obj

    for r in roots:
        build(r, under)

    def described(n: Node) -> bool:
        """A wire whose endpoint did not come to mind is not wired. Without this, `only` would leak:
        one retrieved statement could drag an unretrieved one into the circuit through a wire, and the
        step would fire a rule that was never recalled."""
        return only is None or n in built

    for w in [n for n in desc.nodes if kind_of(desc, n) == "wire"]:
        src, dst = _one(desc, w, "from"), _one(desc, w, "to")
        if not (described(src) and described(dst)):
            continue
        s = build(src)
        # A described wire out of a bare unit is handed to `wire` unchanged, so the seal refuses it
        # there rather than here — one rule, one place (§6).
        circuit.wire(s.end if isinstance(s, Statement) else s, build(dst))

    for wb in [n for n in desc.nodes if kind_of(desc, n) == "write-back"]:
        port_node = _one(desc, wb, "port")
        if not described(port_node):
            continue
        p = build(port_node)
        if not isinstance(p, Statement):
            raise ValueError("write-back names a statement's end marker, never a unit")
        circuit.write_back(p.end)

    entries = [desc.attr(_one(desc, e, "at"), "label")
               for e in desc.nodes if kind_of(desc, e) == "entry"]

    return Assembly(circuit, by_label, entries, scopes)


__all__ = ["assemble", "Assembly", "roles_of", "kind_of", "decode_pattern"]
