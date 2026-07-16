"""
The intake ACT arm (cnl_intake_design.md §5, wait-set v2 — 2026-07-16): a `goal …` utterance is
recognized like any other (the `form.goal` intake form mints a `<goal>` control node; routing stays
by-what-fired), and the minted goal triggers the forward act loop — KB-declared rules × the caller's
tool registry. Sync `<call>`s run inline (`run_bank(tools=…)`); an ASYNC tool suspends through the
control-machine dispatcher and surfaces as a `"call"` event whose send is the world's response — the
same threadless suspend/resume as `"ask"`, generalized to the tool boundary.
"""
import pytest

import ugm as h
from ugm import AttrGraph, Pat, Rule
from ugm.intake import ingest, converse, Outcome
from ugm.dispatch import AsyncTool, call_arg, pending_calls


# The mini act bank: a landed goal emits a `ping` call about its target. Content-blind on intake's
# side — `target` / `ping` / `pinged` are THIS bank's declared vocabulary, nothing in intake knows them.
EMIT_PING = Rule(key="emit.ping",
                 lhs=[Pat("?g", "target", "?x")],
                 nac=[Pat("?x", "is", "pinged")],
                 rhs=[Pat("<call>?", "tool", "ping"), Pat("<call>?", "subj", "?x")])


def _ping_tool(g, call_id):
    """Sync world boundary: mark the call's subject pinged (copula fact — `ada is pinged`)."""
    subj = call_arg(g, call_id, "subj")
    pinged = g.nodes_named("pinged")
    rel = g.add_relation(subj, "is", pinged[0] if pinged else g.add_node("pinged"))
    return {rel}


def test_goal_utterance_routes_as_goal_and_runs_sync_tools():
    kb, rules = AttrGraph(), [EMIT_PING]
    events = []
    out = ingest(kb, rules, "goal ada is a target", tools={"ping": _ping_tool},
                 on_event=events.append)
    assert out.kind == "goal" and out.acted >= 1
    assert [e.kind for e in events][0] == "goal" and events[-1].kind == "acted"
    # the tool actually acted: ada is pinged, queryable through the ordinary question route
    assert ingest(kb, rules, "is ada pinged", tools={"ping": _ping_tool}).answer == ["yes"]


def test_goal_without_tools_still_lands_and_fires_rules():
    kb, rules = AttrGraph(), [EMIT_PING]
    out = ingest(kb, rules, "goal ada is a target")
    assert out.kind == "goal" and out.acted >= 1      # the emit rule fired …
    assert pending_calls(kb)                          # … and its <call> waits for a registered tool


def test_plain_fact_and_question_routes_are_untouched():
    kb, rules = AttrGraph(), [EMIT_PING]
    assert ingest(kb, rules, "ada is nervous").kind == "fact"
    assert ingest(kb, rules, "is ada nervous").kind == "answer"


def test_async_tool_suspends_through_converse_and_resumes_on_send():
    kb, rules = AttrGraph(), [EMIT_PING]
    ping = AsyncTool(
        request=lambda g, c: ("ping", g.name(call_arg(g, c, "subj"))),   # what the world must answer
        fold=lambda g, c, resp: _ping_tool(g, c) if resp == "pong" else set())
    gen, send = converse(kb, rules, "goal ada is a target", async_tools={"ping": ping}), None
    kinds, outcome = [], None
    try:
        while True:
            ev = gen.send(send)
            send = None
            kinds.append(ev.kind)
            if ev.kind == "call":
                assert ev.data["tool"] == "ping" and ev.data["request"] == ("ping", "ada")
                send = "pong"                          # the world's answer, folded by the tool
    except StopIteration as stop:
        outcome = stop.value
    assert outcome.kind == "goal"
    assert "goal" in kinds and "call" in kinds and kinds[-1] == "acted"
    assert ingest(kb, rules, "is ada pinged").answer == ["yes"]


def test_blocking_ingest_answers_async_calls_via_answer_call():
    kb, rules = AttrGraph(), [EMIT_PING]
    ping = AsyncTool(request=lambda g, c: "what now?",
                     fold=lambda g, c, resp: _ping_tool(g, c) if resp == "pong" else set())
    out = ingest(kb, rules, "goal ada is a target",
                 async_tools={"ping": ping}, answer_call=lambda req: "pong")
    assert out.kind == "goal"
    assert ingest(kb, rules, "is ada pinged").answer == ["yes"]


def test_blocking_ingest_without_answer_call_is_loud():
    ping = AsyncTool(request=lambda g, c: "?", fold=lambda g, c, r: set())
    with pytest.raises(ValueError, match="answer_call"):
        ingest(AttrGraph(), [], "goal ada is a target", async_tools={"ping": ping})


# --- §3 focus-reachability GC: leaving a topic sweeps its cold <goal>/<call> scaffolding --------


def test_forgetting_the_topic_sweeps_its_goal_and_pending_calls():
    kb, rules = AttrGraph(), [EMIT_PING]
    ingest(kb, rules, "goal ada is a target")              # no tools: the <call> stays pending
    assert kb.nodes_named("<goal>") and pending_calls(kb)
    out = ingest(kb, rules, "forget that")                 # narrowing move -> reachability GC
    assert out.kind == "focus"
    assert kb.nodes_named("<goal>") == [] and pending_calls(kb) == []


def test_goal_warm_in_a_lower_frame_survives_dropping_another_topic():
    kb, rules = AttrGraph(), [EMIT_PING]
    ingest(kb, rules, "ada is nervous")                    # ada enters the focus working set
    ingest(kb, rules, "goal ada is a target")
    ingest(kb, rules, "focus on bo")                       # push a NEW topic above ada's
    ingest(kb, rules, "forget that")                       # drop bo's frame — ada's frame is live again
    assert kb.nodes_named("<goal>")                        # ada is warm: her goal survives
    ingest(kb, rules, "forget that")                       # now drop ada's frame too
    assert kb.nodes_named("<goal>") == []                  # cold -> swept
    # the FACT survives the sweep (facts always stay; only control scaffolding goes)
    assert ingest(kb, rules, "is ada nervous").answer == ["yes"]


# --- the stance meta-line: `be cautious` / `be decisive` — the θ dial as CNL --------------------


def test_stance_meta_line_governs_subsequent_turns():
    from ugm.cnl.world import load_world
    kb, rules = load_world("""\
cy is a suspect
cy is unlikely alibied
?p is thief when ?p is a suspect and ?p is not alibied
""")
    # CAUTIOUS first (derives nothing — the refusal leaves no fork behind for later turns)
    out = ingest(kb, rules, "be cautious")
    assert out.kind == "stance"
    assert ingest(kb, rules, "is cy thief").answer == ["no (assumed)"]
    # flip the dial: DECISIVE makes the jump, wearing its doubt
    assert ingest(kb, rules, "be decisive").kind == "stance"
    assert ingest(kb, rules, "is cy thief").answer == ["likely"]
    # an EXPLICIT policy= still wins over the session stance (the caller's override)
    from ugm import FirmwarePolicy
    assert ingest(kb, rules, "is cy thief", policy=FirmwarePolicy()).answer == ["yes"]


def test_be_with_an_undeclared_word_is_not_a_stance():
    out = ingest(AttrGraph(), [], "be silly")
    assert out.kind != "stance"                            # falls through to ordinary routing


def test_read_only_banded_queries_leave_no_derived_forks():
    # the fork-leak fix (docs/possibilistic.md "slice edges"): a commit=False banded run sweeps the
    # DERIVED forks it minted along with its <query> pencils — repeated queries neither accrete
    # forks nor change their own answers.
    from ugm.cnl.world import load_world
    from ugm.possibility import LIKELINESS
    from ugm import FirmwarePolicy, ask_goal, query_goal
    kb, rules = load_world("""\
cy is a suspect
cy is unlikely alibied
?p is thief when ?p is a suspect and ?p is not alibied
""")
    pol = FirmwarePolicy(uncertainty="banded")
    base = len(list(kb.nodes_with_key(LIKELINESS)))        # the AUTHORED fork(s) stay, always
    for _ in range(3):
        assert ask_goal(kb, "is cy thief", rules, policy=pol, commit=False) == ["likely"]
        assert len(list(kb.nodes_with_key(LIKELINESS))) == base
    rows = query_goal(kb, ("is", "cy", "thief"), rules=rules, policy=pol)   # commit=False default
    assert rows and rows[0][3] > 0
    assert len(list(kb.nodes_with_key(LIKELINESS))) == base


# --- §4a habitability: the rejection carries the NEAREST FORMS, computed from the banks ---------


def test_unrecognized_suggests_nearest_forms_from_the_banks():
    out = ingest(AttrGraph(), [], "goal ada winner")       # goal keyword, malformed shape
    assert out.kind == "unrecognized"
    assert "goal … is a …" in out.nearest                  # the form's OWN template, not a canned string
    out2 = ingest(AttrGraph(), [], "is ada")               # question keyword, too few tokens
    assert out2.kind == "unrecognized" and any(t.startswith("is …") for t in out2.nearest)


def test_unrecognized_with_no_keyword_overlap_suggests_nothing():
    out = ingest(AttrGraph(), [], "colorless green ideas")
    assert out.kind == "unrecognized" and out.nearest == []


def test_unrecognized_event_carries_the_suggestions():
    events = []
    ingest(AttrGraph(), [], "goal ada winner", on_event=events.append)
    unrec = [e for e in events if e.kind == "unrecognized"]
    assert unrec and "goal … is a …" in unrec[0].data["nearest"]
