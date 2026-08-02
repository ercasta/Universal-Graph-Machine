"""THE ISA — imperative operations over named/indexed edges, focus heads, and references.

Revised twice on 2026-07-30: first for named edges (replacing `ugm/machine.py`'s nameless-edge, lowered-rule
premises), then again when the substrate became mutable and focus became the control mechanism.

**Why an ISA at all, when microfunctions are ordinary Python.** Because a program that is *data* can be
inspected, generated, stored in the graph, and learned; a Python function is fast and readable but opaque,
and an episode cannot be compiled into one. Both forms coexist by the test `mechanism_policy_separation.md`
already uses: **Python for mechanism nothing reasons about; ISA for anything that must be inspectable,
generated, or learned.**

**Three operand conventions.** A bare Python value is a literal; `R("x")` reads a register; `F("h")` reads
the node a focus head points at. That third one is what makes a program *pointed*: an instruction names the
head it acts on, never "whatever matches."

**State.** The machine carries a graph (mutated in place), registers (values and node ids), and a focus
(named heads). It runs inside a savepoint, so a failed or hypothetical run rewinds in O(changes) —
`north_star.md` §4's hypothesis-by-running, with the economics the copy-on-write version had backwards.

**⭐⭐ And that state is GRAPH DATA, so the executor has a yield point.** `_loop` was an ordinary Python
`while` holding `pc`, `stack` and `regs` as locals; it is now `tick`, one primitive operation over an
**activation record** that lives in the graph (`activation.py`). `run` is a loop over `tick` and nothing
else — there is one implementation of a step, deliberately, because two executors that are supposed to
agree is the drift class this codebase keeps re-finding (HANDOFF §6b).

What that buys is the test the whole arc is organised around: *can the executor be stopped between any two
primitive operations, and can the system say what it was doing?* Before this, `driver.step` made **planning**
steppable while the microfunction driving it ran inside an atomic invocation — steppability at the wrong
level, one seam removed and an identical one left below it.

**Control flow** is by label: a bare string in the program is a jump target, not an instruction.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import activation as A
from .focus import Focus
from .graph import Graph, Ref


@dataclass(frozen=True)
class R:
    """Read a register."""
    name: str


@dataclass(frozen=True)
class F:
    """Read the node a focus head points at — the *pointed* operand."""
    name: str


@dataclass(frozen=True)
class I:
    op: str
    args: tuple = ()

    def __repr__(self) -> str:
        return f"{self.op} {' '.join(map(str, self.args))}".strip()


def _ins(op):
    return lambda *args: I(op, args)


# graph writes
NEW, SET, LINK, LINK_AT, UNLINK, DROP, SETREF = (
    _ins(o) for o in ("NEW", "SET", "LINK", "LINK_AT", "UNLINK", "DROP", "SETREF"))
# graph reads
GET, GET_AT, COUNT, ATTR, EPROP, DEREF, SOURCES = (
    _ins(o) for o in ("GET", "GET_AT", "COUNT", "ATTR", "EPROP", "DEREF", "SOURCES"))
# focus
FOCUS, FORK, CLOSE, MOVE, BACK, FOLLOW, SPREAD, HEAD, HASFOCUS = (
    _ins(o) for o in ("FOCUS", "FORK", "CLOSE", "MOVE", "BACK", "FOLLOW", "SPREAD", "HEAD", "HASFOCUS"))
# values / arithmetic
CONST, COPY, ADD, LT, EQ, NOT = (_ins(o) for o in ("CONST", "COPY", "ADD", "LT", "EQ", "NOT"))
# control
JMP, JMPIF, JMPNOT, CALL, RET, HALT = (
    _ins(o) for o in ("JMP", "JMPIF", "JMPNOT", "CALL", "RET", "HALT"))
# ⭐ a primitive the kernel does not KNOW — see the NATIVE handler. Replaced `PLAN`/`STEP`, which made
# this module import `driver` and so put the planner below the kernel boundary.
NATIVE = _ins("NATIVE")
# calling a STORED function (graph-resident), as opposed to CALL's jump to a local label
INVOKE = _ins("INVOKE")
# the ONE way an effect leaves the graph — routed through `dispatch.service`'s checkpoint
DISPATCH = _ins("DISPATCH")

# Opcodes whose FIRST operand is a register they OVERWRITE. Stated here, beside the interpreter that does
# the overwriting, because a static reader of a stored body (`driver.establishes`) has to know exactly when
# a register stops denoting what it used to — and a list of those maintained anywhere else would drift.
WRITES_REGISTER = frozenset({
    "NEW", "GET", "GET_AT", "COUNT", "ATTR", "EPROP", "DEREF", "SOURCES",
    "SPREAD", "HEAD", "HASFOCUS", "CONST", "COPY", "ADD", "LT", "EQ", "NOT",
    "INVOKE", "DISPATCH", "NATIVE"})


class Machine:
    MAX_STEPS = 100_000        # a runaway program halts LOUDLY; termination is still unsolved in general

    def __init__(self, program) -> None:
        self.program = tuple(program)
        self.labels = {ins: i for i, ins in enumerate(self.program) if isinstance(ins, str)}

    def start(self, g: Graph, focus: Focus | None = None, *, of: str | None = None,
              caller: str | None = None, label: str | None = None, **regs) -> str:
        """Open an activation on this program and return the **node**. Nothing has run yet.

        ⭐ This is the seam. A caller that wants to be able to stop between two instructions drives `tick`
        itself and owns the activation; `run` is the convenience that ticks to completion."""
        focus = focus if focus is not None else Focus(g).open("root")
        return A.open_activation(g, focus.node, size=len(self.program), of=of, caller=caller,
                                 label=label, regs=regs)

    def tick(self, g: Graph, act: str) -> bool:
        """**ONE primitive operation.** Returns `True` while there is more to do, `False` once the program
        has run off its end or halted — so `while m.tick(g, a): ...` is the whole of running it.

        ⚠ Every piece of what happens between two ticks is on the activation, which is what makes stopping
        here a *pause* rather than a loss. Nothing is carried in a Python local across the boundary."""
        if A.finished(g, act):
            return False
        if A.took_a_step(g, act) > self.MAX_STEPS:
            raise RuntimeError(f"ISA program exceeded {self.MAX_STEPS} steps — not silently truncated")
        here = A.pc(g, act)
        ins = self.program[here]
        if isinstance(ins, str):                       # a label is a jump target, not an instruction
            A.set_pc(g, act, here + 1)
            return not A.finished(g, act)
        nxt, stop = self._step(ins, g, act, Focus(g, A.focus_node(g, act)), here)
        A.set_pc(g, act, nxt)
        if stop:
            A.halt(g, act)
        return not A.finished(g, act)

    def run(self, g: Graph, focus: Focus | None = None, *, rollback_on_error: bool = True,
            retire: bool = True, of: str | None = None, caller: str | None = None,
            label: str | None = None, **regs):
        """Execute against `g`, mutating it in place. On error, rewind to the entry savepoint so a failed
        program leaves no half-written graph behind — the transactional discipline mutability makes
        possible and copy-on-write was faking.

        ⚠ **This is a loop over `tick` and contains no interpreter of its own.** Keeping a fast Python loop
        beside the ticked one "just for the hot path" is the trap HANDOFF §6b names: it would drift, and it
        would drift silently. Slow and singular beats fast and forked.

        `retire=False` keeps the finished activation in the graph — for a caller that wants to read back
        how far it got, or what it was doing when it stopped."""
        # ⚠ The savepoint is taken FIRST, before the default focus is minted, or a failed run would leave
        # its own focus and head nodes behind — "a failed program leaves no half-written graph" has to
        # include the interpreter's own state now that the state is in the graph.
        sp = g.savepoint()
        focus = focus if focus is not None else Focus(g).open("root")
        try:
            act = self.start(g, focus, of=of, caller=caller, label=label, **regs)
            while self.tick(g, act):
                pass
            out = A.registers(g, act)
            if retire:
                A.retire(g, act)
            return g, focus, out
        except Exception:
            if rollback_on_error:
                g.rollback(sp)
            raise

    def _v(self, g, focus, act, x):
        if isinstance(x, R):
            return A.get_reg(g, act, x.name)
        if isinstance(x, F):
            return focus.at(x.name)
        return x

    def _step(self, ins, g: Graph, act: str, focus: Focus, pc: int):
        op, a = ins.op, ins.args
        v = lambda x: self._v(g, focus, act, x)                     # noqa: E731
        w = lambda dst, val: A.set_reg(g, act, dst.name, val)       # noqa: E731

        def node(x):
            """⭐⭐ **An operand that must be a NODE, refused when it is nothing.**

            ⚠ `activation.get_reg` answers `None` for a register that was never assigned — including one by
            a `GET` that found no edge, which is an ordinary occurrence the moment a part of the input can
            be missing. `g.link` then appended that `None`, and the graph gained **an edge whose target is
            `None`**: `targets` came back non-empty, so every "is this part present?" test answered *yes*,
            and whatever dereferenced the binding was handed `None` as though it were a node. Reported by
            `../pystrider` (`feedback_microfunctions.md` §10) with a repro, and confirmed here.

            **It converts a MISSING part into a PRESENT-BUT-NULL one**, so the failure surfaces arbitrarily
            far from the instruction that caused it. That is precisely the distinction `graph.UNKNOWN` was
            built to protect one slot over — *not there* versus *not looked at* — and a null edge destroys
            a third one underneath both: *no part* versus *a part that is nothing*.

            Refused here rather than in `Graph.link`, for the reason their suggestion gives: this layer
            knows the **opcode and the operand**, so the message can name them, while the substrate would
            only know that something passed it a `None`. `run` rolls back on any exception, so a refusal
            leaves no half-written graph."""
            got = v(x)
            if got is None:
                where = f"R({x.name})" if isinstance(x, R) else f"F({x.name})" if isinstance(x, F) else x
                raise RuntimeError(
                    f"{op}: operand {where} is not a node — it holds nothing. A register is unset until "
                    f"something assigns it, and a GET that found no edge assigns nothing. Writing this "
                    f"would mint an edge to None, and the graph would stop being able to tell 'no part' "
                    f"from 'a part that is nothing'.")
            return got

        # --- graph writes ---
        if op == "NEW":
            # ⭐ The ONE instruction that mints, so the activation can record exactly what this call
            # created — see `activation.minted` for why that replaced a whole-graph diff.
            made = g.mint(v(a[1]))
            A.record_mint(g, act, made)
            w(a[0], made)
        elif op == "SET":
            # ⚠ The SUBJECT must exist; the VALUE may legitimately be `None`, which is an ordinary
            # attribute value and distinct from `UNKNOWN`. Guarding the value would ban saying so.
            g.put(node(a[0]), **{v(a[1]): v(a[2])})
        elif op == "SETREF":
            g.set_ref(node(a[0]), v(a[1]), node(a[2]))
        elif op == "LINK":
            g.link(node(a[0]), v(a[1]), node(a[2]))
        elif op == "LINK_AT":
            g.link_at(node(a[0]), v(a[1]), int(v(a[2])), node(a[3]))
        elif op == "UNLINK":
            g.unlink(node(a[0]), v(a[1]), index=int(v(a[2])))
        elif op == "DROP":
            g.drop(node(a[0]))

        # --- graph reads ---
        elif op == "GET":
            w(a[0], g.target(v(a[1]), v(a[2])))
        elif op == "GET_AT":
            w(a[0], g.at(v(a[1]), v(a[2]), int(v(a[3]))))
        elif op == "COUNT":
            w(a[0], g.count(v(a[1]), v(a[2])))
        elif op == "ATTR":
            w(a[0], g.attr(v(a[1]), v(a[2])))
        elif op == "EPROP":
            w(a[0], g.edge_prop(v(a[1]), v(a[2]), int(v(a[3])), v(a[4])))
        elif op == "DEREF":
            w(a[0], g.deref(v(a[1]), v(a[2])))
        elif op == "SOURCES":
            w(a[0], g.sources(v(a[1]), v(a[2]) if len(a) > 2 else None))

        # --- focus ---
        elif op == "FOCUS":
            focus.open(v(a[0]), v(a[1]) if len(a) > 1 else "root")
        elif op == "FORK":
            focus.fork(v(a[0]), v(a[1]))
        elif op == "CLOSE":
            focus.close(v(a[0]))
        elif op == "MOVE":
            focus.move(g, v(a[0]), v(a[1]), int(v(a[2])) if len(a) > 2 else 0)
        elif op == "BACK":
            focus.back(g, v(a[0]), v(a[1]) if len(a) > 1 else None,
                       int(v(a[2])) if len(a) > 2 else 0)
        elif op == "FOLLOW":
            focus.follow_ref(g, v(a[0]), v(a[1]))
        elif op == "SPREAD":
            w(a[0], focus.spread(g, v(a[1]), v(a[2])))
        elif op == "HEAD":
            w(a[0], focus.at(v(a[1])))
        elif op == "HASFOCUS":
            w(a[0], focus.has(v(a[1])))

        # --- values ---
        elif op == "CONST" or op == "COPY":
            w(a[0], v(a[1]))
        elif op == "ADD":
            w(a[0], v(a[1]) + v(a[2]))
        elif op == "LT":
            w(a[0], v(a[1]) < v(a[2]))
        elif op == "EQ":
            w(a[0], v(a[1]) == v(a[2]))
        elif op == "NOT":
            w(a[0], not v(a[1]))

        # --- control ---
        elif op == "JMP":
            return self.labels[v(a[0])], False
        elif op == "JMPIF":
            if v(a[0]):
                return self.labels[v(a[1])], False
        elif op == "JMPNOT":
            if not v(a[0]):
                return self.labels[v(a[1])], False
        elif op == "CALL":
            A.push(g, act, pc + 1)
            return self.labels[v(a[0])], False
        elif op == "RET":
            ret = A.pop(g, act)
            return (len(self.program) if ret is None else ret), False
        elif op == "HALT":
            return pc, True

        elif op == "INVOKE":
            # Call a STORED function: `INVOKE R(dst), "name", {"param": operand, …}`. The callee gets a
            # fresh focus holding only its bound parameters — never the caller's heads — so a function is
            # never silently sensitive to where its caller happened to be looking.
            from .function import invoke as _invoke
            # A `Ref` operand resolves to the node it points at. This is how a LEARNED function carries a
            # binding that was deliberately kept constant (`application.generalise`): the generalised
            # arguments arrive as `F(param)`, the fixed ones as a stored pointer to that exact node.
            bindings = {k: (x.node if isinstance(x, Ref) else v(x))
                        for k, x in (v(a[2]) or {}).items()} if len(a) > 2 else {}
            # ⚠ `caller=act` is what keeps the call chain readable. A nested invocation used to be a nested
            # Python frame — invisible to the system running it — so "what was it doing?" could only ever
            # answer about the outermost program. `activation.chain` walks it.
            _f, out = _invoke(g, v(a[1]), bindings, caller=act)
            if isinstance(a[0], R):
                w(a[0], out.get("result"))

        elif op == "DISPATCH":
            # `DISPATCH R(dst), "tool", F(head)` — the only escape hatch to the outside world, and it
            # goes through the one checkpoint (`dispatch.service`): veto checked at APPLY time, graph
            # committed before the handler runs. A `Vetoed` propagates, so a forbidden effect fails
            # loudly rather than being skipped in silence.
            #
            # ⚠ A handler mints straight into the graph — it is the world arriving, not an instruction —
            # so this is the one place a diff is still the honest way to learn what appeared. It is scoped
            # to the single call that crosses the boundary rather than to a whole invocation, and dispatch
            # is rare by construction.
            from .dispatch import service as _service
            before = set(g.nodes)
            got = _service(g, v(a[1]), v(a[2]))
            for made in sorted(set(g.nodes) - before):
                A.record_mint(g, act, made)
            w(a[0], got)

        elif op == "NATIVE":
            # `NATIVE R(dst), "name", <operand>…` — call a primitive the kernel does NOT know.
            #
            # ⭐⭐ **THIS IS WHERE THE KERNEL STOPS AND THE REPRESENTATION BEGINS.** It used to be two
            # opcodes, `PLAN` and `STEP`, whose handlers imported `driver` — so the instruction set, the
            # most kernel thing there is, knew what a plan was, and a Rust port would have had to port the
            # whole planner to implement two instructions (`docs/microfunctions/kernel_boundary.md`).
            #
            # ⭐ The old docstring's argument was RIGHT and is preserved: search is a **primitive**, not
            # sugar — no sequence of GET/SET/LINK imagines a state, and a frontier ordering is not data
            # manipulation. What was wrong was concluding that a primitive must therefore be an *opcode*.
            # It must be reachable and uncomposable; it need not be NAMED here. `native.py` is the table,
            # `driver` puts the planner in it, and this instruction knows only a string.
            #
            # ⚠ Operands resolve with `node()`, so both `F(x)` and `R(x)` work in any position — which is
            # what the two mnemonics needed between them (`PLAN` took focus heads, `STEP` a register).
            # ⚠ The destination is OPTIONAL and told apart by TYPE, not by counting: a register operand
            # is an `R`, a name is a string literal, so `NATIVE R(s) "plan" …` and `NATIVE "check" …`
            # cannot be confused. `CHECK` needed that — it answers by raising, not by returning.
            from .native import call as _native
            dst = a[0] if isinstance(a[0], R) else None
            rest = a[1:] if dst is not None else a
            got = _native(g, v(rest[0]), tuple(node(x) for x in rest[1:]), act)
            if dst is not None:
                w(dst, got)

        else:
            raise ValueError(f"unknown opcode {op!r}")
        return pc + 1, False


def run(program, g: Graph, focus: Focus | None = None, **regs):
    return Machine(program).run(g, focus, **regs)


__all__ = ["R", "F", "I", "Ref", "Machine", "run", "WRITES_REGISTER",
           "NEW", "SET", "LINK", "LINK_AT", "UNLINK", "DROP", "SETREF",
           "GET", "GET_AT", "COUNT", "ATTR", "EPROP", "DEREF", "SOURCES",
           "FOCUS", "FORK", "CLOSE", "MOVE", "BACK", "FOLLOW", "SPREAD", "HEAD", "HASFOCUS",
           "CONST", "COPY", "ADD", "LT", "EQ", "NOT",
           "JMP", "JMPIF", "JMPNOT", "CALL", "RET", "HALT", "INVOKE", "DISPATCH",
           "NATIVE"]
