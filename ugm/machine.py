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

THE INVARIANT AS A PROPERTY OF THE OPCODE SET (rule-isa-design.md payoff #1).  The only
mutating opcodes are `EMIT`/`MINT` (monotone: add a node, raise a graded degree, assert a
value — never lower or delete) and `DROP_CTRL` (delete a bare edge, but it consults
`AttrGraph.edge_is_fact` and REFUSES a fact edge). There is NO opcode that deletes a fact
edge or lowers a degree — "an ungated fact deletion" is simply not expressible. There is also
NO `CHECK-ABSENT`/NAC opcode: the matching core is purely positive (negation is materialized
as a positive attribute and matched positively — the decide/de-pythonization line).
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
    if op == "~=":               # approximate: numeric tolerance, else equality
        try:
            return abs(float(a) - float(b)) <= 1e-9
        except (TypeError, ValueError):
            return a == b
    raise ValueError(f"unknown comparator {op!r} (expected =, <=, >=, ~=)")


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
    valued comparison). No score change."""
    reg: str
    key: str
    cmp: str | None = None
    value: object = None


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
        self._inert_cache: dict[str, bool] = {}

    # --- matching transitions (state -> zero-or-more states) ---------------

    def _inert(self, g: AttrGraph, nid: str) -> bool:
        # Called ONLY when `skip_inert` is on (guarded by `self.skip_inert and ...` at each call site,
        # so the OFF path pays nothing — not even this call). Phase 2.2: the node's dedicated
        # `inert` flag (set at every provenance mint site), not a name-string sniff — a node's
        # inertness is fixed for the run, so the verdict is still memoizable per nid.
        c = self._inert_cache.get(nid)
        if c is None:
            c = g.node(nid).inert
            self._inert_cache[nid] = c
        return c

    def _match_step(self, g: AttrGraph, ins: Instr, st: State) -> Iterator[State]:
        if isinstance(ins, SET):
            yield st.bind(ins.reg, ins.nid)
        elif isinstance(ins, DUP):
            yield st.bind(ins.dst, st.regs[ins.src])
        elif isinstance(ins, SAME):
            if st.regs[ins.a] == st.regs[ins.b]:
                yield st
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
            if g.has_key(nid, ins.key) and self._valued_ok(g, nid, ins.key, ins.cmp, ins.value):
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
            nid = st.regs[ins.reg]
            attr = g.get_attr(nid, ins.key)
            if attr is None:
                return
            if ins.threshold is not None:                # graded alpha-cut
                if attr.kind != GRADED:
                    return
                deg = float(attr.value)
                if deg >= ins.threshold and deg > 0.0:
                    yield st.scaled(deg, self.tnorm)
            elif ins.cmp is not None:                    # valued comparison
                if attr.kind == VALUED and _cmp(attr.value, ins.cmp, ins.value):
                    yield st
            else:
                raise ProgramError("GRADE needs either a graded threshold or a valued cmp")
        else:
            raise ProgramError(f"{type(ins).__name__} is an effect opcode in the match phase")

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
