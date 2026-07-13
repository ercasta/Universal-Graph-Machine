# Implementation Plan — Universal Graph Machine (ACTIVE / remaining work)

> **Status: THE ACTIVE PLAN (2026-07-12, post done-split).** This is the UGM-only continuation of
> the original `harneskills` plan. Completed phases + landed milestones + settled rationale trails
> moved to `implementation_plan_done.md` (2026-07-12). This file is ONLY the remaining work.
> The harness (planning rule banks, SLM, session, TUI) has its own plan in `harneskills`.
>
> Module paths after split: `ugm.xxx` (was `harneskills.isa.xxx`); `ugm.cnl.xxx` (was
> `harneskills.xxx` for CNL-level modules). Tests: `ugm/tests/`. Source: `ugm/ugm/`.
>
> Read first: `reference.md` → `vision.md` → `logic_fragment.md` → `processing_modes.md`
> → `graph low level machine/isa-reference.md` → `architecture.md`. Log landed work in `CHANGELOG.md`.
>
> Standing rules: no commits by the assistant; domain logic ONLY in banks; strategies are
> DECLARED data, never engine sniffing; correctness before raw performance.
>
> **RATIFIED 2026-07-10 (user): EQUIVALENCE WITH THE PREVIOUS (rewriter / name-based) GENERATION IS NOT
> A CORRECTNESS TARGET.** The old generation was never used. The goal is a **WORKING, self-consistent
> firmware system**, judged on producing sensible answers on the benches, NOT on reproducing the old
> exhaustive engine's outputs. Impossible-blocker chance < 5%. Real long-pole for a *usable* system =
> **performance (Phase 7)**, not correctness.

## Current state

**Suite: 346 passed, 0 failed** (`python -m pytest -q`, ~50s; run via `.venv/Scripts/python.exe -m
pytest -q`). Production runtime is 100% the ISA engine, and so is every test — no second engine anywhere
in the repo. `ask_goal` is demand-driven; `rewriter.py`/`goal.py`/`walker.py`/`decide.py`/`solve.py` are
all deleted.

**▶ LANDED 2026-07-13 — pystrider-feedback pass** (`docs/feedback_from_pystrider.md`, tests in
`tests/test_feedback_fixes.py`). Four items closed, one deferred:
- **#2 minting.** Bare RHS-only head `?x` stays rejected (unsound: invisible forward, self-fulfilling on a
  ground demand). The SUPPORTED minting primitive is the LHS-keyed bound-literal skolem (`foo?` fact / `<foo>?`
  control), a skolem FUNCTION of the match. It BLEW UP on the demand chain (fresh node/round, fuel-capped);
  fixed by `chain._resolve_skolems`/`_find_skolem_witness` — re-find the skolem STRUCTURALLY by its defining
  relation to the LHS-bound anchors, so check-before-derive converges (idempotent, agrees with forward).
- **#8a** query-time name-split warning (`query._warn_name_split_join`).
- **#8b** solved the VISION-ALIGNED way: `intern_node` helper KILLED (a Python twin of `MINT(intern=True)`);
  fact authoring is now `lowering.assemble_facts`(triples)→`MINT` program→`Machine.run` (`load_fact_triples`).
  Interning is the instruction's. Principle ratified: capabilities/semantics are ISA programs, never substrate-
  poking helpers — see the vision-cleanup residual below.
- **#7** confirmed done (`suppose` has `focus_scope`).
- **#8c DEFERRED — id-addressed RETRIEVE surface.** `ask_goal`/`suppose` have `focus_scope`; `choose` is
  already id-addressed + doesn't reason; id-addressed GOALS already work via `chain_sip`+`ById` (collision-
  free). The remaining ergonomic — an id-addressable "who realizes X" — should be a **RETRIEVE `<call>` mode**
  (like CHECK/CHOOSE/SUPPOSE in `mode_calls.py`: a `<call>` with id-addressed slots, serviced by the dumb
  dispatcher, emitting answer bindings as nodes), NOT a `who()` Python helper. Not started.

**▶ RESUME HERE (2026-07-12):** the active track is **coreference-as-rules** (`docs/coreference_as_rules_
design.md`), the reshaped "D". Stages **1–4 DONE** (value-match primitive + CNL surface + **id-addressed
core** (Stage 3: demand-chain env binds node ids in FREE slots, so distinct same-named nodes bind to
distinct vars) + **Stage 4**: the FORWARD value-JOIN op `machine.VMATCH` (value-match rules now fire under
`run_bank`/`run_rules`, not just the demand chain) AND same-name coref as ONE declared rule over a universal
`is_a <mention>` marker (`forms.mark_mentions` + `universal.same_name_coref_rules()`), retiring mechanical
`wire_same_as` as the `load_corpus`/`load_facts` default — marking ("what is an entity") separated from the
coref DECISION (a CNL rule); position-agnostic, so untyped entities corefer). **NEXT = Stage 5** (boundary
migration + docs) and, optional, delete the retired `canonicalize` merge + rewrite its `test_new_core`
users. OPEN with the user: `load_corpus` auto-injects the universal coref rule (current, demos green) vs
silent-by-default. Key finding trail: the user chose declared-value-match-bank over an ingest naming policy,
which forced the forward VMATCH first; per-type coref then hit the untyped-entity wall (subject-vs-object
position → no shared type), resolved by the universal marker. S-P-O is just a directed 2-hop path (no
role semantics baked in — direction carries it); role-labeled edges were REJECTED by the user.

**Consumer-feedback hardening DONE 2026-07-12** (`docs/feedback_from_pystrider.md`, `tests/test_feedback_fixes.py`):
the recurring theme was SILENT failures — SEVEN made LOUD or fixed: #1 machine-rule non-triple clause raises;
#2 skolem/RHS-only head var rejected at load (option A; genuine minting = STILL DEFERRED, the one remaining
pystrider item); #3 CNL case-fold false-negative warns; #4 `apply_*` clear error on a `Rule` vs node-id;
#5 `load_facts(strict=True)`; #6 read-only `suppose(commit=False)` returns in-scope derivations (2026-07-12);
#7 `suppose(focus_scope=…)`. Session API also promoted to top-level exports (`ingest`/`converse`/…). The
name-vs-id addressing item (C→D) is now RESOLVED (coreference-as-rules, all stages done).

Phases 0–2, 3.1-step1, 3.3, 4, 5, 6.0/6.1, firmware v3 (demand-driven negation), stance-as-data, and
perf lever (a) are **DONE** — see `implementation_plan_done.md` and `CHANGELOG.md`. **Do NOT re-do them;
do NOT resurrect `decide.solve`, `solve.py`, or the demand/coref/walk/asp leftovers.**

**Phase 8 (CLIENT: agent loop + TUI) IN PROGRESS — the active track.** DONE: NAC endpoint-driven perf fix
(40×); 8.1 unified intake (`ugm/intake.py`); 8.3a `<focus>` stack + widen + explicit focus-CNL + scaffolding
GC (`ugm/focus.py`); 8.3b seed-from-focus BOUNDED ATTENTION (`ingest(attention=…)`/`ask_goal(focus_scope=…)`,
probe-validated: bound query flat under focus vs a 0.5s→112s global cliff); 8.5a live event stream
(`ingest(on_event=…)`, ask-bracketed); 8.5b non-blocking generator driver `converse` (threadless
suspend/resume of the ask via `_ingest_gen` core + exception-unwind/re-enter); 8.6 conflict-lint AS
CONVERSATION (a mid-session rule that loops with the theory is asked about via the ask channel, not
raised); 8.6 DISABLE (`forget that rule` marks the last rule `<disabled>` — additive, no deletion §5);
8.5b TRACE (`trace=True` streams an `Event("derive", …)` per rule firing, read from the provenance
substrate); 8.5b MID-CHAIN ask (gather the OPEN premises a derivation demands, not just the top goal —
closes a silent-wrong-`no` hole). **8.5b and 8.6 are functionally COMPLETE.** ANAPHORA resolution was tried (8.4a) and BACKED OUT — it is a boundary
concern the SLM owns via the exposed `focus.top_centers` (2026-07-12; see §4). New modules:
`ugm/intake.py`, `ugm/focus.py`, `ugm/rule_control.py`; new tests:
`test_isa_intake`/`_focus`/`_stream`; `bench/session_accretion.py`. Spec: `docs/cnl_intake_design.md`
(+ §D anti-hardcoding discipline). REMAINING: 8.5b tail (true wall-clock trace interleaving; extend
mid-chain gather to who/∃/n-ary + lazy asking), 8.6 incremental head-index (perf follow-on) — see Phase 8
below.

## NEXT STEP — id-addressed goal API (~~C now~~ → **D reshaped: coreference-as-rules**) — name-vs-id addressing

> **⚠ D WAS RESHAPED 2026-07-12 (user) → see `docs/coreference_as_rules_design.md`.** D's original
> "mechanical same-name binding at ingest" was rejected: it bakes an NLP judgment into the engine. New
> direction — **every mention stays a separate node; coreference becomes DECLARED rules**, enabled by a new
> value-equality / graded-closeness match primitive (`ValueMatch`). Approved sequence **1→2→3→4→5**:
> (1) the primitive ✅ DONE; (2) coref-as-rules (CNL form `?x same/close DIM as ?y` + declared-bank demo)
> ✅ DONE; (3) id-addressed core (env binds ids in FREE slots — `_facts_matching` returns `ById`) ✅ DONE;
> (4) same-name coref as a declared rule + retire mechanical `wire_same_as` as the default ✅ DONE (forward
> `VMATCH` op + universal `is_a <mention>` marker; `canonicalize` deletion is optional follow-up);
> (5) boundary migration + docs **NEXT**. The C→D name-vs-id analysis below is SUBSUMED: id-addressing is
> Stage 3, and the same-named-collapse it works around is exactly why Stage 3 was needed. **Stages 1–4 DONE**
> (`ValueMatch` + CNL surface + id-core + forward value-JOIN + declared same-name coref;
> `tests/test_isa_value_match.py`, `tests/test_isa_idcore.py`; 340 suite green).

> **C DONE 2026-07-12** (`chain.ById`, `tests/test_isa_byid.py`, 11 tests, 325 suite green; CHANGELOG +
> `engine_user_guide.md` §2). The tuple-goal APIs (`chain_sip`/`check`/`suppose`) now accept a
> `ById(node_id)` endpoint that PINS the demand seed + the EMIT/pencil write to that node (additive; the
> name path untouched); a stale pin raises (`validate_ids`); a name resolving to >1 GENUINELY DISTINCT
> entity warns before the `[0]`-pick (coref-aware via `_one_identity`, scaffolding-aware via
> `_is_fact_entity`). New helpers `resolve_write_node` (single write-target site) / `_candidate_nodes` /
> `_endpoint_matches`. The three write points (`chain._node_for_name`, `suppose._resolve`,
> `query._materialize_fact`) all route through `resolve_write_node`. **D is now the active next step.**

> **The immediate next step (ratified with the user 2026-07-12).** From the pystrider offline feedback:
> the firmware's tuple-goal APIs (`chain_sip`/`check`/`ask_goal`/`suppose`) address entities by NAME and,
> on a duplicate name, the WRITE/seed side silently takes `nodes_named(...)[0]` — so a consumer with
> legitimately DISTINCT same-named nodes (created directly, not via CNL) can't hand the firmware a node id
> and is forced into global name-uniqueness. **This is NOT a nameless-substrate regression:** the MATCHER
> (`chain._facts_matching`) already uses name as a value-ACCELERATOR (iterates ALL same-named candidate
> nodes, reasons by topology — "never identity, the label-less discipline holds"). The `[0]`-pick is
> confined to THREE write/seed points: `chain._node_for_name` (EMIT), `query._materialize_fact`
> (ask-user gather + top-goal materialize), `suppose._resolve` (pencil assumptions).

**C — id-addressed goal path — ✅ DONE 2026-07-12.** The tuple-goal APIs accept a `ById(node_id)` endpoint
(an id-or-name endpoint, not a separate `_by_id` variant), seeding the demand from that specific node and
using it directly at the write/seed points instead of `nodes_named(...)[0]`. The matcher walks FROM the
pinned node (`_candidate_nodes`); the name-based path is UNTOUCHED (CNL consumers unaffected). Silent→loud
(same theme): a stale pin RAISES (`validate_ids`), and the three write points WARN when a name resolves to
>1 GENUINELY DISTINCT entity before taking `[0]` (coref/scaffolding excluded so the value-accelerator's
normal multi-mention state stays quiet). Delivered: a consumer keeps readable duplicate names and manages
identity itself via ids. Shipped with `tests/test_isa_byid.py` (11) + a user-guide note (§2).

**D — id-addressed CORE, names resolved at the CNL boundary (the "real" solution; do AFTER C).** Migrate
the CNL entry points (`ask_goal`/`check`/`suppose`/`choose`) to resolve names→ids at their surface and sit
on top of the id primitives from C, so the reasoning core becomes purely id/structural — the nameless-core
purity the vision wants (name-resolution becomes a boundary concern, not a core one). **C is a strict
prerequisite and contains no wasted work; D = C + this migration + a deprecation of the name-first core
path.** ⚠Opus.

**Design key — SPLIT what "coreference" currently lumps together (ratified with the user 2026-07-12).** The
matcher's "iterate-ALL-same-named" is NOT one primitive; it conflates two concerns, and separating them is
what makes D clean rather than a core crux:
- **(1) automatic same-NAME linking** (`wire_same_as` on identical surface tokens: "ada" in one sentence =
  "ada" in another) is a NAMING CONVENTION, structurally the SAME boundary concern as ANAPHORA (§4, which we
  kicked to the SLM). It RELOCATES to ingest: bind a mention's name to the existing node id at load time (a
  deterministic policy — no SLM needed, unlike anaphora; a direct-API consumer like pystrider supplies the
  id itself). Do this and facts land on ONE node, composition is automatic, and the "iterate-all-same-named"
  dance DISAPPEARS from the core.
- **(2) asserted / derived identity** (`X same_as Y` declared or reasoned — "the morning star is the evening
  star") is GENUINE COMPUTATION — an identity FACT reasoning follows — and STAYS in the core. It is NOT
  anaphora-like (reasoning is not byte-identical: learning `X same_as Y` changes what composes).
- **Why ugm went additive-`same_as` originally:** identity can be REVEALED LATER (mention "ada", then later
  assert "ada is the detective") — you can't bind that at ingest, hence the additive link. That wrinkle IS
  the (1)/(2) line: name-known-at-ingest → bind to id at the boundary; identity-asserted-later → a core
  `same_as` fact.

So D is: **core id-addressed, knowing only asserted `same_as` (2); same-name binding becomes an ingest-side
naming policy (1)** — the anaphora principle applied to identity. There is NO "resolve to a coreferent
node-SET" crux in the core; that requirement was an artifact of NOT doing (1) at ingest. Model routing:
**C ✓S with tests; D ⚠Opus** (control/identity/coref semantics + the ingest same-name-binding policy).

## Residuals carried out of done sections (don't lose these)

These were TODOs embedded in now-done phases; they live in the open work below:
- **`same_as propagates through X` CNL surface** (from Phase 3.1-step1) — needs coref rules reified;
  `coref_prop` is forward-compatible. Lands with Phase 3 rules-as-data. Also the mechanism half of the
  Phase 5.4 residual below.
- **APPLY-body graded α-cut + inverted ('not at all') cut** (from Phase 5.2 companion) — the CHAIN half
  is DONE (firmware v3 `chain._graded_ok`); the APPLY-body match-time cut remains. ⚠Opus.
- **`session.py:CONTENT_PREDS` + Python-generated coref rules** (from Phase 5.4 residual) — harness-side;
  resolves once coref rules reify (bank-authored `same_as propagates through X`).
- RETIRED / not carried: Phase 5.1's "aggressive `is_not` completion" (replaced by demand-driven NAF);
  Phase 2.2's "Phase-6 reader flip" (landed in Phase 6.0).
- **VISION-CLEANUP: get-or-create plumbing should EMIT `MINT`, not poke the substrate** (2026-07-13, from the
  feedback #8b pass). The principle (ratified with the user): the machine is a MACHINE — every *semantic*
  (interning, dedup, reasoning) is an ISA instruction/program run by the one interpreter; the raw storage API
  (`add_node`/`add_relation`) is the dumb loader/RAM and must never host a semantic that is already an
  instruction. `MINT(intern=True)` IS interning; the public `intern_node` twin was therefore KILLED, and
  fact-authoring now goes through `lowering.assemble_facts` (facts → a `MINT` program → `Machine.run`). Left
  to clean up (tagged `TODO(vision-cleanup)` in-source): the internal get-or-create plumbing that still pokes
  the substrate directly — `dispatch._ensure`, `mode_calls._ensure`, `focus._entity_node` (and the general
  question of whether firmware minting scaffolding — `_control_rel`, verdict nodes — should emit `MINT` too).
  These are the machine's own plumbing minting *control* nodes, so lower priority than a public API twin, but
  the same principle applies: a mode/tool should lay down instructions, not call substrate methods. ✓S per
  site (mechanical), ⚠Opus for the "does all firmware minting become emitted `MINT`" scope call.

## Phase 8 — CLIENT: unified CNL intake + focus + streaming (ACTIVE — the current build)

> **This is now the primary track (2026-07-12, ratified with the user).** The first UGM *client* is an
> **agent loop with a TUI**, driven by CNL (the NL→CNL SLM is external; the system boundary is CNL). The
> load-bearing goal is **seamlessness** — a CNL utterance's own structure drives the loop with NO
> intent-recognition dispatcher. Full spec: **`docs/cnl_intake_design.md`**. This reroutes the plan onto
> the client build; the old NEXT STEP items become secondary/parallel tracks below. **Phase 3.2 (runtime
> rule edits) is ABSORBED here** (§8.6). The perf priority shifts from Phase 7a (total-KB size, wrong
> axis for this client) to **session accretion** (`docs/critique.md` §4.1a), answered by seed-from-focus.

**INTAKE-SPINE DISCIPLINE (anti-hardcoding — any session on Phase 8 MUST obey; reviewers reject diffs that
break one).** The spine is where the seamlessness claim is easiest to betray with a Python shortcut. Full
list: `docs/cnl_intake_design.md` §D. In brief: (1) route by which FORMS fired, never by sniffing the
utterance string; (2) focus moves (`focus on`/`forget that`/`back to`) are CNL forms, not `if "forget" in
text`; (3) pronoun ranking is DECLARED defeasible-priority data (content-blind defaults, domain-overridable),
not engine-baked; (4) rejection/"nearest forms" computed from recognition structure, not a hardcoded table;
(5) `<focus>`/`<query>`/`<goal>` are control tokens via the `<…>`→control chokepoint; (6) no predicate/
English-word STRINGS as control signals in intake code (vocab from `ugm/vocabulary.py`, domain preds from
the KB); (7) metareasoning owns only effort/margins, not answers. Litmus: grep intake code for a domain or
function word used as a control signal — if one is load-bearing, it belongs in a bank, not the engine.

Build slices, in dependency order (each with tests; the probe first to validate the premise):

- **8.0 — accretion + suspend/resume PROBE (first, diagnostic). PARTLY DONE 2026-07-12.**
  `bench/session_accretion.py` written. KEY FINDING (changed the picture): the near-term blocker is NOT
  accretion but PER-UTTERANCE NAF cost — a *bound* query on a bank with one `not …` rule was super-linear
  in the bank's entity count (`is s0 thief` over 6 suspects = 13.8s). Root cause: the NAC existence check
  `apply._find_fact_relnode` did a whole-predicate scan (lever-(a) never applied there). **FIXED** →
  endpoint-driven, 40× (m=6 13.8s→0.34s), suite 258 green + 54s→35s (CHANGELOG 2026-07-12). RESIDUAL
  super-linearity (m=12=5.5s) = levers (b) agenda re-servicing + (c) coref `same_as` fan-out; the profile
  is now flat. Seed-from-focus (8.3) bounds the coref fan-out by scoping — so the residual is addressed by
  the spine build, not a separate perf push. STILL TODO in 8.0: re-run the probe AFTER 8.3 to confirm
  focus-scoping isolates+flattens accretion, and that suspend/resume on `chain_sip` preserves the frontier.
- **8.1 — unified intake entry + routing. FIRST INCREMENT DONE 2026-07-12.** `ugm/intake.py`
  `ingest(kb, rules, utterance) -> Outcome`: routes fact / rule / question / unrecognized by which FORMS
  fire (not a string sniff), reusing `recognize`/`ask_goal`/`load_rules`/`load_facts`/`expand_rules`.
  Rule route appends + re-lints so a mid-session rule reasons immediately (Phase 8.6 seed). Gibberish/empty
  → the habitability rejection outcome (§4a). `tests/test_isa_intake.py` (6 tests, 264 suite green).
  STAGING: the caller-side fork is closed at the ENTRY; the QUESTION *parse* still runs off-graph
  (`recognize` throwaway) — collapsing it into a live control-flagged `<query>` node is 8.2. GOAL/command
  route + focus control-CNL are 8.3. Design §1, §D discipline obeyed (content-blind, no string sniff).
- **8.2 — `<query>`/`<goal>` as live control nodes. FOLDED INTO 8.3** (2026-07-12): a standalone 8.2 has
  no clean form — recognizing a question over the live graph via `run_bank` isn't scoped (it tags fact
  tokens' `is_kw`), and the live `<query>`'s only consumer (retention/GC) IS focus. So the transplant
  (recognize in a scratch scope → mint a control-flagged `<query>`/`<goal>` in the live KB) lands in 8.3,
  where focus-GC gives it a real lifecycle. Groundwork done: `tokenize(..., control=True)` (Phase 8.2).
- **8.3 — `<focus>` stack + centers + `<query>`/`<goal>` landing + seed-from-focus.** Pointer-at-center
  (extent DERIVED, not scope-as-subgraph); seed scope = top frame's centers; implicit widen-only + explicit
  `focus on`/`forget that`/`back to` (reuse SUPPOSE scope ops); `<query>`/`<goal>` land as control nodes
  retained/GC'd by focus reachability. Design §2, §3.
  - **8.3a DONE 2026-07-12** — `ugm/focus.py`: `<focus>` stack (top = frame nothing is stacked below-of),
    `push`/`widen`/`drop`/`reenter`/`top_centers`; implicit widen-only on assert (content-blind
    `utterance_subjects`); explicit `FOCUS_FORMS` (`focus on`/`forget that`/`back to`) recognized as forms,
    wired into `ingest` (route "focus"); drop/reenter are control-layer ops (§5-safe). Answer-neutral.
    `tests/test_isa_focus.py` (9), 273 suite green.
  - **8.3a remainder DONE 2026-07-12** — QUESTIONS widen focus too (`_question_entities`: bound subject/
    object, skipping who/someone unknowns); spent token-chain scaffolding GC'd per utterance
    (`focus.gc_utterance_scaffolding` — surgical to the utterance's own `<sentence>` chain, answer-neutral:
    facts live on entity nodes, grammar tokens swept). `tests/test_isa_focus.py` now 13, 276 suite green.
    DEFERRED to 8.5 (streaming): a PERSISTENT `<query>`/`<goal>` control node (needs the streaming consumer
    + focus-reachability GC of it, vs today's per-utterance chain sweep).
  - **8.3b DONE 2026-07-12** — seed-from-focus as BOUNDED ATTENTION, EXPOSED + caller-selected (user
    directive: "code using the system decides which mode"). `focus_scope: frozenset[str] | None` threaded
    through `chain_sip`/`_solve_demand_rule`/`_nac_blocks`/`_facts_matching` (the reader filters: a fact is
    visible iff an endpoint is in scope) + `check` + `ask_goal`; `ingest(attention="global"|"focus")` maps
    "focus" → the top frame's centers (widen-before-answer so a bound question's subject is in scope).
    Default None/"global" = whole-graph, behaviour-identical (278 suite green). Focus holds INDIVIDUALS not
    types (`_question_entities` excludes the copula object — a shared type would be a stopword-anchor).
    PROBE (`focus_probe`, bound `is s<k>_0 thief` as independent cases accrete): global 0.5s→5.5s→31s→112s
    (super-linear cliff); focus 23→29→65→83ms (FLAT); ratio 23×→1361× and climbing. Bounded attention makes
    per-utterance cost track the focus, not the session — the accretion fix, validated. `tests/test_isa_focus.py`
    (16). SEMANTIC: off-focus facts leave attention (agent-not-theorem-prover); that is the point.
- **8.4 — anaphora: OFF THE ROADMAP (boundary concern).** Ratified 2026-07-12: anaphora resolution is NL
  pragmatics the external SLM owns on the NL→CNL side, using the substrate's EXPOSED discourse state
  (`focus.top_centers`); the substrate reasons over already-resolved CNL and never sees a pronoun. A landed
  8.4a (in-substrate bare-pronoun resolution via a recency-ranked `salient_center` + `clarify` escalation)
  was BACKED OUT — it bought nothing structural (reasoning is byte-identical for "she" vs "ada"); the test
  is "does a feature buy anything besides nicer language?" (focus/streaming/dispatch pass; anaphora fails).
  8.4b (descriptive anaphora + substrate ask-margin) is dropped for the same reason. Design §4; a bonus
  from the back-out: `focus.utterance_subjects` now skips coref `same_as` edges so a TYPE can't leak into
  the centers as a stopword-anchor. 283 suite green.
- **8.5 — event-emitting + resumable driver; suspend/resume `ask_user`.** Design §5.
  - **8.5a DONE 2026-07-12** — LIVE EVENT STREAM: `ingest(on_event=…)` emits `Event(kind, data)` at the
    route boundaries (focus / clarify / question / **ask** / answer / fact / rule / unrecognized), so a TUI
    renders a turn as it happens. The `"ask"` event brackets the human-in-the-loop `ask_user` gather (the
    §4 ask-vs-guess escalation). Additive: `on_event=None` (default) = no-op, behaviour-identical (287
    suite green). `tests/test_isa_stream.py` (4): `question→answer`, `question→ask→answer` (the gather),
    fact/focus/clarify. Works for a BLOCKING TUI (`ask_user` is a top-level suspension point already).
  - **8.5b DRIVER DONE 2026-07-12** — generator-based `converse(kb, rules, utt)` for a NON-BLOCKING UI:
    the caller pumps it (`gen.send(...)`), it yields an `Event` per step boundary and `.send()`s take the
    ask verdict. Threadless suspend/resume — the ask wait-point RAISES `_NeedVerdict` (an internal
    suspension that unwinds the chain cleanly, graph state persisting monotone), the driver yields
    `Event("ask")`, and RESUME re-enters `ask_goal` with the verdict as a one-shot handler ("the graph is
    the continuation" — the demand chain prunes-and-continues; the re-entry `check` is the accepted §5 perf
    follow-on). Refactor: ONE routing core `_ingest_gen` (generator), TWO drivers — `ingest` (blocking,
    8.5a, byte-identical) and `converse` (non-blocking). `tests/test_isa_stream.py` (+3: question→answer,
    suspend-at-ask→send-True→materialize→re-ask-needs-no-gather, verdict no/unknown). 286 suite green.
  - **8.5b TRACE DONE 2026-07-12** — PER-EMIT reasoning-trace streaming: `ingest`/`converse(trace=True)`
    runs the demand chain with `provenance=True` and yields an `Event("derive", {rule, fact})` per rule
    firing before the answer. Reads the in-graph proves/uses support the chain mints (`provenance.py`) by
    snapshotting `<j:>` justification nodes before/after the closure (`_derivations_since`) — an OBSERVER of
    the RECORD substrate, NOT a control-flow hook, so it never perturbs reasoning (the meta-debug trace
    renderer IS the event stream, §5). `ask_goal` gained a `provenance` param threaded to its check/chain_sip
    calls. Additive: `trace=False` default = behaviour-identical (296 suite green). `tests/test_isa_stream.py`
    (+3: blocking trace order / trace-off neutral / converse trace). BUFFERED per turn (the derivations are
    yielded after the closure returns, ordered but not wall-clock-interleaved).
  - **8.5b MID-CHAIN ASK DONE 2026-07-12** — the ask now fires for OPEN PREMISES a derivation demands, not
    just the top goal, closing a SILENT-WRONG-answer hole: a rule blocked only by a gatherable open premise
    (`safe when cleared`, `cleared` open) used to return a confident ASSUMED_NO without ever asking; now
    `ask_goal.gather_open_premises` asks the premise, materializes it, and the rule fires. WHICH premises
    is DERIVED, not hardcoded (§D): the candidates are the visible bound `<demand>` magic-set the backward
    closure itself produced (`chain.bound_demands`), filtered by the FIRMWARE openness STANCE
    (`policy.is_open`) and skipping NAF neg-predicate demands via the substrate convention
    (`vocabulary.is_neg_pred`, added) — no predicate/word list in Python decides it. MULTIPLE distinct asks
    per turn work through a MEMOIZING handler in `_answer_with_ask` (raise `_NeedVerdict` on each new tuple
    → yield → record verdict → re-enter `ask_goal`; converges monotonically — the graph is the
    continuation). Only fires when the goal wasn't already derivable (a derivable goal pays no extra
    closure) and never asks the negative/goal tuples. `tests/test_isa_stream.py` (+5: premise→derive /
    denied→no / already-derivable→no-ask / two-premise gather / converse per-premise suspend). 301 suite
    green. REMAINING in 8.5b: TRUE wall-clock trace interleaving (a live `_record` callback needs coroutine
    reasoning — the generator can't yield from inside the synchronous chain; deferred) + extending
    mid-chain gather to who/∃/n-ary questions (v1 covers the yes/no-bound path, the common case) and lazy
    (relevance-ordered) instead of eager frontier asking.
- **8.6 — runtime rule authoring (Phase 3.2, global KB concern).** `HEAD when …` lands via the same
  intake, reifies, reasons immediately; incremental head-index extend; RE-LINT stratification per add
  (`on_cycle` stance); conflict-lint AS CONVERSATION (a contradictory rule is rejected by ASKING, via the
  8.5 channel); disable = `<disabled>` marker (no deletion §5). Design §6.
  - **8.6 CONFLICT-AS-CONVERSATION DONE 2026-07-12** — a mid-session `HEAD when …` that forms a NEGATION
    CYCLE with the live theory is now a CONVERSATION, not a raise: intake parses with `load_rules(lint=
    False)` (runtime authoring OWNS the lint), tests a TRIAL `rules + new` via `_stratify_conflict`
    (content-blind `authoring.stratify`), and on a cycle YIELDS `Event("rule-conflict", {detail})` through
    the §5 ask channel. A falsey verdict REJECTS (discarded — the trial list means `rules` never mutated on
    reject, fixing the old extend-before-lint bug); a truthy verdict ACCEPTS (committed; `run_rules`
    degrades the NAF rules). Blocking `ingest` gets `on_conflict(detail)->bool`, defaulting to a SAFE
    REJECT when unwired (never silently admit a cycle, never crash); `converse` yields the event for the
    caller to `.send()`. Per-add re-lint now rides this same check (the old `lint_stratifiable` raise in
    the rule route is gone). `tests/test_isa_intake.py` (+3: reject-by-default / accept-on-verdict /
    clean-rule-no-ask) + `tests/test_isa_stream.py` (+1: converse reject+accept). 290 suite green.
  - **8.6 DISABLE DONE 2026-07-12** — `forget that rule` / `disable that rule` marks the LAST-AUTHORED rule
    `<disabled>` — an additive control-layer marker, NEVER a deletion (§5). New module `ugm/rule_control.py`
    (mirrors `focus.py`): `<disabled>`/`<last-rule>` control hubs pointing at nodes named by rule key;
    `RULE_FORMS` recognized as a FORM (§D.2, not string-sniffed), checked BEFORE the focus forms since
    `forget that rule` is a MORE SPECIFIC form than the focus `forget that` (trailing `rule` token
    disambiguates — grammar precedence). `active_rules(kb, rules)` = the theory minus disabled, used at
    BOTH question-answering and the conflict trial (a disabled rule neither fires nor cycles). "that rule"
    = the last add (the discourse referent, parallel to focus's `forget that`). SEMANTIC (surfaced by the
    test): disable stops FUTURE derivations; a conclusion already MATERIALIZED by an earlier query persists
    (monotone, §5 no retraction). `tests/test_isa_intake.py` (+3: disable-a-fresh-subject / not-focus-drop /
    no-op-when-nothing-authored). 293 suite green. REMAINING in 8.6: INCREMENTAL head-index extend only
    (today `_reify_rules` rebuilds per `ask_goal`, so a new/disabled rule already takes effect immediately
    — this is a PERF follow-on, not a correctness gap). **8.6 is functionally COMPLETE.**

**Model routing for Phase 8:** ⚠Opus for 8.1/8.2/8.3/8.5 (control/fact segregation, discourse model,
driver resumability — vision judgment); ✓S for 8.0 (probe/benchmark) and mechanical parts of 8.4/8.6
under the design spec.

## Secondary / parallel tracks (was NEXT STEP; run alongside or after Phase 8)

1. **Phase 5 exit gate — bench-sensibility half (harness-side).** Run card-trader + coref + full
   ProofWriter-coverage in `harneskills`. The engine half is MET in-repo (audited 2026-07-11); this half
   is not verifiable from this repo. NOTE: Phase 2.5 de-hardcoded the domain coref predicate list — coref
   now composes over `relation_predicates(graph)` + declared relations/prepositions, NOT a fixed engine
   list. A bench relying on a domain predicate composing across coref should Just Work if the predicate is
   present as a relation (default-grammar `in`/`has`/`before` included); if one regresses, DECLARE the
   relation in the harness KB — do NOT re-add an engine string.

2. **Phase 6.2 remaining (docs converge).** Two items left after the architecture-half landed:
   (a) refresh `reference.md`'s doc-map — it still lists `architecture.md` as pre-rehost / "must be
   rewritten at Phase 6.2", which is now stale (the rewrite landed 2026-07-12); also add the three engine
   docs (`architecture.md`, `engine_developer_guide.md`, `engine_user_guide.md`) to the LIVE map;
   (b) confirm finished phases are summarized in `CHANGELOG.md` (it is well-maintained; this is a
   verification pass, not new writing). ✓S.

3. **Phase 7(a) — the stated long-pole.** Now that 2.3 settled the name/key/value model, intern keys/
   values to ints + CSR adjacency + bitsets on a CLEAN representation (no bridge). ✓S for mechanical rungs
   with benchmarks; ⚠Opus for design.

4. **Demand-driven-negation PERF follow-on levers (b)(c)** (Phase 7-adjacent — the query is already
   sub-second at session scale, so this is optimization not correctness):
   - (b) semi-naive worklist so a demand re-services only when a relevant fact appeared (the round loop
     still re-services the whole local agenda each round; the profile's top is now `relations_from`/
     `_read_atoms` re-reading static reified-rule structure per service).
   - (c) the domain coref `same_as.*.is` demand fan-out.
   ALSO: `why` provenance is order-sensitive (a fact pre-derived without provenance renders `(given)`) —
   design AS-BUILT §5.

5. **Phase 3 remaining (rules-as-data / homoiconicity — off the critical path).**
   - **3.1 step 2:** demonstrate/prove pattern nodes stay fact-INVISIBLE when a rule fragment is folded
     into a live fact graph (control flag = segregation) — the one-graph fold. ⚠Opus (control/fact
     segregation). HAZARD: ephemeral APPLY frames add incoming edges to fact nodes; previewed and
     controlled by GC-after-pass, but the full fold needs care.
   - **3.2:** runtime rule edits by user CNL — **ABSORBED into Phase 8.6** (the client needs it as a live
     capability: add = same path as facts; disable = additive `<disabled>` marker; no deletion §5).
   - **3.4:** collections as first-class KB structure: member `next`-chains + list-authoring CNL forms
     (the ITERATE substrate — `processing_modes.md` §1). ⚠Opus.
   - Exit gate: every bank rule round-trips CNL → rule subgraph → rendered CNL.
   - NOTE: the meta-circular FORM-rule authoring (the quote/eval wall) is DEFERRED as a homoiconicity-
     purity milestone off the critical path (scoping decision 2026-07-09).

## Placeholders / optional follow-ons (not concrete tasks)

- **Broader FirmwarePolicy stance surface.** The stance-as-data work landed the two knobs the audit named
  (`negation_default`, `on_cycle`). A broader surface is a PLACEHOLDER — no third opinion is pending.
  Candidates ONLY if a workload needs one: CHOOSE tie-break / always-provenance `why` / default α-cut.
- **Prose `suppose … predict …` sugar** folding to slice 3c's reified encoding (new surface → SLM debt;
  deferred like `to NAME`, pick up if the SLM ledger is being retrained).
- **`tests/test_joern_corpus.py`** — legitimately slow, live-Joern; candidate for a `slow` marker.

## Phase 7 — PERFORMANCE track (after correctness — user standing rule)

In leverage order:
- **(a)** Intern keys/values to ints, CSR adjacency, bitset candidate sets — see NEXT STEP item 3.
- **(b)** Rust (PyO3) inner loop for Machine + store; Python stays the shell.
- **(c)** Per-rule AOT codegen = partial evaluation of APPLY (Soufflé-style), differentially gated.
- **(d)** Two-tier execution for runtime-edited rules — fresh rules interpret, stable-hot rules compile in
  background, version-stamp invalidation on edit. JIT (Cranelift/copy-and-patch before LLVM) only if
  profiling demands it.

## Model routing

⚠Opus = needs vision-judgment; ✓S = Sonnet-safe where a gate/spec catches deviation.
- Phase 5 exit gate (classify divergences / bench sensibility): **⚠Opus**
- Phase 6.2 remaining (doc-map refresh + CHANGELOG verification): **✓S**
- Phase 7(a) (intern/CSR/bitset): **✓S** with benchmarks for mechanical rungs; **⚠Opus** for design + AOT
  codegen
- Perf levers (b)(c) + `why` provenance ordering: **✓S** with benchmarks / differential gate
- APPLY-body α-cut + inverted ('not at all') cut: **⚠Opus**
- Phase 3.1 step 2 (one-graph fold): **⚠Opus** (control/fact segregation). 3.2/3.4: **⚠Opus**

## Risks

- **Session accretion is the client's real perf risk** (`docs/critique.md` §4.1a), NOT total-KB size —
  the monotone graph grows with the transcript. Answered by seed-from-focus (Phase 8.3) and validated by
  the 8.0 probe. Phase 7a interning is the WRONG axis for the agent-loop client; deprioritized.
- **Habitability at the CNL boundary** (`docs/critique.md` §4.4) — an unrecognized utterance must be an
  actionable rejection ("didn't understand X; nearest forms"), not a dead end. Falls out of the unified
  intake (Phase 8.1/§4a) as the empty-recognition case.
- **Performance (Phase 7) is the long-pole for the GENERAL engine** post the no-equivalence ratification;
  for the client it is reframed as session accretion above. Correctness risk is < 5% impossible-blocker.
- **SLM surface debt** accumulates from CNL form changes — batch retrains via the ledger in `harneskills`
  (`handoff_slm_surface_track.md`).
- **One-graph fold hazard (Phase 3.1 step 2)** — ephemeral APPLY frames add incoming edges to fact nodes;
  previewed and controlled by GC-after-pass, but the full fold needs care.
- **Meta-debugging** — the Phase 4 trace renderer is the mitigation; it is complete.
