# UGM — Universal Graph Machine

**A substrate for performing computation over graphs.**

UGM doesn't *break* the wall between (controlled) language and computation — it **dissolves**
it. Parsing, reasoning, and explanation are one process (graph rewriting over one substrate),
so language isn't a layer bolted onto an engine — it's made of the same thing. ([see how](#the-cnl-layer-ugmcnl))

UGM is a self-contained Python library: a label-less attribute graph substrate, a
declarative instruction set architecture (ISA) for graph computation, a demand-driven
reasoning **firmware** on top, and an optional Controlled Natural Language (CNL) surface
for authoring and rendering. The core is pure symbolic graph computation — no neural nets,
no LLMs, no external solvers (the graded layer is *sparse named* attributes in `[0,1]`, not
dense/neural embeddings).

New here? Read **`docs/architecture.md`** for the layering, then the **`docs/engine_user_guide.md`**
(build on UGM) or **`docs/engine_developer_guide.md`** (extend/fork it).

---

## Core idea

The whole system is one idea applied without exception: **everything is in the graph**.
Knowledge, rules, goals, the control flow of computation, and the source language are
all nodes in the same graph. Computation is rewriting that graph.

**Edges are typeless.** An edge is a bare, untyped connection between two nodes. All
meaning lives in nodes. Where other systems write a typed relation, UGM writes a *node*
bearing that word, wired to its arguments by plain edges:

```
paul ── is_a ── person          (three nodes; two untyped edges)
```

`is_a` is not an edge type. It is an ordinary node, matchable and rewritable like any
other. A **relation** is always a node — never an edge label.

**Nodes carry attributes.** A node holds a bundle of `(key, value, comparator)`
attributes: crisp symbolic facts (`person: 1`), graded characters (`urgent: 0.9`), and
scalar valued attributes (`name = "Paul"`, `age = 42`). Reasoning happens on attributes;
opaque blobs stay as nodes for tools to open.

**Fact and control are segregated.** `<angle-bracket>` nodes are control tokens —
working state the engine creates and destroys. Ordinary nodes are the persistent fact
layer. A rule that creates a control token leaves facts untouched; teardown is DROP_CTRL,
never fact deletion. The fact layer is **monotone**: nothing is ever deleted from it.

**Matching is set-at-a-time, not single-token.** A program doesn't walk the graph one
value at a time and loop where it needs to branch; each step runs over a whole *set* of
in-flight candidate matches at once, and an instruction that has multiple valid
continuations (e.g. a node with several outgoing edges) expands that set — one candidate
in, several out — for free. There is no separate loop construct for "for each match": it
falls out of every step operating on a set instead of a single candidate. This isn't
primarily a performance trick: a rule's meaning IS "every binding that satisfies the
body," so enumerating the full set is what correct matching means, independent of speed —
and it does so without mutating anything mid-search (no backtrack-and-undo), which is
what lets semi-naive fixpoint iteration, demand-driven CHAIN, and per-derivation RECORD
provenance all build on it directly. That every candidate in the set is independent does
make the fold embarrassingly parallel, but parallel execution is deliberately kept a
semantics-invisible *accelerator*, never a semantics of its own (`processing_modes.md`
§6's forbidden-concurrent-actors line). See below.

---

## Architecture — the layers

UGM is built in layers, from the most **generic** (knows no domain, takes no position) to the
most **opinionated** (a reasoning stance). The bottom layers are reusable by any firmware; the
opinions live at the top, as data — so you can swap the reasoning firmware without forking the
engine.

```
  CNL surface     forms · load_corpus · ask_goal · render
  ─────────────────────────────────────────────────────────────────────────
  STANCE          FirmwarePolicy (CWA/OWA default, on_cycle)     ← opinion, as DATA
  FIRMWARE        CHAIN · CHECK · CHOOSE · SUPPOSE · mode-calls   ← the reasoning "psychology"
  reified rules   write_rule · head index                        ← homoiconic: rules are graph too
  TOOLS (§8)      <call> nodes · Tool registry · service_calls    ← generic calculator boundary
  ENGINE (ISA)    Machine (opcodes) · run_bank · run_rules        ← the stupid scheduler
  SUBSTRATE       AttrGraph (label-less attribute graph)          ← one kind of thing: a node
```

Everything below the STANCE line is generic and reused unchanged by any firmware; a different
reasoning firmware is a bank-and-policy swap, not an engine fork. Full detail —
**`docs/architecture.md`**. The opcode set and processing modes below are the ENGINE and
FIRMWARE rows expanded.

---

## The ISA — the opcode set

Every rule and mode compiles down to a small, closed instruction set: a WAM-style register
machine over the label-less attribute substrate (`ugm/machine.py`). Like any register machine
it has a register file — but a register here is not a scalar or a memory cell, it is a
**pointer to a node in the graph**: `State.regs` is a `name -> node identity` map, and every
opcode either binds a register to a node (SEED/FOLLOW/MINT/...), reads the node a register
already points to (TEST/EMIT/...), or compares two registers for pointer equality (SAME). The
graph *is* the machine's addressable memory; there is no separate data space. A program is
always **match-then-apply** — matching opcodes (purely positive, non-mutating) followed by
effect opcodes (mutating); a matching opcode after an effect opcode is a `ProgramError`.

One more thing the register-file framing can obscure: `State` is a *single* binding, but
the interpreter never runs just one `State` through a program — it runs a **list** of
them, threaded through instruction-by-instruction, where a match opcode maps one input
state to zero-or-more output states (e.g. `FOLLOW` yields one state per matching edge).
So a register is single-valued *within one state*, but a program step routinely turns one
state into many. There's a full worked example after the opcode table.

| Opcode | Phase | What it does |
|--------|-------|--------------|
| **SEED** | match | bind a register to every node carrying a key (the rarest anchor); optional valued filter |
| **FUZZY** | match | graded SEED: bind to every node whose key's degree clears a threshold, scaling `score` |
| **FOLLOW** | match | pointer-register cursor: bind to an out/in-neighbour across a bare edge |
| **TEST** | match | crisp filter on an already-bound register (key presence, optional valued comparison) |
| **JOIN** | match | sugar for FOLLOW + TEST in one step |
| **GRADE** | match | filter a bound register on a graded (α-cut, scales `score`) or valued attribute |
| **SET** | match | bind a register directly to a known ground identity |
| **DUP** | match | copy one register into another |
| **SAME** | match | keep the state iff two registers are bound to the same node (join consistency) |
| **MINT** | effect | create a fresh node (Skolem / reified relation / chunk head), write attrs, wire edges |
| **EMIT** | effect | assert a fact attribute on a bound node (graded: monotone raise; valued: set) |
| **DROP_CTRL** | effect | delete a bare edge — refuses and raises if the edge is a FACT edge |
| **INTERPOSE** | effect | reversibly hide an edge by splicing in a control marker (the sole fact-edge mutation) |
| **RESTORE** | effect | the exact inverse of INTERPOSE |

There is no NAC/`CHECK-ABSENT` opcode — the matching core is purely positive. Negation is
not an ISA primitive but a FIRMWARE decision: in the forward driver a rule's NAC is a
match-time filter, and in the demand-driven firmware a `not L` clause is resolved on demand by
stratified **negation-as-failure** — `chain_sip` demands the positive to closure and reads
absence, never an exhaustive-search opcode (`docs/demand_driven_negation_design.md`). Nothing
is materialized or retracted for a negation. There is also no opcode that deletes or lowers a
fact: the invariant is a property of the opcode set itself, not a lint pass.

## Processing modes — nine KB-level operations built on the ISA

Rules, goals, and control flow lower to opcode programs; on top of that substrate UGM
exposes a closed inventory of nine composed computation modes, each corresponding to a
recognisable step in deliberate reasoning:

| Mode | What it computes | Analogue |
|------|-----------------|----------|
| **SATURATE** | forward closure within a demand scope | automatic association |
| **ITERATE** | cursor over a reified collection | walking a list |
| **CHAIN** | demand-driven rule application | deliberate inference |
| **CHECK** | bounded completion with CWA verdict | looking and possibly not finding |
| **CHOOSE** | graded α-cut selection over candidates | comparing and picking |
| **SUPPOSE** | pencil/ink hypothesis scope | "what if" reasoning |
| **WALK** | fueled variable-length traversal | scouting at distance |
| **CALL** | reified tool calls folded back | using a calculator |
| **RECORD** | provenance journaling woven through every mode | remembering what you did |

Every computation the system performs is one of these, or a KB-authored composition of
them (a *procedure*). There are no other moving parts.

> **Note (WALK).** WALK's standalone fuelled-traversal implementation was retired as
> superseded: long-range reachability over a declared-transitive relation is now handled by
> demand-driven CHAIN (fuel-bounded), so the current firmware realizes the other eight modes
> directly. WALK is kept as a design mode in `processing_modes.md`; a dedicated walker would be
> re-added only if a workload needs traversal that CHAIN over declared transitivity can't
> express.

**SATURATE / CHAIN** are the forward and backward engines respectively. Rules are
reified as graph structure (a `<rule>` node with `rl_lhs`, `rl_rhs` relations). SATURATE
walks the rule body forward, emitting derivations into the graph; CHAIN pulls the same
reified rules backward from a demand (magic-sets), so it never over-derives.

**CHECK** answers a yes/no/unknown question with four statuses: `POSITIVE` (proved),
`ENTAILED_NEG` (negation proved), `ASSUMED_NO` (CWA: no evidence), `UNKNOWN` (open
world). This closed-vs-open reading of absence is the firmware **stance**, carried as
declared data on a `FirmwarePolicy` (`ugm/policy.py`), not baked into the engine.
**CWA is the shipped default**: an underivable goal is a defeasible `no`. **OWA is opt-in**
— per predicate (`FirmwarePolicy(open_preds=…)`) or as the default (`negation_default="open"`)
— for concepts where absence should not be taken as false ("no sighting" ≠ "no mice"), so the
verdict stays `UNKNOWN` and defers to evidence-gathering. A different firmware activates a
different stance by swapping the policy object.

**CHOOSE** selects the best option from a candidate set using graded α-cut: an option
wins if it satisfies the goal at a level no other option does. Ties are retained.
Graded attributes (`urgent: 0.9`) feed directly into the selection.

**SUPPOSE** enables safe hypothesis reasoning via a pencil/ink split. Assumed facts are
written as control-scoped (`pencil`) nodes; derivations run inside the scope. On
confirmation the assumptions are committed to the fact layer (`ink`); on refutation the
entire scope is dropped. The fact layer is never tentatively modified.

**ITERATE** walks a reified collection one member at a time via a `<current>` cursor
token advancing a `next`-chain — the domino/forall pattern. There is no hidden Python
`for` loop or recursion: the list is graph structure, and stepping the cursor is the
only iteration primitive. Counting/totaling over the walked members is delegated to CALL,
keeping the rule layer itself arithmetic-free.

**CALL** folds tool use back into the graph: a reified `<call>` node holds argument
slots, is serviced at fixpoint by the tool registry (arithmetic, aggregation, temporal,
external solvers, an SLM), and its result is written back as an ordinary fact. This is
the generic calculator boundary (`§8` in the architecture diagram) — arithmetic and
aggregation are never smuggled in as hidden rule-layer helpers.

**RECORD** is provenance journaling woven through every other mode, not a bolt-on debug
flag: every MINT/EMIT carries a `<j:…>` journal entry recording which rule fired, over
which bindings, from which facts. It is free (no fuel cost) and mandatory. Explanations
(`why …`) are a replay of this journal rendered back to CNL, not post-hoc template text
— in the Horn fragment the journal *is* the proof object.

---

## The CNL layer (`ugm.cnl`)

The `ugm.cnl` subpackage provides a Controlled Natural Language surface over the ISA.
Rules and facts are authored as plain English-like text files:

```
alice wants vanilla
vanilla is in_stock
alice gets vanilla when alice wants vanilla and vanilla is in_stock
```

CNL is parsed into graph structure by `load_facts` / `load_rules`, which run the ISA
forward engine over the form-recognition grammar. There is no separate parser; parsing
IS graph rewriting. Explanations render back to CNL via `explain(graph, fact_id)`.

**There is no wall between language and computation — it isn't broken, it's dissolved.**
Parsing and reasoning are *both* graph rewriting: each lowers to the same opcode ISA over
the same label-less graph, so there is no AST handed from a parser to a distinct engine.
They differ only in *driver* — recognition is a whole-batch forward pass (`run_bank` over
the form grammar), reasoning is demand-first (`chain_sip` / CHAIN), because recognizing all
of the input is a closure while answering a question is goal-scoped. A fact, a rule, a
question, and the control tokens of computation are all nodes in one graph, and *what a line
is* emerges from which form rewrites it, not from a classifier that routes before reasoning
begins. `why` closes the loop: an explanation is the RECORD journal rendered back *to* CNL,
so language-out is the inverse of language-in over the same structure. Language and inference
are one rewriting process at different points on a continuum — not two systems with glue
between them. The one boundary UGM draws **on purpose** is at CNL itself: free English is
translated in by an external model ("CNL as surface, not engine input," the Attempto
stance); from CNL inward, language and computation are made of the same thing.

Key CNL concepts:
- **Facts**: subject–predicate–object triples (`alice wants vanilla`)
- **Rules**: `HEAD when BODY` with `and`, `not`, graded conditions (`is very urgent`)
- **Universals**: `if BODY then HEAD` and `ADJ things are PRED` laws
- **Gradable dimensions**: declared with `X is gradable`; used in rules as `?x is very X`
- **Closed/open world**: CWA is the query-time default (an underivable goal is a defeasible
  `no`); a concept is opted into OWA through the firmware **stance**
  (`FirmwarePolicy(open_preds=…)` / `negation_default`), so absence stays `UNKNOWN` and defers
  to evidence. Negation itself is demand-driven negation-as-failure — nothing is completed or
  retracted (`docs/demand_driven_negation_design.md`)

### Lowering: CNL rule → ISA program

CNL never reaches the engine as text at reasoning time — it authors a `Rule` (an LHS/RHS
list of `Pat`s), and `lowering.lower_rule` compiles that `Rule` into the opcode program
CHAIN/SATURATE actually run. Given the rule behind the last line of the CNL snippet above:

```python
from ugm.production_rule import Pat, Rule
from ugm.lowering import lower_rule

rule = Rule(
    key="gets_when_wants_and_stocked",
    lhs=[Pat("?x", "wants", "?y"), Pat("?y", "is", "in_stock")],
    rhs=[Pat("?x", "gets", "?y")],
)
for ins in lower_rule(rule):
    print(ins)
```

produces (register names elided to their role):

```
SEED   _rel0 key=wants                       # anchor: every "wants" relation node
FOLLOW ?x   <- _rel0 (in)                    # its subject
FOLLOW ?y   <- _rel0 (out)                   # its object
FOLLOW _rel1 <- ?y (out)                     # ?y's outgoing relations
TEST   _rel1 key=is                          # ... that are an "is" relation
FOLLOW _ts1 <- _rel1 (in)                    # that relation's subject
SAME   _ts1 == ?y                            # join-consistency: must be ?y itself
FOLLOW _to1 <- _rel1 (out)                   # that relation's object
TEST   _to1 name = "in_stock"                # ... must be named in_stock
MINT   _head0 name=gets, gets=1.0            #   |
       edges=[?y] in_edges=[?x]              #   } effect: reify "?x gets ?y"
       dedup=True                            #   (reuse if this relation already exists)
```

The first nine instructions are the **match phase** (purely positive, no mutation); `MINT`
is the sole **effect**, run only for surviving states. This is the whole story: no separate
rule interpreter, no AST walk at runtime — a rule IS this program, and running it to
fixpoint (`run_bank` / `apply_to_fixpoint` / `chain_sip`) is what SATURATE/CHAIN mean above.

**A register holds a set of bindings, not one value — this is where "iterate over every
matching edge" comes from.** It's tempting to read `FOLLOW _rel1 <- ?y (out)` as "follow
the one edge out of `?y`" and the `TEST` after it as a single check on that one result. That's
not what happens. `Machine.match` (`ugm/machine.py`) runs the program as a fold over a
**list of states**: `states = [State()]` to start, then for every instruction it computes
`states = [st2 for st in states for st2 in _match_step(ins, st)]`. `FOLLOW`'s step is a
generator that yields one new state per matching edge — `for nid in g.succ(src): yield
st.bind(dst, nid)` — so one `?y` with three outgoing relations turns one input state into
three output states, each with `_rel1` bound to a different edge. The next instruction
(`TEST`) then runs once per state independently, so "`FOLLOW` then `TEST`" reads as *for
every outgoing edge of `?y`, keep it iff it's an `is` relation* — with no explicit loop in
the program text, because the iteration is the fold in `match`, not something a rule author
writes.

---

## What is expressible

UGM targets a deliberately small, well-understood logic fragment:

- **Definite Horn rules** with conjunctive bodies (Datalog; least-fixpoint semantics)
- **Stratified negation** decided on demand (negation-as-failure) with a CWA-default stance
- **Defeasible rules with priorities** — defaults, exceptions, overrides (no contraposition)
- **Deontic statuses** as reified ranked predicates (`forbidden` … `obligatory`)
- **Declared congruence** (`same_as`) propagated over KB-declared predicates only
- **Graded attributes** in `[0,1]` unified with the rule matching layer (α-cut)
- **Scoped hypothetical reasoning** (SUPPOSE) without possible-worlds machinery

Formal anchors are kept for correctness; general theorem proving is not the goal.

---

## Usage

Load a knowledge base and ask it questions — answering is demand-driven (it derives only
what the goal needs), so there is no forward `run_rules` pass required first:

```python
import ugm as h

kb, rules = h.load_corpus("""
alice wants vanilla
vanilla is in_stock
alice gets vanilla when alice wants vanilla and vanilla is in_stock
""")

h.ask_goal(kb, "who gets vanilla", rules)      # ['alice gets vanilla']
h.ask_goal(kb, "is vanilla in_stock", rules)   # ['yes']
h.ask_goal(kb, "why alice gets vanilla", rules)  # a CNL derivation trace
```

Pick a reasoning stance with a `FirmwarePolicy`, register your own tools, or drop to the
lower-level demand-driven API (`chain_sip`, `check`, `choose`, `suppose`) — see
**`docs/engine_user_guide.md`** (consuming UGM) and **`docs/engine_developer_guide.md`**
(extending it). For a full forward snapshot when you need one, `h.run_rules(kb, rules)`.

---

## Try it out

The **`demos/`** folder has five runnable, self-contained walkthroughs of increasing
complexity. Each is a single `.cnl` file — facts, rules, questions, and an inline
walkthrough (as comments) explaining what the engine does at each step — and each ends
with a **NOW TRY CHANGING IT** section: concrete edits to make, with the outcome to expect.

```bash
python demos/run.py                          # run all five, in order
python demos/run.py demos/01_basics.cnl      # run just one
```

| # | Demo | Teaches |
|---|------|---------|
| 1 | `demos/01_basics.cnl` | Facts, one rule, forward chaining, `who` / `why` |
| 2 | `demos/02_chains_and_recursion.cnl` | Rules feeding rules: chaining and self-feeding **recursion** (transitive closure) |
| 3 | `demos/03_negation_and_worlds.cnl` | **Negation-as-failure** and the **closed- vs open-world** reading of "no" |
| 4 | `demos/04_graded_and_defeasible.cnl` | **Graded attributes** (the α-cut) and **defeasible defaults** |
| 5 | `demos/05_card_trader_playground.cnl` | **Playground** — a card-trading agent that *decides* what to buy/sell (market, rarity, named cards), with many knobs to turn |

See **`demos/README.md`** for the index and the CNL surface rules the demos rely on.

---

## Installation

```bash
pip install ugm              # core (no dependencies)
```

Pure Python, requires Python ≥ 3.8.

---

## Design philosophy

> *The whole system is one idea applied without exception: there is a single substrate —
> a graph of nodes — and everything is in it. Computation is the rewriting of that graph.
> There are no other moving parts, and crucially, no seams.*
>
> — `docs/vision.md`

The design is informed by:
- Datalog / Prolog (definite clause engines)
- Defeasible logic (Nute, Governatori)
- Magic-sets demand-driven evaluation
- Attempto Controlled English (CNL as surface, not engine input)
- Provenance / truth-maintenance traditions

See `docs/vision.md`, `docs/logic_fragment.md`, and `docs/processing_modes.md` for the
canonical design rationale; `docs/architecture.md` for the as-built layering; and
`docs/engine_user_guide.md` / `docs/engine_developer_guide.md` for building on and extending
the engine.
