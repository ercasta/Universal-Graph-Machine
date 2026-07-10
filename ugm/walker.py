"""
Walkers — the long-range demand primitive of goal-direction.

`goal.py`'s tabled solver answers a demanded goal by expanding subgoals to a (demanded)
least-fixpoint. For a LONG-RANGE reachability goal — "is `w` reachable from `x` along `isa`?"
— that expands the whole reachable chain. A **walker** is the bounded alternative
(`decision_walkers_locality`, `vision.md` §6a/§11): a demand token that carries the goal
across the graph hop by hop, spending **fuel**, and stops when it arrives or runs dry. Fuel is
the content-blind effort budget (§14): *"think harder" is literally more fuel*, never a
cleverer search. On arrival the walker **materializes a shortcut** — the derived transitive
relation, marked as a walker discovery — so the next query is O(1) ("discoveries materialize as
provenance shortcuts").

This is the demand carrier a goal-directed driver spawns for an unbounded transitive subgoal
instead of enumerating it. In a full in-graph realization the walker is a CONTROL token with a
`fuel` attribute serviced by rules (the main engine's `harneskills/walker.py`); this reference
driver models that semantics over the label-less `AttrGraph`, matching `goal.py`'s Python-driver
style. It stays positive and monotone — it only ever ADDS a shortcut fact.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from .attrgraph import AttrGraph, graded


@dataclass
class WalkResult:
    """The outcome of a walk. `reached` is whether the target was found within fuel;
    `path` is the node names along the found path (empty if not reached); `hops` its edge
    length; `fuel_spent` the edge-traversals consumed (≤ the fuel budget)."""
    reached: bool
    hops: int = 0
    fuel_spent: int = 0
    path: list[str] = field(default_factory=list)


class Walker:
    """A fuel-bounded reachability demand over one relation on `ag`.

    `rel` is the relation WALKED over (the base edges the reachability follows). `mint_rel` is
    the relation the discovered shortcut is MINTED as; it defaults to `rel`. They differ for
    LINEAR RECURSION over a different base — a derived relation `D` that is the transitive
    closure of a base `B` (`D(a,b):-B(a,b)`, `D(a,c):-B(a,b),D(b,c)`) is answered by walking `B`
    (`rel=B`) and materializing the shortcut as `D` (`mint_rel=D`). For the same-relation
    transitive closure `R(a,c):-R(a,b),R(b,c)` the two coincide (`rel=mint_rel=R`)."""

    def __init__(self, ag: AttrGraph, rel: str, *, mint_rel: str | None = None) -> None:
        self.ag = ag
        self.rel = rel                           # walked over
        self.mint_rel = mint_rel or rel          # shortcut materialized as
        self._name_ids: dict[str, str] = {}      # name -> node id (KB: distinct entity names)
        for nid in ag.nodes():
            a = ag.get_attr(nid, "name")
            if a is not None:
                self._name_ids.setdefault(str(a.value), nid)

    def _successors(self, node: str, rel: str) -> set[str]:
        """Nodes reached from `node` across one reified `rel` hop: node -> [rel] -> succ."""
        out: set[str] = set()
        for r in self.ag.succ(node):
            a = self.ag.get_attr(r, "name")
            if a is not None and a.value == rel:
                out |= self.ag.succ(r)
        return out

    def walk(self, subj: str, obj: str, fuel: int) -> WalkResult:
        """Carry the reachability goal from `subj`, spending one fuel unit per edge-traversal of
        the base relation `rel`, up to `fuel`. A frontier (BFS) keeps the walk goal-directed —
        confined to what is reachable from the source — and `visited` guarantees termination even
        through cycles. On arrival, materialize the shortcut (as `mint_rel`) and return the path.

        This answers a TRANSITIVE reachability (>= 1 hop — the closure the rules compute), so
        there is NO 0-hop short-circuit for `subj == obj`: a reflexive answer holds only via a
        real cycle back to the source, which the BFS finds like any other target (the target
        check runs BEFORE the visited skip so the source is not pruned as already-seen)."""
        s_id, o_id = self._name_ids.get(subj), self._name_ids.get(obj)
        if s_id is None or o_id is None:
            return WalkResult(False)

        visited = {s_id}
        parent: dict[str, str | None] = {s_id: None}
        frontier: deque[str] = deque([s_id])
        spent = 0
        reached_from: str | None = None                  # the node the target was reached from
        while frontier and spent < fuel and reached_from is None:
            node = frontier.popleft()
            for nxt in self._successors(node, self.rel):
                if spent >= fuel:
                    break
                spent += 1                       # each edge-follow burns one fuel unit
                if nxt == o_id:                  # target BEFORE the visited skip (reflexive cycle)
                    reached_from = node
                    break
                if nxt in visited:
                    continue
                visited.add(nxt)
                parent[nxt] = node
                frontier.append(nxt)

        if reached_from is None:
            return WalkResult(False, 0, spent, [])

        # path = [source ... reached_from] then the target as the final node; walking parent[]
        # from reached_from never revisits the source's None-terminated root, so a reflexive
        # (subj == obj) path reconstructs as the cycle [subj ... reached_from, subj].
        path_ids: list[str] = []
        cur: str | None = reached_from
        while cur is not None:
            path_ids.append(cur)
            cur = parent[cur]
        path_ids.reverse()
        path_ids.append(o_id)
        self._materialize_shortcut(s_id, o_id)
        names = [str(self.ag.get_attr(n, "name").value) for n in path_ids]
        return WalkResult(True, len(path_ids) - 1, spent, names)

    def _materialize_shortcut(self, s_id: str, o_id: str) -> None:
        """MINT the derived relation `subj -> [mint_rel] -> obj`, marked `shortcut: 1` (the
        walker's provenance), unless that relation already exists. Monotone — only ever added."""
        if o_id in self._successors(s_id, self.mint_rel):
            return
        r = self.ag.add_relation(s_id, self.mint_rel, o_id)  # Phase 2.1: dual-write bridge
        self.ag.set_attr(r, "shortcut", graded(1.0))


def walk_to_goal(ag: AttrGraph, rel: str, subj: str, obj: str, fuel: int) -> WalkResult:
    """Convenience: spawn a `Walker` and carry the reachability goal `rel(subj, obj)` from
    `subj` with the given `fuel` budget. Materializes a shortcut into `ag` on success."""
    return Walker(ag, rel).walk(subj, obj, fuel)
