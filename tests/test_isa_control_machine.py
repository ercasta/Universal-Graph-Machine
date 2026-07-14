"""
The control machine (docs/isa_control_machine.md §9, brick #1) — a PC over an addressable program
of labeled basic blocks, with the primitive control transfers (BRANCH/BRANCH_IF) and a minimal
loop kit on scalar control registers (SETI/DEC). The headline claim: a bounded loop expressed with
these primitives reproduces `ITERATE`'s graph effects EXACTLY (the differential test) — proving the
primitive control layer subsumes the bulk op before subgoals (brick #2) enter the picture.

The seam `ITERATE` could not cross (a loop body that subgoals) is not exercised here — brick #1 is
just the control PATH; this file proves it is faithful to the existing bulk loop first.
"""
from ugm.attrgraph import AttrGraph, NAME, valued
from ugm.machine import (
    Machine, ControlMachine, Block, State,
    ITERATE, MINT, EMIT, SEED, SETI, DEC, FALL, BRANCH, BRANCH_IF, CALL, RET, HALT, PRIM,
    SUSPEND, Continuation,
    ProgramError,
)
from ugm.attrgraph import valued as _valued
from ugm.lowering import derived_triples


def _counted_loop(n: int, body: list) -> list[Block]:
    """A zero-safe (while-style) counted loop over `body`, run `n` times:
        SETI i,n ; L: if i<=0 goto END ; BODY ; DEC i ; goto L ; END: halt
    The top guard makes it a WHILE loop (body runs 0 times when n==0), matching `ITERATE(_, n)`
    which forks `range(n)` (also empty at n==0). Loops compose as a branch-back — the counter is a
    scalar control register, never a graph node (the seam is a Python `for` inside `ITERATE`)."""
    return [
        Block(control=[SETI("i", n)], term=FALL()),                       # init the loop counter
        Block(label="L", term=BRANCH_IF("i", "<=", 0, "END")),           # guard: exit when exhausted
        Block(body=body, control=[DEC("i")], term=BRANCH("L")),          # body; step; branch back
        Block(label="END", term=HALT()),
    ]


def test_primitive_loop_reproduces_iterate_effects():
    # ITERATE version: fork 4 states, MINT one node each.
    g_iter = AttrGraph()
    Machine().run(g_iter, [ITERATE("i", 4), MINT("x", attrs={NAME: valued("item")})])

    # Primitive-control version: the same loop built from PC + SETI/DEC/BRANCH_IF over a basic block.
    g_ctrl = AttrGraph()
    ControlMachine().run(g_ctrl, _counted_loop(4, [MINT("x", attrs={NAME: valued("item")})]))

    # IDENTICAL effects: same node count, same derived triples.
    assert len(g_iter.nodes_named("item")) == 4
    assert len(g_ctrl.nodes_named("item")) == len(g_iter.nodes_named("item"))
    assert derived_triples(g_ctrl) == derived_triples(g_iter)


def test_primitive_loop_reproduces_iterate_on_a_built_relation():
    # A body that MINTs a reified relation `s -[rel]-> o` each iteration -> compare the DERIVED triples.
    body = [
        MINT("s", attrs={NAME: valued("row")}),
        MINT("o", attrs={NAME: valued("cell")}),
        MINT("r", attrs={"has": valued(1.0)}, in_edges=["s"], edges=["o"]),
    ]
    g_iter = AttrGraph()
    Machine().run(g_iter, [ITERATE("i", 3)] + body)
    g_ctrl = AttrGraph()
    ControlMachine().run(g_ctrl, _counted_loop(3, body))
    # both build three fresh (row -[has]-> cell) relations; the triple SETS are identical
    assert derived_triples(g_ctrl) == derived_triples(g_iter)
    assert len(g_ctrl.nodes_named("row")) == 3 and len(g_ctrl.nodes_named("cell")) == 3


def test_zero_trip_loop_matches_iterate_zero():
    # n==0: the top guard skips the body entirely, exactly like ITERATE(_, 0) (an empty fork).
    g_iter = AttrGraph()
    states = Machine().run(g_iter, [ITERATE("i", 0), MINT("x", attrs={NAME: valued("never")})])
    assert states == [] and g_iter.nodes() == []

    g_ctrl = AttrGraph()
    ControlMachine().run(g_ctrl, _counted_loop(0, [MINT("x", attrs={NAME: valued("never")})]))
    assert g_ctrl.nodes() == []                       # the body never ran


def test_seti_dec_are_scalar_control_registers_not_graph_nodes():
    # The loop counter lives in ControlMachine.ctrl — NOT State.regs, NOT a graph node.
    cm = ControlMachine()
    cm.run(AttrGraph(), _counted_loop(5, [MINT("x", attrs={NAME: valued("thing")})]))
    assert cm.ctrl["i"] == 0                          # counted down to zero
    # and nothing named like the counter leaked into the graph
    g = AttrGraph()
    cm.run(g, _counted_loop(3, [MINT("x", attrs={NAME: valued("thing")})]))
    assert g.nodes_named("0") == [] and g.nodes_named("3") == []


def test_branch_if_falls_through_when_condition_false():
    # BRANCH_IF that never fires: fall through both blocks, running each body once.
    g = AttrGraph()
    prog = [
        Block(control=[SETI("i", 0)],
              body=[MINT("x", attrs={NAME: valued("a")})],
              term=BRANCH_IF("i", ">", 0, "SKIP")),   # 0 > 0 is false -> fall through
        Block(body=[MINT("x", attrs={NAME: valued("b")})], term=FALL()),
        Block(label="SKIP", term=HALT()),
    ]
    ControlMachine().run(g, prog)
    assert len(g.nodes_named("a")) == 1 and len(g.nodes_named("b")) == 1


def test_branch_skips_a_block_unconditionally():
    g = AttrGraph()
    prog = [
        Block(body=[MINT("x", attrs={NAME: valued("a")})], term=BRANCH("AFTER")),
        Block(body=[MINT("x", attrs={NAME: valued("skipped")})], term=FALL()),  # jumped over
        Block(label="AFTER", body=[MINT("x", attrs={NAME: valued("c")})], term=HALT()),
    ]
    ControlMachine().run(g, prog)
    assert len(g.nodes_named("a")) == 1 and len(g.nodes_named("c")) == 1
    assert g.nodes_named("skipped") == []


def test_state_stream_threads_across_fall_through_blocks():
    # The value between blocks is a set of states (§10): a SEED in block 0 binds a register the
    # apply-phase of a LATER block reads. Two seeded rows fork the stream; each gets an EMIT.
    g = AttrGraph()
    a = g.add_node({NAME: valued("a")})
    b = g.add_node({NAME: valued("b")})
    prog = [
        Block(body=[SEED("n", NAME, cmp="=", value="a")], term=FALL()),
        Block(body=[EMIT("n", "seen", 1.0)], term=HALT()),
    ]
    ControlMachine().run(g, prog)
    assert g.get_attr(a, "seen") is not None          # the register bound in block 0 survived to block 1
    assert g.get_attr(b, "seen") is None


def test_undefined_branch_target_is_a_loud_error():
    prog = [Block(term=BRANCH("nowhere"))]
    try:
        ControlMachine().run(AttrGraph(), prog)
        assert False, "expected ProgramError for an undefined label"
    except ProgramError as e:
        assert "nowhere" in str(e)


def test_runaway_loop_raises_instead_of_hanging():
    # A loop with no DEC never terminates -> max_steps guard fires (not a hang).
    prog = [
        Block(control=[SETI("i", 1)], term=FALL()),
        Block(label="L", term=BRANCH_IF("i", ">", 0, "L")),   # i never decremented
    ]
    try:
        ControlMachine(max_steps=1000).run(AttrGraph(), prog)
        assert False, "expected ProgramError for a nonterminating loop"
    except ProgramError as e:
        assert "max_steps" in str(e)


# ---------------------------------------------------------------------------
# Brick #2 — CALL / RET + the control stack (subgoals nest via the machine)
# ---------------------------------------------------------------------------

def test_call_runs_a_subroutine_and_returns():
    # A CALL descends into a subroutine that MINTs a fact; RET returns; the caller continues and
    # SEEDs the fact the callee wrote (graph is shared across the call — the subgoal's whole point).
    g = AttrGraph()
    prog = [
        Block(term=CALL("SUB")),                                    # [0] call the subroutine
        Block(body=[SEED("f", NAME, cmp="=", value="fact"),         # [1] return here: read callee's write
                    EMIT("f", "seen_by_caller", 1.0)],
              term=HALT()),
        Block(label="SUB", body=[MINT("x", attrs={NAME: valued("fact")})], term=RET()),
    ]
    ControlMachine().run(g, prog)
    facts = g.nodes_named("fact")
    assert len(facts) == 1                                          # the callee minted exactly one
    assert g.get_attr(facts[0], "seen_by_caller") is not None       # and the caller saw it after RET


def test_call_restores_the_caller_register_window():
    # The callee gets a FRESH window; the caller's bindings survive the call (caller-saved registers).
    g = AttrGraph()
    caller_node = g.add_node({NAME: valued("caller")})
    prog = [
        Block(body=[SEED("c", NAME, cmp="=", value="caller")], term=CALL("SUB")),   # bind ?c, then call
        Block(body=[EMIT("c", "still_bound", 1.0)], term=HALT()),                   # ?c must still be bound
        Block(label="SUB", body=[MINT("x", attrs={NAME: valued("junk")})], term=RET()),
    ]
    ControlMachine().run(g, prog)
    assert g.get_attr(caller_node, "still_bound") is not None       # ?c survived the callee's fresh window


def test_calls_nest_to_depth_three_via_the_stack():
    # A -> B -> C, each mints a marker; all three RET in LIFO order back to the top. Proves the
    # control STACK (not one saved slot) carries arbitrary nesting.
    g = AttrGraph()
    prog = [
        Block(body=[MINT("x", attrs={NAME: valued("A")})], term=CALL("B")),   # [0]
        Block(body=[MINT("x", attrs={NAME: valued("A_after")})], term=HALT()),# [1] top returns here
        Block(label="B", body=[MINT("x", attrs={NAME: valued("B")})], term=CALL("C")),
        Block(body=[MINT("x", attrs={NAME: valued("B_after")})], term=RET()),
        Block(label="C", body=[MINT("x", attrs={NAME: valued("C")})], term=RET()),
    ]
    ControlMachine().run(g, prog)
    for name in ("A", "B", "C", "B_after", "A_after"):
        assert len(g.nodes_named(name)) == 1, f"{name} not minted exactly once"


def test_bounded_recursion_via_the_stack_not_python():
    # A routine REC mints a node then, while its counter > 0, DECs and CALLs ITSELF — recursion
    # carried by the explicit control stack. Depth n=3 -> REC entered 4 times (n..0) -> 4 nodes.
    g = AttrGraph()
    prog = [
        Block(control=[SETI("n", 3)], term=CALL("REC")),            # [0] top-level call, depth 3
        Block(label="DONE", term=HALT()),                           # [1] top returns here
        Block(label="REC", body=[MINT("x", attrs={NAME: valued("frame")})],
              term=BRANCH_IF("n", "<=", 0, "BASE")),                # [2] base case?
        Block(control=[DEC("n")], term=CALL("REC")),                # [3] else recurse with n-1
        Block(term=RET()),                                          # [4] unwind after the recursive call
        Block(label="BASE", term=RET()),                            # [5] base case returns
    ]
    cm = ControlMachine()
    cm.run(g, prog)
    assert len(g.nodes_named("frame")) == 4                         # entered REC 4 times (depth 3 + base)
    assert cm.stack == []                                           # every CALL was matched by a RET


def test_ret_without_call_is_a_loud_error():
    try:
        ControlMachine().run(AttrGraph(), [Block(term=RET())])
        assert False, "expected ProgramError for RET with an empty stack"
    except ProgramError as e:
        assert "empty control stack" in str(e)


def test_unbounded_recursion_hits_the_step_guard():
    # A routine that CALLs itself with no base case -> the step guard fires (not a stack overflow hang).
    prog = [
        Block(term=CALL("REC")),
        Block(label="REC", term=CALL("REC")),   # no RET, no base case
    ]
    try:
        ControlMachine(max_steps=5000).run(AttrGraph(), prog)
        assert False, "expected ProgramError for unbounded recursion"
    except ProgramError as e:
        assert "max_steps" in str(e)


# ---------------------------------------------------------------------------
# PRIM — the upper-level interpreter step (the escape hatch driver ports run on)
# ---------------------------------------------------------------------------

def test_prim_runs_a_callable_and_writes_a_flag_register():
    # A PRIM mints two nodes and reports a flag; the flag lands in a control register.
    def step(g, stream, ctrl):
        g.add_node({NAME: _valued("p")})
        g.add_node({NAME: _valued("p")})
        return stream, 7                                   # flag = 7
    g = AttrGraph()
    cm = ControlMachine()
    cm.run(g, [Block(prim=PRIM(step, out="k"), term=HALT())])
    assert len(g.nodes_named("p")) == 2
    assert cm.ctrl["k"] == 7                               # the PRIM's flag reached the register file


def test_prim_flag_drives_a_branch_if():
    # BRANCH_IF branches on a flag a PRIM computed (control decided by the interpreter step's outcome).
    def probe(g, stream, ctrl):
        return stream, 0                                   # flag says "false"
    g = AttrGraph()
    prog = [
        Block(prim=PRIM(probe, out="hit"),
              body=[], term=BRANCH_IF("hit", ">", 0, "YES")),
        Block(body=[MINT("x", attrs={NAME: _valued("fell_through")})], term=HALT()),
        Block(label="YES", body=[MINT("x", attrs={NAME: _valued("branched")})], term=HALT()),
    ]
    ControlMachine().run(g, prog)
    assert len(g.nodes_named("fell_through")) == 1 and g.nodes_named("branched") == []


def test_prim_fixpoint_branch_back_over_a_changed_flag():
    # The driver-port SHAPE (§9.5, run_bank): a PRIM runs one 'round' (mints a node while work remains,
    # reporting changed=1), and BRANCH_IF loops back until the round reports changed=0. Proves a Python
    # fixpoint driver becomes a branch-back over a PRIM-computed flag — no Python `for`/`while`.
    budget = {"n": 3}

    def one_round(g, stream, ctrl):
        if budget["n"] > 0:
            g.add_node({NAME: _valued("derived")})
            budget["n"] -= 1
            return stream, 1                               # changed -> keep looping
        return stream, 0                                   # quiesced -> exit

    g = AttrGraph()
    prog = [
        Block(label="ROUND", prim=PRIM(one_round, out="changed"),
              term=BRANCH_IF("changed", ">", 0, "ROUND")),
        Block(term=HALT()),
    ]
    ControlMachine().run(g, prog)
    assert len(g.nodes_named("derived")) == 3             # ran exactly to quiescence

def test_prim_block_rejects_a_body():
    def noop(g, stream, ctrl):
        return stream, 0
    prog = [Block(prim=PRIM(noop), body=[MINT("x")], term=HALT())]
    try:
        ControlMachine().run(AttrGraph(), prog)
        assert False, "expected ProgramError for a block with both body and prim"
    except ProgramError as e:
        assert "body OR prim" in str(e)


# ---------------------------------------------------------------------------
# Brick #4 — SUSPEND / RESUME (the continuation for a mid-computation wait)
# ---------------------------------------------------------------------------

def test_suspend_returns_a_continuation_and_resume_continues():
    # A PRIM computes a REQUEST into a register; SUSPEND hands a Continuation to the driver, which folds
    # in a RESPONSE and resumes; the post-suspend block reads the response and acts on it.
    def ask(g, stream, ctrl):
        return stream, "need the answer"                 # the request payload
    def use_answer(g, stream, ctrl):
        g.add_node({NAME: _valued(str(ctrl["answer"]))})  # read the driver's folded-in response
        return stream, 0
    g = AttrGraph()
    prog = [
        Block(prim=PRIM(ask, out="req"), term=SUSPEND(request_reg="req")),   # [0] pause, asking
        Block(prim=PRIM(use_answer), term=HALT()),                           # [1] resume point
    ]
    cm = ControlMachine()
    cont = cm.run(g, prog)
    assert isinstance(cont, Continuation)
    assert cont.request == "need the answer"             # the driver sees what the machine asked for
    assert g.nodes() == []                               # nothing past the suspend has run yet
    result = cm.resume(g, cont, response={"answer": 42})
    assert result == [] or isinstance(result, list)      # HALTed (a state stream)
    assert len(g.nodes_named("42")) == 1                 # the resumed block used the response


def test_suspend_preserves_the_control_stack_across_the_wait():
    # SUSPEND inside a subroutine: the CALL frame must survive the wait, so RET after resume returns to
    # the right caller. Proves the whole control stack is captured, not just the PC.
    def pause(g, stream, ctrl):
        return stream, None
    g = AttrGraph()
    prog = [
        Block(term=CALL("SUB")),                                     # [0] call ...
        Block(body=[MINT("x", attrs={NAME: _valued("after_call")})], term=HALT()),  # [1] returns here
        Block(label="SUB", prim=PRIM(pause), term=SUSPEND()),        # [2] pause mid-subroutine
        Block(body=[MINT("x", attrs={NAME: _valued("after_wait")})], term=RET()),   # [3] resume, then RET
    ]
    cm = ControlMachine()
    cont = cm.run(g, prog)
    assert isinstance(cont, Continuation)
    assert len(cont.stack) == 1                          # the CALL frame was captured in the continuation
    cm.resume(g, cont)
    # both the post-wait subroutine body AND the caller's post-return body ran, in order
    assert len(g.nodes_named("after_wait")) == 1 and len(g.nodes_named("after_call")) == 1


def test_repeated_suspends_stream_through_the_driver():
    # A loop that SUSPENDs each iteration (a streaming ask/act cycle): the driver resumes it N times.
    def ask(g, stream, ctrl):
        return stream, ctrl["i"]
    g = AttrGraph()
    prog = [
        Block(control=[SETI("i", 3)], term=FALL()),
        Block(label="L", prim=PRIM(ask, out="req"), term=SUSPEND(request_reg="req")),
        Block(control=[DEC("i")],
              body=[MINT("x", attrs={NAME: _valued("tick")})],
              term=BRANCH_IF("i", ">", 0, "L")),
        Block(term=HALT()),
    ]
    cm = ControlMachine()
    seen = []
    result = cm.run(g, prog)
    while isinstance(result, Continuation):
        seen.append(result.request)
        result = cm.resume(g, result)
    assert seen == [3, 2, 1]                             # suspended once per iteration, counting down
    assert len(g.nodes_named("tick")) == 3


def test_internal_subgoal_via_suspend_and_a_service_loop():
    # The brick-#3 SHAPE: a work step yields a SUBGOAL request ("close goal G") mid-computation; the
    # driver services it by mutating the shared graph, then resumes. Arbitrary-depth subgoals are the
    # driver's service loop over suspensions — no Python recursion in the solver's control.
    def solve_step(g, stream, ctrl):
        # needs subgoal 'base' closed before it can finish; asks for it
        return stream, ("subgoal", "base")
    def finish(g, stream, ctrl):
        # the subgoal wrote 'base'; now derive the dependent fact
        if g.nodes_named("base"):
            g.add_node({NAME: _valued("dependent")})
        return stream, 0
    g = AttrGraph()
    prog = [
        Block(prim=PRIM(solve_step, out="req"), term=SUSPEND(request_reg="req")),
        Block(prim=PRIM(finish), term=HALT()),
    ]
    cm = ControlMachine()
    result = cm.run(g, prog)
    # the driver services the subgoal request against the SHARED graph, then resumes
    assert isinstance(result, Continuation)
    kind, goal = result.request
    assert kind == "subgoal" and goal == "base"
    g.add_node({NAME: _valued("base")})                 # "closing the subgoal" writes to the shared graph
    cm.resume(g, result)
    assert len(g.nodes_named("dependent")) == 1         # the resumed solver saw the subgoal's result
