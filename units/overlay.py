"""OVERLAYS — `docs/units/revision-02-two-planes.md` §6.

A spike, deliberately separate from `standing.py`, which implements revision 01 and carries the design
error this module exists to correct.

## The claim

A unit's output is **not a graph**. It is an **overlay**: a revertable mutation applied to the one graph
— mint a node, add an edge, set an attribute, identify two nodes. Nothing is materialized; a read
consults the live overlays and composes the answer.

## What went wrong in `standing.py`, and why it is the type's fault

`Value` carries `graph: Graph` **and** `merges: tuple` beside it. `Merge` could not be expressed as a
fragment — it rewrites every mention of a node, anywhere — so it was carried out of band and re-applied
at read time in `Network._assemble`. **One effect type not fitting the container is the container being
wrong.** Here all four effects are the same kind of thing and there is no side channel.

## Two constraints this module is built to keep

**A read is relative to a configuration, and returns one value or reports a conflict** (invariant 16,
rewritten — the first version of this module got it wrong).

A read takes `under`: which suppositions are powering things. §3 — *scope is support* — means two
overlays resting on different suppositions are **never both live in one read**, so *"a man under H1, a
woman under H2"* never presents as a conflict. What remains, two values in **one** configuration, is an
inconsistency and is reported as one.

⚠ There are **three** options here, not two, and the first draft of this module took the wrong one of the
three. *Picking a winner* is CSS's cascade — engine-hardcoded precedence, which `model.md` §11 says must
stay authored. *Returning a set* looks like the principled refusal to pick, and is not: a caller takes
the first element and the contradiction disappears exactly as quietly as it did under `Graph.union`, now
with the engine's blessing. **Not picking is not the same as returning a set.** A conflicted read is
**absent**, and the conflict is a **positive fact** (`model.md` §8) that a rule can match and resolve by
concluding a `Retract` — after which the next revive reads cleanly.

Absent-on-conflict is safe here in a way it would not be in a system with strong negation: §4 already
weakened absence to *"nothing matched above θ"*, so a conflicted value reading as absent corrupts no
claim that was ever made.

**Applying an attribute overlay must never write the attribute** (`revision-01` §9's design-changing
finding). `Graph.union` merges attrs by node, so two live derivations disagreeing about one
`(node, attr)` collapsed silently, and the contradiction vanished exactly when it mattered. A `SetAttr`
applies as a **reified attribution node**. Keeping that here is what lets one graph hold *"a man under
H1, a woman under H2"*.

## The number this module exists to produce

`Identify` is the case that decides whether lazy application is affordable. Mint, edge and attribute
overlays are local, so a read consults a small set; an identification rewrites every mention, so *every*
read — including every read the matcher does, which is most of the inner loop — must resolve identity as
it goes. See `bench_overlay.py`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from .graph import EMPTY, Graph, Node

ATTRIBUTION = "attribution"
BASE = "<base>"


# -- the four effects. All of them mutate the one graph; none of them is a fragment. -------------

@dataclass(frozen=True)
class Mint:
    """Bring a node into being, with crisp attributes. The only effect that creates identity."""

    node: Node
    attrs: tuple = ()                       # ((key, value), …)


@dataclass(frozen=True)
class AddEdge:
    src: Node
    dst: Node


@dataclass(frozen=True)
class SetAttr:
    """Derive an attribute onto a node that lives elsewhere.

    ⚠ Applies as a **reified attribution**, never as a write — see the module docstring. The target is
    untouched wherever it actually lives, so *"Paul is 43"* from a birthday rule stands beside the
    asserted *"Paul is 42"* rather than overwriting it."""

    target: Node
    attr: str
    value: Any


@dataclass(frozen=True)
class Retract:
    """Remove something. `attr=None` removes the node itself; `source` narrows it to one claim.

    **A computation unit's retraction hides while powered**; no data is lost and it reverts by the
    ordinary revive, exactly as every other overlay does. A *mutating* rule's retraction is applied to
    the asserted layer at write-back and is real — the two dispositions again (`revision-01` §2).

    This is what makes conflict resolution expressible without engine policy: a rule matches the
    `conflict` fact a conflicted read produces and concludes which side goes.

    ⚠ **`source` exists because asserted and derived facts do not yet wear one shape**, and the spike
    walked into that open question from the other direction. *Retract Paul's age* is ambiguous between
    *that claim* and *that slot* — and a rule resolving a conflict always means the first, since what it
    matched was a `Conflict` naming readings by source. Naming the source is therefore exactly as
    expressive as what the rule can see. Once a base fact is a **node** like a derived one
    (`revision-01` §9's third finding, still open), this collapses into naming that node and the
    parameter goes."""

    target: Node
    attr: str | None = None
    source: str | None = None          # None = the whole slot; BASE = the asserted claim


@dataclass(frozen=True)
class Grade:
    """Set a **gradable** attribute at a band (`model.md` §3's second sort of attribute).

    ⚠ **Grades meet; they do not conflict.** Two crisp values for one slot are an inconsistency (§6), but
    two bands are not: `band.py`'s min-join is commutative and associative, so *"likely"* and
    *"unlikely"* about the same thing compose to the weaker rather than disagreeing. A chain is as strong
    as its weakest link, and that is a *combination*, not a contradiction.

    This asymmetry is the design already sitting on the truth-axis / knowledge-axis split that bilattices
    formalise (`review-01` §5): disagreement about *what is so* is a conflict; disagreement about *how
    strongly* is a join."""

    target: Node
    attr: str
    band: str


@dataclass(frozen=True)
class Identify:
    """Two nodes are one thing — the **applied** coreference decision.

    This is the effect that proves an overlay is a mutation rather than a fragment: minting, edges and
    attributes can all be described locally, and this cannot. It is still revertable for the ordinary
    reason: it is re-applied from the axioms on every revive, so an identification whose unit loses
    power simply is not made again. Nothing is ever un-merged.

    ⚠ The *decision* is a rule's (`cnl.md` §1, create-never-merge). This is only its application."""

    keep: Node
    drop: Node


EFFECTS = (Mint, AddEdge, SetAttr, Grade, Identify, Retract)


@dataclass(frozen=True)
class Reading:
    """One answer, and what is keeping it alive.

    `source` is the unit whose overlay produced it, or `BASE` for asserted data — which is provenance
    arriving free, since the overlay set *is* the derivation."""

    value: Any
    source: str

    def __repr__(self) -> str:
        return f"{self.value!r}@{self.source}"


@dataclass(frozen=True)
class Conflict:
    """Two live values for one slot, **in one configuration**. A positive fact (`model.md` §8), not an
    absence to be noticed, and not something the engine resolves.

    Its whole job is to be matchable, so a rule can conclude a `Retract` and the next revive reads
    cleanly."""

    node: Node
    attr: str
    readings: tuple

    def __repr__(self) -> str:
        return f"<conflict {self.attr} {list(self.readings)}>"


class Overlays:
    """A base graph plus the live overlays, read lazily.

    The index is built once per revive and thrown away with the values — it holds nothing across a
    revive that the effects do not describe (invariant 18). Reads are then O(1) lookups plus identity
    resolution, which is the whole cost question.
    """

    __slots__ = ("base", "effects", "support", "_parent", "_members", "_edges", "_attribs",
                 "_minted", "_retracts", "_grades")

    def __init__(self, base: Graph = EMPTY, effects: Sequence[tuple] = (),
                 support: dict | None = None) -> None:
        self.base = base
        self.effects = list(effects)            # (source, effect)
        # §3: scope is SUPPORT. Which suppositions a source rests on — in the real engine this is
        # `Network.powering()`, walked backwards over the wiring. Nothing here names a scope; the
        # *reader* states the configuration it is reading under, which is not the same thing.
        self.support: dict = dict(support or {})
        self.reindex()

    # -- indexing: once per revive ---------------------------------------------------------------

    def reindex(self) -> None:
        """Two passes, and the order matters.

        Identity first, because everything else is indexed **by resolved node** — that is what keeps a
        read from having to walk the equivalence class. Doing it the other way round means every read
        pays for the merge; doing it this way means only the index does.
        """
        self._parent: dict = {}
        touched: list = []
        for _, e in self.effects:
            if isinstance(e, Identify):
                self._union(e.keep, e.drop)
                touched.extend((e.keep, e.drop))

        # ⚠ The root belongs to its own class. Building this from `_parent`'s keys alone omits it, and
        # a read then silently loses the surviving node's *own* asserted attributes — found by
        # `test_a_read_gathers_across_an_identification`, and exactly the quiet-degradation class
        # `STATUS.md` records seven of.
        self._members: dict = {}
        for n in touched:
            members = self._members.setdefault(self._find(n), [])
            if n not in members:
                members.append(n)

        self._edges: dict = {}
        self._attribs: dict = {}
        self._minted: list = []
        self._retracts: dict = {}
        self._grades: dict = {}
        for src, e in self.effects:
            if isinstance(e, AddEdge):
                self._edges.setdefault(self._find(e.src), []).append((self._find(e.dst), src))
            elif isinstance(e, SetAttr):
                self._attribs.setdefault(self._find(e.target), []).append((e.attr, e.value, src))
            elif isinstance(e, Mint):
                self._minted.append((e, src))
            elif isinstance(e, Grade):
                self._grades.setdefault(self._find(e.target), []).append((e.attr, e.band, src))
            elif isinstance(e, Retract):
                self._retracts.setdefault(self._find(e.target), []).append((e.attr, e.source, src))
            elif not isinstance(e, Identify):
                raise TypeError(f"unknown effect {e!r}")

    def _union(self, keep: Node, drop: Node) -> None:
        a, b = self._find(keep), self._find(drop)
        if a is not b:
            self._parent[b] = a                 # `keep` wins, so resolution is stable and authored

    def _find(self, n: Node) -> Node:
        p = self._parent.get(n)
        if p is None:
            return n
        root = self._find(p)
        self._parent[n] = root                  # path compression
        return root

    # -- the read path ---------------------------------------------------------------------------

    def resolve(self, n: Node) -> Node:
        """Which node this one turned out to be. Identity is plumbing (`model.md` §11) and this is where
        it is paid for."""
        return self._find(n)

    def _raw(self, n: Node) -> Iterable[Node]:
        """Every node that resolves to `n` — what a read has to gather over."""
        return self._members.get(n, (n,))

    def live(self, source: str, under: frozenset) -> bool:
        """Is this source powered in this configuration? §3: an overlay resting on a supposition is
        simply not there when you are not reading under it — no projection is computed and no rule is
        asked which world it is in."""
        return self.support.get(source, frozenset()) <= under

    def _candidates(self, n: Node, key: str, under: frozenset) -> list:
        out: list = []
        for raw in self._raw(n):
            v = self.base.attr(raw, key)
            if v is not None:
                out.append(Reading(v, BASE))
        for attr, value, src in self._attribs.get(n, ()):
            if attr == key and self.live(src, under):
                out.append(Reading(value, src))
        for minted, src in self._minted:
            if self._find(minted.node) is n and self.live(src, under):
                for k, v in minted.attrs:
                    if k == key:
                        out.append(Reading(v, src))

        # A retraction hides while its own unit is powered. `target=None` empties the slot; a named
        # source removes exactly one claim, which is what a conflict-resolving rule concludes.
        killed = [t for a, t, src in self._retracts.get(n, ())
                  if a in (key, None) and self.live(src, under)]
        if any(t is None for t in killed):
            return []
        return [r for r in out if r.source not in killed]

    def read(self, n: Node, key: str, under: frozenset = frozenset()) -> Reading | None:
        """The value of `n.key` in this configuration — **one**, or `None`.

        `None` means either *nothing says* or *two things disagree*, and the caller is not told which,
        because the difference is not the caller's business: what distinguishes them is a `conflict`
        fact in the graph, which a rule matches (§8's discipline — the outcome is a positive fact, never
        the absence itself).

        ⚠ It does **not** return a set. See the module docstring: not picking is not the same as handing
        the caller a set, and a set is the quieter of the two failures."""
        n = self._find(n)
        found = self._candidates(n, key, under)
        distinct = {r.value for r in found}
        if len(distinct) != 1:
            return None                         # nothing, or a conflict — `conflicts()` says which
        return found[0]

    def conflicts(self, under: frozenset = frozenset()) -> list:
        """Every slot with two live values in this configuration. Positive facts, for a rule to match.

        Note what this is **not**: a consistency check over the whole store. It is a report of what the
        overlays that actually fired disagree about, which is bounded by the circuit."""
        out: list = []
        for n in self.nodes(under):
            keys = {a for a, _, _ in self._attribs.get(n, ())}
            keys |= {k for raw in self._raw(n) for k in self.base.attrs.get(raw, {})}
            for key in keys:
                found = self._candidates(n, key, under)
                if len({r.value for r in found}) > 1:
                    out.append(Conflict(n, key, tuple(found)))
        return out

    def _gone(self, n: Node, under: frozenset) -> bool:
        return any(a is None and self.live(src, under)
                   for a, _t, src in self._retracts.get(n, ()))

    def out(self, n: Node, under: frozenset = frozenset()) -> tuple:
        """Outgoing neighbours, resolved. Base edges and overlay edges are the same thing here."""
        n = self._find(n)
        if self._gone(n, under):
            return ()
        seen: list = []
        for raw in self._raw(n):
            for d in self.base.out(raw):
                d = self._find(d)
                if d not in seen and not self._gone(d, under):
                    seen.append(d)
        for d, src in self._edges.get(n, ()):
            if d not in seen and self.live(src, under) and not self._gone(d, under):
                seen.append(d)
        return tuple(seen)

    def degree(self, n: Node, key: str, under: frozenset = frozenset()) -> str | None:
        """The band for `n.key` — the **meet** of every live grade and the base. See `Grade`: bands
        combine rather than disagree, so this never reports a conflict."""
        from .band import meet
        n = self._find(n)
        if any(a in (key, None) and self.live(src, under)
               for a, _t, src in self._retracts.get(n, ())):
            return None
        band = None
        for raw in self._raw(n):
            d = self.base.degree(raw, key)
            if d is not None:
                band = meet(band, d)
        for attr, b, src in self._grades.get(n, ()):
            if attr == key and self.live(src, under):
                band = meet(band, b)
        return band

    def view(self, under: frozenset = frozenset()) -> "View":
        return View(self, under)

    def nodes(self, under: frozenset = frozenset()) -> tuple:
        """**The** graph as it stands, in this configuration.

        This is what System 1 recalls against next turn (`model.md` §7) — the *overlaid* graph, with
        derived structure present and retracted structure gone. Associative recall over a set-valued
        graph would not be coherent, which is an independent reason a read yields one value."""
        seen: list = []
        minted = [(m.node, src) for m, src in self._minted]
        # A node **mentioned** by a live effect is visible here, even if nothing minted it. Otherwise a
        # downstream unit handed only `SetAttr(paul, …)` cannot see Paul at all and the matcher never
        # tries him — found by `test_crossing_is_one_wire_out_of_the_supposition`. This is not ambient
        # access: it is still only what the gates delivered.
        mentioned = [(t, src) for src, e in self.effects
                     for t in (_targets(e))]
        for n, src in [(b, BASE) for b in self.base.nodes] + minted + mentioned:
            if not self.live(src, under):
                continue
            r = self._find(n)
            if r not in seen and not self._gone(r, under):
                seen.append(r)
        return tuple(seen)

    # -- comparison only: the eager path ---------------------------------------------------------

    def materialize(self) -> Graph:
        """Apply everything and hand back a `Graph`.

        Here **for the benchmark and for nothing else.** It is what lazy application is being compared
        against, and its cost is the argument: materializing rebuilds the whole graph including the
        untouched base, so it scales with the *twin* where a lazy read scales with the *overlays*. Under
        `revision-01` a revive is already O(circuit); making it O(twin) as well is the thing to avoid."""
        g = self.base
        for _, e in self.effects:
            if isinstance(e, Mint):
                g = g.with_node(e.node, **dict(e.attrs))
            elif isinstance(e, AddEdge):
                g = g.with_edge(e.src, e.dst)
            elif isinstance(e, SetAttr):
                a = Node(f"{e.attr}={e.value}")
                g = g.with_node(a, name=ATTRIBUTION, attr=e.attr, value=e.value)
                r = Node("of")
                g = g.with_node(r, name="of").with_edge(a, r).with_edge(r, e.target)
            elif isinstance(e, Identify):
                g = g.merge(e.keep, e.drop)
        return g


def _targets(e) -> tuple:
    """Which nodes an effect mentions."""
    if isinstance(e, (SetAttr, Grade, Retract)):
        return (e.target,)
    if isinstance(e, AddEdge):
        return (e.src, e.dst)
    if isinstance(e, Identify):
        return (e.keep, e.drop)
    return ()


class View:
    """A configuration-fixed read surface, shaped exactly like `Graph` where the matcher touches it.

    `match.solve()` uses four things — `nodes`, `attr`, `degree`, `out` — so threading the matcher
    through overlays needs no change to `match.py` at all. That is the payoff of `Graph` having been kept
    to a small read surface.

    ⚠ **A conflicted attribute simply does not match.** `attr` returns `None` when two live values
    disagree, because a conflicted read is absent (§6). So a rule wanting `age = 42` is silent about a
    node the system is in two minds over — which is the right behaviour and needed no special case."""

    __slots__ = ("_o", "under")

    def __init__(self, overlays: "Overlays", under: frozenset = frozenset()) -> None:
        self._o = overlays
        self.under = under

    @property
    def nodes(self) -> tuple:
        return self._o.nodes(self.under)

    def attr(self, n: Node, key: str):
        r = self._o.read(n, key, self.under)
        return None if r is None else r.value

    def degree(self, n: Node, key: str):
        return self._o.degree(n, key, self.under)

    def out(self, n: Node) -> tuple:
        return self._o.out(n, self.under)

    def conflicts(self) -> list:
        return self._o.conflicts(self.under)


__all__ = ["Mint", "AddEdge", "SetAttr", "Grade", "Identify", "Retract", "Overlays", "View",
           "Reading", "Conflict", "EFFECTS", "ATTRIBUTION", "BASE"]
