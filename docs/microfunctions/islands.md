# Islands — what the engine cannot model, and why

**The question this document exists to answer**, and it is deliberately not *"what does the parser
reject"*:

> Which expressions can this engine not model — where the obstacle is **not** a missing grammar, but that
> nothing *executes* the thing, or that the thing exists and is **unreachable from the rest**?

`not_supported.md` asks a neighbouring question — *what cannot be SAID* — and answers it with
SUGAR / KB / CAPABILITY. This one asks *what cannot be DONE, or cannot be COMPOSED*, and the taxonomy is:

| verdict | means | cost to close |
|---|---|---|
| **PARSE** | the surface lacks a form; the machinery exists and is reachable | a verb, sometimes a line |
| **EXECUTION** | it can be said and **nothing runs it**, or it runs and means nothing | real work |
| **ISLAND** | it exists, it works, and it **cannot be reached or composed** from where it is needed | usually a lift, sometimes a substrate change |

⚠ **ISLAND is the verdict that hides.** An island passes its own tests, has a docstring, and is *used* —
by exactly one caller. Nothing fails. It surfaces only when a second caller needs it and reimplements it,
which is how four of this session's findings were found.

⚠⚠ **And a fourth, unnamed verdict is the dangerous one: it PARSES, RUNS, AND MEANS THE WRONG THING.**
Twice in this session a form was accepted, planned, and reported **done with an empty plan, having never
looked**. That is worse than any gap on this page, because a gap announces itself.

---

## 1. The method, which is the only reason to trust the list

Not derived from a design document. Fourteen utterances of the shape *"what would somebody actually say to
an agentic coding assistant?"*, each pushed **all the way to execution** rather than to the parser —
`probe_agentic_coding.py`, which records four verdicts (`RUNS` / `PARSES` / `REFUSED` / `NO FORM`) and
keeps the ones that turned out to be wrong.

**⭐ Push to execution, never to the parser.** `PARSES` is the verdict that found the two false successes,
and a parser test would have scored both of them green.

**⚠ The probe corrected itself three times, and every correction made a claim weaker:**

* *"for each file, lint it"* was reported as a **capability gap**; it was the probe's own `max_depth` of 8
  against a nine-cast plan. It plans fine at 12 — at **1124 imagined states**, so plurality is a **cost**
  problem, not a capability one;
* the plural constraint was measured at **band 1** and is band **4** — raw nodes had been passed where
  `relevance` wants mappings, which is the trap `plural_step.md` §1 already records;
* *"the planner structurally cannot ask"* was written into a docstring by inference from
  `dispatch.service`'s workbench refusal, then **measured false** — the target is a question node minted
  fresh in the real graph, so the refusal never fires.

> **The standing lesson, now with a third year of evidence: every claim in this project that got checked
> came out weaker, and the weakened version is the one worth keeping.**

---

## 2. What was found, classified

### Closed during this session

| # | expression / thing | verdict | what it actually was |
|---|---|---|---|
| 1 | *"list all the files in the repo"* | **⚠ false success** | `x.k known` accepted for a key naming an **edge**, and for a key naming **nothing** (a mistyped plural). Reported done, empty plan, never looked. Both refuse now. |
| 2 | *"after you edit a file, lint THAT file"* | **ISLAND** | `some <n> in <ref> by <link>` existed in `criterion`, absent from `method`. Lifted. |
| 3 | *"ignore that"* | **EXECUTION** | `intake.read` recorded **nothing about the fact that somebody said it**. Measured: two blocks authored, thread held only its opening entry. → `discourse.py` |
| 4 | a discourse with three actors | **ISLAND** | the speaker was a **string attribute**. An utterance is a world event; the thread merely attends it. |
| 5 | *"who may withdraw what"* | **EXECUTION** | anybody could withdraw anything — a policy nobody chose. → authority as world data |
| 6 | the system asking a question | **PARSE-ish** | needed no machinery: asking is a **dispatch**, `observes=True`. |
| 7 | another process writing to the graph | **ISLAND** | external utterances landed in the conversation and were **invisible** — `utterances` reads off the thread. → `attend_new` |
| 8 | a goal constraint / a step / a condition | **ISLAND** | **three hand-written parsers** for one grammar, drifted in four ways nobody chose. → `intake._shape` |
| 9 | `x l+ y` in a `when` line | **EXECUTION** | the parser change alone would have parsed it while the evaluator compared **one direct edge**. Evaluator moved with the surface. |
| 10 | a defeasible prohibition | **EXECUTION** | no force could express it; a consumer wrote ~17 lines of Python and lost auditability. → `norm.py` |
| 11 | *"has this always been true"* | **EXECUTION** | four unconnected notions of *when*, **no clock at all**, none of them a node. → `clock.py` |
| 12 | body-line vocabularies | **ISLAND** | reachable only as display strings inside raise sites, so a consumer had to re-type the grammar. → `intake.FORMS` |
| 13 | an ambiguous name | **PARSE** | the answer set was in hand and dropped to report a count. → `intake.Ambiguous.candidates` |
| 14 | authored advice with no `rank=` | **⚠ false success** | a `prefer` block parsed, minted a node, and was **inert**; indistinguishable from advice that lost. Now warns. |

### Open, ranked by what they block

| # | expression | verdict | note |
|---|---|---|---|
| A | *"here is how a trading floor works"* | **ISLAND** | ⭐⭐⭐ **operators are authorable only in `.mf` assembly.** Everything a domain contributes is data **except the mechanics**. `asm.py` says a CNL for this is "explicitly future work". This is the largest remaining island. |
| B | *"the newest quote"*, *"the three highest bids"* | **EXECUTION** | G0/G1 — the engine has *act* and *check* and no **find**. Now has three callers where the catalog deferred it for having none. |
| C | *"total volume"*, *"how many"* | **PARSE (tool-closable)** | a machine closes a computation gap; only representation closes a distinction gap. Aggregates are the first kind. |
| D | plan frames vs. real history | **ISLAND** | `workbench.predicted_changes` computes the before/after pair and **throws it away**. A frame transition *is* a *becoming*. |
| E | *"meat takes 1 minute to cook"* | **EXECUTION** | projection: current state = latest observation aged forward by a rule. `memory.believed` vs `g.attr` is already the right split; the magnitude to compute staleness from arrived with `clock.py`. |
| F | *"when did this file appear under this directory"* | **SUBSTRATE** | edges have **no identity**: `eprops` is keyed by `(src,label,index)` and reindexes. Slice one of the substrate change. |
| G | `criterion.decide`'s Python loop | **ISLAND** | ⚠⚠ `loop.py` claims *"the Python-control-loop inventory is empty"* and **it is not true** — a `propose=` hook loops to completion, invisible to the agenda. |
| H | `remember`, `learn`, `forbid`, `ignore that` | **PARSE (shape)** | four things now want a surface, and two do not fit `<verb> <label>:` + body. One decision, not four. |
| I | `type` / `prefer` bodies | **ISLAND** | the last two parser islands, not yet on `_shape`. |

---

## 3. ⭐⭐⭐ The findings that generalise

**(a) The same defect has now appeared in five places, and it is the project's signature.** *The one thing
the system was doing was the one thing it could not point at* — attention (`thread.py`), the goal
(`goal.py`), deliberation (`search.py`), the decomposition rung (§6n, still open), and now **the telling**
(`discourse.py`). When something feels unreachable, ask what the system is *doing* that has no node.

**(b) An island is created by a second caller, not by a first.** `some … in … by …` was correct in
`criterion` for as long as only criteria needed it. Three parsers for one proposition grammar were each
fine alone. ⚠ So the review question is never *"is this right?"* but *"who else will need this, and what
will they do when they cannot reach it?"*

**(c) A form that parses and does nothing is worse than a missing form.** Both false successes were
*accepted* text on the surface a language model writes to. A model emitting a good block and seeing no
effect has no way to tell it was ignored. ⚠ Refusal is the feature; **silent acceptance is the bug**.

**(d) The surface is a programming language missing bind, branch and loop.** The three utterances that
failed were exactly variable binding, conditional, and iteration. ⭐ Bind is now done. ⚠ *Branch turned
out not to be needed* — see §4.

**(e) One shape, several executors — never one grammar per executor.** SQL is the cautionary case, and it
is precise: its *expression* grammar composes across every clause, its *clause* grammar is forty years of
islands, and its answer to a limited execution model was **a second language** (PL/SQL). Every rule here
is `conditions → consequent`; only the consequent and the executor differ.

**(f) A mechanism built for one purpose closed an unrelated gap twice.** `discourse.authority` — written
for multi-party retraction — arbitrates **norms** unchanged, because *a norm's source is its speaker*. And
`path.reaches` now serves three rankings (`contains+`, `authority_over`, time's `before`). ⚠ That is the
argument for closing islands rather than adding mechanisms: the second use is free only if the first was
reachable.

**(g) Measure the thing, not the pieces.** Three claims this session were assembled from correct
components and were false. A measurement whose **control does not light up** is not a measurement — it
caught a retraction check that withdrew a criterion making no difference, and an authority check that
asked whether Bob could withdraw Bob's own utterance.

---

## 4. ⭐⭐ Two things that turned out NOT to be gaps

Recorded because each is something somebody would otherwise have built.

**Branch-on-outcome.** *"Run the tests; if any fail, fix them"* needs no conditional in the surface.
`END_TO_END_plan_act_diverge_replan_succeed` and `recovery_resumes_onto_the_branch_reality_took` are both
green: the engine plans, acts, **diverges**, and replans — and forking on declared outcomes already works
where it is wanted. The `if` is the *speaker* explaining a contingency, not a construct to mirror, and
replanning is **strictly better** because it handles outcomes nobody enumerated. ⚠ The genuine gap is
narrow and different: nothing says *where a fork is worth paying for*, which §9 item 4 already states as a
policy (*"branch only where being wrong is expensive"*).

**Unbounded nesting in the CNL.** Depth already exists — in the **decomposition tree at run time**, where
every rung is a node that can be inspected, disputed and explained. A deeply nested sentence yields one
opaque tree instead. ⭐ The correction that mattered: *seams* are the point, and composition gives them
where nesting does not.

---

## 5. What to do, in order

1. ✅ **DONE — the comparison operators reach goals and conditions.** `type` held the full set, and it was
   an accident of where the comparison code sat. ⚠ **Not a parser edit:** three readers assumed equality
   and each was wrong differently — `goal.holds` never held, `query.refutes` reported a positive *no*
   about a satisfied range, and `conflict.unsatisfiable` called `size > 10` with `size > 20` impossible,
   which **refuses an achievable goal**. All three share `types.compare` now.
   ⚠⚠ **Widening it re-created a defect that had only ever been refused BY ACCIDENT:** `a.size > b.size`
   was three words with an unknown middle, so it was read as a link and `parse_link('>')` rejected it.
   With `>` legal it parses, and the right side is a **literal** — silently `a.size > "b.size"`, which can
   never hold. *A refusal that exists by accident is not a refusal; it survives only until the accident
   stops holding.*
   ⭐ `prefer`/`avoid` is **closed, not pending**: its body names an action and an individual
   (`action f | touching x | when T`), not a proposition. There is nothing real to share.
2. **The typed consequent** (A, H) — collapse `step` / `do` / a memory write / **effects** into
   `conditions → consequent`. ⭐ This is what makes `remember` and `learn` cheap rather than two more
   islands, and **operator-as-data is the motivating case**: it is the last island in the domain surface,
   and declared effects are *exact* where `establishes` currently walks a body linearly and skips jumps.
3. ✅ **DONE — edge identity (substrate slice one).** `eprops` keyed by id, `inc` generalised so an edge
   is an ordinary link target, `_reindex`/`_label_props`/`_restore_props` **deleted**. Edges follow the
   node pattern: journalled mint, fresh ids in a copy. ⭐ Back-refs were free — `g.sources(eid)` answers
   *"what refers to this edge"* with no change to the reverse index.
   ⚠⚠ **Two silent bugs it introduced, both of which passed the full suite:** `drop` popped `out` without
   `eids`/`edges`, and `workbench` read `eprops` by the **old** key, silently returning `{}` — a copied
   edge lost its properties and *nothing failed, because no check had ever copied one.*
   ⭐⭐ **And a proposal that came out of it was WRONG, which is worth more than the slice.** `thread.py`
   said *"a `prev` edge property cannot be pointed at"*, so `connect` — which mints a node for anything
   something else must point at — looked like a workaround that could now be deleted. It cannot: it is
   **enumerable by `kind`**, and as an edge it would be indistinguishable from the structural `at` /
   `prev` / `step` without a label convention somebody has to remember. It was kept, and the *reason* was
   corrected in place.
   > **Closing a substrate gap can invalidate the JUSTIFICATION for a design without invalidating the
   > design.** A stale reason is dangerous in its own right — it is what somebody copies into a new module
   > because they trusted it. Restated rule: *ride on the edge what merely describes that edge; mint a
   > node for what has its own ends, its own attributes, or must be enumerable as a kind.*

   **Slice two, not started:** edge refs on the surface (`path.py`).
4. **`becoming`** (D, E) — minted where a plan meets reality, from frames that already exist, dated with
   moments. ⚠ Imagined becomings stay derived: §5f's cost refusal still holds for the hundreds a search
   makes.
5. **The sidecar** (G) — decision rules have the same shape as everything else and differ only in
   **execution**: a sidecar that runs to completion beside the loop that ticks. Deleting
   `criterion.decide`'s Python loop is the vacuity test for the whole architecture — `loop.py`'s claim
   becomes true for the first time.
6. **`find`** (B) — now with three callers.

⚠ **Scope is not on this list, and that is deliberate.** *Anything expressable is in scope; the how is a
design choice, and "in a consumer's Python" is not one of the available choices.* See `not_supported.md`
§4.
