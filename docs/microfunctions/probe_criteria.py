"""PROBE — expert judgement as an ordered list of criteria (docs/microfunctions/expert_judgement.md §8).

Four questions:
  1. does first-match expert judgement solve Sussman?
  2. HOW MANY criteria does it take?  (one is knowledge; five is encoding the answer)
  3. does coverage hold under perturbation?
  4. what could the condition language NOT say without a loop?

⚠ The prune arm cannot be wired without an engine change (`allow` filters on function NAME only, and
`decide` runs after `take_best`). So criteria are wired as a DOMINATING `rank`, and the cost a pruning
version would have paid is read off `imagined steps vs plan length`: if they are equal, every criterion
pick was on the winning path and pruning would have been free and correct.
"""
from __future__ import annotations
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from microfunctions import driver as D, goal as G, path as PATH, thread as T, workbench as W
from microfunctions.selftest import _blocks

RESIDUE = []          # question 4: what the condition language could not say


def note_residue(what):
    if what not in RESIDUE:
        RESIDUE.append(what)


# --- reading the imagined world -------------------------------------------------------------------
def here(g, frame, real):
    """The image of a REAL node inside this frame.

    ⚠ `W.mapping_for` matches on the IMMEDIATE `original`, which is not always the real node; fall back to
    `W.resolve`, which walks the whole chain out of every nested workbench."""
    m = W.mapping_for(g, frame, real)
    if m is not None:
        return W.image_of(g, m)
    for m in W.mappings(g, frame):
        if W.resolve(g, m) == real:
            return W.image_of(g, m)
    return None


def real(g, node):
    return W.original_of(g, node) if node is not None else None


def on_what(g, frame, block):
    """What `block` is sitting on, in this frame — as a REAL node."""
    img = here(g, frame, block)
    return real(g, g.target(img, "on")) if img is not None else None


def whats_on(g, frame, block):
    """The block sitting on `block` in this frame, or None.

    ⚠⚠ **NOT residue, and the first version of this probe said it was.** The inverse hop already exists:
    `x.^on`, in the path grammar since `path.py` was written. It resolves only when exactly one node
    points that way — true of a block, false of the ground — which is why this hand-rolled version filters
    on `kind_of`. See `c1_directly_on_via_paths` for the same thing said in the reference language."""
    img = here(g, frame, block)
    if img is None:
        return None
    riders = [s for s in g.sources(img, "on") if g.attr(s, "kind_of") == "block"]
    return real(g, riders[0]) if riders else None


def is_clear(g, frame, block):
    img = here(g, frame, block)
    return bool(img is not None and g.attr(img, "clear"))


def wants_on(g, goal):
    """The goal's `on` constraints as (subject, object) REAL pairs — the closed-sort key of §7."""
    out = []
    for c in G.constraints(g, goal):
        if g.attr(c, "sort") == "link" and g.attr(c, "label") == "on":
            out.append((g.target(c, "subject"), g.target(c, "object")))
    return out


def settled(g, frame, goal, block):
    """Is `block` already where the goal finally wants it? True if the goal says nothing about where it
    goes, or if that constraint already holds in this frame."""
    for x, y in wants_on(g, goal):
        if x == block:
            return on_what(g, frame, block) == y
    return True                       # the goal never says where it goes — it is already final


# --- THE CRITERIA, in precedence order -------------------------------------------------------------
def c1_clear_the_way(g, frame, goal, ground):
    """⭐ If the goal wants X on Y and something is sitting on X or on Y, take that thing off.

    This is the whole of Sussman's knowledge: the move that closes nothing but unblocks everything."""
    for x, y in wants_on(g, goal):
        for blocked in (x, y):
            rider = whats_on(g, frame, blocked)
            if rider is not None:
                if not is_clear(g, frame, rider):
                    # This criterion cannot name "the TOPMOST block above x" and therefore gives up. That
                    # is the coverage gap the two-deep-blocker scenario exposes.
                    # ⚠⚠ It needs a SET-VALUED READER AND A SELECTOR, **not a loop** — `path.via` already
                    # walks the pile nearest-first, so the topmost is simply the last one. Measured:
                    # `c0_topmost_via_paths` reproduces the hand-rolled `while` version exactly.
                    note_residue("SET POSITION + SELECTOR — 'the TOPMOST block above x'. `path.via` "
                                 "already does the traversal; what is missing is a surface form that may "
                                 "denote a SET and pick one from it. NOT control flow.")
                    continue
                return ("unstack", {"b": rider, "floor": ground}, "clear the way")
    return None


def c2_build_from_the_bottom(g, frame, goal, ground):
    """⭐ If the goal wants X on Y, both are clear, and Y is already in its final place — stack X on Y.

    The `settled` test is the ordering knowledge: build bottom-up, or you stack onto something that still
    has to move."""
    for x, y in wants_on(g, goal):
        if on_what(g, frame, x) == y:
            continue                                     # already done
        if is_clear(g, frame, x) and is_clear(g, frame, y) and settled(g, frame, goal, y):
            return ("stack", {"b": x, "onto": y}, "build from the bottom up")
    return None


def c0_take_off_the_topmost(g, frame, goal, ground):
    """⭐⭐ THE ONE THAT NEEDS A LOOP. If the goal wants X on Y and anything is above X or Y, take off the
    **topmost** block of that pile — not the one directly on top, which may itself be buried.

    ⚠ `while` here is the thing §4 forbids. As a BOUNDED form it is fine: iterate `on` upward, and the
    collection is finite and already materialised. This criterion exists to measure whether the residue is
    load-bearing — compare `LOOP=False`."""
    for x, y in wants_on(g, goal):
        for blocked in (x, y):
            top, guard = whats_on(g, frame, blocked), 0
            if top is None:
                continue
            while not is_clear(g, frame, top) and guard < 20:      # ⚠ bounded iteration
                nxt = whats_on(g, frame, top)
                if nxt is None:
                    break
                top, guard = nxt, guard + 1
            if is_clear(g, frame, top):
                return ("unstack", {"b": top, "floor": ground}, "take off the topmost")
    return None


def c0_topmost_via_paths(g, frame, goal, ground):
    """⭐⭐ THE SAME CRITERION WITH NO CONTROL FLOW — written in the EXISTING reference language.

    `path.via(x, "on", back=True)` is the pile above `x`, breadth-first so **nearest first**; the topmost
    is therefore *the last one*. No `while`, no recursion: a **set-valued reader plus a selector**.

    ⚠ `via` is deliberately NOT reachable from the path grammar — a reference that denoted a set would
    break `node_at`'s promise of one node. So what a criterion vocabulary needs is a **set position with a
    selector**, which is a new surface form but is not a loop."""
    for x, y in wants_on(g, goal):
        for blocked in (x, y):
            img = here(g, frame, blocked)
            if img is None:
                continue
            pile = PATH.via(g, img, "on", back=True)          # bounded: finite, already materialised
            pile = [n for n in pile if g.attr(n, "kind_of") == "block"]
            if pile:
                return ("unstack", {"b": real(g, pile[-1]), "floor": ground}, "the topmost of the pile")
    return None


def c1_directly_on_via_paths(g, frame, goal, ground):
    """`x.^on` — the inverse hop the path grammar has had all along. ⚠ It resolves only when EXACTLY one
    node points that way, which is true of a block and false of the ground."""
    for x, y in wants_on(g, goal):
        for blocked in (x, y):
            img = here(g, frame, blocked)
            rider = PATH.node_at(g, img, PATH.parse("^on")) if img is not None else None
            if rider is not None and g.attr(rider, "clear"):
                return ("unstack", {"b": real(g, rider), "floor": ground}, "the block directly on it")
    return None


CRITERIA = []



# --- wiring them as a dominating rank ---------------------------------------------------------------
def make_rank(g, goal, ground, log):
    memo = {}

    def pick_for(frame):
        if frame not in memo:
            memo[frame] = None
            for cname, crit in CRITERIA:                 # FIRST MATCH WINS — declaration order
                got = crit(g, frame, goal, ground)
                if got is not None:
                    memo[frame] = (cname,) + got
                    break
        return memo[frame]

    def rank(gr, name, bindings, unmet):
        base = D.relevance(gr, name, bindings, unmet)
        if not bindings:
            return base
        anchor = next(iter(bindings.values()))
        # ⚠ `sources(m, "mapping")` returns BINDING nodes as well as the frame — `W.step` links
        # `binding -mapping-> m` too. Filtering by kind is not optional.
        frames = [f for f in gr.sources(anchor, "mapping") if gr.kind(f) == "frame"]
        if not frames:
            return base
        got = pick_for(frames[0])
        if got is None:
            return base                                  # SILENT — `relevance` ranks, as designed
        cname, fname, want, why = got
        if name != fname:
            return base
        bound = {p: W.resolve(gr, m) or W.image_of(gr, m) for p, m in bindings.items()}
        if bound == want:
            log.append((cname, fname, tuple(sorted(gr.attr(n, "label") or n for n in want.values())), why))
            return 100.0                                 # dominating — the expert's pick goes first
        return base

    return rank


# --- worlds -----------------------------------------------------------------------------------------
def blocks_world(n=3):
    """`_blocks()` with n blocks instead of 3 — same library, same types."""
    g, world = _blocks()
    if n > 3:
        ground = g.target(world, "ground")
        for i in range(3, n):
            label = "abcdefghijklmnopqrstuvwxyz"[i] if i < 26 else f"b{i}"
            b = g.mint("block", kind_of="block", label=label, clear=True, height=1)
            g.link(b, "on", ground)
            g.link(world, "block", b)
    return g, world


def tower_goal(g, world, pairs, label):
    goal = G.open_goal(g, label=label)
    blocks = {g.attr(b, "label"): b for b in g.targets(world, "block")}
    for x, y in pairs:
        G.require_link(g, goal, blocks[x], "on", blocks[y])
    return goal, blocks


def put_on(g, top, under):
    g.unlink(top, "on", index=0)
    g.link(top, "on", under)
    g.put(under, clear=None)
    g.put(top, height=g.attr(under, "height", 0) + 1)


def run(label, build, *, max_steps=800, max_depth=7):
    g, world, goal = build()
    ground = g.target(world, "ground")
    log = []
    guided = D.pursue(g, goal, T.open_thread(g), world, max_steps=max_steps, max_depth=max_depth)

    g2, world2, goal2 = build()
    ground2 = g2.target(world2, "ground")
    log2 = []
    expert = D.pursue(g2, goal2, T.open_thread(g2), world2, max_steps=max_steps, max_depth=max_depth,
                      rank=make_rank(g2, goal2, ground2, log2))
    _ = ground, log
    plan = D.plan_steps(g2, expert) if expert["found"] else ()
    return {"scenario": label,
            "relevance_only": (guided["found"], guided.get("steps"),
                               D.plan_steps(g, guided) if guided["found"] else ()),
            "with_criteria": (expert["found"], expert.get("steps"), plan),
            "criteria_fired": len(log2),
            "PRUNE_WOULD_HAVE_BEEN_FREE": bool(expert["found"] and expert.get("steps") == len(plan)),
            "picks": log2[:12]}


# --- the scenarios ----------------------------------------------------------------------------------
def sussman():
    g, world = blocks_world(3)
    goal, b = tower_goal(g, world, [("a", "b"), ("b", "c")], "a on b on c")
    put_on(g, b["c"], b["a"])                            # C on A — the anomaly
    return g, world, goal


def plain_tower():
    g, world = blocks_world(3)
    goal, _ = tower_goal(g, world, [("a", "b"), ("b", "c")], "a on b on c")
    return g, world, goal


def sussman_reordered():
    """Same world, goal constraints DECLARED in the other order."""
    g, world = blocks_world(3)
    goal, b = tower_goal(g, world, [("b", "c"), ("a", "b")], "b on c, a on b")
    put_on(g, b["c"], b["a"])
    return g, world, goal


def four_blocks():
    """A fourth block, and a deeper goal: a on b on c on d, with d sitting on a."""
    g, world = blocks_world(4)
    goal, b = tower_goal(g, world, [("a", "b"), ("b", "c"), ("c", "d")], "a on b on c on d")
    put_on(g, b["d"], b["a"])
    return g, world, goal


def two_deep_blocker():
    """⚠ THE PERTURBATION THAT SHOULD HURT: TWO blocks stacked on the one that must move.
    c on a, and d on c. Criterion 1 can name `c` but `c` is not clear, and nothing can say 'the topmost'."""
    g, world = blocks_world(4)
    goal, b = tower_goal(g, world, [("a", "b")], "a on b")
    put_on(g, b["c"], b["a"])
    put_on(g, b["d"], b["c"])
    return g, world, goal


SCENARIOS = [("SUSSMAN", sussman),
             ("plain tower", plain_tower),
             ("SUSSMAN, goal reordered", sussman_reordered),
             ("PERTURBED: 4 blocks, 3 constraints", four_blocks),
             ("PERTURBED: two-deep blocker", two_deep_blocker)]


def sweep(title):
    print(f"\n{'='*94}\n{title}   [criteria: {len(CRITERIA)} -> {[c for c, _ in CRITERIA]}]\n{'='*94}")
    print(f"{'scenario':38} {'imagined':>18}   {'plan length':>13}   verdict")
    print(f"{'':38} {'relevance / criteria':>18}   {'rel / crit':>13}")
    for name, build in SCENARIOS:
        r = run(name, build)
        (rf, rs, rp), (ef, es, ep) = r["relevance_only"], r["with_criteria"]
        if not ef:
            verdict = "!! NO PLAN"
        elif len(ep) > len(rp):
            verdict = f"WORSE PLAN (+{len(ep)-len(rp)})" + \
                      ("  and a prune would have LOCKED IT IN" if r["PRUNE_WOULD_HAVE_BEEN_FREE"] else "")
        elif len(ep) < len(rp):
            verdict = f"BETTER PLAN (-{len(rp)-len(ep)})"
        else:
            verdict = "same plan"
        print(f"{name:38} {rs:>8} / {es:<7}   {len(rp):>5} / {len(ep):<5}   {verdict}")



CRITERIA = []          # set per sweep


if __name__ == "__main__":
    variants = [("LOOP-FREE    hand-rolled  ('the block DIRECTLY on x')",
                 [("clear the way", c1_clear_the_way),
                  ("build from the bottom", c2_build_from_the_bottom)]),
                ("BOUNDED LOOP hand-rolled  ('the TOPMOST block above x')",
                 [("take off the topmost", c0_take_off_the_topmost),
                  ("build from the bottom", c2_build_from_the_bottom)]),
                ("PATH-ONLY, NO CONTROL FLOW  (path.via + a selector)",
                 [("the topmost of the pile", c0_topmost_via_paths),
                  ("build from the bottom", c2_build_from_the_bottom)]),
                ("PATH-ONLY, inverse hop only  (x.^on)",
                 [("directly on it", c1_directly_on_via_paths),
                  ("build from the bottom", c2_build_from_the_bottom)])]
    for title, crits in variants:
        CRITERIA[:] = crits
        sweep(title)
    print()
    print("=== CONDITION-LANGUAGE RESIDUE (question 4) ===")
    for r in RESIDUE:
        print("  - " + r)
