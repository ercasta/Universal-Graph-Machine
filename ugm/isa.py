"""The instruction set — imperative operations over named and indexed edges, focus heads, and references.

A program that is data can be inspected, generated, stored in the graph and learned; a Python
function is fast and readable but opaque, and an episode cannot be compiled into one. Both forms
coexist by one test: Python for mechanism nothing reasons about, stored instructions for anything
that must be inspectable, generated, or learned.

Three operand conventions. A bare Python value is a literal, `R("x")` reads a register, and
`F("h")` reads the node a focus head points at. The third is what makes a program pointed: an
instruction names the head it acts on, never whatever matches.

A machine carries a graph, mutated in place, registers holding values and node ids, and a focus
of named heads. It runs inside a savepoint, so a failed or hypothetical run rewinds at a cost
proportional to the changes made.

That state is graph data, so the executor has a yield point. `run` is a loop over `tick`, one
primitive operation over an activation record that lives in the graph, and there is exactly one
implementation of a step. Two executors that are supposed to agree is a drift class this codebase
keeps re-finding, and it would drift silently.

What that buys is the property the whole execution model is organised around: the executor can be
stopped between any two primitive operations, and the system can say what it was doing.

Control flow is by label — a bare string in the program is a jump target rather than an
instruction. A runaway program raises at a step limit rather than truncating silently.

See `docs/reference/isa.md`.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import activation as A
from .focus import Focus
from .graph import Graph, Ref, Refusal


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


#: The edge and attribute a binding set is described with, when it is graph data rather than a literal.
ARG, PARAM, VALUE = "arg", "param", "value"


def _bindings(g, v, operand) -> dict:
    """`INVOKE`'s third operand: a literal mapping, or a NODE describing one.

    The literal form fixes the parameter *names* at assembly time, which is fine for a program that
    knows what it is calling and useless for one that does not. `execution.step` assembles its arguments
    by walking a transformation's `arg` edges — names and values both computed — and that is why it is
    Python: not because calling dynamically was impossible (the function name already resolves through a
    register) but because a *binding set* could not be built at all.

    So the second form is graph data, deliberately, rather than "a register may hold a dict". A dict in a
    register would be a Python value the system cannot read, which is the island pattern with a shorter
    name; a node with `arg` edges is something a rule can build, inspect, store and hand to something
    else. It is also the shape `transformation` already uses to record the arguments of a step.

        NEW  R(b) "binding"
        SET  R(b) "param" R(name)      ← the parameter name, computed
        LINK R(b) "value" R(node)      ← what to bind it to
        LINK R(args) "arg" R(b)
        INVOKE R(out) R(fn) R(args)

    A `Ref` operand resolves to the node it points at. This is how a learned function carries a binding
    that was deliberately kept constant (`application.generalise`): the generalised arguments arrive as
    `F(param)`, the fixed ones as a stored pointer to that exact node."""
    got = v(operand)
    if isinstance(got, dict):
        return {k: (x.node if isinstance(x, Ref) else v(x)) for k, x in got.items()}
    if got is None:
        return {}
    out = {}
    for b in g.targets(got, ARG):
        name = g.attr(b, PARAM)
        if name is None:
            raise RuntimeError(
                f"INVOKE: {b} is in {got}'s binding set but names no parameter. A binding is a node with "
                f"a {PARAM!r} attribute and a {VALUE!r} edge; without the name there is nowhere to put it.")
        out[name] = g.target(b, VALUE)
    return out


def _keys(g, node) -> tuple:
    """A node's attribute keys, sorted, without `kind`. The one place that exclusion is decided."""
    return tuple(sorted(k for k in g.attrs.get(node, {}) if k != "kind"))


def _eprop_keys(g, src, label, index) -> tuple:
    """An edge's property keys, sorted. Sorted for the reason `_keys` is: a program that walks the same
    edge twice must walk it alike, and edge properties are a plain dict whose insertion order is a fact
    about how the edge was written rather than about the graph.

    An edge that does not exist has no properties, which is the same answer as an edge that has none.
    That conflation is deliberate here and safe: the caller reached this by way of `COUNT`, so a
    position it did not get from there is its own bug and not something to encode a second signal for."""
    eid = g.edge_at(src, label, index)
    return () if eid is None else tuple(sorted(g.edge_props(eid)))


# graph writes
NEW, SET, LINK, LINK_AT, UNLINK, DROP, SETREF = (
    _ins(o) for o in ("NEW", "SET", "LINK", "LINK_AT", "UNLINK", "DROP", "SETREF"))
# `SET`, for an edge. Python gives an edge its properties when it creates it, because Python can build the
# whole dict first; the surface cannot hold a dict, so it makes the edge and then carries the properties
# over one at a time. Addressed as `EPROP` addresses them — src, label, index — and never by edge id, so
# programs keep holding exactly one kind of pointer.
SETEPROP = _ins("SETEPROP")
# graph reads
GET, GET_AT, COUNT, ATTR, EPROP, DEREF, SOURCES = (
    _ins(o) for o in ("GET", "GET_AT", "COUNT", "ATTR", "EPROP", "DEREF", "SOURCES"))
# graph reflection — the shape of a node, rather than what is at a slot you already know the name of.
#
# Every read above takes a *named* slot: `GET dest subj "label"` asks what is at this label, and nothing
# asked *which labels are there*. That single asymmetry is why copying a subgraph looked like a primitive.
# It is not: `workbench.reachable` walks outgoing edges and `_copy_set` mints a node with the same kind and
# attributes, and both are ordinary loops over structure the instruction set could not see. With these,
# they are ordinary programs, and the closed class shrinks by a whole family of would-be natives.
#
# Substrate, deliberately, and it is the classification that matters: none of these encodes a decision
# about goals, plans, time or criteria, so they sit *below* the kernel boundary rather than above it.
# The counter-proposal was a single `CLONE` opcode — fewer primitives, and the wrong trade, because
# "the same kind and the same attributes" is a decision, and baking it in is a composite wearing
# substrate's clothes.
#
# Count-plus-index rather than returning a collection, matching `COUNT`/`GET_AT`, so iteration is the
# loop the instruction set already writes and a register keeps holding one scalar.
KIND, NLABELS, LABEL_AT, NKEYS, KEY_AT = (
    _ins(o) for o in ("KIND", "NLABELS", "LABEL_AT", "NKEYS", "KEY_AT"))
# The same asymmetry one level further out, and it was left open when the five above were added: `EPROP`
# reads a property whose name you already know, and nothing asked which properties an edge has. So a copy
# written in the surface silently dropped them — the defect `_copy_set` had once in Python, where it also
# failed silently, because no check copied an edge that carried any.
#
# An edge rather than a node, so the subject is `src`/`label`/`index` — `EPROP`'s addressing, not a second
# one. Naming the edge by its id was the alternative and is worse: `edge_at` already exists for exactly
# this, and handing programs raw edge ids would make them hold a second kind of pointer whose lifetime
# nothing in the surface manages.
NEPROPS, EPROP_AT = (_ins(o) for o in ("NEPROPS", "EPROP_AT"))
# focus
FOCUS, FORK, CLOSE, MOVE, BACK, FOLLOW, SPREAD, HEAD, HASFOCUS = (
    _ins(o) for o in ("FOCUS", "FORK", "CLOSE", "MOVE", "BACK", "FOLLOW", "SPREAD", "HEAD", "HASFOCUS"))
# values / arithmetic
CONST, COPY, ADD, LT, EQ, NOT = (_ins(o) for o in ("CONST", "COPY", "ADD", "LT", "EQ", "NOT"))
# control
JMP, JMPIF, JMPNOT, CALL, RET, HALT = (
    _ins(o) for o in ("JMP", "JMPIF", "JMPNOT", "CALL", "RET", "HALT"))
# a primitive the kernel does not know — see the NATIVE handler. Replaced `PLAN`/`STEP`, which made
# this module import `driver` and so put the planner below the kernel boundary.
NATIVE = _ins("NATIVE")
# calling a stored function (graph-resident), as opposed to CALL's jump to a local label
INVOKE = _ins("INVOKE")
# the same call, with the refusal handed back as a VALUE instead of raising.
#
# `types.check` raises and `types.is_a` answers; the same pair was missing one level up. `INVOKE` raises,
# and nothing answered — which is exactly why `execution.step` is Python: its whole job is to turn a
# refused call into a `deviation`, and turning a refusal into data is the one thing the surface could not
# do. The engine has repeatedly had the *enforcing* form and lacked the *answering* one.
#
# A separate opcode rather than a flag on `INVOKE`: failing-as-a-value and calling-dynamically are
# independent capabilities that merely happened to be needed together, and bundling them would be the
# `CLONE` mistake — a composite wearing a primitive's clothes.
ATTEMPT = _ins("ATTEMPT")
# the one way an effect leaves the graph — routed through `dispatch.service`'s checkpoint
DISPATCH = _ins("DISPATCH")

# Opcodes whose first operand is a register they overwrite. Stated here, beside the interpreter that does
# the overwriting, because a static reader of a stored body (`driver.establishes`) has to know exactly when
# a register stops denoting what it used to — and a list of those maintained anywhere else would drift.
WRITES_REGISTER = frozenset({
    "NEW", "GET", "GET_AT", "COUNT", "ATTR", "EPROP", "DEREF", "SOURCES",
    "KIND", "NLABELS", "LABEL_AT", "NKEYS", "KEY_AT", "NEPROPS", "EPROP_AT",
    "SPREAD", "HEAD", "HASFOCUS", "CONST", "COPY", "ADD", "LT", "EQ", "NOT",
    "INVOKE", "ATTEMPT", "DISPATCH", "NATIVE"})

# Opcodes that read the graph, mapped to the kind of slot they read — the counterpart of the write side
# `driver._effects` already reads off a body, and stated here for the same reason `WRITES_REGISTER` is:
# a second list maintained beside a consumer would drift from the interpreter that does the reading.
#
# Every one of these has the same operand shape — `OP R(dest) <subject> "slot"` — which is what makes the
# static reader uniform. `SOURCES`'s slot is optional (no label means *every* label, which is honestly
# unreadable), and `EPROP` reads a property *of an edge*, so its slot is the edge's label: an edge property
# is a property of a link, and reporting it as `("link", label)` keeps it in the vocabulary
# `driver.establishes` already speaks rather than inventing a third kind for one opcode.
#
# The reflection opcodes are in here and always land in the *unknown* bucket, which is the honest answer
# rather than a shortcoming: none of them takes a literal slot, because not knowing the slot is what they
# are for. `_reads` already handles that case — it names the subject it could not finish reading — so a
# body that walks a node's shape reports "reads all of this node, and I cannot say which parts",
# and a consumer can see exactly how much of the answer is missing.
READS_GRAPH = {"GET": "link", "GET_AT": "link", "COUNT": "link", "SOURCES": "link", "DEREF": "link",
               "ATTR": "attr", "EPROP": "link",
               "KIND": "attr", "NKEYS": "attr", "KEY_AT": "attr",
               "NLABELS": "link", "LABEL_AT": "link",
               # A property of an edge is a property of a link, which is the vocabulary `EPROP` already
               # reports in rather than a third kind invented for two opcodes.
               "NEPROPS": "link", "EPROP_AT": "link"}


class Machine:
    MAX_STEPS = 100_000        # a runaway program halts loudly; termination is still unsolved in general

    def __init__(self, program) -> None:
        self.program = tuple(program)
        self.labels = {ins: i for i, ins in enumerate(self.program) if isinstance(ins, str)}

    def start(self, g: Graph, focus: Focus | None = None, *, of: str | None = None,
              caller: str | None = None, label: str | None = None, **regs) -> str:
        """Open an activation on this program and return the node. Nothing has run yet.

        This is the seam. A caller that wants to be able to stop between two instructions drives `tick`
        itself and owns the activation; `run` is the convenience that ticks to completion."""
        focus = focus if focus is not None else Focus(g).open("root")
        return A.open_activation(g, focus.node, size=len(self.program), of=of, caller=caller,
                                 label=label, regs=regs)

    def tick(self, g: Graph, act: str) -> bool:
        """one primitive operation. Returns `True` while there is more to do, `False` once the program
        has run off its end or halted — so `while m.tick(g, a): ...` is the whole of running it.

        Every piece of what happens between two ticks is on the activation, which is what makes stopping
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

        This is a loop over `tick` and contains no interpreter of its own. Keeping a fast Python loop
        beside the ticked one "just for the hot path" is the trap an earlier note names: it would drift, and it
        would drift silently. Slow and singular beats fast and forked.

        `retire=False` keeps the finished activation in the graph — for a caller that wants to read back
        how far it got, or what it was doing when it stopped."""
        # The savepoint is taken first, before the default focus is minted, or a failed run would leave
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
            """An operand that must be a node, refused when it is nothing.

            `activation.get_reg` answers `None` for a register that was never assigned — including one by
            a `GET` that found no edge, which is an ordinary occurrence the moment a part of the input can
            be missing. `g.link` then appended that `None`, and the graph gained an edge whose target is
            `None`: `targets` came back non-empty, so every "is this part present?" test answered *yes*,
            and whatever dereferenced the binding was handed `None` as though it were a node. Reported by
            the first consumer with a repro, and confirmed here.

            It converts a missing part into a present-but-null one, so the failure surfaces arbitrarily
            far from the instruction that caused it. That is precisely the distinction `graph.UNKNOWN` was
            built to protect one slot over — *not there* versus *not looked at* — and a null edge destroys
            a third one underneath both: *no part* versus *a part that is nothing*.

            Refused here rather than in `Graph.link`, for the reason their suggestion gives: this layer
            knows the opcode and the operand, so the message can name them, while the substrate would
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
            # The one instruction that mints, so the activation can record exactly what this call
            # created — see `activation.minted` for why that replaced a whole-graph diff.
            made = g.mint(v(a[1]))
            A.record_mint(g, act, made)
            w(a[0], made)
        elif op == "SET":
            # The SUBJECT must exist; the value may legitimately be `None`, which is an ordinary
            # attribute value and distinct from `UNKNOWN`. Guarding the value would ban saying so.
            g.put(node(a[0]), **{v(a[1]): v(a[2])})
        elif op == "SETREF":
            g.set_ref(node(a[0]), v(a[1]), node(a[2]))
        elif op == "SETEPROP":
            # The edge must exist; the value may be `None`, for `SET`'s reason.
            _eid = g.edge_at(node(a[0]), v(a[1]), int(v(a[2])))
            if _eid is None:
                raise ValueError(f"SETEPROP: no edge at {v(a[1])!r}[{v(a[2])}] of {node(a[0])}")
            g.put_edge_props(_eid, **{v(a[3]): v(a[4])})
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

        # --- reflection: the shape of a node, not the contents of a slot you already named ---
        # Order is load-bearing and inherited, not invented here. `g.labels` is sorted and `g.targets`
        # is insertion-ordered, which is what makes a copy deterministic; `workbench.reachable` records
        # what it cost to learn that — returning a `set` there substituted the iteration order of node-id
        # strings and made the identical search cost 12, then 306, then fail, in one process. Attribute
        # keys are sorted here for the same reason, so a program walking them twice walks them alike.
        elif op == "KIND":
            w(a[0], g.kind(v(a[1])))
        elif op == "NLABELS":
            w(a[0], len(g.labels(v(a[1]))))
        elif op == "LABEL_AT":
            _lbls = g.labels(v(a[1]))
            _i = int(v(a[2]))
            w(a[0], _lbls[_i] if -len(_lbls) <= _i < len(_lbls) else None)
        # `kind` lives in the same dict as the attributes but is not one of them: it is positional, it
        # cannot be changed after minting, and `KIND` is how you read it. Letting it out here would make a
        # copy written in the surface set `kind` twice — once by minting, once by replay — and `g.put`
        # refuses a changed kind, so the honest bug would surface as a confusing one.
        elif op == "NKEYS":
            w(a[0], len(_keys(g, v(a[1]))))
        elif op == "KEY_AT":
            _ks = _keys(g, v(a[1]))
            _i = int(v(a[2]))
            w(a[0], _ks[_i] if -len(_ks) <= _i < len(_ks) else None)
        elif op == "NEPROPS":
            w(a[0], len(_eprop_keys(g, v(a[1]), v(a[2]), int(v(a[3])))))
        elif op == "EPROP_AT":
            _ps = _eprop_keys(g, v(a[1]), v(a[2]), int(v(a[3])))
            _i = int(v(a[4]))
            w(a[0], _ps[_i] if -len(_ps) <= _i < len(_ps) else None)

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
            # Call a stored function: `INVOKE R(dst), "name", {"param": operand, …}`. The callee gets a
            # fresh focus holding only its bound parameters — never the caller's heads — so a function is
            # never silently sensitive to where its caller happened to be looking.
            from .function import invoke as _invoke
            bindings = _bindings(g, v, a[2]) if len(a) > 2 else {}
            # `caller=act` is what keeps the call chain readable. A nested invocation used to be a nested
            # Python frame — invisible to the system running it — so "what was it doing?" could only ever
            # answer about the outermost program. `activation.chain` walks it.
            _f, out = _invoke(g, v(a[1]), bindings, caller=act)
            if isinstance(a[0], R):
                w(a[0], out.get("result"))

        elif op == "ATTEMPT":
            # `ATTEMPT R(out) R(err) <name> <bindings>` — call, and hand back a refusal as a node.
            #
            # **What is caught is a closed set, and the line is whose fault it is.** A refusal is a claim
            # about the WORLD or the REQUEST: a precondition no longer holds, a standing prohibition
            # names the target, the target is imagined. An error is a claim about the PROGRAM: an unset
            # register, an unknown function, a bad opcode. Catching the second kind would turn a bug into
            # a quiet `err` nobody reads, which is the failure this codebase keeps naming — so they are
            # not caught, and they still abort.
            #
            # A refused attempt leaves NOTHING behind. The savepoint is taken here and rolled back on
            # refusal, matching the discipline every other border keeps: a half-applied call would be
            # worse than a raised one, because the caller carries on. Nothing real can have escaped —
            # `TypeViolation` fires at the parameter check and the dispatch refusals fire before the
            # handler runs, all of them before `dispatch.service` commits.
            from .function import invoke as _invoke2
            binds = _bindings(g, v, a[3]) if len(a) > 3 else {}
            sp = g.savepoint()
            try:
                _f, out = _invoke2(g, v(a[2]), binds, caller=act)
            except Refusal as e:
                g.rollback(sp)
                refusal = g.mint("refusal", refused=type(e).__name__, why=str(e),
                                 **{k: getattr(e, k) for k in ("param", "want")
                                    if getattr(e, k, None) is not None})
                if isinstance(a[1], R):
                    w(a[1], refusal)
                if isinstance(a[0], R):
                    w(a[0], None)
            else:
                if isinstance(a[1], R):
                    w(a[1], None)
                if isinstance(a[0], R):
                    w(a[0], out.get("result"))

        elif op == "DISPATCH":
            # `DISPATCH R(dst), "tool", F(head)` — the only escape hatch to the outside world, and it
            # goes through the one checkpoint (`dispatch.service`): veto checked at apply time, graph
            # committed before the handler runs. A `Vetoed` propagates, so a forbidden effect fails
            # loudly rather than being skipped in silence.
            #
            # A handler mints straight into the graph — it is the world arriving, not an instruction —
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
            # This is where the kernel stops and the representation begins. It used to be two
            # opcodes, `PLAN` and `STEP`, whose handlers imported `driver` — so the instruction set, the
            # most kernel thing there is, knew what a plan was, and a Rust port would have had to port the
            # whole planner to implement two instructions (`docs/execution-model.md`).
            #
            # The old docstring's argument was right and is preserved: search is a primitive, not
            # sugar — no sequence of GET/SET/LINK imagines a state, and a frontier ordering is not data
            # manipulation. What was wrong was concluding that a primitive must therefore be an *opcode*.
            # It must be reachable and uncomposable; it need not be named here. `native.py` is the table,
            # `driver` puts the planner in it, and this instruction knows only a string.
            #
            # Operands resolve with `node()`, so both `F(x)` and `R(x)` work in any position — which is
            # what the two mnemonics needed between them (`PLAN` took focus heads, `STEP` a register).
            # The destination is optional and told apart by type, not by counting: a register operand
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


__all__ = ["R", "F", "I", "Ref", "Machine", "run", "WRITES_REGISTER", "READS_GRAPH",
           "NEW", "SET", "LINK", "LINK_AT", "UNLINK", "DROP", "SETREF", "SETEPROP",
           "GET", "GET_AT", "COUNT", "ATTR", "EPROP", "DEREF", "SOURCES",
           "KIND", "NLABELS", "LABEL_AT", "NKEYS", "KEY_AT", "NEPROPS", "EPROP_AT",
           "FOCUS", "FORK", "CLOSE", "MOVE", "BACK", "FOLLOW", "SPREAD", "HEAD", "HASFOCUS",
           "CONST", "COPY", "ADD", "LT", "EQ", "NOT",
           "JMP", "JMPIF", "JMPNOT", "CALL", "RET", "HALT", "INVOKE", "ATTEMPT", "DISPATCH",
           "NATIVE"]
