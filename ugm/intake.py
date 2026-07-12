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
    kind: str                # "answer" | "fact" | "rule" | "focus" | "clarify" | "unrecognized"
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
    kind: str                # "focus"|"clarify"|"question"|"ask"|"answer"|"fact"|"rule"|"unrecognized"
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


def ingest(kb, rules, utterance, *, policy=None, ask_user=None, attention: str = "global",
           on_event=None) -> Outcome:
    """Route ONE CNL `utterance` against the live session KB `kb` (+ accumulated `rules`) by which
    recognition forms fire, and act on it. Returns an `Outcome`. `rules` is mutated in place when the
    utterance adds a rule (so subsequent turns reason with it immediately — Phase 8.6).

    `attention` (EXPOSED so the consuming system picks the reasoning mode, docs/cnl_intake_design.md §3):
      - "global" (default) — reason over the whole KB (behaviour-identical to a bare `ask_goal`).
      - "focus"  — BOUNDED ATTENTION: a question reasons only within the current focus working set (the
        top frame's centers + their closure). Per-utterance cost then tracks the focus, not the accreted
        session, and the coref fan-out is bounded — but off-focus facts are outside attention (a SEMANTIC
        choice, the agent-not-theorem-prover reading), so answers can differ from "global"."""
    from .cnl.query import recognize, ask_goal
    from .cnl.authoring import load_rules, load_facts, _on_cycle
    from .cnl.forms import declared_pronouns, expand_pronouns_text
    from . import focus as focus_mod

    emit = on_event if on_event is not None else (lambda e: None)   # §5 stream; no-op when unwired

    text = utterance.strip()
    if not text:
        emit(Event("unrecognized"))
        return Outcome("unrecognized", utterance)

    # FOCUS — an explicit focus move (`focus on X` / `forget that` / `back to X`), recognized as a FORM
    # (not a string sniff, §D.2). Checked first: these are control-CNL, never facts/questions.
    fop = focus_mod.recognize_focus_op(text)
    if fop is not None and fop[0] is not None:
        focus_mod.apply_focus_op(kb, fop[0], fop[1])
        emit(Event("focus", {"op": fop[0], "target": fop[1]}))
        return Outcome("focus", utterance, focus_op=fop)

    # ANAPHORA (§4): resolve bare pronouns against the focus's salient center BEFORE routing, so
    # "is she cleared?" reasons about the entity in play. The pronoun set and the antecedent are DATA
    # (`declared_pronouns` + focus salience), never engine-baked (§D.3). Runs AFTER the focus-op check so
    # `forget that` is untouched. ASK-VS-GUESS MARGIN (metareasoning, §4): a pronoun with NO antecedent in
    # focus is maximal ambiguity — CLARIFY rather than silently answer about a literal `she`. (Graded
    # recency margins + type/number agreement + descriptive anaphora are 8.4b.)
    prons = declared_pronouns(kb)
    if any(w in prons for w in text.lower().split()):
        ante = focus_mod.salient_center(kb)
        if ante is None:
            emit(Event("clarify"))
            return Outcome("clarify", utterance)
        text = expand_pronouns_text(text, prons, ante)

    # QUESTION — recognition (forms, not a word list) decides; answer demand-driven over the live KB.
    q = recognize(text)
    if q is not None:
        emit(Event("question", {"s": q.get("s"), "p": q.get("p"), "o": q.get("o")}))
        # widen BEFORE answering so bounded attention includes what this question is about.
        focus_mod.widen(kb, _question_entities(q))
        fscope = frozenset(focus_mod.top_centers(kb)) if attention == "focus" else None

        def _ask(s, r, o):                    # bracket the human-in-the-loop gather with an event (§5/§4)
            emit(Event("ask", {"subj": s, "rel": r, "obj": o}))
            return ask_user(s, r, o)
        answer = ask_goal(kb, text, rules, policy=policy,
                          ask_user=(_ask if ask_user is not None else None), focus_scope=fscope)
        emit(Event("answer", {"answer": answer}))
        return Outcome("answer", utterance, answer=answer)

    # RULE — a `HEAD when …` line reflects to executable rule(s); none => not a rule line.
    new_rules = load_rules(text, policy=policy)
    if new_rules:
        rules.extend(new_rules)
        if _on_cycle(policy) == "raise":                     # re-lint per add (firmware STANCE); a
            from .cnl.authoring import lint_stratifiable     # negation cycle rejects here (Phase 8.6:
            lint_stratifiable(rules, source="ingest")        # conflict-lint-as-conversation replaces raise)
        emit(Event("rule", {"added": len(new_rules)}))
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
    emit(Event("fact" if is_fact else "unrecognized"))
    return Outcome("fact", utterance) if is_fact else Outcome("unrecognized", utterance)
