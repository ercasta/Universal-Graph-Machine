"""INTAKE — turning something said into a goal, as data.

The loop is driven entirely by a goal, and until now the only way to get one was to call `goal.py` from
Python. So the one thing that starts the system was the one thing the system had no way to receive.

**⭐ Why intake is tractable now, when it was not before.** The `ugm/`-era attempts translated prose into
*arbitrary graph structure* and got 0/50 on raw prose, with the gap recorded as "100% constructional" —
unsurprising, because the target was unbounded. A goal is no longer arbitrary structure: it is a handful of
**constraint nodes** from a closed vocabulary (link, attribute, type; never, must, at most). Translating
into eight forms is a different problem from translating into anything, and that is the whole reason this
is a small module rather than a research programme.

**The border, and where the language model sits.** `asm.py` is already "the text surface and LLM border"
for *functions*; this is its sibling for *goals*. The division is the project's standing one — **the model
is a boundary tool, never the computation model**: a model may write this text, and the parser then accepts
or refuses it deterministically. What a model must never do is reach past the surface and write graph
structure directly, because then nothing could refuse it.

**⚠ The translator must be able to refuse, and refusal is the feature.** Three ways in, all loud:

* a line that matches no form — the vocabulary is closed, so an unrecognised sentence is not "best effort";
* a name that matches nothing;
* a name that matches **more than one thing**. Nodes here are nameless and a `label` is a convenience for
  humans, so resolving one is a lookup that can genuinely be ambiguous. `docs/units` records the lesson at
  length: *never identify by name alone*. Guessing between two candidates would be inventing a referent,
  which is exactly the failure a controlled language exists to prevent.

**The grammar**, deliberately boring — each form is recognisable by its shape or leading keyword:

```
goal stack them:
    # what must be true of the world
    a on b                      a link between individuals
    b.clear = true              an attribute value
    d.contents known            a KNOWLEDGE claim — go and look, rather than make it so
    some file                   SOMETHING of this type must exist
    a is a serviced_car         this individual must satisfy this type

    # what the plan itself may do
    never unstack               a forbidden operator
    never touch c               an individual that must not be bound
    must paint                  the plan has to include this
    at most 3 steps             a budget
```

## ⭐⭐ Three verbs, ONE grammar — because a question IS a goal

`goal`, `ask` and `why` take **exactly the same body**. That is not an economy in the parser; it is the
data model showing through. A goal is a set of constraints, a question is a set of constraints, and what
differs is only what you then *do* with them — pursue, answer, or explain.

```
goal make it so:      ask is it so?:        why is it so?:
    a on b                a on b                a on b
```

**⚠ So what distinguishes them in the graph? Only a record of how it arrived.** The constraints are
identical, and the `verb` attribute is *not* a labelling error of the kind `HANDOFF.md` warns about —
structure does not entail it. Which speech act something was is genuinely extra information, unrecoverable
from the constraints, and it is exactly the project's standing **force-is-the-missing-axis** finding: force
is a property of the intake **route**, not of the form. Two people can want and doubt the same proposition.

**⭐ Plan constraints work in a question, and mean something useful.** `never phone_the_registrar` in an
`ask` block is *"is this derivable without asking anyone?"*; `at most 2 steps` is *"is it derivable in two
steps?"*. Nothing had to be added for this — constraining the route is constraining the route, whether the
route is a plan of action or a derivation.

⚠ `why` differs from `ask` in **what it reports, not in what it searches**: it wants the history behind
something that already holds (`query.account`), where `ask` wants a verdict on something that may not. A
`why` about a fact that is not true is answered by saying so, never by inventing a derivation for it.
"""
from __future__ import annotations

import re

from . import goal as G
from .graph import Graph
from . import guideline as GL
from . import method as M
from .workbench import reachable


class Unreadable(Exception):
    """A line the closed vocabulary cannot represent, or a name that cannot be resolved to one node.

    Loud on purpose — see the module docstring. Carries the line number and the text."""


def _literal(tok: str):
    if tok.startswith('"') and tok.endswith('"'):
        return tok[1:-1]
    if tok in ("true", "false"):
        return tok == "true"
    if tok in ("null", "none"):
        return None
    if re.fullmatch(r"-?\d+", tok):
        return int(tok)
    return tok


def resolve(g: Graph, name: str, *, under: str = "root") -> str:
    """The one node labelled `name` in the world. Refuses on none, and refuses on more than one.

    ⚠ Searched by **traversal from `under`**, never by scanning — the same discipline as
    `types.instances`, and for the same reason: a scan would find the system's own imaginings and offer a
    workbench copy as the referent of a word someone said."""
    hits = [n for n in reachable(g, under) if g.attr(n, "label") == name]
    if not hits:
        raise Unreadable(f"nothing here is called {name!r}")
    if len(hits) > 1:
        raise Unreadable(f"{name!r} is ambiguous — {len(hits)} things are called that; "
                         f"a name is not an identity")
    return hits[0]


def _constrain(g: Graph, goal: str, words: list, line: str, lineno: int, under: str) -> None:
    """One line to one constraint. Ordered most-specific first, so a keyword form is never shadowed."""
    node = lambda w: resolve(g, w, under=under)          # noqa: E731

    if words[:2] == ["at", "most"] and len(words) >= 3:
        G.limit_steps(g, goal, int(words[2]))
    elif words[:2] == ["never", "touch"] and len(words) == 3:
        G.forbid_action(g, goal, on=node(words[2]), reason=line)
    elif words[0] == "never" and len(words) == 2:
        G.forbid_action(g, goal, function=words[1], reason=line)
    elif words[0] == "must" and len(words) == 2:
        G.require_action(g, goal, function=words[1])
    elif words[0] == "some" and len(words) == 2:
        G.require_type(g, goal, words[1])
    elif len(words) == 4 and words[1:3] == ["is", "a"]:
        G.require_type(g, goal, words[3], about=node(words[0]))
    elif len(words) == 2 and words[1] == "known" and "." in words[0]:
        # ⭐ A KNOWLEDGE claim: *go and look*, as opposed to *make it so*. The surface distinguishes them
        # because the system now can — see `graph.UNKNOWN`.
        subject, key = words[0].split(".", 1)
        G.require_known(g, goal, node(subject), key)
    elif len(words) == 3 and words[1] == "=" and "." in words[0]:
        subject, key = words[0].split(".", 1)
        G.require_attr(g, goal, node(subject), key, _literal(words[2]))
    elif len(words) == 3:
        G.require_link(g, goal, node(words[0]), words[1], node(words[2]))
    else:
        raise Unreadable(f"line {lineno}: cannot read {line!r} — the goal vocabulary is closed "
                         f"(a b c | a.k = v | a.k known | some T | a is a T | never f | never touch x | "
                         f"must f | at most n steps)")


GOAL_VERBS = ("goal", "ask", "why")
ADVICE_VERBS = ("prefer", "avoid")
METHOD_VERBS = ("method", "procedure")
VERBS = GOAL_VERBS + ADVICE_VERBS + METHOD_VERBS

ROLES = (M.SUBJECT, M.OBJECT)


def _advise(g: Graph, gl: str, words: list, line: str, lineno: int, under: str) -> None:
    """One line of a `prefer`/`avoid` block. Closed, keyword-led, and deliberately tiny."""
    if words[0] == "action" and len(words) == 2:
        g.put(gl, function=words[1])
    elif words[0] == "touching" and len(words) == 2:
        g.link(gl, "on", resolve(g, words[1], under=under))
    elif words[0] == "when" and len(words) == 2:
        g.put(gl, when=words[1])
    elif words[0] == "because" and len(words) > 1:
        g.put(gl, because=" ".join(words[1:]))
    else:
        raise Unreadable(f"line {lineno}: cannot read {line!r} — the advice vocabulary is closed "
                         f"(action f | touching x | when T | because …)")


def _step(g: Graph, m: str, words: list, line: str, lineno: int) -> None:
    """One `step …` line. ⭐ **The step grammar is the GOAL grammar with roles instead of names** — the
    only legal subjects are `subject` and `object`, meaning the matched constraint's. A method that named
    an individual would be about that individual and could not be reused, which is the same reason
    `types.py` refuses to let a schema name a target."""
    def role(w: str) -> str:
        if w not in ROLES:
            raise Unreadable(f"line {lineno}: {w!r} is not a role — a step may only speak of "
                             f"{' or '.join(ROLES)}, never a named individual")
        return w

    if len(words) == 3 and words[1] == "=" and "." in words[0]:
        who, key = words[0].split(".", 1)
        M.step(g, m, sort="attr", key=key, value=_literal(words[2]), subject=role(who), note=line)
    elif len(words) == 4 and words[1:3] == ["is", "a"]:
        M.step(g, m, sort="type", label=words[3], subject=role(words[0]), note=line)
    elif len(words) == 3:
        M.step(g, m, sort="link", label=words[1], subject=role(words[0]),
               object=role(words[2]), note=line)
    else:
        raise Unreadable(f"line {lineno}: cannot read step {line!r} — a step is "
                         f"(subject l object | subject.k = v | subject is a T), with roles not names")


def _method_line(g: Graph, m: str, words: list, line: str, lineno: int) -> None:
    if words[0] == "handles" and len(words) == 3:
        if words[1] not in ("link", "attr", "type"):
            raise Unreadable(f"line {lineno}: a method handles link, attr or type — not {words[1]!r}")
        g.put(m, handles=words[1], label=words[2])
    elif words[0] == "when" and len(words) == 2:
        g.put(m, when=words[1])
    elif words[0] == "within" and len(words) == 2:
        hits = [n for n in M.methods(g) if g.attr(n, "name") == words[1]]
        if len(hits) != 1:
            raise Unreadable(f"line {lineno}: {words[1]!r} names {len(hits)} methods; "
                             f"a method's context must be exactly one declared method")
        g.link(m, "within", hits[0])
    elif words[0] == "because" and len(words) > 1:
        g.put(m, because=" ".join(words[1:]))
    elif words[0] == "step" and len(words) > 1:
        _step(g, m, words[1:], line, lineno)
    else:
        raise Unreadable(f"line {lineno}: cannot read {line!r} — the method vocabulary is closed "
                         f"(handles S l | when T | within m | because … | step …)")


def read(g: Graph, text: str, *, under: str = "root") -> tuple:
    """Parse one `<verb> <label>:` block. Returns `(verb, node)`. Raises `Unreadable`.

    **⭐ One block grammar, three families**, because the standing principle is that microfunctions ship
    with the engine and *everything a domain contributes is data*. Until this existed the border held for
    goals alone: a guideline or a method could only be authored by calling Python, which is exactly the
    "reach past the surface and write graph structure" the module docstring says must never happen. The
    principle was stated and unenforced.

    | verb | produces |
    |---|---|
    | `goal` / `ask` / `why` | a **goal** — same body, different thing done with it |
    | `prefer` / `avoid` | a **guideline** — reorders, can never exclude |
    | `method` / `procedure` | a **method** — a decomposition, advisory or mandatory |

    ⚠ **`method` and `procedure` differ ONLY in force, and that is the point.** The bodies are identical;
    what changes is what happens when a step does not work out — fall back to searching, or refuse to
    improvise. `deliberation.md` §3: force is about *failure*, not strength, and it cannot be inferred
    from content, so the surface makes the author say which word they mean.

    ⚠ **Refusal leaves nothing behind, now via the JOURNAL rather than by hand.** The old goal path dropped
    its constraints one by one on failure, which had to be kept in step with everything a body could mint —
    exactly the maintenance a transactional substrate exists to remove. `savepoint`/`rollback` is what the
    journal was built for, and this is its first real consumer outside `selftest.py`. ⚠ It is transactional
    only: nothing between the savepoint and the rollback may `commit`, and nothing here does."""
    lines = [(i + 1, ln.split("#")[0].rstrip())
             for i, ln in enumerate(text.splitlines())]
    lines = [(i, ln) for i, ln in lines if ln.strip()]
    if not lines:
        raise Unreadable("nothing to read")

    lineno, header = lines[0]
    m = re.fullmatch(r"(%s)\s+(.+?)\s*:" % "|".join(VERBS), header.strip())
    if not m:
        raise Unreadable(f"line {lineno}: expected `<verb> <label>:` with verb one of "
                         f"{', '.join(VERBS)}, got {header.strip()!r}")
    verb, label = m.group(1), m.group(2)

    sp = g.savepoint()
    try:
        node = _open(g, verb, label)
        for lineno, raw in lines[1:]:
            _body(g, verb, node, raw.split(), raw.strip(), lineno, under)
        _seal(g, verb, node, label)
    except Unreadable as e:
        g.rollback(sp)
        raise Unreadable(str(e) if "line " in str(e) else f"line {lineno}: {e}") from None
    return verb, node


def _open(g: Graph, verb: str, label: str) -> str:
    if verb in GOAL_VERBS:
        goal = G.open_goal(g, label=label)
        g.put(goal, verb=verb)
        return goal
    if verb in ADVICE_VERBS:
        return g.mint("guideline", stance=GL.PREFER if verb == "prefer" else GL.AVOID, label=label)
    return g.mint("method", name=label, handles="link", force=(G.MANDATORY if verb == "procedure"
                                                               else G.ADVISORY))


def _body(g: Graph, verb: str, node: str, words: list, line: str, lineno: int, under: str) -> None:
    if verb in GOAL_VERBS:
        _constrain(g, node, words, line, lineno, under)
    elif verb in ADVICE_VERBS:
        _advise(g, node, words, line, lineno, under)
    else:
        _method_line(g, node, words, line, lineno)


def _seal(g: Graph, verb: str, node: str, label: str) -> None:
    """⚠ **Every family refuses a body that says nothing**, and each needs its own closure fact — the
    generalisation `goal_machinery.md` §8 reached as *don't trust an open-ended absence without an explicit
    closure fact*. A guideline matching everything is not advice; a method with no steps decomposes into
    nothing, which `goal.decomposed` would then read as an undecomposed goal."""
    if verb in GOAL_VERBS:
        if not G.constraints(g, node):
            raise Unreadable(f"a {verb} with no constraints says nothing")
    elif verb in ADVICE_VERBS:
        if g.attr(node, "function") is None and g.target(node, "on") is None:
            raise Unreadable(f"`{verb} {label}` names neither an action nor a thing — advice that "
                             f"matches everything is not advice")
    elif not M.steps_of(g, node):
        raise Unreadable(f"`{verb} {label}` has no steps; it would decompose into nothing")


def read_goal(g: Graph, text: str, *, under: str = "root") -> str:
    """Parse a `goal …:` block. Refuses `ask` and `why` — a caller wanting one of those wants `read`."""
    sp = g.savepoint()
    verb, goal = read(g, text, under=under)
    if verb != "goal":
        g.rollback(sp)
        raise Unreadable(f"this is a {verb!r} block, not a goal; use `read` to take any of {VERBS}")
    return goal


def respond(g: Graph, text: str, thread: str, subject: str = "root", *,
            under: str = "root", keep: bool = True, **kw) -> str:
    """Read something said and do the right thing with it. The whole conversational surface, in one call.

    ⚠ **`ask` settles by default (`keep=True`), and that is a choice worth seeing.** The derivation ran on
    a workbench, so nothing is committed unless it is replayed; keeping it means the next question does not
    re-derive what this one worked out, and — the part that matters more — it is what gives `why` anything
    to answer from later. Pass `keep=False` for a question that should leave no trace."""
    from . import query as Q
    verb, goal = read(g, text, under=under)
    if verb == "goal":
        return G.describe(g, goal)                 # pursuing is the caller's to schedule, not intake's
    if verb == "why":
        return Q.account(g, goal, thread, subject)
    answer = Q.ask(g, goal, thread, subject, **kw)
    if keep and answer["verdict"] == Q.YES:
        Q.settle(g, answer, thread)
    return Q.describe(g, answer) + ("\n" + Q.explain(g, answer) if answer["proof"] else "")


def describe(g: Graph, goal: str) -> str:
    """Render a goal back to the surface it came from — the round trip a model reads to check itself.

    ⚠ **Refuses anything that is not a goal rather than rendering it badly.** Handed a guideline it would
    otherwise emit `goal <label>:` with an empty body — well-formed, wrong, and exactly the "best effort"
    this module exists to refuse. A round trip a model checks itself against must not be able to lie."""
    if g.kind(goal) != "goal":
        raise Unreadable(f"describe renders a goal; {goal} is a {g.kind(goal)}")
    lines = [f"{g.attr(goal, 'verb') or 'goal'} {g.attr(goal, 'label')}:"]
    lines.extend(f"    {G.describe_constraint(g, c)}" for c in G.constraints(g, goal))
    return "\n".join(lines)


__all__ = ["Unreadable", "VERBS", "GOAL_VERBS", "ADVICE_VERBS", "METHOD_VERBS", "ROLES",
           "resolve", "read", "read_goal", "respond", "describe"]
