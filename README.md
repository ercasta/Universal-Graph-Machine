# UGM — Universal Graph Machine

**A substrate for performing computation over graphs.**

UGM is a self-contained Python library that provides a label-less attribute graph
substrate, a declarative instruction set architecture (ISA) for graph computation,
and an optional Controlled Natural Language (CNL) surface for authoring and rendering.
No external reasoning engines. No embeddings. No LLMs. Pure symbolic graph
computation.

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

There is no NAC/`CHECK-ABSENT` opcode — the matching core is purely positive; negation is
materialized as a positive `is_not` attribute and matched like any other (`ugm/decide.py`).
There is also no opcode that deletes or lowers a fact: the invariant is a property of the
opcode set itself, not a lint pass.

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

**SATURATE / CHAIN** are the forward and backward engines respectively. Rules are
reified as graph structure (a `<rule>` node with `rl_lhs`, `rl_rhs` relations). APPLY
walks the rule body, emitting derivations into the graph. CHAIN is demand-driven
(magic-sets), so it never over-derives.

**CHECK** answers a yes/no/unknown question with four statuses: `POSITIVE` (proved),
`ENTAILED_NEG` (negation proved), `ASSUMED_NO` (CWA: no evidence), `UNKNOWN` (open
world). **CWA is the default**: an underivable goal is a defeasible `no`. **OWA is
opt-in per predicate** (`open_preds`) — for concepts where absence should not be taken
as false ("no sighting" ≠ "no mice"), so the verdict stays `UNKNOWN` and defers to
evidence-gathering instead.

**CHOOSE** selects the best option from a candidate set using graded α-cut: an option
wins if it satisfies the goal at a level no other option does. Ties are retained.
Graded attributes (`urgent: 0.9`) feed directly into the selection.

**SUPPOSE** enables safe hypothesis reasoning via a pencil/ink split. Assumed facts are
written as control-scoped (`pencil`) nodes; derivations run inside the scope. On
confirmation the assumptions are committed to the fact layer (`ink`); on refutation the
entire scope is dropped. The fact layer is never tentatively modified.

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

Key CNL concepts:
- **Facts**: subject–predicate–object triples (`alice wants vanilla`)
- **Rules**: `HEAD when BODY` with `and`, `not`, graded conditions (`is very urgent`)
- **Universals**: `if BODY then HEAD` and `ADJ things are PRED` laws
- **Gradable dimensions**: declared with `X is gradable`; used in rules as `?x is very X`
- **Closed-world declarations**: `P is closed world` opts a predicate into aggressive
  `is_not` completion (`ugm/decide.py`) — distinct from CHECK's query-time CWA-default/OWA-opt-in
  split, which is a Python-level `open_preds` set (no CNL surface form yet)

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

---

## What is expressible

UGM targets a deliberately small, well-understood logic fragment:

- **Definite Horn rules** with conjunctive bodies (Datalog; least-fixpoint semantics)
- **Stratified negation-as-completion** with CWA-default bounded enumeration
- **Defeasible rules with priorities** — defaults, exceptions, overrides (no contraposition)
- **Deontic statuses** as reified ranked predicates (`forbidden` … `obligatory`)
- **Declared congruence** (`same_as`) propagated over KB-declared predicates only
- **Graded attributes** in `[0,1]` unified with the rule matching layer (α-cut)
- **Scoped hypothetical reasoning** (SUPPOSE) without possible-worlds machinery

Formal anchors are kept for correctness; general theorem proving is not the goal.

---

## Usage

```python
import ugm as h

g = h.Graph()
h.load_facts(g, """
alice wants vanilla
vanilla is in_stock
""")
h.load_rules(g, """
alice gets vanilla when alice wants vanilla and vanilla is in_stock
""")
h.run_rules(g)

# Query
answer, status = h.ask(g, "alice gets vanilla")
print(answer)   # True

# Explanation
print(h.explain(g, next(iter(g.nodes_named("gets")))))
```

The ISA engine is available directly:

```python
from ugm import chain_sip, check, choose, suppose, Graph

g = Graph()
# ... populate g ...

result = chain_sip(g, rules, goal_pattern)
verdict = check(g, rules, "alice", "gets", "vanilla")
```

---

## The rewriter oracle (temporary)

`ugm.cnl.rewriter` is the reference engine from the previous generation of the system.
It is retained as a differential-test oracle during the ISA build and will be deleted in
Phase 6 once the firmware is fully self-consistent. Do not use it in new code.

---

## Installation

```bash
pip install ugm              # core (no mandatory deps)
pip install "ugm[asp]"       # + clingo for disjunction/model-enumeration calculators
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
canonical design rationale.
