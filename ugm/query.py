"""Query — asking, which is a goal like any other.

"Is Paul mortal?" is the goal find out whether Paul is mortal, and answering it is pursuing it.
There is no second control loop, no query evaluator and no separate ask/tell duality: the driver
already searches, and a question hands it the same constraint nodes any other goal is made of.

The plan is the proof. The driver finds a plan rather than building one, and for a question that
plan is the derivation — the frame path from what is known to the claim being true. An answer
therefore arrives with its justification already in hand, as ordinary graph data, and nothing has
to reconstruct why afterwards.

A derivation must never act. Concluding something and doing something are both running a rule
here, and the difference cannot be left to intent. A function is usable as a derivation only if
it provably never dispatches, read off the stored body and transitively through its calls. That
is a proof, so it prunes rather than merely ranking.

What the bar actually buys, stated precisely. During `ask` an impure function could not reach the
world anyway: the search runs on a workbench and the dispatcher refuses any imagined target, so
what such a function does instead is raise, which makes the question unanswerable rather than
unsafe. The real exposure is one step later, at `settle`, which replays the proof against the
real graph where dispatch fires for real — a proof containing an impure step would send the mail
at the moment you decide to keep the answer. So the bar does two jobs: it keeps the search from
crashing on a candidate it was never entitled to try, and it makes `settle` safe by construction
rather than by the caller inspecting the proof first.

Three answers, and the third is not a failure.

| verdict | means |
|---|---|
| `yes` | a derivation was found — the proof is the path that establishes it |
| `no` | the claim is refuted: something incompatible with it holds now |
| `unknown` | neither; the search was exhausted without settling it |

`unknown` is the honest default and `no` is the strong claim, which is the open-world reading. A
searcher that failed to find a derivation has learned about its own library, not about the world.
Assuming completeness buys the closed-world reading — if it were true I would have found it — and
it is a stance passed per question, because it is an opinion and opinions do not belong wired
into a mechanism.

Refutation is checked, never searched for. `refutes` asks whether the graph now holds something
incompatible, such as an attribute constraint wanting a value the node already has differently.
It is deliberately narrow: absence of an edge refutes nothing in an open world, so a link or type
constraint can only come back unknown from a failed search. Widening this without the stance
would quietly convert "I did not find it" into "it is false", which is the most common way a
reasoner starts lying.

Why-questions are goals too. `why` asks for a causal explanation of something that holds, and the
answer is the same object read differently: the derivation path, with each step naming the
function that made the next thing true. A step is a cause in the only sense this engine can
honour — this ran, and afterwards that held — which is why an explanation says "because" and
never "therefore".

See `docs/planning.md`.
"""
from __future__ import annotations

from . import access, fact as FACT
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
    """Whether this function provably never reaches the world. Read off the stored body, transitively.

    Conservative in the direction that refuses, which is the opposite of `driver.establishes`. That is
    an over-approximation built to order candidates, so it is safe to overstate what a function might do.
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
        if access.as_opcode(ins) is not None:
            # A call to the closed access vocabulary is a graph operation wearing a name, and it is pure
            # for the same reason `GET` is. Recursing into it would refuse every properly written rule in
            # the library: `slot_of`'s body ends in a call *through a register* — the resolver, chosen by
            # the ambient context — and a computed callee is exactly what this refuses.
            #
            # Reading the closed set is legitimate because it is closed, which is the third place that
            # argument earns its keep (`access.as_opcode`, `driver._walk`, here). What it rests on is
            # stated so it can be checked: no member's body contains `DISPATCH`, and the one computed call
            # in each reaches a *resolver*. A resolver that dispatched would be a layer violation rather
            # than a surprise — and `dispatch.service` still refuses an imagined target underneath it.
            continue
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
    """Whether the world holds something incompatible with this constraint — a positive `no`.

    Only an attribute constraint can be refuted this way, and that is a real limit rather than an
    oversight: a node carrying `colour='red'` genuinely contradicts *`colour` must be `blue`*, because an
    attribute is single-valued. A missing edge contradicts nothing in an open world — the graph not saying
    Paul is mortal is not the graph saying he is not. Treating absence as refutation is what `assume_complete`
    is for, and keeping the two apart is what stops a silent slide from ignorance into denial."""
    view = view or (lambda n: n)
    if g.attr(c, "sort") != "attr":
        return False
    subject = view(FACT.participant(g, c, 1))
    if subject is None:
        return False
    key = g.attr(c, "key")
    # Refuting a `>=` constraint is *not* `got != want` — the value may differ and still satisfy it.
    # Equality was assumed here while comparisons lived only in `type` blocks; with the operators widened
    # to goals, this had to become "the slot is present and the comparison fails".
    from .types import compare
    return key in g.attrs.get(subject, {}) and \
        not compare(g.attr(c, "op") or "==", g.attr(subject, key), g.attr(c, "value"))


# --- asking --------------------------------------------------------------------------------------
def ask(g: Graph, question: str, thread: str, subject: str, *, assume_complete: bool = False,
        max_steps: int = 60, max_depth: int = 4, **kw) -> dict:
    """Answer a question by pursuing it. `question` is an ordinary goal node.

    Returns `{verdict, proof, why, steps, workbench, goal}`. `proof` is the derivation path on success —
    `execution.path_to`'s output, which is to say a plan, replayable by `execute` because a derivation
    is a sequence of applications like any other.

    Nothing is concluded in reality here. `pursue` searches on a workbench, so answering leaves the
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
            # Say what actually holds, not what was wanted. Rendering the constraint here read
            # "refuted: zed.mortal = True" — the wanted value, printed as though it were the finding.
            subject, key = FACT.participant(g, c, 1), g.attr(c, "key")
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

    # The search is exhausted, and what that licences depends entirely on the stance.
    # Ascii only in anything that gets printed.: a non-ascii marker made the selftest report
    # unpipeable on a cp1252 console, and the same glyph reappeared here the first time.
    verdict = NO if assume_complete else UNKNOWN
    why = ("nothing known makes it true, and the library is assumed complete"
           if assume_complete else "no derivation found - this says nothing about the world")
    return {"verdict": verdict, "proof": (), "steps": report.get("steps", 0),
            "workbench": report.get("workbench"), "goal": question, "why": why}


def settle(g: Graph, answer: dict, thread: str | None = None) -> dict:
    """Replay a `yes` answer's proof against the real graph, so what was worked out is kept.

    Safe by construction rather than by care: every step came from `derivations`, so none of them can reach
    the world — this commits conclusions, never effects. Returns `execution.execute`'s report.

    Recording on the thread is what makes `why` answerable later, and it was missing at first. Without
    it a fact could be derived, committed, and then be unexplainable ten minutes afterwards — the engine
    would know Paul is mortal and have no account of how it came to think so. The entries are marked `done`,
    the same marker `conflict.py` uses to separate what really ran from what was merely imagined during the
    search; a thread full of considered-but-abandoned proposals would make "why" answer with roads not
    taken."""
    if answer["verdict"] != YES or not answer["proof"]:
        return {"ran": (), "completed": True, "deviation": None}
    report = X.execute(g, answer["workbench"], answer["frame"])
    if thread is not None:
        ran = set(report.get("ran", ()))
        for name, bound in steps_of(g, answer):
            if name in ran:
                T.applied(g, thread, name, bound, why="settled a question",
                          for_goal=answer["goal"], done=True)
    return report


def history_for(g: Graph, thread: str, c: str) -> tuple:
    """The applications that really ran and could have established this constraint. The honest "why".

    History, never reconstruction. This looks only at entries marked `done`, and it matches on the
    *roles* an application's function establishes resolved against that application's own bindings — so
    `conclude_mortal(p=paul)` explains *paul* being mortal and says nothing about anyone else. Anything less
    specific would offer a plausible-looking cause for a fact it did not produce."""
    from . import application as ap
    out = []
    sort = g.attr(c, "sort")
    want_label = g.attr(c, "label") if sort == "link" else g.attr(c, "key")
    kind = {"link": "link", "attr": "attr"}.get(sort)
    subject, obj = FACT.participant(g, c, 1), FACT.participant(g, c, 2)
    for entry in T.entries(g, thread):
        if g.kind(entry) != "application" or not g.attr(entry, "done"):
            continue
        name = g.attr(entry, "function") or g.attr(entry, "name")
        if name is None:
            continue
        bound = ap.bindings_of(g, entry)
        effects, _unknown = D.establishes(g, name)
        for k, lbl, sp, op in effects:
            if kind is not None and (k != kind or lbl != want_label):
                continue
            if D.role_node(g, bound, sp) != subject:
                continue
            if obj is not None and D.role_node(g, bound, op) != obj:
                continue
            out.append((entry, name, bound))
            break
    return tuple(out)


# --- why -----------------------------------------------------------------------------------------
def steps_of(g: Graph, answer: dict) -> tuple:
    """The proof read back as `(function, {param: real node})` per step.

    A proof *is* a plan, so this is `driver.plan_bindings` — one implementation, deliberately, so that a
    derivation and a plan of action read identically. They are the same object arrived at by different
    verbs, and two readers would eventually disagree about one of them."""
    return D.plan_bindings(g, answer.get("proof", ()))


def why(g: Graph, answer: dict) -> tuple:
    """The causal chain behind a `yes`, as `(function, bindings, effects, unknown)` per step.

    This is not a second record. It is the proof read as *cause*: each step names the function that ran
    and what its body establishes. "Why" being a goal means its answer was already produced by answering the
    original question — there is nothing extra to search for."""
    return tuple((name, bound) + D.establishes(g, name) for name, bound in steps_of(g, answer))


def explain(g: Graph, answer: dict) -> str:
    """A readable causal explanation. Says "because", never "therefore" — a step is a cause here only in
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


def account(g: Graph, question: str, thread: str, subject: str = "root") -> str:
    """Why does this hold? — the causal explanation, answered from history where there is one.

    Three genuinely different situations, and the whole value here is refusing to blur them:

    * it does not hold — then there is no "why". The honest response redirects to asking whether it
      *could*, which is a different question with a different answer.
    * it holds and something here made it hold — `history_for` names the application. This is the only
      case that is really a cause.
    * it holds and nothing here made it hold — it was given, not derived. Saying so is the answer.

    The tempting fourth behaviour is deliberately absent: re-deriving it hypothetically. For a fact
    that is already true, a fresh search would answer *"here is a way this could follow"* — which is a
    perfectly good question (`ask` it of a world where the fact is absent) and a lie when presented as
    the reason something actually happened. An engine that manufactures plausible history is worse than one
    that admits it kept none, because nothing downstream can tell the two apart."""
    lines = []
    for c in G.world_constraints(g, question):
        claim = G.describe_constraint(g, c)
        if not G.holds(g, c):
            lines.append(f"{claim}: does not hold - there is nothing to explain "
                         f"(ask whether it could be derived instead)")
            continue
        found = history_for(g, thread, c)
        if not found:
            lines.append(f"{claim}: holds, but nothing here derived it - it was given, not worked out")
            continue
        for _entry, name, bound in found:
            who = ", ".join(f"{p}={g.attr(n, 'label') or n}" for p, n in sorted(bound.items()))
            lines.append(f"{claim}: because {name}({who}) ran")
    return "\n".join(lines) if lines else "nothing was asked"


def describe(g: Graph, answer: dict) -> str:
    return f"{answer['verdict'].upper()} - {answer['why']} ({answer['steps']} step(s) considered)"


__all__ = ["YES", "NO", "UNKNOWN", "is_pure", "derivations", "refutes", "ask", "settle",
           "history_for", "steps_of", "why", "explain", "account", "describe"]
