"""
Phase 8.1 — unified CNL intake (docs/design/cnl_intake_design.md §1).

ONE entry for a CNL utterance in a live agent session: `ingest(kb, rules, utterance)`. What the
utterance IS — an assertion, a rule, a question, or nothing recognized — EMERGES from which recognition
forms fire (the same "no Python classifier — the keywords route it" discipline `load_corpus` already
states), NOT from a caller-side word list. That caller-side question-vs-assert fork was the residual
intent-recognizer the seamlessness goal forbids; `ingest` removes it — a caller just hands over the
utterance and reads the outcome.

ROUTING is by the graph structure recognition produces, never by sniffing the utterance string:
  - a `<query>` / `<qevent>` was recognized      -> QUESTION  -> answer demand-driven
  - a rule fragment (`HEAD when …`) was recognized -> RULE     -> reflect + append + re-lint (Phase 8.6)
  - a content fact relation was produced          -> FACT      -> it is in the KB (monotone)
  - nothing fired                                 -> UNRECOGNIZED (the habitability signal, §4a)

STAGING. This first slice keeps the QUESTION parse on the existing throwaway-graph path (`query.recognize`
/ `ask_goal`), which already ANSWERS over the live KB — only the PARSE is off-graph. Collapsing that parse
into a live control-flagged `<query>` node (so asking, asserting and commanding are literally one motion)
is Phase 8.2 (folded into 8.3: a live `<query>` has no consumer but focus).

GOAL/COMMAND — the ACT arm (2026-07-16, §5 wait-set v2). A `goal …` utterance is recognized like any
other (the `form.goal` intake form mints a `<goal>` control node — routing stays by-what-fired), and the
minted goal TRIGGERS the forward act loop: `run_bank` over the active rules with the caller's TOOL
registry. The KB's own rules decide everything domain-shaped (plan→act→check as declared rules — WHICH
`<call>`s exist, what "done" means); intake only pumps. A sync tool runs inline at each quiescence
(`run_bank(tools=…)`, the existing dispatch); an ASYNC tool suspends through the control-machine
dispatcher (`service_calls_cm`) and surfaces as a `"call"` event whose `.send()` is the world's answer —
the same threadless suspend/resume as `"ask"`, generalized to the tool boundary.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# The goal control token the `form.goal` intake form mints (reserved `<…>` chokepoint, discipline §D.5).
# One definition — `focus.py` owns it (the focus-reachability GC sweeps by it).
from .focus import GOAL  # noqa: E402


@dataclass
class Outcome:
    """What `ingest` did with one utterance. `kind` is the route recognition selected."""
    kind: str                # "answer"|"fact"|"rule"|"rule-disable"|"focus"|"stance"|"goal"|"form"|"procedure"|"ambiguous"|"unrecognized"
    utterance: str
    answer: list[str] | None = None              # QUESTION: the CNL answer(s)
    added_rules: list = field(default_factory=list)   # RULE: the executable rules this utterance added
    disabled_keys: list = field(default_factory=list) # RULE-DISABLE: the rule keys marked `<disabled>`
    focus_op: tuple | None = None                # FOCUS: the (op, target) move applied
    acted: int | None = None                     # GOAL: forward firings the act loop produced
    nearest: list = field(default_factory=list)  # UNRECOGNIZED: nearest form templates (§4a)


@dataclass
class Event:
    """A live progress event streamed DURING `ingest` (Phase 8.5, docs/design/cnl_intake_design.md §5) so a TUI
    renders the turn as it happens instead of one final blob. Emitted at step boundaries by which FORMS
    fire — same discipline as routing (no string sniff). An `"ask"` event brackets the human-in-the-loop
    `ask_user` gather, so the TUI can show the prompt (the ask-vs-guess escalation, §4). A `"call"` event
    is the ASYNC-TOOL suspension (§5 wait-set v2): its data carries `{tool, call, request}` and the
    driver's `.send()` value is the world's response, folded by the tool's `fold` half."""
    kind: str                # focus|question|ask|subgoal|derive|answer|fact|rule|rule-conflict|rule-disable|form|form-conflict|procedure|goal|call|acted|unrecognized
    data: dict = field(default_factory=dict)


def _stratify_conflict(rules) -> str | None:
    """The negation-cycle detail if `rules` is NOT stratifiable, else None (§6/Phase 8.6). The
    content-blind `authoring.stratify` decides — no relation name is special-cased. Used to turn a
    mid-session rule that loops with the existing theory into a CONVERSATION instead of a raise."""
    from .cnl.authoring import stratify
    try:
        stratify(list(rules))
        return None
    except ValueError as e:
        return str(e)


def _question_entities(q: dict) -> set[str]:
    """The concrete entities a recognized question is ABOUT — its bound SUBJECT (skipping the `who`/
    `someone` unknowns), or an n-ary question's filled roles. These enter the focus so a follow-up
    ('is he cleared?') resolves against them (§4). The OBJECT of a binary question is deliberately
    EXCLUDED: for a copula question it is a TYPE (`is bo thief` -> `thief`), and a shared type in the
    focus scope would act as a stopword-anchor that reconnects everything, defeating bounded attention.
    Mirrors `focus.utterance_subjects` (subjects, not types)."""
    from .cnl.query import EXISTENTIAL_SUBJECTS, WH
    if q.get("qtype") == "nary":
        return {v for v in q.get("roles", {}).values() if v and v != WH}
    s = q.get("s")
    return {s} if (s and s not in EXISTENTIAL_SUBJECTS) else set()


class _NeedVerdict(Exception):
    """Internal suspension signal (§5/8.5b): the demand-driven chain hit an open-predicate UNKNOWN it
    needs a human/tool verdict for. Raised from inside `ask_goal` (via a throwaway `ask_user`), it
    UNWINDS the chain cleanly — a threadless suspend. The graph state persists (monotone, §5-safe), so
    re-entering `ask_goal` with the supplied verdict RESUMES: the demand chain prunes-and-continues."""
    def __init__(self, subj, rel, obj):
        self.subj, self.rel, self.obj = subj, rel, obj


def _j_nodes(kb) -> set[str]:
    """The justification node ids currently in the KB (provenance RECORDs). Snapshotted before/after a
    demand closure to isolate the derivations of ONE question — the per-emit trace (§5/8.5b)."""
    from . import provenance as prov
    return {n for n in kb.nodes() if prov.is_justification(kb.name(n))}


def _derivations_since(kb, before: set[str]) -> list[dict]:
    """One `{rule, fact}` record per derivation the demand chain minted SINCE the `before` snapshot. Reads
    the in-graph proves/uses support the chain wrote under `provenance=True` (`provenance.py`) — an
    OBSERVER of the substrate, not a control-flow hook, so it never perturbs reasoning (the trace renderer
    IS the event stream, §5)."""
    from . import provenance as prov
    from .cnl.surface import render_relation
    out: list[dict] = []
    for j in _j_nodes(kb) - before:
        rule = prov.rule_of_j(kb, j)
        for fact in prov.proven_of(kb, j):
            rendered = render_relation(kb, fact)
            if rendered is not None:
                out.append({"rule": rule, "fact": rendered})
    return out


def _answer_with_ask(kb, text, rules, policy, fscope, can_ask, trace, extra_forms=(), max_rounds=1000):
    """Answer the recognized question. This is a GENERATOR so the ask wait-point can SUSPEND: if the
    chain hits an open-predicate UNKNOWN and `can_ask`, it yields an `Event("ask", …)` and pauses; the
    driver `.send()`s back the verdict (True/False/None), and we RESUME by re-entering `ask_goal` with
    that verdict as a one-shot handler (the graph is the continuation, §5). With `can_ask` false there is
    no handler, so we answer straight (no suspension). When `trace`, the demand chain runs with provenance
    on and each derivation is yielded as an `Event("derive", …)` before the answer (buffered per turn —
    true wall-clock interleaving would need coroutine reasoning, the deferred refinement). Returns the CNL
    answer list.

    ASK is MID-CHAIN capable (§8.5b): `ask_goal` consults the handler not only for the top goal but for
    every OPEN premise the derivation demands. A memoizing handler drives it: it RAISES `_NeedVerdict` on
    each NEW (subj, rel, obj), we yield the ask, record the caller's verdict, and RE-ENTER `ask_goal` —
    which now answers that tuple from the memo and raises on the next unmet premise, converging when the
    closure needs no more evidence (the graph is the continuation, so each re-entry continues the gather)."""
    from .cnl.query import ask_goal
    before = _j_nodes(kb) if trace else set()

    memo: dict = {}                       # (subj, rel, obj) -> verdict, filled as each ask is answered
    subgoals: list = []                   # the demand-side trace: goals/NAF-checks the chain raised

    def handler(s, r, o):
        if (s, r, o) in memo:             # already answered this turn -> reuse, don't re-ask
            return memo[(s, r, o)]
        raise _NeedVerdict(s, r, o)       # a NEW open goal/premise -> suspend for the caller's verdict

    while True:
        try:
            subgoals.clear()              # keep only the FINAL (complete) run's subgoal trace, not the
            answer = ask_goal(kb, text, rules, policy=policy,   # partial pre-gather re-entries
                              max_rounds=max_rounds,            # the "think harder" budget (§14 fuel)
                              ask_user=(handler if can_ask else None),
                              # provenance ALWAYS-ON for committed asks (reconsider D2, ratified
                              # 2026-07-16): RECORD is mode 9, "always on" — and without receipts
                              # there are no assumed-records for revision to key from.
                              focus_scope=fscope, provenance=True,
                              extra_forms=extra_forms,          # session-authored question forms
                              on_subgoal=(subgoals.append if trace else None))
            break
        except _NeedVerdict as nv:
            verdict = yield Event("ask", {"subj": nv.subj, "rel": nv.rel, "obj": nv.obj})
            memo[(nv.subj, nv.rel, nv.obj)] = verdict
    if trace:
        # The demand-side trace (what the machine asked itself) then the provenance-side trace (what it
        # concluded) — the two halves of a demand-driven explanation. Only the "resolve" phase of the
        # NAF checks (depth>=1) is streamed: those are the crux ("looked for X, found nothing -> not X").
        # Collapse the SAME check (a chain may re-enter a subgoal) to one event, in first-seen order;
        # monotone, so a check that is ever found stays found.
        checks: dict = {}
        order: list = []
        for rec in subgoals:
            if rec["phase"] != "resolve" or rec["depth"] < 1:
                continue
            key = (rec["pred"], rec["subj"], rec["obj"])
            if key not in checks:
                checks[key] = dict(rec)
                order.append(key)
            elif rec["found"]:
                checks[key]["found"] = True
        for key in order:
            yield Event("subgoal", checks[key])
        for rec in _derivations_since(kb, before):
            yield Event("derive", rec)
    return answer


def _form_template(form) -> str:
    """A form's SURFACE TEMPLATE, reconstructed from its LHS token chain: a bound literal shows its
    word, a variable shows `…` — e.g. `ask.yesno.is_a` renders "is … a …". Follows the `first`/`next`
    chain; an unanchored form (keyed mid-chain, like `form.then`) starts at the chain's head subject."""
    from .production_rule import is_bound_literal, literal_name
    nxt, start = {}, None
    for p in form.lhs:
        if p.p == "first":
            start = p.o
        elif p.p == "next":
            nxt[p.s] = p.o
    if start is None:                                       # unanchored: the subject nothing points at
        objs = set(nxt.values())
        start = next((s for s in nxt if s not in objs), None)
    words, seen = [], set()
    tok = start
    while tok is not None and tok not in seen:
        seen.add(tok)
        words.append(literal_name(tok) if is_bound_literal(tok) else "…")
        tok = nxt.get(tok)
    return " ".join(words)


def _nearest_forms(text: str, top: int = 3, extra=()) -> list[str]:
    """The habitability signal (§4a): when NOTHING fires, which intake forms came CLOSEST — computed
    from the form banks' OWN bound literals (which of each form's keyword tokens the utterance
    contains), never a hardcoded suggestion table (discipline §D.4). Candidates are the declared
    intake surface: the question forms, the surface `FORM_RULES` (goal/every/then/…), the focus
    control-CNL, and `extra` (the session's authored forms — Phase 9 Slice B: an authored shape
    suggests exactly like a shipped one, structurally). Returns up to `top` surface templates,
    best keyword coverage first."""
    from .production_rule import is_bound_literal, literal_name
    from .cnl.query import QUESTION_FORMS
    from .cnl.forms import FORM_RULES
    from .focus import FOCUS_FORMS
    toks = set(text.lower().split())
    scored: list[tuple[float, str, str]] = []
    for form in (*QUESTION_FORMS, *FORM_RULES, *FOCUS_FORMS, *extra):
        lits = {literal_name(t) for p in form.lhs for t in (p.s, p.o) if is_bound_literal(t)}
        hit = len(lits & toks)
        if not hit:
            continue
        tpl = _form_template(form)
        if len(tpl.split()) < 2:                            # not a renderable surface shape
            continue
        scored.append((hit / len(lits), tpl, form.key))
    scored.sort(key=lambda t: (-t[0], t[2]))
    out: list[str] = []
    for _score, tpl, _key in scored:
        if tpl not in out:
            out.append(tpl)
        if len(out) >= top:
            break
    return out


def _act_loop(kb, active, sync_tools, async_tools, *, provenance=False, max_cycles=100):
    """The ACT arm's pump (§5 wait-set v2): forward-run the `active` rules STRATIFIED (`run_rules` —
    stratified negation, each layer to fixpoint, servicing sync `<call>`s at each layer via the existing
    dispatch), then run the control-machine dispatcher so an ASYNC tool SUSPENDs — yielded up as an
    `Event("call")` whose send is the world's response — and iterate until the graph AND the calls are
    both quiet. Returns the number of productive forward cycles (>=1 when the loop did work).

    Why stratified-and-iterated, not a single `run_bank` (procedures FINDING, docs/design/procedures_design.md
    §Slice-2): the planner gate RACES under one unstratified bank — `ready` fires before a drop-rule clears
    an `unmet`/`waits_for`. And acting mutates the `<now>` state, so the drop-rules and the act-emit (which
    lags `ready` by a stratum) only re-fire on the NEXT whole-bank pass. So we loop `run_rules` to GRAPH
    quiescence (a full pass that derives no new triple — the same convergence `plan.solve` uses), not just to
    a single fixpoint. This makes `_act_loop` a strict superset of the test's in-line `_solve` (stratified
    forward + async `<call>` suspension) — the ONE act driver, UGM-side of the tool boundary.

    CONTENT-BLIND (discipline §D): which `<call>`s exist and what "done" means are KB-declared (plan→act→check
    as rules); this loop only pumps. `max_cycles` is the fuel bound — a KB whose rules never settle (mints
    calls forever / oscillates) terminates honestly instead of spinning."""
    from .cnl.authoring import run_rules
    from .lowering import derived_triples
    from .dispatch import service_calls_cm
    from .machine import ControlMachine, Continuation
    total = 0
    prev = frozenset(derived_triples(kb))       # pre-image, so a no-op goal reports 0 (not a phantom cycle)
    for _ in range(max_cycles):
        run_rules(kb, active, tools=(sync_tools or None), provenance=provenance)
        cur = frozenset(derived_triples(kb))
        moved = cur != prev                     # did this stratified pass derive anything new?
        prev = cur
        if moved:
            total += 1
        if not async_tools:                     # sync-only world: loop the stratified pass to graph quiescence
            if not moved:
                return total
            continue
        res = service_calls_cm(kb, sync_tools, async_tools)
        folded = False
        while isinstance(res, Continuation):    # each async call: suspend to the driver, fold, continue
            folded = True
            name, call_id, payload = res.request
            response = yield Event("call", {"tool": name, "call": call_id, "request": payload})
            res = ControlMachine().resume(kb, res, response={"response": response})
        if not folded and not moved:
            return total                        # a full cycle moved nothing: quiescent
    return total                                # fuel bound reached — stop honestly


def _ingest_gen(kb, rules, utterance, *, policy=None, attention="global", can_ask=False, trace=False,
                sync_tools=None, async_tools=None, max_rounds=1000):
    """The routing CORE as a generator (§5/8.5b): route ONE CNL `utterance` by which recognition forms
    fire and act on it, YIELDING an `Event` at each step boundary and RETURNING the `Outcome` (via
    `StopIteration.value`). Both `ingest` (blocking) and `converse` (non-blocking) drive this ONE core, so
    routing/streaming discipline lives in a single place. The only wait-point is the ask yield inside
    `_answer_with_ask`; every other yield is fire-and-forget (its sent value is ignored)."""
    from .cnl.query import recognize
    from .cnl.authoring import load_rules, load_facts, _on_cycle, anchor_has_content_fact
    from . import focus as focus_mod
    from . import rule_control

    if policy is None:                                    # no explicit stance: the SESSION stance (the
        policy = kb.registers.get("policy")               # `be cautious` register) governs, if set

    def _fresh_conflict(new):
        # None unless ADDING `new` to the ACTIVE theory forms a negation cycle (a fresh trial list, so a
        # rejected rule never touches `rules`; disabled rules are excluded — they neither fire nor cycle).
        # Only the "raise" stance conflict-asks; "degrade" accepts.
        if _on_cycle(policy) != "raise":
            return None
        return _stratify_conflict(rule_control.active_rules(kb, rules) + new)

    text = utterance.strip()
    if not text:
        yield Event("unrecognized")
        return Outcome("unrecognized", utterance)

    # RULE DISABLE — `forget that rule` / `disable that rule` marks the last-authored rule `<disabled>`
    # (additive, no deletion §5). Recognized as a FORM (§D.2) and checked BEFORE the focus forms: it is a
    # MORE SPECIFIC form than the focus `forget that` (the trailing `rule` token disambiguates).
    if rule_control.recognize_rule_op(text) == "disable":
        disabled = rule_control.disable_last(kb)
        if disabled:                                         # a disabled rule's conclusions are up for
            from .reconsider import mark_dirty, rule_grains  # RECONSIDER at the next committed ask
            mark_dirty(kb, rule_grains([r for r in rules if r.key in disabled]))
        yield Event("rule-disable", {"disabled": disabled})
        return Outcome("rule-disable", utterance, disabled_keys=disabled)

    # FOCUS — an explicit focus move (`focus on X` / `forget that` / `back to X`), recognized as a FORM
    # (not a string sniff, §D.2). Checked first: these are control-CNL, never facts/questions.
    fop = focus_mod.recognize_focus_op(text)
    if fop is not None and fop[0] is not None:
        focus_mod.apply_focus_op(kb, fop[0], fop[1])
        yield Event("focus", {"op": fop[0], "target": fop[1]})
        return Outcome("focus", utterance, focus_op=fop)

    # STANCE — a policy meta-line (`be cautious` / `be decisive`): the θ dial as CNL. Sets the
    # SESSION stance register (`kb.registers["policy"]` — execution attitude, the register home);
    # subsequent turns without an explicit `policy=` reason under it. An explicit param still wins
    # (the caller's override). Recognized as a form + declared table (`policy.recognize_stance`).
    from .policy import recognize_stance
    stance = recognize_stance(text)
    if stance is not None:
        kb.registers["policy"] = stance
        yield Event("stance", {"uncertainty": stance.uncertainty, "theta": stance.theta})
        return Outcome("stance", utterance)

    # FORM — a grammar extension (`form KEY : HEAD when BODY`, Phase 9 Slice B,
    # docs/design/form_authoring_design.md §2). Routed by the HEADER form having fired
    # (`parse_form_line` is None otherwise — §D.2, never a string sniff); a fired header with a
    # malformed body raises loudly there, like the rule route's loader. The authored form joins
    # the SESSION GRAMMAR (`kb.registers["forms"]`), consumed at the use sites below and placed
    # by its OWN RHS structure (D3: a `<query>`/`<qevent>` head = question form, else
    # declarative). A key re-declared IDENTICALLY is idempotent (the multi-KB-file model makes
    # that the NORMAL case); a DIFFERENT rule under an existing key is a CONVERSATION, exactly
    # like rule-conflict: accept = the new definition replaces the old, reject = drop it.
    from .cnl import form_authoring
    new_forms = form_authoring.parse_form_line(text)
    if new_forms is not None:
        existing = form_authoring.session_forms(kb)
        try:
            merged = form_authoring.merge_forms(existing, new_forms, source="intake")
        except ValueError as e:
            verdict = yield Event("form-conflict", {"detail": str(e),
                                                    "keys": [r.key for r in new_forms]})
            if not verdict:
                yield Event("form", {"added": 0, "rejected": True})
                return Outcome("form", utterance, added_rules=[])
            replaced = {r.key for r in new_forms}          # accepted: the new definition wins
            merged = [r for r in existing if r.key not in replaced] + new_forms
        kb.registers[form_authoring.FORMS_REGISTER] = merged
        rule_control.mark_last_added(kb, [r.key for r in new_forms])   # 'disable that rule' referent
        yield Event("form", {"added": len(merged) - len(existing),
                             "keys": [r.key for r in new_forms]})
        return Outcome("form", utterance, added_rules=list(new_forms))

    # PROCEDURE — `to NAME : A then B then C` authors a named step sequence (Procedures arc Slice 2,
    # docs/design/procedures_design.md §2). A HEADER route, sibling to `form KEY :` above: the `to … :`
    # header is recognized here (not as a fact-form), so it emits PROCEDURE-SCOPED `step_before` and
    # never races `form.then`'s global `before` in the fact bank (procedure_surface.py). The facts it
    # stages are exactly the stepping bank's vocabulary — running is a separate `<run> proc NAME` route.
    from .cnl import procedure_surface
    defined = procedure_surface.parse_define(text)
    if defined is not None:
        name, steps = defined
        procedure_surface.stage_procedure(kb, name, steps)
        yield Event("procedure", {"name": name, "steps": steps})
        return Outcome("procedure", utterance)

    # PROCEDURE RUN — `run NAME` seeds `<run> proc NAME` (the stepping bank's INVOKE request) and drives
    # the SAME act arm a `goal …` does: a pre-made plan and a synthesized one execute through one gate
    # (§2). Recognized as a keyword-led COMMAND here — before the fact route, which would not know the
    # `run` verb. The act loop is the stratified `_act_loop` (Slice 2); world steps suspend as `call` events.
    invoked = procedure_surface.parse_run(text)
    if invoked is not None:
        procedure_surface.stage_run(kb, invoked)
        yield Event("goal", {"procedure": invoked})
        before_j = _j_nodes(kb) if trace else set()
        acted = yield from _act_loop(kb, rule_control.active_rules(kb, rules),
                                     sync_tools or {}, async_tools or {}, provenance=trace)
        if trace:
            for rec in _derivations_since(kb, before_j):
                yield Event("derive", rec)
        yield Event("acted", {"fired": acted})
        return Outcome("goal", utterance, acted=acted)

    # The session's authored grammar, minus disabled forms — threaded into every recognition
    # site below (question recognition/answering, fact recognition, nearest-forms). With no
    # authored forms these are empty and every path is byte-identical to before (including the
    # question-recognition memo, which the empty extra_forms leaves on its static fast path).
    session_grammar = rule_control.active_rules(kb, form_authoring.session_forms(kb))
    question_forms = [f for f in session_grammar if form_authoring.is_question_form(f)]
    declarative_forms = [f for f in session_grammar if not form_authoring.is_question_form(f)]

    # ANAPHORA is a BOUNDARY concern, resolved by the external SLM on the NL->CNL side using the exposed
    # discourse state (`focus.top_centers`), NOT here (decision 2026-07-12, `cnl_intake_design.md` §4). The
    # substrate receives already-resolved CNL and never sees a pronoun — reasoning is byte-identical whether
    # the CNL says "she" or "ada", so a pronoun resolver bought nothing structural. Intake stays reasoning-
    # facing; NLP stays on the SLM side of the boundary where the vision puts it.

    # QUESTION — recognition (forms, not a word list) decides; answer demand-driven over the live KB.
    q = recognize(text, extra_forms=question_forms)
    if q is not None:
        yield Event("question", {"s": q.get("s"), "p": q.get("p"), "o": q.get("o")})
        # widen BEFORE answering so bounded attention includes what this question is about.
        focus_mod.widen(kb, _question_entities(q))
        fscope = frozenset(focus_mod.top_centers(kb)) if attention == "focus" else None
        active = rule_control.active_rules(kb, rules)     # a `<disabled>` rule neither fires nor decides
        answer = yield from _answer_with_ask(kb, text, active, policy, fscope, can_ask, trace,
                                             extra_forms=question_forms, max_rounds=max_rounds)
        yield Event("answer", {"answer": answer})
        return Outcome("answer", utterance, answer=answer)

    # RULE — a `HEAD when …` line reflects to executable rule(s); none => not a rule line. Parse WITHOUT
    # linting (`lint=False`): runtime authoring owns the stratification check so a mid-session negation
    # cycle becomes a CONVERSATION, not a raise (§6/Phase 8.6).
    new_rules = load_rules(text, policy=policy, lint=False)
    if new_rules:
        conflict = _fresh_conflict(new_rules)
        if conflict is not None:
            # CONFLICT-LINT AS CONVERSATION (§6): the new rule loops with the existing theory. Don't
            # silently drop and don't raise — ASK (via the §5 channel) whether to accept it anyway
            # (run_rules will then degrade the NAF rules) or reject it. A falsey verdict => reject.
            verdict = yield Event("rule-conflict", {"detail": conflict, "added": len(new_rules)})
            if not verdict:
                yield Event("rule", {"added": 0, "rejected": True})
                return Outcome("rule", utterance, added_rules=[])
        rules.extend(new_rules)                              # commit only after the accept decision
        rule_control.mark_last_added(kb, [r.key for r in new_rules])   # 'that rule' referent (§6 disable)
        from .reconsider import mark_dirty, rule_grains     # a new rule may make an assumed absence
        mark_dirty(kb, rule_grains(new_rules))               # derivable — RECONSIDER at the next ask
        yield Event("rule", {"added": len(new_rules)})
        return Outcome("rule", utterance, added_rules=list(new_rules))

    # FACT / GOAL / UNRECOGNIZED — recognize into the live KB. A content relation means a fact landed;
    # a freshly minted `<goal>` node means the GOAL form fired (routing by produced structure, §D.1 —
    # the before/after delta attributes the goal to THIS utterance, no string sniff).
    # THE GRAMMAR FORK (integration step 2). A KB that DECLARES a grammar takes the declarative tail
    # through parse -> interpretation scope instead of `load_facts`, so its facts land on ENTITY
    # nodes reached by `denotes` rather than on the tokens themselves. Routed by a declared
    # register, never by sniffing the utterance (§D.1). Everything above this line — questions,
    # rules, focus, forms, procedures — is untouched and shared by both paths.
    # This fork is TEMPORARY and deliberately duplicative (user decision 2026-07-19): the target is
    # interpretation nodes everywhere, and the duplication buys the freedom to move this path
    # without holding the token-is-entity path green in lockstep.
    from .cnl import grammar_intake
    gbanks = grammar_intake.session_banks(kb)
    if gbanks is not None:
        kind, data = grammar_intake.route(kb, text, gbanks)
        if kind == "ambiguous":
            # AMBIGUOUS IS ITS OWN OUTCOME, not a flavour of unrecognized: "I cannot parse this" and
            # "I parsed it two ways" want different responses, and only the second can become a
            # discriminating question (`can_ask`) — which is where this is headed.
            yield Event("ambiguous", {"spans": data["spans"]})
            return Outcome("ambiguous", utterance, nearest=data["spans"])
        if kind == "unrecognized":
            yield Event("unrecognized", {"nearest": []})
            return Outcome("unrecognized", utterance)
        focus_mod.widen(kb, data["centers"])
        yield Event("fact", {"centers": sorted(data["centers"])})
        return Outcome("fact", utterance)

    goals_before = set(kb.nodes_named(GOAL))
    nodes_before = set(kb.nodes())                   # to attribute this utterance's NEW fact relations
    anchors = load_facts(kb, text, extra_forms=declarative_forms)
    anchor = anchors[0] if anchors else None
    minted_goals = [n for n in kb.nodes_named(GOAL) if n not in goals_before]
    # `since=nodes_before`: only a relation THIS utterance minted counts as a landed fact — an
    # unrecognized line that merely mentions already-related entities must not misroute as one.
    is_fact = anchor is not None and anchor_has_content_fact(kb, anchor, since=nodes_before)
    if is_fact:                                      # a user-asserted fact may make an assumed absence
        from .reconsider import mark_dirty, fact_grain   # derivable — RECONSIDER at the next ask
        mark_dirty(kb, [fact_grain(kb, n) for n in kb.nodes()
                        if n not in nodes_before and kb.predicate(n)
                        and not (kb.is_control(n) or kb.is_inert(n))])
    if is_fact or minted_goals:
        # IMPLICIT widen (§3): the entities the utterance is about enter the top focus frame. Never a
        # push — a topic switch is explicit. Content-blind subject extraction (`focus.utterance_subjects`).
        focus_mod.widen(kb, focus_mod.utterance_subjects(kb, anchor))
    if anchor is not None:
        focus_mod.gc_utterance_scaffolding(kb, anchor)   # sweep the spent token chain (accretion control)
        # (surgical: a token holding the <goal>'s target/type relation survives the sweep)
    if minted_goals:
        # GOAL/COMMAND — the ACT arm: the landed goal triggers the forward act loop (KB-declared
        # plan→act→check rules × the caller's tools). Async tools suspend as "call" events.
        yield Event("goal", {"goals": len(minted_goals)})
        before_j = _j_nodes(kb) if trace else set()
        acted = yield from _act_loop(kb, rule_control.active_rules(kb, rules),
                                     sync_tools or {}, async_tools or {}, provenance=trace)
        if trace:
            for rec in _derivations_since(kb, before_j):
                yield Event("derive", rec)
        yield Event("acted", {"fired": acted})
        return Outcome("goal", utterance, acted=acted)
    if is_fact:
        yield Event("fact")
        return Outcome("fact", utterance)
    # UNRECOGNIZED — the habitability signal (§4a): say what was not understood AND which declared
    # forms came closest, computed from the form banks themselves (no hardcoded suggestion table).
    # Session-authored forms are candidates too — an authored shape suggests like a shipped one.
    nearest = _nearest_forms(text, extra=session_grammar)
    yield Event("unrecognized", {"nearest": nearest})
    return Outcome("unrecognized", utterance, nearest=nearest)


def ingest(kb, rules, utterance, *, policy=None, ask_user=None, on_conflict=None,
           attention: str = "global", on_event=None, trace: bool = False,
           tools=None, async_tools=None, answer_call=None, max_rounds: int = 1000) -> Outcome:
    """Route ONE CNL `utterance` against the live session KB `kb` (+ accumulated `rules`) by which
    recognition forms fire, and act on it. Returns an `Outcome`. `rules` is mutated in place when the
    utterance adds a rule (so subsequent turns reason with it immediately — Phase 8.6).

    This is the BLOCKING driver (8.5a): it runs the `_ingest_gen` core to completion, forwarding every
    `Event` to `on_event` and answering the two wait-points synchronously — `ask_user(subj, rel, obj)`
    at an open-predicate ask (§4), and `on_conflict(detail) -> bool` at a runtime-rule negation cycle
    (§6). Both default to a SAFE non-crashing answer when unwired: no ask handler => `unknown`; no
    conflict handler => REJECT the cycle-forming rule (never silently admit a cycle). The non-blocking
    generator driver is `converse` (8.5b). `trace=True` streams an `Event("derive", {rule, fact})` per
    rule firing (the reasoning trace) before the answer — additive, off by default.

    `max_rounds` is the reasoning BUDGET ("think harder" = a bigger budget, §14 fuel): the demand
    closure answering a question runs at most this many saturation rounds. A chain deeper than the
    budget leaves the closure short of fixpoint, and that shortfall surfaces as an honest `unknown`
    ("I did not finish looking"), never a confident guess — threaded to `ask_goal` (see there).

    `attention` (EXPOSED so the consuming system picks the reasoning mode, docs/design/cnl_intake_design.md §3):
      - "global" (default) — reason over the whole KB (behaviour-identical to a bare `ask_goal`).
      - "focus"  — BOUNDED ATTENTION: a question reasons only within the current focus working set (the
        top frame's centers + their closure). Per-utterance cost then tracks the focus, not the accreted
        session, and the coref fan-out is bounded — but off-focus facts are outside attention (a SEMANTIC
        choice, the agent-not-theorem-prover reading), so answers can differ from "global".

    `tools` / `async_tools` (the ACT arm, §5 wait-set v2): the caller's `<call>` registries
    (`dispatch.Tool` / `dispatch.AsyncTool`), used when a `goal …` utterance triggers the forward act
    loop. Sync tools run inline. An async tool's suspension is answered by `answer_call(request) ->
    response` — required up front when `async_tools` is given (this driver BLOCKS; without a host
    callback an async suspension would have no answer, and folding a silent None would be the
    does-less failure mode). The non-blocking `converse` instead yields the `"call"` event."""
    if async_tools and answer_call is None:
        raise ValueError(
            "ingest(async_tools=...) needs answer_call= (a request -> response host callback): this "
            "driver blocks, so an async tool's suspension must have an answerer. Use converse() to "
            "own the wait yourself.")
    emit = on_event if on_event is not None else (lambda e: None)   # §5 stream; no-op when unwired
    gen = _ingest_gen(kb, rules, utterance, policy=policy, attention=attention,
                      can_ask=ask_user is not None, trace=trace,
                      sync_tools=tools, async_tools=async_tools, max_rounds=max_rounds)
    send_val = None
    try:
        while True:
            ev = gen.send(send_val)
            send_val = None
            emit(ev)                                     # stream every event (ask/rule-conflict included)
            if ev.kind == "ask":
                send_val = ask_user(ev.data["subj"], ev.data["rel"], ev.data["obj"])
            elif ev.kind == "call":                      # async tool boundary: the host answers
                send_val = answer_call(ev.data["request"])
            elif ev.kind in ("rule-conflict", "form-conflict"):   # §6 (+ Phase 9 form keys): no
                # handler => reject the conflicting rule/form, never silently admit/replace
                send_val = on_conflict(ev.data["detail"]) if on_conflict is not None else False
    except StopIteration as stop:
        return stop.value


def load_kb(kb, rules, text, *, policy=None, attention: str = "global",
            on_event=None) -> list[Outcome]:
    """Load a KB FILE: its lines are batched utterances through the ONE intake route, in order
    (Phase 9 Slice B — the multi-KB-file model, docs/design/form_authoring_design.md D2). The
    shipped/base grammar file is just another file loaded this way; a session composes its
    world by loading N of them.

    LOAD ORDER IS SEMANTIC — strictly declare-before-use: a `form …` (or rule, or relation
    declaration) line extends the grammar for every LATER line, and a line using a form that
    arrives later is unrecognized. That is the same contract as a live session (files ARE
    batched utterances); there is no whole-file re-offer fixpoint.

    LOUD WALLS (a file has no conversation partner): an UNRECOGNIZED line raises, naming the
    line and the nearest-forms guidance; a rule/form CONFLICT raises with the conflict detail
    instead of negotiating. Facts land monotonically as lines load, so a raise leaves earlier
    lines standing — the KB is the session; re-loading a fixed file is idempotent for forms
    (key-identity merge) and additive for facts. Blank/`#` lines skipped. Returns the per-line
    `Outcome`s."""
    def _conflict_is_fatal(detail):
        raise ValueError(f"load_kb: conflict — {detail}")
    outcomes: list[Outcome] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out = ingest(kb, rules, s, policy=policy, attention=attention,
                     on_event=on_event, on_conflict=_conflict_is_fatal)
        if out.kind == "unrecognized":
            raise ValueError(
                f"load_kb: unrecognized line '{s}'"
                + (f" — nearest forms: {out.nearest}" if out.nearest else "")
                + ". Load order is declare-before-use: a form/relation this line needs must "
                "be declared on an EARLIER line (or in an earlier-loaded file).")
        outcomes.append(out)
    return outcomes


def converse(kb, rules, utterance, *, policy=None, attention: str = "global", trace: bool = False,
             tools=None, async_tools=None, max_rounds: int = 1000):
    """Non-blocking generator driver (8.5b, docs/design/cnl_intake_design.md §5): the same routing as `ingest`,
    but as a GENERATOR the caller pumps. It YIELDS an `Event` per step boundary; the caller renders each
    and answers the WAIT-POINT events via `.send()`:
      - `"ask"`  — the human/tool verdict (True/False/None) for an open-predicate gather;
      - `"call"` — the world's response to an ASYNC tool's request (`ev.data["request"]`), folded by
        the tool's `fold` half (§5 wait-set v2 — the tool boundary is a suspension, same mechanism).
    Every other event's send is ignored (send `None` / call `next`). SUSPEND/RESUME is threadless: a
    wait-point unwinds cleanly, and resuming re-enters over the graph (the continuation). `trace=True`
    interleaves an `Event("derive", …)` per rule firing before the answer. The final `Outcome` is the
    generator's `StopIteration.value`.

        gen, send = converse(kb, rules, utt, async_tools=my_tools), None
        try:
            while True:
                ev = gen.send(send); send = None
                if ev.kind == "ask":    send = decide(ev.data)
                elif ev.kind == "call": send = do_in_world(ev.data["request"])   # else: render(ev)
        except StopIteration as stop:
            outcome = stop.value
    """
    return _ingest_gen(kb, rules, utterance, policy=policy, attention=attention, can_ask=True,
                       trace=trace, sync_tools=tools, async_tools=async_tools, max_rounds=max_rounds)
