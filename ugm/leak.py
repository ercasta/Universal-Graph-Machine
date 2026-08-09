"""Leak audit — is a frame's state exactly what its transformation licensed?

The requirement this serves is *no leak under composition*: reasoning must not produce information the
facts did not license. For the frame mechanism that has an exact form, and it falls out of frames being
Memento — a frame stores **what was done** (`via` → a transformation, which names the function applied,
the activation that ran it and the hypothesis it assumed) alongside **what changed** (its mappings, each
an identity and the version in force here).

Those two are not a duplication, they are two jobs: the transformation is the residue that answers *why
is the state this way*, and the mapping index is the O(1) answer to *what is the state*. Pure Memento
would keep only the first and replay from the root, which makes reads O(history). Keeping only the
second is speed with no explanation, and the explanation is the thesis.

⭐ **But keeping both means they can disagree, and this codebase has a standing lesson that carrying one
fact in two shapes is how they drift.** So the pairing hands over an invariant for free:

> **Every entry in a frame's delta must be attributable to that frame's transformation.**

An entry nothing in the transformation accounts for *is* information no operation licensed. The
attribution needs no new machinery: `activation.minted` already records what a call brought into
existence, callees included, and it is exact rather than an over-approximation — it exists precisely
because the whole-graph diff it replaced answered *what nodes appeared anywhere* when the question was
*what did this call add*.

Two forms, catching different things:

* **containment** — the delta's versions are among what the activation minted. Cheap enough to run on
  every step, which is what makes it useful during a conversion.
* **replay** — re-run the transformation chain from the root and compare against the stored index. Not
  built here; it is the `_python_step` pattern, except the reference implementation is free because it
  is the history.

⚠ Run this **before** a representation change, not after. During a change that moves every relation from
an edge to a node, a suite going red says a hundred things at once and none of them says *leak*.

`python -m ugm.leak`.
"""
from __future__ import annotations

from . import activation as A, workbench as W
from .graph import Graph

VIA, RAN = "via", "ran"


def transformation_of(g: Graph, frame: str):
    """What was applied to produce this frame, or `None` for a root frame.

    A root frame has no transformation and must not be audited against one: it maps *everything* by
    construction — `frame 0 maps everything, always` — so it is the workbench's starting position rather
    than the result of an operation. Auditing it would report the entire world as unlicensed, which is
    the kind of finding that discredits an instrument rather than the code."""
    return g.target(frame, VIA)


def licensed_by(g: Graph, frame: str) -> set:
    """Every node the transformation behind this frame brought into existence.

    ⚠ The activation is reached through the transformation rather than assumed: `ran` is what ties the
    record of the step to the call that performed it, and it is the only link between the two that
    survives the call's own scaffolding being discarded."""
    t = transformation_of(g, frame)
    if t is None:
        return set()
    act = g.target(t, RAN)
    return set(A.minted(g, act)) if act is not None else set()


def unlicensed(g: Graph, frame: str) -> tuple:
    """The mappings in this frame's delta that its transformation does not account for.

    A mapping is accounted for when the **version it points at** was minted by the step — that is what
    *the writer mints a version the first time a frame writes to a node* means, read backwards. The
    mapping node itself is checked too: a delta entry minted by something other than the step is an
    entry some other call put there, which is the same defect wearing a different node."""
    if transformation_of(g, frame) is None:
        return ()
    ok = licensed_by(g, frame)
    out = []
    for m in W.mappings(g, frame):
        image = g.target(m, "image")
        if m not in ok or (image is not None and image not in ok):
            out.append(m)
    return tuple(out)


def audit(g: Graph) -> dict:
    """Every frame in the graph, and what its transformation fails to account for.

    Reports the population as well as the offenders, because *no leaks* and *nothing to leak* are the
    same sentence otherwise — the standing lesson that a pass reporting no gaps and a pass that cannot
    see gaps read alike."""
    frames = [n for n in g.nodes if g.kind(n) == "frame"]
    audited = [f for f in frames if transformation_of(g, f) is not None]
    bad = {f: unlicensed(g, f) for f in audited}
    bad = {f: v for f, v in bad.items() if v}
    # ⚠ How much the invariant is actually asking. Containment is satisfied for free if a step licenses
    # far more than it writes, and *no leaks* would then mean *the net has holes the size of the fish*.
    # `minted` includes the call's own scaffolding, so this ratio is expected to be well above 1 — the
    # number is here to be looked at, not to have a threshold, and it is the first thing to re-read if
    # this pass ever reports green through a change it should have caught.
    licensed = sum(len(licensed_by(g, f)) for f in audited)
    entries = sum(len(W.mappings(g, f)) for f in audited)
    return {"frames": len(frames),
            "audited": len(audited),
            "roots": len(frames) - len(audited),
            "entries": entries,
            "licensed": licensed,
            "slack": round(licensed / entries, 1) if entries else None,
            "leaking_frames": len(bad),
            "unlicensed": sum(len(v) for v in bad.values()),
            "worst": sorted(bad.items(), key=lambda kv: -len(kv[1]))[:5]}


def _control(g: Graph) -> bool:
    """Plant an unlicensed entry and confirm the audit reports it.

    ⚠ Without this the pass is worth nothing: *a check that asserts no offenders must also assert that
    it can still see one*, which is the vacuity that left `EVERY_TEACHING_RULE_IS_MEDIATED` green with
    its instrument stubbed. The entry is planted the way a real leak would arrive — a mapping added to a
    frame by something that is not the step that made the frame."""
    victim = next((f for f in g.nodes
                   if g.kind(f) == "frame" and transformation_of(g, f) is not None), None)
    if victim is None:
        return False
    before = len(unlicensed(g, victim))
    m = g.mint("mapping")
    g.link(m, "original", victim)
    g.link(m, "image", victim)
    g.link(victim, "mapping", m)
    seen = len(unlicensed(g, victim)) == before + 1
    g.unlink(victim, "mapping", dst=m)
    return seen


def report() -> str:
    from . import driver as D, selftest as S, thread as T
    g, world = S._blocks()
    goal, _abc = S._sussman(g, world)
    D.pursue(g, goal, T.open_thread(g), world, max_steps=200, max_depth=5)

    a = audit(g)
    control = _control(g)
    lines = [f"frames {a['frames']} ({a['roots']} root, {a['audited']} audited), "
             f"{a['entries']} delta entries",
             f"control — a planted unlicensed entry is reported: "
             f"{'yes' if control else 'NO, this audit means nothing'}",
             f"slack — {a['licensed']} nodes licensed for {a['entries']} written, "
             f"{a['slack']}× (how loose the net is; scaffolding is in the numerator)",
             f"unlicensed entries: {a['unlicensed']} across {a['leaking_frames']} frames"]
    for f, v in a["worst"]:
        t = transformation_of(g, f)
        lines.append(f"  {f}: {len(v)} unaccounted, applied {g.target(t, 'applies')}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
