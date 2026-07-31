"""QUERY — asking, which is a goal like any other.

**⭐ A question IS a goal, and that is the whole design.** "Is Paul mortal?" is the goal *find out whether
Paul is mortal*; answering it is pursuing it. There is no second control loop, no query evaluator, no
separate ask/tell duality — `driver.pursue` already searches, and a question hands it the same constraint
nodes `goal.py` mints for anything else. The old engine had `cnl/query.py`, `ask_goal`, and a demand-driven
`CHAIN` alongside its forward chainer; all of that is one verb applied to data that already existed.

**⭐⭐ The plan IS the proof.** `driver` finds a plan rather than building one, and for a question that plan
is the derivation: the frame path from what is known to the claim being true. So an answer arrives with its
justification already in hand, as ordinary graph data, and nothing has to reconstruct *why* afterwards. This
is the property the old engine needed `provenance.py` and per-derivation `RECORD` to approximate.

**⚠ THE ONE THING THAT IS GENUINELY NEW: a derivation must never act.** Concluding something and doing
something are both "running a microfunction" here, and the difference cannot be left to intent. A function
is usable as a derivation only if it **provably never dispatches** — read off the stored body, transitively.
That is a *proof*, so it PRUNES (`driver.proposals(allow=…)`); it is not a guess, so it does not merely rank.
`README.md`'s standing rule is "rank a guess; prune a proof", and this is the second place a proof shows up.

**⚠ What the bar actually buys, stated precisely — the first version of this docstring overclaimed.** It is
tempting to say that without it, asking "is the file there?" could delete something. During `ask` that is
already false: the search runs on a workbench, and `dispatch.service` refuses any imagined target, so an
impure function cannot reach the world *while planning*. What it does instead is **raise**, which makes the
question unanswerable rather than unsafe. Measured by planting exactly that: removing the bar turns a clean
`yes` into `Imagined: refusing to dispatch 'registrar'`.

The real exposure is one step later, at **`settle`** — which replays the proof against the *real* graph,
where dispatch fires for real. A proof containing an impure step sends the mail at the moment you decide to
keep the answer. So the bar does two distinct jobs, and both are worth having: it keeps the search from
crashing on a candidate it was never entitled to try, and it is what makes `settle` **safe by construction**
rather than by the caller inspecting the proof first. The two guards are layered, not redundant — the
workbench one is the last line of defence, this one is the one that lets questions work at all.

**Three answers, and the third is not a failure.**

| verdict | means |
|---|---|
| `yes` | a derivation was found — `proof` is the path that establishes it |
| `no` | the claim is *refuted*: something incompatible with it holds now |
| `unknown` | neither; the search was exhausted without settling it |

⚠ `unknown` is the honest default and `no` is the strong claim, which is the open-world reading. A searcher
that failed to find a derivation has learned about its own library, not about the world. `assume_complete=True`
buys the closed-world reading — *if it were true I would have found it* — and it is a **stance**, exactly the
`FirmwarePolicy` CWA/OWA dial the old engine put in data rather than in code. It is a parameter here for the
same reason: it is an opinion, and opinions do not belong wired into a mechanism.

**Refutation is checked, never searched for.** `refutes` asks whether the graph *now* holds something
incompatible — an attribute constraint wanting a value the node already has differently. ⚠ Deliberately
narrow: absence of an edge refutes nothing in an open world, so a link or type constraint can only ever come
back `unknown` from a failed search. Widening this without the stance would quietly convert "I did not find
it" into "it is false", which is the single most common way a reasoner starts lying.

**Why-questions are goals too.** `why` asks for a *causal* explanation of something that holds, and the
answer is the same object read differently: the derivation path, with each step naming the function that
made the next thing true. `explain` renders it. A step is a cause here in the only sense this engine can
honour — *this ran, and afterwards that held* — which is why `explain` says "because" and never "therefore".
"""
from __future__ import annotations

from . import driver as D
from . import execution as X
from . import function as fn
from . import goal as G
from . import isa
from . import thread as T
from . import workbench as W
from .graph import Graph

YES, NO, UNKNOWN = "yes", "no", "unknown"


# --- the bar: what may be used to conclude -------------------------------------------------------
def is_pure(g: Graph, name: str, *, _seen: frozenset | None = None) -> bool:
    """Whether this function provably never reaches the world. **Read off the stored body, transitively.**

    ⚠ **Conservative in the direction that refuses, which is the opposite of `driver.establishes`.** That is
    an over-approximation built to ORDER candidates, so it is safe to overstate what a function might do.
    This one licences *running* something to answer a question, so an unreadable body must come back
    `False`: a maybe-dispatching function is barred, and the cost of being wrong is a question that goes
    unanswered rather than a question that sends an email.

    `INVOKE` with a statically readable target recurses; a computed target is refused, because nothing can
    be proved about a callee we cannot name. Mocks are irrelevant — a mock is an assumption about how a real
    call turns out, and assumptions are not run for real."""
    seen = _seen or frozenset()
    if name in seen:
        return True                     # already being proved further up; recursion adds no new dispatch
    try:
        _params, program = fn.load(g, name)
    except Exception:
        return False                    # cannot read it, cannot vouch for it
    for ins in program:
        if isinstance(ins, str):
            continue
        if ins.op == "DISPATCH":
            return False
        if ins.op == "INVOKE":
            target = ins.args[1] if len(ins.args) > 1 else None
            callee = target.name if isinstance(target, isa.F) else target
            if not isinstance(callee, str) or fn.find(g, callee) is None:
                return False            # a computed callee: unprovable, so refused
            if not is_pure(g, callee, _seen=seen | {name}):
                return False
    return True


def derivations(g: Graph) -> tuple:
    """The functions usable to conclude something — the library a question is allowed to reason with."""
    return tuple(n for n in fn.names(g)
                 if fn.mocks_target(g, n) is None and is_pure(g, n))


# --- refutation ----------------------------------------------------------------------------------
def refutes(g: Graph, c: str, *, view=None) -> bool:
    """Whether the world holds something INCOMPATIBLE with this constraint — a positive `no`.

    ⚠ Only an attribute constraint can be refuted this way, and that is a real limit rather than an
    oversight: a node carrying `colour='red'` genuinely contradicts *`colour` must be `blue`*, because an
    attribute is single-valued. A missing edge contradicts nothing in an open world — the graph not saying
    Paul is mortal is not the graph saying he is not. Treating absence as refutation is what `assume_complete`
    is for, and keeping the two apart is what stops a silent slide from ignorance into denial."""
    view = view or (lambda n: n)
    if g.attr(c, "sort") != "attr":
        return False
    subject = view(g.target(c, "subject"))
    if subject is None:
        return False
    key = g.attr(c, "key")
    return key in g.attrs.get(subject, {}) and g.attr(subject, key) != g.attr(c, "value")


# --- asking --------------------------------------------------------------------------------------
def ask(g: Graph, question: str, thread: str, subject: str, *, assume_complete: bool = False,
        max_steps: int = 60, max_depth: int = 4, **kw) -> dict:
    """Answer a question by pursuing it. `question` is an ordinary goal node.

    Returns `{verdict, proof, why, steps, workbench, goal}`. `proof` is the derivation path on success —
    `execution.path_to`'s output, which is to say **a plan**, replayable by `execute` because a derivation
    is a sequence of applications like any other.

    ⚠ **Nothing is concluded in reality here.** `pursue` searches on a workbench, so answering leaves the
    world untouched even though every step of the derivation "ran". To keep what was worked out, replay the
    proof with `settle`. Keeping those apart matters: a question that silently saturated the graph with
    everything it happened to derive on the way would make asking a destructive act."""
    already = G.unmet(g, question, under=subject)
    if not already:
        T.attend(g, thread, question, why="asked", note="already known")
        return {"verdict": YES, "proof": (), "why": "already known", "steps": 0,
                "workbench": None, "goal": question}

    for c in already:
        if refutes(g, c):
            T.attend(g, thread, question, why="asked", note="refuted by what is already known")
            # ⚠ Say what actually HOLDS, not what was wanted. Rendering the constraint here read
            # "refuted: zed.mortal = True" — the wanted value, printed as though it were the finding.
            subject, key = g.target(c, "subject"), g.attr(c, "key")
            return {"verdict": NO, "proof": (), "steps": 0, "workbench": None, "goal": question,
                    "why": "refuted: %s.%s is already %r, not %r" % (
                        g.attr(subject, "label") or subject, key,
                        g.attr(subject, key), g.attr(c, "value"))}

    allowed = frozenset(derivations(g))
    report = D.pursue(g, question, thread, subject, max_steps=max_steps, max_depth=max_depth,
                      allow=allowed.__contains__, **kw)
    if report.get("found"):
        return {"verdict": YES, "proof": report.get("plan", ()), "steps": report.get("steps", 0),
                "workbench": report.get("workbench"), "frame": report.get("frame"), "goal": question,
                "why": "derived in %d step(s)" % report.get("length", 0)}

    # ⚠ The search is exhausted, and what that licences depends entirely on the stance.
    # ⚠ ASCII only in anything that gets printed. §5j: a non-ASCII marker made the selftest report
    # unpipeable on a cp1252 console, and the same glyph reappeared here the first time.
    verdict = NO if assume_complete else UNKNOWN
    why = ("nothing known makes it true, and the library is assumed complete"
           if assume_complete else "no derivation found - this says nothing about the world")
    return {"verdict": verdict, "proof": (), "steps": report.get("steps", 0),
            "workbench": report.get("workbench"), "goal": question, "why": why}


def settle(g: Graph, answer: dict) -> dict:
    """Replay a `yes` answer's proof against the real graph, so what was worked out is KEPT.

    Safe by construction rather than by care: every step came from `derivations`, so none of them can reach
    the world — this commits conclusions, never effects. Returns `execution.execute`'s report."""
    if answer["verdict"] != YES or not answer["proof"]:
        return {"ran": (), "completed": True, "deviation": None}
    return X.execute(g, answer["workbench"], answer["frame"])


# --- why -----------------------------------------------------------------------------------------
def steps_of(g: Graph, answer: dict) -> tuple:
    """The proof's frame path read back as `(function, {param: real node})` per step.

    ⚠ A plan is a path of FRAMES, and the step that reached each one hangs off it as `via`. Bindings point
    at *mappings*, never raw nodes — that indirection is what makes a plan replayable — so each is resolved
    back to the real node it stands for, which is what a reader of an explanation is asking about."""
    out = []
    for frame in answer.get("proof", ())[1:]:          # frame 0 is the starting world, reached by nothing
        tr = g.target(frame, "via")
        if tr is None:
            continue
        bound = {}
        for b in g.targets(tr, "arg"):
            m = g.target(b, "mapping")
            bound[g.attr(b, "param")] = (W.resolve(g, m) or W.image_of(g, m)) if m else None
        out.append((g.attr(tr, "function"), bound))
    return tuple(out)


def why(g: Graph, answer: dict) -> tuple:
    """The causal chain behind a `yes`, as `(function, bindings, effects, unknown)` per step.

    ⭐ This is not a second record. It is the proof read as *cause*: each step names the function that ran
    and what its body establishes. "Why" being a goal means its answer was already produced by answering the
    original question — there is nothing extra to search for."""
    return tuple((name, bound) + D.establishes(g, name) for name, bound in steps_of(g, answer))


def explain(g: Graph, answer: dict) -> str:
    """A readable causal explanation. ⚠ Says "because", never "therefore" — a step is a cause here only in
    the sense the engine can honour, that it ran and afterwards something held."""
    if answer["verdict"] != YES:
        return f"{answer['verdict']}: {answer['why']}"
    if not answer["proof"]:
        return "yes, because it was already known"
    lines = ["yes, because:"]
    for name, bindings, _effects, unknown in why(g, answer):  # noqa: B007 — shape documented in `why`
        who = ", ".join(f"{p}={g.attr(n, 'label') or n}" for p, n in sorted(bindings.items()))
        lines.append(f"  {name}({who})" + ("   [partly unreadable]" if unknown else ""))
    return "\n".join(lines)


def describe(g: Graph, answer: dict) -> str:
    return f"{answer['verdict'].upper()} - {answer['why']} ({answer['steps']} step(s) considered)"


__all__ = ["YES", "NO", "UNKNOWN", "is_pure", "derivations", "refutes", "ask", "settle",
           "why", "explain", "describe"]
