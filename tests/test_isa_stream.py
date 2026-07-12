"""Phase 8.5a/8.5b — live event streaming (`ingest`) + generator suspend/resume (`converse`),
docs/cnl_intake_design.md §5."""
from ugm import FirmwarePolicy
from ugm.cnl.authoring import load_corpus
from ugm.intake import ingest, converse


def _drive(gen, verdicts=()):
    """Pump a `converse` generator to completion, recording each Event kind and answering every `"ask"`
    from `verdicts` in order. Returns (kinds, outcome) — the mirror of a non-blocking TUI loop."""
    verdicts, kinds, send = list(verdicts), [], None
    try:
        while True:
            ev = gen.send(send)
            send = None
            kinds.append(ev.kind)
            if ev.kind == "ask":
                send = verdicts.pop(0)
    except StopIteration as stop:
        return kinds, stop.value


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


def test_stream_fact_and_focus():
    kb, rules = load_corpus("")
    ev = []
    ingest(kb, rules, "ada is happy", on_event=ev.append)
    assert ev[-1].kind == "fact"

    ev = []
    ingest(kb, rules, "focus on bo", on_event=ev.append)
    assert [e.kind for e in ev] == ["focus"]


# --- 8.5b: generator-based `converse` — non-blocking suspend/resume -------------------------------

def test_converse_question_then_answer():
    kb, rules = load_corpus(THIEF)
    ingest(kb, rules, "ada is a suspect")
    kinds, out = _drive(converse(kb, rules, "is ada thief"))
    assert kinds == ["question", "answer"]                 # no ask needed -> no suspension
    assert out.answer == ["yes"]


def test_converse_suspends_at_ask_and_resumes_on_send():
    kb, rules = load_corpus("")
    pol = FirmwarePolicy(negation_default="open")          # unknown -> ask, not CWA-no
    # The caller SENDS True at the ask wait-point; the chain resumes and materializes -> yes.
    kinds, out = _drive(converse(kb, rules, "is cellar has mice", policy=pol), verdicts=[True])
    assert kinds == ["question", "ask", "answer"]
    assert out.answer == ["yes"]
    # RESUME is monotone: the acquired fact persists, so a re-ask needs no gather.
    kinds2, out2 = _drive(converse(kb, rules, "is cellar has mice", policy=pol))
    assert kinds2 == ["question", "answer"]
    assert out2.answer == ["yes"]


# --- 8.5b: MID-CHAIN ask — gather OPEN premises a derivation needs, not just the top goal ----------

SAFE = "?x is safe when ?x is cleared"                # 'safe' derived; 'cleared' is a gatherable premise


def test_midchain_asks_open_premise_then_derives():
    kb, rules = load_corpus(SAFE)
    ingest(kb, rules, "bo is a suspect")
    asked = []
    pol = FirmwarePolicy(open_preds=frozenset({"cleared"}))     # 'cleared' open, 'safe' still closed
    out = ingest(kb, rules, "is bo safe", policy=pol,
                 ask_user=lambda s, r, o: (asked.append((s, r, o)) or True))
    assert asked == [("bo", "is", "cleared")]                   # asked the PREMISE, not the goal 'safe'
    assert out.answer == ["yes"]                                # gathered premise -> rule fires


def test_midchain_denied_premise_is_not_derivable():
    kb, rules = load_corpus(SAFE)
    ingest(kb, rules, "bo is a suspect")
    pol = FirmwarePolicy(open_preds=frozenset({"cleared"}))
    out = ingest(kb, rules, "is bo safe", policy=pol, ask_user=lambda s, r, o: False)
    assert out.answer == ["no"]                                 # premise denied -> goal not derivable


def test_midchain_no_ask_when_already_derivable():
    kb, rules = load_corpus(SAFE)
    ingest(kb, rules, "bo is a suspect")
    ingest(kb, rules, "bo is cleared")                          # premise already a fact
    pol = FirmwarePolicy(open_preds=frozenset({"cleared"}))
    asked = []
    out = ingest(kb, rules, "is bo safe", policy=pol,
                 ask_user=lambda s, r, o: (asked.append(1) or True))
    assert out.answer == ["yes"] and asked == []               # derivable -> no gather, no extra ask


def test_midchain_gathers_multiple_premises():
    kb, rules = load_corpus("?x is ok when ?x is cleared and ?x is funded")
    ingest(kb, rules, "bo is a suspect")
    pol = FirmwarePolicy(open_preds=frozenset({"cleared", "funded"}))
    asked = []
    out = ingest(kb, rules, "is bo ok", policy=pol,
                 ask_user=lambda s, r, o: (asked.append((s, r, o)) or True))
    assert set(asked) == {("bo", "is", "cleared"), ("bo", "is", "funded")}
    assert out.answer == ["yes"]


def test_converse_midchain_ask_suspends_per_premise():
    kb, rules = load_corpus(SAFE)
    ingest(kb, rules, "bo is a suspect")
    pol = FirmwarePolicy(open_preds=frozenset({"cleared"}))
    kinds, out = _drive(converse(kb, rules, "is bo safe", policy=pol), verdicts=[True])
    assert kinds == ["question", "ask", "answer"]              # the premise ask is a real suspension point
    assert out.answer == ["yes"]


def test_trace_streams_derivations_before_answer():
    # trace=True surfaces one `derive` event per rule firing, in order, before the answer.
    kb, rules = load_corpus(THIEF)
    ingest(kb, rules, "ada is a suspect")
    ev = []
    out = ingest(kb, rules, "is ada thief", on_event=ev.append, trace=True)
    kinds = [e.kind for e in ev]
    assert kinds == ["question", "derive", "answer"]
    d = ev[kinds.index("derive")].data
    assert d["fact"] == "ada is thief" and d["rule"]      # the firing names its fact and rule
    assert out.answer == ["yes"]


def test_trace_off_is_neutral():
    kb, rules = load_corpus(THIEF)
    ingest(kb, rules, "ada is a suspect")
    ev = []
    ingest(kb, rules, "is ada thief", on_event=ev.append)   # trace defaults off
    assert [e.kind for e in ev] == ["question", "answer"]   # no derive events


def test_converse_trace_interleaves_derivations():
    kb, rules = load_corpus(THIEF)
    ingest(kb, rules, "ada is a suspect")
    kinds, out = _drive(converse(kb, rules, "is ada thief", trace=True))
    assert kinds == ["question", "derive", "answer"]
    assert out.answer == ["yes"]


def test_converse_rule_conflict_yields_and_resumes():
    # A mid-session rule that loops with the theory yields a "rule-conflict" event; the caller decides.
    from ugm.cnl.authoring import load_corpus
    base, new = "?x is q when ?x is not p", "?x is p when ?x is not q"

    kb, rules = load_corpus(base)
    kinds, out = _drive_conflict(converse(kb, rules, new), verdict=False)
    assert "rule-conflict" in kinds and out.added_rules == []      # rejected

    kb, rules = load_corpus(base)
    kinds, out = _drive_conflict(converse(kb, rules, new), verdict=True)
    assert "rule-conflict" in kinds and out.added_rules            # accepted


def _drive_conflict(gen, *, verdict):
    """Pump a `converse` generator, answering a `"rule-conflict"` event with `verdict`."""
    kinds, send = [], None
    try:
        while True:
            ev = gen.send(send)
            send = None
            kinds.append(ev.kind)
            if ev.kind == "rule-conflict":
                send = verdict
    except StopIteration as stop:
        return kinds, stop.value


def test_converse_ask_verdict_no_and_unknown():
    pol = FirmwarePolicy(negation_default="open")
    kb, rules = load_corpus("")
    _, no = _drive(converse(kb, rules, "is cellar has mice", policy=pol), verdicts=[False])
    assert no.answer == ["no"]                             # verdict False -> no, nothing materialized
    kb, rules = load_corpus("")
    _, unk = _drive(converse(kb, rules, "is cellar has mice", policy=pol), verdicts=[None])
    assert unk.answer == ["unknown"]                       # verdict None -> stays unknown
