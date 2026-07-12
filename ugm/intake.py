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
    kind: str                                    # "answer" | "fact" | "rule" | "unrecognized"
    utterance: str
    answer: list[str] | None = None              # QUESTION: the CNL answer(s)
    added_rules: list = field(default_factory=list)   # RULE: the executable rules this utterance added


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


def ingest(kb, rules, utterance, *, policy=None, ask_user=None) -> Outcome:
    """Route ONE CNL `utterance` against the live session KB `kb` (+ accumulated `rules`) by which
    recognition forms fire, and act on it. Returns an `Outcome`. `rules` is mutated in place when the
    utterance adds a rule (so subsequent turns reason with it immediately — Phase 8.6)."""
    from .cnl.query import recognize, ask_goal
    from .cnl.authoring import load_rules, load_facts, _on_cycle
    from .policy import DEFAULT_POLICY

    text = utterance.strip()
    if not text:
        return Outcome("unrecognized", utterance)

    # QUESTION — recognition (forms, not a word list) decides; answer demand-driven over the live KB.
    if recognize(text) is not None:
        answer = ask_goal(kb, text, rules, policy=policy, ask_user=ask_user)
        return Outcome("answer", utterance, answer=answer)

    # RULE — a `HEAD when …` line reflects to executable rule(s); none => not a rule line.
    new_rules = load_rules(text, policy=policy)
    if new_rules:
        rules.extend(new_rules)
        if _on_cycle(policy) == "raise":                     # re-lint per add (firmware STANCE); a
            from .cnl.authoring import lint_stratifiable     # negation cycle rejects here (Phase 8.6:
            lint_stratifiable(rules, source="ingest")        # conflict-lint-as-conversation replaces raise)
        return Outcome("rule", utterance, added_rules=list(new_rules))

    # FACT vs UNRECOGNIZED — recognize into the live KB; a content relation means a fact landed.
    anchors = load_facts(kb, text)
    if anchors and _anchor_has_content_fact(kb, anchors[0]):
        return Outcome("fact", utterance)
    return Outcome("unrecognized", utterance)
