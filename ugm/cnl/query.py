"""
Asking the knowledge base questions in CNL, and getting CNL answers (Q2).

Same discipline as everywhere else (vision §3/§8):
  - **Recognition is emergent.** A question is loaded as tokens and `QUESTION_FORMS`
    decide what it is — yes/no (`is S P O`), wh (`who P O`), or why (`why S P O`) —
    by which form fires. Nothing classifies the input from the top; an unrecognized
    question simply produces no `<query>` node.
  - **Execution is a §8 tool.** `ask` reflects the recognized `<query>` into the
    engine's `match` (the purely technical subgraph matcher) over the KB, or into
    `surface.explain` for why-questions. It never bakes reasoning of its own.
  - **Answers render from the graph** (the graph IS CNL), via `surface.render_relation`.

A question is an *interaction*, not corpus content: it is parsed in a throwaway
graph and executed against the KB by NAME, so asking never mutates the KB.
"""
from __future__ import annotations

import warnings

from .forms import WH, normalize_surface, tokenize
from ..production_rule import Pat, Rule
from ..lowering import match_pats as match, run_bank
from .surface import explain
from ..world_model import Graph


# Existential quantifier words. As a QUESTION subject, `is someone happy` / `is anything a dog`
# mean ∃ — "does ANY witness satisfy this" — matching a named individual (`bob is happy`) OR an
# anonymous existential witness, NOT a literal node named "someone". So an existential subject is
# answered by binding a VARIABLE in the match, the query-side dual of the labelled-null witness a
# `someone is …` FACT materializes. `everyone`/`everything` are UNIVERSAL, not existential, and are
# deliberately excluded (they would need a ∀-check, a different question). `they`/`it` are anaphora.
EXISTENTIAL_SUBJECTS: frozenset[str] = frozenset(
    {"someone", "somebody", "anyone", "anybody", "something", "anything"})

# Substrate copula vocabulary — single source of truth in `ugm.vocabulary` (Phase 2.5).
from ..vocabulary import COPULA, is_neg_pred


# ---------------------------------------------------------------------------
# Recognition — question shapes as forms (emergent, like every other form)
# ---------------------------------------------------------------------------

# Tag the "a" of an "is a" question so the generic forms can NAC it (same is_kw
# idiom as the rule grammar). Run FIRST (a prior pass), so the tag is present
# before the generic forms test their NAC — avoids a same-step race.
_KW_FORMS: list[Rule] = [
    Rule(key="ask.kw.a", lhs=[Pat("?x", "next", "a?")], rhs=[Pat("a?", "is_kw", "yes")]),
]


QUESTION_FORMS: list[Rule] = [
    # "is S a O ?"  -> a yes/no query on the canonical is_a relation
    Rule(
        key="ask.yesno.is_a",
        lhs=[Pat("?s", "first", "is?"), Pat("is?", "next", "?qs"),
             Pat("?qs", "next", "a?"), Pat("a?", "next", "?qo")],
        rhs=[Pat("<query>?", "qtype", "yesno"), Pat("<query>?", "q_s", "?qs"),
             Pat("<query>?", "q_p", "is_a"), Pat("<query>?", "q_o", "?qo")],
    ),
    # "is S P O ?"  -> a yes/no query (P is a plain relation, not the "a" marker)
    Rule(
        key="ask.yesno",
        lhs=[Pat("?s", "first", "is?"), Pat("is?", "next", "?qs"),
             Pat("?qs", "next", "?qp"), Pat("?qp", "next", "?qo")],
        nac=[Pat("?qp", "is_kw", "yes")],
        rhs=[Pat("<query>?", "qtype", "yesno"), Pat("<query>?", "q_s", "?qs"),
             Pat("<query>?", "q_p", "?qp"), Pat("<query>?", "q_o", "?qo")],
    ),
    # "is S O ?"  -> a yes/no query on the copula relation 'is' (O is terminal:
    # excludes both "is S P O" and "is S a O", whose O-slot has a successor)
    Rule(
        key="ask.yesno.is_state",
        lhs=[Pat("?s", "first", "is?"), Pat("is?", "next", "?qs"),
             Pat("?qs", "next", "?qo")],
        nac=[Pat("?qo", "next", "?z")],
        rhs=[Pat("<query>?", "qtype", "yesno"), Pat("<query>?", "q_s", "?qs"),
             Pat("<query>?", "q_p", "is"), Pat("<query>?", "q_o", "?qo")],
    ),
    # "does S P O ?"  -> a yes/no query on a plain relation. Generic over P (like `is S P O`
    # above): a question is GATED by its interrogative marker (`does`), so — unlike the
    # declarative side, which needs one form per DECLARED relation to stay controlled — no
    # per-relation form is needed here. `does the dog eat the squirrel` -> match `dog eat squirrel`.
    Rule(
        key="ask.yesno.does",
        lhs=[Pat("?s", "first", "does?"), Pat("does?", "next", "?qs"),
             Pat("?qs", "next", "?qp"), Pat("?qp", "next", "?qo")],
        nac=[Pat("?qp", "is_kw", "yes")],
        rhs=[Pat("<query>?", "qtype", "yesno"), Pat("<query>?", "q_s", "?qs"),
             Pat("<query>?", "q_p", "?qp"), Pat("<query>?", "q_o", "?qo")],
    ),
    # "who is a O ?"  -> a wh query on is_a
    Rule(
        key="ask.who.is_a",
        lhs=[Pat("?s", "first", "who?"), Pat("who?", "next", "is?"),
             Pat("is?", "next", "a?"), Pat("a?", "next", "?qo")],
        rhs=[Pat("<query>?", "qtype", "who"),
             Pat("<query>?", "q_p", "is_a"), Pat("<query>?", "q_o", "?qo")],
    ),
    # "who P O ?"  -> a wh query (subject is the unknown)
    Rule(
        key="ask.who",
        lhs=[Pat("?s", "first", "who?"), Pat("who?", "next", "?qp"),
             Pat("?qp", "next", "?qo")],
        nac=[Pat("?qo", "is_kw", "yes")],
        rhs=[Pat("<query>?", "qtype", "who"),
             Pat("<query>?", "q_p", "?qp"), Pat("<query>?", "q_o", "?qo")],
    ),
    # "why S is a O ?"  -> a derivation request on is_a
    Rule(
        key="ask.why.is_a",
        lhs=[Pat("?s", "first", "why?"), Pat("why?", "next", "?qs"),
             Pat("?qs", "next", "is?"), Pat("is?", "next", "a?"), Pat("a?", "next", "?qo")],
        rhs=[Pat("<query>?", "qtype", "why"), Pat("<query>?", "q_s", "?qs"),
             Pat("<query>?", "q_p", "is_a"), Pat("<query>?", "q_o", "?qo")],
    ),
    # "why S P O ?"  -> a derivation request (P not the "a" marker)
    Rule(
        key="ask.why",
        lhs=[Pat("?s", "first", "why?"), Pat("why?", "next", "?qs"),
             Pat("?qs", "next", "?qp"), Pat("?qp", "next", "?qo")],
        nac=[Pat("?qo", "is_kw", "yes")],
        rhs=[Pat("<query>?", "qtype", "why"), Pat("<query>?", "q_s", "?qs"),
             Pat("<query>?", "q_p", "?qp"), Pat("<query>?", "q_o", "?qo")],
    ),
]


# ---------------------------------------------------------------------------
# Execution — a §8 tool reflecting the <query> into `match` / `explain`
# ---------------------------------------------------------------------------

def _slot(graph: Graph, q: str, role: str) -> str | None:
    for r, o in graph.relations_from(q):
        if graph.has_key(r, role):
            return graph.name(o)
    return None


def _parse_qevent(graph: Graph, qid: str) -> dict:
    """Read an n-ary question pattern `<qevent>` into {qtype, pred, roles, unknown}.

    `roles` maps each role (subj/obj/<preposition>) to its value name; the queried role's
    value is the `<wh>` marker, recorded in `unknown`."""
    pred, roles, unknown = None, {}, None
    for r, o in graph.relations_from(qid):
        role, val = graph.predicate(r), graph.name(o)
        if role == "pred":
            pred = val
        else:
            roles[role] = val
            if val == WH:
                unknown = role
    return {"qtype": "nary", "pred": pred, "roles": roles, "unknown": unknown}


def _parse_question(question: str, extra_forms: list[Rule] = (), *, strata=None) -> dict | None:
    """Recognize `question` (in a throwaway graph) into a query dict.

    Binary -> {qtype, s, p, o}; n-ary -> {qtype:'nary', pred, roles, unknown}. `extra_forms`
    are caller-supplied generated forms (e.g. `forms.nary_question_forms(kb)` for the declared
    verbs). An n-ary `<qevent>` is PREFERRED over a binary `<query>`: the general `who P O`
    form also matches `who gives book to bob` (binding only P=gives, O=book), but that binary
    reading finds nothing — the fact is a reified event — so the n-ary reading is the right one.

    `strata` are the surface-normalization form banks (`forms.surface_forms(...)`): run first so a
    question with a determiner / multi-word entity ("is the bald eagle a bird") normalizes to the
    same names the assert path produced and matches by name. None (direct callers) => no
    normalization, single-word behaviour."""
    tmp = Graph()
    anchor = tokenize(tmp, question)
    if strata:
        normalize_surface(tmp, anchor, strata)
    run_bank(tmp, _KW_FORMS)          # tag keywords first (no NAC race)
    run_bank(tmp, list(QUESTION_FORMS) + list(extra_forms))
    for nid in tmp.nodes():       # prefer the n-ary reading when present
        if tmp.name(nid) == "<qevent>":
            return _parse_qevent(tmp, nid)
    for nid in tmp.nodes():
        if tmp.name(nid) != "<query>":
            continue
        return {
            "qtype": _slot(tmp, nid, "qtype"),
            "s": _slot(tmp, nid, "q_s"),
            "p": _slot(tmp, nid, "q_p"),
            "o": _slot(tmp, nid, "q_o"),
        }
    return None


def recognize(question: str, extra_forms: list[Rule] = (), *, strata=None) -> dict | None:
    """The parsed query if `question` is a recognized question, else None.

    Lets a caller (e.g. the REPL) branch question-vs-assertion by which forms fire,
    rather than by a hardcoded word list. `extra_forms` adds KB-derived question forms
    (e.g. n-ary question forms for the declared verbs); `strata` drives surface normalization
    (see `_parse_question`).
    """
    q = _parse_question(question, extra_forms, strata=strata)
    return q if (q is not None and q.get("qtype") is not None) else None


def _render_nary(q: dict, value: str) -> str:
    """Reconstruct the n-ary statement with `value` in the queried slot, in
    `subj pred obj <prep> arg` order."""
    roles = dict(q["roles"])
    roles[q["unknown"]] = value
    prep = next((k for k in roles if k not in ("subj", "obj")), None)
    return " ".join(x for x in (roles.get("subj"), q["pred"], roles.get("obj"),
                                prep, roles.get(prep) if prep else None) if x is not None)


def ask(graph: Graph, question: str, *, journal: list | None = None,
        rules: list | None = None, extra_forms: list[Rule] = (), strata=None) -> list[str]:
    """Answer a CNL `question` against the KB `graph`, in CNL.

    yes/no -> ['yes'] or ['no']; who -> the matching facts; n-ary -> the matching event(s)
    with the queried role filled; why -> the derivation trace (needs `journal` + `rules`, as
    `surface.explain` does). An unrecognized question returns '(no question form recognized
    this)'. `extra_forms` adds KB-derived question forms (n-ary verbs); `strata` drives surface
    normalization (see `_parse_question`)."""
    q = _parse_question(question, extra_forms, strata=strata)
    if q is None or q.get("qtype") is None:
        return ["(no question form recognized this)"]

    if q["qtype"] == "yesno":
        # An existential subject (`is anyone happy`) becomes ∃ — a VARIABLE that matches any
        # witness (named or anonymous); otherwise the literal subject is matched by name.
        subj = "?w" if q["s"] in EXISTENTIAL_SUBJECTS else q["s"]
        found = bool(match(graph, [Pat(subj, q["p"], q["o"])]))
        return ["yes" if found else "no"]

    if q["qtype"] == "who":
        names = sorted({graph.name(b["?x"])
                        for b in match(graph, [Pat("?x", q["p"], q["o"])])})
        return [f"{n} {q['p']} {q['o']}" for n in names] or ["(no answer)"]

    if q["qtype"] == "nary":
        if q["unknown"] is None or q["pred"] is None:
            return ["(no answer)"]
        # join all role constraints on one event node `?e`; the queried role is the variable.
        pats = [Pat("?e", "pred", q["pred"])]
        for role, val in q["roles"].items():
            pats.append(Pat("?e", role, "?x" if role == q["unknown"] else val))
        names = sorted({graph.name(b["?x"]) for b in match(graph, pats)})
        return [_render_nary(q, n) for n in names] or ["(no answer)"]

    if q["qtype"] == "why":
        if journal is None or rules is None:
            return ["(why needs the firing journal and rules)"]
        return explain(graph, journal, rules, q["s"], q["p"], q["o"])

    return ["(no question form recognized this)"]


# ---------------------------------------------------------------------------
# Goal-directed answering — the engine works BACKWARD (decision-attrgraph-rehost,
# decision-cwa-default). Recognition stays forward; ANSWERING demands only the question-goal.
# ---------------------------------------------------------------------------

def _reify_rules(rules: list[Rule]) -> Graph:
    """A reified rule graph (`<rule> -[lhs/rhs/nac/drop]-> patom`) the demand-driven firmware reads —
    `write_rule` for each executable `Rule`. Built per `ask_goal` call; the head index is (re)built
    lazily by `chain_sip`/`check`. (A caller answering many questions can reify once and reuse it.)"""
    from .rule_graph import write_rule
    rg = Graph()
    for r in rules:
        write_rule(rg, r)
    return rg


def _materialize_fact(graph: Graph, s: str, p: str, o: str) -> None:
    """Assert the domain relation `s p o` into the KB (monotone — the ask-user acquisition path),
    reusing existing same-named nodes or minting them. Never deletes (§5)."""
    def node(name: str) -> str:
        existing = graph.nodes_named(name)
        return existing[0] if existing else graph.add_node(name)
    graph.add_relation(node(s), p, node(o))

def _warn_case_folded_mismatch(graph: Graph, q: dict) -> None:
    """Feedback #3: CNL question parsing lowercases identifiers, so a query about a case-PRESERVED node
    (e.g. `eB`, created via the tuple API rather than CNL) silently folds to `eb` and returns a FALSE
    negative. The folding stays (the CNL and tuple paths are documented to differ), but the SILENT
    mismatch is removed: warn when a folded query identifier matches NO node yet a case-variant node
    exists — the actionable signal ("use lowercase for CNL, or the case-preserving tuple APIs")."""
    names = {v for k in ("s", "o") if isinstance((v := q.get(k)), str)}
    names |= {v for v in (q.get("roles") or {}).values() if isinstance(v, str)}
    for nm in names:
        if not nm or nm in EXISTENTIAL_SUBJECTS or nm == WH or graph.nodes_named(nm):
            continue                                     # wildcard, or an exact node match exists — fine
        variants = sorted({graph.name(n) for n in graph.nodes() if graph.name(n).lower() == nm})
        if variants:
            warnings.warn(
                f"CNL query folded a name to '{nm}', which matches no node, but case-variant node(s) "
                f"{variants} exist. CNL questions lowercase identifiers — use lowercase node names for "
                f"CNL queries, or the case-preserving tuple APIs (check / chain_sip / suppose).",
                stacklevel=3)


def ask_goal(graph: Graph, question: str, rules: list[Rule], *,
             policy=None, open_preds: frozenset[str] | None = None, ask_user=None,
             extra_forms: list[Rule] = (), strata=None, journal: list | None = None,
             focus_scope: frozenset[str] | None = None, provenance: bool = False) -> list[str]:
    """Answer a CNL `question` GOAL-DIRECTED: demand just the question's goal through the ISA
    machine (`GoalSolver`), materializing only the facts that goal needs — NOT a forward pass over
    the whole rule set. This is the backward face of the engine (`decision-attrgraph-rehost`
    Phase B): `ask` above reads a pre-materialized graph; `ask_goal` DOES the reasoning on demand.

    CWA-DEFAULT + per-predicate OWA opt-in (`decision-cwa-default`, revising the earlier
    OWA-default). An agent must act, and action needs a decision, so the DEFAULT is closed-world: a
    derivable goal is `yes`; an UNDERIVABLE goal is `no` — a DEFEASIBLE "no, to the best of current
    knowledge" (revisable, computed demand-driven so nothing is materialized/retracted — §5-safe),
    not a claim of necessity. A predicate declared OPEN (`open_preds`) is the exception: there
    absence is NOT taken as false (`unknown`), for the cases where CWA is unsafe/undesirable ("are
    there mice in the cellar" — no sighting != no mice; "no test failure" != no bug). The three
    negatives an agent should distinguish — ENTAILED-no (a derivable `is_not`, as trustworthy as a
    yes), ASSUMED-no (CWA default, the defeasible one), and UNKNOWN (open predicate, unprovable) —
    collapse to `no`/`no`/`unknown` here; surfacing the hard-vs-assumed KIND for the metareasoning
    escalation policy (deontics-over-epistemic-acts) is the capstone follow-up.

    ASK-USER (the OWA evidence-gatherer): when a yes/no goal on an OPEN predicate is `unknown` and an
    `ask_user(subj, rel, obj) -> bool | None` handler is given, the engine gathers evidence from it
    (the human-in-the-loop / a tool, §8). `True` MATERIALIZES the fact (monotone, persists) -> `yes`;
    `False` -> `no`; `None` -> stays `unknown`. Only OPEN predicates gather (a CWA-default predicate
    is already decided `no`); this is where the deontic-triggered "better check" escalation will hook.

    Note: reasoning materializes the demanded facts into `graph` (monotone — never deletes; §5). Pass
    a `graph.copy()` if the KB must stay untouched. why/n-ary demand-materialize then render via `ask`.

    FIRMWARE v3 (demand-driven NEGATION) — answering is the DEMAND-DRIVEN chain (`check`/`chain_sip`),
    not a forward materialize-then-read. A NAC clause `not L` is decided ON DEMAND by negation-as-failure
    (nested negative demand -> positive closure -> absence decides); NOTHING is completed or retracted for
    a negation. This RETIRES the forward `decide.solve` (aggressive `is_not` completion + INTERPOSE
    defeat): a human decides a negation by ASKING the positive when the question comes up, absence-decides
    — the agent-not-theorem-prover model, restoring locality (only the goal's own closure is materialized)
    for the RIGHT reason (the model), and making fuel-exhaustion an honest `unknown` the forward model
    cannot express. Same yes/no/who answers as the forward path on every stratifiable bank (the step-4
    differential gate); a genuinely NON-stratifiable bank is rejected at LOAD by
    `authoring.lint_stratifiable` (object-aware), so the chain never mis-answers one."""
    from ..check import check, collapse
    from ..chain import chain_sip, bound_demands, _facts_matching
    from ..policy import DEFAULT_POLICY
    from dataclasses import replace

    # The closed-vs-open reading of absence is the firmware STANCE (`policy.py`), not the engine's.
    # `open_preds=` folds into the default closed-world policy as the OWA exception set (back-compat).
    policy_ = policy if policy is not None else DEFAULT_POLICY
    if open_preds is not None:
        policy_ = replace(policy_, open_preds=frozenset(open_preds))

    q = _parse_question(question, extra_forms, strata=strata)
    if q is None or q.get("qtype") is None:
        return ["(no question form recognized this)"]
    _warn_case_folded_mismatch(graph, q)             # feedback #3: no silent case-fold false negative

    def concept_key(p: str, o: str | None) -> str:
        # Openness is a property of the CONCEPT: for a copula query (`is S C`) it is the object
        # concept C (`C is open world`), not the shared copula; for a relational query it is R.
        return o if (p == COPULA and o is not None) else p

    rule_g = _reify_rules(rules)

    def gather_open_premises(goal: tuple[str, str | None, str | None]) -> bool:
        """MID-CHAIN evidence gathering (firmware v3 / §8.5b): a rule blocked ONLY by an OPEN premise the
        derivation DEMANDS can fire once that premise is gathered — so ask the human/tool for the open
        premises on the demand frontier and materialize the confirmed ones. Returns whether anything was
        materialized (so the caller re-decides). Only called when the goal was NOT already derivable.

        WHICH premises to ask is DERIVED, never hardcoded (§D): the candidates are the visible bound
        `<demand>` magic-set the backward closure itself produced (`bound_demands`), filtered by the
        FIRMWARE openness STANCE (`policy.is_open`, data on `policy`) — no predicate/English-word list in
        Python decides it. Only fully-bound premises OTHER than the goal are asked (the goal itself is the
        existing top-level OWA gather below); each is asked at most once; the loop re-runs the closure
        after materializing and stops when nothing new is gathered (monotone → converges)."""
        if ask_user is None:
            return False
        asked: dict = {}
        materialized = False
        while True:
            chain_sip(graph, rule_g, goal, provenance=provenance, focus_scope=focus_scope)
            if _facts_matching(graph, goal[0], goal[1], goal[2], focus_scope=focus_scope):
                return materialized                            # goal now derivable — done gathering
            frontier = [(p, s, o) for (p, s, o) in bound_demands(rule_g)
                        if s is not None and o is not None and (p, s, o) != goal
                        and (p, s, o) not in asked and not is_neg_pred(p)   # skip NAF neg-pred demands
                        and policy_.is_open(concept_key(p, o))
                        and not _facts_matching(graph, p, s, o, focus_scope=focus_scope)]
            if not frontier:
                return materialized
            progressed = False
            for (p, s, o) in frontier:
                held = ask_user(s, p, o)                        # the caller's human/tool handler
                asked[(p, s, o)] = held
                if held is True:
                    _materialize_fact(graph, s, p, o)          # persist the acquired premise (monotone)
                    progressed = materialized = True
            if not progressed:
                return materialized                            # no new evidence — re-running won't change

    if q["qtype"] == "yesno":
        if q["s"] in EXISTENTIAL_SUBJECTS:
            # `is anyone happy` is ∃ — demand the WILDCARD-subject goal, then match any witness.
            chain_sip(graph, rule_g, (q["p"], None, q["o"]), provenance=provenance, focus_scope=focus_scope)
            if match(graph, [Pat("?w", q["p"], q["o"])]):
                return ["yes"]
            return ["unknown"] if policy_.is_open(concept_key(q["p"], q["o"])) else ["no"]
        # a bound goal: the demand-driven 4-status CHECK, collapsed to yes/no/unknown. CHECK runs the
        # positive closure (POSITIVE), the negative closure (ENTAILED_NEG), else CWA-default ASSUMED_NO
        # unless the concept is OPEN (UNKNOWN) or fuel ran out before closure (also UNKNOWN).
        goal = (q["p"], q["s"], q["o"])
        v = collapse(check(graph, rule_g, goal, policy=policy_,
                           provenance=provenance, focus_scope=focus_scope))
        # MID-CHAIN gather (§8.5b): only when the goal was NOT derivable — ask for the OPEN premises the
        # derivation demands, materialize the confirmed ones, and re-decide (so a rule blocked solely by a
        # gatherable fact fires instead of being wrongly assumed-no). A derivable goal pays no extra work.
        if v != "yes" and ask_user is not None and gather_open_premises(goal):
            v = collapse(check(graph, rule_g, goal, policy=policy_,
                               provenance=provenance, focus_scope=focus_scope))
        # OWA evidence-gatherer: an open UNKNOWN the goal needs -> gather (never a CWA-default `no`).
        if v == "unknown" and ask_user is not None and q["o"] is not None:
            held = ask_user(q["s"], q["p"], q["o"])
            if held is True:
                _materialize_fact(graph, q["s"], q["p"], q["o"])   # persist the acquired fact
                return ["yes"]
            if held is False:
                return ["no"]
        return [v]

    if q["qtype"] == "who":
        chain_sip(graph, rule_g, (q["p"], None, q["o"]),                            # wildcard-subject goal
                  provenance=provenance, focus_scope=focus_scope)
        names = sorted({graph.name(b["?x"])
                        for b in match(graph, [Pat("?x", q["p"], q["o"])])})
        if names:
            return [f"{n} {q['p']} {q['o']}" for n in names]
        return ["unknown"] if policy_.is_open(concept_key(q["p"], q["o"])) else ["(no answer)"]

    if q["qtype"] == "why":
        # demand the goal WITH provenance (RECORD, mode 9) so the in-graph support is present, then
        # render the derivation trace via the existing reader. `explain` reads the in-graph proves/uses
        # support (not the journal), so an empty journal is enough to pass the reader's guard.
        chain_sip(graph, rule_g, (q["p"], q["s"], q["o"]), provenance=True, focus_scope=focus_scope)
        return ask(graph, question, journal=journal if journal is not None else [],
                   rules=rules, extra_forms=extra_forms, strata=strata)

    # n-ary: demand the event predicate, then render via the reader (event-role reads stay in `ask`).
    if q.get("pred") is not None:
        chain_sip(graph, rule_g, (q["pred"], None, None), provenance=provenance, focus_scope=focus_scope)
    return ask(graph, question, journal=journal, rules=rules, extra_forms=extra_forms, strata=strata)
