"""
The bridge to the as-built engine: a DUMB `Rule` -> ISA-program lowering, a name-`Graph` ->
`AttrGraph` bridge, and a fixpoint driver — so the reference machine can be differential-tested
against `rewriter.run` (the swap-safety net the design names,
`docs/reference/isa_reference.md` "Next slice").

Scope of this slice (kept deliberately narrow, per "keep the compiler dumb"): the POSITIVE,
MONOTONE, non-graded fragment — a rule of plain-relation `Pat`s (`s p o`), no NAC, no graded
conditions, no drop/rewire, and an RHS whose endpoints are LHS-bound and whose predicate is a
plain-literal relation name. Anything outside raises `Unlowerable` (explicit, never a silent
mis-lowering). Graded lowering (FUZZY/GRADE) and NAC->materialized-positive lowering (the
decide line) are later slices.

THE BRIDGE (why it is faithful). In the label-less substrate a former node NAME is just the
valued attribute `name="…"` (`decision_labelless_substrate`: "the old node-name 'Paul' IS the
valued attribute name='Paul', so name-based seeding ports over unchanged"). So a name-`Graph`
maps 1:1: every node -> an `AttrGraph` node carrying `name`, every bare edge copied. A relation
`subject -> [rel] -> object` stays a bare 2-hop path whose middle node carries the relation
name — matched by FOLLOW across the bare edges, exactly as `_match` walks it. (This is the
name-preserving bridge, NOT the neo-Davidsonian role reification; role-nodes are an authoring
convention on top, orthogonal to differential-testing the matcher.)

A `Pat(s, p, o)` lowers around its rel node as the pivot: bind the rel node (SEED it by name if
the predicate is a literal; else reach it by FOLLOW from an already-bound / literal-anchored
endpoint), then reach the subject as the rel's predecessor and the object as its successor —
binding a fresh variable, or SAME-checking an already-bound one, or TEST-ing a literal.
"""
from __future__ import annotations

from .production_rule import Pat, Rule, binder, is_var, is_bound_literal, literal_name
from .attrgraph import AttrGraph, valued, graded as graded_attr, _is_inert, NAME, PATTERN_MARK, INERT_MARK
from .vocabulary import MENTION
from .machine import (
    Instr, Machine, SEED, FOLLOW, TEST, SAME, DUP, GRADE, VMATCH, DISTINCT, MINT, EMIT, DROP_CTRL,
    SWEEP, State,
    ControlMachine, Block, PRIM, SETI, DEC, FALL, BRANCH_IF, HALT,
)


class Unlowerable(Exception):
    """The rule is outside this slice's positive/monotone/non-graded fragment."""


# ---------------------------------------------------------------------------
# Control-layer classification (vision §5/§6) — content-blind, drop-independent
# ---------------------------------------------------------------------------

def _is_control_token(tok: str) -> bool:
    """A control-token literal is a `<…>`-named node — the RESERVED control syntax the substrate
    already recognizes (forms.py excludes `<…>` from surface words; the linter requires a control
    rule to be gated by one, vision §5/§12.3). Content-blind: it reads the bracket convention,
    NEVER a domain predicate name (a bank could rename every predicate and this would not change)."""
    nm = literal_name(tok)
    return nm.startswith("<") and nm.endswith(">")


def _rule_touches_control(rule: Rule) -> bool:
    """True iff the rule references a control token anywhere in its match (LHS/NAC) or head — so
    the relations it MINTs are CONTROL-layer, not facts (vision §5: a control rule is gated by a
    control token and produces control-layer output). This is the producer-side, content-blind
    criterion that lets `DROP_CTRL` delete the planner's derived scaffolding (`viable`, `candidate`,
    `before` …) while still REFUSING a genuine fact — control-ness is established INDEPENDENTLY of
    any `drop` rule (a fact minted by a control-free rule stays a fact, so its deletion is refused).
    Static per-rule; covers both the `<…>`-endpoint heads and the bracket-less relations whose
    body reads a control token."""
    pats = list(rule.lhs) + list(rule.nac) + list(rule.rhs)
    return any(_is_control_token(t) for p in pats for t in p.tokens())


# ---------------------------------------------------------------------------
# The substrate bridge: name-Graph -> label-less AttrGraph
# ---------------------------------------------------------------------------

def to_attrgraph(graph: AttrGraph) -> tuple[AttrGraph, dict[str, str]]:
    """Bridge a `Graph`/`AttrGraph` into a FRESH `AttrGraph` under new identities: each non-inert node
    -> a node carrying its VALUED `name` (entities) and its GRADED keys — a relation's PREDICATE plus
    any embedding dims (both surfaced by `get_embedding`) — with each bare edge copied. Provenance/
    withdrawal nodes (inert) are skipped — they are not domain facts. Returns (attrgraph, old->new).

    Phase 2.3: a relation's predicate rides its graded key, NOT a VALUED `name`, so the retired
    `TEMPORARY BRIDGE`'s name-write + predicate-key post-pass are both gone (`name_demotion_design.md`).
    A rel node's graded predicate key comes across in the `get_embedding` copy exactly like an
    `add_relation` mint, so ISA reads (`nodes_with_key`/`has_key`/`predicate`) see it identically."""
    ag = AttrGraph()
    idmap: dict[str, str] = {}
    for old in graph.nodes():
        if graph.is_inert(old):                            # Phase 2.2 inert FLAG (was name-string based)
            continue
        attrs: dict = {}
        nm = graph.name(old)
        if nm:
            attrs["name"] = valued(nm)
        for dim, v in graph.get_embedding(old).items():    # predicate key (rels) + embedding dims (entities)
            attrs[dim] = graded_attr(v)
        idmap[old] = ag.add_node(attrs)
    for a, b in graph.edges():
        if a in idmap and b in idmap:
            ag.add_edge(idmap[a], idmap[b])
    return ag, idmap


# ---------------------------------------------------------------------------
# Rule -> program lowering
# ---------------------------------------------------------------------------

def _reject_unsupported(rule: Rule) -> None:
    if any(c.inverted for c in rule.graded):
        raise Unlowerable(f"{rule.key}: inverted graded condition ('not at all') is a later slice")
    if rule.nac:
        raise Unlowerable(f"{rule.key}: NAC (materialized-positive lowering is a later slice)")
    if rule.drop:
        raise Unlowerable(f"{rule.key}: drop (control layer) is out of this slice")


def _reach_endpoint(
    prog: list[Instr], bound: set[str], rel_reg: str, tok: str, direction: str, tmp: str,
) -> None:
    """Reach a Pat endpoint from its rel node: the subject is the rel's predecessor
    (direction='in'), the object its successor (direction='out'). Bind a fresh variable, or
    SAME-check an already-bound one, or TEST a literal."""
    key = binder(tok)
    if key is None:                                   # plain literal: reach a temp, TEST name
        prog.append(FOLLOW(tmp, rel_reg, direction))
        prog.append(TEST(tmp, "name", cmp="=", value=literal_name(tok)))
    elif key in bound:                                # already bound: reach a temp, unify
        prog.append(FOLLOW(tmp, rel_reg, direction))
        prog.append(SAME(tmp, key))
    else:                                             # fresh: bind it
        prog.append(FOLLOW(key, rel_reg, direction))
        bound.add(key)
        if is_bound_literal(tok):
            prog.append(TEST(key, "name", cmp="=", value=literal_name(tok)))


def lower_conj(pats: list[Pat], prebound: set[str] = frozenset(),
               tag: str = "", rel_out: list[str] | None = None) -> list[Instr]:
    """Lower a positive Pat conjunction to a match program, treating `prebound` binder keys as
    ALREADY bound (in the register file). `prebound` empty gives a self-contained LHS match; a
    non-empty `prebound` (the rule's LHS binding keys) lowers a NAC group SEEDED with the firing's
    bindings — its already-bound endpoints become FOLLOW-to-temp + SAME checks, its NAC-local free
    vars bind fresh. Each Pat is seeded from a ground anchor (a literal, or a var an earlier Pat —
    or the prebinding — already bound). `tag` disambiguates temp-register names across sub-programs.

    `rel_out` (if given) collects, per Pat and in order, the register that holds its matched RELATION
    node — the premises a provenance-minting driver `uses` (run_bank, `rewriter.match_with_premises`)."""
    prog: list[Instr] = []
    bound: set[str] = set(prebound)
    for i, pat in enumerate(pats):
        p_key = binder(pat.p)
        if p_key is not None and p_key in bound:      # predicate var already bound to a rel node
            rel_reg = p_key
        elif not is_var(pat.p):                        # literal predicate
            rel_reg = f"_rel{tag}{i}"
            s_key, o_key = binder(pat.s), binder(pat.o)
            # DRIVE FROM THE BOUND ENDPOINT (df-optimal join order). If an endpoint var is already
            # bound, the rel node is that node's neighbour carrying predicate KEY `p` — reach it by
            # FOLLOWing from the bound (specific, rarest) node + a predicate-key TEST, NOT by
            # SEEDing the whole predicate class and SAME-filtering. The set is identical
            # ({rel : edge(s,rel) ∧ has_key(rel,p)}), but the candidate set starts at a handful of
            # neighbours instead of every `p`-keyed node — this kills the `next`-chain cross-product
            # blowup (a literal `next` pattern whose subject an earlier pattern already bound was
            # seeding all ~200 `next` nodes).
            # Phase 2.1/2.3 (decision_attrgraph_rehost, "predicates become graded keys"): predicate
            # identity is a KEY-PRESENCE test/seed (`nodes_with_key`), not a `name` equality —
            # `add_relation` mints the graded key `p: 1.0` as the SOLE predicate representation on a rel
            # node (the legacy `name` dual-write is retired; see attrgraph.add_relation / name_demotion_design).
            if s_key is not None and s_key in bound:
                prog.append(FOLLOW(rel_reg, s_key, "out"))
                prog.append(TEST(rel_reg, literal_name(pat.p)))
            elif o_key is not None and o_key in bound:
                prog.append(FOLLOW(rel_reg, o_key, "in"))
                prog.append(TEST(rel_reg, literal_name(pat.p)))
            else:                                      # no bound endpoint: SEED the rel by predicate key
                prog.append(SEED(rel_reg, literal_name(pat.p), cmp=None))
            if p_key is not None:                      # bound-literal predicate binds too
                prog.append(DUP(p_key, rel_reg)); bound.add(p_key)
        else:                                          # free-var predicate: reach rel via a ground s/o
            rel_reg = f"_rel{tag}{i}"
            s_key, o_key = binder(pat.s), binder(pat.o)
            if s_key is not None and s_key in bound:
                prog.append(FOLLOW(rel_reg, s_key, "out"))
            elif o_key is not None and o_key in bound:
                prog.append(FOLLOW(rel_reg, o_key, "in"))
            elif not is_var(pat.s):
                anc = f"_anc{tag}{i}"
                prog.append(SEED(anc, "name", cmp="=", value=literal_name(pat.s)))
                prog.append(FOLLOW(rel_reg, anc, "out"))
            elif not is_var(pat.o):
                anc = f"_anc{tag}{i}"
                prog.append(SEED(anc, "name", cmp="=", value=literal_name(pat.o)))
                prog.append(FOLLOW(rel_reg, anc, "in"))
            else:
                raise Unlowerable(f"pattern {pat.tokens()} has no ground anchor")
            prog.append(DUP(p_key, rel_reg)); bound.add(p_key)
        _reach_endpoint(prog, bound, rel_reg, pat.s, "in", f"_ts{tag}{i}")
        _reach_endpoint(prog, bound, rel_reg, pat.o, "out", f"_to{tag}{i}")
        if rel_out is not None:
            rel_out.append(rel_reg)
    return prog


def lower_lhs(rule: Rule, rel_out: list[str] | None = None) -> list[Instr]:
    """Lower the rule's LHS conjunction to a self-contained positive match program. `rel_out`
    collects the premise rel-node registers (provenance; see `lower_conj`)."""
    return lower_conj(rule.lhs, rel_out=rel_out)


def lower_graded(rule: Rule) -> list[Instr]:
    """Lower each (non-inverted) graded condition to `GRADE` α-cut ops. A condition on `?c`
    with dims {d…} threshold t becomes one `GRADE(?c, d, threshold=t)` per dim: under the min
    t-norm each dim must clear t (so min ≥ t) and the score becomes the min over dims — exactly
    `rewriter.graded_degree` (min over dims, α-cut, min across conditions). These are MATCH ops
    (a filter), appended after the structural LHS match."""
    ops: list[Instr] = []
    for c in rule.graded:
        for dim in c.embedding:
            ops.append(GRADE(c.var, dim, threshold=c.threshold))
    return ops


def lower_value_matches(rule: Rule) -> list[Instr]:
    """Lower each declared value-match to a `VMATCH` filter (the forward-engine counterpart of the
    demand chain's `_value_matches_ok`, coreference-as-rules Stage 4). Both vars must be LHS-bound —
    VMATCH filters two ALREADY-bound registers — so an unbound value-match var is `Unlowerable` (loud,
    never a silent KeyError at run time). Exact -> equality on the VALUED dim; graded -> closeness on
    the GRADED dim. A MATCH op (filter), appended after the structural LHS match, like `lower_graded`."""
    bound = {t for pat in rule.lhs for t in pat.tokens() if is_var(t)}
    ops: list[Instr] = []
    for vm in rule.value_matches:
        for v in (vm.var_a, vm.var_b):
            if v not in bound:
                raise Unlowerable(f"{rule.key}: value-match var {v!r} is not LHS-bound")
        ops.append(VMATCH(vm.var_a, vm.var_b, vm.dim, threshold=vm.threshold))
    return ops


def lower_distinct(rule: Rule) -> list[Instr]:
    """Lower each declared distinctness condition to a `DISTINCT` filter (feedback #11 — the forward
    counterpart of the demand chain's `_distincts_pass`). Both vars must be LHS-bound — DISTINCT
    filters two ALREADY-bound registers — so an unbound var is `Unlowerable` (loud, never a silent
    KeyError at run time). A filter op, appended after the structural LHS match, like
    `lower_value_matches`."""
    bound = {t for pat in rule.lhs for t in pat.tokens() if is_var(t)}
    ops: list[Instr] = []
    for dc in rule.distinct:
        for v in (dc.var_a, dc.var_b):
            if v not in bound:
                raise Unlowerable(f"{rule.key}: distinctness var {v!r} is not LHS-bound")
        ops.append(DISTINCT(dc.var_a, dc.var_b))
    return ops


def lower_rhs(rule: Rule, control_preds: frozenset[str] = frozenset(),
              head_out: list[str] | None = None) -> list[Instr]:
    """Lower the RHS conjunction to MINT effects. Each Pat mints a rel node carrying the
    relation NAME with a bare in-edge from the subject and out-edge to the object — the
    reified `subject -> [rel] -> object` (additive; the monotone fact write).

    A RHS endpoint that is NOT LHS-bound is a VALUE INVENTION, reproducing `rewriter.apply_rule`'s
    per-firing `fresh` dict: a skolem `<cond>?`/`<rule>?`/`<succ>?` (bound-literal binder) mints ONE fresh
    node per firing, SHARED across the RHS clauses that reference it (so a rule fragment's `<rule>` is a
    single node) — a skolem FUNCTION of the firing's LHS match. This is the SUPPORTED minting path: forward
    it mints one-per-firing here; on the demand chain `chain._resolve_skolems` re-finds the same node by its
    defining relation so a re-served demand converges (feedback #2). A bare RHS-only VARIABLE (`?x` in the
    head, absent from the body) would instead be a node from nowhere — unsound (forward mints a fresh
    unnamed node the name surfaces can't see; the demand chain self-fulfils a ground goal) — so the loaders
    REJECT it at authoring (`authoring.reject_rhs_only_head_vars`). A PLAIN LITERAL
    (`yes`, `have_valuable`, `<yes>`) instead CANONICALIZES to its graph-wide node (`MINT(intern=)`),
    reproducing `rewriter.resolve_so`'s `nodes_named(nm)[0]`: cross-firing sharing is REQUIRED for
    reasoning (not just recognition), because a downstream rule joins two head-derived literals by
    NODE identity — a fresh node per firing splits the join (`<need> for ?c` and `?o add ?c` sharing
    `have_valuable`) and the derivation silently stalls. For pure RECOGNITION the fact-set is compared
    as a SET of triples so duplicate literal nodes collapsed harmlessly, which is why this only
    surfaced when the planner's REASONING banks moved onto run_bank (implementation_plan Phase 0.3)."""
    bound = rule.bound_names()
    ctrl = _rule_touches_control(rule)   # a control-gated rule mints CONTROL-layer relations (§5)
    prog: list[Instr] = []
    reg_of: dict[str, str] = {}          # value-invention identity -> register minted for it

    def resolve(tok: str) -> str:
        key = binder(tok)
        if key is not None and key in bound:             # LHS-bound: the match phase bound it
            return key
        # a fresh binder (skolem / RHS-only var) or a plain literal -> mint once per firing, share
        ident = key if key is not None else "=" + literal_name(tok)
        reg = reg_of.get(ident)
        if reg is None:
            name = literal_name(tok) if (key is None or is_bound_literal(tok)) else ""
            reg = f"_h{len(reg_of)}"
            # A PLAIN LITERAL (`key is None`) canonicalizes to its graph-wide node (`intern`),
            # exactly `rewriter.resolve_so` — so a downstream rule joins two head-derived literals
            # by NODE identity (a fresh node per firing splits the join, e.g. `<need> for ?c` and
            # `?o add ?c` sharing `have_valuable`). A skolem / RHS-only var stays a fresh MINT
            # (value invention, per firing).
            # BORN-CONTROL (2026-07-16): a `<…>`-token name gets the string-form `add_node`
            # treatment — the token dual-write + the CONTROL flag — so a rule-minted `<call>?` /
            # `<goal>?` SKOLEM is scaffolding from birth (its relations already were, via
            # `_rule_touches_control`), and the gated `SWEEP` can consume it (never a fact).
            tok_name = name.startswith("<") and name.endswith(">")
            attrs = {"name": valued(name), **({name: graded_attr(1.0)} if tok_name else {})}
            prog.append(MINT(reg, attrs=attrs, control=tok_name, intern=(key is None)))
            reg_of[ident] = reg
        return reg

    for k, pat in enumerate(rule.rhs):
        if binder(pat.p) is not None:
            raise Unlowerable(f"{rule.key}: RHS non-plain predicate {pat.tokens()} is a later slice")
        s_reg, o_reg = resolve(pat.s), resolve(pat.o)
        # PER-ATOM control-ness: a control-gated rule (`ctrl`) mints control, AND — independently —
        # a head whose PREDICATE is a scaffolding predicate (`control_preds`, e.g. surface
        # `next`/`first`) is control REGARDLESS of the rule, so a recognition form can read the
        # scaffolding chain and mint CONTENT facts (fact) while its `next`/`first` BRIDGE stays
        # control (a later strip's `DROP_CTRL` then permits deleting it).
        head_ctrl = ctrl or literal_name(pat.p) in control_preds
        pred = literal_name(pat.p)
        # Phase 2.1/2.3: the head rel node's predicate is the SOLE graded key `pred: 1.0` (canonical).
        # The TEMPORARY BRIDGE's VALUED `name` dual-write is retired (`name_demotion_design.md`):
        # MINT.dedup now matches on the predicate KEY (`_pred_key`/`has_key`), not `attrs[NAME]`, so a
        # predicate literally named `name` is sound as `{name: 1.0}` (no reserved-key collision).
        head_attrs = {pred: graded_attr(1.0)}
        prog.append(MINT(f"_head{k}", attrs=head_attrs,
                         in_edges=[s_reg], edges=[o_reg], control=head_ctrl, dedup=True))
        if head_out is not None:
            head_out.append(f"_head{k}")
    return prog


def _propagate_ops(rule: Rule) -> list[dict]:
    p = rule.propagate
    if p is None:
        return []
    return p if isinstance(p, list) else [p]


def lower_propagate(rule: Rule) -> list[Instr]:
    """Lower `rule.propagate` embedding-writes to EMIT effects (vision §13; the ISA face of
    `rewriter._propagate_ops`). Supports the `set` op — set the target var's embedding at a
    dimension to a value, the graded rule's `?x.embedding[name(?adj)] = value`. The DIMENSION may be
    a bound var (dynamic key = its bound node's NAME, via `EMIT(key_reg=)`) or a plain literal
    (static key); the write is a graded SET (`raise_degree=False`), matching `set_embedding`'s
    overwrite (NOT the monotone max-raise a derived degree uses). Both the target and a variable
    dimension must be LHS-bound (the graded rule binds `?x`/`?adj`); anything else is out of slice."""
    bound = rule.bound_names()
    prog: list[Instr] = []
    for op in _propagate_ops(rule):
        if op.get("op") != "set":
            raise Unlowerable(f"{rule.key}: propagate op {op.get('op')!r} (only 'set' lowers)")
        var_key = binder(op["var"])
        if var_key is None or var_key not in bound:
            raise Unlowerable(f"{rule.key}: propagate target {op['var']!r} is not LHS-bound")
        dim, val = op["dim"], float(op["value"])
        dim_key = binder(dim)
        if dim_key is not None and dim_key in bound:                 # dynamic key = name(bound dim)
            prog.append(EMIT(reg=var_key, key="", value=val,
                             key_reg=dim_key, raise_degree=False))
        elif dim_key is None:                                        # a literal dimension
            prog.append(EMIT(reg=var_key, key=literal_name(dim), value=val,
                             raise_degree=False))
        else:
            raise Unlowerable(f"{rule.key}: propagate dim {dim!r} is an unbound var")
    return prog


def _drop_endpoint_reg(prog: list[Instr], rel_reg: str, tok: str, direction: str,
                       tmp: str, bound: set[str]) -> str:
    """Return the register holding a drop endpoint's NODE (for DROP_CTRL). A bound var/literal is
    already in the register file (its key); a plain literal is reached from the rel node + a name
    TEST — the drop targets the SPECIFIC relation instance the bound endpoint anchors."""
    key = binder(tok)
    if key is not None and key in bound:
        return key
    prog.append(FOLLOW(tmp, rel_reg, direction))
    prog.append(TEST(tmp, "name", cmp="=", value=literal_name(tok)))
    return tmp


def lower_drop(rule: Rule) -> tuple[list[Instr], list[Instr]]:
    """Lower a control rule's `drop` patterns to (extra match ops, DROP_CTRL effect ops).

    A `drop s p o` deletes a reified relation `s -> [rel] -> o` (a control-layer deletion, vision
    §5). Seeded from the firing's LHS bindings (`_drops_only_bound` guarantees every drop token is
    bound or a plain literal), it reaches the rel node from a bound endpoint (df-optimal, the same
    join order as matching), then DROP_CTRLs BOTH bare edges (subject->rel, rel->object). DROP_CTRL
    refuses a fact edge, so this deletes ONLY when the rel node is control-stamped (`_rule_touches_
    control` at MINT) — the §5 fact-immutability invariant, enforced structurally by the opcode.
    The now-orphaned rel node is gc'd by `run_bank` (disconnected control node)."""
    bound = set(rule.bound_names())
    match_ops: list[Instr] = []
    effect_ops: list[Instr] = []
    for i, pat in enumerate(rule.drop):
        rel_reg = f"_drel{i}"
        s_key, o_key = binder(pat.s), binder(pat.o)
        # Phase 2.1: predicate identity is a key-presence test/seed (see lower_conj).
        if s_key is not None and s_key in bound:          # reach rel from the bound subject
            match_ops.append(FOLLOW(rel_reg, s_key, "out"))
            match_ops.append(TEST(rel_reg, literal_name(pat.p)))
        elif o_key is not None and o_key in bound:        # else from the bound object
            match_ops.append(FOLLOW(rel_reg, o_key, "in"))
            match_ops.append(TEST(rel_reg, literal_name(pat.p)))
        else:                                             # no bound endpoint: seed the rel by predicate key
            match_ops.append(SEED(rel_reg, literal_name(pat.p), cmp=None))
        s_reg = _drop_endpoint_reg(match_ops, rel_reg, pat.s, "in", f"_dts{i}", bound)
        o_reg = _drop_endpoint_reg(match_ops, rel_reg, pat.o, "out", f"_dto{i}", bound)
        effect_ops.append(DROP_CTRL(s_reg, rel_reg))
        effect_ops.append(DROP_CTRL(rel_reg, o_reg))
    return match_ops, effect_ops


# `lower_rewire` — DELETED 2026-07-16 with the INTERPOSE/RESTORE opcodes and `Rule.rewire` (the
# pre-Axis-A retraction interposition; unused since copy-on-delete/`RETIRE`, kept only for its tests).


def rule_touches_provenance(rule: Rule) -> bool:
    """True iff the rule's LHS/NAC names a provenance LITERAL (`proves`/`uses`/`<j:…>`/`<axiom>`/
    `<retracted>`) — the meta/TMS rules whose match must SEE inert nodes (`rewriter._pats_touch_prov`).
    Such a rule is lowered WITHOUT the inert guard (`guard_inert`) so `?j` can bind a `<j:…>` and
    `?j proves ?f` matches (a plain reasoning rule never names provenance, so it stays inert-blind).
    This convention read (`_is_inert` on the rule's own token names) is AUTHORING-layer work — the
    compiler deciding which guard to emit — which §3 of the firmware doc explicitly permits; the
    substrate and machine stay convention-free."""
    pats = list(rule.lhs) + list(rule.nac)
    return any(not is_var(t) and _is_inert(literal_name(t))
               for pat in pats for t in pat.tokens())


def guard_inert(prog: list[Instr]) -> list[Instr]:
    """The COMPILER-EMITTED fact-read guard for the FORWARD path (firmware §3): after every op that
    BINDS a register from the graph (`SEED`/`FOLLOW`/`JOIN` — exactly the binds the retired
    `Machine.skip_inert` mode used to filter), test that the bound node is NOT provenance-inert
    (`TEST(..., absent=True)` on the `<inert>` marker attribute). Uniform and un-forgettable — the
    guard is part of the PROGRAM, never a privileged machine mode; a provenance-aware rule
    (`rule_touches_provenance`) is simply lowered without it and sees the `<j:…>` layer."""
    out: list[Instr] = []
    for op in prog:
        out.append(op)
        if isinstance(op, SEED):
            out.append(TEST(op.reg, INERT_MARK, absent=True))
        elif isinstance(op, FOLLOW):
            out.append(TEST(op.dst, INERT_MARK, absent=True))
    return out


def lower_rule(rule: Rule) -> list[Instr]:
    """The dumb `Rule` -> program lowering (LHS match ops, graded α-cut, value-JOIN, then RHS/propagate
    effects). Single-program form (no NAC — a NAC needs the driver's match-time filter, `run_bank`)."""
    _reject_unsupported(rule)
    return (lower_lhs(rule) + lower_graded(rule) + lower_value_matches(rule) + lower_distinct(rule)
            + lower_rhs(rule) + lower_propagate(rule))


# ---------------------------------------------------------------------------
# NAC as a forward, match-time DRIVER filter (the opcode set stays positive)
# ---------------------------------------------------------------------------

def _nac_groups(rule: Rule) -> list[list[Pat]]:
    """Partition `rule.nac` into INDEPENDENT groups connected by shared NAC-LOCAL free vars (binders
    the LHS does not bind): `not (A and B)` (one group, shared free var) vs `not A and not B` (two
    groups). Reproduces `rewriter._nac_groups`; the rule is blocked if ANY group has a witness."""
    prebound = rule.bound_names()

    def free(pat: Pat) -> set[str]:
        return {b for t in pat.tokens() if (b := binder(t)) is not None and b not in prebound}

    groups: list[tuple[set[str], list[Pat]]] = []
    for pat in rule.nac:
        fv = free(pat)
        cur_vars, cur_pats = set(fv), [pat]
        merged: list[tuple[set[str], list[Pat]]] = []
        for gv, gp in groups:
            if fv and gv & fv:
                cur_vars |= gv
                cur_pats = gp + cur_pats
            else:
                merged.append((gv, gp))
        merged.append((cur_vars, cur_pats))
        groups = merged
    return [pats for _, pats in groups]


def lower_nac_programs(rule: Rule) -> list[list[Instr]]:
    """One positive match SUB-PROGRAM per independent NAC group, seeded with the rule's LHS binder
    keys as prebound. `run_bank` runs each under a candidate firing's state; if any yields a witness
    the firing is BLOCKED — the match-time NAC filter, faithful to `rewriter.nac_blocks`. The opcode
    set stays PURELY POSITIVE: a NAC is a positive sub-program the DRIVER uses as a filter, never a
    CHECK-ABSENT opcode (decision-rule-isa). Reasoning negation stays NAC-as-completion in GoalSolver;
    this filter is only the FORWARD recognition/control path's stratified surface guards."""
    prebound = rule.bound_names()
    return [lower_conj(group, prebound, tag=f"n{gi}_")
            for gi, group in enumerate(_nac_groups(rule))]


def _survived_nacs(g: AttrGraph, rule: Rule, st: State) -> list[tuple]:
    """The absences a FORWARD firing leaned on — one `(pred, subj, obj, 0.0)` per genuine NAC atom,
    named under the firing's register file (a bound var -> its node's NAME; an unbound NAC-local
    free var -> None = wildcard; a literal -> itself). The forward record half of RECONSIDER
    (docs/design/reconsider_design.md §6): `run_bank`'s NAC filter reads absence at match time, so a
    firing that passed it leaned on exactly these tuples, crisp (Π = 0). A NAC atom identical to a
    head atom is the idempotency memo, not epistemic negation — excluded, as the demand path does.
    A non-plain (variable) NAC predicate cannot be keyed for re-checking — skipped."""
    heads = {p.tokens() for p in rule.rhs}

    def nm(tok: str) -> str | None:
        b = binder(tok)
        if b is None:
            return literal_name(tok)
        nid = st.regs.get(b)
        return g.name(nid) if nid is not None else None

    out = []
    for gi, group in enumerate(_nac_groups(rule)):       # tag the NAC group (feedback #16) so `why`
        for pat in group:                                # renders a conjunctive NAC's atoms jointly
            if pat.tokens() in heads or binder(pat.p) is not None:
                continue
            out.append((literal_name(pat.p), nm(pat.s), nm(pat.o), 0.0, gi))
    return out


def _lower_bank_rule(rule: Rule, control_preds: frozenset[str] = frozenset(),
                     *, guard: bool = False):
    """Structured lowering for the bank driver: (match_ops, effect_ops, nac_programs, keys). NAC is
    NOT folded into the main program (it is the driver's filter). `drop` lowers to DROP_CTRL (its
    match ops append to the LHS match, using its bindings; its DROP_CTRLs append to the effects);
    `propagate` lowers to EMIT embedding-writes (graded rules).
    `control_preds` marks heads whose predicate is a scaffolding predicate as control-layer.
    `guard=True` emits the inert fact-read guard into the match + NAC programs (`guard_inert` —
    the compiler-emitted replacement for the retired `Machine.skip_inert` mode).

    MEMOIZED per `Rule` instance (feedback #13, the compile-once lowered program): lowering is a pure
    function of (rule, control_preds, guard), and `Rule` objects are shared-immutable (the #9
    `load_machine_rules` memo returns the same instances; every engine path treats them as frozen), so
    a static bank's ISA programs are compiled ONCE instead of on every `run_bank` round-trip — this was
    ~45% of `ask_goal`'s fixed per-call floor (the question-form banks re-lowered per question). The
    cached tuple is read-only by contract (`run_bank` only iterates it; a caller must never mutate the
    op lists). The cache lives on the rule's own `__dict__` (not a module dict keyed on `id()`), so its
    lifetime is exactly the rule's and a `dataclasses.replace` copy starts fresh."""
    cache = rule.__dict__.setdefault("_lowered_bank", {})
    hit = cache.get((control_preds, guard))
    if hit is None:
        cache[(control_preds, guard)] = hit = _lower_bank_rule_uncached(
            rule, control_preds, guard=guard)
    return hit


def _lower_bank_rule_uncached(rule: Rule, control_preds: frozenset[str], *, guard: bool):
    if any(c.inverted for c in rule.graded):
        raise Unlowerable(f"{rule.key}: inverted graded condition is a later slice")
    prem_regs: list[str] = []             # LHS body rel nodes a firing `uses` (provenance)
    head_regs: list[str] = []             # RHS head rel nodes a firing `proves` (provenance)
    match_ops, effect_ops = Machine.split(
        lower_lhs(rule, rel_out=prem_regs) + lower_graded(rule) + lower_value_matches(rule)
        + lower_distinct(rule)
        + lower_rhs(rule, control_preds, head_out=head_regs) + lower_propagate(rule))
    drop_match, drop_effect = lower_drop(rule)
    all_match = match_ops + drop_match
    nac_progs = lower_nac_programs(rule)
    if guard:                                              # firmware §3: the guard is in the PROGRAM
        all_match = guard_inert(all_match)
        nac_progs = [guard_inert(np) for np in nac_progs]
    return (all_match, effect_ops + drop_effect,
            nac_progs, rule.bound_names(), prem_regs, head_regs)


def run_bank(ag: AttrGraph, rules: list[Rule], *, max_rounds: int = 200,
             tools: dict | None = None, control_preds: frozenset[str] = frozenset(),
             provenance: bool = False) -> int:
    """Forward-chain `rules` over `ag` (in place) to fixpoint — the ISA forward driver at BANK level
    (the recognition/control engine, the forward face of the re-host, replacing `rewriter.run`).
    Each round: match every rule on the current graph, suppress already-fired bindings (keyed over
    the rule's LHS binders — the `fired` set that terminates recursive rules), apply the match-time
    NAC filter, and fire the survivors' effects (mutating `ag`, so later rules this round see the new
    facts). Iterate until no rule produces a NEW firing. Naive — no semi-naive delta / df-seeding
    (correctness-first). Returns the number of firings applied.

    `tools` (a {name -> handler} registry, dispatch.py) services materialized `<call>` nodes at each
    rule-fixpoint (exactly `rewriter.run`'s tool loop): when the rules quiesce, run every pending call
    whose tool is registered, fold its output back, and re-run the rules — until BOTH quiesce. The
    driver stays dumb (vision §6/§8).

    `provenance` (default OFF, the control-layer/planner path — `plan()` runs provenance=OFF) mints an
    in-graph justification per firing exactly as `rewriter._apply` does: a firing that CREATES new fact
    relations gets a `<j:RULEKEY>` node with `proves`->each new fact and `uses`->each LHS premise it
    matched (provenance.py). J/proves/uses nodes are inert (their NAMEs), so a later round skips them
    in matching — hence provenance forces `skip_inert` ON from the start (the J's it mints accrue)."""
    # Skip provenance-inert nodes in matching (cf. rewriter._match) when the graph already carries
    # provenance OR this run will MINT it — a fresh recognition graph with provenance OFF pays nothing
    # (common path); a graph that reasoned (e.g. `normalize_surface`'s `<j:…>`/`uses`) or a provenance
    # run needs it (else a `uses`->fact edge is matched as a fact).
    has_prov = provenance or any(ag.node(nid).inert for nid in ag.nodes())
    machine = Machine()
    # A META/TMS rule that NAMES provenance (`?j proves ?f`, the retraction CASCADE) must SEE the
    # inert `<j:…>` nodes — lowered WITHOUT the inert guard; a plain reasoning rule gets the
    # compiler-emitted guard (`guard_inert`) whenever the graph carries (or this run will mint)
    # provenance. A fresh guard-free graph pays nothing — the same profile as the retired machine
    # mode, but the visibility now lives in the PROGRAM (firmware §3), never a privileged flag.
    prov_aware = [rule_touches_provenance(r) for r in rules]
    lowered = [(i, _lower_bank_rule(r, control_preds, guard=has_prov and not prov_aware[i]))
               for i, r in enumerate(rules)]
    # Fired-suppression keyed by (rule KEY, binding-sig) — NOT per rule-index — exactly `rewriter`'s
    # `set[(rule.key, frozenset(bindings))]`. So a rule that appears TWICE in the bank (form generators
    # legitimately overlap — default forms + per-KB regenerated defaults) SHARES one suppression set
    # and fires once, instead of once per copy (which double-minted a value-invention head, e.g. a
    # duplicate `<cond>` NAC in rule-source recognition — finding-session480-not-phase41).
    fired: set[tuple[str, frozenset]] = set()
    has_drops = any(r.drop for r in rules)   # a drop orphans its rel node -> gc it (vision §5)
    total = 0

    def one_round(g, stream, ctrl):
        """One fixpoint ROUND (a §10 PRIM interpreter step): collect-then-apply, returning a 'changed?'
        flag — 1 if a firing (or a serviced tool `<call>`) advanced the graph, else 0 (quiesced). The
        BRANCH_IF loops while it stays 1 (docs/attic/isa_control_machine.md §9.5)."""
        nonlocal total
        # COLLECT-THEN-APPLY (the engine's collect-pending-then-fire order): match + NAC-filter every
        # rule against the START-OF-ROUND graph, THEN apply. A rule never sees a half-updated graph, so
        # a guard tag (`a is_kw yes`) and the clause it gates (matchable only once its `body_subj` is
        # set) can never race within a round — the clause first becomes matchable the round AFTER the
        # tag is applied, so its NAC sees the tag. This is the stratified reading recognition relies on.
        pending: list[tuple[int, list, State]] = []
        for i, (match_ops, effect_ops, nac_progs, keys, prem_regs, head_regs) in lowered:
            for st in machine.match(g, match_ops):         # visibility rides IN the lowered program
                sig = (rules[i].key, frozenset((k, st.regs[k]) for k in keys if k in st.regs))
                if sig in fired:
                    continue
                if any(machine.match(g, np, init=[State(dict(st.regs))]) for np in nac_progs):
                    continue                              # a NAC group has a witness -> blocked
                fired.add(sig)
                pending.append((i, effect_ops, st))
        if not pending:
            if tools:                                 # rules quiesced: service <call>s, re-run
                from .dispatch import service_calls  # lazy (dispatch -> world_model import cycle)
                if service_calls(g, tools):
                    return stream, 1                  # tool progress -> another round (was `continue`)
            return stream, 0                          # quiesced -> exit (was `break`)
        for i, effect_ops, st in pending:
            emit_prov = provenance and not rules[i].meta   # META rules stay PROVENANCE-SILENT even
            before = set(g.nodes()) if emit_prov else None   # in a provenance=True run (the regress
            out = machine.apply(g, effect_ops, st)           # guard — a meta rule naming proves/uses
            total += 1                                       # would else re-match the <j:> it just
            if emit_prov:                              # minted), so reasoning + TMS/retraction rules
                from .provenance import record_firing, record_assumptions   # share ONE run.
                *_, prem_regs, head_regs = lowered[i][1]
                # made_facts = head rel nodes this firing NEWLY created (a deduped/existing rel is not
                # re-proven — `before` excludes it), the analog of rewriter's `if not _relation_exists`.
                made = [n for hr in head_regs
                        if (n := out.regs.get(hr)) is not None and n not in before]
                if made:                              # RECORD as an ISA program (the one minting path)
                    premises = [pn for pr in prem_regs
                                if (pn := st.regs.get(pr)) is not None and g.has(pn)]
                    j = record_firing(g, rules[i].key, made, premises)
                    if rules[i].nac:                  # the forward record half (reconsider §6): the
                        record_assumptions(           # firing leaned on its NACs' absences, crisp
                            g, j, _survived_nacs(g, rules[i], st))
        return stream, 1                              # a firing advanced the graph -> another round

    def final_gc(g, stream, ctrl):
        if has_drops:                             # remove control rel nodes a DROP_CTRL orphaned
            doomed = [nid for nid in g.nodes()    # (disconnected + control: never fact/rule structure)
                      if g.is_control(nid) and not g.succ(nid) and not g.pred(nid)]
            if doomed:                            # the deletion is the gated SWEEP opcode, not a poke
                machine.apply(g, [SWEEP(f"_n{i}") for i in range(len(doomed))],
                              State({f"_n{i}": n for i, n in enumerate(doomed)}))
        return stream, 0

    # THE FIXPOINT AS A BRANCH-BACK (docs/attic/isa_control_machine.md §9.5, brick #5). The Python
    # `for _ in range(max_rounds)` driver loop is now a CONTROL-MACHINE program: a round counter (the
    # `for` bound), a for-guard, a ROUND block whose PRIM runs one collect-then-apply round and reports
    # `changed?`, and a branch-back. run_bank no longer HOLDS the loop — it ASSEMBLES the program and
    # runs it (the Python driver is gone; control lives in the machine). Behaviour-identical to the loop
    # above (the recognition/planning banks that exercise run_bank are the differential oracle).
    program = [
        Block(control=[SETI("rounds", max_rounds)], term=FALL()),           # for _ in range(max_rounds):
        Block(label="HEAD", term=BRANCH_IF("rounds", "<=", 0, "DONE")),      #   the for-guard (budget)
        Block(prim=PRIM(one_round, out="changed"), control=[DEC("rounds")],  #   one round; then loop back
              term=BRANCH_IF("changed", ">", 0, "HEAD")),                    #   while it changed, else fall
        Block(label="DONE", prim=PRIM(final_gc), term=HALT()),               # drop-orphan GC, once at end
    ]
    ControlMachine().run(ag, program)
    return total


def match_pats(ag: AttrGraph, pats: list[Pat], *,
               skip_inert: bool | None = None) -> list[dict[str, str]]:
    """All variable / bound-literal bindings of the positive conjunction `pats` over `ag`
    (binding key -> node id) — the ISA face of `rewriter.match` (a PURE one-shot matcher, no rule
    firing). Used by the read-side query surface (`query.ask`).

    `skip_inert` defaults to True UNLESS `pats` names a provenance LITERAL (`proves`/`uses`/`<j:…>`/
    `<axiom>`/`<retracted>`) — a meta query that must SEE the inert nodes — reproducing rewriter's
    `match_inert = _pats_touch_prov(pats)`. Duplicate binding tuples are collapsed (the matcher may
    yield the same binding via different seed orders; a set-membership query never wants dups)."""
    if skip_inert is None:
        skip_inert = not any(not is_var(t) and _is_inert(literal_name(t))
                             for pat in pats for t in pat.tokens())
    prog = lower_conj(list(pats))
    if skip_inert:                                         # compiler-emitted guard (firmware §3),
        prog = guard_inert(prog)                           # never a machine mode
    keys = [k for pat in pats for t in pat.tokens() if (k := binder(t)) is not None]
    seen: set[frozenset] = set()
    out: list[dict[str, str]] = []
    for st in Machine().match(ag, prog):
        b = {k: st.regs[k] for k in keys if k in st.regs}
        fb = frozenset(b.items())
        if fb not in seen:
            seen.add(fb)
            out.append(b)
    return out


# ---------------------------------------------------------------------------
# Fact authoring: (subject, predicate, object) name triples -> an ISA MINT program
# ---------------------------------------------------------------------------

def assemble_facts(facts: list[tuple[str, str, str]]) -> list[Instr]:
    """Lower `(subject, predicate, object)` NAME triples to an ISA program of MINT effects — the
    vision-aligned way to BUILD a graph. In a machine, state is written by INSTRUCTIONS, not by Python
    functions that poke the substrate: authoring is assembling a program and running it through the one
    interpreter (exactly as `lower_rhs` lowers a rule's head).

    Each distinct endpoint NAME becomes `MINT(intern=True)`, so a re-mentioned entity CANONICALIZES to a
    single node — the get-or-create is the INSTRUCTION's semantic (`machine._apply` intern branch), so a
    built graph never silently SPLITS a repeated name across two nodes (feedback #8b) and no `intern_node`
    Python twin is needed. Each relation becomes a deduped reified rel node `subject -[predicate]-> object`
    (`MINT(dedup=True)`, exactly `lower_rhs`), so re-asserting a fact is idempotent. Endpoints thread
    through registers, so every fact assembles into ONE program applied in a single pass (`Machine.run` /
    `load_fact_triples`)."""
    prog: list[Instr] = []
    reg_of: dict[str, str] = {}

    def endpoint(name: str) -> str:
        reg = reg_of.get(name)
        if reg is None:
            reg = f"_e{len(reg_of)}"
            prog.append(MINT(reg, attrs={NAME: valued(name)}, intern=True))   # get-or-create = the instruction
            reg_of[name] = reg
        return reg

    for k, (s, p, o) in enumerate(facts):
        s_reg, o_reg = endpoint(s), endpoint(o)
        prog.append(MINT(f"_r{k}", attrs={p: graded_attr(1.0)},
                         in_edges=[s_reg], edges=[o_reg], dedup=True))       # reified, deduped fact
    return prog


def load_fact_triples(ag: AttrGraph, facts: list[tuple[str, str, str]]) -> None:
    """Build `ag` from `(subject, predicate, object)` NAME triples by RUNNING their MINT program through the
    interpreter (`assemble_facts` + `Machine.run`). The vision-aligned authoring surface: a repeated name
    interns to one node VIA THE ISA, so facts never split across duplicate nodes — no id cache, no Python
    interner (feedback #8b). Monotone and idempotent: re-loading the same facts is a no-op (dedup)."""
    Machine().run(ag, assemble_facts(facts))


# ---------------------------------------------------------------------------
# The fixpoint driver (the scheduler around the machine)
# ---------------------------------------------------------------------------

def run_to_fixpoint(
    ag: AttrGraph, program: list[Instr], keys: set[str], *, max_rounds: int = 200,
) -> int:
    """Apply `program` to `ag` (in place) until no NEW firing is possible, reusing the engine's
    fired-suppression: a firing is keyed by its binding over `keys` (the rule's binding-keys),
    and a key already fired is skipped — the analog of `rewriter`'s `fired` set, which is what
    makes a recursive (e.g. transitive) rule terminate. Returns the number of firings applied.

    Takes a LOWERED ISA PROGRAM, not a rule bank (feedback #17: the names invite the wrong call, and
    passing a bank fails on arity — "missing argument 'keys'" — which reads as a typo rather than as
    "you want the other function"). To run a bank of `Rule`s to fixpoint, call `run_bank(ag, rules)`,
    which lowers each rule and drives this per rule with its own binding-keys."""
    machine = Machine()
    match_ops, effect_ops = Machine.split(program)
    fired: set[frozenset] = set()
    total = 0
    for _ in range(max_rounds):
        states = machine.match(ag, match_ops)
        fresh: list[State] = []
        for st in states:
            sig = frozenset((k, st.regs[k]) for k in keys if k in st.regs)
            if sig in fired:
                continue
            fired.add(sig)
            fresh.append(st)
        if not fresh:
            break
        for st in fresh:
            machine.apply(ag, effect_ops, st)
            total += 1
    return total


# ---------------------------------------------------------------------------
# Triple extraction (for differential comparison)
# ---------------------------------------------------------------------------

def derived_triples(ag: AttrGraph) -> set[tuple[str, str, str]]:
    """Every relation in `ag` as a `(subject_name, rel_name, object_name)` triple: a rel node
    is a node with a domain PREDICATE (its graded key, Phase 2.3 — no longer the VALUED `name`
    bridge), at least one predecessor (subject) and one successor (object). Subject/object are read
    by their VALUED `name` (they are entities). Diff two snapshots (final - initial) to get DERIVED.

    Memoized on `ag.version` (a monotonic mutation counter): the goal solver takes this snapshot
    on every subgoal evaluation across many nested solvers, so an uncached full-graph scan per
    call dominated (profiling: ~38k scans for one small plan). The result is a pure function of
    the current graph, so a version-keyed cache is safe and shared across every solver over `ag`.
    Returns a frozenset so a cached snapshot cannot be mutated by a caller doing set arithmetic."""
    cached = getattr(ag, "_dt_cache", None)
    if cached is not None and cached[0] == ag.version:
        return cached[1]

    def nm(nid: str) -> str | None:
        n = ag.name(nid)                          # VALUED entity name only (Phase 2.3: a `name`-predicate
        return n if n else None                   # rel node reports "", so it is not read as an endpoint name)

    out: set[tuple[str, str, str]] = set()
    for r in ag.nodes():
        rn = ag.predicate(r)                   # Phase 2.3: the predicate is the domain graded key
        if not rn:
            continue
        preds, succs = ag.pred(r), ag.succ(r)
        if not preds or not succs:
            continue
        # ONE-GRAPH FOLD (firmware §7 step 4): PATTERN-SPACE stays out of the fact view. Reified-rule
        # wiring (pattern atoms, role rels, head-index entries) carries the ordinary `PATTERN_MARK`
        # attribute written at authoring time — selected HERE (a view), never by the matcher (which
        # already excludes rule wiring via its control marker). Control-plane derivations joining
        # control nodes (`<goal> reached <plan>`) carry no pattern mark and stay visible as before.
        if ag.has_key(r, PATTERN_MARK):
            continue
        for s in preds:
            for o in succs:
                sn, on = nm(s), nm(o)
                if sn is not None and on is not None and on != MENTION:
                    out.add((sn, rn, on))     # hide the universal `is_a <mention>` coref handle (Stage 4)
    frozen = frozenset(out)
    ag._dt_cache = (ag.version, frozen)
    return frozen
