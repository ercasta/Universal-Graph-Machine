"""SIDE-EFFECT REACTIONS — a chosen recovery ACTS (the §C fork of the reactive core, the live-agent loop).

The reflexive stack derives a recovery (`<goal> recovery escalate`, chosen by authority) as an inert FACT.
Declaring the predicate ACTIONABLE (`recovery is actionable`, DATA) turns a materialized action-fact into a
`<call>` to the tool named by the action — which the driver services through the same `Event("call")`
suspend/resume the tool boundary already uses. So a QUESTION whose failure the governor governed can ESCALATE
(ask a human / give up) with nothing but data + rules + the tool boundary — no caller orchestration.

These tests drive the WHOLE stack through the REAL non-blocking `converse` loop (not a hand-driven `fire`):
repeated fuel exhaustion -> flares -> governor abandons -> recovery by authority -> a real serviced `<call>`.
"""
from __future__ import annotations

import pathlib
import warnings

from ugm import AttrGraph, AsyncTool
from ugm.dispatch import call_arg, pending_calls
from ugm.intake import converse, ingest, load_kb
from ugm.cnl.machine_rules import load_machine_rules
from ugm.chain import _facts_matching
from ugm.reactive import (react, declare_reactive, declare_actionable,
                          actionable_preds, emit_action_calls, SIDE_EFFECT_REG)
from ugm.reconsider import mark_dirty

warnings.simplefilter("ignore")
_CORPUS = pathlib.Path(__file__).resolve().parent.parent / "corpus"
_GOV = (_CORPUS / "governor.cnl").read_text(encoding="utf-8")
_RECOVERY = (_CORPUS / "recovery.cnl").read_text(encoding="utf-8")
NHOPS, BUDGET = 12, 6                                    # a 12-hop cascade starved at budget 6; governance fits


def _tools(log):
    """Async recovery tools (the WORLD side): each SUSPENDs and, on the host's answer, records the action."""
    def mk(label):
        return AsyncTool(request=lambda g, c: (label, g.name(call_arg(g, c, "arg"))),
                         fold=lambda g, c, resp: (log.append((label, resp)) or set()))
    return {"escalate": mk("escalate"), "giveup": mk("giveup")}


def _build(authority):
    preds = [chr(ord("a") + i) for i in range(NHOPS)]
    kb, rules = AttrGraph(), []
    kb.add_relation(kb.add_node("x"), "a", kb.add_node("y"))
    for lo, hi in zip(preds, preds[1:]):
        rules += load_machine_rules(f"?x {hi} ?y when ?x {lo} ?y")
    load_kb(kb, rules, _GOV)
    load_kb(kb, rules, _RECOVERY)
    if authority is not None:
        ingest(kb, rules, authority)
    return kb, rules, preds[-1]


def _drive(kb, rules, question, tools, *, turns, human="ok"):
    """Drive `turns` asks of `question` through the REAL `converse` loop, answering any recovery <call>."""
    all_calls = []
    for _ in range(turns):
        gen, send = converse(kb, rules, question, async_tools=tools, max_rounds=BUDGET), None
        try:
            while True:
                ev = gen.send(send); send = None
                if ev.kind == "call":
                    all_calls.append(ev.data["tool"]); send = human
        except StopIteration:
            pass
    return all_calls


def test_a_chosen_recovery_acts_through_a_real_call():
    # The live loop: a never-settling question, asked repeatedly, escalates FOR REAL — the escalate <call>
    # suspends to the host and the host's answer is folded (the recovery acted in the world).
    kb, rules, last = _build("ops more_important_than policy")
    log = []
    calls = _drive(kb, rules, f"does x {last} y", _tools(log), turns=5, human="acknowledged")
    assert "escalate" in calls                           # a real <call> to the chosen recovery action fired
    assert log and log[0] == ("escalate", "acknowledged") # ...and the world side folded the human's answer
    assert _facts_matching(kb, "abandoned", None, "yes")  # the governor did abandon (the trigger)


def test_authority_chooses_which_action_acts():
    # SAME banks, SAME failing question — only the authority fact is reversed. The action that ACTS flips
    # from escalate to giveup, with no code change: authoritativeness composing with the side-effect reaction.
    kb, rules, last = _build("policy more_important_than ops")
    log = []
    calls = _drive(kb, rules, f"does x {last} y", _tools(log), turns=5)
    assert "giveup" in calls and "escalate" not in calls
    assert log[0][0] == "giveup"


def test_the_action_fires_once_not_every_turn():
    # DEDUP / no storm: the action fires on the turn the recovery FRESHLY materializes, then is monotone —
    # later turns re-derive the same recovery (a no-op) and must NOT re-escalate.
    kb, rules, last = _build("ops more_important_than policy")
    log = []
    calls = _drive(kb, rules, f"does x {last} y", _tools(log), turns=6)
    assert calls.count("escalate") == 1                  # exactly one action across many governed failures
    assert len(log) == 1


def test_an_answerable_question_never_acts():
    # Opt-in / zero-cost: with the banks loaded but the question ANSWERABLE (no exhaustion, no flare, no
    # abandonment), nothing is chosen and nothing acts — an ordinary turn pays no side-effect.
    kb, rules, _last = _build("ops more_important_than policy")
    kb.add_relation((kb.nodes_named("x") or [kb.add_node("x")])[0], "settled",
                    (kb.nodes_named("y") or [kb.add_node("y")])[0])
    log = []
    calls = _drive(kb, rules, "does x settled y", _tools(log), turns=3)
    assert calls == [] and log == []
    assert not pending_calls(kb)


def test_actionable_is_opt_in_a_reactive_pred_alone_never_acts():
    # A predicate declared REACTIVE but NOT actionable materializes but never emits a <call>: the world-action
    # boundary is a separate, explicit opt-in (a KB may derive an action fact yet choose not to act on it).
    kb, rules = AttrGraph(), load_machine_rules("?g chose ?a when ?g wants ?a")
    g, a = kb.add_node("goal1"), kb.add_node("act1")
    kb.add_relation(g, "wants", a)
    declare_reactive(kb, "chose")                        # reactive, but NOT actionable
    mark_dirty(kb, [("wants", None)])
    react(kb, rules)
    assert _facts_matching(kb, "chose", None, None)       # it DID materialize (reactive)
    assert actionable_preds(kb) == set()                  # ...but nothing is actionable
    assert emit_action_calls(kb) == [] and not pending_calls(kb)   # ...so no action, no call
    assert not kb.registers.get(SIDE_EFFECT_REG)


def test_emit_action_calls_is_deduped_against_pending():
    # The fact->call bridge is idempotent against an unserviced call: a materialized action with a call
    # already pending for the same (tool, goal) does not re-emit, so an un-answered action does not storm.
    kb = AttrGraph()
    g, esc = kb.add_node("goal:solve:x:y"), kb.add_node("escalate")
    kb.add_relation(g, "recovery", esc)
    declare_actionable(kb, "recovery")
    first = emit_action_calls(kb)
    assert first == [("escalate", g)] and len(pending_calls(kb)) == 1
    assert emit_action_calls(kb) == []                    # already pending -> no duplicate
    assert len(pending_calls(kb)) == 1


def test_the_action_declaration_is_read_as_data():
    # `P is actionable` is ordinary DATA, read like `P is reactive` — a corpus/session declares it in its own
    # text, no Python. (The programmatic `declare_actionable` is only a test/embedding convenience.)
    kb, rules = AttrGraph(), []
    ingest(kb, rules, "recovery is actionable")
    assert "recovery" in actionable_preds(kb)
