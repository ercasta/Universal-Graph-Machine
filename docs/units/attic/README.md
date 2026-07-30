# Attic — the `units` reasoning trail, never authoritative

Design documents, status pages and decision records for the `units` substrate whose work is **finished,
superseded, or reversed**. They are kept because they hold the *rationale trails* — several decisions here were
reversed, and knowing why is what makes the current positions re-derivable — but **nothing in here is a source
of truth about the current system**.

For that, read `../model.md` (the consolidated model), `../STATUS.md` (what is being worked on), and the
CNL/forms documents listed in `../README.md`.

> Some documents carry stale status headers that predate their own supersession. **The table below is the final
> word on each.**

| doc | what it was | how it ended |
|---|---|---|
| `model-superseded.md` | The computation model as first written, 2026-07-26, with `[R1]`/`[R2]` revision marks added later | **CONSOLIDATED into `../model.md`** (2026-07-28). Read it for the original derivation of §§1–5 and for the *whole* of the old §6 (statements, seals, tunnels), which is the single largest thing this project deleted |
| `revision-01-standing-circuits.md` | Circuits **stand**; values revive from the axioms each turn. Adopted and built 2026-07-27 | **CONSOLIDATED into `../model.md`**. Its §3 (what revive-from-axioms deletes) and §5 (attention binds dangling gates) are the arguments behind the current §§1 and 7. Its §4 energy-on-the-value was later replaced by energy-on-the-gate |
| `revision-02-two-planes.md` | Two planes: inert data vs the running circuit. Scope becomes **support**; the tunnel dissolves | **CONSOLIDATED into `../model.md`**. The richest of the three — §§8b–8e are the build logs for the consolidation, `pattern:` and `effect:`, and its §6 carries the overlay spike numbers in full |
| `STATUS.md` | The status page for the pre-inversion `units` engine (174 tests) | **SUPERSEDED 2026-07-26**, and it says so in its own header. The code it reports on was deleted and rebuilt twice since. Superseded as a *page* by `../STATUS.md` |
| `substrate_inversion.md` | The lab notebook for the substrate inversion — an append-only trail of what was tried and what broke, 2026-07-25/26 | **HISTORY, and it says so in its own banner.** Moved here from `docs/design/` (2026-07-28), where it had been sitting among the retired `ugm` engine's design docs. 2,714 lines; not maintained |
| `reference-annotated.md` | The reference for the pre-inversion `units` substrate, with the user's annotations in the margin | **SUPERSEDED.** Those annotations are what produced the inversion — the original `model.md` answered them one by one, and that table survives nowhere else |
| `decisions/` | 41 decision records, `0001`–`0041`, from the pre-inversion design | **MOSTLY CONTRADICTED.** Each file now carries a *current* status line; `decisions/README.md` has the whole table. Seven survive and are in force |
| `forms_extra_considerations.md` | A Q&A trail pressure-testing `../forms_discourse.md`/`../forms_llm.md` from first principles, 2026-07-28 | **FILED, 2026-07-30 hygiene pass.** It said "not a specification, nothing here should be cited outward" from the day it was written — never load-bearing on its own, and every idea that survived from it is already inside the two documents it was pressure-testing |
| `planning_example.md` | The raw, unedited note that started the whole planning/middle-tier/closed-class-rechallenge arc, 2026-07-30 | **FILED the same day it was superseded.** Every idea in it (meta-rules reading a causal fact to mint a plan step, REQUIRES/satisfies business norms) is now developed in `../planning_meta_concepts_arc.md` §5/§7 and `../closed_class_rechallenged.md` §5/§7. Kept verbatim as the historical seed |
| `handoff_ugm_reversion_evaluation.md` | The `ugm/`-reversion audit + the tunnel/metaprocedure resolution, 2026-07-30 | **RESOLVED the same day.** Decision: neither revert wholesale nor stay on `units/`'s substrate — keep `ugm/`'s substrate (`attrgraph.py`) + ISA (`machine.py`) + rule-lowering, replace `ugm/lowering.run_bank`'s blind whole-graph fixpoint driver with an outer-loop metaprocedure built from "a rule writes a rule." Resolution recorded at the top of the file itself; full rationale in `../arc_recap.md`'s current Act |

## What was deleted outright rather than filed here

- `docs/units/reference.md` — replaced by the original `model.md`; recoverable from git history.
- `docs/units/attachment.md` — folded into `revision-01` §7 and deleted the same day. Its acceptance harness
  survives inside that section.
- `units/standing.py`, `units/turn.py`, and the pre-inversion engine (`assemble`, `circuit`, `loop`,
  `cooldown`, `recall`, `describe`, `unit`) — all deleted during the consolidation. The findings they produced
  are recorded in the two revisions.

## What is *not* here

The retired `ugm` engine's documentation. That is a different generation with its own index and its own attic:
`docs/README.md` and `docs/attic/`. Nothing in this directory supersedes anything in those.
