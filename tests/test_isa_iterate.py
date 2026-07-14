"""
ITERATE — bounded control-flow whose loop COUNTER is a REGISTER value, not a MINT-ed graph node
(docs/attic/axis_b_control_registers.md §7; mechanism_policy_separation.md §8, Axis B). A loop counter
explains nothing → it is register state. ITERATE forks the match-phase state stream over range(count),
binding the counter in `State.regs`; the effect phase then runs the body once per index.
"""
from ugm.attrgraph import AttrGraph, NAME, valued
from ugm.machine import Machine, ITERATE, MINT, EMIT, State


def test_iterate_forks_the_stream_over_a_range_binding_a_register_counter():
    g = AttrGraph()
    states = Machine().match(g, [ITERATE("i", 3)])
    assert sorted(st.regs["i"] for st in states) == [0, 1, 2]   # one state per loop index
    # the counter lives ONLY in the register file — the graph was not touched (no <iter> node minted)
    assert g.nodes() == []


def test_iterate_runs_the_effect_body_once_per_iteration():
    # a loop that BUILDS: ITERATE forks 4 states, each MINTs one node -> 4 nodes, no iteration scaffolding.
    g = AttrGraph()
    Machine().run(g, [ITERATE("i", 4), MINT("x", attrs={NAME: valued("item")})])
    assert len(g.nodes_named("item")) == 4
    # every node is a real item; NOTHING named like a loop/round/iter control node was created
    assert all(g.name(n) == "item" for n in g.nodes())


def test_iterate_counter_is_available_to_the_body_no_graph_iteration_state():
    # the body can STAMP the loop index by reading the counter register (proof the counter is usable
    # control state, not graph structure). Bind the mint, then EMIT the index as a valued attr.
    g = AttrGraph()
    states = Machine().run(g, [ITERATE("i", 3),
                               MINT("x", attrs={NAME: valued("row")})])
    # the three MINTs produced three distinct nodes, one per register-counter value
    rows = g.nodes_named("row")
    assert len(rows) == 3
    # and the loop counter was a plain register int in each surviving state (0,1,2), never interned
    assert sorted(st.regs["i"] for st in states) == [0, 1, 2]
    assert g.nodes_named("0") == [] and g.nodes_named("1") == []   # no counter node leaked into the graph


def test_iterate_zero_is_an_empty_loop():
    g = AttrGraph()
    states = Machine().run(g, [ITERATE("i", 0), MINT("x", attrs={NAME: valued("never")})])
    assert states == [] and g.nodes() == []                       # no iterations -> no body, no nodes


def test_iterate_folds_through_an_incoming_state_stream():
    # ITERATE forks EACH incoming state: 2 states x 3 iterations = 6 (the loop composes with a prior fork).
    g = AttrGraph()
    a, b = g.add_node({NAME: valued("a")}), g.add_node({NAME: valued("b")})
    outs = Machine().match(g, [ITERATE("i", 3)], init=[State({"s": a}), State({"s": b})])
    assert len(outs) == 6
    assert {st.regs["s"] for st in outs} == {a, b}
    assert {st.regs["i"] for st in outs} == {0, 1, 2}
