# The register-machine proposal vs. the current harneskills system

> A comparison of the "graph low-level machine" idea (`conversation.md`) against the
> system as actually built (`docs/architecture.md`, `docs/vision.md`, `harneskills/rewriter.py`),
> written 2026-07-05.
>
> **Reframed 2026-07-05 (see `rule-isa-design.md`).** Two follow-up discussions clarified
> the idea: the ISA sits **below** the rules (rules stay the authoring surface and the home
> of semantics — the machine only *runs* rules), the working-set bound is a *decomposition*
> device (more steps, same result — never lossy), and the goal is **design tractability, not
> speed**. Also: **NACs are gone at the vision level** — negation is materialized as a
> positive `is_not` fact, so the machine has no `CHECK-ABSENT` opcode. Under that framing two
> objections below were overstated; the affected sections (Tension A, Tension B, addition #4,
> Recommendation) carry corrected notes, and the full corrected treatment is in
> `rule-isa-design.md`.
>
> **UPDATE (2026-07-14).** The comparison below contrasts the ISA idea with the current system's Python
> control (`rewriter.run`, the fixpoint/subgoal/dispatch drivers). Those drivers are now themselves ISA
> programs: the machine gained a **control path** (`docs/isa_control_machine.md`, `isa-reference.md`
> §"The control path"). So the "the machine only runs a basic block; Python does the control" reading
> below is superseded — `run_bank`'s fixpoint, `chain_sip`'s subgoal recursion, and the `<call>`
> dispatcher now run as control-machine instructions (PC/`BRANCH`/`CALL`/`RET`/`SUSPEND`/`PRIM`).

---

## TL;DR

The proposal reads as a *reconstruction from prior art* of an architecture you have
**already largely built by a different route.** Roughly 70% of what the conversation
proposes — incremental RETE-style matching, bound-driven (WAM/magic-sets) evaluation,
the monotone-assert / non-monotone-retract split, an explicit position on the
descriptive-complexity ladder, a separated gradable-attribute layer, and
instruction-trace-as-explanation — is present in the current engine, arrived at
independently and for the same reasons.

The genuinely *new* ideas in the proposal are two. In the *first* draft of this doc they
read as tensions with the founding commitments; the 2026-07-05 reframing (see the note
above and `rule-isa-design.md`) softens both substantially:

1. **A compile step from rules to a low-level ISA.** Read as a `CNL → IR` seam this
   violates `vision.md` §2/§3. But the ISA sits *below* the rules (which are already
   downstream of CNL), not between the text and the reasoning — and lowering a rule to
   visible primitive steps is *more* homoiconic, not less, if the instructions are graph
   nodes (`rule_graph.py` already round-trips rules as nodes). So this is not the forbidden
   seam; it is the reasoning's own micro-structure. See Tension A (corrected).
2. **A capacity-bounded working set / register.** Read as the retired hop-radius cap this
   loses derivations. But the intended bound is a *decomposition* device — a match too big
   for a register becomes *more instructions, same result* (the RISC / binary-join floor),
   never a lossy runtime gate. It does not touch the index-driven, disconnected-mention
   matching. See addition #4 (corrected).

The honest caveat that *does* survive is the framing one: the **Fifth-Generation lesson**.
If the ISA is sold as *speed*, it aims at a constraint that is not binding — your findings
(`finding_coverage_composition_audit`: 61.5% real-bug recall; the frontier moves by
*general rules and premise classes*, not match speed) say coverage/expressiveness is the
wall, not throughput. The reframing answers this too: the ISA's value is **design
tractability, not speed** — an explicit operational semantics, a testable machine/rule
boundary, illegal-states-unrepresentable invariants, and the ability to reason *formally*
about expressiveness. Those accrue independent of throughput. So the recommendation shifts
from "harvest only the static-analysis parts" to "**also** run the cheap spec-first ISA
experiment" (see Recommendation, corrected).

---

## The mapping: proposal concept → current status

| Proposal concept (`conversation.md`) | Current status | Where it lives now |
|---|---|---|
| RETE incremental match; conflict set = small dynamic subset | **Have** | `rewriter.delta_matches` (semi-naive), `Rewriter._relevant` (anchor-delta activation), the `changed` frontier. The code literally comments "the incremental half of the Rete." |
| Registers hold *pointers*, not copies (WAM) | **Have (implicitly)** | Matching binds `dict[str, str]` = binding-key → node **id**. Node ids are pointers into the one `Graph`; nothing is copied. |
| Drive from bound columns, pass bindings on (WAM `get/put`, magic sets, SIP) | **Have** | Seed-from-ground (`rewriter._triples`, `_pos`): seed each pattern from its most-selective *ground* anchor via the lexical index; free vars are destinations only. `vision.md` §11 names this "magic-sets / sideways-information-passing." |
| COMMIT split: monotonic assert vs non-monotonic retract | **Have (load-bearing)** | The two-layer split — monotone fact layer / non-monotone control layer (`vision.md` §5). Reasoning never deletes; only token-gated control edges are deleted; the linter enforces it. |
| Descriptive-complexity ladder (FO / Datalog-PTIME / stratified / ASP-NP) | **Have (positioned)** | `vision.md` §11: monotone forward chaining = Datalog/PTIME; **stratified negation only** (cyclic NAF *refused*, `stratify` raises); non-monotone control = Turing-complete with `max_steps` as the deliberate backstop (§12.6). |
| EVALUATE: gradable attributes as a *separate* instruction class | **Have** | The graded layer (`vision.md` §13): embeddings, α-cut, `rewriter.graded_degree`, declarative `rule.propagate`. Already separated from the boolean structural core, exactly as the proposal argues for. |
| ASP / clingo as the non-monotone escape hatch | **Have (as a tool)** | `harneskills/asp.py`; clingo used as a scoped `<call>` calculator, not the core reasoner (per memory `decision_agentic_direction`). |
| Instruction trace = explanation trace "for free" | **Have (different realization)** | In-graph provenance: each firing materializes `<j:KEY> --proves--> C`, `--uses--> Pi` (`provenance.py`, `rewriter.apply_rule`). `explain` traverses these. The explanation payoff already exists. |
| Transitive-closure / bounded-fixpoint instruction | **Have (as control tokens)** | Walkers: fuel-bounded traversal tokens (`walker.py`, `corpus/walker.cnl`). "Think harder" = more fuel (`vision.md` §11/§14). |
| Chunking / salience / effort budget = "think harder = bigger N" | **Have (as a named layer)** | The metareasoning layer (`vision.md` §14): content-blind df-selectivity, α-cut, fuel, fire counts. Explicitly the boundary that keeps the smart planner out. |
| Working-set gates which rules are candidates (ACT-R buffers) | **Partial** | `rewriter.near_rules` (rules a ground locus would seed) + walkers give per-position rule sets. But this is *not* a capacity bound — the current system reaches disconnected mentions through the index on purpose. |
| Node-sharing / superinstruction fusion across rules | **Absent** | Each rule is matched independently every step; there is no compiled, shared join network across rules. Genuine performance opportunity. |
| Compile rules to a low-level ISA (LOAD/TRANSFORM/EVALUATE/COMMIT) | **Absent** | Rules are *interpreted directly* by the generic `run()` loop over `Pat` triples. There is no compile step and no instruction stream. This is the core of the proposal and the biggest architectural addition. |
| Bounded register sizing via treewidth / GYO / Yannakakis | **Absent (partly moot)** | No register abstraction and no per-rule width analysis. But the runtime *already* joins pattern-by-pattern (RETE's binary-join floor), so it is already at "the practical floor" the proposal recommends. |
| Static rule-dependency reachability (the real XCON fix) | **Absent (building blocks present)** | No "rule A writes predicate X, rule B reads X ⟹ A→B" dependency graph. But `_rule_anchors` / `_anchor_names` already extract each rule's *read* predicate names for activation — half the graph is already computed. |

---

## Where you have already converged (and why that's the signal, not the noise)

Four convergences are worth stating plainly, because they mean the proposal is
*validating* the current direction rather than redirecting it:

- **The COMMIT split is the same insight, load-bearing on both sides.** The proposal
  says: split COMMIT into monotonic assert vs non-monotonic retract, because that split
  "determines the complexity class." The current system's *entire* discipline is that
  split — the monotone fact layer vs the non-monotone control layer — and it is the one
  deliberate seam the vision keeps (`vision.md` §5). The proposal independently rederives
  your most load-bearing partition.

- **Seed-from-ground *is* the WAM/magic-sets idea.** The conversation frames WAM as
  "compile-time specialization: drive from the bound arguments." The current matcher does
  exactly this at runtime via the lexical index and df-selectivity — the difference is
  *interpreted per step* rather than *compiled once per rule*. That difference is the
  whole question in the "genuine additions" section below.

- **You already separated the boolean core from the gradable layer** — the proposal's
  EVALUATE class — and for the same stated reason: keep the gradable part from silently
  pushing the crisp core into a harder complexity class (`vision.md` §13; proposal §5).

- **Instruction-trace-as-proof already ships** as in-graph `proves`/`uses` provenance.
  The proposal sells this as a payoff of *going* to an instruction machine; you got it
  from making provenance a substrate citizen instead.

The lesson: the conversation is a good *external audit* — it confirms, from four
independent literatures (production systems, logic programming, database theory,
cognitive architecture), that the core decisions are sound and have prior art. That is
genuinely reassuring, and it's most of what the exercise buys.

---

## The genuine additions, ranked by value-per-friction

### 1. Static rule-dependency reachability analysis — highest value, lowest friction

This is the proposal's *actual* answer to the XCON risk (memory flags this risk under
`decision_agentic_direction`: "rule-base growth outpacing your ability to keep
interactions comprehensible"). The idea: because rules compile to a small closed
vocabulary (here, `Pat(s,p,o)` triples over named nodes — not arbitrary Lisp), you can
statically build a graph *rule A writes predicate X ⟹ rule B that reads X* and ask
"can A ever transitively affect B" as a decidable query.

Why it's the best first harvest:
- **Content-blind** — it reads rule structure (predicate names on LHS vs RHS), never
  node meaning. It sits cleanly inside the metareasoning layer (`vision.md` §14) and the
  linter's remit (`lint.py`), no vision conflict.
- **Building blocks already exist.** `rewriter._rule_anchors` already extracts each
  rule's LHS literal predicate names (its *reads*). The mirror — RHS literal predicate
  names (its *writes*) — is a five-line function. The dependency edge is then a set
  intersection you already compute for activation.
- **It targets your *stated* scaling worry directly**, and it does so at design time,
  which is exactly where an untyped, homoiconic, self-modifying rule base most needs a
  guardrail.

Caveat for the untyped substrate: a "predicate" here is a relation *node name*, and the
same name can appear in many unrelated relations, so the dependency graph will be an
over-approximation (sound for "cannot interact," conservative for "might interact").
That's the correct direction for a safety analysis.

### 2. Per-rule treewidth as a compile-time cost/complexity label — cheap, informative

Run GYO/tree-decomposition over each rule's body once and stamp it with (a) which rung of
the ladder it needs (monotone? stratified NAF? escalates to the ASP tool?) and (b) a
join-chain-depth cost estimate. This is a *label*, not a new runtime — it feeds the
metareasoning layer and the linter, and it gives authors a per-rule "this one is
expensive / this one is cyclic and won't get the linear-time guarantee" signal. Low
friction because it changes nothing at runtime; it only annotates.

One honest deflation: the runtime is *already* doing pairwise, seed-from-ground joins
(RETE's binary floor, which the proposal itself recommends as the default). So treewidth
buys you a **cost estimate and a cyclicity warning**, not a faster matcher. The
decomposition-into-binary-joins the proposal describes is work the current `_match`
already does implicitly.

### 3. Node-sharing across rules — real performance, but not your bottleneck

Compiling a recurring join sub-pattern once and reusing it across rules is a real win
*if matching throughput is the constraint*. Per `finding_matcher_is_matching_bound`, the
matcher is matching-bound at scale — but the *fix already applied* (O(1) df, seed rarest
anchor) made it flat, and the open item is dense/cyclic hub-flooding (a walker problem),
not redundant cross-rule joins. So this is a "later, if profiling says so" item, not a
now item.

### 4. Bounded registers / working-set — corrected 2026-07-05

The original text (below) read the register bound as a *lossy runtime capacity gate* and
warned against it. **That reading was wrong for the intended idea.** The clarified framing
(`rule-isa-design.md`): the bound is a **decomposition** device — a match too big for a
register becomes *more instructions, same result* (the RISC / binary-join floor). It is
correctness-preserving and does not touch the index-driven, disconnected-mention matching.
So the distinction below still holds, but the conclusion flips: the bound is *fine* because
it is not the ACT-R runtime-capacity gate at all — it is compile-time pattern
decomposition.

Original text, kept for the record — the only part still live is: a *runtime capacity* cap
(ACT-R "only what's in a buffer can fire") would indeed be harmful and must never be a
correctness-affecting gate; but that is *not* what the ISA proposes.
- **Bounding pattern arity** (how many variables one join step touches) — a compile-time
  property; the runtime is already at the binary-join floor. Fine.
- **Bounding runtime working memory** (ACT-R capacity) — would be harmful (a single-pattern
  law finds a graph-disconnected mention *through the index*, not by proximity;
  `finding_matcher_is_matching_bound`, `vision.md` §11). The ISA does **not** propose this;
  its "more steps for a bigger match" is the *former*, not the latter.

---

## The two "tensions" — both softened by the 2026-07-05 reframing

### Tension A — compile-to-ISA vs. the no-seam / no-IR commitment (softened)

The original worry: a `rules → ISA` compiler reintroduces the `CNL → typed IR → reason`
seam `vision.md` §2/§3 and decision #6 forbid. **This is largely dissolved by the clarified
framing** (`rule-isa-design.md`): the forbidden seam is *between CNL and reasoning*; the
Rule ISA sits *below* the rules, which are already downstream of CNL, so it is the
reasoning's own micro-structure, not a wall between text and reasoning. And lowering a rule
to visible primitive steps is *more* homoiconic, not less.

One real fork remains, to decide explicitly: **in-graph instruction nodes** (fully
homoiconic, rule-inspectable, slower) vs. an **out-of-graph rebuildable bytecode cache**
(faster; still not a seam if never authored and never the source of truth, only
regenerated from the rule nodes — like the lexical index). The design-clarity benefits
accrue under either; the choice is orthogonal. `rule_graph.py` already round-trips rules as
graph nodes, so the in-graph path is buildable.

### Tension B — performance framing vs. your actual constraint (reframed away)

The original worry: the conversation is framed around throughput, but your binding
constraint is coverage/expressiveness, not match speed (`finding_coverage_composition_audit`,
`finding_raw_nl_coverage`) — the Fifth-Generation lesson (foundations Ch. 8). **The
reframing removes this tension by removing the performance framing.** The ISA's value is
**design tractability, not speed**: explicit operational semantics, a testable machine/rule
boundary, invariants enforced by the opcode set (illegal-states-unrepresentable), and
*formal* reasoning about expressiveness. None of that is a throughput claim, so the
Fifth-Generation objection does not bite it. The honest residual is only that the ISA does
*not* move the coverage frontier either — it is design-hygiene, to be sized accordingly and
not allowed to displace the coverage work.

---

## One substrate mismatch to keep in view

The conversation's whole complexity/treewidth apparatus assumes **typed edges as a
relation** ("edges as a typed relation"). The current substrate is more radical: *no edge
types at all* — a relation `s R o` is a two-hop path `s → [R] → o` through a reified node
(`vision.md` §1). Two consequences when importing the theory:

- A rule body's "query hypergraph" is over the **reified triples**, not over typed edges,
  so variable/arity counts (and therefore treewidth) are computed on the 2-hop encoding.
  This roughly doubles the node count of each condition but changes nothing essential —
  it just means the GYO/treewidth analysis runs on `Pat(s,p,o)` patterns as written,
  which is fine.
- "Relation-terminal routing / the RETE alpha network keyed on relation type" is
  *explicitly rejected* (`vision.md` §10). So if you adopt RETE-style node-sharing (#3),
  it must key on **node name via the lexical index**, not on an edge/relation type — the
  same discipline `_rule_anchors` already follows. Don't import the classic alpha-network
  shape; import its *sharing idea* over the name index.

---

## Recommendation (updated 2026-07-05)

1. **Build the static rule-dependency reachability graph** (proposal's real XCON fix).
   Content-blind, building blocks in `_rule_anchors`, targets your stated scaling risk,
   fits the linter/metareasoning remit. Still the one clearly-worth-it-now *analysis* item.
2. **Stamp each rule with a compile-time complexity/cyclicity label** (treewidth rung +
   join-depth estimate). A pure annotation; feeds the linter and effort policy.
3. **Run the cheap spec-first ISA experiment** (`rule-isa-design.md`): write the opcode set
   as an explicit small-step semantics + a reference interpreter, *before* any compiler.
   This is now a *design-tractability* play (not speed): it either enumerates cleanly (you
   get an explicit operational semantics + illegal-states-unrepresentable invariants + a
   formal expressiveness handle) or it reveals which reasoning feature won't fit yet
   (learned on paper, cheaply). Guardrails: keep the lowering *dumb*; scope expressiveness
   claims to the *crisp positive core*. Design-hygiene, not on the critical path — size
   accordingly, don't let it displace the coverage work.
4. **If you route execution through it, decide the fork** (Tension A): in-graph instruction
   nodes (homoiconic, slower) vs. rebuildable bytecode cache (faster, still not a seam).
   Never an authored IR. Note: the machine's matching core is **purely positive** — no
   NAC/`CHECK-ABSENT` opcode, since negation is materialized as a positive `is_not` fact.

The conversation's most valuable output was a four-literature confirmation that the
architecture you already have is right. The follow-up reframing added a genuinely useful
*second* output: the Rule ISA as a design-tractability instrument — a way to make the
engine's implicit semantics explicit, testable, and formally reasoned-about — worth a cheap
spec-first experiment even though it does not move the coverage frontier.
