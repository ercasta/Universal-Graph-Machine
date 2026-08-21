# What is old — an audit before the first release

Run on `e1da382`, 2026-08-20. Everything below was measured on the tree as it
stands, not recalled: check counts come from running the module, call counts from
grep over `ugm/`, and the one regression was bisected.

The question this answers is narrow: **which parts of the system were built for,
or are described in terms of, something the attention table has replaced.**

---

## 0. The axis

`Machine.run` is `attention.run`. The loop that ships is the table loop:

    a score per rule    ordered, tie broken by declaration order
    apply the first     highest-scoring rule whose antecedent matches
    then spend          run that rule's postconditions to move the table
    ...and stop         if one of them said so, the run is over

The option-set loop — recall, match everything, defeat, forgo, quiescence,
arbitrate, note doubt, apply — survives as `Machine.tick`, and it survives **on
purpose**: it is the second arm of `python -m ugm.attention`, the gate that says
the table loop concludes no less than the loop it replaced. It is not dead code.
It is a reference implementation kept for a comparison, and that is a different
disposition, with different consequences for a release.

So "old" here has three grades, and they want three different actions:

| grade | what it means | action |
|---|---|---|
| **A. superseded, still live** | two mechanisms doing one job; the design has already chosen | retire, one at a time, with a gate |
| **B. kept for the gate** | only reachable from a comparison | keep, and say so where it is, so it is not mistaken for the loop |
| **C. stale description** | the code moved, the sentence did not | rewrite |

Almost all of the problem is C.

---

## 1. Grade A — superseded mechanisms that are still live

### 1.1 `prefer` rows and the score buffs

The design's own endpoint (`docs/loop-migration.md`, last section;
`docs/HANDOFF.md` 20f) is that these retire in favour of attention. They are
still here:

| construct | where | count |
|---|---|---|
| `prefer(<R>, key, score)` | `selftest` 16, `learning` 6, `attention` 4, `workload` 3, `practice` 1, `bundle.ugm` 1 (`<relevant>`) | 31 |
| `boost` / `damp` | `text` (surface), `melee` 6, `selftest` 5, `attention` 5, `acting` 4, `teaching` 3 | 31 |
| `reset` | surface and loop only — no corpus uses it | 0 in corpora |
| `_priority` / `_rank` / `_in_play` | `machine.py`, read by `attention` and `arbitration` | 3 readers |

Two things the audit adds to what HANDOFF already records:

**The blast radius in the suite is small.** Only ten selftest functions touch any
of it: `recall_is_narrowable`, `the_better_move_wins`, `experience_is_offline`,
`doubt_is_a_tie`, `attention_is_about_a_node_not_a_rule`,
`what_the_situation_is_about`, `prohibitions_are_not_recalled`,
`a_teacher_cannot_supervise_what_it_cannot_see`, and the two attention lessons.
The expensive part of retirement is not the runner.

**The blast radius in the fixtures is not.** `ugm.learning`, `ugm.practice` and
`ugm.workload` are about `prefer` rows — they are 8/8, 8/8, and a workload
generator whose corpora are built out of `fact prefer(...)` lines. Retiring the
mechanism retires their subject. That decision was raised in `loop-migration.md`
("retire `ugm.learning` and `ugm.practice` with the `prefer`-row subsystem") and
then answered the other way — the table absorbs the claim. It is still open for
release: two notations for one thing is the thing a first release should not
ship.

**And `<relevant>`, the bundle's one `prefer` rule, is barely load-bearing.**
`python -m ugm.bundle` deletes each shipped rule and re-runs the suite: deleting
`<relevant>` costs **1 check**, against 40 for `<expand>`, 20 for `<give-up>`, 15
for `<ask-check>` and 8–10 for each of the three new call-stack rules. It is the
second-cheapest rule in the bundle.

**`reset` is already unused by every corpus.** It exists in the surface
(`text.py:440`), in `Rules`, and in the loop, and nothing outside the engine's
own tests spends it. It is the cheapest deletion on this list and the one with no
argument on the other side.

### 1.2 Attention has no `LIFE`

Recorded in HANDOFF 20f and repeated here because it is a release concern rather
than a design note: `attend(?x)` accumulates and only an explicit `unattend`
takes it back, and `unattend` was removed from the learned focus lesson. Measured
cost on the dungeon today: none. But nothing bounds the attended set, and the
automatic half is not built. Ship it with the bound named, or ship it with the
bound.

---

## 2. Grade B — kept for the gate, and mislabelled where it is

`Machine.tick`, `_choose`, `_materialise`, `_survives`, `_note_doubt`, `_forgo`'s
window, `_priority`/`_rank`/`_in_play`, and `ugm/arbitration.py` (the gate that
holds `_choose` against the list it replaced).

These are correct to keep. What is wrong is that nothing at the reader's eye
level says they are the old loop. Three concrete places:

**`Machine.run` carries a dead paragraph.** `ugm/machine.py:3496` still reads
*"THE MIGRATION TO THE TABLE LOOP IS STAGED, AND THIS IS THE SWITCH … Left on the
option-set loop until those land"*, immediately above the block that says the
table loop **is** the loop. The first paragraph was true for two days and is now
the opposite of the code under it. A first-time reader hits it before the
correction.

**`docs/code-walkthrough.md` §4, "One tick, end to end"**, walks `Machine.tick()`
as *the* tick, with `_choose`, `_in_play`/`_rank` and `_note_doubt` in the
listing. That is the loop that does not run.

**`ugm/arbitration.py`'s docstring** — *"Does the chooser agree with the list it
replaced?"* — is true of a chooser nothing calls. Both arms live inside the
retired loop, which `loop-migration.md` predicted ("deleting it retires the
gate") and which has not been reflected in the module.

---

## 3. Grade C — descriptions the code has moved out from under

### 3.1 `README.md`

- **The step is wrong.** *"The step is `read enough -> recall -> match -> defeat
  -> forgo -> quiescence -> arbitrate -> note doubt -> apply`"* is the option-set
  loop. The falsifiable consequence the README stakes the design on — *the
  interpreter's step should have no phases* — is still true, but the evidence
  offered for it is the wrong loop.
- **Check count stale twice**: `523 checks` at lines 14 and 126; actual **641**.
- **`python -m ugm.attention` is described as "the table loop against the shipped
  one".** The table loop is the shipped one; the gate drives `Machine.tick`
  directly for its other arm.
- **`python -m ugm.arbitration` is listed among the floor gates** with no note
  that both of its arms are retired machinery.
- The attention row in *What is taught* is correct and current — the one place in
  the README that already describes the loop that runs.

### 3.2 `docs/code-walkthrough.md`

Snapshot dated 2026-08-18, and stale in every number:

| | doc says | actual |
|---|---|---|
| `selftest` | 523/0, 7466 lines | **641/0**, 8962 |
| `machine` | 5604 | 6232 |
| `rules` | 1992 | 2170 |
| `graph` | 215 | **874** |
| `chain` | 597 | 665 |
| `text` | 1265 | 1394 |
| `gate` | 259 | 322 |

Plus §4 above, and a module roster in §2 that predates `hanoi`, `melee`, `quest`,
`intake`, `walkers`, `agreement` and `necessity` having their current roles.

### 3.3 `docs/rules-design.md` — the largest single gap

5,799 lines, the only design document, and **it does not mention the table
loop.** §19 *Recall* still presents the design as three selection steps with
opposite requirements — recall / match / arbitrate — and argues at length for
where experience belongs *in recall*. The engine now spends attention on a table
and takes the first match. The two documents that do describe the current loop —
`attention.py`'s docstring and `docs/loop-migration.md` — are a module paper and
a work list, and neither is where a reader is sent.

This is the one item on the list that cannot be fixed by editing numbers.

### 3.4 The book — five chapters describe the loop that lost

Every chapter predates the flip (`7776439`, 08-19). Most are unaffected: the
substrate, entries, signs, moments, spans, shapes, channels, tools, time, several
agents and several experts are all about the representation, and the
representation did not move. What did move:

| chapter | what it now says wrongly |
|---|---|
| `floor/32-zero-phases.md` | *"The step is: read `enough` → recall → match → defeat → forgo → quiescence → arbitrate → note doubt → apply"* |
| `watching/27-recall.md` | recall / match / arbitrate as the three steps |
| `watching/28-the-table.md` | frames the table as *"the biggest open argument"* and *"the other loop"*, against *"what the shipped loop does"*. Inverted. |
| `watching/26-stopping.md` | *"stopping → recall → learning"* as the build order, in the old loop's terms |
| `wanting/13-blocked.md` | `blocked` argued from an option set the loop no longer materialises |
| `watching/29-learning.md` | the `prefer`-row half, which is §1.1 above |

Chapter 28 is the tell: it was written to *argue for* the table, and it is now the
chapter describing what shipped. Rewriting it is not a correction, it is a change
of genre.

---

## 4. What running everything found

`python -m ugm.selftest` → **641 checks, 0 failing**. Then every one of the 45
modules was run as `python -m ugm.<name>`. Forty exit 0. Four do not, and one
could not be run inside five minutes:

| module | result |
|---|---|
| `attention` | **1 failing** — see §4.1 |
| `practice` | **21 checks, 1 failing** — see §4.1 |
| `vocabulary` | 18 checks, 2 failing — known, see §4.3 |
| `quiescence` | known red, see §4.3 — **165 candidates, 0 disagreeing**, so the gate agrees and exits 1 on the blind rule alone. Over 300s |
| `necessity` | **does not finish in 25 minutes.** See §4.2 |
| `bundle` | **green** — 22 bundled rules, 22 exercised, 9 answerers, 0 anomalies — but it takes over five minutes |

Against HANDOFF 20f's *"modules all green; vocabulary 18/2 unchanged"*, that is
two reds unaccounted for.

### 4.1 Two gates have been red since 2026-08-19, and HANDOFF says they are green

    ugm.attention   FAIL  1 conclusion(s) lost that are not an accepted loss:
                          ['defeated(<hero-holds>, <hero-acts>)']

    ugm.practice    FAIL  forgoing works inside a supposition, so a rehearsal is
                          a CHOICE -- one route taken, the other passed up and named

Both bisected to the **same commit**, independently: green at `f3514c4` (hanoi),
red at `049ab17` (callstack) and at every commit since, including HEAD.
`049ab17` added three rules to `ugm/rules/bundle.ugm` — `<call-spawn>`,
`<call-advance>`, `<call-return>`.

That is *the bundle is not free*, exactly as HANDOFF 20e states it: a bundled
rule shifts the declaration rank of every rule in every corpus, and rank is the
tie-break at the floor. 20e records the same commit costing `ugm.walkers` its
central demonstration, and it was the second time that session. It does not
record these two, and both 20e and 20f report *"modules all 29 green"* while both
were already exiting 1.

The finding worth keeping is not either lost record. It is that the one gate
whose job is to catch the table loop concluding **less** than the loop it
replaced was failing for a day and was reported as passing — and that the cost of
a bundle rule was already a known, twice-recorded hazard when it was paid a third
time. Before release, the module sweep should be something that **runs**, not
something that is asserted.

### 4.2 The two kill-probe gates have outgrown the suite

Both `bundle` and `necessity` re-run the **whole suite** once per thing they
suppress, so their cost is the product of two numbers the project keeps adding
to. The suite has gone 523 → 641 checks.

| gate | suppresses | runs of the suite | wall clock |
|---|---|---|---|
| `bundle` | each bundled rule | 22 | 162s on 08-18, **over 300s** now |
| `necessity` | each reserved name ever deposited | **91** (of 118 reserved, 27 out of scope) | **over 25 minutes** — did not finish under a 1500s timeout |

`quiescence` is also now over 300s.

Neither is a defect. But these two are the gates that enforce this repository's
own standing discipline — *a rule no fixture can kill is a rule the fixture is
not testing* — and they are the two nobody can afford to run on a change. §4.1 is
what that costs: three bundled rules landed, two gates went red, and the session
that landed them reported all modules green.

For a release, the sweep needs a shape that runs: a fast tier that is cheap
enough to be a habit, and the two exhaustive probes on a schedule rather than in
the loop.

### 4.3 Known and pre-existing

- `python -m ugm.quiescence` exits 1 on **165 candidates, 0 disagreeing** — the
  gate itself agrees; what fails is its own kill-probe. Its `<silent>` rule is
  blind: suppressing it changes nothing, so the fixture never exercises it. Fails
  identically on both loops and predates all of this. (`code-walkthrough.md`
  records 145 candidates; it is 165 now.)
- `python -m ugm.vocabulary` 18/2. `holds_at` and `time` are in
  `Machine.reserved` and unclassified in `ROLES`, so the partition is not total.
  A stale classification, and the census is what catches it.

### 4.4 Hygiene

- `Python/` — an empty untracked directory at the repository root.
- `docs/overview.md` — untracked, four lines, and outside the doc set the README
  points at.
- `python -m ugm.chain`, `.channels`, `.gate` and `.graph` each print a
  `RuntimeWarning: found in sys.modules after import of package` before their
  output. Cosmetic, and among the first things a new reader runs.
- The `§` numbers in code comments are stale against `rules-design.md`'s current
  numbering, which `code-walkthrough.md` documents rather than fixes.

---

## 5. Suggested order

The order is forced in one place and free everywhere else.

**Forced**: HANDOFF 20f's dependency. Attention cannot do `prefer`'s job yet —
three attempts, 10/13/13 checks failing, and the counted variant cost the focus
arm 44 domain conclusions against 3. So attention-based scoring has to work
(length normalisation, inverse frequency) *before* any of §1.1 is retired.

Which means the documentation is not blocked on the code, and it is the larger
half of the audit. A reasonable release order:

1. **Repair the two gates** (§4.1) and make the module sweep a command, in two
   tiers (§4.2) — a fast one that is cheap enough to be a habit, and `bundle` and
   `necessity` on a schedule. Everything after this should be measured rather
   than believed.
2. **Delete `reset`** (§1.1) — unused by every corpus, no argument against.
3. **Numbers and labels**: the README's step and counts, `code-walkthrough` §4
   and §10, `arbitration.py`'s docstring, the dead paragraph in `Machine.run`,
   the four `RuntimeWarning`s, `Python/`.
4. **`rules-design.md` §19** — the real work, and the thing a first release is
   judged on.
5. **The five book chapters**, which mostly follow from 4.
6. **Then** attention-based scoring, and `prefer` and the buffs after it.

Steps 1–3 are hours. Step 4 is the release.

---

# Second sweep — 2026-08-21, on the tree after the table-loop landing

Run on `982a086` plus this commit's cleanups. The first audit above was taken
one landing earlier; between the two, most of its Grade A and B items were
**done**: `ugm.arbitration`, `ugm.walkers`, `ugm.modality`, `ugm.workload` and
`ugm.melee` are deleted; `boost`/`damp`/`reset` are gone from the surface and
the parser says so when one is written; `prefer` rows are inert (a row and its
denial give the same move, and the suite checks that); `<relevant>` left the
bundle; `Machine.run`'s "staged migration" paragraph now says the table loop IS
the loop. `vocabulary` runs 18/0 (was 18/2).

## Measured on this tree

- **Module level is clean.** Every module is imported by another or is a door
  (`if __name__`), and `./tools_sweep.sh` runs 30 doors: **29 green, 1 red** —
  `gates.quiescence` at 5/6, the pre-existing blind-rule coverage complaint
  HANDOFF records (167 candidates, 0 disagreeing: the gate agrees, one of its
  own six rules is exercised by no fixture).
- **All nine corpora are loaded by something** (`quest-*` through the probe's
  f-string, which a filename grep misses).
- **Dead code found: one method** (`Machine._frame`, shadowed by the
  `_attention` property) — removed. No dead public def anywhere else.
- **34 unused imports** across 22 files — removed.
- **The wheel was broken**: `packages = ["ugm"]` shipped no subpackage, so an
  installed wheel imported nothing. Fixed by listing `ugm.core`, `ugm.gates`,
  `ugm.learning`, `ugm.probes`.
- **Stale citations of deleted modules in live code**, fixed in place:
  `chain.rests_on`'s docstring credited `ugm.support` (the selftest's
  structural-mirror checks hold that agreement now), `probes/__init__` cited
  `ugm.modality` in the present tense, and one selftest docstring still called
  `prefer` "the shipped way".
- **README check counts** said 646 and 513 in one file; both now read the
  number the runner prints.
- **`docs/code-walkthrough.md`** got the tombstone header the deleted-module
  docs use: still a useful map, wrong in every number, and §4 walks the
  retired loop.

## Deliberate keeps, verified as deliberate

`docs/design/hindsight.md` and `docs/design/walkers.md` are tombstones for
deleted modules and say so in their first line; `Machine.tick` is one bounded
step of the table loop (the option-set loop AND the comparison that held the
two side by side are deleted -- `python -m ugm.core.attention` now runs worked
examples, not a comparison); `ugm.workload` mentions in `hanoi`/`artefact` are
explicit "the retired..." records. None of these is unused code; all of them are the record.

## Still stale, and not a sweep's to fix

Prose that presents the retired loop as the shipped one, unchanged since the
first audit flagged it:

- `README.md` "The step is `read enough -> recall -> match -> ...`" — the
  option-set listing, offered as the evidence for zero phases.
- `docs/rules-design.md` still does not mention the table loop (§19 argues
  recall), and its `ugm.harmony` collision note (~line 660) names a deleted
  module.
- The book: `floor/32-zero-phases.md` lists the old step;
  `watching/28-the-table.md` still frames the table as "the other loop";
  26 and 27 are in the old loop's terms. The book was last touched 08-18,
  one day before the flip.
- `docs/design/machine.md` (and `rules.md`, `maze.md`, `hanoi.md`,
  `atlas.md`, `vocabulary.md`, `chain.md`) cite deleted instruments in the
  present tense where they quote old measurements.
- `docs/HANDOFF.md` is a dated session record whose numbers are one landing
  old; it reads as such.

These are rewrites of the argument, not deletions of code — the first audit's
§3.3 verdict stands: the one item that cannot be fixed by editing numbers.
