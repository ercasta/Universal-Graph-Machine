"""THE OUTER LOOP — one agenda, one tick, and nothing uninterruptible.

**The principle, which is the user's and is sharper than what the engine was built toward** (the design notes):

> There is a **single outer-outer control loop**. Planning is not a real execution control loop — its
> control loop is *represented as data*, and the outer loop always interleaves and ticks. No seams, no
> fixpoint procedures that cannot be interrupted.

⚠ **This is not a new direction; it completes one already taken.** `run_bank`'s blind fixpoint was retired
for exactly this reason — a fixpoint is a computation you cannot be inside of — and `agent-not-theorem-
prover` rejects eager exhaustive completion on the same grounds. This module is that decision applied
without exception, at every level.

## What made it small

Almost nothing here is mechanism, and that is the evidence the preceding slices were the right ones. Every
control loop in the engine had already become a **node plus a `step`**:

| task | one primitive step is | state |
|---|---|---|
| `activation` | one ISA instruction | `activation.py` |
| `search` | one imagined state | `search.py` |
| `replay` | one real action | `execution.py` |
| `pursuit` | one step of plan/act/check/replan | `driver.py` |

So the outer loop is an **ordered agenda** and a dispatch on `kind`. Adding a kind of work means writing
its `step`, not touching this file.

⭐ **Round-robin, and the rotation is the data.** `tick` takes the task at the head of the agenda, advances
it by one step, and puts it back at the tail — so interleaving is not a policy this module implements but
the ordinary consequence of the agenda being an ordered edge. Two goals pursued at once really do
interleave, one primitive step each, and *which one is next* is a question anybody can ask of the graph.

## ⚠ What must NOT become uniform: irreversibility

Advancing a search costs time; advancing a replay can send an email. `dispatch.py` calls that asymmetry the
single most important safety property in the design, and a uniform cycle is exactly the thing most likely
to erode it. So a tick **reports the verb it performed** — `imagine`, `look`, `act`, `run` — and `until=`
lets a driver stop *before* the first irreversible one. Rank a guess, prune a proof: *"this cannot be
undone"* is nearer a proof.

⚠ **`dispatch` is not a seam to remove.** Once a handler is called the world is executing, not us. The
loop can decline to take the step; it cannot make the step reversible.

## ⚠ What this does NOT do

**It does not flatten the goal.** A game loop *simulates*; this *pursues*. `goal.unmet` is the gradient and
it is the entire reason guidance works (2 imagined states against 67). The loop's shape governs *what may
happen at a step*; the goal still governs *how the step is chosen*.
"""
from __future__ import annotations

from .graph import Graph

KINDS = ("loop",)

#: The verbs of §6b, as they arise. `forget` is the slower clock, and it is an ordinary task on this
#: agenda like anything else; `commit` / `refuse` are terminal and already exist as outcomes, not as steps.
IMAGINE, LOOK, ACT, RUN, FORGET = "imagine", "look", "act", "run", "forget"

#: Verbs that reach the world. Nothing after one of these can be undone.
IRREVERSIBLE = frozenset({ACT})


def open_loop(g: Graph, label: str = "loop") -> str:
    l = g.mint("loop", label=label, ticks=0)
    return l


def schedule(g: Graph, loop: str, task: str, why: str | None = None, *, not_before=None) -> str:
    """Put a task on the agenda. Appended, so the order is the order things were asked for.

    ⭐⭐ **`not_before` is a TIMER, and it is the first thing that has ever made the agenda a choice.**
    *"Stop cooking the pasta after ten minutes"* — a procedure installs it on itself, so the payload is an
    ordinary task and the gate is an ordinary moment node. Nothing new is represented: `clock.moment(at=…)`
    already existed, and this is the edge that lets the loop honour one.

    ⚠ The gate lives on the TASK, not on the agenda edge, so *"when may this run?"* is a property of the
    work rather than of the queue it happens to be sitting in."""
    if not_before is not None:
        g.link(task, "not_before", not_before)
    # ⚠⚠ **TWO DIFFERENT FACTS WERE RIDING ON ONE EDGE, and it made a question unanswerable exactly when
    # it mattered.** `loop -task-> t` is TURN ORDER: `tick` unlinks the head before advancing it and
    # re-appends it at the tail, so **a running task is not on the agenda at all**. *"Which loop do I
    # belong to?"* is a different, stable fact, and a body that wants to schedule its own follow-up
    # (`_after`) asks it precisely while running. So membership gets its own edge.
    if loop not in g.targets(task, "on"):
        g.link(task, "on", loop)
    g.link(loop, "task", task, **({"why": why} if why else {}))
    return task


def due(g: Graph, task: str, *, at=None) -> bool:
    """May this task run yet? Ungated work is always due."""
    from . import clock as C
    gate = g.target(task, "not_before")
    return True if gate is None else C.arrived(g, gate, at=at)


def loop_of(g: Graph, task: str):
    """Which agenda is this task on? ⚠ **Derived from the reverse index, never passed** — the same
    argument `dispatch._thread_of` makes: threading a `loop=` parameter down through every caller would be
    plumbing for something the graph already answers."""
    holders = g.targets(task, "on")
    return holders[0] if len(holders) == 1 else None


def _after(g: Graph, act, seconds, function: str, subject: str):
    """`NATIVE R(t) "after" 600 "take_the_pasta_off" F(pot)` — **a procedure installing its own timer.**

    ⭐⭐ This is the user's case in one line: *"stop cooking the pasta after ten minutes"*, where the
    thing that knows about the ten minutes is the **cooking procedure**, not its caller. Nothing new is
    represented — `clock.moment(at=…)` is the gate, an activation is the payload, and `schedule` already
    honours both. What was missing was a way for a running body to reach the agenda it is *on*.

    ⚠ It finds that agenda from its **own activation**, which is why natives receive `act`. A body that
    had to be told which loop it was running on would be a body that could not be moved.

    ⚠ Refused loudly when the caller is not on an agenda: scheduling into nowhere would leave a timer that
    can never fire, which is indistinguishable from one that is merely early."""
    from . import clock as C, function as fn
    from .focus import Focus
    from .isa import Machine
    here = loop_of(g, act) if act is not None else None
    if here is None:
        raise ValueError(
            "`after` was called by something that is not on an agenda, so there is nothing to schedule "
            "onto. A timer installed nowhere can never fire.")
    if fn.find(g, function) is None:
        raise ValueError(f"`after` names {function!r}, which is not a function in this library")
    _params, program = fn.load(g, function)
    param = fn.subject_param(g, function)
    task = Machine(program).start(g, Focus(g).open(param, subject),
                                  of=fn.find(g, function), label=function)
    when = C.moment(g, at=C._wallclock.time() + float(seconds), label=f"{function} is due")
    schedule(g, here, task, why=f"in {seconds}s", not_before=when)
    return task


def agenda(g: Graph, loop: str) -> tuple:
    """Everything waiting, **in turn order** — the head is what `tick` will advance next."""
    return g.targets(loop, "task")


def ticks(g: Graph, loop: str) -> int:
    return g.attr(loop, "ticks", 0)


# --- what one step of each kind of task is ------------------------------------------------------------
def finished(g: Graph, task: str) -> bool:
    # ⭐⭐ **`stop` is ordinary data, and it means the same thing for every kind of task.** This is what
    # lets the system act on a judgement about *itself*: everything about a running computation — how many
    # states a search has imagined, which phase a pursuit is in, which instruction an activation is on — is
    # already readable, and a watcher is just another task on this agenda. What was missing was a way for
    # that watcher to *do* something, and one uniform attribute is it.
    #
    # ⚠ **Stopping a `replay` is the valuable case and the dangerous one.** It means *do not take the next
    # irreversible action* — which is exactly what a monitor should be able to say, and it leaves a plan
    # half-carried-out. That is honest rather than new: a divergence already leaves one, and `execution`'s
    # standing rule is that nothing is undone, because real effects have already left the graph.
    if g.attr(task, "stop"):
        return True
    kind = g.kind(task)
    if kind == "activation":
        from . import activation as A
        return A.finished(g, task)
    if kind == "replay":
        from . import execution as X
        return X.finished(g, task)
    if kind == "search":
        return bool(g.attr(task, "done"))
    if kind == "pursuit":
        return g.attr(task, "phase") == "done"
    if kind == "forgetting":
        from . import forget as FG
        return FG.finished(g, task)
    raise ValueError(f"{task}: nothing here knows how to advance a {kind!r}")


def describe(g: Graph, task: str) -> str:
    """What this task is in the middle of. Every kind can answer, which is the half of §6b's test that is
    easy to forget: being able to *stop* is worth nothing if the system cannot say what it stopped in."""
    kind = g.kind(task)
    if kind == "activation":
        from . import activation as A
        return A.describe(g, task)
    if kind == "pursuit":
        from . import driver as D
        return D.describe_pursuit(g, task)
    if kind == "search":
        from . import search as S
        return (f"searching for {g.attr(g.target(task, 'goal'), 'label')!r}: "
                f"{S.steps_taken(g, task)} imagined, {len(S.frontier(g, task))} on the frontier")
    if kind == "replay":
        return (f"carrying out a plan: step {g.attr(task, 'at', 0)} of {g.count(task, 'frame') - 1}"
                + (", diverged" if g.target(task, "deviation") is not None else ""))
    if kind == "forgetting":
        from . import forget as FG
        return FG.describe(g, task)
    return f"{kind} {task}"


def verb_of(g: Graph, task: str) -> str:
    """What kind of step advancing this task would be, **asked before it is taken** — which is the only
    time the answer is useful, because `act` is the one that cannot be taken back.

    ⚠ For an `activation` this reads the instruction the program counter is on. A `DISPATCH` is `look` or
    `act` according to whether the tool was registered as observing, which is the distinction the design notes
    flagged as missing: the veto and commit machinery treated a directory scan and a sent email alike."""
    kind = g.kind(task)
    if kind == "search":
        return IMAGINE
    if kind == "replay":
        return ACT
    if kind == "forgetting":
        return FORGET
    if kind == "pursuit":
        from . import driver as D
        # ⚠⚠ **SENSING REACHES THE WORLD, so it must never be reported as `imagine`.** It was, and that is
        # precisely the distinction this function exists for: a driver reads the verb to decline a tick
        # *before* something irreversible, and a sensing tick performs a real `DISPATCH`. It is `look`
        # rather than `act` because the tool is registered `observes=True` — the same asymmetry the
        # activation branch below already draws.
        if g.attr(task, "phase") == D.SENSING:
            return LOOK
        sub = _subtask(g, task)
        return verb_of(g, sub) if sub is not None else IMAGINE
    if kind == "activation":
        from . import activation as A, dispatch as D, function as fn
        i = A.doing(g, task)
        if i is None or g.attr(i, "op") != "DISPATCH":
            return RUN
        tool = next((g.attr(a, "value") for a in g.targets(i, "arg")
                     if g.attr(a, "form") == "literal"), None)
        _ = fn                                     # the program is stored; the tool name is a literal
        return LOOK if tool is not None and D.observes(g, tool) else ACT
    return RUN


def _subtask(g: Graph, pursuit: str):
    from . import driver as D
    phase = g.attr(pursuit, "phase")
    if phase == D.PLANNING:
        return g.target(pursuit, "search")
    if phase in (D.ACTING, D.RECOVERING):
        got = g.targets(pursuit, "replay")
        return got[-1] if got else None
    return None


def advance(g: Graph, task: str, **hooks) -> bool:
    """**One primitive step of whatever this is.** `True` while there is more to do.

    ⚠ There is no loop in here and there must never be one. The whole claim of this module is that the
    only `while` in the system is the one a *driver* writes around `tick`, where something can stop it."""
    kind = g.kind(task)
    if kind == "activation":
        from . import activation as A, function as fn
        from .isa import Machine
        of = g.target(task, "of")
        if of is None:
            # ⚠ Loud, per the standing discipline. An anonymous program is one the loop cannot reconstruct,
            # so it cannot be resumed by anything but the Python caller that holds it — which is precisely
            # the island this arc exists to remove. Say so rather than skipping it.
            raise ValueError(
                f"{task}: this activation has no `of`, so its program exists only in Python. Only a "
                f"STORED function can be driven by the outer loop — that is what makes it resumable.")
        _params, program = fn.load(g, g.attr(of, "name"))
        _ = A
        return Machine(program).tick(g, task)
    if kind == "search":
        from . import driver as D
        return D.step(g, task, **hooks) is None
    if kind == "replay":
        from . import execution as X
        return X.step(g, task)
    if kind == "forgetting":
        from . import forget as FG
        return FG.step(g, task)
    if kind == "pursuit":
        from . import driver as D
        return D.pursuit_step(g, task, **hooks)
    raise ValueError(f"{task}: nothing here knows how to advance a {g.kind(task)!r}")


# --- the loop -----------------------------------------------------------------------------------------
def tick(g: Graph, loop: str, *, at=None, **hooks):
    """Advance the task at the head of the agenda by **one** step and rotate it to the back.

    Returns a record of what it did — `None` when the agenda is empty. A finished task leaves the agenda;
    it is not dropped from the graph, because a finished computation is a record, not rubbish."""
    here = agenda(g, loop)
    if not here:
        return None
    # ⭐⭐ **THE FIRST SELECTION THE AGENDA HAS EVER MADE.** It was `here[0]`, unconditionally — round-robin
    # with no content. A timer forces a choice: take the first task that is *due*.
    #
    # ⚠⚠ **Waiting is REPORTED, never spun on.** If everything is gated, rotating the head to the back and
    # trying again would busy-loop until the clock caught up — burning the tick budget and looking like
    # progress. So the tick returns a record saying it waited and what it is waiting for. A driver can then
    # sleep, or do something else, which is a decision only a driver can make.
    idx = next((i for i, t in enumerate(here) if due(g, t, at=at)), None)
    if idx is None:
        return {"task": None, "kind": None, "verb": None, "more": True, "waiting": tuple(here),
                "doing": f"waiting on {len(here)} timer(s)", "retired": False}
    task = here[idx]
    g.unlink(loop, "task", index=idx)
    if finished(g, task):
        return {"task": task, "kind": g.kind(task), "verb": None, "more": False,
                "doing": describe(g, task), "retired": True}
    verb = verb_of(g, task)
    doing = describe(g, task)
    more = advance(g, task, **hooks)
    g.put(loop, ticks=ticks(g, loop) + 1)
    if more:
        g.link(loop, "task", task)                 # ⭐ to the BACK — interleaving, as ordinary data
    return {"task": task, "kind": g.kind(task), "verb": verb, "more": more,
            "doing": doing, "now": describe(g, task), "retired": not more}


def run(g: Graph, loop: str, *, max_ticks: int = 10_000, until=None, at=None, **hooks) -> dict:
    """Tick until the agenda empties, the budget runs out, or `until` says stop. A **driver**, and the
    only `while` above the primitives.

    `until(record) -> bool` is consulted **after** each tick. To stop *before* something irreversible, do
    not use this — read `verb_of` on the head of the agenda and simply decline to call `tick`. That
    asymmetry is deliberate: declining to act has to be something a caller does, not something a loop does
    on its behalf.

    ⚠ `max_ticks` is a budget, and it is now the ONLY one above the ISA's own. The design notes' argument for
    that: three independent stand-ins in three corners cannot be reasoned about together, and *"have I
    spent enough on this?"* is a decision that needs one place to live."""
    done = []
    for _ in range(max_ticks):
        rec = tick(g, loop, at=at, **hooks)
        if rec is None:
            return {"ticks": ticks(g, loop), "did": tuple(done), "why": "the agenda is empty",
                    "agenda": ()}
        done.append(rec)
        # ⚠ Nothing is due and nothing will become due without the clock moving, so stop rather than
        # spending the rest of the budget discovering that again.
        if rec.get("waiting"):
            return {"ticks": ticks(g, loop), "did": tuple(done), "why": "waiting on a timer",
                    "agenda": agenda(g, loop)}
        if until is not None and until(rec):
            return {"ticks": ticks(g, loop), "did": tuple(done), "why": "asked to stop",
                    "agenda": agenda(g, loop)}
    return {"ticks": ticks(g, loop), "did": tuple(done), "why": f"budget of {max_ticks} ticks",
            "agenda": agenda(g, loop)}


from . import native as _N
_N.register("after", _after)

__all__ = ["KINDS", "loop_of", "IMAGINE", "LOOK", "ACT", "RUN", "FORGET", "IRREVERSIBLE",
           "open_loop", "schedule", "due", "agenda", "ticks", "finished", "describe", "verb_of",
           "advance", "tick", "run"]
