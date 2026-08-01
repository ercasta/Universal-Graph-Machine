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

**Control flow** is by label: a bare string in the program is a jump target, not an instruction.
"""
from __future__ import annotations

from dataclasses import dataclass

from .focus import Focus
from .graph import Graph, Ref
from .types import check


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
# the demoted match
CHECK = _ins("CHECK")
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
    "INVOKE", "DISPATCH"})


class Machine:
    MAX_STEPS = 100_000        # a runaway program halts LOUDLY; termination is still unsolved in general

    def __init__(self, program) -> None:
        self.program = tuple(program)
        self.labels = {ins: i for i, ins in enumerate(self.program) if isinstance(ins, str)}

    def run(self, g: Graph, focus: Focus | None = None, *, rollback_on_error: bool = True, **regs):
        """Execute against `g`, mutating it in place. On error, rewind to the entry savepoint so a failed
        program leaves no half-written graph behind — the transactional discipline mutability makes
        possible and copy-on-write was faking."""
        focus = focus if focus is not None else Focus().open("root")
        sp = g.savepoint()
        try:
            return self._loop(g, focus, dict(regs))
        except Exception:
            if rollback_on_error:
                g.rollback(sp)
            raise

    def _loop(self, g, focus, regs):
        pc, stack, steps = 0, [], 0
        while pc < len(self.program):
            steps += 1
            if steps > self.MAX_STEPS:
                raise RuntimeError(f"ISA program exceeded {self.MAX_STEPS} steps — not silently truncated")
            ins = self.program[pc]
            if isinstance(ins, str):
                pc += 1
                continue
            pc, stop = self._step(ins, g, focus, regs, pc, stack)
            if stop:
                break
        return g, focus, regs

    def _v(self, g, focus, regs, x):
        if isinstance(x, R):
            return regs.get(x.name)
        if isinstance(x, F):
            return focus.at(x.name)
        return x

    def _step(self, ins, g: Graph, focus: Focus, regs, pc, stack):
        op, a = ins.op, ins.args
        v = lambda x: self._v(g, focus, regs, x)        # noqa: E731

        def node(x):
            """⭐⭐ **An operand that must be a NODE, refused when it is nothing.**

            ⚠ `regs.get` answers `None` for a register that was never assigned — including one assigned by
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
            regs[a[0].name] = g.mint(v(a[1]))
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
            regs[a[0].name] = g.target(v(a[1]), v(a[2]))
        elif op == "GET_AT":
            regs[a[0].name] = g.at(v(a[1]), v(a[2]), int(v(a[3])))
        elif op == "COUNT":
            regs[a[0].name] = g.count(v(a[1]), v(a[2]))
        elif op == "ATTR":
            regs[a[0].name] = g.attr(v(a[1]), v(a[2]))
        elif op == "EPROP":
            regs[a[0].name] = g.edge_prop(v(a[1]), v(a[2]), int(v(a[3])), v(a[4]))
        elif op == "DEREF":
            regs[a[0].name] = g.deref(v(a[1]), v(a[2]))
        elif op == "SOURCES":
            regs[a[0].name] = g.sources(v(a[1]), v(a[2]) if len(a) > 2 else None)

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
            regs[a[0].name] = focus.spread(g, v(a[1]), v(a[2]))
        elif op == "HEAD":
            regs[a[0].name] = focus.at(v(a[1]))
        elif op == "HASFOCUS":
            regs[a[0].name] = focus.has(v(a[1]))

        # --- values ---
        elif op == "CONST" or op == "COPY":
            regs[a[0].name] = v(a[1])
        elif op == "ADD":
            regs[a[0].name] = v(a[1]) + v(a[2])
        elif op == "LT":
            regs[a[0].name] = v(a[1]) < v(a[2])
        elif op == "EQ":
            regs[a[0].name] = v(a[1]) == v(a[2])
        elif op == "NOT":
            regs[a[0].name] = not v(a[1])

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
            stack.append(pc + 1)
            return self.labels[v(a[0])], False
        elif op == "RET":
            return (stack.pop() if stack else len(self.program)), False
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
            _f, out = _invoke(g, v(a[1]), bindings)
            if isinstance(a[0], R):
                regs[a[0].name] = out.get("result")

        elif op == "DISPATCH":
            # `DISPATCH R(dst), "tool", F(head)` — the only escape hatch to the outside world, and it
            # goes through the one checkpoint (`dispatch.service`): veto checked at APPLY time, graph
            # committed before the handler runs. A `Vetoed` propagates, so a forbidden effect fails
            # loudly rather than being skipped in silence.
            from .dispatch import service as _service
            regs[a[0].name] = _service(g, v(a[1]), v(a[2]))

        elif op == "CHECK":
            check(g, v(a[0]), v(a[1]))
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
           "JMP", "JMPIF", "JMPNOT", "CALL", "RET", "HALT", "CHECK", "INVOKE", "DISPATCH"]
