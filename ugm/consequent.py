"""Consequent — the one right-hand side, tagged.

Every authored rule in this engine is conditions and a consequent; only the consequent and the
executor differ. This is the shared node kind those families mint through, rather than a method's
rung and a criterion's action being two kinds with nothing in common, each reachable only through
its own accessor.

It is a tagged shape rather than its own grammar, for a reason that only shows up at execution.
The two consequents do not differ in what they can reach — `driver.establishes` unions in each
mock's effects, so every operator a criterion can name is one search could already select, and
every binding it can name is one enumeration could already produce. They differ in shape,
irreducibly: `achieve` carries a proposition with roles, `call` carries a function with named
bindings. One grammar over both would have to be their union, which is a tag with the tag left
off.

The collapse therefore buys nothing in reach, which is exactly why it is worth having: it makes
the next consequent cheap. On the old shape, each new kind arrived with its own accessor.

What a consequent is not is a decision about who chooses. An `achieve` leaves the choice of
action open and lets the engine find one; a `call` closes it. That difference is a property of
the executor, and `method.decompose` and `criterion.speaks` remain the two executors. Unifying
the representation is what lets a reader ask both the same question; unifying the executors is
not attempted.
"""
from __future__ import annotations

from .graph import Graph

#: The closed set of consequent kinds. Closed, and each new member is a decision about an executor —
#: adding a tag with nothing that runs it is `docs/limits.md`'s execution verdict, which is worse than no form.
ACHIEVE, CALL = "achieve", "call"
KINDS = (ACHIEVE, CALL)

#: The edge from a rule to its consequent. One label for both families: the whole point is that a reader
#: asking *"what does this rule do?"* does not have to know which family it is holding.
LINK = "consequent"


def achieve(g: Graph, owner: str, *, sort: str, label: str | None = None, key: str | None = None,
            value=None, subject: str = "subject", object: str = "object",
            note: str | None = None) -> str:
    """A proposition to bring about. `sort` is a constraint sort (`link`/`attr`/`type`), and the referring
    positions hold roles rather than individuals — see `method.py` on why a rule that named an
    individual could not be reused.

    Ordered by declaration, because the edge is ordered. `method.decompose` reads that order as `then`."""
    c = g.mint("consequent", does=ACHIEVE, sort=sort, subject_role=subject,
               **{k: v for k, v in (("label", label), ("key", key), ("object_role", object),
                                    ("note", note)) if v is not None})
    if value is not None:
        g.put(c, value=value)
    g.link(owner, LINK, c)
    return c


def call(g: Graph, owner: str, *, function: str, bindings: dict) -> str:
    """A bound call. `bindings` maps each parameter to a reference, as text — resolved against the
    world when the rule is consulted, by `criterion.resolve_ref`.

    Text, not a node, and deliberately: a reference like `subject.owner.prefers` denotes different
    individuals in different situations, which is the whole reason a rule is reusable."""
    c = g.mint("consequent", does=CALL, function=function)
    for param in sorted(bindings):
        g.link(c, "arg", g.mint("binds", param=param, ref=bindings[param]))
    g.link(owner, LINK, c)
    return c


def of(g: Graph, owner: str) -> tuple:
    """Every consequent of a rule, in declaration order — whatever family it is.

    This is the function the collapse exists for. Before it, a reader wanting *"what does this rule
    do?"* had to know whether it was holding a method (`steps_of`, an ordered list) or a criterion
    (`action_of`, a single node), and there was no way to ask both."""
    return g.targets(owner, LINK)


def kind(g: Graph, c: str):
    """Which of `KINDS` this consequent is, or `None` if it is not a consequent at all."""
    return g.attr(c, "does")


def bindings_of(g: Graph, c: str) -> tuple:
    """`(param, reference-text)` pairs of a `call`, in parameter order. Empty for an `achieve`."""
    return tuple((g.attr(a, "param"), g.attr(a, "ref")) for a in g.targets(c, "arg"))


def describe(g: Graph, c: str) -> str:
    """One consequent, in words, without the reader knowing which family it came from.

    A rendering, never an identity — `driver._name` records that lesson at length."""
    which = kind(g, c)
    if which == CALL:
        args = ", ".join(f"{p} = {r}" for p, r in bindings_of(g, c))
        return f"do {g.attr(c, 'function')}({args})"
    if which == ACHIEVE:
        note = g.attr(c, "note")
        if note:
            return note
        sort, subj = g.attr(c, "sort"), g.attr(c, "subject_role")
        if sort == "link":
            return f"achieve {subj} {g.attr(c, 'label')} {g.attr(c, 'object_role')}"
        if sort == "attr":
            return f"achieve {subj}.{g.attr(c, 'key')} = {g.attr(c, 'value')}"
        return f"achieve {subj} is a {g.attr(c, 'label')}"
    raise ValueError(f"{c} is not a consequent (does={which!r}); a reader must not guess what a rule does")


__all__ = ["ACHIEVE", "CALL", "KINDS", "LINK", "achieve", "call", "of", "kind", "bindings_of", "describe"]
