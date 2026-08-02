"""MEMORY — what the agent has seen, and whether it was the one that changed it.

**The gap this closes.** The graph held *the world as currently believed* and nothing else. An application
on the thread recorded that `stack` ran; nothing recorded what it changed, so "what was true before?" had
no answer. Meanwhile `graph.py`'s undo journal held the inverse of **every** mutation — 650 of them after
one two-step plan — as a Python list of closures the system could not read, LIFO-only, and cleared outright
by `dispatch.service`'s `commit()`. So the past was computed, unreadable, and then destroyed.

⚠ **`commit()` is right and stays.** It answers *"can I reverse this?"* — and once an email has left, you
cannot. What it should never have answered is *"can I remember what preceded it?"*, which is a different
question with a different answer. The journal keeps its semantics untouched; memory is recorded separately,
as graph data, before anything leaves.

## ⭐⭐ The external world moves on its own, and that breaks a delta log

A journal delta records only **the agent's own writes**. When a file changes on disk *nothing happens in
the graph at all* — no mutation, no entry — and the belief is simply wrong until someone looks again. Worse,
the second look is itself a write, so a naive delta log would record *"the agent changed `dir.count` from 3
to 5"* when the truth is *"the agent looked, and found 5 where it had recorded 3."* Conflating those is a
silent epistemic error.

So two records with two jobs, and the interesting thing is **derived** from their combination:

* an **observation** — what was seen, of what, when, from which source (recorded at the dispatch boundary,
  which `dispatch.py` already makes the one place anything crosses in or out);
* the **thread** — what the agent did, already ordered, already flagging `done` versus merely imagined;
* **attribution** — *did I do this?* Two observations of one slot differ, and either some `done`
  application between them could have written it, or **the world moved on its own.**

⭐ That needs no new primitive. `driver.establishes` already reads a stored function body to say what it
writes and **with which roles**, and `driver.role_node` resolves a role against bindings. So "could this
application have touched that slot?" is a question the engine could already answer and had never been
asked.

⚠ **Attribution is EVIDENCE, not proof, and says so.** `establishes` is an over-approximation by contract,
so "mine" means *could have been mine*. And an action of mine and an external change can both have happened
— `attribute` reports what is possible, never a verdict. The same stance `establishes` takes about itself.

## ⚠ What sampling can and cannot see

* **Change-and-back is visible** whenever an observation falls inside the excursion — three sightings
  showing A, B, A is exactly that. It is invisible only when nothing looks during the window, which makes
  it a **sampling-rate** question rather than an impossibility, and sampling rate is something the agent
  controls.
* **Observations bound change from below, never count it.** A, B, A proves *at least* two changes; it can
  never distinguish two from six. A consumer counting transitions is counting *observed* transitions.
* **⚠ One case stays genuinely undecidable**, and it is the everyday one: observe A, act expecting B,
  observe A. Either the action did not take effect, or it did and the world reverted it. Same evidence, and
  no further looking recovers which — the window has closed. Reported as both possibilities standing, never
  resolved by guessing.

## ⭐⭐ Encoding and retention are different moments with OPPOSITE defaults

*You do not remember how many steps it took to get to school.* That is not forgetting — it was never
encoded. Treating the two as one thing is what makes "record everything" look safe when it is not: at scale
it makes the interesting things unfindable, which is a kind of forgetting in itself.

| moment | default | why |
|---|---|---|
| **encoding** — an observation arrives | **do not** | never-encoded yields honest ignorance, which is *recoverable by looking* |
| **retention** — deciding what to keep | **do** | dropping what was already reasoned from can contradict conclusions already drawn |

⭐ **The encoding gate already exists, and it is attention.** You do not remember the steps because you were
not attending to them — and `dispatch.service` is called *on a target*, which is precisely what is being
attended to. So the structural default is neither everything nor nothing: **the slots of the thing being
looked at**. `keep` is the seam for overriding that in either direction, and it is **inert by default**,
exactly as `pursue`'s decision seam shipped inert.
"""
from __future__ import annotations

from . import application as ap
from . import thread as T
from .graph import Graph

#: A sighting is a thread entry like any other, so ordering, `why` and every existing reader come free.
OBSERVATION = "observation"

#: What `attribute` can answer. Closed, like every other decision vocabulary here.
MINE, EXTERNAL, BOTH = "mine", "external", "both"


def observe(g: Graph, thread: str, node: str, key: str, value, *,
            source: str | None = None, why: str | None = None, when: str | None = None) -> str:
    """Record one sighting of one slot. Returns the entry.

    ⚠ Recorded **whether or not the value differs** from what was believed. Collapsing to "only when it
    changed" would be cheaper and would destroy exactly the case that matters: A, B, A would store as *no
    change*, so the agent would have watched a round trip happen and recorded that nothing did. It also
    reintroduces the `UNKNOWN` conflation one level up — *unchanged* would become indistinguishable from
    *unobserved*, and "when did I last check?" would have no answer for anything stable."""
    entry = g.mint(OBSERVATION, key=key, value=value, **({"source": source} if source else {}))
    g.link(entry, "of", node)
    T._append(g, thread, entry, why)
    # ⭐⭐ **EVERYTHING OBSERVED CARRIES AN ABSOLUTE TIMESTAMP** (the user's specification, 2026-08-02).
    # Before this, *when* an observation happened was its **position in the thread** — an order with no
    # magnitude, so "how stale is this?" and "has this always been true?" had nothing to compute from.
    # ⚠ The moment POINTS AT the observation rather than being an attribute on it: one look dates many
    # slots, and `record_sighting` passes one `when` for the whole look precisely so they share it.
    from . import clock as C
    C.stamp(g, when if when is not None else C.now(g), entry)
    return entry


def sightings(g: Graph, thread: str, node: str, key: str | None = None) -> tuple:
    """Every observation of this node (optionally this slot), oldest first."""
    return tuple(e for e in T.entries(g, thread)
                 if g.kind(e) == OBSERVATION and g.target(e, "of") == node
                 and (key is None or g.attr(e, "key") == key))


def believed(g: Graph, thread: str, node: str, key: str):
    """The most recent sighting of a slot, or `None` if it was never looked at.

    ⚠ Distinct from `g.attr(node, key)`, deliberately. That is the current belief and is what everything
    reasons over; this is *what was actually seen, and when*. Keeping them apart is what lets a belief be
    recognised as stale rather than silently trusted."""
    seen = sightings(g, thread, node, key)
    return seen[-1] if seen else None


def transitions(g: Graph, thread: str, node: str, key: str) -> tuple:
    """Consecutive sightings whose values differ, as `(before, after)` pairs.

    ⚠ A **lower bound** on how often the slot changed — see the module docstring. Anything reading this as
    a count is counting observed transitions, which is a different quantity."""
    seen = sightings(g, thread, node, key)
    return tuple((a, b) for a, b in zip(seen, seen[1:])
                 if g.attr(a, "value") != g.attr(b, "value"))


def _positions(g: Graph, thread: str) -> dict:
    return {e: i for i, e in enumerate(T.entries(g, thread))}


def _could_have_written(g: Graph, app: str, node: str, key: str) -> bool:
    """Could this application have written `node.key`? Read off the stored body, never declared.

    ⭐ `driver.establishes` says which slots a function writes and **with which roles**; `role_node`
    resolves a role against the bindings this application actually used. Both already existed for ranking;
    this is the same question asked for a different purpose.

    ⚠ Over-approximates on purpose. An unreadable instruction yields `unknown`, and an unknown that could
    concern this subject counts as *could have* — because the safe direction here is to admit the agent
    might be responsible, not to blame the world."""
    from . import driver as D
    name = g.attr(app, "function")
    if not name:
        return False
    effects, unknown = D.establishes(g, name)
    bound = ap.bindings_of(g, app)
    for kind, label, subject_role, _obj in effects:
        if kind == "attr" and label == key and D.role_node(g, bound, subject_role) == node:
            return True
    if unknown:
        # `unknown` is a frozenset of the roles an unreadable instruction concerns; `None` inside it means
        # "somewhere we cannot name at all", which could be anywhere, including here.
        return any(r is None or D.role_node(g, bound, r) == node for r in unknown)
    return False


def attribute(g: Graph, thread: str, before: str, after: str) -> dict:
    """**Did I do this, or did the world move?** For one observed transition.

    Returns `{"verdict": MINE | EXTERNAL | BOTH, "by": (application, …), "unknown_gap": bool}`.

    ⚠ **Evidence, not proof.** `MINE` means an action of mine *could* have written that slot between the
    two sightings — `establishes` over-approximates, so this can never be a verdict about causation.
    `BOTH` is returned when an action could have written it *and* the observed value is not what that
    action would produce, which is the undecidable case from the module docstring standing open rather than
    being resolved by preference.

    ⭐ `EXTERNAL` is the interesting one and it is **derived**: nothing the agent did between the two looks
    could have touched the slot, so something else did. That is the answer to *"was it me?"*, and it needed
    no new record — only the thread, which was already ordered and already flagged `done`."""
    node, key = g.target(before, "of"), g.attr(before, "key")
    pos = _positions(g, thread)
    lo, hi = pos.get(before, -1), pos.get(after, -1)
    between = [e for e, i in pos.items()
               if lo < i < hi and g.kind(e) == "application" and g.attr(e, "done")]
    culprits = tuple(a for a in between if _could_have_written(g, a, node, key))
    if not culprits:
        return {"verdict": EXTERNAL, "by": (), "unknown_gap": False}
    # ⚠ An action that COULD have written it does not mean the value seen is the one it wrote. When both
    # remain possible, say so — the module docstring's undecidable case.
    return {"verdict": MINE if len(culprits) == 1 else BOTH, "by": culprits, "unknown_gap": False}


def volatility(g: Graph, thread: str, node: str, key: str) -> dict:
    """How much this slot moves **under** the agent — the statistic a sampling decision needs.

    ⭐ This is what gives `driver.SENSE` something to aim at. `driver.py` records that `SENSE` "needs
    ignorance", and ignorance was the only trigger available: *I do not know, so go and look*. Volatility
    supplies a better one — **I knew, and it is probably stale** — which is the case that actually arises
    for an agent whose world has other people in it."""
    seen = sightings(g, thread, node, key)
    moved = transitions(g, thread, node, key)
    external = sum(1 for a, b in moved if attribute(g, thread, a, b)["verdict"] == EXTERNAL)
    return {"looks": len(seen), "changes": len(moved), "unattributed": external,
            "rate": (external / (len(seen) - 1)) if len(seen) > 1 else 0.0}


def record_sighting(g: Graph, thread: str, target: str, before: dict, *,
                    source: str | None = None, keep=None, when: str | None = None) -> tuple:
    """Turn "we looked at `target`" into observations, by comparing its attributes to `before`.

    ⚠ **The encoding default is the slots of the thing being LOOKED AT**, which is the attention gate made
    structural: `dispatch.service` is called *on a target*, and that target is by definition what is being
    attended to. Everything else the tool happened to touch is the walk to school — not encoded, and that
    is the correct outcome rather than a loss.

    ⚠ **EVERY slot of the target, not only the ones the tool rewrote**, because that is what "I checked
    this" means — the state it was in at that moment. A difference-only record would be cheaper and could
    not tell *unchanged* from *unobserved*, which is the `UNKNOWN` conflation one level up, and it would
    leave "when did I last check?" unanswerable for anything stable. The provenance is therefore per-look,
    not per-slot: `source` says which look produced the sighting, never that the tool reported that field.

    `keep(slot) -> bool` is the seam that overrides in either direction. ⚠ **Inert by default**, exactly as
    `pursue`'s decision seam shipped inert: passing nothing keeps the disposition unchanged, and a decision
    has to speak up to alter it."""
    now = g.attrs.get(target, {})
    out = []
    # ⭐ ONE LOOK IS ONE MOMENT, and every slot it saw shares it. That is the cardinality the time-node
    # direction exists for: a timestamp *attribute* would write the same reading onto each observation and
    # invite them to drift, while one moment pointing at all of them cannot disagree with itself. It also
    # makes *"what did we learn in that one look?"* an O(1) reverse walk from the moment.
    # ⚠ `when` is passed in by `dispatch.service` so the sightings and the nodes the action PRODUCED
    # share one moment — the same action cannot have happened at two times. Minting our own when none is
    # given keeps every other caller working.
    from . import clock as C
    seen_at = when if when is not None else C.now(g)
    for key in sorted(set(now) | set(before)):
        if key == "kind":
            continue
        if keep is not None and not keep({"node": target, "key": key,
                                          "was": before.get(key), "now": now.get(key)}):
            continue
        out.append(observe(g, thread, target, key, now.get(key), source=source, why="looked",
                           when=seen_at))
    return tuple(out)


def describe(g: Graph, thread: str, node: str, key: str) -> str:
    """What is known about how this slot got the way it is — the answer to *"was it me?"*, in words."""
    seen = sightings(g, thread, node, key)
    if not seen:
        return f"{key}: never looked at"
    lines = [f"{key}: {len(seen)} sighting(s), now {g.attr(seen[-1], 'value')!r}"]
    for a, b in transitions(g, thread, node, key):
        who = attribute(g, thread, a, b)
        by = ", ".join(sorted({g.attr(x, "function") for x in who["by"]}))
        lines.append(f"  {g.attr(a, 'value')!r} -> {g.attr(b, 'value')!r}: {who['verdict']}"
                     + (f" ({by})" if by else " — nothing I did could have"))
    return "\n".join(lines)


__all__ = ["OBSERVATION", "MINE", "EXTERNAL", "BOTH", "observe", "sightings", "believed",
           "transitions", "attribute", "volatility", "record_sighting", "describe"]
