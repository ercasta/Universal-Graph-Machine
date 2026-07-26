"""RULES AS SUBGRAPHS — the bridge from a VALUE to network STRUCTURE (§24.7).

> **The user's observation, and it decides an architecture:** *"The OUTPUT of the system should be usable
> to create more network wirings, because the discourse could lead to new rules. So either we convert
> subgraphs (output) to CNL and then ingest it back, or we also need a transpiler from output graph to
> network."*

**The round-trip through CNL is not merely expensive — it is UNSOUND on this substrate.** Rendering a
subgraph to text means naming its nodes, and re-ingesting means resolving those names back to nodes. That
is exactly §22.5's forbidden interning-by-name and §24.3's *"discourse reference is not lookup"*: two
independently minted nodes called `mary` would fuse, and §5 records identity inheritance as a CORRECTNESS
requirement, not a cost. **Text is a lossy channel for identity, so the loop must not pass through it.**

So: a transpiler from graph to structure. **And it is not a SECOND transpiler — it is the ONLY one**, which
is the point:

    CNL text ──parse──▶ rule-shaped SUBGRAPH ──declare──▶ template in the library
    a unit's output ─────────────────────────▶ (same path from here)

**The CNL front-end must therefore target a SUBGRAPH, never the `Net` API.** If it targeted `Net` directly,
output→network would need a second implementation and the two would drift — the system would be able to
say things it could not learn. Pinning this contract BEFORE the grammar exists is the whole reason to
decide it now.

**WHAT MAY CROSS, AND WHAT MAY NOT.** §16.6 settled this and the wording matters: *the discourse adds
SHAPES, not wiring policy*. This bridge declares TEMPLATES. It never wires — the assembler still decides
who feeds whom (§3b's spawn policy), and §8's line stays absolute: **units never touch wiring.** A rule
authored by a unit is a shape; a unit choosing its own consumers would be policy, and is refused by
construction here because nothing in this module wires anything.

**THE ENCODING REUSES `reify`'s VOCABULARY.** An atom of a pattern is described exactly as a fact is:
`<of_s>/<of_p>/<of_o>`. The only difference is that a slot may be a VARIABLE — a node marked `<var>` —
which is [[learning-arc]]'s *"only the FLAT reification is learner-writable"*, arriving as a consequence
rather than as a design.
"""
from __future__ import annotations

from .match import Absent, Mint, Triple, Var
from .reify import OF_O, OF_P, OF_S
from .value import Fact, Node, Subgraph, mint
from .vocab import role

IS_A = role("<is_a>")
RULE = role("<rule>")
VAR = role("<var>")
MINT = role("<mint>")
ABSENT = role("<absent>")
LHS = role("<lhs>")
RHS = role("<rhs>")
NAMED = role("<named>")          # rule handle -> a node whose LABEL names the template


class NotARule(ValueError):
    """The subgraph does not describe a well-formed rule. **Refusal is first-class** — intake must be
    closed under composition (reasoned ∪ refused, never silently mis-mapped), and a bridge that guesses
    is how [[book-corpus-experiment]]'s optimistic bias gets in."""


# -- value -> structure ---------------------------------------------------------------------------------

def _slot(view: Subgraph, n: Node):
    """A pattern slot: a variable, a mint, or a ground node."""
    if Fact(n, IS_A, VAR) in view:
        return Var(n.name)
    if Fact(n, IS_A, MINT) in view:
        return Mint(n.name)
    return n


def _atom(view: Subgraph, a: Node):
    s = p = o = None
    for t in view.by_pred(OF_S):
        if t.s == a:
            s = t.o
    for t in view.by_pred(OF_P):
        if t.s == a:
            p = t.o
    for t in view.by_pred(OF_O):
        if t.s == a:
            o = t.o
    if None in (s, p, o):
        raise NotARule(f"atom {a!r} is missing a slot")
    tri = Triple(_slot(view, s), _slot(view, p), _slot(view, o))
    return Absent(tri) if Fact(a, IS_A, ABSENT) in view else tri


def rules_in(view: Subgraph) -> list:
    """Every rule the value describes, as `(name, lhs, rhs)`. Bounded local enumeration — the value is
    what a unit was handed, so this reads no more than the unit itself could."""
    out = []
    for t in view.by_pred(IS_A):
        if t.o != RULE:
            continue
        r = t.s
        lhs = tuple(_atom(view, x.o) for x in sorted(view.by_pred(LHS), key=repr) if x.s == r)
        rhs = tuple(_atom(view, x.o) for x in sorted(view.by_pred(RHS), key=repr) if x.s == r)
        if not rhs:
            raise NotARule(f"rule {r!r} has no head")
        name = next((x.o.name for x in view.by_pred(NAMED) if x.s == r), r.name)
        out.append((name, lhs, rhs))
    return out


def declare_all(net, view: Subgraph) -> list:
    """Declare every rule the value describes. **Templates only — this never wires** (§8, §16.6).

    Idempotent by name, because [[extend-equals-rebuild]] requires that saying the same thing twice does
    not double the network."""
    added = []
    for name, lhs, rhs in rules_in(view):
        if name in net.library:
            continue
        net.declare(name, lhs, rhs)
        added.append(name)
    return added


# -- structure -> value ---------------------------------------------------------------------------------

def _derived(owner: Node, tag: int, name: str) -> Node:
    """A node DERIVED from the rule's key rather than minted. Negative nids mark structural nodes.

    Without this, encoding one rule twice yields unequal values and a DERIVED rule never settles —
    §22.8's standing rule (*anything minted per run must be keyed*) reaching a third construct."""
    return Node(-(abs(owner.nid) * 100000 + tag), name)


def _slot_facts(slot, seen: dict, owner: Node):
    """Encode a slot. One node per distinct variable, DERIVED from the rule key so the encoding is
    stable — and per-rule, so two rules using `?x` never share a node (variable scoping, structurally)."""
    if isinstance(slot, (Var, Mint)):
        key = (type(slot).__name__, slot.name)
        n = seen.get(key)
        if n is None:
            n = seen[key] = _derived(owner, 10000 + len(seen), slot.name)
        return n, [Fact(n, IS_A, VAR if isinstance(slot, Var) else MINT)]
    return slot, []


def encode(name: str, lhs, rhs, key: Node | None = None) -> Subgraph:
    """A rule as a value. `key` names the rule node — supply it for a DERIVED rule, or re-encoding the
    same rule yields a different value every time and nothing converges."""
    r = key if key is not None else mint(name)
    facts = [Fact(r, IS_A, RULE), Fact(r, NAMED, _derived(r, 99999, name))]
    seen: dict = {}
    for side, atoms in ((LHS, lhs), (RHS, rhs)):
        for i, atom in enumerate(atoms):
            neg = isinstance(atom, Absent)
            tri = atom.atom if neg else atom
            a = _derived(r, (0 if side is LHS else 500) + i, f"{name}#a{i}")
            facts.append(Fact(r, side, a))
            if neg:
                facts.append(Fact(a, IS_A, ABSENT))
            for slot_role, slot in ((OF_S, tri.s), (OF_P, tri.p), (OF_O, tri.o)):
                n, extra = _slot_facts(slot, seen, r)
                facts.append(Fact(a, slot_role, n))
                facts.extend(extra)
    return Subgraph(facts)


__all__ = ["IS_A", "RULE", "VAR", "MINT", "ABSENT", "LHS", "RHS", "NAMED", "NotARule",
           "rules_in", "declare_all", "encode"]
