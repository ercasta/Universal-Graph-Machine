# Implementation Plan — Universal Graph Machine (ACTIVE / remaining work)

> **Status: THE ACTIVE PLAN (re-pointed 2026-07-16 — see "Current focus").** This file holds ONLY remaining
> work. Everything landed lives in `CHANGELOG.md` (dated entries + the phase appendix at its end);
> the as-built system is described by `architecture.md` and the reference docs. The harness (planning
> rule banks, SLM, session, TUI) has its own plan in `harneskills`.
>
> Module paths: `ugm.xxx` (engine), `ugm.cnl.xxx` (CNL surface). Tests: `tests/`. Source: `ugm/`.
>
> Read first: `README.md` (index + decisions in force) → `vision.md` → `reference/logic_fragment.md`
> → `reference/processing_modes.md` → `reference/isa_reference.md` → `architecture.md`. Log landed
> work in `CHANGELOG.md`.
>
> Standing rules: no commits by the assistant; domain logic ONLY in banks; strategies are
> DECLARED data, never engine sniffing; correctness before raw performance.
>
> **RATIFIED 2026-07-10 (user): EQUIVALENCE WITH THE PREVIOUS (rewriter / name-based) GENERATION IS NOT
> A CORRECTNESS TARGET.** The old generation was never used. The goal is a **WORKING, self-consistent
> firmware system**, judged on producing sensible answers on the benches, NOT on reproducing the old
> exhaustive engine's outputs. Real long-pole for a *usable* system = **performance (Phase 7)**, not
> correctness.

## ▶ PICK UP HERE (handoff 2026-07-19, suite 721 green, working tree clean of blockers)

**STATE.** Integration steps 1, 2, 3 are DONE and the revision loop (slice 3) is built; steps 4, 5
remain. Design: `design/homoiconic_grammar.md` §13, `design/surface_interpretation.md`.

**Where the new code is:** `ugm/cnl/grammar_intake.py` (the forked route + `reconsider`),
`ugm/cnl/grammar.py` (`mintable_slots` / `remint_mark_bank` / `reinterpretation_slots`, and the span
rule's idempotency NAC), `ugm/interpretation.py` (`interpret(slots=…)` override, `discard_scope`
fixes), the fork block at `ugm/intake.py:461`, tests `tests/test_grammar_intake.py` (15) +
`test_parse_banks_are_idempotent` in `tests/test_grammar.py`.

**STEP 2 LANDED 2026-07-19 AS OPTION (b), VIA A DELIBERATE FORK.** User decision: option (a)'s
direct fold was rejected as a target because it entrenches the token/entity duality —
**the target is interpretation nodes**, and "going red for a while" plus duplicated intake paths is
acceptable to get there. Built:

- `ugm/cnl/grammar_intake.py` — the grammar route. `declare_grammar` parks compiled banks in
  `kb.registers["grammar"]` (mechanism state, beside `forms`/`policy`); `route()` runs
  parse → `live_scope` → `interpretation.interpret`, so **facts land on ENTITY nodes reached by
  `denotes`, never on the tokens**. ONE live scope per session (`registers["interpretation"]`) —
  enforcing a single live interpretation is what keeps branch selection out.
- **Entity-aware counterparts of the three duality-dependent readers**, written beside the
  originals rather than as edits to them: `denotata` (the `denotes` hop), `has_content_fact`
  (counterpart of `authoring.anchor_has_content_fact`), `utterance_centers` (counterpart of
  `focus.utterance_subjects`, rendering centers via `describe` so a minted subkind enters focus by
  its DESCRIPTION — it has no name).
- **The fork point** is one block at `ugm/intake.py:461`, routed by the declared register (§D.1, no
  string sniff). Questions, rules, focus moves, forms and procedures are UNTOUCHED and shared by
  both paths. Declare-before-use means the suite stayed green by construction — **the fork cost 0
  failures**, since no KB in the repo declares a grammar yet.
- **`Outcome("ambiguous")` is a new kind** (not a flavour of `unrecognized`): "I cannot parse this"
  and "I parsed it two ways" want different responses, and only the second becomes a discriminating
  question. An ambiguous utterance commits NOTHING (pinned by test) where today's bank writes three
  wrong facts.
- `tests/test_grammar_intake.py` (15) pins the contract: fact-on-entity-not-token, surface survives
  `discard_scope`, the exception sentence lands as `has_not`, refused ≠ ambiguous, and a KB with no
  grammar is unaffected.

**SLICE 3 (THE REVISION LOOP) DONE 2026-07-19 (suite 721 green).** `grammar_intake.reconsider`.
The design question below DISSOLVED: the answer is not "declare alternative readings" but
**evidence-driven re-minting** — the contradiction itself says where to re-read.

- **THE DISCRIMINATOR** (user's framing, and the key architectural point): one derived contradiction
  is the same signal for two faults in different layers — "you merged two entities" (a JUDGEMENT:
  defeasible, session-scoped, discardable) vs "your rule needs an exception" (KNOWLEDGE: structural,
  persists across sessions). The support tells them apart: if the contradicted entity was
  interpreted from >1 surface mention, a coreference judgement is load-bearing → re-interpret. If
  not, `reconsider` returns `RULE` and touches NOTHING — that case belongs to the learning arc's
  defeasible-exception model (§7.3), not here. **Try the revisable thing first, because being wrong
  about it is free.**
- **Mechanism, all in rules:** `remint_mark_bank` marks the spans a contradiction implicates (it
  re-derives the contradiction condition inline, like `contradiction_bank`, since the
  `<contradiction>` node has no stable identity to match on); `reinterpretation_slots` percolates
  everywhere EXCEPT a marked span and mints there instead (NAC / premise on the same marker, so a
  re-interpretation is still ONE reading, never a branch). `mintable_slots` derives WHERE minting is
  meaningful from the grammar's own declarations — a `head`-slot whose category asserts a
  description built from another slot of the same production — never from category names.
- **Result on the real case** (`bengal`/`guzerat`/bare `lion`): 1 contradiction → `REVISED`, 0
  remaining, and the facts are `<is bengal & is_a lion> has mane`, `<is guzerat & is_a lion> has_not
  mane`, **`lion has mane`**. The bare mention stays unsplit because it heads no mintable production
  — which is exactly what makes minting evidence-driven rather than the unconditional (and for a
  non-restrictive modifier, wrong) move a declared `mint` grammar makes. This closes the plan's open
  item "restrictive vs non-restrictive modification" by a route it did not anticipate.
- Marks live on SPANS (surface), so they survive the discard that clears the entities: a re-minting
  judgement is DURABLE and every later utterance is read under it.

**BUGS FOUND BUILDING IT.**
1. **`discard_scope` leaked one orphan `member` rel per member** — `remove_node` does not clean up a
   node's INCOMING relations. The operation the whole architecture rests on being free was quietly
   not discarding. (Then I broke it worse: reading `scope_members` AFTER unlinking them discarded
   NOTHING — snapshot membership first. That regression, not any name collision, is what made a
   3-sentence session stop terminating.)
2. **`route` accumulated interpretations instead of replacing one** — 3 sentences produced 5
   duplicate contradiction markers. One live interpretation means exactly one, rebuilt.
3. **A bound-literal marker mints a fresh node per firing**, so the mint rule matched once per mark
   and minted an entity for each (35 marks, 5× node blowup). The mark is a flag: it must be a PLAIN
   literal, which the lowering interns graph-wide.
4. **⭐ `span_bank` WAS NOT IDEMPOTENT — a pre-existing shipped defect (integration step 1) that made
   session-long surface accretion QUADRATIC.** `<span>?` is a BOUND literal: named, but minted FRESH
   per firing. `parse` runs every bank over the WHOLE graph, so each utterance re-minted all of the
   session's earlier spans — re-running the banks on an UNCHANGED graph added 52 nodes every time,
   and parsing one sentence five times grew the graph by 104, 149, 201, 253, 305. Fixed with a
   self-guarding NAC ("unless a span with this cat/begin/end already stands"); accretion is now FLAT
   at 97/sentence. This is the structural counterpart of `intern_described`, which fixes exactly
   this re-minting for minted ENTITIES — same defect, other layer. Pinned by
   `test_parse_banks_are_idempotent`. **GENERAL LESSON, alongside the `load_facts` one: a bank that
   runs over the whole graph must be IDEMPOTENT, or repetition is quadratic by construction.**

**MEASURED AFTER THE FIXES** (3-sentence session): route `0.23 / 0.60 / 1.07 s` (was 0.21 / 1.14 /
4.41 — 4.1× on the third), `reconsider` **0.91 s** (was 6.65 — 7.3×), graph 508 nodes (was 1497),
suite 97 s → 63 s. Interpretation now shows ZERO leak across repeated interpret/discard cycles.

**A CORRECTION, RECORDED BECAUSE THE WRONG VERSION WAS BRIEFLY WRITTEN DOWN HERE.** This plan
claimed a second bug: "a standing interpretation makes the next `parse` explode, because the chart
keys on NAMES and `interpret_mentions` mints entities carrying their token's name". **That is
FALSE.** Measured: parsing with a live interpretation costs 0.06 s and the chart does not grow — the
lexicon rules require `?t next ?u` and entity nodes have no `next`, so they cannot match. The
apparent explosion was bug 1 (nothing was being discarded, so interpretations piled up). The
`route`-discards-before-parsing layering built on that false premise has been REMOVED; results and
timings are identical without it.

**Consequence for the token/entity partition question (user, 2026-07-19):** distinguishing discourse
tokens from interpretation nodes would NOT have helped performance, because the bug motivating it
does not exist. The epistemic split may still be right on other grounds (`surface_interpretation.md`
argues observation-vs-inference decides membership unambiguously, unlike the engineering strata a
`<stratum>` tag was rejected for) — but it should be decided on those grounds, NOT sold as a perf
fix. The real perf lever was idempotency.

**Still owed:** `route` calls `parse` (not `parse_batch`) and `interpret` re-reads the WHOLE standing
surface per utterance, so cost is still linear-per-utterance = quadratic per session. Now that
discarding before parsing is gone, the incremental path is open: keep the scope and interpret only
the new spans, re-interpreting wholesale only when a contradiction demands it.

**STEP 4, FIRST LEVER LANDED 2026-07-19 (suite 723 green): THE PARSE TREE IS MATERIALIZED.**
Measured first, and the measurement redirected the work twice — record this, because the plan's
stated priorities were wrong in a specific, repeatable way.

- **What the 8-sentence session actually cost:** `parse` 0.66 s / `interpret` 10.75 s. So
  **`parse_batch` — the lever this section owed — is 6% of the problem**, and `interpret` is 94%.
  One level down, `interpret`'s five whole-graph banks split **88.5% slots**, 11% asserts, and
  ~0% for the other three.
- **The fix** (the "materialize the parse tree" lever below, confirmed still dominant): a new
  `decomposition_bank` reifies ONE `<dec>` node per (parent, children) decomposition, and every
  slot rule now seeds on a `dprod` literal and does two pointer hops instead of redoing the same
  9-premise `cat`/`begin`/`end` join. `_production_lhs` is the single chokepoint, so `slot_bank`,
  `remint_mark_bank` and `reinterpretation_slots` all got it at once.
- **A REIFIED decomposition node, not flat `kidl`/`kidr` edges** — the chart is PACKED, so one span
  can carry several decompositions, and two flat edge sets would let the left child of one reading
  pair with the right child of another and feed a slot from a tree that was never parsed. Pinned by
  `test_decompositions_tile_their_parent`.
- The bank runs in `parse` (it is SURFACE — spans and their tree, no denotation) and is
  **idempotent by NAC**, the `span_bank` lesson applied one layer up.
- **MEASURED:** slot stage 9.39 → 0.54 s (**17×**), interpret 10.75 → 1.67 s (**6.4×**), session
  11.41 → 3.11 s (**3.7×**), suite 66.7 → 53.1 s. Work moved INTO parse (0.66 → 1.44 s), which is
  the right trade: derived once per decomposition instead of 32 times per interpretation.

**WHERE THE COST SITS NOW** (re-measure again before the next lever — that is twice this section's
stated priority has been wrong):
- `parse` **1.44 s (46%)**, now the steeper curve: `decomposition_bank` still runs its 9-premise
  join over the WHOLE standing surface every utterance. Idempotent, so it accretes nothing — but it
  still pays the match. This is the natural landing site for the incremental fix, and the cost is
  now concentrated in ONE bank instead of smeared across 32 slot rules.
- `interpret` **1.67 s (54%)**, now dominated by **`asserts` (1.02 s, 63% of interpretation)** —
  which is lever (2) below (86 rules only because a slot-valued predicate expands per lexicon word;
  RHS variable predicates take it to ~6, and the LEARNING ARC WANTS THE SAME PRIMITIVE).
- So the ordering from here is: **(a) RHS variable predicates** (biggest single stage, and shared
  with the learning arc), then **(b) incremental surface** (the remaining curve, both banks).

**STEP 4, SECOND LEVER LANDED 2026-07-19 (suite 728 green): RHS VARIABLE PREDICATES.** The
`predicates-are-keys` primitive the learning arc also wants, built as its first slice.

- **`MINT` gained `key_reg`** — a DYNAMIC PREDICATE for a reified relation, the same mechanism
  `EMIT` already had. The mechanism existing on `EMIT` but not `MINT` is the whole reason this was
  blocked: a fact head is a MINTED rel node, so `EMIT`'s dynamic key could not reach it.
  **`dedup` resolves the dynamic key too** — without that, a variable-predicate rule mints a fresh
  rel node per firing and never reaches a fixpoint (the accretion `dedup` exists to prevent, back
  through the door). Pinned by `test_a_dynamic_key_head_still_dedups`.
- **`lower_rhs` now accepts an LHS-BOUND predicate variable** and still rejects an RHS-ONLY one:
  with no LHS binding there is no node to take a name from, and inventing one is predicate
  INVENTION — the rest of `predicates-are-keys`, deliberately NOT smuggled in through the lowering.
- **`assert_bank` 133 rules → 33.** A slot-valued predicate no longer expands per lexicon word.
- **DENY still expands** (26 of the remaining 33 rules): its head is `neg_pred(?w)`, a STRING
  derivation from the matched word, and the ISA has no string ops. Collapsing it needs the
  positive/negative pairing to exist as GRAPH DATA (`w -[neg_of]-> w_not`) so the rule can BIND the
  negative instead of computing it — a vocabulary change, not a lowering one. Cheap and worth doing;
  it would take the bank to ~8.
- **MEASURED:** asserts stage 1.02 → 0.28 s (**3.6×**), interpret 1.67 → 1.03 s, session
  3.11 → 2.50 s. **Cumulative across both levers: 11.41 → 2.50 s (4.6×)**, suite 97 → 52 s.

**NOW: `parse` is 1.48 s = 59% of the session and is the whole remaining curve.** It is
`decomposition_bank` re-joining over the WHOLE standing surface every utterance — idempotent, so it
accretes nothing, but it still pays the match. Both remaining levers are the SAME fix now
(incremental surface: keep the scope, process only new spans), and the cost is concentrated in one
bank, which is the best shape it has been in for that work. **Re-measure first — the stated lever
has been wrong twice in this section.**

**Also fixed 2026-07-19: `declare_grammar` failed SILENTLY on a bad path.** A non-existent path fell
through to `load_grammar(str(...))` and was parsed AS GRAMMAR TEXT, giving an empty grammar that
refused every sentence — the failure looked like "the grammar is fast", and it cost one bogus
benchmark run before being noticed. Now raises on an unresolvable path, plus a backstop `ValueError`
for any grammar with no lexicon and no productions whatever it was built from.

**Superseded design question (kept — the argument is why the answer is better):** The loop
contradiction → ask → `discard_scope` → re-interpret is what interpretation nodes are FOR, and three
of its four pieces already exist (`contradiction_bank` runs inside `interpret`; `discard_scope`;
`culprits`). The missing piece is **how a KB declares ALTERNATIVE READINGS**. The Loudon bench gets
its two readings by string-substituting one declaration line
(`slot head in np from modifier plus np is right head` → `mint head in np from modifier plus np
under right head`), which is a bench trick, not a surface. Options to decide between: a declared
ranked list of readings in the grammar file; a reading as a named variant bank the re-interpretation
selects; or the discriminating question choosing the slot declaration directly. Do NOT invent this
silently — it decides what "re-interpret" even means.

**Then step 4 (optimize) and step 5 (retire what the fork subsumes).** Note the grammar route
inherits the "run_bank over the whole graph, once per utterance" quadratic shape — `route()` calls
`parse` (not `parse_batch`) and `interpret` re-runs over the standing surface. Fine at session
scale; MEASURE before step 4, and re-measure the step-4 levers below since the 29× `load_facts` fix
already changed the cost picture.

**Superseded resume block (2026-07-18) follows** — its option (a)/(b) question is CLOSED by the
above.

**Where the code is:** `ugm/cnl/grammar.py` (declarations → `Grammar` → `GrammarBanks` → `parse` /
`parse_batch`), `ugm/interpretation.py` (scope, `denotes`/`interprets`, `discard_scope`,
`<contradiction>`, `describe`/`intern_described`), grammars as KB files
(`corpus/lion_grammar.cnl`, `corpus/loudon_grammar.cnl`), tests `tests/test_grammar.py` (24),
benches `bench/spike_homoiconic_grammar.py`, `bench/spike_interpretation_scope.py`,
`bench/spike_loudon_grammar.py`. Designs: `design/homoiconic_grammar.md` (READ ITS §0 FIRST — §§8-12
are spike evidence), `design/surface_interpretation.md`.

**⚠ THE NEXT ACTION NEEDS A DECISION FROM THE USER — ask before building.** Integration step 2
(wire the grammar as an opt-in intake route) hits the **token/entity duality**: today the token node
IS the entity (`focus.utterance_subjects`, `anchor_has_content_fact`, `gc_utterance_scaffolding`,
every `nodes_named` lookup depend on it, and `intern_mentions` maintains it by destructively folding
same-named mentions). But `interpretation.interpret_mentions` mints a SEPARATE entity node named
`lion` beside the token also named `lion` — two nodes, one name, ambiguous lookups. Two options:

- **(a) grammar route, DIRECT fold — ~1 hour.** Lexical head is the token itself, no interpretation
  scope; facts land exactly where they do today so nothing downstream changes. Ships the coverage
  win (intransitive / negation / comparative / prepositional + REFUSE + ambiguity detection) into
  production intake. Drops the defeasible-denotation layer. **Recommended** — the hook is one block
  at `intake.py:462-468` (`_ingest_gen`'s FACT/GOAL/UNRECOGNIZED route), and exercising the grammar
  from real intake paths should surface more of what step 3 surfaced.
- **(b) grammar route WITH the interpretation scope — a session or more.** Requires resolving the
  duality across intake/focus/query, in code with no grammar tests protecting it. NOTE: a middle
  path (make the representative TOKEN be the entity, so no duplicate names) was explored and
  collapses back into (b) — it needs a consistent representative across mentions, which is exactly
  what destructive `intern_mentions` provides today and what the scope is meant to make revisable.

If (a): also decide what an AMBIGUOUS utterance returns — a new `Outcome` kind, or `unrecognized`
with distinct guidance. It should ultimately become a discriminating question via `can_ask`.

**Alternative if the user prefers not to split the layer:** skip to step 4 (optimization) and return
to integration once the duality has a plan. Step 4's measured levers: materialize the parse tree
(slot stage 81.7 → 21.7 ms, 3.8×, MEASURED) and RHS variable predicates (assert bank 86 → ~6 rules;
**the learning arc wants the same primitive**, `predicates-are-keys`). Note the 29× `load_facts` fix
below already changed the cost picture — RE-MEASURE before optimizing further.

**Not blocking but owed:** `<contradiction>` derivation is still a local stand-in
(`interpretation.contradiction_bank`); `consistency_design.md` designs the real one and remains a
SKETCH. The interpretation loop depends on it. Also `authoring.load_facts` does not strip `#`
comments though every other CNL loader does (worked around in `grammar.load_grammar`) — fix at
source.

## Current focus (re-pointed 2026-07-18 — INTAKE GRAMMAR, ahead of more learning)

**SPIKE DONE 2026-07-18, GREEN — the arc is buildable** (`bench/spike_homoiconic_grammar.py`,
results in `design/homoiconic_grammar.md` §8). **NEXT TASK: slice 1, THE FOLD** (parse → facts,
production-attached semantics), gated on subsuming `FACT_FORMS`.

What the spike settled, in one paragraph. A grammar declared in CNL (lexicon `lion is a noun`,
unchanged shipped surface + ONE new production form pair `np expands to determiner plus np`)
generates chart rules that run on `run_bank` with NO engine change. **Token-passing IS chart
parsing** — a chart is exactly "every enabled rule fires, nothing selects" — so the §3 crux was a
false alarm at the level of the control regime. All five residual Loudon failures now parse
(intransitive, negation+modifier, prepositional, comparative), including `the guzerat lion has no
mane` — the exception-bearing sentence the whole re-point was about — and `glorp the flarn` is
REFUSED. **Ambiguity is detectable in-engine with no branch selection**: not by counting root
spans (that silently reports "unambiguous" — packing erases derivation identity), and not by an
unpacked forest (correct but 5.2 s at 11 tokens), but by a generated top-down USEFULNESS pass plus
a `Distinct` on the split point — exact on the PP-attachment case, zero false positives, 41 rules.
Open vocabulary works and refusal survives it (one NAC rule over declared closed classes; also
cheaper). Cost 15-41 ms/utterance against a ~12 ms budget, on an unmemoized bank.

**SLICE 1 (THE FOLD) DONE 2026-07-18** — `bench/spike_grammar_fold.py`, design §9. Semantics is
CNL too (`slot head in np from determiner plus np is right head`; `clause denies subj pred obj
when neg`) — 68 CNL lines, 206 generated rules, no Python escape hatch, so **§5.4 answers "no
second system"** on the evidence available. The architectural move: the chart stays PACKED while
parsing and identity is minted only for the spans the usefulness pass says survive — O(n), so
slots get nodes to hang on without paying for the unpacked forest. `the guzerat lion has no mane`
now writes **`(lion has_not mane)`** — the exception the learner needed and never got. The
ambiguous sentence writes NOTHING and asks, where today's bank writes three wrong facts.

**§7 RESOLVED 2026-07-18** — `bench/spike_grammar_subkind.py`, design §10. The dichotomy was
FALSE: the choice was never "decompose onto the head" vs "an opaque `african_lion` string". A
modified NP mints a distinct NAMELESS node whose identity is its DESCRIPTION — `<e> is_a lion`,
`<e> is guzerat` — so decomposition stays completely intact (both questions still answer) and only
the node carrying it changes. Nameless is the precedent, not an exception: feedback #15's
`ByDesc`/`_find_skolem_witness` identity law already says a minted node has no name, only its
defining relations. **One declaration line** carries it (`mint head in np from modifier plus np
under right head`). Payoff beyond tidiness: `lion has mane` and `<e> has_not mane` now stand on
different nodes linked by `is_a`, so the exception is a REACHABLE counterexample to
`?x has mane when ?x is_a lion` — the structure the defeasible-exception arc has been missing was
a grammar problem all along. Cost: interning must become description-keyed (`intern_described`,
the counterpart to the name-keyed `intern_mentions`, which is structurally blind to nameless
nodes) — and that is REQUIRED for correctness, not tidiness, because RHS-only value invention
re-mints on every bank run (10 nodes → 1 on a 3-sentence corpus).

**INTEGRATION STEP 1 DONE 2026-07-18 (suite 705 green).** The machinery moved out of `bench/` into
`ugm/cnl/grammar.py` (declaration forms, `Grammar`/`GrammarBanks`, chart/ambiguity/span/slot/assert
generation, `parse`) and `ugm/interpretation.py` (scope, `denotes`/`interprets`, `discard_scope`,
contradiction marker, `describe`/`intern_described`); the grammar itself is now a real KB file,
`corpus/lion_grammar.cnl`; behaviours pinned by `tests/test_grammar.py` (22 tests). The two spikes
whose content had entirely moved were DELETED; the two that remain keep only the measurements that
decided design questions and import the modules (output verified byte-identical). **No existing
path changed** — nothing calls the grammar yet, which is why the suite stayed green.

**INTEGRATION STEP 3 DONE 2026-07-18 (suite 706 green)** — the grammar met the Loudon corpus
(`bench/spike_loudon_grammar.py`, `corpus/loudon_grammar.cnl`, design §12). **19/19 (100%) parsed
on the FIRST pass**, 0 refused, 0 ambiguous, 28.5 ms/line; the grammar needed three new
constructions (predicative adjective, copula+NP subsumption, a second preposition), all
declarations, no Python. The KB now holds the generalization AND its counterexample on distinct
`is_a`-linked entities; the same corpus derives **1 contradiction under the percolating reading and
0 under minting**. Caveat: these are the 19 CNL lines an LLM produced from the 50 sentences, not
the sentences.

**⚠ SHIPPED-CODE DEFECT FOUND AND FIXED: `load_facts` was QUADRATIC in batch size.**
`authoring._recognize` ran `normalize_surface` once per sentence, but that ignores its `anchor` and
runs each stratum over the WHOLE graph to fixpoint — N sentences = N global fixpoints over a graph
growing with N. 26 ms/line at 10 lines, 161 ms/line at 80; an 85-line KB file took 24 s. Hoisted to
ONE batch pass: per-line cost FLAT ~5 ms, 80 lines **12.9 s → 0.44 s (29×)**, and the whole test
suite 78 s → 42 s. This bites `load_facts`/`load_corpus`/`load_kb` equally — the grammar arc only
exposed it. GENERAL LESSON (it recurred immediately in the new code, fixed with `parse_batch`):
**"run_bank over the whole graph, once per utterance" is quadratic by construction.**

Also fixed: **identity must be settled before predication** — an acquired fact (`the african lion
is strong`) leaked into a minted entity's DESCRIPTION and stopped it interning with the same
subkind elsewhere, because NP-level attribution and clause-level predication both write `is`.
Assertions in a MINTING category are now DEFINING, run first, then interning, then everything else.

**Integration steps 2, 4, 5:** (2) wire as an OPT-IN intake route — a KB that declares a grammar gets
the grammar path, everything else keeps the shipped forms (declare-before-use, so the suite stays
green by construction); (3) **run the real corpora** — Loudon's 50 sentences first: all coverage so
far is on 7 hand-picked sentences chosen to exercise known gaps, so expect this to be sobering, and
it will force the question of WHO WRITES THE GRAMMAR for open prose (loops back to the learning
arc's T3 form learning); (4) optimize; (5) retire what it subsumes. Step 3 needs `<contradiction>`
derivation, which `consistency_design.md` sketches but does not build.

**Optimizations, when step 4 arrives:** (1) ~~**materialize the parse tree**~~ **DONE 2026-07-19 —
see the step-4 block above.** Diagnosis confirmed (all 32 slot rules redid the same 6-way
parent/child join; the stage was 88.5% of interpretation), but the prescription needed one change:
NOT flat `?p kidL/kidR` edges, which mispair children of a packed span, but a REIFIED decomposition
node. Result 17× on the stage, better than the 3.8× predicted here. ~~Second lever: the assert stage
is 86 rules only because a slot-valued predicate expands per lexicon word~~ **ALSO DONE 2026-07-19
(133 → 33 on the Loudon grammar; see the second-lever block above)** — `MINT.key_reg` plus
`lower_rhs` accepting an LHS-BOUND predicate variable. Landed the LEARNING ARC's shared primitive
(`predicates-are-keys`) in its first slice; predicate INVENTION (an RHS-only predicate variable)
stays rejected. The DENY case still expands per word and needs the negative-predicate pairing as
graph data to finish; (2) ambiguity → discriminating question
via `can_ask`; (3) restrictive vs non-restrictive modification — minting is currently unconditional,
which is weaker rather than wrong but loses the merge's free coreference; route on the existing
`declared_definites`/`is_unique` machinery (UNTESTED); (4) declaration loudness (a malformed `slot`
line still fails silently); (5) compare against `comparative.py` before claiming full subsumption.

**SURFACE / INTERPRETATION SPLIT — spiked 2026-07-18** (`bench/spike_interpretation_scope.py`,
design §11; user proposal). The sentence's nodes are the permanent monotone record; every
JUDGEMENT about what it MEANS (denotation, coreference, subkind-vs-same-entity) lives in a SCOPE of
COPIES with provenance back to the surface. **Inside the scope the merge stays destructive** — one
node per entity, no `same_as` clique, no representative hop — because reversal is never needed:
discard and re-derive. Demonstrated end to end: 2 sentences parsed ONCE (231 surface nodes) →
interpretation A percolates → `lion has mane` + `lion has_not mane` → `<contradiction>` derived →
provenance shows the entity came from 2 surface mentions, so a JUDGEMENT is in the support → ASK →
discard scope (90 nodes, 231/231 surface intact) → interpretation B mints a subkind → 0
contradictions, no re-parse. **The system discovers the reading was wrong instead of being told** —
which removes §10's requirement that the domain author know the right reading in advance.

**This is also the answer to the substrate-layering question.** A `<stratum>` node attribute was
the wrong shape because the strata on offer were ENGINEERING distinctions (control vs fact) while
the failures were reading rules over legitimately shared nodes. Observation vs inference is
EPISTEMIC, is exactly two layers, and decides membership unambiguously. Key finding: the line is
not "which node it hangs on" but "structure vs denotation" — the surface is tokens, chains and
`cat`/`begin`/`end`, and every slot/`denotes` edge is interpretation even when written onto a
surface span. Open before this is production: copy-on-WRITE scope (materialized today — at session
scale it must be a delta over `OVERLAY` or it shadows the whole KB); PROMOTION of uncontested
interpretations (same mechanism as promotion-by-survival for rules); enforcing ONE live
interpretation (else branch selection returns); culprit selection when the support holds several
judgements; and reusing `suppose`/`SCOPE` (noting this is a STANDING scope, not a hypothesis fork).

**Substrate layering (user question, 2026-07-18):** the fold slice hit TWO accidental cross-layer
reads — `is_a <mention>` polluting the lexicon (152 rules instead of 30, ~80% of runtime) and a
CNL `yes` token being deleted by `authoring._recognize`'s scaffolding strip. Both are name-keyed
GLOBAL partitions leaking into user data (a shared PREDICATE; a reserved NAME). Neither would have
been caught by a node-level `<stratum>` tag — in both cases the node was legitimately shared and
the *reading rule* had no business seeing it. Design note in §9.5; decide after the memoization
pass, against this incident list rather than speculatively.

Original framing of the task, kept because the argument is what selected it:

Why this and not the next learning slice — a real-corpus test redirected the plan. The learning arc
landed (S1, S1b, S3a, S5, S6; `design/learning_design.md`), and was then run against 50 verbatim
sentences of a real natural-history book (`bench/spike_loudon.py`, `bench/loudon_lion_corpus.py`).
Three results, in ascending order of importance:

1. **Real prose is 26% facts.** 13/50 sentences assert anything extractable; the rest is anecdote,
   quoted narrative, hedged attribution. That is the SOURCE's property, not a defect.
2. **Intake was 0%, and it was a WIRING gap.** `surface_forms` (determiner stripping + noun-phrase
   decomposition) ran on the question path and the loose-rule path but never on the FACT path.
   Wiring it into `authoring._recognize` took routed coverage 0% → 79%; 7.1 → 11.2 ms/utterance
   after memoizing the strata. `tests/test_intake_surface_facts.py`.
3. **PARTIAL INTAKE COVERAGE IS NOT NEUTRAL — this is what re-points the plan.** Exceptions are
   LINGUISTICALLY MARKED ("without any mane", "no", "unlike", "except"), and those are exactly the
   constructions a bare S-P-O form bank drops. The corpus states a real generalization (lions have
   manes) AND its real exception (the Lion of Guzerat has none); the learner proposed the
   generalization and the exception never reached the KB, because that sentence is the one that
   would not parse. A partially-covering parser does not lose sentences at random: it loses the
   EXCEPTIONS and keeps the GENERALIZATIONS, biasing everything downstream toward confident
   over-generalization.

So more learning machinery on top of partial intake produces optimistically-biased results, and the
defeasible-exception work has no data to run on. **Intake first.**

And 79% is ROUTING, not correctness — two silent defects are pinned as tests:
`the lion lives in africa` ROUTES as a fact and folds to `('lives','is','lion')` (an undeclared verb
absorbed by NP-decomposition — worse than the unrecognized case it replaced), and
`the guzerat lion has no mane` is unrecognized yet still writes `lion is guzerat` (an unrecognized
line is not inert, and the dropped part is the negation). Both are the "quietly does something
wrong" class that S1/S1b spent the session eliminating — which is the argument for the grammar.

### Then (unblocked, in the learning arc)
- **§7.3 rule revision** + the **defeasible-exception model** (user-agreed: refutation should record
  an exception, not delete a good rule). Blocked on intake for DATA, not for mechanism.
- **Promotion by survival** — counting survived/failed discriminating questions as rule attributes
  (user's idea; auditable, unlike frequency). Decide defeasible-vs-fatal refutation FIRST, or the
  fatal model gets baked in.
- **S2/S2b/S2c** — the dialogue surfaces (Caveman CNL T1, the T3 alignment spike, and the
  discriminating question, which is the bootstrapping engine and serves both halves of the arc).

## Current focus (SUPERSEDED — re-pointed 2026-07-16, Phase 8's engine side is COMPLETE)

Every substrate-side arc that was in flight is now closed (see CHANGELOG 2026-07-16 entries and the
per-arc docs): mechanism/policy BOTH AXES (incl. the discriminator audit), the possibilistic layer
(incl. the polish batch: kind-wearing verdicts, env-rendering, stance CNL, fork-leak fix), the whole
explanation arc (linked subgoal chain + certain-NAF assumed-records), Phase 8's engine side
(goal/act route with async-tool suspend, nearest-forms rejection, focus-reachability GC), and the
parked-item cleanup (demand-coref CLOSED-as-settled; INTERPOSE/RESTORE deleted). The book is synced.

**Also closed (2026-07-16, the compliance/revision session):**
- **ISA-compliance pass** — every driver write is an ISA program (`provenance.record_firing` =
  the ONE justification-minting path; retraction RECORD = MINT+`REDIRECT`; suppose/possibility/
  choose writes lowered); new gated opcodes `REDIRECT` (privileged, retraction-only) and `SWEEP`
  (control-node deletion, refuses facts/provenance); BORN-CONTROL token skolems
  (`lower_rhs.resolve`), so every scaffolding deletion flows through `SWEEP`/`DROP_CTRL`; the
  superseded APPLY frame-matcher DELETED (`apply.py` = shared readers + head index).
- **Determinism + demand subsumption** — substrate adjacency/indices are insertion-ordered
  dict-as-set (the 30× PYTHONHASHSEED work-variance fix; runs are bit-for-bit reproducible on the
  fast topology); `_round` skips demands whose strict generalization stands (halves adversarial
  topologies, +0.45% on the fast path).
- **RECONSIDER (`design/reconsider_design.md`, BUILT)** — demand-driven revision of materialized
  NAF conclusions: intake marks `(pred, obj)` grains in registers; the next committed ask re-checks
  affected `<assumed>` records and withdraws broken support (cascade + copy-on-delete, history
  stamped `broken_assumption`); forward `run_bank` journals its survived NACs too (provenance=True);
  committed intake asks run provenance ALWAYS-ON (user-ratified; +15% heavy whole-graph ask).
- **Hard-vs-assumed surfacing capstone** — `ask_goal` verdicts wear their kind in every stance
  (`no` / `no (assumed)` / `unknown`); book synced (chs. 0/3/4/5/8/9/10/19 + appendix; ch. 8 tells
  the self-revision story).
- **Habitability hardening** — inverted why-question forms; the keyword-in-name-slot lint
  (`query._kw_in_name_slot`): a mis-parse is UNRECOGNIZED (loud wall + nearest-forms), never a
  silent wrong answer.

**The queue, in order:**

1. **The CLIENT — rebuild `harneskills_new` against the `converse`/Event/Outcome contract**
   (external repo; UGM owns the contract — user decision 2026-07-16, recorded in
   `design/cnl_intake_design.md`). The harness's own session/driver/interaction scaffolding predates
   the intake spine and duplicates it; the end-state is a `Session` that only drives `converse` and
   renders events (TUI), with the SLM at the NL→CNL boundary (anaphora via `focus.top_centers`).
   The **Phase 5 exit-gate bench half** (card-trader + coref + ProofWriter coverage) rides along —
   it runs in the harness. Nothing in this repo blocks it; engine gaps found there come back here as
   feedback items.
2. **CNL FORM AUTHORING (Phase 9 — RE-SCOPED + RATIFIED 2026-07-16).** ⭐ DESIGN:
   **`design/form_authoring_design.md`** — build by its §5 slices. The original
   "forms-as-KB-data" scope (migrate every bank to KB-resident reified rules, self-hosting
   kernel, zero-`Rule`-literals gate) was CUT after benefit decomposition (design §6): the
   shipped banks are frozen in practice, `Rule` lists are already DATA to the lowering (so the
   Rust boundary was already final), habitability already derives from `Rule` structure, and
   in-engine grammar metareasoning — the only capability reification enables — is ruled out
   (user, 2026-07-16). What remains is the capability that was genuinely missing: **the grammar
   is extensible from the outside, in CNL** — `form KEY : HEAD when BODY` (machine grammar +
   new `rl_key` naming form), recognized at intake and in loaded KB files (multi-KB model,
   strict declare-before-use), routed to its bank by its own RHS structure, disable/nearest-
   forms covered, persisted as the CNL line itself. Enabling finding kept: rule-source CNL
   already spans the form language (bound-literal tokens `is?`/`<query>?`; NAC-group
   independence) — full reification stays a proven, parked path. Exit gate
   (capability-shaped): a domain KB file declares a new sentence shape in CNL; facts and
   questions in that shape parse; nearest-forms and disable cover it; no Python edited.
   **Slices A+B DONE 2026-07-16 (567 green)** — `cnl/form_authoring.py` (`form KEY :` grammar,
   `rl_key`, safety lint, key-merge) + intake FORM route + D3 bank placement + `load_kb`
   (multi-KB-file, declare-before-use); nearest-forms/disable cover authored forms. Exit gate
   MET (a KB file declares new shapes; parse/answer/suggest/disable all work; no Python edited).
   Book DONE (ch. 7 "You can teach it new shapes"). Remaining: optional Slice C (exemplar sugar).
3. **PROCEDURES (queued arc — design notes RATIFIED 2026-07-16: `design/procedures_design.md`).**
   Sequences of actions toward a goal — the agentic-harness "drive the execution" capability,
   after Phase 9 Slice B. Decomposition (all KB data + declared banks, NO engine change —
   composition ITERATE × CALL × CHECK, passes `processing_modes.md` §4): **collections 3.4**
   (step lists as member `next`-chains — 3.4's driving workload, absorbed here) + a universal
   **STEPPING BANK** (invoke/step/advance/discrepancy + the resurrected planner gap-fill
   bridge; procedure = pre-made plan, planner = synthesized plan, same execution gate) + a
   **`to NAME :` authoring form** (Slice-A family). TOOL BOUNDARY RATIFIED same day (design
   notes §1): UGM owns the call token + the fold, executes CALCULATORS inline, SUSPENDS world
   actions to the harness (`Event("call")` / `.send()`); failure is data rules react to.
   **Slice 1 DONE 2026-07-16 (569 green)** — `corpus/procedure.cnl` (3 content-blind rules:
   invoke/order/gap-fill) rides the existing planner gate unchanged; first in-repo end-to-end
   planner run (`tests/test_procedures.py`). FINDING: `intake._act_loop` uses unstratified
   `run_bank` and must stratify to run the NAC-heavy planner gate — a Slice-2 wiring item.
   Remaining: Slice 2 (`to NAME :` surface + `<run> proc` request + act-arm stratification).
4. **Phase 7b — the Rust interpreter port** (full plan `design/rust_engine_plan.md`). Fully
   unblocked: procedures became ISA firmware first (Phase A done 2026-07-14; the 2026-07-16
   compliance pass closed the driver-write gaps), so Phase B ports ONLY the interpreter and the
   instruction set is the frozen contract. Measured prize: 381× on the match loop. The former
   "after Phase 9" ordering constraint DISSOLVED with the 9 re-scope (the data/interpreter
   boundary was already final — `Rule` lists are data to the lowering); start whenever a real
   target-scale workload is too slow and 7(a) is exhausted.

Small in-repo residuals live in their homes, none blocking: the 8.5b tail + perf levers below
("until they bite"), the possibilistic feature threads (`possibilistic.md`: abduction SUPPOSE,
propagation-strength knob, S7.7 band scale), and the Phase 3 leftovers (below).

## Current state (2026-07-16)

**Suite: 538 passed, 0 failed.** Production runtime is
100% the ISA engine — no second engine anywhere in the repo. The big arcs are COMPLETE (see CHANGELOG
for each):

- **Firmware over ISA** — the demand solver's work runs as ISA programs (one matcher, `State.regs`
  bindings, ephemeral `GRADE`/`VMATCH`, compiler-emitted visibility guards, `MEMBER`/`OVERLAY`
  live-sets); `skip_inert` retired — the machine has NO privileged category and NO mode; ONE-GRAPH FOLD
  landed including the API (`chain_sip(g, goal)` / `check(g, goal)` / `suppose(g, asms, preds)`, with
  `rules=` as an optional separate bank).
- **The ISA control machine** — `ControlMachine` (PC, `BRANCH`/`BRANCH_IF`/`CALL`/`RET`/`SUSPEND`/
  `HALT`, `SETI`/`DEC`, control stack, `PRIM`); every Python control driver ported; forward-only plane.
- **Mechanism/policy separation** — Axis A copy-on-delete retraction (privileged `RETIRE` + `<history>`
  records); Axis B `AttrGraph.registers` (focus stack is a register; the demand trace stays a graph
  node because it is EXPLANATION).
- **Phase 8 client spine** — unified intake, focus stack + seed-from-focus bounded attention (probe-
  validated flat curve), streaming `ingest`/`converse` with suspend/resume ask, trace events, runtime
  rule authoring (conflict-as-conversation, disable). 8.5b/8.6 functionally complete.

## Open follow-ons from the completed arcs (small, concrete)

- **Wire real async tools / `ask_user` through `service_calls_cm`** (control machine follow-on, lands
  with Phase 8.5 streaming): the `SUSPEND`/`RESUME` mechanism exists end-to-end with a simulated
  `AsyncTool`; it is a candidate replacement for the generator `_NeedVerdict` unwind.
- **Retire the control-mechanics `<…>` tokens** now that control moved into the machine
  (`attic/isa_control_machine.md` §6/§11 triage: explanation stays graph, mechanics become
  registers/instructions).
- **SUPPOSE scope overlay maintained incrementally by the writers** — today the `OVERLAY` set is
  derived per lookup from the `SCOPE` tags (`chain._scope_pencils`); end-state: `suppose`/`chain`
  writers maintain the register-pointed set, the tag stays the pencil's persistent explanation.
- **Forward-path readers onto the same visibility program** — `apply._fact_relnodes` etc. still read
  scope tags directly; migrate onto the `MEMBER`/`OVERLAY`/guard vocabulary the demand read uses.
- **`<call>` / dispatch state audit** — confirm none of it is a persisted fact-graph node; move
  mechanics to registers/ephemeral.
- **A5 — name the irreducible primitive set** (partially done): TEST-absent, `MEMBER`, `OVERLAY` are
  named ops; still Python: skolem re-finding (`_find_skolem_witness`) and sub-demand raising (a driver
  step in `_round`). Write the closed list down in `reference/isa_reference.md` when it stabilizes.
- **Axis A side item (user's call):** `DROP_CTRL` goes raw; fact/control deletion policy moves above
  the mechanism.
- **Linked subgoal chain** (Axis B "later"): parent→child in-graph pointers so `explain` walks the
  negative's decomposition.
- **pystrider #8c — id-addressed RETRIEVE surface:** "who realizes X" as a **RETRIEVE `<call>` mode**
  (like CHECK/CHOOSE/SUPPOSE in `mode_calls.py`), NOT a `who()` Python helper. Not started.
- **VISION-CLEANUP: get-or-create plumbing should EMIT `MINT`, not poke the substrate** (tagged
  `TODO(vision-cleanup)` in-source): `dispatch._ensure`, `mode_calls._ensure`, `focus._entity_node`.
  Principle ratified: every *semantic* (interning, dedup) is an ISA instruction/program; `add_node`/
  `add_relation` are the dumb loader. ✓S per site (mechanical); ⚠Opus for the "does ALL firmware
  minting become emitted `MINT`" scope call.

## Residuals carried out of done phases (don't lose these)

- **`same_as propagates through X` CNL surface** (from Phase 3.1-step1) — needs coref rules reified;
  `coref_prop` is forward-compatible. Lands with Phase 3 rules-as-data. Also the mechanism half of the
  Phase 5.4 residual below.
- **APPLY-body graded α-cut + inverted ('not at all') cut** (from Phase 5.2 companion) — the CHAIN half
  is DONE (`chain._graded_ok` → now the ephemeral `GRADE` program); the APPLY-body match-time cut
  remains. ⚠Opus.
- **`session.py:CONTENT_PREDS` + Python-generated coref rules** (from Phase 5.4 residual) —
  harness-side; resolves once coref rules reify (bank-authored `same_as propagates through X`).
- RETIRED / not carried: Phase 5.1's "aggressive `is_not` completion" (replaced by demand-driven NAF);
  Phase 2.2's "Phase-6 reader flip" (landed in Phase 6.0); the coref `canonicalize` deletion follow-up
  (already deleted along with `wire_same_as` — interning at the CNL reader replaced them, see
  `attic/indexing_and_coalescing_design.md`).

## Phase 8 — CLIENT: unified CNL intake + focus + streaming (ENGINE SIDE COMPLETE 2026-07-16 — residuals only)

> The first UGM *client* is an **agent loop with a TUI**, driven by CNL (the NL→CNL SLM is external;
> the system boundary is CNL). Load-bearing goal: **seamlessness** — the utterance's own structure
> drives the loop, NO intent-recognition dispatcher. Full spec: **`design/cnl_intake_design.md`** —
> its §8 build map shows every substrate row BUILT; what remains of Phase 8 is the CLIENT itself
> (queue item 1 above, in `harneskills_new`). The slices below are non-blocking residuals.
> Anaphora (8.4) is OFF the roadmap (boundary concern, SLM-side).

**INTAKE-SPINE DISCIPLINE (anti-hardcoding — any session on Phase 8 MUST obey; reviewers reject diffs
that break one).** Full list: `design/cnl_intake_design.md` §D. In brief: (1) route by which FORMS
fired, never by sniffing the utterance string; (2) focus moves are CNL forms; (3) pronoun ranking is
DECLARED defeasible-priority data; (4) rejection/"nearest forms" computed from recognition structure;
(5) `<focus>`/`<query>`/`<goal>` are control tokens via the `<…>`→control chokepoint; (6) no predicate/
English-word STRINGS as control signals in intake code; (7) metareasoning owns only effort/margins.
Litmus: grep intake code for a domain or function word used as a control signal — if one is
load-bearing, it belongs in a bank.

Remaining slices:

- **8.5b tail:** TRUE wall-clock trace interleaving (a live `_record` callback needs coroutine
  reasoning — the generator can't yield from inside the synchronous chain; the control machine's
  `SUSPEND` may now be the mechanism); extend mid-chain gather to who/∃/n-ary questions (v1 covers the
  yes/no-bound path); lazy (relevance-ordered) instead of eager frontier asking.
- ~~**8.5 async wiring**~~ **DONE 2026-07-16:** the GOAL/COMMAND route landed (`form.goal`-minted
  `<goal>` triggers `intake._act_loop`); async tools suspend through `service_calls_cm` as `"call"`
  events (wait-set = `{ask, call}`); §4a nearest-forms rejection computed from the banks; persistent
  `<goal>`/`<call>` scaffolding gets focus-reachability GC (`focus.gc_cold_scaffolding` on narrowing
  moves). ENGINE SIDE OF PHASE 8 COMPLETE — see `design/cnl_intake_design.md` status + §8 build map.
  Remaining Phase 8 work is CLIENT-side (TUI+SLM in `harneskills_new`, consuming the
  `converse`/Event/Outcome contract — UGM owns the contract, user decision 2026-07-16).
- **8.6 perf follow-on:** INCREMENTAL head-index extend (today `_reify_rules` rebuilds per `ask_goal`;
  correctness already right — a new/disabled rule takes effect immediately).
- **Wildcard-closure re-entry (perf lever (b), wire when it bites):** `chain_sip` re-entry redoes the
  closure for a WILDCARD/whole-session goal (bound queries are cheap and focus subsumes the common
  interactive turn — measured 2026-07-14). Fix when wildcard-streaming latency matters: persistent
  tabled frontier / semi-naive delta ACROSS calls via the memo-table-in-`AttrGraph.registers`; the
  control machine's `Continuation` is the mechanism. Differentially gated.

**Model routing for Phase 8:** ⚠Opus for the async/streaming driver work (vision judgment); ✓S for
mechanical parts under the design spec.

## Secondary / parallel tracks

1. **Phase 5 exit gate — bench-sensibility half (harness-side).** Run card-trader + coref + full
   ProofWriter-coverage in `harneskills`. The engine half is MET in-repo (audited 2026-07-11). If a
   bench relying on a domain predicate composing across coref regresses, DECLARE the relation in the
   harness KB — do NOT re-add an engine string.

2. **Phase 3 remaining (rules-as-data / homoiconicity — off the critical path).**
   - ~~3.1 step 2 (one-graph fold)~~ **DONE 2026-07-14** (firmware-over-ISA arc, `PATTERN_MARK`).
   - **3.4:** collections as first-class KB structure: member `next`-chains + list-authoring CNL forms
     (the ITERATE substrate — `reference/processing_modes.md` §1). ⚠Opus. ABSORBED into the
     PROCEDURES arc (Current-focus queue item 3, `design/procedures_design.md`) — step lists
     are its driving workload.
   - Exit gate: every bank rule round-trips CNL → rule subgraph → rendered CNL.
   - NOTE: meta-circular FORM-rule authoring (the quote/eval wall) — RESOLVED 2026-07-16: the
     wall needs no new machinery (rule-source CNL already expresses forms; finding recorded in
     `design/form_authoring_design.md` §1). The authoring surface is **Phase 9 (CNL form
     authoring)**, item 2 of the Current-focus queue; FULL bank reification was cut (design §6)
     and stays a parked, proven path.

3. **Program-as-data homoiconicity** — the wider frontier the firmware arc opened: programs the
   machine runs, represented in the graph it runs on (seed-from-focus is already in-machine as
   `MEMBER` over `registers["<focus>"]`; value operands generalize by "just change the lowering
   program" — `attic/isa_value_operands_design.md` §6). Phase 9 is its first concrete slice
   (rules-as-data was the zeroth); the rest stays design-track (⚠Opus).

## Phase 7 — PERFORMANCE track (after correctness — user standing rule)

In leverage order:
- **(a)** Intern keys/values to ints, CSR adjacency, bitset candidate sets. **The LOW-RISK first rung,
  in PURE PYTHON** (dispatch-table `_match_step`, int-interned keys, array/`__slots__` register states).
  Likely 2–3× at near-zero risk. Do this BEFORE (b) if perf bites. ✓S for mechanical rungs with
  benchmarks; ⚠Opus for design. NOTE: for the agent-loop client the axis that matters is session
  accretion (answered by seed-from-focus), not total-KB size — don't start 7a for the client's sake.
- **(b) → Phase 7b: Rust core, Python surface.** ⭐ FULL PLAN: **`design/rust_engine_plan.md`**.
  STRATEGY (user-ratified): procedures became ISA FIRMWARE first (Phase A — now DONE, 2026-07-14), so
  Phase B ports ONLY the interpreter — the procedures come along as DATA both interpreters run.
  MEASURED CONSTANT: match inner loop ~381× (`bench/rust_pilot/`). GUARDRAILS: perf NOT the current
  bottleneck; Rust = CONSTANT, focus = CURVE; Amdahl-bounded; the Python engine STAYS the reference
  oracle, differential-tested; FREEZE the ISA first. Start only when a real target-scale workload is
  too slow AND (a) is exhausted. ✓S for the mechanical slices under the differential gate.
- **(c)** Per-rule AOT codegen = partial evaluation of APPLY (Soufflé-style), differentially gated.
- **(d)** Two-tier execution for runtime-edited rules — fresh rules interpret, stable-hot rules compile
  in background, version-stamp invalidation on edit. JIT only if profiling demands it.
- **Perf levers (b')(c') from the demand-negation work** (query already sub-second at session scale):
  semi-naive worklist so a demand re-services only when a relevant fact appeared; the domain coref
  `same_as.*.is` demand fan-out (bounded by focus in practice). ALSO: `why` provenance is
  order-sensitive (a fact pre-derived without provenance renders `(given)`).

## Placeholders / optional follow-ons (not concrete tasks)

- **Broader FirmwarePolicy stance surface** — no third opinion is pending. Candidates ONLY if a
  workload needs one: CHOOSE tie-break / always-provenance `why` / default α-cut.
- **Prose `suppose … predict …` sugar** folding to the reified encoding (new surface → SLM debt).
- **`tests/test_joern_corpus.py`** — legitimately slow, live-Joern; candidate for a `slow` marker.

## Model routing

⚠Opus = needs vision-judgment; ✓S = Sonnet-safe where a gate/spec catches deviation.
- Phase 8 async/streaming driver work: **⚠Opus**; mechanical slices under spec: **✓S**
- Phase 7(a): **✓S** with benchmarks for mechanical rungs; **⚠Opus** for design + AOT codegen
- Phase 3.4 collections; program-as-data design: **⚠Opus**
- APPLY-body α-cut + inverted cut: **⚠Opus**
- Vision-cleanup MINT-emission sites: **✓S** per site; **⚠Opus** for the scope call

## Risks

- **Session accretion is the client's real perf risk** (`critique.md` §4.1a), NOT total-KB size.
  Answered by seed-from-focus (8.3b) and validated by the probes; re-validate if the client workload
  changes shape.
- **Habitability at the CNL boundary** (`critique.md` §4.4) — an unrecognized utterance must be an
  actionable rejection, not a dead end. Handled by unified intake; keep it true as forms grow.
- **Performance (Phase 7) is the long-pole for the GENERAL engine**; for the client it is reframed as
  session accretion. Correctness risk is < 5% impossible-blocker.
- **SLM surface debt** accumulates from CNL form changes — batch retrains via the ledger in
  `harneskills` (`handoff_slm_surface_track.md`).
- **Meta-debugging** — the Phase 4 trace renderer is the mitigation; it is complete.
