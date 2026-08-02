"""Selection — choosing which function to apply to which head, one step at a time.

Under rule matching, dispatch was automatic: everything applicable fired, which is fast to write
and produces exactly the defects this project spent a long time cataloguing. Here nothing happens
unless something chooses, so selection is not an optimisation, it is the control flow.

Three stages, deliberately separated, because conflating them is what made matching hard to
reason about.

1. Candidates — which functions could apply to a head, answered by the declared parameter types.
   This is matching in its demoted role: bounded, one node at a time, no fixpoint.
2. Ranking — which of them should go first. Ordinary data in a declared priority, plus one
   structural rule, plus an optional external scorer, which is where a language model plugs in
   reading the function catalogue's natural-language docs.
3. Applying — invoke it, and record the application, so the next round can see what happened.

The idempotence rule is structural and it is the one that earned its place: a candidate already
applied to this node is dropped. Under rules, "did this already fire for this reason" needed a
consumption marker per rule, authored by hand, and forgetting one produced an unbounded stream of
repeated effects. Here it is one check in one place, possible only because applications are
recorded.

What is deliberately not here: no search, no lookahead, no learned preference for sequences.
`step` chooses greedily among ranked candidates. Greedy is honest for now and the hooks for
better are explicit — an external scorer, and recorded episodes for a future selector to learn
from. Non-greedy selection informed by which subsequences work well needs the episode corpus this
module produces, so it comes after rather than with.

See `docs/execution-model.md`.
"""
from __future__ import annotations

from . import application as app
from . import function as fn
from .focus import Focus
from .graph import Graph
from .types import is_a


def candidates(g: Graph, node: str, *, skip_applied: bool = True) -> tuple:
    """Functions whose single declared parameter type validates for `node`.

    Restricted to single-parameter functions on purpose: a multi-parameter function needs a *binding*
    proposed, not just a subject, and inventing bindings is a different problem (search) that should not
    hide inside candidate generation. Such functions stay callable directly; they are just not offered
    for automatic selection."""
    out = []
    for name in fn.names(g):
        ptypes = fn.param_types(g, name)
        params, _ = fn.load(g, name)
        if len(params) != 1 or not ptypes:
            continue
        param = params[0]
        declared = ptypes.get(param)
        if declared is None or not is_a(g, node, declared):
            continue
        if skip_applied and app.has_been_applied(g, name, node):
            continue
        out.append(name)
    return tuple(out)


def score(g: Graph, name: str, node: str, scorer=None) -> float:
    """Rank one candidate. Declared `priority` on the function node is ordinary authored data; `scorer`
    is the hook where a language model (or a learned policy) overrides it, reading the function's
    natural-language doc."""
    if scorer is not None:
        return float(scorer(g, name, node))
    f = fn.find(g, name)
    return float(g.attr(f, "priority", 0) if f is not None else 0)


def rank(g: Graph, node: str, scorer=None, **kw) -> tuple:
    """Candidates best-first. Ties break by name so a run is deterministic — a selector that reorders
    itself between identical runs is not debuggable."""
    cands = candidates(g, node, **kw)
    return tuple(sorted(cands, key=lambda n: (-score(g, n, node, scorer), n)))


def step(g: Graph, node: str, *, episode=None, scorer=None, focus: Focus | None = None):
    """Choose one function and apply it. Returns `(name, application_node)`, or `(None, None)` if nothing
    applies — which is an ordinary answer, not a failure.

    This is the metaprocedure in miniature: not an algorithm run end to end, but one deliberate choice,
    applied, recorded, and then the situation reassessed."""
    ranked = rank(g, node, scorer)
    if not ranked:
        return None, None
    chosen = ranked[0]
    params, _ = fn.load(g, chosen)
    bindings = {params[0]: node}
    try:
        fn.invoke(g, chosen, bindings)
        outcome = "ok"
    except Exception as e:                       # a refused application is data, not a crash
        outcome = f"{type(e).__name__}"
    record = app.record(g, chosen, bindings, episode=episode, outcome=outcome)
    return chosen, record


def run_until_settled(g: Graph, node: str, *, episode=None, scorer=None, max_steps: int = 50) -> tuple:
    """Keep stepping until nothing applies. Returns the sequence of function names applied.

    Termination here is honest rather than proven: the idempotence rule means each function applies to a
    given node at most once, so this loop is bounded by the library size — but `max_steps` stays as a loud
    backstop, because "bounded by an argument I made" is not the same as "bounded"."""
    applied = []
    for _ in range(max_steps):
        name, _rec = step(g, node, episode=episode, scorer=scorer)
        if name is None:
            return tuple(applied)
        applied.append(name)
    raise RuntimeError(f"selection did not settle in {max_steps} steps on {node} — not silently truncated")


__all__ = ["candidates", "score", "rank", "step", "run_until_settled"]
