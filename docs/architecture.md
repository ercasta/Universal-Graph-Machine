# Architecture — the as-built Universal Graph Machine

> **What this is.** The as-built description of the layers that make up UGM, ordered from the most
> GENERIC (knows no domain, takes no position) to the most OPINIONATED (a reasoning stance). Read
> `vision.md` first for *why* the system is shaped this way; this doc is *what is actually in the code*
> and *where the seams are*. Companions: the **engine developer guide** (how to extend each layer) and
> the **engine user guide** (how to consume the engine as a library, like `harneskills` does).

UGM is a library. A consumer (e.g. `harneskills`) builds a knowledge base, asks it questions, plugs in
its own tools, and — if it wants — its own reasoning firmware. The whole point of the layering below is
that **the bottom layers are generic and the opinions live at the top, as data**. You can swap the
firmware without forking the engine.

```
  ┌─────────────────────────────────────────────────────────────────────┐
  │  CNL surface        forms (rules) · load_corpus · ask_goal · render  │   surface
  ├─────────────────────────────────────────────────────────────────────┤
  │  STANCE             FirmwarePolicy  (CWA/OWA default, on_cycle)       │   ← opinion, as DATA
  ├─────────────────────────────────────────────────────────────────────┤
  │  FIRMWARE           CHAIN · CHECK · CHOOSE · SUPPOSE · mode-calls     │   ← the "psychology"
  │  (reasoning)        demand-driven, negation-as-failure, α-cut         │      (rules + thin Python)
  ├─────────────────────────────────────────────────────────────────────┤
  │  reified rules      write_rule · head index · the rule-graph reader   │   homoiconic mechanism
  ├─────────────────────────────────────────────────────────────────────┤
  │  TOOLS (§8)         <call> nodes · Tool registry · service_calls      │   generic calculator boundary
  ├─────────────────────────────────────────────────────────────────────┤
  │  ENGINE (ISA)       Machine (opcodes) · run_bank · run_rules          │   the stupid scheduler
  ├─────────────────────────────────────────────────────────────────────┤
  │  SUBSTRATE          AttrGraph  (label-less attribute graph)           │   one kind of thing: a node
  └─────────────────────────────────────────────────────────────────────┘
       everything below the STANCE line is GENERIC; a different firmware reuses it unchanged.
```

The metareasoning layer (vision §14 — fuel, df-selectivity, α-cut thresholds) is not a box in this
stack: it is the set of content-blind *dials* threaded through the engine and firmware as parameters
(`fuel`, `max_rounds`, `alpha`), never a node population.

---

## 1. Substrate — `AttrGraph` (`ugm/attrgraph.py`)

The one kind of thing is a **node**: an opaque identity plus a bundle of attributes. Edges are bare and
directed. Everything meaning used to carry in edge-types and names now lives in `(attributes + directed
topology)`.

- **Attributes** are `(key, value, kind)`. Two kinds: **GRADED** (`dog: 0.8`, a membership degree in
  `[0,1]`; `1.0` is the crisp corner) and **VALUED** (`name="Paul"`, `age=42`, open-domain data read by
  a comparator). Keys are closed (pass `schema=`); values are open.
- **Relations reify** neo-Davidsonian: `chase(a,b)` is a rel node carrying the GRADED key `{chase:1.0}`,
  wired `a → [rel] → b` by two bare edges. A relation's *predicate* is its single domain graded key
  (`AttrGraph.predicate(rid)`). There is no `name` label on a rel node (the Phase 2.3 demotion).
- **Two indexes, both candidate-sets — never identity.** `_by_key` (key → nids) is the only universal
  index; matching seeds from it and *tests* candidates. `_by_value` accelerates a small set of
  **declared discriminating keys** (default `{name}`, extend via `declare_index`) so seed-from-ground
  can jump to `name="Paul"` in O(1). The bright line (vision §1/§12.8): a value is *data under a key*,
  never a node-identity index — two people both named "Paul" stay two nodes. `nodes_with_value` returns
  a set to test, never "the" node.
- **Two disciplines, one graph** (vision §5). A node/edge is either **fact-layer** (monotone: reasoning
  never deletes) or **control-layer** (the `control` flag: ephemeral scaffolding, freely deleted, but
  only control edges). A third flag, `inert`, marks provenance/justification nodes invisible to
  matching. This partition is the one deliberate seam — ink vs pencil.

The substrate knows no domain, no strategy, no reasoning. It is a store with a matching index.

## 2. Engine (the ISA) — `Machine` + `run_bank` (`ugm/machine.py`, `ugm/lowering.py`)

The **stupid scheduler** (vision §6): fire enabled rules; carry ordering in tokens, not in a clever
driver. Two sub-parts:

- **`Machine` / `run_program`** executes a program of **opcodes** over the graph, threading a list of
  `State`s (register bindings + a graded score). The opcodes are the ISA:
  - *Matching core (purely positive, no side effects):* `SEED` (bind a register to each node with a
    key — the rarest-anchor seed), `FOLLOW` (edge cursor), `TEST` (valued comparator), `JOIN`
    (co-binding), `GRADE`/`FUZZY` (α-cut / soft unification — the graded layer, vision §13), `SET`,
    `DUP`, `SAME`.
  - *Effects (the second phase):* `MINT`, `EMIT` (assert a derived relation), `DROP_CTRL` (delete a
    *control* edge — refuses a fact edge), `INTERPOSE`/`RESTORE` (reversible retraction — the TMS).
  The split between matching and effects is what keeps a rule's reads consistent within a firing.
- **`run_bank`** lowers a `Rule` (a Horn clause with optional NAC / graded conditions / drops) to such
  a program and drives it to fixpoint: seed-from-ground, semi-naive delta matching, NAC as a match-time
  filter, fuel-bounded. **`run_rules`** wraps `run_bank` with **stratification** — it partitions the
  bank so a NAC over a *derived* predicate runs in a later stratum (vision §11), and on a genuine cycle
  it either raises or degrades to the monotone subset (the choice is the STANCE, §6 below).

The engine is generic: it hardcodes no predicate name and no strategy. It is Datalog's *evaluation
lessons* (semi-naive, lexical index, stratified negation) without Datalog's *language seam*.

## 3. Tools — the §8 calculator boundary (`ugm/dispatch.py`)

Some computation should not be graph rewriting — arithmetic, parsing a blob, calling a service, or a
firmware mode. Those are **tools**, and a tool is a calculator on opaque nodes:

- A rule MATERIALIZES a call node: `<call> --tool--> NAME --slot--> arg`.
- `service_calls(graph, registry)` runs every pending call whose tool is registered, at each fixpoint,
  and folds the emitted nodes back into the frontier. The dispatcher is dumb — it never inspects what a
  tool does.
- A tool is `Tool = Callable[[Graph, call_id], set[str]]`: it reads its call's opaque slots, EMITS
  nodes, and returns the touched ids. It must never rewrite/reason; a rule never calls a tool's
  internals. They couple only through nodes (vision §8/§12.5).
- Registries compose with `merge_tools(*registries)` (raises on a name collision). This is the seam a
  consumer extends to add its own tools (see the developer/user guides).

Tools are generic mechanism; *which* tools exist is the consumer's choice.

## 4. Reified rules — homoiconic mechanism (`ugm/cnl/rule_graph.py`, `ugm/apply.py`)

Rules are themselves graph structure (vision §2). `write_rule` reifies a `Rule` into a `<rule>` subgraph
(`lhs`/`rhs`/`nac`/`graded` pattern atoms, each built in *fact shape* so the matcher seeds them exactly
like facts). `build_head_index` / `rules_producing` build the in-graph **head index** (which rules'
heads could produce a demanded predicate). This reified form is what the demand-driven firmware reads —
it is why the firmware can reason *about* rules with the same machinery it reasons about facts. Still
generic: the reader is content-blind.

## 5. Firmware — the reasoning capabilities (`chain.py`, `check.py`, `choose.py`, `suppose.py`, `mode_calls.py`)

This is where the psychology lives — the "opinionated" layer, but the opinions are a *reasoning model*,
not domain knowledge. All of it runs on the generic engine + reified rules:

- **CHAIN** (`chain.chain_sip`) — the demand-driven prover. A bound-tuple goal `(pred, subj?, obj?)`
  raises a magic-set `<demand>`; the head index selects producing rules; each is served with
  sideways-information-passing (SIP), interleaving demand-raising and evaluation to a fixpoint. Derives
  exactly the goal's facts, never applies an irrelevant rule.
- **Negation-as-failure** (`chain._nac_blocks`) — a rule's NAC `not L` is decided ON DEMAND: bind it,
  demand the positive `L` to closure (a nested negative demand), read ABSENCE. Nothing is materialized
  for the negative. Sound because the bank is **stratified** (checked at load); fuel-exhaustion before
  closure yields UNKNOWN, not a decided no (the agent-not-theorem-prover model). See
  `demand_driven_negation_design.md`.
- **CHECK** (`check.check`) — runs the positive closure, then the negative, and returns a **4-status**
  verdict: POSITIVE / ENTAILED_NEG (a hard no) / ASSUMED_NO (the closed-world default) / UNKNOWN (open
  or fuel-exhausted). The closed-vs-open reading of absence is the STANCE (§6).
- **CHOOSE** (`choose.choose`) — graded α-cut argmax over the graded layer (nothing-beats-it, monotone,
  ties→all). **SUPPOSE** (`suppose`) — `<hypothesis>` scopes: pencil writes, in-scope reasoning,
  confirm→ink / refute→drop.
- **Mode-calls** (`mode_calls`) — CHECK/CHOOSE/SUPPOSE exposed as *tools*, so a control-token program
  (a KB-declared composition, e.g. plan→act→check→replan) invokes them through the one `<call>` loop.
  No new driver: firmware composition reuses the tool boundary of §3.

A different firmware is a different set of these — different reasoning capabilities and/or different
banks — reusing everything in §§1–4.

## 6. Stance — `FirmwarePolicy` (`ugm/policy.py`)

The firmware's *opinions*, as one immutable declared object, so an alternative firmware activates by
swapping data, not by forking `check`/`ask_goal`:

- `negation_default` — `"closed"` (CWA: absence → a defeasible ASSUMED_NO; `open_preds` are the OWA
  exceptions) or `"open"` (OWA: absence → UNKNOWN; `closed_preds` are the CWA exceptions).
- `on_cycle` — `"raise"` (reject a non-stratifiable bank at load) or `"degrade"` (defer to the forward
  path, which drops the NAF rules and warns).

`DEFAULT_POLICY` is the shipped stance (closed-world, reject cycles) — a caller that passes nothing gets
exactly today's behaviour. `check`, `ask_goal`, and `mode_registry` all accept `policy=`.

## 7. CNL surface (`ugm/cnl/forms.py`, `authoring.py`, `query.py`, `surface.py`)

The natural-language skin, all in-graph (vision §3): **recognition** is forms (normalization rewrite
rules) run by `run_bank` — a sentence that matches no form stays raw tokens. **Loading** (`load_corpus`,
`load_facts`, `load_rules`) tokenizes, recognizes, wires additive coreference (`same_as`), and reflects
rule-source into reified rules. **Asking** (`ask_goal`) recognizes the question, then answers it
demand-driven via CHECK/CHAIN. **Rendering** (`surface`) reads the graph back as CNL — explanation is
faithful because the graph *is* CNL. Exactly one thing stays outside the graph: the tokenizer tool.

---

## Where the seams are (the generic/opinionated split, summarized)

- **Generic, reused by any firmware:** substrate (§1), engine/ISA (§2), tools (§3), reified-rule
  mechanism (§4). None hardcodes a domain predicate or a reasoning strategy (audited: the substrate
  vocabulary is centralized in `ugm/vocabulary.py`; coreference derives its predicate set content-blind;
  the only `== "literal"` sites are control-token syntax, reified-rule role names, or declared-property
  → rule-schema generators).
- **Opinionated, swappable:** the firmware capabilities (§5) and the stance (§6). Today there is ONE
  firmware; the layering is what makes a second one a bank-and-policy swap rather than an engine fork.
- **The consumer's to fill:** domain rule banks, domain tools, and (optionally) a chosen policy — all
  data passed into the generic layers. See the user guide.

## Module map

| Concern | Module |
|---|---|
| Substrate | `ugm/attrgraph.py` |
| Substrate vocabulary (single source) | `ugm/vocabulary.py` |
| ISA engine | `ugm/machine.py`, `ugm/lowering.py` |
| Tools | `ugm/dispatch.py`, `ugm/external.py` |
| Reified rules / head index | `ugm/cnl/rule_graph.py`, `ugm/apply.py` |
| Firmware — demand-driven core | `ugm/chain.py` |
| Firmware — modes | `ugm/check.py`, `ugm/choose.py`, `ugm/suppose.py`, `ugm/mode_calls.py` |
| Stance | `ugm/policy.py` |
| CNL surface | `ugm/cnl/forms.py`, `authoring.py`, `query.py`, `surface.py`, `machine_rules.py` |
| Provenance / retraction | `ugm/provenance.py`, `ugm/retraction.py` |

The pre-firmware-v3 demand/coref/walk subsystems (`ugm/demand.py`, `ugm/coref_walk.py`,
`ugm/cnl/walker.py`) and the optional `ugm/asp.py` calculator were RETIRED (2026-07-12): the
firmware-v3 chain subsumes on-demand transitivity and coref (via reified `same_as`/declared-transitive
rules), so those modules were superseded. Coreference at load time is `authoring._coref_propagation`
(`same_as_rules` over the content predicates), which stays.
