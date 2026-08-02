"""PROBE — IS AN EXPECTATION A CONSTRAINT? (the user's question, 2026-08-02)

> I think expectations should be **constraints**, not models; or maybe they are the same thing?

Worth taking seriously because the two were built years apart in this design's history and have never been
compared. Laid side by side they look like the same three sorts said twice:

    goal.py  sorts : link (± transitive) | attr (± comparison op) | type | known
    predicted_changes : links (label, presence, target) | attrs (key, want) | minted (kinds)

If they ARE the same, then a mock is not an alternative to a constraint — it is a **way of computing
one**, and `workbench.unmet_expectations` and `goal.unmet` are two evaluators of one thing, which is the
"two vocabularies, one meaning" defect this codebase keeps finding (`intake._shape`: one proposition
grammar, three parsers that had drifted four ways).

Three questions, and the third is the one that decides it:

  (Q1) **Does every form `predicted_changes` produces translate into a goal constraint?**
  (Q2) **Do the two evaluators AGREE** on the translatable ones — same world, same verdict? If they
       disagree, they are not the same thing however alike they read.
  (Q3) **What does NOT translate**, exactly? A residue is the interesting answer: it says which side is
       the more expressive, and that is a fact about the design nobody has written down.

⚠ Q2 needs a world where the expectation genuinely FAILS, or two evaluators that both say "fine" would
agree vacuously.
"""
from __future__ import annotations
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from microfunctions import asm, dispatch as D, execution as X, function as fn   # noqa: E402
from microfunctions import goal as G, types as TY, workbench as W               # noqa: E402
from microfunctions.graph import new_graph                                      # noqa: E402

declare = TY.declare_type
bar = "=" * 88


def scanner():
    """One step that predicts an EXACT attribute, an EXISTENTIAL link, and a MINT — three forms at once."""
    g = new_graph()
    declare(g, "dir", attrs={"kind_of": "dir"})
    declare(g, "listing", base="dir", attrs={"listed": True})
    declare(g, "file", attrs={"kind_of": "file"})
    asm.load_text(g, "\n".join([
        "fn scan_dir(d: dir) -> listing:",
        '    DISPATCH R(out) "ls" F(d)',
        '    SET F(d) "listed" true',
        "",
        "fn found_two(d: dir) -> listing mocks scan_dir:",
        '    SET F(d) "listed" true',
        '    SET F(d) "dirty" true',                 # an EXACT attribute expectation
        '    NEW R(f1) "file"', '    LINK F(d) "file" R(f1)',
        '    NEW R(f2) "file"', '    LINK F(d) "file" R(f2)',
    ]))
    d = g.mint("dir", kind_of="dir")
    g.link("root", "has", d)
    return g, d


# --- Q1/Q3: TRANSLATE each predicted form into a goal constraint ----------------------------------------
def translate(g, prediction, goal, bound):
    """Express a derived expectation as goal constraints. Returns (made, untranslatable)."""
    made, stuck = [], []
    for m, key, want in prediction["attrs"]:
        subject = bound.get(m)
        if subject is None:
            continue
        if want == "<set>":
            made.append(("known", G.require_known(g, goal, subject, key)))
        else:
            made.append(("attr", G.require_attr(g, goal, subject, key, want)))
    for m, label, presence, target in prediction["links"]:
        subject = bound.get(m)
        if subject is None:
            continue
        if target is not None:
            made.append(("link", G.require_link(g, goal, subject, label, target)))
        elif presence == "some":
            stuck.append(f"SOME {label!r} edge on {subject} (existential link, no named object)")
        else:
            stuck.append(f"NO {label!r} edge on {subject} (negative link)")
    for kind in sorted(prediction["minted"]):
        if TY.find_type(g, kind) is not None:
            made.append(("type", G.require_type(g, goal, kind)))
        else:
            stuck.append(f"some new node of graph KIND {kind!r} (no declared type of that name)")
    return made, stuck


g, d = scanner()
wb = W.open_workbench(g, d)
f0 = W.root_frame(g, wb)
f1, tr = W.step(g, wb, f0, "scan_dir", {"d": W.mapping_for(g, f0, d)}, assume="found_two")
pred = W.predicted_changes(g, f0, f1)

print(bar)
print("  WHAT THE PLAN ANTICIPATED, in `predicted_changes`' own vocabulary")
print(bar)
print(f"  attrs  : {[(k, v) for _m, k, v in pred['attrs']]}")
print(f"  links  : {[(l, p, t) for _m, l, p, t in pred['links']]}")
print(f"  minted : {sorted(pred['minted'])}")

# reality: git-style lie — nothing appeared, and the flag was not set
D.register("ls", lambda gr, target: gr.put(target, count=0))
result = X.execute(g, wb, f1)
missed = (result["deviation"] or {}).get("unmet_expectations", ())
bound = result["bindings"]

print()
print(bar)
print("  Q1/Q3 — TRANSLATING IT INTO GOAL CONSTRAINTS")
print(bar)
# ⚠ `label=`, NOT positional: `open_goal`'s first argument is `want`, which is sugar for a TYPE
# constraint. Passing the prose there minted a constraint for a type that does not exist, and `unmet`
# duly reported "something is a what that step said would happen" — a self-inflicted extra failure that
# would have made the two evaluators look like they disagreed.
goal = G.open_goal(g, label="what that step said would happen")
made, stuck = translate(g, pred, goal, bound)
for sort, c in made:
    print(f"  [{sort:5}] {G.describe_constraint(g, c)}")
for s in stuck:
    print(f"  [ -- ] UNTRANSLATABLE: {s}")

print()
print(bar)
print("  Q2 — DO THE TWO EVALUATORS AGREE, in the same failed world?")
print(bar)
still_open = G.unmet(g, goal)
print(f"  workbench.unmet_expectations says : {list(missed)}")
print(f"  goal.unmet says                   : "
      f"{[G.describe_constraint(g, c) for c in still_open]}")

# The discriminating comparison: the ATTR expectation failed, and both must say so.
attr_missed = any("dirty" in m for m in missed)
attr_unmet = any(g.attr(c, "sort") == "attr" and g.attr(c, "key") == "dirty" for c in still_open)
# ...and the `listed` claim is the CAST's business, so neither should be reporting it.
neither_claims_listed = (not any("listed" in m for m in missed)
                         and not any(g.attr(c, "key") == "listed" for c in still_open))

print()
print(f"  both flag the broken ATTR expectation : {attr_missed and attr_unmet}")
print(f"  neither re-checks the CAST's own slot : {neither_claims_listed}")

# --- the OTHER link form: an edge that must be GONE ------------------------------------------------------
print()
print(bar)
print("  AND THE NEGATIVE FORM — a step that predicts an edge DISAPPEARS")
print(bar)

g2 = new_graph()
declare(g2, "dir", attrs={"kind_of": "dir"})
declare(g2, "listing", base="dir", attrs={"listed": True})
asm.load_text(g2, "\n".join([
    "fn clear_out(d: dir) -> listing:",
    '    DISPATCH R(out) "rm" F(d)',
    '    SET F(d) "listed" true',
    "",
    "fn assume_emptied(d: dir) -> listing mocks clear_out:",
    '    SET F(d) "listed" true',
    '    UNLINK F(d) "file" 0',
]))
d2 = g2.mint("dir", kind_of="dir")
g2.link("root", "has", d2)
g2.link(d2, "file", g2.mint("file", kind_of="file"))
wb2 = W.open_workbench(g2, d2)
f0b = W.root_frame(g2, wb2)
f1b, _ = W.step(g2, wb2, f0b, "clear_out", {"d": W.mapping_for(g2, f0b, d2)}, assume="assume_emptied")
pred2 = W.predicted_changes(g2, f0b, f1b)
neg = [(l, p, t) for _m, l, p, t in pred2["links"]]
print(f"  links predicted : {neg}")
goal2 = G.open_goal(g2, label="the files are gone")
_made2, stuck2 = translate(g2, pred2, goal2, {m: d2 for m in
                                              [mm for mm, _l, _p, _t in pred2["links"]]})
for s in stuck2:
    print(f"  [ -- ] UNTRANSLATABLE: {s}")
print(f"  a goal CANNOT say 'no such edge' : {bool(stuck2)}")

print()
print(bar)
print("  VERDICT")
print(bar)
print(f"  Q1 forms that DID translate      : {sorted({s for s, _ in made})}")
print(f"  Q3 forms that did NOT            : {len(stuck)}")
for s in stuck:
    print(f"       - {s}")
print(f"  Q2 the two evaluators agree      : {attr_missed and attr_unmet}")
print()
print("  If the residue in Q3 is the EXISTENTIAL and NEGATIVE link, then expectations have quietly been")
print("  using constraint forms the GOAL vocabulary cannot say - and unifying them would strengthen goals,")
print("  not merely tidy the code.")
