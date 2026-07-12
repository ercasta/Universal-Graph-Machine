"""Phase 8.5a — live event streaming from `ingest` (docs/cnl_intake_design.md §5)."""
from ugm import FirmwarePolicy
from ugm.cnl.authoring import load_corpus
from ugm.intake import ingest


THIEF = """
?x is cleared when ?x is alibied
?x is thief when ?x is a suspect and ?x is not cleared
"""


def test_stream_off_by_default_is_neutral():
    kb, rules = load_corpus(THIEF)
    ingest(kb, rules, "ada is a suspect")
    assert ingest(kb, rules, "is ada thief").answer == ["yes"]     # no on_event: unchanged


def test_stream_question_then_answer():
    kb, rules = load_corpus(THIEF)
    ingest(kb, rules, "ada is a suspect")
    events = []
    out = ingest(kb, rules, "is ada thief", on_event=events.append)
    kinds = [e.kind for e in events]
    assert kinds == ["question", "answer"]
    assert events[-1].data["answer"] == ["yes"] == out.answer


def test_stream_ask_brackets_the_human_gather():
    kb, rules = load_corpus("")
    asked, events = [], []

    def gather(s, r, o):
        asked.append((s, r, o))
        return True                                   # human says yes -> materialize

    pol = FirmwarePolicy(negation_default="open")     # unknown -> gather, not CWA-no
    out = ingest(kb, rules, "is cellar has mice", policy=pol, ask_user=gather, on_event=events.append)
    kinds = [e.kind for e in events]
    assert kinds == ["question", "ask", "answer"]     # the ask is streamed before the answer
    assert asked == [("cellar", "has", "mice")]
    assert out.answer == ["yes"]


def test_stream_fact_and_focus_and_clarify():
    kb, rules = load_corpus("")
    ev = []
    ingest(kb, rules, "ada is happy", on_event=ev.append)
    assert ev[-1].kind == "fact"

    ev = []
    ingest(kb, rules, "focus on bo", on_event=ev.append)
    assert [e.kind for e in ev] == ["focus"]

    kb2, rules2 = load_corpus("")
    ev = []
    ingest(kb2, rules2, "is she happy", on_event=ev.append)   # empty focus -> unresolved pronoun
    assert [e.kind for e in ev] == ["clarify"]
