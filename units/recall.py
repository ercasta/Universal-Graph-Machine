"""SYSTEM 1 — retrieval (`docs/units/model.md` §7, step 1).

> Associative, approximate, not rationally controlled… It is allowed to be incomplete and allowed to be
> wrong; the cost of a wrong suggestion is a wasted step.
>
> **Retrieval may be approximate; application must be exact.**

⚠ **The mechanism is undecided** (§13, first open question) — subgraph similarity, activation spreading,
or something learned; and whether the similarity function is authored data or the one thing the engine
fixes. What is here is the crudest thing that has the right *shape*, so that the loop can be built and
measured. Do not mistake it for the answer.

`resemblance` asks one question per statement: **how much of what it talks about is present in what I am
attending to?** That is enough to reproduce the two properties the loop depends on:

- it is **incomplete** — a statement whose vocabulary is mostly absent never comes to mind, which is
  exactly §7's *"a rule that would have applied may simply never come to mind"*;
- it is **wrong sometimes** — a statement overlapping the world is offered whether or not it is
  relevant, which is §10's birthday-discount rule. The cost is a wasted step.

**Attention bounds retrieval, not application** (§7). `attended` is the region recalled against; passing
the whole world is what §7 says cannot be afforded at scale, and is offered here only for small tests.

⚠ **This reverses `ugm`'s [[recall-explicit-not-autofire]]**, deliberately and on the terms §7 sets: the
ban existed to protect a strong negation, and graded matching has already weakened that negation, so
there is no strong claim left for auto-fire to corrupt. **The self-reinforcement half is NOT resolved**
(§13) — nothing here diversifies, and a narrow attention will keep confirming itself.
"""
from __future__ import annotations

from .assemble import kind_of, roles_of
from .graph import Graph, Node


def vocabulary(desc: Graph, statement: Node) -> set:
    """Every `name` a statement's patterns ask about — its 'what this is about'.

    Read off the description, never off the built circuit: retrieval happens *before* assembly."""
    words: set = set()
    for step in roles_of(desc, statement, "step"):
        if kind_of(desc, step) == "statement":
            words |= vocabulary(desc, step)
            continue
        for pat in roles_of(desc, step, "pattern"):
            words |= _atom_names(desc, pat)
    return words


def _atom_names(desc: Graph, atom: Node) -> set:
    words = set()
    for c in roles_of(desc, atom, "constraint"):
        if desc.attr(c, "key") == "name":
            words.add(desc.attr(c, "value"))
    for child in roles_of(desc, atom, "out"):
        words |= _atom_names(desc, child)
    return words


def present(attended: Graph) -> set:
    return {attended.attr(n, "name") for n in attended.nodes if attended.attr(n, "name") is not None}


def coverage(attended: Graph, desc: Graph, statement: Node) -> float:
    """What fraction of what this statement talks about is present in the attended region."""
    vocab = vocabulary(desc, statement)
    if not vocab:
        return 0.0
    return len(vocab & present(attended)) / len(vocab)


def resemblance(attended: Graph, desc: Graph, *, pinned: tuple = (), theta: float = 0.5) -> list:
    """Which statements come to mind, as labels. Non-exhaustive by construction.

    Scored by **coverage** rather than by any-overlap, and the reason is a real defect found while
    building the loop:

    ⚠ **Role names make everything resemble everything.** A pattern that reaches a participant through
    a role node matches `name = "agent"` explicitly (§4), so `"agent"` lands in its vocabulary — and
    every world with any agent in it contains that word. Under any-overlap, every rule with an agent
    role comes to mind for every world, and retrieval stops discriminating at all. This is `model.md`
    §13's *role node sharing* question arriving from an unexpected direction: role names behave like a
    shared vocabulary whether or not one was declared, and here they leak into **retrieval** rather than
    into matching. Coverage dilutes it rather than fixing it — a common word costs a statement nothing
    but also buys it little. **Not solved.**

    `pinned` is §7's hard requirement that **a pending goal must stay attended** — the loop is tight, so
    a goal is re-retrieved dozens of times before it is satisfied, and uniform decay would turn the tight
    loop's advantage into its failure mode. It is also how §7's *"linguistic competence must be attended
    even when nothing is"* would be expressed.

    `theta` is a **tuning parameter with no principle behind it**, which is honest: §13 leaves the
    mechanism open, and this one exists so the loop can be built and measured, not because it is right."""
    nested = {t for s in _statements(desc) for t in roles_of(desc, s, "step")}
    out = []
    for s in _statements(desc):
        if s in nested:
            continue
        label = desc.attr(s, "label")
        if label in pinned or coverage(attended, desc, s) >= theta:
            out.append(label)
    return sorted(out)


def _statements(desc: Graph) -> list:
    return [n for n in desc.nodes if kind_of(desc, n) == "statement"]


__all__ = ["resemblance", "coverage", "vocabulary", "present"]
