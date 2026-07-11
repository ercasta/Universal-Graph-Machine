"""
Coreference as a serialized cursor — the rules-based replacement for `coref.coref_on_demand`'s
Python generate-and-test loop (docs/coref_as_rules_design.md).

A `<coref>` token walks the pairs of one name's mentions ONE AT A TIME (serialized, so a
rejected link's consequences never pollute the next pair's test — coref hypotheses interact
through `same_as`, unlike decide's independent negatives). The whole process runs in ONE
`run()`: control flow is emergent (rule firing + the engine's fixpoint-then-service cycle), NOT
a Python driver loop.

  materialize  a `<pair>` chain over the mentions + a cursor on the first pair   (thin seed)
  hypothesize  cursor pair -> `a same_as b`  +  a `<call> settle` barrier
  propagate    same_as_rules   (reused, provenance ON)
  detect       constraint schemas -> `<contradiction>`   (reused, provenance ON)
  [engine services the `<call> settle` ONLY at quiescence -> marks the pair `settled`]
  reject       settled + `<contradiction> about a mention  ->  `<retract> targets link`   (meta)
  keep         (nothing: a link that is never retracted is kept — no NAC, no NAF)
  advance      settled + cursor pair has a `pnext`  ->  move cursor  (fires positively; the
               walk ends naturally at the last pair, which has no `pnext`)

This module holds the vocabulary, the thin materializer, and the cursor rules. Reasoning
(propagate/detect) and retraction (`RETRACT_RULES`) are added by the caller (`coref`), not here.
"""
from __future__ import annotations

from typing import Callable

from . import retraction as ret
from .dispatch import call_arg
from .external import ARG
from .production_rule import Pat, Rule
from .lowering import run_bank
from .cnl.universal import UNIVERSAL_RULES, same_as_rules
from .world_model import Graph

Resolver = Callable[[Graph, str, str, str], str]

SAME_AS = "same_as"
NOT_SAME_AS = ret.NOT_SAME_AS          # the recorded rejection (re-use retraction's vocabulary)

# Vocabulary — all ordinary nodes/relations; `<coref>`/`<coref-pair>`/`<coref-settled>` are
# keyword nodes (canonicalize skips them) but NOT inert, so the cursor rules see them. The
# relation names are deliberately distinct so the `same_as` propagation (which carries only the
# named content predicates) never touches the cursor scaffolding.
CTOK = "<coref>"                 # the cursor token
PAIR = "<coref-pair>"            # one candidate pair of mentions
CURSOR = "coref_cursor"          # <coref> --coref_cursor--> the pair currently under test
PA = "coref_a"                   # <pair> --coref_a--> mention
PB = "coref_b"                   # <pair> --coref_b--> mention
PNEXT = "coref_pnext"            # <pair> --coref_pnext--> next <pair> (the walk order)
MENTION = "coref_mention"        # <coref> --coref_mention--> each mention
SETTLED = "coref_settled"        # <pair> --coref_settled--> <coref-settled> (barrier stamp)
SETTLED_MARK = "<coref-settled>"
CHECKED = "coref_checked"        # <pair> --coref_checked--> <coref-checked> (one-step delay after settled)
CHECKED_MARK = "<coref-checked>"
SETTLE = "settle"                # the barrier tool name
IS_A = "is_a"
DISJOINT = "disjoint_from"


def _ensure(graph: Graph, name: str, *, control: bool = False) -> str:
    found = graph.nodes_named(name)
    return found[0] if found else graph.add_node(name, control=control)


# ---------------------------------------------------------------------------
# The thin materializer (demand scope — locates mentions by name, like seed_demand)
# ---------------------------------------------------------------------------

def materialize_cursor(graph: Graph, name: str, *, skip=None) -> str | None:
    """Wire a `<coref>` token for `name`: a `coref_mention` edge to each mention, a linear
    `<coref-pair>` chain over every unordered pair (`coref_a`/`coref_b` + `coref_pnext`), and a
    `coref_cursor` on the first pair. Returns the token id, or None if <2 mentions remain.

    Enumerating the mentions (by name) and the pair sequence is demand SCOPING — the same
    category as `seed_demand` locating a node by name — NOT the coreference DECISION (which is
    the cursor rules). `skip(a, b)` (optional) drops a pair from the chain (e.g. already
    `not_same_as` from a prior episode), keeping the walk idempotent."""
    mentions = [m for m in graph.nodes_named(name)]
    if len(mentions) < 2:
        return None
    # The cursor apparatus is CONTROL-layer scaffolding (ephemeral, GC'd by `_gc_cursor`), so mint
    # every scaffolding node/edge control-stamped — this is what lets the `<coref>`-gated ADVANCE
    # rule's `drop` of the `coref_cursor` edge pass run_bank's `DROP_CTRL` (which refuses a FACT
    # edge). A Python helper minting a control marker must stamp it, exactly like the planner's
    # tool-minted `done`/`ranked` markers (implementation_plan.md Phase 0.3). Harmless on the
    # rewriter path (it ignores the control flag when matching/dropping). Content mentions are
    # ordinary fact nodes — only the scaffolding wiring is control.
    tok = graph.add_node(CTOK, control=True)
    for m in mentions:
        graph.add_relation(tok, MENTION, m, control=True)
    pairs: list[str] = []
    for i in range(len(mentions)):
        for j in range(i + 1, len(mentions)):
            a, b = mentions[i], mentions[j]
            if skip is not None and skip(a, b):
                continue
            p = graph.add_node(PAIR, control=True)
            graph.add_relation(p, PA, a, control=True)
            graph.add_relation(p, PB, b, control=True)
            pairs.append(p)
    if not pairs:
        return None
    for prev, nxt in zip(pairs, pairs[1:]):
        graph.add_relation(prev, PNEXT, nxt, control=True)
    graph.add_relation(tok, CURSOR, pairs[0], control=True)
    return tok


# ---------------------------------------------------------------------------
# The barrier tool — its post-quiescence servicing IS the "detection settled" signal
# ---------------------------------------------------------------------------

def settle_tool(graph: Graph, call_id: str) -> set[str]:
    """Tool for a `settle` call: stamp the argument pair `settled`. It does NO inspection — the
    engine services a `<call>` only once rules have quiesced (propagation + detection done), so
    the mere fact this ran is the "detection is complete for this pair" signal that the verdict
    rules gate on. That signal is irreducibly the engine's to give (a rule cannot match "no rule
    can fire"); this is the same primitive the walker's `dec` uses."""
    p = call_arg(graph, call_id, ARG)
    if p is None or not graph.has(p):
        return set()
    mark = _ensure(graph, SETTLED_MARK, control=True)
    graph.add_relation(p, SETTLED, mark, control=True)   # barrier stamp = control scaffolding
    return {p, mark}


SETTLE_TOOLS: dict = {SETTLE: settle_tool}


# ---------------------------------------------------------------------------
# The cursor rules — CHECK-BEFORE-COMMIT (retraction-free; docs/coref_as_rules_design.md)
# ---------------------------------------------------------------------------
#
# Per pair the walk (a) waits for a barrier so the endpoints' sorts are current, (b) checks a
# disqualifying clash between the endpoints, and (c) COMMITS the link only if there is no clash.
# Coref is thus purely ADDITIVE — it never links-then-retracts — so there is no cascade and no
# propagation-fight (the step-4 finding). The general propagate-then-retract path is deferred; see
# the design note's generalization hook.
#
# The one ordering hazard is CLASH-vs-COMMIT (a `NOT not_same_as` NAC on COMMIT would race a CLASH
# firing in the same wave). It is resolved by a one-step delay: the `settle` barrier marks a pair
# `settled`; a CHECKED rule turns that into `checked` one step later; CLASH fires on `settled`
# (same step as CHECKED) while COMMIT/ADVANCE fire on `checked` — so any `not_same_as` CLASH
# produced is already present when COMMIT's NAC is evaluated. A NAC gated behind the barrier this
# way is STRATIFIED negation (vision §11 permits it), not premature NAF.

# PROBE: emit the settle barrier for the current pair (so its endpoints' sort closures are
# complete — is_a transitivity + prior commits' same_as propagation have quiesced — before the
# clash check reads them). Fires once per cursor position.
PROBE = Rule(
    key="coref.probe",
    lhs=[Pat(f"{CTOK}?", CURSOR, "?p")],
    rhs=[Pat("<call>?", "tool", SETTLE), Pat("<call>?", ARG, "?p")],
)

# CHECKED: the one-step delay marker — `settled` (this step) becomes `checked` (next step), the
# window in which CLASH runs so COMMIT sees any `not_same_as` it produced.
CHECKED_RULE = Rule(
    key="coref.checked",
    lhs=[Pat("?p", SETTLED, "?m")],
    rhs=[Pat("?p", CHECKED, f"{CHECKED_MARK}?")],
)

# CLASH is not a single rule but a FAMILY generated per `A disjoint_from B` declaration, matching
# the cat names as LITERALS (name-based, like the general `_disjoint_rule`), so it is robust to
# distinct same-NAME instances — `paul is a teacher` and `teacher is disjoint from student` create
# separate `teacher` nodes, and only a literal `?a is_a teacher` matches both. A single generic
# rule binding `?s1 disjoint_from ?s2` to instances would miss when the pauls' `is_a`-object and
# the disjoint declaration are different `teacher` instances. is_a transitivity (UNIVERSAL_RULES)
# supplies inherited sorts before the barrier, so a subtype clash surfaces too.

def _clash_rule(cat_a: str, cat_b: str) -> Rule:
    """The endpoints are provably distinct — `?a is_a cat_a` and `?b is_a cat_b` for a declared
    disjoint pair. Record `not_same_as` and DON'T link. `meta=True` keeps it a clean record."""
    return Rule(
        key=f"coref.clash.{cat_a}.{cat_b}",
        lhs=[Pat(f"{CTOK}?", CURSOR, "?p"), Pat("?p", SETTLED, "?m"),
             Pat("?p", PA, "?a"), Pat("?p", PB, "?b"),
             Pat("?a", IS_A, cat_a), Pat("?b", IS_A, cat_b)],
        rhs=[Pat("?a", NOT_SAME_AS, "?b")],
        meta=True,
    )


def clash_rules(graph: Graph) -> list[Rule]:
    """Generate the cross-node clash rules from the graph's `A disjoint_from B` declarations (both
    orientations, since a pair is unordered). Read like `rule_graph.rules_in_graph` reads the
    constraint schemas — the disjointness is DATA, the rules are derived from it."""
    seen: set[tuple[str, str]] = set()
    rules: list[Rule] = []
    for n in graph.nodes():
        for r, o in graph.relations_from(n):
            if not graph.has_key(r, DISJOINT):
                continue
            a, b = graph.name(n), graph.name(o)
            for x, y in ((a, b), (b, a)):
                if (x, y) not in seen:
                    seen.add((x, y))
                    rules.append(_clash_rule(x, y))
    return rules


# COMMIT: no clash was found for this pair (barrier-gated NAC = stratified) -> link it. The reused
# `same_as_rules` (added by the caller) then compose facts across the kept link — and, crucially,
# extend the endpoints' sort closures BEFORE the next pair's barrier, so a transitive clash is
# caught at that pair's CLASH check.
COMMIT = Rule(
    key="coref.commit",
    lhs=[Pat(f"{CTOK}?", CURSOR, "?p"), Pat("?p", CHECKED, "?c"),
         Pat("?p", PA, "?a"), Pat("?p", PB, "?b")],
    nac=[Pat("?a", NOT_SAME_AS, "?b")],
    rhs=[Pat("?a", SAME_AS, "?b")],
)

# ADVANCE: once the pair is `checked` (its commit/clash decision has been made this step) and has
# a successor, move the cursor on. Gated on `checked` (NOT `settled`) so COMMIT — which also fires
# on `checked` for the same cursor — is not skipped by the cursor moving first. Fires POSITIVELY
# on `pnext`; the last pair has none, so the walk ends naturally.
ADVANCE = Rule(
    key="coref.advance",
    lhs=[Pat(f"{CTOK}?", CURSOR, "?p"), Pat("?p", CHECKED, "?c"), Pat("?p", PNEXT, "?p2")],
    rhs=[Pat(f"{CTOK}?", CURSOR, "?p2")],
    drop=[Pat(f"{CTOK}?", CURSOR, "?p")],
)

# The cursor control rules. The caller appends the generated `clash_rules(graph)`, the reused
# propagation (`same_as_rules(preds)`), and is_a transitivity (`UNIVERSAL_RULES`) so the whole walk
# runs in ONE `run(..., provenance=True, tools=SETTLE_TOOLS)` — no Python loop, no retraction.
CURSOR_RULES: list[Rule] = [PROBE, CHECKED_RULE, COMMIT, ADVANCE]

# STEP 2 cursor-mechanics ruleset (PROBE + CHECKED + ADVANCE only) — walks every pair with no
# reasoning/clash/commit, to exercise the cursor + barrier + service cycle in isolation.
CURSOR_WALK_STUB: list[Rule] = [PROBE, CHECKED_RULE, ADVANCE]


# ---------------------------------------------------------------------------
# FORCE mode — `X is one thing`: link EVERY pair unconditionally (no clash check)
# ---------------------------------------------------------------------------
#
# The user asserted all mentions are ONE entity, overriding the distinct-witness default. So we
# commit every pair even if incompatible — a genuine single-identity mistake (`ice is a solid` +
# `ice is a liquid`) then surfaces as a REAL `<contradiction>` under the general detection
# (Session._check), instead of being read as two distinct witnesses. No retraction: force KEEPS
# the contradiction by design (it is the point). FORCE_COMMIT is COMMIT without the clash NAC.
FORCE_COMMIT = Rule(
    key="coref.force.commit",
    lhs=[Pat(f"{CTOK}?", CURSOR, "?p"), Pat("?p", CHECKED, "?c"),
         Pat("?p", PA, "?a"), Pat("?p", PB, "?b")],
    rhs=[Pat("?a", SAME_AS, "?b")],
)
FORCE_RULES: list[Rule] = [PROBE, CHECKED_RULE, FORCE_COMMIT, ADVANCE]


# ---------------------------------------------------------------------------
# RESOLVER mode — a CONSISTENT-but-ambiguous pair is referred to the user
# ---------------------------------------------------------------------------
#
# CLASH still auto-rejects provably-distinct pairs (no user needed). For a pair with NO clash, an
# oracle decides identity: RESOLVE_EMIT materializes a `<call> resolve` (only where CLASH did not
# record `not_same_as`), and the resolve tool writes `same_as` (keep) or `not_same_as` (distinct).
RESOLVE = "resolve"
RESOLVE_EMIT = Rule(
    key="coref.resolve.emit",
    lhs=[Pat(f"{CTOK}?", CURSOR, "?p"), Pat("?p", CHECKED, "?c"),
         Pat("?p", PA, "?a"), Pat("?p", PB, "?b")],
    nac=[Pat("?a", NOT_SAME_AS, "?b")],              # skip pairs CLASH already rejected
    rhs=[Pat("<call>?", "tool", RESOLVE), Pat("<call>?", PA, "?a"), Pat("<call>?", PB, "?b")],
)
# CLASH rules are generated per declaration and added by the caller (like CURSOR_RULES).
RESOLVE_RULES: list[Rule] = [PROBE, CHECKED_RULE, RESOLVE_EMIT, ADVANCE]


def _resolve_tool(resolver: Resolver) -> Callable[[Graph, str], "set[str]"]:
    """Wrap a Python `resolver(graph, name, a, b) -> 'same'|'distinct'` as a `resolve` tool. It
    reads the pair off the call, consults the resolver on the mentions' NAME, and writes the
    verdict as a fact: `same_as` (keep) or `not_same_as` (distinct). The DECISION is the oracle's;
    the tool is the §8 boundary that carries it into the graph."""
    def tool(graph: Graph, call_id: str) -> set[str]:
        a = call_arg(graph, call_id, PA)
        b = call_arg(graph, call_id, PB)
        if a is None or b is None or not (graph.has(a) and graph.has(b)):
            return set()
        verdict = resolver(graph, graph.name(a), a, b)
        pred = NOT_SAME_AS if str(verdict).strip().lower().startswith("d") else SAME_AS
        graph.add_relation(a, pred, b)
        return {a, b}
    return tool


# ---------------------------------------------------------------------------
# Incident predicates + idempotence helpers (pure — not the DECISION)
# ---------------------------------------------------------------------------

def _incident_predicates(graph: Graph, mentions: list[str]) -> list[str]:
    """The relation predicates actually INCIDENT to `mentions` (either position) — the only ones
    worth propagating across a link (propagating the whole vocabulary is what makes `same_as`
    saturate). `same_as`/provenance/scaffolding excluded."""
    preds: set[str] = set()
    for m in mentions:
        for r, _o in graph.relations_from(m):
            preds.add(graph.predicate(r))
        for r in graph.into(m):
            preds.add(graph.predicate(r))
    preds.discard(SAME_AS)
    return sorted(p for p in preds if not p.startswith("<") and p not in ("next", "first"))


def _same_as_live(graph: Graph, a: str, b: str) -> bool:
    return (any(graph.has_key(r, SAME_AS) and b in graph.out(r) for r in graph.out(a))
            or any(graph.has_key(r, SAME_AS) and a in graph.out(r) for r in graph.out(b)))


# The scaffolding names a completed walk leaves behind (token, pairs, cursor edges, barrier marks).
# GC'd after each walk so the content graph stays clean (like walk_on_demand GC-ing its demands).
_SCAFFOLD_NAMES = (CTOK, PAIR, CURSOR, PA, PB, PNEXT, MENTION, SETTLED, CHECKED,
                   SETTLED_MARK, CHECKED_MARK)


def _gc_cursor(graph: Graph) -> None:
    for nm in _SCAFFOLD_NAMES:
        for n in list(graph.nodes_named(nm)):
            graph.remove_node(n)


# ---------------------------------------------------------------------------
# resolve_coref — the whole walk in ONE run() (the coref tool's new body)
# ---------------------------------------------------------------------------

def resolve_coref(graph: Graph, name: str, *, resolver: Resolver | None = None,
                  force: bool = False, base_predicates=None) -> None:
    """Resolve coreference for `name`'s mentions by the check-before-commit cursor walk, in ONE
    `run()` (no Python loop, no retraction). `force` links every pair unconditionally (`X is one
    thing`); `resolver` refers a consistent-but-ambiguous pair to the user; the default checks a
    disjoint-sort clash and commits only compatible pairs. Additive — provably-distinct or
    user-distinct mentions are recorded `not_same_as` and never linked."""
    mentions = graph.nodes_named(name)
    if len(mentions) < 2:
        return
    preds = (sorted(set(base_predicates)) if base_predicates is not None
             else sorted(set(_incident_predicates(graph, mentions)) | {"is_a"}))
    skip = lambda a, b: ret.is_rejected(graph, a, b) or _same_as_live(graph, a, b)
    if materialize_cursor(graph, name, skip=skip) is None:
        return
    if force:
        rules, tools = FORCE_RULES, SETTLE_TOOLS       # link all; no clash check (force keeps clashes)
    elif resolver is not None:
        rules = RESOLVE_RULES + clash_rules(graph)     # auto-reject provably-distinct, then ask
        tools = {**SETTLE_TOOLS, RESOLVE: _resolve_tool(resolver)}
    else:
        rules, tools = CURSOR_RULES + clash_rules(graph), SETTLE_TOOLS
    # ISA forward driver (implementation_plan.md Phase 0.5): the cursor scaffolding is control-
    # stamped (materialize_cursor/settle_tool), so the `<coref>`-gated ADVANCE `drop` lowers to
    # DROP_CTRL over control edges; `<call>` settle/resolve tools are serviced at fixpoint;
    # provenance minting matches `rewriter`. The COMMIT/CLASH heads (same_as/not_same_as) are
    # control-stamped like the walker shortcut (their rules are `<coref>`-gated) — a retractable
    # coref verdict is control-layer; matching ignores the flag so propagation is unaffected.
    run_bank(graph, rules + same_as_rules(preds) + UNIVERSAL_RULES, tools=tools, provenance=True)
    _gc_cursor(graph)


def coref_request_handler(resolver: Resolver | None = None, *, base_predicates=None,
                          force_names=None) -> Callable[[Graph, str], "set[str]"]:
    """A tool for a coref request `<call> --tool--> coref --arg--> X`: resolve coreference for the
    requested entity's NAME via `resolve_coref`. Registered as the `coref` tool. `force_names` (a
    set) selects explicit single-identity entities (`is_unique` facts) resolved with `force=True`.
    The force decision stays DATA (the `is_unique` facts threaded here), not hardcoded Python."""
    forced = set(force_names) if force_names else set()

    def handler(graph: Graph, call_id: str) -> set[str]:
        arg = call_arg(graph, call_id, ARG)
        if arg is None or not graph.has(arg):
            return set()
        nm = graph.name(arg)
        resolve_coref(graph, nm, resolver=resolver, force=nm in forced,
                      base_predicates=base_predicates)
        return set(graph.nodes_named(nm)) | {arg}
    return handler
