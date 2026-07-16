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


# --- the DYNAMIC trip count (axis_b §7 follow-on): `count` as a register NAME -----------------


def test_iterate_dynamic_count_reads_an_int_literal_register():
    # the bound comes from the state's own register file (SET/ITERATE-style int literal content)
    g = AttrGraph()
    outs = Machine().match(g, [ITERATE("i", "n")], init=[State({"n": 3})])
    assert sorted(st.regs["i"] for st in outs) == [0, 1, 2]


def test_iterate_dynamic_count_reads_a_value_node_pointer():
    # a register holding a NODE-POINTER counts by the value-node's carried value — so the bound can
    # come from graph DATA matched earlier in the program (interpretation inside the instruction, §3)
    g = AttrGraph()
    outs = Machine().match(g, [ITERATE("i", "n")], init=[State({"n": g.value_node(2)})])
    assert sorted(st.regs["i"] for st in outs) == [0, 1]
    # a numeric STRING value (the CNL-authored shape) counts too
    outs = Machine().match(g, [ITERATE("i", "n")], init=[State({"n": g.value_node("2")})])
    assert sorted(st.regs["i"] for st in outs) == [0, 1]


def test_iterate_dynamic_count_is_per_state():
    # each incoming state resolves its OWN bound: n=2 and n=3 fork to 2+3=5 successors
    g = AttrGraph()
    outs = Machine().match(g, [ITERATE("i", "n")], init=[State({"n": 2}), State({"n": 3})])
    assert len(outs) == 5
    assert sorted(st.regs["i"] for st in outs if st.regs["n"] == 2) == [0, 1]
    assert sorted(st.regs["i"] for st in outs if st.regs["n"] == 3) == [0, 1, 2]


def test_iterate_dynamic_count_non_numeric_is_loud_never_a_silent_empty_loop():
    import pytest
    from ugm.machine import ProgramError
    g = AttrGraph()
    entity = g.add_node({NAME: valued("ada")})            # an ENTITY node carries no operand value
    with pytest.raises(ProgramError, match="not a number"):
        Machine().match(g, [ITERATE("i", "n")], init=[State({"n": entity})])
    with pytest.raises(ProgramError, match="fractional"):  # refuses to truncate, never rounds
        Machine().match(g, [ITERATE("i", "n")], init=[State({"n": g.value_node(2.5)})])
    with pytest.raises(ProgramError, match="unbound"):     # unbound register = program bug, loud
        Machine().match(g, [ITERATE("i", "n")], init=[State({})])
