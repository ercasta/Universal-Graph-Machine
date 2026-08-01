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

```
type car:
    is a vehicle                    inherit another type's demands
    has 4 wheel each a wheel        a count, a label, and what each target must BE (recursive)
    has 1 body each of kind body    ...or merely what it was minted as (one level, cheap)
    has at most 1 trailer           a count is a RANGE
    weight between 800 and 2000     an attribute, bounded
    colour = "red"                  an attribute, exact
    wheel[0].pressure == wheel[1].pressure     two places inside the subgraph agreeing
    wheel[0].rim is not wheel[1].rim           ...and not being the same node
```

## ⭐⭐ ONE reference language, and where each block may use it

Everything that refers to something not directly at hand goes through `path.py`: `car.wheel[1].pressure`,
unbounded depth, `^label` for the backward direction. It is one grammar because it used to be three — a
private regex in `driver.role_node`, a hand-split on the first dot here, and the dotted roles
`establishes` emits, none of which knew about the others.

**What differs per block is only what the FIRST segment names**, which is why one language can serve
surfaces with nothing else in common:

| block | the base is | depth available |
|---|---|---|
| `type` | the node being checked | **any** — a type only ever *checks*, so nothing downstream can be misled |
| `goal` / `ask` / `why` | a **named individual**, resolved by `resolve` | one hop, to an attribute |
| `method` / `procedure` | a **role** (`subject`, `object`), never a name | one hop, to an attribute |
| `prefer` / `avoid` | a named individual (whole, no hops) | none |
| `establishes` (not authored) | a **parameter** of the function | any |

⚠ **The goal and method rows are a REFUSAL, not an omission, and they were a silent bug first.**
`a.wheel[1].pressure = 3` used to split on the first dot and build a constraint about an attribute
literally called `wheel[1].pressure` — a slot nothing has, and `describe_constraint` rendered it back
looking right. What blocks the honest version is downstream of intake: `conflict.py` identifies a slot as
`(subject, key)` and would read two different wheels' pressures as one contended slot, and `query.settle`
writes an answer with `g.put(subject, …)`, which would land on the base rather than on the node the
reference reaches. Until both understand a navigated subject, `_one_hop` refuses and says so.

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
from . import path as P
from . import types as TY
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
    if re.fullmatch(r"-?\d+\.\d+", tok):
        return float(tok)                # a range like `pressure between 2.1 and 2.5` needs these
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


def _one_hop(text: str, lineno: int, what: str) -> tuple:
    """`"b.clear"` → `("b", "clear")`. **Refuses a deeper reference rather than mis-reading one.**

    ⚠ **This was a silent mis-parse, and it is the reason a shared reference language had to come with a
    composition review rather than after one.** `a.wheel[1].pressure = 3` split on the first dot and left a
    constraint whose *attribute* was literally named `wheel[1].pressure` — a slot nothing has, so the goal
    could never be met, and `describe_constraint` rendered it back looking exactly right. A round trip that
    a model checks itself against must not be able to lie.

    ⚠ **Why refused rather than supported here, when a `type` block takes any depth.** A goal constraint is
    not only *read*: `conflict.py` identifies a slot as `(subject, key)` and would conflate
    `a.wheel[0].pressure` with `a.wheel[1].pressure` into a conflict that is not one, and `query.settle`
    writes an answer with `g.put(subject, …)` and would write it to the base node rather than the one the
    reference reaches. Both are silent wrongness. A type schema has neither problem because it only ever
    *checks*. So the depth is available where it is correct, and refused — loudly, with this reason —
    where the machinery behind it has not caught up. That boundary is recorded rather than papered over."""
    base, rest = P.split_base(text)
    if rest is None or len(rest.hops) != 1 or rest.hops[0].index is not None or rest.hops[0].back:
        raise Unreadable(
            f"line {lineno}: {text!r} reaches deeper than a {what} can go. One hop from a named "
            f"individual to one of its attributes is what this form supports (`b.clear`); a `type` block "
            f"takes references of any depth")
    return base, rest.hops[0].label


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
        subject, key = _one_hop(words[0], lineno, "goal constraint")
        G.require_known(g, goal, node(subject), key)
    elif len(words) == 3 and words[1] == "=" and "." in words[0]:
        subject, key = _one_hop(words[0], lineno, "goal constraint")
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
TYPE_VERBS = ("type",)
VERBS = GOAL_VERBS + ADVICE_VERBS + METHOD_VERBS + TYPE_VERBS

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
        who, key = _one_hop(words[0], lineno, "method step")
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


_COUNTS = {"some": (1, None), "no": (0, 0), "a": (1, 1), "an": (1, 1), "one": (1, 1),
           "any": (0, None)}


def _count(words: list, lineno: int, line: str) -> tuple:
    """A count spec and the label it counts, from the words between `has` and the end of the phrase.

    ⚠ **A bare `has wheel` is REFUSED**, and the temptation to read it as "at least one" is exactly what a
    controlled language exists to resist: the author who wrote it may have meant one, or four, or any. The
    surface has a word for each of those, so it costs nothing to say which."""
    if len(words) >= 2:
        head, label = words[:-1], words[-1]
        if len(head) == 1 and head[0] in _COUNTS:
            return _COUNTS[head[0]] + (label,)
        if len(head) == 1 and re.fullmatch(r"\d+", head[0]):
            return int(head[0]), int(head[0]), label
        if len(head) == 3 and head[1] == "to" and all(re.fullmatch(r"\d+", h) for h in (head[0], head[2])):
            return int(head[0]), int(head[2]), label
        if len(head) == 3 and head[:2] == ["at", "least"] and re.fullmatch(r"\d+", head[2]):
            return int(head[2]), None, label
        if len(head) == 3 and head[:2] == ["at", "most"] and re.fullmatch(r"\d+", head[2]):
            return 0, int(head[2]), label
    raise Unreadable(f"line {lineno}: cannot read the count in {line!r} — a count is "
                     f"(n | n to m | at least n | at most n | some | no | a | any), and it is never "
                     f"left out")


def _type_line(g: Graph, t: str, words: list, line: str, lineno: int) -> None:
    """One line of a `type` block. Ordered most-specific first, so a keyword form is never shadowed.

    ⭐ **Both sides of a comparison are `path.py` references, so a demand may reach as deep as it likes.**
    That is the whole of what lifted the one-level limit at the surface: nothing here counts hops, and
    nothing here has its own idea of what a reference is."""
    if words and words[0] == "-":
        words = words[1:]                            # a bullet is punctuation, not vocabulary
    if not words:
        return
    is_ref = lambda w: P.is_reference(w)          # noqa: E731

    if words[:2] == ["is", "a"] and len(words) == 3:
        g.put(t, base=words[2])
    elif words[0] == "because" and len(words) > 1:
        g.put(t, because=" ".join(words[1:]))
    elif words[0] == "has":
        rest = words[1:]
        kind = type_ = None
        if "each" in rest:
            head, tail = rest[:rest.index("each")], rest[rest.index("each"):]
            if len(tail) == 3 and tail[1] in ("a", "an"):
                type_ = tail[2]
            elif len(tail) == 4 and tail[1:3] == ["of", "kind"]:
                kind = tail[3]
            else:
                raise Unreadable(f"line {lineno}: cannot read {' '.join(tail)!r} — what each target must "
                                 f"be is (each a TYPE | each of kind KIND)")
            rest = head
        lo, hi, label = _count(rest, lineno, line)
        TY.require_edge(g, t, label, TY.Req(kind=kind, type=type_, lo=lo, hi=hi))
    elif len(words) == 5 and words[1] == "between" and words[3] == "and":
        _demand(g, t, words[0], "between", words[2], lineno, line, hi=words[4])
    elif len(words) == 4 and words[1:3] == ["is", "not"]:
        TY.require_relation(g, t, TY.Rel(words[0], "is not", words[3], True))
    elif len(words) == 3 and words[1] == "is":
        TY.require_relation(g, t, TY.Rel(words[0], "is", words[2], True))
    elif len(words) == 3 and words[1] in ("=",) + TY.VALUE_OPS:
        _demand(g, t, words[0], "==" if words[1] == "=" else words[1], words[2], lineno, line)
    else:
        raise Unreadable(
            f"line {lineno}: cannot read {line!r} — the type vocabulary is closed "
            f"(is a T | has <count> label [each a T | each of kind K] | key = v | key <op> v | "
            f"key between lo and hi | path <op> path | path is [not] path | because …)")


def _demand(g: Graph, t: str, left: str, op: str, right: str, lineno: int, line: str, hi=None) -> None:
    """⭐⭐ **The one place the surface decides ATTRIBUTE-OF-THIS-NODE versus RELATION-BETWEEN-TWO-PLACES**,
    and it decides it by reading the operands rather than by asking the graph.

    `weight between 800 and 2000` constrains *this* node's weight; `wheel[0].pressure == wheel[1].pressure`
    relates two places within the subgraph. A bare word on the left is a one-hop path — this node's own
    attribute — and a bare word on the right is a **literal**, so `colour = red` compares against the
    string. An author who means a reference on the right writes a hop (`colour = body.colour`). That rule
    lives in `path.is_reference`, once, so every block reads it identically."""
    try:
        P.parse(left)
    except P.BadPath as e:
        raise Unreadable(f"line {lineno}: {e} (in {line!r})") from None
    if not P.is_reference(left) and not P.is_reference(right):
        TY.require_value(g, t, left, TY.AttrReq(op, _literal(right),
                                                None if hi is None else _literal(hi)))
        return
    if op == "between":
        raise Unreadable(f"line {lineno}: `between` constrains one attribute of this node, so its left "
                         f"side is a bare key — {left!r} is a reference")
    ref = P.is_reference(right)
    TY.require_relation(g, t, TY.Rel(left, op, right if ref else _literal(right), ref))


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
    | `type` | a **type** — a schema over a subgraph, of any depth |

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
    if verb in TYPE_VERBS:
        # ⚠ Refuses a REDECLARATION rather than minting a second type of the same name. Two would both
        # be found by `type_names` and `find_type` would answer with whichever came first — the same
        # "a name is not an identity" failure `resolve` refuses for individuals, one level up.
        if TY.find_type(g, label) is not None:
            raise Unreadable(f"{label!r} is already declared; a second declaration would not replace it, "
                             f"it would sit beside it")
        return TY.declare_type(g, label)
    return g.mint("method", name=label, handles="link", force=(G.MANDATORY if verb == "procedure"
                                                               else G.ADVISORY))


def _body(g: Graph, verb: str, node: str, words: list, line: str, lineno: int, under: str) -> None:
    if verb in GOAL_VERBS:
        _constrain(g, node, words, line, lineno, under)
    elif verb in ADVICE_VERBS:
        _advise(g, node, words, line, lineno, under)
    elif verb in TYPE_VERBS:
        _type_line(g, node, words, line, lineno)
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
    elif verb in TYPE_VERBS:
        # ⚠ A type that demands nothing is satisfied by everything, so it is not recognition — the same
        # stance `types.type_names` and `subsumes` already take, enforced at the surface that authors one.
        # A bare `is a <base>` is enough: it demands whatever the base demands.
        if not (g.attr(node, "base") or TY.schema_of(g, label) or TY.attrs_of(g, label)
                or TY.rels_of(g, label)):
            raise Unreadable(f"`type {label}` demands nothing, so everything is one; "
                             f"that is not a type, it is a word")
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
    if verb in TYPE_VERBS:
        return TY.describe(g, g.attr(goal, "name"))     # declaring is the whole of what a type block does
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


__all__ = ["Unreadable", "VERBS", "GOAL_VERBS", "ADVICE_VERBS", "METHOD_VERBS", "TYPE_VERBS", "ROLES",
           "resolve", "read", "read_goal", "respond", "describe"]
