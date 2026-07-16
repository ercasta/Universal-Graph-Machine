# CNL form authoring — Phase 9 design (RE-SCOPED 2026-07-16, ratified)

> **Status: DESIGN, ratified scope — build by §5.** This file supersedes the first draft
> (`forms_as_kb_data_design.md`, deleted same day): the original "migrate every form bank into
> KB-resident reified rules" scope was CUT after user discussion — see §6 for the decision
> record. What remains is the part with a capability behind it: **the grammar becomes
> extensible from the outside, in CNL.** Read after: `vision.md` §3/§8,
> `design/cnl_intake_design.md` (§D discipline, §4a habitability), `cnl/machine_rules.py`.

## 0. What this arc is, and is not

The seam question that opened Phase 9: *"are we subtly reintroducing hardcoded parsing?"*
Decomposing the original arc's claimed benefits gave the honest answer:

- The recognition MECHANISM is vision-true (forms are `Rule`s the one engine runs; routing is
  by what fired). A Python list of `Rule` literals is declarative DATA to the lowering — not a
  parser.
- The Rust boundary was already final: `Rule` lists (data) → lowering (Python surface) → ISA
  (contract). Moving banks from `.py` to pattern-space moves nothing Rust cares about.
- Habitability (nearest-forms, keyword lint, `form_keywords`) derives from `Rule` STRUCTURE,
  not from where rules live.
- The only capability Python-hosted banks actually block is the machine reasoning about its
  own grammar in-engine — **ruled out by the user 2026-07-16 ("not even a hypothesis in a
  remote future")**.

What IS missing today: a user or a domain KB file cannot add a sentence SHAPE without editing
Python. The lexicon reified long ago (`R is a relation`, `V is a verb`, degree adverbs,
auxiliaries — all declarations); the grammar did not. **This arc closes exactly that gap and
nothing else.** The fundamental banks stay Python — frozen in practice, and reifying frozen
working code behind a differential gate that proves nothing changed is the
equivalence-with-the-old-generation trap in new clothes.

## 1. The enabling finding (kept from the first draft)

**Rule-source CNL already spans the form language.** The machine grammar
(`machine_rules.MACHINE_RULE_FORMS` + the shared body spine) accepts ANY token in S/P/O
position — variables `?x`, bound-literals `is?`/`a?`, control bound-literals `<query>?`,
plain literals `first`/`next`/`yes` — with multi-clause heads, `drop`, `not`, `!=`. And
`lowering._nac_groups` makes NAC pats independent groups unless joined by NAC-local free
variables, so the guard-NAC idiom the shipped forms use is expressible as separate `not`
clauses. A recognition form is therefore ONE machine-CNL line over the token-chain
vocabulary; no new quoting machinery exists or is needed — the fold writes rule-source
structure, `expand_rules` reflects it, same as every rule today.

(Corollary, parked: full bank reification remains a proven path — `write_rule` /
`rules_in_graph` round-trip the fragments — should a workload ever demand in-engine grammar
reasoning. Nothing rots by deferring it; see §6.)

## 2. The authoring surface

**[D1] `form KEY : HEAD when BODY`** — one new form in the rule-source grammar. Anchored to
the sentence's first token (`form?` leads, the same disambiguation idiom as `goal`/`every`),
it folds `rl_key` onto the rule node; everything after the `:` is the existing machine
grammar, unchanged. `expand_rules` uses `rl_key` when present (digest key otherwise — this
also closes the stable-key gap for any future machine-rule needs). Example:

```
form ask.costs : <query>? qtype yesno and <query>? q_s ?qs and <query>? q_p costs
and <query>? q_o ?qo when ?s first does? and does? next ?qs and ?qs next costs?
and costs? next ?qo
```

**[D2] Where it is recognized: everywhere CNL is** — a live intake utterance, or a line in a
loaded KB file. Under the multi-KB-files model (user-ratified in the D2.2 discussion), a
domain file ships its own sentence shapes as leading `form …` lines; **load order is
semantic, strictly declare-before-use**: a line is parsed by the grammar active at that
moment (identical contract to a live session — files are batched utterances). A line using a
form that arrives later is UNRECOGNIZED, loudly, with nearest-forms. No re-offer fixpoint.

**[D3] Where an authored form lands: routed by its own structure (§D-compliant).** A form
whose head mints `<query>`/`<qevent>` joins the question bank; one producing content
relations joins the declarative bank — inspected from the folded RHS, never from a keyword
list. Authored forms run AFTER the shipped bank they join; the existing specificity idiom
(anchoring, NAC deferral) resolves overlaps. An explicit placement surface is deferred until
a concrete pre-emption case appears.

**[D4] Persistence is the CNL line itself.** A session's grammar delta persists as its
`form …` (and `disable …`) lines in the transcript / KB file, replayed at load. No reified
storage, no bank chains, no version stamps in the graph.

**[D5] Key semantics (now load-bearing under multi-file loading):** same key + identical
folded `Rule` → idempotent no-op; same key + different `Rule` → loud error at file load, a
conversation at live intake (the existing rule-conflict machinery, generalized). Disable is
`rule_control` by key — it already works over Python-hosted rules, so shipped and authored
forms are uniformly disable-able with zero new machinery.

## 3. Safety and habitability

- **Recognition-safety lint (new):** an authored form's LHS may read ONLY token-chain
  scaffolding (`first`/`next`/`SCAFFOLD_PREDS` tags) and bound literals. A "form" whose
  conditions match fact structure would be a domain rule firing at recognition time — reject
  loudly at fold. (RHS is unrestricted: writing canonical relations onto content tokens IS
  what a form does.)
- **Existing loader lints apply unchanged:** malformed-clause defects, RHS-only head vars.
- **Habitability carries over structurally, not by porting:** `form_keywords`,
  `_nearest_forms`, `_kw_in_name_slot` consume the assembled `Rule` lists — the only work is
  making sure authored forms are IN the lists those readers receive (they join the same
  banks recognition runs).
- **Memo correctness:** `_RECOGNIZED_QUESTIONS` / `_PARSED_BANKS` key on text + static banks.
  A session with authored forms must not serve stale memos: key the recognition memo on a
  session grammar-version counter (a plain int in `kb.registers`, bumped per authored/disabled
  form) — the one small survivor of the old design's version register.

## 4. Exemplar sugar (optional follow-on)

`a why question looks like why is ?s ?o` — the exemplar's token chain after `looks like` IS
the LHS (literal words → bound-literal keywords, `?vars` → slots, anchored at `first`); the
declared question type names the RHS template; slot mapping by variable-name convention
(`?s`→`q_s`, `?p`→`q_p`, `?o`→`q_o`). Question and fact exemplars only; arbitrary RHS stays
Tier 1 (§2). Build only after Tier 1 proves out — it is a convenience, not a capability.

## 5. Slices + exit gate

- **Slice A — the grammar — DONE 2026-07-16 (554 green):** `cnl/form_authoring.py` —
  `FORM_HEADER_FORMS` prior stratum + `mrule.start` NAC on `form_hdr`; `rl_key` in
  `expand_rules`; `lint_recognition_safe`; `merge_forms` (D5). Proven end-to-end through the
  existing `extra_forms=` hook (`tests/test_form_authoring.py`).
- **Slice B — the plumbing — DONE 2026-07-16 (567 green):** intake FORM route (new
  `Outcome`/`Event` kind `"form"` + `"form-conflict"` wait-point, routed by
  `parse_form_line` — the header form firing, never a string sniff); RHS-structure bank
  placement (D3, `is_question_form`); nearest-forms + `disable that rule` coverage of authored
  forms; `session_forms` in `kb.registers["forms"]`; `load_kb` (declare-before-use). NOTE: the
  planned MEMO VERSION COUNTER proved UNNEEDED — session-authored forms take the `extra_forms=`
  path, which already bypasses the static-banks memo (`_parse_question`), and the empty-grammar
  case leaves every path byte-identical. Fixed en route: `anchor_has_content_fact` now takes a
  `since=` snapshot so an unrecognized line mentioning already-related entities doesn't misroute
  as a fact. `tests/test_intake_forms.py`.
- **Slice C (optional) — exemplar sugar** (§4). Not started.

**Exit gate (capability-shaped) — MET 2026-07-16 (Slices A+B):** a domain KB file declares a
new sentence shape in CNL; facts and questions in that shape parse and answer; nearest-forms
suggests it; `disable` covers it; **no Python edited**. Book: a short section in the authoring
chapter (still owed), not a rewrite of ch. 7/15.

Model routing: Slice A/B mechanical under this spec (✓S) except the intake-route judgment
calls (⚠Opus for D3's placement edge cases); Slice C ⚠Opus.

## 6. Decision record — what was cut, and why (2026-07-16)

The first draft scoped Phase 9 as full forms-as-KB-data: migrate every shipped bank to
KB-resident reified rules (`banks/*.cnl`, bank member-chains, pipelines-as-data, a
self-hosting kernel artifact, per-bank differential gates, a "zero `Rule` literals in `cnl/`"
exit gate). CUT in user discussion, because its benefits decompose to:

1. extensibility → delivered by this thinner arc without touching the shipped banks;
2. the Rust data/interpreter boundary → was already final (`Rule` lists are data);
3. habitability/inspectability → already derived from `Rule` structure;
4. in-engine grammar metareasoning → the ONLY thing genuinely requiring reification, and the
   user ruled it out ("not even a hypothesis in a remote future").

The shipped banks are frozen in practice; migrating them is converting working code into
equivalent data behind a gate that proves nothing changed — the same shape as the
equivalence-target trap ratified against on 2026-07-10. Consequences of the cut: the "Phase 9
before 7b" ordering constraint DISSOLVES (Rust is unblocked whenever perf bites); collections
(3.4) is decoupled from this arc; `Q9.1/Q9.2` (pat-order sensitivity, GC of bank fragments)
are moot — nothing new lives in the graph. If in-engine grammar reasoning ever becomes real,
§1's finding + the existing `write_rule`/`rules_in_graph` round-trip are the revival path.
