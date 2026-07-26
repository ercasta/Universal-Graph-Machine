"""MATCHING — a unit's LHS against the value it was handed (`docs/design/substrate_inversion.md` §14).

This is where variables get bound, and it is the whole reason the substrate is not NETL. NETL propagated a
MARKER — one bit at a node — which does inheritance perfectly and cannot correlate two matches, because
there is nowhere to record WHICH `?y` a given `?x` went with; a two-place join becomes a cross-product.
Here a unit's state is a SUBGRAPH, so **the binding IS the datum**: the value of `?y` is simply a node in
the value. There is no separate binding mechanism that could be got wrong.

Spiked before the package existed (`bench/spike_substrate_inversion_binding.py`, 6/6): markers answer 4 on
the canonical two-place join, of which 2 are false; this answers exactly 2.

NEGATION HERE IS THE EXACT KIND (§6a). `Absent` asks whether a fact is missing from the value on the wire
— a FINISHED value, whatever upstream produced — so it is decidable immediately, with no drain, no
fixpoint and no fuel. That is the negation this substrate gets for free. The other kind ("P is not
derivable AT ALL") is open, semi-decidable, and answered by fuel; it does not live in this module, and
conflating the two is how a resource limit silently becomes a claim about the world.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from .value import Fact, Node, Subgraph, mint as _mint


@dataclass(frozen=True)
class Var:
    name: str

    def __repr__(self) -> str:
        return f"?{self.name}"


@dataclass(frozen=True)
class Triple:
    """A pattern atom. **Every slot is uniform** (§22.3, §22.5): each of `s`, `p`, `o` is a `Var` to bind
    or a `Node` to match. A `str` in the predicate slot is resolved through the form set at construction.

    That uniformity IS the predicate variable — `?s ?p ?o` needs no new machinery, which is why §17.E's
    recorded hole is dissolved rather than filled."""
    s: object
    p: object
    o: object

    def __post_init__(self) -> None:
        if not isinstance(self.p, (Node, Var)):
            from .vocab import role
            object.__setattr__(self, "p", role(self.p))

    def vars(self) -> frozenset:
        return frozenset(t for t in (self.s, self.p, self.o) if isinstance(t, Var))

    def mints(self) -> frozenset:
        return frozenset(t for t in (self.s, self.p, self.o) if isinstance(t, Mint))

    def __repr__(self) -> str:
        pn = self.p.name if isinstance(self.p, Node) else self.p
        return f"({self.s} {pn} {self.o})"


@dataclass(frozen=True)
class Mint:
    """A HEAD-ONLY term: mint a node, **keyed on the match that produced it** ([[skolem-minting-lhs-keyed]]).

    This is the primitive three separate things were blocked on, and the convergence is the argument for
    building it:

    * §22.7 — `band.inherit` mints a handle per graded conclusion, so degree inheritance had to stay
      Python instead of being the one generic RULE §16.5 designed it as;
    * §22.8 — a DERIVED denial mints a `not` node, so it could not be derived at all without diverging;
    * §20.1(a) — the trace's firing nodes hit the same wall first, and were fixed by hand.

    All three are the standing rule §22.8 states: **anything minted per run must be KEYED, or it destroys
    the fixpoint it is annotating.** `Mint` is that rule made into a construct rather than a discipline —
    the node is a function of (unit, head position, binding), so re-running a unit on the same match
    yields the SAME node and the output stops changing.

    An RHS-only `Var` remains refused (unsound — it asserts an unbound existential). A `Mint` is not a
    variable: it names a FUNCTION of the binding, which is exactly the supported skolem form."""
    name: str

    def vars(self) -> frozenset:
        return frozenset()

    def __repr__(self) -> str:
        return f"{self.name}?"


@dataclass(frozen=True)
class Absent:
    """NAF over the value on the wire — exact, immediate, no fuel (§6a).

    SAFETY: every variable in the negated atom must already be bound by the positive atoms, exactly as in
    datalog. An unsafe `Absent` asks an unbounded question of a bounded value, which has no answer; it
    raises rather than guessing, because the alternative is a rule whose meaning depends on evaluation
    order."""
    atom: Triple

    def __repr__(self) -> str:
        return f"not {self.atom}"


class UnsafePattern(ValueError):
    """A variable appears only in a negated atom, or only in the head."""


def check_safety(lhs: tuple, rhs: tuple = ()) -> None:
    """Raise unless every variable is BOUND by a positive body atom. Checked once, at construction, so a
    unit cannot be built with a meaning that depends on the order its patterns happen to be tried."""
    bound: frozenset = frozenset()
    for pat in lhs:
        if isinstance(pat, Triple):
            bound |= pat.vars()
    for pat in lhs:
        if isinstance(pat, Absent):
            loose = pat.atom.vars() - bound
            if loose:
                raise UnsafePattern(
                    f"{pat!r}: {sorted(v.name for v in loose)} appear only under negation — a negated "
                    f"atom may only test variables the positive body has already bound")
    for head in rhs:
        loose = head.vars() - bound
        if loose:
            raise UnsafePattern(
                f"{head!r}: {sorted(v.name for v in loose)} appear only in the head — this substrate has "
                f"no minting rule yet, so a head variable must be bound by the body")


def _bind(spec: object, n: Node, b: dict) -> bool:
    """Unify one slot. THE LINE THAT MATTERS: a bound variable is compared by node IDENTITY, never by
    name (§5). Joining by name fuses two independently-minted `mary`s and fabricates a conclusion."""
    if isinstance(spec, Var):
        prev = b.get(spec)
        if prev is not None:
            return prev == n                        # Node equality is nid equality — identity
        b[spec] = n
        return True
    return spec == n


def solve(lhs: tuple, view: Subgraph) -> list:
    """Every binding of `lhs` in `view`. Positive atoms join first (each seeded from the value's own
    bounded per-predicate index); `Absent` atoms filter the surviving bindings."""
    positives = tuple(p for p in lhs if isinstance(p, Triple))
    negatives = tuple(p for p in lhs if isinstance(p, Absent))

    def go(rest: tuple, b: dict) -> Iterator[dict]:
        if not rest:
            yield dict(b)
            return
        atom, tail = rest[0], rest[1:]
        # A GROUND role still uses the value's index; a VARIABLE role scans the value. The scan is
        # bounded local enumeration over one wire (§1 permits it) — but note what it costs: a `?s ?p ?o`
        # rule wakes on EVERYTHING (§22.5, measured). The generic rule that avoids a clause per template
        # is the same one that makes "wake broadly" mean "wake always".
        cands = view.by_pred(atom.p) if isinstance(atom.p, Node) else view.facts
        for f in cands:
            b2 = dict(b)
            if _bind(atom.s, f.s, b2) and _bind(atom.p, f.p, b2) and _bind(atom.o, f.o, b2):
                yield from go(tail, b2)

    out = []
    for b in go(positives, {}):
        if all(not _holds(n.atom, b, view) for n in negatives):
            out.append(b)
    return out


def _resolve(slot, b: dict):
    return b[slot] if isinstance(slot, Var) else slot


def _holds(atom: Triple, b: dict, view: Subgraph) -> bool:
    return Fact(_resolve(atom.s, b), _resolve(atom.p, b), _resolve(atom.o, b)) in view


def matched(atom: Triple, f: Fact, b: dict) -> bool:
    """Did `f` supply `atom` under binding `b`? — used to record a firing's CONSUMED PREMISES.

    Why this is recorded rather than recovered: a conclusion's annotations (a band, an attribution) are
    inherited from the facts that PRODUCED it, and once a rule emits only its conclusion there is no
    afterwards in which to work out which those were. Same lesson as `Unit.derived` — a derivation is a
    fact about a RUN (§15.2) — arrived at from the inheritance side rather than the cycle side."""
    return (f.s == _resolve(atom.s, b) and f.p == _resolve(atom.p, b) and f.o == _resolve(atom.o, b))


def ground(head: Triple, b: dict, memo: dict | None = None, owner: str = "") -> Fact:
    """Instantiate a head atom under a binding. Every `Var` slot is bound — `check_safety` guarantees it —
    and every `Mint` slot resolves through `memo`, KEYED ON THE BINDING.

    `memo` is the minting unit's OWN state, not a global: two units that mint for the same match get
    different nodes, which is correct, because they are different derivations. Convergence between them
    is a separate question ([[skolem-minting-lhs-keyed]]'s defining-relation reuse) and is not solved
    here."""
    return Fact(_mint_or_resolve(head.s, b, memo, owner, 0),
                _mint_or_resolve(head.p, b, memo, owner, 1),
                _mint_or_resolve(head.o, b, memo, owner, 2))


def _mint_or_resolve(slot, b: dict, memo: dict | None, owner: str, pos: int):
    if not isinstance(slot, Mint):
        return _resolve(slot, b)
    if memo is None:
        raise UnsafePattern(f"{slot!r}: a minting head needs a keyed memo — see `Mint`")
    key = (owner, pos, slot.name, tuple(sorted((v.name, n.nid) for v, n in b.items())))
    node = memo.get(key)
    if node is None:
        node = _mint(slot.name)
        memo[key] = node
    return node
