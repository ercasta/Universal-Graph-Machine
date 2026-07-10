# The Harneskills Vision — One Substrate

> The doc index is `docs/reference.md`.)

> Design home: `docs/graph low level machine/rule-isa-design.md`;
> memory `decision-labelless-substrate`.

The whole system is one idea applied without exception: **there is a single
substrate — a graph of nodes — and everything is in it.** Knowledge, rules, goals,
the control flow of computation, and the source language itself are all nodes in the
same graph. Computation is the rewriting of that graph. There are no other moving
parts, and crucially, no *seams*: nothing ever leaves the substrate to be processed
by foreign machinery and come back.

Every rule below is a consequence of that one commitment.

---

## 1. Edges have no types

An edge is a bare, untyped connection between two nodes. It carries no label, no
relation name, no direction-of-meaning. **All meaning lives in nodes.**

Where a conventional system writes a typed relation — `is_a`, `causes`, `requires`,
`has_part`, `derived_from`, `resolves` — this system writes a **node** bearing that
word, wired to its arguments by plain edges:

```
   paul ── is_a ── person          (three nodes; two untyped edges)
```

`is_a` here is not an edge type. It is an ordinary node, indistinguishable in kind
from `paul` or `person`. A rule can match it, bind it, rewrite it, or create it, just
like any other node.

This is the hardest constraint to hold and the most load-bearing. It is what makes
the substrate uniform: there is exactly one kind of thing (a node) and one kind of
link (an edge). No taxonomy of edge types, no `Ref` reference type, no routing table
keyed on a relation. The cost is a **normalization tax** (§7) — but the payoff is
that rules and data are made of the same stuff, which is the precondition for
everything else.

**Keyword nodes** carry the structural semantics that edge-types and control
keywords used to carry. `<forall>`, `<current>`, `<goal>`, and the relation-words
above are all nodes. They look special only because rules treat them specially — not
because the substrate distinguishes them.

**Nodes have instance identity; a node is a bundle of attributes.** *(2026-07-05
amendment.)* A node's identity is its own — a unique `identity` attribute — and two
distinct nodes may share every other attribute (there can be many `Paul` nodes, many
`<current>` nodes). Everything else a node "is" lives in a **bundle of graded and valued
attributes** drawn from the KB's closed key-vocabulary; a former node-*name* like `Paul`
is just the valued attribute `name="Paul"`. Matching binds node *instances*, not names.
This is what makes control tokens work: a loop's `<current>` is a specific node instance,
and nested or concurrent loops each hold their own token node, all bearing the attribute
`<current>` without colliding.

**A relation is a node, never an edge label.** Because edges have no types, a relation
like `is_a` is realized as an intermediate node on a two-edge path —
`subject → [is_a node] → object` — both edges bare. The relation word, the subject, and
the object are all nodes; the edges carry nothing. This is the substrate's existing
"two directed edges through a fresh intermediate node" shape, and it is already correct.

**Nodes carry attributes — reasoning happens on attributes, not on blobs.**
Once nodes are label-less, information a node carries has nowhere to live *but* its
attributes, so a node holds a **bundle of `(key, value, comparator)` attributes**:

- A *crisp symbolic* fact is an attribute at the `1.0` corner (`person: 1`).
- A *graded* character is an attribute in `[0,1]` (`urgent: 0.9`) — the §13 embedding
  slice, now unified into the same bundle.
- A *scalar datum under a key* is a **valued attribute** — `name = "Paul"`, `age = 42`,
  config `urgency_per_tick = 0.2` — read by a comparator (`=`, `≤`, `≈`). These no
  longer become separate `[value node]` triples.

The driving principle: **reasoning happens on attributes, not on opaque blobs.** So an
**opaque blob** — a source string, a serialized payload — *stays a node* that only a
**tool** (§8) cracks open into attributes; the rule layer still never reads inside it.
The dividing line is exactly reasoning-surface vs. inert-content: a scalar the rules
compare is an attribute; a blob the rules cannot interpret is a node awaiting a tool.

**Values are not labels.** A value confers no identity — two distinct people both
`name="Paul"` stay distinct, keyed by their `identity` attribute. The guarantee holds
*only if the matcher treats `name="Paul"` as a value-test, never as a node-identity
index.* The comparator that reads `age ≤ 40` is the **minimal calculator** (§8), not the
rule layer parsing meaning.

**No name index — an attribute index instead.** Nodes are located by *matching on
attributes* inside rules, never by a name lookup table. Seed-from-ground (§11) drives
from the rarest attribute `key=value` pair (valued) or key (graded), located in O(1)
through the lexical/df index — the old node-name "Paul" is now the valued attribute
`name="Paul"`, so name-based seeding ports over unchanged. There is one node population
and one way to reach a node: a rule pattern.

---

## 2. One substrate, homoiconic

Facts, rules, goals, plan state, and the source CNL are all nodes in the one graph.
There is **no separate intermediate representation** and **no Python object
vocabulary that acts as a program**. Domain logic is never a Python class with an
`.execute(context)` method; it is graph structure that rules rewrite.

Because rules are themselves nodes, a rule can match, create, and rewrite other
rules. The system is homoiconic in the Lisp sense — code and data are the same
material — and this is what makes self-modification and learning ordinary graph
rewriting rather than a special subsystem.

---

## 3. CNL is loaded as-is — no compile seam

Controlled Natural Language is loaded **directly** into the graph as nodes. Words,
tokens, and keywords become nodes; rules pick up CNL expressions *as written*. There
is no compiler that parses CNL into typed triples, dataclasses, or rule objects.

The traditional pipeline `CNL → parse → typed IR → reason` has a wall in the middle:
the IR is foreign to the source, reasoning happens in a different universe from the
text, and explanation requires rendering logic back into English. **That wall is the
seam, and we abolish it.**

Abolishing it does not make the parser's work vanish — it **relocates** that work
into the graph as ordinary rewrite rules:

- Normalization (paraphrase → canonical form) becomes monotone rewrite rules.
- Coreference becomes rules that wire a `<same-as>` node between mentions.
- Disambiguation becomes rules, often triggered by downstream reasoning.

So "no seam" means precisely: **nothing ever exits the substrate.** Structure
*accretes* on the original text, in-graph, by rules — it is never imposed by code
outside the graph. Parsing and reasoning interleave in one engine instead of being
two phases separated by a wall.

This is not the same as "no structure." Structure is welcome — light typing of
keyword nodes, head-word links, canonical nodes — as long as it is built by rules,
in the graph, on the text. The seam we forbid is the *exit*, not the structure.

**Forms — the acceptance grammar, as rules.** A *controlled* natural language must
define which sentence shapes it accepts (`X is a Y`, `every X must have Y`, `to BREW:
step then step`). These "forms" survive — but as **in-graph normalization rewrite
rules**, never as a Python parser emitting typed dataclasses. A form is a rule whose
LHS matches a surface token pattern and whose RHS wires up canonical nodes. The CNL
grammar thus lives in the same graph as everything else; adding an accepted shape is
adding a monotone rule, not editing a compiler.

Exactly one mechanical step stays outside the graph, and it is a **tool** (§8): a
**tokenizer** that turns a raw CNL string (an opaque node) into token nodes plus
adjacency edges. It assigns no meaning — purely mechanical, domain-free. After
tokenization, all meaning is assigned by in-graph form/normalization rules:

```
raw CNL string (opaque) → [tokenizer tool] → token nodes + adjacency
                        → [form / normalization rules, in-graph] → canonical nodes
```

A sentence that matches no form simply remains raw tokens — the natural place for the
linter to report "no form recognized this." (The deleted `corpus_reader.py` fused
tokenizing + form-recognition + compile-to-dataclass into one pass; we keep the first
as a tool, turn the second into rules, and dropped the third — the seam.)

**Surface subsystems collapse into the substrate.** Anything that was a bespoke
Python component reading typed KB keys is re-expressed as *forms + nodes/rules + at
most a thin output tool*, not ported:

- **Explanation** is reading the append-only journal of firings that touched a node
  (§9), rendered from the CNL nodes themselves — not a template-substitution engine.
- **Narration** of a step *is* the canonical CNL node(s) that step asserted;
  conditional narration is an ordinary rule. At most a thin render-for-display tool
  remains at the output boundary.
- **Goal / scenario seeding** is adding a `<goal>` node wired to condition nodes (and
  fact nodes), recognized by the same forms on the tokenizer path. The domino engine
  (§6) takes over because the `<goal>` node triggers rules like any token — no bespoke
  seeding pass.

---

## 4. Computation is graph rewriting

Rules rewrite the graph. A rule has a left-hand side (a pattern of nodes and edges)
and a right-hand side (the rewrite). Rules:

- **Match and bind** nodes, including terminals and keyword nodes. A rule binds a
  matched node by name — written `paul?` or `<forall>?` — so the right-hand side can
  refer to it and act on it.
- **Create new nodes.** Rules (and tools) generate fresh nodes.
- Come in two disciplines, mirroring the two layers (§5):
  - **Reasoning rules** are monotone: they never delete a fact. Changes in truth are
    expressed by *adding* marker nodes (e.g. a `<retracted>` node wired to the fact),
    read through a guarded filter.
  - **Control rules** may delete — but only control/ephemeral edges (§5).

There is no separate rule language with its own syntax that creates a rule/graph
seam (this is why we reject Datalog-the-language, §11). A rule is graph structure
matching graph structure.

---

## 5. Two layers, one graph

The single graph is partitioned — by node/edge convention, not by storage — into two
disciplines. This partition is the *one* deliberate seam we keep: the line between
ink and pencil.

**Monotone fact layer** — knowledge and its derivations.
- Facts are never deleted by reasoning.
- Evaluated by semi-naive forward chaining (§11).
- Indexed lexically on keyword / head-word nodes.
- Normalization rules live here; they are additive (they annotate the surface with
  canonical nodes, never erase it), so they are monotone by construction.

**Non-monotone control layer** — the scratchpad of computation.
- Control tokens (`<current>`, frames, markers) and ephemeral scaffolding.
- Freely created and deleted.
- **Edge deletion is permitted only on control/ephemeral edges**, never on fact
  edges. A control rule that is not gated by a control token is a bug (it creates
  invisible order-dependence) — and is exactly what the linter must flag.

**Garbage collection** of disconnected nodes is always permitted: a node connected
to nothing can never participate in a future match, so removing it is semantically
invisible. GC is operational, never a step of reasoning.

The reason for the partition: dropping monotonicity is all-or-nothing for the
property it protects (confluence, termination, "every fact has a derivation"). You do
not get partial confluence by deleting "only sometimes." So we do not *weaken*
monotonicity — we *partition* it: facts stay monotone and debuggable; control is
free to mutate. The subtlety lives in the partition, not in a fuzzy guarantee.

---

## 6. Control is data — the planner is stupid

There is no smart planner. No beam search, no backward chaining, no scoring, no
priority queue, no HTN. The scheduler does the dumbest possible thing: fire enabled
rules.

All control flow is **data in the graph**, encoded as token-passing:

- A `<current>` token marks "where computation is." A rule that requires `<current>`
  on node X, and moves it to node Y, is a transition. This is a Petri-net token / a
  program counter reified as a node.
- Iteration is **domino tiles**: each rewrite leaves behind the precondition for the
  next. A `<forall>` node over a collection drives a loop by advancing a `<current>`
  marker through the members one at a time, firing the body for each.
- **Goal-setting and plan-evaluation are nodes that trigger rules.** "Planning" is
  rules rewriting goal-nodes into subgoal-nodes into action-nodes. The planner is
  just the rule engine; the goal-nodes are the plan.

Because ordering is carried by tokens, the scheduler can stay dumb and the result is
still deterministic: at any moment only the token-enabled rules (or mutually
commutative ones) fire. Determinism comes from the graph, not from a clever engine.

To keep token-passing from becoming GOTO-spaghetti, build behavior from a small,
reusable vocabulary of **control gadgets** — sequence, branch, forall, call/return
frame — each a node+token pattern. Complex control is composed from these, not
hand-rolled per case.

---

## 6a. Everything is goal-directed — computation is demand-pulled

Everything the agent does is goal-directed: no rule fires "just
because it matched." **Goal-pull is the default driver; forward saturation is the
exception**, confined to the monotone fact layer within whatever scope a goal opens.
This makes explicit what §6 and §11 already carry — goals are nodes that trigger rules,
and a rule with no ground anchor is demand-driven (the magic-sets rule).

The mechanism is **demand-forward, not backward SLD.** A goal is a partial
attribute-node to be matched-or-minted — the same shape as a fact (§1). Given that goal,
a **rule-head index** finds which rules' heads (the consequent/RHS of each Horn clause —
the fact the rule *produces*) could produce it, and a **magic-sets**
rewrite makes forward chaining derive only goal-relevant facts; **walkers** (§11) carry
demand across long range. This gives backward chaining's focus while the matching core
stays **positive and monotone**. We reject SLD + trail + negation-as-failure: it would
re-import the non-monotone negation §5/§11 removed and forfeit the crisp-core
expressiveness the substrate is built to keep.

Two lines this must not cross:

- **The scheduler stays dumb (§6/§12.4).** Goal-direction scopes *what is demanded*,
  never *which answer to prefer* — the latter is the rejected smart planner (§10). A goal
  decides how hard to look and where, not which conclusion is better; preference among
  valid matches is the graded layer (§13), and effort is the content-blind metareasoning
  layer (§14).
- **Negation is demand-driven, not failure-by-exhaustion.** A query distinguishes THREE
  negatives (`decision-cwa-default`): an ENTAILED `is_not` (derived, e.g. from disjointness) is
  a HARD `no`; an ASSUMED `no` is the CWA-default read for an unprovable goal on a closed-world
  predicate (defeasible — "best of current knowledge", computed demand-driven, nothing
  materialized/retracted so §5 holds); and `unknown` for a predicate declared OPEN (the OWA
  opt-in, where absence != false). Where a negative must be REIFIED for later matching (the
  forcing-a-decision line, `decide`), it is materialized positively as `is_not` — never a Prolog
  `\+` that succeeds by exhausting a search.

---

## 7. The normalization tax and the conventions

Because edges have no types and CNL is loaded as-is, two surface forms that mean the
same thing do not automatically match the same rules. The work that a compiler's
canonicalization used to do does not disappear — it must be paid as a **normalization
tax**: a thin layer of monotone rewrite rules that funnel paraphrases to **canonical
nodes**, so the bulk of reasoning rules match the canonical form, not every variant.

This tax is paid through **conventions that must hold everywhere** — uniform choices
about how surface text is wired, which keyword nodes mark which roles, how canonical
nodes are named. The conventions are the price of a seamless, untyped substrate, and
they are non-negotiable: a convention that holds in only part of the graph reintroduces
the inconsistency the single substrate was meant to remove.

---

## 8. Tools are calculators on opaque nodes

Some computation should not be done by graph rewriting — arithmetic, parsing a blob
of source, calling an external service. For these there are **tools**, and a tool is
exactly a calculator: a human offloading a hard computation to a device.

- A tool takes the content of one or more **opaque** nodes, computes externally, and
  **emits new nodes** back into the graph.
- The rule system **never inspects opaque content.** A fact value is an atomic,
  equality-comparable label until a tool chooses to expand it into graph structure.
- Tools are the **expansion / serialization boundary**: opaque blob → (tool) → graph
  nodes the rules can match → (tool) → serialized blob. Rules operate only on the
  expanded structure; they never cross into the opaque content themselves.

A tool never applies a rewrite, and a rule never invokes a tool's internal logic.
The tool is a black box that consumes nodes and produces nodes — like a calculator
that consumes digits and produces a sum, with the rule layer none the wiser about how.

**The reasoning surface is the attribute layer (§1 amendment).** Reasoning happens on
attributes, never on opaque blobs. A scalar under a key is a **valued attribute** the
rules compare directly — via the *minimal built-in comparator calculator* (`=`, `≤`,
`≈`), the smallest tool: it reads two opaque values and returns a truth degree, not the
rule layer parsing meaning. A **blob** (source string, serialized payload) stays an
opaque node until a tool expands it into attributes. This is why "scalar-under-a-key is
an attribute, opaque-blob is a node": the attribute layer is where reasoning lives, and
blobs are inert content outside it until a tool lifts them in.

---

## 9. Provenance and inspectability

Because the working graph mutates (control deletes, tools emit), provenance is kept
by an **append-only rewrite journal**: every firing records what matched and what was
added or deleted. This gives full "why did this happen" tracing without forcing the
working graph itself to be monotone.

Two further inspectability wins fall out of the vision for free:
- **Explanation is faithful** because the graph *is* CNL — there is no lossy
  re-rendering of logic back into English.
- **The neural/symbolic boundary disappears**: an LLM reads and writes graph nodes as
  text natively, with no serialization layer between it and the symbolic engine.

---

## 10. What this rejects

The following, all present in the pre-rebuild code and the numbered spec (now in
`attic/spec/`), contradict the vision and were deleted or rewritten:

- **Typed edges** and the `Ref` typed reference. → Edges are untyped; references are
  just nodes.
- **Relation-terminal routing** (engine lanes keyed on `causes` / `requires` /
  `is_a` / first-terminal; the RETE alpha network). → Relations are nodes; no engine
  routing by relation.
- **Python object vocabulary as programs** — `.execute(context)` constraint /
  scoring / plausibility / objective classes; `HardConstraint` closures. → Domain
  logic is graph/CNL.
- **The smart planner / reasoner** — beam search, backward chaining, scoring as
  *control*, HTN, Bayesian hypothesis ranking. → Stupid scheduler over token-gated
  rules. (Note: graded *matching* survives — see §13 — what is rejected is a clever
  planner, not gradable rules. Note also: *backward chaining* is rejected only as
  **SLD/trail/NAF control**; goal-directed **demand-forward** — magic-sets + walkers over
  the positive core — is kept and is in fact the default, §6a.)
- **The CNL "Forms 1–27" compiler** (`corpus_reader.py`) that parses CNL into typed
  dataclasses/triples. → CNL loaded as-is.
- **The PCFG *grammar structure*** (terminal/non-terminal symbols) and **probability
  used as a branch *selector*** (OR-alternatives summing to 1.0 that choose which
  production a parser expands). → Out of the core, because control is now token-passing,
  not branch-selection: every enabled rule fires; nothing *selects* a branch. Engine-
  *enforced* sum-to-1 normalization is also dropped (rules are independent weighted
  rewrites; normalization is a domain modeling choice for genuine distributions).
- **Mappers / dispatcher / grounder as separate Python subsystems.** → Tools (opaque
  calculators) plus rules.

**Explicitly NOT rejected — kept as first-class, the graded layer (§13):** sparse named
embeddings on nodes (the *qualitative* half) AND probability as a rule prior / fact
belief degree (the *quantitative* half). Earlier drafts wrongly listed both as rejected;
that was a mistake. The mechanism is engine; dimensions, weights, and probabilities are
authored graph/rule data. **Open (neither adopted nor rejected):** EM / inside-outside
*learning* of those weights — representing probability is settled; learning it is a
separate, still-open question.
- **The "parsing over a probabilistic grammar" unifying principle.** → Replaced by
  "one substrate, graph rewriting."

---

## 11. What we keep from Datalog (and why we still reject it)

Datalog-the-language creates a seam: its rules live in a different universe from its
tuples — rules are not data, cannot be created by rules, cannot reflect on control.
That seam is fatal to a homoiconic substrate, so we reject Datalog as a surface
language.

But Datalog's **evaluation lessons** apply to any forward-chaining engine and we keep
them, on the monotone fact layer:

- **Semi-naive evaluation** — join only against newly derived facts each round.
- **Lexical indexing** — a hash index per keyword/head-word node so an unconstrained
  match never scans the whole graph.
- **Stratified negation** — the discipline behind monotone retraction (the
  `<retracted>`-marker filter sits in a lower stratum than its consumers).

We keep the engine lessons; we drop the language.

**The negation fragment is deliberately STRATIFIED-ONLY (a soundness/termination trade).**
Negation-as-failure is admitted only when the rule set is *stratifiable* — no predicate
depends negatively on itself through a cycle. A cyclic negation (`p :- not q`, `q :- not p`)
has no unique perfect model, so the engine **refuses** it rather than pick one arbitrarily:
`stratify` raises. This is more conservative than the iterative closed-world assumption of some
benchmarks (the ProofWriter coverage probe's whole residual gap is exactly this — a handful of
theories outside the stratified fragment; canonical detail in memory `finding_coverage_proofwriter`).
We accept the conservatism: stratified negation is *sound* and *terminating*, and well-founded /
stable-model semantics would revisit the whole §5 retraction discipline. Should a real workload
need non-stratified NAF, that is a deliberate future decision, not a casual one. Until then the
engine **degrades gracefully** (`run_rules`): on a cycle it drops the NAF rules and reasons with
the monotone subset (positive chains still answer), warning which rules it dropped — never
silently losing the theory, never silently guessing a model.

**Seed-from-ground — the matching strategy.** Rule matching seeds every pattern from its
most-selective **ground** anchor — a literal, or an already-bound variable — located in O(1)
through the lexical index; free variables are destinations, never origins. A rule with no
ground anchor cannot run eagerly (it is demand-driven). This is the database magic-sets /
sideways-information-passing rule: drive from the bound columns and pass bindings on. It keeps
an unconstrained match from scanning the graph **with no neighbourhood cap at all**.

> Earlier this layer shipped a **hop-radius locality-bounded Rete** (match only within N
> undirected hops of the change frontier). Profiling (2026-06-30) showed hop-radius is
> mismatched to a substrate whose join key is the node *name* — a single-pattern law finds a
> graph-disconnected mention through the index, not by hops — and a too-small radius silently
> **truncated valid long joins** (a 40-hop transitive chain closed incompletely under radius=3).
> So `within`/radius is **RETIRED** as the matching scope: matching is unbounded and correct,
> seed-from-ground keeps it cheap. (`radius` survives only as a vestigial, ignored parameter.)
> See `docs/walkers_and_locality.md`. This is still a **different** Rete than the deleted
> dimension-indexed "alpha network" that routed by `lhs_embedding` (the relation-routing §10
> forbids); we keep the **lexical index** and **semi-naive** delta matching, drop the radius.

**"Think harder" has two content-blind knobs (§14), neither a hop radius.** For *eager* matching
it is **df-selectivity** — seed from the rarest anchor (a name borne by ~everything, like
`is_a`, is a stopword). For deliberate *long-range / iterative* exploration it is a **walker's
FUEL**: a walker is a control token carrying an origin + a frontier + a fuel budget; raising the
fuel explores further before giving up, and a materialized **shortcut** (a derived fact, or a
`same_as` link = coreference) lowers the fuel needed next time. Deliberation depth is a budget,
not a different algorithm. Two walkers at different positions get different **near-rules** (the
rules the index would seed from each position) automatically — concurrent control flows for free.

---

## 12. Disciplines to hold (the standing guardrails)

1. **Edges stay untyped.** Any reintroduction of an edge label or `Ref` is a regression.
2. **Conventions hold everywhere.** A normalization/wiring convention that holds in
   only part of the graph is a bug.
3. **Reasoning rules never delete; only control rules delete, only control edges, only
   token-gated.** A linter flags any ungated deleting rule.
4. **The scheduler stays dumb.** Any creeping intelligence in the planner belongs in
   the graph as nodes and rules instead.
5. **Tools never read opaque content with rules; rules never call tools' internals.**
   The opaque/expanded boundary is absolute.
6. **Crossing into non-monotone control is crossing into Turing-completeness** —
   termination is no longer guaranteed; `max_steps` is a real backstop, used
   deliberately, not as a nicety.
7. **Metareasoning is content-blind (§14).** Effort/budget policy may read structural
   graph statistics (name frequency, hop distance, fire counts) and exogenous budget
   (the user's "think harder"), but NEVER what a node *means*. An effort dial that reads
   domain meaning is reasoning in disguise, and a metareasoning policy that scores
   *content* to select a branch is the smart planner (§6/§10) sneaking back in.
8. **Attribute values are not labels (§1 amendment).** A valued attribute (`name="Paul"`)
   is data under a key; match it as a value-test, never index it as node identity.
   Blurring value into identity resurrects the label seam the substrate abolished.
9. **Goal-direction is not a smart planner (§6a).** Goals decide *how hard to look and
   where*, never *which conclusion to prefer*; the moment a goal scores content to choose
   an answer, the rejected planner (§10) is back.

---

## 13. The graded layer — probability and sparse embeddings

The substrate is symbolic, but reasoning is not crisp. The graded layer adds two
first-class, separable degrees on top of the crisp graph rewriting — and they are one
of the system's defining features, not an add-on:

- **Probability — the quantitative degree.** A *prior* weight on a rule, and a
  *belief/likelihood* (confidence) on a fact node. It is the engine's **semiring**: when
  a rule fires, the derived node's confidence is
  `(matched confidences) ⊗ (rule probability) ⊗ (embedding match degree)`, under the
  chosen semiring (product for likelihood; `min` for fuzzy). This single local
  computation delivers the three things probability is for — **ranked hypotheses**
  (competing abduction nodes carry different confidences, ranked by reading the numbers,
  no search), **Bayesian update** (prior × likelihood → posterior confidence), and
  **weighted derivation** (degrees chain along a derivation = semiring parsing). It needs
  no smart planner: the weight is computed at each firing, exactly like confidence.
  Probability is *not* a branch selector (§10) — every enabled rule still fires; the
  probability only *weights the outcome*.

- **Embeddings — the qualitative degree.** "More urgent", "more conservative", "fairly
  tall" are directions in a sparse named space, not symbols. A node carries a
  `dict[str, float]` over human-authored dimensions, values in `[-1, 1]`:

```
customer_42.embedding = {"urgency": 0.9, "waiting": 0.7}
fix_clamp.embedding   = {"risky": -0.5, "reversible": 0.8, "localized": 0.7}
```

This layer is **kept and first-class** — it is orthogonal to (and survives) the
rejection of the PCFG grammar and EM learning (§10). What is engine vs. authored:

- **Engine mechanism:** storing embeddings on nodes; dot-product similarity over shared
  dimensions; t-norm aggregation and α-cut thresholding for graded conditions; graded
  firing (a rule's derived facts inherit confidence proportional to match degree);
  embedding propagation when a rule fires.
- **Authored graph data:** which dimensions exist, the values on each node, the
  per-rule weights. None of this is Python domain logic — it is data on nodes and
  parameters on rules.

Three uses, all on the rule layer:

1. **Graded LHS conditions (soft applicability guards).** After a rule's structural
   pattern binds, a graded condition tests a bound node's embedding against a direction
   (`align(?x.embedding, urgency) ≥ α`). Conjoined conditions aggregate by t-norm
   (non-compensatory — both bars must clear), distinct from the ranking dot product.
   The rule fires *to a degree*; derived facts carry that degree as confidence.
2. **LHS computation / embedding propagation (bottom-up).** When a rule fires, the
   embedding of a node it *creates* is computed from the embeddings of the matched
   nodes — the "synthesized" direction. This is how a derived/composite node acquires
   its qualitative character from its parts.
3. **RHS / match steering (top-down).** Embeddings rescore which rule or which bound
   target is preferred among structurally-valid matches — the "inherited" direction —
   so gradable preference ("the more conservative fix") is expressible without a hard
   threshold.

**Propagation is declarative, not arbitrary Python.** The old `EmbeddingEquations`
carried free `Callable` closures (domain logic in Python — a §2 violation). The kept
form parameterizes propagation declaratively on the rule — e.g.
`{"op": "weighted_sum", "weights": [...]}`, `{"op": "shift", "delta": {...}}`,
`{"op": "identity"}` — so the mechanism stays in the engine and only parameters are
authored. Degrees chain along a derivation (product → decay, or `min` → weakest-link),
flowing into node confidence: formally this is **semiring parsing** over the `[0,1]`
(Viterbi/fuzzy) semiring layered on the crisp graph rewriting. The crisp graph is the
backbone; the embedding layer weights it. It never reintroduces typed edges (embeddings
live on *nodes*) and never reintroduces a smart planner (graded *matching* is local to
a rule, not a global search).

**Embeddings are the graded slice of the §1 attribute bundle (2026-07-05).** Under the
label-less amendment there is no separate `embedding` field beside a symbolic name: a
node is one bundle of attributes, and the graded ones (`urgent: 0.9`) *are* the
embedding. Crisp facts are the `{0,1}` corners of the same space; valued data (`age=42`)
are attributes with a datatype comparator. So this graded layer is not "on top of" the
crisp graph — it is the same attribute space read at different sharpness, with
**FUZZY-MATCH** (soft unification by embedding distance) generalizing the crisp attribute
test. The semiring / α-cut / propagation semantics above are unchanged; only the framing
unifies — one attribute bundle, read crisply or gradedly.

---

## 14. The metareasoning layer — content-blind effort policy

There is a third layer, distinct from the engine and the substrate. The **engine** is
mechanism: what one rewrite step *is* (stupid, fixed, §4/§6). The **substrate** is content:
what is *true* and what computation is *in flight* (facts, rules, control tokens, §5). The
metareasoning layer is neither — it governs **how much computation to do and where to
spend it**. It is the system's bounded rationality.

Its members are the dials that parametrize inference, not its mechanism or its content:

- **Locality radius (§11)** — how far from the change frontier to expand. "Think harder"
  is raising it.
- **Name selectivity / frequency (idf)** — a name's document frequency (how many nodes
  wear it — a count already in the lexical index) tells the matcher which anchor is most
  *selective* to seed from, and tells coreference which same-name collisions are worth
  hypothesizing on. A name borne by almost everything (`is_a`, `same_as`) is a *stopword*:
  cheap to ignore as an anchor, pointless to disambiguate.
- **α-cut thresholds** — how strict a graded match must be to fire (the *cutoff*, not the
  embedding degrees themselves, which are §13 content).
- **Fire counts / adaptive policies** — where effort has historically paid off.
- **The deliberation ceiling** — when to stop (distinct from `max_steps`, which is a
  *safety* backstop on non-monotone control, §12.6, not a tuning dial).

Three properties define the layer:

1. **Results are resource-relative.** The output is not a fixed function of (substrate,
   engine) but of (substrate, engine, **budget**). Turn the dials up and reasoning is more
   complete and slower; down and it is faster and partial. These are *anytime* knobs —
   reasoning degrades gracefully, it does not break.
2. **It is supporting machinery, outside the graph.** Like the lexical index and the
   matcher's caches, these dials are part of the harness, not the substrate — they are not
   a new kind of node, so they do not dent the one-substrate commitment (§2). They are the
   apparatus *around* the graph, the way the engine code is.
3. **It is content-blind (the discipline, §12.7).** Its inputs are *structural* graph
   statistics (frequency, hop distance, fire counts) and *exogenous* budget (the user's
   effort directive) — never what a node *means*. This is the bright line that makes
   `idf`-based name gating legitimate where a hand-coded "category vs. individual"
   distinction is not: a node *count* is structure; "person is a category" is world
   knowledge, which belongs in the substrate as facts/rules, never in an effort dial.

**This layer is where the rejected smart planner (§6, §10) would re-enter, so the boundary
is load-bearing.** Metareasoning may be *adaptive* — grow the radius until something fires,
skip high-frequency names, follow the fire counts — but it operates over **structure and
budget**, never by scoring *content* to choose which conclusion to pursue. A content-blind
effort controller wrapped around a stupid object-level scheduler is *not* the beam-search /
HTN planner that was cut: that planner chose *which answer* to chase; this layer chooses
only *how hard to look*. Keep that line bright and the layer is safe; blur it and the
planner is back.
