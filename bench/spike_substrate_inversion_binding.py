"""Spike: does VARIABLE BINDING survive the substrate inversion? (`docs/design/substrate_inversion.md` §13.2)

THE PROPOSAL. Computation units are the substrate; each unit holds a whole SUBGRAPH as its state; a unit
fires when its input matches its LHS and emits a new subgraph that flows on. No global store. Scope is not
a primitive — it is a CHAIN, i.e. which producers you happen to be wired to.

WHY BINDING IS THE ONLY CASE WORTH SPIKING. The plumbing (index, flow discipline, output caching) is
well-trodden and will work. **NETL (Fahlman 1979) is the closest ancestor of this substrate and it
foundered on exactly one thing: VARIABLES AND BINDING.** Marker passing does inheritance beautifully and
cannot correlate two matches, because a marker carries no binding — it is one bit at a node. That is also
this project's known weak axis ([[binding-is-the-missing-axis]]). So:

    HYPOTHESIS (H): because a unit's state is a whole SUBGRAPH rather than a marker, bindings are carried
    STRUCTURALLY — a variable's value is just a node in the value — and NETL's failure does not recur,
    including across several input wires and several chains.

CASES
  1. the NETL DIAGNOSIS — marker passing vs subgraph passing on a two-place join.
  2. cross-wire binding must join by IDENTITY, never by NAME (the name-luck failure, shown failing).
  3. a legitimate cross-chain join (base + hypothesis) — this MUST work or hypotheses are useless.
  4. sibling isolation at BINDING level — and nothing in the implementation is named "scope".
  5. the falsifiable test of §1 — NO GLOBAL ENUMERATION over data.
  6. can the topology of 3+4 be ASSEMBLED rather than hand-wired? (the emergence claim, tested)

GO = 1-5 pass. Case 6 is the open one and is reported either way.

NO-IMPORT RULE (agreed before writing): this spike may not import from `ugm/`. Anything it needs is
COPIED, and what gets copied is then evidence about what is genuinely shared versus what is a store-shaped
assumption riding along. Asserted mechanically at the bottom of the imports.

DELIBERATELY OUT OF SCOPE: fuel, refire, structural sharing, lifetime. All plumbing (§10).
"""
from __future__ import annotations

import itertools
import pathlib
import sys
from dataclasses import dataclass, field

# THE NO-IMPORT RULE, enforced rather than promised.
_ROOT = str(pathlib.Path(__file__).resolve().parent.parent)
sys.path[:] = [p for p in sys.path if p != _ROOT]
assert not any(m == "ugm" or m.startswith("ugm.") for m in sys.modules), \
    "this spike must not import from ugm/ — copy what it needs (see the docstring)"


# ── the value: a subgraph, immutable ────────────────────────────────────────

@dataclass(frozen=True)
class Node:
    """A node. `nid` is IDENTITY (minted once, at a source, inherited through the pipeline); `name` is a
    LABEL and is never identity ([[node-identity-is-not-a-semantic-proxy]]). Case 2 is entirely about
    keeping those two apart."""
    nid: int
    name: str

    def __repr__(self) -> str:
        return f"{self.name}#{self.nid}"


@dataclass(frozen=True)
class Fact:
    s: Node
    p: str
    o: Node

    def __repr__(self) -> str:
        return f"{self.s} {self.p} {self.o}"


@dataclass(frozen=True)
class Var:
    name: str

    def __repr__(self) -> str:
        return f"?{self.name}"


Subgraph = frozenset            # frozenset[Fact] — the value on a wire
_NID = itertools.count(1)


def node(name: str) -> Node:
    """MINT a node. Two calls give two DISTINCT nodes that happen to share a name — which is the whole
    point of case 2, and the reason there is no `nodes_named` here to fuse them."""
    return Node(next(_NID), name)


# ── matching: the only place a variable is bound ────────────────────────────

def _unify(spec, n: Node, b: dict, *, by_name: bool) -> bool:
    if isinstance(spec, Var):
        if spec in b:
            return (b[spec].name == n.name) if by_name else (b[spec] == n)
        b[spec] = n
        return True
    return (spec.name == n.name) if by_name else (spec == n)


def match(pats: tuple, view: Subgraph, *, by_name: bool = False):
    """Every binding of `pats` in `view`. Ordinary backtracking join — the point is NOT the algorithm, it
    is that the JOIN VARIABLE is resolved against nodes carried IN THE VALUE, so a binding needs no global
    node table to be meaningful. `by_name=True` is the deliberately-wrong variant case 2 contrasts."""
    def go(rest, b):
        if not rest:
            yield dict(b)
            return
        (s, p, o), tail = rest[0], rest[1:]
        for f in view:
            if f.p != p:
                continue
            b2 = dict(b)
            if _unify(s, f.s, b2, by_name=by_name) and _unify(o, f.o, b2, by_name=by_name):
                yield from go(tail, b2)
    return list(go(pats, {}))


# ── the unit ────────────────────────────────────────────────────────────────

@dataclass
class Unit:
    """A computation unit. Its state is its INPUTS (one cached subgraph per in-wire) and its last OUTPUT.

    NOTE WHAT `view()` IS, because it is the spike's first real finding: a unit joins over the UNION of its
    inputs. So the store is not abolished — it is BOUNDED. A unit has a local store consisting of exactly
    what its in-edges deliver, which is the entire difference from a blackboard (unbounded and shared).
    """
    name: str
    lhs: tuple = ()
    rhs: tuple | None = None            # (subj_spec, pred, obj_spec)
    delta: Subgraph = frozenset()       # facts this unit contributes UNCONDITIONALLY
    inputs: dict = field(default_factory=dict)      # producer name -> its last output
    output: Subgraph = frozenset()
    fired: int = 0

    # NOTE that `delta` unifies two things the first draft kept apart, exactly as §2 predicts: a SOURCE is
    # a unit with in-degree 0 and a delta (an axiom — a nullary computation), and a hypothesis BRANCH is
    # the same construct with in-degree 1. There is no separate notion of "a fact".

    def view(self) -> Subgraph:
        v: Subgraph = frozenset()
        for val in self.inputs.values():
            v |= val
        return v

    def run(self, *, by_name: bool = False) -> bool:
        """Recompute. Output = input carried through, PLUS this unit's delta, PLUS what it derived (§5
        accretion). Returns whether the output changed — the termination condition, not a mechanism."""
        view = self.view() | self.delta
        derived = set()
        if self.rhs is not None:
            s, p, o = self.rhs
            for b in match(self.lhs, view, by_name=by_name):
                derived.add(Fact(b[s] if isinstance(s, Var) else s, p,
                                 b[o] if isinstance(o, Var) else o))
        new = view | derived
        changed = new != self.output
        if derived:
            self.fired += 1
        self.output = new
        return changed

    def derived(self, pred: str) -> set:
        """What THIS unit concluded (not what it carried through or contributed) — every case's probe."""
        carried = self.view() | self.delta
        return {f for f in self.output if f.p == pred} - {f for f in carried if f.p == pred}


@dataclass
class Net:
    """The assembler. Holds the ONE permitted global structure (§3.3): an index over unit LHS/RHS
    PREDICATES. It indexes COMPUTATION, never data — there is deliberately no registry of nodes or facts
    anywhere in this file, which is what case 5 checks."""
    units: dict = field(default_factory=dict)
    wires: list = field(default_factory=list)       # (producer, consumer)
    lhs_index: dict = field(default_factory=dict)   # pred -> [unit]  (forward: who could take this?)
    rhs_index: dict = field(default_factory=dict)   # pred -> [unit]  (reverse: who could feed this?)

    def spawn(self, u: Unit) -> Unit:
        self.units[u.name] = u
        for _s, p, _o in u.lhs:
            self.lhs_index.setdefault(p, []).append(u)
        out_preds = ({u.rhs[1]} if u.rhs else set()) | {f.p for f in u.delta}
        for p in out_preds:
            self.rhs_index.setdefault(p, []).append(u)
        return u

    def wire(self, producer: Unit, consumer: Unit) -> None:
        self.wires.append((producer.name, consumer.name))

    def upstream(self, u: Unit) -> set:
        """Transitive producers of `u` — walked over the TOPOLOGY, the only structure there is. Case 6
        uses this; note it needs no notion of scope, chain, or context."""
        seen, frontier = set(), [u.name]
        while frontier:
            cur = frontier.pop()
            for p, c in self.wires:
                if c == cur and p not in seen:
                    seen.add(p)
                    frontier.append(p)
        return seen

    def propagate(self, rounds: int = 20, *, by_name: bool = False) -> int:
        """Run to quiescence. Stops when no output changes — the idempotence condition, again."""
        for i in range(rounds):
            changed = False
            for u in self.units.values():
                for p, c in self.wires:
                    if c == u.name:
                        u.inputs[p] = self.units[p].output
                changed |= u.run(by_name=by_name)
            if not changed:
                return i + 1
        return rounds


# ── the shared rule under test ──────────────────────────────────────────────
# `?x likes ?y , ?y is ?z  ->  ?x admires ?z`.  Two premises, and the join variable ?y is what a marker
# cannot carry. This one rule is used by cases 1, 2, 3, 4 and 6.

X, Y, Z = Var("x"), Var("y"), Var("z")
ADMIRE_LHS = ((X, "likes", Y), (Y, "is", Z))
ADMIRE_RHS = (X, "admires", Z)


# ── CASE 1: the NETL diagnosis ──────────────────────────────────────────────

def case1_markers_vs_subgraphs():
    """NETL propagates a MARKER — one bit at a node. That does inheritance perfectly and cannot correlate
    two matches, because there is nowhere to record WHICH ?y a given ?x went with. The failure is a
    CROSS-PRODUCT, and it is quantifiable."""
    jack, bob, mary, sue, rich, poor = (node(n) for n in
                                        ("jack", "bob", "mary", "sue", "rich", "poor"))
    facts = frozenset({Fact(jack, "likes", mary), Fact(bob, "likes", sue),
                       Fact(mary, "is", rich), Fact(sue, "is", poor)})

    # --- marker passing: mark the subjects of `likes`, follow `is`, conclude. No bindings anywhere.
    marked_x = {f.s for f in facts if f.p == "likes"}
    marked_y = {f.o for f in facts if f.p == "likes"}
    marked_z = {f.o for f in facts if f.p == "is" and f.s in marked_y}
    marker_answers = {(x.name, z.name) for x in marked_x for z in marked_z}

    # --- subgraph passing: the same rule as a unit
    u = Unit("admire", ADMIRE_LHS, ADMIRE_RHS)
    u.inputs["src"] = facts
    u.run()
    unit_answers = {(f.s.name, f.o.name) for f in u.derived("admires")}

    truth = {("jack", "rich"), ("bob", "poor")}
    ok = unit_answers == truth and marker_answers != truth and truth < marker_answers
    print(f"  CASE 1 (NETL diagnosis) marker-passing={sorted(marker_answers)}")
    print(f"                          subgraph-unit ={sorted(unit_answers)}  (truth={sorted(truth)})")
    print(f"                          markers over-conclude by "
          f"{len(marker_answers - truth)} of {len(marker_answers)}  -> {'PASS' if ok else 'FAIL'}")
    return ok


# ── CASE 2: binding across wires is by IDENTITY, never by NAME ──────────────

def case2_identity_not_name():
    """The join variable arrives from TWO DIFFERENT PRODUCERS. What makes `mary` on wire A the same as
    `mary` on wire B? If the answer is 'the name', two independently-minted marys fuse and the unit
    concludes something false — the name-luck failure this project has paid for before. If the answer is
    identity inherited through the pipeline, it does not."""
    jack, mary_a = node("jack"), node("mary")
    mary_b, rich = node("mary"), node("rich")      # a DIFFERENT mary, same name, independent source

    u = Unit("admire", ADMIRE_LHS, ADMIRE_RHS)
    u.inputs["A"] = frozenset({Fact(jack, "likes", mary_a)})
    u.inputs["B"] = frozenset({Fact(mary_b, "is", rich)})    # NOT about mary_a

    u.run(by_name=False)
    by_identity = {(f.s.name, f.o.name) for f in u.derived("admires")}
    u.output = frozenset()
    u.run(by_name=True)
    by_name = {(f.s.name, f.o.name) for f in u.derived("admires")}

    # and the positive control: the SAME node on both wires must join
    v = Unit("admire2", ADMIRE_LHS, ADMIRE_RHS)
    v.inputs["A"] = frozenset({Fact(jack, "likes", mary_a)})
    v.inputs["B"] = frozenset({Fact(mary_a, "is", rich)})    # the very same node object
    v.run()
    joined = {(f.s.name, f.o.name) for f in v.derived("admires")}

    ok = not by_identity and by_name == {("jack", "rich")} and joined == {("jack", "rich")}
    print(f"  CASE 2 (identity)       two distinct marys: by-identity={sorted(by_identity)} (want none)  "
          f"by-NAME={sorted(by_name)} (the false positive)")
    print(f"                          same node on both wires: {sorted(joined)}  "
          f"-> {'PASS' if ok else 'FAIL'}")
    return ok


# ── CASES 3 + 4: chains, hand-wired ─────────────────────────────────────────

def _chain_world():
    """base: `jack likes mary`. Two hypothesis branches, each taking base as INPUT, carrying it THROUGH,
    and adding its own claim (§5 accretion). NOTHING here is called a scope: a branch is a unit, and a
    chain is what being wired to it means.

    (The first draft of this spike modelled the branches as INDEPENDENT sources carrying only their delta.
    That contradicts §5 — a branch carries its input through — and it is what made case 6 fail. Recorded
    because the mis-modelling is instructive: without accretion, chains are not chains at all.)"""
    jack, mary = node("jack"), node("mary")
    rich, poor = node("rich"), node("poor")
    net = Net()
    base = net.spawn(Unit("base", delta=frozenset({Fact(jack, "likes", mary)})))
    h1 = net.spawn(Unit("H1", delta=frozenset({Fact(mary, "is", rich)})))
    h2 = net.spawn(Unit("H2", delta=frozenset({Fact(mary, "is", poor)})))
    net.wire(base, h1)
    net.wire(base, h2)
    return net, base, h1, h2


def case3_and_4_chains():
    net, base, h1, h2 = _chain_world()
    e1 = net.spawn(Unit("E@H1", ADMIRE_LHS, ADMIRE_RHS))
    e2 = net.spawn(Unit("E@H2", ADMIRE_LHS, ADMIRE_RHS))
    net.wire(base, e1); net.wire(h1, e1)          # E1 sees base + H1
    net.wire(base, e2); net.wire(h2, e2)          # E2 sees base + H2
    net.propagate()

    a1 = {(f.s.name, f.o.name) for f in e1.derived("admires")}
    a2 = {(f.s.name, f.o.name) for f in e2.derived("admires")}

    # CASE 3: the cross-chain join MUST work — ?x/?y bound in base, ?z in the hypothesis
    crosses = a1 == {("jack", "rich")} and a2 == {("jack", "poor")}
    # CASE 4: and must not leak between siblings
    isolated = not (a1 & a2) and "poor" not in {z for _x, z in a1} and "rich" not in {z for _x, z in a2}

    print(f"  CASE 3 (cross-chain)    E@H1={sorted(a1)}  E@H2={sorted(a2)}  "
          f"-> {'PASS' if crosses else 'FAIL'}")
    print(f"  CASE 4 (sibling isol.)  no shared conclusion={not (a1 & a2)}  no cross-binding={isolated}  "
          f"-> {'PASS' if isolated else 'FAIL'}")
    return crosses, isolated, (a1, a2)


# ── CASE 5: the falsifiable test — no global enumeration over DATA ──────────

def case5_no_global_enumeration(net: Net):
    """§1's criterion. The only global structure is the unit index, and its keys must be PREDICATES —
    computation — never node or fact identities. Also checked structurally: `Unit.run` reads `self.view()`
    and nothing else, so a unit has no address for what was not piped in."""
    index_keys = set(net.lhs_index) | set(net.rhs_index)
    keys_are_predicates = all(isinstance(k, str) for k in index_keys)
    # there is no module-level registry of nodes or facts in this file — the only counter is `_NID`
    globals_holding_data = [n for n, v in globals().items()
                            if isinstance(v, (dict, set, list)) and not n.startswith("_")
                            and any(isinstance(x, (Node, Fact)) for x in v)]
    import inspect
    src = inspect.getsource(Unit.run)
    reads_only_inputs = "self.view()" in src and "Net" not in src and "global" not in src

    ok = keys_are_predicates and not globals_holding_data and reads_only_inputs
    print(f"  CASE 5 (no global enum) index keys={sorted(index_keys)} (all predicates="
          f"{keys_are_predicates})  data-holding globals={globals_holding_data}  "
          f"unit-reads-only-its-inputs={reads_only_inputs}  -> {'PASS' if ok else 'FAIL'}")
    return ok


# ── CASE 6: can that topology be ASSEMBLED? (the emergence claim) ───────────

def case6_assembly(expected):
    """Cases 3+4 hand-wired the chains. The proposal says chains EMERGE — that scope is nothing but which
    producers you are wired to. So: can the assembler reach the same topology from the index alone?

    TWO POLICIES, and the difference is the whole finding:
      (a) NAIVE — wire every producer whose output predicate a consumer's LHS mentions.
      (b) ANCESTRY — a producer joins an existing instance only if it is COMPARABLE (ancestor, descendant
          or identical) with EVERY producer already wired into it. Two sibling branches are incomparable,
          so the second one SPAWNS A NEW INSTANCE instead of adding a wire. Purely local, walked over the
          topology (`Net.upstream`), and it names no scope, context or vantage.

          "Every", not "any": `base` is an ancestor of BOTH branches, so an any-test lets H2 join the
          instance already holding H1 and the chains collapse anyway. That one quantifier is the
          difference between the emergence claim holding and not.
    """
    def assemble(policy: str):
        net, base, h1, h2 = _chain_world()
        made: list = []
        wired: dict = {}                           # instance name -> producers wired into it
        lhs_preds = {p for _s, p, _o in ADMIRE_LHS}

        def comparable(a: str, b: str) -> bool:
            return a == b or a in net.upstream(net.units[b]) or b in net.upstream(net.units[a])

        for producer in (base, h1, h2):            # lazy spawn: producers arrive one at a time
            if not {f.p for f in producer.delta} & lhs_preds:
                continue
            target = None
            for u in made:
                if policy == "naive" or all(comparable(producer.name, q) for q in wired[u.name]):
                    target = u                     # one lineage -> add a wire
                    break
            if target is None:                     # an independent branch -> a NEW instance of the rule
                target = net.spawn(Unit(f"E#{len(made) + 1}", ADMIRE_LHS, ADMIRE_RHS))
                made.append(target)
                wired[target.name] = set()
            net.wire(producer, target)
            wired[target.name].add(producer.name)
        net.propagate()
        return [{(f.s.name, f.o.name) for f in u.derived("admires")} for u in made]

    naive = assemble("naive")
    ancestry = assemble("ancestry")
    want = list(expected)
    collapsed = len(naive) == 1 and naive[0] == {("jack", "rich"), ("jack", "poor")}
    emerged = len(ancestry) == 2 and [a for a in ancestry if a] == [a for a in want if a]

    print(f"  CASE 6 (assembly)       naive index-only -> {len(naive)} instance(s) {naive}  "
          f"CHAINS COLLAPSED={collapsed}")
    print(f"                          ancestry policy  -> {len(ancestry)} instance(s) {ancestry}  "
          f"matches hand-wired={emerged}  -> {'PASS' if (collapsed and emerged) else 'FAIL'}")
    return collapsed, emerged


if __name__ == "__main__":
    print("SPIKE: does VARIABLE BINDING survive the substrate inversion? (NETL's failure mode)\n")
    ok1 = case1_markers_vs_subgraphs()
    ok2 = case2_identity_not_name()
    ok3, ok4, expected = case3_and_4_chains()
    net_for_5 = Net()
    net_for_5.spawn(Unit("probe", ADMIRE_LHS, ADMIRE_RHS))
    ok5 = case5_no_global_enumeration(net_for_5)
    collapsed, emerged = case6_assembly(expected)
    print()
    core = ok1 and ok2 and ok3 and ok4 and ok5
    if core:
        print("VERDICT: GO on BINDING — NETL's failure mode does NOT recur.")
        print()
        print("  * A marker carries no binding, so a two-place join becomes a CROSS-PRODUCT (case 1).")
        print("    A unit whose state is a SUBGRAPH carries the binding structurally — the value of ?y")
        print("    is just a node in the value — so the join is exact. That is the whole difference,")
        print("    and it is why this substrate is not NETL.")
        print("  * Binding across wires works, and works BY IDENTITY (case 2). Joining by NAME produces")
        print("    a false conclusion from two independently-minted `mary`s. So node identity must be")
        print("    INHERITED through the pipeline, not re-derived at each unit — which makes structural")
        print("    sharing (§5) load-bearing for CORRECTNESS, not just for cost.")
        print("  * Chains work in both directions that matter: a unit wired to base + one hypothesis")
        print("    joins across them (case 3), and sibling branches cannot bind into each other (4) —")
        print("    with nothing in the implementation named scope, context, or vantage.")
        print("  * No global enumeration over data (case 5): the one global structure is the unit index,")
        print("    keyed by predicate.")
        print()
        print("  FINDING NOT IN THE DOC: the store is not abolished, it is BOUNDED. A unit joins over the")
        print("  UNION of its inputs, so it has a local store consisting of exactly what its in-edges")
        print("  deliver. 'No blackboard' means no UNBOUNDED SHARED store — a distinction the doc should")
        print("  make, because a unit's in-degree is now the thing that bounds its epistemic reach.")
    else:
        print("VERDICT: NO-GO on binding — see the failing case above.")
    print()
    if collapsed and emerged:
        print("CASE 6 — the emergence claim SURVIVES, with a policy the doc does not yet state:")
        print("  Predicate-level indexing ALONE collapses the chains (one instance sees both hypotheses")
        print("  and derives both conclusions). What separates them is a purely LOCAL test: a producer")
        print("  neither upstream nor downstream of a unit's existing inputs is an independent branch and")
        print("  SPAWNS A NEW INSTANCE instead of adding a wire. Scope stays emergent — the policy names")
        print("  no scope, only reachability over the wiring — but the index is NOT sufficient by itself,")
        print("  and §3 currently reads as though it were.")
    else:
        print("CASE 6 — INCONCLUSIVE: assembly did not reproduce the hand-wired topology; the emergence")
        print("  claim needs more than an ancestry test. See the numbers above.")
