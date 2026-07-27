"""THE SIEVE — combinatorial closure probing over the axis space.

`forms_cnl.md` §8's `T3`/`T4` as a sweep rather than as hand-authored cases, plus one thing the tests
as specified do not do: **measure the axes instead of assuming them.**

## The oracle, which is the only interesting part

The obvious objection is that the engine can report what it derived but not whether that is *right*, so
where does ground truth come from. It does not have to:

> **A form declares what must never be concluded. A leak is that happening.**

Each form carries `forbids` — the half of `forms_cnl.md` §5's `commits` field that states what believing
it rules *out*. Checking it needs no notion of truth, only of what the run concluded.

⚠ **The first version of this module subtracted a per-form baseline instead**, on the theory that a leak
is *a commitment respected alone and violated in company*. That is wrong here, and the reason is
structural: **there is no "form alone."** A claim always carries a polarity, a force and a level, so a
force form's minimal cell already contains a content form, and any interaction between them is already
in the supposed baseline. The classifier duly graded every leak as a defect in its *victim*. What
`forbids` states is absolute, so nothing needs subtracting — and the baseline machinery survives only
for the much weaker job of asking whether a composite concluded anything new.

## ⭐ The axes are measured, not declared

`forms_discourse` §2.2 asserts three orthogonal axes and never tests them; §12 records that they were
carried over as *"the single most durable result"*, i.e. because nothing had knocked them over.

There is a mechanical test, and it is how phonology derived its feature inventory rather than declaring
one: **two forms occupy the same axis iff they exclude each other.** Free combination means independent
dimensions; mutual refusal means competing values of one slot. `slots()` recovers the partition from
the refusal behaviour and `axis_audit()` compares it to what the entries declare.

## Four verdicts, and three of them are fine

| | |
|---|---|
| `PASS` | every commitment held, and the composite concluded something the parts did not |
| `INERT` | every commitment held, and the composite concluded **nothing new**. ⚠ Not a success: `P8` calls introduction-without-elimination inert, and a composite that goes quiet is that failure at the pair level. It is how a guard *hides* a leak rather than fixing it |
| `REFUSED` | the forms are incompatible and said so. Closed and fine — and it is also the signal `slots()` reads |
| `LEAK` | a commitment held alone and failed in company. **Never fine** |

`BASELINE` is a fifth and marks a cell with fewer than two non-default forms: it is its own control and
grades nothing. `seed_is_sound()` is the precondition — if the all-defaults cell violates anything, no
verdict below it means anything.

## ⚠ What this cannot do

It explores the space **as parameterized**, so it can never discover a form nobody wrote down — only
that the ones present exclude or leak into each other. `slots()` can split a declared axis (it has
evidence: refusals) but cannot invent a missing one. The consolation is Mendeleev-shaped and weak: if
leaks cluster in a shape the slots do not explain, that is a hint, which is why `geometry()` reports
where failures sit rather than only how many there are.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from .forms import (BY_AXIS, DEFAULTS, SEED, Form, excludes, frame, run, signature, slots)

PASS, INERT, REFUSED, LEAK, BROKEN = "PASS", "INERT", "REFUSED", "LEAK", "BROKEN"
BASELINE = "BASELINE"     # one form in the default frame: it IS its own control, so it grades nothing


@dataclass(frozen=True)
class Verdict:
    """One cell's result. `violations` names the form whose commitment failed, which is what makes a
    LEAK actionable rather than merely counted."""

    cell: tuple
    outcome: str
    violations: tuple = ()
    gained: tuple = ()
    detail: str = ""

    @property
    def names(self) -> str:
        return " ∘ ".join(f.name for f in self.cell)

    def __repr__(self) -> str:
        tail = f" [{self.detail}]" if self.detail else ""
        return f"{self.outcome:8} {self.names}{tail}"


def _state(forms: tuple, guarded: bool, composed: bool = False) -> tuple:
    """Run a framed cell: `(ctx, violations, concluded)`. `violations is None` marks a refusal."""
    cell = frame(forms)
    ctx, view, _net = run(cell, guarded, composed)
    if view is None:
        return ctx, None, None
    leaks = tuple((f.name, msg) for f in cell
                  if (msg := f.forbids(ctx, view)) is not None)
    silences = tuple((f.name, msg) for f in cell
                     if (msg := f.commits(ctx, view)) is not None)
    return ctx, (leaks, silences), signature(ctx, view)


def baseline(f: Form, guarded: bool, composed: bool = False) -> tuple:
    """A form **on its own terms**: itself, in the default frame.

    Not the bare form — `frame()` fixes the axes it does not fill, because an unmarked claim is an
    assertion about the world rather than a claim with holes in it."""
    return _state((f,), guarded, composed)


def reference(guarded: bool = False) -> tuple:
    """The all-defaults cell — an unqualified affirmation about the world.

    Every other cell is a departure from this one, and it is the only control the space admits:
    ⚠ **there is no "form alone".** A claim always carries a polarity, a force and a level, so a force
    form's minimal cell already contains a content form and any interaction between them is already in
    it. Subtracting a baseline therefore cannot isolate a leak, which is why `forbids` is absolute."""
    return _state((), guarded)


def seed_is_sound(guarded: bool = False) -> tuple:
    """The precondition. If the reference cell itself violates anything, no verdict below means
    anything — the seed is broken before composition is reached."""
    _ctx, outcome, _s = reference(guarded)
    leaks, silences = outcome
    return leaks + silences


def probe(cell: tuple, guarded: bool = False, composed: bool = False) -> Verdict:
    """Classify one cell.

    ⚠ **A `forbids` violation is a LEAK unconditionally**, with no baseline comparison. That is what
    distinguishes it from `commits`: it states something that must never be concluded, so there is no
    frame in which it is acceptable and nothing to subtract. The earlier version of this classifier
    subtracted a per-form baseline and mis-graded every leak as a defect in the *victim*, because the
    victim's own minimal cell already contained the form that leaked into it."""
    full = frame(cell)
    ctx, outcome, concluded = _state(cell, guarded, composed)
    if outcome is None:
        return Verdict(full, REFUSED, detail=ctx.refusal or "incompatible")
    leaks, silences = outcome

    if leaks:
        return Verdict(full, LEAK, violations=leaks, detail=leaks[0][1])
    if silences:
        return Verdict(full, INERT, violations=silences, detail=silences[0][1])

    non_default = [f for f in full if f not in DEFAULTS]
    if len(non_default) < 2:
        return Verdict(full, BASELINE)

    union: frozenset = frozenset()
    for f in non_default:
        _c, _v, s = baseline(f, guarded, composed)
        union |= (s or frozenset())
    gained = tuple(sorted(f"{w}.{k}={v}" for w, k, v in (concluded - union)))
    if not gained:
        return Verdict(full, INERT, detail="composite concluded nothing the parts did not")
    return Verdict(full, PASS, gained=gained)


# -- the space ------------------------------------------------------------------------------------

def cells(forms: tuple = SEED, content_depth: int = 2) -> list:
    """Every cell worth running: subsets of content up to `content_depth`, × each force × each level.

    ⚠ **This shape is itself a claim, and it is the one under test.** `P1` says a category is a *point*
    in CONTENT × FORCE × LEVEL — one value per axis. But content forms **stack**: *"not very dangerous"*
    bears negation and degree at once, and a point in a product has no room for that. Content is swept
    as a subset and force/level as single values precisely so the asymmetry shows up rather than being
    designed away."""
    content = [f for f in forms if f.axis == "content"]
    forces = [f for f in forms if f.axis == "force"] or [DEFAULTS[0]]
    levels = [f for f in forms if f.axis == "level"] or [DEFAULTS[1]]
    out: list = []
    for k in range(1, content_depth + 1):
        for combo in combinations(content, k):
            for force in forces:
                for level in levels:
                    out.append(combo + (force, level))
    return out


def sweep(forms: tuple = SEED, content_depth: int = 2, guarded: bool = False,
          composed: bool = False) -> list:
    return [probe(c, guarded, composed) for c in cells(forms, content_depth)]


# -- measuring the axes ---------------------------------------------------------------------------

def axis_audit(forms: tuple = SEED) -> dict:
    """Measured slots vs declared axes. A declared axis holding more than one slot has been **split by
    evidence**, which is a finding about the axis, not about the forms."""
    measured = slots(forms)
    per_declared: dict = {}
    for members in measured.values():
        for axis in {m.axis for m in members}:
            per_declared.setdefault(axis, []).append(tuple(sorted(m.name for m in members)))
    split = {a: s for a, s in per_declared.items() if len(s) > 1}
    return {"declared_axes": sorted(BY_AXIS),
            "measured_slots": {k: sorted(m.name for m in v) for k, v in measured.items()},
            "n_declared": len(BY_AXIS), "n_measured": len(measured),
            "axes_split_by_evidence": split}


# -- the numbers ----------------------------------------------------------------------------------

def geometry(verdicts: list) -> dict:
    """**Where** the failures sit, not just how many — is a leak a property of a pair, or of one form
    that leaks against everything, and do the leaks respect the axis boundaries."""
    leaks = [v for v in verdicts if v.outcome == LEAK]
    per_form: dict = {}
    per_axis_pair: dict = {}
    for v in leaks:
        for n, _m in v.violations:
            per_form[n] = per_form.get(n, 0) + 1
        axes = tuple(sorted({f.axis for f in v.cell}))
        per_axis_pair[axes] = per_axis_pair.get(axes, 0) + 1
    return {"leaks": len(leaks), "victim_form": per_form, "per_axis_combo": per_axis_pair}


def guard_density(forms: tuple = SEED, content_depth: int = 2) -> dict:
    """**The number this exercise exists to produce.**

    `forms_discourse` §4.2 claims a local per-form harmony check *buys* global closure, so checking ~50
    forms covers 1,225 pairs. That is a theorem about connectives composing by nesting; axes are not
    connectives, and the transplant is assumed rather than argued.

    This measures it: the fraction of cells that stop leaking only once an elimination is rewritten to
    **consult its neighbours**. Sparse ⇒ the local check nearly suffices. Dense ⇒ closure costs O(n²)
    authored guards, and *"the closed class is small"* stops being the reassurance it is used as.

    ⚠ `guard_made_inert` is the number that stops this being good news: a guard that ends a leak by
    making the composite **silent** has contained it, not composed it."""
    naive = {v.names: v for v in sweep(forms, content_depth, guarded=False)}
    guarded = {v.names: v for v in sweep(forms, content_depth, guarded=True)}
    live = [k for k, v in naive.items() if v.outcome != REFUSED]
    leaking = [k for k in live if naive[k].outcome == LEAK]
    fixed = [k for k in leaking if guarded[k].outcome != LEAK]
    return {"cells": len(live), "leaking": len(leaking),
            "fixed_by_guard": len(fixed),
            "still_leaking": [k for k in leaking if guarded[k].outcome == LEAK],
            "guard_made_inert": [k for k in fixed if guarded[k].outcome == INERT],
            "density": round(len(leaking) / len(live), 3) if live else 0.0}


def interactions(forms: tuple = SEED, guarded: bool = False) -> dict:
    """**The n² measurement, at the level that matters: PAIRS of forms, not cells.**

    `guard_density` counts cells, which double-counts one bad interaction across every frame it appears
    in. This asks the question `forms_discourse` §4.2 actually needs answered: of the pairs that can
    co-occur at all, how many fail to compose?"""
    pairs = [(a, b) for a, b in combinations(forms, 2)]
    live, leaking, inert = [], [], []
    for a, b in pairs:
        if a in DEFAULTS and b in DEFAULTS:
            continue
        v = probe((a, b), guarded)
        if v.outcome == REFUSED:
            continue
        live.append(v.names)
        if v.outcome == LEAK:
            leaking.append(v.names)
        elif v.outcome == INERT:
            inert.append(v.names)
    return {"pairs_that_combine": len(live), "leaking": leaking, "inert": inert,
            "leak_rate": round(len(leaking) / len(live), 3) if live else 0.0}


def axis_appeals(forms: tuple = SEED) -> dict:
    """How many forms cannot state their own commitment without naming another axis.

    If the axes were orthogonal this would be zero: a commitment on one axis would be statable in that
    axis's own terms. It is the specification-level form of `guard_density`."""
    appealing = {f.name: list(f.appeals) for f in forms if f.appeals}
    return {"forms": len(forms), "needing_other_axes": len(appealing), "detail": appealing}


def report(forms: tuple = SEED, content_depth: int = 2) -> str:
    lines: list = ["=== seed soundness ===",
                   f"  reference cell violations: naive={seed_is_sound(False)} "
                   f"guarded={seed_is_sound(True)}",
                   "\n=== axes, measured vs declared ==="]
    audit = axis_audit(forms)
    lines.append(f"  declared: {audit['n_declared']}  measured: {audit['n_measured']}")
    for k, v in audit["measured_slots"].items():
        lines.append(f"    slot {k:10} {v}")
    if audit["axes_split_by_evidence"]:
        lines.append(f"  ⚠ split by evidence: {audit['axes_split_by_evidence']}")

    for label, guarded, composed in (("NAIVE", False, False), ("GUARDED", True, False),
                                     ("GUARDED + PAIR ENTRY", True, True)):
        verdicts = sweep(forms, content_depth, guarded, composed)
        lines.append(f"\n=== {label} eliminations ({len(verdicts)} cells) ===")
        tally: dict = {}
        for v in verdicts:
            tally[v.outcome] = tally.get(v.outcome, 0) + 1
        lines.append("  " + "  ".join(f"{k}={n}" for k, n in sorted(tally.items())))
        for v in verdicts:
            if v.outcome in (LEAK, BROKEN, INERT):
                lines.append(f"  {v!r}")
        lines.append(f"  geometry: {geometry(verdicts)}")
    lines.append(f"\n=== guard density (cells) ===\n  {guard_density(forms, content_depth)}")
    lines.append(f"\n=== interactions (pairs) ===\n  naive:   {interactions(forms, False)}"
                 f"\n  guarded: {interactions(forms, True)}")
    lines.append(f"\n=== axis appeals ===\n  {axis_appeals(forms)}")
    return "\n".join(lines)


__all__ = ["Verdict", "probe", "cells", "sweep", "baseline", "excludes", "slots", "axis_audit",
           "geometry", "guard_density", "interactions", "axis_appeals", "report",
           "reference", "seed_is_sound",
           "PASS", "INERT", "REFUSED", "LEAK", "BROKEN", "BASELINE"]
