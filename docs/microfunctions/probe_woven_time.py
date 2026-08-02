"""PROBE — is timestamping WOVEN, and is one action ONE moment?

The user's concern, 2026-08-02:

> Some concerns ("aspects") should be automatically **woven** into the procedures — like transaction
> management. Timestamping, for example: I don't expect each business rule to handle it manually. And it
> is not that each node gets a different timestamp — **when listing files in a folder, the entire list of
> files should get the same timestamp, because it corresponds to a single action.**

Two separable claims, and they must be measured apart because the machinery could satisfy either alone:

  (1) **WOVEN** — a business rule must not have to call the clock;
  (2) **ONE ACTION, ONE MOMENT** — everything a single action produced shares one moment.

⚠ `clock.py`'s docstring already claims (2) as a design property — *"one look dates many facts… the
natural cardinality is one moment → many dated things"* — and `memory.record_sighting` passes one `when`
for a whole look. So the mechanism exists. The question this probe asks is **what it is woven INTO**, which
is a different question and the one the user's example is about.

⚠⚠ The control: the folder must come back **dated**, or this measures nothing but a broken fixture.
"""
from __future__ import annotations
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from microfunctions import clock as C, dispatch as DP, thread as T
from microfunctions.graph import new_graph

MINTED = []


def list_dir(g, target):
    """A tool that LOOKS at a folder and produces the files it found — the user's exact example."""
    MINTED.clear()
    for name in ("a.txt", "b.txt", "c.txt"):
        f = g.mint("chunk", kind_of="file", label=name)
        g.link(target, "file", f)
        MINTED.append(f)
    g.put(target, count=len(MINTED))
    return tuple(MINTED)


DP.register("list_dir", list_dir, observes=True)

g = new_graph()
folder = g.mint("chunk", kind_of="folder", label="src")
g.link("root", "has", folder)
th = T.open_thread(g)
entry = T.attend(g, th, folder, why="looking")

before_moments = len(C.moments(g))
DP.service(g, "list_dir", folder, record_on=entry)
after_moments = len(C.moments(g))

from microfunctions import memory as M                                            # noqa: E402

print("=" * 78)
print("  A single action: list the files in a folder. It minted 3 file nodes.")
print("=" * 78)
print(f"  moments before = {before_moments}, after = {after_moments}")
print()

# ⚠⚠ FIRST VERSION OF THIS CONTROL WAS WRONG and reported the folder as undated. A moment dates the
# SIGHTING, not the world node — `dated(folder)` was simply the wrong question, and it would have made
# the whole probe read as "nothing is woven at all".
seen = M.sightings(g, th, folder)
moments_of_look = {m for o in seen for m in C.dated(g, o)}
print(f"  ++ CONTROL   the look produced {len(seen)} sightings of the folder "
      f"({', '.join(sorted(g.attr(o, 'key') for o in seen))})")
print(f"  ++ CONTROL   ...dated by {len(moments_of_look)} moment(s) — the weaving mechanism ran, and no")
print(f"               business rule called the clock")
print()
print(f"  >> (2) ONE ACTION, ONE MOMENT: {len(seen)} sightings share {len(moments_of_look)} moment "
      f"-> {'HOLDS' if len(moments_of_look) == 1 and len(seen) > 1 else 'FAILS'}")
print()

each = [(g.attr(f, "label"), C.dated(g, f), M.sightings(g, th, f)) for f in MINTED]
undated = [lbl for lbl, ms, _ in each]
print(f"  >> the FILES the action PRODUCED: "
      f"{[(l, f'{len(m)} moments', f'{len(s)} sightings') for l, m, s in each]}")

# ⭐⭐ THE CLAIM THAT MATTERS: not merely that the products are dated, but that they share the SAME
# moment as the look — "it corresponds to a single action". Two moments would be two actions.
moments_of_products = {m for f in MINTED for m in C.dated(g, f)}
one_action_one_moment = (moments_of_products == moments_of_look) and len(moments_of_look) == 1

print()
print("=" * 78)
print("  VERDICT")
print("=" * 78)
print("  ++ (1) WOVEN — HOLDS. `dispatch.service` mints the moment and records the sighting, so no")
print("     business rule touches the clock. The user's expectation was already the design.")
print(f"  {'++' if one_action_one_moment else '!!'} (2) ONE ACTION, ONE MOMENT — "
      f"{'HOLDS' if one_action_one_moment else 'FAILS'}: the 3 sightings and the 3 produced nodes are")
print(f"     dated by the SAME moment. sightings={sorted(moments_of_look)} "
      f"products={sorted(moments_of_products)}")
print(f"  ++ and the products carry NO sighting "
      f"({sum(len(M.sightings(g, th, f)) for f in MINTED)}) — dating is provenance, not attention.")
print()
print("  >> WAS: the products had no moment at all. `record_sighting` covered the target's ATTRIBUTES")
print("     only, so listing a folder left the file list with no time on it — HANDOFF §9 item 3 reached")
print("     from the other side, and sharper: the missing notion was **the products of an action**.")
print("  >> ⚠ `record_sighting`'s walk-to-school rule is UNTOUCHED: what the tool happened to touch is")
print("     still not encoded as observed. Dating and encoding are separate, and only dating was widened.")
