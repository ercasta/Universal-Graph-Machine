"""THE COMPUTED INDEX — selectivity from SHAPES, not from what has accumulated (§19, §24.7, §26.2).

§3's index keys on the PREDICATE ALONE, and §24.7 measured what that costs on a **two-line rule**:
`MORTAL#1` emits `socrates is_a mortal`, `is_a` is what the template reads, so the assembler unrolls onto
its own conclusion and spawns an instance whose LHS requires `object = man` — **a unit that can never
fire.** Harmless (it gates, and correctly writes nothing) but not free, and it appears on the first rule
anyone writes rather than at scale.

§19's insight is that this is answerable statically: *"forms come from the grammar and LHS/RHS shapes come
from forms, so which template can in principle feed which is derivable from the form set."* Computed, not
accumulated — which is why it had to be built before the form set is, since retrofitting means the index has
already accumulated.

**⭐ THERE ARE TWO INDEXES HERE AND CONFLATING THEM WOULD BE UNSOUND.** The distinction was found by
spiking case 5 (`bench/spike_computed_index.py`):

    the STATIC index    over TEMPLATES — which template can in principle feed which. A pure function of
                        the library. It answers §10.5's selectivity question BEFORE anything runs, and it
                        is the thing a form set can be AUDITED with. It may NOT gate a wire.
    the RUNTIME filter  over FACTS — can this value satisfy any atom of this LHS? Exact, and the only one
                        allowed to refuse a wire.

The reason is not stylistic: a `given`, a `branch` and a `carrier` are units whose output NO template RHS
describes, so a template→template relation is silent about them. Gate on the static index and every
hand-supplied fact stops reaching the rules that read it.

**⚠ AND THE FILTER MUST COUNT NEGATED ATOMS** (case 3, the soundness trap this spike was written to find).
A producer emitting only `socrates is_a dead` satisfies no POSITIVE atom of *`?x is_a man ∧ ¬ ?x is_a dead`*
— and refusing that wire makes the rule FIRE where it must not. A fact that can SUPPRESS a firing is
relevant to the wire even though it can never justify one. So feasibility spans both polarities while
`spawn_need` stays positive-only: negative evidence may complete an instance, never instantiate one.

**Where it buys nothing, measured rather than assumed** (case 8): an all-variable template — §22.5's
wildcard, which is exactly the coref-merge shape of §24.3 — is fed by everything, and the trace-reading
templates of §26 are all-variable in their non-predicate slots, so **§26.2's hope that a trace consumer
"could be restricted statically to the units whose conclusions it actually grades" does not hold.** The
shape does not say which those are. What the static index does supply there is the DIAGNOSIS: `wildcards()`
names the offenders from the form set alone, before a single unit exists.
"""
from __future__ import annotations

from .match import Absent, Mint, Triple, Var
from .value import Fact, Node, Subgraph


def _slot_matches(spec: object, n: Node) -> bool:
    """One slot of a pattern against one node of a fact. A `Var` accepts anything; a `Node` must be the
    SAME node — identity, never name (§21.2, and `match._bind`'s line)."""
    return True if isinstance(spec, Var) else spec == n


def can_satisfy(f: Fact, atom: Triple) -> bool:
    """Could this fact supply this atom, under SOME binding? The runtime filter's primitive.

    It is exactly `match.matched` with the binding left open, which is why it cannot disagree with the
    matcher: the matcher will bind each positive atom to a fact from the view, so a fact matching no atom
    contributes to no firing."""
    return (_slot_matches(atom.s, f.s) and _slot_matches(atom.p, f.p) and _slot_matches(atom.o, f.o))


def atoms(lhs) -> tuple:
    """Every atom of an LHS, **both polarities** — see this module's docstring on why the negated ones
    count for the wire even though they can never justify a firing."""
    out = []
    for pat in lhs:
        if isinstance(pat, Triple):
            out.append(pat)
        elif isinstance(pat, Absent):
            out.append(pat.atom)
    return tuple(out)


def positive(lhs) -> tuple:
    return tuple(p for p in lhs if isinstance(p, Triple))


def feasible(value: Subgraph, lhs) -> frozenset:
    """The facts in `value` that could satisfy SOME atom of `lhs`. Empty means this producer has nothing
    this template can read — and that is the only sound reason to refuse a wire.

    This is also the PROJECTION for `assemble`'s dedup, and using the same set for both is deliberate: what
    a producer OFFERS a template and what the template may read from it are the same question, so they
    cannot drift apart."""
    ats = atoms(lhs)
    return frozenset(f for f in value if any(can_satisfy(f, a) for a in ats))


def spawn_need(lhs) -> frozenset:
    """The ground predicates of the POSITIVE body — what may INSTANTIATE a template.

    Negative evidence must not spawn: an instance born on *"there is no `dead` fact"* has nothing to
    conclude from. A variable predicate contributes no key at all (§22.5: a rule that declines to say what
    it reads gets no discrimination), which `wildcards()` reports."""
    return frozenset(a.p for a in positive(lhs) if isinstance(a.p, Node))


def selectivity(lhs) -> float:
    """The fraction of a template's non-predicate slots that are GROUND — how much a shape filter can
    possibly restrict. 0.0 means a wildcard: the honest number for §26.2's trace consumers."""
    ats = atoms(lhs)
    if not ats:
        return 0.0
    slots = [s for a in ats for s in (a.s, a.o)]
    return sum(1 for s in slots if not isinstance(s, (Var, Mint))) / len(slots)


def can_feed(head: Triple, body: Triple) -> bool:
    """SHAPE against SHAPE: could a conclusion of this form ever satisfy a body atom of that form?

    Every slot is compatible unless BOTH sides are ground and different — with one addition that is a real
    bit of selectivity rather than bookkeeping: **a `Mint` slot mints a FRESH node** (§23.1), so it can
    never equal a node the form set supplied. A minting head therefore cannot feed a ground body slot,
    while it can feed a variable one."""
    for h, b in ((head.s, body.s), (head.p, body.p), (head.o, body.o)):
        if isinstance(b, Var):
            continue
        if isinstance(h, Mint):
            return False                    # fresh node vs a form's own node — never equal
        if isinstance(h, Var):
            continue
        if h != b:
            return False
    return True


class ComputedIndex:
    """Which template can in principle feed which — **a pure function of the library** (§19).

    Note what it is NOT: a table that grows as things happen. It is recomputed from the shapes, so it
    cannot become the second global structure §3 forbids, and it cannot go stale. It also cannot gate a
    wire — see the module docstring."""

    __slots__ = ("library", "_feeds")

    def __init__(self, library: dict) -> None:
        self.library = dict(library)
        self._feeds: dict = {}
        for pname, (_, prhs) in self.library.items():
            targets = set()
            for cname, (clhs, _) in self.library.items():
                cats = atoms(clhs)
                if any(can_feed(h, b) for h in prhs for b in cats):
                    targets.add(cname)
            self._feeds[pname] = frozenset(targets)

    @property
    def templates(self) -> tuple:
        return tuple(self.library)

    def feeds(self, template: str) -> frozenset:
        """The templates this one's conclusions could reach."""
        return self._feeds.get(template, frozenset())

    def fed_by(self, template: str) -> frozenset:
        return frozenset(p for p, ts in self._feeds.items() if template in ts)

    def wildcards(self) -> set:
        """Templates the index cannot discriminate for — §22.5's *"wake broadly" means "wake always"*.

        **This is §19's actual payoff and it is a diagnosis, not a speedup:** a form set can be told that
        it contains a rule nothing will restrict, from the shapes alone, before a unit exists. §19 also
        predicted the tension it exposes — *"a small form set makes §10.5 WORSE, not better"*, because with
        ten forms all discrimination falls on predicate constants."""
        return {n for n, (lhs, _) in self.library.items()
                if any(isinstance(a.p, Var) for a in atoms(lhs))}

    def density(self) -> float:
        """Fraction of ordered template pairs the index permits. 1.0 = no selectivity at all."""
        n = len(self.library)
        return (sum(len(v) for v in self._feeds.values()) / (n * n)) if n else 0.0

    def __repr__(self) -> str:
        return f"<ComputedIndex {len(self.library)} templates density={self.density():.2f}>"


__all__ = ["can_satisfy", "can_feed", "feasible", "spawn_need", "selectivity", "atoms", "positive",
           "ComputedIndex"]
