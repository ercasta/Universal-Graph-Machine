# Goal/subgoal machinery — design, verified against the running engine

**Status: design, settled 2026-07-29, worked examples built and green (`units/goal_experiment.py`,
`units/goal_decomposition_experiment.py`, `units/nac_verification_experiment.py`); updated 2026-07-30 for
two corrections (§6/§8's same-turn gate dropped, both self-inflicted) and §9's NAC/closed-vs-open-world
finding.** This is the document `model.md` §8 points to and `cnl_engine_goal_plan.md` §7 was building
toward. It exists because §7's three-thread arc (goal lineage, a first System 1, additive rewriting) needed
a worked example before being written up as settled — that example is built, it found several places where
the first draft over-engineered a fix, and this document states the corrected, minimal shape plus the
general mechanisms it exposed.

**Read `model.md` §8 first** (goals as data, outcome as a positive fact, energy/burn) — this document only
covers what §8 leaves as "design, not built": the lineage relation itself, and how it survives across turns.

---

## 1. The shape, unchanged from `cnl_engine_goal_plan.md` §7c

| fact/relation | shape | who writes it |
|---|---|---|
| a goal | an ordinary node + a `wants:` role pointing at its satisfaction-condition claim | a mutating rule |
| subgoal lineage | `goal -[raised]-> subgoal`, interned (get-or-create per parent) | a mutating rule, guarded |
| outcome | a positive marker attribute on the goal node — `achieved` / `diverged` / `abandoned` | a mutating rule |
| decay | `abandoned=True` **plus** retracting the goal's own gate-wiring; the `raised` lineage edge stays | a mutating rule, using the one non-monotone effect (`Drop`) |

Nothing here needed a new effect kind or a new gate concept. All four rows are buildable with the five
effects `units/engine.py` already has (mint, edge, attribute, identify, retract) and the `absent()` guard
`units/match.py` already has.

---

## 2. Interning needs a guard, and the guard needs delivery — the two things that are load-bearing

**Interning** ("don't raise a second subgoal for the same parent + condition") is an ordinary NAC pattern:

```python
_GOAL_PAT = (atom("g", name="goal", out=(role("wants", atom("c")),)),
             absent(atom("g", out=(role("raised", atom()),))))
```

This works exactly as it looks *once the guard's own view actually contains what a prior turn concluded.*
That "once" is the entire content of §3 below — it is not automatic, and getting it wrong the first time is
the most useful part of this write-up.

**Machinery visibility** (a decay rule that needs to see and drop a `<wire>` occurrence) needs the same
discipline `model.md` §6 already states as invariant 19 — *"machinery must be delivered to a gate before any
pattern can see it"* — and needs nothing beyond that. See §4.

---

## 3. How a turn actually works here — the mechanism this write-up is really about

This is the part that generalizes past goals entirely, and it deserves to be stated once, plainly, because
nothing in `model.md` spells it out end to end even though the mechanism is used three times in
`tests/units/test_engine.py` (`test_a_mutating_rule_can_conclude_a_wire`, both
`test_a_rule_writes_a_whole_rule_with_nothing_authored_in_python` variants).

**A `Cell`'s `held` value is a fixed snapshot, taken once, at construction.** `Network.given(g)` computes
`effects_of(g)` a single time and stores it. `revive()` does not re-derive an axiom's contribution from
`self.asserted` — it reseeds the queue from `self.axioms` exactly as they are. So calling `revive()` again on
an unmodified `Network`, with unmodified axioms, redelivers *exactly* the same values to every wired unit. This
is not a partial re-run of "the world as it now stands" — it is a *repeat* of the first run's input, and by
`model.md` §5 (*"a repeat arrival is a firing... there is no value-comparison test suppressing it"*), a unit
sees the identical value again and fires again. Feeding an interning guard the same, stale snapshot forever and
expecting it to notice its own prior output is asking it to see something that was never delivered to it.

**⚠ The wrong reaction to this, tried and reverted while building `goal_experiment.py`:** treat "next turn" as
"build a brand-new `Network`, re-run `given()` on the whole accumulated graph, re-add fresh unit objects." It
works, but it is not what the design calls for and it is not the cheaper of the two options: `model.md` §5 is
explicit that **units stand across turns** — *"a partially wired unit is a stable state"* — precisely so that
wiring, described patterns, and effects persist as the same graph-and-Python structures rather than being
re-derived from scratch on every turn. Discarding the `Network` object each turn throws that away for no
reason; it was reached for because it visibly "worked," not because it was the design's answer.

**The actual mechanism — precedented, minimal, and what this document settles on:**

> **A turn is: the same `Network`, the same standing units, and an explicit decision about which axioms
> deliver what.** When nothing new needs to be seen, an axiom's `.held` is left as `None` (or simply not
> re-triggered) and nothing refires on stale repetition. When something *does* need to be seen — including a
> unit's own prior conclusion, now sitting in `self.asserted` after write-back — a fresh axiom captures it:
> `n.axiom(*effects_of(n.asserted), name=...)`, wired onto the gate the consuming unit already has.

Verified directly (`units/goal_experiment.py::check_lineage_interning_managed`): one `Network`, one
`StandingUnit`, axiom nulled and replaced with a reflective snapshot between turns — the guard correctly blocks
a second subgoal (1 → 1). No second `Network`, no rebuild.

**Why this matters beyond goals.** Any standing rule that needs to react to *its own* (or any other rule's)
accumulated output across turns — not just goal lineage — hits this exact mechanism. It is the general answer
to *"how does a unit ever see what write-back just added"*, and goal lineage is simply the first place this
document had to state it precisely because interning is the case where getting it wrong produces a visible,
countable defect (a duplicated subgoal) rather than a silent one.

---

## 4. Machinery delivery needs one gate, not one gate per source

The decay rule (`abandoned=True` + `Drop` the watching wire) needs to see two things at once: the goal's own
`stale` fact, and the `<wire>` occurrence connecting the goal's watcher to its feed. The first attempt at this
split delivery across two gates — one fed by the plain axiom, one by a reflective axiom carrying wire data —
and reported that as a requirement ("machinery needs its own gate"). It doesn't, in general:

> `effects_of(n.asserted)`, taken **after** `given()` and `wire()` have both already written into the graph,
> is a **strict superset** of what the plain axiom alone would have delivered. One reflective axiom, on the
> unit's one ordinary gate, already contains everything — the plain axiom wired to the same unit becomes
> redundant, not conflicting.

The general rule, stated once: **wire the single axiom that is a superset of everything a unit's pattern
needs.** Splitting across gates is only necessary when no single available snapshot already contains
everything — which did not turn out to be the case here, and should be checked before assuming it's needed
elsewhere.

⚠ **Amendment, from `units/quantification_cursor_experiment.py`: sometimes no single available snapshot *is*
a superset, and the fix is a second, narrower source, not a bigger snapshot.** A reflective axiom refreshed
*before* `revive()` runs necessarily reflects the graph as it stood *before* this same turn's own mutating
rules fire — so a rule wired only to that snapshot sees this turn's sibling conclusions one turn late. The
fix there was a second gate fed directly by the sibling rule's own `Cell` (its output from *this* firing,
available before write-back applies it to `self.asserted`), not a second, bigger reflective snapshot. Restated
precisely: **wire every source that's needed; reach for a bigger reflective snapshot only when the gap is
*what's been written to the store*, and reach for a sibling's own cell when the gap is *what a unit concluded
this same turn*.** §6 below has the worked example.

---

## 5. Additive rewriting — a distinct finding, and it did generalize

Separate from goal machinery, but part of the same next-action (`cnl_engine_goal_plan.md` §7a's third thread):
does minting a fact's *new* form **alongside** the old (never replacing it) let two independent rules, one per
form, both fire?

Verified (`units/goal_experiment.py::check_rewrite_via_addition`): yes, mechanically, with no new effect kind.
The one real finding is a repeat of `computation_units.md` §5's tunnel, from the additive-mint side rather than
the `Identify`-merge side: `StandingUnit.view()` is built from an `EMPTY` base, never `self.asserted`, so a
rule's own output never carries a copy of an attribute it merely *read* — only what it minted or concluded. A
rewrite rule that mints `age_claim --about--> paul` does not re-assert `paul`'s `name` or other attributes; a
consumer matching on those attributes over the rewrite rule's output alone will fail, not because the rewrite
is wrong but because the consumer over-constrained a match against data nothing re-asserted. **This is now
confirmed twice, independently (merge and mint), so treat it as a standing property of the engine, not a
one-off bug to patch per rule:** any rule consuming a derived fact must be wired or pattern-scoped to exactly
what that fact's producer re-asserts, never assume a matched node's other attributes travel with it for free.

---

## 6. The quantification cursor, built — `closed_class_inventory.md` §8 case (c)

*"Did every member of a bounded set get evaluated, when checking each one needs a tool call (more than one
revive)."* Built and verified (`units/quantification_cursor_experiment.py`): a `checked` marker per member,
minted by a mutating rule once that member's result has arrived from outside — the cursor `model.md` §8
requires be asserted data, not a computation unit's overlay, or it would reset every revive and re-ask an
already-answered member forever. Verified directly: `checked` survives a turn where the member gets *no* new
input at all (`check_cursor_survives_because_it_is_asserted_not_derived`).

The universal outcome — `achieved` (every member eligible) or `diverged` (at least one wasn't) — resolves the
same way `goal_machinery.md` §2 already established: a positive fact, concluded only once no unchecked member
remains, never read off an absence. Verified both ways (`check_all_eligible_reaches_achieved_only_at_the_end`,
`check_one_ineligible_member_reaches_diverged_not_achieved`), and verified that **neither** fires prematurely —
`achieved`/`diverged` stay `None` through every middle turn, which matters: concluding completeness early is
exactly the false-positive `model.md` §8 exists to prevent.

**The one new finding is §4's amendment above, found here first.** Fan-out from one reused reflective axiom
(§4) is not quite enough when the consuming rule needs to react on the *same* turn a sibling rule produces the
fact that completes it — the reflective snapshot, refreshed before `revive()` runs, is one turn stale relative
to that sibling's own output. Fixed with a second gate wired directly to the sibling's `Cell`, not a bigger
snapshot.

---

## 7. What's still open

- ~~A subgoal with its own satisfaction condition~~ — **built and run, 2026-07-29,
  `units/goal_decomposition_experiment.py`, three checks green.** See §8 below.
- **System 1** (`model.md` §7, associative retrieval) — a first prototype exists (`units/system1_experiment.py`)
  but everything in this document is still hand-wired past that point (retrieval proposes a wire; nothing yet
  proposes the *reflective-axiom-vs-sibling-cell* choice §4/§6 found matters). §7 nominates System 1 as the
  thing that eventually absorbs that authoring cost too.

---

## 8. Built and run, 2026-07-29 — `units/goal_decomposition_experiment.py`, a subgoal with its own condition

Every prior worked example either used a bare lineage marker (§6's cursor quantifies over a flat,
externally-given member set) or a subgoal with no `wants` of its own (`goal_experiment.py`). Neither
tests real decomposition: a goal minting *several* subgoals, each with an independent satisfaction
condition, each resolved on its own turn, with the parent's own outcome bubbling up only once every
child's is in — the shape §7c's original table actually described. Three checks, all green.

**Composes, doesn't reinvent.** Every rule here — first-level (decompose; each subgoal's own
achieved/diverged) and second-level (the *parent's* achieved/diverged) alike — uses the single reused
reflective-axiom-lifecycle discipline (§3). Nothing new was needed in the engine.

**⚠ Correction, 2026-07-30: §6's same-turn sibling-cell gate has been dropped from both this file and
`quantification_cursor_experiment.py`, and the "same-turn, not one turn late" claim below is superseded.**
Checked directly against `Network._drain()` (`units/engine.py:801`): a sibling's own conclusion already
propagates within one `revive()` call via the ordinary queue mechanism, so the extra gate wasn't fixing a
correctness gap. And the *other* half of the original justification — "otherwise the answer might never
appear if no further turn comes" — was also wrong: a unit that can't fire because a gate is empty goes
`dangling()` (`engine.py:569`), which `model.md` §7 already names as the honest "still waiting" signal for
an outer driver to act on, not a silent failure needing to be engineered around. The engine's own test
suite already treats one-turn lag on freshly-produced structure as normal
(`test_a_rule_writes_a_whole_rule_with_nothing_authored_in_python`'s docstring: *"on the next turn it
runs"*). The parent's achieved/diverged now use one gate, like everything else, and see a child's
conclusion one *settle* turn later — traced explicitly, not hidden behind extra wiring.

**One wrinkle specific to decomposition, not present in the flat case, and still real.** The parent's
`achieved` guard (`absent(raised subgoal with achieved=None)`) is vacuously true *before any subgoal has
even been minted* — an undecomposed goal would read as trivially, falsely achieved.
`quantification_cursor_experiment.py` never hit this because its member set was given up front, never
minted by the same rule chain that consumes it. Fixed with a positive existence premise
(`atom(out=(role("raised", atom())))`) alongside the NAC — checked explicitly
(`check_undecomposed_goal_is_not_vacuously_achieved`), not just reasoned about. §9 below generalizes this
into "don't trust an open-ended absence without an explicit closure fact."

**Verified, both directions:** both children succeeding reaches `achieved` on the settle turn after the
*second* child's result arrives; one child diverging reaches `diverged` on the settle turn after its own
result, without waiting on its still-pending sibling, and never falsely reaches `achieved`.

**What this closes:** the first item of §7's open list. What's still open is System 1 alone (unchanged,
restated above) — a subgoal's own satisfaction condition, and the parent-quantifies-over-children shape,
are now both built and verified against the real engine rather than only designed.

**⭐ 2026-07-30: goal/subgoal turned out to be the shape everything else in this arc reduces to.**
`planning_meta_concepts_arc.md` (prose) tells the full story — planning, real side effects and
idempotency, closed/open-world stance, and the closed class itself being rechallenged — ending at
`units/meta_concept_unification_experiment.py`: a procedure is this shape plus one sequencing edge, a
question is this shape wanting a knowledge-claim instead of a world-state claim, and a standing
prohibition is an ordinary stance-fact veto, all checked together in one worked example, not just argued.

---

## 9. NAC guards: closed-world default, per-concept stance, and active verification — 2026-07-30

Raised in conversation, checked against the running engine before being written up: what should a
NAC-guarded rule (`absent(...)`) actually mean, and does it need to mean the same thing everywhere? The
old `ugm` engine (`ugm/check.py`, `ugm/policy.py`) had already worked this out once, as a four-status
model (`POSITIVE` / `ENTAILED_NEG` / `ASSUMED_NO` / `UNKNOWN`) with openness declared **per concept**,
never as a single global stance. This section is that distinction, rebuilt on `units/`'s actual
primitives rather than ported as Python config — and a working demonstration
(`units/nac_verification_experiment.py`, four checks green) that it needed no new engine mechanism, only
an authoring pattern.

### 9a. The three findings, in order

**1. "Per concept" has to be a fact, not Python policy.** Old `ugm`'s `FirmwarePolicy.open_preds` was a
frozenset passed at call time — exactly the "hardcoded stance, unreachable from the graph" shape
[[composability-principle]] rules out. Here, a concept's stance is an ordinary attribute on its own node
(`atom("hazmat", actively_verify=True)`, `units/nac_verification_experiment.py`), checked as an ordinary
positive premise by whatever rule needs it. No policy object, no new kind.

**2. A defeasible "assumed no" should be a *computation unit's* conclusion, never a mutating rule's.**
This is what makes it revisable for free, matching old `ugm`'s own framing of `ASSUMED_NO` as *"a
computed verdict, not a write."* A non-mutating `StandingUnit`'s output is never applied at write-back
(`engine.py:927`) — it's recomputed fresh from current gate content every `revive()`. Mint it via a
*mutating* rule instead and it becomes permanent data needing an explicit `Drop` the moment new evidence
contradicts it — exactly the kind of self-inflicted machinery this session already caught itself building
twice (§6, and `quantification_cursor_experiment.py`'s original same-turn gate).

**3. "Try hard before assuming no" does not need a new engine primitive — it needs the investigate rule's
positive premises to include the stance fact, nothing more.** The heavier mechanism raised in
conversation — a meta-rule that inspects another rule's `<absent>` node (already fully homoiconic data,
`units/engine.py:151-197`) and generates a companion rule from it — is real and buildable, but wasn't
needed for this. Simpler: author the investigate rule directly, with the stance fact as an ordinary
premise (`out=(role("kind", atom("k", actively_verify=True)))`) — it then only fires for flagged
concepts, the same way any other guard restricts a rule. "Configurable per concept" turns out to be
nothing more than which fact happens to be true of a given node.

### 9b. The shape, verified (`units/nac_verification_experiment.py`)

| concept's stance | rule shape | what it concludes | when |
|---|---|---|---|
| default (no stance fact) | bare NAC (`absent(dangerous=True)`) | `assumed_safe` | immediately, first revive — cheap CWA |
| `actively_verify=True` | investigate rule (stance fact as a positive premise) raises a subgoal wanting the real answer; **no** assumed-anything rule ever matches this concept | `confirmed_safe` / `confirmed_dangerous`, from the subgoal's own `achieved`/`diverged` (`goal_machinery.md` §2's shape, reused verbatim) | only once the subgoal genuinely resolves — real evidence, never a guess |

The flagged concept has **no defeasible middle state**: before the subgoal resolves it is honestly
pending (all three of `assumed_safe`/`confirmed_safe`/`confirmed_dangerous` stay `None`, checked
explicitly — `check_flagged_concept_never_assumes_before_investigating`), never a silent fallback to CWA.

### 9c. What was raised but not built, and why

**A safety veto for an already-concluded `assumed_no`** (a flagged concept's own rule producing a
conflicting conclusion, surfaced through the engine's *existing* `detect_conflicts()`/`report()`
machinery, `engine.py:837-901`, rather than a bespoke "trigger on assuming no" primitive) was proposed as
the general mechanism for overriding a prior assumption. Not needed for this worked example, because
finding 2+3 together made it moot here: a flagged concept never produces `assumed_no` in the first place,
so there is nothing to veto after the fact. Worth building as its own worked example if a case ever needs
*retracting* an already-trusted assumption rather than pre-empting it.

**A generic "read any rule's `<absent>` and generate its investigate companion"** meta-rule was the
originally-proposed heavier mechanism. Confirmed buildable (`Absent` is homoiconic, precedent exists in
`test_a_rule_writes_a_whole_rule_with_nothing_authored_in_python`) but not built — §9a finding 3 found the
direct-authoring version sufficient for every case tried so far. Worth revisiting only if hand-authoring
an investigate companion for every flagged concept becomes real, repeated cost — not before.
