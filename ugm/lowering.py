"""
The bridge to the as-built engine: a DUMB `Rule` -> ISA-program lowering, a name-`Graph` ->
`AttrGraph` bridge, and a fixpoint driver — so the reference machine can be differential-tested
against `rewriter.run` (the swap-safety net the design names,
`docs/graph low level machine/isa-reference.md` "Next slice").

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
from .attrgraph import AttrGraph, valued, graded as graded_attr, _is_inert
from .machine import (
    Instr, Machine, SEED, FOLLOW, TEST, SAME, DUP, GRADE, MINT, EMIT, DROP_CTRL,
    INTERPOSE, RESTORE, State,
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
    if rule.drop or rule.rewire:
        raise Unlowerable(f"{rule.key}: drop/rewire (control layer) is out of this slice")


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


def lower_rhs(rule: Rule, control_preds: frozenset[str] = frozenset(),
              head_out: list[str] | None = None) -> list[Instr]:
    """Lower the RHS conjunction to MINT effects. Each Pat mints a rel node carrying the
    relation NAME with a bare in-edge from the subject and out-edge to the object — the
    reified `subject -> [rel] -> object` (additive; the monotone fact write).

    A RHS endpoint that is NOT LHS-bound is a VALUE INVENTION, reproducing `rewriter.apply_rule`'s
    per-firing `fresh` dict: a skolem `<cond>?`/`<rule>?` (bound-literal binder) mints ONE fresh node per
    firing, SHARED across the RHS clauses that reference it (so a rule fragment's `<rule>` is a single
    node). This lowering STILL emits a bare RHS-only VARIABLE (`?x` in the head, absent from the body) as a
    fresh-per-firing `""` node — but that is NOT usable end-to-end (check-before-derive never suppresses a
    fresh object, so the rule re-fires and mints garbage; the demand chain collapses the var onto the query
    goal), so the loaders now REJECT such a rule at authoring (`authoring.reject_rhs_only_head_vars`,
    feedback #2). Genuine per-match minting would be wired HERE (or via an explicit MINT tool) if it lands.
    A PLAIN LITERAL
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
            prog.append(MINT(reg, attrs={"name": valued(name)}, intern=(key is None)))
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


def lower_rewire(rule: Rule) -> list[Instr]:
    """Lower a rule's `rewire` list to effect ops. The ONLY rewire in the system is the reversible
    INTERPOSITION the TMS uses to hide a retracted fact (`retraction.INTERPOSE_RULE`): the triple
      [("cut", rel, obj), ("link", rel, marker), ("link", marker, obj)]
    — cut the fact's object edge and splice a fresh `<retracted>` marker into the 2-hop path. That
    is EXACTLY the `INTERPOSE` opcode (isa-reference.md "Reserved: INTERPOSE / RESTORE"), so it lowers
    to one INTERPOSE (rel/obj are LHS-bound; marker is the fresh skolem literal). Any OTHER rewire
    shape (a bare cut/link — only test fixtures, never a bank) stays `Unlowerable`: raw-edge surgery
    outside the reversible interposition is not a sanctioned ISA fact op."""
    ops = rule.rewire
    bound = set(rule.bound_names())
    if (len(ops) == 3 and ops[0][0] == "cut" and ops[1][0] == "link" and ops[2][0] == "link"):
        (_, a, b), (_, a2, m), (_, m2, b2) = ops
        a_key, b_key = binder(a), binder(b)
        # the interposition shape: cut(A,B); link(A,M); link(M,B), A/B LHS-bound, M a fresh skolem
        if (a == a2 and b == b2 and m == m2 and a_key in bound and b_key in bound
                and binder(m) is not None and binder(m) not in bound and is_bound_literal(m)):
            return [INTERPOSE(rel=a_key, obj=b_key, marker_name=literal_name(m))]
    raise Unlowerable(f"{rule.key}: rewire {ops} is not the reversible interposition shape")


def rule_touches_provenance(rule: Rule) -> bool:
    """True iff the rule's LHS/NAC names a provenance LITERAL (`proves`/`uses`/`<j:…>`/`<axiom>`/
    `<retracted>`) — the meta/TMS rules whose match must SEE inert nodes (`rewriter._pats_touch_prov`).
    For such a rule `run_bank` matches with `skip_inert` OFF so `?j` can bind a `<j:…>` and
    `?j proves ?f` matches (a plain reasoning rule never names provenance, so it stays inert-blind)."""
    pats = list(rule.lhs) + list(rule.nac)
    return any(not is_var(t) and _is_inert(literal_name(t))
               for pat in pats for t in pat.tokens())


def lower_rule(rule: Rule) -> list[Instr]:
    """The dumb `Rule` -> program lowering (LHS match ops, graded α-cut, then RHS/propagate effects).
    Single-program form (no NAC — a NAC needs the driver's match-time filter, `run_bank`)."""
    _reject_unsupported(rule)
    return lower_lhs(rule) + lower_graded(rule) + lower_rhs(rule) + lower_propagate(rule)


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


def _lower_bank_rule(rule: Rule, control_preds: frozenset[str] = frozenset()):
    """Structured lowering for the bank driver: (match_ops, effect_ops, nac_programs, keys). NAC is
    NOT folded into the main program (it is the driver's filter). `drop` lowers to DROP_CTRL (its
    match ops append to the LHS match, using its bindings; its DROP_CTRLs append to the effects);
    `propagate` lowers to EMIT embedding-writes (graded rules); `rewire` lowers to INTERPOSE (the
    reversible retraction interposition — `lower_rewire`).
    `control_preds` marks heads whose predicate is a scaffolding predicate as control-layer."""
    if any(c.inverted for c in rule.graded):
        raise Unlowerable(f"{rule.key}: inverted graded condition is a later slice")
    prem_regs: list[str] = []             # LHS body rel nodes a firing `uses` (provenance)
    head_regs: list[str] = []             # RHS head rel nodes a firing `proves` (provenance)
    match_ops, effect_ops = Machine.split(
        lower_lhs(rule, rel_out=prem_regs) + lower_graded(rule)
        + lower_rhs(rule, control_preds, head_out=head_regs) + lower_propagate(rule))
    drop_match, drop_effect = lower_drop(rule)
    rewire_effect = lower_rewire(rule) if rule.rewire else []
    return (match_ops + drop_match, effect_ops + drop_effect + rewire_effect,
            lower_nac_programs(rule), rule.bound_names(), prem_regs, head_regs)


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
    machine = Machine(skip_inert=has_prov)
    # A META/TMS rule that NAMES provenance (`?j proves ?f`, the retraction CASCADE) must SEE the
    # inert `<j:…>` nodes — matched with `skip_inert` OFF (`rewriter`'s per-rule `match_inert`). A
    # plain reasoning rule never names provenance, so it keeps the fact-only view. Lazily built.
    prov_aware = [rule_touches_provenance(r) for r in rules]
    machine_prov = Machine(skip_inert=False) if any(prov_aware) else machine
    lowered = [(i, _lower_bank_rule(r, control_preds)) for i, r in enumerate(rules)]
    # Fired-suppression keyed by (rule KEY, binding-sig) — NOT per rule-index — exactly `rewriter`'s
    # `set[(rule.key, frozenset(bindings))]`. So a rule that appears TWICE in the bank (form generators
    # legitimately overlap — default forms + per-KB regenerated defaults) SHARES one suppression set
    # and fires once, instead of once per copy (which double-minted a value-invention head, e.g. a
    # duplicate `<cond>` NAC in rule-source recognition — finding-session480-not-phase41).
    fired: set[tuple[str, frozenset]] = set()
    has_drops = any(r.drop for r in rules)   # a drop orphans its rel node -> gc it (vision §5)
    total = 0
    for _ in range(max_rounds):
        # COLLECT-THEN-APPLY (the engine's collect-pending-then-fire order): match + NAC-filter every
        # rule against the START-OF-ROUND graph, THEN apply. A rule never sees a half-updated graph, so
        # a guard tag (`a is_kw yes`) and the clause it gates (matchable only once its `body_subj` is
        # set) can never race within a round — the clause first becomes matchable the round AFTER the
        # tag is applied, so its NAC sees the tag. This is the stratified reading recognition relies on.
        pending: list[tuple[int, list, State]] = []
        for i, (match_ops, effect_ops, nac_progs, keys, prem_regs, head_regs) in lowered:
            m = machine_prov if prov_aware[i] else machine   # meta rules match with inert visible
            for st in m.match(ag, match_ops):
                sig = (rules[i].key, frozenset((k, st.regs[k]) for k in keys if k in st.regs))
                if sig in fired:
                    continue
                if any(m.match(ag, np, init=[State(dict(st.regs))]) for np in nac_progs):
                    continue                              # a NAC group has a witness -> blocked
                fired.add(sig)
                pending.append((i, effect_ops, st))
        if not pending:
            if tools:                                 # rules quiesced: service <call>s, re-run
                from .dispatch import service_calls  # lazy (dispatch -> world_model import cycle)
                if service_calls(ag, tools):
                    continue
            break
        for i, effect_ops, st in pending:
            emit_prov = provenance and not rules[i].meta   # META rules stay PROVENANCE-SILENT even
            before = set(ag.nodes()) if emit_prov else None  # in a provenance=True run (the regress
            out = machine.apply(ag, effect_ops, st)          # guard — a meta rule naming proves/uses
            total += 1                                       # would else re-match the <j:> it just
            if emit_prov:                              # minted), so reasoning + TMS/retraction rules
                from .provenance import j_name, PROVES, USES   # can share ONE run (coref-as-rules).
                *_, prem_regs, head_regs = lowered[i][1]
                # made_facts = head rel nodes this firing NEWLY created (a deduped/existing rel is not
                # re-proven — `before` excludes it), the analog of rewriter's `if not _relation_exists`.
                made = [n for hr in head_regs
                        if (n := out.regs.get(hr)) is not None and n not in before]
                if made:
                    j = ag.add_node(j_name(rules[i].key), inert=True)  # Phase 2.2: inert flag
                    for c in made:
                        ag.add_relation(j, PROVES, c, inert=True)
                    for pr in prem_regs:              # uses each still-present LHS premise rel node
                        pn = st.regs.get(pr)
                        if pn is not None and ag.has(pn):
                            ag.add_relation(j, USES, pn, inert=True)
    if has_drops:                             # remove control rel nodes a DROP_CTRL orphaned
        for nid in ag.nodes():                # (disconnected + control: never fact/rule structure)
            if ag.is_control(nid) and not ag.succ(nid) and not ag.pred(nid):
                ag.remove_node(nid)
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
    keys = [k for pat in pats for t in pat.tokens() if (k := binder(t)) is not None]
    seen: set[frozenset] = set()
    out: list[dict[str, str]] = []
    for st in Machine(skip_inert=skip_inert).match(ag, prog):
        b = {k: st.regs[k] for k in keys if k in st.regs}
        fb = frozenset(b.items())
        if fb not in seen:
            seen.add(fb)
            out.append(b)
    return out


# ---------------------------------------------------------------------------
# The fixpoint driver (the scheduler around the machine)
# ---------------------------------------------------------------------------

def run_to_fixpoint(
    ag: AttrGraph, program: list[Instr], keys: set[str], *, max_rounds: int = 200,
) -> int:
    """Apply `program` to `ag` (in place) until no NEW firing is possible, reusing the engine's
    fired-suppression: a firing is keyed by its binding over `keys` (the rule's binding-keys),
    and a key already fired is skipped — the analog of `rewriter`'s `fired` set, which is what
    makes a recursive (e.g. transitive) rule terminate. Returns the number of firings applied."""
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
        for s in preds:
            for o in succs:
                sn, on = nm(s), nm(o)
                if sn is not None and on is not None:
                    out.add((sn, rn, on))
    frozen = frozenset(out)
    ag._dt_cache = (ag.version, frozen)
    return frozen
