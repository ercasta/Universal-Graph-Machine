# The plural step — scope

**The gap, stated precisely.** A KB can already *build* a collection: a machine mints a node and links its
members, and `types` counts them. What nothing can do is **plan over one**. `docs/microfunctions/
not_supported.md` §G0 gets as far as *the engine has act and check and no find*; this is the other half —
the engine has **one action on one thing**, and no notion of *an action on each of many*.

`§5c` already recorded the shape from the other side: *backward chaining cannot express repetition;
repetition comes from the loop.* That is true and it is not a plan. A loop can *run* `ls | rm`; only a
plural step makes it **plannable** — proposable, rankable, imaginable, replayable, and honestly described.

---

## 1. What was measured, before designing on it

On the file KB, with `delete_one(f: file)` and an authored looping `delete_each(s: selection)`:

| | singular constraint (`readme.gone = true`) | universal constraint (`d is a tidied_dir`) |
|---|---|---|
| `relevance(delete_one)` | **4** | **1** |
| `relevance(delete_each)` | **1** | **1** |

Band 4 means *this call with these bindings writes exactly the open constraint*; band 1 means *no reason to
prefer it*. So there are **two independent blockers**, and conflating them would have produced the wrong
design.

⚠ **Getting the control right took two tries, and the first version proved nothing.** `relevance` binds
**mappings**, not raw nodes (`W.resolve(m) or W.image_of(m)`), so passing raw nodes silently collapsed
every score to band 1 — including the control. A measurement whose control does not light up is not a
measurement.

### ⭐⭐ Blocker 1 — a plural action is UNRANKABLE, not misread

```
establishes(delete_each) = [('attr','emptied','s',None), ('attr','gone', None, None)]   unknown=frozenset()
```

The per-member write **is** reported, and its subject role comes back `None` — §5k's *"somewhere we cannot
name at all"*. So `establishes` is **honest about a loop**, which corrects what §6e's note led me to
predict (*"a write in a loop body is reported once"* — true, and the missing half is that it is reported
on an unnameable subject). `driver.role_node` can never resolve `None` to a constraint's subject, so the
plural action scores 1 even against a constraint it would certainly close.

### ⭐⭐⭐ Blocker 2 — a universal constraint reintroduces the defect §5d was built to remove

Against `d is a tidied_dir`, **the singular actor also scores 1**. The universal is expressible as a type
constraint (`has no file each a ungone_file`, measured as sugar in `not_supported.md` §1) — but
`goal.unmet` can only say *that* it is false, never *which members* make it false. §5d's founding
argument, one level up:

> *A goal that can only answer yes/no forces blind search. One that names **which constraints are still
> false** lets the driver ask what could close them — means-ends instead of generate-and-test.*

A universal constraint is currently a yes/no. That is the same *predicate-is-expressible, planning-half-is-
missing* split §6h found for transitive reach, and it is **independent of plurality**: it must be fixed
even if no plural action is ever built.

---

## 2. ⭐⭐ The design decision the measurement settles: LIFT, do not author

Two ways to get a plural action:

| | **author** it (`fn delete_each(s)` with a loop) | **lift** the singular one (`delete_one ⊗ members(s)`) |
|---|---|---|
| effects | must be read out of a loop, and `_effects` walks **linearly and skips jumps** (§6e) | **derived** from `establishes(delete_one)`, whose role is nameable — measured at band 4 |
| exactness | subject role `None`, unrankable | exact, because nothing new is read |
| authoring cost | one plural function per action, forever | none |
| §6e | fights it | needs nothing from it |

**Lifting wins on measured evidence, not taste.** The authored loop's honest `None` is precisely what makes
it unrankable, and lifting never reads a loop at all. This also keeps `establishes`'s contract intact: it
stays a linear reader over a body, and plurality lives in the **proposal**, not in the body.

⚠ **So the plural step is a proposal SHAPE, not a new opcode and not a new kind of function.** That is the
same move §6d made for tasks — *adding a kind of work means writing its `step`, not touching `loop.py`* —
and it is why this is scoped as slices rather than as an engine rewrite.

---

## 3. Slices

### ✅ Slice A — witnesses for a universal — **BUILT, 2026-08-01** (184 checks, 0 FAILED)

`types.offenders` / `types.offending_type` / `goal.witnesses` / `workbench.original_of`, and a witness
branch in `driver.relevance`. **The acceptance number was hit: a singular action against
`b is a tidy_bin` goes from band 1 to band 4**, with no plural machinery at all — so *"clean all of them"*
is now plannable one member at a time, which is a complete capability on its own.

**⭐ `relevance` kept its four-argument signature, and that was the design constraint that shaped it.** A
`view=` parameter would have to be threaded through `pursue`'s `rank=` hook and `guideline.compose`, so
every author of a ranker would have to know about frames; a module-level "current view" would be the
hidden Python channel the loop arc exists to remove. Instead `_frame_of` **recovers the frame from the
bindings** — a frame points at its mappings, so the reverse index already answers it. Same move
`dispatch._thread_of` makes for threads: derive it, never accept it.

**⚠ Witnesses are derived and NOT stored, deliberately, and this is where "keep it in the graph" is
overruled by two precedents.** §5f refused to materialise expectations because the driver imagines
hundreds of frames and a node per step is a node per step; §5i is the other half — a stored witness list
is a claim about the *past*, and this is a question about *now*, which is the type-cache drift defect
exactly. What did move into the open is the *question*: "which members make this false" was buried inside
a local `sum()` in `types.fails` and is now a public reader anything can call.

**⚠ One implementation, so nothing can disagree.** `_matching` returns the targets that satisfy a
requirement; `fails` counts them and `offenders` names them (§5m's structural answer rather than a
guarded one).

**Four planted-bug probes, each biting a distinct key**, with the means-ends and Sussman checks as
controls throughout: naming members for a *satisfied* constraint; a witness branch that scores any write
to a witness (kills the discrimination between `clean_one` and `weigh`); no witness branch at all (the
state before this slice); and `offenders` inventing witnesses for the too-few case. ⚠ The fourth probe was
**itself vacuous at first** — `goal.py` binds `offenders` at import, so patching `types.offenders` never
reached it. *For every green, ask what would make it vacuous* applies to the probes too.

### Slice A — the reasoning (independent, done first)

A failing count-over-label constraint must name **the targets that violate it**. `types.fails` already
computes `n = sum(1 for x in g.targets(node, label) if _target_ok(...))` — the offending members are in
hand at exactly that moment and are then thrown away for a count.

* `goal.unmet` (or a companion reader) reports witnesses for a type constraint;
* `driver.relevance` matches an effect against a constraint's **witnesses** as well as its subject.

**Measured acceptance:** `relevance(delete_one)` against `d is a tidied_dir` goes **1 → 4**, with the
singular actor and no plural machinery at all. ⚠ Vacuity guard: a constraint that is already satisfied must
yield **no** witnesses, or the key measures the reader rather than the failure.

⭐ This alone makes *"delete all the files"* plannable **one file at a time**, which is a complete
capability and may be enough for a long while. Slices B–C buy atomicity and cost, not reach.

### Slice B — a distributive role

`establishes` role forms today are three (§5k): `c` (a parameter), `c.right` (navigated), `$it` (minted).
Add a fourth: **`each c.member`** — *this effect applies to every target of that path*. `role_node` gains a
plural resolution, and `relevance` scores band 4 when the constraint's subject **is among** them.

⚠ Nothing authors this role. It is **produced by lifting** and consumed by ranking, so it cannot drift from
a body — the same property that made `establishes` trustworthy in the first place.

### Slice C — imagining and replaying a plural step

* `workbench.step` over N members. ⚠ The open question is **one frame or N**: N frames keep every existing
  reader working and make partial progress representable; one frame makes the step atomic and gives
  `execution.recover` nothing to resume from. **N, on the evidence of §5a** — a diverged step must have a
  frame to resume at.
* `execution` replay is **already** one real action per tick (§6d), so a plural step becomes N ticks for
  free, and `loop.verb_of` keeps answering `act` **per element** — so *"stop after deleting three of
  seven"* works with nothing added. This is the loop arc paying rent.
* Expectations stay **qualitative** (§5f): *some members changed*, never *seven did*. A partial completion
  is a **deviation**, not a silent success.

### Slice D — the surface

`let x be most size of d.file` (denotation, previous discussion) and a plural constraint form. ⚠ Last, on
purpose: §5v's rule is that a surface must never say what the machinery cannot honour.

---

## 4. Risks, and what NOT to do

* ⚠⚠ **Do not expand the plural step at plan time into N singular steps.** It is tempting and it destroys
  the case that motivated the work: `ls | rm` must be plannable *without knowing the members yet*. An
  expanded plan is valid only for the collection as it was when planned.
* ⚠ **Do not teach `_effects` to read loops.** §6e measured the payoff of loop-awareness at zero for the
  existing library, and lifting removes the need entirely. If it is ever done, it is a separate decision
  with its own evidence.
* ⚠ **Do not let a plural step become atomic.** Irreversibility is per element; the whole point of §6d's
  `verb_of` is being able to decline the *next* act, not the batch.
* ⚠ Cost: `proposals` already tests every mapping against every parameter type. Lifting multiplies
  candidates by the collections in the frame. **Measure before and after** — §5m's lesson is that the
  named lever was aimed at the wrong thing.

## 5. What this does not need

No new opcode. No new node kind (a collection is an edge-bundle; `not_supported.md` §2b's item (1) would
merely *name* what already exists in four places). No change to `goal`'s vocabulary — the universal already
parses. No loop reading. That is the argument that this is a slice-shaped arc rather than a rewrite.
