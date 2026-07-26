"""SPIKE — does PREDICATE-AS-NODE dissolve §17.E's predicate variable? (`substrate_inversion.md` §22.3)

§22.4 puts this first for one reason: **if `?s ?p ?o` does not fall out, the rest of §22 is built on sand.**
§17.E recorded the predicate variable as the one hole, hit twice independently in two days (coref-merge as
a unit; entity boundaries as data) and a third time by §22.3. It recommended BUILDING the primitive. The
user's role-node proposal would instead REMOVE THE NEED for it — a predicate that is a node makes `?p` an
ordinary node variable, with no new machinery anywhere.

Written as a standalone model rather than against `units/`, because `match.Triple.p` is a `str` and the
question is exactly whether it should be. What gets copied here is evidence about what the change costs:
**the matcher below is the existing one with the special case for `p` DELETED**, and nothing else.

Cases 5-8 are attempts to break it. Two of them find the price.

    python bench/spike_predicate_as_node.py
"""
from __future__ import annotations

import itertools
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PASS, FAIL = [], []


def check(name: str, ok: bool, detail: str = "") -> None:
    (PASS if ok else FAIL).append(name)
    line = f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   {detail}" if detail else "")
    enc = sys.stdout.encoding or "utf-8"
    print(line.encode(enc, "replace").decode(enc))       # the console is cp1252; the source is not


# ======================================================================================================
# THE MODEL — `units/value.py` + `units/match.py` with the predicate's special case removed.
# ======================================================================================================

_NID = itertools.count(1)


@dataclass(frozen=True)
class Node:
    nid: int
    name: str

    def __repr__(self) -> str:
        return f"{self.name}#{self.nid}"


def mint(name: str = "") -> Node:
    return Node(next(_NID), name)


@dataclass(frozen=True)
class Fact:
    """S-P-O where **ALL THREE SLOTS ARE NODES.** The only change from `units/value.Fact`."""
    s: Node
    p: Node
    o: Node

    def __repr__(self) -> str:
        return f"{self.s} {self.p} {self.o}"


class Graph:
    """A value on a wire. The per-predicate index now keys on the ROLE NODE's identity rather than on a
    string — note it stays CRISP, and §22.3 assumed it would have to go graded immediately. It does not:
    identity indexing works as long as the role node is SHARED, which §22.1 below is about."""

    def __init__(self, facts=()):
        self.facts = frozenset(facts)
        self._idx = None

    def by_pred(self, p: Node) -> tuple:
        if self._idx is None:
            d = {}
            for f in self.facts:
                d.setdefault(f.p, []).append(f)
            self._idx = {k: tuple(v) for k, v in d.items()}
        return self._idx.get(p, ())

    def preds(self) -> frozenset:
        self.by_pred(None)
        return frozenset(self._idx or ())

    def __iter__(self):
        return iter(self.facts)

    def __contains__(self, f):
        return f in self.facts

    def __len__(self):
        return len(self.facts)

    def __repr__(self):
        return "{" + ", ".join(sorted(repr(f) for f in self.facts)) + "}"


@dataclass(frozen=True)
class Var:
    name: str

    def __repr__(self):
        return f"?{self.name}"


@dataclass(frozen=True)
class Pat:
    """A pattern atom. **Every slot is uniform now** — `Var` or `Node`, including `p`."""
    s: object
    p: object
    o: object

    def vars(self) -> frozenset:
        return frozenset(t for t in (self.s, self.p, self.o) if isinstance(t, Var))

    def __repr__(self):
        return f"({self.s} {self.p} {self.o})"


@dataclass(frozen=True)
class NotEq:
    """`?p != k`. Not part of the substrate — added HERE only to measure what case 2e would cost to fix
    the obvious way, so the cost is visible rather than assumed."""
    var: Var
    node: Node

    def vars(self) -> frozenset:
        return frozenset({self.var})


class Unsafe(ValueError):
    pass


def check_safety(lhs, rhs=()) -> None:
    bound = frozenset().union(*[p.vars() for p in lhs]) if lhs else frozenset()
    for h in rhs:
        loose = h.vars() - bound
        if loose:
            raise Unsafe(f"{h!r}: {sorted(v.name for v in loose)} unbound in the head")


def _bind(spec, n: Node, b: dict) -> bool:
    if isinstance(spec, Var):
        prev = b.get(spec)
        if prev is not None:
            return prev == n
        b[spec] = n
        return True
    return spec == n


def solve(lhs, view: Graph) -> list:
    """**THE WHOLE DIFF.** `units/match.solve` seeds each atom from `view.by_pred(atom.p)`, which requires
    a ground predicate. Here a ground `p` still uses the index; a VARIABLE `p` scans the value — bounded
    local enumeration over one wire's value, which §1 permits and which is what `by_pred` was always
    doing one level down."""
    def go(rest, b):
        if not rest:
            yield dict(b)
            return
        atom, tail = rest[0], rest[1:]
        if isinstance(atom, NotEq):
            if b.get(atom.var) != atom.node:
                yield from go(tail, b)
            return
        cands = view.by_pred(atom.p) if isinstance(atom.p, Node) else view.facts
        for f in cands:
            b2 = dict(b)
            if _bind(atom.s, f.s, b2) and _bind(atom.p, f.p, b2) and _bind(atom.o, f.o, b2):
                yield from go(tail, b2)

    positives = tuple(a for a in lhs if not isinstance(a, NotEq))
    return list(go(positives + tuple(a for a in lhs if isinstance(a, NotEq)), {}))


def ground(h: Pat, b: dict) -> Fact:
    g = lambda t: b[t] if isinstance(t, Var) else t          # noqa: E731
    return Fact(g(h.s), g(h.p), g(h.o))


def derive(lhs, rhs, view: Graph) -> Graph:
    check_safety(lhs, rhs)
    return Graph(ground(h, b) for b in solve(lhs, view) for h in rhs)


# ======================================================================================================
print("\n== 1. §17.E's predicate variable: does `?s ?p ?o` just fall out? ==")

# ROLE NODES. Minted ONCE — §22.1 below is about who mints them.
likes, is_a, same_as = mint("likes"), mint("is_a"), mint("same_as")
jack, mary, rich = mint("jack"), mint("mary"), mint("rich")

world = Graph([Fact(jack, likes, mary), Fact(mary, is_a, rich)])
S, P, O = Var("s"), Var("p"), Var("o")

all_of_it = solve([Pat(S, P, O)], world)
check("1a `?s ?p ?o` is EXPRESSIBLE — no new primitive, `?p` is an ordinary node variable",
      len(all_of_it) == 2, f"{len(all_of_it)} bindings")
check("1b and it BINDS the predicate like any other slot",
      {b[P] for b in all_of_it} == {likes, is_a})

# the thing `units/` cannot say at all today: a rule whose HEAD carries a bound predicate variable
swapped = derive([Pat(S, P, O)], [Pat(O, P, S)], world)
check("1c a predicate variable survives into the HEAD (safety unchanged: bound by the body)",
      Fact(mary, likes, jack) in swapped)
try:
    derive([Pat(S, is_a, O)], [Pat(S, P, O)], world)
    check("1d an UNBOUND head predicate is still refused", False)
except Unsafe:
    check("1d an UNBOUND head predicate is still refused — one uniform safety rule, not a new one", True)

# ======================================================================================================
print("\n== 2. §17.D: coref-merge as a UNIT, generically ==")

# §17.D: "nothing may conclude 'same entity' FROM an id. A coref-merge unit DECIDES; the ids downstream
# merely record that decision." Blocked today because it needs a generic substitution. Here:
mary2 = mint("mary")                                  # a second, independently minted mary
coref_world = Graph([Fact(jack, likes, mary2), Fact(mary2, is_a, rich), Fact(mary, same_as, mary2)])

A, B = Var("a"), Var("b")
COREF_SUBJ = ([Pat(A, same_as, B), Pat(B, P, O)], [Pat(A, P, O)])
COREF_OBJ = ([Pat(A, same_as, B), Pat(S, P, B)], [Pat(S, P, A)])

merged = derive(*COREF_SUBJ, coref_world)
check("2a ONE generic rule substitutes B->A in subject position",
      Fact(mary, is_a, rich) in merged, repr(merged))
check("2b and it did NOT need a clause per template — `form_inventory.md` §9's explosion avoided",
      len(COREF_SUBJ[0]) == 2)
merged_o = derive(*COREF_OBJ, coref_world)
check("2c the object-position twin is the same shape",
      Fact(jack, likes, mary) in merged_o or Fact(jack, likes, mary2) in merged_o, repr(merged_o))

# §17.D's reconciliation: identity is DECIDED, never read off an id.
check("2d nothing concluded sameness FROM an id — the `same_as` fact is an input, not an inference",
      Fact(mary, same_as, mary2) in coref_world)

# ⚠ FOUND HERE, and the first version of this case only failed because of it. A `?s ?p ?o` rule has NO
# PREDICATE TO KEY ON, so it matches the very `same_as` fact that LICENSES it, and derives a reflexive
# junk fact. This is not a coref bug — it is the general shape: **a generic rule cannot tell the object
# language from the control vocabulary that drives it.**
junk = Fact(mary, same_as, mary) in merged_o or Fact(mary2, same_as, mary2) in merged_o
check("2e ⚠ THE WILDCARD CONSUMES ITS OWN CONTROL PREDICATE — a reflexive `same_as` derived from nothing",
      junk, repr(merged_o))

guarded = derive([Pat(A, same_as, B), Pat(S, P, B), NotEq(P, same_as)], [Pat(S, P, A)], coref_world)
check("2f an inequality guard fixes it — but that is a NEW primitive the substrate does not have",
      not any(f.p == same_as for f in guarded), repr(guarded))
check("2g ⭐ and the OTHER fix is the one §20 already built: put control on ITS OWN WIRE",
      True, "same class as trace_leaks — a wildcard makes every predicate ambient")

# ======================================================================================================
print("\n== 3. §17.E: facts occupying node slots (entity boundaries as data) ==")

# The second requirement that bottomed out in the same hole. Reify a fact as a node and describe it —
# note this is EXACTLY the shape `units/trace.py` already uses for a conclusion handle.
subj, role, obj, member = mint("<subj>"), mint("<role>"), mint("<obj>"), mint("<member>")
boundary = mint("boundary")
f1 = Fact(jack, likes, mary)
h1 = mint("f")
reified = Graph([f1,
                 Fact(h1, subj, f1.s), Fact(h1, role, f1.p), Fact(h1, obj, f1.o),
                 Fact(boundary, member, h1)])

hits = solve([Pat(Var("h"), subj, Var("x")), Pat(Var("h"), role, Var("r")), Pat(Var("h"), obj, Var("y"))],
             reified)
check("3a a fact occupies a node slot — reification needs no new construct either",
      len(hits) == 1 and hits[0][Var("x")] == jack and hits[0][Var("r")] == likes)
check("3b membership over reified facts is an ordinary fact (§17.E's entity boundaries)",
      Fact(boundary, member, h1) in reified)
check("3c ⭐ and this is the SAME shape `units/trace.py` already uses for a conclusion handle",
      True, "trace.describe() = subject/predicate/object over a minted handle")

# ======================================================================================================
print("\n== 4. BREAK: does the INDEX survive, or must it go graded immediately? ==")

# §22.3 assumed all five predicate-keyed mechanisms go graded at once. Measure it.
big = Graph([Fact(mint("e"), likes, mint("e")) for _ in range(50)] +
            [Fact(mint("e"), is_a, mint("e")) for _ in range(50)])
crisp = len(big.by_pred(likes))
wildcard = len(solve([Pat(S, P, O)], big))
check("4a a GROUND role node still indexes crisply — identity, not similarity, and no registry",
      crisp == 50, f"{crisp} candidates for a ground role")
check("4b ⚠ but a PREDICATE-VARIABLE rule is a WILDCARD — it wakes on the whole value",
      wildcard == 100, f"{wildcard} bindings, i.e. everything")
check("4c so §22.3 rows 1-4 do NOT have to go graded to get §17.E — the two changes are SEPARABLE",
      crisp == 50 and wildcard == 100)

# ======================================================================================================
print("\n== 5. BREAK: two independently minted role nodes — where does the price land? ==")

likes2 = mint("likes")                                # a NOVEL role, same surface word
novel = Graph([Fact(jack, likes2, mary)])
check("5a a fresh role node does NOT match an existing one — namelessness, applied to roles too",
      len(solve([Pat(S, likes, O)], novel)) == 0)
check("5b ⭐ SO ROLE IDENTITY MUST COME FROM THE FORM SET, not from interning per utterance",
      True, "a registry keyed on the surface word would be §3's forbidden second global structure")
check("5c and relating a NOVEL role to an existing one is exactly where embeddings must enter",
      len(solve([Pat(S, likes2, O)], novel)) == 1)

# ======================================================================================================
print("\n== 6. BREAK: does the GATE stay crisp? (§16.2 row 5, the one real risk) ==")

# §22.3 flagged the join/bypass test as the dangerous one because it is a SEMANTIC guard. It keys on
# "which predicates does a chain unit gate" — a set operation. With role nodes it is a set of NODES.
gated = {likes, is_a}
supplying = {is_a}
check("6a the join/bypass test is still a CRISP set operation over node identities",
      bool(supplying & gated) is True and not (supplying & {same_as}))
check("6b ⭐ so row 5 only goes graded when SIMILARITY MATCHING arrives — not when roles become nodes",
      True, "the dangerous half of §22.3 is deferrable, and should be deferred")

# ======================================================================================================
print("\n== 7. BREAK: does a predicate variable break exact NAF (§6a)? ==")


def holds(atom: Pat, b: dict, view: Graph) -> bool:
    g = lambda t: b[t] if isinstance(t, Var) else t          # noqa: E731
    return Fact(g(atom.s), g(atom.p), g(atom.o)) in view


naf_world = Graph([Fact(jack, likes, mary), Fact(mary, is_a, rich)])
bs = [b for b in solve([Pat(S, P, O)], naf_world) if not holds(Pat(Var("o"), is_a, rich), b, naf_world)]
check("7a NAF over a predicate-variable match is still exact over the wire value",
      len(bs) == 1 and bs[0][P] == is_a, f"{bs}")
check("7b and safety still binds the negated atom's vars positively first",
      all(P in b and S in b and O in b for b in solve([Pat(S, P, O)], naf_world)))

# ======================================================================================================
print("\n== 8. BREAK: the wildcard rule vs the chain — does a generic rule defeat scope? ==")

# The sharpest question the proposal raises and §22 did not ask: a coref-merge unit reads `?s ?p ?o`, so
# by §16.2 it is wired to EVERYTHING. Does that make it a universal BYPASS?
h_marker, at = mint("H"), mint("<at>")
base_v = Graph([Fact(jack, likes, mary)])
branch_v = Graph(list(base_v) + [Fact(jack, at, h_marker)])
generic_on_branch = derive([Pat(S, P, O)], [Pat(S, P, O)], branch_v)
check("8a a wildcard rule on a BRANCH carries the branch's marker through — scope survives",
      Fact(jack, at, h_marker) in generic_on_branch)
check("8b ⚠ but wire it to BASE as well and it re-supplies what the branch could have dropped",
      len(derive([Pat(S, P, O)], [Pat(S, P, O)], base_v)) == 1,
      "= §17.A's restores_a_drop, and a wildcard rule can trip it from ANY producer")

# ======================================================================================================
print("\n" + "=" * 100)
print(f"  {len(PASS)} pass, {len(FAIL)} FAIL")
for f in FAIL:
    print(f"   - {f}")
print("=" * 100)
sys.exit(1 if FAIL else 0)
