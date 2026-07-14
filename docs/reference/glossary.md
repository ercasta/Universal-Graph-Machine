# Glossary — the project vocabulary

> **Status: REFERENCE (2026-07-14).** The invented/repurposed terms, alphabetical. Each entry gives
> the one-sentence meaning and the home doc/module. Terms marked † are HISTORICAL — they name
> retired mechanisms you will meet in the changelog/attic, not in the code.

- **α-cut** — a graded threshold: a condition/choice passes iff its degree ≥ α. In rule bodies via
  degree adverbs (`GRADE`), in CHOOSE as the argmax cut. (`reference/logic_fragment.md`)
- **agenda** — the demand solver's per-frame worklist of pending subgoals; execution state, lives in
  a driver-owned `_Frame`/register, never the graph. (`chain.py`)
- **assumed-no** — the CWA verdict for an unprovable goal: a *defeasible* no (absence of evidence),
  as opposed to the hard **entailed-neg**. (`check.py`)
- **AttrGraph** — the substrate: label-less nodes (opaque id + attribute bundle) and bare directed
  edges; the ONE kind of thing. (`attrgraph.py`, `architecture.md` §1)
- **bank** — a list of `Rule`s loaded from CNL, run to fixpoint by `run_bank`; domain knowledge and
  policy live ONLY in banks (never Python).
- **bound literal** — a rule token `name?` that binds to THE node named `name` (every occurrence in
  the rule is the same node); the machine-grammar's constant. (`production_rule.py`)
- **ById** — an endpoint wrapper pinning a goal/write to a specific node id instead of a name;
  the id-addressed API. (`chain.py`)
- **centers** — the entity names a focus frame points at; the seed set for focus attention.
  (`focus.py`)
- **CNL** — the controlled natural language; the system boundary (the SLM translates NL→CNL).
  Surface: `reference/cnl_reference.md`.
- **control layer** — non-monotone scaffolding (tokens, frames, `<…>` nodes) freely mutated, vs the
  monotone **fact layer**; since the firmware arc, control-ness is a MARKER ATTRIBUTE, not a
  substrate flag. (vision §5)
- **ControlMachine** — the control path: a PC over labeled basic blocks with
  `BRANCH/BRANCH_IF/CALL/RET/SUSPEND/HALT/SETI/DEC/PRIM`, layered on the untouched `Machine`.
  (`reference/isa_reference.md` §control path)
- **continuation** — a suspended `ControlMachine` (PC + registers + control stack) that `RESUME`
  re-enters; how async tools and NAC subgoals wait. (`machine.py`)
- **coref class** — the set of mentions linked by `same_as`; instructions aggregate over it when a
  name is used as an operand.
- **CWA / OWA** — closed/open world assumption; the stance's `negation_default` with per-predicate
  exceptions. (`policy.py`)
- **degree adverb** — a declared word→number mapping (`very is 0.8`) driving graded writes and
  α-cut conditions; KB data, not config. (`authoring.py`)
- **demand** — a bound `<demand>` node (predicate + bound endpoints) recording "this subgoal is
  wanted": the magic set made literal graph structure. Its chain is a negative's provenance and
  stays in the graph. (`chain.py`)
- **driver** — thin Python orchestration around the interpreter (`run_bank`, `chain_sip`,
  `ingest`); loops rounds and manages agendas, contains no matching/binding logic.
- **entailed-neg** — the hard no: a derived `is_not` fact (e.g. from disjointness), trusted like a
  yes. (`check.py`, `universal.py`)
- **fact layer** — the monotone half of the graph: facts are never deleted by reasoning (only the
  privileged retraction driver deletes, with history).
- **firmware** — the reasoning procedures (CHAIN/CHECK/CHOOSE/SUPPOSE/…) expressed as ISA programs
  + thin drivers; the system's replaceable "psychology". (`reference/firmware_reference.md`)
- **focus** — the discourse working set: a stack of frames (in `AttrGraph.registers`), whose top
  centers bound attention (`MEMBER` live-set) so per-utterance cost tracks the focus, not the
  session. (`focus.py`)
- **forms** — the acceptance grammar: normalization rewrite rules over the token chain
  (surface → canonical), never an imperative parser. (`forms.py`)
- **frame** — (a) a goal-closure execution unit in the demand solver (`_Frame` + a ControlMachine
  program); (b) a focus stack entry. Context disambiguates.
- **fuel** — the bounded-effort budget; exhaustion yields UNKNOWN honestly (bounded-defeasible
  semantics, "agent, not theorem prover").
- **GRADE / VMATCH / DISTINCT** — the value-test instructions: graded threshold, value-match join,
  distinctness — run as ephemeral programs on both engines. (`machine.py`)
- **graded vs valued attribute** — the two attribute kinds: a membership degree in [0,1]
  (`dog: 0.8`) vs open-domain data under a key (`name="paul"`). (`attrgraph.py`)
- **head index** — graph structure (`<head-index>` hub) mapping head predicate → rules producing
  it; how demands find relevant rules. (`apply.py`)
- **ink / pencil** — committed monotone facts vs scoped hypothetical writes (SUPPOSE scopes);
  CONFIRM inks, REFUTE drops the scope. (`suppose.py`)
- **inert** — marker attribute for provenance/meta nodes that fact reads must skip; enforced by the
  compiler-emitted guard, not a matcher mode.
- **intake** — the unified CNL entry: routes fact/rule/question/focus/rule-control/unrecognized by
  which FORMS fired (never string sniffing); streams events. (`intake.py`)
- **interning (mentions)** — the CNL reader's "same name ⇒ same node" coalescing of
  `<mention>`-marked entities at ingest. (`forms.intern_mentions`)
- **ISA** — the instruction set: the data-path opcodes + control transfers; the CONTRACT a Rust
  interpreter would re-implement. (`reference/isa_reference.md`)
- **live-set** — a register-pointed set of nodes restricting (`MEMBER`, focus) or extending
  (`OVERLAY`, scope pencils) a read's candidates; contents = policy, membership test = mechanism.
- **lowering** — compiling a `Rule`/read into an ISA program (`lower_conj`, `assemble_facts`,
  `guard_inert`); the compilers are allowed to know conventions, the machine is not. (`lowering.py`)
- **machine rules** — the formal control-rule surface (`H and drop S P O when B and not C`), vs the
  prose surface; one shared body grammar. (`machine_rules.py`)
- **magic set** — classic Datalog demand propagation; here literal: the `<demand>` nodes ARE the
  magic set.
- **marker attribute** — an ordinary attribute (`CONTROL_MARK`/`INERT_MARK`/`PATTERN_MARK`) whose
  meaning is emergent from the rules/guards that select it — the no-privileged-partitions model.
- **mention** — a surface entity occurrence, marked `is_a <mention>`; marking (what is an entity)
  is separate from deciding (coreference).
- **mode** — one of the CLOSED inventory of nine computation shapes (SATURATE, ITERATE, CHAIN,
  CHECK, CHOOSE, SUPPOSE, WALK, CALL, RECORD); new modes must pass the acceptance test.
  (`reference/processing_modes.md`)
- **NAC** — negative application condition: a rule's `not S P O` conjunct; solved by NAF at demand
  time. **NAF** — negation as failure: raise the positive subgoal, absence decides.
- **one-graph fold** — rules living in the same graph as facts (`PATTERN_MARK` keeps pattern-space
  out of the fact view); a separate bank is the consumer's `rules=` choice.
- **operand node** — a regular interned node carrying `<isa_operand_value>="…"`, standing for a
  literal value in a register (registers hold only node-pointers).
- **provenance** — the in-graph `<j:rulekey>` justification records (`proves`/`uses`) minted per
  derivation; what `why`/trace read. A negative's provenance is its demand chain.
- **registers** — the second home (vs the graph): `State.regs` = per-match bindings,
  `AttrGraph.registers` = the control-register file (focus stack, …); invisible to matching.
- **RETIRE / history** — the privileged fact-deletion opcode + the inert `<history>` pre-image
  record; copy-on-delete retraction with surviving explanation. (`retraction.py`)
- **rule variable words** — the NL surface of a universal's bound variable: `someone/they` → `?x`,
  `something/it` → `?y`, plus declared words.
- **same_as** — asserted/derived cross-name identity (a fact reasoning follows); NOT the same-name
  default (which is interning).
- **scope** — a `<hypothesis>`/SUPPOSE pencil region; reads extend visibility onto it via
  `OVERLAY`.
- **seed-from-focus** — bounding a query's fact reads to the focus centers: the session-accretion
  answer (flat curve). Also **seed-from-ground**: matching starts at bound/ground positions, free
  variables are destinations.
- **SIP** — sideways information passing: ordering body atoms so bound endpoints flow into the next
  atom's seed. (`chain._sideways_order`)
- **skolem** — a bound-literal head token (`s2?`) minting one node per LHS match, re-found
  structurally by its defining relations (LHS-keyed; RHS-only `?x` heads are rejected).
- **SLM** — the small language model at the ONE boundary (user NL → CNL); owns anaphora and
  same-name judgment calls the substrate refuses.
- **stance** — the firmware's declared opinions (`FirmwarePolicy`: negation default, on_cycle);
  data, not forked Python. (`policy.py`)
- **stratification** — the load-time layering that makes NAF sound; a negation cycle is rejected
  (or degraded) at load, never silently answered.
- **substrate** — the AttrGraph + its dumb storage API; "physics". Everything above it that
  carries meaning is attributes + rules.
- **tools / calculators** — the §8 escape hatch: `<call>` nodes serviced by the dumb dispatcher
  (arithmetic, tokenizer, SLM, …); sync inline, async via SUSPEND/RESUME. (`dispatch.py`)
- **two-phase match-then-apply** — the `Machine`'s execution model: matching never mutates; effects
  apply after. (`reference/isa_reference.md`)
- **verdict** — CHECK's 4-status answer: POSITIVE / ENTAILED_NEG / ASSUMED_NO / UNKNOWN;
  `collapse()` folds to yes/no/unknown.
- **walker †** — the retired Python long-range demand primitive (`walker.py`, deleted Phase 6.1);
  survives only in attic docs and old changelog entries.
- **why** — the explanation renderer over provenance (`explain`, `render_demands`).
