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
from ..chain import resolve_write_node, ById


# ---------------------------------------------------------------------------
# Recognition — question shapes as forms (emergent, like every other form)
# ---------------------------------------------------------------------------

# Tag the "a" of an "is a" question so the generic forms can NAC it (same is_kw
# idiom as the rule grammar). Run FIRST (a prior pass), so the tag is present
# before the generic forms test their NAC — avoids a same-step race.
_KW_FORMS: list[Rule] = [
    Rule(key="ask.kw.a", lhs=[Pat("?x", "next", "a?")], rhs=[Pat("a?", "is_kw", "yes")]),
    # `is` mid-sentence is the copula keyword, never a subject/object name — tagging it lets the
    # generic why form REFUSE the inverted "why is S O" reading (which used to bind s='is' and
    # answer "(not present)"); the dedicated inverted forms below handle it.
    Rule(key="ask.kw.is", lhs=[Pat("?x", "next", "is?")], rhs=[Pat("is?", "is_kw", "yes")]),
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
    # "why is S a O ?"  -> the INVERTED (question-order) form of the same is_a request
    Rule(
        key="ask.why.yesno.is_a",
        lhs=[Pat("?s", "first", "why?"), Pat("why?", "next", "is?"),
             Pat("is?", "next", "?qs"), Pat("?qs", "next", "a?"), Pat("a?", "next", "?qo")],
        rhs=[Pat("<query>?", "qtype", "why"), Pat("<query>?", "q_s", "?qs"),
             Pat("<query>?", "q_p", "is_a"), Pat("<query>?", "q_o", "?qo")],
    ),
    # "why is S O ?"  -> the INVERTED copula form ("why is ada thief" = "why ada is thief").
    # Without it the generic form below bound s='is' and the trail came back "(not present)".
    Rule(
        key="ask.why.yesno",
        lhs=[Pat("?s", "first", "why?"), Pat("why?", "next", "is?"),
             Pat("is?", "next", "?qs"), Pat("?qs", "next", "?qo")],
        nac=[Pat("?qo", "is_kw", "yes")],           # "why is S a O" belongs to the is_a form above
        rhs=[Pat("<query>?", "qtype", "why"), Pat("<query>?", "q_s", "?qs"),
             Pat("<query>?", "q_p", "is"), Pat("<query>?", "q_o", "?qo")],
    ),
    # "why S P O ?"  -> a derivation request (P not the "a" marker; S not the "is" keyword)
    Rule(
        key="ask.why",
        lhs=[Pat("?s", "first", "why?"), Pat("why?", "next", "?qs"),
             Pat("?qs", "next", "?qp"), Pat("?qp", "next", "?qo")],
        nac=[Pat("?qo", "is_kw", "yes"), Pat("?qs", "is_kw", "yes")],
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


def _kw_in_name_slot(graph: Graph, q: str, role: str) -> bool:
    """Is the token bound into name-slot `role` of query `q` a tagged grammar KEYWORD (`is_kw`)?
    A form that binds a keyword where a NAME belongs has read grammar as content — a MIS-PARSE,
    e.g. `is a ada thief` binding s='a'. The habitability rule (loud walls): such a reading must
    be REJECTED as unrecognized — never answered — because a confident answer from a mis-parse
    ("no (assumed)" about a subject named 'a') teaches the user a false model of the language.
    Checked on the RECOGNITION graph (the tagging is form-rule structure, no word list here)."""
    for r, o in graph.relations_from(q):
        if graph.has_key(r, role):
            return any(graph.has_key(rel, "is_kw") for rel, _t in graph.relations_from(o))
    return False


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


# Feedback #13: question RECOGNITION is a pure function of the question text (a throwaway graph +
# the STATIC form banks), yet it dominated `ask_goal`'s ~2.8ms fixed per-call floor — a consumer
# running one check-question many times re-recognized the same string every call. Memoized here for
# the default path (no `extra_forms`/`strata` — those vary by caller and KB, so they bypass the memo).
# Values are the recognized query dicts; `_parse_question` returns a fresh COPY per call so a caller
# mutating its result can never poison the memo.
_RECOGNIZED_QUESTIONS: dict[str, dict | None] = {}


def _copy_query(q: dict | None) -> dict | None:
    return None if q is None else ({**q, "roles": dict(q["roles"])} if "roles" in q else dict(q))


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
    normalization, single-word behaviour.

    Memoized on the question text for the static-banks path (feedback #13, see
    `_RECOGNIZED_QUESTIONS`); a call with `extra_forms` or `strata` recognizes fresh every time."""
    if not extra_forms and strata is None:
        if question not in _RECOGNIZED_QUESTIONS:
            _RECOGNIZED_QUESTIONS[question] = _recognize_question(question)
        return _copy_query(_RECOGNIZED_QUESTIONS[question])
    return _recognize_question(question, extra_forms, strata=strata)


def _recognize_question(question: str, extra_forms: list[Rule] = (), *, strata=None) -> dict | None:
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
        # HABITABILITY LINT: a reading that bound a grammar keyword into a NAME slot is a
        # mis-parse — skip it (a cleaner reading from a more specific form may also have fired);
        # if every reading is tainted, the question is UNRECOGNIZED (the loud wall + nearest-forms
        # guidance at intake), never a silent wrong answer.
        if _kw_in_name_slot(tmp, nid, "q_s") or _kw_in_name_slot(tmp, nid, "q_o"):
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


def _materialize_fact(graph: Graph, s, p: str, o) -> None:
    """Assert the domain relation `s p o` into the KB (monotone — the ask-user acquisition path),
    reusing existing same-named nodes or minting them. An endpoint may be a `ById` (Phase 8 C, an
    id-addressed goal materializing onto a specific node); an ambiguous name WARNS before the [0]-pick
    (the shared `chain.resolve_write_node` discipline). Never deletes (§5). Gathered evidence is NEW
    KNOWLEDGE, so it marks its grain for RECONSIDER (an absence assumed before this arrived may now
    be derivable — settled at the next committed ask)."""
    from ..reconsider import mark_dirty
    o_id = resolve_write_node(graph, o, where="ask_goal materialize")
    graph.add_relation(resolve_write_node(graph, s, where="ask_goal materialize"), p, o_id)
    mark_dirty(graph, [(p, graph.name(o_id) or None)])

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


def _warn_name_split_join(graph: Graph, q: dict) -> None:
    """Feedback #8a: a query name that resolves to MULTIPLE genuinely-distinct nodes silently splits a
    rule join. `?p is_a thing and ?p flag yes` derives NOTHING when a graph-builder mentioned `plan`
    twice (`add_node` is fresh-per-call by design — a name is a label, not an identity), scattering the
    two facts across two `plan` nodes. ugm only signalled at WRITE time (`resolve_write_node`'s ambiguity
    warning); a read-only join got no signal — the same silent-does-less theme as #1/#2/#5, on the query
    path. Warn where it BITES: when a goal/query name denotes >1 distinct IDENTITY — not mere coref
    mentions of one entity (`_one_identity`), and counting only real fact entities (`_is_fact_entity`, so
    reified rule/clause vocabulary carrying the name does not inflate the count)."""
    from ..chain import _one_identity, _is_fact_entity
    names = {v for k in ("s", "o") if isinstance((v := q.get(k)), str)}
    names |= {v for v in (q.get("roles") or {}).values() if isinstance(v, str)}
    for nm in names:
        if not nm or nm in EXISTENTIAL_SUBJECTS or nm == WH:
            continue                                     # a wildcard subject/object is not an entity name
        entities = [n for n in graph.nodes_named(nm)
                    if not (graph.is_control(n) or graph.is_inert(n)) and _is_fact_entity(graph, n)]
        if len(entities) > 1 and not _one_identity(graph, entities):
            warnings.warn(
                f"CNL query names '{nm}', which resolves to {len(entities)} distinct nodes; a rule join "
                f"over '{nm}' may silently derive nothing (its facts are split across the copies). Intern "
                f"the name to one node when building the graph, or address the intended node by id.",
                stacklevel=3)


_TUPLE_QTYPES = {"why": "why", "who": "who", "is": "yesno", "yesno": "yesno"}


def _tuple_query(question: tuple, graph: Graph) -> dict:
    """A STRUCTURED goal for `ask_goal`, bypassing the CNL question string: `(qtype, s, p, o)` where
    either endpoint may be a `ById` node pin (feedback #15, ask 2).

    A CNL question addresses its endpoints BY NAME, which cannot reach one of several same-named nodes —
    precisely the case a rule-minted skolem head creates (N firings, N nodes, one literal name). `ById`
    is the sanctioned escape hatch for that (chain/`query_goal` have taken it since Phase 8 C) but the
    question-STRING layer had no way to carry one, so "why THIS node" was unaskable. This is the
    label-less-substrate answer to #15: address the node, rather than teach heads to fabricate
    distinguishing names (which would re-seat identity in the label — see the arc of #8).

    An endpoint may also be a `ByDesc` DEFINITE DESCRIPTION (`ByDesc("c", (("for_step", "s2"),))` — "the
    `c` whose `for_step` is `s2`"), resolved here to the node it denotes. That is the preferred form: it
    identifies a node the way the engine itself does, by its relations, so a nameless minted node is
    addressable without the caller ever handling a raw id.

    Raises `ValueError` (never a silent mis-read) on a malformed tuple, an unknown qtype, or a
    description that is not definite."""
    if len(question) != 4:
        raise ValueError(
            f"a tuple goal is (qtype, s, p, o) — 4 items, got {len(question)}: {question!r}. "
            'e.g. ("why", ById("n14"), "ast_arg", "world")')
    qtype, s, p, o = question
    if qtype not in _TUPLE_QTYPES:
        raise ValueError(f"tuple goal qtype {qtype!r} is not one of {sorted(_TUPLE_QTYPES)}")
    if not isinstance(p, str) or not p:
        raise ValueError(f"tuple goal predicate must be a non-empty name, got {p!r}")
    from ..chain import as_pin
    s, o = as_pin(graph, s), as_pin(graph, o)        # a definite description denotes ONE node
    for slot, v in (("s", s), ("o", o)):
        if not (v is None or isinstance(v, (str, ById))):
            raise ValueError(
                f"tuple goal {slot} must be a name, a ById, a ByDesc, or None — got {v!r}")
        # `why` explains ONE fact, so it needs both endpoints; a free slot would silently explain
        # whichever fact happened to be found first (the very ambiguity #15 is about).
        if qtype == "why" and v is None:
            raise ValueError(
                f"a why-goal must bind both endpoints (it explains one fact); {slot} is None. "
                'Ask `("who", None, p, o)` to enumerate witnesses, then `why` each by ById.')
    return {"qtype": _TUPLE_QTYPES[qtype], "s": s, "p": p, "o": o}


def _witness_answers(graph: Graph, nodes: list[str], pred: str, obj: str) -> list[str]:
    """Render one `who` answer per genuinely-distinct WITNESS, not per witness NAME (feedback #15).

    A rule-minted skolem head (`c?`) mints one node per firing, every one carrying the head's literal
    name, so a name-keyed answer set collapses N built things into ONE line — "the enumeration is
    invisible" half of #15. Names cannot fix this: the substrate is LABEL-LESS on purpose (a name is a
    label, never an identity), so we DISAMBIGUATE THE WAY THE ENGINE ITSELF DOES — by the node's
    defining relations, the same structural identity `chain._find_skolem_witness` uses to re-find a
    skolem. Each ambiguous witness renders with the outgoing facts that its same-named siblings do NOT
    have (`c (for_step s1) is_a ast_call`), which is also exactly the provenance a reader wants: what
    this node was minted FROM.

    Co-named nodes that are ONE coref identity (`_one_identity` — repeated mentions, the ordinary CNL
    case) still render as a single line, so no existing answer changes shape; only a genuine
    name-degenerate split expands."""
    from ..chain import _one_identity
    by_name: dict[str, list[str]] = {}
    for n in nodes:
        by_name.setdefault(graph.name(n), []).append(n)
    out: list[str] = []
    for nm, group in by_name.items():
        if len(group) == 1 or _one_identity(graph, group):
            out.append(f"{nm} {pred} {obj}")
            continue
        facts = {n: _defining_facts(graph, n, skip=(pred, obj)) for n in group}
        for n in group:
            others: set = set()
            for m in group:
                if m != n:
                    others |= facts[m]
            uniq = sorted(facts[n] - others) or sorted(facts[n])
            disc = ", ".join(f"{p} {o}" for p, o in uniq[:2])
            out.append(f"{nm} ({disc}) {pred} {obj}" if disc else f"{nm} {pred} {obj}")
    return sorted(out)


def _defining_facts(graph: Graph, node: str, *, skip: tuple[str, str]) -> set[tuple[str, str]]:
    """The (predicate, object-name) pairs this node stands in — its structural identity, minus the
    relation being asked about (which every witness shares, so it discriminates nothing)."""
    out: set[tuple[str, str]] = set()
    for rel, obj in graph.relations_from(node):
        if graph.is_control(rel) or graph.is_inert(rel):
            continue
        p, o = graph.predicate(rel), graph.name(obj)
        if p and (p, o) != skip:
            out.add((p, o))
    return out


def ask_goal(graph: Graph, question: str, rules: list[Rule], *,
             policy=None, open_preds: frozenset[str] | None = None, ask_user=None,
             extra_forms: list[Rule] = (), strata=None, journal: list | None = None,
             focus_scope: frozenset[str] | None = None, provenance: bool = False,
             on_subgoal=None, commit: bool = True, max_rounds: int = 1000) -> list[str]:
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
    each WEAR THEIR KIND here (the hard-vs-assumed capstone, completed 2026-07-16): `no` / `no
    (assumed)` / `unknown`. The assumed form is exactly the answer RECONSIDER may later take back
    (docs/design/reconsider_design.md); an actor that only needs the decision collapses both `no`s
    with `check.collapse`. (An `ask_user`-testified False stays a plain `no` — user testimony, not
    a CWA default; the forward reader `ask` keeps its simple yes/no contract over materialized ink.)

    ASK-USER (the OWA evidence-gatherer): when a yes/no goal on an OPEN predicate is `unknown` and an
    `ask_user(subj, rel, obj) -> bool | None` handler is given, the engine gathers evidence from it
    (the human-in-the-loop / a tool, §8). `True` MATERIALIZES the fact (monotone, persists) -> `yes`;
    `False` -> `no`; `None` -> stays `unknown`. Only OPEN predicates gather (a CWA-default predicate
    is already decided `no`); this is where the deontic-triggered "better check" escalation will hook.

    Note: reasoning materializes the demanded facts into `graph` (monotone — never deletes; §5). Pass
    `commit=False` for a READ-ONLY query, or a `graph.copy()`. why/n-ary demand-materialize then
    render via `ask`.

    `commit=False` (feedback #12) makes the query READ-ONLY, mirroring `suppose(commit=False)`:
    reasoning runs inside an ephemeral pencil scope (derivations are scope-tagged CONTROL relations —
    the SUPPOSE mechanism, never a `graph.copy()`), the answer is read in-scope, and the scope is
    swept — so a check-query over a persistent graph never mutates what it checks (an earlier query's
    derived conclusion cannot poison the next). Supported for yes/no and who questions; a why-question
    exists to MATERIALIZE the derivation it renders, and an n-ary question renders through the forward
    reader, so both raise under `commit=False` (loud, not silently committing). Two deliberate
    boundaries: an `ask_user`-confirmed fact still inks (user-asserted EVIDENCE is new knowledge, not
    a derivation), and a skolem-minting rule (`<foo>?`) still mints its witness entity node (only
    derived RELATIONS are pencil).

    FIRMWARE v3 (demand-driven NEGATION) — answering is the DEMAND-DRIVEN chain (`check`/`chain_sip`),
    not a forward materialize-then-read. A NAC clause `not L` is decided ON DEMAND by negation-as-failure
    (nested negative demand -> positive closure -> absence decides); NOTHING is completed or retracted for
    a negation. This RETIRES the forward `decide.solve` (aggressive `is_not` completion + INTERPOSE
    defeat): a human decides a negation by ASKING the positive when the question comes up, absence-decides
    — the agent-not-theorem-prover model, restoring locality (only the goal's own closure is materialized)
    for the RIGHT reason (the model), and making fuel-exhaustion an honest `unknown` the forward model
    cannot express. Same yes/no/who answers as the forward path on every stratifiable bank (the step-4
    differential gate); a genuinely NON-stratifiable bank is rejected at LOAD by
    `authoring.lint_stratifiable` (object-aware), so the chain never mis-answers one.

    `max_rounds` is the reasoning BUDGET ("think harder" = a bigger budget, §14 fuel): each demand
    closure runs at most this many saturation rounds, so a chain deeper than the budget can leave the
    positive closure short of fixpoint. That fuel exhaustion surfaces as an honest UNKNOWN ("I did not
    finish looking"), never a confident guess (`check` FUEL → UNKNOWN) — the distinction an exhaustive
    forward model cannot make. Threaded to every `check`/`chain_sip` demand below."""
    from ..check import check, collapse, ASSUMED_NO
    from ..chain import chain_sip, bound_demands, _facts_matching
    from ..policy import DEFAULT_POLICY
    from dataclasses import replace

    # The closed-vs-open reading of absence is the firmware STANCE (`policy.py`), not the engine's.
    # `open_preds=` folds into the default closed-world policy as the OWA exception set (back-compat).
    policy_ = policy if policy is not None else DEFAULT_POLICY
    if open_preds is not None:
        policy_ = replace(policy_, open_preds=frozenset(open_preds))

    q = _tuple_query(question, graph) if isinstance(question, tuple) else \
        _parse_question(question, extra_forms, strata=strata)
    if q is None or q.get("qtype") is None:
        return ["(no question form recognized this)"]
    _warn_case_folded_mismatch(graph, q)             # feedback #3: no silent case-fold false negative
    _warn_name_split_join(graph, q)                  # feedback #8a: no silent name-split join (read side)

    if commit:                                       # RECONSIDER (docs/design/reconsider_design.md, D1):
        from ..reconsider import reconsider          # settle marked assumption-staleness BEFORE answering
        reconsider(graph, rules, policy=policy_,     # (zero-cost when nothing was marked; commit=False
                    focus_scope=focus_scope)         # keeps its no-mutation promise and may see stale ink)

    def concept_key(p: str, o: str | None) -> str:
        # Openness is a property of the CONCEPT: for a copula query (`is S C`) it is the object
        # concept C (`C is open world`), not the shared copula; for a relational query it is R.
        return o if (p == COPULA and o is not None) else p

    rule_g = _reify_rules(rules)

    # feedback #12: READ-ONLY mode reasons in an ephemeral pencil scope (the SUPPOSE mechanism —
    # derivations are scope-tagged control, swept in the finally below; ink is never touched).
    if not commit and q["qtype"] not in ("yesno", "who"):
        raise ValueError(
            f"ask_goal(commit=False) supports yes/no and who questions, not {q['qtype']!r}: a "
            "why-question exists to materialize the derivation (provenance) it renders, and an n-ary "
            "question renders through the forward reader. Query a graph.copy() for those.")
    scope = graph.add_node("<query>", control=True) if not commit else None
    # READ-ONLY + BANDED: snapshot fork scopes so the finally can sweep the ones this query DERIVES
    # (the fork-leak fix — mirrors `query_goal`; see the note there).
    pre_forks = None
    if scope is not None and policy_.banded:
        from ..possibility import LIKELINESS
        pre_forks = set(graph.nodes_with_key(LIKELINESS))

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

        def as_name(x):
            # A demand endpoint is a NAME, or (id-addressed core, Stage 3) a node id when a free var was
            # bound to a node — the ask is a USER boundary, which speaks names, so resolve id -> name.
            # This also DEDUPS the id/name forms of one premise (e.g. `n49 is funded` == `bo is funded`).
            return graph.name(x) if x is not None and graph.has(x) else x

        while True:
            chain_sip(graph, goal, provenance=provenance, focus_scope=focus_scope, rules=rule_g,
                      scope=scope, policy=policy_, max_rounds=max_rounds)
            if _facts_matching(graph, goal[0], goal[1], goal[2], focus_scope=focus_scope, scope=scope):
                return materialized                            # goal now derivable — done gathering
            frontier = {(p, as_name(s), as_name(o)) for (p, s, o) in bound_demands(rule_g)
                        if s is not None and o is not None and (p, as_name(s), as_name(o)) != goal
                        and (p, as_name(s), as_name(o)) not in asked and not is_neg_pred(p)
                        and policy_.is_open(concept_key(p, o))
                        and not _facts_matching(graph, p, s, o, focus_scope=focus_scope, scope=scope)}
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

    def ep_name(x) -> str:
        # A scope-aware read returns a free slot as a `ById` pin — render it by its node's name.
        return graph.name(x.node_id) if isinstance(x, ById) else x

    try:
        if q["qtype"] == "yesno":
            if q["s"] in EXISTENTIAL_SUBJECTS:
                # `is anyone happy` is ∃ — demand the WILDCARD-subject goal, then match any witness.
                chain_sip(graph, (q["p"], None, q["o"]), provenance=provenance, focus_scope=focus_scope,
                          rules=rule_g, scope=scope, on_subgoal=on_subgoal, policy=policy_,
                          max_rounds=max_rounds)
                if policy_.banded:
                    # BANDED ∃ (the possibilistic fold): the verdict is the BEST witness's band —
                    # a certain witness is `yes`, a fork-only one answers with its band word.
                    from ..possibility import band_word
                    p = max((b for _s, _o, b, _e in
                             _facts_matching(graph, q["p"], None, q["o"], scope=scope,
                                             focus_scope=focus_scope, bands=True)), default=0.0)
                    if p >= 1.0:
                        return ["yes"]
                    if p > 0.0:
                        return [band_word(p)]
                else:
                    found = (_facts_matching(graph, q["p"], None, q["o"], scope=scope,
                                             focus_scope=focus_scope) if scope is not None
                             else match(graph, [Pat("?w", q["p"], q["o"])]))
                    if found:
                        return ["yes"]
                if policy_.is_open(concept_key(q["p"], q["o"])):
                    return ["unknown"]
                return ["no (assumed)"]                    # ∃-failure is always the CWA default
            # a bound goal: the demand-driven 4-status CHECK, and the verdict WEARS ITS KIND (the
            # capstone's surfacing half, completed for the crisp stance 2026-07-16): an ASSUMED_NO
            # answers `no (assumed)` — the CWA default, out in the open, the "no" that RECONSIDER
            # may later take back — while an ENTAILED_NEG stays a plain hard `no` (as trustworthy
            # as a yes). Actors that only need the decision use `check.collapse` (both are no).
            def verdict(status: str) -> str:
                if status == ASSUMED_NO:
                    return "no (assumed)"
                return collapse(status)
            goal = (q["p"], q["s"], q["o"])
            v = verdict(check(graph, goal, policy=policy_, provenance=provenance,
                              focus_scope=focus_scope, rules=rule_g, scope=scope,
                              on_subgoal=on_subgoal, max_rounds=max_rounds))
            # MID-CHAIN gather (§8.5b): only when the goal was NOT derivable — ask for the OPEN premises the
            # derivation demands, materialize the confirmed ones, and re-decide (so a rule blocked solely by a
            # gatherable fact fires instead of being wrongly assumed-no). A derivable goal pays no extra work.
            if v != "yes" and ask_user is not None and gather_open_premises(goal):
                v = verdict(check(graph, goal, policy=policy_, provenance=provenance,
                                  focus_scope=focus_scope, rules=rule_g, scope=scope,
                                  max_rounds=max_rounds))
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
            chain_sip(graph, (q["p"], None, q["o"]), # wildcard-subject goal
                      provenance=provenance, focus_scope=focus_scope, rules=rule_g, scope=scope,
                      on_subgoal=on_subgoal, policy=policy_, max_rounds=max_rounds)
            if policy_.banded:
                # BANDED who (the possibilistic fold): each witness answers at its BEST band —
                # a certain witness reads as today, a fork-only one wears its band word
                # (`cy is thief (likely)`). Max-of-min over derivations, per witness.
                from ..possibility import band_word
                best: dict[str, float] = {}
                for s, _o, b, _e in _facts_matching(graph, q["p"], None, q["o"], scope=scope,
                                                    focus_scope=focus_scope, bands=True):
                    n = ep_name(s)
                    if b > best.get(n, 0.0):
                        best[n] = b
                if best:
                    return [f"{n} {q['p']} {q['o']}" + ("" if b >= 1.0 else f" ({band_word(b)})")
                            for n, b in sorted(best.items())]
                return ["unknown"] if policy_.is_open(concept_key(q["p"], q["o"])) else ["(no answer)"]
            # Witness NODES, not witness names: same-named-but-distinct nodes (a rule-minted skolem
            # head) each get their own answer, disambiguated structurally (feedback #15).
            if scope is not None:                     # read-only: answer from ink + this scope's pencil
                wit = [s for s, _o in _facts_matching(
                    graph, q["p"], None, q["o"], scope=scope, focus_scope=focus_scope)]
                nodes = [w.node_id for w in wit if isinstance(w, ById)]
                loose = sorted({w for w in wit if not isinstance(w, ById)})   # name-only reads
            else:
                nodes = [b["?x"] for b in match(graph, [Pat("?x", q["p"], q["o"])])]
                loose = []
            answers = _witness_answers(graph, list(dict.fromkeys(nodes)), q["p"], q["o"])
            answers += [f"{n} {q['p']} {q['o']}" for n in loose]
            if answers:
                return sorted(set(answers))
            return ["unknown"] if policy_.is_open(concept_key(q["p"], q["o"])) else ["(no answer)"]

        if q["qtype"] == "why":
            # demand the goal WITH provenance (RECORD, mode 9) so the in-graph support is present, then
            # render the derivation trace via the existing reader. `explain` reads the in-graph proves/uses
            # support (not the journal), so an empty journal is enough to pass the reader's guard.
            # POLICY THREADED (2026-07-16): without it a banded session's `why` closed CRISPLY —
            # deriving the θ-gated jump into INK (a stance leak, worse than a cosmetic miss).
            chain_sip(graph, (q["p"], q["s"], q["o"]), provenance=True, focus_scope=focus_scope,
                      rules=rule_g, on_subgoal=on_subgoal, policy=policy_, max_rounds=max_rounds)
            if isinstance(question, tuple):
                # A structured goal has no question string to re-read: render the trace straight from
                # the endpoints (which may be `ById` pins — `explain` addresses those, feedback #15).
                from .surface import explain
                return explain(graph, journal if journal is not None else [], rules,
                               q["s"], q["p"], q["o"])
            return ask(graph, question, journal=journal if journal is not None else [],
                       rules=rules, extra_forms=extra_forms, strata=strata)

        # n-ary: demand the event predicate, then render via the reader (event-role reads stay in `ask`).
        if q.get("pred") is not None:
            chain_sip(graph, (q["pred"], None, None), provenance=provenance, focus_scope=focus_scope,
                      rules=rule_g, max_rounds=max_rounds)
        return ask(graph, question, journal=journal, rules=rules, extra_forms=extra_forms, strata=strata)
    finally:
        if scope is not None:                          # sweep the read-only pencil (control-only cut)
            from ..suppose import _drop_scope
            _drop_scope(graph, scope)
        if pre_forks is not None:                      # ... and the derived forks it minted (leak fix)
            from ..possibility import LIKELINESS
            from ..suppose import _drop_scope
            for f in set(graph.nodes_with_key(LIKELINESS)) - pre_forks:
                _drop_scope(graph, f)
