"""Spike: is a RULE-AS-ACTIVE-CELL a re-point, or a refinement of `execution_topology.md` §4b?

THE PROPOSAL (2026-07-26). Facts stay data; RULES become active computation CELLS, dynamically assembled
from the KB and the discourse (e.g. to nest scopes), wired to each other, firing when the subgraph fed to
them matches their LHS — "a symbolic neural network". §4b of the ratified topology says a queue item is a
`Continuation` and is SILENT on how a rule finds its data; §4d already derived half the proposal for
watchers alone ("do NOT seed; INDEX", `O(watchers x rounds)` -> `O(matches)`). So the reconciliation on
the table is:

    HYPOTHESIS (H): a CELL IS A PARKED CONTINUATION INDEXED BY ITS LHS TRIGGER. The network is the
    index over parked continuations; the wiring is graph-resident work-requests (§4b, rule-visible);
    the partial match rides in the continuation (registers). No third state home, no opcode delta.

H is worth nothing if it costs the topology its soundness argument. §5/§5b make NAF legal only in a
well-defined DRAINED state, and a network of cells that NEVER LEAVE is §4d hazard 1 — unbounded arrival —
promoted from a watcher corner case to the default. Hence the question this spike exists to answer:

    Q: DOES A SCOPE STILL HAVE A DEFINABLE DRAINED STATE WHEN THE RULE NEVER LEAVES THE NETWORK?

CASES
  1. a cell IS a parked continuation, woken by an INDEXED positive delta — and the index is SELECTIVE
     (an unrelated grain wakes nothing: O(matches), not O(cells x rounds)).
  2. the JOIN — a two-premise cell's partial match lives in the CONTINUATION, not in a third state
     home, and is INVISIBLE to a fact read (§8: a rule must never match on machinery).
  3. DRAIN — the answer to Q, and it forces the predicate to be RESTATED.
  4. UNBOUNDED ARRIVAL — (a) a monotone cell CYCLE drains, and chained firing shows the wiring is
     complete by construction; (b) a non-monotone cell does NOT drain, and is caught by budget.
  5. SCOPED cells — nesting, sibling isolation, parent-first order, and what an UNTAGGED delta costs.

GO = 1, 2, 3, 4a, 5 pass AND 4b fails as designed (the hazard is real and detected, not silent).
NO-GO = drain is undefinable, or the partial match needs a home in the graph.

Deliberately self-contained: `CellNet` below is ~60 lines of scheduler standing in for what §7 would
own. Nothing here proposes to ship it — the spike tests the MODEL, and the matcher is not under test
(each cell's LHS check is a Python read of `g`, which is what a lowered ISA body would do).
"""
from __future__ import annotations

import pathlib
import sys
import warnings
from collections import defaultdict
from dataclasses import dataclass, field

warnings.simplefilter("ignore")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ugm.attrgraph import AttrGraph, NAME, graded, valued                  # noqa: E402
from ugm.machine import (                                                  # noqa: E402
    Block, Continuation, ControlMachine, PRIM, SUSPEND, BRANCH,
)
from ugm.scope_tree import (                                               # noqa: E402
    is_visible, put_under, scope_chain, scope_name,
)

WATCHES = "watches"          # cell --watches--> trigger: why the cell is here, ANSWERABLE in-graph


# ── the fact layer (data) ────────────────────────────────────────────────────
# Entities live in BASE (base ink is visible from every vantage, §4c); only the FACT relation nodes are
# scoped. That is the topology's own claim that isolation is a WRITE discipline, not a storage one (§6b).

def _entity(g: AttrGraph, name: str) -> str:
    hits = [n for n in g.nodes_named(name) if not g.predicate(n)]
    return hits[0] if hits else g.add_node({NAME: valued(name)})


def facts(g: AttrGraph, p: str, o: str | None, vantage: str | None) -> set[str]:
    """Subject names of the live `?s p o` facts VISIBLE from `vantage` — the ordinary scoped read."""
    out = set()
    for rel in g.nodes_with_key(p):
        if not is_visible(g, rel, vantage):
            continue
        obj = next(iter(g.out(rel)), None)
        if o is not None and (obj is None or g.name(obj) != o):
            continue
        out |= {g.name(s) for s in g.into(rel) if g.name(s)}
    return out


def tell(g: AttrGraph, net: "CellNet", s: str, p: str, o: str, scope: str | None = None) -> bool:
    """Materialize `s p o` under `scope` and enqueue its POSITIVE delta. IDEMPOTENT: re-telling a fact
    already visible from that vantage writes nothing and enqueues nothing — which is `reactive.py`'s
    monotonicity argument, and case 4 turns on it."""
    if s in facts(g, p, o, scope):
        return False
    rel = g.add_relation(_entity(g, s), p, _entity(g, o))
    if scope is not None:
        put_under(g, rel, scope)
    net.emit((p, o, scope))
    return True


# ── the cell layer (the network) ─────────────────────────────────────────────

@dataclass
class Cell:
    """A rule, live in the network. THREE HOMES, exactly the two §4b allows plus nothing:

      * `node`     -> the GRAPH. A work REQUEST (§4b's three-way split), rule-visible, `watches`-linked
                      to its trigger so "why am I watching for this?" is answerable in-language.
      * `cont`     -> REGISTERS. The parked continuation; ITS `ctrl` is the cell's memory (case 2).
      * `triggers` -> the INDEX key, derived MECHANICALLY from the LHS. Never hand-wired: that is what
                      keeps a cell from missing a fact that arrived by an unforeseen route (case 4a).
    """
    name: str
    node: str
    triggers: frozenset
    scope: str | None
    cont: Continuation
    woken: int = 0               # resumptions — what the INDEX decided
    fired: int = 0               # resumptions that WROTE — what the LHS read decided. The two differ,
                                 # and cases 4a/5 turn on the difference.


@dataclass
class CellNet:
    """The scheduler §7 would own, in miniature: an index from trigger grain to cell, and a delta queue.

    A grain is `(pred, obj, scope)`. NOTE THE THIRD SLOT — `reconsider.DIRTY_REG` grains are `(pred, obj)`
    today; case 5 is what that costs."""
    cells: list = field(default_factory=list)
    index: dict = field(default_factory=lambda: defaultdict(list))
    queue: list = field(default_factory=list)
    wakes: int = 0                       # resumptions attempted — the selectivity measure
    wake_order: list = field(default_factory=list)    # scheduler order, for the parent-first probe
    order: list = field(default_factory=list)         # cells that actually WROTE

    def install(self, g: AttrGraph, name: str, triggers, fire, scope: str | None = None) -> Cell:
        """ASSEMBLE a cell: mint its work-request node, park its continuation, index it by LHS."""
        node = g.add_node({NAME: valued(f"cell_{name}")})
        if scope is not None:
            put_under(g, node, scope)
        for t in triggers:
            g.add_relation(node, WATCHES, _entity(g, f"{t[0]}:{t[1]}"))
        prog = [
            Block(label="WAIT", term=SUSPEND(request_reg="grain")),   # PARKED — the cell at rest
            Block(prim=PRIM(fn=fire, out="fired"), term=BRANCH("WAIT")),   # fire, then RE-PARK
        ]
        cm = ControlMachine()
        cont = cm.run(g, prog)
        assert isinstance(cont, Continuation), "a cell must park, not run to completion"
        cont.ctrl["self"] = node
        cont.ctrl["scope"] = scope or ""
        cell = Cell(name, node, frozenset(triggers), scope, cont)
        self.cells.append(cell)
        for t in triggers:
            self.index[t].append(cell)
        return cell

    def emit(self, grain) -> None:
        self.queue.append(grain)

    def _wakeable(self, g: AttrGraph, grain) -> list:
        """The cells an arriving grain reaches. A cell sees a delta in its OWN scope or an ANCESTOR's —
        the same live-inheritance rule `is_visible` implements for facts (§4c), applied to control."""
        p, o, sc = grain
        hits = [c for key in ((p, o), (p, None)) for c in self.index.get(key, ())]
        return [c for c in hits if sc is None or sc in scope_chain(g, c.scope)]

    def _depth(self, g: AttrGraph, c: Cell) -> int:
        return len(scope_chain(g, c.scope))

    def enabled(self, g: AttrGraph) -> list:
        """Cells a grain in the CURRENT queue can reach. `drained` is defined over THIS, not over the
        network's occupancy — which is the whole finding of case 3."""
        return [c for gr in self.queue for c in self._wakeable(g, gr)]

    def drained(self, g: AttrGraph) -> bool:
        return not self.queue and not self.enabled(g)

    def step(self, g: AttrGraph) -> int:
        """One round: detach the queue (the regress guard `reactive.fire` already uses), wake every
        indexed cell PARENT-FIRST (§5b (iii): a parent drains before its children run)."""
        batch, self.queue = self.queue, []
        pairs = [(c, gr) for gr in batch for c in self._wakeable(g, gr)]
        pairs.sort(key=lambda cg: self._depth(g, cg[0]))
        n = 0
        for cell, grain in pairs:
            self.wakes += 1
            cell.woken += 1
            self.wake_order.append(cell.name)
            cont = ControlMachine().resume(g, cell.cont, {"grain": grain})
            assert isinstance(cont, Continuation), "a fired cell must RE-PARK, not leave the network"
            cell.cont = cont                       # the cell's memory IS its continuation
            if cont.ctrl.get("fired"):
                cell.fired += 1
                self.order.append(cell.name)
                n += 1
        return n

    def drain(self, g: AttrGraph, budget: int = 50) -> tuple[int, bool]:
        """Run to quiescence. Returns `(rounds, drained?)` — a budget rather than a hang, so an
        unbounded-arrival network reports UNKNOWN honestly ([[think-harder-chapter]])."""
        rounds = 0
        while self.queue and rounds < budget:
            self.step(g)
            rounds += 1
        return rounds, self.drained(g)


def rule(net: CellNet, head_pred: str, head_obj: str, body_pred: str, body_obj: str):
    """A one-premise cell body: for every `?x body_pred body_obj` VISIBLE FROM THE CELL'S SCOPE, write
    `?x head_pred head_obj` UNDER that scope. The LHS read is scoped; the write is scope-local (§4.2)."""
    def fire(g, stream, ctrl):
        sc = ctrl.get("scope") or None
        wrote = 0
        for s in facts(g, body_pred, body_obj, sc):
            wrote += tell(g, net, s, head_pred, head_obj, sc)
        return stream, wrote
    return fire


# ── CASE 1: a cell is a parked continuation, woken by an indexed delta ───────

def case1_cell_is_a_parked_continuation():
    g, net = AttrGraph(), CellNet()
    c = net.install(g, "mortal", [("is", "human")], rule(net, "is", "mortal", "is", "human"))

    tell(g, net, "socrates", "is", "human")          # intake: a fact + its positive delta
    net.step(g)
    derived = facts(g, "is", "mortal", None)

    wakes_before = net.wakes
    net.emit(("is", "blue", None))                   # an UNRELATED grain: the index must ignore it
    net.step(g)
    selective = net.wakes == wakes_before

    parked = isinstance(c.cont, Continuation)
    # the work REQUEST is in the graph and rule-visible: "why am I watching for this?" is answerable
    watched = {g.name(o) for r, o in g.relations_from(c.node) if g.has_key(r, WATCHES)}

    ok = derived == {"socrates"} and selective and parked and watched == {"is:human"}
    print(f"  CASE 1 (cell=continuation)  derived={sorted(derived)}  re-parked={parked}  "
          f"selective(unrelated grain wakes 0)={selective}  watches={sorted(watched)}  "
          f"-> {'PASS' if ok else 'FAIL'}")
    return ok


# ── CASE 2: the join — partial match in the continuation, invisible to reads ─

def case2_partial_match_has_no_third_home():
    g, net = AttrGraph(), CellNet()

    def fire(g_, stream, ctrl):
        """A two-premise cell. The half-match is remembered in `ctrl` — the CONTINUATION — and the cell
        never re-reads the premise it already saw. That is a RETE beta memory with no new state home."""
        p, o, _sc = ctrl["grain"]
        seen = set((ctrl.get("seen") or "").split(",")) - {""}
        if (p, o) == ("is", "human"):
            seen |= facts(g_, "is", "human", None)
            ctrl["seen"] = ",".join(sorted(seen))
            return stream, 0                                    # PARTIAL — park again, write nothing
        wrote = 0
        for s in facts(g_, "is", "old", None) & seen:           # the JOIN, against remembered bindings
            wrote += tell(g_, net, s, "is", "venerable", None)
        return stream, wrote

    c = net.install(g, "venerable", [("is", "human"), ("is", "old")], fire)

    tell(g, net, "socrates", "is", "human")
    snapshot = (len(g.nodes()), len(g.edges()))     # take it AFTER intake, BEFORE the cell runs
    net.step(g)
    remembered = "socrates" in (c.cont.ctrl.get("seen") or "")
    # §8 PROBE: the firing that produced a HALF-MATCH must have added NOTHING to the graph — no beta
    # memory node, no attr on the cell, no fact. If the partial match were visible, a rule could match
    # on machinery and scheduling would become semantics.
    leaked = (len(g.nodes()), len(g.edges())) != snapshot or bool(facts(g, "is", "venerable", None))

    tell(g, net, "socrates", "is", "old")
    net.step(g)
    fired = facts(g, "is", "venerable", None)

    ok = remembered and not leaked and fired == {"socrates"}
    print(f"  CASE 2 (join)               partial-match-in-continuation={remembered}  "
          f"visible-in-graph={leaked}  after-2nd-premise={sorted(fired)}  "
          f"-> {'PASS' if ok else 'FAIL'}")
    return ok


# ── CASE 3: the drain — Q, and the restatement it forces ────────────────────

def case3_drain_is_definable():
    g, net = AttrGraph(), CellNet()
    net.install(g, "mortal", [("is", "human")], rule(net, "is", "mortal", "is", "human"))
    net.install(g, "named", [("is", "mortal")], rule(net, "is", "named", "is", "mortal"))

    tell(g, net, "socrates", "is", "human")
    rounds, drained = net.drain(g)

    # THE RESTATEMENT. The network is NON-EMPTY and stays non-empty: both cells are still parked, still
    # indexed, still able to fire forever. "Drained" therefore cannot mean "no work left in the system";
    # it means NO ENABLED CELL AND AN EMPTY DELTA QUEUE.
    occupied = len(net.cells)
    still_parked = all(isinstance(c.cont, Continuation) for c in net.cells)

    before = len(g.nodes())
    r2, _ = net.drain(g)                            # STABILITY: a quiesced network does not self-arrive
    stable = r2 == 0 and len(g.nodes()) == before

    # and NAF is legal here: the absence decides, and re-draining does not revoke it
    naf = not facts(g, "is", "immortal", None)
    naf_stable = naf and not facts(g, "is", "immortal", None)

    ok = drained and occupied == 2 and still_parked and stable and naf_stable
    print(f"  CASE 3 (drain)              rounds={rounds}  drained={drained}  cells-still-in-network="
          f"{occupied}  re-drain-rounds={r2}  stable={stable}  NAF-decidable={naf_stable}  "
          f"-> {'PASS' if ok else 'FAIL'}")
    return ok


# ── CASE 4: unbounded arrival — the hazard, both halves ─────────────────────

def case4a_monotone_cycle_drains():
    g, net = AttrGraph(), CellNet()
    net.install(g, "p2q", [("is", "p")], rule(net, "is", "q", "is", "p"))
    net.install(g, "q2p", [("is", "q")], rule(net, "is", "p", "is", "q"))   # a CYCLE

    tell(g, net, "a", "is", "p")
    rounds, drained = net.drain(g)
    # CHAINING = WIRING COMPLETENESS: `q2p` was woken by a fact `p2q` wrote, not by intake. Nothing
    # connected the two cells; the LHS-derived index did, which is why dynamic assembly cannot silently
    # under-wire (the failure mode that would be invisible if a cell only saw what it was handed).
    chained = net.cells[1].woken > 0
    # AND THE CYCLE DRAINS BECAUSE THAT SECOND FIRING WROTE NOTHING. `q2p` woke, re-derived `a is p`,
    # found it already there, and enqueued no grain. Monotonicity is not a nicety here — it IS the
    # termination argument, and it lives in `tell`'s idempotence, one layer below the scheduler.
    silent = net.cells[1].woken > 0 and net.cells[1].fired == 0
    ok = drained and chained and silent and rounds <= 5
    print(f"  CASE 4a (monotone cycle)    rounds={rounds}  drained={drained}  "
          f"consumer-woken-by-producer={chained}  its-write-was-a-no-op={silent}  "
          f"-> {'PASS' if ok else 'FAIL'}")
    return ok


def case4b_nonmonotone_cell_never_drains():
    """THE HAZARD, made visible. `reactive.py`'s soundness rests on materialization being MONOTONE — a
    re-derived fact adds nothing and enqueues no grain. A cell whose write is FRESH each firing breaks
    that, and then no absence is ever final: §5's argument against a single global queue, arriving from
    inside the network. Expected to FAIL to drain — and to be CAUGHT BY BUDGET rather than hang."""
    g, net = AttrGraph(), CellNet()
    counter = [0]

    def fire(g_, stream, ctrl):
        counter[0] += 1
        tell(g_, net, f"gensym{counter[0]}", "is", "p", None)   # a NEW subject every time
        return stream, 1

    net.install(g, "runaway", [("is", "p")], fire)
    tell(g, net, "a", "is", "p")
    rounds, drained = net.drain(g, budget=20)

    ok = not drained and rounds == 20                 # fails as designed, and is DETECTED
    print(f"  CASE 4b (non-monotone)      rounds={rounds}(budget=20)  drained={drained}  "
          f"detected-not-hung={ok}  -> {'FAILS AS DESIGNED' if ok else 'UNEXPECTED'}")
    return ok


# ── CASE 5: scoped cells — nesting, isolation, order, and a defect ──────────

def case5_scoped_cells():
    g, net = AttrGraph(), CellNet()
    h1, h2 = g.add_node({NAME: valued(scope_name())}), g.add_node({NAME: valued(scope_name())})
    for s in (h1, h2):
        g.set_attr(s, "hypothesis", graded(1.0))

    # THE SAME RULE, assembled once per scope — "dynamically assembled to nest scopes", literally
    net.install(g, "H1", [("is", "human")], rule(net, "is", "mortal", "is", "human"), scope=h1)
    net.install(g, "H2", [("is", "human")], rule(net, "is", "mortal", "is", "human"), scope=h2)

    tell(g, net, "socrates", "is", "human", scope=h1)      # a delta INSIDE H1
    net.drain(g)
    in_h1 = facts(g, "is", "mortal", h1)
    in_h2 = facts(g, "is", "mortal", h2)
    in_base = facts(g, "is", "mortal", None)
    isolated = in_h1 == {"socrates"} and not in_h2 and not in_base

    # THE COST OF AN UNTAGGED GRAIN — and it is NOT the one predicted. `reconsider.DIRTY_REG` grains are
    # `(pred, obj)`, with no scope slot. Replay the identical delta as today's dirty set would carry it:
    woken_before = net.cells[1].woken
    wrote_before = net.cells[1].fired
    net.emit(("is", "human", None))
    net.drain(g)
    spurious_wake = net.cells[1].woken > woken_before        # H2's cell IS woken by H1's delta
    contaminated = net.cells[1].fired > wrote_before or bool(facts(g, "is", "mortal", h2))

    # PARENT-FIRST (§5b (iii)): a nested child cell must not run before its parent has drained
    g2, net2 = AttrGraph(), CellNet()
    par = g2.add_node({NAME: valued(scope_name())})
    kid = g2.add_node({NAME: valued(scope_name())})
    put_under(g2, kid, par)
    net2.install(g2, "child", [("is", "human")], rule(net2, "is", "mortal", "is", "human"), scope=kid)
    net2.install(g2, "parent", [("is", "human")], rule(net2, "is", "mortal", "is", "human"), scope=par)
    tell(g2, net2, "socrates", "is", "human")              # a BASE delta, inherited by both
    net2.drain(g2)
    parent_first = net2.wake_order[:2] == ["parent", "child"]
    # AND THE PAYOFF, unbidden: the child wrote NOTHING, because by the time it ran it could already SEE
    # its parent's conclusion (§4c live inheritance). Parent-first is not merely a soundness constraint
    # on NAF — it is also what stops a lineage re-deriving the same fact once per level.
    child_inherited = net2.cells[0].woken > 0 and net2.cells[0].fired == 0

    ok = isolated and spurious_wake and not contaminated and parent_first and child_inherited
    print(f"  CASE 5 (scoped cells)       H1={sorted(in_h1)} H2={sorted(in_h2)} base={sorted(in_base)}  "
          f"isolated={isolated}  untagged-grain: sibling-woken={spurious_wake} "
          f"sibling-contaminated={contaminated}  parent-first={parent_first}  "
          f"child-inherited={child_inherited}  -> {'PASS' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    print("SPIKE: rules as ACTIVE CELLS — a re-point, or a refinement of execution_topology.md §4b?\n")
    ok1 = case1_cell_is_a_parked_continuation()
    ok2 = case2_partial_match_has_no_third_home()
    ok3 = case3_drain_is_definable()
    ok4a = case4a_monotone_cycle_drains()
    ok4b = case4b_nonmonotone_cell_never_drains()
    ok5 = case5_scoped_cells()
    print()
    if ok1 and ok2 and ok3 and ok4a and ok4b and ok5:
        print("VERDICT: GO as a REFINEMENT of §4b, not a re-point.")
        print()
        print("  * A cell IS a parked continuation indexed by its LHS (1). The partial match rides in")
        print("    the continuation — NO THIRD STATE HOME, and invisible to fact reads, so §8 holds (2).")
        print("    The opcode delta is ZERO again: `SUSPEND` + BRANCH-back is the whole mechanism.")
        print("  * DRAIN SURVIVES — but §5's predicate must be RESTATED. The network is PERMANENTLY")
        print("    OCCUPIED (3: drained with 2 cells still parked), so drained can no longer mean 'no")
        print("    work in the system'. It means: EMPTY DELTA QUEUE AND NO ENABLED CELL.")
        print("  * Its precondition is MONOTONE materialization, and that is now load-bearing rather")
        print("    than incidental. 4a drains only because the cycle's second firing WROTE NOTHING;")
        print("    4b, identical but for a fresh write each time, never drains. The termination")
        print("    argument lives in `tell`'s idempotence, one layer BELOW the scheduler.")
        print()
        print("CORRECTION to this spike's own prediction. An untagged `(pred, obj)` dirty grain was")
        print("expected to CONTAMINATE a sibling scope; it does not (5). It wakes the sibling's cells")
        print("spuriously, but their scoped LHS read finds nothing and they write nothing. So the scope")
        print("slot on a grain buys SELECTIVITY, not soundness — the §4d cost argument, not a defect.")
        print("The actual guard against cross-scope leakage is the scoped read plus the scope-local")
        print("write, exactly as §4.2/§4c claim; the delta queue is not load-bearing for isolation.")
    else:
        print("VERDICT: NO-GO / inconclusive — see the failing case above.")
