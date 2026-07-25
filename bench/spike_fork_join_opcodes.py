"""Spike: is FORK/JOIN an OPCODE delta, or a SCHEDULER CONVENTION over the existing `SUSPEND`?

`docs/design/execution_topology.md` §6 claims the ISA does not change — "a FORK is 'suspend, and keep N
continuations instead of one'" — and §10.5 defers the question to this spike, with the cheapest decisive
experiment named: sibling queues that risk no semantics. §4b then settled what a queue ITEM is: a
`Continuation` tagged with its scope. That makes the question sharp and mechanical:

    HYPOTHESIS (H): the scheduler forks by RESUMING ONE CONTINUATION N TIMES — once per child scope —
    and joins by running the crossing after every child has drained. Zero new terminators.

H rests entirely on a `Continuation` being an immutable VALUE that may be resumed more than once. It is
built to look like one (`machine.py:1229` copies stack, ctrl and stream on capture), and §0.2's sequential
parent-first rule means no two resumptions ever run concurrently — so the only way H fails is if two
SEQUENTIAL resumptions of the same continuation can still see each other's control state.

CASES
  1. fork at TOP LEVEL (empty control stack) — the easy case, and the control for case 2.
  2. fork INSIDE A CALL (non-empty control stack) — the predicted defect. `SUSPEND` captures
     `list(self.stack)`: a SHALLOW copy whose frame tuples `(ret_pc, stream, saved_ctrl)` are SHARED
     across every resumption. `RET` then does `self.ctrl = saved_ctrl` (aliases, does not copy), so a
     later `SETI`/`DEC`/`PRIM` write mutates a dict the sibling will also restore.
  3. the JOIN — children stay isolated from base until one boundary promotes a winner (§4.3).

GO = cases 1 and 3 pass AND case 2's verdict is a CAPTURE-DEPTH bug (fixable in `SUSPEND`, no new
opcodes) rather than a missing control primitive. NO-GO = something about forking needs the machine to
know it is forking, i.e. real `FORK`/`JOIN` terminators.
"""
from __future__ import annotations

import pathlib
import sys
import warnings

warnings.simplefilter("ignore")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ugm.attrgraph import AttrGraph, NAME, valued                          # noqa: E402
from ugm.machine import (                                                  # noqa: E402
    ControlMachine, Block, Continuation, PRIM,
    MINT, SETI, DEC, FALL, CALL, RET, HALT, SUSPEND,
)
from ugm.scope_tree import put_under, scope_of, is_visible                 # noqa: E402

_SCOPE_N = [0]


def _scope(g) -> str:
    """An ordinary, uniquely-named scope node (a queue's identity, §4.1)."""
    _SCOPE_N[0] += 1
    return g.add_node({NAME: valued(f"scope{_SCOPE_N[0]}")})


def _child_work(label: str, seen: list):
    """A PRIM standing in for whatever a child queue does: mint a claim UNDER the scope the scheduler
    handed it, and record the control registers it can SEE on entry (the contamination probe)."""
    def fn(g, stream, ctrl):
        seen.append((label, dict(ctrl)))                  # what this resumption observes
        scope = ctrl["scope"]
        n = g.add_node({NAME: valued(f"claim_{ctrl['who']}")})
        put_under(g, n, scope)                            # writes are SCOPE-LOCAL (§4.2)
        ctrl["mine"] = ctrl["who"]                        # a control write AFTER the fork point
        return stream, 0
    return PRIM(fn=fn)


# ── CASE 1: fork at top level ────────────────────────────────────────────────

def case1_toplevel_fork():
    g = AttrGraph()
    seen: list = []
    prog = [
        Block(body=[MINT("b", attrs={NAME: valued("base_fact")})], term=FALL()),   # parent work
        Block(term=SUSPEND(request_reg="fork")),                                   # THE FORK POINT
        Block(prim=_child_work("top", seen), term=HALT()),                         # the child body
    ]
    cm = ControlMachine()
    cont = cm.run(g, prog)
    assert isinstance(cont, Continuation), "expected the fork point to suspend"

    sA, sB = _scope(g), _scope(g)
    for who, sc in (("A", sA), ("B", sB)):                # FORK = resume the SAME continuation N times
        ControlMachine().resume(g, cont, {"scope": sc, "who": who})

    claims = {scope_of(g, n) for n in g.nodes() if (g.name(n) or "").startswith("claim_")}
    leaked = [regs for _l, regs in seen if "mine" in regs]
    ok = claims == {sA, sB} and not leaked
    print(f"  CASE 1 (top level)   forked-to={len(claims)} scopes  contamination={bool(leaked)}  "
          f"-> {'PASS' if ok else 'FAIL'}")
    return ok, g, (sA, sB)


# ── CASE 2: fork inside a CALL ───────────────────────────────────────────────

def case2_fork_inside_a_call():
    g = AttrGraph()
    seen: list = []
    after: list = []

    def observe(g_, stream, ctrl):
        after.append(dict(ctrl))                          # the CALLER's registers, post-RET
        return stream, 0

    # NOTE the placement of the mutation. A write INSIDE the callee lands in the fresh `dict(cont.ctrl)`
    # that `resume` makes and is then DISCARDED by `RET` (which restores the caller frame) — so it probes
    # nothing. The write must happen in the CALLER, after `RET` has aliased `self.ctrl = saved_ctrl`;
    # only then does it hit the dict the frame tuple holds and that every resumption shares.
    prog = [
        Block(control=[SETI("depth", 7)], term=CALL("SUB")),       # caller: push a frame with its ctrl
        Block(label="AFTER", prim=PRIM(fn=observe),                # observe, THEN mutate the restored
              control=[DEC("depth")], term=HALT()),                # caller window (stock opcode)
        Block(label="SUB", term=SUSPEND(request_reg="fork")),      # THE FORK POINT, one frame deep
        Block(prim=_child_work("sub", seen), term=RET()),          # child body, then return to caller
    ]
    cm = ControlMachine()
    cont = cm.run(g, prog)
    assert isinstance(cont, Continuation) and cont.stack, "expected a suspend with a non-empty stack"

    sA, sB = _scope(g), _scope(g)
    for who, sc in (("A", sA), ("B", sB)):
        ControlMachine().resume(g, cont, {"scope": sc, "who": who})

    claims = {scope_of(g, n) for n in g.nodes() if (g.name(n) or "").startswith("claim_")}
    # THE PROBE: after RET the caller restores `saved_ctrl`. Each resumption should see the frame EXACTLY
    # as the parent left it at CALL time (depth=7). If the frame dict is shared, sibling B inherits
    # sibling A's decrement.
    depths = [regs.get("depth") for regs in after]
    contaminated = depths != [7] * len(depths)
    ok = claims == {sA, sB} and not contaminated
    print(f"  CASE 2 (inside CALL) forked-to={len(claims)} scopes  caller-depth-per-sibling={depths} "
          f"(expected {[7] * len(depths)})  contamination={contaminated}  "
          f"-> {'PASS' if ok else 'FAIL'}")
    return ok, prog


def case2b_capture_depth_is_the_fix(prog):
    """Is case 2 a CAPTURE-DEPTH bug or a missing control primitive? Decisive test: re-run the identical
    program, but hand each sibling a continuation whose STACK FRAMES are copied one level deeper. If the
    contamination vanishes with no change to the program and no new terminator, the defect is
    `SUSPEND`'s `list(self.stack)` and the answer to §10.5 is 'scheduler convention'."""
    g = AttrGraph()
    after: list = []
    # rebuild the program against a fresh probe list (the blocks hold closures over `after`)
    prog = [Block(control=list(b.control), body=list(b.body),
                  prim=(PRIM(fn=(lambda g_, s, c: (after.append(dict(c)), (s, 0))[1]))
                        if b.label == "AFTER" else b.prim),
                  label=b.label, term=b.term) for b in prog]
    cont = ControlMachine().run(g, prog)

    def deepen(c: Continuation) -> Continuation:
        """What `SUSPEND` should have captured: frame tuples copied, not aliased."""
        return Continuation(c.program, c.pc,
                            [(pc, list(st), dict(cx)) for pc, st, cx in c.stack],
                            dict(c.ctrl), list(c.stream), c.request)

    for who, sc in (("A", _scope(g)), ("B", _scope(g))):
        ControlMachine().resume(g, deepen(cont), {"scope": sc, "who": who})

    depths = [regs.get("depth") for regs in after]
    ok = depths == [7] * len(depths)
    print(f"  CASE 2b (deep copy)  caller-depth-per-sibling={depths} (expected {[7] * len(depths)})  "
          f"-> {'PASS' if ok else 'FAIL'}")
    return ok


# ── CASE 3: the join ─────────────────────────────────────────────────────────

def case3_join(g, scopes):
    sA, _sB = scopes
    claims = [n for n in g.nodes() if (g.name(n) or "").startswith("claim_")]
    isolated = all(not is_visible(g, n, None) for n in claims)      # nothing crossed on its own

    # ONE boundary promotes ONE winner (§4.3) — the crossing itself is already DATA (scope_crossing.py);
    # what is under test here is only that the execution model leaves base untouched until it runs.
    winner = next(n for n in claims if scope_of(g, n) == sA)
    promoted = g.add_node({NAME: valued(g.name(winner))})           # a BASE copy: the merge-back
    base_claims = [n for n in g.nodes()
                   if (g.name(n) or "").startswith("claim_") and scope_of(g, n) is None]
    ok = isolated and base_claims == [promoted]
    print(f"  CASE 3 (join)        isolated-before-join={isolated}  base-after-join={len(base_claims)}  "
          f"-> {'PASS' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    print("SPIKE: FORK/JOIN — opcode delta, or scheduler convention over SUSPEND?\n")
    ok1, g, scopes = case1_toplevel_fork()
    ok2, prog = case2_fork_inside_a_call()
    ok2b = case2b_capture_depth_is_the_fix(prog)
    ok3 = case3_join(g, scopes)
    print()
    if ok1 and ok3 and not ok2 and ok2b:
        print("VERDICT: GO — the OPCODE DELTA IS ZERO. Fork = resume one continuation N times; join =")
        print("run the crossing once every child has drained (cases 1 + 3). Case 2 found a real defect")
        print("but case 2b proves it is CAPTURE DEPTH in SUSPEND (`list(self.stack)` aliases the frame")
        print("dicts), fixable in one line, NOT a missing control primitive.")
    elif ok1 and ok2 and ok3:
        print("VERDICT: GO, unconditionally — resume-N-times IS fork; opcode delta is ZERO.")
    else:
        print("VERDICT: NO-GO / inconclusive — see the failing case above.")
