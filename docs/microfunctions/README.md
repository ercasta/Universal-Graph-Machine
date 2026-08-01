# `docs/microfunctions/` — the design documents for the new engine

Moved here from `docs/units/` on 2026-07-30, when `microfunctions/` became the engine these documents
actually describe. The code's own entry point is `microfunctions/README.md`; these three are the reasoning
behind it.

| document | what it is | read when |
|---|---|---|
| **`HANDOFF.md`** | ⭐ **start here if picking this up cold** — state, decisions and their wrong versions, what to do next, known limits | first |
| `north_star.md` | the repoint — content as data, mechanism as mini-algorithms; triggers; microfunctions; what gets cut | first, always |
| **`plural_step.md`** | ⭐ **an action on EACH of many** — scope for the one thing a KB provably cannot supply: a collection can be built and cannot be planned over. Measured blockers, the lift-don't-author decision, four slices | before building anything plural |
| **`not_supported.md`** | ⭐ **what cannot be said** — expressions that fail for lack of a *capability*, separated from the ones that only look that way. Verdicts are SUGAR / KB / CAPABILITY, measured over a real file KB | before proposing a new form, and before assuming something is missing |
| `the_data_model.md` | plain-language prose: what a goal, a plan and a hypothesis *are*; the operations; why they nest without limit | to understand the model |
| `graph_data_model.md` | the same as signature tables, a closure check, named gaps, and the probe results | to verify something |
| `planning_workbench.md` | the workbench design — mappings, frames, mocks, the direction invariant, and the decisions that were got wrong first | before touching `workbench.py` |
| **`thread_and_system1.md`** | ⭐ the missing outer loop — thread as materialised short-term memory, System 1 as bounded association, types recognised bottom-up; all figures measured | **next up**; the computation model was never specified until this |

---

## Review, 2026-07-30 — what is still true, and what these documents now get wrong

These were written earlier the same day, before the substrate changed twice and before `microfunctions/`
existed. Most of the content survives — which is the encouraging result, since the data model was supposed
to be independent of the execution model and largely proved to be. But three passages are now **wrong**,
not merely dated, and are called out here rather than left to mislead. Corrections have been applied in
place; this section records what changed so the reasoning trail stays honest.

### Still true, unchanged

- **The whole concept model.** A goal is a node pointing at a claim it wants true, resolved by *positive*
  marks; a question is a goal; a procedure is a decomposition plus ordering; a prohibition is a stance fact.
  None of this depended on how rules execute, and none of it moved.
- **The closure argument for unbounded depth.** Every operation reads and mints structures from the same
  vocabulary, so depth is the same case repeated. If anything this got *stronger*: `types.py` makes the
  vocabulary explicit and checkable, and `function.py` closes it over function-creation too.
- **The prior-art sections.** ECS, GOAP, behaviour trees, SHACL, frames — all still the right comparisons,
  and the narrow claim (*same representation, so a rule can write a rule*) is now demonstrated in running
  code rather than argued.
- **The probe results** in `graph_data_model.md` §7 and `north_star.md` §5b. Historical records of runs
  that happened; they stand as written, including the false greens.
- **Triggers** (`north_star.md` §5/§5b), including the implementation rule that came out of probing:
  **check at APPLY time, not MINT time**, and never let a rollback boundary span a dispatch.

### Corrected — these were wrong

1. **`the_data_model.md`'s hypothesis section described a scope.** It said a hypothesis is "a region of the
   graph in which things can be held true provisionally," with conclusions marked as belonging to that
   region and discarding done by dropping the region. That is the mechanism we then decided *against*.
   A hypothesis is now an ordinary **node**, with ordinary subgraphs under it (`variant`) and explicit
   `backup` nodes for prior values — no scope, no relativization, no pencil/ink layer. Two things improved
   in the process: rival hypotheses now coexist as two live nodes (the old machinery entertained one at a
   time), and the **verdict is a fact** on a node, which closes `graph_data_model.md` §6.1's named gap by
   not reintroducing it.
2. **`north_star.md` §4 argued hypothesis-by-running against a scratch graph.** That argument was correct
   *against the objection it answered* (you do not need to walk a derivation symbolically), and it is why
   the repoint was safe — but the conclusion it reached, "pen the assumption into a scratch graph," has
   been superseded. Scratch graphs were the copy-on-write design; the substrate is mutable now, and
   hypotheses are nodes. §4 has been rewritten to keep the argument and drop the obsolete mechanism.
3. **"Operations are generic metarules"** throughout `the_data_model.md`. They are microfunctions —
   ordinary functions taking typed subgraph parameters, pointed at their arguments. `north_star.md` §3
   already said this; the prose document lagged.

### Superseded by better mechanisms, not wrong exactly

- **"Parts are separate nodes joined by named edges"** — still the rule, but the substrate now has *actual*
  named edges with ordered targets, so several places where the prose works around nameless edges and role
  nodes are more convoluted than they need to be. Notably, `graph_data_model.md`'s note that episodes need
  an externally-stamped turn counter to recover order is **obsolete**: ordering is native now.
- **`graph_data_model.md`'s concept and operation tables** cite `units/` and `ugm/` predicates
  (`chosen`, `ready`, `wants`, `raised`). The *operations* survive as a catalogue; the "built?" column now
  points at superseded code. Treat the tables as the operation vocabulary, not as a map of the codebase.

### Closed since this review was written

- **§6.3, "an application is not a node"** — the gap this project called its most load-bearing. Closed by
  `microfunctions/application.py`: applications and episodes are ordinary nodes, and episode ordering is
  native rather than needing a driver-stamped turn counter.
- **§6.2, "no plan node"** — closed by `plan.py`, and better than the section imagined: a plan is a *lazy
  chain* of pending calls, so it is data that can be compared and critiqued before anything runs.
- **§6.1, "a hypothesis's verdict is not a fact"** — closed by `hypothesis.py`, by never reintroducing the
  scope that caused it.

### Still open

- **Replanning on divergence.** `execution.py` reports a deviation and offers explored alternatives;
  nothing yet chooses one or re-proposes from the actual state.
- **⚠ Conflict detection — a regression, not a deferral.** The old engine surfaced two conclusions
  disagreeing; the new one has last-write-wins. The composition-safety argument rested on the old
  behaviour. Reflective microfunctions are the intended answer and need no new mechanism.
- **Termination.** The ISA fails loudly at `MAX_STEPS` as an honest stand-in; nothing solves it.
- **The audit in `north_star.md` §6** — which of the ten scenarios actually needs skolems, ATMS, bands,
  stratified NAF, or demand-driven SIP. Not run. Deletion of `ugm/` machinery should wait on it.
