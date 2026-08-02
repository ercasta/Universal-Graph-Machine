"""ACTIVATION — the ISA interpreter's own state, as ordinary graph data.

**The gap this closes, stated as the test that makes it checkable** (the design notes):

> Can the executor be stopped between any two primitive operations, and can the system say what it was
> doing?

Before this module the answer was no, and in a way that was easy to miss. §5z made *planning* steppable —
`search.py` moved the frontier, the visited set and the step counter into the graph, and `driver.step` became
the yield point. But `isa.Machine._loop` was an ordinary Python `while` holding `pc`, `stack` and `regs` as
locals, so the microfunction that drove the steppable search —

```
fn think(goal, subject, thread) -> plan:
    NATIVE R(s) "plan" F(goal) F(subject) F(thread)
    .again:
    NATIVE R(more) "plan_step" R(s)
    JMPIF R(more) ".again"
```

— ran an **interruptible** search from inside an **atomic** invocation. Steppability at the wrong level: one
seam removed and an identical one left below it, inverted. The principle predicts exactly that, which is the
argument for adopting it rather than patching upward.

**⚠ Four things had to materialise, not three.** `pc`, the call stack, the registers — and the **focus**,
which is as much interpreter state as the registers and is easy to miss because `Focus` looks like a helper
rather than a loop variable. It moved in `focus.py`; the activation merely points at it.

## The shape

```
activation(pc, steps, stack, halted) ──focus──▶ focus ──head──▶ head ──at──▶ world
                                     ──register──▶ register(name, value)
                                     ──of──▶ function          (when the program is a stored one)
                                     ──caller──▶ activation    (INVOKE, so the chain is readable)
```

**⭐ A register is a node, not an attribute of the activation.** An attribute keyed by register name would
collide with the activation's own slots — a program with a register called `pc` or `kind` would corrupt the
interpreter, and `Graph.put` refuses to write `kind` at all. One node per register also gives a register a
stable address, so something can point at one.

⚠ **A register's value is any Python value**, because the ISA's is: `SOURCES` yields a tuple, `COUNT` an
int, `HEAD` a node id. It is stored as an attribute rather than an edge for that reason — an edge would be
a claim that the register and the node are *related*, which is exactly the reference/edge distinction
`graph.py` keeps sharp. A register holding a node holds a pointer.

⚠ **The stack is a tuple attribute, and tuples are why that is safe.** The journal records the *previous
value* of an attribute, so a mutable list would be recorded by reference and roll back to itself. Every
push and pop writes a fresh tuple.

## What it is NOT

⚠ **This is not a second interpreter.** `Machine.run` is a loop over `Machine.tick`, and there is exactly
one implementation of a step. The design notes names keeping a fast Python loop "just for the hot path" as the
trap: two executors that are supposed to agree is the drift class this codebase keeps re-finding, and it
would drift silently. Slow and singular beats fast and forked.

⚠ **Retirement is not the same as being uninterruptible.** `run` drops the activation's registers and the
activation itself once the program is finished, because a finished activation is not state anybody can be
inside of — the same reason `dispatch.commit()` is right. Anything that wants to keep one drives `tick`
itself and owns the node. `retire` is refused while the activation can still take a step, so this cannot
become a way of throwing away a live computation.
"""
from __future__ import annotations

from .graph import Graph

KINDS = ("activation", "register")


# --- opening ------------------------------------------------------------------------------------------
def open_activation(g: Graph, focus_node: str, *, size: int, of: str | None = None,
                    caller: str | None = None, label: str | None = None,
                    regs: dict | None = None) -> str:
    """A fresh activation, at `pc=0`, ready to be ticked. `size` is the program length — the halt
    condition, and the one fact about the program the state itself has to carry.

    `of` is the stored `function` node when the program came from one, which is what lets `doing` name the
    instruction rather than only its index.

    ⚠ The seed registers arrive as a **dict**, not as `**regs`: a register may legitimately be called
    `size` or `of`, and a keyword-splat here would let one silently become an activation slot."""
    a = g.mint("activation", pc=0, steps=0, stack=(), halted=False, size=size)
    if label:
        g.put(a, label=label)
    g.link(a, "focus", focus_node)
    if of is not None:
        g.link(a, "of", of)
    if caller is not None:
        g.link(a, "caller", caller)
    for name, value in (regs or {}).items():
        set_reg(g, a, name, value)
    return a


# --- the program counter -------------------------------------------------------------------------------
def pc(g: Graph, a: str) -> int:
    return g.attr(a, "pc", 0)


def set_pc(g: Graph, a: str, i: int) -> None:
    g.put(a, pc=i)


def size(g: Graph, a: str) -> int:
    return g.attr(a, "size", 0)


def halted(g: Graph, a: str) -> bool:
    return bool(g.attr(a, "halted"))


def halt(g: Graph, a: str) -> None:
    g.put(a, halted=True)


def finished(g: Graph, a: str) -> bool:
    """Ran off the end, or halted. The condition `tick` reports and `retire` requires."""
    return halted(g, a) or pc(g, a) >= size(g, a)


def steps_taken(g: Graph, a: str) -> int:
    return g.attr(a, "steps", 0)


def took_a_step(g: Graph, a: str) -> int:
    n = steps_taken(g, a) + 1
    g.put(a, steps=n)
    return n


# --- the call stack ------------------------------------------------------------------------------------
def stack(g: Graph, a: str) -> tuple:
    return g.attr(a, "stack", ())


def push(g: Graph, a: str, ret: int) -> None:
    g.put(a, stack=stack(g, a) + (ret,))


def pop(g: Graph, a: str):
    """The return address, or `None` when the stack is empty — `RET` from the top level, which runs off
    the end of the program rather than raising, exactly as it did when the stack was a Python list."""
    s = stack(g, a)
    if not s:
        return None
    g.put(a, stack=s[:-1])
    return s[-1]


# --- the registers -------------------------------------------------------------------------------------
def register(g: Graph, a: str, name: str):
    for r in g.targets(a, "register"):
        if g.attr(r, "name") == name:
            return r
    return None


def get_reg(g: Graph, a: str, name: str):
    """⚠ `None` for a register nothing has assigned — the same answer `regs.get(name)` gave, and the
    reason `isa._step.node()` exists to refuse writing one into an edge."""
    r = register(g, a, name)
    return None if r is None else g.attr(r, "value")


def set_reg(g: Graph, a: str, name: str, value) -> str:
    r = register(g, a, name)
    if r is None:
        r = g.mint("register", name=name)
        g.link(a, "register", r)
    g.put(r, value=value)
    return r


def registers(g: Graph, a: str) -> dict:
    """`{name: value}` — the dict `run` used to return, read back out of the graph."""
    return {g.attr(r, "name"): g.attr(r, "value") for r in g.targets(a, "register")}


# --- what the call created -------------------------------------------------------------------------------
def record_mint(g: Graph, a: str, node: str) -> None:
    """`NEW` minted a node, or a dispatched handler did. Recorded on the activation that caused it."""
    g.link(a, "minted", node)


def minted(g: Graph, a: str) -> tuple:
    """Every node this call created, its callees included, **sorted by id**.

    **⭐⭐ This replaces a whole-graph diff, and the diff was measuring the wrong thing.** `workbench.step`
    and `execution._replay` both wrapped an invocation in `before = set(g.nodes)` … `set(g.nodes) - before`,
    which answers *what nodes appeared anywhere* when the question is *what did this call add to the world*.
    That was an over-approximation from the start — a callee minting a hypothesis or a thread entry would
    have been counted as the call's output — and materialising the interpreter's own state turned the latent
    defect into a live one: a `focus`, its `head`s, an `activation` and its `register`s all appeared inside
    the window, and one of them was duly bound as an imagined result and type-checked as a `report`.

    ⚠ The fix is a record, not a filter over kinds. `NEW` is the only instruction that mints, `DISPATCH` is
    the only other way the world grows, and a callee is reached through its `caller` edge — so this is exact
    rather than a list of exclusions that would have to be kept in step with every module that mints. It is
    also one less whole-graph scan, which `labelling-error-and-when-tests-earn-their-place` records as the
    right shape of answer: **the fix was not to scan.**

    ⚠ Sorted by id, because that is what `sorted(set(g.nodes) - before)` gave and `execution._bind_minted`
    pairs imagined nodes with real ones **by kind and order**. Changing the order here would silently
    change which imagined node binds to which real one."""
    out = set(g.targets(a, "minted"))
    for callee in g.sources(a, "caller"):
        out |= set(minted(g, callee))
    return tuple(sorted(out))


def for_focus(g: Graph, focus_node_id: str):
    """The activation running on this focus, or `None`. `function.invoke` keeps the callee's activation
    (`retire=False`) precisely so a Python caller holding the returned focus can still ask what the call
    did — which is the same question `chain` answers from the inside."""
    got = g.sources(focus_node_id, "focus")
    return got[0] if got else None


# --- reading it back -----------------------------------------------------------------------------------
def focus_node(g: Graph, a: str):
    return g.target(a, "focus")


def doing(g: Graph, a: str):
    """The `instr` node this activation is stopped on, when its program is a stored function.

    ⭐ This is the second half of the test — *and can the system say what it was doing?* — and it needs no
    new record, because `function.define` already stores instructions as an ordered `instr` edge in the
    same order `load` returns them, labels included. So the program counter indexes it directly."""
    fn = g.target(a, "of")
    return None if fn is None else g.at(fn, "instr", pc(g, a))


def describe(g: Graph, a: str) -> str:
    """One line saying what this activation is in the middle of. Deliberately readable when the program is
    anonymous too — then it can only give the index, and says so rather than inventing a name."""
    where = g.attr(a, "label")
    fn = g.target(a, "of")
    if fn is not None:
        where = g.attr(fn, "name")
    i = doing(g, a)
    what = f"{g.attr(i, 'op')}" if i is not None else "?"
    if i is not None and g.attr(i, "op") == "LABEL":
        what = f"LABEL {g.attr(i, 'label')}"
    state = "halted" if halted(g, a) else ("finished" if finished(g, a) else what)
    return f"{where or 'anonymous'} @{pc(g, a)}/{size(g, a)}: {state}"


def chain(g: Graph, a: str) -> tuple:
    """This activation and everything that called it, innermost first. The ISA's own stack trace, which
    exists because `INVOKE` links the callee to its caller rather than nesting a Python frame invisibly."""
    out, seen = [], set()
    while a is not None and a not in seen:
        seen.add(a)
        out.append(a)
        a = g.target(a, "caller")
    return tuple(out)


# --- closing -------------------------------------------------------------------------------------------
def retire(g: Graph, a: str) -> None:
    """Drop a finished activation and its registers.

    ⚠ **Refused while it can still take a step**, so this cannot quietly discard a live computation —
    the whole point of materialising the state is that something can be *inside* it. The focus is not
    dropped: it belongs to whoever passed it in, and `function.invoke` hands it back to the caller."""
    if not finished(g, a):
        raise RuntimeError(
            f"refusing to retire {a}: it is at pc={pc(g, a)} of {size(g, a)} and can still take a step. "
            f"A live activation is exactly the state something may be stopped inside of.")
    for r in tuple(g.targets(a, "register")):
        g.unlink(a, "register", dst=r)
        g.drop(r)
    g.drop(a)


def scrap(g: Graph, a: str) -> None:
    """Drop a finished activation **and the focus it ran on**, heads included.

    ⚠ The difference from `retire` is ownership, not thoroughness. `retire` leaves the focus alone because
    `run`'s caller passed it in and gets it back; an imagined call's focus was minted for that call and is
    handed to nobody, so scrapping it is what makes `workbench.discard` able to say *back to the original
    size* — a workbench that leaves interpreter residue behind is not discarded, it is mostly discarded."""
    f = focus_node(g, a)
    retire(g, a)
    if f is not None:
        for h in tuple(g.targets(f, "head")):
            g.drop(h)
        g.drop(f)


__all__ = ["KINDS", "open_activation", "scrap", "pc", "set_pc", "size", "halted", "halt", "finished",
           "steps_taken", "took_a_step", "stack", "push", "pop", "register", "get_reg", "set_reg",
           "registers", "focus_node", "doing", "describe", "chain", "retire",
           "record_mint", "minted", "for_focus"]
