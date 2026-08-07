# Documentation audit — what must be revised, where, and why

**A work list, not a page.** Delete it once it has been acted on; it describes the doc base as of
2026-08-07 (`4bf265e` + `docs/rules.md`), 31 files, 10,985 lines.

The doc base is the residue of several engine generations, and it shows in a specific way: **the
prose that describes what runs was written for a substrate the live arc is replacing, and neither
side says so.** Nothing is decayed at the level of individual arguments — the reasoning trail is in
good condition and is the directory's real asset. What has rotted is the **frame**: which page is
current, which is superseded, which is a sketch, and which of four incompatible notations for *a
rule* a reader is supposed to believe.

Findings are ordered by what a reader gets wrong if nothing is done.

---

## A. ⚠⚠⚠ Two incompatible models of the substrate are both presented as current

This is the finding that matters. `concepts.md` is README's recommended **second read** and has the
most inbound links of any page (8). It argues, at length and well, for the substrate the live arc
exists to replace — and it does not know that.

| where | says | contradicted by |
|---|---|---|
| `concepts.md:23–28` | *"Named edges rather than role nodes… an earlier design made edges nameless and roles into nodes… charged a node plus two edges for **every** connection. **Reification stays available and stops being mandatory.**"* | `facts-as-nodes.md` — every relation becomes a node; reification is exactly what becomes mandatory. `HANDOFF.md:12` calls this THE LIVE ARC |
| `concepts.md:34–39` | **edge properties** and edge identity, with the argument that this is what lets a moment date a connection | `HANDOFF.md:70–74` — *"edge properties go with them, since they exist only because an edge could not carry a fact"* |
| `concepts.md` §*Absence*, `overview.md:50` | a type is a schema over *structure and attributes*; `g.attr` returns `None` | `HANDOFF.md:70` — *"if attributes are nodes, **the substrate stops having attributes at all**"* |
| `overview.md:48–56` | *"Precondition and effect collapse into parameter type and return type"* — mutation needs no representation | `rules.md` §2 — a rule is `causes(moment, moment)` with a **signed delta**; `facts-as-nodes.md` §*Frames* |

⚠ The reader most damaged is the one following README's own instructions, who reads
`overview.md` → `concepts.md` and comes away with the pre-arc model stated as settled fact, having
been shown the *argument against* the direction the project is actually taking.

**Revise:** add a status banner to `concepts.md` and `overview.md` in the shape the design docs
already use (line 3, bold), naming `facts-as-nodes.md` as the arc that revises them, and mark the
four passages above inline. `execution-model.md:16` already does exactly this — *"This page
describes what runs; `self-and-processes.md` is the design that revises it"* — so the pattern is
established in the directory and simply has not been applied to the two most-read pages.

---

## B. ⚠⚠⚠ Four notations for *a rule*, and nothing names the winner

| notation | where | status given |
|---|---|---|
| `fn seal(j: jar) -> sealed_jar:` + CNL blocks | `overview.md:33`, `authoring.md`, `reference/isa.md` | current, checked by the self-test |
| `pass: <head> { MINT / LINK }` | `passes.md:37` | sketch, reviewed and **rejected** in the same file |
| `when <condition> then <start a process>` | `self-and-processes.md:308` | design, nothing built |
| `causes(<moment>, <moment>)` | `rules.md` §2 | design, taken fresh |

Four surfaces for the one construct the whole system is about. `rules.md` §1 rejects the second,
`passes.md` now points forward to `rules.md` — but **`self-and-processes.md` §8's `when/then`
trigger form is not reconciled with either**, and it is the one that will collide first, because
§8 and `rules.md` §9–10 are describing the same mechanism (what starts a process) in different
notations without cross-referencing.

⚠⚠ And underneath the notation there is a real disagreement, not a cosmetic one:

> `overview.md:28` — **"Nothing fires.** A rule has parameters and runs when something calls it, on
> the arguments it was given, and never otherwise." Stated as a foundational commitment, with the
> trade written out.
>
> `deliberation.md:3` — "**Because nothing fires**, something must decide what to do next, and that
> decision is the whole of the system's control flow."

versus `self-and-processes.md` §8 (*a trigger is a rule whose condition is over the graph*) and
`rules.md` §9 (*recall proposes rules given the situation*). Both design docs reintroduce
condition-driven activation. Neither acknowledges that it is reversing a commitment that two current
pages present as load-bearing.

**Revise, in order:**
1. `rules.md` — add a section reconciling `when/then` triggers with `causes(A, B)`; they are the
   same object (a trigger is a rule whose consequent starts a process), which should be *stated*
   rather than left to a reader to notice.
2. `self-and-processes.md` §8 — point at `rules.md` for the form.
3. `overview.md:26–46` and `deliberation.md:3` — say what survives of *nothing fires* under
   recall + arbitrate. ⭐ The honest answer is that it **does** survive, and sharpening it is worth
   a paragraph: nothing fires *automatically*, because recall proposes and arbitration commits — the
   original property was *no rule runs without something selecting it*, and that is exactly what
   the four-primitive floor preserves. Left unwritten, it reads as an abandoned principle.

---

## C. Numbers that are stale or self-inconsistent

Mechanical, and the file that carries most of them **already warns about this exact failure**
(`HANDOFF.md:102`: *"it was written here as 98 and had drifted by one before anybody re-ran it…
re-read the number, do not quote this line"*).

| where | says | measured 2026-08-07 |
|---|---|---|
| `README.md:49` | **221 checks**, 0 FAILED | **267 checks, 0 FAILED** — run for this audit |
| `limits.md:267` | **221 checks** | **267** — same run |
| `HANDOFF.md:296` | reach: **87 named things** cannot be started by a rule | **99** (`python -m ugm.reach`) |
| `HANDOFF.md:553` | reach: **98** named things | **99** |
| `HANDOFF.md:100` | reach: **99** | ✅ correct |
| `HANDOFF.md:600` | *"there are **five**, unrelated"* — then enumerates **six** (`before`, `then`, `after`, `next`/frames, `next`/tokens, method-step position) | six |
| `defining-terms.md:17` | *"❌ **six** unrelated orders"* | six |
| `HANDOFF.md:625`, `expressiveness-and-uniformity.md:214`, `addressability.md:307`, `facts-as-nodes.md:46` | *"the **five** orders"* | six |

⭐ *Five orders* has propagated to four documents from one miscount in `HANDOFF.md:600`, whose own
enumeration disproves it on the next line. It is the clearest instance of the directory's failure
mode: a figure written once, quoted onward, never re-derived. **Fix the source and the four
quotations together, or it will re-propagate.**

**Revise also:** the three benchmark figures in `HANDOFF.md:452–459` carry a warning that wall-clock
drifts with the host, which is right, but the surrounding prose quotes them as bare numbers in six
other places. Either mark them all as *measured at a commit* or move them into `bench` output only.

---

## D. `reference/modules.md` is missing a third of the package

Ten modules exist in `ugm/` and are absent from the map:

`access.py` · `bench.py` · `boundary.py` · `construction.py` · `fact.py` · `horizon.py` ·
`labels.py` · `leak.py` · `precedence.py` · `reach.py`

⚠⚠ That is **every module from the last six arcs**, and it includes **all five instruments
`HANDOFF.md` instructs a new session to run** (`reach`, `horizon`, `labels`, `boundary`, `leak`) and
the two modules the live arc turns on (`fact.py`, `precedence.py`). A reader who takes
`reference/modules.md` as the map of the system cannot find the tools the handoff tells them to use.

**Revise:** regenerate the table. ⭐ And per the project's own standing rule — `reach.py` and
`horizon.py` both *derive* their inventories so they cannot drift — **this table should be
generated, not written.** A hand-maintained module map in a repo that refuses hand-maintained
inventories everywhere else is the same defect one level up.

---

## E. `README.md` describes a directory that no longer exists

* `README.md:3` — *"documents the Universal Graph Machine **as it currently stands**"*. Over half
  the directory is now design-ahead-of-build, and three files are raw notes.
* The page table lists **14 of 31** files. Missing: `harmony.md`, `facts-as-nodes.md`,
  `addressability.md`, `agent-representation.md`, `expressiveness-and-uniformity.md`,
  `defining-terms.md`, `self-and-processes.md`, `comparison.md`, `reflection.md`,
  `harmonization.md`, `mediated-access.md`, `predicate-dispatch.md`, `passes.md`, `rules.md`,
  `language-semantics-reasoning.md`, `observations.md`, `TODO.md`.
* Every missing entry is from the current work. README's map is a snapshot of the doc base at the
  end of the *previous* arc.
* README's *Where to start* sends a newcomer to the two pages finding A says are superseded.

**Revise:** rebuild the table with a **status column** (see H), and change *Where to start* to route
by intent — *what runs today* vs *what is being designed*.

---

## F. `HANDOFF.md` is 1,745 lines and is the mandated first read

`CLAUDE.md` says read it first. It currently holds five different documents:

| part | lines | is it *state*? |
|---|---|---|
| the live arc + verify/measure commands | ~1–110 | ✅ yes — this is the handoff |
| *Where to read* | 112–136 | ✅ yes, and it is better than README's table |
| *Current state* + *The swap landed* | 137–265 | ⚠ mixed — architecture prose, mostly stable |
| *What landed since the audit* — four *"the session before that, in one paragraph"* blocks + a 25-item bullet list + 15 traps | 266–451 | ❌ **history**, ~40% of the file |
| the plan (THE FRAME, matrix, P0–P5, items 0–7) | 484–1555 | ✅ yes, but it is its own document |
| *How to work on this* | 1556–1745 | ✅ yes, and it is generally applicable |

⚠ And the mandated first read opens its own plan section (`:488`) with *"the clean version of
everything in this section is `agent-representation.md`. **Read that first**"* — a page that appears
in **no** README table and has exactly one inbound link.

**Revise:** split into three, keeping the name on the first:
* `HANDOFF.md` — state, commands, where to read, the current arc. Target ≤ 300 lines.
* `docs/plan.md` — THE FRAME, the matrix, P0–P5, items 0–7.
* `docs/log.md` — the session-by-session history, newest first.
⭐ The **traps** list (`:379–451`) and *How to work on this* should stay in `HANDOFF.md` or move to
one page of their own — they are the highest-value prose in the directory and they are currently
buried at line 379 of a file nobody finishes.

---

## G. The same gap is derived independently in five places

*Order over a sequence / `step[i+1]` / taking turns* is the worked example in:

| doc | framing | numbering |
|---|---|---|
| `limits.md` §*Nothing constrains the ORDER* | capability gap | — |
| `advice-over-sequences.md` | four demands, §4 is the gap | §1–4 |
| `expressiveness-and-uniformity.md` | requirement 1 ∧ 2, the `[i+1]` sentence | §§1–7 |
| `defining-terms.md` | six needs in dependency order | 1–6 |
| `addressability.md` | finding 3, *which successor* | 1–8 |
| `HANDOFF.md` matrix | a blank row | P-plan |

Each is a good document. Together they are five numbering schemes over one problem, and the *five
vs six orders* error in C is a direct consequence — a figure crossing between them with nothing
reconciling the counts.

**Revise:** designate **one** as the canonical statement (`defining-terms.md` is the best candidate:
it is the only one whose entries are each traced to the forcing example) and reduce the other four
to a pointer plus whatever they add. ⚠ Do **not** merge them — the reasoning trails differ and are
worth keeping; what must go is five independent *inventories*.

---

## H. Status labelling is applied to the wrong half of the directory

Eight docs carry an explicit status on line 3 — `addressability`, `advice-over-sequences`,
`defining-terms`, `expressiveness-and-uniformity`, `harmonization`, `mediated-access`,
`predicate-dispatch`, `rules`. The practice is good and should be universal. It is missing from:

* ⚠⚠ **`facts-as-nodes.md`** — THE LIVE ARC, partly built (the `fact.py` wrapper and one swap have
  landed, world relations and attributes have not). A reader cannot tell which half.
* ⚠⚠ **`harmony.md`** — not a design at all but a **standing process** the user has asked to be
  applied to every representation decision. It should say so on line 3; today that instruction lives
  only in `HANDOFF.md:14`.
* `overview.md`, `concepts.md`, `planning.md`, `deliberation.md`, `memory.md`, `authoring.md` —
  describe what runs, but see finding A.
* `passes.md`, `observations.md`, `language-semantics-reasoning.md` — see I.

**Revise:** one bold line at the top of every file, from a closed set: **runs today** ·
**live arc — partly built** · **design, nothing built** · **standing process** · **raw notes**.

---

## I. Raw notes in the tree, one of them load-bearing

| file | lines | inbound links | problem |
|---|---|---|---|
| `observations.md` | 14 | **0** | No title, no status, no links in or out. Contains live design claims that duplicate or contradict other pages: *"maybe we don't need attention"* (vs `memory.md`, whose whole first section is the thread), *"users should not write functions"* (vs `authoring.md`), *"expert rules must be `<criteria> → goals/actions`"* (which is `rules.md`'s subject, arrived at independently) |
| `language-semantics-reasoning.md` | 41 | 3 | ⚠⚠⚠ **Unedited notes, and the entire current plan is framed on them.** `HANDOFF.md:494` quotes it as *the* one-sentence criterion the work is ordered by. Load-bearing content in a file that has never been written up |
| `passes.md` | 242 | 2 | The verbatim sketch is deliberately kept (correctly — the reasoning trail is worth more than a tidy version), but the file has no status line and the sketch's `pass:` form has since been rejected in the same file and superseded by `rules.md` |
| `TODO.md` | 15 | 1 | Says *"Nothing is here right now"* and then lists two items, both of which have graduated to their own pages. The file is now a stale pointer to `advice-over-sequences.md` and `harmonization.md` |

**Revise:** promote `language-semantics-reasoning.md` into a real page (its content is the frame for
everything — it deserves better than a note) or fold it into `agent-representation.md`, which is
already described as *the clean statement* of the same material. Fold `observations.md`'s four claims
into the pages that own them and delete it. Empty `TODO.md` or delete it.

---

## J. `rules.md` is not placed

Written this session, linked only from `passes.md`. It supersedes or touches `overview.md` (§*A rule
is a function*), `concepts.md` (the substrate), `planning.md` (backward chaining over return types
vs regression over signed deltas), `self-and-processes.md` §8, and `passes.md`. None of them except
`passes.md` knows it exists, and it is in neither README's table nor `HANDOFF.md`'s *Where to read*.

⚠ Minor, in the file itself: `rules.md` §8 links the text *"precedence"* to `reflection.md`; the
`seal_rule` / *last stage must be total* argument it is citing should be pointed at precisely, or the
link reads as a mis-target.

---

## The recommended order

| # | action | why first | size |
|---|---|---|---|
| 1 | Status banners on all 31 files (H), starting with `concepts.md` and `overview.md` (A) | Stops the one error that actively misleads: superseded prose read as current. Everything else is inconvenience | small |
| 2 | Fix the numbers (C), source-first for *five orders* | Mechanical, verifiable, and each stale figure is currently being quoted onward | small |
| 3 | Regenerate `reference/modules.md`, ideally derived (D) | The handoff instructs readers to run five tools the map does not list | small |
| 4 | Rebuild `README.md` with a status column, route by intent (E) | It is the front door and it describes a previous arc | small |
| 5 | Place `rules.md`; reconcile the four rule notations and *nothing fires* (B, J) | The deepest disagreement, and the one that will cost design time if left | medium |
| 6 | Split `HANDOFF.md` three ways (F) | High value, but nothing is *wrong* today — it is only unreadable | medium |
| 7 | Designate one canonical order/expressiveness inventory (G) | Prevents the next *five vs six* | medium |
| 8 | Promote or fold the raw notes (I) | `language-semantics-reasoning.md` especially — the plan's foundation is an unedited note | medium |

⭐ **What the directory does well, and should not be "fixed":** the reasoning trail — wrong turns
kept, probes that cancelled their own builds, traps recorded with the cost attached — is unusual and
is the reason a cold session can pick this project up at all. Every finding above is about
**framing**: which page is current, what the numbers are, where a thing is said once. None of it
argues for shortening an argument.
