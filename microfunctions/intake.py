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
    some file                   SOMETHING of this type must exist
    a is a serviced_car         this individual must satisfy this type

    # what the plan itself may do
    never unstack               a forbidden operator
    never touch c               an individual that must not be bound
    must paint                  the plan has to include this
    at most 3 steps             a budget
```
"""
from __future__ import annotations

import re

from . import goal as G
from .graph import Graph
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
    elif len(words) == 3 and words[1] == "=" and "." in words[0]:
        subject, key = words[0].split(".", 1)
        G.require_attr(g, goal, node(subject), key, _literal(words[2]))
    elif len(words) == 3:
        G.require_link(g, goal, node(words[0]), words[1], node(words[2]))
    else:
        raise Unreadable(f"line {lineno}: cannot read {line!r} — the goal vocabulary is closed "
                         f"(a b c | a.k = v | some T | a is a T | never f | never touch x | "
                         f"must f | at most n steps)")


def read_goal(g: Graph, text: str, *, under: str = "root") -> str:
    """Parse one `goal <label>:` block into a goal node with its constraints. Raises `Unreadable`.

    Nothing is minted until the whole block parses — a half-built goal would be worse than none, because
    the driver would pursue it and appear to be working."""
    lines = [(i + 1, ln.split("#")[0].rstrip())
             for i, ln in enumerate(text.splitlines())]
    lines = [(i, ln) for i, ln in lines if ln.strip()]
    if not lines:
        raise Unreadable("nothing to read")

    lineno, header = lines[0]
    m = re.fullmatch(r"goal\s+(.+?)\s*:", header.strip())
    if not m:
        raise Unreadable(f"line {lineno}: expected `goal <label>:`, got {header.strip()!r}")

    # Parse into a throwaway goal first so a bad line leaves nothing behind.
    goal = G.open_goal(g, label=m.group(1))
    try:
        for lineno, raw in lines[1:]:
            _constrain(g, goal, raw.split(), raw.strip(), lineno, under)
    except Unreadable as e:
        for c in G.constraints(g, goal):
            g.drop(c)
        g.drop(goal)
        raise Unreadable(f"line {lineno}: {e}" if "line " not in str(e) else str(e)) from None
    if not G.constraints(g, goal):
        g.drop(goal)
        raise Unreadable("a goal with no constraints wants nothing")
    return goal


def describe(g: Graph, goal: str) -> str:
    """Render a goal back to the surface it came from — the round trip a model reads to check itself."""
    lines = [f"goal {g.attr(goal, 'label')}:"]
    lines.extend(f"    {G.describe_constraint(g, c)}" for c in G.constraints(g, goal))
    return "\n".join(lines)


__all__ = ["Unreadable", "resolve", "read_goal", "describe"]
