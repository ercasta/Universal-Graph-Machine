# Implementation audit — a judgement read

**A work list, not a page.** Sibling to [doc-audit.md](doc-audit.md); delete both once acted on.
`ugm/` as of 2026-08-07, 45 modules, 32,805 lines including `selftest.py`.

Deliberately **not** what the instruments already derive. `reach`, `horizon`, `labels`, `boundary`,
`leak` and `bench` cover reachability, closed-class cost, traffic and the copy boundary better than a
read can, and re-deriving them by eye would be the hand-maintained-inventory mistake this codebase
refuses everywhere else. What follows is what no instrument is pointed at: **one fact carried in two
shapes, islands, decisions embodied in Python that could have been arguments, and claims a docstring
makes that nothing enforces.**

⭐ **State first: this is a clean codebase.** 6 of 710 functions are unreferenced. Every closed set is
a *declared* module-level constant rather than an inline literal, which is `concepts.md`'s *"a closed
class earns its place by being declared"* actually honoured across ~20 modules. Docstrings carry
their own drift notes — `fact.py`'s header says *"this module has not caught up"* and names the two
seams. Findings below are specific, not systemic.

---

## 1. ⚠⚠⚠ A dormant twin is rotting, and its docstring claims it is not

`ugm/workbench.py:843` — *"`_python_predicted_changes` is kept below as the reference this is checked
against."*

**Nothing references it.** Not `selftest.py`, not `bench.py`, not `leak.py`, not any `.mf`. It is one
of exactly six unreferenced functions in the package.

The other three reference twins are genuinely compared:

| twin | compared by |
|---|---|
| `workbench._python_step` | `selftest.py:7303`, `bench.py:92` |
| `execution._python_step` | `selftest.py:2273`, `bench.py:169` |
| `workbench._python_open_workbench` | `selftest.py:6245, 6262` |
| `goal._python_holds` | `selftest.py:8405, 8421, 12055` |
| **`workbench._python_predicted_changes`** | ❌ **nothing** |

⚠⚠⚠ And the codebase **knows the rule** — `selftest.py:12275` quotes it: *"…and **a dormant twin
rots** — so the answer is the one used for `_python_step`: not a deletion."* Applied four times,
missed once.

⭐ **Why it survived is the generalisable part.** *Is there a reference twin?* is answerable by
reading, and everybody did. *Is the twin actually compared?* is only answerable by deriving, and
nothing derives it. The pattern has a shape — a Python original kept beside a surface replacement —
so **it can be a check**: for every `_python_*` in the package, assert something calls it. That is
four lines and it closes the class rather than this instance.

**Fix:** add the comparison check (preferred — `predicted_changes` is the one surface function that
was *"never on the blocker list, and it was one"*), or delete the twin. Either way the docstring at
`:843` must stop asserting a check that does not exist.

---

## 2. ⚠⚠ A retirement condition fired and the code did not retire

`ugm/workbench.py:746`, on the `deviates` wrapper:

> *"That translation is the wrapper's whole job and it is **temporary — when `execution.step` moves
> to the surface it will read the node directly and this dies with it**."*

`execution.step` **has** moved (`rules/execute.mf`, which invokes `deviates` directly at `:527`).
The wrapper is still here, because a caller the note did not anticipate still wants the rendered
dict: `execution.py:588`, inside `matching_alternative`.

⭐ **The generalisable shape:** a conditional deletion note names *one* caller's future and is
invalidated by a *second* caller — the island rule (*an island is created by the SECOND caller*)
applied to deletions rather than to definitions. A note of the form *"this dies when X happens"*
should name **every** caller, or say *"when nothing but X calls it"*.

Three other `for now` / `temporary` notes exist and their conditions have **not** fired, so they are
correct as written: `asm.py:10` (assembly rather than a CNL), `selection.py:24` (greedy selection),
`types.py:745` (`instances` as a native, *"for a stated reason, not because it is primitive"*).

**Fix:** either move `matching_alternative` to `deviation_violations` + the node form and delete the
wrapper, or amend the note to say what actually holds it open.

---

## 3. ⚠⚠ Two answers to *what did this action produce*, differing by the bookkeeping

| | window | excludes |
|---|---|---|
| `dispatch.py:158–164` | `existing = set(g.nodes)` taken **after** the veto, `produced` computed **immediately after the tool returns** | the moment and sightings minted below it — *"computed here and not a moment later, so nothing minted by the bookkeeping below can be mistaken for something the world handed us"* |
| `isa.py:642–645` | `before = set(g.nodes)` around the **whole** `_service(...)` call | nothing — so `activation.record_mint` records the moment node and the sighting nodes as things this call minted |

Each diff is individually argued for, and both arguments are good — `isa.py`'s comment correctly
says the dispatch boundary is *"the one place a diff is still the honest way to learn what
appeared."* The problem is that they are **two computations of one window with nothing relating
them**, and they disagree by exactly the set `dispatch` went out of its way to exclude.

⚠ This matters because `activation.minted`'s own docstring says the result is order-sensitive and
load-bearing: *"`execution._bind_minted` pairs imagined nodes with real ones by kind and order.
Changing the order here would silently change which imagined node binds to which real one."*

⚠⚠ And `activation.py:184` records **the previous instance of this exact pattern** causing a live
defect — a focus, its heads, an activation and its registers landing inside a `set(g.nodes)` window
and one of them being *"duly bound as an imagined result and type-checked as a `report`"*. The fix
then was *"a record, not a filter over kinds"*. `dispatch` is the one place the record does not
reach, and the diff came back.

**Not a demonstrated bug** — dispatch is refused while imagining, so the imagined/real pairing does
not currently straddle it. It is a shape with a recorded history. **Fix:** have `dispatch.service`
hand its `produced` tuple to the activation directly, so there is one answer and `isa.py`'s diff
disappears rather than being narrowed.

---

## 4. ⭐⭐⭐ `driver.relevance` **is** the recall/System-1 of [rules.md](rules.md) §9, hardcoded

The docstring says it outright (`driver.py:689`): *"This is also **System 1's first real job**, and
notably it needs none of the neighbourhood/radius question resolved."*

What it actually is: a **four-band ladder in Python**, returning an `int`.

| | `rules.md` §9 says | `driver.relevance` + `selection.candidates` do |
|---|---|---|
| complete? | ❌ never, by design | ✅ **complete** — `selection.candidates` iterates every name in `fn.names(g)` and calls `fn.load` per name |
| learned or authored? | **learned** | **neither** — the four bands are compiled in |
| returns | a set **plus a state** (*nothing applies* vs *nothing came to mind*) | an `int`; the two silences are indistinguishable |
| keyed by | situation **and active goal** | goal only (`unmet`), which is the half it gets right |

⭐ This is **the most direct contact point between the new design and the existing engine**, and
neither `rules.md` nor `HANDOFF.md` mentions it. `relevance` already got two things right that the
design argues for — it *ranks and never filters*, and it is indexed by the goal rather than the world
(which is also what the guard-address probe measured) — so the design is not starting from nothing.
What is missing is exactly the two things §9 names: **incompleteness with a reported state**, and
**learning from the residue that is already being deposited** (`application.compile_episode`,
`generalise`).

⚠ And note the cost shape: recall being complete is not currently a bottleneck because the library
is small. `selection.candidates` is O(library) with a `fn.load` per name, so it is the function that
converts *"a narrow domain"* from a scope statement into a performance assumption.

**Fix:** none yet — this is a design note that belongs in `rules.md` §9 and in the handoff, so the
next session starts from `relevance` rather than from a blank page.

---

## 5. ⭐⭐ `precedence.py` already **is** the arbitrator [rules.md](rules.md) §8 specifies

Worth recording so it is not re-derived. §8 asks for a bottom-most selector that is *total,
table-driven, always answers, and never searches*. `precedence.py` has all four, plus two properties
the design note did not think to ask for:

* **A closed set that ships, with an escape.** `add_stage` refuses an unknown stage name with
  *"For anything else, name a function (`run <fn>`) rather than adding a word here"* — the closed
  class is the set that *ships*, never the set that is *possible*.
* **Totality enforced where it is written.** `seal_rule` refuses a rule whose last stage is not in
  `TOTAL`, *"at authoring time, never at run time… an incomplete order is invisible until the one
  pair it cannot separate turns up."* That is precisely §8's stratification condition, already built.
* **A named failure mode:** *"a stage consulted twice cannot change its mind."*

**Fix:** cite it from `rules.md` §8 instead of describing the requirement abstractly.

---

## 6. ⚠⚠ The phase machine is 12 inline transitions, and the plan says they are not owed

`_PHASES` (`driver.py:2023`) is a Python dict of Python callables — known, and listed in
`HANDOFF.md` as the last unwritten piece. What the plan understates is the *transitions*: there are
**12 `g.put(p, phase=…)` sites** (`:1831, 1836, 1843, 1863, 1870, 1873, 1891, 1984, 1993, 2005,
2011, 2019`), each behind an inline condition. They are not a table and cannot be enumerated.

⚠ `HANDOFF.md:762` splits P4 as *"only A1 / A4 / C1 are owed (the **decisions**, as data); the phase
machine itself can stay Python indefinitely."* But the decisions **are** the transitions, and while
they are inline conditions, *"why are you planning?"* has no answer that does not involve reading
Python — which is exactly the third payoff `self-and-processes.md` §8 claims for trigger rules
(*"triggering becomes explicable"*). The current split concedes the thing the design says pays.

**Fix:** re-read the P4 split against `self-and-processes.md` §8 before building it. Either the
transitions are owed, or §8's third payoff should be withdrawn.

---

## 7. Unreferenced functions — 6 of 710

| function | verdict |
|---|---|
| `workbench._python_predicted_changes:849` | see §1 — the one that matters |
| `fact.raw_touches:115` | in the module the live arc is built behind; check against `facts-as-nodes.md` before deleting |
| `precedence.describe_ranking:362` | a reader for a module whose readers are otherwise exercised |
| `discourse.last_said:175`, `discourse.withdrawn_at:273` | two readers in one module |
| `construction.denoted:95` | in the newest module; likely written ahead of its consumer |

⚠ Per this project's own standard, *machinery built for no consumer is the trade this codebase
declines* (`fact.py`, on why there is no `retract` yet). Three of these are readers written before
anything asked — which is the same trade, taken the other way, five times.

**Fix:** delete, or note the intended consumer. The ratio (6/710) says this is housekeeping, not rot.

---

## What is good and should not be "tidied"

* **Closed sets are declared, everywhere.** `KINDS`, `VERBS`, `STAGES`, `FORCES`, `STRENGTHS`,
  `ROLES`, `SELECTORS`, `MET_BY`, `STANCES` — ~20 modules, all module-level, all reachable. The
  failure `concepts.md` warns about (*"a closed class that is neither named nor reachable, existing
  only as a Python function nobody can see"*) does not occur.
* **Docstrings carry their own drift.** `fact.py` flags that it still stores the predicate in `label`
  and numbers positions from 1 where the design numbers from 0, and names what has to move with the
  callers. That is better hygiene than `docs/concepts.md` had.
* **The reference-twin discipline works** — three of four twins are measured, and the exception in §1
  is a missing check rather than a missing principle.
* **`types.gather_instances`** declares itself a native *"for now, and for a stated reason, not
  because it is primitive"*, and states the exact vocabulary member that would retire it. That is the
  horizon rule applied to a live decision rather than to a retrospective.

---

## Order

| # | action | size |
|---|---|---|
| 1 | Check every `_python_*` twin is referenced; add the missing comparison or delete it (§1) | small |
| 2 | Give `dispatch.service` its `produced` set to the activation, delete `isa.py`'s diff (§3) | small |
| 3 | Close or re-word the `deviates` wrapper's retirement note (§2) | small |
| 4 | Resolve the 6 unreferenced functions (§7) | small |
| 5 | Record `relevance` + `selection.candidates` in `rules.md` §9, and `precedence` in §8 (§4, §5) | small, high value |
| 6 | Re-read the P4 split against `self-and-processes.md` §8 before building it (§6) | design, not code |
