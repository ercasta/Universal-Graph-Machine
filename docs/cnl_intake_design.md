# CNL intake + focus working-set + streaming — design

> **Status: DESIGN (2026-07-12, ratified with the user in conversation).** The spec for the first
> UGM *client*: an **agent loop with a TUI**. Not yet built. The active plan tracks the build in
> `implementation_plan.md` (Phase 8); this doc is the detail that phase points at.
>
> Read after: `architecture.md` (the generic→opinionated layering), `engine_user_guide.md` (today's
> boundary API), `docs/critique.md` (the risks this design answers — §4.1a session accretion, §4.4
> habitability, §3.3 conflict-lint). Related memory: `cnl-intake-focus-design`,
> `ugm-scope-session-sized`, `agent-not-theorem-prover`.

## 0. The goal, and the boundary

The first client is an **agent loop driven by CNL**, with a **TUI** for a human. The system boundary is
**CNL**: an external SLM maps user natural language → CNL, and everything downstream is CNL over the
substrate. Nothing in this design touches the SLM.

The load-bearing property is **seamlessness**: *a CNL utterance's own structure drives the loop, with no
intent-recognition dispatcher between the utterance and the substrate.* This is the differentiator over
brittle chatbot wizards, and it is structural, not cosmetic:

- **Compositional** — novel combinations of known forms work with no new handler.
- **Transparent / auditable** — the "intent" is the literal CNL sitting in the graph, editable and
  explainable, not a latent softmax over an enum.
- **One substrate** holds the utterance, the reasoning, *and* the explanation — so "explain why X" is not
  an EXPLAIN handler; it is CNL whose `why …` form fires and renders a trace faithful by construction.

## 1. The one seam, and the fix

Today the engine *almost* delivers seamlessness. Assertions and goals already land in the live substrate
by recognition (`cnl/forms.py` has a `goal X is a Y` → `<goal>` intake form; facts land as facts). But
**questions do not**: `cnl/query.py` parses a question in a *throwaway* graph, matches it against the KB
by name, and never lands it. That asymmetry forces a **caller-side question-vs-assert fork** — and that
fork, wherever it lives, *is* the residual intent-recognizer the seamlessness claim says must not exist.

**Fix: one unified intake.** A CNL utterance is tokenized into the *live* substrate (control-flagged),
normalized, and recognized; the fired forms decide what happens. No caller branch.

```
CNL utterance
  1. tokenize into the LIVE substrate, control-flagged      → <sentence> anchor + token chain
  2. normalize_surface                                      → determiners, multi-word NPs,
                                                               pronoun/anaphora vs. retained centers
  3. recognize (forms fire) → route by what fired:
       fact form        → promote content into the FACT layer (monotone, persists)
       rule form        → add a reified rule (runtime authoring, §6)
       <query> form      → land a <query> CONTROL node; raise its demand (§2)
       <goal>/command   → seed a trigger; the slice-4 plan→act→check loop services it
       nothing fires    → the uniform rejection outcome: "didn't understand X; nearest forms are …" (§4a)
  4. run to quiescence (fuel-bounded); tool <call>s + ask_user interleave, STREAMING (§5)
  5. collect outcomes → render (answers, tool calls, why on request)
  6. GC spent scaffolding, reachability from the focus roots (§3)
```

Steps 1–2 exist (`tokenize`, `normalize_surface`). Step 3's fact/rule/goal routes largely exist. The two
genuinely new things are **`<query>` as a live control node** (§2) and the **focus + GC** of step 6 (§3).

## 2. `<query>` as a live control node

A question stops being a throwaway-graph computation and becomes a **control-flagged node in the live
KB**. Recognition (the `QUESTION_FORMS` of `query.py`) fires in-place and mints `<query>`/`<qevent>`;
answering raises the demand (`chain_sip`/`check`) directly over the live graph.

**Monotonicity is preserved** by the existing control/fact layer split (`control=True`): a `<query>` is
control-layer — visible to recognition, drives the loop, GC-able (§3) — and *never* writes the monotone
fact layer. The old "throwaway graph so asking never mutates the KB" guarantee is kept at the layer that
matters (§5), while asking, asserting, and commanding become **one motion**: land in the substrate,
recognition decides.

The demand answering itself is unchanged (`check` → 4-status verdict; `collapse` → yes/no/unknown; the
CWA/OWA stance from `FirmwarePolicy`). What changes is *where* the `<query>` lives and that it participates
in the same loop as everything else.

## 3. The working set — a `<focus>` stack

An agent loop is a long, topical conversation. The working set (what is "in play") is **not** last-N-turns
(topics switch); it is a **focus**: pointer nodes into the graph marking what the conversation is about.
This is a discourse-focus model (Grosz & Sidner centering / focus stack is the closest prior art).

**Shape.** A `<focus>` **stack** in the control layer. Each frame is a `<focus>` node pointing at
**center** node(s) — the in-play entities.

**Pointer-at-center, extent DERIVED (not scope-as-subgraph).** A declared "scope subgraph" would need an
arbitrary in/out boundary, and that boundary is domain-dependent — so the engine cannot own it without
violating *no domain logic in the engine*. Instead the pointer names only the centers; the **extent of the
working set is derived** = the demand-closure the reasoner reaches from those centers. Same emergent
principle as recognition and demand-driven negation: attention extent is computed, never declared.

**Seed scope = the top frame's centers.** The next utterance's reasoning seeds from the current centers,
so **per-utterance cost tracks the closure from the centers, not total graph size**. This is the
performance mechanism for session accretion (critique §4.1a) — see §7.

**Implicit vs explicit.**
- *Implicit (default):* an ordinary utterance only **widens** the top frame — its mentioned entities
  accrue as centers. It never pushes a new frame. This deliberately sidesteps brittle implicit
  topic-switch detection (the exact thing wizards get wrong).
- *Explicit (a small control-CNL surface):* `focus on X` (push a frame), `forget that` (drop/pop),
  `back to X` (re-enter a retained frame), optionally `also consider Y` (widen). These reuse the SUPPOSE
  scope ops (open / drop_scope / re-enter). Small, closed, low SLM-surface debt.

A stray center from an unflagged topic switch is a *soft* degradation (a slightly larger closure), repaired
by `forget that`. It is recoverable **because focus is inspectable graph structure** — unlike a hidden
intent classifier's wrong guess, which is silent. Salience/decay is deferred; we resist a temporal
threshold in v1 for the same reason we rejected last-N-turns.

**GC.** Mark-and-sweep of cold *control* scaffolding from the focus roots: spent `<query>` nodes, resolved
frames, old token chains no focus reaches. **Facts are never collected** (monotone, §5); a cold fact simply
leaves the seed scope. So the graph still grows with facts, but the *working set* stays bounded.

## 4. Anaphora is reasoning, not a resolver

The top frame's centers are the referents. Resolution splits:

- **Descriptive anaphora** ("the cheaper one", "the alibied suspect") → **CHOOSE over the centers**: which
  center satisfies the description. No resolver — it folds into ordinary reasoning.
- **Bare pronouns** ("it", "that") → **CHOOSE over graded defeasible preferences**. The ranking is
  recency + grammatical role as **content-blind defaults**, **overridable by declared domain preference**
  (a legal domain may declare "the defendant" as the default referent). The ranking is *defeasible
  priority data*, not engine-baked.

**Where metareasoning enters — and where it does not.** The *ranking* is **not** metareasoning
(metareasoning = content-blind *effort/resource* policy: fuel, α-cut, radius; a preference over answers is
not effort). Metareasoning owns **only the ask-vs-guess margin** — the α-cut on the resolution: a clear
winner resolves silently; a near-tie **does not guess** but **asks** ("did you mean the knife or the
rope?"), escalating through the **same `ask_user` channel** as OWA evidence-gathering and the deontic
"better check." An ambiguous "it" produces a clarifying question through the existing path, not a special
anaphora dialogue. One mechanism (CHOOSE), one layer boundary.

### 4a. Habitability — the rejection outcome

When **no form fires**, that is the single, uniform "I didn't understand" signal (critique §4.4: the
frustration lands on the first sentence). The intake surfaces it as actionable: *what* was not understood
and the *nearest forms*. This is the named-rejection linter made central — and it costs nothing extra: it
is the empty-recognition case of the one intake path.

## 5. Streaming + suspend/resume

The TUI **streams** intermediate state (recognition, tool-call start/end, verdicts, `ask_user` pauses),
not one turn-synchronous render. This does **not** require rewriting the engine — the architecture makes it
cheap:

`run_bank` / `chain_sip` are already a **round-based fixpoint over graph-resident control state**
(`<demand>`, `<frame>`, `<current>`, `<query>`). **The graph is the continuation** — so suspend/resume
needs no threads and no async rewrite. Two additive pieces:

1. **An event sink at the existing step boundaries** — round-end, each `service_calls`, each EMIT. Reuse
   the RECORD/provenance substrate: `run_bank(provenance=True)` already mints a `<j:RULEKEY>` node with
   `proves`/`uses` at every firing. Streaming = surface these as they are minted, not only at the end. The
   trace renderer built for meta-debugging *is* the event stream.
2. **Generalize the blocking `ask_user` into suspend → return → resume.** Today it is a synchronous
   callback inside `ask_goal` that freezes the loop. Instead: when the chain needs an open-predicate fact
   it cannot derive, leave the pending question as a graph node, **return** control to the TUI, and
   **resume** by materializing the supplied answer and re-entering the loop. The demand frontier is
   graph-resident, so re-entry continues.

Streaming and a clean `ask_user` are the **same mechanism** — suspend-at-a-wait-point with graph state as
the continuation. (This is why a synchronous `ask_user` "gets complicated" without streaming.)

**Bounded caveats (not a rewrite):**
- The top-level driver needs a **resumable/event-emitting variant** — a wrapper around the round loop.
- Re-entry is **correct** (derived facts are graph-resident), but `run_bank`'s `fired` suppression set is
  *per-run in-memory*, so a naive re-entry re-does matching — a perf follow-on, not a correctness bug. The
  agent-loop path is the *demand-driven* `chain_sip`/`check`, which already prune-and-continues on re-entry
  (firmware v3), so the hit is small where it matters.
- **Wait-set for v1 = `{ask_user}`.** Tools run synchronously but emit start/end events (the TUI shows
  "calling…"). Truly async/long tools are a later refinement.
- **Empirical unknown to probe (§7):** that suspend/resume on `chain_sip` preserves the demand frontier
  without redoing the closure.

## 6. Runtime rule authoring (a global KB concern)

The user can supply a rule mid-conversation when the KB cannot decide ("messy real-world"). A
`HEAD when …` utterance lands through the **same intake** as a fact (reified via `cnl/rule_graph.write_rule`)
and reasons **immediately**. This is homoiconic — the repair-the-reasoner-in-conversation capability — and
it is **Phase 3.2**.

- **Incremental add.** A mid-session rule **extends** the head index (`apply.build_head_index` /
  `rules_producing`), it does not trigger a rebuild. The chain builds it lazily → invalidate/extend, cheap.
- **Re-lint stratification per add.** A new rule can introduce a negation cycle; `authoring.lint_stratifiable`
  (load-time today) runs **per add**, and the `FirmwarePolicy.on_cycle` stance (raise/degrade) decides the
  reaction.
- **Conflict-lint as conversation (the synergy).** A rule that breaks stratification or conflicts with an
  existing priority is **not silently dropped** — the agent **asks** ("that rule loops with *X* — which
  wins?"), routed through the same streaming/`ask_user` channel (§5). This is critique §3.3's wedge. Rule
  authoring + lint + streaming compose into "the reasoner negotiates its own repair."
- **Disable / repair.** "No, forget that rule" is a `<disabled>` marker (Phase 3.2), never a deletion
  (§5). It joins `forget that` in the small explicit control-CNL surface.
- **Scope: global.** Runtime rules are **global KB content**, not focus-scoped — a rule is a general truth,
  not a discourse referent. Focus governs which *entities* are in play, not which *rules*.

## 7. The performance premise, and the probe

The client's real perf risk is **not** total-KB size (Phase 7a interning is the wrong axis here, critique
§4.1a). It is **session accretion**: the graph grows monotonically with the transcript. The design's
answer is **seed-from-focus** (§3): per-utterance cost = the closure from the current centers, independent
of transcript length.

**First buildable step = a diagnostic probe** that measures **per-utterance latency across a growing
transcript** and confirms two things:
1. **Seed-from-focus keeps it flat** — latency tracks the focus closure, not the accumulated session.
2. **Suspend/resume on `chain_sip` preserves the demand frontier** — re-entry after an `ask_user`
   suspension continues the closure rather than redoing it.

Run the probe *before* building the full spine on top of the premise. If (1) fails, the focus seeding needs
tightening; if (2) fails, the demand frontier needs explicit persistence before streaming lands.

## 8. Build map — what exists vs. what is new

| Piece | Status | Where |
|---|---|---|
| tokenize + `normalize_surface` | exists | `cnl/forms.py` |
| fact / goal intake forms | exists | `cnl/forms.py` |
| question recognition (`QUESTION_FORMS`) | exists (throwaway graph) | `cnl/query.py` |
| demand answering (`check`/`collapse`/`chain_sip`) | exists | `check.py`, `chain.py` |
| reified rules (`write_rule`) + head index | exists | `cnl/rule_graph.py`, `apply.py` |
| plan→act→check loop | exists (slice 4) | `mode_calls.py` |
| RECORD/provenance trace (event substrate) | exists | `run_bank(provenance=True)`, `surface.explain` |
| **unified intake entry + routing** | **new** | (§1) |
| **`<query>` as live control node** | **new** | (§2) |
| **`<focus>` stack + centers + seed-from-focus** | **new** | (§3) |
| **explicit focus CNL** (`focus on`/`forget`/`back to`) | **new** | (§3) |
| **bare-pronoun ranking + ask-margin escalation** | **new** | (§4) |
| **scaffolding GC (reachability from focus)** | **new** | (§3) |
| **event-emitting + resumable driver** | **new** | (§5) |
| **suspend/resume `ask_user`** | **new** | (§5) |
| **incremental rule add + per-add re-lint + conflict-ask** | **partly new** (Phase 3.2) | (§6) |
| **accretion + suspend/resume probe** | **new (first step)** | (§7) |

## 9. Open / deferred

- Salience/decay of centers (deferred; no temporal threshold in v1).
- Implicit topic-switch *push* (v1 is widen-only; auto-push is a later heuristic, recoverable meanwhile).
- Async/long tools as suspension points (v1 wait-set = `{ask_user}`).
- Cross-bank join selectivity at the moment of combination (critique §4.1b) — check once 2+ real banks
  compose; bounded by the endpoint-driven seeding of perf-lever-(a), now focus-scoped.
