"""
Brick #4-slice (docs/isa_control_machine.md §9.4): the `<call>` dispatcher AS A CONTROL-MACHINE PROGRAM,
including the piece the flat `service_calls` loop cannot express — an ASYNC tool that SUSPENDs to the host
and RESUMEs with the answer (the streaming suspend/resume the intake design wants). Sync tools run inline
(a PRIM); async tools are a SUSPEND return/resume pair. The `<call>` RECORD stays a graph node; only the
return/resume MECHANICS became control instructions.
"""
from ugm import (
    AttrGraph, AsyncTool, emit_call, call_arg, pending_calls, service_calls, service_calls_cm,
)
from ugm.machine import ControlMachine, Continuation


def _has(g: AttrGraph, s: str, p: str, o: str) -> bool:
    for a in g.nodes_named(s):
        for rel, obj in g.relations_from(a):
            if g.has_key(rel, p) and g.name(obj) == o:
                return True
    return False


# --- a SYNC tool and an ASYNC tool ------------------------------------------

def _echo(g, call_id):                                  # sync: writes `x -[saw]-> echoed`
    x = call_arg(g, call_id, "x")
    n = g.add_node("echoed")
    r = g.add_relation(x, "saw", n)
    return {n, r}


# an async "weather" tool: request = the city name to look up; fold = write `city -[weather]-> answer`.
def _weather_request(g, call_id):
    return g.name(call_arg(g, call_id, "city"))

def _weather_fold(g, call_id, response):
    city = call_arg(g, call_id, "city")
    temp = g.add_node(str(response))
    rel = g.add_relation(city, "weather", temp)
    return {temp, rel}

WEATHER = AsyncTool(_weather_request, _weather_fold)


# --- sync path: the control-machine dispatcher matches the flat service_calls ---

def test_service_calls_cm_sync_matches_service_calls():
    g1 = AttrGraph(); a1 = g1.add_node("a"); emit_call(g1, "echo", {"x": a1})
    service_calls(g1, {"echo": _echo})                  # the flat loop (the oracle)

    g2 = AttrGraph(); a2 = g2.add_node("a"); emit_call(g2, "echo", {"x": a2})
    touched = service_calls_cm(g2, {"echo": _echo})     # the control-machine dispatcher

    assert _has(g1, "a", "saw", "echoed") and _has(g2, "a", "saw", "echoed")   # same effect
    assert not pending_calls(g1) and not pending_calls(g2)                      # both consumed
    assert touched                                                             # touched ids reported


# --- async path: SUSPEND to the host, RESUME with the answer -----------------

def test_async_tool_suspends_and_resumes_end_to_end():
    g = AttrGraph()
    g.add_node("paris")
    emit_call(g, "weather", {"city": g.nodes_named("paris")[0]})
    answers = {"paris": "18C"}
    touched = service_calls_cm(g, {}, {"weather": WEATHER},
                               answer=lambda req: answers[req[2]])   # req = (tool, call_id, payload)
    assert _has(g, "paris", "weather", "18C")            # the async answer was folded in
    assert not pending_calls(g)                          # the call was consumed after folding
    assert touched


def test_async_dispatch_suspends_to_the_caller_for_streaming():
    # answer OMITTED -> the dispatcher returns a Continuation on the first async call, so the CALLER owns
    # the wait (the true streaming boundary): do other work, then resume with the answer.
    g = AttrGraph()
    g.add_node("cairo")
    emit_call(g, "weather", {"city": g.nodes_named("cairo")[0]})

    cont = service_calls_cm(g, {}, {"weather": WEATHER})
    assert isinstance(cont, Continuation)
    tool_name, _call_id, payload = cont.request          # the host sees WHAT is being asked
    assert tool_name == "weather" and payload == "cairo"
    assert not _has(g, "cairo", "weather", "35C")         # nothing folded yet — the machine is paused

    # the host does the "async" wait, then resumes the SAME captured continuation with the answer
    ControlMachine().resume(g, cont, response={"response": "35C"})
    assert _has(g, "cairo", "weather", "35C")
    assert not pending_calls(g)


def test_mixed_sync_and_multiple_async_calls_all_serviced():
    g = AttrGraph()
    for n in ("paris", "cairo", "thing"):
        g.add_node(n)
    emit_call(g, "weather", {"city": g.nodes_named("paris")[0]})
    emit_call(g, "echo", {"x": g.nodes_named("thing")[0]})
    emit_call(g, "weather", {"city": g.nodes_named("cairo")[0]})
    answers = {"paris": "18C", "cairo": "35C"}

    service_calls_cm(g, {"echo": _echo}, {"weather": WEATHER}, answer=lambda req: answers[req[2]])

    assert _has(g, "paris", "weather", "18C")             # both async calls serviced (two suspends)
    assert _has(g, "cairo", "weather", "35C")
    assert _has(g, "thing", "saw", "echoed")              # the sync call too
    assert not pending_calls(g)


def test_async_handler_that_creates_a_call_is_serviced_in_the_same_dispatch():
    # a fold that CREATES a new (sync) call -> the dispatcher's re-scan loop services it too, in one
    # dispatch (the loop is a branch-back, not a one-shot snapshot).
    def _chain_fold(g, call_id, response):
        city = call_arg(g, call_id, "city")
        temp = g.add_node(str(response))
        g.add_relation(city, "weather", temp)
        emit_call(g, "echo", {"x": temp})                 # a downstream sync call
        return {temp}
    chained = AsyncTool(_weather_request, _chain_fold)
    g = AttrGraph()
    g.add_node("paris")
    emit_call(g, "weather", {"city": g.nodes_named("paris")[0]})

    service_calls_cm(g, {"echo": _echo}, {"weather": chained}, answer=lambda req: "18C")
    assert _has(g, "paris", "weather", "18C")
    assert _has(g, "18C", "saw", "echoed")                # the fold's downstream call was serviced too
    assert not pending_calls(g)


def test_no_pending_calls_is_a_noop():
    g = AttrGraph()
    assert service_calls_cm(g, {"echo": _echo}, {"weather": WEATHER},
                            answer=lambda req: "x") == set()
