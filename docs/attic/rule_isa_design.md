# The Rule ISA — a low-level machine *below* the rules

> **Status: DESIGN EXPLORATION (2026-07-05). Not built.** This is the single canonical
> writeup of the "graph low-level machine" idea after the design conversation in
> `conversation.md` and the two follow-up discussions that reframed it. It supersedes the
> stale framing in the first draft of `comparison-to-current-system.md` (which read the
> idea as a performance/seam play). Companion references: `harneskills-foundations.md` and
> `harneskills-foundations-extended.md` (the prior art), `comparison-to-current-system.md`
> (what harneskills already implements), `docs/vision.md` (the substrate philosophy this
> must not violate), `docs/architecture.md` (the engine as built).
>
> **UPDATE (2026-07-14): BUILT, and extended with a CONTROL PATH.** This design describes the *data path*
> — the opcodes that run a rule as a straight-line basic block ("the machine only *runs* rules"). What
> ran those blocks was still Python (`run_bank`'s fixpoint, `chain_sip`'s recursion, the dispatch loop).
> That gap is now closed: `docs/attic/isa_control_machine.md` adds the **control path** (a PC over labeled basic
> blocks + `BRANCH`/`CALL`/`RET`/`SUSPEND` + a control stack + `PRIM` interpreter steps), and the Python
> drivers are ported onto it — so loops, subgoals, fixpoints, and tool waits are now ISA control, not
> procedures. See `isa-reference.md` §"The control path" for the built semantics.

---

## The idea in one screen

Today a rule is executed by one interpreter (`rewriter.run`) that walks `Pat(s,p,o)`
triples and, per rule, implicitly applies a great deal of machinery — seed-from-ground
matching, NAC evaluation, graded α-cut, semi-naive delta bookkeeping, provenance emission,
confidence semiring math, embedding propagation. The rule's *meaning* and the *machinery
that runs it* are entangled in that one loop, which has no independent specification other
than "whatever `run()` does."

The proposal: define a small, fixed **instruction set (ISA)** that sits **below** the
rules. Every rule compiles down (mechanically) to a sequence of these instructions, and a
small **machine** executes instruction sequences. Crucially:

- **Rules stay the authoring surface and the home of semantics.** The ISA is *only a way
  to run rules*. Expressiveness and meaning live at the rule level, exactly as now.
- **The two strata become independently addressable.** Machine bugs are diagnosed by
  hand-written instruction sequences with no rules involved; rule bugs are diagnosed at
  the rule level. You stop asking "is this a rule bug or a matcher bug?" of one tangled
  loop.

This is **not** a speed play and **not** an expressiveness increase. It is a
**design-tractability** play: an explicit operational semantics, a testable machine/rule
boundary, invariants enforced by the shape of the instruction set, and — the real prize —
the ability to reason *formally* about what the system can and cannot express.

The organizing analogy is the one the user gave: all software is expressed over a small,
fixed low-level ISA and architecture, and that is a *feature* — it lets hardware and
software be designed, tested, and reasoned about separately across a stable, small
contract. The claim here is that the same separation buys design clarity for the reasoner,
at n=1, even before any of the scale benefits of a real ISA apply.

---

## Why this is on-vision, not the forbidden seam

The first draft of the comparison called compile-to-ISA a reintroduction of the
`CNL → typed IR → reason` seam that `vision.md` §2/§3 and decision #6 abolish. Under the
clarified framing that objection is largely wrong, for two reasons:

1. **The forbidden seam is between CNL and reasoning** — a foreign typed IR the source is
   parsed *into*, so reasoning happens "in a different universe from the text." The Rule
   ISA is not there. It sits *below* the rules, which are already downstream of CNL. It is
   the reasoning's own micro-structure, not a wall between the text and the reasoning.

2. **Lowering a rule to visible primitive steps is *more* homoiconic, not less.** Today a
   rule is an opaque object the interpreter switches on. An instruction sequence the rule
   lowers to — if the instructions are themselves graph nodes — is a *transparent,
   inspectable* rewrite program. `rule_graph.py` already round-trips rules as graph nodes,
   so the machinery for in-graph instructions exists.

There is one real design fork, and it should be decided explicitly:

- **In-graph instruction nodes** — fully homoiconic, rule-inspectable, self-modifiable;
  slower. The vision-purest option.
- **Out-of-graph bytecode, a rebuildable cache** (like the lexical index or
  `Graph._by_name`) — faster, and *still not a seam* provided it is never authored and
  never the source of truth, only regenerated from the rule nodes.

The design-clarity benefits below accrue under *either* choice. The homoiconicity question
is orthogonal to the design-tractability question; do not let it block the experiment.

---

## The opcode set (materialized-negation, purely-positive matching core)

A critical correction from the discussion: **NACs are gone at the vision level.** Negation
is not a matching primitive — it is *materialized* as an explicit `c is_not P` node and
matched **positively** (the `decide.py` / forcing-a-decision / de-pythonization line:
a completion rule emits `is_not`, the consumer JOINs it positively, and a defeat rule
retracts it when a positive arrives). `nac_blocks` / `_nac_groups` in `rewriter.py` are
implementation residue of a superseded mechanism, not the ISA target.

This makes the machine markedly smaller and cleaner: the **matching core is purely
positive and monotone**, and the gnarliest current machinery (independent-NAC-group
partitioning) *evaporates from the machine* — it becomes ordinary rules (materialize +
defeat) living at the rule/semantics level, exactly where the vision wants it.

Candidate opcodes, each mapped to the code it subsumes:

| Opcode | Meaning | Subsumes in current code |
|---|---|---|
| `SEED` | bind the rarest **ground** anchor via the lexical index | `rewriter._triples` seed selection (`_pos`, df choice) |
| `JOIN` | extend bindings with the next triple pattern (positive only) | `_triples` + `_try_bind` per Pat in `_match` |
| `GRADE` | α-cut + degree on a bound node's embedding | `graded_degree` |
| `EMIT` | assert a fact triple (incl. `is_not` nodes); conf = semiring product | `apply_rule` RHS loop + confidence math |
| `EMIT-PROV` | materialize `<j:> --proves/uses-->` (or fold into `EMIT`) | `apply_rule` justification tail |
| `DROP-CTRL` | delete a control edge (token-gated) | `apply_rule` `rule.drop` loop |
| `REWIRE` | cut / link raw edges (control layer; the retraction interpose) | `apply_rule` `rule.rewire` loop |
| `PROPAGATE` | embedding op (`set`, later `weighted_sum`/`shift`) | `apply_rule` `_propagate_ops` |

There is **no `CHECK-ABSENT` / NAC opcode.** Negation-as-failure is not machine primitive;
it is `EMIT is_not` (a completion rule's action) + positive `JOIN` + `DROP-CTRL`/`REWIRE`
driven by provenance-matching `JOIN`s (the defeat / retract meta-rules). The provenance
opt-in (`match_inert` / `_pats_touch_prov`) becomes a *compiler decision* — a rule that
names `proves`/`uses` compiles its `JOIN`s in the inert-binding-permitted mode — rather
than a flag threaded through the whole matcher.

Note how small the matching core is: `SEED` + `JOIN` + `GRADE`, all positive. Mutation is
`EMIT` (monotone facts) + `DROP-CTRL`/`REWIRE` (control, gated). That is a very analyzable
machine.

---

## The label-less attribute substrate (2026-07-05 revision)

This revision records a representational shift decided in the follow-up design conversation
and folds in three new instruction classes (FUZZY-MATCH, MINT, pointer registers). It
supersedes the node-name / edge-predicate assumptions implicit in the opcode table above.

**The shift.** Nodes carry no label and no name. A node is an opaque identity plus a bundle
of **attributes** drawn from the KB's (closed) vocabulary. Edges are directed and
**unlabeled** — already the "untyped edges" commitment of the one-substrate vision; the new
part is label-less *nodes*. All discrimination that used to live in node-names and
edge-predicates now lives in **(attributes + directed topology)**. This removes the
label/attribute matching seam: matching becomes uniformly attribute comparison, continuous
by default, with crisp `{0,1}` as the corners.

**An attribute is `(key, value, comparator)`**, with two poles:
- *Graded membership* — `dog: 0.8`. value ∈ [0,1], comparator = α-cut / t-norm / embedding
  distance. This is what FUZZY-MATCH tests; `dog: 1` is the crisp corner.
- *Valued data* — `name = "Paul"`, `age = 42`. value from an open domain, comparator ∈
  {`=`, `≤`, `≈`}. **These are not optional: once nodes are label-less, a literal like
  "Paul" has nowhere to live except as an attribute value** — the alternative, a node whose
  label is "Paul", is exactly the label the substrate abolished. Valued-attribute tests are
  the EVALUATE/GRADE class (scalar comparison off a bound pointer), already partitioned away
  from the boolean core in the foundations (Ch. 5).

**Values do not resurrect labels — the guarantee to hold.** A label conferred *identity* and
was indexed as "what the node IS"; a value is data under a key, and identity stays the node's
own `identity` attribute. Two distinct people both `name="Paul"` remain distinct — values
don't merge identity, labels did. This holds **only if the matcher treats `name="Paul"` as a
value-test, never as a node-identity index.** Cross that line and the seam returns.

**Closed keys, open values.** The vocabulary of attribute *keys* (concept-words,
data-attribute-words, and chunk-words) is closed; the *values* of valued attributes are an
open domain — closed schema over open constants, exactly as in Datalog. Tame comparisons
(equality, ordering, ranges) keep the crisp core tractable; arbitrary arithmetic is the gated
case (the "arithmetic = absent-premise-class" of the coverage/composition audit).

**Relations and roles reify — uniformly.** Unary facts are attributes on a node. n-ary facts
reify (neo-Davidsonian): `chase(a,b)` → an event node `{chase:1}` linked by bare directed
edges through **role-nodes** — themselves label-less nodes whose attribute *is* the role
(`{agent:1}`, `{patient:1}`). Reading convention is directional: event → role-instance →
filler. Roles-as-attribute-nodes is what keeps the substrate fully uniform and forecloses the
"roles as edge labels" temptation (which would smuggle a label back).

**Chunking is a closed, definitional rule — not mining.** `pursuing is X chasing Y` is a KB
*definition*; `pursuing` already lives in the vocabulary. It compiles to a rule whose body is
the chase-configuration and whose head `MINT`s a node `{pursuing:1}` with edges back to the
*retained* constituents (additive — honors §5, a named shortcut structurally identical to the
walker shortcut-chains). No runtime vocabulary growth; the world stays closed. SUBDUE/MDL
demotes to an *offline authoring aid* that proposes candidate definitions, never a runtime
policy. VSA/HRR-binding the chunk's embedding lets a later near-miss FUZZY-MATCH it.

**Identity is an attribute.** A unique `identity` attribute per node unifies the Skolem
witness of the existentials decision (a minted node with a fresh identity) and `same_as` /
merge (coref-as-rules, verb-catalog) as attribute-level reasoning.

**Seeding survives, re-indexed and in fact recovered.** Seed-from-ground picks the rarest
anchor by df; it now ranges over attribute `key=value` pairs (valued) and keys (graded). The
old node-name "Paul" *is* the valued attribute `name="Paul"`, so name-based seeding ports over
unchanged — nothing lost. Fuzzy `SEED`/`JOIN` still need an ANN index + α-cut or they flood
(the open Tier-4 hub-flooding case).

**Goal-direction lean: demand-forward.** A goal is now a partial attribute-node to be
matched-or-minted — the same shape as a fact. So goal-direction = rule-head index + magic-sets
demand transformation + walkers, keeping the matching core positive and monotone (no trail, no
NAF). Recorded as the *lean*, not yet a hard commit; SLD + trail + NAF remains the rejected
alternative precisely because it forfeits the crisp-core expressiveness prize.

### Opcode delta

`EMIT` / `EMIT-PROV` / `DROP-CTRL` / `REWIRE` / `PROPAGATE` are unchanged.

| Opcode | Meaning | Status |
|---|---|---|
| `SEED` | bind rarest anchor by df, now over **attribute `key=value` pairs / keys** | revised (attributes, not node-names) |
| `JOIN` | extend bindings across a bare directed edge; positive attribute test on the reached node | revised |
| `GRADE` | α-cut / degree (graded) **or** value comparison `=`,`≤`,`≈` (valued) | revised (covers valued attrs) |
| `FUZZY-MATCH` | graded `SEED`/`JOIN`: embedding-distance-above-θ; writes a score; t-norm composes down the `JOIN` chain | NEW (soft unification) |
| `MINT` | create a label-less node; write attributes (incl. fresh `identity`) + bare edges back to retained constituents (Skolem / reification / chunk) | NEW |
| `SET`/`FOLLOW`/`DUP`/`DEREF` | pointer-register cursor model (direct / across-bare-edge / copy / resolve indirection); per-rule register count sized by treewidth+1 (foundations Ch. 4) | NEW (WAM-style) |

### Where this sits in the literature

No published system is this exact union; it is a synthesis whose pieces are each
well-precedented. Closest single anchor: **VSA / HRR / HDC** (label-less vector-nodes,
role⊛filler binding = roles-as-attributes, bundling = chunking, native similarity) — diverging
in that we keep an *explicit rewritable graph* rather than superposing into one lossy vector,
which is what preserves provenance and the crisp formal core. Reasoning layer: **Neural
Theorem Provers** / **Logic Tensor Networks** (soft unification, predicates-as-vectors, t-norm
semantics). Concept semantics: **Gärdenfors' Conceptual Spaces** (node = point in a feature
space) + **Formal Concept Analysis** (chunk = named definable intent; closed chunking = the
definable-concept closure). Relation encoding: **Sowa's Conceptual Graphs** (relations-are-
nodes) with the type labels dissolved into graded attributes. Valued-vs-graded attributes =
RDF datatype-vs-object properties / DL concrete domains / FCA many-valued contexts +
conceptual scaling. One-line: *Conceptual Graphs with labels dissolved into VSA-style
graded+valued attributes, reasoned over by NTP/LTN soft unification, with FCA-style closed
definitional chunking.*

---

## What this buys (in priority order)

1. **Make illegal states unrepresentable.** The load-bearing invariant — reasoning never
   deletes a fact edge (`vision.md` §5) — is enforced today by a linter that *inspects
   rule structure*. If the only mutating opcodes are `EMIT` (monotone) and
   `DROP-CTRL`/`REWIRE` (token-gated, control-only), then "an ungated fact deletion" is
   simply **not expressible** — there is no opcode for it. The invariant becomes a property
   of the instruction set, not a lint pass you can forget or that can have gaps.

2. **Cross-cutting machinery stops being smeared through one interpreter.** Provenance
   (the `match_inert` threading), graded α-cut, semi-naive bookkeeping, and embedding
   propagation stop being implicit behaviours applied to every rule and become explicit
   opcodes or compiler passes. A rule that needs no provenance simply lacks the `EMIT-PROV`
   instruction. This is the concrete form of "address issues in the machinery separately
   from issues in the rules."

3. **A testable machine/rule boundary.** The machine gets a conformance suite of
   hand-written instruction sequences — no rules involved. Two machine implementations
   (naive, optimized) can be differential-tested for agreement on the ISA. Wanted engine
   changes (e.g. object-aware stratification) become "change these opcodes against a spec,"
   not open-heart surgery on `run()` with 165 tests as the only description of intent.

   Evidence this is the right cut: the architecture doc's "known gotchas" are mostly
   *machinery-level* bugs that are hard precisely because there is no clean machine/rule
   boundary — completion aggressiveness, the non-stratifiable all-defeated cascade,
   provenance-awareness threading, rule-key collisions. That list is the symptom this
   idea treats.

4. **The real prize — reason *formally* about expressiveness.** Today "what can harneskills
   express?" is an *empirical* question probed by coverage audits. With a fixed opcode set,
   expressiveness becomes the closure of those opcodes, sitting at a definite rung on the
   descriptive-complexity ladder (`harneskills-foundations-extended.md` Ch. 3). "I hit a
   wall" becomes precise: *this inference class needs an opcode I do not have, and adding it
   crosses PTIME → NP.* It also gives the coverage-audit taxonomy a formal home:
   *composable-but-unencoded* = expressible in the current opcodes (a rule-authoring gap);
   *absent-premise-class* (taint, concurrency, arithmetic) = needs a new primitive or fact
   class. You can point at *which* wall you hit.

---

## The two guardrails (so the benefits are real)

1. **Keep the compiler dumb.** A two-stratum split turns "one place a bug can be" into
   three — rule / **lowering** / machine — and adds a new class, *miscompilation* (correct
   rule, correct machine, wrong lowering), which is nasty because it presents as "correct
   rule, wrong answer, no obvious culprit." A *mechanical* `Pat`-triple → opcode lowering
   (nothing clever: no optimization, no cross-rule fusion) keeps that surface small and
   auditable — the same "the scheduler stays dumb" discipline (`vision.md` §6). Cleverness
   (node-sharing / chunking) is where miscompilation risk grows; defer it.

2. **Scope the expressiveness claim to the crisp core.** The clean ladder result describes
   the *unbounded-budget limit*. The graded layer and the metareasoning budget dials (α-cut,
   fuel, df-gating, `max_steps`) make *effective* expressiveness resource-relative
   (`vision.md` §14 says exactly this). So reason formally about the crisp positive core;
   treat the graded/budget layer as a separate, resource-relative story — do not claim a
   single clean expressiveness number for the whole system.

---

## Honest costs and the one real risk

- **Two artifacts to maintain** (a compiler and a machine) where there is one interpreter
  now — real ongoing cost at n=1.
- **Source-maps required.** Provenance today gives a derivation trace at the
  *rule-firing* level — the level authors and explanation work at. An instruction trace is
  *below* that; without instruction→rule mapping you make ordinary debugging and
  explanation noisier. Keep rule-level provenance as the primary view.
- **Part already exists implicitly.** `_match` already reduces every rule to a sequence of
  pairwise 2-hop triple-joins from a ground seed; the "register" is effectively the
  bindings dict. So some of the ISA is *reifying and naming what the interpreter already
  does* — which lowers risk (not a semantics rewrite) but tempers the novelty.
- **The one real risk: formalizing a still-moving semantics.** A narrow waist's
  *decoupling* value is lowest when there is one thing on each side and both are moving
  (existentials, aggregation, disjunction, object-aware stratification are all in flight).
  BUT — the *specification/testability* benefits (1–3 above) accrue even while the semantics
  moves, because separability of *testing* needs the interface to *exist*, not to be
  *stable*. And the trend is favourable: the semantics is shrinking toward a **small
  positive core** (NAC out → materialized-positive in; the whole de-pythonization arc
  collapses Python machinery into rules). A waist contracting toward a small positive core
  is *stabilizing*, which is the condition under which formalizing it is a good bet rather
  than premature.

Net: this is a **specification / design-hygiene** investment. It will make the *engine*
easier to reason about, test, and keep invariant-correct. It will **not** move the actual
frontier — coverage and expressiveness, which stay a matter of rule content and premise
classes. Size it accordingly; do not let it displace the coverage work.

---

## The cheap experiment (do this first, before any compiler)

Write the opcode set as an explicit **small-step operational semantics**: a spec document
plus a **reference interpreter** that executes instruction sequences — *before* building
any compiler that routes real execution through it. Two outcomes, both informative:

- **It enumerates cleanly** and the two-layer monotonicity invariant falls out as a
  property of the opcode set → you have your ISA spec and can decide whether to route
  execution through it (and whether instructions are in-graph nodes or a rebuildable cache).
- **It does not enumerate cleanly** because aggregation / existentials keep demanding new
  opcodes → you have learned, cheaply and on paper, that the waist is not ready to freeze —
  before building a compiler.

Prior on the outcome: the monotonicity / two-layer part will formalize cleanly and be worth
it; the graded and provenance parts will be mixed; the still-open reasoning features
(existentials, aggregation) are the real test of whether the ISA is premature. The
reference interpreter should be checkable against the existing engine on the current test
corpus (the behavioral contract suite in `tests/test_contract.py` is the swap-safety net
for exactly this kind of engine substitution).

**This is design-hygiene, not on the critical path.** The immediate build remains graded
means-selection (`docs/attic/graded_means_selection_design.md`); the ISA experiment is a
parallel, low-cost track to pick up when the engine's implicit semantics next gets in the
way.
