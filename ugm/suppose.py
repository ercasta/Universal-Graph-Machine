"""
Phase 5.3 — SUPPOSE (firmware v2, `processing_modes.md` mode 6): "what if" — entertain before
believing. The hypothesis-formulation-and-verification mechanism, composed from the firmware modes
already built (CHAIN inside a scope, CHECK its predicted consequences).

The mechanics are the PENCIL/INK split (`vision.md` §5, `processing_modes.md` §3):

  - a `<hypothesis>` scope node is minted (control);
  - each ASSUMED fact is written in PENCIL — a CONTROL relation node tagged `scope=<hypothesis>` (via
    `apply.SCOPE`). Because it is control, it is invisible to ordinary fact matching and can never be
    read as ink; because it is tagged, the scope-aware fact readers (`apply._fact_relnodes(scope=…)`)
    make it visible WITHIN this scope;
  - CHAIN (`chain_sip(scope=…)`) reasons INSIDE the scope: it sees the pencil + the real ink, and
    writes its derivations back in PENCIL (scope-tagged control), so nothing unconfirmed touches ink;
  - each PREDICTED consequence is CHECKed in-scope. A contradiction (the supposition entails the
    NEGATION of a prediction, in-scope) REFUTES the hypothesis; every prediction holding CONFIRMS it;
  - on CONFIRM the assumptions are EMITted to INK (real facts) with optional provenance, then the
    pencil scaffolding is swept; on REFUTE (or an inconclusive within-budget result) the whole scope
    is DROP_CTRL-swept and ink is untouched.

The fact layer stays MONOTONE throughout — there is no retraction, because nothing unconfirmed ever
became a fact. This is the whole point of the pencil/ink split.

NOT possible-worlds: reasoning happens on the SAME graph, segregated by the scope tag — never on a
`graph.copy()` branch, which `processing_modes.md` mode 6 names as SUPPOSE's TRAP (backtrackable
fact-layer writes / truth-maintenance by deletion). The price of same-graph is scope-aware matching:
the deliberately-additive posture of CHECK/CHOOSE (new modules over `chain_sip`, touching nothing in
the hot path) could not hold here, so `apply._fact_relnodes` / `chain._facts_matching` / the EMIT path
gained a `scope=` parameter — gated to be behavior-NEUTRAL when no scope is active (protecting the
positive core, differentially proven).

v0 SCOPE:
  - the assumptions and predictions are `(pred, subj, obj)` name triples; assumption endpoints resolve
    to existing entity nodes (minted as real if absent — the entities the hypothesis is ABOUT), only
    the RELATION is assumed. A supposition that introduces a fresh pencil ENTITY is a later slice.
  - the negation convention is `check._neg_pred` (`is`->`is_not`, `R`->`R_not`); a contradiction fires
    only where the bank has negative-producing rules/facts.
  - CONFIRM commits the ASSUMPTIONS to ink (the consequences re-derive from ink by ordinary forward
    reasoning — committing them too would be redundant); provenance is minimal (`<j:confirmed>`).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .attrgraph import AttrGraph, VALUED, graded, valued, NAME
from .apply import SCOPE, _fact_exists
from .chain import chain_sip, _facts_matching, render_demands, resolve_write_node, ById
from .check import _neg_pred
from .machine import Machine, MINT, EMIT, SWEEP, State

_MACHINE = Machine()

HYPOTHESIS = "<hypothesis>"

# SCOPE KIND (scope_generalization.md §4). A scope is a KINDED relativizer: a fact holds RELATIVE TO
# the scope, and the KIND says how the read treats that relativity. The kind lives as a VALUED attr on
# the scope node — extending the `<likeliness>`-on-`<hypothesis>` pattern (a `kind` attr, not distinct
# marker names, so every scope stays a `<hypothesis>` and only the READ dispatches on kind). An ABSENT
# kind = `epistemic` (today's fork/suppose scopes, untouched — the generalization is additive).
SCOPE_KIND = "<scope-kind>"      # valued attr on the scope node; absent ⇒ epistemic
KIND_EPISTEMIC = "epistemic"     # a possibility (fork = discounted; suppose = a stance entertained)
KIND_HOLDER = "holder"           # attribution: the fact holds DEFINITELY for a holder, non-veridical globally
KIND_TEMPORAL = "temporal"       # tense: the fact holds DEFINITELY at an ordered index, non-veridical globally
HOLDER = "<holder>"              # valued attr on a holder scope: WHO holds it (keys the scope to a party)
INDEX = "<temporal-index>"       # valued attr on a temporal scope: WHICH ordered index it relativizes to


def scope_kind(g: AttrGraph, scope: str) -> str:
    """The KIND of `scope` — the value of its `<scope-kind>` attr, defaulting to `epistemic` (an
    unkinded fork/suppose scope). The single dispatch point for a kind-parameterized read."""
    a = g.get_attr(scope, SCOPE_KIND)
    return a.value if a is not None else KIND_EPISTEMIC


# The three SUPPOSE verdicts.
CONFIRMED = "confirmed"          # every prediction held in-scope, no contradiction -> committed to ink
REFUTED = "refuted"              # a contradiction: the supposition entails a prediction's negation -> dropped
INCONCLUSIVE = "inconclusive"    # no contradiction, but not every prediction was derivable in budget -> dropped

Triple = tuple[str, str, str]


@dataclass
class SupposeResult:
    """The verdict of a SUPPOSE run. `committed` is the ink written on CONFIRM (empty otherwise);
    `contradiction` is the predicted tuple whose negation was entailed (set only on REFUTE);
    `looked_for` is the rendered magic set the in-scope CHAIN explored (the 'what I reasoned about'
    trace). `derived` is the in-scope DERIVED consequences (the hypothesis's pencil derivations, seed
    assumptions excluded) — populated only on a READ-ONLY run (`commit=False`, feedback #6), so a
    hypothesis-driven analyzer can inspect what held under the supposition (incl. after INCONCLUSIVE)
    without the KB being mutated. The scope has already been resolved — committed to ink (CONFIRM) or
    swept (else) — so no live `<hypothesis>` id is returned."""
    status: str
    committed: list[Triple] = field(default_factory=list)
    contradiction: Triple | None = None
    looked_for: list[str] = field(default_factory=list)
    derived: list[Triple] = field(default_factory=list)


def _resolve(g: AttrGraph, name) -> str:
    """The node a hypothesis assumption is about. A `ById` endpoint (Phase 8 C, id-addressed suppose)
    pins to its node; a name reuses an existing same-named node or mints one — WARNING on an ambiguous
    name (the shared silent->loud [0]-pick discipline in `chain.resolve_write_node`)."""
    return resolve_write_node(g, name, where="suppose assumption")


def _pencil(g: AttrGraph, scope: str, s_id: str, pred: str, o_id: str) -> str:
    """Write an assumed fact `s -[pred]-> o` in PENCIL, as an ISA program: a CONTROL rel node tagged
    `scope` — invisible to ordinary matching, visible only within its `<hypothesis>` scope."""
    st = _MACHINE.apply(g, [
        MINT("_rel", attrs={pred: graded(1.0)}, in_edges=["_s"], edges=["_o"], control=True),
        EMIT("_rel", SCOPE, scope, kind=VALUED),
    ], State({"_s": s_id, "_o": o_id}))
    return st.regs["_rel"]


def scope_members(g: AttrGraph, scope: str) -> list[str]:
    """Every pencil / scope-derived rel node tagged with `scope` — the scope's contents, read through
    the key index then value-filtered (the blessed 'candidates-by-key, filter-by-value' pattern; there
    is deliberately no value index)."""
    out: list[str] = []
    for n in g.nodes_with_key(SCOPE):
        a = g.get_attr(n, SCOPE)
        if a is not None and a.value == scope:
            out.append(n)
    return out


def _scope_derivations(g: AttrGraph, scope: str, seed_rels: set[str]) -> list[Triple]:
    """The in-scope DERIVED consequences as `(subj, pred, obj)` name-triples — every scope-tagged pencil
    fact that is NOT one of the seed assumption rels (feedback #6: inspect what the hypothesis ENTAILED,
    e.g. to see WHY a run was inconclusive). Read before the scope is swept; endpoints as their names."""
    out: list[Triple] = []
    for rel in scope_members(g, scope):
        if rel in seed_rels or not g.has(rel):
            continue
        p = g.predicate(rel)
        if not p:
            continue
        for s in g.pred(rel):
            for o in g.succ(rel):
                sn, on = g.name(s), g.name(o)
                if sn and on:
                    out.append((sn, p, on))
    return out


def _drop_scope(g: AttrGraph, scope: str) -> None:
    """DROP the whole scope, as a SWEEP program: remove every rel node tagged `scope` (the pencil
    assumptions + every in-scope pencil derivation) and the `<hypothesis>` node itself. All are
    CONTROL — and the opcode REFUSES anything else — so this cuts only control structure; the real
    entity endpoints and every ink fact are untouched (§5 monotone)."""
    doomed = [rel for rel in scope_members(g, scope) if g.has(rel)]
    if g.has(scope):
        doomed.append(scope)
    if doomed:
        _MACHINE.apply(g, [SWEEP(f"_n{i}") for i in range(len(doomed))],
                       State({f"_n{i}": n for i, n in enumerate(doomed)}))


def _record_confirmed(g: AttrGraph, ink_node: str) -> None:
    """Minimal provenance for a confirmed assumption entering ink: a `<j:confirmed>` justification
    (`proves -> the inked fact`), through the ONE justification-minting program (`record_firing`),
    in the inert substrate shape `surface.explain` replays."""
    from .provenance import record_firing
    record_firing(g, "confirmed", [ink_node], [])


def suppose(fact_g: AttrGraph,
            assumptions: list[Triple], predictions: list[Triple], *,
            rules: AttrGraph | None = None,
            provenance: bool = False, commit: bool = True,
            focus_scope: frozenset[str] | None = None) -> SupposeResult:
    """Entertain `assumptions` in a `<hypothesis>` scope, CHAIN their consequences in pencil, and CHECK
    the `predictions` in-scope. Returns a `SupposeResult`. Side effect on the graph: CONFIRM commits the
    assumptions to ink (monotone, with optional provenance) and sweeps the pencil; REFUTE / INCONCLUSIVE
    sweep the scope and leave ink untouched.

    Contradiction = the supposition entails the NEGATION of a prediction (in-scope). Confirmation = every
    prediction is derivable in-scope and none contradicted.

    `commit=False` (feedback #6) makes it READ-ONLY: nothing is ever inked — even a CONFIRMED run only
    reports the verdict and returns the in-scope DERIVED consequences (`result.derived`) for inspection,
    then sweeps the pencil, so the KB's committed facts are unchanged. This fits a hypothesis-driven
    analyzer ('does X hold under this assumption?') that would otherwise copy/rebuild the KB per query,
    and it lets you inspect WHY a run was INCONCLUSIVE (the partial derivations that used to be swept
    unseen). (A brand-new entity NAME in an assumption still mints its node — pass `ById` to stay fully
    pure.) Default `commit=True` is behaviour-identical to before (`derived` stays empty).

    `focus_scope` (feedback #7) BOUNDS attention exactly as `ask_goal` does — threaded into the in-scope
    `chain_sip`/`_facts_matching` so the hypothesis reasons only within the working set (an endpoint in
    `focus_scope`), keeping per-hypothesis cost tracking the focus, not the accreted graph. `None` =
    whole-graph (behaviour-identical). Orthogonal to the pencil `scope` (which segregates the hypothesis)."""
    from .chain import validate_ids
    rule_g = rules if rules is not None else fact_g        # one-graph default (the fold)
    for s, _p, o in (*assumptions, *predictions):          # id-addressed pins must exist (silent->loud)
        validate_ids(fact_g, s, o)
    scope = _MACHINE.apply(fact_g, [MINT("_h", attrs={NAME: valued(HYPOTHESIS),
                                                      HYPOTHESIS: graded(1.0)}, control=True)],
                           State({})).regs["_h"]
    seed_rels: set[str] = set()
    for s, p, o in assumptions:
        seed_rels.add(_pencil(fact_g, scope, _resolve(fact_g, s), p, _resolve(fact_g, o)))

    contradiction: Triple | None = None
    all_hold = True
    for pred, subj, obj in predictions:
        # CHAIN the prediction and its negation inside the scope (pencil reasoning; provenance is
        # ephemeral here, so it is never journaled — only the confirmed ink commit records provenance).
        chain_sip(fact_g, (pred, subj, obj), rules=rule_g, scope=scope, focus_scope=focus_scope)
        neg_pred = _neg_pred(pred)
        chain_sip(fact_g, (neg_pred, subj, obj), rules=rule_g, scope=scope, focus_scope=focus_scope)
        if _facts_matching(fact_g, neg_pred, subj, obj, scope=scope, focus_scope=focus_scope):
            contradiction = (pred, subj, obj)          # entails the opposite of the prediction -> refute
            break
        if not _facts_matching(fact_g, pred, subj, obj, scope=scope, focus_scope=focus_scope):
            all_hold = False

    looked_for = render_demands(rule_g)
    # READ-ONLY (commit=False): snapshot the in-scope derivations BEFORE the sweep, for inspection.
    derived = _scope_derivations(fact_g, scope, seed_rels) if not commit else []

    if contradiction is not None:
        _drop_scope(fact_g, scope)
        return SupposeResult(REFUTED, [], contradiction, looked_for, derived)
    if not all_hold:
        _drop_scope(fact_g, scope)
        return SupposeResult(INCONCLUSIVE, [], None, looked_for, derived)

    # CONFIRMED. READ-ONLY: report the verdict + derivations, ink NOTHING, sweep the pencil.
    if not commit:
        _drop_scope(fact_g, scope)
        return SupposeResult(CONFIRMED, [], None, looked_for, derived)
    # COMMIT: EMIT the assumptions to INK (real facts), then sweep the pencil scaffolding.
    committed: list[Triple] = []
    for s, p, o in assumptions:
        s_id, o_id = _resolve(fact_g, s), _resolve(fact_g, o)
        if not _fact_exists(fact_g, s_id, p, o_id):    # scope=None: consult ink only
            ink = _MACHINE.apply(fact_g,               # EMIT to ink (monotone), as a MINT program
                                 [MINT("_ink", attrs={p: graded(1.0)},
                                       in_edges=["_s"], edges=["_o"])],
                                 State({"_s": s_id, "_o": o_id})).regs["_ink"]
            committed.append((s, p, o))
            if provenance:
                _record_confirmed(fact_g, ink)
    _drop_scope(fact_g, scope)
    return SupposeResult(CONFIRMED, committed, None, looked_for)


def explain_suppose(result: SupposeResult) -> list[str]:
    """RECORD the SUPPOSE as CNL: the verdict, what (if anything) entered ink, and what the in-scope
    reasoning looked at — the honest, renderable trace of a hypothesis test."""
    head = {
        CONFIRMED: "confirmed — every predicted consequence held under the supposition",
        REFUTED: ("refuted — the supposition entails the opposite of "
                  f"{result.contradiction}" if result.contradiction else "refuted"),
        INCONCLUSIVE: "inconclusive — no contradiction, but not every prediction was derivable in budget",
    }[result.status]
    lines = [head]
    if result.committed:
        lines.append("  committed to ink:")
        lines += [f"    {s} {p} {o}" for s, p, o in result.committed]
    if result.derived:                                     # read-only run (feedback #6): what held in-scope
        lines.append("  in-scope consequences (not committed):")
        lines += [f"    {s} {p} {o}" for s, p, o in result.derived]
    lines.append("  reasoned about:")
    lines += [f"    {ln}" for ln in result.looked_for]
    return lines
