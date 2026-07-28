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

from .forms import (BY_AXIS, CANDIDATES, DEFAULTS, SEED, Form, excludes, frame, run, signal_audit,
                    signature, slots)

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


_CACHE: dict = {}


def _state(forms: tuple, guarded: bool, composed: bool = False,
           inventory: tuple = SEED) -> tuple:
    """Run a framed cell: `(ctx, violations, concluded)`. `violations is None` marks a refusal.

    ⚠ `inventory` is not decoration. `frame()` fills slots, and which slot a form occupies is measured
    **against an inventory** — so framing a candidate form against the seed puts it in a slot of its
    own and bolts on a competing default, and the cell refuses for no reason but the caller's default
    argument. Every audit below threads it."""
    key = (tuple(f.name for f in forms), guarded, composed,
           tuple(f.name for f in inventory))
    if key in _CACHE:
        return _CACHE[key]

    cell = frame(forms, inventory)
    ctx, view, _net = run(cell, guarded, composed)
    if view is None:
        return _CACHE.setdefault(key, (ctx, None, None))
    leaks = tuple((f.name, msg) for f in cell
                  if (msg := f.forbids(ctx, view)) is not None)
    silences = tuple((f.name, msg) for f in cell
                     if (msg := f.commits(ctx, view)) is not None)
    # A run is a pure function of (cell, guarded, composed) — the engine's own invariant 15 — so this
    # caches a result rather than a coincidence. It holds only within a process.
    return _CACHE.setdefault(key, (ctx, (leaks, silences), signature(ctx, view)))


def baseline(f: Form, guarded: bool, composed: bool = False,
             inventory: tuple = SEED) -> tuple:
    """A form **on its own terms**: itself, in the default frame.

    Not the bare form — `frame()` fixes the axes it does not fill, because an unmarked claim is an
    assertion about the world rather than a claim with holes in it."""
    return _state((f,), guarded, composed, inventory)


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


def probe(cell: tuple, guarded: bool = False, composed: bool = False,
          inventory: tuple = SEED) -> Verdict:
    """Classify one cell.

    ⚠ **A `forbids` violation is a LEAK unconditionally**, with no baseline comparison. That is what
    distinguishes it from `commits`: it states something that must never be concluded, so there is no
    frame in which it is acceptable and nothing to subtract. The earlier version of this classifier
    subtracted a per-form baseline and mis-graded every leak as a defect in the *victim*, because the
    victim's own minimal cell already contained the form that leaked into it."""
    full = frame(cell, inventory)
    ctx, outcome, concluded = _state(cell, guarded, composed, inventory)
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
        _c, _v, s = baseline(f, guarded, composed, inventory)
        union |= (s or frozenset())
    gained = tuple(sorted(f"{w}.{k}={v}" for w, k, v in (concluded - union)))
    if not gained:
        return Verdict(full, INERT, detail="composite concluded nothing the parts did not")
    return Verdict(full, PASS, gained=gained)


# -- the space ------------------------------------------------------------------------------------

def cells(forms: tuple = SEED, depth: int = 2) -> list:
    """Every cell worth running: one form from each **defaulted** slot, times a subset of the optional
    slots up to `depth` — except a defaulted slot is skipped for a specific combination if one of the
    optional forms chosen for it declares that default excluded (`Form.excludes_defaults`), so a
    relational form (`unmet`) doesn't get handed an unrelated default polarity to independently
    decorate the same node with.

    ⚠ **Built over measured slots, not declared axes**, for the same reason `frame()` is. `P1` says a
    category is a *point* in CONTENT × FORCE × LEVEL — one value per axis — but forms within `content`
    stack: *"not very dangerous"* bears polarity and strength at once, and a point in a product has no
    room for that. Once slots are measured the shape is regular again: **defaulted slots always carry a
    value, optional slots stack.** That is the corrected form of P1, and it is what the sieve enumerates.

    ⭐ **Found 2026-07-28: the un-excluded version manufactures `unmet ∘ positive` for every cell that
    mentions `unmet` at all** — the base was built once, globally, before `unmet` had any say in which
    defaults apply to it. Computing the base per-`picks` fixes that, and is exactly the same correction
    `frame()` needed for the same reason (`closed_class_inventory.md` §5, `composition_grammar.md`)."""
    groups = slots(forms)
    default_names = {d.name for d in DEFAULTS}
    defaulted = [v for v in groups.values() if any(m.name in default_names for m in v)]
    optional = [v for v in groups.values() if not any(m.name in default_names for m in v)]

    def base_for(picks: tuple) -> list:
        excluded = {d.name for f in picks for d in f.excludes_defaults}
        active = [group for group in defaulted if not any(m.name in excluded for m in group)]
        b: list = [()]
        for group in active:
            b = [c + (f,) for c in b for f in group]
        return b

    out: list = []
    for k in range(0, depth + 1):
        for chosen in combinations(optional, k):
            picks: list = [()]
            for group in chosen:
                picks = [c + (f,) for c in picks for f in group]
            for p in picks:
                out.extend(b + p for b in base_for(p))
    return out


def sweep(forms: tuple = SEED, content_depth: int = 2, guarded: bool = False,
          composed: bool = False) -> list:
    return [probe(c, guarded, composed, forms) for c in cells(forms, content_depth)]


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

def factors(f: Form, inventory: tuple = SEED, depth: int = 2) -> list:
    """**The other sieve — primality.** Which combinations of *other* forms produce exactly this form's
    state change?

    `forms_cnl` §3's underlying test is *"can it be paraphrased without changing what the system
    believes?"*, and `P3` says a form **is** what it does to the information state. Put together they are
    mechanical: a form is **composite** (baroque, desugar it) iff some combination of held forms reaches
    the identical state, and **prime** (fundamental, admit it) iff none does.

    ⚠ Identity of state change is stricter than paraphrase. This can only report exact factorizations,
    so it finds the clear cases and is silent about near-misses — which is the right direction to fail
    (`P9`: too closed is recoverable)."""
    _c, _v, target = baseline(f, guarded=False, inventory=inventory)
    if target is None:
        return []
    others = [g for g in inventory if g is not f]
    mine = frozenset(frame((f,), inventory))
    found: list = []
    for k in range(1, depth + 1):
        for combo in combinations(others, k):
            # ⚠ A combo that FRAMES to the same cell is the identity, not a factorization. Every
            # default form frames to the reference cell, so without this every default "factors" into
            # every other one — which is what the first run of this reported.
            if frozenset(frame(combo, inventory)) == mine:
                continue
            _c2, viol, got = _state(combo, guarded=False, inventory=inventory)
            if viol is not None and got == target:
                found.append(tuple(g.name for g in combo))
    return found


def factorization_audit(inventory: tuple = SEED) -> dict:
    """Every form that turns out to be a combination of others."""
    # Defaults are excluded: a default form's baseline IS the reference cell, so it has no isolable
    # contribution to factor. That is a limit of the method, not a verdict about those forms.
    testable = [f for f in inventory if f not in DEFAULTS]
    composite = {f.name: fs for f in testable if (fs := factors(f, inventory))}
    return {"forms": len(inventory), "testable": len(testable), "composite": composite,
            "prime": sorted(f.name for f in testable if f.name not in composite)}


def impure_slots(inventory: tuple = SEED) -> dict:
    """Slots whose members were filed on **different declared axes**.

    A slot is one dimension by measurement. If its members carry different `axis` values, the axis
    assignment and the behaviour disagree, and the behaviour is the evidence: forms that exclude each
    other or write the same field are competing values of one thing, whatever they were filed as."""
    out: dict = {}
    for key, members in slots(inventory).items():
        axes = {m.axis for m in members}
        if len(axes) > 1:
            out[key] = {"members": sorted(m.name for m in members), "declared_axes": sorted(axes)}
    misfiled = sorted({m.name for v in out.values() for m in ()} |
                      {n for v in out.values() for n in v["members"]})
    return {"impure": out, "n_impure": len(out), "forms_involved": misfiled}


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
        v = probe((a, b), guarded, inventory=forms)
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
           "reference", "seed_is_sound", "factors", "factorization_audit", "impure_slots",
           "PASS", "INERT", "REFUSED", "LEAK", "BROKEN", "BASELINE"]
