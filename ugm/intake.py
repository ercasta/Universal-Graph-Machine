"""
Phase 8.1 — unified CNL intake (docs/cnl_intake_design.md §1).

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
is Phase 8.2. GOAL/command routing (the plan→act→check trigger) and the focus control-CNL are Phase 8.3.
So the seam is closed at the ENTRY here; the internal question-parse relocation follows.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Outcome:
    """What `ingest` did with one utterance. `kind` is the route recognition selected."""
    kind: str                # "answer" | "fact" | "rule" | "focus" | "unrecognized"
    utterance: str
    answer: list[str] | None = None              # QUESTION: the CNL answer(s)
    added_rules: list = field(default_factory=list)   # RULE: the executable rules this utterance added
    focus_op: tuple | None = None                # FOCUS: the (op, target) move applied


@dataclass
class Event:
    """A live progress event streamed DURING `ingest` (Phase 8.5, docs/cnl_intake_design.md §5) so a TUI
    renders the turn as it happens instead of one final blob. Emitted at step boundaries by which FORMS
    fire — same discipline as routing (no string sniff). An `"ask"` event brackets the human-in-the-loop
    `ask_user` gather, so the TUI can show the prompt (the ask-vs-guess escalation, §4). Per-EMIT reasoning
    trace (reuse the RECORD/`<j:>` substrate) and generator-based suspend/resume are 8.5b."""
    kind: str                # "focus"|"question"|"ask"|"answer"|"fact"|"rule"|"unrecognized"
    data: dict = field(default_factory=dict)


def _anchor_has_content_fact(kb, anchor: str) -> bool:
    """Did recognition give this utterance's token chain a CONTENT relation (a real fact), as opposed
    to only the control `first`/`next` scaffolding of an unrecognized line? Content-blind: a fact is a
    non-control, non-inert relation between the utterance's own (content) token nodes."""
    seen, frontier = set(), [anchor]
    toks: list[str] = []
    while frontier:                                          # walk the first/next token chain
        n = frontier.pop()
        if n in seen:
            continue
        seen.add(n)
        if not (kb.is_control(n) or kb.is_inert(n)):
            toks.append(n)
        for rel, nxt in kb.relations_from(n):
            if kb.has_key(rel, "first") or kb.has_key(rel, "next"):
                frontier.append(nxt)
    tokset = set(toks)
    for t in toks:
        for rel, obj in kb.relations_from(t):
            if kb.is_control(rel) or kb.is_inert(rel):
                continue                                     # scaffolding / provenance, not a fact
            if kb.has_key(rel, "first") or kb.has_key(rel, "next"):
                continue                                     # the token chain itself
            if obj in tokset:                                # a content edge between the line's tokens
                return True
    return False


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


def _answer_with_ask(kb, text, rules, policy, fscope, can_ask):
    """Answer the recognized question. This is a GENERATOR so the ask wait-point can SUSPEND: if the
    chain hits an open-predicate UNKNOWN and `can_ask`, it yields an `Event("ask", …)` and pauses; the
    driver `.send()`s back the verdict (True/False/None), and we RESUME by re-entering `ask_goal` with
    that verdict as a one-shot handler (the graph is the continuation, §5). With `can_ask` false there is
    no handler, so we answer straight (no suspension). Returns the CNL answer list."""
    from .cnl.query import ask_goal
    if not can_ask:
        return ask_goal(kb, text, rules, policy=policy, ask_user=None, focus_scope=fscope)

    def _raise(s, r, o):
        raise _NeedVerdict(s, r, o)
    try:
        return ask_goal(kb, text, rules, policy=policy, ask_user=_raise, focus_scope=fscope)
    except _NeedVerdict as nv:
        verdict = yield Event("ask", {"subj": nv.subj, "rel": nv.rel, "obj": nv.obj})
        return ask_goal(kb, text, rules, policy=policy,
                        ask_user=lambda s, r, o: verdict, focus_scope=fscope)


def _ingest_gen(kb, rules, utterance, *, policy=None, attention="global", can_ask=False):
    """The routing CORE as a generator (§5/8.5b): route ONE CNL `utterance` by which recognition forms
    fire and act on it, YIELDING an `Event` at each step boundary and RETURNING the `Outcome` (via
    `StopIteration.value`). Both `ingest` (blocking) and `converse` (non-blocking) drive this ONE core, so
    routing/streaming discipline lives in a single place. The only wait-point is the ask yield inside
    `_answer_with_ask`; every other yield is fire-and-forget (its sent value is ignored)."""
    from .cnl.query import recognize
    from .cnl.authoring import load_rules, load_facts, _on_cycle
    from . import focus as focus_mod

    text = utterance.strip()
    if not text:
        yield Event("unrecognized")
        return Outcome("unrecognized", utterance)

    # FOCUS — an explicit focus move (`focus on X` / `forget that` / `back to X`), recognized as a FORM
    # (not a string sniff, §D.2). Checked first: these are control-CNL, never facts/questions.
    fop = focus_mod.recognize_focus_op(text)
    if fop is not None and fop[0] is not None:
        focus_mod.apply_focus_op(kb, fop[0], fop[1])
        yield Event("focus", {"op": fop[0], "target": fop[1]})
        return Outcome("focus", utterance, focus_op=fop)

    # ANAPHORA is a BOUNDARY concern, resolved by the external SLM on the NL->CNL side using the exposed
    # discourse state (`focus.top_centers`), NOT here (decision 2026-07-12, `cnl_intake_design.md` §4). The
    # substrate receives already-resolved CNL and never sees a pronoun — reasoning is byte-identical whether
    # the CNL says "she" or "ada", so a pronoun resolver bought nothing structural. Intake stays reasoning-
    # facing; NLP stays on the SLM side of the boundary where the vision puts it.

    # QUESTION — recognition (forms, not a word list) decides; answer demand-driven over the live KB.
    q = recognize(text)
    if q is not None:
        yield Event("question", {"s": q.get("s"), "p": q.get("p"), "o": q.get("o")})
        # widen BEFORE answering so bounded attention includes what this question is about.
        focus_mod.widen(kb, _question_entities(q))
        fscope = frozenset(focus_mod.top_centers(kb)) if attention == "focus" else None
        answer = yield from _answer_with_ask(kb, text, rules, policy, fscope, can_ask)
        yield Event("answer", {"answer": answer})
        return Outcome("answer", utterance, answer=answer)

    # RULE — a `HEAD when …` line reflects to executable rule(s); none => not a rule line.
    new_rules = load_rules(text, policy=policy)
    if new_rules:
        rules.extend(new_rules)
        if _on_cycle(policy) == "raise":                     # re-lint per add (firmware STANCE); a
            from .cnl.authoring import lint_stratifiable     # negation cycle rejects here (Phase 8.6:
            lint_stratifiable(rules, source="ingest")        # conflict-lint-as-conversation replaces raise)
        yield Event("rule", {"added": len(new_rules)})
        return Outcome("rule", utterance, added_rules=list(new_rules))

    # FACT vs UNRECOGNIZED — recognize into the live KB; a content relation means a fact landed.
    anchors = load_facts(kb, text)
    anchor = anchors[0] if anchors else None
    is_fact = anchor is not None and _anchor_has_content_fact(kb, anchor)
    if is_fact:
        # IMPLICIT widen (§3): the entities the utterance is about enter the top focus frame. Never a
        # push — a topic switch is explicit. Content-blind subject extraction (`focus.utterance_subjects`).
        focus_mod.widen(kb, focus_mod.utterance_subjects(kb, anchor))
    if anchor is not None:
        focus_mod.gc_utterance_scaffolding(kb, anchor)   # sweep the spent token chain (accretion control)
    yield Event("fact" if is_fact else "unrecognized")
    return Outcome("fact", utterance) if is_fact else Outcome("unrecognized", utterance)


def ingest(kb, rules, utterance, *, policy=None, ask_user=None, attention: str = "global",
           on_event=None) -> Outcome:
    """Route ONE CNL `utterance` against the live session KB `kb` (+ accumulated `rules`) by which
    recognition forms fire, and act on it. Returns an `Outcome`. `rules` is mutated in place when the
    utterance adds a rule (so subsequent turns reason with it immediately — Phase 8.6).

    This is the BLOCKING driver (8.5a): it runs the `_ingest_gen` core to completion, forwarding every
    `Event` to `on_event` and calling `ask_user` synchronously at the ask wait-point (a TUI that can
    block on the prompt). The non-blocking generator driver is `converse` (8.5b).

    `attention` (EXPOSED so the consuming system picks the reasoning mode, docs/cnl_intake_design.md §3):
      - "global" (default) — reason over the whole KB (behaviour-identical to a bare `ask_goal`).
      - "focus"  — BOUNDED ATTENTION: a question reasons only within the current focus working set (the
        top frame's centers + their closure). Per-utterance cost then tracks the focus, not the accreted
        session, and the coref fan-out is bounded — but off-focus facts are outside attention (a SEMANTIC
        choice, the agent-not-theorem-prover reading), so answers can differ from "global"."""
    emit = on_event if on_event is not None else (lambda e: None)   # §5 stream; no-op when unwired
    gen = _ingest_gen(kb, rules, utterance, policy=policy, attention=attention,
                      can_ask=ask_user is not None)
    send_val = None
    try:
        while True:
            ev = gen.send(send_val)
            send_val = None
            emit(ev)                                     # stream every event, "ask" included (brackets §4)
            if ev.kind == "ask":
                send_val = ask_user(ev.data["subj"], ev.data["rel"], ev.data["obj"])
    except StopIteration as stop:
        return stop.value


def converse(kb, rules, utterance, *, policy=None, attention: str = "global"):
    """Non-blocking generator driver (8.5b, docs/cnl_intake_design.md §5): the same routing as `ingest`,
    but as a GENERATOR the caller pumps. It YIELDS an `Event` per step boundary; the caller renders each
    and, for the single `"ask"` event, `.send()`s the human/tool verdict (True/False/None) — every other
    event's send is ignored (send `None` / call `next`). SUSPEND/RESUME is threadless: the ask unwinds the
    chain, and resuming re-enters the demand-driven chain over the graph (the continuation). The final
    `Outcome` is the generator's `StopIteration.value`.

        gen, send = converse(kb, rules, utt), None
        try:
            while True:
                ev = gen.send(send); send = None
                if ev.kind == "ask": send = decide(ev.data)   # else: render(ev)
        except StopIteration as stop:
            outcome = stop.value
    """
    return _ingest_gen(kb, rules, utterance, policy=policy, attention=attention, can_ask=True)
