"""
The reference ISA machine — a small-step interpreter for the opcode set, over the
label-less attribute substrate (`attrgraph.AttrGraph`).

This is the reference interpreter of the *cheap experiment* (rule-isa-design.md): the
opcode set written as an explicit operational semantics, executed directly, checkable by
HAND-WRITTEN instruction sequences with no rules involved. It is deliberately naive and
correctness-first — no df-ordered seeding, no semi-naive delta, no cross-rule fusion. Those
are optimizations a second (optimized) machine may add and be differential-tested against
this one.

MACHINE STATE.  A program runs over a stream of `State`s. A `State` is
  * `regs`  -- a WAM-style register file, `name -> node identity` (also holds valued literals
               a SET introduced);
  * `score` -- the accumulated graded degree in [0, 1], composed by a t-norm as GRADE/FUZZY
               fire down a match chain (Godel `min` by default; product is the alternative).
A matching opcode is a nondeterministic transition: it maps one state to zero-or-more
successor states (SEED/FOLLOW fork over candidates; TEST/GRADE/FUZZY prune or scale).

TWO PHASES (match-then-apply — the "keep the compiler dumb" discipline, and the engine's own
collect-pending-then-fire order).  A well-formed program is all matching opcodes followed by
all effect opcodes; a matching opcode AFTER an effect opcode raises `ProgramError`. The match
phase produces the final states WITHOUT mutating the graph; the apply phase then runs the
effect opcodes for each surviving state, in state order, mutating the graph. So a MINT in one
state is visible to a following EMIT in the SAME state (they share that state's regs), and no
effect perturbs matching.

THE INVARIANT AS A PROPERTY OF THE OPCODE SET (rule-isa-design.md payoff #1).  The
monotone mutating opcodes are `EMIT`/`MINT` (add a node, raise a graded degree, assert a
value — never lower or delete) and `DROP_CTRL` (delete a bare edge, but it consults
`AttrGraph.edge_is_fact` and REFUSES a fact edge). Fact deletion is not expressible from
ordinary reasoning: there is no fact-deleting opcode in the rule->program lowering vocabulary.
The ONE fact-deletion opcode, `RETIRE`, is the PRIVILEGED mechanism of the retraction/GC policy
(mechanism_policy_separation.md): it really deletes a reified relation, but `lowering` never
emits it — only the retraction driver assembles a program containing it (the privilege gate),
so monotonicity is now a POLICY the driver imposes between passes, not an opcode refusal within
a pass. There is also NO `CHECK-ABSENT`/NAC opcode: the matching core is purely positive
(negation is materialized as a positive attribute and matched positively — the decide/
de-pythonization line).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterator

from .attrgraph import AttrGraph, Attr, GRADED, VALUED, NAME, CONF


def _pred_key(attrs: dict) -> str | None:
    """The domain predicate carried in a MINT's attrs — its single non-reserved, non-CONF GRADED key
    (Phase 2.3: the relation's predicate is the graded key, no longer the VALUED `name` bridge)."""
    for k, a in attrs.items():
        if a.kind == GRADED and k != CONF and not (k.startswith("<") and k.endswith(">")):
            return k
    return None


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class ProgramError(Exception):
    """A malformed program (e.g. a matching opcode after an effect opcode)."""


_MISSING = object()   # "no value carried" sentinel (distinct from a carried None) for `_first_valued`


class ControlEdgeError(Exception):
    """DROP_CTRL was pointed at a FACT edge. The invariant made an error, not a deletion:
    reasoning never deletes a fact edge (vision.md §5) — there is no opcode for it."""


class SchemaError(Exception):
    """An opcode referenced an off-schema attribute key (raised by AttrGraph)."""


# ---------------------------------------------------------------------------
# Comparators (valued attributes) and t-norms (graded composition)
# ---------------------------------------------------------------------------

def _cmp(a: object, op: str, b: object) -> bool:
    if op == "=":
        return a == b
    if op == "<=":
        return a <= b            # type: ignore[operator]
    if op == ">=":
        return a >= b            # type: ignore[operator]
    if op == "<":
        return a < b             # type: ignore[operator]
    if op == ">":
        return a > b             # type: ignore[operator]
    if op == "~=":               # approximate: numeric tolerance, else equality
        try:
            return abs(float(a) - float(b)) <= 1e-9
        except (TypeError, ValueError):
            return a == b
    raise ValueError(f"unknown comparator {op!r} (expected =, <, >, <=, >=, ~=)")


TNorm = Callable[[float, float], float]

T_MIN: TNorm = lambda x, y: min(x, y)          # Godel  (idempotent; matches graded_degree)
T_PROD: TNorm = lambda x, y: x * y             # Goguen (product)


# ---------------------------------------------------------------------------
# Machine state
# ---------------------------------------------------------------------------

@dataclass
class State:
    regs: dict[str, str] = field(default_factory=dict)
    score: float = 1.0

    def bind(self, reg: str, nid: str) -> "State":
        r = dict(self.regs)
        r[reg] = nid
        return State(r, self.score)

    def scaled(self, degree: float, tnorm: TNorm) -> "State":
        return State(dict(self.regs), tnorm(self.score, degree))


# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------

class Instr:
    """Base opcode. `is_effect` splits the two phases (see module docstring)."""
    is_effect = False


# --- Matching core (purely positive) ---------------------------------------

@dataclass
class SEED(Instr):
    """Bind `reg` to each node carrying attribute `key` (the rarest anchor in a real machine).
    Enumerates candidates BY KEY only; an optional valued `(cmp, value)` filters each candidate
    — never an index by value (the label guard). ONE sanctioned exception: an equality SEED on
    the reserved NAME key uses the O(1) lexical accelerator (`nodes_named`), the KB-blessed
    discriminating index (Phase 2.3) — a df-seed, not a general value index."""
    reg: str
    key: str
    cmp: str | None = None       # None = key-presence seed; else valued comparison
    value: object = None


@dataclass
class FOLLOW(Instr):
    """Pointer-register cursor: bind `dst` to each out- (or in-) neighbour of `src` across a
    bare directed edge. The primitive edge step; JOIN is FOLLOW + TEST."""
    dst: str
    src: str
    direction: str = "out"       # "out" | "in"


@dataclass
class TEST(Instr):
    """Crisp filter: the node in `reg` must carry `key` (and, if `cmp` given, satisfy the
    valued comparison). No score change. `absent=True` INVERTS to a TEST-ABSENT — keep the
    state iff the node does NOT carry `key`: the fact-read attribute guard primitive
    (firmware §3/A5), emitted by the lowering compiler so a read never binds control/inert
    scaffolding — an ordinary attribute test, never a privileged matcher skip."""
    reg: str
    key: str
    cmp: str | None = None
    value: object = None
    absent: bool = False


@dataclass
class JOIN(Instr):
    """Sugar: FOLLOW `src`->`dst` then TEST `dst`. The rule-level positive join in one op."""
    dst: str
    src: str
    direction: str = "out"
    key: str | None = None
    cmp: str | None = None
    value: object = None


@dataclass
class GRADE(Instr):
    """Filter an already-bound register on a graded OR valued attribute (the dual role of the
    design's GRADE row). Graded mode (`threshold` given): alpha-cut degree >= threshold, and
    compose the degree into `score` by the machine t-norm. Valued mode (`cmp` given): a crisp
    value comparison, score unchanged."""
    reg: str
    key: str
    threshold: float | None = None   # graded alpha-cut
    cmp: str | None = None           # valued comparison
    value: object = None


@dataclass
class FUZZY(Instr):
    """Graded SEED (soft unification): bind `reg` to each node whose graded `key` degree is
    >= `threshold`, composing the degree into `score` by the t-norm. This is the
    candidate-introducing graded op (in a real machine, an ANN index over embeddings); GRADE
    only filters a bound register. A graded JOIN is FOLLOW then FUZZY."""
    reg: str
    key: str
    threshold: float = 0.0


@dataclass
class SET(Instr):
    """Bind `reg` directly to a known ground identity `nid` (WAM SET)."""
    reg: str
    nid: str


@dataclass
class DUP(Instr):
    """Copy register `src` into `dst` (WAM DUP)."""
    dst: str
    src: str


@dataclass
class SAME(Instr):
    """Register unification: keep the state iff `a` and `b` are bound to the SAME node (WAM
    get_value). This is the join-consistency check for a pattern whose endpoint is ALREADY
    bound — reached by FOLLOW to a temp register, then SAME against the bound one. Positive
    and monotone (a filter, never a bind)."""
    a: str
    b: str


@dataclass
class ITERATE(Instr):
    """Bounded control-flow: FORK the state stream over `range(count)`, binding `counter` to each index
    in the register file (`State.regs`) — a LOOP whose counter is a REGISTER value, never a MINT-ed
    `<iter>`/`<round>` graph node (mechanism_policy_separation.md §8, Axis B: "control-flow ISA ops like
    ITERATE over a loop register, instead of MINT-ed control nodes"; a loop counter explains nothing → it
    is register state, not a fact). It fits the machine's model exactly: the match phase is ALREADY a
    nondeterministic fork (SEED forks over candidates), so a bounded loop is a fork over a range — the
    effect phase then runs the body ONCE PER iteration, in index order. Positive/monotone (a fork, never a
    graph read or write): purely a matching op. This is PARALLEL/MAP iteration (each index independent —
    the body of iteration `i` cannot see iteration `i-1`); a stateful ACCUMULATING loop is the driver's
    fixpoint (`run_bank`/`run_to_fixpoint`), whose round counter is likewise a Python-local register.

    `count` is a literal bound (the common case); reading it from a register — a dynamic trip count —
    is a later refinement. The counter binding is a VALUED literal (an int), the same register file that
    holds node identities and SET's literals; a body effect that wants to STAMP the index reads it there."""
    counter: str
    count: int


@dataclass
class MEMBER(Instr):
    """Register-pointed LIVE-SET restriction (firmware §5/A5 — bounded attention as MECHANISM):
    keep the state iff the live-set register `live` (a key in `AttrGraph.registers`, the control-
    register file) is absent/None — no restriction — or ANY of `regs`' bound nodes has its NAME in
    the set. Set CONTENTS are driver POLICY (a focus frame's working set); this membership test is
    the machine mechanism — the first op of the §5 focus/scope live-set unification. The any-of
    disjunction is the focus semantic: a fact is in attention iff it TOUCHES the working set."""
    regs: tuple[str, ...]
    live: str


@dataclass
class OVERLAY(Instr):
    """Register-pointed live-set EXTENSION (firmware §5/A5 — the 'extend' face of the membership
    primitive; MEMBER is the 'restrict' face): keep the state iff the node in `reg` does NOT carry
    `key` (the BASE — e.g. a fact rel, no `<control>` marker), OR the live-set register `live` holds
    a set containing the node's ID (the OVERLAY — e.g. the active SUPPOSE scope's pencil rels,
    visible in-scope although control-marked). With no set parked the op degenerates to the plain
    absent-test, so ONE program shape serves scoped and unscoped reads. Set contents are driver
    policy; this test is mechanism."""
    reg: str
    key: str
    live: str


@dataclass
class VMATCH(Instr):
    """Value-JOIN filter: keep the state iff two ALREADY-bound registers carry MATCHING values on
    `key` — the TWO-register sibling of GRADE (which tests one register). The ONE op both engines run
    for a declared `ValueMatch` (coreference-as-rules Stage 1/4): the forward path lowers to it, and
    the demand chain runs it as an ephemeral program (`chain._vmatches_pass`, (X)). Unlike SAME (which needs the same NODE), VMATCH
    relates DISTINCT nodes that agree on a value — the join the path language cannot otherwise express.
    Exact mode (`threshold` None): both carry EQUAL VALUED `key` values (e.g. the same `name`). Graded
    mode (`threshold` given): both carry a GRADED `key` degree and `1 - |da - db| >= threshold`. A
    missing/wrong-kind value on either side fails (never fire on an unevaluable join). Positive,
    monotone (a filter, never a bind)."""
    a: str
    b: str
    key: str
    threshold: float | None = None


# --- Effects (monotone facts + gated control) ------------------------------

@dataclass
class MINT(Instr):
    """Create a fresh label-less node (Skolem witness / relation event / chunk head), write
    `attrs`, wire bare directed edges, and bind `out` to it. Monotone (additive).
    `edges` are OUT-edges (new -> target reg); `in_edges` are IN-edges (source reg -> new) —
    a reified relation `subject -> [rel] -> object` is `MINT(rel, in_edges=[subj], edges=[obj])`.
    `control=True` mints a control-layer node.

    `intern=True` CANONICALIZES by name: if a node named `attrs[NAME]` already exists, bind `out`
    to it (the graph-wide one, insertion-first) instead of minting a duplicate. This reproduces
    `rewriter.apply_rule.resolve_so`'s plain-literal branch (`nodes_named(nm)[0]`, else create), so
    a head endpoint that is a PLAIN LITERAL (`have_valuable`, `<yes>`, a category) shares ONE node
    across firings — which is what lets a downstream rule join two head-derived literals by NODE
    identity (a fresh node per firing would split `?c` and silently break the join). Skolems /
    RHS-only vars stay `intern=False` (value invention MINTs fresh per firing).

    `dedup=True` (for a reified RELATION node — exactly one `in_edge` subject, one out `edge`
    object, a NAME) reuses an existing `subject -> [name] -> object` instead of minting a
    duplicate, reproducing `rewriter.apply_rule`'s `_relation_exists` guard. Without it a fresh
    rel node per firing accretes across outer control cycles, so the graph's EDGE set (identity,
    not triples) never reaches a fixpoint and the planner's `_fingerprint` loop never settles."""
    out: str
    attrs: dict[str, Attr] = field(default_factory=dict)
    edges: list[str] = field(default_factory=list)      # target register names (bare out-edges)
    in_edges: list[str] = field(default_factory=list)   # source register names (bare in-edges)
    control: bool = False
    intern: bool = False
    dedup: bool = False
    is_effect = True


@dataclass
class EMIT(Instr):
    """Assert a fact attribute on the node in `reg` (monotone). Graded: raise `key` to
    max(old, value (x) score) — a degree only goes up. Valued: assert `key = value` (data).

    DYNAMIC KEY: when `key_reg` is set the attribute key is the NAME of the node in that register
    (resolved at apply time), not the static `key`. This is how a `propagate` embedding-write whose
    dimension is a BOUND variable (`?adj` -> "urgent") lowers — the write target is `reg`, the dim
    is `name(regs[key_reg])`. `raise_degree=False` SETS the graded attr (overwrite, ignoring score),
    the embedding-write semantics `rewriter`'s `set_embedding` gives; the default `True` is the
    monotone max-raise a derived degree uses."""
    reg: str
    key: str
    value: object
    kind: str = GRADED
    key_reg: str | None = None
    raise_degree: bool = True
    is_effect = True


@dataclass
class DROP_CTRL(Instr):
    """Delete the bare edge regs[src] -> regs[dst]. Control-layer ONLY: raises
    `ControlEdgeError` on a fact edge. This is where the no-fact-deletion invariant lives — as
    a refusal in the one deleting opcode, not a lint pass."""
    src: str
    dst: str
    is_effect = True


@dataclass
class INTERPOSE(Instr):
    """Hide the edge  regs[rel] -> regs[obj]  REVERSIBLY by splicing a fresh control `marker`
    into the path:  rel -> obj  becomes  rel -> <marker> -> obj  (obj preserved). The SOLE
    sanctioned fact-edge mutation (isa-reference.md "Reserved: INTERPOSE / RESTORE") — §5 reframes
    from "no opcode mutates a fact edge" to "the sole fact-edge op is a reversible interposition
    that preserves its pre-image" (no IRREVERSIBLE loss; `RESTORE` is the exact inverse).

    Obliviousness is STRUCTURAL: after the splice `out(rel) = {marker}`, so `_relation_exists(s,
    rel, obj)` is false NATURALLY and the matcher (a dumb positive reader that skips the inert/
    control marker) never learns what retraction is. Because interposition is reversible, it is
    SAFE on any live edge — fact OR control (a retractable walker shortcut is control-stamped) — so
    this asserts only that the edge exists, not that it is a fact (unlike the spec's illustrative
    `edge_is_fact` pre-check); no reader change is needed either way. `out` (optional) binds the
    minted marker so an inverse-op rule can find it."""
    rel: str
    obj: str
    marker_name: str
    out: str | None = None
    is_effect = True


@dataclass
class RESTORE(Instr):
    """The exact inverse of `INTERPOSE`: un-hide  rel -> marker -> obj  back to  rel -> obj,
    dropping the marker's two bare edges and reconstructing the original edge. A `<reconsider>`
    rule emits this on new evidence (belief revision as pure banks). `INTERPOSE ∘ RESTORE =
    identity` on the graph's edge set — the checkable structural guarantee behind §5."""
    rel: str
    marker: str
    obj: str
    is_effect = True


@dataclass
class RETIRE(Instr):
    """PRIVILEGED fact-deletion mechanism (mechanism_policy_separation.md, Probe 1): really delete
    the reified relation in `regs[rel]` — its subject->rel and rel->object bare edges AND the rel
    node itself. Unlike `DROP_CTRL` it does NOT consult `edge_is_fact` and does NOT refuse a fact
    edge: deleting a live fact relation is its whole PURPOSE. This is the raw mechanism the
    retraction (and later GC) policy wields — the honest "delete" behind copy-on-delete.

    It carries NO archiving: the "copy" of copy-on-delete is POLICY, done by the retraction driver
    (record_history) BEFORE this runs — baking archiving into the opcode would re-conflate mechanism
    and policy. The opcode just deletes.

    THE PRIVILEGE GATE is structural: `RETIRE` is NOT in the rule->program lowering vocabulary
    (`lowering.lower_rhs`/`lower_rewire`/… never emit it). Only the retraction policy driver
    assembles a program containing it, so ordinary reasoning rules CANNOT delete a fact
    (soundness-by-construction for reasoning is preserved), while the policy layer wields real
    deletion — the mechanism/policy split made concrete. By the time it runs, `record_history` has
    redirected `rel`'s inert provenance (proves/uses) onto the archive record, so `rel`'s only
    remaining edges are the live fact edges this drops."""
    rel: str
    is_effect = True


# ---------------------------------------------------------------------------
# The interpreter
# ---------------------------------------------------------------------------

class Machine:
    """Executes an instruction sequence over an `AttrGraph`. See module docstring."""

    def __init__(self, tnorm: TNorm = T_MIN, *, skip_inert: bool = False) -> None:
        self.tnorm = tnorm
        # `skip_inert` = never bind a SEED/FOLLOW/JOIN candidate that is provenance-inert (a `<j:…>`
        # justification, `proves`/`uses`, `<axiom>`/`<quarantine>`/`<retracted>`). The pure reference
        # matcher (default OFF) sees every node; the PRODUCTION forward driver (`run_bank`) turns it ON
        # so matching sees only FACTS — exactly `rewriter._match` / `GoalSolver._facts_matching`, which
        # skip inert. Without it, a `uses`->fact provenance edge is walked as if it were a fact edge
        # (e.g. `?s first if?` binding `?s` to the `uses` node that justified the `first` relation).
        self.skip_inert = skip_inert

    # --- matching transitions (state -> zero-or-more states) ---------------

    def _inert(self, g: AttrGraph, nid: str) -> bool:
        # Called ONLY when `skip_inert` is on (guarded by `self.skip_inert and ...` at each call site,
        # so the OFF path pays nothing — not even this call). Phase 2.2: the node's dedicated
        # `inert` flag (set at every provenance mint site), not a name-string sniff. A per-machine
        # memo keyed by nid was REMOVED (pystrider feedback #10, cold==warm): nids collide ACROSS
        # graphs (every graph mints n0, n1, …), so a machine shared over two graphs would serve one
        # graph's verdict to the other — and the memo saved nothing over this direct field read.
        return g.node(nid).inert

    def _match_step(self, g: AttrGraph, ins: Instr, st: State) -> Iterator[State]:
        if isinstance(ins, SET):
            yield st.bind(ins.reg, ins.nid)
        elif isinstance(ins, DUP):
            yield st.bind(ins.dst, st.regs[ins.src])
        elif isinstance(ins, SAME):
            if st.regs[ins.a] == st.regs[ins.b]:
                yield st
        elif isinstance(ins, ITERATE):
            for i in range(ins.count):           # fork the stream: one successor per loop index ...
                yield st.bind(ins.counter, i)    # ... the counter is a REGISTER value, not a graph node
        elif isinstance(ins, SEED):
            # Blessed name-index fast path: an equality SEED on the reserved NAME key hits the
            # O(1) lexical accelerator (`nodes_named`) instead of scanning EVERY named node and
            # comparing values one by one. `name` is the KB-blessed discriminating key (Phase 2.3
            # — `nodes_named`/`name_count` exist precisely as "the selectivity the matcher seeds
            # from"), so this is the sanctioned df-seed, not the forbidden general value index.
            # Semantically transparent: `_by_name` is kept in sync with the (always-VALUED) NAME
            # attr, so the candidate set is identical to the scan-and-filter path.
            if ins.key == NAME and ins.cmp == "=" and isinstance(ins.value, str):
                for nid in g.nodes_named(ins.value):
                    if self.skip_inert and self._inert(g, nid):
                        continue
                    yield st.bind(ins.reg, nid)
                return
            for nid in g.nodes_with_key(ins.key):
                if self.skip_inert and self._inert(g, nid):
                    continue
                if self._valued_ok(g, nid, ins.key, ins.cmp, ins.value):
                    yield st.bind(ins.reg, nid)
        elif isinstance(ins, FUZZY):
            for nid in g.nodes_with_key(ins.key):
                deg = self._graded_degree(g, nid, ins.key)
                if deg >= ins.threshold and deg > 0.0:
                    yield st.bind(ins.reg, nid).scaled(deg, self.tnorm)
        elif isinstance(ins, FOLLOW):
            src = st.regs[ins.src]
            nbrs = g.succ(src) if ins.direction == "out" else g.pred(src)
            for nid in nbrs:
                if self.skip_inert and self._inert(g, nid):
                    continue
                yield st.bind(ins.dst, nid)
        elif isinstance(ins, TEST):
            nid = st.regs[ins.reg]
            if ins.absent:                               # the fact-read attribute guard (test-absent)
                if not g.has_key(nid, ins.key):
                    yield st
            elif g.has_key(nid, ins.key) and self._valued_ok(g, nid, ins.key, ins.cmp, ins.value):
                yield st
        elif isinstance(ins, MEMBER):
            live = g.registers.get(ins.live)
            if live is None or any(g.name(st.regs[r]) in live for r in ins.regs):
                yield st
        elif isinstance(ins, OVERLAY):
            nid = st.regs[ins.reg]
            if not g.has_key(nid, ins.key):                # the base: an unmarked (fact) node
                yield st
            else:
                live = g.registers.get(ins.live)           # the overlay: in-scope marked nodes
                if live is not None and nid in live:
                    yield st
        elif isinstance(ins, JOIN):
            src = st.regs[ins.src]
            nbrs = g.succ(src) if ins.direction == "out" else g.pred(src)
            for nid in nbrs:
                if self.skip_inert and self._inert(g, nid):
                    continue
                if ins.key is not None:
                    if not g.has_key(nid, ins.key):
                        continue
                    if not self._valued_ok(g, nid, ins.key, ins.cmp, ins.value):
                        continue
                yield st.bind(ins.dst, nid)
        elif isinstance(ins, GRADE):
            # ISA VALUE OPERANDS (docs/isa_value_operands_design.md §1/§3): the register may hold a
            # VALUE-NODE, whose denotation is the coref class of same-named entities — the instruction
            # interprets it, aggregating max-over-mentions (graded) / first-carried-value (valued),
            # exactly the demand chain's α-cut semantics (`chain._grades_pass` runs THIS op). An
            # entity register denotes itself, so
            # the single-node behaviour is unchanged (the forward path never binds value-nodes today).
            cands = self._operand_nodes(g, st.regs[ins.reg])
            if ins.threshold is not None:                # graded alpha-cut (max over the denotation)
                deg = self._max_graded(g, cands, ins.key)
                if deg >= ins.threshold and deg > 0.0:
                    yield st.scaled(deg, self.tnorm)
            elif ins.cmp is not None:                    # valued comparison (first carried value)
                val = self._first_valued(g, cands, ins.key)
                if val is not _MISSING and _cmp(val, ins.cmp, ins.value):
                    yield st
            else:
                raise ProgramError("GRADE needs either a graded threshold or a valued cmp")
        elif isinstance(ins, VMATCH):
            ca = self._operand_nodes(g, st.regs[ins.a])
            cb = self._operand_nodes(g, st.regs[ins.b])
            if ins.threshold is None:                    # exact VALUED equality
                va = self._first_valued(g, ca, ins.key)
                vb = self._first_valued(g, cb, ins.key)
                if va is not _MISSING and vb is not _MISSING and va == vb:
                    yield st
            else:                                        # graded 'close enough'
                da = self._graded_or_none(g, ca, ins.key)
                db = self._graded_or_none(g, cb, ins.key)
                if da is not None and db is not None and (1.0 - abs(da - db)) >= ins.threshold:
                    yield st
        else:
            raise ProgramError(f"{type(ins).__name__} is an effect opcode in the match phase")

    def _operand_nodes(self, g: AttrGraph, nid: str) -> tuple[str, ...]:
        """The fact-layer node(s) a register's node DENOTES (docs/isa_value_operands_design.md): a
        VALUE-NODE (carries `<isa_operand_value>`) denotes the entities NAMED its value — the coref-
        class aggregate the carried name refers to, control/inert scaffolding skipped; any other node
        denotes itself. Resolution lives INSIDE the instruction (§3), never in the substrate."""
        v = g.operand_value(nid)
        if v is None:
            return (nid,)
        return tuple(n for n in g.nodes_named(v) if not (g.is_control(n) or g.is_inert(n)))

    def _first_valued(self, g: AttrGraph, cands: tuple[str, ...], key: str) -> object:
        """The first VALUED `key` value carried across a denotation (`_MISSING` when none carries it —
        distinct from a carried None value). The demand chain's `valued_of` aggregation."""
        for n in cands:
            a = g.get_attr(n, key)
            if a is not None and a.kind == VALUED:
                return a.value
        return _MISSING

    def _max_graded(self, g: AttrGraph, cands: tuple[str, ...], key: str) -> float:
        """Max GRADED `key` degree over a denotation, 0.0 when absent (GRADE's `deg > 0` guard then
        fails). The demand chain's max-over-mentions aggregation, now inside the instruction."""
        deg = 0.0
        for n in cands:
            a = g.get_attr(n, key)
            if a is not None and a.kind == GRADED:
                deg = max(deg, float(a.value))
        return deg

    def _graded_or_none(self, g: AttrGraph, cands: tuple[str, ...], key: str) -> float | None:
        """Like `_max_graded` but None when NO candidate carries a GRADED `key` — VMATCH must
        distinguish ABSENT (unevaluable join -> fail) from a present 0.0 degree (evaluable)."""
        deg: float | None = None
        for n in cands:
            a = g.get_attr(n, key)
            if a is not None and a.kind == GRADED:
                deg = float(a.value) if deg is None else max(deg, float(a.value))
        return deg

    def _valued_ok(self, g: AttrGraph, nid: str, key: str, cmp: str | None, value: object) -> bool:
        if cmp is None:
            return True
        attr = g.get_attr(nid, key)
        return attr is not None and attr.kind == VALUED and _cmp(attr.value, cmp, value)

    def _graded_degree(self, g: AttrGraph, nid: str, key: str) -> float:
        attr = g.get_attr(nid, key)
        return float(attr.value) if (attr is not None and attr.kind == GRADED) else 0.0

    # --- effect application (mutates the graph) ----------------------------

    def _apply(self, g: AttrGraph, ins: Instr, st: State) -> State:
        if isinstance(ins, MINT):
            new = None
            if ins.intern:                       # canonicalize a plain literal to its graph-wide node
                name_attr = ins.attrs.get(NAME)  # (rewriter.resolve_so: reuse nodes_named(nm)[0])
                if name_attr is not None:
                    nm = str(name_attr.value)
                    for cand in g.nodes_named(nm):        # insertion-first, like nodes_named(nm)[0]
                        # KEY-AWARE INTERN (finding-interning-aliases-predicate-literals): a value-literal
                        # must canonicalize to another VALUE-literal / control token, NEVER to a reified
                        # DOMAIN-RELATION node. Post Phase 2.3 a domain relation carries NO valued name
                        # (its predicate is only a graded key), so `nodes_named(nm)` cannot return one —
                        # the aliasing hazard is now structurally impossible. This graded-key guard is kept
                        # as defence in depth (and still excludes a would-be domain-rel candidate should one
                        # ever carry both a valued name and a same-named graded key); a control token
                        # (`<yes>`) carries a graded key == its name but IS a legit intern target, so
                        # exclude only NON-reserved (domain-predicate) names.
                        ka = g.get_attr(cand, nm)
                        is_domain_rel = (ka is not None and ka.kind == GRADED
                                         and not (nm.startswith("<") and nm.endswith(">")))
                        if not is_domain_rel:
                            new = cand
                            break
            if ins.dedup and new is None:        # reuse an existing subject -[pred]-> object
                pred = _pred_key(ins.attrs)      # Phase 2.3: match on the predicate KEY, not VALUED name
                if pred is not None and ins.in_edges and ins.edges:
                    subj, obj = st.regs[ins.in_edges[0]], st.regs[ins.edges[0]]
                    for r in g.succ(subj):
                        if g.has_key(r, pred) and obj in g.succ(r):
                            return st.bind(ins.out, r)   # relation already present -> no new edges
            if new is None:
                new = g.add_node(control=ins.control)
                for key, attr in ins.attrs.items():
                    g.set_attr(new, key, attr)
            for tgt in ins.edges:
                g.add_edge(new, st.regs[tgt])
            for src in ins.in_edges:
                g.add_edge(st.regs[src], new)
            return st.bind(ins.out, new)
        if isinstance(ins, EMIT):
            nid = st.regs[ins.reg]
            key = g.name(st.regs[ins.key_reg]) if ins.key_reg is not None else ins.key
            if ins.kind == GRADED:
                if ins.raise_degree:
                    g.raise_graded(nid, key, self.tnorm(st.score, float(ins.value)))
                else:                                    # embedding-write SET (rewriter.set_embedding)
                    g.set_attr(nid, key, Attr(GRADED, float(ins.value)))
            else:
                g.set_attr(nid, key, Attr(VALUED, ins.value))
            return st
        if isinstance(ins, DROP_CTRL):
            a, b = st.regs[ins.src], st.regs[ins.dst]
            if g.edge_is_fact(a, b):
                raise ControlEdgeError(
                    f"DROP_CTRL refused: {a}->{b} is a fact edge (reasoning never deletes a fact)"
                )
            g.remove_edge(a, b)
            return st
        if isinstance(ins, INTERPOSE):
            rel, obj = st.regs[ins.rel], st.regs[ins.obj]
            # CANONICALIZE the marker (rewriter.resolve_so's reuse-if-exists for a plain literal):
            # re-interposing an already-interposed edge (a NEW candidate match forms every round
            # otherwise, since `rel`'s new successor is a genuinely fresh node the matcher can bind
            # `?o` to again — an unbounded interpose chain, `rel -> m1 -> m2 -> m3 -> ...`) collapses
            # onto the SAME shared marker instead of minting a fresh one each time, so a repeat
            # firing becomes an idempotent self-splice the fired-set then suppresses. Matches the
            # reference oracle's behavior exactly (rewriter mints markers via `resolve_so`, which is
            # canonicalizing for every plain-literal RHS/rewire token).
            existing = g.nodes_named(ins.marker_name)
            m = existing[0] if existing else g.add_node(ins.marker_name, control=True)
            g.remove_edge(rel, obj)                          # redirect rel's object edge ...
            g.add_edge(rel, m); g.add_edge(m, obj)           # ... through the marker (obj preserved)
            return st.bind(ins.out, m) if ins.out is not None else st
        if isinstance(ins, RESTORE):
            rel, m, obj = st.regs[ins.rel], st.regs[ins.marker], st.regs[ins.obj]
            g.remove_edge(rel, m); g.remove_edge(m, obj)     # drop the marker's two bare edges ...
            g.add_edge(rel, obj)                             # ... reconstruct the original edge
            return st
        if isinstance(ins, RETIRE):
            # Privileged real deletion: remove the rel node and every edge touching it (its live
            # subject->rel / rel->object fact edges — provenance was redirected off it first by the
            # driver's record_history). NO fact-edge refusal: deletion is the point (see RETIRE doc).
            g.remove_node(st.regs[ins.rel])
            return st
        raise ProgramError(f"{type(ins).__name__} is a matching opcode in the apply phase")

    # --- the driver --------------------------------------------------------

    @staticmethod
    def split(program: list[Instr]) -> tuple[list[Instr], list[Instr]]:
        """Partition a well-formed program into (match_ops, effect_ops). A matching opcode
        after an effect opcode is malformed (the match-then-apply discipline)."""
        seen_effect = False
        match_ops: list[Instr] = []
        effect_ops: list[Instr] = []
        for ins in program:
            if ins.is_effect:
                seen_effect = True
                effect_ops.append(ins)
            else:
                if seen_effect:
                    raise ProgramError(
                        f"matching opcode {type(ins).__name__} after an effect opcode "
                        "(a well-formed program is match-then-apply)"
                    )
                match_ops.append(ins)
        return match_ops, effect_ops

    def match(self, g: AttrGraph, match_ops: list[Instr],
              init: list[State] | None = None) -> list[State]:
        """Run the match phase only: fold the state stream through the matching opcodes.
        No graph mutation, so a scheduler can inspect the states (e.g. for fired-suppression)
        before deciding which to apply. `init` seeds the stream (default a single empty state);
        a NAC sub-program is run with `init=[<the candidate firing's state>]` so its LHS bindings
        are already in the register file (the forward NAC filter — see `lowering.run_bank`)."""
        states: list[State] = list(init) if init is not None else [State()]
        for ins in match_ops:
            nxt: list[State] = []
            for st in states:
                try:
                    nxt.extend(self._match_step(g, ins, st))
                except KeyError as e:                    # unbound register reference
                    raise ProgramError(f"{type(ins).__name__} referenced unbound register {e}")
            states = nxt
        return states

    def apply(self, g: AttrGraph, effect_ops: list[Instr], st: State) -> State:
        """Run the effect phase for one state, in order, mutating the graph. Returns the state
        with any post-apply bindings (a MINT's `out`)."""
        cur = st
        for ins in effect_ops:
            try:
                cur = self._apply(g, ins, cur)
            except KeyError as e:
                raise ProgramError(f"{type(ins).__name__} referenced unbound register {e}")
        return cur

    def run(self, g: AttrGraph, program: list[Instr]) -> list[State]:
        match_ops, effect_ops = self.split(program)
        states = self.match(g, match_ops)
        # Apply the effects for each surviving state, in state order. The returned states carry
        # post-apply bindings, so a caller can read back the nodes a firing produced.
        return [self.apply(g, effect_ops, st) for st in states]


def run_program(g: AttrGraph, program: list[Instr], *, tnorm: TNorm = T_MIN) -> list[State]:
    """Convenience: run `program` over `g` (mutated in place) and return the surviving match
    states. See `Machine`."""
    return Machine(tnorm=tnorm).run(g, program)


# ===========================================================================
# The control machine — control flow as instructions, not procedures
# ===========================================================================
#
# docs/isa_control_machine.md §4 (brick #1). The `Machine` above is a straight-line basic
# block: match-then-apply over a state stream, run ONCE, with NO program counter and NO way to
# transfer control — every loop/branch/subgoal is faked in a Python driver (`run_bank`,
# `chain_sip`, `service_calls`) or hidden INSIDE an opcode (`ITERATE`'s Python `for`). That
# hidden control is exactly what cannot compose: a loop whose body needs a subgoal is
# inexpressible (the SEAM). This layer adds the missing CONTROL PATH — a PC over an addressable
# program of labeled basic blocks, plus the primitive control transfers (`BRANCH`/`BRANCH_IF`)
# and a minimal loop kit on SCALAR control registers (`SETI`/`DEC`) — so a bounded loop is a
# branch-back over a basic block instead of a `for` inside an opcode.
#
# Brick #1 is deliberately narrow: PC + BRANCH + BRANCH_IF + SETI + DEC, differential-tested to
# reproduce `ITERATE`'s effects with primitive control (tests/test_isa_control_machine.py).
# `CALL`/`RET` + the control stack (arbitrary-depth subgoals) are brick #2; the state stream
# threaded across blocks stays the basic-block primitive's `list[State]` (§10: "value between
# blocks is a set of states; loop counters + control stack are scalar control registers").
# `ITERATE` STAYS as the REP/SIMD data-parallel convenience — it is no longer the ONLY loop.


# --- Scalar control-register ops (the minimal loop kit) --------------------
#
# SETI/DEC touch the machine's SCALAR CONTROL REGISTERS — a home distinct from BOTH `State.regs`
# (per-state node bindings, forked by matching) AND the graph (facts/explanation). A loop counter
# is neither a fact nor a node binding: it is "how the machine steps" (mechanism_policy_separation
# Axis B). It lives in a machine-level control context (`ControlMachine.ctrl`), the §4.3-sanctioned
# alternative to `AttrGraph.registers` — loop counters are ephemeral to one control-machine run and
# need not persist, unlike the control stack/memo table (brick #2) which will use `AttrGraph.registers`
# for free suspend/resume. These are NOT `Instr` (never match nor effect) — they never enter a block
# body; they run in the block's separate `control` phase, so the two-phase match-then-apply stays
# pure within a block (§10).

@dataclass
class SETI:
    """Set scalar control register `reg` to integer `value` (the loop-counter initializer of
    `SETI i,N; L: <body>; DEC i; BRANCH_IF i>0,L`). A control-register op, not a graph op."""
    reg: str
    value: int


@dataclass
class DEC:
    """Decrement scalar control register `reg` by 1 (the loop step). A control-register op."""
    reg: str


# --- Basic-block terminators (the control transfers) ----------------------

class Term:
    """A basic block's TERMINATOR: after the block's match-then-apply body and its scalar-control
    phase, the terminator sets the next PC. This is where control transfers live (the ISA's
    JMP/JZ row). Neither match nor effect — a block-terminator PHASE (§10)."""


@dataclass
class FALL(Term):
    """Fall through to the next block in program order (the default terminator; `PC += 1`)."""


@dataclass
class BRANCH(Term):
    """Unconditional branch: `PC = label`. (The ISA `JMP`.)"""
    label: str


@dataclass
class BRANCH_IF(Term):
    """Conditional branch on a SCALAR control register: if `ctrl[reg] cmp value`, `PC = label`;
    else fall through. (The ISA `JZ/JNZ`.) A loop is a branch-BACK to the body's label — e.g.
    `BRANCH_IF("i", ">", 0, "L")` re-enters block `L` while the counter is positive."""
    reg: str
    cmp: str
    value: object
    label: str


@dataclass
class CALL(Term):
    """Call a subroutine (brick #2, docs/isa_control_machine.md §4.2). PUSH a frame — the return-PC
    (`pc+1`, the block after this CALL) and the caller's saved register window (its state stream +
    scalar-control snapshot) — onto the CONTROL STACK, then `PC = label`. The callee begins with a
    FRESH window (a single empty state); the graph is SHARED, so the callee's fact writes persist and
    the caller reads them back after `RET`. Subgoals compose to ANY depth via the stack — this is the
    WAM environment stack that `chain_sip`'s Python recursion fakes today (brick #3 ports it here).

    The caller's scalar-control snapshot is INHERITED live by the callee (so a counter can pass an
    argument down — `DEC n; CALL rec`) and RESTORED on `RET` (caller-saved registers), giving each
    recursion frame its own counter without a graph node."""
    label: str


@dataclass
class RET(Term):
    """Return from a subroutine (brick #2). POP a frame from the control stack, RESTORE the caller's
    saved register window (state stream + control snapshot) and set `PC` to the frame's return-PC. The
    callee's GRAPH effects persist (shared graph); only its register window is discarded. An empty
    stack is a `ProgramError` (a `RET` with no matching `CALL`)."""


@dataclass
class HALT(Term):
    """Stop the control machine (return the current state stream)."""


@dataclass
class SUSPEND(Term):
    """Pause the machine and hand a resumable CONTINUATION back to the caller (docs/isa_control_machine.md
    §4.2 — "save/restore the whole control stack + PC as a continuation"). Unlike `HALT` (done) or `RET`
    (return within the machine), `SUSPEND` yields control OUT to the driver that called `run`/`resume`,
    capturing the FULL control state (resume-PC, control stack, control registers, state stream) as a
    `Continuation`. The driver services the pending REQUEST — an external wait (a tool `<call>`, an
    `ask_user`), OR an internal sub-solve (the NAC negative subgoal, brick #3: a work-step yields "close
    goal L" mid-computation) — then calls `ControlMachine.resume(...)` to continue exactly where it paused.

    `request_reg` (optional) names the control register holding the request payload a preceding work step
    computed; it is copied onto `Continuation.request` so the driver can dispatch on it. Resume-PC is the
    NEXT block (fall-through after the wait), so the response a preceding-set register carries is read by
    the block after `SUSPEND`."""
    request_reg: str | None = None


@dataclass
class Continuation:
    """A SUSPENDed control machine, captured as a resumable value (§4.2). Holds the full control state —
    the block `program`, the resume `pc`, the control `stack`, the control registers `ctrl`, the state
    `stream`, and the pending `request` (what the suspend is asking for). `ControlMachine.resume(g, cont,
    ...)` restores this context and runs on. No graph snapshot: the graph is SHARED and monotone, so the
    driver's between-suspend mutations (a folded-in tool result) are simply visible on resume. For a
    DURABLE continuation (serialize, resume across a restart) the stack/regs would live in
    `AttrGraph.registers`, which `g.copy()` deep-copies (§10) — not needed for in-process suspend/resume."""
    program: list
    pc: int
    stack: list
    ctrl: dict
    stream: list
    request: object = None


@dataclass
class PRIM:
    """An upper-level INTERPRETER STEP (docs/isa_control_machine.md §10, "two levels of program").

    The control machine has two client programs: the ISA-level match-then-apply opcodes (a block's
    `body`), and — layered ON TOP — the reified-rule / demand REASONING program, "interpreted on top,
    data-directed" (§10). A `PRIM` is one primitive step of that upper interpreter — a Python callable
    the control machine SEQUENCES but does not itself decode (match a body atom, close a subgoal, run
    one fixpoint round). It is the escape hatch that lets the control machine RUN the demand solver /
    fixpoint driver (bricks #3–5) while CONTROL (loop/branch/call/ret) stays in the ISA: the data-plane
    work is the callable, the control-plane is the PC — the analogue of a real CPU where an instruction
    computes a value + a flag and `BRANCH` tests the flag.

    Contract: `fn(g, stream, ctrl) -> (new_stream, flag)`. The returned `new_stream` threads on to the
    next block (like a body's output); if `out` is set, `flag` is written to control register `out` so
    a following `BRANCH_IF` can branch on the step's OUTCOME — e.g. a fixpoint round returns
    `flag = 1 if it derived a new fact else 0` and the loop is `BRANCH_IF(out, ">", 0, round_label)`
    (run_bank's "branch-back over a changed? flag", §9.5); a tabled solve returns `flag = already-tabled?`
    for the `BRANCH_IF already-tabled` memo consult (§10). `fn` mutates the shared graph in place."""
    fn: "Callable[[AttrGraph, list[State], dict], tuple[list[State], object]]"
    out: str | None = None


@dataclass
class Block:
    """A labeled basic block — the addressable unit the PC indexes (docs/isa_control_machine.md §4).

    A block runs, in order:
      * `body` OR `prim` — the WORK. Either the ISA match-then-apply `body` (ordinary `Instr` opcodes,
                    run by the underlying `Machine` — the BASIC-BLOCK PRIMITIVE, unchanged) OR a single
                    upper-level `prim` interpreter step (§10). A block sets at most one; a `prim` block
                    keeps `body` empty (they are the two levels of program, not mixed within a block).
      * `control` — scalar control-register ops (`SETI`/`DEC`) on `ControlMachine.ctrl`.
      * `term`    — the terminator (`FALL`/`BRANCH`/`BRANCH_IF`/`CALL`/`RET`/`HALT`) that sets the
                    next PC (and, for `CALL`/`RET`, moves the control stack).

    A program is an ordered `list[Block]`; blocks with a `label` are branch targets. Fall-through is
    program order, so a `FALL` block hands its output state stream to `blocks[pc+1]`."""
    body: list[Instr] = field(default_factory=list)
    prim: PRIM | None = None
    control: list = field(default_factory=list)     # SETI / DEC
    term: Term = field(default_factory=FALL)
    label: str | None = None


class ControlMachine:
    """Fetch-decode-execute over a PC-indexed program of `Block`s — the control path the ISA lacked
    (docs/isa_control_machine.md §4, brick #1). Wraps the straight-line `Machine` (the basic-block
    primitive) with a program counter, scalar control registers, and control transfers, so loops
    (and later subgoals) COMPOSE as instructions instead of Python drivers.

    Execution threads a state stream (`list[State]`, §10 "value between blocks is a set of states")
    from block to block: each block runs `Machine.match` then `Machine.apply` over the incoming
    stream (mutating `g`), runs its scalar-control ops, then its terminator picks the next PC. A
    back-edge (`BRANCH_IF`/`BRANCH` to an earlier label) is a loop; the counter lives in `self.ctrl`.
    `CALL`/`RET` push/pop the CONTROL STACK (`self.stack`) — return-PC + the caller's saved register
    window — so subgoals nest to arbitrary depth in the machine, not in Python recursion (brick #2).
    `SUSPEND` captures the whole control state as a resumable `Continuation` handed to the driver, and
    `resume` continues it (brick #4) — the mechanism a mid-computation subgoal or an external tool/
    ask-user wait needs. `PRIM` blocks run upper-level interpreter steps the loop sequences (§10).

    Correctness-first (the standing rule): naive fetch-decode-execute, no compilation. `max_steps`
    guards a runaway loop or unbounded recursion with a `ProgramError` rather than hanging."""

    def __init__(self, tnorm: TNorm = T_MIN, *, skip_inert: bool = False,
                 max_steps: int = 1_000_000) -> None:
        self.machine = Machine(tnorm, skip_inert=skip_inert)
        self.max_steps = max_steps
        self.ctrl: dict[str, int] = {}     # scalar control registers (loop counters); reset per run
        # the control stack: frames of (return-PC, saved state stream, saved control snapshot). One
        # slot holding a growable Python list — the register IS the stack pointer, the stack grows in
        # machine memory (Axis B §5: no infinite registers, no graph nodes). Reset per run.
        self.stack: list[tuple[int, list[State], dict[str, int]]] = []

    def run(self, g: AttrGraph, program: list[Block],
            init: list[State] | None = None) -> "list[State] | Continuation":
        """Run `program` over `g` (mutated in place) from the entry block (index 0). Returns the final
        state stream on `HALT`/fall-off, or a `Continuation` if a `SUSPEND` paused it (the driver then
        services the request and calls `resume`). `init` seeds the stream (default a single empty state),
        exactly like `Machine.match`."""
        self._validate_labels(program)
        self.ctrl = {}
        self.stack = []
        stream: list[State] = list(init) if init is not None else [State()]
        return self._execute(g, program, 0, stream)

    def resume(self, g: AttrGraph, cont: Continuation,
               response: dict | None = None) -> "list[State] | Continuation":
        """Continue a `SUSPEND`ed machine from its `Continuation` (§4.2). `response` (optional) is the
        driver's answer — merged into the control registers so the block after the `SUSPEND` reads it.
        Restores the captured control stack + registers + stream and runs on `g` (which the driver may
        have mutated in the interim — the fold-in of a tool result). May itself `HALT` or `SUSPEND` again."""
        self.ctrl = dict(cont.ctrl)
        if response:
            self.ctrl.update(response)
        self.stack = list(cont.stack)
        return self._execute(g, cont.program, cont.pc, list(cont.stream))

    @staticmethod
    def _validate_labels(program: list[Block]) -> dict[str, int]:
        labels = {b.label: i for i, b in enumerate(program) if b.label is not None}
        for i, b in enumerate(program):                 # validate branch targets up front (loud, not a
            for tgt in _branch_targets(b.term):          # KeyError mid-run) — a mistyped label is a bug
                if tgt not in labels:
                    raise ProgramError(f"block {i} branches to undefined label {tgt!r}")
        return labels

    def _execute(self, g: AttrGraph, program: list[Block], pc: int,
                 stream: list[State]) -> "list[State] | Continuation":
        """The fetch-decode-execute loop, shared by `run` (from pc=0) and `resume` (from a saved pc).
        Uses `self.ctrl`/`self.stack` as the live control context (set up by the caller)."""
        labels = {b.label: i for i, b in enumerate(program) if b.label is not None}
        steps = 0
        while 0 <= pc < len(program):
            steps += 1
            if steps > self.max_steps:
                raise ProgramError(
                    f"control machine exceeded max_steps={self.max_steps} "
                    "(a nonterminating branch-back?)"
                )
            block = program[pc]
            # 1) the WORK phase: either an upper-level interpreter step (PRIM) or the ISA basic-block
            # primitive (match-then-apply over the incoming stream). A block is one level or the other.
            if block.prim is not None:
                if block.body:
                    raise ProgramError("a block sets EITHER body OR prim, not both (§10 two levels)")
                stream, flag = block.prim.fn(g, stream, self.ctrl)
                if block.prim.out is not None:
                    self.ctrl[block.prim.out] = flag
            else:
                match_ops, effect_ops = Machine.split(block.body)
                states = self.machine.match(g, match_ops, init=stream)
                stream = [self.machine.apply(g, effect_ops, st) for st in states]
            # 2) scalar-control phase: mutate the control registers
            for op in block.control:
                if isinstance(op, SETI):
                    self.ctrl[op.reg] = op.value
                elif isinstance(op, DEC):
                    self.ctrl[op.reg] = self.ctrl[op.reg] - 1
                else:
                    raise ProgramError(f"{type(op).__name__} is not a control-register op (SETI/DEC)")
            # 3) terminator: set the next PC
            term = block.term
            if isinstance(term, FALL):
                pc += 1
            elif isinstance(term, BRANCH):
                pc = labels[term.label]
            elif isinstance(term, BRANCH_IF):
                pc = labels[term.label] if _cmp(self.ctrl[term.reg], term.cmp, term.value) else pc + 1
            elif isinstance(term, CALL):
                # push the return-PC + caller's register window (stream + control snapshot); the
                # callee starts fresh (a single empty state). The graph is shared, so callee facts
                # persist; the control snapshot is copied so the callee's counter edits are local.
                self.stack.append((pc + 1, stream, dict(self.ctrl)))
                stream = [State()]
                pc = labels[term.label]
            elif isinstance(term, RET):
                if not self.stack:
                    raise ProgramError("RET with an empty control stack (no matching CALL)")
                ret_pc, saved_stream, saved_ctrl = self.stack.pop()
                stream = saved_stream          # restore the caller's window (callee graph writes persist)
                self.ctrl = saved_ctrl
                pc = ret_pc
            elif isinstance(term, SUSPEND):
                # capture the whole control state as a resumable Continuation and hand it to the driver.
                # Resume at the NEXT block (the wait's fall-through); copy stack/ctrl so post-suspend
                # driver work cannot corrupt the captured snapshot.
                request = self.ctrl.get(term.request_reg) if term.request_reg is not None else None
                return Continuation(program, pc + 1, list(self.stack), dict(self.ctrl),
                                    stream, request)
            elif isinstance(term, HALT):
                break
            else:
                raise ProgramError(f"{type(term).__name__} is not a terminator")
        return stream


def _branch_targets(term: Term) -> list[str]:
    if isinstance(term, (BRANCH, BRANCH_IF, CALL)):
        return [term.label]
    return []
